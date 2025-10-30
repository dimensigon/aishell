# Schema Diff Tutorial

Learn how to compare database schemas, detect differences, and generate migration scripts automatically with AI-Shell's Schema Diff tool.

## Table of Contents

1. [What You'll Learn](#what-youll-learn)
2. [Prerequisites](#prerequisites)
3. [Part 1: Understanding Schema Diffing](#part-1-understanding-schema-diffing-5-min)
4. [Part 2: Basic Schema Comparison](#part-2-basic-schema-comparison-10-min)
5. [Part 3: Analyzing Differences](#part-3-analyzing-differences-15-min)
6. [Part 4: Generating Migrations](#part-4-generating-migrations-15-min)
7. [Part 5: Multi-Environment Sync](#part-5-multi-environment-sync-10-min)
8. [Part 6: Advanced Diff Strategies](#part-6-advanced-diff-strategies-10-min)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Next Steps](#next-steps)

## What You'll Learn

By the end of this tutorial, you will:

- Compare schemas between databases
- Identify schema differences (tables, columns, indexes, constraints)
- Generate migration scripts automatically
- Synchronize schemas across environments
- Handle complex schema changes safely
- Detect schema drift in production
- Create database documentation from schemas
- Implement schema versioning strategies

**Estimated Time:** 65 minutes

## Prerequisites

Before starting this tutorial, ensure you have:

- AI-Shell installed and configured
- Access to at least two databases (dev, staging, or production)
- Basic understanding of database schemas
- Familiarity with SQL DDL statements
- 65 minutes of focused time

## Part 1: Understanding Schema Diffing (5 min)

### What is Schema Diffing?

Schema diffing compares two database schemas to find differences in:

- **Tables**: Added, removed, or modified tables
- **Columns**: New columns, dropped columns, data type changes
- **Indexes**: Missing or extra indexes
- **Constraints**: Primary keys, foreign keys, unique constraints, check constraints
- **Views**: Created or dropped views
- **Functions**: Stored procedures and functions
- **Triggers**: Database triggers
- **Sequences**: Auto-increment sequences

### Why Schema Diff Matters

**Common Use Cases:**

1. **Environment Synchronization**
   ```
   Development → Staging → Production
   Ensure all environments have identical schemas
   ```

2. **Deployment Validation**
   ```
   Before deploying:
   - Compare prod schema with migration target
   - Ensure migrations cover all changes
   - Detect unexpected drift
   ```

3. **Disaster Recovery**
   ```
   Compare backup schema with current schema
   Identify what changed since last backup
   ```

4. **Multi-Tenant Applications**
   ```
   Ensure all tenant databases have same schema
   Detect schema inconsistencies
   ```

5. **Database Documentation**
   ```
   Generate schema change reports
   Track schema evolution over time
   ```

### Schema Diff Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                  1. Connect to Databases                     │
│              Source (dev) and Target (prod)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   2. Extract Schemas                         │
│     Read table definitions, indexes, constraints, etc.       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    3. Compare Schemas                        │
│          Identify additions, deletions, modifications        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  4. Generate Diff Report                     │
│           Visual report of all differences                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 5. Generate Migration SQL                    │
│      CREATE, ALTER, DROP statements to sync schemas         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   6. Review & Apply                          │
│           Test migration, then apply to target               │
└─────────────────────────────────────────────────────────────┘
```

### Types of Schema Changes

**1. Additive Changes (Low Risk)**
- Add new tables
- Add new columns with defaults
- Add new indexes
- Add new constraints (non-enforcing)

**2. Modifying Changes (Medium Risk)**
- Rename columns
- Change column types
- Modify constraints
- Alter indexes

**3. Destructive Changes (High Risk)**
- Drop tables
- Drop columns
- Remove indexes
- Drop constraints

## Part 2: Basic Schema Comparison (10 min)

### Step 1: Compare Two Databases

Compare development and production schemas:

```bash
ai-shell schema diff \
  --source "postgresql://localhost/myapp_dev" \
  --target "postgresql://prod.example.com/myapp_prod"
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCHEMA DIFF REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Source: myapp_dev (PostgreSQL 15.2)
Target: myapp_prod (PostgreSQL 15.2)
Comparison Date: 2025-10-30 14:30:00 UTC

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Differences: 12

Tables:           2 added, 0 removed, 3 modified
Columns:          5 added, 1 removed, 2 modified
Indexes:          4 added, 0 removed
Constraints:      3 added, 0 removed
Views:            1 added, 0 removed
Functions:        0 added, 0 removed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TABLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

➕ Added Tables (2):

  1. user_profiles
     Columns: 7
     Indexes: 2
     Constraints: 1 foreign key

  2. notification_preferences
     Columns: 5
     Indexes: 1
     Constraints: 1 foreign key

🔄 Modified Tables (3):

  1. users
     ➕ Added column: email_verified (boolean)
     ➕ Added column: email_verified_at (timestamp)
     🔄 Modified column: bio (varchar(255) → varchar(500))

  2. orders
     ➕ Added index: idx_orders_user_id_status
     ➕ Added constraint: check_positive_total

  3. products
     ➕ Added column: featured (boolean DEFAULT false)
     ➕ Added index: idx_products_featured

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INDEXES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

➕ Added Indexes (4):

  1. idx_orders_user_id_status
     Table: orders
     Columns: (user_id, status)
     Type: btree

  2. idx_products_featured
     Table: products
     Columns: (featured) WHERE featured = true
     Type: btree (partial)

  3. idx_user_profiles_user_id
     Table: user_profiles
     Columns: (user_id)
     Type: btree

  4. idx_notification_preferences_user_id
     Table: notification_preferences
     Columns: (user_id)
     Type: btree

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONSTRAINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

➕ Added Constraints (3):

  1. fk_user_profiles_user_id
     Table: user_profiles
     Type: FOREIGN KEY
     References: users(id) ON DELETE CASCADE

  2. fk_notification_preferences_user_id
     Table: notification_preferences
     Type: FOREIGN KEY
     References: users(id) ON DELETE CASCADE

  3. check_positive_total
     Table: orders
     Type: CHECK
     Condition: total_amount > 0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RISK ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall Risk: LOW

✓ No destructive changes detected
✓ All new columns have defaults
✓ All constraints are additive
⚠ Column type change requires validation: users.bio

Estimated Migration Time: 15 seconds
Recommended Maintenance Window: Not required
```

### Step 2: Save Diff Report

Save the report for review:

```bash
ai-shell schema diff \
  --source dev \
  --target prod \
  --output diff-report.json \
  --format json
```

### Step 3: Visual Diff Report

Generate an HTML visualization:

```bash
ai-shell schema diff \
  --source dev \
  --target prod \
  --output diff-report.html \
  --format html \
  --visualize
```

Opens a visual report in your browser showing:
- Side-by-side schema comparison
- Highlighted differences
- Interactive table/column browser
- Generated migration SQL

### Step 4: Using TypeScript API

```typescript
// schema-diff.ts
import { AIShell } from 'ai-shell';

async function compareDatabases() {
  const shell = new AIShell();

  const diff = await shell.schema.diff({
    source: {
      type: 'postgresql',
      host: 'localhost',
      database: 'myapp_dev',
      user: 'dev',
      password: process.env.DEV_DB_PASSWORD,
    },
    target: {
      type: 'postgresql',
      host: 'prod.example.com',
      database: 'myapp_prod',
      user: 'readonly',
      password: process.env.PROD_DB_PASSWORD,
    },
  });

  console.log('Differences found:', diff.totalDifferences);

  // Tables
  console.log('\nTables:');
  console.log('  Added:', diff.tables.added.length);
  console.log('  Removed:', diff.tables.removed.length);
  console.log('  Modified:', diff.tables.modified.length);

  // Details
  diff.tables.added.forEach(table => {
    console.log(`  + ${table.name} (${table.columns.length} columns)`);
  });

  // Generate migration
  const migration = await shell.schema.generateMigration(diff);
  console.log('\nGenerated migration SQL:');
  console.log(migration.sql);

  // Save migration
  await shell.schema.saveMigration(migration, 'migrations/sync-prod.sql');
}

compareDatabases().catch(console.error);
```

## Part 3: Analyzing Differences (15 min)

### Detailed Diff Analysis

Get comprehensive difference details:

```bash
ai-shell schema diff-analyze \
  --source dev \
  --target prod \
  --detailed
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETAILED SCHEMA ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Table: users

Source (dev):
  Columns: 12
  Indexes: 4
  Constraints: 5
  Size: 2.4 GB

Target (prod):
  Columns: 10
  Indexes: 3
  Constraints: 4
  Size: 5.8 GB

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Column Differences:

➕ email_verified
   Type: boolean
   Nullable: YES
   Default: false
   Impact: No data migration needed (has default)
   Risk: LOW

➕ email_verified_at
   Type: timestamp without time zone
   Nullable: YES
   Default: NULL
   Impact: No data migration needed
   Risk: LOW

🔄 bio
   Source:  varchar(255)
   Target:  varchar(500)
   Change:  Length increased (255 → 500)
   Impact:  Existing data preserved
   Risk:    LOW
   Note:    No truncation risk

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Index Differences:

➕ idx_users_email_verified
   Columns: (email_verified) WHERE email_verified = false
   Type: btree (partial)
   Size estimate: 50 MB
   Build time estimate: 12 seconds
   Impact: Improves queries filtering unverified users
   Risk: LOW (partial index, small overhead)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Constraint Differences:

➕ check_email_verified_at
   Type: CHECK
   Condition: (email_verified = false) OR (email_verified_at IS NOT NULL)
   Impact: Ensures verified_at is set when verified
   Risk: MEDIUM - May fail if existing data inconsistent
   Recommendation: Validate data before applying

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Migration Order:

1. Add email_verified column
2. Add email_verified_at column
3. Alter bio column length
4. Validate data for check constraint
5. Add check_email_verified_at constraint
6. Create idx_users_email_verified index

Estimated Total Time: 25 seconds
```

### Comparing Specific Tables

Compare individual tables:

```bash
ai-shell schema diff-table users \
  --source dev \
  --target prod
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TABLE COMPARISON: users
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Columns:
╔════════════════════╦════════════════╦════════════════╦══════════╗
║ Column             ║ Source (dev)   ║ Target (prod)  ║ Status   ║
╠════════════════════╬════════════════╬════════════════╬══════════╣
║ id                 ║ integer        ║ integer        ║ Same     ║
║ email              ║ varchar(255)   ║ varchar(255)   ║ Same     ║
║ name               ║ varchar(255)   ║ varchar(255)   ║ Same     ║
║ bio                ║ varchar(500)   ║ varchar(255)   ║ Modified ║
║ created_at         ║ timestamp      ║ timestamp      ║ Same     ║
║ updated_at         ║ timestamp      ║ timestamp      ║ Same     ║
║ email_verified     ║ boolean        ║ -              ║ Added    ║
║ email_verified_at  ║ timestamp      ║ -              ║ Added    ║
╚════════════════════╩════════════════╩════════════════╩══════════╝

Indexes:
╔══════════════════════════╦════════════════════╦═══════════╗
║ Index                    ║ Columns            ║ Status    ║
╠══════════════════════════╬════════════════════╬═══════════╣
║ users_pkey               ║ (id)               ║ Same      ║
║ idx_users_email          ║ (email)            ║ Same      ║
║ idx_users_created_at     ║ (created_at)       ║ Same      ║
║ idx_users_email_verified ║ (email_verified)   ║ Added     ║
╚══════════════════════════╩════════════════════╩═══════════╝

Constraints:
╔════════════════════════════╦════════════╦══════════╗
║ Constraint                 ║ Type       ║ Status   ║
╠════════════════════════════╬════════════╬══════════╣
║ users_pkey                 ║ PRIMARY    ║ Same     ║
║ users_email_unique         ║ UNIQUE     ║ Same     ║
║ check_email_format         ║ CHECK      ║ Same     ║
║ check_email_verified_at    ║ CHECK      ║ Added    ║
╚════════════════════════════╩════════════╩══════════╝
```

### Detecting Schema Drift

Monitor for unexpected changes:

```bash
ai-shell schema drift-detect \
  --baseline schema-baseline.json \
  --current prod
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCHEMA DRIFT DETECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Baseline: schema-baseline.json (2025-10-15 00:00:00)
Current:  production database (2025-10-30 14:30:00)
Duration: 15 days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  UNEXPECTED CHANGES DETECTED

🔴 Critical Drift:

  1. Table "temp_exports" exists in production
     Created: ~7 days ago
     Rows: 45,231
     Size: 1.2 GB
     Issue: Undocumented table, not in baseline
     Action: Investigate origin and purpose

  2. Index "idx_users_last_login" was dropped
     Dropped: ~3 days ago
     Issue: Missing index may affect query performance
     Impact: Queries on last_login are now slower
     Action: Restore index or update baseline

🟡 Minor Drift:

  3. Column "users.metadata" type changed
     Before: jsonb
     After:  text
     Changed: ~5 days ago
     Issue: Data type downgrade, loss of JSON validation
     Action: Verify intentional change

  4. Constraint "check_positive_total" was disabled
     Disabled: ~2 days ago
     Issue: Data validation constraint not enforcing
     Action: Re-enable or remove constraint

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Expected Changes (from migrations):

✓ Added table "user_profiles"
✓ Added columns to "orders" table
✓ Created indexes on "products"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recommendations:

1. Investigate unexpected table "temp_exports"
2. Restore dropped index "idx_users_last_login"
3. Update baseline with approved changes
4. Review change control process

Update baseline? [Y/n]:
```

## Part 4: Generating Migrations (15 min)

### Auto-Generate Migration SQL

Generate migration to sync schemas:

```bash
ai-shell schema generate-migration \
  --source dev \
  --target prod \
  --output migrations/sync-prod.sql
```

**Generated Migration:**

```sql
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Schema Sync Migration: dev → prod
-- Generated: 2025-10-30 14:30:00 UTC
-- AI-Shell v2.0.0
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- UP MIGRATION
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BEGIN;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 1. Add new tables
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Create table: user_profiles
CREATE TABLE user_profiles (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  bio VARCHAR(500),
  avatar_url VARCHAR(255),
  location VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT fk_user_profiles_user_id
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);

-- Create table: notification_preferences
CREATE TABLE notification_preferences (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL UNIQUE,
  email_notifications BOOLEAN DEFAULT true,
  push_notifications BOOLEAN DEFAULT true,
  sms_notifications BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT fk_notification_preferences_user_id
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 2. Modify existing tables
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Table: users

-- Add column: email_verified
ALTER TABLE users
ADD COLUMN email_verified BOOLEAN DEFAULT false NOT NULL;

-- Add column: email_verified_at
ALTER TABLE users
ADD COLUMN email_verified_at TIMESTAMP;

-- Modify column: bio (increase length)
ALTER TABLE users
ALTER COLUMN bio TYPE VARCHAR(500);

-- Add check constraint
ALTER TABLE users
ADD CONSTRAINT check_email_verified_at
CHECK (
  (email_verified = false) OR
  (email_verified_at IS NOT NULL)
);

-- Table: products

-- Add column: featured
ALTER TABLE products
ADD COLUMN featured BOOLEAN DEFAULT false NOT NULL;

-- Table: orders

-- Add check constraint
ALTER TABLE orders
ADD CONSTRAINT check_positive_total
CHECK (total_amount > 0);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 3. Create indexes
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Index on user_profiles.user_id
CREATE INDEX idx_user_profiles_user_id
ON user_profiles(user_id);

-- Index on notification_preferences.user_id
CREATE INDEX idx_notification_preferences_user_id
ON notification_preferences(user_id);

-- Composite index on orders (user_id, status)
CREATE INDEX idx_orders_user_id_status
ON orders(user_id, status);

-- Partial index on products.featured
CREATE INDEX idx_products_featured
ON products(featured)
WHERE featured = true;

-- Partial index on users.email_verified
CREATE INDEX idx_users_email_verified
ON users(email_verified)
WHERE email_verified = false;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 4. Create views
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- View: user_profile_summary
CREATE VIEW user_profile_summary AS
SELECT
  u.id,
  u.email,
  u.name,
  u.email_verified,
  u.created_at,
  up.bio,
  up.location,
  np.email_notifications,
  np.push_notifications
FROM users u
LEFT JOIN user_profiles up ON u.id = up.user_id
LEFT JOIN notification_preferences np ON u.id = np.user_id;

COMMIT;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- DOWN MIGRATION (Rollback)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Uncomment to create rollback script:

-- BEGIN;
--
-- -- Drop views
-- DROP VIEW IF EXISTS user_profile_summary;
--
-- -- Drop indexes
-- DROP INDEX IF EXISTS idx_users_email_verified;
-- DROP INDEX IF EXISTS idx_products_featured;
-- DROP INDEX IF EXISTS idx_orders_user_id_status;
-- DROP INDEX IF EXISTS idx_notification_preferences_user_id;
-- DROP INDEX IF EXISTS idx_user_profiles_user_id;
--
-- -- Remove constraints
-- ALTER TABLE orders DROP CONSTRAINT IF EXISTS check_positive_total;
-- ALTER TABLE users DROP CONSTRAINT IF EXISTS check_email_verified_at;
--
-- -- Remove columns
-- ALTER TABLE products DROP COLUMN IF EXISTS featured;
-- ALTER TABLE users DROP COLUMN IF EXISTS email_verified_at;
-- ALTER TABLE users DROP COLUMN IF EXISTS email_verified;
--
-- -- Revert column modifications
-- ALTER TABLE users ALTER COLUMN bio TYPE VARCHAR(255);
--
-- -- Drop tables
-- DROP TABLE IF EXISTS notification_preferences CASCADE;
-- DROP TABLE IF EXISTS user_profiles CASCADE;
--
-- COMMIT;
```

### Safe Migration Generation

Generate migration with safety checks:

```bash
ai-shell schema generate-migration \
  --source dev \
  --target prod \
  --safe \
  --validate \
  --backup \
  --output migrations/sync-prod.sql
```

**Options:**
- `--safe`: Add rollback script and transaction wrapper
- `--validate`: Include data validation steps
- `--backup`: Create backup before applying
- `--dry-run`: Show what would be generated without creating file

### TypeScript API for Migration Generation

```typescript
// generate-migration.ts
import { AIShell } from 'ai-shell';

async function generateMigration() {
  const shell = new AIShell();

  // Compare schemas
  const diff = await shell.schema.diff({
    source: 'dev',
    target: 'prod',
  });

  // Generate migration
  const migration = await shell.schema.generateMigration(diff, {
    safe: true,
    includeRollback: true,
    transactional: true,

    // Migration metadata
    name: 'sync_prod_from_dev',
    description: 'Sync production with development schema changes',
    author: 'dev-team',

    // Safety options
    validateData: true,
    createBackup: true,
    dryRun: false,

    // Ordering
    orderStrategy: 'dependency',  // Respect foreign key dependencies

    // Formatting
    format: {
      indent: 2,
      comments: true,
      groupByType: true,
    },
  });

  console.log('Migration generated:');
  console.log(`  File: ${migration.filename}`);
  console.log(`  Statements: ${migration.statementCount}`);
  console.log(`  Estimated time: ${migration.estimatedTime}s`);
  console.log(`  Risk level: ${migration.riskLevel}`);

  // Save migration
  await shell.schema.saveMigration(migration, 'migrations/');

  console.log('\n✓ Migration saved successfully');
}

generateMigration().catch(console.error);
```

### Customize Migration Template

Use custom templates for migrations:

```typescript
// custom-migration-template.ts
export const migrationTemplate = {
  header: `
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Migration: {{name}}
-- Description: {{description}}
-- Author: {{author}}
-- Generated: {{timestamp}}
-- Risk Level: {{riskLevel}}
-- Estimated Time: {{estimatedTime}}
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`,

  upMigration: `
BEGIN;

-- Backup data before changes
{{#if needsBackup}}
CREATE TABLE _backup_{{tableName}}_{{timestamp}} AS
SELECT * FROM {{tableName}};
{{/if}}

-- Apply changes
{{#each statements}}
{{this}};
{{/each}}

-- Validate changes
{{#each validations}}
DO $$
BEGIN
  IF NOT ({{this.condition}}) THEN
    RAISE EXCEPTION '{{this.message}}';
  END IF;
END $$;
{{/each}}

COMMIT;
`,

  downMigration: `
BEGIN;

-- Rollback changes
{{#each rollbackStatements}}
{{this}};
{{/each}}

COMMIT;
`,
};

// Use custom template
await shell.schema.generateMigration(diff, {
  template: migrationTemplate,
});
```

## Part 5: Multi-Environment Sync (10 min)

### Syncing Multiple Environments

Compare and sync across dev, staging, production:

```bash
ai-shell schema sync \
  --source dev \
  --targets staging,prod \
  --strategy sequential
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MULTI-ENVIRONMENT SCHEMA SYNC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Source: dev
Targets: staging, prod
Strategy: Sequential (dev → staging → prod)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stage 1: dev → staging

Comparing schemas...
✓ Differences found: 8

Generating migration...
✓ Migration generated: migrations/dev-to-staging.sql

Apply migration to staging? [Y/n]: y

Creating backup...
✓ Backup created: staging_backup_20251030_143000

Running migration...
✓ Migration completed in 12.3s

Validating changes...
✓ Schema sync successful
✓ All tests passed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stage 2: staging → prod

Comparing schemas...
✓ Schemas identical

✓ Staging and production schemas are in sync
  No migration needed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYNC SUMMARY

✓ dev → staging: 8 changes applied
✓ staging → prod: Already in sync

All environments synchronized successfully!
```

### Environment Validation

Ensure all environments match a baseline:

```bash
ai-shell schema validate-environments \
  --baseline prod \
  --environments dev,staging,test
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENVIRONMENT VALIDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Baseline: prod
Environments: dev, staging, test

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ staging: Matches baseline (0 differences)

⚠️  dev: 5 differences from baseline
    - 2 tables added (user_profiles, notifications)
    - 3 columns added
    - Expected for development environment

❌ test: 12 differences from baseline
    - 1 table missing (products)
    - 8 indexes missing
    - Requires sync!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recommendations:

1. test environment requires sync
   Run: ai-shell schema sync --source prod --target test

2. dev environment has expected differences
   Consider creating feature branch baseline

Sync test environment now? [Y/n]:
```

## Part 6: Advanced Diff Strategies (10 min)

### Filtered Comparison

Compare only specific schema elements:

```bash
# Only compare tables and columns (ignore indexes)
ai-shell schema diff \
  --source dev \
  --target prod \
  --include tables,columns \
  --exclude indexes,constraints

# Only compare specific tables
ai-shell schema diff \
  --source dev \
  --target prod \
  --tables users,orders,products

# Ignore specific tables (e.g., logs, temp tables)
ai-shell schema diff \
  --source dev \
  --target prod \
  --ignore-tables audit_logs,temp_*,_backup_*
```

### Semantic Diff

Compare schemas semantically (ignoring cosmetic differences):

```bash
ai-shell schema diff \
  --source dev \
  --target prod \
  --semantic \
  --ignore-comments \
  --ignore-order
```

**Ignores:**
- Comment changes
- Column order changes
- Index naming differences (if functionally same)
- Whitespace differences

### Historical Comparison

Compare current schema with historical version:

```bash
ai-shell schema diff \
  --source prod \
  --target prod@2025-10-01 \
  --show-history
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCHEMA EVOLUTION: prod (Oct 1 → Oct 30)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Timeline of Changes:

2025-10-05: Added table user_profiles
  Migration: 001_add_user_profiles
  Author: dev-team

2025-10-12: Modified users table
  - Added email_verified column
  - Added email_verified_at column
  Migration: 002_add_email_verification
  Author: dev-team

2025-10-18: Added indexes
  - idx_orders_user_id_status
  - idx_products_featured
  Migration: 003_performance_indexes
  Author: dba-team

2025-10-25: Added table notification_preferences
  Migration: 004_add_notifications
  Author: dev-team

Total Changes: 4 migrations, 15 schema objects modified
```

### Custom Diff Rules

Define custom comparison rules:

```typescript
// custom-diff-rules.ts
export const diffRules = {
  // Ignore auto-generated columns
  ignoreColumns: [
    /^_.*$/,        // Columns starting with underscore
    /^created_by$/,  // Audit columns
    /^updated_by$/,
  ],

  // Ignore temp tables
  ignoreTables: [
    /^temp_/,
    /^_backup_/,
    /^staging_/,
  ],

  // Consider these columns equivalent
  columnEquivalence: {
    'varchar(255)': 'character varying(255)',
    'int': 'integer',
    'bool': 'boolean',
  },

  // Ignore index differences if semantically same
  semanticIndexes: true,

  // Ignore constraint naming differences
  ignoreConstraintNames: true,
};

// Use custom rules
await shell.schema.diff({
  source: 'dev',
  target: 'prod',
  rules: diffRules,
});
```

## Best Practices

### Do's ✅

1. **Always Compare Before Deploying**
   - Verify migration covers all changes
   - Check for unexpected differences
   - Review generated SQL carefully

2. **Use Source Control for Schemas**
   ```bash
   # Save schema snapshots
   ai-shell schema export dev > schemas/dev-$(date +%Y%m%d).sql
   git add schemas/
   git commit -m "Schema snapshot: dev"
   ```

3. **Validate Across Environments**
   - Ensure dev, staging, prod are in sync
   - Test migrations on staging before prod
   - Monitor for schema drift

4. **Generate Rollback Scripts**
   - Always include down migrations
   - Test rollback procedures
   - Keep rollback scripts with migrations

5. **Document Schema Changes**
   ```sql
   -- Migration description
   -- Why: Add email verification feature
   -- Impact: No downtime, backward compatible
   -- Rollback: Run down migration
   ```

6. **Use Transactions**
   - Wrap migrations in BEGIN/COMMIT
   - Automatic rollback on errors
   - Maintain consistency

7. **Create Backups Before Sync**
   ```bash
   ai-shell schema sync --backup --source dev --target prod
   ```

8. **Monitor Schema Health**
   ```bash
   # Regular drift detection
   ai-shell schema drift-detect --baseline prod --schedule daily
   ```

### Don'ts ❌

1. **Don't Modify Production Directly**
   - Always go through dev → staging → prod
   - Use migrations, not manual changes
   - Document all changes

2. **Don't Ignore Drift Warnings**
   - Investigate unexpected changes
   - Update baseline or fix drift
   - Don't accumulate technical debt

3. **Don't Skip Testing**
   - Test migrations on staging
   - Validate data integrity
   - Check application compatibility

4. **Don't Compare Incompatible Versions**
   - Ensure compatible database versions
   - Check for version-specific features
   - Test cross-version migrations

5. **Don't Forget About Data**
   - Schema changes may require data migration
   - Validate existing data compatibility
   - Plan for large dataset migrations

6. **Don't Auto-Apply in Production**
   - Always review before applying
   - Schedule maintenance windows
   - Have rollback plan ready

7. **Don't Ignore Permissions**
   - Check user has ALTER privileges
   - Verify constraint permissions
   - Test with production-like permissions

8. **Don't Mix Schema and Data Changes**
   - Keep schema migrations separate
   - Use data migrations for data changes
   - Easier to track and rollback

## Troubleshooting

### Problem: Diff Shows Too Many Differences

**Symptom**: Hundreds of differences reported

**Causes:**
1. Comparing wrong databases
2. Missing schema baseline
3. Development changes not tracked

**Solutions:**

```bash
# Filter to specific areas
ai-shell schema diff --source dev --target prod --tables users,orders

# Ignore unimportant differences
ai-shell schema diff --source dev --target prod --semantic --ignore-comments

# Use baseline
ai-shell schema diff --baseline schema-baseline.json --target prod
```

### Problem: Generated Migration Fails

**Symptom**: Migration SQL fails when applied

**Causes:**
1. Foreign key dependency order wrong
2. Missing data for constraints
3. Incompatible data types

**Solutions:**

```bash
# Generate with dependency ordering
ai-shell schema generate-migration \
  --source dev \
  --target prod \
  --order-by-dependency

# Add data validation
ai-shell schema generate-migration \
  --source dev \
  --target prod \
  --validate-data

# Dry run first
ai-shell schema generate-migration \
  --source dev \
  --target prod \
  --dry-run
```

### Problem: Cannot Detect Some Differences

**Symptom**: Known differences not showing up

**Solutions:**

```bash
# Update statistics
ai-shell schema refresh dev prod

# Clear cache
ai-shell schema clear-cache

# Verbose output
ai-shell schema diff --source dev --target prod --verbose
```

## Next Steps

### Advanced Topics

1. **[Migration Tester](./migration-tester-tutorial.md)** - Test schema changes safely
2. **[Cost Optimizer](./cost-optimizer-tutorial.md)** - Optimize schema performance
3. **[Schema Versioning Guide](../advanced/schema-versioning.md)** - Version control schemas

### Related Tutorials

- **[Query Cache](./query-cache-tutorial.md)** - Cache query results
- **[SQL Explainer](./sql-explainer-tutorial.md)** - Understand query plans

### API Reference

- **[Schema Diff API](../../api/schema-diff-api.md)**
- **[Migration API](../../api/migration-api.md)**

---

**Tutorial Version:** 1.0.0
**Last Updated:** 2025-10-30
**Estimated Time:** 65 minutes
**Difficulty:** Intermediate

**License:** MIT
