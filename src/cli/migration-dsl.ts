/**
 * Migration DSL - Declarative API for Database Migrations
 * Provides fluent interface for building zero-downtime migrations
 *
 * Example:
 * ```typescript
 * migration('add-email-verified')
 *   .addColumn('users', 'email_verified', 'BOOLEAN')
 *   .withDefault(false)
 *   .nullable()
 *   .backfill('email_verified = false')
 *   .makeNonNullable()
 *   .validate()
 *   .commit();
 * ```
 */

import { DatabaseType } from './database-manager';
import * as yaml from 'js-yaml';
import * as fs from 'fs/promises';
import * as path from 'path';

interface MigrationPhase {
  phase: number;
  description: string;
  operations: Operation[];
  validation: ValidationRule[];
  rollbackOperations?: Operation[];
  timeout?: number;
}

interface Operation {
  type: string;
  table?: string;
  column?: string;
  oldColumn?: string;
  newColumn?: string;
  dataType?: string;
  nullable?: boolean;
  default?: any;
  indexName?: string;
  constraintName?: string;
  sql?: string;
  concurrent?: boolean;
  columns?: string[];
}

interface ValidationRule {
  check: string;
  table?: string;
  column?: string;
  indexName?: string;
  sql?: string;
  errorMessage?: string;
}

interface MigrationDefinition {
  name: string;
  database: DatabaseType;
  description?: string;
  phases: MigrationPhase[];
  metadata?: {
    author?: string;
    created?: number;
    tags?: string[];
  };
}

/**
 * Migration Builder - Fluent API for creating migrations
 */
export class MigrationBuilder {
  private definition: MigrationDefinition;
  private currentPhase: MigrationPhase = {
    phase: 0,
    description: '',
    operations: [],
    validation: []
  };
  private phaseCounter: number = 0;
  private currentOperation?: Operation;
  private currentTable?: string;
  private currentColumn?: string;

  constructor(
    name: string,
    database: DatabaseType = DatabaseType.POSTGRESQL,
    description?: string
  ) {
    this.definition = {
      name,
      database,
      description,
      phases: [],
      metadata: {
        created: Date.now()
      }
    };

    // Start first phase
    this.nextPhase('Initial phase');
  }

  /**
   * Start a new phase
   */
  phase(description: string): this {
    return this.nextPhase(description);
  }

  private nextPhase(description: string): this {
    // Save current phase if it has operations
    if (this.currentPhase && this.currentPhase.operations.length > 0) {
      this.definition.phases.push(this.currentPhase);
    }

    this.phaseCounter++;
    this.currentPhase = {
      phase: this.phaseCounter,
      description,
      operations: [],
      validation: []
    };

    return this;
  }

  /**
   * Add a column (Expand phase)
   */
  addColumn(table: string, column: string, dataType: string): this {
    this.currentTable = table;
    this.currentColumn = column;

    this.currentOperation = {
      type: 'add_column',
      table,
      column,
      dataType,
      nullable: true // Default to nullable for expand pattern
    };

    this.currentPhase.operations.push(this.currentOperation);

    // Add rollback operation
    if (!this.currentPhase.rollbackOperations) {
      this.currentPhase.rollbackOperations = [];
    }
    this.currentPhase.rollbackOperations.unshift({
      type: 'drop_column',
      table,
      column
    });

    return this;
  }

  /**
   * Make column nullable
   */
  nullable(): this {
    if (this.currentOperation) {
      this.currentOperation.nullable = true;
    }
    return this;
  }

  /**
   * Make column non-nullable
   */
  notNullable(): this {
    if (this.currentOperation) {
      this.currentOperation.nullable = false;
    }
    return this;
  }

  /**
   * Set default value
   */
  withDefault(value: any): this {
    if (this.currentOperation) {
      this.currentOperation.default = value;
    }
    return this;
  }

  /**
   * Drop a column (Contract phase)
   */
  dropColumn(table: string, column: string): this {
    this.currentOperation = {
      type: 'drop_column',
      table,
      column
    };

    this.currentPhase.operations.push(this.currentOperation);
    return this;
  }

  /**
   * Rename a column (multi-phase)
   */
  renameColumn(table: string, oldColumn: string, newColumn: string, dataType: string): this {
    // This creates a multi-phase rename using expand/contract pattern

    // Phase 1: Add new column
    this.phase(`Add new column ${newColumn}`);
    this.addColumn(table, newColumn, dataType).nullable();

    // Phase 2: Enable dual-write
    this.phase('Enable dual-write');
    this.enableDualWrite(table, oldColumn, newColumn);

    // Phase 3: Backfill new column
    this.phase(`Backfill ${newColumn} from ${oldColumn}`);
    this.backfill(table, `${newColumn} = ${oldColumn}`);

    // Phase 4: Switch reads to new column
    this.phase('Switch to new column');
    this.addValidation('column_exists', table, newColumn);

    // Phase 5: Drop old column
    this.phase(`Drop old column ${oldColumn}`);
    this.disableDualWrite(table, oldColumn, newColumn);
    this.dropColumn(table, oldColumn);

    return this;
  }

