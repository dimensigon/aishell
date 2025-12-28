# Part 8: Complete End-to-End Scenarios

**Level:** Expert
**Duration:** 90-120 minutes
**Prerequisites:** Parts 1-7 completed

## Overview

This tutorial presents three complete, realistic scenarios that demonstrate AI-Shell's capabilities in production environments. Each scenario includes setup, implementation, optimization, and best practices.

## Table of Contents

1. [Scenario 1: E-commerce Analytics Platform](#scenario-1-ecommerce-analytics-platform)
2. [Scenario 2: Enterprise Security Audit](#scenario-2-enterprise-security-audit)
3. [Scenario 3: Database Migration Project](#scenario-3-database-migration-project)
4. [Bonus: Multi-Cloud Data Integration](#bonus-multi-cloud-data-integration)

---

## Scenario 1: E-commerce Analytics Platform

### Business Context

**Company:** GlobalMart
**Challenge:** Analyze sales across multiple databases with real-time dashboards
**Tech Stack:**
- PostgreSQL: Order and customer data
- MongoDB: Product catalog and reviews
- Redis: Cache and session data
- Elasticsearch: Search logs

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   AI-Shell Platform                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ PostgreSQL   │  │   MongoDB    │  │   Redis   │ │
│  │   Orders     │  │   Products   │  │   Cache   │ │
│  │  Customers   │  │   Reviews    │  │  Sessions │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │         GraphQL API & Query Engine             │ │
│  │  - Multi-DB Queries  - Joins  - Aggregations  │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │          Real-time Dashboards                  │ │
│  │  - Sales KPIs  - Product Analytics  - Trends  │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Step 1: Environment Setup

**1.1 Database Preparation**

```bash
# Create project directory
mkdir -p /home/claude/AIShell/scenarios/ecommerce
cd /home/claude/AIShell/scenarios/ecommerce

# Start databases with Docker Compose
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ecommerce
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secure_pass
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./init-postgres.sql:/docker-entrypoint-initdb.d/init.sql

  mongodb:
    image: mongo:6
    environment:
      MONGO_INITDB_DATABASE: products
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: secure_pass
    ports:
      - "27017:27017"
    volumes:
      - ./data/mongodb:/data/db

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data

  elasticsearch:
    image: elasticsearch:8.9.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - ./data/elasticsearch:/usr/share/elasticsearch/data

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
  elasticsearch_data:
EOF

docker-compose up -d
```

**1.2 PostgreSQL Schema**

Create `init-postgres.sql`:

```sql
-- Customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    segment VARCHAR(50), -- VIP, Regular, New
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lifetime_value DECIMAL(10, 2) DEFAULT 0
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL, -- pending, processing, completed, cancelled
    total DECIMAL(10, 2) NOT NULL,
    tax DECIMAL(10, 2) DEFAULT 0,
    shipping DECIMAL(10, 2) DEFAULT 0,
    payment_method VARCHAR(50),
    shipping_country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at);
CREATE INDEX idx_orders_status_date ON orders(status, created_at);

-- Order items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id VARCHAR(50) NOT NULL, -- MongoDB reference
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(5, 2) DEFAULT 0
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- Payments table
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    amount DECIMAL(10, 2) NOT NULL,
    method VARCHAR(50),
    status VARCHAR(50),
    transaction_id VARCHAR(255),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics aggregates table (materialized view)
CREATE TABLE daily_sales (
    date DATE PRIMARY KEY,
    total_orders INTEGER,
    total_revenue DECIMAL(12, 2),
    avg_order_value DECIMAL(10, 2),
    unique_customers INTEGER,
    completed_orders INTEGER,
    cancelled_orders INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function to update daily sales
CREATE OR REPLACE FUNCTION update_daily_sales()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO daily_sales (
        date,
        total_orders,
        total_revenue,
        avg_order_value,
        unique_customers,
        completed_orders,
        cancelled_orders
    )
    SELECT
        DATE(created_at),
        COUNT(*),
        SUM(total),
        AVG(total),
        COUNT(DISTINCT customer_id),
        COUNT(*) FILTER (WHERE status = 'completed'),
        COUNT(*) FILTER (WHERE status = 'cancelled')
    FROM orders
    WHERE DATE(created_at) = DATE(NEW.created_at)
    GROUP BY DATE(created_at)
    ON CONFLICT (date) DO UPDATE SET
        total_orders = EXCLUDED.total_orders,
        total_revenue = EXCLUDED.total_revenue,
        avg_order_value = EXCLUDED.avg_order_value,
        unique_customers = EXCLUDED.unique_customers,
        completed_orders = EXCLUDED.completed_orders,
        cancelled_orders = EXCLUDED.cancelled_orders,
        updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_daily_sales
AFTER INSERT OR UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION update_daily_sales();

-- Generate sample data
INSERT INTO customers (email, name, country, segment, lifetime_value)
SELECT
    'customer' || i || '@example.com',
    'Customer ' || i,
    CASE (i % 5)
        WHEN 0 THEN 'USA'
        WHEN 1 THEN 'UK'
        WHEN 2 THEN 'Canada'
        WHEN 3 THEN 'Germany'
        ELSE 'France'
    END,
    CASE
        WHEN i % 10 = 0 THEN 'VIP'
        WHEN i % 3 = 0 THEN 'Regular'
        ELSE 'New'
    END,
    RANDOM() * 10000
FROM generate_series(1, 1000) i;

-- Generate sample orders (last 90 days)
INSERT INTO orders (customer_id, order_number, status, total, tax, shipping, payment_method, shipping_country, created_at)
SELECT
    (RANDOM() * 999 + 1)::INTEGER,
    'ORD-' || LPAD(i::TEXT, 8, '0'),
    CASE (RANDOM() * 100)::INTEGER % 10
        WHEN 0 THEN 'cancelled'
        WHEN 1 THEN 'pending'
        WHEN 2 THEN 'processing'
        ELSE 'completed'
    END,
    (RANDOM() * 500 + 50)::DECIMAL(10,2),
    (RANDOM() * 50)::DECIMAL(10,2),
    (RANDOM() * 20 + 5)::DECIMAL(10,2),
    CASE (RANDOM() * 3)::INTEGER
        WHEN 0 THEN 'credit_card'
        WHEN 1 THEN 'paypal'
        ELSE 'bank_transfer'
    END,
    CASE (RANDOM() * 5)::INTEGER
        WHEN 0 THEN 'USA'
        WHEN 1 THEN 'UK'
        WHEN 2 THEN 'Canada'
        WHEN 3 THEN 'Germany'
        ELSE 'France'
    END,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '90 days')
FROM generate_series(1, 5000) i;

-- Generate order items
INSERT INTO order_items (order_id, product_id, quantity, price, discount)
SELECT
    o.id,
    'PROD-' || LPAD((RANDOM() * 100 + 1)::INTEGER::TEXT, 3, '0'),
    (RANDOM() * 5 + 1)::INTEGER,
    (RANDOM() * 200 + 10)::DECIMAL(10,2),
    (RANDOM() * 20)::DECIMAL(5,2)
FROM orders o
CROSS JOIN generate_series(1, (RANDOM() * 3 + 1)::INTEGER) item_num;
```

**1.3 MongoDB Setup**

Create `init-mongodb.js`:

```javascript
// Connect to MongoDB
db = db.getSiblingDB('products');

// Create products collection
db.products.insertMany([
  {
    product_id: "PROD-001",
    name: "Wireless Headphones",
    category: "Electronics",
    price: 149.99,
    cost: 75.00,
    stock: 245,
    attributes: {
      brand: "SoundPro",
      color: ["Black", "White", "Blue"],
      wireless: true,
      battery_life: "30 hours"
    },
    reviews: [
      { user: "user123", rating: 5, comment: "Excellent sound quality!", date: new Date("2024-01-10") },
      { user: "user456", rating: 4, comment: "Good value for money", date: new Date("2024-01-15") }
    ],
    images: ["url1.jpg", "url2.jpg"],
    created_at: new Date("2023-06-01"),
    updated_at: new Date("2024-01-20")
  }
  // Add 99 more products programmatically
]);

// Generate 100 products
for (let i = 2; i <= 100; i++) {
  const categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"];
  const brands = ["BrandA", "BrandB", "BrandC", "BrandD", "BrandE"];

  db.products.insert({
    product_id: `PROD-${String(i).padStart(3, '0')}`,
    name: `Product ${i}`,
    category: categories[i % categories.length],
    price: Math.random() * 500 + 20,
    cost: Math.random() * 200 + 10,
    stock: Math.floor(Math.random() * 500),
    attributes: {
      brand: brands[i % brands.length],
      weight: Math.random() * 5 + 0.5,
      dimensions: {
        length: Math.random() * 50 + 10,
        width: Math.random() * 50 + 10,
        height: Math.random() * 50 + 10
      }
    },
    reviews: [
      {
        user: `user${Math.floor(Math.random() * 1000)}`,
        rating: Math.floor(Math.random() * 5) + 1,
        comment: "Sample review",
        date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000)
      }
    ],
    images: [`product${i}_1.jpg`, `product${i}_2.jpg`],
    created_at: new Date(Date.now() - Math.random() * 730 * 24 * 60 * 60 * 1000),
    updated_at: new Date()
  });
}

// Create indexes
db.products.createIndex({ product_id: 1 }, { unique: true });
db.products.createIndex({ category: 1 });
db.products.createIndex({ price: 1 });
db.products.createIndex({ "attributes.brand": 1 });
db.products.createIndex({ "reviews.rating": 1 });

print("MongoDB initialization complete!");
```

**1.4 AI-Shell Configuration**

Create `config/ecommerce-config.yaml`:

```yaml
name: "E-commerce Analytics Platform"
version: "1.0.0"

databases:
  postgres_orders:
    type: postgresql
    host: localhost
    port: 5432
    database: ecommerce
    username: admin
    password: secure_pass
    pool:
      min: 5
      max: 20
    ssl: false

  mongodb_products:
    type: mongodb
    host: localhost
    port: 27017
    database: products
    username: admin
    password: secure_pass
    auth_source: admin

  redis_cache:
    type: redis
    host: localhost
    port: 6379
    database: 0
    ttl: 300

api:
  enabled: true
  port: 8080
  graphql:
    enabled: true
    playground: true

  auth:
    enabled: true
    jwt_secret: "${JWT_SECRET}"

  rate_limiting:
    enabled: true
    max_requests: 1000
    window_seconds: 60

caching:
  enabled: true
  backend: redis
  default_ttl: 300
  strategies:
    - pattern: "sales_*"
      ttl: 60
    - pattern: "product_*"
      ttl: 600

monitoring:
  enabled: true
  metrics_port: 9090
  slow_query_threshold: 1000
  log_level: info
```

### Step 2: Multi-Database Queries

**2.1 Start AI-Shell**

```bash
# Load configuration and start
ai-shell --config config/ecommerce-config.yaml

# Or with environment variables
export JWT_SECRET="your-secret-key"
ai-shell --config config/ecommerce-config.yaml --api --web
```

**2.2 Complex JOIN Query (PostgreSQL)**

```sql
-- Top customers by revenue with order statistics
WITH customer_stats AS (
    SELECT
        c.id,
        c.name,
        c.email,
        c.segment,
        c.country,
        COUNT(DISTINCT o.id) as total_orders,
        SUM(CASE WHEN o.status = 'completed' THEN o.total ELSE 0 END) as total_revenue,
        AVG(CASE WHEN o.status = 'completed' THEN o.total ELSE NULL END) as avg_order_value,
        MAX(o.created_at) as last_order_date,
        COUNT(DISTINCT CASE WHEN o.created_at >= CURRENT_DATE - INTERVAL '30 days'
              THEN o.id ELSE NULL END) as orders_last_30_days
    FROM customers c
    LEFT JOIN orders o ON c.id = o.customer_id
    GROUP BY c.id, c.name, c.email, c.segment, c.country
)
SELECT
    cs.*,
    CASE
        WHEN cs.orders_last_30_days >= 3 THEN 'Highly Active'
        WHEN cs.orders_last_30_days >= 1 THEN 'Active'
        ELSE 'Inactive'
    END as activity_status,
    RANK() OVER (ORDER BY cs.total_revenue DESC) as revenue_rank
FROM customer_stats cs
WHERE cs.total_revenue > 0
ORDER BY cs.total_revenue DESC
LIMIT 100;
```

**2.3 Product Performance Analysis (Cross-Database)**

```javascript
// GraphQL Query combining PostgreSQL and MongoDB
query ProductPerformanceAnalysis {
  productAnalytics(
    dateRange: {
      start: "2024-01-01"
      end: "2024-12-31"
    }
  ) {
    productId

    # From MongoDB
    productDetails {
      name
      category
      brand
      currentPrice
      costPrice
      stockLevel
      averageReview
      reviewCount
    }

    # From PostgreSQL
    salesMetrics {
      totalOrders
      totalQuantity
      totalRevenue
      averageOrderValue
      profitMargin
      returnRate
    }

    # Calculated fields
    performance {
      revenueRank
      profitability
      turnoverRate
      stockDays
      popularityScore
    }
  }
}
```

**Resolver Implementation:**

```javascript
// File: /home/claude/AIShell/scenarios/ecommerce/resolvers/productAnalytics.js

const { DataLoader } = require('dataloader');

const productAnalytics = async (_, { dateRange }, context) => {
  // Query PostgreSQL for sales data
  const salesQuery = `
    SELECT
      oi.product_id,
      COUNT(DISTINCT oi.order_id) as total_orders,
      SUM(oi.quantity) as total_quantity,
      SUM(oi.price * oi.quantity * (1 - oi.discount/100)) as total_revenue,
      AVG(oi.price) as avg_price
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.id
    WHERE o.status = 'completed'
      AND o.created_at BETWEEN $1 AND $2
    GROUP BY oi.product_id
    ORDER BY total_revenue DESC
  `;

  const salesData = await context.postgres.query(
    salesQuery,
    [dateRange.start, dateRange.end]
  );

  // Query MongoDB for product details
  const productIds = salesData.rows.map(r => r.product_id);
  const products = await context.mongodb
    .collection('products')
    .find({ product_id: { $in: productIds } })
    .toArray();

  // Combine data
  return salesData.rows.map((sale, index) => {
    const product = products.find(p => p.product_id === sale.product_id);

    const avgReview = product?.reviews?.length > 0
      ? product.reviews.reduce((sum, r) => sum + r.rating, 0) / product.reviews.length
      : 0;

    const profitMargin = product?.cost
      ? ((sale.avg_price - product.cost) / sale.avg_price) * 100
      : 0;

    return {
      productId: sale.product_id,

      productDetails: {
        name: product?.name || 'Unknown',
        category: product?.category || 'Uncategorized',
        brand: product?.attributes?.brand || 'Unknown',
        currentPrice: product?.price || 0,
        costPrice: product?.cost || 0,
        stockLevel: product?.stock || 0,
        averageReview: avgReview,
        reviewCount: product?.reviews?.length || 0
      },

      salesMetrics: {
        totalOrders: parseInt(sale.total_orders),
        totalQuantity: parseInt(sale.total_quantity),
        totalRevenue: parseFloat(sale.total_revenue),
        averageOrderValue: parseFloat(sale.avg_price),
        profitMargin: profitMargin,
        returnRate: 0 // Would need returns data
      },

      performance: {
        revenueRank: index + 1,
        profitability: profitMargin > 30 ? 'High' : profitMargin > 15 ? 'Medium' : 'Low',
        turnoverRate: product?.stock > 0
          ? (parseInt(sale.total_quantity) / product.stock) * 100
          : 0,
        stockDays: product?.stock > 0
          ? (product.stock / (parseInt(sale.total_quantity) / 90))
          : 0,
        popularityScore: (
          (parseInt(sale.total_orders) * 0.4) +
          (avgReview * 10 * 0.3) +
          (parseInt(sale.total_quantity) * 0.3)
        )
      }
    };
  });
};

module.exports = { productAnalytics };
```

### Step 3: Performance Optimization

**3.1 Query Optimization**

```sql
-- Before: Slow query (15 seconds)
SELECT
    c.name,
    COUNT(o.id) as order_count,
    SUM(o.total) as total_spent
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE o.status = 'completed'
GROUP BY c.id, c.name
ORDER BY total_spent DESC;

-- After: Optimized query (0.3 seconds)
-- Add indexes
CREATE INDEX CONCURRENTLY idx_orders_customer_status
ON orders(customer_id, status)
INCLUDE (total);

-- Use materialized view for aggregates
CREATE MATERIALIZED VIEW customer_lifetime_value AS
SELECT
    c.id as customer_id,
    c.name,
    c.email,
    COUNT(o.id) as order_count,
    SUM(o.total) as total_spent,
    AVG(o.total) as avg_order_value,
    MAX(o.created_at) as last_order_date
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE o.status = 'completed'
GROUP BY c.id, c.name, c.email;

CREATE UNIQUE INDEX ON customer_lifetime_value(customer_id);

-- Refresh materialized view
REFRESH MATERIALIZED VIEW CONCURRENTLY customer_lifetime_value;

-- Create refresh function (runs hourly)
CREATE OR REPLACE FUNCTION refresh_customer_ltv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY customer_lifetime_value;
END;
$$ LANGUAGE plpgsql;

-- Query the view (fast!)
SELECT * FROM customer_lifetime_value
ORDER BY total_spent DESC
LIMIT 100;
```

**3.2 Caching Strategy**

```javascript
// File: /home/claude/AIShell/scenarios/ecommerce/middleware/cache.js

const Redis = require('ioredis');
const redis = new Redis({
  host: 'localhost',
  port: 6379
});

const cacheMiddleware = {
  // Cache expensive queries
  async cacheQuery(key, queryFn, ttl = 300) {
    const cached = await redis.get(key);

    if (cached) {
      console.log(`Cache HIT: ${key}`);
      return JSON.parse(cached);
    }

    console.log(`Cache MISS: ${key}`);
    const result = await queryFn();

    await redis.setex(key, ttl, JSON.stringify(result));
    return result;
  },

  // Invalidate cache on mutations
  async invalidatePattern(pattern) {
    const keys = await redis.keys(pattern);
    if (keys.length > 0) {
      await redis.del(...keys);
      console.log(`Invalidated ${keys.length} cache keys: ${pattern}`);
    }
  },

  // Multi-level caching
  async getOrSetMulti(keys, fetchFn) {
    // Try to get all from cache
    const cached = await redis.mget(...keys);
    const missing = [];
    const results = {};

    keys.forEach((key, i) => {
      if (cached[i]) {
        results[key] = JSON.parse(cached[i]);
      } else {
        missing.push(key);
      }
    });

    // Fetch missing data
    if (missing.length > 0) {
      const freshData = await fetchFn(missing);

      // Cache new data
      const pipeline = redis.pipeline();
      Object.entries(freshData).forEach(([key, value]) => {
        pipeline.setex(key, 300, JSON.stringify(value));
        results[key] = value;
      });
      await pipeline.exec();
    }

    return results;
  }
};

// Usage in resolver
const getDashboardData = async () => {
  return cacheMiddleware.cacheQuery(
    'dashboard:overview',
    async () => {
      // Expensive query
      const data = await db.query(`
        SELECT /* complex query */ FROM orders ...
      `);
      return data.rows;
    },
    60 // Cache for 1 minute
  );
};

// Invalidate on order creation
const createOrder = async (orderData) => {
  const result = await db.query('INSERT INTO orders ...');

  // Invalidate related caches
  await cacheMiddleware.invalidatePattern('dashboard:*');
  await cacheMiddleware.invalidatePattern('sales:*');

  return result;
};

module.exports = cacheMiddleware;
```

**3.3 Database Connection Pooling**

```javascript
// File: /home/claude/AIShell/scenarios/ecommerce/config/database.js

const { Pool } = require('pg');
const { MongoClient } = require('mongodb');

// PostgreSQL connection pool
const pgPool = new Pool({
  host: 'localhost',
  port: 5432,
  database: 'ecommerce',
  user: 'admin',
  password: 'secure_pass',

  // Pool configuration
  min: 5,              // Minimum connections
  max: 20,             // Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,

  // Performance tuning
  statement_timeout: 10000, // 10 seconds max query time
  query_timeout: 10000,

  // Logging
  log: (msg) => console.log('PG Pool:', msg)
});

// MongoDB connection pool
const mongoClient = new MongoClient('mongodb://admin:secure_pass@localhost:27017', {
  maxPoolSize: 50,
  minPoolSize: 10,
  maxIdleTimeMS: 30000,
  serverSelectionTimeoutMS: 5000,
  socketTimeoutMS: 45000,
});

// Health check
const checkConnections = async () => {
  try {
    // Test PostgreSQL
    const pgResult = await pgPool.query('SELECT NOW()');
    console.log('PostgreSQL connected:', pgResult.rows[0].now);

    // Test MongoDB
    await mongoClient.connect();
    const mongoDb = mongoClient.db('products');
    const mongoResult = await mongoDb.admin().ping();
    console.log('MongoDB connected:', mongoResult.ok);

  } catch (error) {
    console.error('Database connection error:', error);
    throw error;
  }
};

module.exports = {
  pgPool,
  mongoClient,
  checkConnections
};
```

### Step 4: Real-time Dashboard

**4.1 Dashboard Configuration**

Create `dashboards/sales-realtime.yaml`:

```yaml
name: "Real-time Sales Dashboard"
refresh_interval: 30  # seconds
layout: grid

widgets:
  # Row 1: KPIs
  - id: revenue_today
    type: kpi_card
    title: "Revenue Today"
    position: { x: 0, y: 0, w: 3, h: 2 }
    query: |
      SELECT SUM(total) as value
      FROM orders
      WHERE DATE(created_at) = CURRENT_DATE
      AND status = 'completed'
    format: currency
    comparison:
      query: |
        SELECT SUM(total) FROM orders
        WHERE DATE(created_at) = CURRENT_DATE - 1
        AND status = 'completed'
      show_trend: true
      show_percentage: true
    refresh: 30

  - id: orders_today
    type: kpi_card
    title: "Orders Today"
    position: { x: 3, y: 0, w: 3, h: 2 }
    query: |
      SELECT COUNT(*) as value
      FROM orders
      WHERE DATE(created_at) = CURRENT_DATE
    format: number
    refresh: 30

  - id: avg_order_value
    type: kpi_card
    title: "Avg Order Value"
    position: { x: 6, y: 0, w: 3, h: 2 }
    query: |
      SELECT AVG(total) as value
      FROM orders
      WHERE DATE(created_at) = CURRENT_DATE
      AND status = 'completed'
    format: currency
    refresh: 30

  - id: conversion_rate
    type: kpi_card
    title: "Conversion Rate"
    position: { x: 9, y: 0, w: 3, h: 2 }
    query: |
      SELECT
        ROUND(
          COUNT(*) FILTER (WHERE status = 'completed')::DECIMAL /
          NULLIF(COUNT(*), 0) * 100,
          2
        ) as value
      FROM orders
      WHERE DATE(created_at) = CURRENT_DATE
    format: percentage
    refresh: 30

  # Row 2: Time series
  - id: revenue_timeline
    type: line_chart
    title: "Revenue (Last 24 Hours)"
    position: { x: 0, y: 2, w: 8, h: 4 }
    query: |
      SELECT
        DATE_TRUNC('hour', created_at) as time,
        SUM(total) as revenue,
        COUNT(*) as orders
      FROM orders
      WHERE created_at >= NOW() - INTERVAL '24 hours'
      AND status = 'completed'
      GROUP BY DATE_TRUNC('hour', created_at)
      ORDER BY time
    x_axis: time
    y_axes:
      - field: revenue
        label: "Revenue ($)"
        color: "#4CAF50"
      - field: orders
        label: "Orders"
        color: "#2196F3"
        yAxisID: secondary
    refresh: 30

  - id: order_status
    type: pie_chart
    title: "Order Status"
    position: { x: 8, y: 2, w: 4, h: 4 }
    query: |
      SELECT
        status,
        COUNT(*) as count
      FROM orders
      WHERE created_at >= NOW() - INTERVAL '24 hours'
      GROUP BY status
    label_field: status
    value_field: count
    colors:
      completed: "#4CAF50"
      processing: "#FFC107"
      pending: "#2196F3"
      cancelled: "#F44336"
    refresh: 30

  # Row 3: Product and Geography
  - id: top_products
    type: bar_chart
    title: "Top 10 Products (Today)"
    position: { x: 0, y: 6, w: 6, h: 4 }
    query: |
      SELECT
        p.name,
        SUM(oi.quantity) as units_sold,
        SUM(oi.price * oi.quantity) as revenue
      FROM order_items oi
      JOIN orders o ON oi.order_id = o.id
      -- Join with MongoDB data (handled by AI-Shell)
      WHERE DATE(o.created_at) = CURRENT_DATE
      AND o.status = 'completed'
      GROUP BY p.product_id, p.name
      ORDER BY revenue DESC
      LIMIT 10
    x_axis: name
    y_axis: revenue
    refresh: 60

  - id: sales_by_country
    type: map
    title: "Sales by Country"
    position: { x: 6, y: 6, w: 6, h: 4 }
    query: |
      SELECT
        shipping_country as country,
        COUNT(*) as orders,
        SUM(total) as revenue
      FROM orders
      WHERE DATE(created_at) = CURRENT_DATE
      GROUP BY shipping_country
    geo_field: country
    value_field: revenue
    refresh: 60

  # Row 4: Customer and Activity
  - id: customer_segments
    type: stacked_bar_chart
    title: "Orders by Customer Segment"
    position: { x: 0, y: 10, w: 6, h: 4 }
    query: |
      SELECT
        DATE(o.created_at) as date,
        c.segment,
        COUNT(*) as orders,
        SUM(o.total) as revenue
      FROM orders o
      JOIN customers c ON o.customer_id = c.id
      WHERE o.created_at >= CURRENT_DATE - INTERVAL '7 days'
      GROUP BY DATE(o.created_at), c.segment
      ORDER BY date
    x_axis: date
    stack_by: segment
    y_axis: orders
    refresh: 120

  - id: recent_orders
    type: table
    title: "Recent Orders"
    position: { x: 6, y: 10, w: 6, h: 4 }
    query: |
      SELECT
        o.order_number,
        c.name as customer,
        o.total,
        o.status,
        o.created_at
      FROM orders o
      JOIN customers c ON o.customer_id = c.id
      ORDER BY o.created_at DESC
      LIMIT 20
    columns:
      - field: order_number
        label: "Order #"
        width: 120
      - field: customer
        label: "Customer"
        width: 200
      - field: total
        label: "Total"
        format: currency
        width: 100
      - field: status
        label: "Status"
        width: 120
        render: badge
      - field: created_at
        label: "Created"
        format: datetime
        width: 150
    refresh: 15

filters:
  - name: date_range
    type: daterange
    default: today

  - name: country
    type: multiselect
    query: "SELECT DISTINCT shipping_country FROM orders"
    label: "Country"

  - name: status
    type: multiselect
    options: [pending, processing, completed, cancelled]
    label: "Status"

alerts:
  - name: low_revenue_alert
    condition: revenue_today.value < 10000
    severity: warning
    notification:
      type: email
      recipients: ["manager@globalmart.com"]
      message: "Daily revenue is below threshold"

  - name: high_cancellation_rate
    condition: |
      (SELECT COUNT(*) FROM orders
       WHERE status = 'cancelled'
       AND DATE(created_at) = CURRENT_DATE) > 50
    severity: critical
    notification:
      type: slack
      channel: "#alerts"
      message: "High cancellation rate detected"
```

**4.2 Launch Dashboard**

```bash
# Start AI-Shell with dashboard
ai-shell --config config/ecommerce-config.yaml \
         --dashboard dashboards/sales-realtime.yaml \
         --web --port 3000

# Access dashboard
open http://localhost:3000/dashboards/sales-realtime
```

### Step 5: Testing and Validation

**5.1 Load Testing**

Create `tests/load-test.js`:

```javascript
// Using Apache Bench or k6
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp up to 200 users
    { duration: '5m', target: 200 },  // Stay at 200 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Error rate under 1%
  },
};

export default function () {
  // Test GraphQL query
  const query = `
    query DashboardData {
      revenueToday
      ordersToday
      topProducts(limit: 10) {
        name
        revenue
      }
    }
  `;

  const res = http.post('http://localhost:8080/graphql', {
    query: query
  }, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_TOKEN'
    }
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time OK': (r) => r.timings.duration < 500,
    'has data': (r) => JSON.parse(r.body).data !== null,
  });

  sleep(1);
}
```

Run load test:

```bash
k6 run tests/load-test.js
```

**5.2 Data Validation**

```sql
-- Validate data consistency
WITH postgres_totals AS (
    SELECT
        COUNT(*) as order_count,
        SUM(total) as total_revenue
    FROM orders
    WHERE status = 'completed'
),
redis_cache AS (
    -- Check cache values match
    SELECT
        get('dashboard:orders:completed') as cached_orders,
        get('dashboard:revenue:total') as cached_revenue
)
SELECT
    pt.order_count,
    rc.cached_orders::INTEGER as cached_count,
    CASE
        WHEN pt.order_count = rc.cached_orders::INTEGER THEN 'OK'
        ELSE 'MISMATCH'
    END as validation_status
FROM postgres_totals pt
CROSS JOIN redis_cache rc;
```

### Challenge Exercise 1

**Task:** Implement a real-time inventory management system that:
1. Tracks product stock levels across warehouses
2. Alerts when stock is low
3. Predicts stockouts based on sales trends
4. Suggests reorder quantities

**Deliverables:**
- Database schema for warehouse inventory
- Real-time dashboard showing stock levels
- Alert system for low stock
- Prediction algorithm implementation

---

## Scenario 2: Enterprise Security Audit

### Business Context

**Company:** SecureBank
**Challenge:** Implement comprehensive security auditing and compliance
**Requirements:**
- Multi-tenant RBAC
- Complete audit logging
- Anomaly detection
- Compliance reporting (SOX, GDPR, PCI-DSS)

### Architecture

```
┌──────────────────────────────────────────────────┐
│          Security & Compliance Layer             │
├──────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │
│  │   RBAC       │  │ Audit Logs   │  │ Alerts │ │
│  │  Engine      │  │   Storage    │  │ System │ │
│  └──────────────┘  └──────────────┘  └────────┘ │
│                                                   │
│  ┌──────────────────────────────────────────┐   │
│  │        Anomaly Detection Engine          │   │
│  │  - Pattern Recognition                   │   │
│  │  - Behavioral Analysis                   │   │
│  │  - Threat Detection                      │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  ┌──────────────────────────────────────────┐   │
│  │       Compliance Reporting               │   │
│  │  - SOX  - GDPR  - PCI-DSS  - HIPAA      │   │
│  └──────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### Step 1: RBAC Implementation

**1.1 Database Schema**

```sql
-- Create security schema
CREATE SCHEMA IF NOT EXISTS security;

-- Roles table
CREATE TABLE security.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    level INTEGER NOT NULL, -- Hierarchy level
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Permissions table
CREATE TABLE security.permissions (
    id SERIAL PRIMARY KEY,
    resource VARCHAR(100) NOT NULL,  -- table, view, function
    action VARCHAR(50) NOT NULL,     -- SELECT, INSERT, UPDATE, DELETE
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resource, action)
);

-- Role permissions mapping
CREATE TABLE security.role_permissions (
    role_id INTEGER REFERENCES security.roles(id),
    permission_id INTEGER REFERENCES security.permissions(id),
    granted_by INTEGER REFERENCES security.users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

-- Users table
CREATE TABLE security.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES security.roles(id),
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log table
CREATE TABLE security.audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES security.users(id),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_user ON security.audit_log(user_id);
CREATE INDEX idx_audit_log_action ON security.audit_log(action);
CREATE INDEX idx_audit_log_created ON security.audit_log(created_at);
CREATE INDEX idx_audit_log_resource ON security.audit_log(resource);
CREATE INDEX idx_audit_log_details ON security.audit_log USING gin(details);

-- Data access log (row-level)
CREATE TABLE security.data_access_log (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES security.users(id),
    table_name VARCHAR(100) NOT NULL,
    row_id INTEGER,
    operation VARCHAR(20), -- SELECT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_access_table ON security.data_access_log(table_name);
CREATE INDEX idx_data_access_user ON security.data_access_log(user_id);
CREATE INDEX idx_data_access_time ON security.data_access_log(accessed_at);

-- Anomaly detection table
CREATE TABLE security.anomalies (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES security.users(id),
    anomaly_type VARCHAR(100),  -- unusual_access_time, high_volume, suspicious_pattern
    severity VARCHAR(20),       -- low, medium, high, critical
    details JSONB,
    confidence_score DECIMAL(5,4), -- 0.0000 to 1.0000
    investigated BOOLEAN DEFAULT false,
    investigator_id INTEGER REFERENCES security.users(id),
    resolution TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_anomalies_user ON security.anomalies(user_id);
CREATE INDEX idx_anomalies_type ON security.anomalies(anomaly_type);
CREATE INDEX idx_anomalies_severity ON security.anomalies(severity);
CREATE INDEX idx_anomalies_investigated ON security.anomalies(investigated);

-- Session tracking
CREATE TABLE security.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES security.users(id),
    token_hash VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT true
);

CREATE INDEX idx_sessions_user ON security.sessions(user_id);
CREATE INDEX idx_sessions_expires ON security.sessions(expires_at);
```

**1.2 Row-Level Security (RLS)**

```sql
-- Enable RLS on sensitive tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Customers can only see their own data
CREATE POLICY customer_isolation ON customers
    FOR SELECT
    USING (
        id = current_setting('app.current_user_id')::INTEGER
        OR
        current_setting('app.user_role') = 'admin'
    );

-- Department-based access
CREATE POLICY department_access ON orders
    FOR SELECT
    USING (
        customer_id IN (
            SELECT id FROM customers
            WHERE department = current_setting('app.user_department')
        )
        OR
        current_setting('app.user_role') IN ('admin', 'auditor')
    );

-- Auditors can read but not modify
CREATE POLICY auditor_readonly ON payments
    FOR SELECT
    USING (current_setting('app.user_role') = 'auditor');

CREATE POLICY no_auditor_modify ON payments
    FOR ALL
    USING (current_setting('app.user_role') != 'auditor')
    WITH CHECK (current_setting('app.user_role') != 'auditor');
```

**1.3 Audit Logging Functions**

```sql
-- Function to log all data access
CREATE OR REPLACE FUNCTION security.log_data_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO security.data_access_log (
        user_id,
        table_name,
        row_id,
        operation,
        old_values,
        new_values
    ) VALUES (
        COALESCE(current_setting('app.current_user_id', true)::INTEGER, 0),
        TG_TABLE_NAME,
        CASE
            WHEN TG_OP = 'DELETE' THEN OLD.id
            ELSE NEW.id
        END,
        TG_OP,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply to sensitive tables
CREATE TRIGGER audit_customers
AFTER INSERT OR UPDATE OR DELETE ON customers
FOR EACH ROW EXECUTE FUNCTION security.log_data_access();

CREATE TRIGGER audit_orders
AFTER INSERT OR UPDATE OR DELETE ON orders
FOR EACH ROW EXECUTE FUNCTION security.log_data_access();

CREATE TRIGGER audit_payments
AFTER INSERT OR UPDATE OR DELETE ON payments
FOR EACH ROW EXECUTE FUNCTION security.log_data_access();
```

### Step 2: Anomaly Detection

**2.1 Detection Algorithm**

Create `/home/claude/AIShell/scenarios/security/anomaly_detection.py`:

```python
import psycopg2
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
import json

class AnomalyDetector:
    def __init__(self, db_config):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()

    def detect_unusual_access_time(self, user_id, threshold=2.5):
        """Detect access outside normal hours for user"""
        query = """
            SELECT EXTRACT(HOUR FROM created_at) as hour
            FROM security.audit_log
            WHERE user_id = %s
            AND created_at >= NOW() - INTERVAL '30 days'
        """

        self.cursor.execute(query, (user_id,))
        hours = [row[0] for row in self.cursor.fetchall()]

        if len(hours) < 10:  # Need enough data
            return []

        # Calculate z-scores
        mean_hour = np.mean(hours)
        std_hour = np.std(hours)

        # Check recent access
        recent_query = """
            SELECT id, EXTRACT(HOUR FROM created_at) as hour, created_at
            FROM security.audit_log
            WHERE user_id = %s
            AND created_at >= NOW() - INTERVAL '24 hours'
        """

        self.cursor.execute(recent_query, (user_id,))
        anomalies = []

        for row in self.cursor.fetchall():
            log_id, hour, timestamp = row
            z_score = abs((hour - mean_hour) / std_hour) if std_hour > 0 else 0

            if z_score > threshold:
                anomalies.append({
                    'user_id': user_id,
                    'anomaly_type': 'unusual_access_time',
                    'severity': 'high' if z_score > 3 else 'medium',
                    'details': {
                        'log_id': log_id,
                        'hour': hour,
                        'z_score': float(z_score),
                        'timestamp': timestamp.isoformat()
                    },
                    'confidence_score': min(z_score / 5.0, 1.0)
                })

        return anomalies

    def detect_high_volume(self, user_id, threshold=3.0):
        """Detect unusually high query volume"""
        query = """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM security.audit_log
            WHERE user_id = %s
            AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
        """

        self.cursor.execute(query, (user_id,))
        daily_counts = [row[1] for row in self.cursor.fetchall()]

        if len(daily_counts) < 7:
            return []

        mean_count = np.mean(daily_counts)
        std_count = np.std(daily_counts)

        # Check today's volume
        today_query = """
            SELECT COUNT(*) FROM security.audit_log
            WHERE user_id = %s
            AND DATE(created_at) = CURRENT_DATE
        """

        self.cursor.execute(today_query, (user_id,))
        today_count = self.cursor.fetchone()[0]

        z_score = abs((today_count - mean_count) / std_count) if std_count > 0 else 0

        if z_score > threshold:
            return [{
                'user_id': user_id,
                'anomaly_type': 'high_volume',
                'severity': 'critical' if z_score > 4 else 'high',
                'details': {
                    'today_count': today_count,
                    'average_count': float(mean_count),
                    'z_score': float(z_score)
                },
                'confidence_score': min(z_score / 5.0, 1.0)
            }]

        return []

    def detect_suspicious_patterns(self, user_id):
        """Detect suspicious query patterns"""
        query = """
            SELECT action, resource, details
            FROM security.audit_log
            WHERE user_id = %s
            AND created_at >= NOW() - INTERVAL '1 hour'
            ORDER BY created_at
        """

        self.cursor.execute(query, (user_id,))
        recent_actions = self.cursor.fetchall()

        anomalies = []

        # Pattern 1: Rapid fire queries
        if len(recent_actions) > 100:
            anomalies.append({
                'user_id': user_id,
                'anomaly_type': 'rapid_fire_queries',
                'severity': 'high',
                'details': {
                    'count': len(recent_actions),
                    'timeframe': '1 hour'
                },
                'confidence_score': 0.9
            })

        # Pattern 2: Sequential table scanning
        tables = [a[1] for a in recent_actions if a[0] == 'SELECT']
        unique_tables = len(set(tables))
        if unique_tables > 20:
            anomalies.append({
                'user_id': user_id,
                'anomaly_type': 'table_enumeration',
                'severity': 'critical',
                'details': {
                    'tables_accessed': unique_tables,
                    'timeframe': '1 hour'
                },
                'confidence_score': 0.95
            })

        # Pattern 3: After-hours bulk export
        current_hour = datetime.now().hour
        if (current_hour < 6 or current_hour > 22):
            exports = [a for a in recent_actions if 'export' in str(a[2]).lower()]
            if len(exports) > 5:
                anomalies.append({
                    'user_id': user_id,
                    'anomaly_type': 'after_hours_export',
                    'severity': 'critical',
                    'details': {
                        'export_count': len(exports),
                        'hour': current_hour
                    },
                    'confidence_score': 0.98
                })

        return anomalies

    def save_anomalies(self, anomalies):
        """Save detected anomalies to database"""
        for anomaly in anomalies:
            insert_query = """
                INSERT INTO security.anomalies (
                    user_id, anomaly_type, severity, details, confidence_score
                ) VALUES (%s, %s, %s, %s, %s)
            """

            self.cursor.execute(insert_query, (
                anomaly['user_id'],
                anomaly['anomaly_type'],
                anomaly['severity'],
                json.dumps(anomaly['details']),
                anomaly['confidence_score']
            ))

        self.conn.commit()

    def run_detection(self):
        """Run all detection algorithms for all users"""
        # Get active users
        self.cursor.execute("""
            SELECT DISTINCT user_id
            FROM security.audit_log
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)

        all_anomalies = []

        for (user_id,) in self.cursor.fetchall():
            anomalies = []
            anomalies.extend(self.detect_unusual_access_time(user_id))
            anomalies.extend(self.detect_high_volume(user_id))
            anomalies.extend(self.detect_suspicious_patterns(user_id))

            if anomalies:
                all_anomalies.extend(anomalies)
                print(f"Found {len(anomalies)} anomalies for user {user_id}")

        self.save_anomalies(all_anomalies)
        print(f"Total anomalies detected: {len(all_anomalies)}")

        return all_anomalies

    def close(self):
        self.cursor.close()
        self.conn.close()

# Usage
if __name__ == '__main__':
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'ecommerce',
        'user': 'admin',
        'password': 'secure_pass'
    }

    detector = AnomalyDetector(db_config)
    anomalies = detector.run_detection()
    detector.close()

    print(f"\nDetected {len(anomalies)} anomalies")
    for anomaly in anomalies:
        print(f"- {anomaly['anomaly_type']}: {anomaly['severity']} (confidence: {anomaly['confidence_score']:.2f})")
```

### Step 3: Compliance Reporting

**3.1 SOX Compliance Report**

```sql
-- SOX compliance: Access controls report
CREATE OR REPLACE VIEW security.sox_access_controls AS
SELECT
    u.username,
    u.email,
    r.name as role,
    u.department,
    u.is_active,
    u.last_login,
    COUNT(DISTINCT rp.permission_id) as permission_count,
    STRING_AGG(DISTINCT p.resource || ':' || p.action, ', ' ORDER BY p.resource || ':' || p.action) as permissions
FROM security.users u
JOIN security.roles r ON u.role_id = r.id
LEFT JOIN security.role_permissions rp ON r.id = rp.role_id
LEFT JOIN security.permissions p ON rp.permission_id = p.id
GROUP BY u.id, u.username, u.email, r.name, u.department, u.is_active, u.last_login;

-- SOX compliance: Segregation of duties violations
CREATE OR REPLACE VIEW security.sox_sod_violations AS
WITH user_permissions AS (
    SELECT
        u.id as user_id,
        u.username,
        p.resource,
        p.action
    FROM security.users u
    JOIN security.roles r ON u.role_id = r.id
    JOIN security.role_permissions rp ON r.id = rp.role_id
    JOIN security.permissions p ON rp.permission_id = p.id
)
SELECT
    up1.user_id,
    up1.username,
    'Can both create and approve: ' || up1.resource as violation,
    'HIGH' as severity
FROM user_permissions up1
JOIN user_permissions up2
    ON up1.user_id = up2.user_id
    AND up1.resource = up2.resource
WHERE up1.action = 'INSERT'
AND up2.action = 'APPROVE';

-- SOX compliance: Audit trail completeness
CREATE OR REPLACE FUNCTION security.verify_audit_completeness(
    table_name TEXT,
    start_date DATE,
    end_date DATE
) RETURNS TABLE (
    total_changes INTEGER,
    audited_changes INTEGER,
    missing_audits INTEGER,
    completeness_pct NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH table_changes AS (
        -- This would need to be customized per table
        SELECT COUNT(*) as total
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = verify_audit_completeness.table_name
    ),
    audit_records AS (
        SELECT COUNT(*) as audited
        FROM security.data_access_log
        WHERE table_name = verify_audit_completeness.table_name
        AND accessed_at BETWEEN start_date AND end_date
    )
    SELECT
        tc.total::INTEGER,
        ar.audited::INTEGER,
        (tc.total - ar.audited)::INTEGER as missing,
        ROUND((ar.audited::NUMERIC / NULLIF(tc.total, 0)) * 100, 2) as completeness
    FROM table_changes tc
    CROSS JOIN audit_records ar;
END;
$$ LANGUAGE plpgsql;
```

**3.2 GDPR Compliance**

```sql
-- GDPR: Data subject access request (DSAR)
CREATE OR REPLACE FUNCTION security.generate_dsar(
    subject_email TEXT
) RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'personal_data', (
            SELECT jsonb_build_object(
                'customer', row_to_json(c),
                'orders', (
                    SELECT json_agg(row_to_json(o))
                    FROM orders o
                    WHERE o.customer_id = c.id
                ),
                'payments', (
                    SELECT json_agg(row_to_json(p))
                    FROM payments p
                    JOIN orders o ON p.order_id = o.id
                    WHERE o.customer_id = c.id
                )
            )
            FROM customers c
            WHERE c.email = subject_email
        ),
        'processing_activities', (
            SELECT json_agg(jsonb_build_object(
                'activity', al.action,
                'purpose', al.resource,
                'timestamp', al.created_at,
                'legal_basis', 'Contract performance'
            ))
            FROM security.audit_log al
            JOIN customers c ON al.user_id = c.id
            WHERE c.email = subject_email
            AND al.created_at >= NOW() - INTERVAL '12 months'
        ),
        'data_retention', jsonb_build_object(
            'retention_period', '7 years',
            'legal_basis', 'Legal obligation (tax law)',
            'deletion_date', (
                SELECT created_at + INTERVAL '7 years'
                FROM customers
                WHERE email = subject_email
            )
        ),
        'generated_at', NOW()
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- GDPR: Right to erasure (right to be forgotten)
CREATE OR REPLACE FUNCTION security.erase_personal_data(
    subject_email TEXT,
    reason TEXT
) RETURNS JSONB AS $$
DECLARE
    customer_id INTEGER;
    result JSONB;
BEGIN
    -- Get customer ID
    SELECT id INTO customer_id
    FROM customers
    WHERE email = subject_email;

    IF customer_id IS NULL THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Customer not found'
        );
    END IF;

    -- Log the erasure request
    INSERT INTO security.audit_log (
        user_id, action, resource, details
    ) VALUES (
        customer_id,
        'GDPR_ERASURE',
        'customers',
        jsonb_build_object('reason', reason, 'email', subject_email)
    );

    -- Anonymize customer data
    UPDATE customers
    SET
        email = 'erased-' || id || '@anonymized.local',
        name = 'Erased User',
        country = 'XX',
        segment = 'ERASED',
        lifetime_value = 0
    WHERE id = customer_id;

    -- Keep orders for legal compliance but anonymize
    UPDATE orders
    SET
        shipping_country = 'XX'
    WHERE customer_id = customer_id;

    result := jsonb_build_object(
        'success', true,
        'customer_id', customer_id,
        'erasure_date', NOW(),
        'records_affected', jsonb_build_object(
            'customer', 1,
            'orders', (SELECT COUNT(*) FROM orders WHERE customer_id = customer_id)
        )
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- GDPR: Consent management
CREATE TABLE security.gdpr_consent (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    purpose VARCHAR(100) NOT NULL,  -- marketing, analytics, third_party_sharing
    consented BOOLEAN NOT NULL,
    consent_date TIMESTAMP,
    withdrawal_date TIMESTAMP,
    version VARCHAR(20),  -- Privacy policy version
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gdpr_consent_customer ON security.gdpr_consent(customer_id);
CREATE INDEX idx_gdpr_consent_purpose ON security.gdpr_consent(purpose);
```

**3.3 PCI-DSS Compliance**

```sql
-- PCI-DSS: Encrypt sensitive payment data
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Secure payment storage
CREATE TABLE security.encrypted_payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    card_last_four CHAR(4), -- Only store last 4 digits
    card_type VARCHAR(20),
    encrypted_token BYTEA, -- Encrypted payment token
    expiry_month INTEGER,
    expiry_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Never store full card numbers, CVV, or magnetic stripe data
    CHECK (expiry_month BETWEEN 1 AND 12),
    CHECK (expiry_year >= EXTRACT(YEAR FROM CURRENT_DATE))
);

-- Function to encrypt payment token
CREATE OR REPLACE FUNCTION security.store_payment_token(
    p_order_id INTEGER,
    p_token TEXT,
    p_last_four CHAR(4),
    p_card_type VARCHAR(20),
    p_expiry_month INTEGER,
    p_expiry_year INTEGER,
    p_encryption_key TEXT
) RETURNS INTEGER AS $$
DECLARE
    payment_id INTEGER;
BEGIN
    INSERT INTO security.encrypted_payments (
        order_id,
        card_last_four,
        card_type,
        encrypted_token,
        expiry_month,
        expiry_year
    ) VALUES (
        p_order_id,
        p_last_four,
        p_card_type,
        pgp_sym_encrypt(p_token, p_encryption_key),
        p_expiry_month,
        p_expiry_year
    ) RETURNING id INTO payment_id;

    -- Log access
    INSERT INTO security.audit_log (
        action, resource, details
    ) VALUES (
        'STORE_PAYMENT',
        'encrypted_payments',
        jsonb_build_object(
            'payment_id', payment_id,
            'order_id', p_order_id
        )
    );

    RETURN payment_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- PCI-DSS: Access logging for cardholder data
CREATE OR REPLACE FUNCTION security.log_payment_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO security.audit_log (
        action,
        resource,
        details,
        ip_address
    ) VALUES (
        TG_OP,
        'encrypted_payments',
        jsonb_build_object(
            'payment_id', NEW.id,
            'order_id', NEW.order_id
        ),
        inet_client_addr()
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER log_payment_access
AFTER SELECT OR UPDATE ON security.encrypted_payments
FOR EACH ROW EXECUTE FUNCTION security.log_payment_access();
```

### Step 4: Security Dashboard

Create `dashboards/security-compliance.yaml`:

```yaml
name: "Security & Compliance Dashboard"
refresh_interval: 60
layout: grid

widgets:
  # Row 1: Security KPIs
  - id: active_users
    type: kpi_card
    title: "Active Users (24h)"
    query: |
      SELECT COUNT(DISTINCT user_id)
      FROM security.audit_log
      WHERE created_at >= NOW() - INTERVAL '24 hours'
    refresh: 60

  - id: failed_logins
    type: kpi_card
    title: "Failed Logins (24h)"
    query: |
      SELECT COUNT(*)
      FROM security.audit_log
      WHERE action = 'LOGIN_FAILED'
      AND created_at >= NOW() - INTERVAL '24 hours'
    refresh: 30
    alert:
      condition: value > 50
      severity: warning

  - id: active_anomalies
    type: kpi_card
    title: "Active Anomalies"
    query: |
      SELECT COUNT(*)
      FROM security.anomalies
      WHERE investigated = false
    refresh: 30
    alert:
      condition: value > 0
      severity: critical

  - id: compliance_score
    type: kpi_card
    title: "Compliance Score"
    query: |
      SELECT
        ROUND(
          (1.0 -
            COUNT(*) FILTER (WHERE severity = 'HIGH')::DECIMAL /
            NULLIF(COUNT(*), 0)
          ) * 100,
          1
        )
      FROM security.sox_sod_violations
    format: percentage
    refresh: 300

  # Row 2: Anomaly Detection
  - id: anomalies_by_type
    type: pie_chart
    title: "Anomalies by Type"
    query: |
      SELECT
        anomaly_type,
        COUNT(*) as count
      FROM security.anomalies
      WHERE detected_at >= NOW() - INTERVAL '7 days'
      AND investigated = false
      GROUP BY anomaly_type
    refresh: 60

  - id: anomalies_timeline
    type: line_chart
    title: "Anomalies Over Time"
    query: |
      SELECT
        DATE_TRUNC('hour', detected_at) as time,
        COUNT(*) as count,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical
      FROM security.anomalies
      WHERE detected_at >= NOW() - INTERVAL '24 hours'
      GROUP BY DATE_TRUNC('hour', detected_at)
      ORDER BY time
    refresh: 60

  # Row 3: Audit Activity
  - id: audit_activity
    type: bar_chart
    title: "Audit Activity by Hour"
    query: |
      SELECT
        EXTRACT(HOUR FROM created_at) as hour,
        COUNT(*) as activities
      FROM security.audit_log
      WHERE created_at >= NOW() - INTERVAL '24 hours'
      GROUP BY EXTRACT(HOUR FROM created_at)
      ORDER BY hour
    refresh: 120

  - id: top_active_users
    type: table
    title: "Most Active Users"
    query: |
      SELECT
        u.username,
        r.name as role,
        COUNT(*) as actions,
        MAX(al.created_at) as last_activity
      FROM security.audit_log al
      JOIN security.users u ON al.user_id = u.id
      JOIN security.roles r ON u.role_id = r.id
      WHERE al.created_at >= NOW() - INTERVAL '24 hours'
      GROUP BY u.id, u.username, r.name
      ORDER BY actions DESC
      LIMIT 20
    refresh: 60

  # Row 4: Compliance
  - id: sod_violations
    type: table
    title: "Segregation of Duties Violations"
    query: |
      SELECT * FROM security.sox_sod_violations
    refresh: 300

  - id: gdpr_requests
    type: table
    title: "Recent GDPR Requests"
    query: |
      SELECT
        user_id,
        action,
        details->>'email' as subject_email,
        created_at
      FROM security.audit_log
      WHERE action LIKE 'GDPR%'
      AND created_at >= NOW() - INTERVAL '30 days'
      ORDER BY created_at DESC
      LIMIT 50
    refresh: 300

alerts:
  - name: critical_anomaly
    condition: active_anomalies.value > 0
    severity: critical
    notification:
      type: email
      recipients: ["security@securebank.com"]

  - name: high_failed_logins
    condition: failed_logins.value > 100
    severity: high
    notification:
      type: slack
      channel: "#security-alerts"
```

### Challenge Exercise 2

**Task:** Implement a complete security monitoring system:
1. Real-time threat detection
2. Automated incident response
3. Forensic data collection
4. Compliance report generation

---

## Scenario 3: Database Migration Project

### Business Context

**Company:** TechCorp
**Challenge:** Migrate from legacy Oracle database to PostgreSQL
**Scale:** 500+ tables, 2TB data, minimal downtime required

### Migration Strategy

```
Phase 1: Assessment & Planning (Week 1-2)
├── Schema analysis
├── Dependency mapping
├── Data profiling
└── Risk assessment

Phase 2: Schema Migration (Week 3-4)
├── DDL conversion
├── Index optimization
├── Constraint validation
└── Function migration

Phase 3: Data Migration (Week 5-6)
├── Initial data load
├── Incremental sync
├── Validation testing
└── Performance tuning

Phase 4: Cutover (Week 7)
├── Final sync
├── Application switch
├── Monitoring
└── Rollback readiness
```

### Step 1: Schema Analysis

Create `/home/claude/AIShell/scenarios/migration/analyze_schema.sql`:

```sql
-- Analyze Oracle schema
-- (Run on source Oracle database)

-- Table inventory
SELECT
    owner,
    table_name,
    num_rows,
    blocks,
    avg_row_len,
    sample_size,
    last_analyzed
FROM all_tables
WHERE owner = 'TECHCORP'
ORDER BY num_rows DESC;

-- Column analysis
SELECT
    table_name,
    column_name,
    data_type,
    data_length,
    data_precision,
    data_scale,
    nullable,
    data_default
FROM all_tab_columns
WHERE owner = 'TECHCORP'
ORDER BY table_name, column_id;

-- Index analysis
SELECT
    table_name,
    index_name,
    index_type,
    uniqueness,
    column_name,
    column_position
FROM all_indexes
JOIN all_ind_columns USING (index_name)
WHERE table_owner = 'TECHCORP'
ORDER BY table_name, index_name, column_position;

-- Constraints
SELECT
    table_name,
    constraint_name,
    constraint_type,
    search_condition,
    r_constraint_name
FROM all_constraints
WHERE owner = 'TECHCORP';

-- Dependencies
SELECT
    name,
    type,
    referenced_name,
    referenced_type
FROM all_dependencies
WHERE owner = 'TECHCORP'
ORDER BY name;
```

**Analysis Script in Python:**

```python
# /home/claude/AIShell/scenarios/migration/migration_analyzer.py

import cx_Oracle
import psycopg2
import pandas as pd
from typing import Dict, List, Tuple
import json

class MigrationAnalyzer:
    def __init__(self, oracle_config, postgres_config):
        self.oracle_conn = cx_Oracle.connect(**oracle_config)
        self.pg_conn = psycopg2.connect(**postgres_config)

    def analyze_schema(self, schema='TECHCORP'):
        """Comprehensive schema analysis"""
        analysis = {
            'tables': self.analyze_tables(schema),
            'columns': self.analyze_columns(schema),
            'indexes': self.analyze_indexes(schema),
            'constraints': self.analyze_constraints(schema),
            'functions': self.analyze_functions(schema),
            'dependencies': self.analyze_dependencies(schema)
        }

        return analysis

    def analyze_tables(self, schema):
        """Analyze table structure and statistics"""
        query = """
            SELECT
                table_name,
                num_rows,
                blocks,
                avg_row_len,
                ROUND(blocks * 8192 / 1024 / 1024, 2) as size_mb
            FROM all_tables
            WHERE owner = :schema
            ORDER BY num_rows DESC
        """

        cursor = self.oracle_conn.cursor()
        cursor.execute(query, schema=schema)

        tables = []
        for row in cursor:
            tables.append({
                'table_name': row[0],
                'num_rows': row[1],
                'blocks': row[2],
                'avg_row_len': row[3],
                'size_mb': float(row[4]) if row[4] else 0
            })

        cursor.close()
        return tables

    def analyze_columns(self, schema):
        """Analyze column data types for conversion"""
        query = """
            SELECT
                table_name,
                column_name,
                data_type,
                data_length,
                data_precision,
                data_scale,
                nullable
            FROM all_tab_columns
            WHERE owner = :schema
            ORDER BY table_name, column_id
        """

        cursor = self.oracle_conn.cursor()
        cursor.execute(query, schema=schema)

        columns = []
        type_mapping = self.get_type_mapping()

        for row in cursor:
            oracle_type = row[2]
            pg_type = type_mapping.get(oracle_type, 'TEXT')

            # Adjust for precision/scale
            if oracle_type == 'NUMBER':
                if row[4] and row[5]:
                    pg_type = f'NUMERIC({row[4]},{row[5]})'
                elif row[4]:
                    pg_type = f'NUMERIC({row[4]})'
                else:
                    pg_type = 'NUMERIC'
            elif oracle_type == 'VARCHAR2':
                pg_type = f'VARCHAR({row[3]})'

            columns.append({
                'table_name': row[0],
                'column_name': row[1],
                'oracle_type': oracle_type,
                'postgres_type': pg_type,
                'length': row[3],
                'precision': row[4],
                'scale': row[5],
                'nullable': row[6] == 'Y'
            })

        cursor.close()
        return columns

    def get_type_mapping(self) -> Dict[str, str]:
        """Oracle to PostgreSQL type mapping"""
        return {
            'VARCHAR2': 'VARCHAR',
            'NVARCHAR2': 'VARCHAR',
            'NUMBER': 'NUMERIC',
            'FLOAT': 'DOUBLE PRECISION',
            'DATE': 'TIMESTAMP',
            'TIMESTAMP': 'TIMESTAMP',
            'CLOB': 'TEXT',
            'BLOB': 'BYTEA',
            'RAW': 'BYTEA',
            'CHAR': 'CHAR',
            'LONG': 'TEXT',
            'BINARY_FLOAT': 'REAL',
            'BINARY_DOUBLE': 'DOUBLE PRECISION'
        }

    def generate_migration_ddl(self, schema):
        """Generate PostgreSQL DDL from Oracle schema"""
        columns = self.analyze_columns(schema)
        tables = {}

        # Group columns by table
        for col in columns:
            table = col['table_name']
            if table not in tables:
                tables[table] = []
            tables[table].append(col)

        ddl_statements = []

        for table_name, cols in tables.items():
            ddl = f"CREATE TABLE {table_name.lower()} (\n"
            col_defs = []

            for col in cols:
                null_constraint = "" if col['nullable'] else " NOT NULL"
                col_def = f"    {col['column_name'].lower()} {col['postgres_type']}{null_constraint}"
                col_defs.append(col_def)

            ddl += ",\n".join(col_defs)
            ddl += "\n);"
            ddl_statements.append(ddl)

        return ddl_statements

    def analyze_indexes(self, schema):
        """Analyze indexes for recreation"""
        query = """
            SELECT
                i.table_name,
                i.index_name,
                i.index_type,
                i.uniqueness,
                ic.column_name,
                ic.column_position
            FROM all_indexes i
            JOIN all_ind_columns ic ON i.index_name = ic.index_name
            WHERE i.owner = :schema
            ORDER BY i.table_name, i.index_name, ic.column_position
        """

        cursor = self.oracle_conn.cursor()
        cursor.execute(query, schema=schema)

        indexes = {}
        for row in cursor:
            idx_key = (row[0], row[1])
            if idx_key not in indexes:
                indexes[idx_key] = {
                    'table_name': row[0],
                    'index_name': row[1],
                    'index_type': row[2],
                    'unique': row[3] == 'UNIQUE',
                    'columns': []
                }
            indexes[idx_key]['columns'].append(row[4])

        cursor.close()
        return list(indexes.values())

    def generate_index_ddl(self, indexes):
        """Generate PostgreSQL index DDL"""
        ddl_statements = []

        for idx in indexes:
            unique = "UNIQUE " if idx['unique'] else ""
            columns = ", ".join([c.lower() for c in idx['columns']])
            ddl = f"CREATE {unique}INDEX {idx['index_name'].lower()} ON {idx['table_name'].lower()} ({columns});"
            ddl_statements.append(ddl)

        return ddl_statements

    def estimate_migration_time(self, tables):
        """Estimate data migration time"""
        # Assume 10MB/sec transfer rate
        transfer_rate_mb_per_sec = 10

        total_size_mb = sum(t['size_mb'] for t in tables)
        transfer_time_sec = total_size_mb / transfer_rate_mb_per_sec

        # Add overhead for indexes and constraints (50%)
        total_time_sec = transfer_time_sec * 1.5

        return {
            'total_size_mb': total_size_mb,
            'estimated_time_hours': total_time_sec / 3600,
            'transfer_rate_mb_per_sec': transfer_rate_mb_per_sec
        }

    def close(self):
        self.oracle_conn.close()
        self.pg_conn.close()

# Usage
if __name__ == '__main__':
    oracle_config = {
        'user': 'techcorp',
        'password': 'oracle_pass',
        'dsn': 'oracle-host:1521/ORCL'
    }

    postgres_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'techcorp_new',
        'user': 'admin',
        'password': 'pg_pass'
    }

    analyzer = MigrationAnalyzer(oracle_config, postgres_config)

    # Run analysis
    analysis = analyzer.analyze_schema('TECHCORP')

    # Generate DDL
    table_ddl = analyzer.generate_migration_ddl('TECHCORP')
    index_ddl = analyzer.generate_index_ddl(analysis['indexes'])

    # Save to files
    with open('migration_table_ddl.sql', 'w') as f:
        f.write('\n\n'.join(table_ddl))

    with open('migration_index_ddl.sql', 'w') as f:
        f.write('\n\n'.join(index_ddl))

    # Estimate time
    estimate = analyzer.estimate_migration_time(analysis['tables'])
    print(f"Migration estimate: {estimate['estimated_time_hours']:.1f} hours")

    analyzer.close()
```

### Step 2: Data Migration

**Migration Script:**

```python
# /home/claude/AIShell/scenarios/migration/data_migrator.py

import cx_Oracle
import psycopg2
from psycopg2 import sql
import logging
from datetime import datetime
import multiprocessing
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s'
)

class DataMigrator:
    def __init__(self, oracle_config, postgres_config, batch_size=10000):
        self.oracle_config = oracle_config
        self.postgres_config = postgres_config
        self.batch_size = batch_size

    def migrate_table(self, table_name, columns):
        """Migrate single table with progress tracking"""
        oracle_conn = cx_Oracle.connect(**self.oracle_config)
        pg_conn = psycopg2.connect(**self.postgres_config)

        try:
            # Get row count
            oracle_cursor = oracle_conn.cursor()
            oracle_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = oracle_cursor.fetchone()[0]

            logging.info(f"Migrating {table_name}: {total_rows} rows")

            # Fetch and insert in batches
            offset = 0
            migrated = 0

            while offset < total_rows:
                # Fetch batch from Oracle
                query = f"""
                    SELECT * FROM (
                        SELECT t.*, ROWNUM as rn
                        FROM {table_name} t
                    ) WHERE rn > {offset} AND rn <= {offset + self.batch_size}
                """

                oracle_cursor.execute(query)
                rows = oracle_cursor.fetchall()

                if not rows:
                    break

                # Insert into PostgreSQL
                pg_cursor = pg_conn.cursor()

                placeholders = ','.join(['%s'] * len(columns))
                insert_query = sql.SQL("INSERT INTO {} VALUES ({})").format(
                    sql.Identifier(table_name.lower()),
                    sql.SQL(placeholders)
                )

                # Remove ROWNUM column
                cleaned_rows = [row[:-1] for row in rows]

                psycopg2.extras.execute_batch(
                    pg_cursor,
                    insert_query,
                    cleaned_rows,
                    page_size=1000
                )

                pg_conn.commit()
                pg_cursor.close()

                migrated += len(rows)
                offset += self.batch_size

                progress = (migrated / total_rows) * 100
                logging.info(f"{table_name}: {migrated}/{total_rows} ({progress:.1f}%)")

            logging.info(f"Completed {table_name}: {migrated} rows migrated")

        except Exception as e:
            logging.error(f"Error migrating {table_name}: {e}")
            pg_conn.rollback()
            raise

        finally:
            oracle_conn.close()
            pg_conn.close()

    def migrate_parallel(self, tables: List[Dict]):
        """Migrate multiple tables in parallel"""
        with multiprocessing.Pool(processes=4) as pool:
            pool.starmap(
                self.migrate_table,
                [(t['table_name'], t['columns']) for t in tables]
            )

    def validate_migration(self, table_name):
        """Validate row counts match"""
        oracle_conn = cx_Oracle.connect(**self.oracle_config)
        pg_conn = psycopg2.connect(**self.postgres_config)

        try:
            # Oracle count
            oracle_cursor = oracle_conn.cursor()
            oracle_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            oracle_count = oracle_cursor.fetchone()[0]

            # PostgreSQL count
            pg_cursor = pg_conn.cursor()
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name.lower()}")
            pg_count = pg_cursor.fetchone()[0]

            match = oracle_count == pg_count

            logging.info(f"Validation {table_name}: Oracle={oracle_count}, PostgreSQL={pg_count}, Match={match}")

            return {
                'table': table_name,
                'oracle_count': oracle_count,
                'postgres_count': pg_count,
                'match': match
            }

        finally:
            oracle_conn.close()
            pg_conn.close()

# Usage
if __name__ == '__main__':
    oracle_config = {
        'user': 'techcorp',
        'password': 'oracle_pass',
        'dsn': 'oracle-host:1521/ORCL'
    }

    postgres_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'techcorp_new',
        'user': 'admin',
        'password': 'pg_pass'
    }

    migrator = DataMigrator(oracle_config, postgres_config)

    # Get table list from analyzer
    tables = [
        {'table_name': 'CUSTOMERS', 'columns': ['id', 'name', 'email']},
        {'table_name': 'ORDERS', 'columns': ['id', 'customer_id', 'total']},
        # ... more tables
    ]

    # Migrate tables
    migrator.migrate_parallel(tables)

    # Validate
    for table in tables:
        migrator.validate_migration(table['table_name'])
```

### Challenge Exercise 3

**Task:** Implement zero-downtime migration:
1. Set up logical replication
2. Implement change data capture
3. Build sync monitor dashboard
4. Create rollback procedure

---

## Summary

You've completed three comprehensive end-to-end scenarios:

1. **E-commerce Analytics**: Multi-database queries, performance optimization, real-time dashboards
2. **Enterprise Security**: RBAC, audit logging, anomaly detection, compliance reporting
3. **Database Migration**: Schema analysis, data migration, validation testing

## Next Steps

- Combine techniques from multiple scenarios
- Build your own production systems
- Contribute to AI-Shell community
- Share your success stories

**Congratulations on completing the AI-Shell Expert Tutorial Series!**
