# True Database Federation - Quick Reference

## Basic Syntax

```sql
SELECT columns
FROM database1.table1 [alias]
JOIN database2.table2 [alias] ON condition
[WHERE condition]
[GROUP BY columns]
[ORDER BY columns]
[LIMIT n]
```

## JOIN Types

### INNER JOIN
```sql
-- Only matching rows
SELECT u.name, o.total
FROM postgres.users u
INNER JOIN mysql.orders o ON u.id = o.user_id;
```

### LEFT JOIN
```sql
-- All left rows + matching right rows
SELECT u.name, o.total
FROM postgres.users u
LEFT JOIN mysql.orders o ON u.id = o.user_id;
```

### RIGHT JOIN
```sql
-- All right rows + matching left rows
SELECT u.name, o.total
FROM postgres.users u
RIGHT JOIN mysql.orders o ON u.id = o.user_id;
```

### FULL OUTER JOIN
```sql
-- All rows from both tables
SELECT u.name, o.total
FROM postgres.users u
FULL OUTER JOIN mysql.orders o ON u.id = o.user_id;
```

## Aggregate Functions

```sql
SELECT
  category,
  COUNT(*) as total_count,
  SUM(amount) as total_amount,
  AVG(amount) as avg_amount,
  MIN(amount) as min_amount,
  MAX(amount) as max_amount
FROM db1.products
JOIN db2.sales ON products.id = sales.product_id
GROUP BY category
HAVING SUM(amount) > 1000
ORDER BY total_amount DESC;
```

## CLI Commands

```bash
# Execute federated query
ai-shell federate "SELECT ... FROM ... JOIN ..."

# Show execution plan
ai-shell federate explain "SELECT ..."

# Show statistics
ai-shell federate stats
```

## MCP Tools

```javascript
// Execute query
db_federated_query({
  query: "SELECT u.name FROM db1.users u JOIN db2.orders o ON u.id = o.user_id",
  explain: false,
  cache: true
})

// Get execution plan
db_federated_explain({
  query: "SELECT ..."
})

// Get statistics
db_federated_stats({
  reset: false
})
```

## TypeScript API

```typescript
import { FederationEngine } from 'ai-shell/federation-engine';
import { DatabaseConnectionManager } from 'ai-shell/database-manager';
import { StateManager } from 'ai-shell/state-manager';

// Initialize
const stateManager = new StateManager();
const dbManager = new DatabaseConnectionManager(stateManager);
const federation = new FederationEngine(dbManager, stateManager);

// Execute query
const result = await federation.executeFederatedQuery(`
  SELECT u.name, o.total
  FROM postgres.users u
  JOIN mysql.orders o ON u.id = o.user_id
`);

console.log(`Found ${result.rowCount} rows`);
console.log(`Execution time: ${result.executionTime}ms`);

// Get execution plan
const explanation = await federation.explainQuery(sql);
console.log(explanation);

// Get statistics
const stats = federation.getStatistics();
console.log(`Cache hit rate: ${stats.cacheHits / (stats.cacheHits + stats.cacheMisses)}`);

// Clear caches
federation.clearCaches();

// Reset statistics
federation.resetStatistics();
```

## Event Monitoring

```typescript
federation.on('queryParsed', (parsed) => {
  console.log('Parsed query:', parsed.type);
});

federation.on('planGenerated', (plan) => {
  console.log('Strategy:', plan.strategy);
});

federation.on('stepCompleted', (step, rows) => {
  console.log(`Step ${step.id} returned ${rows} rows`);
});

federation.on('queryCompleted', (result) => {
  console.log(`Query completed in ${result.executionTime}ms`);
});
```

## Common Patterns

### Find all records + counts
```sql
SELECT u.name, COUNT(o.id) as order_count
FROM db1.users u
LEFT JOIN db2.orders o ON u.id = o.user_id
GROUP BY u.name;
```

### Calculate totals by category
```sql
SELECT p.category, SUM(o.amount) as total
FROM db1.products p
JOIN db2.orders o ON p.id = o.product_id
GROUP BY p.category
ORDER BY total DESC;
```

### Find top customers
```sql
SELECT u.name, SUM(o.total) as lifetime_value
FROM db1.users u
JOIN db2.orders o ON u.id = o.user_id
GROUP BY u.name
ORDER BY lifetime_value DESC
LIMIT 10;
```

### Multi-database join
```sql
SELECT u.name, o.total, p.name, c.category
FROM postgres.users u
JOIN mysql.orders o ON u.id = o.user_id
JOIN mysql.products p ON o.product_id = p.id
JOIN mongodb.categories c ON p.category_id = c.id;
```

### Time-series aggregation
```sql
SELECT
  DATE_TRUNC('month', o.created_at) as month,
  db1.region,
  SUM(o.total) as revenue
FROM postgres.orders o
JOIN mysql.customers db1 ON o.customer_id = db1.id
GROUP BY month, db1.region
ORDER BY month DESC;
```

## Performance Tips

1. **Add WHERE filters** to reduce data transfer
2. **Use LIMIT** for testing large queries
3. **Index join columns** in source databases
4. **Enable caching** for repeated queries
5. **Choose appropriate JOIN type** (INNER is fastest)
6. **Aggregate at source** when possible
7. **Monitor statistics** to identify bottlenecks

## Troubleshooting

### Query too slow?
- Check execution plan: `ai-shell federate explain "..."`
- Add indexes on join columns
- Use WHERE to filter early
- Increase cache size

### Out of memory?
- Reduce result set with LIMIT
- Add more WHERE filters
- Use streaming for large datasets

### Connection errors?
- Verify all databases are connected
- Check network connectivity
- Verify connection names match query

### Type errors?
- Use explicit CAST for complex types
- Check data type compatibility

## Supported SQL

✅ SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, LIMIT
✅ INNER, LEFT, RIGHT, FULL OUTER JOIN
✅ COUNT, SUM, AVG, MIN, MAX
✅ Multiple JOINs (3+ databases)
✅ Table and column aliases

❌ Distributed transactions
❌ Window functions
❌ CTEs (WITH clause)
❌ UNION/INTERSECT

## Limits

- Maximum result set: Limited by memory
- Maximum JOIN depth: Unlimited (but slow after 5+)
- Network latency: Affects cross-region queries
- Transaction support: No distributed transactions

## Best Practices

1. Test with LIMIT first
2. Use aliases for readability
3. Filter early with WHERE
4. Index join columns
5. Monitor performance
6. Cache frequently used queries
7. Use appropriate JOIN types

## Examples

See:
- `/examples/federation-demo.ts` - Complete demo
- `/docs/features/true-federation.md` - Full documentation
- `/tests/cli/federation-engine.test.ts` - Test examples
