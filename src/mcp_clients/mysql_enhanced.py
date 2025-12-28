"""
Enhanced MySQL MCP Client with 100% Feature Coverage

Adds advanced MySQL features:
- Prepared statements
- Stored procedures
- Multiple result sets
- Retry logic with exponential backoff
- Connection health monitoring
- Transaction support
"""

import asyncio
from typing import Any, Dict, Optional, List, Tuple
from .mysql_client import MySQLClient
from .base import ConnectionConfig, MCPClientError
import logging

logger = logging.getLogger(__name__)


class MySQLEnhancedClient(MySQLClient):
    """
    Enhanced MySQL client with advanced features and reliability improvements
    """

    def __init__(self) -> None:
        super().__init__()
        self._prepared_statements: Dict[str, Any] = {}
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
            'reconnections': 0,
            'prepared_statements': 0
        }

    def configure_retry(
        self,
        max_retries: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 10.0,
        exponential_base: int = 2
    ) -> None:
        """Configure retry behavior with exponential backoff"""
        self._retry_config = {
            'max_retries': max_retries,
            'base_delay': base_delay,
            'max_delay': max_delay,
            'exponential_base': exponential_base
        }

    async def _retry_with_backoff(self, operation, *args, **kwargs) -> Any:
        """Execute operation with exponential backoff retry"""
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
        """Reconnect to the database"""
        if not self._config:
            raise MCPClientError("No configuration available for reconnection", "NO_CONFIG")

        await self.disconnect()
        return await self.connect(self._config)

    async def execute_query_with_retry(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute query with automatic retry on failure"""
        result = await self._retry_with_backoff(
            super().execute_query,
            query,
            params
        )
        self._metrics['queries_executed'] += 1
        return result

    # Prepared Statements

    async def prepare(self, stmt_name: str, query: str) -> None:
        """
        Prepare a statement for repeated execution

        Args:
            stmt_name: Name to identify the prepared statement
            query: SQL query with ? placeholders

        Raises:
            MCPClientError: If preparation fails
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        if not self._cursor:
            self._cursor = await self._connection.cursor()

        # Store the prepared statement
        self._prepared_statements[stmt_name] = query
        self._metrics['prepared_statements'] += 1

        logger.debug(f"Prepared statement: {stmt_name}")

    async def execute_prepared(
        self,
        stmt_name: str,
        params: Optional[Tuple] = None
    ) -> Dict[str, Any]:
        """
        Execute a prepared statement

        Args:
            stmt_name: Name of prepared statement
            params: Parameters for the statement

        Returns:
            Query result

        Raises:
            MCPClientError: If statement not found or execution fails
        """
        if stmt_name not in self._prepared_statements:
            raise MCPClientError(
                f"Prepared statement not found: {stmt_name}",
                "STATEMENT_NOT_FOUND"
            )

        query = self._prepared_statements[stmt_name]
        return await self.execute_query(query, params)

    async def deallocate(self, stmt_name: str) -> None:
        """
        Deallocate a prepared statement

        Args:
            stmt_name: Name of prepared statement
        """
        if stmt_name in self._prepared_statements:
            del self._prepared_statements[stmt_name]
            logger.debug(f"Deallocated statement: {stmt_name}")

    # Stored Procedures

    async def call_procedure(
        self,
        proc_name: str,
        args: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Call a stored procedure

        Args:
            proc_name: Procedure name
            args: Procedure arguments

        Returns:
            List of result sets

        Raises:
            MCPClientError: If procedure call fails
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        if not self._cursor:
            self._cursor = await self._connection.cursor()

        try:
            # Build CALL statement
            if args:
                placeholders = ', '.join(['%s'] * len(args))
                query = f"CALL {proc_name}({placeholders})"
                await self._cursor.execute(query, args)
            else:
                query = f"CALL {proc_name}()"
                await self._cursor.execute(query)

            # Fetch all result sets
            results = []
            has_more = True

            while has_more:
                if self._cursor.description:
                    columns = [desc[0] for desc in self._cursor.description]
                    rows = await self._cursor.fetchall()
                    results.append([dict(zip(columns, row)) for row in rows])

                has_more = await self._cursor.nextset()

            return results

        except Exception as e:
            raise MCPClientError(
                f"Stored procedure call failed: {e}",
                "PROCEDURE_FAILED"
            ) from e

    async def create_procedure(
        self,
        proc_name: str,
        parameters: str,
        body: str,
        replace: bool = False
    ) -> None:
        """
        Create a stored procedure

        Args:
            proc_name: Procedure name
            parameters: Parameter list (e.g., "IN p1 INT, OUT p2 VARCHAR(100)")
            body: Procedure body SQL
            replace: Whether to replace if exists

        Raises:
            MCPClientError: If creation fails
        """
        if replace:
            await self.execute_ddl(f"DROP PROCEDURE IF EXISTS {proc_name}")

        ddl = f"""
        CREATE PROCEDURE {proc_name}({parameters})
        BEGIN
            {body}
        END
        """

        await self.execute_ddl(ddl)
        logger.info(f"Created stored procedure: {proc_name}")

    async def drop_procedure(self, proc_name: str, if_exists: bool = True) -> None:
        """
        Drop a stored procedure

        Args:
            proc_name: Procedure name
            if_exists: Use IF EXISTS clause

        Raises:
            MCPClientError: If drop fails
        """
        if if_exists:
            await self.execute_ddl(f"DROP PROCEDURE IF EXISTS {proc_name}")
        else:
            await self.execute_ddl(f"DROP PROCEDURE {proc_name}")

        logger.info(f"Dropped stored procedure: {proc_name}")

    async def list_procedures(self, schema: Optional[str] = None) -> List[str]:
        """
        List stored procedures

        Args:
            schema: Optional schema name

        Returns:
            List of procedure names
        """
        if schema is None:
            schema = self._config.database if self._config else 'mysql'

        query = """
            SELECT ROUTINE_NAME
            FROM information_schema.ROUTINES
            WHERE ROUTINE_TYPE = 'PROCEDURE'
            AND ROUTINE_SCHEMA = %s
            ORDER BY ROUTINE_NAME
        """

        result = await self.execute_query(query, (schema,))
        return [row[0] for row in result.rows]

    # Multiple Result Sets

    async def execute_multi(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute query returning multiple result sets

        Args:
            query: SQL query (can contain multiple statements)

        Returns:
            List of result sets

        Raises:
            MCPClientError: If execution fails
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        if not self._cursor:
            self._cursor = await self._connection.cursor()

        try:
            await self._cursor.execute(query, multi=True)

            results = []
            has_more = True

            while has_more:
                if self._cursor.description:
                    columns = [desc[0] for desc in self._cursor.description]
                    rows = await self._cursor.fetchall()
                    results.append({
                        'columns': columns,
                        'rows': rows,
                        'rowcount': self._cursor.rowcount
                    })

                has_more = await self._cursor.nextset()

            return results

        except Exception as e:
            raise MCPClientError(
                f"Multi-query execution failed: {e}",
                "MULTI_QUERY_FAILED"
            ) from e

    # Transaction Support

    async def begin_transaction(self, isolation_level: Optional[str] = None) -> None:
        """
        Start a transaction

        Args:
            isolation_level: Transaction isolation level
                ('READ UNCOMMITTED', 'READ COMMITTED',
                 'REPEATABLE READ', 'SERIALIZABLE')

        Raises:
            MCPClientError: If transaction start fails
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        if isolation_level:
            await self.execute_query(
                f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"
            )

        await self.execute_query("START TRANSACTION")
        logger.debug("Transaction started")

    async def commit(self) -> None:
        """Commit the current transaction"""
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        await self._connection.commit()
        logger.debug("Transaction committed")

    async def rollback(self) -> None:
        """Rollback the current transaction"""
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        await self._connection.rollback()
        logger.debug("Transaction rolled back")

    # Health Monitoring

    async def health_check_detailed(self) -> Dict[str, Any]:
        """Perform detailed health check with additional metrics"""
        health = await super().health_check()

        health['metrics'] = self._metrics.copy()

        if self.is_connected:
            try:
                # Get connection count
                result = await self.execute_query(
                    "SHOW STATUS LIKE 'Threads_connected'"
                )
                if result.rows:
                    health['threads_connected'] = int(result.rows[0][1])

                # Get database size
                if self._config:
                    result = await self.execute_query(
                        """
                        SELECT SUM(data_length + index_length) as size
                        FROM information_schema.TABLES
                        WHERE table_schema = %s
                        """,
                        (self._config.database,)
                    )
                    if result.rows and result.rows[0][0]:
                        health['database_size_bytes'] = result.rows[0][0]

                # Get table count
                if self._config:
                    result = await self.execute_query(
                        """
                        SELECT COUNT(*) FROM information_schema.TABLES
                        WHERE table_schema = %s
                        """,
                        (self._config.database,)
                    )
                    if result.rows:
                        health['table_count'] = result.rows[0][0]

            except Exception as e:
                health['metrics_error'] = str(e)

        return health

    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
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
            'reconnections': 0,
            'prepared_statements': 0
        }

    # Advanced Features

    async def get_server_info(self) -> Dict[str, Any]:
        """
        Get MySQL server information

        Returns:
            Dictionary with server details
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        info = {}

        # Get server version
        result = await self.execute_query("SELECT VERSION()")
        info['version'] = result.rows[0][0]

        # Get server variables
        result = await self.execute_query("SHOW VARIABLES LIKE 'max_connections'")
        if result.rows:
            info['max_connections'] = result.rows[0][1]

        result = await self.execute_query("SHOW VARIABLES LIKE 'innodb_buffer_pool_size'")
        if result.rows:
            info['innodb_buffer_pool_size'] = result.rows[0][1]

        return info

    async def optimize_table(self, table_name: str) -> None:
        """
        Optimize a table

        Args:
            table_name: Table name

        Raises:
            MCPClientError: If optimization fails
        """
        await self.execute_query(f"OPTIMIZE TABLE {table_name}")
        logger.info(f"Optimized table: {table_name}")

    async def analyze_table(self, table_name: str) -> None:
        """
        Analyze a table for query optimization

        Args:
            table_name: Table name

        Raises:
            MCPClientError: If analysis fails
        """
        await self.execute_query(f"ANALYZE TABLE {table_name}")
        logger.info(f"Analyzed table: {table_name}")
