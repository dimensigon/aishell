/**
 * Interactive Query Builder CLI
 * Step-by-step query construction with validation, templates, and draft management
 *
 * Features:
 * - Interactive prompts for SELECT/INSERT/UPDATE/DELETE
 * - Visual query preview at each step
 * - Query validation and SQL generation
 * - Save/load draft functionality
 * - Template system
 * - Event-driven architecture
 */

import inquirer from 'inquirer';
import { EventEmitter } from 'eventemitter3';
import chalk from 'chalk';
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { QueryExecutor, QueryResult } from './query-executor';
import { ResultFormatter } from './formatters';
import { StateManager } from '../core/state-manager';
import { createLogger } from '../core/logger';
import { v4 as uuidv4 } from 'uuid';
import fs from 'fs/promises';
import path from 'path';

const logger = createLogger('QueryBuilderCLI');

/**
 * Query types
 */
export enum QueryType {
  SELECT = 'SELECT',
  INSERT = 'INSERT',
  UPDATE = 'UPDATE',
  DELETE = 'DELETE'
}

/**
 * Join types
 */
export enum JoinType {
  INNER = 'INNER JOIN',
  LEFT = 'LEFT JOIN',
  RIGHT = 'RIGHT JOIN',
  FULL = 'FULL OUTER JOIN'
}

/**
 * Condition operator
 */
export enum ConditionOperator {
  EQUAL = '=',
  NOT_EQUAL = '!=',
  GREATER = '>',
  LESS = '<',
  GREATER_EQUAL = '>=',
  LESS_EQUAL = '<=',
  LIKE = 'LIKE',
  IN = 'IN',
  NOT_IN = 'NOT IN',
  IS_NULL = 'IS NULL',
  IS_NOT_NULL = 'IS NOT NULL',
  BETWEEN = 'BETWEEN'
}

/**
 * Query condition
 */
export interface QueryCondition {
  column: string;
  operator: ConditionOperator;
  value?: any;
  secondValue?: any; // For BETWEEN
  logicalOperator?: 'AND' | 'OR';
}

/**
 * Join clause
 */
export interface JoinClause {
  type: JoinType;
  table: string;
  on: string;
}

/**
 * Order by clause
 */
export interface OrderByClause {
  column: string;
  direction: 'ASC' | 'DESC';
}

/**
 * Query builder state
 */
export interface QueryBuilderState {
  type: QueryType;
  table: string;
  columns: string[];
  values?: Record<string, any>;
  conditions: QueryCondition[];
  joins: JoinClause[];
  orderBy: OrderByClause[];
  groupBy: string[];
  having: QueryCondition[];
  limit?: number;
  offset?: number;
  distinct?: boolean;
}

/**
 * Query draft
 */
export interface QueryDraft {
  id: string;
  name: string;
  state: QueryBuilderState;
  createdAt: number;
  updatedAt: number;
  sql?: string;
}

/**
 * Query template
 */
export interface QueryTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  state: Partial<QueryBuilderState>;
  variables?: string[];
}

/**
 * Query history entry
 */
export interface QueryHistoryEntry {
  id: string;
  sql: string;
  state: QueryBuilderState;
  executedAt: number;
  success: boolean;
  rowCount?: number;
  error?: string;
}

/**
 * Query builder events
 */
export interface QueryBuilderEvents {
  stateChanged: (state: QueryBuilderState) => void;
  queryGenerated: (sql: string) => void;
  queryExecuted: (result: QueryResult) => void;
  draftSaved: (draft: QueryDraft) => void;
  draftLoaded: (draft: QueryDraft) => void;
  templateApplied: (template: QueryTemplate) => void;
  error: (error: Error) => void;
}

/**
 * Interactive Query Builder CLI
 */
export class QueryBuilderCLI extends EventEmitter<QueryBuilderEvents> {
  private state: QueryBuilderState;
  private draftsDir: string;
  private historyFile: string;
  private templatesFile: string;
  private history: QueryHistoryEntry[] = [];
  private templates: QueryTemplate[] = [];

  constructor(
    private connectionManager: DatabaseConnectionManager,
    private queryExecutor: QueryExecutor,
    private formatter: ResultFormatter,
    private stateManager: StateManager
  ) {
    super();

    this.state = this.createEmptyState();
    this.draftsDir = path.join(process.cwd(), '.aishell', 'query-drafts');
    this.historyFile = path.join(process.cwd(), '.aishell', 'query-history.json');
    this.templatesFile = path.join(process.cwd(), '.aishell', 'query-templates.json');

    this.initializeStorage();
    this.loadTemplates();
    this.loadHistory();
  }

