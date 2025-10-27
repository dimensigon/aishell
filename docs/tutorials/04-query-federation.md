# Query Federation Tutorial: Join PostgreSQL and MongoDB in One Query

## Real-World Scenario

**Problem**: Your user data is in PostgreSQL, but order history is in MongoDB, product analytics in Elasticsearch, and sessions in Redis. You need to join data across all four databases for a customer 360 dashboard. Writing separate queries and merging results manually is taking hours.

**Solution**: AI-Shell's Query Federation lets you query across multiple databases using natural language, handling all the complexity behind the scenes.

---

## Table of Contents

1. [Setup](#setup)
2. [Basic Federation](#basic-federation)
3. [Real-World Example](#real-world-example)
4. [Advanced Patterns](#advanced-patterns)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Setup

### Connect Multiple Databases

```bash
# Add your databases
aishell connect postgres://user:pass@localhost:5432/users --name users-db
aishell connect mongodb://localhost:27017/orders --name orders-db
aishell connect elasticsearch://localhost:9200/analytics --name analytics-db
aishell connect redis://localhost:6379/0 --name sessions-db
```

**Connected Databases:**

```
✅ Connected Databases
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. users-db (PostgreSQL 14.2)
   - Tables: users, profiles, addresses
   - Rows: 3.2M users

2. orders-db (MongoDB 6.0)
   - Collections: orders, payments, reviews
   - Documents: 12.4M orders

3. analytics-db (Elasticsearch 8.5)
   - Indices: page_views, events, sessions
   - Documents: 456M events

4. sessions-db (Redis 7.0)
   - Keys: 89K active sessions
   - TTL: 30 minutes

🔗 Federation Mode: ACTIVE
   All databases available for cross-database queries
```

---

## Basic Federation

### Step 1: Simple Cross-Database Query

```bash
# Natural language query across databases
aishell query "Show me users from PostgreSQL who made purchases in MongoDB last week"
```

**AI Translation:**

```
🤖 AI Query Translator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyzing query...
  ✓ Detected 2 data sources
  ✓ Identified join condition (user_id)
  ✓ Temporal filter (last week)

Execution Plan:

┌─────────────────────────────────────────────────────┐
│ Step 1: Query PostgreSQL (users-db)                │
│   SELECT id, email, created_at FROM users           │
│   Est. rows: 3,214,567                              │
│                                                     │
│ Step 2: Query MongoDB (orders-db)                  │
│   db.orders.find({                                  │
│     created_at: {$gte: ISODate("2025-10-20")}      │
│   })                                                │
│   Est. documents: 234,567                           │
│                                                     │
│ Step 3: Join in memory                             │
│   JOIN ON users.id = orders.user_id                │
│   Est. result: 145,234 rows                         │
│                                                     │
│ Step 4: Return results                             │
│   Format: JSON                                      │
└─────────────────────────────────────────────────────┘

Optimization:
  ✓ Using indexes on both sides
  ✓ Filtering before join
  ✓ Streaming results (no memory overflow)

Estimated time: 2.3 seconds
Proceed? (Y/n): Y
```

**Results:**

```
📊 Federated Query Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────┬──────────────────────────┬──────────┬──────────────┐
│ user_id  │ email                    │ orders   │ total_spent  │
├──────────┼──────────────────────────┼──────────┼──────────────┤
│ 12345    │ john@example.com         │ 3        │ $234.56      │
│ 12346    │ jane@example.com         │ 5        │ $567.89      │
│ 12347    │ bob@example.com          │ 2        │ $123.45      │
│ ...      │ ...                      │ ...      │ ...          │
└──────────┴──────────────────────────┴──────────┴──────────────┘

Results: 145,234 rows
Execution time: 2.1 seconds
Data sources: PostgreSQL, MongoDB

💡 Export options:
   aishell export last --format csv > results.csv
   aishell export last --format json > results.json
```

### Step 2: Three-Way Join

```bash
# Join across three databases
aishell query "
  Show me active users (Redis sessions)
  with their profile data (PostgreSQL)
  and recent page views (Elasticsearch)
"
```

**Execution Plan:**

```
🔗 Three-Way Federation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Data Flow:

    ┌──────────┐
    │  Redis   │ (89K active sessions)
    │ sessions │
    └────┬─────┘
         │ user_id
         ▼
    ┌──────────┐
    │PostgreSQL│ (3.2M users)
    │  users   │
    └────┬─────┘
         │ user_id
         ▼
    ┌──────────┐
    │  Elastic │ (456M events)
    │pageviews │
    └──────────┘

Strategy: Start with smallest dataset (sessions)

Step 1: Get active sessions from Redis ........... 0.3s
  → 89,234 sessions

Step 2: Fetch user profiles from PostgreSQL ...... 1.2s
  → 89,234 users (batch fetch, 10K per query)

Step 3: Query page views from Elasticsearch ....... 2.8s
  → 234,567 page views (filtered by user_ids)

Step 4: Merge and format .......................... 0.4s

Total time: 4.7 seconds
Memory usage: 450 MB (within limits)

Executing...

[■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■] 100%

✅ Complete!
```

---

## Real-World Example: Customer 360 Dashboard

### Scenario

Build a complete customer profile by joining data from 4 different databases.

### Complex Query

```bash
aishell query "
  Give me a complete profile for user john@example.com including:
  - Basic info from PostgreSQL users table
  - Order history from MongoDB orders collection
  - Page view analytics from Elasticsearch
  - Current session data from Redis
  - Product recommendations from our ML service
"
```

**AI Analysis:**

```
🎯 Customer 360 Query Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query Complexity: HIGH
- 5 data sources
- 4 database types
- 1 external API
- Multiple join conditions

Data Sources:
✓ PostgreSQL: users, profiles, addresses
✓ MongoDB: orders, payments, reviews
✓ Elasticsearch: page_views, search_history
✓ Redis: active_session, cart_items
✓ External API: ML recommendations service

Execution Strategy:

Phase 1: Fetch Core Data (Parallel)
  ├─ PostgreSQL: User basic info [0.2s]
  ├─ MongoDB: Order history [0.8s]
  └─ Elasticsearch: Analytics [1.2s]

Phase 2: Fetch Session Data
  └─ Redis: Current session [0.1s]

Phase 3: External Enrichment
  └─ ML API: Recommendations [2.5s]

Phase 4: Merge & Format
  └─ Combine all data [0.3s]

Total estimated time: 5.1 seconds
```

**Results:**

```
👤 Customer 360 Profile: john@example.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Basic Information (PostgreSQL)
──────────────────────────────────────────────────────
User ID: 12345
Email: john@example.com
Name: John Doe
Member since: 2023-03-15
Account status: Active
Loyalty tier: Gold
Lifetime value: $2,345.67

📍 Addresses (PostgreSQL)
──────────────────────────────────────────────────────
Primary: 123 Main St, San Francisco, CA 94102
Billing: Same as primary
Shipping: 456 Work Ave, San Francisco, CA 94103

🛍️  Order History (MongoDB)
──────────────────────────────────────────────────────
Total orders: 27
Total spent: $2,345.67
Average order: $86.88
Last order: 2025-10-25 (2 days ago)

Recent Orders:
1. Order #ORD-8834 - $124.99 - Delivered ✓
   Items: Wireless Mouse, USB-C Cable
   Date: 2025-10-25

2. Order #ORD-8723 - $89.99 - In Transit 🚚
   Items: Laptop Stand
   Date: 2025-10-23

3. Order #ORD-8456 - $234.99 - Delivered ✓
   Items: Mechanical Keyboard
   Date: 2025-10-15

⭐ Reviews (MongoDB)
──────────────────────────────────────────────────────
Total reviews: 12
Average rating: 4.6/5.0
Helpful votes: 234

📊 Behavior Analytics (Elasticsearch)
──────────────────────────────────────────────────────
Page views (30 days): 342
Sessions (30 days): 45
Avg session duration: 8m 34s
Bounce rate: 23%

Top viewed categories:
1. Electronics (45%)
2. Home & Garden (28%)
3. Books (18%)

Search history (recent):
- "wireless mouse ergonomic"
- "standing desk converter"
- "mechanical keyboard quiet"

🔴 Current Session (Redis)
──────────────────────────────────────────────────────
Status: Active
Session started: 12 minutes ago
Current page: /products/monitors
Session ID: sess_abc123xyz

🛒 Cart (Redis):
Items: 2
Total: $456.98
  1. 27" 4K Monitor - $399.99
  2. HDMI Cable - $56.99

🤖 AI Recommendations (ML Service)
──────────────────────────────────────────────────────
Based on browsing and purchase history:

1. Monitor Arm Mount - $89.99 (92% match)
   "Customers who bought monitors also bought this"

2. Webcam HD 1080p - $79.99 (87% match)
   "Complete your home office setup"

3. Noise Cancelling Headphones - $199.99 (85% match)
   "Perfect for your work-from-home setup"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query executed in 4.8 seconds
Data sources: 5 (PostgreSQL, MongoDB, Elasticsearch, Redis, ML API)
Confidence: 100%

Export this profile:
  aishell export last --format pdf > customer-profile.pdf
```

---

## Advanced Patterns

### Pattern 1: Aggregations Across Databases

```bash
# Aggregate data from multiple sources
aishell query "
  Show total revenue by region:
  - Users and addresses from PostgreSQL
  - Orders and payments from MongoDB
  Group by region and calculate sum
"
```

**Execution:**

```
📊 Cross-Database Aggregation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategy: Pushdown aggregation where possible

Step 1: Pre-aggregate in MongoDB
  db.orders.aggregate([
    {$group: {
      _id: "$user_id",
      total_revenue: {$sum: "$total"}
    }}
  ])
  Result: 234K users with order totals (5.2s)

Step 2: Join with PostgreSQL
  SELECT region, SUM(mongo.total_revenue)
  FROM users
  JOIN mongo_results ON users.id = mongo.user_id
  GROUP BY region
  Result: 50 regions (1.3s)

Results:
┌──────────────┬──────────────┬────────────┬──────────┐
│ Region       │ Customers    │ Orders     │ Revenue  │
├──────────────┼──────────────┼────────────┼──────────┤
│ West Coast   │ 45,234       │ 234,567    │ $2.3M    │
│ East Coast   │ 38,123       │ 198,234    │ $1.9M    │
│ Midwest      │ 28,456       │ 145,678    │ $1.4M    │
│ South        │ 32,789       │ 167,890    │ $1.6M    │
│ International│ 12,345       │ 67,891     │ $678K    │
└──────────────┴──────────────┴────────────┴──────────┘

Total: $7.9M across all regions
Execution time: 6.5s
```

### Pattern 2: Real-Time Data Enrichment

```bash
# Enrich real-time events with historical data
aishell stream "
  Watch for new orders in MongoDB
  and enrich with user data from PostgreSQL
  and product analytics from Elasticsearch
" --output enriched-orders.jsonl
```

**Streaming Output:**

```
🔴 Live Stream: Enriched Orders
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[14:23:45] New Order Detected
{
  "order_id": "ORD-9012",
  "user_id": 12345,

  // From MongoDB
  "items": [
    {"product_id": "PROD-567", "quantity": 1, "price": 99.99}
  ],
  "total": 99.99,
  "created_at": "2025-10-27T14:23:45Z",

  // Enriched from PostgreSQL
  "user": {
    "email": "john@example.com",
    "name": "John Doe",
    "loyalty_tier": "Gold",
    "lifetime_value": 2445.66
  },

  // Enriched from Elasticsearch
  "analytics": {
    "viewed_product": "2025-10-27T14:18:32Z",
    "time_to_purchase": "5m 13s",
    "referrer": "google_search",
    "previous_searches": ["wireless headphones", "noise cancelling"]
  },

  // AI Enrichment
  "predictions": {
    "churn_risk": "low",
    "upsell_opportunity": "high",
    "recommended_products": ["PROD-890", "PROD-234"]
  }
}

[14:24:12] New Order Detected
...

Events processed: 45
Enrichment success rate: 100%
Avg enrichment time: 123ms
```

### Pattern 3: Federated Search

```bash
# Search across all databases
aishell search "wireless mouse" --all-databases
```

**Search Results:**

```
🔍 Federated Search: "wireless mouse"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Results from PostgreSQL (products table):
┌─────────────────────────────────────────────────────┐
│ 1. Logitech MX Master 3 Wireless Mouse             │
│    Price: $99.99 | Stock: 45 | Rating: 4.8/5       │
│                                                     │
│ 2. Razer DeathAdder V2 Pro Wireless                │
│    Price: $129.99 | Stock: 23 | Rating: 4.6/5      │
└─────────────────────────────────────────────────────┘
Found: 234 products

Results from MongoDB (orders.items):
┌─────────────────────────────────────────────────────┐
│ Most purchased wireless mice (last 30 days):       │
│ 1. Logitech MX Master 3 - 2,345 orders             │
│ 2. Apple Magic Mouse - 1,234 orders                │
│ 3. Razer DeathAdder - 892 orders                   │
└─────────────────────────────────────────────────────┘

Results from Elasticsearch (search_logs):
┌─────────────────────────────────────────────────────┐
│ Related searches:                                   │
│ - "wireless mouse ergonomic" (12,345 searches)     │
│ - "wireless mouse gaming" (8,901 searches)         │
│ - "wireless mouse for Mac" (5,678 searches)        │
└─────────────────────────────────────────────────────┘

Results from Elasticsearch (page_views):
┌─────────────────────────────────────────────────────┐
│ Most viewed wireless mice:                          │
│ 1. Logitech MX Master 3 - 45,678 views             │
│ 2. Apple Magic Mouse - 34,567 views                │
└─────────────────────────────────────────────────────┘

🤖 AI Insights:
- "Logitech MX Master 3" is the clear winner
- High search volume for ergonomic options
- Gaming mice also popular
- Consider bundling with mouse pads

Total search time: 1.2 seconds across 4 databases
```

### Pattern 4: Data Synchronization

```bash
# Sync data between databases
aishell sync users-db.users -> orders-db.users_cache \
  --mode incremental \
  --schedule "*/15 * * * *"
```

**Sync Configuration:**

```yaml
sync_job:
  name: "Users to Orders Sync"
  source:
    database: users-db (PostgreSQL)
    table: users
    columns: [id, email, name, created_at, updated_at]

  destination:
    database: orders-db (MongoDB)
    collection: users_cache

  mode: incremental
  sync_key: updated_at
  schedule: "*/15 * * * *"  # Every 15 minutes

  transforms:
    - rename: {id: user_id}
    - add_field: {synced_at: NOW()}
    - exclude_fields: [password_hash, ssn]

  conflict_resolution: source_wins

  monitoring:
    alert_on_failure: true
    track_metrics: true
```

### Pattern 5: Virtual Tables

Create virtual tables that join multiple databases:

```bash
# Define virtual table
aishell create-view customer_summary << EOF
SELECT
  u.id,
  u.email,
  u.name,
  COUNT(o.id) as total_orders,
  SUM(o.total) as lifetime_value,
  MAX(o.created_at) as last_order_date,
  es.page_views_30d
FROM
  [users-db].users u
  LEFT JOIN [orders-db].orders o ON u.id = o.user_id
  LEFT JOIN [analytics-db].user_analytics es ON u.id = es.user_id
GROUP BY u.id, es.page_views_30d
EOF
```

**Usage:**

```bash
# Query the virtual view
aishell query "SELECT * FROM customer_summary WHERE total_orders > 10"

# Virtual table behaves like a regular table
aishell query "
  SELECT
    CASE
      WHEN total_orders > 50 THEN 'VIP'
      WHEN total_orders > 20 THEN 'Gold'
      WHEN total_orders > 5 THEN 'Silver'
      ELSE 'Bronze'
    END as tier,
    COUNT(*) as customer_count,
    AVG(lifetime_value) as avg_ltv
  FROM customer_summary
  GROUP BY tier
"
```

---

## Best Practices

### 1. Start with Smaller Dataset

```bash
# Query smallest dataset first for efficiency
# ✓ Good: Start with Redis (89K sessions)
aishell query "active sessions -> user data -> order history"

# ✗ Bad: Start with Elasticsearch (456M events)
aishell query "all events -> user data -> sessions"
```

### 2. Use Indexes

```bash
# Check federated query plan
aishell explain "your complex federated query"

# AI will suggest indexes across all databases
💡 Add these indexes for better performance:
  PostgreSQL: CREATE INDEX idx_users_email ON users(email);
  MongoDB: db.orders.createIndex({user_id: 1, created_at: -1});
```

### 3. Cache Federated Results

```bash
# Enable result caching for repeated queries
aishell cache enable --ttl 300  # 5 minutes

# Federated queries are automatically cached
aishell query "complex federated query"  # Takes 5s
aishell query "same query"                # Takes 0.1s (cached!)
```

### 4. Monitor Performance

```bash
# Track federated query performance
aishell monitor federation --dashboard

# Set performance budgets
aishell config set federation.max_query_time 10s
aishell config set federation.max_memory 1GB
```

### 5. Handle Failures Gracefully

```bash
# Configure fallback behavior
aishell config set federation.on_source_failure continue

# AI will return partial results if one database fails
⚠️  Warning: MongoDB connection failed
    Returning partial results from PostgreSQL and Elasticsearch
    Missing: Order history data
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Cartesian Product Explosion

**Problem:** Joining without proper filters creates huge result set

**Solution:**

```bash
# AI detects potential cartesian product
⚠️  Warning: Potential cartesian product detected
    users (3.2M) × orders (12.4M) = 39.7 trillion rows!

    Missing join condition?
    Suggestion: Add "ON users.id = orders.user_id"

# AI can auto-fix
aishell query "..." --auto-fix
```

### Pitfall 2: Data Type Mismatches

**Problem:** PostgreSQL INT vs MongoDB String

**Solution:**

```bash
# AI handles type conversion automatically
ℹ️  Type mismatch detected:
    PostgreSQL users.id (integer)
    MongoDB orders.user_id (string)

    Auto-converting: CAST(users.id AS TEXT)

# Or configure explicit mappings
aishell config set federation.type_mappings '
  users-db.users.id: string
'
```

### Pitfall 3: Network Latency

**Problem:** Federated queries slow due to network round-trips

**Solution:**

```bash
# Use batch fetching
aishell config set federation.batch_size 10000

# Enable parallel execution
aishell config set federation.parallel true

# Cache frequently joined data
aishell sync --cache users-db.users -> local-cache
```

---

## Troubleshooting

### Issue 1: "Query timeout on federated join"

```bash
# Increase timeout
aishell config set federation.timeout 60s

# Or use async execution
aishell query "..." --async --notify-on-complete
```

### Issue 2: "Out of memory during join"

```bash
# Use streaming join
aishell query "..." --streaming

# Or increase memory limit
aishell config set federation.max_memory 4GB
```

### Issue 3: "Data inconsistency across databases"

```bash
# Check data freshness
aishell validate-sync users-db orders-db

# Force sync before query
aishell query "..." --fresh-data
```

---

## Summary

**Key Takeaways:**

- ✅ Query across any combination of databases
- ✅ Natural language interface for complex joins
- ✅ Automatic optimization and caching
- ✅ Real-time data enrichment
- ✅ Virtual tables for common join patterns

**Next Steps:**

1. Try the [Query Cache Tutorial](./06-query-cache.md) for performance
2. Learn about [Schema Designer](./05-schema-designer.md) for data modeling
3. Explore [SQL Explainer](./08-sql-explainer.md) for understanding queries

**Real Results:**

> "Federation cut our data pipeline code from 2,000 lines to 5 queries. Customer 360 dashboards that took hours now take seconds." - Sarah Kim, Data Engineer

---

## Quick Commands Cheat Sheet

```bash
# Connect databases
aishell connect <url> --name <name>

# Simple federated query
aishell query "natural language query across databases"

# Explain execution plan
aishell explain "federated query"

# Search across all databases
aishell search "term" --all-databases

# Create virtual view
aishell create-view <name> <query>

# Sync databases
aishell sync source -> destination

# Monitor federation
aishell monitor federation
```

**Pro Tip:** Use virtual views for frequently joined data to simplify queries and improve performance! 🚀
