# Backup and Recovery Tutorial

> **📋 Implementation Status**
>
> **Current Status:** In Development
> **CLI Availability:** Partial
> **Completeness:** 40%
>
> **What Works Now:**
> - Basic database dump/restore operations
> - Manual backup creation via standard database tools
> - Database connection verification
>
> **Coming Soon:**
> - Automated backup scheduling
> - Point-in-time recovery (PITR)
> - Backup validation and verification
> - Retention policy management
> - Cross-database backup coordination
> - Disaster recovery automation
> - Backup compression and encryption
>
> **Note:** This tutorial describes the intended functionality. Check the [Gap Analysis Report](../FEATURE_GAP_ANALYSIS_REPORT.md) for detailed implementation status.

## Introduction and Overview

AI-Shell's intelligent backup and recovery system ensures you never lose critical data. With automated scheduling, point-in-time recovery, incremental backups, and cross-database support, AI-Shell transforms database backup from a manual chore into a seamless, automated process.

This tutorial will teach you how to:
- Create and schedule automated backups
- Perform point-in-time recovery
- Manage backup retention policies
- Validate backup integrity
- Restore databases with zero downtime
- Handle disaster recovery scenarios

**What You'll Learn:**
- Backup strategies and best practices
- Automated backup scheduling
- Incremental and differential backups
- Point-in-time recovery (PITR)
- Cross-database backup coordination
- Disaster recovery planning
- Backup validation and testing

**Time to Complete:** 30-40 minutes

---

## Prerequisites

Before starting this tutorial, ensure you have:

### Required
- AI-Shell installed (v1.0.0 or higher)
  ```bash
  npm install -g ai-shell
  ```
- Database connection with backup permissions
  ```bash
  ai-shell connect postgres://user:pass@localhost:5432/mydb
  ```
- Sufficient storage space for backups (at least 2x your database size)
- Anthropic API key configured
  ```bash
  export ANTHROPIC_API_KEY="your-api-key"
  ```

### Recommended
- Separate storage location for backups (not same disk as database)
- Access to development/test database for practice
- Understanding of your database size and growth rate
- Backup storage solution (S3, Google Cloud Storage, or local storage)

### Verify Your Setup
```bash
# Check backup features are available
ai-shell features check backup
# Expected: ✓ Backup features enabled

# Verify backup permissions
ai-shell check-permissions --feature backup
# Expected: ✓ Read access, ✓ Backup privileges

# Check available storage
ai-shell check-disk-space --backup-dir /backup
# Expected: Show available space

# Test backup functionality
ai-shell backup test --dry-run
# Expected: ✓ Backup test successful (no actual backup created)
```

---

## Step-by-Step Instructions

### Step 1: Your First Manual Backup

Let's create your first database backup.

```bash
# Create simple backup
ai-shell backup create

# AI-Shell creates backup with automatic naming
# 🔄 Creating backup...
#
# Backup Details:
#   Database: mydb
#   Type: Full
#   Started: 2025-10-28 14:30:00
#
# Progress:
#   ✓ Analyzing database (234MB)
#   ✓ Creating snapshot
#   ✓ Compressing (234MB → 67MB, 71% reduction)
#   ✓ Calculating checksum
#   ✓ Verifying integrity
#
# ✓ Backup completed successfully
#
# Backup Info:
#   Filename: mydb-20251028-143000.backup
#   Location: /backup/mydb-20251028-143000.backup
#   Size: 67MB (compressed from 234MB)
#   Duration: 12 seconds
#   Checksum: sha256:8f7a3d9c...

# Create backup with custom name
ai-shell backup create --name "before-migration"

# Create backup to specific location
ai-shell backup create --output /backups/important/
```

---

### Step 2: Understanding Backup Types

AI-Shell supports multiple backup types for different scenarios.

#### Full Backup
```bash
# Complete database backup (default)
ai-shell backup create --type full

# Best for:
# - Initial backups
# - Weekly/monthly archives
# - Pre-migration snapshots
#
# Pros: Complete standalone backup
# Cons: Largest size, slowest
```

