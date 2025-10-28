# Database Federation Tutorial

> **📋 Implementation Status**
>
> **Current Status:** Planned
> **CLI Availability:** Coming Soon
> **Completeness:** 15%
>
> **What Works Now:**
> - Single database connection management
> - Basic query execution
>
> **Coming Soon:**
> - Multi-database connection support
> - Cross-database query execution
> - Federated joins and aggregations
> - Data type conversion between database types
> - Optimized federated query strategies
> - Cross-database transaction support
>
> **Note:** This tutorial describes the intended functionality. Check the [Gap Analysis Report](../FEATURE_GAP_ANALYSIS_REPORT.md) for detailed implementation status.

## Introduction and Overview

AI-Shell is the world's first multi-database federation platform, allowing you to query across PostgreSQL, MySQL, MongoDB, Redis, Oracle, and more in a single command. No more context switching between different database clients, learning different query syntaxes, or writing complex ETL pipelines.

This tutorial will teach you how to:
- Connect multiple databases simultaneously
- Query across different database types in one command
- Perform cross-database joins and aggregations
- Optimize federated query performance
- Manage multi-database connections
- Handle data type conversions automatically

**What You'll Learn:**
- Multi-database connection setup
- Cross-database query syntax
- Federated join strategies
- Data type mapping and conversion
- Performance optimization for federation
- Best practices for multi-database architectures

**Time to Complete:** 35-45 minutes

---

## Prerequisites

Before starting this tutorial, ensure you have:

### Required
- AI-Shell installed (v1.0.0 or higher)
  ```bash
  npm install -g ai-shell
  ```
- Access to at least 2 different databases (any combination of PostgreSQL, MySQL, MongoDB, Redis, Oracle)
- Anthropic API key configured
  ```bash
  export ANTHROPIC_API_KEY="your-api-key"
  ```

### Recommended
- Different database types for best learning experience (e.g., PostgreSQL + MongoDB)
- Sample data in each database
- Basic understanding of each database's data model
- Development/test databases (not production)

### Verify Your Setup
```bash
# Check federation features are available
ai-shell features check federation
# Expected: ✓ Federation features enabled

# Check supported database types
ai-shell federation supported-databases
# Expected: PostgreSQL, MySQL, MongoDB, Redis, Oracle, Cassandra, Neo4j

# Verify AI-Shell version
ai-shell --version
# Expected: v1.0.0 or higher
```

---

## Step-by-Step Instructions

### Step 1: Connecting Multiple Databases

First, establish connections to multiple databases.

```bash
# Connect to PostgreSQL (users and orders)
ai-shell connect postgres://user:pass@localhost:5432/ecommerce \
  --name pg-ecommerce \
  --alias postgres

# Connect to MongoDB (product catalog)
ai-shell connect mongodb://user:pass@localhost:27017/products \
  --name mongo-products \
  --alias mongodb

# Connect to Redis (session data)
ai-shell connect redis://localhost:6379/0 \
  --name redis-sessions \
  --alias redis

# List all connections
ai-shell connections list

# Output:
# 📊 Database Connections
#
# 1. pg-ecommerce (PostgreSQL)
#    Host: localhost:5432
#    Database: ecommerce
#    Status: ✓ Connected
#    Tables: users, orders, payments
#
# 2. mongo-products (MongoDB)
#    Host: localhost:27017
#    Database: products
#    Status: ✓ Connected
#    Collections: products, categories, reviews
#
# 3. redis-sessions (Redis)
#    Host: localhost:6379
#    Database: 0
#    Status: ✓ Connected
#    Keys: ~45,000 session keys
```

**Connection Configuration:**
```bash
# Save connections to config file
ai-shell connections export ~/.ai-shell/connections.yaml

# connections.yaml example:
# connections:
#   pg-ecommerce:
#     type: postgres
#     host: localhost
#     port: 5432
#     database: ecommerce
#     pool: {min: 2, max: 10}
#   mongo-products:
#     type: mongodb
#     host: localhost
#     port: 27017
#     database: products
#   redis-sessions:
#     type: redis
#     host: localhost
#     port: 6379

# Load connections from config
ai-shell connections import ~/.ai-shell/connections.yaml
```

