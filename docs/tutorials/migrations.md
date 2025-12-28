# Schema Management and Migrations Tutorial

> **📋 Implementation Status**
>
> **Current Status:** In Development
> **CLI Availability:** Partial
> **Completeness:** 35%
>
> **What Works Now:**
> - Basic schema inspection
> - Manual DDL execution
> - Database connection management
>
> **Coming Soon:**
> - Natural language schema change descriptions
> - Automatic migration generation
> - Migration history tracking
> - Zero-downtime migration strategies
> - Rollback capabilities
> - Schema versioning and comparison
> - Cross-database migration coordination
>
> **Note:** This tutorial describes the intended functionality. Check the [Gap Analysis Report](../FEATURE_GAP_ANALYSIS_REPORT.md) for detailed implementation status.

## Introduction and Overview

AI-Shell revolutionizes database schema management by allowing you to describe schema changes in natural language, automatically generating and applying migrations with built-in safety checks, rollback capabilities, and zero-downtime strategies for production environments.

This tutorial will teach you how to:
- Create schema changes using natural language
- Generate and review migration scripts
- Apply migrations safely with automatic rollback
- Perform zero-downtime schema changes
- Track and version database schemas
- Handle complex migration scenarios

**What You'll Learn:**
- Natural language schema management
- Migration generation and execution
- Schema versioning and tracking
- Zero-downtime migration strategies
- Rollback and recovery procedures
- Cross-database schema management
- Migration testing and validation

**Time to Complete:** 30-40 minutes

---

## Prerequisites

Before starting this tutorial, ensure you have:

### Required
- AI-Shell installed (v1.0.0 or higher)
  ```bash
  npm install -g ai-shell
  ```
- Database connection with DDL permissions
  ```bash
  ai-shell connect postgres://user:pass@localhost:5432/mydb
  ```
- Anthropic API key configured
  ```bash
  export ANTHROPIC_API_KEY="your-api-key"
  ```

### Recommended
- Development or test database for practice (not production initially)
- Basic understanding of database schema concepts
- Version control system (Git) for tracking migrations
- Backup of your database before starting

### Verify Your Setup
```bash
# Check migration features are available
ai-shell features check migrations
# Expected: ✓ Migration features enabled

# Verify DDL permissions
ai-shell check-permissions --feature migrations
# Expected: ✓ CREATE, ALTER, DROP permissions

# Check current schema version
ai-shell schema version
# Expected: Shows current schema version or "Not initialized"

# Initialize migration tracking (if needed)
ai-shell migrate init
# Expected: ✓ Migration tracking initialized
```

---

## Step-by-Step Instructions

### Step 1: Your First Schema Change with Natural Language

Let's create a simple schema change using natural language.

```bash
# Add a new column using natural language
ai-shell migrate "add email field to users table"

# AI-Shell processes the request:
# 🔍 Analyzing schema change request...
#
# Current Schema:
#   Table: users
#   Columns: id (int), name (varchar), created_at (timestamp)
#
# Proposed Changes:
#   + Add column: email (varchar(255))
#   + Add constraint: email is NOT NULL with default ''
#   + Add index: idx_users_email for performance
#
# Generated Migration:
#   -- Migration: add_email_to_users
#   -- Created: 2025-10-28 15:00:00
#
#   -- Up Migration
#   ALTER TABLE users ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT '';
#   CREATE INDEX idx_users_email ON users(email);
#
#   -- Down Migration (rollback)
#   DROP INDEX idx_users_email;
#   ALTER TABLE users DROP COLUMN email;
#
# Apply this migration? [y/N]: y
#
# 🔄 Applying migration...
# ✓ Migration applied successfully
# ✓ Schema version: 1 → 2
#
# Summary:
#   Migration ID: 002_add_email_to_users
#   Status: Applied
#   Duration: 234ms
#   Rollback available: Yes

# More examples of natural language migrations
ai-shell migrate "make email field unique in users table"
ai-shell migrate "add created_at and updated_at timestamps to products"
ai-shell migrate "create orders table with customer_id foreign key"
ai-shell migrate "rename column username to user_name in accounts"
```

---

### Step 2: Understanding Migration Structure

AI-Shell creates structured migrations with up/down paths.

