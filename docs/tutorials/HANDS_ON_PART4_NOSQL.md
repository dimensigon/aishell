# AI-Shell Hands-On Tutorial - Part 4: NoSQL & Advanced Databases

**Level:** Intermediate
**Duration:** 45-60 minutes
**Prerequisites:** Complete Parts 1-3

## Overview

This tutorial covers NoSQL databases (MongoDB, Redis) and advanced multi-database operations in AI-Shell. You'll learn how to work with document stores, caching layers, and coordinate operations across different database types.

## Learning Objectives

By the end of this tutorial, you will:
- Perform MongoDB CRUD operations and aggregations
- Use Redis for caching, pub/sub, and session management
- Coordinate operations across multiple databases
- Execute cross-database queries
- Optimize NoSQL database operations

---

## Part 1: MongoDB Operations (20 minutes)

### 1.1 Connect to MongoDB

```bash
# Start AI-Shell and connect to MongoDB
aishell

# Add MongoDB connection
aishell> db add mongodb://localhost:27017/ecommerce --name mongodb_main --type mongodb

# Verify connection
aishell> db list
```

**Expected Output:**
```
✓ Connected to MongoDB: mongodb_main
Database: ecommerce
Collections: 0
```

### 1.2 MongoDB CRUD Operations

#### Create Documents

```javascript
// Insert single product
aishell> mongo mongodb_main
db.products.insertOne({
  name: "Wireless Mouse",
  category: "Electronics",
  price: 29.99,
  stock: 150,
  tags: ["wireless", "ergonomic", "gaming"],
  specifications: {
    brand: "TechPro",
    warranty_months: 24,
    connectivity: "Bluetooth 5.0"
  },
  created_at: new Date(),
  updated_at: new Date()
})

// Insert multiple products
db.products.insertMany([
  {
    name: "Mechanical Keyboard",
    category: "Electronics",
    price: 89.99,
    stock: 75,
    tags: ["mechanical", "rgb", "gaming"],
    specifications: {
      brand: "KeyMaster",
      warranty_months: 36,
      switches: "Cherry MX Blue"
    },
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    name: "USB-C Cable",
    category: "Accessories",
    price: 12.99,
    stock: 500,
    tags: ["usb-c", "fast-charging", "durable"],
    specifications: {
      brand: "CablePro",
      warranty_months: 12,
      length_meters: 2
    },
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    name: "Laptop Stand",
    category: "Accessories",
    price: 39.99,
    stock: 200,
    tags: ["ergonomic", "aluminum", "adjustable"],
    specifications: {
      brand: "DeskHelper",
      warranty_months: 24,
      material: "Aluminum Alloy"
    },
    created_at: new Date(),
    updated_at: new Date()
  }
])
```

#### Read Documents

```javascript
// Find all products
db.products.find()

// Find with filters
db.products.find({ category: "Electronics" })

// Find with complex queries
db.products.find({
  price: { $gte: 20, $lte: 50 },
  stock: { $gt: 100 }
})

// Find with array matching
db.products.find({ tags: "gaming" })

// Find with nested document queries
db.products.find({ "specifications.brand": "TechPro" })

// Find with projection (select specific fields)
db.products.find(
  { category: "Electronics" },
  { name: 1, price: 1, _id: 0 }
)

// Find one document
db.products.findOne({ name: "Wireless Mouse" })

// Count documents
db.products.countDocuments({ category: "Electronics" })
```

#### Update Documents

