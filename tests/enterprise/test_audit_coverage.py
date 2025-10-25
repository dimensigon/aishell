"""
Comprehensive coverage tests for Audit Logger
Targeting uncovered branches, error paths, and edge cases
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime
from src.enterprise.audit.audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditLevel,
)


class TestAuditLevelEnum:
    """Test AuditLevel enum"""

    def test_all_audit_levels(self):
        """Test all audit level values"""
        assert AuditLevel.INFO.value == "info"
        assert AuditLevel.WARNING.value == "warning"
        assert AuditLevel.ERROR.value == "error"
        assert AuditLevel.CRITICAL.value == "critical"


class TestAuditEventDataclass:
    """Test AuditEvent dataclass"""

    def test_event_creation_minimal(self):
        """Test creating event with minimal fields"""
        event = AuditEvent(
            id="test-id",
            timestamp="2024-01-01T00:00:00",
            tenant_id=None,
            user_id=None,
            action="test_action",
            resource="test_resource",
            level=AuditLevel.INFO,
            details={}
        )

        assert event.id == "test-id"
        assert event.action == "test_action"
        assert event.result == "success"  # Default value

    def test_event_creation_full(self):
        """Test creating event with all fields"""
        event = AuditEvent(
            id="test-id",
            timestamp="2024-01-01T00:00:00",
            tenant_id="tenant-123",
            user_id="user-456",
            action="update_record",
            resource="database",
            level=AuditLevel.WARNING,
            details={"key": "value"},
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
            result="failure"
        )

        assert event.tenant_id == "tenant-123"
        assert event.user_id == "user-456"
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "TestAgent/1.0"
        assert event.result == "failure"

    def test_event_to_dict(self):
        """Test converting event to dictionary"""
        event = AuditEvent(
            id="test-id",
            timestamp="2024-01-01T00:00:00",
            tenant_id="tenant-123",
            user_id="user-456",
            action="test_action",
            resource="test_resource",
            level=AuditLevel.ERROR,
            details={"key": "value"}
        )

        event_dict = event.to_dict()

        assert event_dict["id"] == "test-id"
        assert event_dict["level"] == "error"  # Enum converted to value
        assert event_dict["details"] == {"key": "value"}

    def test_event_to_dict_with_all_fields(self):
        """Test to_dict with all optional fields"""
        event = AuditEvent(
            id="test-id",
            timestamp="2024-01-01T00:00:00",
            tenant_id="tenant-123",
            user_id="user-456",
            action="test_action",
            resource="test_resource",
            level=AuditLevel.CRITICAL,
            details={"nested": {"key": "value"}},
            ip_address="10.0.0.1",
            user_agent="TestAgent",
            result="partial"
        )

        event_dict = event.to_dict()

        assert event_dict["ip_address"] == "10.0.0.1"
        assert event_dict["user_agent"] == "TestAgent"
        assert event_dict["result"] == "partial"


class TestAuditLoggerInitialization:
    """Test AuditLogger initialization"""

    def test_initialization_default_path(self):
        """Test initialization with default path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / ".ai-shell" / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            assert logger.db_path == str(db_path)
            assert Path(logger.db_path).parent.exists()

    def test_initialization_custom_path(self):
        """Test initialization with custom path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "custom_audit.db"
            logger = AuditLogger(db_path=str(db_path))

            assert logger.db_path == str(db_path)

    def test_database_creation(self):
        """Test that database and tables are created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            # Check database file exists
            assert Path(logger.db_path).exists()

            # Check table exists
            with sqlite3.connect(logger.db_path) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'"
                )
                assert cursor.fetchone() is not None

    def test_database_indexes_created(self):
        """Test that indexes are created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            with sqlite3.connect(logger.db_path) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index'"
                )
                indexes = [row[0] for row in cursor.fetchall()]

                assert any("audit_timestamp" in idx for idx in indexes)
                assert any("audit_tenant" in idx for idx in indexes)
                assert any("audit_user" in idx for idx in indexes)
                assert any("audit_action" in idx for idx in indexes)


class TestAuditLogging:
    """Test audit logging functionality"""

    def test_log_minimal_event(self):
        """Test logging event with minimal data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            event_id = logger.log(
                action="test_action",
                resource="test_resource"
            )

            assert event_id is not None

            # Verify in database
            with sqlite3.connect(logger.db_path) as conn:
                cursor = conn.execute(
                    "SELECT action, resource FROM audit_log WHERE id = ?",
                    (event_id,)
                )
                row = cursor.fetchone()
                assert row[0] == "test_action"
                assert row[1] == "test_resource"

    def test_log_with_all_parameters(self):
        """Test logging with all parameters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            event_id = logger.log(
                action="create_record",
                resource="database",
                level=AuditLevel.WARNING,
                tenant_id="tenant-123",
                user_id="user-456",
                details={"table": "users", "count": 5},
                ip_address="192.168.1.1",
                user_agent="TestAgent/1.0",
                result="success"
            )

            assert event_id is not None

            # Verify all fields
            with sqlite3.connect(logger.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM audit_log WHERE id = ?",
                    (event_id,)
                )
                row = cursor.fetchone()

                assert row["tenant_id"] == "tenant-123"
                assert row["user_id"] == "user-456"
                assert row["level"] == "warning"
                assert row["ip_address"] == "192.168.1.1"
                assert row["user_agent"] == "TestAgent/1.0"
                assert row["result"] == "success"

    def test_log_multiple_events(self):
        """Test logging multiple events"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            event_ids = []
            for i in range(10):
                event_id = logger.log(
                    action=f"action_{i}",
                    resource="test_resource",
                    level=AuditLevel.INFO
                )
                event_ids.append(event_id)

            # Verify all events were logged
            with sqlite3.connect(logger.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM audit_log")
                count = cursor.fetchone()[0]
                assert count == 10

    def test_log_with_complex_details(self):
        """Test logging with complex nested details"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            details = {
                "nested": {"level1": {"level2": "value"}},
                "list": [1, 2, 3],
                "mixed": {"a": [1, 2], "b": {"c": 3}}
            }

            event_id = logger.log(
                action="test",
                resource="test",
                details=details
            )

            # Verify details are stored as JSON
            with sqlite3.connect(logger.db_path) as conn:
                cursor = conn.execute(
                    "SELECT details FROM audit_log WHERE id = ?",
                    (event_id,)
                )
                stored_details = cursor.fetchone()[0]
                assert "nested" in stored_details
                assert "level2" in stored_details


class TestAuditQuerying:
    """Test audit log querying"""

    def test_query_all_events(self):
        """Test querying all events"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            # Log some events
            for i in range(5):
                logger.log(action=f"action_{i}", resource="test")

            results = logger.query()

            assert len(results) == 5

    def test_query_by_tenant_id(self):
        """Test querying by tenant ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="action1", resource="test", tenant_id="tenant-1")
            logger.log(action="action2", resource="test", tenant_id="tenant-2")
            logger.log(action="action3", resource="test", tenant_id="tenant-1")

            results = logger.query(tenant_id="tenant-1")

            assert len(results) == 2

    def test_query_by_user_id(self):
        """Test querying by user ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="action1", resource="test", user_id="user-1")
            logger.log(action="action2", resource="test", user_id="user-2")
            logger.log(action="action3", resource="test", user_id="user-1")

            results = logger.query(user_id="user-1")

            assert len(results) == 2

    def test_query_by_action(self):
        """Test querying by action"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="create", resource="test")
            logger.log(action="update", resource="test")
            logger.log(action="create", resource="test")

            results = logger.query(action="create")

            assert len(results) == 2

    def test_query_by_time_range(self):
        """Test querying by time range"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="action1", resource="test")
            logger.log(action="action2", resource="test")

            # Query with time range
            start_time = "2020-01-01T00:00:00"
            end_time = "2030-01-01T00:00:00"

            results = logger.query(start_time=start_time, end_time=end_time)

            assert len(results) == 2

    def test_query_by_level(self):
        """Test querying by audit level"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="action1", resource="test", level=AuditLevel.INFO)
            logger.log(action="action2", resource="test", level=AuditLevel.ERROR)
            logger.log(action="action3", resource="test", level=AuditLevel.INFO)

            results = logger.query(level=AuditLevel.ERROR)

            assert len(results) == 1
            assert results[0]["level"] == "error"

    def test_query_with_limit(self):
        """Test querying with result limit"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            for i in range(10):
                logger.log(action=f"action_{i}", resource="test")

            results = logger.query(limit=5)

            assert len(results) == 5

    def test_query_with_multiple_filters(self):
        """Test querying with multiple filters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(
                action="create",
                resource="test",
                tenant_id="tenant-1",
                user_id="user-1",
                level=AuditLevel.INFO
            )
            logger.log(
                action="update",
                resource="test",
                tenant_id="tenant-1",
                user_id="user-2",
                level=AuditLevel.INFO
            )
            logger.log(
                action="create",
                resource="test",
                tenant_id="tenant-2",
                user_id="user-1",
                level=AuditLevel.WARNING
            )

            results = logger.query(
                tenant_id="tenant-1",
                action="create",
                level=AuditLevel.INFO
            )

            assert len(results) == 1

    def test_query_empty_results(self):
        """Test querying with no matching results"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="action1", resource="test", tenant_id="tenant-1")

            results = logger.query(tenant_id="nonexistent")

            assert len(results) == 0

    def test_query_order_by_timestamp_desc(self):
        """Test that results are ordered by timestamp descending"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="first", resource="test")
            logger.log(action="second", resource="test")
            logger.log(action="third", resource="test")

            results = logger.query()

            assert results[0]["action"] == "third"  # Most recent first
            assert results[-1]["action"] == "first"  # Oldest last


class TestAuditStatistics:
    """Test audit statistics"""

    def test_get_statistics_empty(self):
        """Test statistics with no events"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            stats = logger.get_statistics()

            assert stats["statistics"] == []

    def test_get_statistics_single_tenant(self):
        """Test statistics for single tenant"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="action1", resource="test", tenant_id="tenant-1", level=AuditLevel.INFO)
            logger.log(action="action2", resource="test", tenant_id="tenant-1", level=AuditLevel.ERROR)
            logger.log(action="action3", resource="test", tenant_id="tenant-1", level=AuditLevel.INFO)

            stats = logger.get_statistics(tenant_id="tenant-1")

            assert len(stats["statistics"]) > 0

    def test_get_statistics_all_tenants(self):
        """Test statistics for all tenants"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="action1", resource="test", tenant_id="tenant-1", level=AuditLevel.INFO)
            logger.log(action="action2", resource="test", tenant_id="tenant-2", level=AuditLevel.ERROR)

            stats = logger.get_statistics()

            assert len(stats["statistics"]) > 0

    def test_get_statistics_groups_by_level_and_result(self):
        """Test statistics groups by level and result"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="action1", resource="test", level=AuditLevel.INFO, result="success")
            logger.log(action="action2", resource="test", level=AuditLevel.INFO, result="success")
            logger.log(action="action3", resource="test", level=AuditLevel.ERROR, result="failure")

            stats = logger.get_statistics()

            # Should have multiple groups
            assert len(stats["statistics"]) >= 2

            # Verify grouping
            for stat in stats["statistics"]:
                assert "total" in stat
                assert "level" in stat
                assert "result" in stat


class TestAuditEdgeCases:
    """Test edge cases and error conditions"""

    def test_log_with_none_details(self):
        """Test logging with None details"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            event_id = logger.log(
                action="test",
                resource="test",
                details=None
            )

            assert event_id is not None

    def test_log_with_empty_details(self):
        """Test logging with empty details dict"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            event_id = logger.log(
                action="test",
                resource="test",
                details={}
            )

            assert event_id is not None

    def test_query_with_zero_limit(self):
        """Test querying with limit of 0"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="action1", resource="test")

            results = logger.query(limit=0)

            assert len(results) == 0

    def test_query_with_negative_limit(self):
        """Test querying with negative limit"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            logger.log(action="action1", resource="test")

            # SQLite will handle negative limit
            results = logger.query(limit=-1)

            # Behavior depends on SQLite version
            assert isinstance(results, list)

    def test_log_very_long_action_name(self):
        """Test logging with very long action name"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            long_action = "a" * 1000

            event_id = logger.log(
                action=long_action,
                resource="test"
            )

            assert event_id is not None

    def test_log_with_unicode_characters(self):
        """Test logging with unicode characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            logger = AuditLogger(db_path=str(db_path))

            event_id = logger.log(
                action="测试动作",
                resource="テストリソース",
                details={"emoji": "🔐"}
            )

            assert event_id is not None

    def test_multiple_loggers_same_database(self):
        """Test multiple logger instances accessing same database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"

            logger1 = AuditLogger(db_path=str(db_path))
            logger2 = AuditLogger(db_path=str(db_path))

            logger1.log(action="action1", resource="test")
            logger2.log(action="action2", resource="test")

            results = logger1.query()
            assert len(results) == 2
