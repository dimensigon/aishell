# API Reference

Complete command-line reference for AI-Shell v1.0.0

## Table of Contents

- [Overview](#overview)
- [Global Options](#global-options)
- [Command Categories](#command-categories)
- [CLI Commands](#cli-commands)
- [MCP Tools](#mcp-tools)
- [Configuration Reference](#configuration-reference)
- [Return Types](#return-types)
- [Error Codes](#error-codes)

## Overview

AI-Shell provides 100+ CLI commands and 70+ MCP tools for comprehensive database management.

### Command Syntax

```bash
ai-shell [global-options] <command> [arguments] [command-options]
```

### Examples

```bash
# Basic command
ai-shell health-check

# With global options
ai-shell --verbose --format json query "SELECT * FROM users"

# With command options
ai-shell optimize "SELECT * FROM users" --explain --dry-run

# Chaining with pipes
ai-shell query "SELECT * FROM users" --format json | jq '.rows[]'
```

## Global Options

These options work with any command:

### Output Formatting

```bash
-f, --format <type>         Output format
                            Values: table, json, csv, xml
                            Default: table

-o, --output <file>         Write output to file instead of stdout
                            Example: --output result.json

--timestamps                Include timestamps in output

--limit <count>             Limit number of results
                            Example: --limit 100
```

### Logging & Debug

```bash
-v, --verbose               Enable verbose logging
                            Sets LOG_LEVEL=debug

-j, --json                  Output in JSON format (shorthand for --format json)

--explain                   Show AI explanation before execution
                            Works with: query, optimize, execute

--dry-run                   Simulate command without making changes
                            Recommended for destructive operations
```

### Configuration

```bash
-c, --config <path>         Path to configuration file
                            Default: ~/.ai-shell/config.yaml
                            Example: --config /etc/ai-shell/config.yaml

--timeout <ms>              Command timeout in milliseconds
                            Default: 120000 (2 minutes)
                            Max: 600000 (10 minutes)
                            Example: --timeout 60000
```

### Help & Version

```bash
-h, --help                  Show help information

-V, --version               Show version number

--examples                  Show usage examples for command
```

## Command Categories

AI-Shell commands are organized into these categories:

### Core Operations (Phase 1)
- [Query Optimization](#query-optimization-commands)
- [Health Monitoring](#health-monitoring-commands)
- [Backup & Recovery](#backup-commands)

### Advanced Features (Phase 2)
- [Query Federation](#query-federation-commands)
- [Schema Design](#schema-design-commands)
- [Query Caching](#caching-commands)

### Advanced Analysis (Phase 3)
- [Migration Testing](#migration-commands)
- [SQL Explanation](#sql-explainer-commands)
- [Schema Comparison](#schema-diff-commands)
- [Cost Optimization](#cost-optimization-commands)

### Database Management
- [Connection Management](#connection-commands)
- [Query Execution](#query-execution-commands)

### Security
- [Vault Management](#vault-commands)
- [Audit Logging](#audit-commands)
- [SSO Integration](#sso-commands)

### Context & Sessions
- [Context Management](#context-commands)
- [Session Management](#session-commands)

### Utilities
- [Performance Analysis](#performance-commands)
- [Query History](#history-commands)

## CLI Commands

### Connection Commands

#### `connect`

Connect to a database.

```bash
ai-shell connect <connection-string> [options]
```

**Arguments:**
- `connection-string` - Database connection URL

**Options:**
```bash
--name <name>               Connection name (auto-generated if not provided)
--test                      Test connection without saving
--set-active                Set as active connection (default: true)
```

**Supported Protocols:**
- `postgresql://` or `postgres://`
- `mysql://`
- `mongodb://` or `mongodb+srv://`
- `redis://` or `rediss://` (SSL)
- `sqlite://path/to/db.sqlite`

**Examples:**
```bash
# PostgreSQL
ai-shell connect postgresql://user:pass@localhost:5432/mydb --name production

# MySQL
ai-shell connect mysql://root:secret@localhost:3306/testdb

# MongoDB
ai-shell connect mongodb://localhost:27017/appdb --name mongo

# Redis
ai-shell connect redis://localhost:6379 --name cache

# Test connection
ai-shell connect postgresql://localhost/mydb --test

# From environment variable
ai-shell connect $DATABASE_URL --name prod
```

**Returns:**
```json
{
  "success": true,
  "message": "Connected to postgresql database: production",
  "connection": {
    "name": "production",
    "type": "postgresql",
    "database": "mydb",
    "host": "localhost",
    "port": 5432,
    "isConnected": true
  }
}
```

---

#### `disconnect`

Disconnect from database(s).

```bash
ai-shell disconnect [name]
```

**Arguments:**
- `name` - Connection name (disconnects all if not provided)

**Examples:**
```bash
# Disconnect specific connection
ai-shell disconnect production

# Disconnect all
ai-shell disconnect
```

**Returns:**
```json
{
  "success": true,
  "message": "Disconnected from production"
}
```

---

#### `connections`

List active database connections.

**Aliases:** `conns`

```bash
ai-shell connections [options]
```

**Options:**
```bash
--verbose                   Show detailed connection information
--health                    Run health checks on all connections
```

**Examples:**
```bash
# List connections
ai-shell connections

# Detailed information
ai-shell conns --verbose

# With health checks
ai-shell connections --health
```

**Returns:**
```
📊 Active Connections (3)

┌──────────────┬──────────────┬──────────┬────────────────────┬────────┬────────┐
│ Name         │ Type         │ Database │ Host:Port          │ Active │ Health │
├──────────────┼──────────────┼──────────┼────────────────────┼────────┼────────┤
│ production   │ postgresql   │ mydb     │ localhost:5432     │ ✓      │ ✓ 12ms │
│ cache        │ redis        │ 0        │ localhost:6379     │        │ ✓ 3ms  │
│ analytics    │ mongodb      │ logs     │ cluster.mongo:27017│        │ ✓ 45ms │
└──────────────┴──────────────┴──────────┴────────────────────┴────────┴────────┘
```

---

#### `use`

Switch active database connection.

```bash
ai-shell use <connection-name>
```

**Arguments:**
- `connection-name` - Name of connection to activate

**Examples:**
```bash
ai-shell use production
ai-shell use staging
```

**Returns:**
```
✅ Active connection switched to: production
```

---

### Query Optimization Commands

#### `optimize`

Optimize a SQL query using AI analysis.

**Aliases:** `opt`

```bash
ai-shell optimize <query> [options]
```

**Arguments:**
- `query` - SQL query to optimize

**Options:**
```bash
--explain                   Show query execution plan
--dry-run                   Validate without executing
--format <type>             Output format (text, json)
```

**Examples:**
```bash
# Basic optimization
ai-shell optimize "SELECT * FROM users WHERE id > 100"

# With execution plan
ai-shell opt "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id" --explain

# Dry run for validation
ai-shell optimize "DELETE FROM users" --dry-run
```

**Returns:**
```
📊 Query Optimization Analysis

Original Query:
SELECT * FROM users WHERE id > 100

Risk Level: LOW
Estimated Execution Time: 45ms
Estimated Cost: 125.5

⚠️  Potential Issues:
  • Using SELECT * (retrieves all columns)
  • Missing index on 'id' column

💡 Optimizations:
  1. Specify explicit columns instead of *
  2. Add index: CREATE INDEX idx_users_id ON users(id)
  3. Consider adding WHERE clause limit

✨ Optimized Query:
SELECT id, name, email FROM users
WHERE id > 100
LIMIT 1000

Expected Improvement: 35% faster, 60% less memory
```

---

#### `analyze-slow-queries`

Analyze and optimize slow queries from log.

**Aliases:** `slow`

```bash
ai-shell analyze-slow-queries [options]
```

**Options:**
```bash
-t, --threshold <ms>        Minimum execution time in ms (default: 1000)
```

**Examples:**
```bash
ai-shell analyze-slow-queries
ai-shell slow --threshold 500
```

**Returns:**
```
🐌 Found 3 slow queries:

⏱️  2,345ms (12x)
   SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE active = true)
   💡 Suggestions:
      - Add index on orders(user_id)
      - Rewrite as JOIN instead of subquery

⏱️  1,567ms (8x)
   SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o GROUP BY u.id
   💡 Suggestions:
      - Add composite index on orders(user_id, id)
      - Use materialized view for frequent aggregations

⏱️  1,234ms (25x)
   SELECT * FROM logs WHERE created_at > NOW() - INTERVAL '30 days'
   💡 Suggestions:
      - Add index on logs(created_at)
      - Consider partitioning by date
      - Archive old data
```

---

### Health Monitoring Commands

#### `health-check`

Perform comprehensive database health check.

**Aliases:** `health`

```bash
ai-shell health-check [options]
```

**Options:**
```bash
--connection <name>         Check specific connection
```

**Examples:**
```bash
ai-shell health-check
ai-shell health --json
ai-shell health-check --connection production
```

**Returns:**
```
🏥 Database Health Check

Overall Status: ✅ HEALTHY

Connection: production (postgresql)
┌─────────────────────┬──────────┬─────────┐
│ Metric              │ Value    │ Status  │
├─────────────────────┼──────────┼─────────┤
│ Response Time       │ 12ms     │ ✓ Good  │
│ Active Connections  │ 8/100    │ ✓ Good  │
│ Database Size       │ 2.3 GB   │ ✓ OK    │
│ Cache Hit Ratio     │ 98.5%    │ ✓ Great │
│ Slow Queries/hour   │ 3        │ ⚠ Review│
│ Replication Lag     │ 0ms      │ ✓ Good  │
│ Disk Usage          │ 45%      │ ✓ OK    │
│ Memory Usage        │ 62%      │ ✓ OK    │
└─────────────────────┴──────────┴─────────┘

⚠️  Recommendations:
  • 3 slow queries detected - run 'ai-shell analyze-slow-queries'
  • Consider adding indexes on frequently queried columns
```

---

#### `monitor`

Start real-time database monitoring.

```bash
ai-shell monitor [options]
```

**Options:**
```bash
-i, --interval <ms>         Monitoring interval in milliseconds (default: 5000)
```

**Examples:**
```bash
ai-shell monitor
ai-shell monitor --interval 10000
ai-shell monitor -i 3000
```

**Output** (updates in real-time):
```
┌─────────────────────────────────────────────────┐
│          DATABASE MONITORING                    │
│          production (postgresql)                │
│          Last updated: 10:23:45                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  Queries/sec:  ████████░░  42 qps              │
│  Connections:  ████░░░░░░  12/100              │
│  CPU Usage:    ██████░░░░  58%                 │
│  Memory:       ████████░░  82%                 │
│  Disk I/O:     ███░░░░░░░  320 MB/s            │
│                                                 │
│  Active Queries: 3                             │
│  Slow Queries:   1                             │
│  Cache Hit:      98.5%                         │
│  Avg Response:   45ms                          │
│                                                 │
│  Press 'q' to quit                             │
└─────────────────────────────────────────────────┘
```

---

#### `alerts setup`

Configure health monitoring alerts.

```bash
ai-shell alerts setup [options]
```

**Options:**
```bash
-s, --slack <webhook>       Slack webhook URL
-e, --email <addresses>     Email addresses (comma-separated)
-w, --webhook <url>         Custom webhook URL
```

**Examples:**
```bash
ai-shell alerts setup --slack https://hooks.slack.com/services/T00/B00/XXX
ai-shell alerts setup --email admin@company.com,ops@company.com
ai-shell alerts setup --webhook https://api.company.com/alerts
```

**Returns:**
```
✅ Alerts configured successfully

Channels:
  • Slack: enabled (webhook configured)
  • Email: enabled (2 recipients)

Alert Triggers:
  • High CPU usage (>80%)
  • Low disk space (<10%)
  • Slow queries (>5/hour)
  • Connection pool exhaustion
  • Replication lag (>1s)
```

---

### Backup Commands

#### `backup`

Create database backup.

```bash
ai-shell backup [options]
```

**Options:**
```bash
-c, --connection <name>     Connection name (uses active if not specified)
```

**Examples:**
```bash
ai-shell backup
ai-shell backup --connection production
ai-shell backup -c staging
```

**Returns:**
```
📦 Creating Database Backup...

Connection: production
Database: mydb (postgresql)
Size: 125.4 MB

Progress: ████████████████████ 100%

✅ Backup completed successfully

Backup ID: backup-1730098800-abc123
Duration: 12.3 seconds
Compression: gzip
Location: ~/.ai-shell/backups/backup-1730098800-abc123.sql.gz

To restore: ai-shell restore backup-1730098800-abc123
```

---

#### `restore`

Restore database from backup.

```bash
ai-shell restore <backup-id> [options]
```

**Arguments:**
- `backup-id` - ID of backup to restore

**Options:**
```bash
-d, --dry-run               Simulate restore without making changes
```

**Examples:**
```bash
ai-shell restore backup-1730098800-abc123
ai-shell restore backup-1730098800-abc123 --dry-run
```

**Returns:**
```
🔄 Restoring Database Backup

Backup ID: backup-1730098800-abc123
Created: 2025-10-28 10:00:00
Size: 125.4 MB
Database: mydb

⚠️  WARNING: This will overwrite the current database!

Continue? [y/N]: y

Progress: ████████████████████ 100%

✅ Restore completed successfully

Duration: 18.7 seconds
Rows restored: 1,234,567
Tables restored: 45

Database is now ready.
```

---

#### `backup-list`

List all backups.

**Aliases:** `backups`

```bash
ai-shell backup-list [options]
```

**Options:**
```bash
-l, --limit <count>         Maximum number of backups to show (default: 20)
```

**Examples:**
```bash
ai-shell backup-list
ai-shell backups --limit 10
```

**Returns:**
```
📋 Available Backups

┌────────────────────────────┬──────────────┬──────────┬─────────────────────┐
│ Backup ID                  │ Database     │ Size     │ Created             │
├────────────────────────────┼──────────────┼──────────┼─────────────────────┤
│ backup-1730098800-abc123   │ mydb         │ 125.4 MB │ 2025-10-28 10:00:00 │
│ backup-1730012400-def456   │ mydb         │ 124.8 MB │ 2025-10-27 10:00:00 │
│ backup-1729926000-ghi789   │ mydb         │ 123.2 MB │ 2025-10-26 10:00:00 │
└────────────────────────────┴──────────────┴──────────┴─────────────────────┘

Total backups: 30
Total size: 3.7 GB
```

---

### Query Federation Commands

#### `federate`

Execute query across multiple databases.

**Aliases:** `fed`

```bash
ai-shell federate <query> [options]
```

**Arguments:**
- `query` - SQL query with database.table notation

**Options:**
```bash
-d, --databases <list>      Comma-separated list of database names (required)
--explain                   Show execution plan
--dry-run                   Validate without executing
```

**Examples:**
```bash
# Join across databases
ai-shell federate "SELECT * FROM db1.users u JOIN db2.orders o ON u.id = o.user_id" --databases db1,db2

# Multiple databases
ai-shell fed "SELECT * FROM users" --databases production,staging,analytics

# With execution plan
ai-shell federate "SELECT * FROM users" -d db1,db2 --explain
```

**Returns:**
```
🔗 Federated Query Execution

Databases: db1 (postgresql), db2 (mysql)
Strategy: Hash Join

Execution Plan:
  1. Fetch from db1.users (estimated: 10,000 rows)
  2. Fetch from db2.orders (estimated: 50,000 rows)
  3. Perform hash join on user_id
  4. Apply filters and sort

Estimated time: 1.2s
Estimated data transfer: 15.3 MB

Results: 8,456 rows
Execution time: 1.34s
Data transferred: 16.1 MB
```

---

### Schema Design Commands

#### `design-schema`

Interactive schema design with AI assistance.

**Aliases:** `design`

```bash
ai-shell design-schema
```

**Interactive Flow:**
```
🎨 AI-Powered Schema Designer

What would you like to design?
> e-commerce product catalog

Analyzing requirements...

💡 Suggested Tables:

1. products
   - id (PRIMARY KEY)
   - name (VARCHAR(255), NOT NULL)
   - description (TEXT)
   - price (DECIMAL(10,2), NOT NULL)
   - category_id (INTEGER, FOREIGN KEY)
   - created_at (TIMESTAMP)
   - updated_at (TIMESTAMP)

2. categories
   - id (PRIMARY KEY)
   - name (VARCHAR(100), UNIQUE, NOT NULL)
   - parent_id (INTEGER, FOREIGN KEY, NULLABLE)

3. inventory
   - product_id (PRIMARY KEY, FOREIGN KEY)
   - quantity (INTEGER, NOT NULL, DEFAULT 0)
   - warehouse_id (INTEGER, FOREIGN KEY)
   - last_updated (TIMESTAMP)

4. prices
   - id (PRIMARY KEY)
   - product_id (INTEGER, FOREIGN KEY)
   - price (DECIMAL(10,2), NOT NULL)
   - effective_date (DATE, NOT NULL)
   - end_date (DATE)

💡 Suggested Indexes:
   - CREATE INDEX idx_products_category ON products(category_id)
   - CREATE INDEX idx_products_price ON products(price)
   - CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id)

Apply this schema? [y/N]:
```

---

#### `validate-schema`

Validate schema definition file.

**Aliases:** `validate`

```bash
ai-shell validate-schema <file>
```

**Arguments:**
- `file` - Path to schema definition file (JSON/YAML)

**Examples:**
```bash
ai-shell validate-schema schema.json
ai-shell validate ./schemas/users.json
```

**Schema File Format:**
```json
{
  "tables": [
    {
      "name": "users",
      "columns": [
        {
          "name": "id",
          "type": "INTEGER",
          "primaryKey": true,
          "autoIncrement": true
        },
        {
          "name": "email",
          "type": "VARCHAR(255)",
          "unique": true,
          "notNull": true
        }
      ],
      "indexes": [
        {
          "name": "idx_users_email",
          "columns": ["email"]
        }
      ]
    }
  ]
}
```

**Returns:**
```
✅ Schema Validation: PASSED

Tables: 3
Columns: 24
Indexes: 7
Foreign Keys: 5

✓ No naming conflicts
✓ All foreign keys reference existing columns
✓ No circular dependencies
✓ All data types valid
✓ Indexes properly defined

Schema is ready to apply.
```

---

### Caching Commands

#### `cache enable`

Enable query caching.

```bash
ai-shell cache enable [options]
```

**Options:**
```bash
-r, --redis <url>           Redis connection URL
```

**Examples:**
```bash
ai-shell cache enable
ai-shell cache enable --redis redis://localhost:6379
```

---

#### `cache stats`

Show cache statistics.

```bash
ai-shell cache stats
```

**Returns:**
```
📊 Query Cache Statistics

Status: Enabled
Provider: Redis (localhost:6379)

Metrics:
  Cache Hit Rate:    87.3%
  Total Queries:     12,456
  Cache Hits:        10,874
  Cache Misses:      1,582
  Cached Entries:    3,421
  Total Cache Size:  45.2 MB
  Avg Query Time:    23ms (cached: 3ms, uncached: 145ms)

Top Cached Queries:
  1. SELECT * FROM users WHERE active = true (234 hits)
  2. SELECT COUNT(*) FROM orders (189 hits)
  3. SELECT * FROM products WHERE category_id = 5 (156 hits)
```

---

#### `cache clear`

Clear all cached queries.

```bash
ai-shell cache clear
```

**Returns:**
```
✅ Cache cleared

Entries removed: 3,421
Space freed: 45.2 MB
```

---

### Migration Commands

#### `test-migration`

Test migration file in isolated environment.

**Aliases:** `test-mig`

```bash
ai-shell test-migration <file> [options]
```

**Arguments:**
- `file` - Path to migration file

**Options:**
```bash
-c, --connection <name>     Connection to test against
```

**Examples:**
```bash
ai-shell test-migration migrations/001_add_users.sql
ai-shell test-mig ./migrations/002_alter_orders.sql
```

**Returns:**
```
🧪 Testing Migration

File: migrations/001_add_users.sql
Connection: test_db (copy of production)

Analyzing migration...
  ✓ Syntax valid
  ✓ No destructive operations
  ✓ Foreign keys valid
  ✓ Indexes properly defined

Creating test environment...
  ✓ Database copied
  ✓ Test user created

Applying migration...
  ✓ CREATE TABLE users
  ✓ CREATE INDEX idx_users_email
  ✓ INSERT default data

Validation:
  ✓ All tables created
  ✓ All indexes created
  ✓ Data integrity maintained
  ✓ No errors

Performance:
  Execution time: 0.234s
  Rows affected: 0
  Size increase: +1.2 MB

✅ Migration test PASSED

Safe to apply to production.
```

---

### SQL Explainer Commands

#### `explain`

Get AI-powered explanation of SQL query.

**Aliases:** `exp`

```bash
ai-shell explain <query> [options]
```

**Arguments:**
- `query` - SQL query to explain

**Options:**
```bash
--format <type>             Output format (text, json)
--analyze                   Include performance analysis
--dry-run                   Validate query without execution
```

**Examples:**
```bash
ai-shell explain "SELECT * FROM users WHERE created_at > NOW() - INTERVAL 7 DAY"
ai-shell exp "SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o GROUP BY u.id"
ai-shell explain "SELECT * FROM users" --format json
```

**Returns:**
```
📖 SQL Query Explanation

Query:
SELECT u.name, u.email, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > NOW() - INTERVAL '7 days'
GROUP BY u.id, u.name, u.email
ORDER BY order_count DESC
LIMIT 10

Plain English:
This query finds the top 10 users who joined in the last 7 days,
ranked by how many orders they've placed, showing their name, email,
and order count.

Execution Steps:
  1. Filter users created in last 7 days
  2. Join with orders table to count orders per user
  3. Group results by user
  4. Sort by order count (highest first)
  5. Return top 10 results

Performance Analysis:
  • Uses index: idx_users_created_at
  • Left join ensures users with 0 orders are included
  • Grouping required for COUNT aggregation
  • Limit reduces result set

Estimated Cost: 285.5
Estimated Rows: 10
Estimated Time: 45ms

💡 Optimization Tips:
  • Good use of specific columns instead of SELECT *
  • Index on users.created_at is beneficial
  • Consider materializing if run frequently
```

---

#### `translate`

Convert natural language to SQL.

**Aliases:** `nl2sql`

```bash
ai-shell translate <natural-language>
```

**Arguments:**
- `natural-language` - Query description in plain English

**Examples:**
```bash
ai-shell translate "Show me all users created in the last week"
ai-shell nl2sql "Count orders by user for active users"
```

**Returns:**
```
🤖 Natural Language to SQL

Input: "Show me all users created in the last week"

Generated SQL:
SELECT *
FROM users
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY created_at DESC;

Confidence: 95%

Assumptions:
  • "last week" = past 7 days
  • Results sorted by creation date (newest first)
  • All columns included

Execute this query? [y/N]:
```

---

### Schema Diff Commands

#### `diff`

Compare schemas between two databases.

```bash
ai-shell diff <db1> <db2> [options]
```

**Arguments:**
- `db1` - First database name
- `db2` - Second database name

**Options:**
```bash
-o, --output <file>         Output diff to file
-f, --format <type>         Output format (text, json, sql)
```

**Examples:**
```bash
ai-shell diff production staging
ai-shell diff db1 db2 --output schema-diff.json --format json
```

**Returns:**
```
🔍 Schema Comparison: production vs staging

Tables:
  + new_feature_table (staging only)
  - deprecated_table (production only)

Columns in 'users':
  + email_verified_at TIMESTAMP (staging only)
  + phone VARCHAR(20) (staging only)
  - old_status VARCHAR(20) (production only)
  ~ status: VARCHAR(20) → VARCHAR(50) (type changed)

Indexes:
  + idx_users_email_verified (staging only)
  + idx_users_phone (staging only)
  - idx_users_old_status (production only)

Foreign Keys:
  + users.organization_id → organizations.id (staging only)

Summary:
  Tables added: 1
  Tables removed: 1
  Columns added: 8
  Columns removed: 3
  Columns modified: 2
  Indexes added: 5
  Indexes removed: 2
```

---

### Cost Optimization Commands

#### `analyze-costs`

Analyze database costs and get optimization recommendations.

**Aliases:** `costs`

```bash
ai-shell analyze-costs <provider> <region> [options]
```

**Arguments:**
- `provider` - Cloud provider (aws, gcp, azure)
- `region` - Cloud region (us-east-1, us-central1, etc.)

**Options:**
```bash
-d, --detailed              Show detailed breakdown
```

**Examples:**
```bash
ai-shell analyze-costs aws us-east-1
ai-shell costs gcp us-central1 --detailed
ai-shell analyze-costs azure eastus
```

**Returns:**
```
💰 Cloud Database Cost Analysis

Provider: AWS
Region: us-east-1
Current Instance: db.r5.xlarge

Current Costs (Monthly):
  Instance:           $438.00
  Storage:            $115.00 (500 GB GP2)
  IOPS:               $65.00
  Backup Storage:     $25.00
  Data Transfer:      $45.00
  ────────────────────────────
  Total:              $688.00/month

💡 Optimization Recommendations:

1. Rightsizing (High Impact)
   Current: db.r5.xlarge (4 vCPU, 32 GB RAM)
   Recommended: db.r5.large (2 vCPU, 16 GB RAM)
   Reason: Current CPU usage: 25%, RAM usage: 45%
   Savings: $219/month (50% reduction)

2. Storage Optimization (Medium Impact)
   Current: 500 GB GP2
   Recommended: 300 GB GP3
   Reason: Current usage: 280 GB, GP3 cheaper
   Savings: $45/month

3. Reserved Instance (High Impact)
   Current: On-demand pricing
   Recommended: 1-year reserved instance
   Reason: Consistent workload
   Savings: $131/month (30% reduction)

4. Backup Optimization (Low Impact)
   Current: 7-day retention
   Recommended: 7-day + lifecycle to Glacier
   Savings: $15/month

Total Potential Savings: $410/month (60% reduction)
New Monthly Cost: $278

Would you like to:
  1. See detailed breakdown
  2. Generate migration plan
  3. Export recommendations

Choice [1-3]:
```

---

### Query Execution Commands

#### `query`

Execute a SELECT query.

```bash
ai-shell query <sql> [options]
```

**Arguments:**
- `sql` - SQL SELECT query

**Options:**
```bash
--connection <name>         Connection name (uses active if not specified)
--params <json>             Query parameters as JSON array
```

**Examples:**
```bash
ai-shell query "SELECT * FROM users LIMIT 10"
ai-shell query "SELECT * FROM users WHERE id = $1" --params '[123]'
ai-shell query "SELECT * FROM orders" --connection production --format json
```

**Returns:**
```
Query: SELECT * FROM users LIMIT 10
Rows: 10
Execution time: 23ms

┌────┬────────────┬─────────────────────┬──────────────────────┐
│ id │ name       │ email               │ created_at           │
├────┼────────────┼─────────────────────┼──────────────────────┤
│ 1  │ John Doe   │ john@example.com    │ 2025-10-15 14:23:01  │
│ 2  │ Jane Smith │ jane@example.com    │ 2025-10-16 09:45:22  │
│ 3  │ Bob Wilson │ bob@example.com     │ 2025-10-17 11:12:33  │
└────┴────────────┴─────────────────────┴──────────────────────┘
```

---

#### `execute`

Execute DDL/DML statements.

```bash
ai-shell execute <sql> [options]
```

**Arguments:**
- `sql` - SQL statement (INSERT, UPDATE, DELETE, CREATE, etc.)

**Options:**
```bash
--connection <name>         Connection name
--params <json>             Statement parameters as JSON array
```

**Examples:**
```bash
ai-shell execute "CREATE TABLE test (id INT, name VARCHAR(50))"
ai-shell execute "INSERT INTO users (name, email) VALUES ($1, $2)" --params '["John", "john@example.com"]'
ai-shell execute "UPDATE users SET status = 'active' WHERE id = 123"
```

**Returns:**
```
✅ Statement executed successfully

Affected rows: 1
Execution time: 12ms
```

---

### Vault Commands

#### `vault-add`

Add credential to secure vault.

```bash
ai-shell vault-add <name> <value> [options]
```

**Arguments:**
- `name` - Credential name/identifier
- `value` - Credential value

**Options:**
```bash
--encrypt                   Encrypt the value (recommended)
```

**Examples:**
```bash
ai-shell vault-add prod-db "password123" --encrypt
ai-shell vault-add api-key "sk-1234567890" --encrypt
```

**Returns:**
```
🔐 Credential Stored Securely

Name: prod-db
Encrypted: Yes
Algorithm: AES-256-GCM
Storage: ~/.ai-shell/vault/credentials.enc

✅ Credential added to vault
```

---

#### `vault-list`

List all vault entries.

```bash
ai-shell vault-list [options]
```

**Options:**
```bash
--show-passwords            Show actual passwords (use with caution)
--format <type>             Output format (json, table)
```

**Examples:**
```bash
ai-shell vault-list
ai-shell vault-list --format json
```

**Returns:**
```
🔐 Vault Entries

┌────────────┬───────────┬──────────────────────┬───────────┐
│ Name       │ Type      │ Created              │ Encrypted │
├────────────┼───────────┼──────────────────────┼───────────┤
│ prod-db    │ password  │ 2025-10-28 10:00:00  │ Yes       │
│ api-key    │ token     │ 2025-10-28 11:30:00  │ Yes       │
│ staging-db │ password  │ 2025-10-27 14:15:00  │ Yes       │
└────────────┴───────────┴──────────────────────┴───────────┘

Total entries: 3
```

---

### Audit Commands

#### `audit-show`

Show audit log entries.

```bash
ai-shell audit-show [options]
```

**Options:**
```bash
--limit <n>                 Limit entries (default: 100)
--user <user>               Filter by user
--from <date>               Start date (YYYY-MM-DD)
--to <date>                 End date (YYYY-MM-DD)
```

**Examples:**
```bash
ai-shell audit-show --limit 50
ai-shell audit-show --user admin
ai-shell audit-show --from 2025-10-01 --to 2025-10-31
```

**Returns:**
```
📋 Audit Log (Last 100 entries)

┌──────────────────────┬────────┬────────────┬─────────┬────────────┐
│ Timestamp            │ User   │ Operation  │ Target  │ Result     │
├──────────────────────┼────────┼────────────┼─────────┼────────────┤
│ 2025-10-28 14:23:01  │ admin  │ QUERY      │ users   │ SUCCESS    │
│ 2025-10-28 14:22:45  │ admin  │ CONNECT    │ prod-db │ SUCCESS    │
│ 2025-10-28 14:20:15  │ dev    │ QUERY      │ orders  │ SUCCESS    │
│ 2025-10-28 14:19:03  │ dev    │ LOGIN      │ -       │ SUCCESS    │
│ 2025-10-28 14:15:22  │ admin  │ BACKUP     │ prod-db │ SUCCESS    │
└──────────────────────┴────────┴────────────┴─────────┴────────────┘
```

---

### Security Commands

#### `security-scan`

Run security scan.

```bash
ai-shell security-scan [options]
```

**Options:**
```bash
--deep                      Deep scan (more thorough)
```

**Examples:**
```bash
ai-shell security-scan
ai-shell security-scan --deep
```

**Returns:**
```
🔒 Security Scan Report

Scan Type: Standard
Duration: 5.3 seconds

✅ Passed Checks (12):
  ✓ SQL injection prevention active
  ✓ Credentials encrypted in vault
  ✓ TLS enabled for connections
  ✓ Audit logging enabled
  ✓ Rate limiting configured
  ✓ Session timeout configured
  ✓ No hardcoded passwords found
  ✓ RBAC enabled
  ✓ Input validation active
  ✓ Error messages sanitized
  ✓ Backup encryption enabled
  ✓ Secure random generation

⚠️  Warnings (2):
  ⚠ 2 database users have excessive privileges
  ⚠ Password policy could be stronger

❌ Failed Checks (0):

Overall Score: 92/100 (Good)

Recommendations:
  1. Review database user privileges
  2. Implement stronger password policy (12+ chars, complexity)
  3. Consider enabling MFA (in development)
```

---

### SSO Commands

#### `sso configure`

Configure SSO provider.

```bash
ai-shell sso configure <provider> [options]
```

**Arguments:**
- `provider` - Provider name

**Options:**
```bash
--template <type>           Use provider template (okta, auth0, azure-ad, google)
```

**Examples:**
```bash
ai-shell sso configure okta-prod --template okta
ai-shell sso configure auth0-prod --template auth0
```

---

#### `sso login`

Authenticate with SSO provider.

```bash
ai-shell sso login [provider]
```

**Arguments:**
- `provider` - Provider name (uses default if not specified)

**Examples:**
```bash
ai-shell sso login
ai-shell sso login okta-prod
```

---

#### `sso status`

Show current SSO status.

```bash
ai-shell sso status
```

**Returns:**
```
🔐 SSO Status

Authentication: Authenticated
Provider: okta-prod
User: john.doe@company.com
Roles: developer, analyst

Session:
  ID: abc123xyz789
  Created: 2025-10-28 09:00:00
  Expires: 2025-10-28 17:00:00 (7h 45m remaining)

Permissions:
  • Read database
  • Write database
  • Run queries
  • Create backups
```

---

### Context Commands

#### `context save`

Save current context.

```bash
ai-shell context save <name> [options]
```

**Arguments:**
- `name` - Context name

**Options:**
```bash
-d, --description <text>    Context description
--include-history           Include query history
--include-aliases           Include aliases
--include-config            Include configuration
--include-variables         Include variables
--include-connections       Include connection info
```

**Examples:**
```bash
ai-shell context save my-project --description "Production analysis"
ai-shell context save dev-env --include-history --include-config
```

---

#### `context load`

Load saved context.

```bash
ai-shell context load <name> [options]
```

**Arguments:**
- `name` - Context name

**Options:**
```bash
--merge                     Merge with current context
```

**Examples:**
```bash
ai-shell context load my-project
ai-shell context load dev-env --merge
```

---

#### `context list`

List all saved contexts.

```bash
ai-shell context list [options]
```

**Options:**
```bash
-v, --verbose               Show detailed information
-f, --format <type>         Output format (table, json)
```

**Examples:**
```bash
ai-shell context list
ai-shell context list --verbose
```

---

### Session Commands

#### `session start`

Start a new session.

```bash
ai-shell session start <name>
```

**Arguments:**
- `name` - Session name

**Examples:**
```bash
ai-shell session start debug-session
ai-shell session start production-analysis
```

---

#### `session end`

End current session.

```bash
ai-shell session end
```

---

#### `session list`

List all sessions.

```bash
ai-shell session list [options]
```

**Options:**
```bash
-f, --format <type>         Output format (table, json)
```

---

### Performance Commands

#### `perf pool`

Show connection pool statistics.

```bash
ai-shell perf pool
```

**Returns:**
```
🔗 Connection Pool Statistics

Total Connections: 10
Active: 3
Idle: 7
Waiting Queries: 0

Average Wait Time: 0ms
Max Wait Time: 0ms
Pool Utilization: 30%

Status: ✅ Healthy
```

---

#### `perf slow-queries`

Show slow queries.

```bash
ai-shell perf slow-queries [options]
```

**Options:**
```bash
-t, --threshold <ms>        Slow query threshold (default: 1000)
-l, --limit <n>             Number of queries to show (default: 10)
```

---

#### `perf indexes`

Suggest missing indexes.

```bash
ai-shell perf indexes
```

**Returns:**
```
📊 Index Recommendations

1. users.email
   Current: No index
   Suggested: CREATE INDEX idx_users_email ON users(email)
   Reason: Frequently used in WHERE clauses (234 times)
   Impact: 45% query time reduction

2. orders.user_id
   Current: No index
   Suggested: CREATE INDEX idx_orders_user_id ON orders(user_id)
   Reason: Used in JOINs and WHERE clauses (189 times)
   Impact: 60% query time reduction

3. products.category_id
   Current: No index
   Suggested: CREATE INDEX idx_products_category ON products(category_id)
   Reason: Frequently filtered (156 times)
   Impact: 30% query time reduction
```

---

### History Commands

#### `history list`

Show recent query history.

```bash
ai-shell history list [options]
```

**Options:**
```bash
-l, --limit <n>             Number of queries to show (default: 20)
-o, --offset <n>            Offset for pagination (default: 0)
```

**Examples:**
```bash
ai-shell history list
ai-shell history list --limit 50
```

---

#### `history search`

Search query logs.

```bash
ai-shell history search <pattern> [options]
```

**Arguments:**
- `pattern` - Search pattern (regex)

**Options:**
```bash
-i, --ignore-case           Case insensitive search
-l, --limit <n>             Limit results (default: 10)
```

**Examples:**
```bash
ai-shell history search "SELECT.*users"
ai-shell history search "DELETE" --ignore-case
```

---

### Utility Commands

#### `features`

List all available features.

```bash
ai-shell features
```

**Returns:**
```
📋 AI-Shell Features (10 Total)

Phase 1 - Core Operations:
  1. ✓ Query Optimizer      - AI-powered SQL optimization
  2. ✓ Health Monitor       - Real-time database monitoring
  3. ✓ Backup System        - Automated backup and recovery

Phase 2 - Advanced Features:
  4. ✓ Query Federation     - Cross-database queries
  5. ✓ Schema Designer      - AI-powered schema design
  6. ✓ Query Cache          - Redis-based query caching

Phase 3 - Advanced Analysis:
  7. ✓ Migration Tester     - Test migrations safely
  8. ✓ SQL Explainer        - Natural language explanations
  9. ✓ Schema Diff          - Compare database schemas
 10. ✓ Cost Optimizer       - Cloud cost optimization
```

---

#### `examples`

Show usage examples.

```bash
ai-shell examples
```

---

#### `dashboard`

Launch interactive performance dashboard.

```bash
ai-shell dashboard [options]
```

**Options:**
```bash
-i, --interval <seconds>    Update interval (default: 5)
```

**Example:**
```bash
ai-shell dashboard --interval 10
```

---

## MCP Tools

AI-Shell provides 70+ MCP (Model Context Protocol) tools for database operations via the MCP server.

### Starting MCP Server

```bash
# Start MCP server
ai-shell-mcp-server

# Or use via npx
npx ai-shell mcp start
```

### Common Database Tools

#### `db_connect`

Connect to a database.

**Input Schema:**
```json
{
  "name": "production",
  "type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "pass",
  "ssl": true,
  "poolSize": 10
}
```

**Returns:**
```json
{
  "success": true,
  "message": "Connected to postgresql database: production",
  "connection": {
    "name": "production",
    "type": "postgresql",
    "database": "mydb",
    "host": "localhost",
    "port": 5432,
    "isConnected": true
  }
}
```

---

#### `db_disconnect`

Disconnect from database.

**Input Schema:**
```json
{
  "name": "production"
}
```

---

#### `db_list_connections`

List all active connections.

**Input Schema:**
```json
{}
```

**Returns:**
```json
{
  "success": true,
  "connections": [
    {
      "name": "production",
      "type": "postgresql",
      "database": "mydb",
      "host": "localhost",
      "port": 5432,
      "isActive": true
    }
  ],
  "statistics": {
    "totalConnections": 1,
    "healthyConnections": 1,
    "activeConnection": "production"
  }
}
```

---

#### `db_query`

Execute SELECT query.

**Input Schema:**
```json
{
  "sql": "SELECT * FROM users WHERE id = $1",
  "params": [123],
  "connection": "production"
}
```

**Returns:**
```json
{
  "success": true,
  "rowCount": 1,
  "rows": [
    {
      "id": 123,
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "query": "SELECT * FROM users WHERE id = $1"
}
```

---

#### `db_execute`

Execute DDL/DML statement.

**Input Schema:**
```json
{
  "sql": "UPDATE users SET status = $1 WHERE id = $2",
  "params": ["active", 123],
  "connection": "production"
}
```

---

#### `db_federated_query`

Execute cross-database query.

**Input Schema:**
```json
{
  "query": "SELECT u.* FROM db1.users u JOIN db2.orders o ON u.id = o.user_id",
  "explain": false,
  "cache": true
}
```

**Returns:**
```json
{
  "success": true,
  "rows": [...],
  "rowCount": 8456,
  "executionTime": 1340,
  "plan": {
    "id": "plan-abc123",
    "databases": ["db1", "db2"],
    "steps": 4,
    "strategy": "hash-join",
    "estimatedCost": 1250.5
  },
  "statistics": {
    "totalDataTransferred": 16777216,
    "queriesExecuted": 2,
    "cacheHits": 0,
    "cacheMisses": 2
  }
}
```

---

### PostgreSQL Tools

#### `pg_query`

Execute PostgreSQL-specific query.

#### `pg_list_tables`

List all tables in schema.

#### `pg_describe_table`

Get table schema.

#### `pg_list_indexes`

List table indexes.

#### `pg_explain`

Get query execution plan.

#### `pg_vacuum`

Run VACUUM operation.

#### `pg_analyze`

Run ANALYZE operation.

---

### MySQL Tools

#### `mysql_query`

Execute MySQL query.

#### `mysql_show_tables`

List all tables.

#### `mysql_describe_table`

Show table structure.

#### `mysql_show_indexes`

Show table indexes.

#### `mysql_explain`

Get query execution plan.

---

### MongoDB Tools

#### `mongo_find`

Find documents in collection.

#### `mongo_insert`

Insert document(s).

#### `mongo_update`

Update document(s).

#### `mongo_delete`

Delete document(s).

#### `mongo_aggregate`

Run aggregation pipeline.

#### `mongo_list_collections`

List all collections.

#### `mongo_create_index`

Create index on collection.

---

### Redis Tools

#### `redis_get`

Get value by key.

#### `redis_set`

Set key-value pair.

#### `redis_delete`

Delete key(s).

#### `redis_keys`

List keys matching pattern.

#### `redis_info`

Get Redis server info.

---

## Configuration Reference

### Configuration File Format

Location: `~/.ai-shell/config.yaml`

```yaml
# Complete configuration example

databases:
  production:
    type: postgresql
    host: localhost
    port: 5432
    database: mydb
    username: user
    # Password stored in vault
    ssl:
      enabled: true
      rejectUnauthorized: true
      ca: /path/to/ca.pem
    poolSize: 10
    connectionTimeout: 30000

llm:
  provider: anthropic
  model: claude-3-sonnet-20240229
  temperature: 0.1
  maxTokens: 4096
  apiKey: ${ANTHROPIC_API_KEY}

security:
  vault:
    enabled: true
    encryption: aes-256-gcm
    keyDerivation: pbkdf2
    iterations: 100000
  audit:
    enabled: true
    destination: ~/.ai-shell/logs/audit.log
    rotation: daily
    retention: 90
  rbac:
    enabled: true
    defaultRole: viewer
  sql_injection_prevention: true
  rateLimit:
    enabled: true
    windowMs: 900000
    maxRequests: 100

query:
  timeout: 30000
  slowQueryThreshold: 1000
  maxResultSize: 10000
  defaultLimit: 100

monitoring:
  enabled: true
  interval: 5000
  metrics:
    - cpu
    - memory
    - connections
    - queryCount
  alerts:
    enabled: true

cache:
  enabled: true
  provider: redis
  ttl: 3600
  maxSize: 100

logging:
  level: info
  format: json
  destination: file
  file:
    path: ~/.ai-shell/logs
    maxSize: 10485760
    maxFiles: 10
```

---

## Return Types

### Success Response

```typescript
{
  success: true,
  message?: string,
  data?: any
}
```

### Error Response

```typescript
{
  success: false,
  error: string,
  code: number,
  details?: any
}
```

### Query Result

```typescript
{
  success: true,
  rowCount: number,
  rows: Array<Record<string, any>>,
  query: string,
  executionTime?: number
}
```

### Health Check Result

```typescript
{
  success: boolean,
  connection: string,
  healthy: boolean,
  latency?: number,
  error?: string,
  metrics?: {
    activeConnections: number,
    databaseSize: string,
    cacheHitRatio: number
  }
}
```

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 1000 | CONNECTION_ERROR | Failed to connect to database |
| 1001 | QUERY_ERROR | Query execution failed |
| 1002 | TIMEOUT_ERROR | Operation timed out |
| 1003 | AUTHENTICATION_ERROR | Authentication failed |
| 1004 | AUTHORIZATION_ERROR | Insufficient permissions |
| 1005 | VALIDATION_ERROR | Input validation failed |
| 1006 | NOT_FOUND | Resource not found |
| 1007 | SQL_INJECTION | SQL injection attempt detected |
| 1008 | RATE_LIMIT | Rate limit exceeded |
| 1009 | INTERNAL_ERROR | Internal server error |

---

## Exit Codes

| Code | Description |
|------|-------------|
| 0    | Success |
| 1    | General error |
| 2    | Connection error |
| 3    | Query error |
| 4    | Configuration error |
| 5    | Authentication error |
| 126  | Command not found |
| 127  | Permission denied |
| 130  | Process terminated (Ctrl+C) |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key (required) | - |
| `DATABASE_URL` | Default database connection URL | - |
| `REDIS_URL` | Redis connection URL for caching | `redis://localhost:6379` |
| `AI_SHELL_CONFIG` | Path to configuration file | `~/.ai-shell/config.yaml` |
| `AI_SHELL_LOG_LEVEL` | Logging level | `info` |
| `AI_SHELL_LOG_PATH` | Log file path | `~/.ai-shell/logs` |
| `AI_SHELL_QUERY_TIMEOUT` | Query timeout (ms) | `30000` |
| `AI_SHELL_MAX_CONNECTIONS` | Max database connections | `10` |

---

## Performance Considerations

### Query Limits

- Default result limit: 100 rows
- Maximum result limit: 10,000 rows
- Query timeout: 30 seconds (configurable)

### Connection Pooling

- Default pool size: 10
- Maximum pool size: 100
- Connection timeout: 30 seconds
- Idle timeout: 10 minutes

### Caching

- Default TTL: 1 hour
- Maximum cache size: 100 MB
- Cache invalidation: Automatic on write operations

---

## Support

- **Documentation**: https://github.com/your-org/ai-shell
- **Issues**: https://github.com/your-org/ai-shell/issues
- **Discussions**: https://github.com/your-org/ai-shell/discussions
- **Email**: support@ai-shell.dev

---

**Last Updated**: October 28, 2025
**Version**: 1.0.0