---

### Step 2: Your First Cross-Database Query

Query data from multiple databases in natural language.

```bash
# Simple cross-database query
ai-shell query "show user names from postgres and their session count from redis"

# AI-Shell processes:
# 🔍 Analyzing query...
# 📊 Databases involved: postgres (users), redis (sessions)
# 🔄 Executing federated query...

# Results:
# ┌──────────────┬───────────────┐
# │ user_name    │ session_count │
# ├──────────────┼───────────────┤
# │ John Doe     │ 47            │
# │ Jane Smith   │ 32            │
# │ Bob Johnson  │ 28            │
# └──────────────┴───────────────┘
#
# ✓ Query executed in 234ms (federated across 2 databases)

# More complex example
ai-shell query "
  show customer names from postgres,
  their order totals from postgres,
  and product details from mongodb
"

# AI-Shell automatically:
# 1. Identifies data sources
# 2. Determines join keys
# 3. Optimizes query execution order
# 4. Merges results
```

---

### Step 3: Understanding Federation Strategies

AI-Shell uses different strategies based on query patterns.

#### Strategy 1: Parallel Execution
```bash
# When queries are independent
ai-shell query "
  get user count from postgres
  and product count from mongodb
" --explain

# Execution Plan:
# Strategy: Parallel Execution
#
# Thread 1: SELECT COUNT(*) FROM postgres.users
# Thread 2: db.products.count() in mongodb
#
# Both queries execute simultaneously
# Results merged after completion
#
# Time: 45ms (vs 89ms sequential)
```

#### Strategy 2: Client-Side Join
```bash
# When databases don't share a connection
ai-shell query "
  join users from postgres with profiles from mongodb on user_id
" --explain

# Execution Plan:
# Strategy: Client-Side Join (Hash Join)
#
# Step 1: Fetch users from postgres (1,247 rows)
# Step 2: Fetch profiles from mongodb (1,247 docs)
# Step 3: Hash join on user_id (in AI-Shell)
#
# Memory: 2.4MB
# Time: 156ms
```

#### Strategy 3: Data Locality Optimization
```bash
# When one dataset is much smaller
ai-shell query "
  join large_orders from postgres (1.2M rows)
  with small_products from mongodb (500 rows)
" --explain

# Execution Plan:
# Strategy: Data Locality (Pull Small to Large)
#
# Step 1: Fetch products from mongodb (500 rows)
# Step 2: Push product_ids to postgres
# Step 3: Filter orders in postgres WHERE product_id IN (...)
# Step 4: Join in postgres
#
# Data transferred: 15KB (vs 450MB naive approach)
# Time: 234ms (vs 12,847ms naive)
```

---

### Step 4: Cross-Database Joins

Perform joins across different database systems.

```bash
# Simple join between PostgreSQL and MongoDB
ai-shell query "
  show user email from postgres
  and user preferences from mongodb
  where user_id matches
"

# Multiple joins across 3 databases
ai-shell query "
  combine:
  - user info from postgres
  - session data from redis
  - order history from mongodb
"

# Left join (include nulls)
ai-shell query "
  show all users from postgres
  with their wishlist from mongodb
  including users with no wishlist
"

# Complex join with filtering
ai-shell query "
  join premium users from postgres
  with high-value products from mongodb
  where user.tier = 'premium'
  and product.price > 100
"
```

**Automatic Join Key Detection:**
```bash
# AI-Shell automatically detects join keys
ai-shell query "join users from postgres with profiles from mongodb"

# If ambiguous, AI-Shell asks:
# 🔍 Multiple possible join keys detected:
# 1. user_id (most common)
# 2. email (alternative)
# 3. username (alternative)
#
# Which should I use? [1-3 or specify]: 1
```

---

### Step 5: Aggregations Across Databases

Perform aggregations using data from multiple sources.

