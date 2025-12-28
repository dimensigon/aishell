# AI-Shell Hands-On Tutorial - Part 6: AI Features & Advanced Security

**Level:** Expert
**Duration:** 60-90 minutes
**Prerequisites:** Complete Parts 1-5

## Overview

This tutorial covers AI-Shell's most advanced features: the AI Query Assistant for natural language database interactions, and enterprise-grade security features including 2FA, SSO, anomaly detection, and activity monitoring.

## Learning Objectives

By the end of this tutorial, you will:
- Use the AI Query Assistant with and without API keys
- Convert natural language to complex SQL queries
- Get AI-powered query explanations and optimizations
- Set up two-factor authentication
- Configure SSO integration
- Implement anomaly detection
- Monitor and audit database activity

---

## Part 1: AI Query Assistant Setup (15 minutes)

### 1.1 Configure AI Assistant

The AI Query Assistant can work with multiple AI providers:

```bash
# Start AI-Shell
aishell

# Configure OpenAI (recommended)
aishell> ai config set --provider openai --api-key sk-your-key-here

# Alternative: Configure Anthropic Claude
aishell> ai config set --provider anthropic --api-key sk-ant-your-key-here

# Alternative: Configure local AI model (no API key needed)
aishell> ai config set --provider local --model-path /path/to/model

# Alternative: Configure Azure OpenAI
aishell> ai config set \
  --provider azure \
  --api-key your-azure-key \
  --endpoint https://your-resource.openai.azure.com \
  --deployment your-deployment-name

# View current configuration
aishell> ai config show
```

**Expected Output:**
```
AI Configuration:
  Provider: openai
  Model: gpt-4-turbo-preview
  API Key: sk-••••••••••••••••
  Max Tokens: 4096
  Temperature: 0.7
  Status: ✓ Connected

Features Enabled:
  ✓ Natural language queries
  ✓ Query explanation
  ✓ Query optimization
  ✓ Schema understanding
  ✓ Error correction
```

### 1.2 Configure AI Without API Key (Local Mode)

For development or privacy-sensitive environments:

```bash
# Use local AI model (requires download first)
aishell> ai download --model tinyllama-1.1b

# Configure local AI
aishell> ai config set --provider local --model tinyllama-1.1b

# Test local AI
aishell> ai test "SELECT users from database"
```

**Note:** Local models are less powerful but provide:
- No API costs
- Complete privacy
- Offline functionality
- Lower latency for simple queries

### 1.3 Connect Database for AI Context

```bash
# Connect to your database
aishell> db add postgresql://localhost/ecommerce --name main_db

# Let AI learn your schema
aishell> ai learn main_db

# Expected output:
# ✓ Analyzing database schema...
# ✓ Found 12 tables
# ✓ Found 87 columns
# ✓ Found 15 relationships
# ✓ Found 8 indexes
# ✓ Schema context loaded
#
# AI can now help with:
# - Table: users (5 columns)
# - Table: products (8 columns)
# - Table: orders (7 columns)
# - Table: order_items (5 columns)
# - ...
```

---

## Part 2: Natural Language Queries (20 minutes)

### 2.1 Simple Queries

```bash
# Ask in natural language (prefix with 'ai:')
aishell> ai: show me all users

# AI generates and executes:
SELECT * FROM users;
```

**AI Output:**
```
💡 I understood: "Retrieve all user records"

Generated Query:
  SELECT * FROM users;

Explanation:
  This query retrieves all columns from the users table.

✓ Executing query...

Results: 1,247 rows

user_id | name          | email                | created_at
--------|---------------|----------------------|-------------------
1       | John Doe      | john@example.com     | 2024-01-15 10:23:45
2       | Jane Smith    | jane@example.com     | 2024-01-16 09:15:22
...
```

### 2.2 Filtering and Conditions

```bash
# Natural language with conditions
aishell> ai: find users who signed up in the last 30 days

# AI generates:
SELECT *
FROM users
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY created_at DESC;
```

```bash
# Complex conditions
aishell> ai: show me orders over $100 that haven't been shipped yet

# AI generates:
SELECT o.order_id, o.total_amount, o.status, u.name as customer_name
FROM orders o
JOIN users u ON o.user_id = u.user_id
WHERE o.total_amount > 100
  AND o.status != 'shipped'
ORDER BY o.created_at DESC;
```

