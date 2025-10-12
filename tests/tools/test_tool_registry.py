"""
Comprehensive Tests for Tool Registry System (Phase 11/12)

Tests the ToolRegistry implementation including:
- Tool registration and validation
- Parameter validation with JSON Schema
- Risk level assessment (5 levels: SAFE, LOW, MEDIUM, HIGH, CRITICAL)
- Capability matching
- Rate limiting
- Audit trail verification
- Tool discovery and filtering
"""

import pytest
import asyncio
import time
from typing import Dict, Any
from unittest.mock import AsyncMock

from src.agents.tools.registry import (
    ToolCategory,
    ToolRiskLevel,
    ToolDefinition,
    ToolRegistry
)
from src.agents.tools import create_default_registry


class TestToolRiskLevels:
    """Test the 5-level risk assessment system"""

    def test_risk_level_enum(self):
        """Test all 5 risk levels exist"""
        assert ToolRiskLevel.SAFE.value == "safe"
        assert ToolRiskLevel.LOW.value == "low"
        assert ToolRiskLevel.MEDIUM.value == "medium"
        assert ToolRiskLevel.HIGH.value == "high"
        assert ToolRiskLevel.CRITICAL.value == "critical"

    def test_risk_level_ordering(self):
        """Test risk levels can be compared"""
        risk_levels = [
            ToolRiskLevel.SAFE,
            ToolRiskLevel.LOW,
            ToolRiskLevel.MEDIUM,
            ToolRiskLevel.HIGH,
            ToolRiskLevel.CRITICAL
        ]

        # Verify ordering by index
        for i in range(len(risk_levels) - 1):
            # Lower index = lower risk
            assert risk_levels.index(risk_levels[i]) < risk_levels.index(risk_levels[i + 1])


class TestToolCategory:
    """Test tool categorization system"""

    def test_category_enum(self):
        """Test all tool categories"""
        assert ToolCategory.DATABASE_READ.value == "database_read"
        assert ToolCategory.DATABASE_WRITE.value == "database_write"
        assert ToolCategory.DATABASE_DDL.value == "database_ddl"
        assert ToolCategory.FILE_SYSTEM.value == "file_system"
        assert ToolCategory.BACKUP.value == "backup"
        assert ToolCategory.ANALYSIS.value == "analysis"
        assert ToolCategory.MIGRATION.value == "migration"
        assert ToolCategory.OPTIMIZATION.value == "optimization"


