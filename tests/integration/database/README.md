# Database Integration Tests

Comprehensive integration test suites for multiple databases using Docker test environments.

## Available Test Suites

- **MySQL 8.x** - `test-mysql-integration.ts` (67 tests)
- **PostgreSQL** - `test-postgres-integration.ts`
- **MongoDB** - `test-mongodb-integration.ts`
- **Oracle Database** - `test-oracle-integration.ts`
- **Redis** - `test-redis-integration.ts`

---

# Oracle Database Integration Tests

Comprehensive integration tests for Oracle database client with Docker environment support.

## Overview

This test suite provides complete coverage of Oracle database operations including:

- ✅ Connection management (CDB$ROOT and FREEPDB1)
- ✅ CRUD operations (SELECT, INSERT, UPDATE, DELETE)
- ✅ Transaction management (COMMIT, ROLLBACK)
- ✅ Stored procedures and functions
- ✅ Sequences and triggers
- ✅ Complex queries (JOINs, subqueries, CTEs)
- ✅ Bulk operations
- ✅ Error handling and recovery
- ✅ Connection pooling
- ✅ Performance queries

## Oracle Prerequisites

### 1. Oracle Database Setup

**Option A: Docker (Recommended)**

```bash
# Pull Oracle Database Free image
docker pull container-registry.oracle.com/database/free:latest

# Run Oracle Database container
docker run -d \
  --name oracle-free \
  -p 1521:1521 \
  -p 5500:5500 \
  -e ORACLE_PWD=MyOraclePass123 \
  container-registry.oracle.com/database/free:latest

# Wait for database to be ready (may take 5-10 minutes)
docker logs -f oracle-free
```

**Option B: Oracle Database XE/Enterprise**

Ensure Oracle is running on `localhost:1521` with the password `MyOraclePass123`.

### 2. Install Oracle Client Library

**Linux:**
```bash
# Download Oracle Instant Client
wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-21.12.0.0.0dbru.zip

# Extract and configure
sudo mkdir -p /opt/oracle
sudo unzip instantclient-basic-linux.x64-21.12.0.0.0dbru.zip -d /opt/oracle
sudo sh -c "echo /opt/oracle/instantclient_21_12 > /etc/ld.so.conf.d/oracle-instantclient.conf"
sudo ldconfig
```

**macOS:**
```bash
brew tap InstantClientTap/instantclient
brew install instantclient-basic
```