#### Incremental Backup
```bash
# Only backup changes since last backup
ai-shell backup create --type incremental

# Best for:
# - Frequent backups (hourly, daily)
# - Large databases with small daily changes
# - Minimizing backup time and storage
#
# Pros: Fast, small size
# Cons: Requires full backup + all incrementals to restore
#
# Example sequence:
# Sunday: Full backup (234MB)
# Monday: Incremental (12MB - only Monday changes)
# Tuesday: Incremental (8MB - only Tuesday changes)
# Wednesday: Incremental (15MB - only Wednesday changes)
#
# To restore Wednesday: Need Sunday full + Mon + Tue + Wed incrementals
```

#### Differential Backup
```bash
# Backup all changes since last full backup
ai-shell backup create --type differential

# Best for:
# - Daily backups
# - Balance between full and incremental
#
# Pros: Faster restore than incremental (only need full + latest differential)
# Cons: Larger than incremental
#
# Example sequence:
# Sunday: Full backup (234MB)
# Monday: Differential (12MB - changes since Sunday)
# Tuesday: Differential (23MB - all changes since Sunday)
# Wednesday: Differential (34MB - all changes since Sunday)
#
# To restore Wednesday: Only need Sunday full + Wednesday differential
```

#### Schema-Only Backup
```bash
# Backup only database structure (no data)
ai-shell backup create --type schema-only

# Best for:
# - Version control of database structure
# - Quick structure snapshots
# - Migration planning
#
# Pros: Very fast, tiny size
# Cons: No data included
```

---

### Step 3: Automated Backup Scheduling

Set up automatic backups to run without manual intervention.

```bash
# Schedule daily backups at 2 AM
ai-shell backup schedule --interval daily --time "02:00"

# Output:
# ✓ Backup schedule created
#
# Schedule Details:
#   Frequency: Daily at 02:00
#   Type: Full (Sunday), Incremental (Mon-Sat)
#   Retention: 7 daily, 4 weekly, 12 monthly
#   Location: /backup
#   Notifications: enabled
#
# Next backup: 2025-10-29 02:00:00

# Schedule with custom pattern
ai-shell backup schedule \
  --cron "0 2 * * *" \          # Daily at 2 AM
  --type full \
  --retain-days 30 \
  --retain-weeks 12 \
  --retain-months 12

# Multiple backup schedules
ai-shell backup schedule --name hourly-incremental \
  --interval hourly \
  --type incremental

ai-shell backup schedule --name weekly-full \
  --interval weekly \
  --day sunday \
  --time "01:00" \
  --type full

# View scheduled backups
ai-shell backup schedules list

# Output:
# 📅 Backup Schedules
#
# 1. daily-backup (active)
#    Frequency: Daily at 02:00
#    Type: Full (Sunday), Incremental (Mon-Sat)
#    Next run: 2025-10-29 02:00:00
#
# 2. hourly-incremental (active)
#    Frequency: Hourly
#    Type: Incremental
#    Next run: 2025-10-28 15:00:00
#
# 3. weekly-full (active)
#    Frequency: Weekly (Sunday) at 01:00
#    Type: Full
#    Next run: 2025-11-03 01:00:00
```

---

### Step 4: Backup Management and Organization

Organize and manage your backup files effectively.

```bash
# List all backups
ai-shell backup list

# Output:
# 📦 Database Backups
#
# Full Backups:
# 1. mydb-20251028-020000.backup
#    Date: 2025-10-28 02:00:00
#    Size: 67MB
#    Type: Full
#    Status: ✓ Verified
#
# 2. mydb-20251021-020000.backup
#    Date: 2025-10-21 02:00:00
#    Size: 65MB
#    Type: Full
#    Status: ✓ Verified
#
# Incremental Backups (last 7 days):
# - 7 incremental backups (89MB total)
#
# Total: 9 backups, 156MB

# Filter backups
ai-shell backup list --type full
ai-shell backup list --after "2025-10-01"
ai-shell backup list --status verified

# Get backup details
ai-shell backup info mydb-20251028-020000.backup

# Output:
# 📦 Backup Information
#
# Filename: mydb-20251028-020000.backup
# Database: mydb
# Type: Full
# Created: 2025-10-28 02:00:00
# Size: 67MB (compressed from 234MB)
# Compression: gzip (71% reduction)
# Checksum: sha256:8f7a3d9c...
# Status: ✓ Verified (2025-10-28 02:05:00)
#
# Content:
#   Tables: 23
#   Rows: 1,247,893
#   Indexes: 45
#   Triggers: 8
#   Functions: 12
#
# Restore Time: ~45 seconds (estimated)
# Compatible Versions: PostgreSQL 13+
```

