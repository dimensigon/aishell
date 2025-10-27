# MongoDB Integration Tests - Quick Start Guide

## 🚀 One-Line Test Execution

```bash
cd tests/integration/database && ./run-tests.sh start && ./run-tests.sh test
```

## 📋 Common Commands

### Start Everything
```bash
./run-tests.sh start
```

### Run Tests
```bash
./run-tests.sh test
```

### Stop Everything
```bash
./run-tests.sh cleanup
```

## 🎯 Test Coverage Summary

| Feature | Tests | Status |
|---------|-------|--------|
| Connection & Auth | 4 | ✅ |
| CRUD Operations | 20 | ✅ |
| Aggregation Pipeline | 7 | ✅ |
| Indexes | 6 | ✅ |
| Text Search | 4 | ✅ |
| Transactions | 2 | ✅ |
| Change Streams | 2 | ✅ |
| Bulk Operations | 2 | ✅ |
| GridFS | 3 | ✅ |
| Schema Validation | 1 | ✅ |
| Geospatial | 2 | ✅ |
| Time Series | 2 | ✅ |
| **Total** | **55+** | ✅ |

## 🔧 Test Features

### 1. Connection & Authentication
```typescript
✓ should successfully connect to MongoDB with credentials
✓ should list available databases
✓ should reject invalid credentials
✓ should list collections in database
```

### 2. CRUD Operations
```typescript
// insertOne
✓ should insert a single document
✓ should handle insertOne with custom _id

// insertMany
✓ should insert multiple documents
✓ should handle ordered insertMany with duplicate key error
✓ should handle unordered insertMany with partial success

// find
✓ should find all documents
✓ should find documents with filter
✓ should find with projection
✓ should find with sorting
✓ should find with limit and skip
✓ should find with complex query operators

// updateOne
✓ should update a single document
✓ should use $inc operator
✓ should use $push operator for arrays
✓ should upsert document when not found

// deleteOne
✓ should delete a single document
✓ should delete the first matching document
✓ should return 0 when no document matches
```

### 3. Aggregation Pipeline
```typescript
✓ should use $match stage
✓ should use $group stage
✓ should use $sort stage
✓ should use $project stage
✓ should use complex aggregation pipeline
✓ should use $lookup for joins
```

### 4. Indexes
```typescript
✓ should create a single field index
✓ should create a compound index
✓ should create a unique index
✓ should list all indexes
✓ should drop an index
✓ should create TTL index
```

### 5. Text Search
```typescript
✓ should perform text search
✓ should search with multiple terms
✓ should search with text score
✓ should search with phrase
```

### 6. Transactions (ACID)
```typescript
✓ should complete a successful transaction
✓ should rollback transaction on error
```

### 7. Change Streams
```typescript
✓ should watch collection changes
✓ should watch with pipeline filter
```

### 8. Bulk Operations
```typescript
✓ should perform ordered bulk write
✓ should perform unordered bulk write
```

### 9. GridFS File Storage
```typescript
✓ should upload file to GridFS
✓ should download file from GridFS
✓ should delete file from GridFS
```

### 10. Schema Validation
```typescript
✓ should create collection with JSON schema validation
```

### 11. Geospatial Queries
```typescript
✓ should find locations near a point
✓ should find locations within polygon
```

### 12. Time Series Collections
```typescript
✓ should create time series collection
✓ should perform aggregations on time series data
```

## 🐳 Docker Commands

```bash
# Start container
./run-tests.sh start

# Check status
./run-tests.sh status

# View logs
./run-tests.sh logs

# Open MongoDB shell
./run-tests.sh shell

# Stop container
./run-tests.sh stop

# Clean up everything
./run-tests.sh cleanup
```

## 📊 Test Execution Flow

```
1. beforeAll:  Connect to MongoDB
               ↓
2. beforeEach: Setup collections
               ↓
3. Test:       Execute test case
               ↓
4. afterEach:  Clean up collections
               ↓
5. afterAll:   Drop database & disconnect
```

## 🔍 Debugging

### Container won't start
```bash
# Check if port is in use
lsof -i :27017

# View logs
./run-tests.sh logs

# Clean restart
./run-tests.sh cleanup
./run-tests.sh start
```

### Tests fail
```bash
# Verify MongoDB is running
./run-tests.sh status

# Test connection manually
./run-tests.sh shell
> db.runCommand({ ping: 1 })

# Run single test
npm run test -- tests/integration/database/test-mongodb-integration.ts -t "insertOne"
```

## 🎨 Example Test Cases

### Simple CRUD
```typescript
const user = {
  name: 'John Doe',
  email: 'john@example.com',
  age: 30
};

const result = await usersCollection.insertOne(user);
expect(result.insertedId).toBeDefined();
```

### Aggregation
```typescript
const result = await ordersCollection.aggregate([
  { $match: { status: 'completed' } },
  { $group: { _id: '$customer', totalSpent: { $sum: '$amount' } } },
  { $sort: { totalSpent: -1 } }
]).toArray();
```

### Transactions
```typescript
const session = client.startSession();
await session.withTransaction(async () => {
  await collection1.updateOne({...}, {...}, { session });
  await collection2.updateOne({...}, {...}, { session });
});
await session.endSession();
```

## 📦 Dependencies

```json
{
  "mongodb": "^6.20.0"
}
```

## 🌐 Connection Details

```
URI:      mongodb://admin:MyMongoPass123@localhost:27017
Database: test_integration_db
Port:     27017
User:     admin
Password: MyMongoPass123
```

## 📈 Performance

- **Total Tests**: 55+
- **Execution Time**: ~30 seconds
- **Coverage**: 12 feature areas
- **Timeout**: 30 seconds per test

## 🏆 Best Practices

1. ✅ Always start container before tests
2. ✅ Use run-tests.sh for lifecycle management
3. ✅ Clean up after testing (./run-tests.sh cleanup)
4. ✅ Check status if tests fail
5. ✅ View logs for debugging

## 📚 Learn More

- Test File: `/tests/integration/database/test-mongodb-integration.ts`
- Full README: `/tests/integration/database/README.md`
- MongoDB Docs: https://www.mongodb.com/docs/
