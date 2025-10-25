"""
MCP Client Integration Module

Provides database client implementations for Oracle, PostgreSQL,
MongoDB, and Redis with MCP protocol compliance and connection management.
"""

from .base import MCPClient, MCPClientError, ConnectionState
from .oracle_client import OracleClient
from .postgresql_client import PostgreSQLClient
from .mysql_client import MySQLClient
from .mongodb_client import MongoDBClient
from .redis_client import RedisClient
from .manager import ConnectionManager

__all__ = [
    'MCPClient',
    'MCPClientError',
    'ConnectionState',
    'OracleClient',
    'PostgreSQLClient',
    'MySQLClient',
    'MongoDBClient',
    'RedisClient',
    'ConnectionManager',
]

__version__ = '1.1.0'
