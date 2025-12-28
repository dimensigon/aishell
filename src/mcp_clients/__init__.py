"""
MCP Client Integration Module

Provides database client implementations with 100% feature coverage:
- PostgreSQL (with LISTEN/NOTIFY, COPY, savepoints, full-text search)
- MySQL (with prepared statements, stored procedures, multiple result sets)
- MongoDB (with change streams, transactions, GridFS)
- Redis (with Streams, Lua scripts, pub/sub)
- SQLite (with WAL mode, backups, analyze)
- Oracle, Neo4j, Cassandra, DynamoDB

All clients include:
- Retry logic with exponential backoff
- Connection health monitoring
- Automatic reconnection
- Connection pooling
- Docker integration support
"""

from .base import MCPClient, MCPClientError, ConnectionState, ConnectionConfig, QueryResult
from .oracle_client import OracleClient
from .postgresql_client import PostgreSQLClient
from .postgresql_enhanced import PostgreSQLEnhancedClient
from .mysql_client import MySQLClient
from .mysql_enhanced import MySQLEnhancedClient
from .mongodb_client import MongoDBClient
from .mongodb_enhanced import MongoDBEnhancedClient
from .redis_client import RedisClient
from .redis_enhanced import RedisEnhancedClient
from .sqlite_client import SQLiteClient
from .neo4j_client import Neo4jClient
from .cassandra_client import CassandraClient
from .dynamodb_client import DynamoDBClient
from .manager import ConnectionManager
from .enhanced_manager import EnhancedConnectionManager
from .docker_integration import DockerIntegrationHelper

__all__ = [
    # Base classes
    'MCPClient',
    'MCPClientError',
    'ConnectionState',
    'ConnectionConfig',
    'QueryResult',
    # Basic clients
    'OracleClient',
    'PostgreSQLClient',
    'MySQLClient',
    'MongoDBClient',
    'RedisClient',
    'SQLiteClient',
    'Neo4jClient',
    'CassandraClient',
    'DynamoDBClient',
    # Enhanced clients
    'PostgreSQLEnhancedClient',
    'MySQLEnhancedClient',
    'MongoDBEnhancedClient',
    'RedisEnhancedClient',
    # Managers
    'ConnectionManager',
    'EnhancedConnectionManager',
    # Docker integration
    'DockerIntegrationHelper',
]

__version__ = '2.0.0'  # Major version bump for 100% feature completeness
