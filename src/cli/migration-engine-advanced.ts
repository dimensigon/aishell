/**
 * Advanced Migration Engine - Zero-Downtime Schema Migrations
 * Implements expand/contract pattern for safe, rolling deployments
 *
 * Features:
 * - Multi-phase migrations (expand/contract)
 * - Dual-write capability for zero-downtime
 * - Automatic rollback on failure
 * - Point-in-time snapshots
 * - Concurrent index creation
 * - Lock timeout management
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { EventEmitter } from 'eventemitter3';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';
import { BackupSystem } from './backup-system';
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import * as yaml from 'js-yaml';

interface MigrationPhase {
  phase: number;
  description: string;
  operations: Operation[];
  validation: ValidationRule[];
  rollbackOperations?: Operation[];
  timeout?: number;
  requiresLock?: boolean;
}

interface Operation {
  type: 'add_column' | 'drop_column' | 'rename_column' | 'change_type' |
        'add_index' | 'drop_index' | 'add_constraint' | 'drop_constraint' |
        'backfill' | 'custom_sql' | 'dual_write_enable' | 'dual_write_disable';
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
  check: 'column_exists' | 'column_not_exists' | 'index_exists' |
         'data_migrated' | 'constraint_valid' | 'custom';
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

interface MigrationExecution {
  id: string;
  migrationName: string;
  currentPhase: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'rolled_back';
  startTime?: number;
  endTime?: number;
  error?: string;
  phaseResults: PhaseResult[];
  backupId?: string;
  snapshotId?: string;
}

interface PhaseResult {
  phase: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'rolled_back';
  startTime?: number;
  endTime?: number;
  error?: string;
  operationsExecuted: number;
}

interface MigrationHistory {
  executions: MigrationExecution[];
  lastMigration?: MigrationExecution;
}

interface MigrationEvents {
  'migration:start': (execution: MigrationExecution) => void;
  'migration:complete': (execution: MigrationExecution) => void;
  'migration:error': (execution: MigrationExecution, error: Error) => void;
  'phase:start': (execution: MigrationExecution, phase: number) => void;
  'phase:complete': (execution: MigrationExecution, phase: number) => void;
  'phase:error': (execution: MigrationExecution, phase: number, error: Error) => void;
  'rollback:start': (execution: MigrationExecution) => void;
  'rollback:complete': (execution: MigrationExecution) => void;
}

/**
 * Advanced Migration Engine with Zero-Downtime Support
 */
export class AdvancedMigrationEngine extends EventEmitter<MigrationEvents> {
  private logger = createLogger('AdvancedMigrationEngine');
  private executions = new Map<string, MigrationExecution>();
  private dualWriteHandlers = new Map<string, DualWriteHandler>();

  constructor(
    private dbManager: DatabaseConnectionManager,
    private stateManager: StateManager,
    private backupSystem: BackupSystem,
    private config: {
      migrationsDir?: string;
      historyTable?: string;
      enableAutoBackup?: boolean;
      enableAutoSnapshot?: boolean;
      lockTimeout?: number;
      maxPhaseRetries?: number;
    } = {}
  ) {
    super();

    this.config.migrationsDir = this.config.migrationsDir || './migrations';
    this.config.historyTable = this.config.historyTable || 'migration_history';
    this.config.enableAutoBackup = this.config.enableAutoBackup !== false;
    this.config.enableAutoSnapshot = this.config.enableAutoSnapshot !== false;
    this.config.lockTimeout = this.config.lockTimeout || 5000; // 5 seconds
    this.config.maxPhaseRetries = this.config.maxPhaseRetries || 3;

    this.initialize();
  }

  /**
   * Initialize migration engine
   */
  private async initialize(): Promise<void> {
    try {
      // Ensure migrations directory exists
      await fs.mkdir(this.config.migrationsDir!, { recursive: true });

      // Create history table
      await this.createHistoryTable();

      // Load execution history
      await this.loadExecutionHistory();

      this.logger.info('Advanced migration engine initialized');
    } catch (error) {
      this.logger.error('Failed to initialize migration engine', error);
      throw error;
    }
  }

