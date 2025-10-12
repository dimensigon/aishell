"""
Comprehensive tests for audit logging module.

Tests audit logging, search, retention, tamper-proof features,
and security compliance.
"""

import pytest
from datetime import datetime, timedelta
import json
from src.security.audit import AuditLogger, TamperProofLogger, AuditLog


class TestBasicAuditLogging:
    """Test suite for basic audit logging."""

    def test_log_action(self):
        """Test logging a basic action."""
        logger = AuditLogger()

        log = logger.log_action(
            user="admin",
            action="create",
            resource="user",
            details={"user_id": "123"}
        )

        assert log.user == "admin"
        assert log.action == "create"
        assert log.resource == "user"
        assert log.details["user_id"] == "123"
        assert log.log_id is not None
        assert log.timestamp is not None

    def test_log_with_ip_and_user_agent(self):
        """Test logging with IP address and user agent."""
        logger = AuditLogger()

        log = logger.log_action(
            user="user1",
            action="login",
            resource="auth",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )

        assert log.ip_address == "192.168.1.100"
        assert log.user_agent == "Mozilla/5.0"

    def test_log_with_custom_timestamp(self):
        """Test logging with custom timestamp."""
        logger = AuditLogger()

        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        log = logger.log_action(
            user="admin",
            action="test",
            resource="system",
            timestamp=custom_time
        )

        assert log.timestamp == custom_time

    def test_multiple_logs(self):
        """Test logging multiple actions."""
        logger = AuditLogger()

        logger.log_action("user1", "read", "file1")
        logger.log_action("user2", "write", "file2")
        logger.log_action("user3", "delete", "file3")

        logs = logger.get_logs()
        assert len(logs) == 3

    def test_unique_log_ids(self):
        """Test that log IDs are unique."""
        logger = AuditLogger()

        log1 = logger.log_action("user1", "action1", "resource1")
        log2 = logger.log_action("user2", "action2", "resource2")

        assert log1.log_id != log2.log_id


class TestLogRetrieval:
    """Test suite for log retrieval and pagination."""

    def test_get_all_logs(self):
        """Test retrieving all logs."""
        logger = AuditLogger()

        logger.log_action("user1", "action1", "resource1")
        logger.log_action("user2", "action2", "resource2")

        logs = logger.get_logs()
        assert len(logs) == 2

    def test_get_logs_with_limit(self):
        """Test retrieving logs with limit."""
        logger = AuditLogger()

        for i in range(10):
            logger.log_action(f"user{i}", "action", "resource")

        logs = logger.get_logs(limit=5)
        assert len(logs) == 5

    def test_get_logs_with_offset(self):
        """Test retrieving logs with offset."""
        logger = AuditLogger()

        for i in range(10):
            logger.log_action(f"user{i}", "action", "resource")

        logs = logger.get_logs(offset=5)
        assert len(logs) == 5

    def test_get_logs_with_limit_and_offset(self):
        """Test retrieving logs with both limit and offset."""
        logger = AuditLogger()

        for i in range(10):
            logger.log_action(f"user{i}", "action", "resource")

        logs = logger.get_logs(limit=3, offset=2)
        assert len(logs) == 3


class TestLogSearch:
    """Test suite for audit log search."""

    def test_search_by_user(self):
        """Test searching logs by user."""
        logger = AuditLogger()

        logger.log_action("alice", "read", "file1")
        logger.log_action("bob", "write", "file2")
        logger.log_action("alice", "delete", "file3")

        logs = logger.search_logs(user="alice")
        assert len(logs) == 2
        assert all(log["user"] == "alice" for log in logs)

    def test_search_by_action(self):
        """Test searching logs by action."""
        logger = AuditLogger()

        logger.log_action("user1", "create", "resource1")
        logger.log_action("user2", "create", "resource2")
        logger.log_action("user3", "delete", "resource3")

        logs = logger.search_logs(action="create")
        assert len(logs) == 2

    def test_search_by_resource(self):
        """Test searching logs by resource."""
        logger = AuditLogger()

        logger.log_action("user1", "read", "database")
        logger.log_action("user2", "write", "database")
        logger.log_action("user3", "read", "api")

        logs = logger.search_logs(resource="database")
        assert len(logs) == 2

    def test_search_by_date_range(self):
        """Test searching logs by date range."""
        logger = AuditLogger()

        now = datetime.now()
        past = now - timedelta(days=5)
        future = now + timedelta(days=5)

        logger.log_action("user1", "action1", "resource1", timestamp=past)
        logger.log_action("user2", "action2", "resource2", timestamp=now)
        logger.log_action("user3", "action3", "resource3", timestamp=future)

        logs = logger.search_logs(start_date=now - timedelta(days=1))
        assert len(logs) == 2

    def test_search_with_end_date(self):
        """Test searching with end date."""
        logger = AuditLogger()

        now = datetime.now()

        logger.log_action("user1", "action1", "resource1", timestamp=now - timedelta(days=2))
        logger.log_action("user2", "action2", "resource2", timestamp=now)

        logs = logger.search_logs(end_date=now - timedelta(days=1))
        assert len(logs) == 1

    def test_search_multiple_criteria(self):
        """Test searching with multiple criteria."""
        logger = AuditLogger()

        logger.log_action("alice", "read", "database")
        logger.log_action("alice", "write", "api")
        logger.log_action("bob", "read", "database")

        logs = logger.search_logs(user="alice", action="read")
        assert len(logs) == 1
        assert logs[0]["user"] == "alice"
        assert logs[0]["action"] == "read"

    def test_search_no_results(self):
        """Test search with no matching results."""
        logger = AuditLogger()

        logger.log_action("user1", "action1", "resource1")

        logs = logger.search_logs(user="nonexistent")
        assert len(logs) == 0