---

### Step 5: Backup Retention Policies

Automatically manage backup lifecycle to save storage.

```bash
# Configure retention policy
ai-shell backup retention set \
  --keep-daily 7 \      # Keep 7 daily backups
  --keep-weekly 4 \     # Keep 4 weekly backups
  --keep-monthly 12 \   # Keep 12 monthly backups
  --keep-yearly 3       # Keep 3 yearly backups

# View retention policy
ai-shell backup retention show

# Output:
# 📊 Backup Retention Policy
#
# Daily Backups: Keep last 7 (1 week)
# Weekly Backups: Keep last 4 (1 month)
# Monthly Backups: Keep last 12 (1 year)
# Yearly Backups: Keep last 3 (3 years)
#
# Current Status:
#   Daily: 7/7 (full)
#   Weekly: 4/4 (full)
#   Monthly: 8/12 (67%)
#   Yearly: 1/3 (33%)
#
# Next Cleanup: 2025-10-29 03:00:00
# Space to be freed: ~45MB

# Apply retention policy immediately
ai-shell backup retention apply

# Output:
# 🗑️ Applying retention policy...
#
# Backups to remove:
#   ❌ mydb-20250927-020000.backup (older than 7 days)
#   ❌ mydb-20250920-020000.backup (superseded by weekly)
#   ... (5 more)
#
# Total to remove: 7 backups (234MB)
# Confirm deletion? [y/N]: y
#
# ✓ 7 backups deleted
# ✓ 234MB freed
```

---

### Step 6: Backup Validation and Verification

Ensure your backups are valid and restorable.

```bash
# Verify backup integrity
ai-shell backup verify mydb-20251028-020000.backup

# Output:
# 🔍 Verifying backup integrity...
#
# Tests:
#   ✓ File exists and is readable
#   ✓ Checksum matches (sha256)
#   ✓ Archive structure is valid
#   ✓ Compression is intact
#   ✓ Database schema is complete
#   ✓ All tables are present
#   ✓ Indexes are complete
#   ✓ No corruption detected
#
# ✓ Backup verification successful
# Backup is valid and restorable

# Test restore (without actually restoring)
ai-shell backup test-restore mydb-20251028-020000.backup

# Output:
# 🧪 Testing backup restore...
#
# Creating temporary test database...
# ✓ Test database created
#
# Restoring backup to test database...
# ✓ Schema restored (23 tables)
# ✓ Data restored (1,247,893 rows)
# ✓ Indexes rebuilt (45 indexes)
# ✓ Constraints applied (34 constraints)
#
# Validation:
#   ✓ Row counts match expected
#   ✓ Primary keys intact
#   ✓ Foreign keys intact
#   ✓ Indexes functional
#   ✓ No data corruption
#
# Cleaning up test database...
# ✓ Test database removed
#
# ✓ Restore test successful
# Estimated restore time: 45 seconds

# Verify all backups automatically
ai-shell backup verify-all --schedule daily
```

---

### Step 7: Restoring from Backups

Recover your database from backup files.