  /**
   * Initialize storage directories
   */
  private async initializeStorage(): Promise<void> {
    try {
      await fs.mkdir(this.draftsDir, { recursive: true });
      await fs.mkdir(path.dirname(this.historyFile), { recursive: true });
    } catch (error) {
      logger.error('Failed to initialize storage', error);
    }
  }

  /**
   * Create empty query state
   */
  private createEmptyState(): QueryBuilderState {
    return {
      type: QueryType.SELECT,
      table: '',
      columns: [],
      conditions: [],
      joins: [],
      orderBy: [],
      groupBy: [],
      having: []
    };
  }

  /**
   * Start interactive query builder
   */
  async start(): Promise<void> {
    console.log(chalk.cyan.bold('\n🔧 Interactive Query Builder\n'));

    try {
      // Step 1: Choose query type
      await this.selectQueryType();

      // Step 2: Build query based on type
      switch (this.state.type) {
        case QueryType.SELECT:
          await this.buildSelectQuery();
          break;
        case QueryType.INSERT:
          await this.buildInsertQuery();
          break;
        case QueryType.UPDATE:
          await this.buildUpdateQuery();
          break;
        case QueryType.DELETE:
          await this.buildDeleteQuery();
          break;
      }

      // Step 3: Preview and execute
      await this.previewAndExecute();
    } catch (error) {
      if (error instanceof Error && error.message !== 'User cancelled') {
        this.emit('error', error as Error);
        logger.error('Query builder error', error);
        console.error(chalk.red(`\n❌ Error: ${(error as Error).message}`));
      }
    }
  }

  /**
   * Select query type
   */
  private async selectQueryType(): Promise<void> {
    const { type } = await inquirer.prompt({
      type: 'list',
      name: 'type',
      message: 'Select query type:',
      choices: [
        { name: '🔍 SELECT - Query data', value: QueryType.SELECT },
        { name: '➕ INSERT - Add new data', value: QueryType.INSERT },
        { name: '✏️  UPDATE - Modify existing data', value: QueryType.UPDATE },
        { name: '🗑️  DELETE - Remove data', value: QueryType.DELETE }
      ]
    });

    this.state.type = type;
    this.emitStateChanged();
  }

  /**
   * Build SELECT query
   */
  private async buildSelectQuery(): Promise<void> {
    // Select table
    await this.selectTable();

    // Select columns
    await this.selectColumns();

    // Add joins (optional)
    await this.addJoins();

    // Add conditions (optional)
    await this.addConditions();

    // Add GROUP BY (optional)
    await this.addGroupBy();

    // Add HAVING (optional)
    if (this.state.groupBy.length > 0) {
      await this.addHaving();
    }

    // Add ORDER BY (optional)
    await this.addOrderBy();

    // Add LIMIT/OFFSET (optional)
    await this.addLimitOffset();

    // Distinct option
    await this.addDistinct();
  }

  /**
   * Build INSERT query
   */
  private async buildInsertQuery(): Promise<void> {
    // Select table
    await this.selectTable();

    // Get table columns
    const columns = await this.getTableColumns(this.state.table);

    // Select columns to insert
    const { selectedColumns } = await inquirer.prompt({
      type: 'checkbox',
      name: 'selectedColumns',
      message: 'Select columns to insert:',
      choices: columns,
      validate: (input: readonly unknown[]) => (input && input.length > 0) || 'Select at least one column'
    });

    this.state.columns = selectedColumns;

    // Enter values
    this.state.values = {};
    for (const column of selectedColumns) {
      const { value } = await inquirer.prompt({
        type: 'input',
        name: 'value',
        message: `Enter value for ${chalk.cyan(column)}:`,
        validate: (input: string) => input.trim() !== '' || 'Value cannot be empty'
      });
      this.state.values[column] = this.parseValue(value);
    }

    this.emitStateChanged();
  }

  /**
   * Build UPDATE query
   */
  private async buildUpdateQuery(): Promise<void> {
    // Select table
    await this.selectTable();

    // Get table columns
    const columns = await this.getTableColumns(this.state.table);

    // Select columns to update
    const { selectedColumns } = await inquirer.prompt({
      type: 'checkbox',
      name: 'selectedColumns',
      message: 'Select columns to update:',
      choices: columns,
      validate: (input: readonly unknown[]) => (input && input.length > 0) || 'Select at least one column'
    });

    this.state.columns = selectedColumns;

    // Enter new values
    this.state.values = {};
    for (const column of selectedColumns) {
      const { value } = await inquirer.prompt({
        type: 'input',
        name: 'value',
        message: `Enter new value for ${chalk.cyan(column)}:`,
        validate: (input: string) => input.trim() !== '' || 'Value cannot be empty'
      });
      this.state.values[column] = this.parseValue(value);
    }

    // Add conditions (required for UPDATE)
    console.log(chalk.yellow('\n⚠️  WHERE clause is required for UPDATE'));
    await this.addConditions(true);

    this.emitStateChanged();
  }

