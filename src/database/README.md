# Database Module

Multi-database support for Oracle, PostgreSQL, and MySQL.

## Current Implementation (from AIShell-Local)

- Core database abstraction
- Connection pooling
- Query execution
- Transaction management

## Extended Database Support

### Oracle Database
- CDB$ROOT support
- FREEPDB1 (PDB) support
- Advanced features: RAC, ASM, Data Guard

### PostgreSQL
- Standard PostgreSQL features
- JSONB operations
- Full-text search
- Advanced indexing

### MySQL
- InnoDB engine support
- Stored procedures
- Replication support

## Directory Structure

```
database/
├── adapters/          # Database-specific adapters
│   ├── oracle.ts
│   ├── postgresql.ts
│   └── mysql.ts
├── connection/        # Connection management
├── query/            # Query builders and executors
├── transaction/      # Transaction management
└── pool/            # Connection pooling
```

## Configuration

Database configurations are located in `/config/database/`:
- `oracle.config.json`
- `postgresql.config.json`
- `mysql.config.json`
