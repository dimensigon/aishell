/**
 * Query Executor with Safety
 * Executes SQL queries with safety checks, confirmations, and transaction support
 */

import { DatabaseConnectionManager } from './db-connection-manager';
import { ErrorHandler } from '../core/error-handler';
import { EventEmitter } from 'eventemitter3';

/**
 * Query result
 */
export interface QueryResult {
  rows: any[];
  rowCount: number;
  fields?: any[];
  executionTime: number;
  affectedRows?: number;
}

/**
 * Execution options
 */
export interface ExecuteOptions {
  timeout?: number;
  maxRows?: number;
  dryRun?: boolean;
  requireConfirmation?: boolean;
  transaction?: boolean;
}

/**
 * Execution plan
 */
export interface ExecutionPlan {
  query: string;
  estimatedRows?: number;
  estimatedCost?: number;
  indexes?: string[];
  warnings: string[];
  isDestructive: boolean;
}

/**
 * Query executor events
 */
export interface QueryExecutorEvents {
  queryStart: (query: string) => void;
  queryComplete: (result: QueryResult) => void;
  queryError: (error: Error) => void;
  confirmationRequired: (query: string, isDestructive: boolean) => void;
}

/**
 * Query Executor with Safety
 */
export class QueryExecutor extends EventEmitter<QueryExecutorEvents> {
  private readonly destructiveKeywords = [
    'drop',
    'delete',
    'truncate',
    'alter',
    'update'
  ];

  constructor(
    private connectionManager: DatabaseConnectionManager,
    private errorHandler: ErrorHandler
  ) {
    super();
  }

  /**
   * Execute SQL query
   */
  async execute(sql: string, options: ExecuteOptions = {}): Promise<QueryResult> {
    const wrappedFn = this.errorHandler.wrap(
      async () => {
        const startTime = Date.now();

        // Check for active connection
        const connection = this.connectionManager.getActive();
        if (!connection) {
          throw new Error('No active database connection');
        }

        // Analyze query for destructive operations
        const isDestructive = this.isDestructiveQuery(sql);

        // Require confirmation for destructive operations if not explicitly disabled
        if (
          isDestructive &&
          options.requireConfirmation !== false
        ) {
          this.emit('confirmationRequired', sql, true);
          // In CLI, this would prompt the user
          // For now, we'll throw an error to force explicit confirmation
          throw new Error(
            'Destructive operation requires explicit confirmation. Use executeWithConfirmation() instead.'
          );
        }

        // Dry run mode
        if (options.dryRun) {
          await this.dryRun(sql);
          return {
            rows: [],
            rowCount: 0,
            executionTime: 0,
            affectedRows: 0
          };
        }

        this.emit('queryStart', sql);

        let result: QueryResult;

        // Execute with timeout if specified
        if (options.timeout) {
          result = await this.executeWithTimeout(sql, options.timeout);
        } else {
          result = await this.executeQuery(sql);
        }

        // Limit rows if specified
        if (options.maxRows && result.rows.length > options.maxRows) {
          result.rows = result.rows.slice(0, options.maxRows);
          result.rowCount = options.maxRows;
        }

        result.executionTime = Date.now() - startTime;

        this.emit('queryComplete', result);

        return result;
      },
      {
        operation: 'execute',
        component: 'QueryExecutor'
      }
    );

    const result = await wrappedFn();
    if (!result) {
      throw new Error('Query execution failed');
    }
    return result;
  }

  /**
   * Execute query with explicit confirmation
   */
  async executeWithConfirmation(sql: string, confirmed: boolean = false): Promise<QueryResult> {
    const isDestructive = this.isDestructiveQuery(sql);

    if (isDestructive && !confirmed) {
      throw new Error('Confirmation required for destructive operation');
    }

    return this.execute(sql, { requireConfirmation: false });
  }

  /**
   * Dry run - analyze query without executing
   */
  async dryRun(sql: string): Promise<ExecutionPlan> {
    const wrappedFn = this.errorHandler.wrap(
      async () => {
        const connection = this.connectionManager.getActive();
        if (!connection) {
          throw new Error('No active database connection');
        }

        const isDestructive = this.isDestructiveQuery(sql);
        const warnings: string[] = [];

        // Add warnings for destructive operations
        if (isDestructive) {
          warnings.push('⚠️ This is a DESTRUCTIVE operation that will modify or delete data');
        }

        // Check for missing WHERE clause in UPDATE/DELETE
        if (this.hasMissingWhereClause(sql)) {
          warnings.push('⚠️ No WHERE clause detected - this will affect ALL rows');
        }

        // Check for SELECT *
        if (sql.toLowerCase().includes('select *')) {
          warnings.push('⚠️ SELECT * can be inefficient for large tables');
        }

        // Try to get query plan (PostgreSQL)
        let estimatedRows: number | undefined;
        let estimatedCost: number | undefined;
        let indexes: string[] | undefined;

        try {
          if (connection.type === 'postgresql') {
            const explainSql = `EXPLAIN (FORMAT JSON) ${sql}`;
            const result = await this.executeQuery(explainSql);

            if (result.rows.length > 0) {
              const plan = result.rows[0]['QUERY PLAN']?.[0];
              if (plan) {
                estimatedRows = plan['Plan']?.['Plan Rows'];
                estimatedCost = plan['Plan']?.['Total Cost'];
                indexes = this.extractIndexes(plan);
              }
            }
          }
        } catch (error) {
          // Ignore errors in EXPLAIN
        }

        return {
          query: sql,
          estimatedRows,
          estimatedCost,
          indexes,
          warnings,
          isDestructive
        };
      },
      {
        operation: 'dryRun',
        component: 'QueryExecutor'
      }
    );

    const result = await wrappedFn();
    if (!result) {
      throw new Error('Dry run failed');
    }
    return result;
  }

