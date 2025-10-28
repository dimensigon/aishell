# Migration Examples

Real-world examples of zero-downtime database migrations.

## Example 1: Add User Email Verification

**Scenario**: Add email verification functionality to existing user system.

**Requirements**:
- Add `email_verified` boolean column
- Default to `false` for existing users
- Make it required (NOT NULL)

**Migration Code**:
```typescript
import { MigrationPatterns } from '../../src/cli/migration-dsl';

const migration = MigrationPatterns.addRequiredColumn(
  'users',
  'email_verified',
  'BOOLEAN',
  false
);

await migration.commit('./migrations');
```

**Deployment Plan**:
1. **Phase 1**: Add nullable column with default
   - Run: `ai-shell migrate apply migration.yaml --phase 1`
   - Deploy: App v1.1 (can write to `email_verified`)

2. **Phase 2**: Backfill existing rows
   - Run: `ai-shell migrate apply migration.yaml --phase 2`
   - Wait for completion

3. **Phase 3**: Make NOT NULL
   - Run: `ai-shell migrate apply migration.yaml --phase 3`
   - Now all users have `email_verified` boolean

**Timeline**: 30 minutes total, zero downtime

---

## Example 2: Rename Column for Clarity

**Scenario**: Rename `name` to `full_name` for clarity.

**Requirements**:
- Existing code uses `name`
- New code should use `full_name`
- No downtime allowed

**Migration Code**:
```typescript
import { MigrationPatterns } from '../../src/cli/migration-dsl';

const migration = MigrationPatterns.safeRenameColumn(
  'users',
  'name',
  'full_name',
  'VARCHAR(255)'
);

await migration.commit('./migrations');
```

**Deployment Plan**:
1. **Phase 1**: Add `full_name` column
   - Run migration phase 1
   - Column exists but unused

2. **Phase 2**: Enable dual-write
   - Deploy app v1.1: Writes to both `name` and `full_name`
   - Run migration phase 2

3. **Phase 3**: Backfill data
   - Run migration phase 3
   - Validates all data copied

4. **Phase 4**: Switch reads
   - Deploy app v1.2: Reads from `full_name`, writes to both
   - Monitor for issues

5. **Phase 5**: Drop old column
   - Deploy app v2.0: Only uses `full_name`
   - Run migration phase 5
   - `name` column dropped

**Timeline**: 1 week (for safety), zero downtime

---

## Example 3: Change Age from String to Integer

**Scenario**: Age stored as VARCHAR, need INTEGER for calculations.

**Requirements**:
- Convert existing data
- Validate all values are numeric
- Handle edge cases

**Migration Code**:
```typescript
import { MigrationPatterns } from '../../src/cli/migration-dsl';

const migration = MigrationPatterns.changeColumnType(
  'users',
  'age',
  'VARCHAR(10)',
  'INTEGER'
);

await migration.commit('./migrations');
```

**Pre-Migration Validation**:
```sql
-- Find invalid data
SELECT id, age FROM users WHERE age !~ '^[0-9]+$';

-- Fix invalid data
UPDATE users SET age = '0' WHERE age !~ '^[0-9]+$';
```

**Deployment Plan**:
1. **Phase 1**: Add `age_new` INTEGER column
   - Run migration phase 1

2. **Phase 2**: Enable dual-write with conversion
   - Deploy app v1.1: Writes to both with type conversion
   - Run migration phase 2

3. **Phase 3**: Backfill and validate
   - Run migration phase 3
   - Validates conversion succeeded

4. **Phase 4**: Switch to new column
   - Deploy app v2.0: Uses `age` as INTEGER
   - Run migration phase 4

**Timeline**: 2-3 days, zero downtime

---

## Example 4: Add Composite Index for Performance

**Scenario**: Slow queries on `user_id` + `created_at` combination.

**Requirements**:
- Add index without blocking writes
- Large table (millions of rows)

**Migration Code**:
```typescript
import { migration } from '../../src/cli/migration-dsl';

const mig = migration('add-orders-index')
  .phase('Create composite index concurrently')
  .addIndex('orders', 'idx_orders_user_created', ['user_id', 'created_at'], {
    concurrent: true
  })
  .addValidation('index_exists', 'orders', undefined, {
    errorMessage: 'Index was not created successfully'
  });

await mig.commit('./migrations');
```

**Deployment**:
```bash
# Verify plan
ai-shell migrate plan migration.yaml

# Apply with monitoring
ai-shell migrate apply migration.yaml -y

# Monitor progress
watch -n 1 "psql -c \"SELECT * FROM pg_stat_progress_create_index\""
```