```bash
# Sum across databases
ai-shell query "
  show total revenue from:
  - completed orders in postgres
  - pending orders in mongodb
"

# Average from multiple sources
ai-shell query "
  calculate average order value combining:
  - orders from postgres
  - orders from mysql backup
"

# Count across databases
ai-shell query "
  count total active users across:
  - postgres main database
  - mongodb archive
  - redis cache
"

# Complex aggregation
ai-shell query "
  show revenue by product category where:
  - orders come from postgres
  - products come from mongodb
  - group by mongodb's category field
"
```

---

### Step 6: Working with Different Data Models

Handle relational (SQL) and NoSQL data models together.

#### Querying MongoDB Documents in SQL-Style
```bash
# Flatten MongoDB nested documents for SQL-like queries
ai-shell query "
  from mongodb products,
  show product.name and product.details.manufacturer
"

# AI-Shell automatically handles:
# - Nested field access (product.details.manufacturer)
# - Array fields (converted to separate rows or JSON)
# - Embedded documents (flattened or preserved as JSON)
```

#### Joining SQL Tables with NoSQL Collections
```bash
# Relational table + document collection
ai-shell query "
  join orders from postgres (relational)
  with products from mongodb (documents)
  showing order.id, order.total, product.name, product.details
"

# Output format options:
ai-shell query "..." --format json    # JSON with nested objects
ai-shell query "..." --format table   # Flattened table
ai-shell query "..." --format csv     # Comma-separated
```

#### Redis Key-Value Integration
```bash
# Use Redis data in joins
ai-shell query "
  show users from postgres
  with their session_count from redis
  where redis key pattern is 'session:*'
"

# Redis hash fields
ai-shell query "
  get user:* hash fields from redis
  and join with user details from postgres
"
```

---

### Step 7: Data Type Conversion

AI-Shell automatically handles data type differences.

```bash
# Date/Time conversions
ai-shell query "
  combine:
  - orders from postgres (timestamp format)
  - events from mongodb (ISODate format)
  - logs from mysql (datetime format)
  where all dates > '2025-01-01'
"

# AI-Shell converts all to common format automatically

# Numeric conversions
ai-shell query "
  show totals from:
  - postgres (numeric type)
  - mongodb (NumberDecimal)
  - redis (string stored numbers)
"

# String encoding handling
ai-shell query "
  join:
  - utf8 strings from postgres
  - latin1 strings from legacy mysql
  - unicode strings from mongodb
"

# View conversion details
ai-shell query "..." --show-conversions

# Output:
# 🔄 Type Conversions Applied:
# - postgres.created_at (timestamp) → standard_timestamp
# - mongodb.createdAt (ISODate) → standard_timestamp
# - mysql.order_date (datetime) → standard_timestamp
# - redis.price (string) → numeric
```

---

### Step 8: Optimizing Federated Query Performance

Improve performance of cross-database queries.

```bash
# Analyze federated query performance
ai-shell query "your federated query" --analyze

# Output:
# 📊 Federated Query Analysis
#
# Data Transfer:
# - postgres → AI-Shell: 1,247 rows (245KB)
# - mongodb → AI-Shell: 1,247 docs (892KB)
# Total transfer: 1.1MB
#
# Processing Time:
# - postgres query: 45ms
# - mongodb query: 67ms
# - client join: 34ms
# - formatting: 12ms
# Total: 158ms
#
# Optimization Opportunities:
# ⚡ Add filter to postgres query (reduce from 1,247 to ~200 rows)
# ⚡ Pre-aggregate mongodb data (reduce transfer by 70%)

# Apply optimizations
ai-shell optimize "your federated query"

# Strategy 1: Filter pushdown
# Before: Fetch all, then filter
# After: Filter in source database

# Strategy 2: Projection pushdown
# Before: SELECT * (23 columns)
# After: SELECT only needed columns (3 columns)

# Strategy 3: Aggregation pushdown
# Before: Aggregate in AI-Shell
# After: Aggregate in source database

# Monitor federated query performance
ai-shell monitor federation --real-time
```

**Caching for Repeated Queries:**
```bash
# Enable federation cache
ai-shell config set federation.cache.enabled true
ai-shell config set federation.cache.ttl 300  # 5 minutes

# Cache results for expensive queries
ai-shell query "expensive federated query" --cache

# Clear cache when data updates
ai-shell cache clear federation
```

