# Query Optimization CLI Commands

**Phase 2 Sprint 1 - Query Optimization Command Suite**

This document provides comprehensive documentation for the Query Optimization CLI commands implemented in Phase 2.

## Table of Contents

1. [Overview](#overview)
2. [Commands](#commands)
3. [Usage Examples](#usage-examples)
4. [Output Formats](#output-formats)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The Query Optimization CLI provides a suite of commands for analyzing, optimizing, and managing SQL queries. These commands leverage AI-powered analysis to provide intelligent recommendations and automate optimization tasks.

### Features

- **AI-Powered Optimization**: Uses Claude AI to analyze and optimize SQL queries
- **Slow Query Analysis**: Identifies and analyzes performance bottlenecks
- **Index Management**: Recommends and manages database indexes
- **Risk Assessment**: Analyzes queries for dangerous operations
- **Multiple Output Formats**: Supports text, JSON, table, and CSV formats

### Prerequisites

- Node.js 16+
- PostgreSQL, MySQL, or compatible database
- ANTHROPIC_API_KEY environment variable (for AI features)
- Active database connection

---

## Commands

### 1. `ai-shell optimize`

Optimize a SQL query using AI analysis.

#### Syntax

```bash
ai-shell optimize <query> [options]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--apply` | Apply optimization immediately | `false` |
| `--explain` | Show query execution plan | `false` |
| `--dry-run` | Validate without executing | `false` |
| `--format <type>` | Output format (text, json, table, csv) | `text` |
| `--output <file>` | Write output to file | - |
| `--compare` | Compare before/after performance | `false` |
| `-v, --verbose` | Enable verbose logging | `false` |

#### Examples

```bash
# Basic optimization
ai-shell optimize "SELECT * FROM users WHERE id > 100"

# With execution plan
ai-shell optimize "SELECT * FROM users" --explain

# Safe dry-run mode
ai-shell optimize "DELETE FROM users WHERE active = false" --dry-run

# Apply optimization and compare performance
ai-shell optimize "SELECT * FROM orders" --apply --compare

# Output to JSON file
ai-shell optimize "SELECT * FROM products" --format json --output result.json
```

#### Output Example

```
📊 Query Optimization Results

Original Query:
  SELECT * FROM users WHERE id > 100

Optimized Query:
  SELECT id, name, email FROM users WHERE id > 100

Estimated Improvement: 40% faster

⚠️  Issues Found:

  1. Using SELECT * returns unnecessary columns
  2. Missing index on id column may slow down lookups

💡 Suggestions:

  1. Specify required columns explicitly
  2. Add index on id column for faster filtering
  3. Consider using LIMIT for large result sets

📈 Index Recommendations:

  1. CREATE INDEX idx_users_id ON users(id)
```

---

### 2. `ai-shell slow-queries`

Analyze slow queries from database logs.

#### Syntax

```bash
ai-shell slow-queries [options]
```

#### Aliases

- `slow`

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --threshold <ms>` | Minimum execution time in ms | `1000` |
| `--last <period>` | Time period (1h, 24h, 7d) | `24h` |
| `-l, --limit <count>` | Maximum queries to show | `20` |
| `--auto-fix` | Automatically optimize queries | `false` |
| `--format <type>` | Output format (text, json, table, csv) | `table` |
| `--output <file>` | Write output to file | - |
| `-v, --verbose` | Enable verbose logging | `false` |

#### Examples

```bash
# List slow queries with default threshold
ai-shell slow-queries

# Show queries slower than 500ms
ai-shell slow --threshold 500

# Last 7 days, limit to 10
ai-shell slow-queries --last 7d --limit 10

# Auto-fix slow queries
ai-shell slow-queries --auto-fix

# Export to JSON
ai-shell slow-queries --format json --output slow-queries.json
```

#### Output Example

```
🔍 Analyzing Slow Queries

  Threshold: 1000ms
  Period: 24h
  Limit: 20

┌───┬──────────────────────────────────────────────┬────────────┬───────────┬───────┬──────────────────────────────────────┐
│ # │ Query                                        │ Avg Time   │ Max Time  │ Calls │ Recommendation                        │
├───┼──────────────────────────────────────────────┼────────────┼───────────┼───────┼──────────────────────────────────────┤
│ 1 │ SELECT * FROM users WHERE email LIKE...     │ 2500ms     │ 5000ms    │ 150   │ Add index on email column             │
│ 2 │ SELECT u.*, COUNT(o.id) FROM users u...     │ 1800ms     │ 3500ms    │ 89    │ Consider materialized view            │
│ 3 │ SELECT * FROM orders WHERE created_at...    │ 1500ms     │ 2800ms    │ 234   │ Add composite index                   │
└───┴──────────────────────────────────────────────┴────────────┴───────────┴───────┴──────────────────────────────────────┘

📊 Summary:
  Total slow queries: 3
  Total execution time: 5800.00ms
  Total calls: 473
  Average time: 1933.33ms

💡 Recommendations:
  1. Consider adding indexes for frequently queried columns
  2. Review and optimize queries with high execution times
  3. Use --auto-fix to automatically optimize queries
  4. Run: ai-shell optimize "<query>" for detailed analysis
```

---

### 3. `ai-shell indexes`

Index management and recommendations.

#### Subcommands

##### 3.1. `recommend`

Get index recommendations for a table.

```bash
ai-shell indexes recommend --table <table> [options]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--table <table>` | Table name (required) | - |
| `--format <type>` | Output format (text, json, table) | `table` |
| `--output <file>` | Write output to file | - |
| `-v, --verbose` | Enable verbose logging | `false` |

**Example:**

```bash
ai-shell indexes recommend --table users
```

##### 3.2. `apply`

Apply recommended index.

```bash
ai-shell indexes apply --table <table> --index <index> [options]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--table <table>` | Table name (required) | - |
| `--index <index>` | Index name (required) | - |
| `--online` | Create index online (non-blocking) | `true` |
| `--dry-run` | Show SQL without executing | `false` |
| `-v, --verbose` | Enable verbose logging | `false` |

**Example:**

```bash
ai-shell indexes apply --table users --index idx_users_email --online
```

##### 3.3. `list`

List all indexes for a table.

```bash
ai-shell indexes list --table <table> [options]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--table <table>` | Table name (required) | - |
| `--show-unused` | Highlight unused indexes | `false` |
| `--format <type>` | Output format (text, json, table) | `table` |
| `-v, --verbose` | Enable verbose logging | `false` |

**Example:**

```bash
ai-shell indexes list --table users --show-unused
```

#### Output Example

```
📊 Index Recommendations for table: users

┌───┬─────────────────────┬──────────────────┬────────┬─────────────────────────────────────┬──────────────────────────┐
│ # │ Index Name          │ Columns          │ Type   │ Reason                              │ Impact                   │
├───┼─────────────────────┼──────────────────┼────────┼─────────────────────────────────────┼──────────────────────────┤
│ 1 │ idx_users_email     │ email            │ btree  │ Frequently used in WHERE and JOINs  │ 70% faster lookups       │
│ 2 │ idx_users_created   │ created_at, id   │ btree  │ Optimizes time-range queries        │ 50% faster range queries │
└───┴─────────────────────┴──────────────────┴────────┴─────────────────────────────────────┴──────────────────────────┘

📝 SQL Statements:

-- Recommendation 1
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- Recommendation 2
CREATE INDEX CONCURRENTLY idx_users_created ON users(created_at DESC, id);

💡 Next Steps:
  1. Review recommendations above
  2. Test in development environment first
  3. Apply indexes using: ai-shell indexes apply --table <table> --index <index>
  4. Monitor performance after applying
```

---

### 4. `ai-shell risk-check`

Analyze query risk level and detect dangerous operations.

#### Syntax

```bash
ai-shell risk-check <query> [options]
```

#### Aliases

- `risk`

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--format <type>` | Output format (text, json) | `text` |
| `--auto-approve` | Skip confirmation for low-risk | `false` |
| `-v, --verbose` | Enable verbose logging | `false` |

#### Risk Levels

- **LOW**: Read-only queries, no side effects
- **MEDIUM**: Updates with WHERE clause, minor changes
- **HIGH**: Bulk updates/deletes, schema changes
- **CRITICAL**: DROP, TRUNCATE, bulk DELETE without WHERE

#### Examples

```bash
# Check SELECT query (low risk)
ai-shell risk-check "SELECT * FROM users"

# Check DELETE query (high risk)
ai-shell risk "DELETE FROM orders WHERE status = 'cancelled'"

# Check DROP query (critical risk)
ai-shell risk-check "DROP TABLE temp_data"

# JSON output
ai-shell risk-check "UPDATE users SET password = 'default'" --format json
```

#### Output Example

```
🔒 Query Risk Analysis

Risk Level: CRITICAL
Affected Tables: users
Estimated Affected Rows: 50,000
Can Rollback: No

⚠️  Identified Risks:

1. BULK_DELETE
   Severity: CRITICAL
   TRUNCATE will delete all rows and cannot be rolled back in some databases
   Mitigation: Use DELETE with WHERE clause if you need rollback capability.

⚠️  Warnings:

  • No WHERE clause detected - will affect ALL rows

💡 Recommendations:

  • Run in transaction for easy rollback: BEGIN; ... ROLLBACK;
  • Test in development environment first
  • Create backup before executing

Query:
TRUNCATE TABLE users

⚠️  This query requires explicit confirmation

Type "CONFIRM" to proceed, or anything else to cancel:
```

---

## Usage Examples

### Complete Workflow Example

```bash
# 1. Identify slow queries
ai-shell slow-queries --threshold 1000 --last 24h

# 2. Analyze specific query
ai-shell optimize "SELECT * FROM users WHERE email LIKE '%@example.com%'" --explain

# 3. Check risk before applying
ai-shell risk-check "UPDATE users SET email_verified = true WHERE email LIKE '%@example.com%'"

# 4. Get index recommendations
ai-shell indexes recommend --table users

# 5. Apply recommended index
ai-shell indexes apply --table users --index idx_users_email --online --dry-run

# 6. Verify index was created
ai-shell indexes list --table users
```

### Batch Optimization

```bash
# Auto-fix top 3 slow queries
ai-shell slow-queries --auto-fix --limit 3

# Optimize multiple queries with JSON output
for query in "SELECT * FROM users" "SELECT * FROM orders"; do
  ai-shell optimize "$query" --format json --output "optimization-$(date +%s).json"
done
```

---

## Output Formats

### Text Format (Default)

Human-readable format with colors and formatting.

```bash
ai-shell optimize "SELECT * FROM users" --format text
```

### JSON Format

Machine-readable format for programmatic use.

```bash
ai-shell optimize "SELECT * FROM users" --format json
```

```json
{
  "originalQuery": "SELECT * FROM users",
  "optimizedQuery": "SELECT id, name, email FROM users",
  "issues": ["Using SELECT * returns unnecessary columns"],
  "suggestions": ["Specify required columns explicitly"],
  "indexRecommendations": ["CREATE INDEX idx_users_id ON users(id)"],
  "estimatedImprovement": "40% faster"
}
```

### Table Format

Tabular format with clear structure.

```bash
ai-shell slow-queries --format table
```

### CSV Format

Comma-separated values for spreadsheet import.

```bash
ai-shell slow-queries --format csv --output slow-queries.csv
```

---

## Best Practices

### 1. Safety First

- Always use `--dry-run` for destructive operations
- Run `risk-check` before executing dangerous queries
- Test optimizations in development environment first
- Create backups before applying schema changes

### 2. Performance Analysis

- Start with `slow-queries` to identify bottlenecks
- Use `--threshold` to focus on worst performers
- Enable `--explain` to understand execution plans
- Use `--compare` to validate improvements

### 3. Index Management

- Review recommendations before applying
- Use `--online` to avoid blocking production traffic
- Monitor performance after index creation
- Periodically check for unused indexes

### 4. Automation

- Use `--auto-fix` for routine optimizations
- Export results to JSON for integration with other tools
- Schedule regular slow query analysis
- Set up alerts for critical risk queries

---

## Troubleshooting

### API Key Not Set

**Error:** `ANTHROPIC_API_KEY environment variable not set`

**Solution:**
```bash
export ANTHROPIC_API_KEY=your-api-key
```

### No Active Connection

**Error:** `No active database connection`

**Solution:**
```bash
ai-shell connect postgresql://user:pass@localhost:5432/dbname
```

### Permission Denied

**Error:** `Permission denied for index creation`

**Solution:**
Ensure your database user has CREATE INDEX permissions:
```sql
GRANT CREATE ON DATABASE mydb TO myuser;
```

### Timeout Errors

**Error:** `Query execution timeout`

**Solution:**
Increase timeout value:
```bash
ai-shell optimize "SELECT * FROM large_table" --timeout 60000
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude AI API key | Yes (for AI features) |
| `DATABASE_URL` | Default database connection | No |
| `LOG_LEVEL` | Logging level (debug, info, warn, error) | No |

---

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error or high risk |
| 2 | Critical risk detected |

---

## Related Commands

- `ai-shell connections` - Manage database connections
- `ai-shell explain` - Explain SQL query
- `ai-shell health-check` - Check database health
- `ai-shell monitor` - Start real-time monitoring

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/ai-shell/issues
- Documentation: https://github.com/yourusername/ai-shell/docs
- Examples: `/examples/optimization/`

---

**Version:** 2.0.0
**Last Updated:** 2025-10-28
**Status:** Production Ready
