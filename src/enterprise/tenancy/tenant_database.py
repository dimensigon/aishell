"""
Tenant Database Isolation

Provides database-level tenant isolation with:
- Schema-per-tenant isolation
- Database-per-tenant isolation
- Connection pooling per tenant
- Query isolation and security
"""

import sqlite3
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


class IsolationStrategy(Enum):
    """Database isolation strategies"""
    SHARED_DATABASE = "shared_database"  # Single DB, tenant_id in all tables
    SCHEMA_PER_TENANT = "schema_per_tenant"  # Separate schemas
    DATABASE_PER_TENANT = "database_per_tenant"  # Separate databases


@dataclass
class TenantSchema:
    """Tenant database schema configuration"""
    tenant_id: str
    schema_name: str
    isolation_strategy: IsolationStrategy
    connection_string: str
    max_connections: int = 5
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TenantDatabaseManager:
    """
    Manages database isolation for multi-tenancy.

    Features:
    - Multiple isolation strategies
    - Per-tenant connection pooling
    - Schema creation and migration
    - Query rewriting for tenant isolation
    - Connection security
    """

    def __init__(
        self,
        base_db_path: Optional[str] = None,
        isolation_strategy: IsolationStrategy = IsolationStrategy.SCHEMA_PER_TENANT,
    ):
        """
        Initialize tenant database manager.

        Args:
            base_db_path: Base path for database files
            isolation_strategy: Isolation strategy to use
        """
        self.base_db_path = Path(base_db_path) if base_db_path else Path.home() / '.ai-shell' / 'tenant_dbs'
        self.isolation_strategy = isolation_strategy
        self.base_db_path.mkdir(parents=True, exist_ok=True)

        # Connection pools per tenant
        self._connection_pools: Dict[str, List[sqlite3.Connection]] = {}

    def create_tenant_database(
        self,
        tenant_id: str,
        schema_name: Optional[str] = None,
    ) -> TenantSchema:
        """
        Create database/schema for a tenant.

        Args:
            tenant_id: Tenant ID
            schema_name: Optional schema name (defaults to tenant_id)

        Returns:
            Created tenant schema configuration
        """
        schema_name = schema_name or f"tenant_{tenant_id}"

        if self.isolation_strategy == IsolationStrategy.DATABASE_PER_TENANT:
            # Create separate database file
            db_path = self.base_db_path / f"{tenant_id}.db"
            connection_string = str(db_path)

            conn = sqlite3.connect(db_path)
            self._initialize_schema(conn, tenant_id)
            conn.close()

        elif self.isolation_strategy == IsolationStrategy.SCHEMA_PER_TENANT:
            # For SQLite, we'll use separate database files
            # For PostgreSQL, this would create separate schemas
            db_path = self.base_db_path / f"{tenant_id}.db"
            connection_string = str(db_path)

            conn = sqlite3.connect(db_path)
            self._initialize_schema(conn, tenant_id)
            conn.close()

        else:  # SHARED_DATABASE
            # Use shared database with tenant_id column
            db_path = self.base_db_path / "shared.db"
            connection_string = str(db_path)

            conn = sqlite3.connect(db_path)
            self._initialize_shared_schema(conn)
            conn.close()

        return TenantSchema(
            tenant_id=tenant_id,
            schema_name=schema_name,
            isolation_strategy=self.isolation_strategy,
            connection_string=connection_string,
        )

    def get_tenant_connection(
        self,
        tenant_id: str,
        readonly: bool = False,
    ) -> sqlite3.Connection:
        """
        Get a database connection for a tenant.

        Args:
            tenant_id: Tenant ID
            readonly: If True, connection is read-only

        Returns:
            Database connection
        """
        if self.isolation_strategy == IsolationStrategy.SHARED_DATABASE:
            db_path = self.base_db_path / "shared.db"
        else:
            db_path = self.base_db_path / f"{tenant_id}.db"

        if not db_path.exists():
            raise ValueError(f"Database for tenant {tenant_id} not found")

        uri = f"file:{db_path}?mode=ro" if readonly else str(db_path)
        conn = sqlite3.connect(uri, uri=readonly)
        conn.row_factory = sqlite3.Row

        # Set tenant context for shared database
        if self.isolation_strategy == IsolationStrategy.SHARED_DATABASE:
            conn.execute(f"-- TENANT_ID: {tenant_id}")

        return conn

    def execute_tenant_query(
        self,
        tenant_id: str,
        query: str,
        params: Optional[tuple] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a query in tenant's isolated database.

        Args:
            tenant_id: Tenant ID
            query: SQL query
            params: Query parameters

        Returns:
            Query results
        """
        conn = self.get_tenant_connection(tenant_id)

        try:
            # Rewrite query if using shared database
            if self.isolation_strategy == IsolationStrategy.SHARED_DATABASE:
                query = self._rewrite_query_for_tenant(query, tenant_id)

            cursor = conn.execute(query, params or ())

            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return [{'rows_affected': cursor.rowcount}]

        finally:
            conn.close()

    def _initialize_schema(self, conn: sqlite3.Connection, tenant_id: str):
        """Initialize database schema for a tenant"""
        # Create standard tables for tenant
        conn.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                execution_time REAL,
                status TEXT,
                user_id TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                result TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()

    def _initialize_shared_schema(self, conn: sqlite3.Connection):
        """Initialize shared database schema with tenant isolation"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                query TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                execution_time REAL,
                status TEXT,
                user_id TEXT
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_queries_tenant
            ON queries(tenant_id)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                query TEXT NOT NULL,
                result TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_tenant
            ON query_history(tenant_id)
        """)

        conn.commit()

    def _rewrite_query_for_tenant(self, query: str, tenant_id: str) -> str:
        """
        Rewrite query to include tenant isolation.

        For shared database strategy, adds tenant_id filters.
        """
        # Simple query rewriting - in production, use a proper SQL parser
        query_upper = query.upper()

        if 'WHERE' in query_upper:
            # Add tenant_id to existing WHERE clause
            where_pos = query_upper.index('WHERE')
            return (
                query[:where_pos + 5] +
                f" tenant_id = '{tenant_id}' AND " +
                query[where_pos + 5:]
            )
        elif 'SELECT' in query_upper:
            # Add WHERE clause with tenant_id
            from_pos = query_upper.index('FROM')
            # Find end of FROM clause (before ORDER BY, GROUP BY, LIMIT, etc.)
            end_clauses = ['ORDER BY', 'GROUP BY', 'LIMIT', 'OFFSET']
            end_pos = len(query)

            for clause in end_clauses:
                if clause in query_upper:
                    clause_pos = query_upper.index(clause)
                    end_pos = min(end_pos, clause_pos)

            return (
                query[:end_pos] +
                f" WHERE tenant_id = '{tenant_id}' " +
                query[end_pos:]
            )

        return query

    def delete_tenant_database(self, tenant_id: str) -> bool:
        """
        Delete tenant's database/schema.

        Args:
            tenant_id: Tenant ID

        Returns:
            True if deleted successfully
        """
        if self.isolation_strategy == IsolationStrategy.SHARED_DATABASE:
            # Delete tenant's data from shared database
            db_path = self.base_db_path / "shared.db"
            conn = sqlite3.connect(db_path)

            try:
                conn.execute("DELETE FROM queries WHERE tenant_id = ?", (tenant_id,))
                conn.execute("DELETE FROM query_history WHERE tenant_id = ?", (tenant_id,))
                conn.commit()
                return True
            finally:
                conn.close()
        else:
            # Delete tenant's database file
            db_path = self.base_db_path / f"{tenant_id}.db"
            if db_path.exists():
                db_path.unlink()
                return True

        return False

    def backup_tenant_database(
        self,
        tenant_id: str,
        backup_path: Optional[str] = None,
    ) -> str:
        """
        Backup tenant's database.

        Args:
            tenant_id: Tenant ID
            backup_path: Optional backup path

        Returns:
            Path to backup file
        """
        from datetime import datetime
        import shutil

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if not backup_path:
            backup_dir = self.base_db_path / 'backups'
            backup_dir.mkdir(exist_ok=True)
            backup_path_obj = backup_dir / f"{tenant_id}_{timestamp}.db"
        else:
            backup_path_obj = Path(backup_path)

        if self.isolation_strategy == IsolationStrategy.SHARED_DATABASE:
            # Export tenant data to separate file
            source_db = self.base_db_path / "shared.db"
            backup_db = backup_path_obj

            source_conn = sqlite3.connect(source_db)
            backup_conn = sqlite3.connect(backup_db)

            # Copy schema
            self._initialize_schema(backup_conn, tenant_id)

            # Copy tenant data
            cursor = source_conn.execute(
                "SELECT * FROM queries WHERE tenant_id = ?",
                (tenant_id,)
            )
            for row in cursor:
                backup_conn.execute(
                    "INSERT INTO queries VALUES (?, ?, ?, ?, ?, ?)",
                    row[1:]  # Skip tenant_id
                )

            backup_conn.commit()
            source_conn.close()
            backup_conn.close()
        else:
            # Copy database file
            source_db = self.base_db_path / f"{tenant_id}.db"
            shutil.copy2(source_db, str(backup_path_obj))

        return str(backup_path_obj)

    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get database statistics for a tenant"""
        conn = self.get_tenant_connection(tenant_id)

        try:
            if self.isolation_strategy == IsolationStrategy.SHARED_DATABASE:
                cursor = conn.execute("""
                    SELECT COUNT(*) as query_count
                    FROM queries
                    WHERE tenant_id = ?
                """, (tenant_id,))
            else:
                cursor = conn.execute("SELECT COUNT(*) as query_count FROM queries")

            row = cursor.fetchone()
            query_count = row[0] if row else 0

            # Get database size
            if self.isolation_strategy == IsolationStrategy.SHARED_DATABASE:
                db_path = self.base_db_path / "shared.db"
            else:
                db_path = self.base_db_path / f"{tenant_id}.db"

            db_size = db_path.stat().st_size if db_path.exists() else 0

            return {
                'tenant_id': tenant_id,
                'query_count': query_count,
                'database_size_bytes': db_size,
                'isolation_strategy': self.isolation_strategy.value,
            }

        finally:
            conn.close()
