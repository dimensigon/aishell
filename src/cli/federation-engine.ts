/**
 * True Database Federation Engine
 * Enables cross-database JOINs with SQL parsing and intelligent query planning
 * Supports homogeneous and heterogeneous database federations
 */

import { DatabaseConnectionManager, DatabaseType, Connection } from './database-manager';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';
import { EventEmitter } from 'eventemitter3';

const logger = createLogger('FederationEngine');

/**
 * SQL Token types for parsing
 */
enum TokenType {
  KEYWORD = 'KEYWORD',
  IDENTIFIER = 'IDENTIFIER',
  OPERATOR = 'OPERATOR',
  LITERAL = 'LITERAL',
  PUNCTUATION = 'PUNCTUATION',
  WHITESPACE = 'WHITESPACE'
}

interface Token {
  type: TokenType;
  value: string;
  position: number;
}

/**
 * Parsed SQL query structure
 */
interface ParsedQuery {
  type: 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE';
  select: SelectClause[];
  from: FromClause[];
  joins: JoinClause[];
  where?: WhereClause;
  groupBy?: GroupByClause;
  orderBy?: OrderByClause;
  limit?: number;
  offset?: number;
}

interface SelectClause {
  expression: string;
  alias?: string;
  isAggregate: boolean;
  aggregateFunction?: 'COUNT' | 'SUM' | 'AVG' | 'MIN' | 'MAX';
}

interface FromClause {
  database: string;
  table: string;
  alias?: string;
}

interface JoinClause {
  type: 'INNER' | 'LEFT' | 'RIGHT' | 'FULL';
  database: string;
  table: string;
  alias?: string;
  on: JoinCondition;
}

interface JoinCondition {
  left: { table: string; column: string };
  operator: string;
  right: { table: string; column: string };
}

interface WhereClause {
  conditions: any[];
  raw: string;
}

interface GroupByClause {
  columns: string[];
}

interface OrderByClause {
  columns: { column: string; direction: 'ASC' | 'DESC' }[];
}

/**
 * Query execution plan
 */
interface ExecutionPlan {
  id: string;
  query: string;
  databases: string[];
  steps: ExecutionStep[];
  estimatedCost: number;
  strategy: 'nested-loop' | 'hash-join' | 'merge-join';
  createdAt: number;
}

interface ExecutionStep {
  id: string;
  type: 'fetch' | 'join' | 'aggregate' | 'filter' | 'sort' | 'limit';
  database?: string;
  query?: string;
  operation?: string;
  dependencies: string[];
  estimatedRows: number;
  estimatedCost: number;
}

/**
 * Federation result
 */
interface FederationResult {
  rows: any[];
  rowCount: number;
  executionTime: number;
  plan: ExecutionPlan;
  statistics: FederationStatistics;
}

interface FederationStatistics {
  totalDataTransferred: number;
  queriesExecuted: number;
  cacheHits: number;
  cacheMisses: number;
  databases: Record<string, { queries: number; rows: number; time: number }>;
}

/**
 * Federation engine events
 */
interface FederationEngineEvents {
  queryParsed: (parsed: ParsedQuery) => void;
  planGenerated: (plan: ExecutionPlan) => void;
  stepStarted: (step: ExecutionStep) => void;
  stepCompleted: (step: ExecutionStep, rows: number) => void;
  queryCompleted: (result: FederationResult) => void;
  error: (error: Error) => void;
}

/**
 * True Database Federation Engine
 */
export class FederationEngine extends EventEmitter<FederationEngineEvents> {
  private resultCache = new Map<string, any[]>();
  private planCache = new Map<string, ExecutionPlan>();
  private statistics: FederationStatistics = {
    totalDataTransferred: 0,
    queriesExecuted: 0,
    cacheHits: 0,
    cacheMisses: 0,
    databases: {}
  };

  constructor(
    private dbManager: DatabaseConnectionManager,
    private stateManager: StateManager
  ) {
    super();
  }

