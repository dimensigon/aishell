# AI-Shell CLI Command Reference

> **⚠️ Implementation Status**: AI-Shell currently implements **10 core features** with standalone CLI commands.
> Most interactive REPL features are planned for future releases. This document reflects current implementation.

Complete command-line interface reference for AI-Shell, covering all available commands, options, and usage examples.

## Command Availability Legend

- ✅ **Available** - Fully implemented and tested
- 🚧 **Partial** - Core functionality works, some options planned
- 📋 **Planned** - Coming in future release
- 🔄 **REPL Only** - Works in interactive mode only (not yet exposed as CLI)

## Table of Contents

- [Quick Reference](#quick-reference)
- [Global Options](#global-options)
- [Phase 1: Core Commands](#phase-1-core-commands)
- [Phase 2: Advanced Features](#phase-2-advanced-features)
- [Phase 3: Advanced Analysis](#phase-3-advanced-analysis)
- [Planned Features](#planned-features)
- [Advanced Usage](#advanced-usage)

---

## Quick Reference

**Currently Available Commands:**

```bash
# Phase 1 - Query Optimization
ai-shell optimize "SELECT * FROM users"                    # ✅ AI-powered query optimization
ai-shell analyze-slow-queries                              # ✅ Analyze slow queries

# Phase 1 - Health Monitoring
ai-shell health-check                                      # ✅ Database health check
ai-shell monitor --interval 5000                           # ✅ Real-time monitoring
ai-shell alerts setup --slack <webhook>                    # ✅ Configure alerts

# Phase 1 - Backup & Recovery
ai-shell backup --connection production                    # ✅ Create backup
ai-shell restore backup-123 --dry-run                      # ✅ Restore from backup
ai-shell backup-list                                       # ✅ List backups

# Phase 2 - Federation & Schema
ai-shell federate "SELECT * FROM users" --databases db1,db2  # ✅ Cross-DB queries
ai-shell design-schema                                     # ✅ AI schema design
ai-shell validate-schema schema.json                       # ✅ Validate schema

# Phase 2 - Query Cache
ai-shell cache enable --redis redis://localhost:6379       # ✅ Enable caching
ai-shell cache stats                                       # ✅ Cache statistics
ai-shell cache clear                                       # ✅ Clear cache

# Phase 3 - Analysis Tools
ai-shell test-migration migrations/001.sql                 # ✅ Test migration
ai-shell explain "SELECT * FROM users WHERE id > 100"      # ✅ SQL explanation
ai-shell translate "show users from last week"             # ✅ Natural language to SQL
ai-shell diff production staging                           # ✅ Schema comparison
ai-shell analyze-costs aws us-east-1                       # ✅ Cost analysis

# Utility Commands
ai-shell features                                          # ✅ List all features
ai-shell examples                                          # ✅ Show examples
ai-shell interactive                                       # 📋 Interactive mode (coming soon)
```

---

## Global Options

Global options can be used with any command:

```bash
--verbose, -v            # ✅ Verbose output (enable debug logging)
--json, -j               # ✅ Output results in JSON format
--config <path>          # ✅ Path to configuration file
--version                # ✅ Show version information
--help, -h               # ✅ Show help information
```

**Examples:**

```bash
ai-shell --verbose optimize "SELECT * FROM orders"
ai-shell --json health-check
ai-shell --config ~/.ai-shell-prod.yaml backup
ai-shell --help
```

---

## Phase 1: Core Commands

### Query Optimization

#### `optimize <query>` ✅

AI-powered SQL query optimization with detailed analysis.

```bash
ai-shell optimize <query> [options]
```

**Options:**
- `--verbose, -v` - Show detailed analysis
- `--json` - Output in JSON format

**Examples:**

```bash
# Optimize a query
ai-shell optimize "SELECT * FROM users WHERE status = 'active'"

# With verbose output
ai-shell optimize "SELECT * FROM orders JOIN users" --verbose

# JSON output for scripting
ai-shell optimize "SELECT * FROM large_table" --json
```

**Output Example:**

```
🔍 Analyzing query...

Original Query:
SELECT * FROM orders WHERE status = 'pending'

Issues Found:
  • Using SELECT * (retrieving unnecessary columns)
  • Missing index on 'status' column
  • Full table scan detected

Optimized Query:
SELECT id, user_id, total, created_at
FROM orders
WHERE status = 'pending'

Index Recommendations:
  • CREATE INDEX idx_orders_status ON orders(status)

Estimated Improvement: 12.3x faster
```

---

#### `analyze-slow-queries` ✅

Analyze and optimize slow queries from execution logs.

```bash
ai-shell analyze-slow-queries [options]
ai-shell slow [options]    # Alias
```

**Options:**
- `--threshold <ms>` - Minimum execution time (default: 1000ms)
- `--limit <n>` - Number of queries to analyze

**Examples:**

```bash
# Analyze slow queries
ai-shell analyze-slow-queries

# Custom threshold
ai-shell slow --threshold 500

# Analyze top 20
ai-shell analyze-slow-queries --limit 20
```

---

### Health Monitoring

#### `health-check` ✅

Perform comprehensive database health check.

```bash
ai-shell health-check [options]
ai-shell health [options]    # Alias
```

**Options:**
- `--json` - Output in JSON format

**Examples:**

```bash
# Basic health check
ai-shell health-check

# JSON output
ai-shell health --json
```

**Output Example:**

```
💊 Performing health check...

┌────────────────────────────┬──────────────┬─────────┐
│ Metric                     │ Value        │ Status  │
├────────────────────────────┼──────────────┼─────────┤
│ Connection Count           │ 23           │ healthy │
│ Active Queries             │ 5            │ healthy │
│ CPU Usage                  │ 45%          │ healthy │
│ Memory Usage               │ 2.3 GB       │ warning │
│ Disk Usage                 │ 67%          │ healthy │
│ Cache Hit Rate             │ 94%          │ healthy │
└────────────────────────────┴──────────────┴─────────┘
```

---

#### `monitor` ✅

Start real-time database performance monitoring.

```bash
ai-shell monitor [options]
```

**Options:**
- `--interval <ms>` - Update interval in milliseconds (default: 5000)

**Examples:**

```bash
# Start monitoring
ai-shell monitor

# Custom update interval (10 seconds)
ai-shell monitor --interval 10000

# Fast updates (3 seconds)
ai-shell monitor --interval 3000
```

Press `Ctrl+C` to stop monitoring.

---

#### `alerts setup` ✅

Configure health monitoring alerts.

```bash
ai-shell alerts setup [options]
```

**Options:**
- `--slack <webhook>` - Slack webhook URL
- `--email <addresses>` - Email addresses (comma-separated)
- `--webhook <url>` - Custom webhook URL

**Examples:**

```bash
# Configure Slack alerts
ai-shell alerts setup --slack https://hooks.slack.com/services/YOUR/WEBHOOK

# Configure email alerts
ai-shell alerts setup --email admin@company.com,ops@company.com

# Multiple channels
ai-shell alerts setup --slack <url> --email ops@company.com
```

---

### Backup & Recovery

#### `backup` ✅

Create database backup.

```bash
ai-shell backup [options]
```

**Options:**
- `--connection <name>` - Connection name (uses active if not specified)

**Examples:**

```bash
# Backup current connection
ai-shell backup

# Backup specific connection
ai-shell backup --connection production

# Backup with alias
ai-shell backup -c staging
```

**Output Example:**

```
💾 Creating backup...

✅ Backup completed!
  ID: backup-1730128547123
  Database: production
  Size: 45.23 MB
  Duration: 3421ms
  Location: /backups/backup-1730128547123.sql
```

---

#### `restore <backup-id>` ✅

Restore database from backup.

```bash
ai-shell restore <backup-id> [options]
```

**Options:**
- `--dry-run` - Simulate restore without making changes

**Examples:**

```bash
# Restore from backup
ai-shell restore backup-1730128547123

# Dry run (validation only)
ai-shell restore backup-1730128547123 --dry-run
```

---

#### `backup-list` ✅

List all available backups.

```bash
ai-shell backup-list [options]
ai-shell backups [options]    # Alias
```

**Options:**
- `--limit <count>` - Maximum number to show (default: 20)

**Examples:**

```bash
# List backups
ai-shell backup-list

# Show only 10 most recent
ai-shell backups --limit 10
```

---

## Phase 2: Advanced Features

### Query Federation

#### `federate <query>` ✅

Execute queries across multiple databases.

```bash
ai-shell federate <query> --databases <list> [options]
ai-shell fed <query> -d <list> [options]    # Alias
```

**Options:**
- `--databases <list>` - Comma-separated database names (required)

**Examples:**

```bash
# Query across multiple databases
ai-shell federate "SELECT * FROM users" --databases db1,db2,db3

# Cross-database join
ai-shell fed "SELECT u.*, o.* FROM users u JOIN orders o" -d production,analytics
```

---

### Schema Design

#### `design-schema` ✅

Interactive AI-powered schema design.

```bash
ai-shell design-schema [options]
ai-shell design [options]    # Alias
```

**Examples:**

```bash
# Start interactive schema design
ai-shell design-schema

# Using alias
ai-shell design
```

This launches an interactive session where you describe your data model and AI-Shell generates optimized schema definitions.

---

#### `validate-schema <file>` ✅

Validate schema definition file.

```bash
ai-shell validate-schema <file> [options]
ai-shell validate <file> [options]    # Alias
```

**Examples:**

```bash
# Validate schema file
ai-shell validate-schema schema.json

# Validate YAML schema
ai-shell validate ./schemas/users.yaml
```

**Output Example:**

```
✓ Validating schema: schema.json

✅ Schema is valid!

⚠️  Warnings:
  • Table 'orders' has no primary key defined
  • Column 'email' should have UNIQUE constraint

💡 Suggestions:
  • Add index on 'created_at' for time-based queries
  • Consider partitioning 'logs' table by date
```

---

### Query Cache

#### `cache enable` ✅

Enable Redis-based query caching.

```bash
ai-shell cache enable [options]
```

**Options:**
- `--redis <url>` - Redis connection URL

**Examples:**

```bash
# Enable cache with default settings
ai-shell cache enable

# Specify Redis URL
ai-shell cache enable --redis redis://localhost:6379

# Remote Redis
ai-shell cache enable --redis redis://cache-server:6379/0
```

---

#### `cache stats` ✅

Show cache statistics.

```bash
ai-shell cache stats [options]
```

**Examples:**

```bash
# View cache statistics
ai-shell cache stats

# JSON output
ai-shell cache stats --json
```

**Output Example:**

```
📊 Cache Statistics

  Hits: 1,234
  Misses: 89
  Hit Rate: 93.28%
  Total Keys: 456
  Memory Used: 12.45 MB
  Evictions: 23
```

---

#### `cache clear` ✅

Clear all cached queries.

```bash
ai-shell cache clear
```

**Examples:**

```bash
# Clear cache
ai-shell cache clear
```

---

## Phase 3: Advanced Analysis

### Migration Testing

#### `test-migration <file>` ✅

Test migration file in isolated environment before applying to production.

```bash
ai-shell test-migration <file> [options]
ai-shell test-mig <file> [options]    # Alias
```

**Options:**
- `--connection <name>` - Connection to test against

**Examples:**

```bash
# Test migration file
ai-shell test-migration migrations/001_add_users.sql

# Test against specific connection
ai-shell test-mig ./migrations/002_alter_orders.sql --connection staging
```

**Output Example:**

```
🧪 Testing migration: migrations/001_add_users.sql

Status: PASSED
Duration: 234ms

Test Results:
✓ Syntax validation (12ms)
✓ Schema integrity check (45ms)
✓ Data preservation test (123ms)
✓ Rollback test (54ms)
```

---

### SQL Explanation

#### `explain <query>` ✅

Get AI-powered natural language explanation of SQL query.

```bash
ai-shell explain <query> [options]
ai-shell exp <query> [options]    # Alias
```

**Examples:**

```bash
# Explain a query
ai-shell explain "SELECT * FROM users WHERE created_at > NOW() - INTERVAL 7 DAY"

# Explain complex query
ai-shell exp "SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o GROUP BY u.id"
```

**Output Example:**

```
🔍 SQL Explanation

Query Purpose:
This query retrieves all users who were created in the last 7 days.

Breakdown:
1. SELECT * FROM users - Retrieves all columns from the users table
2. WHERE created_at > NOW() - INTERVAL 7 DAY - Filters for records created within the past week
   - NOW() gets the current timestamp
   - INTERVAL 7 DAY subtracts 7 days

Performance Notes:
• Requires index on 'created_at' for optimal performance
• Uses full table scan if no index present

Suggestions:
• Consider selecting only needed columns instead of *
• Add index: CREATE INDEX idx_users_created_at ON users(created_at)
```

---

#### `translate <natural-language>` ✅

Convert natural language to SQL query.

```bash
ai-shell translate <natural-language> [options]
ai-shell nl2sql <natural-language> [options]    # Alias
```

**Examples:**

```bash
# Translate to SQL
ai-shell translate "Show me all users created in the last week"

# Complex query
ai-shell nl2sql "Count orders by user for active users"
```

**Output Example:**

```
🔄 Translating to SQL...

Generated SQL:
SELECT * FROM users
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC

Explanation:
This query selects all users created within the past 7 days, sorted by creation date in descending order (newest first).

Confidence: 95%

Alternatives:
  1. SELECT * FROM users WHERE created_at > CURRENT_DATE - 7
  2. SELECT * FROM users WHERE DATE(created_at) >= DATE_SUB(NOW(), INTERVAL 7 DAY)
```

---

### Schema Comparison

#### `diff <db1> <db2>` ✅

Compare schemas between two databases.

```bash
ai-shell diff <db1> <db2> [options]
```

**Options:**
- `--output <file>` - Save diff to file
- `--format <type>` - Output format: text, json, sql (default: text)

**Examples:**

```bash
# Compare schemas
ai-shell diff production staging

# Save to file
ai-shell diff prod dev --output schema-diff.json --format json

# Generate migration SQL
ai-shell diff staging production --format sql
```

**Output Example:**

```
🔍 Comparing schemas: production vs staging

Summary:
  Tables Added: 2
  Tables Removed: 0
  Tables Modified: 3
  Columns Added: 8
  Columns Removed: 1
  Columns Modified: 4

Details:
+ Table 'notifications' (added in production)
  - id: bigint, PRIMARY KEY
  - user_id: bigint, NOT NULL
  - message: text
  - created_at: timestamp

~ Table 'users' (modified)
  + Column 'last_login_at' (timestamp)
  ~ Column 'email' (varchar(255) → varchar(320))
```

---

### Cost Optimization

#### `analyze-costs <provider> <region>` ✅

Analyze cloud database costs and get optimization recommendations.

```bash
ai-shell analyze-costs <provider> <region> [options]
ai-shell costs <provider> <region> [options]    # Alias
```

**Providers:**
- `aws` - Amazon Web Services (RDS, Aurora, DynamoDB)
- `gcp` - Google Cloud Platform (Cloud SQL, Spanner)
- `azure` - Microsoft Azure (SQL Database, Cosmos DB)

**Options:**
- `--detailed` - Show detailed breakdown

**Examples:**

```bash
# Analyze AWS costs
ai-shell analyze-costs aws us-east-1

# GCP with details
ai-shell costs gcp us-central1 --detailed

# Azure costs
ai-shell analyze-costs azure eastus
```

**Output Example:**

```
💰 Analyzing costs...

Current Monthly Costs:
  Compute: $450.00
  Storage: $125.00
  Backup: $45.00
  Data Transfer: $80.00
  Total: $700.00

💡 Potential Savings: $245.50/month
   Annual Savings: $2,946.00

Recommendations (5):

1. Switch to Reserved Instances
   Savings: $135/month | Priority: high
   Moving from on-demand to 1-year reserved instances can reduce compute costs by 30%.

2. Enable Storage Auto-Scaling
   Savings: $45/month | Priority: medium
   Current over-provisioned storage can be optimized with auto-scaling.

3. Use Read Replicas for Analytics
   Savings: $35/month | Priority: medium
   Offload read-heavy analytics queries to cheaper read replicas.

4. Compress Backups
   Savings: $20.50/month | Priority: low
   Enable compression to reduce backup storage costs.

5. Optimize Data Transfer
   Savings: $10/month | Priority: low
   Use regional endpoints to reduce cross-region transfer costs.
```

---

## Planned Features

The following commands are planned for future releases:

### 📋 Interactive Mode (Coming Soon)

```bash
ai-shell interactive              # Start REPL mode
ai-shell i                        # Alias
```

Full-featured interactive shell with:
- Natural language query interface
- Auto-completion
- Query history
- Multi-line editing
- Session management

---

### 📋 Database Management (Planned)

```bash
# Connection management
ai-shell setup                    # Interactive setup wizard
ai-shell connect <connection>     # Connect to database
ai-shell test-connection [name]   # Test connectivity

# Database inspection
ai-shell show <objects>           # List database objects
ai-shell describe <object>        # Describe object details
ai-shell inspect <table>          # Deep inspection with AI
```

---

### 📋 Data Operations (Planned)

```bash
# Query execution
ai-shell query "natural language" # Execute NL query
ai-shell execute "SQL"            # Execute raw SQL
ai-shell exec "SQL"               # Alias

# Data import/export
ai-shell export <source>          # Export data
ai-shell import <file>            # Import data
```

---

### 📋 Security & Compliance (Planned)

```bash
# Credential management
ai-shell vault add <name>         # Store credentials
ai-shell vault get <name>         # Retrieve credentials
ai-shell vault list               # List stored credentials

# Auditing
ai-shell audit-log                # View audit logs
ai-shell permissions grant        # Manage permissions
ai-shell permissions revoke       # Revoke permissions
```

---

### 📋 Advanced Schema (Planned)

```bash
# Migration management
ai-shell migrate "description"    # Create migration
ai-shell rollback                 # Rollback migration
ai-shell sync-schema <src> <dst>  # Sync schemas

# Migration validation
ai-shell validate-migration <file>  # Validate migration syntax
```

---

### 📋 Scheduling (Planned)

```bash
# Task scheduling
ai-shell schedule <task>          # Schedule recurring task
ai-shell schedule --list          # List scheduled tasks
ai-shell schedule --remove <id>   # Remove scheduled task
```

---

### 📋 Advanced Options (Planned)

```bash
# Output formats (not all implemented)
--format table                    # ✅ Table output (default)
--format json                     # 🚧 JSON output (partial)
--format csv                      # 📋 CSV output (planned)
--format xml                      # 📋 XML output (planned)
--format excel                    # 📋 Excel output (planned)
--format pdf                      # 📋 PDF output (planned)
```

---

## Utility Commands

### `features` ✅

List all 10 AI-Shell features.

```bash
ai-shell features
```

**Output:**

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

### `examples` ✅

Show usage examples for all features.

```bash
ai-shell examples
```

Displays comprehensive examples organized by feature category.

---

### `version` ✅

Show version information.

```bash
ai-shell --version
ai-shell version
```

---

### `help` ✅

Show help information.

```bash
ai-shell --help
ai-shell help
ai-shell <command> --help
```

---

## Advanced Usage

### Command Chaining

Chain multiple commands using shell operators:

```bash
# Sequential execution
ai-shell backup && ai-shell optimize "SELECT * FROM users"

# Conditional execution
ai-shell test-migration migrations/001.sql && ai-shell monitor
```

---

### Scripting

Use AI-Shell in automation scripts:

```bash
#!/bin/bash
# daily-maintenance.sh

# Run health check
ai-shell health-check --json > health-report.json

# Create backup
ai-shell backup --connection production

# Analyze slow queries
ai-shell analyze-slow-queries --threshold 500

# Clear old cache entries
ai-shell cache clear

echo "Maintenance completed"
```

---

### Environment Variables

Configure AI-Shell using environment variables:

```bash
# Required for AI features
export ANTHROPIC_API_KEY="your-api-key"

# Database connection (optional)
export DATABASE_URL="postgres://localhost:5432/myapp"

# Redis for caching (optional)
export REDIS_URL="redis://localhost:6379"

# Logging level
export LOG_LEVEL="debug"
```

---

### Output Formatting

Control output format for different use cases:

```bash
# JSON for scripting
ai-shell health-check --json | jq '.memory.value'

# Verbose for debugging
ai-shell --verbose optimize "SELECT * FROM users"

# Quiet for cron jobs
ai-shell --quiet backup
```

---

### Exit Codes

AI-Shell uses standard exit codes for scripting:

- `0` - Success
- `1` - General error
- `2` - Configuration error
- `3` - Connection error
- `4` - Query error
- `5` - Permission denied

**Example:**

```bash
#!/bin/bash
if ai-shell health-check --quiet; then
    echo "Database healthy"
else
    echo "Health check failed with code $?"
    exit 1
fi
```

---

## Common Workflows

### Daily DBA Tasks

```bash
# Morning routine
ai-shell health-check
ai-shell analyze-slow-queries
ai-shell cache stats

# If issues found
ai-shell optimize "problematic query"
ai-shell cache clear
```

---

### Pre-Deployment Checks

```bash
# Test migrations
ai-shell test-migration migrations/new-feature.sql

# Validate schema changes
ai-shell diff staging production

# Create backup before deploy
ai-shell backup --connection production
```

---

### Performance Optimization

```bash
# Identify issues
ai-shell analyze-slow-queries --threshold 500

# Optimize queries
ai-shell optimize "SELECT * FROM slow_table"

# Monitor improvements
ai-shell monitor --interval 3000
```

---

### Cost Management

```bash
# Monthly cost review
ai-shell analyze-costs aws us-east-1 --detailed

# Compare providers
ai-shell costs aws us-east-1
ai-shell costs gcp us-central1
ai-shell costs azure eastus
```

---

## Troubleshooting

### Common Issues

**API Key Not Set:**
```bash
Error: ANTHROPIC_API_KEY environment variable not set

# Solution:
export ANTHROPIC_API_KEY="your-key-here"
```

**Connection Failed:**
```bash
# Check connection
ai-shell test-connection

# Verify environment variables
echo $DATABASE_URL
```

**Cache Not Working:**
```bash
# Verify Redis connection
ai-shell cache enable --redis redis://localhost:6379

# Check cache stats
ai-shell cache stats
```

---

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Global verbose flag
ai-shell --verbose health-check

# Environment variable
export LOG_LEVEL=debug
ai-shell monitor
```

---

## Command Aliases

Quick reference for command aliases:

| Full Command | Alias |
|-------------|-------|
| `optimize` | `opt` |
| `analyze-slow-queries` | `slow` |
| `health-check` | `health` |
| `backup-list` | `backups` |
| `federate` | `fed` |
| `design-schema` | `design` |
| `validate-schema` | `validate` |
| `test-migration` | `test-mig` |
| `explain` | `exp` |
| `translate` | `nl2sql` |
| `analyze-costs` | `costs` |

---

## See Also

- [Quick Start Guide](./quick-start.md) - Get started in 5 minutes
- [Configuration Reference](./configuration.md) - Configuration options
- [10 Features Overview](./10-features.md) - Detailed feature documentation
- [API Reference](./api-reference.md) - Programmatic API
- [Troubleshooting Guide](./troubleshooting.md) - Common issues and solutions
- [ROADMAP](./ROADMAP.md) - Future development plans

---

## Implementation Roadmap

For details on what's currently implemented vs. planned, see:
- [ROADMAP.md](./ROADMAP.md) - Full implementation roadmap
- [PENDING_FEATURES.md](./PENDING_FEATURES.md) - Feature status tracking