  /**
   * Build DELETE query
   */
  private async buildDeleteQuery(): Promise<void> {
    // Select table
    await this.selectTable();

    // Add conditions (required for DELETE)
    console.log(chalk.yellow('\n⚠️  WHERE clause is required for DELETE'));
    await this.addConditions(true);

    this.emitStateChanged();
  }

  /**
   * Select table
   */
  private async selectTable(): Promise<void> {
    const tables = await this.getTableList();

    const { table } = await inquirer.prompt({
      type: 'list',
      name: 'table',
      message: 'Select table:',
      choices: tables,
      pageSize: 15
    });

    this.state.table = table;
    this.emitStateChanged();
  }

  /**
   * Select columns
   */
  private async selectColumns(): Promise<void> {
    const columns = await this.getTableColumns(this.state.table);

    const { selectedColumns } = await inquirer.prompt({
      type: 'checkbox',
      name: 'selectedColumns',
      message: 'Select columns (leave empty for all):',
      choices: [
        { name: '* (All columns)', value: '*' } as const,
        ...columns.map(c => typeof c === 'string' ? { name: c, value: c } as const : c)
      ]
    });

    if (selectedColumns.includes('*') || selectedColumns.length === 0) {
      this.state.columns = ['*'];
    } else {
      this.state.columns = selectedColumns;
    }

    this.emitStateChanged();
  }

  /**
   * Add joins
   */
  private async addJoins(): Promise<void> {
    let addMore = true;

    while (addMore) {
      const { shouldAddJoin } = await inquirer.prompt({
        type: 'confirm',
        name: 'shouldAddJoin',
        message: 'Add JOIN clause?',
        default: false
      });

      if (!shouldAddJoin) {
        break;
      }

      const tables = await this.getTableList();
      const availableTables = tables.filter(t =>
        t !== this.state.table && !this.state.joins.some(j => j.table === t)
      );

      const { joinType } = await inquirer.prompt({
        type: 'list',
        name: 'joinType',
        message: 'Select JOIN type:',
        choices: Object.values(JoinType)
      });

      const { table } = await inquirer.prompt({
        type: 'list',
        name: 'table',
        message: 'Select table to join:',
        choices: availableTables
      });

      const { on } = await inquirer.prompt({
        type: 'input',
        name: 'on',
        message: 'Enter ON condition (e.g., table1.id = table2.user_id):',
        validate: (input: string) => input.trim() !== '' || 'ON condition is required'
      });

      this.state.joins.push({
        type: joinType,
        table: table,
        on: on
      });

      this.emitStateChanged();
      console.log(chalk.green(`✓ Added ${joinType} ${table}`));
    }
  }

  /**
   * Add conditions
   */
  private async addConditions(required = false): Promise<void> {
    let addMore = required;

    while (true) {
      if (!required) {
        const { shouldAddCondition } = await inquirer.prompt({
          type: 'confirm',
          name: 'shouldAddCondition',
          message: 'Add WHERE condition?',
          default: addMore
        });

        if (!shouldAddCondition) {
          break;
        }
      }

      const columns = await this.getTableColumns(this.state.table);

      const { column } = await inquirer.prompt({
        type: 'list',
        name: 'column',
        message: 'Select column:',
        choices: columns
      });

      const { operator } = await inquirer.prompt({
        type: 'list',
        name: 'operator',
        message: 'Select operator:',
        choices: Object.values(ConditionOperator)
      });

      let value: any;
      let secondValue: any;

      // Get value(s) based on operator
      if (![ConditionOperator.IS_NULL, ConditionOperator.IS_NOT_NULL].includes(operator)) {
        if (operator === ConditionOperator.BETWEEN) {
          const { value1 } = await inquirer.prompt({
            type: 'input',
            name: 'value1',
            message: 'Enter first value:',
            validate: (input: string) => input.trim() !== '' || 'Value is required'
          });

          const { value2 } = await inquirer.prompt({
            type: 'input',
            name: 'value2',
            message: 'Enter second value:',
            validate: (input: string) => input.trim() !== '' || 'Value is required'
          });

          value = this.parseValue(value1);
          secondValue = this.parseValue(value2);
        } else {
          const { inputValue } = await inquirer.prompt({
            type: 'input',
            name: 'inputValue',
            message: 'Enter value:',
            validate: (input: string) => input.trim() !== '' || 'Value is required'
          });
          value = this.parseValue(inputValue);
        }
      }

      // Logical operator for subsequent conditions
      let logicalOperator: 'AND' | 'OR' | undefined;
      if (this.state.conditions.length > 0) {
        const { logical } = await inquirer.prompt({
          type: 'list',
          name: 'logical',
          message: 'Combine with previous condition using:',
          choices: ['AND', 'OR']
        });
        logicalOperator = logical;
      }

      this.state.conditions.push({
        column: column,
        operator: operator,
        value,
        secondValue,
        logicalOperator
      });

      this.emitStateChanged();
      console.log(chalk.green(`✓ Added condition: ${column} ${operator}`));

      addMore = false;
      required = false;
    }
  }

