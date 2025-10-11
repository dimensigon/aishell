"""
Resource Quota Management

Provides per-tenant resource limits and usage tracking:
- Query rate limiting
- Storage quotas
- Concurrent connection limits
- API request quotas
- Custom resource limits
"""

import time
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
from pathlib import Path


class QuotaType(Enum):
    """Types of resource quotas"""
    QUERIES_PER_MINUTE = "queries_per_minute"
    QUERIES_PER_HOUR = "queries_per_hour"
    QUERIES_PER_DAY = "queries_per_day"
    STORAGE_MB = "storage_mb"
    MAX_CONNECTIONS = "max_connections"
    API_REQUESTS_PER_DAY = "api_requests_per_day"
    MAX_DATABASES = "max_databases"
    MAX_USERS = "max_users"
    CUSTOM = "custom"


@dataclass
class ResourceQuota:
    """Resource quota configuration"""
    tenant_id: str
    quota_type: QuotaType
    limit: int
    current_usage: int = 0
    soft_limit: Optional[int] = None  # Warning threshold
    reset_period: Optional[str] = None  # e.g., 'hourly', 'daily', 'monthly'
    last_reset: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['quota_type'] = self.quota_type.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceQuota':
        """Create from dictionary"""
        data['quota_type'] = QuotaType(data['quota_type'])
        return cls(**data)

    def is_exceeded(self) -> bool:
        """Check if quota is exceeded"""
        return self.current_usage >= self.limit

    def is_soft_limit_exceeded(self) -> bool:
        """Check if soft limit is exceeded"""
        if self.soft_limit is None:
            return False
        return self.current_usage >= self.soft_limit

    def remaining(self) -> int:
        """Get remaining quota"""
        return max(0, self.limit - self.current_usage)

    def percentage_used(self) -> float:
        """Get percentage of quota used"""
        if self.limit == 0:
            return 100.0
        return (self.current_usage / self.limit) * 100.0


