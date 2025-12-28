# Query Explainer and Dry-Run Features

## Overview

The Query Explainer and Dry-Run features provide comprehensive query analysis, execution plan visualization, and safe query validation for AI-Shell commands.

## Features

### 1. **--explain Flag**
Shows detailed query execution plan with performance insights, bottleneck identification, and optimization suggestions.

### 2. **--dry-run Flag**
Validates queries without execution, checking syntax, permissions, and estimating impact.

### 3. **Multi-Database Support**
Works with PostgreSQL, MySQL, and SQLite databases.

### 4. **Visual Execution Plans**
ASCII art visualization of query execution flow.

### 5. **Performance Analysis**
- Cost estimation
- Row count predictions
- Execution time estimates
- Bottleneck detection

### 6. **Optimization Suggestions**
- Index recommendations
- Query rewrite suggestions
- Schema optimization tips

## Usage

### Basic Explain

```bash
# Explain a SELECT query
ai-shell explain "SELECT * FROM users WHERE email = 'test@example.com'"

# Explain with JSON output
ai-shell explain "SELECT * FROM users" --format json
```

### Dry-Run Mode

```bash
# Validate without execution
ai-shell optimize "DELETE FROM users WHERE inactive = true" --dry-run

# Check federated query
ai-shell federate "SELECT * FROM users" --databases db1,db2 --dry-run
```

### Combined Usage

```bash
# Optimize with explain
ai-shell optimize "SELECT * FROM orders o JOIN users u ON o.user_id = u.id" --explain

# Explain with analysis
ai-shell explain "SELECT COUNT(*) FROM logs" --analyze
```

## Command Reference

### ai-shell explain

Explains SQL queries with AI-powered insights.

**Options:**
- `--format <type>` - Output format: text or json (default: text)
- `--analyze` - Include detailed performance analysis
- `--dry-run` - Validate query without execution

**Examples:**
```bash
ai-shell explain "SELECT * FROM users WHERE created_at > NOW() - INTERVAL 7 DAY"
ai-shell exp "SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o GROUP BY u.id"
ai-shell explain "UPDATE users SET active = false" --dry-run
```

### ai-shell optimize

Optimizes SQL queries with explain and dry-run support.

**Options:**
- `--explain` - Show query execution plan
- `--dry-run` - Validate without executing
- `--format <type>` - Output format (default: text)

**Examples:**
```bash
ai-shell optimize "SELECT * FROM users WHERE id > 100" --explain
ai-shell opt "SELECT * FROM users" --dry-run
```

### ai-shell federate

Executes federated queries with explain support.

**Options:**
- `--databases <list>` - Comma-separated database names (required)
- `--explain` - Show execution plan
- `--dry-run` - Validate without executing

**Examples:**
```bash
ai-shell federate "SELECT * FROM users" -d db1,db2 --explain
ai-shell fed "DELETE FROM users" -d db1,db2 --dry-run
```

## Explanation Output

### Text Format

```
═══════════════════════════════════════════════════════════════
                    QUERY EXECUTION PLAN
═══════════════════════════════════════════════════════════════

Database: production (postgresql)

Query:
───────────────────────────────────────────────────────────────
SELECT * FROM users WHERE email = 'test@example.com'
───────────────────────────────────────────────────────────────

Execution Metrics:
───────────────────────────────────────────────────────────────
  Estimated Cost:     125.50
  Estimated Rows:     1,000
  Estimated Time:     125ms

Plan Analysis:
───────────────────────────────────────────────────────────────
  Index Scans:        0
  Table Scans:        1
  Joins:              0
  Sorts:              0
  Temp Tables:        0

Visual Execution Plan:
───────────────────────────────────────────────────────────────
Seq Scan [cost: 125.50] [rows: 1,000]
   Table: users
   Scan: sequential
   Filter: email = 'test@example.com'

⚠️  Performance Bottlenecks:
───────────────────────────────────────────────────────────────
1. 🟠 Sequential scan on users examining 1,000 rows
   Type:        sequential_scan
   Severity:    MEDIUM
   Location:    Root
   Impact:      Medium - Full table scan without index
   Fix:         Consider adding an index on the columns used in WHERE/JOIN clauses for users

💡 Optimization Suggestions:
───────────────────────────────────────────────────────────────
1. 🔸 Add indexes to improve query performance
   Type:        index
   Priority:    MEDIUM
   Description: Consider adding an index on the columns used in WHERE/JOIN clauses for users
   Improvement: 50-80%

Permissions Check:
───────────────────────────────────────────────────────────────
  ✓ All required permissions granted

═══════════════════════════════════════════════════════════════
```

### JSON Format

```json
{
  "query": "SELECT * FROM users WHERE email = 'test@example.com'",
  "database": "production",
  "databaseType": "postgresql",
  "executionPlan": {
    "nodeType": "Seq Scan",
    "operation": "Seq Scan",
    "cost": 125.50,
    "rows": 1000,
    "table": "users",
    "scanType": "sequential"
  },
  "estimatedCost": 125.50,
  "estimatedRows": 1000,
  "estimatedTime": "125ms",
  "bottlenecks": [
    {
      "type": "sequential_scan",
      "severity": "medium",
      "description": "Sequential scan on users examining 1,000 rows",
      "location": "Root",
      "estimatedImpact": "Medium - Full table scan without index",
      "recommendation": "Consider adding an index on the columns used in WHERE/JOIN clauses for users"
    }
  ],
  "suggestions": [
    {
      "type": "index",
      "priority": "medium",
      "title": "Add indexes to improve query performance",
      "description": "Consider adding an index on the columns used in WHERE/JOIN clauses for users",
      "estimatedImprovement": "50-80%"
    }
  ],
  "metrics": {
    "indexUsage": 0,
    "tableScans": 1,
    "joins": 0,
    "sorts": 0,
    "tempTables": 0
  },
  "permissions": {
    "hasPermission": true,
    "requiredPermissions": ["SELECT"]
  }
}
```

