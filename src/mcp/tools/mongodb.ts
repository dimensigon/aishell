/**
 * MongoDB-Specific Tools for MCP Server
 * Provides MongoDB-specific database operations
 */

import { DatabaseConnectionManager, DatabaseType } from '../../cli/database-manager';
import { MCPTool } from '../types';
import { MongoClient, Db } from 'mongodb';

/**
 * MongoDB-specific MCP tools
 */
export class MongoDBTools {
  constructor(private connectionManager: DatabaseConnectionManager) {}

  /**
   * Get tool definitions
   */
  getToolDefinitions(): MCPTool[] {
    return [
      {
        name: 'mongo_list_databases',
        description: 'List all databases in MongoDB instance',
        inputSchema: {
          type: 'object',
          properties: {
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          }
        }
      },
      {
        name: 'mongo_list_collections',
        description: 'List all collections in current database',
        inputSchema: {
          type: 'object',
          properties: {
            database: {
              type: 'string',
              description: 'Database name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          }
        }
      },
      {
        name: 'mongo_find',
        description: 'Find documents in a collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'Collection name'
            },
            filter: {
              type: 'object',
              description: 'Query filter (MongoDB query object)'
            },
            limit: {
              type: 'number',
              description: 'Maximum number of documents to return'
            },
            skip: {
              type: 'number',
              description: 'Number of documents to skip'
            },
            sort: {
              type: 'object',
              description: 'Sort specification'
            },
            projection: {
              type: 'object',
              description: 'Field projection'
            },
            database: {
              type: 'string',
              description: 'Database name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['collection']
        }
      },
      {
        name: 'mongo_aggregate',
        description: 'Run aggregation pipeline on a collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'Collection name'
            },
            pipeline: {
              type: 'array',
              description: 'Aggregation pipeline stages',
              items: {
                type: 'object'
              }
            },
            database: {
              type: 'string',
              description: 'Database name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['collection', 'pipeline']
        }
      },
      {
        name: 'mongo_insert',
        description: 'Insert one or more documents into a collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'Collection name'
            },
            documents: {
              type: 'array',
              description: 'Documents to insert',
              items: {
                type: 'object'
              }
            },
            database: {
              type: 'string',
              description: 'Database name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['collection', 'documents']
        }
      },
      {
        name: 'mongo_update',
        description: 'Update documents in a collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'Collection name'
            },
            filter: {
              type: 'object',
              description: 'Query filter to match documents'
            },
            update: {
              type: 'object',
              description: 'Update operations'
            },
            upsert: {
              type: 'boolean',
              description: 'Create document if it does not exist'
            },
            multi: {
              type: 'boolean',
              description: 'Update multiple documents'
            },
            database: {
              type: 'string',
              description: 'Database name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['collection', 'filter', 'update']
        }
      },
      {
        name: 'mongo_delete',
        description: 'Delete documents from a collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'Collection name'
            },
            filter: {
              type: 'object',
              description: 'Query filter to match documents'
            },
            multi: {
              type: 'boolean',
              description: 'Delete multiple documents'
            },
            database: {
              type: 'string',
              description: 'Database name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['collection', 'filter']
        }
      },
      {
        name: 'mongo_create_index',
        description: 'Create an index on a collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'Collection name'
            },
            keys: {
              type: 'object',
              description: 'Index key specification'
            },
            options: {
              type: 'object',
              description: 'Index options (unique, sparse, etc.)'
            },
            database: {
              type: 'string',
              description: 'Database name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['collection', 'keys']
        }
      },
      {
        name: 'mongo_list_indexes',
        description: 'List all indexes on a collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'Collection name'
            },
            database: {
              type: 'string',
              description: 'Database name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['collection']
        }
      },
      {
        name: 'mongo_get_stats',
        description: 'Get collection statistics',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'Collection name'
            },
            database: {
              type: 'string',
              description: 'Database name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['collection']
        }
      }
    ];
  }

  /**
   * Execute a tool
   */
  async executeTool(name: string, args: any): Promise<any> {
    switch (name) {
      case 'mongo_list_databases':
        return this.listDatabases(args);
      case 'mongo_list_collections':
        return this.listCollections(args);
      case 'mongo_find':
        return this.find(args);
      case 'mongo_aggregate':
        return this.aggregate(args);
      case 'mongo_insert':
        return this.insert(args);
      case 'mongo_update':
        return this.update(args);
      case 'mongo_delete':
        return this.delete(args);
      case 'mongo_create_index':
        return this.createIndex(args);
      case 'mongo_list_indexes':
        return this.listIndexes(args);
      case 'mongo_get_stats':
        return this.getStats(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  /**
   * Get MongoDB client and database
   */
  private getDatabase(connectionName?: string, databaseName?: string): { client: MongoClient; db: Db } {
    const connection = connectionName
      ? this.connectionManager.getConnection(connectionName)
      : this.connectionManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    if (connection.type !== DatabaseType.MONGODB) {
      throw new Error(`Not a MongoDB connection: ${connection.type}`);
    }

    const client = connection.client as MongoClient;
    const dbName = databaseName || connection.config.database || 'test';
    const db = client.db(dbName);

    return { client, db };
  }

  /**
   * List databases
   */
  private async listDatabases(args: any): Promise<any> {
    const { client } = this.getDatabase(args.connection);

    const adminDb = client.db('admin');
    const result = await adminDb.admin().listDatabases();

    return {
      success: true,
      databases: result.databases,
      totalSize: result.totalSize,
      count: result.databases.length
    };
  }

  /**
   * List collections
   */
  private async listCollections(args: any): Promise<any> {
    const { db } = this.getDatabase(args.connection, args.database);

    const collections = await db.listCollections().toArray();

    return {
      success: true,
      database: db.databaseName,
      collections: collections.map(c => ({
        name: c.name,
        type: c.type,
        options: (c as any).options
      })),
      count: collections.length
    };
  }

  /**
   * Find documents
   */
  private async find(args: any): Promise<any> {
    const { db } = this.getDatabase(args.connection, args.database);

    const collection = db.collection(args.collection);
    let cursor = collection.find(args.filter || {});

    if (args.projection) {
      cursor = cursor.project(args.projection);
    }
    if (args.sort) {
      cursor = cursor.sort(args.sort);
    }
    if (args.skip) {
      cursor = cursor.skip(args.skip);
    }
    if (args.limit) {
      cursor = cursor.limit(args.limit);
    }

    const documents = await cursor.toArray();

    return {
      success: true,
      collection: args.collection,
      documents,
      count: documents.length
    };
  }

  /**
   * Run aggregation pipeline
   */
  private async aggregate(args: any): Promise<any> {
    const { db } = this.getDatabase(args.connection, args.database);

    const collection = db.collection(args.collection);
    const documents = await collection.aggregate(args.pipeline).toArray();

    return {
      success: true,
      collection: args.collection,
      pipeline: args.pipeline,
      documents,
      count: documents.length
    };
  }

  /**
   * Insert documents
   */
  private async insert(args: any): Promise<any> {
    const { db } = this.getDatabase(args.connection, args.database);

    const collection = db.collection(args.collection);
    const result = args.documents.length === 1
      ? await collection.insertOne(args.documents[0])
      : await collection.insertMany(args.documents);

    return {
      success: true,
      collection: args.collection,
      insertedCount: 'insertedCount' in result ? result.insertedCount : 1,
      insertedIds: 'insertedIds' in result ? result.insertedIds : [result.insertedId]
    };
  }

  /**
   * Update documents
   */
  private async update(args: any): Promise<any> {
    const { db } = this.getDatabase(args.connection, args.database);

    const collection = db.collection(args.collection);
    const options = { upsert: args.upsert || false };

    const result = args.multi
      ? await collection.updateMany(args.filter, args.update, options)
      : await collection.updateOne(args.filter, args.update, options);

    return {
      success: true,
      collection: args.collection,
      matchedCount: result.matchedCount,
      modifiedCount: result.modifiedCount,
      upsertedCount: result.upsertedCount,
      upsertedId: result.upsertedId
    };
  }

  /**
   * Delete documents
   */
  private async delete(args: any): Promise<any> {
    const { db } = this.getDatabase(args.connection, args.database);

    const collection = db.collection(args.collection);
    const result = args.multi
      ? await collection.deleteMany(args.filter)
      : await collection.deleteOne(args.filter);

    return {
      success: true,
      collection: args.collection,
      deletedCount: result.deletedCount
    };
  }

  /**
   * Create index
   */
  private async createIndex(args: any): Promise<any> {
    const { db } = this.getDatabase(args.connection, args.database);

    const collection = db.collection(args.collection);
    const indexName = await collection.createIndex(args.keys, args.options || {});

    return {
      success: true,
      collection: args.collection,
      indexName,
      keys: args.keys
    };
  }

  /**
   * List indexes
   */
  private async listIndexes(args: any): Promise<any> {
    const { db } = this.getDatabase(args.connection, args.database);

    const collection = db.collection(args.collection);
    const indexes = await collection.indexes();

    return {
      success: true,
      collection: args.collection,
      indexes,
      count: indexes.length
    };
  }

  /**
   * Get collection statistics
   */
  private async getStats(args: any): Promise<any> {
    const { db } = this.getDatabase(args.connection, args.database);

    const stats = await db.command({ collStats: args.collection });

    return {
      success: true,
      collection: args.collection,
      statistics: {
        namespace: stats.ns,
        count: stats.count,
        size: stats.size,
        storageSize: stats.storageSize,
        avgObjSize: stats.avgObjSize,
        indexes: stats.nindexes,
        indexSize: stats.totalIndexSize
      }
    };
  }
}
