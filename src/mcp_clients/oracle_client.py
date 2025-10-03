"""
Oracle MCP Client Implementation

Implements Oracle database connectivity using cx_Oracle in thin mode
(no Oracle Instant Client required).
"""

import asyncio
from typing import Any, Dict, Optional, List
import oracledb
from .base import BaseMCPClient, ConnectionConfig, MCPClientError


class OracleClient(BaseMCPClient):
    """
    Oracle database client using thin mode connection

    Uses oracledb (cx_Oracle) thin mode which doesn't require
    Oracle Instant Client installation.
    """

    def __init__(self):
        super().__init__()
        self._cursor = None

    async def _connect_impl(self, config: ConnectionConfig) -> Any:
        """
        Connect to Oracle database using thin mode

        Args:
            config: Connection configuration

        Returns:
            Connection object
        """
        loop = asyncio.get_event_loop()

        # Build connection string for thin mode
        dsn = f"{config.host}:{config.port}/{config.database}"

        # Get additional parameters
        extra_params = config.extra_params or {}

        # Create connection in thread pool (oracledb is synchronous)
        # Note: Thin mode is the default in oracledb (no explicit mode parameter needed)
        connection = await loop.run_in_executor(
            None,
            lambda: oracledb.connect(
                user=config.username,
                password=config.password,
                dsn=dsn,
                **extra_params
            )
        )

        return connection

    async def _disconnect_impl(self):
        """Close Oracle connection"""
        if self._cursor:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._cursor.close)
            self._cursor = None

        if self._connection:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._connection.close)

    async def _execute_query_impl(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Oracle query

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Dictionary with columns, rows, rowcount, and metadata
        """
        loop = asyncio.get_event_loop()

        # Create cursor
        if not self._cursor:
            self._cursor = await loop.run_in_executor(None, self._connection.cursor)

        # Execute query
        if params:
            await loop.run_in_executor(None, self._cursor.execute, query, params)
        else:
            await loop.run_in_executor(None, self._cursor.execute, query)

        # Fetch results
        columns = [desc[0] for desc in self._cursor.description] if self._cursor.description else []
        rows = await loop.run_in_executor(None, self._cursor.fetchall)
        rowcount = self._cursor.rowcount

        # Get metadata
        metadata = {
            'database': self._config.database,
            'query_type': self._get_query_type(query)
        }

        if self._cursor.description:
            metadata['column_types'] = [desc[1].__name__ for desc in self._cursor.description]

        return {
            'columns': columns,
            'rows': rows,
            'rowcount': rowcount,
            'metadata': metadata
        }

    async def _execute_ddl_impl(self, ddl: str):
        """
        Execute Oracle DDL statement

        Args:
            ddl: DDL statement string
        """
        loop = asyncio.get_event_loop()

        if not self._cursor:
            self._cursor = await loop.run_in_executor(None, self._connection.cursor)

        await loop.run_in_executor(None, self._cursor.execute, ddl)
        await loop.run_in_executor(None, self._connection.commit)

    def _get_ping_query(self) -> str:
        """Get Oracle-specific ping query"""
        return "SELECT 1 FROM DUAL"

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

    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get Oracle table information

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table metadata
        """
        query = """
            SELECT
                column_name,
                data_type,
                data_length,
                nullable,
                data_default
            FROM user_tab_columns
            WHERE table_name = :table_name
            ORDER BY column_id
        """

        result = await self.execute_query(query, {'table_name': table_name.upper()})

        return {
            'table_name': table_name,
            'columns': [
                {
                    'name': row[0],
                    'type': row[1],
                    'length': row[2],
                    'nullable': row[3] == 'Y',
                    'default': row[4]
                }
                for row in result.rows
            ]
        }

    async def get_table_list(self) -> List[str]:
        """
        Get list of tables in current schema

        Returns:
            List of table names
        """
        query = "SELECT table_name FROM user_tables ORDER BY table_name"
        result = await self.execute_query(query)
        return [row[0] for row in result.rows]
