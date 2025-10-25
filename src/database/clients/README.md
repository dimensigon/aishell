# Database Clients

Production-ready database clients for Oracle, PostgreSQL, and MySQL with comprehensive features.

## Features

### Core Features
- ✅ **Connection Pooling**: Min 5, max 20 connections with automatic management
- ✅ **Async/Await Support**: Native async operations for all databases
- ✅ **Error Handling**: Comprehensive error handling with automatic retry logic
- ✅ **Health Checks**: Real-time health monitoring and connection validation
- ✅ **Query Metrics**: Detailed query logging and performance tracking
- ✅ **Transaction Management**: Full ACID compliance with context managers
- ✅ **Security**: SQL injection prevention via prepared statements

### Database-Specific Features

#### Oracle
- CDB (Container Database) support
- PDB (Pluggable Database) support with switching
- SYSDBA/SYSOPER authentication modes
- Thread pool for sync operations
- CDB management operations

#### PostgreSQL
- Native asyncpg async/await
- JSONB data type support
- Prepared statements
- SSL/TLS support
- Advanced indexing (btree, hash, gist, gin)

#### MySQL
- Native aiomysql async/await
- Connection pooling
- Table optimization and analysis
- Index management
- SSL/TLS support

## Installation

### Required Dependencies

```bash
# PostgreSQL
pip install asyncpg

# MySQL
pip install aiomysql

# Oracle
pip install cx_Oracle oracledb
```

## Quick Start

### 1. Basic Usage

```python
import asyncio
from database.clients import PostgreSQLClient, DatabaseConfig

# Create configuration
config = DatabaseConfig(
    host='localhost',
    port=5432,
    database='mydb',
    user='postgres',
    password='password',
    min_pool_size=5,
    max_pool_size=20,
)

async def main():
    # Create and initialize client
    client = PostgreSQLClient(config, name="my_postgres")
    await client.initialize()

    try:
        # Execute query
        result = await client.execute("SELECT * FROM users")
        print(f"Found {result['rowcount']} users")

    finally:
        await client.close()

asyncio.run(main())
```

### 2. Transaction Management

```python
async def transfer_money(client, from_account, to_account, amount):
    async with client.transaction():
        # Debit from source account
        await client.execute(
            "UPDATE accounts SET balance = balance - $1 WHERE id = $2",
            params={'amount': amount, 'account': from_account}
        )

        # Credit to destination account
        await client.execute(
            "UPDATE accounts SET balance = balance + $1 WHERE id = $2",
            params={'amount': amount, 'account': to_account}
        )

        # Transaction automatically commits on success
        # or rolls back on exception
```

### 3. Health Monitoring

```python
async def monitor_database(client):
    # Perform health check
    health = await client.health_check()

    print(f"Status: {health.status.value}")
    print(f"Response time: {health.response_time:.3f}s")
    print(f"Pool stats: {health.details['pool']}")

    # Get metrics
    metrics = client.metrics
    print(f"Queries: {metrics['query_count']}")
    print(f"Errors: {metrics['error_count']}")
    print(f"Avg time: {metrics['avg_execution_time']:.3f}s")
```

### 4. Client Manager

```python
from database.clients import DatabaseClientManager, DatabaseType

async def main():
    manager = DatabaseClientManager()

    # Register multiple clients
    await manager.register_client(
        'postgres',
        DatabaseType.POSTGRESQL,
        postgres_config
    )

    await manager.register_client(
        'mysql',
        DatabaseType.MYSQL,
        mysql_config
    )

    # Execute queries
    result = await manager.execute_on_client(
        'postgres',
        "SELECT version()"
    )

    # Health check all
    health = await manager.health_check_all()

    # Get all metrics
    metrics = await manager.get_all_metrics()

    # Cleanup
    await manager.close_all()
```

## Configuration

### DatabaseConfig Options

```python
config = DatabaseConfig(
    # Connection settings
    host='localhost',
    port=5432,
    database='mydb',
    user='postgres',
    password='password',

    # Pool configuration
    min_pool_size=5,          # Minimum connections
    max_pool_size=20,         # Maximum connections
    pool_timeout=30.0,        # Pool acquisition timeout
    connection_timeout=10.0,  # Connection timeout

    # Query configuration
    query_timeout=300.0,      # Query execution timeout
    statement_timeout=None,   # Statement timeout (ms)

    # Retry configuration
    max_retries=3,            # Maximum retry attempts
    retry_delay=1.0,          # Initial retry delay
    retry_backoff=2.0,        # Backoff multiplier

    # SSL/TLS configuration
    ssl_enabled=False,
    ssl_cert='/path/to/cert.pem',
    ssl_key='/path/to/key.pem',
    ssl_ca='/path/to/ca.pem',

    # Additional parameters
    extra_params={}
)
```

### Environment Variables

Set these environment variables to use `create_clients_from_env()`:

