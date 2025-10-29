/**
 * Redis CLI - Comprehensive Redis operations
 * Exposes Redis operations via CLI commands with full data type support
 */

import chalk from 'chalk';
import Table from 'cli-table3';
import Redis, { RedisOptions, Cluster } from 'ioredis';
import { createLogger } from '../core/logger';
import * as fs from 'fs/promises';
import * as path from 'path';

const logger = createLogger('RedisCLI');

/**
 * Redis connection configuration
 */
export interface RedisConnectionConfig {
  name?: string;
  db?: number;
  tls?: boolean;
  cluster?: boolean;
  retryStrategy?: (times: number) => number | void;
}

/**
 * Connection info
 */
export interface ConnectionInfo {
  name: string;
  host: string;
  port: number;
  db: number;
  status: 'connected' | 'disconnected' | 'connecting';
  cluster: boolean;
  client: Redis | Cluster;
}

/**
 * Key-value result
 */
export interface KeyValueResult {
  key: string;
  value: string | null;
  type?: string;
  ttl?: number;
  exists: boolean;
}

/**
 * Set operation result
 */
export interface SetResult {
  success: boolean;
  key: string;
  message: string;
}

/**
 * Keys result
 */
export interface KeysResult {
  keys: string[];
  count: number;
  pattern: string;
  cursor?: string;
}

/**
 * Info result
 */
export interface InfoResult {
  section: string;
  data: Record<string, any>;
  raw?: string;
}

/**
 * Flush result
 */
export interface FlushResult {
  success: boolean;
  message: string;
  deletedKeys?: number;
}

/**
 * TTL result
 */
export interface TTLResult {
  key: string;
  ttl: number;
  hasExpiry: boolean;
  message: string;
}

/**
 * Monitor options
 */
export interface MonitorOptions {
  connection?: string;
  duration?: number;
  filter?: string;
  output?: string;
}

/**
 * Redis CLI - Main class for Redis operations
 */
export class RedisCLI {
  private logger = createLogger('RedisCLI');
  private connections = new Map<string, ConnectionInfo>();
  private activeConnection: string = 'default';