```javascript
// Update single document
db.products.updateOne(
  { name: "Wireless Mouse" },
  {
    $set: {
      price: 27.99,
      updated_at: new Date()
    }
  }
)

// Update multiple documents
db.products.updateMany(
  { category: "Electronics" },
  {
    $inc: { stock: -10 },
    $set: { updated_at: new Date() }
  }
)

// Update with array operators
db.products.updateOne(
  { name: "Wireless Mouse" },
  {
    $push: { tags: "bestseller" },
    $set: { updated_at: new Date() }
  }
)

// Update or insert (upsert)
db.products.updateOne(
  { name: "Monitor Arm" },
  {
    $set: {
      name: "Monitor Arm",
      category: "Accessories",
      price: 79.99,
      stock: 50,
      created_at: new Date(),
      updated_at: new Date()
    }
  },
  { upsert: true }
)

// Replace entire document
db.products.replaceOne(
  { name: "USB-C Cable" },
  {
    name: "USB-C Cable 3.0",
    category: "Accessories",
    price: 14.99,
    stock: 450,
    tags: ["usb-c", "fast-charging", "3.0"],
    specifications: {
      brand: "CablePro",
      warranty_months: 18,
      length_meters: 2,
      version: "USB 3.0"
    },
    created_at: new Date(),
    updated_at: new Date()
  }
)
```

#### Delete Documents

```javascript
// Delete single document
db.products.deleteOne({ name: "Monitor Arm" })

// Delete multiple documents
db.products.deleteMany({
  stock: { $lt: 10 },
  category: "Accessories"
})

// Delete all documents in collection (be careful!)
// db.products.deleteMany({})
```

### 1.3 MongoDB Aggregation Pipeline

Aggregation is MongoDB's powerful framework for data analysis:

```javascript
// Group products by category with statistics
db.products.aggregate([
  {
    $group: {
      _id: "$category",
      total_products: { $sum: 1 },
      avg_price: { $avg: "$price" },
      total_stock: { $sum: "$stock" },
      min_price: { $min: "$price" },
      max_price: { $max: "$price" }
    }
  },
  {
    $sort: { avg_price: -1 }
  }
])

// Find top products by price in each category
db.products.aggregate([
  {
    $sort: { price: -1 }
  },
  {
    $group: {
      _id: "$category",
      top_product: { $first: "$name" },
      highest_price: { $first: "$price" }
    }
  }
])

// Calculate inventory value
db.products.aggregate([
  {
    $project: {
      name: 1,
      category: 1,
      inventory_value: { $multiply: ["$price", "$stock"] }
    }
  },
  {
    $group: {
      _id: "$category",
      total_value: { $sum: "$inventory_value" }
    }
  },
  {
    $sort: { total_value: -1 }
  }
])

// Complex aggregation: Products with gaming tags
db.products.aggregate([
  {
    $match: { tags: "gaming" }
  },
  {
    $unwind: "$tags"
  },
  {
    $group: {
      _id: "$tags",
      count: { $sum: 1 },
      products: { $push: "$name" }
    }
  },
  {
    $sort: { count: -1 }
  }
])

// Products by brand with filtering
db.products.aggregate([
  {
    $match: {
      price: { $gte: 20 },
      stock: { $gt: 50 }
    }
  },
  {
    $group: {
      _id: "$specifications.brand",
      product_count: { $sum: 1 },
      avg_price: { $avg: "$price" },
      products: {
        $push: {
          name: "$name",
          price: "$price"
        }
      }
    }
  },
  {
    $sort: { product_count: -1 }
  }
])
```

### 1.4 MongoDB Indexes

Indexes dramatically improve query performance:

```javascript
// Create single field index
db.products.createIndex({ name: 1 })

// Create compound index
db.products.createIndex({ category: 1, price: -1 })

// Create text index for full-text search
db.products.createIndex({
  name: "text",
  "specifications.brand": "text"
})

// Use text search
db.products.find({ $text: { $search: "wireless gaming" } })

// Create unique index
db.products.createIndex({ name: 1 }, { unique: true })

// Create sparse index (only indexes documents with the field)
db.products.createIndex(
  { "specifications.warranty_months": 1 },
  { sparse: true }
)

// View all indexes
db.products.getIndexes()

// Drop an index
db.products.dropIndex("name_1")

// Analyze query performance
db.products.find({ category: "Electronics" }).explain("executionStats")
```

---

## Part 2: Redis Operations (15 minutes)

### 2.1 Connect to Redis

```bash
# Add Redis connection
aishell> db add redis://localhost:6379 --name redis_cache --type redis

# Verify connection
aishell> db list
```

### 2.2 Redis Basic Operations

