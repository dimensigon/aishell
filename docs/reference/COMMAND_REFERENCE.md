# AI-Shell Command Reference

Comprehensive reference guide for all 106+ CLI commands in AI-Shell.

## Table of Contents

- [Quick Reference Table](#quick-reference-table)
- [Commands by Category](#commands-by-category)
  - [Connection Commands](#connection-commands)
  - [Query Optimization Commands](#query-optimization-commands)
  - [Schema Commands](#schema-commands)
  - [Index Commands](#index-commands)
  - [Performance Commands](#performance-commands)
  - [Backup Commands](#backup-commands)
  - [Security Commands](#security-commands)
  - [Monitoring Commands](#monitoring-commands)
  - [Database-Specific Commands](#database-specific-commands)
  - [Integration Commands](#integration-commands)
  - [Context Management](#context-management)
  - [Session Management](#session-management)
  - [Utility Commands](#utility-commands)
- [Database-Specific Commands](#database-specific-section)
- [Advanced Usage](#advanced-usage)
- [Command Index](#command-index)

---

## Quick Reference Table

| Command | Database | Category | Description |
|---------|----------|----------|-------------|
| `connect` | All | Connection | Connect to a database |
| `disconnect` | All | Connection | Disconnect from database |
| `connections` | All | Connection | List active connections |
| `use` | All | Connection | Switch active connection |
| `optimize` | SQL | Query | AI-powered query optimization |
| `analyze-slow-queries` | All | Performance | Analyze slow queries |
| `translate` | SQL | Query | Natural language to SQL |
| `explain` | SQL | Query | Explain query execution |
| `health-check` | All | Monitoring | Database health check |
| `monitor` | All | Monitoring | Real-time monitoring |
| `backup` | All | Backup | Create backup |
| `restore` | All | Backup | Restore from backup |
| `vault-add` | All | Security | Add credential to vault |
| `audit-log` | All | Security | View audit logs |
| `mysql connect` | MySQL | Database | Connect to MySQL |
| `mongo connect` | MongoDB | Database | Connect to MongoDB |
| `redis connect` | Redis | Database | Connect to Redis |
| `migration create` | SQL | Migration | Create migration file |
| `migration up` | SQL | Migration | Run migrations |
| `slack setup` | All | Integration | Setup Slack integration |
| `context save` | All | Context | Save current context |
| `dashboard` | All | Monitoring | Launch dashboard |

---

## Commands by Category

### Connection Commands

#### ai-shell connect

**Description:** Connect to a database (PostgreSQL, MySQL, MongoDB, Redis, SQLite)

**Syntax:**
```bash
ai-shell connect <connection-string> [options]
```

**Options:**
- `--name <name>` - Connection name (default: auto-generated)
- `--test` - Test connection only without saving
- `--set-active` - Set as active connection (default: true)

**Examples:**
```bash
# Connect to PostgreSQL
ai-shell connect postgresql://user:pass@localhost:5432/mydb --name production

# Connect to MySQL
ai-shell connect mysql://root:secret@localhost:3306/testdb

# Connect to MongoDB
ai-shell connect mongodb://localhost:27017/appdb --name mongo

# Connect to Redis
ai-shell connect redis://localhost:6379 --name cache

# Test connection without saving
ai-shell connect postgresql://localhost/mydb --test
```

**Output:**
```
🔌 Connecting to database...

✅ Connected successfully!
   Name: production
   Type: postgresql
   Database: mydb
   Host: localhost
```

**Related Commands:**
- `disconnect` - Disconnect from database
- `connections` - List all connections
- `use` - Switch active connection

---

#### ai-shell disconnect

**Description:** Disconnect from database (disconnect all if no name provided)

**Syntax:**
```bash
ai-shell disconnect [name]
```

**Examples:**
```bash
# Disconnect specific connection
ai-shell disconnect production

# Disconnect all connections
ai-shell disconnect
```

**Output:**
```
🔌 Disconnecting from: production

✅ Disconnected successfully
```

**Related Commands:**
- `connect` - Connect to database
- `connections` - List connections

---

#### ai-shell connections

**Description:** List active database connections

**Aliases:** `conns`

**Syntax:**
```bash
ai-shell connections [options]
```

**Options:**
- `--verbose` - Show detailed connection information
- `--health` - Run health checks on all connections

**Examples:**
```bash
# List all connections
ai-shell connections

# Detailed view
ai-shell conns --verbose

# With health checks
ai-shell connections --health
```

**Output:**
```
📊 Active Connections (3)

┌────────────┬──────────┬──────────┬─────────────┬────────┐
│ Name       │ Type     │ Database │ Host:Port   │ Active │
├────────────┼──────────┼──────────┼─────────────┼────────┤
│ production │ postgres │ mydb     │ localhost   │ ✓      │
│ staging    │ mysql    │ testdb   │ 10.0.1.5    │        │
│ cache      │ redis    │ 0        │ localhost   │        │
└────────────┴──────────┴──────────┴─────────────┴────────┘
```

**Related Commands:**
- `connect` - Add new connection
- `use` - Switch active connection
- `health-check` - Check connection health

---

#### ai-shell use

**Description:** Switch active database connection

**Syntax:**
```bash
ai-shell use <connection-name>
```

**Examples:**
```bash
# Switch to production database
ai-shell use production

# Switch to staging
ai-shell use staging
```

**Output:**
```
✅ Active connection switched to: production
```

**Related Commands:**
- `connections` - List available connections
- `connect` - Create new connection

---

### Query Optimization Commands

#### ai-shell optimize

**Description:** Optimize a SQL query using AI analysis

**Aliases:** `opt`

**Syntax:**
```bash
ai-shell optimize <query> [options]
```

**Options:**
- `--explain` - Show query execution plan
- `--dry-run` - Validate without executing
- `--format <type>` - Output format (text, json)

**Examples:**
```bash
# Basic optimization
ai-shell optimize "SELECT * FROM users WHERE id > 100"

# With execution plan
ai-shell opt "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id" --explain

# Dry run mode
ai-shell optimize "DELETE FROM users WHERE inactive = true" --dry-run

# JSON output
ai-shell optimize "SELECT * FROM orders" --format json
```

**Output:**
```
🔍 Analyzing Query...

Original Query:
  SELECT * FROM users WHERE id > 100

Issues Found:
  ⚠️  SELECT * returns unnecessary columns
  ⚠️  Missing index on 'id' column
  ⚠️  No LIMIT clause on potentially large result

Optimized Query:
  SELECT id, name, email FROM users WHERE id > 100 LIMIT 1000

Performance Impact:
  • Estimated speedup: 3.2x faster
  • Reduced data transfer: 65% less
  • Index recommendation: CREATE INDEX idx_users_id ON users(id)

💡 Recommendations:
  1. Create index on users(id)
  2. Add LIMIT clause to prevent large result sets
  3. Select only required columns
```

**Related Commands:**
- `analyze-slow-queries` - Analyze slow queries
- `explain` - Explain query execution
- `indexes analyze` - Analyze indexes

---

#### ai-shell analyze-slow-queries

**Description:** Analyze and optimize slow queries from query log

**Aliases:** `slow`

**Syntax:**
```bash
ai-shell analyze-slow-queries [options]
```

**Options:**
- `-t, --threshold <ms>` - Minimum execution time in milliseconds (default: 1000)
- `-l, --limit <n>` - Number of queries to show (default: 10)
- `--last <period>` - Time period (e.g., 24h, 7d, 30d)
- `--auto-fix` - Automatically optimize slow queries
- `--export <file>` - Export results to file

**Examples:**
```bash
# Basic analysis
ai-shell analyze-slow-queries

# Custom threshold
ai-shell slow --threshold 500

# Last 7 days with auto-fix
ai-shell slow --last 7d --auto-fix

# Export results
ai-shell analyze-slow-queries --export slow-queries.json
```

**Output:**
```
🐌 Found 5 slow queries:

⏱️  3254.12ms (15x)
   SELECT o.*, u.name FROM orders o JOIN users u ON o.user_id = u.id WHERE o.created_at > '2024-01-01'
   💡 Suggestions:
      - Add index on orders.created_at
      - Consider using JOIN on indexed columns only
      - Add LIMIT clause

⏱️  2847.58ms (8x)
   SELECT * FROM products WHERE category IN (SELECT id FROM categories WHERE active = 1)
   💡 Suggestions:
      - Rewrite subquery as JOIN
      - Add index on categories.active
```

**Related Commands:**
- `optimize` - Optimize single query
- `slow-queries` - Advanced slow query analysis
- `indexes analyze` - Analyze indexes

---

#### ai-shell translate

**Description:** Convert natural language to SQL query

**Aliases:** `nl2sql`

**Syntax:**
```bash
ai-shell translate <natural-language> [options]
```

**Options:**
- `-f, --format <type>` - Output format (json, table, csv)
- `-o, --output <file>` - Export result to file
- `--execute` - Execute the generated SQL query

**Examples:**
```bash
# Basic translation
ai-shell translate "show me all users"

# Execute generated query
ai-shell translate "find orders from last week" --execute

# Complex query
ai-shell nl2sql "count active users by country"

# Export result
ai-shell translate "show top 10 products by sales" --execute --format json
```

**Output:**
```
🤖 Translating natural language to SQL...

Input: "show me all active users created in the last 30 days"

Generated SQL:
  SELECT * FROM users
  WHERE active = true
    AND created_at >= NOW() - INTERVAL '30 days'
  ORDER BY created_at DESC

Explanation:
  • Filters for active users (active = true)
  • Checks creation date within last 30 days
  • Sorts by most recent first

Execute this query? (y/n)
```

**Related Commands:**
- `optimize` - Optimize generated query
- `explain` - Explain query execution

---

#### ai-shell explain

**Description:** Get AI-powered explanation of SQL query

**Aliases:** `exp`

**Syntax:**
```bash
ai-shell explain <query> [options]
```

**Options:**
- `--format <type>` - Output format (text, json)
- `--analyze` - Include performance analysis
- `--dry-run` - Validate query without execution

**Examples:**
```bash
# Basic explanation
ai-shell explain "SELECT * FROM users WHERE created_at > NOW() - INTERVAL 7 DAY"

# With performance analysis
ai-shell exp "SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o GROUP BY u.id" --analyze

# JSON format
ai-shell explain "SELECT * FROM users" --format json

# Dry run validation
ai-shell explain "UPDATE users SET active = false WHERE last_login < '2023-01-01'" --dry-run
```

**Output:**
```
📊 Query Explanation:

Query: SELECT * FROM users WHERE created_at > NOW() - INTERVAL 7 DAY

What it does:
  Retrieves all user records created within the last 7 days

Step-by-step breakdown:
  1. Scans the 'users' table
  2. Filters rows where created_at is within the last 7 days
  3. Returns all columns for matching rows

Performance considerations:
  • Full table scan if no index on created_at
  • Returns all columns (SELECT *)
  • Date calculation on each comparison

Optimization suggestions:
  ✓ Add index: CREATE INDEX idx_users_created ON users(created_at)
  ✓ Limit result set with LIMIT clause
  ✓ Select only needed columns instead of *
```

**Related Commands:**
- `optimize` - Optimize the query
- `analyze-slow-queries` - Analyze performance

---

#### ai-shell optimize-all

**Description:** Optimize all slow queries automatically

**Syntax:**
```bash
ai-shell optimize-all [options]
```

**Options:**
- `--threshold <ms>` - Only optimize queries slower than threshold (default: 1000)
- `--auto-apply` - Apply all recommendations automatically
- `--report <file>` - Save optimization report to file

**Examples:**
```bash
# Optimize all slow queries
ai-shell optimize-all

# Custom threshold with auto-apply
ai-shell optimize-all --threshold 500 --auto-apply

# Generate report
ai-shell optimize-all --report optimization-report.json
```

**Output:**
```
🔄 Optimizing all slow queries...

Found 12 slow queries (>1000ms)

Query 1/12: SELECT * FROM orders WHERE user_id = 123
  Original: 2340ms
  Optimized: 145ms
  Improvement: 16.1x faster
  ✓ Applied optimization

Query 2/12: SELECT u.*, COUNT(o.id) FROM users u...
  Original: 1820ms
  Optimized: 320ms
  Improvement: 5.7x faster
  ✓ Applied optimization

Summary:
  Total queries optimized: 12
  Average improvement: 8.3x faster
  Total time saved: 18.4 seconds per execution cycle
```

**Related Commands:**
- `optimize` - Optimize single query
- `slow-queries` - View slow query details

---

### Schema Commands

#### ai-shell design-schema

**Description:** Interactive schema design with AI assistance

**Aliases:** `design`

**Syntax:**
```bash
ai-shell design-schema
```

**Examples:**
```bash
# Start interactive schema designer
ai-shell design-schema

# Using alias
ai-shell design
```

**Output:**
```
🎨 AI-Powered Schema Designer

? What type of application are you building?
  > E-commerce
    Social Network
    Blog/CMS
    SaaS Platform
    Custom

? Describe your data requirements:
> I need to track users, products, orders, and reviews

🤖 Analyzing requirements...

Recommended Schema:

Table: users
  - id (UUID, PRIMARY KEY)
  - email (VARCHAR, UNIQUE)
  - password_hash (VARCHAR)
  - created_at (TIMESTAMP)
  - updated_at (TIMESTAMP)

Table: products
  - id (UUID, PRIMARY KEY)
  - name (VARCHAR)
  - description (TEXT)
  - price (DECIMAL)
  - stock (INTEGER)
  - created_at (TIMESTAMP)

Table: orders
  - id (UUID, PRIMARY KEY)
  - user_id (UUID, FOREIGN KEY -> users)
  - total_amount (DECIMAL)
  - status (ENUM: pending, paid, shipped, delivered)
  - created_at (TIMESTAMP)

Table: order_items
  - id (UUID, PRIMARY KEY)
  - order_id (UUID, FOREIGN KEY -> orders)
  - product_id (UUID, FOREIGN KEY -> products)
  - quantity (INTEGER)
  - price (DECIMAL)

? Would you like to generate migration files? (Y/n)
```

**Related Commands:**
- `validate-schema` - Validate schema definition
- `schema export` - Export schema
- `migration create` - Create migration

---

#### ai-shell validate-schema

**Description:** Validate schema definition file

**Aliases:** `validate`

**Syntax:**
```bash
ai-shell validate-schema <file>
```

**Examples:**
```bash
# Validate JSON schema
ai-shell validate-schema schema.json

# Validate YAML schema
ai-shell validate ./schemas/users.yaml
```

**Output:**
```
✓ Validating schema: schema.json

Schema Structure: Valid
  • 5 tables defined
  • 23 columns total
  • 8 indexes defined
  • 6 foreign keys defined

Validation Results:

✓ Table naming conventions
✓ Column data types
✓ Primary keys defined
✓ Foreign key constraints valid
⚠️  Missing indexes on foreign keys: orders.user_id
⚠️  No created_at/updated_at timestamps on 'products' table

Recommendations:
  1. Add index on orders.user_id for JOIN performance
  2. Add timestamp columns for audit trail
  3. Consider adding soft delete (deleted_at) column
```

**Related Commands:**
- `design-schema` - Create schema interactively
- `schema diff` - Compare schemas

---

#### ai-shell schema diff

**Description:** Compare schemas between two databases

**Syntax:**
```bash
ai-shell schema diff <db1> <db2> [options]
```

**Options:**
- `-o, --output <file>` - Output diff to file
- `-f, --format <type>` - Output format (text, json, sql)

**Examples:**
```bash
# Compare schemas
ai-shell schema diff production staging

# Export to file
ai-shell schema diff db1 db2 --output schema-diff.json --format json

# Generate SQL migration
ai-shell schema diff production staging --format sql --output migrate.sql
```

**Output:**
```
🔍 Schema Comparison: production vs staging

Tables:
  + users (exists in production only)
  + audit_log (exists in production only)
  - temp_data (exists in staging only)
  ≈ products (different structure)

Columns in 'products':
  + sku (VARCHAR, added in production)
  + category_id (INTEGER, added in production)
  - old_price (DECIMAL, removed from production)
  ≈ description (TEXT in production, VARCHAR in staging)

Indexes:
  + idx_products_category (production)
  - idx_old_price (staging)

Foreign Keys:
  + products.category_id -> categories.id (production)

Summary:
  • 2 tables added
  • 1 table removed
  • 1 table modified
  • 5 column changes
  • 2 index changes
  • 1 foreign key added
```

**Related Commands:**
- `schema sync` - Sync schemas
- `schema export` - Export schema
- `migration create` - Create migration

---

#### ai-shell schema sync

**Description:** Synchronize schema from source to target database

**Syntax:**
```bash
ai-shell schema sync <source> <target> [options]
```

**Options:**
- `-d, --dry-run` - Show SQL without executing

**Examples:**
```bash
# Dry run (preview changes)
ai-shell schema sync production staging --dry-run

# Actual sync
ai-shell schema sync production staging
```

**Output:**
```
🔄 Synchronizing schema: production → staging

Generating migration script...

SQL to execute:
  CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
  );

  ALTER TABLE products ADD COLUMN sku VARCHAR(50);
  ALTER TABLE products ADD COLUMN category_id INTEGER;
  ALTER TABLE products DROP COLUMN old_price;

  CREATE INDEX idx_products_category ON products(category_id);
  ALTER TABLE products ADD CONSTRAINT fk_category
    FOREIGN KEY (category_id) REFERENCES categories(id);

Execute these changes? (y/n)
```

**Related Commands:**
- `schema diff` - Compare schemas
- `migration create` - Create migration

---

#### ai-shell schema export

**Description:** Export schema to file

**Syntax:**
```bash
ai-shell schema export <file> [options]
```

**Options:**
- `-f, --format <type>` - Format (sql, json, yaml)
- `--include-data` - Include sample data

**Examples:**
```bash
# Export as SQL
ai-shell schema export schema.sql --format sql

# Export as JSON
ai-shell schema export schema.json --format json

# Include data
ai-shell schema export full-export.sql --include-data
```

**Output:**
```
📤 Exporting schema...

✓ Exported 8 tables
✓ Exported 45 columns
✓ Exported 12 indexes
✓ Exported 7 foreign keys

Schema saved to: schema.sql
Size: 24.5 KB
```

**Related Commands:**
- `schema import` - Import schema
- `backup create` - Full backup

---

#### ai-shell schema import

**Description:** Import schema from file

**Syntax:**
```bash
ai-shell schema import <file>
```

**Examples:**
```bash
# Import SQL file
ai-shell schema import schema.sql

# Import JSON definition
ai-shell schema import schema.json
```

**Output:**
```
📥 Importing schema from: schema.sql

✓ Created table: users
✓ Created table: products
✓ Created table: orders
✓ Created 8 indexes
✓ Created 6 foreign keys

Import complete!
  • 5 tables created
  • 8 indexes created
  • 6 foreign keys created
```

**Related Commands:**
- `schema export` - Export schema
- `migration create` - Create migration

---

### Index Commands

#### ai-shell indexes analyze

**Description:** Analyze indexes and provide recommendations

**Syntax:**
```bash
ai-shell indexes analyze [table]
```

**Examples:**
```bash
# Analyze all indexes
ai-shell indexes analyze

# Analyze specific table
ai-shell indexes analyze users
```

**Output:**
```
📊 Index Analysis Report

Table: users
  Indexes:
    ✓ PRIMARY KEY (id) - Used: 98.5% - Size: 45 MB
    ✓ UNIQUE (email) - Used: 87.2% - Size: 12 MB
    ⚠️  INDEX (last_login) - Used: 2.1% - Size: 8 MB - UNUSED
    ✓ INDEX (created_at) - Used: 45.6% - Size: 6 MB

Table: orders
  Indexes:
    ✓ PRIMARY KEY (id) - Used: 99.1% - Size: 128 MB
    ✓ INDEX (user_id) - Used: 95.3% - Size: 64 MB
    ⚠️  INDEX (status, created_at) - Used: 8.4% - Size: 42 MB - LOW USAGE

Recommendations:
  1. DROP INDEX last_login on users (unused, wasting 8 MB)
  2. Consider composite index on orders(user_id, status) for common queries
  3. Rebuild fragmented indexes on orders table (30% fragmentation)
```

**Related Commands:**
- `indexes missing` - Find missing indexes
- `indexes stats` - Index statistics
- `indexes rebuild` - Rebuild indexes

---

#### ai-shell indexes missing

**Description:** Detect missing indexes from query patterns

**Syntax:**
```bash
ai-shell indexes missing
```

**Examples:**
```bash
# Analyze query patterns for missing indexes
ai-shell indexes missing
```

**Output:**
```
🔍 Analyzing query patterns for missing indexes...

Missing Index Recommendations:

1. Table: orders, Column: user_id
   Impact: HIGH
   Frequency: 1,247 queries/day
   Avg query time: 2,340ms -> estimated 45ms with index
   Recommended: CREATE INDEX idx_orders_user_id ON orders(user_id);

2. Table: products, Columns: category_id, price
   Impact: MEDIUM
   Frequency: 342 queries/day
   Avg query time: 890ms -> estimated 120ms with index
   Recommended: CREATE INDEX idx_products_category_price ON products(category_id, price);

3. Table: users, Column: created_at
   Impact: LOW
   Frequency: 89 queries/day
   Avg query time: 450ms -> estimated 80ms with index
   Recommended: CREATE INDEX idx_users_created ON users(created_at);

Total potential time savings: ~3.2 hours/day
```

**Related Commands:**
- `indexes analyze` - Analyze existing indexes
- `indexes create` - Create index

---

#### ai-shell indexes recommendations

**Description:** Get AI-powered index recommendations

**Syntax:**
```bash
ai-shell indexes recommendations
```

**Examples:**
```bash
# Get index recommendations
ai-shell indexes recommendations
```

**Output:**
```
💡 AI Index Recommendations

Based on workload analysis:

High Priority:
  1. CREATE INDEX idx_orders_user_status ON orders(user_id, status);
     Reason: Covers 45% of queries, expected 12x speedup
     Impact: Very High

  2. CREATE INDEX idx_products_category ON products(category_id);
     Reason: Foreign key without index, JOIN bottleneck
     Impact: High

Medium Priority:
  3. CREATE INDEX idx_users_email_active ON users(email, active);
     Reason: Common WHERE clause combination
     Impact: Medium

Low Priority:
  4. DROP INDEX idx_users_temp ON users;
     Reason: Never used, wasting space
     Impact: Low (save 15 MB)
```

**Related Commands:**
- `indexes analyze` - Analyze indexes
- `indexes create` - Create index

---

#### ai-shell indexes create

**Description:** Create a new index

**Syntax:**
```bash
ai-shell indexes create <table> <columns> [options]
```

**Options:**
- `--name <name>` - Index name
- `--unique` - Create unique index
- `--concurrently` - Create without locking table (PostgreSQL)

**Examples:**
```bash
# Simple index
ai-shell indexes create users email

# Composite index
ai-shell indexes create orders user_id,status --name idx_orders_user_status

# Unique index
ai-shell indexes create products sku --unique

# Concurrent creation
ai-shell indexes create orders created_at --concurrently
```

**Output:**
```
🔨 Creating index...

Index: idx_users_email
Table: users
Columns: email
Type: B-tree

Creating... (this may take a while for large tables)

✓ Index created successfully
  Time: 3.2 seconds
  Size: 8.5 MB
```

**Related Commands:**
- `indexes drop` - Remove index
- `indexes analyze` - Analyze indexes

---

#### ai-shell indexes drop

**Description:** Drop an existing index

**Syntax:**
```bash
ai-shell indexes drop <index-name> [options]
```

**Options:**
- `--cascade` - Drop dependent objects
- `--if-exists` - Don't error if index doesn't exist

**Examples:**
```bash
# Drop index
ai-shell indexes drop idx_users_temp

# With cascade
ai-shell indexes drop idx_orders_status --cascade

# Safe drop
ai-shell indexes drop idx_old_index --if-exists
```

**Output:**
```
⚠️  Are you sure you want to drop index 'idx_users_temp'?
   Table: users
   Size: 15 MB
   Last used: 30 days ago

Confirm deletion? (yes/no): yes

✓ Index dropped successfully
  Freed space: 15 MB
```

**Related Commands:**
- `indexes create` - Create index
- `indexes analyze` - Analyze indexes

---

#### ai-shell indexes rebuild

**Description:** Rebuild indexes

**Syntax:**
```bash
ai-shell indexes rebuild [table] [options]
```

**Options:**
- `--all` - Rebuild all indexes
- `--online` - Rebuild without locking (if supported)

**Examples:**
```bash
# Rebuild all indexes
ai-shell indexes rebuild --all

# Rebuild indexes for specific table
ai-shell indexes rebuild orders

# Online rebuild
ai-shell indexes rebuild users --online
```

**Output:**
```
🔄 Rebuilding indexes...

Table: orders
  ✓ Rebuilding PRIMARY KEY (id)... 45s
  ✓ Rebuilding idx_orders_user... 23s
  ✓ Rebuilding idx_orders_status... 18s

Space reclaimed: 128 MB
Fragmentation reduced from 35% to 2%

Rebuild complete!
  Time: 1m 26s
  Indexes rebuilt: 3
```

**Related Commands:**
- `indexes analyze` - Check fragmentation
- `indexes stats` - View statistics

---

#### ai-shell indexes stats

**Description:** Show index statistics

**Syntax:**
```bash
ai-shell indexes stats [table]
```

**Examples:**
```bash
# All index statistics
ai-shell indexes stats

# Specific table
ai-shell indexes stats orders
```

**Output:**
```
📊 Index Statistics

Database: production
Total Indexes: 47
Total Size: 2.3 GB

Table: orders
  Index: idx_orders_user_id
    Size: 124 MB
    Scans: 45,234
    Tuples Read: 12,456,789
    Tuples Fetched: 234,567
    Cache Hit Ratio: 98.5%
    Last Used: 2 minutes ago
    Bloat: 12% (15 MB wasted)

  Index: idx_orders_status
    Size: 45 MB
    Scans: 12,890
    Cache Hit Ratio: 95.2%
    Last Used: 15 minutes ago
    Bloat: 5% (2 MB wasted)

Top 5 Most Used Indexes:
  1. orders.idx_orders_user_id - 45,234 scans
  2. users.idx_users_email - 38,902 scans
  3. products.idx_products_sku - 28,456 scans
```

**Related Commands:**
- `indexes analyze` - Detailed analysis
- `indexes rebuild` - Rebuild indexes

---

### Performance Commands

#### ai-shell monitor

**Description:** Start real-time database monitoring

**Syntax:**
```bash
ai-shell monitor [options]
```

**Options:**
- `-i, --interval <ms>` - Monitoring interval in milliseconds (default: 5000)

**Examples:**
```bash
# Start monitoring with default interval
ai-shell monitor

# Custom interval (10 seconds)
ai-shell monitor --interval 10000

# Fast updates (2 seconds)
ai-shell monitor -i 2000
```

**Output:**
```
📊 Real-Time Database Monitoring (refresh: 5s)

System Metrics:
  CPU Usage: ████████░░ 78%
  Memory: █████░░░░░ 45% (2.3 GB / 8 GB)
  Disk I/O: ███░░░░░░░ 28%

Connections:
  Active: 45 / 100
  Idle: 12
  Waiting: 2

Query Performance:
  Queries/sec: 234
  Avg Duration: 45ms
  Slow Queries: 3

Cache:
  Hit Rate: 94.5%
  Size: 512 MB / 1 GB

Top Queries (last 5 min):
  1. SELECT * FROM orders WHERE... (234ms, 45x)
  2. UPDATE users SET last_seen... (123ms, 89x)

Press 'q' to quit
```

**Related Commands:**
- `dashboard` - Interactive dashboard
- `health-check` - Health check
- `metrics show` - View metrics

---

#### ai-shell dashboard

**Description:** Launch interactive performance dashboard

**Syntax:**
```bash
ai-shell dashboard [options]
```

**Options:**
- `-i, --interval <seconds>` - Update interval in seconds (default: 5)

**Examples:**
```bash
# Launch dashboard
ai-shell dashboard

# Custom refresh interval
ai-shell dashboard --interval 10
```

**Output:**
```
┌─────────────────────────────────────────────────────────────┐
│               🚀 AI-Shell Performance Dashboard             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Database: production (PostgreSQL 14.2)                     │
│  Uptime: 45 days, 12:34:56                                  │
│  Last Update: 2024-01-15 10:23:45                           │
│                                                             │
├───────────────────────┬─────────────────────────────────────┤
│   System Metrics      │   Connection Pool                   │
├───────────────────────┼─────────────────────────────────────┤
│                       │                                     │
│  CPU:  ████████░░ 78% │  Active:   45 / 100                 │
│  Mem:  █████░░░░░ 45% │  Idle:     12                       │
│  Disk: ███░░░░░░░ 28% │  Waiting:  2                        │
│                       │  Wait Time: 12ms                    │
│                       │                                     │
├───────────────────────┼─────────────────────────────────────┤
│   Query Stats         │   Cache Performance                 │
├───────────────────────┼─────────────────────────────────────┤
│                       │                                     │
│  Queries/sec: 234     │  Hit Rate:  94.5%                   │
│  Avg Time:    45ms    │  Hits:      12,456                  │
│  Slow:        3       │  Misses:    723                     │
│  Errors:      0       │  Size:      512MB / 1GB             │
│                       │                                     │
├───────────────────────────────────────────────────────────  ┤
│   Slow Queries (>1000ms)                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. SELECT * FROM orders WHERE user_id IN...   2340ms (15x) │
│  2. UPDATE products SET stock = stock - 1...   1890ms (8x)  │
│  3. SELECT u.*, COUNT(o.id) FROM users u...    1245ms (3x)  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

[q] Quit  [r] Refresh  [s] Settings  [h] Help
```

**Related Commands:**
- `monitor` - Simple monitoring
- `metrics show` - View metrics
- `analyze-slow-queries` - Slow query analysis

---

#### ai-shell health-check

**Description:** Perform comprehensive database health check

**Aliases:** `health`

**Syntax:**
```bash
ai-shell health-check
```

**Examples:**
```bash
# Run health check
ai-shell health-check

# Using alias
ai-shell health
```

**Output:**
```
🏥 Database Health Check

System Health: ✓ HEALTHY

✓ Connection Pool
  Status: Healthy
  Active: 45 / 100 connections
  Avg wait time: 12ms

✓ Query Performance
  Avg query time: 45ms
  Slow queries: 3 (<1% of total)
  Error rate: 0.01%

⚠️  Disk Space
  Status: Warning
  Used: 85% of 100 GB
  Free: 15 GB
  Recommendation: Consider cleanup or expansion

✓ Indexes
  Total: 47 indexes
  Unused: 2 (4%)
  Fragmented: 3 (6%)
  Recommendation: Run 'ai-shell indexes rebuild'

⚠️  Backups
  Last backup: 8 hours ago
  Status: Warning
  Recommendation: Backup older than 6 hours

✓ Replication
  Status: Healthy
  Lag: 234ms
  Replicas: 2/2 healthy

Overall Score: 85/100 (Good)

Recommendations:
  1. Free up disk space or add storage
  2. Run backup immediately
  3. Rebuild fragmented indexes
```

**Related Commands:**
- `monitor` - Real-time monitoring
- `alerts setup` - Configure alerts

---

#### ai-shell metrics show

**Description:** Show current performance metrics

**Syntax:**
```bash
ai-shell metrics show [options]
```

**Options:**
- `--format <type>` - Output format (table, json, prometheus)

**Examples:**
```bash
# Show metrics
ai-shell metrics show

# JSON format
ai-shell metrics show --format json

# Prometheus format
ai-shell metrics show --format prometheus
```

**Output:**
```
📊 Current Performance Metrics

Database Metrics:
  Connections: 45
  Active Queries: 12
  Transactions/sec: 234
  Commits: 12,456
  Rollbacks: 23

Query Metrics:
  Total Queries: 45,678
  Queries/sec: 234
  Avg Duration: 45ms
  Slow Queries (>1s): 3
  Failed Queries: 5

Cache Metrics:
  Hit Rate: 94.5%
  Hits: 12,456
  Misses: 723
  Size: 512 MB
  Evictions: 89

System Metrics:
  CPU Usage: 78%
  Memory Usage: 2.3 GB
  Disk I/O: 28 MB/s
  Network I/O: 12 MB/s
```

**Related Commands:**
- `metrics export` - Export metrics
- `monitor` - Real-time monitoring

---

#### ai-shell metrics export

**Description:** Export metrics in various formats

**Syntax:**
```bash
ai-shell metrics export <file> [options]
```

**Options:**
- `--format <type>` - Format (json, csv, prometheus)
- `--interval <seconds>` - Collection interval for time series

**Examples:**
```bash
# Export as JSON
ai-shell metrics export metrics.json

# Export as CSV
ai-shell metrics export metrics.csv --format csv

# Export Prometheus metrics
ai-shell metrics export metrics.prom --format prometheus
```

**Output:**
```
📤 Exporting metrics...

✓ Collected 234 data points
✓ Exported to: metrics.json
  Size: 45 KB
  Format: JSON
  Time Range: Last 1 hour
```

**Related Commands:**
- `metrics show` - View current metrics
- `prometheus` - Prometheus integration

---

#### ai-shell performance analyze

**Description:** Analyze system performance

**Syntax:**
```bash
ai-shell performance analyze
```

**Examples:**
```bash
# Analyze performance
ai-shell performance analyze
```

**Output:**
```
🔬 Performance Analysis Report

Analysis Period: Last 24 hours

Query Performance:
  Total Queries: 1,234,567
  Avg Duration: 67ms
  95th Percentile: 234ms
  99th Percentile: 890ms

  Trend: ↑ 15% slower than previous period

  Bottlenecks Identified:
    1. Missing index on orders.user_id (affects 45% of queries)
    2. N+1 query pattern in user profile endpoint
    3. Full table scans on products table

Resource Utilization:
  CPU: Avg 45%, Peak 89%
  Memory: Avg 2.1 GB, Peak 3.4 GB
  Disk I/O: Avg 23 MB/s, Peak 89 MB/s

  Concerns:
    ⚠️  CPU spikes during peak hours (8-10am)
    ⚠️  Memory trending upward (possible leak)

Recommendations:
  Priority 1: Add missing indexes (expected 3x speedup)
  Priority 2: Fix N+1 queries (expected 80% reduction in queries)
  Priority 3: Investigate memory trend
  Priority 4: Consider caching for product queries
```

**Related Commands:**
- `performance report` - Generate report
- `analyze-slow-queries` - Query analysis

---

#### ai-shell performance report

**Description:** Generate performance report

**Syntax:**
```bash
ai-shell performance report [options]
```

**Options:**
- `--period <duration>` - Report period (24h, 7d, 30d)
- `--output <file>` - Save report to file
- `--format <type>` - Format (text, html, pdf)

**Examples:**
```bash
# Generate daily report
ai-shell performance report

# Weekly report
ai-shell performance report --period 7d

# Export as HTML
ai-shell performance report --format html --output report.html
```

**Output:**
```
📊 Performance Report
Period: Last 24 hours
Generated: 2024-01-15 10:00:00

Executive Summary:
  Overall Health: Good (85/100)
  Query Performance: Good
  Resource Usage: Normal
  Incidents: 2 minor

Key Metrics:
  • Total Queries: 1.2M
  • Avg Response Time: 67ms
  • Error Rate: 0.01%
  • Uptime: 99.98%

Top 5 Slowest Queries:
  1. User dashboard aggregation - 2,340ms
  2. Product search with filters - 1,890ms
  3. Order history report - 1,245ms
  4. Analytics calculation - 1,123ms
  5. User activity summary - 1,045ms

Recommendations:
  1. Add composite index on orders table
  2. Enable query caching for product searches
  3. Optimize dashboard aggregation query

Report saved to: performance-report.html
```

**Related Commands:**
- `performance analyze` - Detailed analysis
- `metrics export` - Export metrics

---

### Backup Commands

#### ai-shell backup

**Description:** Create database backup

**Syntax:**
```bash
ai-shell backup [options]
```

**Options:**
- `-c, --connection <name>` - Connection name (uses active if not specified)

**Examples:**
```bash
# Backup active connection
ai-shell backup

# Backup specific connection
ai-shell backup --connection production

# Backup with name
ai-shell backup -c staging
```

**Output:**
```
💾 Creating backup...

Database: production (PostgreSQL)
Started: 2024-01-15 10:00:00

Progress:
  Backing up schema... ✓
  Backing up data... ████████░░ 78% (2.3 GB / 3.0 GB)

Estimated time remaining: 45 seconds

✓ Backup completed successfully!

  Backup ID: backup-20240115-100000-abc123
  Size: 3.0 GB
  Compressed: 1.2 GB (60% compression)
  Duration: 3m 24s
  Location: ./backups/backup-20240115-100000.tar.gz
```

**Related Commands:**
- `restore` - Restore from backup
- `backup-list` - List backups
- `backup verify` - Verify backup integrity

---

#### ai-shell restore

**Description:** Restore database from backup

**Syntax:**
```bash
ai-shell restore <backup-id> [options]
```

**Options:**
- `-d, --dry-run` - Simulate restore without making changes
- `--target <connection>` - Target connection (default: source connection)

**Examples:**
```bash
# Restore backup
ai-shell restore backup-20240115-100000-abc123

# Dry run
ai-shell restore backup-20240115-100000-abc123 --dry-run

# Restore to different connection
ai-shell restore backup-abc123 --target staging
```

**Output:**
```
⚠️  WARNING: This will REPLACE all data in the target database!

Backup Information:
  ID: backup-20240115-100000-abc123
  Database: production
  Created: 2024-01-15 10:00:00
  Size: 3.0 GB (compressed: 1.2 GB)
  Tables: 25
  Records: 12,456,789

Target Database: production

Are you sure you want to restore? Type 'yes' to confirm: yes

🔄 Restoring backup...

Progress:
  Extracting backup... ✓
  Dropping existing tables... ✓
  Restoring schema... ✓
  Restoring data... ████████░░ 78%

Estimated time remaining: 2m 15s

✓ Restore completed successfully!
  Duration: 4m 38s
  Tables restored: 25
  Records restored: 12,456,789
```

**Related Commands:**
- `backup` - Create backup
- `backup-list` - List available backups
- `backup verify` - Verify before restore

---

#### ai-shell backup-list

**Description:** List all backups

**Aliases:** `backups`

**Syntax:**
```bash
ai-shell backup-list [options]
```

**Options:**
- `-l, --limit <count>` - Maximum number of backups to show (default: 20)

**Examples:**
```bash
# List all backups
ai-shell backup-list

# List recent 10
ai-shell backups --limit 10
```

**Output:**
```
📋 Available Backups (23 total)

┌──────────────────────────┬────────────┬────────┬───────────┬──────────────────┐
│ Backup ID                │ Database   │ Size   │ Records   │ Created          │
├──────────────────────────┼────────────┼────────┼───────────┼──────────────────┤
│ backup-20240115-100000   │ production │ 1.2 GB │ 12.4M     │ 2 hours ago      │
│ backup-20240115-040000   │ production │ 1.2 GB │ 12.3M     │ 8 hours ago      │
│ backup-20240114-220000   │ production │ 1.1 GB │ 12.1M     │ 1 day ago        │
│ backup-20240114-160000   │ staging    │ 450 MB │ 4.2M      │ 1 day ago        │
│ backup-20240114-100000   │ production │ 1.1 GB │ 11.9M     │ 2 days ago       │
└──────────────────────────┴────────────┴────────┴───────────┴──────────────────┘

Total backup size: 15.3 GB
Oldest backup: 30 days ago
```

**Related Commands:**
- `backup` - Create new backup
- `restore` - Restore backup
- `backup status` - Detailed backup info

---

#### ai-shell backup schedule

**Description:** Schedule automated backups

**Syntax:**
```bash
ai-shell backup schedule [options]
```

**Options:**
- `--cron <expression>` - Cron schedule expression
- `--interval <duration>` - Interval (e.g., 6h, 12h, 1d)
- `--retention <days>` - Keep backups for N days

**Examples:**
```bash
# Daily backups at 2 AM
ai-shell backup schedule --cron "0 2 * * *"

# Every 6 hours
ai-shell backup schedule --interval 6h

# With retention policy
ai-shell backup schedule --interval 12h --retention 30
```

**Output:**
```
⏰ Configuring backup schedule...

Schedule Configuration:
  Frequency: Every 12 hours
  Next Backup: 2024-01-15 22:00:00
  Retention: 30 days
  Auto-cleanup: Enabled

✓ Backup schedule configured

Upcoming backups:
  • 2024-01-15 22:00:00
  • 2024-01-16 10:00:00
  • 2024-01-16 22:00:00
```

**Related Commands:**
- `backup` - Manual backup
- `backup config` - View configuration

---

#### ai-shell backup verify

**Description:** Verify backup integrity

**Syntax:**
```bash
ai-shell backup verify <backup-id>
```

**Examples:**
```bash
# Verify backup
ai-shell backup verify backup-20240115-100000-abc123
```

**Output:**
```
🔍 Verifying backup integrity...

Backup: backup-20240115-100000-abc123

Checks:
  ✓ File exists and is readable
  ✓ Checksum matches (SHA-256)
  ✓ Archive structure valid
  ✓ Schema integrity verified
  ✓ Data consistency verified
  ✓ All tables present (25/25)
  ✓ Record counts match
  ✓ No corruption detected

Verification Result: ✓ VALID

Backup is safe to restore.
  Size: 1.2 GB
  Tables: 25
  Records: 12,456,789
  Created: 2024-01-15 10:00:00
```

**Related Commands:**
- `restore` - Restore backup
- `backup-list` - List backups

---

#### ai-shell backup delete

**Description:** Delete a backup

**Syntax:**
```bash
ai-shell backup delete <backup-id> [options]
```

**Options:**
- `--force` - Skip confirmation

**Examples:**
```bash
# Delete backup
ai-shell backup delete backup-20240101-100000-old123

# Force delete
ai-shell backup delete backup-old --force
```

**Output:**
```
⚠️  Are you sure you want to delete this backup?

  Backup ID: backup-20240101-100000-old123
  Database: production
  Size: 1.2 GB
  Created: 15 days ago

  This action cannot be undone!

Confirm deletion? (yes/no): yes

✓ Backup deleted successfully
  Freed space: 1.2 GB
```

**Related Commands:**
- `backup-list` - List backups
- `backup verify` - Verify before deleting

---

#### ai-shell backup export

**Description:** Export backup to external location

**Syntax:**
```bash
ai-shell backup export <backup-id> <destination> [options]
```

**Options:**
- `--format <type>` - Export format (tar.gz, sql, custom)

**Examples:**
```bash
# Export to S3
ai-shell backup export backup-abc123 s3://my-bucket/backups/

# Export to local path
ai-shell backup export backup-abc123 /mnt/external/backups/

# Custom format
ai-shell backup export backup-abc123 ./export/ --format sql
```

**Output:**
```
📤 Exporting backup...

Source: backup-20240115-100000-abc123
Destination: s3://my-bucket/backups/
Format: tar.gz

Uploading... ████████░░ 78% (945 MB / 1.2 GB)

✓ Export completed successfully!
  Uploaded: 1.2 GB
  Duration: 2m 34s
  Location: s3://my-bucket/backups/backup-20240115-100000-abc123.tar.gz
```

**Related Commands:**
- `backup import` - Import backup
- `backup-list` - List backups

---

#### ai-shell backup import

**Description:** Import backup from external location

**Syntax:**
```bash
ai-shell backup import <source>
```

**Examples:**
```bash
# Import from S3
ai-shell backup import s3://my-bucket/backups/backup-abc123.tar.gz

# Import from local path
ai-shell backup import /mnt/external/backups/backup-abc123.tar.gz
```

**Output:**
```
📥 Importing backup...

Source: s3://my-bucket/backups/backup-abc123.tar.gz
Size: 1.2 GB

Downloading... ████████░░ 78%

✓ Import completed successfully!
  Backup ID: backup-20240115-imported-def456
  Size: 1.2 GB
  Duration: 1m 45s
```

**Related Commands:**
- `backup export` - Export backup
- `restore` - Restore imported backup

---

#### ai-shell backup config

**Description:** Show or edit backup configuration

**Syntax:**
```bash
ai-shell backup config [options]
```

**Options:**
- `--edit` - Edit configuration
- `--reset` - Reset to defaults

**Examples:**
```bash
# Show configuration
ai-shell backup config

# Edit configuration
ai-shell backup config --edit

# Reset to defaults
ai-shell backup config --reset
```

**Output:**
```
⚙️  Backup Configuration

Schedule:
  Enabled: Yes
  Frequency: Every 12 hours
  Next Backup: 2024-01-15 22:00:00

Retention:
  Keep backups for: 30 days
  Auto-cleanup: Enabled
  Min backups to keep: 7

Storage:
  Location: ./backups
  Max size: 50 GB (23 GB used)
  Compression: Enabled (gzip, level 6)

Notifications:
  On success: Email to admin@example.com
  On failure: Email + Slack

Cloud Backup:
  Enabled: Yes
  Provider: AWS S3
  Bucket: my-backup-bucket
  Region: us-east-1
```

**Related Commands:**
- `backup schedule` - Configure schedule
- `backup` - Create backup

---

#### ai-shell backup status

**Description:** Show detailed backup status and information

**Syntax:**
```bash
ai-shell backup status [backup-id]
```

**Examples:**
```bash
# Show overall backup status
ai-shell backup status

# Show specific backup details
ai-shell backup status backup-20240115-100000-abc123
```

**Output:**
```
📊 Backup Status Overview

Last Backup:
  ID: backup-20240115-100000-abc123
  Status: ✓ Completed
  Created: 2 hours ago
  Duration: 3m 24s
  Size: 1.2 GB (compressed)
  Database: production

Schedule Status:
  Next backup: 6 hours from now
  Auto-backup: Enabled
  Last 7 backups: ✓✓✓✓✓✓✓

Storage:
  Total backups: 23
  Total size: 15.3 GB
  Available space: 34.7 GB
  Oldest backup: 30 days ago

Health:
  All backups verified: Yes
  Failed backups: 0
  Warnings: 1 (disk space <40%)

Recommendations:
  • Consider cleaning up old backups
  • Increase backup retention or free disk space
```

**Related Commands:**
- `backup-list` - List all backups
- `backup verify` - Verify backup

---

### Security Commands

#### ai-shell vault-add

**Description:** Add credential to secure vault

**Syntax:**
```bash
ai-shell vault-add <name> <value> [options]
```

**Options:**
- `--encrypt` - Encrypt the value (default: true)

**Examples:**
```bash
# Add database password
ai-shell vault-add db_password "super_secret_123"

# Add API key
ai-shell vault-add api_key "sk-abc123xyz789" --encrypt
```

**Output:**
```
🔐 Adding credential to vault...

Name: db_password
Type: Encrypted
Encryption: AES-256

✓ Credential stored securely
  Key: db_password
  Status: Encrypted
  Access: Restricted to authorized users
```

**Related Commands:**
- `vault-list` - List vault entries
- `vault-get` - Retrieve credential
- `vault-delete` - Remove credential

---

#### ai-shell vault-list

**Description:** List all vault entries

**Syntax:**
```bash
ai-shell vault-list [options]
```

**Options:**
- `--show-passwords` - Show actual passwords (not recommended)
- `--format <type>` - Output format (json, table)

**Examples:**
```bash
# List all entries (masked)
ai-shell vault-list

# Show passwords
ai-shell vault-list --show-passwords

# JSON format
ai-shell vault-list --format json
```

**Output:**
```
🔐 Vault Entries (5 total)

┌────────────────┬───────────────┬──────────────┬──────────────────┐
│ Name           │ Value         │ Type         │ Last Updated     │
├────────────────┼───────────────┼──────────────┼──────────────────┤
│ db_password    │ ************  │ Encrypted    │ 2 hours ago      │
│ api_key        │ sk-******    │ Encrypted    │ 3 days ago       │
│ smtp_password  │ ************  │ Encrypted    │ 1 week ago       │
│ aws_secret     │ ************  │ Encrypted    │ 2 weeks ago      │
│ jwt_secret     │ ************  │ Encrypted    │ 1 month ago      │
└────────────────┴───────────────┴──────────────┴──────────────────┘
```

**Related Commands:**
- `vault-add` - Add credential
- `vault-get` - Get specific entry
- `vault-delete` - Remove entry

---

#### ai-shell vault-get

**Description:** Get specific vault entry

**Syntax:**
```bash
ai-shell vault-get <name>
```

**Examples:**
```bash
# Get credential
ai-shell vault-get db_password
```

**Output:**
```
🔐 Vault Entry: db_password

Name: db_password
Value: super_secret_123
Type: Encrypted
Encryption: AES-256
Created: 2024-01-10 08:30:00
Last Updated: 2024-01-15 10:00:00
Last Accessed: 2024-01-15 10:15:00
Access Count: 45

⚠️  This credential was copied to clipboard
   It will be cleared in 30 seconds
```

**Related Commands:**
- `vault-list` - List all entries
- `vault-add` - Add credential

---

#### ai-shell vault-delete

**Description:** Delete vault entry

**Syntax:**
```bash
ai-shell vault-delete <name>
```

**Examples:**
```bash
# Delete credential
ai-shell vault-delete old_api_key
```

**Output:**
```
⚠️  Are you sure you want to delete credential 'old_api_key'?
   This action cannot be undone!

Confirm deletion? (yes/no): yes

✓ Credential deleted successfully
  Name: old_api_key
```

**Related Commands:**
- `vault-list` - List entries
- `vault-add` - Add credential

---

#### ai-shell permissions-grant

**Description:** Grant permission to role for a resource

**Syntax:**
```bash
ai-shell permissions-grant <role> <resource> [options]
```

**Options:**
- `--actions <actions>` - Comma-separated actions (read,write,delete)

**Examples:**
```bash
# Grant read/write
ai-shell permissions-grant developer database --actions read,write

# Grant all permissions
ai-shell permissions-grant admin database --actions read,write,delete,manage
```

**Output:**
```
🔑 Granting permissions...

Role: developer
Resource: database
Actions: read, write

✓ Permissions granted successfully

  developer can now:
    • Read from database
    • Write to database
```

**Related Commands:**
- `permissions-revoke` - Revoke permissions
- `audit-log` - View permission changes

---

#### ai-shell permissions-revoke

**Description:** Revoke permission from role for a resource

**Syntax:**
```bash
ai-shell permissions-revoke <role> <resource>
```

**Examples:**
```bash
# Revoke permissions
ai-shell permissions-revoke developer production-db
```

**Output:**
```
⚠️  Revoking permissions...

Role: developer
Resource: production-db

✓ Permissions revoked

  developer can no longer:
    • Read from production-db
    • Write to production-db
```

**Related Commands:**
- `permissions-grant` - Grant permissions
- `audit-log` - View changes

---

#### ai-shell audit-log

**Description:** Show audit log entries

**Syntax:**
```bash
ai-shell audit-log [options]
```

**Options:**
- `--limit <n>` - Limit entries (default: 100)
- `--user <user>` - Filter by user
- `--action <action>` - Filter by action
- `--resource <resource>` - Filter by resource
- `--format <type>` - Output format (json, csv, table)

**Examples:**
```bash
# Show recent entries
ai-shell audit-log

# Filter by user
ai-shell audit-log --user admin --limit 50

# Filter by action
ai-shell audit-log --action delete

# Export as CSV
ai-shell audit-log --format csv --limit 1000 > audit.csv
```

**Output:**
```
📋 Audit Log (Last 100 entries)

┌──────────────────────┬──────────┬─────────┬─────────────┬────────────┐
│ Timestamp            │ User     │ Action  │ Resource    │ Result     │
├──────────────────────┼──────────┼─────────┼─────────────┼────────────┤
│ 2024-01-15 10:15:23  │ admin    │ GRANT   │ production  │ SUCCESS    │
│ 2024-01-15 10:12:45  │ developer│ READ    │ users       │ SUCCESS    │
│ 2024-01-15 10:10:12  │ admin    │ DELETE  │ backup-old  │ SUCCESS    │
│ 2024-01-15 10:05:34  │ system   │ BACKUP  │ production  │ SUCCESS    │
│ 2024-01-15 09:58:21  │ developer│ WRITE   │ products    │ FAILED     │
│ 2024-01-15 09:45:10  │ admin    │ REVOKE  │ staging     │ SUCCESS    │
└──────────────────────┴──────────┴─────────┴─────────────┴────────────┘

Summary:
  Total entries: 100
  Time range: Last 24 hours
  Users: 4 unique
  Failed actions: 2 (2%)
```

**Related Commands:**
- `permissions-grant` - Grant permissions
- `permissions-revoke` - Revoke permissions
- `security-scan` - Security scan

---

#### ai-shell security-scan

**Description:** Run security scan

**Syntax:**
```bash
ai-shell security-scan [options]
```

**Options:**
- `--deep` - Deep scan (slower but more thorough)

**Examples:**
```bash
# Quick scan
ai-shell security-scan

# Deep scan
ai-shell security-scan --deep
```

**Output:**
```
🔒 Security Scan Report

Scanning... ████████████ 100%

Vulnerabilities Found: 3

🔴 CRITICAL (1)
  • Weak password detected for user 'admin'
    Risk: Account compromise
    Fix: Update password to meet complexity requirements

🟠 HIGH (1)
  • Unencrypted connection detected
    Risk: Data exposure in transit
    Fix: Enable SSL/TLS encryption

🟡 MEDIUM (1)
  • Outdated database version
    Risk: Known vulnerabilities
    Fix: Upgrade to latest version

Security Score: 72/100 (Needs Improvement)

Recommendations:
  1. Update admin password immediately
  2. Enable SSL/TLS for all connections
  3. Schedule database upgrade
  4. Review and update access controls
  5. Enable audit logging
```

**Related Commands:**
- `audit-log` - View audit trail
- `permissions-grant` - Manage permissions

---

### Monitoring Commands

#### ai-shell alerts setup

**Description:** Configure health monitoring alerts

**Syntax:**
```bash
ai-shell alerts setup [options]
```

**Options:**
- `-s, --slack <webhook>` - Slack webhook URL
- `-e, --email <addresses>` - Email addresses (comma-separated)
- `-w, --webhook <url>` - Custom webhook URL

**Examples:**
```bash
# Setup Slack alerts
ai-shell alerts setup --slack https://hooks.slack.com/services/xxx

# Setup email alerts
ai-shell alerts setup --email admin@company.com,ops@company.com

# Multiple channels
ai-shell alerts setup --slack https://... --email admin@company.com
```

**Output:**
```
🔔 Configuring alerts...

Alert Channels:
  ✓ Slack: #database-alerts
  ✓ Email: admin@company.com, ops@company.com

Alert Triggers:
  • High CPU usage (>80%)
  • Low disk space (<20%)
  • Slow queries (>5s)
  • Connection pool exhaustion
  • Backup failures
  • Replication lag (>1s)

✓ Alerts configured successfully

Test notification sent to all channels.
```

**Related Commands:**
- `alerts list` - List active alerts
- `alerts test` - Test alert notification
- `monitor` - Start monitoring

---

#### ai-shell alerts list

**Description:** List active alerts

**Syntax:**
```bash
ai-shell alerts list
```

**Examples:**
```bash
# List active alerts
ai-shell alerts list
```

**Output:**
```
🔔 Active Alerts (3)

🔴 CRITICAL
  High CPU Usage
  Current: 92%
  Threshold: 80%
  Duration: 15 minutes
  First seen: 10:00 AM
  Actions: Auto-scaling triggered

🟠 WARNING
  Low Disk Space
  Current: 18% free
  Threshold: 20%
  Duration: 2 hours
  First seen: 8:00 AM
  Actions: Cleanup job queued

🟡 INFO
  Replication Lag
  Current: 1.2s
  Threshold: 1.0s
  Duration: 5 minutes
  First seen: 10:10 AM
  Actions: Monitoring

Notification Channels:
  ✓ Slack: 3 alerts sent
  ✓ Email: 2 alerts sent
```

**Related Commands:**
- `alerts setup` - Configure alerts
- `health-check` - Check health
- `monitor` - Real-time monitoring

---

#### ai-shell alerts test

**Description:** Test alert notification

**Syntax:**
```bash
ai-shell alerts test [channel]
```

**Examples:**
```bash
# Test all channels
ai-shell alerts test

# Test specific channel
ai-shell alerts test slack
```

**Output:**
```
🔔 Testing alert notifications...

Testing Slack...
  ✓ Message sent to #database-alerts
  ✓ Webhook responded in 234ms

Testing Email...
  ✓ Email sent to admin@company.com
  ✓ Email sent to ops@company.com
  ✓ SMTP responded in 456ms

Testing Custom Webhook...
  ✓ Webhook called successfully
  ✓ Response: 200 OK

All channels working correctly!
```

**Related Commands:**
- `alerts setup` - Configure alerts
- `alerts list` - List alerts

---

#### ai-shell grafana setup

**Description:** Configure Grafana connection

**Syntax:**
```bash
ai-shell grafana setup [options]
```

**Options:**
- `--url <url>` - Grafana URL
- `--api-key <key>` - API key
- `--org-id <id>` - Organization ID

**Examples:**
```bash
# Interactive setup
ai-shell grafana setup

# Non-interactive
ai-shell grafana setup --url https://grafana.company.com --api-key xxx
```

**Output:**
```
📊 Grafana Integration Setup

Grafana URL: https://grafana.company.com
API Key: ****************************
Organization: my-org (ID: 1)

Testing connection... ✓

✓ Grafana connection configured

Available dashboards:
  • Database Overview
  • Query Performance
  • System Metrics
  • Connection Pool
  • Backup Status

Next steps:
  1. Run 'ai-shell grafana deploy-dashboards' to deploy dashboards
  2. Visit https://grafana.company.com to view metrics
```

**Related Commands:**
- `grafana deploy-dashboards` - Deploy dashboards
- `prometheus` - Prometheus integration
- `metrics export` - Export metrics

---

#### ai-shell grafana deploy-dashboards

**Description:** Deploy all dashboards to Grafana

**Syntax:**
```bash
ai-shell grafana deploy-dashboards
```

**Examples:**
```bash
# Deploy dashboards
ai-shell grafana deploy-dashboards
```

**Output:**
```
📊 Deploying Grafana dashboards...

Deploying dashboards:
  ✓ Database Overview (ID: 1)
  ✓ Query Performance (ID: 2)
  ✓ System Metrics (ID: 3)
  ✓ Connection Pool (ID: 4)
  ✓ Backup Status (ID: 5)

✓ All dashboards deployed successfully!

View dashboards:
  • Database Overview: https://grafana.company.com/d/db-overview
  • Query Performance: https://grafana.company.com/d/query-perf
```

**Related Commands:**
- `grafana setup` - Configure Grafana
- `metrics export` - Export metrics

---

#### ai-shell prometheus

**Description:** Configure Prometheus integration

**Syntax:**
```bash
ai-shell prometheus [options]
```

**Options:**
- `--port <port>` - Metrics port (default: 9090)
- `--path <path>` - Metrics path (default: /metrics)

**Examples:**
```bash
# Start Prometheus exporter
ai-shell prometheus

# Custom port
ai-shell prometheus --port 8080

# Custom path
ai-shell prometheus --port 9090 --path /database-metrics
```

**Output:**
```
📊 Prometheus Metrics Exporter

Listening on: http://localhost:9090/metrics
Status: Running

Available metrics:
  • database_connections_total
  • database_queries_total
  • database_query_duration_seconds
  • database_slow_queries_total
  • database_cache_hit_ratio
  • database_disk_usage_bytes
  • database_cpu_usage_percent

Prometheus configuration:
  Add this to your prometheus.yml:

  scrape_configs:
    - job_name: 'ai-shell'
      static_configs:
        - targets: ['localhost:9090']

Press Ctrl+C to stop
```

**Related Commands:**
- `metrics show` - View current metrics
- `metrics export` - Export metrics
- `grafana setup` - Grafana integration

---

<a name="database-specific-section"></a>
## Database-Specific Commands

### MySQL Commands

#### ai-shell mysql connect

**Description:** Connect to MySQL database

**Syntax:**
```bash
ai-shell mysql connect <connection-string> [options]
```

**Options:**
- `--name <name>` - Connection name

**Examples:**
```bash
# Connect to MySQL
ai-shell mysql connect mysql://root:password@localhost:3306/mydb

# With name
ai-shell mysql connect mysql://localhost/db --name production
```

**Output:**
```
🐬 Connecting to MySQL...

✓ Connected to MySQL 8.0.35
  Database: mydb
  Host: localhost:3306
  User: root
  Connection: production
```

**Related Commands:**
- `mysql disconnect` - Disconnect
- `mysql status` - Connection status

---

#### ai-shell mysql disconnect

**Description:** Disconnect from MySQL database

**Syntax:**
```bash
ai-shell mysql disconnect [name]
```

**Examples:**
```bash
# Disconnect active
ai-shell mysql disconnect

# Disconnect specific
ai-shell mysql disconnect production
```

**Related Commands:**
- `mysql connect` - Connect to MySQL

---

#### ai-shell mysql query

**Description:** Execute SQL query on MySQL

**Syntax:**
```bash
ai-shell mysql query <sql> [options]
```

**Options:**
- `--format <type>` - Output format (table, json, csv)

**Examples:**
```bash
# Execute query
ai-shell mysql query "SELECT * FROM users LIMIT 10"

# JSON output
ai-shell mysql query "SELECT id, name FROM products" --format json
```

**Output:**
```
🐬 Executing query...

Results (10 rows):
┌────┬────────────┬───────────────────────┬────────┐
│ id │ name       │ email                 │ active │
├────┼────────────┼───────────────────────┼────────┤
│ 1  │ John Doe   │ john@example.com      │ true   │
│ 2  │ Jane Smith │ jane@example.com      │ true   │
└────┴────────────┴───────────────────────┴────────┘

Query executed in 23ms
```

**Related Commands:**
- `mysql tables` - List tables
- `optimize` - Optimize query

---

#### ai-shell mysql status

**Description:** Show MySQL connection status and statistics

**Syntax:**
```bash
ai-shell mysql status
```

**Examples:**
```bash
# Show status
ai-shell mysql status
```

**Output:**
```
🐬 MySQL Connection Status

Connection:
  Status: Connected
  Database: mydb
  Host: localhost:3306
  User: root
  Uptime: 2 hours

Statistics:
  Queries executed: 1,234
  Slow queries: 3
  Errors: 0
  Cache hit rate: 94.5%

Version:
  MySQL: 8.0.35
  Protocol: 10
```

**Related Commands:**
- `mysql connect` - Connect
- `health-check` - Health check

---

#### ai-shell mysql tables

**Description:** List tables in MySQL database

**Syntax:**
```bash
ai-shell mysql tables [options]
```

**Options:**
- `--pattern <pattern>` - Filter tables by name pattern

**Examples:**
```bash
# List all tables
ai-shell mysql tables

# Filter tables
ai-shell mysql tables --pattern "user*"
```

**Output:**
```
🐬 Tables in database 'mydb'

┌───────────────┬────────┬─────────┬─────────────────────┐
│ Table         │ Rows   │ Size    │ Engine              │
├───────────────┼────────┼─────────┼─────────────────────┤
│ users         │ 10,234 │ 2.3 MB  │ InnoDB              │
│ products      │ 5,678  │ 8.7 MB  │ InnoDB              │
│ orders        │ 45,890 │ 45 MB   │ InnoDB              │
│ order_items   │ 123K   │ 234 MB  │ InnoDB              │
└───────────────┴────────┴─────────┴─────────────────────┘

Total: 4 tables, 281.0 MB
```

**Related Commands:**
- `mysql describe` - Table structure
- `schema export` - Export schema

---

#### ai-shell mysql describe

**Description:** Show table structure and indexes

**Syntax:**
```bash
ai-shell mysql describe <table>
```

**Examples:**
```bash
# Describe table
ai-shell mysql describe users
```

**Output:**
```
🐬 Table: users

Columns:
┌───────────────┬──────────────┬──────┬─────┬────────────────┐
│ Field         │ Type         │ Null │ Key │ Default        │
├───────────────┼──────────────┼──────┼─────┼────────────────┤
│ id            │ INT          │ NO   │ PRI │ NULL           │
│ name          │ VARCHAR(255) │ NO   │     │ NULL           │
│ email         │ VARCHAR(255) │ NO   │ UNI │ NULL           │
│ created_at    │ TIMESTAMP    │ NO   │     │ CURRENT_TIMESTAMP │
└───────────────┴──────────────┴──────┴─────┴────────────────┘

Indexes:
  • PRIMARY KEY (id)
  • UNIQUE KEY email (email)
  • KEY idx_created (created_at)

Statistics:
  Rows: 10,234
  Size: 2.3 MB
  Engine: InnoDB
```

**Related Commands:**
- `mysql tables` - List tables
- `indexes analyze` - Analyze indexes

---

#### ai-shell mysql import

**Description:** Import data from file (SQL, CSV, JSON)

**Syntax:**
```bash
ai-shell mysql import <file> [options]
```

**Options:**
- `--table <table>` - Target table
- `--format <type>` - File format (sql, csv, json)

**Examples:**
```bash
# Import SQL
ai-shell mysql import backup.sql

# Import CSV
ai-shell mysql import data.csv --table users --format csv

# Import JSON
ai-shell mysql import data.json --table products --format json
```

**Output:**
```
🐬 Importing data from: data.csv

Format: CSV
Target table: users
Records: 1,000

Progress: ████████████ 100%

✓ Import completed successfully
  Records imported: 1,000
  Duplicates skipped: 5
  Errors: 0
  Duration: 2.3s
```

**Related Commands:**
- `mysql export` - Export data
- `backup` - Full backup

---

#### ai-shell mysql export

**Description:** Export table data to file

**Syntax:**
```bash
ai-shell mysql export <table> <file> [options]
```

**Options:**
- `--format <type>` - Format (sql, csv, json)
- `--where <condition>` - Filter condition

**Examples:**
```bash
# Export as SQL
ai-shell mysql export users users.sql

# Export as CSV
ai-shell mysql export products products.csv --format csv

# Export filtered
ai-shell mysql export users active-users.csv --where "active = 1"
```

**Output:**
```
🐬 Exporting table: users

Format: CSV
Records: 10,234

Progress: ████████████ 100%

✓ Export completed successfully
  File: users.csv
  Records: 10,234
  Size: 1.2 MB
  Duration: 1.8s
```

**Related Commands:**
- `mysql import` - Import data
- `backup` - Full backup

---

### MongoDB Commands

#### ai-shell mongo connect

**Description:** Connect to MongoDB database

**Syntax:**
```bash
ai-shell mongo connect <connection-string> [options]
```

**Options:**
- `--name <name>` - Connection name

**Examples:**
```bash
# Connect to MongoDB
ai-shell mongo connect mongodb://localhost:27017/mydb

# With authentication
ai-shell mongo connect mongodb://user:pass@localhost:27017/mydb --name production
```

**Output:**
```
🍃 Connecting to MongoDB...

✓ Connected to MongoDB 6.0.5
  Database: mydb
  Host: localhost:27017
  Connection: production
```

**Related Commands:**
- `mongo disconnect` - Disconnect
- `mongo stats` - Connection statistics

---

#### ai-shell mongo disconnect

**Description:** Disconnect from MongoDB database

**Syntax:**
```bash
ai-shell mongo disconnect [name]
```

**Examples:**
```bash
# Disconnect active
ai-shell mongo disconnect

# Disconnect specific
ai-shell mongo disconnect production
```

**Related Commands:**
- `mongo connect` - Connect to MongoDB

---

#### ai-shell mongo query

**Description:** Query MongoDB collection

**Syntax:**
```bash
ai-shell mongo query <collection> <filter> [options]
```

**Options:**
- `--limit <n>` - Limit results
- `--sort <field>` - Sort by field
- `--format <type>` - Output format (json, table)

**Examples:**
```bash
# Find all
ai-shell mongo query users '{}'

# Filter query
ai-shell mongo query users '{"active": true}' --limit 10

# Sort results
ai-shell mongo query products '{}' --sort price --limit 5
```

**Output:**
```
🍃 Querying collection: users

Filter: {"active": true}
Limit: 10

Results (10 documents):
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "active": true
  },
  ...
]

Query executed in 12ms
```

**Related Commands:**
- `mongo aggregate` - Aggregation pipeline
- `mongo collections` - List collections

---

#### ai-shell mongo aggregate

**Description:** Execute aggregation pipeline

**Syntax:**
```bash
ai-shell mongo aggregate <collection> <pipeline>
```

**Examples:**
```bash
# Count by field
ai-shell mongo aggregate users '[{"$group": {"_id": "$country", "count": {"$sum": 1}}}]'

# Complex aggregation
ai-shell mongo aggregate orders '[{"$match": {"status": "completed"}}, {"$group": {"_id": "$user_id", "total": {"$sum": "$amount"}}}]'
```

**Output:**
```
🍃 Executing aggregation...

Collection: users
Pipeline: 2 stages

Results:
[
  {"_id": "USA", "count": 234},
  {"_id": "UK", "count": 123},
  {"_id": "CA", "count": 89}
]

Aggregation executed in 45ms
```

**Related Commands:**
- `mongo query` - Simple query
- `optimize` - Optimize query

---

#### ai-shell mongo collections

**Description:** List all collections in MongoDB database

**Syntax:**
```bash
ai-shell mongo collections
```

**Examples:**
```bash
# List collections
ai-shell mongo collections
```

**Output:**
```
🍃 Collections in database 'mydb'

┌─────────────────┬──────────────┬─────────────┬─────────────┐
│ Name            │ Documents    │ Indexes     │ Size        │
├─────────────────┼──────────────┼─────────────┼─────────────┤
│ users           │ 10,234       │ 3           │ 2.3 MB      │
│ products        │ 5,678        │ 2           │ 8.7 MB      │
│ orders          │ 45,890       │ 4           │ 45 MB       │
│ sessions        │ 123,456      │ 2           │ 12 MB       │
└─────────────────┴──────────────┴─────────────┴─────────────┘

Total: 4 collections, 68.0 MB
```

**Related Commands:**
- `mongo indexes` - List indexes
- `mongo query` - Query collection

---

#### ai-shell mongo indexes

**Description:** List indexes for a collection

**Syntax:**
```bash
ai-shell mongo indexes <collection>
```

**Examples:**
```bash
# List indexes
ai-shell mongo indexes users
```

**Output:**
```
🍃 Indexes for collection: users

┌───────────────────────┬──────────────┬────────┬──────────┐
│ Name                  │ Keys         │ Unique │ Size     │
├───────────────────────┼──────────────┼────────┼──────────┤
│ _id_                  │ {_id: 1}     │ Yes    │ 256 KB   │
│ email_1               │ {email: 1}   │ Yes    │ 128 KB   │
│ created_at_1          │ {created: 1} │ No     │ 64 KB    │
└───────────────────────┴──────────────┴────────┴──────────┘

Total: 3 indexes
```

**Related Commands:**
- `mongo collections` - List collections
- `indexes analyze` - Analyze indexes

---

#### ai-shell mongo import

**Description:** Import data into MongoDB collection

**Syntax:**
```bash
ai-shell mongo import <file> <collection> [options]
```

**Options:**
- `--format <type>` - Format (json, csv)
- `--drop` - Drop collection before import

**Examples:**
```bash
# Import JSON
ai-shell mongo import data.json users

# Import CSV
ai-shell mongo import data.csv products --format csv

# Drop and import
ai-shell mongo import backup.json users --drop
```

**Output:**
```
🍃 Importing data to collection: users

File: data.json
Format: JSON
Documents: 1,000

Progress: ████████████ 100%

✓ Import completed successfully
  Documents imported: 1,000
  Duplicates: 0
  Duration: 3.2s
```

**Related Commands:**
- `mongo export` - Export data
- `backup` - Full backup

---

#### ai-shell mongo export

**Description:** Export MongoDB collection data

**Syntax:**
```bash
ai-shell mongo export <collection> <file> [options]
```

**Options:**
- `--format <type>` - Format (json, csv)
- `--query <filter>` - Filter documents

**Examples:**
```bash
# Export collection
ai-shell mongo export users users.json

# Export filtered
ai-shell mongo export users active-users.json --query '{"active": true}'

# Export as CSV
ai-shell mongo export products products.csv --format csv
```

**Output:**
```
🍃 Exporting collection: users

Format: JSON
Documents: 10,234

Progress: ████████████ 100%

✓ Export completed successfully
  File: users.json
  Documents: 10,234
  Size: 2.3 MB
  Duration: 2.1s
```

**Related Commands:**
- `mongo import` - Import data
- `backup` - Full backup

---

### Redis Commands

#### ai-shell redis connect

**Description:** Connect to a Redis server

**Syntax:**
```bash
ai-shell redis connect <connection-string> [options]
```

**Options:**
- `--name <name>` - Connection name

**Examples:**
```bash
# Connect to Redis
ai-shell redis connect redis://localhost:6379

# With password
ai-shell redis connect redis://:password@localhost:6379 --name cache
```

**Output:**
```
🔴 Connecting to Redis...

✓ Connected to Redis 7.0.11
  Host: localhost:6379
  Database: 0
  Connection: cache
```

**Related Commands:**
- `redis disconnect` - Disconnect
- `redis info` - Server info

---

#### ai-shell redis disconnect

**Description:** Disconnect from Redis server

**Syntax:**
```bash
ai-shell redis disconnect [name]
```

**Examples:**
```bash
# Disconnect
ai-shell redis disconnect
```

**Related Commands:**
- `redis connect` - Connect to Redis

---

#### ai-shell redis get

**Description:** Get the value of a key

**Syntax:**
```bash
ai-shell redis get <key>
```

**Examples:**
```bash
# Get value
ai-shell redis get user:1234

# Get JSON
ai-shell redis get config:app
```

**Output:**
```
🔴 Key: user:1234

Type: string
Value: {"id": 1234, "name": "John Doe", "email": "john@example.com"}
Size: 68 bytes
TTL: 3600 seconds (1 hour)
```

**Related Commands:**
- `redis set` - Set value
- `redis keys` - Find keys

---

#### ai-shell redis set

**Description:** Set the string value of a key

**Syntax:**
```bash
ai-shell redis set <key> <value> [options]
```

**Options:**
- `--ex <seconds>` - Set expiry time in seconds
- `--px <milliseconds>` - Set expiry time in milliseconds

**Examples:**
```bash
# Set value
ai-shell redis set user:1234 '{"name": "John"}'

# Set with expiry (1 hour)
ai-shell redis set session:abc123 'data' --ex 3600

# Set with milliseconds expiry
ai-shell redis set temp:key 'value' --px 5000
```

**Output:**
```
🔴 Set key: user:1234

✓ Value set successfully
  Type: string
  Size: 18 bytes
  TTL: 3600 seconds
```

**Related Commands:**
- `redis get` - Get value
- `redis expire` - Set expiry

---

#### ai-shell redis keys

**Description:** Find all keys matching a pattern

**Syntax:**
```bash
ai-shell redis keys <pattern>
```

**Examples:**
```bash
# All keys
ai-shell redis keys '*'

# Pattern match
ai-shell redis keys 'user:*'

# Specific pattern
ai-shell redis keys 'session:*:active'
```

**Output:**
```
🔴 Keys matching pattern: user:*

Found 234 keys:
  user:1
  user:2
  user:3
  ...
  user:234

Total keys: 234
```

**Related Commands:**
- `redis get` - Get key value
- `redis del` - Delete keys

---

#### ai-shell redis info

**Description:** Get information and statistics about the Redis server

**Syntax:**
```bash
ai-shell redis info [section]
```

**Examples:**
```bash
# All info
ai-shell redis info

# Specific section
ai-shell redis info server
ai-shell redis info memory
ai-shell redis info stats
```

**Output:**
```
🔴 Redis Server Information

Server:
  Version: 7.0.11
  Mode: standalone
  OS: Linux 5.10.0
  Uptime: 30 days

Clients:
  Connected: 45
  Blocked: 0

Memory:
  Used: 2.3 GB
  Peak: 3.1 GB
  Fragmentation Ratio: 1.08

Stats:
  Total Connections: 12,456
  Commands Processed: 1,234,567
  Keys: 45,890
  Expires: 12,345

Keyspace:
  db0: keys=45890, expires=12345
```

**Related Commands:**
- `redis monitor` - Monitor commands
- `health-check` - Health check

---

#### ai-shell redis flush

**Description:** Flush (delete) all keys in database

**Syntax:**
```bash
ai-shell redis flush [options]
```

**Options:**
- `--db <number>` - Database number (default: current)
- `--async` - Asynchronous flush

**Examples:**
```bash
# Flush current database
ai-shell redis flush

# Flush specific database
ai-shell redis flush --db 1

# Async flush
ai-shell redis flush --async
```

**Output:**
```
⚠️  WARNING: This will delete ALL keys in database 0!
   Total keys: 45,890

   This action cannot be undone!

Confirm flush? Type 'yes' to continue: yes

🔴 Flushing database...

✓ Database flushed successfully
  Keys deleted: 45,890
  Duration: 234ms
```

**Related Commands:**
- `redis keys` - List keys
- `redis del` - Delete specific keys

---

#### ai-shell redis monitor

**Description:** Monitor Redis commands in real-time

**Syntax:**
```bash
ai-shell redis monitor
```

**Examples:**
```bash
# Start monitoring
ai-shell redis monitor
```

**Output:**
```
🔴 Monitoring Redis commands... (Press Ctrl+C to stop)

[10:15:23] GET user:1234
[10:15:23] SET session:abc123 "data" EX 3600
[10:15:24] DEL temp:old_key
[10:15:24] HGETALL product:5678
[10:15:25] ZADD leaderboard 100 "player1"
[10:15:25] EXPIRE cache:page:home 600
...

Commands/sec: 234
```

**Related Commands:**
- `redis info` - Server info
- `monitor` - Database monitoring

---

#### ai-shell redis ttl

**Description:** Get the time to live for a key

**Syntax:**
```bash
ai-shell redis ttl <key>
```

**Examples:**
```bash
# Check TTL
ai-shell redis ttl session:abc123
```

**Output:**
```
🔴 Key: session:abc123

TTL: 2847 seconds (47 minutes, 27 seconds)
Expires at: 2024-01-15 11:02:47
```

**Related Commands:**
- `redis expire` - Set TTL
- `redis get` - Get value

---

#### ai-shell redis expire

**Description:** Set a timeout on a key

**Syntax:**
```bash
ai-shell redis expire <key> <seconds>
```

**Examples:**
```bash
# Set expiry (1 hour)
ai-shell redis expire user:1234 3600

# Set expiry (1 day)
ai-shell redis expire cache:data 86400
```

**Output:**
```
🔴 Key: user:1234

✓ Expiry set successfully
  TTL: 3600 seconds (1 hour)
  Expires at: 2024-01-15 11:15:34
```

**Related Commands:**
- `redis ttl` - Check TTL
- `redis set` - Set with expiry

---

#### ai-shell redis del

**Description:** Delete one or more keys

**Syntax:**
```bash
ai-shell redis del <key...>
```

**Examples:**
```bash
# Delete single key
ai-shell redis del user:1234

# Delete multiple keys
ai-shell redis del session:abc session:def session:ghi
```

**Output:**
```
🔴 Deleting keys...

✓ Keys deleted: 3
  • session:abc
  • session:def
  • session:ghi
```

**Related Commands:**
- `redis get` - Get key
- `redis keys` - Find keys

---

#### ai-shell redis type

**Description:** Determine the type of a key

**Syntax:**
```bash
ai-shell redis type <key>
```

**Examples:**
```bash
# Check type
ai-shell redis type user:1234
```

**Output:**
```
🔴 Key: user:1234

Type: string
Encoding: embstr
Size: 68 bytes
TTL: 3600 seconds
```

**Related Commands:**
- `redis get` - Get value
- `redis info` - Server info

---

### Integration Commands

#### ai-shell slack setup

**Description:** Setup Slack integration

**Syntax:**
```bash
ai-shell slack setup [options]
```

**Options:**
- `--webhook <url>` - Slack webhook URL
- `--channel <channel>` - Default channel

**Examples:**
```bash
# Interactive setup
ai-shell slack setup

# Direct setup
ai-shell slack setup --webhook https://hooks.slack.com/xxx --channel #database
```

**Output:**
```
📱 Slack Integration Setup

Webhook URL: https://hooks.slack.com/services/xxx
Channel: #database-alerts

Testing connection... ✓

✓ Slack integration configured

Test notification sent to #database-alerts
```

**Related Commands:**
- `slack notify` - Send notification
- `slack alert` - Send alert

---

#### ai-shell slack notify

**Description:** Send notification to Slack channel

**Syntax:**
```bash
ai-shell slack notify <message> [options]
```

**Options:**
- `--channel <channel>` - Target channel

**Examples:**
```bash
# Send message
ai-shell slack notify "Backup completed successfully"

# To specific channel
ai-shell slack notify "Migration finished" --channel #devops
```

**Output:**
```
📱 Sending Slack notification...

Channel: #database-alerts
Message: Backup completed successfully

✓ Notification sent successfully
```

**Related Commands:**
- `slack setup` - Configure Slack
- `slack alert` - Send alert

---

#### ai-shell email setup

**Description:** Setup email integration

**Syntax:**
```bash
ai-shell email setup [options]
```

**Options:**
- `--smtp-host <host>` - SMTP server host
- `--smtp-port <port>` - SMTP server port
- `--from <email>` - From email address
- `--to <emails>` - To email addresses (comma-separated)

**Examples:**
```bash
# Interactive setup
ai-shell email setup

# Direct setup
ai-shell email setup --smtp-host smtp.gmail.com --smtp-port 587 --from db@company.com
```

**Output:**
```
📧 Email Integration Setup

SMTP Server: smtp.gmail.com:587
From: database@company.com
To: admin@company.com, ops@company.com

Testing connection... ✓
Sending test email... ✓

✓ Email integration configured

Test email sent to configured recipients
```

**Related Commands:**
- `email send` - Send email
- `email alert` - Send alert

---

#### ai-shell federation add

**Description:** Add database to federation

**Syntax:**
```bash
ai-shell federation add <name> <connection-string>
```

**Examples:**
```bash
# Add database to federation
ai-shell federation add db1 postgresql://localhost/db1
ai-shell federation add db2 mysql://localhost/db2
```

**Output:**
```
🔗 Adding database to federation...

Name: db1
Type: PostgreSQL
Host: localhost
Database: db1

✓ Database added to federation
  Federation size: 3 databases
```

**Related Commands:**
- `federation remove` - Remove database
- `federation query` - Federated query
- `federation status` - Show status

---

#### ai-shell federation query

**Description:** Execute federated query across multiple databases

**Syntax:**
```bash
ai-shell federation query <sql>
```

**Examples:**
```bash
# Query across databases
ai-shell federation query "SELECT * FROM db1.users UNION ALL SELECT * FROM db2.users"
```

**Output:**
```
🔗 Executing federated query...

Databases: db1, db2
Query: SELECT * FROM db1.users UNION ALL SELECT * FROM db2.users

Results (150 rows):
┌────┬──────────────┬─────────────────┐
│ id │ name         │ database        │
├────┼──────────────┼─────────────────┤
│ 1  │ John (db1)   │ db1             │
│ 2  │ Jane (db1)   │ db1             │
│ 1  │ Alice (db2)  │ db2             │
│ 2  │ Bob (db2)    │ db2             │
└────┴──────────────┴─────────────────┘

Query executed in 345ms
```

**Related Commands:**
- `federation add` - Add database
- `federation status` - Show status

---

### Context Management

#### ai-shell context save

**Description:** Save current context

**Syntax:**
```bash
ai-shell context save <name> [options]
```

**Options:**
- `-d, --description <text>` - Context description
- `--include-history` - Include query history
- `--include-aliases` - Include aliases
- `--include-config` - Include configuration
- `--include-variables` - Include variables
- `--include-connections` - Include connection info

**Examples:**
```bash
# Save context
ai-shell context save my-project --description "Production context"

# Save with history
ai-shell context save dev-env --include-history --include-config
```

**Output:**
```
💾 Saving context: my-project

Included:
  • Database connection: production
  • Configuration: 12 settings
  • Query history: 50 queries
  • Aliases: 8 aliases
  • Variables: 5 variables

✅ Context "my-project" saved successfully
  Size: 45 KB
  Location: .ai-shell/contexts/my-project.json
```

**Related Commands:**
- `context load` - Load context
- `context list` - List contexts

---

#### ai-shell context load

**Description:** Load saved context

**Syntax:**
```bash
ai-shell context load <name> [options]
```

**Options:**
- `--merge` - Merge with current context
- `--overwrite` - Overwrite current context (default)

**Examples:**
```bash
# Load context
ai-shell context load my-project

# Merge with current
ai-shell context load dev-env --merge
```

**Output:**
```
📂 Loading context: my-project

Restoring:
  • Database connection: production
  • Configuration: 12 settings
  • Query history: 50 queries
  • Aliases: 8 aliases
  • Variables: 5 variables

✅ Context "my-project" loaded successfully
```

**Related Commands:**
- `context save` - Save context
- `context show` - Show context details

---

#### ai-shell context list

**Description:** List all saved contexts

**Syntax:**
```bash
ai-shell context list [options]
```

**Options:**
- `-v, --verbose` - Show detailed information
- `-f, --format <type>` - Output format (table, json)

**Examples:**
```bash
# List contexts
ai-shell context list

# Verbose output
ai-shell context list --verbose

# JSON format
ai-shell context list --format json
```

**Output:**
```
📋 Saved Contexts

my-project
  Production context
  Created: 2024-01-10 10:00:00
  Updated: 2024-01-15 09:30:00

dev-env
  Development environment
  Created: 2024-01-12 14:20:00
  Updated: 2024-01-15 08:15:00

staging
  Staging database context
  Created: 2024-01-14 11:45:00
  Updated: 2024-01-15 10:00:00

Total contexts: 3
```

**Related Commands:**
- `context save` - Save context
- `context load` - Load context
- `context delete` - Delete context

---

### Session Management

#### ai-shell session start

**Description:** Start a new session

**Syntax:**
```bash
ai-shell session start <name>
```

**Examples:**
```bash
# Start session
ai-shell session start debug-session

# Start analysis session
ai-shell session start production-analysis
```

**Output:**
```
🎯 Starting session: debug-session

✅ Session "debug-session" started
  Session ID: session_1642245600_abc123
  Started: 2024-01-15 10:00:00

All queries and operations will be tracked in this session.
```

**Related Commands:**
- `session end` - End session
- `session list` - List sessions

---

#### ai-shell session end

**Description:** End current session

**Syntax:**
```bash
ai-shell session end
```

**Examples:**
```bash
# End session
ai-shell session end
```

**Output:**
```
🎯 Ending session...

Session Summary:
  Name: debug-session
  Duration: 2 hours, 34 minutes
  Queries executed: 45
  Success rate: 97.8%

✅ Session ended successfully
  Session saved to: .ai-shell/sessions/session_1642245600_abc123.json
```

**Related Commands:**
- `session start` - Start session
- `session list` - List sessions

---

### Utility Commands

#### ai-shell interactive

**Description:** Start interactive mode (REPL)

**Aliases:** `i`

**Syntax:**
```bash
ai-shell interactive
```

**Examples:**
```bash
# Start interactive mode
ai-shell interactive

# Using alias
ai-shell i
```

**Output:**
```
🤖 Starting AI-Shell Interactive Mode...

Welcome to AI-Shell v1.0.0
Type 'help' for available commands or 'exit' to quit

ai-shell> _
```

**Related Commands:**
- `features` - List features
- `examples` - Show examples

---

#### ai-shell features

**Description:** List all available features

**Syntax:**
```bash
ai-shell features
```

**Examples:**
```bash
# List features
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

**Related Commands:**
- `examples` - Usage examples
- `commands` - List commands

---

#### ai-shell examples

**Description:** Show usage examples

**Syntax:**
```bash
ai-shell examples
```

**Examples:**
```bash
# Show examples
ai-shell examples
```

**Output:**
```
📚 AI-Shell Examples

Query Optimization:
  ai-shell optimize "SELECT * FROM users WHERE active = true"
  ai-shell analyze-slow-queries --threshold 500

Health Monitoring:
  ai-shell health-check
  ai-shell monitor --interval 10000
  ai-shell alerts setup --slack https://hooks.slack.com/...

Backup & Recovery:
  ai-shell backup --connection production
  ai-shell restore backup-1234567890
  ai-shell backup-list

Advanced Features:
  ai-shell federate "SELECT * FROM users" --databases db1,db2
  ai-shell design-schema
  ai-shell cache enable --redis redis://localhost:6379

Analysis & Optimization:
  ai-shell explain "SELECT u.*, COUNT(o.id) FROM users u..."
  ai-shell translate "Show all users created last week"
  ai-shell diff production staging
  ai-shell analyze-costs aws us-east-1

Global Flags (use with any command):
  --format json       Output in JSON format
  --format csv        Output in CSV format
  --verbose          Enable verbose logging
  --explain          Show AI explanation before execution
  --dry-run          Simulate without making changes
  --output file.json Write output to file
  --limit 10         Limit results to 10 items
  --timestamps       Show timestamps in output
```

**Related Commands:**
- `features` - List features
- `commands` - List commands

---

#### ai-shell commands

**Description:** List all available commands

**Syntax:**
```bash
ai-shell commands [options]
```

**Options:**
- `-c, --category <category>` - Filter by category
- `-p, --phase <phase>` - Filter by phase (1, 2, or 3)
- `-s, --search <query>` - Search commands
- `--json` - Output as JSON
- `--count` - Show command count only

**Examples:**
```bash
# List all commands
ai-shell commands

# Filter by category
ai-shell commands --category "Query Optimization"

# Filter by phase
ai-shell commands --phase 2

# Search commands
ai-shell commands --search backup

# Show count
ai-shell commands --count
```

**Output:**
```
📋 Available Commands (106)

Query Optimization:
  optimize                       [Phase 1] Optimize a SQL query using AI analysis
    Aliases: opt
  analyze-slow-queries          [Phase 1] Analyze and optimize slow queries from log
    Aliases: slow
  translate                     [Phase 1] Translate natural language to SQL query

Health & Monitoring:
  health-check                  [Phase 1] Perform comprehensive database health check
    Aliases: health
  monitor                       [Phase 1] Start real-time database monitoring
  dashboard                     [Phase 1] Launch interactive performance dashboard

[... more categories ...]

Total Commands: 106
```

**Related Commands:**
- `features` - List features
- `examples` - Show examples

---

#### ai-shell version

**Description:** Show version and command summary

**Syntax:**
```bash
ai-shell version [options]
```

**Options:**
- `--verbose` - Show detailed information

**Examples:**
```bash
# Show version
ai-shell version

# Detailed info
ai-shell version --verbose
```

**Output:**
```
🤖 AI-Shell Database Management CLI

Version: 1.0.0
Total Commands: 106

Phase Breakdown:
  Phase 1 (Core Operations):      25 commands
  Phase 2 (Advanced Features):    68 commands
  Phase 3 (Analysis & Utilities): 13 commands

Category Breakdown:
  Query Optimization             13 commands
  Health & Monitoring            15 commands
  Backup & Recovery              10 commands
  Database Operations            32 commands
  Security & Permissions         7 commands
  Migration & Schema             8 commands
  Integration                    20 commands
  Connection Management          4 commands
  Context Management             6 commands
  Utilities                      3 commands
```

**Related Commands:**
- `commands` - List all commands
- `features` - List features

---

## Advanced Usage

### Chaining Commands

Commands can be chained using shell operators:

```bash
# Sequential execution
ai-shell backup && ai-shell optimize "SELECT * FROM users"

# Conditional execution
ai-shell health-check || ai-shell alerts setup

# Pipe to other tools
ai-shell metrics show --format json | jq '.cpu_usage'
```

### Scripting with AI-Shell

Create automated scripts:

```bash
#!/bin/bash
# daily-maintenance.sh

# Run health check
ai-shell health-check

# Analyze slow queries
ai-shell analyze-slow-queries --threshold 500

# Create backup
ai-shell backup --connection production

# Send notification
ai-shell slack notify "Daily maintenance completed"
```

### Configuration Files

Use configuration files for repeated operations:

```bash
# config.yaml
database:
  host: localhost
  port: 5432
  name: mydb

alerts:
  slack:
    webhook: https://hooks.slack.com/xxx
    channel: #database

backup:
  schedule: "0 2 * * *"
  retention: 30
```

```bash
# Use config file
ai-shell --config config.yaml backup
```

### Environment Variables

Configure defaults via environment variables:

```bash
# Set in .bashrc or .zshrc
export DATABASE_URL="postgresql://localhost/mydb"
export ANTHROPIC_API_KEY="sk-xxx"
export REDIS_URL="redis://localhost:6379"
export AI_SHELL_FORMAT="json"
```

### Global Flags

Apply to any command:

```bash
# JSON output
ai-shell optimize "SELECT * FROM users" --format json

# Verbose mode
ai-shell backup --verbose

# Dry run
ai-shell restore backup-123 --dry-run

# Output to file
ai-shell metrics show --output metrics.json

# With limit
ai-shell backup-list --limit 5

# With timestamps
ai-shell health-check --timestamps
```

### Plugins and Extensions

Extend AI-Shell functionality:

```bash
# Install plugin
ai-shell plugin install ai-shell-prometheus

# List plugins
ai-shell plugin list

# Enable plugin
ai-shell plugin enable ai-shell-prometheus
```

---

## Command Index

### By Category

**Connection Management (4)**
- `connect` - Connect to database
- `disconnect` - Disconnect from database
- `connections` - List connections
- `use` - Switch active connection

**Query Optimization (13)**
- `optimize` - Optimize SQL query
- `analyze-slow-queries` - Analyze slow queries
- `translate` - Natural language to SQL
- `explain` - Explain query execution
- `optimize-all` - Optimize all slow queries
- `slow-queries` - Advanced slow query analysis
- `indexes analyze` - Analyze indexes
- `indexes missing` - Detect missing indexes
- `indexes recommendations` - Index recommendations
- `indexes create` - Create index
- `indexes drop` - Drop index
- `indexes rebuild` - Rebuild indexes
- `indexes stats` - Index statistics

**Health & Monitoring (15)**
- `health-check` - Database health check
- `monitor` - Real-time monitoring
- `dashboard` - Interactive dashboard
- `alerts setup` - Configure alerts
- `alerts list` - List active alerts
- `alerts test` - Test alert notification
- `metrics show` - Show current metrics
- `metrics export` - Export metrics
- `performance analyze` - Analyze performance
- `performance report` - Generate report
- `grafana setup` - Configure Grafana
- `grafana deploy-dashboards` - Deploy dashboards
- `prometheus` - Prometheus integration
- `anomaly` - Detect anomalies
- `monitor start` - Start monitoring
- `monitor stop` - Stop monitoring

**Backup & Recovery (10)**
- `backup` - Create backup
- `restore` - Restore from backup
- `backup-list` - List backups
- `backup schedule` - Schedule backups
- `backup verify` - Verify backup integrity
- `backup delete` - Delete backup
- `backup export` - Export backup
- `backup import` - Import backup
- `backup config` - Backup configuration
- `backup status` - Backup status

**Security & Permissions (7)**
- `vault-add` - Add credential to vault
- `vault-list` - List vault entries
- `vault-get` - Get vault entry
- `vault-delete` - Delete vault entry
- `permissions-grant` - Grant permission
- `permissions-revoke` - Revoke permission
- `audit-log` - Show audit log
- `security-scan` - Run security scan

**Migration & Schema (8)**
- `migration create` - Create migration
- `migration up` - Run migrations
- `migration down` - Rollback migrations
- `migration status` - Migration status
- `schema diff` - Compare schemas
- `schema sync` - Synchronize schemas
- `schema export` - Export schema
- `schema import` - Import schema

**Database Operations (32)**
- MySQL (8): `mysql connect`, `mysql disconnect`, `mysql query`, `mysql status`, `mysql tables`, `mysql describe`, `mysql import`, `mysql export`
- MongoDB (10): `mongo connect`, `mongo disconnect`, `mongo query`, `mongo aggregate`, `mongo collections`, `mongo indexes`, `mongo import`, `mongo export`, `mongo connections`, `mongo stats`
- Redis (14): `redis connect`, `redis disconnect`, `redis get`, `redis set`, `redis keys`, `redis info`, `redis flush`, `redis monitor`, `redis ttl`, `redis expire`, `redis del`, `redis type`

**Integration (20)**
- `slack setup` - Setup Slack
- `slack notify` - Send Slack notification
- `slack alert` - Send Slack alert
- `slack report` - Send Slack report
- `email setup` - Setup email
- `email send` - Send email
- `email alert` - Send email alert
- `email report` - Send email report
- `federation add` - Add database to federation
- `federation remove` - Remove from federation
- `federation query` - Federated query
- `federation status` - Federation status
- `ada start` - Start autonomous agent
- `ada stop` - Stop autonomous agent
- `ada status` - Agent status
- `ada configure` - Configure agent

**Context Management (6)**
- `context save` - Save context
- `context load` - Load context
- `context list` - List contexts
- `context delete` - Delete context
- `context export` - Export context
- `context import` - Import context

**Session Management (4)**
- `session start` - Start session
- `session end` - End session
- `session list` - List sessions
- `session restore` - Restore session

**Utilities (3)**
- `interactive` - Interactive mode (REPL)
- `features` - List features
- `examples` - Show examples
- `commands` - List commands
- `version` - Show version

### Alphabetical Index

A - B
- `ada configure` - Configure autonomous agent
- `ada start` - Start autonomous agent
- `ada status` - Agent status
- `ada stop` - Stop autonomous agent
- `alerts list` - List active alerts
- `alerts setup` - Configure alerts
- `alerts test` - Test alert notification
- `analyze-slow-queries` - Analyze slow queries
- `anomaly` - Detect anomalies
- `audit-log` - Show audit log
- `backup` - Create backup
- `backup config` - Backup configuration
- `backup delete` - Delete backup
- `backup export` - Export backup
- `backup import` - Import backup
- `backup schedule` - Schedule backups
- `backup status` - Backup status
- `backup verify` - Verify backup integrity
- `backup-list` - List backups

C - D
- `commands` - List commands
- `connect` - Connect to database
- `connections` - List connections
- `context delete` - Delete context
- `context export` - Export context
- `context import` - Import context
- `context list` - List contexts
- `context load` - Load context
- `context save` - Save context
- `dashboard` - Interactive dashboard
- `design-schema` - Interactive schema designer
- `disconnect` - Disconnect from database

E - F
- `email alert` - Send email alert
- `email report` - Send email report
- `email send` - Send email
- `email setup` - Setup email
- `examples` - Show examples
- `explain` - Explain query execution
- `features` - List features
- `federation add` - Add database to federation
- `federation query` - Federated query
- `federation remove` - Remove from federation
- `federation status` - Federation status

G - I
- `grafana deploy-dashboards` - Deploy dashboards
- `grafana setup` - Configure Grafana
- `health-check` - Database health check
- `indexes analyze` - Analyze indexes
- `indexes create` - Create index
- `indexes drop` - Drop index
- `indexes missing` - Detect missing indexes
- `indexes rebuild` - Rebuild indexes
- `indexes recommendations` - Index recommendations
- `indexes stats` - Index statistics
- `interactive` - Interactive mode

M
- `metrics export` - Export metrics
- `metrics show` - Show current metrics
- `migration create` - Create migration
- `migration down` - Rollback migrations
- `migration status` - Migration status
- `migration up` - Run migrations
- `mongo aggregate` - Execute aggregation
- `mongo collections` - List collections
- `mongo connect` - Connect to MongoDB
- `mongo disconnect` - Disconnect from MongoDB
- `mongo export` - Export collection data
- `mongo import` - Import data
- `mongo indexes` - List indexes
- `mongo query` - Query collection
- `monitor` - Real-time monitoring
- `mysql connect` - Connect to MySQL
- `mysql describe` - Show table structure
- `mysql disconnect` - Disconnect from MySQL
- `mysql export` - Export table data
- `mysql import` - Import data
- `mysql query` - Execute SQL query
- `mysql status` - Connection status
- `mysql tables` - List tables

O - P
- `optimize` - Optimize SQL query
- `optimize-all` - Optimize all slow queries
- `performance analyze` - Analyze performance
- `performance report` - Generate report
- `permissions-grant` - Grant permission
- `permissions-revoke` - Revoke permission
- `prometheus` - Prometheus integration

R - S
- `redis connect` - Connect to Redis
- `redis del` - Delete keys
- `redis disconnect` - Disconnect from Redis
- `redis expire` - Set timeout on key
- `redis flush` - Flush database
- `redis get` - Get key value
- `redis info` - Server information
- `redis keys` - Find keys by pattern
- `redis monitor` - Monitor commands
- `redis set` - Set key value
- `redis ttl` - Get time to live
- `redis type` - Determine key type
- `restore` - Restore from backup
- `schema diff` - Compare schemas
- `schema export` - Export schema
- `schema import` - Import schema
- `schema sync` - Synchronize schemas
- `security-scan` - Run security scan
- `session end` - End session
- `session list` - List sessions
- `session restore` - Restore session
- `session start` - Start session
- `slack alert` - Send Slack alert
- `slack notify` - Send Slack notification
- `slack report` - Send Slack report
- `slack setup` - Setup Slack
- `slow-queries` - Advanced slow query analysis

T - V
- `translate` - Natural language to SQL
- `use` - Switch active connection
- `validate-schema` - Validate schema
- `vault-add` - Add credential to vault
- `vault-delete` - Delete vault entry
- `vault-get` - Get vault entry
- `vault-list` - List vault entries
- `version` - Show version

---

## Summary

This comprehensive command reference covers all **106+ CLI commands** in AI-Shell, organized by:

- **10 categories** covering all database operations
- **3 phases** of functionality (Core, Advanced, Analysis)
- **5 database types** (PostgreSQL, MySQL, MongoDB, Redis, SQLite)
- **Multiple integrations** (Slack, Email, Grafana, Prometheus)
- **Security features** (Vault, Permissions, Audit)
- **Advanced features** (Federation, Context, Sessions)

For more information:
- Run `ai-shell help <command>` for detailed command help
- Visit the documentation at [GitHub Repository]
- Report issues at [Issues Page]
- Join community at [Discord/Slack]

---

**Last Updated:** 2024-01-15
**Version:** 1.0.0
**Total Commands:** 106
