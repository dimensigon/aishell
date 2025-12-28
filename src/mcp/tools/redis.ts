/**
 * Redis-Specific Tools for MCP Server
 * Provides Redis-specific database operations
 */

import { DatabaseConnectionManager, DatabaseType } from '../../cli/database-manager';
import { MCPTool } from '../types';
import Redis from 'ioredis';

/**
 * Redis-specific MCP tools
 */
export class RedisTools {
  constructor(private connectionManager: DatabaseConnectionManager) {}

  /**
   * Get tool definitions
   */
  getToolDefinitions(): MCPTool[] {
    return [
      {
        name: 'redis_get',
        description: 'Get the value of a key',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'Key name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['key']
        }
      },
      {
        name: 'redis_set',
        description: 'Set the string value of a key',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'Key name'
            },
            value: {
              type: 'string',
              description: 'Value to set'
            },
            ex: {
              type: 'number',
              description: 'Expiration time in seconds'
            },
            px: {
              type: 'number',
              description: 'Expiration time in milliseconds'
            },
            nx: {
              type: 'boolean',
              description: 'Only set if key does not exist'
            },
            xx: {
              type: 'boolean',
              description: 'Only set if key already exists'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['key', 'value']
        }
      },
      {
        name: 'redis_del',
        description: 'Delete one or more keys',
        inputSchema: {
          type: 'object',
          properties: {
            keys: {
              type: 'array',
              description: 'Keys to delete',
              items: {
                type: 'string'
              }
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['keys']
        }
      },
      {
        name: 'redis_keys',
        description: 'Find all keys matching a pattern',
        inputSchema: {
          type: 'object',
          properties: {
            pattern: {
              type: 'string',
              description: 'Pattern to match (e.g., "user:*")'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['pattern']
        }
      },
      {
        name: 'redis_scan',
        description: 'Incrementally iterate over keys (safer than KEYS for large datasets)',
        inputSchema: {
          type: 'object',
          properties: {
            cursor: {
              type: 'number',
              description: 'Cursor position (0 to start)'
            },
            match: {
              type: 'string',
              description: 'Pattern to match'
            },
            count: {
              type: 'number',
              description: 'Approximate number of keys to return'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['cursor']
        }
      },
      {
        name: 'redis_exists',
        description: 'Check if one or more keys exist',
        inputSchema: {
          type: 'object',
          properties: {
            keys: {
              type: 'array',
              description: 'Keys to check',
              items: {
                type: 'string'
              }
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['keys']
        }
      },
      {
        name: 'redis_ttl',
        description: 'Get the time to live for a key in seconds',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'Key name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['key']
        }
      },
      {
        name: 'redis_expire',
        description: 'Set a timeout on a key',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'Key name'
            },
            seconds: {
              type: 'number',
              description: 'Expiration time in seconds'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['key', 'seconds']
        }
      },
      {
        name: 'redis_hgetall',
        description: 'Get all fields and values in a hash',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'Hash key name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['key']
        }
      },
      {
        name: 'redis_hset',
        description: 'Set the value of a hash field',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'Hash key name'
            },
            field: {
              type: 'string',
              description: 'Field name'
            },
            value: {
              type: 'string',
              description: 'Value to set'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['key', 'field', 'value']
        }
      },
      {
        name: 'redis_lrange',
        description: 'Get a range of elements from a list',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'List key name'
            },
            start: {
              type: 'number',
              description: 'Start index'
            },
            stop: {
              type: 'number',
              description: 'Stop index'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['key', 'start', 'stop']
        }
      },
      {
        name: 'redis_lpush',
        description: 'Prepend one or multiple values to a list',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'List key name'
            },
            values: {
              type: 'array',
              description: 'Values to prepend',
              items: {
                type: 'string'
              }
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['key', 'values']
        }
      },
      {
        name: 'redis_info',
        description: 'Get information and statistics about the server',
        inputSchema: {
          type: 'object',
          properties: {
            section: {
              type: 'string',
              description: 'Info section (server, clients, memory, persistence, stats, replication, cpu, etc.)'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          }
        }
      },
      {
        name: 'redis_dbsize',
        description: 'Get the number of keys in the currently selected database',
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
        name: 'redis_flushdb',
        description: 'Delete all keys in the current database',
        inputSchema: {
          type: 'object',
          properties: {
            async: {
              type: 'boolean',
              description: 'Flush asynchronously'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          }
        }
      }
    ];
  }

  /**
   * Execute a tool
   */
  async executeTool(name: string, args: any): Promise<any> {
    switch (name) {
      case 'redis_get':
        return this.get(args);
      case 'redis_set':
        return this.set(args);
      case 'redis_del':
        return this.del(args);
      case 'redis_keys':
        return this.keys(args);
      case 'redis_scan':
        return this.scan(args);
      case 'redis_exists':
        return this.exists(args);
      case 'redis_ttl':
        return this.ttl(args);
      case 'redis_expire':
        return this.expire(args);
      case 'redis_hgetall':
        return this.hgetall(args);
      case 'redis_hset':
        return this.hset(args);
      case 'redis_lrange':
        return this.lrange(args);
      case 'redis_lpush':
        return this.lpush(args);
      case 'redis_info':
        return this.info(args);
      case 'redis_dbsize':
        return this.dbsize(args);
      case 'redis_flushdb':
        return this.flushdb(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  /**
   * Get Redis client
   */
  private getClient(connectionName?: string): Redis {
    const connection = connectionName
      ? this.connectionManager.getConnection(connectionName)
      : this.connectionManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    if (connection.type !== DatabaseType.REDIS) {
      throw new Error(`Not a Redis connection: ${connection.type}`);
    }

    return connection.client as Redis;
  }

  /**
   * GET command
   */
  private async get(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const value = await client.get(args.key);

    return {
      success: true,
      key: args.key,
      value,
      exists: value !== null
    };
  }

  /**
   * SET command
   */
  private async set(args: any): Promise<any> {
    const client = this.getClient(args.connection);

    // Build options object for ioredis SET command
    const options: any = {};
    if (args.ex) options.EX = args.ex;
    if (args.px) options.PX = args.px;
    if (args.nx) options.NX = true;
    if (args.xx) options.XX = true;

    const result = await client.set(args.key, args.value, options);

    return {
      success: result === 'OK',
      key: args.key,
      value: args.value
    };
  }

  /**
   * DEL command
   */
  private async del(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const count = await client.del(args.keys as string[]);

    return {
      success: true,
      keys: args.keys,
      deletedCount: count
    };
  }

  /**
   * KEYS command
   */
  private async keys(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const keys = await client.keys(args.pattern);

    return {
      success: true,
      pattern: args.pattern,
      keys,
      count: keys.length
    };
  }

  /**
   * SCAN command
   */
  private async scan(args: any): Promise<any> {
    const client = this.getClient(args.connection);

    // Build SCAN options
    const options: any = {};
    if (args.match) options.MATCH = args.match;
    if (args.count) options.COUNT = args.count;

    const [cursor, keys] = await client.scan(args.cursor, options);

    return {
      success: true,
      cursor: parseInt(cursor),
      keys,
      count: keys.length,
      complete: cursor === '0'
    };
  }

  /**
   * EXISTS command
   */
  private async exists(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const count = await client.exists(args.keys as string[]);

    return {
      success: true,
      keys: args.keys,
      existingCount: count
    };
  }

  /**
   * TTL command
   */
  private async ttl(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const ttl = await client.ttl(args.key);

    return {
      success: true,
      key: args.key,
      ttl,
      hasExpiry: ttl > 0,
      message: ttl === -1 ? 'No expiry set' : ttl === -2 ? 'Key does not exist' : `Expires in ${ttl} seconds`
    };
  }

  /**
   * EXPIRE command
   */
  private async expire(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const result = await client.expire(args.key, args.seconds);

    return {
      success: result === 1,
      key: args.key,
      seconds: args.seconds,
      message: result === 1 ? 'Expiry set' : 'Key does not exist'
    };
  }

  /**
   * HGETALL command
   */
  private async hgetall(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const hash = await client.hgetall(args.key);

    return {
      success: true,
      key: args.key,
      hash,
      fieldCount: Object.keys(hash).length
    };
  }

  /**
   * HSET command
   */
  private async hset(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const result = await client.hset(args.key, args.field, args.value);

    return {
      success: true,
      key: args.key,
      field: args.field,
      value: args.value,
      isNew: result === 1
    };
  }

  /**
   * LRANGE command
   */
  private async lrange(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const values = await client.lrange(args.key, args.start, args.stop);

    return {
      success: true,
      key: args.key,
      values,
      count: values.length
    };
  }

  /**
   * LPUSH command
   */
  private async lpush(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const length = await client.lpush(args.key, ...args.values);

    return {
      success: true,
      key: args.key,
      values: args.values,
      newLength: length
    };
  }

  /**
   * INFO command
   */
  private async info(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const info = await client.info(args.section);

    // Parse INFO response into structured object
    const parsed: Record<string, any> = {};
    let currentSection = 'default';

    info.split('\r\n').forEach(line => {
      if (line.startsWith('#')) {
        currentSection = line.substring(2).trim();
        parsed[currentSection] = {};
      } else if (line.includes(':')) {
        const [key, value] = line.split(':');
        if (!parsed[currentSection]) {
          parsed[currentSection] = {};
        }
        parsed[currentSection][key] = value;
      }
    });

    return {
      success: true,
      section: args.section || 'all',
      info: parsed
    };
  }

  /**
   * DBSIZE command
   */
  private async dbsize(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const size = await client.dbsize();

    return {
      success: true,
      keyCount: size
    };
  }

  /**
   * FLUSHDB command
   */
  private async flushdb(args: any): Promise<any> {
    const client = this.getClient(args.connection);
    const result = args.async ? await client.flushdb('ASYNC') : await client.flushdb();

    return {
      success: result === 'OK',
      message: 'Database flushed',
      async: args.async || false
    };
  }
}