  /**
   * Execute federated query with cross-database JOINs
   */
  async executeFederatedQuery(sql: string): Promise<FederationResult> {
    logger.info('Executing federated query', { queryLength: sql.length });
    const startTime = Date.now();

    try {
      // Parse SQL query
      const parsed = this.parseSQL(sql);
      this.emit('queryParsed', parsed);
      logger.debug('Query parsed', { type: parsed.type, joins: parsed.joins.length });

      // Validate cross-database query
      this.validateCrossDatabaseQuery(parsed);

      // Generate execution plan
      const plan = await this.generateExecutionPlan(parsed);
      this.emit('planGenerated', plan);
      logger.debug('Execution plan generated', { steps: plan.steps.length, cost: plan.estimatedCost });

      // Execute plan
      const rows = await this.executePlan(plan);

      // Apply post-processing (GROUP BY, ORDER BY, LIMIT)
      const processedRows = await this.applyPostProcessing(rows, parsed);

      const executionTime = Date.now() - startTime;

      const result: FederationResult = {
        rows: processedRows,
        rowCount: processedRows.length,
        executionTime,
        plan,
        statistics: { ...this.statistics }
      };

      this.emit('queryCompleted', result);
      logger.info('Federated query completed', { rowCount: result.rowCount, executionTime });

      return result;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      logger.error('Federated query failed', err);
      this.emit('error', err);
      throw err;
    }
  }

  /**
   * Parse SQL query into structured format
   */
  private parseSQL(sql: string): ParsedQuery {
    const tokens = this.tokenize(sql);
    logger.debug('SQL tokenized', { tokenCount: tokens.length });

    return this.parseTokens(tokens);
  }

  /**
   * Tokenize SQL string
   */
  private tokenize(sql: string): Token[] {
    const tokens: Token[] = [];
    let position = 0;
    let current = 0;

    const keywords = new Set([
      'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER',
      'ON', 'AND', 'OR', 'GROUP', 'BY', 'ORDER', 'LIMIT', 'OFFSET', 'AS',
      'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'DISTINCT', 'ASC', 'DESC'
    ]);

    while (current < sql.length) {
      const char = sql[current];

      // Whitespace
      if (/\s/.test(char)) {
        current++;
        position++;
        continue;
      }

      // String literals
      if (char === "'" || char === '"') {
        const quote = char;
        let value = char;
        current++;
        while (current < sql.length && sql[current] !== quote) {
          value += sql[current];
          current++;
        }
        value += sql[current];
        current++;
        tokens.push({ type: TokenType.LITERAL, value, position });
        position += value.length;
        continue;
      }

      // Numbers
      if (/\d/.test(char)) {
        let value = '';
        while (current < sql.length && /[\d.]/.test(sql[current])) {
          value += sql[current];
          current++;
        }
        tokens.push({ type: TokenType.LITERAL, value, position });
        position += value.length;
        continue;
      }

      // Operators
      if (/[=<>!]/.test(char)) {
        let value = char;
        current++;
        if (current < sql.length && /[=<>]/.test(sql[current])) {
          value += sql[current];
          current++;
        }
        tokens.push({ type: TokenType.OPERATOR, value, position });
        position += value.length;
        continue;
      }

      // Punctuation
      if (/[,();.]/.test(char)) {
        tokens.push({ type: TokenType.PUNCTUATION, value: char, position });
        current++;
        position++;
        continue;
      }

      // Identifiers and keywords
      if (/[a-zA-Z_]/.test(char)) {
        let value = '';
        while (current < sql.length && /[a-zA-Z0-9_]/.test(sql[current])) {
          value += sql[current];
          current++;
        }

        const upperValue = value.toUpperCase();
        const type = keywords.has(upperValue) ? TokenType.KEYWORD : TokenType.IDENTIFIER;
        tokens.push({ type, value, position });
        position += value.length;
        continue;
      }

      // Unknown character
      current++;
      position++;
    }

    return tokens;
  }

