# Query Optimization Tutorial

> **📋 Implementation Status**
>
> **Current Status:** In Development
> **CLI Availability:** Partial
> **Completeness:** 28%
>
> **What Works Now:**
> - Basic query execution
> - Database connection management
> - Manual query analysis
>
> **Coming Soon:**
> - Automatic slow query detection
> - AI-powered optimization recommendations
> - Index management and suggestions
> - Execution plan analysis
> - Batch optimization capabilities
> - Auto-optimization features
>
> **Note:** This tutorial describes the intended functionality. Check the [Gap Analysis Report](../FEATURE_GAP_ANALYSIS_REPORT.md) for detailed implementation status.

## Introduction and Overview

AI-Shell's intelligent query optimization is a game-changer for database performance. Instead of manually analyzing query execution plans and testing index strategies, AI-Shell automatically identifies performance bottlenecks and applies optimizations that can make your queries 10-100x faster.

This tutorial will teach you how to:
- Automatically optimize slow queries
- Understand optimization recommendations
- Apply and manage database indexes
- Monitor query performance improvements
- Configure auto-optimization features
- Learn from optimization patterns

**What You'll Learn:**
- Query performance analysis
- Automatic query rewriting
- Index recommendations and creation
- Execution plan interpretation
- Performance monitoring and tracking
- Self-learning optimization strategies

**Time to Complete:** 30-40 minutes

---

## Prerequisites

Before starting this tutorial, ensure you have:

### Required
- AI-Shell installed (v1.0.0 or higher)
  ```bash
  npm install -g ai-shell
  ```
- Database connection configured with write permissions (for index creation)
  ```bash
  ai-shell connect postgres://user:pass@localhost:5432/mydb
  ```
- Anthropic API key configured
  ```bash
  export ANTHROPIC_API_KEY="your-api-key"
  ```

### Recommended
- A database with realistic data volume (1000+ records for meaningful optimization)
- Access to database statistics and execution plans
- Understanding of basic database concepts (indexes, query plans)
- Development/staging environment for testing optimizations

### Verify Your Setup
```bash
# Check optimization features are available
ai-shell features check optimization
# Expected: ✓ Optimization features enabled

# Verify database permissions
ai-shell check-permissions --feature optimize
# Expected: ✓ Read access, ✓ Index creation, ✓ Statistics access

# Test basic optimization
ai-shell optimize "SELECT * FROM users LIMIT 10" --dry-run
# Should show analysis without applying changes
```

---

## Step-by-Step Instructions

### Step 1: Identifying Slow Queries

Before optimizing, identify which queries need attention.

```bash
# View slowest queries from recent history
ai-shell slow-queries

# Output shows:
# 📊 Slow Queries Report
#
# 1. Query: SELECT * FROM orders WHERE status = 'pending'
#    Average Time: 2,847ms
#    Executions: 1,247
#    Total Time: 59 minutes
#    Impact: HIGH
#
# 2. Query: SELECT users.*, COUNT(orders.id) FROM users LEFT JOIN orders...
#    Average Time: 1,523ms
#    Executions: 892
#    Total Time: 23 minutes
#    Impact: HIGH

# Filter by minimum execution time
ai-shell slow-queries --threshold 1000ms

# Show queries from specific time range
ai-shell slow-queries --last 24h

# Export slow queries report
ai-shell slow-queries --export slow-queries-report.json
```

**Understanding the Output:**
- **Average Time**: Mean execution time per query
- **Executions**: Number of times query was run
- **Total Time**: Cumulative time spent on this query
- **Impact**: HIGH/MEDIUM/LOW based on total time and frequency

---

### Step 2: Your First Query Optimization

Let's optimize a slow query step by step.

