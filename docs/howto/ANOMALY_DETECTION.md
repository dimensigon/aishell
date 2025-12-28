# How-To: Anomaly Detection & Self-Healing

## Quick Start

### Start Monitoring

```bash
# Start with auto-fix enabled (default)
aishell anomaly start

# Custom interval (default: 60s)
aishell anomaly start --interval 30

# Monitoring only (no auto-fix)
aishell anomaly start --no-auto-fix
```

### Check Status

```bash
# View current status
aishell anomaly status

# JSON output for scripting
aishell anomaly status --json-output
```

### Manual Check

```bash
# Run immediate check
aishell anomaly check
```

## What Gets Detected

### Resource Anomalies
- **CPU**: > 80% (high), > 95% (critical)
- **Memory**: > 80% (high), > 90% (critical)
- **Disk**: > 80% (high), > 95% (critical)

### Performance Anomalies
- Response time degradation
- Request rate anomalies
- Error rate spikes

### Pattern Anomalies
- Unusual command patterns
- Deviation from historical behavior
- Statistical outliers (>3 std deviations)

## Auto-Remediation Examples

### Memory Issues
```bash
# Detected: High memory usage (85%)
# Auto-fix: Clear system caches
$ sync && echo 3 > /proc/sys/vm/drop_caches
```

### Disk Space
```bash
# Detected: Disk usage 90%
# Auto-fix: Clean old temp files
$ find /tmp -type f -atime +7 -delete
```

### Zombie Processes
```bash
# Detected: High process count with zombies
# Auto-fix: Kill zombie processes
$ ps aux | grep defunct | awk '{print $2}' | xargs kill -9
```

## Use Cases

### 1. Production Monitoring

```bash
# Run in background
nohup aishell anomaly start --interval 60 &

# Check daily
aishell anomaly status | mail -s "Daily Report" admin@example.com
```

### 2. Development Environment

```bash
# Short interval for active development
aishell anomaly start --interval 10

# Get alerts for resource issues
aishell anomaly check >> /var/log/dev-monitoring.log
```

### 3. Integration with Alerts

```bash
# Create alert script
cat > ~/.aishell/alert.sh << 'EOF'
#!/bin/bash
STATUS=$(aishell anomaly status --json-output)
ANOMALIES=$(echo $STATUS | jq -r '.active_anomalies')

if [ "$ANOMALIES" -gt 0 ]; then
    echo "$STATUS" | mail -s "⚠️ Anomalies Detected" ops@example.com
fi
EOF

# Run hourly
crontab -e
# Add: 0 * * * * ~/.aishell/alert.sh
```

## Configuration

Create `~/.aishell/anomaly_config.yaml`:

```yaml
anomaly_detection:
  # Monitoring
  enabled: true
  interval: 60

  # Thresholds
  thresholds:
    cpu_usage:
      high: 80
      critical: 95
    memory_usage:
      high: 80
      critical: 90
    disk_usage:
      high: 80
      critical: 95

  # Auto-remediation
  auto_fix:
    enabled: true
    max_per_hour: 10
    risk_threshold: 0.3

  # Notifications
  notify:
    - type: email
      recipients: ["admin@example.com"]
      severity: ["HIGH", "CRITICAL"]
```

## Best Practices

1. **Start Conservative**: Begin with monitoring only
2. **Review Fixes**: Check remediation history regularly
3. **Set Limits**: Use rate limiting (default: 10/hour)
4. **Test Fixes**: Validate auto-fixes in dev first
5. **Monitor Logs**: Keep detailed logs of all actions

## Troubleshooting

```bash
# View remediation history
aishell anomaly status --json-output | jq '.recent_fixes'

# Check auto-fix rate limit
aishell anomaly status | grep "Fixes Remaining"

# Disable auto-fix temporarily
kill -USR1 $(pgrep -f "aishell anomaly")
```

---

**See also**: [Cognitive Memory](COGNITIVE_MEMORY.md) | [ADA](AUTONOMOUS_DEVOPS.md)