**Timeline**: 30-60 minutes (depending on table size), zero downtime

---

## Example 5: Split Full Name into First and Last

**Scenario**: `full_name` column should be `first_name` + `last_name`.

**Requirements**:
- Parse existing names
- Handle edge cases (single names, multiple spaces)
- Preserve original data until migration complete

**Migration Code**:
```typescript
import { MigrationPatterns } from '../../src/cli/migration-dsl';

const migration = MigrationPatterns.splitColumn(
  'users',
  'full_name',
  [
    {
      name: 'first_name',
      type: 'VARCHAR(100)',
      extract: `
        CASE
          WHEN POSITION(' ' IN TRIM(full_name)) > 0
          THEN TRIM(SPLIT_PART(TRIM(full_name), ' ', 1))
          ELSE TRIM(full_name)
        END
      `
    },
    {
      name: 'last_name',
      type: 'VARCHAR(100)',
      extract: `
        CASE
          WHEN POSITION(' ' IN TRIM(full_name)) > 0
          THEN TRIM(SUBSTRING(TRIM(full_name) FROM POSITION(' ' IN TRIM(full_name))))
          ELSE ''
        END
      `
    }
  ]
);

await migration.commit('./migrations');
```

**Data Validation**:
```sql
-- Check split results before finalizing
SELECT
  full_name,
  first_name,
  last_name
FROM users
WHERE first_name IS NOT NULL
LIMIT 100;

-- Find problematic names
SELECT full_name, first_name, last_name
FROM users
WHERE LENGTH(TRIM(full_name)) > 0
  AND (first_name IS NULL OR first_name = '');
```

**Timeline**: 1 week, zero downtime

---

## Example 6: Add Foreign Key with Validation

**Scenario**: Add foreign key constraint to `orders.user_id`.

**Requirements**:
- Ensure all user_id values are valid
- Clean up orphaned records
- Add constraint safely

**Migration Code**:
```typescript
import { migration } from '../../src/cli/migration-dsl';

const mig = migration('add-orders-user-fk')
  .phase('Find and handle orphaned orders')
  .customSQL(`
    -- Log orphaned orders
    CREATE TABLE IF NOT EXISTS orphaned_orders AS
    SELECT o.*
    FROM orders o
    LEFT JOIN users u ON o.user_id = u.id
    WHERE u.id IS NULL;

    -- Delete or assign to default user
    DELETE FROM orders
    WHERE id IN (SELECT id FROM orphaned_orders);
  `)

  .phase('Validate data integrity')
  .validateDataIntegrity(`
    SELECT COUNT(*) FROM orders o
    LEFT JOIN users u ON o.user_id = u.id
    WHERE u.id IS NULL
  `, 'Orphaned orders still exist')

  .phase('Add foreign key constraint')
  .addConstraint('orders', 'fk_orders_user_id',
    'FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE')

  .phase('Add index for FK performance')
  .addIndex('orders', 'idx_orders_user_id', ['user_id'], {
    concurrent: true
  });

await mig.commit('./migrations');
```

**Timeline**: 1 hour, zero downtime

---

## Example 7: Partition Large Table by Date

**Scenario**: Orders table has 50M+ rows, queries are slow.

**Requirements**:
- Partition by created_at (quarterly)
- Migrate existing data
- Zero downtime