```bash
# Multiple conditions
aishell> ai: list products that are either low stock (less than 50) or expensive (over $100)

# AI generates:
SELECT product_id, name, price, stock, category
FROM products
WHERE stock < 50 OR price > 100
ORDER BY
  CASE WHEN stock < 50 THEN 1 ELSE 2 END,
  stock ASC;
```

### 2.3 Aggregation and Analytics

```bash
# Count and sum
aishell> ai: how many orders do we have per customer?

# AI generates:
SELECT
  u.user_id,
  u.name,
  COUNT(o.order_id) as order_count,
  SUM(o.total_amount) as total_spent
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.name
ORDER BY order_count DESC;
```

```bash
# Time-based analytics
aishell> ai: show me daily revenue for the last week

# AI generates:
SELECT
  DATE(created_at) as order_date,
  COUNT(*) as order_count,
  SUM(total_amount) as daily_revenue,
  AVG(total_amount) as avg_order_value
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY order_date DESC;
```

```bash
# Complex analytics
aishell> ai: what are the top 5 best-selling products this month?

# AI generates:
SELECT
  p.product_id,
  p.name,
  p.category,
  COUNT(oi.order_item_id) as times_ordered,
  SUM(oi.quantity) as units_sold,
  SUM(oi.quantity * oi.price) as total_revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE DATE_TRUNC('month', o.created_at) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY p.product_id, p.name, p.category
ORDER BY units_sold DESC
LIMIT 5;
```

### 2.4 Joins and Relationships

```bash
# Natural language joins
aishell> ai: show me customers with their order history

# AI generates:
SELECT
  u.user_id,
  u.name,
  u.email,
  COUNT(DISTINCT o.order_id) as total_orders,
  MAX(o.created_at) as last_order_date,
  SUM(o.total_amount) as lifetime_value
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.name, u.email
ORDER BY lifetime_value DESC;
```

```bash
# Complex multi-table joins
aishell> ai: list all orders with customer details and item details

# AI generates:
SELECT
  o.order_id,
  o.created_at as order_date,
  u.name as customer_name,
  u.email as customer_email,
  p.name as product_name,
  oi.quantity,
  oi.price as unit_price,
  (oi.quantity * oi.price) as line_total
FROM orders o
JOIN users u ON o.user_id = u.user_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
ORDER BY o.created_at DESC, o.order_id, oi.order_item_id;
```

### 2.5 Advanced Queries

```bash
# Subqueries
aishell> ai: find users who spent more than the average customer

# AI generates:
WITH customer_spending AS (
  SELECT
    user_id,
    SUM(total_amount) as total_spent
  FROM orders
  GROUP BY user_id
),
avg_spending AS (
  SELECT AVG(total_spent) as avg_amount
  FROM customer_spending
)
SELECT
  u.user_id,
  u.name,
  u.email,
  cs.total_spent,
  ROUND((cs.total_spent / avgs.avg_amount - 1) * 100, 2) as pct_above_avg
FROM users u
JOIN customer_spending cs ON u.user_id = cs.user_id
CROSS JOIN avg_spending avgs
WHERE cs.total_spent > avgs.avg_amount
ORDER BY cs.total_spent DESC;
```

```bash
# Window functions
aishell> ai: rank products by revenue within each category

# AI generates:
SELECT
  category,
  name as product_name,
  total_revenue,
  RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) as rank_in_category,
  ROUND(total_revenue / SUM(total_revenue) OVER (PARTITION BY category) * 100, 2) as pct_of_category_revenue
FROM (
  SELECT
    p.category,
    p.name,
    SUM(oi.quantity * oi.price) as total_revenue
  FROM products p
  JOIN order_items oi ON p.product_id = oi.product_id
  GROUP BY p.product_id, p.category, p.name
) product_revenues
ORDER BY category, rank_in_category;
```