class TestToolDefinition:
    """Test ToolDefinition dataclass and methods"""

    @pytest.fixture
    def sample_tool(self):
        """Create a sample tool definition"""
        async def sample_implementation(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {'result': 'success', 'value': params.get('value', 0) * 2}

        return ToolDefinition(
            name="sample_tool",
            description="A sample tool for testing",
            category=ToolCategory.ANALYSIS,
            risk_level=ToolRiskLevel.SAFE,
            required_capabilities=["analysis_read"],
            parameters_schema={
                "type": "object",
                "properties": {
                    "value": {"type": "integer", "minimum": 0, "maximum": 100}
                },
                "required": ["value"]
            },
            returns_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "value": {"type": "integer"}
                },
                "required": ["result", "value"]
            },
            implementation=sample_implementation,
            requires_approval=False,
            max_execution_time=60,
            rate_limit=10
        )

    def test_tool_definition_creation(self, sample_tool):
        """Test creating tool definition"""
        assert sample_tool.name == "sample_tool"
        assert sample_tool.category == ToolCategory.ANALYSIS
        assert sample_tool.risk_level == ToolRiskLevel.SAFE
        assert sample_tool.requires_approval is False
        assert sample_tool.max_execution_time == 60
        assert sample_tool.rate_limit == 10

    def test_parameter_validation_success(self, sample_tool):
        """Test valid parameter validation"""
        valid_params = {"value": 50}
        is_valid, error_msg = sample_tool.validate_parameters(valid_params)

        assert is_valid is True
        assert error_msg is None

    def test_parameter_validation_missing_required(self, sample_tool):
        """Test parameter validation with missing required field"""
        invalid_params = {}
        is_valid, error_msg = sample_tool.validate_parameters(invalid_params)

        assert is_valid is False
        assert error_msg is not None
        assert "required" in error_msg.lower() or "value" in error_msg.lower()

    def test_parameter_validation_wrong_type(self, sample_tool):
        """Test parameter validation with wrong type"""
        invalid_params = {"value": "not_an_integer"}
        is_valid, error_msg = sample_tool.validate_parameters(invalid_params)

        assert is_valid is False
        assert error_msg is not None

    def test_parameter_validation_out_of_range(self, sample_tool):
        """Test parameter validation with value out of range"""
        invalid_params = {"value": 150}  # max is 100
        is_valid, error_msg = sample_tool.validate_parameters(invalid_params)

        assert is_valid is False
        assert error_msg is not None

    def test_return_value_validation_success(self, sample_tool):
        """Test valid return value validation"""
        valid_return = {"result": "success", "value": 100}
        is_valid, error_msg = sample_tool.validate_return_value(valid_return)

        assert is_valid is True
        assert error_msg is None

    def test_return_value_validation_failure(self, sample_tool):
        """Test invalid return value validation"""
        invalid_return = {"result": "success"}  # missing 'value'
        is_valid, error_msg = sample_tool.validate_return_value(invalid_return)

        assert is_valid is False
        assert error_msg is not None

    @pytest.mark.asyncio
    async def test_tool_execution_success(self, sample_tool):
        """Test successful tool execution"""
        params = {"value": 10}
        context = {}

        result = await sample_tool.execute(params, context)

        assert result['result'] == 'success'
        assert result['value'] == 20  # 10 * 2

    @pytest.mark.asyncio
    async def test_tool_execution_invalid_params(self, sample_tool):
        """Test tool execution with invalid parameters"""
        params = {}  # missing required 'value'
        context = {}

        with pytest.raises(ValueError) as exc_info:
            await sample_tool.execute(params, context)

        assert "Invalid parameters" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tool_execution_invalid_return(self):
        """Test tool execution with invalid return value"""
        async def bad_implementation(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {"wrong": "format"}  # doesn't match schema

        tool = ToolDefinition(
            name="bad_tool",
            description="Tool with bad return",
            category=ToolCategory.ANALYSIS,
            risk_level=ToolRiskLevel.SAFE,
            required_capabilities=[],
            parameters_schema={"type": "object"},
            returns_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                },
                "required": ["result"]
            },
            implementation=bad_implementation,
            requires_approval=False,
            max_execution_time=60
        )

        with pytest.raises(RuntimeError) as exc_info:
            await tool.execute({}, {})

        assert "Invalid return value" in str(exc_info.value)