```bash
# Switch to Redis context
aishell> redis redis_cache

# String operations
SET user:1000:name "John Doe"
GET user:1000:name
SET user:1000:email "john@example.com" EX 3600  # Expires in 1 hour
SETEX session:abc123 1800 '{"user_id": 1000, "role": "admin"}'
SETNX lock:payment:1000 "processing"  # Set if not exists

# Increment operations (for counters)
SET page:views 0
INCR page:views
INCRBY page:views 10
DECR page:views
GET page:views

# Multiple operations
MSET user:1000:first_name "John" user:1000:last_name "Doe" user:1000:age "30"
MGET user:1000:first_name user:1000:last_name user:1000:age

# Check existence and delete
EXISTS user:1000:name
DEL user:1000:email
EXISTS user:1000:email

# Set expiration
EXPIRE user:1000:name 3600
TTL user:1000:name  # Check time to live
PERSIST user:1000:name  # Remove expiration
```

### 2.3 Redis Data Structures

#### Lists (Queues and Stacks)

```bash
# Push to list (queue operations)
RPUSH queue:emails "email1@test.com"
RPUSH queue:emails "email2@test.com" "email3@test.com"
LPUSH queue:priority "urgent@test.com"

# Pop from list
RPOP queue:emails  # Remove from right (FIFO)
LPOP queue:emails  # Remove from left (LIFO)

# View list
LRANGE queue:emails 0 -1  # Get all items
LLEN queue:emails  # Get length

# Blocking operations (useful for task queues)
BRPOP queue:emails 5  # Wait up to 5 seconds for item

# List as stack
LPUSH stack:undo "action1"
LPUSH stack:undo "action2"
LPOP stack:undo  # Last in, first out
```

#### Sets (Unique Collections)

```bash
# Add to set
SADD tags:product:1 "wireless" "gaming" "ergonomic"
SADD tags:product:2 "gaming" "rgb" "mechanical"

# Check membership
SISMEMBER tags:product:1 "gaming"

# Get all members
SMEMBERS tags:product:1

# Set operations
SINTER tags:product:1 tags:product:2  # Intersection (common tags)
SUNION tags:product:1 tags:product:2  # Union (all unique tags)
SDIFF tags:product:1 tags:product:2   # Difference

# Remove from set
SREM tags:product:1 "ergonomic"

# Count members
SCARD tags:product:1
```

#### Sorted Sets (Leaderboards, Rankings)

```bash
# Add to sorted set with scores
ZADD leaderboard 1000 "player1"
ZADD leaderboard 1500 "player2" 1200 "player3" 2000 "player4"

# Get rank
ZRANK leaderboard "player1"  # 0-based rank (ascending)
ZREVRANK leaderboard "player1"  # Rank (descending)

# Get score
ZSCORE leaderboard "player2"

# Get range by rank
ZRANGE leaderboard 0 2  # Top 3 (ascending)
ZREVRANGE leaderboard 0 2 WITHSCORES  # Top 3 (descending) with scores

# Get range by score
ZRANGEBYSCORE leaderboard 1000 1500

# Increment score
ZINCRBY leaderboard 100 "player1"

# Count members
ZCARD leaderboard

# Remove member
ZREM leaderboard "player3"
```

#### Hashes (Objects)

```bash
# Set hash fields
HSET product:1 name "Wireless Mouse" price "29.99" stock "150"
HMSET product:2 name "Keyboard" price "89.99" stock "75"

# Get hash fields
HGET product:1 name
HMGET product:1 name price stock
HGETALL product:1

# Check field existence
HEXISTS product:1 name

# Increment hash field
HINCRBY product:1 stock -10
HINCRBYFLOAT product:1 price -5.00

# Get all keys or values
HKEYS product:1
HVALS product:1

# Delete field
HDEL product:1 stock
```

### 2.4 Redis Caching Patterns

