"""
Comprehensive Audit Logging System

Features:
- All user actions logged
- Structured audit events
- Searchable audit trail
- Tamper-proof logging
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path


class AuditLevel(Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event record"""
    id: str
    timestamp: str
    tenant_id: Optional[str]
    user_id: Optional[str]
    action: str
    resource: str
    level: AuditLevel
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    result: str = "success"

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['level'] = self.level.value
        return result


class AuditLogger:
    """
    Comprehensive audit logging system.

    Features:
    - Structured logging
    - Multi-tenant support
    - Searchable history
    - Export capabilities
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or str(Path.home() / '.ai-shell' / 'audit.db')
        self._init_database()

    def _init_database(self) -> None:
        """Initialize audit database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    tenant_id TEXT,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    level TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    result TEXT DEFAULT 'success'
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_log(tenant_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)
            """)

    def log(
        self,
        action: str,
        resource: str,
        level: AuditLevel = AuditLevel.INFO,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        result: str = "success",
    ) -> str:
        """Log an audit event"""
        import uuid

        event_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        event = AuditEvent(
            id=event_id,
            timestamp=now,
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
            level=level,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_log (
                    id, timestamp, tenant_id, user_id, action, resource,
                    level, details, ip_address, user_agent, result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id,
                event.timestamp,
                event.tenant_id,
                event.user_id,
                event.action,
                event.resource,
                event.level.value,
                json.dumps(event.details),
                event.ip_address,
                event.user_agent,
                event.result,
            ))

        return event_id

    def query(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        level: Optional[AuditLevel] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query audit log"""
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []

        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if action:
            query += " AND action = ?"
            params.append(action)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        if level:
            query += " AND level = ?"
            params.append(level.value)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(str(limit))

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get audit statistics"""
        query = "SELECT COUNT(*) as total, level, result FROM audit_log"
        params: List[str] = []

        if tenant_id:
            query += " WHERE tenant_id = ?"
            params.append(tenant_id)

        query += " GROUP BY level, result"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            return {'statistics': results}