  /**
   * Connect to Redis server
   */
  async connect(connectionString: string, config?: RedisConnectionConfig): Promise<void> {
    const name = config?.name || 'default';

    try {
      logger.info('Connecting to Redis', { name, connectionString });

      // Parse connection string
      const url = new URL(connectionString);
      const host = url.hostname;
      const port = parseInt(url.port) || 6379;
      const password = url.password || undefined;
      const username = url.username || undefined;
      const db = config?.db || (url.pathname ? parseInt(url.pathname.substring(1)) : 0);

      // Build Redis options
      const options: RedisOptions = {
        host,
        port,
        db,
        password,
        username,
        retryStrategy: config?.retryStrategy || ((times: number) => {
          const delay = Math.min(times * 50, 2000);
          return delay;
        }),
        lazyConnect: false,
        enableReadyCheck: true,
        maxRetriesPerRequest: 3
      };

      // Add TLS if needed
      if (config?.tls || url.protocol === 'rediss:') {
        options.tls = {};
      }

      // Create client
      let client: Redis | Cluster;

      if (config?.cluster) {
        // Redis Cluster
        client = new Redis.Cluster([{ host, port }], {
          redisOptions: options,
          clusterRetryStrategy: (times: number) => {
            const delay = Math.min(times * 50, 2000);
            return delay;
          }
        });
      } else {
        // Standalone Redis
        client = new Redis(options);
      }

      // Wait for connection
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, 10000);

        client.on('ready', () => {
          clearTimeout(timeout);
          resolve();
        });

        client.on('error', (error) => {
          clearTimeout(timeout);
          reject(error);
        });
      });

      // Store connection
      const connectionInfo: ConnectionInfo = {
        name,
        host,
        port,
        db,
        status: 'connected',
        cluster: config?.cluster || false,
        client
      };

      this.connections.set(name, connectionInfo);
      this.activeConnection = name;

      logger.info('Connected to Redis', { name, host, port, db });
    } catch (error) {
      logger.error('Connection failed', error);
      throw error;
    }
  }

  /**
   * Disconnect from Redis
   */
  async disconnect(name?: string): Promise<void> {
    const connectionName = name || this.activeConnection;
    const connection = this.connections.get(connectionName);

    if (!connection) {
      throw new Error(`Connection not found: ${connectionName}`);
    }

    try {
      await connection.client.quit();
      connection.status = 'disconnected';
      this.connections.delete(connectionName);

      // If active connection was removed, switch to another
      if (this.activeConnection === connectionName) {
        const remaining = Array.from(this.connections.keys());
        this.activeConnection = remaining.length > 0 ? remaining[0] : 'default';
      }

      logger.info('Disconnected from Redis', { name: connectionName });
    } catch (error) {
      logger.error('Disconnection failed', error);
      throw error;
    }
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
   * Get active client
   */
  private getClient(connectionName?: string): Redis {
    const name = connectionName || this.activeConnection;
    const connection = this.connections.get(name);

    if (!connection) {
      throw new Error(`No active connection. Use 'redis connect' first.`);
    }

    if (connection.status !== 'connected') {
      throw new Error(`Connection not ready: ${name}`);
    }

    // Return client (handle both standalone and cluster)
    if (connection.cluster) {
      // For cluster, we need to get a node client
      return (connection.client as any) as Redis;
    }

    return connection.client as Redis;
  }

  /**
   * GET command
   */
  async get(key: string, options?: { connection?: string; showType?: boolean }): Promise<KeyValueResult> {
    try {
      const client = this.getClient(options?.connection);

      // Get value
      const value = await client.get(key);
      const exists = value !== null;

      // Get type if requested
      let type: string | undefined;
      let ttl: number | undefined;

      if (options?.showType && exists) {
        type = await client.type(key);
        ttl = await client.ttl(key);
      }

      return {
        key,
        value,
        type,
        ttl,
        exists
      };
    } catch (error) {
      logger.error('GET failed', error);
      throw error;
    }
  }

  /**
   * SET command
   */
  async set(
    key: string,
    value: string,
    options?: {
      connection?: string;
      ex?: number;
      px?: number;
      nx?: boolean;
      xx?: boolean;
      keepttl?: boolean;
    }
  ): Promise<SetResult> {
    try {
      const client = this.getClient(options?.connection);

      // Build SET arguments
      const args: any[] = [key, value];

      if (options?.ex) {
        args.push('EX', options.ex);
      }
      if (options?.px) {
        args.push('PX', options.px);
      }
      if (options?.nx) {
        args.push('NX');
      }
      if (options?.xx) {
        args.push('XX');
      }
      if (options?.keepttl) {
        args.push('KEEPTTL');
      }

      const result = await client.call('SET', ...args);

      const success = result === 'OK' || result === null;

      return {
        success,
        key,
        message: success
          ? options?.nx
            ? 'Key set (if not exists)'
            : options?.xx
            ? 'Key updated (if exists)'
            : 'Key set successfully'
          : 'Key not set (condition not met)'
      };
    } catch (error) {
      logger.error('SET failed', error);
      throw error;
    }
  }

  /**
   * KEYS command
   */
  async keys(
    pattern: string,
    options?: { connection?: string; limit?: number; useScan?: boolean }
  ): Promise<KeysResult> {
    try {
      const client = this.getClient(options?.connection);

      let keys: string[];

      if (options?.useScan) {
        // Use SCAN for safer iteration
        keys = [];
        let cursor = '0';
        let iterations = 0;
        const maxIterations = 1000;

        do {
          const result = await client.scan(
            cursor,
            'MATCH',
            pattern,
            'COUNT',
            options?.limit || 100
          );
          cursor = result[0];
          keys.push(...result[1]);

          iterations++;
          if (iterations >= maxIterations) {
            logger.warn('SCAN max iterations reached', { iterations });
            break;
          }

          if (options?.limit && keys.length >= options.limit) {
            keys = keys.slice(0, options.limit);
            break;
          }
        } while (cursor !== '0');
      } else {
        // Use KEYS (not recommended for production)
        keys = await client.keys(pattern);

        if (options?.limit) {
          keys = keys.slice(0, options.limit);
        }
      }

      return {
        keys,
        count: keys.length,
        pattern,
        cursor: options?.useScan ? 'scan' : undefined
      };
    } catch (error) {
      logger.error('KEYS failed', error);
      throw error;
    }
  }

  /**
   * INFO command
   */
  async info(section?: string, options?: { connection?: string }): Promise<InfoResult> {
    try {
      const client = this.getClient(options?.connection);

      const raw = section ? await client.info(section) : await client.info();

      // Parse INFO response
      const data: Record<string, any> = {};
      let currentSection = 'default';

      raw.split('\r\n').forEach((line) => {
        if (line.startsWith('#')) {
          currentSection = line.substring(2).trim();
          data[currentSection] = {};
        } else if (line.includes(':')) {
          const [key, value] = line.split(':');
          if (!data[currentSection]) {
            data[currentSection] = {};
          }
          data[currentSection][key] = value;
        }
      });

      return {
        section: section || 'all',
        data,
        raw
      };
    } catch (error) {
      logger.error('INFO failed', error);
      throw error;
    }
  }

  /**
   * FLUSH command
   */
  async flush(options?: {
    connection?: string;
    db?: number;
    all?: boolean;
    async?: boolean;
  }): Promise<FlushResult> {
    try {
      const client = this.getClient(options?.connection);

      // Get current key count for reporting
      const keyCount = await client.dbsize();

      if (options?.all) {
        // FLUSHALL
        if (options?.async) {
          await client.flushall('ASYNC');
        } else {
          await client.flushall();
        }
      } else if (options?.db !== undefined) {
        // Select DB and flush
        await client.select(options.db);
        if (options?.async) {
          await client.flushdb('ASYNC');
        } else {
          await client.flushdb();
        }
      } else {
        // FLUSHDB current
        if (options?.async) {
          await client.flushdb('ASYNC');
        } else {
          await client.flushdb();
        }
      }

      return {
        success: true,
        message: options?.all
          ? 'All databases flushed'
          : options?.db !== undefined
          ? `Database ${options.db} flushed`
          : 'Current database flushed',
        deletedKeys: keyCount
      };
    } catch (error) {
      logger.error('FLUSH failed', error);
      throw error;
    }
  }

  /**
   * MONITOR command
   */
  async monitor(options: MonitorOptions): Promise<void> {
    try {
      const client = this.getClient(options.connection);

      console.log(chalk.blue('\n🔍 Monitoring Redis commands...\n'));
      console.log(chalk.dim('Press Ctrl+C to stop\n'));

      let outputStream: fs.FileHandle | null = null;

      // Open output file if specified
      if (options.output) {
        const outputPath = path.resolve(options.output);
        outputStream = await fs.open(outputPath, 'w');
        console.log(chalk.dim(`Logging to: ${outputPath}\n`));
      }

      // Start monitoring
      const monitorClient = await client.monitor();

      let startTime = Date.now();
      const duration = options.duration ? options.duration * 1000 : null;

      monitorClient.on('monitor', async (time, args, source, database) => {
        // Check duration
        if (duration && Date.now() - startTime >= duration) {
          await monitorClient.disconnect();
          if (outputStream) {
            await outputStream.close();
          }
          console.log(chalk.green('\n✓ Monitoring stopped (duration reached)\n'));
          return;
        }

        // Format command
        const command = args.join(' ');

        // Apply filter if specified
        if (options.filter) {
          const pattern = new RegExp(options.filter.replace(/\*/g, '.*'), 'i');
          if (!pattern.test(command)) {
            return;
          }
        }

        // Display and log
        const timestamp = new Date(time * 1000).toISOString();
        const line = `[${timestamp}] [DB ${database}] ${source}: ${command}`;

        console.log(chalk.dim(line));

        if (outputStream) {
          await outputStream.write(line + '\n');
        }
      });

      // Handle Ctrl+C
      process.on('SIGINT', async () => {
        await monitorClient.disconnect();
        if (outputStream) {
          await outputStream.close();
        }
        console.log(chalk.green('\n✓ Monitoring stopped\n'));
        process.exit(0);
      });

      // If duration is set, auto-stop
      if (duration) {
        setTimeout(async () => {
          await monitorClient.disconnect();
          if (outputStream) {
            await outputStream.close();
          }
          console.log(chalk.green('\n✓ Monitoring stopped (duration reached)\n'));
        }, duration);
      }
    } catch (error) {
      logger.error('MONITOR failed', error);
      throw error;
    }
  }

  /**
   * TTL command
   */
  async ttl(key: string, options?: { connection?: string }): Promise<TTLResult> {
    try {
      const client = this.getClient(options?.connection);
      const ttl = await client.ttl(key);

      return {
        key,
        ttl,
        hasExpiry: ttl > 0,
        message:
          ttl === -1
            ? 'No expiry set'
            : ttl === -2
            ? 'Key does not exist'
            : `Expires in ${ttl} seconds`
      };
    } catch (error) {
      logger.error('TTL failed', error);
      throw error;
    }
  }

  /**
   * EXPIRE command
   */
  async expire(
    key: string,
    seconds: number,
    options?: { connection?: string }
  ): Promise<SetResult> {
    try {
      const client = this.getClient(options?.connection);
      const result = await client.expire(key, seconds);

      return {
        success: result === 1,
        key,
        message: result === 1 ? `Expiry set to ${seconds} seconds` : 'Key does not exist'
      };
    } catch (error) {
      logger.error('EXPIRE failed', error);
      throw error;
    }
  }

  /**
   * DEL command
   */
  async del(keys: string[], options?: { connection?: string }): Promise<{ deletedCount: number }> {
    try {
      const client = this.getClient(options?.connection);
      const count = await client.del(...keys);

      return { deletedCount: count };
    } catch (error) {
      logger.error('DEL failed', error);
      throw error;
    }
  }

  /**
   * TYPE command
   */
  async type(key: string, options?: { connection?: string }): Promise<{ type: string }> {
    try {
      const client = this.getClient(options?.connection);
      const type = await client.type(key);

      return { type };
    } catch (error) {
      logger.error('TYPE failed', error);
      throw error;
    }
  }

  /**
   * Display value with formatting
   */
  displayValue(key: string, result: KeyValueResult): void {
    console.log('\n' + chalk.bold('Key:') + ' ' + chalk.cyan(key));

    if (!result.exists) {
      console.log(chalk.yellow('(key does not exist)\n'));
      return;
    }

    console.log(chalk.bold('Value:') + ' ' + result.value);

    if (result.type) {
      console.log(chalk.bold('Type:') + ' ' + chalk.magenta(result.type));
    }

    if (result.ttl !== undefined && result.ttl > 0) {
      console.log(chalk.bold('TTL:') + ' ' + chalk.green(`${result.ttl}s`));
    } else if (result.ttl === -1) {
      console.log(chalk.bold('TTL:') + ' ' + chalk.dim('No expiry'));
    }

    console.log('');
  }

  /**
   * Display keys as table
   */
  displayKeysTable(keys: string[]): void {
    if (keys.length === 0) {
      console.log(chalk.yellow('\nNo keys found\n'));
      return;
    }

    const table = new Table({
      head: [chalk.bold('#'), chalk.bold('Key')],
      colWidths: [8, 70]
    });

    keys.forEach((key, index) => {
      table.push([String(index + 1), key]);
    });

    console.log('\n' + table.toString());
    console.log(chalk.dim(`\nTotal: ${keys.length} key(s)\n`));
  }

  /**
   * Display keys as list
   */
  displayKeysList(keys: string[]): void {
    if (keys.length === 0) {
      console.log(chalk.yellow('\nNo keys found\n'));
      return;
    }

    console.log('');
    keys.forEach((key) => {
      console.log(chalk.cyan(`  ${key}`));
    });
    console.log(chalk.dim(`\nTotal: ${keys.length} key(s)\n`));
  }

  /**
   * Display info
   */
  displayInfo(result: InfoResult): void {
    console.log(chalk.blue(`\n📊 Redis Info - ${result.section}\n`));

    Object.entries(result.data).forEach(([section, fields]) => {
      if (typeof fields === 'object' && Object.keys(fields).length > 0) {
        console.log(chalk.bold(`\n${section}:`));

        Object.entries(fields as Record<string, any>).forEach(([key, value]) => {
          console.log(`  ${chalk.dim(key)}: ${value}`);
        });
      }
    });

    console.log('');
  }

  /**
   * Display TTL
   */
  displayTTL(key: string, result: TTLResult): void {
    console.log('\n' + chalk.bold('Key:') + ' ' + chalk.cyan(key));

    if (result.ttl === -2) {
      console.log(chalk.yellow('(key does not exist)\n'));
      return;
    }

    if (result.ttl === -1) {
      console.log(chalk.bold('TTL:') + ' ' + chalk.dim('No expiry set'));
    } else {
      console.log(chalk.bold('TTL:') + ' ' + chalk.green(`${result.ttl} seconds`));

      // Human-readable format
      if (result.ttl > 60) {
        const minutes = Math.floor(result.ttl / 60);
        const seconds = result.ttl % 60;
        console.log(chalk.dim(`      (${minutes}m ${seconds}s)`));
      }
    }

    console.log('');
  }

  /**
   * Cleanup
   */
  async cleanup(): Promise<void> {
    await this.disconnectAll();
  }
}

export default RedisCLI;