```bash
# Generate migration without applying
ai-shell migrate "add phone field to users" --generate-only

# AI-Shell creates migration file:
# migrations/003_add_phone_to_users.sql
#
# Content:
# -- ===================================
# -- Migration: add_phone_to_users
# -- Version: 003
# -- Created: 2025-10-28 15:05:00
# -- Description: Add phone field to users table
# -- ===================================
#
# -- Up Migration
# BEGIN;
#
# -- Add phone column
# ALTER TABLE users ADD COLUMN phone VARCHAR(20);
#
# -- Add validation (E.164 format)
# ALTER TABLE users ADD CONSTRAINT check_phone_format
#   CHECK (phone ~ '^\+?[1-9]\d{1,14}$');
#
# -- Add index for phone lookups
# CREATE INDEX idx_users_phone ON users(phone);
#
# -- Update schema version
# INSERT INTO schema_migrations (version, name, applied_at)
# VALUES (3, 'add_phone_to_users', NOW());
#
# COMMIT;
#
# -- Down Migration (Rollback)
# BEGIN;
#
# DROP INDEX IF EXISTS idx_users_phone;
# ALTER TABLE users DROP CONSTRAINT IF EXISTS check_phone_format;
# ALTER TABLE users DROP COLUMN IF EXISTS phone;
#
# DELETE FROM schema_migrations WHERE version = 3;
#
# COMMIT;

# Review generated migration
ai-shell migrate review 003_add_phone_to_users

# Edit migration if needed
ai-shell migrate edit 003_add_phone_to_users

# Apply reviewed migration
ai-shell migrate apply 003_add_phone_to_users
```

---

### Step 3: Managing Migration History

Track and manage your schema evolution over time.

```bash
# View migration history
ai-shell migrate history

# Output:
# 📜 Migration History
#
# ✓ 001_initial_schema (2025-10-20 10:00:00)
#   Created users, products, orders tables
#   Status: Applied
#
# ✓ 002_add_email_to_users (2025-10-28 15:00:00)
#   Added email column to users
#   Status: Applied
#
# ✓ 003_add_phone_to_users (2025-10-28 15:05:00)
#   Added phone column to users
#   Status: Applied
#
# Current Schema Version: 3
# Pending Migrations: 0

# View detailed migration info
ai-shell migrate info 002_add_email_to_users

# Output:
# 📋 Migration Details
#
# ID: 002_add_email_to_users
# Version: 2
# Description: Add email field to users table
# Applied: 2025-10-28 15:00:00
# Duration: 234ms
# Applied By: admin
#
# Changes:
#   + Added column: users.email (varchar(255))
#   + Added index: idx_users_email
#
# SQL:
#   ALTER TABLE users ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT '';
#   CREATE INDEX idx_users_email ON users(email);
#
# Rollback Available: Yes
# Dependencies: None
# Affected Rows: 1,247 (users table)

# Export migration history
ai-shell migrate history --export migrations-log.json
```

---

### Step 4: Rolling Back Migrations

Safely undo schema changes when needed.

```bash
# Rollback last migration
ai-shell migrate rollback

# Output:
# ⚠️  Rolling back migration: 003_add_phone_to_users
#
# This will:
#   - Drop index: idx_users_phone
#   - Remove constraint: check_phone_format
#   - Drop column: users.phone
#
# Continue? [y/N]: y
#
# 🔄 Rolling back...
# ✓ Index dropped
# ✓ Constraint removed
# ✓ Column dropped
# ✓ Schema version: 3 → 2
#
# ✓ Rollback successful
# Duration: 189ms

# Rollback to specific version
ai-shell migrate rollback --to-version 1

# Output:
# ⚠️  Rolling back 2 migrations:
#   - 003_add_phone_to_users
#   - 002_add_email_to_users
#
# This will revert schema to version 1
# Continue? [y/N]: y
#
# 🔄 Rolling back...
# ✓ Rolled back 003_add_phone_to_users
# ✓ Rolled back 002_add_email_to_users
# ✓ Schema version: 3 → 1
#
# ✓ Rollback to version 1 complete

# Dry-run rollback (preview without applying)
ai-shell migrate rollback --dry-run

# Rollback with automatic backup
ai-shell migrate rollback --backup-first
```

---

### Step 5: Zero-Downtime Migrations

Perform schema changes without application downtime.

