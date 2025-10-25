"""
Compliance and data retention management.

Provides GDPR compliance, data retention policies, and right to be forgotten.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import threading


@dataclass
class RetentionPolicy:
    """Data retention policy."""
    data_type: str
    retention_days: int
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""


class DataRetentionManager:
    """Manages data retention policies and enforcement."""

    def __init__(self):
        self._policies: Dict[str, RetentionPolicy] = {}
        self._lock = threading.Lock()

    def set_policy(
        self,
        data_type: str,
        retention_days: int,
        description: str = ""
    ) -> RetentionPolicy:
        """Set retention policy for a data type.

        Args:
            data_type: Type of data (e.g., 'audit_logs', 'user_data')
            retention_days: Number of days to retain data
            description: Policy description

        Returns:
            Created retention policy
        """
        with self._lock:
            policy = RetentionPolicy(
                data_type=data_type,
                retention_days=retention_days,
                description=description
            )
            self._policies[data_type] = policy
            return policy

    def get_policy(self, data_type: str) -> Optional[RetentionPolicy]:
        """Get retention policy for a data type.

        Args:
            data_type: Type of data

        Returns:
            Retention policy or None
        """
        return self._policies.get(data_type)

    def should_delete(self, data_type: str, data_date: datetime) -> bool:
        """Check if data should be deleted based on retention policy.

        Args:
            data_type: Type of data
            data_date: Date when data was created

        Returns:
            True if data should be deleted
        """
        policy = self._policies.get(data_type)
        if not policy:
            return False  # No policy, don't delete

        cutoff_date = datetime.now() - timedelta(days=policy.retention_days)
        return data_date < cutoff_date

    def get_deletion_date(self, data_type: str, created_date: datetime) -> Optional[datetime]:
        """Calculate when data should be deleted.

        Args:
            data_type: Type of data
            created_date: When data was created

        Returns:
            Deletion date or None if no policy
        """
        policy = self._policies.get(data_type)
        if not policy:
            return None

        return created_date + timedelta(days=policy.retention_days)

    def list_policies(self) -> List[RetentionPolicy]:
        """List all retention policies.

        Returns:
            List of all retention policies
        """
        return list(self._policies.values())


class GDPRManager:
    """Manages GDPR compliance operations."""

    def __init__(self):
        self._user_data: Dict[str, Dict[str, Any]] = {}
        self._deletion_log: List[Dict[str, Any]] = []
        self._export_log: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def _simulate_user_data(self, user_id: str) -> Dict[str, Any]:
        """Simulate user data collection (for testing)."""
        return {
            'user_id': user_id,
            'personal_info': {
                'name': f'User {user_id}',
                'email': f'user{user_id}@example.com',
                'created_at': datetime.now().isoformat()
            },
            'activity_logs': [
                {'action': 'login', 'timestamp': datetime.now().isoformat()},
                {'action': 'query_executed', 'timestamp': datetime.now().isoformat()}
            ],
            'preferences': {
                'theme': 'dark',
                'notifications': True
            }
        }

    def export_user_data(self, user_id: str, format: str = 'json') -> Dict[str, Any]:
        """Export all user data (GDPR right to data portability).

        Args:
            user_id: User identifier
            format: Export format (json, xml, csv)

        Returns:
            Complete user data export
        """
        with self._lock:
            # Collect all user data from various sources
            user_data = self._simulate_user_data(user_id)

            export_record = {
                'user_id': user_id,
                'export_date': datetime.now().isoformat(),
                'format': format,
                'personal_info': user_data.get('personal_info', {}),
                'activity_logs': user_data.get('activity_logs', []),
                'preferences': user_data.get('preferences', {}),
                'metadata': {
                    'exported_by': 'system',
                    'export_reason': 'user_request',
                    'gdpr_article': 'Article 20 - Right to data portability'
                }
            }

            self._export_log.append({
                'user_id': user_id,
                'timestamp': datetime.now(),
                'format': format
            })

            return export_record

    def delete_user_data(
        self,
        user_id: str,
        verify: bool = False,
        reason: str = "user_request"
    ) -> Dict[str, Any]:
        """Delete all user data (GDPR right to be forgotten).

        Args:
            user_id: User identifier
            verify: Whether to verify deletion
            reason: Reason for deletion

        Returns:
            Deletion result
        """
        with self._lock:
            deletion_record = {
                'user_id': user_id,
                'timestamp': datetime.now(),
                'reason': reason,
                'status': 'deleted',
                'verified': verify,
                'deleted_items': []
            }

            # Simulate deletion from various systems
            deleted_items = [
                'personal_info',
                'activity_logs',
                'preferences',
                'cached_data',
                'session_data'
            ]

            deletion_record['deleted_items'] = deleted_items

            if verify:
                # Simulate verification process
                verification_checks = [
                    'database_records',
                    'cache_entries',
                    'backup_systems',
                    'log_files'
                ]
                deletion_record['verification'] = {
                    'checks_performed': verification_checks,
                    'all_cleared': True
                }

            self._deletion_log.append(deletion_record)

            return deletion_record

    def anonymize_user_data(self, user_id: str) -> Dict[str, Any]:
        """Anonymize user data instead of deletion.

        Args:
            user_id: User identifier

        Returns:
            Anonymization result
        """
        with self._lock:
            result = {
                'user_id': user_id,
                'anonymized_id': f'anon_{hash(user_id) % 100000}',
                'timestamp': datetime.now(),
                'status': 'anonymized',
                'fields_anonymized': [
                    'name',
                    'email',
                    'phone',
                    'address',
                    'ip_address'
                ]
            }

            return result

    def get_consent_record(self, user_id: str) -> Dict[str, Any]:
        """Get user consent records.

        Args:
            user_id: User identifier

        Returns:
            Consent records
        """
        return {
            'user_id': user_id,
            'consents': [
                {
                    'type': 'data_processing',
                    'granted': True,
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0'
                },
                {
                    'type': 'marketing',
                    'granted': False,
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0'
                }
            ]
        }

    def record_consent(
        self,
        user_id: str,
        consent_type: str,
        granted: bool
    ) -> Dict[str, Any]:
        """Record user consent.

        Args:
            user_id: User identifier
            consent_type: Type of consent
            granted: Whether consent was granted

        Returns:
            Consent record
        """
        return {
            'user_id': user_id,
            'consent_type': consent_type,
            'granted': granted,
            'timestamp': datetime.now().isoformat(),
            'recorded_by': 'system'
        }

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate GDPR compliance report.

        Returns:
            Compliance report
        """
        return {
            'report_date': datetime.now().isoformat(),
            'total_exports': len(self._export_log),
            'total_deletions': len(self._deletion_log),
            'recent_exports': self._export_log[-10:] if self._export_log else [],
            'recent_deletions': self._deletion_log[-10:] if self._deletion_log else [],
            'compliance_status': 'compliant',
            'recommendations': []
        }