---

### Step 9: Advanced Federation Patterns

Master sophisticated cross-database scenarios.

#### Pattern 1: Multi-Database Transactions
```bash
# Coordinated writes across databases
ai-shell transaction "
  insert user into postgres
  and create profile in mongodb
  and initialize session in redis
" --rollback-on-error

# AI-Shell uses two-phase commit protocol
# If any operation fails, all are rolled back
```

#### Pattern 2: Cross-Database Subqueries
```bash
# Use results from one database to query another
ai-shell query "
  find products in mongodb
  where product_id IN (
    select product_id from top_selling_products in postgres
  )
"
```

#### Pattern 3: Federated Views
```bash
# Create virtual view spanning databases
ai-shell view create customer_360 "
  SELECT
    u.name, u.email from postgres.users u,
    p.preferences from mongodb.profiles p,
    COUNT(s.id) as sessions from redis.sessions s
  WHERE u.user_id = p.user_id
    AND u.user_id = s.user_id
"

# Query the federated view
ai-shell query "select * from customer_360 where sessions > 10"

# List federated views
ai-shell views list
```

#### Pattern 4: Time-Series Across Databases
```bash
# Combine time-series data from different sources
ai-shell query "
  show daily metrics combining:
  - user signups from postgres
  - page views from mongodb
  - cache hits from redis
  grouped by date for last 30 days
"
```

---

### Step 10: Managing Federation Configuration

Configure and tune federation behavior.

```bash
# View federation settings
ai-shell config show federation

# Output:
# federation:
#   strategy: auto           # auto, parallel, sequential
#   timeout: 30000           # 30 seconds
#   maxConcurrent: 4         # parallel queries
#   cache:
#     enabled: true
#     ttl: 300               # 5 minutes
#   optimization:
#     pushdown: true         # push filters to source
#     autoIndex: true        # suggest indexes
#   dataTransfer:
#     maxSize: 100MB         # max transfer per query
#     compression: true      # compress large results

# Configure federation strategy
ai-shell config set federation.strategy parallel

# Set timeout for federated queries
ai-shell config set federation.timeout 60000  # 60 seconds

# Enable/disable optimization features
ai-shell config set federation.optimization.pushdown true
ai-shell config set federation.optimization.autoIndex true

# Set data transfer limits
ai-shell config set federation.dataTransfer.maxSize 50MB

# Per-database connection tuning
ai-shell connection tune pg-ecommerce \
  --pool-size 20 \
  --timeout 10000

# Export federation config
ai-shell config export federation --file federation-config.yaml
```

---

## Common Use Cases

### Use Case 1: Customer 360 View

**Scenario:** Combine customer data scattered across multiple databases.

```bash
# Customer data spread across systems:
# - PostgreSQL: User accounts, orders
# - MongoDB: Product preferences, browsing history
# - Redis: Active sessions, cart data

ai-shell query "
  create comprehensive customer profile for user_id 12345:
  - basic info from postgres users table
  - order history from postgres orders table
  - preferences from mongodb user_preferences collection
  - browsing history from mongodb events collection
  - active session from redis
  - cart contents from redis
"

# Results in unified customer view:
# Customer Profile (ID: 12345)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Basic Info (PostgreSQL):
#   Name: John Doe
#   Email: john@example.com
#   Member Since: 2024-03-15
#   Tier: Premium
#
# Order History (PostgreSQL):
#   Total Orders: 23
#   Lifetime Value: $3,452
#   Last Order: 2025-10-20
#
# Preferences (MongoDB):
#   Favorite Categories: Electronics, Books
#   Communication: Email, SMS
#   Language: English
#
# Activity (MongoDB):
#   Last 30 Days: 47 page views
#   Most Viewed: Laptops
#
# Current Session (Redis):
#   Active: Yes
#   Started: 25 minutes ago
#   Cart Items: 2 ($234.00)

# Save as federated view for reuse
ai-shell view create customer_profile "..."
```

---