  /**
   * Add GROUP BY
   */
  private async addGroupBy(): Promise<void> {
    const { shouldAddGroupBy } = await inquirer.prompt({
      type: 'confirm',
      name: 'shouldAddGroupBy',
      message: 'Add GROUP BY clause?',
      default: false
    });

    if (!shouldAddGroupBy) {
      return;
    }

    const columns = await this.getTableColumns(this.state.table);

    const { groupColumns } = await inquirer.prompt({
      type: 'checkbox',
      name: 'groupColumns',
      message: 'Select columns to group by:',
      choices: columns,
      validate: (input: readonly unknown[]) => (input && input.length > 0) || 'Select at least one column'
    });

    this.state.groupBy = groupColumns;
    this.emitStateChanged();
  }

  /**
   * Add HAVING clause
   */
  private async addHaving(): Promise<void> {
    const { shouldAddHaving } = await inquirer.prompt({
      type: 'confirm',
      name: 'shouldAddHaving',
      message: 'Add HAVING clause?',
      default: false
    });

    if (!shouldAddHaving) {
      return;
    }

    // Similar to WHERE conditions but for HAVING
    const columns = await this.getTableColumns(this.state.table);

    const { column } = await inquirer.prompt({
      type: 'list',
      name: 'column',
      message: 'Select aggregate column:',
      choices: columns
    });

    const { operator } = await inquirer.prompt({
      type: 'list',
      name: 'operator',
      message: 'Select operator:',
      choices: Object.values(ConditionOperator)
    });

    const { value } = await inquirer.prompt({
      type: 'input',
      name: 'value',
      message: 'Enter value:',
      validate: (input: string) => input.trim() !== '' || 'Value is required'
    });

    this.state.having.push({
      column: column,
      operator: operator,
      value: this.parseValue(value)
    });

    this.emitStateChanged();
  }

  /**
   * Add ORDER BY
   */
  private async addOrderBy(): Promise<void> {
    let addMore = true;

    while (addMore) {
      const { shouldAddOrder } = await inquirer.prompt({
        type: 'confirm',
        name: 'shouldAddOrder',
        message: 'Add ORDER BY clause?',
        default: this.state.orderBy.length === 0
      });

      if (!shouldAddOrder) {
        break;
      }

      const columns = await this.getTableColumns(this.state.table);

      const { column } = await inquirer.prompt({
        type: 'list',
        name: 'column',
        message: 'Select column to order by:',
        choices: columns
      });

      const { direction } = await inquirer.prompt({
        type: 'list',
        name: 'direction',
        message: 'Select order direction:',
        choices: ['ASC', 'DESC']
      });

      this.state.orderBy.push({
        column: column,
        direction: direction
      });

      this.emitStateChanged();
      console.log(chalk.green(`✓ Added ORDER BY ${column} ${direction}`));

      addMore = false;
    }
  }

  /**
   * Add LIMIT and OFFSET
   */
  private async addLimitOffset(): Promise<void> {
    const { shouldAddLimit } = await inquirer.prompt({
      type: 'confirm',
      name: 'shouldAddLimit',
      message: 'Add LIMIT clause?',
      default: false
    });

    if (!shouldAddLimit) {
      return;
    }

    const { limit } = await inquirer.prompt({
      type: 'number',
      name: 'limit',
      message: 'Enter LIMIT:',
      validate: (input: number | undefined) => (input !== undefined && input > 0) ? true : 'LIMIT must be positive'
    });

    const { shouldAddOffset } = await inquirer.prompt({
      type: 'confirm',
      name: 'shouldAddOffset',
      message: 'Add OFFSET?',
      default: false
    });

    this.state.limit = limit;

    if (shouldAddOffset) {
      const { offset } = await inquirer.prompt({
        type: 'number',
        name: 'offset',
        message: 'Enter OFFSET:',
        validate: (input: number | undefined) => (input !== undefined && input >= 0) ? true : 'OFFSET must be non-negative'
      });
      this.state.offset = offset;
    }

    this.emitStateChanged();
  }

