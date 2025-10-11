# AI-Shell Hands-On Tutorial - Part 5: Backup, Restore & Migration

**Level:** Advanced
**Duration:** 60 minutes
**Prerequisites:** Complete Parts 1-4

## Overview

This tutorial covers critical data operations: backing up databases, restoring from backups, and managing migrations. You'll learn production-ready strategies for data protection, disaster recovery, and schema evolution.

## Learning Objectives

By the end of this tutorial, you will:
- Create encrypted and compressed backups
- Schedule automated backup jobs
- Perform point-in-time restoration
- Create and execute database migrations
- Implement rollback procedures
- Handle cross-database migrations

---

## Part 1: Database Backups (20 minutes)

### 1.1 Basic Backup Operations

```bash
# Start AI-Shell
aishell

# List available databases
aishell> db list

# Create a simple backup
aishell> backup create postgres_main --output /backups/postgres_main_backup.sql

# Create backup with timestamp
aishell> backup create postgres_main --output /backups/postgres_$(date +%Y%m%d_%H%M%S).sql
```

**Expected Output:**
```
✓ Creating backup of postgres_main
✓ Backup completed: /backups/postgres_20251011_103000.sql
Size: 2.4 MB
Duration: 3.2s
```

### 1.2 Compressed Backups

Compressed backups save disk space and transfer time:

```bash
# PostgreSQL compressed backup
aishell> backup create postgres_main \
  --output /backups/postgres_main.sql.gz \
  --compress gzip \
  --compression-level 9

# MongoDB compressed backup
aishell> backup create mongodb_main \
  --output /backups/mongodb_main.archive.gz \
  --compress gzip

# Custom format (PostgreSQL) - best compression and features
aishell> backup create postgres_main \
  --output /backups/postgres_main.dump \
  --format custom \
  --compress 9

# Directory format (parallel backup for large databases)
aishell> backup create postgres_main \
  --output /backups/postgres_main_dir \
  --format directory \
  --jobs 4  # Use 4 parallel jobs
```

**Compression Comparison:**
```
Plain SQL:       2.4 MB
Gzip Level 6:    380 KB (default)
Gzip Level 9:    320 KB (best compression, slower)
Custom Format:   280 KB (best for PostgreSQL)
```

### 1.3 Encrypted Backups

Protect sensitive data with encryption:

```bash
# Create encrypted backup (AES-256)
aishell> backup create postgres_main \
  --output /backups/postgres_main.sql.enc \
  --encrypt \
  --encryption-key "your-secure-key-here" \
  --compress gzip

# Alternative: Use environment variable for key
export AISHELL_BACKUP_KEY="your-secure-key-here"
aishell> backup create postgres_main \
  --output /backups/postgres_main.sql.enc \
  --encrypt \
  --compress gzip

# Verify encrypted backup
aishell> backup info /backups/postgres_main.sql.enc
```

**Expected Output:**
```
Backup Information:
  File: /backups/postgres_main.sql.enc
  Encrypted: Yes (AES-256)
  Compressed: Yes (gzip)
  Size: 325 KB
  Created: 2025-10-11 10:30:00
  Database: postgres_main
  Type: PostgreSQL 15.3
```

### 1.4 Selective Backups

Backup specific tables or collections:

#### PostgreSQL Selective Backup

```bash
# Backup specific tables
aishell> backup create postgres_main \
  --output /backups/users_orders_backup.sql \
  --tables users,orders,order_items

# Backup specific schema
aishell> backup create postgres_main \
  --output /backups/public_schema_backup.sql \
  --schema public

# Exclude specific tables
aishell> backup create postgres_main \
  --output /backups/postgres_no_logs.sql \
  --exclude-tables logs,temp_data,cache

# Data-only backup (no schema)
aishell> backup create postgres_main \
  --output /backups/postgres_data_only.sql \
  --data-only

# Schema-only backup (no data)
aishell> backup create postgres_main \
  --output /backups/postgres_schema_only.sql \
  --schema-only
```

#### MongoDB Selective Backup