### Use Case 2: Real-Time Analytics Dashboard

**Scenario:** Power analytics dashboard with data from multiple sources.

```bash
# Dashboard requires:
# - PostgreSQL: Historical sales data
# - MongoDB: Recent events (high-volume)
# - Redis: Real-time metrics

ai-shell query "
  show business metrics:
  - total revenue (sum from postgres orders)
  - daily active users (count from redis active_users)
  - conversion rate (events from mongodb)
  - average order value (from postgres)
  - page views (from mongodb events)
  all for today
" --cache --ttl 60

# Enable auto-refresh
ai-shell dashboard create business-metrics \
  --query "..." \
  --refresh 60  # every 60 seconds

# Optimize for dashboard performance
ai-shell optimize-for dashboard business-metrics

# AI-Shell creates:
# - Materialized view for postgres aggregations
# - Index on mongodb timestamp field
# - Redis cache layer for final results
#
# Performance improvement:
# Before: 3,247ms per query
# After: 89ms per query (36x faster)
```

---

### Use Case 3: Data Migration Validation

**Scenario:** Validate data migration from MySQL to PostgreSQL.

```bash
# Connect to both old and new databases
ai-shell connect mysql://old-db:3306/app --name mysql-old
ai-shell connect postgres://new-db:5432/app --name postgres-new

# Compare record counts
ai-shell query "
  compare:
  - count from mysql-old.users
  - count from postgres-new.users
"

# Find missing records
ai-shell query "
  find user_ids in mysql-old.users
  that don't exist in postgres-new.users
"

# Validate data integrity
ai-shell query "
  compare sample of 1000 random records
  from mysql-old.users and postgres-new.users
  checking all fields match
"

# Generate migration validation report
ai-shell migrate-validate \
  --source mysql-old \
  --target postgres-new \
  --report validation-report.html

# Output:
# ✓ Record count: 1,247,893 (match)
# ✓ Primary keys: all accounted for
# ⚠️ Data differences: 23 records (0.002%)
#   - Timestamp format differences: 12
#   - Decimal precision: 8
#   - Null vs empty string: 3
# ✓ Foreign keys: integrity maintained
# ✓ Indexes: all created
#
# Overall: 99.998% match
```

---

### Use Case 4: Microservices Data Aggregation

**Scenario:** Each microservice has its own database, need unified reporting.

```bash
# Services architecture:
# - User Service (PostgreSQL)
# - Order Service (PostgreSQL)
# - Product Service (MongoDB)
# - Inventory Service (MongoDB)
# - Cache Service (Redis)

ai-shell connections add-group microservices \
  user-db postgres://... \
  order-db postgres://... \
  product-db mongodb://... \
  inventory-db mongodb://... \
  cache-db redis://...

# Query across microservices
ai-shell query --group microservices "
  generate daily report:
  - new users from user-db
  - orders from order-db
  - top products from product-db
  - inventory levels from inventory-db
  - cache hit rate from cache-db
"

# Create scheduled report
ai-shell report create daily-microservices \
  --query "..." \
  --format pdf \
  --email team@example.com \
  --schedule "0 9 * * *"  # daily at 9am
```

---

### Use Case 5: Hybrid Cloud Data Access

**Scenario:** Data split between on-premise and cloud databases.

```bash
# Mixed environment:
# - On-premise: Legacy Oracle database
# - Cloud: PostgreSQL on AWS RDS
# - Cloud: MongoDB Atlas

ai-shell connect oracle://on-prem:1521/prod --name oracle-legacy
ai-shell connect postgres://rds.aws.com:5432/app --name postgres-cloud
ai-shell connect mongodb+srv://atlas.mongodb.net/app --name mongo-cloud

# Query across hybrid infrastructure
ai-shell query "
  join:
  - customer master data from oracle-legacy
  - recent orders from postgres-cloud
  - product catalog from mongo-cloud
"

# Monitor cross-location performance
ai-shell monitor federation --show-latency

# Output:
# 📊 Federation Performance (Hybrid Cloud)
#
# oracle-legacy (on-premise):
#   Latency: 12ms
#   Throughput: 2,300 queries/sec
#
# postgres-cloud (AWS us-east-1):
#   Latency: 45ms
#   Throughput: 5,400 queries/sec
#
# mongo-cloud (Atlas us-east-1):
#   Latency: 38ms
#   Throughput: 3,800 queries/sec
#
# Recommendation:
# ⚡ Co-locate postgres-cloud and mongo-cloud in same region
# 💾 Cache oracle-legacy queries (rarely changes)
# 🔄 Consider read replica of oracle-legacy in cloud

# Apply recommendations
ai-shell optimize hybrid-federation --apply-recommendations
```