```bash
# Start with a slow query
ai-shell query "SELECT * FROM orders WHERE status = 'pending'"
# Execution time: 2,847ms

# Run optimization analysis
ai-shell optimize "SELECT * FROM orders WHERE status = 'pending'"

# AI-Shell analyzes and responds:
# 🔍 Analyzing query performance...
#
# Performance Issues Detected:
# ❌ Full table scan on 'orders' (1.2M rows)
# ❌ No index on 'status' column
# ⚠️ SELECT * retrieves unnecessary columns
#
# Optimization Recommendations:
# 1. Add index on status column (estimated 95% speedup)
# 2. Select only needed columns (estimated 40% data reduction)
#
# Optimized Query:
# CREATE INDEX idx_orders_status ON orders(status);
# SELECT id, customer_id, total, created_at
# FROM orders
# WHERE status = 'pending';
#
# Apply optimization? [y/N]
```

**Applying the Optimization:**
```bash
# Apply recommended optimization
y

# Output:
# ✓ Creating index idx_orders_status...
# ✓ Index created successfully
# ✓ Re-running query with optimized version...
#
# Results:
# Before: 2,847ms
# After: 34ms
# Improvement: 98.8% faster (83.7x speedup)
#
# ✓ Optimization saved 2,813ms per execution
# ✓ With 1,247 daily executions, saves ~59 minutes/day
```

---

### Step 3: Understanding Optimization Types

AI-Shell applies multiple optimization techniques.

#### A. Index Optimization

```bash
# Missing index detection
ai-shell optimize "SELECT * FROM users WHERE email = 'john@example.com'"

# Recommendation: Add index on frequently filtered columns
# CREATE INDEX idx_users_email ON users(email);

# Composite index for multi-column filters
ai-shell optimize "SELECT * FROM orders WHERE status = 'pending' AND created_at > NOW() - INTERVAL '7 days'"

# Recommendation: Composite index on both columns
# CREATE INDEX idx_orders_status_created ON orders(status, created_at);
```

#### B. Query Rewriting

```bash
# Original inefficient query
ai-shell optimize "SELECT * FROM orders WHERE YEAR(created_at) = 2025"

# Rewritten query:
# -- Original prevents index usage
# -- Rewritten to be index-friendly:
# SELECT * FROM orders
# WHERE created_at >= '2025-01-01'
#   AND created_at < '2026-01-01';
```

#### C. Join Optimization

```bash
# Suboptimal join order
ai-shell optimize "
  SELECT u.name, o.total
  FROM orders o
  JOIN users u ON o.user_id = u.id
  WHERE o.status = 'completed'
"

# Optimized with filter pushdown:
# SELECT u.name, o.total
# FROM (
#   SELECT user_id, total
#   FROM orders
#   WHERE status = 'completed'
# ) o
# JOIN users u ON o.user_id = u.id;
```

#### D. Column Selection Optimization

```bash
# Inefficient SELECT *
ai-shell optimize "SELECT * FROM users WHERE active = true"

# Recommendation:
# "SELECT * retrieves 23 columns (including large text fields)
#  Specify only needed columns for 78% data reduction"
#
# Suggested:
# SELECT id, name, email, created_at FROM users WHERE active = true;
```

---

### Step 4: Batch Optimization

Optimize multiple queries at once for maximum impact.

```bash
# Analyze and optimize all slow queries
ai-shell optimize-all --threshold 500ms

# Output:
# 🔍 Found 15 queries over 500ms threshold
#
# Analyzing optimizations...
# ✓ 15/15 queries analyzed
#
# Optimization Plan:
# - 8 indexes to create
# - 12 queries to rewrite
# - Estimated total impact: 4.2 hours/day saved
#
# Apply all optimizations? [y/N]

# Apply selectively
ai-shell optimize-all --threshold 500ms --interactive

# Review each optimization before applying
# 1/15: Create index on orders.status? [y/n/s(kip all)]
```

---

### Step 5: Index Management

Manage database indexes effectively.

