# MCP Database Clients - 100% Feature Complete

Complete Python MCP client implementations for all major databases with Docker integration support.

## Overview

The MCP Clients module provides production-ready database connectivity with:

- **100% Feature Coverage** for all database-specific features
- **Retry Logic** with exponential backoff
- **Health Monitoring** with automatic reconnection
- **Connection Pooling** with configurable limits
- **Docker Integration** for seamless testing
- **Async/Await** support throughout
- **Type Safety** with full type hints

## Supported Databases

### 1. PostgreSQL

**Basic Client**: `PostgreSQLClient`
**Enhanced Client**: `PostgreSQLEnhancedClient`

#### Features

- ✅ Connection pooling
- ✅ Query execution with parameters
- ✅ DDL operations
- ✅ **LISTEN/NOTIFY** support
- ✅ **COPY operations** (from/to files)
- ✅ **Transaction savepoints**
- ✅ **Full-text search** with GIN indexes
- ✅ Table introspection
- ✅ Schema management
- ✅ Health checks with metrics

#### Example

```python
from src.mcp_clients import PostgreSQLEnhancedClient, ConnectionConfig

# Create client
client = PostgreSQLEnhancedClient()

# Configure retry behavior
client.configure_retry(max_retries=3, base_delay=0.1, max_delay=10.0)

# Connect
config = ConnectionConfig(
    host='localhost',
    port=5432,
    database='mydb',
    username='postgres',
    password='password'
)
await client.connect(config)

# Use LISTEN/NOTIFY
async def notification_handler(channel, payload):
    print(f"Received: {channel} - {payload}")

await client.listen('updates', notification_handler)
await client.notify('updates', 'New data available')

# Use COPY for bulk data
await client.copy_from_file('users', '/data/users.csv', columns=['id', 'name'])

# Full-text search
results = await client.fts_search('articles', 'content', 'python async', limit=10)

# Transaction with savepoints
await client.execute_query("BEGIN")
await client.savepoint('sp1')
await client.execute_query("INSERT INTO users VALUES (1, 'Alice')")
await client.rollback_to_savepoint('sp1')  # Undo if needed
await client.release_savepoint('sp1')
await client.execute_query("COMMIT")

# Get detailed health metrics
health = await client.health_check_detailed()
print(f"Database size: {health['database_size_bytes']} bytes")
print(f"Active connections: {health['active_connections']}")
```

### 2. MySQL

**Basic Client**: `MySQLClient`
**Enhanced Client**: `MySQLEnhancedClient`

#### Features

- ✅ Connection pooling with aiomysql
- ✅ Query execution
- ✅ **Prepared statements**
- ✅ **Stored procedures** (create, call, drop)
- ✅ **Multiple result sets**
- ✅ Transaction support with isolation levels
- ✅ Table introspection
- ✅ Schema management
- ✅ Health checks with server info

#### Example

```python
from src.mcp_clients import MySQLEnhancedClient, ConnectionConfig

client = MySQLEnhancedClient()
client.configure_retry(max_retries=3)

config = ConnectionConfig(
    host='localhost',
    port=3306,
    database='mydb',
    username='root',
    password='password'
)
await client.connect(config)

# Prepared statements
await client.prepare('insert_user', 'INSERT INTO users (id, name) VALUES (?, ?)')
await client.execute_prepared('insert_user', (1, 'Alice'))

# Call stored procedure
await client.create_procedure(
    'get_user_count',
    'OUT total INT',
    'SELECT COUNT(*) INTO total FROM users;'
)
results = await client.call_procedure('get_user_count')

# Execute multiple queries
results = await client.execute_multi("""
    SELECT * FROM users WHERE id = 1;
    SELECT * FROM orders WHERE user_id = 1;
""")

# Transaction with isolation level
await client.begin_transaction('REPEATABLE READ')
await client.execute_query("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
await client.execute_query("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
await client.commit()

# Server info
info = await client.get_server_info()
print(f"MySQL version: {info['version']}")
```

