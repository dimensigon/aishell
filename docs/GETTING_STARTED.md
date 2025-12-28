# Getting Started with AI-Shell

Welcome to AI-Shell! This guide will help you get up and running in 5 minutes.

## Table of Contents

- [5-Minute Quick Start](#5-minute-quick-start)
- [First Connection](#first-connection)
- [First Query](#first-query)
- [Basic Workflows](#basic-workflows)
- [Common Use Cases](#common-use-cases)
- [Tips & Best Practices](#tips--best-practices)
- [Next Steps](#next-steps)

## 5-Minute Quick Start

### Step 1: Install AI-Shell

```bash
# Install globally via npm
npm install -g ai-shell

# Verify installation
ai-shell --version
```

### Step 2: Set Up Environment

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"

# Optional: Set default database URL
export DATABASE_URL="postgres://localhost:5432/mydb"
```

### Step 3: Connect to Database

```bash
# Connect to PostgreSQL
ai-shell connect postgres://localhost:5432/mydb --name local

# Verify connection
ai-shell connections
```

### Step 4: Run Your First Command

```bash
# Check database health
ai-shell health-check

# Optimize a query
ai-shell optimize "SELECT * FROM users WHERE active = true"
```

Congratulations! You're now using AI-Shell.

## First Connection

### Interactive Connection Setup

AI-Shell supports multiple connection methods:

#### Method 1: Connection String (Recommended)

```bash
# PostgreSQL
ai-shell connect postgres://user:password@localhost:5432/database --name production

# MySQL
ai-shell connect mysql://root:password@localhost:3306/database --name mysql-db

# MongoDB
ai-shell connect mongodb://localhost:27017/database --name mongo-db

# Redis
ai-shell connect redis://localhost:6379 --name cache

# SQLite
ai-shell connect sqlite:///path/to/database.db --name sqlite-db
```

#### Method 2: Test Connection First

```bash
# Test before saving
ai-shell connect postgres://localhost:5432/mydb --test

# If successful, save the connection
ai-shell connect postgres://localhost:5432/mydb --name local
```

#### Method 3: Using Environment Variables

```bash
# Set DATABASE_URL
export DATABASE_URL="postgres://localhost:5432/mydb"

# Connect using environment variable
ai-shell connect $DATABASE_URL --name production
```

### Managing Connections

```bash
# List all connections
ai-shell connections

# Show detailed connection info
ai-shell connections --verbose

# Check connection health
ai-shell connections --health

# Switch active connection
ai-shell use production

# Disconnect from a database
ai-shell disconnect local

# Disconnect from all databases
ai-shell disconnect
```

## First Query

### Simple Query Execution

```bash
# Run a SELECT query
ai-shell query "SELECT * FROM users LIMIT 10"

# Query with specific connection
ai-shell query "SELECT * FROM users" --connection production

# Output in JSON format
ai-shell query "SELECT * FROM users" --format json

# Output to file
ai-shell query "SELECT * FROM users" --output users.json
```

### Query Optimization

```bash
# Optimize a query before running
ai-shell optimize "SELECT * FROM users WHERE created_at > NOW() - INTERVAL '7 days'"

# Show execution plan
ai-shell optimize "SELECT * FROM users u JOIN orders o ON u.id = o.user_id" --explain

# Test query without execution
ai-shell optimize "DELETE FROM users WHERE active = false" --dry-run
```

### Natural Language Queries (In Development)

```bash
# Coming soon: Natural language to SQL
# ai-shell query "Show me all active users from last week"
# ai-shell query "Count orders by status"
```

## Basic Workflows

### Workflow 1: Connect to Database

**Goal**: Establish a connection to your database

```bash
# Step 1: Test connection
ai-shell connect postgres://localhost:5432/mydb --test

# Step 2: Save connection if successful
ai-shell connect postgres://localhost:5432/mydb --name local --set-active

# Step 3: Verify health
ai-shell health-check

# Expected output:
# ✅ Database Health: Healthy
# Connection: local
# Latency: 12ms
# Active Connections: 1
# Database Size: 45.3 MB
```

### Workflow 2: Execute Queries

**Goal**: Run queries and view results in different formats

```bash
# Simple query
ai-shell query "SELECT * FROM users LIMIT 5"

# JSON output for automation
ai-shell query "SELECT id, name, email FROM users" --format json > users.json

# CSV output for spreadsheets
ai-shell query "SELECT * FROM orders WHERE created_at > '2025-01-01'" --format csv > orders.csv

# Table format (default, human-readable)
ai-shell query "SELECT product, SUM(amount) FROM sales GROUP BY product" --format table
```

### Workflow 3: Use Query Builder

**Goal**: Build complex queries interactively

```bash
# Start query builder
ai-shell query-builder

# Interactive prompts:
# 1. Select table: users
# 2. Select columns: id, name, email, created_at
# 3. Add WHERE clause: active = true
# 4. Add ORDER BY: created_at DESC
# 5. Add LIMIT: 10

# Generated query:
# SELECT id, name, email, created_at
# FROM users
# WHERE active = true
# ORDER BY created_at DESC
# LIMIT 10

# Execute or save the query
```

### Workflow 4: Monitor Performance

**Goal**: Track database health and performance

```bash
# One-time health check
ai-shell health-check

# Continuous monitoring
ai-shell monitor --interval 5000

# View slow queries
ai-shell analyze-slow-queries --threshold 500

# Show performance metrics
ai-shell perf pool  # Connection pool stats
```

### Workflow 5: Optimize Queries

**Goal**: Improve query performance

```bash
# Step 1: Identify slow queries
ai-shell analyze-slow-queries

# Output:
# 🐌 Found 3 slow queries:
# ⏱️  2,345ms (12x)
#    SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE active = true)
#    💡 Suggestions:
#       - Add index on orders(user_id)
#       - Rewrite as JOIN instead of subquery

# Step 2: Analyze specific query
ai-shell optimize "SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE active = true)"

# Step 3: Apply recommendations
ai-shell execute "CREATE INDEX idx_orders_user_id ON orders(user_id)"

# Step 4: Verify improvement
ai-shell optimize "SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE active = true)"
```

### Workflow 6: Create Backups

**Goal**: Back up your database safely

```bash
# Create immediate backup
ai-shell backup --connection production

# Output:
# ✅ Backup created successfully
# Backup ID: backup-1730098800-abc123
# Size: 125.4 MB
# Duration: 12.3s
# Location: ~/.ai-shell/backups/

# List backups
ai-shell backup-list

# Restore from backup (with dry-run first)
ai-shell restore backup-1730098800-abc123 --dry-run

# Actual restore
ai-shell restore backup-1730098800-abc123
```

## Common Use Cases

### Use Case 1: Daily Health Check

**Scenario**: Monitor database health every morning

```bash
#!/bin/bash
# daily-health-check.sh

# Connect to production database
ai-shell use production

# Run health check
ai-shell health-check

# Check for slow queries
ai-shell analyze-slow-queries --threshold 1000

# Get connection pool stats
ai-shell perf pool

# Export report
ai-shell health-check --format json > reports/health-$(date +%Y-%m-%d).json
```

### Use Case 2: Data Export for Analysis

**Scenario**: Export data for analytics team

```bash
# Export users to CSV
ai-shell query "SELECT * FROM users WHERE created_at >= '2025-10-01'" \
  --format csv \
  --output exports/users-october.csv

# Export orders to JSON
ai-shell query "SELECT * FROM orders WHERE status = 'completed'" \
  --format json \
  --output exports/completed-orders.json

# Export with specific columns
ai-shell query "SELECT id, name, email, total_spent FROM customers ORDER BY total_spent DESC" \
  --format csv \
  --limit 1000 \
  --output exports/top-customers.csv
```

### Use Case 3: Database Comparison

**Scenario**: Compare production and staging schemas

```bash
# Compare schemas
ai-shell diff production staging

# Output shows differences:
# 🔍 Schema Differences
#
# Tables:
#   + new_feature_table (staging only)
#   - deprecated_table (production only)
#
# Columns in 'users':
#   + email_verified_at (staging only)
#   ~ status: VARCHAR(20) → VARCHAR(50) (type changed)
#
# Indexes:
#   + idx_users_email_verified (staging only)

# Generate migration SQL
ai-shell sync-schema production staging --dry-run > migration.sql

# Review and apply
cat migration.sql
ai-shell execute "$(cat migration.sql)" --connection production
```

### Use Case 4: Query Performance Investigation

**Scenario**: Investigate why a query is slow

```bash
# Step 1: Analyze the slow query
ai-shell explain "SELECT u.*, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2025-01-01'
GROUP BY u.id"

# Step 2: Review execution plan
# Output shows:
# - Seq Scan on users (cost: 1000)
# - Hash Join (cost: 5000)
# - GroupAggregate (cost: 2000)
# ⚠️  Missing index on users.created_at

# Step 3: Get optimization suggestions
ai-shell optimize "SELECT u.*, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2025-01-01'
GROUP BY u.id"

# Step 4: Apply suggested indexes
ai-shell execute "CREATE INDEX idx_users_created_at ON users(created_at)"

# Step 5: Verify improvement
ai-shell explain "SELECT u.*, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2025-01-01'
GROUP BY u.id"
```

### Use Case 5: Automated Reporting

**Scenario**: Generate daily sales report

```bash
#!/bin/bash
# daily-sales-report.sh

REPORT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="reports/sales-$REPORT_DATE.json"

# Connect to production
ai-shell use production

# Generate sales report
ai-shell query "
SELECT
  DATE(created_at) as sale_date,
  COUNT(*) as order_count,
  SUM(total) as revenue,
  AVG(total) as avg_order_value
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY sale_date DESC
" --format json --output "$REPORT_FILE"

# Send via email (example)
# cat "$REPORT_FILE" | mail -s "Daily Sales Report" team@company.com

echo "Report generated: $REPORT_FILE"
```

## Tips & Best Practices

### Performance Tips

1. **Use Query Caching**
```bash
# Enable Redis caching
ai-shell cache enable --redis redis://localhost:6379

# Check cache stats
ai-shell cache stats

# Clear cache when needed
ai-shell cache clear
```

2. **Limit Result Sets**
```bash
# Always use LIMIT for large tables
ai-shell query "SELECT * FROM large_table LIMIT 100"

# Use --limit flag
ai-shell query "SELECT * FROM users" --limit 50
```

3. **Use Indexes Wisely**
```bash
# Check existing indexes
ai-shell perf indexes

# Get recommendations
ai-shell perf indexes --recommendations
```

### Security Best Practices

1. **Use Vault for Credentials**
```bash
# Store password securely
ai-shell vault-add production "secret-password" --encrypt

# Connect using vault
ai-shell connect postgres://user@localhost:5432/db --name prod
# (password retrieved from vault automatically)
```

2. **Enable Audit Logging**
```bash
# Check audit log
ai-shell audit-show --limit 100

# Filter by user
ai-shell audit-show --user admin

# Export audit log
ai-shell audit-show --format json --output audit-report.json
```

3. **Use Read-Only Connections for Analysis**
```bash
# Create read-only user in database first
# Then connect with limited privileges
ai-shell connect postgres://readonly@localhost:5432/db --name analytics
```

### Workflow Best Practices

1. **Use Named Sessions**
```bash
# Start a session
ai-shell session start "data-migration-2025-10-28"

# Work normally...
ai-shell query "..."

# End session
ai-shell session end

# Review session later
ai-shell session list
```

2. **Save Contexts for Different Projects**
```bash
# Save current context
ai-shell context save "project-alpha" --include-all

# Switch projects
ai-shell context load "project-beta"

# Return to previous project
ai-shell context load "project-alpha"
```

3. **Use Dry-Run for Safety**
```bash
# Always dry-run destructive operations
ai-shell execute "DELETE FROM users WHERE inactive = true" --dry-run

# Review impact
ai-shell execute "UPDATE users SET status = 'archived'" --explain

# Then execute
ai-shell execute "DELETE FROM users WHERE inactive = true"
```

### Automation Tips

1. **Script Common Tasks**
```bash
# Create alias for common queries
alias daily-users="ai-shell query 'SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE'"

# Or use context
ai-shell context save daily-reports --include-aliases
```

2. **Use JSON Output for Parsing**
```bash
# Query to JSON
ai-shell query "SELECT * FROM users" --format json | jq '.rows[] | select(.active == true)'

# Pipe to other tools
ai-shell query "SELECT email FROM users" --format json | jq -r '.rows[].email' | xargs -I {} echo {}
```

3. **Set Up Cron Jobs**
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /usr/local/bin/ai-shell backup --connection production

# Hourly health check
0 * * * * /usr/local/bin/ai-shell health-check --format json >> /var/log/ai-shell-health.log
```

## Next Steps

### Learn More Features

1. **Query Optimization**
   - Read: [Query Optimization Tutorial](./tutorials/query-optimization.md)
   - Try: `ai-shell optimize "YOUR_SLOW_QUERY"`

2. **Performance Monitoring**
   - Read: [Performance Monitoring Tutorial](./tutorials/performance-monitoring.md)
   - Try: `ai-shell monitor --dashboard`

3. **Database Federation**
   - Read: [Database Federation Tutorial](./tutorials/database-federation.md)
   - Try: `ai-shell federate "SELECT * FROM db1.users JOIN db2.orders" --databases db1,db2`

4. **Schema Management**
   - Read: [Schema Migrations Tutorial](./tutorials/migrations.md)
   - Try: `ai-shell design-schema`

5. **Security Features**
   - Read: [Security Setup Guide](./tutorials/security.md)
   - Try: `ai-shell security-scan`

### Explore Advanced Features

```bash
# View all available commands
ai-shell --help

# View specific command help
ai-shell optimize --help

# List all features
ai-shell features

# View examples
ai-shell examples
```

### Join the Community

- **GitHub**: https://github.com/your-org/ai-shell
- **Discussions**: https://github.com/your-org/ai-shell/discussions
- **Issues**: https://github.com/your-org/ai-shell/issues
- **Discord**: https://discord.gg/ai-shell

### Get Help

```bash
# Built-in help
ai-shell --help
ai-shell <command> --help

# Documentation
ls docs/

# Tutorials
ls docs/tutorials/

# Examples
ai-shell examples
```

## Quick Reference Card

### Essential Commands

```bash
# Connection
ai-shell connect <url> --name <name>
ai-shell connections
ai-shell use <name>
ai-shell disconnect [name]

# Queries
ai-shell query "<sql>"
ai-shell optimize "<sql>"
ai-shell explain "<sql>"

# Monitoring
ai-shell health-check
ai-shell monitor
ai-shell analyze-slow-queries

# Backup
ai-shell backup
ai-shell backup-list
ai-shell restore <backup-id>

# Performance
ai-shell perf pool
ai-shell perf indexes
ai-shell perf slow-queries

# Security
ai-shell vault-add <name> <value> --encrypt
ai-shell audit-show
ai-shell security-scan

# Utilities
ai-shell features
ai-shell examples
ai-shell --help
```

### Global Flags

```bash
--format <type>     # Output format: json, table, csv
--output <file>     # Write output to file
--verbose           # Enable verbose logging
--explain           # Show AI explanation
--dry-run           # Simulate without changes
--limit <n>         # Limit result count
--timeout <ms>      # Set timeout
```

## Troubleshooting Quick Guide

### Connection Issues
```bash
# Test connection
ai-shell connect <url> --test

# Check health
ai-shell health-check

# View connection details
ai-shell connections --verbose
```

### Query Issues
```bash
# Analyze query
ai-shell explain "<query>"

# Optimize query
ai-shell optimize "<query>"

# Dry-run query
ai-shell query "<query>" --dry-run
```

### Performance Issues
```bash
# Check slow queries
ai-shell analyze-slow-queries

# Check connection pool
ai-shell perf pool

# Get index recommendations
ai-shell perf indexes
```

## Resources

- **[Installation Guide](./INSTALLATION.md)**: Complete installation instructions
- **[API Reference](./API_REFERENCE.md)**: Complete command reference
- **[Tutorials](./tutorials/)**: Step-by-step guides
- **[Security Policy](../SECURITY.md)**: Security best practices
- **[Contributing](../CONTRIBUTING.md)**: Contribution guidelines
- **[FAQ](./FAQ.md)**: Frequently asked questions

---

**Last Updated**: October 28, 2025
**Version**: 1.0.0

Need help? Open an issue at https://github.com/your-org/ai-shell/issues
