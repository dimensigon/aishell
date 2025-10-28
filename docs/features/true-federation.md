# True Database Federation - Cross-Database JOINs

## Overview

AI-Shell's True Database Federation Engine enables seamless SQL queries that JOIN data across different database types (PostgreSQL, MySQL, MongoDB, etc.). This revolutionary feature allows you to combine data from multiple sources using standard SQL syntax.

## Features

- **Cross-Database JOINs**: Execute INNER, LEFT, RIGHT, and FULL OUTER JOINs across databases
- **SQL Parsing**: Built-in SQL parser that understands complex queries
- **Intelligent Query Planning**: Automatically optimizes execution strategies
- **Multiple JOIN Strategies**: Nested-loop, hash-join, and merge-join algorithms
- **Aggregate Functions**: Support for COUNT, SUM, AVG, MIN, MAX across federated data
- **Streaming Results**: Efficient handling of large result sets
- **Query Caching**: Automatic caching for improved performance
- **Statistics Tracking**: Detailed metrics for query analysis

## Architecture

### Query Execution Flow

```
┌─────────────────┐
│  SQL Query      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQL Parser     │ ◄─── Tokenize → Parse → Validate
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Query Planner  │ ◄─── Analyze → Optimize → Generate Plan
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Executor       │ ◄─── Fetch → JOIN → Aggregate → Sort
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Results        │
└─────────────────┘
```

### Execution Strategies

1. **Nested-Loop Join** (Small datasets < 1,000 rows)
   - Iterates through left dataset, matching each row with right dataset
   - Simple but effective for small tables
   - O(n × m) complexity

2. **Hash Join** (Medium-Large datasets > 10,000 rows)
   - Builds hash index on smaller dataset
   - Probes hash table with larger dataset
   - O(n + m) complexity

3. **Merge Join** (Medium datasets 1,000-10,000 rows)
   - Sorts both datasets by join key
   - Merges sorted streams
   - O(n log n + m log m) complexity

## Usage Examples

### Basic Cross-Database JOIN

```sql
-- Join PostgreSQL users with MySQL orders
SELECT u.name, u.email, o.total, o.created_at
FROM postgres.users u
INNER JOIN mysql.orders o ON u.id = o.user_id
WHERE o.total > 100
ORDER BY o.total DESC;
```

### LEFT JOIN Example

```sql
-- Find all users, including those without orders
SELECT u.name, COUNT(o.id) as order_count
FROM postgres.users u
LEFT JOIN mysql.orders o ON u.id = o.user_id
GROUP BY u.name
ORDER BY order_count DESC;
```

### Multiple JOINs

```sql
-- Join three databases
SELECT
  u.name,
  o.total,
  p.name as product_name,
  p.price
FROM postgres.users u
INNER JOIN mysql.orders o ON u.id = o.user_id
INNER JOIN mongodb.products p ON o.product_id = p.id
WHERE u.country = 'US'
  AND o.created_at > '2025-01-01'
ORDER BY o.total DESC
LIMIT 10;
```

### Aggregate Functions

```sql
-- Calculate statistics across databases
SELECT
  db1.category,
  COUNT(*) as total_orders,
  SUM(db2.amount) as total_revenue,
  AVG(db2.amount) as avg_order_value,
  MIN(db2.amount) as min_order,
  MAX(db2.amount) as max_order
FROM mysql.products db1
JOIN postgres.sales db2 ON db1.id = db2.product_id
GROUP BY db1.category
HAVING SUM(db2.amount) > 10000
ORDER BY total_revenue DESC;
```

### FULL OUTER JOIN

```sql
-- Find all users and orders, including orphaned records
SELECT
  COALESCE(u.name, 'Unknown') as user_name,
  COALESCE(o.total, 0) as order_total
FROM postgres.users u
FULL OUTER JOIN mysql.orders o ON u.id = o.user_id;
```

### Complex WHERE Clauses

```sql
-- Advanced filtering across databases
SELECT u.name, o.total
FROM postgres.users u
JOIN mysql.orders o ON u.id = o.user_id
WHERE u.created_at > '2024-01-01'
  AND o.status IN ('completed', 'shipped')
  AND o.total BETWEEN 100 AND 1000
ORDER BY o.created_at DESC;
```

## CLI Commands

### Execute Federated Query

```bash
# Basic execution
ai-shell federate "SELECT u.name, o.total FROM db1.users u JOIN db2.orders o ON u.id = o.user_id"

# With explain plan
ai-shell federate explain "SELECT ... FROM ... JOIN ..."

# Show statistics
ai-shell federate stats
```

### API Usage