### 3. MongoDB

**Basic Client**: `MongoDBClient`
**Enhanced Client**: `MongoDBEnhancedClient`

#### Features

- ✅ CRUD operations
- ✅ Aggregation pipeline
- ✅ **Change streams** for real-time updates
- ✅ **Transactions** (multi-document ACID)
- ✅ **GridFS** for file storage
- ✅ Index management
- ✅ Collection statistics
- ✅ Health checks

#### Example

```python
from src.mcp_clients import MongoDBEnhancedClient, ConnectionConfig

client = MongoDBEnhancedClient()

config = ConnectionConfig(
    host='localhost',
    port=27017,
    database='mydb',
    username='admin',
    password='password'
)
await client.connect(config)

# Watch collection for changes
async for change in client.watch_collection('users'):
    print(f"Change: {change['operation_type']}")
    print(f"Document: {change['full_document']}")

# GridFS file storage
file_id = await client.gridfs_upload('document.pdf', pdf_bytes, metadata={'type': 'invoice'})
file_data = await client.gridfs_download(file_id)
files = await client.gridfs_list()
await client.gridfs_delete(file_id)

# Transactions
async def transfer_money(session):
    users = client._database['users']
    await users.update_one({'id': 1}, {'$inc': {'balance': -100}}, session=session)
    await users.update_one({'id': 2}, {'$inc': {'balance': 100}}, session=session)

await client.with_transaction(transfer_money)

# Health check
health = await client.health_check_detailed()
print(f"MongoDB version: {health['server_version']}")
```

### 4. Redis

**Basic Client**: `RedisClient`
**Enhanced Client**: `RedisEnhancedClient`

#### Features

- ✅ Basic operations (get, set, delete, etc.)
- ✅ Hashes, Lists, Sets, Sorted Sets
- ✅ Pub/Sub messaging
- ✅ **Redis Streams** with consumer groups
- ✅ **Lua scripts** (register and execute)
- ✅ **Pipeline** for batching
- ✅ Session management
- ✅ Memory-efficient scanning
- ✅ Health checks with INFO

#### Example

```python
from src.mcp_clients import RedisEnhancedClient, ConnectionConfig

client = RedisEnhancedClient()

config = ConnectionConfig(
    host='localhost',
    port=6379,
    database='0',
    username='',
    password='password'
)
await client.connect(config)

# Redis Streams
message_id = await client.xadd('events', {'type': 'user_login', 'user_id': '123'})
messages = await client.xread({'events': '0'}, count=10)

# Consumer groups
await client.xgroup_create('events', 'processors', id='0')
messages = await client.xreadgroup('processors', 'worker1', {'events': '>'})

# Lua scripts
script = """
local key = KEYS[1]
local increment = ARGV[1]
redis.call('INCR', key)
return redis.call('GET', key)
"""
await client.register_script('increment_and_get', script)
result = await client.execute_script('increment_and_get', keys=['counter'], args=[1])

# Pipeline for batching
commands = [
    ('set', ('key1', 'value1'), {}),
    ('set', ('key2', 'value2'), {}),
    ('get', ('key1',), {}),
]
results = await client.execute_pipeline(commands)

# Memory usage
usage = await client.get_memory_usage('large_key')
print(f"Key uses {usage} bytes")
```

### 5. SQLite

**Client**: `SQLiteClient`

#### Features

- ✅ File-based database
- ✅ **WAL mode** for better concurrency
- ✅ **VACUUM** optimization
- ✅ **ANALYZE** for query optimization
- ✅ **Backup** functionality
- ✅ **Attach/Detach** databases
- ✅ **Checkpoint** WAL
- ✅ Database statistics
- ✅ Index management

#### Example

