"""
Comprehensive coverage tests for SafetyController
Targeting uncovered branches, error paths, and edge cases
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.agents.safety.controller import (
    SafetyController,
    SafetyLevel,
    SafetyPolicy,
    SafetyViolation,
    ApprovalRequirement,
)
from src.agents.base import AgentConfig
from src.agents.tools.registry import ToolRiskLevel, ToolCategory
from src.database.risk_analyzer import SQLRiskAnalyzer, RiskLevel


class MockTool:
    """Mock tool for testing"""
    def __init__(self, risk_level, category, requires_approval=False):
        self.risk_level = risk_level
        self.category = category
        self.requires_approval = requires_approval


class TestSafetyPolicyEdgeCases:
    """Test SafetyPolicy edge cases"""

    def test_policy_default_values(self):
        """Test policy with all default values"""
        policy = SafetyPolicy()

        assert policy.safety_level == SafetyLevel.MEDIUM
        assert policy.require_approval_for == []
        assert policy.blocked_operations == []
        assert policy.allow_destructive is False

    def test_policy_with_empty_lists(self):
        """Test policy with explicitly empty lists"""
        policy = SafetyPolicy(
            require_approval_for=[],
            blocked_operations=[]
        )

        assert policy.require_approval_for == []
        assert policy.blocked_operations == []

    def test_policy_allows_unblocked_operation(self):
        """Test that unblocked operations are allowed"""
        policy = SafetyPolicy(blocked_operations=["drop_table"])

        assert policy.is_operation_allowed("select_data")
        assert policy.is_operation_allowed("insert_data")

    def test_policy_blocks_specified_operation(self):
        """Test that blocked operations are blocked"""
        policy = SafetyPolicy(blocked_operations=["drop_table", "truncate"])

        assert not policy.is_operation_allowed("drop_table")
        assert not policy.is_operation_allowed("truncate")

    def test_policy_requires_approval_for_specified(self):
        """Test approval requirement check"""
        policy = SafetyPolicy(require_approval_for=["migration", "backup"])

        assert policy.requires_approval("migration")
        assert policy.requires_approval("backup")
        assert not policy.requires_approval("query")

    def test_policy_all_safety_levels(self):
        """Test all safety levels"""
        for level in SafetyLevel:
            policy = SafetyPolicy(safety_level=level)
            assert policy.safety_level == level

    def test_policy_allow_destructive_true(self):
        """Test policy with destructive operations allowed"""
        policy = SafetyPolicy(allow_destructive=True)
        assert policy.allow_destructive is True

    def test_policy_with_many_blocked_operations(self):
        """Test policy with many blocked operations"""
        blocked = [f"operation_{i}" for i in range(100)]
        policy = SafetyPolicy(blocked_operations=blocked)

        assert len(policy.blocked_operations) == 100
        for op in blocked:
            assert not policy.is_operation_allowed(op)


class TestSafetyViolationEdgeCases:
    """Test SafetyViolation edge cases"""

    def test_violation_with_minimal_data(self):
        """Test violation with only message"""
        violation = SafetyViolation("Test violation")

        assert violation.message == "Test violation"
        assert violation.risk_level == "unknown"
        assert violation.details == {}

    def test_violation_with_all_data(self):
        """Test violation with full details"""
        details = {"table": "users", "operation": "DROP"}
        violation = SafetyViolation(
            "Dangerous operation",
            risk_level="critical",
            details=details
        )

        assert violation.message == "Dangerous operation"
        assert violation.risk_level == "critical"
        assert violation.details == details

    def test_violation_with_empty_details(self):
        """Test violation with explicitly empty details"""
        violation = SafetyViolation("Test", details={})

        assert violation.details == {}

    def test_violation_with_complex_details(self):
        """Test violation with nested details"""
        details = {
            "nested": {"level1": {"level2": "value"}},
            "list": [1, 2, 3]
        }
        violation = SafetyViolation("Test", details=details)

        assert violation.details == details

    def test_violation_exception_behavior(self):
        """Test that violation can be raised as exception"""
        with pytest.raises(SafetyViolation) as exc_info:
            raise SafetyViolation("Test violation", risk_level="high")

        assert "Test violation" in str(exc_info.value)


class TestSafetyControllerValidationEdgeCases:
    """Test SafetyController validation edge cases"""

    def test_validate_step_without_tool_definition(self):
        """Test validation when tool definition is missing"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        agent_config = AgentConfig(
            agent_type="database_agent",
            model="gpt-4",
            safety_level="moderate"
        )

        step = {
            "tool": "unknown_tool",
            "params": {}
        }

        validation = controller.validate_step(step, agent_config)

        assert validation["risk_level"] == "unknown"
        assert validation["requires_approval"] is True
        assert validation["approval_requirement"] == ApprovalRequirement.REQUIRED
        assert any("Tool definition not available" in r for r in validation["risks"])

    def test_validate_step_strict_safety_high_risk(self):
        """Test strict safety mode with high risk operation"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        agent_config = AgentConfig(
            agent_type="database_agent",
            model="gpt-4",
            safety_level="strict"
        )

        tool = MockTool(
            risk_level=ToolRiskLevel.HIGH,
            category=ToolCategory.DATABASE_WRITE,
            requires_approval=False
        )

        step = {
            "tool": "risky_operation",
            "params": {},
            "tool_definition": tool
        }

        validation = controller.validate_step(step, agent_config)

        assert validation["requires_approval"] is True
        assert validation["approval_requirement"] == ApprovalRequirement.REQUIRED

    def test_validate_step_strict_safety_critical_risk(self):
        """Test strict safety mode with critical risk"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        agent_config = AgentConfig(
            agent_type="database_agent",
            model="gpt-4",
            safety_level="strict"
        )

        tool = MockTool(
            risk_level=ToolRiskLevel.CRITICAL,
            category=ToolCategory.DATABASE_DDL
        )

        step = {
            "tool": "critical_operation",
            "params": {},
            "tool_definition": tool
        }

        validation = controller.validate_step(step, agent_config)

        assert validation["requires_approval"] is True

    def test_validate_step_moderate_safety_critical_risk(self):
        """Test moderate safety mode with critical risk"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        agent_config = AgentConfig(
            agent_type="database_agent",
            model="gpt-4",
            safety_level="moderate"
        )

        tool = MockTool(
            risk_level=ToolRiskLevel.CRITICAL,
            category=ToolCategory.DATABASE_WRITE
        )

        step = {
            "tool": "critical_op",
            "params": {},
            "tool_definition": tool
        }

        validation = controller.validate_step(step, agent_config)

        assert validation["requires_approval"] is True
        assert validation["approval_requirement"] == ApprovalRequirement.REQUIRED

    def test_validate_step_moderate_safety_high_risk(self):
        """Test moderate safety mode with high risk"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        agent_config = AgentConfig(
            agent_type="database_agent",
            model="gpt-4",
            safety_level="moderate"
        )

        tool = MockTool(
            risk_level=ToolRiskLevel.HIGH,
            category=ToolCategory.DATABASE_WRITE
        )

        step = {
            "tool": "high_risk_op",
            "params": {},
            "tool_definition": tool
        }

        validation = controller.validate_step(step, agent_config)

        assert validation["approval_requirement"] == ApprovalRequirement.OPTIONAL

    def test_validate_step_permissive_safety(self):
        """Test permissive safety mode"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        agent_config = AgentConfig(
            agent_type="database_agent",
            model="gpt-4",
            safety_level="permissive"
        )

        tool = MockTool(
            risk_level=ToolRiskLevel.MEDIUM,
            category=ToolCategory.DATABASE_WRITE,
            requires_approval=False
        )

        step = {
            "tool": "operation",
            "params": {},
            "tool_definition": tool
        }

        validation = controller.validate_step(step, agent_config)

        # In permissive mode, only explicit tool approval flags matter
        assert validation["requires_approval"] is False

    def test_validate_step_database_write_with_sql(self):
        """Test database write with SQL analysis"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        risk_analyzer.analyze.return_value = {
            "risk_level": "HIGH",
            "warnings": ["Missing WHERE clause", "Affects all rows"]
        }

        controller = SafetyController(risk_analyzer)

        agent_config = AgentConfig(
            agent_type="database_agent",
            model="gpt-4",
            safety_level="moderate"
        )

        tool = MockTool(
            risk_level=ToolRiskLevel.MEDIUM,
            category=ToolCategory.DATABASE_WRITE
        )

        step = {
            "tool": "execute_query",
            "params": {"sql": "DELETE FROM users"},
            "tool_definition": tool
        }

        validation = controller.validate_step(step, agent_config)

        assert validation["requires_approval"] is True
        assert "sql_analysis" in validation
        assert any("Missing WHERE" in w for w in validation["risks"])

    def test_validate_step_database_write_with_query_param(self):
        """Test database write with 'query' param instead of 'sql'"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        risk_analyzer.analyze.return_value = {
            "risk_level": "MEDIUM",
            "warnings": []
        }

        controller = SafetyController(risk_analyzer)

        agent_config = AgentConfig(
            agent_type="database_agent",
            model="gpt-4",
            safety_level="moderate"
        )

        tool = MockTool(
            risk_level=ToolRiskLevel.LOW,
            category=ToolCategory.DATABASE_WRITE
        )

        step = {
            "tool": "execute",
            "params": {"query": "UPDATE users SET active=1"},
            "tool_definition": tool
        }

        validation = controller.validate_step(step, agent_config)

        assert "sql_analysis" in validation
        risk_analyzer.analyze.assert_called_once()

    def test_validate_step_database_ddl(self):
        """Test DDL operations always require approval"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        risk_analyzer.analyze.return_value = {
            "risk_level": "HIGH",
            "warnings": ["Schema modification"]
        }

        controller = SafetyController(risk_analyzer)

        agent_config = AgentConfig(
            agent_type="database_agent",
            model="gpt-4",
            safety_level="permissive"  # Even in permissive mode
        )

        tool = MockTool(
            risk_level=ToolRiskLevel.HIGH,
            category=ToolCategory.DATABASE_DDL
        )

        step = {
            "tool": "create_table",
            "params": {"migration_sql": "CREATE TABLE test (id INT)"},
            "tool_definition": tool
        }

        validation = controller.validate_step(step, agent_config)

        assert validation["requires_approval"] is True
        assert validation["approval_requirement"] == ApprovalRequirement.REQUIRED
        assert any("Schema modification" in r for r in validation["risks"])

    def test_validate_step_ddl_with_sql_param(self):
        """Test DDL with 'sql' param instead of 'migration_sql'"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        risk_analyzer.analyze.return_value = {
            "risk_level": "HIGH",
            "warnings": []
        }

        controller = SafetyController(risk_analyzer)

        agent_config = AgentConfig(
            agent_type="database_agent",
            model="gpt-4",
            safety_level="moderate"
        )

        tool = MockTool(
            risk_level=ToolRiskLevel.HIGH,
            category=ToolCategory.DATABASE_DDL
        )

        step = {
            "tool": "alter_table",
            "params": {"sql": "ALTER TABLE users ADD COLUMN email VARCHAR(255)"},
            "tool_definition": tool
        }

        validation = controller.validate_step(step, agent_config)

        assert validation["requires_approval"] is True
        risk_analyzer.analyze.assert_called_once()


class TestDestructiveOperationDetection:
    """Test destructive operation detection"""

    def test_detect_destructive_tool_execute_migration(self):
        """Test detection of execute_migration tool"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {"tool": "execute_migration", "params": {}}

        assert controller._is_destructive_operation(step) is True

    def test_detect_destructive_tool_drop_table(self):
        """Test detection of drop_table tool"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {"tool": "drop_table", "params": {}}

        assert controller._is_destructive_operation(step) is True

    def test_detect_destructive_tool_truncate_table(self):
        """Test detection of truncate_table tool"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {"tool": "truncate_table", "params": {}}

        assert controller._is_destructive_operation(step) is True

    def test_detect_destructive_drop_in_sql(self):
        """Test detection of DROP in SQL"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {
            "tool": "execute_sql",
            "params": {"sql": "DROP TABLE users"}
        }

        assert controller._is_destructive_operation(step) is True

    def test_detect_destructive_truncate_in_sql(self):
        """Test detection of TRUNCATE in SQL"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {
            "tool": "execute_sql",
            "params": {"sql": "TRUNCATE TABLE logs"}
        }

        assert controller._is_destructive_operation(step) is True

    def test_detect_destructive_delete_from_in_sql(self):
        """Test detection of DELETE FROM in SQL"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {
            "tool": "execute_sql",
            "params": {"sql": "DELETE FROM users"}
        }

        assert controller._is_destructive_operation(step) is True

    def test_non_destructive_select(self):
        """Test that SELECT is not destructive"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {
            "tool": "execute_query",
            "params": {"sql": "SELECT * FROM users"}
        }

        assert controller._is_destructive_operation(step) is False

    def test_non_destructive_insert(self):
        """Test that INSERT is not destructive"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {
            "tool": "insert_data",
            "params": {"sql": "INSERT INTO users VALUES (1, 'test')"}
        }

        assert controller._is_destructive_operation(step) is False

    def test_detect_destructive_restore_backup(self):
        """Test that restore_backup is destructive"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {"tool": "restore_backup", "params": {}}

        assert controller._is_destructive_operation(step) is True

    def test_detect_destructive_in_migration_sql(self):
        """Test detection in migration_sql param"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {
            "tool": "apply_migration",
            "params": {"migration_sql": "DROP INDEX idx_users_email"}
        }

        assert controller._is_destructive_operation(step) is True

    def test_detect_destructive_in_query_param(self):
        """Test detection in query param"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {
            "tool": "run_query",
            "params": {"query": "TRUNCATE TABLE sessions"}
        }

        assert controller._is_destructive_operation(step) is True

    def test_non_destructive_empty_sql(self):
        """Test empty SQL is not destructive"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {
            "tool": "execute",
            "params": {"sql": ""}
        }

        assert controller._is_destructive_operation(step) is False

    def test_non_destructive_no_params(self):
        """Test step with no params"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {"tool": "read_data"}

        assert controller._is_destructive_operation(step) is False


