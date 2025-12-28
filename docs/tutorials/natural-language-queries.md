# Natural Language Queries Tutorial

> **📋 Implementation Status**
>
> **Current Status:** In Development
> **CLI Availability:** Partial
> **Completeness:** 31%
>
> **What Works Now:**
> - Basic query execution with AI-Shell CLI
> - Database connection management
> - Simple natural language query interpretation
>
> **Coming Soon:**
> - Advanced context-aware querying
> - Query refinement and iteration features
> - Semantic search through command history
> - Query templates and aliases
> - Full natural language parsing capabilities
>
> **Note:** This tutorial describes the intended functionality. Check the [Gap Analysis Report](../FEATURE_GAP_ANALYSIS_REPORT.md) for detailed implementation status.

## Introduction and Overview

AI-Shell revolutionizes database interaction by allowing you to query your databases using plain English instead of complex SQL syntax. Powered by Anthropic's Claude AI, AI-Shell understands context, intent, and natural language patterns to generate optimized SQL queries automatically.

This tutorial will teach you how to leverage natural language queries to:
- Query databases without knowing SQL
- Perform complex data analysis with simple commands
- Save time and reduce errors
- Enable non-technical team members to access data

**What You'll Learn:**
- Basic natural language query syntax
- Advanced query patterns and techniques
- Context-aware querying
- Query refinement and iteration
- Best practices for natural language queries

**Time to Complete:** 20-30 minutes

---

## Prerequisites

Before starting this tutorial, ensure you have:

### Required
- AI-Shell installed (v1.0.0 or higher)
  ```bash
  npm install -g ai-shell
  ```
- Anthropic API key configured
  ```bash
  export ANTHROPIC_API_KEY="your-api-key"
  ```
- At least one database connection configured
  ```bash
  ai-shell connect postgres://user:pass@localhost:5432/mydb
  ```

### Recommended
- Basic understanding of database concepts (tables, rows, columns)
- Sample data in your database for testing
- Access to a development or test database (not production for learning)

### Verify Your Setup
```bash
# Check AI-Shell version
ai-shell --version
# Expected output: ai-shell v1.0.0 or higher

# Verify database connection
ai-shell query "show tables"
# Should display list of tables in your database

# Test AI connectivity
ai-shell query "how many tables do I have?"
# Should return a count of your tables
```

---

## Step-by-Step Instructions

### Step 1: Your First Natural Language Query

Let's start with simple queries to understand the basics.

```bash
# Count records in a table
ai-shell query "how many users do we have?"

# View recent records
ai-shell query "show me the last 10 orders"

# Find specific data
ai-shell query "find all active customers"
```

**What's Happening:**
- AI-Shell analyzes your natural language input
- Claude AI interprets your intent and database schema
- SQL query is generated and executed automatically
- Results are formatted for easy reading

**Expected Output:**
```
🔍 Query: how many users do we have?
📊 SQL Generated:
SELECT COUNT(*) as user_count FROM users;

Results:
┌────────────┐
│ user_count │
├────────────┤
│ 1,247      │
└────────────┘

✓ Query executed in 23ms
```

---

### Step 2: Filtering and Conditions

Natural language makes complex filtering intuitive.

```bash
# Date-based filtering
ai-shell query "show users who signed up this week"

# Multiple conditions
ai-shell query "find orders over $100 placed in the last 30 days"

# Status filtering
ai-shell query "show all pending orders from premium customers"

# Exclusion queries
ai-shell query "find users who haven't logged in for 90 days"
```

**Advanced Filtering Examples:**
```bash
# Range queries
ai-shell query "show products priced between $50 and $200"

# Pattern matching
ai-shell query "find customers with gmail email addresses"

# Null handling
ai-shell query "show users without a phone number"

# Boolean logic
ai-shell query "find orders that are either shipped or delivered"
```

**Pro Tip:** AI-Shell understands temporal references like "this week," "last month," "yesterday," and "last quarter."

---

### Step 3: Aggregations and Analytics

Perform complex analytics without writing GROUP BY clauses.

```bash
# Simple aggregations
ai-shell query "what's the average order value?"
ai-shell query "show total revenue by product category"

# Time-based analytics
ai-shell query "show daily signups for the last month"
ai-shell query "compare sales this quarter vs last quarter"

# Multi-level aggregations
ai-shell query "show top 10 customers by total spending"
ai-shell query "what's the average order value per customer segment?"

# Percentile queries
ai-shell query "show 95th percentile response time for API calls"
```

