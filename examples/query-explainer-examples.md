# Query Explainer Examples

## Basic Usage

### 1. Simple SELECT Query

```bash
# Explain a basic SELECT query
ai-shell explain "SELECT * FROM users WHERE id = 1"
```

**Output:**
- Execution plan visualization
- Cost estimation
- Performance insights
- Index usage analysis

### 2. Complex JOIN Query

```bash
# Explain multi-table JOIN
ai-shell explain "
  SELECT u.name, o.order_number, p.product_name
  FROM users u
  JOIN orders o ON u.id = o.user_id
  JOIN order_items oi ON o.id = oi.order_id
  JOIN products p ON oi.product_id = p.id
  WHERE u.active = true
"
```

**Output:**
- Join strategy analysis
- Nested loop detection
- Index recommendations
- Optimization suggestions

### 3. Aggregate Query

```bash
# Explain GROUP BY with aggregation
ai-shell explain "
  SELECT user_id, COUNT(*) as order_count, SUM(total) as revenue
  FROM orders
  GROUP BY user_id
  HAVING COUNT(*) > 5
  ORDER BY revenue DESC
"
```

**Output:**
- Aggregation cost
- Sort analysis
- Temporary table usage
- Performance bottlenecks

## Dry-Run Mode

### 1. Validate DELETE Query

```bash
# Check DELETE without executing
ai-shell optimize "DELETE FROM users WHERE last_login < NOW() - INTERVAL 1 YEAR" --dry-run
```

**Output:**
```
DRY RUN MODE - NO EXECUTION
─────────────────────────────
Query: DELETE FROM users WHERE last_login < NOW() - INTERVAL 1 YEAR
Is Destructive: ⚠️  YES
Estimated Rows: 1,523
Warnings:
  ⚠️ This is a DESTRUCTIVE operation that will modify or delete data
Status: ✓ Validation passed - Query is safe to execute
```

### 2. Validate UPDATE Query

```bash
# Check UPDATE impact
ai-shell explain "UPDATE orders SET status = 'shipped' WHERE status = 'pending'" --dry-run
```

### 3. Validate Complex Migration

```bash
# Test migration query
ai-shell explain "
  ALTER TABLE users
  ADD COLUMN email_verified BOOLEAN DEFAULT false
" --dry-run
```

## Format Options

### 1. JSON Output

```bash
# Get JSON output for automation
ai-shell explain "SELECT * FROM users WHERE active = true" --format json > query-plan.json
```

**Use Cases:**
- CI/CD integration
- Performance tracking
- Documentation generation
- Automated analysis

### 2. Text Output (Default)

```bash
# Human-readable format
ai-shell explain "SELECT * FROM orders WHERE created_at > NOW() - INTERVAL 7 DAY"
```

## Performance Analysis

### 1. Slow Query Analysis

```bash
# Analyze slow query
ai-shell explain "
  SELECT *
  FROM logs
  WHERE message LIKE '%error%'
  ORDER BY created_at DESC
" --analyze
```

**Output:**
- Bottleneck identification
- Cost breakdown
- Optimization recommendations
- Estimated improvement

### 2. Subquery Optimization

```bash
# Analyze subquery performance
ai-shell explain "
  SELECT u.*
  FROM users u
  WHERE u.id IN (
    SELECT DISTINCT user_id
    FROM orders
    WHERE total > 1000
  )
"
```

**Suggestions:**
- JOIN vs. subquery comparison
- Index recommendations
- Query rewrite options

### 3. Index Usage Check

```bash
# Verify index usage
ai-shell explain "SELECT * FROM users WHERE email = 'test@example.com'" --analyze
```

**Output:**
- Index scan vs. sequential scan
- Index effectiveness
- Missing index detection

## Federated Query Analysis

### 1. Cross-Database Query

```bash
# Explain federated query
ai-shell federate "
  SELECT u.*, o.*
  FROM users u
  JOIN orders o ON u.id = o.user_id
" --databases production,analytics --explain
```

### 2. Validate Federated Query

```bash
# Dry-run federated query
ai-shell federate "DELETE FROM old_data WHERE created_at < '2020-01-01'" --databases db1,db2,db3 --dry-run
```

## Optimization Workflow

### 1. Identify Slow Queries

```bash
# Find slow queries
ai-shell analyze-slow-queries --threshold 100
```

### 2. Explain Each Query

```bash
# Analyze specific slow query
ai-shell explain "SELECT * FROM large_table WHERE unindexed_column = 'value'"
```

### 3. Apply Optimizations

```bash
# Optimize based on suggestions
ai-shell optimize "SELECT * FROM large_table WHERE unindexed_column = 'value'"
```

**Suggested Actions:**
```sql
-- Create recommended index
CREATE INDEX idx_large_table_unindexed_column ON large_table(unindexed_column);

-- Rewrite query
SELECT id, name, status
FROM large_table
WHERE unindexed_column = 'value'
LIMIT 100;
```

### 4. Verify Improvement

```bash
# Re-explain after optimization
ai-shell explain "SELECT id, name, status FROM large_table WHERE unindexed_column = 'value' LIMIT 100"
```

## Real-World Examples

### Example 1: E-Commerce Order Query

```bash
ai-shell explain "
  SELECT
    u.name,
    u.email,
    COUNT(DISTINCT o.id) as order_count,
    SUM(o.total) as lifetime_value,
    MAX(o.created_at) as last_order_date
  FROM users u
  LEFT JOIN orders o ON u.id = o.user_id
  WHERE u.created_at > '2024-01-01'
  GROUP BY u.id, u.name, u.email
  HAVING COUNT(DISTINCT o.id) > 0
  ORDER BY lifetime_value DESC
  LIMIT 100
"
```