---

## Troubleshooting Tips

### Issue 1: Slow Federated Queries

**Problem:** Cross-database queries are taking too long.

**Solutions:**
```bash
# Analyze performance bottleneck
ai-shell query "your query" --profile

# Output shows:
# Database fetch times, data transfer, join time, etc.

# Apply specific optimizations:

# 1. Push filters to source databases
ai-shell query "..." --optimize pushdown

# 2. Reduce data transfer
ai-shell query "..." --select "only needed columns"

# 3. Use parallel execution
ai-shell config set federation.strategy parallel

# 4. Enable caching
ai-shell query "..." --cache --ttl 300

# 5. Add indexes to source databases
ai-shell optimize federated-query --add-indexes
```

---

### Issue 2: Connection Timeouts

**Problem:** Federated queries timeout before completing.

**Solutions:**
```bash
# Increase timeout
ai-shell config set federation.timeout 90000  # 90 seconds

# Increase per-database timeouts
ai-shell connection tune pg-ecommerce --timeout 30000

# Use async execution for very long queries
ai-shell query "..." --async

# Check query status
ai-shell query status <query-id>

# Retrieve results when ready
ai-shell query results <query-id>
```

---

### Issue 3: Data Type Mismatches

**Problem:** Type conversion errors in cross-database joins.

**Solutions:**
```bash
# View type conversion details
ai-shell query "..." --show-conversions

# Force specific type conversion
ai-shell query "
  join postgres.users (id as string)
  with mongodb.profiles (user_id as string)
"

# Configure default type mappings
ai-shell config set federation.typeMapping postgres.numeric mongodb.NumberDecimal

# Handle null vs empty string
ai-shell config set federation.nullHandling coalesce
```

---

### Issue 4: Memory Issues with Large Results

**Problem:** Out of memory errors on large federated queries.

**Solutions:**
```bash
# Use streaming for large results
ai-shell query "..." --stream

# Limit result size
ai-shell query "... limit 10000"

# Use pagination
ai-shell query "... offset 0 limit 1000"
ai-shell query "... offset 1000 limit 1000"

# Configure memory limits
ai-shell config set federation.maxMemory 512MB

# Export large results directly to file
ai-shell query "..." --export large-results.csv
```

---

### Issue 5: Authentication Issues Across Databases

**Problem:** Connection failures to one or more databases.

**Solutions:**
```bash
# Test each connection individually
ai-shell connection test pg-ecommerce
ai-shell connection test mongo-products

# Update credentials
ai-shell connection update pg-ecommerce --password new-password

# Use connection pooling to avoid auth overhead
ai-shell connection tune pg-ecommerce --pool-min 5 --pool-max 20

# Check SSL/TLS requirements
ai-shell connection update mongo-products --ssl true --ssl-ca /path/to/ca.pem

# Use vault for secure credential storage
ai-shell vault add pg-ecommerce --encrypt
```

---

## Best Practices

### 1. Design for Federation

```bash
# Use consistent naming across databases
# Good: user_id (postgres), user_id (mongodb), user:id (redis)
# Bad: id (postgres), userId (mongodb), user-key (redis)

# Define federated views for common queries
ai-shell view create user_summary "..." --optimize

# Document cross-database relationships
ai-shell relationships document \
  postgres.users.id → mongodb.profiles.user_id
```

### 2. Optimize Data Transfer