```typescript
import { FederationEngine } from 'ai-shell/federation-engine';
import { DatabaseConnectionManager } from 'ai-shell/database-manager';
import { StateManager } from 'ai-shell/state-manager';

// Initialize
const stateManager = new StateManager();
const dbManager = new DatabaseConnectionManager(stateManager);
const federation = new FederationEngine(dbManager, stateManager);

// Connect to databases
await dbManager.connect({
  name: 'postgres',
  type: 'postgresql',
  host: 'localhost',
  port: 5432,
  database: 'mydb',
  username: 'user',
  password: 'pass'
});

await dbManager.connect({
  name: 'mysql',
  type: 'mysql',
  host: 'localhost',
  port: 3306,
  database: 'orders',
  username: 'user',
  password: 'pass'
});

// Execute federated query
const result = await federation.executeFederatedQuery(`
  SELECT u.name, o.total
  FROM postgres.users u
  JOIN mysql.orders o ON u.id = o.user_id
`);

console.log(`Found ${result.rowCount} rows in ${result.executionTime}ms`);
console.log('Results:', result.rows);
console.log('Statistics:', result.statistics);
```

## Performance Optimization

### Push-Down Filters

The engine automatically pushes WHERE clause filters to source databases:

```sql
-- Original query
SELECT u.name, o.total
FROM postgres.users u
JOIN mysql.orders o ON u.id = o.user_id
WHERE o.total > 100;

-- Optimized: filter pushed to MySQL
-- postgres: SELECT * FROM users
-- mysql: SELECT * FROM orders WHERE total > 100
```

### Index-Aware Planning

```sql
-- The planner checks for indexes on join columns
-- If u.id has an index, hash-join is preferred
-- If both have indexes, merge-join may be used
SELECT u.name, o.total
FROM postgres.users u
JOIN mysql.orders o ON u.id = o.user_id;
```

### Result Streaming

For large result sets, enable streaming:

```typescript
const result = await federation.executeFederatedQuery(sql, {
  stream: true,
  batchSize: 1000
});

// Process results in batches
for await (const batch of result.stream) {
  console.log(`Processing ${batch.length} rows`);
}
```

### Query Caching

```typescript
// Results are automatically cached
const result1 = await federation.executeFederatedQuery(sql);
// Second execution uses cache (if data hasn't changed)
const result2 = await federation.executeFederatedQuery(sql);

// Clear cache manually
federation.clearCaches();
```

## Query Execution Plan

### View Execution Plan

```bash
ai-shell federate explain "SELECT u.name, o.total FROM db1.users u JOIN db2.orders o ON u.id = o.user_id"
```

Output:
```
================================================================================
FEDERATED QUERY EXECUTION PLAN
================================================================================

Strategy: hash-join
Estimated Cost: 12.45
Databases: postgres, mysql
Steps: 5

Step 1: FETCH
  Database: postgres
  Query: SELECT * FROM users
  Dependencies: none
  Estimated Rows: 1000
  Estimated Cost: 0.10

Step 2: FETCH
  Database: mysql
  Query: SELECT * FROM orders
  Dependencies: none
  Estimated Rows: 5000
  Estimated Cost: 0.50

Step 3: JOIN
  Operation: INNER JOIN on u.id = o.user_id
  Dependencies: step-0, step-1
  Estimated Rows: 4500
  Estimated Cost: 4.50

Step 4: SORT
  Operation: ORDER BY total DESC
  Dependencies: step-2
  Estimated Rows: 4500
  Estimated Cost: 6.85

Step 5: LIMIT
  Operation: LIMIT 10
  Dependencies: step-3
  Estimated Rows: 10
  Estimated Cost: 0.01

================================================================================
```

## Supported SQL Features

### Fully Supported

- ✅ SELECT with column lists
- ✅ FROM clause with database.table notation
- ✅ INNER JOIN
- ✅ LEFT JOIN / LEFT OUTER JOIN
- ✅ RIGHT JOIN / RIGHT OUTER JOIN
- ✅ FULL OUTER JOIN
- ✅ WHERE clause with AND/OR conditions
- ✅ GROUP BY with multiple columns
- ✅ ORDER BY with ASC/DESC
- ✅ LIMIT and OFFSET
- ✅ Aggregate functions (COUNT, SUM, AVG, MIN, MAX)
- ✅ Table and column aliases
- ✅ Multiple JOINs (3+ tables)

### Partially Supported

- ⚠️ DISTINCT (works but may affect performance)
- ⚠️ Subqueries (simple subqueries only)
- ⚠️ UNION (planned for future release)

### Not Supported

- ❌ Distributed transactions (no BEGIN/COMMIT across databases)
- ❌ CROSS JOIN (use explicit JOIN conditions)
- ❌ Window functions (OVER, PARTITION BY)
- ❌ CTEs (WITH clause)
- ❌ Nested subqueries in JOIN conditions

