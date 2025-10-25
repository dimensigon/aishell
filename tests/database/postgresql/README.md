# PostgreSQL Database Tests

This directory contains tests for PostgreSQL database connectivity and operations.

## Test Environment

- **Connection**: `localhost:5432/postgres`
- **User**: postgres
- **Remote Test Server**: `51.15.90.27:5432`

## Test Categories

1. **Connection Tests** - Basic connectivity and authentication
2. **Query Tests** - SELECT, DML operations
3. **Schema Tests** - DDL operations, table management
4. **Transaction Tests** - ACID compliance, isolation levels
5. **JSON Tests** - JSONB operations, indexing
6. **Full-Text Search** - Text search operations
7. **Performance Tests** - Query optimization, EXPLAIN plans

## Running Tests

```bash
npm run test:postgresql
npm run test:postgresql:local   # Local instance
npm run test:postgresql:remote  # Remote test server
```

## Configuration

See `/config/database/postgresql.config.json` for connection settings.
