/**
 * MySQL-Specific Tools for MCP Server
 * Provides MySQL-specific database operations and optimizations
 */

import { DatabaseConnectionManager, DatabaseType } from '../../cli/database-manager';
import { MCPTool } from '../types';
import { Pool as MySqlPool } from 'mysql2/promise';

/**
 * MySQL-specific MCP tools
 */
export class MySQLTools {
  constructor(private connectionManager: DatabaseConnectionManager) {}

  /**
   * Get tool definitions
   */
  getToolDefinitions(): MCPTool[] {
    return [
      {
        name: 'mysql_explain',
        description: 'Get query execution plan using EXPLAIN',
        inputSchema: {
          type: 'object',
          properties: {
            sql: {
              type: 'string',
              description: 'SQL query to analyze'
            },
            format: {
              type: 'string',
              enum: ['traditional', 'json', 'tree'],
              description: 'Output format (default: traditional)'
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
        name: 'mysql_optimize',
        description: 'Optimize a table to reclaim unused space and defragment data',
        inputSchema: {
          type: 'object',
          properties: {
            table: {
              type: 'string',
              description: 'Table name to optimize'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['table']
        }
      },
      {
        name: 'mysql_analyze',
        description: 'Analyze and store key distribution for a table',
        inputSchema: {
          type: 'object',
          properties: {
            table: {
              type: 'string',
              description: 'Table name to analyze'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['table']
        }
      },
      {
        name: 'mysql_table_status',
        description: 'Get detailed status information for a table',
        inputSchema: {
          type: 'object',
          properties: {
            table: {
              type: 'string',
              description: 'Table name'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['table']
        }
      },
      {
        name: 'mysql_processlist',
        description: 'Show currently running queries and connections',
        inputSchema: {
          type: 'object',
          properties: {
            full: {
              type: 'boolean',
              description: 'Show full query text'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          }
        }
      },
      {
        name: 'mysql_kill_query',
        description: 'Kill a running query or connection',
        inputSchema: {
          type: 'object',
          properties: {
            id: {
              type: 'number',
              description: 'Process ID to kill'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['id']
        }
      },
      {
        name: 'mysql_variables',
        description: 'Show MySQL system variables',
        inputSchema: {
          type: 'object',
          properties: {
            pattern: {
              type: 'string',
              description: 'Variable name pattern (uses LIKE)'
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
      case 'mysql_explain':
        return this.explain(args);
      case 'mysql_optimize':
        return this.optimize(args);
      case 'mysql_analyze':
        return this.analyze(args);
      case 'mysql_table_status':
        return this.getTableStatus(args);
      case 'mysql_processlist':
        return this.getProcessList(args);
      case 'mysql_kill_query':
        return this.killQuery(args);
      case 'mysql_variables':
        return this.getVariables(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  /**
   * Get MySQL connection
   */
  private getConnection(connectionName?: string): MySqlPool {
    const connection = connectionName
      ? this.connectionManager.getConnection(connectionName)
      : this.connectionManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    if (connection.type !== DatabaseType.MYSQL) {
      throw new Error(`Not a MySQL connection: ${connection.type}`);
    }

    return connection.client as MySqlPool;
  }

  /**
   * EXPLAIN query
   */
  private async explain(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    let explainQuery = 'EXPLAIN';
    if (args.format === 'json') {
      explainQuery = 'EXPLAIN FORMAT=JSON';
    } else if (args.format === 'tree') {
      explainQuery = 'EXPLAIN FORMAT=TREE';
    }
    explainQuery += ` ${args.sql}`;

    const [rows] = await pool.query(explainQuery);

    return {
      success: true,
      query: args.sql,
      format: args.format || 'traditional',
      plan: rows
    };
  }

  /**
   * OPTIMIZE table
   */
  private async optimize(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    const [rows] = await pool.query(`OPTIMIZE TABLE ${args.table}`);

    return {
      success: true,
      table: args.table,
      result: rows,
      message: `Table ${args.table} optimized`
    };
  }

  /**
   * ANALYZE table
   */
  private async analyze(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    const [rows] = await pool.query(`ANALYZE TABLE ${args.table}`);

    return {
      success: true,
      table: args.table,
      result: rows,
      message: `Table ${args.table} analyzed`
    };
  }

  /**
   * Get table status
   */
  private async getTableStatus(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    const [rows] = await pool.query(`SHOW TABLE STATUS LIKE ?`, [args.table]);

    if (!Array.isArray(rows) || rows.length === 0) {
      throw new Error(`Table not found: ${args.table}`);
    }

    return {
      success: true,
      table: args.table,
      status: rows[0]
    };
  }

  /**
   * Get process list
   */
  private async getProcessList(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    const query = args.full ? 'SHOW FULL PROCESSLIST' : 'SHOW PROCESSLIST';
    const [rows] = await pool.query(query);

    return {
      success: true,
      processes: rows,
      count: Array.isArray(rows) ? rows.length : 0
    };
  }

  /**
   * Kill query
   */
  private async killQuery(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    try {
      await pool.query(`KILL ${args.id}`);

      return {
        success: true,
        id: args.id,
        message: `Killed process ${args.id}`
      };
    } catch (error) {
      return {
        success: false,
        id: args.id,
        error: error instanceof Error ? error.message : String(error),
        message: `Failed to kill process ${args.id}`
      };
    }
  }

  /**
   * Get system variables
   */
  private async getVariables(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    const query = args.pattern
      ? `SHOW VARIABLES LIKE ?`
      : `SHOW VARIABLES`;

    const params = args.pattern ? [args.pattern] : [];
    const [rows] = await pool.query(query, params);

    return {
      success: true,
      variables: rows,
      count: Array.isArray(rows) ? rows.length : 0
    };
  }
}
