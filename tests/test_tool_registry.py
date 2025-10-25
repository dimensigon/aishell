"""
Tests for Tool Registry System

Tests the core functionality of the tool registry including:
- Tool registration and retrieval
- Parameter validation
- Risk-based filtering
- LLM-friendly descriptions
"""

import pytest
import asyncio
from src.agents.tools import (
    ToolCategory,
    ToolRiskLevel,
    ToolDefinition,
    ToolRegistry,
    create_default_registry
)


# Sample tool implementation for testing
async def sample_tool_impl(params: dict, context: dict) -> dict:
    """Sample tool implementation"""
    return {
        "result": f"Processed {params.get('input', 'nothing')}",
        "status": "success"
    }


def test_tool_registry_initialization():
    """Test registry can be created"""
    registry = ToolRegistry()
    assert len(registry.list_tools()) == 0


def test_tool_registration():
    """Test registering a tool"""
    registry = ToolRegistry()

    tool = ToolDefinition(
        name="test_tool",
        description="A test tool",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=["test_capability"],
        parameters_schema={
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        },
        returns_schema={
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "status": {"type": "string"}
            }
        },
        implementation=sample_tool_impl,
        requires_approval=False,
        max_execution_time=60
    )

    registry.register_tool(tool)
    assert len(registry.list_tools()) == 1
    assert "test_tool" in registry.list_tools()


def test_duplicate_registration_fails():
    """Test that duplicate tool names are rejected"""
    registry = ToolRegistry()

    tool = ToolDefinition(
        name="duplicate_tool",
        description="Test",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=[],
        parameters_schema={"type": "object"},
        returns_schema={"type": "object"},
        implementation=sample_tool_impl,
        requires_approval=False,
        max_execution_time=60
    )

    registry.register_tool(tool)

    with pytest.raises(ValueError, match="already registered"):
        registry.register_tool(tool)


def test_get_tool():
    """Test retrieving a registered tool"""
    registry = ToolRegistry()

    tool = ToolDefinition(
        name="get_test",
        description="Test retrieval",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=[],
        parameters_schema={"type": "object"},
        returns_schema={"type": "object"},
        implementation=sample_tool_impl,
        requires_approval=False,
        max_execution_time=60
    )

    registry.register_tool(tool)
    retrieved = registry.get_tool("get_test")

    assert retrieved is not None
    assert retrieved.name == "get_test"
    assert retrieved.description == "Test retrieval"


def test_get_nonexistent_tool():
    """Test that getting a non-existent tool returns None"""
    registry = ToolRegistry()
    assert registry.get_tool("nonexistent") is None


def test_find_tools_by_category():
    """Test filtering tools by category"""
    registry = ToolRegistry()

    # Create tools in different categories
    for i, category in enumerate([ToolCategory.ANALYSIS, ToolCategory.BACKUP, ToolCategory.ANALYSIS]):
        tool = ToolDefinition(
            name=f"tool_{i}",
            description=f"Tool {i}",
            category=category,
            risk_level=ToolRiskLevel.SAFE,
            required_capabilities=[],
            parameters_schema={"type": "object"},
            returns_schema={"type": "object"},
            implementation=sample_tool_impl,
            requires_approval=False,
            max_execution_time=60
        )
        registry.register_tool(tool)

    # Find analysis tools
    analysis_tools = registry.find_tools(category=ToolCategory.ANALYSIS)
    assert len(analysis_tools) == 2

    # Find backup tools
    backup_tools = registry.find_tools(category=ToolCategory.BACKUP)
    assert len(backup_tools) == 1


def test_find_tools_by_risk_level():
    """Test filtering tools by maximum risk level"""
    registry = ToolRegistry()

    # Create tools with different risk levels
    risk_levels = [ToolRiskLevel.SAFE, ToolRiskLevel.MEDIUM, ToolRiskLevel.CRITICAL]
    for i, risk in enumerate(risk_levels):
        tool = ToolDefinition(
            name=f"risk_tool_{i}",
            description=f"Risk tool {i}",
            category=ToolCategory.ANALYSIS,
            risk_level=risk,
            required_capabilities=[],
            parameters_schema={"type": "object"},
            returns_schema={"type": "object"},
            implementation=sample_tool_impl,
            requires_approval=False,
            max_execution_time=60
        )
        registry.register_tool(tool)

    # Find only safe and low risk tools
    safe_tools = registry.find_tools(max_risk=ToolRiskLevel.MEDIUM)
    assert len(safe_tools) == 2  # SAFE and MEDIUM, not CRITICAL


def test_find_tools_by_capabilities():
    """Test filtering tools by required capabilities"""
    registry = ToolRegistry()

    # Create tools with different capabilities
    tools_data = [
        ("tool_1", ["cap_a"]),
        ("tool_2", ["cap_a", "cap_b"]),
        ("tool_3", ["cap_c"])
    ]

    for name, caps in tools_data:
        tool = ToolDefinition(
            name=name,
            description=name,
            category=ToolCategory.ANALYSIS,
            risk_level=ToolRiskLevel.SAFE,
            required_capabilities=caps,
            parameters_schema={"type": "object"},
            returns_schema={"type": "object"},
            implementation=sample_tool_impl,
            requires_approval=False,
            max_execution_time=60
        )
        registry.register_tool(tool)

    # Agent with cap_a and cap_b should get tools that need only those
    matching_tools = registry.find_tools(capabilities=["cap_a", "cap_b"])
    assert len(matching_tools) == 2  # tool_1 and tool_2


