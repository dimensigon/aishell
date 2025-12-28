/**
 * MongoDB Connection Helper for Tests
 * Provides utilities for establishing and managing MongoDB connections in tests
 */

import { MongoClient, Db, Collection } from 'mongodb';
import { testDatabaseConfig } from '../../config/databases.test';

export interface MongoTestContext {
  client: MongoClient;
  db: Db;
  collections: Map<string, Collection>;
  isReplicaSetEnabled: boolean;
}

/**
 * Connect to MongoDB test database
 */
export async function connectToTestMongo(
  dbName?: string,
  timeout: number = 5000
): Promise<MongoTestContext> {
  const client = new MongoClient(testDatabaseConfig.mongodb.url, {
    serverSelectionTimeoutMS: timeout,
    connectTimeoutMS: timeout,
  });

  await client.connect();

  const db = client.db(dbName || testDatabaseConfig.mongodb.database);

  // Check if replica set is enabled
  let isReplicaSetEnabled = false;
  try {
    const adminDb = client.db('admin');
    await adminDb.command({ replSetGetStatus: 1 });
    isReplicaSetEnabled = true;
  } catch {
    // Standalone mode
    isReplicaSetEnabled = false;
  }

  return {
    client,
    db,
    collections: new Map(),
    isReplicaSetEnabled,
  };
}

/**
 * Disconnect from MongoDB
 */
export async function disconnectFromMongo(context: MongoTestContext): Promise<void> {
  if (context.client) {
    await context.client.close();
  }
}

/**
 * Clean up all collections in database
 */
export async function cleanupCollections(db: Db): Promise<void> {
  try {
    const collections = await db.listCollections().toArray();
    for (const collection of collections) {
      // Skip system collections and time series views
      if (
        !collection.name.startsWith('system.') &&
        collection.type !== 'view'
      ) {
        await db.collection(collection.name).deleteMany({});
      }
    }
  } catch (error) {
    console.warn('Warning: Collection cleanup failed:', error);
  }
}

/**
 * Drop test database
 */
export async function dropTestDatabase(db: Db): Promise<void> {
  try {
    await db.dropDatabase();
  } catch (error) {
    console.warn('Warning: Database drop failed:', error);
  }
}

/**
 * Get or create collection
 */
export function getCollection(
  context: MongoTestContext,
  collectionName: string
): Collection {
  if (!context.collections.has(collectionName)) {
    const collection = context.db.collection(collectionName);
    context.collections.set(collectionName, collection);
  }
  return context.collections.get(collectionName)!;
}

/**
 * Wait for MongoDB to be ready
 */
export async function waitForMongo(
  maxRetries: number = 30,
  delayMs: number = 1000
): Promise<boolean> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const client = new MongoClient(testDatabaseConfig.mongodb.url, {
        serverSelectionTimeoutMS: 2000,
      });
      await client.connect();
      await client.db().admin().ping();
      await client.close();
      return true;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
  return false;
}

/**
 * Create test indexes
 */
export async function createTestIndexes(db: Db): Promise<void> {
  // Users indexes
  const usersCollection = db.collection('users');
  await usersCollection.createIndex({ email: 1 });
  await usersCollection.createIndex({ city: 1, age: -1 });
  await usersCollection.createIndex({ active: 1 });
  await usersCollection.createIndex({ createdAt: 1 });

  // Products indexes
  const productsCollection = db.collection('products');
  await productsCollection.createIndex({ name: 'text', description: 'text' });
  await productsCollection.createIndex({ category: 1, price: -1 });
  await productsCollection.createIndex({ tags: 1 });

  // Orders indexes
  const ordersCollection = db.collection('orders');
  await ordersCollection.createIndex({ customerId: 1, orderDate: -1 });
  await ordersCollection.createIndex({ status: 1 });
  await ordersCollection.createIndex({ orderDate: -1 });

  // Locations index
  const locationsCollection = db.collection('locations');
  await locationsCollection.createIndex({ location: '2dsphere' });
}

/**
 * Check if MongoDB container is running
 */
export async function isMongoContainerRunning(): Promise<boolean> {
  try {
    const client = new MongoClient(testDatabaseConfig.mongodb.url, {
      serverSelectionTimeoutMS: 2000,
      connectTimeoutMS: 2000,
    });
    await client.connect();
    await client.db().admin().ping();
    await client.close();
    return true;
  } catch {
    return false;
  }
}

/**
 * Get MongoDB server info
 */
export async function getMongoServerInfo(client: MongoClient): Promise<any> {
  try {
    const adminDb = client.db().admin();
    const serverInfo = await adminDb.serverInfo();
    return serverInfo;
  } catch (error) {
    return { error: 'Failed to get server info' };
  }
}