```bash
# List all indexes
ai-shell indexes list

# Output:
# 📊 Database Indexes
#
# Table: orders
# - idx_orders_status (status) - 1.2M rows, 45MB
# - idx_orders_created (created_at) - 1.2M rows, 52MB
# - idx_orders_user_id (user_id) - 1.2M rows, 48MB
#
# Table: users
# - idx_users_email (email) - 450K rows, 28MB
# - idx_users_created (created_at) - 450K rows, 31MB

# Analyze index usage
ai-shell indexes analyze

# Output:
# 📊 Index Usage Analysis
#
# Highly Used:
# ✓ idx_orders_status - 12,847 scans/day
# ✓ idx_users_email - 8,234 scans/day
#
# Rarely Used:
# ⚠️ idx_orders_archived - 3 scans/day (consider removing)
# ⚠️ idx_users_legacy_id - 0 scans/day (consider removing)
#
# Recommended New Indexes:
# + idx_orders_status_created (composite) - would improve 234 queries

# Remove unused indexes
ai-shell indexes remove idx_orders_archived

# Create recommended indexes
ai-shell indexes apply-recommendations
```

---

### Step 6: Understanding Execution Plans

Learn to read and interpret query execution plans.

```bash
# View execution plan for a query
ai-shell explain "SELECT * FROM orders WHERE status = 'pending'"

# Output (formatted for readability):
# 📊 Query Execution Plan
#
# Seq Scan on orders  (cost=0.00..25847.00 rows=1200 width=128)
#   Filter: (status = 'pending')
#   Rows: 1,247 actual
#   Time: 2,847ms
#
# 🔍 Analysis:
# ❌ Sequential Scan (reads entire table)
# ❌ 1.2M rows scanned to find 1,247 matches
# ⚡ Adding index would enable Index Scan (100x faster)

# Compare before/after optimization
ai-shell explain "SELECT * FROM orders WHERE status = 'pending'" --compare-optimized

# Shows side-by-side comparison:
# BEFORE                          AFTER
# Seq Scan (2,847ms)       →      Index Scan (34ms)
# 1.2M rows scanned        →      1,247 rows scanned
# cost=25847               →      cost=287
```

**Key Execution Plan Terms:**
- **Seq Scan**: Full table scan (slow for large tables)
- **Index Scan**: Using index (fast)
- **Cost**: Database's estimate of query expense
- **Rows**: Estimated vs actual rows processed
- **Width**: Average row size in bytes

---

### Step 7: Auto-Optimization Features

Enable AI-Shell to optimize queries automatically.

```bash
# Enable auto-optimization
ai-shell config set auto-optimize.enabled true

# Configure auto-optimization thresholds
ai-shell config set auto-optimize.threshold 1000ms
ai-shell config set auto-optimize.minExecutions 10

# Set approval mode
ai-shell config set auto-optimize.mode interactive
# Options: interactive (ask before applying), automatic (apply all), suggest (notify only)

# View auto-optimization activity
ai-shell auto-optimize status

# Output:
# 🤖 Auto-Optimization Status
#
# Status: Enabled
# Mode: Interactive
# Threshold: 1000ms
# Min Executions: 10
#
# Activity (Last 7 Days):
# - 23 optimizations detected
# - 18 applied (78%)
# - 5 pending approval
# - Average improvement: 12.3x faster
#
# Pending Approvals:
# 1. orders.status index (estimated 15.2x speedup)
# 2. Query rewrite for date filtering (estimated 3.4x speedup)
# [Review: ai-shell auto-optimize review]

# Review and approve pending optimizations
ai-shell auto-optimize review
```

---

### Step 8: Performance Monitoring

Track optimization impact over time.

```bash
# View performance dashboard
ai-shell performance dashboard

# Output:
# 📊 Performance Dashboard
#
# Query Performance (Last 30 Days):
# Average Query Time: 234ms (↓ 78% from last period)
# Slowest Query: 1,523ms (was 12,847ms)
# Total Queries: 127,483
#
# Optimizations Applied:
# ✓ 45 indexes created
# ✓ 127 queries rewritten
# ✓ 12 unused indexes removed
#
# Impact:
# ⚡ Time saved: 142 hours
# 💰 Cost reduced: $1,247 (estimated infrastructure)
# 📈 Performance improvement: 12.3x average speedup
#
# Top Optimizations:
# 1. idx_orders_status - saved 59 min/day
# 2. Query rewrite for user search - saved 23 min/day
# 3. idx_products_category - saved 18 min/day

# Export performance report
ai-shell performance report --export performance-report.pdf

# Set up performance alerts
ai-shell alerts add slow-query \
  --condition "query_time > 2000ms" \
  --action notify

# View performance trends
ai-shell performance trends --last 90d --chart
```