@pytest.mark.asyncio
class TestSafetyControllerApprovalWorkflow:
    """Test approval workflow"""

    async def test_request_approval_with_custom_callback(self):
        """Test approval with custom callback"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {"tool": "test_tool", "params": {}}
        validation = {"risk_level": "high", "risks": []}

        async def custom_callback(request):
            return {
                "approved": True,
                "reason": "Custom approval",
                "approver": "admin",
                "timestamp": "2024-01-01T00:00:00",
                "conditions": []
            }

        approval = await controller.request_approval(
            step, validation, approval_callback=custom_callback
        )

        assert approval["approved"] is True
        assert approval["approver"] == "admin"
        assert len(controller.approval_history) == 1

    async def test_request_approval_rejected_by_callback(self):
        """Test approval rejection via callback"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {"tool": "dangerous_op", "params": {}}
        validation = {"risk_level": "critical", "risks": ["High risk"]}

        async def reject_callback(request):
            return {
                "approved": False,
                "reason": "Too risky",
                "approver": "security_team",
                "timestamp": "2024-01-01T00:00:00",
                "conditions": []
            }

        approval = await controller.request_approval(
            step, validation, approval_callback=reject_callback
        )

        assert approval["approved"] is False
        assert "Too risky" in approval["reason"]

    async def test_interactive_approval_with_yes_input(self):
        """Test interactive approval with 'yes' response"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {"tool": "test", "params": {"key": "value"}}
        validation = {
            "risk_level": "high",
            "approval_requirement": ApprovalRequirement.REQUIRED,
            "risks": ["Risk 1"],
            "mitigations": ["Mitigation 1"]
        }

        with patch("builtins.input", return_value="yes"):
            request = {
                "step": step,
                "validation": validation,
                "timestamp": "2024-01-01T00:00:00"
            }
            approval = await controller._interactive_approval(request)

        assert approval["approved"] is True
        assert approval["approver"] == "user"

    async def test_interactive_approval_with_no_input(self):
        """Test interactive approval with 'no' response"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {"tool": "test", "params": {}}
        validation = {
            "risk_level": "high",
            "approval_requirement": ApprovalRequirement.REQUIRED,
            "risks": [],
            "mitigations": []
        }

        with patch("builtins.input", side_effect=["no", "Security concerns"]):
            request = {
                "step": step,
                "validation": validation,
                "timestamp": "2024-01-01T00:00:00"
            }
            approval = await controller._interactive_approval(request)

        assert approval["approved"] is False
        assert "Security concerns" in approval["reason"]

    async def test_interactive_approval_with_sql_analysis(self):
        """Test interactive approval displays SQL analysis"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {"tool": "test", "params": {"sql": "DELETE FROM users"}}
        validation = {
            "risk_level": "critical",
            "approval_requirement": ApprovalRequirement.REQUIRED,
            "risks": ["High risk"],
            "mitigations": ["Backup available"],
            "sql_analysis": {
                "risk_level": "CRITICAL",
                "requires_confirmation": True,
                "issues": ["No WHERE clause"]
            }
        }

        with patch("builtins.input", return_value="yes"):
            with patch("builtins.print") as mock_print:
                request = {
                    "step": step,
                    "validation": validation,
                    "timestamp": "2024-01-01T00:00:00"
                }
                approval = await controller._interactive_approval(request)

                # Check that SQL analysis was printed
                printed_text = " ".join([str(call[0][0]) for call in mock_print.call_args_list])
                assert "SQL Analysis" in printed_text

        assert approval["approved"] is True

    async def test_interactive_approval_with_long_param_values(self):
        """Test interactive approval truncates long parameter values"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        step = {
            "tool": "test",
            "params": {"long_value": "x" * 200}
        }
        validation = {
            "risk_level": "medium",
            "approval_requirement": ApprovalRequirement.OPTIONAL,
            "risks": [],
            "mitigations": []
        }

        with patch("builtins.input", return_value="yes"):
            with patch("builtins.print") as mock_print:
                request = {
                    "step": step,
                    "validation": validation,
                    "timestamp": "2024-01-01T00:00:00"
                }
                await controller._interactive_approval(request)

                # Check truncation occurred
                printed_text = " ".join([str(call[0][0]) for call in mock_print.call_args_list])
                assert "..." in printed_text