```bash
# Add column with zero-downtime strategy
ai-shell migrate "add status field to orders" --zero-downtime

# AI-Shell creates multi-phase migration:
#
# 📋 Zero-Downtime Migration Plan
#
# Phase 1: Add column (nullable)
#   ALTER TABLE orders ADD COLUMN status VARCHAR(20);
#   - No locks, no downtime
#   - Existing queries unaffected
#
# Phase 2: Backfill data (batched)
#   UPDATE orders SET status = 'pending' WHERE status IS NULL;
#   - Processes 10,000 rows at a time
#   - Minimal lock time per batch
#
# Phase 3: Add constraint
#   ALTER TABLE orders ALTER COLUMN status SET NOT NULL;
#   ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'pending';
#   - Short lock, validates data
#
# Phase 4: Add index (concurrent)
#   CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);
#   - No locks, builds in background
#
# Total estimated time: ~5 minutes
# Application downtime: 0 seconds
#
# Apply? [y/N]: y
#
# 🔄 Executing zero-downtime migration...
#
# Phase 1/4: Adding nullable column... ✓ (45ms)
# Phase 2/4: Backfilling data...
#   Batch 1/125 (8%) ✓
#   Batch 25/125 (20%) ✓
#   Batch 50/125 (40%) ✓
#   Batch 75/125 (60%) ✓
#   Batch 100/125 (80%) ✓
#   Batch 125/125 (100%) ✓
# Phase 3/4: Adding constraint... ✓ (123ms)
# Phase 4/4: Creating index concurrently... ✓ (2,847ms)
#
# ✓ Zero-downtime migration complete
# Total time: 4 minutes 23 seconds
# Application downtime: 0 seconds

# Remove column with zero-downtime
ai-shell migrate "remove deprecated_field from products" --zero-downtime

# AI-Shell strategy:
# 1. Mark column as deprecated (no data removal yet)
# 2. Stop writing to column (application must be updated)
# 3. Wait for confirmation application no longer uses column
# 4. Remove column
```

---

### Step 6: Complex Schema Changes

Handle sophisticated migration scenarios.

#### Renaming Tables
```bash
ai-shell migrate "rename users table to accounts"

# AI-Shell handles:
# - Rename table
# - Update foreign keys
# - Update indexes
# - Update constraints
# - Update views/triggers
# - Generate compatibility view (optional)
#
# Generated:
# ALTER TABLE users RENAME TO accounts;
# ALTER INDEX idx_users_email RENAME TO idx_accounts_email;
# ALTER SEQUENCE users_id_seq RENAME TO accounts_id_seq;
#
# -- Compatibility view (temporary)
# CREATE VIEW users AS SELECT * FROM accounts;
# -- Remove after applications updated
```

#### Splitting Tables
```bash
ai-shell migrate "split users table into accounts and profiles"

# AI-Shell creates:
# 1. Create new tables (accounts, profiles)
# 2. Copy data with appropriate splits
# 3. Add foreign keys
# 4. Validate data integrity
# 5. Optional: keep original table for rollback
```

#### Merging Tables
```bash
ai-shell migrate "merge user_details into users table"

# AI-Shell strategy:
# 1. Add columns from user_details to users
# 2. Copy data with LEFT JOIN
# 3. Handle conflicts
# 4. Validate integrity
# 5. Drop user_details (after validation)
```

#### Changing Column Types
```bash
ai-shell migrate "change user_id from integer to bigint in all tables"

# AI-Shell handles:
# - Identify all tables with user_id
# - Check foreign key relationships
# - Create temporary columns
# - Copy and convert data
# - Swap columns atomically
# - Update foreign keys
# - Clean up temporary columns
#
# Zero-downtime strategy automatically applied
```

---

### Step 7: Migration Testing and Validation

Test migrations before applying to production.