```bash
# Backup specific collections
aishell> backup create mongodb_main \
  --output /backups/products_backup.archive \
  --collections products,categories

# Backup with query filter
aishell> backup create mongodb_main \
  --output /backups/recent_orders.archive \
  --collection orders \
  --query '{"created_at": {"$gte": ISODate("2025-10-01")}}'

# Exclude specific collections
aishell> backup create mongodb_main \
  --output /backups/mongodb_no_logs.archive \
  --exclude-collections logs,sessions,cache
```

### 1.5 Incremental Backups

Save time and space with incremental backups:

```bash
# Create base backup
aishell> backup create postgres_main \
  --output /backups/base_backup \
  --format directory \
  --base-backup

# Create incremental backup (only changes since base)
aishell> backup create postgres_main \
  --output /backups/incremental_001 \
  --format directory \
  --incremental \
  --base-backup /backups/base_backup

# Create another incremental
aishell> backup create postgres_main \
  --output /backups/incremental_002 \
  --format directory \
  --incremental \
  --base-backup /backups/base_backup

# List backup chain
aishell> backup list /backups --show-chain
```

**Expected Output:**
```
Backup Chain:
  Base: /backups/base_backup (2.4 MB) - 2025-10-11 10:00:00
  ├─ Incremental: /backups/incremental_001 (120 KB) - 2025-10-11 11:00:00
  └─ Incremental: /backups/incremental_002 (85 KB) - 2025-10-11 12:00:00

Total Size: 2.6 MB (saved 4.2 MB with incremental backups)
```

---

## Part 2: Scheduled Backups (10 minutes)

### 2.1 Create Backup Schedule

```bash
# Schedule daily backup at 2 AM
aishell> backup schedule create \
  --name daily_postgres_backup \
  --database postgres_main \
  --cron "0 2 * * *" \
  --output /backups/daily/postgres_$(date +%Y%m%d).sql.gz \
  --compress gzip \
  --encrypt \
  --retention-days 30

# Schedule hourly incremental backup
aishell> backup schedule create \
  --name hourly_incremental \
  --database postgres_main \
  --cron "0 * * * *" \
  --output /backups/hourly/postgres_$(date +%Y%m%d_%H%M).sql.gz \
  --incremental \
  --base-backup /backups/base_backup \
  --retention-days 7

# Schedule weekly full backup (Sunday 3 AM)
aishell> backup schedule create \
  --name weekly_full_backup \
  --database postgres_main \
  --cron "0 3 * * 0" \
  --output /backups/weekly/postgres_week_$(date +%U).dump \
  --format custom \
  --compress 9 \
  --encrypt \
  --retention-weeks 12

# Schedule MongoDB backup (every 6 hours)
aishell> backup schedule create \
  --name mongodb_6h_backup \
  --database mongodb_main \
  --cron "0 */6 * * *" \
  --output /backups/mongodb/mongodb_$(date +%Y%m%d_%H%M).archive.gz \
  --compress gzip \
  --encrypt \
  --retention-days 14
```

### 2.2 Manage Backup Schedules

```bash
# List all schedules
aishell> backup schedule list

# Expected output:
# ID  Name                  Database        Cron         Next Run           Status
# 1   daily_postgres_backup postgres_main   0 2 * * *    2025-10-12 02:00   Active
# 2   hourly_incremental    postgres_main   0 * * * *    2025-10-11 11:00   Active
# 3   weekly_full_backup    postgres_main   0 3 * * 0    2025-10-13 03:00   Active
# 4   mongodb_6h_backup     mongodb_main    0 */6 * * *  2025-10-11 12:00   Active

# View schedule details
aishell> backup schedule show daily_postgres_backup

# Pause a schedule
aishell> backup schedule pause daily_postgres_backup

# Resume a schedule
aishell> backup schedule resume daily_postgres_backup

# Delete a schedule
aishell> backup schedule delete hourly_incremental

# Run a scheduled backup immediately
aishell> backup schedule run daily_postgres_backup
```

### 2.3 Backup Rotation and Retention

```bash
# Configure retention policy
aishell> backup retention set \
  --policy tiered \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 12 \
  --keep-yearly 3

# Clean old backups manually
aishell> backup cleanup /backups/daily --older-than 30d

# View backup storage usage
aishell> backup storage-stats /backups
```

