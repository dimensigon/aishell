/**
 * Database Connection Manager
 * Manages connections to multiple database types (PostgreSQL, MySQL, SQLite, MongoDB)
 */

import { EventEmitter } from 'eventemitter3';
import { StateManager } from '../core/state-manager';
import { Pool as PgPool, PoolConfig as PgPoolConfig } from 'pg';
import { createPool, PoolOptions as MySqlPoolOptions } from 'mysql2/promise';
import type { Pool as MySqlPool } from 'mysql2/promise';
import { MongoClient, MongoClientOptions } from 'mongodb';
import sqlite3 from 'sqlite3';

/**
 * Database types
 */
export enum DatabaseType {
  POSTGRESQL = 'postgresql',
  MYSQL = 'mysql',
  SQLITE = 'sqlite',
  MONGODB = 'mongodb'
}

/**
 * Connection configuration
 */
export interface ConnectionConfig {
  name: string;
  type: DatabaseType;
  host?: string;
  port?: number;
  database: string;
  username?: string;
  password?: string;
  connectionString?: string;
  ssl?: boolean;
  poolSize?: number;
}

/**
 * Connection info
 */
export interface ConnectionInfo {
  name: string;
  type: DatabaseType;
  database: string;
  host?: string;
  port?: number;
  isActive: boolean;
  createdAt: number;
}

/**
 * Connection instance
 */
export interface Connection {
  config: ConnectionConfig;
  client: any;
  type: DatabaseType;
  isConnected: boolean;
}

/**
 * Connection manager events
 */
export interface ConnectionManagerEvents {
  connected: (name: string) => void;
  disconnected: (name: string) => void;
  activeChanged: (name: string) => void;
  error: (error: Error) => void;
}

/**
 * Database Connection Manager
 */
export class DatabaseConnectionManager extends EventEmitter<ConnectionManagerEvents> {
  private connections = new Map<string, Connection>();
  private activeConnection: string | null = null;

  constructor(private stateManager: StateManager) {
    super();
    this.loadConnectionsFromState();
  }

  /**
   * Connect to database
   */
  async connect(config: ConnectionConfig): Promise<Connection> {
    try {
      // Check if connection already exists
      if (this.connections.has(config.name)) {
        await this.disconnect(config.name);
      }

      let client: any;

      switch (config.type) {
        case DatabaseType.POSTGRESQL:
          client = await this.connectPostgreSQL(config);
          break;

        case DatabaseType.MYSQL:
          client = await this.connectMySQL(config);
          break;

        case DatabaseType.SQLITE:
          client = await this.connectSQLite(config);
          break;

        case DatabaseType.MONGODB:
          client = await this.connectMongoDB(config);
          break;

        default:
          throw new Error(`Unsupported database type: ${config.type}`);
      }

      const connection: Connection = {
        config,
        client,
        type: config.type,
        isConnected: true
      };

      this.connections.set(config.name, connection);

      // Save to state
      this.saveConnectionToState(config);

      // Set as active if first connection
      if (this.connections.size === 1) {
        this.activeConnection = config.name;
      }

      this.emit('connected', config.name);

      return connection;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.emit('error', err);
      throw new Error(`Failed to connect to ${config.type}: ${err.message}`);
    }
  }

  /**
   * Connect to PostgreSQL
   */
  private async connectPostgreSQL(config: ConnectionConfig): Promise<PgPool> {
    const poolConfig: PgPoolConfig = config.connectionString
      ? { connectionString: config.connectionString }
      : {
          host: config.host,
          port: config.port || 5432,
          database: config.database,
          user: config.username,
          password: config.password,
          ssl: config.ssl ? { rejectUnauthorized: false } : undefined,
          max: config.poolSize || 10
        };

    const pool = new PgPool(poolConfig);

    // Test connection
    const client = await pool.connect();
    client.release();

    return pool;
  }

  /**
   * Connect to MySQL
   */
  private async connectMySQL(config: ConnectionConfig): Promise<MySqlPool> {
    const poolConfig: MySqlPoolOptions = config.connectionString
      ? { uri: config.connectionString }
      : {
          host: config.host,
          port: config.port || 3306,
          database: config.database,
          user: config.username,
          password: config.password,
          ssl: config.ssl ? {} : undefined,
          connectionLimit: config.poolSize || 10
        };

    const pool = createPool(poolConfig);

    // Test connection
    const conn = await pool.getConnection();
    conn.release();

    return pool;
  }

  /**
   * Connect to SQLite
   */
  private async connectSQLite(config: ConnectionConfig): Promise<sqlite3.Database> {
    return new Promise((resolve, reject) => {
      const db = new sqlite3.Database(config.database, (err) => {
        if (err) {
          reject(err);
        } else {
          resolve(db);
        }
      });
    });
  }