**Migration Code**:
```typescript
import { migration } from '../../src/cli/migration-dsl';

const mig = migration('partition-orders', 'postgresql')
  .phase('Create partitioned table')
  .customSQL(`
    CREATE TABLE orders_new (
      LIKE orders INCLUDING ALL
    ) PARTITION BY RANGE (created_at)
  `)

  .phase('Create quarterly partitions')
  .customSQL(`
    CREATE TABLE orders_2024_q1 PARTITION OF orders_new
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

    CREATE TABLE orders_2024_q2 PARTITION OF orders_new
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

    CREATE TABLE orders_2024_q3 PARTITION OF orders_new
    FOR VALUES FROM ('2024-07-01') TO ('2024-10-01');

    CREATE TABLE orders_2024_q4 PARTITION OF orders_new
    FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');

    CREATE TABLE orders_future PARTITION OF orders_new
    FOR VALUES FROM ('2025-01-01') TO (MAXVALUE);
  `)

  .phase('Migrate data in batches')
  .customSQL(`
    DO $$
    DECLARE
      batch_size INT := 100000;
      min_id BIGINT;
      max_id BIGINT;
      current_id BIGINT := 0;
    BEGIN
      SELECT MIN(id), MAX(id) INTO min_id, max_id FROM orders;

      WHILE current_id < max_id LOOP
        INSERT INTO orders_new
        SELECT * FROM orders
        WHERE id > current_id AND id <= current_id + batch_size;

        current_id := current_id + batch_size;

        RAISE NOTICE 'Migrated up to ID: %', current_id;
        PERFORM pg_sleep(0.5);
      END LOOP;
    END $$;
  `)

  .phase('Verify migration')
  .validateDataIntegrity(`
    SELECT
      (SELECT COUNT(*) FROM orders) =
      (SELECT COUNT(*) FROM orders_new)
  `, 'Row count mismatch')

  .phase('Swap tables')
  .customSQL(`
    BEGIN;
      ALTER TABLE orders RENAME TO orders_old;
      ALTER TABLE orders_new RENAME TO orders;
    COMMIT;
  `);

await mig.commit('./migrations');
```

**Timeline**: 2-4 hours (depending on data volume), zero downtime

---

## Example 8: Add JSONB Preferences Column

**Scenario**: Add flexible user preferences using JSONB.

**Requirements**:
- Support complex nested preferences
- Enable fast queries
- Default to empty object

**Migration Code**:
```typescript
import { migration } from '../../src/cli/migration-dsl';

const mig = migration('add-user-preferences')
  .phase('Add JSONB column')
  .addColumn('users', 'preferences', 'JSONB')
  .nullable()
  .withDefault("'{}'::jsonb")

  .phase('Backfill with defaults')
  .backfill('users', `
    preferences = jsonb_build_object(
      'email_notifications', true,
      'theme', 'light',
      'language', 'en'
    )
  `)

  .phase('Add GIN index for JSONB queries')
  .customSQL(`
    CREATE INDEX CONCURRENTLY idx_users_preferences_gin
    ON users USING GIN (preferences)
  `)

  .phase('Add specific path indexes')
  .customSQL(`
    CREATE INDEX CONCURRENTLY idx_users_pref_theme
    ON users ((preferences->>'theme'))
    WHERE preferences->>'theme' IS NOT NULL
  `);

await mig.commit('./migrations');
```

**Usage After Migration**:
```sql
-- Query by preference
SELECT * FROM users WHERE preferences->>'theme' = 'dark';

-- Update preferences
UPDATE users
SET preferences = jsonb_set(preferences, '{email_notifications}', 'false')
WHERE id = 123;
```

**Timeline**: 30 minutes, zero downtime

---

## Example 9: Add Soft Delete Support

**Scenario**: Add soft delete functionality (deleted_at timestamp).

**Requirements**:
- Add deleted_at column
- Update indexes to exclude deleted rows
- Maintain performance

**Migration Code**:
```typescript
import { migration } from '../../src/cli/migration-dsl';

const mig = migration('add-soft-delete')
  .phase('Add deleted_at column')
  .addColumn('users', 'deleted_at', 'TIMESTAMP')
  .nullable()

  .phase('Add partial index for active users')
  .customSQL(`
    CREATE INDEX CONCURRENTLY idx_users_active
    ON users (id, email)
    WHERE deleted_at IS NULL
  `)

  .phase('Create view for active users')
  .customSQL(`
    CREATE OR REPLACE VIEW users_active AS
    SELECT * FROM users WHERE deleted_at IS NULL
  `);

await mig.commit('./migrations');
```

**Application Code Changes**:
```typescript
// Before
SELECT * FROM users WHERE email = 'user@example.com';

// After
SELECT * FROM users WHERE email = 'user@example.com' AND deleted_at IS NULL;

// Or use view
SELECT * FROM users_active WHERE email = 'user@example.com';
```

**Timeline**: 1 hour, zero downtime

---

## Example 10: Comprehensive E-commerce Schema Migration

**Scenario**: Migrate from monolithic orders table to normalized schema.

**Requirements**:
- Split orders into orders + order_items
- Add proper foreign keys
- Maintain referential integrity
- Zero downtime

