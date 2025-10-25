"""
Database clients module for unified database connectivity.

Provides production-ready clients for Oracle, PostgreSQL, and MySQL with:
- Connection pooling
- Async/await support
- Comprehensive error handling
- Health checks and monitoring
- Query logging and metrics
- Transaction management (ACID compliance)
"""

from .base import (
    BaseDatabaseClient,
    DatabaseConfig,
    ConnectionPool,
    DatabaseError,
    ConnectionError,
    QueryError,
    TransactionError,
    HealthStatus,
    QueryMetrics,
)
from .oracle_client import OracleClient, OraclePDBClient
from .postgresql_client import PostgreSQLClient
from .mysql_client import MySQLClient
from .manager import DatabaseClientManager

__all__ = [
    # Base classes
    'BaseDatabaseClient',
    'DatabaseConfig',
    'ConnectionPool',
    'HealthStatus',
    'QueryMetrics',

    # Errors
    'DatabaseError',
    'ConnectionError',
    'QueryError',
    'TransactionError',

    # Clients
    'OracleClient',
    'OraclePDBClient',
    'PostgreSQLClient',
    'MySQLClient',

    # Manager
    'DatabaseClientManager',
]
