# Interactive Query Builder - AI-Shell P3 Feature

**Status**: Priority 3 (P3) Feature
**Version**: 2.0.0
**Last Updated**: 2025-10-28

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Configuration](#configuration)
- [Use Cases](#use-cases)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [API Reference](#api-reference)

---

## Overview

The Interactive Query Builder is a visual, step-by-step interface for constructing complex database queries without writing SQL directly. It provides an intuitive way to:

- Build SELECT, INSERT, UPDATE, and DELETE queries
- Join multiple tables with visual relationship mapping
- Add filters, sorting, and grouping interactively
- Preview query results in real-time
- Save and reuse query templates
- Export queries in multiple formats

### Benefits

✅ **Beginner-Friendly**: No SQL knowledge required
✅ **Error Prevention**: Validates syntax in real-time
✅ **Time-Saving**: Build complex queries 3x faster
✅ **Reusable**: Save templates for common queries
✅ **Educational**: Learn SQL by seeing generated code
✅ **Multi-Database**: Works with PostgreSQL, MySQL, Oracle, MongoDB

---

## Features

### Core Capabilities

1. **Visual Table Selection**
   - Browse available tables and schemas
   - View table structure and relationships
   - Autocomplete for column names
   - Data type indicators

2. **Interactive Query Construction**
   - Drag-and-drop interface for joins
   - Point-and-click filter creation
   - Visual aggregate function builder
   - Nested query support

3. **Real-Time Preview**
   - Live query validation
   - Result preview (first 10 rows)
   - Execution time estimates
   - Resource usage predictions

4. **Query Templates**
   - Save commonly used queries
   - Parameter substitution
   - Version control for templates
   - Share templates across teams

5. **Export Options**
   - SQL script generation
   - JSON/CSV result export
   - Visualization integration
   - API endpoint generation

---

## Installation

### Prerequisites

```bash
# AI-Shell core installation
npm install -g aishell

# Query builder dependencies
npm install -g @aishell/query-builder

# Optional: UI enhancement packages
npm install -g blessed blessed-contrib
```

### Enable Query Builder Module

```bash
# Initialize query builder
aishell config set features.queryBuilder true

# Configure default database
aishell config set queryBuilder.defaultDatabase postgres

# Set UI preferences
aishell config set queryBuilder.theme dark
aishell config set queryBuilder.autoSave true
```

### Verify Installation

```bash
# Check query builder status
aishell query-builder --version
# Expected: Query Builder v2.0.0

# Test connection
aishell query-builder test
# Expected: ✓ Query Builder ready
```

---

## Quick Start

### Example 1: Basic SELECT Query

```bash
# Start interactive query builder
aishell qb

# Terminal UI opens:
┌─ Query Builder ───────────────────────────────────────────┐
│ [1] SELECT Query                                           │
│ [2] INSERT Query                                           │
│ [3] UPDATE Query                                           │
│ [4] DELETE Query                                           │
│ [5] Load Template                                          │
│                                                            │
│ Select query type: _                                       │
└────────────────────────────────────────────────────────────┘

# Select option 1, then follow prompts:
# > Select table: users
# > Select columns: id, name, email
# > Add filter? (y/n): y
# > Column: status
# > Operator: equals
# > Value: active
# > Order by? (y/n): y
# > Column: name
# > Direction: ASC

# Generated SQL:
SELECT id, name, email
FROM users
WHERE status = 'active'
ORDER BY name ASC;

# [E] Execute  [S] Save  [M] Modify  [X] Exit
```

### Example 2: Join Multiple Tables

```bash
# Start builder with join template
aishell qb --template join

# Interactive prompts:
┌─ Join Builder ────────────────────────────────────────────┐
│                                                            │
│  Primary Table: users                                      │
│  │                                                         │
│  ├─ JOIN orders (user_id = id)                            │
│  │  │                                                      │
│  │  └─ JOIN order_items (order_id = id)                   │
│  │                                                         │
│  └─ JOIN user_profiles (user_id = id)                     │
│                                                            │
│  [+] Add Join  [-] Remove  [C] Configure  [V] View SQL    │
└────────────────────────────────────────────────────────────┘

# Configure join conditions:
JOIN Type: INNER
ON: users.id = orders.user_id

# Generated SQL:
SELECT
    u.id,
    u.name,
    u.email,
    COUNT(o.id) as order_count,
    SUM(oi.price) as total_spent
FROM users u
INNER JOIN orders o ON u.id = o.user_id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN user_profiles up ON u.id = up.user_id
GROUP BY u.id, u.name, u.email
ORDER BY total_spent DESC;
```

### Example 3: Save and Load Templates

```bash
# Save current query as template
aishell qb save --name "active-users-report" \
  --description "List all active users with order statistics" \
  --parameters "status,min_orders"

# Template saved: active-users-report
# Parameters:
#   - status (default: active)
#   - min_orders (default: 1)

# Load template later
aishell qb load active-users-report

# Use with parameters
aishell qb load active-users-report \
  --param status=premium \
  --param min_orders=5

# List all templates
aishell qb templates list
```

---

## Command Reference

### Main Commands

#### `aishell query-builder` (alias: `qb`)
Start the interactive query builder.

```bash
aishell qb [options]

Options:
  -d, --database <name>      Target database connection
  -t, --template <name>      Load saved template
  -m, --mode <type>          Query mode (select|insert|update|delete)
  -i, --interactive          Force interactive mode
  -o, --output <format>      Output format (sql|json|csv)
  --dry-run                  Preview only, don't execute
  --theme <name>             UI theme (dark|light|high-contrast)
  -v, --verbose              Show detailed output
  -h, --help                 Show help
```

**Examples:**

```bash
# Start in SELECT mode
aishell qb --mode select

# Load template with custom database
aishell qb --template daily-sales --database production

# Build query and export SQL
aishell qb --output sql --dry-run > query.sql

# High contrast theme for accessibility
aishell qb --theme high-contrast
```

---

#### `aishell qb select`
Build SELECT queries.

```bash
aishell qb select [table] [options]

Options:
  -c, --columns <cols>       Columns to select (comma-separated)
  -w, --where <condition>    WHERE clause
  -j, --join <table:on>      JOIN clause
  -g, --group-by <cols>      GROUP BY columns
  -o, --order-by <col:dir>   ORDER BY column
  -l, --limit <n>            LIMIT results
  --distinct                 Use DISTINCT
  --aggregate <func:col>     Add aggregate function

Examples:
  aishell qb select users -c "id,name,email"
  aishell qb select users -c "name,email" -w "status='active'" -l 10
  aishell qb select users -j "orders:users.id=orders.user_id"
  aishell qb select orders --aggregate "COUNT:*,SUM:total" -g "user_id"
```

---

#### `aishell qb insert`
Build INSERT queries.

```bash
aishell qb insert <table> [options]

Options:
  -v, --values <data>        Values as JSON or key=value pairs
  -f, --file <path>          Read values from file
  -b, --batch                Batch insert mode
  --from-select              INSERT FROM SELECT

Examples:
  aishell qb insert users --values '{"name":"John","email":"john@example.com"}'
  aishell qb insert users -v "name=Jane" -v "email=jane@example.com"
  aishell qb insert users --file users-data.json --batch
  aishell qb insert users_archive --from-select "SELECT * FROM users WHERE archived=true"
```

---

#### `aishell qb update`
Build UPDATE queries.

```bash
aishell qb update <table> [options]

Options:
  -s, --set <assignments>    SET clauses (col=value)
  -w, --where <condition>    WHERE clause
  --confirm                  Require confirmation before execute

Examples:
  aishell qb update users --set "status=active" --where "id=123"
  aishell qb update users --set "last_login=NOW()" --where "status='active'"
  aishell qb update products --set "price=price*1.1" --where "category='electronics'" --confirm
```

---

#### `aishell qb delete`
Build DELETE queries (with safety checks).

```bash
aishell qb delete <table> [options]

Options:
  -w, --where <condition>    WHERE clause (required)
  --force                    Skip safety confirmation
  --soft-delete              Use soft delete if available

Examples:
  aishell qb delete users --where "id=123"
  aishell qb delete sessions --where "expired_at < NOW()"
  aishell qb delete users --where "inactive=true" --soft-delete
```

---

### Template Management

#### `aishell qb save`
Save current query as template.

```bash
aishell qb save <name> [options]

Options:
  -d, --description <text>   Template description
  -p, --parameters <params>  Comma-separated parameter list
  -c, --category <cat>       Template category
  -t, --tags <tags>          Tags for search

Examples:
  aishell qb save daily-report --description "Daily sales report"
  aishell qb save user-search --parameters "status,role,date_from"
  aishell qb save customer-analysis --category analytics --tags "customer,revenue"
```

---

#### `aishell qb load`
Load saved template.

```bash
aishell qb load <name> [options]

Options:
  --param <key=value>        Override parameter value
  --list-params              Show template parameters
  -e, --edit                 Edit template after loading

Examples:
  aishell qb load daily-report
  aishell qb load user-search --param status=premium --param role=admin
  aishell qb load sales-monthly --edit
```

---

#### `aishell qb templates`
Manage query templates.

```bash
aishell qb templates <command> [options]

Commands:
  list                       List all templates
  show <name>                Show template details
  edit <name>                Edit template
  delete <name>              Delete template
  export <name> <file>       Export template
  import <file>              Import template
  search <query>             Search templates

Examples:
  aishell qb templates list
  aishell qb templates list --category reports
  aishell qb templates show daily-report
  aishell qb templates search "sales"
  aishell qb templates export daily-report report.json
  aishell qb templates import team-templates.json
```

---

### Query Operations

#### `aishell qb execute`
Execute query from builder.

```bash
aishell qb execute [options]

Options:
  -q, --query <sql>          Execute raw SQL
  -t, --template <name>      Execute saved template
  -o, --output <format>      Output format (table|json|csv)
  -f, --file <path>          Save results to file
  --timeout <ms>             Query timeout
  --explain                  Show execution plan

Examples:
  aishell qb execute --query "SELECT * FROM users LIMIT 10"
  aishell qb execute --template daily-report --output csv
  aishell qb execute -t weekly-sales -f report.csv
  aishell qb execute -q "SELECT * FROM large_table" --explain
```

---

#### `aishell qb validate`
Validate query syntax.

```bash
aishell qb validate [options]

Options:
  -q, --query <sql>          Query to validate
  -f, --file <path>          Validate queries in file
  -s, --strict               Enable strict validation

Examples:
  aishell qb validate --query "SELECT * FROM users"
  aishell qb validate --file queries.sql
  aishell qb validate -q "SELCT * FROM users" # Shows error
```

---

#### `aishell qb optimize`
Get query optimization suggestions.

```bash
aishell qb optimize [options]

Options:
  -q, --query <sql>          Query to optimize
  -t, --template <name>      Optimize template
  --auto-fix                 Apply suggested fixes

Examples:
  aishell qb optimize --query "SELECT * FROM users WHERE status='active'"
  # Suggestion: Avoid SELECT *, specify columns
  # Suggestion: Add index on status column

  aishell qb optimize --template slow-report --auto-fix
```

---

## Configuration

### Query Builder Settings

Location: `~/.aishell/config/query-builder.json`

```json
{
  "queryBuilder": {
    "enabled": true,
    "defaultDatabase": "postgres",
    "autoSave": true,
    "autoComplete": true,
    "ui": {
      "theme": "dark",
      "keyBindings": "vim",
      "showHints": true,
      "previewRows": 10
    },
    "validation": {
      "strictMode": false,
      "warnOnSelectStar": true,
      "requireWhereOnDelete": true,
      "maxResultRows": 1000
    },
    "templates": {
      "directory": "~/.aishell/templates",
      "autoBackup": true,
      "shareEnabled": false
    },
    "performance": {
      "cacheQueries": true,
      "cacheTTL": 300,
      "explainThreshold": 100
    }
  }
}
```

### Update Configuration

```bash
# Set individual options
aishell config set queryBuilder.ui.theme light
aishell config set queryBuilder.validation.strictMode true
aishell config set queryBuilder.templates.shareEnabled true

# View current configuration
aishell config get queryBuilder

# Reset to defaults
aishell config reset queryBuilder
```

---

## Use Cases

### Use Case 1: Customer Analysis Report

**Scenario**: Generate a report of top customers by revenue.

```bash
# Start query builder
aishell qb

# Step-by-step builder:
Step 1: Select query type
  → SELECT

Step 2: Select primary table
  → customers

Step 3: Select columns
  → id, name, email, total_orders, total_revenue

Step 4: Add joins?
  → Yes
  → Table: orders
  → Type: LEFT JOIN
  → Condition: customers.id = orders.customer_id

Step 5: Add aggregations?
  → Yes
  → COUNT(orders.id) AS total_orders
  → SUM(orders.total) AS total_revenue

Step 6: Add filters?
  → Yes
  → total_revenue > 1000

Step 7: Group by?
  → customers.id, customers.name, customers.email

Step 8: Order by?
  → total_revenue DESC

Step 9: Limit?
  → 50

Generated SQL:
SELECT
    c.id,
    c.name,
    c.email,
    COUNT(o.id) AS total_orders,
    SUM(o.total) AS total_revenue
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name, c.email
HAVING total_revenue > 1000
ORDER BY total_revenue DESC
LIMIT 50;

Execute? (y/n): y
Save as template? (y/n): y
Template name: top-customers-by-revenue
```

---

### Use Case 2: Data Migration Query

**Scenario**: Move archived orders to separate table.

```bash
# Start with INSERT template
aishell qb --template insert-from-select

# Interactive prompts:
Target table: orders_archive

Source query:
  → Use builder? (y/n): y

  Table: orders
  Columns: * (all)
  Where: archived = true AND created_at < '2024-01-01'

Generated SQL:
INSERT INTO orders_archive
SELECT * FROM orders
WHERE archived = true
  AND created_at < '2024-01-01';

Preview: 2,547 rows will be migrated
Continue? (y/n): y

Success! 2,547 rows inserted.

Delete from source? (y/n): n
```

---

### Use Case 3: Performance Debugging

**Scenario**: Analyze slow query performance.

```bash
# Load existing slow query
aishell qb load monthly-sales-report

# Current query execution time: 8.5s

# Get optimization suggestions
aishell qb optimize --template monthly-sales-report

┌─ Optimization Suggestions ────────────────────────────────┐
│                                                            │
│ ⚠️  HIGH IMPACT (3)                                        │
│                                                            │
│ 1. Missing Index                                           │
│    Table: orders                                           │
│    Column: created_at                                      │
│    Estimated speedup: 65%                                  │
│    Fix: CREATE INDEX idx_orders_created ON orders(created_at) │
│                                                            │
│ 2. Inefficient Join                                        │
│    Current: CROSS JOIN detected                            │
│    Suggestion: Add explicit JOIN condition                 │
│    Estimated speedup: 40%                                  │
│                                                            │
│ 3. SELECT *                                                │
│    Fetching unnecessary columns                            │
│    Suggestion: Specify required columns                    │
│    Estimated speedup: 15%                                  │
│                                                            │
│ 📊 MEDIUM IMPACT (2)                                       │
│                                                            │
│ 4. Subquery in WHERE                                       │
│    Can be converted to JOIN                                │
│    Estimated speedup: 20%                                  │
│                                                            │
│ 5. No LIMIT clause                                         │
│    Query returns all rows                                  │
│    Suggestion: Add LIMIT or pagination                     │
│                                                            │
│ [A] Apply All  [S] Apply Selected  [V] View Fixed Query   │
└────────────────────────────────────────────────────────────┘

# Apply all fixes
Select: A

Optimized query saved as: monthly-sales-report-v2
New execution time: 1.2s (7x faster!)
```

---

## Advanced Features

### 1. Nested Queries / Subqueries

```bash
# Build subquery in WHERE clause
aishell qb select orders

# In WHERE condition builder:
Column: customer_id
Operator: IN
Value: <subquery>

# Subquery builder opens:
SELECT id FROM customers WHERE status = 'premium'

# Final query:
SELECT * FROM orders
WHERE customer_id IN (
    SELECT id FROM customers WHERE status = 'premium'
);
```

---

### 2. Common Table Expressions (CTE)

```bash
# Enable CTE mode
aishell qb --mode cte

# Define first CTE
CTE Name: active_users
Query: SELECT id, name FROM users WHERE status = 'active'

# Define second CTE
CTE Name: user_orders
Query: SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id

# Main query
SELECT au.name, uo.order_count
FROM active_users au
JOIN user_orders uo ON au.id = uo.user_id

# Generated SQL:
WITH active_users AS (
    SELECT id, name FROM users WHERE status = 'active'
),
user_orders AS (
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    GROUP BY user_id
)
SELECT au.name, uo.order_count
FROM active_users au
JOIN user_orders uo ON au.id = uo.user_id;
```

---

### 3. Window Functions

```bash
# Start builder with window function
aishell qb select orders --advanced

# Add window function:
Function: ROW_NUMBER()
Over: PARTITION BY customer_id ORDER BY created_at DESC
Alias: order_rank

# Generated SQL:
SELECT
    id,
    customer_id,
    total,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC
    ) as order_rank
FROM orders;
```

---

### 4. Query Variables/Parameters

```bash
# Define parameterized query
aishell qb select users

# Add parameter:
Parameter: @status
Type: STRING
Default: active

WHERE status = @status

# Save as template with parameters
aishell qb save user-by-status --parameters "status"

# Use with different values
aishell qb load user-by-status --param status=inactive
```

---

### 5. Query Versioning

```bash
# Save query with version
aishell qb save customer-report --version 1.0.0

# Make changes and save new version
aishell qb load customer-report
# ... make changes ...
aishell qb save customer-report --version 1.1.0

# List versions
aishell qb templates versions customer-report
# v1.0.0 - 2025-10-01 - Initial version
# v1.1.0 - 2025-10-15 - Added revenue column

# Compare versions
aishell qb templates diff customer-report 1.0.0 1.1.0

# Rollback to previous version
aishell qb templates rollback customer-report 1.0.0
```

---

## Troubleshooting

### Issue 1: Query Builder Won't Start

**Symptoms**: Error when running `aishell qb`

```bash
Error: Query Builder not enabled
```

**Solution**:
```bash
# Enable query builder
aishell config set features.queryBuilder true

# Install dependencies
npm install -g blessed blessed-contrib

# Verify installation
aishell qb --version
```

---

### Issue 2: Database Connection Failed

**Symptoms**: Cannot connect to database in query builder

**Solution**:
```bash
# Test database connection first
aishell connect test --database mydb

# If connection works, specify database explicitly
aishell qb --database mydb

# Check connection config
aishell config get connections.mydb
```

---

### Issue 3: Template Not Found

**Symptoms**: `Template 'xyz' not found`

**Solution**:
```bash
# List all templates
aishell qb templates list

# Check template directory
aishell config get queryBuilder.templates.directory

# Verify template file exists
ls -la ~/.aishell/templates/

# Re-import template
aishell qb templates import xyz.json
```

---

### Issue 4: Query Validation Errors

**Symptoms**: Query marked as invalid but seems correct

**Solution**:
```bash
# Disable strict mode temporarily
aishell config set queryBuilder.validation.strictMode false

# Get detailed validation report
aishell qb validate --query "YOUR_QUERY" --verbose

# Check database-specific syntax
aishell qb validate --database postgres --query "YOUR_QUERY"
```

---

### Issue 5: UI Rendering Issues

**Symptoms**: Broken UI, garbled characters

**Solution**:
```bash
# Try different theme
aishell qb --theme light

# Check terminal compatibility
echo $TERM
# Should be xterm-256color or similar

# Set explicit terminal type
export TERM=xterm-256color
aishell qb

# Use fallback ASCII mode
aishell qb --ascii-mode
```

---

## Best Practices

### 1. Use Templates for Repeated Queries

❌ **Don't**: Rebuild same query repeatedly
✅ **Do**: Save as template with parameters

```bash
# Good practice
aishell qb save daily-active-users --parameters "date"
aishell qb load daily-active-users --param date="2025-10-28"
```

---

### 2. Always Preview Before Execute

❌ **Don't**: Execute large DELETE/UPDATE directly
✅ **Do**: Preview and verify first

```bash
# Good practice
aishell qb delete old_logs --where "created_at < '2024-01-01'" --dry-run
# Review affected rows
# Then execute:
aishell qb execute --confirm
```

---

### 3. Use Query Optimization

❌ **Don't**: Accept slow queries without investigation
✅ **Do**: Analyze and optimize

```bash
# Good practice
aishell qb optimize --template my-report
# Review suggestions
# Apply fixes
aishell qb optimize --template my-report --auto-fix
```

---

### 4. Version Your Important Templates

❌ **Don't**: Overwrite templates without backup
✅ **Do**: Use version control

```bash
# Good practice
aishell qb save critical-report --version 1.0.0
aishell qb save critical-report --version 1.1.0
aishell qb templates export critical-report backup.json
```

---

### 5. Validate Before Saving

❌ **Don't**: Save broken queries
✅ **Do**: Validate first

```bash
# Good practice
aishell qb validate --query "$(cat current-query.sql)"
# If valid:
aishell qb save my-query
```

---

## API Reference

### JavaScript/TypeScript API

```typescript
import { QueryBuilder } from '@aishell/query-builder';

// Initialize builder
const qb = new QueryBuilder({
  database: 'postgres',
  connection: connectionConfig
});

// Build SELECT query
const selectQuery = qb
  .select('users')
  .columns(['id', 'name', 'email'])
  .where('status', '=', 'active')
  .orderBy('name', 'ASC')
  .limit(10)
  .build();

console.log(selectQuery.sql);
// SELECT id, name, email FROM users WHERE status = 'active' ORDER BY name ASC LIMIT 10

// Execute query
const results = await selectQuery.execute();

// Build JOIN query
const joinQuery = qb
  .select('users')
  .join('orders', 'users.id', '=', 'orders.user_id')
  .columns(['users.name', 'COUNT(orders.id) as order_count'])
  .groupBy('users.id', 'users.name')
  .build();

// Build INSERT query
const insertQuery = qb
  .insert('users')
  .values({
    name: 'John Doe',
    email: 'john@example.com',
    status: 'active'
  })
  .build();

// Build UPDATE query
const updateQuery = qb
  .update('users')
  .set({ status: 'inactive' })
  .where('last_login', '<', '2024-01-01')
  .build();

// Save as template
await qb.saveTemplate('user-updates', updateQuery, {
  parameters: ['status', 'date'],
  description: 'Update user status by date'
});

// Load template
const template = await qb.loadTemplate('user-updates');
const query = template.bind({
  status: 'active',
  date: '2025-01-01'
});
```

---

## Summary

The Interactive Query Builder provides a powerful, user-friendly way to construct database queries without deep SQL knowledge. Key features include:

- 🎯 Visual query construction
- 💾 Template management with versioning
- ⚡ Real-time validation and optimization
- 🔄 Multi-database support
- 📊 Result preview and export

For more information:
- [Template System Guide](./template-system.md)
- [Pattern Detection](./pattern-detection.md)
- [Dashboard Guide](./enhanced-dashboard.md)

---

**Need Help?**
- 📖 [AI-Shell Documentation](../README.md)
- 💬 [Community Forum](https://github.com/yourusername/aishell/discussions)
- 🐛 [Report Issues](https://github.com/yourusername/aishell/issues)
