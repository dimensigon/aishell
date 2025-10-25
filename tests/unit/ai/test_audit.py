"""Tests for audit and compliance features"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta

from src.enterprise.audit.audit_logger import AuditLogger, AuditLevel
from src.enterprise.audit.compliance_reporter import ComplianceReporter, ComplianceFramework
from src.enterprise.audit.change_tracker import ChangeTracker


class TestAuditLogger:
    """Test audit logging"""

    @pytest.fixture
    def logger(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            db_path = f.name
        yield AuditLogger(db_path=db_path)
        os.unlink(db_path)

    def test_log_event(self, logger):
        """Test logging audit event"""
        event_id = logger.log(
            action="user.login",
            resource="authentication",
            level=AuditLevel.INFO,
            tenant_id="tenant_1",
            user_id="user_1",
            details={"method": "password"},
        )

        assert event_id is not None

    def test_query_logs(self, logger):
        """Test querying audit logs"""
        logger.log("user.login", "auth", tenant_id="tenant_1")
        logger.log("user.logout", "auth", tenant_id="tenant_1")

        logs = logger.query(tenant_id="tenant_1")
        assert len(logs) == 2

    def test_query_by_action(self, logger):
        """Test querying by action"""
        logger.log("user.login", "auth")
        logger.log("user.logout", "auth")
        logger.log("database.query", "db")

        logs = logger.query(action="user.login")
        assert len(logs) == 1

    def test_query_by_time_range(self, logger):
        """Test querying by time range"""
        logger.log("test", "resource")

        now = datetime.now()
        logs = logger.query(
            start_time=(now - timedelta(minutes=1)).isoformat(),
            end_time=(now + timedelta(minutes=1)).isoformat(),
        )

        assert len(logs) > 0

    def test_get_statistics(self, logger):
        """Test audit statistics"""
        logger.log("test1", "resource", level=AuditLevel.INFO)
        logger.log("test2", "resource", level=AuditLevel.WARNING)
        logger.log("test3", "resource", level=AuditLevel.ERROR)

        stats = logger.get_statistics()
        assert len(stats) > 0


class TestComplianceReporter:
    """Test compliance reporting"""

    @pytest.fixture
    def reporter(self, tmp_path):
        db_file = tmp_path / "test_audit.db"
        logger = AuditLogger(db_path=str(db_file))
        # Add some test logs
        logger.log("user.access", "data", tenant_id="tenant_1")
        logger.log("data.update", "record", tenant_id="tenant_1")
        return ComplianceReporter(logger)

    def test_generate_soc2_report(self, reporter):
        """Test SOC2 report generation"""
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()

        report = reporter.generate_report(
            ComplianceFramework.SOC2,
            start,
            end,
            tenant_id="tenant_1",
        )

        assert report['framework'] == 'SOC2'
        assert 'access_controls' in report
        assert 'change_management' in report

    def test_generate_hipaa_report(self, reporter):
        """Test HIPAA report generation"""
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()

        report = reporter.generate_report(
            ComplianceFramework.HIPAA,
            start,
            end,
        )

        assert report['framework'] == 'HIPAA'
        assert 'phi_access' in report

    def test_generate_gdpr_report(self, reporter):
        """Test GDPR report generation"""
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()

        report = reporter.generate_report(
            ComplianceFramework.GDPR,
            start,
            end,
        )

        assert report['framework'] == 'GDPR'
        assert 'data_access' in report
        assert 'data_deletion' in report


class TestChangeTracker:
    """Test change tracking"""

    @pytest.fixture
    def tracker(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            db_path = f.name
        yield ChangeTracker(db_path=db_path)
        os.unlink(db_path)

    def test_track_change(self, tracker):
        """Test tracking database change"""
        change_id = tracker.track_change(
            change_type="data",
            operation="UPDATE",
            table_name="users",
            tenant_id="tenant_1",
            user_id="user_1",
            before_value={"name": "Old Name"},
            after_value={"name": "New Name"},
        )

        assert change_id is not None

    def test_get_changes(self, tracker):
        """Test retrieving changes"""
        tracker.track_change("data", "INSERT", table_name="users")
        tracker.track_change("data", "UPDATE", table_name="users")

        changes = tracker.get_changes(table_name="users")
        assert len(changes) == 2

    def test_changes_by_tenant(self, tracker):
        """Test filtering changes by tenant"""
        tracker.track_change("data", "INSERT", tenant_id="tenant_1")
        tracker.track_change("data", "INSERT", tenant_id="tenant_2")

        changes = tracker.get_changes(tenant_id="tenant_1")
        assert len(changes) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