**Expected Output:**
```
Backup Storage Statistics:
  Total Backups: 47
  Total Size: 15.2 GB

  By Age:
    Last 24 hours: 4 backups (820 MB)
    Last 7 days: 28 backups (5.6 GB)
    Last 30 days: 47 backups (15.2 GB)

  By Type:
    Full Backups: 12 (12.4 GB)
    Incremental: 35 (2.8 GB)

  Retention Policy: Tiered
    Will keep: 24 backups (8.5 GB)
    Can delete: 23 backups (6.7 GB)
```

---

## Part 3: Restore Operations (15 minutes)

### 3.1 Basic Restore

```bash
# Restore entire database
aishell> restore /backups/postgres_main.sql.gz \
  --database postgres_main \
  --confirm

# Restore to a different database (for testing)
aishell> restore /backups/postgres_main.sql.gz \
  --database postgres_test \
  --create-database \
  --confirm

# Restore encrypted backup
aishell> restore /backups/postgres_main.sql.enc \
  --database postgres_main \
  --encryption-key "your-secure-key-here" \
  --confirm
```

**Warning Output:**
```
⚠️  WARNING: This will overwrite database 'postgres_main'
Current database size: 2.8 GB
Backup date: 2025-10-11 10:30:00
Backup size: 2.4 GB

Type 'RESTORE postgres_main' to confirm: RESTORE postgres_main

✓ Restoring database...
✓ Restore completed successfully
Duration: 45.3s
Rows restored: 1,245,892
```

### 3.2 Selective Restore

```bash
# Restore specific tables only
aishell> restore /backups/postgres_main.sql.gz \
  --database postgres_main \
  --tables users,orders \
  --confirm

# Restore with table mapping (rename during restore)
aishell> restore /backups/postgres_main.sql.gz \
  --database postgres_main \
  --table-mapping users=users_backup,orders=orders_backup \
  --confirm

# Restore data only (keep existing schema)
aishell> restore /backups/postgres_main.sql.gz \
  --database postgres_main \
  --data-only \
  --confirm

# Restore schema only (no data)
aishell> restore /backups/postgres_schema_only.sql \
  --database postgres_new \
  --schema-only \
  --create-database \
  --confirm
```

### 3.3 Point-in-Time Recovery (PITR)

For PostgreSQL with WAL archiving enabled:

```bash
# Restore to specific timestamp
aishell> restore /backups/base_backup \
  --database postgres_main \
  --point-in-time "2025-10-11 10:25:00" \
  --wal-archive /backups/wal_archive \
  --confirm

# Restore to specific transaction ID
aishell> restore /backups/base_backup \
  --database postgres_main \
  --target-xid 12345678 \
  --wal-archive /backups/wal_archive \
  --confirm

# Restore incremental backup chain
aishell> restore /backups/base_backup \
  --database postgres_main \
  --incremental /backups/incremental_001 \
  --incremental /backups/incremental_002 \
  --confirm
```

### 3.4 MongoDB Restore

```bash
# Restore entire MongoDB database
aishell> restore /backups/mongodb_main.archive.gz \
  --database mongodb_main \
  --confirm

# Restore specific collections
aishell> restore /backups/mongodb_main.archive.gz \
  --database mongodb_main \
  --collections products,categories \
  --confirm

# Restore with collection renaming
aishell> restore /backups/mongodb_main.archive.gz \
  --database mongodb_main \
  --collection-mapping products=products_backup \
  --confirm

# Restore to different database
aishell> restore /backups/mongodb_main.archive.gz \
  --database mongodb_test \
  --create-database \
  --confirm
```

### 3.5 Verify Restore

```bash
# Verify backup before restore
aishell> restore /backups/postgres_main.sql.gz \
  --verify-only

# Expected output:
# ✓ Backup file is valid
# ✓ Compression: gzip
# ✓ Encryption: None
# ✓ Database type: PostgreSQL 15.3
# ✓ Estimated restore size: 2.8 GB
# ✓ Estimated restore time: 45s
# ✓ No errors found

# Test restore (dry run)
aishell> restore /backups/postgres_main.sql.gz \
  --database postgres_main \
  --dry-run

# Restore with verification
aishell> restore /backups/postgres_main.sql.gz \
  --database postgres_main \
  --verify-after-restore \
  --confirm
```

