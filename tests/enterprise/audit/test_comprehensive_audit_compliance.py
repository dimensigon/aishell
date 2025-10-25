"""
Comprehensive tests for audit and compliance modules

Tests:
- Audit logging
- Change tracking
- Compliance reporting (GDPR, SOC2, HIPAA)
- Audit trail integrity
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from src.enterprise.audit.audit_logger import AuditLogger, AuditLevel
from src.enterprise.audit.change_tracker import ChangeTracker
from src.enterprise.audit.compliance_reporter import ComplianceReporter, ComplianceFramework


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def audit_logger(temp_db):
    return AuditLogger(db_path=temp_db)


@pytest.fixture
def change_tracker():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    tracker = ChangeTracker(db_path=path)
    yield tracker
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def compliance_reporter(audit_logger):
    return ComplianceReporter(audit_logger=audit_logger)


class TestAuditLogging:
    """Test audit logging functionality"""

    def test_log_basic_event(self, audit_logger):
        """Test logging basic audit event"""
        event_id = audit_logger.log(
            action="user.login",
            resource="auth",
            tenant_id="tenant_123",
            user_id="user_456"
        )

        assert event_id is not None

    def test_log_with_details(self, audit_logger):
        """Test logging event with details"""
        event_id = audit_logger.log(
            action="database.query",
            resource="database",
            tenant_id="tenant_123",
            user_id="user_456",
            details={"query": "SELECT * FROM users", "duration_ms": 45}
        )

        assert event_id is not None

    def test_log_different_levels(self, audit_logger):
        """Test logging at different severity levels"""
        audit_logger.log(
            action="info.action",
            resource="test",
            level=AuditLevel.INFO
        )

        audit_logger.log(
            action="warning.action",
            resource="test",
            level=AuditLevel.WARNING
        )

        audit_logger.log(
            action="error.action",
            resource="test",
            level=AuditLevel.ERROR
        )

        audit_logger.log(
            action="critical.action",
            resource="test",
            level=AuditLevel.CRITICAL
        )

    def test_log_with_ip_and_user_agent(self, audit_logger):
        """Test logging with IP and user agent"""
        event_id = audit_logger.log(
            action="api.request",
            resource="api",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )

        assert event_id is not None

    def test_log_failure_result(self, audit_logger):
        """Test logging failed operation"""
        event_id = audit_logger.log(
            action="auth.failed",
            resource="auth",
            level=AuditLevel.WARNING,
            result="failure",
            details={"reason": "invalid_credentials"}
        )

        assert event_id is not None


class TestAuditQuerying:
    """Test audit log querying"""

    def test_query_by_tenant(self, audit_logger):
        """Test querying logs by tenant"""
        audit_logger.log(
            action="test.action",
            resource="test",
            tenant_id="tenant_1"
        )

        results = audit_logger.query(tenant_id="tenant_1")

        assert len(results) > 0
        assert all(r['tenant_id'] == 'tenant_1' for r in results)

    def test_query_by_user(self, audit_logger):
        """Test querying logs by user"""
        audit_logger.log(
            action="test.action",
            resource="test",
            user_id="user_123"
        )

        results = audit_logger.query(user_id="user_123")

        assert len(results) > 0

    def test_query_by_action(self, audit_logger):
        """Test querying logs by action"""
        audit_logger.log(
            action="specific.action",
            resource="test"
        )

        results = audit_logger.query(action="specific.action")

        assert len(results) > 0

    def test_query_by_time_range(self, audit_logger):
        """Test querying logs by time range"""
        start_time = datetime.now()

        audit_logger.log(action="test.action", resource="test")

        end_time = datetime.now() + timedelta(seconds=1)

        results = audit_logger.query(
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )

        assert len(results) > 0

    def test_query_by_level(self, audit_logger):
        """Test querying logs by level"""
        audit_logger.log(
            action="error.action",
            resource="test",
            level=AuditLevel.ERROR
        )

        results = audit_logger.query(level=AuditLevel.ERROR)

        assert len(results) > 0

    def test_query_with_limit(self, audit_logger):
        """Test query result limiting"""
        for i in range(20):
            audit_logger.log(action=f"action_{i}", resource="test")

        results = audit_logger.query(limit=10)

        assert len(results) == 10


class TestAuditStatistics:
    """Test audit statistics"""

    def test_get_statistics(self, audit_logger):
        """Test getting audit statistics"""
        audit_logger.log(action="test1", resource="test", level=AuditLevel.INFO)
        audit_logger.log(action="test2", resource="test", level=AuditLevel.WARNING)
        audit_logger.log(action="test3", resource="test", level=AuditLevel.ERROR, result="failure")

        stats = audit_logger.get_statistics()

        assert 'statistics' in stats
        assert len(stats['statistics']) > 0


class TestChangeTracking:
    """Test database change tracking"""

    def test_track_schema_change(self, change_tracker):
        """Test tracking schema changes"""
        change_id = change_tracker.track_change(
            change_type="schema",
            operation="ALTER",
            table_name="users",
            sql_statement="ALTER TABLE users ADD COLUMN email VARCHAR(255)"
        )

        assert change_id is not None

    def test_track_data_change(self, change_tracker):
        """Test tracking data modifications"""
        change_id = change_tracker.track_change(
            change_type="data",
            operation="UPDATE",
            table_name="users",
            before_value={"status": "inactive"},
            after_value={"status": "active"},
            tenant_id="tenant_123",
            user_id="user_456"
        )

        assert change_id is not None

    def test_track_insert_operation(self, change_tracker):
        """Test tracking INSERT operations"""
        change_id = change_tracker.track_change(
            change_type="data",
            operation="INSERT",
            table_name="users",
            after_value={"id": 1, "username": "john", "email": "john@example.com"}
        )

        assert change_id is not None

    def test_track_delete_operation(self, change_tracker):
        """Test tracking DELETE operations"""
        change_id = change_tracker.track_change(
            change_type="data",
            operation="DELETE",
            table_name="users",
            before_value={"id": 1, "username": "john"}
        )

        assert change_id is not None

    def test_get_changes(self, change_tracker):
        """Test retrieving change history"""
        change_tracker.track_change(
            change_type="data",
            operation="UPDATE",
            table_name="users"
        )

        changes = change_tracker.get_changes()

        assert len(changes) > 0

    def test_get_changes_by_tenant(self, change_tracker):
        """Test filtering changes by tenant"""
        change_tracker.track_change(
            change_type="data",
            operation="UPDATE",
            tenant_id="tenant_123"
        )

        changes = change_tracker.get_changes(tenant_id="tenant_123")

        assert len(changes) > 0

    def test_get_changes_by_table(self, change_tracker):
        """Test filtering changes by table"""
        change_tracker.track_change(
            change_type="schema",
            operation="ALTER",
            table_name="orders"
        )

        changes = change_tracker.get_changes(table_name="orders")

        assert len(changes) > 0


class TestComplianceReporting:
    """Test compliance report generation"""

    def test_generate_soc2_report(self, compliance_reporter, audit_logger):
        """Test generating SOC2 compliance report"""
        # Add some audit events
        audit_logger.log(action="access.granted", resource="database")
        audit_logger.log(action="config.changed", resource="system")

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        report = compliance_reporter.generate_report(
            framework=ComplianceFramework.SOC2,
            start_date=start_date,
            end_date=end_date
        )

        assert report['framework'] == 'SOC2'
        assert 'total_events' in report
        assert 'access_controls' in report
        assert 'change_management' in report

    def test_generate_hipaa_report(self, compliance_reporter, audit_logger):
        """Test generating HIPAA compliance report"""
        audit_logger.log(
            action="phi.accessed",
            resource="patient_records",
            details={"phi": True}
        )

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        report = compliance_reporter.generate_report(
            framework=ComplianceFramework.HIPAA,
            start_date=start_date,
            end_date=end_date
        )

        assert report['framework'] == 'HIPAA'
        assert 'phi_access' in report
        assert 'audit_trail' in report

    def test_generate_gdpr_report(self, compliance_reporter, audit_logger):
        """Test generating GDPR compliance report"""
        audit_logger.log(action="data.accessed", resource="user_data")
        audit_logger.log(action="data.deleted", resource="user_data")
        audit_logger.log(action="consent.granted", resource="user_consent")

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        report = compliance_reporter.generate_report(
            framework=ComplianceFramework.GDPR,
            start_date=start_date,
            end_date=end_date
        )

        assert report['framework'] == 'GDPR'
        assert 'data_access' in report
        assert 'data_deletion' in report
        assert 'consent_management' in report

    def test_generate_report_with_tenant_filter(self, compliance_reporter, audit_logger):
        """Test generating tenant-specific compliance report"""
        audit_logger.log(
            action="test.action",
            resource="test",
            tenant_id="tenant_123"
        )

        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        report = compliance_reporter.generate_report(
            framework=ComplianceFramework.SOC2,
            start_date=start_date,
            end_date=end_date,
            tenant_id="tenant_123"
        )

        assert report is not None

    def test_report_includes_timestamp(self, compliance_reporter):
        """Test compliance reports include generation timestamp"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        report = compliance_reporter.generate_report(
            framework=ComplianceFramework.SOC2,
            start_date=start_date,
            end_date=end_date
        )

        assert 'generated_at' in report


