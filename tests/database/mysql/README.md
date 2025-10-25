# MySQL Database Tests

This directory contains tests for MySQL database connectivity and operations.

## Test Environment

- **Connection**: `localhost:3307`
- **User**: root
- **Remote Test Server**: `51.15.90.27:3307`

## Test Categories

1. **Connection Tests** - Basic connectivity and authentication
2. **Query Tests** - SELECT, DML operations
3. **Schema Tests** - DDL operations, table management
4. **Transaction Tests** - InnoDB transactions, locking
5. **Index Tests** - Index types, optimization
6. **Stored Procedures** - Routine creation and execution
7. **Performance Tests** - Query optimization, EXPLAIN plans

## Running Tests

```bash
npm run test:mysql
npm run test:mysql:local   # Local instance
npm run test:mysql:remote  # Remote test server
```

## Configuration

See `/config/database/mysql.config.json` for connection settings.