---

## Part 4: Database Migrations (20 minutes)

### 4.1 Create Migration Files

```bash
# Initialize migrations directory
aishell> migrate init

# Create a new migration
aishell> migrate create add_user_preferences_table

# Expected output:
# ✓ Created migration: 20251011103000_add_user_preferences_table.sql
# ✓ Edit: migrations/20251011103000_add_user_preferences_table.sql
```

Edit the migration file:

```sql
-- migrations/20251011103000_add_user_preferences_table.sql

-- Up Migration
-- +migrate Up
CREATE TABLE user_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'en',
    notifications_enabled BOOLEAN DEFAULT true,
    email_frequency VARCHAR(20) DEFAULT 'daily',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- Insert default preferences for existing users
INSERT INTO user_preferences (user_id)
SELECT user_id FROM users
WHERE NOT EXISTS (
    SELECT 1 FROM user_preferences WHERE user_preferences.user_id = users.user_id
);

-- Down Migration
-- +migrate Down
DROP TABLE IF EXISTS user_preferences CASCADE;
```

### 4.2 More Migration Examples

```bash
# Create migration for adding column
aishell> migrate create add_email_verified_to_users
```

```sql
-- migrations/20251011103100_add_email_verified_to_users.sql

-- +migrate Up
ALTER TABLE users
ADD COLUMN email_verified BOOLEAN DEFAULT false,
ADD COLUMN email_verification_token VARCHAR(255),
ADD COLUMN email_verification_sent_at TIMESTAMP;

CREATE INDEX idx_users_email_verification_token
ON users(email_verification_token)
WHERE email_verification_token IS NOT NULL;

-- +migrate Down
ALTER TABLE users
DROP COLUMN IF EXISTS email_verified,
DROP COLUMN IF EXISTS email_verification_token,
DROP COLUMN IF EXISTS email_verification_sent_at;

DROP INDEX IF EXISTS idx_users_email_verification_token;
```

```bash
# Create migration for data transformation
aishell> migrate create normalize_user_emails
```

```sql
-- migrations/20251011103200_normalize_user_emails.sql

-- +migrate Up
-- Normalize all email addresses to lowercase
UPDATE users
SET email = LOWER(email),
    updated_at = CURRENT_TIMESTAMP
WHERE email != LOWER(email);

-- Add constraint to ensure lowercase emails
ALTER TABLE users
ADD CONSTRAINT check_email_lowercase
CHECK (email = LOWER(email));

-- +migrate Down
ALTER TABLE users
DROP CONSTRAINT IF EXISTS check_email_lowercase;
```

### 4.3 Run Migrations

```bash
# Check migration status
aishell> migrate status postgres_main

# Expected output:
# Migration Status for postgres_main:
# ID        Migration                              Status     Applied At
# 20251011103000  add_user_preferences_table    Pending    -
# 20251011103100  add_email_verified_to_users   Pending    -
# 20251011103200  normalize_user_emails         Pending    -

# Run all pending migrations
aishell> migrate up postgres_main

# Expected output:
# ✓ Running migration: 20251011103000_add_user_preferences_table
# ✓ Running migration: 20251011103100_add_email_verified_to_users
# ✓ Running migration: 20251011103200_normalize_user_emails
# ✓ All migrations completed successfully

# Run migrations one at a time
aishell> migrate up postgres_main --steps 1

# Run specific migration
aishell> migrate up postgres_main --to 20251011103100
```

### 4.4 Rollback Migrations

```bash
# Rollback last migration
aishell> migrate down postgres_main

# Rollback multiple migrations
aishell> migrate down postgres_main --steps 2

# Rollback to specific version
aishell> migrate down postgres_main --to 20251011103000

# Rollback all migrations
aishell> migrate down postgres_main --all

# Check status after rollback
aishell> migrate status postgres_main
```

