/**
 * MongoDB Integration Tests
 * Comprehensive test suite for MongoDB operations using Docker test environment
 *
 * Prerequisites:
 * - MongoDB container running: docker run -d -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=MyMongoPass123 mongo:latest
 * - Connection: mongodb://admin:MyMongoPass123@localhost:27017
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { MongoClient, Db, Collection, ObjectId, GridFSBucket, ChangeStream } from 'mongodb';

// MongoDB connection configuration
const MONGO_URI = 'mongodb://admin:MyMongoPass123@localhost:27017';
const TEST_DB = 'test_integration_db';
const TIMEOUT = 30000;

describe('MongoDB Integration Tests', () => {
  let client: MongoClient;
  let db: Db;
  let usersCollection: Collection;
  let productsCollection: Collection;
  let ordersCollection: Collection;
  let locationsCollection: Collection;

  // ============================================================================
  // Setup and Teardown
  // ============================================================================

  beforeAll(async () => {
    try {
      // Connect to MongoDB
      client = new MongoClient(MONGO_URI, {
        serverSelectionTimeoutMS: 5000,
        connectTimeoutMS: 5000,
      });
      await client.connect();

      // Get database reference
      db = client.db(TEST_DB);

      console.log('✅ MongoDB connection established');
    } catch (error) {
      console.error('❌ MongoDB connection failed:', error);
      throw error;
    }
  }, TIMEOUT);

  afterAll(async () => {
    try {
      // Drop test database
      if (db) {
        await db.dropDatabase();
        console.log('🗑️  Test database dropped');
      }

      // Close connection
      if (client) {
        await client.close();
        console.log('✅ MongoDB connection closed');
      }
    } catch (error) {
      console.error('❌ Cleanup failed:', error);
    }
  }, TIMEOUT);

  beforeEach(async () => {
    // Get collection references
    usersCollection = db.collection('users');
    productsCollection = db.collection('products');
    ordersCollection = db.collection('orders');
    locationsCollection = db.collection('locations');
  });

  afterEach(async () => {
    // Clean up collections after each test
    try {
      const collections = await db.listCollections().toArray();
      for (const collection of collections) {
        await db.collection(collection.name).deleteMany({});
      }
    } catch (error) {
      console.warn('Warning: Collection cleanup failed:', error);
    }
  });

  // ============================================================================
  // 1. Connection and Authentication Tests
  // ============================================================================

  describe('Connection and Authentication', () => {
    it('should successfully connect to MongoDB with credentials', async () => {
      // Verify connection by running a simple command
      const result = await db.admin().ping();
      expect(result).toEqual({ ok: 1 });
    });

    it('should list available databases', async () => {
      const adminDb = client.db().admin();
      const databasesList = await adminDb.listDatabases();

      expect(databasesList.databases).toBeDefined();
      expect(Array.isArray(databasesList.databases)).toBe(true);
      expect(databasesList.databases.length).toBeGreaterThan(0);
    });

    it('should reject invalid credentials', async () => {
      const invalidClient = new MongoClient('mongodb://wrong:wrongpass@localhost:27017', {
        serverSelectionTimeoutMS: 2000,
      });

      await expect(invalidClient.connect()).rejects.toThrow();
      await invalidClient.close();
    });

    it('should list collections in database', async () => {
      // Create test collection
      await db.createCollection('test_collection');

      const collections = await db.listCollections().toArray();
      expect(collections).toBeDefined();
      expect(collections.some(c => c.name === 'test_collection')).toBe(true);

      // Cleanup
      await db.collection('test_collection').drop();
    });
  });

  // ============================================================================
  // 2. Document CRUD Operations
  // ============================================================================

  describe('Document CRUD Operations', () => {
    describe('insertOne', () => {
      it('should insert a single document', async () => {
        const user = {
          name: 'John Doe',
          email: 'john@example.com',
          age: 30,
          createdAt: new Date(),
        };

        const result = await usersCollection.insertOne(user);

        expect(result.acknowledged).toBe(true);
        expect(result.insertedId).toBeDefined();
        expect(result.insertedId).toBeInstanceOf(ObjectId);

        // Verify document was inserted
        const found = await usersCollection.findOne({ _id: result.insertedId });
        expect(found).toBeDefined();
        expect(found?.name).toBe('John Doe');
      });

      it('should handle insertOne with custom _id', async () => {
        const customId = new ObjectId();
        const user = {
          _id: customId,
          name: 'Jane Doe',
          email: 'jane@example.com',
        };

        const result = await usersCollection.insertOne(user);

        expect(result.insertedId.toString()).toBe(customId.toString());
      });
    });

    describe('insertMany', () => {
      it('should insert multiple documents', async () => {
        const users = [
          { name: 'User 1', email: 'user1@example.com', age: 25 },
          { name: 'User 2', email: 'user2@example.com', age: 30 },
          { name: 'User 3', email: 'user3@example.com', age: 35 },
        ];

        const result = await usersCollection.insertMany(users);

        expect(result.acknowledged).toBe(true);
        expect(result.insertedCount).toBe(3);
        expect(Object.keys(result.insertedIds).length).toBe(3);

        // Verify all documents were inserted
        const count = await usersCollection.countDocuments();
        expect(count).toBe(3);
      });

      it('should handle ordered insertMany with duplicate key error', async () => {
        const customId = new ObjectId();
        const users = [
          { _id: customId, name: 'User 1' },
          { _id: customId, name: 'User 2' }, // Duplicate _id
          { name: 'User 3' },
        ];

        await expect(
          usersCollection.insertMany(users, { ordered: true })
        ).rejects.toThrow();

        // Only first document should be inserted
        const count = await usersCollection.countDocuments();
        expect(count).toBe(1);
      });

      it('should handle unordered insertMany with partial success', async () => {
        const customId = new ObjectId();
        const users = [
          { _id: customId, name: 'User 1' },
          { _id: customId, name: 'User 2' }, // Duplicate _id
          { name: 'User 3' },
        ];

        try {
          await usersCollection.insertMany(users, { ordered: false });
        } catch (error) {
          // Expected to throw, but should insert non-duplicate documents
        }

        const count = await usersCollection.countDocuments();
        expect(count).toBe(2); // User 1 and User 3
      });
    });

    describe('find', () => {
      beforeEach(async () => {
        // Insert test data
        await usersCollection.insertMany([
          { name: 'Alice', age: 25, city: 'New York', active: true },
          { name: 'Bob', age: 30, city: 'Los Angeles', active: true },
          { name: 'Charlie', age: 35, city: 'New York', active: false },
          { name: 'Diana', age: 28, city: 'Chicago', active: true },
        ]);
      });

      it('should find all documents', async () => {
        const users = await usersCollection.find().toArray();
        expect(users.length).toBe(4);
      });

      it('should find documents with filter', async () => {
        const nyUsers = await usersCollection.find({ city: 'New York' }).toArray();
        expect(nyUsers.length).toBe(2);
        expect(nyUsers.every(u => u.city === 'New York')).toBe(true);
      });

      it('should find with projection', async () => {
        const users = await usersCollection
          .find({}, { projection: { name: 1, age: 1, _id: 0 } })
          .toArray();

        expect(users[0]).not.toHaveProperty('city');
        expect(users[0]).toHaveProperty('name');
        expect(users[0]).toHaveProperty('age');
      });

      it('should find with sorting', async () => {
        const users = await usersCollection
          .find()
          .sort({ age: -1 })
          .toArray();

        expect(users[0].age).toBe(35);
        expect(users[users.length - 1].age).toBe(25);
      });

      it('should find with limit and skip', async () => {
        const users = await usersCollection
          .find()
          .sort({ age: 1 })
          .skip(1)
          .limit(2)
          .toArray();

        expect(users.length).toBe(2);
        expect(users[0].age).toBe(28);
      });

      it('should find with complex query operators', async () => {
        const users = await usersCollection
          .find({
            age: { $gte: 28, $lte: 30 },
            active: true,
          })
          .toArray();

        expect(users.length).toBe(2);
        expect(users.every(u => u.age >= 28 && u.age <= 30)).toBe(true);
      });
    });

    describe('updateOne', () => {
      beforeEach(async () => {
        await usersCollection.insertOne({
          name: 'Test User',
          email: 'test@example.com',
          age: 25,
        });
      });

      it('should update a single document', async () => {
        const result = await usersCollection.updateOne(
          { name: 'Test User' },
          { $set: { age: 26 } }
        );

        expect(result.acknowledged).toBe(true);
        expect(result.modifiedCount).toBe(1);
        expect(result.matchedCount).toBe(1);

        const updated = await usersCollection.findOne({ name: 'Test User' });
        expect(updated?.age).toBe(26);
      });

      it('should use $inc operator', async () => {
        await usersCollection.updateOne(
          { name: 'Test User' },
          { $inc: { age: 5 } }
        );

        const updated = await usersCollection.findOne({ name: 'Test User' });
        expect(updated?.age).toBe(30);
      });

      it('should use $push operator for arrays', async () => {
        await usersCollection.updateOne(
          { name: 'Test User' },
          { $push: { tags: 'developer' } as any }
        );

        const updated = await usersCollection.findOne({ name: 'Test User' });
        expect(updated?.tags).toEqual(['developer']);
      });

      it('should upsert document when not found', async () => {
        const result = await usersCollection.updateOne(
          { name: 'New User' },
          { $set: { email: 'new@example.com', age: 20 } },
          { upsert: true }
        );

        expect(result.upsertedCount).toBe(1);
        expect(result.upsertedId).toBeDefined();

        const count = await usersCollection.countDocuments();
        expect(count).toBe(2);
      });
    });

    describe('deleteOne', () => {
      beforeEach(async () => {
        await usersCollection.insertMany([
          { name: 'User 1', status: 'active' },
          { name: 'User 2', status: 'inactive' },
          { name: 'User 3', status: 'active' },
        ]);
      });

      it('should delete a single document', async () => {
        const result = await usersCollection.deleteOne({ name: 'User 1' });

        expect(result.acknowledged).toBe(true);
        expect(result.deletedCount).toBe(1);

        const remaining = await usersCollection.countDocuments();
        expect(remaining).toBe(2);
      });

      it('should delete the first matching document', async () => {
        const result = await usersCollection.deleteOne({ status: 'active' });

        expect(result.deletedCount).toBe(1);

        const activeCount = await usersCollection.countDocuments({ status: 'active' });
        expect(activeCount).toBe(1); // One active document remains
      });

      it('should return 0 when no document matches', async () => {
        const result = await usersCollection.deleteOne({ name: 'Nonexistent' });
        expect(result.deletedCount).toBe(0);
      });
    });
  });

  // ============================================================================
  // 3. Aggregation Pipeline
  // ============================================================================

  describe('Aggregation Pipeline', () => {
    beforeEach(async () => {
      // Insert test data
      await ordersCollection.insertMany([
        { customer: 'Alice', product: 'Laptop', amount: 1200, status: 'completed', date: new Date('2024-01-15') },
        { customer: 'Bob', product: 'Mouse', amount: 25, status: 'completed', date: new Date('2024-01-20') },
        { customer: 'Alice', product: 'Keyboard', amount: 75, status: 'completed', date: new Date('2024-02-10') },
        { customer: 'Charlie', product: 'Monitor', amount: 300, status: 'pending', date: new Date('2024-02-15') },
        { customer: 'Bob', product: 'Laptop', amount: 1200, status: 'completed', date: new Date('2024-03-01') },
      ]);
    });

    it('should use $match stage', async () => {
      const result = await ordersCollection
        .aggregate([
          { $match: { status: 'completed' } },
        ])
        .toArray();

      expect(result.length).toBe(4);
      expect(result.every(order => order.status === 'completed')).toBe(true);
    });

    it('should use $group stage', async () => {
      const result = await ordersCollection
        .aggregate([
          {
            $group: {
              _id: '$customer',
              totalSpent: { $sum: '$amount' },
              orderCount: { $sum: 1 },
            },
          },
        ])
        .toArray();

      expect(result.length).toBe(3); // Alice, Bob, Charlie

      const alice = result.find(r => r._id === 'Alice');
      expect(alice?.totalSpent).toBe(1275);
      expect(alice?.orderCount).toBe(2);
    });

    it('should use $sort stage', async () => {
      const result = await ordersCollection
        .aggregate([
          { $sort: { amount: -1 } },
          { $limit: 2 },
        ])
        .toArray();

      expect(result[0].amount).toBe(1200);
      expect(result[1].amount).toBe(1200);
    });

    it('should use $project stage', async () => {
      const result = await ordersCollection
        .aggregate([
          {
            $project: {
              customer: 1,
              product: 1,
              amountInCents: { $multiply: ['$amount', 100] },
              _id: 0,
            },
          },
        ])
        .toArray();

      expect(result[0]).not.toHaveProperty('amount');
      expect(result[0]).toHaveProperty('amountInCents');
      expect(result[0].amountInCents).toBe(120000);
    });

    it('should use complex aggregation pipeline', async () => {
      const result = await ordersCollection
        .aggregate([
          { $match: { status: 'completed' } },
          {
            $group: {
              _id: '$customer',
              totalSpent: { $sum: '$amount' },
              avgOrderValue: { $avg: '$amount' },
              orders: { $push: '$product' },
            },
          },
          { $sort: { totalSpent: -1 } },
          {
            $project: {
              customer: '$_id',
              totalSpent: 1,
              avgOrderValue: { $round: ['$avgOrderValue', 2] },
              orderCount: { $size: '$orders' },
              _id: 0,
            },
          },
        ])
        .toArray();

      expect(result.length).toBe(2); // Only completed orders customers
      expect(result[0].customer).toBe('Alice'); // Highest total
      expect(result[0].orderCount).toBe(2);
    });

    it('should use $lookup for joins', async () => {
      // Create customers collection
      const customersCollection = db.collection('customers');
      const aliceId = new ObjectId();
      const bobId = new ObjectId();

      await customersCollection.insertMany([
        { _id: aliceId, name: 'Alice', email: 'alice@example.com' },
        { _id: bobId, name: 'Bob', email: 'bob@example.com' },
      ]);

      // Update orders to reference customers
      await ordersCollection.updateMany(
        { customer: 'Alice' },
        { $set: { customerId: aliceId } }
      );

      const result = await ordersCollection
        .aggregate([
          {
            $lookup: {
              from: 'customers',
              localField: 'customerId',
              foreignField: '_id',
              as: 'customerDetails',
            },
          },
          { $match: { customerId: aliceId } },
        ])
        .toArray();

      expect(result[0].customerDetails).toBeDefined();
      expect(result[0].customerDetails[0].email).toBe('alice@example.com');
    });
  });

  // ============================================================================
  // 4. Indexes
  // ============================================================================

  describe('Indexes', () => {
    it('should create a single field index', async () => {
      const result = await usersCollection.createIndex({ email: 1 });
      expect(result).toBeDefined();

      const indexes = await usersCollection.listIndexes().toArray();
      const emailIndex = indexes.find(idx => idx.name === 'email_1');
      expect(emailIndex).toBeDefined();
    });

    it('should create a compound index', async () => {
      const result = await usersCollection.createIndex({ city: 1, age: -1 });
      expect(result).toBeDefined();

      const indexes = await usersCollection.listIndexes().toArray();
      const compoundIndex = indexes.find(idx => idx.name === 'city_1_age_-1');
      expect(compoundIndex).toBeDefined();
      expect(compoundIndex?.key).toEqual({ city: 1, age: -1 });
    });

    it('should create a unique index', async () => {
      await usersCollection.createIndex({ email: 1 }, { unique: true });

      await usersCollection.insertOne({ email: 'unique@example.com' });

      await expect(
        usersCollection.insertOne({ email: 'unique@example.com' })
      ).rejects.toThrow();
    });

    it('should list all indexes', async () => {
      await usersCollection.createIndex({ name: 1 });
      await usersCollection.createIndex({ age: -1 });

      const indexes = await usersCollection.listIndexes().toArray();

      // At least 3 indexes: _id, name, age
      expect(indexes.length).toBeGreaterThanOrEqual(3);
      expect(indexes.some(idx => idx.name === '_id_')).toBe(true);
      expect(indexes.some(idx => idx.name === 'name_1')).toBe(true);
    });

    it('should drop an index', async () => {
      await usersCollection.createIndex({ temp: 1 });

      let indexes = await usersCollection.listIndexes().toArray();
      expect(indexes.some(idx => idx.name === 'temp_1')).toBe(true);

      await usersCollection.dropIndex('temp_1');

      indexes = await usersCollection.listIndexes().toArray();
      expect(indexes.some(idx => idx.name === 'temp_1')).toBe(false);
    });

    it('should create TTL index', async () => {
      const sessionsCollection = db.collection('sessions');

      await sessionsCollection.createIndex(
        { createdAt: 1 },
        { expireAfterSeconds: 3600 } // Expire after 1 hour
      );

      const indexes = await sessionsCollection.listIndexes().toArray();
      const ttlIndex = indexes.find(idx => idx.name === 'createdAt_1');

      expect(ttlIndex).toBeDefined();
      expect(ttlIndex?.expireAfterSeconds).toBe(3600);
    });
  });

  // ============================================================================
  // 5. Text Search
  // ============================================================================

  describe('Text Search', () => {
    beforeEach(async () => {
      // Create text index
      await productsCollection.createIndex({ name: 'text', description: 'text' });

      // Insert test data
      await productsCollection.insertMany([
        { name: 'Laptop Pro', description: 'High-performance laptop for developers' },
        { name: 'Gaming Mouse', description: 'RGB gaming mouse with high DPI' },
        { name: 'Mechanical Keyboard', description: 'Professional mechanical keyboard' },
        { name: 'USB Cable', description: 'Standard USB-C cable' },
      ]);
    });

    it('should perform text search', async () => {
      const results = await productsCollection
        .find({ $text: { $search: 'gaming' } })
        .toArray();

      expect(results.length).toBe(1);
      expect(results[0].name).toBe('Gaming Mouse');
    });

    it('should search with multiple terms', async () => {
      const results = await productsCollection
        .find({ $text: { $search: 'laptop keyboard' } })
        .toArray();

      expect(results.length).toBeGreaterThanOrEqual(2);
    });

    it('should search with text score', async () => {
      const results = await productsCollection
        .find(
          { $text: { $search: 'professional' } },
          { projection: { score: { $meta: 'textScore' } } }
        )
        .sort({ score: { $meta: 'textScore' } })
        .toArray();

      expect(results.length).toBeGreaterThan(0);
      expect(results[0]).toHaveProperty('score');
    });

    it('should search with phrase', async () => {
      const results = await productsCollection
        .find({ $text: { $search: '"mechanical keyboard"' } })
        .toArray();

      expect(results.length).toBe(1);
      expect(results[0].name).toBe('Mechanical Keyboard');
    });
  });

  // ============================================================================
  // 6. Transactions
  // ============================================================================

  describe('Transactions (Multi-Document ACID)', () => {
    it('should complete a successful transaction', async () => {
      const session = client.startSession();

      try {
        await session.withTransaction(async () => {
          // Deduct from sender
          await usersCollection.updateOne(
            { name: 'Alice' },
            { $inc: { balance: -100 } },
            { session }
          );

          // Add to receiver
          await usersCollection.updateOne(
            { name: 'Bob' },
            { $inc: { balance: 100 } },
            { session }
          );
        });

        // Insert initial balances for verification
        await usersCollection.insertMany([
          { name: 'Alice', balance: 1000 },
          { name: 'Bob', balance: 500 },
        ]);

        // Run transaction
        const transactionSession = client.startSession();
        await transactionSession.withTransaction(async () => {
          await usersCollection.updateOne(
            { name: 'Alice' },
            { $inc: { balance: -100 } },
            { session: transactionSession }
          );

          await usersCollection.updateOne(
            { name: 'Bob' },
            { $inc: { balance: 100 } },
            { session: transactionSession }
          );
        });

        await transactionSession.endSession();

        // Verify balances
        const alice = await usersCollection.findOne({ name: 'Alice' });
        const bob = await usersCollection.findOne({ name: 'Bob' });

        expect(alice?.balance).toBe(900);
        expect(bob?.balance).toBe(600);
      } finally {
        await session.endSession();
      }
    });

    it('should rollback transaction on error', async () => {
      // Setup initial data
      await usersCollection.insertMany([
        { name: 'Alice', balance: 1000 },
        { name: 'Bob', balance: 500 },
      ]);

      const session = client.startSession();

      try {
        await session.withTransaction(async () => {
          await usersCollection.updateOne(
            { name: 'Alice' },
            { $inc: { balance: -100 } },
            { session }
          );

          // Simulate error
          throw new Error('Transaction failed');
        });
      } catch (error) {
        // Expected to fail
      } finally {
        await session.endSession();
      }

      // Verify rollback - balance should remain unchanged
      const alice = await usersCollection.findOne({ name: 'Alice' });
      expect(alice?.balance).toBe(1000);
    });
  });

  // ============================================================================
  // 7. Change Streams
  // ============================================================================

  describe('Change Streams', () => {
    it('should watch collection changes', async () => {
      const changes: any[] = [];
      const changeStream: ChangeStream = usersCollection.watch();

      // Listen for changes
      const changePromise = new Promise<void>((resolve) => {
        changeStream.on('change', (change) => {
          changes.push(change);
          if (changes.length === 2) {
            resolve();
          }
        });
      });

      // Make changes
      await usersCollection.insertOne({ name: 'Test User 1' });
      await usersCollection.insertOne({ name: 'Test User 2' });

      // Wait for changes to be captured
      await changePromise;
      await changeStream.close();

      expect(changes.length).toBe(2);
      expect(changes[0].operationType).toBe('insert');
      expect(changes[1].operationType).toBe('insert');
    });

    it('should watch with pipeline filter', async () => {
      const changes: any[] = [];
      const changeStream = usersCollection.watch([
        { $match: { 'fullDocument.status': 'active' } },
      ]);

      const changePromise = new Promise<void>((resolve) => {
        let activeCount = 0;
        changeStream.on('change', (change) => {
          changes.push(change);
          activeCount++;
          if (activeCount === 1) {
            resolve();
          }
        });
      });

      // Insert documents
      await usersCollection.insertOne({ name: 'User 1', status: 'active' });
      await usersCollection.insertOne({ name: 'User 2', status: 'inactive' });

      await changePromise;
      await changeStream.close();

      expect(changes.length).toBe(1);
      expect(changes[0].fullDocument.status).toBe('active');
    }, 15000);
  });

  // ============================================================================
  // 8. Bulk Operations
  // ============================================================================

  describe('Bulk Operations', () => {
    it('should perform ordered bulk write', async () => {
      const result = await usersCollection.bulkWrite([
        {
          insertOne: {
            document: { name: 'User 1', age: 25 },
          },
        },
        {
          updateOne: {
            filter: { name: 'User 1' },
            update: { $set: { age: 26 } },
          },
        },
        {
          deleteOne: {
            filter: { name: 'Nonexistent' },
          },
        },
      ]);

      expect(result.insertedCount).toBe(1);
      expect(result.modifiedCount).toBe(1);
      expect(result.deletedCount).toBe(0);

      const user = await usersCollection.findOne({ name: 'User 1' });
      expect(user?.age).toBe(26);
    });

    it('should perform unordered bulk write', async () => {
      const result = await usersCollection.bulkWrite(
        [
          { insertOne: { document: { name: 'User 1' } } },
          { insertOne: { document: { name: 'User 2' } } },
          { insertOne: { document: { name: 'User 3' } } },
          { updateMany: { filter: {}, update: { $set: { active: true } } } },
        ],
        { ordered: false }
      );

      expect(result.insertedCount).toBe(3);
      expect(result.modifiedCount).toBe(3);

      const count = await usersCollection.countDocuments({ active: true });
      expect(count).toBe(3);
    });
  });

  // ============================================================================
  // 9. GridFS File Storage
  // ============================================================================

  describe('GridFS File Storage', () => {
    let bucket: GridFSBucket;

    beforeEach(() => {
      bucket = new GridFSBucket(db, { bucketName: 'test_files' });
    });

    it('should upload file to GridFS', async () => {
      const filename = 'test-file.txt';
      const content = Buffer.from('Hello, GridFS!');

      // Upload file
      const uploadStream = bucket.openUploadStream(filename);
      const uploadPromise = new Promise<ObjectId>((resolve, reject) => {
        uploadStream.on('finish', () => resolve(uploadStream.id as ObjectId));
        uploadStream.on('error', reject);
      });

      uploadStream.write(content);
      uploadStream.end();

      const fileId = await uploadPromise;
      expect(fileId).toBeInstanceOf(ObjectId);

      // Verify file exists
      const files = await bucket.find({ _id: fileId }).toArray();
      expect(files.length).toBe(1);
      expect(files[0].filename).toBe(filename);
    });

    it('should download file from GridFS', async () => {
      const filename = 'download-test.txt';
      const content = Buffer.from('Test content for download');

      // Upload file
      const uploadStream = bucket.openUploadStream(filename);
      const uploadPromise = new Promise<ObjectId>((resolve) => {
        uploadStream.on('finish', () => resolve(uploadStream.id as ObjectId));
      });
      uploadStream.write(content);
      uploadStream.end();
      const fileId = await uploadPromise;

      // Download file
      const downloadStream = bucket.openDownloadStream(fileId);
      const chunks: Buffer[] = [];

      const downloadPromise = new Promise<Buffer>((resolve, reject) => {
        downloadStream.on('data', (chunk) => chunks.push(chunk));
        downloadStream.on('end', () => resolve(Buffer.concat(chunks)));
        downloadStream.on('error', reject);
      });

      const downloaded = await downloadPromise;
      expect(downloaded.toString()).toBe('Test content for download');
    });

    it('should delete file from GridFS', async () => {
      const uploadStream = bucket.openUploadStream('delete-test.txt');
      const uploadPromise = new Promise<ObjectId>((resolve) => {
        uploadStream.on('finish', () => resolve(uploadStream.id as ObjectId));
      });
      uploadStream.write(Buffer.from('Delete me'));
      uploadStream.end();
      const fileId = await uploadPromise;

      // Delete file
      await bucket.delete(fileId);

      // Verify deletion
      const files = await bucket.find({ _id: fileId }).toArray();
      expect(files.length).toBe(0);
    });
  });

  // ============================================================================
  // 10. Schema Validation
  // ============================================================================

  describe('Schema Validation', () => {
    it('should create collection with JSON schema validation', async () => {
      await db.createCollection('validated_users', {
        validator: {
          $jsonSchema: {
            bsonType: 'object',
            required: ['name', 'email', 'age'],
            properties: {
              name: {
                bsonType: 'string',
                description: 'must be a string and is required',
              },
              email: {
                bsonType: 'string',
                pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
                description: 'must be a valid email',
              },
              age: {
                bsonType: 'int',
                minimum: 0,
                maximum: 150,
                description: 'must be an integer between 0 and 150',
              },
            },
          },
        },
      });

      const validatedCollection = db.collection('validated_users');

      // Valid document should succeed
      await expect(
        validatedCollection.insertOne({ name: 'John', email: 'john@example.com', age: 30 })
      ).resolves.toBeDefined();

      // Invalid document should fail
      await expect(
        validatedCollection.insertOne({ name: 'Jane', email: 'invalid-email', age: 25 })
      ).rejects.toThrow();
    });
  });

  // ============================================================================
  // 11. Geospatial Queries
  // ============================================================================

  describe('Geospatial Queries', () => {
    beforeEach(async () => {
      // Create 2dsphere index
      await locationsCollection.createIndex({ location: '2dsphere' });

      // Insert test locations
      await locationsCollection.insertMany([
        {
          name: 'Central Park',
          location: { type: 'Point', coordinates: [-73.965355, 40.782865] },
        },
        {
          name: 'Times Square',
          location: { type: 'Point', coordinates: [-73.985130, 40.758896] },
        },
        {
          name: 'Brooklyn Bridge',
          location: { type: 'Point', coordinates: [-73.996826, 40.706086] },
        },
      ]);
    });

    it('should find locations near a point', async () => {
      const results = await locationsCollection
        .find({
          location: {
            $near: {
              $geometry: {
                type: 'Point',
                coordinates: [-73.968285, 40.785091], // Near Central Park
              },
              $maxDistance: 1000, // 1km
            },
          },
        })
        .toArray();

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].name).toBe('Central Park');
    });

    it('should find locations within polygon', async () => {
      const results = await locationsCollection
        .find({
          location: {
            $geoWithin: {
              $geometry: {
                type: 'Polygon',
                coordinates: [
                  [
                    [-74.0, 40.7],
                    [-74.0, 40.8],
                    [-73.9, 40.8],
                    [-73.9, 40.7],
                    [-74.0, 40.7],
                  ],
                ],
              },
            },
          },
        })
        .toArray();

      expect(results.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // 12. Time Series Collections
  // ============================================================================

  describe('Time Series Collections', () => {
    it('should create time series collection', async () => {
      await db.createCollection('sensor_data', {
        timeseries: {
          timeField: 'timestamp',
          metaField: 'sensorId',
          granularity: 'minutes',
        },
      });

      const sensorCollection = db.collection('sensor_data');

      // Insert time series data
      await sensorCollection.insertMany([
        {
          sensorId: 'sensor_1',
          timestamp: new Date('2024-01-01T10:00:00Z'),
          temperature: 22.5,
          humidity: 60,
        },
        {
          sensorId: 'sensor_1',
          timestamp: new Date('2024-01-01T10:05:00Z'),
          temperature: 23.0,
          humidity: 62,
        },
        {
          sensorId: 'sensor_2',
          timestamp: new Date('2024-01-01T10:00:00Z'),
          temperature: 21.5,
          humidity: 58,
        },
      ]);

      // Query time series data
      const data = await sensorCollection
        .find({ sensorId: 'sensor_1' })
        .sort({ timestamp: 1 })
        .toArray();

      expect(data.length).toBe(2);
      expect(data[0].temperature).toBe(22.5);
    });

    it('should perform aggregations on time series data', async () => {
      const sensorCollection = db.collection('sensor_data');

      const result = await sensorCollection
        .aggregate([
          {
            $group: {
              _id: '$sensorId',
              avgTemp: { $avg: '$temperature' },
              avgHumidity: { $avg: '$humidity' },
              readings: { $sum: 1 },
            },
          },
        ])
        .toArray();

      expect(result.length).toBeGreaterThan(0);
      expect(result[0]).toHaveProperty('avgTemp');
      expect(result[0]).toHaveProperty('avgHumidity');
    });
  });
});
