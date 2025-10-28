# MCP Database Integration Tests

Comprehensive integration testing framework for all MCP (Model Context Protocol) database clients with Docker orchestration.

## Overview

This test suite provides end-to-end integration testing for:
- PostgreSQL
- MySQL
- MongoDB
- Redis
- SQLite
- Connection Manager

**Total Tests**: 250+ integration tests
**Coverage Goal**: 85%+ line coverage, 95%+ integration coverage

## Test Structure

```
tests/integration/mcp/
├── __init__.py                          # Package initialization
├── config.py                            # Test configuration and Docker configs
├── conftest.py                          # Pytest fixtures and setup
├── test_postgresql_integration.py      # PostgreSQL tests (40+ tests)
├── test_mysql_integration.py           # MySQL tests (35+ tests)
├── test_mongodb_integration.py         # MongoDB tests (35+ tests)
├── test_redis_integration.py           # Redis tests (40+ tests)
├── test_sqlite_integration.py          # SQLite tests (25+ tests)
├── test_manager_integration.py         # Connection Manager tests (30+ tests)
├── test_docker_integration.py          # Docker container tests (20+ tests)
├── test_mcp_performance.py             # Performance benchmarks (25+ tests)
├── run_tests.sh                        # Test execution script
├── cleanup.sh                          # Cleanup script
└── README.md                           # This file
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Required Python packages:
  ```bash
  pip install pytest pytest-asyncio pytest-cov
  pip install psycopg pymongo redis motor aiosqlite mysql-connector-python pyyaml
  ```

### Running Tests

#### Option 1: Using the test script (Recommended)

```bash
cd tests/integration/mcp
chmod +x run_tests.sh
./run_tests.sh
```

The script will:
1. Check Docker availability
2. Start all database containers
3. Wait for containers to be healthy
4. Run all integration tests
5. Generate coverage reports
6. Clean up containers on exit

#### Option 2: Manual execution

```bash
# Start Docker containers
docker-compose -f docker-compose.test.yml up -d

# Wait for containers to be healthy
# ...

# Run tests
pytest tests/integration/mcp/ -v --cov=src/mcp --cov-report=html

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

#### Option 3: Using existing containers

```bash
./run_tests.sh --skip-docker
```

### Cleanup

```bash
cd tests/integration/mcp
./cleanup.sh

# Full cleanup (including Docker images)
./cleanup.sh --full
```

## Test Categories

### 1. Connection Tests
- Connection establishment
- Authentication
- Reconnection
- Connection pooling
- Health checks

### 2. CRUD Operations
- Create (INSERT)
- Read (SELECT)
- Update (UPDATE)
- Delete (DELETE)
- Bulk operations

### 3. Transaction Tests
- Transaction commit
- Transaction rollback
- Savepoints
- Isolation levels

### 4. Advanced Features
- PostgreSQL: LISTEN/NOTIFY, COPY, prepared statements, JSON/JSONB
- MySQL: Stored procedures, prepared statements, multiple result sets
- MongoDB: Aggregation, indexing, GridFS, change streams
- Redis: Pub/Sub, streams, Lua scripts, pipelines
- SQLite: WAL mode, full-text search, concurrent access

### 5. Performance Tests
- Query execution time
- Bulk insert performance
- Concurrent operations
- Connection pool performance
- Comparative benchmarks

### 6. Docker Tests
- Container health
- Port exposure
- Volume persistence
- Network connectivity
- Resource usage

### 7. Connection Manager Tests
- Multiple connections
- Connection lifecycle
- Pool limits
- Health monitoring
- Metrics collection

## Configuration

Test configuration is in `/home/claude/AIShell/aishell/tests/integration/mcp/config.py`:

```python
DOCKER_CONFIGS = {
    'postgresql': {
        'host': 'localhost',
        'port': 5432,
        'database': 'test_integration_db',
        'username': 'postgres',
        'password': 'MyPostgresPass123'
    },
    # ... other databases
}

BENCHMARK_CONFIGS = {
    'query_count': 1000,
    'concurrent_connections': 10,
    'large_result_rows': 10000,
    'bulk_insert_rows': 5000
}
```

## CI/CD Integration

GitHub Actions workflow is configured in `/home/claude/AIShell/aishell/.github/workflows/mcp-integration-tests.yml`:

### Features:
- Automatic test execution on push/PR
- Multiple Python version matrix (3.10, 3.11, 3.12)
- Coverage reporting to Codecov
- Performance benchmarking
- Docker container testing
- Test result publishing

### Triggers:
- Push to main/develop branches
- Pull requests
- Daily scheduled runs (2 AM UTC)
- Manual workflow dispatch

## Coverage Goals

- **Line Coverage**: 85%+
- **Integration Coverage**: 95%+
- **All Critical Paths**: 100%

Current coverage can be viewed after running tests:
```bash
open htmlcov/index.html  # View HTML coverage report
```

## Test Patterns

### Async Test Example
```python
@pytest.mark.asyncio
async def test_postgresql_connection(pg_client, postgresql_clean):
    config = DOCKER_CONFIGS['postgresql']

    await pg_client.connect(**config)

    assert pg_client.is_connected()

    health = await pg_client.health_check()
    assert health['healthy'] is True
```

### Fixture Usage
```python
# postgresql_clean fixture automatically cleans database before/after test
async def test_insert_user(pg_client, postgresql_clean):
    await pg_client.connect(**DOCKER_CONFIGS['postgresql'])

    result = await pg_client.execute(
        "INSERT INTO test_users (name, email) VALUES ($1, $2)",
        ("John", "john@example.com")
    )

    assert result['rows'][0]['id'] is not None
```

## Troubleshooting

### Containers not starting
```bash
# Check Docker status
docker ps -a

# View container logs
docker logs mcp-test-postgres
docker logs mcp-test-mysql
docker logs mcp-test-mongodb
docker logs mcp-test-redis

# Restart containers
docker-compose -f docker-compose.test.yml restart
```

### Tests failing
```bash
# Run with verbose output
pytest tests/integration/mcp/ -vv -s

# Run specific test file
pytest tests/integration/mcp/test_postgresql_integration.py -v

# Run specific test
pytest tests/integration/mcp/test_postgresql_integration.py::TestPostgreSQLConnection::test_connect_success -v
```

### Port conflicts
```bash
# Check port usage
lsof -i :5432  # PostgreSQL
lsof -i :3306  # MySQL
lsof -i :27017 # MongoDB
lsof -i :6379  # Redis

# Change ports in config.py if needed
```

## Performance Benchmarks

Run performance tests separately:
```bash
pytest tests/integration/mcp/test_mcp_performance.py -v -s
```

Expected performance (approximate):
- PostgreSQL: 1000+ queries/second
- MySQL: 800+ queries/second
- MongoDB: 1500+ inserts/second
- Redis: 10000+ operations/second
- SQLite: 500+ queries/second

## Contributing

When adding new tests:

1. Follow existing test patterns
2. Use appropriate fixtures
3. Clean up test data (fixtures handle this)
4. Add docstrings to test classes/methods
5. Update test counts in this README
6. Ensure tests are idempotent
7. Test both success and failure cases

## Support

For issues or questions:
- Check existing tests for examples
- Review Docker logs for container issues
- Verify network connectivity
- Ensure all dependencies are installed
- Check Python version compatibility

## License

Part of the AIShell project. See main project LICENSE file.