```bash
# Oracle CDB
export ORACLE_CDB_HOST=localhost
export ORACLE_CDB_PORT=1521
export ORACLE_CDB_DATABASE=free
export ORACLE_CDB_USER=SYS
export ORACLE_CDB_PASSWORD=MyOraclePass123

# Oracle PDB
export ORACLE_PDB_HOST=localhost
export ORACLE_PDB_PORT=1521
export ORACLE_PDB_DATABASE=freepdb1
export ORACLE_PDB_USER=SYS
export ORACLE_PDB_PASSWORD=MyOraclePass123

# PostgreSQL
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DATABASE=postgres
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=MyPostgresPass123

# MySQL
export MYSQL_HOST=localhost
export MYSQL_PORT=3307
export MYSQL_DATABASE=mysql
export MYSQL_USER=root
export MYSQL_PASSWORD=MyMySQLPass123
```

Then:

```python
from database.clients import create_clients_from_env

manager = await create_clients_from_env()
```

## Advanced Usage

### Oracle PDB Operations

```python
from database.clients import OraclePDBClient

# Create PDB client with CDB config for management
client = OraclePDBClient(
    pdb_config,
    name="my_pdb",
    cdb_config=cdb_config
)

await client.initialize()

# Get current PDB
current = await client.get_current_pdb()

# List all PDBs
pdbs = await client.list_pdbs()

# Switch PDB
await client.switch_pdb('FREEPDB2')

# Open/Close PDB (requires CDB connection)
await client.open_pdb('FREEPDB1')
await client.close_pdb('FREEPDB1')
```

### PostgreSQL JSONB Queries

```python
# Insert JSONB data
await pg_client.execute(
    "INSERT INTO documents (data) VALUES ($1)",
    params={'data': {'name': 'John', 'age': 30}}
)

# Query JSONB data
result = await pg_client.execute(
    "SELECT * FROM documents WHERE data->>'name' = $1",
    params={'name': 'John'}
)

# Create GIN index for JSONB
await pg_client.create_index(
    'documents',
    ['data'],
    method='gin'
)
```

### MySQL Table Operations

```python
# Get table info
info = await mysql_client.get_table_info('users')
print(f"Columns: {info['columns']}")

# Optimize table
result = await mysql_client.optimize_table('users')

# Analyze table
result = await mysql_client.analyze_table('users')

# Create index
await mysql_client.create_index(
    'users',
    ['email', 'created_at'],
    unique=True
)
```

## Error Handling

All clients provide comprehensive error handling:

```python
from database.clients import (
    DatabaseError,
    ConnectionError,
    QueryError,
    TransactionError,
)

try:
    result = await client.execute("SELECT * FROM users")
except ConnectionError as e:
    print(f"Connection failed: {e.message}")
    print(f"Error code: {e.error_code}")
except QueryError as e:
    print(f"Query failed: {e.message}")
    print(f"Original error: {e.original_error}")
except TransactionError as e:
    print(f"Transaction failed: {e.message}")
except DatabaseError as e:
    print(f"Database error: {e.message}")
```

## Performance Metrics

Each client tracks detailed metrics:

```python
metrics = client.metrics

print(f"Query count: {metrics['query_count']}")
print(f"Error count: {metrics['error_count']}")
print(f"Error rate: {metrics['error_rate']:.2%}")
print(f"Avg execution time: {metrics['avg_execution_time']:.3f}s")

# Pool statistics
pool_stats = metrics['pool_stats']
print(f"Pool size: {pool_stats['size']}")
print(f"Active connections: {pool_stats['active']}")
print(f"Available connections: {pool_stats['available']}")

# Recent queries
for query_metric in metrics['recent_queries']:
    print(f"{query_metric.query}: {query_metric.execution_time:.3f}s")
```

## Health Checks

Health checks provide detailed status information:

```python
health = await client.health_check()

# Health status: HEALTHY, DEGRADED, UNHEALTHY, UNKNOWN
print(f"Status: {health.status.value}")

# Response time
print(f"Response time: {health.response_time:.3f}s")

# Error information (if unhealthy)
if health.error:
    print(f"Error: {health.error}")

# Additional details
print(f"Details: {health.details}")
```

## Best Practices

1. **Always use connection pooling** - Never create individual connections
2. **Use transactions** - Wrap related operations in transactions
3. **Monitor health** - Regular health checks prevent issues
4. **Handle errors** - Implement proper error handling
5. **Close connections** - Always close clients when done
6. **Use prepared statements** - Prevent SQL injection
7. **Configure timeouts** - Set appropriate timeouts for your workload
8. **Monitor metrics** - Track performance over time

## Architecture

```
database/clients/
├── __init__.py          # Package initialization
├── base.py              # Base client and common functionality
├── oracle_client.py     # Oracle CDB/PDB client
├── postgresql_client.py # PostgreSQL client
├── mysql_client.py      # MySQL client
├── manager.py           # Client manager
├── config_example.py    # Configuration examples
└── README.md           # This file
```

## Testing

See `/home/claude/aishell-consolidation/aishell-consolidated/tests/database/` for comprehensive test suites.

## Support

For issues or questions, see the main AIShell documentation.