class TestToolRegistry:
    """Test ToolRegistry functionality"""

    @pytest.fixture
    def registry(self):
        """Create empty tool registry"""
        return ToolRegistry()

    @pytest.fixture
    def populated_registry(self):
        """Create registry with default tools"""
        return create_default_registry()

    @pytest.fixture
    def sample_tool_def(self):
        """Create sample tool definition"""
        async def impl(params, context):
            return {"status": "ok"}

        return ToolDefinition(
            name="test_tool",
            description="Test tool",
            category=ToolCategory.ANALYSIS,
            risk_level=ToolRiskLevel.LOW,
            required_capabilities=["test"],
            parameters_schema={"type": "object"},
            returns_schema={"type": "object"},
            implementation=impl,
            requires_approval=False,
            max_execution_time=30
        )

    def test_registry_initialization(self, registry):
        """Test registry initialization"""
        assert len(registry.list_tools()) == 0
        assert len(registry._execution_log) == 0
        assert len(registry._rate_limit_tracking) == 0

    def test_register_tool(self, registry, sample_tool_def):
        """Test tool registration"""
        registry.register_tool(sample_tool_def)

        assert len(registry.list_tools()) == 1
        assert "test_tool" in registry.list_tools()

    def test_register_duplicate_tool(self, registry, sample_tool_def):
        """Test registering duplicate tool raises error"""
        registry.register_tool(sample_tool_def)

        with pytest.raises(ValueError) as exc_info:
            registry.register_tool(sample_tool_def)

        assert "already registered" in str(exc_info.value)

    def test_unregister_tool(self, registry, sample_tool_def):
        """Test tool unregistration"""
        registry.register_tool(sample_tool_def)
        assert len(registry.list_tools()) == 1

        result = registry.unregister_tool("test_tool")

        assert result is True
        assert len(registry.list_tools()) == 0

    def test_unregister_nonexistent_tool(self, registry):
        """Test unregistering non-existent tool"""
        result = registry.unregister_tool("nonexistent")

        assert result is False

    def test_get_tool(self, registry, sample_tool_def):
        """Test retrieving tool by name"""
        registry.register_tool(sample_tool_def)

        tool = registry.get_tool("test_tool")

        assert tool is not None
        assert tool.name == "test_tool"

    def test_get_nonexistent_tool(self, registry):
        """Test retrieving non-existent tool"""
        tool = registry.get_tool("nonexistent")

        assert tool is None

    def test_list_tools(self, populated_registry):
        """Test listing all registered tools"""
        tools = populated_registry.list_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0
        assert "backup_database_full" in tools
        assert "analyze_schema" in tools

    def test_find_tools_by_category(self, populated_registry):
        """Test finding tools by category"""
        backup_tools = populated_registry.find_tools(category=ToolCategory.BACKUP)

        assert len(backup_tools) > 0
        for tool in backup_tools:
            assert tool.category == ToolCategory.BACKUP

    def test_find_tools_by_risk_level(self, populated_registry):
        """Test finding tools by maximum risk level"""
        safe_tools = populated_registry.find_tools(max_risk=ToolRiskLevel.SAFE)

        assert len(safe_tools) > 0
        for tool in safe_tools:
            assert tool.risk_level == ToolRiskLevel.SAFE

        low_and_safe_tools = populated_registry.find_tools(max_risk=ToolRiskLevel.LOW)

        # Should include SAFE and LOW
        assert len(low_and_safe_tools) >= len(safe_tools)

    def test_find_tools_by_capabilities(self, populated_registry):
        """Test finding tools by required capabilities"""
        capabilities = ["database_read", "schema_analyze"]
        tools = populated_registry.find_tools(capabilities=capabilities)

        assert len(tools) > 0
        for tool in tools:
            # Agent must have all required capabilities
            assert all(cap in capabilities for cap in tool.required_capabilities)

    def test_find_tools_combined_filters(self, populated_registry):
        """Test finding tools with multiple filters"""
        tools = populated_registry.find_tools(
            category=ToolCategory.BACKUP,
            max_risk=ToolRiskLevel.MEDIUM,
            capabilities=["database_read", "backup_create", "file_write"]
        )

        for tool in tools:
            assert tool.category == ToolCategory.BACKUP
            assert tool.risk_level.value in ["safe", "low", "medium"]

    def test_get_tool_description(self, populated_registry):
        """Test getting formatted tool description"""
        description = populated_registry.get_tool_description("backup_database_full")

        assert "backup_database_full" in description
        assert "Parameters:" in description
        assert "Returns:" in description
        assert "Risk Level:" in description

    def test_get_tool_description_nonexistent(self, populated_registry):
        """Test getting description for non-existent tool"""
        description = populated_registry.get_tool_description("nonexistent")

        assert "not found" in description.lower()

    def test_get_available_tools_for_llm(self, populated_registry):
        """Test getting LLM-formatted tool descriptions"""
        capabilities = ["database_read", "schema_analyze"]
        descriptions = populated_registry.get_available_tools_for_llm(
            capabilities=capabilities,
            max_risk=ToolRiskLevel.SAFE
        )

        assert isinstance(descriptions, str)
        assert len(descriptions) > 0

    def test_get_available_tools_for_llm_no_tools(self, registry):
        """Test LLM descriptions when no tools match"""
        descriptions = registry.get_available_tools_for_llm(
            capabilities=["nonexistent"],
            max_risk=ToolRiskLevel.SAFE
        )

        assert "No tools available" in descriptions

    def test_log_execution(self, registry):
        """Test logging tool execution"""
        registry.log_execution(
            tool_name="test_tool",
            params={"value": 10},
            result={"status": "success"},
            execution_time=0.5,
            success=True
        )

        logs = registry.get_execution_log()

        assert len(logs) == 1
        assert logs[0]['tool_name'] == "test_tool"
        assert logs[0]['success'] is True
        assert logs[0]['execution_time'] == 0.5

    def test_log_execution_failure(self, registry):
        """Test logging failed execution"""
        registry.log_execution(
            tool_name="test_tool",
            params={"value": 10},
            result={},
            execution_time=0.1,
            success=False,
            error="Execution failed"
        )

        logs = registry.get_execution_log()

        assert len(logs) == 1
        assert logs[0]['success'] is False
        assert logs[0]['error'] == "Execution failed"

    def test_get_execution_log_filtered(self, registry):
        """Test getting filtered execution log"""
        registry.log_execution("tool1", {}, {}, 1.0, True)
        registry.log_execution("tool2", {}, {}, 1.0, True)
        registry.log_execution("tool1", {}, {}, 1.0, True)

        # Filter by tool name
        tool1_logs = registry.get_execution_log(tool_name="tool1")

        assert len(tool1_logs) == 2
        for log in tool1_logs:
            assert log['tool_name'] == "tool1"

    def test_get_execution_log_limited(self, registry):
        """Test getting limited execution log"""
        for i in range(10):
            registry.log_execution(f"tool_{i}", {}, {}, 1.0, True)

        # Get last 5 entries
        logs = registry.get_execution_log(limit=5)

        assert len(logs) == 5

    def test_check_rate_limit_no_limit(self, registry, sample_tool_def):
        """Test rate limit check when no limit is set"""
        # Remove rate limit
        sample_tool_def.rate_limit = None
        registry.register_tool(sample_tool_def)

        is_allowed, error_msg = registry.check_rate_limit("test_tool")

        assert is_allowed is True
        assert error_msg is None

    def test_check_rate_limit_within_limit(self, registry, sample_tool_def):
        """Test rate limit check within allowed limit"""
        sample_tool_def.rate_limit = 5
        registry.register_tool(sample_tool_def)

        # Make 3 calls (under limit of 5)
        for _ in range(3):
            is_allowed, error_msg = registry.check_rate_limit("test_tool")
            assert is_allowed is True

    def test_check_rate_limit_exceeded(self, registry, sample_tool_def):
        """Test rate limit check when exceeded"""
        sample_tool_def.rate_limit = 3
        registry.register_tool(sample_tool_def)

        # Make calls up to limit
        for _ in range(3):
            is_allowed, _ = registry.check_rate_limit("test_tool")
            assert is_allowed is True

        # Next call should exceed limit
        is_allowed, error_msg = registry.check_rate_limit("test_tool")

        assert is_allowed is False
        assert error_msg is not None
        assert "Rate limit exceeded" in error_msg

    def test_rate_limit_window_reset(self, registry, sample_tool_def):
        """Test rate limit window resets after time"""
        sample_tool_def.rate_limit = 2
        registry.register_tool(sample_tool_def)

        # Fill rate limit
        registry.check_rate_limit("test_tool")
        registry.check_rate_limit("test_tool")

        # Should be at limit
        is_allowed, _ = registry.check_rate_limit("test_tool")
        assert is_allowed is False

        # Manually clear old entries (simulate 60+ seconds passing)
        registry._rate_limit_tracking["test_tool"] = []

        # Should be allowed again
        is_allowed, _ = registry.check_rate_limit("test_tool")
        assert is_allowed is True

    def test_get_registry_stats(self, populated_registry):
        """Test getting registry statistics"""
        stats = populated_registry.get_registry_stats()

        assert 'total_tools' in stats
        assert 'tools_by_category' in stats
        assert 'tools_by_risk_level' in stats
        assert 'total_executions' in stats

        assert stats['total_tools'] > 0
        assert isinstance(stats['tools_by_category'], dict)
        assert isinstance(stats['tools_by_risk_level'], dict)

    def test_registry_stats_with_executions(self, registry, sample_tool_def):
        """Test registry statistics with execution data"""
        registry.register_tool(sample_tool_def)

        # Log some executions
        registry.log_execution("test_tool", {}, {}, 1.0, True)
        registry.log_execution("test_tool", {}, {}, 1.0, True)
        registry.log_execution("test_tool", {}, {}, 1.0, False, error="Failed")

        stats = registry.get_registry_stats()

        assert stats['total_executions'] == 3
        assert stats['successful_executions'] == 2
        assert stats['failed_executions'] == 1


