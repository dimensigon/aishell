/**
 * MongoDB-specific CLI Commands
 * Provides MongoDB commands with aggregation, document operations, and index management
 */

import { Command } from 'commander';
import { MongoClient, ObjectId, Document, AggregationCursor } from 'mongodb';
import { StateManager } from '../core/state-manager';
import { createLogger } from '../core/logger';
import { readFileSync } from 'fs';
import { writeFileSync } from 'fs';
import Table3 from 'cli-table3';
import chalk from 'chalk';

const logger = createLogger('MongoDBCLI');

/**
 * MongoDB connection info
 */
interface MongoConnection {
  name: string;
  client: MongoClient;
  connectionString: string;
  database?: string;
  connectedAt: number;
  isActive: boolean;
}

/**
 * Query options
 */
interface QueryOptions {
  collection: string;
  filter?: string;
  projection?: string;
  sort?: string;
  limit?: number;
  skip?: number;
}

/**
 * Aggregation options
 */
interface AggregateOptions {
  collection: string;
  pipeline: string;
  explain?: boolean;
}

/**
 * Export options
 */
interface ExportOptions {
  collection: string;
  output: string;
  format?: 'json' | 'csv';
  filter?: string;
  limit?: number;
}

/**
 * Import options
 */
interface ImportOptions {
  collection: string;
  file: string;
  format?: 'json' | 'csv';
  dropCollection?: boolean;
}

/**
 * MongoDB CLI Manager
 */
export class MongoDBCLI {
  private connections = new Map<string, MongoConnection>();
  private activeConnection: string | null = null;

  constructor(private stateManager: StateManager) {
    this.loadConnectionsFromState();
  }

  /**
   * Load connections from state
   */
  private loadConnectionsFromState(): void {
    const state = this.stateManager.get('mongodb.connections');
    if (state && Array.isArray(state)) {
      // Note: Connections are not automatically restored on startup
      // User must reconnect manually for security
      logger.info(`Found ${state.length} saved MongoDB connections (not restored)`);
    }
  }

  /**
   * Save connections to state
   */
  private saveConnectionsToState(): void {
    const connections = Array.from(this.connections.values()).map((conn) => ({
      name: conn.name,
      connectionString: conn.connectionString,
      database: conn.database,
      connectedAt: conn.connectedAt,
      isActive: conn.isActive,
    }));

    this.stateManager.set('mongodb.connections', connections);
  }