### 4.5 MongoDB Migrations

```bash
# Create MongoDB migration
aishell> migrate create add_indexes_to_products --database mongodb_main
```

```javascript
// migrations/20251011103300_add_indexes_to_products.js

// Up Migration
exports.up = function(db) {
  return Promise.all([
    // Create text index for search
    db.collection('products').createIndex(
      { name: 'text', description: 'text' },
      { weights: { name: 10, description: 5 } }
    ),

    // Create compound index for filtering
    db.collection('products').createIndex(
      { category: 1, price: -1 }
    ),

    // Create index for tags
    db.collection('products').createIndex(
      { tags: 1 }
    ),

    // Add field to existing documents
    db.collection('products').updateMany(
      { featured: { $exists: false } },
      { $set: { featured: false, featured_at: null } }
    )
  ]);
};

// Down Migration
exports.down = function(db) {
  return Promise.all([
    db.collection('products').dropIndex('name_text_description_text'),
    db.collection('products').dropIndex('category_1_price_-1'),
    db.collection('products').dropIndex('tags_1'),
    db.collection('products').updateMany(
      {},
      { $unset: { featured: '', featured_at: '' } }
    )
  ]);
};
```

```bash
# Run MongoDB migrations
aishell> migrate up mongodb_main

# Rollback MongoDB migrations
aishell> migrate down mongodb_main
```

### 4.6 Migration Best Practices

```sql
-- migrations/20251011103400_safe_column_modification.sql

-- +migrate Up
-- Safe approach: Add new column, migrate data, drop old column

-- Step 1: Add new column
ALTER TABLE products ADD COLUMN price_cents INTEGER;

-- Step 2: Migrate data
UPDATE products SET price_cents = ROUND(price * 100);

-- Step 3: Make new column NOT NULL after data migration
ALTER TABLE products ALTER COLUMN price_cents SET NOT NULL;

-- Step 4: Add constraint
ALTER TABLE products ADD CONSTRAINT check_price_cents_positive
CHECK (price_cents > 0);

-- Step 5: Create index if needed
CREATE INDEX idx_products_price_cents ON products(price_cents);

-- Note: Keep old column for now, drop in future migration after verification

-- +migrate Down
DROP INDEX IF EXISTS idx_products_price_cents;
ALTER TABLE products DROP CONSTRAINT IF EXISTS check_price_cents_positive;
ALTER TABLE products DROP COLUMN IF EXISTS price_cents;
```

---

## Part 5: Cross-Database Migrations (10 minutes)

### 5.1 Migrate Data Between Database Types

```bash
# Example: Migrate user sessions from PostgreSQL to Redis

# Create migration script
aishell> migrate create migrate_sessions_to_redis --type custom
```

```sql
-- migrations/20251011103500_migrate_sessions_to_redis.sql

-- +migrate Up
-- This is a custom migration that requires code execution
-- Run via: aishell> migrate up --custom postgres_main

-- Export sessions from PostgreSQL
\copy (SELECT session_id, user_id, data, expires_at FROM sessions WHERE expires_at > CURRENT_TIMESTAMP) TO '/tmp/sessions_export.csv' WITH CSV HEADER;

-- +migrate Down
-- No automated rollback for this migration
-- Manual intervention required
```

```bash
# Create Node.js script for complex migration
# migrations/migrate_sessions_to_redis.js

const { Pool } = require('pg');
const Redis = require('redis');

async function migrateSessionsToRedis() {
  const pgPool = new Pool({
    connectionString: 'postgresql://localhost/postgres_main'
  });

  const redisClient = Redis.createClient({
    url: 'redis://localhost:6379'
  });

  await redisClient.connect();

  try {
    // Get all active sessions from PostgreSQL
    const result = await pgPool.query(`
      SELECT session_id, user_id, data,
             EXTRACT(EPOCH FROM (expires_at - CURRENT_TIMESTAMP)) as ttl_seconds
      FROM sessions
      WHERE expires_at > CURRENT_TIMESTAMP
    `);

    console.log(`Migrating ${result.rows.length} sessions...`);

    // Migrate each session to Redis
    for (const session of result.rows) {
      const key = `session:${session.session_id}`;
      const value = JSON.stringify({
        user_id: session.user_id,
        data: session.data
      });
      const ttl = Math.floor(session.ttl_seconds);

      await redisClient.setEx(key, ttl, value);
    }

    console.log('✓ Migration completed successfully');

  } finally {
    await pgPool.end();
    await redisClient.quit();
  }
}

migrateSessionsToRedis().catch(console.error);
```