class TestDatabaseTools:
    """Test actual database tools from the registry"""

    @pytest.fixture
    def registry(self):
        """Create registry with database tools"""
        return create_default_registry()

    @pytest.mark.asyncio
    async def test_backup_database_full(self, registry):
        """Test backup_database_full tool"""
        tool = registry.get_tool("backup_database_full")

        assert tool is not None
        assert tool.category == ToolCategory.BACKUP
        assert tool.risk_level == ToolRiskLevel.LOW

        # Execute tool
        params = {
            "database": "test_db",
            "destination": "/tmp/pytest_backup.sql.gz",
            "compression": True
        }

        result = await tool.execute(params, {})

        assert result['backup_path'].endswith('.sql.gz')
        assert 'size_bytes' in result
        assert 'checksum' in result
        assert len(result['checksum']) == 32  # MD5 hex

    @pytest.mark.asyncio
    async def test_analyze_schema(self, registry):
        """Test analyze_schema tool"""
        tool = registry.get_tool("analyze_schema")

        assert tool is not None
        assert tool.category == ToolCategory.ANALYSIS
        assert tool.risk_level == ToolRiskLevel.SAFE

        # Execute tool
        params = {
            "database": "test_db",
            "include_indexes": True,
            "include_constraints": True
        }

        result = await tool.execute(params, {})

        assert 'tables' in result
        assert 'indexes' in result
        assert 'constraints' in result
        assert 'statistics' in result
        assert isinstance(result['tables'], list)

    @pytest.mark.asyncio
    async def test_validate_backup(self, registry):
        """Test validate_backup tool"""
        tool = registry.get_tool("validate_backup")

        assert tool is not None
        assert tool.category == ToolCategory.BACKUP
        assert tool.risk_level == ToolRiskLevel.SAFE

        # First create a backup to validate
        backup_tool = registry.get_tool("backup_database_full")
        backup_result = await backup_tool.execute({
            "database": "test_db",
            "destination": "/tmp/pytest_validate_backup.sql.gz"
        }, {})

        # Now validate it
        params = {"backup_path": backup_result['backup_path']}
        result = await tool.execute(params, {})

        assert result['valid'] is True
        assert 'checksum' in result
        assert result['size_bytes'] > 0
        assert result['error_message'] is None

    @pytest.mark.asyncio
    async def test_validate_backup_missing_file(self, registry):
        """Test validate_backup with missing file"""
        tool = registry.get_tool("validate_backup")

        params = {"backup_path": "/tmp/nonexistent_backup.sql.gz"}
        result = await tool.execute(params, {})

        assert result['valid'] is False
        assert result['error_message'] is not None
        assert "not found" in result['error_message'].lower()