```bash
# Cohort analysis
aishell> ai: show customer retention by signup month

# AI generates:
WITH user_cohorts AS (
  SELECT
    user_id,
    DATE_TRUNC('month', created_at) as cohort_month
  FROM users
),
order_months AS (
  SELECT
    user_id,
    DATE_TRUNC('month', created_at) as order_month
  FROM orders
)
SELECT
  uc.cohort_month,
  om.order_month,
  EXTRACT(MONTH FROM AGE(om.order_month, uc.cohort_month)) as months_since_signup,
  COUNT(DISTINCT om.user_id) as active_users,
  COUNT(DISTINCT uc.user_id) as cohort_size,
  ROUND(COUNT(DISTINCT om.user_id)::NUMERIC / COUNT(DISTINCT uc.user_id) * 100, 2) as retention_rate
FROM user_cohorts uc
LEFT JOIN order_months om ON uc.user_id = om.user_id
GROUP BY uc.cohort_month, om.order_month
ORDER BY uc.cohort_month, months_since_signup;
```

---

## Part 3: AI Query Optimization (15 minutes)

### 3.1 Get Query Explanations

```bash
# Ask AI to explain any query
aishell> ai explain
SELECT u.name, COUNT(o.order_id) as orders
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.name;
```

**AI Output:**
```
📊 Query Explanation:

Purpose:
  This query counts the number of orders for each user.

Query Breakdown:
  1. FROM users u
     - Starts with the users table (alias: u)

  2. LEFT JOIN orders o ON u.user_id = o.user_id
     - Joins orders table (alias: o)
     - Uses LEFT JOIN to include users with zero orders
     - Matches on user_id column

  3. COUNT(o.order_id) as orders
     - Counts order_id for each user
     - NULL values (users with no orders) count as 0

  4. GROUP BY u.name
     - Groups results by user name
     - Enables aggregation (COUNT)

Potential Issues:
  ⚠️  Grouping by name may produce incorrect results if multiple users have the same name
  💡 Suggestion: GROUP BY u.user_id, u.name instead

Performance:
  - Estimated rows: 1,247
  - Estimated cost: 45.32
  - Uses index: idx_orders_user_id ✓
  - Seq scan on users (consider index on name if filtering by name)
```

### 3.2 Get Optimization Suggestions

```bash
# Ask AI to optimize a slow query
aishell> ai optimize
SELECT *
FROM orders o
WHERE o.user_id IN (
  SELECT user_id
  FROM users
  WHERE email LIKE '%@gmail.com'
)
ORDER BY o.created_at DESC;
```

**AI Output:**
```
🚀 Optimization Suggestions:

Original Query Performance:
  ⚠️  Execution time: 2,450 ms
  ⚠️  Rows scanned: 1,247,000
  ⚠️  Using subquery in WHERE clause (inefficient)
  ⚠️  No index on users.email

Optimized Query:
  SELECT o.*
  FROM orders o
  INNER JOIN users u ON o.user_id = u.user_id
  WHERE u.email LIKE '%@gmail.com'
  ORDER BY o.created_at DESC;

Improvements:
  ✓ Replaced IN subquery with JOIN (more efficient)
  ✓ Uses INNER JOIN (no need for LEFT JOIN here)
  ✓ Specified columns (o.* instead of *)

Additional Recommendations:
  1. Create index on users.email:
     CREATE INDEX idx_users_email ON users(email);

  2. If searching by email domain is common, consider:
     CREATE INDEX idx_users_email_pattern ON users(email text_pattern_ops);

  3. Index already exists on orders.created_at ✓

Expected Performance:
  ✓ Execution time: ~180 ms (13x faster)
  ✓ Rows scanned: ~85,000 (reduced by 93%)

Would you like me to:
  1. Execute optimized query
  2. Create recommended indexes
  3. Explain query plan
  4. Cancel

Choose [1-4]:
```

### 3.3 Automatic Index Suggestions

```bash
# Ask AI to analyze your database for index opportunities
aishell> ai analyze-indexes main_db

# AI scans query logs and suggests indexes
```

