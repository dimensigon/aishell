# Integration Guide

## Table of Contents

1. [Overview](#overview)
2. [Slack Integration](#slack-integration)
3. [Email Notifications](#email-notifications)
4. [Federation Setup](#federation-setup)
5. [Schema Management](#schema-management)
6. [Autonomous Agent (ADA)](#autonomous-agent-ada)
7. [Third-Party Integrations](#third-party-integrations)
8. [API and Webhooks](#api-and-webhooks)

---

## Overview

AI-Shell provides extensive integration capabilities allowing you to connect with external systems, automate workflows, and manage distributed database environments.

### Integration Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   Integration Architecture                     │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
          ┌───────────────────────────────────────┐
          │        AI-Shell Integration Core       │
          └───────┬────────────────┬───────────────┘
                  │                │
         ┌────────▼────────┐  ┌───▼──────────────┐
         │  Notifications  │  │   Data Sync      │
         │  - Slack        │  │  - Federation    │
         │  - Email        │  │  - Replication   │
         │  - SMS          │  │  - Schema Sync   │
         │  - PagerDuty    │  │  - Data Migration│
         └────────┬────────┘  └──────────────────┘
                  │
         ┌────────▼──────────────────────────────┐
         │      External Systems                  │
         │  - Grafana/Prometheus                 │
         │  - CI/CD (Jenkins, GitLab, GitHub)    │
         │  - Ticketing (Jira, ServiceNow)       │
         │  - Cloud Providers (AWS, Azure, GCP)  │
         │  - Custom Webhooks                    │
         └────────────────────────────────────────┘
```

---

## Slack Integration

### Setup Slack Workspace

```bash
# Configure Slack webhook
aishell integration slack configure \
  --webhook https://hooks.slack.com/services/T00/B00/XXXX \
  --channel #database-alerts \
  --username "DB Monitor" \
  --icon-emoji ":database:"

# Test Slack connection
aishell integration slack test

# Output:
# ✓ Sending test message to Slack...
# ✓ Message delivered successfully
# ✓ Channel: #database-alerts
# ✓ Webhook: https://hooks.slack.com/services/T00/B00/XXXX
```

### Slack Notifications

```bash
# Send custom message
aishell integration slack send \
  --message "Database maintenance starting in 10 minutes" \
  --channel #db-team

# Send with formatting
aishell integration slack send \
  --message "Database backup completed" \
  --attachment '{
    "color": "good",
    "title": "Backup Summary",
    "fields": [
      {"title": "Database", "value": "prod-db", "short": true},
      {"title": "Size", "value": "4.2 GB", "short": true},
      {"title": "Duration", "value": "7m 23s", "short": true},
      {"title": "Status", "value": "Success", "short": true}
    ]
  }'

# Send with buttons (interactive)
aishell integration slack send \
  --message "Slow query detected" \
  --attachment '{
    "text": "Query taking 5.2 seconds to execute",
    "callback_id": "query_actions",
    "actions": [
      {"name": "analyze", "text": "Analyze", "type": "button"},
      {"name": "optimize", "text": "Optimize", "type": "button"},
      {"name": "ignore", "text": "Ignore", "type": "button"}
    ]
  }'
```

### Automated Slack Alerts

```bash
# Configure alert forwarding to Slack
aishell integration slack alerts enable \
  --forward-critical \
  --forward-warning \
  --channel #db-alerts

# Alert on backup completion
aishell backup schedule prod-db \
  --name daily-backup \
  --schedule "0 2 * * *" \
  --on-success slack:#db-team \
  --on-failure slack:#db-critical

# Alert on query performance
aishell monitor alerts create prod-db \
  --name slow-queries \
  --metric query-time \
  --threshold 1000ms \
  --action slack:#db-performance

# Daily summary to Slack
aishell integration slack summary prod-db \
  --schedule "0 9 * * *" \
  --channel #db-daily-summary \
  --include-metrics \
  --include-slow-queries \
  --include-backup-status
```

### Slack Commands

```bash
# Enable Slack slash commands
aishell integration slack commands enable \
  --signing-secret YOUR_SLACK_SIGNING_SECRET

# Available commands:
# /aishell health prod-db           - Check database health
# /aishell query prod-db "SELECT..." - Run query
# /aishell backup prod-db            - Create backup
# /aishell status prod-db            - Show status

# Custom command
aishell integration slack command create \
  --name check-connections \
  --command "aishell monitor connections prod-db" \
  --response-channel true
```

---

## Email Notifications

### Configure Email

```bash
# Configure SMTP settings
aishell integration email configure \
  --smtp smtp.gmail.com:587 \
  --from database-alerts@example.com \
  --username alerts@example.com \
  --password-prompt \
  --tls-enabled

# Test email configuration
aishell integration email test \
  --to your-email@example.com

# Configure multiple recipients
aishell integration email configure \
  --to dba-team@example.com,ops@example.com \
  --cc manager@example.com
```

### Email Templates

```bash
# Create custom email template
cat > alert-template.html << EOF
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial, sans-serif; }
    .alert { border-left: 4px solid #ff0000; padding: 10px; }
    .success { border-left: 4px solid #00ff00; padding: 10px; }
  </style>
</head>
<body>
  <h2>{{alert_title}}</h2>
  <div class="{{alert_class}}">
    <p><strong>Database:</strong> {{database}}</p>
    <p><strong>Alert:</strong> {{alert_message}}</p>
    <p><strong>Time:</strong> {{timestamp}}</p>
    <p><strong>Metric:</strong> {{metric_value}}</p>
  </div>
  <p>View details: <a href="{{dashboard_url}}">Dashboard</a></p>
</body>
</html>
EOF

aishell integration email template \
  --name alert-template \
  --file alert-template.html

# Use template
aishell integration email send \
  --to dba@example.com \
  --template alert-template \
  --variables '{
    "alert_title": "High CPU Usage",
    "database": "prod-db",
    "alert_message": "CPU usage at 95%",
    "alert_class": "alert",
    "metric_value": "95%",
    "dashboard_url": "http://dashboard.example.com/prod-db"
  }'
```

### Email Alerts

```bash
# Configure backup email notifications
aishell backup schedule prod-db \
  --name daily-backup \
  --schedule "0 2 * * *" \
  --email-on-success dba@example.com \
  --email-on-failure urgent@example.com

# Configure monitoring alerts
aishell monitor alerts create prod-db \
  --name high-cpu \
  --metric cpu \
  --threshold 80 \
  --action email \
  --email-to ops@example.com \
  --email-subject "ALERT: High CPU on {{database}}"

# Daily report via email
aishell integration email schedule-report prod-db \
  --schedule "0 9 * * *" \
  --to management@example.com \
  --subject "Daily Database Report" \
  --include-metrics \
  --include-summary \
  --format pdf
```

### Email Digests

```bash
# Configure daily digest
aishell integration email digest prod-db \
  --schedule "0 18 * * *" \
  --to team@example.com \
  --include-alerts \
  --include-performance \
  --include-backups \
  --include-slow-queries

# Weekly summary
aishell integration email digest prod-db \
  --schedule "0 9 * * 1" \
  --to management@example.com \
  --subject "Weekly Database Summary" \
  --period 7d \
  --format html
```

---

## Federation Setup

### What is Federation?

Federation allows you to manage multiple database instances as a single logical unit, enabling distributed queries, schema synchronization, and unified monitoring.

```
Federation Architecture:
┌─────────────────────────────────────────────────────────┐
│              Federation Coordinator                     │
└────────┬──────────┬──────────┬──────────┬───────────────┘
         │          │          │          │
    ┌────▼────┐┌────▼────┐┌────▼────┐┌────▼────┐
    │  Node 1 ││  Node 2 ││  Node 3 ││  Node 4 │
    │ (Write) ││  (Read) ││  (Read) ││  (Read) │
    └─────────┘└─────────┘└─────────┘└─────────┘
```

### Creating a Federation

```bash
# Initialize federation
aishell federation init my-cluster \
  --topology mesh \
  --strategy round-robin

# Add database nodes
aishell federation add-node my-cluster \
  --name prod-db-1 \
  --connection prod-db-1 \
  --role primary \
  --weight 1.0

aishell federation add-node my-cluster \
  --name prod-db-2 \
  --connection prod-db-2 \
  --role replica \
  --weight 0.5

aishell federation add-node my-cluster \
  --name prod-db-3 \
  --connection prod-db-3 \
  --role replica \
  --weight 0.5

# Show federation status
aishell federation status my-cluster

# Output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Federation: my-cluster
#  Topology: mesh
#  Strategy: round-robin
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Nodes:
#  Name        | Role    | Status  | Lag    | Weight | Load
#  ------------|---------|---------|--------|--------|------
#  prod-db-1   | primary | healthy | 0ms    | 1.0    | 45%
#  prod-db-2   | replica | healthy | 120ms  | 0.5    | 23%
#  prod-db-3   | replica | healthy | 150ms  | 0.5    | 28%
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Federated Queries

```bash
# Query across federation
aishell federation query my-cluster \
  --sql "SELECT COUNT(*) FROM users"

# This query automatically routes to the best available node

# Force specific node
aishell federation query my-cluster \
  --sql "SELECT * FROM orders WHERE id = 123" \
  --node prod-db-1

# Read from replicas only
aishell federation query my-cluster \
  --sql "SELECT * FROM products" \
  --read-preference secondary

# Distributed join (query multiple nodes)
aishell federation query my-cluster \
  --sql "
    SELECT u.name, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    GROUP BY u.name
  " \
  --distributed

# Aggregate across nodes
aishell federation query my-cluster \
  --sql "SELECT region, SUM(sales) FROM regional_sales GROUP BY region" \
  --aggregate
```

### Schema Synchronization

```bash
# Sync schema across federation
aishell federation sync-schema my-cluster \
  --source prod-db-1 \
  --targets prod-db-2,prod-db-3 \
  --dry-run

# Output:
# Schema Sync Preview:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  prod-db-2:
#    + CREATE TABLE new_products (...)
#    ~ ALTER TABLE users ADD COLUMN last_login timestamp
#    - DROP TABLE old_logs
#
#  prod-db-3:
#    + CREATE INDEX idx_orders_user_id ON orders(user_id)
#    ~ ALTER TABLE products ADD COLUMN description text
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Apply schema sync
aishell federation sync-schema my-cluster \
  --source prod-db-1 \
  --targets prod-db-2,prod-db-3 \
  --apply

# Continuous schema sync
aishell federation sync-schema my-cluster \
  --continuous \
  --check-interval 5m \
  --auto-apply
```

### Load Balancing

```bash
# Configure load balancing
aishell federation configure my-cluster \
  --load-balance-strategy weighted-round-robin \
  --health-check-interval 30s \
  --failover-enabled

# Update node weights
aishell federation update-node my-cluster \
  --name prod-db-2 \
  --weight 1.0

# Show load distribution
aishell federation load-stats my-cluster

# Rebalance load
aishell federation rebalance my-cluster
```

### Failover and High Availability

```bash
# Configure automatic failover
aishell federation configure my-cluster \
  --auto-failover \
  --failover-threshold 3 \
  --promote-on-failure

# Manual failover
aishell federation failover my-cluster \
  --from prod-db-1 \
  --to prod-db-2

# Promote replica to primary
aishell federation promote my-cluster \
  --node prod-db-2

# Test failover
aishell federation test-failover my-cluster \
  --dry-run
```

---

## Schema Management

### Schema Migration

```bash
# Create migration
aishell schema migration create \
  --name add-user-preferences \
  --database prod-db

# This creates: migrations/20240115_add_user_preferences.sql

# Edit migration file
cat > migrations/20240115_add_user_preferences.sql << EOF
-- Up migration
CREATE TABLE user_preferences (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  preferences JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- Down migration
-- DROP TABLE user_preferences;
EOF

# Run migration
aishell schema migration run prod-db \
  --name add-user-preferences

# Rollback migration
aishell schema migration rollback prod-db \
  --name add-user-preferences

# Show migration status
aishell schema migration status prod-db

# Output:
# Migrations:
# Name                       | Status  | Applied At
# ---------------------------|---------|------------------
# 001_initial_schema         | applied | 2024-01-01 10:00
# 002_add_orders_table       | applied | 2024-01-05 14:30
# 003_add_user_preferences   | applied | 2024-01-15 09:00
# 004_add_analytics_tables   | pending | -
```

### Schema Versioning

```bash
# Version current schema
aishell schema version prod-db \
  --tag v1.0.0 \
  --message "Initial production schema"

# Compare schema versions
aishell schema diff prod-db \
  --from v1.0.0 \
  --to v1.1.0

# Restore schema version
aishell schema restore prod-db \
  --version v1.0.0 \
  --target restore-db
```

### Schema Documentation

```bash
# Generate schema documentation
aishell schema document prod-db \
  --output schema-docs/ \
  --format html

# Generate ER diagram
aishell schema diagram prod-db \
  --output schema-diagram.png \
  --format png \
  --include-relationships

# Generate data dictionary
aishell schema dictionary prod-db \
  --output data-dictionary.pdf \
  --include-descriptions \
  --include-constraints
```

---

## Autonomous Agent (ADA)

### What is ADA?

ADA (Autonomous Database Agent) is an AI-powered agent that monitors your database, detects issues, and can automatically fix common problems.

### Starting ADA

```bash
# Start ADA for database
aishell ada start prod-db \
  --mode monitor

# Output:
# ✓ ADA started for prod-db
# ✓ Mode: monitor
# ✓ AI Model: GPT-4
# ✓ Learning from: 30 days of history
#
# ADA is now monitoring your database...
# - Query performance
# - Connection pool
# - Disk space
# - Replication lag
# - Security anomalies

# Start with auto-fix enabled
aishell ada start prod-db \
  --mode auto-fix \
  --confidence-threshold 0.8

# Start with specific capabilities
aishell ada start prod-db \
  --capabilities optimize-queries,manage-indexes,vacuum-tables \
  --schedule-maintenance-window "02:00-04:00"
```

### ADA Configuration

```bash
# Configure ADA behavior
aishell ada configure prod-db \
  --learning-period 30d \
  --auto-optimize-queries \
  --auto-create-indexes \
  --auto-vacuum-tables \
  --dry-run-first

# Set safety limits
aishell ada configure prod-db \
  --max-query-rewrite-complexity 5 \
  --max-index-size 1GB \
  --require-approval-for high-impact

# Configure notifications
aishell ada configure prod-db \
  --notify-on-action slack:#ada-actions \
  --notify-on-anomaly email:dba@example.com \
  --daily-summary slack:#ada-summary
```

### ADA Actions and Insights

```bash
# View ADA activity
aishell ada logs prod-db --limit 20

# Output:
# ADA Activity Log:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  2024-01-15 10:30:00 | OPTIMIZE | Created index on orders(user_id)
#    Reason: High scan cost on frequent query
#    Impact: 15x performance improvement
#    Confidence: 0.92
#
#  2024-01-15 09:15:00 | VACUUM | Vacuumed table 'products'
#    Reason: 35% bloat detected
#    Impact: Reduced table size by 1.2GB
#    Confidence: 0.95
#
#  2024-01-15 08:00:00 | ALERT | Detected unusual query pattern
#    Pattern: SELECT * FROM users without WHERE clause
#    User: app_user
#    Recommendation: Add row limit or filter
#    Confidence: 0.88
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Get ADA insights
aishell ada insights prod-db

# Ask ADA for recommendations
aishell ada recommend prod-db \
  --topic "query performance"

# ADA health check
aishell ada status prod-db

# Output:
# ADA Status:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Status: Active
#  Mode: auto-fix
#  Uptime: 15 days, 4 hours
#  Actions Taken: 234
#  Issues Detected: 456
#  Issues Auto-Fixed: 189
#  Issues Requiring Approval: 12
#  Learning Accuracy: 94.5%
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### ADA Learning

```bash
# Train ADA on your workload
aishell ada train prod-db \
  --period 90d \
  --workload production

# Export ADA knowledge base
aishell ada export-knowledge prod-db \
  --output ada-knowledge.json

# Import knowledge to another database
aishell ada import-knowledge staging-db \
  --input ada-knowledge.json

# Review ADA decisions
aishell ada decisions prod-db \
  --period 7d \
  --show-reasoning
```

---

## Third-Party Integrations

### Grafana Integration

```bash
# Configure Grafana
aishell integration grafana configure \
  --url http://grafana.example.com \
  --api-key YOUR_API_KEY

# Create datasource
aishell integration grafana datasource prod-db \
  --name "Production Database" \
  --type prometheus

# Import dashboards
aishell integration grafana import \
  --template postgresql-overview \
  --datasource prod-db
```

### Prometheus Integration

```bash
# Start Prometheus exporter
aishell integration prometheus start prod-db \
  --port 9187

# Configure Prometheus scrape config
aishell integration prometheus config \
  --output prometheus-scrape.yml

# Sample output for prometheus.yml:
# scrape_configs:
#   - job_name: 'aishell-prod-db'
#     static_configs:
#       - targets: ['localhost:9187']
```

### CI/CD Integration

#### Jenkins

```bash
# Generate Jenkins pipeline
aishell integration jenkins pipeline \
  --database prod-db \
  --output Jenkinsfile

# Sample Jenkinsfile:
# pipeline {
#   agent any
#   stages {
#     stage('Database Health Check') {
#       steps {
#         sh 'aishell monitor health prod-db'
#       }
#     }
#     stage('Run Migrations') {
#       steps {
#         sh 'aishell schema migration run prod-db'
#       }
#     }
#     stage('Backup Database') {
#       steps {
#         sh 'aishell backup create prod-db --upload s3'
#       }
#     }
#   }
# }
```

#### GitHub Actions

```bash
# Generate GitHub Actions workflow
aishell integration github-actions \
  --database prod-db \
  --output .github/workflows/database.yml

# Sample workflow:
# name: Database Operations
# on: [push]
# jobs:
#   database-check:
#     runs-on: ubuntu-latest
#     steps:
#       - uses: actions/checkout@v2
#       - name: Install AI-Shell
#         run: npm install -g @aishell/cli
#       - name: Health Check
#         run: aishell monitor health prod-db
#       - name: Run Migrations
#         run: aishell schema migration run prod-db
```

### JIRA Integration

```bash
# Configure JIRA
aishell integration jira configure \
  --url https://your-domain.atlassian.net \
  --username your-email@example.com \
  --api-token YOUR_JIRA_API_TOKEN

# Create ticket on alert
aishell monitor alerts create prod-db \
  --name critical-alert \
  --metric cpu \
  --threshold 90 \
  --action jira \
  --jira-project OPS \
  --jira-issue-type Incident

# Auto-create tickets for slow queries
aishell integration jira auto-ticket \
  --trigger slow-query \
  --threshold 5s \
  --project DBA \
  --assignee dba-team
```

---

## API and Webhooks

### REST API

```bash
# Start API server
aishell api start \
  --port 8080 \
  --auth-token YOUR_API_TOKEN

# Output:
# ✓ API server started
# ✓ Listening on http://localhost:8080
# ✓ API documentation: http://localhost:8080/docs
#
# Endpoints:
#   GET    /health/:database
#   POST   /query/:database
#   GET    /metrics/:database
#   POST   /backup/:database
#   GET    /status/:database
```

### Webhook Configuration

```bash
# Configure webhook endpoint
aishell integration webhook create \
  --name backup-webhook \
  --url https://your-app.com/webhooks/backup \
  --events backup.started,backup.completed,backup.failed \
  --auth-header "Authorization: Bearer YOUR_TOKEN"

# Test webhook
aishell integration webhook test backup-webhook

# List webhooks
aishell integration webhook list

# Webhook payload example:
# {
#   "event": "backup.completed",
#   "database": "prod-db",
#   "timestamp": "2024-01-15T14:30:00Z",
#   "data": {
#     "backup_name": "daily-backup-20240115",
#     "size": "4.2GB",
#     "duration": "7m 23s",
#     "status": "success"
#   }
# }
```

### Custom Integrations

```bash
# Create custom integration
aishell integration create my-monitoring-tool \
  --type webhook \
  --url https://monitoring.example.com/api/events \
  --headers '{"X-API-Key": "YOUR_KEY"}' \
  --events "*"

# Send custom event
aishell integration send my-monitoring-tool \
  --event custom.event \
  --data '{"message": "Custom event data"}'
```

---

## Best Practices

### Integration Monitoring

```bash
# Monitor integration health
aishell integration health

# Test all integrations
aishell integration test-all

# Integration usage statistics
aishell integration stats --period 30d
```

### Error Handling

```bash
# Configure retry logic
aishell integration configure \
  --retry-attempts 3 \
  --retry-delay 5s \
  --timeout 30s

# Configure fallback
aishell integration fallback \
  --primary slack \
  --fallback email \
  --on-failure-notify pagerduty
```

### Documentation

```bash
# Generate integration documentation
aishell integration document \
  --output integration-docs.md \
  --include-examples
```

---

## Next Steps

- Review [Monitoring & Analytics](./MONITORING_ANALYTICS.md)
- Check [Security Best Practices](./SECURITY_BEST_PRACTICES.md)
- See [Troubleshooting Guide](../TROUBLESHOOTING.md)

---

*Last Updated: 2024-01-15 | Version: 1.0.0*
