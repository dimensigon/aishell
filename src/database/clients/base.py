"""
Base database client with unified interface and common functionality.

Provides:
- Connection pooling (5-20 connections)
- Async/await support
- Error handling with retry logic
- Health checks and monitoring
- Query logging and metrics
- Transaction management (ACID)
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Database health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class DatabaseError(Exception):
    """Base exception for database errors"""
    def __init__(self, message: str, error_code: Optional[str] = None, original_error: Optional[Exception] = None):
        self.message = message
        self.error_code = error_code
        self.original_error = original_error
        super().__init__(self.message)


class ConnectionError(DatabaseError):
    """Connection-specific errors"""
    pass


class QueryError(DatabaseError):
    """Query execution errors"""
    pass


class TransactionError(DatabaseError):
    """Transaction management errors"""
    pass


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    user: str
    password: str

    # Pool configuration
    min_pool_size: int = 5
    max_pool_size: int = 20
    pool_timeout: float = 30.0
    connection_timeout: float = 10.0

    # Query configuration
    query_timeout: float = 300.0
    statement_timeout: Optional[int] = None  # in milliseconds

    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0

    # SSL/TLS configuration
    ssl_enabled: bool = False
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None

    # Additional parameters
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryMetrics:
    """Query execution metrics"""
    query: str
    execution_time: float
    rows_affected: int
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    query_type: Optional[str] = None


@dataclass
class HealthCheckResult:
    """Health check result"""
    status: HealthStatus
    response_time: float
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConnectionPool:
    """
    Generic connection pool implementation

    Manages a pool of database connections with min/max sizing,
    timeout handling, and health monitoring.
    """

    def __init__(
        self,
        min_size: int = 5,
        max_size: int = 20,
        timeout: float = 30.0,
        name: str = "default"
    ):
        self.min_size = min_size
        self.max_size = max_size
        self.timeout = timeout
        self.name = name

        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._size = 0
        self._lock = asyncio.Lock()
        self._closed = False

        # Metrics
        self._created_connections = 0
        self._active_connections = 0
        self._failed_connections = 0

        logger.info(f"Initialized connection pool '{name}': min={min_size}, max={max_size}")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        if self._closed:
            raise ConnectionError("Connection pool is closed")

        connection = None
        try:
            # Try to get existing connection from pool
            try:
                connection = await asyncio.wait_for(
                    self._pool.get(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                raise ConnectionError(
                    f"Timeout acquiring connection from pool '{self.name}'",
                    error_code="POOL_TIMEOUT"
                )

            self._active_connections += 1
            yield connection

        finally:
            if connection is not None:
                try:
                    # Return connection to pool
                    await self._pool.put(connection)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
                finally:
                    self._active_connections -= 1

    async def add_connection(self, connection: Any) -> None:
        """Add a connection to the pool"""
        async with self._lock:
            if self._size >= self.max_size:
                raise ConnectionError(
                    f"Pool '{self.name}' has reached max size {self.max_size}",
                    error_code="POOL_MAX_SIZE"
                )

            await self._pool.put(connection)
            self._size += 1
            self._created_connections += 1
            logger.debug(f"Added connection to pool '{self.name}' (size: {self._size})")

    async def close(self) -> None:
        """Close all connections in the pool"""
        self._closed = True

        # Close all connections
        while not self._pool.empty():
            try:
                conn = await asyncio.wait_for(self._pool.get(), timeout=1.0)
                if hasattr(conn, 'close'):
                    if asyncio.iscoroutinefunction(conn.close):
                        await conn.close()
                    else:
                        conn.close()
            except asyncio.TimeoutError:
                break
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

        self._size = 0
        logger.info(f"Closed connection pool '{self.name}'")

    @property
    def stats(self) -> Dict[str, int]:
        """Get pool statistics"""
        return {
            'size': self._size,
            'active': self._active_connections,
            'available': self._pool.qsize(),
            'created': self._created_connections,
            'failed': self._failed_connections,
        }


class BaseDatabaseClient(ABC):
    """
    Abstract base class for database clients

    Provides common functionality:
    - Connection pooling
    - Async/await support
    - Error handling with retries
    - Health checks
    - Query logging and metrics
    - Transaction management
    """

    def __init__(self, config: DatabaseConfig, name: str = "database"):
        self.config = config
        self.name = name
        self._pool: Optional[ConnectionPool] = None
        self._lock = asyncio.Lock()
        self._initialized = False

        # Metrics
        self._query_count = 0
        self._error_count = 0
        self._total_execution_time = 0.0
        self._last_query_metrics: List[QueryMetrics] = []
        self._max_metrics = 100  # Keep last 100 queries

        logger.info(f"Created {self.__class__.__name__} for '{name}'")

    async def initialize(self) -> None:
        """Initialize the database client and connection pool"""
        async with self._lock:
            if self._initialized:
                return

            # Create connection pool
            self._pool = ConnectionPool(
                min_size=self.config.min_pool_size,
                max_size=self.config.max_pool_size,
                timeout=self.config.pool_timeout,
                name=f"{self.name}_pool"
            )

            # Create minimum connections
            for i in range(self.config.min_pool_size):
                try:
                    conn = await self._create_connection()
                    await self._pool.add_connection(conn)
                except Exception as e:
                    logger.error(f"Failed to create initial connection {i+1}: {e}")
                    raise ConnectionError(
                        f"Failed to initialize connection pool: {e}",
                        error_code="POOL_INIT_FAILED",
                        original_error=e
                    )

            self._initialized = True
            logger.info(f"Initialized database client '{self.name}' with {self.config.min_pool_size} connections")

    async def close(self) -> None:
        """Close the database client and all connections"""
        async with self._lock:
            if self._pool:
                await self._pool.close()
                self._pool = None

            self._initialized = False
            logger.info(f"Closed database client '{self.name}'")

    @abstractmethod
    async def _create_connection(self) -> Any:
        """Create a new database connection (implementation-specific)"""
        pass

    @abstractmethod
    async def _execute_impl(
        self,
        connection: Any,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[Tuple], int]:
        """
        Execute query implementation (database-specific)

        Returns:
            Tuple of (columns, rows, rowcount)
        """
        pass

    @abstractmethod
    async def _get_ping_query(self) -> str:
        """Get database-specific ping query for health checks"""
        pass

    async def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a SQL query with retry logic and metrics

        Args:
            query: SQL query string
            params: Query parameters
            retry: Enable retry on transient errors

        Returns:
            Dictionary with columns, rows, rowcount, and metrics
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.time()
        attempt = 0
        last_error = None

        while attempt < self.config.max_retries if retry else 1:
            try:
                async with self._pool.acquire() as conn:
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
                    # Record error metrics
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

        # Should never reach here
        raise QueryError(
            f"Query execution failed: {last_error}",
            error_code="QUERY_FAILED",
            original_error=last_error
        )

    async def health_check(self) -> HealthCheckResult:
        """
        Perform health check on the database connection

        Returns:
            HealthCheckResult with status and metrics
        """
        if not self._initialized:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                response_time=0.0,
                error="Client not initialized"
            )

        start_time = time.time()

        try:
            ping_query = await self._get_ping_query()
            await self.execute(ping_query, retry=False)

            response_time = time.time() - start_time

            # Check response time thresholds
            if response_time > 5.0:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY

            pool_stats = self._pool.stats if self._pool else {}

            return HealthCheckResult(
                status=status,
                response_time=response_time,
                details={
                    'pool': pool_stats,
                    'query_count': self._query_count,
                    'error_count': self._error_count,
                    'avg_execution_time': self._get_avg_execution_time(),
                }
            )

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Health check failed: {e}")

            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                error=str(e)
            )

    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for transaction management (ACID compliance)

        Usage:
            async with client.transaction() as tx:
                await client.execute("INSERT ...")
                await client.execute("UPDATE ...")
                # Commit on success, rollback on exception
        """
        if not self._initialized:
            await self.initialize()

        async with self._pool.acquire() as conn:
            try:
                # Begin transaction
                await self._begin_transaction(conn)

                yield conn

                # Commit transaction
                await self._commit_transaction(conn)

            except Exception as e:
                # Rollback transaction
                try:
                    await self._rollback_transaction(conn)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

                raise TransactionError(
                    f"Transaction failed: {e}",
                    error_code="TRANSACTION_FAILED",
                    original_error=e
                )

    async def _begin_transaction(self, connection: Any) -> None:
        """Begin a transaction (implementation-specific)"""
        # Default implementation - override if needed
        pass

    async def _commit_transaction(self, connection: Any) -> None:
        """Commit a transaction (implementation-specific)"""
        # Default implementation - override if needed
        pass

    async def _rollback_transaction(self, connection: Any) -> None:
        """Rollback a transaction (implementation-specific)"""
        # Default implementation - override if needed
        pass

    def _record_metrics(
        self,
        query: str,
        execution_time: float,
        rows_affected: int,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Record query execution metrics"""
        self._query_count += 1
        if not success:
            self._error_count += 1
        else:
            self._total_execution_time += execution_time

        metrics = QueryMetrics(
            query=query[:100],  # Truncate long queries
            execution_time=execution_time,
            rows_affected=rows_affected,
            timestamp=datetime.utcnow(),
            success=success,
            error=error,
            query_type=self._get_query_type(query)
        )

        self._last_query_metrics.append(metrics)

        # Keep only last N metrics
        if len(self._last_query_metrics) > self._max_metrics:
            self._last_query_metrics.pop(0)

    def _get_avg_execution_time(self) -> float:
        """Get average query execution time"""
        if self._query_count == 0:
            return 0.0
        return self._total_execution_time / max(1, self._query_count - self._error_count)

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
        elif query_upper.startswith(('BEGIN', 'COMMIT', 'ROLLBACK')):
            return 'TRANSACTION'
        else:
            return 'OTHER'

    @property
    def metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        return {
            'query_count': self._query_count,
            'error_count': self._error_count,
            'error_rate': self._error_count / max(1, self._query_count),
            'avg_execution_time': self._get_avg_execution_time(),
            'pool_stats': self._pool.stats if self._pool else {},
            'recent_queries': self._last_query_metrics[-10:],  # Last 10 queries
        }