```bash
# Test migration in dry-run mode
ai-shell migrate "add indexes to orders table" --test

# Output:
# 🧪 Testing Migration (Dry Run)
#
# Test Database: Created temporary test database
# Sample Data: Copied 10,000 sample rows
#
# Executing migration...
# ✓ Migration SQL validated
# ✓ Applied to test database
# ✓ Indexes created successfully
# ✓ Performance improved 12.3x
#
# Testing queries...
# ✓ SELECT queries work correctly
# ✓ INSERT queries work correctly
# ✓ UPDATE queries work correctly
# ✓ DELETE queries work correctly
#
# Testing rollback...
# ✓ Rollback successful
# ✓ Schema restored to original state
#
# Cleanup: Test database removed
#
# ✓ Migration test passed
# Safe to apply to production

# Validate migration SQL
ai-shell migrate validate 004_add_indexes

# Check migration impact
ai-shell migrate impact "add status column to orders"

# Output:
# 📊 Migration Impact Analysis
#
# Affected Tables:
#   - orders (1.2M rows)
#
# Estimated Duration:
#   - Column addition: ~100ms
#   - Index creation: ~3 seconds
#   - Total: ~3.1 seconds
#
# Lock Time:
#   - Zero-downtime strategy: 0 seconds
#   - Standard strategy: ~100ms
#
# Performance Impact:
#   - Query improvement: 15.2x (status filters)
#   - Storage increase: ~8MB
#   - Index maintenance overhead: minimal
#
# Risks:
#   ✓ Low risk (additive change only)
#
# Recommendation:
#   ✓ Safe to apply during business hours
#   Consider: Zero-downtime strategy for zero impact

# Simulate migration on copy of production data
ai-shell migrate simulate 004_add_indexes --use-prod-copy
```

---

### Step 8: Schema Versioning and Comparison

Track schema evolution and compare environments.

```bash
# Get current schema version
ai-shell schema version

# Output:
# Schema Version: 5
# Last Migration: 005_add_payment_methods
# Applied: 2025-10-28 15:30:00

# Export current schema
ai-shell schema export --output schema-v5.sql

# Compare schemas between environments
ai-shell schema diff production staging

# Output:
# 📊 Schema Differences
#
# Environment Comparison:
#   Production: version 5
#   Staging: version 7
#
# Staging is 2 versions ahead:
#
# ✓ 006_add_user_preferences (staging only)
#   + Added table: user_preferences
#   + Added foreign key: user_preferences.user_id → users.id
#
# ✓ 007_optimize_orders_indexes (staging only)
#   + Added index: idx_orders_status_created (composite)
#   - Removed index: idx_orders_status (redundant)
#
# To sync production with staging:
#   ai-shell migrate sync production --from staging

# Generate migration to sync environments
ai-shell schema diff production staging --generate-migration

# Compare with specific schema version
ai-shell schema diff current --to-version 3

# Compare with schema file
ai-shell schema diff current --to-file schema-backup.sql
```

---

### Step 9: Cross-Database Migrations

Manage schema changes across multiple databases in federation.

```bash
# Apply migration to all databases in federation
ai-shell migrate "add updated_at timestamp to all tables" \
  --all-databases

# Output:
# 🔄 Cross-Database Migration
#
# Databases:
#   - postgres-main (3 tables affected)
#   - mysql-legacy (5 tables affected)
#   - mongodb-products (not applicable - document DB)
#
# Execution Plan:
#   postgres-main: ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()
#   mysql-legacy: ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#   mongodb-products: Skip (handled differently for documents)
#
# Apply to all? [y/N]: y
#
# Results:
#   ✓ postgres-main: 3/3 tables updated
#   ✓ mysql-legacy: 5/5 tables updated
#   ⚠️ mongodb-products: Skipped (not applicable)
#
# ✓ Cross-database migration complete

# Database-specific migrations
ai-shell migrate "create full-text index on products" \
  --database postgres-main \
  --dialect postgresql

# Handle database dialect differences
ai-shell migrate "add uuid primary key" \
  --postgres "gen_random_uuid()" \
  --mysql "UUID()" \
  --auto-adapt
```

---

### Step 10: Migration Best Practices and Safety

Configure safety checks and best practices.

```bash
# Enable migration safety checks
ai-shell config set migrations.safety.enabled true
ai-shell config set migrations.safety.requireBackup true
ai-shell config set migrations.safety.requireReview true

# Configure automatic backup before migrations
ai-shell config set migrations.backup.auto true
ai-shell config set migrations.backup.retention 7d

# Set up migration approval workflow
ai-shell migrate "drop unused_table" --require-approval

# Output:
# ⚠️  DESTRUCTIVE MIGRATION DETECTED
#
# This migration will:
#   - DROP TABLE unused_table (1,247 rows)
#   - Data will be PERMANENTLY deleted
#
# Safety checks:
#   ✓ Backup created: pre-migration-20251028-153000.backup
#   ⚠️ Approval required
#
# To approve:
#   1. Review migration: ai-shell migrate review pending
#   2. Approve: ai-shell migrate approve <migration-id>
#   3. Apply: ai-shell migrate apply <migration-id>

# Review pending migrations
ai-shell migrate pending

# Approve migration
ai-shell migrate approve 006_drop_unused_table --reason "Confirmed unused"

# Set up migration notifications
ai-shell config set migrations.notify.enabled true
ai-shell config set migrations.notify.slack $SLACK_WEBHOOK
ai-shell config set migrations.notify.events "applied,failed,rolled_back"
```