---

### Step 9: Learning from Patterns

AI-Shell learns from your query patterns to improve recommendations.

```bash
# View learned patterns
ai-shell patterns show

# Output:
# 🧠 Learned Query Patterns
#
# Common Patterns Detected:
# 1. Status Filtering (87% of order queries)
#    - Always filter by status column
#    - Recommendation: Keep idx_orders_status optimized
#
# 2. Date Range Queries (67% of analytics queries)
#    - Frequent date range filters
#    - Recommendation: Partition large tables by date
#
# 3. User Joins (45% of queries)
#    - Frequently join orders with users
#    - Recommendation: Consider materialized view
#
# Seasonal Patterns:
# - Query volume increases 3x on Mondays
# - Month-end reporting creates load spike
# - Recommendation: Pre-cache common reports

# Enable pattern-based optimization
ai-shell config set learn.patterns true

# Train on historical queries
ai-shell train --from query-history --days 90

# Apply pattern-based recommendations
ai-shell patterns apply-recommendations
```

---

### Step 10: Advanced Optimization Strategies

Master advanced techniques for maximum performance.

#### Composite Indexes
```bash
# AI-Shell suggests composite indexes for multi-column filters
ai-shell optimize "
  SELECT * FROM orders
  WHERE status = 'pending'
    AND created_at > NOW() - INTERVAL '7 days'
    AND customer_tier = 'premium'
"

# Recommendation:
# CREATE INDEX idx_orders_composite ON orders(status, customer_tier, created_at);
#
# Index column order optimized for:
# - Highest selectivity first (status)
# - Equality before range (customer_tier before created_at)
```

#### Partial Indexes
```bash
# For queries that always filter on specific values
ai-shell optimize "SELECT * FROM orders WHERE status = 'pending'"

# Recommendation for PostgreSQL:
# CREATE INDEX idx_orders_pending ON orders(created_at)
# WHERE status = 'pending';
#
# Benefits:
# - 90% smaller than full index
# - Faster to update
# - More cache-friendly
```

#### Covering Indexes
```bash
# Include columns in index to avoid table lookups
ai-shell optimize "
  SELECT order_id, total, created_at
  FROM orders
  WHERE status = 'completed'
"

# Recommendation:
# CREATE INDEX idx_orders_covering ON orders(status)
# INCLUDE (order_id, total, created_at);
#
# Benefit: Index-only scan (no table access needed)
```

---

## Common Use Cases

### Use Case 1: Optimizing E-Commerce Query Performance

**Scenario:** Product search queries are slow during peak traffic.

```bash
# Identify the slow product search query
ai-shell slow-queries --filter "products"

# Optimize product search
ai-shell optimize "
  SELECT * FROM products
  WHERE category = 'electronics'
    AND price BETWEEN 100 AND 500
    AND in_stock = true
"

# AI-Shell recommendations:
# 1. CREATE INDEX idx_products_category_price ON products(category, price)
#    WHERE in_stock = true;
# 2. Add product_search materialized view for common searches
# 3. Enable query result caching (TTL: 5 minutes)
#
# Apply optimizations? [y/N]: y
#
# Results:
# Before: 3,247ms
# After: 45ms
# Improvement: 98.6% faster (72x speedup)
#
# Additional benefit: Can handle 72x more concurrent searches
```

---

### Use Case 2: Analytics Dashboard Performance

**Scenario:** Executive dashboard takes 30+ seconds to load.