class TestApprovalHistory:
    """Test approval history management"""

    def test_get_approval_history_empty(self):
        """Test getting history when empty"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        history = controller.get_approval_history()

        assert history == []

    def test_get_approval_history_with_limit(self):
        """Test getting history with limit"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        # Add some history
        for i in range(10):
            controller.approval_history.append({
                "request": {},
                "approval": {"approved": True},
                "decision_timestamp": f"2024-01-{i+1:02d}"
            })

        history = controller.get_approval_history(limit=5)

        assert len(history) == 5

    def test_get_approval_history_approved_only(self):
        """Test filtering for approved only"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        controller.approval_history.extend([
            {"request": {}, "approval": {"approved": True}},
            {"request": {}, "approval": {"approved": False}},
            {"request": {}, "approval": {"approved": True}},
            {"request": {}, "approval": {"approved": False}},
        ])

        history = controller.get_approval_history(approved_only=True)

        assert len(history) == 2
        assert all(h["approval"]["approved"] for h in history)

    def test_get_approval_history_approved_only_with_limit(self):
        """Test approved only with limit"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        for i in range(10):
            controller.approval_history.append({
                "request": {},
                "approval": {"approved": i % 2 == 0}
            })

        history = controller.get_approval_history(limit=3, approved_only=True)

        assert len(history) == 3
        assert all(h["approval"]["approved"] for h in history)

    def test_clear_approval_history(self):
        """Test clearing approval history"""
        risk_analyzer = Mock(spec=SQLRiskAnalyzer)
        controller = SafetyController(risk_analyzer)

        controller.approval_history.extend([
            {"request": {}, "approval": {"approved": True}},
            {"request": {}, "approval": {"approved": False}},
        ])

        assert len(controller.approval_history) == 2

        controller.clear_approval_history()

        assert len(controller.approval_history) == 0


class TestApprovalRequirementEnum:
    """Test ApprovalRequirement enum"""

    def test_all_approval_requirements(self):
        """Test all approval requirement values"""
        assert ApprovalRequirement.NONE.value == "none"
        assert ApprovalRequirement.OPTIONAL.value == "optional"
        assert ApprovalRequirement.REQUIRED.value == "required"
        assert ApprovalRequirement.MULTI_PARTY.value == "multi_party"


class TestSafetyLevelEnum:
    """Test SafetyLevel enum"""

    def test_all_safety_levels(self):
        """Test all safety level values"""
        assert SafetyLevel.LOW.value == "low"
        assert SafetyLevel.MEDIUM.value == "medium"
        assert SafetyLevel.HIGH.value == "high"
        assert SafetyLevel.CRITICAL.value == "critical"