---

## Common Use Cases

### Use Case 1: Adding New Feature Schema

**Scenario:** Add database schema for new feature.

```bash
# Describe the feature schema in natural language
ai-shell migrate "
  create user_preferences table with:
  - user_id foreign key to users
  - theme (light/dark)
  - language
  - notifications_enabled
  - email_frequency
"

# AI-Shell generates:
# CREATE TABLE user_preferences (
#   id SERIAL PRIMARY KEY,
#   user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
#   theme VARCHAR(10) DEFAULT 'light' CHECK (theme IN ('light', 'dark')),
#   language VARCHAR(5) DEFAULT 'en',
#   notifications_enabled BOOLEAN DEFAULT true,
#   email_frequency VARCHAR(20) DEFAULT 'daily'
#     CHECK (email_frequency IN ('realtime', 'daily', 'weekly', 'never')),
#   created_at TIMESTAMP DEFAULT NOW(),
#   updated_at TIMESTAMP DEFAULT NOW()
# );
#
# CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
# CREATE UNIQUE INDEX idx_user_preferences_user_id_unique
#   ON user_preferences(user_id);

# Apply with zero-downtime
ai-shell migrate apply --zero-downtime

# Verify schema
ai-shell query "describe user_preferences"
```

---

### Use Case 2: Database Normalization

**Scenario:** Normalize denormalized schema for better data integrity.

```bash
# Current: users table has address fields
# Target: separate addresses table

ai-shell migrate "
  extract address fields from users into separate addresses table:
  - create addresses table
  - move street, city, state, zip from users
  - add foreign key from users to addresses
  - handle users with no address (nullable)
"

# AI-Shell creates multi-step migration:
# Step 1: Create addresses table
# Step 2: Copy address data from users
# Step 3: Add address_id to users
# Step 4: Update foreign keys
# Step 5: Drop address columns from users
# Step 6: Clean up

# Preview migration plan
ai-shell migrate preview --show-steps

# Apply with rollback points
ai-shell migrate apply --checkpoint-each-step
```

---

### Use Case 3: Production Schema Update

**Scenario:** Safely update production database schema.

```bash
# Workflow for production migrations

# 1. Test on staging
ai-shell connect staging
ai-shell migrate "add payment_status to orders" --test
ai-shell migrate apply

# 2. Verify on staging
ai-shell schema verify
ai-shell query "select * from orders limit 5"

# 3. Prepare for production
ai-shell connect production

# 4. Create backup
ai-shell backup create --name "pre-migration-payment-status"

# 5. Apply with zero-downtime
ai-shell migrate "add payment_status to orders" \
  --zero-downtime \
  --monitor-performance \
  --auto-rollback-on-error

# 6. Verify production
ai-shell schema verify
ai-shell monitor queries --watch payment_status

# 7. Monitor for issues
ai-shell alerts add migration-issues \
  --condition "error_rate > 1%" \
  --action rollback
```

---

### Use Case 4: Legacy Database Modernization

**Scenario:** Modernize old database schema to current standards.

```bash
# Analyze current schema
ai-shell schema analyze --legacy-patterns

# Output:
# 🔍 Legacy Schema Analysis
#
# Issues Found:
#   ⚠️ No created_at/updated_at timestamps (12 tables)
#   ⚠️ Missing indexes on foreign keys (8 tables)
#   ⚠️ No cascading deletes configured (6 relationships)
#   ⚠️ Using TEXT instead of VARCHAR with limits (23 columns)
#   ⚠️ No check constraints for enums (15 columns)
#   ⚠️ Missing default values (34 columns)
#
# Recommendations:
#   1. Add timestamps to all tables
#   2. Add foreign key indexes
#   3. Configure cascade rules
#   4. Migrate TEXT to VARCHAR with appropriate limits
#   5. Add check constraints for enum-like columns
#   6. Set sensible defaults

# Generate modernization migration
ai-shell migrate modernize --auto-generate

# Review and apply in stages
ai-shell migrate apply 010_add_timestamps
ai-shell migrate apply 011_add_foreign_key_indexes
ai-shell migrate apply 012_configure_cascades
# etc.
```