```bash
# Cache-aside pattern (application code would handle this)
# 1. Try to get from cache
GET user:1000:profile

# 2. If miss, fetch from database and cache
SET user:1000:profile '{"id":1000,"name":"John Doe","email":"john@example.com"}' EX 3600

# Write-through cache (write to cache and database)
SET user:1000:email "newemail@example.com" EX 3600
# Application also writes to database

# Cache invalidation
DEL user:1000:profile
# Or use key patterns
KEYS user:1000:*  # Find keys to invalidate
# DEL user:1000:profile user:1000:email  # Batch delete

# Session storage
SETEX session:abc123 1800 '{"user_id":1000,"role":"admin","login_time":"2025-10-11T10:00:00Z"}'
GET session:abc123
EXPIRE session:abc123 1800  # Extend session

# Rate limiting
INCR rate:api:user:1000
EXPIRE rate:api:user:1000 60  # 60 second window
GET rate:api:user:1000  # Check if exceeded limit
```

### 2.5 Redis Pub/Sub

```bash
# Terminal 1 - Subscribe to channels
SUBSCRIBE notifications
SUBSCRIBE user:1000:updates

# Terminal 2 - Publish messages
PUBLISH notifications "New product launch!"
PUBLISH user:1000:updates '{"type":"order","order_id":5000,"status":"shipped"}'

# Pattern subscription (Terminal 1)
PSUBSCRIBE user:*:updates  # Subscribe to all user updates

# Terminal 2
PUBLISH user:2000:updates '{"type":"message","from":"admin"}'

# Unsubscribe
UNSUBSCRIBE notifications
PUNSUBSCRIBE user:*:updates
```

---

## Part 3: Multi-Database Coordination (15 minutes)

### 3.1 Cross-Database Transaction Pattern

AI-Shell doesn't provide true distributed transactions, but you can coordinate operations:

```bash
# Example: Create order in PostgreSQL and cache in Redis

# 1. Start transaction in PostgreSQL
aishell> db use postgres_main
aishell> BEGIN;

# 2. Insert order
INSERT INTO orders (user_id, total_amount, status, created_at)
VALUES (1000, 159.97, 'pending', CURRENT_TIMESTAMP)
RETURNING order_id;

# Note the order_id (e.g., 5000)

# 3. Insert order items
INSERT INTO order_items (order_id, product_id, quantity, price)
VALUES
  (5000, 1, 2, 29.99),
  (5000, 2, 1, 89.99);

# 4. Update product stock in MongoDB
aishell> mongo mongodb_main
db.products.updateMany(
  { _id: { $in: [ObjectId("..."), ObjectId("...")] } },
  {
    $inc: { stock: -2 },
    $set: { updated_at: new Date() }
  }
)

# 5. Cache order in Redis
aishell> redis redis_cache
SETEX order:5000 3600 '{"order_id":5000,"user_id":1000,"total":159.97,"status":"pending"}'
ZADD recent:orders:user:1000 1728649200 "5000"

# 6. Commit PostgreSQL transaction
aishell> db use postgres_main
COMMIT;

# If anything fails, rollback PostgreSQL and clean up Redis
# ROLLBACK;
# DEL order:5000
# ZREM recent:orders:user:1000 "5000"
```

### 3.2 Cross-Database Query Pattern

Query data from multiple databases and combine results:

```bash
# 1. Get order summary from PostgreSQL
aishell> db use postgres_main
SELECT
  o.order_id,
  o.user_id,
  o.total_amount,
  o.status,
  array_agg(oi.product_id) as product_ids
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_id = 5000
GROUP BY o.order_id;

# Result: order_id=5000, product_ids=[1, 2]

# 2. Get product details from MongoDB
aishell> mongo mongodb_main
db.products.find(
  { _id: { $in: [ObjectId("product1_id"), ObjectId("product2_id")] } },
  { name: 1, price: 1, specifications: 1 }
)

# 3. Check cache status in Redis
aishell> redis redis_cache
EXISTS order:5000
GET order:5000
```

### 3.3 Data Synchronization Pattern

Keep data synchronized across databases:

