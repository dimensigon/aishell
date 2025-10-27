# Legacy Migration - AI-Shell Example

## Scenario: Migrating from Oracle to PostgreSQL

This example demonstrates a complete database migration from Oracle to PostgreSQL, including schema comparison, data validation, query translation, and zero-downtime migration strategies. Perfect for modernization projects and cloud migrations.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│               AI-Shell Migration Orchestrator                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────┐         Migration Flow      ┌─────────────┐│
│  │  Oracle Source  │ ────────────────────────────>│ PostgreSQL  ││
│  │  (Legacy)       │                              │ (Target)    ││
│  │                 │  1. Schema comparison        │             ││
│  │  - Production   │  2. Data validation          │ - Staging   ││
│  │  - Read-only    │  3. Incremental sync         │ - Test      ││
│  │                 │  4. Cut-over                 │             ││
│  └─────────────────┘                              └─────────────┘│
│         │                                                │         │
│         │                                                │         │
│         └────────────────┬───────────────────────────────┘         │
│                          │                                         │
│                 ┌────────▼─────────┐                              │
│                 │   Validation DB  │                              │
│                 │   (PostgreSQL)   │                              │
│                 │                  │                              │
│                 │ - Migration logs │                              │
│                 │ - Test results   │                              │
│                 │ - Rollback data  │                              │
│                 └──────────────────┘                              │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

## Migration Phases

### Phase 1: Assessment
- Schema analysis and comparison
- Incompatibility detection
- Migration complexity scoring
- Resource estimation

### Phase 2: Preparation
- Schema translation (Oracle → PostgreSQL)
- Query conversion
- Stored procedure migration
- Test environment setup

### Phase 3: Data Migration
- Initial bulk load
- Incremental sync
- Data validation
- Performance benchmarking

### Phase 4: Cut-Over
- Final sync
- Switch traffic
- Validation
- Rollback capability

## Key Features

- **Schema Comparison**: Automatic diff between Oracle and PostgreSQL
- **Query Translation**: Convert Oracle SQL to PostgreSQL
- **Data Validation**: Ensure data integrity post-migration
- **Zero-Downtime**: Incremental sync with minimal downtime
- **Rollback Plan**: Documented rollback procedures
- **Performance Testing**: Benchmark before/after
- **Compatibility Checks**: Identify Oracle-specific features

## Sample Scenarios

### 1. Schema Differences
```
"Compare schema between Oracle source and PostgreSQL target"
"Show Oracle-specific features that need conversion"
"Generate PostgreSQL equivalents for Oracle sequences"
```

### 2. Query Translation
```
"Convert this Oracle query to PostgreSQL: SELECT * FROM ..."
"Translate Oracle PL/SQL stored procedure to PL/pgSQL"
"Find Oracle-specific hints and suggest PostgreSQL alternatives"
```

### 3. Data Validation
```
"Validate row counts match between source and target"
"Check data integrity constraints after migration"
"Compare checksums for critical tables"
```

### 4. Performance Comparison
```
"Benchmark query performance: Oracle vs PostgreSQL"
"Identify queries that are slower after migration"
"Suggest PostgreSQL optimizations for converted queries"
```

## Migration Steps

```bash
# 1. Setup both databases
./scripts/setup.sh

# 2. Run assessment
./scripts/assess.sh

# 3. Prepare migration
./scripts/prepare.sh

# 4. Test migration (staging)
./scripts/migrate-test.sh

# 5. Validate results
./scripts/validate.sh

# 6. Production migration
./scripts/migrate-production.sh

# 7. Rollback (if needed)
./scripts/rollback.sh
```

## Quick Start

```bash
cd examples/legacy-migration
./scripts/setup.sh
./scripts/demo.sh
```

## Sample Data

- **Oracle Database**: 100K legacy records
- **Schema**: 50 tables, 200 columns
- **Stored Procedures**: 20 procedures
- **Views**: 15 views
- **Indexes**: 80 indexes
- **Constraints**: 40 foreign keys

## Common Migration Challenges

### 1. Data Type Conversion
```
Oracle NUMBER → PostgreSQL NUMERIC
Oracle VARCHAR2 → PostgreSQL VARCHAR
Oracle DATE → PostgreSQL TIMESTAMP
Oracle CLOB → PostgreSQL TEXT
Oracle BLOB → PostgreSQL BYTEA
```

### 2. Syntax Differences
```
Oracle: NVL() → PostgreSQL: COALESCE()
Oracle: SYSDATE → PostgreSQL: CURRENT_TIMESTAMP
Oracle: DECODE() → PostgreSQL: CASE
Oracle: ROWNUM → PostgreSQL: ROW_NUMBER()
Oracle: (+) joins → PostgreSQL: LEFT/RIGHT JOIN
```

### 3. Sequence Migration
```
Oracle: CREATE SEQUENCE → PostgreSQL: SERIAL or SEQUENCE
Oracle: seq.NEXTVAL → PostgreSQL: nextval('seq')
```

### 4. PL/SQL to PL/pgSQL
```
Oracle packages → PostgreSQL schemas + functions
Oracle triggers → PostgreSQL triggers (similar syntax)
Exception handling → Similar but different syntax
```

## Validation Checks

The migration includes comprehensive validation:

1. **Row Count Validation**: Ensure all rows migrated
2. **Data Integrity**: Check foreign keys and constraints
3. **Checksum Validation**: Verify data accuracy
4. **Query Results**: Compare query outputs
5. **Performance**: Benchmark critical queries
6. **Application Testing**: End-to-end tests

## Rollback Strategy

Complete rollback procedure included:

1. **Pre-Migration Backup**: Full Oracle backup
2. **Incremental Backups**: During migration
3. **Traffic Switch**: Easy rollback to Oracle
4. **Data Sync Reverse**: If needed
5. **Documentation**: Step-by-step rollback guide

## Performance Benchmarks

Example migration performance:

- **Schema Translation**: < 5 minutes
- **Initial Data Load**: ~1 hour per 100GB
- **Incremental Sync**: < 5 minutes
- **Validation**: ~10 minutes
- **Total Downtime**: < 15 minutes (with proper planning)

## AI-Shell Commands

```
# Assessment
"Analyze Oracle schema for PostgreSQL compatibility"
"Estimate migration complexity and duration"
"List Oracle features without PostgreSQL equivalents"

# Preparation
"Generate PostgreSQL DDL from Oracle schema"
"Convert Oracle PL/SQL to PL/pgSQL"
"Create migration plan with risk assessment"

# Migration
"Start incremental data sync"
"Monitor migration progress"
"Validate data integrity"

# Validation
"Compare row counts across all tables"
"Run data integrity checks"
"Benchmark query performance"

# Troubleshooting
"Find tables with mismatched row counts"
"Identify slow queries after migration"
"Show migration errors and suggested fixes"
```

## Success Criteria

Migration is considered successful when:

- ✅ All tables migrated with 100% row count match
- ✅ All constraints and indexes created
- ✅ All queries producing identical results
- ✅ Performance meets or exceeds Oracle
- ✅ Application tests passing
- ✅ Zero data loss
- ✅ Downtime < planned window

## Resources Provided

- Step-by-step migration guide
- Oracle to PostgreSQL conversion cheat sheet
- Validation SQL scripts
- Performance benchmarking tools
- Rollback procedures
- Common issues and solutions

[Full Documentation →](./README.md)