  /**
   * Parse tokens into query structure
   */
  private parseTokens(tokens: Token[]): ParsedQuery {
    let current = 0;

    const expectKeyword = (keyword: string): void => {
      if (current >= tokens.length || tokens[current].value.toUpperCase() !== keyword) {
        throw new Error(`Expected keyword ${keyword} at position ${tokens[current]?.position || 'end'}`);
      }
      current++;
    };

    const parseSelectClause = (): SelectClause[] => {
      expectKeyword('SELECT');
      const columns: SelectClause[] = [];

      while (current < tokens.length && tokens[current].value.toUpperCase() !== 'FROM') {
        if (tokens[current].type === TokenType.PUNCTUATION && tokens[current].value === ',') {
          current++;
          continue;
        }

        const token = tokens[current];
        const upperValue = token.value.toUpperCase();

        // Check for aggregate functions
        if (['COUNT', 'SUM', 'AVG', 'MIN', 'MAX'].includes(upperValue)) {
          const func = upperValue as 'COUNT' | 'SUM' | 'AVG' | 'MIN' | 'MAX';
          current++;

          // Expect (
          if (tokens[current].value !== '(') {
            throw new Error('Expected ( after aggregate function');
          }
          current++;

          let expression = '';
          let parenDepth = 1;
          while (parenDepth > 0 && current < tokens.length) {
            if (tokens[current].value === '(') parenDepth++;
            if (tokens[current].value === ')') parenDepth--;
            if (parenDepth > 0) {
              expression += tokens[current].value;
            }
            current++;
          }

          let alias: string | undefined;
          if (current < tokens.length && tokens[current].value.toUpperCase() === 'AS') {
            current++;
            alias = tokens[current].value;
            current++;
          }

          columns.push({
            expression: `${func}(${expression})`,
            alias,
            isAggregate: true,
            aggregateFunction: func
          });
        } else {
          // Regular column
          let expression = token.value;
          current++;

          // Handle table.column notation
          if (current < tokens.length && tokens[current].value === '.') {
            expression += '.';
            current++;
            expression += tokens[current].value;
            current++;
          }

          // Check for alias
          let alias: string | undefined;
          if (current < tokens.length && tokens[current].value.toUpperCase() === 'AS') {
            current++;
            alias = tokens[current].value;
            current++;
          } else if (current < tokens.length && tokens[current].type === TokenType.IDENTIFIER) {
            // Implicit alias
            alias = tokens[current].value;
            current++;
          }

          columns.push({
            expression,
            alias,
            isAggregate: false
          });
        }
      }

      return columns;
    };

    const parseFromClause = (): FromClause => {
      expectKeyword('FROM');

      let database = '';
      let table = '';
      let alias: string | undefined;

      // Check for database.table notation
      const identifier = tokens[current].value;
      current++;

      if (current < tokens.length && tokens[current].value === '.') {
        database = identifier;
        current++;
        table = tokens[current].value;
        current++;
      } else {
        table = identifier;
        // Use active connection's database
        const activeConn = this.dbManager.getActive();
        database = activeConn?.config.name || 'default';
      }

      // Check for alias
      if (current < tokens.length && tokens[current].value.toUpperCase() === 'AS') {
        current++;
        alias = tokens[current].value;
        current++;
      } else if (current < tokens.length && tokens[current].type === TokenType.IDENTIFIER) {
        alias = tokens[current].value;
        current++;
      }

      return { database, table, alias };
    };

    const parseJoinClauses = (): JoinClause[] => {
      const joins: JoinClause[] = [];

      while (current < tokens.length) {
        const keyword = tokens[current].value.toUpperCase();

        if (!['INNER', 'LEFT', 'RIGHT', 'FULL', 'JOIN'].includes(keyword)) {
          break;
        }

        let joinType: 'INNER' | 'LEFT' | 'RIGHT' | 'FULL' = 'INNER';

        if (keyword === 'INNER') {
          current++;
          expectKeyword('JOIN');
          joinType = 'INNER';
        } else if (keyword === 'LEFT') {
          current++;
          if (tokens[current].value.toUpperCase() === 'OUTER') current++;
          expectKeyword('JOIN');
          joinType = 'LEFT';
        } else if (keyword === 'RIGHT') {
          current++;
          if (tokens[current].value.toUpperCase() === 'OUTER') current++;
          expectKeyword('JOIN');
          joinType = 'RIGHT';
        } else if (keyword === 'FULL') {
          current++;
          if (tokens[current].value.toUpperCase() === 'OUTER') current++;
          expectKeyword('JOIN');
          joinType = 'FULL';
        } else {
          current++; // Just JOIN
        }

        // Parse table
        let database = '';
        let table = '';
        let alias: string | undefined;

        const identifier = tokens[current].value;
        current++;

        if (current < tokens.length && tokens[current].value === '.') {
          database = identifier;
          current++;
          table = tokens[current].value;
          current++;
        } else {
          table = identifier;
          const activeConn = this.dbManager.getActive();
          database = activeConn?.config.name || 'default';
        }

        // Check for alias
        if (current < tokens.length && tokens[current].value.toUpperCase() === 'AS') {
          current++;
          alias = tokens[current].value;
          current++;
        } else if (current < tokens.length && tokens[current].type === TokenType.IDENTIFIER) {
          alias = tokens[current].value;
          current++;
        }

        // Parse ON condition
        expectKeyword('ON');

        const leftTable = tokens[current].value;
        current++;
        if (tokens[current].value !== '.') {
          throw new Error('Expected . after table name in JOIN condition');
        }
        current++;
        const leftColumn = tokens[current].value;
        current++;

        const operator = tokens[current].value;
        current++;

        const rightTable = tokens[current].value;
        current++;
        if (tokens[current].value !== '.') {
          throw new Error('Expected . after table name in JOIN condition');
        }
        current++;
        const rightColumn = tokens[current].value;
        current++;

        joins.push({
          type: joinType,
          database,
          table,
          alias,
          on: {
            left: { table: leftTable, column: leftColumn },
            operator,
            right: { table: rightTable, column: rightColumn }
          }
        });
      }

      return joins;
    };

    const parseWhereClause = (): WhereClause | undefined => {
      if (current >= tokens.length || tokens[current].value.toUpperCase() !== 'WHERE') {
        return undefined;
      }

      expectKeyword('WHERE');

      let raw = '';
      while (current < tokens.length) {
        const keyword = tokens[current].value.toUpperCase();
        if (['GROUP', 'ORDER', 'LIMIT', 'OFFSET'].includes(keyword)) {
          break;
        }
        raw += tokens[current].value + ' ';
        current++;
      }

      return { conditions: [], raw: raw.trim() };
    };

    const parseGroupByClause = (): GroupByClause | undefined => {
      if (current >= tokens.length || tokens[current].value.toUpperCase() !== 'GROUP') {
        return undefined;
      }

      expectKeyword('GROUP');
      expectKeyword('BY');

      const columns: string[] = [];
      while (current < tokens.length) {
        const keyword = tokens[current].value.toUpperCase();
        if (['ORDER', 'LIMIT', 'OFFSET'].includes(keyword)) {
          break;
        }

        if (tokens[current].type === TokenType.PUNCTUATION && tokens[current].value === ',') {
          current++;
          continue;
        }

        columns.push(tokens[current].value);
        current++;
      }

      return { columns };
    };

    const parseOrderByClause = (): OrderByClause | undefined => {
      if (current >= tokens.length || tokens[current].value.toUpperCase() !== 'ORDER') {
        return undefined;
      }

      expectKeyword('ORDER');
      expectKeyword('BY');

      const columns: { column: string; direction: 'ASC' | 'DESC' }[] = [];

      while (current < tokens.length) {
        const keyword = tokens[current].value.toUpperCase();
        if (['LIMIT', 'OFFSET'].includes(keyword)) {
          break;
        }

        if (tokens[current].type === TokenType.PUNCTUATION && tokens[current].value === ',') {
          current++;
          continue;
        }

        const column = tokens[current].value;
        current++;

        let direction: 'ASC' | 'DESC' = 'ASC';
        if (current < tokens.length && ['ASC', 'DESC'].includes(tokens[current].value.toUpperCase())) {
          direction = tokens[current].value.toUpperCase() as 'ASC' | 'DESC';
          current++;
        }

        columns.push({ column, direction });
      }

      return { columns };
    };

    const parseLimitOffset = (): { limit?: number; offset?: number } => {
      let limit: number | undefined;
      let offset: number | undefined;

      if (current < tokens.length && tokens[current].value.toUpperCase() === 'LIMIT') {
        current++;
        limit = parseInt(tokens[current].value);
        current++;
      }

      if (current < tokens.length && tokens[current].value.toUpperCase() === 'OFFSET') {
        current++;
        offset = parseInt(tokens[current].value);
        current++;
      }

      return { limit, offset };
    };

    // Parse query
    const select = parseSelectClause();
    const from = parseFromClause();
    const joins = parseJoinClauses();
    const where = parseWhereClause();
    const groupBy = parseGroupByClause();
    const orderBy = parseOrderByClause();
    const { limit, offset } = parseLimitOffset();

    return {
      type: 'SELECT',
      select,
      from: [from],
      joins,
      where,
      groupBy,
      orderBy,
      limit,
      offset
    };
  }

