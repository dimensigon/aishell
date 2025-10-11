"""
Comprehensive audit logging with tamper-proof features.

Provides audit trail, search capabilities, and integrity verification.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import hashlib
import json
import threading


@dataclass
class AuditLog:
    """Represents an audit log entry."""
    log_id: str
    user: str
    action: str
    resource: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    hash: Optional[str] = None


class AuditLogger:
    """Basic audit logger with search and retention."""

    def __init__(self, retention_days: int = 90):
        """Initialize audit logger.

        Args:
            retention_days: Number of days to retain logs
        """
        self._logs: List[AuditLog] = []
        self._retention_days = retention_days
        self._lock = threading.Lock()
        self._log_counter = 0

    def log_action(
        self,
        user: str,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log an action.

        Args:
            user: User performing action
            action: Action performed
            resource: Resource affected
            details: Additional details
            timestamp: Optional timestamp (defaults to now)
            ip_address: Optional IP address
            user_agent: Optional user agent

        Returns:
            Created audit log entry
        """
        with self._lock:
            self._log_counter += 1
            log_id = f'log_{self._log_counter}_{datetime.now().timestamp()}'

            log_entry = AuditLog(
                log_id=log_id,
                user=user,
                action=action,
                resource=resource,
                timestamp=timestamp or datetime.now(),
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent
            )

            self._logs.append(log_entry)
            return log_entry

    def get_logs(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit logs.

        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip

        Returns:
            List of audit log entries
        """
        logs = self._logs[offset:]
        if limit:
            logs = logs[:limit]

        return [self._log_to_dict(log) for log in logs]

    def search_logs(
        self,
        user: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Search audit logs.

        Args:
            user: Filter by user
            action: Filter by action
            resource: Filter by resource
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            Filtered audit logs
        """
        results = []

        for log in self._logs:
            # Apply filters
            if user and log.user != user:
                continue
            if action and log.action != action:
                continue
            if resource and log.resource != resource:
                continue
            if start_date and log.timestamp < start_date:
                continue
            if end_date and log.timestamp > end_date:
                continue

            results.append(self._log_to_dict(log))

        return results

    def cleanup_old_logs(self) -> int:
        """Remove logs older than retention period.

        Returns:
            Number of logs removed
        """
        cutoff_date = datetime.now() - timedelta(days=self._retention_days)

        with self._lock:
            original_count = len(self._logs)
            self._logs = [
                log for log in self._logs
                if log.timestamp >= cutoff_date
            ]
            removed_count = original_count - len(self._logs)

        return removed_count

    def export_logs(
        self,
        format: str = 'json',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export logs for compliance.

        Args:
            format: Export format (json, csv)
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Exported logs as string
        """
        # Filter logs by date range
        logs = self.search_logs(start_date=start_date, end_date=end_date)

        export_data = {
            'export_date': datetime.now().isoformat(),
            'log_count': len(logs),
            'retention_days': self._retention_days,
            'logs': logs
        }

        if format == 'json':
            return json.dumps(export_data, indent=2, default=str)
        elif format == 'csv':
            # Simple CSV export
            lines = ['timestamp,user,action,resource,details']
            for log in logs:
                lines.append(
                    f"{log['timestamp']},{log['user']},{log['action']},"
                    f"{log['resource']},{json.dumps(log['details'])}"
                )
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit log statistics.

        Returns:
            Statistics dictionary
        """
        return {
            'total_logs': len(self._logs),
            'retention_days': self._retention_days,
            'oldest_log': min(log.timestamp for log in self._logs) if self._logs else None,
            'newest_log': max(log.timestamp for log in self._logs) if self._logs else None,
            'unique_users': len(set(log.user for log in self._logs)),
            'unique_actions': len(set(log.action for log in self._logs))
        }

    def _log_to_dict(self, log: AuditLog) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        return {
            'log_id': log.log_id,
            'user': log.user,
            'action': log.action,
            'resource': log.resource,
            'timestamp': log.timestamp,
            'details': log.details,
            'ip_address': log.ip_address,
            'user_agent': log.user_agent,
            'hash': log.hash
        }


class TamperProofLogger(AuditLogger):
    """Audit logger with tamper-proof features using hash chains."""

    def __init__(self, retention_days: int = 90):
        """Initialize tamper-proof logger.

        Args:
            retention_days: Number of days to retain logs
        """
        super().__init__(retention_days)
        self._previous_hash: Optional[str] = None

    def log_action(
        self,
        user: str,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log an action with hash chain.

        Args:
            user: User performing action
            action: Action performed
            resource: Resource affected
            details: Additional details
            timestamp: Optional timestamp
            ip_address: Optional IP address
            user_agent: Optional user agent

        Returns:
            Created audit log entry with hash
        """
        log_entry = super().log_action(
            user, action, resource, details,
            timestamp, ip_address, user_agent
        )

        # Calculate hash including previous hash (chain)
        log_entry.hash = self._calculate_hash(log_entry)
        self._previous_hash = log_entry.hash

        return log_entry

    def _calculate_hash(self, log: AuditLog) -> str:
        """Calculate SHA-256 hash of log entry.

        Args:
            log: Log entry to hash

        Returns:
            Hexadecimal hash string
        """
        # Create hash input from log data
        hash_input = json.dumps({
            'user': log.user,
            'action': log.action,
            'resource': log.resource,
            'timestamp': log.timestamp.isoformat(),
            'details': log.details,
            'previous_hash': self._previous_hash
        }, sort_keys=True)

        return hashlib.sha256(hash_input.encode()).hexdigest()

    def verify_log_integrity(self, log: Dict[str, Any]) -> bool:
        """Verify integrity of a log entry.

        Args:
            log: Log entry dictionary

        Returns:
            True if log is valid and unmodified
        """
        if not log.get('hash'):
            return False

        # Find the log in our list
        for stored_log in self._logs:
            if stored_log.log_id == log.get('log_id'):
                # Verify hash matches
                return stored_log.hash == log.get('hash')

        return False

    def verify_chain_integrity(self) -> Dict[str, Any]:
        """Verify integrity of entire log chain.

        Returns:
            Verification result
        """
        if not self._logs:
            return {
                'valid': True,
                'total_logs': 0,
                'invalid_logs': []
            }

        invalid_logs = []
        previous_hash = None

        for log in self._logs:
            # Recalculate expected hash
            temp_previous = self._previous_hash
            self._previous_hash = previous_hash

            expected_hash = self._calculate_hash(log)

            self._previous_hash = temp_previous

            if log.hash != expected_hash:
                invalid_logs.append({
                    'log_id': log.log_id,
                    'expected_hash': expected_hash,
                    'actual_hash': log.hash
                })

            previous_hash = log.hash

        return {
            'valid': len(invalid_logs) == 0,
            'total_logs': len(self._logs),
            'invalid_logs': invalid_logs,
            'verified_at': datetime.now().isoformat()
        }