  /**
   * Change column type (multi-phase)
   */
  changeColumnType(
    table: string,
    column: string,
    oldType: string,
    newType: string
  ): this {
    const tempColumn = `${column}_new`;

    // Phase 1: Add new column with new type
    this.phase(`Add ${tempColumn} with type ${newType}`);
    this.addColumn(table, tempColumn, newType).nullable();

    // Phase 2: Enable dual-write
    this.phase('Enable dual-write for type migration');
    this.enableDualWrite(table, column, tempColumn);

    // Phase 3: Backfill and validate
    this.phase('Backfill with type conversion');
    this.backfill(table, `${tempColumn} = CAST(${column} AS ${newType})`);
    this.validateBackfill(table, tempColumn);

    // Phase 4: Switch to new column
    this.phase('Switch to new column');
    this.dropColumn(table, column);
    this.renameColumnDirect(table, tempColumn, column);

    return this;
  }

  /**
   * Direct rename (use with caution - not zero-downtime)
   */
  private renameColumnDirect(table: string, oldColumn: string, newColumn: string): this {
    this.currentOperation = {
      type: 'rename_column',
      table,
      oldColumn,
      newColumn
    };

    this.currentPhase.operations.push(this.currentOperation);
    return this;
  }

  /**
   * Backfill data
   */
  backfill(table: string, sql: string): this {
    this.currentOperation = {
      type: 'backfill',
      table,
      sql
    };

    this.currentPhase.operations.push(this.currentOperation);
    return this;
  }

  /**
   * Make column non-nullable (separate phase after backfill)
   */
  makeNonNullable(): this {
    if (!this.currentTable || !this.currentColumn) {
      throw new Error('makeNonNullable requires a current column context');
    }

    // Start new phase for constraint change
    this.phase(`Make ${this.currentColumn} NOT NULL`);

    this.currentOperation = {
      type: 'custom_sql',
      sql: `ALTER TABLE ${this.currentTable} ALTER COLUMN ${this.currentColumn} SET NOT NULL`
    };

    this.currentPhase.operations.push(this.currentOperation);
    return this;
  }

  /**
   * Add an index
   */
  addIndex(
    table: string,
    indexName: string,
    columns: string[],
    options: { concurrent?: boolean } = {}
  ): this {
    this.currentOperation = {
      type: 'add_index',
      table,
      indexName,
      columns,
      concurrent: options.concurrent !== false // Default to concurrent
    };

    this.currentPhase.operations.push(this.currentOperation);

    // Add rollback
    if (!this.currentPhase.rollbackOperations) {
      this.currentPhase.rollbackOperations = [];
    }
    this.currentPhase.rollbackOperations.unshift({
      type: 'drop_index',
      indexName,
      table,
      concurrent: options.concurrent
    });

    return this;
  }

  /**
   * Drop an index
   */
  dropIndex(indexName: string, table?: string, options: { concurrent?: boolean } = {}): this {
    this.currentOperation = {
      type: 'drop_index',
      indexName,
      table,
      concurrent: options.concurrent
    };

    this.currentPhase.operations.push(this.currentOperation);
    return this;
  }

  /**
   * Add a constraint
   */
  addConstraint(table: string, constraintName: string, sql: string): this {
    this.currentOperation = {
      type: 'add_constraint',
      table,
      constraintName,
      sql
    };

    this.currentPhase.operations.push(this.currentOperation);

    // Add rollback
    if (!this.currentPhase.rollbackOperations) {
      this.currentPhase.rollbackOperations = [];
    }
    this.currentPhase.rollbackOperations.unshift({
      type: 'drop_constraint',
      table,
      constraintName
    });

    return this;
  }

  /**
   * Drop a constraint
   */
  dropConstraint(table: string, constraintName: string): this {
    this.currentOperation = {
      type: 'drop_constraint',
      table,
      constraintName
    };

    this.currentPhase.operations.push(this.currentOperation);
    return this;
  }

  /**
   * Enable dual-write for column migration
   */
  enableDualWrite(table: string, oldColumn: string, newColumn: string): this {
    this.currentOperation = {
      type: 'dual_write_enable',
      table,
      oldColumn,
      newColumn
    };

    this.currentPhase.operations.push(this.currentOperation);
    return this;
  }

  /**
   * Disable dual-write
   */
  disableDualWrite(table: string, oldColumn: string, newColumn: string): this {
    this.currentOperation = {
      type: 'dual_write_disable',
      table,
      oldColumn,
      newColumn
    };

    this.currentPhase.operations.push(this.currentOperation);
    return this;
  }