```bash
# Example: User profile sync across databases

# 1. Update in PostgreSQL (source of truth)
aishell> db use postgres_main
BEGIN;
UPDATE users
SET email = 'newemail@example.com',
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = 1000
RETURNING *;
COMMIT;

# 2. Update cache in Redis
aishell> redis redis_cache
SET user:1000:email "newemail@example.com" EX 3600
DEL user:1000:profile  # Invalidate cached profile
SET user:1000:profile:version "v2"  # Versioning

# 3. Update denormalized data in MongoDB
aishell> mongo mongodb_main
db.orders.updateMany(
  { user_id: 1000 },
  {
    $set: {
      "user_email": "newemail@example.com",
      "last_synced": new Date()
    }
  }
)

# 4. Publish change event to Redis pub/sub
aishell> redis redis_cache
PUBLISH user:updates '{"user_id":1000,"field":"email","value":"newemail@example.com","timestamp":"2025-10-11T10:30:00Z"}'
```

### 3.4 Multi-Database Analytics

Combine data from multiple sources for analytics:

```bash
# 1. Get order statistics from PostgreSQL
aishell> db use postgres_main
SELECT
  DATE_TRUNC('day', created_at) as order_date,
  COUNT(*) as order_count,
  SUM(total_amount) as daily_revenue
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY order_date DESC;

# 2. Get product statistics from MongoDB
aishell> mongo mongodb_main
db.products.aggregate([
  {
    $group: {
      _id: "$category",
      total_products: { $sum: 1 },
      avg_price: { $avg: "$price" },
      total_inventory_value: {
        $sum: { $multiply: ["$price", "$stock"] }
      }
    }
  }
])

# 3. Get cache hit rate from Redis
aishell> redis redis_cache
INFO stats
# Look for keyspace_hits and keyspace_misses

# Calculate cache efficiency
# hit_rate = hits / (hits + misses)
```

---

## Part 4: Performance Optimization (10 minutes)

### 4.1 MongoDB Optimization

```javascript
// 1. Use indexes effectively
db.products.createIndex({ category: 1, price: -1 })
db.products.createIndex({ tags: 1 })

// 2. Analyze query performance
db.products.find({ category: "Electronics" }).explain("executionStats")

// 3. Use projection to limit fields
db.products.find(
  { category: "Electronics" },
  { name: 1, price: 1, _id: 0 }
)

// 4. Batch operations
var bulk = db.products.initializeUnorderedBulkOp();
bulk.find({ stock: { $lt: 50 } }).update({ $set: { reorder: true } });
bulk.find({ stock: { $gt: 500 } }).update({ $set: { overstocked: true } });
bulk.execute();

// 5. Use aggregation pipeline efficiently
db.products.aggregate([
  { $match: { category: "Electronics" } },  // Filter early
  { $project: { name: 1, price: 1 } },      // Limit fields early
  { $sort: { price: -1 } },
  { $limit: 10 }
])

// 6. Connection pooling (configured in connection string)
// mongodb://localhost:27017/ecommerce?maxPoolSize=50
```

### 4.2 Redis Optimization

```bash
# 1. Use appropriate data structures
# Use HASH instead of multiple keys
HMSET user:1000 name "John" email "john@example.com" age "30"
# Instead of: SET user:1000:name, SET user:1000:email, etc.

# 2. Set expiration on cached data
SETEX cache:product:1 3600 '{"name":"Mouse","price":29.99}'

# 3. Use pipelining for multiple commands (in application code)
# Redis will execute these as a batch

# 4. Monitor slow queries
CONFIG SET slowlog-log-slower-than 10000  # 10ms
SLOWLOG GET 10

# 5. Check memory usage
INFO memory
MEMORY USAGE user:1000

# 6. Use appropriate eviction policies
CONFIG GET maxmemory-policy
# allkeys-lru: Remove least recently used keys
# volatile-ttl: Remove keys with shortest TTL

# 7. Optimize key naming
# Use namespaces: product:1:name instead of product_1_name
# Shorter keys save memory: p:1:n instead of product:1:name

# 8. Monitor performance
INFO stats
INFO cpu
```

### 4.3 Cross-Database Optimization