```bash
# Analyze dashboard queries
ai-shell optimize-all --tag dashboard

# AI-Shell creates optimization plan:
#
# Dashboard Optimization Plan:
#
# 1. Materialized View for Daily Metrics
#    CREATE MATERIALIZED VIEW daily_metrics AS
#    SELECT date, SUM(revenue), COUNT(orders), AVG(order_value)
#    FROM orders GROUP BY date;
#    Refresh: every 1 hour
#    Speedup: 87x (from 12s to 138ms)
#
# 2. Pre-aggregated Customer Stats
#    CREATE TABLE customer_stats_cache AS ...
#    Refresh: every 5 minutes
#    Speedup: 145x (from 18s to 124ms)
#
# 3. Indexed Time Series Data
#    CREATE INDEX idx_metrics_timestamp ON metrics(timestamp DESC);
#    Speedup: 23x (from 5s to 217ms)
#
# Total Dashboard Load:
# Before: 35 seconds
# After: 479ms
# Improvement: 98.6% faster
#
# Apply? [y/N]: y

# Set up automatic refresh
ai-shell refresh schedule daily_metrics --interval 1h
ai-shell refresh schedule customer_stats_cache --interval 5m
```

---

### Use Case 3: Handling Traffic Spikes

**Scenario:** Prepare database for Black Friday traffic spike.

```bash
# Analyze for scale optimization
ai-shell optimize-for-scale --target-load 50x

# Output:
# 🔍 Analyzing current performance baseline...
# Current: 1,000 req/min avg
# Target: 50,000 req/min (50x scale)
#
# Bottlenecks Identified:
# ❌ Product queries: 847ms avg (will fail at 12x load)
# ❌ Checkout process: 1,523ms avg (will fail at 8x load)
# ❌ User session lookup: 234ms avg (will fail at 25x load)
#
# Optimization Plan for 50x Scale:
#
# 1. Add 12 strategic indexes
# 2. Implement query result caching (5-min TTL)
# 3. Add read replicas routing
# 4. Optimize connection pooling (5 → 50 connections)
# 5. Enable statement-level caching
#
# Estimated Capacity After Optimization: 73x baseline
# Safety Margin: 46% above target
#
# Apply optimizations? [y/N]: y

# Monitor during event
ai-shell monitor --real-time --alert-threshold 80%
```

---

### Use Case 4: Multi-Tenant SaaS Optimization

**Scenario:** Some tenants experience slow queries while others are fast.

```bash
# Analyze per-tenant performance
ai-shell optimize --strategy per-tenant

# Output:
# 📊 Per-Tenant Analysis (1,247 tenants)
#
# Performance Distribution:
# Fast (< 100ms): 892 tenants (72%)
# Medium (100-500ms): 287 tenants (23%)
# Slow (> 500ms): 68 tenants (5%)
#
# Root Cause: Data volume variance
# - Fast tenants: avg 2,500 rows
# - Slow tenants: avg 280,000 rows
#
# Recommendations:
# 1. Partition large tenant data
# 2. Per-tenant index strategy
# 3. Dedicated connection pools for large tenants
#
# Apply tenant-specific optimizations? [y/N]: y
#
# Optimizing 68 slow tenants...
# ✓ 68/68 optimized
#
# Results:
# Average improvement: 14.2x faster
# All tenants now under 150ms
```

---

### Use Case 5: Data Warehouse Query Performance

**Scenario:** Analytical queries on large datasets are too slow.

```bash
# Optimize for analytical workloads
ai-shell optimize --workload analytics

# AI-Shell recommendations:
#
# Analytics Optimization Strategy:
#
# 1. Columnar Storage for Analytics Tables
#    - Convert fact tables to columnar format
#    - 5-10x faster aggregations
#
# 2. Partitioning Strategy
#    - Partition by date (monthly)
#    - 20x faster time-range queries
#
# 3. Pre-aggregations
#    - Hourly, daily, monthly rollups
#    - 100x faster dashboard queries
#
# 4. Bitmap Indexes for Categories
#    - Product categories, customer segments
#    - 15x faster filtering
#
# 5. Query Result Caching
#    - 1-hour TTL for reports
#    - Near-instant repeat queries
#
# Apply analytics optimizations? [y/N]: y
```

---

## Troubleshooting Tips