  /**
   * Execute query in transaction
   */
  async executeInTransaction(queries: string[]): Promise<QueryResult[]> {
    const wrappedFn = this.errorHandler.wrap(
      async () => {
        const connection = this.connectionManager.getActive();
        if (!connection) {
          throw new Error('No active database connection');
        }

        const results: QueryResult[] = [];

        try {
          // Begin transaction
          await this.executeQuery('BEGIN');

          // Execute all queries
          for (const sql of queries) {
            const result = await this.executeQuery(sql);
            results.push(result);
          }

          // Commit transaction
          await this.executeQuery('COMMIT');

          return results;
        } catch (error) {
          // Rollback on error
          await this.executeQuery('ROLLBACK');
          throw error;
        }
      },
      {
        operation: 'executeInTransaction',
        component: 'QueryExecutor'
      }
    );

    const result = await wrappedFn();
    if (!result) {
      throw new Error('Transaction failed');
    }
    return result;
  }

  /**
   * Execute query with timeout
   */
  private async executeWithTimeout(sql: string, timeout: number): Promise<QueryResult> {
    return Promise.race([
      this.executeQuery(sql),
      new Promise<QueryResult>((_, reject) =>
        setTimeout(() => reject(new Error(`Query timeout after ${timeout}ms`)), timeout)
      )
    ]);
  }

  /**
   * Execute query on active connection
   */
  private async executeQuery(sql: string): Promise<QueryResult> {
    const rows = await this.connectionManager.executeQuery(sql);

    return {
      rows,
      rowCount: rows.length,
      executionTime: 0,
      affectedRows: rows.length
    };
  }

  /**
   * Check if query is destructive
   */
  private isDestructiveQuery(sql: string): boolean {
    const sqlLower = sql.toLowerCase().trim();

    return this.destructiveKeywords.some((keyword) => {
      const pattern = new RegExp(`\\b${keyword}\\b`, 'i');
      return pattern.test(sqlLower);
    });
  }

  /**
   * Check if query is missing WHERE clause
   */
  private hasMissingWhereClause(sql: string): boolean {
    const sqlLower = sql.toLowerCase().trim();

    if (sqlLower.startsWith('delete') || sqlLower.startsWith('update')) {
      return !sqlLower.includes('where');
    }

    return false;
  }

  /**
   * Extract indexes from query plan
   */
  private extractIndexes(plan: any): string[] {
    const indexes: string[] = [];

    const traverse = (node: any) => {
      if (node['Index Name']) {
        indexes.push(node['Index Name']);
      }

      if (node.Plans) {
        for (const child of node.Plans) {
          traverse(child);
        }
      }
    };

    traverse(plan.Plan);
    return indexes;
  }

  /**
   * Validate SQL syntax (basic)
   */
  validateSyntax(sql: string): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Check for balanced parentheses
    let parenCount = 0;
    for (const char of sql) {
      if (char === '(') parenCount++;
      if (char === ')') parenCount--;
      if (parenCount < 0) {
        errors.push('Unbalanced parentheses');
        break;
      }
    }

    if (parenCount !== 0) {
      errors.push('Unbalanced parentheses');
    }

    // Check for SQL injection patterns (basic)
    const suspiciousPatterns = [
      /;\s*drop\s+table/i,
      /;\s*delete\s+from/i,
      /union\s+select/i,
      /'\s*or\s+'1'\s*=\s*'1/i,
      /--/,
      /\/\*/
    ];

    for (const pattern of suspiciousPatterns) {
      if (pattern.test(sql)) {
        errors.push('Potentially unsafe SQL pattern detected');
        break;
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Stream large result set
   */
  async *executeStream(
    sql: string,
    batchSize: number = 100
  ): AsyncGenerator<any[], void, undefined> {
    const connection = this.connectionManager.getActive();
    if (!connection) {
      throw new Error('No active database connection');
    }

    // For now, execute and batch results
    // TODO: Implement proper streaming for each database type
    const result = await this.executeQuery(sql);

    for (let i = 0; i < result.rows.length; i += batchSize) {
      yield result.rows.slice(i, i + batchSize);
    }
  }

  /**
   * Batch execute multiple queries
   */
  async executeBatch(queries: string[]): Promise<QueryResult[]> {
    const results: QueryResult[] = [];

    for (const sql of queries) {
      const result = await this.execute(sql);
      results.push(result);
    }

    return results;
  }

  /**
   * Get query statistics
   */
  async getQueryStats(sql: string): Promise<{
    estimatedRows: number;
    estimatedCost: number;
    estimatedTime: number;
  }> {
    const plan = await this.dryRun(sql);

    return {
      estimatedRows: plan.estimatedRows || 0,
      estimatedCost: plan.estimatedCost || 0,
      estimatedTime: 0 // TODO: Estimate based on cost
    };
  }
}