  /**
   * Add DISTINCT option
   */
  private async addDistinct(): Promise<void> {
    const { distinct } = await inquirer.prompt({
      type: 'confirm',
      name: 'distinct',
      message: 'Use DISTINCT?',
      default: false
    });

    this.state.distinct = distinct;
    this.emitStateChanged();
  }

  /**
   * Preview and execute query
   */
  private async previewAndExecute(): Promise<void> {
    const sql = this.generateSQL();

    console.log(chalk.cyan('\n📋 Generated Query:'));
    console.log(chalk.white(this.formatSQL(sql)));

    const { action } = await inquirer.prompt({
      type: 'list',
      name: 'action',
      message: 'What would you like to do?',
      choices: [
        { name: '▶️  Execute query', value: 'execute' },
        { name: '💾 Save as draft', value: 'save' },
        { name: '📋 Copy to clipboard', value: 'copy' },
        { name: '✏️  Edit query', value: 'edit' },
        { name: '❌ Cancel', value: 'cancel' }
      ]
    });

    switch (action) {
      case 'execute':
        await this.executeQuery(sql);
        break;
      case 'save':
        await this.saveDraft();
        break;
      case 'copy':
        console.log(chalk.green('✓ Query copied to clipboard'));
        console.log(sql);
        break;
      case 'edit':
        await this.editQuery(sql);
        break;
      case 'cancel':
        console.log(chalk.yellow('Query cancelled'));
        break;
    }
  }

  /**
   * Execute query
   */
  private async executeQuery(sql: string): Promise<void> {
    try {
      console.log(chalk.cyan('\n⏳ Executing query...'));

      const startTime = Date.now();
      const activeConn = this.connectionManager.getActive();
      const result = await this.queryExecutor.execute(sql);
      const executionTime = Date.now() - startTime;

      this.emit('queryExecuted', result);

      // Add to history
      this.addToHistory(sql, true, result.rowCount);

      // Display results
      console.log(chalk.green(`\n✓ Query executed successfully in ${executionTime}ms`));
      console.log(chalk.cyan(`Rows: ${result.rowCount}`));

      if (result.rows && result.rows.length > 0) {
        const formatted = ResultFormatter.format(result.rows, {
          format: 'table',
          colors: true,
          headers: true
        });
        console.log('\n' + formatted);
      }
    } catch (error) {
      this.emit('error', error as Error);
      this.addToHistory(sql, false, 0, (error as Error).message);
      console.error(chalk.red(`\n❌ Query failed: ${(error as Error).message}`));
    }
  }

  /**
   * Edit query manually
   */
  private async editQuery(sql: string): Promise<void> {
    const { editedSQL } = await inquirer.prompt({
      type: 'editor',
      name: 'editedSQL',
      message: 'Edit query:',
      default: sql
    });

    if (editedSQL.trim()) {
      await this.executeQuery(editedSQL.trim());
    }
  }

  /**
   * Generate SQL from state
   */
  generateSQL(): string {
    const dbType = this.connectionManager.getActive()?.type;

    switch (this.state.type) {
      case QueryType.SELECT:
        return this.generateSelectSQL(dbType);
      case QueryType.INSERT:
        return this.generateInsertSQL(dbType);
      case QueryType.UPDATE:
        return this.generateUpdateSQL(dbType);
      case QueryType.DELETE:
        return this.generateDeleteSQL(dbType);
      default:
        throw new Error(`Unsupported query type: ${this.state.type}`);
    }
  }

  /**
   * Generate SELECT SQL
   */
  private generateSelectSQL(dbType?: DatabaseType): string {
    let sql = 'SELECT ';

    if (this.state.distinct) {
      sql += 'DISTINCT ';
    }

    sql += this.state.columns.join(', ');
    sql += ` FROM ${this.escapeIdentifier(this.state.table || '', dbType)}`;

    // JOINs
    for (const join of this.state.joins) {
      sql += ` ${join.type} ${this.escapeIdentifier(join.table, dbType)} ON ${join.on}`;
    }

    // WHERE
    if (this.state.conditions.length > 0) {
      sql += ' WHERE ' + this.buildConditions(this.state.conditions, dbType);
    }

    // GROUP BY
    if (this.state.groupBy.length > 0) {
      sql += ' GROUP BY ' + this.state.groupBy.map(c => this.escapeIdentifier(c, dbType)).join(', ');
    }

    // HAVING
    if (this.state.having.length > 0) {
      sql += ' HAVING ' + this.buildConditions(this.state.having, dbType);
    }

    // ORDER BY
    if (this.state.orderBy.length > 0) {
      sql += ' ORDER BY ' + this.state.orderBy.map(o =>
        `${this.escapeIdentifier(o.column, dbType)} ${o.direction}`
      ).join(', ');
    }

    // LIMIT/OFFSET
    if (this.state.limit !== undefined) {
      sql += ` LIMIT ${this.state.limit}`;
    }
    if (this.state.offset !== undefined) {
      sql += ` OFFSET ${this.state.offset}`;
    }

    return sql;
  }

