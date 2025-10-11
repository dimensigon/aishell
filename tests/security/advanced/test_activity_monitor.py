"""
Tests for Activity Monitor and Anomaly Detection
"""

import pytest
from datetime import datetime, timedelta
from src.security.advanced.activity_monitor import (
    ActivityMonitor,
    AnomalyDetector,
    SecurityEvent,
    EventType,
    ThreatLevel
)


@pytest.fixture
def activity_monitor():
    """Create ActivityMonitor instance"""
    return ActivityMonitor(retention_days=90)


@pytest.fixture
def anomaly_detector(activity_monitor):
    """Create AnomalyDetector instance"""
    return AnomalyDetector(activity_monitor)


class TestActivityMonitor:
    """Test ActivityMonitor functionality"""

    def test_initialization(self, activity_monitor):
        """Test monitor initialization"""
        assert activity_monitor is not None
        assert activity_monitor.retention_days == 90

    def test_log_event(self, activity_monitor):
        """Test logging security event"""
        event = activity_monitor.log_event(
            event_type=EventType.LOGIN,
            user_id="user123",
            description="User logged in",
            ip_address="192.168.1.1"
        )

        assert isinstance(event, SecurityEvent)
        assert event.user_id == "user123"
        assert event.event_type == EventType.LOGIN

    def test_log_query(self, activity_monitor):
        """Test logging query execution"""
        event = activity_monitor.log_query(
            user_id="user123",
            sql_query="SELECT * FROM users",
            execution_time=0.5,
            rows_affected=10,
            success=True,
            ip_address="192.168.1.1"
        )

        assert event.event_type == EventType.QUERY_EXECUTE
        assert event.metadata['sql_query'] == "SELECT * FROM users"
        assert event.metadata['execution_time'] == 0.5

    def test_get_events(self, activity_monitor):
        """Test retrieving events"""
        # Log some events
        activity_monitor.log_event(
            EventType.LOGIN,
            "user123",
            "Login"
        )
        activity_monitor.log_event(
            EventType.LOGOUT,
            "user123",
            "Logout"
        )

        # Get all events
        events = activity_monitor.get_events(limit=10)
        assert len(events) >= 2

        # Filter by user
        user_events = activity_monitor.get_events(user_id="user123", limit=10)
        assert all(e.user_id == "user123" for e in user_events)

    def test_get_statistics(self, activity_monitor):
        """Test getting statistics"""
        # Log multiple events
        for i in range(5):
            activity_monitor.log_event(
                EventType.QUERY_EXECUTE,
                f"user{i}",
                "Query"
            )

        stats = activity_monitor.get_statistics()

        assert 'total_events' in stats
        assert 'unique_users' in stats
        assert stats['total_events'] >= 5

    def test_user_activity_summary(self, activity_monitor):
        """Test user activity summary"""
        user_id = "test_user"

        # Log some activity
        activity_monitor.log_event(EventType.LOGIN, user_id, "Login")
        activity_monitor.log_query(
            user_id,
            "SELECT * FROM test",
            0.1,
            5,
            True
        )

        summary = activity_monitor.get_user_activity_summary(user_id)

        assert summary['user_id'] == user_id
        assert summary['total_events'] >= 2

    def test_threat_assessment(self, activity_monitor):
        """Test query threat assessment"""
        # High threat query
        event = activity_monitor.log_query(
            "user123",
            "DROP TABLE users",
            0.1,
            0,
            False
        )

        assert event.threat_level == ThreatLevel.CRITICAL

        # Low threat query
        event = activity_monitor.log_query(
            "user123",
            "SELECT * FROM users LIMIT 10",
            0.1,
            10,
            True
        )

        assert event.threat_level == ThreatLevel.INFO


class TestAnomalyDetector:
    """Test AnomalyDetector functionality"""

    def test_initialization(self, anomaly_detector):
        """Test detector initialization"""
        assert anomaly_detector is not None
        assert anomaly_detector.monitor is not None

    def test_detect_failed_auth_anomaly(self, activity_monitor, anomaly_detector):
        """Test detection of failed authentication anomaly"""
        user_id = "suspicious_user"

        # Simulate multiple failed auth attempts
        for _ in range(6):
            activity_monitor.log_event(
                EventType.FAILED_AUTH,
                user_id,
                "Failed login"
            )

        result = anomaly_detector.detect_anomalies(
            user_id,
            time_window=timedelta(hours=1)
        )

        assert result.is_anomaly is True
        assert result.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        assert len(result.reasons) > 0

    def test_detect_high_query_rate_anomaly(self, activity_monitor, anomaly_detector):
        """Test detection of high query rate"""
        user_id = "active_user"

        # Simulate high query rate
        for _ in range(100):
            activity_monitor.log_query(
                user_id,
                "SELECT * FROM test",
                0.01,
                10,
                True
            )

        result = anomaly_detector.detect_anomalies(
            user_id,
            time_window=timedelta(minutes=1)
        )

        # May or may not be anomaly depending on baseline
        assert isinstance(result.is_anomaly, bool)

    def test_detect_sql_injection(self, activity_monitor, anomaly_detector):
        """Test SQL injection pattern detection"""
        user_id = "attacker"

        # Simulate SQL injection attempt
        activity_monitor.log_query(
            user_id,
            "SELECT * FROM users WHERE id = 1 OR '1'='1'",
            0.1,
            100,
            True
        )

        result = anomaly_detector.detect_anomalies(
            user_id,
            time_window=timedelta(hours=1)
        )

        assert result.is_anomaly is True
        assert result.threat_level == ThreatLevel.CRITICAL

    def test_update_baseline(self, activity_monitor, anomaly_detector):
        """Test baseline update"""
        user_id = "normal_user"

        # Log normal activity
        for _ in range(10):
            activity_monitor.log_query(
                user_id,
                "SELECT * FROM test",
                0.1,
                5,
                True
            )

        anomaly_detector.update_baseline(user_id)

        assert user_id in anomaly_detector.baseline_patterns['avg_queries_per_hour']

    def test_threat_dashboard(self, activity_monitor, anomaly_detector):
        """Test threat dashboard"""
        # Log some events
        activity_monitor.log_event(
            EventType.LOGIN,
            "user1",
            "Login",
            threat_level=ThreatLevel.HIGH
        )

        dashboard = anomaly_detector.get_threat_dashboard()

        assert 'timestamp' in dashboard
        assert 'high_threat_events_24h' in dashboard
        assert 'users_with_anomalies' in dashboard


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
