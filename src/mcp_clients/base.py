"""
Base MCP Client Protocol and Implementation

Defines the protocol interface and base functionality for all MCP clients.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass
import asyncio
from datetime import datetime


class ConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    CLOSED = "closed"


class MCPClientError(Exception):
    """Base exception for MCP client errors"""
    def __init__(self, message: str, error_code: Optional[str] = None) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


@dataclass
class QueryResult:
    """Structured query result"""
    columns: List[str]
    rows: List[tuple]
    rowcount: int
    execution_time: float
    metadata: Dict[str, Any]


@dataclass
class ConnectionConfig:
    """Connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    extra_params: Optional[Dict[str, Any]] = None


class MCPClient(Protocol):
    """
    MCP Client Protocol Interface

    All database clients must implement this protocol for MCP compliance.
    """

    @property
    def state(self) -> ConnectionState:
        """Get current connection state"""
        ...

    async def connect(self, config: ConnectionConfig) -> bool:
        """
        Establish database connection

        Args:
            config: Connection configuration

        Returns:
            True if connection successful

        Raises:
            MCPClientError: If connection fails
        """
        ...

    async def disconnect(self) -> bool:
        """
        Close database connection

        Returns:
            True if disconnection successful
        """
        ...

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        Execute a query and return results

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            QueryResult with columns, rows, and metadata

        Raises:
            MCPClientError: If query execution fails
        """
        ...

    async def execute_ddl(self, ddl: str) -> bool:
        """
        Execute DDL statement

        Args:
            ddl: DDL statement string

        Returns:
            True if execution successful

        Raises:
            MCPClientError: If DDL execution fails
        """
        ...

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform connection health check

        Returns:
            Health status dictionary
        """
        ...


class BaseMCPClient(ABC):
    """
    Abstract base class for MCP clients

    Provides common functionality for all database clients.
    """

    def __init__(self) -> None:
        self._state = ConnectionState.DISCONNECTED
        self._connection = None
        self._config: Optional[ConnectionConfig] = None
        self._last_error: Optional[str] = None
        self._connection_time: Optional[datetime] = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> ConnectionState:
        """Get current connection state"""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._state == ConnectionState.CONNECTED and self._connection is not None

    def _set_state(self, state: ConnectionState, error: Optional[str] = None):
        """Set connection state with optional error"""
        self._state = state
        if error:
            self._last_error = error

    async def connect(self, config: ConnectionConfig) -> bool:
        """
        Establish database connection with state management

        Args:
            config: Connection configuration

        Returns:
            True if connection successful

        Raises:
            MCPClientError: If connection fails
        """
        async with self._lock:
            try:
                self._set_state(ConnectionState.CONNECTING)
                self._config = config

                # Call implementation-specific connection
                self._connection = await self._connect_impl(config)

                self._connection_time = datetime.utcnow()
                self._set_state(ConnectionState.CONNECTED)
                return True

            except Exception as e:
                error_msg = f"Connection failed: {str(e)}"
                self._set_state(ConnectionState.ERROR, error_msg)
                raise MCPClientError(error_msg, "CONNECTION_FAILED") from e

    async def disconnect(self) -> bool:
        """
        Close database connection with state management

        Returns:
            True if disconnection successful
        """
        async with self._lock:
            try:
                if self._connection:
                    await self._disconnect_impl()
                    self._connection = None

                self._set_state(ConnectionState.CLOSED)
                return True

            except Exception as e:
                error_msg = f"Disconnection failed: {str(e)}"
                self._set_state(ConnectionState.ERROR, error_msg)
                return False

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        Execute query with error handling and timing

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            QueryResult with columns, rows, and metadata

        Raises:
            MCPClientError: If query execution fails
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        start_time = asyncio.get_event_loop().time()

        try:
            result = await self._execute_query_impl(query, params)
            execution_time = asyncio.get_event_loop().time() - start_time

            return QueryResult(
                columns=result['columns'],
                rows=result['rows'],
                rowcount=result['rowcount'],
                execution_time=execution_time,
                metadata=result.get('metadata', {})
            )

        except Exception as e:
            raise MCPClientError(f"Query execution failed: {str(e)}", "QUERY_FAILED") from e

    async def execute_ddl(self, ddl: str) -> bool:
        """
        Execute DDL statement

        Args:
            ddl: DDL statement string

        Returns:
            True if execution successful

        Raises:
            MCPClientError: If DDL execution fails
        """
        if not self.is_connected:
            raise MCPClientError("Not connected to database", "NOT_CONNECTED")

        try:
            await self._execute_ddl_impl(ddl)
            return True

        except Exception as e:
            raise MCPClientError(f"DDL execution failed: {str(e)}", "DDL_FAILED") from e

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform connection health check

        Returns:
            Health status dictionary
        """
        health = {
            'state': self._state.value,
            'connected': self.is_connected,
            'last_error': self._last_error,
            'connection_time': self._connection_time.isoformat() if self._connection_time else None
        }

        if self.is_connected:
            try:
                # Simple ping query
                result = await self.execute_query(self._get_ping_query())
                health['ping_successful'] = True
                health['ping_time'] = float(result.execution_time)
            except Exception as e:
                health['ping_successful'] = False
                health['ping_error'] = str(e)

        return health

    # Abstract methods to be implemented by subclasses

    @abstractmethod
    async def _connect_impl(self, config: ConnectionConfig) -> Any:
        """Implementation-specific connection logic"""
        pass

    @abstractmethod
    async def _disconnect_impl(self) -> None:
        """Implementation-specific disconnection logic"""
        pass

    @abstractmethod
    async def _execute_query_impl(self, query: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Implementation-specific query execution"""
        pass

    @abstractmethod
    async def _execute_ddl_impl(self, ddl: str) -> None:
        """Implementation-specific DDL execution"""
        pass

    @abstractmethod
    def _get_ping_query(self) -> str:
        """Get database-specific ping query"""
        pass