  /**
   * Connect to MongoDB
   */
  private async connectMongoDB(config: ConnectionConfig): Promise<MongoClient> {
    const uri = config.connectionString || `mongodb://${config.host}:${config.port || 27017}`;

    const options: MongoClientOptions = {
      maxPoolSize: config.poolSize || 10,
      ssl: config.ssl
    };

    if (config.username && config.password) {
      options.auth = {
        username: config.username,
        password: config.password
      };
    }

    const client = new MongoClient(uri, options);
    await client.connect();

    return client;
  }

  /**
   * Disconnect from database
   */
  async disconnect(name: string): Promise<void> {
    const connection = this.connections.get(name);

    if (!connection) {
      return;
    }

    try {
      switch (connection.type) {
        case DatabaseType.POSTGRESQL:
          await (connection.client as PgPool).end();
          break;

        case DatabaseType.MYSQL:
          await (connection.client as MySqlPool).end();
          break;

        case DatabaseType.SQLITE:
          await new Promise<void>((resolve, reject) => {
            (connection.client as sqlite3.Database).close((err) => {
              if (err) reject(err);
              else resolve();
            });
          });
          break;

        case DatabaseType.MONGODB:
          await (connection.client as MongoClient).close();
          break;
      }

      this.connections.delete(name);

      // Clear active if this was active
      if (this.activeConnection === name) {
        this.activeConnection = null;
      }

      this.emit('disconnected', name);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.emit('error', err);
      throw new Error(`Failed to disconnect from ${name}: ${err.message}`);
    }
  }

  /**
   * List all connections
   */
  listConnections(): ConnectionInfo[] {
    return Array.from(this.connections.entries()).map(([name, connection]) => ({
      name,
      type: connection.type,
      database: connection.config.database,
      host: connection.config.host,
      port: connection.config.port,
      isActive: name === this.activeConnection,
      createdAt: Date.now()
    }));
  }

  /**
   * Switch active connection
   */
  async switchActive(name: string): Promise<void> {
    if (!this.connections.has(name)) {
      throw new Error(`Connection not found: ${name}`);
    }

    this.activeConnection = name;
    this.emit('activeChanged', name);
  }

  /**
   * Get active connection
   */
  getActive(): Connection | null {
    if (!this.activeConnection) {
      return null;
    }

    return this.connections.get(this.activeConnection) || null;
  }

  /**
   * Get connection by name
   */
  getConnection(name: string): Connection | undefined {
    return this.connections.get(name);
  }

  /**
   * Test connection
   */
  async testConnection(config: ConnectionConfig): Promise<boolean> {
    try {
      await this.connect({
        ...config,
        name: '__test__'
      });

      await this.disconnect('__test__');
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Execute query on active connection
   */
  async executeQuery(sql: string, params?: any[]): Promise<any[]> {
    const connection = this.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    switch (connection.type) {
      case DatabaseType.POSTGRESQL:
        const pgResult = await (connection.client as PgPool).query(sql, params);
        return pgResult.rows;

      case DatabaseType.MYSQL:
        const [mysqlRows] = await (connection.client as MySqlPool).query(sql, params);
        return mysqlRows as any[];

      case DatabaseType.SQLITE:
        return new Promise((resolve, reject) => {
          (connection.client as sqlite3.Database).all(sql, params || [], (err, rows) => {
            if (err) reject(err);
            else resolve(rows);
          });
        });

      case DatabaseType.MONGODB:
        // MongoDB uses different query syntax
        throw new Error('Use MongoDB-specific methods for querying');

      default:
        throw new Error(`Unsupported database type: ${connection.type}`);
    }
  }

  /**
   * Save connection config to state
   */
  private saveConnectionToState(config: ConnectionConfig): void {
    const sanitized = {
      ...config,
      password: undefined // Don't store password
    };

    this.stateManager.set(`connection:${config.name}`, sanitized, {
      metadata: { type: 'database-connection' }
    });
  }

  /**
   * Load connections from state
   */
  private loadConnectionsFromState(): void {
    this.stateManager.findByMetadata('type', 'database-connection');

    // Connections will be reconnected manually by user
    // We just store the config for reference
  }

  /**
   * Disconnect all connections
   */
  async disconnectAll(): Promise<void> {
    const names = Array.from(this.connections.keys());

    for (const name of names) {
      await this.disconnect(name);
    }
  }

  /**
   * Get connection statistics
   */
  getStatistics(): {
    totalConnections: number;
    activeConnection: string | null;
    connectionsByType: Record<string, number>;
  } {
    const connectionsByType: Record<string, number> = {};

    for (const connection of this.connections.values()) {
      connectionsByType[connection.type] = (connectionsByType[connection.type] || 0) + 1;
    }

    return {
      totalConnections: this.connections.size,
      activeConnection: this.activeConnection,
      connectionsByType
    };
  }
}
