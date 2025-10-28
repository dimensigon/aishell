# Alias System Guide

The AI Shell Alias System provides a powerful way to create named shortcuts for frequently used queries with support for parameterized queries, templates, and usage tracking.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Usage](#basic-usage)
3. [Parameterized Queries](#parameterized-queries)
4. [Templates](#templates)
5. [Import/Export](#importexport)
6. [Statistics and Analytics](#statistics-and-analytics)
7. [Advanced Features](#advanced-features)
8. [Best Practices](#best-practices)

## Quick Start

### Installation

The alias system is built into AI Shell. No additional installation required.

### Create Your First Alias

```bash
# Simple alias without parameters
ai-shell alias add my-users "SELECT * FROM users" \
  --description "Get all users"

# Run the alias
ai-shell alias run my-users
```

## Basic Usage

### Adding Aliases

```bash
# Basic alias
ai-shell alias add get-orders "SELECT * FROM orders ORDER BY created_at DESC"

# With description
ai-shell alias add active-users "SELECT * FROM users WHERE status = 'active'" \
  --description "Get all active users"

# With tags for organization
ai-shell alias add daily-report "SELECT * FROM reports WHERE date = CURRENT_DATE" \
  --description "Today's report" \
  --tags "reports,daily"
```

### Listing Aliases

```bash
# List all aliases (compact view)
ai-shell alias list

# Verbose view with full queries
ai-shell alias list --verbose

# Filter by tags
ai-shell alias list --tags "reports,analytics"

# Output as JSON
ai-shell alias list --format json

# Output as YAML
ai-shell alias list --format yaml
```

### Viewing Alias Details

```bash
# Show detailed information about an alias
ai-shell alias show my-users
```

Output:
```
my-users
────────────────────────────────────────────────────────────────────────────────
Description: Get all users
Query: SELECT * FROM users

Created: 2025-01-15 10:30:00
Usage count: 15
Last used: 2025-01-28 14:22:00
────────────────────────────────────────────────────────────────────────────────

Usage:
  ai-shell alias run my-users
```

### Editing Aliases

```bash
# Update query
ai-shell alias edit my-users --query "SELECT * FROM users WHERE deleted_at IS NULL"

# Update description
ai-shell alias edit my-users --description "Get all non-deleted users"

# Update tags
ai-shell alias edit my-users --tags "users,active"
```

### Renaming Aliases

```bash
# Rename an alias
ai-shell alias rename old-name new-name
```

### Removing Aliases

```bash
# Remove an alias
ai-shell alias remove my-users

# Shorthand
ai-shell alias rm my-users
```

## Parameterized Queries

Parameterized queries allow you to create reusable aliases with variable inputs.

### Parameter Types

The alias system supports four parameter types:

- `string` - Text values
- `number` - Numeric values (integers and decimals)
- `date` - Date values (YYYY-MM-DD format)
- `boolean` - Boolean values (true/false)

### Parameter Format

Parameters are defined using the format: `name:type:required:default`

- `name` - Parameter name
- `type` - Parameter type (string, number, date, boolean)
- `required` - Whether the parameter is required (true/false)
- `default` - Default value if parameter is not provided (optional)

### Single Parameter Example

```bash
# Create alias with one parameter
ai-shell alias add user-by-id "SELECT * FROM users WHERE id = $1" \
  --description "Get user by ID" \
  --parameters "user_id:number:true"

# Run with parameter
ai-shell alias run user-by-id 123
```

Generates:
```sql
SELECT * FROM users WHERE id = 123
```

### Multiple Parameters Example

```bash
# Create alias with multiple parameters
ai-shell alias add date-range-orders \
  "SELECT * FROM orders WHERE created_at BETWEEN $1 AND $2" \
  --description "Get orders in date range" \
  --parameters "start_date:date:true,end_date:date:true"

# Run with parameters
ai-shell alias run date-range-orders "2025-01-01" "2025-01-31"
```

Generates:
```sql
SELECT * FROM orders WHERE created_at BETWEEN '2025-01-01' AND '2025-01-31'
```

### Optional Parameters with Defaults

```bash
# Create alias with optional parameters
ai-shell alias add user-search \
  "SELECT * FROM users WHERE status = $1 LIMIT $2" \
  --parameters "status:string:false:active,limit:number:false:10"

# Run without parameters (uses defaults)
ai-shell alias run user-search
# Generates: SELECT * FROM users WHERE status = 'active' LIMIT 10

# Run with one parameter
ai-shell alias run user-search "inactive"
# Generates: SELECT * FROM users WHERE status = 'inactive' LIMIT 10

# Run with both parameters
ai-shell alias run user-search "active" 50
# Generates: SELECT * FROM users WHERE status = 'active' LIMIT 50
```

### Parameter Type Examples

#### String Parameters

```bash
ai-shell alias add search-products \
  "SELECT * FROM products WHERE name LIKE $1" \
  --parameters "search_term:string:true"

ai-shell alias run search-products "%laptop%"
# Generates: SELECT * FROM products WHERE name LIKE '%laptop%'
```

#### Number Parameters

```bash
ai-shell alias add top-products \
  "SELECT * FROM products ORDER BY sales DESC LIMIT $1" \
  --parameters "limit:number:true"

ai-shell alias run top-products 10
# Generates: SELECT * FROM products ORDER BY sales DESC LIMIT 10
```

#### Date Parameters

```bash
ai-shell alias add orders-after \
  "SELECT * FROM orders WHERE created_at > $1" \
  --parameters "after_date:date:true"

ai-shell alias run orders-after "2025-01-01"
# Generates: SELECT * FROM orders WHERE created_at > '2025-01-01'
```

#### Boolean Parameters

```bash
ai-shell alias add users-by-status \
  "SELECT * FROM users WHERE active = $1" \
  --parameters "is_active:boolean:true"

ai-shell alias run users-by-status true
# Generates: SELECT * FROM users WHERE active = true
```

### Complex Parameterized Query Example

```bash
# Create complex query with multiple parameter types
ai-shell alias add advanced-search \
  "SELECT * FROM orders
   WHERE user_id = $1
   AND status = $2
   AND created_at BETWEEN $3 AND $4
   AND total > $5
   LIMIT $6" \
  --parameters "user_id:number:true,status:string:false:pending,start_date:date:true,end_date:date:true,min_total:number:false:0,limit:number:false:100"

# Run with required parameters only
ai-shell alias run advanced-search 123 "2025-01-01" "2025-01-31"

# Run with all parameters
ai-shell alias run advanced-search 123 "completed" "2025-01-01" "2025-01-31" 50 25
```

### Testing Queries (Dry Run)

```bash
# Test parameter substitution without executing
ai-shell alias run user-by-id 123 --dry-run

# Show detailed execution plan
ai-shell alias run date-range-orders "2025-01-01" "2025-01-31" --explain
```

Output:
```
Execution Plan:
────────────────────────────────────────────────────────────────────────────────
Alias: date-range-orders
Description: Get orders in date range

Query Template:
SELECT * FROM orders WHERE created_at BETWEEN $1 AND $2

Parameters:
  $1 (start_date: date) = 2025-01-01
  $2 (end_date: date) = 2025-01-31

Executed Query:
SELECT * FROM orders WHERE created_at BETWEEN '2025-01-01' AND '2025-01-31'
────────────────────────────────────────────────────────────────────────────────
```

## Templates

Templates provide pre-configured alias patterns that you can customize.

### Listing Templates

```bash
# List all available templates
ai-shell alias template list
```

### Built-in Templates

The system includes these default templates:

1. **user-query** - Query user data by ID
2. **date-range** - Query records within a date range
3. **search-text** - Search records by text field

### Creating Aliases from Templates

```bash
# Create alias from template
ai-shell alias from-template user-query my-user-query

# This creates an alias named 'my-user-query' based on the 'user-query' template
```

### Creating Custom Templates

```bash
# Create a new template
ai-shell alias template create pagination-template \
  --query "SELECT * FROM records LIMIT $1 OFFSET $2" \
  --description "Paginated query template" \
  --parameters "limit:number:true,offset:number:true" \
  --tags "pagination,common"
```

### Template Use Cases

#### Analytics Template

```bash
ai-shell alias template create analytics-range \
  --query "SELECT DATE(created_at) as date, COUNT(*) as count
           FROM events
           WHERE created_at BETWEEN $1 AND $2
           GROUP BY DATE(created_at)
           ORDER BY date" \
  --parameters "start_date:date:true,end_date:date:true" \
  --tags "analytics,reporting"

# Create specific analytics alias
ai-shell alias from-template analytics-range daily-signups
```

#### Filter Template

```bash
ai-shell alias template create filtered-list \
  --query "SELECT * FROM records WHERE category = $1 AND status = $2 ORDER BY created_at DESC LIMIT $3" \
  --parameters "category:string:true,status:string:false:active,limit:number:false:50" \
  --tags "lists,filters"
```

## Import/Export

### Exporting Aliases

```bash
# Export to JSON
ai-shell alias export aliases-backup.json

# Export to YAML
ai-shell alias export aliases-backup.yaml --format yaml
```

### Importing Aliases

```bash
# Import and replace existing aliases
ai-shell alias import aliases-backup.json

# Import and merge with existing aliases
ai-shell alias import aliases-backup.json --merge
```

### Sharing Aliases with Team

```bash
# Export team aliases
ai-shell alias export team-aliases.json

# Team members can import
ai-shell alias import team-aliases.json --merge
```

### Backup Strategy

```bash
# Regular backup (add to cron or script)
ai-shell alias export ~/.ai-shell/backups/aliases-$(date +%Y%m%d).json

# Weekly backup with rotation
ai-shell alias export ~/.ai-shell/backups/aliases-weekly.json
```

## Statistics and Analytics

### View Usage Statistics

```bash
ai-shell alias stats
```

Output:
```
Alias Statistics:
────────────────────────────────────────────────────────────────────────────────
Total aliases: 25
Total usage: 342

Most Used:
  1. user-by-id (89 times)
  2. daily-report (54 times)
  3. active-users (42 times)
  4. date-range-orders (38 times)
  5. top-products (31 times)

Least Used:
  1. experimental-query (0 times)
  2. test-alias (1 times)
  3. backup-query (2 times)

Recently Created:
  1. new-analytics (2025-01-28)
  2. user-metrics (2025-01-27)
  3. performance-check (2025-01-26)
────────────────────────────────────────────────────────────────────────────────
```

### Analyzing Alias Usage

Statistics help you:

- Identify frequently used patterns
- Find unused aliases to clean up
- Discover which queries should be optimized
- Track alias adoption across team

## Advanced Features

### SQL Injection Protection

The system automatically escapes single quotes in string parameters:

```bash
ai-shell alias add name-search "SELECT * FROM users WHERE name = $1" \
  --parameters "name:string:true"

# Safe handling of quotes
ai-shell alias run name-search "O'Brien"
# Generates: SELECT * FROM users WHERE name = 'O''Brien'
```

### Complex Queries with Multiple Conditions

```bash
# Create alias with complex logic
ai-shell alias add advanced-filter \
  "SELECT u.*, COUNT(o.id) as order_count
   FROM users u
   LEFT JOIN orders o ON u.id = o.user_id
   WHERE u.status = $1
   AND u.created_at >= $2
   GROUP BY u.id
   HAVING COUNT(o.id) >= $3
   ORDER BY order_count DESC
   LIMIT $4" \
  --parameters "status:string:true,since:date:true,min_orders:number:false:1,limit:number:false:100"
```

### Organizing with Tags

```bash
# Create organized alias structure
ai-shell alias add daily-users "..." --tags "users,daily,reports"
ai-shell alias add weekly-users "..." --tags "users,weekly,reports"
ai-shell alias add monthly-users "..." --tags "users,monthly,reports"

# List by category
ai-shell alias list --tags "users"
ai-shell alias list --tags "daily"
ai-shell alias list --tags "reports"
```

### Alias Naming Conventions

Good naming practices:

```bash
# Use descriptive, hyphenated names
ai-shell alias add user-orders-by-date "..."
ai-shell alias add product-inventory-low "..."

# Prefix by domain
ai-shell alias add analytics-daily-revenue "..."
ai-shell alias add analytics-user-retention "..."

# Indicate time scope
ai-shell alias add report-weekly-summary "..."
ai-shell alias add report-monthly-metrics "..."
```

## Best Practices

### 1. Use Descriptive Names

```bash
# Good
ai-shell alias add active-premium-users "..."

# Bad
ai-shell alias add apu "..."
```

### 2. Always Add Descriptions

```bash
ai-shell alias add user-activity \
  "SELECT * FROM user_events WHERE created_at > $1" \
  --description "Get user activity events after a specific date" \
  --parameters "after_date:date:true"
```

### 3. Leverage Optional Parameters

```bash
# Make commonly used values optional with sensible defaults
ai-shell alias add recent-orders \
  "SELECT * FROM orders ORDER BY created_at DESC LIMIT $1" \
  --parameters "limit:number:false:50"
```

### 4. Use Tags for Organization

```bash
# Tag by domain, frequency, and purpose
ai-shell alias add revenue-report "..." \
  --tags "finance,reports,monthly"
```

### 5. Create Templates for Common Patterns

```bash
# Create reusable templates for your team
ai-shell alias template create audit-log \
  --query "SELECT * FROM audit_logs WHERE user_id = $1 AND action = $2 AND created_at > $3" \
  --parameters "user_id:number:true,action:string:true,after:date:true"
```

### 6. Regular Maintenance

```bash
# Review statistics quarterly
ai-shell alias stats

# Remove unused aliases
ai-shell alias list --verbose
ai-shell alias remove unused-alias

# Export backups regularly
ai-shell alias export backups/aliases-$(date +%Y%m%d).json
```

### 7. Team Collaboration

```bash
# Share common aliases with team
ai-shell alias export team/shared-aliases.json

# Document team conventions in descriptions
ai-shell alias add standard-user-query "..." \
  --description "Standard user query - follows company data access policy"
```

### 8. Test Before Deploying

```bash
# Always test with --dry-run and --explain
ai-shell alias run complex-query param1 param2 --dry-run --explain
```

### 9. Version Control

```bash
# Keep aliases in version control
git add ~/.ai-shell/aliases.json
git commit -m "Update shared aliases"
```

### 10. Security Considerations

- Never store sensitive data in alias definitions
- Use parameters instead of hardcoding values
- Review aliases before importing from external sources
- Audit alias usage regularly

## Examples by Use Case

### Database Administration

```bash
# Table size analysis
ai-shell alias add table-size \
  "SELECT table_name, pg_size_pretty(pg_total_relation_size(table_name::regclass)) as size
   FROM information_schema.tables
   WHERE table_schema = 'public'
   ORDER BY pg_total_relation_size(table_name::regclass) DESC
   LIMIT $1" \
  --parameters "limit:number:false:10"

# Index usage
ai-shell alias add index-usage \
  "SELECT * FROM pg_stat_user_indexes WHERE schemaname = $1 ORDER BY idx_scan DESC" \
  --parameters "schema:string:false:public"
```

### Analytics

```bash
# Daily active users
ai-shell alias add dau \
  "SELECT DATE(last_login) as date, COUNT(DISTINCT user_id) as active_users
   FROM user_sessions
   WHERE last_login >= $1
   GROUP BY DATE(last_login)
   ORDER BY date" \
  --parameters "since:date:true"

# Revenue by product
ai-shell alias add revenue-by-product \
  "SELECT product_id, SUM(amount) as revenue
   FROM orders
   WHERE created_at BETWEEN $1 AND $2
   GROUP BY product_id
   ORDER BY revenue DESC" \
  --parameters "start_date:date:true,end_date:date:true"
```

### Monitoring

```bash
# Slow queries
ai-shell alias add slow-queries \
  "SELECT * FROM pg_stat_statements
   WHERE mean_exec_time > $1
   ORDER BY mean_exec_time DESC
   LIMIT $2" \
  --parameters "threshold_ms:number:false:1000,limit:number:false:20"

# Error logs
ai-shell alias add recent-errors \
  "SELECT * FROM error_logs
   WHERE severity = $1
   AND created_at > NOW() - INTERVAL '$2 hours'
   ORDER BY created_at DESC" \
  --parameters "severity:string:false:ERROR,hours:number:false:24"
```

### Reporting

```bash
# Executive summary
ai-shell alias add exec-summary \
  "SELECT
     COUNT(DISTINCT user_id) as total_users,
     COUNT(*) as total_orders,
     SUM(amount) as total_revenue,
     AVG(amount) as avg_order_value
   FROM orders
   WHERE created_at BETWEEN $1 AND $2" \
  --parameters "start_date:date:true,end_date:date:true"
```

## Troubleshooting

### Parameter Count Mismatch

```bash
# Error: Invalid parameter placeholder $3
# Fix: Ensure parameter count matches placeholders in query
ai-shell alias edit my-alias --parameters "param1:string:true,param2:number:true"
```

### Type Conversion Errors

```bash
# Error: Invalid number: "abc"
# Fix: Ensure parameter types match input values
ai-shell alias run numeric-query 123  # Not "abc"
```

### Missing Required Parameters

```bash
# Error: Missing required parameter: user_id
# Fix: Provide all required parameters or make them optional with defaults
ai-shell alias edit my-alias --parameters "user_id:number:false:0"
```

## Configuration

Aliases are stored in:
```
~/.ai-shell/aliases.json
~/.ai-shell/alias-templates.json
```

These files are automatically created and managed by the system.

## Conclusion

The AI Shell Alias System provides a powerful and flexible way to manage your frequently used queries. By leveraging parameterized queries, templates, and organizational features, you can create a library of reusable, type-safe query shortcuts that improve productivity and maintain consistency across your team.

For more information, visit the [AI Shell Documentation](https://github.com/your-repo/aishell).
