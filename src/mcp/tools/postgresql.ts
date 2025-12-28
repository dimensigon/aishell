/**
 * PostgreSQL-Specific Tools for MCP Server
 * Provides PostgreSQL-specific database operations and optimizations
 */

import { DatabaseConnectionManager, DatabaseType } from '../../cli/database-manager';
import { MCPTool } from '../types';
import { Pool as PgPool } from 'pg';

/**
 * PostgreSQL-specific MCP tools
 */
export class PostgreSQLTools {
  constructor(private connectionManager: DatabaseConnectionManager) {}

  /**
   * Get tool definitions
   */
  getToolDefinitions(): MCPTool[] {
    return [
      {
        name: 'pg_explain',
        description: 'Get query execution plan using EXPLAIN or EXPLAIN ANALYZE',
        inputSchema: {
          type: 'object',
          properties: {
            sql: {
              type: 'string',
              description: 'SQL query to analyze'
            },
            analyze: {
              type: 'boolean',
              description: 'Execute the query and show actual timings (EXPLAIN ANALYZE)'
            },
            verbose: {
              type: 'boolean',
              description: 'Show additional information'
            },
            buffers: {
              type: 'boolean',
              description: 'Show buffer usage statistics'
            },
            format: {
              type: 'string',
              enum: ['text', 'json', 'xml', 'yaml'],
              description: 'Output format (default: text)'
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
        name: 'pg_vacuum',
        description: 'Run VACUUM on a table to reclaim storage and update statistics',
        inputSchema: {
          type: 'object',
          properties: {
            table: {
              type: 'string',
              description: 'Table name to vacuum'
            },
            full: {
              type: 'boolean',
              description: 'Perform full vacuum (rewrites entire table)'
            },
            analyze: {
              type: 'boolean',
              description: 'Update statistics after vacuum'
            },
            verbose: {
              type: 'boolean',
              description: 'Show detailed vacuum information'
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
        name: 'pg_analyze',
        description: 'Update query planner statistics for a table',
        inputSchema: {
          type: 'object',
          properties: {
            table: {
              type: 'string',
              description: 'Table name to analyze (omit for all tables)'
            },
            verbose: {
              type: 'boolean',
              description: 'Show detailed analyze information'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          }
        }
      },
      {
        name: 'pg_get_stats',
        description: 'Get detailed statistics for a table',
        inputSchema: {
          type: 'object',
          properties: {
            table: {
              type: 'string',
              description: 'Table name'
            },
            schema: {
              type: 'string',
              description: 'Schema name (default: public)'
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
        name: 'pg_table_size',
        description: 'Get the size of a table and its indexes',
        inputSchema: {
          type: 'object',
          properties: {
            table: {
              type: 'string',
              description: 'Table name'
            },
            schema: {
              type: 'string',
              description: 'Schema name (default: public)'
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
        name: 'pg_active_queries',
        description: 'List currently running queries',
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
        name: 'pg_kill_query',
        description: 'Terminate a running query by its process ID',
        inputSchema: {
          type: 'object',
          properties: {
            pid: {
              type: 'number',
              description: 'Process ID of the query to terminate'
            },
            connection: {
              type: 'string',
              description: 'Connection name (uses active if not specified)'
            }
          },
          required: ['pid']
        }
      }
    ];
  }

  /**
   * Execute a tool
   */
  async executeTool(name: string, args: any): Promise<any> {
    switch (name) {
      case 'pg_explain':
        return this.explain(args);
      case 'pg_vacuum':
        return this.vacuum(args);
      case 'pg_analyze':
        return this.analyze(args);
      case 'pg_get_stats':
        return this.getStats(args);
      case 'pg_table_size':
        return this.getTableSize(args);
      case 'pg_active_queries':
        return this.getActiveQueries(args);
      case 'pg_kill_query':
        return this.killQuery(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  /**
   * Get PostgreSQL connection
   */
  private getConnection(connectionName?: string): PgPool {
    const connection = connectionName
      ? this.connectionManager.getConnection(connectionName)
      : this.connectionManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    if (connection.type !== DatabaseType.POSTGRESQL) {
      throw new Error(`Not a PostgreSQL connection: ${connection.type}`);
    }

    return connection.client as PgPool;
  }

  /**
   * EXPLAIN query
   */
  private async explain(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    const options: string[] = [];
    if (args.analyze) options.push('ANALYZE');
    if (args.verbose) options.push('VERBOSE');
    if (args.buffers) options.push('BUFFERS');
    if (args.format) options.push(`FORMAT ${args.format.toUpperCase()}`);

    const explainQuery = `EXPLAIN ${options.length ? `(${options.join(', ')})` : ''} ${args.sql}`;

    const result = await pool.query(explainQuery);

    return {
      success: true,
      query: args.sql,
      explainOptions: options,
      plan: args.format === 'json' ? result.rows[0]['QUERY PLAN'] : result.rows.map(r => r['QUERY PLAN'] || Object.values(r)[0])
    };
  }

  /**
   * VACUUM table
   */
  private async vacuum(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    const options: string[] = [];
    if (args.full) options.push('FULL');
    if (args.analyze) options.push('ANALYZE');
    if (args.verbose) options.push('VERBOSE');

    const vacuumQuery = `VACUUM ${options.length ? `(${options.join(', ')})` : ''} ${args.table}`;

    const result = await pool.query(vacuumQuery);

    return {
      success: true,
      table: args.table,
      options,
      message: `VACUUM completed on ${args.table}`
    };
  }

  /**
   * ANALYZE table
   */
  private async analyze(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    const analyzeQuery = `ANALYZE ${args.verbose ? 'VERBOSE' : ''} ${args.table || ''}`.trim();

    await pool.query(analyzeQuery);

    return {
      success: true,
      table: args.table || 'all tables',
      message: `ANALYZE completed`
    };
  }

  /**
   * Get table statistics
   */
  private async getStats(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);
    const schema = args.schema || 'public';

    const query = `
      SELECT
        schemaname,
        tablename,
        n_tup_ins as inserts,
        n_tup_upd as updates,
        n_tup_del as deletes,
        n_live_tup as live_tuples,
        n_dead_tup as dead_tuples,
        last_vacuum,
        last_autovacuum,
        last_analyze,
        last_autoanalyze
      FROM pg_stat_user_tables
      WHERE tablename = $1 AND schemaname = $2
    `;

    const result = await pool.query(query, [args.table, schema]);

    if (result.rows.length === 0) {
      throw new Error(`Table not found: ${schema}.${args.table}`);
    }

    return {
      success: true,
      table: args.table,
      schema,
      statistics: result.rows[0]
    };
  }

  /**
   * Get table size
   */
  private async getTableSize(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);
    const schema = args.schema || 'public';
    const fullTableName = `"${schema}"."${args.table}"`;

    const query = `
      SELECT
        pg_size_pretty(pg_total_relation_size($1)) as total_size,
        pg_size_pretty(pg_relation_size($1)) as table_size,
        pg_size_pretty(pg_indexes_size($1)) as indexes_size,
        pg_total_relation_size($1) as total_bytes,
        pg_relation_size($1) as table_bytes,
        pg_indexes_size($1) as indexes_bytes
    `;

    const result = await pool.query(query, [fullTableName]);

    return {
      success: true,
      table: args.table,
      schema,
      size: result.rows[0]
    };
  }

  /**
   * Get active queries
   */
  private async getActiveQueries(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    const query = `
      SELECT
        pid,
        usename,
        application_name,
        client_addr,
        state,
        query,
        query_start,
        state_change,
        wait_event_type,
        wait_event
      FROM pg_stat_activity
      WHERE state != 'idle'
        AND pid != pg_backend_pid()
      ORDER BY query_start
    `;

    const result = await pool.query(query);

    return {
      success: true,
      activeQueries: result.rows,
      count: result.rows.length
    };
  }

  /**
   * Kill query
   */
  private async killQuery(args: any): Promise<any> {
    const pool = this.getConnection(args.connection);

    const query = `SELECT pg_terminate_backend($1)`;
    const result = await pool.query(query, [args.pid]);

    return {
      success: result.rows[0].pg_terminate_backend,
      pid: args.pid,
      message: result.rows[0].pg_terminate_backend
        ? `Terminated query with PID ${args.pid}`
        : `Failed to terminate query with PID ${args.pid}`
    };
  }
}