**Advanced Analytics:**
```bash
# Revenue analysis
ai-shell query "show revenue by product category this quarter, sorted by highest revenue"

# Customer insights
ai-shell query "find customers who made more than 5 purchases and spent over $1000"

# Growth metrics
ai-shell query "show month-over-month user growth for the past year"

# Conversion funnels
ai-shell query "show conversion rate from signup to first purchase"
```

---

### Step 4: Joining Data Across Tables

AI-Shell automatically determines relationships between tables.

```bash
# Simple joins
ai-shell query "show orders with customer names"

# Multiple table joins
ai-shell query "show order details with customer info and product names"

# Left joins (including nulls)
ai-shell query "show all users and their orders, including users with no orders"

# Complex relationships
ai-shell query "find customers who ordered products from the electronics category"
```

**Real-World Join Examples:**
```bash
# E-commerce analysis
ai-shell query "show customer names, order dates, and product names for orders placed this month"

# User activity analysis
ai-shell query "show users with their last login date and total number of sessions"

# Sales pipeline
ai-shell query "show deals with associated contact information and sales rep names"
```

**How AI-Shell Handles Joins:**
- Automatically detects foreign key relationships
- Infers table relationships from naming conventions
- Optimizes join order for performance
- Handles ambiguous references by asking for clarification

---

### Step 5: Sorting and Limiting Results

Control result ordering and size naturally.

```bash
# Sorting
ai-shell query "show top 10 products by sales"
ai-shell query "list customers alphabetically"
ai-shell query "show recent orders, newest first"

# Limiting results
ai-shell query "show 5 random products"
ai-shell query "give me a sample of 100 user records"

# Pagination hints
ai-shell query "show the next 20 products after skipping the first 40"
```

**Advanced Sorting:**
```bash
# Multi-column sorting
ai-shell query "show orders sorted by status, then by date descending"

# Conditional sorting
ai-shell query "show products sorted by price within each category"

# Complex ordering
ai-shell query "show top performers by sales volume, breaking ties by revenue"
```

---

### Step 6: Working with Dates and Times

AI-Shell excels at natural date/time handling.

```bash
# Relative dates
ai-shell query "show orders from yesterday"
ai-shell query "find users created in the last 7 days"
ai-shell query "show revenue for last quarter"

# Specific dates
ai-shell query "show orders placed on October 26, 2025"
ai-shell query "find users who signed up in Q3 2025"

# Date ranges
ai-shell query "show sales between January 1 and March 31, 2025"
ai-shell query "find orders from the past week excluding weekends"

# Time-based grouping
ai-shell query "show orders by day for the last 30 days"
ai-shell query "group revenue by month for this year"
ai-shell query "show average response time per hour over the last 24 hours"
```

**Supported Date Formats:**
- Relative: "today," "yesterday," "this week," "last month," "past year"
- Specific: "January 15, 2025," "2025-01-15," "Jan 15"
- Ranges: "between X and Y," "from X to Y"
- Periods: "Q1 2025," "March 2025," "week of Jan 15"

---

### Step 7: Context-Aware Querying

AI-Shell remembers context from previous queries for natural conversation flow.

```bash
# Initial query
ai-shell query "show all orders from last month"

# Follow-up queries (context maintained)
ai-shell query "filter those to only premium customers"
ai-shell query "now sort by order value descending"
ai-shell query "show me just the top 10"
ai-shell query "export those to CSV"

# Referencing previous results
ai-shell query "how many were there total?"
ai-shell query "what's the average order value?"
```

**Context Management:**
```bash
# Clear context when starting new analysis
ai-shell context clear

# Save context for later
ai-shell context save "monthly-order-analysis"

# Restore saved context
ai-shell context load "monthly-order-analysis"
```

---

### Step 8: Query Refinement and Iteration

Learn from AI-Shell's interpretations and refine your queries.

```bash
# Start broad
ai-shell query "show user activity"
# AI may ask: "Which activity metrics? (logins, purchases, page views, etc.)"

# Provide specifics
ai-shell query "show user logins for the past week"

# View generated SQL to understand interpretation
ai-shell query "show revenue by category" --show-sql

# Refine based on results
ai-shell query "show revenue by category for active products only"
```

