"""
PostgreSQL MCP Client Implementation

Implements PostgreSQL database connectivity using psycopg2.
"""

import asyncio
from typing import Any, Dict, Optional, List
import psycopg2
import psycopg2.extras
from .base import BaseMCPClient, ConnectionConfig, MCPClientError


class PostgreSQLClient(BaseMCPClient):
    """
    PostgreSQL database client using psycopg2

    Provides async interface to PostgreSQL database operations.
    """

    def __init__(self) -> None:
        super().__init__()
        self._cursor = None

    async def _connect_impl(self, config: ConnectionConfig) -> Any:
        """
        Connect to PostgreSQL database

        Args:
            config: Connection configuration

        Returns:
            Connection object
        """
        loop = asyncio.get_event_loop()

        # Build connection parameters
        conn_params = {
            'host': config.host,
            'port': config.port,
            'database': config.database,
            'user': config.username,
            'password': config.password,
        }

        # Add extra parameters
        if config.extra_params:
            conn_params.update(config.extra_params)

        # Create connection in thread pool (psycopg2 is synchronous)
        connection = await loop.run_in_executor(
            None,
            lambda: psycopg2.connect(**conn_params)
        )

        # Set autocommit for DDL operations
        await loop.run_in_executor(None, setattr, connection, 'autocommit', False)

        return connection

    async def _disconnect_impl(self) -> None:
        """Disconnect from PostgreSQL"""
        if self._cursor:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._cursor.close)
            self._cursor = None

        if self._connection:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._connection.close)

    async def _execute_query_impl(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute PostgreSQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Dictionary with columns, rows, rowcount, and metadata
        """
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        loop = asyncio.get_event_loop()

        # Create cursor with dictionary support
        if not self._cursor:
            def create_cursor():
                return self._connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            self._cursor = await loop.run_in_executor(None, create_cursor)

        # Execute query
        if params:
            await loop.run_in_executor(None, self._cursor.execute, query, params)
        else:
            await loop.run_in_executor(None, self._cursor.execute, query)

        # Fetch results (only for SELECT queries that return data)
        columns = [desc.name for desc in self._cursor.description] if self._cursor.description else []

        # Only fetch rows if query returned results (SELECT statements)
        rows = []
        if self._cursor.description:
            try:
                rows_dict = await loop.run_in_executor(None, self._cursor.fetchall)
                # Convert RealDictRow to tuples
                if rows_dict and columns:
                    rows = [tuple(row[col] for col in columns) for row in rows_dict]
            except Exception:
                # No results to fetch (DML/DDL statements)
                pass

        rowcount = self._cursor.rowcount

        # Get metadata
        if self._config is None:
            raise MCPClientError("No active configuration", "NOT_CONFIGURED")

        metadata = {
            'database': self._config.database,
            'query_type': self._get_query_type(query)
        }

        if self._cursor.description:
            metadata['column_types'] = [desc.type_code for desc in self._cursor.description]

        return {
            'columns': columns,
            'rows': rows,
            'rowcount': rowcount,
            'metadata': metadata
        }

    async def _execute_ddl_impl(self, ddl: str) -> None:
        """Method implementation."""
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        loop = asyncio.get_event_loop()

        if not self._cursor:
            def create_cursor():
                return self._connection.cursor()

            self._cursor = await loop.run_in_executor(None, create_cursor)

        await loop.run_in_executor(None, self._cursor.execute, ddl)
        await loop.run_in_executor(None, self._connection.commit)

    def _get_ping_query(self) -> str:
        """Get PostgreSQL-specific ping query"""
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

    async def get_table_info(self, table_name: str, schema: str = 'public') -> Dict[str, Any]:
        """
        Get PostgreSQL table information

        Args:
            table_name: Name of the table
            schema: Schema name (default: 'public')

        Returns:
            Dictionary with table metadata
        """
        query = """
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %(schema)s
            AND table_name = %(table_name)s
            ORDER BY ordinal_position
        """

        result = await self.execute_query(
            query,
            {'schema': schema, 'table_name': table_name}
        )

        return {
            'table_name': table_name,
            'schema': schema,
            'columns': [
                {
                    'name': row[0],
                    'type': row[1],
                    'length': row[2],
                    'nullable': row[3] == 'YES',
                    'default': row[4]
                }
                for row in result.rows
            ]
        }

    async def get_table_list(self, schema: str = 'public') -> List[str]:
        """
        Get list of tables in schema

        Args:
            schema: Schema name (default: 'public')

        Returns:
            List of table names
        """
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %(schema)s
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        result = await self.execute_query(query, {'schema': schema})
        return [row[0] for row in result.rows]

    async def get_schemas(self) -> List[str]:
        """
        Get list of schemas

        Returns:
            List of schema names
        """
        query = """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
        """
        result = await self.execute_query(query)
        return [row[0] for row in result.rows]