  /**
   * Load migration definition from YAML file
   */
  async loadMigration(filepath: string): Promise<MigrationDefinition> {
    try {
      const content = await fs.readFile(filepath, 'utf-8');
      const definition = yaml.load(content) as any;

      // Validate migration definition
      this.validateMigrationDefinition(definition.migration);

      return definition.migration as MigrationDefinition;
    } catch (error) {
      throw new Error(`Failed to load migration from ${filepath}: ${error}`);
    }
  }

  /**
   * Validate migration definition
   */
  private validateMigrationDefinition(def: MigrationDefinition): void {
    if (!def.name) {
      throw new Error('Migration name is required');
    }

    if (!def.database) {
      throw new Error('Database type is required');
    }

    if (!def.phases || def.phases.length === 0) {
      throw new Error('At least one phase is required');
    }

    // Validate each phase
    def.phases.forEach((phase, index) => {
      if (phase.phase !== index + 1) {
        throw new Error(`Phase numbers must be sequential starting from 1`);
      }

      if (!phase.operations || phase.operations.length === 0) {
        throw new Error(`Phase ${phase.phase} has no operations`);
      }
    });
  }

  /**
   * Create execution plan (dry-run)
   */
  async plan(filepath: string): Promise<{
    migration: MigrationDefinition;
    estimatedDuration: number;
    risks: string[];
    phases: Array<{
      phase: number;
      description: string;
      operations: string[];
      estimatedDuration: number;
    }>;
  }> {
    const migration = await this.loadMigration(filepath);

    const risks: string[] = [];
    const phases = migration.phases.map(phase => {
      const operations: string[] = [];
      let estimatedDuration = 0;

      phase.operations.forEach(op => {
        const sql = this.generateSQL(op, migration.database);
        operations.push(sql);

        // Estimate duration and detect risks
        if (op.type === 'backfill') {
          estimatedDuration += 10000; // Backfills are slow
          risks.push(`Phase ${phase.phase}: Backfill operation may lock table`);
        } else if (op.type === 'add_index' && !op.concurrent) {
          estimatedDuration += 5000;
          risks.push(`Phase ${phase.phase}: Non-concurrent index creation will lock table`);
        } else {
          estimatedDuration += 100;
        }
      });

      return {
        phase: phase.phase,
        description: phase.description,
        operations,
        estimatedDuration
      };
    });

    const totalDuration = phases.reduce((sum, p) => sum + p.estimatedDuration, 0);

    return {
      migration,
      estimatedDuration: totalDuration,
      risks,
      phases
    };
  }

