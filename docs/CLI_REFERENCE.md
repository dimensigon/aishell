# AI-Shell CLI Reference

**Complete Command Reference for AI-Shell Database Administration Platform**

**Version:** 1.0.0 (Phase 2 Complete)
**Last Updated:** October 29, 2025
**Total Commands:** 105 commands across 8 categories

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Natural Language & Query Optimization](#natural-language--query-optimization) (13 commands)
3. [PostgreSQL Commands](#postgresql-commands) (16 commands)
4. [MySQL Commands](#mysql-commands) (12 commands)
5. [MongoDB Commands](#mongodb-commands) (12 commands)
6. [Redis Commands](#redis-commands) (12 commands)
7. [Backup & Recovery](#backup--recovery) (10 commands)
8. [Migration & Schema](#migration--schema) (10 commands)
9. [Security & Vault](#security--vault) (10 commands)
10. [Analytics & Monitoring](#analytics--monitoring) (10 commands)

---

## Getting Started

### Installation

```bash
# Clone and install
git clone https://github.com/your-org/ai-shell.git
cd ai-shell
npm install

# Set up environment
export ANTHROPIC_API_KEY="your-api-key"
export DATABASE_URL="postgres://user:pass@localhost:5432/mydb"
```

### Global Options

All commands support these common options:

```bash
--format <type>     Output format: text, json, table, csv (default: text)
--output <file>     Write output to file instead of stdout
--verbose           Enable verbose logging
--help              Show command help
--version           Show version information
```

---

## Natural Language & Query Optimization

### 1. ai-shell translate

**Purpose:** Convert natural language to SQL queries

**Syntax:**
```bash
ai-shell translate "<natural language query>" [options]
```

**Options:**
- `--database <type>` - Target database: postgres, mysql, mongo, redis (default: postgres)
- `--dialect <version>` - Database version/dialect
- `--execute` - Execute the translated query immediately
- `--explain` - Show query execution plan
- `--dry-run` - Translate without executing

**Examples:**
```bash
# Basic translation
ai-shell translate "show all active users"

# Translate and execute
ai-shell translate "count orders from last month" --execute

# MongoDB translation
ai-shell translate "find products with price over 100" --database mongo

# Get execution plan
ai-shell translate "get top 10 customers by revenue" --explain
```

**Output:**
```json
{
  "natural_query": "show all active users",
  "sql": "SELECT * FROM users WHERE status = 'active'",
  "confidence": 0.95,
  "database": "postgres",
  "execution_time": "125ms",
  "estimated_rows": 1543
}
```

---

### 2. ai-shell optimize

**Purpose:** AI-powered query optimization with execution plan analysis

**Syntax:**
```bash
ai-shell optimize "<query>" [options]
```

**Options:**
- `--apply` - Apply optimization immediately
- `--explain` - Show execution plans (before/after)
- `--compare` - Performance comparison (before/after)
- `--dry-run` - Validate without executing
- `--database <name>` - Target database connection

**Examples:**
```bash
# Basic optimization
ai-shell optimize "SELECT * FROM orders WHERE status = 'pending'"

# With execution plan
ai-shell optimize "SELECT * FROM users WHERE email LIKE '%@gmail.com'" --explain

# Apply optimization
ai-shell optimize "SELECT * FROM products WHERE category = 'electronics'" --apply

# Performance comparison
ai-shell optimize "SELECT * FROM orders" --compare --format json
```

**Output:**
```
Original Query:
  SELECT * FROM orders WHERE status = 'pending'

Optimized Query:
  SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC LIMIT 1000

Improvements:
  - Added index recommendation: CREATE INDEX idx_orders_status ON orders(status)
  - Added result limiting to prevent large result sets
  - Estimated performance: 65% faster (320ms -> 112ms)

Risk Level: LOW
Apply optimization? [Y/n]
```

---

### 3. ai-shell slow-queries

**Purpose:** Analyze and optimize slow queries from database logs

**Syntax:**
```bash
ai-shell slow-queries [options]
```

**Options:**
- `--threshold <ms>` - Execution time threshold (default: 1000ms)
- `--last <period>` - Time period: 1h, 24h, 7d, 30d (default: 24h)
- `--limit <n>` - Number of results (default: 20)
- `--auto-fix` - Automatically optimize slow queries
- `--database <name>` - Target database

**Examples:**
```bash
# Show slow queries from last 24 hours
ai-shell slow-queries

# Custom threshold and period
ai-shell slow-queries --threshold 500 --last 7d

# Auto-fix slow queries
ai-shell slow-queries --auto-fix --threshold 2000

# Export to CSV
ai-shell slow-queries --format csv --output slow-queries.csv
```

**Output:**
```
Slow Query Analysis (Last 24h, Threshold: 1000ms)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Query: SELECT * FROM orders WHERE customer_id = ...
   Execution Time: 3,450ms (avg)
   Call Count: 1,234 times
   Recommendation: Add index on customer_id
   Estimated Improvement: 78% faster

2. Query: SELECT COUNT(*) FROM products WHERE ...
   Execution Time: 2,100ms (avg)
   Call Count: 567 times
   Recommendation: Add covering index
   Estimated Improvement: 85% faster
```

---

### 4. ai-shell indexes analyze

**Purpose:** Analyze index usage and get recommendations

**Syntax:**
```bash
ai-shell indexes analyze [options]
```

**Options:**
- `--table <name>` - Analyze specific table
- `--show-unused` - Show unused indexes
- `--show-missing` - Show missing index recommendations
- `--database <name>` - Target database

**Examples:**
```bash
# Analyze all tables
ai-shell indexes analyze

# Specific table
ai-shell indexes analyze --table users

# Show unused indexes
ai-shell indexes analyze --show-unused

# Get recommendations
ai-shell indexes analyze --show-missing --format json
```

---

### 5. ai-shell indexes recommend

**Purpose:** Get smart index recommendations based on query patterns

**Syntax:**
```bash
ai-shell indexes recommend --table <table> [options]
```

**Options:**
- `--table <name>` - Target table (required)
- `--query-log` - Analyze query logs for patterns
- `--workload <type>` - Workload type: read, write, mixed (default: mixed)

**Examples:**
```bash
# Basic recommendations
ai-shell indexes recommend --table orders

# Based on query logs
ai-shell indexes recommend --table users --query-log

# For read-heavy workload
ai-shell indexes recommend --table products --workload read
```

---

### 6. ai-shell indexes create

**Purpose:** Create recommended indexes

**Syntax:**
```bash
ai-shell indexes create --table <table> --columns <cols> [options]
```

**Options:**
- `--table <name>` - Target table (required)
- `--columns <cols>` - Comma-separated column list (required)
- `--name <name>` - Custom index name
- `--unique` - Create unique index
- `--online` - Non-blocking creation (default: true)
- `--dry-run` - Show SQL without executing

**Examples:**
```bash
# Basic index
ai-shell indexes create --table users --columns email

# Composite index
ai-shell indexes create --table orders --columns "customer_id,created_at"

# Unique index with custom name
ai-shell indexes create --table users --columns email --unique --name idx_users_email_unique

# Preview SQL
ai-shell indexes create --table products --columns category --dry-run
```

---

### 7. ai-shell indexes drop

**Purpose:** Drop indexes safely

**Syntax:**
```bash
ai-shell indexes drop --table <table> --index <name> [options]
```

**Options:**
- `--table <name>` - Target table (required)
- `--index <name>` - Index name (required)
- `--force` - Skip confirmation prompt
- `--concurrent` - Non-blocking drop (PostgreSQL)

**Examples:**
```bash
# Drop index
ai-shell indexes drop --table users --index idx_users_email

# Force drop
ai-shell indexes drop --table orders --index old_index --force
```

---

### 8. ai-shell indexes list

**Purpose:** List all indexes for a table

**Syntax:**
```bash
ai-shell indexes list --table <table> [options]
```

**Examples:**
```bash
# List indexes
ai-shell indexes list --table users

# JSON output
ai-shell indexes list --table orders --format json
```

---

### 9. ai-shell indexes unused

**Purpose:** Find unused indexes that can be dropped

**Syntax:**
```bash
ai-shell indexes unused [options]
```

**Options:**
- `--table <name>` - Check specific table
- `--min-age <days>` - Minimum age to consider (default: 30)
- `--size-threshold <MB>` - Size threshold (default: 10MB)

**Examples:**
```bash
# Find all unused indexes
ai-shell indexes unused

# Specific table
ai-shell indexes unused --table orders

# Large unused indexes
ai-shell indexes unused --size-threshold 100
```

---

### 10. ai-shell indexes missing

**Purpose:** Find missing indexes based on query patterns

**Syntax:**
```bash
ai-shell indexes missing [options]
```

**Options:**
- `--table <name>` - Check specific table
- `--analyze-queries` - Analyze slow query log
- `--min-impact <percent>` - Minimum impact threshold (default: 20%)

**Examples:**
```bash
# Find missing indexes
ai-shell indexes missing

# With query analysis
ai-shell indexes missing --analyze-queries

# High-impact only
ai-shell indexes missing --min-impact 50
```

---

### 11. ai-shell risk-check

**Purpose:** Query risk assessment and safety validation

**Syntax:**
```bash
ai-shell risk-check "<query>" [options]
```

**Options:**
- `--database <name>` - Target database
- `--allow-high-risk` - Allow high-risk operations
- `--estimate-impact` - Estimate affected rows

**Examples:**
```bash
# Check query risk
ai-shell risk-check "DELETE FROM users WHERE active = false"

# Estimate impact
ai-shell risk-check "UPDATE orders SET status = 'cancelled'" --estimate-impact
```

**Output:**
```
Risk Assessment:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Query: DELETE FROM users WHERE active = false
Risk Level: HIGH

Detected Issues:
  ⚠️  DELETE operation without transaction
  ⚠️  Affects multiple rows (estimated: 1,234)
  ⚠️  No backup confirmed

Recommendations:
  1. Create backup before proceeding
  2. Test on staging environment first
  3. Use transaction with rollback capability
  4. Consider soft delete instead

Estimated Impact:
  Affected Rows: ~1,234
  Affected Tables: 1 (users)
  Cascade Effects: 3 related tables

Proceed? [y/N]
```

---

### 12. ai-shell explain

**Purpose:** Visualize query execution plans

**Syntax:**
```bash
ai-shell explain "<query>" [options]
```

**Options:**
- `--analyze` - Run EXPLAIN ANALYZE (actual execution)
- `--format <type>` - Format: text, json, tree (default: tree)
- `--database <name>` - Target database

**Examples:**
```bash
# Basic explain
ai-shell explain "SELECT * FROM orders WHERE status = 'pending'"

# With actual execution
ai-shell explain "SELECT COUNT(*) FROM users" --analyze

# Tree format
ai-shell explain "SELECT * FROM orders JOIN customers" --format tree
```

---

### 13. ai-shell pattern-detect

**Purpose:** Detect query patterns and anti-patterns

**Syntax:**
```bash
ai-shell pattern-detect [options]
```

**Options:**
- `--period <duration>` - Analysis period (default: 24h)
- `--database <name>` - Target database
- `--include-suggestions` - Include optimization suggestions

**Examples:**
```bash
# Detect patterns
ai-shell pattern-detect

# Last week
ai-shell pattern-detect --period 7d

# With suggestions
ai-shell pattern-detect --include-suggestions
```

---

## PostgreSQL Commands

### 1. ai-shell pg connect

**Purpose:** Connect to PostgreSQL database

**Syntax:**
```bash
ai-shell pg connect <connection-string> [options]
```

**Options:**
- `--name <name>` - Named connection for switching
- `--ssl` - Enable SSL/TLS encryption
- `--pool-size <n>` - Connection pool size (default: 10)
- `--timeout <ms>` - Connection timeout (default: 5000)

**Examples:**
```bash
# Basic connection
ai-shell pg connect "postgresql://user:pass@localhost:5432/mydb"

# Named connection with SSL
ai-shell pg connect "postgresql://user:pass@prod.db.com:5432/app" --name production --ssl

# Custom pool size
ai-shell pg connect "postgresql://localhost:5432/mydb" --pool-size 20
```

**Output:**
```
✓ Connected to PostgreSQL
  Host: localhost:5432
  Database: mydb
  User: user
  Pool Size: 10
  Connection: production (active)
```

---

### 2. ai-shell pg disconnect

**Purpose:** Disconnect from PostgreSQL database

**Syntax:**
```bash
ai-shell pg disconnect [name] [options]
```

**Options:**
- `--all` - Disconnect all connections

**Examples:**
```bash
# Disconnect active connection
ai-shell pg disconnect

# Disconnect named connection
ai-shell pg disconnect production

# Disconnect all
ai-shell pg disconnect --all
```

---

### 3. ai-shell pg query

**Purpose:** Execute SQL queries on PostgreSQL

**Syntax:**
```bash
ai-shell pg query "<sql>" [options]
```

**Options:**
- `--explain` - Show execution plan
- `--format <type>` - Output format (text, json, table, csv)
- `--limit <n>` - Limit results
- `--timeout <ms>` - Query timeout

**Examples:**
```bash
# Basic query
ai-shell pg query "SELECT * FROM users WHERE active = true"

# With execution plan
ai-shell pg query "SELECT * FROM orders" --explain

# JSON output
ai-shell pg query "SELECT * FROM products" --format json --output products.json

# Limited results
ai-shell pg query "SELECT * FROM logs" --limit 100
```

---

### 4. ai-shell pg status

**Purpose:** Show PostgreSQL connection status

**Syntax:**
```bash
ai-shell pg status [options]
```

**Examples:**
```bash
# Connection status
ai-shell pg status

# Detailed status
ai-shell pg status --verbose --format json
```

---

### 5. ai-shell pg tables

**Purpose:** List all tables in database

**Syntax:**
```bash
ai-shell pg tables [schema] [options]
```

**Options:**
- `--schema <name>` - Filter by schema (default: public)
- `--pattern <glob>` - Filter by pattern
- `--show-size` - Show table sizes

**Examples:**
```bash
# All tables
ai-shell pg tables

# Specific schema
ai-shell pg tables --schema analytics

# With sizes
ai-shell pg tables --show-size --format table

# Pattern matching
ai-shell pg tables --pattern "user*"
```

---

### 6. ai-shell pg describe

**Purpose:** Describe table structure

**Syntax:**
```bash
ai-shell pg describe <table> [options]
```

**Options:**
- `--schema <name>` - Schema name
- `--show-indexes` - Include index information
- `--show-constraints` - Include constraints

**Examples:**
```bash
# Basic describe
ai-shell pg describe users

# Full details
ai-shell pg describe orders --show-indexes --show-constraints

# JSON format
ai-shell pg describe products --format json
```

---

### 7. ai-shell pg vacuum

**Purpose:** Vacuum tables to reclaim storage

**Syntax:**
```bash
ai-shell pg vacuum [table] [options]
```

**Options:**
- `--full` - Full vacuum (rewrites table)
- `--analyze` - Update statistics
- `--verbose` - Show detailed progress
- `--parallel <n>` - Parallel workers

**Examples:**
```bash
# Vacuum specific table
ai-shell pg vacuum users --analyze

# Full vacuum
ai-shell pg vacuum orders --full --verbose

# All tables with parallel
ai-shell pg vacuum --parallel 4 --analyze
```

---

### 8. ai-shell pg analyze

**Purpose:** Update query planner statistics

**Syntax:**
```bash
ai-shell pg analyze [table] [options]
```

**Options:**
- `--verbose` - Show detailed output
- `--skip-locked` - Skip locked tables

**Examples:**
```bash
# Analyze specific table
ai-shell pg analyze users --verbose

# Analyze all tables
ai-shell pg analyze
```

---

### 9. ai-shell pg reindex

**Purpose:** Rebuild indexes

**Syntax:**
```bash
ai-shell pg reindex <type> <name> [options]
```

**Types:** `index`, `table`, `schema`, `database`

**Options:**
- `--concurrently` - Non-blocking rebuild
- `--verbose` - Show progress

**Examples:**
```bash
# Reindex specific index
ai-shell pg reindex index idx_users_email --concurrently

# Reindex table
ai-shell pg reindex table orders --verbose

# Reindex entire schema
ai-shell pg reindex schema public
```

---

### 10. ai-shell pg stats

**Purpose:** Show table statistics

**Syntax:**
```bash
ai-shell pg stats [table] [options]
```

**Options:**
- `--schema <name>` - Schema filter
- `--sort <field>` - Sort by field (scans, inserts, updates, deletes)

**Examples:**
```bash
# Show all stats
ai-shell pg stats

# Specific table
ai-shell pg stats users

# Sort by scans
ai-shell pg stats --sort scans --format table
```

---

### 11. ai-shell pg locks

**Purpose:** Show current database locks

**Syntax:**
```bash
ai-shell pg locks [options]
```

**Options:**
- `--blocking` - Show only blocking locks
- `--wait-time <ms>` - Filter by wait time

**Examples:**
```bash
# All locks
ai-shell pg locks

# Blocking locks only
ai-shell pg locks --blocking

# Long waits
ai-shell pg locks --wait-time 5000
```

---

### 12. ai-shell pg activity

**Purpose:** Show active connections and queries

**Syntax:**
```bash
ai-shell pg activity [options]
```

**Options:**
- `--all` - Include idle connections
- `--long-running <ms>` - Filter long-running queries

**Examples:**
```bash
# Active queries
ai-shell pg activity

# All connections
ai-shell pg activity --all --format table

# Long-running queries
ai-shell pg activity --long-running 10000
```

---

### 13. ai-shell pg extensions

**Purpose:** Manage PostgreSQL extensions

**Syntax:**
```bash
ai-shell pg extensions <action> [name] [options]
```

**Actions:** `list`, `enable`, `disable`, `available`

**Examples:**
```bash
# List installed extensions
ai-shell pg extensions list

# Enable extension
ai-shell pg extensions enable pg_stat_statements

# Disable extension
ai-shell pg extensions disable postgis --cascade

# Show available
ai-shell pg extensions available
```

---

### 14. ai-shell pg partitions

**Purpose:** Show partition information

**Syntax:**
```bash
ai-shell pg partitions <table> [options]
```

**Examples:**
```bash
# Show partitions
ai-shell pg partitions orders

# Detailed info
ai-shell pg partitions logs --format json
```

---

### 15. ai-shell pg import

**Purpose:** Import data from file

**Syntax:**
```bash
ai-shell pg import <file> [options]
```

**Options:**
- `--table <name>` - Target table
- `--format <type>` - File format (sql, csv, json)
- `--truncate` - Truncate table before import
- `--batch-size <n>` - Batch size (default: 1000)

**Examples:**
```bash
# Import SQL dump
ai-shell pg import backup.sql

# Import CSV
ai-shell pg import users.csv --table users --truncate

# Import JSON with batching
ai-shell pg import data.json --table orders --batch-size 500
```

---

### 16. ai-shell pg export

**Purpose:** Export data to file

**Syntax:**
```bash
ai-shell pg export <table> [options]
```

**Options:**
- `--format <type>` - Export format (sql, csv, json)
- `--where <clause>` - Filter condition
- `--columns <cols>` - Column selection
- `--output <file>` - Output file

**Examples:**
```bash
# Export to JSON
ai-shell pg export users --format json --output users.json

# Export with filter
ai-shell pg export orders --where "created_at > '2024-01-01'" --format csv

# Select columns
ai-shell pg export products --columns "id,name,price" --output products.csv
```

---

## MySQL Commands

### 1-8. MySQL Core Commands

Similar to PostgreSQL commands:
- `ai-shell mysql connect`
- `ai-shell mysql disconnect`
- `ai-shell mysql query`
- `ai-shell mysql status`
- `ai-shell mysql tables`
- `ai-shell mysql describe`
- `ai-shell mysql import`
- `ai-shell mysql export`

### 9. ai-shell mysql optimize

**Purpose:** Optimize MySQL tables

**Syntax:**
```bash
ai-shell mysql optimize [table] [options]
```

**Examples:**
```bash
# Optimize table
ai-shell mysql optimize users

# Optimize all tables
ai-shell mysql optimize --all
```

---

### 10. ai-shell mysql repair

**Purpose:** Repair corrupted tables

**Syntax:**
```bash
ai-shell mysql repair <table> [options]
```

**Examples:**
```bash
ai-shell mysql repair orders --quick
```

---

### 11. ai-shell mysql processlist

**Purpose:** Show running processes

**Syntax:**
```bash
ai-shell mysql processlist [options]
```

**Examples:**
```bash
ai-shell mysql processlist --full
```

---

### 12. ai-shell mysql variables

**Purpose:** Show/set MySQL variables

**Syntax:**
```bash
ai-shell mysql variables [pattern] [options]
```

**Examples:**
```bash
ai-shell mysql variables "max_connections"
```

---

## MongoDB Commands

### 1-8. MongoDB Core Commands

- `ai-shell mongo connect`
- `ai-shell mongo disconnect`
- `ai-shell mongo query`
- `ai-shell mongo aggregate`
- `ai-shell mongo collections`
- `ai-shell mongo indexes`
- `ai-shell mongo import`
- `ai-shell mongo export`

### 9. ai-shell mongo stats

**Purpose:** Show collection statistics

**Syntax:**
```bash
ai-shell mongo stats <collection> [options]
```

**Examples:**
```bash
ai-shell mongo stats users
```

---

### 10. ai-shell mongo createIndex

**Purpose:** Create MongoDB index

**Syntax:**
```bash
ai-shell mongo createIndex <collection> <keys> [options]
```

**Examples:**
```bash
ai-shell mongo createIndex users '{"email": 1}' --unique
```

---

### 11. ai-shell mongo dropIndex

**Purpose:** Drop MongoDB index

**Syntax:**
```bash
ai-shell mongo dropIndex <collection> <name>
```

---

### 12. ai-shell mongo compact

**Purpose:** Compact collection

**Syntax:**
```bash
ai-shell mongo compact <collection>
```

---

## Redis Commands

### 1-12. Redis Commands

- `ai-shell redis connect`
- `ai-shell redis disconnect`
- `ai-shell redis get <key>`
- `ai-shell redis set <key> <value>`
- `ai-shell redis keys <pattern>`
- `ai-shell redis del <key...>`
- `ai-shell redis ttl <key>`
- `ai-shell redis expire <key> <seconds>`
- `ai-shell redis type <key>`
- `ai-shell redis info [section]`
- `ai-shell redis flush [database]`
- `ai-shell redis monitor`

---

## Backup & Recovery

### 1. ai-shell backup create

**Purpose:** Create database backup

**Syntax:**
```bash
ai-shell backup create [options]
```

**Options:**
- `--database <name>` - Database to backup
- `--output <path>` - Backup file path
- `--compress` - Compress backup
- `--encrypt` - Encrypt backup
- `--exclude-tables <pattern>` - Exclude tables

**Examples:**
```bash
# Full backup
ai-shell backup create --database production --output backup.sql

# Compressed backup
ai-shell backup create --compress --encrypt --output secure-backup.sql.gz

# Exclude tables
ai-shell backup create --exclude-tables "temp_*,cache_*"
```

---

### 2. ai-shell backup restore

**Purpose:** Restore from backup

**Syntax:**
```bash
ai-shell backup restore <file> [options]
```

**Options:**
- `--database <name>` - Target database
- `--point-in-time <timestamp>` - Point-in-time recovery
- `--dry-run` - Validate without restoring
- `--force` - Skip confirmation

**Examples:**
```bash
# Restore backup
ai-shell backup restore backup.sql --database mydb

# Point-in-time recovery
ai-shell backup restore backup.sql --point-in-time "2025-10-29 14:30:00"

# Dry run
ai-shell backup restore backup.sql --dry-run
```

---

### 3-10. Additional Backup Commands

- `ai-shell backup list` - List available backups
- `ai-shell backup schedule` - Schedule automatic backups
- `ai-shell backup status` - Show backup status
- `ai-shell backup validate` - Validate backup integrity
- `ai-shell backup export` - Export backup to cloud
- `ai-shell backup import` - Import backup from cloud
- `ai-shell backup cleanup` - Clean old backups
- `ai-shell backup verify` - Verify backup can be restored

---

## Migration & Schema

### 1-10. Migration Commands

- `ai-shell migrate create <name>` - Create new migration
- `ai-shell migrate up` - Run pending migrations
- `ai-shell migrate down` - Rollback last migration
- `ai-shell migrate status` - Show migration status
- `ai-shell migrate rollback [n]` - Rollback N migrations
- `ai-shell migrate history` - Show migration history
- `ai-shell migrate generate` - Generate migration from schema diff
- `ai-shell migrate validate` - Validate migrations
- `ai-shell migrate apply <name>` - Apply specific migration
- `ai-shell migrate reset` - Reset all migrations

---

## Security & Vault

### 1-10. Security Commands

- `ai-shell vault add <key> <value>` - Store credential
- `ai-shell vault get <key>` - Retrieve credential
- `ai-shell vault list` - List stored credentials
- `ai-shell vault remove <key>` - Remove credential
- `ai-shell vault rotate <key>` - Rotate credential
- `ai-shell audit log` - Show audit log
- `ai-shell audit export` - Export audit log
- `ai-shell permissions grant` - Grant permissions
- `ai-shell permissions revoke` - Revoke permissions
- `ai-shell permissions list` - List permissions

---

## SSO (Single Sign-On)

### 1. Configure SSO Provider

```bash
ai-shell sso configure <provider> [options]
```

Configure SSO provider (SAML, OAuth2, OIDC, LDAP).

**Examples**:
```bash
ai-shell sso configure okta --domain company.okta.com --client-id abc123
ai-shell sso configure azure-ad --tenant-id xyz789
ai-shell sso configure google --client-id google-client-id --client-secret secret
```

### 2. Login with SSO

```bash
ai-shell sso login [provider]
```

Authenticate using configured SSO provider.

### 3. Logout from SSO

```bash
ai-shell sso logout
```

End SSO session and clear tokens.

### 4. SSO Status

```bash
ai-shell sso status
```

Show current SSO authentication status and active sessions.

### 5. Refresh SSO Token

```bash
ai-shell sso refresh-token
```

Refresh the SSO authentication token before expiration.

### 6. Map SSO Roles

```bash
ai-shell sso map-roles <provider> [options]
```

Map SSO provider roles to application permissions.

**Example**:
```bash
ai-shell sso map-roles okta --role admin --permission full-access
```

### 7. List SSO Providers

```bash
ai-shell sso list-providers
```

Display all configured SSO providers.

### 8. Show SSO Configuration

```bash
ai-shell sso show-config [provider]
```

Display SSO provider configuration details.

### 9. Remove SSO Provider

```bash
ai-shell sso remove-provider <provider>
```

Remove a configured SSO provider.

---

## Context Management

### 1. Save Context

```bash
ai-shell context save <name> [options]
```

Save current database context (connections, queries, results) for later use.

**Options**:
- `--description, -d <text>`: Context description
- `--tags, -t <tags>`: Comma-separated tags

**Example**:
```bash
ai-shell context save pre-migration --description "Before schema migration" --tags "backup,migration"
```

### 2. Load Context

```bash
ai-shell context load <name>
```

Restore a previously saved context.

### 3. List Contexts

```bash
ai-shell context list [options]
```

List all saved contexts.

**Options**:
- `--tags, -t <tags>`: Filter by tags
- `--format, -f <format>`: Output format (table, json, yaml)

### 4. Delete Context

```bash
ai-shell context delete <name>
```

Delete a saved context.

### 5. Export Context

```bash
ai-shell context export <name> [file]
```

Export context to a file for sharing or backup.

**Example**:
```bash
ai-shell context export production-state ./contexts/prod-backup.json
```

### 6. Import Context

```bash
ai-shell context import <file>
```

Import a context from an exported file.

### 7. Show Context

```bash
ai-shell context show [name]
```

Display detailed information about a context (current or specified).

### 8. Context Diff

```bash
ai-shell context diff <name1> <name2>
```

Compare two contexts and show differences.

**Example**:
```bash
ai-shell context diff before-migration after-migration
```

### 9. Current Context

```bash
ai-shell context current
```

Display information about the current active context.

---

## Session Management

### 1. Start Session

```bash
ai-shell session start [name]
```

Start a new named session for tracking work and history.

**Example**:
```bash
ai-shell session start migration-2024-01
```

### 2. End Session

```bash
ai-shell session end
```

End the current session and save history.

### 3. List Sessions

```bash
ai-shell session list [options]
```

List all sessions with status and metadata.

**Options**:
- `--active`: Show only active sessions
- `--format, -f <format>`: Output format

### 4. Restore Session

```bash
ai-shell session restore <name>
```

Restore a previous session with all its context and history.

### 5. Export Session

```bash
ai-shell session export <name> [file]
```

Export session data for backup or sharing.

**Example**:
```bash
ai-shell session export migration-2024-01 ./sessions/migration-backup.json
```

---

## Analytics & Monitoring

### 1-10. Analytics Commands

- `ai-shell metrics show` - Show performance metrics
- `ai-shell metrics export` - Export metrics
- `ai-shell trends analyze` - Analyze trends
- `ai-shell insights generate` - Generate insights
- `ai-shell reports create` - Create report
- `ai-shell reports schedule` - Schedule reports
- `ai-shell dashboard launch` - Launch TUI dashboard
- `ai-shell health check` - Health check
- `ai-shell alerts list` - List alerts
- `ai-shell alerts configure` - Configure alerts

---

## Command Chaining & Workflows

### Piping Commands

```bash
# Optimize slow queries
ai-shell slow-queries --threshold 1000 | ai-shell optimize

# Backup before migration
ai-shell backup create && ai-shell migrate up

# Export and analyze
ai-shell pg export orders --format json | ai-shell trends analyze
```

---

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Invalid arguments
- `3` - Connection error
- `4` - Query error
- `5` - Permission denied
- `6` - Operation cancelled by user

---

## Environment Variables

```bash
ANTHROPIC_API_KEY       # Claude AI API key (required)
DATABASE_URL            # Default database connection
AI_SHELL_CONFIG         # Config file path
AI_SHELL_LOG_LEVEL      # Log level (debug, info, warn, error)
AI_SHELL_OUTPUT_FORMAT  # Default output format
AI_SHELL_VAULT_KEY      # Vault encryption key
```

---

## Configuration File

Location: `~/.ai-shell/config.yaml`

```yaml
# Database connections
databases:
  production:
    type: postgres
    host: prod.db.com
    port: 5432
    database: myapp
    pool_size: 10
    ssl: true

# Output preferences
output:
  default_format: table
  color_enabled: true
  timestamp: true

# Performance
performance:
  query_timeout: 30000
  max_connections: 10
  cache_enabled: true

# Security
security:
  vault_enabled: true
  audit_logging: true
  require_confirmation: true
```

---

## Tips & Best Practices

### Performance

1. Use `--limit` for large result sets
2. Enable connection pooling for frequent queries
3. Use `--explain` to understand query performance
4. Run `analyze` regularly on large tables

### Safety

1. Always use `--dry-run` for dangerous operations
2. Create backups before migrations
3. Use `risk-check` before DELETE/UPDATE operations
4. Enable audit logging in production

### Optimization

1. Use `slow-queries` to identify bottlenecks
2. Apply index recommendations regularly
3. Monitor with `pg activity` or `mysql processlist`
4. Use `pattern-detect` to find anti-patterns

---

## Getting Help

```bash
# General help
ai-shell --help

# Command-specific help
ai-shell optimize --help

# Show examples
ai-shell examples optimize

# View documentation
ai-shell docs optimize
```

---

## Version History

**2.0.0** (Oct 29, 2025) - Phase 2 Complete
- 105 commands implemented
- Multi-database support (PostgreSQL, MySQL, MongoDB, Redis)
- Comprehensive backup and migration
- Security and vault commands
- Analytics and monitoring

**1.0.0** (Oct 28, 2025) - Phase 1
- Initial release
- Query optimization
- Natural language translation
- PostgreSQL support

---

**Need more help?** Visit [docs.ai-shell.dev](https://docs.ai-shell.dev) or join our [Discord](https://discord.gg/ai-shell)