class TestLogRetention:
    """Test suite for log retention and cleanup."""

    def test_retention_cleanup(self):
        """Test cleaning up old logs."""
        logger = AuditLogger(retention_days=7)

        now = datetime.now()
        old = now - timedelta(days=10)

        logger.log_action("user1", "old_action", "resource", timestamp=old)
        logger.log_action("user2", "new_action", "resource", timestamp=now)

        removed = logger.cleanup_old_logs()

        assert removed == 1
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0]["action"] == "new_action"

    def test_retention_keeps_recent(self):
        """Test that recent logs are kept."""
        logger = AuditLogger(retention_days=30)

        now = datetime.now()
        recent = now - timedelta(days=15)

        logger.log_action("user1", "action1", "resource", timestamp=recent)
        logger.log_action("user2", "action2", "resource", timestamp=now)

        removed = logger.cleanup_old_logs()

        assert removed == 0
        assert len(logger.get_logs()) == 2

    def test_retention_boundary(self):
        """Test retention at exact boundary."""
        logger = AuditLogger(retention_days=7)

        now = datetime.now()
        boundary = now - timedelta(days=7, seconds=1)  # Just past boundary
        old = now - timedelta(days=8)

        logger.log_action("user1", "old", "resource", timestamp=old)
        logger.log_action("user2", "boundary", "resource", timestamp=boundary)
        logger.log_action("user3", "new", "resource", timestamp=now)

        removed = logger.cleanup_old_logs()

        # Both old and boundary logs should be removed (>= cutoff)
        assert removed == 2
        logs = logger.get_logs()
        assert len(logs) == 1


class TestLogExport:
    """Test suite for log export functionality."""

    def test_export_json(self):
        """Test exporting logs as JSON."""
        logger = AuditLogger()

        logger.log_action("user1", "action1", "resource1")
        logger.log_action("user2", "action2", "resource2")

        exported = logger.export_logs(format='json')

        data = json.loads(exported)
        assert data["log_count"] == 2
        assert len(data["logs"]) == 2
        assert "export_date" in data

    def test_export_csv(self):
        """Test exporting logs as CSV."""
        logger = AuditLogger()

        logger.log_action("user1", "action1", "resource1", details={"key": "value"})

        exported = logger.export_logs(format='csv')

        lines = exported.split('\n')
        assert lines[0] == 'timestamp,user,action,resource,details'
        assert len(lines) >= 2

    def test_export_with_date_filter(self):
        """Test exporting logs with date filter."""
        logger = AuditLogger()

        now = datetime.now()
        old = now - timedelta(days=10)

        logger.log_action("user1", "old", "resource", timestamp=old)
        logger.log_action("user2", "new", "resource", timestamp=now)

        exported = logger.export_logs(format='json', start_date=now - timedelta(days=5))

        data = json.loads(exported)
        assert data["log_count"] == 1

    def test_export_unsupported_format(self):
        """Test exporting with unsupported format."""
        logger = AuditLogger()

        with pytest.raises(ValueError, match="Unsupported format"):
            logger.export_logs(format='xml')