```bash
# Always select specific columns, not SELECT *
ai-shell query "select id, name from postgres.users" # Good
ai-shell query "select * from postgres.users"        # Bad

# Apply filters at source, not after fetching
ai-shell query "from postgres.users where active=true" # Good
ai-shell query "from postgres.users" # then filter     # Bad

# Use aggregation pushdown
ai-shell config set federation.optimization.pushdown true
```

### 3. Monitor Federation Performance

```bash
# Regular performance monitoring
ai-shell monitor federation --report daily

# Set up alerts for slow queries
ai-shell alerts add federation-slow \
  --condition "query_time > 5000ms" \
  --action notify

# Track data transfer volume
ai-shell monitor data-transfer --alert-threshold 1GB/hour
```

### 4. Cache Strategically

```bash
# Cache stable, frequently-accessed data
ai-shell query "from oracle-legacy" --cache --ttl 3600

# Don't cache frequently-changing data
ai-shell query "from redis sessions" --no-cache

# Use different TTLs for different data types
# Reference data: 1 hour
# Aggregated reports: 5 minutes
# Real-time data: no cache
```

### 5. Handle Failures Gracefully

```bash
# Use fallback strategies
ai-shell query "..." --fallback "alternative-query" --on-timeout

# Set reasonable timeouts
ai-shell config set federation.timeout 30000  # 30s

# Implement retry logic
ai-shell config set federation.retries 3
ai-shell config set federation.retryDelay 1000
```

### 6. Secure Cross-Database Access

```bash
# Use principle of least privilege
# Grant only necessary permissions to each database

# Encrypt credentials
ai-shell vault add-all --encrypt

# Use read-only connections where possible
ai-shell connect postgres://readonly@db:5432/app --readonly

# Audit federation queries
ai-shell config set federation.audit true
ai-shell audit-log show federation --last 24h
```

---

## Next Steps

### Master Related Features

1. **Query Optimization**
   - Optimize federated query performance
   - [Tutorial: Query Optimization](./query-optimization.md)

2. **Natural Language Queries**
   - Use natural language for cross-database queries
   - [Tutorial: Natural Language Queries](./natural-language-queries.md)

3. **Performance Monitoring**
   - Monitor federation performance
   - [Tutorial: Performance Monitoring](./performance-monitoring.md)

### Practice Exercises

1. **Exercise 1: Basic Federation**
   - Connect 2 different database types
   - Query data from each separately
   - Perform simple cross-database query

2. **Exercise 2: Cross-Database Joins**
   - Join tables from different databases
   - Handle different data types
   - Optimize join performance

3. **Exercise 3: Aggregations**
   - Aggregate data from multiple sources
   - Compare aggregation strategies
   - Measure performance differences

4. **Exercise 4: Federated Views**
   - Create federated view spanning 3+ databases
   - Query the view with various filters
   - Monitor view performance

5. **Exercise 5: Production Scenario**
   - Design federation strategy for your architecture
   - Implement with caching and optimization
   - Set up monitoring and alerts

### Additional Resources

- **Documentation**: [Federation guide](https://docs.ai-shell.dev/federation)
- **Architecture**: [Federation architecture](../ARCHITECTURE.md#federation)
- **API Reference**: [Federation API](../api/federation.md)
- **Examples**: [Federation examples](../examples/federation)

---

## Summary

You've learned how to:
- Connect and manage multiple databases simultaneously
- Query across different database types in natural language
- Perform cross-database joins and aggregations
- Optimize federated query performance
- Handle data type conversions automatically
- Apply best practices for multi-database architectures

Database federation with AI-Shell eliminates the complexity of working with multiple databases, enabling you to query across your entire data infrastructure as if it were a single database.

**Key Takeaway:** Start simple with 2 databases, master the basics, then expand to more complex federation scenarios. Always optimize for data transfer and use caching strategically.

---

**Related Tutorials:**
- [Natural Language Queries](./natural-language-queries.md)
- [Query Optimization](./query-optimization.md)
- [Performance Monitoring](./performance-monitoring.md)

**Need Help?** [Visit our documentation](https://docs.ai-shell.dev) or [join the community](https://github.com/your-org/ai-shell/discussions)
