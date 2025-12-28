# Migration Patterns Library

A comprehensive library of zero-downtime migration patterns for common database operations.

## Table of Contents

- [Column Operations](#column-operations)
- [Index Operations](#index-operations)
- [Constraint Operations](#constraint-operations)
- [Table Operations](#table-operations)
- [Data Transformation](#data-transformation)
- [Schema Refactoring](#schema-refactoring)
- [Performance Patterns](#performance-patterns)
- [Anti-Patterns](#anti-patterns)

## Column Operations

### Pattern 1: Add Nullable Column

**Use Case**: Add a new optional column to an existing table.

**Safety**: ✅ Safe - No downtime required

**Code**:
```typescript
import { MigrationPatterns } from './migration-dsl';

const migration = MigrationPatterns.addNullableColumn(
  'users',
  'bio',
  'TEXT',
  'No bio provided' // optional default
);
```

**Generated SQL**:
```sql
-- Phase 1: Add column
ALTER TABLE users ADD COLUMN bio TEXT NULL DEFAULT 'No bio provided';
```

**Phases**: 1

**Deployment Steps**:
1. Run migration
2. Deploy application code that can use new column

---

### Pattern 2: Add Required (NOT NULL) Column

**Use Case**: Add a new required column with a default value.

**Safety**: ✅ Safe - Uses expand/contract pattern

**Code**:
```typescript
const migration = MigrationPatterns.addRequiredColumn(
  'users',
  'status',
  'VARCHAR(50)',
  'active'
);
```

**Generated SQL**:
```sql
-- Phase 1: Add column as nullable with default
ALTER TABLE users ADD COLUMN status VARCHAR(50) NULL DEFAULT 'active';

-- Phase 2: Backfill existing rows
UPDATE users SET status = 'active' WHERE status IS NULL;

-- Phase 3: Make column NOT NULL
ALTER TABLE users ALTER COLUMN status SET NOT NULL;
```

**Phases**: 3

**Deployment Steps**:
1. Run Phase 1 → Deploy app that writes to new column
2. Run Phase 2 → Wait for backfill
3. Run Phase 3 → Column is now required

---

### Pattern 3: Remove Column Safely

**Use Case**: Remove a column that's no longer needed.

**Safety**: ✅ Safe - Ensures no code references column

**Code**:
```typescript
const migration = MigrationPatterns.removeColumn('users', 'deprecated_field');
```

**Generated SQL**:
```sql
-- Phase 1: Stop writing (code change required)
-- No SQL

-- Phase 2: Remove from queries (code change required)
-- No SQL

-- Phase 3: Drop column
ALTER TABLE users DROP COLUMN deprecated_field;
```

**Phases**: 3

**Deployment Steps**:
1. Deploy app that stops writing to column
2. Deploy app that stops reading from column
3. Run Phase 3 → Column dropped

---

### Pattern 4: Rename Column

**Use Case**: Rename a column while maintaining zero downtime.

**Safety**: ✅ Safe - Uses dual-write pattern

**Code**:
```typescript
const migration = MigrationPatterns.safeRenameColumn(
  'users',
  'old_name',
  'new_name',
  'VARCHAR(255)'
);
```

**Generated SQL**:
```sql
-- Phase 1: Add new column
ALTER TABLE users ADD COLUMN new_name VARCHAR(255) NULL;

-- Phase 2: Enable dual-write (application change)
-- Write to both columns

-- Phase 3: Backfill new column
UPDATE users SET new_name = old_name WHERE new_name IS NULL;

-- Phase 4: Switch reads to new column (application change)
-- Read from new_name, write to both

-- Phase 5: Drop old column
ALTER TABLE users DROP COLUMN old_name;
```

**Phases**: 5

**Deployment Steps**:
1. Run Phase 1
2. Deploy app with dual-write → Run Phase 3
3. Deploy app that reads from new_name → Run Phase 5

---

### Pattern 5: Change Column Type

**Use Case**: Change the data type of a column.

**Safety**: ⚠️ Use with caution - Requires data validation

**Code**:
```typescript
const migration = MigrationPatterns.changeColumnType(
  'users',
  'age',
  'VARCHAR(10)',
  'INTEGER'
);
```

**Generated SQL**:
```sql
-- Phase 1: Add new column with new type
ALTER TABLE users ADD COLUMN age_new INTEGER NULL;

-- Phase 2: Enable dual-write with type conversion
-- Write to both with conversion

-- Phase 3: Backfill and validate
UPDATE users SET age_new = CAST(age AS INTEGER);
-- Validate: SELECT COUNT(*) FROM users WHERE age_new IS NULL;

-- Phase 4: Switch to new column
ALTER TABLE users DROP COLUMN age;
ALTER TABLE users RENAME COLUMN age_new TO age;
```

**Phases**: 4

**Deployment Steps**:
1. Run Phase 1
2. Deploy app with type conversion → Run Phase 3
3. Validate data → Run Phase 4

---

### Pattern 6: Make Column Nullable

**Use Case**: Remove NOT NULL constraint from a column.

**Safety**: ✅ Safe - Always safe to relax constraints

**Code**:
```typescript
migration('make-nullable')
  .phase('Remove NOT NULL constraint')
  .customSQL('ALTER TABLE users ALTER COLUMN bio DROP NOT NULL');
```

**Phases**: 1

---

### Pattern 7: Make Column NOT NULL

**Use Case**: Add NOT NULL constraint to an existing column.

**Safety**: ⚠️ Requires backfill

**Code**:
```typescript
migration('make-not-null')
  .phase('Backfill NULL values')
  .backfill('users', "bio = 'No bio' WHERE bio IS NULL")
  .validateBackfill('users', 'bio')

  .phase('Add NOT NULL constraint')
  .customSQL('ALTER TABLE users ALTER COLUMN bio SET NOT NULL');
```

**Phases**: 2

---

## Index Operations

### Pattern 8: Add Concurrent Index

**Use Case**: Add an index without blocking writes.

**Safety**: ✅ Safe - Uses CONCURRENTLY (PostgreSQL)

**Code**:
```typescript
const migration = MigrationPatterns.addConcurrentIndex(
  'users',
  'idx_users_email',
  ['email']
);
```

**Generated SQL**:
```sql
-- PostgreSQL
CREATE INDEX CONCURRENTLY idx_users_email ON users (email);

-- MySQL (no CONCURRENTLY support)
CREATE INDEX idx_users_email ON users (email);
```

**Phases**: 1

**Notes**:
- PostgreSQL: Non-blocking
- MySQL: May lock table (use pt-online-schema-change for large tables)
- SQLite: Locks table

---

### Pattern 9: Add Composite Index

**Use Case**: Create index on multiple columns.

**Safety**: ✅ Safe with CONCURRENTLY

**Code**:
```typescript
migration('add-composite-index')
  .phase('Create index')
  .addIndex('orders', 'idx_orders_user_date', ['user_id', 'created_at'], {
    concurrent: true
  });
```

**Generated SQL**:
```sql
CREATE INDEX CONCURRENTLY idx_orders_user_date ON orders (user_id, created_at);
```

**Phases**: 1

---

### Pattern 10: Drop Index

**Use Case**: Remove an unused index.

**Safety**: ✅ Safe - Can drop concurrently

**Code**:
```typescript
migration('drop-index')
  .phase('Drop index')
  .dropIndex('idx_old_index', 'users', { concurrent: true });
```

**Generated SQL**:
```sql
-- PostgreSQL
DROP INDEX CONCURRENTLY idx_old_index;

-- MySQL
DROP INDEX idx_old_index ON users;
```

**Phases**: 1

---

### Pattern 11: Replace Index

**Use Case**: Replace an existing index with a better one.

**Safety**: ✅ Safe - Add before drop

**Code**:
```typescript
migration('replace-index')
  .phase('Add new index')
  .addIndex('users', 'idx_users_email_new', ['email', 'status'], {
    concurrent: true
  })

  .phase('Drop old index')
  .dropIndex('idx_users_email', 'users', { concurrent: true });
```

**Phases**: 2

---

## Constraint Operations

### Pattern 12: Add Foreign Key

**Use Case**: Add referential integrity constraint.

**Safety**: ⚠️ May lock tables - validate data first

**Code**:
```typescript
const migration = MigrationPatterns.addForeignKey(
  'orders',
  'user_id',
  'users',
  'id'
);
```

**Generated SQL**:
```sql
ALTER TABLE orders
ADD CONSTRAINT fk_orders_user_id
FOREIGN KEY (user_id) REFERENCES users(id);
```

**Phases**: 1

**Best Practice**:
```typescript
migration('add-foreign-key-safe')
  .phase('Validate data')
  .validateDataIntegrity(`
    SELECT COUNT(*) FROM orders o
    LEFT JOIN users u ON o.user_id = u.id
    WHERE u.id IS NULL
  `, 'Orphaned orders found')

  .phase('Add constraint')
  .addConstraint('orders', 'fk_orders_user_id',
    'FOREIGN KEY (user_id) REFERENCES users(id)');
```

---

### Pattern 13: Add Unique Constraint

**Use Case**: Enforce uniqueness on column(s).

**Safety**: ⚠️ Requires data validation

**Code**:
```typescript
const migration = MigrationPatterns.addUniqueConstraint(
  'users',
  ['email', 'tenant_id']
);
```

**Generated SQL**:
```sql
ALTER TABLE users ADD CONSTRAINT uq_users_email_tenant_id UNIQUE (email, tenant_id);
```

**Phases**: 1

**Best Practice**:
```typescript
migration('add-unique-safe')
  .phase('Find duplicates')
  .validateDataIntegrity(`
    SELECT email, tenant_id, COUNT(*)
    FROM users
    GROUP BY email, tenant_id
    HAVING COUNT(*) > 1
  `, 'Duplicate records found')

  .phase('Add constraint')
  .addConstraint('users', 'uq_users_email_tenant_id',
    'UNIQUE (email, tenant_id)');
```

---

### Pattern 14: Add Check Constraint

**Use Case**: Enforce data validation rules.

**Safety**: ⚠️ Validate existing data first

**Code**:
```typescript
migration('add-check-constraint')
  .phase('Validate existing data')
  .validateDataIntegrity(`
    SELECT COUNT(*) FROM users WHERE age < 0 OR age > 150
  `, 'Invalid age values found')

  .phase('Add constraint')
  .addConstraint('users', 'chk_users_age',
    'CHECK (age >= 0 AND age <= 150)');
```

**Phases**: 2

---

### Pattern 15: Drop Constraint

**Use Case**: Remove an unnecessary constraint.

**Safety**: ✅ Safe - Relaxing constraints is always safe

**Code**:
```typescript
migration('drop-constraint')
  .phase('Drop constraint')
  .dropConstraint('users', 'chk_old_constraint');
```

**Phases**: 1

---

## Table Operations

### Pattern 16: Create Table

**Use Case**: Add a new table.

**Safety**: ✅ Safe - No existing data affected

**Code**:
```typescript
migration('create-audit-log')
  .phase('Create table')
  .customSQL(`
    CREATE TABLE audit_log (
      id BIGSERIAL PRIMARY KEY,
      user_id BIGINT NOT NULL,
      action VARCHAR(100) NOT NULL,
      metadata JSONB,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id)
    )
  `)

  .phase('Add indexes')
  .addIndex('audit_log', 'idx_audit_user_id', ['user_id'], { concurrent: true })
  .addIndex('audit_log', 'idx_audit_created', ['created_at'], { concurrent: true });
```

**Phases**: 2

---

### Pattern 17: Drop Table

**Use Case**: Remove an obsolete table.

**Safety**: ⚠️ Ensure no code references table

**Code**:
```typescript
migration('drop-table')
  .phase('Verify no references')
  // Code deployment: Remove all table references

  .phase('Drop table')
  .customSQL('DROP TABLE IF EXISTS obsolete_table CASCADE');
```

**Phases**: 2

---

### Pattern 18: Rename Table

**Use Case**: Rename a table for better naming.

**Safety**: ⚠️ Requires coordinated deployment

**Code**:
```typescript
migration('rename-table')
  .phase('Create view with old name')
  .customSQL('ALTER TABLE old_name RENAME TO new_name')
  .customSQL('CREATE VIEW old_name AS SELECT * FROM new_name')

  .phase('Update application')
  // Deploy app using new_name

  .phase('Drop view')
  .customSQL('DROP VIEW old_name');
```

**Phases**: 3

---

## Data Transformation

### Pattern 19: Split Column

**Use Case**: Split one column into multiple columns.

**Safety**: ⚠️ Requires data validation

**Code**:
```typescript
const migration = MigrationPatterns.splitColumn(
  'users',
  'full_name',
  [
    {
      name: 'first_name',
      type: 'VARCHAR(100)',
      extract: "SPLIT_PART(full_name, ' ', 1)"
    },
    {
      name: 'last_name',
      type: 'VARCHAR(100)',
      extract: "SPLIT_PART(full_name, ' ', 2)"
    }
  ]
);
```

**Generated Phases**:
1. Add first_name and last_name columns
2. Backfill from full_name
3. Validate data
4. Drop full_name column

---

### Pattern 20: Merge Columns

**Use Case**: Combine multiple columns into one.

**Safety**: ⚠️ Requires data validation

**Code**:
```typescript
const migration = MigrationPatterns.mergeColumns(
  'users',
  ['first_name', 'last_name'],
  'full_name',
  'VARCHAR(200)',
  "first_name || ' ' || last_name"
);
```

**Generated Phases**:
1. Add full_name column
2. Backfill merged data
3. Validate
4. Drop source columns

---

### Pattern 21: Normalize Data

**Use Case**: Extract repeated data into separate table.

**Safety**: ⚠️ Complex - requires careful planning

**Code**:
```typescript
migration('normalize-countries')
  .phase('Create countries table')
  .customSQL(`
    CREATE TABLE countries (
      id SERIAL PRIMARY KEY,
      code VARCHAR(2) UNIQUE NOT NULL,
      name VARCHAR(100) NOT NULL
    )
  `)

  .phase('Populate countries')
  .customSQL(`
    INSERT INTO countries (code, name)
    SELECT DISTINCT country_code, country_name
    FROM users
    WHERE country_code IS NOT NULL
  `)

  .phase('Add country_id to users')
  .addColumn('users', 'country_id', 'INTEGER')
  .nullable()

  .phase('Backfill country_id')
  .backfill('users', `
    country_id = (
      SELECT id FROM countries
      WHERE countries.code = users.country_code
    )
  `)

  .phase('Add foreign key')
  .addConstraint('users', 'fk_users_country',
    'FOREIGN KEY (country_id) REFERENCES countries(id)')

  .phase('Drop old columns')
  .dropColumn('users', 'country_code')
  .dropColumn('users', 'country_name');
```

**Phases**: 6

---

### Pattern 22: Denormalize Data

**Use Case**: Copy frequently accessed data to avoid joins.

**Safety**: ⚠️ Requires maintaining consistency

**Code**:
```typescript
migration('denormalize-user-name')
  .phase('Add denormalized column')
  .addColumn('orders', 'user_name', 'VARCHAR(200)')
  .nullable()

  .phase('Backfill from join')
  .backfill('orders', `
    user_name = (
      SELECT name FROM users WHERE users.id = orders.user_id
    )
  `)

  .phase('Add trigger to maintain consistency')
  .customSQL(`
    CREATE OR REPLACE FUNCTION update_order_user_name()
    RETURNS TRIGGER AS $$
    BEGIN
      UPDATE orders
      SET user_name = NEW.name
      WHERE user_id = NEW.id;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_update_order_user_name
    AFTER UPDATE OF name ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_order_user_name();
  `);
```

**Phases**: 3

---

## Schema Refactoring

### Pattern 23: Add Enum Column

**Use Case**: Add a column with predefined values.

**Safety**: ✅ Safe with proper default

**PostgreSQL with ENUM**:
```typescript
migration('add-status-enum')
  .phase('Create ENUM type')
  .customSQL(`
    CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended')
  `)

  .phase('Add column')
  .customSQL(`
    ALTER TABLE users
    ADD COLUMN status user_status DEFAULT 'active'
  `);
```

**Universal with VARCHAR**:
```typescript
migration('add-status-varchar')
  .phase('Add column with check constraint')
  .addColumn('users', 'status', 'VARCHAR(50)')
  .withDefault('active')
  .addConstraint('users', 'chk_user_status',
    "CHECK (status IN ('active', 'inactive', 'suspended'))");
```

---

### Pattern 24: Add JSON/JSONB Column

**Use Case**: Add flexible schema column.

**Safety**: ✅ Safe with NULL default

**Code**:
```typescript
migration('add-preferences')
  .phase('Add JSONB column')
  .addColumn('users', 'preferences', 'JSONB')
  .nullable()
  .withDefault("'{}'::jsonb")

  .phase('Add GIN index for queries')
  .addIndex('users', 'idx_users_preferences', ['preferences'], {
    concurrent: true
  });
```

**Phases**: 2

---

### Pattern 25: Add Timestamp Columns

**Use Case**: Add audit timestamp columns.

**Safety**: ✅ Safe with defaults

**Code**:
```typescript
migration('add-timestamps')
  .phase('Add created_at')
  .addColumn('users', 'created_at', 'TIMESTAMP')
  .withDefault('CURRENT_TIMESTAMP')
  .notNullable()

  .phase('Add updated_at')
  .addColumn('users', 'updated_at', 'TIMESTAMP')
  .withDefault('CURRENT_TIMESTAMP')
  .notNullable()

  .phase('Add trigger for updated_at')
  .customSQL(`
    CREATE OR REPLACE FUNCTION update_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
      NEW.updated_at = CURRENT_TIMESTAMP;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
  `);
```

**Phases**: 3

---

## Performance Patterns

### Pattern 26: Add Partial Index

**Use Case**: Index only subset of rows for better performance.

**Safety**: ✅ Safe with CONCURRENTLY

**Code**:
```typescript
migration('add-partial-index')
  .phase('Create partial index')
  .customSQL(`
    CREATE INDEX CONCURRENTLY idx_users_active_email
    ON users (email)
    WHERE status = 'active'
  `);
```

**Phases**: 1

---

### Pattern 27: Add Covering Index

**Use Case**: Include additional columns in index to avoid table lookups.

**Safety**: ✅ Safe with CONCURRENTLY

**PostgreSQL**:
```typescript
migration('add-covering-index')
  .phase('Create index with INCLUDE')
  .customSQL(`
    CREATE INDEX CONCURRENTLY idx_users_email_with_name
    ON users (email) INCLUDE (first_name, last_name)
  `);
```

**Phases**: 1

---

### Pattern 28: Partition Large Table

**Use Case**: Split large table for better performance.

**Safety**: ⚠️ Complex - requires significant planning

**PostgreSQL 10+**:
```typescript
migration('partition-orders')
  .phase('Create partitioned table')
  .customSQL(`
    CREATE TABLE orders_new (
      id BIGSERIAL,
      user_id BIGINT NOT NULL,
      created_at TIMESTAMP NOT NULL,
      status VARCHAR(50),
      total DECIMAL(10,2),
      PRIMARY KEY (id, created_at)
    ) PARTITION BY RANGE (created_at)
  `)

  .phase('Create partitions')
  .customSQL(`
    CREATE TABLE orders_2024_q1 PARTITION OF orders_new
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

    CREATE TABLE orders_2024_q2 PARTITION OF orders_new
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
  `)

  .phase('Migrate data')
  .customSQL(`
    INSERT INTO orders_new
    SELECT * FROM orders;
  `)

  .phase('Swap tables')
  .customSQL(`
    ALTER TABLE orders RENAME TO orders_old;
    ALTER TABLE orders_new RENAME TO orders;
  `);
```

**Phases**: 4

---

## Anti-Patterns

### ❌ Anti-Pattern 1: Adding NOT NULL Without Default

**Problem**: Breaks compatibility with existing code.

**Bad**:
```typescript
migration('bad-not-null')
  .phase('Add column')
  .addColumn('users', 'required_field', 'VARCHAR(100)')
  .notNullable(); // ❌ Fails on existing rows
```

**Good**:
```typescript
migration('good-not-null')
  .phase('Add nullable with default')
  .addColumn('users', 'required_field', 'VARCHAR(100)')
  .nullable()
  .withDefault('default_value')

  .phase('Backfill')
  .backfill('users', "required_field = 'default_value'")

  .phase('Make NOT NULL')
  .makeNonNullable();
```

---

### ❌ Anti-Pattern 2: Dropping Column Before Code Deployment

**Problem**: Application errors when code still references column.

**Bad**:
```typescript
migration('bad-drop')
  .phase('Drop column')
  .dropColumn('users', 'old_field'); // ❌ Code may still use this
```

**Good**:
```typescript
migration('good-drop')
  .phase('Stop writing')
  // Deploy app v1: Stop writing to old_field

  .phase('Stop reading')
  // Deploy app v2: Stop reading old_field

  .phase('Drop column')
  .dropColumn('users', 'old_field'); // ✅ Safe now
```

---

### ❌ Anti-Pattern 3: Non-Concurrent Index Creation

**Problem**: Locks table during index creation.

**Bad**:
```typescript
migration('bad-index')
  .phase('Add index')
  .addIndex('users', 'idx_email', ['email'], {
    concurrent: false // ❌ Locks table
  });
```

**Good**:
```typescript
migration('good-index')
  .phase('Add index')
  .addIndex('users', 'idx_email', ['email'], {
    concurrent: true // ✅ No lock
  });
```

---

### ❌ Anti-Pattern 4: Single-Phase Type Change

**Problem**: May cause downtime or data loss.

**Bad**:
```typescript
migration('bad-type-change')
  .phase('Change type')
  .customSQL('ALTER TABLE users ALTER COLUMN age TYPE INTEGER'); // ❌ Risky
```

**Good**:
```typescript
migration('good-type-change')
  .changeColumnType('users', 'age', 'VARCHAR(10)', 'INTEGER'); // ✅ Multi-phase
```

---

### ❌ Anti-Pattern 5: Large Backfill Without Batching

**Problem**: Long-running transaction locks table.

**Bad**:
```typescript
migration('bad-backfill')
  .phase('Backfill')
  .backfill('users', "status = 'active'"); // ❌ May lock for minutes
```

**Good**:
```typescript
migration('good-backfill')
  .phase('Batched backfill')
  .customSQL(`
    DO $$
    DECLARE
      batch_size INT := 10000;
    BEGIN
      LOOP
        UPDATE users SET status = 'active'
        WHERE id IN (
          SELECT id FROM users
          WHERE status IS NULL
          LIMIT batch_size
        );

        EXIT WHEN NOT FOUND;
        PERFORM pg_sleep(0.1);
      END LOOP;
    END $$;
  `);
```

---

## Quick Reference

| Pattern | Safety | Phases | Downtime |
|---------|--------|--------|----------|
| Add nullable column | ✅ Safe | 1 | None |
| Add required column | ✅ Safe | 3 | None |
| Remove column | ✅ Safe | 3 | None |
| Rename column | ✅ Safe | 5 | None |
| Change type | ⚠️ Caution | 4 | None |
| Add concurrent index | ✅ Safe | 1 | None |
| Add foreign key | ⚠️ Caution | 1 | None* |
| Add unique constraint | ⚠️ Caution | 1 | None* |
| Create table | ✅ Safe | 1 | None |
| Drop table | ⚠️ Caution | 2 | None* |

*None if data is valid and operations are properly prepared

## Resources

- [Zero-Downtime Migrations Guide](./zero-downtime-migrations.md)
- [Database Best Practices](../best-practices.md)
- [Performance Optimization](./performance-optimization.md)