```python
from src.mcp_clients import SQLiteClient, ConnectionConfig

client = SQLiteClient()

config = ConnectionConfig(
    host='/path/to/database.db',  # File path
    port=0,
    database='sqlite',
    username='',
    password='',
    extra_params={
        'synchronous': 'NORMAL',
        'cache_size': -32000  # 32MB
    }
)
await client.connect(config)

# Optimize database
await client.vacuum()
await client.analyze('users')

# Backup
await client.backup('/path/to/backup.db')

# Checkpoint WAL
stats = await client.checkpoint()
print(f"Checkpointed {stats['checkpointed_frames']} frames")

# Database statistics
stats = await client.get_database_stats()
print(f"Database: {stats['file_size_mb']:.2f} MB")
print(f"Tables: {stats['table_count']}")
print(f"Journal mode: {stats['journal_mode']}")

# Attach another database
await client.attach_database('/path/to/other.db', 'other_db')
await client.execute_query("SELECT * FROM other_db.users")
await client.detach_database('other_db')
```

## Connection Manager

The `EnhancedConnectionManager` provides centralized connection management with health monitoring and auto-reconnection.

### Features

- ✅ Connection pooling with limits
- ✅ Health monitoring (background task)
- ✅ Automatic reconnection
- ✅ Connection statistics
- ✅ Pool resizing
- ✅ Multi-protocol support

### Example

```python
from src.mcp_clients import EnhancedConnectionManager, ConnectionConfig

# Create manager
manager = EnhancedConnectionManager(
    max_connections=20,
    health_check_interval=60,  # seconds
    auto_reconnect=True
)

# Create connections
pg_config = ConnectionConfig(
    host='localhost',
    port=5432,
    database='mydb',
    username='postgres',
    password='password'
)
await manager.create_connection('pg_main', 'postgresql', pg_config)

redis_config = ConnectionConfig(
    host='localhost',
    port=6379,
    database='0',
    username='',
    password='password'
)
await manager.create_connection('redis_cache', 'redis', redis_config)

# Start health monitoring
await manager.start_health_monitoring()

# Get connection
client = await manager.get_connection('pg_main')
result = await client.execute_query("SELECT * FROM users")

# Health status
health = await manager.get_all_connection_health()
for conn_id, status in health.items():
    print(f"{conn_id}: {'healthy' if status['connected'] else 'unhealthy'}")

# Pool statistics
stats = manager.get_pool_stats()
print(f"Utilization: {stats['utilization_percent']:.1f}%")

# Cleanup
await manager.stop_health_monitoring()
await manager.close_all()
```

## Docker Integration

The `DockerIntegrationHelper` provides utilities for testing with Docker containers.

### Features

- ✅ Wait for containers to be ready
- ✅ Generate connection configurations
- ✅ Health checks for containers
- ✅ Pre-configured database defaults

### Example

```python
from src.mcp_clients import DockerIntegrationHelper, ConnectionConfig

# Wait for database to be ready
await DockerIntegrationHelper.wait_for_database('postgresql', max_wait_time=30)

# Get connection configuration
config_dict = DockerIntegrationHelper.get_connection_config('postgresql')
config = ConnectionConfig(**config_dict)

# Get connection string
uri = DockerIntegrationHelper.get_connection_string('postgresql')
# postgresql://postgres:MyPostgresPass123@localhost:5432/postgres

# Check container health
health = await DockerIntegrationHelper.check_container_health('test_postgres')
print(f"Container status: {health['status']}")
```

## Testing

Comprehensive Docker-based integration tests are provided in `tests/integration/test_mcp_clients_docker.py`.

### Running Tests

```bash
# Start Docker containers
cd tests/integration/database
docker-compose up -d

# Wait for containers to be ready
sleep 30

# Run tests
pytest tests/integration/test_mcp_clients_docker.py -v

# Cleanup
docker-compose down -v
```

### Test Coverage

- ✅ Connection establishment and disconnection
- ✅ Retry logic with exponential backoff
- ✅ Health checks (basic and detailed)
- ✅ Advanced features for each database
- ✅ Connection pooling and limits
- ✅ Health monitoring with auto-reconnect
- ✅ Multi-database scenarios

## Error Handling

All clients implement consistent error handling:

```python
from src.mcp_clients import MCPClientError

try:
    await client.execute_query("SELECT * FROM users")
except MCPClientError as e:
    print(f"Error code: {e.error_code}")
    print(f"Message: {e.message}")

    if e.error_code == 'CONNECTION_FAILED':
        # Handle connection error
        await client.reconnect()
    elif e.error_code == 'QUERY_FAILED':
        # Handle query error
        pass
```

### Error Codes

- `CONNECTION_FAILED`: Connection establishment failed
- `NOT_CONNECTED`: Operation attempted without active connection
- `QUERY_FAILED`: Query execution failed
- `DDL_FAILED`: DDL operation failed
- `RETRY_EXHAUSTED`: All retry attempts failed
- `TIMEOUT`: Operation timed out
- `INVALID_OPERATION`: Unsupported operation

## Best Practices

### 1. Use Enhanced Clients

Always use enhanced clients for production:

```python
# Good
from src.mcp_clients import PostgreSQLEnhancedClient
client = PostgreSQLEnhancedClient()

# Basic client is fine for simple cases
from src.mcp_clients import PostgreSQLClient
client = PostgreSQLClient()
```

### 2. Configure Retry Logic

```python
client.configure_retry(
    max_retries=3,
    base_delay=0.1,  # Start with 100ms
    max_delay=10.0,  # Cap at 10 seconds
    exponential_base=2
)
```

### 3. Monitor Health

```python
# Enable automatic health monitoring
manager = EnhancedConnectionManager(
    health_check_interval=60,
    auto_reconnect=True
)
await manager.start_health_monitoring()
```

### 4. Use Connection Pooling

```python
# Create pool for high-throughput scenarios
manager = EnhancedConnectionManager(max_connections=50)
```

### 5. Cleanup Resources

```python
try:
    # Your code
    await client.execute_query("SELECT * FROM users")
finally:
    # Always cleanup
    await client.disconnect()
```

## Performance Tips

1. **Connection Reuse**: Keep connections alive and reuse them
2. **Pooling**: Use connection manager for multiple concurrent operations
3. **Prepared Statements**: Use for repeated queries (PostgreSQL, MySQL)
4. **Batch Operations**: Use COPY (PostgreSQL) or bulk inserts
5. **WAL Mode**: Enable for SQLite concurrent access
6. **Pipeline**: Batch Redis commands for better performance

## Architecture

```
MCP Clients
├── Base Layer (base.py)
│   ├── MCPClient Protocol
│   ├── BaseMCPClient
│   └── Error Types
│
├── Database Clients
│   ├── PostgreSQL (basic + enhanced)
│   ├── MySQL (basic + enhanced)
│   ├── MongoDB (basic + enhanced)
│   ├── Redis (basic + enhanced)
│   ├── SQLite
│   ├── Oracle
│   ├── Neo4j
│   ├── Cassandra
│   └── DynamoDB
│
├── Connection Management
│   ├── ConnectionManager (basic)
│   └── EnhancedConnectionManager (with health monitoring)
│
└── Docker Integration
    └── DockerIntegrationHelper
```

## Requirements

```txt
# PostgreSQL
psycopg2-binary>=2.9.0

# MySQL
aiomysql>=0.1.1

# MongoDB
motor>=3.3.0
pymongo>=4.5.0

# Redis
redis[asyncio]>=5.0.0

# SQLite
aiosqlite>=0.19.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

## Version History

### v2.0.0 (Current)
- 100% feature completeness for all databases
- Enhanced clients with retry logic
- Health monitoring and auto-reconnection
- Docker integration helper
- Comprehensive test suite
- Full documentation

### v1.1.0
- Basic clients for PostgreSQL, MySQL, MongoDB, Redis
- Connection manager
- Basic health checks

### v1.0.0
- Initial release with Oracle client

## Support

For issues, questions, or contributions, please refer to the main AI-Shell documentation or open an issue on GitHub.

## License

Part of the AI-Shell project. See main project license.