```bash
# Simple restore (overwrites current database)
ai-shell backup restore mydb-20251028-020000.backup

# Output:
# ⚠️  WARNING: This will overwrite database 'mydb'
# Current database will be backed up first for safety.
#
# Continue? [y/N]: y
#
# 🔄 Restoring database...
#
# Safety:
#   ✓ Created safety backup: mydb-pre-restore-20251028-143000.backup
#
# Restore Progress:
#   ✓ Stopping active connections (3 connections closed)
#   ✓ Clearing current database
#   ✓ Restoring schema (23 tables)
#   ✓ Restoring data (1,247,893 rows)
#   ✓ Rebuilding indexes (45 indexes)
#   ✓ Applying constraints
#   ✓ Restoring triggers and functions
#   ✓ Verifying integrity
#
# ✓ Database restored successfully
# Duration: 47 seconds
# Database is now at: 2025-10-28 02:00:00

# Restore to different database
ai-shell backup restore mydb-20251028-020000.backup \
  --target-db mydb_restored

# Restore specific tables only
ai-shell backup restore mydb-20251028-020000.backup \
  --tables users,orders,products

# Restore without downtime (to separate instance)
ai-shell backup restore mydb-20251028-020000.backup \
  --target postgres://other-host:5432/mydb \
  --no-downtime
```

---

### Step 8: Point-in-Time Recovery (PITR)

Restore your database to any specific moment in time.

```bash
# Enable continuous backup (required for PITR)
ai-shell backup pitr enable

# Output:
# 🔄 Enabling Point-in-Time Recovery...
#
# Configuration:
#   ✓ WAL archiving enabled
#   ✓ Archive directory: /backup/wal-archive
#   ✓ Continuous backup mode activated
#
# PITR is now active. You can restore to any point in time.
# First recovery point: 2025-10-28 14:30:00

# Check PITR status
ai-shell backup pitr status

# Output:
# 📊 Point-in-Time Recovery Status
#
# Status: ✓ Active
# First recovery point: 2025-10-28 14:30:00
# Latest recovery point: 2025-10-28 14:45:23
# Coverage: 15 minutes 23 seconds
#
# WAL Archives:
#   Location: /backup/wal-archive
#   Archives: 23 files
#   Size: 145MB
#   Oldest: 2025-10-28 14:30:00
#   Newest: 2025-10-28 14:45:23

# Restore to specific point in time
ai-shell backup pitr restore --point-in-time "2025-10-28 14:35:00"

# Output:
# 🔄 Point-in-Time Recovery
#
# Target time: 2025-10-28 14:35:00
# Current time: 2025-10-28 14:45:23
# Recovery window: 10 minutes 23 seconds back
#
# ⚠️  This will restore database to 2025-10-28 14:35:00
# All changes after that point will be lost.
#
# Continue? [y/N]: y
#
# Recovery Progress:
#   ✓ Finding base backup (2025-10-28 14:30:00)
#   ✓ Restoring base backup
#   ✓ Applying WAL archives (5 archives)
#   ✓ Replaying transactions up to 14:35:00
#   ✓ Stopping at target point
#   ✓ Verifying consistency
#
# ✓ Point-in-Time recovery successful
# Database restored to: 2025-10-28 14:35:00
#
# Timeline:
#   Base backup: 14:30:00
#   Target time: 14:35:00 ← database is here now
#   Current time: 14:45:23

# Restore to "5 minutes ago"
ai-shell backup pitr restore --relative "5 minutes ago"

# Restore to before specific event
ai-shell backup pitr restore --before-transaction <transaction-id>
```

---

### Step 9: Cross-Database Backup Coordination

Coordinate backups across multiple databases in federation.

```bash
# Backup multiple databases together
ai-shell backup create --all-databases

# Output:
# 🔄 Creating coordinated backup...
#
# Databases:
#   - postgres-main (PostgreSQL)
#   - mongodb-products (MongoDB)
#   - redis-cache (Redis)
#
# Strategy: Coordinated snapshot at 14:50:00
#
# Progress:
#   ✓ Taking snapshot of postgres-main
#   ✓ Taking snapshot of mongodb-products
#   ✓ Saving redis snapshot
#   ✓ Creating manifest
#   ✓ Verifying consistency
#
# ✓ Coordinated backup completed
#
# Backup Set: multi-db-20251028-145000
# Files:
#   - postgres-main.backup (67MB)
#   - mongodb-products.archive (45MB)
#   - redis-cache.rdb (12MB)
#   - manifest.json (4KB)
# Total size: 124MB
#
# ⚠️  Important: This backup set must be restored together
#              to maintain data consistency across databases.

# Schedule coordinated backups
ai-shell backup schedule \
  --all-databases \
  --interval daily \
  --time "02:00" \
  --coordinated

# Restore coordinated backup
ai-shell backup restore multi-db-20251028-145000 --all
```

