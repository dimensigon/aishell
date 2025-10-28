# Template System - AI-Shell P3 Feature

**Status**: Priority 3 (P3) Feature
**Version**: 2.0.0
**Last Updated**: 2025-10-28

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Installation & Setup](#installation--setup)
- [Quick Start](#quick-start)
- [Template Types](#template-types)
- [Command Reference](#command-reference)
- [Template Language](#template-language)
- [Advanced Features](#advanced-features)
- [Use Cases & Examples](#use-cases--examples)
- [Template Library](#template-library)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

---

## Overview

The AI-Shell Template System provides a powerful framework for creating reusable, parameterized database operations, queries, and workflows. It enables teams to:

- **Standardize Operations**: Create consistent, tested query patterns
- **Reduce Errors**: Pre-validated templates prevent common mistakes
- **Boost Productivity**: 10x faster than writing queries from scratch
- **Share Knowledge**: Distribute best practices across teams
- **Version Control**: Track template changes over time
- **Multi-Database**: Same template works across different databases

### Key Benefits

✅ **Reusability**: Write once, use everywhere
✅ **Parameters**: Dynamic values with validation
✅ **Inheritance**: Extend existing templates
✅ **Composability**: Combine multiple templates
✅ **Security**: Built-in SQL injection prevention
✅ **Testing**: Test templates before deployment

---

## Core Concepts

### What is a Template?

A template is a reusable query or workflow pattern with placeholders for dynamic values.

```sql
-- Simple template
SELECT {{ columns }}
FROM {{ table }}
WHERE {{ condition }}
LIMIT {{ limit | default: 100 }};
```

### Template Anatomy

```yaml
# Template metadata
name: user-report
version: 1.0.0
description: Generate user activity report
author: team@company.com

# Parameters with validation
parameters:
  date_from:
    type: date
    required: true
    description: Start date
  date_to:
    type: date
    required: false
    default: "{{ now }}"
  status:
    type: enum
    values: [active, inactive, suspended]
    default: active

# The template body
query: |
  SELECT
    u.id,
    u.name,
    u.email,
    COUNT(o.id) as order_count
  FROM users u
  LEFT JOIN orders o ON u.id = o.user_id
  WHERE u.status = {{ status | quote }}
    AND o.created_at BETWEEN {{ date_from | quote }} AND {{ date_to | quote }}
  GROUP BY u.id, u.name, u.email
  ORDER BY order_count DESC;

# Post-processing
output:
  format: table
  save_to: reports/user-activity-{{ date_from }}.csv
```

---

## Installation & Setup

### Install Template Engine

```bash
# Install template system
npm install -g @aishell/templates

# Enable templates feature
aishell config set features.templates true

# Configure template directory
aishell config set templates.directory ~/.aishell/templates

# Enable auto-sync (sync with team repository)
aishell config set templates.autoSync true
aishell config set templates.repository https://github.com/your-org/aishell-templates
```

### Initialize Template Repository

```bash
# Create local template directory
aishell templates init

# Output:
# ✓ Created ~/.aishell/templates
# ✓ Initialized template registry
# ✓ Created default templates
# ✓ Template system ready

# Verify installation
aishell templates version
# Template System v2.0.0
```

### Import Default Templates

```bash
# Import standard template library
aishell templates import --source official

# Import community templates
aishell templates import --source community

# Import custom repository
aishell templates import --source https://github.com/your-org/templates
```

---

## Quick Start

### Example 1: Create Your First Template

```bash
# Create new template interactively
aishell templates create

# Interactive prompts:
Template name: daily-sales
Description: Calculate daily sales totals
Category: reports

# Add parameters
Add parameter? (y/n): y
Parameter name: date
Parameter type: (date/string/number/boolean): date
Required: yes
Default value: {{ today }}

Add another parameter? (y/n): y
Parameter name: region
Parameter type: string
Required: no
Default value: all

Add another parameter? (y/n): n

# Enter template query (press Ctrl+D when done):
SELECT
  DATE(created_at) as sale_date,
  {{ 'region' if region != 'all' else 'SUM(total)' }} as region,
  SUM(total) as total_sales,
  COUNT(*) as order_count
FROM orders
WHERE DATE(created_at) = {{ date | quote }}
  {% if region != 'all' %}
  AND region = {{ region | quote }}
  {% endif %}
GROUP BY DATE(created_at){{ ', region' if region != 'all' else '' }}
ORDER BY total_sales DESC;

# Template created: daily-sales
# Location: ~/.aishell/templates/daily-sales.yaml
```

### Example 2: Use Existing Template

```bash
# List available templates
aishell templates list

# Output:
# ┌─ Available Templates ────────────────────────────────┐
# │ Name              Category    Version  Description    │
# ├───────────────────────────────────────────────────────┤
# │ daily-sales       reports     1.0.0    Daily sales    │
# │ user-activity     analytics   1.2.0    User stats     │
# │ inventory-check   operations  1.0.0    Stock levels   │
# │ slow-queries      monitoring  1.1.0    Find slow SQL  │
# └───────────────────────────────────────────────────────┘

# Use template
aishell templates run daily-sales --param date="2025-10-28"

# Output:
# ┌─ Daily Sales Report (2025-10-28) ────────────────────┐
# │ Region      Total Sales    Orders                     │
# ├───────────────────────────────────────────────────────┤
# │ North       $15,420.50     87                         │
# │ South       $12,890.25     65                         │
# │ East        $18,905.75     102                        │
# │ West        $9,234.50      43                         │
# ├───────────────────────────────────────────────────────┤
# │ Total       $56,451.00     297                        │
# └───────────────────────────────────────────────────────┘
```

### Example 3: Template with Multiple Formats

```bash
# Run template with JSON output
aishell templates run daily-sales \
  --param date="2025-10-28" \
  --format json \
  --output report.json

# Run template with CSV output
aishell templates run daily-sales \
  --param date="2025-10-28" \
  --format csv \
  --output report.csv

# Run template and pipe to another command
aishell templates run daily-sales \
  --param date="2025-10-28" \
  --format json | jq '.[] | select(.total_sales > 10000)'
```

---

## Template Types

### 1. Query Templates

Simple SELECT queries with parameters.

```yaml
name: find-users
parameters:
  search:
    type: string
    required: true
  limit:
    type: number
    default: 50

query: |
  SELECT id, name, email, status
  FROM users
  WHERE name ILIKE {{ '%' + search + '%' | quote }}
     OR email ILIKE {{ '%' + search + '%' | quote }}
  ORDER BY created_at DESC
  LIMIT {{ limit }};
```

### 2. CRUD Templates

Create, Read, Update, Delete operations.

```yaml
name: create-user
type: insert
parameters:
  name:
    type: string
    required: true
    validate: "^[A-Za-z ]{2,50}$"
  email:
    type: string
    required: true
    validate: "^[\\w.-]+@[\\w.-]+\\.\\w+$"
  role:
    type: enum
    values: [admin, user, guest]
    default: user

query: |
  INSERT INTO users (name, email, role, created_at)
  VALUES (
    {{ name | quote }},
    {{ email | quote }},
    {{ role | quote }},
    NOW()
  )
  RETURNING id, name, email, role;
```

### 3. Report Templates

Complex analytical queries.

```yaml
name: monthly-revenue-report
parameters:
  year:
    type: number
    default: "{{ current_year }}"
  month:
    type: number
    validate: "^([1-9]|1[0-2])$"
    default: "{{ current_month }}"

query: |
  WITH daily_revenue AS (
    SELECT
      DATE(created_at) as day,
      SUM(total) as revenue,
      COUNT(*) as orders
    FROM orders
    WHERE YEAR(created_at) = {{ year }}
      AND MONTH(created_at) = {{ month }}
    GROUP BY DATE(created_at)
  )
  SELECT
    day,
    revenue,
    orders,
    revenue / orders as avg_order_value,
    SUM(revenue) OVER (ORDER BY day) as cumulative_revenue
  FROM daily_revenue
  ORDER BY day;

output:
  format: table
  charts:
    - type: line
      x: day
      y: revenue
      title: "Daily Revenue - {{ month }}/{{ year }}"
```

### 4. Migration Templates

Database schema changes.

```yaml
name: add-user-preferences
type: migration
version: 20251028_001

up: |
  CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, key)
  );

  CREATE INDEX idx_user_prefs_user_id ON user_preferences(user_id);
  CREATE INDEX idx_user_prefs_key ON user_preferences(key);

down: |
  DROP TABLE IF EXISTS user_preferences CASCADE;

validation:
  pre_check:
    - "SELECT 1 FROM information_schema.tables WHERE table_name = 'users'"
  post_check:
    - "SELECT 1 FROM information_schema.tables WHERE table_name = 'user_preferences'"
```

### 5. Workflow Templates

Multi-step operations.

```yaml
name: user-onboarding
type: workflow
parameters:
  email:
    type: string
    required: true
  name:
    type: string
    required: true
  send_welcome_email:
    type: boolean
    default: true

steps:
  - name: create-user
    query: |
      INSERT INTO users (name, email, status, created_at)
      VALUES ({{ name | quote }}, {{ email | quote }}, 'pending', NOW())
      RETURNING id;
    capture: user_id

  - name: create-default-preferences
    query: |
      INSERT INTO user_preferences (user_id, key, value)
      VALUES
        ({{ user_id }}, 'theme', 'light'),
        ({{ user_id }}, 'notifications', 'true'),
        ({{ user_id }}, 'language', 'en');

  - name: send-welcome-email
    condition: "{{ send_welcome_email }}"
    action: email
    to: "{{ email }}"
    template: welcome-email
    data:
      name: "{{ name }}"
      user_id: "{{ user_id }}"

  - name: update-user-status
    query: |
      UPDATE users
      SET status = 'active'
      WHERE id = {{ user_id }};

output:
  message: "User {{ name }} (ID: {{ user_id }}) created successfully"
```

---

## Command Reference

### Template Management

#### `aishell templates create`
Create new template interactively or from file.

```bash
aishell templates create [name] [options]

Options:
  -f, --file <path>          Create from YAML file
  -t, --type <type>          Template type (query|crud|report|migration|workflow)
  -c, --category <cat>       Category name
  --from-query <sql>         Create from raw SQL query
  --interactive              Use interactive wizard (default)

Examples:
  aishell templates create my-report --interactive
  aishell templates create --file template.yaml
  aishell templates create quick-select --from-query "SELECT * FROM users"
```

---

#### `aishell templates list`
List all available templates.

```bash
aishell templates list [options]

Options:
  -c, --category <cat>       Filter by category
  -t, --type <type>          Filter by type
  -s, --search <term>        Search by name or description
  --tags <tags>              Filter by tags
  -v, --verbose              Show detailed information
  --format <fmt>             Output format (table|json|yaml)

Examples:
  aishell templates list
  aishell templates list --category reports
  aishell templates list --search "user"
  aishell templates list --type crud --format json
```

---

#### `aishell templates show`
Display template details.

```bash
aishell templates show <name> [options]

Options:
  -v, --version <ver>        Show specific version
  --source                   Show raw template source
  --example                  Show usage example

Examples:
  aishell templates show daily-sales
  aishell templates show daily-sales --version 1.0.0
  aishell templates show user-report --source
  aishell templates show create-user --example
```

---

#### `aishell templates run`
Execute template with parameters.

```bash
aishell templates run <name> [options]

Options:
  -p, --param <key=value>    Set parameter value
  -f, --format <fmt>         Output format (table|json|csv|yaml)
  -o, --output <file>        Save results to file
  -d, --database <name>      Target database
  --dry-run                  Show generated query without executing
  --explain                  Show query execution plan
  -v, --verbose              Show detailed execution info

Examples:
  aishell templates run daily-sales --param date="2025-10-28"
  aishell templates run user-report -p date_from="2025-10-01" -p date_to="2025-10-31"
  aishell templates run inventory-check --format csv --output stock.csv
  aishell templates run complex-query --dry-run --explain
```

---

#### `aishell templates edit`
Edit existing template.

```bash
aishell templates edit <name> [options]

Options:
  -e, --editor <cmd>         Editor command (default: $EDITOR)
  --create-version           Create new version instead of modifying
  --no-validation            Skip validation after edit

Examples:
  aishell templates edit daily-sales
  aishell templates edit user-report --editor vim
  aishell templates edit critical-query --create-version
```

---

#### `aishell templates delete`
Remove template.

```bash
aishell templates delete <name> [options]

Options:
  -v, --version <ver>        Delete specific version
  --all-versions             Delete all versions
  -f, --force                Skip confirmation
  --backup                   Create backup before deletion

Examples:
  aishell templates delete old-report --force
  aishell templates delete user-query --version 1.0.0
  aishell templates delete deprecated-template --backup
```

---

### Template Validation

#### `aishell templates validate`
Validate template syntax and parameters.

```bash
aishell templates validate <name> [options]

Options:
  -f, --file <path>          Validate file before importing
  --strict                   Enable strict validation
  -p, --param <key=value>    Test with specific parameters

Examples:
  aishell templates validate daily-sales
  aishell templates validate --file new-template.yaml
  aishell templates validate user-report --param date="2025-10-28" --strict
```

---

#### `aishell templates test`
Test template execution.

```bash
aishell templates test <name> [options]

Options:
  -p, --param <key=value>    Test parameter
  --all-combinations         Test all parameter combinations
  --sample-data              Use sample/mock data
  --performance              Measure execution time

Examples:
  aishell templates test daily-sales -p date="2025-10-28"
  aishell templates test user-report --all-combinations
  aishell templates test slow-query --performance
```

---

### Template Sharing

#### `aishell templates export`
Export template to file.

```bash
aishell templates export <name> [output] [options]

Options:
  -v, --version <ver>        Export specific version
  --with-data                Include sample data
  --format <fmt>             Format (yaml|json)

Examples:
  aishell templates export daily-sales report.yaml
  aishell templates export user-report --format json --with-data
  aishell templates export all-reports templates-bundle.zip
```

---

#### `aishell templates import`
Import template from file or repository.

```bash
aishell templates import [source] [options]

Options:
  -f, --file <path>          Import from file
  -u, --url <url>            Import from URL
  -r, --repository <url>     Import from git repository
  --overwrite                Overwrite existing templates
  --validate                 Validate before import

Examples:
  aishell templates import --file template.yaml
  aishell templates import --url https://example.com/template.yaml
  aishell templates import --repository https://github.com/org/templates
  aishell templates import --source official
```

---

#### `aishell templates publish`
Publish template to shared repository.

```bash
aishell templates publish <name> [options]

Options:
  -r, --repository <url>     Target repository
  -m, --message <msg>        Publish message
  --tag <tag>                Add tags
  --private                  Mark as private

Examples:
  aishell templates publish daily-sales --message "Initial version"
  aishell templates publish user-report --tag "analytics,users"
  aishell templates publish internal-audit --private
```

---

### Template Versioning

#### `aishell templates versions`
Manage template versions.

```bash
aishell templates versions <name> [command] [options]

Commands:
  list                       List all versions
  show <version>             Show specific version
  diff <v1> <v2>             Compare two versions
  rollback <version>         Rollback to version

Examples:
  aishell templates versions daily-sales list
  aishell templates versions user-report show 1.0.0
  aishell templates versions daily-sales diff 1.0.0 1.1.0
  aishell templates versions critical-query rollback 1.0.0
```

---

## Template Language

### Variable Syntax

```yaml
# Simple variable
{{ variable_name }}

# Variable with default
{{ variable_name | default: "default_value" }}

# Variable with filter
{{ variable_name | upper }}
{{ price | currency }}
{{ date | format: "%Y-%m-%d" }}
```

### Filters

```yaml
# String filters
{{ name | upper }}                    # JOHN DOE
{{ email | lower }}                   # john@example.com
{{ text | trim }}                     # Remove whitespace
{{ text | truncate: 50 }}             # Limit length

# Quoting and escaping
{{ value | quote }}                   # 'value' (SQL safe)
{{ value | double_quote }}            # "value"
{{ value | escape }}                  # SQL injection safe

# Numeric filters
{{ price | round: 2 }}                # 10.50
{{ amount | currency }}               # $10.50
{{ number | format: "0,0.00" }}       # 1,234.56

# Date filters
{{ date | format: "%Y-%m-%d" }}       # 2025-10-28
{{ date | relative }}                 # "2 days ago"
{{ timestamp | unix }}                # 1698451200

# Array filters
{{ items | join: ", " }}              # "a, b, c"
{{ items | first }}                   # First item
{{ items | last }}                    # Last item
{{ items | length }}                  # Count
{{ items | unique }}                  # Remove duplicates

# Logic filters
{{ value | default: "N/A" }}          # Fallback value
{{ value | or: other_value }}         # First non-empty
```

### Conditional Statements

```yaml
# If statement
{% if condition %}
  SQL when true
{% endif %}

# If-else
{% if status == 'active' %}
  WHERE status = 'active'
{% else %}
  WHERE status != 'active'
{% endif %}

# Elsif
{% if role == 'admin' %}
  SELECT * FROM admin_view
{% elsif role == 'user' %}
  SELECT * FROM user_view
{% else %}
  SELECT * FROM public_view
{% endif %}

# Complex conditions
{% if (age >= 18) and (country == 'US' or country == 'UK') %}
  WHERE eligible = true
{% endif %}
```

### Loops

```yaml
# Simple loop
{% for item in items %}
  {{ item }}{% if not loop.last %},{% endif %}
{% endfor %}

# Loop with index
{% for column in columns %}
  {{ column }}{% if not loop.last %},{% endif %}
{% endfor %}

# Loop variables
loop.index        # Current iteration (1-indexed)
loop.index0       # Current iteration (0-indexed)
loop.first        # True if first iteration
loop.last         # True if last iteration
loop.length       # Total iterations
```

### Functions

```yaml
# Built-in functions
{{ now() }}                           # Current timestamp
{{ today() }}                         # Current date
{{ uuid() }}                          # Generate UUID
{{ random(1, 100) }}                  # Random number
{{ hash('md5', value) }}              # Hash value

# Date functions
{{ date_add(date, 7, 'days') }}       # Add 7 days
{{ date_sub(date, 1, 'month') }}      # Subtract 1 month
{{ date_diff(date1, date2, 'days') }} # Difference in days

# String functions
{{ concat(str1, str2) }}              # Concatenate
{{ replace(text, 'old', 'new') }}     # Replace text
{{ split(text, ',') }}                # Split to array

# Math functions
{{ abs(number) }}                     # Absolute value
{{ ceil(number) }}                    # Round up
{{ floor(number) }}                   # Round down
{{ round(number, decimals) }}         # Round to decimals
```

---

## Advanced Features

### 1. Template Inheritance

```yaml
# base-report.yaml
name: base-report
abstract: true  # Cannot be executed directly

parameters:
  date:
    type: date
    required: true

query: |
  SELECT {{ columns }}
  FROM {{ table }}
  WHERE DATE(created_at) = {{ date | quote }}
  {{ extra_conditions }}
  ORDER BY {{ order_by | default: "id DESC" }};
```

```yaml
# sales-report.yaml (extends base-report)
name: sales-report
extends: base-report

parameters:
  columns:
    type: string
    default: "id, total, customer_id"
  table:
    type: string
    default: "orders"
  min_amount:
    type: number
    default: 0

extra_conditions: |
  {% if min_amount > 0 %}
  AND total >= {{ min_amount }}
  {% endif %}
```

---

### 2. Template Composition

```yaml
# Combined template using multiple sub-templates
name: comprehensive-report
type: composite

templates:
  - name: user-stats
    as: users
  - name: order-stats
    as: orders
  - name: revenue-stats
    as: revenue

query: |
  -- User Statistics
  {% template users with date=date %}

  -- Order Statistics
  {% template orders with date=date %}

  -- Revenue Statistics
  {% template revenue with date=date, groupby='region' %}
```

---

### 3. Dynamic Schema

```yaml
name: flexible-query
parameters:
  table:
    type: string
    required: true
  columns:
    type: array
    default: []  # Empty means all columns
  filters:
    type: object
    default: {}

query: |
  SELECT
    {% if columns | length > 0 %}
      {{ columns | join: ', ' }}
    {% else %}
      *
    {% endif %}
  FROM {{ table }}
  {% if filters | length > 0 %}
  WHERE
    {% for key, value in filters %}
      {{ key }} = {{ value | quote }}
      {% if not loop.last %}AND{% endif %}
    {% endfor %}
  {% endif %};

# Usage:
# aishell templates run flexible-query \
#   --param table=users \
#   --param 'columns=["id","name","email"]' \
#   --param 'filters={"status":"active","role":"admin"}'
```

---

### 4. Macros

```yaml
name: report-with-macros
macros:
  date_filter:
    parameters: [column, start, end]
    body: |
      {{ column }} BETWEEN {{ start | quote }} AND {{ end | quote }}

  pagination:
    parameters: [page, per_page]
    body: |
      LIMIT {{ per_page }} OFFSET {{ (page - 1) * per_page }}

query: |
  SELECT * FROM orders
  WHERE {% macro date_filter with 'created_at', date_from, date_to %}
  ORDER BY created_at DESC
  {% macro pagination with page, per_page %};
```

---

### 5. Pre/Post Hooks

```yaml
name: user-deletion-safe
parameters:
  user_id:
    type: number
    required: true

hooks:
  before:
    - name: backup-user
      query: |
        INSERT INTO users_backup
        SELECT * FROM users WHERE id = {{ user_id }};
    - name: check-dependencies
      query: |
        SELECT
          (SELECT COUNT(*) FROM orders WHERE user_id = {{ user_id }}) as order_count,
          (SELECT COUNT(*) FROM subscriptions WHERE user_id = {{ user_id }}) as sub_count;
      validate: |
        if result.order_count > 0 or result.sub_count > 0:
          raise Error("Cannot delete user with active orders or subscriptions")

query: |
  DELETE FROM users WHERE id = {{ user_id }};

hooks:
  after:
    - name: log-deletion
      query: |
        INSERT INTO audit_log (action, entity, entity_id, timestamp)
        VALUES ('DELETE', 'user', {{ user_id }}, NOW());
    - name: notify
      action: webhook
      url: "{{ config.webhook_url }}"
      data:
        event: user_deleted
        user_id: "{{ user_id }}"
```

---

## Use Cases & Examples

### Use Case 1: Monthly Report Automation

```yaml
name: monthly-revenue-report
description: Automated monthly revenue report with email delivery
category: reporting

parameters:
  month:
    type: number
    validate: "^([1-9]|1[0-2])$"
    default: "{{ current_month }}"
  year:
    type: number
    default: "{{ current_year }}"
  email_to:
    type: string
    default: "finance@company.com"

query: |
  WITH daily_stats AS (
    SELECT
      DATE(created_at) as day,
      COUNT(*) as orders,
      SUM(total) as revenue,
      AVG(total) as avg_order_value
    FROM orders
    WHERE YEAR(created_at) = {{ year }}
      AND MONTH(created_at) = {{ month }}
    GROUP BY DATE(created_at)
  )
  SELECT
    day,
    orders,
    revenue,
    avg_order_value,
    SUM(revenue) OVER (ORDER BY day) as cumulative_revenue,
    (revenue - LAG(revenue) OVER (ORDER BY day)) / LAG(revenue) OVER (ORDER BY day) * 100 as growth_rate
  FROM daily_stats
  ORDER BY day;

output:
  format: table
  save_to: "reports/revenue-{{ year }}-{{ month | format: '02d' }}.csv"
  email:
    to: "{{ email_to }}"
    subject: "Monthly Revenue Report - {{ year }}-{{ month }}"
    body: |
      Please find attached the revenue report for {{ year }}-{{ month }}.

      Total Revenue: {{ results | sum: 'revenue' | currency }}
      Total Orders: {{ results | sum: 'orders' }}
      Average Order Value: {{ results | avg: 'avg_order_value' | currency }}
      Growth Rate: {{ results | last | get: 'growth_rate' | round: 2 }}%

# Schedule this template
schedule:
  cron: "0 9 1 * *"  # 9 AM on 1st of each month
  timezone: "America/New_York"
```

**Usage:**
```bash
# Run for specific month
aishell templates run monthly-revenue-report \
  --param month=10 \
  --param year=2025

# Schedule for automatic execution
aishell templates schedule monthly-revenue-report --enable
```

---

### Use Case 2: Data Migration

```yaml
name: migrate-orders-to-new-schema
description: Migrate orders from old schema to new partitioned schema
type: workflow
version: 2.0.0

parameters:
  batch_size:
    type: number
    default: 1000
  date_from:
    type: date
    required: true
  date_to:
    type: date
    required: true

steps:
  - name: validate-target-schema
    query: |
      SELECT COUNT(*) as table_count
      FROM information_schema.tables
      WHERE table_schema = 'public'
        AND table_name LIKE 'orders_p_%';
    validate: "result.table_count > 0"

  - name: get-total-count
    query: |
      SELECT COUNT(*) as total
      FROM orders_old
      WHERE created_at BETWEEN {{ date_from | quote }} AND {{ date_to | quote }};
    capture: total_records

  - name: migrate-in-batches
    query: |
      WITH batch AS (
        SELECT *
        FROM orders_old
        WHERE created_at BETWEEN {{ date_from | quote }} AND {{ date_to | quote }}
        ORDER BY id
        LIMIT {{ batch_size }}
        OFFSET {{ iteration * batch_size }}
      )
      INSERT INTO orders_new
      SELECT
        id,
        customer_id,
        total,
        status,
        created_at,
        updated_at
      FROM batch
      ON CONFLICT (id) DO NOTHING;
    repeat: "{{ ceil(total_records / batch_size) }}"
    progress: true

  - name: verify-migration
    query: |
      SELECT
        (SELECT COUNT(*) FROM orders_old WHERE created_at BETWEEN {{ date_from | quote }} AND {{ date_to | quote }}) as source_count,
        (SELECT COUNT(*) FROM orders_new WHERE created_at BETWEEN {{ date_from | quote }} AND {{ date_to | quote }}) as target_count;
    validate: "result.source_count == result.target_count"

output:
  message: "Successfully migrated {{ total_records }} records"
  log_file: "logs/migration-{{ date_from }}-to-{{ date_to }}.log"
```

**Usage:**
```bash
aishell templates run migrate-orders-to-new-schema \
  --param date_from="2024-01-01" \
  --param date_to="2024-12-31" \
  --param batch_size=5000 \
  --verbose
```

---

### Use Case 3: Dynamic Dashboard Query

```yaml
name: dashboard-metrics
description: Generate dashboard metrics based on user role
category: analytics

parameters:
  user_role:
    type: enum
    values: [admin, manager, analyst, viewer]
    required: true
  date_range:
    type: number
    default: 7
    description: "Days to look back"

query: |
  -- Permissions based on role
  {% if user_role == 'admin' %}
    {% set allowed_tables = ['orders', 'users', 'revenue', 'costs'] %}
  {% elsif user_role == 'manager' %}
    {% set allowed_tables = ['orders', 'users', 'revenue'] %}
  {% elsif user_role == 'analyst' %}
    {% set allowed_tables = ['orders', 'revenue'] %}
  {% else %}
    {% set allowed_tables = ['orders'] %}
  {% endif %}

  WITH date_range AS (
    SELECT
      CURRENT_DATE - INTERVAL '{{ date_range }} days' as start_date,
      CURRENT_DATE as end_date
  )

  {% if 'orders' in allowed_tables %}
  , order_metrics AS (
    SELECT
      COUNT(*) as total_orders,
      SUM(total) as order_revenue,
      AVG(total) as avg_order_value
    FROM orders, date_range
    WHERE created_at BETWEEN start_date AND end_date
  )
  {% endif %}

  {% if 'users' in allowed_tables %}
  , user_metrics AS (
    SELECT
      COUNT(*) as new_users,
      COUNT(DISTINCT CASE WHEN last_login >= date_range.start_date THEN id END) as active_users
    FROM users, date_range
    WHERE created_at BETWEEN start_date AND end_date
  )
  {% endif %}

  {% if 'costs' in allowed_tables %}
  , cost_metrics AS (
    SELECT
      SUM(amount) as total_costs
    FROM costs, date_range
    WHERE date BETWEEN start_date AND end_date
  )
  {% endif %}

  SELECT
    {% if 'orders' in allowed_tables %}
    om.total_orders,
    om.order_revenue,
    om.avg_order_value,
    {% endif %}
    {% if 'users' in allowed_tables %}
    um.new_users,
    um.active_users,
    {% endif %}
    {% if 'revenue' in allowed_tables and 'costs' in allowed_tables %}
    om.order_revenue - cm.total_costs as profit,
    (om.order_revenue - cm.total_costs) / om.order_revenue * 100 as profit_margin,
    {% endif %}
    dr.start_date,
    dr.end_date
  FROM date_range dr
  {% if 'orders' in allowed_tables %}
  CROSS JOIN order_metrics om
  {% endif %}
  {% if 'users' in allowed_tables %}
  CROSS JOIN user_metrics um
  {% endif %}
  {% if 'costs' in allowed_tables %}
  CROSS JOIN cost_metrics cm
  {% endif %};

output:
  format: json
  cache:
    ttl: 300  # Cache for 5 minutes
    key: "dashboard-{{ user_role }}-{{ date_range }}"
```

---

## Template Library

### Official Templates

```bash
# Install official template library
aishell templates import --source official

# Available official templates:

# Analytics
- user-cohort-analysis
- retention-report
- conversion-funnel
- revenue-analysis

# Operations
- daily-health-check
- slow-query-finder
- table-size-report
- index-usage-stats

# Administration
- user-management
- permission-audit
- backup-verification
- database-cleanup

# Development
- schema-diff
- data-validation
- test-data-generator
- migration-helper
```

### Community Templates

```bash
# Browse community templates
aishell templates browse --source community

# Search for specific templates
aishell templates search "e-commerce" --source community

# Install community template
aishell templates install customer-lifetime-value --source community
```

---

## Best Practices

### 1. Parameter Validation

✅ **Always validate parameters**

```yaml
parameters:
  email:
    type: string
    required: true
    validate: "^[\\w.-]+@[\\w.-]+\\.\\w+$"
    error_message: "Invalid email format"

  age:
    type: number
    validate: "value >= 0 and value <= 150"
    error_message: "Age must be between 0 and 150"

  status:
    type: enum
    values: [active, inactive, suspended]
    error_message: "Status must be active, inactive, or suspended"
```

---

### 2. Use Meaningful Names

❌ **Don't use cryptic names**
```yaml
name: rpt1
name: query_template_v2
```

✅ **Do use descriptive names**
```yaml
name: monthly-revenue-by-region
name: active-users-last-30-days
```

---

### 3. Document Your Templates

✅ **Include comprehensive metadata**

```yaml
name: user-activity-report
version: 1.2.0
description: |
  Generate detailed user activity report including:
  - Login frequency
  - Feature usage
  - Time spent in app
  - Most used pages

author: analytics-team@company.com
created: 2025-10-01
updated: 2025-10-28

tags:
  - analytics
  - users
  - reporting

examples:
  - description: "Last 7 days activity"
    params:
      days: 7
  - description: "Monthly report for specific user"
    params:
      user_id: 12345
      days: 30
```

---

### 4. Version Your Templates

✅ **Use semantic versioning**

```bash
# Initial version
aishell templates save my-report --version 1.0.0

# Bug fix
aishell templates save my-report --version 1.0.1

# New feature (backwards compatible)
aishell templates save my-report --version 1.1.0

# Breaking change
aishell templates save my-report --version 2.0.0
```

---

### 5. Test Before Deployment

✅ **Always test templates**

```bash
# Test with sample data
aishell templates test my-template --sample-data

# Test all parameter combinations
aishell templates test my-template --all-combinations

# Performance test
aishell templates test my-template --performance --iterations 100

# Validate syntax
aishell templates validate my-template --strict
```

---

## Troubleshooting

### Issue 1: Template Not Found

**Error**: `Template 'my-template' not found`

**Solutions**:
```bash
# Check if template exists
aishell templates list | grep my-template

# Check template directory
ls -la ~/.aishell/templates/

# Re-import template
aishell templates import --file my-template.yaml

# Verify template path configuration
aishell config get templates.directory
```

---

### Issue 2: Parameter Validation Failed

**Error**: `Parameter 'date' validation failed: invalid format`

**Solutions**:
```bash
# Check parameter requirements
aishell templates show my-template

# View parameter examples
aishell templates show my-template --example

# Use correct format
aishell templates run my-template --param date="2025-10-28"

# Skip validation (not recommended)
aishell templates run my-template --no-validate --param date="invalid"
```

---

### Issue 3: Template Syntax Error

**Error**: `Syntax error in template at line 15`

**Solutions**:
```bash
# Validate template
aishell templates validate my-template --verbose

# Check template source
aishell templates show my-template --source

# Edit and fix
aishell templates edit my-template

# Test after fix
aishell templates test my-template
```

---

### Issue 4: Query Execution Failed

**Error**: `Query execution failed: column "xyz" does not exist`

**Solutions**:
```bash
# Check generated query
aishell templates run my-template --dry-run

# Verify database schema
aishell schema describe table_name

# Test with smaller dataset
aishell templates run my-template --param limit=10

# Add error handling
# In template:
on_error: rollback
retry: 3
retry_delay: 1000
```

---

## API Reference

### JavaScript/TypeScript API

```typescript
import { TemplateEngine } from '@aishell/templates';

// Initialize template engine
const engine = new TemplateEngine({
  templateDir: '~/.aishell/templates',
  autoReload: true
});

// Load template
const template = await engine.load('daily-sales');

// Set parameters
template.setParam('date', '2025-10-28');
template.setParam('region', 'north');

// Get generated SQL
const sql = template.render();
console.log(sql);

// Execute template
const results = await template.execute();

// Save new template
const newTemplate = engine.create({
  name: 'my-query',
  parameters: {
    id: { type: 'number', required: true }
  },
  query: 'SELECT * FROM users WHERE id = {{ id }}'
});

await newTemplate.save();

// Validate template
const validation = await newTemplate.validate();
if (!validation.valid) {
  console.error(validation.errors);
}

// Export template
await newTemplate.export('my-query.yaml');
```

### Python API

```python
from aishell.templates import TemplateEngine

# Initialize
engine = TemplateEngine(template_dir='~/.aishell/templates')

# Load and execute
template = engine.load('daily-sales')
template.set_param('date', '2025-10-28')
results = template.execute()

# Create new template
template = engine.create(
    name='my-query',
    parameters={'id': {'type': 'number', 'required': True}},
    query='SELECT * FROM users WHERE id = {{ id }}'
)
template.save()
```

---

## Summary

The Template System provides:

- 📝 **Reusable Query Patterns** - Write once, use everywhere
- 🔒 **Parameter Validation** - Built-in security and type checking
- 🔄 **Version Control** - Track changes over time
- 🎯 **Type System** - Query, CRUD, Report, Migration, Workflow
- 🧩 **Composition** - Combine templates for complex operations
- 📊 **Output Formats** - Table, JSON, CSV, YAML
- ⚡ **Performance** - Caching and optimization
- 🤝 **Team Collaboration** - Share templates across teams

For more information:
- [Query Builder Guide](./query-builder.md)
- [Pattern Detection](./pattern-detection.md)
- [API Reference](../api/templates.md)

---

**Need Help?**
- 📖 [Full Documentation](../README.md)
- 💬 [Community Forum](https://github.com/yourusername/aishell/discussions)
- 🐛 [Report Issues](https://github.com/yourusername/aishell/issues)
