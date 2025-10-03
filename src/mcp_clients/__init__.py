"""
MCP Client Integration Module

Provides database client implementations for Oracle and PostgreSQL
with MCP protocol compliance and connection management.
"""

from .base import MCPClient, MCPClientError, ConnectionState
from .oracle_client import OracleClient
from .postgresql_client import PostgreSQLClient
from .manager import ConnectionManager

__all__ = [
    'MCPClient',
    'MCPClientError',
    'ConnectionState',
    'OracleClient',
    'PostgreSQLClient',
    'ConnectionManager',
]

__version__ = '1.0.0'
