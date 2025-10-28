/**
 * Enhanced Database Connection Manager
 * Manages connections to PostgreSQL, MySQL, MongoDB, Redis, and SQLite
 * with connection pooling, health checking, and automatic reconnection
 */

import { EventEmitter } from 'eventemitter3';
import { StateManager } from '../core/state-manager';
import { Pool as PgPool, PoolConfig as PgPoolConfig, PoolClient } from 'pg';
import { createPool, PoolOptions as MySqlPoolOptions, Pool as MySqlPool } from 'mysql2/promise';
import { MongoClient, MongoClientOptions, Db } from 'mongodb';
import Redis, { RedisOptions } from 'ioredis';
import sqlite3 from 'sqlite3';
import { createLogger } from '../core/logger';
import { parse as parseUrl } from 'url';

const logger = createLogger('DatabaseManager');

/**
 * Database types
 */
export enum DatabaseType {
  POSTGRESQL = 'postgresql',
  MYSQL = 'mysql',
  SQLITE = 'sqlite',
  MONGODB = 'mongodb',
  REDIS = 'redis'
}

/**
 * Connection configuration
 */
export interface ConnectionConfig {
  name: string;
  type: DatabaseType;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  connectionString?: string;
  ssl?: boolean;
  poolSize?: number;
  options?: Record<string, any>;
}

/**
 * Connection info
 */
export interface ConnectionInfo {
  name: string;
  type: DatabaseType;
  database?: string;
  host?: string;
  port?: number;
  isActive: boolean;
  isHealthy: boolean;
  createdAt: number;
  lastHealthCheck?: number;
}

/**
 * Connection instance
 */
export interface Connection {
  config: ConnectionConfig;
  client: PgPool | MySqlPool | MongoClient | Redis | sqlite3.Database;
  type: DatabaseType;
  isConnected: boolean;
  lastHealthCheck?: number;
  healthCheckInterval?: NodeJS.Timeout;
}

/**
 * Health check result
 */
export interface HealthCheckResult {
  healthy: boolean;
  latency: number;
  error?: string;
  timestamp: number;
}

/**
 * Connection manager events
 */
export interface ConnectionManagerEvents {
  connected: (name: string) => void;
  disconnected: (name: string) => void;
  activeChanged: (name: string) => void;
  healthCheckFailed: (name: string, error: Error) => void;
  reconnecting: (name: string) => void;
  reconnected: (name: string) => void;
  error: (error: Error) => void;
}

/**
 * Enhanced Database Connection Manager
 */
export class DatabaseConnectionManager extends EventEmitter<ConnectionManagerEvents> {
  private connections = new Map<string, Connection>();
  private activeConnection: string | null = null;
  private healthCheckIntervalMs = 30000; // 30 seconds

  constructor(private stateManager: StateManager) {
    super();
    this.loadConnectionsFromState();
  }