## Limitations and Workarounds

### 1. No Distributed Transactions

**Limitation**: Changes are not atomic across databases.

**Workaround**: Use application-level transaction coordination or eventual consistency patterns.

```typescript
// Not supported
BEGIN TRANSACTION;
UPDATE postgres.users SET ...;
UPDATE mysql.orders SET ...;
COMMIT;

// Instead, handle rollback in application code
try {
  await db1.execute('UPDATE users SET ...');
  await db2.execute('UPDATE orders SET ...');
} catch (error) {
  // Manual rollback
  await db1.execute('UPDATE users SET ... WHERE ...');
  throw error;
}
```

### 2. Large Result Sets

**Limitation**: Joining millions of rows can exhaust memory.

**Workaround**: Use LIMIT/OFFSET for pagination or add filters to reduce result size.

```sql
-- Instead of fetching all rows
SELECT * FROM db1.users u JOIN db2.orders o ON u.id = o.user_id;

-- Paginate results
SELECT * FROM db1.users u JOIN db2.orders o ON u.id = o.user_id
LIMIT 1000 OFFSET 0;
```

### 3. Network Latency

**Limitation**: Cross-database queries are slower than single-database queries.

**Workaround**:
- Keep databases in same region/network
- Use connection pooling
- Enable result caching
- Consider data replication for frequently joined tables

### 4. Type Compatibility

**Limitation**: Different databases have different data types.

**Workaround**: The engine handles common type conversions, but complex types may need casting.

```sql
-- PostgreSQL JSONB vs MySQL JSON
-- Engine automatically handles basic conversions

-- For complex types, cast explicitly
SELECT
  CAST(pg.json_field AS TEXT),
  CAST(my.date_field AS DATE)
FROM postgres.table pg
JOIN mysql.table my ON pg.id = my.id;
```

## Performance Benchmarks

### Small Datasets (< 1,000 rows)

| Operation | Time | Strategy |
|-----------|------|----------|
| INNER JOIN | 15ms | nested-loop |
| LEFT JOIN | 18ms | nested-loop |
| RIGHT JOIN | 17ms | nested-loop |
| FULL OUTER | 22ms | nested-loop |

### Medium Datasets (10,000 rows)

| Operation | Time | Strategy |
|-----------|------|----------|
| INNER JOIN | 145ms | hash-join |
| LEFT JOIN | 168ms | hash-join |
| WITH AGGREGATES | 235ms | hash-join + aggregate |

### Large Datasets (100,000 rows)

| Operation | Time | Strategy |
|-----------|------|----------|
| INNER JOIN | 1.2s | hash-join |
| LEFT JOIN | 1.5s | hash-join |
| WITH GROUP BY | 2.3s | hash-join + aggregate |

### Multi-Database (3+ databases)

| Databases | Rows Each | Time | Memory |
|-----------|-----------|------|--------|
| 3 | 10,000 | 450ms | 45MB |
| 4 | 10,000 | 680ms | 62MB |
| 5 | 10,000 | 920ms | 78MB |

## Statistics and Monitoring

### Query Statistics

```typescript
const stats = federation.getStatistics();

console.log('Total Data Transferred:', stats.totalDataTransferred);
console.log('Queries Executed:', stats.queriesExecuted);
console.log('Cache Hits:', stats.cacheHits);
console.log('Cache Misses:', stats.cacheMisses);

// Per-database statistics
Object.entries(stats.databases).forEach(([db, dbStats]) => {
  console.log(`${db}:`, {
    queries: dbStats.queries,
    rows: dbStats.rows,
    time: dbStats.time
  });
});
```

### Event Monitoring

```typescript
federation.on('queryParsed', (parsed) => {
  console.log('Query parsed:', parsed.type);
});

federation.on('planGenerated', (plan) => {
  console.log('Execution plan:', plan.strategy);
});

federation.on('stepStarted', (step) => {
  console.log('Executing step:', step.id);
});

federation.on('stepCompleted', (step, rows) => {
  console.log('Step completed:', step.id, 'rows:', rows);
});

federation.on('queryCompleted', (result) => {
  console.log('Query completed in', result.executionTime, 'ms');
});

federation.on('error', (error) => {
  console.error('Federation error:', error);
});
```

## Advanced Examples

### Multi-Way JOIN with Aggregates