**AI Output:**
```
🔍 Index Analysis for main_db

Analyzing query patterns from the last 7 days...
✓ Analyzed 45,892 queries

Recommended Indexes:

High Priority (will improve >50% of slow queries):
  1. CREATE INDEX idx_orders_user_id_created_at ON orders(user_id, created_at);
     Impact: 23,455 queries (avg 1,200ms → 85ms)
     Reason: Frequently filtered by user_id and sorted by created_at

  2. CREATE INDEX idx_products_category_price ON products(category, price);
     Impact: 12,348 queries (avg 450ms → 35ms)
     Reason: Common pattern: filter by category, sort by price

Medium Priority:
  3. CREATE INDEX idx_users_email ON users(email);
     Impact: 5,234 queries (avg 320ms → 15ms)
     Reason: Frequent lookups by email

  4. CREATE INDEX idx_order_items_product_id ON order_items(product_id);
     Impact: 3,892 queries (avg 180ms → 25ms)
     Reason: Join performance improvement

Low Priority:
  5. CREATE INDEX idx_users_created_at ON users(created_at);
     Impact: 1,456 queries (avg 95ms → 12ms)
     Reason: Date range queries on user signups

Estimated Total Improvement:
  Average query time: 845ms → 52ms (94% faster)
  Disk space required: ~85 MB
  Index maintenance overhead: Low

Apply all high-priority indexes? [y/N]:
```

### 3.4 Query Correction

```bash
# AI automatically detects and fixes common errors
aishell> ai: show me user who made orders last month

# AI detects plural error and generates:
SELECT u.user_id, u.name, u.email, COUNT(o.order_id) as order_count
FROM users u
JOIN orders o ON u.user_id = o.user_id
WHERE DATE_TRUNC('month', o.created_at) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
GROUP BY u.user_id, u.name, u.email
ORDER BY order_count DESC;

# Note: AI corrected "user" → "users" (plural)
```

```bash
# AI fixes syntax errors
aishell> SELECT * FORM users WHERE email = john@example.com;

# AI detects errors:
```

**AI Output:**
```
⚠️  Syntax Errors Detected:

1. Typo: "FORM" should be "FROM"
2. Missing quotes: john@example.com should be 'john@example.com'

Corrected Query:
  SELECT * FROM users WHERE email = 'john@example.com';

Execute corrected query? [Y/n]:
```

---

## Part 4: Advanced Security Features (20 minutes)

### 4.1 Enable Two-Factor Authentication (2FA)

```bash
# Enable 2FA for your AI-Shell account
aishell> security 2fa enable

# Expected output:
```

**Output:**
```
🔐 Enabling Two-Factor Authentication

Step 1: Scan QR Code

  ████ ▄▄▄▄▄ █▀█ █▄▀▄▀▄█ ▄▄▄▄▄ ████
  ████ █   █ █▀▀▀█ ▀ ▀▀█ █   █ ████
  ████ █▄▄▄█ █▀ █▀▀▄ ▄ █ █▄▄▄█ ████
  ████▄▄▄▄▄▄▄█▀▄▀█▄█ █▀█▄▄▄▄▄▄▄████
  ████▄ ▄  ▀▄▄ ▀▄▀▄▄▀▄▀  ▄█  █▀████
  ████ ▄  ▀█▄ █ ▄ ██▄ ▀▀▀▄▄ ▀▀▀████
  ████ █▄▄▄█▄▄▀▄▀ █▀ ▄  ▀ ▀▄ █▀████
  ████▄▄▄███▄█ █▄ ▄ ▀▀█ ▄▄▄▄▀▀█████
  ████ ▄▄▄▄▄ █▄▄█ █▀▀  ▀ █ ▄  ████
  ████ █   █ █  ▄ ▄ ▀▀ ▄▄▄▄█▀█▀████
  ████ █▄▄▄█ █ ▀▄█ ▄▀▄ █▄▄▀ ▄▀█████
  ████▄▄▄▄▄▄▄█▄██▄█▄▄▄█▄▄██▄██▄████

  Or enter this key manually in your authenticator app:
  JBSWY3DPEHPK3PXP

Step 2: Enter 6-digit code from your authenticator app:
Code: 123456

✓ 2FA enabled successfully!

Backup Codes (save these securely):
  1. 8H3K-9NM2-4LP7
  2. 5QW8-2RT6-9YU3
  3. 1KJ7-6HG4-3FD9
  4. 7NB5-4VC2-8XZ1
  5. 3MK8-9LO5-2IU7

⚠️  Store these backup codes securely. You'll need one if you lose access to your authenticator.
```

```bash
# Verify 2FA status
aishell> security 2fa status

# Disable 2FA (requires authentication)
aishell> security 2fa disable
```

### 4.2 Configure Single Sign-On (SSO)

