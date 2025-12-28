# Backup CLI Guide

Comprehensive guide to backup and recovery operations using AI-Shell's backup CLI commands.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Disaster Recovery](#disaster-recovery)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Overview

The AI-Shell Backup CLI provides enterprise-grade backup and recovery operations for multiple database types with features including:

- **Automated Backups**: Schedule backups with cron expressions
- **Multiple Formats**: SQL, JSON, and CSV backup formats
- **Compression**: Automatic compression with gzip/bzip2
- **Incremental Backups**: Save storage with incremental backups
- **Verification**: Integrity checks with checksums
- **Point-in-Time Recovery**: Restore to specific timestamps
- **Cross-Database Support**: PostgreSQL, MySQL, MongoDB, SQLite
- **Email Notifications**: Alert on backup success/failure

## Installation

```bash
# Install AI-Shell CLI
npm install -g ai-shell

# Verify installation
ai-shell --version

# Configure database connections
ai-shell connect postgresql://user:pass@localhost:5432/mydb --name production
```

## Quick Start

### Create Your First Backup

```bash
# Create a simple backup
ai-shell backup create --database production --name my-first-backup

# Create compressed backup with verification
ai-shell backup create --database production \
  --name verified-backup \
  --compression gzip \
  --verify

# Create incremental backup
ai-shell backup create --database production \
  --name incremental-backup \
  --incremental
```

### List Backups

```bash
# List all backups
ai-shell backup list

# List backups for specific database
ai-shell backup list --database production

# Filter by date range
ai-shell backup list --after 2024-01-01 --before 2024-12-31

# JSON output
ai-shell backup list --format json
```

### Restore a Backup

```bash
# Restore backup (with confirmation)
ai-shell backup restore backup-123456789

# Dry run (test without applying)
ai-shell backup restore backup-123456789 --dry-run

# Restore to different database
ai-shell backup restore backup-123456789 --database test-db

# Point-in-time restore
ai-shell backup restore backup-123456789 --point-in-time 2024-01-15T10:30:00
```

## Commands

### Backup Creation

#### `ai-shell backup create`

Create a new database backup with customizable options.

**Options:**
- `-d, --database <name>` - Database name (required)
- `-n, --name <name>` - Backup name (optional)
- `-c, --compression <type>` - Compression: gzip, bzip2, none (default: gzip)
- `--incremental` - Create incremental backup
- `--verify` - Verify backup after creation
- `--format <type>` - Backup format: sql, json, csv (default: sql)

**Examples:**

```bash
# Basic backup
ai-shell backup create --database mydb --name daily-backup

# Full backup with all options
ai-shell backup create \
  --database production \
  --name full-backup-2024-01-15 \
  --compression gzip \
  --verify \
  --format sql

# Incremental backup
ai-shell backup create \
  --database production \
  --name incremental-2024-01-15 \
  --incremental

# JSON format backup
ai-shell backup create \
  --database analytics \
  --name json-export \
  --format json
```

### Backup Restoration

#### `ai-shell backup restore <backup-id>`

Restore database from a backup.

**Options:**
- `-d, --database <name>` - Target database
- `--point-in-time <timestamp>` - Restore to specific point
- `--dry-run` - Test restore without applying
- `--verify` - Verify integrity before restore

**Examples:**

```bash
# Simple restore
ai-shell backup restore backup-abc123

# Restore to different database
ai-shell backup restore backup-abc123 --database staging

# Test restore (no changes)
ai-shell backup restore backup-abc123 --dry-run

# Point-in-time restore
ai-shell backup restore backup-abc123 \
  --point-in-time "2024-01-15 10:30:00"

# Restore with verification
ai-shell backup restore backup-abc123 --verify
```

### Backup Management

#### `ai-shell backup list`

List all available backups with filtering options.

**Options:**
- `-d, --database <name>` - Filter by database
- `--after <date>` - Show backups after date
- `--before <date>` - Show backups before date
- `--format <type>` - Output format: table, json

