/**
 * Centralized Test Database Configuration
 *
 * This file provides a single source of truth for all database connection
 * configurations used in integration tests. It uses environment variables
 * with sensible defaults matching the Docker Compose test environment.
 *
 * Usage:
 *   import { testDatabaseConfig } from '../config/databases.test';
 *   const pool = new Pool(testDatabaseConfig.postgres);
 */

export interface DatabaseConfig {
  postgres: {
    host: string;
    port: number;
    database: string;
    user: string;
    password: string;
    max?: number;
    idleTimeoutMillis?: number;
    connectionTimeoutMillis?: number;
  };
  mongodb: {
    url: string;
    host?: string;
    port?: number;
    database?: string;
    username?: string;
    password?: string;
  };
  mysql: {
    host: string;
    port: number;
    database: string;
    user: string;
    password: string;
    multipleStatements?: boolean;
    waitForConnections?: boolean;
    connectionLimit?: number;
    queueLimit?: number;
  };
  redis: {
    host: string;
    port: number;
    password?: string;
    db?: number;
    maxRetriesPerRequest?: number;
    retryStrategy?: (times: number) => number | void;
    enableOfflineQueue?: boolean;
    lazyConnect?: boolean;
  };
  oracle?: {
    user: string;
    password: string;
    connectString: string;
    privilege?: number;
  };
}

/**
 * Test Database Configuration
 *
 * Environment variables override defaults:
 * - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
 * - MONGO_HOST, MONGO_PORT, MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE
 * - MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
 * - REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
 * - ORACLE_HOST, ORACLE_PORT, ORACLE_USER, ORACLE_PASSWORD, ORACLE_SERVICE
 */
export const testDatabaseConfig: DatabaseConfig = {
  // PostgreSQL Configuration
  postgres: {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    database: process.env.POSTGRES_DB || 'postgres',
    user: process.env.POSTGRES_USER || 'postgres',
    password: process.env.POSTGRES_PASSWORD || 'MyPostgresPass123',
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
  },

  // MongoDB Configuration
  mongodb: {
    url: process.env.MONGO_URL ||
         `mongodb://${process.env.MONGO_USERNAME || 'admin'}:${process.env.MONGO_PASSWORD || 'MyMongoPass123'}@${process.env.MONGO_HOST || 'localhost'}:${process.env.MONGO_PORT || '27017'}/${process.env.MONGO_DATABASE || 'test_integration_db'}?authSource=admin`,
    host: process.env.MONGO_HOST || 'localhost',
    port: parseInt(process.env.MONGO_PORT || '27017'),
    database: process.env.MONGO_DATABASE || 'test_integration_db',
    username: process.env.MONGO_USERNAME || 'admin',
    password: process.env.MONGO_PASSWORD || 'MyMongoPass123',
  },

  // MySQL Configuration
  mysql: {
    host: process.env.MYSQL_HOST || 'localhost',
    port: parseInt(process.env.MYSQL_PORT || '3306'),
    database: process.env.MYSQL_DATABASE || 'test_db',
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || 'MyMySQLPass123',
    multipleStatements: true,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0,
  },

  // Redis Configuration
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
    password: process.env.REDIS_PASSWORD,
    db: parseInt(process.env.REDIS_DB || '15'), // Use dedicated test DB
    maxRetriesPerRequest: 3,
    retryStrategy: (times: number) => {
      const delay = Math.min(times * 50, 2000);
      return delay;
    },
    enableOfflineQueue: false,
    lazyConnect: true,
  },

  // Oracle Configuration (optional)
  oracle: process.env.ORACLE_HOST ? {
    user: process.env.ORACLE_USER || 'SYS',
    password: process.env.ORACLE_PASSWORD || 'MyOraclePass123',
    connectString: `${process.env.ORACLE_HOST || 'localhost'}:${process.env.ORACLE_PORT || '1521'}/${process.env.ORACLE_SERVICE || 'FREEPDB1'}`,
    privilege: 2, // SYSDBA
  } : undefined,
};

/**
 * Check if a database is available for testing
 */
export async function isDatabaseAvailable(dbType: keyof DatabaseConfig): Promise<boolean> {
  try {
    switch (dbType) {
      case 'postgres': {
        const { Pool } = await import('pg');
        const pool = new Pool(testDatabaseConfig.postgres);
        try {
          await pool.query('SELECT 1');
          await pool.end();
          return true;
        } catch {
          await pool.end();
          return false;
        }
      }

      case 'mongodb': {
        const { MongoClient } = await import('mongodb');
        const client = new MongoClient(testDatabaseConfig.mongodb.url, {
          serverSelectionTimeoutMS: 2000,
        });
        try {
          await client.connect();
          await client.close();
          return true;
        } catch {
          await client.close();
          return false;
        }
      }

      case 'mysql': {
        const mysql = await import('mysql2/promise');
        try {
          const connection = await mysql.createConnection(testDatabaseConfig.mysql);
          await connection.end();
          return true;
        } catch {
          return false;
        }
      }

      case 'redis': {
        const Redis = (await import('ioredis')).default;
        const client = new Redis(testDatabaseConfig.redis);

        // Add error event listener to prevent unhandled error warnings
        const errorHandler = () => {
          // Suppress connection errors during availability check
        };
        client.on('error', errorHandler);

        try {
          await client.connect();
          await client.ping();
          client.off('error', errorHandler);
          await client.quit();
          return true;
        } catch {
          client.off('error', errorHandler);
          await client.quit();
          return false;
        }
      }

      default:
        return false;
    }
  } catch {
    return false;
  }
}

/**
 * Wait for database to be ready (with retry logic)
 */
export async function waitForDatabase(
  dbType: keyof DatabaseConfig,
  maxRetries: number = 30,
  delayMs: number = 1000
): Promise<boolean> {
  for (let i = 0; i < maxRetries; i++) {
    if (await isDatabaseAvailable(dbType)) {
      return true;
    }
    await new Promise(resolve => setTimeout(resolve, delayMs));
  }
  return false;
}

export default testDatabaseConfig;