### 5.2 Migrate from PostgreSQL to MongoDB

```bash
# Create migration for moving product catalog
aishell> migrate create migrate_products_to_mongodb --type custom
```

```javascript
// migrations/migrate_products_to_mongodb.js

const { Pool } = require('pg');
const { MongoClient } = require('mongodb');

async function migrateProductsToMongoDB() {
  const pgPool = new Pool({
    connectionString: 'postgresql://localhost/postgres_main'
  });

  const mongoClient = new MongoClient('mongodb://localhost:27017');
  await mongoClient.connect();
  const db = mongoClient.db('mongodb_main');

  try {
    // Get all products with their categories and tags
    const result = await pgPool.query(`
      SELECT
        p.product_id,
        p.name,
        p.description,
        p.price,
        p.stock,
        c.category_name,
        p.created_at,
        p.updated_at,
        array_agg(DISTINCT t.tag_name) as tags
      FROM products p
      LEFT JOIN categories c ON p.category_id = c.category_id
      LEFT JOIN product_tags pt ON p.product_id = pt.product_id
      LEFT JOIN tags t ON pt.tag_id = t.tag_id
      GROUP BY p.product_id, c.category_name
    `);

    console.log(`Migrating ${result.rows.length} products...`);

    // Transform relational data to document format
    const mongoProducts = result.rows.map(row => ({
      _id: row.product_id,
      name: row.name,
      description: row.description,
      price: parseFloat(row.price),
      stock: row.stock,
      category: row.category_name,
      tags: row.tags.filter(tag => tag !== null),
      created_at: row.created_at,
      updated_at: row.updated_at
    }));

    // Insert into MongoDB
    await db.collection('products').insertMany(mongoProducts);

    // Create indexes
    await db.collection('products').createIndex({ name: 'text' });
    await db.collection('products').createIndex({ category: 1, price: -1 });
    await db.collection('products').createIndex({ tags: 1 });

    console.log('✓ Migration completed successfully');

  } finally {
    await pgPool.end();
    await mongoClient.close();
  }
}

migrateProductsToMongoDB().catch(console.error);
```

```bash
# Run custom migration
aishell> migrate run migrations/migrate_products_to_mongodb.js

# Verify migration
aishell> mongo mongodb_main
db.products.countDocuments()
db.products.findOne()
```

---

## Part 6: Disaster Recovery Procedures (5 minutes)

### 6.1 Complete Disaster Recovery Plan

```bash
# 1. Verify backup integrity
aishell> backup verify /backups/latest/postgres_main.dump

# 2. Prepare new server (if necessary)
aishell> db add postgresql://newserver/postgres_main --name postgres_recovery

# 3. Restore database
aishell> restore /backups/latest/postgres_main.dump \
  --database postgres_recovery \
  --verify-after-restore \
  --confirm

# 4. Restore WAL files for PITR
aishell> restore /backups/latest/postgres_main.dump \
  --database postgres_recovery \
  --point-in-time "2025-10-11 09:55:00" \
  --wal-archive /backups/wal_archive \
  --confirm

# 5. Verify data integrity
aishell> db use postgres_recovery
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM orders;
SELECT COUNT(*) FROM products;

# 6. Run consistency checks
SELECT * FROM users WHERE email IS NULL;
SELECT * FROM orders WHERE user_id NOT IN (SELECT user_id FROM users);

# 7. Update application configuration to use recovery database
# Update connection strings in application

# 8. Test application functionality
# Perform smoke tests

# 9. Monitor for issues
aishell> db stats postgres_recovery
```

### 6.2 Emergency Rollback Procedure