  /**
   * Generate INSERT SQL
   */
  private generateInsertSQL(dbType?: DatabaseType): string {
    if (!this.state.values) {
      throw new Error('No values provided for INSERT');
    }

    const columns = this.state.columns.map(c => this.escapeIdentifier(c, dbType));
    const values = this.state.columns.map(c => this.escapeValue(this.state.values![c], dbType));

    return `INSERT INTO ${this.escapeIdentifier(this.state.table, dbType)} (${columns.join(', ')}) VALUES (${values.join(', ')})`;
  }

  /**
   * Generate UPDATE SQL
   */
  private generateUpdateSQL(dbType?: DatabaseType): string {
    if (!this.state.values) {
      throw new Error('No values provided for UPDATE');
    }

    const setClauses = this.state.columns.map(c =>
      `${this.escapeIdentifier(c, dbType)} = ${this.escapeValue(this.state.values![c], dbType)}`
    );

    let sql = `UPDATE ${this.escapeIdentifier(this.state.table, dbType)} SET ${setClauses.join(', ')}`;

    if (this.state.conditions.length > 0) {
      sql += ' WHERE ' + this.buildConditions(this.state.conditions, dbType);
    }

    return sql;
  }

  /**
   * Generate DELETE SQL
   */
  private generateDeleteSQL(dbType?: DatabaseType): string {
    let sql = `DELETE FROM ${this.escapeIdentifier(this.state.table, dbType)}`;

    if (this.state.conditions.length > 0) {
      sql += ' WHERE ' + this.buildConditions(this.state.conditions, dbType);
    }

    return sql;
  }

  /**
   * Build conditions string
   */
  private buildConditions(conditions: QueryCondition[], dbType?: DatabaseType): string {
    return conditions.map((condition, index) => {
      let clause = '';

      // Add logical operator
      if (index > 0 && condition.logicalOperator) {
        clause += ` ${condition.logicalOperator} `;
      }

      const column = this.escapeIdentifier(condition.column, dbType);

      switch (condition.operator) {
        case ConditionOperator.IS_NULL:
          clause += `${column} IS NULL`;
          break;
        case ConditionOperator.IS_NOT_NULL:
          clause += `${column} IS NOT NULL`;
          break;
        case ConditionOperator.BETWEEN:
          clause += `${column} BETWEEN ${this.escapeValue(condition.value, dbType)} AND ${this.escapeValue(condition.secondValue, dbType)}`;
          break;
        case ConditionOperator.IN:
        case ConditionOperator.NOT_IN:
          clause += `${column} ${condition.operator} (${this.escapeValue(condition.value, dbType)})`;
          break;
        default:
          clause += `${column} ${condition.operator} ${this.escapeValue(condition.value, dbType)}`;
      }

      return clause;
    }).join('');
  }

  /**
   * Escape identifier (table/column name)
   */
  private escapeIdentifier(identifier: string, dbType?: DatabaseType): string {
    if (identifier === '*') {
      return '*';
    }

    switch (dbType) {
      case DatabaseType.POSTGRESQL:
        return `"${identifier}"`;
      case DatabaseType.MYSQL:
        return `\`${identifier}\``;
      case DatabaseType.SQLITE:
        return `"${identifier}"`;
      case DatabaseType.MONGODB:
        return identifier; // MongoDB uses different syntax
      default:
        return `"${identifier}"`;
    }
  }