---

### Step 10: Disaster Recovery Planning

Prepare for worst-case scenarios with disaster recovery setup.

```bash
# Create disaster recovery plan
ai-shell backup dr-plan create

# Output:
# 🔧 Creating Disaster Recovery Plan...
#
# Analyzing environment...
#   Database: mydb (PostgreSQL)
#   Size: 234MB
#   Daily change rate: ~5%
#   Critical: Yes
#
# Recommended DR Plan:
#
# 1. Backup Schedule:
#    - Full backup: Daily at 02:00
#    - Incremental: Every 4 hours
#    - PITR: Enabled (continuous)
#
# 2. Backup Locations:
#    - Primary: Local (/backup)
#    - Secondary: S3 (s3://backups/mydb)
#    - Tertiary: Google Cloud (gs://dr-backups/mydb)
#
# 3. Retention:
#    - Primary: 7 days
#    - Secondary: 30 days
#    - Tertiary: 1 year
#
# 4. Recovery Objectives:
#    - RPO (Recovery Point): 4 hours
#    - RTO (Recovery Time): 1 hour
#
# 5. Testing:
#    - Monthly DR drill
#    - Quarterly full recovery test
#
# Apply this plan? [y/N]: y

# Configure off-site backup
ai-shell backup remote add s3://my-backups/mydb \
  --access-key $AWS_ACCESS_KEY \
  --secret-key $AWS_SECRET_KEY \
  --region us-east-1

# Enable automatic remote sync
ai-shell backup remote sync enable \
  --destination s3://my-backups/mydb \
  --schedule "after-each-backup"

# Test disaster recovery
ai-shell backup dr-test

# Output:
# 🧪 Disaster Recovery Test
#
# Scenario: Complete database loss
#
# Test Steps:
#   1. Simulating database failure...
#   2. Identifying latest valid backup...
#   3. Retrieving from remote (S3)...
#   4. Restoring to test environment...
#   5. Verifying data integrity...
#   6. Testing application connectivity...
#   7. Measuring recovery time...
#
# Results:
#   ✓ Recovery successful
#   ✓ Data integrity verified
#   ✓ Application functional
#
# Metrics:
#   Recovery Point: 2025-10-28 02:00:00 (current time: 14:50:00)
#   Data Loss: 12 hours 50 minutes
#   Recovery Time: 18 minutes 34 seconds
#
# Analysis:
#   ✓ RPO met (target: 4 hours, actual: 12h 50m) ⚠️  exceeds target
#   ✓ RTO met (target: 1 hour, actual: 18m 34s)
#
# Recommendation:
#   ⚡ Increase incremental backup frequency to meet RPO
```

---

## Common Use Cases

### Use Case 1: Production Database Protection

**Scenario:** Protect critical production database with comprehensive backup strategy.