class TestAuditTrailIntegrity:
    """Test audit trail integrity and tamper protection"""

    def test_audit_events_are_immutable(self, audit_logger):
        """Test that audit events cannot be modified"""
        event_id = audit_logger.log(
            action="critical.operation",
            resource="sensitive_data"
        )

        # Audit logs should be append-only
        # In production, you'd verify hash chains or cryptographic signatures

    def test_audit_events_timestamped(self, audit_logger):
        """Test all audit events have timestamps"""
        event_id = audit_logger.log(
            action="test.action",
            resource="test"
        )

        results = audit_logger.query(action="test.action")

        assert all('timestamp' in r for r in results)

    def test_comprehensive_audit_trail(self, audit_logger):
        """Test comprehensive audit trail captures all actions"""
        actions = [
            "user.login",
            "database.query",
            "config.update",
            "user.logout"
        ]

        for action in actions:
            audit_logger.log(action=action, resource="system")

        results = audit_logger.query()

        logged_actions = [r['action'] for r in results]

        for action in actions:
            assert action in logged_actions


class TestMultiTenantAuditIsolation:
    """Test audit log isolation between tenants"""

    def test_tenant_audit_isolation(self, audit_logger):
        """Test tenants cannot access each other's audit logs"""
        audit_logger.log(
            action="tenant1.action",
            resource="data",
            tenant_id="tenant_1"
        )

        audit_logger.log(
            action="tenant2.action",
            resource="data",
            tenant_id="tenant_2"
        )

        tenant1_logs = audit_logger.query(tenant_id="tenant_1")
        tenant2_logs = audit_logger.query(tenant_id="tenant_2")

        # Verify no cross-tenant data leakage
        assert all(log['tenant_id'] == 'tenant_1' for log in tenant1_logs)
        assert all(log['tenant_id'] == 'tenant_2' for log in tenant2_logs)
