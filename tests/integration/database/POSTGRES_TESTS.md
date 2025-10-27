# PostgreSQL Integration Tests

Comprehensive integration tests for PostgreSQL client with Docker environment support.

## Overview

This test suite provides complete coverage of PostgreSQL operations including:

- ✅ Connection and authentication (pool management)
- ✅ CRUD operations (INSERT, SELECT, UPDATE, DELETE)
- ✅ Transaction management (BEGIN, COMMIT, ROLLBACK, savepoints)
- ✅ Array and JSON data types (ARRAY, JSONB)
- ✅ Full-text search (tsvector, tsquery, ts_rank)
- ✅ Window functions (ROW_NUMBER, RANK, LEAD, LAG)
- ✅ Common Table Expressions (CTEs, recursive CTEs)
- ✅ Foreign key constraints and cascading
- ✅ Indexes and query optimization
- ✅ Concurrent connections and connection pooling
- ✅ Listen/Notify pub-sub messaging
- ✅ Prepared statements and statement caching
- ✅ Batch operations and bulk inserts
- ✅ Error handling and recovery
- ✅ Advanced features (views, materialized views, UPSERT)

## Prerequisites

### 1. PostgreSQL Server

Start PostgreSQL using Docker:

```bash
cd tests/integration/database
docker-compose up -d postgres
```

Check if PostgreSQL is ready:

```bash
docker-compose ps postgres
docker-compose logs postgres

# Or check health
docker-compose exec postgres pg_isready -U postgres
```

### 2. Dependencies

PostgreSQL driver is already included in package.json:

```json
{
  "dependencies": {
    "pg": "^8.16.3"
  },
  "devDependencies": {
    "@types/pg": "^8.15.5"
  }
}
```

## Running Tests

### Run All PostgreSQL Tests

```bash
npm test tests/integration/database/test-postgres-integration.ts
```

### Run Specific Test Suite

```bash
# Connection tests only
npm test tests/integration/database/test-postgres-integration.ts -t "Connection"

# CRUD operations
npm test tests/integration/database/test-postgres-integration.ts -t "CRUD"

# Transaction tests
npm test tests/integration/database/test-postgres-integration.ts -t "Transaction"

# Array and JSON tests
npm test tests/integration/database/test-postgres-integration.ts -t "Array and JSON"

# Full-text search tests
npm test tests/integration/database/test-postgres-integration.ts -t "Full-Text Search"

# Window functions
npm test tests/integration/database/test-postgres-integration.ts -t "Window Functions"

# Concurrent operations
npm test tests/integration/database/test-postgres-integration.ts -t "Concurrent"
```

### Run with Coverage

```bash
npm run test:coverage tests/integration/database/test-postgres-integration.ts
```

### Watch Mode

```bash
npm run test:watch tests/integration/database/test-postgres-integration.ts
```

## Test Configuration

Connection settings (can be overridden with environment variables):

```typescript
const TEST_CONFIG = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  database: process.env.POSTGRES_DB || 'postgres',
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'MyPostgresPass123',
  max: 20, // Connection pool size
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
};
```

### Environment Variables

Create a `.env` file in the project root:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=MyPostgresPass123
```

## Test Database Schema

The test database includes the following tables with seed data:

### Core Tables

#### users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    roles TEXT[] DEFAULT '{}',           -- Array type
    preferences JSONB DEFAULT '{}',      -- JSON type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### customers
```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address JSONB,                       -- JSON address
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### products
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    category VARCHAR(50),
    tags TEXT[],                         -- Array of tags
    metadata JSONB,                      -- Product metadata
    search_vector TSVECTOR,              -- Full-text search
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### orders & order_items
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    shipping_address JSONB,
    notes TEXT
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(10, 2) NOT NULL
);
```

#### search_documents
```sql
CREATE TABLE search_documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    author VARCHAR(100),
    search_vector TSVECTOR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### analytics