class ResourceQuotaManager:
    """
    Manages resource quotas and usage tracking for tenants.

    Features:
    - Define and enforce quotas
    - Track usage in real-time
    - Automatic reset periods
    - Soft limits with warnings
    - Usage analytics
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize quota manager.

        Args:
            db_path: Path to SQLite database for quota storage
        """
        self.db_path = db_path or str(Path.home() / '.ai-shell' / 'quotas.db')
        self._init_database()
        self._usage_cache: Dict[str, Dict[str, Any]] = {}

    def _init_database(self) -> None:
        """Initialize quota database schema"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quotas (
                    tenant_id TEXT NOT NULL,
                    quota_type TEXT NOT NULL,
                    limit_value INTEGER NOT NULL,
                    current_usage INTEGER DEFAULT 0,
                    soft_limit INTEGER,
                    reset_period TEXT,
                    last_reset TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, quota_type)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    quota_type TEXT NOT NULL,
                    usage_amount INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_tenant_type
                ON usage_history(tenant_id, quota_type, timestamp)
            """)

    def set_quota(
        self,
        tenant_id: str,
        quota_type: QuotaType,
        limit: int,
        soft_limit: Optional[int] = None,
        reset_period: Optional[str] = None,
    ) -> ResourceQuota:
        """
        Set or update a resource quota.

        Args:
            tenant_id: Tenant ID
            quota_type: Type of quota
            limit: Maximum limit
            soft_limit: Warning threshold
            reset_period: Reset period ('hourly', 'daily', 'monthly')

        Returns:
            Created/updated quota
        """
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO quotas (
                    tenant_id, quota_type, limit_value, soft_limit,
                    reset_period, last_reset, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, '{}', ?, ?)
                ON CONFLICT(tenant_id, quota_type) DO UPDATE SET
                    limit_value = excluded.limit_value,
                    soft_limit = excluded.soft_limit,
                    reset_period = excluded.reset_period,
                    updated_at = excluded.updated_at
            """, (
                tenant_id,
                quota_type.value,
                limit,
                soft_limit,
                reset_period,
                now,
                now,
                now,
            ))

        return self.get_quota(tenant_id, quota_type)

    def get_quota(self, tenant_id: str, quota_type: QuotaType) -> Optional[ResourceQuota]:
        """Get quota configuration"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM quotas
                WHERE tenant_id = ? AND quota_type = ?
            """, (tenant_id, quota_type.value))

            row = cursor.fetchone()
            if not row:
                return None

            quota = ResourceQuota(
                tenant_id=row['tenant_id'],
                quota_type=QuotaType(row['quota_type']),
                limit=row['limit_value'],
                current_usage=row['current_usage'],
                soft_limit=row['soft_limit'],
                reset_period=row['reset_period'],
                last_reset=row['last_reset'],
                metadata={},
            )
            return quota

    def check_quota(
        self,
        tenant_id: str,
        quota_type: QuotaType,
        amount: int = 1,
    ) -> Dict[str, Any]:
        """
        Check if quota allows the operation.

        Args:
            tenant_id: Tenant ID
            quota_type: Type of quota to check
            amount: Amount of resource to consume

        Returns:
            Dict with allowed status and quota info
        """
        quota = self.get_quota(tenant_id, quota_type)

        if not quota:
            # No quota defined = unlimited
            return {
                'allowed': True,
                'unlimited': True,
            }

        # Check if reset is needed
        self._check_and_reset_quota(quota)

        # Re-fetch after potential reset
        quota = self.get_quota(tenant_id, quota_type)

        if not quota:
            return {
                'allowed': True,
                'unlimited': True,
            }

        would_exceed = (quota.current_usage + amount) > quota.limit
        soft_limit_exceeded = quota.is_soft_limit_exceeded()

        return {
            'allowed': not would_exceed,
            'quota_exceeded': would_exceed,
            'soft_limit_exceeded': soft_limit_exceeded,
            'current_usage': quota.current_usage,
            'limit': quota.limit,
            'remaining': quota.remaining(),
            'percentage_used': quota.percentage_used(),
        }

    def consume_quota(
        self,
        tenant_id: str,
        quota_type: QuotaType,
        amount: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Consume quota if available.

        Args:
            tenant_id: Tenant ID
            quota_type: Type of quota
            amount: Amount to consume
            metadata: Additional metadata to track

        Returns:
            True if quota was consumed, False if exceeded
        """
        check_result = self.check_quota(tenant_id, quota_type, amount)

        if not check_result['allowed']:
            return False

        # Update usage
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE quotas
                SET current_usage = current_usage + ?,
                    updated_at = ?
                WHERE tenant_id = ? AND quota_type = ?
            """, (amount, now, tenant_id, quota_type.value))

            # Record in history
            conn.execute("""
                INSERT INTO usage_history (
                    tenant_id, quota_type, usage_amount, timestamp, metadata
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                tenant_id,
                quota_type.value,
                amount,
                now,
                metadata or '{}',
            ))

        return True

    def reset_quota(self, tenant_id: str, quota_type: QuotaType):
        """Manually reset a quota"""
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE quotas
                SET current_usage = 0,
                    last_reset = ?,
                    updated_at = ?
                WHERE tenant_id = ? AND quota_type = ?
            """, (now, now, tenant_id, quota_type.value))

    def _check_and_reset_quota(self, quota: ResourceQuota):
        """Check if quota should be reset based on period"""
        if not quota.reset_period or not quota.last_reset:
            return

        last_reset = datetime.fromisoformat(quota.last_reset)
        now = datetime.now()

        should_reset = False

        if quota.reset_period == 'hourly':
            should_reset = now - last_reset > timedelta(hours=1)
        elif quota.reset_period == 'daily':
            should_reset = now - last_reset > timedelta(days=1)
        elif quota.reset_period == 'monthly':
            should_reset = now - last_reset > timedelta(days=30)

        if should_reset:
            self.reset_quota(quota.tenant_id, quota.quota_type)

    def get_all_quotas(self, tenant_id: str) -> List[ResourceQuota]:
        """Get all quotas for a tenant"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM quotas WHERE tenant_id = ?",
                (tenant_id,)
            )

            quotas = []
            for row in cursor.fetchall():
                quotas.append(ResourceQuota(
                    tenant_id=row['tenant_id'],
                    quota_type=QuotaType(row['quota_type']),
                    limit=row['limit_value'],
                    current_usage=row['current_usage'],
                    soft_limit=row['soft_limit'],
                    reset_period=row['reset_period'],
                    last_reset=row['last_reset'],
                    metadata={},
                ))

            return quotas

    def get_usage_history(
        self,
        tenant_id: str,
        quota_type: Optional[QuotaType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get usage history for analytics"""
        query = "SELECT * FROM usage_history WHERE tenant_id = ?"
        params = [tenant_id]

        if quota_type:
            query += " AND quota_type = ?"
            params.append(quota_type.value)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(str(limit))

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            return [dict(row) for row in cursor.fetchall()]

    def get_usage_analytics(
        self,
        tenant_id: str,
        quota_type: QuotaType,
        period: str = 'daily',
    ) -> Dict[str, Any]:
        """Get usage analytics and trends"""
        history = self.get_usage_history(tenant_id, quota_type, limit=1000)

        if not history:
            return {
                'total_usage': 0,
                'average_usage': 0,
                'peak_usage': 0,
                'trend': 'stable',
            }

        total_usage = sum(h['usage_amount'] for h in history)
        average_usage = total_usage / len(history)
        peak_usage = max(h['usage_amount'] for h in history)

        # Simple trend analysis
        recent_avg = sum(h['usage_amount'] for h in history[:10]) / min(10, len(history))
        older_avg = sum(h['usage_amount'] for h in history[-10:]) / min(10, len(history))

        if recent_avg > older_avg * 1.2:
            trend = 'increasing'
        elif recent_avg < older_avg * 0.8:
            trend = 'decreasing'
        else:
            trend = 'stable'

        return {
            'total_usage': total_usage,
            'average_usage': average_usage,
            'peak_usage': peak_usage,
            'trend': trend,
            'data_points': len(history),
        }