  /**
   * Escape value
   */
  private escapeValue(value: any, dbType?: DatabaseType): string {
    if (value === null || value === undefined) {
      return 'NULL';
    }

    if (typeof value === 'number') {
      return value.toString();
    }

    if (typeof value === 'boolean') {
      return value ? 'TRUE' : 'FALSE';
    }

    if (Array.isArray(value)) {
      return value.map(v => this.escapeValue(v, dbType)).join(', ');
    }

    // String - escape single quotes
    const escaped = value.toString().replace(/'/g, "''");
    return `'${escaped}'`;
  }

  /**
   * Parse value from string input
   */
  private parseValue(input: string): any {
    // Try to parse as JSON first
    try {
      return JSON.parse(input);
    } catch {
      // Return as string if not valid JSON
      return input;
    }
  }

  /**
   * Format SQL for display
   */
  private formatSQL(sql: string): string {
    return sql
      .replace(/\bSELECT\b/gi, chalk.blue('SELECT'))
      .replace(/\bFROM\b/gi, chalk.blue('FROM'))
      .replace(/\bWHERE\b/gi, chalk.blue('WHERE'))
      .replace(/\bJOIN\b/gi, chalk.blue('JOIN'))
      .replace(/\bON\b/gi, chalk.blue('ON'))
      .replace(/\bGROUP BY\b/gi, chalk.blue('GROUP BY'))
      .replace(/\bHAVING\b/gi, chalk.blue('HAVING'))
      .replace(/\bORDER BY\b/gi, chalk.blue('ORDER BY'))
      .replace(/\bLIMIT\b/gi, chalk.blue('LIMIT'))
      .replace(/\bOFFSET\b/gi, chalk.blue('OFFSET'))
      .replace(/\bINSERT INTO\b/gi, chalk.blue('INSERT INTO'))
      .replace(/\bVALUES\b/gi, chalk.blue('VALUES'))
      .replace(/\bUPDATE\b/gi, chalk.blue('UPDATE'))
      .replace(/\bSET\b/gi, chalk.blue('SET'))
      .replace(/\bDELETE FROM\b/gi, chalk.blue('DELETE FROM'));
  }

  /**
   * Save draft
   */
  async saveDraft(name?: string): Promise<void> {
    if (!name) {
      const { draftName } = await inquirer.prompt({
        type: 'input',
        name: 'draftName',
        message: 'Enter draft name:',
        validate: (input: string) => input.trim() !== '' || 'Name is required'
      });
      name = draftName;
    }

    const draft: QueryDraft = {
      id: uuidv4(),
      name: name || 'untitled',
      state: { ...this.state },
      createdAt: Date.now(),
      updatedAt: Date.now(),
      sql: this.generateSQL()
    };

    const draftPath = path.join(this.draftsDir, `${draft.id}.json`);
    await fs.writeFile(draftPath, JSON.stringify(draft, null, 2));

    this.emit('draftSaved', draft);
    console.log(chalk.green(`✓ Draft saved: ${name}`));
  }

  /**
   * Load draft
   */
  async loadDraft(draftId?: string): Promise<void> {
    if (!draftId) {
      const drafts = await this.listDrafts();

      if (drafts.length === 0) {
        console.log(chalk.yellow('No drafts found'));
        return;
      }

      const { selectedDraft } = await inquirer.prompt({
        type: 'list',
        name: 'selectedDraft',
        message: 'Select draft to load:',
        choices: drafts.map(d => ({
          name: `${d.name} (${new Date(d.updatedAt).toLocaleString()})`,
          value: d.id
        }))
      });

      draftId = selectedDraft;
    }

    const draftPath = path.join(this.draftsDir, `${draftId}.json`);
    const draftContent = await fs.readFile(draftPath, 'utf-8');
    const draft: QueryDraft = JSON.parse(draftContent);

    this.state = draft.state;
    this.emit('draftLoaded', draft);

    console.log(chalk.green(`✓ Draft loaded: ${draft.name}`));

    await this.previewAndExecute();
  }

  /**
   * List all drafts
   */
  async listDrafts(): Promise<QueryDraft[]> {
    try {
      const files = await fs.readdir(this.draftsDir);
      const drafts: QueryDraft[] = [];

      for (const file of files) {
        if (file.endsWith('.json')) {
          const content = await fs.readFile(path.join(this.draftsDir, file), 'utf-8');
          drafts.push(JSON.parse(content));
        }
      }

      return drafts.sort((a, b) => b.updatedAt - a.updatedAt);
    } catch (error) {
      return [];
    }
  }

  /**
   * Apply template
   */
  async applyTemplate(templateId?: string): Promise<void> {
    if (!templateId) {
      const { selectedTemplate } = await inquirer.prompt({
        type: 'list',
        name: 'selectedTemplate',
        message: 'Select template:',
        choices: this.templates.map(t => ({
          name: `${t.name} - ${t.description}`,
          value: t.id
        }))
      });

      templateId = selectedTemplate;
    }

    const template = this.templates.find(t => t.id === templateId);
    if (!template) {
      throw new Error('Template not found');
    }

    // Merge template state with current state
    this.state = {
      ...this.state,
      ...template.state
    };

    this.emit('templateApplied', template);
    console.log(chalk.green(`✓ Template applied: ${template.name}`));
  }

  /**
   * Load templates
   */
  private async loadTemplates(): Promise<void> {
    try {
      const content = await fs.readFile(this.templatesFile, 'utf-8');
      this.templates = JSON.parse(content);
    } catch (error) {
      // Initialize with default templates
      this.templates = this.getDefaultTemplates();
      await this.saveTemplates();
    }
  }

  /**
   * Save templates
   */
  private async saveTemplates(): Promise<void> {
    await fs.writeFile(this.templatesFile, JSON.stringify(this.templates, null, 2));
  }

  /**
   * Get default templates
   */
  private getDefaultTemplates(): QueryTemplate[] {
    return [
      {
        id: 'select-all',
        name: 'Select All',
        description: 'Select all columns from a table',
        category: 'basic',
        state: {
          type: QueryType.SELECT,
          columns: ['*'],
          conditions: [],
          joins: [],
          orderBy: [],
          groupBy: [],
          having: []
        }
      },
      {
        id: 'select-with-limit',
        name: 'Select with Limit',
        description: 'Select with pagination',
        category: 'basic',
        state: {
          type: QueryType.SELECT,
          columns: ['*'],
          conditions: [],
          joins: [],
          orderBy: [],
          groupBy: [],
          having: [],
          limit: 10
        }
      },
      {
        id: 'count-all',
        name: 'Count Records',
        description: 'Count all records in a table',
        category: 'aggregate',
        state: {
          type: QueryType.SELECT,
          columns: ['COUNT(*) as count'],
          conditions: [],
          joins: [],
          orderBy: [],
          groupBy: [],
          having: []
        }
      }
    ];
  }

  /**
   * Add to history
   */
  private addToHistory(sql: string, success: boolean, rowCount?: number, error?: string): void {
    const entry: QueryHistoryEntry = {
      id: uuidv4(),
      sql,
      state: { ...this.state },
      executedAt: Date.now(),
      success,
      rowCount,
      error
    };

    this.history.unshift(entry);

    // Keep only last 100 entries
    if (this.history.length > 100) {
      this.history = this.history.slice(0, 100);
    }

    this.saveHistory();
  }

  /**
   * Load history
   */
  private async loadHistory(): Promise<void> {
    try {
      const content = await fs.readFile(this.historyFile, 'utf-8');
      this.history = JSON.parse(content);
    } catch (error) {
      this.history = [];
    }
  }

  /**
   * Save history
   */
  private async saveHistory(): Promise<void> {
    try {
      await fs.writeFile(this.historyFile, JSON.stringify(this.history, null, 2));
    } catch (error) {
      logger.error('Failed to save history', error);
    }
  }

  /**
   * Show history
   */
  async showHistory(): Promise<void> {
    if (this.history.length === 0) {
      console.log(chalk.yellow('No query history'));
      return;
    }

    console.log(chalk.cyan.bold('\n📜 Query History\n'));

    for (const entry of this.history.slice(0, 20)) {
      const status = entry.success ? chalk.green('✓') : chalk.red('✗');
      const date = new Date(entry.executedAt).toLocaleString();
      console.log(`${status} ${chalk.gray(date)} - ${entry.sql.substring(0, 80)}...`);
      if (entry.rowCount !== undefined) {
        console.log(`  ${chalk.gray(`Rows: ${entry.rowCount}`)}`);
      }
      if (entry.error) {
        console.log(`  ${chalk.red(entry.error)}`);
      }
      console.log();
    }
  }

  /**
   * Get table list
   */
  private async getTableList(): Promise<string[]> {
    const connection = this.connectionManager.getActive();
    if (!connection) {
      throw new Error('No active connection');
    }

    // This would typically query the database for tables
    // For now, return mock data
    return ['users', 'posts', 'comments', 'categories', 'tags'];
  }

  /**
   * Get table columns
   */
  private async getTableColumns(table: string): Promise<string[]> {
    const connection = this.connectionManager.getActive();
    if (!connection) {
      throw new Error('No active connection');
    }

    // This would typically query the database for columns
    // For now, return mock data based on table
    const mockColumns: Record<string, string[]> = {
      users: ['id', 'username', 'email', 'created_at', 'updated_at'],
      posts: ['id', 'user_id', 'title', 'content', 'created_at'],
      comments: ['id', 'post_id', 'user_id', 'content', 'created_at'],
      categories: ['id', 'name', 'description'],
      tags: ['id', 'name', 'slug']
    };

    return mockColumns[table] || ['id', 'name', 'created_at'];
  }

  /**
   * Emit state changed event
   */
  private emitStateChanged(): void {
    this.emit('stateChanged', { ...this.state });
  }

  /**
   * Reset builder
   */
  reset(): void {
    this.state = this.createEmptyState();
    this.emitStateChanged();
  }

  /**
   * Get current state
   */
  getState(): QueryBuilderState {
    return { ...this.state };
  }

  /**
   * Set state
   */
  setState(state: Partial<QueryBuilderState>): void {
    this.state = { ...this.state, ...state };
    this.emitStateChanged();
  }
}
