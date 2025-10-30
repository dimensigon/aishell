# Database Clients Guide

Complete overview of all MCP database clients in AI-Shell, including connection configuration, supported operations, and usage examples.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Base MCP Client](#base-mcp-client)
- [Connection Manager](#connection-manager)
- [PostgreSQL Client](#postgresql-client)
- [MySQL Client](#mysql-client)
- [MongoDB Client](#mongodb-client)
- [Redis Client](#redis-client)
- [Oracle Client](#oracle-client)
- [Neo4j Client](#neo4j-client)
- [Cassandra Client](#cassandra-client)
- [DynamoDB Client](#dynamodb-client)
- [Performance Comparison](#performance-comparison)
- [Best Practices](#best-practices)

## Architecture Overview

All database clients in AI-Shell implement the MCP (Model Context Protocol) interface, providing a consistent API across different database systems.

### Client Hierarchy

```
BaseMCPClient (base.py)
    ├── PostgreSQLClient (postgresql_client.py)
    ├── MySQLClient (mysql_client.py)
    ├── MongoDBClient (mongodb_client.py)
    ├── RedisClient (redis_client.py)
    ├── OracleClient (oracle_client.py)
    ├── Neo4jClient (neo4j_client.py)
    ├── CassandraClient (cassandra_client.py)
    └── DynamoDBClient (dynamodb_client.py)

ConnectionManager (manager.py)
    └── Manages lifecycle of multiple client instances
```

## Base MCP Client

All database clients inherit from `BaseMCPClient`, which provides core functionality:

### Core Interface

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseMCPClient(ABC):
    """Abstract base class for MCP clients"""

    async def connect(self, config: ConnectionConfig) -> bool:
        """Establish database connection"""
        pass

    async def disconnect(self) -> bool:
        """Close database connection"""
        pass

    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """Execute query and return results"""
        pass

    async def execute_ddl(self, ddl: str) -> bool:
        """Execute DDL statement"""
        pass

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        pass
```

### Connection States

```python
from enum import Enum

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    CLOSED = "closed"
```

### Common Data Structures

```python
from dataclasses import dataclass

@dataclass
class ConnectionConfig:
    """Connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    extra_params: Optional[Dict[str, Any]] = None

@dataclass
class QueryResult:
    """Structured query result"""
    columns: List[str]
    rows: List[tuple]
    rowcount: int
    execution_time: float
    metadata: Dict[str, Any]
```

## Connection Manager

The `ConnectionManager` class provides centralized management of multiple database connections.

### Features

- **Connection Pooling**: Manage up to N concurrent connections
- **Lifecycle Management**: Automatic creation, tracking, and cleanup
- **Health Monitoring**: Periodic health checks across all connections
- **Multi-Database**: Support multiple database types simultaneously

### Basic Usage

```python
from src.mcp_clients import ConnectionManager, ConnectionConfig

# Create manager with maximum 10 connections
manager = ConnectionManager(max_connections=10)

# Create PostgreSQL connection
await manager.create_connection(
    'app_db',
    'postgresql',
    ConnectionConfig(
        host='localhost',
        port=5432,
        database='myapp',
        username='postgres',
        password='password'
    )
)

# Create Redis cache connection
await manager.create_connection(
    'cache',
    'redis',
    ConnectionConfig(
        host='localhost',
        port=6379,
        database='0',
        username='',
        password=''
    )
)

# Get connection and use it
pg_client = await manager.get_connection('app_db')
result = await pg_client.execute_query("SELECT * FROM users")

# List all connections
connections = manager.list_connections()
for conn in connections:
    print(f"{conn['connection_id']}: {conn['client_type']} @ {conn['host']}")

# Health check all connections
health = await manager.health_check_all()

# Get statistics
stats = manager.get_stats()
print(f"Total connections: {stats['total_connections']}")
print(f"Utilization: {stats['utilization']:.1%}")

# Cleanup
await manager.close_all()
```

### Advanced Features

```python
# Reconnect specific connection
await manager.reconnect('app_db')

# Close specific connection
await manager.close_connection('cache')

# Get connection count
count = manager.get_connection_count()

# Get detailed stats by type and state
stats = manager.get_stats()
print(f"PostgreSQL connections: {stats['by_type'].get('postgresql', 0)}")
print(f"Connected: {stats['by_state'].get('connected', 0)}")
print(f"Error: {stats['by_state'].get('error', 0)}")
```

## PostgreSQL Client

### Connection

```python
from src.mcp_clients import PostgreSQLClient, ConnectionConfig

client = PostgreSQLClient()

config = ConnectionConfig(
    host='localhost',
    port=5432,
    database='myapp',
    username='postgres',
    password='MyPostgresPass123',
    extra_params={
        'sslmode': 'require',
        'connect_timeout': 10,
        'application_name': 'ai-shell'
    }
)

await client.connect(config)
```

### Supported Operations

- **CRUD Operations**: SELECT, INSERT, UPDATE, DELETE
- **Transactions**: BEGIN, COMMIT, ROLLBACK
- **LISTEN/NOTIFY**: PostgreSQL pub/sub
- **COPY**: Bulk data import/export
- **JSON Operations**: JSONB queries and manipulation
- **Full-Text Search**: ts_query, ts_vector
- **CTEs**: Common Table Expressions

### Example Operations

```python
# Basic query
result = await client.execute_query(
    "SELECT * FROM users WHERE email = %(email)s",
    {'email': 'user@example.com'}
)

# DDL operation
await client.execute_ddl("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        price DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Get table information
table_info = await client.get_table_info('products', schema='public')
print(f"Columns: {table_info['columns']}")

# List all tables
tables = await client.get_table_list('public')

# List schemas
schemas = await client.get_schemas()
```

**Performance**: Average query latency 1-5ms, 10,000+ ops/sec

See [PostgreSQL Guide](./databases/POSTGRESQL.md) for complete reference.

## MySQL Client

### Connection

```python
from src.mcp_clients import MySQLClient, ConnectionConfig

client = MySQLClient()

config = ConnectionConfig(
    host='localhost',
    port=3306,
    database='myapp',
    username='root',
    password='MyMySQLPass123',
    extra_params={
        'charset': 'utf8mb4',
        'connect_timeout': 10,
        'autocommit': False
    }
)

await client.connect(config)
```

### Supported Operations

- **CRUD Operations**: SELECT, INSERT, UPDATE, DELETE
- **Prepared Statements**: Parameterized queries
- **Stored Procedures**: CALL procedures
- **Transactions**: Transactional support
- **Multiple Result Sets**: Handling multiple queries
- **JSON Support**: JSON column operations
- **Full-Text Search**: MATCH AGAINST

### Connection Pooling

```python
# Create connection pool
await client.create_pool(config, pool_size=20)

# Execute with pool
result = await client.execute_with_pool(
    "SELECT * FROM orders WHERE status = %s",
    ('pending',)
)
```

### Example Operations

```python
# Insert with prepared statement
result = await client.execute_query(
    "INSERT INTO products (name, price) VALUES (%s, %s)",
    ('Widget', 19.99)
)

# Get table info
table_info = await client.get_table_info('products')

# List tables
tables = await client.get_table_list()

# List schemas (databases)
schemas = await client.get_schemas()
```

**Performance**: Average query latency 1-5ms, 10,000+ ops/sec

See [MySQL Guide](./databases/MYSQL.md) for complete reference.

## MongoDB Client

### Connection

```python
from src.mcp_clients import MongoDBClient, ConnectionConfig

client = MongoDBClient()

config = ConnectionConfig(
    host='localhost',
    port=27017,
    database='myapp',
    username='admin',
    password='MyMongoPass123',
    extra_params={
        'authSource': 'admin',
        'retryWrites': 'true',
        'w': 'majority'
    }
)

await client.connect(config)
```

### Supported Operations

- **CRUD**: find, insert_one, insert_many, update_one, update_many, delete_one, delete_many
- **Aggregation**: Complex aggregation pipelines
- **Change Streams**: Real-time data change monitoring
- **GridFS**: Large file storage
- **Transactions**: Multi-document ACID transactions
- **Index Management**: Create, list, drop indexes
- **Geospatial Queries**: Location-based queries

### Example Operations

```python
# Insert document
result = await client.execute_query('''
    {
        "operation": "insert_one",
        "collection": "users",
        "document": {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }
    }
''')

# Find documents
result = await client.execute_query('''
    {
        "operation": "find",
        "collection": "users",
        "filter": {"age": {"$gte": 18}},
        "projection": {"name": 1, "email": 1},
        "sort": [["name", 1]],
        "limit": 10
    }
''')

# Aggregation
result = await client.execute_query('''
    {
        "operation": "aggregate",
        "collection": "orders",
        "pipeline": [
            {"$match": {"status": "completed"}},
            {"$group": {"_id": "$customer_id", "total": {"$sum": "$amount"}}},
            {"$sort": {"total": -1}},
            {"$limit": 10}
        ]
    }
''')

# Index management
await client.create_index('users', [('email', 1)], unique=True)
indexes = await client.list_indexes('users')

# Collection stats
stats = await client.get_collection_stats('users')
print(f"Document count: {stats['count']}")
```

**Performance**: Average query latency 2-8ms, 15,000+ ops/sec

See [MongoDB Guide](./databases/MONGODB.md) for complete reference.

## Redis Client

### Connection

```python
from src.mcp_clients import RedisClient, ConnectionConfig

client = RedisClient()

config = ConnectionConfig(
    host='localhost',
    port=6379,
    database='0',  # Redis database number (0-15)
    username='',
    password='MyRedisPass123',
    extra_params={
        'decode_responses': True,
        'socket_connect_timeout': 5
    }
)

await client.connect(config)
```

### Supported Operations

- **String Operations**: GET, SET, INCR, DECR, APPEND
- **Hash Operations**: HGET, HSET, HGETALL, HDEL
- **List Operations**: LPUSH, RPUSH, LPOP, RPOP, LRANGE
- **Set Operations**: SADD, SREM, SMEMBERS, SINTER, SUNION
- **Sorted Set Operations**: ZADD, ZRANGE, ZREM, ZINCRBY
- **Pub/Sub**: PUBLISH, SUBSCRIBE, UNSUBSCRIBE
- **Streams**: XADD, XREAD, XGROUP
- **TTL Management**: EXPIRE, EXPIREAT, TTL, PERSIST

### High-Level API

```python
# Caching
await client.cache_set('user:123', {'name': 'Alice', 'email': 'alice@example.com'}, ttl=3600)
user = await client.cache_get('user:123')
await client.cache_delete('user:123')

# Session management
await client.session_create('session_abc', {'user_id': 123, 'role': 'admin'}, ttl=3600)
session = await client.session_get('session_abc')
await client.session_extend('session_abc', ttl=3600)
await client.session_delete('session_abc')

# Pub/Sub
async def message_handler(channel, message):
    print(f"Received: {message}")

await client.subscribe('notifications', message_handler)
await client.publish('notifications', 'New order received')
```

### Example Operations

```python
# String operations
await client.execute_query('{"command": "set", "key": "counter", "value": "0"}')
await client.execute_query('{"command": "incr", "key": "counter"}')
result = await client.execute_query('{"command": "get", "key": "counter"}')

# Hash operations
await client.execute_query('{"command": "hset", "key": "user:1", "field": "name", "value": "Alice"}')
result = await client.execute_query('{"command": "hgetall", "key": "user:1"}')

# List operations
await client.execute_query('{"command": "lpush", "key": "queue", "values": ["task1", "task2"]}')
result = await client.execute_query('{"command": "lrange", "key": "queue", "start": 0, "stop": -1}')
```

**Performance**: Average query latency <1ms, 50,000+ ops/sec

See [Redis Guide](./databases/REDIS.md) for complete reference.

## Oracle Client

### Connection

```python
from src.mcp_clients import OracleClient, ConnectionConfig

client = OracleClient()

config = ConnectionConfig(
    host='localhost',
    port=1521,
    database='ORCL',  # Service name or SID
    username='system',
    password='MyOraclePass123',
    extra_params={
        'threaded': True,
        'encoding': 'UTF-8'
    }
)

await client.connect(config)
```

### Supported Operations

- **SQL Queries**: Full SQL support
- **PL/SQL**: Procedures, functions, packages
- **Cursors**: REF cursors
- **LOB Operations**: BLOB, CLOB handling
- **Advanced Types**: Collections, objects, records
- **Connection Pooling**: Session pooling

**Performance**: Average query latency 2-10ms, 8,000+ ops/sec

## Neo4j Client

### Connection

```python
from src.mcp_clients import Neo4jClient, ConnectionConfig

client = Neo4jClient()

config = ConnectionConfig(
    host='bolt://localhost',
    port=7687,
    database='neo4j',
    username='neo4j',
    password='MyNeo4jPass123'
)

await client.connect(config)
```

### Supported Operations

- **Cypher Queries**: Full Cypher support
- **Graph Algorithms**: Shortest path, centrality, etc.
- **APOC Procedures**: Advanced graph operations
- **Transactions**: ACID transactions
- **Relationships**: Create, query, delete relationships

**Performance**: Average query latency 5-20ms, 5,000+ ops/sec

## Cassandra Client

### Connection

```python
from src.mcp_clients import CassandraClient, ConnectionConfig

client = CassandraClient()

config = ConnectionConfig(
    host='localhost',
    port=9042,
    database='mykeyspace',
    username='cassandra',
    password='MyCassandraPass123',
    extra_params={
        'protocol_version': 4
    }
)

await client.connect(config)
```

### Supported Operations

- **CQL Queries**: Cassandra Query Language
- **Batching**: Batch operations
- **Materialized Views**: Automatic view updates
- **User-Defined Types**: Custom data types
- **Lightweight Transactions**: IF NOT EXISTS

**Performance**: Average query latency 2-15ms, 20,000+ ops/sec

## DynamoDB Client

### Connection

```python
from src.mcp_clients import DynamoDBClient, ConnectionConfig

client = DynamoDBClient()

config = ConnectionConfig(
    host='localhost',  # For local development
    port=8000,
    database='us-east-1',  # Region
    username='',  # AWS access key
    password='',  # AWS secret key
    extra_params={
        'endpoint_url': 'http://localhost:8000'  # Local DynamoDB
    }
)

await client.connect(config)
```

### Supported Operations

- **Item Operations**: GetItem, PutItem, UpdateItem, DeleteItem
- **Query**: Key-based queries
- **Scan**: Table scans
- **BatchGet/BatchWrite**: Batch operations
- **Transactions**: TransactWriteItems, TransactGetItems
- **Streams**: Change data capture
- **GSI/LSI**: Global/Local secondary indexes

**Performance**: Average query latency 10-50ms, variable throughput

## Performance Comparison

### Connection Overhead

| Database | Initial Connect | Reconnect | Pool Overhead |
|----------|----------------|-----------|---------------|
| PostgreSQL | 50-100ms | 20-50ms | 5-10ms |
| MySQL | 40-80ms | 15-40ms | 5-10ms |
| MongoDB | 30-60ms | 10-30ms | 3-8ms |
| Redis | 10-20ms | 5-10ms | 1-3ms |
| Oracle | 100-200ms | 50-100ms | 10-20ms |
| Neo4j | 50-150ms | 20-80ms | 8-15ms |
| Cassandra | 30-100ms | 15-50ms | 5-12ms |
| DynamoDB | 50-150ms | 20-80ms | N/A |

### Query Performance

| Database | Simple Query | Complex Query | Bulk Insert (1000 rows) |
|----------|-------------|---------------|-------------------------|
| PostgreSQL | 1-3ms | 5-50ms | 100-500ms |
| MySQL | 1-3ms | 5-50ms | 100-500ms |
| MongoDB | 2-5ms | 10-100ms | 50-200ms |
| Redis | <1ms | 1-5ms | 10-50ms |
| Oracle | 2-5ms | 10-100ms | 200-1000ms |
| Neo4j | 5-15ms | 20-200ms | 500-2000ms |
| Cassandra | 2-8ms | 10-80ms | 50-300ms |
| DynamoDB | 10-30ms | 50-500ms | 200-1000ms |

## Best Practices

### Connection Management

1. **Use Connection Pooling**: Always use connection pools for production
2. **Limit Pool Size**: Don't exceed database max_connections
3. **Health Checks**: Implement periodic health checks
4. **Timeout Configuration**: Set appropriate connection and query timeouts
5. **Resource Cleanup**: Always close connections in finally blocks

```python
# Good practice
manager = ConnectionManager(max_connections=10)

try:
    await manager.create_connection('db', 'postgresql', config)
    client = await manager.get_connection('db')
    result = await client.execute_query("SELECT * FROM users")
finally:
    await manager.close_all()
```

### Error Handling

1. **Catch Specific Errors**: Handle different error types appropriately
2. **Retry Logic**: Implement exponential backoff for transient errors
3. **Circuit Breaker**: Prevent cascading failures
4. **Logging**: Log all database errors with context

```python
from src.mcp_clients import MCPClientError
import asyncio

async def query_with_retry(client, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.execute_query(query)
        except MCPClientError as e:
            if e.error_code == "CONNECTION_FAILED" and attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
```

### Security

1. **Never Hardcode Credentials**: Use environment variables or secret managers
2. **Use SSL/TLS**: Enable encryption for production connections
3. **Principle of Least Privilege**: Use minimal required permissions
4. **Connection String Sanitization**: Validate and sanitize connection strings

```python
import os

# Good practice
config = ConnectionConfig(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', 5432)),
    database=os.getenv('DB_NAME'),
    username=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    extra_params={'sslmode': 'require'}
)
```

### Performance Optimization

1. **Use Indexes**: Ensure queries use appropriate indexes
2. **Batch Operations**: Batch inserts/updates when possible
3. **Connection Reuse**: Reuse connections instead of reconnecting
4. **Query Optimization**: Use EXPLAIN to optimize queries
5. **Caching**: Cache frequently accessed data in Redis

```python
# Use Redis for caching
redis_client = await manager.get_connection('cache')
pg_client = await manager.get_connection('db')

# Check cache first
cached_result = await redis_client.cache_get('users:all')
if cached_result:
    return cached_result

# Query database and cache result
result = await pg_client.execute_query("SELECT * FROM users")
await redis_client.cache_set('users:all', result.rows, ttl=300)

return result.rows
```

### Database-Specific Tips

#### PostgreSQL
- Use EXPLAIN ANALYZE for query optimization
- Leverage JSONB for semi-structured data
- Use LISTEN/NOTIFY for real-time updates

#### MySQL
- Use connection pooling for high concurrency
- Enable query cache for read-heavy workloads
- Use prepared statements to prevent SQL injection

#### MongoDB
- Design schema for your query patterns
- Use indexes effectively
- Leverage aggregation pipeline for complex queries

#### Redis
- Use pipelining for multiple operations
- Choose appropriate data structures
- Set reasonable TTLs to manage memory

## Next Steps

- [PostgreSQL Guide](./databases/POSTGRESQL.md) - Detailed PostgreSQL documentation
- [MySQL Guide](./databases/MYSQL.md) - Detailed MySQL documentation
- [MongoDB Guide](./databases/MONGODB.md) - Detailed MongoDB documentation
- [Redis Guide](./databases/REDIS.md) - Detailed Redis documentation
- [API Reference](./API_REFERENCE.md) - Complete API documentation

---

**Version**: 1.0.0
**Last Updated**: October 2025
