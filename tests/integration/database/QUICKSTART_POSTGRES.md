# PostgreSQL Integration Tests - Quick Start Guide

## ⚡ Quick Start (60 seconds)

### 1. Start PostgreSQL (10 seconds)
```bash
cd tests/integration/database
docker-compose up -d postgres
```

### 2. Wait for Ready (20 seconds)
```bash
# Check status
docker-compose ps postgres

# View logs
docker-compose logs -f postgres

# Test connection
docker-compose exec postgres pg_isready -U postgres
```

### 3. Run Tests (30 seconds)
```bash
cd /home/claude/AIShell/aishell
npm test tests/integration/database/test-postgres-integration.ts
```

## 🎯 Quick Commands

### Run All PostgreSQL Tests
```bash
npm test tests/integration/database/test-postgres-integration.ts
```

### Run Specific Test Suites
```bash
# Connection tests
npm test tests/integration/database/test-postgres-integration.ts -t "Connection"

# CRUD operations
npm test tests/integration/database/test-postgres-integration.ts -t "CRUD"

# Transactions
npm test tests/integration/database/test-postgres-integration.ts -t "Transaction"

# Full-text search
npm test tests/integration/database/test-postgres-integration.ts -t "Full-Text Search"

# Window functions
npm test tests/integration/database/test-postgres-integration.ts -t "Window"

# Concurrent operations
npm test tests/integration/database/test-postgres-integration.ts -t "Concurrent"
```

### Run with Coverage
```bash
npm run test:coverage tests/integration/database/test-postgres-integration.ts
```

## 🐳 Docker Commands

### Start
```bash
cd tests/integration/database
docker-compose up -d postgres
```

### Stop
```bash
docker-compose stop postgres
```

### Reset (Full Clean)
```bash
docker-compose down -v
docker-compose up -d postgres
```

### View Logs
```bash
docker-compose logs -f postgres
```

### Connect to PostgreSQL
```bash
# Via Docker
docker-compose exec postgres psql -U postgres -d postgres

# Via host (if psql installed)
PGPASSWORD=MyPostgresPass123 psql -h localhost -U postgres -d postgres
```

## 📊 Test Coverage

**Total: 57 comprehensive tests**

| Category | Tests | Coverage |
|----------|-------|----------|
| Connection & Auth | 5 | Connection pooling, timeouts, capabilities |
| CRUD Operations | 6 | INSERT, SELECT, UPDATE, DELETE, bulk ops |
| Transactions | 4 | COMMIT, ROLLBACK, savepoints, nested |
| Array & JSON | 6 | ARRAY[], JSONB, operators (@>, ->, ->>) |
| Full-Text Search | 4 | tsvector, tsquery, ranking, highlighting |
| Window Functions | 6 | ROW_NUMBER, RANK, LAG, LEAD, aggregates |
| CTEs | Included | WITH clause, recursive CTEs |
| Foreign Keys | 3 | Constraints, CASCADE, referential integrity |
| Indexes | 4 | Index usage, EXPLAIN, optimization |
| Concurrent Ops | 3 | Pool management, parallel queries |
| Listen/Notify | 2 | Pub-sub messaging, channels |
| Prepared Statements | 2 | Statement caching, reuse |
| Batch Operations | 3 | Bulk INSERT, UPDATE, DELETE |
| Error Handling | 4 | Syntax errors, constraints, connections |
| Advanced Features | 6 | Views, UPSERT, RETURNING, aggregations |

## 🔧 Troubleshooting

### Connection Refused
```bash
docker-compose restart postgres
docker-compose logs postgres
```

### Port Already in Use
```bash
lsof -i :5432
# Or change port in docker-compose.yml
```

### Tests Timeout
```bash
# Increase timeout in test file or vitest.config.ts
testTimeout: 15000
```

### Clean Slate
```bash
docker-compose down -v
docker-compose up -d postgres
npm test tests/integration/database/test-postgres-integration.ts
```

## 📝 Configuration

### Connection (Default)
```
Host: localhost
Port: 5432
Database: postgres
User: postgres
Password: MyPostgresPass123
```

### Environment Variables
```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=postgres
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=MyPostgresPass123
```

## 📦 Test Data

The database is pre-populated with:
- 5 users (with roles and preferences)
- 5 customers (with addresses)
- 8 products (with tags and metadata)
- 6 orders (with items)
- 5 documents (for full-text search)
- 8 analytics events (for window functions)

## 🚀 Features Tested

- ✅ Connection pooling (max 20 connections)
- ✅ Parameterized queries (SQL injection prevention)
- ✅ Transaction management (ACID compliance)
- ✅ Array data types (TEXT[], INTEGER[])
- ✅ JSON data types (JSONB with operators)
- ✅ Full-text search (tsvector, tsquery)
- ✅ Window functions (analytics queries)
- ✅ CTEs (recursive and non-recursive)
- ✅ Foreign key constraints (CASCADE)
- ✅ GIN indexes (arrays, JSONB, full-text)
- ✅ B-tree indexes (standard lookups)
- ✅ Pub-sub messaging (LISTEN/NOTIFY)
- ✅ Prepared statements (performance)
- ✅ Batch operations (bulk processing)
- ✅ Error handling (graceful degradation)
- ✅ Views and materialized views
- ✅ UPSERT (INSERT ... ON CONFLICT)
- ✅ RETURNING clause
- ✅ Triggers and functions

## 📚 Files

- `test-postgres-integration.ts` - 57 comprehensive tests (1034 lines)
- `init-postgres.sql` - Database schema and seed data
- `POSTGRES_TESTS.md` - Detailed documentation
- `docker-compose.yml` - Docker configuration

## ⏱️ Expected Performance

- Full test suite: 8-12 seconds
- Individual suites: 500ms - 5 seconds
- Connection tests: ~500ms
- Batch operations: 3-5 seconds (100+ records)

## 🎓 Learning Resources

See `POSTGRES_TESTS.md` for:
- Detailed test descriptions
- SQL query examples
- Best practices
- Performance tuning tips
- Advanced PostgreSQL features

## 💡 Next Steps

1. ✅ Start PostgreSQL: `docker-compose up -d postgres`
2. ✅ Run tests: `npm test tests/integration/database/test-postgres-integration.ts`
3. ✅ Review coverage: `npm run test:coverage`
4. ✅ Read docs: `cat POSTGRES_TESTS.md`
5. ✅ Explore data: `docker-compose exec postgres psql -U postgres`

## 🔗 Related

- See `README.md` for other database tests (MongoDB, MySQL, Oracle, Redis)
- See `run-tests.sh` for automated test runner (MongoDB example)
- See `docker-compose.yml` for all database services
