# Monitoring and Analytics Guide

## Table of Contents

1. [Overview](#overview)
2. [Health Checks](#health-checks)
3. [Real-Time Monitoring](#real-time-monitoring)
4. [Setting Up Alerts](#setting-up-alerts)
5. [Performance Analysis](#performance-analysis)
6. [Dashboard Usage](#dashboard-usage)
7. [Grafana Integration](#grafana-integration)
8. [Prometheus Integration](#prometheus-integration)

---

## Overview

Comprehensive monitoring is essential for maintaining database health, performance, and availability. AI-Shell provides real-time monitoring, alerting, and analytics capabilities for all supported databases.

### Monitoring Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Monitoring Architecture                     │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
          ┌───────────────────────────────────────┐
          │        AI-Shell Monitoring Core        │
          │  ┌─────────────────────────────────┐  │
          │  │   Metric Collection Engine      │  │
          │  │   - Database Metrics            │  │
          │  │   - System Metrics              │  │
          │  │   - Query Performance           │  │
          │  │   - Connection Pool Stats       │  │
          │  └─────────────────────────────────┘  │
          └───────┬────────────────┬───────────────┘
                  │                │
         ┌────────▼────────┐  ┌───▼──────────────┐
         │  Storage Layer  │  │  Alert Engine    │
         │  - Time Series  │  │  - Rule Engine   │
         │  - Aggregation  │  │  - Notifications │
         │  - Retention    │  │  - Escalation    │
         └────────┬────────┘  └──────────────────┘
                  │
         ┌────────▼────────────────────────────┐
         │        Visualization Layer          │
         │  - CLI Dashboard                    │
         │  - Web Dashboard                    │
         │  - Grafana                          │
         │  - Prometheus                       │
         └─────────────────────────────────────┘
```

### Monitoring Metrics

| Category | Metrics | Update Frequency |
|----------|---------|------------------|
| **Database** | Connections, transactions, locks, replication lag | 1-60s |
| **Performance** | Query time, throughput, cache hit ratio | 1-60s |
| **System** | CPU, memory, disk I/O, network | 5-60s |
| **Availability** | Uptime, health status, error rate | 10-60s |
| **Security** | Failed logins, privilege changes, audit events | Real-time |

---

## Health Checks

### Basic Health Checks

```bash
# Check database health
aishell monitor health prod-db

# Output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Database Health Check: prod-db
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Status: HEALTHY ✓
#  Type: PostgreSQL 14.5
#  Uptime: 45 days, 12 hours
#  Last Check: 2024-01-15 14:30:00
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Connectivity               ✓ PASS (12ms latency)
#  Authentication             ✓ PASS
#  Database Accessible        ✓ PASS
#  Disk Space                 ✓ PASS (65% used)
#  Replication                ✓ PASS (0.2s lag)
#  Connections                ⚠ WARNING (78/100 used)
#  Cache Hit Ratio            ✓ PASS (98.5%)
#  Slow Queries               ⚠ WARNING (23 in last hour)
#  Table Bloat                ✓ PASS (12% avg)
#  Index Usage                ✓ PASS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Verbose health check
aishell monitor health prod-db --verbose

# Quick health check (essential checks only)
aishell monitor health prod-db --quick

# Check all databases
aishell monitor health --all
```

### Comprehensive Health Assessment

```bash
# Full health assessment
aishell monitor health prod-db \
  --comprehensive \
  --include-recommendations

# Output includes:
# - All basic health checks
# - Performance metrics
# - Security assessment
# - Backup status
# - Optimization suggestions
# - Capacity planning
# - Risk assessment

# Health check with thresholds
aishell monitor health prod-db \
  --cpu-threshold 80 \
  --memory-threshold 85 \
  --disk-threshold 90 \
  --connection-threshold 80

# Export health report
aishell monitor health prod-db \
  --format json \
  --output health-report.json

# Schedule periodic health checks
aishell monitor health-schedule prod-db \
  --interval 5m \
  --alert-on-failure \
  --slack-webhook https://hooks.slack.com/...
```

### Health Check Categories

#### 1. Connectivity Check

```bash
# Test database connectivity
aishell monitor health prod-db --check connectivity

# Test with timeout
aishell monitor health prod-db \
  --check connectivity \
  --timeout 5s

# Measure latency
aishell monitor ping prod-db \
  --count 10 \
  --interval 1s
```

#### 2. Resource Check

```bash
# Check CPU usage
aishell monitor health prod-db --check cpu

# Check memory usage
aishell monitor health prod-db --check memory

# Check disk space
aishell monitor health prod-db --check disk

# Check all resources
aishell monitor resources prod-db
```

#### 3. Replication Check

```bash
# Check replication status
aishell monitor health prod-db --check replication

# Monitor replication lag
aishell monitor replication-lag prod-db \
  --alert-threshold 5s \
  --continuous

# Check replication topology
aishell monitor replication-topology prod-db
```

---

## Real-Time Monitoring

### Live Metrics Dashboard

```bash
# Start real-time monitoring dashboard
aishell monitor dashboard prod-db

# Dashboard output (updates every second):
# ╔═══════════════════════════════════════════════════════════════╗
# ║           prod-db - Real-Time Monitoring                      ║
# ║                 2024-01-15 14:30:45                          ║
# ╠═══════════════════════════════════════════════════════════════╣
# ║                                                               ║
# ║  STATUS: HEALTHY ✓                    UPTIME: 45d 12h 30m    ║
# ║                                                               ║
# ║  ┌─ Connections ─────────────────────────────────────────┐   ║
# ║  │  Active: 78/100  [████████████████░░░░]  78%          │   ║
# ║  │  Idle:   15      Waiting: 0                           │   ║
# ║  └───────────────────────────────────────────────────────┘   ║
# ║                                                               ║
# ║  ┌─ Performance ──────────────────────────────────────────┐  ║
# ║  │  QPS:        1,234/sec  [▁▂▃▅▆▇█▇▆▅▃▂]                │  ║
# ║  │  Avg Query:  12ms                                      │  ║
# ║  │  Slow:       3/min      Cache Hit: 98.5%              │  ║
# ║  └───────────────────────────────────────────────────────┘  ║
# ║                                                               ║
# ║  ┌─ Resources ────────────────────────────────────────────┐  ║
# ║  │  CPU:    45%  [████████████░░░░░░░░░░░░]              │  ║
# ║  │  Memory: 68%  [████████████████░░░░░░░░]              │  ║
# ║  │  Disk:   65%  [███████████████░░░░░░░░░]              │  ║
# ║  │  I/O:    234 MB/s  Read: 156MB/s  Write: 78MB/s       │  ║
# ║  └───────────────────────────────────────────────────────┘  ║
# ║                                                               ║
# ║  ┌─ Recent Activity ──────────────────────────────────────┐  ║
# ║  │  14:30:42  Query completed in 234ms (SELECT...)        │  ║
# ║  │  14:30:40  New connection from 192.168.1.50           │  ║
# ║  │  14:30:38  Index scan on orders (12ms)                │  ║
# ║  └───────────────────────────────────────────────────────┘  ║
# ║                                                               ║
# ╚═══════════════════════════════════════════════════════════════╝

# Customize dashboard refresh rate
aishell monitor dashboard prod-db --refresh 5s

# Dashboard with specific metrics
aishell monitor dashboard prod-db \
  --metrics cpu,memory,connections,queries \
  --refresh 2s
```

### Real-Time Metrics Streaming

```bash
# Stream metrics to stdout
aishell monitor stream prod-db \
  --metrics cpu,memory,qps \
  --format json

# Stream to file
aishell monitor stream prod-db \
  --metrics all \
  --format csv \
  --output metrics.csv

# Stream to monitoring system
aishell monitor stream prod-db \
  --metrics all \
  --format prometheus \
  --push-gateway http://prometheus:9091
```

### Top Queries Monitor

```bash
# Monitor top queries in real-time
aishell monitor top-queries prod-db

# Output (updates live):
# TOP QUERIES (by total time)
# ────────────────────────────────────────────────────────────────
# Calls | Avg Time | Total Time | Query
# ────────────────────────────────────────────────────────────────
# 1,234 | 125ms    | 2m 34s     | SELECT * FROM orders WHERE...
#   678 | 89ms     | 1m 0s      | UPDATE users SET last_login...
#   456 | 67ms     | 30s        | SELECT COUNT(*) FROM products
# ────────────────────────────────────────────────────────────────

# Monitor slow queries
aishell monitor slow-queries prod-db \
  --threshold 100ms \
  --realtime

# Monitor by specific criteria
aishell monitor top-queries prod-db \
  --sort-by total-time \
  --limit 20 \
  --refresh 10s
```

---

## Setting Up Alerts

### Alert Configuration

```bash
# Create CPU alert
aishell monitor alerts create prod-db \
  --name high-cpu \
  --metric cpu \
  --condition "> 80" \
  --duration 5m \
  --severity warning \
  --action slack,email

# Create connection pool alert
aishell monitor alerts create prod-db \
  --name connection-pool-full \
  --metric connection-usage \
  --condition "> 90%" \
  --severity critical \
  --action pagerduty,slack

# Create slow query alert
aishell monitor alerts create prod-db \
  --name slow-queries \
  --metric slow-query-count \
  --condition "> 10" \
  --period 1h \
  --severity warning \
  --action email

# Create replication lag alert
aishell monitor alerts create prod-db \
  --name replication-lag \
  --metric replication-lag \
  --condition "> 5s" \
  --severity critical \
  --action pagerduty,email,sms

# Create disk space alert
aishell monitor alerts create prod-db \
  --name disk-space-low \
  --metric disk-usage \
  --condition "> 85%" \
  --severity warning \
  --action email,slack

# Create custom alert with expression
aishell monitor alerts create prod-db \
  --name custom-alert \
  --expression "(cpu > 80 AND memory > 85) OR connections > 95%" \
  --severity critical \
  --action pagerduty
```

### Alert Management

```bash
# List all alerts
aishell monitor alerts list prod-db

# Output:
# Name               | Metric        | Condition | Severity | Status
# -------------------|---------------|-----------|----------|--------
# high-cpu           | cpu           | > 80      | warning  | active
# connection-pool    | connections   | > 90%     | critical | active
# slow-queries       | slow-queries  | > 10/h    | warning  | firing
# replication-lag    | repl-lag      | > 5s      | critical | ok
# disk-space-low     | disk-usage    | > 85%     | warning  | ok

# Show alert details
aishell monitor alerts show high-cpu

# Update alert
aishell monitor alerts update high-cpu \
  --condition "> 85" \
  --duration 10m

# Enable/disable alert
aishell monitor alerts disable high-cpu
aishell monitor alerts enable high-cpu

# Delete alert
aishell monitor alerts delete high-cpu

# Test alert
aishell monitor alerts test high-cpu
```

### Alert Channels

#### Slack Integration

```bash
# Configure Slack webhook
aishell monitor alerts configure slack \
  --webhook https://hooks.slack.com/services/T00/B00/XX \
  --channel #db-alerts \
  --username "DB Monitor" \
  --icon-emoji ":database:"

# Test Slack notification
aishell monitor alerts test-channel slack

# Create alert with Slack
aishell monitor alerts create prod-db \
  --name test-alert \
  --metric cpu \
  --condition "> 80" \
  --action slack \
  --slack-channel #critical-alerts
```

#### Email Alerts

```bash
# Configure email
aishell monitor alerts configure email \
  --smtp smtp.gmail.com:587 \
  --from alerts@example.com \
  --to dba-team@example.com \
  --auth-user alerts@example.com

# Email with template
aishell monitor alerts configure email \
  --template custom-alert-template.html

# Create email alert
aishell monitor alerts create prod-db \
  --name email-alert \
  --metric memory \
  --condition "> 90%" \
  --action email \
  --email-to urgent@example.com \
  --email-subject "URGENT: High Memory Usage"
```

#### PagerDuty Integration

```bash
# Configure PagerDuty
aishell monitor alerts configure pagerduty \
  --integration-key YOUR_INTEGRATION_KEY \
  --service-name "Production Database"

# Create PagerDuty alert
aishell monitor alerts create prod-db \
  --name critical-alert \
  --metric database-down \
  --action pagerduty \
  --pagerduty-severity critical
```

#### SMS Alerts

```bash
# Configure SMS (Twilio)
aishell monitor alerts configure sms \
  --provider twilio \
  --account-sid YOUR_ACCOUNT_SID \
  --auth-token YOUR_AUTH_TOKEN \
  --from-number +1234567890

# Create SMS alert
aishell monitor alerts create prod-db \
  --name urgent-alert \
  --metric database-down \
  --action sms \
  --sms-to +1987654321
```

### Alert Rules and Conditions

```bash
# Threshold-based alert
aishell monitor alerts create prod-db \
  --name threshold-alert \
  --metric cpu \
  --condition "> 80" \
  --threshold-type static

# Anomaly detection alert
aishell monitor alerts create prod-db \
  --name anomaly-alert \
  --metric query-duration \
  --condition "anomaly" \
  --sensitivity high \
  --baseline-period 7d

# Rate of change alert
aishell monitor alerts create prod-db \
  --name rate-change-alert \
  --metric connections \
  --condition "rate > 20/min" \
  --window 5m

# Composite alert
aishell monitor alerts create prod-db \
  --name composite-alert \
  --expression "cpu > 80 AND (memory > 85 OR disk-io > 1000)" \
  --severity critical
```

---

## Performance Analysis

### Query Performance Analysis

```bash
# Analyze query performance
aishell monitor analyze-queries prod-db \
  --period 24h

# Output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Query Performance Analysis (Last 24h)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Total Queries: 1,234,567
#  Avg Duration: 23ms
#  Slow Queries: 567 (0.05%)
#  Failed Queries: 12 (0.001%)
#
#  TOP SLOW QUERIES:
#  1. SELECT * FROM orders WHERE user_id IN (...)
#     Calls: 234  Avg: 2.3s  Total: 9m 2s
#     Recommendation: Add index on user_id
#
#  2. UPDATE products SET stock = stock - 1 WHERE id = ?
#     Calls: 5,678  Avg: 156ms  Total: 14m 47s
#     Recommendation: Consider bulk updates
#
#  QUERY PATTERNS:
#  - SELECT queries: 89% (mostly cached)
#  - INSERT queries: 7%
#  - UPDATE queries: 3%
#  - DELETE queries: 1%
#
#  RECOMMENDATIONS:
#  ✓ 3 queries can be optimized with indexes
#  ✓ 2 queries should use prepared statements
#  ⚠ 1 query has high lock contention
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Detailed query analysis
aishell monitor analyze-queries prod-db \
  --period 7d \
  --format detailed \
  --output query-analysis-report.pdf
```

### Performance Trends

```bash
# Show performance trends
aishell monitor trends prod-db \
  --metrics qps,latency,cache-hit-ratio \
  --period 30d

# ASCII chart output:
# QPS (Queries Per Second) - Last 30 days
# 2000 │                                  ╭─╮
# 1800 │                              ╭───╯ ╰─╮
# 1600 │                          ╭───╯       ╰───╮
# 1400 │                      ╭───╯               ╰───╮
# 1200 │                  ╭───╯                       ╰───╮
# 1000 │              ╭───╯                               ╰──
#  800 │          ╭───╯
#  600 │      ╭───╯
#  400 │  ╭───╯
#  200 │──╯
#    0 └──────────────────────────────────────────────────────
#      Jan 1    Jan 8    Jan 15   Jan 22   Jan 29

# Compare trends between periods
aishell monitor trends prod-db \
  --compare-periods "last week,this week"

# Export trends data
aishell monitor trends prod-db \
  --period 90d \
  --format csv \
  --output performance-trends.csv
```

### Capacity Planning

```bash
# Generate capacity report
aishell monitor capacity prod-db \
  --forecast 90d

# Output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Capacity Planning Report
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  CURRENT USAGE:
#  - Database Size: 156 GB
#  - Growth Rate: 2.3 GB/week
#  - Connections: 78/100 (78%)
#  - QPS: 1,234 (peak: 2,456)
#
#  90-DAY FORECAST:
#  - Expected Size: 186 GB
#  - Expected QPS: 1,480 (peak: 2,950)
#  - Connection Needs: 94/100 (94%) ⚠
#
#  RECOMMENDATIONS:
#  ⚠ Increase connection pool to 150 within 60 days
#  ✓ Disk space adequate for 12+ months
#  ⚠ Consider read replicas for query distribution
#  ✓ Memory usage within acceptable range
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Resource utilization forecast
aishell monitor forecast prod-db \
  --resource disk \
  --period 180d \
  --visualize
```

### Bottleneck Detection

```bash
# Identify performance bottlenecks
aishell monitor bottlenecks prod-db

# Output:
# BOTTLENECK ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  1. DISK I/O (HIGH SEVERITY)
#     - Current: 850 IOPS (capacity: 1000 IOPS)
#     - Impact: Query latency +45%
#     - Solution: Upgrade to SSD or add read replicas
#
#  2. CONNECTION POOL (MEDIUM SEVERITY)
#     - Current: 78/100 connections
#     - Wait time: avg 23ms
#     - Solution: Increase pool size or optimize query duration
#
#  3. TABLE BLOAT (LOW SEVERITY)
#     - Tables affected: orders (23%), users (15%)
#     - Impact: Index scan slowdown
#     - Solution: Run VACUUM FULL during maintenance window
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Continuous bottleneck monitoring
aishell monitor bottlenecks prod-db \
  --continuous \
  --alert-on-new \
  --action slack
```

---

## Dashboard Usage

### Web Dashboard

```bash
# Start web dashboard
aishell monitor web-dashboard prod-db \
  --port 8080 \
  --bind 0.0.0.0

# Output:
# ✓ Starting web dashboard...
# ✓ Server running at http://localhost:8080
# ✓ Press Ctrl+C to stop

# Dashboard with authentication
aishell monitor web-dashboard prod-db \
  --port 8080 \
  --auth-user admin \
  --auth-password-prompt

# Dashboard with SSL
aishell monitor web-dashboard prod-db \
  --port 8443 \
  --ssl-cert /path/to/cert.pem \
  --ssl-key /path/to/key.pem
```

### Multi-Database Dashboard

```bash
# Monitor multiple databases
aishell monitor dashboard \
  --databases prod-db,staging-db,dev-db \
  --layout grid

# Federation dashboard
aishell monitor dashboard \
  --federation my-cluster \
  --show-topology
```

### Custom Dashboards

```bash
# Create custom dashboard layout
cat > custom-dashboard.yaml << EOF
layout:
  - row:
    - panel: metrics
      metrics: [cpu, memory, disk]
      width: 60%
    - panel: connections
      width: 40%
  - row:
    - panel: top-queries
      limit: 10
      width: 50%
    - panel: slow-queries
      threshold: 100ms
      width: 50%
  - row:
    - panel: alerts
      severity: [critical, warning]
      width: 100%
EOF

aishell monitor dashboard prod-db \
  --config custom-dashboard.yaml
```

---

## Grafana Integration

### Setup Grafana Data Source

```bash
# Configure Grafana integration
aishell monitor configure grafana \
  --url http://grafana.example.com \
  --api-key YOUR_GRAFANA_API_KEY

# Create Grafana data source
aishell monitor grafana create-datasource prod-db \
  --name "Production Database" \
  --type prometheus

# Verify connection
aishell monitor grafana test-connection
```

### Import Dashboards

```bash
# List available Grafana dashboards
aishell monitor grafana list-dashboards

# Import pre-built dashboard
aishell monitor grafana import-dashboard \
  --template postgresql-overview \
  --datasource prod-db

# Import custom dashboard
aishell monitor grafana import-dashboard \
  --file my-dashboard.json \
  --datasource prod-db

# Create dashboard from metrics
aishell monitor grafana create-dashboard prod-db \
  --name "Custom DB Dashboard" \
  --metrics cpu,memory,qps,latency,connections \
  --auto-refresh 5s
```

### Dashboard Templates

Pre-built Grafana dashboard templates:

1. **PostgreSQL Overview**
   - Connection stats
   - Query performance
   - Cache hit ratio
   - Replication lag
   - Table/index statistics

2. **MySQL Performance**
   - InnoDB metrics
   - Query analysis
   - Slow query log
   - Replication status

3. **MongoDB Cluster**
   - Replica set status
   - Sharding metrics
   - Operation counters
   - WiredTiger cache

4. **Redis Monitoring**
   - Memory usage
   - Command stats
   - Key space analysis
   - Persistence status

```bash
# Import all templates
aishell monitor grafana import-templates \
  --datasource prod-db \
  --all
```

---

## Prometheus Integration

### Configure Prometheus Exporter

```bash
# Start Prometheus exporter
aishell monitor prometheus-exporter prod-db \
  --port 9187 \
  --bind 0.0.0.0

# Output:
# ✓ Prometheus exporter started
# ✓ Metrics endpoint: http://localhost:9187/metrics
# ✓ Exporting metrics every 15s

# Configure custom metrics
aishell monitor prometheus-exporter prod-db \
  --port 9187 \
  --metrics cpu,memory,qps,connections,replication-lag \
  --interval 10s

# Export to Prometheus Pushgateway
aishell monitor prometheus-push prod-db \
  --pushgateway http://pushgateway:9091 \
  --job production-db \
  --interval 30s
```

### Prometheus Metrics

Available Prometheus metrics:

```
# Database metrics
aishell_db_up{database="prod-db"} 1
aishell_db_connections_active{database="prod-db"} 78
aishell_db_connections_total{database="prod-db"} 100
aishell_db_queries_per_second{database="prod-db"} 1234
aishell_db_query_duration_seconds{database="prod-db",quantile="0.5"} 0.012
aishell_db_query_duration_seconds{database="prod-db",quantile="0.95"} 0.089
aishell_db_query_duration_seconds{database="prod-db",quantile="0.99"} 0.234

# System metrics
aishell_db_cpu_usage{database="prod-db"} 45
aishell_db_memory_usage{database="prod-db"} 68
aishell_db_disk_usage{database="prod-db"} 65
aishell_db_disk_io_read_bytes{database="prod-db"} 156000000
aishell_db_disk_io_write_bytes{database="prod-db"} 78000000

# Replication metrics
aishell_db_replication_lag_seconds{database="prod-db",replica="standby-1"} 0.2
```

### Prometheus Alerts

```bash
# Export Prometheus alert rules
aishell monitor prometheus-export-alerts prod-db \
  --output prometheus-alerts.yml

# Sample prometheus-alerts.yml:
# groups:
#   - name: database
#     rules:
#       - alert: HighCPUUsage
#         expr: aishell_db_cpu_usage > 80
#         for: 5m
#         labels:
#           severity: warning
#         annotations:
#           summary: "High CPU usage on {{ $labels.database }}"
#
#       - alert: HighConnectionUsage
#         expr: aishell_db_connections_active / aishell_db_connections_total > 0.9
#         for: 5m
#         labels:
#           severity: critical
```

---

## Best Practices

### 1. Baseline Performance

```bash
# Establish performance baseline
aishell monitor baseline prod-db \
  --duration 7d \
  --metrics all \
  --output baseline.json

# Compare against baseline
aishell monitor compare-baseline prod-db \
  --baseline baseline.json \
  --alert-on-deviation 20%
```

### 2. Regular Monitoring Reviews

```bash
#!/bin/bash
# weekly-monitoring-review.sh

# Generate weekly report
aishell monitor report prod-db \
  --period 7d \
  --format pdf \
  --output weekly-report-$(date +%Y%m%d).pdf

# Check for performance regression
aishell monitor regression-check prod-db \
  --period 7d

# Review slow queries
aishell monitor slow-queries prod-db \
  --period 7d \
  --threshold 500ms
```

### 3. Alert Tuning

```bash
# Avoid alert fatigue - tune thresholds based on baseline
aishell monitor alerts tune prod-db \
  --auto-adjust-thresholds \
  --baseline-period 30d

# Set up alert escalation
aishell monitor alerts escalation prod-db \
  --level-1 slack \
  --level-2 email \
  --level-3 pagerduty \
  --escalation-delay 15m
```

---

## Next Steps

- Review [Security Best Practices](./SECURITY_BEST_PRACTICES.md)
- Configure [Integration Guide](./INTEGRATION_GUIDE.md)
- Check [Troubleshooting Guide](../TROUBLESHOOTING.md)

---

*Last Updated: 2024-01-15 | Version: 1.0.0*