```sql
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    event_value NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Views

- **customer_order_summary**: Aggregated customer order information
- **product_sales_summary**: Materialized view of product sales statistics

### Indexes

- B-tree indexes on primary keys and foreign keys
- GIN indexes on ARRAY and JSONB columns
- GIN indexes on TSVECTOR columns for full-text search
- Composite indexes for common query patterns

### Triggers

- Automatic search_vector updates on products
- Automatic search_vector updates on search_documents
- Timestamp triggers for updated_at fields

### Sample Data

- 5 users with various roles and preferences
- 5 customers with complete profile information
- 8 products across different categories
- 6 orders with multiple items
- 5 documents for full-text search testing
- 8 analytics events for window function testing

## Test Coverage Details

### 1. Connection and Authentication (5 tests)
- ✅ Successful connection establishment
- ✅ Invalid credentials handling
- ✅ Connection timeout handling
- ✅ Database version retrieval
- ✅ Database capabilities checking

### 2. CRUD Operations (6 tests)
- ✅ CREATE (INSERT) with RETURNING
- ✅ READ (SELECT) with parameterized queries
- ✅ UPDATE with conditions
- ✅ DELETE with verification
- ✅ Bulk INSERT operations
- ✅ Constraint enforcement

### 3. Transaction Management (4 tests)
- ✅ Transaction commit
- ✅ Transaction rollback
- ✅ Savepoints (SAVEPOINT, ROLLBACK TO SAVEPOINT)
- ✅ Nested transactions with multiple savepoints

### 4. Array and JSON Data Types (6 tests)
- ✅ ARRAY column operations
- ✅ ARRAY queries with ANY operator
- ✅ JSONB column operations
- ✅ JSONB queries with -> and ->> operators
- ✅ JSONB containment queries with @>
- ✅ Nested JSONB field updates with jsonb_set

### 5. Full-Text Search (4 tests)
- ✅ Basic full-text search with to_tsquery
- ✅ Multi-term search with & operator
- ✅ Phrase queries with phraseto_tsquery
- ✅ Search result highlighting with ts_headline

### 6. Window Functions and CTEs (6 tests)
- ✅ ROW_NUMBER window function
- ✅ RANK and DENSE_RANK
- ✅ LAG and LEAD window functions
- ✅ Common Table Expressions (WITH clause)
- ✅ Recursive CTEs
- ✅ Aggregate window functions (SUM, AVG with OVER)

### 7. Foreign Key Constraints (3 tests)
- ✅ Foreign key enforcement on INSERT
- ✅ CASCADE delete operations
- ✅ Referential integrity validation

### 8. Indexes and Query Optimization (4 tests)
- ✅ Index usage verification with EXPLAIN
- ✅ Index listing
- ✅ Table statistics (pg_stat_user_tables)
- ✅ Query performance analysis with EXPLAIN ANALYZE

### 9. Concurrent Connections (3 tests)
- ✅ Multiple concurrent queries
- ✅ Connection pool management
- ✅ Concurrent transactions

### 10. Listen/Notify Pub-Sub (2 tests)
- ✅ Send and receive notifications
- ✅ Multiple channel handling

### 11. Prepared Statements (2 tests)
- ✅ Prepared statement execution
- ✅ Prepared statement reuse for performance

### 12. Batch Operations (3 tests)
- ✅ Batch INSERT (100+ records)
- ✅ Batch UPDATE
- ✅ Batch DELETE

### 13. Error Handling (4 tests)
- ✅ Syntax error handling
- ✅ Constraint violation handling
- ✅ Connection error handling
- ✅ Detailed error information extraction

### 14. Advanced Features (6 tests)
- ✅ Materialized views (REFRESH MATERIALIZED VIEW)
- ✅ Regular views
- ✅ RETURNING clause
- ✅ UPSERT (INSERT ... ON CONFLICT)
- ✅ Series and sequence generation
- ✅ Complex aggregations (COUNT, SUM, AVG, STDDEV)

**Total: 58 comprehensive tests**

## Docker Management

### Start PostgreSQL Only

```bash
cd tests/integration/database
docker-compose up -d postgres
```

### Check PostgreSQL Status

```bash
docker-compose ps postgres
docker-compose logs -f postgres
```

### Stop PostgreSQL

```bash
docker-compose stop postgres
```

### Remove PostgreSQL Container and Volumes

```bash
docker-compose down -v
```

### Connect to PostgreSQL CLI

From Docker:
```bash
docker-compose exec postgres psql -U postgres -d postgres
```

From host (if psql installed):
```bash
PGPASSWORD=MyPostgresPass123 psql -h localhost -U postgres -d postgres
```

### Useful PostgreSQL Commands

```sql
-- List all tables
\dt

-- Describe table structure
\d users

-- List all indexes
\di

-- Show table size
\dt+ users

-- List all databases
\l

-- List all schemas
\dn

-- Show current database
SELECT current_database();

-- Show active connections
SELECT * FROM pg_stat_activity WHERE datname = 'postgres';

-- Kill long-running query
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';
```

### Reset Test Database

Full reset (destroys all data):
```bash
docker-compose down -v
docker-compose up -d postgres
```

Reload seed data only:
```bash
docker-compose exec postgres psql -U postgres -d postgres -f /docker-entrypoint-initdb.d/init.sql
```

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs for errors
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Port Already in Use

```bash
# Find process using port 5432
lsof -i :5432

# Kill the process (replace PID)
kill -9 <PID>