---

### Use Case 5: Multi-Environment Schema Sync

**Scenario:** Keep dev, staging, and production schemas in sync.

```bash
# Set up environment connections
ai-shell connections add-group environments \
  dev postgres://localhost:5432/mydb_dev \
  staging postgres://staging.db:5432/mydb_staging \
  production postgres://prod.db:5432/mydb_prod

# Check schema versions across environments
ai-shell schema versions --all-environments

# Output:
# 📊 Schema Versions
#
# Development: version 12
#   Last migration: 012_add_analytics_tables
#   Status: 3 versions ahead of production
#
# Staging: version 10
#   Last migration: 010_optimize_queries
#   Status: 1 version ahead of production
#
# Production: version 9
#   Last migration: 009_add_user_roles
#   Status: Behind by 1 (staging) and 3 (dev)

# Generate migration plan to sync production with staging
ai-shell migrate sync-plan production --from staging

# Apply staged migrations to production
ai-shell migrate sync production --from staging --verify-each-step

# Set up automatic staging → production sync
ai-shell migrate auto-sync \
  --from staging \
  --to production \
  --schedule "0 2 * * 0"  # Sunday 2 AM
  --require-approval \
  --notify-slack
```

---

## Troubleshooting Tips

### Issue 1: Migration Fails Midway

**Problem:** Migration fails partway through execution.

**Solutions:**
```bash
# Check migration status
ai-shell migrate status

# Output shows:
# Migration 005_add_indexes
# Status: Failed (step 3/5)
# Error: Deadlock detected

# View detailed error
ai-shell migrate logs 005_add_indexes

# Rollback failed migration
ai-shell migrate rollback 005_add_indexes

# Fix and retry
ai-shell migrate retry 005_add_indexes --fix-deadlock

# Or start fresh
ai-shell migrate revert 005_add_indexes
ai-shell migrate apply 005_add_indexes --with-retry
```

---

### Issue 2: Schema Drift

**Problem:** Manual changes made to database outside migration system.

**Solutions:**
```bash
# Detect schema drift
ai-shell schema detect-drift

# Output:
# ⚠️  Schema Drift Detected
#
# Unexpected changes:
#   + Column: users.middle_name (not in migrations)
#   + Index: idx_orders_custom (not in migrations)
#   - Column: products.old_price (expected but missing)
#
# This indicates manual changes were made outside migration system

# Generate migration to capture drift
ai-shell schema capture-drift --generate-migration

# Or reset to match migrations
ai-shell schema reset-to-migrations --force
```

---

### Issue 3: Cannot Rollback Migration

**Problem:** Rollback fails or is not available.

**Solutions:**
```bash
# Check why rollback is unavailable
ai-shell migrate rollback-status 005_add_indexes

# Output:
# Rollback Status: Not Available
# Reason: Irreversible data transformation
# Details: Column dropped with CASCADE

# Options:
# 1. Restore from backup
ai-shell backup restore pre-migration-backup.backup

# 2. Manually revert
ai-shell migrate generate-manual-revert 005_add_indexes

# 3. Forward fix
ai-shell migrate "recreate dropped column with recovery"
```

---

### Issue 4: Long-Running Migration Locks Database

**Problem:** Migration taking too long, blocking other queries.

**Solutions:**
```bash
# Cancel running migration
ai-shell migrate cancel <migration-id>

# Use zero-downtime strategy instead
ai-shell migrate apply <migration-id> --zero-downtime

# Or batch large operations
ai-shell migrate apply <migration-id> --batch-size 1000

# Set timeout for migrations
ai-shell config set migrations.timeout 300  # 5 minutes

# Monitor migration progress
ai-shell migrate monitor <migration-id>
```

---

### Issue 5: Cross-Database Migration Inconsistency

**Problem:** Migration succeeds on some databases but fails on others.

**Solutions:**
```bash
# Check status across all databases
ai-shell migrate status --all-databases

# Retry failed databases only
ai-shell migrate retry --failed-only

# Rollback all to maintain consistency
ai-shell migrate rollback --all-databases --coordinated

# Use two-phase commit for critical migrations
ai-shell migrate apply --two-phase-commit
```