  /**
   * Parse connection string to config
   */
  static parseConnectionString(connectionString: string): Partial<ConnectionConfig> {
    try {
      const parsed = parseUrl(connectionString);
      const protocol = parsed.protocol?.replace(':', '');

      let type: DatabaseType;
      switch (protocol) {
        case 'postgresql':
        case 'postgres':
          type = DatabaseType.POSTGRESQL;
          break;
        case 'mysql':
          type = DatabaseType.MYSQL;
          break;
        case 'mongodb':
        case 'mongodb+srv':
          type = DatabaseType.MONGODB;
          break;
        case 'redis':
        case 'rediss':
          type = DatabaseType.REDIS;
          break;
        case 'sqlite':
          type = DatabaseType.SQLITE;
          break;
        default:
          throw new Error(`Unsupported protocol: ${protocol}`);
      }

      const config: Partial<ConnectionConfig> = {
        type,
        connectionString,
        host: parsed.hostname || undefined,
        port: parsed.port ? parseInt(parsed.port) : undefined,
      };

      // Extract auth
      if (parsed.auth) {
        const [username, password] = parsed.auth.split(':');
        config.username = username;
        config.password = password;
      }

      // Extract database from pathname
      if (parsed.pathname) {
        const database = parsed.pathname.replace(/^\//, '');
        if (database) {
          config.database = database;
        }
      }

      // Check for SSL
      if (parsed.query?.includes('ssl=true') || protocol?.includes('rediss') || protocol?.includes('mongodb+srv')) {
        config.ssl = true;
      }

      return config;
    } catch (error) {
      throw new Error(`Invalid connection string: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Connect to database
   */
  async connect(config: ConnectionConfig): Promise<Connection> {
    try {
      logger.info('Connecting to database', { name: config.name, type: config.type });

      // Check if connection already exists
      if (this.connections.has(config.name)) {
        logger.info('Disconnecting existing connection', { name: config.name });
        await this.disconnect(config.name);
      }

      let client: PgPool | MySqlPool | MongoClient | Redis | sqlite3.Database;

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

        case DatabaseType.REDIS:
          client = await this.connectRedis(config);
          break;

        default:
          throw new Error(`Unsupported database type: ${config.type}`);
      }

      const connection: Connection = {
        config,
        client,
        type: config.type,
        isConnected: true,
        lastHealthCheck: Date.now()
      };

      this.connections.set(config.name, connection);

      // Save to state (without password)
      this.saveConnectionToState(config);

      // Set as active if first connection
      if (this.connections.size === 1) {
        this.activeConnection = config.name;
      }

      // Start health checks
      this.startHealthChecks(config.name);

      this.emit('connected', config.name);
      logger.info('Connected successfully', { name: config.name });

      return connection;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      logger.error('Connection failed', { name: config.name, error: err.message });
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
          max: config.poolSize || 10,
          idleTimeoutMillis: 30000,
          connectionTimeoutMillis: 5000
        };

    const pool = new PgPool(poolConfig);

    // Test connection
    const client = await pool.connect();
    await client.query('SELECT 1');
    client.release();

    // Handle errors
    pool.on('error', (err) => {
      logger.error('PostgreSQL pool error', err);
      this.emit('error', err);
    });

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
          connectionLimit: config.poolSize || 10,
          waitForConnections: true,
          queueLimit: 0
        };

    const pool = createPool(poolConfig);

    // Test connection
    const conn = await pool.getConnection();
    await conn.query('SELECT 1');
    conn.release();

    // Note: MySQL pool error handling is managed internally by mysql2

    return pool;
  }

  /**
   * Connect to SQLite
   */
  private async connectSQLite(config: ConnectionConfig): Promise<sqlite3.Database> {
    return new Promise((resolve, reject) => {
      const dbPath = config.database || config.connectionString || ':memory:';
      const db = new sqlite3.Database(dbPath, (err) => {
        if (err) {
          reject(err);
        } else {
          // Test connection
          db.get('SELECT 1', (err) => {
            if (err) {
              reject(err);
            } else {
              resolve(db);
            }
          });
        }
      });
    });
  }

  /**
   * Connect to MongoDB
   */
  private async connectMongoDB(config: ConnectionConfig): Promise<MongoClient> {
    const uri = config.connectionString ||
      `mongodb://${config.host || 'localhost'}:${config.port || 27017}`;

    const options: MongoClientOptions = {
      maxPoolSize: config.poolSize || 10,
      minPoolSize: 2,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
      ...(config.ssl && { tls: true }),
      ...(config.options || {})
    };

    if (config.username && config.password) {
      options.auth = {
        username: config.username,
        password: config.password
      };
    }

    const client = new MongoClient(uri, options);
    await client.connect();

    // Test connection
    await client.db('admin').admin().ping();

    return client;
  }

  /**
   * Connect to Redis
   */
  private async connectRedis(config: ConnectionConfig): Promise<Redis> {
    const options: RedisOptions = config.connectionString
      ? { connectionName: config.name }
      : {
          host: config.host || 'localhost',
          port: config.port || 6379,
          password: config.password,
          db: config.database ? parseInt(config.database) : 0,
          retryStrategy: (times) => {
            const delay = Math.min(times * 50, 2000);
            return delay;
          },
          maxRetriesPerRequest: 3,
          enableReadyCheck: true,
          ...(config.ssl && { tls: {} }),
          ...(config.options || {})
        };

    const redis = config.connectionString
      ? new Redis(config.connectionString, options)
      : new Redis(options);

    // Wait for ready
    await new Promise<void>((resolve, reject) => {
      redis.once('ready', () => resolve());
      redis.once('error', (err) => reject(err));
    });

    // Test connection
    await redis.ping();

    // Handle errors
    redis.on('error', (err) => {
      logger.error('Redis client error', err);
      this.emit('error', err);
    });

    redis.on('reconnecting', () => {
      logger.info('Redis reconnecting');
      const connName = this.findConnectionNameByClient(redis);
      if (connName) {
        this.emit('reconnecting', connName);
      }
    });

    return redis;
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
      logger.info('Disconnecting from database', { name });

      // Stop health checks
      if (connection.healthCheckInterval) {
        clearInterval(connection.healthCheckInterval);
      }

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

        case DatabaseType.REDIS:
          await (connection.client as Redis).quit();
          break;
      }

      this.connections.delete(name);

      // Clear active if this was active
      if (this.activeConnection === name) {
        this.activeConnection = null;
        // Set next available as active
        const nextConnection = Array.from(this.connections.keys())[0];
        if (nextConnection) {
          this.activeConnection = nextConnection;
        }
      }

      this.emit('disconnected', name);
      logger.info('Disconnected successfully', { name });
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      logger.error('Disconnect failed', { name, error: err.message });
      this.emit('error', err);
      throw new Error(`Failed to disconnect from ${name}: ${err.message}`);
    }
  }

  /**
   * Health check for a connection
   */
  async healthCheck(name: string): Promise<HealthCheckResult> {
    const connection = this.connections.get(name);

    if (!connection) {
      return {
        healthy: false,
        latency: 0,
        error: 'Connection not found',
        timestamp: Date.now()
      };
    }

    const startTime = Date.now();

    try {
      switch (connection.type) {
        case DatabaseType.POSTGRESQL:
          const pgClient = await (connection.client as PgPool).connect();
          await pgClient.query('SELECT 1');
          pgClient.release();
          break;

        case DatabaseType.MYSQL:
          const mysqlConn = await (connection.client as MySqlPool).getConnection();
          await mysqlConn.query('SELECT 1');
          mysqlConn.release();
          break;

        case DatabaseType.SQLITE:
          await new Promise<void>((resolve, reject) => {
            (connection.client as sqlite3.Database).get('SELECT 1', (err) => {
              if (err) reject(err);
              else resolve();
            });
          });
          break;

        case DatabaseType.MONGODB:
          await (connection.client as MongoClient).db('admin').admin().ping();
          break;

        case DatabaseType.REDIS:
          await (connection.client as Redis).ping();
          break;
      }

      const latency = Date.now() - startTime;
      connection.lastHealthCheck = Date.now();

      return {
        healthy: true,
        latency,
        timestamp: Date.now()
      };
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      logger.error('Health check failed', { name, error: err.message });
      this.emit('healthCheckFailed', name, err);

      return {
        healthy: false,
        latency: Date.now() - startTime,
        error: err.message,
        timestamp: Date.now()
      };
    }
  }

  /**
   * Start automatic health checks for a connection
   */
  private startHealthChecks(name: string): void {
    const connection = this.connections.get(name);
    if (!connection) return;

    connection.healthCheckInterval = setInterval(async () => {
      const result = await this.healthCheck(name);
      if (!result.healthy) {
        logger.warn('Health check failed, attempting reconnection', { name });
        // Attempt reconnection
        try {
          const config = connection.config;
          await this.disconnect(name);
          await this.connect(config);
          logger.info('Reconnection successful', { name });
          this.emit('reconnected', name);
        } catch (error) {
          logger.error('Reconnection failed', { name, error });
        }
      }
    }, this.healthCheckIntervalMs);
  }

  /**
   * Test connection without saving
   */
  async testConnection(config: ConnectionConfig): Promise<HealthCheckResult> {
    const testName = `__test_${Date.now()}__`;
    try {
      await this.connect({
        ...config,
        name: testName
      });

      const result = await this.healthCheck(testName);
      await this.disconnect(testName);

      return result;
    } catch (error) {
      return {
        healthy: false,
        latency: 0,
        error: error instanceof Error ? error.message : String(error),
        timestamp: Date.now()
      };
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
      isHealthy: connection.lastHealthCheck ? (Date.now() - connection.lastHealthCheck < 60000) : false,
      createdAt: Date.now(),
      lastHealthCheck: connection.lastHealthCheck
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
    logger.info('Active connection changed', { name });
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
        throw new Error('Use MongoDB-specific methods for querying');

      case DatabaseType.REDIS:
        throw new Error('Use Redis-specific methods for commands');

      default:
        throw new Error(`Unsupported database type: ${connection.type}`);
    }
  }

  /**
   * Load connections from config file
   */
  async loadFromConfig(configPath: string): Promise<void> {
    // TODO: Implement YAML config file loading
    logger.info('Loading connections from config', { configPath });
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
    try {
      this.stateManager.findByMetadata('type', 'database-connection');
      // Connections will be reconnected manually by user
    } catch (error) {
      logger.warn('Failed to load connections from state', { error: String(error) });
    }
  }

  /**
   * Find connection name by client instance
   */
  private findConnectionNameByClient(client: any): string | null {
    for (const [name, connection] of this.connections.entries()) {
      if (connection.client === client) {
        return name;
      }
    }
    return null;
  }

  /**
   * Disconnect all connections
   */
  async disconnectAll(): Promise<void> {
    const names = Array.from(this.connections.keys());

    for (const name of names) {
      await this.disconnect(name);
    }

    logger.info('All connections disconnected');
  }

  /**
   * Get connection statistics
   */
  getStatistics(): {
    totalConnections: number;
    activeConnection: string | null;
    connectionsByType: Record<string, number>;
    healthyConnections: number;
  } {
    const connectionsByType: Record<string, number> = {};
    let healthyConnections = 0;

    for (const connection of this.connections.values()) {
      connectionsByType[connection.type] = (connectionsByType[connection.type] || 0) + 1;

      if (connection.lastHealthCheck && (Date.now() - connection.lastHealthCheck < 60000)) {
        healthyConnections++;
      }
    }

    return {
      totalConnections: this.connections.size,
      activeConnection: this.activeConnection,
      connectionsByType,
      healthyConnections
    };
  }
}