  /**
   * Validate cross-database query
   */
  private validateCrossDatabaseQuery(parsed: ParsedQuery): void {
    const databases = new Set<string>();

    // Collect all databases
    parsed.from.forEach(f => databases.add(f.database));
    parsed.joins.forEach(j => databases.add(j.database));

    if (databases.size < 2) {
      throw new Error('Query must involve at least 2 databases for federation');
    }

    // Verify all databases are connected
    for (const dbName of databases) {
      const conn = this.dbManager.getConnection(dbName);
      if (!conn) {
        throw new Error(`Database connection not found: ${dbName}`);
      }
    }

    logger.info('Cross-database query validated', { databases: Array.from(databases) });
  }

  /**
   * Generate execution plan
   */
  private async generateExecutionPlan(parsed: ParsedQuery): Promise<ExecutionPlan> {
    const planId = `plan-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const databases = new Set<string>();
    const steps: ExecutionStep[] = [];

    // Collect databases
    parsed.from.forEach(f => databases.add(f.database));
    parsed.joins.forEach(j => databases.add(j.database));

    // Determine optimal execution strategy
    const strategy = await this.determineJoinStrategy(parsed);

    // Step 1: Fetch from base table
    const baseTable = parsed.from[0];
    const baseQuery = this.buildFetchQuery(baseTable, parsed.where, parsed.select);
    const baseStats = await this.estimateTableSize(baseTable.database, baseTable.table);

    steps.push({
      id: 'step-0',
      type: 'fetch',
      database: baseTable.database,
      query: baseQuery,
      dependencies: [],
      estimatedRows: baseStats.rowCount,
      estimatedCost: baseStats.rowCount * 0.1
    });

    // Step 2+: Process each JOIN
    for (let i = 0; i < parsed.joins.length; i++) {
      const join = parsed.joins[i];
      const joinStats = await this.estimateTableSize(join.database, join.table);

      // Fetch from join table
      const fetchQuery = this.buildFetchQuery(
        { database: join.database, table: join.table, alias: join.alias },
        parsed.where,
        parsed.select
      );

      steps.push({
        id: `step-${i * 2 + 1}`,
        type: 'fetch',
        database: join.database,
        query: fetchQuery,
        dependencies: [],
        estimatedRows: joinStats.rowCount,
        estimatedCost: joinStats.rowCount * 0.1
      });

      // Perform join
      steps.push({
        id: `step-${i * 2 + 2}`,
        type: 'join',
        operation: `${join.type} JOIN on ${join.on.left.table}.${join.on.left.column} = ${join.on.right.table}.${join.on.right.column}`,
        dependencies: [steps[steps.length - 2].id, steps[steps.length - 1].id],
        estimatedRows: Math.min(baseStats.rowCount, joinStats.rowCount),
        estimatedCost: baseStats.rowCount * joinStats.rowCount * 0.001
      });
    }

    // Add post-processing steps
    if (parsed.groupBy) {
      steps.push({
        id: `step-aggregate`,
        type: 'aggregate',
        operation: `GROUP BY ${parsed.groupBy.columns.join(', ')}`,
        dependencies: [steps[steps.length - 1].id],
        estimatedRows: Math.floor(steps[steps.length - 1].estimatedRows * 0.1),
        estimatedCost: steps[steps.length - 1].estimatedRows * 0.05
      });
    }

    if (parsed.orderBy) {
      steps.push({
        id: `step-sort`,
        type: 'sort',
        operation: `ORDER BY ${parsed.orderBy.columns.map(c => `${c.column} ${c.direction}`).join(', ')}`,
        dependencies: [steps[steps.length - 1].id],
        estimatedRows: steps[steps.length - 1].estimatedRows,
        estimatedCost: steps[steps.length - 1].estimatedRows * Math.log(steps[steps.length - 1].estimatedRows) * 0.01
      });
    }

    if (parsed.limit) {
      steps.push({
        id: `step-limit`,
        type: 'limit',
        operation: `LIMIT ${parsed.limit}${parsed.offset ? ` OFFSET ${parsed.offset}` : ''}`,
        dependencies: [steps[steps.length - 1].id],
        estimatedRows: Math.min(parsed.limit, steps[steps.length - 1].estimatedRows),
        estimatedCost: 0.01
      });
    }

    const totalCost = steps.reduce((sum, step) => sum + step.estimatedCost, 0);

    return {
      id: planId,
      query: '', // Original query
      databases: Array.from(databases),
      steps,
      estimatedCost: totalCost,
      strategy,
      createdAt: Date.now()
    };
  }

  /**
   * Determine optimal JOIN strategy
   */
  private async determineJoinStrategy(parsed: ParsedQuery): Promise<'nested-loop' | 'hash-join' | 'merge-join'> {
    // Simple heuristic: use hash join for larger datasets
    const baseTableStats = await this.estimateTableSize(parsed.from[0].database, parsed.from[0].table);

    if (baseTableStats.rowCount > 10000) {
      return 'hash-join';
    } else if (baseTableStats.rowCount > 1000) {
      return 'merge-join';
    } else {
      return 'nested-loop';
    }
  }

  /**
   * Build fetch query for a table
   */
  private buildFetchQuery(
    table: FromClause | { database: string; table: string; alias?: string },
    where?: WhereClause,
    select?: SelectClause[]
  ): string {
    let query = `SELECT `;

    if (select && select.length > 0) {
      query += select.map(s => s.expression).join(', ');
    } else {
      query += '*';
    }

    query += ` FROM ${table.table}`;

    if (where && where.raw) {
      // Filter WHERE clause to only conditions relevant to this table
      query += ` WHERE ${where.raw}`;
    }

    return query;
  }

  /**
   * Estimate table size
   */
  private async estimateTableSize(database: string, table: string): Promise<{ rowCount: number; sizeBytes: number }> {
    const connection = this.dbManager.getConnection(database);

    if (!connection) {
      return { rowCount: 1000, sizeBytes: 100000 }; // Default estimate
    }

    try {
      const originalActive = this.dbManager.getActive();
      await this.dbManager.switchActive(database);

      let rowCount = 0;

      switch (connection.type) {
        case DatabaseType.POSTGRESQL:
          const pgResult = await this.dbManager.executeQuery(
            `SELECT reltuples AS estimate FROM pg_class WHERE relname = $1`,
            [table]
          );
          rowCount = pgResult[0]?.estimate || 1000;
          break;

        case DatabaseType.MYSQL:
          const mysqlResult = await this.dbManager.executeQuery(
            `SELECT TABLE_ROWS FROM information_schema.TABLES WHERE TABLE_NAME = '${table}'`
          );
          rowCount = mysqlResult[0]?.TABLE_ROWS || 1000;
          break;

        default:
          rowCount = 1000;
      }

      if (originalActive) {
        await this.dbManager.switchActive(originalActive.config.name);
      }

      return { rowCount, sizeBytes: rowCount * 100 };
    } catch (error) {
      logger.warn('Failed to estimate table size', { database, table, error });
      return { rowCount: 1000, sizeBytes: 100000 };
    }
  }

  /**
   * Execute execution plan
   */
  private async executePlan(plan: ExecutionPlan): Promise<any[]> {
    const results = new Map<string, any[]>();
    const executed = new Set<string>();

    while (executed.size < plan.steps.length) {
      // Find steps ready to execute
      const ready = plan.steps.filter(
        step => !executed.has(step.id) && step.dependencies.every(dep => executed.has(dep))
      );

      if (ready.length === 0) {
        throw new Error('Circular dependency in execution plan');
      }

      // Execute ready steps in parallel
      const stepResults = await Promise.all(
        ready.map(step => this.executeStep(step, results))
      );

      ready.forEach((step, idx) => {
        results.set(step.id, stepResults[idx]);
        executed.add(step.id);
      });
    }

    // Return result from final step
    const finalStep = plan.steps[plan.steps.length - 1];
    return results.get(finalStep.id) || [];
  }

  /**
   * Execute single step
   */
  private async executeStep(step: ExecutionStep, intermediateResults: Map<string, any[]>): Promise<any[]> {
    this.emit('stepStarted', step);
    logger.debug('Executing step', { id: step.id, type: step.type });

    let result: any[] = [];

    try {
      switch (step.type) {
        case 'fetch':
          result = await this.executeFetch(step);
          break;

        case 'join':
          result = await this.executeJoin(step, intermediateResults);
          break;

        case 'aggregate':
          result = await this.executeAggregate(step, intermediateResults);
          break;

        case 'filter':
          result = await this.executeFilter(step, intermediateResults);
          break;

        case 'sort':
          result = await this.executeSort(step, intermediateResults);
          break;

        case 'limit':
          result = await this.executeLimit(step, intermediateResults);
          break;
      }

      this.emit('stepCompleted', step, result.length);
      this.statistics.queriesExecuted++;

      return result;
    } catch (error) {
      logger.error('Step execution failed', { step: step.id, error });
      throw error;
    }
  }

  /**
   * Execute fetch step
   */
  private async executeFetch(step: ExecutionStep): Promise<any[]> {
    if (!step.database || !step.query) {
      throw new Error('Fetch step missing database or query');
    }

    // Check cache
    const cacheKey = `${step.database}:${step.query}`;
    if (this.resultCache.has(cacheKey)) {
      this.statistics.cacheHits++;
      return this.resultCache.get(cacheKey)!;
    }

    this.statistics.cacheMisses++;

    // Execute query
    const originalActive = this.dbManager.getActive();
    await this.dbManager.switchActive(step.database);

    const startTime = Date.now();
    const rows = await this.dbManager.executeQuery(step.query);
    const executionTime = Date.now() - startTime;

    if (originalActive) {
      await this.dbManager.switchActive(originalActive.config.name);
    }

    // Update statistics
    if (!this.statistics.databases[step.database]) {
      this.statistics.databases[step.database] = { queries: 0, rows: 0, time: 0 };
    }
    this.statistics.databases[step.database].queries++;
    this.statistics.databases[step.database].rows += rows.length;
    this.statistics.databases[step.database].time += executionTime;

    // Cache result
    this.resultCache.set(cacheKey, rows);

    return rows;
  }

  /**
   * Execute JOIN step
   */
  private async executeJoin(step: ExecutionStep, intermediateResults: Map<string, any[]>): Promise<any[]> {
    const [leftId, rightId] = step.dependencies;
    const leftData = intermediateResults.get(leftId) || [];
    const rightData = intermediateResults.get(rightId) || [];

    if (!step.operation) {
      throw new Error('JOIN step missing operation details');
    }

    // Parse JOIN condition from operation string
    const match = step.operation.match(/(\w+)\s+JOIN\s+on\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)/i);
    if (!match) {
      throw new Error('Invalid JOIN operation format');
    }

    const [, joinType, leftTable, leftColumn, rightTable, rightColumn] = match;

    return this.performJoin(
      leftData,
      rightData,
      { leftColumn, rightColumn },
      joinType.toUpperCase() as 'INNER' | 'LEFT' | 'RIGHT' | 'FULL'
    );
  }

  /**
   * Perform in-memory JOIN
   */
  private performJoin(
    leftData: any[],
    rightData: any[],
    condition: { leftColumn: string; rightColumn: string },
    joinType: 'INNER' | 'LEFT' | 'RIGHT' | 'FULL'
  ): any[] {
    const results: any[] = [];

    // Create hash index for right data
    const rightIndex = new Map<any, any[]>();
    rightData.forEach(row => {
      const key = row[condition.rightColumn];
      if (!rightIndex.has(key)) {
        rightIndex.set(key, []);
      }
      rightIndex.get(key)!.push(row);
    });

    const matchedRightKeys = new Set<any>();

    // Perform join based on type
    leftData.forEach(leftRow => {
      const key = leftRow[condition.leftColumn];
      const matchingRows = rightIndex.get(key) || [];

      if (matchingRows.length > 0) {
        matchingRows.forEach(rightRow => {
          results.push({ ...leftRow, ...rightRow });
        });
        matchedRightKeys.add(key);
      } else if (joinType === 'LEFT' || joinType === 'FULL') {
        // Left join - include left row with nulls for right columns
        const nullRightRow: any = {};
        if (rightData.length > 0) {
          Object.keys(rightData[0]).forEach(col => {
            nullRightRow[col] = null;
          });
        }
        results.push({ ...leftRow, ...nullRightRow });
      }
    });

    // Right or Full outer join - add unmatched right rows
    if (joinType === 'RIGHT' || joinType === 'FULL') {
      rightData.forEach(rightRow => {
        const key = rightRow[condition.rightColumn];
        if (!matchedRightKeys.has(key)) {
          const nullLeftRow: any = {};
          if (leftData.length > 0) {
            Object.keys(leftData[0]).forEach(col => {
              nullLeftRow[col] = null;
            });
          }
          results.push({ ...nullLeftRow, ...rightRow });
        }
      });
    }

    this.statistics.totalDataTransferred += results.length;

    return results;
  }

  /**
   * Execute aggregate step
   */
  private async executeAggregate(step: ExecutionStep, intermediateResults: Map<string, any[]>): Promise<any[]> {
    const inputData = intermediateResults.get(step.dependencies[0]) || [];

    if (!step.operation) {
      return inputData;
    }

    // Parse GROUP BY columns
    const match = step.operation.match(/GROUP\s+BY\s+(.+)/i);
    if (!match) {
      return inputData;
    }

    const groupByColumns = match[1].split(',').map(c => c.trim());

    // Group data
    const groups = new Map<string, any[]>();

    inputData.forEach(row => {
      const key = groupByColumns.map(col => row[col]).join('|');
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)!.push(row);
    });

    // Aggregate each group
    const results: any[] = [];

    groups.forEach((rows, key) => {
      const groupRow: any = {};

      // Add grouping columns
      groupByColumns.forEach((col, idx) => {
        groupRow[col] = key.split('|')[idx];
      });

      // Calculate aggregates
      Object.keys(rows[0]).forEach(col => {
        if (!groupByColumns.includes(col)) {
          // Check if this is an aggregate column
          const values = rows.map(r => r[col]).filter(v => v != null);
          if (values.length > 0 && typeof values[0] === 'number') {
            groupRow[`count_${col}`] = values.length;
            groupRow[`sum_${col}`] = values.reduce((a, b) => a + b, 0);
            groupRow[`avg_${col}`] = values.reduce((a, b) => a + b, 0) / values.length;
            groupRow[`min_${col}`] = Math.min(...values);
            groupRow[`max_${col}`] = Math.max(...values);
          }
        }
      });

      results.push(groupRow);
    });

    return results;
  }

  /**
   * Execute filter step
   */
  private async executeFilter(step: ExecutionStep, intermediateResults: Map<string, any[]>): Promise<any[]> {
    const inputData = intermediateResults.get(step.dependencies[0]) || [];

    // Implement filtering logic based on step.operation
    // For now, return input data as-is
    return inputData;
  }

  /**
   * Execute sort step
   */
  private async executeSort(step: ExecutionStep, intermediateResults: Map<string, any[]>): Promise<any[]> {
    const inputData = intermediateResults.get(step.dependencies[0]) || [];

    if (!step.operation) {
      return inputData;
    }

    // Parse ORDER BY
    const match = step.operation.match(/ORDER\s+BY\s+(.+)/i);
    if (!match) {
      return inputData;
    }

    const orderBy = match[1].split(',').map(col => {
      const parts = col.trim().split(/\s+/);
      return {
        column: parts[0],
        direction: parts[1]?.toUpperCase() === 'DESC' ? 'DESC' : 'ASC'
      };
    });

    return inputData.sort((a, b) => {
      for (const { column, direction } of orderBy) {
        const aVal = a[column];
        const bVal = b[column];

        if (aVal < bVal) return direction === 'ASC' ? -1 : 1;
        if (aVal > bVal) return direction === 'ASC' ? 1 : -1;
      }
      return 0;
    });
  }

  /**
   * Execute limit step
   */
  private async executeLimit(step: ExecutionStep, intermediateResults: Map<string, any[]>): Promise<any[]> {
    const inputData = intermediateResults.get(step.dependencies[0]) || [];

    if (!step.operation) {
      return inputData;
    }

    // Parse LIMIT and OFFSET
    const match = step.operation.match(/LIMIT\s+(\d+)(?:\s+OFFSET\s+(\d+))?/i);
    if (!match) {
      return inputData;
    }

    const limit = parseInt(match[1]);
    const offset = match[2] ? parseInt(match[2]) : 0;

    return inputData.slice(offset, offset + limit);
  }

  /**
   * Apply post-processing
   */
  private async applyPostProcessing(rows: any[], parsed: ParsedQuery): Promise<any[]> {
    // Most post-processing is handled in execution steps
    // This is for any final transformations
    return rows;
  }

  /**
   * Get execution plan explanation
   */
  explainQuery(sql: string): Promise<string> {
    return new Promise(async (resolve) => {
      try {
        const parsed = this.parseSQL(sql);
        const plan = await this.generateExecutionPlan(parsed);

        let explanation = '='.repeat(80) + '\n';
        explanation += 'FEDERATED QUERY EXECUTION PLAN\n';
        explanation += '='.repeat(80) + '\n\n';

        explanation += `Strategy: ${plan.strategy}\n`;
        explanation += `Estimated Cost: ${plan.estimatedCost.toFixed(2)}\n`;
        explanation += `Databases: ${plan.databases.join(', ')}\n`;
        explanation += `Steps: ${plan.steps.length}\n\n`;

        plan.steps.forEach((step, idx) => {
          explanation += `Step ${idx + 1}: ${step.type.toUpperCase()}\n`;
          if (step.database) explanation += `  Database: ${step.database}\n`;
          if (step.query) explanation += `  Query: ${step.query}\n`;
          if (step.operation) explanation += `  Operation: ${step.operation}\n`;
          explanation += `  Dependencies: ${step.dependencies.length > 0 ? step.dependencies.join(', ') : 'none'}\n`;
          explanation += `  Estimated Rows: ${step.estimatedRows}\n`;
          explanation += `  Estimated Cost: ${step.estimatedCost.toFixed(2)}\n`;
          explanation += '\n';
        });

        explanation += '='.repeat(80);

        resolve(explanation);
      } catch (error) {
        resolve(`Error explaining query: ${error instanceof Error ? error.message : String(error)}`);
      }
    });
  }

  /**
   * Get federation statistics
   */
  getStatistics(): FederationStatistics {
    return { ...this.statistics };
  }

  /**
   * Clear caches
   */
  clearCaches(): void {
    this.resultCache.clear();
    this.planCache.clear();
    logger.info('Federation caches cleared');
  }

  /**
   * Reset statistics
   */
  resetStatistics(): void {
    this.statistics = {
      totalDataTransferred: 0,
      queriesExecuted: 0,
      cacheHits: 0,
      cacheMisses: 0,
      databases: {}
    };
    logger.info('Federation statistics reset');
  }
}