  /**
   * Execute custom SQL
   */
  customSQL(sql: string): this {
    this.currentOperation = {
      type: 'custom_sql',
      sql
    };

    this.currentPhase.operations.push(this.currentOperation);
    return this;
  }

  /**
   * Add validation rule
   */
  addValidation(
    check: string,
    table?: string,
    column?: string,
    options: { errorMessage?: string; sql?: string } = {}
  ): this {
    const validation: ValidationRule = {
      check,
      table,
      column,
      errorMessage: options.errorMessage,
      sql: options.sql
    };

    this.currentPhase.validation.push(validation);
    return this;
  }

  /**
   * Validate column exists
   */
  validateColumnExists(table: string, column: string, errorMessage?: string): this {
    return this.addValidation('column_exists', table, column, { errorMessage });
  }

  /**
   * Validate column not exists
   */
  validateColumnNotExists(table: string, column: string, errorMessage?: string): this {
    return this.addValidation('column_not_exists', table, column, { errorMessage });
  }

  /**
   * Validate backfill completion
   */
  validateBackfill(table: string, column: string): this {
    const sql = `SELECT COUNT(*) as count FROM ${table} WHERE ${column} IS NULL`;
    return this.addValidation('custom', table, column, {
      sql,
      errorMessage: `Backfill incomplete: ${column} has NULL values`
    });
  }

  /**
   * Validate data integrity
   */
  validateDataIntegrity(sql: string, errorMessage?: string): this {
    return this.addValidation('custom', undefined, undefined, { sql, errorMessage });
  }

  /**
   * Shorthand for common validation
   */
  validate(): this {
    if (this.currentTable && this.currentColumn) {
      this.validateColumnExists(this.currentTable, this.currentColumn);
    }
    return this;
  }

  /**
   * Set phase timeout
   */
  setTimeout(milliseconds: number): this {
    this.currentPhase.timeout = milliseconds;
    return this;
  }

  /**
   * Set migration metadata
   */
  setAuthor(author: string): this {
    if (!this.definition.metadata) {
      this.definition.metadata = {};
    }
    this.definition.metadata.author = author;
    return this;
  }

  /**
   * Add tags
   */
  addTags(...tags: string[]): this {
    if (!this.definition.metadata) {
      this.definition.metadata = {};
    }
    if (!this.definition.metadata.tags) {
      this.definition.metadata.tags = [];
    }
    this.definition.metadata.tags.push(...tags);
    return this;
  }

  /**
   * Build the migration definition
   */
  build(): MigrationDefinition {
    // Add current phase if it has operations
    if (this.currentPhase && this.currentPhase.operations.length > 0) {
      this.definition.phases.push(this.currentPhase);
    }

    return this.definition;
  }

  /**
   * Export to YAML
   */
  toYAML(): string {
    const definition = this.build();
    return yaml.dump({ migration: definition }, {
      indent: 2,
      lineWidth: 100,
      noRefs: true
    });
  }

  /**
   * Save to file
   */
  async save(directory: string): Promise<string> {
    const definition = this.build();
    const timestamp = Date.now();
    const filename = `${timestamp}_${definition.name.replace(/\s+/g, '_')}.yaml`;
    const filepath = path.join(directory, filename);

    await fs.mkdir(directory, { recursive: true });
    await fs.writeFile(filepath, this.toYAML(), 'utf-8');

    return filepath;
  }

  /**
   * Commit migration (alias for save)
   */
  async commit(directory: string = './migrations'): Promise<string> {
    return this.save(directory);
  }
}

/**
 * Create a new migration
 */
export function migration(
  name: string,
  database: DatabaseType = DatabaseType.POSTGRESQL,
  description?: string
): MigrationBuilder {
  return new MigrationBuilder(name, database, description);
}

/**
 * Common migration patterns
 */
export class MigrationPatterns {
  /**
   * Pattern: Add nullable column
   */
  static addNullableColumn(
    table: string,
    column: string,
    dataType: string,
    defaultValue?: any
  ): MigrationBuilder {
    const builder = migration(`add-${column}-to-${table}`)
      .phase(`Add ${column} column`)
      .addColumn(table, column, dataType)
      .nullable();

    if (defaultValue !== undefined) {
      builder.withDefault(defaultValue);
    }

    return builder.validate();
  }

  /**
   * Pattern: Add NOT NULL column with default
   */
  static addRequiredColumn(
    table: string,
    column: string,
    dataType: string,
    defaultValue: any
  ): MigrationBuilder {
    return migration(`add-required-${column}-to-${table}`)
      .phase('Add column as nullable with default')
      .addColumn(table, column, dataType)
      .nullable()
      .withDefault(defaultValue)
      .validate()

      .phase('Backfill existing rows')
      .backfill(table, `${column} = ${defaultValue}`)
      .validateBackfill(table, column)

      .phase('Make column NOT NULL')
      .makeNonNullable();
  }

