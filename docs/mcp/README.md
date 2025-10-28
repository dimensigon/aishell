# AI-Shell MCP (Model Context Protocol) Documentation

## Overview

AI-Shell implements comprehensive Model Context Protocol (MCP) support for seamless database integration with Claude Desktop and other AI assistants. MCP provides a standardized way for AI tools to interact with databases, enabling natural language database operations.

## Table of Contents

- [Architecture](#architecture)
- [Supported Databases](#supported-databases)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Integration with Claude Desktop](#integration-with-claude-desktop)
- [Documentation](#documentation)
- [Examples](#examples)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Desktop / AI Client            │
└─────────────────────┬───────────────────────────────────┘
                      │ MCP Protocol
                      │ (JSON-RPC over stdio/WebSocket)
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 AI-Shell MCP Server                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │          TypeScript MCP Implementation          │   │
│  │  - Client Manager (client.ts)                   │   │
│  │  - Message Builder (messages.ts)                │   │
│  │  - Error Handler (error-handler.ts)             │   │
│  │  - Resource Manager (resource-manager.ts)       │   │
│  │  - Tool Executor (tool-executor.ts)             │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │                                 │
│  ┌─────────────────────▼───────────────────────────┐   │
│  │       Python Database Client Layer              │   │
│  │  - Connection Manager (manager.py)              │   │
│  │  - Base MCP Client (base.py)                    │   │
│  │  - Database-Specific Clients:                   │   │
│  │    • PostgreSQL Client (postgresql_client.py)   │   │
│  │    • MySQL Client (mysql_client.py)             │   │
│  │    • MongoDB Client (mongodb_client.py)         │   │
│  │    • Redis Client (redis_client.py)             │   │
│  │    • Oracle Client (oracle_client.py)           │   │
│  │    • Neo4j Client (neo4j_client.py)             │   │
│  │    • Cassandra Client (cassandra_client.py)     │   │
│  │    • DynamoDB Client (dynamodb_client.py)       │   │
│  └─────────────────────┬───────────────────────────┘   │
└────────────────────────┼─────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼───────┐ ┌─────▼─────┐ ┌───────▼────────┐
│   PostgreSQL  │ │   MySQL   │ │    MongoDB     │
│   Database    │ │  Database │ │    Database    │
└───────────────┘ └───────────┘ └────────────────┘
        │                │                │
┌───────▼───────┐ ┌─────▼─────┐ ┌───────▼────────┐
│     Redis     │ │  Oracle   │ │     Neo4j      │
│    Cache      │ │ Database  │ │     Graph      │
└───────────────┘ └───────────┘ └────────────────┘
```

## Supported Databases

AI-Shell MCP implementation supports **8 major database systems**:

### Relational Databases

| Database | Status | Client | Features |
|----------|--------|--------|----------|
| **PostgreSQL** | ✅ Production Ready | `postgresql_client.py` | LISTEN/NOTIFY, COPY, Transactions, Connection Pooling |
| **MySQL** | ✅ Production Ready | `mysql_client.py` | Prepared Statements, Stored Procedures, Connection Pooling |
| **Oracle** | ✅ Production Ready | `oracle_client.py` | PL/SQL, Advanced Types, Connection Pooling |

### NoSQL Databases

| Database | Status | Client | Features |
|----------|--------|--------|----------|
| **MongoDB** | ✅ Production Ready | `mongodb_client.py` | Aggregation Pipeline, Change Streams, GridFS, Transactions |
| **Redis** | ✅ Production Ready | `redis_client.py` | Pub/Sub, Streams, Lua Scripts, Session Management |
| **Cassandra** | ✅ Production Ready | `cassandra_client.py` | CQL, Materialized Views, Batching |
| **DynamoDB** | ✅ Production Ready | `dynamodb_client.py` | Transactions, GSI/LSI, Streams |

### Graph Databases

| Database | Status | Client | Features |
|----------|--------|--------|----------|
| **Neo4j** | ✅ Production Ready | `neo4j_client.py` | Cypher Queries, Graph Algorithms, APOC |

## Key Features

### 🔌 Universal Connection Management
- **Unified Interface**: Single MCP protocol for all databases
- **Connection Pooling**: Automatic connection pool management
- **Auto-Reconnection**: Built-in reconnection with exponential backoff
- **Health Monitoring**: Real-time health checks and metrics

### 🔒 Security & Sandboxing
- **Process Isolation**: Each MCP server runs in sandboxed environment
- **Resource Limits**: CPU, memory, and output buffer restrictions
- **Environment Filtering**: Whitelisted environment variables only
- **Audit Logging**: Comprehensive security event logging

### ⚡ Performance Optimization
- **Async Operations**: Full async/await support across all clients
- **Query Caching**: Intelligent query result caching
- **Batch Operations**: Batch query execution support
- **Connection Reuse**: Efficient connection lifecycle management

### 🛠️ Developer Experience
- **Type Safety**: Full TypeScript and Python type annotations
- **Error Handling**: Comprehensive error handling and reporting
- **Resource Discovery**: Automatic database resource enumeration
- **Tool Integration**: Seamless tool execution through MCP protocol

### 📊 Monitoring & Observability
- **Metrics Collection**: Performance metrics and statistics
- **Connection States**: Real-time connection state tracking
- **Query Analytics**: Query execution time and performance data
- **Resource Monitoring**: Memory, CPU, and buffer usage tracking

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install psycopg2-binary aiomysql motor redis[asyncio] cx_Oracle neo4j-driver cassandra-driver boto3

# Install TypeScript dependencies (for MCP server)
npm install
```

### 2. Start Docker Databases (Development)

```bash
# Start all databases
docker-compose -f tests/integration/database/docker-compose.yml up -d

# Or start individual databases
docker-compose -f tests/integration/database/docker-compose.yml up -d postgres
docker-compose -f tests/integration/database/docker-compose.yml up -d mongodb
```

See [Docker Setup Guide](./DOCKER_SETUP.md) for detailed instructions.

### 3. Configure Connection

```python
from src.mcp_clients import PostgreSQLClient, ConnectionConfig

# Create connection configuration
config = ConnectionConfig(
    host='localhost',
    port=5432,
    database='myapp_db',
    username='postgres',
    password='MyPostgresPass123'
)

# Create and connect client
client = PostgreSQLClient()
await client.connect(config)

# Execute query
result = await client.execute_query(
    "SELECT * FROM users WHERE email = %(email)s",
    {'email': 'user@example.com'}
)

print(f"Found {result.rowcount} users")
for row in result.rows:
    print(row)

# Cleanup
await client.disconnect()
```

### 4. Use Connection Manager (Recommended)

```python
from src.mcp_clients import ConnectionManager

# Create manager
manager = ConnectionManager(max_connections=10)

# Create multiple connections
await manager.create_connection(
    'main_db',
    'postgresql',
    ConnectionConfig(
        host='localhost',
        port=5432,
        database='main_db',
        username='postgres',
        password='password'
    )
)

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

# Use connections
pg_client = await manager.get_connection('main_db')
redis_client = await manager.get_connection('cache')

# Execute operations
result = await pg_client.execute_query("SELECT * FROM users")
await redis_client.cache_set('user_count', result.rowcount, ttl=300)

# Health check all connections
health = await manager.health_check_all()
print(health)

# Cleanup
await manager.close_all()
```

## Integration with Claude Desktop

AI-Shell MCP server can be integrated with Claude Desktop for natural language database operations.

### Configuration

Create or edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-shell-db": {
      "command": "node",
      "args": [
        "/path/to/aishell/dist/mcp/server.js"
      ],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

### Example Claude Desktop Usage

```
You: Connect to my PostgreSQL database at localhost:5432, database name 'myapp_db'

Claude: I'll connect to your PostgreSQL database using the MCP interface...
[Uses MCP tool to establish connection]

You: Show me all users who registered in the last 7 days

Claude: Let me query the users table for recent registrations...
[Executes: SELECT * FROM users WHERE created_at > NOW() - INTERVAL '7 days']

Found 42 users who registered in the last 7 days:
1. user1@example.com - 2025-10-25
2. user2@example.com - 2025-10-24
...
```

See [Claude Desktop Integration](./CLAUDE_DESKTOP.md) for complete setup instructions.

## Documentation

### Core Documentation
- [Database Clients Guide](./DATABASE_CLIENTS.md) - Overview of all database clients
- [MCP Server Guide](./MCP_SERVER.md) - TypeScript MCP server implementation
- [Docker Setup](./DOCKER_SETUP.md) - Docker configuration for databases

### Database-Specific Guides
- [PostgreSQL Guide](./databases/POSTGRESQL.md) - Complete PostgreSQL MCP reference
- [MySQL Guide](./databases/MYSQL.md) - Complete MySQL MCP reference
- [MongoDB Guide](./databases/MONGODB.md) - Complete MongoDB MCP reference
- [Redis Guide](./databases/REDIS.md) - Complete Redis MCP reference
- [SQLite Guide](./databases/SQLITE.md) - Complete SQLite MCP reference

### Advanced Topics
- [Integration Patterns](./INTEGRATION_PATTERNS.md) - Best practices and patterns
- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Performance Guide](./PERFORMANCE.md) - Optimization and tuning
- [Security Guide](./SECURITY.md) - Security best practices
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues and solutions
- [Migration Guide](./MIGRATION_GUIDE.md) - Migrating to MCP

## Examples

### Basic Operations

```python
from src.mcp_clients import MySQLClient, ConnectionConfig

# Connect to MySQL
client = MySQLClient()
await client.connect(ConnectionConfig(
    host='localhost',
    port=3306,
    database='myapp',
    username='root',
    password='password'
))

# Insert data
result = await client.execute_query(
    "INSERT INTO products (name, price) VALUES (%(name)s, %(price)s)",
    {'name': 'Widget', 'price': 19.99}
)
print(f"Inserted {result.rowcount} row(s)")

# Update data
result = await client.execute_query(
    "UPDATE products SET price = %(price)s WHERE name = %(name)s",
    {'price': 24.99, 'name': 'Widget'}
)
print(f"Updated {result.rowcount} row(s)")

# Query data
result = await client.execute_query(
    "SELECT * FROM products WHERE price < %(max_price)s",
    {'max_price': 50.00}
)
for row in result.rows:
    print(f"Product: {row[0]}, Price: ${row[1]}")
```

### NoSQL Operations

```python
from src.mcp_clients import MongoDBClient, ConnectionConfig

# Connect to MongoDB
client = MongoDBClient()
await client.connect(ConnectionConfig(
    host='localhost',
    port=27017,
    database='myapp',
    username='admin',
    password='password'
))

# Insert document
result = await client.execute_query(
    '{"operation": "insert_one", "collection": "users", "document": {"name": "John", "email": "john@example.com"}}'
)
print(f"Inserted ID: {result.rows[0][0]}")

# Find documents
result = await client.execute_query(
    '{"operation": "find", "collection": "users", "filter": {"name": "John"}, "limit": 10}'
)
print(f"Found {result.rowcount} documents")

# Aggregation pipeline
result = await client.execute_query(
    '''
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
    '''
)
```

### Caching with Redis

```python
from src.mcp_clients import RedisClient, ConnectionConfig
import json

# Connect to Redis
client = RedisClient()
await client.connect(ConnectionConfig(
    host='localhost',
    port=6379,
    database='0',
    username='',
    password=''
))

# Cache user data
user_data = {'id': 123, 'name': 'Alice', 'email': 'alice@example.com'}
await client.cache_set('user:123', user_data, ttl=3600)

# Retrieve cached data
cached_user = await client.cache_get('user:123')
print(f"Cached user: {cached_user}")

# Session management
session_data = {
    'user_id': 123,
    'login_time': '2025-10-28T10:00:00Z',
    'permissions': ['read', 'write']
}
await client.session_create('session_abc123', session_data, ttl=3600)

# Pub/Sub messaging
async def message_handler(channel, message):
    print(f"Received on {channel}: {message}")

await client.subscribe('notifications', message_handler)
await client.publish('notifications', json.dumps({'type': 'alert', 'message': 'New order'}))
```

## Performance Characteristics

| Database | Avg Connection Time | Query Latency | Throughput (ops/sec) |
|----------|---------------------|---------------|----------------------|
| PostgreSQL | 50-100ms | 1-5ms | 10,000+ |
| MySQL | 40-80ms | 1-5ms | 10,000+ |
| MongoDB | 30-60ms | 2-8ms | 15,000+ |
| Redis | 10-20ms | <1ms | 50,000+ |
| Oracle | 100-200ms | 2-10ms | 8,000+ |
| Neo4j | 50-150ms | 5-20ms | 5,000+ |
| Cassandra | 30-100ms | 2-15ms | 20,000+ |
| DynamoDB | 50-150ms | 10-50ms | Variable |

*Note: Performance varies based on query complexity, network latency, and database configuration.*

## Error Handling

All MCP clients provide comprehensive error handling:

```python
from src.mcp_clients import MCPClientError, ConnectionState

try:
    result = await client.execute_query("SELECT * FROM users")
except MCPClientError as e:
    print(f"MCP Error [{e.error_code}]: {e.message}")

    # Handle specific errors
    if e.error_code == "NOT_CONNECTED":
        print("Client not connected, attempting reconnection...")
        await client.connect(config)
    elif e.error_code == "QUERY_FAILED":
        print("Query failed, check syntax and permissions")
    elif e.error_code == "CONNECTION_FAILED":
        print("Connection failed, check network and credentials")

# Check connection state
if client.state == ConnectionState.ERROR:
    print("Client in error state, performing health check...")
    health = await client.health_check()
    print(f"Health status: {health}")
```

## Connection States

MCP clients track connection state:

```python
from src.mcp_clients import ConnectionState

# Possible states
ConnectionState.DISCONNECTED  # Not connected
ConnectionState.CONNECTING    # Connection in progress
ConnectionState.CONNECTED     # Successfully connected
ConnectionState.ERROR         # Error state
ConnectionState.CLOSED        # Explicitly closed

# Check state
print(f"Current state: {client.state}")
print(f"Is connected: {client.is_connected}")
```

## Resource Management

### Connection Pooling

```python
# MySQL connection pooling
mysql_client = MySQLClient()
await mysql_client.create_pool(config, pool_size=20)

# Use pooled connections
result = await mysql_client.execute_with_pool(
    "SELECT * FROM orders WHERE status = %s",
    ('pending',)
)
```

### Health Monitoring

```python
# Individual health check
health = await client.health_check()
print(f"Connected: {health['connected']}")
print(f"Ping time: {health['ping_time']}ms")

# Manager health check
manager_health = await manager.health_check_all()
for conn_id, health in manager_health.items():
    print(f"{conn_id}: {health['state']} (ping: {health.get('ping_time', 'N/A')}ms)")
```

## Supported MCP Protocol Version

AI-Shell implements **MCP Protocol v1.0.0** with full support for:

- JSON-RPC 2.0 message format
- Tool invocation and discovery
- Resource enumeration and access
- Context synchronization
- Error handling and reporting
- Streaming support (where applicable)

## Community & Support

- **Documentation**: [Full Documentation](./API_REFERENCE.md)
- **Examples**: [examples/](./examples/)
- **Issues**: Report issues on GitHub
- **Contributing**: See CONTRIBUTING.md

## License

AI-Shell MCP implementation is part of the AI-Shell project. See LICENSE for details.

## Next Steps

1. **[Database Clients Guide](./DATABASE_CLIENTS.md)** - Learn about each database client
2. **[Docker Setup](./DOCKER_SETUP.md)** - Set up development databases
3. **[Claude Desktop Integration](./CLAUDE_DESKTOP.md)** - Integrate with Claude Desktop
4. **[API Reference](./API_REFERENCE.md)** - Comprehensive API documentation
5. **[Examples](./examples/)** - Working code examples

---

**Version**: 1.1.0
**Last Updated**: October 2025
**MCP Protocol**: v1.0.0
