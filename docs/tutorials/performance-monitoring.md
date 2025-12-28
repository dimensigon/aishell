# Performance Monitoring Tutorial

> **📋 Implementation Status**
>
> **Current Status:** Planned
> **CLI Availability:** Coming Soon
> **Completeness:** 18%
>
> **What Works Now:**
> - Basic query execution
> - Manual performance observation
> - Database connection verification
>
> **Coming Soon:**
> - Real-time performance dashboard
> - Slow query detection and logging
> - Resource usage monitoring (CPU, memory, I/O)
> - Automated performance alerts
> - Query pattern analysis
> - Historical metrics tracking
> - Performance regression detection
>
> **Note:** This tutorial describes the intended functionality. Check the [Gap Analysis Report](../FEATURE_GAP_ANALYSIS_REPORT.md) for detailed implementation status.

## Table of Contents
- [Introduction](#introduction)
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Step-by-Step Instructions](#step-by-step-instructions)
- [Common Use Cases](#common-use-cases)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Introduction

Real-time performance monitoring is essential for maintaining healthy, high-performing databases. AI-Shell's performance monitoring system provides comprehensive visibility into your database operations, automatically detecting issues and providing actionable insights.

**What You'll Learn:**
- How to start and configure real-time monitoring
- Interpreting performance dashboards and metrics
- Detecting and fixing slow queries
- Setting up performance alerts
- Using anomaly detection for proactive monitoring

**Time to Complete:** 20-30 minutes

---

## Overview

AI-Shell's performance monitoring system provides:

- **Real-Time Query Tracking**: Monitor every query as it executes
- **Slow Query Detection**: Automatically identify performance bottlenecks
- **Resource Usage Monitoring**: Track CPU, memory, and connection pool usage
- **Anomaly Detection**: AI-powered detection of unusual patterns
- **Performance Alerts**: Get notified before problems become critical
- **Historical Analysis**: Analyze trends over time

### Key Benefits

| Feature | Benefit |
|---------|---------|
| Real-time dashboards | Instant visibility into database health |
| Automatic detection | Catch issues before they impact users |
| AI-powered insights | Get actionable recommendations |
| Zero configuration | Works out of the box |
| Low overhead | < 1% performance impact |

---

## Prerequisites

### Required

- AI-Shell installed and configured ([Installation Guide](../installation.md))
- At least one database connection configured
- Database user with monitoring privileges (e.g., `pg_stat_statements` for PostgreSQL)

### Optional

- Terminal with color support for better visualization
- Notification system (email/Slack) for alerts
- Grafana/Prometheus for advanced visualization

### Recommended Database Permissions

**PostgreSQL:**
```sql
-- Enable query statistics
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Grant monitoring permissions
GRANT pg_monitor TO ai_shell_user;
```

**MySQL:**
```sql
-- Enable performance schema
SET GLOBAL performance_schema = ON;

-- Grant monitoring permissions
GRANT PROCESS, SELECT ON performance_schema.* TO 'ai_shell_user'@'%';
```

---

## Getting Started

### Quick Start: First Monitoring Session

```bash
# Start real-time monitoring
ai-shell monitor start

# View the dashboard
ai-shell dashboard
```

You'll see output like:

```
📊 AI-Shell Performance Dashboard

Connection: postgres://localhost:5432/mydb
Status: ✓ Healthy (uptime: 42 days)

Query Performance (Last 5 minutes):
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total Queries:      1,234
  Avg Response Time:  23ms
  Slow Queries:       3 (0.2%)
  Errors:             0
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Top 3 Slowest Queries:
  1. SELECT * FROM orders WHERE status = 'pending'
     ⏱️  847ms | 🔄 23 calls | 💾 2.3MB scanned
     💡 Fix: CREATE INDEX idx_orders_status ON orders(status)

  2. SELECT COUNT(*) FROM users
     ⏱️  423ms | 🔄 156 calls | 💾 45MB scanned
     💡 Fix: Use approximate counts or add WHERE clause

  3. SELECT * FROM products ORDER BY created_at DESC
     ⏱️  234ms | 🔄 89 calls | 💾 12MB scanned
     💡 Fix: Add index on created_at column

Resource Usage:
  CPU:         42% ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░
  Memory:      1.2GB / 4.0GB (30%)
  Connections: 12 / 100 (12%)
  Cache Hit:   94.5%

Recent Alerts:
  ⚠️  High memory usage detected (85%) - 2 minutes ago
  ✓  Resolved: Connection pool exhaustion - 15 minutes ago

Next Steps:
  → Fix slow queries: ai-shell optimize-slow
  → View detailed metrics: ai-shell metrics detailed
  → Export report: ai-shell report export
```

---

## Step-by-Step Instructions

### Step 1: Enable Performance Monitoring

#### Basic Monitoring

```bash
# Start monitoring in the foreground
ai-shell monitor start

# Or run in the background
ai-shell monitor start --daemon
```

#### Configure Monitoring Settings

```bash
# Set monitoring interval (default: 5 seconds)
ai-shell config set monitor.interval 10s

# Enable detailed logging
ai-shell config set monitor.detail verbose

# Set slow query threshold
ai-shell config set monitor.slowQueryThreshold 100ms
```

### Step 2: View Real-Time Dashboard

```bash
# Interactive dashboard with auto-refresh
ai-shell dashboard

# Dashboard with specific refresh rate
ai-shell dashboard --refresh 2s

# Dashboard for specific database
ai-shell dashboard --database production
```

**Dashboard Sections:**

1. **Overview**: Connection status, uptime, health score
2. **Query Performance**: Response times, throughput, error rates
3. **Slow Queries**: Automatically detected performance issues
4. **Resource Usage**: CPU, memory, disk I/O, connections
5. **Recent Alerts**: Time-sensitive notifications

### Step 3: Analyze Slow Queries

```bash
# List all slow queries
ai-shell slow-queries

# Show detailed analysis
ai-shell slow-queries --detailed

# Filter by time period
ai-shell slow-queries --last 1h

# Show only fixable queries
ai-shell slow-queries --fixable
```

**Example Output:**

```
🐌 Slow Queries Detected

Query #1 (CRITICAL - 847ms avg)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SQL: SELECT * FROM orders WHERE status = 'pending'

Performance:
  Avg Time:      847ms
  Max Time:      2,340ms
  Calls:         23 (last hour)
  Scanned:       2.3MB per call
  Impact:        HIGH (19.5 seconds total)

Root Cause:
  ❌ Missing index on 'status' column
  ❌ Full table scan on 45,000 rows
  ⚠️  Returns unnecessary columns (SELECT *)

Recommended Fixes:
  1. CREATE INDEX idx_orders_status ON orders(status)
     Expected improvement: 89% faster (847ms → 93ms)

  2. SELECT id, customer_id, total FROM orders WHERE status = 'pending'
     Expected improvement: 67% reduction in data transfer

  3. Add LIMIT clause if pagination is possible
     Expected improvement: Up to 95% faster

Auto-fix Available:
  ai-shell optimize "SELECT * FROM orders WHERE status = 'pending'"
```

### Step 4: Fix Performance Issues

```bash
# Automatically fix a specific slow query
ai-shell optimize "SELECT * FROM orders WHERE status = 'pending'"

# Fix all slow queries (with confirmation)
ai-shell optimize-slow --auto-apply

# Preview fixes without applying
ai-shell optimize-slow --dry-run

# Fix queries above a certain threshold
ai-shell optimize-slow --threshold 500ms
```

**Auto-fix Process:**

```
🔧 Optimizing Slow Queries

Step 1: Analyzing query...
  ✓ Query parsed successfully
  ✓ Execution plan analyzed
  ✓ 3 optimization opportunities found

Step 2: Generating optimizations...
  ✓ Index recommendation: idx_orders_status
  ✓ Query rewrite: SELECT specific columns
  ✓ Add LIMIT for pagination

Step 3: Estimating impact...
  ✓ Expected speedup: 12.3x (847ms → 69ms)
  ✓ Index size: ~450KB
  ✓ Build time: ~2 seconds

Apply these changes? [y/N]: y

Step 4: Applying optimizations...
  ✓ Created index idx_orders_status
  ✓ Query rewritten in application cache
  ✓ Updated query documentation

Results:
  ✓ Optimization saved 778ms (91.8% faster)
  ✓ Expected annual savings: 4.2 hours
  ✓ 0 queries affected negatively

Monitoring for regressions...
```

### Step 5: Set Up Performance Alerts

```bash
# Configure alert thresholds
ai-shell alert config

# Add specific alert rules
ai-shell alert add --metric "response_time" --threshold 100ms --severity warning
ai-shell alert add --metric "error_rate" --threshold 5% --severity critical
ai-shell alert add --metric "connection_pool" --threshold 80% --severity warning

# Configure notification channels
ai-shell alert channel add email --to devops@example.com
ai-shell alert channel add slack --webhook https://hooks.slack.com/...
```

**Alert Configuration Example:**

```yaml
# ~/.ai-shell/alerts.yaml
alerts:
  - name: slow_queries
    condition: avg_response_time > 100ms
    duration: 5m
    severity: warning
    actions:
      - log
      - slack

  - name: high_error_rate
    condition: error_rate > 5%
    duration: 1m
    severity: critical
    actions:
      - log
      - email
      - auto_rollback

  - name: connection_exhaustion
    condition: connection_usage > 90%
    duration: 2m
    severity: critical
    actions:
      - log
      - email
      - scale_pool

notifications:
  email:
    to: devops@example.com
    from: alerts@ai-shell.dev

  slack:
    webhook: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
    channel: "#database-alerts"
```

### Step 6: Monitor Resource Usage

```bash
# View current resource usage
ai-shell resources

# Historical resource trends
ai-shell resources --history 24h

# Resource usage by query
ai-shell resources --by-query

# Export resource metrics
ai-shell resources --export csv
```

**Resource Monitoring Output:**

```
💻 Resource Usage Monitor

CPU Usage:
  Current:    42% ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░
  Avg (1h):   38%
  Peak (24h): 87% (at 2025-10-28 14:23:00)

  Top CPU Consumers:
    1. Query execution:     28%
    2. Index maintenance:   8%
    3. Connection handling: 6%

Memory Usage:
  Current:    1.2GB / 4.0GB (30%)
  Avg (1h):   1.1GB (28%)
  Peak (24h): 3.2GB (80%)

  Breakdown:
    Shared buffers:  512MB
    Work mem:        256MB
    Connections:     180MB
    Cache:           252MB

Connection Pool:
  Active:     12 ▓▓░░░░░░░░░░░░░░░░░░
  Idle:       8
  Max:        100
  Wait time:  0ms

  Longest queries:
    1. SELECT * FROM analytics - 34s (active)
    2. UPDATE users SET last_seen = NOW() - 2s
    3. DELETE FROM logs WHERE created_at < NOW() - 1s

Disk I/O:
  Read:   45 MB/s
  Write:  12 MB/s
  IOPS:   1,234

  Cache Performance:
    Hit rate:   94.5%
    Miss rate:  5.5%
    Evictions:  234/hour

Network:
  In:  23 MB/s
  Out: 67 MB/s
  Connections: 45 active
```

### Step 7: Analyze Query Patterns

```bash
# View query patterns and trends
ai-shell analyze patterns

# Find repeated inefficient queries
ai-shell analyze duplicates

# Identify N+1 query problems
ai-shell analyze n-plus-one

# Get optimization recommendations
ai-shell analyze recommend
```

---

## Common Use Cases

### Use Case 1: Daily Performance Health Check

**Scenario:** Start each day by checking database health

```bash
#!/bin/bash
# daily-health-check.sh

echo "🏥 Daily Database Health Check"
echo "================================"

# Overall health score
ai-shell health-check

# Recent performance trends
ai-shell metrics --last 24h --summary

# Check for new slow queries
ai-shell slow-queries --since yesterday

# Review alerts
ai-shell alerts list --last 24h

# Generate daily report
ai-shell report generate --period daily --export pdf
```

**Output:**

```
🏥 Daily Database Health Check
================================

Overall Health: ✓ EXCELLENT (97/100)

Key Metrics (Last 24h):
  ✓ Avg response time: 23ms (target: <50ms)
  ✓ Error rate: 0.01% (target: <1%)
  ⚠ Slow query count: 3 (target: 0)
  ✓ Uptime: 100%
  ✓ CPU usage: 42% avg

New Issues:
  ⚠ 3 new slow queries detected
  → ai-shell optimize-slow

Improvements:
  ✓ 12 queries optimized yesterday
  ✓ Avg speedup: 8.4x
  ✓ Time saved: 2.3 hours

Recommendations:
  → Consider adding index on users.email
  → Review analytics queries (high memory usage)
  → Connection pool usage trending up (plan capacity)

Report generated: /tmp/ai-shell-health-2025-10-28.pdf
```

### Use Case 2: Production Deployment Monitoring

**Scenario:** Monitor performance during and after deployment

```bash
# Pre-deployment baseline
ai-shell monitor snapshot --label "pre-deployment"

# Start monitoring with alerts
ai-shell monitor start --alert-mode strict

# Deploy application
# ... deployment process ...

# Compare performance post-deployment
ai-shell monitor compare pre-deployment

# Check for performance regressions
ai-shell analyze regression --since "30 minutes ago"
```

**Regression Detection:**

```
🔍 Performance Regression Analysis

Baseline: pre-deployment (2025-10-28 14:00:00)
Current:  2025-10-28 14:45:00

Overall: ⚠ REGRESSION DETECTED

Metrics Comparison:
  Response Time:
    Before: 23ms avg
    After:  156ms avg
    Change: ❌ +578% WORSE

  Throughput:
    Before: 1,234 qps
    After:  892 qps
    Change: ❌ -27.7% WORSE

  Error Rate:
    Before: 0.01%
    After:  0.01%
    Change: ✓ No change

Affected Queries (3):
  1. SELECT * FROM products WHERE category = ?
     Before: 12ms | After: 234ms | Change: +1850%
     Root cause: New code queries without index

  2. UPDATE orders SET status = ? WHERE id = ?
     Before: 5ms | After: 67ms | Change: +1240%
     Root cause: Lock contention from new workflow

  3. SELECT COUNT(*) FROM user_sessions
     Before: 89ms | After: 445ms | Change: +400%
     Root cause: Table size increased, no optimization

Recommendations:
  🚨 IMMEDIATE: Rollback or apply hotfix
  1. CREATE INDEX idx_products_category ON products(category)
  2. Optimize transaction isolation level for orders table
  3. Add approximate count function for user_sessions

Apply fixes automatically? [y/N]:
```

### Use Case 3: Peak Traffic Monitoring

**Scenario:** Monitor performance during high-traffic events (Black Friday, product launches)

```bash
# Predict required capacity
ai-shell analyze predict-load --event "black-friday" --multiplier 50x

# Pre-scale resources
ai-shell scale prepare --target-load 50x

# Start intensive monitoring
ai-shell monitor start --mode intensive --dashboard

# Enable auto-scaling
ai-shell scale auto --min-connections 20 --max-connections 200

# Real-time alerts
ai-shell alert enable --all --priority critical
```

**Load Prediction Output:**

```
📊 Load Prediction: Black Friday 2025

Historical Data:
  Last year peak: 52x baseline
  Duration: 6 hours
  Max concurrent queries: 12,450

Predicted Load:
  Expected peak: 50x baseline (12,000 qps)
  Start time: 2025-11-29 00:00:00 EST
  Duration: 8 hours
  Risk level: HIGH

Current Capacity:
  Max throughput: 1,800 qps
  ❌ Insufficient for predicted load

Required Changes:
  ✓ Connection pool: 20 → 150 connections
  ✓ Query cache: 1GB → 8GB
  ✓ Read replicas: 0 → 3 replicas
  ⚠ Add 12 indexes (1.2GB total)
  ⚠ Optimize 23 queries

Cost Impact:
  Current: $420/month
  Scaled: $1,240/month (event duration)
  Savings vs downtime: $18,000

Apply scaling plan? [y/N]:
```

### Use Case 4: Debugging Performance Issues

**Scenario:** Investigate sudden performance degradation

```bash
# Find when performance degraded
ai-shell analyze timeline --metric response_time

# Identify what changed
ai-shell analyze changes --since "2 hours ago"

# Trace specific slow query
ai-shell trace "SELECT * FROM orders WHERE status = 'pending'"

# Compare with historical baseline
ai-shell compare --baseline "last-week-avg"
```

**Performance Timeline:**

```
📈 Performance Timeline Analysis

Metric: Average Response Time
Period: Last 6 hours

Timeline:
  14:00 ━━━━━━━━━━━━━━━━━━━━ 23ms ✓
  14:30 ━━━━━━━━━━━━━━━━━━━━ 25ms ✓
  15:00 ━━━━━━━━━━━━━━━━━━━━ 28ms ✓
  15:30 ━━━━━━━━━━━━━━━━━━━━ 31ms ✓
  16:00 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 156ms ❌ SPIKE
  16:30 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 168ms ❌
  17:00 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 172ms ❌

⚠️ SPIKE DETECTED at 16:00:00

Changes at 15:58:00 (2 minutes before spike):
  1. Deployment: app-server v2.4.1
  2. Schema change: Added column 'metadata' to orders table
  3. Configuration: Updated connection pool size

Likely Root Causes:
  1. New queries in v2.4.1 without indexes (80% confidence)
  2. Schema change caused table locks (15% confidence)
  3. Connection pool misconfiguration (5% confidence)

Affected Queries:
  1. SELECT * FROM orders WHERE status = 'pending'
     New in v2.4.1 | Missing index on 'status'

  2. SELECT o.*, m.data FROM orders o JOIN metadata m
     New join on unindexed 'metadata' table

Recommended Actions:
  1. CREATE INDEX idx_orders_status ON orders(status)
  2. CREATE INDEX idx_metadata_order_id ON metadata(order_id)
  3. Consider rollback if business-critical

Apply fixes? [y/N]:
```

### Use Case 5: Long-Term Performance Trending

**Scenario:** Track performance trends over weeks/months for capacity planning

```bash
# Generate monthly performance report
ai-shell report generate --period monthly

# Export metrics for external analysis
ai-shell metrics export --format prometheus --since "30 days ago"

# Trend analysis
ai-shell analyze trends --metrics response_time,throughput,errors

# Capacity forecasting
ai-shell forecast capacity --horizon "6 months"
```

---

## Advanced Features

### Real-Time Query Profiling

Profile individual queries to understand performance bottlenecks:

```bash
# Profile a specific query
ai-shell profile "SELECT * FROM orders WHERE customer_id = 123"

# Output:
# Query Execution Profile
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Total Time: 847ms
#
# Breakdown:
#   Planning:        3ms  (0.4%)  ━
#   Execution:     844ms (99.6%)  ━━━━━━━━━━━━━━━━━━━━
#     - Seq Scan:  789ms (93.5%)  ━━━━━━━━━━━━━━━━━━
#     - Sort:       45ms  (5.3%)  ━━
#     - Filter:     10ms  (1.2%)  ━
#
# I/O Statistics:
#   Disk Reads:    245 blocks (1.9MB)
#   Cache Hits:     12 blocks (96KB)
#   Hit Rate:      4.7% (very low!)
#
# Recommendations:
#   1. Add index on customer_id (eliminates Seq Scan)
#   2. Increase shared_buffers for better caching
#   3. Consider partitioning orders table
```

### Explain Query Plans

```bash
# Explain a query execution plan
ai-shell explain "SELECT * FROM orders WHERE status = 'pending'"

# Explain with visual tree
ai-shell explain "SELECT * FROM orders WHERE status = 'pending'" --visual

# Compare execution plans
ai-shell explain compare \
  "SELECT * FROM orders WHERE status = 'pending'" \
  "SELECT id, total FROM orders WHERE status = 'pending'"
```

### Historical Metrics Export

```bash
# Export to Prometheus format
ai-shell metrics export --format prometheus > metrics.prom

# Export to JSON for custom analysis
ai-shell metrics export --format json --since "7 days ago" > metrics.json

# Export to CSV for Excel/Sheets
ai-shell metrics export --format csv --metrics response_time,throughput > metrics.csv

# Export to Grafana dashboard
ai-shell metrics export --format grafana --output dashboard.json
```

### Custom Monitoring Dashboards

Create custom monitoring views:

```yaml
# ~/.ai-shell/dashboards/custom.yaml
name: "Production Monitoring"
refresh: 5s

sections:
  - name: "Critical Metrics"
    metrics:
      - response_time_p99
      - error_rate
      - connection_pool_usage
    thresholds:
      response_time_p99: 100ms
      error_rate: 1%
      connection_pool_usage: 80%

  - name: "Business Metrics"
    queries:
      - name: "Orders per minute"
        sql: "SELECT COUNT(*) FROM orders WHERE created_at > NOW() - INTERVAL '1 minute'"
      - name: "Revenue per hour"
        sql: "SELECT SUM(total) FROM orders WHERE created_at > NOW() - INTERVAL '1 hour'"

  - name: "Top Queries"
    show:
      - slowest_queries: 5
      - most_frequent_queries: 5
      - most_expensive_queries: 5
```

Load custom dashboard:

```bash
ai-shell dashboard --config ~/.ai-shell/dashboards/custom.yaml
```

### Integration with External Tools

#### Grafana Integration

```bash
# Export metrics to Grafana
ai-shell integration grafana setup

# Configure data source
ai-shell integration grafana configure \
  --url http://grafana.example.com \
  --api-key YOUR_API_KEY

# Auto-import dashboards
ai-shell integration grafana import-dashboards
```

#### Prometheus Integration

```bash
# Start Prometheus exporter
ai-shell integration prometheus start --port 9090

# Configure scraping
ai-shell integration prometheus config > /etc/prometheus/ai-shell.yml
```

#### Datadog Integration

```bash
# Configure Datadog agent
ai-shell integration datadog setup --api-key YOUR_API_KEY

# Start sending metrics
ai-shell integration datadog start
```

---

## Troubleshooting

### Issue 1: Monitoring Not Starting

**Symptoms:**
```
Error: Failed to start monitoring
Cause: Insufficient database permissions
```

**Solution:**

```bash
# Check required permissions
ai-shell check-permissions

# Grant monitoring permissions (PostgreSQL)
psql -U postgres -c "GRANT pg_monitor TO ai_shell_user"

# Enable pg_stat_statements
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements"

# Restart monitoring
ai-shell monitor restart
```

### Issue 2: High Monitoring Overhead

**Symptoms:**
- Database performance degraded after enabling monitoring
- High CPU usage from monitoring process

**Solution:**

```bash
# Reduce monitoring frequency
ai-shell config set monitor.interval 30s

# Disable detailed logging
ai-shell config set monitor.detail basic

# Limit tracked queries
ai-shell config set monitor.maxTrackedQueries 100

# Use sampling instead of full tracking
ai-shell config set monitor.samplingRate 0.1  # Track 10% of queries
```

### Issue 3: Missing Slow Query Data

**Symptoms:**
- Slow queries not appearing in dashboard
- Empty slow query reports

**Solution:**

```bash
# Check slow query threshold
ai-shell config get monitor.slowQueryThreshold

# Lower threshold to capture more queries
ai-shell config set monitor.slowQueryThreshold 50ms

# Verify pg_stat_statements is enabled (PostgreSQL)
psql -c "SELECT * FROM pg_stat_statements LIMIT 1"

# Reset statistics and start fresh
ai-shell monitor reset
ai-shell monitor start
```

### Issue 4: Inaccurate Performance Metrics

**Symptoms:**
- Metrics don't match observed performance
- Inconsistent dashboard data

**Solution:**

```bash
# Clear cache
ai-shell cache clear

# Reset baseline metrics
ai-shell monitor calibrate

# Verify time synchronization
ai-shell system check-time

# Restart with verbose logging
ai-shell monitor start --verbose --log-level debug
```

### Issue 5: Alert Fatigue

**Symptoms:**
- Too many alerts
- Difficult to identify critical issues

**Solution:**

```bash
# Review and adjust alert thresholds
ai-shell alert list
ai-shell alert tune --auto  # Use AI to optimize thresholds

# Enable alert aggregation
ai-shell config set alerts.aggregation true
ai-shell config set alerts.aggregationWindow 5m

# Implement alert severity levels
ai-shell alert configure --critical-only-email true
ai-shell alert configure --warning-to-log true

# Add alert suppression during maintenance
ai-shell alert suppress --during "maintenance-window"
```

### Issue 6: Dashboard Performance Issues

**Symptoms:**
- Dashboard slow to load
- UI freezes or lags

**Solution:**

```bash
# Reduce dashboard refresh rate
ai-shell dashboard --refresh 10s  # Instead of default 2s

# Limit displayed data
ai-shell config set dashboard.maxQueries 10
ai-shell config set dashboard.historyWindow 1h

# Use terminal-optimized display
ai-shell dashboard --mode compact

# Export to file instead of live view
ai-shell dashboard snapshot > dashboard.txt
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Permission denied: pg_stat_statements` | Missing PostgreSQL extension | `CREATE EXTENSION pg_stat_statements` |
| `Monitoring overhead too high` | Tracking too many queries | Increase `monitor.interval` or enable sampling |
| `Connection pool exhausted` | Too many monitoring connections | Reduce monitoring frequency or increase pool size |
| `Alert delivery failed` | Invalid notification configuration | Check `ai-shell alert test` |
| `Metrics export failed` | Insufficient disk space | Clear old metrics: `ai-shell metrics prune` |

---

## Next Steps

### Recommended Learning Path

1. **Master the Basics** (Completed ✓)
   - You now understand performance monitoring fundamentals

2. **Explore Query Optimization** (Next: 30 mins)
   - [Query Optimization Tutorial](./query-optimization.md)
   - Learn to automatically fix slow queries

3. **Set Up Anomaly Detection** (Next: 20 mins)
   - [Anomaly Detection Tutorial](./anomaly-detection.md)
   - Enable AI-powered proactive monitoring

4. **Implement Autonomous Operations** (Next: 45 mins)
   - [Autonomous DevOps Tutorial](./autonomous-devops.md)
   - Let AI-Shell automatically optimize your infrastructure

### Related Documentation

- [Query Optimization Guide](./query-optimization.md)
- [Anomaly Detection Tutorial](./anomaly-detection.md)
- [Security Best Practices](./security.md)
- [Database Federation](./database-federation.md)

### Advanced Topics

- **Custom Metrics**: [Building Custom Metrics](../advanced/custom-metrics.md)
- **Integration APIs**: [Monitoring API Reference](../api/monitoring.md)
- **Enterprise Features**: [Enterprise Monitoring](../enterprise/monitoring.md)

### Community Resources

- **Examples**: [Real-world monitoring setups](https://github.com/your-org/ai-shell-examples)
- **Discussion**: [Performance optimization tips](https://github.com/your-org/ai-shell/discussions)
- **Support**: [Get help with monitoring](https://discord.gg/ai-shell)

---

## Feedback

Help us improve this tutorial:
- [Report an issue](https://github.com/your-org/ai-shell/issues/new?template=tutorial-feedback)
- [Suggest improvements](https://github.com/your-org/ai-shell/discussions/new)
- [Share your success story](https://twitter.com/aishell_dev)

---

**Last Updated:** 2025-10-28
**Version:** 1.0.0
**Difficulty:** Intermediate