**Examples:**

```bash
# List all backups
ai-shell backup list

# Filter by database
ai-shell backup list --database production

# Date range filter
ai-shell backup list \
  --after 2024-01-01 \
  --before 2024-12-31

# JSON output
ai-shell backup list --format json > backups.json
```

#### `ai-shell backup info <backup-id>`

Display detailed information about a specific backup.

**Examples:**

```bash
# Show backup details
ai-shell backup info backup-abc123

# Output:
# ID: backup-abc123
# Database: production
# Date: 2024-01-15 10:30:00
# Format: sql
# Size: 125.45 MB
# Compressed: Yes
# Tables: 42
# Checksum: sha256:abc123...
```

#### `ai-shell backup delete <backup-id>`

Delete a backup permanently.

**Options:**
- `--force` - Force deletion without confirmation

**Examples:**

```bash
# Delete with confirmation
ai-shell backup delete backup-abc123 --force

# Multiple deletions
for id in backup-1 backup-2 backup-3; do
  ai-shell backup delete $id --force
done
```

### Backup Verification

#### `ai-shell backup verify <backup-id>`

Verify backup integrity with checksums.

**Options:**
- `--deep` - Deep verification with checksums

**Examples:**

```bash
# Basic verification
ai-shell backup verify backup-abc123

# Deep verification
ai-shell backup verify backup-abc123 --deep

# Verify all backups
for backup in $(ai-shell backup list --format json | jq -r '.[].id'); do
  echo "Verifying $backup..."
  ai-shell backup verify $backup --deep
done
```

#### `ai-shell backup test <backup-id>`

Test backup restore capability without applying changes.

**Options:**
- `--sample-size <n>` - Test sample size (default: 10)
- `--validate-data` - Validate data integrity

**Examples:**

```bash
# Basic test
ai-shell backup test backup-abc123

# Test with data validation
ai-shell backup test backup-abc123 --validate-data

# Custom sample size
ai-shell backup test backup-abc123 --sample-size 50
```

### Backup Scheduling

#### `ai-shell backup schedule <cron>`

Schedule automated backups using cron expressions.

**Options:**
- `-n, --name <name>` - Schedule name (required)
- `-d, --database <name>` - Database to backup (required)
- `--retention <days>` - Keep backups for N days (default: 30)
- `--email <address>` - Notification email

**Cron Expression Examples:**
- `0 2 * * *` - Daily at 2 AM
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 0` - Weekly on Sunday
- `0 0 1 * *` - Monthly on 1st day

**Examples:**

```bash
# Daily backup at 2 AM
ai-shell backup schedule "0 2 * * *" \
  --name daily-production-backup \
  --database production \
  --retention 30 \
  --email admin@company.com

# Hourly backup for critical data
ai-shell backup schedule "0 * * * *" \
  --name hourly-critical-backup \
  --database critical \
  --retention 7 \
  --email oncall@company.com

# Weekly full backup
ai-shell backup schedule "0 0 * * 0" \
  --name weekly-full-backup \
  --database production \
  --retention 90
```

#### `ai-shell backup schedules`

List all configured backup schedules.

**Examples:**

```bash
# List schedules
ai-shell backup schedules

# Output:
# Name                    Database    Schedule       Enabled  Next Run
# daily-prod-backup       production  0 2 * * *      Yes      2024-01-16 02:00:00
# hourly-critical         critical    0 * * * *      Yes      2024-01-15 11:00:00
```

#### `ai-shell backup unschedule <schedule-id>`

Remove a backup schedule.

**Examples:**

```bash
# Remove schedule
ai-shell backup unschedule schedule-abc123
```

### Import/Export

#### `ai-shell backup export <backup-id> <path>`

Export backup to external location.

**Examples:**

```bash
# Export to local path
ai-shell backup export backup-abc123 /backup/external/prod-backup.sql

# Export to network storage
ai-shell backup export backup-abc123 /mnt/nas/backups/prod-backup.sql