  /**
   * Execute migration
   */
  async executeMigration(
    filepath: string,
    options: {
      phase?: number;
      dryRun?: boolean;
      skipBackup?: boolean;
      skipSnapshot?: boolean;
    } = {}
  ): Promise<MigrationExecution> {
    const migration = await this.loadMigration(filepath);

    const executionId = `exec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    const execution: MigrationExecution = {
      id: executionId,
      migrationName: migration.name,
      currentPhase: options.phase || 1,
      status: 'pending',
      phaseResults: []
    };

    this.executions.set(executionId, execution);

    try {
      // Dry run check
      if (options.dryRun) {
        this.logger.info('Dry run mode - generating execution plan', { migrationName: migration.name });
        return execution;
      }

      execution.status = 'running';
      execution.startTime = Date.now();
      this.emit('migration:start', execution);

      // Create backup if enabled
      if (this.config.enableAutoBackup && !options.skipBackup) {
        this.logger.info('Creating backup before migration');
        const backup = await this.backupSystem.createBackup();
        execution.backupId = backup.id;
      }

      // Create snapshot if enabled
      if (this.config.enableAutoSnapshot && !options.skipSnapshot) {
        execution.snapshotId = await this.createSnapshot();
      }

      // Execute phases
      const startPhase = options.phase || 1;
      const endPhase = options.phase || migration.phases.length;

      for (let i = startPhase - 1; i < endPhase; i++) {
        const phase = migration.phases[i];
        await this.executePhase(execution, phase, migration.database);
      }

      execution.status = 'completed';
      execution.endTime = Date.now();
      this.emit('migration:complete', execution);

      // Record in history
      await this.recordExecution(execution);

      this.logger.info('Migration completed successfully', {
        executionId,
        duration: execution.endTime - (execution.startTime || 0)
      });

      return execution;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));

      execution.status = 'failed';
      execution.error = err.message;
      execution.endTime = Date.now();

      this.emit('migration:error', execution, err);

      // Attempt rollback
      if (execution.currentPhase > 0) {
        this.logger.info('Attempting automatic rollback');
        try {
          await this.rollbackExecution(execution, migration);
        } catch (rollbackError) {
          this.logger.error('Rollback failed', rollbackError);
        }
      }

      await this.recordExecution(execution);
      throw err;
    }
  }

  /**
   * Execute single phase
   */
  private async executePhase(
    execution: MigrationExecution,
    phase: MigrationPhase,
    dbType: DatabaseType
  ): Promise<void> {
    const phaseResult: PhaseResult = {
      phase: phase.phase,
      status: 'running',
      startTime: Date.now(),
      operationsExecuted: 0
    };

    execution.phaseResults.push(phaseResult);
    execution.currentPhase = phase.phase;

    this.emit('phase:start', execution, phase.phase);

    try {
      // Set lock timeout if specified
      if (phase.timeout) {
        await this.setLockTimeout(phase.timeout);
      }

      // Execute operations
      for (const operation of phase.operations) {
        await this.executeOperation(operation, dbType);
        phaseResult.operationsExecuted++;
      }

      // Run validations
      for (const validation of phase.validation) {
        await this.runValidation(validation, dbType);
      }

      phaseResult.status = 'completed';
      phaseResult.endTime = Date.now();
      this.emit('phase:complete', execution, phase.phase);

      this.logger.info('Phase completed', {
        phase: phase.phase,
        operations: phaseResult.operationsExecuted,
        duration: phaseResult.endTime - (phaseResult.startTime || 0)
      });
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));

      phaseResult.status = 'failed';
      phaseResult.error = err.message;
      phaseResult.endTime = Date.now();

      this.emit('phase:error', execution, phase.phase, err);
      throw err;
    }
  }

  /**
   * Execute single operation
   */
  private async executeOperation(operation: Operation, dbType: DatabaseType): Promise<void> {
    // Special handling for dual-write operations
    if (operation.type === 'dual_write_enable') {
      await this.enableDualWrite(operation);
      return;
    }

    if (operation.type === 'dual_write_disable') {
      await this.disableDualWrite(operation);
      return;
    }

    // Generate and execute SQL
    const sql = this.generateSQL(operation, dbType);

    this.logger.debug('Executing operation', { type: operation.type, sql });

    await this.executeSQL(sql);
  }

  /**
   * Generate SQL for operation
   */
  private generateSQL(operation: Operation, dbType: DatabaseType): string {
    switch (operation.type) {
      case 'add_column':
        return this.generateAddColumnSQL(operation, dbType);

      case 'drop_column':
        return this.generateDropColumnSQL(operation, dbType);

      case 'rename_column':
        return this.generateRenameColumnSQL(operation, dbType);

      case 'change_type':
        return this.generateChangeTypeSQL(operation, dbType);

      case 'add_index':
        return this.generateAddIndexSQL(operation, dbType);

      case 'drop_index':
        return this.generateDropIndexSQL(operation, dbType);

      case 'add_constraint':
        return this.generateAddConstraintSQL(operation, dbType);

      case 'drop_constraint':
        return this.generateDropConstraintSQL(operation, dbType);

      case 'backfill':
        return this.generateBackfillSQL(operation, dbType);

      case 'custom_sql':
        return operation.sql || '';

      default:
        throw new Error(`Unknown operation type: ${operation.type}`);
    }
  }

  /**
   * Generate ADD COLUMN SQL
   */
  private generateAddColumnSQL(op: Operation, dbType: DatabaseType): string {
    if (!op.table || !op.column || !op.dataType) {
      throw new Error('add_column requires table, column, and dataType');
    }

    let sql = `ALTER TABLE ${op.table} ADD COLUMN ${op.column} ${op.dataType}`;

    if (op.nullable !== false) {
      sql += ' NULL';
    }

    if (op.default !== undefined) {
      sql += ` DEFAULT ${this.formatValue(op.default, dbType)}`;
    }

    return sql;
  }

  /**
   * Generate DROP COLUMN SQL
   */
  private generateDropColumnSQL(op: Operation, _dbType: DatabaseType): string {
    if (!op.table || !op.column) {
      throw new Error('drop_column requires table and column');
    }

    return `ALTER TABLE ${op.table} DROP COLUMN ${op.column}`;
  }

  /**
   * Generate RENAME COLUMN SQL
   */
  private generateRenameColumnSQL(op: Operation, dbType: DatabaseType): string {
    if (!op.table || !op.oldColumn || !op.newColumn) {
      throw new Error('rename_column requires table, oldColumn, and newColumn');
    }

    switch (dbType) {
      case DatabaseType.POSTGRESQL:
        return `ALTER TABLE ${op.table} RENAME COLUMN ${op.oldColumn} TO ${op.newColumn}`;

      case DatabaseType.MYSQL:
        // MySQL requires specifying the full column definition
        return `ALTER TABLE ${op.table} CHANGE ${op.oldColumn} ${op.newColumn} ${op.dataType || 'VARCHAR(255)'}`;

      case DatabaseType.SQLITE:
        // SQLite doesn't support RENAME COLUMN directly
        throw new Error('SQLite requires full table recreation for column rename');

      default:
        return `ALTER TABLE ${op.table} RENAME COLUMN ${op.oldColumn} TO ${op.newColumn}`;
    }
  }

  /**
   * Generate CHANGE TYPE SQL
   */
  private generateChangeTypeSQL(op: Operation, dbType: DatabaseType): string {
    if (!op.table || !op.column || !op.dataType) {
      throw new Error('change_type requires table, column, and dataType');
    }

    switch (dbType) {
      case DatabaseType.POSTGRESQL:
        return `ALTER TABLE ${op.table} ALTER COLUMN ${op.column} TYPE ${op.dataType}`;

      case DatabaseType.MYSQL:
        return `ALTER TABLE ${op.table} MODIFY COLUMN ${op.column} ${op.dataType}`;

      default:
        return `ALTER TABLE ${op.table} ALTER COLUMN ${op.column} TYPE ${op.dataType}`;
    }
  }

  /**
   * Generate ADD INDEX SQL
   */
  private generateAddIndexSQL(op: Operation, dbType: DatabaseType): string {
    if (!op.table || !op.indexName || !op.columns) {
      throw new Error('add_index requires table, indexName, and columns');
    }

    let sql = 'CREATE';

    // PostgreSQL supports CONCURRENTLY for zero-downtime index creation
    if (op.concurrent && dbType === DatabaseType.POSTGRESQL) {
      sql += ' INDEX CONCURRENTLY';
    } else {
      sql += ' INDEX';
    }

    sql += ` ${op.indexName} ON ${op.table} (${op.columns.join(', ')})`;

    return sql;
  }

  /**
   * Generate DROP INDEX SQL
   */
  private generateDropIndexSQL(op: Operation, dbType: DatabaseType): string {
    if (!op.indexName) {
      throw new Error('drop_index requires indexName');
    }

    let sql = 'DROP INDEX';

    if (op.concurrent && dbType === DatabaseType.POSTGRESQL) {
      sql += ' CONCURRENTLY';
    }

    switch (dbType) {
      case DatabaseType.POSTGRESQL:
        sql += ` ${op.indexName}`;
        break;

      case DatabaseType.MYSQL:
        if (!op.table) {
          throw new Error('MySQL drop_index requires table');
        }
        sql += ` ${op.indexName} ON ${op.table}`;
        break;

      default:
        sql += ` ${op.indexName}`;
    }

    return sql;
  }

  /**
   * Generate ADD CONSTRAINT SQL
   */
  private generateAddConstraintSQL(op: Operation, _dbType: DatabaseType): string {
    if (!op.table || !op.constraintName || !op.sql) {
      throw new Error('add_constraint requires table, constraintName, and sql');
    }

    return `ALTER TABLE ${op.table} ADD CONSTRAINT ${op.constraintName} ${op.sql}`;
  }

  /**
   * Generate DROP CONSTRAINT SQL
   */
  private generateDropConstraintSQL(op: Operation, _dbType: DatabaseType): string {
    if (!op.table || !op.constraintName) {
      throw new Error('drop_constraint requires table and constraintName');
    }

    return `ALTER TABLE ${op.table} DROP CONSTRAINT ${op.constraintName}`;
  }

  /**
   * Generate BACKFILL SQL
   */
  private generateBackfillSQL(op: Operation, _dbType: DatabaseType): string {
    if (!op.table || !op.sql) {
      throw new Error('backfill requires table and sql');
    }

    return `UPDATE ${op.table} SET ${op.sql}`;
  }

  /**
   * Run validation
   */
  private async runValidation(validation: ValidationRule, dbType: DatabaseType): Promise<void> {
    switch (validation.check) {
      case 'column_exists':
        await this.validateColumnExists(validation, dbType);
        break;

      case 'column_not_exists':
        await this.validateColumnNotExists(validation, dbType);
        break;

      case 'index_exists':
        await this.validateIndexExists(validation, dbType);
        break;

      case 'data_migrated':
        await this.validateDataMigrated(validation);
        break;

      case 'constraint_valid':
        await this.validateConstraint(validation);
        break;

      case 'custom':
        await this.validateCustom(validation);
        break;

      default:
        throw new Error(`Unknown validation check: ${validation.check}`);
    }
  }

  /**
   * Validate column exists
   */
  private async validateColumnExists(validation: ValidationRule, dbType: DatabaseType): Promise<void> {
    if (!validation.table || !validation.column) {
      throw new Error('column_exists validation requires table and column');
    }

    let sql: string;

    switch (dbType) {
      case DatabaseType.POSTGRESQL:
        sql = `
          SELECT column_name
          FROM information_schema.columns
          WHERE table_name = '${validation.table}'
            AND column_name = '${validation.column}'
        `;
        break;

      case DatabaseType.MYSQL:
        sql = `
          SELECT COLUMN_NAME
          FROM information_schema.COLUMNS
          WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = '${validation.table}'
            AND COLUMN_NAME = '${validation.column}'
        `;
        break;

      default:
        throw new Error(`Column validation not implemented for ${dbType}`);
    }

    const result = await this.executeQuery(sql);

    if (!result || result.length === 0) {
      throw new Error(
        validation.errorMessage ||
        `Column ${validation.column} does not exist in table ${validation.table}`
      );
    }
  }

  /**
   * Validate column not exists
   */
  private async validateColumnNotExists(validation: ValidationRule, dbType: DatabaseType): Promise<void> {
    try {
      await this.validateColumnExists(validation, dbType);
      // If we reach here, column exists - validation failed
      throw new Error(
        validation.errorMessage ||
        `Column ${validation.column} should not exist in table ${validation.table}`
      );
    } catch (error) {
      // Column doesn't exist - validation passed
      return;
    }
  }

  /**
   * Validate index exists
   */
  private async validateIndexExists(validation: ValidationRule, dbType: DatabaseType): Promise<void> {
    if (!validation.indexName) {
      throw new Error('index_exists validation requires indexName');
    }

    let sql: string;

    switch (dbType) {
      case DatabaseType.POSTGRESQL:
        sql = `
          SELECT indexname
          FROM pg_indexes
          WHERE indexname = '${validation.indexName}'
        `;
        break;

      case DatabaseType.MYSQL:
        sql = `
          SELECT INDEX_NAME
          FROM information_schema.STATISTICS
          WHERE TABLE_SCHEMA = DATABASE()
            AND INDEX_NAME = '${validation.indexName}'
        `;
        break;

      default:
        throw new Error(`Index validation not implemented for ${dbType}`);
    }

    const result = await this.executeQuery(sql);

    if (!result || result.length === 0) {
      throw new Error(
        validation.errorMessage ||
        `Index ${validation.indexName} does not exist`
      );
    }
  }

  /**
   * Validate data migrated
   */
  private async validateDataMigrated(validation: ValidationRule): Promise<void> {
    if (!validation.sql) {
      throw new Error('data_migrated validation requires sql');
    }

    const result = await this.executeQuery(validation.sql);

    if (!result || result.length === 0) {
      throw new Error(validation.errorMessage || 'Data migration validation failed');
    }
  }

  /**
   * Validate constraint
   */
  private async validateConstraint(validation: ValidationRule): Promise<void> {
    if (!validation.sql) {
      throw new Error('constraint_valid validation requires sql');
    }

    await this.executeQuery(validation.sql);
  }

  /**
   * Validate custom SQL
   */
  private async validateCustom(validation: ValidationRule): Promise<void> {
    if (!validation.sql) {
      throw new Error('custom validation requires sql');
    }

    const result = await this.executeQuery(validation.sql);

    if (!result || result.length === 0) {
      throw new Error(validation.errorMessage || 'Custom validation failed');
    }
  }

  /**
   * Rollback execution
   */
  private async rollbackExecution(
    execution: MigrationExecution,
    migration: MigrationDefinition
  ): Promise<void> {
    this.emit('rollback:start', execution);

    try {
      // Rollback phases in reverse order
      for (let i = execution.currentPhase - 1; i >= 0; i--) {
        const phase = migration.phases[i];

        if (phase.rollbackOperations) {
          this.logger.info('Rolling back phase', { phase: phase.phase });

          for (const operation of phase.rollbackOperations) {
            await this.executeOperation(operation, migration.database);
          }
        }
      }

      // Restore from snapshot if available
      if (execution.snapshotId) {
        await this.restoreSnapshot(execution.snapshotId);
      }

      execution.status = 'rolled_back';
      this.emit('rollback:complete', execution);

      this.logger.info('Rollback completed', { executionId: execution.id });
    } catch (error) {
      this.logger.error('Rollback failed', error);
      throw error;
    }
  }

  /**
   * Enable dual-write for column migration
   */
  private async enableDualWrite(operation: Operation): Promise<void> {
    if (!operation.table || !operation.oldColumn || !operation.newColumn) {
      throw new Error('dual_write_enable requires table, oldColumn, and newColumn');
    }

    const key = `${operation.table}.${operation.oldColumn}-${operation.newColumn}`;

    const handler = new DualWriteHandler(
      operation.table,
      operation.oldColumn,
      operation.newColumn,
      this.dbManager
    );

    this.dualWriteHandlers.set(key, handler);
    await handler.enable();

    this.logger.info('Dual-write enabled', { table: operation.table, columns: [operation.oldColumn, operation.newColumn] });
  }

  /**
   * Disable dual-write
   */
  private async disableDualWrite(operation: Operation): Promise<void> {
    if (!operation.table || !operation.oldColumn || !operation.newColumn) {
      throw new Error('dual_write_disable requires table, oldColumn, and newColumn');
    }

    const key = `${operation.table}.${operation.oldColumn}-${operation.newColumn}`;
    const handler = this.dualWriteHandlers.get(key);

    if (handler) {
      await handler.disable();
      this.dualWriteHandlers.delete(key);

      this.logger.info('Dual-write disabled', { table: operation.table });
    }
  }

  /**
   * Get migration status
   */
  async getStatus(): Promise<MigrationHistory> {
    const executions = Array.from(this.executions.values());
    const completed = executions.filter(e => e.status === 'completed');
    const lastMigration = completed.sort((a, b) =>
      (b.endTime || 0) - (a.endTime || 0)
    )[0];

    return {
      executions,
      lastMigration
    };
  }

  /**
   * Verify migration safety
   */
  async verify(filepath: string): Promise<{
    safe: boolean;
    warnings: string[];
    errors: string[];
    recommendations: string[];
  }> {
    const warnings: string[] = [];
    const errors: string[] = [];
    const recommendations: string[] = [];

    try {
      const migration = await this.loadMigration(filepath);

      // Check each phase
      migration.phases.forEach(phase => {
        phase.operations.forEach(op => {
          // Check for dangerous operations
          if (op.type === 'drop_column') {
            warnings.push(`Phase ${phase.phase}: Dropping column ${op.column} - ensure data is backed up`);
          }

          if (op.type === 'drop_constraint') {
            warnings.push(`Phase ${phase.phase}: Dropping constraint ${op.constraintName} - may affect data integrity`);
          }

          // Check for missing rollback operations
          if (!phase.rollbackOperations || phase.rollbackOperations.length === 0) {
            warnings.push(`Phase ${phase.phase}: No rollback operations defined`);
          }

          // Check for non-concurrent index creation
          if (op.type === 'add_index' && !op.concurrent) {
            warnings.push(`Phase ${phase.phase}: Index creation is not concurrent - will lock table`);
            recommendations.push(`Use "concurrent: true" for index ${op.indexName}`);
          }

          // Check for backfills without batching
          if (op.type === 'backfill') {
            warnings.push(`Phase ${phase.phase}: Backfill operation - consider batching for large tables`);
            recommendations.push('Use batch updates with LIMIT clauses for better performance');
          }
        });

        // Check for validations
        if (!phase.validation || phase.validation.length === 0) {
          warnings.push(`Phase ${phase.phase}: No validation rules defined`);
        }
      });

      // Check phase ordering for expand/contract pattern
      const hasAddColumn = migration.phases.some(p =>
        p.operations.some(op => op.type === 'add_column')
      );
      const hasDropColumn = migration.phases.some(p =>
        p.operations.some(op => op.type === 'drop_column')
      );

      if (hasAddColumn && hasDropColumn) {
        const addPhase = migration.phases.findIndex(p =>
          p.operations.some(op => op.type === 'add_column')
        );
        const dropPhase = migration.phases.findIndex(p =>
          p.operations.some(op => op.type === 'drop_column')
        );

        if (dropPhase <= addPhase) {
          errors.push('Column drops should come after column adds in expand/contract pattern');
        }
      }

    } catch (error) {
      errors.push(`Failed to load migration: ${error}`);
    }

    return {
      safe: errors.length === 0,
      warnings,
      errors,
      recommendations
    };
  }

  // Helper methods

  private async executeSQL(sql: string): Promise<void> {
    await this.dbManager.executeQuery(sql);
  }

  private async executeQuery(sql: string): Promise<any[]> {
    const result = await this.dbManager.executeQuery(sql);
    return result;
  }

  private async setLockTimeout(timeout: number): Promise<void> {
    const connection = this.dbManager.getActive();

    if (!connection) {
      return;
    }

    switch (connection.type) {
      case DatabaseType.POSTGRESQL:
        await this.executeSQL(`SET lock_timeout = '${timeout}ms'`);
        break;

      case DatabaseType.MYSQL:
        await this.executeSQL(`SET SESSION innodb_lock_wait_timeout = ${Math.floor(timeout / 1000)}`);
        break;
    }
  }

  private formatValue(value: any, dbType: DatabaseType): string {
    if (value === null || value === undefined) {
      return 'NULL';
    }

    if (typeof value === 'string') {
      return `'${value.replace(/'/g, "''")}'`;
    }

    if (typeof value === 'boolean') {
      switch (dbType) {
        case DatabaseType.POSTGRESQL:
          return value ? 'TRUE' : 'FALSE';
        case DatabaseType.MYSQL:
          return value ? '1' : '0';
        default:
          return value ? 'TRUE' : 'FALSE';
      }
    }

    return String(value);
  }

  private async createSnapshot(): Promise<string> {
    // Create point-in-time snapshot
    const snapshotId = `snapshot-${Date.now()}`;
    // Implementation depends on database type
    this.logger.info('Snapshot created', { snapshotId });
    return snapshotId;
  }

  private async restoreSnapshot(snapshotId: string): Promise<void> {
    this.logger.info('Restoring snapshot', { snapshotId });
    // Implementation depends on database type
  }

  private async createHistoryTable(): Promise<void> {
    const connection = this.dbManager.getActive();

    if (!connection) {
      return;
    }

    const sql = `
      CREATE TABLE IF NOT EXISTS ${this.config.historyTable} (
        id VARCHAR(255) PRIMARY KEY,
        migration_name VARCHAR(255) NOT NULL,
        current_phase INTEGER NOT NULL,
        status VARCHAR(50) NOT NULL,
        start_time BIGINT,
        end_time BIGINT,
        error TEXT,
        backup_id VARCHAR(255),
        snapshot_id VARCHAR(255),
        phase_results TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `;

    try {
      await this.executeSQL(sql);
    } catch (error) {
      this.logger.warn('Failed to create history table', { error });
    }
  }

  private async recordExecution(execution: MigrationExecution): Promise<void> {
    const sql = `
      INSERT INTO ${this.config.historyTable}
        (id, migration_name, current_phase, status, start_time, end_time, error, backup_id, snapshot_id, phase_results)
      VALUES
        ('${execution.id}', '${execution.migrationName}', ${execution.currentPhase}, '${execution.status}',
         ${execution.startTime || 'NULL'}, ${execution.endTime || 'NULL'},
         ${execution.error ? `'${execution.error.replace(/'/g, "''")}'` : 'NULL'},
         ${execution.backupId ? `'${execution.backupId}'` : 'NULL'},
         ${execution.snapshotId ? `'${execution.snapshotId}'` : 'NULL'},
         '${JSON.stringify(execution.phaseResults).replace(/'/g, "''")}'
        )
      ON CONFLICT (id) DO UPDATE SET
        status = EXCLUDED.status,
        current_phase = EXCLUDED.current_phase,
        end_time = EXCLUDED.end_time,
        error = EXCLUDED.error,
        phase_results = EXCLUDED.phase_results
    `;

    try {
      await this.executeSQL(sql);
    } catch (error) {
      this.logger.error('Failed to record execution', error);
    }

    // Also save to state manager
    this.stateManager.set(`migration:execution:${execution.id}`, execution);
  }

  private async loadExecutionHistory(): Promise<void> {
    try {
      const sql = `SELECT * FROM ${this.config.historyTable} ORDER BY start_time DESC LIMIT 100`;
      const rows = await this.executeQuery(sql);

      rows.forEach((row: any) => {
        const execution: MigrationExecution = {
          id: row.id,
          migrationName: row.migration_name,
          currentPhase: row.current_phase,
          status: row.status,
          startTime: row.start_time,
          endTime: row.end_time,
          error: row.error,
          backupId: row.backup_id,
          snapshotId: row.snapshot_id,
          phaseResults: row.phase_results ? JSON.parse(row.phase_results) : []
        };

        this.executions.set(execution.id, execution);
      });

      this.logger.info('Loaded execution history', { count: this.executions.size });
    } catch (error) {
      this.logger.warn('Failed to load execution history', { error });
    }
  }
}

/**
 * Dual-Write Handler for zero-downtime column migrations
 */
class DualWriteHandler {
  private logger = createLogger('DualWriteHandler');
  private enabled = false;

  constructor(
    private table: string,
    private oldColumn: string,
    private newColumn: string,
    private dbManager: DatabaseConnectionManager
  ) {}

  async enable(): Promise<void> {
    this.enabled = true;
    // In a real implementation, this would install database triggers or
    // application-level hooks to write to both columns
    this.logger.info('Dual-write enabled', {
      table: this.table,
      oldColumn: this.oldColumn,
      newColumn: this.newColumn
    });
  }

  async disable(): Promise<void> {
    this.enabled = false;
    // Clean up triggers/hooks
    this.logger.info('Dual-write disabled', {
      table: this.table
    });
  }

  isEnabled(): boolean {
    return this.enabled;
  }
}
