"""
Database Client Manager

Manages multiple database clients with unified configuration and monitoring.
Provides centralized control for all database connections.
"""

import logging
from typing import Any, Dict, List, Optional
from enum import Enum

from .base import DatabaseConfig, HealthStatus
from .oracle_client import OracleClient, OraclePDBClient
from .postgresql_client import PostgreSQLClient
from .mysql_client import MySQLClient


logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types"""
    ORACLE = "oracle"
    ORACLE_PDB = "oracle_pdb"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class DatabaseClientManager:
    """
    Centralized manager for all database clients

    Provides:
    - Unified client registration and management
    - Health monitoring across all clients
    - Configuration management
    - Metrics aggregation
    """

    def __init__(self):
        self._clients: Dict[str, Any] = {}
        self._configs: Dict[str, DatabaseConfig] = {}
        logger.info("Initialized DatabaseClientManager")

    async def register_client(
        self,
        name: str,
        db_type: DatabaseType,
        config: DatabaseConfig,
        **kwargs
    ) -> None:
        """
        Register a new database client

        Args:
            name: Unique client identifier
            db_type: Type of database
            config: Database configuration
            **kwargs: Additional client-specific parameters
        """
        if name in self._clients:
            raise ValueError(f"Client '{name}' already registered")

        # Create appropriate client
        if db_type == DatabaseType.ORACLE:
            client = OracleClient(config, name, **kwargs)
        elif db_type == DatabaseType.ORACLE_PDB:
            client = OraclePDBClient(config, name, **kwargs)
        elif db_type == DatabaseType.POSTGRESQL:
            client = PostgreSQLClient(config, name)
        elif db_type == DatabaseType.MYSQL:
            client = MySQLClient(config, name)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        # Initialize client
        await client.initialize()

        self._clients[name] = client
        self._configs[name] = config

        logger.info(f"Registered {db_type.value} client '{name}'")

    async def unregister_client(self, name: str) -> None:
        """
        Unregister and close a database client

        Args:
            name: Client identifier
        """
        if name not in self._clients:
            raise ValueError(f"Client '{name}' not found")

        client = self._clients[name]
        await client.close()

        del self._clients[name]
        del self._configs[name]

        logger.info(f"Unregistered client '{name}'")

    def get_client(self, name: str) -> Any:
        """
        Get a registered client

        Args:
            name: Client identifier

        Returns:
            Database client instance
        """
        if name not in self._clients:
            raise ValueError(f"Client '{name}' not found")

        return self._clients[name]

    def list_clients(self) -> List[str]:
        """Get list of registered client names"""
        return list(self._clients.keys())

    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health check on all registered clients

        Returns:
            Dictionary with health status for each client
        """
        results = {}

        for name, client in self._clients.items():
            try:
                health_result = await client.health_check()
                results[name] = {
                    'status': health_result.status.value,
                    'response_time': health_result.response_time,
                    'details': health_result.details,
                    'error': health_result.error,
                }
            except Exception as e:
                logger.error(f"Health check failed for client '{name}': {e}")
                results[name] = {
                    'status': HealthStatus.UNHEALTHY.value,
                    'response_time': 0.0,
                    'error': str(e),
                }

        return results

    async def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get metrics from all registered clients

        Returns:
            Dictionary with metrics for each client
        """
        metrics = {}

        for name, client in self._clients.items():
            try:
                metrics[name] = client.metrics
            except Exception as e:
                logger.error(f"Failed to get metrics for client '{name}': {e}")
                metrics[name] = {'error': str(e)}

        return metrics

    async def close_all(self) -> None:
        """Close all registered clients"""
        for name in list(self._clients.keys()):
            try:
                await self.unregister_client(name)
            except Exception as e:
                logger.error(f"Error closing client '{name}': {e}")

        logger.info("Closed all database clients")

    async def execute_on_client(
        self,
        name: str,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> Dict[str, Any]:
        """
        Execute query on a specific client

        Args:
            name: Client identifier
            query: SQL query
            params: Query parameters
            retry: Enable retry logic

        Returns:
            Query results
        """
        client = self.get_client(name)
        return await client.execute(query, params, retry)

    def get_config(self, name: str) -> DatabaseConfig:
        """
        Get configuration for a client

        Args:
            name: Client identifier

        Returns:
            Database configuration
        """
        if name not in self._configs:
            raise ValueError(f"Client '{name}' not found")

        return self._configs[name]

    @property
    def client_count(self) -> int:
        """Get number of registered clients"""
        return len(self._clients)

    @property
    def summary(self) -> Dict[str, Any]:
        """Get summary of all clients"""
        return {
            'client_count': self.client_count,
            'clients': list(self._clients.keys()),
            'by_type': self._get_clients_by_type(),
        }

    def _get_clients_by_type(self) -> Dict[str, List[str]]:
        """Group clients by database type"""
        by_type: Dict[str, List[str]] = {}

        for name, client in self._clients.items():
            client_type = client.__class__.__name__
            if client_type not in by_type:
                by_type[client_type] = []
            by_type[client_type].append(name)

        return by_type


# Convenience function to create pre-configured clients from environment
async def create_clients_from_env() -> DatabaseClientManager:
    """
    Create database clients from environment variables

    Expected environment variables:
    - ORACLE_CDB_HOST, ORACLE_CDB_PORT, ORACLE_CDB_DATABASE, etc.
    - ORACLE_PDB_HOST, ORACLE_PDB_PORT, ORACLE_PDB_DATABASE, etc.
    - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE, etc.
    - MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, etc.
    """
    import os

    manager = DatabaseClientManager()

    # Oracle CDB
    if os.getenv('ORACLE_CDB_HOST'):
        config = DatabaseConfig(
            host=os.getenv('ORACLE_CDB_HOST', 'localhost'),
            port=int(os.getenv('ORACLE_CDB_PORT', '1521')),
            database=os.getenv('ORACLE_CDB_DATABASE', 'free'),
            user=os.getenv('ORACLE_CDB_USER', 'SYS'),
            password=os.getenv('ORACLE_CDB_PASSWORD', ''),
        )
        try:
            import cx_Oracle
            await manager.register_client(
                'oracle_cdb',
                DatabaseType.ORACLE,
                config,
                mode=cx_Oracle.SYSDBA
            )
        except Exception as e:
            logger.warning(f"Failed to register Oracle CDB client: {e}")

    # Oracle PDB
    if os.getenv('ORACLE_PDB_HOST'):
        config = DatabaseConfig(
            host=os.getenv('ORACLE_PDB_HOST', 'localhost'),
            port=int(os.getenv('ORACLE_PDB_PORT', '1521')),
            database=os.getenv('ORACLE_PDB_DATABASE', 'freepdb1'),
            user=os.getenv('ORACLE_PDB_USER', 'SYS'),
            password=os.getenv('ORACLE_PDB_PASSWORD', ''),
        )
        try:
            import cx_Oracle
            await manager.register_client(
                'oracle_pdb',
                DatabaseType.ORACLE_PDB,
                config,
                mode=cx_Oracle.SYSDBA
            )
        except Exception as e:
            logger.warning(f"Failed to register Oracle PDB client: {e}")

    # PostgreSQL
    if os.getenv('POSTGRES_HOST'):
        config = DatabaseConfig(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            database=os.getenv('POSTGRES_DATABASE', 'postgres'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', ''),
        )
        try:
            await manager.register_client(
                'postgresql',
                DatabaseType.POSTGRESQL,
                config
            )
        except Exception as e:
            logger.warning(f"Failed to register PostgreSQL client: {e}")

    # MySQL
    if os.getenv('MYSQL_HOST'):
        config = DatabaseConfig(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', '3307')),
            database=os.getenv('MYSQL_DATABASE', 'mysql'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
        )
        try:
            await manager.register_client(
                'mysql',
                DatabaseType.MYSQL,
                config
            )
        except Exception as e:
            logger.warning(f"Failed to register MySQL client: {e}")

    return manager
