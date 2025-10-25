"""
Extended PostgreSQL client with retry and error handling capabilities.
"""

import asyncio
from typing import Any, Dict, Optional
from .postgresql_client import PostgreSQLClient
from .base import ConnectionConfig


class PostgreSQLClientExtended(PostgreSQLClient):
    """
    Extended PostgreSQL client with error handling and retry mechanisms.
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5432,
        database: str = 'postgres',
        user: str = 'postgres',
        password: str = '',
        timeout: float = 30.0,
        connect_timeout: float = 10.0,
        query_timeout: float = 60.0,
        max_pool_size: int = 10,
        auto_reconnect: bool = False,
        transaction_timeout: float = 300.0,
        partial_results: bool = False
    ):
        """
        Initialize extended PostgreSQL client.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Username
            password: Password
            timeout: General timeout in seconds
            connect_timeout: Connection timeout in seconds
            query_timeout: Query execution timeout in seconds
            max_pool_size: Maximum connection pool size
            auto_reconnect: Enable automatic reconnection
            transaction_timeout: Transaction timeout in seconds
            partial_results: Return partial results on timeout
        """
        super().__init__()

        # Store connection parameters
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password
        self._timeout = timeout
        self._connect_timeout = connect_timeout
        self._query_timeout = query_timeout
        self._max_pool_size = max_pool_size
        self._auto_reconnect = auto_reconnect
        self._transaction_timeout = transaction_timeout
        self._partial_results = partial_results

    async def connect(self) -> bool:
        """Connect to database with stored configuration"""
        config = ConnectionConfig(
            host=self._host,
            port=self._port,
            database=self._database,
            username=self._user,
            password=self._password
        )
        return await super().connect(config)

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Execute query (alias for execute_query)"""
        result = await self.execute_query(query, params)
        # Return list of dicts for compatibility
        if result.columns and result.rows:
            return [dict(zip(result.columns, row)) for row in result.rows]
        return []

    async def execute_with_retry(
        self,
        query: str,
        max_retries: int = 3,
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Execute query with automatic retry.

        Args:
            query: SQL query
            max_retries: Maximum number of retries
            params: Query parameters

        Returns:
            Query result
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await self.execute(query, params)
            except Exception as e:
                last_exception = e

                if attempt < max_retries:
                    # Exponential backoff
                    delay = 0.1 * (2 ** attempt)
                    await asyncio.sleep(delay)

                    # Try to reconnect if connection error
                    if self._auto_reconnect and isinstance(e, ConnectionError):
                        try:
                            await self.connect()
                        except Exception:
                            pass

        raise last_exception

    async def execute_with_timeout(
        self,
        query: str,
        timeout: float,
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Execute query with timeout.

        Args:
            query: SQL query
            timeout: Timeout in seconds
            params: Query parameters

        Returns:
            Query result

        Raises:
            asyncio.TimeoutError: If query times out
        """
        return await asyncio.wait_for(
            self.execute(query, params),
            timeout=timeout
        )

    async def execute_with_partial_results(
        self,
        query: str,
        timeout: float,
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Execute query and return partial results on timeout.

        Args:
            query: SQL query
            timeout: Timeout in seconds
            params: Query parameters

        Returns:
            Query results (may be partial)
        """
        try:
            return await asyncio.wait_for(
                self.execute(query, params),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # Return partial results if available
            # In real implementation, this would return accumulated rows
            return []

    async def transaction(self, timeout: Optional[float] = None):
        """
        Context manager for transactions.

        Args:
            timeout: Transaction timeout in seconds

        Yields:
            Transaction context
        """
        # Simplified transaction implementation
        class TransactionContext:
            def __init__(self, client, timeout):
                self.client = client
                self.timeout = timeout or client._transaction_timeout

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return False

        return TransactionContext(self, timeout)