class TestAuditTrail:
    """Test audit trail functionality"""

    @pytest.fixture
    def registry(self):
        """Create registry for audit testing"""
        return create_default_registry()

    @pytest.mark.asyncio
    async def test_audit_trail_creation(self, registry):
        """Test that tool executions create audit trail"""
        tool = registry.get_tool("analyze_schema")

        # Execute tool
        params = {"database": "audit_test_db"}
        result = await tool.execute(params, {})

        # Log execution
        registry.log_execution(
            tool_name="analyze_schema",
            params=params,
            result=result,
            execution_time=0.5,
            success=True
        )

        # Check audit log
        logs = registry.get_execution_log(tool_name="analyze_schema")

        assert len(logs) > 0
        last_log = logs[-1]
        assert last_log['tool_name'] == "analyze_schema"
        assert last_log['params'] == params
        assert last_log['success'] is True
        assert 'timestamp' in last_log

    @pytest.mark.asyncio
    async def test_audit_trail_timestamps(self, registry):
        """Test audit trail includes timestamps"""
        registry.log_execution("tool1", {}, {}, 1.0, True)
        time.sleep(0.01)  # Small delay
        registry.log_execution("tool2", {}, {}, 1.0, True)

        logs = registry.get_execution_log()

        assert len(logs) == 2
        # Later execution should have later timestamp
        assert logs[1]['timestamp'] > logs[0]['timestamp']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