```bash
# Configure SSO with various providers

# Option 1: Google SSO
aishell> security sso configure google \
  --client-id "your-client-id" \
  --client-secret "your-client-secret" \
  --domain "yourcompany.com"

# Option 2: Microsoft Azure AD
aishell> security sso configure azure \
  --tenant-id "your-tenant-id" \
  --client-id "your-client-id" \
  --client-secret "your-client-secret"

# Option 3: Okta
aishell> security sso configure okta \
  --domain "yourcompany.okta.com" \
  --client-id "your-client-id" \
  --client-secret "your-client-secret"

# Option 4: SAML 2.0 (generic)
aishell> security sso configure saml \
  --idp-url "https://idp.example.com/saml" \
  --certificate-path "/path/to/cert.pem"
```

**Expected Output:**
```
✓ SSO Configuration: Google

Settings:
  Provider: Google
  Client ID: 123456789-abc.apps.googleusercontent.com
  Domain: yourcompany.com
  Redirect URI: https://localhost:8080/auth/callback

Status: ✓ Active

Test SSO:
  Visit: https://localhost:8080/auth/login

  Or use:
  aishell> security sso test
```

```bash
# Enable SSO enforcement
aishell> security sso enforce --required

# Allow specific users to bypass SSO
aishell> security sso allow-bypass user@example.com

# View SSO audit log
aishell> security sso audit-log --last 24h
```

### 4.3 Role-Based Access Control (RBAC)

```bash
# Create custom roles
aishell> security role create data_analyst \
  --permissions read_all_tables,create_views,execute_queries

aishell> security role create developer \
  --permissions read_all_tables,write_all_tables,create_indexes,execute_queries,create_functions

aishell> security role create admin \
  --permissions all

# Assign roles to users
aishell> security user grant john@example.com data_analyst
aishell> security user grant jane@example.com developer

# Create fine-grained permissions
aishell> security permission create \
  --role data_analyst \
  --table orders \
  --operations SELECT \
  --condition "created_at >= CURRENT_DATE - INTERVAL '90 days'"

# This allows data analysts to only see orders from last 90 days

# View user permissions
aishell> security user permissions john@example.com
```

**Expected Output:**
```
Permissions for john@example.com:

Roles:
  - data_analyst

Allowed Operations:
  Tables:
    ✓ users: SELECT
    ✓ orders: SELECT (last 90 days only)
    ✓ products: SELECT
    ✓ order_items: SELECT

  Views:
    ✓ CREATE VIEW
    ✓ DROP VIEW (own views only)

  Queries:
    ✓ SELECT queries
    ✗ INSERT queries
    ✗ UPDATE queries
    ✗ DELETE queries

  System:
    ✗ Backup operations
    ✗ Restore operations
    ✗ User management
```

### 4.4 Query Auditing

```bash
# Enable comprehensive audit logging
aishell> security audit enable --level detailed

# Configure audit log destination
aishell> security audit configure \
  --output-file /var/log/aishell/audit.log \
  --output-database postgresql://localhost/audit_db \
  --output-syslog true

# View audit log
aishell> security audit log --last 1h

# Expected output:
```

**Output:**
```
Audit Log (Last 1 hour):

Timestamp           User              Action              Table       Details                    Result
2025-10-11 10:23:45 john@example.com  SELECT              users       WHERE created_at > ...     Success (245 rows)
2025-10-11 10:24:12 jane@example.com  INSERT              products    1 row                      Success
2025-10-11 10:25:01 admin@example.com CREATE INDEX        products    idx_products_category      Success
2025-10-11 10:26:33 john@example.com  DELETE              orders      WHERE order_id = 5000      Denied (insufficient permissions)
2025-10-11 10:27:18 jane@example.com  UPDATE              products    SET price = 29.99 ...      Success (1 row)
2025-10-11 10:28:45 john@example.com  SELECT              orders      Large query (>10k rows)    Success (12,458 rows)
2025-10-11 10:29:12 unknown           LOGIN ATTEMPT       -           Failed (invalid password)  Failed
2025-10-11 10:30:00 admin@example.com BACKUP              main_db     /backups/main.dump         Success

High-Risk Events:
  ⚠️  10:26:33 - Failed DELETE attempt by john@example.com
  ⚠️  10:29:12 - Failed login attempt from IP 192.168.1.100
```

```bash
# Query audit log with filters
aishell> security audit query \
  --user john@example.com \
  --action DELETE \
  --result Failed \
  --last 7d

# Export audit log
aishell> security audit export \
  --format csv \
  --output /reports/audit_report.csv \
  --start "2025-10-01" \
  --end "2025-10-11"
```