**Understanding Query Interpretation:**
```bash
# Use explain mode to see how AI interprets your query
ai-shell query "show top customers" --explain

# Output shows:
# Interpretation:
#   - "top" interpreted as highest value metric
#   - Assumed metric: total_spending (you can specify others)
#   - Default limit: 10 (you can change this)
#   - Sorting: descending
#
# You can modify with:
#   - "top 20 customers by order count"
#   - "top customers by lifetime value"
```

---

### Step 9: Advanced Natural Language Patterns

Master sophisticated query patterns.

```bash
# Subqueries (automatically handled)
ai-shell query "show products that have never been ordered"
ai-shell query "find users whose spending is above average"

# Window functions (through natural language)
ai-shell query "show running total of revenue by date"
ai-shell query "rank products by sales within each category"

# Complex conditions
ai-shell query "find customers who ordered in January but not in February"
ai-shell query "show products with sales growing month over month"

# Statistical queries
ai-shell query "show standard deviation of order values by customer segment"
ai-shell query "calculate correlation between marketing spend and signup rate"
```

---

### Step 10: Handling Ambiguity and Clarifications

Learn how AI-Shell handles unclear requests.

**Example 1: Ambiguous Table References**
```bash
ai-shell query "show recent activity"

# AI-Shell responds:
# "I found multiple tables related to activity:
#  1. user_activity (user logins and actions)
#  2. system_activity (system logs)
#  3. purchase_activity (transaction logs)
# Which would you like to query?"

# You respond:
ai-shell query "the first one"
# or
ai-shell query "user activity"
```

**Example 2: Missing Context**
```bash
ai-shell query "show totals by category"

# AI-Shell responds:
# "What metric would you like totaled? (Examples: revenue, order_count, quantity)"

# You respond:
ai-shell query "revenue"
```

**Example 3: Ambiguous Time Periods**
```bash
ai-shell query "show weekly data"

# AI-Shell responds:
# "How many weeks of data? (Default: last 4 weeks)"

# You respond:
ai-shell query "last 12 weeks"
```

---

## Common Use Cases

### Use Case 1: Sales Analysis

**Scenario:** Analyze sales performance without SQL knowledge.

```bash
# Daily sales
ai-shell query "show daily revenue for the last 30 days"

# Product performance
ai-shell query "which products had the highest sales last month?"

# Customer segments
ai-shell query "compare revenue from new vs returning customers"

# Trends
ai-shell query "show month-over-month sales growth"

# Forecasting
ai-shell query "what's the average daily revenue? use that to project this month's total"
```

---

### Use Case 2: User Behavior Analysis

**Scenario:** Understand how users interact with your application.

```bash
# Engagement metrics
ai-shell query "show daily active users for the past week"

# Retention analysis
ai-shell query "how many users from last month are still active?"

# Feature usage
ai-shell query "show most popular features by user count"

# Cohort analysis
ai-shell query "group users by signup month and show retention rate"

# User journey
ai-shell query "show average time from signup to first purchase"
```

---

### Use Case 3: Operational Monitoring

**Scenario:** Monitor system health and performance.

```bash
# Error tracking
ai-shell query "show error count by type in the last hour"

# Performance monitoring
ai-shell query "show average API response time per endpoint today"

# Resource usage
ai-shell query "find database queries taking longer than 1 second"

# Anomaly detection
ai-shell query "show days where error rate was above average"

# Capacity planning
ai-shell query "show peak concurrent users by hour over the last week"
```

---

### Use Case 4: Customer Support

**Scenario:** Quickly access customer data for support inquiries.

```bash
# Customer lookup
ai-shell query "find customer with email john.doe@example.com"

# Order history
ai-shell query "show last 10 orders for customer ID 12345"

# Support tickets
ai-shell query "show open tickets for customers with premium subscriptions"

# Account status
ai-shell query "find customers with failed payment methods"

# Usage summary
ai-shell query "show total purchases and account age for customer 12345"
```

---

### Use Case 5: Marketing Analytics

**Scenario:** Measure campaign effectiveness and ROI.

