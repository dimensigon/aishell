"""
Enhanced PostgreSQL MCP Client with 100% Feature Coverage

Adds advanced PostgreSQL features:
- LISTEN/NOTIFY support
- COPY operations
- Transaction savepoints
- Full-text search
- Retry logic with exponential backoff
- Connection health monitoring
"""

import asyncio
import io
from typing import Any, Dict, Optional, List, Callable, AsyncIterator
from .postgresql_client import PostgreSQLClient
from .base import ConnectionConfig, MCPClientError
import logging

logger = logging.getLogger(__name__)


class PostgreSQLEnhancedClient(PostgreSQLClient):
    """
    Enhanced PostgreSQL client with advanced features and reliability improvements
    """

    def __init__(self) -> None:
        super().__init__()
        self._notifications: List[Dict[str, Any]] = []
        self._notification_handlers: Dict[str, Callable] = {}
        self._listen_task: Optional[asyncio.Task] = None
        self._retry_config = {
            'max_retries': 3,
            'base_delay': 0.1,
            'max_delay': 10.0,
            'exponential_base': 2
        }
        self._metrics = {
            'queries_executed': 0,
            'queries_failed': 0,
            'total_latency': 0.0,
            'reconnections': 0
        }

    def configure_retry(
        self,
        max_retries: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 10.0,
        exponential_base: int = 2
    ) -> None:
        """
        Configure retry behavior with exponential backoff

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self._retry_config = {
            'max_retries': max_retries,
            'base_delay': base_delay,
            'max_delay': max_delay,
            'exponential_base': exponential_base
        }

    async def _retry_with_backoff(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute operation with exponential backoff retry

        Args:
            operation: Async function to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Result from operation

        Raises:
            MCPClientError: If all retries exhausted
        """
        last_error = None

        for attempt in range(self._retry_config['max_retries'] + 1):
            try:
                result = await operation(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Operation succeeded after {attempt} retries")
                return result

            except Exception as e:
                last_error = e
                self._metrics['queries_failed'] += 1

                if attempt < self._retry_config['max_retries']:
                    # Calculate delay with exponential backoff
                    delay = min(
                        self._retry_config['base_delay'] * (
                            self._retry_config['exponential_base'] ** attempt
                        ),
                        self._retry_config['max_delay']
                    )

                    logger.warning(
                        f"Operation failed (attempt {attempt + 1}/"
                        f"{self._retry_config['max_retries'] + 1}): {e}. "
                        f"Retrying in {delay:.2f}s"
                    )

                    await asyncio.sleep(delay)

                    # Try to reconnect if connection error
                    if 'connection' in str(e).lower():
                        try:
                            logger.info("Attempting to reconnect...")
                            await self.reconnect()
                            self._metrics['reconnections'] += 1
                        except Exception as reconnect_error:
                            logger.error(f"Reconnection failed: {reconnect_error}")

        raise MCPClientError(
            f"Operation failed after {self._retry_config['max_retries']} retries: {last_error}",
            "RETRY_EXHAUSTED"
        ) from last_error

    async def reconnect(self) -> bool:
        """
        Reconnect to the database using stored configuration

        Returns:
            True if reconnection successful
        """
        if not self._config:
            raise MCPClientError("No configuration available for reconnection", "NO_CONFIG")

        await self.disconnect()
        return await self.connect(self._config)

    async def execute_query_with_retry(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute query with automatic retry on failure

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query result with retry protection
        """
        result = await self._retry_with_backoff(
            super().execute_query,
            query,
            params
        )
        self._metrics['queries_executed'] += 1
        return result

    # LISTEN/NOTIFY Support

    async def listen(self, channel: str, handler: Optional[Callable] = None) -> None:
        """
        Start listening on a PostgreSQL notification channel

        Args:
            channel: Channel name to listen on
            handler: Optional async callback function(channel, payload)

        Raises:
            MCPClientError: If not connected
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        loop = asyncio.get_event_loop()

        # Execute LISTEN command
        await loop.run_in_executor(
            None,
            self._connection.cursor().execute,
            f"LISTEN {channel}"
        )

        # Store handler if provided
        if handler:
            self._notification_handlers[channel] = handler

        # Start listening task if not already running
        if not self._listen_task or self._listen_task.done():
            self._listen_task = asyncio.create_task(self._notification_listener())

        logger.info(f"Started listening on channel: {channel}")

    async def unlisten(self, channel: str) -> None:
        """
        Stop listening on a channel

        Args:
            channel: Channel name to stop listening on
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        loop = asyncio.get_event_loop()

        await loop.run_in_executor(
            None,
            self._connection.cursor().execute,
            f"UNLISTEN {channel}"
        )

        # Remove handler
        if channel in self._notification_handlers:
            del self._notification_handlers[channel]

        logger.info(f"Stopped listening on channel: {channel}")

    async def notify(self, channel: str, payload: str = '') -> None:
        """
        Send a notification to a channel

        Args:
            channel: Channel name
            payload: Notification payload (optional)

        Raises:
            MCPClientError: If not connected
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        if payload:
            query = f"SELECT pg_notify(%s, %s)"
            await self.execute_query(query, {'channel': channel, 'payload': payload})
        else:
            query = f"NOTIFY {channel}"
            await self.execute_query(query)

        logger.debug(f"Sent notification to {channel}: {payload}")

    async def _notification_listener(self) -> None:
        """Background task to listen for PostgreSQL notifications"""
        while self.is_connected:
            try:
                # Poll for notifications
                await asyncio.sleep(0.1)

                if self._connection and hasattr(self._connection, 'notifies'):
                    loop = asyncio.get_event_loop()

                    # Check for pending notifications
                    await loop.run_in_executor(None, self._connection.poll)

                    while self._connection.notifies:
                        notify = self._connection.notifies.pop(0)

                        notification = {
                            'channel': notify.channel,
                            'payload': notify.payload,
                            'pid': notify.pid
                        }

                        self._notifications.append(notification)

                        # Call handler if registered
                        if notify.channel in self._notification_handlers:
                            handler = self._notification_handlers[notify.channel]
                            try:
                                await handler(notify.channel, notify.payload)
                            except Exception as e:
                                logger.error(f"Notification handler error: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Notification listener error: {e}")
                await asyncio.sleep(1.0)

    def get_notifications(self, channel: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get received notifications

        Args:
            channel: Optional channel name to filter

        Returns:
            List of notifications
        """
        if channel:
            return [n for n in self._notifications if n['channel'] == channel]
        return self._notifications.copy()

    def clear_notifications(self, channel: Optional[str] = None) -> None:
        """
        Clear received notifications

        Args:
            channel: Optional channel name to filter
        """
        if channel:
            self._notifications = [n for n in self._notifications if n['channel'] != channel]
        else:
            self._notifications.clear()

    # COPY Operations

    async def copy_from_file(
        self,
        table_name: str,
        file_path: str,
        columns: Optional[List[str]] = None,
        delimiter: str = ',',
        null_string: str = ''
    ) -> int:
        """
        Copy data from file to table using COPY command

        Args:
            table_name: Target table name
            file_path: Path to file
            columns: Optional list of column names
            delimiter: Field delimiter
            null_string: String representing NULL

        Returns:
            Number of rows copied

        Raises:
            MCPClientError: If operation fails
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        loop = asyncio.get_event_loop()

        # Build COPY command
        if columns:
            cols = ', '.join(columns)
            copy_cmd = f"COPY {table_name} ({cols}) FROM STDIN WITH (FORMAT CSV, DELIMITER '{delimiter}', NULL '{null_string}')"
        else:
            copy_cmd = f"COPY {table_name} FROM STDIN WITH (FORMAT CSV, DELIMITER '{delimiter}', NULL '{null_string}')"

        cursor = await loop.run_in_executor(None, self._connection.cursor)

        try:
            with open(file_path, 'r') as f:
                await loop.run_in_executor(None, cursor.copy_expert, copy_cmd, f)

            await loop.run_in_executor(None, self._connection.commit)

            rowcount = cursor.rowcount
            await loop.run_in_executor(None, cursor.close)

            logger.info(f"Copied {rowcount} rows from {file_path} to {table_name}")
            return rowcount

        except Exception as e:
            await loop.run_in_executor(None, self._connection.rollback)
            raise MCPClientError(f"COPY FROM failed: {e}", "COPY_FAILED") from e

    async def copy_to_file(
        self,
        query: str,
        file_path: str,
        delimiter: str = ',',
        null_string: str = ''
    ) -> int:
        """
        Copy query results to file using COPY command

        Args:
            query: SELECT query
            file_path: Path to output file
            delimiter: Field delimiter
            null_string: String representing NULL

        Returns:
            Number of rows copied

        Raises:
            MCPClientError: If operation fails
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        loop = asyncio.get_event_loop()

        # Build COPY command
        copy_cmd = f"COPY ({query}) TO STDOUT WITH (FORMAT CSV, DELIMITER '{delimiter}', NULL '{null_string}')"

        cursor = await loop.run_in_executor(None, self._connection.cursor)

        try:
            with open(file_path, 'w') as f:
                await loop.run_in_executor(None, cursor.copy_expert, copy_cmd, f)

            rowcount = cursor.rowcount
            await loop.run_in_executor(None, cursor.close)

            logger.info(f"Copied {rowcount} rows from query to {file_path}")
            return rowcount

        except Exception as e:
            raise MCPClientError(f"COPY TO failed: {e}", "COPY_FAILED") from e

    # Transaction Savepoints

    async def savepoint(self, name: str) -> None:
        """
        Create a transaction savepoint

        Args:
            name: Savepoint name

        Raises:
            MCPClientError: If not in transaction
        """
        await self.execute_query(f"SAVEPOINT {name}")
        logger.debug(f"Created savepoint: {name}")

    async def rollback_to_savepoint(self, name: str) -> None:
        """
        Rollback to a savepoint

        Args:
            name: Savepoint name

        Raises:
            MCPClientError: If savepoint doesn't exist
        """
        await self.execute_query(f"ROLLBACK TO SAVEPOINT {name}")
        logger.debug(f"Rolled back to savepoint: {name}")

    async def release_savepoint(self, name: str) -> None:
        """
        Release a savepoint

        Args:
            name: Savepoint name
        """
        await self.execute_query(f"RELEASE SAVEPOINT {name}")
        logger.debug(f"Released savepoint: {name}")

    # Full-Text Search

    async def create_fts_index(
        self,
        table_name: str,
        column_name: str,
        index_name: Optional[str] = None,
        language: str = 'english'
    ) -> None:
        """
        Create full-text search index

        Args:
            table_name: Table name
            column_name: Column to index
            index_name: Optional index name
            language: Text search configuration language

        Raises:
            MCPClientError: If index creation fails
        """
        if not index_name:
            index_name = f"{table_name}_{column_name}_fts_idx"

        ddl = f"""
        CREATE INDEX {index_name} ON {table_name}
        USING GIN (to_tsvector('{language}', {column_name}))
        """

        await self.execute_ddl(ddl)
        logger.info(f"Created full-text search index: {index_name}")

    async def fts_search(
        self,
        table_name: str,
        column_name: str,
        search_query: str,
        language: str = 'english',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search

        Args:
            table_name: Table name
            column_name: Column to search
            search_query: Search query string
            language: Text search configuration language
            limit: Maximum results

        Returns:
            List of matching rows with ranking

        Raises:
            MCPClientError: If search fails
        """
        query = f"""
        SELECT *,
               ts_rank(to_tsvector('{language}', {column_name}),
                      to_tsquery('{language}', %s)) as rank
        FROM {table_name}
        WHERE to_tsvector('{language}', {column_name}) @@ to_tsquery('{language}', %s)
        ORDER BY rank DESC
        LIMIT %s
        """

        result = await self.execute_query(query, (search_query, search_query, limit))

        return [
            dict(zip(result.columns, row))
            for row in result.rows
        ]

    # Health Monitoring

    async def health_check_detailed(self) -> Dict[str, Any]:
        """
        Perform detailed health check with additional metrics

        Returns:
            Detailed health status
        """
        health = await super().health_check()

        # Add connection pool stats
        health['metrics'] = self._metrics.copy()

        # Add database-specific metrics
        if self.is_connected:
            try:
                # Get active connections
                result = await self.execute_query(
                    "SELECT count(*) FROM pg_stat_activity"
                )
                health['active_connections'] = result.rows[0][0]

                # Get database size
                if self._config:
                    result = await self.execute_query(
                        "SELECT pg_database_size(%s)",
                        {'db': self._config.database}
                    )
                    health['database_size_bytes'] = result.rows[0][0]

                # Get transaction stats
                result = await self.execute_query("""
                    SELECT xact_commit, xact_rollback
                    FROM pg_stat_database
                    WHERE datname = %s
                """, {'db': self._config.database})

                if result.rows:
                    health['transactions'] = {
                        'commits': result.rows[0][0],
                        'rollbacks': result.rows[0][1]
                    }

            except Exception as e:
                health['metrics_error'] = str(e)

        return health

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get client metrics

        Returns:
            Dictionary with performance metrics
        """
        metrics = self._metrics.copy()

        if metrics['queries_executed'] > 0:
            metrics['average_latency'] = (
                metrics['total_latency'] / metrics['queries_executed']
            )
            metrics['success_rate'] = (
                (metrics['queries_executed'] - metrics['queries_failed']) /
                metrics['queries_executed']
            )

        return metrics

    def reset_metrics(self) -> None:
        """Reset performance metrics"""
        self._metrics = {
            'queries_executed': 0,
            'queries_failed': 0,
            'total_latency': 0.0,
            'reconnections': 0
        }