---

## Best Practices

### 1. Always Use Migrations for Schema Changes

```bash
# Never modify schema manually in production
# Always generate and track migrations

# Good:
ai-shell migrate "add column email to users"

# Bad:
# Directly running: ALTER TABLE users ADD COLUMN email...
```

### 2. Test Migrations Before Production

```bash
# Always test in non-production first
ai-shell migrate apply --environment staging
ai-shell migrate test --with-sample-data
ai-shell migrate verify
```

### 3. Make Migrations Reversible

```bash
# Always provide rollback path
# AI-Shell does this automatically, but verify:
ai-shell migrate review --check-reversibility

# For irreversible operations, document recovery procedure
ai-shell migrate note "recovery requires backup restore"
```

### 4. Keep Migrations Small and Focused

```bash
# Good: One logical change per migration
ai-shell migrate "add email to users"
ai-shell migrate "add index on email"

# Bad: Multiple unrelated changes in one migration
ai-shell migrate "add email, rename table, drop old columns, add indexes"
```

### 5. Use Zero-Downtime for Production

```bash
# Always use zero-downtime strategies in production
ai-shell config set migrations.production.zero-downtime true

# Or explicitly for each migration:
ai-shell migrate apply --zero-downtime
```

### 6. Version Control Your Migrations

```bash
# Keep migration files in version control
git add migrations/
git commit -m "Add migration: add user preferences"

# AI-Shell can integrate with git
ai-shell config set migrations.vcs.enabled true
ai-shell config set migrations.vcs.auto-commit true
```

### 7. Document Complex Migrations

```bash
# Add detailed notes to complex migrations
ai-shell migrate note 015_complex_refactor "
This migration refactors the order processing schema.
Breaking changes: old_orders table structure changed
Requires: application version 2.5+ before applying
Rollback plan: restore from backup if deployed app is < 2.5
"
```

---

## Next Steps

### Master Related Features

1. **Backup & Recovery**
   - Always backup before migrations
   - [Tutorial: Backup & Recovery](./backup-recovery.md)

2. **Schema Design**
   - Design schemas for maintainability
   - [Guide: Database Design Best Practices](../best-practices.md#schema-design)

3. **Performance**
   - Optimize schema for performance
   - [Tutorial: Query Optimization](./query-optimization.md)

### Practice Exercises

1. **Exercise 1: Basic Migration**
   - Add a new column to existing table
   - Apply migration
   - Verify change
   - Rollback

2. **Exercise 2: Complex Schema Change**
   - Rename a table
   - Update foreign keys
   - Create compatibility view
   - Test application still works

3. **Exercise 3: Zero-Downtime Migration**
   - Add NOT NULL column to large table
   - Use zero-downtime strategy
   - Monitor during execution

4. **Exercise 4: Schema Versioning**
   - Create multiple migrations
   - Compare schemas between versions
   - Generate diff migration

5. **Exercise 5: Production Workflow**
   - Test migration on staging
   - Create production backup
   - Apply with zero-downtime
   - Verify and monitor

### Additional Resources

- **Documentation**: [Migration guide](https://docs.ai-shell.dev/migrations)
- **Best Practices**: [Schema management](../best-practices.md#migrations)
- **API Reference**: [Migration API](../api/migrations.md)
- **Examples**: [Migration examples](../examples/migrations)

---

## Summary

You've learned how to:
- Create schema changes using natural language
- Generate and apply database migrations safely
- Perform zero-downtime schema changes
- Rollback migrations when needed
- Track and version database schemas
- Handle complex migration scenarios
- Apply migrations across multiple databases

Schema management with AI-Shell transforms what was once a risky, manual process into a safe, automated workflow with built-in safety checks and rollback capabilities.

**Key Takeaway:** Treat schema changes with the same care as code changes - version controlled, tested, reviewed, and deployed systematically. Always test migrations in non-production environments first and always have a rollback plan.

---

**Related Tutorials:**
- [Backup & Recovery](./backup-recovery.md)
- [Query Optimization](./query-optimization.md)
- [Database Federation](./database-federation.md)

**Need Help?** [Visit our documentation](https://docs.ai-shell.dev) or [join the community](https://github.com/your-org/ai-shell/discussions)