```bash
# Campaign performance
ai-shell query "show signups by referral source this month"

# Conversion rates
ai-shell query "calculate conversion rate from trial to paid subscription"

# Customer acquisition cost
ai-shell query "show marketing spend per new customer by channel"

# Attribution analysis
ai-shell query "show first and last touch attribution for conversions"

# Segment analysis
ai-shell query "compare engagement rates across customer segments"
```

---

## Troubleshooting Tips

### Issue 1: Query Returns Unexpected Results

**Problem:** Results don't match what you expected.

**Solutions:**
```bash
# View the generated SQL to understand interpretation
ai-shell query "your query here" --show-sql

# Add more specificity to your query
# Instead of: "show users"
# Try: "show all user records with their email addresses"

# Use explicit date ranges
# Instead of: "show recent orders"
# Try: "show orders from the last 7 days"

# Specify sorting and limits
# Instead of: "show top customers"
# Try: "show top 10 customers by total spending, highest first"
```

---

### Issue 2: AI-Shell Asks Too Many Clarifying Questions

**Problem:** Query requires multiple follow-up questions.

**Solutions:**
```bash
# Provide complete information upfront
# Instead of: "show sales"
# Try: "show total sales revenue by product category for Q3 2025"

# Be specific about:
# - Time periods: "last 30 days" vs "recently"
# - Metrics: "revenue" vs "performance"
# - Scope: "active users" vs "users"
# - Sorting: "top 10 by sales" vs "top products"

# Use explicit table names for ambiguous queries
# Instead of: "show activity"
# Try: "show records from user_activity table"
```

---

### Issue 3: Query Takes Too Long

**Problem:** Natural language query is slow to execute.

**Solutions:**
```bash
# Add limits to large queries
ai-shell query "show first 100 orders from last year"

# Use date filters to reduce data volume
ai-shell query "show orders from last month" # instead of all orders

# Check the generated SQL for optimization opportunities
ai-shell query "your query" --show-sql --explain-plan

# Use the optimize command on slow queries
ai-shell optimize "your natural language query"

# Enable query caching for repeated queries
ai-shell config set performance.enableCache true
```

---

### Issue 4: AI Doesn't Understand Domain-Specific Terms

**Problem:** Your business uses unique terminology that AI-Shell doesn't recognize.

**Solutions:**
```bash
# Define custom aliases for your terminology
ai-shell alias add "deals" "opportunities table"
ai-shell alias add "ARR" "annual recurring revenue"

# Use table and column names explicitly
# Instead of: "show MRR"
# Try: "show sum of monthly_revenue column"

# Provide context in your query
ai-shell query "show 'opportunities' which we call deals"

# Train AI-Shell with examples
ai-shell train "when I say 'active deals', query opportunities where status='open'"
```

---

### Issue 5: Results Format Is Hard to Read

**Problem:** Query results are not formatted as needed.

**Solutions:**
```bash
# Specify output format
ai-shell query "show users" --format table
ai-shell query "show users" --format json
ai-shell query "show users" --format csv

# Request specific columns
ai-shell query "show only user names and emails"

# Control result size
ai-shell query "show first 20 users"

# Export to file
ai-shell query "show all orders" --export orders.csv

# Use pretty-print for large results
ai-shell query "show users" --pretty
```

---

### Issue 6: Cannot Query Specific Edge Cases

**Problem:** Complex edge cases aren't handled well by natural language.

**Solutions:**
```bash
# Fall back to SQL for complex queries
ai-shell execute "SELECT ... your SQL here ..."

# Break complex queries into steps
ai-shell query "show all orders" --save temp_orders
ai-shell query "from temp_orders, show those over $100"

# Combine natural language with SQL hints
ai-shell query "show users (use LEFT JOIN with orders table)"

# Use the query builder for complex scenarios
ai-shell build-query
# Follow interactive prompts
```

---

## Best Practices

### 1. Start Simple, Then Add Complexity

```bash
# Start with basic query
ai-shell query "show orders"

# Add time filter
ai-shell query "show orders from last month"

# Add additional filters
ai-shell query "show orders from last month where amount > 100"

# Add aggregation
ai-shell query "show total revenue from orders last month where amount > 100"
```

### 2. Be Explicit About Intent

```bash
# Vague
ai-shell query "show data"

# Better
ai-shell query "show user signup data"

# Best
ai-shell query "show count of user signups by date for the last 30 days"
```

