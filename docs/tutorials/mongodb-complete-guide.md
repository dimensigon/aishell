# MongoDB Complete Guide

A comprehensive tutorial for MongoDB database management, from basics to advanced aggregation pipelines.

**Estimated Time:** 6-8 hours
**Prerequisites:** Basic database knowledge, Docker installed

---

## Table of Contents

1. [Setup and Installation](#1-setup-and-installation)
2. [Database and Collection Management](#2-database-and-collection-management)
3. [Document CRUD Operations](#3-document-crud-operations)
4. [Querying and Filtering](#4-querying-and-filtering)
5. [Aggregation Pipeline](#5-aggregation-pipeline)
6. [Indexing and Performance](#6-indexing-and-performance)
7. [Data Modeling Patterns](#7-data-modeling-patterns)
8. [Transactions and Atomicity](#8-transactions-and-atomicity)
9. [Backup and Restore](#9-backup-and-restore)
10. [Monitoring and Optimization](#10-monitoring-and-optimization)
11. [Replica Sets Basics](#11-replica-sets-basics)
12. [Real-World Scenarios](#12-real-world-scenarios)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Setup and Installation

**Time:** 20 minutes

### 1.1 Docker Setup

```bash
# Pull MongoDB image
docker pull mongo:7

# Run MongoDB container
docker run -d \
  --name my-mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=secure_password \
  -p 27017:27017 \
  -v mongodata:/data/db \
  mongo:7

# Verify container is running
docker ps | grep mongo
```

### 1.2 Connect to MongoDB

```bash
# Using docker exec with mongosh
docker exec -it my-mongodb mongosh -u admin -p secure_password

# Using AIShell
aishell mongodb connect --host localhost --port 27017 --username admin --password secure_password
```

### 1.3 Initial Configuration

```javascript
// Check MongoDB version
db.version()

// Show current database
db.getName()

// List all databases
show dbs

// Create and switch to database
use myapp

// Show collections
show collections

// Get server status
db.serverStatus()

// Set profiling level
db.setProfilingLevel(1, { slowms: 100 })
```

**Expected Output:**
```
7.0.x
```

**Exercise 1.1:** Set up MongoDB with authentication
- Create a database for your application
- Create a user with readWrite permissions
- Test connection with the new user

<details>
<summary>Solution</summary>

```javascript
// Connect as admin
use admin
db.auth("admin", "secure_password")

// Create database and user
use myapp
db.createUser({
  user: "app_user",
  pwd: "app_password",
  roles: [
    { role: "readWrite", db: "myapp" }
  ]
})

// Test connection
// Exit and reconnect
use myapp
db.auth("app_user", "app_password")

// Verify permissions
db.runCommand({ connectionStatus: 1 })
```
</details>

---

## 2. Database and Collection Management

**Time:** 30 minutes

### 2.1 Database Operations

```javascript
// Create/switch to database
use ecommerce

// Show current database
db.getName()

// List all databases
show dbs

// Database stats
db.stats()

// Drop database (careful!)
use test_db
db.dropDatabase()
```

### 2.2 Collection Operations

```javascript
// Create collection explicitly
db.createCollection("customers")

// Create collection with validation
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["customerId", "items", "total"],
      properties: {
        customerId: {
          bsonType: "objectId",
          description: "Customer ID is required"
        },
        items: {
          bsonType: "array",
          minItems: 1,
          description: "At least one item is required"
        },
        total: {
          bsonType: "number",
          minimum: 0,
          description: "Total must be a positive number"
        },
        status: {
          enum: ["pending", "processing", "shipped", "delivered", "cancelled"],
          description: "Status must be one of the enum values"
        }
      }
    }
  }
})

// List collections
show collections
db.getCollectionNames()

// Collection statistics
db.customers.stats()

// Rename collection
db.old_name.renameCollection("new_name")

// Drop collection
db.test_collection.drop()
```

### 2.3 Capped Collections

```javascript
// Create capped collection (fixed size, FIFO)
db.createCollection("logs", {
  capped: true,
  size: 10485760, // 10MB
  max: 10000 // Maximum 10,000 documents
})

// Insert into capped collection
db.logs.insertMany([
  { timestamp: new Date(), level: "info", message: "Application started" },
  { timestamp: new Date(), level: "warn", message: "High memory usage" },
  { timestamp: new Date(), level: "error", message: "Connection failed" }
])

// Query capped collection (newest first with natural order)
db.logs.find().sort({ $natural: -1 }).limit(10)
```

**Exercise 2.1:** Create a complete schema
- Create a blog database
- Create collections: users, posts, comments
- Add validation rules
- Create appropriate indexes

<details>
<summary>Solution</summary>

```javascript
use blog

// Users collection with validation
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["username", "email", "passwordHash"],
      properties: {
        username: {
          bsonType: "string",
          minLength: 3,
          maxLength: 50
        },
        email: {
          bsonType: "string",
          pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        },
        passwordHash: {
          bsonType: "string"
        },
        profile: {
          bsonType: "object",
          properties: {
            bio: { bsonType: "string" },
            avatar: { bsonType: "string" }
          }
        },
        createdAt: {
          bsonType: "date"
        }
      }
    }
  }
})

// Posts collection
db.createCollection("posts", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["userId", "title", "content"],
      properties: {
        userId: { bsonType: "objectId" },
        title: {
          bsonType: "string",
          minLength: 5,
          maxLength: 200
        },
        content: { bsonType: "string" },
        tags: {
          bsonType: "array",
          items: { bsonType: "string" }
        },
        publishedAt: { bsonType: "date" },
        status: {
          enum: ["draft", "published", "archived"]
        }
      }
    }
  }
})

// Comments collection
db.createCollection("comments", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["postId", "userId", "content"],
      properties: {
        postId: { bsonType: "objectId" },
        userId: { bsonType: "objectId" },
        content: {
          bsonType: "string",
          minLength: 1,
          maxLength: 1000
        },
        createdAt: { bsonType: "date" }
      }
    }
  }
})

// Create indexes
db.users.createIndex({ email: 1 }, { unique: true })
db.users.createIndex({ username: 1 }, { unique: true })
db.posts.createIndex({ userId: 1, publishedAt: -1 })
db.posts.createIndex({ tags: 1 })
db.comments.createIndex({ postId: 1, createdAt: -1 })
```
</details>

---

## 3. Document CRUD Operations

**Time:** 45 minutes

### 3.1 Insert Operations

```javascript
// Insert single document
db.customers.insertOne({
  email: "john@example.com",
  firstName: "John",
  lastName: "Doe",
  phone: "+1234567890",
  address: {
    street: "123 Main St",
    city: "New York",
    state: "NY",
    zip: "10001"
  },
  tags: ["premium", "early_adopter"],
  createdAt: new Date()
})

// Insert multiple documents
db.customers.insertMany([
  {
    email: "alice@example.com",
    firstName: "Alice",
    lastName: "Johnson",
    phone: "+1234567891",
    createdAt: new Date()
  },
  {
    email: "bob@example.com",
    firstName: "Bob",
    lastName: "Smith",
    phone: "+1234567892",
    createdAt: new Date()
  }
])

// Insert with specific _id
db.products.insertOne({
  _id: "PROD-001",
  name: "Laptop",
  price: 999.99,
  category: "Electronics",
  stock: 50
})

// Ordered vs unordered inserts
db.customers.insertMany([
  { email: "user1@example.com", firstName: "User1" },
  { email: "user2@example.com", firstName: "User2" },
  { email: "user1@example.com", firstName: "Duplicate" } // Will fail
], { ordered: false }) // Continue on error
```

### 3.2 Query Operations

```javascript
// Find all documents
db.customers.find()

// Find with filter
db.customers.find({ firstName: "John" })

// Find one document
db.customers.findOne({ email: "john@example.com" })

// Find with projection (select specific fields)
db.customers.find(
  { tags: "premium" },
  { email: 1, firstName: 1, lastName: 1, _id: 0 }
)

// Find with multiple conditions
db.products.find({
  category: "Electronics",
  price: { $lt: 1000 },
  stock: { $gt: 0 }
})

// Query nested documents
db.customers.find({
  "address.city": "New York",
  "address.state": "NY"
})

// Query arrays
db.customers.find({ tags: "premium" })
db.customers.find({ tags: { $in: ["premium", "vip"] } })
db.customers.find({ tags: { $all: ["premium", "early_adopter"] } })

// Query with regex
db.customers.find({
  email: { $regex: /@gmail\.com$/, $options: "i" }
})
```

### 3.3 Update Operations

```javascript
// Update single document
db.customers.updateOne(
  { email: "john@example.com" },
  {
    $set: { phone: "+9876543210", updatedAt: new Date() },
    $inc: { loyaltyPoints: 100 }
  }
)

// Update multiple documents
db.products.updateMany(
  { category: "Electronics" },
  {
    $mul: { price: 0.9 } // 10% discount
  }
)

// Replace entire document
db.customers.replaceOne(
  { email: "old@example.com" },
  {
    email: "new@example.com",
    firstName: "New",
    lastName: "User",
    createdAt: new Date()
  }
)

// Update or insert (upsert)
db.customers.updateOne(
  { email: "new@example.com" },
  {
    $set: {
      firstName: "New",
      lastName: "Customer",
      createdAt: new Date()
    }
  },
  { upsert: true }
)

// Update array elements
db.customers.updateOne(
  { email: "john@example.com" },
  {
    $push: { tags: "loyal_customer" },
    $addToSet: { tags: "verified" } // Add only if not exists
  }
)

// Remove from array
db.customers.updateOne(
  { email: "john@example.com" },
  {
    $pull: { tags: "early_adopter" }
  }
)

// Update array element by position
db.orders.updateOne(
  { _id: ObjectId("..."), "items.sku": "PROD-001" },
  {
    $set: { "items.$.quantity": 5 }
  }
)

// Update with findOneAndUpdate (returns document)
db.customers.findOneAndUpdate(
  { email: "john@example.com" },
  { $inc: { loyaltyPoints: 50 } },
  { returnDocument: "after", projection: { email: 1, loyaltyPoints: 1 } }
)
```

### 3.4 Delete Operations

```javascript
// Delete single document
db.customers.deleteOne({ email: "delete@example.com" })

// Delete multiple documents
db.customers.deleteMany({
  createdAt: { $lt: new Date("2023-01-01") },
  tags: { $size: 0 }
})

// Find and delete
db.customers.findOneAndDelete(
  { email: "remove@example.com" },
  { projection: { email: 1, firstName: 1 } }
)

// Delete all documents in collection
db.test_collection.deleteMany({})
```

**Exercise 3.1:** Complex CRUD operations
- Insert 10 sample customers with orders
- Update all orders from last month
- Add a new field to all documents
- Delete inactive customers

<details>
<summary>Solution</summary>

```javascript
// Insert sample customers
const customerIds = []
for (let i = 1; i <= 10; i++) {
  const result = db.customers.insertOne({
    email: `customer${i}@example.com`,
    firstName: `Customer${i}`,
    lastName: "Test",
    loyaltyPoints: Math.floor(Math.random() * 1000),
    isActive: i % 2 === 0,
    createdAt: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000)
  })
  customerIds.push(result.insertedId)
}

// Insert sample orders
customerIds.forEach(customerId => {
  const orderCount = Math.floor(Math.random() * 5) + 1
  for (let i = 0; i < orderCount; i++) {
    db.orders.insertOne({
      customerId: customerId,
      items: [
        {
          sku: `PROD-${Math.floor(Math.random() * 100)}`,
          quantity: Math.floor(Math.random() * 5) + 1,
          price: Math.random() * 100
        }
      ],
      total: Math.random() * 500,
      status: ["pending", "processing", "shipped", "delivered"][Math.floor(Math.random() * 4)],
      orderDate: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000)
    })
  }
})

// Update all orders from last month
const lastMonth = new Date()
lastMonth.setMonth(lastMonth.getMonth() - 1)

db.orders.updateMany(
  { orderDate: { $gte: lastMonth } },
  {
    $set: { processedAt: new Date() },
    $inc: { priority: 1 }
  }
)

// Add new field to all customers
db.customers.updateMany(
  {},
  {
    $set: {
      customerSegment: "standard",
      lastActivityAt: new Date()
    }
  }
)

// Update segment based on loyalty points
db.customers.updateMany(
  { loyaltyPoints: { $gte: 500 } },
  { $set: { customerSegment: "premium" } }
)

db.customers.updateMany(
  { loyaltyPoints: { $gte: 800 } },
  { $set: { customerSegment: "vip" } }
)

// Delete inactive customers with no orders
const inactiveCustomers = db.customers.find(
  { isActive: false },
  { _id: 1 }
).toArray()

const inactiveIds = inactiveCustomers.map(c => c._id)

const customersWithOrders = db.orders.distinct("customerId", {
  customerId: { $in: inactiveIds }
})

const toDelete = inactiveIds.filter(id => !customersWithOrders.includes(id))

db.customers.deleteMany({
  _id: { $in: toDelete }
})

// Verify results
print("Active customers:", db.customers.countDocuments({ isActive: true }))
print("Total orders:", db.orders.countDocuments())
print("Deleted customers:", toDelete.length)
```
</details>

---

## 4. Querying and Filtering

**Time:** 45 minutes

### 4.1 Comparison Operators

```javascript
// Equal to
db.products.find({ price: 999.99 })

// Not equal to
db.products.find({ category: { $ne: "Electronics" } })

// Greater than / Less than
db.products.find({
  price: { $gt: 100, $lt: 1000 }
})

// Greater/Less than or equal
db.products.find({
  stock: { $gte: 10, $lte: 100 }
})

// In array
db.products.find({
  category: { $in: ["Electronics", "Computers", "Phones"] }
})

// Not in array
db.customers.find({
  email: { $nin: ["banned1@example.com", "banned2@example.com"] }
})
```

### 4.2 Logical Operators

```javascript
// AND (implicit)
db.products.find({
  category: "Electronics",
  price: { $lt: 1000 },
  stock: { $gt: 0 }
})

// OR
db.products.find({
  $or: [
    { category: "Electronics" },
    { price: { $lt: 50 } }
  ]
})

// AND with OR
db.products.find({
  $and: [
    {
      $or: [
        { category: "Electronics" },
        { category: "Computers" }
      ]
    },
    { price: { $lt: 1000 } }
  ]
})

// NOT
db.products.find({
  price: { $not: { $gt: 1000 } }
})

// NOR
db.products.find({
  $nor: [
    { price: { $lt: 100 } },
    { stock: 0 }
  ]
})
```

### 4.3 Element Operators

```javascript
// Field exists
db.customers.find({
  phone: { $exists: true }
})

// Field type
db.products.find({
  price: { $type: "double" }
})

// Field type (multiple types)
db.data.find({
  value: { $type: ["string", "number"] }
})
```

### 4.4 Array Operators

```javascript
// Array contains element
db.customers.find({
  tags: "premium"
})

// Array contains all elements
db.customers.find({
  tags: { $all: ["premium", "verified"] }
})

// Array size
db.customers.find({
  tags: { $size: 3 }
})

// Array element match
db.orders.find({
  items: {
    $elemMatch: {
      quantity: { $gte: 5 },
      price: { $lt: 100 }
    }
  }
})
```

### 4.5 Sorting and Limiting

```javascript
// Sort ascending
db.products.find().sort({ price: 1 })

// Sort descending
db.products.find().sort({ price: -1 })

// Multiple sort fields
db.products.find().sort({ category: 1, price: -1 })

// Limit results
db.products.find().limit(10)

// Skip and limit (pagination)
db.products.find().skip(20).limit(10)

// Count documents
db.products.countDocuments({ category: "Electronics" })

// Distinct values
db.products.distinct("category")
```

### 4.6 Text Search

```javascript
// Create text index
db.products.createIndex({
  name: "text",
  description: "text"
})

// Text search
db.products.find({
  $text: { $search: "laptop computer" }
})

// Text search with score
db.products.find(
  { $text: { $search: "laptop" } },
  { score: { $meta: "textScore" } }
).sort({ score: { $meta: "textScore" } })

// Text search with exact phrase
db.products.find({
  $text: { $search: "\"gaming laptop\"" }
})
```

**Exercise 4.1:** Complex queries
- Find top 10 customers by loyalty points
- Find products in multiple categories with stock > 10
- Search for customers in specific cities
- Find orders from last 30 days with status "shipped"

<details>
<summary>Solution</summary>

```javascript
// Top 10 customers by loyalty points
db.customers.find(
  { isActive: true },
  { email: 1, firstName: 1, lastName: 1, loyaltyPoints: 1 }
)
  .sort({ loyaltyPoints: -1 })
  .limit(10)

// Products in multiple categories with stock > 10
db.products.find({
  category: { $in: ["Electronics", "Computers", "Phones"] },
  stock: { $gt: 10 }
})
  .sort({ category: 1, name: 1 })

// Customers in specific cities
db.customers.find({
  "address.city": { $in: ["New York", "Los Angeles", "Chicago"] },
  isActive: true
})
  .projection({ email: 1, firstName: 1, lastName: 1, "address.city": 1 })

// Orders from last 30 days with status "shipped"
const thirtyDaysAgo = new Date()
thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

db.orders.find({
  orderDate: { $gte: thirtyDaysAgo },
  status: "shipped"
})
  .sort({ orderDate: -1 })

// Complex query: High-value customers with recent orders
db.customers.aggregate([
  {
    $match: {
      loyaltyPoints: { $gte: 500 },
      isActive: true
    }
  },
  {
    $lookup: {
      from: "orders",
      localField: "_id",
      foreignField: "customerId",
      as: "orders"
    }
  },
  {
    $addFields: {
      recentOrders: {
        $filter: {
          input: "$orders",
          as: "order",
          cond: {
            $gte: ["$$order.orderDate", thirtyDaysAgo]
          }
        }
      }
    }
  },
  {
    $match: {
      recentOrders: { $ne: [] }
    }
  },
  {
    $project: {
      email: 1,
      firstName: 1,
      lastName: 1,
      loyaltyPoints: 1,
      recentOrderCount: { $size: "$recentOrders" },
      totalSpent: { $sum: "$recentOrders.total" }
    }
  },
  {
    $sort: { totalSpent: -1 }
  }
])
```
</details>

---

## 5. Aggregation Pipeline

**Time:** 90 minutes

### 5.1 Basic Aggregation Stages

```javascript
// $match - Filter documents
db.orders.aggregate([
  {
    $match: {
      status: "completed",
      orderDate: { $gte: new Date("2024-01-01") }
    }
  }
])

// $project - Select and transform fields
db.orders.aggregate([
  {
    $project: {
      customerId: 1,
      total: 1,
      year: { $year: "$orderDate" },
      month: { $month: "$orderDate" }
    }
  }
])

// $group - Group and aggregate
db.orders.aggregate([
  {
    $group: {
      _id: "$status",
      count: { $sum: 1 },
      totalRevenue: { $sum: "$total" },
      avgOrder: { $avg: "$total" },
      maxOrder: { $max: "$total" },
      minOrder: { $min: "$total" }
    }
  }
])

// $sort - Sort results
db.orders.aggregate([
  {
    $group: {
      _id: "$customerId",
      totalSpent: { $sum: "$total" }
    }
  },
  {
    $sort: { totalSpent: -1 }
  }
])

// $limit and $skip
db.orders.aggregate([
  { $sort: { orderDate: -1 } },
  { $limit: 10 }
])
```

### 5.2 Advanced Aggregation

```javascript
// $lookup - Join collections
db.orders.aggregate([
  {
    $lookup: {
      from: "customers",
      localField: "customerId",
      foreignField: "_id",
      as: "customer"
    }
  },
  {
    $unwind: "$customer"
  },
  {
    $project: {
      orderId: "$_id",
      customerEmail: "$customer.email",
      customerName: {
        $concat: ["$customer.firstName", " ", "$customer.lastName"]
      },
      total: 1,
      status: 1
    }
  }
])

// $unwind - Deconstruct arrays
db.orders.aggregate([
  {
    $unwind: "$items"
  },
  {
    $group: {
      _id: "$items.sku",
      totalQuantity: { $sum: "$items.quantity" },
      totalRevenue: { $sum: { $multiply: ["$items.quantity", "$items.price"] } }
    }
  },
  {
    $sort: { totalRevenue: -1 }
  }
])

// $addFields - Add computed fields
db.orders.aggregate([
  {
    $addFields: {
      itemCount: { $size: "$items" },
      orderYear: { $year: "$orderDate" },
      orderMonth: { $month: "$orderDate" }
    }
  }
])

// $bucket - Group by ranges
db.products.aggregate([
  {
    $bucket: {
      groupBy: "$price",
      boundaries: [0, 50, 100, 500, 1000, 5000],
      default: "Other",
      output: {
        count: { $sum: 1 },
        products: { $push: "$name" }
      }
    }
  }
])

// $facet - Multiple pipelines
db.orders.aggregate([
  {
    $facet: {
      byStatus: [
        { $group: { _id: "$status", count: { $sum: 1 } } }
      ],
      byMonth: [
        {
          $group: {
            _id: { $month: "$orderDate" },
            revenue: { $sum: "$total" }
          }
        },
        { $sort: { _id: 1 } }
      ],
      topCustomers: [
        {
          $group: {
            _id: "$customerId",
            totalSpent: { $sum: "$total" }
          }
        },
        { $sort: { totalSpent: -1 } },
        { $limit: 10 }
      ]
    }
  }
])
```

### 5.3 Aggregation Operators

```javascript
// String operators
db.customers.aggregate([
  {
    $project: {
      fullName: {
        $concat: ["$firstName", " ", "$lastName"]
      },
      emailDomain: {
        $arrayElemAt: [
          { $split: ["$email", "@"] },
          1
        ]
      },
      upperName: { $toUpper: "$firstName" }
    }
  }
])

// Array operators
db.customers.aggregate([
  {
    $project: {
      email: 1,
      tagCount: { $size: { $ifNull: ["$tags", []] } },
      firstTag: { $arrayElemAt: ["$tags", 0] },
      hasPremiumTag: { $in: ["premium", { $ifNull: ["$tags", []] }] }
    }
  }
])

// Date operators
db.orders.aggregate([
  {
    $project: {
      orderId: "$_id",
      year: { $year: "$orderDate" },
      month: { $month: "$orderDate" },
      dayOfWeek: { $dayOfWeek: "$orderDate" },
      daysSinceOrder: {
        $divide: [
          { $subtract: [new Date(), "$orderDate"] },
          1000 * 60 * 60 * 24
        ]
      }
    }
  }
])

// Conditional operators
db.customers.aggregate([
  {
    $project: {
      email: 1,
      loyaltyPoints: 1,
      segment: {
        $switch: {
          branches: [
            { case: { $gte: ["$loyaltyPoints", 1000] }, then: "VIP" },
            { case: { $gte: ["$loyaltyPoints", 500] }, then: "Premium" },
            { case: { $gte: ["$loyaltyPoints", 100] }, then: "Standard" }
          ],
          default: "Basic"
        }
      },
      discount: {
        $cond: {
          if: { $gte: ["$loyaltyPoints", 500] },
          then: 0.15,
          else: 0.05
        }
      }
    }
  }
])
```

### 5.4 Window Functions (MongoDB 5.0+)

```javascript
// Running totals
db.orders.aggregate([
  {
    $match: { customerId: ObjectId("...") }
  },
  {
    $setWindowFields: {
      partitionBy: "$customerId",
      sortBy: { orderDate: 1 },
      output: {
        runningTotal: {
          $sum: "$total",
          window: {
            documents: ["unbounded", "current"]
          }
        }
      }
    }
  }
])

// Moving average
db.dailySales.aggregate([
  {
    $setWindowFields: {
      sortBy: { date: 1 },
      output: {
        movingAvg7Day: {
          $avg: "$revenue",
          window: {
            documents: [-6, 0]
          }
        }
      }
    }
  }
])

// Rank
db.products.aggregate([
  {
    $setWindowFields: {
      partitionBy: "$category",
      sortBy: { price: -1 },
      output: {
        priceRank: {
          $rank: {}
        }
      }
    }
  }
])
```

**Exercise 5.1:** Complex aggregation pipeline
- Calculate customer lifetime value
- Segment customers by purchase behavior
- Find trending products
- Monthly revenue with growth rate

<details>
<summary>Solution</summary>

```javascript
// Customer Lifetime Value Analysis
db.customers.aggregate([
  // Join with orders
  {
    $lookup: {
      from: "orders",
      localField: "_id",
      foreignField: "customerId",
      as: "orders"
    }
  },
  // Calculate metrics
  {
    $addFields: {
      completedOrders: {
        $filter: {
          input: "$orders",
          as: "order",
          cond: { $eq: ["$$order.status", "completed"] }
        }
      }
    }
  },
  {
    $project: {
      email: 1,
      firstName: 1,
      lastName: 1,
      registrationDate: "$createdAt",
      totalOrders: { $size: "$completedOrders" },
      lifetimeValue: { $sum: "$completedOrders.total" },
      averageOrderValue: { $avg: "$completedOrders.total" },
      firstOrderDate: { $min: "$completedOrders.orderDate" },
      lastOrderDate: { $max: "$completedOrders.orderDate" },
      daysSinceLastOrder: {
        $divide: [
          { $subtract: [new Date(), { $max: "$completedOrders.orderDate" }] },
          1000 * 60 * 60 * 24
        ]
      }
    }
  },
  // Segment customers
  {
    $addFields: {
      segment: {
        $switch: {
          branches: [
            {
              case: {
                $and: [
                  { $gte: ["$lifetimeValue", 1000] },
                  { $lte: ["$daysSinceLastOrder", 30] }
                ]
              },
              then: "VIP Active"
            },
            {
              case: { $gte: ["$lifetimeValue", 500] },
              then: "Premium"
            },
            {
              case: { $lte: ["$daysSinceLastOrder", 90] },
              then: "Active"
            },
            {
              case: { $gt: ["$daysSinceLastOrder", 90] },
              then: "At Risk"
            }
          ],
          default: "New"
        }
      }
    }
  },
  { $sort: { lifetimeValue: -1 } }
])

// Trending Products Analysis
db.orders.aggregate([
  // Recent orders only
  {
    $match: {
      orderDate: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
      status: "completed"
    }
  },
  // Unwind items
  { $unwind: "$items" },
  // Join with products
  {
    $lookup: {
      from: "products",
      localField: "items.sku",
      foreignField: "_id",
      as: "product"
    }
  },
  { $unwind: "$product" },
  // Calculate trends by week
  {
    $group: {
      _id: {
        sku: "$items.sku",
        week: { $week: "$orderDate" }
      },
      productName: { $first: "$product.name" },
      category: { $first: "$product.category" },
      weeklyQuantity: { $sum: "$items.quantity" },
      weeklyRevenue: { $sum: { $multiply: ["$items.quantity", "$items.price"] } }
    }
  },
  // Sort and group by product
  { $sort: { "_id.sku": 1, "_id.week": 1 } },
  {
    $group: {
      _id: "$_id.sku",
      productName: { $first: "$productName" },
      category: { $first: "$category" },
      weeks: {
        $push: {
          week: "$_id.week",
          quantity: "$weeklyQuantity",
          revenue: "$weeklyRevenue"
        }
      }
    }
  },
  // Calculate trend
  {
    $addFields: {
      totalQuantity: { $sum: "$weeks.quantity" },
      totalRevenue: { $sum: "$weeks.revenue" },
      trend: {
        $cond: {
          if: { $gt: [{ $size: "$weeks" }, 1] },
          then: {
            $subtract: [
              { $arrayElemAt: ["$weeks.quantity", -1] },
              { $arrayElemAt: ["$weeks.quantity", 0] }
            ]
          },
          else: 0
        }
      }
    }
  },
  { $sort: { trend: -1 } },
  { $limit: 20 }
])

// Monthly Revenue with Growth Rate
db.orders.aggregate([
  {
    $match: {
      status: "completed",
      orderDate: { $gte: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000) }
    }
  },
  {
    $group: {
      _id: {
        year: { $year: "$orderDate" },
        month: { $month: "$orderDate" }
      },
      revenue: { $sum: "$total" },
      orderCount: { $sum: 1 },
      avgOrderValue: { $avg: "$total" }
    }
  },
  { $sort: { "_id.year": 1, "_id.month": 1 } },
  {
    $setWindowFields: {
      sortBy: { "_id.year": 1, "_id.month": 1 },
      output: {
        previousMonthRevenue: {
          $shift: {
            output: "$revenue",
            by: -1
          }
        }
      }
    }
  },
  {
    $addFields: {
      growthRate: {
        $multiply: [
          {
            $divide: [
              { $subtract: ["$revenue", "$previousMonthRevenue"] },
              "$previousMonthRevenue"
            ]
          },
          100
        ]
      }
    }
  },
  {
    $project: {
      month: {
        $concat: [
          { $toString: "$_id.year" },
          "-",
          {
            $cond: {
              if: { $lt: ["$_id.month", 10] },
              then: { $concat: ["0", { $toString: "$_id.month" }] },
              else: { $toString: "$_id.month" }
            }
          }
        ]
      },
      revenue: { $round: ["$revenue", 2] },
      orderCount: 1,
      avgOrderValue: { $round: ["$avgOrderValue", 2] },
      growthRate: { $round: ["$growthRate", 2] }
    }
  }
])
```
</details>

---

## 6. Indexing and Performance

**Time:** 60 minutes

### 6.1 Index Types

```javascript
// Single field index
db.customers.createIndex({ email: 1 }) // Ascending
db.orders.createIndex({ orderDate: -1 }) // Descending

// Unique index
db.customers.createIndex(
  { email: 1 },
  { unique: true }
)

// Compound index
db.orders.createIndex({
  customerId: 1,
  orderDate: -1,
  status: 1
})

// Multikey index (for arrays)
db.customers.createIndex({ tags: 1 })

// Text index
db.products.createIndex({
  name: "text",
  description: "text"
}, {
  weights: {
    name: 10,
    description: 5
  }
})

// Geospatial index
db.stores.createIndex({ location: "2dsphere" })

// Partial index
db.orders.createIndex(
  { customerId: 1, orderDate: -1 },
  {
    partialFilterExpression: {
      status: { $in: ["pending", "processing"] }
    }
  }
)

// TTL index (auto-delete documents)
db.sessions.createIndex(
  { createdAt: 1 },
  { expireAfterSeconds: 3600 } // Delete after 1 hour
)

// Sparse index
db.customers.createIndex(
  { phone: 1 },
  { sparse: true }
)
```

### 6.2 Index Management

```javascript
// List all indexes
db.customers.getIndexes()

// Get index information
db.customers.stats().indexSizes

// Drop index
db.customers.dropIndex("email_1")

// Drop all indexes except _id
db.customers.dropIndexes()

// Rebuild indexes
db.customers.reIndex()

// Hide index (test before dropping)
db.customers.hideIndex("email_1")
db.customers.unhideIndex("email_1")
```

### 6.3 Query Optimization

```javascript
// Explain query execution
db.customers.find({ email: "john@example.com" }).explain("executionStats")

// Explain aggregation
db.orders.explain("executionStats").aggregate([
  { $match: { status: "completed" } },
  { $group: { _id: "$customerId", total: { $sum: "$total" } } }
])

// Covered query (index-only query)
db.customers.find(
  { email: "john@example.com" },
  { email: 1, _id: 0 }
)

// Index intersection
db.products.createIndex({ category: 1 })
db.products.createIndex({ price: 1 })
db.products.find({
  category: "Electronics",
  price: { $lt: 1000 }
}).explain("executionStats")

// Hint to force index usage
db.customers.find({ firstName: "John" }).hint({ email: 1 })
```

### 6.4 Performance Analysis

```javascript
// Enable profiling
db.setProfilingLevel(2) // Profile all operations
db.setProfilingLevel(1, { slowms: 100 }) // Profile slow operations

// View slow queries
db.system.profile.find({
  millis: { $gt: 100 }
}).sort({ ts: -1 }).limit(10)

// Collection statistics
db.customers.stats()

// Index usage statistics
db.customers.aggregate([
  { $indexStats: {} }
])

// Find unused indexes
db.customers.aggregate([
  { $indexStats: {} },
  {
    $match: {
      "accesses.ops": { $eq: 0 }
    }
  }
])
```

**Exercise 6.1:** Index optimization
- Analyze a slow query
- Create appropriate indexes
- Measure performance improvement
- Identify unused indexes

<details>
<summary>Solution</summary>

```javascript
// Step 1: Analyze slow query
const slowQuery = db.orders.find({
  status: "completed",
  orderDate: { $gte: new Date("2024-01-01") },
  total: { $gte: 100 }
}).sort({ orderDate: -1 })

// Explain before optimization
const beforeStats = slowQuery.explain("executionStats")
print("Execution time before:", beforeStats.executionStats.executionTimeMillis, "ms")
print("Documents examined:", beforeStats.executionStats.totalDocsExamined)
print("Documents returned:", beforeStats.executionStats.nReturned)

// Step 2: Create optimized indexes
// Compound index for the query
db.orders.createIndex({
  status: 1,
  orderDate: -1,
  total: 1
})

// Alternative: Partial index for completed orders only
db.orders.createIndex(
  { orderDate: -1, total: 1 },
  {
    partialFilterExpression: { status: "completed" },
    name: "completed_orders_idx"
  }
)

// Step 3: Measure improvement
const afterStats = slowQuery.explain("executionStats")
print("Execution time after:", afterStats.executionStats.executionTimeMillis, "ms")
print("Documents examined:", afterStats.executionStats.totalDocsExamined)
print("Documents returned:", afterStats.executionStats.nReturned)

const improvement = (
  (beforeStats.executionStats.executionTimeMillis -
   afterStats.executionStats.executionTimeMillis) /
  beforeStats.executionStats.executionTimeMillis * 100
).toFixed(2)
print("Performance improvement:", improvement + "%")

// Step 4: Find unused indexes
const indexStats = db.orders.aggregate([
  { $indexStats: {} }
]).toArray()

print("\nIndex Usage Statistics:")
indexStats.forEach(idx => {
  print(`Index: ${idx.name}`)
  print(`  Operations: ${idx.accesses.ops}`)
  print(`  Since: ${idx.accesses.since}`)
  if (idx.accesses.ops === 0) {
    print("  WARNING: Unused index - consider dropping")
  }
  print("")
})

// Drop unused indexes
indexStats.forEach(idx => {
  if (idx.name !== "_id_" && idx.accesses.ops === 0) {
    print(`Dropping unused index: ${idx.name}`)
    db.orders.dropIndex(idx.name)
  }
})

// Step 5: Monitor index sizes
const stats = db.orders.stats()
print("\nCollection Statistics:")
print(`Total documents: ${stats.count}`)
print(`Data size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`)
print(`Index size: ${(stats.totalIndexSize / 1024 / 1024).toFixed(2)} MB`)
print(`Indexes:`)
Object.entries(stats.indexSizes).forEach(([name, size]) => {
  print(`  ${name}: ${(size / 1024 / 1024).toFixed(2)} MB`)
})
```
</details>

---

## 7. Data Modeling Patterns

**Time:** 60 minutes

### 7.1 Embedded vs Referenced

```javascript
// EMBEDDED: One-to-Few
// Good for: Data accessed together, limited array size
db.users.insertOne({
  _id: ObjectId("..."),
  name: "John Doe",
  email: "john@example.com",
  addresses: [
    {
      type: "home",
      street: "123 Main St",
      city: "New York",
      zip: "10001"
    },
    {
      type: "work",
      street: "456 Office Blvd",
      city: "New York",
      zip: "10002"
    }
  ]
})

// REFERENCED: One-to-Many
// Good for: Large datasets, data accessed independently
// Customers collection
db.customers.insertOne({
  _id: ObjectId("customer1"),
  name: "John Doe",
  email: "john@example.com"
})

// Orders collection (references customer)
db.orders.insertMany([
  {
    _id: ObjectId("order1"),
    customerId: ObjectId("customer1"),
    total: 99.99,
    orderDate: new Date()
  },
  {
    _id: ObjectId("order2"),
    customerId: ObjectId("customer1"),
    total: 149.99,
    orderDate: new Date()
  }
])
```

### 7.2 Extended Reference Pattern

```javascript
// Store frequently accessed data with reference
db.orders.insertOne({
  _id: ObjectId("..."),
  customerId: ObjectId("customer1"),
  // Denormalized customer data for quick access
  customerInfo: {
    name: "John Doe",
    email: "john@example.com"
  },
  items: [...],
  total: 99.99
})
```

### 7.3 Subset Pattern

```javascript
// Store most recent/relevant items embedded
db.products.insertOne({
  _id: ObjectId("product1"),
  name: "Laptop",
  price: 999.99,
  // Only recent reviews embedded
  recentReviews: [
    {
      userId: ObjectId("user1"),
      rating: 5,
      comment: "Great product!",
      date: new Date()
    }
    // ... last 10 reviews
  ],
  reviewCount: 1547,
  avgRating: 4.7
})

// All reviews in separate collection
db.reviews.insertMany([
  {
    _id: ObjectId("..."),
    productId: ObjectId("product1"),
    userId: ObjectId("user1"),
    rating: 5,
    comment: "Great product!",
    date: new Date()
  }
  // ... all 1547 reviews
])
```

### 7.4 Bucket Pattern

```javascript
// Group time-series data into buckets
db.sensorData.insertOne({
  _id: ObjectId("..."),
  sensorId: "sensor1",
  date: new Date("2024-01-01"),
  readings: [
    { time: new Date("2024-01-01T00:00:00Z"), temperature: 22.5, humidity: 60 },
    { time: new Date("2024-01-01T00:01:00Z"), temperature: 22.6, humidity: 59 },
    // ... readings for entire day
  ],
  readingCount: 1440,
  avgTemperature: 22.8,
  avgHumidity: 58
})
```

### 7.5 Schema Versioning

```javascript
// Include schema version for migrations
db.customers.insertOne({
  _id: ObjectId("..."),
  schemaVersion: 2,
  email: "john@example.com",
  profile: {
    firstName: "John",
    lastName: "Doe"
  },
  preferences: {
    newsletter: true,
    sms: false
  }
})

// Migration script
db.customers.updateMany(
  { schemaVersion: { $exists: false } },
  [
    {
      $set: {
        schemaVersion: 2,
        profile: {
          firstName: "$firstName",
          lastName: "$lastName"
        }
      }
    },
    {
      $unset: ["firstName", "lastName"]
    }
  ]
)
```

**Exercise 7.1:** Design a data model
- Blog platform with users, posts, comments
- E-commerce with products, reviews, orders
- Social media with posts, likes, follows
- Choose appropriate patterns for each

<details>
<summary>Solution</summary>

```javascript
// Blog Platform Data Model

// Users collection (reference)
db.users.insertOne({
  _id: ObjectId("user1"),
  username: "johndoe",
  email: "john@example.com",
  passwordHash: "...",
  profile: {
    bio: "Software developer",
    avatar: "https://...",
    website: "https://johndoe.com"
  },
  stats: {
    postCount: 42,
    followerCount: 150,
    followingCount: 89
  },
  createdAt: new Date()
})

// Posts collection (embedded comments, referenced user)
db.posts.insertOne({
  _id: ObjectId("post1"),
  authorId: ObjectId("user1"),
  // Extended reference pattern
  authorInfo: {
    username: "johndoe",
    avatar: "https://..."
  },
  title: "Getting Started with MongoDB",
  content: "...",
  slug: "getting-started-with-mongodb",
  tags: ["mongodb", "database", "tutorial"],
  // Recent comments embedded (subset pattern)
  recentComments: [
    {
      _id: ObjectId("comment1"),
      userId: ObjectId("user2"),
      username: "janedoe",
      content: "Great post!",
      createdAt: new Date()
    }
    // ... last 5 comments
  ],
  stats: {
    viewCount: 1547,
    likeCount: 89,
    commentCount: 23
  },
  publishedAt: new Date(),
  updatedAt: new Date()
})

// All comments in separate collection
db.comments.insertOne({
  _id: ObjectId("comment1"),
  postId: ObjectId("post1"),
  userId: ObjectId("user2"),
  content: "Great post!",
  likes: 5,
  createdAt: new Date()
})

// E-commerce Data Model

// Products collection
db.products.insertOne({
  _id: "PROD-001",
  name: "Wireless Mouse",
  description: "...",
  category: "Electronics",
  price: 29.99,
  inventory: {
    stock: 150,
    reserved: 10,
    available: 140
  },
  // Recent reviews (subset pattern)
  recentReviews: [
    {
      userId: ObjectId("user1"),
      username: "johndoe",
      rating: 5,
      comment: "Perfect mouse!",
      date: new Date()
    }
  ],
  stats: {
    reviewCount: 234,
    avgRating: 4.7,
    soldCount: 1547
  },
  createdAt: new Date()
})

// Orders collection (embedded items)
db.orders.insertOne({
  _id: ObjectId("order1"),
  customerId: ObjectId("user1"),
  // Extended reference
  customerInfo: {
    name: "John Doe",
    email: "john@example.com"
  },
  items: [
    {
      productId: "PROD-001",
      name: "Wireless Mouse",
      quantity: 2,
      price: 29.99,
      subtotal: 59.98
    }
  ],
  shipping: {
    address: {
      street: "123 Main St",
      city: "New York",
      state: "NY",
      zip: "10001"
    },
    method: "standard",
    cost: 5.99
  },
  payment: {
    method: "credit_card",
    last4: "1234",
    transactionId: "txn_..."
  },
  totals: {
    subtotal: 59.98,
    shipping: 5.99,
    tax: 5.50,
    total: 71.47
  },
  status: "shipped",
  statusHistory: [
    { status: "pending", date: new Date("2024-01-01T10:00:00Z") },
    { status: "processing", date: new Date("2024-01-01T11:00:00Z") },
    { status: "shipped", date: new Date("2024-01-02T09:00:00Z") }
  ],
  createdAt: new Date()
})

// Social Media Data Model

// Users collection
db.users.insertOne({
  _id: ObjectId("user1"),
  username: "johndoe",
  email: "john@example.com",
  profile: {
    displayName: "John Doe",
    bio: "Developer",
    avatar: "https://...",
    coverPhoto: "https://..."
  },
  stats: {
    postCount: 342,
    followerCount: 1547,
    followingCount: 423
  }
})

// Posts collection (embedded interactions)
db.posts.insertOne({
  _id: ObjectId("post1"),
  userId: ObjectId("user1"),
  userInfo: {
    username: "johndoe",
    avatar: "https://..."
  },
  content: "Just deployed my first MongoDB app!",
  media: [
    {
      type: "image",
      url: "https://...",
      thumbnail: "https://..."
    }
  ],
  // Embedded likes (subset pattern - recent only)
  recentLikes: [
    { userId: ObjectId("user2"), username: "janedoe", date: new Date() }
  ],
  stats: {
    likeCount: 89,
    commentCount: 12,
    shareCount: 5
  },
  createdAt: new Date()
})

// Follows collection (many-to-many)
db.follows.insertOne({
  _id: ObjectId("..."),
  followerId: ObjectId("user1"),
  followingId: ObjectId("user2"),
  createdAt: new Date()
})

// Create compound indexes for efficient queries
db.follows.createIndex({ followerId: 1, followingId: 1 }, { unique: true })
db.follows.createIndex({ followingId: 1, createdAt: -1 })
db.posts.createIndex({ userId: 1, createdAt: -1 })
db.comments.createIndex({ postId: 1, createdAt: -1 })
```
</details>

---

## 8. Transactions and Atomicity

**Time:** 45 minutes

### 8.1 Single Document Atomicity

```javascript
// Atomic update operators
db.accounts.updateOne(
  { accountId: "A123" },
  {
    $inc: { balance: -100 },
    $push: {
      transactions: {
        amount: -100,
        type: "withdrawal",
        date: new Date()
      }
    }
  }
)

// findAndModify for atomic read-modify-write
db.counters.findAndModify({
  query: { _id: "orderNumber" },
  update: { $inc: { sequence: 1 } },
  new: true
})
```

### 8.2 Multi-Document Transactions

```javascript
// Start a session
const session = db.getMongo().startSession()

try {
  session.startTransaction()

  // Transfer money between accounts
  db.accounts.updateOne(
    { accountId: "A123" },
    { $inc: { balance: -100 } },
    { session }
  )

  db.accounts.updateOne(
    { accountId: "B456" },
    { $inc: { balance: 100 } },
    { session }
  )

  // Record transaction
  db.transactions.insertOne({
    from: "A123",
    to: "B456",
    amount: 100,
    date: new Date()
  }, { session })

  // Commit transaction
  session.commitTransaction()
  print("Transaction successful")
} catch (error) {
  // Rollback on error
  session.abortTransaction()
  print("Transaction failed:", error)
} finally {
  session.endSession()
}
```

### 8.3 Optimistic Concurrency Control

```javascript
// Version-based optimistic locking
function updateWithVersionCheck(documentId, updates) {
  const doc = db.products.findOne({ _id: documentId })

  const result = db.products.updateOne(
    {
      _id: documentId,
      version: doc.version
    },
    {
      $set: updates,
      $inc: { version: 1 }
    }
  )

  if (result.matchedCount === 0) {
    throw new Error("Document was modified by another process")
  }

  return result
}

// Usage
try {
  updateWithVersionCheck("PROD-001", {
    stock: 45,
    updatedAt: new Date()
  })
} catch (error) {
  print("Update failed:", error.message)
  // Retry logic here
}
```

**Exercise 8.1:** Implement order processing with transactions
- Decrease product inventory
- Create order record
- Update customer order history
- Handle insufficient stock scenario

<details>
<summary>Solution</summary>

```javascript
function processOrder(customerId, items) {
  const session = db.getMongo().startSession()

  try {
    session.startTransaction({
      readConcern: { level: "snapshot" },
      writeConcern: { w: "majority" },
      readPreference: "primary"
    })

    // Step 1: Validate and reserve inventory
    for (const item of items) {
      const product = db.products.findOne(
        { _id: item.sku },
        { session }
      )

      if (!product) {
        throw new Error(`Product ${item.sku} not found`)
      }

      if (product.inventory.available < item.quantity) {
        throw new Error(
          `Insufficient stock for ${product.name}. ` +
          `Available: ${product.inventory.available}, ` +
          `Requested: ${item.quantity}`
        )
      }

      // Decrease inventory atomically
      db.products.updateOne(
        { _id: item.sku },
        {
          $inc: {
            "inventory.available": -item.quantity,
            "inventory.reserved": item.quantity
          }
        },
        { session }
      )
    }

    // Step 2: Calculate order total
    const orderItems = items.map(item => {
      const product = db.products.findOne(
        { _id: item.sku },
        { session }
      )
      return {
        productId: item.sku,
        name: product.name,
        quantity: item.quantity,
        price: product.price,
        subtotal: item.quantity * product.price
      }
    })

    const subtotal = orderItems.reduce((sum, item) => sum + item.subtotal, 0)
    const tax = subtotal * 0.0875 // 8.75% tax
    const shipping = subtotal > 50 ? 0 : 9.99
    const total = subtotal + tax + shipping

    // Step 3: Create order
    const orderResult = db.orders.insertOne({
      customerId: ObjectId(customerId),
      items: orderItems,
      totals: {
        subtotal: subtotal,
        tax: tax,
        shipping: shipping,
        total: total
      },
      status: "pending",
      createdAt: new Date()
    }, { session })

    const orderId = orderResult.insertedId

    // Step 4: Update customer
    db.customers.updateOne(
      { _id: ObjectId(customerId) },
      {
        $inc: {
          "stats.orderCount": 1,
          "stats.totalSpent": total
        },
        $push: {
          recentOrders: {
            $each: [{
              orderId: orderId,
              total: total,
              date: new Date()
            }],
            $slice: -10 // Keep only last 10 orders
          }
        }
      },
      { session }
    )

    // Step 5: Commit transaction
    session.commitTransaction()

    print("Order processed successfully!")
    print("Order ID:", orderId)
    print("Total:", total)

    return {
      success: true,
      orderId: orderId,
      total: total
    }

  } catch (error) {
    print("Order processing failed:", error.message)
    session.abortTransaction()
    return {
      success: false,
      error: error.message
    }
  } finally {
    session.endSession()
  }
}

// Test the function
const result = processOrder("user1", [
  { sku: "PROD-001", quantity: 2 },
  { sku: "PROD-002", quantity: 1 }
])

printjson(result)
```
</details>

---

## 9. Backup and Restore

**Time:** 30 minutes

### 9.1 mongodump and mongorestore

```bash
# Backup entire database
docker exec my-mongodb mongodump \
  --username admin \
  --password secure_password \
  --authenticationDatabase admin \
  --db myapp \
  --out /backup

# Copy backup from container
docker cp my-mongodb:/backup ./mongodb-backup

# Backup specific collection
docker exec my-mongodb mongodump \
  --db myapp \
  --collection customers \
  --out /backup

# Backup with query filter
docker exec my-mongodb mongodump \
  --db myapp \
  --collection orders \
  --query '{"status": "completed"}' \
  --out /backup

# Restore database
docker cp ./mongodb-backup my-mongodb:/backup
docker exec my-mongodb mongorestore \
  --username admin \
  --password secure_password \
  --authenticationDatabase admin \
  --db myapp \
  /backup/myapp

# Restore to different database
docker exec my-mongodb mongorestore \
  --db myapp_restore \
  /backup/myapp

# Restore with drop existing
docker exec my-mongodb mongorestore \
  --drop \
  --db myapp \
  /backup/myapp
```

### 9.2 Automated Backup Script

```bash
#!/bin/bash
# mongodb-backup.sh

CONTAINER="my-mongodb"
USERNAME="admin"
PASSWORD="secure_password"
BACKUP_DIR="/backups/mongodb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATABASES=("myapp" "analytics")

mkdir -p $BACKUP_DIR

for DB in "${DATABASES[@]}"; do
  echo "Backing up $DB..."

  docker exec $CONTAINER mongodump \
    --username $USERNAME \
    --password $PASSWORD \
    --authenticationDatabase admin \
    --db $DB \
    --out /tmp/backup_$TIMESTAMP

  # Copy from container
  docker cp $CONTAINER:/tmp/backup_$TIMESTAMP/$DB $BACKUP_DIR/${DB}_${TIMESTAMP}

  # Compress backup
  tar -czf $BACKUP_DIR/${DB}_${TIMESTAMP}.tar.gz \
    -C $BACKUP_DIR ${DB}_${TIMESTAMP}

  # Remove uncompressed backup
  rm -rf $BACKUP_DIR/${DB}_${TIMESTAMP}

  # Clean up container
  docker exec $CONTAINER rm -rf /tmp/backup_$TIMESTAMP

  echo "Backup completed: ${DB}_${TIMESTAMP}.tar.gz"
done

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup process completed"
```

### 9.3 Point-in-Time Backup with Oplog

```bash
# Enable oplog
# Add to mongod.conf:
# replication:
#   replSetName: "rs0"

# Backup with oplog
docker exec my-mongodb mongodump \
  --oplog \
  --out /backup

# Restore to specific point in time
docker exec my-mongodb mongorestore \
  --oplogReplay \
  --oplogLimit "1704067200:1" \
  /backup
```

**Exercise 9.1:** Create backup and restore strategy
- Implement automated daily backups
- Test restore process
- Implement retention policy
- Add monitoring and alerts

<details>
<summary>Solution</summary>

```bash
#!/bin/bash
# comprehensive-mongodb-backup.sh

set -e

# Configuration
CONTAINER="my-mongodb"
USERNAME="admin"
PASSWORD="secure_password"
BACKUP_ROOT="/backups/mongodb"
RETENTION_DAYS=30
LOG_FILE="/var/log/mongodb-backup.log"

# Slack webhook for notifications (optional)
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Function to send notification
notify() {
  local message="$1"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a $LOG_FILE

  if [ -n "$SLACK_WEBHOOK" ]; then
    curl -X POST -H 'Content-type: application/json' \
      --data "{\"text\":\"MongoDB Backup: $message\"}" \
      $SLACK_WEBHOOK
  fi
}

# Create backup directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
mkdir -p $BACKUP_DIR

notify "Starting backup process..."

# Get list of databases
DATABASES=$(docker exec $CONTAINER mongosh \
  --username $USERNAME \
  --password $PASSWORD \
  --authenticationDatabase admin \
  --quiet \
  --eval "db.adminCommand('listDatabases').databases.map(d => d.name).join(' ')")

# Backup each database
for DB in $DATABASES; do
  if [ "$DB" != "admin" ] && [ "$DB" != "local" ] && [ "$DB" != "config" ]; then
    notify "Backing up database: $DB"

    docker exec $CONTAINER mongodump \
      --username $USERNAME \
      --password $PASSWORD \
      --authenticationDatabase admin \
      --db $DB \
      --out /tmp/backup_$TIMESTAMP 2>> $LOG_FILE

    docker cp $CONTAINER:/tmp/backup_$TIMESTAMP/$DB $BACKUP_DIR/$DB

    # Get database size
    DB_SIZE=$(du -sh $BACKUP_DIR/$DB | cut -f1)
    notify "Completed backup of $DB (Size: $DB_SIZE)"
  fi
done

# Compress backup
cd $BACKUP_ROOT
tar -czf ${TIMESTAMP}.tar.gz $TIMESTAMP
rm -rf $TIMESTAMP

# Verify backup
if [ -f "${TIMESTAMP}.tar.gz" ]; then
  BACKUP_SIZE=$(du -sh ${TIMESTAMP}.tar.gz | cut -f1)
  notify "Backup compressed successfully (Size: $BACKUP_SIZE)"

  # Test backup integrity
  tar -tzf ${TIMESTAMP}.tar.gz > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    notify "Backup integrity verified"
  else
    notify "ERROR: Backup integrity check failed!"
    exit 1
  fi
else
  notify "ERROR: Backup file not found!"
  exit 1
fi

# Clean up old backups
notify "Cleaning up old backups..."
find $BACKUP_ROOT -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
REMAINING=$(find $BACKUP_ROOT -name "*.tar.gz" | wc -l)
notify "Retention policy applied. Remaining backups: $REMAINING"

# Clean up container
docker exec $CONTAINER rm -rf /tmp/backup_$TIMESTAMP

# Generate backup report
TOTAL_SIZE=$(du -sh $BACKUP_ROOT | cut -f1)
cat <<EOF | tee -a $LOG_FILE

=== Backup Report ===
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Backup Location: $BACKUP_ROOT/${TIMESTAMP}.tar.gz
Backup Size: $BACKUP_SIZE
Total Backup Storage: $TOTAL_SIZE
Retention Period: $RETENTION_DAYS days
Number of Backups: $REMAINING
=====================

EOF

notify "Backup process completed successfully"

# Add to crontab for daily execution:
# 0 2 * * * /path/to/comprehensive-mongodb-backup.sh
```

Test restore script:
```bash
#!/bin/bash
# test-restore.sh

BACKUP_FILE="$1"
TEST_CONTAINER="mongodb-test-restore"

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup-file.tar.gz>"
  exit 1
fi

echo "Starting test restore container..."
docker run -d --name $TEST_CONTAINER \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=test_password \
  mongo:7

sleep 10

echo "Extracting backup..."
tar -xzf $BACKUP_FILE -C /tmp

echo "Copying backup to container..."
docker cp /tmp/$(basename $BACKUP_FILE .tar.gz) $TEST_CONTAINER:/backup

echo "Restoring backup..."
docker exec $TEST_CONTAINER mongorestore \
  --username admin \
  --password test_password \
  --authenticationDatabase admin \
  /backup

echo "Verifying restore..."
docker exec $TEST_CONTAINER mongosh \
  --username admin \
  --password test_password \
  --authenticationDatabase admin \
  --eval "db.adminCommand('listDatabases')"

echo "Cleaning up..."
docker stop $TEST_CONTAINER
docker rm $TEST_CONTAINER
rm -rf /tmp/$(basename $BACKUP_FILE .tar.gz)

echo "Test restore completed successfully!"
```
</details>

---

## 10. Monitoring and Optimization

**Time:** 45 minutes

### 10.1 Server Status and Statistics

```javascript
// Server status
db.serverStatus()

// Database statistics
db.stats()

// Collection statistics
db.customers.stats()

// Current operations
db.currentOp()

// Kill long-running operation
db.killOp(operationId)

// Connection statistics
db.serverStatus().connections

// Memory usage
db.serverStatus().mem

// Network statistics
db.serverStatus().network
```

### 10.2 Query Performance Monitoring

```javascript
// Enable profiling
db.setProfilingLevel(2) // Profile all
db.setProfilingLevel(1, { slowms: 100 }) // Profile slow queries
db.setProfilingLevel(0) // Disable

// View slow queries
db.system.profile.find({
  millis: { $gt: 100 }
}).sort({ ts: -1 }).limit(10)

// Aggregated slow query analysis
db.system.profile.aggregate([
  {
    $match: { millis: { $gt: 100 } }
  },
  {
    $group: {
      _id: "$ns",
      count: { $sum: 1 },
      avgTime: { $avg: "$millis" },
      maxTime: { $max: "$millis" }
    }
  },
  {
    $sort: { avgTime: -1 }
  }
])

// Check index usage
db.customers.aggregate([{ $indexStats: {} }])

// Query plan cache
db.customers.getPlanCache().list()
db.customers.getPlanCache().clear()
```

### 10.3 Monitoring Dashboard Query

```javascript
// Comprehensive monitoring query
const monitoringReport = {
  timestamp: new Date(),
  server: db.serverStatus(),
  databases: db.adminCommand({ listDatabases: 1 }),
  replication: db.adminCommand({ replSetGetStatus: 1 }),
  currentOps: db.currentOp(),
  slowQueries: db.system.profile.find({ millis: { $gt: 100 } }).toArray()
}

// Calculate metrics
const metrics = {
  connections: {
    current: db.serverStatus().connections.current,
    available: db.serverStatus().connections.available,
    percentage: (
      db.serverStatus().connections.current /
      (db.serverStatus().connections.current + db.serverStatus().connections.available) *
      100
    ).toFixed(2)
  },
  memory: {
    resident: db.serverStatus().mem.resident,
    virtual: db.serverStatus().mem.virtual,
    mapped: db.serverStatus().mem.mapped
  },
  operations: {
    insert: db.serverStatus().opcounters.insert,
    query: db.serverStatus().opcounters.query,
    update: db.serverStatus().opcounters.update,
    delete: db.serverStatus().opcounters.delete
  }
}

printjson(metrics)
```

### 10.4 Performance Optimization Tips

```javascript
// 1. Use covered queries
db.customers.createIndex({ email: 1, firstName: 1, lastName: 1 })
db.customers.find(
  { email: "john@example.com" },
  { email: 1, firstName: 1, lastName: 1, _id: 0 }
)

// 2. Limit fields returned
db.orders.find({}, { customerId: 1, total: 1, status: 1 })

// 3. Use aggregation pipeline for complex queries
// Instead of loading all data into memory
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $group: { _id: "$customerId", total: { $sum: "$total" } } },
  { $sort: { total: -1 } },
  { $limit: 10 }
])

// 4. Batch operations
const bulk = db.customers.initializeUnorderedBulkOp()
for (let i = 0; i < 1000; i++) {
  bulk.insert({ email: `user${i}@example.com`, createdAt: new Date() })
}
bulk.execute()

// 5. Use appropriate index types
db.products.createIndex({ name: "text" }) // For text search
db.stores.createIndex({ location: "2dsphere" }) // For geo queries
db.logs.createIndex({ createdAt: 1 }, { expireAfterSeconds: 86400 }) // TTL index
```

**Exercise 10.1:** Create monitoring dashboard
- Real-time performance metrics
- Slow query analysis
- Index usage statistics
- Resource utilization

<details>
<summary>Solution</summary>

```javascript
// monitoring-dashboard.js

function generateMonitoringReport() {
  const report = {
    timestamp: new Date(),
    server: {},
    databases: {},
    performance: {},
    alerts: []
  }

  // Server Info
  const serverStatus = db.serverStatus()
  report.server = {
    version: serverStatus.version,
    uptime: serverStatus.uptime,
    host: serverStatus.host,
    process: serverStatus.process
  }

  // Connections
  report.performance.connections = {
    current: serverStatus.connections.current,
    available: serverStatus.connections.available,
    totalCreated: serverStatus.connections.totalCreated,
    usagePercent: (
      serverStatus.connections.current /
      (serverStatus.connections.current + serverStatus.connections.available) *
      100
    ).toFixed(2)
  }

  // Alert if connections > 80%
  if (report.performance.connections.usagePercent > 80) {
    report.alerts.push({
      severity: "warning",
      message: "Connection usage above 80%",
      value: report.performance.connections.usagePercent + "%"
    })
  }

  // Memory
  report.performance.memory = {
    residentMB: serverStatus.mem.resident,
    virtualMB: serverStatus.mem.virtual
  }

  // Operations
  const opcounters = serverStatus.opcounters
  report.performance.operations = {
    insert: opcounters.insert,
    query: opcounters.query,
    update: opcounters.update,
    delete: opcounters.delete,
    getmore: opcounters.getmore,
    command: opcounters.command
  }

  // Network
  report.performance.network = {
    bytesInMB: (serverStatus.network.bytesIn / 1024 / 1024).toFixed(2),
    bytesOutMB: (serverStatus.network.bytesOut / 1024 / 1024).toFixed(2),
    requests: serverStatus.network.numRequests
  }

  // Database Statistics
  const dbList = db.adminCommand({ listDatabases: 1 })
  report.databases.list = dbList.databases.map(d => ({
    name: d.name,
    sizeMB: (d.sizeOnDisk / 1024 / 1024).toFixed(2)
  }))

  report.databases.totalSizeMB = (dbList.totalSize / 1024 / 1024).toFixed(2)

  // Collection Statistics for current database
  const collections = db.getCollectionNames()
  report.databases.currentDB = {
    name: db.getName(),
    collections: collections.map(coll => {
      const stats = db.getCollection(coll).stats()
      return {
        name: coll,
        count: stats.count,
        sizeMB: (stats.size / 1024 / 1024).toFixed(2),
        indexSizeMB: (stats.totalIndexSize / 1024 / 1024).toFixed(2)
      }
    })
  }

  // Slow Queries (if profiling enabled)
  try {
    const slowQueries = db.system.profile.aggregate([
      {
        $match: {
          millis: { $gt: 100 },
          ts: { $gte: new Date(Date.now() - 3600000) } // Last hour
        }
      },
      {
        $group: {
          _id: "$ns",
          count: { $sum: 1 },
          avgMillis: { $avg: "$millis" },
          maxMillis: { $max: "$millis" }
        }
      },
      { $sort: { avgMillis: -1 } },
      { $limit: 10 }
    ]).toArray()

    report.performance.slowQueries = slowQueries

    if (slowQueries.length > 0) {
      report.alerts.push({
        severity: "warning",
        message: "Slow queries detected in last hour",
        count: slowQueries.reduce((sum, q) => sum + q.count, 0)
      })
    }
  } catch (e) {
    report.performance.slowQueries = "Profiling not enabled"
  }

  // Index Usage
  const indexUsage = collections.map(coll => {
    const indexes = db.getCollection(coll).aggregate([
      { $indexStats: {} }
    ]).toArray()

    const unused = indexes.filter(idx => idx.accesses.ops === 0)

    return {
      collection: coll,
      totalIndexes: indexes.length,
      unusedIndexes: unused.length,
      unused: unused.map(idx => idx.name)
    }
  })

  report.performance.indexUsage = indexUsage

  // Alert if unused indexes found
  const totalUnused = indexUsage.reduce((sum, coll) => sum + coll.unusedIndexes, 0)
  if (totalUnused > 0) {
    report.alerts.push({
      severity: "info",
      message: "Unused indexes detected",
      count: totalUnused
    })
  }

  // Current Operations
  const currentOps = db.currentOp()
  const activeOps = currentOps.inprog.filter(op => op.active && op.secs_running > 10)

  if (activeOps.length > 0) {
    report.performance.longRunningOps = activeOps.map(op => ({
      opid: op.opid,
      op: op.op,
      ns: op.ns,
      secsRunning: op.secs_running
    }))

    report.alerts.push({
      severity: "warning",
      message: "Long-running operations detected",
      count: activeOps.length
    })
  }

  // Replication Status (if replica set)
  try {
    const replStatus = db.adminCommand({ replSetGetStatus: 1 })
    report.replication = {
      set: replStatus.set,
      myState: replStatus.myState,
      members: replStatus.members.map(m => ({
        name: m.name,
        state: m.stateStr,
        health: m.health,
        lag: m.optimeDate ? (Date.now() - m.optimeDate.getTime()) / 1000 : null
      }))
    }
  } catch (e) {
    report.replication = "Not configured"
  }

  return report
}

// Generate and print report
const report = generateMonitoringReport()

print("\n=== MongoDB Monitoring Dashboard ===\n")
print(`Timestamp: ${report.timestamp}\n`)

print(`--- Server Info ---`)
print(`Version: ${report.server.version}`)
print(`Uptime: ${(report.server.uptime / 3600).toFixed(2)} hours`)
print(`Host: ${report.server.host}\n`)

print(`--- Performance Metrics ---`)
print(`Connections: ${report.performance.connections.current} / ${report.performance.connections.current + report.performance.connections.available} (${report.performance.connections.usagePercent}%)`)
print(`Memory: ${report.performance.memory.residentMB} MB resident, ${report.performance.memory.virtualMB} MB virtual`)
print(`Operations: Query=${report.performance.operations.query}, Insert=${report.performance.operations.insert}, Update=${report.performance.operations.update}`)
print(`Network: ${report.performance.network.bytesInMB} MB in, ${report.performance.network.bytesOutMB} MB out\n`)

print(`--- Database Statistics ---`)
print(`Total Size: ${report.databases.totalSizeMB} MB`)
report.databases.list.forEach(db => {
  print(`  ${db.name}: ${db.sizeMB} MB`)
})

if (report.alerts.length > 0) {
  print(`\n--- Alerts ---`)
  report.alerts.forEach(alert => {
    print(`[${alert.severity.toUpperCase()}] ${alert.message}`)
  })
}

print("\n===================================\n")

// Export full report
printjson(report)
```

Schedule this script to run periodically:
```bash
# Add to crontab to run every 5 minutes
*/5 * * * * docker exec my-mongodb mongosh --eval "load('/scripts/monitoring-dashboard.js')" >> /var/log/mongodb-monitoring.log 2>&1
```
</details>

---

## 11. Replica Sets Basics

**Time:** 45 minutes

### 11.1 Initialize Replica Set

```bash
# Start MongoDB instances
docker network create mongo-cluster

docker run -d --name mongo1 --network mongo-cluster \
  -p 27017:27017 mongo:7 --replSet rs0

docker run -d --name mongo2 --network mongo-cluster \
  -p 27018:27017 mongo:7 --replSet rs0

docker run -d --name mongo3 --network mongo-cluster \
  -p 27019:27017 mongo:7 --replSet rs0

# Initialize replica set
docker exec -it mongo1 mongosh --eval '
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017" },
    { _id: 1, host: "mongo2:27017" },
    { _id: 2, host: "mongo3:27017" }
  ]
})
'
```

### 11.2 Replica Set Operations

```javascript
// Check replica set status
rs.status()

// Check replica set configuration
rs.conf()

// Add member to replica set
rs.add("mongo4:27017")

// Remove member
rs.remove("mongo4:27017")

// Step down primary (for maintenance)
rs.stepDown(60) // Step down for 60 seconds

// Check replication lag
rs.printReplicationInfo()
rs.printSecondaryReplicationInfo()

// Read preference
db.getMongo().setReadPref("primaryPreferred")
db.getMongo().setReadPref("secondary")
```

### 11.3 Write Concerns and Read Concerns

```javascript
// Write concern - majority
db.customers.insertOne(
  { email: "john@example.com", name: "John Doe" },
  { writeConcern: { w: "majority", wtimeout: 5000 } }
)

// Read concern - majority
db.customers.find({ email: "john@example.com" })
  .readConcern("majority")

// Causal consistency
const session = db.getMongo().startSession({ causalConsistency: true })
const sessionDb = session.getDatabase("myapp")

sessionDb.customers.insertOne({ email: "test@example.com" })
sessionDb.customers.findOne({ email: "test@example.com" })

session.endSession()
```

**Exercise 11.1:** Set up and test replica set
- Initialize 3-node replica set
- Test failover scenario
- Configure read preferences
- Monitor replication lag

<details>
<summary>Solution</summary>

```bash
#!/bin/bash
# setup-replica-set.sh

# Create network
docker network create mongo-cluster || true

# Start MongoDB instances
for i in 1 2 3; do
  docker run -d \
    --name mongo$i \
    --network mongo-cluster \
    -p $((27016 + i)):27017 \
    -v mongo${i}-data:/data/db \
    mongo:7 --replSet rs0
done

# Wait for containers to start
sleep 10

# Initialize replica set
docker exec -it mongo1 mongosh --eval '
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017", priority: 2 },
    { _id: 1, host: "mongo2:27017", priority: 1 },
    { _id: 2, host: "mongo3:27017", priority: 1 }
  ]
})
'

# Wait for replica set to initialize
sleep 10

# Check status
docker exec -it mongo1 mongosh --eval 'rs.status()'

echo "Replica set initialized successfully!"
```

Test failover:
```javascript
// test-failover.js

// Connect to primary
const primary = db.getMongo()

print("Initial replica set status:")
printjson(rs.status().members.map(m => ({
  name: m.name,
  state: m.stateStr,
  health: m.health
})))

// Insert test data
db.failoverTest.insertMany([
  { _id: 1, data: "Test 1", timestamp: new Date() },
  { _id: 2, data: "Test 2", timestamp: new Date() },
  { _id: 3, data: "Test 3", timestamp: new Date() }
], { writeConcern: { w: "majority" } })

print("Data inserted successfully")

// Get current primary
const primaryMember = rs.status().members.find(m => m.state === 1)
print(`Current primary: ${primaryMember.name}`)

print("\nSimulating primary failure...")
print("Stop the primary container manually:")
print(`docker stop ${primaryMember.name.split(':')[0]}`)
print("\nWaiting 30 seconds for election...")

// In another terminal, stop the primary:
// docker stop mongo1

// Wait for new primary election
sleep(30000)

print("\nChecking new replica set status:")
printjson(rs.status().members.map(m => ({
  name: m.name,
  state: m.stateStr,
  health: m.health
})))

// Verify data is still accessible
const count = db.failoverTest.countDocuments()
print(`\nData verification: ${count} documents found`)

if (count === 3) {
  print("✓ Failover successful! Data is accessible.")
} else {
  print("✗ Failover failed! Data mismatch.")
}

// Restart original primary
print("\nRestart original primary:")
print("docker start mongo1")
```

Monitor replication:
```javascript
// monitor-replication.js

function monitorReplication() {
  const status = rs.status()

  print("\n=== Replication Monitoring ===\n")
  print(`Set: ${status.set}`)
  print(`Date: ${status.date}\n`)

  print("Members:")
  status.members.forEach(member => {
    print(`\n  ${member.name}`)
    print(`    State: ${member.stateStr}`)
    print(`    Health: ${member.health === 1 ? "UP" : "DOWN"}`)
    print(`    Uptime: ${(member.uptime / 3600).toFixed(2)} hours`)

    if (member.optimeDate) {
      print(`    Last heartbeat: ${member.lastHeartbeat}`)
      const lag = (Date.now() - member.optimeDate.getTime()) / 1000
      print(`    Replication lag: ${lag.toFixed(2)} seconds`)

      if (lag > 10) {
        print(`    ⚠️  WARNING: High replication lag!`)
      }
    }

    if (member.state === 1) {
      print(`    *** PRIMARY ***`)
    }
  })

  // Replication info
  print("\n--- Replication Info ---")
  rs.printReplicationInfo()

  print("\n--- Secondary Replication Info ---")
  rs.printSecondaryReplicationInfo()

  print("\n============================\n")
}

// Run monitoring
while (true) {
  monitorReplication()
  sleep(30000) // Monitor every 30 seconds
}
```
</details>

---

## 12. Real-World Scenarios

**Time:** 60 minutes

### Scenario 1: E-commerce Analytics

```javascript
// Daily sales report
db.orders.aggregate([
  {
    $match: {
      status: "completed",
      orderDate: {
        $gte: new Date(new Date().setHours(0, 0, 0, 0)),
        $lt: new Date(new Date().setHours(23, 59, 59, 999))
      }
    }
  },
  {
    $facet: {
      overview: [
        {
          $group: {
            _id: null,
            totalOrders: { $sum: 1 },
            totalRevenue: { $sum: "$total" },
            avgOrderValue: { $avg: "$total" }
          }
        }
      ],
      byHour: [
        {
          $group: {
            _id: { $hour: "$orderDate" },
            orders: { $sum: 1 },
            revenue: { $sum: "$total" }
          }
        },
        { $sort: { _id: 1 } }
      ],
      topProducts: [
        { $unwind: "$items" },
        {
          $group: {
            _id: "$items.productId",
            quantity: { $sum: "$items.quantity" },
            revenue: { $sum: "$items.subtotal" }
          }
        },
        { $sort: { revenue: -1 } },
        { $limit: 10 }
      ]
    }
  }
])
```

### Scenario 2: User Segmentation

```javascript
// RFM (Recency, Frequency, Monetary) Analysis
db.customers.aggregate([
  {
    $lookup: {
      from: "orders",
      localField: "_id",
      foreignField: "customerId",
      as: "orders"
    }
  },
  {
    $addFields: {
      completedOrders: {
        $filter: {
          input: "$orders",
          as: "order",
          cond: { $eq: ["$$order.status", "completed"] }
        }
      }
    }
  },
  {
    $project: {
      email: 1,
      recency: {
        $divide: [
          { $subtract: [new Date(), { $max: "$completedOrders.orderDate" }] },
          1000 * 60 * 60 * 24
        ]
      },
      frequency: { $size: "$completedOrders" },
      monetary: { $sum: "$completedOrders.total" }
    }
  },
  {
    $addFields: {
      recencyScore: {
        $switch: {
          branches: [
            { case: { $lte: ["$recency", 30] }, then: 5 },
            { case: { $lte: ["$recency", 60] }, then: 4 },
            { case: { $lte: ["$recency", 90] }, then: 3 },
            { case: { $lte: ["$recency", 180] }, then: 2 }
          ],
          default: 1
        }
      },
      frequencyScore: {
        $switch: {
          branches: [
            { case: { $gte: ["$frequency", 10] }, then: 5 },
            { case: { $gte: ["$frequency", 5] }, then: 4 },
            { case: { $gte: ["$frequency", 3] }, then: 3 },
            { case: { $gte: ["$frequency", 1] }, then: 2 }
          ],
          default: 1
        }
      },
      monetaryScore: {
        $switch: {
          branches: [
            { case: { $gte: ["$monetary", 1000] }, then: 5 },
            { case: { $gte: ["$monetary", 500] }, then: 4 },
            { case: { $gte: ["$monetary", 250] }, then: 3 },
            { case: { $gte: ["$monetary", 100] }, then: 2 }
          ],
          default: 1
        }
      }
    }
  },
  {
    $addFields: {
      rfmScore: {
        $concat: [
          { $toString: "$recencyScore" },
          { $toString: "$frequencyScore" },
          { $toString: "$monetaryScore" }
        ]
      },
      segment: {
        $switch: {
          branches: [
            {
              case: {
                $and: [
                  { $gte: ["$recencyScore", 4] },
                  { $gte: ["$frequencyScore", 4] },
                  { $gte: ["$monetaryScore", 4] }
                ]
              },
              then: "Champions"
            },
            {
              case: {
                $and: [
                  { $gte: ["$recencyScore", 3] },
                  { $gte: ["$frequencyScore", 3] }
                ]
              },
              then: "Loyal Customers"
            },
            {
              case: { $lte: ["$recencyScore", 2] },
              then: "At Risk"
            }
          ],
          default: "Regular"
        }
      }
    }
  },
  {
    $group: {
      _id: "$segment",
      customers: { $sum: 1 },
      avgRecency: { $avg: "$recency" },
      avgFrequency: { $avg: "$frequency" },
      avgMonetary: { $avg: "$monetary" }
    }
  }
])
```

### Scenario 3: Real-Time Inventory Management

```javascript
// Check low stock and auto-reorder
db.products.aggregate([
  {
    $match: {
      "inventory.available": { $lt: "$inventory.reorderPoint" }
    }
  },
  {
    $lookup: {
      from: "suppliers",
      localField: "supplierId",
      foreignField: "_id",
      as: "supplier"
    }
  },
  { $unwind: "$supplier" },
  {
    $project: {
      _id: 1,
      name: 1,
      sku: 1,
      currentStock: "$inventory.available",
      reorderPoint: "$inventory.reorderPoint",
      reorderQuantity: "$inventory.reorderQuantity",
      supplierName: "$supplier.name",
      supplierEmail: "$supplier.email",
      estimatedCost: {
        $multiply: ["$inventory.reorderQuantity", "$supplierPrice"]
      }
    }
  },
  {
    $merge: {
      into: "purchaseOrders",
      whenMatched: "keepExisting",
      whenNotMatched: "insert"
    }
  }
])
```

### Scenario 4: Fraud Detection

```javascript
// Detect suspicious patterns
db.transactions.aggregate([
  {
    $match: {
      timestamp: { $gte: new Date(Date.now() - 24 * 60 * 60 * 1000) }
    }
  },
  {
    $group: {
      _id: {
        userId: "$userId",
        day: { $dateToString: { format: "%Y-%m-%d", date: "$timestamp" } }
      },
      transactionCount: { $sum: 1 },
      totalAmount: { $sum: "$amount" },
      uniqueLocations: { $addToSet: "$location" },
      transactions: { $push: "$$ROOT" }
    }
  },
  {
    $match: {
      $or: [
        { transactionCount: { $gt: 20 } },
        { totalAmount: { $gt: 10000 } },
        { $expr: { $gt: [{ $size: "$uniqueLocations" }, 5] } }
      ]
    }
  },
  {
    $lookup: {
      from: "users",
      localField: "_id.userId",
      foreignField: "_id",
      as: "user"
    }
  },
  { $unwind: "$user" },
  {
    $project: {
      userId: "$_id.userId",
      userEmail: "$user.email",
      date: "$_id.day",
      transactionCount: 1,
      totalAmount: 1,
      locationCount: { $size: "$uniqueLocations" },
      riskScore: {
        $add: [
          { $cond: [{ $gt: ["$transactionCount", 20] }, 30, 0] },
          { $cond: [{ $gt: ["$totalAmount", 10000] }, 40, 0] },
          { $cond: [{ $gt: [{ $size: "$uniqueLocations" }, 5] }, 30, 0] }
        ]
      }
    }
  },
  {
    $match: { riskScore: { $gte: 50 } }
  },
  {
    $sort: { riskScore: -1 }
  }
])
```

---

## 13. Troubleshooting

### Common Issues and Solutions

#### Issue 1: Slow Queries

**Symptoms:** Queries taking too long

**Diagnosis:**
```javascript
// Enable profiling
db.setProfilingLevel(1, { slowms: 100 })

// Check slow queries
db.system.profile.find().sort({ ts: -1 }).limit(10)
```

**Solutions:**
- Add appropriate indexes
- Reduce returned fields
- Use aggregation pipeline efficiently
- Consider data modeling changes

#### Issue 2: High Memory Usage

**Symptoms:** Server running out of memory

**Diagnosis:**
```javascript
db.serverStatus().mem
db.serverStatus().wiredTiger.cache
```

**Solutions:**
- Increase server memory
- Reduce cache size
- Optimize queries to use less memory
- Add indexes to reduce collection scans

#### Issue 3: Connection Timeout

**Symptoms:** "MongoNetworkError: connection timed out"

**Solutions:**
- Check network connectivity
- Verify MongoDB is running
- Check firewall rules
- Increase connection timeout

#### Issue 4: Document Too Large

**Symptoms:** "Document exceeds maximum size"

**Solutions:**
- Split document into multiple documents
- Use GridFS for large binary data
- Review data model

---

## Further Reading

### Official Documentation
- [MongoDB Manual](https://docs.mongodb.com/)
- [Aggregation Pipeline](https://docs.mongodb.com/manual/core/aggregation-pipeline/)
- [Data Modeling](https://docs.mongodb.com/manual/core/data-modeling-introduction/)

### Books
- "MongoDB: The Definitive Guide" by Shannon Bradshaw
- "MongoDB Applied Design Patterns" by Rick Copeland

### Tools
- MongoDB Compass - GUI tool
- MongoDB Atlas - Cloud database
- Studio 3T - IDE for MongoDB

### Community
- [MongoDB Community Forums](https://www.mongodb.com/community/forums/)
- [Stack Overflow MongoDB Tag](https://stackoverflow.com/questions/tagged/mongodb)

---

## Conclusion

You've completed the MongoDB Complete Guide! You should now be able to:

✅ Set up and manage MongoDB databases
✅ Perform complex CRUD operations
✅ Build advanced aggregation pipelines
✅ Optimize performance with indexing
✅ Design effective data models
✅ Implement backup and recovery strategies
✅ Monitor database health
✅ Work with replica sets

**Next Steps:**
1. Explore sharding for horizontal scaling
2. Learn about MongoDB Atlas cloud features
3. Study advanced aggregation operators
4. Practice with real-world projects

Happy coding! 🍃
