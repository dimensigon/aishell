# MongoDB CLI Usage Examples

## Quick Start

### 1. Connect to MongoDB
```bash
# Connect to local MongoDB
ai-shell mongo connect "mongodb://admin:MyMongoPass123@localhost:27017/myapp?authSource=admin"

# Connect with custom name
ai-shell mongo connect "mongodb://localhost:27017/myapp" --name myapp

# Connect to MongoDB Atlas (cloud)
ai-shell mongo connect "mongodb+srv://user:pass@cluster.mongodb.net/production" --name prod
```

### 2. List Collections
```bash
ai-shell mongo collections
ai-shell mongo collections production
```

### 3. Query Documents
```bash
# Find all users
ai-shell mongo query '{}' --collection users

# Find users over 30
ai-shell mongo query '{"age": {"$gte": 30}}' -c users

# Query with projection (select specific fields)
ai-shell mongo query '{}' -c users --projection '{"name": 1, "email": 1, "_id": 0}'

# Query with sorting
ai-shell mongo query '{"status": "active"}' -c users --sort '{"createdAt": -1}' --limit 10

# Pagination
ai-shell mongo query '{}' -c users --skip 20 --limit 10
```

### 4. Aggregation Pipelines
```bash
# Group by category and count
ai-shell mongo aggregate '[{"$group": {"_id": "$category", "count": {"$sum": 1}}}]' -c products

# Complex aggregation with multiple stages
ai-shell mongo aggregate '[
  {"$match": {"status": "completed"}},
  {"$group": {"_id": "$customerId", "total": {"$sum": "$amount"}}},
  {"$sort": {"total": -1}},
  {"$limit": 10}
]' -c orders

# Aggregation with computed fields
ai-shell mongo aggregate '[
  {"$project": {
    "name": 1,
    "total": {"$multiply": ["$price", "$quantity"]}
  }}
]' -c products

# View execution plan
ai-shell mongo aggregate '[{"$match": {"price": {"$gte": 100}}}]' -c products --explain
```

### 5. Index Management
```bash
# List all indexes
ai-shell mongo indexes users

# View indexes in JSON format
ai-shell mongo indexes products --format json
```

### 6. Import Data
```bash
# Import JSON array
ai-shell mongo import users.json --collection users

# Import and drop existing collection
ai-shell mongo import backup.json -c users --drop

# Import single document
ai-shell mongo import single-user.json -c users
```

### 7. Export Data
```bash
# Export entire collection
ai-shell mongo export users --output users-backup.json

# Export with filter
ai-shell mongo export users -o active-users.json --filter '{"status": "active"}'

# Export with limit
ai-shell mongo export orders -o recent-orders.json --limit 1000
```

### 8. Connection Management
```bash
# List all connections
ai-shell mongo connections

# View connection statistics
ai-shell mongo stats
ai-shell mongo stats prod

# Disconnect
ai-shell mongo disconnect
ai-shell mongo disconnect prod
```

## Advanced Examples

### Complex Queries

```bash
# Multiple conditions with $and
ai-shell mongo query '{"$and": [{"age": {"$gte": 18}}, {"age": {"$lte": 65}}]}' -c users

# Use $or operator
ai-shell mongo query '{"$or": [{"status": "active"}, {"premium": true}]}' -c users

# Array field queries
ai-shell mongo query '{"tags": {"$in": ["javascript", "typescript"]}}' -c posts

# Nested field queries
ai-shell mongo query '{"address.city": "New York"}' -c users
```

### Advanced Aggregations

```bash
# Sales by month
ai-shell mongo aggregate '[
  {"$group": {
    "_id": {
      "year": {"$year": "$date"},
      "month": {"$month": "$date"}
    },
    "revenue": {"$sum": "$amount"},
    "orders": {"$sum": 1}
  }},
  {"$sort": {"_id.year": -1, "_id.month": -1}}
]' -c sales

# Top customers by spending
ai-shell mongo aggregate '[
  {"$match": {"status": "completed"}},
  {"$group": {
    "_id": "$customerId",
    "totalSpent": {"$sum": "$amount"},
    "orderCount": {"$sum": 1},
    "avgOrder": {"$avg": "$amount"}
  }},
  {"$sort": {"totalSpent": -1}},
  {"$limit": 10}
]' -c orders

# Product analytics
ai-shell mongo aggregate '[
  {"$lookup": {
    "from": "categories",
    "localField": "categoryId",
    "foreignField": "_id",
    "as": "category"
  }},
  {"$unwind": "$category"},
  {"$group": {
    "_id": "$category.name",
    "products": {"$sum": 1},
    "avgPrice": {"$avg": "$price"}
  }}
]' -c products
```

