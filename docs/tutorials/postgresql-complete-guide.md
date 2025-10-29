# PostgreSQL Complete Guide

A comprehensive tutorial for PostgreSQL database management, from basics to advanced topics.

**Estimated Time:** 6-8 hours
**Prerequisites:** Basic SQL knowledge, Docker installed

---

## Table of Contents

1. [Setup and Installation](#1-setup-and-installation)
2. [Connection Management](#2-connection-management)
3. [Database and Schema Operations](#3-database-and-schema-operations)
4. [Basic Queries](#4-basic-queries)
5. [Advanced Queries](#5-advanced-queries)
6. [Indexing Strategies](#6-indexing-strategies)
7. [Performance Tuning](#7-performance-tuning)
8. [Backup and Restore](#8-backup-and-restore)
9. [Monitoring and Maintenance](#9-monitoring-and-maintenance)
10. [Security Best Practices](#10-security-best-practices)
11. [Real-World Scenarios](#11-real-world-scenarios)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Setup and Installation

**Time:** 20 minutes

### 1.1 Docker Setup

```bash
# Pull PostgreSQL image
docker pull postgres:16

# Run PostgreSQL container
docker run -d \
  --name my-postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_DB=mydb \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16

# Verify container is running
docker ps | grep postgres
```

### 1.2 Connect to PostgreSQL

```bash
# Using docker exec
docker exec -it my-postgres psql -U myuser -d mydb

# Using AIShell
aishell postgres connect --host localhost --port 5432 --user myuser --database mydb
```

### 1.3 Initial Configuration

```sql
-- Check PostgreSQL version
SELECT version();

-- Show current database
SELECT current_database();

-- List all databases
\l

-- Show server settings
SHOW ALL;

-- Set timezone
SET timezone = 'UTC';
```

**Expected Output:**
```
PostgreSQL 16.x on x86_64-pc-linux-gnu, compiled by gcc
```

**Exercise 1.1:** Set up a PostgreSQL container with custom configuration
- Use port 5433 instead of 5432
- Set max_connections to 200
- Enable logging

<details>
<summary>Solution</summary>

```bash
docker run -d \
  --name postgres-custom \
  -e POSTGRES_PASSWORD=password \
  -p 5433:5432 \
  -v pgdata2:/var/lib/postgresql/data \
  postgres:16 \
  -c max_connections=200 \
  -c log_statement=all
```
</details>

---

## 2. Connection Management

**Time:** 30 minutes

### 2.1 Connection Pooling

```sql
-- View current connections
SELECT
  pid,
  usename,
  application_name,
  client_addr,
  state,
  query_start,
  query
FROM pg_stat_activity
WHERE datname = 'mydb';

-- Terminate idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND query_start < NOW() - INTERVAL '30 minutes';

-- Set connection limits
ALTER DATABASE mydb CONNECTION LIMIT 100;
```

### 2.2 Session Variables

```sql
-- Set session variables
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';

-- Show current settings
SHOW work_mem;
SHOW maintenance_work_mem;

-- Reset to default
RESET work_mem;
```

**Exercise 2.1:** Monitor and manage connections
- Find all connections from a specific IP
- Terminate long-running queries (>5 minutes)
- Count connections per database

<details>
<summary>Solution</summary>

```sql
-- Find connections from specific IP
SELECT * FROM pg_stat_activity
WHERE client_addr = '192.168.1.100';

-- Terminate long-running queries
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < NOW() - INTERVAL '5 minutes';

-- Count connections per database
SELECT datname, COUNT(*) as connection_count
FROM pg_stat_activity
GROUP BY datname
ORDER BY connection_count DESC;
```
</details>

---

## 3. Database and Schema Operations

**Time:** 45 minutes

### 3.1 Database Management

```sql
-- Create database with specific encoding
CREATE DATABASE ecommerce
  ENCODING 'UTF8'
  LC_COLLATE 'en_US.UTF-8'
  LC_CTYPE 'en_US.UTF-8'
  TEMPLATE template0;

-- List databases with details
SELECT
  datname,
  pg_size_pretty(pg_database_size(datname)) as size,
  datcollate,
  datctype
FROM pg_database;

-- Drop database (if exists)
DROP DATABASE IF EXISTS test_db;
```

### 3.2 Schema Management

```sql
-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS sales;
CREATE SCHEMA IF NOT EXISTS inventory;
CREATE SCHEMA IF NOT EXISTS analytics;

-- List schemas
\dn+

-- Set search path
SET search_path TO sales, public;

-- Show current search path
SHOW search_path;

-- Grant schema permissions
GRANT USAGE ON SCHEMA sales TO myuser;
GRANT CREATE ON SCHEMA sales TO myuser;
```

### 3.3 Table Creation with Best Practices

```sql
-- Create customers table
CREATE TABLE sales.customers (
  customer_id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  phone VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Add table comment
COMMENT ON TABLE sales.customers IS 'Customer master data';

-- Create orders table with foreign key
CREATE TABLE sales.orders (
  order_id SERIAL PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES sales.customers(customer_id) ON DELETE CASCADE,
  order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  total_amount NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
  shipping_address TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on foreign key
CREATE INDEX idx_orders_customer_id ON sales.orders(customer_id);
CREATE INDEX idx_orders_order_date ON sales.orders(order_date);
```

**Exercise 3.1:** Create a complete schema
- Create a blog schema
- Create tables: users, posts, comments, tags
- Add appropriate constraints and indexes
- Insert sample data

<details>
<summary>Solution</summary>

```sql
CREATE SCHEMA blog;

CREATE TABLE blog.users (
  user_id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE blog.posts (
  post_id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES blog.users(user_id),
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  published_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE blog.comments (
  comment_id SERIAL PRIMARY KEY,
  post_id INTEGER NOT NULL REFERENCES blog.posts(post_id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES blog.users(user_id),
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE blog.tags (
  tag_id SERIAL PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE blog.post_tags (
  post_id INTEGER REFERENCES blog.posts(post_id) ON DELETE CASCADE,
  tag_id INTEGER REFERENCES blog.tags(tag_id) ON DELETE CASCADE,
  PRIMARY KEY (post_id, tag_id)
);

-- Indexes
CREATE INDEX idx_posts_user_id ON blog.posts(user_id);
CREATE INDEX idx_posts_published_at ON blog.posts(published_at);
CREATE INDEX idx_comments_post_id ON blog.comments(post_id);

-- Sample data
INSERT INTO blog.users (username, email, password_hash) VALUES
  ('john_doe', 'john@example.com', 'hashed_password_1'),
  ('jane_smith', 'jane@example.com', 'hashed_password_2');
```
</details>

---

## 4. Basic Queries

**Time:** 45 minutes

### 4.1 CRUD Operations

```sql
-- Insert single row
INSERT INTO sales.customers (email, first_name, last_name, phone)
VALUES ('john@example.com', 'John', 'Doe', '+1234567890');

-- Insert multiple rows
INSERT INTO sales.customers (email, first_name, last_name) VALUES
  ('alice@example.com', 'Alice', 'Johnson'),
  ('bob@example.com', 'Bob', 'Smith'),
  ('carol@example.com', 'Carol', 'Williams')
RETURNING customer_id, email;

-- Update with conditions
UPDATE sales.customers
SET phone = '+9876543210', updated_at = CURRENT_TIMESTAMP
WHERE email = 'john@example.com';

-- Upsert (INSERT ON CONFLICT)
INSERT INTO sales.customers (email, first_name, last_name)
VALUES ('john@example.com', 'John', 'Doe')
ON CONFLICT (email) DO UPDATE
SET first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    updated_at = CURRENT_TIMESTAMP;

-- Delete with conditions
DELETE FROM sales.customers
WHERE is_active = false
  AND created_at < NOW() - INTERVAL '1 year';
```

### 4.2 Querying Data

```sql
-- Select with filtering
SELECT customer_id, email, first_name, last_name
FROM sales.customers
WHERE is_active = true
  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY created_at DESC
LIMIT 10;

-- Pattern matching
SELECT * FROM sales.customers
WHERE email LIKE '%@gmail.com'
   OR first_name ILIKE 'john%';

-- IN clause
SELECT * FROM sales.customers
WHERE customer_id IN (1, 2, 3, 5, 8);

-- BETWEEN
SELECT * FROM sales.orders
WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31'
  AND total_amount BETWEEN 100 AND 1000;
```

### 4.3 Aggregations

```sql
-- Basic aggregations
SELECT
  COUNT(*) as total_customers,
  COUNT(phone) as customers_with_phone,
  COUNT(DISTINCT SUBSTRING(email FROM POSITION('@' IN email) + 1)) as unique_domains
FROM sales.customers;

-- Group by with HAVING
SELECT
  DATE_TRUNC('month', order_date) as month,
  status,
  COUNT(*) as order_count,
  SUM(total_amount) as total_revenue,
  AVG(total_amount) as avg_order_value,
  MIN(total_amount) as min_order,
  MAX(total_amount) as max_order
FROM sales.orders
GROUP BY DATE_TRUNC('month', order_date), status
HAVING SUM(total_amount) > 1000
ORDER BY month DESC, status;
```

**Exercise 4.1:** Complex query challenge
- Find top 5 customers by order count
- Calculate their total spending
- Show average order value
- Include only customers with >3 orders

<details>
<summary>Solution</summary>

```sql
SELECT
  c.customer_id,
  c.email,
  c.first_name || ' ' || c.last_name as full_name,
  COUNT(o.order_id) as order_count,
  SUM(o.total_amount) as total_spent,
  AVG(o.total_amount) as avg_order_value,
  MIN(o.order_date) as first_order_date,
  MAX(o.order_date) as last_order_date
FROM sales.customers c
JOIN sales.orders o ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
GROUP BY c.customer_id, c.email, c.first_name, c.last_name
HAVING COUNT(o.order_id) > 3
ORDER BY total_spent DESC
LIMIT 5;
```
</details>

---

## 5. Advanced Queries

**Time:** 90 minutes

### 5.1 Common Table Expressions (CTEs)

```sql
-- Simple CTE
WITH recent_customers AS (
  SELECT customer_id, email, first_name, last_name
  FROM sales.customers
  WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT
  rc.email,
  COUNT(o.order_id) as order_count,
  SUM(o.total_amount) as total_spent
FROM recent_customers rc
LEFT JOIN sales.orders o ON rc.customer_id = o.customer_id
GROUP BY rc.customer_id, rc.email;

-- Multiple CTEs
WITH monthly_revenue AS (
  SELECT
    DATE_TRUNC('month', order_date) as month,
    SUM(total_amount) as revenue
  FROM sales.orders
  WHERE status = 'completed'
  GROUP BY DATE_TRUNC('month', order_date)
),
monthly_customers AS (
  SELECT
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as new_customers
  FROM sales.customers
  GROUP BY DATE_TRUNC('month', created_at)
)
SELECT
  mr.month,
  mr.revenue,
  mc.new_customers,
  mr.revenue / NULLIF(mc.new_customers, 0) as revenue_per_new_customer
FROM monthly_revenue mr
LEFT JOIN monthly_customers mc ON mr.month = mc.month
ORDER BY mr.month DESC;

-- Recursive CTE (organizational hierarchy)
CREATE TABLE sales.employees (
  employee_id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  manager_id INTEGER REFERENCES sales.employees(employee_id)
);

WITH RECURSIVE employee_hierarchy AS (
  -- Base case: top-level managers
  SELECT employee_id, name, manager_id, 1 as level, name as path
  FROM sales.employees
  WHERE manager_id IS NULL

  UNION ALL

  -- Recursive case: employees with managers
  SELECT e.employee_id, e.name, e.manager_id, eh.level + 1,
         eh.path || ' > ' || e.name
  FROM sales.employees e
  JOIN employee_hierarchy eh ON e.manager_id = eh.employee_id
)
SELECT * FROM employee_hierarchy ORDER BY level, name;
```

### 5.2 Window Functions

```sql
-- Ranking functions
SELECT
  customer_id,
  order_id,
  order_date,
  total_amount,
  ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) as order_number,
  RANK() OVER (PARTITION BY customer_id ORDER BY total_amount DESC) as amount_rank,
  DENSE_RANK() OVER (ORDER BY total_amount DESC) as dense_rank
FROM sales.orders;

-- Aggregate window functions
SELECT
  order_id,
  customer_id,
  order_date,
  total_amount,
  SUM(total_amount) OVER (PARTITION BY customer_id ORDER BY order_date) as running_total,
  AVG(total_amount) OVER (PARTITION BY customer_id) as customer_avg,
  total_amount - AVG(total_amount) OVER (PARTITION BY customer_id) as deviation_from_avg
FROM sales.orders;

-- Lead and Lag
SELECT
  customer_id,
  order_date,
  total_amount,
  LAG(total_amount) OVER (PARTITION BY customer_id ORDER BY order_date) as previous_order_amount,
  LEAD(total_amount) OVER (PARTITION BY customer_id ORDER BY order_date) as next_order_amount,
  order_date - LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) as days_since_last_order
FROM sales.orders;

-- NTILE for quartiles
SELECT
  customer_id,
  total_amount,
  NTILE(4) OVER (ORDER BY total_amount) as quartile
FROM sales.orders;
```

### 5.3 JSON Operations

```sql
-- Insert JSON data
UPDATE sales.customers
SET metadata = jsonb_build_object(
  'preferences', jsonb_build_object('newsletter', true, 'sms', false),
  'loyalty_points', 150,
  'tags', jsonb_build_array('vip', 'early_adopter')
)
WHERE customer_id = 1;

-- Query JSON fields
SELECT
  customer_id,
  email,
  metadata->>'loyalty_points' as loyalty_points,
  metadata->'preferences'->>'newsletter' as newsletter_subscribed
FROM sales.customers
WHERE metadata @> '{"preferences": {"newsletter": true}}';

-- JSON aggregation
SELECT
  status,
  jsonb_agg(
    jsonb_build_object(
      'order_id', order_id,
      'total', total_amount,
      'date', order_date
    )
  ) as orders
FROM sales.orders
GROUP BY status;

-- JSON array operations
SELECT
  customer_id,
  metadata->'tags' as tags
FROM sales.customers
WHERE metadata->'tags' @> '"vip"';
```

**Exercise 5.1:** Advanced analytics query
- Calculate customer lifetime value (CLV)
- Segment customers into quartiles
- Calculate retention rate by cohort
- Use CTEs and window functions

<details>
<summary>Solution</summary>

```sql
WITH customer_metrics AS (
  SELECT
    c.customer_id,
    c.email,
    DATE_TRUNC('month', c.created_at) as cohort_month,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as lifetime_value,
    MIN(o.order_date) as first_order_date,
    MAX(o.order_date) as last_order_date,
    AVG(o.total_amount) as avg_order_value
  FROM sales.customers c
  LEFT JOIN sales.orders o ON c.customer_id = o.customer_id AND o.status = 'completed'
  GROUP BY c.customer_id, c.email, DATE_TRUNC('month', c.created_at)
),
segmented_customers AS (
  SELECT
    *,
    NTILE(4) OVER (ORDER BY lifetime_value DESC) as value_quartile,
    CASE
      WHEN last_order_date >= CURRENT_DATE - INTERVAL '30 days' THEN 'active'
      WHEN last_order_date >= CURRENT_DATE - INTERVAL '90 days' THEN 'at_risk'
      ELSE 'churned'
    END as status
  FROM customer_metrics
)
SELECT
  cohort_month,
  value_quartile,
  status,
  COUNT(*) as customer_count,
  AVG(lifetime_value) as avg_clv,
  AVG(total_orders) as avg_orders,
  AVG(avg_order_value) as avg_order_value
FROM segmented_customers
GROUP BY cohort_month, value_quartile, status
ORDER BY cohort_month DESC, value_quartile;
```
</details>

---

## 6. Indexing Strategies

**Time:** 60 minutes

### 6.1 Index Types

```sql
-- B-tree index (default)
CREATE INDEX idx_customers_email ON sales.customers(email);

-- Partial index
CREATE INDEX idx_active_customers ON sales.customers(email)
WHERE is_active = true;

-- Composite index
CREATE INDEX idx_orders_customer_date ON sales.orders(customer_id, order_date DESC);

-- Expression index
CREATE INDEX idx_customers_email_lower ON sales.customers(LOWER(email));

-- GIN index for JSONB
CREATE INDEX idx_customers_metadata ON sales.customers USING GIN(metadata);

-- GiST index for full-text search
CREATE INDEX idx_customers_fulltext ON sales.customers
USING GiST(to_tsvector('english', first_name || ' ' || last_name || ' ' || email));
```

### 6.2 Index Analysis

```sql
-- List all indexes
SELECT
  schemaname,
  tablename,
  indexname,
  indexdef,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_indexes
WHERE schemaname = 'sales'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Find unused indexes
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as scans,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'sales'
  AND idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- Find missing indexes
SELECT
  schemaname,
  tablename,
  seq_scan,
  seq_tup_read,
  idx_scan,
  seq_tup_read / NULLIF(seq_scan, 0) as avg_seq_read
FROM pg_stat_user_tables
WHERE schemaname = 'sales'
  AND seq_scan > 0
ORDER BY seq_scan DESC;
```

### 6.3 Index Maintenance

```sql
-- Reindex specific index
REINDEX INDEX idx_customers_email;

-- Reindex table
REINDEX TABLE sales.customers;

-- Check index bloat
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as size,
  ROUND(100 * pg_relation_size(indexrelid) / NULLIF(pg_relation_size(tablename::regclass), 0), 2) as index_ratio
FROM pg_stat_user_indexes
WHERE schemaname = 'sales'
ORDER BY pg_relation_size(indexrelid) DESC;
```

**Exercise 6.1:** Index optimization
- Create appropriate indexes for a query workload
- Identify and remove unused indexes
- Optimize a slow query using indexes

<details>
<summary>Solution</summary>

```sql
-- Analyze slow query
EXPLAIN ANALYZE
SELECT c.email, COUNT(o.order_id), SUM(o.total_amount)
FROM sales.customers c
JOIN sales.orders o ON c.customer_id = o.customer_id
WHERE c.is_active = true
  AND o.order_date >= CURRENT_DATE - INTERVAL '30 days'
  AND o.status = 'completed'
GROUP BY c.email;

-- Create optimized indexes
CREATE INDEX idx_orders_date_status ON sales.orders(order_date, status)
WHERE status = 'completed';

CREATE INDEX idx_active_customers_id ON sales.customers(customer_id)
WHERE is_active = true;

-- Remove unused indexes
DROP INDEX IF EXISTS idx_unused_index;

-- Verify improvement
EXPLAIN ANALYZE
SELECT c.email, COUNT(o.order_id), SUM(o.total_amount)
FROM sales.customers c
JOIN sales.orders o ON c.customer_id = o.customer_id
WHERE c.is_active = true
  AND o.order_date >= CURRENT_DATE - INTERVAL '30 days'
  AND o.status = 'completed'
GROUP BY c.email;
```
</details>

---

## 7. Performance Tuning

**Time:** 90 minutes

### 7.1 Query Analysis with EXPLAIN

```sql
-- Basic EXPLAIN
EXPLAIN
SELECT * FROM sales.orders WHERE customer_id = 1;

-- EXPLAIN ANALYZE (actually runs the query)
EXPLAIN ANALYZE
SELECT
  c.email,
  COUNT(o.order_id) as order_count,
  SUM(o.total_amount) as total_spent
FROM sales.customers c
LEFT JOIN sales.orders o ON c.customer_id = o.customer_id
WHERE c.created_at >= '2024-01-01'
GROUP BY c.email;

-- EXPLAIN with detailed options
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, COSTS)
SELECT * FROM sales.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '7 days';
```

**Understanding EXPLAIN output:**
- **Seq Scan**: Full table scan (slow for large tables)
- **Index Scan**: Using an index (fast)
- **Index Only Scan**: Using only the index (fastest)
- **Nested Loop**: Good for small datasets
- **Hash Join**: Good for medium datasets
- **Merge Join**: Good for large sorted datasets
- **cost=X..Y**: Startup cost..total cost
- **rows=N**: Estimated number of rows

### 7.2 Vacuum and Analyze

```sql
-- Analyze table statistics
ANALYZE sales.customers;
ANALYZE sales.orders;

-- Vacuum to reclaim space
VACUUM sales.customers;

-- Vacuum with analyze
VACUUM ANALYZE sales.orders;

-- Full vacuum (locks table)
VACUUM FULL sales.customers;

-- Auto-vacuum settings
ALTER TABLE sales.orders SET (
  autovacuum_vacuum_scale_factor = 0.1,
  autovacuum_analyze_scale_factor = 0.05
);

-- Check vacuum progress
SELECT
  schemaname,
  tablename,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze,
  n_dead_tup,
  n_live_tup
FROM pg_stat_user_tables
WHERE schemaname = 'sales';
```

### 7.3 Query Optimization Techniques

```sql
-- Use EXISTS instead of IN for large subqueries
-- SLOW
SELECT * FROM sales.customers
WHERE customer_id IN (
  SELECT customer_id FROM sales.orders WHERE total_amount > 1000
);

-- FAST
SELECT * FROM sales.customers c
WHERE EXISTS (
  SELECT 1 FROM sales.orders o
  WHERE o.customer_id = c.customer_id AND o.total_amount > 1000
);

-- Use LIMIT for pagination
SELECT * FROM sales.orders
ORDER BY order_date DESC
LIMIT 20 OFFSET 40;

-- Better: Use keyset pagination
SELECT * FROM sales.orders
WHERE order_id < 12345
ORDER BY order_id DESC
LIMIT 20;

-- Batch updates
UPDATE sales.customers SET is_active = false
WHERE customer_id IN (
  SELECT customer_id FROM sales.orders
  WHERE order_date < CURRENT_DATE - INTERVAL '2 years'
  LIMIT 1000
);
```

### 7.4 Connection Pooling

```sql
-- Check connection pool settings
SHOW max_connections;
SHOW shared_buffers;
SHOW effective_cache_size;
SHOW work_mem;

-- Optimize for web applications
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET work_mem = '50MB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';

-- Reload configuration
SELECT pg_reload_conf();
```

**Exercise 7.1:** Optimize a slow query
- Given a slow query, analyze with EXPLAIN
- Identify bottlenecks
- Add appropriate indexes
- Rewrite query for better performance
- Measure improvement

<details>
<summary>Solution</summary>

```sql
-- Original slow query
EXPLAIN ANALYZE
SELECT
  c.email,
  c.first_name,
  c.last_name,
  o.order_id,
  o.total_amount
FROM sales.customers c
JOIN sales.orders o ON c.customer_id = o.customer_id
WHERE LOWER(c.email) LIKE '%@gmail.com'
  AND o.status = 'completed'
ORDER BY o.order_date DESC;

-- Issues identified:
-- 1. LOWER(email) prevents index usage
-- 2. LIKE with leading wildcard causes full scan
-- 3. Missing index on orders.status

-- Add indexes
CREATE INDEX idx_customers_email_lower ON sales.customers(LOWER(email));
CREATE INDEX idx_orders_status_date ON sales.orders(status, order_date DESC);

-- Optimized query
EXPLAIN ANALYZE
SELECT
  c.email,
  c.first_name,
  c.last_name,
  o.order_id,
  o.total_amount
FROM sales.orders o
JOIN sales.customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
  AND LOWER(c.email) LIKE '%@gmail.com'
ORDER BY o.order_date DESC
LIMIT 100;

-- Further optimization: Use full-text search for email domains
CREATE INDEX idx_customers_email_domain ON sales.customers(
  SUBSTRING(email FROM POSITION('@' IN email) + 1)
);

SELECT
  c.email,
  c.first_name,
  c.last_name,
  o.order_id,
  o.total_amount
FROM sales.orders o
JOIN sales.customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
  AND SUBSTRING(c.email FROM POSITION('@' IN c.email) + 1) = 'gmail.com'
ORDER BY o.order_date DESC
LIMIT 100;
```
</details>

---

## 8. Backup and Restore

**Time:** 45 minutes

### 8.1 Logical Backups with pg_dump

```bash
# Backup single database
docker exec my-postgres pg_dump -U myuser -d mydb > /tmp/mydb_backup.sql

# Backup with custom format (compressed)
docker exec my-postgres pg_dump -U myuser -Fc -d mydb > /tmp/mydb_backup.dump

# Backup specific schema
docker exec my-postgres pg_dump -U myuser -d mydb -n sales > /tmp/sales_schema.sql

# Backup specific tables
docker exec my-postgres pg_dump -U myuser -d mydb -t sales.customers -t sales.orders > /tmp/tables_backup.sql

# Backup with data only
docker exec my-postgres pg_dump -U myuser -d mydb --data-only > /tmp/data_only.sql

# Backup with schema only
docker exec my-postgres pg_dump -U myuser -d mydb --schema-only > /tmp/schema_only.sql
```

### 8.2 Restore Operations

```bash
# Restore from SQL file
docker exec -i my-postgres psql -U myuser -d mydb < /tmp/mydb_backup.sql

# Restore from custom format
docker exec my-postgres pg_restore -U myuser -d mydb /tmp/mydb_backup.dump

# Restore specific schema
docker exec -i my-postgres psql -U myuser -d mydb < /tmp/sales_schema.sql

# Restore with clean (drop existing objects)
docker exec my-postgres pg_restore -U myuser -d mydb --clean /tmp/mydb_backup.dump

# Parallel restore (faster)
docker exec my-postgres pg_restore -U myuser -d mydb -j 4 /tmp/mydb_backup.dump
```

### 8.3 Automated Backup Script

```bash
#!/bin/bash
# backup-postgres.sh

CONTAINER_NAME="my-postgres"
DB_USER="myuser"
DB_NAME="mydb"
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.dump"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -Fc -d $DB_NAME > $BACKUP_FILE

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
  echo "Backup successful: $BACKUP_FILE"

  # Delete backups older than 7 days
  find $BACKUP_DIR -name "${DB_NAME}_*.dump" -mtime +7 -delete
else
  echo "Backup failed!"
  exit 1
fi
```

### 8.4 Point-in-Time Recovery (PITR)

```sql
-- Enable WAL archiving
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET archive_mode = 'on';
ALTER SYSTEM SET archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f';

-- Take base backup
SELECT pg_start_backup('base_backup');
-- Copy data directory
SELECT pg_stop_backup();

-- Restore to specific point in time
-- Create recovery.conf
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2024-01-15 12:00:00'
recovery_target_action = 'promote'
```

**Exercise 8.1:** Backup and recovery strategy
- Create a backup script with compression
- Test restore to a new database
- Implement retention policy
- Schedule automated backups

<details>
<summary>Solution</summary>

```bash
#!/bin/bash
# comprehensive-backup.sh

CONTAINER="my-postgres"
USER="myuser"
DATABASES=("mydb" "analytics" "reporting")
BACKUP_ROOT="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

for DB in "${DATABASES[@]}"; do
  BACKUP_DIR="$BACKUP_ROOT/$DB"
  mkdir -p $BACKUP_DIR

  BACKUP_FILE="$BACKUP_DIR/${DB}_${TIMESTAMP}.dump"

  echo "Backing up $DB..."
  docker exec $CONTAINER pg_dump -U $USER -Fc -d $DB > $BACKUP_FILE

  if [ -f "$BACKUP_FILE" ]; then
    # Compress backup
    gzip $BACKUP_FILE

    # Calculate size
    SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo "Backup completed: ${BACKUP_FILE}.gz ($SIZE)"

    # Delete old backups
    find $BACKUP_DIR -name "${DB}_*.dump.gz" -mtime +$RETENTION_DAYS -delete
    echo "Cleaned up backups older than $RETENTION_DAYS days"
  else
    echo "Backup failed for $DB!"
  fi
done

# Test restore to temporary database
echo "Testing restore..."
TEST_DB="test_restore_$TIMESTAMP"
docker exec $CONTAINER psql -U $USER -c "CREATE DATABASE $TEST_DB;"
gunzip -c "${BACKUP_FILE}.gz" | docker exec -i $CONTAINER pg_restore -U $USER -d $TEST_DB
docker exec $CONTAINER psql -U $USER -c "DROP DATABASE $TEST_DB;"
echo "Restore test completed successfully"
```

Add to crontab:
```bash
# Run daily at 2 AM
0 2 * * * /path/to/comprehensive-backup.sh >> /var/log/postgres-backup.log 2>&1
```
</details>

---

## 9. Monitoring and Maintenance

**Time:** 60 minutes

### 9.1 System Monitoring

```sql
-- Database size
SELECT
  datname,
  pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
ORDER BY pg_database_size(datname) DESC;

-- Table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables
WHERE schemaname = 'sales'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Cache hit ratio
SELECT
  'cache hit rate' as metric,
  ROUND(sum(blks_hit)::numeric / nullif(sum(blks_hit + blks_read), 0) * 100, 2) as percentage
FROM pg_stat_database;

-- Slow queries
SELECT
  pid,
  now() - query_start as duration,
  query,
  state
FROM pg_stat_activity
WHERE state = 'active'
  AND now() - query_start > interval '5 minutes'
ORDER BY duration DESC;

-- Blocking queries
SELECT
  blocked_locks.pid AS blocked_pid,
  blocked_activity.usename AS blocked_user,
  blocking_locks.pid AS blocking_pid,
  blocking_activity.usename AS blocking_user,
  blocked_activity.query AS blocked_statement,
  blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
  ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

### 9.2 Performance Statistics

```sql
-- Most frequently executed queries
SELECT
  query,
  calls,
  total_exec_time,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
ORDER BY calls DESC
LIMIT 10;

-- Slowest queries
SELECT
  query,
  calls,
  total_exec_time,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Table I/O statistics
SELECT
  schemaname,
  tablename,
  heap_blks_read,
  heap_blks_hit,
  idx_blks_read,
  idx_blks_hit,
  ROUND(100.0 * heap_blks_hit / NULLIF(heap_blks_hit + heap_blks_read, 0), 2) as cache_hit_ratio
FROM pg_statio_user_tables
WHERE schemaname = 'sales'
ORDER BY heap_blks_read DESC;
```

### 9.3 Maintenance Tasks

```sql
-- Reindex all indexes in a schema
REINDEX SCHEMA sales;

-- Update statistics
ANALYZE;

-- Vacuum all tables
VACUUM ANALYZE;

-- Check for table bloat
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
  n_dead_tup,
  n_live_tup,
  ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_tuple_percent
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;

-- Find duplicate indexes
SELECT
  pg_size_pretty(SUM(pg_relation_size(idx))::BIGINT) AS size,
  (array_agg(idx))[1] AS idx1,
  (array_agg(idx))[2] AS idx2,
  (array_agg(idx))[3] AS idx3,
  (array_agg(idx))[4] AS idx4
FROM (
  SELECT
    indexrelid::regclass AS idx,
    (indrelid::text ||E'\n'|| indclass::text ||E'\n'|| indkey::text ||E'\n'|| COALESCE(indexprs::text,'')||E'\n' || COALESCE(indpred::text,'')) AS KEY
  FROM pg_index
) sub
GROUP BY KEY
HAVING COUNT(*) > 1
ORDER BY SUM(pg_relation_size(idx)) DESC;
```

**Exercise 9.1:** Create a monitoring dashboard
- Query for database health metrics
- Identify performance bottlenecks
- Create alerts for critical conditions

<details>
<summary>Solution</summary>

```sql
-- Comprehensive monitoring query
WITH database_stats AS (
  SELECT
    datname,
    pg_size_pretty(pg_database_size(datname)) as size,
    numbackends as connections,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    ROUND(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2) as cache_hit_ratio
  FROM pg_stat_database
  WHERE datname = 'mydb'
),
connection_stats AS (
  SELECT
    state,
    COUNT(*) as count
  FROM pg_stat_activity
  GROUP BY state
),
slow_queries AS (
  SELECT
    COUNT(*) as slow_query_count
  FROM pg_stat_activity
  WHERE state = 'active'
    AND now() - query_start > interval '1 minute'
),
table_stats AS (
  SELECT
    SUM(n_dead_tup) as total_dead_tuples,
    SUM(seq_scan) as total_seq_scans
  FROM pg_stat_user_tables
),
alerts AS (
  SELECT
    CASE
      WHEN (SELECT cache_hit_ratio FROM database_stats) < 90 THEN 'WARNING: Cache hit ratio below 90%'
      WHEN (SELECT slow_query_count FROM slow_queries) > 5 THEN 'WARNING: More than 5 slow queries'
      WHEN (SELECT total_dead_tuples FROM table_stats) > 100000 THEN 'WARNING: High dead tuple count - run VACUUM'
      ELSE 'OK'
    END as alert_message
)
SELECT
  'Database Health Report' as report,
  d.datname,
  d.size,
  d.connections,
  d.cache_hit_ratio,
  c.count as active_connections,
  s.slow_query_count,
  t.total_dead_tuples,
  a.alert_message
FROM database_stats d
CROSS JOIN connection_stats c
CROSS JOIN slow_queries s
CROSS JOIN table_stats t
CROSS JOIN alerts a
WHERE c.state = 'active';
```
</details>

---

## 10. Security Best Practices

**Time:** 45 minutes

### 10.1 User and Role Management

```sql
-- Create roles
CREATE ROLE readonly;
CREATE ROLE readwrite;
CREATE ROLE admin;

-- Grant privileges
GRANT CONNECT ON DATABASE mydb TO readonly;
GRANT USAGE ON SCHEMA sales TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA sales TO readonly;

GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sales TO readwrite;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sales TO readwrite;

-- Create users
CREATE USER analyst WITH PASSWORD 'secure_password';
CREATE USER app_user WITH PASSWORD 'app_password';

-- Assign roles
GRANT readonly TO analyst;
GRANT readwrite TO app_user;

-- Revoke privileges
REVOKE DELETE ON sales.customers FROM readwrite;

-- View permissions
SELECT
  grantee,
  table_schema,
  table_name,
  privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'readonly';
```

### 10.2 Row-Level Security (RLS)

```sql
-- Enable RLS
ALTER TABLE sales.orders ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY customer_isolation ON sales.orders
  FOR ALL
  TO app_user
  USING (customer_id = current_setting('app.current_customer_id')::INTEGER);

-- Create policy for admins
CREATE POLICY admin_all ON sales.orders
  FOR ALL
  TO admin
  USING (true);

-- Set session variable
SET app.current_customer_id = '123';

-- Test RLS
SELECT * FROM sales.orders; -- Will only show orders for customer 123
```

### 10.3 Encryption and Security

```sql
-- Install pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Hash passwords
CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL
);

INSERT INTO users (username, password_hash)
VALUES ('john_doe', crypt('my_password', gen_salt('bf')));

-- Verify password
SELECT username
FROM users
WHERE username = 'john_doe'
  AND password_hash = crypt('my_password', password_hash);

-- Encrypt sensitive data
ALTER TABLE sales.customers ADD COLUMN credit_card_encrypted BYTEA;

UPDATE sales.customers
SET credit_card_encrypted = pgp_sym_encrypt('4111-1111-1111-1111', 'encryption_key')
WHERE customer_id = 1;

-- Decrypt data
SELECT
  customer_id,
  pgp_sym_decrypt(credit_card_encrypted, 'encryption_key') as credit_card
FROM sales.customers
WHERE customer_id = 1;
```

### 10.4 Audit Logging

```sql
-- Create audit table
CREATE TABLE audit.activity_log (
  log_id BIGSERIAL PRIMARY KEY,
  table_name TEXT NOT NULL,
  operation TEXT NOT NULL,
  old_data JSONB,
  new_data JSONB,
  user_name TEXT DEFAULT CURRENT_USER,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit.log_changes()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO audit.activity_log (table_name, operation, new_data)
    VALUES (TG_TABLE_NAME, TG_OP, row_to_json(NEW));
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO audit.activity_log (table_name, operation, old_data, new_data)
    VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW));
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO audit.activity_log (table_name, operation, old_data)
    VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD));
    RETURN OLD;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger
CREATE TRIGGER customers_audit
AFTER INSERT OR UPDATE OR DELETE ON sales.customers
FOR EACH ROW EXECUTE FUNCTION audit.log_changes();

-- Query audit log
SELECT * FROM audit.activity_log
WHERE table_name = 'customers'
  AND timestamp >= CURRENT_DATE
ORDER BY timestamp DESC;
```

**Exercise 10.1:** Implement security controls
- Create role hierarchy
- Implement RLS for multi-tenant application
- Add audit logging
- Encrypt sensitive columns

<details>
<summary>Solution</summary>

```sql
-- Step 1: Create role hierarchy
CREATE ROLE tenant_user;
CREATE ROLE tenant_admin;
CREATE ROLE super_admin;

GRANT tenant_user TO tenant_admin;
GRANT tenant_admin TO super_admin;

-- Step 2: Create multi-tenant table
CREATE TABLE sales.tenant_data (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  data TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 3: Enable RLS
ALTER TABLE sales.tenant_data ENABLE ROW LEVEL SECURITY;

-- Step 4: Create RLS policies
CREATE POLICY tenant_isolation ON sales.tenant_data
  FOR ALL
  TO tenant_user
  USING (tenant_id = current_setting('app.tenant_id')::INTEGER);

CREATE POLICY admin_see_all ON sales.tenant_data
  FOR SELECT
  TO super_admin
  USING (true);

-- Step 5: Create audit schema and table
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE audit.tenant_activity (
  log_id BIGSERIAL PRIMARY KEY,
  tenant_id INTEGER,
  user_name TEXT,
  action TEXT,
  table_name TEXT,
  record_id INTEGER,
  old_data JSONB,
  new_data JSONB,
  ip_address INET,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 6: Audit trigger
CREATE OR REPLACE FUNCTION audit.log_tenant_changes()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO audit.tenant_activity (tenant_id, action, table_name, record_id, new_data)
    VALUES (NEW.tenant_id, TG_OP, TG_TABLE_NAME, NEW.id, row_to_json(NEW));
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO audit.tenant_activity (tenant_id, action, table_name, record_id, old_data, new_data)
    VALUES (NEW.tenant_id, TG_OP, TG_TABLE_NAME, NEW.id, row_to_json(OLD), row_to_json(NEW));
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO audit.tenant_activity (tenant_id, action, table_name, record_id, old_data)
    VALUES (OLD.tenant_id, TG_OP, TG_TABLE_NAME, OLD.id, row_to_json(OLD));
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tenant_data_audit
AFTER INSERT OR UPDATE OR DELETE ON sales.tenant_data
FOR EACH ROW EXECUTE FUNCTION audit.log_tenant_changes();

-- Step 7: Encrypt sensitive columns
CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE sales.tenant_data ADD COLUMN sensitive_data_encrypted BYTEA;

-- Function to encrypt
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data TEXT)
RETURNS BYTEA AS $$
BEGIN
  RETURN pgp_sym_encrypt(data, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted BYTEA)
RETURNS TEXT AS $$
BEGIN
  RETURN pgp_sym_decrypt(encrypted, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Test setup
CREATE USER tenant1_user WITH PASSWORD 'secure_pass1';
GRANT tenant_user TO tenant1_user;

-- Set session context
SET app.tenant_id = 1;
SET app.encryption_key = 'super_secret_key';

-- Insert test data
INSERT INTO sales.tenant_data (tenant_id, data, sensitive_data_encrypted)
VALUES (1, 'Regular data', encrypt_sensitive_data('Sensitive information'));

-- Query as tenant user
SELECT
  id,
  tenant_id,
  data,
  decrypt_sensitive_data(sensitive_data_encrypted) as sensitive_data
FROM sales.tenant_data;
```
</details>

---

## 11. Real-World Scenarios

**Time:** 90 minutes

### Scenario 1: E-commerce Order Processing

```sql
-- Create comprehensive order system
CREATE TABLE sales.products (
  product_id SERIAL PRIMARY KEY,
  sku VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
  stock_quantity INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sales.order_items (
  order_item_id SERIAL PRIMARY KEY,
  order_id INTEGER NOT NULL REFERENCES sales.orders(order_id) ON DELETE CASCADE,
  product_id INTEGER NOT NULL REFERENCES sales.products(product_id),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  unit_price NUMERIC(10, 2) NOT NULL,
  subtotal NUMERIC(10, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- Transaction for order placement
BEGIN;

-- Create order
INSERT INTO sales.orders (customer_id, status, total_amount)
VALUES (1, 'pending', 0)
RETURNING order_id;

-- Add order items
INSERT INTO sales.order_items (order_id, product_id, quantity, unit_price)
VALUES
  (1, 101, 2, 29.99),
  (1, 102, 1, 49.99);

-- Update stock
UPDATE sales.products
SET stock_quantity = stock_quantity - 2
WHERE product_id = 101;

UPDATE sales.products
SET stock_quantity = stock_quantity - 1
WHERE product_id = 102;

-- Update order total
UPDATE sales.orders
SET total_amount = (
  SELECT SUM(subtotal)
  FROM sales.order_items
  WHERE order_id = 1
)
WHERE order_id = 1;

COMMIT;

-- Inventory check function
CREATE OR REPLACE FUNCTION check_inventory()
RETURNS TABLE(product_id INTEGER, sku VARCHAR, name VARCHAR, stock INTEGER, status TEXT) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.product_id,
    p.sku,
    p.name,
    p.stock_quantity,
    CASE
      WHEN p.stock_quantity = 0 THEN 'Out of Stock'
      WHEN p.stock_quantity < 10 THEN 'Low Stock'
      ELSE 'In Stock'
    END as status
  FROM sales.products p
  ORDER BY p.stock_quantity;
END;
$$ LANGUAGE plpgsql;
```

### Scenario 2: User Analytics Dashboard

```sql
-- User engagement metrics
WITH user_cohorts AS (
  SELECT
    c.customer_id,
    DATE_TRUNC('month', c.created_at) as cohort_month,
    DATE_TRUNC('month', o.order_date) as order_month
  FROM sales.customers c
  LEFT JOIN sales.orders o ON c.customer_id = o.customer_id
),
cohort_analysis AS (
  SELECT
    cohort_month,
    order_month,
    COUNT(DISTINCT customer_id) as customers,
    EXTRACT(MONTH FROM AGE(order_month, cohort_month)) as months_since_signup
  FROM user_cohorts
  WHERE order_month IS NOT NULL
  GROUP BY cohort_month, order_month
)
SELECT
  cohort_month,
  months_since_signup,
  customers,
  ROUND(100.0 * customers / FIRST_VALUE(customers) OVER (
    PARTITION BY cohort_month ORDER BY months_since_signup
  ), 2) as retention_percentage
FROM cohort_analysis
ORDER BY cohort_month DESC, months_since_signup;
```

### Scenario 3: Time-Series Analysis

```sql
-- Sales trends and forecasting
CREATE TABLE sales.daily_sales AS
SELECT
  DATE_TRUNC('day', order_date) as date,
  COUNT(*) as order_count,
  SUM(total_amount) as revenue,
  AVG(total_amount) as avg_order_value
FROM sales.orders
WHERE status = 'completed'
GROUP BY DATE_TRUNC('day', order_date);

-- Moving averages
SELECT
  date,
  revenue,
  AVG(revenue) OVER (
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as revenue_7day_ma,
  AVG(revenue) OVER (
    ORDER BY date
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as revenue_30day_ma,
  revenue - LAG(revenue, 7) OVER (ORDER BY date) as week_over_week_change
FROM sales.daily_sales
ORDER BY date DESC;
```

### Scenario 4: Fraud Detection

```sql
-- Detect suspicious patterns
WITH order_velocity AS (
  SELECT
    customer_id,
    COUNT(*) as order_count_1h,
    SUM(total_amount) as total_spent_1h
  FROM sales.orders
  WHERE order_date >= NOW() - INTERVAL '1 hour'
  GROUP BY customer_id
),
high_value_orders AS (
  SELECT
    o.order_id,
    o.customer_id,
    o.total_amount,
    AVG(o2.total_amount) as customer_avg
  FROM sales.orders o
  JOIN sales.orders o2 ON o.customer_id = o2.customer_id AND o2.order_id != o.order_id
  WHERE o.order_date >= NOW() - INTERVAL '24 hours'
  GROUP BY o.order_id, o.customer_id, o.total_amount
  HAVING o.total_amount > AVG(o2.total_amount) * 5
)
SELECT
  c.customer_id,
  c.email,
  ov.order_count_1h,
  ov.total_spent_1h,
  hvo.order_id as suspicious_order,
  hvo.total_amount as order_amount,
  hvo.customer_avg as typical_amount,
  'REVIEW_REQUIRED' as flag
FROM sales.customers c
LEFT JOIN order_velocity ov ON c.customer_id = ov.customer_id
LEFT JOIN high_value_orders hvo ON c.customer_id = hvo.customer_id
WHERE ov.order_count_1h > 5 OR hvo.order_id IS NOT NULL;
```

### Scenario 5: Data Migration

```sql
-- Safe data migration with validation
BEGIN;

-- Create new table structure
CREATE TABLE sales.customers_v2 (
  customer_id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(200) NOT NULL,
  phone VARCHAR(20),
  address JSONB,
  preferences JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migrate data
INSERT INTO sales.customers_v2 (customer_id, email, full_name, phone, created_at)
SELECT
  customer_id,
  LOWER(TRIM(email)),
  first_name || ' ' || last_name,
  phone,
  created_at
FROM sales.customers
WHERE is_active = true;

-- Validate migration
SELECT
  'Source count' as metric,
  COUNT(*) as value
FROM sales.customers
WHERE is_active = true
UNION ALL
SELECT
  'Target count',
  COUNT(*)
FROM sales.customers_v2;

-- If validation passes
-- COMMIT;
-- DROP TABLE sales.customers;
-- ALTER TABLE sales.customers_v2 RENAME TO customers;

ROLLBACK; -- For safety in this example
```

---

## 12. Troubleshooting

### Common Issues and Solutions

#### Issue 1: Slow Queries

**Symptoms:** Queries taking too long to execute

**Diagnosis:**
```sql
-- Find slow queries
SELECT
  pid,
  now() - query_start as duration,
  query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

-- Analyze query plan
EXPLAIN ANALYZE your_slow_query;
```

**Solutions:**
- Add appropriate indexes
- Update table statistics with ANALYZE
- Rewrite query to avoid full table scans
- Consider partitioning large tables

#### Issue 2: High Memory Usage

**Symptoms:** Out of memory errors

**Diagnosis:**
```sql
-- Check memory settings
SHOW shared_buffers;
SHOW work_mem;
SHOW maintenance_work_mem;

-- Find memory-intensive queries
SELECT * FROM pg_stat_statements
ORDER BY temp_blks_written DESC;
```

**Solutions:**
- Reduce work_mem for specific queries
- Add LIMIT clauses where appropriate
- Use cursors for large result sets
- Optimize joins and aggregations

#### Issue 3: Deadlocks

**Symptoms:** Deadlock detected errors

**Diagnosis:**
```sql
-- Enable deadlock logging
ALTER SYSTEM SET log_lock_waits = on;
ALTER SYSTEM SET deadlock_timeout = '1s';
SELECT pg_reload_conf();

-- View locks
SELECT * FROM pg_locks
WHERE NOT granted;
```

**Solutions:**
- Always access tables in the same order
- Keep transactions short
- Use appropriate isolation levels
- Consider LOCK TABLE with NOWAIT

#### Issue 4: Connection Exhaustion

**Symptoms:** "too many clients" errors

**Diagnosis:**
```sql
-- Check current connections
SELECT COUNT(*) FROM pg_stat_activity;

-- Find idle connections
SELECT * FROM pg_stat_activity
WHERE state = 'idle'
ORDER BY state_change;
```

**Solutions:**
- Implement connection pooling (PgBouncer)
- Increase max_connections if needed
- Kill idle connections
- Fix application connection leaks

---

## Further Reading

### Official Documentation
- [PostgreSQL Manual](https://www.postgresql.org/docs/)
- [Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Security Guide](https://www.postgresql.org/docs/current/security.html)

### Books
- "PostgreSQL: Up and Running" by Regina Obe
- "The Art of PostgreSQL" by Dimitri Fontaine
- "PostgreSQL Query Optimization" by Henrietta Dombrovskaya

### Tools
- pgAdmin - GUI administration tool
- pg_stat_statements - Query statistics
- pgBadger - Log analyzer
- pg_top - Real-time monitoring

### Community
- [PostgreSQL Mailing Lists](https://www.postgresql.org/list/)
- [Stack Overflow PostgreSQL Tag](https://stackoverflow.com/questions/tagged/postgresql)
- [Reddit r/PostgreSQL](https://www.reddit.com/r/PostgreSQL/)

---

## Conclusion

You've completed the PostgreSQL Complete Guide! You should now be able to:

✅ Set up and configure PostgreSQL databases
✅ Write efficient SQL queries with CTEs and window functions
✅ Optimize performance with proper indexing
✅ Implement backup and recovery strategies
✅ Monitor database health and performance
✅ Apply security best practices
✅ Troubleshoot common issues

**Next Steps:**
1. Practice with real-world datasets
2. Explore PostgreSQL extensions (PostGIS, TimescaleDB)
3. Learn about replication and high availability
4. Study advanced topics like partitioning and sharding

Happy querying! 🐘