```bash
# Set up production backup strategy
ai-shell backup strategy production

# AI-Shell configures:
#
# ✓ Full backup: Daily at 2 AM
# ✓ Incremental: Every 2 hours
# ✓ PITR: Enabled (continuous WAL archiving)
# ✓ Remote backup: S3 (automatic sync)
# ✓ Retention: 7 daily, 4 weekly, 12 monthly, 7 yearly
# ✓ Verification: Automatic after each backup
# ✓ Test restore: Weekly
# ✓ Monitoring: Real-time alerts
# ✓ Encryption: AES-256
#
# Recovery capabilities:
# - RPO: 2 hours (incremental backups)
# - RTO: < 30 minutes (optimized restore)
# - PITR: Any point in time (continuous)

# Monitor backup health
ai-shell backup health-check --production

# Output:
# 📊 Production Backup Health
#
# Status: ✓ Healthy
#
# Last 24 Hours:
#   ✓ 12 incremental backups (all successful)
#   ✓ 1 full backup (successful)
#   ✓ 12 verifications (all passed)
#   ✓ WAL archiving (100% coverage)
#   ✓ Remote sync (up to date)
#
# Storage:
#   Local: 1.2GB / 10GB (12%)
#   S3: 8.4GB / 1TB (0.8%)
#
# Last Restore Test: 2025-10-21 (7 days ago) ✓ Passed
# Next Restore Test: 2025-10-28
```

---

### Use Case 2: Pre-Migration Backup

**Scenario:** Create safe fallback before major database migration.

```bash
# Create comprehensive pre-migration backup
ai-shell backup create --name "pre-migration-v2" \
  --type full \
  --verify \
  --test-restore \
  --remote s3://backups/migrations/

# Output:
# 🔄 Creating migration safety backup...
#
# Backup Progress:
#   ✓ Creating full backup (234MB)
#   ✓ Compressing (234MB → 67MB)
#   ✓ Verifying integrity
#   ✓ Testing restore (successful)
#   ✓ Uploading to S3
#   ✓ Creating backup manifest
#
# ✓ Pre-migration backup complete
#
# Safety Backup:
#   Name: pre-migration-v2
#   Local: /backup/pre-migration-v2-20251028-150000.backup
#   Remote: s3://backups/migrations/pre-migration-v2-20251028-150000.backup
#   Verified: ✓ Yes
#   Restore tested: ✓ Yes (47 seconds)
#
# You can now proceed with migration.
# To rollback: ai-shell backup restore pre-migration-v2

# After migration, verify you can still restore old backup
ai-shell backup verify pre-migration-v2 --compatibility-check
```

---

### Use Case 3: Development Database Snapshots

**Scenario:** Quick snapshots for development and testing.

```bash
# Create dev snapshot
ai-shell backup snapshot --name "feature-xyz-testing"

# Output:
# 📸 Creating development snapshot...
# ✓ Snapshot created in 3 seconds
#
# Snapshot: feature-xyz-testing
# Type: Lightweight snapshot (copy-on-write)
# Size: 2MB (metadata only, shares data with original)
#
# Restore: ai-shell backup restore-snapshot feature-xyz-testing

# List snapshots
ai-shell backup snapshots list

# Quickly restore snapshot
ai-shell backup restore-snapshot feature-xyz-testing
# Restore in 1-2 seconds (instant)

# Remove snapshot when done
ai-shell backup snapshot remove feature-xyz-testing
```

---

### Use Case 4: Compliance and Archival

**Scenario:** Long-term backup retention for compliance requirements.

```bash
# Create archival backup
ai-shell backup create --type full \
  --name "EOY-2025-archive" \
  --compress maximum \
  --encrypt \
  --immutable \
  --archive

# Output:
# 🔄 Creating archival backup...
#
# Backup Progress:
#   ✓ Creating full backup
#   ✓ Maximum compression (234MB → 45MB, 81% reduction)
#   ✓ Encrypting (AES-256)
#   ✓ Setting immutable flag (cannot be deleted)
#   ✓ Adding compliance metadata
#   ✓ Uploading to archival storage
#
# ✓ Archival backup complete
#
# Archive Details:
#   Name: EOY-2025-archive
#   Date: 2025-10-28
#   Size: 45MB (encrypted, compressed)
#   Retention: Permanent (immutable)
#   Compliance: SOC2, HIPAA compliant
#   Location: s3://archives/EOY-2025-archive.backup
#   Checksum: sha256:8f7a3d9c...
#
# ⚠️  This backup cannot be deleted (immutable)
# Minimum retention: 7 years (compliance requirement)

# List archival backups
ai-shell backup list --type archive
```

---

### Use Case 5: Disaster Recovery Across Regions