---

## Part 5: Anomaly Detection (15 minutes)

### 5.1 Enable AI-Powered Anomaly Detection

```bash
# Enable anomaly detection
aishell> security anomaly enable

# Configure detection parameters
aishell> security anomaly configure \
  --sensitivity high \
  --alert-email security@yourcompany.com \
  --alert-slack "#security-alerts" \
  --baseline-days 30
```

**Expected Output:**
```
✓ Anomaly Detection Enabled

Configuration:
  Sensitivity: High
  Baseline Period: 30 days
  Alert Channels:
    - Email: security@yourcompany.com
    - Slack: #security-alerts

Monitoring:
  ✓ Unusual query patterns
  ✓ Excessive data access
  ✓ Off-hours access
  ✓ Failed authentication attempts
  ✓ Privilege escalation attempts
  ✓ Data exfiltration patterns
  ✓ Unusual geographic access

Learning baseline from last 30 days...
✓ Baseline established
```

### 5.2 Anomaly Detection in Action

```bash
# View detected anomalies
aishell> security anomaly list
```

**Example Anomalies:**
```
🚨 Detected Anomalies:

HIGH SEVERITY:
  1. Unusual Data Volume (2025-10-11 10:15:32)
     User: john@example.com
     Query: SELECT * FROM users
     Issue: Query returned 1.2M rows (baseline: 500 rows avg)
     Action: Query allowed but logged
     Risk Score: 85/100

  2. Off-Hours Access (2025-10-11 02:34:18)
     User: jane@example.com
     Location: IP 203.0.113.45 (Vietnam)
     Issue: Access from unusual location outside business hours
     Action: 2FA challenge issued
     Risk Score: 75/100

MEDIUM SEVERITY:
  3. Unusual Query Pattern (2025-10-11 09:12:45)
     User: developer@example.com
     Query: Multiple DELETE statements (15 in 2 minutes)
     Issue: Abnormal deletion rate (baseline: 2 per hour)
     Action: Temporarily rate-limited
     Risk Score: 60/100

  4. New Table Access (2025-10-11 08:45:22)
     User: john@example.com
     Table: financial_records
     Issue: First time accessing this sensitive table
     Action: Manager notification sent
     Risk Score: 55/100

LOW SEVERITY:
  5. Increased Query Frequency (2025-10-11 10:30:00)
     User: jane@example.com
     Issue: 150 queries in last hour (baseline: 45 per hour)
     Action: Monitoring
     Risk Score: 35/100
```

### 5.3 Configure Automated Responses

```bash
# Set up automated responses to anomalies
aishell> security anomaly response configure \
  --high-severity "require_2fa,alert_admin,rate_limit" \
  --medium-severity "alert_user,log_detailed" \
  --low-severity "log_standard"

# Create custom detection rules
aishell> security anomaly rule create \
  --name "large_export_detection" \
  --condition "rows_returned > 100000" \
  --action "require_approval" \
  --severity high

aishell> security anomaly rule create \
  --name "sensitive_table_access" \
  --condition "table IN ('users', 'credit_cards', 'financial_records')" \
  --action "notify_security_team" \
  --severity medium

# View active rules
aishell> security anomaly rule list
```

### 5.4 Anomaly Investigation

```bash
# Investigate specific anomaly
aishell> security anomaly investigate 1

# Expected output:
```

**Output:**
```
🔍 Anomaly Investigation: #1

Overview:
  Detected: 2025-10-11 10:15:32
  Type: Unusual Data Volume
  Severity: High
  Risk Score: 85/100

User Details:
  User: john@example.com
  Role: data_analyst
  Department: Marketing
  Last Login: 2025-10-11 09:45:23
  Location: 192.168.1.50 (Office Network)

Query Details:
  SELECT * FROM users;

  Execution Time: 8.5s
  Rows Returned: 1,247,892
  Data Volume: 145 MB

Baseline Comparison:
  Typical Query Size: 500 rows
  Typical Data Volume: 58 KB
  Deviation: 2,496x larger than normal

Historical Context:
  This user's previous queries:
    - Avg rows returned: 482
    - Max rows returned: 5,230
    - Never exceeded 10,000 rows before

Similar Patterns:
  ✓ No other users show this pattern
  ✗ Not consistent with user's role

Risk Factors:
  ⚠️  Extracted entire user table (sensitive data)
  ⚠️  2,496x larger than typical query
  ⚠️  No WHERE clause (unusual for this user)
  ✓  During business hours
  ✓  From office network
  ✓  2FA verified

Recommended Actions:
  1. Contact user to verify intent
  2. Review query necessity
  3. Implement data export policies
  4. Add WHERE clause requirements for large tables

Timeline:
  10:15:30 - Query initiated
  10:15:32 - Anomaly detected
  10:15:32 - Query completed (not blocked)
  10:15:33 - Alert sent to security team
  10:15:35 - Detailed audit log created
```

