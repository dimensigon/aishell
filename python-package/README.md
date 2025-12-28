# AI-Shell Python SDK

[![PyPI version](https://badge.fury.io/py/ai-shell-py.svg)](https://badge.fury.io/py/ai-shell-py)
[![Python Versions](https://img.shields.io/pypi/pyversions/ai-shell-py.svg)](https://pypi.org/project/ai-shell-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python SDK for AI-Shell providing database clients, MCP integration, and AI agents for database management.

## Features

- **Multi-Database Support**: PostgreSQL, MySQL, MongoDB, Redis, Oracle, Cassandra, Neo4j, DynamoDB
- **Async/Await**: Built on asyncio for high-performance operations
- **MCP Integration**: Model Context Protocol support for AI coordination
- **Database Agents**: AI-powered database optimization, migration, and backup agents
- **Connection Pooling**: Intelligent connection management with retry logic
- **Type Safety**: Full type hints and Pydantic models
- **Security**: Built-in encryption and secure credential management

## Installation

### Basic Installation

```bash
pip install ai-shell-py
```

### With Specific Database Support

```bash
# PostgreSQL
pip install ai-shell-py[postgresql]

# MySQL
pip install ai-shell-py[mysql]

# MongoDB
pip install ai-shell-py[mongodb]

# Redis
pip install ai-shell-py[redis]

# All databases
pip install ai-shell-py[all-databases]
```

### With AI Features

```bash
# MCP integration
pip install ai-shell-py[mcp]

# AI/LLM features
pip install ai-shell-py[ai]

# Everything
pip install ai-shell-py[all]
```

## Quick Start

### PostgreSQL Client

```python
from ai_shell_py.database import PostgreSQLClient

async def main():
    client = PostgreSQLClient(
        host="localhost",
        port=5432,
        database="mydb",
        user="user",
        password="password"
    )

    await client.connect()

    # Execute query
    result = await client.execute("SELECT * FROM users LIMIT 10")

    await client.disconnect()

import asyncio
asyncio.run(main())
```

### MySQL Client

```python
from ai_shell_py.database import MySQLClient

async def main():
    client = MySQLClient(
        host="localhost",
        port=3306,
        database="mydb",
        user="user",
        password="password"
    )

    await client.connect()
    result = await client.execute("SELECT * FROM users")
    await client.disconnect()
```

### MongoDB Client

```python
from ai_shell_py.database import MongoDBClient

async def main():
    client = MongoDBClient(
        host="localhost",
        port=27017,
        database="mydb"
    )

    await client.connect()

    # Find documents
    results = await client.find("users", {"status": "active"})

    await client.disconnect()
```

### Redis Client

```python
from ai_shell_py.database import RedisClient

async def main():
    client = RedisClient(
        host="localhost",
        port=6379,
        db=0
    )

    await client.connect()

    # Set/Get operations
    await client.set("key", "value")
    value = await client.get("key")

    await client.disconnect()
```

## MCP Clients

```python
from ai_shell_py.mcp_clients import MCPManager

async def main():
    manager = MCPManager()

    # Register database client
    await manager.register_client("postgresql", client)

    # Execute MCP operations
    result = await manager.execute_operation("query", {
        "database": "postgresql",
        "sql": "SELECT * FROM users"
    })
```

## Database Agents

```python
from ai_shell_py.agents import DatabaseOptimizer, BackupManager

# Optimization agent
optimizer = DatabaseOptimizer(client)
recommendations = await optimizer.analyze_performance()

# Backup agent
backup_manager = BackupManager(client)
await backup_manager.create_backup("/path/to/backup")
```

## Advanced Features

### Connection Pooling

```python
from ai_shell_py.database import PostgreSQLClient

client = PostgreSQLClient(
    host="localhost",
    pool_size=20,
    pool_timeout=30,
    max_overflow=10
)
```

### Retry Logic

```python
from ai_shell_py.database import RetryConfig

retry_config = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0,
    exponential_backoff=True
)

client = PostgreSQLClient(
    host="localhost",
    retry_config=retry_config
)
```

### Docker Integration

```python
from ai_shell_py.mcp_clients import DockerIntegration

docker = DockerIntegration()
container = await docker.create_database_container("postgresql:15")
```

## Configuration

Create a `.env` file:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mydb
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=mydb
MYSQL_USER=user
MYSQL_PASSWORD=password

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=mydb

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

Load configuration:

```python
from ai_shell_py.database import load_config_from_env

config = load_config_from_env()
client = PostgreSQLClient(**config["postgresql"])
```

## Documentation

Full documentation is available at: https://ai-shell-py.readthedocs.io

## Requirements

- Python 3.9+
- Database-specific drivers (installed via extras)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](https://github.com/yourusername/AIShell/blob/main/CONTRIBUTING.md)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- GitHub Issues: https://github.com/yourusername/AIShell/issues
- Documentation: https://ai-shell-py.readthedocs.io
- PyPI: https://pypi.org/project/ai-shell-py/

## Related Projects

- [AI-Shell](https://github.com/yourusername/AIShell) - Full AI-powered database management CLI
- [Claude-Flow](https://github.com/dimensigon/claude-flow) - MCP orchestration framework

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