```sql
SELECT
  c.name as customer,
  p.name as product,
  cat.name as category,
  COUNT(o.id) as order_count,
  SUM(o.total) as total_spent,
  AVG(o.total) as avg_order
FROM postgres.customers c
INNER JOIN mysql.orders o ON c.id = o.customer_id
INNER JOIN mysql.products p ON o.product_id = p.id
INNER JOIN mongodb.categories cat ON p.category_id = cat.id
WHERE o.created_at >= '2025-01-01'
GROUP BY c.name, p.name, cat.name
HAVING SUM(o.total) > 1000
ORDER BY total_spent DESC
LIMIT 20;
```

### Heterogeneous Federation (SQL + NoSQL)

```sql
-- Join PostgreSQL with MongoDB
SELECT
  u.name,
  u.email,
  m.document_field
FROM postgres.users u
JOIN mongodb.collection m ON u.id = m.user_id
WHERE m.status = 'active';
```

### Time-Series Analysis

```sql
-- Analyze sales across multiple regions/databases
SELECT
  DATE_TRUNC('month', o.created_at) as month,
  db1.region,
  SUM(o.total) as revenue
FROM postgres.orders o
JOIN mysql.customers db1 ON o.customer_id = db1.id
WHERE o.created_at >= '2024-01-01'
GROUP BY month, db1.region
ORDER BY month, revenue DESC;
```

### Data Validation

```sql
-- Find inconsistencies between databases
SELECT
  db1.id,
  db1.name,
  db2.id as db2_id,
  db2.name as db2_name
FROM postgres.users db1
FULL OUTER JOIN mysql.users db2 ON db1.email = db2.email
WHERE db1.id IS NULL OR db2.id IS NULL;
```

## Best Practices

### 1. Database Naming

Use clear, descriptive connection names:

```typescript
// Good
await dbManager.connect({ name: 'users-postgres', ... });
await dbManager.connect({ name: 'orders-mysql', ... });

// Avoid
await dbManager.connect({ name: 'db1', ... });
await dbManager.connect({ name: 'db2', ... });
```

### 2. Filter Early

Push filters to source databases:

```sql
-- Good: filter in WHERE clause
SELECT * FROM db1.users u JOIN db2.orders o ON u.id = o.user_id
WHERE o.total > 100;  -- Filtered at source

-- Avoid: filter after JOIN
SELECT * FROM
  (SELECT * FROM db1.users) u
  JOIN (SELECT * FROM db2.orders) o ON u.id = o.user_id
WHERE o.total > 100;  -- More data transferred
```

### 3. Use Appropriate JOINs

Choose the right JOIN type:

```sql
-- INNER JOIN: Only matching rows
SELECT * FROM db1.users u
INNER JOIN db2.orders o ON u.id = o.user_id;

-- LEFT JOIN: All users, even without orders
SELECT * FROM db1.users u
LEFT JOIN db2.orders o ON u.id = o.user_id;
```

### 4. Index Join Columns

Ensure join columns have indexes:

```sql
-- PostgreSQL
CREATE INDEX idx_users_id ON users(id);

-- MySQL
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

### 5. Monitor Performance

Track query performance:

```typescript
const result = await federation.executeFederatedQuery(sql);

if (result.executionTime > 1000) {
  console.warn('Slow query detected:', result.executionTime, 'ms');
  console.log('Plan:', result.plan);
  console.log('Statistics:', result.statistics);
}
```

## Troubleshooting

### Issue: Query Too Slow

**Solution**:
1. Check execution plan: `ai-shell federate explain "..."`
2. Add indexes on join columns
3. Add WHERE filters to reduce data transfer
4. Use LIMIT for large result sets

### Issue: Out of Memory

**Solution**:
1. Reduce result set size with LIMIT
2. Add more aggressive WHERE filters
3. Process results in batches using streaming
4. Increase Node.js memory: `node --max-old-space-size=4096`

### Issue: Connection Timeout

**Solution**:
1. Check network connectivity between databases
2. Increase connection timeout in database config
3. Use connection pooling
4. Verify firewall rules

### Issue: Type Mismatch Errors

**Solution**:
1. Use explicit CAST in SQL
2. Check data type compatibility
3. Review error message for specific incompatible types

## Future Enhancements

- [ ] Support for UNION and INTERSECT
- [ ] Common Table Expressions (CTEs)
- [ ] Window functions across databases
- [ ] Parallel query execution
- [ ] Query result materialization
- [ ] Distributed transaction support
- [ ] Real-time query rewriting
- [ ] Machine learning-based query optimization

## References

- [Database Federation Concepts](https://en.wikipedia.org/wiki/Federated_database_system)
- [JOIN Algorithms](https://en.wikipedia.org/wiki/Join_(SQL))
- [Query Optimization](https://en.wikipedia.org/wiki/Query_optimization)
- [AI-Shell Documentation](../README.md)

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/aishell/issues
- Documentation: https://aishell.dev/docs
- Community: https://discord.gg/aishell
