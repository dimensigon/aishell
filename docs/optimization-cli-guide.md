# Query Optimization CLI Guide

Complete guide to using AI-Shell's query optimization features via CLI commands.

## Table of Contents

1. [Overview](#overview)
2. [Query Optimization](#query-optimization)
3. [Slow Query Analysis](#slow-query-analysis)
4. [Index Management](#index-management)
5. [Pattern Analysis](#pattern-analysis)
6. [Auto-Optimization](#auto-optimization)
7. [Performance Examples](#performance-examples)
8. [Best Practices](#best-practices)

## Overview

The Optimization CLI provides powerful tools to analyze, optimize, and monitor your database queries. It uses AI-powered analysis to identify performance issues and recommend improvements.

### Key Features

- **AI-Powered Analysis**: Uses Claude AI to understand query patterns and suggest optimizations
- **Automatic Optimization**: Configure rules to automatically optimize slow queries
- **Index Management**: Analyze, create, and manage database indexes
- **Pattern Detection**: Identify common performance anti-patterns
- **Comprehensive Reporting**: Export results in JSON, CSV, or table formats

## Query Optimization

### Basic Usage

Optimize a single query:

```bash
ai-shell optimize "SELECT * FROM users WHERE email = 'test@example.com'"
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--apply` | Apply optimizations automatically | `--apply` |
| `--compare` | Show before/after comparison | `--compare` |
| `--explain` | Show execution plan | `--explain` |
| `--dry-run` | Test without applying | `--dry-run` |
| `--format` | Output format (json, table, csv) | `--format json` |
| `--output` | Save results to file | `--output result.json` |

### Examples

**Explain execution plan:**
```bash
ai-shell optimize "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id" --explain
```

**Apply optimizations automatically:**
```bash
ai-shell optimize "SELECT * FROM users WHERE active = true" --apply
```

**Export results:**
```bash
ai-shell optimize "SELECT * FROM orders" --output optimization.json --format json
```

**Dry run (validate only):**
```bash
ai-shell optimize "DELETE FROM old_data WHERE created_at < '2020-01-01'" --dry-run
```

## Slow Query Analysis

### Commands

#### analyze-slow-queries (alias: slow)

Analyze slow queries from history:

```bash
ai-shell slow-queries
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --threshold <ms>` | Minimum query time | 1000ms |
| `-l, --limit <n>` | Number of results | 10 |
| `--last <period>` | Time period (24h, 7d, 30d) | All |
| `--auto-fix` | Automatically optimize | false |
| `--export <file>` | Export results | - |
| `-f, --format <type>` | Output format | table |

### Examples

**Find queries slower than 500ms:**
```bash
ai-shell slow-queries --threshold 500
```

**Show top 20 slowest queries:**
```bash
ai-shell slow-queries --limit 20
```

**Analyze last 7 days:**
```bash
ai-shell slow-queries --last 7d
```

**Auto-fix slow queries:**
```bash
ai-shell slow-queries --threshold 1000 --auto-fix
```

**Export to JSON:**
```bash
ai-shell slow-queries --export slow-queries.json --format json
```

### optimize-all

Optimize all slow queries at once:

```bash
ai-shell optimize-all --threshold 500 --auto-apply --report optimization-report.json
```

## Index Management

### Commands

#### indexes analyze

Analyze existing indexes and identify opportunities:

```bash
ai-shell indexes analyze
```

Output:
```
📊 Analyzing indexes...

┌────────────┬──────────────────────┬───────────────┬─────────────────────┐
│ Table      │ Columns              │ Impact        │ Reason              │
├────────────┼──────────────────────┼───────────────┼─────────────────────┤
│ users      │ email                │ 60% faster    │ Missing index on... │
│ orders     │ user_id, created_at  │ 40% faster    │ Composite index...  │
│ products   │ category_id          │ 30% faster    │ Foreign key not...  │
└────────────┴──────────────────────┴───────────────┴─────────────────────┘
```

#### indexes recommendations

Get index recommendations:

```bash
ai-shell indexes recommendations
```

**Apply recommendations:**
```bash
ai-shell indexes recommendations --apply
```

#### indexes create

Create a new index:

```bash
ai-shell indexes create idx_users_email users email
```

**Create composite index:**
```bash
ai-shell indexes create idx_orders_user_date orders user_id created_at
```

**Create index online (no table lock):**
```bash
ai-shell indexes create idx_users_email users email --online
```

#### indexes drop

Drop an existing index:

```bash
ai-shell indexes drop idx_users_email
```

#### indexes rebuild

Rebuild indexes:

```bash
ai-shell indexes rebuild
```

**Rebuild all indexes:**
```bash
ai-shell indexes rebuild --all
```

#### indexes stats

Show index statistics:

```bash
ai-shell indexes stats
```

Output:
```
📊 Index Statistics

┌──────────────────────────┬─────────┐
│ Metric                   │ Value   │
├──────────────────────────┼─────────┤
│ Total Indexes            │ 45      │
│ Unused Indexes           │ 3       │
│ Duplicate Indexes        │ 2       │
│ Total Size               │ 250 MB  │
└──────────────────────────┴─────────┘
```

## Pattern Analysis

### analyze patterns

Identify common query anti-patterns:

```bash
ai-shell analyze patterns
```

Output:
```
🔍 Analyzing query patterns...

┌─────────────────────────┬───────┬────────┐
│ Pattern                 │ Count │ Impact │
├─────────────────────────┼───────┼────────┤
│ Full Table Scans        │ 12    │ High   │
│ Missing Indexes         │ 8     │ High   │
│ Suboptimal Joins        │ 5     │ Medium │
│ SELECT * Queries        │ 15    │ Medium │
└─────────────────────────┴───────┴────────┘
```

### analyze workload

Analyze overall database workload:

```bash
ai-shell analyze workload
```

Output:
```
📊 Analyzing database workload...

┌──────────────────────┬──────────┐
│ Metric               │ Value    │
├──────────────────────┼──────────┤
│ Total Queries        │ 12,450   │
│ Slow Queries         │ 234      │
│ Read/Write Ratio     │ 3.5      │
│ Avg Query Time       │ 45ms     │
└──────────────────────┴──────────┘
```

### analyze bottlenecks

Identify system bottlenecks:

```bash
ai-shell analyze bottlenecks
```

Output:
```
🔍 Analyzing performance bottlenecks...

┌──────────┬──────────┬─────────────────────────────────┐
│ Type     │ Severity │ Description                     │
├──────────┼──────────┼─────────────────────────────────┤
│ CPU      │ low      │ CPU usage within normal range   │
│ Memory   │ medium   │ Memory elevated during peaks    │
│ I/O      │ low      │ Disk I/O performing well        │
│ Network  │ low      │ Network latency acceptable      │
└──────────┴──────────┴─────────────────────────────────┘
```

### analyze recommendations

Get comprehensive optimization recommendations:

```bash
ai-shell analyze recommendations
```

Output:
```
💡 Optimization Recommendations

┌──────────┬───────────┬──────────────────────────────────────┐
│ Priority │ Category  │ Recommendation                       │
├──────────┼───────────┼──────────────────────────────────────┤
│ high     │ Index     │ Add index on users(email) for login  │
│ medium   │ Query     │ Optimize SELECT * to specific cols   │
│ medium   │ Cache     │ Enable query caching for frequent... │
│ low      │ Stats     │ Update table statistics for better..│
└──────────┴───────────┴──────────────────────────────────────┘
```

## Auto-Optimization

### enable

Enable automatic query optimization:

```bash
ai-shell auto-optimize enable
```

**With custom settings:**
```bash
ai-shell auto-optimize enable --threshold 500 --max-per-day 20
```

**Without approval requirement:**
```bash
ai-shell auto-optimize enable --no-approval
```

### disable

Disable auto-optimization:

```bash
ai-shell auto-optimize disable
```

### status

Check auto-optimization status:

```bash
ai-shell auto-optimize status
```

Output:
```
📊 Auto-Optimization Status

┌─────────────────────────────────┬──────────┐
│ Setting                         │ Value    │
├─────────────────────────────────┼──────────┤
│ Enabled                         │ Yes      │
│ Threshold                       │ 1000ms   │
│ Max Optimizations/Day           │ 10       │
│ Require Approval                │ Yes      │
│ Index Creation Allowed          │ Yes      │
│ Statistics Update Allowed       │ Yes      │
│ Notify on Optimization          │ Yes      │
└─────────────────────────────────┴──────────┘
```

### configure

Configure auto-optimization settings:

```bash
ai-shell auto-optimize configure --threshold 500 --max-per-day 15
```

**Available options:**
- `--threshold <ms>` - Optimization threshold in milliseconds
- `--max-per-day <n>` - Maximum optimizations per day
- `--require-approval` - Require approval for optimizations
- `--allow-index-creation` - Allow automatic index creation

## Performance Examples

### Example 1: E-commerce Site Optimization

**Problem:** Slow product search queries

```bash
# Analyze slow queries
ai-shell slow-queries --threshold 500

# Output shows:
# 1. SELECT * FROM products WHERE category = 'electronics' (avg: 1200ms)
# 2. SELECT * FROM orders WHERE user_id = 123 ORDER BY created_at (avg: 800ms)
```

**Solution:**

```bash
# Create indexes
ai-shell indexes create idx_products_category products category
ai-shell indexes create idx_orders_user_date orders user_id created_at

# Verify improvement
ai-shell optimize "SELECT * FROM products WHERE category = 'electronics'" --compare
```

**Results:**
- Product queries: 1200ms → 80ms (93% improvement)
- Order queries: 800ms → 45ms (94% improvement)

### Example 2: User Authentication Optimization

**Problem:** Slow login queries

```bash
# Analyze pattern
ai-shell analyze patterns

# Shows: Missing index on users(email)
```

**Solution:**

```bash
# Get recommendations
ai-shell indexes recommendations --apply

# Creates:
# - idx_users_email on users(email)
# - idx_sessions_user on sessions(user_id)
```

**Results:**
- Login queries: 500ms → 5ms (99% improvement)
- Session lookups: 200ms → 3ms (98.5% improvement)

### Example 3: Analytics Dashboard

**Problem:** Dashboard loads slowly

```bash
# Analyze workload
ai-shell analyze workload

# Shows high read/write ratio (10:1)
# Recommendation: Enable caching
```

**Solution:**

```bash
# Enable auto-optimization
ai-shell auto-optimize enable --threshold 200

# Optimize dashboard queries
ai-shell optimize-all --auto-apply
```

**Results:**
- Dashboard load time: 8s → 1.2s (85% improvement)
- Database load: Reduced by 70%

### Example 4: Report Generation

**Problem:** Monthly report generation takes hours

```bash
# Analyze bottlenecks
ai-shell analyze bottlenecks

# Shows: I/O bottleneck, multiple full table scans
```

**Solution:**

```bash
# Optimize report queries
ai-shell optimize "
  SELECT
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as total_orders,
    SUM(amount) as revenue
  FROM orders
  WHERE created_at >= '2023-01-01'
  GROUP BY DATE_TRUNC('month', created_at)
" --explain --apply

# Create supporting indexes
ai-shell indexes recommendations --apply
```

**Results:**
- Report generation: 2 hours → 5 minutes (96% improvement)
- Resource usage: Reduced by 80%

## Best Practices

### 1. Regular Analysis

Run weekly analysis:

```bash
# Weekly optimization routine
ai-shell slow-queries --last 7d --export weekly-report.json
ai-shell analyze patterns
ai-shell analyze bottlenecks
```

### 2. Gradual Optimization

Start with high-impact changes:

```bash
# 1. Identify critical queries
ai-shell slow-queries --threshold 1000 --limit 5

# 2. Optimize one at a time
ai-shell optimize "<query>" --explain --dry-run

# 3. Apply and verify
ai-shell optimize "<query>" --apply --compare
```

### 3. Index Management

Monitor index health:

```bash
# Regular index maintenance
ai-shell indexes stats
ai-shell indexes analyze

# Remove unused indexes
ai-shell indexes recommendations

# Rebuild fragmented indexes
ai-shell indexes rebuild
```

### 4. Auto-Optimization Settings

Configure based on workload:

**High-traffic production:**
```bash
ai-shell auto-optimize configure \
  --threshold 200 \
  --max-per-day 50 \
  --require-approval \
  --allow-index-creation
```

**Development environment:**
```bash
ai-shell auto-optimize configure \
  --threshold 500 \
  --max-per-day 100 \
  --no-approval
```

### 5. Monitoring and Alerts

Set up regular monitoring:

```bash
#!/bin/bash
# daily-optimization-check.sh

# Run slow query analysis
ai-shell slow-queries --threshold 500 --export /var/log/slow-queries-$(date +%Y%m%d).json

# Check for critical issues
SLOW_COUNT=$(ai-shell slow-queries --threshold 1000 --format json | jq 'length')

if [ $SLOW_COUNT -gt 10 ]; then
  echo "Warning: $SLOW_COUNT slow queries detected"
  ai-shell optimize-all --threshold 1000 --report /var/log/optimization-$(date +%Y%m%d).json
fi
```

### 6. Performance Baselines

Establish and track baselines:

```bash
# Create baseline
ai-shell analyze workload > baseline-$(date +%Y%m%d).txt
ai-shell analyze patterns >> baseline-$(date +%Y%m%d).txt

# Compare after optimization
ai-shell analyze workload > after-optimization-$(date +%Y%m%d).txt
diff baseline-*.txt after-optimization-*.txt
```

## Common Issues and Solutions

### Issue: Too Many Slow Queries

```bash
# Identify patterns
ai-shell analyze patterns

# Bulk optimization
ai-shell optimize-all --threshold 500 --auto-apply
```

### Issue: Index Bloat

```bash
# Check index statistics
ai-shell indexes stats

# Find unused indexes
ai-shell indexes analyze

# Rebuild necessary indexes
ai-shell indexes rebuild --all
```

### Issue: High Memory Usage

```bash
# Analyze bottlenecks
ai-shell analyze bottlenecks

# Check workload
ai-shell analyze workload

# Optimize queries with large result sets
ai-shell slow-queries --threshold 200
```

## Advanced Techniques

### Combining Commands

```bash
# Comprehensive optimization workflow
ai-shell slow-queries --threshold 500 --export slow.json && \
ai-shell analyze patterns && \
ai-shell indexes analyze && \
ai-shell optimize-all --auto-apply --report results.json
```

### Scheduled Optimization

```bash
# Add to crontab
0 2 * * * /usr/local/bin/ai-shell optimize-all --threshold 1000 --auto-apply
0 3 * * 0 /usr/local/bin/ai-shell indexes rebuild --all
```

### Integration with CI/CD

```yaml
# .github/workflows/db-optimization.yml
name: Database Optimization

on:
  schedule:
    - cron: '0 2 * * *'

jobs:
  optimize:
    runs-on: ubuntu-latest
    steps:
      - name: Analyze slow queries
        run: ai-shell slow-queries --threshold 500 --export slow-queries.json

      - name: Optimize queries
        run: ai-shell optimize-all --auto-apply --report optimization-report.json

      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: optimization-reports
          path: |
            slow-queries.json
            optimization-report.json
```

## Support

For issues or questions:
- GitHub: https://github.com/yourusername/ai-shell/issues
- Documentation: https://github.com/yourusername/ai-shell/docs
- Email: support@example.com

## Version History

- v1.0.0 - Initial release with core optimization features
- v1.1.0 - Added auto-optimization capabilities
- v1.2.0 - Enhanced index management and pattern analysis