# Export multiple backups
for backup in $(ai-shell backup list --database production --format json | jq -r '.[].id'); do
  ai-shell backup export $backup /archive/$backup.sql
done
```

#### `ai-shell backup import <path>`

Import backup from external location.

**Examples:**

```bash
# Import backup
ai-shell backup import /backup/external/prod-backup.sql

# Import from network storage
ai-shell backup import /mnt/nas/backups/prod-backup.sql

# Batch import
for file in /archive/*.sql; do
  ai-shell backup import "$file"
done
```

## Disaster Recovery

### Complete Disaster Recovery Plan

#### 1. Preparation

```bash
# Test your backups regularly
ai-shell backup test backup-latest --validate-data

# Verify all critical backups
ai-shell backup verify backup-production --deep

# Document your recovery procedure
ai-shell backup info backup-latest > recovery-plan.txt
```

#### 2. Emergency Restore Procedure

```bash
# Step 1: Identify the latest good backup
ai-shell backup list --database production --format json | \
  jq -r '.[0].id'

# Step 2: Verify backup integrity
ai-shell backup verify backup-abc123 --deep

# Step 3: Test restore (dry-run)
ai-shell backup restore backup-abc123 --dry-run

# Step 4: Perform actual restore
ai-shell backup restore backup-abc123

# Step 5: Verify restoration
ai-shell health-check --database production
```

#### 3. Point-in-Time Recovery

```bash
# Find backup before incident
ai-shell backup list \
  --before "2024-01-15 10:00:00" \
  --database production

# Restore to point before data corruption
ai-shell backup restore backup-abc123 \
  --point-in-time "2024-01-15 09:55:00"
```

#### 4. Cross-Database Migration

```bash
# Backup source database
ai-shell backup create \
  --database production \
  --name migration-backup \
  --verify

# Export backup
ai-shell backup export backup-abc123 /migration/prod-backup.sql

# Import to new environment
ai-shell backup import /migration/prod-backup.sql

# Restore to new database
ai-shell backup restore backup-abc123 --database new-production
```

### Recovery Time Objectives (RTO)

| Database Size | Expected RTO | Recommended Strategy |
|---------------|--------------|---------------------|
| < 1 GB        | 5-10 minutes | Full backups hourly |
| 1-10 GB       | 15-30 minutes | Full daily + incrementals hourly |
| 10-100 GB     | 1-2 hours | Full weekly + incrementals daily |
| > 100 GB      | 2-4 hours | Full monthly + incrementals daily |

## Best Practices

### 1. Backup Frequency

```bash
# Critical databases: Hourly backups
ai-shell backup schedule "0 * * * *" \
  --name critical-hourly \
  --database critical \
  --retention 7

# Production databases: Daily backups
ai-shell backup schedule "0 2 * * *" \
  --name prod-daily \
  --database production \
  --retention 30

# Development databases: Weekly backups
ai-shell backup schedule "0 0 * * 0" \
  --name dev-weekly \
  --database development \
  --retention 14
```

### 2. Backup Verification

```bash
# Verify daily
#!/bin/bash
for backup in $(ai-shell backup list --format json | jq -r '.[].id'); do
  if ! ai-shell backup verify $backup --deep; then
    echo "ALERT: Backup verification failed for $backup"
    # Send alert
  fi
done
```

### 3. Storage Management

```bash
# Monitor backup storage
du -sh ~/.ai-shell/backups/*

# Clean old backups (keep last 30 days)
ai-shell backup list --before $(date -d '30 days ago' +%Y-%m-%d) | \
  jq -r '.[].id' | \
  xargs -I {} ai-shell backup delete {} --force
```

### 4. Compression Strategy

```bash
# Large databases: Use compression
ai-shell backup create \
  --database large-db \
  --compression gzip \
  --format sql

# Small databases: Skip compression for speed
ai-shell backup create \
  --database small-db \
  --compression none \
  --format sql
```

### 5. Multi-Environment Strategy

```bash
# Production: Daily full + hourly incremental
ai-shell backup schedule "0 2 * * *" \
  --name prod-full \
  --database production

ai-shell backup schedule "0 * * * *" \
  --name prod-incremental \
  --database production \
  --incremental

# Staging: Daily backups
ai-shell backup schedule "0 3 * * *" \
  --name staging-daily \
  --database staging

# Development: Weekly backups
ai-shell backup schedule "0 4 * * 0" \
  --name dev-weekly \
  --database development
```

## Troubleshooting

### Common Issues

#### Issue: Backup Creation Fails

```bash
# Check database connection
ai-shell connections --health

# Verify disk space
df -h ~/.ai-shell/backups

# Check permissions
ls -la ~/.ai-shell/backups

# Enable verbose logging
ai-shell backup create --database mydb --verbose
```

#### Issue: Restore Fails

```bash
# Verify backup integrity
ai-shell backup verify backup-abc123 --deep

# Check target database exists
ai-shell connect <connection-string> --test

# Try dry-run first
ai-shell backup restore backup-abc123 --dry-run

# Check logs
tail -f ~/.ai-shell/logs/backup.log
```

#### Issue: Scheduled Backups Not Running

```bash
# List schedules
ai-shell backup schedules

# Validate cron expression
# Use: https://crontab.guru/

# Check system cron service
systemctl status cron

# Review backup logs
tail -f ~/.ai-shell/logs/scheduled-backups.log
```

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Database connection not found" | Connection not configured | Run `ai-shell connect` first |
| "Insufficient disk space" | Storage full | Clean old backups or add storage |
| "Backup verification failed" | Corrupted backup | Create new backup |
| "Invalid cron expression" | Syntax error | Validate at crontab.guru |
| "Permission denied" | Insufficient permissions | Check file/directory permissions |

## Advanced Usage

### 1. Automated Backup Testing

```bash
#!/bin/bash
# test-backups.sh

echo "Testing all backups..."

for backup in $(ai-shell backup list --format json | jq -r '.[].id'); do
  echo "Testing $backup..."

  # Verify integrity
  if ! ai-shell backup verify $backup --deep; then
    echo "ERROR: Verification failed for $backup"
    continue
  fi

  # Test restore
  if ! ai-shell backup test $backup --validate-data; then
    echo "ERROR: Test failed for $backup"
    continue
  fi

  echo "SUCCESS: $backup is valid"
done
```

### 2. Cross-Region Backup Replication

```bash
#!/bin/bash
# replicate-backups.sh

REMOTE_HOST="backup-server.example.com"
REMOTE_PATH="/backups/replicas"

for backup in $(ai-shell backup list --format json | jq -r '.[].id'); do
  backup_path=$(ai-shell backup info $backup | grep Path | awk '{print $2}')

  echo "Replicating $backup to $REMOTE_HOST..."
  rsync -avz "$backup_path" "$REMOTE_HOST:$REMOTE_PATH/"

  # Verify remote copy
  ssh $REMOTE_HOST "sha256sum $REMOTE_PATH/$(basename $backup_path)"
done
```

### 3. Backup Performance Monitoring

```bash
#!/bin/bash
# monitor-backup-performance.sh

while true; do
  echo "=== Backup Performance Report ==="
  echo "Date: $(date)"

  # Backup count
  total=$(ai-shell backup list --format json | jq 'length')
  echo "Total backups: $total"

  # Storage usage
  size=$(du -sh ~/.ai-shell/backups | awk '{print $1}')
  echo "Storage used: $size"

  # Recent backup status
  recent=$(ai-shell backup list --format json | jq -r '.[0]')
  echo "Recent backup: $recent"

  sleep 3600  # Check hourly
done
```

### 4. Database Migration Workflow

```bash
#!/bin/bash
# migrate-database.sh

SOURCE_DB="production-old"
TARGET_DB="production-new"

echo "Step 1: Creating backup of source database..."
backup_id=$(ai-shell backup create \
  --database $SOURCE_DB \
  --name migration-backup \
  --verify \
  --format json | jq -r '.id')

echo "Step 2: Verifying backup..."
ai-shell backup verify $backup_id --deep

echo "Step 3: Exporting backup..."
ai-shell backup export $backup_id /migration/backup.sql

echo "Step 4: Testing restore..."
ai-shell backup restore $backup_id --dry-run

echo "Step 5: Restoring to new database..."
ai-shell backup restore $backup_id --database $TARGET_DB

echo "Step 6: Verifying migration..."
ai-shell health-check --database $TARGET_DB

echo "Migration complete!"
```

### 5. Compliance and Audit Trail

```bash
#!/bin/bash
# backup-audit.sh

echo "=== Backup Compliance Report ==="
echo "Generated: $(date)"
echo ""

# List all backups with metadata
ai-shell backup list --format json | \
  jq -r '.[] | "Database: \(.database), Date: \(.timestamp), Size: \(.size), Checksum: \(.metadata.checksum)"'

echo ""
echo "=== Schedule Compliance ==="

# Verify schedules are active
ai-shell backup schedules

echo ""
echo "=== Verification Status ==="

# Test random sample
sample=$(ai-shell backup list --format json | jq -r '.[0:5][].id')
for backup in $sample; do
  if ai-shell backup verify $backup --deep > /dev/null 2>&1; then
    echo "✓ $backup: Valid"
  else
    echo "✗ $backup: Failed"
  fi
done
```

## Performance Optimization

### 1. Parallel Backups

```bash
# Backup multiple databases in parallel
for db in db1 db2 db3; do
  ai-shell backup create --database $db --name parallel-$db &
done
wait
```

### 2. Compression Trade-offs

```bash
# Fast backup (no compression)
ai-shell backup create --database mydb --compression none

# Balanced (gzip)
ai-shell backup create --database mydb --compression gzip

# Maximum compression (slower, smaller)
ai-shell backup create --database mydb --compression bzip2
```

### 3. Incremental Backup Strategy

```bash
# Weekly full backup
ai-shell backup schedule "0 0 * * 0" \
  --name weekly-full \
  --database production

# Daily incremental backups
ai-shell backup schedule "0 2 * * *" \
  --name daily-incremental \
  --database production \
  --incremental
```

## Security Considerations

### 1. Encrypt Backups

```bash
# Create and encrypt backup
ai-shell backup create --database sensitive-db --name secure-backup
backup_path=$(ai-shell backup info backup-abc123 | grep Path | awk '{print $2}')

# Encrypt with GPG
gpg --encrypt --recipient admin@company.com "$backup_path"

# Store encrypted version
mv "$backup_path.gpg" /secure/backups/
```

### 2. Access Control

```bash
# Restrict backup directory permissions
chmod 700 ~/.ai-shell/backups

# Create backups with specific user
sudo -u backup-user ai-shell backup create --database production
```

### 3. Secure Transfer

```bash
# Export with secure transfer
ai-shell backup export backup-abc123 /tmp/backup.sql
scp /tmp/backup.sql backup-server:/secure/backups/
rm /tmp/backup.sql
```

## Support and Resources

- **Documentation**: https://github.com/ai-shell/docs
- **Issues**: https://github.com/ai-shell/issues
- **Community**: https://discord.gg/ai-shell

## Appendix

### Cron Expression Reference

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday=0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Backup File Formats

| Format | Use Case | Pros | Cons |
|--------|----------|------|------|
| SQL | Full database backup | Universal, easy restore | Large size |
| JSON | Data export/import | Human-readable, portable | Limited SQL features |
| CSV | Table-level export | Simple, widely supported | No schema info |

### Compression Comparison

| Method | Speed | Ratio | CPU Usage |
|--------|-------|-------|-----------|
| None | Fastest | 1:1 | Minimal |
| gzip | Fast | 3:1 | Low |
| bzip2 | Slow | 4:1 | High |

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0