### 3. Use Consistent Terminology

```bash
# Maintain consistency in how you refer to concepts
# Always use "customers" or always use "users", not both
# This helps AI-Shell learn your patterns
```

### 4. Leverage Context for Related Queries

```bash
# Efficient use of context
ai-shell query "show orders from last month"
ai-shell query "filter to premium customers"
ai-shell query "sort by order value"
ai-shell query "export to CSV"

# Context automatically maintained across queries
```

### 5. Validate Results on Unfamiliar Queries

```bash
# For new query types, verify the SQL
ai-shell query "your new query pattern" --show-sql

# Check row count makes sense
ai-shell query "how many results in previous query?"

# Spot-check a few records
ai-shell query "show 5 random samples from previous results"
```

### 6. Save and Reuse Common Queries

```bash
# Save frequently used queries as aliases
ai-shell alias add "daily-sales" "show total revenue by date for last 30 days"

# Use saved queries
ai-shell query daily-sales

# List all saved queries
ai-shell alias list

# Create query templates
ai-shell template create "revenue-by-period" \
  "show total revenue for [period]"

# Use template
ai-shell query revenue-by-period --period "last quarter"
```

### 7. Use Natural Language for Exploration, SQL for Production

```bash
# Exploration phase - use natural language
ai-shell query "show me interesting patterns in user signups"

# Once you know what you need - get the SQL
ai-shell query "show daily signups with 7-day moving average" --show-sql

# Copy SQL to your application code for production use
# Natural language is great for ad-hoc analysis, but
# SQL is better for reliable, repeatable production queries
```

---

## Next Steps

### Master Advanced Features

1. **Query Optimization**
   - Learn to optimize your queries automatically
   - [Tutorial: Query Optimization](./query-optimization.md)

2. **Database Federation**
   - Query across multiple databases simultaneously
   - [Tutorial: Database Federation](./database-federation.md)

3. **Cognitive Features**
   - Use AI-Shell's memory and learning capabilities
   - [Tutorial: Cognitive Features](./cognitive-features.md)

### Explore Related Topics

- [Performance Monitoring](./performance-monitoring.md) - Track query performance
- [Security Setup](./security.md) - Secure your natural language queries
- [CLI Reference](../cli-reference.md) - Complete command reference

### Practice Exercises

Try these exercises to solidify your learning:

1. **Exercise 1: Basic Queries**
   - Count records in each of your tables
   - Find records created today
   - Show the 10 most recent records from your main table

2. **Exercise 2: Filtering**
   - Find records matching multiple conditions
   - Query date ranges
   - Use pattern matching (emails, names, etc.)

3. **Exercise 3: Analytics**
   - Calculate averages, sums, and counts
   - Group data by categories
   - Show trends over time

4. **Exercise 4: Joins**
   - Query related data across tables
   - Show data with customer/user information
   - Create comprehensive reports

5. **Exercise 5: Complex Scenarios**
   - Combine multiple filters, joins, and aggregations
   - Use context to build complex queries iteratively
   - Export results in different formats

### Get Help

- **Documentation**: [Complete documentation](https://docs.ai-shell.dev)
- **Examples**: [More query examples](../examples/natural-language-queries.md)
- **Community**: [Join discussions](https://github.com/your-org/ai-shell/discussions)
- **Support**: [Get help](https://github.com/your-org/ai-shell/issues)

---

## Summary

You've learned how to:
- Execute natural language queries without SQL knowledge
- Filter, sort, and aggregate data conversationally
- Use context to build complex queries iteratively
- Handle ambiguity and refine queries
- Apply natural language queries to real-world scenarios
- Troubleshoot common issues
- Follow best practices for effective querying

Natural language queries in AI-Shell empower everyone on your team to access and analyze data, regardless of SQL expertise. Start with simple queries and gradually build complexity as you become more comfortable with the system.

**Remember:** The best way to learn is by doing. Start querying your database with natural language today and discover how much more productive you can be!

---

**Related Tutorials:**
- [Query Optimization](./query-optimization.md)
- [Database Federation](./database-federation.md)
- [Performance Monitoring](./performance-monitoring.md)

**Need Help?** [Visit our documentation](https://docs.ai-shell.dev) or [join the community](https://github.com/your-org/ai-shell/discussions)