  /**
   * Parse MongoDB connection string
   */
  parseConnectionString(connectionString: string): {
    protocol: string;
    host: string;
    port: number;
    database?: string;
    options?: Record<string, string>;
  } {
    try {
      // Handle mongodb:// or mongodb+srv://
      const match = connectionString.match(
        /^mongodb(\+srv)?:\/\/(?:([^:]+):([^@]+)@)?([^:/]+)(?::(\d+))?(?:\/([^?]+))?(?:\?(.+))?$/
      );

      if (!match) {
        throw new Error('Invalid MongoDB connection string format');
      }

      const [, srv, username, password, host, port, database, queryString] = match;

      const result: any = {
        protocol: srv ? 'mongodb+srv' : 'mongodb',
        host,
        port: port ? parseInt(port) : 27017,
      };

      if (database) {
        result.database = database;
      }

      if (queryString) {
        result.options = Object.fromEntries(
          queryString.split('&').map((param) => param.split('='))
        );
      }

      return result;
    } catch (error) {
      throw new Error(
        `Failed to parse connection string: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Connect to MongoDB
   */
  async connect(connectionString: string, name?: string): Promise<MongoConnection> {
    try {
      logger.info('Connecting to MongoDB', { connectionString, name });

      // Parse connection string
      const parsed = this.parseConnectionString(connectionString);

      // Generate name if not provided
      const connName = name || `mongo_${parsed.host}_${parsed.port}`;

      // Check if connection already exists
      if (this.connections.has(connName)) {
        logger.info('Connection already exists', { name: connName });
        return this.connections.get(connName)!;
      }

      // Create MongoDB client
      const client = new MongoClient(connectionString, {
        maxPoolSize: 10,
        minPoolSize: 2,
        serverSelectionTimeoutMS: 5000,
      });

      // Connect
      await client.connect();

      // Test connection
      await client.db('admin').command({ ping: 1 });

      const connection: MongoConnection = {
        name: connName,
        client,
        connectionString,
        database: parsed.database,
        connectedAt: Date.now(),
        isActive: false,
      };

      this.connections.set(connName, connection);

      // Set as active if first connection
      if (this.connections.size === 1) {
        this.activeConnection = connName;
        connection.isActive = true;
      }

      this.saveConnectionsToState();

      logger.info('Connected to MongoDB successfully', { name: connName });

      console.log(chalk.green(`\n✓ Connected to MongoDB: ${connName}`));
      if (parsed.database) {
        console.log(chalk.gray(`  Database: ${parsed.database}`));
      }
      console.log(chalk.gray(`  Host: ${parsed.host}:${parsed.port}\n`));

      return connection;
    } catch (error) {
      logger.error('Failed to connect to MongoDB', { error });
      throw new Error(
        `Failed to connect to MongoDB: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Disconnect from MongoDB
   */
  async disconnect(name?: string): Promise<void> {
    try {
      if (name) {
        // Disconnect specific connection
        const connection = this.connections.get(name);
        if (!connection) {
          throw new Error(`Connection not found: ${name}`);
        }

        await connection.client.close();
        this.connections.delete(name);

        if (this.activeConnection === name) {
          this.activeConnection = this.connections.size > 0 ? this.connections.keys().next().value : null;
        }

        console.log(chalk.yellow(`\n✓ Disconnected from MongoDB: ${name}\n`));
      } else {
        // Disconnect active connection
        if (!this.activeConnection) {
          throw new Error('No active MongoDB connection');
        }

        await this.disconnect(this.activeConnection);
      }

      this.saveConnectionsToState();
    } catch (error) {
      logger.error('Failed to disconnect from MongoDB', { error });
      throw new Error(
        `Failed to disconnect from MongoDB: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Get active connection
   */
  private getActiveConnection(): MongoConnection {
    if (!this.activeConnection) {
      throw new Error('No active MongoDB connection. Use "ai-shell mongo connect" first.');
    }

    const connection = this.connections.get(this.activeConnection);
    if (!connection) {
      throw new Error('Active connection not found');
    }

    return connection;
  }

  /**
   * Query MongoDB collection
   */
  async query(options: QueryOptions): Promise<Document[]> {
    try {
      const connection = this.getActiveConnection();
      const db = connection.client.db(connection.database);
      const collection = db.collection(options.collection);

      // Parse filter
      const filter = options.filter ? this.parseJSON(options.filter) : {};

      // Parse projection
      const projection = options.projection ? this.parseJSON(options.projection) : undefined;

      // Parse sort
      const sort = options.sort ? this.parseJSON(options.sort) : undefined;

      // Build query
      let cursor = collection.find(filter);

      if (projection) {
        cursor = cursor.project(projection);
      }

      if (sort) {
        cursor = cursor.sort(sort);
      }

      if (options.skip) {
        cursor = cursor.skip(options.skip);
      }

      if (options.limit) {
        cursor = cursor.limit(options.limit);
      }

      const results = await cursor.toArray();

      logger.info('Query executed', {
        collection: options.collection,
        count: results.length,
      });

      return results;
    } catch (error) {
      logger.error('Query failed', { error });
      throw new Error(
        `Query failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Execute aggregation pipeline
   */
  async aggregate(options: AggregateOptions): Promise<Document[]> {
    try {
      const connection = this.getActiveConnection();
      const db = connection.client.db(connection.database);
      const collection = db.collection(options.collection);

      // Parse pipeline
      const pipeline = this.parseJSON(options.pipeline);

      if (!Array.isArray(pipeline)) {
        throw new Error('Pipeline must be an array');
      }

      // Execute aggregation
      if (options.explain) {
        const explanation = await collection
          .aggregate(pipeline, { explain: true })
          .toArray();

        console.log(chalk.cyan('\n📊 Aggregation Execution Plan:\n'));
        console.log(JSON.stringify(explanation, null, 2));
        console.log();

        return [];
      }

      const results = await collection.aggregate(pipeline).toArray();

      logger.info('Aggregation executed', {
        collection: options.collection,
        stages: pipeline.length,
        count: results.length,
      });

      return results;
    } catch (error) {
      logger.error('Aggregation failed', { error });
      throw new Error(
        `Aggregation failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * List collections
   */
  async listCollections(database?: string): Promise<string[]> {
    try {
      const connection = this.getActiveConnection();
      const dbName = database || connection.database;

      if (!dbName) {
        throw new Error('No database specified');
      }

      const db = connection.client.db(dbName);
      const collections = await db.listCollections().toArray();

      return collections.map((coll) => coll.name);
    } catch (error) {
      logger.error('Failed to list collections', { error });
      throw new Error(
        `Failed to list collections: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * List indexes for a collection
   */
  async listIndexes(collection: string): Promise<Document[]> {
    try {
      const connection = this.getActiveConnection();
      const db = connection.client.db(connection.database);
      const coll = db.collection(collection);

      const indexes = await coll.indexes();

      logger.info('Indexes retrieved', {
        collection,
        count: indexes.length,
      });

      return indexes;
    } catch (error) {
      logger.error('Failed to list indexes', { error });
      throw new Error(
        `Failed to list indexes: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Import data into collection
   */
  async import(options: ImportOptions): Promise<number> {
    try {
      const connection = this.getActiveConnection();
      const db = connection.client.db(connection.database);
      const collection = db.collection(options.collection);

      // Read file
      const fileContent = readFileSync(options.file, 'utf-8');

      let documents: Document[];

      // Parse based on format
      const format = options.format || 'json';

      if (format === 'json') {
        const parsed = JSON.parse(fileContent);
        documents = Array.isArray(parsed) ? parsed : [parsed];
      } else {
        throw new Error('CSV import not yet implemented');
      }

      // Drop collection if requested
      if (options.dropCollection) {
        await collection.drop().catch(() => {
          // Collection might not exist
        });
      }

      // Insert documents
      const result = await collection.insertMany(documents);

      logger.info('Data imported', {
        collection: options.collection,
        count: result.insertedCount,
      });

      console.log(chalk.green(`\n✓ Imported ${result.insertedCount} documents\n`));

      return result.insertedCount;
    } catch (error) {
      logger.error('Import failed', { error });
      throw new Error(
        `Import failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Export data from collection
   */
  async export(options: ExportOptions): Promise<void> {
    try {
      const connection = this.getActiveConnection();
      const db = connection.client.db(connection.database);
      const collection = db.collection(options.collection);

      // Parse filter
      const filter = options.filter ? this.parseJSON(options.filter) : {};

      // Build query
      let cursor = collection.find(filter);

      if (options.limit) {
        cursor = cursor.limit(options.limit);
      }

      const documents = await cursor.toArray();

      // Export based on format
      const format = options.format || 'json';

      if (format === 'json') {
        writeFileSync(options.output, JSON.stringify(documents, null, 2), 'utf-8');
      } else {
        throw new Error('CSV export not yet implemented');
      }

      logger.info('Data exported', {
        collection: options.collection,
        count: documents.length,
        output: options.output,
      });

      console.log(chalk.green(`\n✓ Exported ${documents.length} documents to ${options.output}\n`));
    } catch (error) {
      logger.error('Export failed', { error });
      throw new Error(
        `Export failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Format and display results
   */
  formatResults(results: Document[], format: 'table' | 'json' = 'table'): void {
    if (results.length === 0) {
      console.log(chalk.yellow('\n⚠ No results found\n'));
      return;
    }

    if (format === 'json') {
      console.log('\n' + JSON.stringify(results, null, 2) + '\n');
      return;
    }

    // Table format
    const keys = Object.keys(results[0]);
    const table = new Table3({
      head: keys.map((k) => chalk.cyan(k)),
      style: { head: [], border: [] },
    });

    for (const row of results) {
      table.push(keys.map((k) => this.formatValue(row[k])));
    }

    console.log('\n' + table.toString() + '\n');
    console.log(chalk.gray(`${results.length} document(s) returned\n`));
  }

  /**
   * Format a value for display
   */
  private formatValue(value: any): string {
    if (value === null || value === undefined) {
      return chalk.gray('null');
    }

    if (value instanceof ObjectId) {
      return chalk.yellow(value.toString());
    }

    if (value instanceof Date) {
      return chalk.green(value.toISOString());
    }

    if (typeof value === 'object') {
      return JSON.stringify(value);
    }

    return String(value);
  }

  /**
   * Parse JSON with error handling
   */
  private parseJSON(json: string): any {
    try {
      // Replace single quotes with double quotes for convenience
      const normalized = json.replace(/'/g, '"');
      return JSON.parse(normalized);
    } catch (error) {
      throw new Error(`Invalid JSON: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * List all connections
   */
  listConnections(): MongoConnection[] {
    return Array.from(this.connections.values());
  }

  /**
   * Get connection stats
   */
  async getConnectionStats(name?: string): Promise<any> {
    try {
      const connName = name || this.activeConnection;
      if (!connName) {
        throw new Error('No active connection');
      }

      const connection = this.connections.get(connName);
      if (!connection) {
        throw new Error(`Connection not found: ${connName}`);
      }

      const db = connection.client.db('admin');
      const stats = await db.command({ serverStatus: 1 });

      return {
        name: connName,
        uptime: stats.uptime,
        connections: stats.connections,
        opcounters: stats.opcounters,
        memory: stats.mem,
      };
    } catch (error) {
      logger.error('Failed to get connection stats', { error });
      throw new Error(
        `Failed to get connection stats: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }
}
