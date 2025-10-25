# Oracle Database Tests

This directory contains tests for Oracle Database connectivity and operations.

## Test Environments

### CDB$ROOT (Container Database)
- **Connection**: `localhost:1521/free`
- **User**: SYS as SYSDBA
- **Purpose**: System-level operations, CDB management

### FREEPDB1 (Pluggable Database)
- **Connection**: `localhost:1521/freepdb1`
- **User**: SYS as SYSDBA
- **Purpose**: Application-level operations, PDB management

## Test Categories

1. **Connection Tests** - Basic connectivity and authentication
2. **Query Tests** - SELECT, DML operations
3. **Schema Tests** - DDL operations, object management
4. **Transaction Tests** - Commit, rollback, savepoints
5. **Security Tests** - User management, privileges
6. **Performance Tests** - Query optimization, execution plans

## Running Tests

```bash
npm run test:oracle
npm run test:oracle:cdb     # CDB$ROOT only
npm run test:oracle:pdb     # FREEPDB1 only
```

## Configuration

See `/config/database/oracle.config.json` for connection settings.
