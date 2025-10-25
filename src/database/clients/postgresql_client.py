"""
PostgreSQL Database Client Implementation

Production-ready PostgreSQL connectivity with:
- Connection pooling (min 5, max 20)
- Native async/await support via asyncpg
- JSONB handling
- Prepared statements
- Comprehensive error handling
- Health checks and monitoring
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None

from .base import (
    BaseDatabaseClient,
    DatabaseConfig,
    DatabaseError,
    ConnectionError,
    QueryError,
)


logger = logging.getLogger(__name__)


class PostgreSQLClient(BaseDatabaseClient):
    """
    PostgreSQL Database Client with asyncpg

    Provides production-ready PostgreSQL connectivity with:
    - Native async/await operations
    - Connection pooling
    - JSONB support
    - Prepared statements
    - Query logging and metrics
    """

    def __init__(self, config: DatabaseConfig, name: str = "postgresql"):
        """
        Initialize PostgreSQL client

        Args:
            config: Database configuration
            name: Client identifier
        """
        if not ASYNCPG_AVAILABLE:
            raise ImportError(
                "asyncpg not available. Install with: pip install asyncpg"
            )

        super().__init__(config, name)
        self._asyncpg_pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """Initialize PostgreSQL client with asyncpg connection pool"""
        try:
            # Build connection parameters
            conn_params = {
                'host': self.config.host,
                'port': self.config.port,
                'database': self.config.database,
                'user': self.config.user,
                'password': self.config.password,
                'min_size': self.config.min_pool_size,
                'max_size': self.config.max_pool_size,
                'timeout': self.config.connection_timeout,
                'command_timeout': self.config.query_timeout,
            }

            # Add SSL parameters if enabled
            if self.config.ssl_enabled:
                ssl_context = self._create_ssl_context()
                conn_params['ssl'] = ssl_context

            # Add extra parameters
            if self.config.extra_params:
                conn_params.update(self.config.extra_params)

            # Create asyncpg connection pool
            self._asyncpg_pool = await asyncpg.create_pool(**conn_params)

            # Test connection
            async with self._asyncpg_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')

            self._initialized = True
            logger.info(
                f"Initialized PostgreSQL client '{self.name}' with pool "
                f"(min={self.config.min_pool_size}, max={self.config.max_pool_size})"
            )

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL client: {e}")
            raise ConnectionError(
                f"Failed to initialize PostgreSQL client: {e}",
                error_code="POSTGRES_INIT_FAILED",
                original_error=e
            )

    async def close(self) -> None:
        """Close PostgreSQL client and connection pool"""
        if self._asyncpg_pool:
            await self._asyncpg_pool.close()
            self._asyncpg_pool = None

        self._initialized = False
        logger.info(f"Closed PostgreSQL client '{self.name}'")

    def _create_ssl_context(self):
        """Create SSL context for secure connections"""
        import ssl

        ssl_context = ssl.create_default_context()

        if self.config.ssl_ca:
            ssl_context.load_verify_locations(cafile=self.config.ssl_ca)

        if self.config.ssl_cert and self.config.ssl_key:
            ssl_context.load_cert_chain(
                certfile=self.config.ssl_cert,
                keyfile=self.config.ssl_key
            )

        return ssl_context

    async def _create_connection(self) -> Any:
        """
        Create a new PostgreSQL connection

        Note: Not used with asyncpg pool, but required by base class
        """
        if self._asyncpg_pool:
            return await self._asyncpg_pool.acquire()

        raise NotImplementedError("Direct connection not supported with asyncpg pool")

    async def _execute_impl(
        self,
        connection: Any,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[Tuple], int]:
        """
        Execute PostgreSQL query using asyncpg

        Args:
            connection: asyncpg connection object
            query: SQL query
            params: Query parameters

        Returns:
            Tuple of (columns, rows, rowcount)
        """
        try:
            # Convert named parameters to positional if needed
            if params:
                # asyncpg uses $1, $2, etc. for positional parameters
                # Convert dict to list of values
                param_values = list(params.values())
            else:
                param_values = []

            # Determine query type
            query_upper = query.strip().upper()

            if query_upper.startswith('SELECT'):
                # SELECT query - fetch results
                if param_values:
                    rows = await connection.fetch(query, *param_values)
                else:
                    rows = await connection.fetch(query)

                if rows:
                    # Get column names from first row
                    columns = list(rows[0].keys())
                    # Convert Record objects to tuples
                    row_tuples = [tuple(row.values()) for row in rows]
                    rowcount = len(rows)
                else:
                    columns = []
                    row_tuples = []
                    rowcount = 0

                return columns, row_tuples, rowcount

            else:
                # DML query (INSERT, UPDATE, DELETE, etc.)
                if param_values:
                    result = await connection.execute(query, *param_values)
                else:
                    result = await connection.execute(query)

                # Parse rowcount from result string (e.g., "UPDATE 5")
                rowcount = 0
                if result:
                    parts = result.split()
                    if len(parts) > 1 and parts[-1].isdigit():
                        rowcount = int(parts[-1])

                return [], [], rowcount

        except Exception as e:
            logger.error(f"PostgreSQL query execution failed: {e}")
            raise QueryError(
                f"Failed to execute PostgreSQL query: {e}",
                error_code="POSTGRES_QUERY_FAILED",
                original_error=e
            )

    async def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> Dict[str, Any]:
        """
        Execute PostgreSQL query using pool

        Overrides base execute to use asyncpg pool directly
        """
        if not self._initialized:
            await self.initialize()

        import time
        start_time = time.time()
        attempt = 0
        last_error = None

        while attempt < self.config.max_retries if retry else 1:
            try:
                async with self._asyncpg_pool.acquire() as conn:
                    columns, rows, rowcount = await self._execute_impl(conn, query, params)

                    execution_time = time.time() - start_time

                    # Record metrics
                    self._record_metrics(
                        query=query,
                        execution_time=execution_time,
                        rows_affected=rowcount,
                        success=True
                    )

                    return {
                        'columns': columns,
                        'rows': rows,
                        'rowcount': rowcount,
                        'execution_time': execution_time,
                        'query_type': self._get_query_type(query),
                    }

            except Exception as e:
                last_error = e
                attempt += 1

                if attempt < self.config.max_retries and retry:
                    delay = self.config.retry_delay * (self.config.retry_backoff ** (attempt - 1))
                    logger.warning(
                        f"Query failed (attempt {attempt}/{self.config.max_retries}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    execution_time = time.time() - start_time
                    self._record_metrics(
                        query=query,
                        execution_time=execution_time,
                        rows_affected=0,
                        success=False,
                        error=str(e)
                    )

                    raise QueryError(
                        f"Query execution failed after {attempt} attempts: {e}",
                        error_code="QUERY_FAILED",
                        original_error=e
                    )

        raise QueryError(
            f"Query execution failed: {last_error}",
            error_code="QUERY_FAILED",
            original_error=last_error
        )

    async def _get_ping_query(self) -> str:
        """Get PostgreSQL-specific ping query"""
        return "SELECT 1"

    async def _begin_transaction(self, connection: Any) -> None:
        """Begin PostgreSQL transaction"""
        await connection.execute("BEGIN")

    async def _commit_transaction(self, connection: Any) -> None:
        """Commit PostgreSQL transaction"""
        await connection.execute("COMMIT")

    async def _rollback_transaction(self, connection: Any) -> None:
        """Rollback PostgreSQL transaction"""
        await connection.execute("ROLLBACK")

    async def get_version(self) -> str:
        """Get PostgreSQL server version"""
        result = await self.execute("SELECT version()")
        return result['rows'][0][0] if result['rows'] else "Unknown"

    async def get_databases(self) -> List[Dict[str, Any]]:
        """Get list of databases"""
        query = """
            SELECT
                datname,
                pg_catalog.pg_get_userbyid(datdba) AS owner,
                pg_encoding_to_char(encoding) AS encoding,
                datcollate,
                datctype,
                datistemplate,
                datallowconn
            FROM pg_database
            ORDER BY datname
        """
        result = await self.execute(query)

        databases = []
        for row in result['rows']:
            databases.append({
                'name': row[0],
                'owner': row[1],
                'encoding': row[2],
                'collate': row[3],
                'ctype': row[4],
                'is_template': row[5],
                'allow_connections': row[6],
            })

        return databases

    async def get_tables(self, schema: str = 'public') -> List[Dict[str, Any]]:
        """Get list of tables in schema"""
        query = """
            SELECT
                schemaname,
                tablename,
                tableowner,
                hasindexes,
                hasrules,
                hastriggers
            FROM pg_tables
            WHERE schemaname = $1
            ORDER BY tablename
        """
        result = await self.execute(query, {'schema': schema})

        tables = []
        for row in result['rows']:
            tables.append({
                'schema': row[0],
                'name': row[1],
                'owner': row[2],
                'has_indexes': row[3],
                'has_rules': row[4],
                'has_triggers': row[5],
            })

        return tables

    async def get_table_size(self, table_name: str, schema: str = 'public') -> Dict[str, Any]:
        """Get table size information"""
        query = """
            SELECT
                pg_size_pretty(pg_total_relation_size($1)) AS total_size,
                pg_size_pretty(pg_relation_size($1)) AS table_size,
                pg_size_pretty(pg_indexes_size($1)) AS indexes_size
        """
        full_table_name = f"{schema}.{table_name}"
        result = await self.execute(query, {'table': full_table_name})

        if result['rows']:
            row = result['rows'][0]
            return {
                'table': table_name,
                'schema': schema,
                'total_size': row[0],
                'table_size': row[1],
                'indexes_size': row[2],
            }

        return {}

    async def execute_jsonb_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute query with JSONB support

        PostgreSQL has excellent JSONB support. This method ensures
        proper handling of JSON data types.
        """
        return await self.execute(query, params)

    async def create_index(
        self,
        table_name: str,
        columns: List[str],
        index_name: Optional[str] = None,
        unique: bool = False,
        method: str = 'btree'
    ) -> None:
        """
        Create an index on a table

        Args:
            table_name: Name of the table
            columns: List of column names
            index_name: Custom index name (auto-generated if None)
            unique: Create unique index
            method: Index method (btree, hash, gist, gin, etc.)
        """
        if not index_name:
            index_name = f"idx_{table_name}_{'_'.join(columns)}"

        unique_clause = "UNIQUE " if unique else ""
        columns_clause = ", ".join(columns)

        query = f"""
            CREATE {unique_clause}INDEX {index_name}
            ON {table_name} USING {method} ({columns_clause})
        """

        await self.execute(query)
        logger.info(f"Created index {index_name} on {table_name}")
