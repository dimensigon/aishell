"""
SQLite MCP Client Implementation

Implements SQLite database connectivity with async operations and connection pooling.
"""

import asyncio
import sqlite3
import aiosqlite
from typing import Any, Dict, Optional, List
from pathlib import Path
from .base import BaseMCPClient, ConnectionConfig, MCPClientError


class SQLiteClient(BaseMCPClient):
    """
    SQLite database client with async support

    Provides async interface to SQLite database operations with WAL mode
    for better concurrency.
    """

    def __init__(self) -> None:
        super().__init__()
        self._cursor = None
        self._db_path = None

    async def _connect_impl(self, config: ConnectionConfig) -> Any:
        """
        Connect to SQLite database

        Args:
            config: Connection configuration (host field used as db_path)

        Returns:
            Connection object
        """
        # SQLite uses file path, so host field contains the database file path
        # If database field is provided, use it; otherwise use host field
        if config.database and config.database != 'sqlite':
            self._db_path = config.database
        else:
            self._db_path = config.host

        # Ensure parent directory exists
        db_file = Path(self._db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # Create connection with aiosqlite
        connection = await aiosqlite.connect(self._db_path)

        # Enable WAL mode for better concurrency
        await connection.execute('PRAGMA journal_mode=WAL')

        # Enable foreign keys
        await connection.execute('PRAGMA foreign_keys=ON')

        # Set synchronous mode (can be configured via extra_params)
        sync_mode = 'NORMAL'
        if config.extra_params and 'synchronous' in config.extra_params:
            sync_mode = config.extra_params['synchronous']
        await connection.execute(f'PRAGMA synchronous={sync_mode}')

        # Set cache size (negative means KB, positive means pages)
        cache_size = -32000  # 32MB default
        if config.extra_params and 'cache_size' in config.extra_params:
            cache_size = config.extra_params['cache_size']
        await connection.execute(f'PRAGMA cache_size={cache_size}')

        await connection.commit()

        return connection

    async def _disconnect_impl(self) -> None:
        """Disconnect from SQLite"""
        if self._cursor:
            await self._cursor.close()
            self._cursor = None

        if self._connection:
            await self._connection.close()

    async def _execute_query_impl(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute SQLite query

        Args:
            query: SQL query string
            params: Query parameters (dict or tuple)

        Returns:
            Dictionary with columns, rows, rowcount, and metadata
        """
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        # Create cursor
        if not self._cursor:
            self._cursor = await self._connection.cursor()

        # Execute query with parameters
        if params:
            # Convert dict to tuple for positional parameters if needed
            if isinstance(params, dict):
                # Named parameters use :name syntax
                await self._cursor.execute(query, params)
            else:
                # Positional parameters use ? syntax
                await self._cursor.execute(query, params)
        else:
            await self._cursor.execute(query)

        # Fetch results
        columns = []
        rows = []

        if self._cursor.description:
            columns = [desc[0] for desc in self._cursor.description]
            rows = await self._cursor.fetchall()

        rowcount = self._cursor.rowcount

        # Get metadata
        metadata = {
            'database': self._db_path,
            'query_type': self._get_query_type(query)
        }

        # For write operations, commit the transaction
        if metadata['query_type'] in ['INSERT', 'UPDATE', 'DELETE', 'DDL']:
            await self._connection.commit()

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
        """Get SQLite-specific ping query"""
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

    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get SQLite table information

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table metadata
        """
        query = f"PRAGMA table_info({table_name})"
        result = await self.execute_query(query)

        return {
            'table_name': table_name,
            'columns': [
                {
                    'cid': row[0],
                    'name': row[1],
                    'type': row[2],
                    'not_null': bool(row[3]),
                    'default': row[4],
                    'pk': bool(row[5])
                }
                for row in result.rows
            ]
        }

    async def get_table_list(self) -> List[str]:
        """
        Get list of tables in database

        Returns:
            List of table names
        """
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        result = await self.execute_query(query)
        return [row[0] for row in result.rows]

    async def get_indexes(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of indexes

        Args:
            table_name: Optional table name to filter indexes

        Returns:
            List of index information
        """
        if table_name:
            query = f"PRAGMA index_list({table_name})"
            result = await self.execute_query(query)

            indexes = []
            for row in result.rows:
                index_name = row[1]
                # Get index details
                index_info = await self.execute_query(f"PRAGMA index_info({index_name})")
                indexes.append({
                    'name': index_name,
                    'unique': bool(row[2]),
                    'origin': row[3],
                    'partial': bool(row[4]),
                    'columns': [col[2] for col in index_info.rows]
                })
            return indexes
        else:
            query = """
                SELECT name, tbl_name FROM sqlite_master
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """
            result = await self.execute_query(query)
            return [{'name': row[0], 'table': row[1]} for row in result.rows]

    async def vacuum(self) -> None:
        """
        Optimize the database by running VACUUM

        Rebuilds the database file, repacking it into a minimal amount of disk space.
        """
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        await self._connection.execute('VACUUM')
        await self._connection.commit()

    async def analyze(self, table_name: Optional[str] = None) -> None:
        """
        Update statistics for query optimizer

        Args:
            table_name: Optional table name to analyze specific table
        """
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        if table_name:
            await self._connection.execute(f'ANALYZE {table_name}')
        else:
            await self._connection.execute('ANALYZE')
        await self._connection.commit()

    async def checkpoint(self) -> Dict[str, int]:
        """
        Run WAL checkpoint

        Returns:
            Dictionary with checkpoint statistics
        """
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        cursor = await self._connection.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        result = await cursor.fetchone()
        await cursor.close()

        return {
            'busy': result[0],
            'log_frames': result[1],
            'checkpointed_frames': result[2]
        }

    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics

        Returns:
            Dictionary with database information
        """
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        # Get page count and page size
        page_count_cursor = await self._connection.execute('PRAGMA page_count')
        page_count = (await page_count_cursor.fetchone())[0]
        await page_count_cursor.close()

        page_size_cursor = await self._connection.execute('PRAGMA page_size')
        page_size = (await page_size_cursor.fetchone())[0]
        await page_size_cursor.close()

        # Get journal mode
        journal_cursor = await self._connection.execute('PRAGMA journal_mode')
        journal_mode = (await journal_cursor.fetchone())[0]
        await journal_cursor.close()

        # Get table count
        tables = await self.get_table_list()

        db_file = Path(self._db_path)
        file_size = db_file.stat().st_size if db_file.exists() else 0

        return {
            'database_path': self._db_path,
            'file_size_bytes': file_size,
            'file_size_mb': file_size / (1024 * 1024),
            'page_count': page_count,
            'page_size': page_size,
            'theoretical_size': page_count * page_size,
            'journal_mode': journal_mode,
            'table_count': len(tables),
            'tables': tables
        }

    async def backup(self, backup_path: str) -> None:
        """
        Create a backup of the database

        Args:
            backup_path: Path for the backup file
        """
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        # Create backup directory if needed
        backup_file = Path(backup_path)
        backup_file.parent.mkdir(parents=True, exist_ok=True)

        # Use SQLite backup API
        async with aiosqlite.connect(backup_path) as backup_conn:
            await self._connection.backup(backup_conn)

    async def attach_database(self, db_path: str, schema_name: str) -> None:
        """
        Attach another database

        Args:
            db_path: Path to database to attach
            schema_name: Schema name to use for the attached database
        """
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        await self._connection.execute(f"ATTACH DATABASE ? AS {schema_name}", (db_path,))

    async def detach_database(self, schema_name: str) -> None:
        """
        Detach a database

        Args:
            schema_name: Schema name of the database to detach
        """
        if self._connection is None:
            raise MCPClientError("No active connection", "NOT_CONNECTED")

        await self._connection.execute(f"DETACH DATABASE {schema_name}")
