# AI-Shell Features Guide

Complete guide to all 10 production-ready features in AI-Shell.

## Table of Contents

1. [AI Query Optimizer](#1-ai-query-optimizer)
2. [Health Dashboard with Alerts](#2-health-dashboard-with-alerts)
3. [Backup/Recovery System](#3-backuprecovery-system)
4. [Query Federation](#4-query-federation)
5. [Schema Designer](#5-schema-designer)
6. [Query Caching](#6-query-caching)
7. [Migration Tester](#7-migration-tester)
8. [SQL Explainer](#8-sql-explainer)
9. [Schema Diff Tool](#9-schema-diff-tool)
10. [Cost Optimizer](#10-cost-optimizer)

---

## 1. AI Query Optimizer

Auto-detect slow queries, suggest indexes, and rewrite queries using Claude AI.

### Commands

```bash
# Optimize a specific query
ai-shell optimize "SELECT * FROM users WHERE email = 'test@example.com'"

# Analyze slow queries from log
ai-shell analyze-slow-queries

# Get query statistics
ai-shell query-stats
```

### Features

- **Automatic Query Analysis**: Uses Claude to analyze query structure and execution plans
- **Index Recommendations**: Suggests optimal indexes based on query patterns
- **Query Rewriting**: Provides optimized versions of queries
- **Slow Query Detection**: Automatically logs and analyzes slow queries
- **Performance Estimation**: Estimates improvement from optimizations

### Configuration

```json
{
  "slowQueryThreshold": 1000,
  "autoOptimize": false,
  "logSlowQueries": true
}
```

### Example Output

```
🔍 Analyzing query...

Original Query:
SELECT * FROM orders WHERE user_id = 123 AND status = 'pending'

Issues Found:
  • Full table scan detected
  • Missing index on user_id column
  • SELECT * pulls unnecessary data

Suggestions:
  • Create composite index on (user_id, status)
  • Select only required columns
  • Consider adding LIMIT clause

Optimized Query:
SELECT id, user_id, status, created_at
FROM orders
WHERE user_id = 123 AND status = 'pending'
LIMIT 100

Index Recommendations:
  • CREATE INDEX idx_orders_user_status ON orders(user_id, status)

Estimated Improvement: 85% faster with index
```

---

## 2. Health Dashboard with Alerts

Real-time monitoring with Slack/email alerts and threshold configuration.

### Commands

```bash
# Perform health check
ai-shell health-check

# Start continuous monitoring
ai-shell monitor

# Configure alerts
ai-shell alerts setup --slack-webhook "https://hooks.slack.com/..."
ai-shell alerts setup --email "admin@example.com"

# Set custom thresholds
ai-shell alerts threshold --response-time 500 --cpu 75
```

### Features

- **Real-time Metrics**: Monitor CPU, memory, connections, query performance
- **Multi-channel Alerts**: Slack, email, webhook notifications
- **Custom Thresholds**: Configure alerts per metric
- **Alert History**: Track and resolve alerts
- **Performance Trends**: Historical data analysis

### Configuration

```json
{
  "enabled": true,
  "monitoringInterval": 5000,
  "alerts": {
    "enabled": true,
    "channels": {
      "slack": {
        "enabled": true,
        "webhookUrl": "https://hooks.slack.com/..."
      }
    },
    "thresholds": {
      "responseTime": 1000,
      "errorRate": 5,
      "cpuUsage": 80
    }
  }
}
```

### Example Output

```
💊 Performing health check...

┌────────────────────────────┬────────────────────┬──────────────┐
│ Metric                     │ Value              │ Status       │
├────────────────────────────┼────────────────────┼──────────────┤
│ Active Connections         │ 15 connections     │ healthy      │
│ Response Time              │ 45 ms              │ healthy      │
│ Error Rate                 │ 0 %                │ healthy      │
│ CPU Usage                  │ 42 %               │ healthy      │
│ Memory Usage               │ 68 %               │ healthy      │
│ Active Queries             │ 3 queries          │ healthy      │
└────────────────────────────┴────────────────────┴──────────────┘
```

---

## 3. Backup/Recovery System

Automated scheduling, point-in-time recovery, multi-database support.

### Commands

```bash
# Create manual backup
ai-shell backup

# Schedule automated backups (daily at 2 AM)
ai-shell backup schedule "0 2 * * *"

# List all backups
ai-shell backup list

# Restore from backup
ai-shell restore <backup-id>

# Dry run restore (no changes)
ai-shell restore <backup-id> --dry-run

# Delete old backups
ai-shell backup cleanup --older-than 30
```

### Features

- **Multi-Database Support**: PostgreSQL, MySQL, SQLite, MongoDB
- **Automated Scheduling**: Cron-based scheduling
- **Compression**: Automatic backup compression
- **Retention Policies**: Automatic cleanup of old backups
- **Point-in-Time Recovery**: Restore to specific timestamp
- **S3 Support**: Upload backups to S3
- **Incremental Backups**: Reduce backup time and storage

### Configuration

```json
{
  "enabled": true,
  "schedule": "0 2 * * *",
  "retention": 30,
  "compression": true,
  "location": "local",
  "localPath": "./backups"
}
```

### Example Output

```
💾 Creating backup...

✅ Backup completed!
  ID: backup-1234567890-abc123
  Database: myapp_production
  Size: 245.67 MB
  Duration: 3452ms
  Location: ./backups/backup-1234567890-abc123.tar.gz
```

---

## 4. Query Federation

Execute queries across multiple databases with AI-powered query planning.

### Commands

```bash
# Execute federated query
ai-shell federate "SELECT u.name, o.total FROM db1.users u JOIN db2.orders o ON u.id = o.user_id" --dbs db1,db2

# Cross-database join
ai-shell join db1:users db2:orders --on "users.id = orders.user_id"

# Clear federation cache
ai-shell federate cache clear
```

### Features

- **Cross-Database Joins**: Join PostgreSQL with MongoDB
- **AI Query Planning**: Optimal execution strategy
- **Parallel Execution**: Execute independent queries in parallel
- **Result Caching**: Cache intermediate results
- **Smart Data Transfer**: Minimize data movement
- **Multi-Database Support**: Mix different database types

### Example

```
🔗 Executing federated query...

Query: Get users and their orders from different databases

Execution Plan:
  Step 1: Fetch users from PostgreSQL (database1)
  Step 2: Fetch orders from MySQL (database2)
  Step 3: Perform in-memory join on user_id

✅ Query completed in 1245ms
  Steps: 3
  Results: 1,543 rows
```

---

## 5. Schema Designer

AI-assisted interactive schema design with automatic migration generation.

### Commands

```bash
# Interactive schema design
ai-shell design-schema

# Validate schema file
ai-shell validate-schema schemas/users.json

# Generate migrations
ai-shell generate-migration schemas/users.json

# Apply schema to database
ai-shell apply-schema schemas/users.json
```

### Features

- **Interactive Design**: AI-guided schema creation
- **Best Practices**: Follows database normalization rules
- **Auto Validation**: Checks for common issues
- **Migration Generation**: Auto-generate SQL migrations
- **Multi-Database**: Supports PostgreSQL, MySQL, SQLite, MongoDB
- **Relationship Mapping**: Define foreign keys and constraints

### Example Session

```
🎨 AI-Powered Schema Designer

Schema name: ecommerce
Describe your schema: An e-commerce platform with users, products, orders, and payments

Generating schema...

📋 Generated Schema:
{
  "tables": [
    {
      "name": "users",
      "columns": [
        {"name": "id", "type": "integer", "primaryKey": true},
        {"name": "email", "type": "varchar(255)", "unique": true},
        {"name": "created_at", "type": "timestamp"}
      ]
    },
    ...
  ]
}

Would you like to refine this schema? (y/n)
```

---

## 6. Query Caching

Redis-based caching with smart invalidation (50-70% load reduction).

### Commands

```bash
# Enable caching
ai-shell cache enable

# Configure Redis
ai-shell cache enable --redis-url "redis://localhost:6379"

# View cache statistics
ai-shell cache stats

# Clear cache
ai-shell cache clear

# Invalidate specific table
ai-shell cache invalidate users

# Warm up cache
ai-shell cache warmup queries.sql
```

### Features

- **Redis Backend**: High-performance caching
- **Automatic Invalidation**: Smart cache invalidation on data changes
- **TTL Management**: Configurable expiration
- **Cache Statistics**: Hit rate, memory usage
- **Fallback Mode**: Local in-memory cache if Redis unavailable
- **Selective Caching**: Cache only specific queries

### Configuration

```json
{
  "enabled": true,
  "ttl": 3600,
  "maxSize": 10485760,
  "redisUrl": "redis://localhost:6379",
  "invalidationStrategy": "smart"
}
```

### Example Output

```
📊 Cache Statistics

  Hits: 1,543
  Misses: 287
  Hit Rate: 84.32%
  Total Keys: 156
  Memory Used: 24.5 MB
  Evictions: 12
```

---

## 7. Migration Tester

Test migrations before production with rollback simulation.

### Commands

```bash
# Test migration file
ai-shell test-migration migrations/001_create_users.sql

# Validate migration
ai-shell validate-migration migrations/001_create_users.sql

# Batch test multiple migrations
ai-shell test-migrations migrations/*.sql

# Generate test report
ai-shell test-report --output report.md
```

### Features

- **Isolated Testing**: Creates temporary test database
- **Rollback Testing**: Verifies down migrations work
- **Idempotency Check**: Ensures migrations can run safely twice
- **Performance Testing**: Measures migration duration
- **Schema Validation**: Validates resulting schema
- **Comprehensive Reports**: Detailed test results

### Example Output

```
🧪 Testing migration: 001_create_users.sql

Status: PASSED
Duration: 234ms

Test Results:
✓ Migration applies successfully (89ms)
✓ Schema validation (12ms)
✓ Rollback works (45ms)
✓ Re-apply after rollback (67ms)
✓ Idempotency check (18ms)
✓ Performance check (3ms)
```

---

## 8. SQL Explainer

SQL to English and English to SQL translation using Claude.

### Commands

```bash
# Explain SQL query
ai-shell explain "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id"

# Translate natural language to SQL
ai-shell translate "show me all users who placed orders in the last 30 days"

# Interactive learning mode
ai-shell explain --interactive
```

### Features

- **SQL to English**: Clear explanations of complex queries
- **English to SQL**: Generate SQL from natural language
- **Query Breakdown**: Step-by-step explanation
- **Multiple Alternatives**: Suggest alternative queries
- **Confidence Scoring**: AI confidence in translations
- **Learning Mode**: Interactive SQL learning

### Example

```
📝 Query:
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.created_at > NOW() - INTERVAL '30 days'
GROUP BY u.id
HAVING COUNT(o.id) > 5
ORDER BY order_count DESC

💡 Explanation:
This query finds users who have placed more than 5 orders in the last 30 days,
showing their names and order counts, sorted by most active first.

📊 Complexity: medium
⚡ Performance: Good - uses indexed join

💭 Suggestions:
  1. Add index on orders.created_at for faster filtering
  2. Consider adding LIMIT for pagination
```

---

## 9. Schema Diff Tool

Compare schemas and auto-generate sync migrations.

### Commands

```bash
# Compare two databases
ai-shell diff production staging

# Generate sync migration
ai-shell diff production staging --generate-migration

# Apply sync migration
ai-shell sync-schema staging production

# Export diff report
ai-shell diff production staging --export report.md
```

### Features

- **Complete Comparison**: Tables, columns, indexes, constraints
- **Migration Generation**: Auto-generate sync SQL
- **Safety Checks**: Detect dangerous operations
- **Multi-Database**: Compare different database types
- **Detailed Reports**: Comprehensive diff reports
- **Bidirectional Sync**: Sync in either direction

### Example Output

```
🔍 Comparing schemas: production vs staging

Summary:
  Tables Added: 2
  Tables Removed: 0
  Tables Modified: 3
  Columns Added: 5
  Columns Removed: 1
  Columns Modified: 2
  Indexes Added: 3
  Indexes Removed: 0

Table Differences:

### payments (added)
  New table for payment processing

### users (modified)
  - Column phone: added
  - Column last_login: modified (nullable changed)
```

---

## 10. Cost Optimizer

Analyze AWS/GCP/Azure costs and provide AI-powered optimization recommendations.

### Commands

```bash
# Analyze current costs
ai-shell analyze-costs --provider AWS --region us-east-1

# Get optimization recommendations
ai-shell optimize-costs

# View cost trends
ai-shell cost-trends --period 30

# Generate cost report
ai-shell cost-report --output report.pdf
```

### Features

- **Cloud Provider Integration**: AWS, GCP, Azure support
- **Cost Breakdown**: Compute, storage, backup, transfer
- **AI Recommendations**: Claude-powered optimization suggestions
- **Savings Estimation**: Calculate potential savings
- **Right-Sizing**: Instance size recommendations
- **Storage Optimization**: Compression, tiering suggestions
- **Trend Analysis**: Historical cost tracking

### Configuration

```json
{
  "enabled": true,
  "provider": {
    "name": "AWS",
    "region": "us-east-1"
  },
  "analysisInterval": "weekly"
}
```

### Example Output

```
💰 Analyzing costs...

Current Monthly Costs:
  Compute: $250
  Storage: $50
  Backup: $15
  Data Transfer: $30
  Total: $345

💡 Potential Savings: $127/month
   Annual Savings: $1,524

Recommendations (5):

1. Right-size database instance
   Savings: $75/month | Priority: high
   Current CPU utilization is only 35%, consider downsizing from
   db.m5.2xlarge to db.m5.xlarge

2. Enable database compression
   Savings: $20/month | Priority: medium
   Compression can reduce storage costs by 40-60%

3. Implement data archival policy
   Savings: $15/month | Priority: low
   Archive data older than 1 year to S3 Glacier
```

---

## Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY="your-api-key"

# Optional
export AI_SHELL_CONFIG="./config/features.config.json"
export REDIS_URL="redis://localhost:6379"
export LOG_LEVEL="info"
```

## Quick Start

1. **Install dependencies**:
```bash
npm install
```

2. **Configure API key**:
```bash
export ANTHROPIC_API_KEY="your-key"
```

3. **Connect to database**:
```bash
ai-shell connect postgres://localhost/mydb
```

4. **Use any feature**:
```bash
ai-shell optimize "SELECT * FROM users"
ai-shell health-check
ai-shell backup
```

## Best Practices

1. **Always test in staging first**
2. **Monitor after applying optimizations**
3. **Schedule regular backups**
4. **Review cost analysis monthly**
5. **Keep query cache enabled for read-heavy workloads**
6. **Test migrations before production deployment**

## Support

For issues or questions:
- GitHub: https://github.com/your-org/ai-shell
- Documentation: https://docs.ai-shell.dev
- Email: support@ai-shell.dev
