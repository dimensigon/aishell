"""
Comprehensive tests for Phase 12 safety and approval system.

Tests cover:
- Risk assessment (automatic evaluation)
- Approval workflow (human-in-the-loop)
- SQL analysis (deep inspection)
- Audit logging (complete trail)
- Safety constraints (rules and policies)
- Multi-layer protection (sanitization, injection prevention, path traversal, credential redaction)
- Real database operations (DDL, DML, DROP)
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

# Import safety controller and dependencies
from src.agents.safety.controller import (
    SafetyController,
    SafetyLevel,
    SafetyPolicy,
    SafetyViolation,
    ApprovalRequirement
)
from src.database.risk_analyzer import SQLRiskAnalyzer, RiskLevel
from src.agents.base import AgentConfig
from src.agents.tools.registry import ToolRiskLevel, ToolCategory

# Import security modules for multi-layer protection tests
from src.security.sql_guard import SQLGuard
from src.security.command_sanitizer import CommandSanitizer, SecurityError
from src.security.path_validator import safe_path_join, validate_vault_path, SecurityError as PathSecurityError
from src.security.redaction import RedactionEngine, RedactionService
from src.security.sanitization import sanitize_sql_input, sanitize_input
from src.security.validation import validate_email, validate_sql_identifier, validate_query_length
from src.security.audit import AuditLogger, TamperProofLogger


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def risk_analyzer():
    """Fixture for SQL risk analyzer."""
    return SQLRiskAnalyzer()


@pytest.fixture
def safety_controller(risk_analyzer):
    """Fixture for safety controller."""
    return SafetyController(risk_analyzer)


@pytest.fixture
def agent_config_strict():
    """Fixture for agent config with strict safety level."""
    from src.agents.base import AgentCapability
    return AgentConfig(
        agent_id="test_agent_001",
        agent_type="database",
        capabilities=[AgentCapability.DATABASE_READ, AgentCapability.DATABASE_WRITE, AgentCapability.DATABASE_DDL],
        llm_config={'model': 'gpt-4', 'temperature': 0.1},
        safety_level="strict"
    )


@pytest.fixture
def agent_config_moderate():
    """Fixture for agent config with moderate safety level."""
    from src.agents.base import AgentCapability
    return AgentConfig(
        agent_id="test_agent_002",
        agent_type="database",
        capabilities=[AgentCapability.DATABASE_READ, AgentCapability.DATABASE_WRITE],
        llm_config={'model': 'gpt-4', 'temperature': 0.3},
        safety_level="moderate"
    )


@pytest.fixture
def agent_config_permissive():
    """Fixture for agent config with permissive safety level."""
    from src.agents.base import AgentCapability
    return AgentConfig(
        agent_id="test_agent_003",
        agent_type="database",
        capabilities=[AgentCapability.DATABASE_READ, AgentCapability.DATABASE_WRITE, AgentCapability.DATABASE_DDL],
        llm_config={'model': 'gpt-4', 'temperature': 0.5},
        safety_level="permissive"
    )


@pytest.fixture
def sql_guard():
    """Fixture for SQL guard."""
    return SQLGuard()


@pytest.fixture
def audit_logger():
    """Fixture for basic audit logger."""
    return AuditLogger(retention_days=90)


@pytest.fixture
def tamper_proof_logger():
    """Fixture for tamper-proof audit logger."""
    return TamperProofLogger(retention_days=90)


@pytest.fixture
def redaction_engine():
    """Fixture for redaction engine."""
    return RedactionEngine()


# ============================================================================
# TEST RISK ASSESSMENT - AUTOMATIC EVALUATION
# ============================================================================

class TestRiskAssessment:
    """Test automatic risk assessment capabilities."""

    def test_low_risk_select_query(self, safety_controller, agent_config_moderate):
        """Test that SELECT queries are assessed as LOW risk."""
        # Create a mock tool definition for SELECT operation
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.LOW
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_READ

        step = {
            'tool': 'execute_query',
            'params': {'sql': 'SELECT * FROM users WHERE id = 1;'},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_moderate)

        assert validation['safe'] is True
        assert validation['risk_level'] == 'low'
        assert validation['requires_approval'] is False
        assert validation['approval_requirement'] == ApprovalRequirement.NONE

    def test_medium_risk_insert_query(self, safety_controller, agent_config_moderate):
        """Test that INSERT queries are assessed as MEDIUM risk."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.MEDIUM
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_WRITE

        step = {
            'tool': 'execute_insert',
            'params': {'sql': 'INSERT INTO users (name) VALUES (\'John\');'},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_moderate)

        assert validation['safe'] is True
        assert validation['risk_level'] == 'medium'
        assert 'Data modification operation' in validation['risks']

    def test_high_risk_update_without_where(self, safety_controller, agent_config_strict):
        """Test that UPDATE without WHERE clause is HIGH risk."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.MEDIUM
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_WRITE

        step = {
            'tool': 'execute_update',
            'params': {'sql': 'UPDATE users SET active = 1;'},  # No WHERE clause
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        # SQL analysis should detect HIGH risk
        assert 'sql_analysis' in validation
        assert validation['sql_analysis']['risk_level'] in ['HIGH', 'CRITICAL']
        assert validation['requires_approval'] is True

    def test_critical_risk_drop_table(self, safety_controller, agent_config_strict):
        """Test that DROP TABLE is CRITICAL risk."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.CRITICAL
        mock_tool.requires_approval = True
        mock_tool.category = ToolCategory.DATABASE_DDL

        step = {
            'tool': 'drop_table',
            'params': {'sql': 'DROP TABLE users;'},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        assert validation['risk_level'] == 'critical'
        assert validation['requires_approval'] is True
        assert validation['approval_requirement'] == ApprovalRequirement.MULTI_PARTY
        assert safety_controller._is_destructive_operation(step) is True

    def test_risk_escalation_based_on_sql_analysis(self, safety_controller, agent_config_moderate):
        """Test that risk level escalates based on SQL analysis."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.LOW
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_WRITE

        # SQL contains dangerous pattern
        step = {
            'tool': 'execute_query',
            'params': {'sql': "SELECT * FROM users WHERE username = '' OR '1'='1';"},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_moderate)

        # Should detect SQL injection and escalate
        assert 'sql_analysis' in validation
        # The sql_analysis returns a dict from the risk_analyzer.analyze() method
        # which has risk_level, requires_confirmation, warnings, issues
        sql_analysis = validation['sql_analysis']
        assert sql_analysis['risk_level'] in ['HIGH', 'CRITICAL'] or len(sql_analysis.get('issues', [])) > 0

    def test_destructive_operation_detection(self, safety_controller, agent_config_moderate):
        """Test detection of destructive operations."""
        # Test various destructive operations
        destructive_tools = [
            'execute_migration',
            'drop_table',
            'drop_database',
            'truncate_table',
            'drop_index'
        ]

        for tool_name in destructive_tools:
            mock_tool = Mock()
            mock_tool.risk_level = ToolRiskLevel.CRITICAL
            mock_tool.requires_approval = True
            mock_tool.category = ToolCategory.DATABASE_DDL

            step = {
                'tool': tool_name,
                'params': {},
                'tool_definition': mock_tool
            }

            assert safety_controller._is_destructive_operation(step) is True

    def test_safety_level_enforcement_strict(self, safety_controller, agent_config_strict):
        """Test strict safety level enforcement."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.HIGH
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_WRITE

        step = {
            'tool': 'execute_update',
            'params': {'sql': 'UPDATE users SET active = 1 WHERE id = 1;'},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        # Strict mode requires approval for HIGH risk
        assert validation['requires_approval'] is True
        assert validation['approval_requirement'] == ApprovalRequirement.REQUIRED

    def test_safety_level_enforcement_moderate(self, safety_controller, agent_config_moderate):
        """Test moderate safety level enforcement."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.HIGH
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_WRITE

        step = {
            'tool': 'execute_update',
            'params': {'sql': 'UPDATE users SET active = 1 WHERE id = 1;'},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_moderate)

        # Moderate mode makes HIGH risk optional approval
        assert validation['approval_requirement'] == ApprovalRequirement.OPTIONAL


# ============================================================================
# TEST APPROVAL WORKFLOW - HUMAN-IN-THE-LOOP
# ============================================================================

class TestApprovalWorkflow:
    """Test human-in-the-loop approval mechanisms."""

    @pytest.mark.asyncio
    async def test_approval_with_custom_callback(self, safety_controller, agent_config_strict):
        """Test approval workflow with custom callback."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.CRITICAL
        mock_tool.requires_approval = True
        mock_tool.category = ToolCategory.DATABASE_DDL

        step = {
            'tool': 'drop_table',
            'params': {'sql': 'DROP TABLE old_data;'},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        # Custom approval callback that approves
        async def approve_callback(request):
            return {
                'approved': True,
                'reason': 'Approved by automated test',
                'approver': 'test_system',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': ['Backup verified']
            }

        approval = await safety_controller.request_approval(step, validation, approve_callback)

        assert approval['approved'] is True
        assert approval['approver'] == 'test_system'
        assert 'Backup verified' in approval['conditions']

    @pytest.mark.asyncio
    async def test_approval_rejection(self, safety_controller, agent_config_strict):
        """Test approval workflow rejection."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.CRITICAL
        mock_tool.requires_approval = True
        mock_tool.category = ToolCategory.DATABASE_DDL

        step = {
            'tool': 'drop_database',
            'params': {'database': 'production'},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        # Custom callback that rejects
        async def reject_callback(request):
            return {
                'approved': False,
                'reason': 'Production database cannot be dropped',
                'approver': 'test_system',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': []
            }

        approval = await safety_controller.request_approval(step, validation, reject_callback)

        assert approval['approved'] is False
        assert 'Production database' in approval['reason']

    @pytest.mark.asyncio
    async def test_approval_history_tracking(self, safety_controller, agent_config_strict):
        """Test that approval history is properly tracked."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.HIGH
        mock_tool.requires_approval = True
        mock_tool.category = ToolCategory.DATABASE_WRITE

        step = {
            'tool': 'execute_migration',
            'params': {'sql': 'ALTER TABLE users ADD COLUMN email VARCHAR(255);'},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        async def approve_callback(request):
            return {
                'approved': True,
                'reason': 'Schema migration approved',
                'approver': 'dba_team',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': []
            }

        # Make approval request
        await safety_controller.request_approval(step, validation, approve_callback)

        # Check history
        history = safety_controller.get_approval_history()
        assert len(history) > 0

        last_approval = history[-1]
        assert 'request' in last_approval
        assert 'approval' in last_approval
        assert 'decision_timestamp' in last_approval
        assert last_approval['approval']['approved'] is True

    @pytest.mark.asyncio
    async def test_multi_party_approval_requirement(self, safety_controller, agent_config_strict):
        """Test multi-party approval for destructive operations."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.CRITICAL
        mock_tool.requires_approval = True
        mock_tool.category = ToolCategory.DATABASE_DDL

        step = {
            'tool': 'truncate_table',
            'params': {'sql': 'TRUNCATE TABLE transactions;'},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        # Destructive operations require multi-party approval
        assert validation['approval_requirement'] == ApprovalRequirement.MULTI_PARTY
        assert 'Multi-party approval required' in validation['mitigations']

    @pytest.mark.asyncio
    async def test_approval_with_conditions(self, safety_controller, agent_config_strict):
        """Test approval with specific conditions attached."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.HIGH
        mock_tool.requires_approval = True
        mock_tool.category = ToolCategory.DATABASE_WRITE

        step = {
            'tool': 'execute_update',
            'params': {'sql': 'UPDATE orders SET status = \'cancelled\' WHERE user_id = 123;'},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        async def conditional_approval(request):
            return {
                'approved': True,
                'reason': 'Approved with conditions',
                'approver': 'supervisor',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': [
                    'Must execute in transaction',
                    'Must verify backup before execution',
                    'Must notify users of cancellation'
                ]
            }

        approval = await safety_controller.request_approval(step, validation, conditional_approval)

        assert approval['approved'] is True
        assert len(approval['conditions']) == 3
        assert 'Must execute in transaction' in approval['conditions']


# ============================================================================
# TEST SQL ANALYSIS - DEEP INSPECTION
# ============================================================================

class TestSQLAnalysis:
    """Test SQL-specific deep inspection and injection detection."""

    def test_sql_injection_detection_or_1_equals_1(self, sql_guard):
        """Test detection of classic OR 1=1 injection."""
        malicious_sql = "SELECT * FROM users WHERE username = 'admin' OR '1'='1';"

        result = sql_guard.validate_query(malicious_sql)

        assert result['is_safe'] is False
        assert result['threat_type'] == 'SQL Injection'
        assert result['severity'] == 'critical'

    def test_sql_injection_detection_union_select(self, sql_guard):
        """Test detection of UNION SELECT injection."""
        malicious_sql = "SELECT id FROM users UNION SELECT password FROM admin_users;"

        result = sql_guard.validate_query(malicious_sql)

        assert result['is_safe'] is False
        assert 'injection_pattern' in result['threats_detected'][0]['type']

    def test_sql_injection_detection_comment_evasion(self, sql_guard):
        """Test detection of comment-based evasion."""
        malicious_sql = "SELECT * FROM users WHERE id = 1; -- DROP TABLE users;"

        result = sql_guard.validate_query(malicious_sql)

        assert result['is_safe'] is False
        # Should detect either injection pattern or dangerous comments

    def test_sql_injection_detection_stacked_queries(self, sql_guard):
        """Test detection of stacked query injection."""
        malicious_sql = "SELECT * FROM users WHERE id = 1; DROP TABLE users;"

        result = sql_guard.validate_query(malicious_sql)

        assert result['is_safe'] is False
        assert result['threat_type'] == 'SQL Injection'

    def test_dangerous_keyword_detection(self, sql_guard):
        """Test detection of dangerous SQL keywords."""
        dangerous_queries = [
            "DROP TABLE users;",
            "TRUNCATE TABLE sessions;",
            "ALTER TABLE users DROP COLUMN password;",
            "EXEC sp_executesql @query;",
            "EXECUTE xp_cmdshell 'dir';"
        ]

        for query in dangerous_queries:
            result = sql_guard.validate_query(query)
            assert len(result['threats_detected']) > 0

    def test_parameterization_check(self, sql_guard):
        """Test detection of parameterized queries."""
        # Parameterized query
        safe_query = "SELECT * FROM users WHERE id = ?;"
        assert sql_guard.check_parameterization(safe_query) is True

        # Non-parameterized query
        unsafe_query = "SELECT * FROM users WHERE id = 1;"
        assert sql_guard.check_parameterization(unsafe_query) is False

    def test_parameterization_suggestion(self, sql_guard):
        """Test parameterization suggestions."""
        query = "SELECT * FROM users WHERE name = 'John' AND age = '25';"

        suggestion = sql_guard.suggest_parameterization(query)

        assert suggestion['parameterized'] is not None
        assert len(suggestion['parameters']) == 2
        assert ':param1' in suggestion['parameterized']
        assert ':param2' in suggestion['parameterized']

    def test_sql_keyword_detection(self, sql_guard):
        """Test SQL keyword detection in text."""
        text = "We need to SELECT data and UPDATE the records, then DROP the old table."

        keywords = sql_guard.detect_sql_keywords(text)

        assert 'SELECT' in keywords
        assert 'UPDATE' in keywords
        assert 'DROP' in keywords

    def test_input_sanitization(self, sql_guard):
        """Test SQL input sanitization."""
        dangerous_input = "admin'; DROP TABLE users;--"

        sanitized = sql_guard.sanitize_input(dangerous_input)

        # Should escape quotes and remove dangerous characters
        assert "'" not in sanitized or "''" in sanitized
        assert '--' not in sanitized


# ============================================================================
# TEST AUDIT LOGGING - COMPLETE TRAIL
# ============================================================================

class TestAuditLogging:
    """Test comprehensive audit logging capabilities."""

    def test_basic_audit_logging(self, audit_logger):
        """Test basic audit log creation."""
        log = audit_logger.log_action(
            user='test_user',
            action='execute_query',
            resource='users_table',
            details={'sql': 'SELECT * FROM users;'}
        )

        assert log.user == 'test_user'
        assert log.action == 'execute_query'
        assert log.resource == 'users_table'
        assert 'sql' in log.details

    def test_audit_log_search_by_user(self, audit_logger):
        """Test searching audit logs by user."""
        audit_logger.log_action('user1', 'action1', 'resource1')
        audit_logger.log_action('user2', 'action2', 'resource2')
        audit_logger.log_action('user1', 'action3', 'resource3')

        results = audit_logger.search_logs(user='user1')

        assert len(results) == 2
        assert all(log['user'] == 'user1' for log in results)

    def test_audit_log_search_by_action(self, audit_logger):
        """Test searching audit logs by action."""
        audit_logger.log_action('user1', 'execute_query', 'resource1')
        audit_logger.log_action('user2', 'execute_migration', 'resource2')
        audit_logger.log_action('user3', 'execute_query', 'resource3')

        results = audit_logger.search_logs(action='execute_query')

        assert len(results) == 2
        assert all(log['action'] == 'execute_query' for log in results)

    def test_audit_log_search_by_date_range(self, audit_logger):
        """Test searching audit logs by date range."""
        from datetime import timedelta

        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        # Log with specific timestamp
        audit_logger.log_action('user1', 'action1', 'resource1', timestamp=now)

        # Search for logs from yesterday to tomorrow
        results = audit_logger.search_logs(start_date=yesterday, end_date=tomorrow)

        assert len(results) >= 1

    def test_audit_log_statistics(self, audit_logger):
        """Test audit log statistics generation."""
        audit_logger.log_action('user1', 'action1', 'resource1')
        audit_logger.log_action('user2', 'action2', 'resource2')
        audit_logger.log_action('user1', 'action1', 'resource3')

        stats = audit_logger.get_statistics()

        assert stats['total_logs'] == 3
        assert stats['unique_users'] == 2
        assert stats['unique_actions'] == 2

    def test_tamper_proof_logging_hash_chain(self, tamper_proof_logger):
        """Test tamper-proof logging with hash chains."""
        log1 = tamper_proof_logger.log_action('user1', 'action1', 'resource1')
        log2 = tamper_proof_logger.log_action('user2', 'action2', 'resource2')

        # Both logs should have hashes
        assert log1.hash is not None
        assert log2.hash is not None

        # Hashes should be different
        assert log1.hash != log2.hash

    def test_tamper_proof_chain_integrity_verification(self, tamper_proof_logger):
        """Test verification of tamper-proof log chain integrity."""
        # Create several logs
        tamper_proof_logger.log_action('user1', 'action1', 'resource1')
        tamper_proof_logger.log_action('user2', 'action2', 'resource2')
        tamper_proof_logger.log_action('user3', 'action3', 'resource3')

        # Verify chain integrity
        verification = tamper_proof_logger.verify_chain_integrity()

        assert verification['valid'] is True
        assert verification['total_logs'] == 3
        assert len(verification['invalid_logs']) == 0

    def test_audit_log_export_json(self, audit_logger):
        """Test audit log export in JSON format."""
        audit_logger.log_action('user1', 'action1', 'resource1')
        audit_logger.log_action('user2', 'action2', 'resource2')

        export = audit_logger.export_logs(format='json')

        assert 'export_date' in export
        assert 'log_count' in export
        assert '"user1"' in export
        assert '"user2"' in export

    def test_audit_log_export_csv(self, audit_logger):
        """Test audit log export in CSV format."""
        audit_logger.log_action('user1', 'action1', 'resource1')
        audit_logger.log_action('user2', 'action2', 'resource2')

        export = audit_logger.export_logs(format='csv')

        # Should have header and data rows
        lines = export.split('\n')
        assert len(lines) >= 3  # Header + 2 data rows
        assert 'timestamp,user,action,resource' in lines[0]

    def test_audit_log_retention(self, audit_logger):
        """Test audit log retention policy."""
        from datetime import timedelta

        old_date = datetime.now() - timedelta(days=100)

        # Create old log
        audit_logger.log_action('user1', 'action1', 'resource1', timestamp=old_date)

        # Create recent log
        audit_logger.log_action('user2', 'action2', 'resource2')

        # Cleanup old logs (retention is 90 days)
        removed = audit_logger.cleanup_old_logs()

        assert removed >= 1


# ============================================================================
# TEST SAFETY CONSTRAINTS - RULES AND POLICIES
# ============================================================================

class TestSafetyConstraints:
    """Test safety rules and policy enforcement."""

    def test_safety_policy_blocked_operations(self):
        """Test safety policy with blocked operations."""
        policy = SafetyPolicy(
            safety_level=SafetyLevel.HIGH,
            blocked_operations=['drop_database', 'truncate_table']
        )

        assert policy.is_operation_allowed('execute_query') is True
        assert policy.is_operation_allowed('drop_database') is False
        assert policy.is_operation_allowed('truncate_table') is False

    def test_safety_policy_required_approval(self):
        """Test safety policy with required approvals."""
        policy = SafetyPolicy(
            safety_level=SafetyLevel.MEDIUM,
            require_approval_for=['execute_migration', 'alter_table']
        )

        assert policy.requires_approval('execute_query') is False
        assert policy.requires_approval('execute_migration') is True
        assert policy.requires_approval('alter_table') is True

    def test_safety_policy_destructive_operations(self):
        """Test safety policy for destructive operations."""
        # Policy that disallows destructive operations
        strict_policy = SafetyPolicy(
            safety_level=SafetyLevel.CRITICAL,
            allow_destructive=False
        )

        assert strict_policy.allow_destructive is False

        # Policy that allows destructive operations
        permissive_policy = SafetyPolicy(
            safety_level=SafetyLevel.LOW,
            allow_destructive=True
        )

        assert permissive_policy.allow_destructive is True

    def test_validation_without_tool_definition(self, safety_controller, agent_config_moderate):
        """Test validation when tool definition is missing."""
        step = {
            'tool': 'unknown_tool',
            'params': {}
            # No tool_definition
        }

        validation = safety_controller.validate_step(step, agent_config_moderate)

        # Should apply conservative defaults
        assert validation['risk_level'] == 'unknown'
        assert validation['requires_approval'] is True
        assert validation['approval_requirement'] == ApprovalRequirement.REQUIRED

    def test_ddl_operations_always_require_approval(self, safety_controller, agent_config_permissive):
        """Test that DDL operations always require approval even in permissive mode."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.MEDIUM
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_DDL

        step = {
            'tool': 'alter_table',
            'params': {'sql': 'ALTER TABLE users ADD COLUMN email VARCHAR(255);'},
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_permissive)

        # DDL always requires approval
        assert validation['requires_approval'] is True
        assert validation['approval_requirement'] == ApprovalRequirement.REQUIRED


# ============================================================================
# TEST MULTI-LAYER PROTECTION
# ============================================================================

class TestMultiLayerProtection:
    """Test multi-layer security protection mechanisms."""

    def test_command_sanitization_blocked_commands(self):
        """Test that dangerous commands are blocked."""
        dangerous_commands = [
            'rm -rf /',
            'dd if=/dev/zero of=/dev/sda',
            'mkfs.ext4 /dev/sda1',
            'shutdown -h now'
        ]

        for cmd in dangerous_commands:
            is_safe, error = CommandSanitizer.is_safe_command(cmd)
            assert is_safe is False
            assert error is not None

    def test_command_sanitization_safe_commands(self):
        """Test that safe commands pass sanitization."""
        safe_commands = [
            'ls -la',
            'cat file.txt',
            'python script.py',
            'git status'
        ]

        for cmd in safe_commands:
            is_safe, error = CommandSanitizer.is_safe_command(cmd)
            assert is_safe is True
            assert error is None

    def test_command_sanitization_dangerous_patterns(self):
        """Test detection of dangerous command patterns."""
        patterns = [
            'rm -rf *',
            'echo "malicious" | bash',
            'cat file.txt; rm file.txt',
            'ls && rm -rf temp'
        ]

        for pattern in patterns:
            with pytest.raises(SecurityError):
                CommandSanitizer.sanitize_command(pattern)

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        import tempfile
        base_dir = tempfile.mkdtemp()

        # Attempt path traversal
        with pytest.raises(PathSecurityError):
            safe_path_join(base_dir, '../../../etc/passwd')

        # Normal path should work
        safe_path = safe_path_join(base_dir, 'subdir/file.txt')
        assert str(safe_path).startswith(base_dir)

    def test_credential_redaction_passwords(self, redaction_engine):
        """Test redaction of password credentials."""
        text = "Login with username=admin password=secret123 to access system"

        redacted = redaction_engine.redact(text)

        assert 'secret123' not in redacted
        assert '[REDACTED_PASSWORD]' in redacted

    def test_credential_redaction_api_keys(self, redaction_engine):
        """Test redaction of API keys."""
        text = "Use API_KEY=sk_live_abc123xyz to authenticate"

        redacted = redaction_engine.redact(text)

        assert 'sk_live_abc123xyz' not in redacted
        assert '[REDACTED' in redacted

    def test_credential_redaction_tokens(self, redaction_engine):
        """Test redaction of bearer tokens."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

        redacted = redaction_engine.redact(text)

        assert 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' not in redacted

    def test_credential_redaction_connection_strings(self, redaction_engine):
        """Test redaction of database connection strings."""
        text = "mongodb://user:password123@localhost:27017/mydb"

        redacted = redaction_engine.redact(text)

        assert 'password123' not in redacted
        assert '[REDACTED' in redacted

    def test_credential_redaction_in_errors(self):
        """Test redaction of credentials in error messages."""
        service = RedactionService()
        error = "Connection failed: postgresql://admin:secret@localhost/db failed with timeout"

        redacted = service.redact_error(error)

        assert 'secret' not in redacted or '[REDACTED]' in redacted

    def test_sql_input_sanitization(self):
        """Test SQL input sanitization."""
        dangerous_input = "user'; DROP TABLE users;--"

        sanitized = sanitize_sql_input(dangerous_input)

        # Should escape or remove dangerous characters
        assert sanitized != dangerous_input
        assert '--' not in sanitized

    def test_validation_sql_identifier(self):
        """Test SQL identifier validation."""
        # Valid identifiers
        assert validate_sql_identifier('users') is True
        assert validate_sql_identifier('user_table') is True
        assert validate_sql_identifier('_private') is True

        # Invalid identifiers
        assert validate_sql_identifier('user-table') is False  # hyphen
        assert validate_sql_identifier('123table') is False  # starts with number
        assert validate_sql_identifier('user table') is False  # space
        assert validate_sql_identifier('user;DROP') is False  # semicolon

    def test_validation_email(self):
        """Test email validation."""
        # Valid emails
        assert validate_email('user@example.com') is True
        assert validate_email('test.user@domain.co.uk') is True

        # Invalid emails
        assert validate_email('invalid') is False
        assert validate_email('user@') is False
        assert validate_email('@domain.com') is False
        assert validate_email('user@domain') is False

    def test_query_length_validation(self):
        """Test query length validation."""
        short_query = "SELECT * FROM users;"
        result = validate_query_length(short_query, max_length=1000)
        assert result['valid'] is True

        long_query = "SELECT * FROM users WHERE " + " OR ".join([f"id = {i}" for i in range(1000)])
        result = validate_query_length(long_query, max_length=100)
        assert result['valid'] is False
        assert 'error' in result


# ============================================================================
# TEST REAL DATABASE OPERATIONS
# ============================================================================

class TestRealDatabaseOperations:
    """Test safety system with real database operation patterns."""

    def test_ddl_create_table(self, safety_controller, agent_config_strict):
        """Test CREATE TABLE DDL operation."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.MEDIUM
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_DDL

        step = {
            'tool': 'execute_ddl',
            'params': {
                'sql': '''
                    CREATE TABLE new_users (
                        id INTEGER PRIMARY KEY,
                        username VARCHAR(100) NOT NULL,
                        email VARCHAR(255) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                '''
            },
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        # DDL operations require approval
        assert validation['requires_approval'] is True
        assert 'Schema modification operation' in validation['risks']

    def test_dml_insert(self, safety_controller, agent_config_moderate):
        """Test INSERT DML operation."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.MEDIUM
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_WRITE

        step = {
            'tool': 'execute_insert',
            'params': {
                'sql': "INSERT INTO users (username, email) VALUES ('john', 'john@example.com');"
            },
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_moderate)

        assert validation['risk_level'] in ['medium', 'low']
        assert 'Data modification operation' in validation['risks']

    def test_dml_update_with_where(self, safety_controller, agent_config_moderate):
        """Test UPDATE with WHERE clause."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.MEDIUM
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_WRITE

        step = {
            'tool': 'execute_update',
            'params': {
                'sql': "UPDATE users SET active = 1 WHERE id = 123;"
            },
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_moderate)

        # Should detect SQL with WHERE clause
        assert 'sql_analysis' in validation

    def test_dml_delete_with_where(self, safety_controller, agent_config_moderate):
        """Test DELETE with WHERE clause."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.HIGH
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_WRITE

        step = {
            'tool': 'execute_delete',
            'params': {
                'sql': "DELETE FROM sessions WHERE created_at < '2024-01-01';"
            },
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_moderate)

        assert 'sql_analysis' in validation

    def test_drop_table_operation(self, safety_controller, agent_config_strict):
        """Test DROP TABLE operation."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.CRITICAL
        mock_tool.requires_approval = True
        mock_tool.category = ToolCategory.DATABASE_DDL

        step = {
            'tool': 'drop_table',
            'params': {
                'sql': "DROP TABLE old_logs;"
            },
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        assert validation['risk_level'] == 'critical'
        assert validation['requires_approval'] is True
        assert safety_controller._is_destructive_operation(step) is True

    def test_truncate_table_operation(self, safety_controller, agent_config_strict):
        """Test TRUNCATE TABLE operation."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.CRITICAL
        mock_tool.requires_approval = True
        mock_tool.category = ToolCategory.DATABASE_DDL

        step = {
            'tool': 'truncate_table',
            'params': {
                'sql': "TRUNCATE TABLE temp_data;"
            },
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        assert validation['risk_level'] == 'critical'
        assert safety_controller._is_destructive_operation(step) is True

    def test_alter_table_add_column(self, safety_controller, agent_config_moderate):
        """Test ALTER TABLE ADD COLUMN operation."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.MEDIUM
        mock_tool.requires_approval = False
        mock_tool.category = ToolCategory.DATABASE_DDL

        step = {
            'tool': 'execute_migration',
            'params': {
                'migration_sql': "ALTER TABLE users ADD COLUMN phone VARCHAR(20);"
            },
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_moderate)

        # DDL always requires approval
        assert validation['requires_approval'] is True
        assert 'Schema modification operation' in validation['risks']

    def test_complex_transaction_query(self, safety_controller, agent_config_strict):
        """Test complex transaction with multiple statements."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.HIGH
        mock_tool.requires_approval = True
        mock_tool.category = ToolCategory.DATABASE_WRITE

        step = {
            'tool': 'execute_transaction',
            'params': {
                'sql': '''
                    BEGIN TRANSACTION;
                    UPDATE accounts SET balance = balance - 100 WHERE id = 1;
                    UPDATE accounts SET balance = balance + 100 WHERE id = 2;
                    INSERT INTO transactions (from_account, to_account, amount) VALUES (1, 2, 100);
                    COMMIT;
                '''
            },
            'tool_definition': mock_tool
        }

        validation = safety_controller.validate_step(step, agent_config_strict)

        # Should require approval due to high risk
        assert validation['requires_approval'] is True


# ============================================================================
# TEST INTEGRATION SCENARIOS
# ============================================================================

class TestIntegrationScenarios:
    """Test complete end-to-end safety scenarios."""

    @pytest.mark.asyncio
    async def test_complete_migration_workflow(self, safety_controller, agent_config_strict):
        """Test complete migration workflow with approval."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.HIGH
        mock_tool.requires_approval = True
        mock_tool.category = ToolCategory.DATABASE_DDL

        step = {
            'tool': 'execute_migration',
            'params': {
                'migration_sql': '''
                    -- Add email verification
                    ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
                    CREATE INDEX idx_email_verified ON users(email_verified);
                '''
            },
            'tool_definition': mock_tool
        }

        # Step 1: Validate
        validation = safety_controller.validate_step(step, agent_config_strict)
        assert validation['requires_approval'] is True

        # Step 2: Request approval
        async def approve_callback(request):
            return {
                'approved': True,
                'reason': 'Migration reviewed and approved by DBA',
                'approver': 'dba_team',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': ['Backup completed', 'Rollback script prepared']
            }

        approval = await safety_controller.request_approval(step, validation, approve_callback)
        assert approval['approved'] is True

        # Step 3: Verify audit trail
        history = safety_controller.get_approval_history()
        assert len(history) > 0
        assert history[-1]['approval']['approved'] is True

    @pytest.mark.asyncio
    async def test_rejected_destructive_operation(self, safety_controller, agent_config_strict):
        """Test rejection of destructive operation."""
        mock_tool = Mock()
        mock_tool.risk_level = ToolRiskLevel.CRITICAL
        mock_tool.requires_approval = True
        mock_tool.category = ToolCategory.DATABASE_DDL

        step = {
            'tool': 'drop_database',
            'params': {'database': 'production'},
            'tool_definition': mock_tool
        }

        # Validate
        validation = safety_controller.validate_step(step, agent_config_strict)
        assert validation['requires_approval'] is True
        assert validation['approval_requirement'] == ApprovalRequirement.MULTI_PARTY

        # Reject
        async def reject_callback(request):
            return {
                'approved': False,
                'reason': 'Cannot drop production database',
                'approver': 'security_team',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': []
            }

        approval = await safety_controller.request_approval(step, validation, reject_callback)
        assert approval['approved'] is False

        # Verify rejection is logged
        history = safety_controller.get_approval_history(approved_only=False)
        assert len(history) > 0
        assert history[-1]['approval']['approved'] is False

    def test_sql_injection_blocked(self, sql_guard):
        """Test that SQL injection is properly blocked."""
        injection_attempts = [
            "SELECT * FROM users WHERE id = 1 OR '1'='1';",
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT * FROM users WHERE name = 'admin' UNION SELECT password FROM admins;",
            "SELECT * FROM users WHERE id = 1; -- evil comment"
        ]

        for attempt in injection_attempts:
            result = sql_guard.validate_query(attempt)
            assert result['is_safe'] is False
            assert len(result['threats_detected']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