---

## Part 6: Real-Time Monitoring (10 minutes)

### 6.1 Security Dashboard

```bash
# Launch security dashboard
aishell> security dashboard
```

**Dashboard View:**
```
╔════════════════════════════════════════════════════════════════╗
║                    AI-Shell Security Dashboard                  ║
╠════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  Active Users (Last Hour): 12                                  ║
║  Total Queries: 1,458                                          ║
║  Failed Auth Attempts: 3                                       ║
║  Active Anomalies: 2 High, 3 Medium, 5 Low                    ║
║                                                                 ║
║  ┌─────────────────── Query Rate (per minute) ───────────────┐ ║
║  │ 45 ██████████░░░░░░░░░░░░░░░░░░░░░░░                      │ ║
║  │ 30 ██████████████░░░░░░░░░░░░░░░░░░                       │ ║
║  │ 15 ████████████████████░░░░░░░░░░░                        │ ║
║  │  0 ───────────────────────────────────                     │ ║
║  └─────────────────────────────────────────────────────────┘ ║
║                                                                 ║
║  Recent Alerts:                                                ║
║  🚨 HIGH   - Large data export by john@example.com (2m ago)    ║
║  ⚠️  MED    - Off-hours access from new location (15m ago)     ║
║  ℹ️  LOW    - Increased query rate by jane@example.com (5m)   ║
║                                                                 ║
║  Top Active Users:                                             ║
║  1. jane@example.com    (245 queries, 0 anomalies)            ║
║  2. john@example.com    (189 queries, 1 anomaly)              ║
║  3. developer@example.com (156 queries, 0 anomalies)          ║
║                                                                 ║
║  Database Health:                                              ║
║  ✓ Connection Pool: 45/100 (Healthy)                          ║
║  ✓ Response Time: 85ms avg (Good)                             ║
║  ✓ Error Rate: 0.2% (Low)                                     ║
║                                                                 ║
╚════════════════════════════════════════════════════════════════╝

Press [q] to quit, [r] to refresh, [a] for alerts, [u] for users
```

### 6.2 Real-Time Activity Monitoring

```bash
# Monitor queries in real-time
aishell> security monitor --real-time

# Monitor specific user
aishell> security monitor --user john@example.com --real-time

# Monitor specific table
aishell> security monitor --table users --real-time
```

**Real-Time Monitor Output:**
```
Real-Time Activity Monitor (Press Ctrl+C to stop)

10:45:23 | jane@example.com   | SELECT    | products      | 125 rows  | 45ms   | ✓
10:45:25 | john@example.com   | SELECT    | orders        | 1,248 rows| 120ms  | ✓
10:45:27 | admin@example.com  | UPDATE    | products      | 1 row     | 12ms   | ✓
10:45:29 | developer@example.com | INSERT | users         | 1 row     | 8ms    | ✓
10:45:31 | john@example.com   | DELETE    | orders        | -         | -      | ✗ DENIED
10:45:33 | jane@example.com   | SELECT    | order_items   | 5,234 rows| 280ms  | ⚠️  SLOW
10:45:35 | unknown            | LOGIN     | -             | -         | -      | ✗ FAILED

Anomalies Detected:
  🚨 10:45:31 - DELETE denied for john@example.com (insufficient permissions)
  ⚠️  10:45:33 - Slow query by jane@example.com (280ms)
  🚨 10:45:35 - Failed login attempt from 192.168.1.200
```

### 6.3 Alerting and Notifications