**Windows:**
Download from [Oracle Instant Client Downloads](https://www.oracle.com/database/technologies/instant-client/downloads.html)

### 3. Install Node Dependencies

```bash
npm install oracledb --save-dev
```

### 4. Initialize Oracle Test Data

```bash
# Connect to Oracle as SYS
sqlplus sys/MyOraclePass123@localhost:1521/freepdb1 as sysdba

# Run initialization script
@tests/integration/database/init-oracle.sql
```

**Or using Docker:**

```bash
# Copy SQL file to container
docker cp tests/integration/database/init-oracle.sql oracle-free:/tmp/

# Execute SQL file
docker exec oracle-free sqlplus sys/MyOraclePass123@FREEPDB1 as sysdba @/tmp/init-oracle.sql
```

## Oracle Connection Details

### CDB$ROOT Connection
```typescript
{
  user: 'SYS',
  password: 'MyOraclePass123',
  connectString: 'localhost:1521/free',
  privilege: SYSDBA
}
```

### FREEPDB1 (Pluggable Database) Connection
```typescript
{
  user: 'SYS',
  password: 'MyOraclePass123',
  connectString: 'localhost:1521/freepdb1',
  privilege: SYSDBA
}
```

## Running Oracle Tests

```bash
# Run all Oracle tests
npm test tests/integration/database/test-oracle-integration.ts

# Run specific test suite
npm test -- --grep "CRUD Operations"

# Run with coverage
npm run test:coverage tests/integration/database/test-oracle-integration.ts
```

## Oracle Test Data Schema

The `init-oracle.sql` script creates:

### Tables
- **employees** - 6 sample employees with salary, department, manager info
- **departments** - 4 departments (Engineering, Sales, Marketing, HR)
- **projects** - 3 active projects
- **employee_projects** - Many-to-many junction table

### Sequences
- `emp_seq` - Employee ID sequence (starts at 1000)
- `dept_seq` - Department ID sequence (starts at 100)
- `proj_seq` - Project ID sequence (starts at 5000)

### Triggers
- `trg_emp_updated_at` - Auto-updates timestamp
- `trg_emp_id` - Auto-assigns employee IDs

### Stored Procedures
- `give_raise(employee_id, percentage, OUT new_salary)`
- `assign_to_project(employee_id, project_id, role, hours)`

### Functions
- `get_dept_salary_total(department_id) RETURN NUMBER`
- `get_full_name(employee_id) RETURN VARCHAR2`

### Views
- `v_employee_details` - Employee info with department
- `v_project_summary` - Project stats with team size

### Package
- `employee_pkg` - Employee management procedures

## Oracle Test Coverage

- **Connection Management** - CDB/PDB connections, health checks
- **CRUD Operations** - INSERT, SELECT, UPDATE, DELETE with bind params
- **Transaction Management** - COMMIT, ROLLBACK, multi-statement
- **Stored Procedures & Functions** - OUT params, function calls
- **Sequences & Triggers** - Auto-increment, validation triggers
- **Complex Queries** - JOINs, subqueries, CTEs, aggregations
- **Bulk Operations** - executeMany for 100+ rows
- **Error Handling** - Constraint violations, syntax errors, recovery
- **Connection Pooling** - Sequential/concurrent connections
- **Performance** - EXPLAIN PLAN, execution stats, timing

## Oracle Troubleshooting

**Connection Issues:**
```bash
# Check if Oracle is running
docker ps | grep oracle

# Check listener status
docker exec oracle-free lsnrctl status

# Wait for ready message
docker logs oracle-free | grep "DATABASE IS READY TO USE"
```

**Library Issues:**
```bash
# Linux: Check LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_12:$LD_LIBRARY_PATH

# macOS: Check DYLD_LIBRARY_PATH
export DYLD_LIBRARY_PATH=/usr/local/lib:$DYLD_LIBRARY_PATH
```

**Test Data Issues:**
```bash
# Recreate test user and data
docker exec oracle-free sqlplus sys/MyOraclePass123@FREEPDB1 as sysdba @/tmp/init-oracle.sql
```

---

# Redis Integration Tests

Comprehensive integration test suite for Redis operations using Docker test environment.

## Prerequisites

### 1. Redis Server

You need a running Redis instance. Use Docker for easy setup:

```bash
# Start Redis container
docker run -d \
  --name redis-test \
  -p 6379:6379 \
  redis:7-alpine

# Or use Docker Compose
cat > docker-compose.redis.yml <<EOF
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --save 60 1 --loglevel warning
EOF

docker-compose -f docker-compose.redis.yml up -d
```

### 2. Dependencies

Install required packages:

```bash
npm install ioredis @types/ioredis --save-dev
```

## Running Tests

### Run All Redis Tests

```bash
npm test tests/integration/database/test-redis-integration.ts
```

### Run Specific Test Suite

```bash
# String operations only
npm test tests/integration/database/test-redis-integration.ts -t "String Operations"

# Pub/Sub tests
npm test tests/integration/database/test-redis-integration.ts -t "Pub/Sub"

# Transactions
npm test tests/integration/database/test-redis-integration.ts -t "Transactions"
```

### Run with Coverage

```bash
npm run test:coverage tests/integration/database/test-redis-integration.ts
```

### Watch Mode

```bash
npm run test:watch tests/integration/database/test-redis-integration.ts
```

## Test Coverage

### 1. Connection Management
- ✅ Connection establishment and health checks
- ✅ Database selection
- ✅ Connection error handling
- ✅ Server info retrieval

### 2. String Operations
- ✅ Basic GET/SET operations
- ✅ Expiration (EX, PX)
- ✅ Conditional set (SETNX)
- ✅ Numeric operations (INCR, DECR, INCRBY, DECRBY)
- ✅ String manipulation (APPEND, STRLEN, GETRANGE)
- ✅ Multiple keys (MSET, MGET)

### 3. Hash Operations
- ✅ Field operations (HSET, HGET, HMSET, HGETALL)
- ✅ Numeric increments (HINCRBY, HINCRBYFLOAT)
- ✅ Field existence checks (HEXISTS)
- ✅ Field deletion (HDEL)
- ✅ Key/value retrieval (HKEYS, HVALS)

### 4. List Operations
- ✅ Push operations (LPUSH, RPUSH)
- ✅ Pop operations (LPOP, RPOP)
- ✅ Range queries (LRANGE)
- ✅ Length and indexing (LLEN, LINDEX, LSET)
- ✅ List manipulation (LTRIM, LREM)

### 5. Set Operations
- ✅ Member operations (SADD, SMEMBERS, SISMEMBER)
- ✅ Cardinality (SCARD)
- ✅ Member removal (SREM, SPOP)
- ✅ Set operations (SINTER, SUNION, SDIFF)

### 6. Sorted Set Operations
- ✅ Score-based operations (ZADD, ZSCORE, ZINCRBY)
- ✅ Range queries (ZRANGE, ZREVRANGE, ZRANGEBYSCORE)
- ✅ Rank operations (ZRANK)
- ✅ Member removal (ZREM, ZPOPMAX, ZPOPMIN)

### 7. Key Expiration
- ✅ Expiration setting (EXPIRE, PEXPIRE, EXPIREAT)
- ✅ TTL queries (TTL, PTTL)
- ✅ Expiration removal (PERSIST)
- ✅ Automatic key expiration

### 8. Pub/Sub Messaging
- ✅ Channel subscription (SUBSCRIBE, UNSUBSCRIBE)
- ✅ Message publishing (PUBLISH)
- ✅ Pattern subscription (PSUBSCRIBE)
- ✅ Message routing

### 9. Transactions
- ✅ Transaction blocks (MULTI, EXEC)
- ✅ Transaction cancellation (DISCARD)
- ✅ Error handling in transactions
- ✅ Optimistic locking (WATCH)

### 10. Pipelining
- ✅ Batch command execution
- ✅ Performance optimization
- ✅ Mixed command pipelining

### 11. Lua Scripting
- ✅ Script execution (EVAL)
- ✅ Script caching (EVALSHA, SCRIPT LOAD)
- ✅ Atomic operations
- ✅ Rate limiting implementation

### 12. Persistence
- ✅ Snapshot creation (SAVE, BGSAVE)
- ✅ Last save time (LASTSAVE)
- ✅ Persistence configuration

### 13. Redis Streams
- ✅ Entry addition (XADD)
- ✅ Stream reading (XREAD, XRANGE)
- ✅ Stream length (XLEN)
- ✅ Stream trimming (XTRIM)
- ✅ Consumer groups (XGROUP)

### 14. HyperLogLog
- ✅ Element addition (PFADD)
- ✅ Cardinality estimation (PFCOUNT)
- ✅ HyperLogLog merging (PFMERGE)
- ✅ Large-scale unique counting

### 15. Advanced Key Operations
- ✅ Pattern matching (KEYS, SCAN)
- ✅ Key deletion (DEL)
- ✅ Key existence (EXISTS)
- ✅ Type checking (TYPE)
- ✅ Key renaming (RENAME, RENAMENX)

### 16. Performance Testing
- ✅ Bulk operation benchmarks
- ✅ Latency measurements
- ✅ Throughput testing

### 17. Error Handling
- ✅ Non-existent key handling
- ✅ Type error handling
- ✅ Connection timeout handling
- ✅ Large value handling

## Test Configuration

The tests use database 15 to avoid conflicts with production data:

```typescript
const REDIS_CONFIG = {
  host: 'localhost',
  port: 6379,
  db: 15, // Dedicated test database
  maxRetriesPerRequest: 3,
  enableOfflineQueue: false,
  lazyConnect: true,
};
```

## Docker Management

### Start Redis

```bash
docker start redis-test

# Or with compose
docker-compose -f docker-compose.redis.yml up -d
```

### Stop Redis

```bash
docker stop redis-test

# Or with compose
docker-compose -f docker-compose.redis.yml down
```

### View Redis Logs

```bash
docker logs -f redis-test
```

### Connect to Redis CLI

```bash
docker exec -it redis-test redis-cli

# Or from host (if redis-cli installed)
redis-cli -h localhost -p 6379 -n 15
```

### Clear Test Database

```bash
# Connect to Redis and clear test DB
docker exec -it redis-test redis-cli -n 15 FLUSHDB
```

## Troubleshooting

### Connection Refused

```bash
# Check if Redis is running
docker ps | grep redis

# Check Redis logs
docker logs redis-test

# Restart Redis
docker restart redis-test
```

### Port Already in Use

```bash
# Find process using port 6379
lsof -i :6379

# Use different port in Docker
docker run -d --name redis-test -p 6380:6379 redis:7-alpine

# Update REDIS_CONFIG port in tests
```

### Test Timeouts

```bash
# Increase test timeout in vitest.config.ts
export default defineConfig({
  test: {
    testTimeout: 10000, // 10 seconds
  }
});
```

### Memory Issues

```bash
# Limit Redis memory
docker run -d \
  --name redis-test \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## Performance Tips

1. **Use Pipelining**: Batch multiple commands to reduce round trips
2. **Use Transactions**: Ensure atomicity for related operations
3. **Use SCAN over KEYS**: For production-safe key iteration
4. **Set Appropriate TTLs**: Prevent memory bloat with expiration
5. **Use Lua Scripts**: For complex atomic operations

## Security Considerations

1. **Use ACLs**: Configure Redis with access control lists
2. **Enable TLS**: Use encrypted connections in production
3. **Bind to Localhost**: Don't expose Redis to public networks
4. **Set Password**: Use requirepass configuration
5. **Disable Dangerous Commands**: FLUSHALL, FLUSHDB, CONFIG, etc.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Redis Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - run: npm ci
      - run: npm test tests/integration/database/test-redis-integration.ts
```

## Additional Resources

- [Redis Documentation](https://redis.io/docs/)
- [ioredis Documentation](https://github.com/redis/ioredis)
- [Redis Commands Reference](https://redis.io/commands/)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)

## Test Metrics

- **Total Tests**: 100+
- **Coverage**: All major Redis features
- **Average Execution Time**: ~5-10 seconds
- **Database**: DB 15 (dedicated test database)
- **Connection Type**: TCP (redis://localhost:6379)

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Clear test data in `beforeEach`
3. Use descriptive test names
4. Add comments for complex operations
5. Update this README with new coverage areas
6. Ensure tests are idempotent
7. Handle cleanup in `afterAll` and `afterEach`
