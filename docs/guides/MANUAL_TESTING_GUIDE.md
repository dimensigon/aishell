# AI-Shell Database Administration - Manual Testing & Tutorial Guide

## Table of Contents
1. [Quick Start (5 minutes)](#quick-start)
2. [Database Setup](#database-setup)
3. [Essential Commands by Category](#essential-commands)
4. [Hands-On Tutorials](#hands-on-tutorials)
5. [Command Reference](#command-reference)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## Quick Start (5 minutes) {#quick-start}

### Prerequisites Checklist

Before you begin, ensure you have:

- [ ] Node.js (v18 or higher) installed
- [ ] Docker installed and running
- [ ] AI-Shell installed: `npm install -g aishell`
- [ ] Basic understanding of SQL concepts
- [ ] Terminal/Command line access
- [ ] 2GB free disk space for Docker containers

### Verify Installation

```bash
# Check Node.js version
node --version

# Check Docker version
docker --version

# Check AI-Shell installation
ai-shell --version

# Verify AI-Shell is accessible
ai-shell --help
```

**Expected Output:**
```
AI-Shell version 1.0.0
AI-powered database management shell with performance monitoring
```

### Environment Configuration

Create a working directory for testing:

```bash
# Create test directory
mkdir -p ~/aishell-tests
cd ~/aishell-tests

# Create environment file
cat > .env << EOF
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=testdb
POSTGRES_USER=testuser
POSTGRES_PASSWORD=testpass123

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=testdb
MYSQL_USER=testuser
MYSQL_PASSWORD=testpass123

# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=testdb

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
EOF
```

> **⚠️ WARNING:** Never commit `.env` files to version control. Add to `.gitignore`.

### First Connection Test

We'll start with PostgreSQL as it's the most commonly used:

```bash
# Start PostgreSQL container
docker run -d \
  --name aishell-postgres \
  -e POSTGRES_DB=testdb \
  -e POSTGRES_USER=testuser \
  -e POSTGRES_PASSWORD=testpass123 \
  -p 5432:5432 \
  postgres:15-alpine

# Wait for PostgreSQL to start (about 10 seconds)
sleep 10

# Test connection
ai-shell connect postgresql://testuser:testpass123@localhost:5432/testdb

# Verify connection
ai-shell query "SELECT version();"
```

**Expected Output:**
```
✓ Connected to PostgreSQL: testdb
PostgreSQL 15.x on x86_64-pc-linux-gnu, compiled by gcc
```

> **✅ SUCCESS:** If you see the PostgreSQL version, your environment is ready!

---

## Database Setup {#database-setup}

### PostgreSQL Setup

#### 1. Start PostgreSQL Container

```bash
docker run -d \
  --name aishell-postgres \
  -e POSTGRES_DB=testdb \
  -e POSTGRES_USER=testuser \
  -e POSTGRES_PASSWORD=testpass123 \
  -p 5432:5432 \
  postgres:15-alpine
```

#### 2. Connection String

```bash
# Basic connection
ai-shell connect postgresql://testuser:testpass123@localhost:5432/testdb

# With connection name
ai-shell connect postgresql://testuser:testpass123@localhost:5432/testdb --name pg-test

# With SSL (for production)
ai-shell connect postgresql://testuser:testpass123@localhost:5432/testdb --ssl
```

#### 3. Initial Database Creation

```sql
-- Connect to default 'testdb'
ai-shell connect postgresql://testuser:testpass123@localhost:5432/testdb

-- Create sample schema
ai-shell query "
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER DEFAULT 0,
    category VARCHAR(50)
);
"
```

#### 4. Sample Data Insertion

```sql
-- Insert sample users
ai-shell query "
INSERT INTO users (username, email) VALUES
    ('alice', 'alice@example.com'),
    ('bob', 'bob@example.com'),
    ('charlie', 'charlie@example.com'),
    ('diana', 'diana@example.com'),
    ('evan', 'evan@example.com')
ON CONFLICT DO NOTHING;
"

-- Insert sample products
ai-shell query "
INSERT INTO products (name, price, stock, category) VALUES
    ('Laptop', 999.99, 50, 'Electronics'),
    ('Mouse', 29.99, 200, 'Electronics'),
    ('Keyboard', 79.99, 150, 'Electronics'),
    ('Monitor', 299.99, 75, 'Electronics'),
    ('Desk Chair', 249.99, 30, 'Furniture')
ON CONFLICT DO NOTHING;
"

-- Insert sample orders
ai-shell query "
INSERT INTO orders (user_id, total_amount, status) VALUES
    (1, 999.99, 'completed'),
    (2, 329.98, 'completed'),
    (3, 79.99, 'pending'),
    (1, 299.99, 'shipped'),
    (4, 249.99, 'pending')
ON CONFLICT DO NOTHING;
"
```

#### 5. Health Check Verification

```bash
# Check database health
ai-shell health

# Verify tables exist
ai-shell query "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';
"

# Check record counts
ai-shell query "
SELECT
    'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders;
"
```

**Expected Output:**
```
✓ Database Health: HEALTHY
  - Connection: Active
  - Tables: 3
  - Total Records: 15
  - Disk Space: 10MB / 100GB
```

---

### MySQL Setup

#### 1. Start MySQL Container

```bash
docker run -d \
  --name aishell-mysql \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=testdb \
  -e MYSQL_USER=testuser \
  -e MYSQL_PASSWORD=testpass123 \
  -p 3306:3306 \
  mysql:8.0
```

#### 2. Connection String

```bash
# Wait for MySQL to initialize (about 30 seconds)
sleep 30

# Connect to MySQL
ai-shell connect mysql://testuser:testpass123@localhost:3306/testdb

# Verify connection
ai-shell query "SELECT VERSION();"
```

#### 3. Initial Database Creation

```sql
-- Create tables (MySQL syntax)
ai-shell query "
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT true
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;
"
```

#### 4. Sample Data & Verification

```bash
# Insert data
ai-shell query "
INSERT IGNORE INTO users (username, email) VALUES
    ('alice', 'alice@example.com'),
    ('bob', 'bob@example.com');
"

# Health check
ai-shell health
```

---

### MongoDB Setup

#### 1. Start MongoDB Container

```bash
docker run -d \
  --name aishell-mongo \
  -p 27017:27017 \
  mongo:7.0
```

#### 2. Connection String

```bash
# Connect to MongoDB
ai-shell connect mongodb://localhost:27017/testdb

# Verify connection
ai-shell mongodb info
```

#### 3. Initial Collection Creation

```bash
# Create collections with sample documents
ai-shell mongodb insert users '{
  "username": "alice",
  "email": "alice@example.com",
  "created_at": {"$date": "2025-01-01T00:00:00Z"},
  "is_active": true
}'

ai-shell mongodb insert products '{
  "name": "Laptop",
  "price": 999.99,
  "stock": 50,
  "category": "Electronics"
}'
```

#### 4. Sample Data & Verification

```bash
# Insert multiple documents
ai-shell mongodb insert users '[
  {"username": "bob", "email": "bob@example.com"},
  {"username": "charlie", "email": "charlie@example.com"}
]'

# Verify data
ai-shell mongodb find users '{}'

# Count documents
ai-shell mongodb count users
```

---

### Redis Setup

#### 1. Start Redis Container

```bash
docker run -d \
  --name aishell-redis \
  -p 6379:6379 \
  redis:7-alpine
```

#### 2. Connection String

```bash
# Connect to Redis
ai-shell redis connect redis://localhost:6379

# Ping Redis
ai-shell redis ping
```

#### 3. Initial Data Insertion

```bash
# Set string values
ai-shell redis set "user:1001" "alice"
ai-shell redis set "session:abc123" '{"user_id": 1001, "expires": 3600}'

# Set with expiration
ai-shell redis setex "cache:homepage" 300 "Homepage HTML content"

# Hash operations
ai-shell redis hset "user:1001:profile" "name" "Alice"
ai-shell redis hset "user:1001:profile" "email" "alice@example.com"

# List operations
ai-shell redis lpush "notifications:1001" "New message"
ai-shell redis lpush "notifications:1001" "New follower"
```

#### 4. Health Check Verification

```bash
# Redis info
ai-shell redis info

# Check key count
ai-shell redis dbsize

# List keys
ai-shell redis keys "*"
```

---

## Essential Commands by Category {#essential-commands}

### A. Connection Management

#### Connect to Database

```bash
# PostgreSQL
ai-shell connect postgresql://user:pass@localhost:5432/dbname
ai-shell connect postgresql://user:pass@localhost:5432/dbname --name prod-db

# MySQL
ai-shell connect mysql://user:pass@localhost:3306/dbname

# MongoDB
ai-shell connect mongodb://localhost:27017/dbname

# Redis
ai-shell redis connect redis://localhost:6379
```

#### List Active Connections

```bash
# Show all connections
ai-shell connections list

# Show connection details
ai-shell connections show prod-db
```

**Expected Output:**
```
Active Connections:
┌──────────┬──────────────┬──────────┬────────────┬────────┐
│ Name     │ Type         │ Database │ Host       │ Status │
├──────────┼──────────────┼──────────┼────────────┼────────┤
│ prod-db  │ postgresql   │ testdb   │ localhost  │ Active │
│ default  │ mysql        │ testdb   │ localhost  │ Active │
└──────────┴──────────────┴──────────┴────────────┴────────┘
```

#### Disconnect from Database

```bash
# Disconnect specific connection
ai-shell disconnect prod-db

# Disconnect current connection
ai-shell disconnect

# Disconnect all
ai-shell disconnect --all
```

#### Test Connection Health

```bash
# Test current connection
ai-shell ping

# Detailed health check
ai-shell health

# Test specific connection
ai-shell ping --connection prod-db
```

**Expected Output:**
```
✓ Connection is healthy
  Response Time: 5ms
  Status: Connected
  Last Activity: 2s ago
```

#### Switch Between Databases

```bash
# Switch active connection
ai-shell use prod-db

# Verify current connection
ai-shell current
```

---

### B. Query Operations

#### Execute SELECT Queries

```bash
# Simple SELECT
ai-shell query "SELECT * FROM users;"

# SELECT with conditions
ai-shell query "SELECT * FROM users WHERE is_active = true;"

# SELECT with formatting
ai-shell query "SELECT * FROM users;" --format table

# Export to file
ai-shell query "SELECT * FROM users;" --output users.csv --format csv

# With pagination
ai-shell query "SELECT * FROM users LIMIT 10 OFFSET 0;"
```

#### Run INSERT Operations

```bash
# Single INSERT
ai-shell query "
INSERT INTO users (username, email)
VALUES ('newuser', 'newuser@example.com');
"

# Multiple INSERT
ai-shell query "
INSERT INTO users (username, email) VALUES
    ('user1', 'user1@example.com'),
    ('user2', 'user2@example.com'),
    ('user3', 'user3@example.com');
"

# INSERT with RETURNING (PostgreSQL)
ai-shell query "
INSERT INTO users (username, email)
VALUES ('testuser', 'test@example.com')
RETURNING id, username;
"
```

> **⚠️ WARNING:** Always verify INSERT statements before execution. Use transactions for critical data.

#### UPDATE Operations

```bash
# Simple UPDATE
ai-shell query "
UPDATE users
SET last_login = CURRENT_TIMESTAMP
WHERE username = 'alice';
"

# UPDATE with conditions (requires confirmation)
ai-shell query "
UPDATE users
SET is_active = false
WHERE last_login < NOW() - INTERVAL '30 days';
" --confirm

# Safe UPDATE with transaction
ai-shell query "
BEGIN;
UPDATE users SET email = 'newemail@example.com' WHERE id = 1;
SELECT * FROM users WHERE id = 1;
-- Review before committing
COMMIT;
"
```

> **⚠️ DANGER:** UPDATE without WHERE clause will modify all rows! Always use `--dry-run` first.

#### DELETE Operations

```bash
# DELETE with safety check
ai-shell query "DELETE FROM users WHERE id = 999;" --safe

# DELETE with confirmation
ai-shell query "DELETE FROM orders WHERE status = 'cancelled';" --confirm

# Soft delete (recommended)
ai-shell query "
UPDATE users
SET is_active = false, deleted_at = NOW()
WHERE id = 999;
"
```

> **🛡️ BEST PRACTICE:** Use soft deletes (is_deleted flag) instead of hard deletes.

#### JOIN Operations

```bash
# INNER JOIN
ai-shell query "
SELECT u.username, o.total_amount, o.order_date
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';
"

# LEFT JOIN
ai-shell query "
SELECT u.username, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username;
"

# Multiple JOINs
ai-shell query "
SELECT u.username, o.id as order_id, p.name as product_name
FROM users u
INNER JOIN orders o ON u.id = o.user_id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id;
"
```

#### Aggregate Functions

```bash
# COUNT
ai-shell query "SELECT COUNT(*) FROM users;"

# SUM
ai-shell query "SELECT SUM(total_amount) FROM orders WHERE status = 'completed';"

# AVG
ai-shell query "SELECT AVG(price) FROM products WHERE category = 'Electronics';"

# GROUP BY with aggregates
ai-shell query "
SELECT
    category,
    COUNT(*) as product_count,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM products
GROUP BY category;
"

# HAVING clause
ai-shell query "
SELECT user_id, COUNT(*) as order_count
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 2;
"
```

---

### C. Query Optimization

#### Analyze Query Performance

```bash
# Analyze a query
ai-shell analyze "
SELECT u.username, COUNT(o.id)
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id;
"

# Detailed analysis
ai-shell analyze "SELECT * FROM orders WHERE status = 'pending';" --detailed
```

**Expected Output:**
```
📊 Query Analysis:

Execution Plan:
  → Seq Scan on orders (cost=0..50 rows=10)
  Filter: (status = 'pending')

Estimated Cost: 50.00
Execution Time: 2.3ms

⚠️  Issues Detected:
  • Sequential scan on large table
  • Missing index on 'status' column

💡 Recommendations:
  • Add index on orders(status)
  • Consider partitioning if table > 1M rows
```

#### Generate EXPLAIN Plans

```bash
# Basic EXPLAIN
ai-shell explain "SELECT * FROM users WHERE email = 'alice@example.com';"

# EXPLAIN ANALYZE (actually executes)
ai-shell explain "SELECT * FROM users WHERE email = 'alice@example.com';" --analyze

# Visual EXPLAIN
ai-shell explain "
SELECT u.username, o.total_amount
FROM users u
JOIN orders o ON u.id = o.user_id;
" --visual
```

#### Identify Slow Queries

```bash
# List slow queries (>1000ms)
ai-shell slow-queries

# Custom threshold
ai-shell slow-queries --threshold 500

# Show top 20 slowest
ai-shell slow-queries --limit 20

# With date range
ai-shell slow-queries --last 7d

# Export to file
ai-shell slow-queries --export slow-queries.json
```

**Expected Output:**
```
🐌 Found 5 slow queries:

1. ⏱️  2,345ms (executed 150x)
   SELECT * FROM orders o
   JOIN order_items oi ON o.id = oi.order_id
   WHERE o.created_at > NOW() - INTERVAL '30 days';

   💡 Suggestions:
      • Add index on orders(created_at)
      • Add index on order_items(order_id)
      • Consider materialized view for this pattern

2. ⏱️  1,823ms (executed 89x)
   SELECT COUNT(*) FROM products WHERE stock < 10;

   💡 Suggestions:
      • Add partial index on products(stock) WHERE stock < 10
```

#### Suggest Indexes

```bash
# Get index recommendations
ai-shell indexes recommendations

# Auto-apply recommendations
ai-shell indexes recommendations --apply

# Analyze specific table
ai-shell indexes analyze --table users
```

#### Apply Optimizations

```bash
# Optimize specific query
ai-shell optimize "SELECT * FROM orders WHERE status = 'pending';"

# Auto-optimize all slow queries
ai-shell optimize-all --threshold 1000

# Enable auto-optimization
ai-shell auto-optimize enable --threshold 500
```

---

### D. Schema Management

#### List Tables/Collections

```bash
# PostgreSQL/MySQL - List tables
ai-shell tables list

# Show table sizes
ai-shell tables list --size

# Filter by schema
ai-shell tables list --schema public

# MongoDB - List collections
ai-shell mongodb collections
```

**Expected Output:**
```
📋 Tables in 'testdb':

┌──────────────┬──────────┬──────────┬────────────┐
│ Table Name   │ Rows     │ Size     │ Indexes    │
├──────────────┼──────────┼──────────┼────────────┤
│ users        │ 1,245    │ 128 KB   │ 3          │
│ orders       │ 8,932    │ 2.4 MB   │ 4          │
│ products     │ 456      │ 64 KB    │ 2          │
└──────────────┴──────────┴──────────┴────────────┘
```

#### Describe Table Structure

```bash
# Describe table
ai-shell describe users

# Show columns only
ai-shell describe users --columns

# Show indexes
ai-shell describe users --indexes

# Show foreign keys
ai-shell describe users --foreign-keys

# Full detail
ai-shell describe users --full
```

**Expected Output:**
```
📋 Table: users

Columns:
┌─────────────┬──────────────┬──────────┬─────────┬─────────────┐
│ Column      │ Type         │ Nullable │ Default │ Extra       │
├─────────────┼──────────────┼──────────┼─────────┼─────────────┤
│ id          │ INTEGER      │ NO       │ NULL    │ PRIMARY KEY │
│ username    │ VARCHAR(50)  │ NO       │ NULL    │ UNIQUE      │
│ email       │ VARCHAR(100) │ NO       │ NULL    │ UNIQUE      │
│ created_at  │ TIMESTAMP    │ YES      │ NOW()   │             │
│ is_active   │ BOOLEAN      │ YES      │ true    │             │
└─────────────┴──────────────┴──────────┴─────────┴─────────────┘

Indexes:
  • PRIMARY KEY on (id)
  • UNIQUE INDEX on (username)
  • UNIQUE INDEX on (email)
```

#### Create Tables

```bash
# Create table
ai-shell query "
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"

# Create table with foreign key
ai-shell query "
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    amount DECIMAL(10,2),
    issue_date DATE,
    due_date DATE
);
"

# Create table from template
ai-shell tables create orders_archive --like orders
```

#### Alter Tables

```bash
# Add column
ai-shell query "ALTER TABLE users ADD COLUMN phone VARCHAR(20);"

# Modify column
ai-shell query "ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(150);"

# Drop column (requires confirmation)
ai-shell query "ALTER TABLE users DROP COLUMN phone;" --confirm

# Add constraint
ai-shell query "
ALTER TABLE orders
ADD CONSTRAINT fk_user
FOREIGN KEY (user_id) REFERENCES users(id);
"

# Rename table
ai-shell query "ALTER TABLE old_name RENAME TO new_name;"
```

> **⚠️ DANGER:** ALTER TABLE operations can lock tables. Use during maintenance windows.

#### Drop Tables

```bash
# Drop table with confirmation
ai-shell query "DROP TABLE temp_table;" --confirm

# Drop with CASCADE (dangerous!)
ai-shell query "DROP TABLE orders CASCADE;" --confirm --force

# Safe approach: rename first
ai-shell query "ALTER TABLE orders RENAME TO orders_archived_2025;"
```

> **🛡️ SAFETY:** Always backup before dropping tables. Consider archiving instead.

---

### E. Index Management

#### List Indexes

```bash
# List all indexes
ai-shell indexes list

# List indexes for specific table
ai-shell indexes list --table users

# Show unused indexes
ai-shell indexes list --unused

# Show index sizes
ai-shell indexes list --size
```

**Expected Output:**
```
📊 Indexes in 'testdb':

┌────────────────────────┬──────────┬────────────────┬──────────┬─────────┐
│ Index Name             │ Table    │ Columns        │ Size     │ Usage   │
├────────────────────────┼──────────┼────────────────┼──────────┼─────────┤
│ users_pkey             │ users    │ id             │ 16 KB    │ 95%     │
│ users_username_key     │ users    │ username       │ 32 KB    │ 78%     │
│ users_email_key        │ users    │ email          │ 32 KB    │ 82%     │
│ orders_user_id_idx     │ orders   │ user_id        │ 128 KB   │ 91%     │
│ orders_status_idx      │ orders   │ status         │ 64 KB    │ 65%     │
│ orders_date_idx        │ orders   │ order_date     │ 96 KB    │ 12% ⚠️  │
└────────────────────────┴──────────┴────────────────┴──────────┴─────────┘

⚠️  Warning: orders_date_idx has low usage (12%)
```

#### Create Indexes

```bash
# Create simple index
ai-shell indexes create idx_users_email users email

# Create composite index
ai-shell indexes create idx_orders_user_date orders user_id order_date

# Create unique index
ai-shell query "CREATE UNIQUE INDEX idx_users_username ON users(username);"

# Create partial index (PostgreSQL)
ai-shell query "
CREATE INDEX idx_orders_pending
ON orders(user_id)
WHERE status = 'pending';
"

# Create index online (no table lock)
ai-shell indexes create idx_large_table_col large_table column_name --online

# Create expression index
ai-shell query "CREATE INDEX idx_users_lower_email ON users(LOWER(email));"
```

> **💡 TIP:** Use `--online` for production databases to avoid locking.

#### Analyze Index Usage

```bash
# Analyze index usage
ai-shell indexes analyze

# Check specific index
ai-shell indexes analyze --index idx_users_email

# Show index hit rate
ai-shell indexes stats

# Detect duplicate indexes
ai-shell indexes duplicates
```

**Expected Output:**
```
📈 Index Usage Analysis:

Top Performing Indexes:
  1. users_pkey: 15,234 scans (99% hit rate)
  2. orders_user_id_idx: 8,432 scans (95% hit rate)

Underutilized Indexes:
  ⚠️  orders_date_idx: 234 scans (12% hit rate)
      Consider dropping if usage remains low

Recommendations:
  • Drop orders_date_idx (low usage)
  • Add composite index on orders(user_id, status)
  • Rebuild users_username_key (fragmented)
```

#### Drop Unused Indexes

```bash
# Drop specific index
ai-shell indexes drop idx_unused_index

# Drop with confirmation
ai-shell indexes drop idx_orders_date --confirm

# Drop all unused indexes (interactive)
ai-shell indexes cleanup

# Force drop (no confirmation)
ai-shell indexes drop idx_test --force
```

> **⚠️ CAUTION:** Dropping indexes can severely impact query performance. Monitor after changes.

#### Rebuild Indexes

```bash
# Rebuild specific index
ai-shell indexes rebuild idx_users_email

# Rebuild all indexes on table
ai-shell indexes rebuild --table users

# Rebuild all indexes (slow!)
ai-shell indexes rebuild --all

# Rebuild concurrently (PostgreSQL)
ai-shell query "REINDEX INDEX CONCURRENTLY idx_users_email;"
```

---

### F. Backup & Restore

#### Create Database Backup

```bash
# Basic backup
ai-shell backup create --database testdb

# Backup with custom name
ai-shell backup create --database testdb --name daily-backup-2025-01-15

# Compressed backup
ai-shell backup create --database testdb --compression gzip

# Incremental backup
ai-shell backup create --database testdb --incremental

# Backup specific tables
ai-shell backup create --database testdb --tables users,orders

# Backup with verification
ai-shell backup create --database testdb --verify

# Cloud backup (AWS S3)
ai-shell backup create --database testdb --cloud --encrypt
```

**Expected Output:**
```
Creating backup...
✓ Backup created successfully

  ID: backup-20250115-143022-a1b2c3
  Path: /backups/testdb-20250115-143022.sql.gz
  Size: 2.4 MB
  Duration: 3.2s

  Tables backed up: users, orders, products (3)
  Compressed: Yes (gzip)
  Verified: Yes ✓
```

#### List Available Backups

```bash
# List all backups
ai-shell backup list

# Filter by database
ai-shell backup list --database testdb

# Filter by date range
ai-shell backup list --after 2025-01-01 --before 2025-01-31

# Show detailed info
ai-shell backup list --output table

# Export list to CSV
ai-shell backup list --output csv > backups.csv

# Sort by size
ai-shell backup list --sort size --order desc
```

**Expected Output:**
```
📋 Backups:

┌──────────────────────┬──────────┬─────────────────────┬──────────┬────────┐
│ ID                   │ Database │ Date                │ Size     │ Format │
├──────────────────────┼──────────┼─────────────────────┼──────────┼────────┤
│ backup-20250115-1430 │ testdb   │ 2025-01-15 14:30:22 │ 2.4 MB   │ sql    │
│ backup-20250114-0200 │ testdb   │ 2025-01-14 02:00:15 │ 2.3 MB   │ sql    │
│ backup-20250113-0200 │ testdb   │ 2025-01-13 02:00:08 │ 2.2 MB   │ sql    │
└──────────────────────┴──────────┴─────────────────────┴──────────┴────────┘

Total: 3 backup(s)
```

#### Restore from Backup

```bash
# Restore latest backup
ai-shell backup restore backup-20250115-143022-a1b2c3

# Restore to different database
ai-shell backup restore backup-20250115-143022-a1b2c3 --database testdb_restored

# Dry run (test without applying)
ai-shell backup restore backup-20250115-143022-a1b2c3 --dry-run

# Restore specific tables only
ai-shell backup restore backup-20250115-143022-a1b2c3 --tables users,orders

# Restore with verification
ai-shell backup restore backup-20250115-143022-a1b2c3 --verify

# Drop existing tables before restore
ai-shell backup restore backup-20250115-143022-a1b2c3 --drop-existing --confirm
```

> **⚠️ DANGER:** Restore operations can overwrite existing data. Always use `--dry-run` first!

**Expected Output:**
```
Verifying backup integrity...
✓ Backup verified. Starting restore...
Restoring backup...
✓ Restore completed successfully

  Database: testdb
  Tables restored: 3
  Rows restored: 15,234
  Duration: 5.8s
```

#### Verify Backup Integrity

```bash
# Quick verification
ai-shell backup verify backup-20250115-143022-a1b2c3

# Deep verification with checksums
ai-shell backup verify backup-20250115-143022-a1b2c3 --deep

# Test restore capability
ai-shell backup verify backup-20250115-143022-a1b2c3 --test

# JSON output
ai-shell backup verify backup-20250115-143022-a1b2c3 --json
```

**Expected Output:**
```
Verifying backup...
✓ Backup is valid

  Checksum: a1b2c3d4e5f6...
  File exists: Yes
  Readable: Yes
  Format: Valid SQL
  Tables: 3 (verified)
  Estimated restore time: 5s
```

#### Schedule Automated Backups

```bash
# Daily backup at 2 AM
ai-shell backup schedule "0 2 * * *" \
  --name daily-backup \
  --database testdb \
  --retention 30

# Hourly backup
ai-shell backup schedule "0 * * * *" \
  --name hourly-backup \
  --database testdb \
  --retention 7

# Weekly backup with cloud upload
ai-shell backup schedule "0 3 * * 0" \
  --name weekly-backup \
  --database testdb \
  --cloud \
  --email admin@example.com

# List scheduled backups
ai-shell backup schedules

# Remove schedule
ai-shell backup unschedule daily-backup
```

**Cron Expression Reference:**
```
* * * * *
│ │ │ │ │
│ │ │ │ └─ Day of week (0-6, Sunday=0)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23)
└───────── Minute (0-59)

Examples:
  "0 2 * * *"     → Daily at 2:00 AM
  "0 */6 * * *"   → Every 6 hours
  "0 0 * * 0"     → Weekly on Sunday
```

---

### G. Performance Monitoring

#### Real-time Metrics

```bash
# Start monitoring
ai-shell monitor start

# Custom update interval
ai-shell monitor start --interval 10

# Monitor specific metrics
ai-shell monitor start --metrics cpu,memory,queries

# JSON output for parsing
ai-shell monitor start --output json

# Stop monitoring
ai-shell monitor stop
```

**Expected Output:**
```
📊 Real-time Performance Monitoring (refresh: 5s)

Database: testdb (PostgreSQL 15.2)
─────────────────────────────────────────────────

System Metrics:
  CPU Usage:     45% ████████░░░░░░░░░░░░
  Memory:        2.3 GB / 8.0 GB (28%)
  Disk I/O:      15 MB/s read, 8 MB/s write

Connection Pool:
  Active:        12 / 50
  Idle:          38
  Waiting:       0

Query Performance:
  Queries/sec:   234
  Avg Duration:  12ms
  Slow Queries:  2
  Errors:        0

Press Ctrl+C to stop monitoring...
```

#### Query Statistics

```bash
# Query statistics
ai-shell stats

# Filter by time period
ai-shell stats --period 1h

# Show top queries
ai-shell stats --top 20

# Export statistics
ai-shell stats --export stats.json
```

#### Connection Pool Status

```bash
# Show pool status
ai-shell pool

# Detailed pool info
ai-shell pool --detailed

# Monitor pool in real-time
ai-shell pool --watch
```

**Expected Output:**
```
🔗 Connection Pool Statistics:

Total Connections:    50
Active Connections:   12 (24%)
Idle Connections:     38 (76%)
Waiting Queries:      0

Performance:
  Avg Wait Time:      2ms
  Max Wait Time:      45ms
  Connections/sec:    15

Health: Healthy ✓
```

#### Cache Hit Rates

```bash
# Show cache statistics
ai-shell cache stats

# Clear query cache
ai-shell cache clear

# Monitor cache in real-time
ai-shell cache monitor
```

#### Slow Query Log

```bash
# View slow query log
ai-shell slow-queries

# Set threshold
ai-shell slow-queries --threshold 500

# Enable slow query logging
ai-shell config set slow_query_threshold 1000

# Disable slow query logging
ai-shell config set slow_query_threshold 0
```

---

### H. Security & Permissions

#### List Users and Roles

```bash
# List all users
ai-shell users list

# Show user details
ai-shell users show alice

# List roles
ai-shell roles list

# Show role permissions
ai-shell roles show admin
```

**Expected Output:**
```
👥 Database Users:

┌──────────┬─────────────┬───────────┬────────────────────────┐
│ Username │ Roles       │ Active    │ Created                │
├──────────┼─────────────┼───────────┼────────────────────────┤
│ admin    │ superuser   │ Yes       │ 2025-01-01 00:00:00    │
│ alice    │ developer   │ Yes       │ 2025-01-15 10:30:00    │
│ bob      │ analyst     │ Yes       │ 2025-01-15 11:00:00    │
│ readonly │ viewer      │ Yes       │ 2025-01-15 12:00:00    │
└──────────┴─────────────┴───────────┴────────────────────────┘
```

#### Grant Permissions

```bash
# Grant table permissions
ai-shell grant SELECT ON users TO alice;
ai-shell grant SELECT, INSERT, UPDATE ON orders TO alice;

# Grant all privileges
ai-shell grant ALL ON TABLE products TO bob;

# Grant database permissions
ai-shell grant CONNECT ON DATABASE testdb TO charlie;

# Grant schema permissions
ai-shell grant USAGE ON SCHEMA public TO analyst_role;

# Grant function permissions
ai-shell grant EXECUTE ON FUNCTION calculate_total TO developer_role;
```

#### Revoke Permissions

```bash
# Revoke table permissions
ai-shell revoke INSERT ON users FROM alice;

# Revoke all privileges
ai-shell revoke ALL ON TABLE orders FROM bob;

# Revoke from role
ai-shell revoke analyst_role FROM alice;
```

#### Audit Log Access

```bash
# View audit log
ai-shell audit log

# Filter by user
ai-shell audit log --user alice

# Filter by action
ai-shell audit log --action DELETE

# Filter by date
ai-shell audit log --since 2025-01-01 --until 2025-01-31

# Export audit log
ai-shell audit log --export audit.csv
```

**Expected Output:**
```
📋 Audit Log:

┌─────────────────────┬──────────┬─────────┬─────────────────────────────┐
│ Timestamp           │ User     │ Action  │ Object                      │
├─────────────────────┼──────────┼─────────┼─────────────────────────────┤
│ 2025-01-15 14:30:22 │ alice    │ SELECT  │ users                       │
│ 2025-01-15 14:32:15 │ alice    │ INSERT  │ orders                      │
│ 2025-01-15 14:35:08 │ bob      │ UPDATE  │ products                    │
│ 2025-01-15 14:40:33 │ alice    │ DELETE  │ orders (id=999)             │
└─────────────────────┴──────────┴─────────┴─────────────────────────────┘
```

#### Password Management

```bash
# Change user password
ai-shell users password alice

# Set password with input
ai-shell users password alice --password newpass123

# Force password change on next login
ai-shell users password alice --force-change

# Set password expiration
ai-shell users password alice --expire-days 90
```

> **🔒 SECURITY:** Never use passwords in command history. Use interactive prompts.

---

## Hands-On Tutorials {#hands-on-tutorials}

### Tutorial 1: Complete PostgreSQL Workflow (15 minutes)

**Objective:** Connect to PostgreSQL, create schema, insert data, optimize queries, and create backup.

#### Step 1: Start PostgreSQL Container

```bash
docker run -d \
  --name tutorial-postgres \
  -e POSTGRES_DB=shopdb \
  -e POSTGRES_USER=shopuser \
  -e POSTGRES_PASSWORD=shoppass123 \
  -p 5433:5432 \
  postgres:15-alpine

# Wait for startup
sleep 10
```

#### Step 2: Connect to Database

```bash
ai-shell connect postgresql://shopuser:shoppass123@localhost:5433/shopdb --name shop-db
```

**Expected:** `✓ Connected to PostgreSQL: shop-db`

#### Step 3: Create Schema

```bash
ai-shell query "
-- Create customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    stock INTEGER DEFAULT 0 CHECK (stock >= 0),
    category VARCHAR(50)
);

-- Create orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'))
);

-- Create order_items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(10,2) NOT NULL
);
"
```

#### Step 4: Insert Sample Data

```bash
# Insert customers
ai-shell query "
INSERT INTO customers (name, email) VALUES
    ('Alice Johnson', 'alice@example.com'),
    ('Bob Smith', 'bob@example.com'),
    ('Charlie Brown', 'charlie@example.com'),
    ('Diana Prince', 'diana@example.com'),
    ('Evan Davis', 'evan@example.com');
"

# Insert products
ai-shell query "
INSERT INTO products (name, price, stock, category) VALUES
    ('Laptop Pro', 1299.99, 50, 'Electronics'),
    ('Wireless Mouse', 29.99, 200, 'Electronics'),
    ('Mechanical Keyboard', 89.99, 150, 'Electronics'),
    ('27\" Monitor', 399.99, 75, 'Electronics'),
    ('USB-C Hub', 49.99, 100, 'Electronics'),
    ('Laptop Bag', 59.99, 80, 'Accessories'),
    ('Desk Lamp', 39.99, 120, 'Office'),
    ('Office Chair', 299.99, 30, 'Furniture');
"

# Insert orders
ai-shell query "
INSERT INTO orders (customer_id, total_amount, status) VALUES
    (1, 1329.98, 'delivered'),
    (2, 439.98, 'shipped'),
    (3, 89.99, 'processing'),
    (1, 499.97, 'delivered'),
    (4, 1299.99, 'pending'),
    (5, 149.97, 'processing');
"

# Insert order items
ai-shell query "
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
    (1, 1, 1, 1299.99),
    (1, 2, 1, 29.99),
    (2, 4, 1, 399.99),
    (2, 5, 1, 39.99),
    (3, 3, 1, 89.99),
    (4, 2, 5, 29.99),
    (4, 6, 1, 59.99),
    (5, 1, 1, 1299.99),
    (6, 3, 1, 89.99),
    (6, 7, 1, 39.99);
"
```

#### Step 5: Run Analytics Queries

```bash
# Total revenue by status
ai-shell query "
SELECT
    status,
    COUNT(*) as order_count,
    SUM(total_amount) as revenue
FROM orders
GROUP BY status
ORDER BY revenue DESC;
"

# Top customers
ai-shell query "
SELECT
    c.name,
    c.email,
    COUNT(o.id) as order_count,
    SUM(o.total_amount) as total_spent
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name, c.email
ORDER BY total_spent DESC
LIMIT 5;
"

# Product inventory status
ai-shell query "
SELECT
    category,
    COUNT(*) as products,
    SUM(stock) as total_stock,
    AVG(price) as avg_price
FROM products
GROUP BY category;
"
```

#### Step 6: Identify Slow Queries

```bash
# Analyze a complex query
ai-shell analyze "
SELECT
    c.name,
    o.id as order_id,
    o.order_date,
    p.name as product_name,
    oi.quantity
FROM customers c
JOIN orders o ON c.id = o.customer_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.status = 'delivered'
ORDER BY o.order_date DESC;
"
```

#### Step 7: Create Indexes

```bash
# Create indexes based on recommendations
ai-shell indexes create idx_orders_status orders status
ai-shell indexes create idx_orders_customer orders customer_id
ai-shell indexes create idx_order_items_order order_items order_id
ai-shell indexes create idx_order_items_product order_items product_id

# Verify indexes
ai-shell indexes list --table orders
```

#### Step 8: Create Backup

```bash
# Create comprehensive backup
ai-shell backup create \
  --database shopdb \
  --name tutorial-backup-complete \
  --compression gzip \
  --verify

# List backups
ai-shell backup list
```

#### Step 9: Test Restore (Dry Run)

```bash
# Test restore without applying
ai-shell backup restore <backup-id> --dry-run

# If dry run successful, actual restore would be:
# ai-shell backup restore <backup-id> --database shopdb_restored
```

#### Step 10: Cleanup

```bash
# Disconnect
ai-shell disconnect shop-db

# Stop container
docker stop tutorial-postgres
docker rm tutorial-postgres
```

**🎉 Congratulations!** You've completed a full database workflow.

---

### Tutorial 2: MongoDB Document Operations (10 minutes)

**Objective:** Work with MongoDB collections, documents, and queries.

#### Step 1: Start MongoDB

```bash
docker run -d --name tutorial-mongo -p 27018:27017 mongo:7.0
sleep 5
ai-shell connect mongodb://localhost:27018/blogdb
```

#### Step 2: Insert Documents

```bash
# Insert blog posts
ai-shell mongodb insert posts '{
  "title": "Getting Started with AI-Shell",
  "author": "Alice",
  "content": "AI-Shell is a powerful database management tool...",
  "tags": ["database", "tutorial", "ai"],
  "published": true,
  "created_at": {"$date": "2025-01-15T10:00:00Z"},
  "views": 0
}'

ai-shell mongodb insert posts '[
  {
    "title": "Advanced Query Optimization",
    "author": "Bob",
    "content": "Learn how to optimize your database queries...",
    "tags": ["optimization", "performance"],
    "published": true,
    "views": 150
  },
  {
    "title": "MongoDB Best Practices",
    "author": "Charlie",
    "content": "Essential tips for working with MongoDB...",
    "tags": ["mongodb", "best-practices"],
    "published": false,
    "views": 0
  }
]'

# Insert comments
ai-shell mongodb insert comments '[
  {
    "post_id": "<first-post-id>",
    "author": "Reader1",
    "text": "Great article!",
    "created_at": {"$date": "2025-01-15T11:00:00Z"}
  }
]'
```

#### Step 3: Query Documents

```bash
# Find all published posts
ai-shell mongodb find posts '{"published": true}'

# Find posts by author
ai-shell mongodb find posts '{"author": "Alice"}'

# Find posts with specific tag
ai-shell mongodb find posts '{"tags": "optimization"}'

# Find with projection (specific fields)
ai-shell mongodb find posts '{}' --project '{"title": 1, "author": 1}'

# Sort by views
ai-shell mongodb find posts '{}' --sort '{"views": -1}'

# Limit results
ai-shell mongodb find posts '{}' --limit 2
```

#### Step 4: Update Documents

```bash
# Update single document
ai-shell mongodb update posts \
  '{"title": "Getting Started with AI-Shell"}' \
  '{"$set": {"views": 100}}'

# Increment views
ai-shell mongodb update posts \
  '{"title": "Getting Started with AI-Shell"}' \
  '{"$inc": {"views": 1}}'

# Add tag
ai-shell mongodb update posts \
  '{"author": "Alice"}' \
  '{"$push": {"tags": "beginner"}}'

# Update multiple documents
ai-shell mongodb update posts \
  '{"published": false}' \
  '{"$set": {"status": "draft"}}' \
  --multiple
```

#### Step 5: Aggregation Pipeline

```bash
# Count posts by author
ai-shell mongodb aggregate posts '[
  {
    "$group": {
      "_id": "$author",
      "post_count": {"$sum": 1},
      "total_views": {"$sum": "$views"}
    }
  },
  {
    "$sort": {"total_views": -1}
  }
]'

# Find most popular tags
ai-shell mongodb aggregate posts '[
  {"$unwind": "$tags"},
  {
    "$group": {
      "_id": "$tags",
      "count": {"$sum": 1}
    }
  },
  {"$sort": {"count": -1}}
]'
```

#### Step 6: Create Indexes

```bash
# Create index on author
ai-shell mongodb createIndex posts '{"author": 1}'

# Create compound index
ai-shell mongodb createIndex posts '{"published": 1, "created_at": -1}'

# Create text index for search
ai-shell mongodb createIndex posts '{"title": "text", "content": "text"}'

# List indexes
ai-shell mongodb listIndexes posts
```

#### Step 7: Cleanup

```bash
ai-shell disconnect
docker stop tutorial-mongo && docker rm tutorial-mongo
```

---

### Tutorial 3: Redis Caching Patterns (10 minutes)

**Objective:** Implement common caching patterns with Redis.

#### Step 1: Connect to Redis

```bash
docker run -d --name tutorial-redis -p 6380:6379 redis:7-alpine
sleep 2
ai-shell redis connect redis://localhost:6380
```

#### Step 2: Simple Cache Operations

```bash
# Cache user data
ai-shell redis set "user:1001" '{"name": "Alice", "email": "alice@example.com"}'

# Get cached data
ai-shell redis get "user:1001"

# Set with expiration (300 seconds = 5 minutes)
ai-shell redis setex "session:abc123" 300 '{"user_id": 1001, "role": "admin"}'

# Check TTL
ai-shell redis ttl "session:abc123"

# Delete cache
ai-shell redis del "session:abc123"
```

#### Step 3: Hash Operations (User Profile)

```bash
# Store user profile as hash
ai-shell redis hset "user:1001:profile" "name" "Alice Johnson"
ai-shell redis hset "user:1001:profile" "email" "alice@example.com"
ai-shell redis hset "user:1001:profile" "age" "30"
ai-shell redis hset "user:1001:profile" "city" "San Francisco"

# Get all fields
ai-shell redis hgetall "user:1001:profile"

# Get specific field
ai-shell redis hget "user:1001:profile" "email"

# Increment counter
ai-shell redis hincrby "user:1001:stats" "login_count" 1
```

#### Step 4: List Operations (Activity Feed)

```bash
# Add to activity feed (newest first)
ai-shell redis lpush "feed:1001" "User logged in"
ai-shell redis lpush "feed:1001" "User updated profile"
ai-shell redis lpush "feed:1001" "User posted comment"

# Get recent activities
ai-shell redis lrange "feed:1001" 0 9

# Trim to keep only last 100 items
ai-shell redis ltrim "feed:1001" 0 99
```

#### Step 5: Set Operations (Tags)

```bash
# Add tags to post
ai-shell redis sadd "post:101:tags" "database"
ai-shell redis sadd "post:101:tags" "tutorial"
ai-shell redis sadd "post:101:tags" "redis"

# Check if tag exists
ai-shell redis sismember "post:101:tags" "redis"

# Get all tags
ai-shell redis smembers "post:101:tags"

# Find common tags between posts
ai-shell redis sinter "post:101:tags" "post:102:tags"
```

#### Step 6: Sorted Set (Leaderboard)

```bash
# Add players to leaderboard
ai-shell redis zadd "leaderboard" 1000 "Alice"
ai-shell redis zadd "leaderboard" 1500 "Bob"
ai-shell redis zadd "leaderboard" 2000 "Charlie"
ai-shell redis zadd "leaderboard" 1200 "Diana"

# Get top 3 players
ai-shell redis zrevrange "leaderboard" 0 2 --withscores

# Get player rank
ai-shell redis zrevrank "leaderboard" "Bob"

# Increment score
ai-shell redis zincrby "leaderboard" 100 "Alice"
```

#### Step 7: Pub/Sub Pattern

```bash
# Terminal 1: Subscribe to channel
ai-shell redis subscribe notifications

# Terminal 2: Publish message
ai-shell redis publish notifications "New order received"
ai-shell redis publish notifications "User registered"
```

#### Step 8: Monitor Performance

```bash
# Get Redis info
ai-shell redis info

# Monitor commands in real-time
ai-shell redis monitor

# Get statistics
ai-shell redis dbsize
ai-shell redis keys "*:1001:*"
```

#### Step 9: Cleanup

```bash
# Flush specific keys
ai-shell redis del "user:1001"

# Or flush entire database (DANGER!)
# ai-shell redis flushdb --confirm

ai-shell redis disconnect
docker stop tutorial-redis && docker rm tutorial-redis
```

---

### Tutorial 4: Query Optimization Workflow (15 minutes)

**Objective:** Identify, analyze, and optimize slow queries.

#### Prerequisites

Ensure you have the PostgreSQL setup from Tutorial 1, or start it:

```bash
docker start tutorial-postgres || docker run -d \
  --name tutorial-postgres \
  -e POSTGRES_DB=shopdb \
  -e POSTGRES_USER=shopuser \
  -e POSTGRES_PASSWORD=shoppass123 \
  -p 5433:5432 \
  postgres:15-alpine

sleep 10
ai-shell connect postgresql://shopuser:shoppass123@localhost:5433/shopdb --name shop-db
```

#### Step 1: Generate Load (Create Slow Query)

```bash
# Create a deliberately slow query
ai-shell query "
-- This query will be slow without proper indexes
SELECT
    c.name as customer_name,
    COUNT(o.id) as order_count,
    SUM(o.total_amount) as total_spent,
    AVG(o.total_amount) as avg_order_value,
    MAX(o.order_date) as last_order_date
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE o.status IN ('delivered', 'shipped')
GROUP BY c.id, c.name
HAVING COUNT(o.id) > 0
ORDER BY total_spent DESC;
"
```

#### Step 2: Identify Slow Queries

```bash
# List slow queries
ai-shell slow-queries --threshold 100

# Get detailed slow query report
ai-shell slow-queries --export slow-queries.json --format json
```

**Expected Output:**
```
🐌 Found 3 slow queries:

1. ⏱️  1,234ms (executed 5x)
   SELECT c.name, COUNT(o.id), SUM(o.total_amount)...

   💡 Suggestions:
      • Add index on orders(status)
      • Add index on orders(customer_id, status)
```

#### Step 3: Analyze Query Plan

```bash
# Get EXPLAIN plan
ai-shell explain "
SELECT
    c.name,
    COUNT(o.id) as order_count
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE o.status = 'delivered'
GROUP BY c.id, c.name;
" --analyze
```

**Expected Output:**
```
EXPLAIN ANALYZE:

HashAggregate (cost=45.50..47.50 rows=200 width=32) (actual time=12.345..13.456 rows=5 loops=1)
  -> Hash Join (cost=12.50..42.50 rows=600 width=24) (actual time=2.345..10.234 rows=5 loops=1)
        Hash Cond: (o.customer_id = c.id)
        -> Seq Scan on orders o (cost=0.00..25.00 rows=600 width=8) (actual time=0.123..8.234 rows=4 loops=1)
              Filter: (status = 'delivered'::text)
              Rows Removed by Filter: 2
        -> Hash (cost=10.00..10.00 rows=200 width=24) (actual time=1.234..1.234 rows=5 loops=1)
              -> Seq Scan on customers c (cost=0.00..10.00 rows=200 width=24)

⚠️  Performance Issues:
  • Sequential scan on orders table (4ms)
  • Missing index on orders(status)
  • Missing index on orders(customer_id)

Planning Time: 0.234 ms
Execution Time: 13.678 ms
```

#### Step 4: Get Index Recommendations

```bash
# Get index recommendations
ai-shell indexes recommendations

# Get missing indexes
ai-shell indexes missing --threshold 100
```

**Expected Output:**
```
📊 Index Recommendations:

1. High Priority:
   CREATE INDEX idx_orders_status ON orders(status);

   Reason: Sequential scan detected in 5 queries
   Expected improvement: 60-80% faster
   Estimated creation time: <1s

2. High Priority:
   CREATE INDEX idx_orders_customer_status ON orders(customer_id, status);

   Reason: Composite index for JOIN + WHERE
   Expected improvement: 70-90% faster
   Estimated creation time: <1s
```

#### Step 5: Create Recommended Indexes

```bash
# Create indexes
ai-shell indexes create idx_orders_status orders status
ai-shell indexes create idx_orders_customer_status orders customer_id status

# Verify index creation
ai-shell indexes list --table orders
```

#### Step 6: Re-run Query and Compare

```bash
# Run the same query again
ai-shell query "
SELECT
    c.name as customer_name,
    COUNT(o.id) as order_count,
    SUM(o.total_amount) as total_spent
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE o.status IN ('delivered', 'shipped')
GROUP BY c.id, c.name
HAVING COUNT(o.id) > 0
ORDER BY total_spent DESC;
"

# Analyze again to see improvement
ai-shell explain "
SELECT
    c.name,
    COUNT(o.id) as order_count
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE o.status = 'delivered'
GROUP BY c.id, c.name;
" --analyze
```

**Expected Output (After Optimization):**
```
EXPLAIN ANALYZE:

HashAggregate (cost=18.50..20.50 rows=200 width=32) (actual time=1.234..1.456 rows=5 loops=1)
  -> Hash Join (cost=5.50..15.50 rows=600 width=24) (actual time=0.345..1.123 rows=5 loops=1)
        -> Index Scan using idx_orders_customer_status on orders o (cost=0.15..8.50 rows=600 width=8)
              Index Cond: (status = 'delivered'::text)
        -> Hash (cost=5.00..5.00 rows=200 width=24)

✓ Performance Improved:
  • Using index scan instead of sequential scan
  • Execution time: 1.456ms (down from 13.678ms)
  • 89% improvement

Planning Time: 0.156 ms
Execution Time: 1.456 ms
```

#### Step 7: Monitor Index Usage

```bash
# Check index usage statistics
ai-shell indexes stats

# Analyze index performance
ai-shell indexes analyze --index idx_orders_customer_status
```

#### Step 8: Enable Auto-Optimization

```bash
# Enable automatic query optimization
ai-shell auto-optimize enable --threshold 500 --max-per-day 10

# Check auto-optimization status
ai-shell auto-optimize status
```

#### Step 9: Performance Monitoring

```bash
# Monitor query performance
ai-shell monitor start --metrics queries,response-time

# View performance report
ai-shell performance report 1h
```

#### Step 10: Cleanup

```bash
ai-shell disconnect shop-db
```

**🎉 Success!** You've identified and fixed a slow query, improving performance by 89%.

---

### Tutorial 5: Backup & Disaster Recovery (10 minutes)

**Objective:** Create backups, simulate data loss, and recover.

#### Step 1: Setup Test Database

```bash
# Start fresh PostgreSQL instance
docker run -d \
  --name tutorial-backup \
  -e POSTGRES_DB=productiondb \
  -e POSTGRES_USER=produser \
  -e POSTGRES_PASSWORD=prodpass123 \
  -p 5434:5432 \
  postgres:15-alpine

sleep 10
ai-shell connect postgresql://produser:prodpass123@localhost:5434/productiondb --name prod-backup
```

#### Step 2: Create Production Data

```bash
# Create schema
ai-shell query "
CREATE TABLE critical_data (
    id SERIAL PRIMARY KEY,
    data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO critical_data (data) VALUES
    ('Important record 1'),
    ('Important record 2'),
    ('Important record 3'),
    ('Important record 4'),
    ('Important record 5');
"

# Verify data
ai-shell query "SELECT COUNT(*) FROM critical_data;"
```

**Expected:** `count: 5`

#### Step 3: Create Initial Backup

```bash
# Create full backup
ai-shell backup create \
  --database productiondb \
  --name initial-backup \
  --compression gzip \
  --verify

# Save the backup ID from output
BACKUP_ID="<backup-id-from-output>"
```

**Expected Output:**
```
✓ Backup created successfully

  ID: backup-20250115-150000-abc123
  Path: /backups/productiondb-20250115-150000.sql.gz
  Size: 4.2 KB
  Duration: 0.8s
  Verified: Yes ✓
```

#### Step 4: Make Changes

```bash
# Add more data
ai-shell query "
INSERT INTO critical_data (data) VALUES
    ('Important record 6'),
    ('Important record 7'),
    ('Important record 8');
"

# Verify
ai-shell query "SELECT COUNT(*) FROM critical_data;"
```

**Expected:** `count: 8`

#### Step 5: Create Incremental Backup

```bash
# Create incremental backup
ai-shell backup create \
  --database productiondb \
  --name incremental-backup \
  --incremental \
  --verify

INCREMENTAL_ID="<backup-id-from-output>"
```

#### Step 6: Simulate Data Loss

```bash
# Accidentally delete critical data
ai-shell query "DELETE FROM critical_data WHERE id > 3;"

# Verify data loss
ai-shell query "SELECT COUNT(*) FROM critical_data;"
```

**Expected:** `count: 3` (5 records lost!)

#### Step 7: List Available Backups

```bash
# List all backups
ai-shell backup list --database productiondb

# Check backup details
ai-shell backup status $BACKUP_ID
```

#### Step 8: Verify Backup Before Restore

```bash
# Verify backup integrity
ai-shell backup verify $BACKUP_ID --deep --test
```

**Expected Output:**
```
Verifying backup...
✓ Backup is valid

  Checksum: Verified ✓
  File exists: Yes
  Readable: Yes
  Format: Valid SQL
  Tables: 1 (verified)

  Restore Tests:
    ✓ Schema validation: Passed
    ✓ Data integrity: Passed
    ✓ Foreign keys: Passed

Estimated restore time: 2s
```

#### Step 9: Test Restore (Dry Run)

```bash
# Dry run to verify restore process
ai-shell backup restore $BACKUP_ID --dry-run
```

**Expected Output:**
```
✓ Dry run completed successfully

  Would restore:
    Database: productiondb
    Tables: critical_data
    Rows: 5
    Duration estimate: 2s

  No changes were made to the database
```

#### Step 10: Perform Actual Restore

```bash
# Restore from backup
ai-shell backup restore $BACKUP_ID --verify

# Verify data recovery
ai-shell query "SELECT COUNT(*) FROM critical_data;"
```

**Expected:** `count: 5` (Data recovered!)

```bash
# Confirm all data is back
ai-shell query "SELECT * FROM critical_data ORDER BY id;"
```

#### Step 11: Schedule Automated Backups

```bash
# Schedule daily backups at 2 AM
ai-shell backup schedule "0 2 * * *" \
  --name daily-production-backup \
  --database productiondb \
  --retention 30 \
  --compression gzip \
  --verify

# Schedule weekly backups on Sunday
ai-shell backup schedule "0 3 * * 0" \
  --name weekly-production-backup \
  --database productiondb \
  --retention 90 \
  --cloud

# List schedules
ai-shell backup schedules
```

#### Step 12: Export Backup to External Location

```bash
# Export backup for offsite storage
ai-shell backup export $BACKUP_ID ~/external-backup/production-backup.sql.gz

# Verify export
ls -lh ~/external-backup/
```

#### Step 13: Test Import from External Backup

```bash
# Import backup from external location
ai-shell backup import ~/external-backup/production-backup.sql.gz --verify

# List backups to see imported backup
ai-shell backup list
```

#### Step 14: Cleanup

```bash
# Disconnect
ai-shell disconnect prod-backup

# Stop container
docker stop tutorial-backup && docker rm tutorial-backup

# Clean up backup files (optional)
# ai-shell backup delete $BACKUP_ID --force
```

**🎉 Mission Accomplished!** You've successfully implemented a complete backup and recovery workflow.

---

## Command Reference {#command-reference}

### PostgreSQL Commands (20+ Essential)

```bash
# Connection
ai-shell connect postgresql://user:pass@host:port/dbname
ai-shell disconnect
ai-shell ping

# Queries
ai-shell query "SELECT * FROM table;"
ai-shell query "SELECT * FROM table;" --format csv
ai-shell query "SELECT * FROM table;" --output results.json

# Tables
ai-shell tables list
ai-shell describe tablename
ai-shell query "CREATE TABLE name (...);"
ai-shell query "DROP TABLE name;" --confirm

# Indexes
ai-shell indexes list
ai-shell indexes create idx_name table column
ai-shell indexes drop idx_name
ai-shell indexes analyze

# Backup
ai-shell backup create --database dbname
ai-shell backup list
ai-shell backup restore backup-id
ai-shell backup verify backup-id

# Performance
ai-shell slow-queries
ai-shell explain "query"
ai-shell analyze "query"
ai-shell optimize "query"

# Monitoring
ai-shell health
ai-shell monitor start
ai-shell performance report
```

### MySQL Commands (20+ Essential)

```bash
# Connection
ai-shell connect mysql://user:pass@host:port/dbname

# Queries (same as PostgreSQL)
ai-shell query "SELECT * FROM table;"

# MySQL-specific
ai-shell query "SHOW TABLES;"
ai-shell query "SHOW CREATE TABLE tablename;"
ai-shell query "SHOW INDEX FROM tablename;"
ai-shell query "SHOW PROCESSLIST;"

# Storage Engines
ai-shell query "SHOW ENGINES;"
ai-shell query "ALTER TABLE name ENGINE=InnoDB;"

# Optimization
ai-shell query "OPTIMIZE TABLE tablename;"
ai-shell query "ANALYZE TABLE tablename;"

# Replication
ai-shell query "SHOW MASTER STATUS;"
ai-shell query "SHOW SLAVE STATUS;"

# Performance Schema
ai-shell query "SELECT * FROM performance_schema.events_statements_summary_by_digest ORDER BY SUM_TIMER_WAIT DESC LIMIT 10;"
```

### MongoDB Commands (20+ Essential)

```bash
# Connection
ai-shell connect mongodb://host:port/dbname

# Collections
ai-shell mongodb collections
ai-shell mongodb createCollection collname

# Insert
ai-shell mongodb insert collname '{"key": "value"}'
ai-shell mongodb insert collname '[{}, {}]'

# Find
ai-shell mongodb find collname '{}'
ai-shell mongodb find collname '{"key": "value"}'
ai-shell mongodb findOne collname '{"_id": "..."}'

# Update
ai-shell mongodb update collname '{"filter"}' '{"$set": {}}'
ai-shell mongodb updateMany collname '{"filter"}' '{"$set": {}}'

# Delete
ai-shell mongodb delete collname '{"filter"}'
ai-shell mongodb deleteMany collname '{"filter"}'

# Count
ai-shell mongodb count collname
ai-shell mongodb count collname '{"filter"}'

# Aggregation
ai-shell mongodb aggregate collname '[{$match: {}}, {$group: {}}]'

# Indexes
ai-shell mongodb listIndexes collname
ai-shell mongodb createIndex collname '{"field": 1}'
ai-shell mongodb dropIndex collname indexname

# Stats
ai-shell mongodb stats collname
ai-shell mongodb dbstats
```

### Redis Commands (20+ Essential)

```bash
# Connection
ai-shell redis connect redis://host:port
ai-shell redis ping

# String Operations
ai-shell redis set key value
ai-shell redis get key
ai-shell redis del key
ai-shell redis setex key seconds value
ai-shell redis ttl key

# Hash Operations
ai-shell redis hset key field value
ai-shell redis hget key field
ai-shell redis hgetall key
ai-shell redis hdel key field

# List Operations
ai-shell redis lpush key value
ai-shell redis rpush key value
ai-shell redis lrange key start stop
ai-shell redis lpop key

# Set Operations
ai-shell redis sadd key member
ai-shell redis smembers key
ai-shell redis srem key member

# Sorted Set Operations
ai-shell redis zadd key score member
ai-shell redis zrange key start stop
ai-shell redis zrevrange key start stop --withscores

# Key Operations
ai-shell redis keys pattern
ai-shell redis exists key
ai-shell redis expire key seconds

# Info
ai-shell redis info
ai-shell redis dbsize
ai-shell redis flushdb --confirm
```

### Cross-Database Commands

```bash
# Works with any database type
ai-shell connections list
ai-shell use connection-name
ai-shell current
ai-shell health
ai-shell monitor start
ai-shell performance report
ai-shell backup create --database dbname
ai-shell backup list
ai-shell backup restore backup-id
ai-shell history
ai-shell help
```

---

## Troubleshooting {#troubleshooting}

### Common Errors and Solutions

#### Error: "Connection refused"

**Symptoms:**
```
Error: Connection refused (ECONNREFUSED)
Cannot connect to postgresql://localhost:5432
```

**Solutions:**

1. Check if Docker container is running:
```bash
docker ps | grep postgres
```

2. Restart container:
```bash
docker restart aishell-postgres
```

3. Check port mapping:
```bash
docker port aishell-postgres
```

4. Verify connection string:
```bash
# Correct format
postgresql://user:password@host:port/database
```

5. Check firewall/network:
```bash
telnet localhost 5432
# or
nc -zv localhost 5432
```

---

#### Error: "Authentication failed"

**Symptoms:**
```
Error: password authentication failed for user "testuser"
FATAL: password authentication failed
```

**Solutions:**

1. Verify credentials in `.env`:
```bash
cat .env | grep POSTGRES
```

2. Reset password:
```bash
docker exec -it aishell-postgres psql -U postgres -c "ALTER USER testuser PASSWORD 'newpassword';"
```

3. Check pg_hba.conf (PostgreSQL):
```bash
docker exec aishell-postgres cat /var/lib/postgresql/data/pg_hba.conf
```

4. Use correct connection string:
```bash
# Ensure special characters are URL-encoded
# @ → %40
# : → %3A
ai-shell connect "postgresql://user:p%40ssw0rd@localhost:5432/db"
```

---

#### Error: "Table does not exist"

**Symptoms:**
```
Error: relation "users" does not exist
```

**Solutions:**

1. List all tables:
```bash
ai-shell tables list
```

2. Check schema:
```bash
ai-shell query "SELECT * FROM information_schema.tables WHERE table_name = 'users';"
```

3. Specify schema explicitly:
```bash
ai-shell query "SELECT * FROM public.users;"
```

4. Create table if missing:
```bash
ai-shell query "CREATE TABLE users (...);"
```

---

#### Error: "Slow queries detected"

**Symptoms:**
```
⚠️  Query took 3,456ms
Warning: Slow query detected
```

**Solutions:**

1. Analyze query:
```bash
ai-shell analyze "YOUR_SLOW_QUERY"
```

2. Check missing indexes:
```bash
ai-shell indexes missing
```

3. Create recommended indexes:
```bash
ai-shell indexes recommendations --apply
```

4. Enable auto-optimization:
```bash
ai-shell auto-optimize enable
```

---

#### Error: "Backup failed"

**Symptoms:**
```
Error: Backup creation failed
Insufficient disk space
```

**Solutions:**

1. Check disk space:
```bash
df -h
```

2. Clean old backups:
```bash
ai-shell backup list
ai-shell backup delete old-backup-id
```

3. Change backup location:
```bash
ai-shell backup config --set backupDir=/mnt/backups
```

4. Use compression:
```bash
ai-shell backup create --database dbname --compression gzip
```

---

### Connection Issues

#### Can't connect to Docker container

```bash
# 1. Check Docker is running
docker info

# 2. Check container status
docker ps -a | grep aishell

# 3. Check container logs
docker logs aishell-postgres

# 4. Restart Docker
sudo systemctl restart docker  # Linux
# or restart Docker Desktop on Mac/Windows

# 5. Recreate container
docker rm -f aishell-postgres
docker run -d --name aishell-postgres -p 5432:5432 postgres:15-alpine
```

---

#### Port already in use

```bash
# Find process using port
lsof -i :5432
# or
netstat -tulpn | grep 5432

# Kill process
kill -9 <PID>

# Or use different port
docker run -d -p 5433:5432 postgres:15-alpine
ai-shell connect postgresql://user:pass@localhost:5433/db
```

---

### Performance Problems

#### Queries are slow

```bash
# 1. Check slow queries
ai-shell slow-queries --threshold 100

# 2. Analyze execution plan
ai-shell explain "YOUR_QUERY" --analyze

# 3. Check missing indexes
ai-shell indexes missing

# 4. Monitor in real-time
ai-shell monitor start

# 5. Check connection pool
ai-shell pool

# 6. Vacuum database (PostgreSQL)
ai-shell query "VACUUM ANALYZE;"
```

---

#### High memory usage

```bash
# 1. Check metrics
ai-shell performance report

# 2. Check connection count
ai-shell connections list

# 3. Reduce connection pool size
ai-shell config set max_connections 50

# 4. Clear cache
ai-shell cache clear

# 5. Restart database
docker restart aishell-postgres
```

---

### Backup Failures

#### Restore fails with errors

```bash
# 1. Verify backup integrity
ai-shell backup verify backup-id --deep --test

# 2. Check backup details
ai-shell backup status backup-id

# 3. Try dry run first
ai-shell backup restore backup-id --dry-run

# 4. Drop existing tables
ai-shell backup restore backup-id --drop-existing

# 5. Restore to new database
ai-shell backup restore backup-id --database new_db_name
```

---

### Permission Errors

#### Access denied

```bash
# 1. Check current user
ai-shell query "SELECT current_user;"

# 2. Check permissions
ai-shell query "SELECT * FROM information_schema.table_privileges WHERE grantee = current_user;"

# 3. Grant permissions (as admin)
ai-shell grant SELECT,INSERT,UPDATE,DELETE ON table TO user;

# 4. Check role membership
ai-shell query "SELECT * FROM pg_roles WHERE rolname = current_user;"
```

---

## Best Practices {#best-practices}

### Safety Guidelines

#### 1. Always Use Transactions for Critical Operations

```bash
# ✅ GOOD: Use transactions
ai-shell query "
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
-- Review changes before committing
SELECT * FROM accounts WHERE id IN (1, 2);
COMMIT;
"

# ❌ BAD: Direct updates without transaction
ai-shell query "UPDATE accounts SET balance = balance - 100 WHERE id = 1;"
```

#### 2. Use Dry Run for Destructive Operations

```bash
# ✅ GOOD: Test first
ai-shell backup restore backup-id --dry-run
ai-shell query "DELETE FROM users WHERE ..." --dry-run

# Then execute
ai-shell backup restore backup-id
```

#### 3. Always Backup Before Major Changes

```bash
# ✅ GOOD: Backup before ALTER TABLE
ai-shell backup create --database prod --name pre-migration-backup
ai-shell query "ALTER TABLE users ADD COLUMN new_field VARCHAR(50);"

# ❌ BAD: No backup before schema change
ai-shell query "ALTER TABLE users DROP COLUMN important_data;"
```

#### 4. Verify WHERE Clause Before DELETE/UPDATE

```bash
# ✅ GOOD: Verify with SELECT first
ai-shell query "SELECT COUNT(*) FROM users WHERE last_login < '2024-01-01';"
# If count is expected, then DELETE
ai-shell query "DELETE FROM users WHERE last_login < '2024-01-01';" --confirm

# ❌ BAD: Delete without verification
ai-shell query "DELETE FROM users WHERE last_login < '2024-01-01';"
```

---

### Performance Tips

#### 1. Use Indexes Wisely

```bash
# ✅ GOOD: Create indexes on frequently queried columns
ai-shell indexes create idx_users_email users email
ai-shell indexes create idx_orders_user_date orders user_id order_date

# ⚠️ CAUTION: Too many indexes slow down INSERTs
# Monitor index usage
ai-shell indexes stats
# Drop unused indexes
ai-shell indexes list --unused
```

#### 2. Optimize Queries Before Production

```bash
# ✅ GOOD: Analyze queries during development
ai-shell analyze "SELECT * FROM orders WHERE status = 'pending';"
ai-shell indexes recommendations

# Enable auto-optimization
ai-shell auto-optimize enable --threshold 500
```

#### 3. Use Connection Pooling

```bash
# ✅ GOOD: Configure connection pool
ai-shell config set pool_size 20
ai-shell config set max_connections 100

# Monitor pool usage
ai-shell pool --watch
```

#### 4. Regular Maintenance

```bash
# ✅ GOOD: Schedule regular maintenance
# PostgreSQL
ai-shell query "VACUUM ANALYZE;" # Weekly

# MySQL
ai-shell query "OPTIMIZE TABLE users;" # Monthly

# MongoDB
ai-shell mongodb compact collection # As needed

# Rebuild indexes
ai-shell indexes rebuild --all # Monthly
```

---

### Security Recommendations

#### 1. Never Store Passwords in Plain Text

```bash
# ✅ GOOD: Use environment variables
export DB_PASSWORD="secret123"
ai-shell connect postgresql://user:${DB_PASSWORD}@host/db

# ✅ GOOD: Use .env file (gitignored)
echo "DB_PASSWORD=secret123" >> .env
ai-shell connect postgresql://user:$(grep DB_PASSWORD .env | cut -d= -f2)@host/db

# ❌ BAD: Hardcoded password
ai-shell connect postgresql://user:password123@host/db
```

#### 2. Use SSL for Production Connections

```bash
# ✅ GOOD: SSL enabled
ai-shell connect postgresql://user:pass@host/db --ssl

# Configure SSL certificates
ai-shell config set ssl_cert /path/to/cert.pem
ai-shell config set ssl_key /path/to/key.pem
```

#### 3. Principle of Least Privilege

```bash
# ✅ GOOD: Grant minimal permissions
ai-shell grant SELECT ON users TO readonly_user;
ai-shell grant SELECT,INSERT ON orders TO app_user;

# ❌ BAD: Grant all privileges
ai-shell grant ALL ON DATABASE prod TO app_user;
```

#### 4. Enable Audit Logging

```bash
# ✅ GOOD: Enable audit log
ai-shell config set audit_log true
ai-shell audit log --since today

# Review suspicious activity
ai-shell audit log --action DELETE --user suspicious_user
```

#### 5. Regular Security Audits

```bash
# ✅ GOOD: Regular security checks
ai-shell users list # Review user accounts
ai-shell roles list # Review permissions
ai-shell audit log --since 7d # Review recent activity

# Check for weak passwords
ai-shell security audit
```

---

### Backup Strategies

#### 1. 3-2-1 Backup Rule

- **3 copies** of data
- **2 different media types**
- **1 copy offsite**

```bash
# Local backup
ai-shell backup create --database prod --name daily-backup

# Cloud backup
ai-shell backup create --database prod --cloud --encrypt

# Export to external storage
ai-shell backup export backup-id /mnt/external/backups/
```

#### 2. Regular Backup Schedule

```bash
# Daily backups (keep 7 days)
ai-shell backup schedule "0 2 * * *" \
  --name daily-backup \
  --database prod \
  --retention 7

# Weekly backups (keep 4 weeks)
ai-shell backup schedule "0 3 * * 0" \
  --name weekly-backup \
  --database prod \
  --retention 28

# Monthly backups (keep 1 year)
ai-shell backup schedule "0 4 1 * *" \
  --name monthly-backup \
  --database prod \
  --retention 365
```

#### 3. Test Restores Regularly

```bash
# ✅ GOOD: Test restore monthly
ai-shell backup restore latest-backup --dry-run
ai-shell backup verify latest-backup --deep --test

# Better: Automated restore testing
ai-shell backup verify latest-backup --test --email admin@example.com
```

#### 4. Document Recovery Procedures

Create `/docs/DISASTER_RECOVERY.md`:

```markdown
# Disaster Recovery Procedure

## Restore from Backup

1. List available backups:
   ai-shell backup list --database prod

2. Verify backup integrity:
   ai-shell backup verify <backup-id> --deep

3. Test restore:
   ai-shell backup restore <backup-id> --dry-run

4. Perform actual restore:
   ai-shell backup restore <backup-id> --verify

## Emergency Contacts
- DBA: John Doe (john@example.com)
- SysAdmin: Jane Smith (jane@example.com)
```

---

### Monitoring Best Practices

#### 1. Set Up Alerts

```bash
# Configure alert thresholds
ai-shell alerts setup
# Follow prompts to set:
# - Slow query threshold: 1000ms
# - CPU threshold: 80%
# - Memory threshold: 90%
# - Error rate threshold: 5%

# Test alerts
ai-shell alerts test
```

#### 2. Regular Performance Reviews

```bash
# Weekly performance review
ai-shell performance report 7d --export weekly-report.json

# Identify trends
ai-shell slow-queries --last 7d
ai-shell indexes analyze
```

#### 3. Dashboard Monitoring

```bash
# Start monitoring dashboard
ai-shell dashboard --port 3000

# Access at http://localhost:3000
```

---

### Development vs Production

#### Development Environment

```bash
# Relaxed settings for development
ai-shell config set auto_optimize true
ai-shell config set slow_query_threshold 100
ai-shell config set verbose true
```

#### Production Environment

```bash
# Strict settings for production
ai-shell config set auto_optimize false # Manual approval required
ai-shell config set slow_query_threshold 1000
ai-shell config set verbose false
ai-shell config set audit_log true
ai-shell config set backup_schedule "0 2 * * *"
ai-shell config set ssl true
```

---

## Conclusion

This guide covered comprehensive database administration with AI-Shell:

- ✅ **Quick Setup**: Docker containers for all databases
- ✅ **Connection Management**: Connect, switch, monitor connections
- ✅ **Query Operations**: CRUD operations with safety checks
- ✅ **Optimization**: Analyze and fix slow queries
- ✅ **Schema Management**: Create, alter, drop tables/indexes
- ✅ **Backup & Recovery**: Complete disaster recovery workflows
- ✅ **Performance Monitoring**: Real-time metrics and alerts
- ✅ **Security**: Permissions, auditing, best practices

### Next Steps

1. **Read the main documentation**: `/docs/README.md`
2. **Try advanced features**: Multi-database queries, AI-powered optimization
3. **Join the community**: GitHub Discussions
4. **Report issues**: GitHub Issues

### Additional Resources

- **Official Docs**: https://github.com/your-org/aishell/docs
- **Video Tutorials**: https://youtube.com/aishell-tutorials
- **Community Forum**: https://community.aishell.io
- **API Reference**: https://api-docs.aishell.io

---

**Happy Database Administration! 🚀**

*Last Updated: 2025-01-15*
*Version: 1.0.0*
