# Database Operations Guide

## Table of Contents

1. [Overview](#overview)
2. [PostgreSQL Operations](#postgresql-operations)
3. [MySQL Operations](#mysql-operations)
4. [MongoDB Operations](#mongodb-operations)
5. [Redis Operations](#redis-operations)
6. [Connection Management](#connection-management)
7. [Multi-Database Workflows](#multi-database-workflows)
8. [Advanced Operations](#advanced-operations)

---

## Overview

AI-Shell provides unified database operations across multiple database types while respecting each database's unique features and capabilities.

### Supported Databases

| Database | Version Support | Features |
|----------|----------------|----------|
| PostgreSQL | 10.0+ | Full SQL, JSONB, Extensions |
| MySQL | 5.7+ | Full SQL, InnoDB, MyISAM |
| MongoDB | 4.0+ | Documents, Aggregation, Sharding |
| Redis | 5.0+ | Key-Value, Pub/Sub, Streams |

### Database Operation Categories

```
Database Operations
├── Connection Management
│   ├── Add/Remove connections
│   ├── Test connectivity
│   └── Connection pooling
├── Query Execution
│   ├── SQL queries (PostgreSQL, MySQL)
│   ├── MongoDB queries
│   └── Redis commands
├── Schema Management
│   ├── Tables/Collections
│   ├── Indexes
│   └── Constraints
├── Data Operations
│   ├── CRUD operations
│   ├── Bulk operations
│   └── Transactions
└── Monitoring
    ├── Performance metrics
    ├── Connection stats
    └── Query analysis
```

---

## PostgreSQL Operations

### Connecting to PostgreSQL

#### Basic Connection

```bash
# Add PostgreSQL connection
aishell connection add \
  --name pg-prod \
  --type postgresql \
  --host postgres.example.com \
  --port 5432 \
  --database production \
  --username pgadmin

# Test connection
aishell connection test pg-prod

# Show connection info
aishell connection show pg-prod
```

#### SSL Connection

```bash
# Connect with SSL
aishell connection add \
  --name pg-secure \
  --type postgresql \
  --host secure-pg.example.com \
  --port 5432 \
  --database myapp \
  --username secureuser \
  --ssl-mode require \
  --ssl-cert /path/to/client-cert.pem \
  --ssl-key /path/to/client-key.pem \
  --ssl-ca /path/to/ca-cert.pem
```

#### Connection URI

```bash
# Use connection URI
aishell connection add \
  --name pg-uri \
  --uri "postgresql://user:pass@host:5432/dbname?sslmode=require"
```

### Running PostgreSQL Queries

#### Simple Queries

```bash
# SELECT query
aishell query run pg-prod \
  --sql "SELECT * FROM users WHERE active = true LIMIT 10"

# INSERT query
aishell query run pg-prod \
  --sql "INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com')"

# UPDATE query
aishell query run pg-prod \
  --sql "UPDATE users SET last_login = NOW() WHERE id = 123"

# DELETE query
aishell query run pg-prod \
  --sql "DELETE FROM sessions WHERE created_at < NOW() - INTERVAL '30 days'"
```

#### Complex Queries

```bash
# Join query
aishell query run pg-prod --sql "
  SELECT
    u.id,
    u.name,
    COUNT(o.id) as order_count,
    SUM(o.total) as total_spent
  FROM users u
  LEFT JOIN orders o ON u.id = o.user_id
  WHERE u.created_at > '2024-01-01'
  GROUP BY u.id, u.name
  HAVING COUNT(o.id) > 5
  ORDER BY total_spent DESC
  LIMIT 100
"

# CTE (Common Table Expression)
aishell query run pg-prod --sql "
  WITH monthly_sales AS (
    SELECT
      DATE_TRUNC('month', created_at) as month,
      SUM(total) as sales
    FROM orders
    GROUP BY DATE_TRUNC('month', created_at)
  )
  SELECT
    month,
    sales,
    LAG(sales) OVER (ORDER BY month) as prev_month_sales,
    sales - LAG(sales) OVER (ORDER BY month) as growth
  FROM monthly_sales
  ORDER BY month DESC
"

# Window functions
aishell query run pg-prod --sql "
  SELECT
    product_id,
    sale_date,
    quantity,
    SUM(quantity) OVER (
      PARTITION BY product_id
      ORDER BY sale_date
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as rolling_7day_sales
  FROM sales
  ORDER BY product_id, sale_date
"
```

#### JSON Queries (JSONB)

```bash
# Query JSONB data
aishell query run pg-prod --sql "
  SELECT
    id,
    metadata->>'name' as name,
    metadata->'settings'->>'theme' as theme
  FROM users
  WHERE metadata @> '{\"premium\": true}'
"

# JSONB aggregation
aishell query run pg-prod --sql "
  SELECT
    jsonb_agg(
      jsonb_build_object(
        'id', id,
        'name', name,
        'email', email
      )
    ) as users_json
  FROM users
  WHERE active = true
"
```

### Schema Management

#### Tables

```bash
# Create table
aishell query run pg-prod --sql "
  CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
  )
"

# Alter table
aishell query run pg-prod --sql "
  ALTER TABLE products
  ADD COLUMN category_id INTEGER REFERENCES categories(id),
  ADD COLUMN tags TEXT[]
"

# Drop table
aishell query run pg-prod --sql "DROP TABLE IF EXISTS old_table CASCADE"

# List all tables
aishell query run pg-prod --sql "
  SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
"
```

#### Indexes

```bash
# Create index
aishell query run pg-prod --sql "
  CREATE INDEX idx_users_email ON users(email)
"

# Create unique index
aishell query run pg-prod --sql "
  CREATE UNIQUE INDEX idx_users_username ON users(LOWER(username))
"

# Create partial index
aishell query run pg-prod --sql "
  CREATE INDEX idx_orders_pending ON orders(created_at)
  WHERE status = 'pending'
"

# Create GIN index for JSONB
aishell query run pg-prod --sql "
  CREATE INDEX idx_users_metadata ON users USING GIN(metadata)
"

# Create full-text search index
aishell query run pg-prod --sql "
  CREATE INDEX idx_products_search ON products
  USING GIN(to_tsvector('english', name || ' ' || description))
"

# List all indexes
aishell query run pg-prod --sql "
  SELECT
    schemaname,
    tablename,
    indexname,
    indexdef,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
  FROM pg_indexes
  WHERE schemaname = 'public'
  ORDER BY pg_relation_size(indexname::regclass) DESC
"

# Analyze index usage
aishell query run pg-prod --sql "
  SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
  FROM pg_stat_user_indexes
  WHERE idx_scan = 0
  ORDER BY pg_relation_size(indexrelid) DESC
"
```

### PostgreSQL-Specific Features

#### Extensions

```bash
# Enable extension
aishell query run pg-prod --sql "CREATE EXTENSION IF NOT EXISTS pg_trgm"
aishell query run pg-prod --sql "CREATE EXTENSION IF NOT EXISTS uuid-ossp"
aishell query run pg-prod --sql "CREATE EXTENSION IF NOT EXISTS postgis"

# List installed extensions
aishell query run pg-prod --sql "SELECT * FROM pg_extension"
```

#### Full-Text Search

```bash
# Create full-text search
aishell query run pg-prod --sql "
  SELECT
    id,
    title,
    ts_rank(to_tsvector('english', title || ' ' || content), query) as rank
  FROM articles,
       to_tsquery('english', 'postgresql & performance') as query
  WHERE to_tsvector('english', title || ' ' || content) @@ query
  ORDER BY rank DESC
  LIMIT 10
"
```

#### Partitioning

```bash
# Create partitioned table
aishell query run pg-prod --sql "
  CREATE TABLE orders_partitioned (
    id BIGSERIAL,
    user_id INTEGER,
    total DECIMAL(10,2),
    created_at TIMESTAMP NOT NULL
  ) PARTITION BY RANGE (created_at)
"

# Create partitions
aishell query run pg-prod --sql "
  CREATE TABLE orders_2024_01 PARTITION OF orders_partitioned
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01')
"

aishell query run pg-prod --sql "
  CREATE TABLE orders_2024_02 PARTITION OF orders_partitioned
  FOR VALUES FROM ('2024-02-01') TO ('2024-03-01')
"
```

#### Materialized Views

```bash
# Create materialized view
aishell query run pg-prod --sql "
  CREATE MATERIALIZED VIEW monthly_sales AS
  SELECT
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as order_count,
    SUM(total) as total_sales
  FROM orders
  GROUP BY DATE_TRUNC('month', created_at)
  WITH DATA
"

# Refresh materialized view
aishell query run pg-prod --sql "REFRESH MATERIALIZED VIEW monthly_sales"

# Concurrent refresh
aishell query run pg-prod --sql "REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_sales"
```

---

## MySQL Operations

### Connecting to MySQL

```bash
# Add MySQL connection
aishell connection add \
  --name mysql-prod \
  --type mysql \
  --host mysql.example.com \
  --port 3306 \
  --database ecommerce \
  --username mysqladmin

# Test connection
aishell connection test mysql-prod
```

### Running MySQL Queries

#### Basic Queries

```bash
# SELECT with MySQL-specific functions
aishell query run mysql-prod --sql "
  SELECT
    id,
    name,
    CONCAT(first_name, ' ', last_name) as full_name,
    DATE_FORMAT(created_at, '%Y-%m-%d') as signup_date
  FROM users
  WHERE YEAR(created_at) = YEAR(CURDATE())
  LIMIT 10
"

# INSERT with ON DUPLICATE KEY
aishell query run mysql-prod --sql "
  INSERT INTO user_stats (user_id, login_count, last_login)
  VALUES (123, 1, NOW())
  ON DUPLICATE KEY UPDATE
    login_count = login_count + 1,
    last_login = NOW()
"
```

#### Joins and Subqueries

```bash
# Complex join
aishell query run mysql-prod --sql "
  SELECT
    u.id,
    u.name,
    COUNT(DISTINCT o.id) as order_count,
    COALESCE(SUM(oi.quantity * oi.price), 0) as total_spent
  FROM users u
  LEFT JOIN orders o ON u.id = o.user_id
  LEFT JOIN order_items oi ON o.id = oi.order_id
  WHERE u.status = 'active'
  GROUP BY u.id, u.name
  HAVING total_spent > 1000
  ORDER BY total_spent DESC
"

# Subquery
aishell query run mysql-prod --sql "
  SELECT *
  FROM products
  WHERE price > (
    SELECT AVG(price)
    FROM products
    WHERE category_id = products.category_id
  )
"
```

### Schema Management

#### Tables

```bash
# Create table with MySQL-specific features
aishell query run mysql-prod --sql "
  CREATE TABLE orders (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled'),
    total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_status_created (status, created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"

# Show table structure
aishell query run mysql-prod --sql "DESCRIBE orders"

# Show create table
aishell query run mysql-prod --sql "SHOW CREATE TABLE orders"

# List all tables
aishell query run mysql-prod --sql "
  SELECT
    TABLE_NAME,
    ENGINE,
    TABLE_ROWS,
    ROUND(DATA_LENGTH / 1024 / 1024, 2) as data_size_mb,
    ROUND(INDEX_LENGTH / 1024 / 1024, 2) as index_size_mb
  FROM information_schema.TABLES
  WHERE TABLE_SCHEMA = DATABASE()
  ORDER BY DATA_LENGTH DESC
"
```

#### Indexes

```bash
# Create index
aishell query run mysql-prod --sql "
  CREATE INDEX idx_orders_user_status ON orders(user_id, status)
"

# Create full-text index
aishell query run mysql-prod --sql "
  CREATE FULLTEXT INDEX idx_products_search ON products(name, description)
"

# Show indexes
aishell query run mysql-prod --sql "
  SHOW INDEX FROM orders
"

# Analyze index usage
aishell query run mysql-prod --sql "
  SELECT
    TABLE_NAME,
    INDEX_NAME,
    CARDINALITY,
    INDEX_TYPE
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
  ORDER BY TABLE_NAME, INDEX_NAME
"
```

### MySQL-Specific Features

#### Full-Text Search

```bash
# Full-text search
aishell query run mysql-prod --sql "
  SELECT
    id,
    name,
    MATCH(name, description) AGAINST('laptop gaming' IN NATURAL LANGUAGE MODE) as relevance
  FROM products
  WHERE MATCH(name, description) AGAINST('laptop gaming' IN NATURAL LANGUAGE MODE)
  ORDER BY relevance DESC
  LIMIT 10
"

# Boolean mode search
aishell query run mysql-prod --sql "
  SELECT *
  FROM articles
  WHERE MATCH(title, content) AGAINST('+mysql -oracle' IN BOOLEAN MODE)
"
```

#### Stored Procedures

```bash
# Create stored procedure
aishell query run mysql-prod --sql "
  DELIMITER //
  CREATE PROCEDURE GetUserOrders(IN userId INT)
  BEGIN
    SELECT
      o.*,
      COUNT(oi.id) as item_count
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    WHERE o.user_id = userId
    GROUP BY o.id;
  END //
  DELIMITER ;
"

# Call stored procedure
aishell query run mysql-prod --sql "CALL GetUserOrders(123)"

# List stored procedures
aishell query run mysql-prod --sql "
  SHOW PROCEDURE STATUS WHERE Db = DATABASE()
"
```

#### Triggers

```bash
# Create trigger
aishell query run mysql-prod --sql "
  CREATE TRIGGER update_order_total
  AFTER INSERT ON order_items
  FOR EACH ROW
  BEGIN
    UPDATE orders
    SET total = (
      SELECT SUM(quantity * price)
      FROM order_items
      WHERE order_id = NEW.order_id
    )
    WHERE id = NEW.order_id;
  END
"

# Show triggers
aishell query run mysql-prod --sql "
  SHOW TRIGGERS WHERE \`Table\` = 'order_items'
"
```

---

## MongoDB Operations

### Connecting to MongoDB

```bash
# Add MongoDB connection
aishell connection add \
  --name mongo-prod \
  --type mongodb \
  --host mongodb://mongo1.example.com:27017,mongo2.example.com:27017,mongo3.example.com:27017 \
  --database analytics \
  --options "replicaSet=rs0&authSource=admin"

# Test connection
aishell connection test mongo-prod

# Show database stats
aishell query run mongo-prod --query '{"command": "dbStats"}'
```

### Running MongoDB Queries

#### Find Operations

```bash
# Simple find
aishell query run mongo-prod \
  --collection users \
  --query '{"active": true}' \
  --limit 10

# Find with projection
aishell query run mongo-prod \
  --collection users \
  --query '{"age": {"$gte": 18}}' \
  --projection '{"name": 1, "email": 1, "_id": 0}' \
  --sort '{"created_at": -1}'

# Find with complex query
aishell query run mongo-prod \
  --collection orders \
  --query '{
    "status": {"$in": ["pending", "processing"]},
    "total": {"$gte": 100},
    "created_at": {"$gte": {"$date": "2024-01-01T00:00:00Z"}}
  }' \
  --limit 50
```

#### Aggregation Pipeline

```bash
# Group and sum
aishell query run mongo-prod \
  --collection orders \
  --aggregate '[
    {
      "$match": {
        "status": "completed",
        "created_at": {"$gte": {"$date": "2024-01-01T00:00:00Z"}}
      }
    },
    {
      "$group": {
        "_id": "$user_id",
        "order_count": {"$sum": 1},
        "total_spent": {"$sum": "$total"},
        "avg_order_value": {"$avg": "$total"}
      }
    },
    {
      "$match": {
        "order_count": {"$gte": 5}
      }
    },
    {
      "$sort": {"total_spent": -1}
    },
    {
      "$limit": 100
    }
  ]'

# Complex aggregation with lookups
aishell query run mongo-prod \
  --collection orders \
  --aggregate '[
    {
      "$lookup": {
        "from": "users",
        "localField": "user_id",
        "foreignField": "_id",
        "as": "user"
      }
    },
    {
      "$unwind": "$user"
    },
    {
      "$lookup": {
        "from": "order_items",
        "localField": "_id",
        "foreignField": "order_id",
        "as": "items"
      }
    },
    {
      "$addFields": {
        "item_count": {"$size": "$items"}
      }
    },
    {
      "$project": {
        "order_id": "$_id",
        "user_name": "$user.name",
        "user_email": "$user.email",
        "total": 1,
        "item_count": 1,
        "created_at": 1
      }
    }
  ]'
```

#### Insert, Update, Delete

```bash
# Insert one
aishell query run mongo-prod \
  --collection users \
  --insert '{
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30,
    "tags": ["premium", "verified"],
    "metadata": {
      "signup_source": "web",
      "referrer": "google"
    }
  }'

# Insert many
aishell query run mongo-prod \
  --collection products \
  --insert-many '[
    {"name": "Product 1", "price": 29.99, "stock": 100},
    {"name": "Product 2", "price": 49.99, "stock": 50},
    {"name": "Product 3", "price": 19.99, "stock": 200}
  ]'

# Update one
aishell query run mongo-prod \
  --collection users \
  --update-one \
  --filter '{"email": "john@example.com"}' \
  --update '{
    "$set": {"last_login": {"$date": "2024-01-15T10:30:00Z"}},
    "$inc": {"login_count": 1}
  }'

# Update many
aishell query run mongo-prod \
  --collection products \
  --update-many \
  --filter '{"category": "electronics"}' \
  --update '{"$mul": {"price": 0.9}}'

# Delete one
aishell query run mongo-prod \
  --collection sessions \
  --delete-one \
  --filter '{"token": "abc123"}'

# Delete many
aishell query run mongo-prod \
  --collection logs \
  --delete-many \
  --filter '{"created_at": {"$lt": {"$date": "2024-01-01T00:00:00Z"}}}'
```

### MongoDB Schema Management

#### Collections

```bash
# Create collection
aishell query run mongo-prod \
  --command '{"create": "new_collection"}'

# Create collection with validation
aishell query run mongo-prod \
  --command '{
    "create": "validated_users",
    "validator": {
      "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "email", "age"],
        "properties": {
          "name": {"bsonType": "string"},
          "email": {"bsonType": "string", "pattern": "^.+@.+$"},
          "age": {"bsonType": "int", "minimum": 18}
        }
      }
    }
  }'

# List collections
aishell query run mongo-prod \
  --command '{"listCollections": 1}'

# Drop collection
aishell query run mongo-prod \
  --command '{"drop": "old_collection"}'
```

#### Indexes

```bash
# Create index
aishell query run mongo-prod \
  --collection users \
  --create-index '{"email": 1}' \
  --unique

# Create compound index
aishell query run mongo-prod \
  --collection orders \
  --create-index '{"user_id": 1, "created_at": -1}'

# Create text index
aishell query run mongo-prod \
  --collection articles \
  --create-index '{
    "title": "text",
    "content": "text"
  }'

# Create geospatial index
aishell query run mongo-prod \
  --collection locations \
  --create-index '{"coordinates": "2dsphere"}'

# List indexes
aishell query run mongo-prod \
  --collection users \
  --command '{"listIndexes": "users"}'

# Drop index
aishell query run mongo-prod \
  --collection users \
  --command '{"dropIndexes": "users", "index": "email_1"}'
```

---

## Redis Operations

### Connecting to Redis

```bash
# Add Redis connection
aishell connection add \
  --name redis-prod \
  --type redis \
  --host redis.example.com \
  --port 6379 \
  --database 0

# Add Redis with authentication
aishell connection add \
  --name redis-secure \
  --type redis \
  --host redis-secure.example.com \
  --port 6379 \
  --password "your-redis-password"

# Test connection
aishell connection test redis-prod
```

### Running Redis Commands

#### String Operations

```bash
# SET and GET
aishell query run redis-prod --command "SET user:123:name 'John Doe'"
aishell query run redis-prod --command "GET user:123:name"

# SET with expiration
aishell query run redis-prod --command "SETEX session:abc123 3600 '{\"user_id\": 123}'"

# INCR/DECR
aishell query run redis-prod --command "INCR page:views:homepage"
aishell query run redis-prod --command "INCRBY user:123:points 100"

# Multiple operations
aishell query run redis-prod --command "MSET user:1:name 'Alice' user:2:name 'Bob' user:3:name 'Charlie'"
aishell query run redis-prod --command "MGET user:1:name user:2:name user:3:name"
```

#### Hash Operations

```bash
# HSET and HGET
aishell query run redis-prod --command "HSET user:123 name 'John Doe' email 'john@example.com' age 30"
aishell query run redis-prod --command "HGET user:123 name"
aishell query run redis-prod --command "HGETALL user:123"

# HINCRBY
aishell query run redis-prod --command "HINCRBY user:123 login_count 1"

# HMSET
aishell query run redis-prod --command "HMSET product:456 name 'Laptop' price 999.99 stock 50"
```

#### List Operations

```bash
# LPUSH and RPUSH
aishell query run redis-prod --command "LPUSH queue:tasks 'task1' 'task2' 'task3'"
aishell query run redis-prod --command "RPUSH recent:views 'page1' 'page2'"

# LPOP and RPOP
aishell query run redis-prod --command "LPOP queue:tasks"

# LRANGE
aishell query run redis-prod --command "LRANGE recent:views 0 10"

# LLEN
aishell query run redis-prod --command "LLEN queue:tasks"
```

#### Set Operations

```bash
# SADD
aishell query run redis-prod --command "SADD tags:article:123 'tech' 'programming' 'database'"

# SMEMBERS
aishell query run redis-prod --command "SMEMBERS tags:article:123"

# SISMEMBER
aishell query run redis-prod --command "SISMEMBER tags:article:123 'tech'"

# Set operations
aishell query run redis-prod --command "SUNION tags:article:123 tags:article:124"
aishell query run redis-prod --command "SINTER tags:article:123 tags:article:124"
aishell query run redis-prod --command "SDIFF tags:article:123 tags:article:124"
```

#### Sorted Set Operations

```bash
# ZADD
aishell query run redis-prod --command "ZADD leaderboard 100 'player1' 200 'player2' 150 'player3'"

# ZRANGE
aishell query run redis-prod --command "ZRANGE leaderboard 0 -1 WITHSCORES"

# ZREVRANGE (highest scores first)
aishell query run redis-prod --command "ZREVRANGE leaderboard 0 9 WITHSCORES"

# ZINCRBY
aishell query run redis-prod --command "ZINCRBY leaderboard 50 'player1'"

# ZRANK
aishell query run redis-prod --command "ZRANK leaderboard 'player1'"
```

#### Pub/Sub

```bash
# Subscribe to channel
aishell query run redis-prod --command "SUBSCRIBE notifications"

# Publish message
aishell query run redis-prod --command "PUBLISH notifications 'New order received'"

# Pattern subscribe
aishell query run redis-prod --command "PSUBSCRIBE user:*:notifications"
```

#### Stream Operations

```bash
# Add to stream
aishell query run redis-prod --command "XADD events:orders * user_id 123 product_id 456 total 99.99"

# Read from stream
aishell query run redis-prod --command "XREAD COUNT 10 STREAMS events:orders 0"

# Consumer groups
aishell query run redis-prod --command "XGROUP CREATE events:orders processors $ MKSTREAM"
aishell query run redis-prod --command "XREADGROUP GROUP processors consumer1 COUNT 10 STREAMS events:orders >"
```

---

## Connection Management

### Managing Multiple Connections

```bash
# List all connections
aishell connection list

# List by type
aishell connection list --type postgresql
aishell connection list --type mysql
aishell connection list --type mongodb
aishell connection list --type redis

# Show detailed connection info
aishell connection show prod-db --verbose

# Export connection configuration
aishell connection export prod-db > prod-db-config.json

# Import connection configuration
aishell connection import < prod-db-config.json

# Clone connection
aishell connection clone prod-db staging-db \
  --host staging.example.com
```

### Connection Pooling

```bash
# Configure pool size
aishell connection update prod-db \
  --pool-min 5 \
  --pool-max 20 \
  --pool-idle-timeout 10000

# Show pool statistics
aishell connection pool-stats prod-db

# Reset connection pool
aishell connection pool-reset prod-db
```

### Connection Testing

```bash
# Basic test
aishell connection test prod-db

# Verbose test with diagnostics
aishell connection test prod-db --verbose

# Test with ping
aishell connection ping prod-db

# Test query performance
aishell connection benchmark prod-db \
  --queries 100 \
  --concurrency 10
```

---

## Multi-Database Workflows

### Querying Multiple Databases

```bash
# Run same query on multiple databases
aishell query run-multi \
  --connections pg-prod,pg-staging,pg-dev \
  --sql "SELECT COUNT(*) FROM users"

# Parallel execution
aishell query run-multi \
  --connections pg-prod,mysql-prod \
  --sql "SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '1 day'" \
  --parallel
```

### Data Migration

```bash
# Export data from PostgreSQL
aishell data export pg-prod \
  --table users \
  --format csv \
  --output users-export.csv

# Import data to MySQL
aishell data import mysql-prod \
  --table users \
  --format csv \
  --input users-export.csv

# Direct database-to-database transfer
aishell data transfer \
  --source pg-prod \
  --target mysql-prod \
  --table users \
  --batch-size 1000
```

### Schema Synchronization

```bash
# Compare schemas
aishell schema compare \
  --source pg-prod \
  --target pg-staging

# Generate migration script
aishell schema diff \
  --source pg-prod \
  --target pg-staging \
  --output migration.sql

# Apply schema changes
aishell schema sync \
  --source pg-prod \
  --target pg-staging \
  --dry-run
```

---

## Advanced Operations

### Transactions

```bash
# PostgreSQL transaction
aishell query run pg-prod --transaction --sql "
  BEGIN;

  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  UPDATE accounts SET balance = balance + 100 WHERE id = 2;

  INSERT INTO transactions (from_account, to_account, amount, created_at)
  VALUES (1, 2, 100, NOW());

  COMMIT;
"

# MySQL transaction with savepoints
aishell query run mysql-prod --transaction --sql "
  START TRANSACTION;

  INSERT INTO orders (user_id, total) VALUES (123, 99.99);
  SET @order_id = LAST_INSERT_ID();

  SAVEPOINT items;

  INSERT INTO order_items (order_id, product_id, quantity)
  VALUES (@order_id, 456, 2);

  -- If something fails, rollback to savepoint
  -- ROLLBACK TO SAVEPOINT items;

  COMMIT;
"
```

### Batch Operations

```bash
# Batch insert from CSV
aishell data batch-insert pg-prod \
  --table products \
  --csv products.csv \
  --batch-size 1000

# Batch update
aishell data batch-update pg-prod \
  --table users \
  --set "status = 'inactive'" \
  --where "last_login < NOW() - INTERVAL '1 year'" \
  --batch-size 500

# Batch delete
aishell data batch-delete pg-prod \
  --table logs \
  --where "created_at < NOW() - INTERVAL '90 days'" \
  --batch-size 1000
```

### Database Maintenance

```bash
# PostgreSQL VACUUM
aishell query run pg-prod --sql "VACUUM ANALYZE"

# MySQL OPTIMIZE
aishell query run mysql-prod --sql "OPTIMIZE TABLE orders"

# MongoDB compact
aishell query run mongo-prod --command '{"compact": "users"}'

# Redis memory cleanup
aishell query run redis-prod --command "MEMORY PURGE"
```

---

## Next Steps

- Learn [Query Optimization](./QUERY_OPTIMIZATION.md) techniques
- Set up [Backup & Recovery](./BACKUP_RECOVERY.md) procedures
- Configure [Monitoring & Analytics](./MONITORING_ANALYTICS.md)
- Review [Security Best Practices](./SECURITY_BEST_PRACTICES.md)

---

*Last Updated: 2024-01-15 | Version: 1.0.0*
