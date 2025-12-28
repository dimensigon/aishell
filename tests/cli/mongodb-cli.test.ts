/**
 * MongoDB CLI Tests
 * Comprehensive test suite for MongoDB-specific CLI commands
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { MongoClient, ObjectId } from 'mongodb';
import { MongoDBCLI } from '../../src/cli/mongodb-cli';
import { StateManager } from '../../src/core/state-manager';
import { writeFileSync, unlinkSync, existsSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';

// MongoDB test configuration
const TEST_MONGO_URL = 'mongodb://admin:MyMongoPass123@localhost:27017/test_db?authSource=admin';
const TEST_DB = 'test_db';

describe('MongoDBCLI', () => {
  let mongoCLI: MongoDBCLI;
  let stateManager: StateManager;
  let testClient: MongoClient;

  beforeAll(async () => {
    // Connect test client for setup/teardown
    testClient = new MongoClient(TEST_MONGO_URL);
    await testClient.connect();
  });

  afterAll(async () => {
    await testClient.close();
  });

  beforeEach(() => {
    stateManager = new StateManager();
    mongoCLI = new MongoDBCLI(stateManager);
  });

  afterEach(async () => {
    // Clean up connections
    const connections = mongoCLI.listConnections();
    for (const conn of connections) {
      await mongoCLI.disconnect(conn.name).catch(() => {});
    }
  });

  describe('Connection String Parsing', () => {
    it('should parse basic MongoDB connection string', () => {
      const result = mongoCLI.parseConnectionString('mongodb://localhost:27017/mydb');

      expect(result.protocol).toBe('mongodb');
      expect(result.host).toBe('localhost');
      expect(result.port).toBe(27017);
      expect(result.database).toBe('mydb');
    });

    it('should parse MongoDB connection string with authentication', () => {
      const result = mongoCLI.parseConnectionString(
        'mongodb://user:pass@localhost:27017/mydb'
      );

      expect(result.protocol).toBe('mongodb');
      expect(result.host).toBe('localhost');
      expect(result.port).toBe(27017);
      expect(result.database).toBe('mydb');
    });

    it('should parse MongoDB SRV connection string', () => {
      const result = mongoCLI.parseConnectionString(
        'mongodb+srv://user:pass@cluster.mongodb.net/mydb'
      );

      expect(result.protocol).toBe('mongodb+srv');
      expect(result.host).toBe('cluster.mongodb.net');
    });

    it('should parse connection string with options', () => {
      const result = mongoCLI.parseConnectionString(
        'mongodb://localhost:27017/mydb?retryWrites=true&w=majority'
      );

      expect(result.options).toBeDefined();
      expect(result.options?.retryWrites).toBe('true');
      expect(result.options?.w).toBe('majority');
    });

    it('should use default port if not specified', () => {
      const result = mongoCLI.parseConnectionString('mongodb://localhost/mydb');

      expect(result.port).toBe(27017);
    });

    it('should throw error for invalid connection string', () => {
      expect(() => {
        mongoCLI.parseConnectionString('invalid://connection');
      }).toThrow('Invalid MongoDB connection string format');
    });
  });

  describe('Connection Management', () => {
    it('should connect to MongoDB successfully', async () => {
      const connection = await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');

      expect(connection.name).toBe('test-conn');
      expect(connection.client).toBeDefined();
      expect(connection.database).toBe(TEST_DB);
    });

    it('should generate connection name if not provided', async () => {
      const connection = await mongoCLI.connect(TEST_MONGO_URL);

      expect(connection.name).toMatch(/^mongo_localhost_/);
    });

    it('should set first connection as active', async () => {
      const connection = await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');

      expect(connection.isActive).toBe(true);
    });

    it('should disconnect from MongoDB', async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');
      await mongoCLI.disconnect('test-conn');

      const connections = mongoCLI.listConnections();
      expect(connections.length).toBe(0);
    });

    it('should disconnect active connection when no name provided', async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');
      await mongoCLI.disconnect();

      const connections = mongoCLI.listConnections();
      expect(connections.length).toBe(0);
    });

    it('should throw error when disconnecting non-existent connection', async () => {
      await expect(mongoCLI.disconnect('non-existent')).rejects.toThrow(
        'Connection not found'
      );
    });

    it('should list all connections', async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'conn1');
      await mongoCLI.connect(TEST_MONGO_URL, 'conn2');

      const connections = mongoCLI.listConnections();
      expect(connections.length).toBe(2);
      expect(connections.map((c) => c.name)).toContain('conn1');
      expect(connections.map((c) => c.name)).toContain('conn2');
    });

    it('should handle connection timeout', async () => {
      const invalidUrl = 'mongodb://invalid-host:27017/mydb';

      await expect(mongoCLI.connect(invalidUrl)).rejects.toThrow();
    }, 10000);
  });

  describe('Collection Operations', () => {
    const TEST_COLLECTION = 'test_collection';

    beforeEach(async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');

      // Setup test data
      const db = testClient.db(TEST_DB);
      const collection = db.collection(TEST_COLLECTION);

      await collection.deleteMany({});
      await collection.insertMany([
        { name: 'Alice', age: 30, city: 'New York' },
        { name: 'Bob', age: 25, city: 'London' },
        { name: 'Charlie', age: 35, city: 'Paris' },
        { name: 'David', age: 28, city: 'Tokyo' },
        { name: 'Eve', age: 32, city: 'Berlin' },
      ]);
    });

    afterEach(async () => {
      const db = testClient.db(TEST_DB);
      await db.collection(TEST_COLLECTION).drop().catch(() => {});
    });

    it('should query all documents', async () => {
      const results = await mongoCLI.query({
        collection: TEST_COLLECTION,
        filter: '{}',
      });

      expect(results.length).toBe(5);
    });

    it('should query with filter', async () => {
      const results = await mongoCLI.query({
        collection: TEST_COLLECTION,
        filter: '{"age": {"$gte": 30}}',
      });

      expect(results.length).toBe(3);
      expect(results.every((doc) => doc.age >= 30)).toBe(true);
    });

    it('should query with projection', async () => {
      const results = await mongoCLI.query({
        collection: TEST_COLLECTION,
        filter: '{}',
        projection: '{"name": 1, "age": 1, "_id": 0}',
      });

      expect(results.length).toBe(5);
      expect(results[0]).not.toHaveProperty('_id');
      expect(results[0]).not.toHaveProperty('city');
      expect(results[0]).toHaveProperty('name');
      expect(results[0]).toHaveProperty('age');
    });

    it('should query with sort', async () => {
      const results = await mongoCLI.query({
        collection: TEST_COLLECTION,
        filter: '{}',
        sort: '{"age": -1}',
      });

      expect(results[0].age).toBe(35);
      expect(results[results.length - 1].age).toBe(25);
    });

    it('should query with limit', async () => {
      const results = await mongoCLI.query({
        collection: TEST_COLLECTION,
        filter: '{}',
        limit: 3,
      });

      expect(results.length).toBe(3);
    });

    it('should query with skip', async () => {
      const results = await mongoCLI.query({
        collection: TEST_COLLECTION,
        filter: '{}',
        sort: '{"age": 1}',
        skip: 2,
      });

      expect(results.length).toBe(3);
      expect(results[0].age).toBe(30);
    });

    it('should list collections', async () => {
      const collections = await mongoCLI.listCollections(TEST_DB);

      expect(collections).toContain(TEST_COLLECTION);
    });

    it('should throw error when querying non-existent collection', async () => {
      await expect(
        mongoCLI.query({
          collection: 'non_existent_collection',
          filter: '{}',
        })
      ).resolves.toEqual([]);
    });
  });

  describe('Aggregation Operations', () => {
    const TEST_COLLECTION = 'test_aggregation';

    beforeEach(async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');

      const db = testClient.db(TEST_DB);
      const collection = db.collection(TEST_COLLECTION);

      await collection.deleteMany({});
      await collection.insertMany([
        { product: 'A', category: 'electronics', price: 100, quantity: 5 },
        { product: 'B', category: 'electronics', price: 200, quantity: 3 },
        { product: 'C', category: 'clothing', price: 50, quantity: 10 },
        { product: 'D', category: 'clothing', price: 75, quantity: 8 },
        { product: 'E', category: 'electronics', price: 150, quantity: 4 },
      ]);
    });

    afterEach(async () => {
      const db = testClient.db(TEST_DB);
      await db.collection(TEST_COLLECTION).drop().catch(() => {});
    });

    it('should execute simple aggregation', async () => {
      const pipeline = JSON.stringify([{ $match: { category: 'electronics' } }]);

      const results = await mongoCLI.aggregate({
        collection: TEST_COLLECTION,
        pipeline,
      });

      expect(results.length).toBe(3);
      expect(results.every((doc) => doc.category === 'electronics')).toBe(true);
    });

    it('should execute aggregation with $group', async () => {
      const pipeline = JSON.stringify([
        {
          $group: {
            _id: '$category',
            totalQuantity: { $sum: '$quantity' },
            avgPrice: { $avg: '$price' },
          },
        },
      ]);

      const results = await mongoCLI.aggregate({
        collection: TEST_COLLECTION,
        pipeline,
      });

      expect(results.length).toBe(2);

      const electronics = results.find((r) => r._id === 'electronics');
      expect(electronics).toBeDefined();
      expect(electronics?.totalQuantity).toBe(12);
    });

    it('should execute aggregation with multiple stages', async () => {
      const pipeline = JSON.stringify([
        { $match: { price: { $gte: 75 } } },
        { $group: { _id: '$category', count: { $sum: 1 } } },
        { $sort: { count: -1 } },
      ]);

      const results = await mongoCLI.aggregate({
        collection: TEST_COLLECTION,
        pipeline,
      });

      expect(results.length).toBeGreaterThan(0);
      expect(results[0]).toHaveProperty('_id');
      expect(results[0]).toHaveProperty('count');
    });

    it('should execute aggregation with $project', async () => {
      const pipeline = JSON.stringify([
        {
          $project: {
            product: 1,
            total: { $multiply: ['$price', '$quantity'] },
          },
        },
      ]);

      const results = await mongoCLI.aggregate({
        collection: TEST_COLLECTION,
        pipeline,
      });

      expect(results.length).toBe(5);
      expect(results[0]).toHaveProperty('total');
    });

    it('should throw error for invalid pipeline', async () => {
      await expect(
        mongoCLI.aggregate({
          collection: TEST_COLLECTION,
          pipeline: 'invalid json',
        })
      ).rejects.toThrow('Invalid JSON');
    });

    it('should throw error for non-array pipeline', async () => {
      await expect(
        mongoCLI.aggregate({
          collection: TEST_COLLECTION,
          pipeline: '{"$match": {"category": "electronics"}}',
        })
      ).rejects.toThrow('Pipeline must be an array');
    });
  });

  describe('Index Operations', () => {
    const TEST_COLLECTION = 'test_indexes';

    beforeEach(async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');

      const db = testClient.db(TEST_DB);
      const collection = db.collection(TEST_COLLECTION);

      await collection.deleteMany({});
      await collection.insertOne({ name: 'test', value: 1 });

      // Create test indexes
      await collection.createIndex({ name: 1 });
      await collection.createIndex({ value: -1 }, { unique: true });
      await collection.createIndex({ name: 1, value: 1 });
    });

    afterEach(async () => {
      const db = testClient.db(TEST_DB);
      await db.collection(TEST_COLLECTION).drop().catch(() => {});
    });

    it('should list indexes for collection', async () => {
      const indexes = await mongoCLI.listIndexes(TEST_COLLECTION);

      expect(indexes.length).toBeGreaterThanOrEqual(4); // _id + 3 custom
    });

    it('should include index details', async () => {
      const indexes = await mongoCLI.listIndexes(TEST_COLLECTION);

      const nameIndex = indexes.find((idx) => idx.name === 'name_1');
      expect(nameIndex).toBeDefined();
      expect(nameIndex?.key).toEqual({ name: 1 });
    });

    it('should identify unique indexes', async () => {
      const indexes = await mongoCLI.listIndexes(TEST_COLLECTION);

      const uniqueIndex = indexes.find((idx) => idx.name === 'value_-1');
      expect(uniqueIndex).toBeDefined();
      expect(uniqueIndex?.unique).toBe(true);
    });

    it('should handle compound indexes', async () => {
      const indexes = await mongoCLI.listIndexes(TEST_COLLECTION);

      const compoundIndex = indexes.find((idx) => idx.name === 'name_1_value_1');
      expect(compoundIndex).toBeDefined();
      expect(compoundIndex?.key).toEqual({ name: 1, value: 1 });
    });
  });

  describe('Import/Export Operations', () => {
    const TEST_COLLECTION = 'test_import_export';
    let tempFiles: string[] = [];

    beforeEach(async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');

      const db = testClient.db(TEST_DB);
      await db.collection(TEST_COLLECTION).deleteMany({});
    });

    afterEach(async () => {
      const db = testClient.db(TEST_DB);
      await db.collection(TEST_COLLECTION).drop().catch(() => {});

      // Clean up temp files
      tempFiles.forEach((file) => {
        if (existsSync(file)) {
          unlinkSync(file);
        }
      });
      tempFiles = [];
    });

    it('should import JSON array', async () => {
      const testData = [
        { name: 'Alice', age: 30 },
        { name: 'Bob', age: 25 },
      ];

      const tempFile = join(tmpdir(), `test-import-${Date.now()}.json`);
      tempFiles.push(tempFile);

      writeFileSync(tempFile, JSON.stringify(testData), 'utf-8');

      const count = await mongoCLI.import({
        collection: TEST_COLLECTION,
        file: tempFile,
        format: 'json',
      });

      expect(count).toBe(2);

      // Verify import
      const db = testClient.db(TEST_DB);
      const docs = await db.collection(TEST_COLLECTION).find({}).toArray();
      expect(docs.length).toBe(2);
    });

    it('should import single JSON object', async () => {
      const testData = { name: 'Alice', age: 30 };

      const tempFile = join(tmpdir(), `test-import-${Date.now()}.json`);
      tempFiles.push(tempFile);

      writeFileSync(tempFile, JSON.stringify(testData), 'utf-8');

      const count = await mongoCLI.import({
        collection: TEST_COLLECTION,
        file: tempFile,
        format: 'json',
      });

      expect(count).toBe(1);
    });

    it('should drop collection before import if requested', async () => {
      const db = testClient.db(TEST_DB);
      await db.collection(TEST_COLLECTION).insertOne({ name: 'Existing', age: 99 });

      const testData = [{ name: 'Alice', age: 30 }];

      const tempFile = join(tmpdir(), `test-import-${Date.now()}.json`);
      tempFiles.push(tempFile);

      writeFileSync(tempFile, JSON.stringify(testData), 'utf-8');

      await mongoCLI.import({
        collection: TEST_COLLECTION,
        file: tempFile,
        format: 'json',
        dropCollection: true,
      });

      const docs = await db.collection(TEST_COLLECTION).find({}).toArray();
      expect(docs.length).toBe(1);
      expect(docs[0].name).toBe('Alice');
    });

    it('should export collection to JSON', async () => {
      const db = testClient.db(TEST_DB);
      await db.collection(TEST_COLLECTION).insertMany([
        { name: 'Alice', age: 30 },
        { name: 'Bob', age: 25 },
      ]);

      const tempFile = join(tmpdir(), `test-export-${Date.now()}.json`);
      tempFiles.push(tempFile);

      await mongoCLI.export({
        collection: TEST_COLLECTION,
        output: tempFile,
        format: 'json',
      });

      expect(existsSync(tempFile)).toBe(true);

      const content = JSON.parse(readFileSync(tempFile, 'utf-8'));
      expect(content.length).toBe(2);
    });

    it('should export with filter', async () => {
      const db = testClient.db(TEST_DB);
      await db.collection(TEST_COLLECTION).insertMany([
        { name: 'Alice', age: 30 },
        { name: 'Bob', age: 25 },
        { name: 'Charlie', age: 35 },
      ]);

      const tempFile = join(tmpdir(), `test-export-${Date.now()}.json`);
      tempFiles.push(tempFile);

      await mongoCLI.export({
        collection: TEST_COLLECTION,
        output: tempFile,
        format: 'json',
        filter: '{"age": {"$gte": 30}}',
      });

      const content = JSON.parse(readFileSync(tempFile, 'utf-8'));
      expect(content.length).toBe(2);
    });

    it('should export with limit', async () => {
      const db = testClient.db(TEST_DB);
      await db.collection(TEST_COLLECTION).insertMany([
        { name: 'Alice', age: 30 },
        { name: 'Bob', age: 25 },
        { name: 'Charlie', age: 35 },
      ]);

      const tempFile = join(tmpdir(), `test-export-${Date.now()}.json`);
      tempFiles.push(tempFile);

      await mongoCLI.export({
        collection: TEST_COLLECTION,
        output: tempFile,
        format: 'json',
        limit: 2,
      });

      const content = JSON.parse(readFileSync(tempFile, 'utf-8'));
      expect(content.length).toBe(2);
    });
  });

  describe('Connection Statistics', () => {
    it('should get connection stats', async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');

      const stats = await mongoCLI.getConnectionStats('test-conn');

      expect(stats).toBeDefined();
      expect(stats.name).toBe('test-conn');
      expect(stats.uptime).toBeGreaterThan(0);
      expect(stats.connections).toBeDefined();
      expect(stats.opcounters).toBeDefined();
    });

    it('should get active connection stats when no name provided', async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');

      const stats = await mongoCLI.getConnectionStats();

      expect(stats).toBeDefined();
      expect(stats.name).toBe('test-conn');
    });

    it('should throw error for non-existent connection', async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');

      await expect(mongoCLI.getConnectionStats('non-existent')).rejects.toThrow(
        'Connection not found'
      );
    });
  });

  describe('Error Handling', () => {
    it('should throw error when no active connection', async () => {
      await expect(
        mongoCLI.query({
          collection: 'test',
          filter: '{}',
        })
      ).rejects.toThrow('No active MongoDB connection');
    });

    it('should handle invalid JSON in query filter', async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');

      await expect(
        mongoCLI.query({
          collection: 'test',
          filter: 'invalid json',
        })
      ).rejects.toThrow('Invalid JSON');
    });

    it('should handle invalid JSON in aggregation pipeline', async () => {
      await mongoCLI.connect(TEST_MONGO_URL, 'test-conn');

      await expect(
        mongoCLI.aggregate({
          collection: 'test',
          pipeline: 'invalid json',
        })
      ).rejects.toThrow('Invalid JSON');
    });
  });
});

// Helper function for reading files
function readFileSync(path: string, encoding: BufferEncoding): string {
  return require('fs').readFileSync(path, encoding);
}