### Issue 1: Optimization Doesn't Improve Performance

**Problem:** Applied optimization but query is still slow.

**Solutions:**
```bash
# Check if index is being used
ai-shell explain "your query here" --verbose

# Force index usage (if database isn't using it)
ai-shell optimize "your query" --force-index idx_name

# Analyze statistics (outdated stats can cause poor planning)
ai-shell analyze-table orders

# Check for other bottlenecks
ai-shell diagnose "your query"
# May reveal: lock contention, I/O limits, network latency

# Review full execution plan
ai-shell explain "your query" --format detailed
```

---

### Issue 2: Index Creation Fails

**Problem:** Cannot create recommended index.

**Solutions:**
```bash
# Check permissions
ai-shell check-permissions --feature create-index

# Check disk space
ai-shell check-disk-space

# Create index online (non-blocking for PostgreSQL)
ai-shell indexes create idx_name --online

# Create index during off-peak hours
ai-shell indexes create idx_name --schedule "02:00"

# For very large tables, use concurrent index creation
ai-shell indexes create idx_name --concurrent
```

---

### Issue 3: Too Many Indexes

**Problem:** Database has too many indexes, slowing down writes.

**Solutions:**
```bash
# Analyze index usage
ai-shell indexes analyze --show-unused

# Remove unused indexes
ai-shell indexes cleanup --remove-unused --min-age 30d

# Consolidate overlapping indexes
ai-shell indexes consolidate

# Before: idx_orders_status, idx_orders_status_created
# After: idx_orders_status_created (covers both use cases)

# Set up automatic index management
ai-shell config set indexes.auto-cleanup true
ai-shell config set indexes.max-per-table 10
```

---

### Issue 4: Optimizations Breaking Application Code

**Problem:** Optimized query returns different results or breaks code.

**Solutions:**
```bash
# Test optimization in dry-run mode
ai-shell optimize "query" --dry-run --test

# Compare results before and after
ai-shell optimize "query" --validate-results

# If results differ:
# Output: ⚠️ Result mismatch detected
# Before: 1,247 rows
# After: 1,245 rows (2 missing due to incorrect rewrite)
#
# Optimization NOT applied (safety check)

# Review optimization details
ai-shell optimize "query" --explain-changes

# Apply with safety checks
ai-shell optimize "query" --safe-mode
# (validates results match before applying)
```

---

### Issue 5: High Optimization Overhead

**Problem:** Auto-optimization consuming too many resources.

**Solutions:**
```bash
# Adjust auto-optimization frequency
ai-shell config set auto-optimize.interval 1h  # default: 5m

# Set resource limits
ai-shell config set auto-optimize.maxConcurrent 2
ai-shell config set auto-optimize.cpuLimit 25%

# Optimize during off-peak hours only
ai-shell config set auto-optimize.schedule "02:00-06:00"

# Reduce analysis depth
ai-shell config set auto-optimize.depth quick  # options: quick, normal, deep

# Disable auto-optimize, use manual optimization instead
ai-shell config set auto-optimize.enabled false
ai-shell optimize-all --once-daily
```

---

## Best Practices

### 1. Start with Biggest Wins

```bash
# Identify highest-impact optimizations
ai-shell optimize-all --sort-by impact

# Focus on queries with:
# - High execution frequency
# - Long execution time
# - Business-critical paths (checkout, search, etc.)
```

### 2. Test Before Production

```bash
# Always test optimizations in staging first
ai-shell optimize "query" --environment staging

# Validate performance improvement
ai-shell benchmark "query" --before-after

# Run regression tests
ai-shell test regression --after-optimization
```

### 3. Monitor Index Size and Usage

```bash
# Regular index health checks
ai-shell indexes health-check --schedule weekly

# Watch for:
# - Unused indexes (waste space and slow writes)
# - Bloated indexes (need rebuilding)
# - Missing indexes (slow queries)

# Set up alerts
ai-shell alerts add index-bloat --threshold 50%
ai-shell alerts add index-unused --threshold 30d
```

### 4. Balance Read vs Write Performance