  /**
   * Pattern: Remove column safely
   */
  static removeColumn(
    table: string,
    column: string
  ): MigrationBuilder {
    return migration(`remove-${column}-from-${table}`)
      .phase('Stop writing to column')
      .validateColumnExists(table, column)

      .phase('Remove from queries')
      // Application deployment happens here

      .phase('Drop column')
      .dropColumn(table, column)
      .validateColumnNotExists(table, column);
  }

  /**
   * Pattern: Rename column with zero downtime
   */
  static safeRenameColumn(
    table: string,
    oldColumn: string,
    newColumn: string,
    dataType: string
  ): MigrationBuilder {
    return migration(`rename-${oldColumn}-to-${newColumn}`)
      .renameColumn(table, oldColumn, newColumn, dataType);
  }

  /**
   * Pattern: Change column type
   */
  static changeColumnType(
    table: string,
    column: string,
    oldType: string,
    newType: string
  ): MigrationBuilder {
    return migration(`change-${column}-type-to-${newType}`)
      .changeColumnType(table, column, oldType, newType);
  }

  /**
   * Pattern: Add index concurrently
   */
  static addConcurrentIndex(
    table: string,
    indexName: string,
    columns: string[]
  ): MigrationBuilder {
    return migration(`add-index-${indexName}`)
      .phase('Create index concurrently')
      .addIndex(table, indexName, columns, { concurrent: true })
      .addValidation('index_exists', table, undefined, { errorMessage: `Index ${indexName} was not created` });
  }

  /**
   * Pattern: Add foreign key constraint
   */
  static addForeignKey(
    table: string,
    column: string,
    refTable: string,
    refColumn: string = 'id'
  ): MigrationBuilder {
    const constraintName = `fk_${table}_${column}`;

    return migration(`add-foreign-key-${constraintName}`)
      .phase('Add foreign key constraint')
      .addConstraint(
        table,
        constraintName,
        `FOREIGN KEY (${column}) REFERENCES ${refTable}(${refColumn})`
      );
  }

  /**
   * Pattern: Add unique constraint
   */
  static addUniqueConstraint(
    table: string,
    columns: string[]
  ): MigrationBuilder {
    const constraintName = `uq_${table}_${columns.join('_')}`;

    return migration(`add-unique-${constraintName}`)
      .phase('Add unique constraint')
      .addConstraint(
        table,
        constraintName,
        `UNIQUE (${columns.join(', ')})`
      );
  }

  /**
   * Pattern: Split column into multiple columns
   */
  static splitColumn(
    table: string,
    sourceColumn: string,
    targetColumns: Array<{ name: string; type: string; extract: string }>
  ): MigrationBuilder {
    const builder = migration(`split-${sourceColumn}`)
      .phase('Add new columns')

    // Add all target columns
    targetColumns.forEach(col => {
      builder.addColumn(table, col.name, col.type).nullable();
    });

    // Backfill each column
    builder.phase('Backfill data from source column');
    targetColumns.forEach(col => {
      builder.backfill(table, `${col.name} = ${col.extract}`);
    });

    // Validate
    builder.phase('Validate data migration');
    targetColumns.forEach(col => {
      builder.validateBackfill(table, col.name);
    });

    // Drop source column
    builder
      .phase('Drop source column')
      .dropColumn(table, sourceColumn);

    return builder;
  }

  /**
   * Pattern: Merge columns
   */
  static mergeColumns(
    table: string,
    sourceColumns: string[],
    targetColumn: string,
    targetType: string,
    mergeExpression: string
  ): MigrationBuilder {
    return migration(`merge-columns-to-${targetColumn}`)
      .phase('Add target column')
      .addColumn(table, targetColumn, targetType)
      .nullable()

      .phase('Backfill merged data')
      .backfill(table, `${targetColumn} = ${mergeExpression}`)
      .validateBackfill(table, targetColumn)

      .phase('Drop source columns')
      .customSQL(
        sourceColumns.map(col => `ALTER TABLE ${table} DROP COLUMN ${col}`).join('; ')
      );
  }
}

/**
 * Load migration from YAML file
 */
export async function loadMigrationFromFile(filepath: string): Promise<MigrationDefinition> {
  const content = await fs.readFile(filepath, 'utf-8');
  const parsed = yaml.load(content) as any;
  return parsed.migration as MigrationDefinition;
}

/**
 * Example usage and exports
 */
export default {
  migration,
  MigrationBuilder,
  MigrationPatterns,
  loadMigrationFromFile
};