### Batch Operations

```bash
# Export filtered data
ai-shell mongo export users -o premium-users.json --filter '{"premium": true}'

# Export specific time range
ai-shell mongo export logs -o recent-logs.json --filter '{
  "timestamp": {"$gte": {"$date": "2025-01-01"}}
}' --limit 10000

# Import with cleanup
ai-shell mongo import seed-data.json -c test_collection --drop
```

## Data Migration Workflow

```bash
# 1. Export from source
ai-shell mongo connect "mongodb://source:27017/sourcedb" --name source
ai-shell mongo export users -o users-migration.json
ai-shell mongo disconnect source

# 2. Import to destination
ai-shell mongo connect "mongodb://dest:27017/destdb" --name dest
ai-shell mongo import users-migration.json -c users
ai-shell mongo disconnect dest
```

## Monitoring Workflow

```bash
# Connect
ai-shell mongo connect "mongodb://localhost:27017/production" --name prod

# Check collections
ai-shell mongo collections

# Check indexes
ai-shell mongo indexes users
ai-shell mongo indexes orders

# View statistics
ai-shell mongo stats

# Query slow queries
ai-shell mongo query '{"duration": {"$gte": 1000}}' -c query_logs --sort '{"duration": -1}' --limit 10

# Export logs
ai-shell mongo export query_logs -o slow-queries.json --filter '{"duration": {"$gte": 1000}}'
```

## Error Handling

The CLI provides clear error messages:

```bash
# Invalid connection string
$ ai-shell mongo connect "invalid://connection"
✗ Error: Invalid MongoDB connection string format

# No active connection
$ ai-shell mongo query '{}' -c users
✗ Error: No active MongoDB connection. Use "ai-shell mongo connect" first.

# Invalid JSON
$ ai-shell mongo query 'invalid json' -c users
✗ Error: Invalid JSON: Unexpected token i in JSON at position 0
```

## Tips and Best Practices

1. **Connection Strings**: Always use authentication in production
2. **Projections**: Use projections to reduce data transfer
3. **Indexes**: Check indexes before running large queries
4. **Limits**: Always use limits when exploring data
5. **Filters**: Test filters on small datasets first
6. **Aggregations**: Use $explain to optimize pipelines
7. **Exports**: Use filters to export only needed data
8. **Imports**: Test imports on copy databases first

## JSON Format Examples

### Filter JSON
```json
{
  "age": {"$gte": 18},
  "status": "active",
  "tags": {"$in": ["premium", "vip"]}
}
```

### Projection JSON
```json
{
  "name": 1,
  "email": 1,
  "createdAt": 1,
  "_id": 0
}
```

### Sort JSON
```json
{
  "createdAt": -1,
  "name": 1
}
```

### Aggregation Pipeline JSON
```json
[
  {"$match": {"status": "active"}},
  {"$group": {"_id": "$category", "count": {"$sum": 1}}},
  {"$sort": {"count": -1}},
  {"$limit": 10}
]
```

## Output Formats

### Table Format (default)
```
┌──────────┬─────┬────────────┐
│ name     │ age │ city       │
├──────────┼─────┼────────────┤
│ Alice    │ 30  │ New York   │
│ Bob      │ 25  │ London     │
└──────────┴─────┴────────────┘

2 document(s) returned
```

### JSON Format
```bash
ai-shell mongo query '{}' -c users --format json
```
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "name": "Alice",
    "age": 30,
    "city": "New York"
  },
  {
    "_id": "507f1f77bcf86cd799439012",
    "name": "Bob",
    "age": 25,
    "city": "London"
  }
]
```