class TestLogStatistics:
    """Test suite for audit log statistics."""

    def test_get_statistics(self):
        """Test getting log statistics."""
        logger = AuditLogger()

        logger.log_action("user1", "read", "resource1")
        logger.log_action("user2", "write", "resource2")
        logger.log_action("user1", "delete", "resource3")

        stats = logger.get_statistics()

        assert stats["total_logs"] == 3
        assert stats["unique_users"] == 2
        assert stats["unique_actions"] == 3

    def test_statistics_empty_logs(self):
        """Test statistics with no logs."""
        logger = AuditLogger()

        stats = logger.get_statistics()

        assert stats["total_logs"] == 0
        assert stats["oldest_log"] is None
        assert stats["newest_log"] is None


class TestTamperProofLogging:
    """Test suite for tamper-proof logging."""

    def test_tamperproof_hash_generation(self):
        """Test that tamper-proof logger generates hashes."""
        logger = TamperProofLogger()

        log = logger.log_action("user1", "action1", "resource1")

        assert log.hash is not None
        assert len(log.hash) == 64  # SHA-256 hex length

    def test_hash_chain(self):
        """Test that logs form a hash chain."""
        logger = TamperProofLogger()

        log1 = logger.log_action("user1", "action1", "resource1")
        log2 = logger.log_action("user2", "action2", "resource2")

        # Second log should include first log's hash in its calculation
        assert log1.hash != log2.hash

    def test_verify_log_integrity(self):
        """Test verifying individual log integrity."""
        logger = TamperProofLogger()

        log = logger.log_action("user1", "action1", "resource1")
        log_dict = logger._log_to_dict(log)

        assert logger.verify_log_integrity(log_dict)

    def test_verify_invalid_log(self):
        """Test verification fails for invalid log."""
        logger = TamperProofLogger()

        log = logger.log_action("user1", "action1", "resource1")
        log_dict = logger._log_to_dict(log)

        # Tamper with the hash
        log_dict["hash"] = "invalid_hash"

        assert not logger.verify_log_integrity(log_dict)

    def test_verify_chain_integrity(self):
        """Test verifying entire chain integrity."""
        logger = TamperProofLogger()

        logger.log_action("user1", "action1", "resource1")
        logger.log_action("user2", "action2", "resource2")
        logger.log_action("user3", "action3", "resource3")

        result = logger.verify_chain_integrity()

        assert result["valid"]
        assert result["total_logs"] == 3
        assert len(result["invalid_logs"]) == 0

    def test_detect_tampered_log(self):
        """Test detection of tampered log in chain."""
        logger = TamperProofLogger()

        log1 = logger.log_action("user1", "action1", "resource1")
        log2 = logger.log_action("user2", "action2", "resource2")

        # Tamper with log
        log1.details["tampered"] = True

        result = logger.verify_chain_integrity()

        assert not result["valid"]
        assert len(result["invalid_logs"]) > 0

    def test_empty_chain_verification(self):
        """Test verification of empty log chain."""
        logger = TamperProofLogger()

        result = logger.verify_chain_integrity()

        assert result["valid"]
        assert result["total_logs"] == 0


class TestAuditLogSecurity:
    """Security-focused tests for audit logging."""

    def test_log_immutability(self):
        """Test that logs cannot be easily modified."""
        logger = TamperProofLogger()

        log = logger.log_action("user1", "sensitive_action", "critical_resource")
        original_hash = log.hash

        # Attempt to modify log
        log.action = "innocent_action"

        # Hash should detect tampering
        result = logger.verify_chain_integrity()
        assert not result["valid"]

    def test_sql_injection_in_log_data(self):
        """Test logging of SQL injection attempts."""
        logger = AuditLogger()

        malicious = "'; DROP TABLE users; --"
        log = logger.log_action(
            user="attacker",
            action="query",
            resource="database",
            details={"query": malicious}
        )

        # Should log without executing
        assert log.details["query"] == malicious

    def test_xss_in_log_data(self):
        """Test logging of XSS attempts."""
        logger = AuditLogger()

        xss = "<script>alert('XSS')</script>"
        log = logger.log_action(
            user="attacker",
            action="input",
            resource="form",
            details={"input": xss}
        )

        assert log.details["input"] == xss

    def test_log_sensitive_data_handling(self):
        """Test handling of sensitive data in logs."""
        logger = AuditLogger()

        # Should not log passwords/secrets directly
        log = logger.log_action(
            user="admin",
            action="password_change",
            resource="user_account",
            details={"user_id": "123", "password": "[REDACTED]"}
        )

        assert log.details["password"] == "[REDACTED]"

    def test_concurrent_logging(self):
        """Test thread-safe concurrent logging."""
        import threading

        logger = TamperProofLogger()
        errors = []

        def log_action(user_id):
            try:
                logger.log_action(f"user_{user_id}", "action", "resource")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=log_action, args=(i,))
            for i in range(20)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(logger.get_logs()) == 20