```bash
# Assess read/write ratio
ai-shell analyze workload-ratio

# For read-heavy workloads (90%+ reads)
# - Aggressive indexing is beneficial
ai-shell optimize --strategy read-optimized

# For write-heavy workloads (50%+ writes)
# - Fewer indexes, focus on critical queries only
ai-shell optimize --strategy balanced
```

### 5. Use Explain Plans Regularly

```bash
# Make EXPLAIN a habit for new queries
ai-shell explain "new query" --save-baseline

# Compare as data grows
ai-shell explain "query" --compare-to-baseline

# Set up automatic monitoring
ai-shell monitor query-plans --alert-on-regression
```

### 6. Maintain Database Statistics

```bash
# Keep statistics fresh for optimal planning
ai-shell analyze-all --schedule daily

# Manual analyze after bulk changes
ai-shell analyze-table orders  # after loading 100K rows

# Auto-analyze configuration
ai-shell config set auto-analyze.enabled true
ai-shell config set auto-analyze.threshold 10%  # after 10% data change
```

### 7. Document Optimizations

```bash
# AI-Shell automatically tracks optimizations
ai-shell optimization-history

# Export optimization log
ai-shell optimization-history --export log.json

# Add notes to optimizations
ai-shell optimization note idx_orders_status \
  "Created for Black Friday 2025 - critical for checkout flow"

# Review before removing indexes
ai-shell indexes show idx_name --history
```

---

## Next Steps

### Master Related Features

1. **Performance Monitoring**
   - Set up real-time performance tracking
   - [Tutorial: Performance Monitoring](./performance-monitoring.md)

2. **Database Federation**
   - Optimize cross-database queries
   - [Tutorial: Database Federation](./database-federation.md)

3. **Autonomous DevOps**
   - Enable self-learning optimization
   - [Tutorial: Autonomous DevOps](./autonomous-devops.md)

### Practice Exercises

1. **Exercise 1: Basic Optimization**
   - Find your 5 slowest queries
   - Apply optimizations and measure improvement
   - Document before/after execution times

2. **Exercise 2: Index Strategy**
   - List all your database indexes
   - Identify unused indexes
   - Remove unused and consolidate overlapping indexes

3. **Exercise 3: Query Rewriting**
   - Find 3 queries using inefficient patterns (LIKE '%...', functions in WHERE, etc.)
   - Let AI-Shell rewrite them
   - Compare performance

4. **Exercise 4: Auto-Optimization**
   - Enable auto-optimization in interactive mode
   - Monitor for 1 week
   - Review and approve recommendations

5. **Exercise 5: Scale Optimization**
   - Estimate your peak load (e.g., 10x current)
   - Use optimize-for-scale feature
   - Implement and test recommendations

### Additional Resources

- **Documentation**: [Optimization guide](https://docs.ai-shell.dev/optimization)
- **Best Practices**: [Performance best practices](../best-practices.md#query-optimization)
- **API Reference**: [Optimization API](../api/optimization.md)
- **Community**: [Share your optimization wins](https://github.com/your-org/ai-shell/discussions)

---

## Summary

You've learned how to:
- Identify and analyze slow queries
- Apply automatic query optimizations
- Manage database indexes effectively
- Understand and interpret execution plans
- Enable auto-optimization features
- Monitor optimization impact over time
- Apply advanced optimization strategies

Query optimization with AI-Shell transforms database performance from a manual, expert-level task into an automatic, continuous process. The self-learning capabilities mean your database gets faster over time as AI-Shell learns your patterns.

**Key Takeaway:** Start with the biggest wins (slow, frequent queries) and gradually expand optimization coverage. Enable auto-optimization to maintain performance as your application evolves.

---

**Related Tutorials:**
- [Natural Language Queries](./natural-language-queries.md)
- [Performance Monitoring](./performance-monitoring.md)
- [Autonomous DevOps](./autonomous-devops.md)

**Need Help?** [Visit our documentation](https://docs.ai-shell.dev) or [join the community](https://github.com/your-org/ai-shell/discussions)
