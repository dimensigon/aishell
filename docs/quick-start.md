# Quick Start Guide

Get started with AI-Shell in 5 minutes. This guide walks you through setup, your first database connection, and your first AI-powered query.

## Table of Contents

- [Prerequisites](#prerequisites)
- [5-Minute Setup](#5-minute-setup)
- [First Database Connection](#first-database-connection)
- [Your First AI-Powered Query](#your-first-ai-powered-query)
- [Common Commands](#common-commands)
- [Next Steps](#next-steps)
- [Quick Reference](#quick-reference)

---

## Prerequisites

Before starting, ensure you have:

- **Node.js 18+** installed ([Download](https://nodejs.org/))
- **npm 9+** installed (comes with Node.js)
- **Database access** to at least one supported database:
  - PostgreSQL, MySQL, MongoDB, Redis, or Oracle
- **Anthropic API Key** ([Get one here](https://console.anthropic.com/))

**Quick Check:**
```bash
node --version   # Should show v18.0.0 or higher
npm --version    # Should show 9.0.0 or higher
```

---

## 5-Minute Setup

### Step 1: Install AI-Shell (30 seconds)

Choose your preferred installation method:

```bash
# Option 1: Global installation (recommended)
npm install -g ai-shell

# Option 2: Use without installation
npx ai-shell

# Option 3: Docker
docker run -it aishell/ai-shell:latest
```

**Verify installation:**
```bash
ai-shell --version
# Expected: ai-shell v1.0.0
```

### Step 2: Set Your API Key (1 minute)

AI-Shell uses Anthropic's Claude for natural language understanding.

```bash
# Linux/macOS
export ANTHROPIC_API_KEY="your-api-key-here"

# Make it permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your-api-key-here"

# Windows (Command Prompt - permanent)
setx ANTHROPIC_API_KEY "your-api-key-here"
```

**Don't have an API key?**
1. Visit [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key

### Step 3: Run Interactive Setup (2 minutes)

Launch the setup wizard to configure AI-Shell:

```bash
ai-shell setup
```

The wizard will ask you about:
- **Database connections** - Add your primary database
- **Security preferences** - Enable vault and audit logging
- **Performance settings** - Configure cache and connection pools
- **Feature enablement** - Enable auto-optimization, monitoring, etc.

**Example interaction:**
```
Welcome to AI-Shell Setup Wizard!

? Enter your primary database type: postgres
? Database host: localhost
? Database port: 5432
? Database name: myapp
? Username: myuser
? Save password to encrypted vault? Yes
? Enter password: ••••••••
✓ Database connection configured

? Enable automatic query optimization? Yes
? Enable audit logging? Yes
? Enable performance monitoring? Yes

✓ Setup complete! Run 'ai-shell status' to verify.
```

### Step 4: Verify Setup (30 seconds)

Check that everything is configured correctly:

```bash
# Check system status
ai-shell status

# Test database connection
ai-shell test-connection default

# View configuration
ai-shell config show
```

**Expected output:**
```
✓ AI-Shell v1.0.0
✓ Node.js v20.10.0
✓ LLM Provider: Anthropic (Claude)
✓ Active Connections: 1 (default: postgres://localhost:5432/myapp)
✓ Cache: Enabled (0/5000 entries)
✓ Monitoring: Enabled
✓ Auto-optimization: Enabled
✓ System Health: OK
```

Congratulations! You're ready to use AI-Shell.

---

## First Database Connection

### Quick Connection

Connect to a database using a connection string:

```bash
# PostgreSQL
ai-shell connect postgres://user:pass@localhost:5432/mydb

# MySQL
ai-shell connect mysql://user:pass@localhost:3306/mydb

# MongoDB
ai-shell connect mongodb://user:pass@localhost:27017/mydb

# Redis
ai-shell connect redis://localhost:6379

# Oracle
ai-shell connect oracle://user:pass@localhost:1521/orcl
```

### Interactive Connection

Use the interactive mode for guided setup:

```bash
ai-shell connect --interactive
```

**Example:**
```
? Select database type: PostgreSQL
? Host: localhost
? Port: 5432
? Database: myapp
? Username: myuser
? Password: ••••••••
? Save to vault? Yes
? Connection name: production

Connecting...
✓ Successfully connected to PostgreSQL
✓ Database version: PostgreSQL 16.0
✓ Connection saved as: production
```

### Managing Multiple Connections

```bash
# Add a connection to vault
ai-shell vault add staging --interactive

# List all connections
ai-shell vault list

# Switch between connections
ai-shell use staging

# Show active connection
ai-shell config get database.active
```

### Connection String Formats

**PostgreSQL:**
```
postgres://user:password@host:port/database
postgresql://user:password@host:port/database?sslmode=require
```

**MySQL:**
```
mysql://user:password@host:port/database
mysql://user:password@host:port/database?charset=utf8mb4
```

**MongoDB:**
```
mongodb://user:password@host:port/database
mongodb+srv://user:password@cluster.mongodb.net/database
```

**Redis:**
```
redis://localhost:6379
redis://:password@localhost:6379/0
```

**Oracle:**
```
oracle://user:password@host:port/servicename
oracle://user:password@host:port/SID
```

---

## Your First AI-Powered Query

AI-Shell's killer feature is natural language queries. No SQL required!

### Example 1: Simple Data Retrieval

```bash
# Natural language
ai-shell query "show me all users"

# What AI-Shell does:
# 1. Understands your intent
# 2. Generates optimal SQL: SELECT * FROM users
# 3. Executes query
# 4. Formats results
```

**Output:**
```
┌────┬──────────────┬─────────────────────┬─────────────────────┐
│ id │ username     │ email               │ created_at          │
├────┼──────────────┼─────────────────────┼─────────────────────┤
│ 1  │ john_doe     │ john@example.com    │ 2025-01-15 10:30:00 │
│ 2  │ jane_smith   │ jane@example.com    │ 2025-01-16 14:20:00 │
│ 3  │ bob_wilson   │ bob@example.com     │ 2025-01-17 09:15:00 │
└────┴──────────────┴─────────────────────┴─────────────────────┘

Showing 3 rows (0.045s)
```

### Example 2: Filtering Data

```bash
ai-shell query "show users who signed up this week"
```

**Generated SQL:**
```sql
SELECT * FROM users
WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)
ORDER BY created_at DESC
```

### Example 3: Aggregations

```bash
ai-shell query "how many orders do we have by status?"
```

**Generated SQL:**
```sql
SELECT status, COUNT(*) as count
FROM orders
GROUP BY status
ORDER BY count DESC
```

**Output:**
```
┌───────────┬───────┐
│ status    │ count │
├───────────┼───────┤
│ completed │ 1,234 │
│ pending   │ 456   │
│ cancelled │ 78    │
└───────────┴───────┘
```

### Example 4: Complex Queries

```bash
ai-shell query "show top 10 customers by revenue in the last 30 days"
```

**Generated SQL:**
```sql
SELECT
  u.name,
  COUNT(o.id) as order_count,
  SUM(o.total) as revenue
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 0
ORDER BY revenue DESC
LIMIT 10
```

### Example 5: Cross-Database Federation

One of AI-Shell's unique features - query multiple databases at once!

```bash
# Query across PostgreSQL and MongoDB
ai-shell query "join user profiles from postgres with session data from mongodb"
```

**What happens:**
1. AI-Shell identifies data sources
2. Executes queries on each database
3. Performs in-memory join
4. Returns unified results

---

## Common Commands

### Query Operations

```bash
# Natural language query
ai-shell query "your question here"

# Execute raw SQL
ai-shell exec "SELECT * FROM users LIMIT 10"

# Explain query
ai-shell explain "SELECT * FROM orders WHERE status = 'pending'"

# Optimize query
ai-shell optimize "SELECT * FROM large_table"
```

### Database Management

```bash
# List databases
ai-shell query "show databases"

# List tables
ai-shell query "show tables"

# Describe table structure
ai-shell query "describe users table"

# Show table size
ai-shell query "how big is the orders table?"
```

### Performance & Optimization

```bash
# Get performance insights
ai-shell insights

# Show slow queries
ai-shell slow-queries

# Analyze query performance
ai-shell analyze "SELECT * FROM orders WHERE status = 'pending'"

# Auto-fix performance issues
ai-shell fix-indexes
```

### Backup & Recovery

```bash
# Create backup
ai-shell backup create

# List backups
ai-shell backup list

# Restore from backup
ai-shell restore --backup latest

# Schedule automatic backups
ai-shell backup schedule --cron "0 2 * * *"
```

### Configuration

```bash
# Show current config
ai-shell config show

# Get specific setting
ai-shell config get database.default.host

# Set configuration
ai-shell config set performance.cacheEnabled true

# Reset to defaults
ai-shell config reset
```

### Monitoring

```bash
# Start real-time monitoring
ai-shell monitor start

# View dashboard
ai-shell dashboard

# Check system health
ai-shell health-check

# View metrics
ai-shell metrics
```

---

## Next Steps

Now that you're up and running, explore AI-Shell's powerful features:

### 1. Learn Natural Language Queries
Master the art of talking to your database.

**Read:** [Natural Language Queries Tutorial](./tutorials/natural-language-queries.md)

**Try:**
```bash
ai-shell query "show me revenue trends by month"
ai-shell query "find duplicate email addresses"
ai-shell query "which products are low in stock?"
```

### 2. Optimize Your Queries
Make your queries 10x faster with AI-powered optimization.

**Read:** [Query Optimization Tutorial](./tutorials/query-optimization.md)

**Try:**
```bash
ai-shell optimize "SELECT * FROM orders WHERE status = 'pending'"
ai-shell insights
ai-shell fix-indexes
```

### 3. Set Up Multi-Database Federation
Query across different databases simultaneously.

**Read:** [Database Federation Tutorial](./tutorials/database-federation.md)

**Try:**
```bash
# Add multiple connections
ai-shell vault add postgres-main --interactive
ai-shell vault add mongodb-analytics --interactive
ai-shell vault add redis-cache --interactive

# Query across them
ai-shell query "combine user data from postgres with logs from mongodb"
```

### 4. Enable Automated Backups
Never lose data with intelligent backup automation.

**Read:** [Backup & Recovery Tutorial](./tutorials/backup-recovery.md)

**Try:**
```bash
ai-shell backup create --schedule "daily at 2am"
ai-shell backup list
```

### 5. Configure Security
Protect your data with enterprise-grade security.

**Read:** [Security Setup Tutorial](./tutorials/security.md)

**Try:**
```bash
ai-shell vault encrypt-all
ai-shell permissions grant read-only --to dev-team
ai-shell audit-log show
```

### 6. Set Up Performance Monitoring
Track query performance and catch issues early.

**Read:** [Performance Monitoring Tutorial](./tutorials/performance-monitoring.md)

**Try:**
```bash
ai-shell monitor start
ai-shell anomaly start --auto-fix
```

### 7. Try Schema Migrations
Evolve your database schema safely with natural language.

**Read:** [Schema Migrations Tutorial](./tutorials/migrations.md)

**Try:**
```bash
ai-shell migrate "add email_verified boolean field to users table"
ai-shell schema diff production staging
```

### 8. Enable Autonomous DevOps
Let AI optimize your infrastructure automatically.

**Read:** [Autonomous DevOps Tutorial](./tutorials/autonomous-devops.md)

**Try:**
```bash
ai-shell ada start --optimize-cost
ai-shell ada status
```

---

## Quick Reference

### Most Used Commands

```bash
# Query in natural language
ai-shell query "your question"

# Connect to database
ai-shell connect postgres://host/db

# Get performance insights
ai-shell insights

# Optimize slow query
ai-shell optimize "SQL query"

# Create backup
ai-shell backup create

# Show system status
ai-shell status

# View configuration
ai-shell config show

# Get help
ai-shell --help
ai-shell query --help
```

### Essential Natural Language Patterns

```bash
# Data retrieval
"show me all X"
"list all X where Y"
"find X that meet condition Y"

# Aggregations
"how many X"
"count X by Y"
"sum of X grouped by Y"

# Time-based queries
"show X from last week"
"find X created today"
"list X between date1 and date2"

# Sorting and limits
"top 10 X by Y"
"show X ordered by Y"
"give me first 5 X"

# Joins and relationships
"show X with their related Y"
"combine X from table1 with Y from table2"
"join X and Y on Z"
```

### Configuration Shortcuts

```bash
# Database
export AI_SHELL_DATABASE_URL="postgres://localhost/mydb"

# API Key
export ANTHROPIC_API_KEY="your-key"

# Log level
export AI_SHELL_LOG_LEVEL="debug"

# Cache directory
export AI_SHELL_CACHE_DIR="/path/to/cache"
```

### Troubleshooting Quick Fixes

```bash
# Connection issues
ai-shell test-connection default
ai-shell config get database.default

# Performance issues
ai-shell cache clear
ai-shell config set performance.cacheEnabled true

# API key issues
echo $ANTHROPIC_API_KEY
ai-shell config validate

# View logs
ai-shell logs show --tail 50
ai-shell logs show --level error
```

---

## Getting Help

### In-App Help

```bash
# General help
ai-shell --help

# Command-specific help
ai-shell query --help
ai-shell backup --help

# Show examples
ai-shell examples
ai-shell examples query
```

### Documentation

- **Full Documentation**: [docs.ai-shell.dev](https://docs.ai-shell.dev)
- **API Reference**: [docs/api/core.md](./api/core.md)
- **Tutorials**: [docs/tutorials/](./tutorials/)
- **FAQ**: [docs/FAQ.md](./FAQ.md)

### Community

- **GitHub Issues**: [Report bugs](https://github.com/your-org/ai-shell/issues)
- **Discussions**: [Ask questions](https://github.com/your-org/ai-shell/discussions)
- **Discord**: [Chat with community](https://discord.gg/ai-shell)
- **Stack Overflow**: Tag questions with `ai-shell`

### Professional Support

For enterprise support, consulting, or training:
- Email: support@ai-shell.dev
- Enterprise: [ai-shell.dev/enterprise](https://ai-shell.dev/enterprise)

---

## What You've Learned

- ✓ How to install and configure AI-Shell
- ✓ How to connect to databases
- ✓ How to run natural language queries
- ✓ Common commands for daily operations
- ✓ Where to find more resources

**Time to master AI-Shell:** About 1 hour of practice with real queries

**Ready to level up?** Explore the tutorials linked in [Next Steps](#next-steps) to unlock AI-Shell's full potential.

---

**Happy querying!** If you build something cool with AI-Shell, share it with the community on [Discord](https://discord.gg/ai-shell) or [Twitter](https://twitter.com/aishell_dev).
