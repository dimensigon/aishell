# Zero-Downtime Schema Migrations

Enterprise-grade database migration system with zero application downtime using the expand/contract pattern.

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Expand/Contract Pattern](#expandcontract-pattern)
- [Migration DSL](#migration-dsl)
- [CLI Commands](#cli-commands)
- [Common Patterns](#common-patterns)
- [Best Practices](#best-practices)
- [Safety Features](#safety-features)
- [Troubleshooting](#troubleshooting)

## Overview

The zero-downtime migration system enables safe database schema changes without interrupting application availability. It achieves this through:

- **Multi-phase migrations**: Break changes into discrete, safe steps
- **Expand/contract pattern**: Add before removing, never break compatibility
- **Dual-write capability**: Write to both old and new columns during transition
- **Automatic rollback**: Revert changes on failure
- **Concurrent operations**: Non-blocking index creation and updates
- **Lock management**: Avoid long-running table locks

## Core Concepts

### Migration Phases

Every migration consists of one or more phases executed sequentially:

1. **Expand Phase**: Add new schema elements (columns, indexes)
2. **Migration Phase**: Backfill data, enable dual-writes
3. **Contract Phase**: Remove old schema elements

### Zero-Downtime Requirements

To achieve zero downtime:

1. Never drop tables or columns in use
2. Always add columns as NULL initially
3. Use concurrent index creation
4. Batch large data migrations
5. Deploy code changes between migration phases

## Expand/Contract Pattern

### Pattern Overview

The expand/contract pattern ensures backward compatibility throughout migrations:

```
Current State → Expanded State → Contracted State
     (v1)            (v1 + v2)          (v2)
```

### Example: Adding a Column

#### Phase 1: Expand (Add Column)
```sql
ALTER TABLE users ADD COLUMN email_verified BOOLEAN NULL;
```
- Application v1 still works (ignores new column)
- Application v2 can use new column

#### Phase 2: Migrate (Backfill)
```sql
UPDATE users SET email_verified = false WHERE email_verified IS NULL;
```
- Populate existing rows with default value

#### Phase 3: Contract (Make NOT NULL)
```sql
ALTER TABLE users ALTER COLUMN email_verified SET NOT NULL;
```
- Enforce constraint after backfill complete

### Example: Removing a Column

#### Phase 1: Stop Writing
- Deploy application that no longer writes to column
- Old column remains readable

#### Phase 2: Remove Reads
- Deploy application that no longer reads column
- Column exists but unused

#### Phase 3: Drop Column
```sql
ALTER TABLE users DROP COLUMN deprecated_field;
```
- Safe to remove as no code references it

### Example: Renaming a Column

#### Phase 1: Add New Column
```sql
ALTER TABLE users ADD COLUMN new_name VARCHAR(255) NULL;
```

#### Phase 2: Enable Dual-Write
- Application writes to both columns
- Ensures consistency during transition

#### Phase 3: Backfill
```sql
UPDATE users SET new_name = old_name WHERE new_name IS NULL;
```

#### Phase 4: Switch Reads
- Deploy application that reads from new_name
- Still writes to both columns

#### Phase 5: Drop Old Column
```sql
ALTER TABLE users DROP COLUMN old_name;
```

### Example: Changing Column Type

#### Phase 1: Add New Column
```sql
ALTER TABLE users ADD COLUMN age_new INTEGER NULL;
```

#### Phase 2: Dual-Write with Conversion
- Write to both columns with type conversion
```sql
-- Application logic
INSERT INTO users (age, age_new) VALUES ('25', 25);
```

#### Phase 3: Backfill and Validate
```sql
UPDATE users SET age_new = CAST(age AS INTEGER);
-- Validate conversion
SELECT COUNT(*) FROM users WHERE age_new IS NULL;
```

#### Phase 4: Switch to New Column
```sql
ALTER TABLE users DROP COLUMN age;
ALTER TABLE users RENAME COLUMN age_new TO age;
```

## Migration DSL

### Basic Usage

```typescript
import { migration } from './migration-dsl';

// Create migration
const builder = migration('add-email-verified')
  .phase('Add column as nullable')
  .addColumn('users', 'email_verified', 'BOOLEAN')
  .nullable()
  .withDefault(false)
  .validate()

  .phase('Backfill existing rows')
  .backfill('users', "email_verified = false")
  .validateBackfill('users', 'email_verified')

  .phase('Make column NOT NULL')
  .makeNonNullable();

// Save to file
await builder.commit('./migrations');
```

### Fluent API Methods

#### Column Operations
```typescript
.addColumn(table, column, dataType)
.dropColumn(table, column)
.renameColumn(table, oldColumn, newColumn, dataType)
.changeColumnType(table, column, oldType, newType)
```

#### Column Modifiers
```typescript
.nullable()
.notNullable()
.withDefault(value)
```

#### Index Operations
```typescript
.addIndex(table, indexName, columns, { concurrent: true })
.dropIndex(indexName, table, { concurrent: true })
```

#### Constraint Operations
```typescript
.addConstraint(table, constraintName, sql)
.dropConstraint(table, constraintName)
```

#### Data Operations
```typescript
.backfill(table, sql)
.enableDualWrite(table, oldColumn, newColumn)
.disableDualWrite(table, oldColumn, newColumn)
```

#### Validation
```typescript
.validateColumnExists(table, column)
.validateColumnNotExists(table, column)
.validateBackfill(table, column)
.validateDataIntegrity(sql, errorMessage)
```

#### Metadata
```typescript
.setAuthor(name)
.addTags(...tags)
.setTimeout(milliseconds)
```

### Migration File Format (YAML)

```yaml
migration:
  name: add-user-preferences
  database: postgresql
  description: Add user preferences column
  phases:
    - phase: 1
      description: Add preferences column
      operations:
        - type: add_column
          table: users
          column: preferences
          dataType: JSONB
          nullable: true
      validation:
        - check: column_exists
          table: users
          column: preferences
      rollbackOperations:
        - type: drop_column
          table: users
          column: preferences

    - phase: 2
      description: Backfill default preferences
      operations:
        - type: backfill
          table: users
          sql: "preferences = '{}'::jsonb"
      validation:
        - check: custom
          sql: "SELECT COUNT(*) FROM users WHERE preferences IS NULL"
          errorMessage: "Backfill incomplete"
```

## CLI Commands

### Create Migration

```bash
# Create from template
ai-shell migrate create add-email-verified \
  --type add-column \
  --table users \
  --column email_verified \
  --data-type BOOLEAN

# Create custom migration
ai-shell migrate create my-custom-migration
```

### Plan Migration

```bash
# Show execution plan
ai-shell migrate plan migrations/20250128_add_email_verified.yaml
```

Output:
```
Analyzing migration: add-email-verified

Migration: add-email-verified
Database: postgresql
Phases: 3
Estimated Duration: 1500ms

Risks:
  ⚠ Phase 2: Backfill operation may lock table

Execution Plan:

Phase 1: Add column as nullable
  Estimated duration: 100ms

  1. ALTER TABLE users ADD COLUMN email_verified BOOLEAN NULL DEFAULT false

Phase 2: Backfill existing rows
  Estimated duration: 1000ms

  1. UPDATE users SET email_verified = false

Phase 3: Make column NOT NULL
  Estimated duration: 400ms

  1. ALTER TABLE users ALTER COLUMN email_verified SET NOT NULL
```

### Apply Migration

```bash
# Apply all phases
ai-shell migrate apply migrations/20250128_add_email_verified.yaml

# Apply specific phase
ai-shell migrate apply migrations/20250128_add_email_verified.yaml --phase 1

# Dry run (show what would execute)
ai-shell migrate apply migrations/20250128_add_email_verified.yaml --dry-run

# Skip automatic backup
ai-shell migrate apply migrations/20250128_add_email_verified.yaml --skip-backup

# Non-interactive
ai-shell migrate apply migrations/20250128_add_email_verified.yaml -y
```

### Verify Migration

```bash
# Check migration safety
ai-shell migrate verify migrations/20250128_add_email_verified.yaml
```

Output:
```
Verifying migration: add-email-verified

✓ Migration appears safe

Warnings:
  ⚠ Phase 2: Backfill operation - consider batching for large tables

Recommendations:
  ℹ Use batch updates with LIMIT clauses for better performance
```

### Migration Status

```bash
# Show current status
ai-shell migrate status
```

Output:
```
Migration Status

Last Migration:
  Name: add-email-verified
  Execution ID: exec-1738051200000-abc123
  Status: completed
  Phase: 3/3
  Started: 2025-01-28 10:00:00
  Completed: 2025-01-28 10:00:02
  Duration: 1523ms

Summary:
  Total executions: 5
  Completed: 4
  Failed: 1
  Rolled back: 0
```

### List Migrations

```bash
# List all migration files
ai-shell migrate list

# Show applied migrations only
ai-shell migrate list --all
```

### Migration History

```bash
# Show execution history
ai-shell migrate history

# Limit results
ai-shell migrate history --limit 5
```

### Generate from Pattern

```bash
# Add nullable column
ai-shell migrate generate add-nullable-column \
  --table users \
  --column bio \
  --data-type TEXT

# Add required column
ai-shell migrate generate add-required-column \
  --table users \
  --column status \
  --data-type VARCHAR(50) \
  --default active

# Remove column
ai-shell migrate generate remove-column \
  --table users \
  --column deprecated_field

# Rename column
ai-shell migrate generate rename-column \
  --table users \
  --old-column old_name \
  --new-column new_name \
  --data-type VARCHAR(255)

# Change type
ai-shell migrate generate change-type \
  --table users \
  --column age \
  --old-type VARCHAR(10) \
  --new-type INTEGER

# Add index
ai-shell migrate generate add-index \
  --table users \
  --columns email,tenant_id

# Add foreign key
ai-shell migrate generate add-foreign-key \
  --table orders \
  --column user_id \
  --ref-table users

# Add unique constraint
ai-shell migrate generate add-unique \
  --table users \
  --columns email,tenant_id
```

## Common Patterns

### Pattern 1: Add NOT NULL Column

```typescript
import { MigrationPatterns } from './migration-dsl';

const migration = MigrationPatterns.addRequiredColumn(
  'users',
  'status',
  'VARCHAR(50)',
  'active'
);
```

Generates:
1. Add column as nullable with default
2. Backfill existing rows
3. Add NOT NULL constraint

### Pattern 2: Remove Column Safely

```typescript
const migration = MigrationPatterns.removeColumn(
  'users',
  'deprecated_field'
);
```

Generates:
1. Stop writing to column (code deployment)
2. Remove from queries (code deployment)
3. Drop column

### Pattern 3: Rename Column

```typescript
const migration = MigrationPatterns.safeRenameColumn(
  'users',
  'old_name',
  'new_name',
  'VARCHAR(255)'
);
```

Generates:
1. Add new column
2. Enable dual-write
3. Backfill data
4. Switch reads
5. Drop old column

### Pattern 4: Change Column Type

```typescript
const migration = MigrationPatterns.changeColumnType(
  'users',
  'age',
  'VARCHAR(10)',
  'INTEGER'
);
```

Generates:
1. Add new column with new type
2. Dual-write with type conversion
3. Backfill and validate
4. Switch to new column
5. Drop old column

### Pattern 5: Add Concurrent Index

```typescript
const migration = MigrationPatterns.addConcurrentIndex(
  'users',
  'idx_email',
  ['email']
);
```

Uses PostgreSQL `CREATE INDEX CONCURRENTLY` to avoid table locks.

### Pattern 6: Split Column

```typescript
const migration = MigrationPatterns.splitColumn(
  'users',
  'full_name',
  [
    { name: 'first_name', type: 'VARCHAR(100)', extract: "SPLIT_PART(full_name, ' ', 1)" },
    { name: 'last_name', type: 'VARCHAR(100)', extract: "SPLIT_PART(full_name, ' ', 2)" }
  ]
);
```

### Pattern 7: Merge Columns

```typescript
const migration = MigrationPatterns.mergeColumns(
  'users',
  ['first_name', 'last_name'],
  'full_name',
  'VARCHAR(200)',
  "first_name || ' ' || last_name"
);
```

## Best Practices

### 1. Always Use Phases

Break complex migrations into discrete phases:

```typescript
migration('complex-change')
  .phase('Phase 1: Expand')
  .addColumn('users', 'new_col', 'TEXT')

  .phase('Phase 2: Migrate')
  .enableDualWrite('users', 'old_col', 'new_col')
  .backfill('users', 'new_col = old_col')

  .phase('Phase 3: Contract')
  .dropColumn('users', 'old_col');
```

### 2. Add Columns as NULL

Never add NOT NULL columns directly:

```typescript
// ❌ BAD
.addColumn('users', 'required_field', 'VARCHAR(100)')
.notNullable()

// ✅ GOOD
.addColumn('users', 'required_field', 'VARCHAR(100)')
.nullable()
.withDefault('default_value')
// ... later phase ...
.makeNonNullable()
```

### 3. Use Concurrent Index Creation

Always use concurrent index creation for production:

```typescript
// ❌ BAD
.addIndex('users', 'idx_email', ['email'], { concurrent: false })

// ✅ GOOD
.addIndex('users', 'idx_email', ['email'], { concurrent: true })
```

### 4. Batch Large Backfills

For large tables, batch updates:

```typescript
.customSQL(`
  DO $$
  DECLARE
    batch_size INT := 10000;
    rows_updated INT;
  BEGIN
    LOOP
      UPDATE users
      SET email_verified = false
      WHERE id IN (
        SELECT id FROM users
        WHERE email_verified IS NULL
        LIMIT batch_size
      );

      GET DIAGNOSTICS rows_updated = ROW_COUNT;
      EXIT WHEN rows_updated = 0;

      PERFORM pg_sleep(0.1); -- Pause between batches
    END LOOP;
  END $$;
`)
```

### 5. Always Add Validations

Verify migration results:

```typescript
.backfill('users', "status = 'active'")
.validateBackfill('users', 'status')
.validateDataIntegrity(
  "SELECT COUNT(*) FROM users WHERE status NOT IN ('active', 'inactive')",
  'Invalid status values found'
)
```

### 6. Document Deployment Steps

```typescript
migration('complex-migration')
  .setAuthor('team@company.com')
  .addTags('requires-deployment', 'breaking-change')
  .phase('Phase 1')
  // ... operations ...
```

### 7. Test Migrations

Always test in staging:

```bash
# Test in staging
ai-shell migrate apply migration.yaml --dry-run
ai-shell migrate verify migration.yaml
ai-shell migrate apply migration.yaml

# Verify application compatibility
# Run test suite

# Apply in production
ai-shell migrate apply migration.yaml -y
```

### 8. Monitor Progress

Watch migration execution:

```bash
# Terminal 1: Apply migration
ai-shell migrate apply long-running-migration.yaml

# Terminal 2: Monitor status
watch -n 1 'ai-shell migrate status'

# Terminal 3: Monitor database
watch -n 1 'psql -c "SELECT * FROM pg_stat_activity"'
```

### 9. Plan Rollback Strategy

Always have a rollback plan:

```typescript
migration('risky-change')
  .phase('Phase 1')
  .addColumn('users', 'new_field', 'TEXT')
  // Rollback automatically generated

  .phase('Phase 2')
  .customSQL('complex operation')
  // Manual rollback
  .customSQL('rollback operation')
```

### 10. Use Lock Timeouts

Prevent long-running locks:

```typescript
.phase('Quick operation')
.setTimeout(5000) // 5 second timeout
.addIndex('users', 'idx_quick', ['field'])
```

## Safety Features

### Automatic Backups

Before every migration:

```bash
# Automatic backup created
ai-shell migrate apply migration.yaml

# Skip if needed
ai-shell migrate apply migration.yaml --skip-backup
```

### Point-in-Time Snapshots

Database snapshots before migration:

```typescript
// Automatic snapshot
const execution = await engine.executeMigration(filepath);

// Access snapshot ID
console.log(execution.snapshotId);

// Restore if needed
await engine.restoreSnapshot(execution.snapshotId);
```

### Automatic Rollback

On failure, automatically rollback:

```yaml
phases:
  - phase: 1
    operations:
      - type: add_column
        table: users
        column: test
    rollbackOperations:  # Auto-executed on failure
      - type: drop_column
        table: users
        column: test
```

### Lock Timeout Management

Prevent long-running locks:

```typescript
// Set lock timeout per phase
.phase('Fast operation')
.setTimeout(5000)  // 5 seconds max
```

### Validation Rules

Verify migration success:

```typescript
.validateColumnExists('users', 'new_column')
.validateBackfill('users', 'new_column')
.validateDataIntegrity(sql, errorMessage)
```

### Dry Run Mode

Test without changes:

```bash
ai-shell migrate apply migration.yaml --dry-run
```

## Troubleshooting

### Migration Failed Mid-Execution

```bash
# Check status
ai-shell migrate status

# View error details
ai-shell migrate history --limit 1

# Restore from backup
ai-shell backup list
ai-shell backup restore backup-<id>
```

### Table Locked During Migration

```bash
# Check for blocking queries
psql -c "SELECT * FROM pg_stat_activity WHERE state != 'idle'"

# Cancel blocking query
psql -c "SELECT pg_cancel_backend(pid) FROM pg_stat_activity WHERE ..."

# Retry migration with shorter timeout
ai-shell migrate apply migration.yaml --phase <failed-phase>
```

### Backfill Taking Too Long

```typescript
// Convert to batched update
.customSQL(`
  -- Batch update with progress tracking
  CREATE TABLE IF NOT EXISTS backfill_progress (
    last_id BIGINT
  );

  DO $$
  DECLARE
    batch_size INT := 10000;
    last_processed_id BIGINT := 0;
  BEGIN
    SELECT COALESCE(last_id, 0) INTO last_processed_id FROM backfill_progress LIMIT 1;

    LOOP
      UPDATE users
      SET new_column = old_column
      WHERE id > last_processed_id
        AND id <= last_processed_id + batch_size
        AND new_column IS NULL;

      UPDATE backfill_progress SET last_id = last_processed_id + batch_size;

      last_processed_id := last_processed_id + batch_size;

      EXIT WHEN (SELECT COUNT(*) FROM users WHERE id > last_processed_id AND new_column IS NULL) = 0;

      PERFORM pg_sleep(0.5);
    END LOOP;
  END $$;
`)
```

### Migration Verification Failed

```bash
# Get detailed verification report
ai-shell migrate verify migration.yaml

# Fix issues in migration file
# Re-verify
ai-shell migrate verify migration.yaml
```

### Rollback Not Working

```bash
# Manual rollback using backup
ai-shell backup restore <backup-id>

# Or manually execute rollback SQL
psql -c "ALTER TABLE users DROP COLUMN new_column"
```

## Database-Specific Notes

### PostgreSQL

- Supports `CREATE INDEX CONCURRENTLY`
- Use `SET lock_timeout` for safety
- Consider `pg_repack` for large table restructuring

### MySQL

- No concurrent index creation
- Use `pt-online-schema-change` for large tables
- Consider `ALTER TABLE ... ALGORITHM=INPLACE`

### SQLite

- Limited ALTER TABLE support
- Requires table recreation for many operations
- Use transactions carefully

## Performance Considerations

### Index Creation

```typescript
// Fast: Concurrent index (PostgreSQL)
.addIndex('users', 'idx_email', ['email'], { concurrent: true })

// Slow: Standard index (locks table)
.addIndex('users', 'idx_email', ['email'], { concurrent: false })
```

### Backfill Operations

```typescript
// Fast: Batched updates
.customSQL(`
  UPDATE users SET status = 'active'
  WHERE id IN (SELECT id FROM users WHERE status IS NULL LIMIT 10000)
`)

// Slow: Single update
.backfill('users', "status = 'active'")
```

### Data Type Changes

```typescript
// Fast: Compatible type change
.changeColumnType('users', 'age', 'VARCHAR(10)', 'TEXT')

// Slow: Incompatible type change (requires full scan)
.changeColumnType('users', 'age', 'VARCHAR(10)', 'INTEGER')
```

## Advanced Topics

### Custom Migration Logic

```typescript
migration('custom-logic')
  .phase('Custom operation')
  .customSQL(`
    -- Complex SQL logic
    WITH updated_users AS (
      UPDATE users
      SET status = CASE
        WHEN last_login > NOW() - INTERVAL '30 days' THEN 'active'
        ELSE 'inactive'
      END
      RETURNING id
    )
    INSERT INTO audit_log (user_id, action)
    SELECT id, 'status_updated' FROM updated_users;
  `);
```

### Multi-Database Migrations

```typescript
// PostgreSQL-specific
migration('pg-specific', DatabaseType.POSTGRESQL)
  .phase('Use PostgreSQL features')
  .customSQL('CREATE INDEX CONCURRENTLY ...')

// MySQL-specific
migration('mysql-specific', DatabaseType.MYSQL)
  .phase('Use MySQL features')
  .customSQL('ALTER TABLE ... ALGORITHM=INPLACE')
```

### Integration with CI/CD

```bash
# In CI/CD pipeline

# 1. Verify migration
ai-shell migrate verify migrations/new-migration.yaml
if [ $? -ne 0 ]; then
  echo "Migration verification failed"
  exit 1
fi

# 2. Apply in staging
ai-shell migrate apply migrations/new-migration.yaml -y

# 3. Run tests
npm test

# 4. Apply in production (if tests pass)
ai-shell migrate apply migrations/new-migration.yaml -y
```

## Resources

- [Migration Patterns Library](./migration-patterns-library.md)
- [Database Best Practices](../best-practices.md)
- [Backup and Recovery](./backup-recovery.md)
- [Performance Optimization](./performance-optimization.md)
