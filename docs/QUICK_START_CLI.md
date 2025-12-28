# AI-Shell Quick Start Guide

**Get up and running with AI-Shell in 5 minutes**

---

## Table of Contents

1. [Installation](#installation)
2. [First Commands](#first-commands)
3. [Common Workflows](#common-workflows)
4. [Database Connections](#database-connections)
5. [Query Optimization](#query-optimization)
6. [Tips & Tricks](#tips--tricks)

---

## Installation

### Prerequisites

- Node.js 18+ installed
- Database: PostgreSQL, MySQL, MongoDB, or Redis
- Anthropic API key (for AI features)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/your-org/ai-shell.git
cd ai-shell

# Install dependencies
npm install

# Build the project
npm run build

# Set up environment variables
export ANTHROPIC_API_KEY="your-api-key-here"
export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"

# Verify installation
ai-shell --version
```

### Alternative: Global Installation

```bash
npm install -g ai-shell
ai-shell --version
```

---

## First Commands

### 1. Check Your Setup

```bash
# Show version
ai-shell --version

# Show help
ai-shell --help

# Check available commands
ai-shell --list
```

### 2. Connect to a Database

```bash
# PostgreSQL
ai-shell pg connect "postgresql://localhost:5432/mydb"

# MySQL
ai-shell mysql connect "mysql://root:password@localhost:3306/mydb"

# MongoDB
ai-shell mongo connect "mongodb://localhost:27017/mydb"

# Redis
ai-shell redis connect "redis://localhost:6379"
```

**Tip:** Save named connections for quick switching:
```bash
ai-shell pg connect "postgresql://prod.db.com:5432/app" --name production
ai-shell pg connect "postgresql://localhost:5432/app" --name dev
```

### 3. Run Your First Query

```bash
# Simple query
ai-shell pg query "SELECT * FROM users LIMIT 10"

# With table output
ai-shell pg query "SELECT * FROM users" --format table

# Export to JSON
ai-shell pg query "SELECT * FROM orders" --format json --output orders.json
```

### 4. Natural Language Query

```bash
# Translate natural language to SQL
ai-shell translate "show all active users"

# Translate and execute
ai-shell translate "count orders from last month" --execute

# Show execution plan
ai-shell translate "get top 10 products by sales" --explain
```

---

## Common Workflows

### Workflow 1: Find and Fix Slow Queries

```bash
# Step 1: Find slow queries
ai-shell slow-queries --threshold 1000 --last 24h

# Step 2: Analyze a specific slow query
ai-shell explain "SELECT * FROM orders WHERE status = 'pending'"

# Step 3: Get optimization recommendations
ai-shell optimize "SELECT * FROM orders WHERE status = 'pending'" --explain

# Step 4: Apply optimization
ai-shell optimize "SELECT * FROM orders WHERE status = 'pending'" --apply
```

**Output Example:**
```
Slow Query Analysis (Last 24h, Threshold: 1000ms)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Query: SELECT * FROM orders WHERE status = 'pending'
   Execution Time: 2,340ms (avg)
   Call Count: 456 times

   Recommendation: Add index on status column
   SQL: CREATE INDEX idx_orders_status ON orders(status)

   Estimated Improvement: 78% faster (2,340ms -> 515ms)

   Apply optimization? [Y/n] y

✓ Index created successfully
✓ Query now runs in 498ms (79% faster)
```

---

### Workflow 2: Database Health Check

```bash
# Check connection status
ai-shell pg status

# View active queries
ai-shell pg activity

# Check for locks
ai-shell pg locks --blocking

# Review table statistics
ai-shell pg stats --sort scans

# Analyze indexes
ai-shell indexes analyze --show-unused
```

---

### Workflow 3: Backup and Migration

```bash
# Create backup before changes
ai-shell backup create --database production --compress --encrypt

# Check migration status
ai-shell migrate status

# Run pending migrations
ai-shell migrate up

# Rollback if needed
ai-shell migrate down

# Verify database state
ai-shell pg tables --show-size
```

---

### Workflow 4: Index Optimization

```bash
# Step 1: Analyze current indexes
ai-shell indexes analyze --table users

# Step 2: Find missing indexes
ai-shell indexes missing --analyze-queries

# Step 3: Get recommendations
ai-shell indexes recommend --table users --query-log

# Step 4: Create recommended index
ai-shell indexes create --table users --columns email --unique --online

# Step 5: Find unused indexes
ai-shell indexes unused --size-threshold 50

# Step 6: Drop unused indexes
ai-shell indexes drop --table users --index old_unused_idx
```

---

### Workflow 5: Performance Monitoring

```bash
# Real-time monitoring
ai-shell pg activity --all

# Check slow queries
ai-shell slow-queries --threshold 500 --last 1h

# View performance metrics
ai-shell metrics show --database production

# Generate performance report
ai-shell reports create --type performance --period 7d
```

---

## Database Connections

### PostgreSQL

```bash
# Local development
ai-shell pg connect "postgresql://localhost:5432/mydb"

# Production with SSL
ai-shell pg connect "postgresql://user:pass@prod.db.com:5432/app" \
  --name production \
  --ssl \
  --pool-size 20

# Check connection
ai-shell pg status

# List tables
ai-shell pg tables

# Describe table
ai-shell pg describe users --show-indexes
```

---

### MySQL

```bash
# Connect
ai-shell mysql connect "mysql://root:password@localhost:3306/mydb"

# List databases
ai-shell mysql query "SHOW DATABASES"

# List tables
ai-shell mysql tables

# Show processlist
ai-shell mysql processlist

# Optimize table
ai-shell mysql optimize users
```

---

### MongoDB

```bash
# Connect
ai-shell mongo connect "mongodb://localhost:27017/mydb"

# List collections
ai-shell mongo collections

# Query documents
ai-shell mongo query '{"status": "active"}' --collection users

# Aggregate
ai-shell mongo aggregate '[{"$match": {"age": {"$gte": 30}}}]' --collection users

# Create index
ai-shell mongo createIndex users '{"email": 1}' --unique

# Show indexes
ai-shell mongo indexes users
```

---

### Redis

```bash
# Connect
ai-shell redis connect "redis://localhost:6379"

# Get value
ai-shell redis get mykey

# Set value
ai-shell redis set mykey "Hello World"

# Set with expiration
ai-shell redis set session:123 "user_data" --ex 3600

# Find keys
ai-shell redis keys "session:*" --scan

# Monitor commands
ai-shell redis monitor --duration 60

# Get server info
ai-shell redis info
```

---

## Query Optimization

### Basic Optimization

```bash
# Optimize single query
ai-shell optimize "SELECT * FROM users WHERE email LIKE '%@gmail.com'"

# Show execution plans
ai-shell optimize "SELECT * FROM orders" --explain --compare

# Safe mode (preview only)
ai-shell optimize "UPDATE users SET status = 'active'" --dry-run
```

### Batch Optimization

```bash
# Auto-fix slow queries
ai-shell slow-queries --auto-fix --threshold 2000

# Optimize all queries in log
ai-shell pattern-detect --include-suggestions --period 7d
```

### Index Management

```bash
# Analyze all indexes
ai-shell indexes analyze

# Get recommendations
ai-shell indexes recommend --table orders --workload read

# Create recommended indexes
ai-shell indexes create --table orders --columns "customer_id,created_at" --online

# Drop unused indexes
ai-shell indexes unused --min-age 30 | xargs -I {} ai-shell indexes drop {}
```

---

## Tips & Tricks

### 1. Use Output Formats

```bash
# Table format for humans
ai-shell pg query "SELECT * FROM users LIMIT 5" --format table

# JSON for scripts
ai-shell pg query "SELECT * FROM users" --format json --output users.json

# CSV for spreadsheets
ai-shell pg export users --format csv --output users.csv
```

### 2. Named Connections

```bash
# Save connections
ai-shell pg connect "postgresql://prod..." --name production
ai-shell pg connect "postgresql://localhost..." --name dev

# Switch between connections
ai-shell pg disconnect
ai-shell pg connect --name production
```

### 3. Command Chaining

```bash
# Backup before migration
ai-shell backup create && ai-shell migrate up

# Optimize after migration
ai-shell migrate up && ai-shell indexes analyze

# Export and compress
ai-shell pg export users --format json | gzip > users.json.gz
```

### 4. Safety Features

```bash
# Always check risk first
ai-shell risk-check "DELETE FROM users WHERE active = false"

# Use dry-run for dangerous operations
ai-shell migrate up --dry-run

# Create backup before major changes
ai-shell backup create --compress --encrypt
```

### 5. Performance Tips

```bash
# Limit large result sets
ai-shell pg query "SELECT * FROM logs" --limit 1000

# Use connection pooling
ai-shell pg connect "..." --pool-size 20

# Enable query caching (in config)
echo "cache_enabled: true" >> ~/.ai-shell/config.yaml
```

### 6. Debugging

```bash
# Verbose mode
ai-shell pg query "SELECT * FROM users" --verbose

# Show execution plan
ai-shell pg query "SELECT * FROM orders" --explain

# Check logs
tail -f ~/.ai-shell/logs/ai-shell.log
```

### 7. Configuration File

Create `~/.ai-shell/config.yaml`:

```yaml
# Default database
databases:
  default:
    type: postgres
    host: localhost
    port: 5432
    database: mydb
    pool_size: 10

# Output preferences
output:
  default_format: table
  color_enabled: true
  timestamp: true

# Performance
performance:
  query_timeout: 30000
  cache_enabled: true

# Security
security:
  vault_enabled: true
  require_confirmation: true
```

Then use:
```bash
ai-shell --config ~/.ai-shell/config.yaml
```

### 8. Shortcuts and Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
# Shortcuts
alias ais='ai-shell'
alias aisq='ai-shell pg query'
alias aist='ai-shell translate'
alias aiso='ai-shell optimize'

# Quick connections
alias ais-prod='ai-shell pg connect --name production'
alias ais-dev='ai-shell pg connect --name dev'

# Common queries
alias ais-slow='ai-shell slow-queries --threshold 1000'
alias ais-stats='ai-shell pg stats'
```

---

## Common Use Cases

### 1. Daily DBA Tasks

```bash
# Morning health check
ai-shell pg status
ai-shell pg activity
ai-shell pg locks --blocking
ai-shell slow-queries --last 24h

# Maintenance
ai-shell pg vacuum --analyze
ai-shell indexes analyze
```

### 2. Performance Troubleshooting

```bash
# Find the problem
ai-shell slow-queries --threshold 500

# Analyze query
ai-shell explain "SELECT * FROM problematic_table"

# Get recommendations
ai-shell optimize "SELECT * FROM problematic_table" --explain

# Apply fix
ai-shell indexes create --table problematic_table --columns indexed_column
```

### 3. Schema Changes

```bash
# Create migration
ai-shell migrate create add_email_to_users

# Edit migration file, then apply
ai-shell migrate up --dry-run
ai-shell migrate up

# Verify
ai-shell pg describe users
```

### 4. Data Export/Import

```bash
# Export
ai-shell pg export users --format json --output users.json

# Import
ai-shell pg import users.json --table users_copy --truncate

# Verify
ai-shell pg query "SELECT COUNT(*) FROM users_copy"
```

---

## Troubleshooting

### Connection Issues

```bash
# Test connection
ai-shell pg connect "postgresql://..." --verbose

# Check status
ai-shell pg status

# View logs
cat ~/.ai-shell/logs/ai-shell.log
```

### Slow Performance

```bash
# Check for locks
ai-shell pg locks --blocking

# Find slow queries
ai-shell slow-queries --threshold 500

# Analyze indexes
ai-shell indexes analyze --show-unused
```

### Permission Errors

```bash
# Check permissions
ai-shell permissions list

# Grant permissions
ai-shell permissions grant read-only --to dev-team
```

---

## Next Steps

1. **Read the full CLI reference:** [CLI_REFERENCE.md](/home/claude/AIShell/aishell/docs/CLI_REFERENCE.md)
2. **Explore tutorials:** Check `/home/claude/AIShell/aishell/docs/tutorials/`
3. **Join the community:** [Discord](https://discord.gg/ai-shell)
4. **Report issues:** [GitHub Issues](https://github.com/your-org/ai-shell/issues)

---

## Getting Help

```bash
# General help
ai-shell --help

# Command help
ai-shell optimize --help

# Show examples
ai-shell examples optimize

# Interactive mode
ai-shell

# Documentation
ai-shell docs
```

---

**Happy querying! 🚀**

For more information, visit [docs.ai-shell.dev](https://docs.ai-shell.dev)
