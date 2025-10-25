"""
MySQL Database Client Implementation

Production-ready MySQL connectivity with:
- Connection pooling (min 5, max 20)
- Native async/await support via aiomysql
- Prepared statements
- Comprehensive error handling
- Health checks and monitoring
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

try:
    import aiomysql
    AIOMYSQL_AVAILABLE = True
except ImportError:
    AIOMYSQL_AVAILABLE = False
    aiomysql = None

from .base import (
    BaseDatabaseClient,
    DatabaseConfig,
    DatabaseError,
    ConnectionError,
    QueryError,
)


logger = logging.getLogger(__name__)


class MySQLClient(BaseDatabaseClient):
    """
    MySQL Database Client with aiomysql

    Provides production-ready MySQL connectivity with:
    - Native async/await operations
    - Connection pooling
    - Prepared statements
    - Query logging and metrics
    """

    def __init__(self, config: DatabaseConfig, name: str = "mysql"):
        """
        Initialize MySQL client

        Args:
            config: Database configuration
            name: Client identifier
        """
        if not AIOMYSQL_AVAILABLE:
            raise ImportError(
                "aiomysql not available. Install with: pip install aiomysql"
            )

        super().__init__(config, name)
        self._aiomysql_pool: Optional[aiomysql.Pool] = None

    async def initialize(self) -> None:
        """Initialize MySQL client with aiomysql connection pool"""
        try:
            # Build connection parameters
            conn_params = {
                'host': self.config.host,
                'port': self.config.port,
                'db': self.config.database,
                'user': self.config.user,
                'password': self.config.password,
                'minsize': self.config.min_pool_size,
                'maxsize': self.config.max_pool_size,
                'pool_recycle': 3600,  # Recycle connections every hour
                'autocommit': False,
                'charset': 'utf8mb4',
                'use_unicode': True,
            }

            # Add SSL parameters if enabled
            if self.config.ssl_enabled:
                ssl_config = {}
                if self.config.ssl_ca:
                    ssl_config['ca'] = self.config.ssl_ca
                if self.config.ssl_cert:
                    ssl_config['cert'] = self.config.ssl_cert
                if self.config.ssl_key:
                    ssl_config['key'] = self.config.ssl_key

                if ssl_config:
                    conn_params['ssl'] = ssl_config

            # Add extra parameters
            if self.config.extra_params:
                conn_params.update(self.config.extra_params)

            # Create aiomysql connection pool
            self._aiomysql_pool = await aiomysql.create_pool(**conn_params)

            # Test connection
            async with self._aiomysql_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute('SELECT 1')

            self._initialized = True
            logger.info(
                f"Initialized MySQL client '{self.name}' with pool "
                f"(min={self.config.min_pool_size}, max={self.config.max_pool_size})"
            )

        except Exception as e:
            logger.error(f"Failed to initialize MySQL client: {e}")
            raise ConnectionError(
                f"Failed to initialize MySQL client: {e}",
                error_code="MYSQL_INIT_FAILED",
                original_error=e
            )

    async def close(self) -> None:
        """Close MySQL client and connection pool"""
        if self._aiomysql_pool:
            self._aiomysql_pool.close()
            await self._aiomysql_pool.wait_closed()
            self._aiomysql_pool = None

        self._initialized = False
        logger.info(f"Closed MySQL client '{self.name}'")

    async def _create_connection(self) -> Any:
        """
        Create a new MySQL connection

        Note: Not used with aiomysql pool, but required by base class
        """
        if self._aiomysql_pool:
            return await self._aiomysql_pool.acquire()

        raise NotImplementedError("Direct connection not supported with aiomysql pool")

    async def _execute_impl(
        self,
        connection: Any,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[Tuple], int]:
        """
        Execute MySQL query using aiomysql

        Args:
            connection: aiomysql connection object
            query: SQL query
            params: Query parameters

        Returns:
            Tuple of (columns, rows, rowcount)
        """
        cursor = None
        try:
            # Create cursor with dictionary support
            cursor = await connection.cursor(aiomysql.DictCursor)

            # Execute query
            if params:
                # Convert dict params to tuple for MySQL
                param_values = tuple(params.values())
                await cursor.execute(query, param_values)
            else:
                await cursor.execute(query)

            # Determine query type
            query_upper = query.strip().upper()

            if query_upper.startswith('SELECT') or cursor.description:
                # SELECT query - fetch results
                rows_dict = await cursor.fetchall()

                if rows_dict:
                    # Get column names
                    columns = list(rows_dict[0].keys())
                    # Convert dict rows to tuples
                    row_tuples = [tuple(row[col] for col in columns) for row in rows_dict]
                    rowcount = len(rows_dict)
                else:
                    columns = []
                    row_tuples = []
                    rowcount = 0

            else:
                # DML query (INSERT, UPDATE, DELETE, etc.)
                columns = []
                row_tuples = []
                rowcount = cursor.rowcount

                # Commit for DML operations
                await connection.commit()

            return columns, row_tuples, rowcount

        except Exception as e:
            # Rollback on error
            try:
                await connection.rollback()
            except Exception:
                pass

            logger.error(f"MySQL query execution failed: {e}")
            raise QueryError(
                f"Failed to execute MySQL query: {e}",
                error_code="MYSQL_QUERY_FAILED",
                original_error=e
            )

        finally:
            if cursor:
                await cursor.close()

    async def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> Dict[str, Any]:
        """
        Execute MySQL query using pool

        Overrides base execute to use aiomysql pool directly
        """
        if not self._initialized:
            await self.initialize()

        import time
        start_time = time.time()
        attempt = 0
        last_error = None

        while attempt < self.config.max_retries if retry else 1:
            try:
                async with self._aiomysql_pool.acquire() as conn:
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
        """Get MySQL-specific ping query"""
        return "SELECT 1"

    async def _begin_transaction(self, connection: Any) -> None:
        """Begin MySQL transaction"""
        async with connection.cursor() as cursor:
            await cursor.execute("START TRANSACTION")

    async def _commit_transaction(self, connection: Any) -> None:
        """Commit MySQL transaction"""
        await connection.commit()

    async def _rollback_transaction(self, connection: Any) -> None:
        """Rollback MySQL transaction"""
        await connection.rollback()

    async def get_version(self) -> str:
        """Get MySQL server version"""
        result = await self.execute("SELECT VERSION()")
        return result['rows'][0][0] if result['rows'] else "Unknown"

    async def get_databases(self) -> List[Dict[str, Any]]:
        """Get list of databases"""
        result = await self.execute("SHOW DATABASES")

        databases = []
        for row in result['rows']:
            databases.append({
                'name': row[0],
            })

        return databases

    async def get_tables(self, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of tables in database"""
        if database:
            await self.execute(f"USE {database}")

        result = await self.execute("SHOW TABLES")

        tables = []
        for row in result['rows']:
            tables.append({
                'name': row[0],
            })

        return tables

    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed table information"""
        # Get table status
        result = await self.execute(f"SHOW TABLE STATUS LIKE '{table_name}'")

        if not result['rows']:
            return {}

        row = result['rows'][0]
        columns = result['columns']

        # Create info dictionary from columns and row
        info = {}
        for i, col in enumerate(columns):
            info[col.lower()] = row[i]

        # Get column information
        columns_result = await self.execute(f"SHOW COLUMNS FROM {table_name}")

        info['columns'] = []
        for col_row in columns_result['rows']:
            info['columns'].append({
                'field': col_row[0],
                'type': col_row[1],
                'null': col_row[2],
                'key': col_row[3],
                'default': col_row[4],
                'extra': col_row[5],
            })

        return info

    async def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table indexes"""
        result = await self.execute(f"SHOW INDEX FROM {table_name}")

        indexes = []
        for row in result['rows']:
            indexes.append({
                'table': row[0],
                'non_unique': row[1],
                'key_name': row[2],
                'seq_in_index': row[3],
                'column_name': row[4],
                'collation': row[5],
                'cardinality': row[6],
                'sub_part': row[7],
                'packed': row[8],
                'null': row[9],
                'index_type': row[10],
                'comment': row[11],
            })

        return indexes

    async def optimize_table(self, table_name: str) -> Dict[str, Any]:
        """Optimize a table"""
        result = await self.execute(f"OPTIMIZE TABLE {table_name}")

        if result['rows']:
            return {
                'table': result['rows'][0][0],
                'op': result['rows'][0][1],
                'msg_type': result['rows'][0][2],
                'msg_text': result['rows'][0][3],
            }

        return {}

    async def analyze_table(self, table_name: str) -> Dict[str, Any]:
        """Analyze a table"""
        result = await self.execute(f"ANALYZE TABLE {table_name}")

        if result['rows']:
            return {
                'table': result['rows'][0][0],
                'op': result['rows'][0][1],
                'msg_type': result['rows'][0][2],
                'msg_text': result['rows'][0][3],
            }

        return {}

    async def create_index(
        self,
        table_name: str,
        columns: List[str],
        index_name: Optional[str] = None,
        unique: bool = False,
        index_type: str = 'BTREE'
    ) -> None:
        """
        Create an index on a table

        Args:
            table_name: Name of the table
            columns: List of column names
            index_name: Custom index name (auto-generated if None)
            unique: Create unique index
            index_type: Index type (BTREE, HASH, etc.)
        """
        if not index_name:
            index_name = f"idx_{'_'.join(columns)}"

        unique_clause = "UNIQUE " if unique else ""
        columns_clause = ", ".join(columns)

        query = f"""
            CREATE {unique_clause}INDEX {index_name}
            ON {table_name} ({columns_clause})
            USING {index_type}
        """

        await self.execute(query)
        logger.info(f"Created index {index_name} on {table_name}")