**Migration Code**:
```typescript
import { migration } from '../../src/cli/migration-dsl';

const mig = migration('normalize-orders')
  .phase('Create order_items table')
  .customSQL(`
    CREATE TABLE order_items (
      id BIGSERIAL PRIMARY KEY,
      order_id BIGINT NOT NULL,
      product_id BIGINT NOT NULL,
      quantity INTEGER NOT NULL,
      unit_price DECIMAL(10,2) NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `)

  .phase('Migrate data from JSON to normalized')
  .customSQL(`
    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
    SELECT
      o.id,
      (item->>'product_id')::BIGINT,
      (item->>'quantity')::INTEGER,
      (item->>'unit_price')::DECIMAL(10,2)
    FROM orders o,
    LATERAL jsonb_array_elements(o.items) AS item
  `)

  .phase('Validate migration')
  .validateDataIntegrity(`
    SELECT
      COUNT(DISTINCT o.id) = (SELECT COUNT(*) FROM orders)
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
  `, 'Order count mismatch')

  .phase('Add foreign keys')
  .addConstraint('order_items', 'fk_order_items_order',
    'FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE')
  .addConstraint('order_items', 'fk_order_items_product',
    'FOREIGN KEY (product_id) REFERENCES products(id)')

  .phase('Add indexes')
  .addIndex('order_items', 'idx_order_items_order', ['order_id'], { concurrent: true })
  .addIndex('order_items', 'idx_order_items_product', ['product_id'], { concurrent: true })

  .phase('Drop old items column')
  // After app deployment uses new table
  .dropColumn('orders', 'items');

await mig.commit('./migrations');
```

**Timeline**: 1-2 weeks (includes app refactoring), zero downtime

---

## Integration with Existing Systems

### With Backup System

```typescript
import { AdvancedMigrationEngine } from './migration-engine-advanced';
import { BackupSystem } from './backup-system';
import { DatabaseConnectionManager } from './database-manager';
import { StateManager } from '../core/state-manager';

// Setup
const dbManager = new DatabaseConnectionManager();
const stateManager = new StateManager({ enablePersistence: true });
const backupSystem = new BackupSystem(dbManager, stateManager);

const engine = new AdvancedMigrationEngine(
  dbManager,
  stateManager,
  backupSystem,
  {
    migrationsDir: './migrations',
    enableAutoBackup: true,
    enableAutoSnapshot: true
  }
);

// Migrations automatically create backups
await engine.executeMigration('./migrations/my-migration.yaml');
```

### With Health Monitoring

```typescript
import { HealthMonitor } from './health-monitor';

const monitor = new HealthMonitor(dbManager, stateManager);

// Monitor during migration
monitor.on('health:warning', (issue) => {
  console.log('Health warning during migration:', issue);
});

// Execute with monitoring
await monitor.startMonitoring({ interval: 5000 });
await engine.executeMigration('./migrations/my-migration.yaml');
await monitor.stopMonitoring();
```

---

## Testing Migrations

### Unit Tests

```typescript
import { describe, it, expect } from 'vitest';
import { migration } from './migration-dsl';

describe('Migration Tests', () => {
  it('should generate correct SQL', () => {
    const mig = migration('test')
      .phase('Add column')
      .addColumn('users', 'test', 'VARCHAR(100)');

    const def = mig.build();

    expect(def.phases[0].operations[0].type).toBe('add_column');
    expect(def.phases[0].operations[0].column).toBe('test');
  });
});
```

### Integration Tests

```typescript
describe('Migration Execution Tests', () => {
  it('should execute migration successfully', async () => {
    const migrationFile = './test-migrations/add-column.yaml';

    const execution = await engine.executeMigration(migrationFile, {
      skipBackup: true,
      skipSnapshot: true
    });

    expect(execution.status).toBe('completed');
    expect(execution.phaseResults[0].status).toBe('completed');
  });
});
```

---

## Best Practices Checklist

- [ ] Always use multi-phase migrations for complex changes
- [ ] Add columns as nullable first, make NOT NULL later
- [ ] Use concurrent index creation (PostgreSQL)
- [ ] Batch large backfills
- [ ] Add validations after each phase
- [ ] Create backups before migrations
- [ ] Test in staging environment first
- [ ] Document deployment steps
- [ ] Monitor migration progress
- [ ] Have rollback plan ready
- [ ] Coordinate with application deployments
- [ ] Use lock timeouts to prevent blocking
- [ ] Verify migration with `ai-shell migrate verify`
- [ ] Review execution plan with `ai-shell migrate plan`

---

## Resources

- [Zero-Downtime Migrations Guide](./zero-downtime-migrations.md)
- [Migration Patterns Library](./migration-patterns-library.md)
- [CLI Reference](../cli-reference.md)
