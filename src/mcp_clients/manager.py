"""
Connection Manager for Multiple Database Clients

Manages multiple database connections with pooling and lifecycle management.
"""

import asyncio
from typing import Dict, Optional, List, Type, Any
from dataclasses import dataclass
from datetime import datetime
from .base import BaseMCPClient, ConnectionConfig, MCPClientError, ConnectionState
from .oracle_client import OracleClient
from .postgresql_client import PostgreSQLClient
from .mysql_client import MySQLClient


@dataclass
class ConnectionInfo:
    """Connection information metadata"""
    connection_id: str
    client_type: str
    config: ConnectionConfig
    client: BaseMCPClient
    created_at: datetime
    last_used: datetime
    use_count: int


class ConnectionManager:
    """
    Manages multiple database connections with pooling

    Provides centralized connection lifecycle management,
    pooling, and health monitoring.
    """

    # Registry of available client types
    CLIENT_REGISTRY: Dict[str, Type[BaseMCPClient]] = {
        'oracle': OracleClient,
        'postgresql': PostgreSQLClient,
        'mysql': MySQLClient,
    }

    def __init__(self, max_connections: int = 10) -> None:
        self._connections: Dict[str, ConnectionInfo] = {}
        self._max_connections = max_connections
        self._lock = asyncio.Lock()

    async def create_connection(
        self,
        connection_id: str,
        client_type: str,
        config: ConnectionConfig
    ) -> str:
        """
        Create and register a new database connection

        Args:
            connection_id: Unique identifier for connection
            client_type: Type of client ('oracle', 'postgresql', 'mysql')
            config: Connection configuration

        Returns:
            Connection ID

        Raises:
            MCPClientError: If connection creation fails
        """
        async with self._lock:
            # Check if connection already exists
            if connection_id in self._connections:
                raise MCPClientError(
                    f"Connection '{connection_id}' already exists",
                    "CONNECTION_EXISTS"
                )

            # Check connection limit
            if len(self._connections) >= self._max_connections:
                raise MCPClientError(
                    f"Maximum connections ({self._max_connections}) reached",
                    "MAX_CONNECTIONS"
                )

            # Get client class
            client_class = self.CLIENT_REGISTRY.get(client_type.lower())
            if not client_class:
                raise MCPClientError(
                    f"Unknown client type: {client_type}",
                    "UNKNOWN_CLIENT_TYPE"
                )

            # Create and connect client
            client = client_class()
            await client.connect(config)

            # Register connection
            now = datetime.utcnow()
            self._connections[connection_id] = ConnectionInfo(
                connection_id=connection_id,
                client_type=client_type,
                config=config,
                client=client,
                created_at=now,
                last_used=now,
                use_count=0
            )

            return connection_id

    async def get_connection(self, connection_id: str) -> BaseMCPClient:
        """
        Get a connection by ID

        Args:
            connection_id: Connection identifier

        Returns:
            Database client

        Raises:
            MCPClientError: If connection not found
        """
        async with self._lock:
            conn_info = self._connections.get(connection_id)
            if not conn_info:
                raise MCPClientError(
                    f"Connection '{connection_id}' not found",
                    "CONNECTION_NOT_FOUND"
                )

            # Update usage info
            conn_info.last_used = datetime.utcnow()
            conn_info.use_count += 1

            return conn_info.client

    async def close_connection(self, connection_id: str) -> bool:
        """
        Close and remove a connection

        Args:
            connection_id: Connection identifier

        Returns:
            True if connection closed successfully
        """
        async with self._lock:
            conn_info = self._connections.get(connection_id)
            if not conn_info:
                return False

            # Disconnect client
            await conn_info.client.disconnect()

            # Remove from registry
            del self._connections[connection_id]

            return True

    async def close_all(self) -> int:
        """
        Close all connections

        Returns:
            Number of connections closed
        """
        async with self._lock:
            count = 0
            for conn_info in list(self._connections.values()):
                try:
                    await conn_info.client.disconnect()
                    count += 1
                except Exception:
                    pass

            self._connections.clear()
            return count

    def list_connections(self) -> List[Dict[str, Any]]:
        """
        List all active connections

        Returns:
            List of connection information dictionaries
        """
        return [
            {
                'connection_id': info.connection_id,
                'client_type': info.client_type,
                'state': info.client.state.value,
                'database': info.config.database,
                'host': info.config.host,
                'created_at': info.created_at.isoformat(),
                'last_used': info.last_used.isoformat(),
                'use_count': info.use_count
            }
            for info in self._connections.values()
        ]

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health check on all connections

        Returns:
            Dictionary mapping connection_id to health status
        """
        health_status = {}

        for conn_id, conn_info in self._connections.items():
            try:
                health = await conn_info.client.health_check()
                health_status[conn_id] = health
            except Exception as e:
                health_status[conn_id] = {
                    'state': 'error',
                    'error': str(e)
                }

        return health_status

    async def reconnect(self, connection_id: str) -> bool:
        """
        Reconnect a disconnected connection

        Args:
            connection_id: Connection identifier

        Returns:
            True if reconnection successful

        Raises:
            MCPClientError: If reconnection fails
        """
        async with self._lock:
            conn_info = self._connections.get(connection_id)
            if not conn_info:
                raise MCPClientError(
                    f"Connection '{connection_id}' not found",
                    "CONNECTION_NOT_FOUND"
                )

            # Disconnect if currently connected
            if conn_info.client.is_connected:
                await conn_info.client.disconnect()

            # Reconnect
            await conn_info.client.connect(conn_info.config)
            conn_info.last_used = datetime.utcnow()

            return True

    def get_connection_count(self) -> int:
        """Get total number of connections"""
        return len(self._connections)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get manager statistics

        Returns:
            Statistics dictionary
        """
        total = len(self._connections)
        by_type: Dict[str, int] = {}
        by_state: Dict[str, int] = {}

        for conn_info in self._connections.values():
            # Count by type
            client_type = conn_info.client_type
            by_type[client_type] = by_type.get(client_type, 0) + 1

            # Count by state
            state = conn_info.client.state.value
            by_state[state] = by_state.get(state, 0) + 1

        return {
            'total_connections': total,
            'max_connections': self._max_connections,
            'utilization': total / self._max_connections if self._max_connections > 0 else 0,
            'by_type': by_type,
            'by_state': by_state
        }
