# Backup and Recovery Guide

## Table of Contents

1. [Overview](#overview)
2. [Creating Backups](#creating-backups)
3. [Scheduling Automated Backups](#scheduling-automated-backups)
4. [Restoring from Backups](#restoring-from-backups)
5. [Cloud Backup Integration](#cloud-backup-integration)
6. [Backup Verification](#backup-verification)
7. [Disaster Recovery](#disaster-recovery)
8. [Best Practices](#best-practices)

---

## Overview

Backup and recovery are critical components of database management. AI-Shell provides comprehensive backup solutions with support for multiple databases and cloud storage providers.

### Backup Strategy (3-2-1 Rule)

```
┌───────────────────────────────────────────────────────────┐
│                   3-2-1 Backup Strategy                   │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  3 Copies of Data                                        │
│  ├── Production Database (primary)                       │
│  ├── Local Backup (secondary)                            │
│  └── Cloud Backup (tertiary)                             │
│                                                           │
│  2 Different Media Types                                 │
│  ├── Disk (local SSD/HDD)                                │
│  └── Cloud Storage (S3/Azure/GCP)                        │
│                                                           │
│  1 Off-Site Backup                                       │
│  └── Cloud Storage (different region)                    │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Backup Types

| Type | Description | Use Case | Frequency |
|------|-------------|----------|-----------|
| **Full** | Complete database backup | Weekly, Monthly | Lower |
| **Incremental** | Changes since last backup | Hourly, Daily | Higher |
| **Differential** | Changes since last full backup | Daily | Medium |
| **Point-in-Time** | Specific timestamp recovery | Continuous WAL/Binlog | Continuous |
| **Logical** | SQL dump format | Portability, Versioning | As needed |
| **Physical** | Raw data files | Fast restore, Large DBs | Regular |

---

## Creating Backups

### Manual Backups

#### PostgreSQL

```bash
# Full backup (custom format, compressed)
aishell backup create prod-db \
  --name "full-backup-$(date +%Y%m%d)" \
  --type full \
  --format custom \
  --compress

# Output:
# ✓ Backup started
# ✓ Analyzing database size: 15.4 GB
# ✓ Estimated time: ~8 minutes
# ✓ Creating backup...
# ✓ Backup completed: full-backup-20240115.backup
# ✓ Size: 4.2 GB (72% compression)
# ✓ Duration: 7m 23s
# ✓ Location: ~/.aishell/backups/prod-db/full-backup-20240115.backup

# Backup specific schemas
aishell backup create prod-db \
  --name schema-backup \
  --schema public,analytics \
  --format directory

# Backup specific tables
aishell backup create prod-db \
  --name table-backup \
  --table users,orders,products \
  --format custom

# Backup with parallel processing
aishell backup create prod-db \
  --name parallel-backup \
  --jobs 4 \
  --compress \
  --format directory

# Schema-only backup (no data)
aishell backup create prod-db \
  --name schema-only \
  --schema-only \
  --format sql

# Data-only backup
aishell backup create prod-db \
  --name data-only \
  --data-only \
  --format custom
```

#### MySQL

```bash
# Full backup using mysqldump
aishell backup create mysql-prod \
  --name "mysql-backup-$(date +%Y%m%d)" \
  --type full \
  --compress

# Backup with single transaction (for InnoDB)
aishell backup create mysql-prod \
  --name consistent-backup \
  --single-transaction \
  --compress

# Backup specific databases
aishell backup create mysql-prod \
  --name multi-db-backup \
  --databases ecommerce,analytics,logs \
  --compress

# Backup with routines and triggers
aishell backup create mysql-prod \
  --name complete-backup \
  --routines \
  --triggers \
  --events \
  --compress
```

#### MongoDB

```bash
# Full backup using mongodump
aishell backup create mongo-prod \
  --name "mongo-backup-$(date +%Y%m%d)" \
  --type full \
  --compress

# Backup specific database
aishell backup create mongo-prod \
  --name analytics-backup \
  --database analytics \
  --compress

# Backup specific collections
aishell backup create mongo-prod \
  --name users-backup \
  --database myapp \
  --collection users \
  --compress

# Backup with query filter
aishell backup create mongo-prod \
  --name recent-orders \
  --database ecommerce \
  --collection orders \
  --query '{"created_at": {"$gte": {"$date": "2024-01-01T00:00:00Z"}}}' \
  --compress
```

#### Redis

```bash
# Create RDB snapshot
aishell backup create redis-prod \
  --name "redis-backup-$(date +%Y%m%d)" \
  --type rdb

# Backup with AOF (Append-Only File)
aishell backup create redis-prod \
  --name redis-aof-backup \
  --type aof \
  --rewrite
```

### Incremental Backups

```bash
# PostgreSQL incremental using WAL archiving
aishell backup create prod-db \
  --name incremental-backup \
  --type incremental \
  --base-backup last-full-backup

# Configure WAL archiving
aishell backup configure-wal prod-db \
  --archive-mode on \
  --archive-command "cp %p ~/.aishell/wal_archive/%f"

# MySQL incremental using binary logs
aishell backup create mysql-prod \
  --name mysql-incremental \
  --type incremental \
  --binlog-position last-position

# MongoDB incremental using oplog
aishell backup create mongo-prod \
  --name mongo-incremental \
  --type incremental \
  --oplog
```

### Encrypted Backups

```bash
# Backup with encryption
aishell backup create prod-db \
  --name encrypted-backup \
  --encrypt \
  --encryption-key ~/.aishell/keys/backup.key \
  --compress

# Generate encryption key
aishell backup generate-key \
  --output ~/.aishell/keys/backup.key \
  --algorithm AES-256

# Backup with password encryption
aishell backup create prod-db \
  --name password-encrypted \
  --encrypt \
  --password-prompt \
  --compress
```

---

## Scheduling Automated Backups

### Creating Backup Schedules

```bash
# Daily full backup at 2 AM
aishell backup schedule prod-db \
  --name daily-full \
  --type full \
  --schedule "0 2 * * *" \
  --compress \
  --upload s3 \
  --retention 7

# Hourly incremental backups
aishell backup schedule prod-db \
  --name hourly-incremental \
  --type incremental \
  --schedule "0 * * * *" \
  --compress \
  --retention 24

# Weekly backup with rotation
aishell backup schedule prod-db \
  --name weekly-backup \
  --type full \
  --schedule "0 2 * * 0" \
  --compress \
  --upload s3,azure \
  --retention-days 30 \
  --retention-weeks 12 \
  --retention-months 6

# Complex schedule
aishell backup schedule prod-db \
  --name complex-schedule \
  --full "0 2 * * 0" \          # Weekly full (Sunday 2 AM)
  --differential "0 2 * * 1-6" \ # Daily differential (Mon-Sat 2 AM)
  --incremental "0 * * * *" \    # Hourly incremental
  --compress \
  --encrypt \
  --upload s3
```

### Managing Schedules

```bash
# List all backup schedules
aishell backup schedule list

# Output:
# Name              | Type        | Schedule      | Next Run           | Status
# ------------------|-------------|---------------|--------------------|---------
# daily-full        | full        | 0 2 * * *     | 2024-01-16 02:00  | Active
# hourly-increment  | incremental | 0 * * * *     | 2024-01-15 14:00  | Active
# weekly-backup     | full        | 0 2 * * 0     | 2024-01-21 02:00  | Active

# Show schedule details
aishell backup schedule show daily-full

# Enable/disable schedule
aishell backup schedule disable daily-full
aishell backup schedule enable daily-full

# Update schedule
aishell backup schedule update daily-full \
  --schedule "0 3 * * *" \
  --retention 14

# Delete schedule
aishell backup schedule delete hourly-increment
```

### Retention Policies

```bash
# Configure retention policy
aishell backup retention prod-db \
  --daily 7 \      # Keep 7 daily backups
  --weekly 4 \     # Keep 4 weekly backups
  --monthly 12 \   # Keep 12 monthly backups
  --yearly 3       # Keep 3 yearly backups

# Custom retention rules
aishell backup retention prod-db \
  --rules '[
    {"type": "full", "keep": 30, "unit": "days"},
    {"type": "incremental", "keep": 7, "unit": "days"},
    {"type": "differential", "keep": 14, "unit": "days"}
  ]'

# Apply retention policy
aishell backup cleanup prod-db \
  --apply-retention \
  --dry-run

# Manual cleanup
aishell backup cleanup prod-db \
  --older-than 30d \
  --type incremental
```

---

## Restoring from Backups

### Full Database Restore

#### PostgreSQL

```bash
# List available backups
aishell backup list prod-db

# Output:
# Name                      | Type | Size  | Date                | Location
# --------------------------|------|-------|---------------------|----------
# full-backup-20240115      | full | 4.2GB | 2024-01-15 02:00   | local
# full-backup-20240114      | full | 4.1GB | 2024-01-14 02:00   | s3
# incremental-20240115-1400 | incr | 50MB  | 2024-01-15 14:00   | local

# Restore full backup
aishell backup restore prod-db \
  --name full-backup-20240115 \
  --target restore-test-db

# Output:
# ✓ Preparing restore...
# ✓ Validating backup integrity
# ✓ Creating target database
# ✓ Restoring schema...
# ✓ Restoring data (4.2 GB)...
#   Progress: [████████████████████] 100% (7m 45s)
# ✓ Restoring indexes...
# ✓ Restoring constraints...
# ✓ Updating sequences...
# ✓ Analyzing tables...
# ✓ Restore completed successfully
# ✓ Duration: 8m 12s

# Restore with parallel processing
aishell backup restore prod-db \
  --name full-backup-20240115 \
  --target restore-test-db \
  --jobs 4

# Restore specific schemas
aishell backup restore prod-db \
  --name full-backup-20240115 \
  --target restore-test-db \
  --schema public,analytics

# Restore specific tables
aishell backup restore prod-db \
  --name full-backup-20240115 \
  --target restore-test-db \
  --table users,orders
```

#### MySQL

```bash
# Restore MySQL backup
aishell backup restore mysql-prod \
  --name mysql-backup-20240115 \
  --target mysql-restore-db

# Restore specific database
aishell backup restore mysql-prod \
  --name mysql-backup-20240115 \
  --target mysql-restore-db \
  --database ecommerce

# Restore to different host
aishell backup restore mysql-prod \
  --name mysql-backup-20240115 \
  --target-host mysql-new.example.com \
  --target-database restored_db
```

#### MongoDB

```bash
# Restore MongoDB backup
aishell backup restore mongo-prod \
  --name mongo-backup-20240115 \
  --target mongo-restore-db

# Restore specific database
aishell backup restore mongo-prod \
  --name mongo-backup-20240115 \
  --database analytics \
  --target mongo-restore-db

# Restore specific collection
aishell backup restore mongo-prod \
  --name mongo-backup-20240115 \
  --database myapp \
  --collection users \
  --target mongo-restore-db
```

#### Redis

```bash
# Restore Redis from RDB
aishell backup restore redis-prod \
  --name redis-backup-20240115 \
  --target redis-restore

# Restore with specific database number
aishell backup restore redis-prod \
  --name redis-backup-20240115 \
  --target redis-restore \
  --database 1
```

### Point-in-Time Recovery (PITR)

#### PostgreSQL PITR

```bash
# Restore to specific timestamp
aishell backup restore prod-db \
  --name full-backup-20240115 \
  --target pitr-restore-db \
  --point-in-time "2024-01-15 14:30:00"

# Configure PITR
aishell backup configure-pitr prod-db \
  --wal-archive ~/.aishell/wal_archive \
  --recovery-target-time "2024-01-15 14:30:00"

# Restore to specific transaction ID
aishell backup restore prod-db \
  --name full-backup-20240115 \
  --target pitr-restore-db \
  --recovery-target-xid 12345678

# Restore to named restore point
aishell backup restore prod-db \
  --name full-backup-20240115 \
  --target pitr-restore-db \
  --recovery-target-name "before_migration"
```

#### MySQL PITR

```bash
# Restore to specific binlog position
aishell backup restore mysql-prod \
  --name mysql-backup-20240115 \
  --target mysql-pitr-db \
  --binlog-file mysql-bin.000123 \
  --binlog-position 456789

# Restore to specific datetime
aishell backup restore mysql-prod \
  --name mysql-backup-20240115 \
  --target mysql-pitr-db \
  --stop-datetime "2024-01-15 14:30:00"
```

#### MongoDB PITR

```bash
# Restore using oplog
aishell backup restore mongo-prod \
  --name mongo-backup-20240115 \
  --target mongo-pitr-db \
  --oplog-replay \
  --oplog-limit "2024-01-15T14:30:00Z"
```

### Partial Restore

```bash
# Restore only schema
aishell backup restore prod-db \
  --name full-backup-20240115 \
  --target schema-restore-db \
  --schema-only

# Restore only data
aishell backup restore prod-db \
  --name full-backup-20240115 \
  --target data-restore-db \
  --data-only

# Restore with data transformation
aishell backup restore prod-db \
  --name full-backup-20240115 \
  --target transformed-db \
  --transform "
    UPDATE users SET email = CONCAT('test_', id, '@example.com');
    UPDATE users SET phone = NULL;
  "
```

---

## Cloud Backup Integration

### AWS S3

#### Configure S3 Integration

```bash
# Configure AWS credentials
aishell cloud configure aws \
  --access-key-id YOUR_ACCESS_KEY \
  --secret-access-key YOUR_SECRET_KEY \
  --region us-east-1

# Or use AWS CLI credentials
aishell cloud configure aws --use-aws-cli

# Configure S3 bucket
aishell cloud configure s3 \
  --bucket my-db-backups \
  --region us-east-1 \
  --storage-class STANDARD_IA \
  --encryption AES256
```

#### Upload to S3

```bash
# Upload backup to S3
aishell backup upload prod-db \
  --name full-backup-20240115 \
  --target s3://my-db-backups/prod-db/

# Upload with lifecycle policy
aishell backup upload prod-db \
  --name full-backup-20240115 \
  --target s3://my-db-backups/prod-db/ \
  --storage-class STANDARD_IA \
  --transition-to-glacier 30

# Upload with server-side encryption
aishell backup upload prod-db \
  --name full-backup-20240115 \
  --target s3://my-db-backups/prod-db/ \
  --encryption aws:kms \
  --kms-key-id arn:aws:kms:us-east-1:123456789:key/abc-123
```

#### Download from S3

```bash
# List S3 backups
aishell backup list-cloud prod-db \
  --provider s3 \
  --bucket my-db-backups

# Download from S3
aishell backup download prod-db \
  --source s3://my-db-backups/prod-db/full-backup-20240115 \
  --target ~/.aishell/backups/

# Restore directly from S3
aishell backup restore prod-db \
  --source s3://my-db-backups/prod-db/full-backup-20240115 \
  --target restore-db
```

### Azure Blob Storage

#### Configure Azure Integration

```bash
# Configure Azure credentials
aishell cloud configure azure \
  --account-name myaccount \
  --account-key YOUR_ACCOUNT_KEY

# Or use Azure CLI credentials
aishell cloud configure azure --use-azure-cli

# Configure blob container
aishell cloud configure azure-blob \
  --container db-backups \
  --storage-tier Cool
```

#### Upload to Azure

```bash
# Upload to Azure Blob
aishell backup upload prod-db \
  --name full-backup-20240115 \
  --target azure://db-backups/prod-db/

# Upload with access tier
aishell backup upload prod-db \
  --name full-backup-20240115 \
  --target azure://db-backups/prod-db/ \
  --access-tier Cool
```

### Google Cloud Storage (GCP)

#### Configure GCP Integration

```bash
# Configure GCP credentials
aishell cloud configure gcp \
  --project-id my-project \
  --credentials-file ~/.gcp/credentials.json

# Configure GCS bucket
aishell cloud configure gcs \
  --bucket my-db-backups \
  --location us-central1 \
  --storage-class NEARLINE
```

#### Upload to GCS

```bash
# Upload to GCS
aishell backup upload prod-db \
  --name full-backup-20240115 \
  --target gs://my-db-backups/prod-db/

# Upload with storage class
aishell backup upload prod-db \
  --name full-backup-20240115 \
  --target gs://my-db-backups/prod-db/ \
  --storage-class NEARLINE
```

### Multi-Cloud Backup

```bash
# Upload to multiple cloud providers
aishell backup upload prod-db \
  --name full-backup-20240115 \
  --target s3://aws-backups/prod-db/,azure://azure-backups/prod-db/,gs://gcp-backups/prod-db/ \
  --parallel

# Configure multi-cloud retention
aishell backup configure prod-db \
  --cloud-providers s3,azure,gcs \
  --primary s3 \
  --replicate-to azure,gcs \
  --retention-primary 30d \
  --retention-secondary 90d
```

---

## Backup Verification

### Integrity Checks

```bash
# Verify backup integrity
aishell backup verify prod-db \
  --name full-backup-20240115

# Output:
# ✓ Checking backup file...
# ✓ File size: 4.2 GB
# ✓ Checksum: VALID (SHA256)
# ✓ Compression: VALID (gzip)
# ✓ Header: VALID
# ✓ Database version: Compatible
# ✓ Backup is valid and restorable

# Verify with restore test
aishell backup verify prod-db \
  --name full-backup-20240115 \
  --restore-test \
  --target verify-db

# Deep verification
aishell backup verify prod-db \
  --name full-backup-20240115 \
  --deep-check \
  --sample-size 1000 \
  --check-constraints \
  --check-indexes
```

### Automated Verification

```bash
# Schedule verification
aishell backup schedule-verify prod-db \
  --schedule "0 6 * * *" \
  --verify-latest \
  --restore-test

# Verify all backups
aishell backup verify-all prod-db \
  --parallel \
  --report verification-report.json
```

### Comparison and Diff

```bash
# Compare backup with production
aishell backup compare prod-db \
  --backup full-backup-20240115 \
  --source prod-db

# Output:
# Comparing backup vs production...
# ✓ Schema: IDENTICAL
# ✓ Row counts: MATCH
# ✓ Sample data check: PASS
# ✓ Sequences: SYNCHRONIZED
# ⚠ Warning: Production has 234 newer rows in 'orders' table

# Diff two backups
aishell backup diff prod-db \
  --backup1 full-backup-20240115 \
  --backup2 full-backup-20240114

# Schema diff
aishell backup schema-diff prod-db \
  --backup1 full-backup-20240115 \
  --backup2 full-backup-20240114 \
  --output schema-changes.sql
```

---

## Disaster Recovery

### DR Planning

```bash
# Create disaster recovery plan
aishell dr plan-create prod-db \
  --name prod-dr-plan \
  --rto 4h \      # Recovery Time Objective
  --rpo 15m \     # Recovery Point Objective
  --backup-frequency 15m \
  --hot-standby enable \
  --failover-region us-west-2

# View DR plan
aishell dr plan-show prod-dr-plan
```

### DR Testing

```bash
# Test disaster recovery
aishell dr test prod-db \
  --plan prod-dr-plan \
  --dry-run

# Full DR drill
aishell dr drill prod-db \
  --plan prod-dr-plan \
  --target dr-test-db \
  --verify-data \
  --measure-rto \
  --measure-rpo \
  --report dr-drill-report.pdf

# Output:
# ✓ DR Drill Started
# ✓ Simulating disaster at: 2024-01-15 14:30:00
# ✓ Identifying latest backup: full-backup-20240115-1425
# ✓ Recovery Point: 5 minutes ago (RPO: 5m < 15m ✓)
# ✓ Starting restore...
# ✓ Restore completed in: 2h 15m (RTO: 2h 15m < 4h ✓)
# ✓ Verifying data integrity...
# ✓ Data verification: PASSED
# ✓ DR Drill: SUCCESSFUL
```

### Failover and Failback

```bash
# Initiate failover
aishell dr failover prod-db \
  --to dr-standby-db \
  --verify-replication \
  --update-dns

# Failback to primary
aishell dr failback dr-standby-db \
  --to prod-db \
  --sync-changes \
  --verify-data
```

### High Availability Setup

```bash
# Configure streaming replication (PostgreSQL)
aishell ha configure prod-db \
  --standby standby-db \
  --streaming-replication \
  --synchronous-commit on

# Configure master-slave replication (MySQL)
aishell ha configure mysql-prod \
  --slave mysql-slave-db \
  --semi-sync-replication

# Configure replica set (MongoDB)
aishell ha configure mongo-prod \
  --replica-set rs0 \
  --members mongo1,mongo2,mongo3

# Monitor replication lag
aishell ha monitor prod-db \
  --check-lag \
  --alert-threshold 10s
```

---

## Best Practices

### 1. Regular Testing

```bash
#!/bin/bash
# monthly-restore-test.sh

# Restore latest backup to test environment
LATEST_BACKUP=$(aishell backup list prod-db --latest --format json | jq -r '.name')

aishell backup restore prod-db \
  --name "$LATEST_BACKUP" \
  --target test-restore-db \
  --verify

# Run validation queries
aishell query run test-restore-db \
  --sql "SELECT COUNT(*) FROM users" \
  --compare-with prod-db

# Cleanup
aishell connection remove test-restore-db
```

### 2. Monitoring and Alerting

```bash
# Monitor backup status
aishell backup monitor prod-db \
  --check-last-backup \
  --alert-if-older-than 24h \
  --slack-webhook https://hooks.slack.com/...

# Track backup metrics
aishell backup metrics prod-db \
  --metric backup-size,backup-duration,compression-ratio \
  --period 30d \
  --export-prometheus
```

### 3. Documentation

```bash
# Generate backup documentation
aishell backup document prod-db \
  --output backup-documentation.md \
  --include-schedules \
  --include-retention \
  --include-cloud-config \
  --include-restore-procedures
```

### 4. Security

```bash
# Encrypt all backups
aishell config set backup.encryption.enabled true
aishell config set backup.encryption.algorithm AES-256-GCM

# Rotate encryption keys
aishell backup rotate-keys \
  --all-connections \
  --schedule quarterly

# Audit backup access
aishell backup audit \
  --show-access-logs \
  --period 90d
```

---

## Troubleshooting

### Common Issues

```bash
# Issue: Backup fails with "out of disk space"
# Solution: Check available space and cleanup old backups
aishell backup cleanup prod-db --older-than 30d

# Issue: Restore is very slow
# Solution: Use parallel restore
aishell backup restore prod-db --name backup --jobs 4

# Issue: Backup file is corrupted
# Solution: Verify backup and use previous backup
aishell backup verify prod-db --name backup
aishell backup list prod-db --sort-by date

# Issue: Cloud upload fails
# Solution: Check credentials and network
aishell cloud test aws
aishell backup upload prod-db --retry 3 --timeout 3600
```

---

## Next Steps

- Set up [Monitoring & Analytics](./MONITORING_ANALYTICS.md)
- Review [Security Best Practices](./SECURITY_BEST_PRACTICES.md)
- Configure [Integration Guide](./INTEGRATION_GUIDE.md)

---

*Last Updated: 2024-01-15 | Version: 1.0.0*
