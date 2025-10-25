"""Comprehensive tests for agent safety controller"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.agents.safety.controller import (
    SafetyController,
    SafetyLevel,
    SafetyViolation,
    SafetyPolicy,
    ApprovalRequirement
)
from src.agents.base import AgentConfig, AgentCapability
from src.agents.tools.registry import ToolRiskLevel, ToolCategory


@pytest.fixture
def mock_tool_definition_safe():
    """Mock safe tool definition"""
    tool = Mock()
    tool.risk_level = ToolRiskLevel.LOW
    tool.requires_approval = False
    tool.category = ToolCategory.DATABASE_READ
    return tool


@pytest.fixture
def mock_tool_definition_write():
    """Mock write tool definition"""
    tool = Mock()
    tool.risk_level = ToolRiskLevel.MEDIUM
    tool.requires_approval = False
    tool.category = ToolCategory.DATABASE_WRITE
    return tool


@pytest.fixture
def mock_tool_definition_ddl():
    """Mock DDL tool definition"""
    tool = Mock()
    tool.risk_level = ToolRiskLevel.HIGH
    tool.requires_approval = True
    tool.category = ToolCategory.DATABASE_DDL
    return tool


@pytest.fixture
def mock_tool_definition_critical():
    """Mock critical tool definition"""
    tool = Mock()
    tool.risk_level = ToolRiskLevel.CRITICAL
    tool.requires_approval = True
    tool.category = ToolCategory.DATABASE_DDL
    return tool


@pytest.fixture
def safety_controller(mock_sql_risk_analyzer):
    """Safety controller instance with mock analyzer"""
    return SafetyController(risk_analyzer=mock_sql_risk_analyzer)


def test_safety_controller_initialization(mock_sql_risk_analyzer):
    """Test safety controller initialization"""
    controller = SafetyController(risk_analyzer=mock_sql_risk_analyzer)
    assert controller.risk_analyzer is not None
    assert controller.approval_history == []


def test_validate_safe_query(safety_controller, mock_agent_config_moderate, mock_tool_definition_safe):
    """Test validation of safe query"""
    step = {
        'tool': 'read_table',
        'params': {'table': 'users'},
        'tool_definition': mock_tool_definition_safe
    }

    result = safety_controller.validate_step(step, mock_agent_config_moderate)

    assert result['safe'] is True
    assert result['requires_approval'] is False
    assert result['risk_level'] == 'low'


def test_detect_drop_table(safety_controller, mock_agent_config_moderate, mock_tool_definition_ddl):
    """Test detection of DROP TABLE command"""
    step = {
        'tool': 'execute_migration',
        'params': {'sql': 'DROP TABLE users'},
        'tool_definition': mock_tool_definition_ddl
    }

    result = safety_controller.validate_step(step, mock_agent_config_moderate)

    assert result['requires_approval'] is True
    assert result['sql_analysis']['risk_level'] == 'CRITICAL'


def test_detect_delete_without_where(safety_controller, mock_agent_config_moderate, mock_tool_definition_write):
    """Test detection of DELETE without WHERE"""
    step = {
        'tool': 'execute_query',
        'params': {'sql': 'DELETE FROM users'},
        'tool_definition': mock_tool_definition_write
    }

    result = safety_controller.validate_step(step, mock_agent_config_moderate)

    assert result['requires_approval'] is True
    assert result['sql_analysis']['risk_level'] == 'HIGH'


def test_detect_update_without_where(safety_controller, mock_agent_config_moderate, mock_tool_definition_write):
    """Test detection of UPDATE without WHERE"""
    step = {
        'tool': 'execute_query',
        'params': {'sql': 'UPDATE users SET active = 0'},
        'tool_definition': mock_tool_definition_write
    }

    result = safety_controller.validate_step(step, mock_agent_config_moderate)

    assert result['requires_approval'] is True
    assert result['sql_analysis']['risk_level'] == 'HIGH'


def test_allow_safe_delete_with_where(safety_controller, mock_agent_config_moderate, mock_tool_definition_write):
    """Test allowing DELETE with WHERE clause"""
    step = {
        'tool': 'execute_query',
        'params': {'sql': 'DELETE FROM users WHERE id = 123'},
        'tool_definition': mock_tool_definition_write
    }

    result = safety_controller.validate_step(step, mock_agent_config_moderate)

    # Safe enough for moderate mode
    assert result['sql_analysis']['risk_level'] == 'LOW'


def test_detect_sql_injection(safety_controller, mock_agent_config_moderate, mock_tool_definition_write):
    """Test detection of SQL injection patterns"""
    step = {
        'tool': 'execute_query',
        'params': {'sql': "SELECT * FROM users WHERE name = ''; DROP TABLE users; --'"},
        'tool_definition': mock_tool_definition_write
    }

    result = safety_controller.validate_step(step, mock_agent_config_moderate)

    assert result['requires_approval'] is True
    assert result['sql_analysis']['risk_level'] == 'CRITICAL'


def test_validation_with_strict_safety(safety_controller, mock_agent_config_strict, mock_tool_definition_ddl):
    """Test strict safety level blocks high-risk operations"""
    step = {
        'tool': 'create_index',  # Non-destructive DDL operation
        'params': {'sql': 'CREATE INDEX idx_users_email ON users(email)'},
        'tool_definition': mock_tool_definition_ddl
    }

    result = safety_controller.validate_step(step, mock_agent_config_strict)

    assert result['requires_approval'] is True
    # Strict mode requires approval for HIGH risk operations
    assert result['approval_requirement'] in [ApprovalRequirement.REQUIRED, ApprovalRequirement.MULTI_PARTY]


def test_validation_with_moderate_safety(safety_controller, mock_agent_config_moderate, mock_tool_definition_write):
    """Test moderate safety level allows medium-risk operations"""
    step = {
        'tool': 'update_row',
        'params': {'sql': 'UPDATE users SET last_login = NOW() WHERE id = 1'},
        'tool_definition': mock_tool_definition_write
    }

    result = safety_controller.validate_step(step, mock_agent_config_moderate)

    # Medium risk operations don't require approval in moderate mode
    assert result['risk_level'] == 'medium'


def test_validation_with_permissive_safety(safety_controller, mock_agent_config_permissive, mock_tool_definition_write):
    """Test permissive safety level allows more operations"""
    step = {
        'tool': 'bulk_update',
        'params': {'sql': 'UPDATE temp_data SET processed = true'},
        'tool_definition': mock_tool_definition_write
    }

    result = safety_controller.validate_step(step, mock_agent_config_permissive)

    # Permissive mode is more lenient
    assert result['risk_level'] == 'medium'


def test_destructive_operation_detection(safety_controller, mock_agent_config_moderate, mock_tool_definition_ddl):
    """Test detection of destructive operations"""
    step = {
        'tool': 'drop_table',
        'params': {'table_name': 'old_data'},
        'tool_definition': mock_tool_definition_ddl
    }

    result = safety_controller.validate_step(step, mock_agent_config_moderate)

    assert result['requires_approval'] is True
    assert result['approval_requirement'] == ApprovalRequirement.MULTI_PARTY


def test_ddl_operations_require_approval(safety_controller, mock_agent_config_moderate, mock_tool_definition_ddl):
    """Test that DDL operations always require approval"""
    step = {
        'tool': 'create_index',
        'params': {'sql': 'CREATE INDEX idx_users_email ON users(email)'},
        'tool_definition': mock_tool_definition_ddl
    }

    result = safety_controller.validate_step(step, mock_agent_config_moderate)

    assert result['requires_approval'] is True


@pytest.mark.asyncio
async def test_approval_with_callback(safety_controller, mock_agent_config_moderate, mock_tool_definition_critical):
    """Test approval request with custom callback"""
    step = {
        'tool': 'drop_database',
        'params': {'database': 'test_db'},
        'tool_definition': mock_tool_definition_critical
    }

    validation = safety_controller.validate_step(step, mock_agent_config_moderate)

    # Mock approval callback
    async def mock_approval_callback(request):
        return {
            'approved': True,
            'reason': 'Approved by test',
            'approver': 'test_user',
            'timestamp': datetime.utcnow().isoformat(),
            'conditions': []
        }

    approval = await safety_controller.request_approval(
        step,
        validation,
        approval_callback=mock_approval_callback
    )

    assert approval['approved'] is True
    assert approval['approver'] == 'test_user'
    assert len(safety_controller.approval_history) == 1


@pytest.mark.asyncio
async def test_approval_rejection(safety_controller, mock_agent_config_moderate, mock_tool_definition_critical):
    """Test approval rejection"""
    step = {
        'tool': 'truncate_table',
        'params': {'table': 'important_data'},
        'tool_definition': mock_tool_definition_critical
    }

    validation = safety_controller.validate_step(step, mock_agent_config_moderate)

    # Mock rejection callback
    async def mock_approval_callback(request):
        return {
            'approved': False,
            'reason': 'Too risky for production',
            'approver': 'test_user',
            'timestamp': datetime.utcnow().isoformat(),
            'conditions': []
        }

    approval = await safety_controller.request_approval(
        step,
        validation,
        approval_callback=mock_approval_callback
    )

    assert approval['approved'] is False
    assert 'risky' in approval['reason'].lower()


def test_approval_history_tracking(safety_controller):
    """Test approval history is properly tracked"""
    # Initially empty
    assert len(safety_controller.approval_history) == 0

    # History tracked after approval
    assert safety_controller.get_approval_history() == []


def test_get_approval_history_with_limit(safety_controller):
    """Test getting approval history with limit"""
    # Add mock history entries
    for i in range(10):
        safety_controller.approval_history.append({
            'request': {'step': f'step_{i}'},
            'approval': {'approved': i % 2 == 0},
            'decision_timestamp': datetime.utcnow().isoformat()
        })

    # Get last 5 entries
    history = safety_controller.get_approval_history(limit=5)
    assert len(history) == 5


def test_get_approval_history_approved_only(safety_controller):
    """Test filtering approved operations only"""
    # Add mock history entries
    for i in range(5):
        safety_controller.approval_history.append({
            'request': {'step': f'step_{i}'},
            'approval': {'approved': i % 2 == 0},
            'decision_timestamp': datetime.utcnow().isoformat()
        })

    # Get only approved
    history = safety_controller.get_approval_history(approved_only=True)
    assert len(history) == 3  # 0, 2, 4 are approved


def test_clear_approval_history(safety_controller):
    """Test clearing approval history"""
    # Add some entries
    safety_controller.approval_history.append({'test': 'data'})
    assert len(safety_controller.approval_history) == 1

    # Clear
    safety_controller.clear_approval_history()
    assert len(safety_controller.approval_history) == 0


def test_missing_tool_definition(safety_controller, mock_agent_config_moderate):
    """Test handling of missing tool definition"""
    step = {
        'tool': 'unknown_tool',
        'params': {}
        # No tool_definition
    }

    result = safety_controller.validate_step(step, mock_agent_config_moderate)

    assert result['risk_level'] == 'unknown'
    assert result['requires_approval'] is True
    assert result['approval_requirement'] == ApprovalRequirement.REQUIRED


def test_sql_analysis_integration(safety_controller, mock_agent_config_moderate, mock_tool_definition_write):
    """Test SQL analysis is properly integrated into validation"""
    # Test multiple SQL patterns
    test_cases = [
        ('SELECT * FROM users WHERE id = 1', 'LOW', False),
        ('UPDATE users SET active = 1 WHERE id = 1', 'LOW', False),
        ('DELETE FROM logs WHERE created < NOW() - INTERVAL 30 DAY', 'LOW', False),
        ('DELETE FROM users', 'HIGH', True),
        ('TRUNCATE TABLE temp_data', 'HIGH', True),
        ('DROP TABLE old_data', 'CRITICAL', True),
    ]

    for sql, expected_risk, should_require_approval in test_cases:
        step = {
            'tool': 'execute_query',
            'params': {'sql': sql},
            'tool_definition': mock_tool_definition_write
        }

        result = safety_controller.validate_step(step, mock_agent_config_moderate)

        assert 'sql_analysis' in result
        assert result['sql_analysis']['risk_level'] == expected_risk

        # High and Critical risk should require approval
        if should_require_approval:
            assert result['requires_approval'] is True
