# Health Monitor - Quick Reference Card

## Essential Commands

```bash
# Basic health check
aishell health check

# Start monitoring dashboard
aishell health monitor --dashboard

# Configure alerts
aishell health alert configure

# Auto-fix issues
aishell health fix --auto

# Analyze issues
aishell health analyze --detailed

# Generate reports
aishell health report --weekly
```

## Common Flags

| Flag | Description |
|------|-------------|
| `--dashboard` | Show live monitoring dashboard |
| `--predictive` | Enable predictive alerts |
| `--auto-fix` | Automatically fix detected issues |
| `--detailed` | Detailed health analysis |
| `--ci-mode` | CI/CD integration mode |
| `--fail-on-warning` | Exit with error on warnings |

## Alert Severity Levels

| Level | Response Time | Channels |
|-------|---------------|----------|
| 🚨 **Critical** | Immediate | Slack, PagerDuty, Phone |
| ⚠️ **Warning** | 5 minutes | Slack |
| ℹ️ **Info** | No action | Slack (weekly summary) |

## Typical Dashboard

```
✅ HEALTHY | Uptime: 45 days 3 hours 12 mins

QPS: 342 ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁
CPU: 78% ████████████████░░░░
Memory: 72% ██████████████░░░░░░
Connections: 87/150

🤖 AI: Detected anomaly at 15:30
   Query volume increased 34% since 14:00
```

## Pro Tips

1. **Enable predictive monitoring** for early warnings
2. **Create custom health checks** for business metrics
3. **Test alerts regularly** with `aishell health test-alert`
4. **Use maintenance windows** during deployments
5. **Tune alert thresholds** with `--auto-learn`

## Common Issues & Fixes

```bash
# Connection pool exhausted
aishell health tune --connection-pool

# Slow query detected
aishell optimize "slow query"

# Memory usage high
aishell health cleanup --memory

# Disk space low
aishell health cleanup --disk

# Replication lag
aishell health sync --force
```

## Emergency Procedures

```bash
# Database unresponsive
aishell emergency diagnose

# Stop all writes
aishell emergency stop-writes

# Force connection cleanup
aishell emergency kill-connections

# Emergency restart
aishell emergency restart --safe
```

## Integration

```yaml
# GitHub Actions
- name: Health Check
  run: aishell health check --ci-mode

# Cron job
0 * * * * aishell health check --quiet || alert-oncall.sh
```

**Next:** [Backup System Cheatsheet](./03-backup-cheatsheet.md)
