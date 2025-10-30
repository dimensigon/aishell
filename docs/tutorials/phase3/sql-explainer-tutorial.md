# SQL Explainer Tutorial

Master the art of understanding and optimizing database query execution plans with AI-Shell's intelligent SQL Explainer.

## Table of Contents

1. [What You'll Learn](#what-youll-learn)
2. [Prerequisites](#prerequisites)
3. [Part 1: Understanding Query Execution Plans](#part-1-understanding-query-execution-plans-10-min)
4. [Part 2: Basic EXPLAIN Analysis](#part-2-basic-explain-analysis-10-min)
5. [Part 3: Reading Execution Plans](#part-3-reading-execution-plans-15-min)
6. [Part 4: Identifying Performance Issues](#part-4-identifying-performance-issues-15-min)
7. [Part 5: Query Optimization Techniques](#part-5-query-optimization-techniques-20-min)
8. [Part 6: Advanced Analysis](#part-6-advanced-analysis-15-min)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Next Steps](#next-steps)

## What You'll Learn

By the end of this tutorial, you will:

- Understand query execution plans and their components
- Read and interpret EXPLAIN output
- Identify performance bottlenecks in queries
- Optimize slow queries using indexes and rewrites
- Analyze join strategies and their costs
- Use AI-Shell's intelligent recommendations
- Profile queries in production
- Monitor query performance over time

**Estimated Time:** 85 minutes

## Prerequisites

Before starting this tutorial, ensure you have:

- AI-Shell installed and configured
- A database with some data (10,000+ rows recommended)
- Basic understanding of SQL and JOINs
- Familiarity with database indexes
- 85 minutes of focused time

## Part 1: Understanding Query Execution Plans (10 min)

### What is a Query Execution Plan?

A query execution plan is the database's strategy for executing a SQL query, showing:

- **How tables are accessed** (sequential scan, index scan, etc.)
- **Join algorithms used** (nested loop, hash join, merge join)
- **Order of operations** (which tables are read first)
- **Estimated costs** (time and resources needed)
- **Row count estimates** (how many rows at each step)

### Why Execution Plans Matter

```
Example: Finding users who placed orders in last 30 days

❌ Bad Plan (10 seconds):
1. Scan ALL users (1M rows)
2. For each user, scan ALL orders (10M rows)
3. Filter orders by date
4. Total: 10 trillion comparisons

✅ Good Plan (50 milliseconds):
1. Use index on orders.date (30k rows)
2. Use index on orders.user_id
3. Fetch matching users (25k rows)
4. Total: 55k rows processed
```

**Performance Difference: 200x faster!**

### Query Execution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      1. SQL Parser                           │
│              Parse SQL and build syntax tree                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   2. Query Rewriter                          │
│           Simplify, normalize, apply rules                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   3. Query Planner                           │
│       Generate possible execution plans (10-1000s)           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  4. Cost Optimizer                           │
│          Estimate cost of each plan, pick best              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  5. Query Executor                           │
│              Execute chosen plan, return results             │
└─────────────────────────────────────────────────────────────┘
```

### Plan Node Types

**Scan Nodes (How data is read):**

| Node Type | Description | Performance | When Used |
|-----------|-------------|-------------|-----------|
| Seq Scan | Read entire table | Slow | Small tables or no index |
| Index Scan | Use index to find rows | Fast | Selective queries |
| Index Only Scan | Read only from index | Fastest | Index covers all columns |
| Bitmap Index Scan | Build bitmap of matching rows | Medium | Multiple indexes |

**Join Nodes (How tables are combined):**

| Node Type | Description | Cost | Best For |
|-----------|-------------|------|----------|
| Nested Loop | For each outer row, scan inner | O(N×M) | Small tables |
| Hash Join | Build hash table, probe | O(N+M) | Large tables, equality joins |
| Merge Join | Sort both, merge | O(N log N + M log M) | Pre-sorted data |

**Other Nodes:**

- **Sort**: Order results by columns
- **Aggregate**: GROUP BY, SUM, COUNT, etc.
- **Limit**: LIMIT/OFFSET results
- **Subquery Scan**: Execute subquery
- **CTE Scan**: Common Table Expression

### Cost Metrics

```sql
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

Seq Scan on users  (cost=0.00..18334.50 rows=1 width=128)
  Filter: (email = 'test@example.com')
```

**Understanding the output:**
- `cost=0.00..18334.50` - Start cost..Total cost
- `rows=1` - Estimated rows returned
- `width=128` - Average row size in bytes

**Cost Units:**
- 1.0 = Reading one 8KB page from disk
- CPU operations are much cheaper (0.01 per row)
- Total cost = I/O cost + CPU cost

## Part 2: Basic EXPLAIN Analysis (10 min)

### Your First EXPLAIN

Use AI-Shell to explain a simple query:

```bash
ai-shell explain "SELECT * FROM users WHERE email = 'test@example.com'"
```

**Output:**

```
┌─────────────────────────────────────────────────────────────┐
│                   QUERY EXECUTION PLAN                       │
└─────────────────────────────────────────────────────────────┘

Query: SELECT * FROM users WHERE email = 'test@example.com'

Seq Scan on users  (cost=0.00..18334.50 rows=1 width=128)
  Filter: (email = 'test@example.com')

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 AI Analysis:

⚠️  Performance Issue Detected!

Problem: Sequential scan on large table (1M rows)
Impact: Reading all rows to find 1 match (slow)
Cost: 18334.50 units

💡 Recommendation:
Create index on users.email for instant lookups

Suggested Index:
  CREATE INDEX idx_users_email ON users(email);

Expected Improvement: 1000x faster (18334 → 8 cost)
```

### EXPLAIN vs EXPLAIN ANALYZE

**EXPLAIN**: Shows the planned execution (estimates)
**EXPLAIN ANALYZE**: Actually runs query and shows real performance

```bash
# Just show the plan (fast, doesn't run query)
ai-shell explain "SELECT * FROM orders WHERE status = 'pending'"

# Run query and show actual performance (slower)
ai-shell explain "SELECT * FROM orders WHERE status = 'pending'" --analyze
```

**EXPLAIN ANALYZE Output:**

```sql
Index Scan using idx_orders_status on orders
  (cost=0.43..1234.56 rows=500 width=200)
  (actual time=0.123..45.678 rows=523 loops=1)
  Index Cond: (status = 'pending')

Planning Time: 0.245 ms
Execution Time: 46.123 ms
```

**Key Differences:**
- `rows=500` - Estimated rows
- `actual rows=523` - Actually returned 523 rows
- Shows real timing: 46.123 ms

### Using AI-Shell's Explain Command

```typescript
// TypeScript API
import { AIShell } from 'ai-shell';

const shell = new AIShell();

// Basic explain
const plan = await shell.explain('SELECT * FROM products WHERE price > 100');

console.log('Plan:', plan.text);
console.log('Cost:', plan.totalCost);
console.log('Estimated Rows:', plan.estimatedRows);

// With analysis
const analysis = await shell.explain(
  'SELECT * FROM products WHERE price > 100',
  { analyze: true }
);

console.log('Actual Rows:', analysis.actualRows);
console.log('Execution Time:', analysis.executionTime, 'ms');

// With recommendations
const withRecs = await shell.explain(
  'SELECT * FROM products WHERE price > 100',
  { recommendations: true }
);

console.log('\nRecommendations:');
withRecs.recommendations.forEach(rec => {
  console.log(`- ${rec.type}: ${rec.description}`);
  console.log(`  Expected improvement: ${rec.improvement}`);
  console.log(`  SQL: ${rec.sql}`);
});
```

### Interactive Explain Session

Start an interactive session:

```bash
ai-shell explain --interactive
```

```
AI-Shell SQL Explainer (Interactive Mode)
Type a query to explain, or 'help' for commands.

> SELECT * FROM users WHERE created_at > '2025-01-01'

Analyzing query...

Seq Scan on users  (cost=0.00..18334.50 rows=15000 width=128)
  Filter: (created_at > '2025-01-01')

⚠️  Sequential scan - consider adding index

> suggestions

💡 Optimization Suggestions:

1. Create index on created_at:
   CREATE INDEX idx_users_created_at ON users(created_at);
   Expected improvement: 100x faster

2. Add WHERE clause to filter earlier:
   Consider if you can narrow the date range

3. Use LIMIT if you don't need all rows

> apply 1

Creating index idx_users_created_at...
✓ Index created successfully

Re-analyzing query...

Index Scan using idx_users_created_at on users
  (cost=0.43..1234.56 rows=15000 width=128)
  Index Cond: (created_at > '2025-01-01')

✓ Improved from 18334.50 to 1234.56 cost (14.9x faster)

> exit
```

## Part 3: Reading Execution Plans (15 min)

### Understanding Plan Trees

Execution plans are trees - read from bottom-up and inside-out:

```sql
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2025-01-01'
GROUP BY u.id, u.name
ORDER BY order_count DESC
LIMIT 10;
```

**Execution Plan:**

```
Limit  (cost=12345..12350 rows=10)
  ->  Sort  (cost=12345..12445 rows=1000)
        Sort Key: (count(o.id)) DESC
        ->  HashAggregate  (cost=10000..11000 rows=1000)
              Group Key: u.id, u.name
              ->  Hash Left Join  (cost=5000..9000 rows=50000)
                    Hash Cond: (o.user_id = u.id)
                    ->  Seq Scan on orders o  (cost=0..2000 rows=50000)
                    ->  Hash  (cost=2500..2500 rows=5000)
                          ->  Index Scan using idx_users_created_at on users u
                                (cost=0..2500 rows=5000)
                                Index Cond: (created_at > '2025-01-01')
```

**Reading Order (bottom to top):**

1. **Index Scan on users** (filter by created_at)
   - Cost: 0..2500
   - Rows: 5000 users after 2025-01-01

2. **Hash** (build hash table of users)
   - Cost: 2500..2500
   - Creates in-memory hash table

3. **Seq Scan on orders** (read all orders)
   - Cost: 0..2000
   - Rows: 50000 orders

4. **Hash Left Join** (join users and orders)
   - Cost: 5000..9000
   - Probe orders hash table for each user

5. **HashAggregate** (GROUP BY and COUNT)
   - Cost: 10000..11000
   - Count orders per user

6. **Sort** (ORDER BY order_count DESC)
   - Cost: 12345..12445
   - Sort by count descending

7. **Limit** (take top 10)
   - Cost: 12345..12350
   - Return only 10 rows

### Visual Plan Analysis

AI-Shell can visualize plans:

```bash
ai-shell explain "SELECT ..." --visualize
```

**Output:**

```
                           Limit (10 rows)
                                 │
                                 ▼
                        Sort (order_count DESC)
                                 │
                                 ▼
                      HashAggregate (GROUP BY)
                                 │
                                 ▼
                          Hash Left Join
                          ┌──────┴──────┐
                          ▼              ▼
                    Seq Scan          Hash
                    (orders)           │
                                       ▼
                                  Index Scan
                                    (users)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bottleneck: Seq Scan on orders (cost: 2000, 50k rows)
Recommendation: Add index on orders.user_id
```

### Common Plan Patterns

#### Pattern 1: Table Scan (Slow)

```
Seq Scan on products  (cost=0.00..5000 rows=100000)
  Filter: (category = 'electronics')
```

**Problem**: Reading entire table
**Fix**: Add index on category

#### Pattern 2: Index Scan (Fast)

```
Index Scan using idx_products_category on products
  (cost=0.43..1234 rows=5000)
  Index Cond: (category = 'electronics')
```

**Good**: Using index for direct lookup

#### Pattern 3: Index Only Scan (Fastest)

```
Index Only Scan using idx_products_category_price on products
  (cost=0.43..456 rows=5000)
  Index Cond: (category = 'electronics')
```

**Best**: Reading only from index, no table access

#### Pattern 4: Bitmap Index Scan (Multiple Conditions)

```
Bitmap Heap Scan on products  (cost=123..2345 rows=1000)
  Recheck Cond: ((category = 'electronics') AND (price > 100))
  ->  BitmapAnd  (cost=123 rows=1000)
        ->  Bitmap Index Scan on idx_category
              Index Cond: (category = 'electronics')
        ->  Bitmap Index Scan on idx_price
              Index Cond: (price > 100)
```

**Multiple indexes**: Combines two indexes efficiently

#### Pattern 5: Nested Loop Join (Small Tables)

```
Nested Loop  (cost=0..1234 rows=100)
  ->  Seq Scan on categories  (cost=0..12 rows=10)
  ->  Index Scan using idx_products_category_id on products
        (cost=0..120 rows=10)
        Index Cond: (category_id = categories.id)
```

**Good for**: Small outer table (10 rows), indexed inner table

#### Pattern 6: Hash Join (Large Tables)

```
Hash Join  (cost=5000..15000 rows=50000)
  Hash Cond: (orders.user_id = users.id)
  ->  Seq Scan on orders  (cost=0..5000 rows=50000)
  ->  Hash  (cost=2500..2500 rows=10000)
        ->  Seq Scan on users  (cost=0..2500 rows=10000)
```

**Good for**: Large tables with equality join

### AI-Powered Plan Explanation

Ask AI-Shell to explain in plain English:

```bash
ai-shell explain "SELECT ..." --explain-like-im-five
```

**Output:**

```
🤖 AI Explanation (ELI5):

Your query is like finding all orders from users in California:

1. First, I look through my users phonebook (users table)
   and write down everyone in California (5,000 people)

2. Then, I put those names in a special quick-lookup box (hash table)

3. Next, I go through my orders filing cabinet (orders table)
   one by one (50,000 orders)

4. For each order, I check if the customer is in my California box

5. I count how many orders each California user has

6. I sort them by who ordered the most

7. I give you the top 10

The slow part: Going through all 50,000 orders one by one (step 3)

How to fix it: Put a sticky note on each order showing which
state the customer is from (create index on orders.user_id)
```

## Part 4: Identifying Performance Issues (15 min)

### Issue 1: Sequential Scans on Large Tables

**Symptom:**

```
Seq Scan on orders  (cost=0..100000 rows=1000000)
  Filter: (status = 'pending')
```

**Problem**: Reading 1M rows to find matches

**Diagnosis:**

```bash
ai-shell explain-issues "SELECT * FROM orders WHERE status = 'pending'"
```

**Output:**

```
🚨 Critical Issue: Sequential Scan

Table: orders (1,000,000 rows)
Scan Cost: 100,000 units
Estimated Time: ~2 seconds

Why it's slow:
- Reading every single row (1M rows)
- Checking each row's status
- No index to quickly find pending orders

Impact:
- Slow query response (2+ seconds)
- High CPU usage
- Blocks other queries
- Poor user experience

Fix:
CREATE INDEX idx_orders_status ON orders(status);

Expected Improvement: 500x faster (cost: 100000 → 200)
```

**Quick Fix:**

```sql
CREATE INDEX idx_orders_status ON orders(status);
```

### Issue 2: Nested Loop on Large Tables

**Symptom:**

```
Nested Loop  (cost=0..5000000 rows=100000)
  ->  Seq Scan on users  (cost=0..5000 rows=10000)
  ->  Seq Scan on orders  (cost=0..5000 rows=50000)
        Filter: (orders.user_id = users.id)
```

**Problem**: 10,000 × 50,000 = 500M comparisons!

**Fix:**

```sql
-- Add index on join column
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Now uses Hash Join instead:
Hash Join  (cost=7500..15000 rows=100000)
  Hash Cond: (orders.user_id = users.id)
  ...
```

### Issue 3: Sorting Large Result Sets

**Symptom:**

```
Sort  (cost=150000..200000 rows=1000000)
  Sort Key: created_at DESC
  ->  Seq Scan on orders  (cost=0..100000 rows=1000000)
```

**Problem**: Sorting 1M rows in memory

**Fix Option 1**: Index for pre-sorted data

```sql
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- Now:
Index Scan using idx_orders_created_at on orders
  (cost=0..5000 rows=1000000)
```

**Fix Option 2**: Use LIMIT

```sql
-- Only need top 100
SELECT * FROM orders ORDER BY created_at DESC LIMIT 100;

-- Much cheaper:
Limit  (cost=0..100 rows=100)
  ->  Index Scan using idx_orders_created_at on orders
```

### Issue 4: Subquery Executed Per Row

**Symptom:**

```
Seq Scan on users  (cost=0..1000000 rows=10000)
  Filter: ((SELECT COUNT(*) FROM orders WHERE user_id = users.id) > 10)
  SubPlan 1
    ->  Aggregate  (cost=50..100 rows=1)
          ->  Seq Scan on orders  (cost=0..50 rows=50)
                Filter: (user_id = users.id)
```

**Problem**: Subquery runs 10,000 times (once per user)!

**Fix**: Rewrite as JOIN

```sql
-- Instead of:
SELECT * FROM users
WHERE (SELECT COUNT(*) FROM orders WHERE user_id = users.id) > 10;

-- Use:
SELECT u.*
FROM users u
JOIN (
  SELECT user_id, COUNT(*) as order_count
  FROM orders
  GROUP BY user_id
  HAVING COUNT(*) > 10
) o ON u.id = o.user_id;

-- Now:
Hash Join  (cost=7500..8500 rows=500)
  ...much faster...
```

### Issue 5: Missing WHERE Clause

**Symptom:**

```
Seq Scan on audit_logs  (cost=0..500000 rows=10000000)
```

**Problem**: Reading 10M rows without filtering

**Fix**: Add WHERE clause

```sql
-- Add date filter
SELECT * FROM audit_logs
WHERE created_at > NOW() - INTERVAL '30 days';

-- Now:
Index Scan using idx_audit_logs_created_at
  (cost=0..5000 rows=50000)
```

### Automated Issue Detection

AI-Shell can automatically find issues:

```bash
ai-shell analyze-slow-queries --threshold 1000ms
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SLOW QUERY ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 5 queries slower than 1000ms

1. SELECT * FROM orders WHERE status = 'pending'
   Execution Time: 2,345 ms
   Issue: Sequential scan (1M rows)
   Fix: CREATE INDEX idx_orders_status ON orders(status);
   Priority: 🔴 Critical

2. SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o ...
   Execution Time: 5,678 ms
   Issue: Nested loop join (500M operations)
   Fix: CREATE INDEX idx_orders_user_id ON orders(user_id);
   Priority: 🔴 Critical

3. SELECT * FROM products ORDER BY created_at DESC
   Execution Time: 1,234 ms
   Issue: Sorting 500k rows
   Fix: CREATE INDEX idx_products_created_at ON products(created_at DESC);
   Priority: 🟡 Medium

4. SELECT * FROM logs WHERE created_at > '2025-01-01'
   Execution Time: 3,456 ms
   Issue: Sequential scan, old data
   Fix: Consider partitioning by date
   Priority: 🟡 Medium

5. SELECT * FROM users WHERE email LIKE '%@gmail.com'
   Execution Time: 1,567 ms
   Issue: Can't use index with leading wildcard
   Fix: Add column for domain, index it
   Priority: 🟢 Low

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Apply all fixes?
[Y]es / [N]o / [S]elect: y

Creating indexes...
✓ idx_orders_status created (2.3s)
✓ idx_orders_user_id created (3.1s)
✓ idx_products_created_at created (1.8s)

Estimated total improvement: 15.2 seconds → 1.1 seconds (13.8x faster)
```

## Part 5: Query Optimization Techniques (20 min)

### Technique 1: Add Strategic Indexes

**Rule**: Index columns used in WHERE, JOIN, and ORDER BY

```sql
-- Query
SELECT * FROM orders
WHERE user_id = 123
  AND status = 'pending'
  AND created_at > '2025-01-01'
ORDER BY created_at DESC;

-- Optimal index (composite)
CREATE INDEX idx_orders_user_status_date
ON orders(user_id, status, created_at DESC);

-- Index covers:
-- ✓ WHERE user_id = 123 (exact match)
-- ✓ WHERE status = 'pending' (exact match)
-- ✓ WHERE created_at > '2025-01-01' (range)
-- ✓ ORDER BY created_at DESC (pre-sorted)
```

**Before (no index):**
```
Sort  (cost=15000..15100 rows=100)
  Sort Key: created_at DESC
  ->  Seq Scan on orders  (cost=0..15000 rows=100)
        Filter: ((user_id = 123) AND (status = 'pending') AND ...)
```

**After (with index):**
```
Index Scan using idx_orders_user_status_date on orders
  (cost=0..50 rows=100)
  Index Cond: ((user_id = 123) AND (status = 'pending') AND ...)
```

**Improvement**: 300x faster!

### Technique 2: Use Covering Indexes

**Rule**: Include all needed columns in the index

```sql
-- Query needs only these columns
SELECT id, status, total_amount
FROM orders
WHERE user_id = 123;

-- Covering index includes all columns
CREATE INDEX idx_orders_user_covering
ON orders(user_id) INCLUDE (id, status, total_amount);

-- Or composite (PostgreSQL 11+)
CREATE INDEX idx_orders_user_covering
ON orders(user_id, id, status, total_amount);
```

**Before:**
```
Index Scan using idx_orders_user_id on orders
  (cost=0..450 rows=100)
  Index Cond: (user_id = 123)
```

**After:**
```
Index Only Scan using idx_orders_user_covering on orders
  (cost=0..150 rows=100)
  Index Cond: (user_id = 123)
```

**Benefit**: No table access needed (3x faster)

### Technique 3: Rewrite Subqueries as JOINs

**Before (slow):**

```sql
SELECT *
FROM products p
WHERE EXISTS (
  SELECT 1
  FROM order_items oi
  WHERE oi.product_id = p.id
    AND oi.created_at > '2025-01-01'
);

-- Execution plan:
Seq Scan on products p  (cost=0..1000000 rows=50000)
  Filter: (SubPlan 1)
  SubPlan 1
    ->  Index Scan on order_items oi
          (cost=0..100 rows=1)
```

**After (fast):**

```sql
SELECT DISTINCT p.*
FROM products p
INNER JOIN order_items oi ON p.id = oi.product_id
WHERE oi.created_at > '2025-01-01';

-- Execution plan:
HashAggregate  (cost=5000..5500 rows=5000)
  ->  Hash Join  (cost=2000..4500 rows=10000)
        Hash Cond: (p.id = oi.product_id)
        ...
```

**Improvement**: 20x faster

### Technique 4: Optimize JOIN Order

**Rule**: Join smaller tables first

**Before (wrong order):**

```sql
-- 1M orders JOIN 10 categories JOIN 100K products
SELECT *
FROM orders o
JOIN products p ON o.product_id = p.id
JOIN categories c ON p.category_id = c.id;

-- Bad plan:
Hash Join  (cost=50000..100000 rows=1000000)
  ->  Hash Join  (cost=40000..80000 rows=1000000)
        ->  Seq Scan on orders o  (cost=0..40000 rows=1000000)
        ->  Hash (cost=1000..1000 rows=100000)
              ->  Seq Scan on products p
  ->  Hash (cost=10..10 rows=10)
        ->  Seq Scan on categories c
```

**After (better order):**

```sql
-- Start with smallest table (categories)
SELECT *
FROM categories c
JOIN products p ON c.id = p.category_id
JOIN orders o ON p.id = o.product_id;

-- Better plan:
Hash Join  (cost=10000..50000 rows=1000000)
  ->  Seq Scan on orders o  (cost=0..40000 rows=1000000)
  ->  Hash (cost=5000..5000 rows=100000)
        ->  Hash Join  (cost=10..5000 rows=100000)
              ->  Seq Scan on categories c  (cost=0..10 rows=10)
              ->  Hash (cost=1000..1000 rows=100000)
                    ->  Seq Scan on products p
```

### Technique 5: Use Partial Indexes

**Rule**: Index only relevant rows

```sql
-- Query only needs active orders
SELECT * FROM orders WHERE status = 'active';

-- Full index (large)
CREATE INDEX idx_orders_status ON orders(status);
-- Size: 50 MB (all 1M orders)

-- Partial index (small)
CREATE INDEX idx_orders_active
ON orders(id, user_id, total)
WHERE status = 'active';
-- Size: 2 MB (only 40K active orders)

-- Benefits:
-- ✓ 25x smaller index
-- ✓ Faster updates (less index maintenance)
-- ✓ Better cache utilization
```

### Technique 6: Use Query Hints (When Needed)

**PostgreSQL Example:**

```sql
-- Force use of specific index
SELECT * FROM orders
WHERE user_id = 123
  AND /*+ IndexScan(orders idx_orders_user_id) */ status = 'pending';

-- Force join method
SELECT * FROM orders o
JOIN /*+ HashJoin(o u) */ users u ON o.user_id = u.id;
```

**When to use hints:**
- Planner makes wrong choice
- Testing different strategies
- Specific performance requirements

**Warning**: Hints can become outdated as data changes!

### Technique 7: Add WHERE Clauses

**Before:**

```sql
-- Gets all data
SELECT * FROM audit_logs;

-- Plan:
Seq Scan on audit_logs  (cost=0..500000 rows=10000000)
```

**After:**

```sql
-- Filter by date range
SELECT * FROM audit_logs
WHERE created_at > NOW() - INTERVAL '30 days';

-- Plan:
Index Scan using idx_audit_logs_created_at
  (cost=0..5000 rows=50000)
```

**Improvement**: 100x faster, 200x less data

### Technique 8: Use EXPLAIN ANALYZE for Verification

Always verify optimizations work:

```bash
# Before optimization
ai-shell explain "SELECT ..." --analyze > before.txt

# Apply optimization
ai-shell query "CREATE INDEX ..."

# After optimization
ai-shell explain "SELECT ..." --analyze > after.txt

# Compare
ai-shell diff before.txt after.txt
```

**Example output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPTIMIZATION COMPARISON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Metric                Before        After         Change
────────────────────────────────────────────────────────
Execution Time        2,345 ms      156 ms        -93.3%
Planning Time         1.2 ms        1.5 ms        +25.0%
Total Cost            18,334        1,234         -93.3%
Rows (est)            1,000,000     50,000        -95.0%
Rows (actual)         50,123        50,123        0.0%
Buffers Shared        10,234        1,567         -84.7%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Optimization successful: 15x faster
```

## Part 6: Advanced Analysis (15 min)

### Analyzing Complex Queries

**Multi-table JOIN with aggregation:**

```sql
SELECT
  c.name as category,
  COUNT(DISTINCT p.id) as products,
  COUNT(o.id) as orders,
  SUM(o.total_amount) as revenue,
  AVG(o.total_amount) as avg_order
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.id
WHERE o.created_at > '2025-01-01'
GROUP BY c.id, c.name
HAVING COUNT(o.id) > 100
ORDER BY revenue DESC
LIMIT 10;
```

**AI-Shell Analysis:**

```bash
ai-shell explain-deep "SELECT ..." --recommendations
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEEP QUERY ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query Complexity: High
Tables: 4
Joins: 3 (all LEFT JOIN)
Aggregations: 5 (COUNT DISTINCT, COUNT, SUM, AVG)
Filters: 1 (date range)
Grouping: 2 columns
Having: 1 condition
Ordering: 1 column
Limit: 10 rows

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXECUTION PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Limit  (cost=50000..50010 rows=10)
  ->  Sort  (cost=50000..50100 rows=100)
        Sort Key: (sum(o.total_amount)) DESC
        ->  GroupAggregate  (cost=40000..48000 rows=100)
              Group Key: c.id, c.name
              Filter: (count(o.id) > 100)
              ->  Hash Join  (cost=30000..40000 rows=50000)
                    Hash Cond: (oi.order_id = o.id)
                    ->  Hash Join  (cost=15000..25000 rows=100000)
                          Hash Cond: (oi.product_id = p.id)
                          ->  Seq Scan on order_items oi
                          ->  Hash Join  (cost=5000..10000 rows=50000)
                                Hash Cond: (p.category_id = c.id)
                                ->  Seq Scan on products p
                                ->  Hash  (cost=10..10 rows=10)
                                      ->  Seq Scan on categories c
                    ->  Hash  (cost=10000..10000 rows=25000)
                          ->  Index Scan using idx_orders_created_at
                                (cost=0..10000 rows=25000)
                                Index Cond: (created_at > '2025-01-01')

Total Cost: 50,010 units
Estimated Time: ~5 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOTTLENECKS DETECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Critical Issues:

1. Sequential scan on order_items (100K rows)
   Cost: 15,000 units (30% of total)
   Impact: High

2. Sequential scan on products (50K rows)
   Cost: 5,000 units (10% of total)
   Impact: Medium

🟡 Optimization Opportunities:

3. GroupAggregate on large result set
   Cost: 8,000 units
   Consider pre-aggregating data

4. Multiple hash table builds
   Memory usage: ~150 MB
   Consider JOIN order optimization

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommendation 1: Add Indexes (Critical)

CREATE INDEX idx_order_items_product_id
ON order_items(product_id);

CREATE INDEX idx_order_items_order_id
ON order_items(order_id);

Expected Improvement: 3-5x faster
Priority: 🔴 High
Confidence: 95%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommendation 2: Materialized View (High Impact)

Create materialized view for pre-aggregated data:

CREATE MATERIALIZED VIEW mv_category_revenue AS
SELECT
  c.id as category_id,
  c.name as category,
  COUNT(DISTINCT p.id) as products,
  COUNT(o.id) as orders,
  SUM(o.total_amount) as revenue,
  AVG(o.total_amount) as avg_order,
  DATE_TRUNC('day', o.created_at) as date
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.id
GROUP BY c.id, c.name, DATE_TRUNC('day', o.created_at);

-- Refresh daily
CREATE INDEX idx_mv_category_revenue_date
ON mv_category_revenue(date);

-- Simplified query:
SELECT *
FROM mv_category_revenue
WHERE date > '2025-01-01'
ORDER BY revenue DESC
LIMIT 10;

Expected Improvement: 50-100x faster
Priority: 🟡 Medium (for frequently run queries)
Confidence: 90%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommendation 3: Query Rewrite

Rewrite to filter earlier:

WITH recent_orders AS (
  SELECT id, total_amount
  FROM orders
  WHERE created_at > '2025-01-01'
),
order_stats AS (
  SELECT
    p.category_id,
    COUNT(DISTINCT p.id) as products,
    COUNT(o.id) as orders,
    SUM(o.total_amount) as revenue,
    AVG(o.total_amount) as avg_order
  FROM recent_orders o
  JOIN order_items oi ON o.id = oi.order_id
  JOIN products p ON oi.product_id = p.id
  GROUP BY p.category_id
  HAVING COUNT(o.id) > 100
)
SELECT c.name, os.*
FROM order_stats os
JOIN categories c ON os.category_id = c.id
ORDER BY revenue DESC
LIMIT 10;

Expected Improvement: 2x faster
Priority: 🟢 Low (marginal improvement)
Confidence: 70%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apply recommendations? [Y/n/select]:
```

### Performance Profiling

Profile query performance over time:

```bash
ai-shell profile "SELECT ..." --duration 60s --interval 5s
```

**Output:**

```
Profiling query for 60 seconds (sampling every 5s)...

Time     Exec Time   Cost      Rows      Hit Rate   Buffers
────────────────────────────────────────────────────────────
00:00    2,345 ms    18,334    50,123    0%         10,234
00:05    2,401 ms    18,334    50,145    0%         10,267
00:10    156 ms      1,234     50,156    98%        1,567
00:15    158 ms      1,234     50,189    97%        1,589
00:20    155 ms      1,234     50,201    99%        1,556
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Performance Summary:

Before optimization (0-10s):
  Avg Execution Time: 2,373 ms
  Cache Hit Rate: 0%
  Avg Buffers: 10,250

After optimization (10-60s):
  Avg Execution Time: 156 ms
  Cache Hit Rate: 98%
  Avg Buffers: 1,567

Improvement: 15.2x faster ✓
Stability: Consistent performance ✓
Caching: Effective ✓
```

### Comparative Analysis

Compare multiple query variants:

```bash
ai-shell compare-queries query1.sql query2.sql query3.sql
```

**Output:**

```
Comparing 3 query variants...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUERY COMPARISON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Metric               Query 1      Query 2      Query 3      Best
─────────────────────────────────────────────────────────────────
Execution Time       2,345 ms     567 ms       156 ms       Q3
Planning Time        1.2 ms       2.1 ms       1.8 ms       Q1
Total Cost           18,334       5,678        1,234        Q3
Rows (actual)        50,123       50,123       50,123       -
Buffers Shared       10,234       4,567        1,567        Q3
Buffers Hit          0%           45%          98%          Q3
Memory Usage         150 MB       80 MB        25 MB        Q3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 Winner: Query 3

Reasons:
✓ 15x faster execution (2,345 ms → 156 ms)
✓ 93% lower cost
✓ 85% less memory usage
✓ 98% cache hit rate

Query 3 Approach:
- Uses composite index on (user_id, status, created_at)
- Avoids sequential scans
- Leverages index-only scan
- Efficient cache utilization

Recommendation: Use Query 3 in production
```

## Best Practices

### Do's ✅

1. **Always EXPLAIN Before Optimizing**
   - Understand current performance
   - Identify bottlenecks
   - Measure improvement after changes

2. **Use EXPLAIN ANALYZE for Verification**
   - Get actual performance, not estimates
   - Verify optimizations work
   - Compare before/after metrics

3. **Add Indexes Strategically**
   - Index WHERE clause columns
   - Index JOIN columns
   - Index ORDER BY columns
   - Use composite indexes for multiple columns

4. **Monitor Query Performance**
   - Track slow queries
   - Set up alerts for regression
   - Review execution plans regularly

5. **Test with Production-Like Data**
   - Volume matters (1K vs 1M rows)
   - Data distribution affects plans
   - Test with realistic queries

6. **Keep Statistics Updated**
   ```sql
   ANALYZE table_name;
   ```
   - Helps planner make good decisions
   - Update after bulk changes

7. **Use Appropriate Join Types**
   - INNER JOIN when possible (faster)
   - LEFT JOIN only when needed
   - Consider join order

8. **Limit Result Sets**
   - Use WHERE to filter early
   - Add LIMIT when appropriate
   - Paginate large results

### Don'ts ❌

1. **Don't Optimize Without Measuring**
   - "Optimization" without data is guessing
   - Always EXPLAIN first
   - Verify improvements

2. **Don't Over-Index**
   - Indexes slow down writes
   - Take up disk space
   - Maintenance overhead
   - Use only needed indexes

3. **Don't Trust Estimates Blindly**
   - Use EXPLAIN ANALYZE for reality
   - Estimates can be wrong
   - Verify with actual execution

4. **Don't Ignore Index Maintenance**
   ```sql
   REINDEX TABLE table_name;
   VACUUM ANALYZE table_name;
   ```
   - Indexes degrade over time
   - Regular maintenance needed

5. **Don't Use SELECT \***
   - Fetches unnecessary columns
   - Prevents index-only scans
   - Use specific columns

6. **Don't Use Functions in WHERE**
   ```sql
   -- Bad (can't use index):
   WHERE UPPER(email) = 'TEST@EXAMPLE.COM'

   -- Good (can use index):
   WHERE email = 'test@example.com'
   ```

7. **Don't Ignore Query Cache**
   - Cached queries are instant
   - Configure cache appropriately
   - See [Query Cache Tutorial](./query-cache-tutorial.md)

8. **Don't Forget About Cost**
   - Indexes aren't free
   - Balance read vs write performance
   - Consider storage costs

## Troubleshooting

### Problem: Plan Differs from Expectations

**Symptom**: Expected index scan, got sequential scan

**Diagnosis:**

```bash
ai-shell explain "SELECT * FROM users WHERE email = 'test@example.com'"
```

**Output shows:**
```
Seq Scan on users  (cost=0..18334 rows=1000000)
  Filter: (email = 'test@example.com')
```

**Possible Causes:**

1. **Index doesn't exist:**
   ```sql
   -- Check indexes
   SELECT * FROM pg_indexes WHERE tablename = 'users';
   ```

2. **Statistics outdated:**
   ```sql
   -- Update statistics
   ANALYZE users;
   ```

3. **Index not selective enough:**
   - If query returns > 10% of rows, sequential scan might be faster
   - Check with EXPLAIN ANALYZE

4. **Wrong data type:**
   ```sql
   -- Index on VARCHAR, querying with TEXT
   CREATE INDEX idx_users_email ON users(email::TEXT);
   ```

### Problem: Slow Query After Adding Index

**Symptom**: Added index but query still slow

**Diagnosis:**

```bash
ai-shell explain "SELECT ..." --analyze --verbose
```

**Possible Causes:**

1. **Wrong column order in composite index:**
   ```sql
   -- Have: CREATE INDEX idx ON table(a, b, c);
   -- Query: WHERE c = 1 AND b = 2 AND a = 3
   -- Fix: CREATE INDEX idx ON table(c, b, a);
   ```

2. **Index too large:**
   ```sql
   -- Check index size
   SELECT pg_size_pretty(pg_relation_size('index_name'));
   ```

3. **Need to rebuild index:**
   ```sql
   REINDEX INDEX index_name;
   ```

### Problem: Different Plan in Production

**Symptom**: Query fast in dev, slow in production

**Possible Causes:**

1. **Different data distribution**
2. **Outdated statistics**
3. **Different configuration**
4. **Resource constraints (memory, CPU)**

**Solution:**

```bash
# Capture prod execution plan
ai-shell explain "SELECT ..." --analyze --production

# Compare with dev
ai-shell compare-plans dev-plan.json prod-plan.json
```

## Next Steps

### Advanced Topics

1. **[Cost Optimizer Tutorial](./cost-optimizer-tutorial.md)** - Reduce query costs
2. **[Query Cache Tutorial](./query-cache-tutorial.md)** - Cache query results
3. **[Performance Tuning Guide](./performance-tuning.md)** - Advanced optimization

### Related Tutorials

- **[Schema Diff](./schema-diff-tutorial.md)** - Schema comparison
- **[Migration Tester](./migration-tester-tutorial.md)** - Test schema changes

### API Reference

- **[Explain API](../../api/explain-api.md)**
- **[Optimization API](../../api/optimization-api.md)**

---

**Tutorial Version:** 1.0.0
**Last Updated:** 2025-10-30
**Estimated Time:** 85 minutes
**Difficulty:** Intermediate to Advanced

**License:** MIT
