# AI-Shell Hands-On Tutorial - Part 2: NLP & Query Features

**Level:** Intermediate
**Duration:** 45-60 minutes
**Prerequisites:** Completion of Part 1, Active database connection

---

## Table of Contents
1. [Natural Language to SQL](#natural-language-to-sql)
2. [33 NLP Query Patterns](#33-nlp-query-patterns)
3. [Query Optimization](#query-optimization)
4. [Performance Monitoring](#performance-monitoring)
5. [Slow Query Detection](#slow-query-detection)
6. [Query Validation](#query-validation)
7. [Validation Checkpoints](#validation-checkpoints)
8. [Troubleshooting](#troubleshooting)

---

## 1. Natural Language to SQL

### Step 1.1: Initialize NLP Engine

```python
from ai_shell import NLPQueryEngine

# Initialize NLP engine
nlp_engine = NLPQueryEngine(
    connector=connector,
    model="gpt-4",  # or "claude-3", "llama-2"
    enable_cache=True,
    cache_ttl=3600
)

# Test basic NLP query
natural_query = "Show me all users who signed up this month"
sql_result = await nlp_engine.translate(natural_query)

print(f"Natural: {natural_query}")
print(f"SQL: {sql_result.sql}")
print(f"Confidence: {sql_result.confidence}%")
```

**Expected Output:**
```
Natural: Show me all users who signed up this month
SQL: SELECT * FROM users WHERE EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE) AND EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
Confidence: 95%
```

### Step 1.2: Execute NLP Query

```python
# Translate and execute in one step
result = await nlp_engine.query(
    "Find the top 5 customers by total purchase amount"
)

print(f"Query executed successfully")
print(f"Rows returned: {len(result.rows)}")
print(f"Execution time: {result.execution_time}ms")

for i, row in enumerate(result.rows, 1):
    print(f"{i}. {row['customer_name']}: ${row['total_amount']}")
```

**Expected Output:**
```
Query executed successfully
Rows returned: 5
Execution time: 45ms

1. John Smith: $15,230.50
2. Sarah Johnson: $12,890.25
3. Mike Davis: $11,450.00
4. Emily Brown: $10,225.75
5. David Wilson: $9,875.50
```

### Step 1.3: Multi-Table Queries

```python
# Complex query across multiple tables
natural_query = """
Show me the total sales by product category
for the last quarter, including the number of orders
"""

result = await nlp_engine.query(natural_query)

print(f"Generated SQL:")
print(result.sql)
print(f"\nResults:")

for row in result.rows:
    print(f"{row['category']}: ${row['total_sales']:,.2f} ({row['order_count']} orders)")
```

**Expected Output:**
```
Generated SQL:
SELECT
    c.name as category,
    SUM(oi.quantity * oi.price) as total_sales,
    COUNT(DISTINCT o.id) as order_count
FROM categories c
JOIN products p ON c.id = p.category_id
JOIN order_items oi ON p.id = oi.product_id
JOIN orders o ON oi.order_id = o.id
WHERE o.created_at >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL '3 months')
GROUP BY c.name
ORDER BY total_sales DESC

Results:
Electronics: $125,430.50 (342 orders)
Clothing: $89,250.75 (567 orders)
Home & Garden: $67,890.25 (234 orders)
```

---

## 2. 33 NLP Query Patterns

### Pattern 1: Simple Selection

```python
# Pattern: "Show/Get/Find [entity]"
queries = [
    "Show me all products",
    "Get all active users",
    "Find customers from New York"
]

for query in queries:
    result = await nlp_engine.query(query)
    print(f"Q: {query}")
    print(f"SQL: {result.sql}")
    print(f"Rows: {len(result.rows)}\n")
```

### Pattern 2: Filtering with Conditions

```python
# Pattern: "[entity] where [condition]"
queries = [
    "Users where age is greater than 25",
    "Products where price is less than 100",
    "Orders where status is pending"
]

for query in queries:
    result = await nlp_engine.query(query)
    print(f"Q: {query}")
    print(f"Rows: {len(result.rows)}")
```

### Pattern 3: Aggregation

```python
# Pattern: "Count/Sum/Average [entity]"
queries = [
    "Count all users",
    "Sum of all order totals",
    "Average product price",
    "Maximum salary in engineering department"
]

for query in queries:
    result = await nlp_engine.query(query)
    print(f"Q: {query}")
    print(f"Result: {result.rows[0]}")
```

**Expected Output:**
```
Q: Count all users
Result: {'count': 1250}

Q: Sum of all order totals
Result: {'sum': 458230.50}

Q: Average product price
Result: {'avg': 45.75}
```

### Pattern 4: Grouping

```python
# Pattern: "[aggregation] by [group]"
query = "Total sales by product category"
result = await nlp_engine.query(query)

print(f"SQL: {result.sql}\n")
for row in result.rows:
    print(f"{row['category']}: ${row['total_sales']:,.2f}")
```

### Pattern 5: Time-based Queries

```python
# Pattern: "[query] in/during [time period]"
queries = [
    "Orders created today",
    "Users who signed up this week",
    "Sales in the last 30 days",
    "Transactions between January and March 2024"
]

for query in queries:
    result = await nlp_engine.query(query)
    print(f"Q: {query}")
    print(f"Rows: {len(result.rows)}\n")
```

### Pattern 6: Sorting

```python
# Pattern: "[query] sorted/ordered by [field]"
queries = [
    "Products sorted by price descending",
    "Users ordered by registration date",
    "Top 10 sellers by revenue"
]

for query in queries:
    result = await nlp_engine.query(query)
    print(f"Q: {query}")
    print(f"First result: {result.rows[0]}\n")
```

### Pattern 7: Joins

```python
# Pattern: "[entity1] with their [entity2]"
query = "Show customers with their order history"
result = await nlp_engine.query(query)

print(f"Generated SQL:\n{result.sql}\n")
print(f"Results: {len(result.rows)} customer-order pairs")
```

### Pattern 8: Subqueries

```python
# Pattern: "[entity] that have/with [nested condition]"
query = "Products that have never been ordered"
result = await nlp_engine.query(query)

print(f"SQL: {result.sql}")
print(f"Found {len(result.rows)} products without orders")
```

### Pattern 9: Multiple Conditions

```python
# Pattern: "[query] where [condition1] and/or [condition2]"
query = "Users where age > 25 and city = 'New York' and status is active"
result = await nlp_engine.query(query)

print(f"SQL: {result.sql}")
print(f"Matching users: {len(result.rows)}")
```

### Pattern 10: Range Queries

```python
# Pattern: "[entity] between [value1] and [value2]"
queries = [
    "Products priced between 50 and 100",
    "Orders with amounts between 100 and 500",
    "Events scheduled between next Monday and Friday"
]

for query in queries:
    result = await nlp_engine.query(query)
    print(f"Q: {query}")
    print(f"Results: {len(result.rows)}\n")
```

### Pattern 11: Pattern Matching

```python
# Pattern: "[entity] containing/starting with/ending with [pattern]"
queries = [
    "Users with email ending in @gmail.com",
    "Products with name containing 'laptop'",
    "Companies starting with 'Tech'"
]

for query in queries:
    result = await nlp_engine.query(query)
    print(f"Q: {query}")
    print(f"SQL: {result.sql}")
    print(f"Matches: {len(result.rows)}\n")
```

### Pattern 12: Null Checking

```python
# Pattern: "[entity] with/without [field]"
queries = [
    "Users without phone numbers",
    "Orders with tracking numbers",
    "Products without images"
]

for query in queries:
    result = await nlp_engine.query(query)
    print(f"Q: {query}")
    print(f"Results: {len(result.rows)}\n")
```

### Pattern 13: Distinct Values

```python
# Pattern: "Unique/Distinct [field]"
queries = [
    "Unique cities from users",
    "Distinct product categories",
    "Different payment methods used"
]

for query in queries:
    result = await nlp_engine.query(query)
    print(f"Q: {query}")
    print(f"Unique values: {len(result.rows)}")
    print(f"Values: {[row[list(row.keys())[0]] for row in result.rows]}\n")
```

### Pattern 14: Top/Bottom N

```python
# Pattern: "Top/Bottom [N] [entity] by [criteria]"
queries = [
    "Top 5 products by sales",
    "Bottom 10 performers this quarter",
    "Top 3 customers by order count"
]

for query in queries:
    result = await nlp_engine.query(query)
    print(f"Q: {query}")
    for i, row in enumerate(result.rows, 1):
        print(f"  {i}. {row}")
    print()
```

### Pattern 15: Percentage Calculations

```python
# Pattern: "Percentage of [entity] that [condition]"
query = "Percentage of orders that were delivered on time"
result = await nlp_engine.query(query)

print(f"SQL: {result.sql}")
print(f"On-time delivery rate: {result.rows[0]['percentage']:.1f}%")
```

### Pattern 16-33: Advanced Patterns

```python
# Pattern 16: Window Functions
query = "Running total of sales by date"

# Pattern 17: Pivot/Unpivot
query = "Sales by month for each product category"

# Pattern 18: Recursive Queries
query = "Employee hierarchy starting from CEO"

# Pattern 19: Array Operations
query = "Products with tags containing 'electronics' or 'gadgets'"

# Pattern 20: JSON Queries
query = "Users with preferences.notifications.email set to true"

# Pattern 21: Full-Text Search
query = "Products matching 'wireless bluetooth headphones'"

# Pattern 22: Geospatial Queries
query = "Stores within 10 miles of Times Square"

# Pattern 23: Date Math
query = "Users who haven't logged in for 30 days"

# Pattern 24: Statistical Functions
query = "Standard deviation of order amounts by category"

# Pattern 25: Conditional Aggregation
query = "Count of orders by status (pending, completed, cancelled)"

# Pattern 26: Self-Joins
query = "Employees and their managers"

# Pattern 27: Cross Joins
query = "All possible product combinations for bundles"

# Pattern 28: Set Operations (UNION/INTERSECT/EXCEPT)
query = "Users who are both customers and vendors"

# Pattern 29: Correlation
query = "Products frequently bought together"

# Pattern 30: Percentile
query = "90th percentile of order amounts"

# Pattern 31: Moving Average
query = "7-day moving average of daily sales"

# Pattern 32: Cohort Analysis
query = "User retention by signup month"

# Pattern 33: Funnel Analysis
query = "Conversion rate from view to purchase"

# Execute all advanced patterns
advanced_patterns = {
    "Window Functions": "Running total of sales by date",
    "Pivot": "Sales by month for each product category",
    "Recursive": "Employee hierarchy starting from CEO",
    "Arrays": "Products with tags containing 'electronics'",
    "JSON": "Users with email notifications enabled",
    "Full-Text": "Products matching 'wireless bluetooth'",
    "Geospatial": "Stores near Times Square",
    "Date Math": "Inactive users in last 30 days",
    "Statistics": "Standard deviation of order amounts",
    "Conditional": "Order count by status"
}

print("=== Advanced Pattern Examples ===\n")

for pattern_name, query in advanced_patterns.items():
    result = await nlp_engine.query(query)
    print(f"{pattern_name}:")
    print(f"  Query: {query}")
    print(f"  SQL: {result.sql[:100]}...")
    print(f"  Rows: {len(result.rows)}\n")
```

**Expected Output:**
```
=== Advanced Pattern Examples ===

Window Functions:
  Query: Running total of sales by date
  SQL: SELECT date, SUM(amount) OVER (ORDER BY date) as running_total FROM sales...
  Rows: 365

Pivot:
  Query: Sales by month for each product category
  SQL: SELECT category, SUM(CASE WHEN month = 1 THEN amount END) as jan, SUM(CASE WHEN month = 2...
  Rows: 5

[...additional patterns...]
```

---

## 3. Query Optimization

### Step 3.1: Automatic Query Optimization

```python
from ai_shell import QueryOptimizer

# Initialize optimizer
optimizer = QueryOptimizer(connector)

# Original query
original_query = """
SELECT u.name, o.total, p.name as product
FROM users u, orders o, products p
WHERE u.id = o.user_id AND o.product_id = p.id
AND o.created_at > '2024-01-01'
"""

# Optimize query
optimized = await optimizer.optimize(original_query)

print("Original Query:")
print(original_query)
print(f"\nOriginal Execution Time: {optimized.original_time}ms")

print("\nOptimized Query:")
print(optimized.query)
print(f"Optimized Execution Time: {optimized.optimized_time}ms")

print(f"\nImprovement: {optimized.improvement_percent}%")
print(f"Optimization Type: {optimized.optimization_type}")
```

**Expected Output:**
```
Original Query:
SELECT u.name, o.total, p.name as product
FROM users u, orders o, products p
WHERE u.id = o.user_id AND o.product_id = p.id
AND o.created_at > '2024-01-01'

Original Execution Time: 1250ms

Optimized Query:
SELECT u.name, o.total, p.name as product
FROM orders o
INNER JOIN users u ON u.id = o.user_id
INNER JOIN products p ON o.product_id = p.id
WHERE o.created_at > '2024-01-01'

Optimized Execution Time: 85ms

Improvement: 93.2%
Optimization Type: JOIN_CONVERSION
```

### Step 3.2: Nine Optimization Types

#### Type 1: Index Suggestion

```python
# Optimizer suggests missing indexes
result = await optimizer.analyze_and_suggest("""
    SELECT * FROM orders WHERE customer_id = 123 AND status = 'pending'
""")

print("Index Suggestions:")
for suggestion in result.index_suggestions:
    print(f"  - {suggestion.statement}")
    print(f"    Expected improvement: {suggestion.improvement}%")
```

**Expected Output:**
```
Index Suggestions:
  - CREATE INDEX idx_orders_customer_status ON orders(customer_id, status)
    Expected improvement: 85%
  - CREATE INDEX idx_orders_status ON orders(status)
    Expected improvement: 45%
```

#### Type 2: JOIN Optimization

```python
# Optimize JOIN order
query = """
SELECT o.*, u.name, p.title
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN products p ON o.product_id = p.id
JOIN categories c ON p.category_id = c.id
WHERE c.name = 'Electronics'
"""

optimized = await optimizer.optimize(query)
print(f"JOIN order optimized: {optimized.optimization_details}")
```

#### Type 3: Subquery to JOIN Conversion

```python
# Convert subquery to JOIN
query = """
SELECT * FROM users
WHERE id IN (
    SELECT user_id FROM orders WHERE total > 1000
)
"""

optimized = await optimizer.optimize(query)
print("Optimized:")
print(optimized.query)
```

**Expected Output:**
```
Optimized:
SELECT DISTINCT u.*
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.total > 1000
```

#### Type 4: SELECT * Elimination

```python
# Replace SELECT * with specific columns
query = "SELECT * FROM users WHERE status = 'active'"

optimized = await optimizer.optimize(query)
print("Optimized:")
print(optimized.query)
```

**Expected Output:**
```
Optimized:
SELECT id, name, email, status, created_at FROM users WHERE status = 'active'
```

#### Type 5: LIMIT Addition

```python
# Add LIMIT to unbounded queries
query = "SELECT * FROM logs ORDER BY created_at DESC"

optimized = await optimizer.optimize(query, add_limit=True)
print(optimized.query)
```

**Expected Output:**
```
SELECT * FROM logs ORDER BY created_at DESC LIMIT 1000
```

#### Type 6: Predicate Pushdown

```python
# Push WHERE clauses closer to tables
query = """
SELECT * FROM (
    SELECT * FROM orders
) o
WHERE o.status = 'completed'
"""

optimized = await optimizer.optimize(query)
print(optimized.query)
```

#### Type 7: Aggregation Optimization

```python
# Optimize aggregation queries
query = """
SELECT user_id, COUNT(*), AVG(total)
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 5
"""

optimized = await optimizer.optimize(query)
print(f"Optimization: {optimized.optimization_details}")
```

#### Type 8: Materialized View Suggestion

```python
# Suggest materialized views for expensive queries
query = """
SELECT
    p.category_id,
    COUNT(*) as order_count,
    SUM(oi.quantity * oi.price) as total_revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.id
GROUP BY p.category_id
"""

result = await optimizer.analyze_and_suggest(query)

if result.materialized_view_suggestion:
    print("Materialized View Suggestion:")
    print(result.materialized_view_suggestion.create_statement)
```

#### Type 9: Partition Pruning

```python
# Optimize queries on partitioned tables
query = """
SELECT * FROM sales
WHERE sale_date >= '2024-01-01' AND sale_date < '2024-02-01'
"""

optimized = await optimizer.optimize(query)
print(f"Partitions accessed: {optimized.partitions_scanned}")
print(f"Partitions pruned: {optimized.partitions_pruned}")
```

### Step 3.3: Batch Optimization

```python
# Optimize multiple queries at once
queries = [
    "SELECT * FROM users WHERE email LIKE '%@gmail.com'",
    "SELECT COUNT(*) FROM orders WHERE status IN ('pending', 'processing')",
    "SELECT p.name, SUM(oi.quantity) FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.name"
]

results = await optimizer.optimize_batch(queries)

for i, result in enumerate(results, 1):
    print(f"\nQuery {i}:")
    print(f"  Improvement: {result.improvement_percent}%")
    print(f"  Original time: {result.original_time}ms")
    print(f"  Optimized time: {result.optimized_time}ms")
```

---

## 4. Performance Monitoring

### Step 4.1: Query Performance Tracking

```python
from ai_shell import PerformanceMonitor

# Initialize monitor
monitor = PerformanceMonitor(connector)

# Enable monitoring
await monitor.start()

# Execute queries
for i in range(10):
    await executor.execute("SELECT * FROM users LIMIT 100")

# Get performance report
report = await monitor.get_report()

print("Performance Report:")
print(f"  Total queries: {report.total_queries}")
print(f"  Average execution time: {report.avg_execution_time}ms")
print(f"  Slowest query: {report.slowest_query_time}ms")
print(f"  Fastest query: {report.fastest_query_time}ms")
print(f"  Total time: {report.total_time}ms")
```

**Expected Output:**
```
Performance Report:
  Total queries: 10
  Average execution time: 23.5ms
  Slowest query: 45ms
  Fastest query: 12ms
  Total time: 235ms
```

### Step 4.2: Real-time Monitoring Dashboard

```python
# Start real-time monitoring
monitor = PerformanceMonitor(connector, realtime=True)

# Monitor queries in real-time
async def monitor_queries():
    async for metric in monitor.stream():
        print(f"[{metric.timestamp}] Query: {metric.query[:50]}...")
        print(f"  Time: {metric.execution_time}ms")
        print(f"  Rows: {metric.rows_returned}")
        print(f"  Cache hit: {metric.cache_hit}")
        print()

# Run monitoring
await monitor_queries()
```

### Step 4.3: Performance Metrics Collection

```python
# Collect detailed metrics
metrics = await monitor.collect_metrics(duration=60)  # 60 seconds

print("\n=== Performance Metrics (60s) ===\n")
print(f"Queries per second: {metrics.qps:.2f}")
print(f"Average latency: {metrics.avg_latency}ms")
print(f"P50 latency: {metrics.p50_latency}ms")
print(f"P95 latency: {metrics.p95_latency}ms")
print(f"P99 latency: {metrics.p99_latency}ms")
print(f"Cache hit rate: {metrics.cache_hit_rate}%")
print(f"Error rate: {metrics.error_rate}%")
```

**Expected Output:**
```
=== Performance Metrics (60s) ===

Queries per second: 45.3
Average latency: 28ms
P50 latency: 22ms
P95 latency: 67ms
P99 latency: 125ms
Cache hit rate: 78.5%
Error rate: 0.2%
```

### Step 4.4: Resource Usage Monitoring

```python
# Monitor database resource usage
resources = await monitor.get_resource_usage()

print("Resource Usage:")
print(f"  CPU: {resources.cpu_percent}%")
print(f"  Memory: {resources.memory_used_gb:.2f}GB / {resources.memory_total_gb:.2f}GB")
print(f"  Disk I/O: {resources.disk_io_mb_per_sec:.2f}MB/s")
print(f"  Network I/O: {resources.network_io_mb_per_sec:.2f}MB/s")
print(f"  Active connections: {resources.active_connections}")
print(f"  Locks: {resources.locks}")
```

---

## 5. Slow Query Detection

### Step 5.1: Automatic Slow Query Detection

```python
from ai_shell import SlowQueryDetector

# Initialize detector
detector = SlowQueryDetector(
    connector,
    threshold_ms=100,  # Queries slower than 100ms
    auto_log=True
)

# Enable detection
await detector.enable()

# Execute some queries
await executor.execute("SELECT * FROM large_table")  # Slow query

# Get detected slow queries
slow_queries = await detector.get_slow_queries()

print(f"\nDetected {len(slow_queries)} slow queries:\n")

for query in slow_queries:
    print(f"Query: {query.sql[:60]}...")
    print(f"  Execution time: {query.execution_time}ms")
    print(f"  Timestamp: {query.timestamp}")
    print(f"  Recommendation: {query.recommendation}")
    print()
```

**Expected Output:**
```
Detected 3 slow queries:

Query: SELECT * FROM large_table WHERE status = 'active' ORDER BY...
  Execution time: 1250ms
  Timestamp: 2024-10-11 14:23:45
  Recommendation: Add index on (status, created_at)

Query: SELECT COUNT(*) FROM orders o JOIN order_items oi ON o.id...
  Execution time: 850ms
  Timestamp: 2024-10-11 14:24:12
  Recommendation: Consider materialized view

Query: SELECT * FROM users WHERE email LIKE '%@gmail.com'...
  Execution time: 450ms
  Timestamp: 2024-10-11 14:25:03
  Recommendation: Avoid leading wildcard in LIKE clause
```

### Step 5.2: Slow Query Analysis

```python
# Analyze slow query
slow_query = slow_queries[0]

analysis = await detector.analyze(slow_query)

print("Slow Query Analysis:")
print(f"  Query: {analysis.query}")
print(f"  Execution time: {analysis.execution_time}ms")
print(f"\nExecution Plan:")
print(analysis.explain_plan)
print(f"\nBottlenecks:")
for bottleneck in analysis.bottlenecks:
    print(f"  - {bottleneck}")
print(f"\nSuggestions:")
for suggestion in analysis.suggestions:
    print(f"  - {suggestion}")
```

### Step 5.3: Slow Query Alerting

```python
# Set up alerts for slow queries
detector.set_alert_handler(
    threshold_ms=500,
    handler=lambda query: print(f"🚨 SLOW QUERY ALERT: {query.execution_time}ms")
)

# Configure email alerts (optional)
detector.configure_email_alerts(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    from_email="alerts@example.com",
    to_emails=["admin@example.com"],
    threshold_ms=1000
)
```

### Step 5.4: Slow Query Report

```python
# Generate slow query report
report = await detector.generate_report(
    period="7d",  # Last 7 days
    min_threshold_ms=100
)

print("\n=== Slow Query Report (7 days) ===\n")
print(f"Total slow queries: {report.total_count}")
print(f"Average execution time: {report.avg_execution_time}ms")
print(f"Slowest query: {report.slowest_query_time}ms")

print("\nTop 5 Slowest Queries:")
for i, query in enumerate(report.top_queries[:5], 1):
    print(f"{i}. {query.sql[:60]}...")
    print(f"   Time: {query.execution_time}ms")
    print(f"   Frequency: {query.count} times")
    print()
```

---

## 6. Query Validation

### Step 6.1: SQL Syntax Validation

```python
from ai_shell import QueryValidator

# Initialize validator
validator = QueryValidator()

# Validate syntax
queries = [
    "SELECT * FROM users WHERE id = 1",  # Valid
    "SELCT * FROM users",  # Invalid - typo
    "SELECT * FROM users WHERE",  # Invalid - incomplete
]

for query in queries:
    result = validator.validate_syntax(query)

    if result.is_valid:
        print(f"✓ Valid: {query}")
    else:
        print(f"✗ Invalid: {query}")
        print(f"  Error: {result.error}")
        print(f"  Suggestion: {result.suggestion}")
    print()
```

**Expected Output:**
```
✓ Valid: SELECT * FROM users WHERE id = 1

✗ Invalid: SELCT * FROM users
  Error: syntax error at or near "SELCT"
  Suggestion: Did you mean 'SELECT'?

✗ Invalid: SELECT * FROM users WHERE
  Error: incomplete WHERE clause
  Suggestion: Add condition after WHERE
```

### Step 6.2: Security Validation

```python
# Validate for SQL injection risks
queries = [
    "SELECT * FROM users WHERE id = 1",  # Safe
    "SELECT * FROM users WHERE name = 'admin' OR '1'='1'",  # Injection risk
    "SELECT * FROM users; DROP TABLE users; --",  # Critical risk
]

for query in queries:
    result = validator.validate_security(query)

    print(f"Query: {query}")
    print(f"  Risk level: {result.risk_level}")  # safe, low, medium, high, critical
    print(f"  Threats detected: {result.threats}")
    if result.threats:
        print(f"  Recommendation: {result.recommendation}")
    print()
```

**Expected Output:**
```
Query: SELECT * FROM users WHERE id = 1
  Risk level: safe
  Threats detected: []

Query: SELECT * FROM users WHERE name = 'admin' OR '1'='1'
  Risk level: high
  Threats detected: ['SQL_INJECTION', 'TAUTOLOGY']
  Recommendation: Use parameterized queries

Query: SELECT * FROM users; DROP TABLE users; --
  Risk level: critical
  Threats detected: ['SQL_INJECTION', 'DATA_MODIFICATION', 'COMMENT_ATTACK']
  Recommendation: BLOCKED - Use parameterized queries and validate input
```

### Step 6.3: Performance Validation

```python
# Validate query performance
query = "SELECT * FROM users u, orders o WHERE u.id = o.user_id"

result = validator.validate_performance(query)

print(f"Query: {query}")
print(f"  Performance score: {result.score}/100")
print(f"  Estimated execution time: {result.estimated_time}ms")
print(f"\nIssues:")
for issue in result.issues:
    print(f"  - {issue.description} (Impact: {issue.impact})")
print(f"\nRecommendations:")
for rec in result.recommendations:
    print(f"  - {rec}")
```

### Step 6.4: Comprehensive Validation

```python
# Run all validations
query = "SELECT * FROM users WHERE email LIKE '%@gmail.com'"

result = validator.validate_all(query)

print("Comprehensive Validation:")
print(f"  Syntax: {'✓' if result.syntax_valid else '✗'}")
print(f"  Security: {result.security_risk_level}")
print(f"  Performance: {result.performance_score}/100")
print(f"  Overall: {'PASS' if result.overall_valid else 'FAIL'}")

if result.issues:
    print("\nIssues:")
    for issue in result.issues:
        print(f"  - {issue}")
```

---

## 7. Validation Checkpoints

### Complete Query System Validation

```python
from ai_shell import QuerySystemValidator

validator = QuerySystemValidator(connector)

print("\n=== Query System Validation ===\n")

# Test NLP translation
nlp_test = await validator.test_nlp_translation()
print(f"✓ NLP Translation: {nlp_test.status}")
print(f"  Accuracy: {nlp_test.accuracy}%")

# Test query optimization
opt_test = await validator.test_optimization()
print(f"✓ Query Optimization: {opt_test.status}")
print(f"  Average improvement: {opt_test.avg_improvement}%")

# Test performance monitoring
perf_test = await validator.test_performance_monitoring()
print(f"✓ Performance Monitoring: {perf_test.status}")

# Test slow query detection
slow_test = await validator.test_slow_query_detection()
print(f"✓ Slow Query Detection: {slow_test.status}")
print(f"  Detection rate: {slow_test.detection_rate}%")

# Test query validation
val_test = await validator.test_query_validation()
print(f"✓ Query Validation: {val_test.status}")
print(f"  SQL injection blocked: {val_test.injection_blocked}")

print(f"\nOverall Status: {'PASS' if validator.all_passed() else 'FAIL'}")
```

**Expected Output:**
```
=== Query System Validation ===

✓ NLP Translation: PASS
  Accuracy: 94.5%
✓ Query Optimization: PASS
  Average improvement: 76.3%
✓ Performance Monitoring: PASS
✓ Slow Query Detection: PASS
  Detection rate: 98.2%
✓ Query Validation: PASS
  SQL injection blocked: True

Overall Status: PASS
```

---

## 8. Troubleshooting

### Issue 1: NLP Translation Errors

**Symptoms:**
```
NLPError: Could not translate natural language query
```

**Solutions:**
```python
# Check model availability
nlp_engine = NLPQueryEngine(connector)
available_models = await nlp_engine.list_available_models()
print(f"Available models: {available_models}")

# Use different model
nlp_engine = NLPQueryEngine(connector, model="claude-3")

# Provide schema context
nlp_engine.set_schema_context({
    "tables": ["users", "orders", "products"],
    "relationships": [
        {"from": "orders.user_id", "to": "users.id"},
        {"from": "orders.product_id", "to": "products.id"}
    ]
})

# Retry with context
result = await nlp_engine.query("Show me order details")
```

### Issue 2: Query Optimization Not Working

**Symptoms:**
```
Optimized query is slower than original
```

**Solutions:**
```python
# Disable specific optimizations
optimizer = QueryOptimizer(
    connector,
    enable_subquery_conversion=False,  # Disable if causing issues
    enable_join_reordering=True
)

# Force index usage
query = "SELECT * FROM users WHERE email = 'test@example.com'"
optimized = await optimizer.optimize(query, force_index="idx_users_email")

# Analyze optimization
result = await optimizer.explain_optimization(query)
print(f"Optimization details: {result.details}")
```

### Issue 3: Slow Query Detection Missing Queries

**Symptoms:**
```
Known slow queries not being detected
```

**Solutions:**
```python
# Lower threshold
detector = SlowQueryDetector(
    connector,
    threshold_ms=50,  # Lower from 100ms
    sampling_rate=1.0  # Monitor 100% of queries
)

# Enable detailed logging
detector.enable_detailed_logging()

# Check detection statistics
stats = await detector.get_statistics()
print(f"Monitored: {stats.monitored_queries}")
print(f"Detected: {stats.detected_slow_queries}")
print(f"Detection rate: {stats.detection_rate}%")
```

### Issue 4: High Memory Usage

**Symptoms:**
```
MemoryError: Query result too large
```

**Solutions:**
```python
# Use streaming for large results
async for batch in executor.execute_streaming(
    "SELECT * FROM large_table",
    batch_size=1000
):
    process_batch(batch)
    # Process in chunks instead of loading all at once

# Limit result size
executor.set_max_rows(10000)

# Use cursor
cursor = await executor.execute_cursor(
    "SELECT * FROM large_table"
)
while True:
    rows = await cursor.fetch(1000)
    if not rows:
        break
    process_rows(rows)
```

### Issue 5: Query Validation False Positives

**Symptoms:**
```
Valid queries being flagged as security risks
```

**Solutions:**
```python
# Whitelist specific patterns
validator = QueryValidator()
validator.add_whitelist_pattern(r"SELECT \* FROM users WHERE id = \d+")

# Adjust sensitivity
validator.set_security_sensitivity("medium")  # low, medium, high

# Use parameterized queries
query = "SELECT * FROM users WHERE id = :id"
params = {"id": user_input}
result = await executor.execute(query, params)
```

---

## Next Steps

Congratulations! You've completed Part 2 of the AI-Shell tutorial. You now know how to:

- ✓ Use NLP to generate SQL queries
- ✓ Apply 33 different query patterns
- ✓ Optimize queries for better performance
- ✓ Monitor query performance in real-time
- ✓ Detect and analyze slow queries
- ✓ Validate queries for security and performance

**Continue to Part 3:** [Security & Enterprise Features](HANDS_ON_PART3_SECURITY.md) to learn:
- SQL injection prevention
- Role-based access control
- Data encryption
- Audit logging
- Multi-tenancy

---

## Quick Reference

### Essential NLP Commands

```python
# Natural language query
result = await nlp_engine.query("Show me all users from last week")

# Optimize query
optimized = await optimizer.optimize(query)

# Monitor performance
report = await monitor.get_report()

# Detect slow queries
slow_queries = await detector.get_slow_queries()

# Validate query
result = validator.validate_all(query)
```

---

**Time to Complete:** 45-60 minutes
**Difficulty:** Intermediate
**Previous Tutorial:** Part 1 - Getting Started & Database Basics
**Next Tutorial:** Part 3 - Security & Enterprise Features
