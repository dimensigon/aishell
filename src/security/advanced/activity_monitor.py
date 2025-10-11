"""
Database Activity Monitor and Anomaly Detection

Monitors database operations and detects suspicious patterns.
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Security threat levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(Enum):
    """Types of security events"""
    LOGIN = "login"
    LOGOUT = "logout"
    QUERY_EXECUTE = "query_execute"
    SCHEMA_CHANGE = "schema_change"
    DATA_EXPORT = "data_export"
    PERMISSION_CHANGE = "permission_change"
    FAILED_AUTH = "failed_auth"
    SUSPICIOUS_PATTERN = "suspicious_pattern"


@dataclass
class SecurityEvent:
    """A security event record"""
    event_type: EventType
    user_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    threat_level: ThreatLevel = ThreatLevel.INFO
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'threat_level': self.threat_level.value,
            'description': self.description,
            'metadata': self.metadata,
            'ip_address': self.ip_address,
            'session_id': self.session_id
        }


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection"""
    is_anomaly: bool
    threat_level: ThreatLevel
    reasons: List[str] = field(default_factory=list)
    confidence: float = 0.0
    recommended_action: Optional[str] = None


class ActivityMonitor:
    """
    Database Activity Monitor

    Tracks database operations and security events in real-time.
    """

    def __init__(self, retention_days: int = 90):
        """
        Initialize activity monitor

        Args:
            retention_days: Number of days to retain events
        """
        self.retention_days = retention_days
        self.events: deque = deque(maxlen=10000)  # Ring buffer
        self.event_counts: Dict[str, int] = defaultdict(int)
        self.user_activity: Dict[str, List[SecurityEvent]] = defaultdict(list)

    def log_event(
        self,
        event_type: EventType,
        user_id: str,
        description: str = "",
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        threat_level: ThreatLevel = ThreatLevel.INFO
    ) -> SecurityEvent:
        """
        Log a security event

        Args:
            event_type: Type of event
            user_id: User identifier
            description: Event description
            metadata: Additional event data
            ip_address: Client IP address
            session_id: Session identifier
            threat_level: Threat level

        Returns:
            Created SecurityEvent
        """
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            description=description,
            metadata=metadata or {},
            ip_address=ip_address,
            session_id=session_id,
            threat_level=threat_level
        )

        # Store event
        self.events.append(event)
        self.event_counts[event_type.value] += 1
        self.user_activity[user_id].append(event)

        # Trim user activity history
        max_user_events = 1000
        if len(self.user_activity[user_id]) > max_user_events:
            self.user_activity[user_id] = self.user_activity[user_id][-max_user_events:]

        # Log based on threat level
        if threat_level == ThreatLevel.CRITICAL:
            logger.critical(f"CRITICAL: {event_type.value} by {user_id}: {description}")
        elif threat_level == ThreatLevel.HIGH:
            logger.error(f"HIGH: {event_type.value} by {user_id}: {description}")
        elif threat_level == ThreatLevel.MEDIUM:
            logger.warning(f"MEDIUM: {event_type.value} by {user_id}: {description}")
        else:
            logger.info(f"{event_type.value} by {user_id}: {description}")

        return event

    def log_query(
        self,
        user_id: str,
        sql_query: str,
        execution_time: float,
        rows_affected: int,
        success: bool,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> SecurityEvent:
        """
        Log SQL query execution

        Args:
            user_id: User who executed query
            sql_query: SQL query text
            execution_time: Execution time in seconds
            rows_affected: Number of rows affected
            success: Whether query succeeded
            ip_address: Client IP
            session_id: Session ID

        Returns:
            Created SecurityEvent
        """
        # Determine threat level based on query
        threat_level = self._assess_query_threat(sql_query, rows_affected)

        description = f"Executed query: {sql_query[:100]}..."

        return self.log_event(
            event_type=EventType.QUERY_EXECUTE,
            user_id=user_id,
            description=description,
            metadata={
                'sql_query': sql_query,
                'execution_time': execution_time,
                'rows_affected': rows_affected,
                'success': success
            },
            ip_address=ip_address,
            session_id=session_id,
            threat_level=threat_level
        )

    def get_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        since: Optional[datetime] = None,
        threat_level: Optional[ThreatLevel] = None,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """
        Retrieve security events with filtering

        Args:
            user_id: Filter by user
            event_type: Filter by event type
            since: Filter by timestamp
            threat_level: Filter by threat level
            limit: Maximum events to return

        Returns:
            List of matching events
        """
        filtered = []

        for event in reversed(self.events):  # Most recent first
            # Apply filters
            if user_id and event.user_id != user_id:
                continue
            if event_type and event.event_type != event_type:
                continue
            if since and event.timestamp < since:
                continue
            if threat_level and event.threat_level != threat_level:
                continue

            filtered.append(event)

            if len(filtered) >= limit:
                break

        return filtered

    def get_statistics(
        self,
        user_id: Optional[str] = None,
        time_window: timedelta = timedelta(hours=24)
    ) -> Dict[str, Any]:
        """
        Get activity statistics

        Args:
            user_id: Filter by user (None for all users)
            time_window: Time window for statistics

        Returns:
            Statistics dictionary
        """
        cutoff = datetime.now() - time_window

        # Filter events
        events = [e for e in self.events if e.timestamp >= cutoff]
        if user_id:
            events = [e for e in events if e.user_id == user_id]

        # Calculate statistics
        total_events = len(events)
        events_by_type = defaultdict(int)
        events_by_threat = defaultdict(int)
        unique_users = set()

        for event in events:
            events_by_type[event.event_type.value] += 1
            events_by_threat[event.threat_level.value] += 1
            unique_users.add(event.user_id)

        return {
            'total_events': total_events,
            'unique_users': len(unique_users),
            'time_window_hours': time_window.total_seconds() / 3600,
            'events_by_type': dict(events_by_type),
            'events_by_threat': dict(events_by_threat),
            'high_threat_count': events_by_threat[ThreatLevel.HIGH.value] +
                                 events_by_threat[ThreatLevel.CRITICAL.value]
        }

    def get_user_activity_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get activity summary for specific user

        Args:
            user_id: User identifier

        Returns:
            Activity summary
        """
        events = self.user_activity.get(user_id, [])

        if not events:
            return {'user_id': user_id, 'no_activity': True}

        recent_events = [e for e in events if e.timestamp >= datetime.now() - timedelta(hours=24)]

        return {
            'user_id': user_id,
            'total_events': len(events),
            'recent_events_24h': len(recent_events),
            'first_activity': events[0].timestamp.isoformat() if events else None,
            'last_activity': events[-1].timestamp.isoformat() if events else None,
            'event_types': {et.value: sum(1 for e in events if e.event_type == et)
                           for et in EventType}
        }

    def _assess_query_threat(self, sql_query: str, rows_affected: int) -> ThreatLevel:
        """Assess threat level of SQL query"""
        sql_upper = sql_query.upper()

        # Critical threats
        if 'DROP TABLE' in sql_upper or 'DROP DATABASE' in sql_upper:
            return ThreatLevel.CRITICAL
        if 'TRUNCATE' in sql_upper:
            return ThreatLevel.HIGH

        # High threats
        if rows_affected > 10000:  # Large data modification
            return ThreatLevel.HIGH
        if 'DELETE' in sql_upper and 'WHERE' not in sql_upper:
            return ThreatLevel.HIGH

        # Medium threats
        if rows_affected > 1000:
            return ThreatLevel.MEDIUM
        if any(keyword in sql_upper for keyword in ['ALTER', 'CREATE', 'GRANT', 'REVOKE']):
            return ThreatLevel.MEDIUM

        return ThreatLevel.INFO


class AnomalyDetector:
    """
    Anomaly Detection for Database Activities

    Detects unusual patterns that may indicate security threats.
    """

    def __init__(self, activity_monitor: ActivityMonitor):
        """
        Initialize anomaly detector

        Args:
            activity_monitor: ActivityMonitor instance to analyze
        """
        self.monitor = activity_monitor

        # Detection thresholds
        self.thresholds = {
            'failed_auth_count': 5,  # Failed auth attempts in time window
            'query_rate_multiplier': 5.0,  # Queries per minute vs baseline
            'unusual_time_queries': True,  # Queries during off-hours
            'data_export_threshold': 100000,  # Rows exported
            'schema_changes_per_hour': 10
        }

        # Baseline patterns (learned over time)
        self.baseline_patterns: Dict[str, Any] = {
            'avg_queries_per_hour': {},
            'typical_query_times': {},
            'common_query_patterns': set()
        }

    def detect_anomalies(
        self,
        user_id: str,
        time_window: timedelta = timedelta(hours=1)
    ) -> AnomalyDetectionResult:
        """
        Detect anomalies in user activity

        Args:
            user_id: User to analyze
            time_window: Time window for analysis

        Returns:
            AnomalyDetectionResult
        """
        reasons = []
        max_threat = ThreatLevel.INFO

        # Get recent events
        cutoff = datetime.now() - time_window
        events = [e for e in self.monitor.user_activity.get(user_id, [])
                 if e.timestamp >= cutoff]

        if not events:
            return AnomalyDetectionResult(
                is_anomaly=False,
                threat_level=ThreatLevel.INFO
            )

        # Check for failed authentication attempts
        failed_auths = sum(1 for e in events if e.event_type == EventType.FAILED_AUTH)
        if failed_auths >= self.thresholds['failed_auth_count']:
            reasons.append(f"Multiple failed authentication attempts ({failed_auths})")
            max_threat = ThreatLevel.HIGH

        # Check for high query rate
        query_events = [e for e in events if e.event_type == EventType.QUERY_EXECUTE]
        queries_per_minute = len(query_events) / (time_window.total_seconds() / 60)

        baseline_qpm = self.baseline_patterns['avg_queries_per_hour'].get(user_id, 10) / 60
        if queries_per_minute > baseline_qpm * self.thresholds['query_rate_multiplier']:
            reasons.append(f"Unusually high query rate ({queries_per_minute:.1f}/min vs baseline {baseline_qpm:.1f}/min)")
            max_threat = max(max_threat, ThreatLevel.MEDIUM)

        # Check for unusual time access
        if self.thresholds['unusual_time_queries']:
            off_hours_queries = sum(1 for e in query_events
                                   if e.timestamp.hour < 6 or e.timestamp.hour > 22)
            if off_hours_queries > 0 and off_hours_queries == len(query_events):
                reasons.append(f"All queries during unusual hours (off-hours: {off_hours_queries})")
                max_threat = max(max_threat, ThreatLevel.MEDIUM)

        # Check for large data exports
        total_rows_affected = sum(e.metadata.get('rows_affected', 0) for e in query_events)
        if total_rows_affected > self.thresholds['data_export_threshold']:
            reasons.append(f"Large data export detected ({total_rows_affected} rows)")
            max_threat = max(max_threat, ThreatLevel.HIGH)

        # Check for schema changes
        schema_changes = sum(1 for e in events if e.event_type == EventType.SCHEMA_CHANGE)
        if schema_changes > self.thresholds['schema_changes_per_hour']:
            reasons.append(f"Excessive schema changes ({schema_changes})")
            max_threat = max(max_threat, ThreatLevel.HIGH)

        # Check for SQL injection patterns
        injection_patterns = self._detect_injection_patterns(query_events)
        if injection_patterns:
            reasons.extend(injection_patterns)
            max_threat = ThreatLevel.CRITICAL

        # Determine if this is an anomaly
        is_anomaly = len(reasons) > 0

        # Calculate confidence
        confidence = min(len(reasons) * 0.25, 1.0)

        # Recommended action
        recommended_action = None
        if max_threat in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            recommended_action = "Immediately review user activity and consider suspending account"
        elif max_threat == ThreatLevel.MEDIUM:
            recommended_action = "Monitor user closely and investigate unusual patterns"

        return AnomalyDetectionResult(
            is_anomaly=is_anomaly,
            threat_level=max_threat,
            reasons=reasons,
            confidence=confidence,
            recommended_action=recommended_action
        )

    def _detect_injection_patterns(self, query_events: List[SecurityEvent]) -> List[str]:
        """Detect SQL injection patterns"""
        patterns_found = []

        injection_signatures = [
            ("' OR '1'='1", "Classic SQL injection (OR 1=1)"),
            ("UNION SELECT", "UNION-based injection"),
            ("'; DROP TABLE", "Destructive injection attempt"),
            ("' AND '1'='1", "Boolean-based injection"),
            ("EXEC(", "Command execution attempt"),
            ("<script>", "XSS attempt in query")
        ]

        for event in query_events:
            sql = event.metadata.get('sql_query', '')
            for signature, description in injection_signatures:
                if signature.upper() in sql.upper():
                    patterns_found.append(f"Potential SQL injection: {description}")

        return patterns_found

    def update_baseline(self, user_id: str):
        """
        Update baseline patterns for user

        Args:
            user_id: User identifier
        """
        # Get user's historical activity
        events = self.monitor.user_activity.get(user_id, [])
        if not events:
            return

        # Calculate average queries per hour
        time_span = (events[-1].timestamp - events[0].timestamp).total_seconds() / 3600
        if time_span > 0:
            query_count = sum(1 for e in events if e.event_type == EventType.QUERY_EXECUTE)
            avg_qph = query_count / time_span
            self.baseline_patterns['avg_queries_per_hour'][user_id] = avg_qph

        logger.info(f"Updated baseline for user {user_id}")

    def get_threat_dashboard(self) -> Dict[str, Any]:
        """
        Get security threat dashboard

        Returns:
            Dashboard data with current threats
        """
        recent_events = self.monitor.get_events(
            since=datetime.now() - timedelta(hours=24),
            limit=1000
        )

        high_threats = [e for e in recent_events
                       if e.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]]

        # Check for anomalies across all active users
        active_users = set(e.user_id for e in recent_events)
        users_with_anomalies = []

        for user_id in active_users:
            result = self.detect_anomalies(user_id, time_window=timedelta(hours=1))
            if result.is_anomaly and result.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                users_with_anomalies.append({
                    'user_id': user_id,
                    'threat_level': result.threat_level.value,
                    'reasons': result.reasons
                })

        return {
            'timestamp': datetime.now().isoformat(),
            'high_threat_events_24h': len(high_threats),
            'users_with_anomalies': users_with_anomalies,
            'total_active_users': len(active_users),
            'recent_critical_events': [
                e.to_dict() for e in high_threats[:10]
            ]
        }
