# Cost Optimizer Tutorial

Learn how to analyze, reduce, and optimize database query costs to improve performance and reduce infrastructure expenses with AI-Shell's Cost Optimizer.

## Table of Contents

1. [What You'll Learn](#what-youll-learn)
2. [Prerequisites](#prerequisites)
3. [Part 1: Understanding Query Costs](#part-1-understanding-query-costs-10-min)
4. [Part 2: Cost Analysis Basics](#part-2-cost-analysis-basics-10-min)
5. [Part 3: Identifying Expensive Queries](#part-3-identifying-expensive-queries-15-min)
6. [Part 4: Cost Reduction Strategies](#part-4-cost-reduction-strategies-20-min)
7. [Part 5: Resource Optimization](#part-5-resource-optimization-15-min)
8. [Part 6: Cost Monitoring and Alerts](#part-6-cost-monitoring-and-alerts-10-min)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Next Steps](#next-steps)

## What You'll Learn

By the end of this tutorial, you will:

- Understand database query cost metrics
- Analyze query costs using AI-Shell
- Identify expensive queries and bottlenecks
- Apply cost reduction strategies
- Optimize resource utilization
- Set up cost monitoring and alerts
- Implement cost-aware query patterns
- Reduce infrastructure costs by 30-70%

**Estimated Time:** 80 minutes

## Prerequisites

Before starting this tutorial, ensure you have:

- AI-Shell installed and configured
- A database with production-like workload
- Basic understanding of SQL and query execution
- Access to query performance metrics
- 80 minutes of focused time

## Part 1: Understanding Query Costs (10 min)

### What Are Query Costs?

Query costs represent the computational resources required to execute a database query:

- **I/O Cost**: Disk reads and writes
- **CPU Cost**: Processing and computation
- **Memory Cost**: RAM usage for sorting, hashing, buffering
- **Network Cost**: Data transfer (for distributed databases)
- **Time Cost**: Total execution duration

### Cost Metrics Explained

**Cost Units:**
```
1.0 cost unit = Reading one 8KB page from disk
```

**Example Query Costs:**
```sql
-- Simple indexed lookup: 8 cost units (0.5ms)
SELECT * FROM users WHERE id = 123;

-- Full table scan: 18,334 cost units (2000ms)
SELECT * FROM users WHERE bio LIKE '%developer%';

-- Complex join: 250,000 cost units (30000ms)
SELECT * FROM orders o
JOIN users u ON o.user_id = u.id
JOIN products p ON o.product_id = p.id
WHERE o.created_at > '2025-01-01';
```

### Cost Breakdown Example

```
Query: SELECT * FROM orders WHERE status = 'pending'

Total Cost: 18,334.50 units

Breakdown:
  Seq Scan Cost:        18,000.00 (98.2%)  ← Primary bottleneck
  Filter Cost:           334.50 (1.8%)

Resource Usage:
  Disk I/O:             2,250 pages read (18 MB)
  CPU:                  1,000,000 row comparisons
  Memory:               5 MB buffer
  Time:                 2,345 ms

Cost in Real Terms:
  Database CPU:         $0.0012 per query
  Storage I/O:          $0.0003 per query
  Total:                $0.0015 per query

At 1M queries/day:    $1,500/day = $45,000/month
```

### Why Cost Optimization Matters

**Real-World Impact:**

1. **Infrastructure Costs**
   ```
   Before: $10,000/month database costs
   After:  $3,000/month (70% reduction)
   Savings: $84,000/year
   ```

2. **Performance**
   ```
   Before: 2000ms average query time
   After:  50ms average query time
   Improvement: 40x faster
   ```

3. **Scalability**
   ```
   Before: 100 queries/second max
   After:  4,000 queries/second max
   Scale: 40x more capacity
   ```

4. **User Experience**
   ```
   Before: 3-5 second page loads
   After:  <200ms page loads
   Result: Higher conversion rates, happier users
   ```

### Cost Optimization Goals

- **Reduce I/O**: Use indexes, avoid full table scans
- **Minimize CPU**: Simplify queries, push filtering to database
- **Optimize Memory**: Efficient joins, appropriate buffer sizes
- **Lower Network**: Reduce data transfer, use compression
- **Decrease Time**: Parallel execution, caching

## Part 2: Cost Analysis Basics (10 min)

### Analyzing a Single Query

Use AI-Shell to analyze query costs:

```bash
ai-shell cost-analyze "SELECT * FROM orders WHERE status = 'pending'"
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUERY COST ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query: SELECT * FROM orders WHERE status = 'pending'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COST SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Cost:           18,334.50 units
Execution Time:       2,345 ms
Cost Rating:          🔴 VERY HIGH

Cost per 1K queries:  $15.00
Cost per 1M queries:  $15,000.00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COST BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

I/O Cost:             18,000.00 (98.2%)  🔴 Critical
  - Pages Read:       2,250 pages (18 MB)
  - Sequential Scan:  1,000,000 rows

CPU Cost:             334.50 (1.8%)      ✓ Acceptable
  - Row Comparisons:  1,000,000
  - Filter Ops:       1,000,000

Memory Cost:          5 MB               ✓ Low
  - Buffers:          640 buffers
  - Work Mem:         5 MB

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOTTLENECKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Critical Issue: Sequential Scan

Operation:   Seq Scan on orders
Cost:        18,000.00 units (98.2% of total)
Impact:      Reading entire table (1M rows)
Reason:      No index on status column

Fix:         CREATE INDEX idx_orders_status ON orders(status);
Improvement: 99% cost reduction (18,334 → 200 units)
New Time:    ~50ms (47x faster)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COST PROJECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current State (1M queries/day):
  Daily Cost:          $15,000
  Monthly Cost:        $450,000
  Annual Cost:         $5,400,000

After Optimization (with index):
  Daily Cost:          $200
  Monthly Cost:        $6,000
  Annual Cost:         $72,000

Potential Savings:    $5,328,000/year (98.7% reduction)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apply optimization? [Y/n]:
```

### Cost Comparison

Compare costs across different query strategies:

```bash
ai-shell cost-compare query1.sql query2.sql query3.sql
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUERY COST COMPARISON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Comparing 3 query variants:

Query 1: Using LIKE pattern
Query 2: Using Full-Text Search
Query 3: Using Indexed Column

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Metric              Query 1      Query 2      Query 3      Best
─────────────────────────────────────────────────────────────────
Total Cost          25,000       5,000        150          Q3
Execution Time      3,200 ms     600 ms       25 ms        Q3
I/O Operations      3,125        625          20           Q3
CPU Usage           85%          30%          5%           Q3
Memory Usage        50 MB        25 MB        2 MB         Q3

Cost per 1K:        $25.00       $5.00        $0.15        Q3
Cost per 1M:        $25,000      $5,000       $150         Q3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 Winner: Query 3

Reasons:
✓ 167x lower cost than Query 1
✓ 128x faster execution
✓ 98% less I/O
✓ 94% less CPU usage
✓ 96% less memory

Recommendation: Use Query 3 approach with indexed column
```

### TypeScript API

```typescript
// cost-analysis.ts
import { AIShell } from 'ai-shell';

async function analyzeQueryCosts() {
  const shell = new AIShell();

  const analysis = await shell.cost.analyze({
    query: 'SELECT * FROM orders WHERE status = ?',
    params: ['pending'],
    database: 'production',
  });

  console.log('Cost Analysis:');
  console.log(`  Total Cost: ${analysis.totalCost} units`);
  console.log(`  Execution Time: ${analysis.executionTime}ms`);
  console.log(`  Cost Rating: ${analysis.rating}`);
  console.log();

  console.log('Cost Breakdown:');
  console.log(`  I/O: ${analysis.ioCost} units (${analysis.ioPercentage}%)`);
  console.log(`  CPU: ${analysis.cpuCost} units (${analysis.cpuPercentage}%)`);
  console.log(`  Memory: ${analysis.memoryCost} MB`);
  console.log();

  console.log('Bottlenecks:');
  analysis.bottlenecks.forEach((bottleneck, i) => {
    console.log(`  ${i + 1}. ${bottleneck.type}: ${bottleneck.description}`);
    console.log(`     Cost: ${bottleneck.cost} units`);
    console.log(`     Fix: ${bottleneck.recommendation}`);
  });

  console.log();
  console.log('Financial Impact:');
  console.log(`  Cost per 1K queries: $${analysis.costPer1K.toFixed(2)}`);
  console.log(`  Cost per 1M queries: $${analysis.costPer1M.toFixed(2)}`);
  console.log(`  Monthly cost (1M queries/day): $${analysis.monthlyCost.toFixed(2)}`);

  if (analysis.optimizations.length > 0) {
    console.log();
    console.log('Optimizations:');
    analysis.optimizations.forEach((opt, i) => {
      console.log(`  ${i + 1}. ${opt.title}`);
      console.log(`     Savings: $${opt.annualSavings.toFixed(2)}/year`);
      console.log(`     SQL: ${opt.sql}`);
    });
  }
}

analyzeQueryCosts().catch(console.error);
```

## Part 3: Identifying Expensive Queries (15 min)

### Finding Top Expensive Queries

Identify the costliest queries in your database:

```bash
ai-shell cost-top-queries --limit 10 --period 24h
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOP 10 EXPENSIVE QUERIES (Last 24 hours)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Queries Analyzed: 15,432,567
Total Cost: $23,456
Average Cost per Query: $0.0015

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. SELECT * FROM orders WHERE status = 'pending'

   Executions:       45,678  (3,156/hour)
   Avg Cost:         18,334 units
   Avg Time:         2,345 ms
   Total Cost:       $684 (29.2% of total)

   Issue:            Sequential scan on 1M rows
   Fix:              CREATE INDEX idx_orders_status ON orders(status);
   Savings:          $675/day ($246,375/year)
   Priority:         🔴 Critical

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. Complex report query with multiple JOINs

   Executions:       2,345   (162/hour)
   Avg Cost:         156,000 units
   Avg Time:         18,234 ms
   Total Cost:       $366 (15.6% of total)

   Issue:            5-table JOIN without proper indexes
   Fix:              Add composite indexes on join columns
   Savings:          $350/day ($127,750/year)
   Priority:         🔴 Critical

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. User activity aggregation

   Executions:       12,345  (854/hour)
   Avg Cost:         25,000 units
   Avg Time:         3,456 ms
   Total Cost:       $309 (13.2% of total)

   Issue:            Aggregating over large dataset
   Fix:              Create materialized view
   Savings:          $295/day ($107,675/year)
   Priority:         🔴 Critical

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. Product search with LIKE

   Executions:       89,234  (6,176/hour)
   Avg Cost:         8,500 units
   Avg Time:         1,234 ms
   Total Cost:       $234 (10.0% of total)

   Issue:            Full-text search on unindexed column
   Fix:              Create GIN index for full-text search
   Savings:          $220/day ($80,300/year)
   Priority:         🟡 High

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[6 more queries...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY

Top 10 queries account for:
  75.2% of total database cost ($17,634/day)
  52.3% of total query time
  68.9% of I/O operations

Optimizing these 10 queries could save:
  $16,500/day
  $6,022,500/year (78% cost reduction)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate optimization plan? [Y/n]:
```

### Cost Distribution Analysis

Understand where costs are concentrated:

```bash
ai-shell cost-distribution --by table,operation --period 7d
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COST DISTRIBUTION (Last 7 days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Cost: $164,192

By Table:
╔════════════════╦══════════╦═══════════╦════════════╗
║ Table          ║ Cost     ║ Queries   ║ % of Total ║
╠════════════════╬══════════╬═══════════╬════════════╣
║ orders         ║ $65,677  ║ 5,432,876 ║ 40.0%      ║
║ products       ║ $32,838  ║ 8,765,432 ║ 20.0%      ║
║ users          ║ $24,629  ║ 3,456,789 ║ 15.0%      ║
║ audit_logs     ║ $16,419  ║ 12,345,678║ 10.0%      ║
║ analytics      ║ $12,315  ║ 456,789   ║ 7.5%       ║
║ Other (23)     ║ $12,314  ║ 2,987,654 ║ 7.5%       ║
╚════════════════╩══════════╩═══════════╩════════════╝

By Operation:
╔════════════════╦══════════╦═══════════╦════════════╗
║ Operation      ║ Cost     ║ Queries   ║ % of Total ║
╠════════════════╬══════════╬═══════════╬════════════╣
║ SELECT         ║ $131,354 ║ 28,765,432║ 80.0%      ║
║ INSERT         ║ $16,419  ║ 3,456,789 ║ 10.0%      ║
║ UPDATE         ║ $9,851   ║ 1,234,567 ║ 6.0%       ║
║ DELETE         ║ $6,568   ║ 456,789   ║ 4.0%       ║
╚════════════════╩══════════╩═══════════╩════════════╝

By Query Pattern:
╔════════════════════════╦══════════╦══════════╗
║ Pattern                ║ Cost     ║ Avg Cost ║
╠════════════════════════╬══════════╬══════════╣
║ Full table scans       ║ $82,096  ║ 18,334   ║
║ Multi-table JOINs      ║ $32,838  ║ 45,678   ║
║ Aggregations           ║ $24,629  ║ 12,345   ║
║ Indexed lookups        ║ $16,419  ║ 234      ║
║ Other                  ║ $8,210   ║ 1,234    ║
╚════════════════════════╩══════════╩══════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key Findings:

🔴 50% of costs from full table scans
   → Add indexes to eliminate sequential scans

🟡 20% of costs from multi-table JOINs
   → Optimize join strategies and add composite indexes

✓ Only 10% of costs from indexed lookups
   → This is good, but could be higher

Optimization Potential: $123,000/week (75% reduction)
```

### Query Cost Trends

Track cost trends over time:

```bash
ai-shell cost-trends --period 30d --interval daily
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COST TRENDS (Last 30 days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Daily Cost Trend:

$8,000 │                                           ╭─╮
       │                                     ╭─────╯ ╰─╮
$7,000 │                               ╭─────╯         ╰─╮
       │                         ╭─────╯                 │
$6,000 │                   ╭─────╯                       │
       │             ╭─────╯                             │
$5,000 │       ╭─────╯                                   ╰─╮
       │ ╭─────╯                                           │
$4,000 │─╯                                                 ╰─
       └──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──
         Oct 1    5     10    15    20    25    30

Average Daily Cost: $6,140
Trend: ↗ Increasing (+42% over 30 days)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cost Spikes Detected:

1. Oct 18 - Oct 20: +85% spike
   Cause: New feature launched without indexes
   Cost: $15,234 (3 days)
   Status: ⚠️  Still elevated

2. Oct 25: +120% spike
   Cause: Report generation query
   Cost: $8,567 (1 day)
   Status: ✓ Resolved

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Projections:

If trend continues:
  Nov 30:  $8,723/day
  Dec 31:  $12,386/day

Annual projection: $3,661,050

With optimization:
  Stabilized cost: $1,500/day
  Annual: $547,500
  Savings: $3,113,550/year
```

## Part 4: Cost Reduction Strategies (20 min)

### Strategy 1: Add Indexes

**Most effective cost reduction technique**

```sql
-- Before: Sequential scan (18,334 cost)
SELECT * FROM orders WHERE status = 'pending';

-- Add index
CREATE INDEX idx_orders_status ON orders(status);

-- After: Index scan (200 cost)
-- Improvement: 99% cost reduction
```

**Composite Indexes for Multiple Columns:**

```sql
-- Query with multiple filters
SELECT * FROM orders
WHERE user_id = 123
  AND status = 'pending'
  AND created_at > '2025-01-01'
ORDER BY created_at DESC;

-- Optimal composite index
CREATE INDEX idx_orders_user_status_date
ON orders(user_id, status, created_at DESC);

-- Result:
-- Before: 25,000 cost
-- After:  150 cost
-- Savings: 99.4%
```

### Strategy 2: Query Rewriting

**Optimize query structure**

```sql
-- Before: Subquery executed per row (500,000 cost)
SELECT *
FROM products p
WHERE (
  SELECT COUNT(*)
  FROM orders o
  WHERE o.product_id = p.id
) > 100;

-- After: JOIN with GROUP BY (5,000 cost)
SELECT DISTINCT p.*
FROM products p
JOIN (
  SELECT product_id
  FROM orders
  GROUP BY product_id
  HAVING COUNT(*) > 100
) o ON p.id = o.product_id;

-- Savings: 99% cost reduction
```

### Strategy 3: Materialized Views

**Pre-compute expensive aggregations**

```sql
-- Expensive query run 1000x/day (1M cost each)
SELECT
  category,
  COUNT(*) as product_count,
  AVG(price) as avg_price,
  SUM(sales) as total_sales
FROM products
GROUP BY category;

-- Create materialized view
CREATE MATERIALIZED VIEW mv_category_stats AS
SELECT
  category,
  COUNT(*) as product_count,
  AVG(price) as avg_price,
  SUM(sales) as total_sales
FROM products
GROUP BY category;

-- Refresh daily
CREATE INDEX idx_mv_category_stats_category
ON mv_category_stats(category);

-- Query the view (100 cost)
SELECT * FROM mv_category_stats WHERE category = 'Electronics';

-- Savings:
-- Before: 1M cost × 1000 queries = 1B cost/day
-- After:  100 cost × 1000 queries + 1M refresh = 101M cost/day
-- Reduction: 90% (saves $900/day)
```

### Strategy 4: Partitioning

**Partition large tables**

```sql
-- Large audit_logs table (100M rows)
-- Query: SELECT * FROM audit_logs WHERE created_at > '2025-01-01'
-- Cost: 500,000 (scans entire table)

-- Partition by date
CREATE TABLE audit_logs_2025_01 PARTITION OF audit_logs
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE audit_logs_2025_02 PARTITION OF audit_logs
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Query now only scans relevant partition (5,000 cost)
-- Savings: 99% cost reduction
```

### Strategy 5: Caching

**Cache frequently accessed data**

```sql
-- Expensive query executed 10,000x/day (25,000 cost)
SELECT * FROM products WHERE featured = true;

-- Enable caching with 1 hour TTL
-- First query: 25,000 cost
-- Next 9,999 queries: 1 cost (cached)

-- Savings:
-- Before: 25,000 × 10,000 = 250M cost/day
-- After:  25,000 + (9,999 × 1) = 35,000 cost/day
-- Reduction: 99.986% (saves $2,500/day)
```

See [Query Cache Tutorial](./query-cache-tutorial.md) for details.

### Strategy 6: Limit Result Sets

**Only fetch needed data**

```sql
-- Before: Fetch all rows (100,000 cost)
SELECT * FROM products ORDER BY created_at DESC;

-- After: Limit to needed rows (1,000 cost)
SELECT * FROM products ORDER BY created_at DESC LIMIT 100;

-- Savings: 99% cost reduction

-- Also select only needed columns
-- Before:
SELECT * FROM products WHERE category = 'Electronics';

-- After:
SELECT id, name, price FROM products WHERE category = 'Electronics';

-- Benefit: Smaller data transfer, less memory, faster
```

### Strategy 7: Optimize JOINs

**Choose efficient join strategies**

```sql
-- Before: Nested loop join (5M cost)
SELECT *
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.status = 'pending';

-- Add indexes on join columns
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_users_id ON users(id);  -- Usually exists

-- Filter before joining
SELECT *
FROM (
  SELECT * FROM orders WHERE status = 'pending'
) o
JOIN users u ON o.user_id = u.id;

-- After: Hash join with filter (50K cost)
-- Savings: 99% cost reduction
```

### Strategy 8: Batch Operations

**Group operations together**

```sql
-- Before: 1000 individual INSERTs (10,000 cost each)
INSERT INTO logs (message) VALUES ('log 1');
INSERT INTO logs (message) VALUES ('log 2');
-- ... 998 more

-- Total cost: 10M

-- After: Batch INSERT (50,000 cost)
INSERT INTO logs (message) VALUES
  ('log 1'),
  ('log 2'),
  ('log 3'),
  -- ... all 1000 rows
  ('log 1000');

-- Savings: 99.5% cost reduction
```

### Automated Cost Optimization

Let AI-Shell optimize automatically:

```bash
ai-shell cost-optimize --auto --dry-run
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTOMATED COST OPTIMIZATION (DRY RUN)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyzing workload...
✓ Found 23 optimization opportunities

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recommended Actions:

1. Create 8 new indexes
   Cost: $0 (one-time: 2 minutes)
   Savings: $12,500/day

2. Create 3 materialized views
   Cost: $50/day (refresh)
   Savings: $3,200/day

3. Enable query caching (15 queries)
   Cost: $100/day (cache storage)
   Savings: $4,800/day

4. Partition 2 large tables
   Cost: $0 (one-time: 30 minutes)
   Savings: $2,100/day

5. Rewrite 4 inefficient queries
   Cost: Developer time (2 hours)
   Savings: $1,800/day

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Current Cost:     $23,456/day
Total Optimized Cost:   $3,106/day
Net Savings:            $20,350/day
Annual Savings:         $7,427,750

ROI: 36,500% (pays back in < 1 hour)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apply optimizations? [Y/n/select]:
```

## Part 5: Resource Optimization (15 min)

### CPU Optimization

Reduce CPU usage:

```bash
ai-shell cost-optimize-cpu
```

**Techniques:**

1. **Push filtering to database**
   ```typescript
   // ❌ Bad: Filter in application (high CPU)
   const allUsers = await db.query('SELECT * FROM users');
   const activeUsers = allUsers.filter(u => u.active);

   // ✅ Good: Filter in database (low CPU)
   const activeUsers = await db.query('SELECT * FROM users WHERE active = true');
   ```

2. **Use appropriate data types**
   ```sql
   -- ❌ Bad: String comparison (slow)
   status VARCHAR(20)
   WHERE status = 'active'

   -- ✅ Good: Enum (fast)
   status status_enum
   WHERE status = 'active'::status_enum
   ```

3. **Avoid expensive functions in WHERE**
   ```sql
   -- ❌ Bad: Function prevents index use
   WHERE UPPER(email) = 'TEST@EXAMPLE.COM'

   -- ✅ Good: Case-insensitive index
   CREATE INDEX idx_users_email_lower ON users(LOWER(email));
   WHERE LOWER(email) = 'test@example.com'
   ```

### Memory Optimization

Reduce memory usage:

```sql
-- Configure work_mem appropriately
SET work_mem = '64MB';  -- For sorting/hashing

-- Use streaming for large results
DECLARE cursor CURSOR FOR
SELECT * FROM large_table;

FETCH 1000 FROM cursor;  -- Process in batches

-- Avoid loading everything into memory
SELECT * FROM huge_table LIMIT 1000 OFFSET 0;  -- Paginate
```

### I/O Optimization

Reduce disk I/O:

**Techniques:**

1. **Index-only scans**
   ```sql
   CREATE INDEX idx_users_email_name ON users(email, name);

   SELECT email, name FROM users WHERE email = 'test@example.com';
   -- Uses index-only scan (no table access)
   ```

2. **Covering indexes**
   ```sql
   CREATE INDEX idx_orders_covering
   ON orders(user_id) INCLUDE (status, total, created_at);

   SELECT status, total, created_at
   FROM orders
   WHERE user_id = 123;
   -- All data from index
   ```

3. **Reduce row width**
   ```sql
   -- Only select needed columns
   SELECT id, name, price FROM products;
   -- Not: SELECT * FROM products;
   ```

### Network Optimization

Reduce data transfer:

```typescript
// ❌ Bad: Transfer all data
const users = await db.query('SELECT * FROM users');
const userNames = users.map(u => u.name);

// ✅ Good: Transfer only needed data
const users = await db.query('SELECT name FROM users');

// ❌ Bad: Multiple round trips
for (const id of userIds) {
  const user = await db.query('SELECT * FROM users WHERE id = ?', [id]);
}

// ✅ Good: Single query
const users = await db.query('SELECT * FROM users WHERE id = ANY(?)', [userIds]);
```

### Resource Monitoring

Monitor resource usage:

```bash
ai-shell cost-monitor-resources --real-time
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESOURCE USAGE MONITOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CPU Usage:
████████████████████░░░░░░░░░░░░░░░░  45%

Top CPU Consumers:
1. Query: SELECT * FROM orders ...        25%
2. Query: Complex JOIN ...                12%
3. Index maintenance                      8%

Memory Usage:
████████████████████████████░░░░░░  75% (12 GB / 16 GB)

Top Memory Consumers:
1. Sorting: ORDER BY created_at           3.2 GB
2. Hash Join: orders × users              2.8 GB
3. Query cache                            2.1 GB

Disk I/O:
████████████████░░░░░░░░░░░░░░░░░░  40% (800 IOPS / 2000 max)

Top I/O Consumers:
1. Sequential scan: audit_logs            450 IOPS
2. Index scan: products                   200 IOPS
3. WAL writes                             150 IOPS

Network:
████████░░░░░░░░░░░░░░░░░░░░░░░░░░  20% (200 Mbps / 1 Gbps)

Top Bandwidth Consumers:
1. Result transfer: large reports         120 Mbps
2. Replication                            50 Mbps
3. Query submissions                      30 Mbps

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  Alerts:
- Memory usage high (75%) - consider tuning work_mem
- Sequential scan on audit_logs causing high I/O

Press 'q' to quit, 'r' to refresh
```

## Part 6: Cost Monitoring and Alerts (10 min)

### Set Up Cost Alerts

Configure alerts for cost anomalies:

```bash
ai-shell cost-alerts setup
```

**Configuration:**

```typescript
// cost-alerts-config.ts
export const alertConfig = {
  alerts: [
    {
      name: 'high-cost-query',
      condition: 'cost > 50000',
      severity: 'critical',
      notification: ['email', 'slack'],
      message: 'Query cost exceeds 50,000 units',
    },
    {
      name: 'daily-cost-spike',
      condition: 'daily_cost > avg(daily_cost, 7d) * 1.5',
      severity: 'warning',
      notification: ['slack'],
      message: 'Daily cost 50% above 7-day average',
    },
    {
      name: 'cost-budget-exceeded',
      condition: 'monthly_cost > 10000',
      severity: 'critical',
      notification: ['email', 'slack', 'pagerduty'],
      message: 'Monthly cost budget exceeded ($10,000)',
    },
  ],

  notifications: {
    email: {
      recipients: ['dba-team@example.com', 'devops@example.com'],
    },
    slack: {
      webhook: process.env.SLACK_WEBHOOK_URL,
      channel: '#database-alerts',
    },
    pagerduty: {
      integrationKey: process.env.PAGERDUTY_KEY,
    },
  },

  checks: {
    interval: '5m',  // Check every 5 minutes
    enabled: true,
  },
};
```

### Cost Dashboard

Create a real-time cost dashboard:

```bash
ai-shell cost-dashboard --port 3000
```

Opens dashboard at http://localhost:3000:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              DATABASE COST DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Real-Time Metrics:

Current Cost Rate:    $6.50/hour
Daily Projection:     $156/day
Monthly Projection:   $4,680/month

Cost vs. Budget:
████████████████░░░░  80% ($4,680 / $5,850)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Live Queries (Top 5 by Cost):

1. ⚠️  Report generation
   Cost: 156K units | Time: 18s | Status: Running

2. Order status check
   Cost: 18K units | Time: 2.3s | Executions: 234/min

3. User profile fetch
   Cost: 8K units | Time: 1.1s | Executions: 1,234/min

4. Product search
   Cost: 5K units | Time: 0.6s | Executions: 456/min

5. Category aggregation
   Cost: 3K units | Time: 0.4s | Executions: 89/min

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cost History (Last 24 hours):

$200 │     ╭─╮
     │   ╭─╯ ╰─╮     ╭─╮
$150 │ ╭─╯     ╰─╮ ╭─╯ ╰─╮
     │─╯         ╰─╯     ╰──────
$100 └─┬───┬───┬───┬───┬───┬───
       0h  4h  8h  12h 16h 20h 24h

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Optimization Opportunities:

🔴 3 critical issues - Save $2,100/day
🟡 5 high priority - Save $800/day
🟢 12 low priority - Save $200/day

[View Details] [Apply Fixes] [Export Report]
```

### Cost Reporting

Generate cost reports:

```bash
ai-shell cost-report --period monthly --format pdf --output cost-report-oct-2025.pdf
```

**Report Contents:**

- Executive summary
- Cost breakdown by table, query, operation
- Trends and forecasts
- Optimization recommendations
- ROI analysis
- Detailed query analysis

## Best Practices

### Do's ✅

1. **Monitor Costs Regularly**
   - Set up daily cost reports
   - Track trends and anomalies
   - Review top expensive queries weekly

2. **Optimize High-Impact Queries First**
   - Focus on queries with highest total cost
   - Consider both per-query cost and frequency
   - Optimize the top 10 queries (80/20 rule)

3. **Use Appropriate Indexes**
   - Index WHERE clause columns
   - Create composite indexes for multiple filters
   - Use covering indexes when possible

4. **Cache Frequently Accessed Data**
   - Cache expensive queries
   - Set appropriate TTLs
   - Monitor cache hit rates

5. **Set Cost Budgets and Alerts**
   - Define acceptable cost thresholds
   - Alert on cost spikes
   - Review budget vs actual monthly

6. **Test Before Production**
   - Analyze query costs in development
   - Load test with production-like data
   - Verify optimizations work

7. **Document Optimizations**
   - Track what was changed and why
   - Measure improvement
   - Share learnings with team

8. **Continuously Optimize**
   - Review costs regularly
   - Optimize as data grows
   - Stay proactive, not reactive

### Don'ts ❌

1. **Don't Ignore Small Frequent Queries**
   - Small cost × high frequency = expensive
   - Optimize frequently executed queries
   - Consider cumulative cost

2. **Don't Over-Index**
   - Indexes have maintenance cost
   - Balance read vs write performance
   - Remove unused indexes

3. **Don't Fetch Unnecessary Data**
   - Avoid SELECT *
   - Use LIMIT appropriately
   - Only fetch needed columns

4. **Don't Run Expensive Queries in Loops**
   - Batch operations when possible
   - Use JOINs instead of N+1 queries
   - Consider materialized views

5. **Don't Ignore Cost Trends**
   - Rising costs indicate problems
   - Address issues early
   - Don't let costs spiral

6. **Don't Optimize Without Measuring**
   - Always measure before and after
   - Verify improvements
   - Track ROI

7. **Don't Skip Cost Analysis for New Features**
   - Analyze queries before deployment
   - Add indexes proactively
   - Avoid costly surprises

8. **Don't Forget About Writes**
   - Optimize INSERT/UPDATE/DELETE too
   - Batch writes when possible
   - Consider write-heavy indexes

## Troubleshooting

### Problem: Costs Keep Rising

**Solutions:**

1. **Identify the cause**
   ```bash
   ai-shell cost-trends --period 30d
   ai-shell cost-top-queries --period 24h
   ```

2. **Check for new queries**
   ```bash
   ai-shell cost-analyze --new-queries --since 7d
   ```

3. **Look for data growth**
   ```bash
   ai-shell cost-by-table --show-growth
   ```

### Problem: Optimization Didn't Help

**Solutions:**

1. **Verify index is being used**
   ```bash
   ai-shell explain "SELECT ..." --analyze
   ```

2. **Check statistics are up-to-date**
   ```sql
   ANALYZE table_name;
   ```

3. **Try different optimization**
   ```bash
   ai-shell cost-analyze "SELECT ..." --all-strategies
   ```

## Next Steps

### Related Tutorials

- **[Query Cache](./query-cache-tutorial.md)** - Cache expensive queries
- **[SQL Explainer](./sql-explainer-tutorial.md)** - Understand query plans
- **[Migration Tester](./migration-tester-tutorial.md)** - Test schema changes

### Advanced Topics

- **[Cost Modeling Guide](../advanced/cost-modeling.md)**
- **[Performance Tuning](../advanced/performance-tuning.md)**
- **[Cloud Cost Optimization](../advanced/cloud-costs.md)**

---

**Tutorial Version:** 1.0.0
**Last Updated:** 2025-10-30
**Estimated Time:** 80 minutes
**Difficulty:** Intermediate to Advanced

**License:** MIT