**Scenario:** Multi-region disaster recovery setup.

```bash
# Configure multi-region DR
ai-shell backup dr-setup \
  --primary us-east-1 \
  --secondary us-west-2 \
  --tertiary eu-west-1

# Output:
# 🌍 Setting up multi-region disaster recovery...
#
# Configuration:
#   Primary: US East (N. Virginia)
#     - Live database
#     - Local backups (7 days)
#     - S3 backups (30 days)
#
#   Secondary: US West (Oregon)
#     - Backup replication (async)
#     - Standby database (optional)
#     - Recovery time: 15 minutes
#
#   Tertiary: EU West (Ireland)
#     - Long-term archives (1 year)
#     - Compliance copies
#     - Recovery time: 1 hour
#
# Replication:
#   Primary → Secondary: Every 2 hours
#   Primary → Tertiary: Daily
#   Cross-region bandwidth: ~25MB/hour
#
# Failover:
#   Primary → Secondary: Automatic (15 min)
#   Primary → Tertiary: Manual (1 hour)
#
# ✓ Multi-region DR configured

# Test regional failover
ai-shell backup dr-failover-test \
  --from us-east-1 \
  --to us-west-2

# Output:
# 🧪 Testing Regional Failover
#
# Scenario: us-east-1 complete failure
# Failover to: us-west-2
#
# Test Steps:
#   1. ✓ Retrieve latest backup from us-west-2
#   2. ✓ Provision test database in us-west-2
#   3. ✓ Restore from backup
#   4. ✓ Apply WAL from replication
#   5. ✓ Verify data consistency
#   6. ✓ Test application connectivity
#   7. ✓ Measure failover time
#
# Results:
#   ✓ Failover successful
#   Data loss: 2 hours (last replication)
#   Failover time: 14 minutes 23 seconds
#   Application ready: 16 minutes 45 seconds
#
# ✓ DR failover test passed
```

---

## Troubleshooting Tips

### Issue 1: Backup Fails with Insufficient Space

**Problem:** Not enough disk space to create backup.

**Solutions:**
```bash
# Check available space
ai-shell check-disk-space --backup-dir /backup

# Clean up old backups
ai-shell backup cleanup --apply-retention

# Use compression
ai-shell backup create --compress high

# Use remote storage
ai-shell backup create --remote s3://backups/

# Backup to different location
ai-shell backup create --output /mnt/large-drive/backup/
```

---

### Issue 2: Restore Takes Too Long

**Problem:** Database restore is taking hours.

**Solutions:**
```bash
# Use parallel restore
ai-shell backup restore mydb.backup --parallel 4

# Restore without indexes first (rebuild after)
ai-shell backup restore mydb.backup --defer-indexes

# Restore only essential tables first
ai-shell backup restore mydb.backup \
  --tables users,orders,products \
  --remainder-async

# Use faster storage for restore
ai-shell backup restore mydb.backup \
  --temp-tablespace /fast-ssd/restore-temp/
```

---

### Issue 3: Backup Verification Fails

**Problem:** Backup verification reports corruption.

**Solutions:**
```bash
# Get detailed verification report
ai-shell backup verify mydb.backup --verbose

# Check if backup file is damaged
ai-shell backup integrity-check mydb.backup

# If corrupted, restore from previous backup
ai-shell backup list --verified-only

# Enable backup redundancy (multiple copies)
ai-shell config set backup.redundancy 2

# Test backup immediately after creation
ai-shell config set backup.verify-after-create true
```

---

### Issue 4: PITR Not Working

**Problem:** Point-in-time recovery fails or is unavailable.

**Solutions:**
```bash
# Check PITR status
ai-shell backup pitr status

# Verify WAL archiving is working
ai-shell backup pitr check-wal-archiving

# Check for WAL archive gaps
ai-shell backup pitr check-coverage

# If gaps found, re-enable PITR
ai-shell backup pitr repair

# Increase WAL retention
ai-shell config set pitr.wal-retention 7d
```

---

### Issue 5: Remote Backup Sync Failing

