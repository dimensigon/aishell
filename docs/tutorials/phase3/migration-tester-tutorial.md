# Migration Tester Tutorial

Learn how to safely test database schema migrations before deploying to production, with automated rollback capabilities and comprehensive validation.

## Table of Contents

1. [What You'll Learn](#what-youll-learn)
2. [Prerequisites](#prerequisites)
3. [Part 1: Understanding Migration Testing](#part-1-understanding-migration-testing-5-min)
4. [Part 2: Basic Migration Testing](#part-2-basic-migration-testing-10-min)
5. [Part 3: Advanced Testing Strategies](#part-3-advanced-testing-strategies-15-min)
6. [Part 4: Rollback Procedures](#part-4-rollback-procedures-10-min)
7. [Part 5: Data Integrity Validation](#part-5-data-integrity-validation-10-min)
8. [Part 6: Production Migration Workflow](#part-6-production-migration-workflow-10-min)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Next Steps](#next-steps)

## What You'll Learn

By the end of this tutorial, you will:

- Understand migration testing fundamentals and risks
- Create and test database migrations safely
- Implement automated rollback procedures
- Validate data integrity after migrations
- Test migrations with production-like data
- Deploy migrations to production with confidence
- Handle migration failures gracefully
- Monitor migration performance

**Estimated Time:** 60 minutes

## Prerequisites

Before starting this tutorial, ensure you have:

- AI-Shell installed and configured
- A database connection (PostgreSQL, MySQL, or SQLite)
- Basic understanding of database schemas
- Familiarity with SQL DDL statements
- A test database for practicing
- 60 minutes of focused time

## Part 1: Understanding Migration Testing (5 min)

### What is Migration Testing?

Database migration testing validates schema changes before production deployment by:

- **Dry-running migrations** in isolated environments
- **Validating data integrity** before and after changes
- **Testing rollback procedures** to ensure reversibility
- **Measuring performance impact** of schema changes
- **Verifying application compatibility** with new schema

### Why Migration Testing Matters

Schema migrations are high-risk operations that can cause:

- **Data loss** from incorrect ALTER TABLE statements
- **Application downtime** during long-running migrations
- **Performance degradation** from missing indexes
- **Data corruption** from failed constraints
- **Irreversible changes** without proper backups

**Real-World Example:**

```
❌ Without Testing:
1. Deploy migration to production
2. Migration fails halfway through
3. Database is in inconsistent state
4. Application crashes
5. Hours of downtime while restoring backup
6. Lost revenue and customer trust

✅ With Testing:
1. Test migration on staging database
2. Discover issue with foreign key constraint
3. Fix migration script
4. Test again - success!
5. Deploy to production confidently
6. Zero downtime, zero issues
```

### Migration Testing Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    1. Create Migration                       │
│              Write migration up/down scripts                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  2. Test on Local Database                   │
│             Validate syntax and basic logic                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              3. Test with Production-Like Data               │
│           Clone production, anonymize, test migration        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    4. Validate Data Integrity                │
│         Compare row counts, checksums, constraints           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    5. Test Rollback                          │
│           Verify down migration restores state               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  6. Performance Testing                      │
│        Measure migration time, lock duration, impact         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                7. Deploy to Staging                          │
│           Test with real application load                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              8. Deploy to Production                         │
│        Execute during maintenance window with backup         │
└─────────────────────────────────────────────────────────────┘
```

### Types of Migrations

**1. Additive Migrations (Low Risk)**
- Add new columns with defaults
- Create new tables
- Add indexes
- Create views

**2. Transformative Migrations (Medium Risk)**
- Rename columns
- Change data types
- Split/merge tables
- Modify constraints

**3. Destructive Migrations (High Risk)**
- Drop columns
- Drop tables
- Remove indexes
- Delete data

### Common Migration Risks

| Risk | Impact | Example |
|------|--------|---------|
| Data Loss | Critical | `DROP COLUMN` without backup |
| Downtime | High | Long-running `ALTER TABLE` on large table |
| Performance | Medium | Missing index after migration |
| Corruption | Critical | Failed foreign key constraint |
| Inconsistency | High | Application incompatible with new schema |

## Part 2: Basic Migration Testing (10 min)

### Step 1: Create Your First Migration

Create a migration file structure:

```bash
mkdir -p migrations
cd migrations
```

Create a migration file:

```typescript
// migrations/001_add_user_profile.ts
export const up = async (db) => {
  await db.schema.createTable('user_profiles', (table) => {
    table.increments('id').primary();
    table.integer('user_id').unsigned().notNullable();
    table.string('bio', 500);
    table.string('avatar_url', 255);
    table.string('location', 100);
    table.timestamp('created_at').defaultTo(db.fn.now());
    table.timestamp('updated_at').defaultTo(db.fn.now());

    // Foreign key
    table.foreign('user_id').references('users.id').onDelete('CASCADE');

    // Indexes
    table.index('user_id');
  });
};

export const down = async (db) => {
  await db.schema.dropTableIfExists('user_profiles');
};

export const metadata = {
  version: '001',
  description: 'Add user_profiles table',
  author: 'dev-team',
  estimatedDuration: '5s',
  risk: 'low',
};
```

### Step 2: Test the Migration Locally

Use AI-Shell to test the migration:

```bash
# Test migration (dry run - no changes)
ai-shell migration test migrations/001_add_user_profile.ts --dry-run

# Output:
# ✓ Migration syntax valid
# ✓ No SQL errors detected
# ✓ Foreign key constraints valid
# ✓ Indexes properly defined
#
# Estimated execution time: 5 seconds
# Risk level: LOW
#
# Changes:
#   + CREATE TABLE user_profiles
#   + ADD FOREIGN KEY (user_id) → users(id)
#   + ADD INDEX idx_user_profiles_user_id
```

### Step 3: Execute Migration on Test Database

Run the migration for real:

```bash
# Execute migration
ai-shell migration run migrations/001_add_user_profile.ts --database test

# Output:
# Running migration 001_add_user_profile...
# ✓ Created table user_profiles (2.3s)
# ✓ Added foreign key constraint (0.5s)
# ✓ Created index on user_id (0.8s)
#
# Migration completed successfully in 3.6s
```

### Step 4: Validate Migration Result

Verify the migration worked correctly:

```bash
# Check table was created
ai-shell migration validate migrations/001_add_user_profile.ts

# Output:
# Validating migration 001_add_user_profile...
#
# ✓ Table user_profiles exists
# ✓ All columns present and correct types
# ✓ Foreign key constraint exists
# ✓ Index exists on user_id
# ✓ No orphaned data
#
# Migration validation: PASSED
```

### Step 5: Test Rollback

Test that the down migration works:

```bash
# Rollback migration
ai-shell migration rollback migrations/001_add_user_profile.ts --database test

# Output:
# Rolling back migration 001_add_user_profile...
# ✓ Dropped table user_profiles (1.2s)
#
# Rollback completed successfully in 1.2s

# Verify rollback
ai-shell migration validate migrations/001_add_user_profile.ts --expect-absent

# Output:
# ✓ Table user_profiles does not exist (expected)
# ✓ Foreign key constraint removed
# ✓ Index removed
#
# Rollback validation: PASSED
```

### Step 6: Re-run Migration

After successful rollback test, re-run the migration:

```bash
ai-shell migration run migrations/001_add_user_profile.ts --database test
```

## Part 3: Advanced Testing Strategies (15 min)

### Strategy 1: Testing with Production Data

Clone and test with real data (anonymized):

```typescript
// test-with-production-data.ts
import { AIShell } from 'ai-shell';

async function testMigrationWithProductionData() {
  const shell = new AIShell();

  console.log('1. Creating test database from production...');
  await shell.migration.cloneDatabase({
    source: 'production',
    target: 'migration_test',
    anonymize: true,  // Anonymize sensitive data
    tables: ['users', 'orders', 'products'],  // Specific tables
  });

  console.log('2. Running pre-migration validation...');
  const preState = await shell.migration.captureState('migration_test');

  console.log('3. Executing migration...');
  const result = await shell.migration.run({
    file: 'migrations/001_add_user_profile.ts',
    database: 'migration_test',
    timeout: 300000,  // 5 minute timeout
  });

  console.log('4. Running post-migration validation...');
  const postState = await shell.migration.captureState('migration_test');

  console.log('5. Comparing states...');
  const comparison = await shell.migration.compareStates(preState, postState);

  console.log('\nValidation Results:');
  console.log(`  Row Count Change: ${comparison.rowCountDiff}`);
  console.log(`  Data Integrity: ${comparison.integrityCheck ? '✓' : '✗'}`);
  console.log(`  Constraint Violations: ${comparison.constraintViolations}`);
  console.log(`  Orphaned Records: ${comparison.orphanedRecords}`);

  console.log('\n6. Testing rollback...');
  await shell.migration.rollback({
    file: 'migrations/001_add_user_profile.ts',
    database: 'migration_test',
  });

  const rollbackState = await shell.migration.captureState('migration_test');
  const rollbackComparison = await shell.migration.compareStates(
    preState,
    rollbackState
  );

  console.log('\nRollback Validation:');
  console.log(`  State Restored: ${rollbackComparison.identical ? '✓' : '✗'}`);

  console.log('\n7. Cleaning up test database...');
  await shell.migration.dropDatabase('migration_test');

  console.log('\n✓ Migration testing completed successfully!');
}

testMigrationWithProductionData().catch(console.error);
```

Run the test:

```bash
npx ts-node test-with-production-data.ts
```

### Strategy 2: Automated Migration Test Suite

Create a comprehensive test suite:

```typescript
// migration-test-suite.ts
import { AIShell } from 'ai-shell';
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';

describe('Migration: 001_add_user_profile', () => {
  let shell: AIShell;
  let testDb: string;

  beforeEach(async () => {
    shell = new AIShell();
    testDb = `test_${Date.now()}`;
    await shell.migration.createTestDatabase(testDb);
  });

  afterEach(async () => {
    await shell.migration.dropDatabase(testDb);
  });

  it('should create user_profiles table', async () => {
    await shell.migration.run({
      file: 'migrations/001_add_user_profile.ts',
      database: testDb,
    });

    const tables = await shell.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'public'
      AND table_name = 'user_profiles'
    `);

    expect(tables.rows.length).toBe(1);
  });

  it('should create all required columns', async () => {
    await shell.migration.run({
      file: 'migrations/001_add_user_profile.ts',
      database: testDb,
    });

    const columns = await shell.query(`
      SELECT column_name, data_type, is_nullable
      FROM information_schema.columns
      WHERE table_name = 'user_profiles'
      ORDER BY ordinal_position
    `);

    const expectedColumns = [
      { column_name: 'id', data_type: 'integer', is_nullable: 'NO' },
      { column_name: 'user_id', data_type: 'integer', is_nullable: 'NO' },
      { column_name: 'bio', data_type: 'character varying', is_nullable: 'YES' },
      { column_name: 'avatar_url', data_type: 'character varying', is_nullable: 'YES' },
      { column_name: 'location', data_type: 'character varying', is_nullable: 'YES' },
      { column_name: 'created_at', data_type: 'timestamp without time zone', is_nullable: 'YES' },
      { column_name: 'updated_at', data_type: 'timestamp without time zone', is_nullable: 'YES' },
    ];

    expect(columns.rows).toMatchObject(expectedColumns);
  });

  it('should create foreign key constraint', async () => {
    // First create users table
    await shell.query(`
      CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL
      )
    `, [], { database: testDb });

    await shell.migration.run({
      file: 'migrations/001_add_user_profile.ts',
      database: testDb,
    });

    const constraints = await shell.query(`
      SELECT constraint_name, constraint_type
      FROM information_schema.table_constraints
      WHERE table_name = 'user_profiles'
      AND constraint_type = 'FOREIGN KEY'
    `);

    expect(constraints.rows.length).toBeGreaterThan(0);
  });

  it('should create index on user_id', async () => {
    await shell.migration.run({
      file: 'migrations/001_add_user_profile.ts',
      database: testDb,
    });

    const indexes = await shell.query(`
      SELECT indexname
      FROM pg_indexes
      WHERE tablename = 'user_profiles'
      AND indexname LIKE '%user_id%'
    `);

    expect(indexes.rows.length).toBeGreaterThan(0);
  });

  it('should enforce foreign key constraint', async () => {
    // Create users table
    await shell.query(`
      CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL
      )
    `, [], { database: testDb });

    await shell.migration.run({
      file: 'migrations/001_add_user_profile.ts',
      database: testDb,
    });

    // Try to insert with invalid user_id
    await expect(
      shell.query(`
        INSERT INTO user_profiles (user_id, bio)
        VALUES (99999, 'Test bio')
      `, [], { database: testDb })
    ).rejects.toThrow(/foreign key constraint/i);
  });

  it('should rollback cleanly', async () => {
    await shell.migration.run({
      file: 'migrations/001_add_user_profile.ts',
      database: testDb,
    });

    await shell.migration.rollback({
      file: 'migrations/001_add_user_profile.ts',
      database: testDb,
    });

    const tables = await shell.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'public'
      AND table_name = 'user_profiles'
    `);

    expect(tables.rows.length).toBe(0);
  });

  it('should preserve existing data during migration', async () => {
    // Create users table with data
    await shell.query(`
      CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL
      )
    `, [], { database: testDb });

    await shell.query(`
      INSERT INTO users (email) VALUES
      ('user1@example.com'),
      ('user2@example.com'),
      ('user3@example.com')
    `, [], { database: testDb });

    await shell.migration.run({
      file: 'migrations/001_add_user_profile.ts',
      database: testDb,
    });

    const users = await shell.query(
      'SELECT COUNT(*) as count FROM users',
      [],
      { database: testDb }
    );

    expect(users.rows[0].count).toBe('3');
  });

  it('should complete within time limit', async () => {
    const start = Date.now();

    await shell.migration.run({
      file: 'migrations/001_add_user_profile.ts',
      database: testDb,
    });

    const duration = Date.now() - start;

    expect(duration).toBeLessThan(10000);  // 10 seconds
  });
});
```

Run the test suite:

```bash
npm test migration-test-suite.ts
```

### Strategy 3: Load Testing Migrations

Test migration performance under load:

```typescript
// load-test-migration.ts
import { AIShell } from 'ai-shell';

async function loadTestMigration() {
  const shell = new AIShell();
  const testDb = 'migration_load_test';

  console.log('1. Creating test database...');
  await shell.migration.createTestDatabase(testDb);

  console.log('2. Generating test data...');
  // Create users table with 1 million rows
  await shell.query(`
    CREATE TABLE users (
      id SERIAL PRIMARY KEY,
      email VARCHAR(255) NOT NULL,
      created_at TIMESTAMP DEFAULT NOW()
    )
  `, [], { database: testDb });

  await shell.query(`
    INSERT INTO users (email)
    SELECT 'user' || generate_series || '@example.com'
    FROM generate_series(1, 1000000)
  `, [], { database: testDb });

  console.log('3. Running migration with large dataset...');
  const start = Date.now();

  await shell.migration.run({
    file: 'migrations/001_add_user_profile.ts',
    database: testDb,
    monitoring: true,  // Monitor locks and performance
  });

  const duration = Date.now() - start;

  console.log(`\nMigration completed in ${(duration / 1000).toFixed(2)}s`);

  console.log('\n4. Analyzing performance impact...');
  const stats = await shell.migration.getStats(testDb);

  console.log(`  Table size: ${(stats.tableSize / 1024 / 1024).toFixed(2)} MB`);
  console.log(`  Index size: ${(stats.indexSize / 1024 / 1024).toFixed(2)} MB`);
  console.log(`  Lock duration: ${stats.lockDuration}ms`);
  console.log(`  Rows affected: ${stats.rowsAffected}`);

  console.log('\n5. Testing concurrent reads during migration...');
  // Simulate application load during migration
  const results = await Promise.all([
    shell.migration.run({
      file: 'migrations/002_add_user_index.ts',
      database: testDb,
    }),
    ...Array(10).fill(null).map(() =>
      shell.query('SELECT * FROM users LIMIT 100', [], { database: testDb })
    ),
  ]);

  console.log(`  Concurrent queries completed: ${results.length - 1}`);

  console.log('\n6. Cleaning up...');
  await shell.migration.dropDatabase(testDb);

  console.log('\n✓ Load testing completed!');
}

loadTestMigration().catch(console.error);
```

## Part 4: Rollback Procedures (10 min)

### Understanding Rollback Strategies

#### Strategy 1: Transaction-Based Rollback (Fastest)

Wrap migration in transaction:

```typescript
// migrations/002_add_email_verification.ts
export const up = async (db) => {
  await db.transaction(async (trx) => {
    // Add column
    await trx.schema.table('users', (table) => {
      table.boolean('email_verified').defaultTo(false);
      table.timestamp('email_verified_at').nullable();
    });

    // Create verification tokens table
    await trx.schema.createTable('email_verification_tokens', (table) => {
      table.increments('id').primary();
      table.integer('user_id').unsigned().notNullable();
      table.string('token', 64).notNullable();
      table.timestamp('expires_at').notNullable();
      table.timestamp('created_at').defaultTo(db.fn.now());

      table.foreign('user_id').references('users.id').onDelete('CASCADE');
      table.unique('token');
      table.index('user_id');
    });
  });
};

export const down = async (db) => {
  await db.transaction(async (trx) => {
    await trx.schema.dropTableIfExists('email_verification_tokens');

    await trx.schema.table('users', (table) => {
      table.dropColumn('email_verified');
      table.dropColumn('email_verified_at');
    });
  });
};
```

#### Strategy 2: Backup-Based Rollback (Safest)

Create backup before migration:

```typescript
// safe-migration-with-backup.ts
import { AIShell } from 'ai-shell';

async function safeMigration() {
  const shell = new AIShell();
  const database = 'production';

  console.log('1. Creating backup...');
  const backupId = await shell.migration.createBackup(database);
  console.log(`   Backup created: ${backupId}`);

  try {
    console.log('2. Running migration...');
    await shell.migration.run({
      file: 'migrations/002_add_email_verification.ts',
      database,
      timeout: 300000,
    });

    console.log('3. Validating migration...');
    const validation = await shell.migration.validate({
      file: 'migrations/002_add_email_verification.ts',
      database,
    });

    if (!validation.passed) {
      throw new Error('Migration validation failed');
    }

    console.log('4. Testing application...');
    // Run application tests
    const appTests = await runApplicationTests();

    if (!appTests.passed) {
      throw new Error('Application tests failed after migration');
    }

    console.log('✓ Migration successful!');
    console.log('  Keeping backup for 7 days...');
    await shell.migration.retainBackup(backupId, { days: 7 });

  } catch (error) {
    console.error('✗ Migration failed:', error.message);

    console.log('\nInitiating rollback...');
    console.log('1. Restoring from backup...');
    await shell.migration.restoreBackup(backupId);

    console.log('2. Validating restore...');
    const restoreValidation = await shell.migration.validateRestore(backupId);

    if (restoreValidation.passed) {
      console.log('✓ Successfully rolled back to pre-migration state');
    } else {
      console.error('✗ CRITICAL: Restore validation failed!');
      console.error('   Manual intervention required');
    }

    throw error;
  }
}

async function runApplicationTests() {
  // Implement application-specific tests
  return { passed: true };
}

safeMigration().catch(console.error);
```

#### Strategy 3: Point-in-Time Rollback

Use database point-in-time recovery:

```bash
# Before migration: Note the timestamp
ai-shell migration timestamp

# Output:
# Current timestamp: 2025-10-30T10:30:00Z
# Recovery command: ai-shell migration rollback --to-timestamp 2025-10-30T10:30:00Z

# After migration failure:
ai-shell migration rollback --to-timestamp 2025-10-30T10:30:00Z

# Output:
# Initiating point-in-time recovery...
# ✓ Database restored to 2025-10-30T10:30:00Z
# ✓ All changes after timestamp have been reverted
```

### Automated Rollback on Failure

Configure automatic rollback:

```typescript
// config/migration.ts
export const migrationConfig = {
  autoRollback: {
    enabled: true,

    // Trigger rollback on these conditions
    triggers: {
      error: true,              // Any error during migration
      timeout: true,            // Migration exceeds timeout
      validationFailed: true,   // Post-migration validation fails
      constraintViolation: true, // Foreign key or constraint errors
    },

    // Rollback strategy
    strategy: 'backup',  // 'transaction', 'backup', 'pitr'

    // Create backup before migration
    createBackup: true,
    backupRetention: 7,  // days

    // Notifications
    notifications: {
      onRollback: {
        email: ['team@example.com'],
        slack: '#database-alerts',
        pagerduty: true,
      },
    },
  },
};
```

### Manual Rollback Procedures

Document manual rollback steps:

```markdown
# Migration Rollback Procedure

## Automated Rollback (Preferred)

bash
ai-shell migration rollback migrations/002_add_email_verification.ts


## Manual Rollback (If Automated Fails)

### Step 1: Stop Application
bash
kubectl scale deployment app --replicas=0


### Step 2: Restore Database Backup
bash
pg_restore -d production backup_20251030_103000.dump


### Step 3: Verify Restore
bash
ai-shell migration validate --expect-version 001


### Step 4: Restart Application
bash
kubectl scale deployment app --replicas=3


### Step 5: Monitor
bash
ai-shell migration monitor


## Emergency Contacts

- Database Admin: +1-555-0100
- DevOps Lead: +1-555-0101
- CTO: +1-555-0102
```

## Part 5: Data Integrity Validation (10 min)

### Pre-Migration Validation

Capture database state before migration:

```typescript
// pre-migration-validation.ts
import { AIShell } from 'ai-shell';

async function preMigrationValidation() {
  const shell = new AIShell();

  console.log('Running pre-migration validation...\n');

  // 1. Row counts
  console.log('1. Capturing row counts...');
  const rowCounts = await shell.query(`
    SELECT
      table_name,
      (xpath('/row/count/text()', xml_count))[1]::text::int as row_count
    FROM (
      SELECT
        table_name,
        table_schema,
        query_to_xml(format('SELECT COUNT(*) as count FROM %I.%I', table_schema, table_name), false, true, '') as xml_count
      FROM information_schema.tables
      WHERE table_schema = 'public'
    ) t
  `);

  console.log('   Tables:', rowCounts.rows.length);

  // 2. Constraint validation
  console.log('2. Validating constraints...');
  const constraints = await shell.query(`
    SELECT
      conname,
      contype,
      conrelid::regclass as table_name
    FROM pg_constraint
    WHERE connamespace = 'public'::regnamespace
  `);

  console.log('   Constraints:', constraints.rows.length);

  // 3. Index validation
  console.log('3. Checking indexes...');
  const indexes = await shell.query(`
    SELECT
      schemaname,
      tablename,
      indexname,
      indexdef
    FROM pg_indexes
    WHERE schemaname = 'public'
  `);

  console.log('   Indexes:', indexes.rows.length);

  // 4. Data checksums
  console.log('4. Computing checksums...');
  const checksums = {};
  for (const row of rowCounts.rows) {
    const checksum = await shell.query(`
      SELECT MD5(CAST(ARRAY_AGG(t.*) AS TEXT)) as checksum
      FROM ${row.table_name} t
    `);
    checksums[row.table_name] = checksum.rows[0].checksum;
  }

  console.log('   Checksums computed:', Object.keys(checksums).length);

  // 5. Foreign key validation
  console.log('5. Validating foreign keys...');
  const orphans = await shell.query(`
    SELECT
      tc.table_name,
      kcu.column_name,
      ccu.table_name AS foreign_table_name,
      COUNT(*) as orphan_count
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
    GROUP BY tc.table_name, kcu.column_name, ccu.table_name
    HAVING COUNT(*) > 0
  `);

  console.log('   Foreign key checks:', orphans.rows.length);

  // Save state
  const state = {
    timestamp: new Date().toISOString(),
    rowCounts: rowCounts.rows,
    constraints: constraints.rows,
    indexes: indexes.rows,
    checksums,
    orphans: orphans.rows,
  };

  await shell.migration.saveState('pre-migration-state.json', state);

  console.log('\n✓ Pre-migration state captured');
  console.log(`  Saved to: pre-migration-state.json`);

  return state;
}

preMigrationValidation().catch(console.error);
```

### Post-Migration Validation

Compare database state after migration:

```typescript
// post-migration-validation.ts
import { AIShell } from 'ai-shell';

async function postMigrationValidation() {
  const shell = new AIShell();

  console.log('Running post-migration validation...\n');

  // Load pre-migration state
  const preState = await shell.migration.loadState('pre-migration-state.json');

  // Capture post-migration state
  const postState = await preMigrationValidation();

  console.log('\nComparing states...\n');

  // 1. Compare row counts
  console.log('1. Row Count Validation:');
  let rowCountIssues = 0;
  for (const preTable of preState.rowCounts) {
    const postTable = postState.rowCounts.find(t => t.table_name === preTable.table_name);

    if (!postTable) {
      console.log(`   ✗ Table ${preTable.table_name} was removed`);
      rowCountIssues++;
    } else if (preTable.row_count !== postTable.row_count) {
      console.log(`   ⚠ Table ${preTable.table_name}: ${preTable.row_count} → ${postTable.row_count} rows`);
    } else {
      console.log(`   ✓ Table ${preTable.table_name}: ${preTable.row_count} rows (unchanged)`);
    }
  }

  // Check for new tables
  for (const postTable of postState.rowCounts) {
    const preTable = preState.rowCounts.find(t => t.table_name === postTable.table_name);
    if (!preTable) {
      console.log(`   + Table ${postTable.table_name} was added (${postTable.row_count} rows)`);
    }
  }

  // 2. Compare checksums
  console.log('\n2. Data Integrity Validation:');
  let checksumIssues = 0;
  for (const [table, preChecksum] of Object.entries(preState.checksums)) {
    const postChecksum = postState.checksums[table];

    if (!postChecksum) {
      console.log(`   ✗ Table ${table} checksum missing`);
      checksumIssues++;
    } else if (preChecksum !== postChecksum) {
      console.log(`   ⚠ Table ${table} data changed`);
    } else {
      console.log(`   ✓ Table ${table} data intact`);
    }
  }

  // 3. Validate constraints
  console.log('\n3. Constraint Validation:');
  let constraintIssues = 0;
  for (const preConstraint of preState.constraints) {
    const postConstraint = postState.constraints.find(
      c => c.conname === preConstraint.conname && c.table_name === preConstraint.table_name
    );

    if (!postConstraint) {
      console.log(`   ✗ Constraint ${preConstraint.conname} on ${preConstraint.table_name} was removed`);
      constraintIssues++;
    } else {
      console.log(`   ✓ Constraint ${preConstraint.conname} on ${preConstraint.table_name} exists`);
    }
  }

  // Check for new constraints
  for (const postConstraint of postState.constraints) {
    const preConstraint = preState.constraints.find(
      c => c.conname === postConstraint.conname && c.table_name === postConstraint.table_name
    );
    if (!preConstraint) {
      console.log(`   + Constraint ${postConstraint.conname} on ${postConstraint.table_name} was added`);
    }
  }

  // 4. Validate indexes
  console.log('\n4. Index Validation:');
  let indexIssues = 0;
  for (const preIndex of preState.indexes) {
    const postIndex = postState.indexes.find(
      i => i.indexname === preIndex.indexname && i.tablename === preIndex.tablename
    );

    if (!postIndex) {
      console.log(`   ✗ Index ${preIndex.indexname} on ${preIndex.tablename} was removed`);
      indexIssues++;
    } else {
      console.log(`   ✓ Index ${preIndex.indexname} on ${preIndex.tablename} exists`);
    }
  }

  // Summary
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('VALIDATION SUMMARY');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  const totalIssues = rowCountIssues + checksumIssues + constraintIssues + indexIssues;

  if (totalIssues === 0) {
    console.log('✓ All validations passed');
    console.log('✓ Migration completed successfully');
    return { passed: true };
  } else {
    console.log(`✗ ${totalIssues} validation issues found:`);
    console.log(`  - Row count issues: ${rowCountIssues}`);
    console.log(`  - Data integrity issues: ${checksumIssues}`);
    console.log(`  - Constraint issues: ${constraintIssues}`);
    console.log(`  - Index issues: ${indexIssues}`);
    return { passed: false, issues: totalIssues };
  }
}

postMigrationValidation().catch(console.error);
```

### Continuous Validation

Monitor data integrity continuously:

```typescript
// continuous-validation.ts
import { AIShell } from 'ai-shell';

async function continuousValidation() {
  const shell = new AIShell();

  setInterval(async () => {
    console.log(`\n[${new Date().toISOString()}] Running validation checks...`);

    // Check for constraint violations
    const violations = await shell.query(`
      SELECT
        conname,
        conrelid::regclass as table_name
      FROM pg_constraint c
      WHERE NOT EXISTS (
        SELECT 1
        FROM pg_trigger t
        WHERE t.tgconstraint = c.oid
      )
      AND contype = 'f'
    `);

    if (violations.rows.length > 0) {
      console.error('⚠ Constraint violations detected:');
      violations.rows.forEach(v => {
        console.error(`  - ${v.conname} on ${v.table_name}`);
      });
    } else {
      console.log('✓ No constraint violations');
    }

    // Check for orphaned records
    const orphans = await shell.query(`
      -- Implement orphan detection query
      SELECT 'orphan-check' as status
    `);

    console.log('✓ Validation cycle complete');

  }, 60000);  // Every minute
}

continuousValidation().catch(console.error);
```

## Part 6: Production Migration Workflow (10 min)

### Complete Production Migration Checklist

```markdown
# Production Migration Checklist

## Pre-Migration (1 week before)

- [ ] Migration tested on local development database
- [ ] Migration tested on staging with production-like data
- [ ] Rollback procedure tested and documented
- [ ] Performance impact analyzed and acceptable
- [ ] Database backup strategy confirmed
- [ ] Maintenance window scheduled and announced
- [ ] Team trained on rollback procedures
- [ ] Monitoring and alerting configured
- [ ] Load test completed successfully
- [ ] Application compatibility verified
- [ ] Documentation updated

## Pre-Migration (1 day before)

- [ ] Staging environment matches production exactly
- [ ] Final migration test on staging successful
- [ ] Rollback procedure re-tested
- [ ] Team availability confirmed
- [ ] Communication plan ready
- [ ] Customer notification sent
- [ ] Support team briefed

## During Migration Window

### Step 1: Preparation (T-30 min)
- [ ] Verify backup is recent (< 24 hours)
- [ ] Create fresh backup: `ai-shell migration backup production`
- [ ] Verify backup integrity: `ai-shell migration verify-backup`
- [ ] Enable read-only mode: `ai-shell db read-only on`
- [ ] Stop background jobs
- [ ] Verify no active connections: `ai-shell db connections`

### Step 2: Migration (T+0)
- [ ] Capture pre-migration state: `ai-shell migration snapshot pre`
- [ ] Run migration: `ai-shell migration run migrations/XXX --database production`
- [ ] Monitor migration progress
- [ ] Watch for errors or warnings

### Step 3: Validation (T+5 min)
- [ ] Capture post-migration state: `ai-shell migration snapshot post`
- [ ] Run validation suite: `ai-shell migration validate`
- [ ] Check row counts: `ai-shell migration compare-snapshots`
- [ ] Verify constraints: `ai-shell db check-constraints`
- [ ] Verify indexes: `ai-shell db check-indexes`
- [ ] Test critical queries

### Step 4: Application Testing (T+10 min)
- [ ] Disable read-only mode: `ai-shell db read-only off`
- [ ] Start application in canary mode
- [ ] Run smoke tests
- [ ] Check application logs for errors
- [ ] Verify critical user flows
- [ ] Monitor error rates

### Step 5: Full Deployment (T+20 min)
- [ ] Scale application to full capacity
- [ ] Restart background jobs
- [ ] Monitor system metrics
- [ ] Watch for performance issues
- [ ] Verify everything working normally

### Step 6: Post-Migration (T+30 min)
- [ ] Send "all clear" notification
- [ ] Document any issues encountered
- [ ] Update runbook with lessons learned
- [ ] Schedule backup retention
- [ ] Return to normal operations

## Rollback Procedure (If Needed)

### Immediate Rollback (< 5 min after migration)
bash
Enable read-only mode
ai-shell db read-only on

Rollback migration
ai-shell migration rollback migrations/XXX --database production

Verify rollback
ai-shell migration validate --expect-version XXX

Restart application
kubectl rollout restart deployment/app


### Backup Restore Rollback (> 5 min after migration)
bash
Stop application
kubectl scale deployment app --replicas=0

Restore backup
ai-shell migration restore-backup <backup-id>

Verify restore
ai-shell migration verify-restore <backup-id>

Restart application
kubectl scale deployment app --replicas=3


## Post-Migration Monitoring (24 hours)

- [ ] Monitor error rates
- [ ] Track performance metrics
- [ ] Watch for constraint violations
- [ ] Check slow query log
- [ ] Review user reports
- [ ] Verify backup schedule resumed
```

### Automated Production Migration Script

```typescript
// production-migration.ts
import { AIShell } from 'ai-shell';

async function productionMigration(migrationFile: string) {
  const shell = new AIShell();
  const database = 'production';

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('       PRODUCTION DATABASE MIGRATION');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log();
  console.log(`Migration: ${migrationFile}`);
  console.log(`Database: ${database}`);
  console.log(`Time: ${new Date().toISOString()}`);
  console.log();

  try {
    // Step 1: Pre-migration checks
    console.log('Step 1: Pre-migration checks...');

    const recentBackup = await shell.migration.getRecentBackup(database);
    if (!recentBackup || Date.now() - recentBackup.timestamp > 24 * 60 * 60 * 1000) {
      throw new Error('No recent backup found (< 24 hours)');
    }
    console.log(`  ✓ Recent backup found: ${recentBackup.id}`);

    const connections = await shell.query(`
      SELECT COUNT(*) as count
      FROM pg_stat_activity
      WHERE datname = $1
      AND state = 'active'
    `, [database]);

    console.log(`  ✓ Active connections: ${connections.rows[0].count}`);

    // Step 2: Create backup
    console.log('\nStep 2: Creating backup...');
    const backupId = await shell.migration.createBackup(database, {
      compression: true,
      verify: true,
    });
    console.log(`  ✓ Backup created: ${backupId}`);

    // Step 3: Enable maintenance mode
    console.log('\nStep 3: Enabling maintenance mode...');
    await shell.db.setReadOnly(database, true);
    await stopBackgroundJobs();
    console.log('  ✓ Maintenance mode enabled');

    // Step 4: Capture pre-migration state
    console.log('\nStep 4: Capturing pre-migration state...');
    const preState = await shell.migration.captureState(database);
    console.log(`  ✓ State captured: ${preState.tables.length} tables, ${preState.totalRows} rows`);

    // Step 5: Run migration
    console.log('\nStep 5: Running migration...');
    const migrationStart = Date.now();

    await shell.migration.run({
      file: migrationFile,
      database,
      timeout: 600000,  // 10 minutes
      monitoring: true,
    });

    const migrationDuration = Date.now() - migrationStart;
    console.log(`  ✓ Migration completed in ${(migrationDuration / 1000).toFixed(2)}s`);

    // Step 6: Validate migration
    console.log('\nStep 6: Validating migration...');
    const postState = await shell.migration.captureState(database);
    const validation = await shell.migration.compareStates(preState, postState);

    if (!validation.passed) {
      throw new Error(`Validation failed: ${validation.errors.join(', ')}`);
    }

    console.log('  ✓ Validation passed');
    console.log(`    - Row count diff: ${validation.rowCountDiff}`);
    console.log(`    - Constraint violations: ${validation.constraintViolations}`);
    console.log(`    - Orphaned records: ${validation.orphanedRecords}`);

    // Step 7: Disable maintenance mode
    console.log('\nStep 7: Disabling maintenance mode...');
    await shell.db.setReadOnly(database, false);
    await startBackgroundJobs();
    console.log('  ✓ Maintenance mode disabled');

    // Step 8: Smoke tests
    console.log('\nStep 8: Running smoke tests...');
    const smokeTests = await runSmokeTests();

    if (!smokeTests.passed) {
      throw new Error('Smoke tests failed');
    }

    console.log(`  ✓ Smoke tests passed (${smokeTests.testCount} tests)`);

    // Step 9: Monitor
    console.log('\nStep 9: Monitoring system...');
    await sleep(30000);  // Wait 30 seconds

    const metrics = await shell.migration.getMetrics(database);
    console.log(`  ✓ Error rate: ${metrics.errorRate.toFixed(2)}%`);
    console.log(`  ✓ Response time: ${metrics.avgResponseTime.toFixed(2)}ms`);
    console.log(`  ✓ Database CPU: ${metrics.cpuUsage.toFixed(1)}%`);

    if (metrics.errorRate > 1.0) {
      throw new Error('Error rate too high');
    }

    // Success!
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('✓ MIGRATION COMPLETED SUCCESSFULLY');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log();
    console.log(`Duration: ${(migrationDuration / 1000).toFixed(2)}s`);
    console.log(`Backup ID: ${backupId}`);
    console.log(`Backup retention: 7 days`);
    console.log();

    await notifySuccess(migrationFile, migrationDuration);

  } catch (error) {
    console.error('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.error('✗ MIGRATION FAILED');
    console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.error();
    console.error('Error:', error.message);
    console.error();

    console.log('Initiating rollback procedure...');

    try {
      // Rollback
      await shell.migration.rollback({
        file: migrationFile,
        database,
      });

      // Verify rollback
      const rollbackValidation = await shell.migration.validate({
        file: migrationFile,
        database,
        expectAbsent: true,
      });

      if (rollbackValidation.passed) {
        console.log('✓ Rollback completed successfully');
      } else {
        console.error('✗ Rollback validation failed - manual intervention required');
      }

      // Re-enable application
      await shell.db.setReadOnly(database, false);
      await startBackgroundJobs();

    } catch (rollbackError) {
      console.error('✗ CRITICAL: Rollback failed:', rollbackError.message);
      console.error('   Manual intervention required immediately');
    }

    await notifyFailure(migrationFile, error);

    throw error;
  }
}

async function stopBackgroundJobs() {
  // Implementation depends on your job system
  console.log('  Stopping background jobs...');
}

async function startBackgroundJobs() {
  // Implementation depends on your job system
  console.log('  Starting background jobs...');
}

async function runSmokeTests() {
  // Run critical application tests
  return { passed: true, testCount: 10 };
}

async function notifySuccess(migration: string, duration: number) {
  // Send success notification to team
}

async function notifyFailure(migration: string, error: Error) {
  // Send failure alert to team
}

function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Run migration
const migrationFile = process.argv[2];
if (!migrationFile) {
  console.error('Usage: npx ts-node production-migration.ts <migration-file>');
  process.exit(1);
}

productionMigration(migrationFile).catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
```

Run production migration:

```bash
npx ts-node production-migration.ts migrations/002_add_email_verification.ts
```

## Best Practices

### Do's ✅

1. **Always Test Migrations**
   - Test on local development first
   - Test on staging with production-like data
   - Test rollback procedures
   - Run automated test suites

2. **Create Backups**
   - Backup before every production migration
   - Verify backup integrity
   - Test backup restoration
   - Retain backups for at least 7 days

3. **Use Transactions**
   - Wrap DDL statements in transactions when possible
   - Automatic rollback on errors
   - Maintains consistency

4. **Validate Data Integrity**
   - Check row counts before/after
   - Validate constraints
   - Check for orphaned records
   - Compare checksums

5. **Monitor Performance**
   - Measure migration duration
   - Track lock duration
   - Monitor database load
   - Watch for performance regression

6. **Document Everything**
   - Write clear migration descriptions
   - Document rollback procedures
   - Keep runbooks updated
   - Log all migration executions

7. **Plan for Rollback**
   - Always write down migrations
   - Test rollback before production
   - Have restore procedure ready
   - Know when to rollback vs. fix forward

8. **Communicate**
   - Announce maintenance windows
   - Notify stakeholders
   - Update status during migration
   - Report completion

### Don'ts ❌

1. **Don't Skip Testing**
   - Never run untested migrations in production
   - Don't assume "it's simple, it'll work"
   - Don't skip rollback testing

2. **Don't Migrate Without Backup**
   - Never migrate without recent backup
   - Don't trust old backups
   - Don't skip backup verification

3. **Don't Ignore Warnings**
   - Investigate validation warnings
   - Don't proceed with constraint violations
   - Don't ignore performance issues

4. **Don't Use Destructive Operations Carelessly**
   - Avoid DROP COLUMN without backup
   - Don't truncate tables in migration
   - Be cautious with CASCADE

5. **Don't Migrate During Peak Hours**
   - Schedule during low-traffic periods
   - Don't surprise users with downtime
   - Avoid business-critical times

6. **Don't Mix Schema and Data Changes**
   - Separate schema migrations from data migrations
   - Keep migrations focused and atomic
   - Don't combine unrelated changes

7. **Don't Forget Application Compatibility**
   - Ensure app works with new schema
   - Test before deploying migration
   - Plan for gradual rollout if needed

8. **Don't Leave Migrations Unmonitored**
   - Watch migrations in progress
   - Monitor system health after
   - Don't assume success without validation

## Troubleshooting

### Problem: Migration Times Out

**Symptoms:**
- Migration exceeds timeout limit
- Database locks preventing completion
- Long-running ALTER TABLE statements

**Solutions:**

1. **Increase timeout:**
   ```typescript
   await shell.migration.run({
     file: 'migrations/XXX.ts',
     timeout: 1800000,  // 30 minutes
   });
   ```

2. **Use concurrent index creation:**
   ```sql
   CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
   ```

3. **Break into smaller migrations:**
   ```typescript
   // Instead of one large migration
   // migrations/003_add_indexes.ts
   // Create multiple smaller migrations
   // migrations/003_add_index_1.ts
   // migrations/004_add_index_2.ts
   ```

### Problem: Foreign Key Constraint Violation

**Symptoms:**
- Migration fails with foreign key error
- Cannot add constraint due to existing data
- Orphaned records detected

**Solutions:**

1. **Clean orphaned records first:**
   ```sql
   DELETE FROM child_table
   WHERE parent_id NOT IN (SELECT id FROM parent_table);
   ```

2. **Add constraint in steps:**
   ```sql
   -- Step 1: Add column without constraint
   ALTER TABLE child_table ADD COLUMN parent_id INT;

   -- Step 2: Populate column
   UPDATE child_table SET parent_id = ...;

   -- Step 3: Add constraint
   ALTER TABLE child_table
   ADD CONSTRAINT fk_parent
   FOREIGN KEY (parent_id) REFERENCES parent_table(id);
   ```

3. **Use NOT VALID initially:**
   ```sql
   -- Add constraint without validating existing data
   ALTER TABLE child_table
   ADD CONSTRAINT fk_parent
   FOREIGN KEY (parent_id) REFERENCES parent_table(id)
   NOT VALID;

   -- Later, validate in background
   ALTER TABLE child_table VALIDATE CONSTRAINT fk_parent;
   ```

### Problem: Data Loss After Migration

**Symptoms:**
- Row counts don't match
- Data missing after migration
- Users reporting lost data

**Solutions:**

1. **Immediate rollback:**
   ```bash
   ai-shell migration rollback migrations/XXX.ts --database production
   ```

2. **Restore from backup:**
   ```bash
   ai-shell migration restore-backup <backup-id>
   ```

3. **Investigate root cause:**
   ```sql
   -- Check migration logs
   SELECT * FROM migration_log WHERE migration = 'XXX';

   -- Find deleted data in backup
   -- Restore specific tables if possible
   ```

### Problem: Application Breaks After Migration

**Symptoms:**
- Application errors after migration
- Missing columns or tables
- Type mismatch errors

**Solutions:**

1. **Check application compatibility:**
   ```bash
   # Run integration tests
   npm test

   # Check application logs
   kubectl logs -f deployment/app
   ```

2. **Quick fix if minor:**
   ```typescript
   // Add migration to fix issue
   export const up = async (db) => {
     // Fix the incompatibility
   };
   ```

3. **Rollback if major:**
   ```bash
   ai-shell migration rollback migrations/XXX.ts
   ```

## Next Steps

### Advanced Topics

1. **[Zero-Downtime Migrations](./zero-downtime-migrations.md)**
   - Online schema changes
   - Blue-green deployments
   - Gradual migration strategies

2. **[Data Migration Patterns](./data-migration-patterns.md)**
   - Backfilling data
   - Transforming data
   - Migrating between databases

3. **[Migration CI/CD](./migration-cicd.md)**
   - Automated testing
   - Deployment pipelines
   - Continuous delivery

### Related Tutorials

- **[Schema Diff](./schema-diff-tutorial.md)** - Compare and sync schemas
- **[SQL Explainer](./sql-explainer-tutorial.md)** - Optimize migration performance
- **[Query Cache](./query-cache-tutorial.md)** - Cache after migrations

### API Reference

- **[Migration API](../../api/migration-api.md)**
- **[CLI Commands](../../cli/migration-commands.md)**

---

**Tutorial Version:** 1.0.0
**Last Updated:** 2025-10-30
**Estimated Time:** 60 minutes
**Difficulty:** Intermediate

**License:** MIT