# Or use different port in docker-compose.yml
services:
  postgres:
    ports:
      - "5433:5432"

# Update environment variable
export POSTGRES_PORT=5433
```

### Permission Denied

```bash
# Check file permissions
ls -la init-postgres.sql

# Fix permissions
chmod 644 init-postgres.sql

# Ensure volume permissions
docker-compose down -v
docker-compose up -d
```

### Test Timeouts

Tests may timeout if PostgreSQL is slow to respond. Increase timeout:

```typescript
// In specific test
it('should handle long operation', async () => {
  // test code
}, 30000); // 30 second timeout

// Or in vitest.config.ts
export default defineConfig({
  test: {
    testTimeout: 15000, // 15 seconds
  }
});
```

### Container Won't Start

```bash
# Check Docker daemon
docker info

# Check Docker Compose version
docker-compose --version

# Rebuild container
docker-compose down
docker-compose build --no-cache postgres
docker-compose up -d postgres
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: PostgreSQL Integration Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: MyPostgresPass123
          POSTGRES_DB: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Initialize database
        run: |
          PGPASSWORD=MyPostgresPass123 psql -h localhost -U postgres -d postgres \
            -f tests/integration/database/init-postgres.sql

      - name: Run PostgreSQL integration tests
        run: npm test tests/integration/database/test-postgres-integration.ts

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        if: always()
        with:
          files: ./coverage/lcov.info
          flags: postgres-integration
```

### GitLab CI Example

```yaml
postgres-tests:
  image: node:18
  services:
    - postgres:16-alpine
  variables:
    POSTGRES_DB: postgres
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: MyPostgresPass123
    POSTGRES_HOST: postgres
  before_script:
    - apt-get update && apt-get install -y postgresql-client
    - npm ci
    - PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U postgres -d postgres
      -f tests/integration/database/init-postgres.sql
  script:
    - npm test tests/integration/database/test-postgres-integration.ts
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
```

## Performance Benchmarks

Expected test execution times (typical development machine):

| Test Suite | Expected Duration | Number of Tests |
|------------|------------------|----------------|
| Full test suite | 8-12 seconds | 58 tests |
| Connection tests | ~500ms | 5 tests |
| CRUD operations | 1-2 seconds | 6 tests |
| Transactions | 1-2 seconds | 4 tests |
| Array/JSON types | ~1 second | 6 tests |
| Full-text search | ~500ms | 4 tests |
| Window functions | ~1 second | 6 tests |
| Foreign keys | ~500ms | 3 tests |
| Indexes/optimization | ~1 second | 4 tests |
| Concurrent operations | 2-3 seconds | 3 tests |
| Listen/Notify | ~1 second | 2 tests |
| Prepared statements | ~500ms | 2 tests |
| Batch operations | 3-5 seconds | 3 tests |
| Error handling | ~500ms | 4 tests |
| Advanced features | 1-2 seconds | 6 tests |

## Best Practices

### Connection Management

1. **Use connection pooling**: Already configured with max 20 connections
2. **Release connections**: Always release clients back to the pool
3. **Handle connection errors**: Implement retry logic for transient errors
4. **Set appropriate timeouts**: Balance between reliability and responsiveness

### Query Optimization

1. **Use parameterized queries**: Prevent SQL injection and improve performance
2. **Create appropriate indexes**: Especially for frequently queried columns
3. **Use EXPLAIN ANALYZE**: Understand query execution plans
4. **Avoid N+1 queries**: Use JOINs or batch operations

### Transaction Management

1. **Keep transactions short**: Minimize lock duration
2. **Use savepoints**: For complex transaction logic
3. **Handle deadlocks**: Implement retry logic
4. **Set isolation levels**: Based on consistency requirements

### Testing

1. **Clean up after tests**: Each test should be independent
2. **Use test database**: Never test on production data
3. **Test error cases**: Verify error handling works correctly
4. **Mock external dependencies**: Keep tests isolated

## Additional Resources

- [PostgreSQL Official Documentation](https://www.postgresql.org/docs/)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)
- [node-postgres (pg) Documentation](https://node-postgres.com/)
- [PostgreSQL Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Don't_Do_This)
- [PostgreSQL Index Types](https://www.postgresql.org/docs/current/indexes-types.html)
- [Full-Text Search Guide](https://www.postgresql.org/docs/current/textsearch.html)
- [Window Functions Tutorial](https://www.postgresql.org/docs/current/tutorial-window.html)

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Use descriptive test names
3. Add proper cleanup in `beforeEach` and `afterEach`
4. Document complex test scenarios
5. Update this README with new coverage areas
6. Ensure tests are idempotent and isolated
7. Add appropriate error handling
8. Include performance considerations

## License

MIT
