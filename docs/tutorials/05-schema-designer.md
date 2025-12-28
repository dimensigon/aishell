# Schema Designer Tutorial: Design Perfect Schemas with AI

## Real-World Scenario

**Problem**: You're designing a database for a new e-commerce platform. You sketch out tables, but you're unsure about normalization, indexes, constraints, and whether your design will scale to millions of users.

**Solution**: AI-Shell's Schema Designer analyzes your requirements, suggests optimal table structures, relationships, and indexes based on access patterns, and validates your design before you write a single line of SQL.

---

## Table of Contents

1. [Setup](#setup)
2. [Basic Schema Design](#basic-schema-design)
3. [Real-World Example](#real-world-example)
4. [Advanced Patterns](#advanced-patterns)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Setup

### Start Schema Designer

```bash
# Launch interactive schema designer
aishell schema design
```

**Welcome Screen:**

```
✨ AI-Powered Schema Designer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Let's design your perfect database schema!

What are you building?

[1] E-commerce platform
[2] Social network
[3] SaaS application
[4] Analytics system
[5] Custom (describe your needs)

> Choice: 1

Great! I'll help you design an e-commerce database.

Tell me about your requirements:
- Expected number of users? 1M
- Expected number of products? 100K
- Expected number of orders per day? 10K
- Support for multiple currencies? Yes
- Support for multiple languages? Yes
- Need inventory management? Yes
- Need review system? Yes

🤖 Analyzing requirements...
```

---

## Basic Schema Design

### Step 1: Describe Your Needs

```bash
# Natural language schema design
aishell schema design "
  I need a database for an e-commerce site with:
  - Users with profiles and multiple addresses
  - Products with categories and variants
  - Shopping carts and wishlist
  - Orders with multiple items
  - Payments and refunds
  - Product reviews and ratings
  - Inventory tracking
"
```

**AI Analysis:**

```
🤖 AI Schema Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Requirements Summary:
  ✓ 8 main entities identified
  ✓ 15 relationships detected
  ✓ 3 many-to-many relationships
  ✓ E-commerce pattern recognized

Recommended Architecture:
  Database: PostgreSQL 14+ (best for e-commerce)
  Normalization: 3NF (balanced)
  Estimated tables: 16
  Estimated indexes: 42

Design Philosophy:
  ✓ Optimized for read-heavy workloads
  ✓ Designed for horizontal scaling
  ✓ Built-in audit trail
  ✓ Soft delete support
  ✓ Multi-tenancy ready

Generating schema...
```

### Step 2: Review Generated Schema

```
📋 Generated Schema: E-Commerce Platform
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tables: 16 | Relationships: 23 | Indexes: 42

1. users
┌─────────────────┬──────────────┬─────────────────────────────┐
│ Column          │ Type         │ Constraints                 │
├─────────────────┼──────────────┼─────────────────────────────┤
│ id              │ BIGSERIAL    │ PRIMARY KEY                 │
│ email           │ VARCHAR(255) │ UNIQUE, NOT NULL            │
│ password_hash   │ VARCHAR(255) │ NOT NULL                    │
│ first_name      │ VARCHAR(100) │                             │
│ last_name       │ VARCHAR(100) │                             │
│ phone           │ VARCHAR(20)  │                             │
│ email_verified  │ BOOLEAN      │ DEFAULT FALSE               │
│ created_at      │ TIMESTAMP    │ DEFAULT NOW()               │
│ updated_at      │ TIMESTAMP    │ DEFAULT NOW()               │
│ deleted_at      │ TIMESTAMP    │ NULL (soft delete)          │
└─────────────────┴──────────────┴─────────────────────────────┘

Indexes:
  ✓ idx_users_email (unique) - for login
  ✓ idx_users_created_at - for analytics
  ✓ idx_users_deleted_at - for soft delete queries

Relationships:
  → addresses (one-to-many)
  → orders (one-to-many)
  → cart_items (one-to-many)
  → wishlist_items (one-to-many)
  → reviews (one-to-many)

2. addresses
┌─────────────────┬──────────────┬─────────────────────────────┐
│ Column          │ Type         │ Constraints                 │
├─────────────────┼──────────────┼─────────────────────────────┤
│ id              │ BIGSERIAL    │ PRIMARY KEY                 │
│ user_id         │ BIGINT       │ FOREIGN KEY → users.id      │
│ type            │ VARCHAR(20)  │ CHECK (billing|shipping)    │
│ is_default      │ BOOLEAN      │ DEFAULT FALSE               │
│ street_line1    │ VARCHAR(255) │ NOT NULL                    │
│ street_line2    │ VARCHAR(255) │                             │
│ city            │ VARCHAR(100) │ NOT NULL                    │
│ state           │ VARCHAR(100) │ NOT NULL                    │
│ postal_code     │ VARCHAR(20)  │ NOT NULL                    │
│ country         │ VARCHAR(2)   │ NOT NULL (ISO 3166-1)       │
│ created_at      │ TIMESTAMP    │ DEFAULT NOW()               │
└─────────────────┴──────────────┴─────────────────────────────┘

Indexes:
  ✓ idx_addresses_user_id - for user lookups
  ✓ idx_addresses_user_default - for default address
    CREATE INDEX idx_addresses_user_default ON addresses(user_id, is_default) WHERE is_default = true

3. products
┌─────────────────┬──────────────┬─────────────────────────────┐
│ Column          │ Type         │ Constraints                 │
├─────────────────┼──────────────┼─────────────────────────────┤
│ id              │ BIGSERIAL    │ PRIMARY KEY                 │
│ sku             │ VARCHAR(100) │ UNIQUE, NOT NULL            │
│ name            │ VARCHAR(255) │ NOT NULL                    │
│ description     │ TEXT         │                             │
│ category_id     │ BIGINT       │ FOREIGN KEY → categories.id │
│ base_price      │ DECIMAL      │ NOT NULL, CHECK (>= 0)      │
│ currency        │ VARCHAR(3)   │ NOT NULL, DEFAULT 'USD'     │
│ is_active       │ BOOLEAN      │ DEFAULT TRUE                │
│ created_at      │ TIMESTAMP    │ DEFAULT NOW()               │
│ updated_at      │ TIMESTAMP    │ DEFAULT NOW()               │
│ deleted_at      │ TIMESTAMP    │ NULL                        │
└─────────────────┴──────────────┴─────────────────────────────┘

Indexes:
  ✓ idx_products_sku (unique)
  ✓ idx_products_category - for category browsing
  ✓ idx_products_active - for active products
  ✓ idx_products_name_gin - for full-text search
    CREATE INDEX idx_products_name_gin ON products USING GIN (to_tsvector('english', name || ' ' || description))

4. product_variants
┌─────────────────┬──────────────┬─────────────────────────────┐
│ Column          │ Type         │ Constraints                 │
├─────────────────┼──────────────┼─────────────────────────────┤
│ id              │ BIGSERIAL    │ PRIMARY KEY                 │
│ product_id      │ BIGINT       │ FOREIGN KEY → products.id   │
│ sku             │ VARCHAR(100) │ UNIQUE, NOT NULL            │
│ size            │ VARCHAR(20)  │                             │
│ color           │ VARCHAR(50)  │                             │
│ price_modifier  │ DECIMAL      │ DEFAULT 0                   │
│ stock_quantity  │ INTEGER      │ NOT NULL, CHECK (>= 0)      │
│ created_at      │ TIMESTAMP    │ DEFAULT NOW()               │
└─────────────────┴──────────────┴─────────────────────────────┘

5. orders
┌─────────────────┬──────────────┬─────────────────────────────┐
│ Column          │ Type         │ Constraints                 │
├─────────────────┼──────────────┼─────────────────────────────┤
│ id              │ BIGSERIAL    │ PRIMARY KEY                 │
│ order_number    │ VARCHAR(50)  │ UNIQUE, NOT NULL            │
│ user_id         │ BIGINT       │ FOREIGN KEY → users.id      │
│ status          │ VARCHAR(20)  │ CHECK (pending|paid|...)    │
│ subtotal        │ DECIMAL      │ NOT NULL                    │
│ tax             │ DECIMAL      │ NOT NULL                    │
│ shipping        │ DECIMAL      │ NOT NULL                    │
│ total           │ DECIMAL      │ NOT NULL                    │
│ currency        │ VARCHAR(3)   │ NOT NULL                    │
│ shipping_addr   │ BIGINT       │ FOREIGN KEY → addresses.id  │
│ billing_addr    │ BIGINT       │ FOREIGN KEY → addresses.id  │
│ created_at      │ TIMESTAMP    │ DEFAULT NOW()               │
│ updated_at      │ TIMESTAMP    │ DEFAULT NOW()               │
└─────────────────┴──────────────┴─────────────────────────────┘

Indexes:
  ✓ idx_orders_user_id - for user order history
  ✓ idx_orders_status - for order management
  ✓ idx_orders_created_at - for analytics
  ✓ idx_orders_number (unique) - for lookups

6. order_items
┌─────────────────┬──────────────┬─────────────────────────────┐
│ Column          │ Type         │ Constraints                 │
├─────────────────┼──────────────┼─────────────────────────────┤
│ id              │ BIGSERIAL    │ PRIMARY KEY                 │
│ order_id        │ BIGINT       │ FOREIGN KEY → orders.id     │
│ product_id      │ BIGINT       │ FOREIGN KEY → products.id   │
│ variant_id      │ BIGINT       │ FOREIGN KEY → variants.id   │
│ quantity        │ INTEGER      │ NOT NULL, CHECK (> 0)       │
│ unit_price      │ DECIMAL      │ NOT NULL                    │
│ subtotal        │ DECIMAL      │ NOT NULL                    │
│ created_at      │ TIMESTAMP    │ DEFAULT NOW()               │
└─────────────────┴──────────────┴─────────────────────────────┘

... (10 more tables)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Schema Features:
  ✓ Normalized to 3NF
  ✓ 42 indexes for optimal performance
  ✓ Full-text search enabled
  ✓ Soft delete support
  ✓ Audit trail (created_at, updated_at)
  ✓ Referential integrity
  ✓ Check constraints for data quality
  ✓ Optimized for 1M+ users

💡 AI Recommendations:
  1. Use UUID for order_number for security
  2. Partition orders table by created_at (monthly)
  3. Consider materialized view for product catalog
  4. Add read replicas for scaling

Options:
  [1] Generate SQL migration
  [2] Visualize schema diagram
  [3] Analyze performance
  [4] Modify schema
  [5] Export schema

> Choice: _
```

### Step 3: Generate SQL

```bash
# Generate creation SQL
aishell schema generate sql
```

**Generated SQL:**

```sql
-- AI-Generated Schema for E-Commerce Platform
-- Generated: 2025-10-27 14:30:00 UTC
-- Database: PostgreSQL 14+
-- Optimized for: 1M users, 100K products, 10K orders/day

-- =====================================================
-- Extensions
-- =====================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy search

-- =====================================================
-- Custom Types
-- =====================================================

CREATE TYPE order_status AS ENUM (
    'pending',
    'paid',
    'processing',
    'shipped',
    'delivered',
    'cancelled',
    'refunded'
);

CREATE TYPE address_type AS ENUM ('billing', 'shipping');

-- =====================================================
-- Tables
-- =====================================================

-- Users
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP  -- Soft delete

    -- Constraints
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Products
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id BIGINT REFERENCES categories(id),
    base_price DECIMAL(10,2) NOT NULL CHECK (base_price >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

-- Orders
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    user_id BIGINT REFERENCES users(id) ON DELETE RESTRICT,
    status order_status DEFAULT 'pending',
    subtotal DECIMAL(10,2) NOT NULL,
    tax DECIMAL(10,2) NOT NULL DEFAULT 0,
    shipping DECIMAL(10,2) NOT NULL DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    shipping_address_id BIGINT REFERENCES addresses(id),
    billing_address_id BIGINT REFERENCES addresses(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT total_calculation CHECK (total = subtotal + tax + shipping)
);

-- =====================================================
-- Indexes
-- =====================================================

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;

-- Products indexes
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category_id) WHERE is_active = TRUE;
CREATE INDEX idx_products_active ON products(is_active, created_at);
CREATE INDEX idx_products_name_gin ON products USING GIN (to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- Orders indexes
CREATE INDEX idx_orders_user ON orders(user_id, created_at DESC);
CREATE INDEX idx_orders_status ON orders(status, created_at) WHERE status != 'delivered' AND status != 'cancelled';
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_number ON orders(order_number);

-- =====================================================
-- Triggers
-- =====================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Views
-- =====================================================

-- Active products with category names
CREATE VIEW active_products AS
SELECT
    p.id,
    p.sku,
    p.name,
    p.description,
    p.base_price,
    c.name as category_name,
    COUNT(v.id) as variant_count
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN product_variants v ON p.id = v.product_id
WHERE p.is_active = TRUE
  AND p.deleted_at IS NULL
GROUP BY p.id, c.name;

-- =====================================================
-- Partitioning (for scaling)
-- =====================================================

-- Partition orders by month
CREATE TABLE orders_2025_10 PARTITION OF orders
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

CREATE TABLE orders_2025_11 PARTITION OF orders
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- Auto-create partitions (requires pg_partman extension)
-- SELECT partman.create_parent('public.orders', 'created_at', 'native', 'monthly');

-- =====================================================
-- Materialized Views (for performance)
-- =====================================================

-- Product catalog with computed fields
CREATE MATERIALIZED VIEW product_catalog AS
SELECT
    p.id,
    p.sku,
    p.name,
    p.description,
    p.base_price,
    c.name as category,
    AVG(r.rating) as avg_rating,
    COUNT(DISTINCT r.id) as review_count,
    SUM(oi.quantity) as total_sold
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN reviews r ON p.id = r.product_id
LEFT JOIN order_items oi ON p.id = oi.product_id
WHERE p.is_active = TRUE
GROUP BY p.id, c.name;

-- Refresh schedule
CREATE INDEX ON product_catalog(id);
-- Schedule: REFRESH MATERIALIZED VIEW CONCURRENTLY product_catalog; (every 1 hour)

-- =====================================================
-- Security
-- =====================================================

-- Row-level security example
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY orders_user_isolation ON orders
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::BIGINT);

-- =====================================================
-- Comments (documentation)
-- =====================================================

COMMENT ON TABLE users IS 'User accounts and authentication';
COMMENT ON COLUMN users.email_verified IS 'Whether the user has verified their email address';
COMMENT ON COLUMN users.deleted_at IS 'Soft delete timestamp - NULL means active';

COMMENT ON TABLE orders IS 'Customer orders - partitioned by month';
COMMENT ON COLUMN orders.order_number IS 'Unique order identifier shown to customer';

-- =====================================================
-- Sample Data (for testing)
-- =====================================================

-- Insert test categories
INSERT INTO categories (name, slug) VALUES
    ('Electronics', 'electronics'),
    ('Clothing', 'clothing'),
    ('Books', 'books');

-- =====================================================
-- Performance Tuning
-- =====================================================

-- Analyze tables for query planner
ANALYZE users;
ANALYZE products;
ANALYZE orders;

-- =====================================================
-- Monitoring
-- =====================================================

-- Create monitoring view
CREATE VIEW table_stats AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- =====================================================
-- Complete!
-- =====================================================

-- Total tables: 16
-- Total indexes: 42
-- Total constraints: 23
-- Estimated size for 1M users: ~50GB
-- Query performance: Optimized for read-heavy workload
```

---

## Real-World Example: Optimizing an Existing Schema

### Scenario

You have an existing schema that's slow and hard to maintain. Let AI-Shell analyze and suggest improvements.

### Analysis

```bash
# Analyze existing schema
aishell schema analyze --database production_db
```

**AI Analysis Report:**

```
🔍 Schema Analysis: production_db
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Schema Health: ⚠️  65/100 (Needs Improvement)

Issues Found: 23

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 Critical Issues (3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Missing Foreign Key Indexes
   Impact: CRITICAL
   Queries affected: 2,345/hour
   Performance impact: 80% slower joins

   Missing indexes:
   - orders.user_id (used in 45% of queries!)
   - order_items.product_id (used in 62% of queries!)
   - reviews.product_id (used in 23% of queries!)

   Fix:
   ```sql
   CREATE INDEX idx_orders_user_id ON orders(user_id);
   CREATE INDEX idx_order_items_product_id ON order_items(product_id);
   CREATE INDEX idx_reviews_product_id ON reviews(product_id);
   ```

   Expected improvement: 5x faster joins

2. Denormalization Issues
   Impact: CRITICAL
   Tables affected: orders, products

   Issue: Storing user email in orders table
   - Data duplication: 12.4M rows
   - Consistency issues: 234 mismatches found
   - Storage waste: 1.2 GB

   Fix: Remove email column, use JOIN
   ```sql
   ALTER TABLE orders DROP COLUMN user_email;
   -- Update queries to join with users table
   ```

3. No Primary Key on Junction Table
   Impact: CRITICAL
   Table: product_tags

   Issue: Many-to-many table without primary key
   - Allows duplicates (456 found!)
   - No way to update/delete specific rows
   - Query optimizer struggles

   Fix:
   ```sql
   ALTER TABLE product_tags ADD PRIMARY KEY (product_id, tag_id);
   ```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  Warning Issues (12)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. Inefficient Data Types
   - users.age: Using INT instead of SMALLINT (wastes 2 bytes/row = 6MB)
   - products.is_active: Using CHAR(1) instead of BOOLEAN
   - orders.status: Using VARCHAR(50) instead of ENUM

5. No Indexes on WHERE Clauses
   Common queries using unindexed columns:
   - products.is_active (used in 89% of product queries)
   - orders.status (used in 76% of order queries)
   - users.created_at (used in 45% of analytics)

6. Missing Constraints
   Data quality issues:
   - orders.total can be negative (found 23 cases!)
   - users.email not validated (1,234 invalid emails)
   - products.price can be NULL (89 products affected)

   Add constraints:
   ```sql
   ALTER TABLE orders ADD CONSTRAINT check_total_positive
       CHECK (total >= 0);

   ALTER TABLE users ADD CONSTRAINT check_email_format
       CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

   ALTER TABLE products ALTER COLUMN price SET NOT NULL;
   ```

7. Table Bloat
   - orders table: 34% bloat (wasting 12 GB)
   - products table: 45% bloat (wasting 8 GB)

   Recommendation: VACUUM FULL or pg_repack

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Optimization Opportunities (8)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8. Partitioning Opportunity
   - orders table (45 GB, 12.4M rows)
   - Should be partitioned by created_at
   - Est. performance improvement: 3-5x for recent queries

9. Materialized View Opportunities
   - Product catalog query (runs 2,340 times/hour)
   - User statistics (runs 890 times/hour)
   - Revenue reports (runs 234 times/hour)

10. Full-Text Search Missing
    - Searching products by name: Using LIKE (very slow!)
    - Recommendation: Add GIN index with to_tsvector

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Schema Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tables: 16
Total size: 92 GB
Total rows: 28.4M
Indexes: 18 (24 missing!)
Constraints: 12 (should be 35)
Foreign keys: 15

Normalization: 2NF (should be 3NF)
Performance score: 4/10
Maintainability: 6/10
Scalability: 5/10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Priority Action Plan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Immediate (Do Now):
  [1] Add missing foreign key indexes (5x perf improvement)
  [2] Add primary key to product_tags
  [3] Add check constraints for data quality

This Week:
  [4] Remove denormalized email column
  [5] Partition orders table
  [6] Create materialized views

This Month:
  [7] Add full-text search indexes
  [8] Optimize data types
  [9] Run VACUUM FULL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Auto-fix available. Apply all fixes? (y/n): _
```

### Auto-Fix

```bash
# Apply recommended fixes
aishell schema fix --apply-all --priority critical,warning
```

**Execution:**

```
🔧 Applying Schema Fixes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Safety checks:
  ✓ Created backup: schema_backup_20251027_143000
  ✓ Dry-run completed successfully
  ✓ No blocking queries

Applying fixes...

[1/15] Creating index idx_orders_user_id ... ✓ (12.3s)
[2/15] Creating index idx_order_items_product_id ... ✓ (8.9s)
[3/15] Creating index idx_reviews_product_id ... ✓ (3.2s)
[4/15] Adding primary key to product_tags ... ✓ (2.1s)
[5/15] Adding check constraint on orders.total ... ✓ (15.6s)
[6/15] Adding email validation constraint ... ⚠️  Skipped
        Reason: 1,234 existing rows violate constraint
        Action: Run cleanup first: aishell schema cleanup-invalid-emails

[7/15] Creating materialized view product_catalog ... ✓ (45.2s)
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Schema Optimization Complete!

Applied: 12/15 fixes
Skipped: 3 (data cleanup required)
Duration: 3m 24s

Performance Improvements:
  Before: 2,345 queries/sec, 234ms avg latency
  After: 11,234 queries/sec, 23ms avg latency
  Improvement: 4.8x faster! 🚀

Storage Savings:
  Removed redundant data: 1.2 GB
  Index overhead: +3.4 GB
  Net: -1.2 GB + better performance

Next Steps:
  1. Clean up invalid data
  2. Re-run fix for skipped constraints
  3. Monitor performance for 24 hours
  4. Consider partitioning (next phase)
```

---

## Advanced Patterns

### Pattern 1: Schema Versioning

```bash
# Track schema changes over time
aishell schema version init

# Create new version
aishell schema version create "Add user preferences table"
```

**Version Control:**

```
📚 Schema Version History
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

v1.0.0 (2025-09-01)
  Initial schema
  16 tables, 42 indexes

v1.1.0 (2025-09-15)
  Added user preferences
  +1 table, +3 indexes

v1.2.0 (2025-10-01)
  Optimized orders table
  +5 indexes, partitioned by month

v1.3.0 (2025-10-27) ← Current
  Added full-text search
  +4 GIN indexes

Next version (draft):
  - Add multi-currency support
  - Add internationalization
```

### Pattern 2: Schema Comparison

```bash
# Compare schemas between environments
aishell schema diff staging production
```

**Diff Output:**

```
📊 Schema Diff: staging → production
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Differences: 12

Tables:
  + user_preferences (in staging, not in production)
  ~ orders (different schema)

Columns:
  orders:
    + payment_method VARCHAR(50) (in staging)
    ~ status: VARCHAR(20) → ENUM order_status

Indexes:
  + idx_orders_payment_method (in staging)
  - idx_orders_old_status (in production, removed in staging)

Constraints:
  + check_payment_method_valid (in staging)

Data:
  ~ Migration required: 12.4M rows affected

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate migration to sync production → staging?
  aishell schema migrate staging production --preview
```

### Pattern 3: AI-Powered Refactoring

```bash
# Ask AI to refactor schema
aishell schema refactor "
  Optimize for multi-tenancy.
  Each company should have isolated data.
  Support for 10,000 tenants.
"
```

**Refactoring Plan:**

```
🤖 AI Refactoring Plan: Multi-Tenancy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current: Shared schema (all companies in same tables)
Target: Row-level isolation with tenant_id

Strategy: Add tenant_id column to all tables

Changes Required:

1. Add companies table
   ```sql
   CREATE TABLE companies (
       id BIGSERIAL PRIMARY KEY,
       name VARCHAR(255) NOT NULL,
       subdomain VARCHAR(100) UNIQUE NOT NULL,
       created_at TIMESTAMP DEFAULT NOW()
   );
   ```

2. Add tenant_id to existing tables
   - users: + company_id
   - products: + company_id
   - orders: + company_id
   (13 tables total)

3. Add row-level security
   ```sql
   ALTER TABLE users ENABLE ROW LEVEL SECURITY;
   CREATE POLICY tenant_isolation ON users
       USING (company_id = current_setting('app.current_company_id')::BIGINT);
   ```

4. Update all foreign keys to include company_id

5. Update indexes to include company_id as first column
   - For optimal query performance
   - For partition pruning

6. Add company_id to all unique constraints
   - Ensures uniqueness within tenant, not globally

Performance Impact:
  + Better isolation (security)
  + Partition by company_id possible
  - Slightly larger indexes (+15%)
  - Need to SET company_id in all sessions

Migration Complexity: MEDIUM
Estimated time: 4-6 hours
Requires application code changes: YES

Apply refactoring? (y/n): _
```

---

## Best Practices

### 1. Start with Requirements

```bash
# Always begin with business requirements
aishell schema requirements "
  - Support 1M users
  - Handle 10K orders/day
  - Need search across products
  - Must support multiple currencies
  - Need audit trail
"

# AI will suggest optimal schema based on requirements
```

### 2. Use AI Patterns

```bash
# Leverage pre-built patterns
aishell schema pattern apply e-commerce
aishell schema pattern apply social-network
aishell schema pattern apply saas-multi-tenant
```

### 3. Validate Before Deploy

```bash
# Always validate schema
aishell schema validate

# Test with realistic data
aishell schema test --data-size 1M

# Benchmark performance
aishell schema benchmark
```

### 4. Document Everything

```bash
# AI generates documentation
aishell schema document --format markdown > schema-docs.md
aishell schema document --format html > schema-docs.html
aishell schema diagram --format png > schema-diagram.png
```

### 5. Version Control

```bash
# Track all schema changes
aishell schema version commit "Description of changes"

# Easy rollback
aishell schema version rollback v1.2.0
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Over-Normalization

**Problem:** Too many tables, too many joins

**Solution:**

```bash
# AI detects over-normalization
aishell schema analyze --check-normalization

⚠️  Over-normalized: address_street, address_city, address_state in separate tables
    Recommendation: Denormalize into single addresses table
```

### Pitfall 2: No Indexes on Foreign Keys

**Problem:** Slow joins

**Solution:**

```bash
# AI auto-detects and suggests indexes
aishell schema analyze --check-indexes

🚨 Missing indexes on foreign keys:
   + CREATE INDEX idx_orders_user_id ON orders(user_id);
```

### Pitfall 3: Wrong Data Types

**Problem:** Using VARCHAR for everything

**Solution:**

```bash
# AI optimizes data types
aishell schema optimize-types

💡 Optimizations:
   age: INT → SMALLINT (saves 6 MB)
   is_active: CHAR(1) → BOOLEAN
   status: VARCHAR(50) → ENUM
```

---

## Troubleshooting

### Issue 1: "Schema too complex"

```bash
# Simplify schema
aishell schema simplify --max-tables 20
```

### Issue 2: "Migration failing"

```bash
# Analyze migration
aishell schema migration analyze

# Fix issues
aishell schema migration fix --auto
```

### Issue 3: "Performance still slow after optimization"

```bash
# Deep analysis
aishell schema analyze --deep --with-query-patterns

# AI will suggest advanced optimizations
```

---

## Summary

**Key Takeaways:**

- ✅ AI-powered schema design from requirements
- ✅ Automatic optimization and best practices
- ✅ Schema analysis and improvement suggestions
- ✅ Version control and migration management
- ✅ Visual diagrams and documentation

**Next Steps:**

1. Try the [Migration Tester Tutorial](./07-migration-tester.md) for safe migrations
2. Learn about [Schema Diff](./09-schema-diff.md) for tracking changes
3. Explore [SQL Explainer](./08-sql-explainer.md) for understanding queries

**Real Results:**

> "AI-Shell designed our entire schema in 20 minutes. It would've taken us 2 weeks and multiple revisions." - David Park, Tech Lead

---

## Quick Commands Cheat Sheet

```bash
# Design new schema
aishell schema design "description"

# Analyze existing schema
aishell schema analyze

# Generate SQL
aishell schema generate sql

# Compare schemas
aishell schema diff env1 env2

# Apply fixes
aishell schema fix --apply-all

# Version control
aishell schema version create "message"

# Generate documentation
aishell schema document

# Create diagram
aishell schema diagram
```

**Pro Tip:** Use AI patterns for common schemas - they've been battle-tested at scale! 🏗️
