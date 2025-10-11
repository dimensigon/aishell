"""
MySQL MCP Client Implementation

Implements MySQL database connectivity using aiomysql for async operations.
"""

import asyncio
from typing import Any, Dict, Optional, List
import aiomysql
from .base import BaseMCPClient, ConnectionConfig, MCPClientError


class MySQLClient(BaseMCPClient):
    """
    MySQL database client using aiomysql

    Provides async interface to MySQL database operations with connection pooling.
    """

    def __init__(self) -> None:
        super().__init__()
        self._cursor = None
        self._pool = None

    async def _connect_impl(self, config: ConnectionConfig) -> Any:
        """
        Connect to MySQL database

        Args:
            config: Connection configuration

        Returns:
            Connection object
        """
        # Build connection parameters
        conn_params = {
            'host': config.host,
            'port': config.port,
            'db': config.database,
            'user': config.username,
            'password': config.password,
            'autocommit': False,
        }

        # Add extra parameters
        if config.extra_params:
            conn_params.update(config.extra_params)

        # Create connection with aiomysql (native async)
        connection = await aiomysql.connect(**conn_params)

        return connection

    async def create_pool(self, config: ConnectionConfig, pool_size: int = 10) -> None:
        """
        Create connection pool for efficient connection management

        Args:
            config: Connection configuration
            pool_size: Maximum pool size
        """
        pool_params = {
            'host': config.host,
            'port': config.port,
            'db': config.database,
            'user': config.username,
            'password': config.password,
            'minsize': 1,
            'maxsize': pool_size,
            'autocommit': False,
        }

        if config.extra_params:
            pool_params.update(config.extra_params)

        self._pool = await aiomysql.create_pool(**pool_params)

    async def _disconnect_impl(self) -> None:
        """Disconnect from MySQL"""
        if self._cursor:
            await self._cursor.close()
            self._cursor = None

        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

        if self._connection:
            self._connection.close()

    async def _execute_query_impl(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute MySQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Dictionary with columns, rows, rowcount, and metadata
        """
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        # Create cursor with dictionary support
        if not self._cursor:
            self._cursor = await self._connection.cursor(aiomysql.DictCursor)

        # Execute query
        if params:
            await self._cursor.execute(query, params)
        else:
            await self._cursor.execute(query)

        # Fetch results
        if self._cursor.description:
            columns = [desc[0] for desc in self._cursor.description]
            rows_dict = await self._cursor.fetchall()

            # Convert DictRow to tuples
            if rows_dict and columns:
                rows = [tuple(row[col] for col in columns) for row in rows_dict]
            else:
                rows = []
        else:
            columns = []
            rows = []

        rowcount = self._cursor.rowcount

        # Get metadata
        if self._config is None:
            raise MCPClientError("No active configuration", "NOT_CONFIGURED")

        metadata = {
            'database': self._config.database,
            'query_type': self._get_query_type(query)
        }

        if self._cursor.description:
            metadata['column_types'] = [desc[1] for desc in self._cursor.description]

        return {
            'columns': columns,
            'rows': rows,
            'rowcount': rowcount,
            'metadata': metadata
        }

    async def _execute_ddl_impl(self, ddl: str) -> None:
        """Execute DDL statement"""
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        if not self._cursor:
            self._cursor = await self._connection.cursor()

        await self._cursor.execute(ddl)
        await self._connection.commit()

    def _get_ping_query(self) -> str:
        """Get MySQL-specific ping query"""
        return "SELECT 1"

    def _get_query_type(self, query: str) -> str:
        """Determine query type from SQL"""
        query_upper = query.strip().upper()

        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith(('CREATE', 'ALTER', 'DROP')):
            return 'DDL'
        else:
            return 'OTHER'

    async def get_table_info(self, table_name: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Get MySQL table information

        Args:
            table_name: Name of the table
            schema: Schema name (optional, defaults to current database)

        Returns:
            Dictionary with table metadata
        """
        if schema is None:
            schema = self._config.database if self._config else 'mysql'

        query = """
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_KEY
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """

        result = await self.execute_query(query, (schema, table_name))

        return {
            'table_name': table_name,
            'schema': schema,
            'columns': [
                {
                    'name': row[0],
                    'type': row[1],
                    'length': row[2],
                    'nullable': row[3] == 'YES',
                    'default': row[4],
                    'key': row[5]
                }
                for row in result.rows
            ]
        }

    async def get_table_list(self, schema: Optional[str] = None) -> List[str]:
        """
        Get list of tables in schema

        Args:
            schema: Schema name (optional, defaults to current database)

        Returns:
            List of table names
        """
        if schema is None:
            schema = self._config.database if self._config else 'mysql'

        query = """
            SELECT TABLE_NAME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s
            AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """

        result = await self.execute_query(query, (schema,))
        return [row[0] for row in result.rows]

    async def get_schemas(self) -> List[str]:
        """
        Get list of schemas (databases)

        Returns:
            List of schema names
        """
        query = """
            SELECT SCHEMA_NAME
            FROM information_schema.SCHEMATA
            WHERE SCHEMA_NAME NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
            ORDER BY SCHEMA_NAME
        """

        result = await self.execute_query(query)
        return [row[0] for row in result.rows]

    async def execute_with_pool(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute query using connection pool

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Dictionary with columns, rows, rowcount, and metadata
        """
        if not self._pool:
            raise MCPClientError("Connection pool not initialized", "NO_POOL")

        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)

                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows_dict = await cursor.fetchall()
                    rows = [tuple(row[col] for col in columns) for row in rows_dict]
                else:
                    columns = []
                    rows = []

                return {
                    'columns': columns,
                    'rows': rows,
                    'rowcount': cursor.rowcount,
                    'metadata': {
                        'database': self._config.database if self._config else 'unknown',
                        'query_type': self._get_query_type(query)
                    }
                }