def test_parameter_validation():
    """Test parameter validation against JSON schema"""
    tool = ToolDefinition(
        name="validation_test",
        description="Test validation",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=[],
        parameters_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "count": {"type": "integer"}
            },
            "required": ["name"]
        },
        returns_schema={"type": "object"},
        implementation=sample_tool_impl,
        requires_approval=False,
        max_execution_time=60
    )

    # Valid parameters
    valid, error = tool.validate_parameters({"name": "test", "count": 5})
    assert valid is True
    assert error is None

    # Missing required parameter
    valid, error = tool.validate_parameters({"count": 5})
    assert valid is False
    assert "name" in error.lower() or "required" in error.lower()

    # Wrong type
    valid, error = tool.validate_parameters({"name": "test", "count": "not an integer"})
    assert valid is False


@pytest.mark.asyncio
async def test_tool_execution():
    """Test executing a tool"""
    tool = ToolDefinition(
        name="exec_test",
        description="Test execution",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=[],
        parameters_schema={
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        },
        returns_schema={
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "status": {"type": "string"}
            }
        },
        implementation=sample_tool_impl,
        requires_approval=False,
        max_execution_time=60
    )

    result = await tool.execute({"input": "test data"}, {})
    assert result["status"] == "success"
    assert "test data" in result["result"]


@pytest.mark.asyncio
async def test_tool_execution_invalid_params():
    """Test that execution fails with invalid parameters"""
    tool = ToolDefinition(
        name="invalid_test",
        description="Test invalid params",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=[],
        parameters_schema={
            "type": "object",
            "properties": {
                "required_field": {"type": "string"}
            },
            "required": ["required_field"]
        },
        returns_schema={"type": "object"},
        implementation=sample_tool_impl,
        requires_approval=False,
        max_execution_time=60
    )

    with pytest.raises(ValueError, match="Invalid parameters"):
        await tool.execute({}, {})


def test_get_tool_description():
    """Test getting LLM-friendly tool description"""
    registry = ToolRegistry()

    tool = ToolDefinition(
        name="desc_test",
        description="A tool for testing descriptions",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.LOW,
        required_capabilities=["test_cap"],
        parameters_schema={
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            }
        },
        returns_schema={
            "type": "object",
            "properties": {
                "output": {"type": "string"}
            }
        },
        implementation=sample_tool_impl,
        requires_approval=True,
        max_execution_time=120,
        examples=[{"params": {"input": "test"}}]
    )

    registry.register_tool(tool)
    description = registry.get_tool_description("desc_test")

    assert "desc_test" in description
    assert "A tool for testing descriptions" in description
    assert "analysis" in description
    assert "low" in description
    assert "True" in description  # requires_approval


def test_get_available_tools_for_llm():
    """Test getting all available tools formatted for LLM"""
    registry = ToolRegistry()

    # Register multiple tools
    for i in range(3):
        tool = ToolDefinition(
            name=f"llm_tool_{i}",
            description=f"Tool {i}",
            category=ToolCategory.ANALYSIS,
            risk_level=ToolRiskLevel.SAFE,
            required_capabilities=["read"],
            parameters_schema={"type": "object"},
            returns_schema={"type": "object"},
            implementation=sample_tool_impl,
            requires_approval=False,
            max_execution_time=60
        )
        registry.register_tool(tool)

    tools_description = registry.get_available_tools_for_llm(capabilities=["read"])

    assert "llm_tool_0" in tools_description
    assert "llm_tool_1" in tools_description
    assert "llm_tool_2" in tools_description


def test_registry_stats():
    """Test getting registry statistics"""
    registry = ToolRegistry()

    # Register tools with different categories and risk levels
    registry.register_tool(ToolDefinition(
        name="stat_tool_1",
        description="Test",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=[],
        parameters_schema={"type": "object"},
        returns_schema={"type": "object"},
        implementation=sample_tool_impl,
        requires_approval=False,
        max_execution_time=60
    ))

    registry.register_tool(ToolDefinition(
        name="stat_tool_2",
        description="Test",
        category=ToolCategory.BACKUP,
        risk_level=ToolRiskLevel.MEDIUM,
        required_capabilities=[],
        parameters_schema={"type": "object"},
        returns_schema={"type": "object"},
        implementation=sample_tool_impl,
        requires_approval=False,
        max_execution_time=60
    ))

    stats = registry.get_registry_stats()

    assert stats["total_tools"] == 2
    assert stats["tools_by_category"]["analysis"] == 1
    assert stats["tools_by_category"]["backup"] == 1
    assert stats["tools_by_risk_level"]["safe"] == 1
    assert stats["tools_by_risk_level"]["medium"] == 1


def test_create_default_registry():
    """Test creating default registry"""
    registry = create_default_registry()
    assert isinstance(registry, ToolRegistry)
    # When core tools are implemented, this will have tools
    # For now, it should be empty but functional
    assert registry.get_registry_stats()["total_tools"] >= 0


def test_unregister_tool():
    """Test unregistering a tool"""
    registry = ToolRegistry()

    tool = ToolDefinition(
        name="unreg_test",
        description="Test",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=[],
        parameters_schema={"type": "object"},
        returns_schema={"type": "object"},
        implementation=sample_tool_impl,
        requires_approval=False,
        max_execution_time=60
    )

    registry.register_tool(tool)
    assert len(registry.list_tools()) == 1

    result = registry.unregister_tool("unreg_test")
    assert result is True
    assert len(registry.list_tools()) == 0

    # Try to unregister non-existent tool
    result = registry.unregister_tool("nonexistent")
    assert result is False
