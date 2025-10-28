/**
 * Common Database Tools for MCP Server
 * Provides database operations that work across all supported database types
 */

import { DatabaseConnectionManager, DatabaseType, ConnectionConfig } from '../../cli/database-manager';
import { MCPTool } from '../types';

/**
 * Common MCP tools for database operations
 */
export class CommonDatabaseTools {
  constructor(private connectionManager: DatabaseConnectionManager) {}

  /**
   * Get tool definitions
   */
  getToolDefinitions(): MCPTool[] {
    return [
      {
        name: 'db_connect',
        description: 'Connect to a database with specified configuration',
        inputSchema: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: 'Connection name'
            },
            type: {
              type: 'string',
              enum: ['postgresql', 'mysql', 'sqlite', 'mongodb', 'redis'],
              description: 'Database type'
            },
            host: {
              type: 'string',
              description: 'Database host (optional if using connectionString)'
            },
            port: {
              type: 'number',
              description: 'Database port (optional if using connectionString)'
            },
            database: {
              type: 'string',
              description: 'Database name'
            },
            username: {
              type: 'string',
              description: 'Username for authentication'
            },
            password: {
              type: 'string',
              description: 'Password for authentication'
            },
            connectionString: {
              type: 'string',
              description: 'Full connection string (alternative to individual parameters)'
            },
            ssl: {
              type: 'boolean',
              description: 'Enable SSL/TLS connection'
            },
            poolSize: {
              type: 'number',
              description: 'Connection pool size (default: 10)'
            }
          },
          required: ['name', 'type']
        }
      },
      {
        name: 'db_disconnect',
        description: 'Disconnect from a database connection',
        inputSchema: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: 'Connection name to disconnect'
            }
          },
          required: ['name']
        }
      },
      {
        name: 'db_list_connections',
        description: 'List all active database connections',
        inputSchema: {
          type: 'object',
          properties: {}
        }
      },
      {
        name: 'db_switch_active',
        description: 'Switch the active database connection',
        inputSchema: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: 'Connection name to set as active'
            }
          },
          required: ['name']
        }
      },
      {
        name: 'db_health_check',
        description: 'Check the health of a database connection',
        inputSchema: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: 'Connection name to check (uses active if not specified)'
            }
          }
        }
      },
      {
        name: 'db_query',
        description: 'Execute a SELECT query on the active connection (PostgreSQL, MySQL, SQLite)',
        inputSchema: {
          type: 'object',
          properties: {
            sql: {
              type: 'string',
              description: 'SQL query to execute'
            },
            params: {
              type: 'array',
              description: 'Query parameters for prepared statements',
              items: {
                type: ['string', 'number', 'boolean', 'null']
              }
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['sql']
        }
      },
      {
        name: 'db_execute',
        description: 'Execute DDL/DML statements (INSERT, UPDATE, DELETE, CREATE, etc.)',
        inputSchema: {
          type: 'object',
          properties: {
            sql: {
              type: 'string',
              description: 'SQL statement to execute'
            },
            params: {
              type: 'array',
              description: 'Statement parameters for prepared statements',
              items: {
                type: ['string', 'number', 'boolean', 'null']
              }
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['sql']
        }
      },
      {
        name: 'db_list_tables',
        description: 'List all tables or collections in the database',
        inputSchema: {
          type: 'object',
          properties: {
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            },
            schema: {
              type: 'string',
              description: 'Schema name (PostgreSQL only)'
            }
          }
        }
      },
      {
        name: 'db_describe_table',
        description: 'Get the schema/structure of a table or collection',
        inputSchema: {
          type: 'object',
          properties: {
            table: {
              type: 'string',
              description: 'Table or collection name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            },
            schema: {
              type: 'string',
              description: 'Schema name (PostgreSQL only)'
            }
          },
          required: ['table']
        }
      },
      {
        name: 'db_get_indexes',
        description: 'List all indexes for a table or collection',
        inputSchema: {
          type: 'object',
          properties: {
            table: {
              type: 'string',
              description: 'Table or collection name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            },
            schema: {
              type: 'string',
              description: 'Schema name (PostgreSQL only)'
            }
          },
          required: ['table']
        }
      }
    ];
  }

  /**
   * Execute a tool
   */
  async executeTool(name: string, args: any): Promise<any> {
    switch (name) {
      case 'db_connect':
        return this.connect(args);
      case 'db_disconnect':
        return this.disconnect(args);
      case 'db_list_connections':
        return this.listConnections();
      case 'db_switch_active':
        return this.switchActive(args);
      case 'db_health_check':
        return this.healthCheck(args);
      case 'db_query':
        return this.query(args);
      case 'db_execute':
        return this.execute(args);
      case 'db_list_tables':
        return this.listTables(args);
      case 'db_describe_table':
        return this.describeTable(args);
      case 'db_get_indexes':
        return this.getIndexes(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  /**
   * Connect to database
   */
  private async connect(args: any): Promise<any> {
    const config: ConnectionConfig = {
      name: args.name,
      type: args.type as DatabaseType,
      host: args.host,
      port: args.port,
      database: args.database,
      username: args.username,
      password: args.password,
      connectionString: args.connectionString,
      ssl: args.ssl,
      poolSize: args.poolSize
    };

    const connection = await this.connectionManager.connect(config);

    return {
      success: true,
      message: `Connected to ${args.type} database: ${args.name}`,
      connection: {
        name: connection.config.name,
        type: connection.type,
        database: connection.config.database,
        host: connection.config.host,
        port: connection.config.port,
        isConnected: connection.isConnected
      }
    };
  }

  /**
   * Disconnect from database
   */
  private async disconnect(args: any): Promise<any> {
    await this.connectionManager.disconnect(args.name);

    return {
      success: true,
      message: `Disconnected from ${args.name}`
    };
  }

  /**
   * List connections
   */
  private listConnections(): any {
    const connections = this.connectionManager.listConnections();

    return {
      success: true,
      connections,
      statistics: this.connectionManager.getStatistics()
    };
  }

  /**
   * Switch active connection
   */
  private async switchActive(args: any): Promise<any> {
    await this.connectionManager.switchActive(args.name);

    return {
      success: true,
      message: `Switched active connection to ${args.name}`,
      activeConnection: args.name
    };
  }

  /**
   * Health check
   */
  private async healthCheck(args: any): Promise<any> {
    const name = args.name || this.connectionManager.getActive()?.config.name;

    if (!name) {
      throw new Error('No active connection');
    }

    const result = await this.connectionManager.healthCheck(name);

    return {
      success: result.healthy,
      connection: name,
      ...result
    };
  }

  /**
   * Execute query
   */
  private async query(args: any): Promise<any> {
    const connection = args.connection
      ? this.connectionManager.getConnection(args.connection)
      : this.connectionManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    if (connection.type === DatabaseType.MONGODB || connection.type === DatabaseType.REDIS) {
      throw new Error(`Use ${connection.type}-specific tools for querying`);
    }

    const rows = await this.connectionManager.executeQuery(args.sql, args.params);

    return {
      success: true,
      rowCount: rows.length,
      rows,
      query: args.sql
    };
  }

  /**
   * Execute statement
   */
  private async execute(args: any): Promise<any> {
    const connection = args.connection
      ? this.connectionManager.getConnection(args.connection)
      : this.connectionManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    if (connection.type === DatabaseType.MONGODB || connection.type === DatabaseType.REDIS) {
      throw new Error(`Use ${connection.type}-specific tools for operations`);
    }

    const rows = await this.connectionManager.executeQuery(args.sql, args.params);

    return {
      success: true,
      affectedRows: rows.length,
      statement: args.sql
    };
  }

  /**
   * List tables
   */
  private async listTables(args: any): Promise<any> {
    const connection = args.connection
      ? this.connectionManager.getConnection(args.connection)
      : this.connectionManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    let query: string;
    let params: any[] = [];

    switch (connection.type) {
      case DatabaseType.POSTGRESQL:
        query = args.schema
          ? `SELECT tablename FROM pg_tables WHERE schemaname = $1 ORDER BY tablename`
          : `SELECT tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') ORDER BY tablename`;
        if (args.schema) params = [args.schema];
        break;

      case DatabaseType.MYSQL:
        query = `SHOW TABLES`;
        break;

      case DatabaseType.SQLITE:
        query = `SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name`;
        break;

      case DatabaseType.MONGODB:
        // MongoDB collections listing would be done via MongoDB API
        throw new Error('Use mongo_list_collections tool for MongoDB');

      case DatabaseType.REDIS:
        throw new Error('Redis does not have tables');

      default:
        throw new Error(`Unsupported database type: ${connection.type}`);
    }

    const rows = await this.connectionManager.executeQuery(query, params);

    return {
      success: true,
      tables: rows.map((r: any) => Object.values(r)[0]),
      count: rows.length
    };
  }

  /**
   * Describe table
   */
  private async describeTable(args: any): Promise<any> {
    const connection = args.connection
      ? this.connectionManager.getConnection(args.connection)
      : this.connectionManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    let query: string;
    let params: any[] = [];

    switch (connection.type) {
      case DatabaseType.POSTGRESQL:
        query = `
          SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
          FROM information_schema.columns
          WHERE table_name = $1
          ${args.schema ? 'AND table_schema = $2' : ''}
          ORDER BY ordinal_position
        `;
        params = args.schema ? [args.table, args.schema] : [args.table];
        break;

      case DatabaseType.MYSQL:
        query = `DESCRIBE ${args.table}`;
        break;

      case DatabaseType.SQLITE:
        query = `PRAGMA table_info(${args.table})`;
        break;

      case DatabaseType.MONGODB:
        throw new Error('Use mongo_get_stats tool for MongoDB collection info');

      case DatabaseType.REDIS:
        throw new Error('Redis does not have table schemas');

      default:
        throw new Error(`Unsupported database type: ${connection.type}`);
    }

    const rows = await this.connectionManager.executeQuery(query, params);

    return {
      success: true,
      table: args.table,
      columns: rows,
      columnCount: rows.length
    };
  }

  /**
   * Get indexes
   */
  private async getIndexes(args: any): Promise<any> {
    const connection = args.connection
      ? this.connectionManager.getConnection(args.connection)
      : this.connectionManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    let query: string;
    let params: any[] = [];

    switch (connection.type) {
      case DatabaseType.POSTGRESQL:
        query = `
          SELECT
            indexname,
            indexdef
          FROM pg_indexes
          WHERE tablename = $1
          ${args.schema ? 'AND schemaname = $2' : ''}
        `;
        params = args.schema ? [args.table, args.schema] : [args.table];
        break;

      case DatabaseType.MYSQL:
        query = `SHOW INDEX FROM ${args.table}`;
        break;

      case DatabaseType.SQLITE:
        query = `SELECT * FROM sqlite_master WHERE type='index' AND tbl_name = ?`;
        params = [args.table];
        break;

      case DatabaseType.MONGODB:
        throw new Error('Use mongo_list_indexes tool for MongoDB');

      case DatabaseType.REDIS:
        throw new Error('Redis does not support indexes in the traditional sense');

      default:
        throw new Error(`Unsupported database type: ${connection.type}`);
    }

    const rows = await this.connectionManager.executeQuery(query, params);

    return {
      success: true,
      table: args.table,
      indexes: rows,
      indexCount: rows.length
    };
  }
}