**Analysis Results:**
- **Cost:** 2,450.75
- **Rows:** 1,250
- **Bottlenecks:**
  - Hash aggregate on large dataset
  - Missing index on users.created_at
- **Suggestions:**
  - Add index: `CREATE INDEX idx_users_created_at ON users(created_at)`
  - Consider materialized view for frequent queries

### Example 2: Analytics Dashboard Query

```bash
ai-shell explain "
  SELECT
    DATE(created_at) as date,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(duration) as avg_duration
  FROM events
  WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'
  GROUP BY DATE(created_at)
  ORDER BY date DESC
" --format json
```

**Optimization Path:**
1. Add composite index on (created_at, user_id)
2. Pre-aggregate data in summary tables
3. Use partitioning for large time ranges

### Example 3: User Search Query

```bash
ai-shell explain "
  SELECT *
  FROM users
  WHERE
    (name ILIKE '%john%' OR email ILIKE '%john%')
    AND active = true
  ORDER BY created_at DESC
  LIMIT 20
"
```

**Issues Identified:**
- ILIKE prevents index usage
- Multiple OR conditions cause full scan
- Missing index on active column

**Recommended Fix:**
```sql
-- Add full-text search index
CREATE INDEX idx_users_search ON users USING gin(to_tsvector('english', name || ' ' || email));

-- Rewrite query
SELECT *
FROM users
WHERE
  to_tsvector('english', name || ' ' || email) @@ to_tsquery('english', 'john')
  AND active = true
ORDER BY created_at DESC
LIMIT 20;
```

## Integration with CI/CD

### 1. Pre-Deployment Query Validation

```bash
#!/bin/bash
# validate-queries.sh

# Validate all migration queries
for migration in migrations/*.sql; do
  echo "Validating $migration..."
  ai-shell explain "$(cat $migration)" --dry-run --format json > "reports/$(basename $migration).json"
done

# Fail if any destructive queries found
if grep -q '"isDestructive": true' reports/*.json; then
  echo "⚠️  Destructive queries found - manual review required"
  exit 1
fi
```

### 2. Performance Regression Detection

```bash
#!/bin/bash
# check-performance.sh

# Explain critical queries
ai-shell explain "$(cat queries/critical-query-1.sql)" --format json > current-plan.json

# Compare with baseline
if [ "$(jq '.estimatedCost' current-plan.json)" -gt 1000 ]; then
  echo "❌ Query cost exceeds threshold"
  exit 1
fi
```

### 3. Automated Optimization

```bash
#!/bin/bash
# auto-optimize.sh

# Get slow queries
ai-shell analyze-slow-queries --threshold 500 --format json > slow-queries.json

# Generate optimization report
jq -r '.[] | "ai-shell optimize \"" + .query + "\" --explain"' slow-queries.json | bash
```

## Tips and Best Practices

### 1. Always Dry-Run Destructive Operations

```bash
# ❌ Dangerous
ai-shell optimize "DELETE FROM users WHERE inactive = true"

# ✅ Safe
ai-shell optimize "DELETE FROM users WHERE inactive = true" --dry-run
```

### 2. Use JSON Format for Automation

```bash
# Export for analysis
ai-shell explain "SELECT * FROM users" --format json | jq '.bottlenecks[] | select(.severity == "high")'
```

### 3. Document Query Plans

```bash
# Create documentation
for query in queries/*.sql; do
  ai-shell explain "$(cat $query)" > docs/query-plans/$(basename $query .sql).txt
done
```

### 4. Regular Performance Audits

```bash
# Weekly audit script
ai-shell analyze-slow-queries --threshold 200 > reports/slow-queries-$(date +%Y-%m-%d).txt
```

### 5. Test Before Production

```bash
# Staging validation
ai-shell explain "SELECT * FROM users WHERE email = ?" --dry-run

# Production execution
ai-shell optimize "SELECT * FROM users WHERE email = ?"
```

## Advanced Patterns

### Pattern 1: Multi-Stage Analysis

```bash
# Stage 1: Identify issues
ai-shell explain "SELECT * FROM users" > analysis.txt

# Stage 2: Test optimization
ai-shell explain "SELECT id, name, email FROM users LIMIT 1000" > optimized.txt

# Stage 3: Compare
diff analysis.txt optimized.txt
```

### Pattern 2: Automated Index Suggestions

```bash
# Extract index suggestions
ai-shell explain "SELECT * FROM users WHERE status = 'active'" --format json |
  jq -r '.suggestions[] | select(.type == "index") | .sqlExample' |
  tee suggested-indexes.sql
```

### Pattern 3: Cost-Based Query Selection

```bash
# Compare query variants
for variant in queries/variant-*.sql; do
  cost=$(ai-shell explain "$(cat $variant)" --format json | jq -r '.estimatedCost')
  echo "$variant: $cost"
done | sort -t: -k2 -n | head -1
```

## Troubleshooting

### Issue: Explain output shows no bottlenecks

**Cause:** Query is already well-optimized

**Verification:**
```bash
ai-shell explain "SELECT * FROM users WHERE id = 1" --analyze
```

### Issue: Dry-run shows different results than actual execution

**Cause:** Database statistics are outdated

**Fix:**
```sql
ANALYZE users;  -- PostgreSQL
ANALYZE TABLE users;  -- MySQL
```

### Issue: Cannot explain federated query

**Cause:** Federation explain not yet fully supported

**Workaround:**
```bash
# Explain each part separately
ai-shell explain "SELECT * FROM users" --database db1
ai-shell explain "SELECT * FROM orders" --database db2
```