**Problem:** Backups not uploading to remote storage (S3, GCS).

**Solutions:**
```bash
# Test remote connection
ai-shell backup remote test s3://backups/

# Check credentials
ai-shell backup remote auth-check

# View sync logs
ai-shell backup remote logs

# Retry failed syncs
ai-shell backup remote retry-failed

# Increase timeout for large backups
ai-shell config set backup.remote.timeout 3600

# Use resumable uploads
ai-shell config set backup.remote.resumable true
```

---

## Best Practices

### 1. Follow the 3-2-1 Rule

```bash
# 3 copies of data
# - Original database
# - Local backup
# - Remote backup

# 2 different media types
# - Disk (local)
# - Cloud (S3/GCS)

# 1 copy off-site
# - Remote storage in different region

ai-shell backup strategy 3-2-1 --auto-configure
```

### 2. Test Restores Regularly

```bash
# Schedule monthly restore tests
ai-shell backup test-restore-schedule monthly

# Verify you can actually restore, not just that backups exist
# "Untested backups are not backups"
```

### 3. Monitor Backup Health

```bash
# Set up alerts
ai-shell alerts add backup-failed
ai-shell alerts add backup-verification-failed
ai-shell alerts add backup-storage-low

# Regular health checks
ai-shell backup health-check --schedule daily
```

### 4. Encrypt Sensitive Data

```bash
# Always encrypt backups containing sensitive data
ai-shell config set backup.encryption enabled
ai-shell config set backup.encryption-key-id $KEY_ID
```

### 5. Document Recovery Procedures

```bash
# Generate recovery runbook
ai-shell backup runbook generate

# Keep runbook accessible (not in same system as backups!)
```

### 6. Separate Backup Storage

```bash
# Never store backups on same disk/server as database
# Use separate physical storage
# Use different cloud account/region
```

---

## Next Steps

### Master Related Features

1. **Disaster Recovery**
   - Advanced DR planning and testing
   - [Tutorial: Disaster Recovery](./disaster-recovery.md)

2. **Security**
   - Backup encryption and access control
   - [Tutorial: Security Setup](./security.md)

3. **Monitoring**
   - Monitor backup and restore performance
   - [Tutorial: Performance Monitoring](./performance-monitoring.md)

### Practice Exercises

1. **Exercise 1: Basic Backup & Restore**
   - Create manual backup
   - Restore to test database
   - Verify data integrity

2. **Exercise 2: Automated Backups**
   - Set up daily backup schedule
   - Configure retention policy
   - Test automatic verification

3. **Exercise 3: Point-in-Time Recovery**
   - Enable PITR
   - Make some changes
   - Restore to 5 minutes ago

4. **Exercise 4: Disaster Recovery**
   - Create DR plan
   - Set up remote backups
   - Test full recovery scenario

5. **Exercise 5: Production Readiness**
   - Implement complete backup strategy
   - Test restore under time pressure
   - Document recovery procedures

### Additional Resources

- **Documentation**: [Backup guide](https://docs.ai-shell.dev/backup)
- **Best Practices**: [Backup best practices](../best-practices.md#backup)
- **API Reference**: [Backup API](../api/backup.md)
- **Examples**: [Backup examples](../examples/backup)

---

## Summary

You've learned how to:
- Create and manage database backups
- Set up automated backup schedules
- Implement retention policies
- Verify backup integrity
- Restore databases and perform point-in-time recovery
- Plan for disaster recovery scenarios

Backups are your last line of defense against data loss. With AI-Shell's intelligent backup system, you can sleep soundly knowing your data is protected, verified, and recoverable.

**Key Takeaway:** The best backup strategy is one that's automated, tested, and proven to work. Regular testing is as important as regular backups.

---

**Related Tutorials:**
- [Migrations](./migrations.md)
- [Security Setup](./security.md)
- [Performance Monitoring](./performance-monitoring.md)

**Need Help?** [Visit our documentation](https://docs.ai-shell.dev) or [join the community](https://github.com/your-org/ai-shell/discussions)