## Bottleneck Types

### 1. Sequential Scan
Full table scans without index usage.

**Severity:** Medium to Critical (based on row count)
**Fix:** Add indexes on frequently queried columns

### 2. Missing Index
Queries that could benefit from indexes.

**Severity:** Medium
**Fix:** Create appropriate indexes

### 3. Nested Loop Join
Inefficient join strategy for large datasets.

**Severity:** High
**Fix:** Add indexes on join columns or rewrite query

### 4. Large Result Set
Queries returning excessive rows.

**Severity:** High
**Fix:** Add LIMIT, filters, or implement pagination

### 5. Sort Operation
Expensive sorting on large datasets.

**Severity:** High
**Fix:** Add index on ORDER BY columns

### 6. Temporary Tables
Use of temporary tables in query execution.

**Severity:** Medium
**Fix:** Optimize query structure or add indexes

## Optimization Suggestion Types

### 1. Index Suggestions
Recommendations for creating or modifying indexes.

**Priority:** Low to High
**Impact:** 40-95% improvement

### 2. Query Rewrite
Suggestions to restructure queries.

**Priority:** Medium to High
**Impact:** 50-80% improvement

### 3. Schema Changes
Database schema modifications.

**Priority:** Low to Medium
**Impact:** Varies

### 4. Configuration
Database configuration adjustments.

**Priority:** Low
**Impact:** 10-30% improvement

## Dry-Run Output

```
═══════════════════════════════════════════════════════════════
                    DRY RUN MODE - NO EXECUTION
═══════════════════════════════════════════════════════════════

Query Validation:
───────────────────────────────────────────────────────────────
  Query: DELETE FROM users WHERE inactive = true
  Is Destructive: ⚠️  YES
  Estimated Rows: 150
  Estimated Cost: 75.25
  Indexes Used: idx_users_inactive

Warnings:
───────────────────────────────────────────────────────────────
  ⚠️ This is a DESTRUCTIVE operation that will modify or delete data

═══════════════════════════════════════════════════════════════
Status: ✓ Validation passed - Query is safe to execute
═══════════════════════════════════════════════════════════════
```

## Integration with Existing Features

### Query Optimizer
```bash
# Optimize with execution plan
ai-shell optimize "SELECT * FROM users WHERE active = true" --explain
```

### Query Federation
```bash
# Validate federated query
ai-shell federate "SELECT * FROM users" -d db1,db2,db3 --dry-run
```

### SQL Explainer
```bash
# Explain with performance analysis
ai-shell explain "SELECT * FROM logs ORDER BY created_at DESC" --analyze
```

## Best Practices

### 1. Use --dry-run for Destructive Operations
Always validate DELETE, UPDATE, and DROP operations before execution.

```bash
ai-shell optimize "DELETE FROM old_logs WHERE created_at < NOW() - INTERVAL 1 YEAR" --dry-run
```

### 2. Explain Complex Queries
Use explain to understand performance characteristics of complex queries.

```bash
ai-shell explain "SELECT u.*, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id HAVING COUNT(o.id) > 10" --format json
```

### 3. Regular Performance Audits
Periodically explain production queries to identify optimization opportunities.

```bash
ai-shell analyze-slow-queries --threshold 100
```

### 4. Document Optimization Decisions
Export explain output as JSON for documentation.

```bash
ai-shell explain "SELECT * FROM users WHERE email = ?" --format json > docs/query-plans/user-email-lookup.json
```

## Performance Considerations

- **Explain Overhead:** Minimal (<50ms for most queries)
- **Dry-Run Safety:** No data modifications
- **Multi-Database:** Works across PostgreSQL, MySQL, SQLite
- **Scalability:** Handles queries of any complexity

## Troubleshooting

### Issue: "No active database connection"
**Solution:** Ensure you have an active database connection before running explain/dry-run.

```bash
ai-shell connect --type postgresql --host localhost --database mydb
```

### Issue: "Unsupported database type"
**Solution:** Only PostgreSQL, MySQL, and SQLite are currently supported.

### Issue: Explain output is empty
**Solution:** Check that the database user has permissions to run EXPLAIN queries.

## API Integration

The Query Explainer can be used programmatically:

```typescript
import { QueryExplainer } from 'ai-shell/cli/query-explainer';
import { DatabaseConnectionManager } from 'ai-shell/cli/db-connection-manager';
import { ErrorHandler } from 'ai-shell/core/error-handler';

const connectionManager = new DatabaseConnectionManager(stateManager);
const errorHandler = new ErrorHandler();
const explainer = new QueryExplainer(connectionManager, errorHandler);

// Explain query
const result = await explainer.explain(
  'SELECT * FROM users WHERE id = 1',
  'mydb',
  'json'
);

// Format output
const formatted = explainer.formatExplanation(result, 'text');
console.log(formatted);
```

## Future Enhancements

- [ ] Real-time query monitoring
- [ ] Historical performance tracking
- [ ] Automated optimization suggestions
- [ ] Query cost prediction based on table statistics
- [ ] Visual query plan diagrams (SVG/PNG export)
- [ ] Integration with monitoring tools (Grafana, Datadog)
- [ ] Machine learning-based optimization recommendations

## Related Documentation

- [Query Optimizer](./query-optimizer.md)
- [SQL Explainer](./sql-explainer.md)
- [Query Federation](./query-federation.md)
- [Performance Monitoring](./health-monitor.md)
