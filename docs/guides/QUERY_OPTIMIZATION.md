# Query Optimization Guide

## Table of Contents

1. [Overview](#overview)
2. [Using the Optimize Command](#using-the-optimize-command)
3. [Understanding Slow Queries](#understanding-slow-queries)
4. [Index Management](#index-management)
5. [Natural Language to SQL](#natural-language-to-sql)
6. [Risk Checking](#risk-checking)
7. [Query Analysis](#query-analysis)
8. [Performance Tuning](#performance-tuning)
9. [Best Practices](#best-practices)

---

## Overview

Query optimization is critical for maintaining database performance. AI-Shell provides AI-powered tools to analyze, optimize, and improve your database queries automatically.

### Optimization Workflow

```
┌──────────────────────────────────────────────────────────────┐
│                  Query Optimization Workflow                 │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │   1. Identify Slow Queries    │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │   2. Analyze Query Plans      │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │   3. Get AI Recommendations   │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │   4. Check Risk Level         │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │   5. Apply Optimizations      │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │   6. Verify Improvement       │
            └───────────────────────────────┘
```

---

## Using the Optimize Command

### Basic Optimization

```bash
# Analyze and optimize a query
aishell optimize suggest prod-db \
  --sql "SELECT * FROM orders WHERE user_id = 123"

# Example output:
# ✓ Query analyzed
#
# Performance Issues Found:
# 1. Missing index on orders(user_id)
# 2. SELECT * returns unnecessary columns
# 3. No LIMIT clause for large result sets
#
# Recommendations:
# 1. Create index: CREATE INDEX idx_orders_user_id ON orders(user_id)
# 2. Specify columns: SELECT id, total, created_at FROM orders
# 3. Add LIMIT: ... LIMIT 100
#
# Estimated Improvement: 87% faster
```

### Comprehensive Analysis

```bash
# Deep analysis with all optimizations
aishell optimize analyze prod-db \
  --sql "SELECT * FROM orders WHERE user_id = 123" \
  --explain \
  --suggest-indexes \
  --rewrite \
  --estimate-cost

# Output includes:
# - Execution plan
# - Index recommendations
# - Query rewrite suggestions
# - Cost estimates (before/after)
# - Memory usage
# - I/O operations
```

### Automatic Query Rewriting

```bash
# Get optimized version of query
aishell optimize rewrite prod-db \
  --sql "
    SELECT *
    FROM orders o, users u, products p
    WHERE o.user_id = u.id
    AND o.product_id = p.id
    AND o.created_at > '2024-01-01'
  "

# AI-optimized output:
# SELECT
#   o.id,
#   o.total,
#   o.created_at,
#   u.name as user_name,
#   p.name as product_name
# FROM orders o
# INNER JOIN users u ON o.user_id = u.id
# INNER JOIN products p ON o.product_id = p.id
# WHERE o.created_at > '2024-01-01'::timestamp
# AND o.created_at < CURRENT_DATE  -- Prevents full table scan
# LIMIT 1000  -- Safety limit
```

---

## Understanding Slow Queries

### Finding Slow Queries

#### PostgreSQL

```bash
# Find slow queries (>1 second)
aishell optimize slow-queries prod-db \
  --threshold 1000ms \
  --limit 20

# Output format:
# Query                          | Avg Time | Calls | Total Time | % Total
# -------------------------------|----------|-------|------------|--------
# SELECT * FROM orders WHERE...  | 2.5s     | 1,234 | 51m 25s    | 45%
# UPDATE users SET last_login... | 850ms    | 5,678 | 80m 23s    | 35%

# Get detailed slow query report
aishell optimize slow-queries prod-db \
  --threshold 500ms \
  --period 24h \
  --format detailed \
  --output slow-queries-report.json
```

#### MySQL

```bash
# Enable slow query log
aishell query run mysql-prod --sql "
  SET GLOBAL slow_query_log = 'ON';
  SET GLOBAL long_query_time = 1;
  SET GLOBAL slow_query_log_file = '/var/log/mysql/slow-query.log';
"

# Analyze slow query log
aishell optimize analyze-slow-log mysql-prod \
  --log-file /var/log/mysql/slow-query.log \
  --top 10

# Use pt-query-digest integration
aishell optimize digest mysql-prod \
  --tool pt-query-digest \
  --output digest-report.txt
```

#### MongoDB

```bash
# Find slow operations
aishell optimize slow-queries mongo-prod \
  --threshold 100ms \
  --collection orders

# Profile slow queries
aishell query run mongo-prod --command '{
  "profile": 2,
  "slowms": 100
}'

# View profiler data
aishell query run mongo-prod \
  --collection system.profile \
  --query '{"millis": {"$gt": 100}}' \
  --sort '{"ts": -1}' \
  --limit 20
```

### Analyzing Query Patterns

```bash
# Identify query patterns
aishell optimize patterns prod-db \
  --period 7d \
  --group-by fingerprint

# Example output:
# Pattern                              | Count  | Avg Time | Total Time
# -------------------------------------|--------|----------|------------
# SELECT ... FROM users WHERE id = ?   | 45,678 | 12ms     | 9m 8s
# SELECT ... FROM orders WHERE user_id | 23,456 | 156ms    | 61m 5s
# UPDATE users SET last_login = ?      | 12,345 | 45ms     | 9m 15s

# Get query fingerprint
aishell optimize fingerprint prod-db \
  --sql "SELECT * FROM users WHERE id = 123"

# Output: SELECT * FROM users WHERE id = ?
```

---

## Index Management

### Analyzing Index Usage

```bash
# Check index usage statistics
aishell optimize indexes prod-db \
  --table orders \
  --analyze

# Output:
# Index Name              | Scans  | Rows Read | Size   | Usage
# ------------------------|--------|-----------|--------|-------
# idx_orders_user_id      | 45,678 | 456,789   | 12 MB  | 89%
# idx_orders_created_at   | 12,345 | 123,456   | 8 MB   | 45%
# idx_orders_status       | 0      | 0         | 4 MB   | 0% ⚠

# Find unused indexes
aishell optimize indexes prod-db \
  --unused \
  --min-age 30d

# Suggestion to drop:
# DROP INDEX idx_orders_status;  -- Never used in 30 days, wasting 4MB
```

### Index Recommendations

```bash
# Get index recommendations for table
aishell optimize suggest-indexes prod-db \
  --table orders \
  --analyze-queries

# AI-powered recommendations:
# 1. CREATE INDEX idx_orders_user_status ON orders(user_id, status)
#    - Covers 67% of queries on this table
#    - Estimated improvement: 2.3x faster
#    - Index size: ~15 MB
#
# 2. CREATE INDEX idx_orders_created_user ON orders(created_at, user_id)
#    - Covers date range queries
#    - Estimated improvement: 4.1x faster
#    - Index size: ~10 MB

# Get recommendations for specific query
aishell optimize suggest-indexes prod-db \
  --sql "
    SELECT * FROM orders
    WHERE user_id = 123
    AND status = 'pending'
    AND created_at > '2024-01-01'
  "

# Recommendation:
# CREATE INDEX idx_orders_composite ON orders(user_id, status, created_at);
# - Covers all WHERE conditions
# - Allows index-only scan
# - Estimated improvement: 15.2x faster
```

### Index Types

#### PostgreSQL Index Types

```bash
# B-tree index (default, most common)
aishell query run prod-db --sql "
  CREATE INDEX idx_users_email ON users(email);
"

# Hash index (for equality comparisons)
aishell query run prod-db --sql "
  CREATE INDEX idx_sessions_token ON sessions USING HASH(token);
"

# GIN index (for full-text search, JSONB, arrays)
aishell query run prod-db --sql "
  CREATE INDEX idx_products_search ON products
  USING GIN(to_tsvector('english', name || ' ' || description));

  CREATE INDEX idx_users_metadata ON users USING GIN(metadata);
"

# GiST index (for geometric data, ranges)
aishell query run prod-db --sql "
  CREATE INDEX idx_events_daterange ON events USING GIST(date_range);
"

# BRIN index (for very large tables with natural ordering)
aishell query run prod-db --sql "
  CREATE INDEX idx_logs_timestamp ON logs USING BRIN(timestamp);
"

# Partial index (index subset of rows)
aishell query run prod-db --sql "
  CREATE INDEX idx_orders_pending ON orders(created_at)
  WHERE status = 'pending';
"

# Expression index
aishell query run prod-db --sql "
  CREATE INDEX idx_users_lower_email ON users(LOWER(email));
"
```

#### MySQL Index Types

```bash
# B-tree index (default)
aishell query run mysql-prod --sql "
  CREATE INDEX idx_users_email ON users(email);
"

# Full-text index
aishell query run mysql-prod --sql "
  CREATE FULLTEXT INDEX idx_products_search ON products(name, description);
"

# Spatial index
aishell query run mysql-prod --sql "
  CREATE SPATIAL INDEX idx_locations_coords ON locations(coordinates);
"

# Composite index
aishell query run mysql-prod --sql "
  CREATE INDEX idx_orders_user_status ON orders(user_id, status, created_at);
"
```

#### MongoDB Indexes

```bash
# Single field index
aishell query run mongo-prod \
  --collection users \
  --create-index '{"email": 1}' \
  --unique

# Compound index
aishell query run mongo-prod \
  --collection orders \
  --create-index '{"user_id": 1, "created_at": -1}'

# Text index
aishell query run mongo-prod \
  --collection articles \
  --create-index '{
    "title": "text",
    "content": "text"
  }'

# Geospatial index
aishell query run mongo-prod \
  --collection locations \
  --create-index '{"coordinates": "2dsphere"}'

# TTL index (auto-delete documents)
aishell query run mongo-prod \
  --collection sessions \
  --create-index '{"created_at": 1}' \
  --expire-after-seconds 3600
```

### Index Maintenance

```bash
# Rebuild indexes (PostgreSQL)
aishell query run prod-db --sql "REINDEX TABLE orders;"

# Analyze table statistics
aishell query run prod-db --sql "ANALYZE orders;"

# Check index bloat
aishell optimize check-bloat prod-db \
  --table orders \
  --indexes

# Example output:
# Index Name              | Size  | Bloat | Bloat % | Action
# ------------------------|-------|-------|---------|--------
# idx_orders_user_id      | 25 MB | 8 MB  | 32%     | REINDEX
# idx_orders_created_at   | 15 MB | 2 MB  | 13%     | OK

# Rebuild bloated indexes
aishell optimize rebuild-indexes prod-db \
  --bloat-threshold 30% \
  --concurrent
```

---

## Natural Language to SQL

### Converting Natural Language Queries

```bash
# Simple conversion
aishell query nl2sql prod-db \
  --prompt "Show me all users who signed up last week"

# Generated SQL:
# SELECT *
# FROM users
# WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
# AND created_at < CURRENT_DATE
# ORDER BY created_at DESC;

# Complex query
aishell query nl2sql prod-db \
  --prompt "Find top 10 customers by total spending in 2024, include their name and email"

# Generated SQL:
# SELECT
#   u.id,
#   u.name,
#   u.email,
#   SUM(o.total) as total_spent,
#   COUNT(o.id) as order_count
# FROM users u
# INNER JOIN orders o ON u.id = o.user_id
# WHERE EXTRACT(YEAR FROM o.created_at) = 2024
# GROUP BY u.id, u.name, u.email
# ORDER BY total_spent DESC
# LIMIT 10;
```

### Advanced NL2SQL Features

```bash
# With execution
aishell query nl2sql prod-db \
  --prompt "How many active users do we have?" \
  --execute

# With explanation
aishell query nl2sql prod-db \
  --prompt "Show me users with more than 5 orders" \
  --explain

# Explanation output:
# Query Intent: Find users with high order count
# Tables Used: users, orders
# Join Type: INNER JOIN (only users with orders)
# Filter: HAVING COUNT(o.id) > 5
# Why this approach: Using aggregation to count orders per user

# Multi-step queries
aishell query nl2sql prod-db \
  --prompt "
    1. Find all orders from last month
    2. Group by product
    3. Show products with more than 100 orders
    4. Sort by total revenue
  " \
  --multi-step

# Context-aware queries
aishell query nl2sql prod-db \
  --prompt "What's the average order value?" \
  --context "orders table has total column"

# Database-specific optimization
aishell query nl2sql prod-db \
  --prompt "Find users by name (case-insensitive)" \
  --optimize-for postgresql

# Generated (PostgreSQL-optimized):
# SELECT * FROM users WHERE name ILIKE '%search%';

# vs MySQL-optimized:
# SELECT * FROM users WHERE LOWER(name) LIKE LOWER('%search%');
```

### NL2SQL Best Practices

```bash
# Provide schema context
aishell query nl2sql prod-db \
  --prompt "Show recent high-value orders" \
  --schema-context "
    orders table: id, user_id, total, status, created_at
    High value means total > $1000
  "

# Validate before execution
aishell query nl2sql prod-db \
  --prompt "Delete old records" \
  --validate \
  --dry-run \
  --require-confirmation

# Safety checks
aishell query nl2sql prod-db \
  --prompt "Update all user emails" \
  --check-risk \
  --require-where-clause
```

---

## Risk Checking

### Query Risk Analysis

```bash
# Check query risk level
aishell optimize risk-check prod-db \
  --sql "DELETE FROM logs WHERE created_at < '2024-01-01'"

# Output:
# Risk Level: MEDIUM
#
# Risks Identified:
# ✓ Has WHERE clause (good)
# ⚠ DELETE operation (destructive)
# ⚠ Affects large number of rows (~2.3M rows)
# ✓ Non-production hours recommended
#
# Recommendations:
# 1. Run EXPLAIN to verify affected rows
# 2. Create backup before execution
# 3. Use batch deletion with LIMIT
# 4. Test on staging environment first

# High-risk query
aishell optimize risk-check prod-db \
  --sql "UPDATE users SET role = 'admin'"

# Output:
# Risk Level: CRITICAL ⚠⚠⚠
#
# Risks Identified:
# ✗ No WHERE clause (affects all rows!)
# ✗ Modifies security-sensitive column (role)
# ✗ Affects ~1.2M users
# ✗ Irreversible without backup
#
# EXECUTION BLOCKED
# This query requires explicit --force flag and backup confirmation
```

### Safe Query Patterns

```bash
# Batch operations with safety limits
aishell optimize safe-batch prod-db \
  --sql "DELETE FROM logs WHERE created_at < '2023-01-01'" \
  --batch-size 1000 \
  --delay 100ms \
  --dry-run

# Safe update with confirmation
aishell optimize safe-update prod-db \
  --sql "UPDATE products SET price = price * 1.1 WHERE category = 'electronics'" \
  --preview-affected \
  --require-confirmation

# Preview output:
# Affected Rows: 234
# Sample affected records:
# - Product A: $99.99 → $109.99
# - Product B: $149.99 → $164.99
# - Product C: $299.99 → $329.99
#
# Continue? (yes/no):
```

### Query Safeguards

```bash
# Enable automatic safeguards
aishell config set optimization.safeguards.enabled true
aishell config set optimization.safeguards.require-where-for-update true
aishell config set optimization.safeguards.require-where-for-delete true
aishell config set optimization.safeguards.max-affected-rows 10000

# Safeguards will prevent:
# - UPDATE/DELETE without WHERE clause
# - Queries affecting more than max-affected-rows
# - DDL operations without confirmation
# - Queries with known performance anti-patterns
```

---

## Query Analysis

### Execution Plans

#### PostgreSQL EXPLAIN

```bash
# Basic EXPLAIN
aishell query explain prod-db \
  --sql "SELECT * FROM orders WHERE user_id = 123"

# Output:
# Index Scan using idx_orders_user_id on orders
#   (cost=0.42..8.44 rows=1 width=123)
#   Index Cond: (user_id = 123)

# EXPLAIN ANALYZE (actually executes query)
aishell query explain prod-db \
  --sql "SELECT * FROM orders WHERE user_id = 123" \
  --analyze

# Output includes actual timing:
# Index Scan using idx_orders_user_id on orders
#   (cost=0.42..8.44 rows=1 width=123)
#   (actual time=0.023..0.025 rows=5 loops=1)
#   Index Cond: (user_id = 123)
# Planning Time: 0.125 ms
# Execution Time: 0.051 ms

# Visual execution plan
aishell query explain prod-db \
  --sql "..." \
  --format visual \
  --analyze

# Output:
#                      ┌──────────────────────────┐
#                      │   Hash Join              │
#                      │   Cost: 234.56           │
#                      │   Rows: 1,234            │
#                      │   Time: 45.23ms          │
#                      └────────┬─────────────────┘
#                               │
#              ┌────────────────┴────────────────┐
#              │                                 │
#    ┌─────────▼─────────┐           ┌─────────▼─────────┐
#    │  Seq Scan (users) │           │ Index Scan (orders)│
#    │  Cost: 0..156.78  │           │  Cost: 0.42..89.23│
#    │  Rows: 10,000     │           │  Rows: 5,432      │
#    │  Time: 23.45ms    │           │  Time: 18.67ms    │
#    └───────────────────┘           └───────────────────┘
```

#### MySQL EXPLAIN

```bash
# Basic EXPLAIN
aishell query explain mysql-prod \
  --sql "SELECT * FROM orders WHERE user_id = 123"

# Output:
# +--+-------------+--------+------+------------------+------+---------+-------+------+
# |id| select_type | table  | type | possible_keys    | key  | key_len | ref   | rows |
# +--+-------------+--------+------+------------------+------+---------+-------+------+
# | 1| SIMPLE      | orders | ref  | idx_orders_user  | idx  | 4       | const |   5  |
# +--+-------------+--------+------+------------------+------+---------+-------+------+

# EXPLAIN with JSON format
aishell query explain mysql-prod \
  --sql "..." \
  --format json

# EXPLAIN ANALYZE (MySQL 8.0+)
aishell query explain mysql-prod \
  --sql "..." \
  --analyze
```

#### MongoDB Explain

```bash
# Explain MongoDB query
aishell query explain mongo-prod \
  --collection orders \
  --query '{"user_id": 123}' \
  --explain

# Output:
# {
#   "queryPlanner": {
#     "winningPlan": {
#       "stage": "FETCH",
#       "inputStage": {
#         "stage": "IXSCAN",
#         "indexName": "user_id_1",
#         "keysExamined": 5,
#         "docsExamined": 5
#       }
#     }
#   },
#   "executionStats": {
#     "executionTimeMillis": 2,
#     "totalDocsExamined": 5,
#     "totalKeysExamined": 5
#   }
# }
```

### Query Cost Estimation

```bash
# Estimate query cost before execution
aishell optimize estimate-cost prod-db \
  --sql "SELECT * FROM orders WHERE created_at > '2024-01-01'"

# Output:
# Estimated Cost: 2,345.67 (high)
# Estimated Rows: ~45,678
# Estimated Time: ~2.3 seconds
# Estimated I/O: 1,234 pages
# Estimated Memory: 45 MB
#
# Recommendation: Add index on created_at or use smaller date range
```

---

## Performance Tuning

### Query Optimization Techniques

#### 1. Use Indexes Effectively

```bash
# Before optimization
aishell query run prod-db --sql "
  SELECT * FROM orders
  WHERE user_id = 123
  AND status = 'pending'
" --analyze

# Seq Scan on orders (cost=0.00..2567.89 rows=123 width=123)
# Execution Time: 245.67 ms

# Create composite index
aishell query run prod-db --sql "
  CREATE INDEX idx_orders_user_status ON orders(user_id, status)
"

# After optimization
# Index Scan using idx_orders_user_status (cost=0.42..8.44 rows=5 width=123)
# Execution Time: 1.23 ms
# Improvement: 200x faster
```

#### 2. Optimize JOINs

```bash
# Before: Inefficient join order
aishell query run prod-db --sql "
  SELECT *
  FROM large_table l
  JOIN small_table s ON l.id = s.large_id
  WHERE s.status = 'active'
"

# After: Filter first, then join
aishell query run prod-db --sql "
  SELECT l.*
  FROM large_table l
  JOIN (
    SELECT large_id
    FROM small_table
    WHERE status = 'active'
  ) s ON l.id = s.large_id
"
```

#### 3. Use Covering Indexes

```bash
# Query only needs id, total, created_at
aishell query run prod-db --sql "
  SELECT id, total, created_at
  FROM orders
  WHERE user_id = 123
"

# Create covering index
aishell query run prod-db --sql "
  CREATE INDEX idx_orders_covering ON orders(user_id)
  INCLUDE (id, total, created_at)
"
# Now PostgreSQL can use index-only scan (no table access needed)
```

#### 4. Avoid SELECT *

```bash
# Bad: Returns unnecessary data
SELECT * FROM users WHERE id = 123

# Good: Only select needed columns
SELECT id, name, email FROM users WHERE id = 123
```

#### 5. Use LIMIT

```bash
# Bad: Returns all results
SELECT * FROM orders WHERE status = 'pending'

# Good: Limit results
SELECT * FROM orders WHERE status = 'pending' LIMIT 100
```

#### 6. Optimize Subqueries

```bash
# Before: Correlated subquery (slow)
aishell query run prod-db --sql "
  SELECT u.id, u.name,
    (SELECT COUNT(*) FROM orders WHERE user_id = u.id) as order_count
  FROM users u
"

# After: Use JOIN (faster)
aishell query run prod-db --sql "
  SELECT u.id, u.name, COUNT(o.id) as order_count
  FROM users u
  LEFT JOIN orders o ON u.id = o.user_id
  GROUP BY u.id, u.name
"
```

### Caching Strategies

```bash
# Enable query result caching
aishell config set optimization.cache.enabled true
aishell config set optimization.cache.ttl 300  # 5 minutes

# Cache specific query
aishell query run prod-db \
  --sql "SELECT COUNT(*) FROM users" \
  --cache \
  --cache-key "user-count" \
  --cache-ttl 600

# Invalidate cache
aishell cache invalidate prod-db --pattern "user-*"

# Show cache statistics
aishell cache stats prod-db
```

### Connection Pooling

```bash
# Optimize connection pool
aishell connection update prod-db \
  --pool-min 5 \
  --pool-max 20 \
  --pool-acquire-timeout 30000 \
  --pool-idle-timeout 10000

# Monitor pool usage
aishell connection pool-stats prod-db

# Output:
# Pool Statistics:
# - Total Connections: 15
# - Active: 8
# - Idle: 7
# - Waiting: 0
# - Peak Usage: 18 (89%)
```

---

## Best Practices

### 1. Regular Analysis

```bash
#!/bin/bash
# weekly-optimization.sh

# Find slow queries
aishell optimize slow-queries prod-db \
  --threshold 500ms \
  --period 7d \
  --output weekly-slow-queries.json

# Check for missing indexes
aishell optimize suggest-indexes prod-db \
  --analyze-queries \
  --output index-recommendations.json

# Identify unused indexes
aishell optimize indexes prod-db \
  --unused \
  --min-age 30d \
  --output unused-indexes.json

# Generate optimization report
aishell optimize report prod-db \
  --period 7d \
  --format pdf \
  --output optimization-report.pdf
```

### 2. Test Before Applying

```bash
# Always test on staging first
aishell optimize suggest prod-db --sql "..." | \
  aishell optimize apply staging-db --dry-run

# Compare performance
aishell optimize benchmark \
  --before "original query" \
  --after "optimized query" \
  --iterations 100
```

### 3. Monitor Impact

```bash
# Track query performance over time
aishell optimize track prod-db \
  --query-fingerprint "SELECT ... FROM orders WHERE user_id = ?" \
  --period 30d

# Set up alerts for performance regression
aishell monitor alerts create prod-db \
  --metric query-time \
  --query-pattern "SELECT ... FROM orders" \
  --threshold 100ms \
  --action slack
```

### 4. Document Changes

```bash
# Generate change log
aishell optimize changelog prod-db \
  --since "2024-01-01" \
  --output optimization-changelog.md

# Include in commit message
git commit -m "
Optimize orders query performance

- Added composite index on (user_id, status)
- Rewrote subquery as JOIN
- Added LIMIT clause

Performance: 245ms → 1.2ms (204x improvement)
Query: fingerprint-abc123
"
```

---

## Troubleshooting

### Common Issues

```bash
# Issue: Query still slow after adding index
# Solution: Check if index is being used
aishell query explain prod-db --sql "..." --analyze

# Issue: Index not used
# Solution: Update table statistics
aishell query run prod-db --sql "ANALYZE table_name"

# Issue: Unexpected query plan
# Solution: Check PostgreSQL planner settings
aishell query run prod-db --sql "SHOW all" | grep planner

# Issue: Out of memory
# Solution: Check work_mem setting
aishell query run prod-db --sql "SHOW work_mem"
# Increase if needed:
aishell query run prod-db --sql "SET work_mem = '256MB'"
```

---

## Next Steps

- Configure [Backup & Recovery](./BACKUP_RECOVERY.md) procedures
- Set up [Monitoring & Analytics](./MONITORING_ANALYTICS.md)
- Review [Security Best Practices](./SECURITY_BEST_PRACTICES.md)

---

*Last Updated: 2024-01-15 | Version: 1.0.0*