```bash
# 1. Cache frequently accessed data
# PostgreSQL query result → Redis cache
aishell> redis redis_cache
SETEX query:top_products:24h 3600 '[{"id":1,"name":"Mouse"},{"id":2,"name":"Keyboard"}]'

# 2. Use Redis as a queue for batch operations
LPUSH batch:update:products "1" "2" "3" "4" "5"
# Worker processes batch from queue

# 3. Denormalize strategically
# Keep user email in MongoDB orders for quick access
# Avoid joining across databases in real-time

# 4. Use Redis pub/sub for cache invalidation
PUBLISH cache:invalidate:products "1,2,3"

# 5. Monitor all database connections
aishell> db list
aishell> db stats postgres_main
aishell> db stats mongodb_main
```

---

## Practice Exercises

### Exercise 1: E-commerce Product Catalog

**Objective:** Build a complete product catalog system using MongoDB

```javascript
// 1. Create products collection with indexes
db.products.createIndex({ name: "text", description: "text" })
db.products.createIndex({ category: 1, price: -1 })
db.products.createIndex({ tags: 1 })

// 2. Insert sample products
db.products.insertMany([
  // Add 10-15 diverse products
])

// 3. Queries to implement:
// - Find products by category and price range
// - Full-text search for products
// - Top 5 products by price in each category
// - Products with specific tags
// - Calculate average price per category
```

### Exercise 2: Redis Caching Layer

**Objective:** Implement a caching strategy

```bash
# 1. Cache user sessions
SETEX session:xyz123 1800 '{"user_id":1000,"role":"admin"}'

# 2. Implement rate limiting (100 requests per minute)
INCR rate:api:user:1000
EXPIRE rate:api:user:1000 60

# 3. Create a leaderboard
ZADD game:scores 1500 "player1" 2000 "player2" 1800 "player3"

# 4. Cache product catalog
HMSET product:cache:1 name "Mouse" price "29.99" stock "150"
```

### Exercise 3: Multi-Database Order Processing

**Objective:** Process an order across PostgreSQL, MongoDB, and Redis

```bash
# Complete workflow:
# 1. Create order in PostgreSQL
# 2. Update product stock in MongoDB
# 3. Cache order in Redis
# 4. Add to recent orders sorted set
# 5. Publish order event
# 6. Implement rollback if any step fails
```

---

## Troubleshooting

### MongoDB Issues

```javascript
// Connection issues
db.adminCommand({ ping: 1 })

// Check collection stats
db.products.stats()

// Find slow queries
db.setProfilingLevel(1, { slowms: 100 })
db.system.profile.find().limit(10).sort({ ts: -1 })

// Repair collection
db.products.validate()
```

### Redis Issues

```bash
# Check connection
PING

# Check memory usage
INFO memory

# Find keys pattern
KEYS product:*  # Warning: expensive in production
SCAN 0 MATCH product:* COUNT 100  # Better alternative

# Check replication
INFO replication

# Monitor commands in real-time
MONITOR  # Warning: performance impact
```

---

## Next Steps

Congratulations! You've mastered NoSQL databases in AI-Shell. You now understand:

- MongoDB CRUD operations and aggregations
- Redis data structures and caching patterns
- Multi-database coordination
- Performance optimization techniques

**Continue to Part 5:** [Backup, Restore & Migration](./HANDS_ON_PART5_DATA_OPS.md)

Learn about:
- Creating encrypted backups
- Scheduling automated backups
- Point-in-time restore
- Database migrations
- Rollback procedures

---

## Quick Reference

### MongoDB Common Commands

```javascript
// CRUD
db.collection.insertOne(doc)
db.collection.find(query)
db.collection.updateOne(query, update)
db.collection.deleteOne(query)

// Aggregation
db.collection.aggregate([stages])

// Indexes
db.collection.createIndex(keys)
db.collection.getIndexes()
```

### Redis Common Commands

```bash
# Strings
SET key value
GET key

# Lists
LPUSH key value
RPOP key

# Sets
SADD key member
SMEMBERS key

# Sorted Sets
ZADD key score member
ZRANGE key start stop

# Hashes
HSET key field value
HGETALL key
```

### AI-Shell Database Commands

```bash
aishell> db add <connection-string> --name <name> --type <type>
aishell> db list
aishell> db use <name>
aishell> mongo <name>
aishell> redis <name>
aishell> db stats <name>
```