```bash
# If new deployment fails, rollback quickly

# 1. Stop application
# systemctl stop myapp

# 2. Restore from backup before deployment
aishell> restore /backups/pre_deployment_backup.dump \
  --database postgres_main \
  --confirm

# 3. Rollback migrations
aishell> migrate down postgres_main --steps 3

# 4. Verify rollback
aishell> migrate status postgres_main
aishell> db use postgres_main
SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1;

# 5. Restart application with previous version
# systemctl start myapp

# 6. Verify application is working
# curl http://localhost:3000/health
```

---

## Practice Exercises

### Exercise 1: Complete Backup Strategy

**Objective:** Implement a production backup strategy

```bash
# 1. Create base backup
aishell> backup create postgres_main --output /backups/base.dump --format custom

# 2. Schedule daily incremental backups
aishell> backup schedule create --name daily_incremental ...

# 3. Schedule weekly full backups
aishell> backup schedule create --name weekly_full ...

# 4. Configure encryption
aishell> backup schedule update daily_incremental --encrypt --encryption-key ...

# 5. Set retention policy
aishell> backup retention set --keep-daily 7 --keep-weekly 4 --keep-monthly 12

# 6. Test restore
aishell> restore /backups/base.dump --database postgres_test --verify-only
```

### Exercise 2: Complex Migration

**Objective:** Create a multi-step migration with rollback

```sql
-- Create migration that:
-- 1. Adds new table
-- 2. Migrates data from old table
-- 3. Adds foreign key constraints
-- 4. Creates indexes
-- 5. Provides clean rollback
```

### Exercise 3: Cross-Database Migration

**Objective:** Migrate user sessions from PostgreSQL to Redis

```javascript
// Write script to:
// 1. Export sessions from PostgreSQL
// 2. Transform data format
// 3. Import to Redis with TTL
// 4. Verify migration
// 5. Remove old sessions from PostgreSQL
```

---

## Troubleshooting

### Backup Issues

```bash
# Backup fails - disk space
df -h
# Free up space or use compression

# Backup too slow
aishell> backup create postgres_main --jobs 4  # Parallel backup

# Cannot read encrypted backup
aishell> backup decrypt /backups/file.enc --output /backups/file.sql

# Verify backup integrity
aishell> backup verify /backups/file.dump
```

### Restore Issues

```bash
# Restore fails - permission issues
# Grant appropriate permissions to restore user

# Restore to wrong database version
# Use compatible backup or upgrade database first

# Partial restore needed
aishell> restore backup.sql --tables users,orders --confirm

# Restore interrupted
# Restart restore with --continue flag
aishell> restore backup.sql --continue --confirm
```

### Migration Issues

```bash
# Migration fails midway
aishell> migrate status postgres_main
# Fix the issue and re-run
aishell> migrate up postgres_main

# Need to skip a migration
aishell> migrate mark-applied postgres_main 20251011103000

# Rollback not working
# Check down migration logic
# Manual intervention may be required
```

---

## Next Steps

Congratulations! You've mastered backup, restore, and migration operations in AI-Shell. You now understand:

- Creating encrypted and compressed backups
- Scheduling automated backups
- Point-in-time recovery
- Database migrations and rollbacks
- Cross-database migrations
- Disaster recovery procedures

**Continue to Part 6:** [AI Features & Advanced Security](./HANDS_ON_PART6_AI_SECURITY.md)

Learn about:
- AI Query Assistant
- Natural language to SQL
- Advanced security features
- 2FA and SSO
- Anomaly detection

---

## Quick Reference

### Backup Commands

```bash
# Create backup
aishell> backup create <database> --output <file> [options]

# Options:
--compress gzip          # Compress backup
--encrypt                # Encrypt backup
--tables <tables>        # Backup specific tables
--exclude-tables <tables> # Exclude tables
--data-only              # Data only
--schema-only            # Schema only

# Restore
aishell> restore <file> --database <database> --confirm [options]

# Migrations
aishell> migrate create <name>      # Create migration
aishell> migrate up <database>      # Run migrations
aishell> migrate down <database>    # Rollback migrations
aishell> migrate status <database>  # Check status
```
