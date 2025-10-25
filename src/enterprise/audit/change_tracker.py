"""
Database Change Tracking

Tracks all database changes for audit trail:
- Schema changes
- Data modifications
- Configuration changes
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import sqlite3
from pathlib import Path


@dataclass
class ChangeEvent:
    """Database change event"""
    id: str
    timestamp: str
    tenant_id: Optional[str]
    user_id: Optional[str]
    change_type: str  # 'schema', 'data', 'config'
    table_name: Optional[str]
    operation: str  # 'INSERT', 'UPDATE', 'DELETE', 'ALTER'
    before_value: Optional[Dict[str, Any]]
    after_value: Optional[Dict[str, Any]]
    sql_statement: Optional[str]


class ChangeTracker:
    """Tracks database changes for compliance"""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or str(Path.home() / '.ai-shell' / 'changes.db')
        self._init_database()

    def _init_database(self) -> None:
        """Initialize change tracking database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS change_log (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    tenant_id TEXT,
                    user_id TEXT,
                    change_type TEXT NOT NULL,
                    table_name TEXT,
                    operation TEXT NOT NULL,
                    before_value TEXT,
                    after_value TEXT,
                    sql_statement TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_change_timestamp ON change_log(timestamp)
            """)

    def track_change(
        self,
        change_type: str,
        operation: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        table_name: Optional[str] = None,
        before_value: Optional[Dict[str, Any]] = None,
        after_value: Optional[Dict[str, Any]] = None,
        sql_statement: Optional[str] = None,
    ) -> str:
        """Track a database change"""
        import uuid
        import json

        change_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO change_log (
                    id, timestamp, tenant_id, user_id, change_type,
                    table_name, operation, before_value, after_value, sql_statement
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                change_id,
                now,
                tenant_id,
                user_id,
                change_type,
                table_name,
                operation,
                json.dumps(before_value) if before_value else None,
                json.dumps(after_value) if after_value else None,
                sql_statement,
            ))

        return change_id

    def get_changes(
        self,
        tenant_id: Optional[str] = None,
        table_name: Optional[str] = None,
        start_time: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query change log"""
        query = "SELECT * FROM change_log WHERE 1=1"
        params = []

        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)

        if table_name:
            query += " AND table_name = ?"
            params.append(table_name)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(str(limit))

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
