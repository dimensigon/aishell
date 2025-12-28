# Backup System - Quick Reference Card

## Essential Commands

```bash
# Create backup
aishell backup create --name "backup-name"

# List backups
aishell backup list

# Restore latest backup
aishell backup restore --latest

# Point-in-time recovery
aishell backup restore --point-in-time "2025-10-27 13:59:59"

# Test backup
aishell backup test --latest

# Configure backups
aishell backup configure
```

## Common Flags

| Flag | Description |
|------|-------------|
| `--name` | Backup name |
| `--latest` | Use latest backup |
| `--point-in-time` | Restore to specific timestamp |
| `--dry-run` | Test without applying |
| `--tables` | Backup specific tables |
| `--exclude-tables` | Exclude tables from backup |
| `--continuous` | Enable WAL streaming |

## Backup Strategies

```bash
# Conservative (daily full + hourly incremental)
aishell backup configure --strategy conservative

# Balanced (hourly full + 15-min incremental) ⭐
aishell backup configure --strategy balanced

# Aggressive (continuous + 5-min snapshots)
aishell backup configure --strategy aggressive
```

## Recovery Speed

| Type | Recovery Time | Data Loss |
|------|---------------|-----------|
| Full Backup | 10-15 minutes | Up to 24 hours |
| Incremental | 5-8 minutes | Up to 1 hour |
| Point-in-Time | 1-2 minutes | <1 minute |
| Continuous | 30-60 seconds | None |

## Pro Tips

1. **Enable WAL archiving** for zero data loss: `--wal-streaming`
2. **Test backups weekly** with `--auto-test`
3. **Use 3-2-1 rule**: 3 copies, 2 media, 1 offsite
4. **Compress backups** to save 70% storage
5. **Encrypt everything** with `--encryption aes-256`

## Emergency Recovery

```bash
# Disaster struck? Quick recovery
aishell emergency stop-writes
aishell backup restore --point-in-time "before-disaster"

# Verify recovery
aishell backup verify --last-restore

# Resume operations
aishell emergency resume-writes
```

## Typical Restore Flow

```
1. Safety backup created
2. Restore tested in sandbox ✓
3. Type 'YES' to confirm
4. Database restored (11m 47s)
5. Verification complete ✓
6. Database online ✓
```

## Storage Optimization

```bash
# Analyze backup storage
aishell backup analyze-storage

# Clean old backups
aishell backup cleanup --older-than 90d

# Optimize compression
aishell backup configure --compression zstd:3
```

## Backup Schedule Examples

```yaml
# Hourly backups, keep 48 hours
hourly:
  schedule: "0 * * * *"
  retention: 48h

# Daily backups, keep 30 days
daily:
  schedule: "0 2 * * *"
  retention: 30d

# Monthly backups, keep 1 year
monthly:
  schedule: "0 3 1 * *"
  retention: 365d
```

## Multi-Region Setup

```bash
# Configure multi-region backups
aishell backup configure \
  --primary s3://us-east-1/backups \
  --secondary s3://us-west-2/backups \
  --tertiary gcs://us-central1/backups
```

**Next:** [Query Federation Cheatsheet](./04-federation-cheatsheet.md)
