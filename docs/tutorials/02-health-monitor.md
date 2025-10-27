# Health Monitor Tutorial: Never Miss a Database Incident

## Real-World Scenario

**Problem**: Your production database crashed at 3 AM due to a connection leak. By the time your team woke up, you'd lost $50,000 in revenue and your database was corrupted.

**Solution**: AI-Shell's Health Monitor provides 24/7 intelligent monitoring with predictive alerts and automatic recovery.

---

## Table of Contents

1. [Setup](#setup)
2. [Basic Monitoring](#basic-monitoring)
3. [Real-World Example](#real-world-example)
4. [Advanced Patterns](#advanced-patterns)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Setup

### Quick Start

```bash
# Install AI-Shell
npm install -g @aishell/cli

# Initialize health monitoring
aishell health init

# Start monitoring
aishell health monitor --mode continuous
```

### Configuration

```bash
# Create monitoring configuration
aishell health configure
```

**Interactive Setup:**

```
🏥 Health Monitor Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What would you like to monitor?

✓ Database connections (pool size, wait time)
✓ Query performance (slow query detection)
✓ Resource usage (CPU, memory, disk I/O)
✓ Replication lag
✓ Table bloat
✓ Lock contention
✓ Cache hit ratio
✓ Connection leaks

How should I alert you?

[1] Slack
[2] Email
[3] PagerDuty
[4] Webhook
[5] All of the above

> Choice: 5

Alert thresholds:

CPU usage: > 80% for > 5 minutes
Memory usage: > 85% for > 3 minutes
Slow queries: > 5 seconds
Connection pool: > 90% full
Replication lag: > 10 seconds

✅ Configuration saved to ~/.aishell/health-config.yaml
```

---

## Basic Monitoring

### Step 1: Start Health Monitoring

```bash
# Basic health check
aishell health check
```

**Expected Output:**

```
🏥 Database Health Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated: 2025-10-27 14:32:15 UTC

Overall Status: ⚠️  WARNING

┌─────────────────────────────────────────────────────┐
│ Critical Issues                                     │
├─────────────────────────────────────────────────────┤
│ ⚠️  Connection pool at 87% capacity                │
│    Current: 87/100 connections                      │
│    Trend: ↗️  Increasing (12% in last hour)        │
│    Impact: Queries may start queueing               │
│    Action: Consider increasing pool size to 150     │
│                                                     │
│ ⚠️  Slow query detected                            │
│    Query: SELECT * FROM orders WHERE...             │
│    Duration: 8,234ms (threshold: 5,000ms)          │
│    Frequency: 45 times/hour                         │
│    Action: Run optimizer (see recommendation)       │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ System Metrics                                      │
├─────────────────────────────────────────────────────┤
│ CPU Usage:        78% ████████████████░░░░          │
│ Memory Usage:     72% ██████████████░░░░░░          │
│ Disk I/O:         34% ███████░░░░░░░░░░░░░          │
│ Network:          12% ███░░░░░░░░░░░░░░░░░          │
│ Cache Hit Ratio:  94% ███████████████████░          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Database Performance                                │
├─────────────────────────────────────────────────────┤
│ Active Connections:    87                           │
│ Queries/Second:       342                           │
│ Avg Query Time:       23ms                          │
│ Slowest Query:     8,234ms                          │
│ Deadlocks:             2 (last hour)                │
│ Replication Lag:       0.3s ✓                       │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ AI Recommendations                                  │
├─────────────────────────────────────────────────────┤
│ 1. 🔧 Increase connection pool to 150               │
│    Command: aishell health tune --connection-pool   │
│                                                     │
│ 2. ⚡ Optimize slow query on orders table           │
│    Command: aishell optimize "SELECT * FROM..."    │
│                                                     │
│ 3. 📊 Enable query caching for repeated queries     │
│    Command: aishell cache enable --ttl 300          │
│                                                     │
│ 4. 🔍 Investigate deadlock pattern                  │
│    Command: aishell health analyze --deadlocks     │
└─────────────────────────────────────────────────────┘

Next check in: 60 seconds
Run 'aishell health fix --auto' to apply fixes automatically
```

### Step 2: Continuous Monitoring

```bash
# Start continuous monitoring with dashboard
aishell health monitor --dashboard
```

**Live Dashboard:**

```
╔═══════════════════════════════════════════════════════════════════╗
║                   AI-Shell Health Monitor                         ║
║                     Live Dashboard                                ║
╚═══════════════════════════════════════════════════════════════════╝

  Status: ✅ HEALTHY          Uptime: 45 days 3 hours 12 mins

  ┌─────────────────────── Real-Time Metrics ───────────────────────┐
  │                                                                  │
  │  Queries/sec:  342 ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁ (last 60s)                  │
  │  CPU:          78% ████████████████░░░░ [↗️ +3%]                │
  │  Memory:       72% ██████████████░░░░░░ [→ stable]              │
  │  Connections:  87  ████████████████████░ [↗️ +12]               │
  │  Avg Latency:  23ms ▁▁▂▂▃▃▄▄▅▅▆▆▇▇█ [↗️ +8ms]                  │
  │                                                                  │
  └──────────────────────────────────────────────────────────────────┘

  ┌─────────────────────── Active Alerts ───────────────────────────┐
  │                                                                  │
  │  14:32:15  ⚠️  [WARNING] Connection pool high (87%)             │
  │  14:28:42  ⚠️  [WARNING] Slow query detected (8.2s)             │
  │  14:15:03  ⚠️  [WARNING] Memory usage increasing                │
  │  13:45:12  ✅ [RESOLVED] Replication lag back to normal         │
  │                                                                  │
  └──────────────────────────────────────────────────────────────────┘

  ┌─────────────────────── Top Queries ─────────────────────────────┐
  │                                                                  │
  │  1. SELECT * FROM orders WHERE...        8,234ms  [45x/hour]    │
  │  2. UPDATE users SET last_seen...          234ms  [2,340x/hr]   │
  │  3. INSERT INTO events VALUES...           12ms   [890x/hour]   │
  │                                                                  │
  └──────────────────────────────────────────────────────────────────┘

  ┌─────────────────────── AI Insights ─────────────────────────────┐
  │                                                                  │
  │  🤖 Detected anomaly: Query volume increased 34% since 14:00    │
  │     Normal for this time? [Traffic spike typical on Mon 2pm]    │
  │                                                                  │
  │  💡 Prediction: Connection pool will reach capacity in ~45min   │
  │     Recommend: Preemptively scale pool or optimize slow query   │
  │                                                                  │
  │  📊 Pattern detected: Slow query correlates with high memory    │
  │     Root cause: Query loading too much data into memory         │
  │     Fix available: Add pagination (auto-apply? y/n)             │
  │                                                                  │
  └──────────────────────────────────────────────────────────────────┘

  Press 'q' to quit | 'f' to auto-fix | 'r' to refresh | 'a' for alerts
```

### Step 3: Set Up Alerts

```bash
# Configure alerting
aishell health alert configure
```

**Alert Configuration:**

```yaml
# ~/.aishell/alerts.yaml

alerts:
  # Critical alerts (immediate notification)
  critical:
    - name: database_down
      condition: "connection.status == 'disconnected'"
      channels: [slack, pagerduty, phone]

    - name: high_error_rate
      condition: "errors_per_minute > 100"
      channels: [slack, pagerduty]

    - name: disk_full
      condition: "disk.free_space_percent < 10"
      channels: [slack, pagerduty, email]

  # Warning alerts (can wait a few minutes)
  warning:
    - name: high_cpu
      condition: "cpu.usage > 80 for 5 minutes"
      channels: [slack]

    - name: connection_pool_high
      condition: "connections.used_percent > 90"
      channels: [slack]

    - name: slow_query
      condition: "query.duration > 5000ms"
      channels: [slack]
      auto_optimize: true  # AI will auto-optimize!

  # Info alerts (FYI, no urgent action)
  info:
    - name: traffic_spike
      condition: "qps > baseline * 1.5"
      channels: [slack]

    - name: replication_lag
      condition: "replication.lag > 10s"
      channels: [slack]

# Alert routing
channels:
  slack:
    webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK
    channel: "#database-alerts"

  pagerduty:
    integration_key: YOUR_KEY
    severity_mapping:
      critical: "critical"
      warning: "warning"
      info: "info"

  email:
    recipients: [dba@yourcompany.com, oncall@yourcompany.com]

  phone:
    numbers: ["+1-555-123-4567"]  # Only for critical!
```

---

## Real-World Example: Preventing a Production Outage

### Scenario

It's Friday at 5 PM. You're about to leave for the weekend when AI-Shell detects an anomaly.

### Detection

```bash
# AI-Shell's continuous monitoring detects pattern
```

**Alert Received:**

```
🚨 CRITICAL ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Time: 2025-10-27 17:03:42
Severity: HIGH (will become CRITICAL in ~23 minutes)

Issue: Connection Leak Detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AI Analysis:
- Connection pool growing abnormally fast
- Current: 142/150 connections (94%)
- Growth rate: +3 connections/minute
- Projection: Pool exhausted at 17:26:42 (23 mins)

Root Cause Identified:
┌─────────────────────────────────────────────────────┐
│ Application code not closing connections properly   │
│                                                     │
│ File: api/controllers/UserController.js:145        │
│ Issue: Missing await on db.release()               │
│                                                     │
│ 15 leaked connections in last hour                  │
│ Memory leak: ~45MB/hour                             │
└─────────────────────────────────────────────────────┘

Impact Analysis:
- If not fixed: Complete outage in 23 minutes
- Affected users: All API users (~50,000 active)
- Est. revenue loss: $12,000/hour
- Database recovery time: 15-30 minutes

Recommended Actions:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Immediate (Do Now):
[1] 🔴 Apply temporary fix (increase pool to 300)
    Command: aishell health fix --connection-pool --temporary

[2] 🟡 Force close idle connections older than 5 minutes
    Command: aishell health cleanup --idle-connections

[3] 🟢 Deploy code fix (PR already created)
    Command: git pull && npm run deploy

Long-term (This Sprint):
- Add connection monitoring to application code
- Implement connection pooling best practices
- Set up automated leak detection

Auto-fix available. Apply? (y/n): _
```

### Response

```bash
# Accept AI's auto-fix
y
```

**Auto-Fix Execution:**

```
🤖 Executing Auto-Fix...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Increase connection pool (temporary)
  ✓ Pool size: 150 → 300 (1.2s)
  ✓ Validated configuration
  ✓ Restarted connection manager
  Result: ✅ Immediate pressure relief

Step 2: Clean up leaked connections
  ✓ Identified 15 leaked connections
  ✓ Gracefully closed 15 connections (3.4s)
  ✓ Freed 45MB memory
  Result: ✅ Pool back to healthy levels

Step 3: Analyze code and create PR
  ✓ Scanned codebase for connection leak patterns
  ✓ Found 3 instances of missing db.release()
  ✓ Generated fix for all instances
  ✓ Created PR #847 with automated tests
  Result: ✅ PR ready for review

Step 4: Deploy monitoring safeguards
  ✓ Added connection leak detector
  ✓ Set up automated alerts
  ✓ Configured auto-cleanup for future leaks
  Result: ✅ Won't happen again

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Crisis Averted!

Timeline:
- Detection: 17:03:42
- Alert sent: 17:03:45
- Fix applied: 17:04:12
- Total time: 30 seconds

Impact:
- Prevented outage: ✅
- Revenue saved: $12,000
- Users affected: 0
- Downtime: 0 seconds

Next Steps:
1. Review and merge PR #847
2. Monitor for 24 hours to ensure stability
3. Consider implementing connection pooling best practices

Have a great weekend! 🎉
```

---

## Advanced Patterns

### Pattern 1: Predictive Monitoring

AI-Shell learns your database patterns and predicts issues before they happen.

```bash
# Enable predictive monitoring
aishell health monitor --predictive --train-days 30
```

**Predictive Alerts:**

```
🔮 Predictive Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Based on 30 days of historical data:

┌─────────────────────────────────────────────────────┐
│ Predictions for Next 24 Hours                       │
├─────────────────────────────────────────────────────┤
│ 18:00-20:00  High traffic spike expected (87%)     │
│              Recommend: Scale up 30 minutes early   │
│              Action: Auto-scaling enabled ✓         │
│                                                     │
│ 22:00-23:00  Backup window may cause slow queries  │
│              Recommend: Shift backup to 01:00       │
│              Action: Schedule updated ✓             │
│                                                     │
│ 02:00-03:00  Maintenance window                    │
│              Impact: 0 users (safe window)          │
│              Action: Auto-vacuum scheduled ✓        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Anomaly Detection                                   │
├─────────────────────────────────────────────────────┤
│ 🔍 Current query pattern differs from baseline      │
│    Detected: 15:30                                  │
│    Confidence: 94%                                  │
│    Pattern: Unusual spike in DELETE operations      │
│                                                     │
│    💡 Analysis:                                     │
│    - Normal DELETE rate: ~50/hour                  │
│    - Current rate: 2,340/hour (46.8x higher!)      │
│    - Started: 15:28:42                              │
│    - Source: api-server-3                           │
│                                                     │
│    ⚠️  Possible Issues:                             │
│    - Bug in cleanup job?                            │
│    - Data breach attempt?                           │
│    - Misconfigured script?                          │
│                                                     │
│    🛡️  Protection Enabled:                          │
│    - Rate limited DELETE operations to 100/min      │
│    - Notified security team                         │
│    - Logged all DELETE queries for audit            │
└─────────────────────────────────────────────────────┘
```

### Pattern 2: Multi-Database Monitoring

Monitor multiple databases from one dashboard:

```bash
# Add databases to monitoring
aishell health add-database prod-postgres-1
aishell health add-database prod-mysql-1
aishell health add-database analytics-mongodb

# Monitor all
aishell health monitor --all --dashboard
```

**Multi-DB Dashboard:**

```
╔═══════════════════════════════════════════════════════════════════╗
║              Multi-Database Health Dashboard                      ║
╚═══════════════════════════════════════════════════════════════════╝

┌──────────────────── prod-postgres-1 ✅ HEALTHY ────────────────────┐
│ QPS: 342  CPU: 78%  Memory: 72%  Connections: 87/150              │
│ Latency: 23ms  Cache Hit: 94%  Replication Lag: 0.3s              │
└────────────────────────────────────────────────────────────────────┘

┌──────────────────── prod-mysql-1 ⚠️  WARNING ──────────────────────┐
│ QPS: 156  CPU: 92%  Memory: 88%  Connections: 142/150             │
│ Latency: 89ms  Cache Hit: 76%  Replication Lag: 2.3s ⚠️           │
│ Alert: High CPU + replication lag                                  │
└────────────────────────────────────────────────────────────────────┘

┌──────────────── analytics-mongodb ✅ HEALTHY ──────────────────────┐
│ QPS: 89  CPU: 45%  Memory: 62%  Connections: 34/100               │
│ Latency: 12ms  Cache Hit: 88%  Replication Lag: N/A               │
└────────────────────────────────────────────────────────────────────┘

┌─────────────────────── Aggregate Stats ───────────────────────────┐
│ Total QPS: 587          Avg Latency: 41ms                         │
│ Alerts: 1 warning       Incidents Today: 0                        │
│ AI Health Score: 87/100 (Good)                                    │
└────────────────────────────────────────────────────────────────────┘

🤖 AI Recommendation: prod-mysql-1 needs attention
   Run: aishell health diagnose prod-mysql-1 --detailed
```

### Pattern 3: Custom Health Checks

Define your own health checks:

```bash
# Create custom check
aishell health create-check business-metrics.yaml
```

**Custom Check Configuration:**

```yaml
# business-metrics.yaml

name: "Business Critical Metrics"
interval: 60  # seconds

checks:
  - name: "Orders per minute"
    query: "SELECT COUNT(*) FROM orders WHERE created_at > NOW() - INTERVAL '1 minute'"
    threshold:
      min: 10   # Alert if < 10 orders/min
      max: 1000 # Alert if > 1000 orders/min (unusual spike)
    severity: critical

  - name: "Payment success rate"
    query: |
      SELECT
        (COUNT(*) FILTER (WHERE status = 'success'))::float / COUNT(*) * 100
      FROM payments
      WHERE created_at > NOW() - INTERVAL '5 minutes'
    threshold:
      min: 95  # Alert if success rate < 95%
    severity: critical

  - name: "Average cart value"
    query: "SELECT AVG(total) FROM carts WHERE status = 'active'"
    threshold:
      min: 50   # Alert if average cart < $50 (business concern)
    severity: warning

  - name: "API response time"
    query: "SELECT AVG(response_time_ms) FROM api_logs WHERE timestamp > NOW() - INTERVAL '5 minutes'"
    threshold:
      max: 500  # Alert if avg > 500ms
    severity: warning

actions:
  critical:
    - notify: [slack, pagerduty]
    - execute: "aishell health diagnose --auto-fix"

  warning:
    - notify: [slack]
    - execute: "aishell health analyze"
```

### Pattern 4: Integration with CI/CD

```bash
# Run health check in CI/CD pipeline
aishell health check --ci-mode --fail-on-warning

# Example GitHub Actions workflow
```

```yaml
# .github/workflows/database-health.yml

name: Database Health Check

on:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes
  push:
    branches: [main]

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Run AI-Shell Health Check
        run: |
          npm install -g @aishell/cli
          aishell health check --ci-mode --detailed

      - name: Upload Health Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: health-report
          path: health-report.json

      - name: Notify on Failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚨 Database health check failed!",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Database Health Check Failed*\n\nRun: ${{ github.run_id }}\nCommit: ${{ github.sha }}"
                  }
                }
              ]
            }
```

---

## Best Practices

### 1. Layer Your Monitoring

```bash
# Layer 1: Basic health (every 60s)
aishell health monitor --basic --interval 60

# Layer 2: Detailed metrics (every 300s)
aishell health monitor --detailed --interval 300

# Layer 3: Deep analysis (hourly)
aishell health analyze --deep --schedule "0 * * * *"
```

### 2. Tune Alert Thresholds

```bash
# Start conservative
aishell health alert set-threshold cpu_usage=90

# Adjust based on false positives
aishell health alert analyze-false-positives

# AI learns optimal thresholds
aishell health alert tune --auto-learn
```

### 3. Create Runbooks

```bash
# Generate runbook from alerts
aishell health runbook generate

# Example output: runbook-connection-leak.md
```

### 4. Test Your Monitoring

```bash
# Simulate failures to test alerts
aishell health test-alert connection_leak
aishell health test-alert high_cpu
aishell health test-alert disk_full

# Verify alert delivery
aishell health test-channels --all
```

### 5. Regular Health Reviews

```bash
# Weekly health report
aishell health report --weekly --email team@company.com

# Monthly trend analysis
aishell health analyze --monthly --export report.pdf
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Alert Fatigue

**Problem:** Too many alerts, team starts ignoring them

**Solution:**

```bash
# Analyze alert patterns
aishell health alert analyze --period 30days

Output:
┌─────────────────────────────────────────────────────┐
│ Alert Analysis (Last 30 Days)                      │
├─────────────────────────────────────────────────────┤
│ Total alerts: 2,340                                 │
│ False positives: 1,876 (80%!) 🚨                   │
│                                                     │
│ Top noisy alerts:                                   │
│ 1. high_cpu: 892 alerts (mostly false)             │
│    Recommendation: Increase threshold 80% → 90%     │
│                                                     │
│ 2. slow_query: 456 alerts (expected during backup)  │
│    Recommendation: Suppress during backup window    │
│                                                     │
│ 3. connection_pool: 234 alerts (normal spikes)      │
│    Recommendation: Use rate-of-change threshold     │
└─────────────────────────────────────────────────────┘

# Auto-tune thresholds
aishell health alert tune --reduce-noise --target-rate 5/day
```

### Pitfall 2: Missing Critical Alerts

**Problem:** Real issue buried in noise

**Solution:**

```bash
# Implement alert prioritization
aishell health alert prioritize --mode smart

# AI learns what's actually critical
aishell health alert train --historical-incidents incidents.json
```

### Pitfall 3: Monitoring Overhead

**Problem:** Monitoring itself impacts performance

**Solution:**

```bash
# Measure monitoring overhead
aishell health meta-monitor

# Optimize monitoring queries
aishell health optimize-monitoring --target-overhead 1%
```

---

## Troubleshooting

### Issue 1: "Health check timing out"

```bash
# Increase timeout
aishell health check --timeout 30s

# Or use async mode
aishell health check --async --notify-on-complete
```

### Issue 2: "Alerts not being delivered"

```bash
# Test alert delivery
aishell health test-alert connection_leak --channel slack

# Check configuration
aishell health alert validate-config

# View alert logs
aishell health alert logs --last 24h
```

### Issue 3: "False positives during deployments"

```bash
# Create maintenance window
aishell health maintenance start --duration 30m

# Auto-detect deployments
aishell health configure --suppress-during-deployment
```

---

## Summary

**Key Takeaways:**

- ✅ 24/7 intelligent monitoring with predictive alerts
- ✅ Automatic issue detection and resolution
- ✅ Multi-database support from one dashboard
- ✅ Custom health checks for business metrics
- ✅ Integration with existing alerting systems

**Next Steps:**

1. Try the [Backup System Tutorial](./03-backup-system.md) for disaster recovery
2. Learn about [Query Optimizer](./01-ai-query-optimizer.md) for performance
3. Explore [Cost Optimizer](./10-cost-optimizer.md) for savings

**Real Results:**

> "AI-Shell detected and fixed a connection leak before it caused an outage. Saved us $50K and countless hours of debugging." - Mike Rodriguez, DevOps Lead

---

## Quick Commands Cheat Sheet

```bash
# Basic health check
aishell health check

# Start continuous monitoring
aishell health monitor --dashboard

# Configure alerts
aishell health alert configure

# Auto-fix issues
aishell health fix --auto

# Analyze incidents
aishell health analyze --detailed

# Generate reports
aishell health report --weekly

# Test monitoring
aishell health test-alert --all
```

**Pro Tip:** Enable predictive monitoring to catch issues before they impact users! 🔮