```bash
# Configure alert channels
aishell> security alert configure \
  --email "security@company.com,ops@company.com" \
  --slack "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  --webhook "https://your-monitoring-system.com/webhook" \
  --pagerduty-key "your-pagerduty-integration-key"

# Set alert thresholds
aishell> security alert threshold set \
  --failed-auth-attempts 5 \
  --query-rate-increase 200% \
  --data-export-size 100MB \
  --off-hours-access true

# Test alert system
aishell> security alert test
```

**Alert Example (Slack):**
```
🚨 AI-Shell Security Alert

Severity: HIGH
Time: 2025-10-11 10:45:31 UTC
Database: main_db

Alert: Excessive Data Export

Details:
  User: john@example.com
  Query: SELECT * FROM users
  Data Exported: 145 MB
  Threshold: 100 MB
  Risk Score: 85/100

Actions Taken:
  ✓ Query completed (not blocked)
  ✓ Detailed audit log created
  ✓ Security team notified

Recommended Actions:
  1. Verify user intent
  2. Review data access policies
  3. Consider implementing approval workflow for large exports

View Details: https://aishell-dashboard/anomalies/12345
```

---

## Practice Exercises

### Exercise 1: Natural Language Query Practice

```bash
# Try these natural language queries:

1. "Show me the top 10 customers by total spending"
2. "What products were ordered more than 50 times last month?"
3. "Find customers who haven't ordered in the last 90 days"
4. "Calculate average order value by customer segment"
5. "Show daily new user signups for the last 30 days"
```

### Exercise 2: Security Configuration

```bash
# Complete security setup:

1. Enable 2FA for all users
2. Configure SSO with your provider
3. Create three custom roles: viewer, analyst, admin
4. Enable audit logging
5. Configure anomaly detection
6. Set up alert notifications
```

### Exercise 3: Anomaly Response Simulation

```bash
# Simulate and respond to anomalies:

1. Generate test anomaly (large query)
2. Investigate the anomaly
3. Create custom detection rule
4. Configure automated response
5. Test alert system
```

---

## Troubleshooting

### AI Assistant Issues

```bash
# AI not responding
aishell> ai test "simple test"
aishell> ai config show
# Check API key and connectivity

# AI generating incorrect queries
aishell> ai learn main_db  # Refresh schema understanding
aishell> ai explain <your-query>  # Get detailed explanation

# Local AI model not working
aishell> ai download --model tinyllama-1.1b --force
aishell> ai config set --provider local
```

### Security Issues

```bash
# 2FA locked out
# Use backup code from setup

# SSO not working
aishell> security sso test
aishell> security sso audit-log

# Anomaly false positives
aishell> security anomaly configure --sensitivity medium
aishell> security anomaly rule disable <rule-name>

# Audit log too large
aishell> security audit rotate
aishell> security audit compress --older-than 30d
```

---

## Next Steps

🎉 **Congratulations!** You've completed all 6 parts of the AI-Shell comprehensive tutorial!

You now have expert-level knowledge of:
- Database operations across multiple database types
- Advanced querying and optimization techniques
- NoSQL databases (MongoDB, Redis)
- Backup, restore, and migration strategies
- AI-powered query assistance
- Enterprise security features

### Continue Learning:

1. **Explore the API**
   - Build applications using AI-Shell's REST API
   - Integrate with your existing tools

2. **Advanced Topics**
   - High availability setups
   - Replication and clustering
   - Performance tuning
   - Custom integrations

3. **Community**
   - Join AI-Shell Discord/Slack
   - Contribute to documentation
   - Share your use cases

---

## Quick Reference

### AI Commands

```bash
# Configure AI
aishell> ai config set --provider <provider> --api-key <key>
aishell> ai learn <database>

# Natural language queries
aishell> ai: <natural language query>

# Query operations
aishell> ai explain <query>
aishell> ai optimize <query>
aishell> ai analyze-indexes <database>
```

### Security Commands

```bash
# 2FA
aishell> security 2fa enable
aishell> security 2fa status

# SSO
aishell> security sso configure <provider>
aishell> security sso enforce

# Audit
aishell> security audit enable
aishell> security audit log
aishell> security audit query

# Anomaly Detection
aishell> security anomaly enable
aishell> security anomaly list
aishell> security anomaly investigate <id>

# Monitoring
aishell> security monitor --real-time
aishell> security dashboard
```

---

Thank you for completing this comprehensive tutorial! Happy querying! 🚀
