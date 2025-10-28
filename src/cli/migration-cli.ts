/**
 * Migration CLI - Command-line interface for database migrations
 *
 * Commands:
 * - ai-shell migrate create <name>
 * - ai-shell migrate plan <file>
 * - ai-shell migrate apply <file> --phase <1-5>
 * - ai-shell migrate status
 * - ai-shell migrate rollback
 * - ai-shell migrate verify <file>
 * - ai-shell migrate list
 */

import { Command } from 'commander';
import { AdvancedMigrationEngine } from './migration-engine-advanced';
import { MigrationBuilder, MigrationPatterns, migration } from './migration-dsl';
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { StateManager } from '../core/state-manager';
import { BackupSystem } from './backup-system';
import { createLogger } from '../core/logger';
import * as fs from 'fs/promises';
import * as path from 'path';
import chalk from 'chalk';
import Table from 'cli-table3';
import inquirer from 'inquirer';

const logger = createLogger('MigrationCLI');

/**
 * Migration CLI Manager
 */
export class MigrationCLI {
  private engine: AdvancedMigrationEngine;
  private migrationsDir: string;

  constructor(
    private dbManager: DatabaseConnectionManager,
    private stateManager: StateManager,
    private backupSystem: BackupSystem,
    options: { migrationsDir?: string } = {}
  ) {
    this.migrationsDir = options.migrationsDir || './migrations';

    this.engine = new AdvancedMigrationEngine(
      dbManager,
      stateManager,
      backupSystem,
      {
        migrationsDir: this.migrationsDir,
        enableAutoBackup: true,
        enableAutoSnapshot: true
      }
    );
  }

  /**
   * Setup CLI commands
   */
  setupCommands(program: Command): void {
    const migrate = program
      .command('migrate')
      .description('Database migration management with zero-downtime support');

    // Create migration
    migrate
      .command('create <name>')
      .description('Create a new migration file')
      .option('-t, --type <type>', 'Migration type (add-column, remove-column, rename-column, change-type, custom)', 'custom')
      .option('--table <table>', 'Table name')
      .option('--column <column>', 'Column name')
      .option('--data-type <type>', 'Data type')
      .option('--old-column <name>', 'Old column name (for rename)')
      .option('--new-column <name>', 'New column name (for rename)')
      .option('--old-type <type>', 'Old data type (for change-type)')
      .option('--new-type <type>', 'New data type (for change-type)')
      .action(async (name, options) => {
        await this.createMigration(name, options);
      });

    // Plan migration
    migrate
      .command('plan <file>')
      .description('Show migration execution plan')
      .action(async (file) => {
        await this.planMigration(file);
      });

    // Apply migration
    migrate
      .command('apply <file>')
      .description('Apply migration')
      .option('--phase <number>', 'Execute specific phase only', parseInt)
      .option('--dry-run', 'Dry run - show what would be executed')
      .option('--skip-backup', 'Skip automatic backup')
      .option('--skip-snapshot', 'Skip snapshot creation')
      .option('-y, --yes', 'Skip confirmation prompts')
      .action(async (file, options) => {
        await this.applyMigration(file, options);
      });

    // Migration status
    migrate
      .command('status')
      .description('Show migration status')
      .action(async () => {
        await this.showStatus();
      });

    // Rollback
    migrate
      .command('rollback')
      .description('Rollback last migration')
      .option('--execution-id <id>', 'Rollback specific execution')
      .option('-y, --yes', 'Skip confirmation prompts')
      .action(async (options) => {
        await this.rollbackMigration(options);
      });

    // Verify migration
    migrate
      .command('verify <file>')
      .description('Verify migration safety')
      .action(async (file) => {
        await this.verifyMigration(file);
      });

    // List migrations
    migrate
      .command('list')
      .description('List all migrations')
      .option('-a, --all', 'Show all migrations including applied')
      .action(async (options) => {
        await this.listMigrations(options);
      });

    // Generate from template
    migrate
      .command('generate <pattern>')
      .description('Generate migration from common pattern')
      .option('--table <table>', 'Table name')
      .option('--column <column>', 'Column name')
      .option('--columns <columns>', 'Comma-separated column names')
      .option('--data-type <type>', 'Data type')
      .option('--old-column <name>', 'Old column name')
      .option('--new-column <name>', 'New column name')
      .option('--old-type <type>', 'Old data type')
      .option('--new-type <type>', 'New data type')
      .option('--default <value>', 'Default value')
      .option('--ref-table <table>', 'Reference table (for foreign keys)')
      .option('--ref-column <column>', 'Reference column (for foreign keys)')
      .action(async (pattern, options) => {
        await this.generateFromPattern(pattern, options);
      });

    // History
    migrate
      .command('history')
      .description('Show migration execution history')
      .option('--limit <number>', 'Limit number of results', parseInt, 10)
      .action(async (options) => {
        await this.showHistory(options);
      });
  }

  /**
   * Create migration
   */
  private async createMigration(name: string, options: any): Promise<void> {
    try {
      console.log(chalk.blue('Creating migration:'), chalk.bold(name));

      let builder: MigrationBuilder;
      const dbType = this.getActiveDatabaseType();

      switch (options.type) {
        case 'add-column':
          if (!options.table || !options.column || !options.dataType) {
            throw new Error('add-column requires --table, --column, and --data-type');
          }
          builder = MigrationPatterns.addNullableColumn(
            options.table,
            options.column,
            options.dataType,
            options.default
          );
          break;

        case 'remove-column':
          if (!options.table || !options.column) {
            throw new Error('remove-column requires --table and --column');
          }
          builder = MigrationPatterns.removeColumn(options.table, options.column);
          break;

        case 'rename-column':
          if (!options.table || !options.oldColumn || !options.newColumn || !options.dataType) {
            throw new Error('rename-column requires --table, --old-column, --new-column, and --data-type');
          }
          builder = MigrationPatterns.safeRenameColumn(
            options.table,
            options.oldColumn,
            options.newColumn,
            options.dataType
          );
          break;

        case 'change-type':
          if (!options.table || !options.column || !options.oldType || !options.newType) {
            throw new Error('change-type requires --table, --column, --old-type, and --new-type');
          }
          builder = MigrationPatterns.changeColumnType(
            options.table,
            options.column,
            options.oldType,
            options.newType
          );
          break;

        default:
          // Custom migration
          builder = migration(name, dbType, 'Custom migration');
          builder.phase('Phase 1 - TODO: Add operations');
          break;
      }

      const filepath = await builder.commit(this.migrationsDir);

      console.log(chalk.green('Migration created successfully:'));
      console.log(chalk.gray('  File:'), filepath);
      console.log(chalk.gray('  Edit the file to customize the migration'));
    } catch (error) {
      console.error(chalk.red('Error creating migration:'), error);
      throw error;
    }
  }

  /**
   * Plan migration
   */
  private async planMigration(file: string): Promise<void> {
    try {
      const filepath = this.resolveMigrationPath(file);

      console.log(chalk.blue('Analyzing migration:'), chalk.bold(filepath));
      console.log();

      const plan = await this.engine.plan(filepath);

      // Display migration info
      console.log(chalk.bold('Migration:'), plan.migration.name);
      if (plan.migration.description) {
        console.log(chalk.gray('Description:'), plan.migration.description);
      }
      console.log(chalk.gray('Database:'), plan.migration.database);
      console.log(chalk.gray('Phases:'), plan.migration.phases.length);
      console.log(chalk.gray('Estimated Duration:'), `${plan.estimatedDuration}ms`);
      console.log();

      // Display risks
      if (plan.risks.length > 0) {
        console.log(chalk.yellow.bold('Risks:'));
        plan.risks.forEach(risk => {
          console.log(chalk.yellow('  ⚠'), risk);
        });
        console.log();
      }

      // Display phases
      console.log(chalk.bold('Execution Plan:'));
      console.log();

      plan.phases.forEach((phase, index) => {
        console.log(chalk.cyan(`Phase ${phase.phase}:`), phase.description);
        console.log(chalk.gray(`  Estimated duration: ${phase.estimatedDuration}ms`));
        console.log();

        phase.operations.forEach((op, opIndex) => {
          console.log(chalk.gray(`  ${opIndex + 1}.`), op);
        });

        console.log();
      });
    } catch (error) {
      console.error(chalk.red('Error planning migration:'), error);
      throw error;
    }
  }

  /**
   * Apply migration
   */
  private async applyMigration(file: string, options: any): Promise<void> {
    try {
      const filepath = this.resolveMigrationPath(file);

      console.log(chalk.blue('Applying migration:'), chalk.bold(filepath));

      // Show plan first
      const plan = await this.engine.plan(filepath);

      console.log();
      console.log(chalk.bold('Migration:'), plan.migration.name);
      console.log(chalk.gray('Phases:'), plan.migration.phases.length);

      if (options.phase) {
        console.log(chalk.gray('Phase to execute:'), options.phase);
      }

      console.log();

      // Confirm unless --yes flag
      if (!options.yes && !options.dryRun) {
        const answers = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'confirm',
            message: 'Do you want to proceed with this migration?',
            default: false
          }
        ]);

        if (!answers.confirm) {
          console.log(chalk.yellow('Migration cancelled'));
          return;
        }
      }

      // Execute
      const startTime = Date.now();

      const execution = await this.engine.executeMigration(filepath, {
        phase: options.phase,
        dryRun: options.dryRun,
        skipBackup: options.skipBackup,
        skipSnapshot: options.skipSnapshot
      });

      const duration = Date.now() - startTime;

      console.log();
      if (options.dryRun) {
        console.log(chalk.yellow('DRY RUN - No changes were made'));
      } else {
        console.log(chalk.green('Migration applied successfully!'));
        console.log(chalk.gray('Execution ID:'), execution.id);
        console.log(chalk.gray('Duration:'), `${duration}ms`);

        if (execution.backupId) {
          console.log(chalk.gray('Backup ID:'), execution.backupId);
        }

        // Show phase results
        console.log();
        console.log(chalk.bold('Phase Results:'));

        execution.phaseResults.forEach(result => {
          const icon = result.status === 'completed' ? chalk.green('✓') :
                       result.status === 'failed' ? chalk.red('✗') : chalk.gray('○');

          console.log(
            icon,
            chalk.gray(`Phase ${result.phase}:`),
            result.status,
            chalk.gray(`(${result.operationsExecuted} operations, ${result.endTime! - result.startTime!}ms)`)
          );
        });
      }
    } catch (error) {
      console.error(chalk.red('Error applying migration:'), error);
      throw error;
    }
  }

  /**
   * Show status
   */
  private async showStatus(): Promise<void> {
    try {
      const status = await this.engine.getStatus();

      console.log(chalk.bold('Migration Status'));
      console.log();

      if (status.lastMigration) {
        console.log(chalk.green('Last Migration:'));
        console.log(chalk.gray('  Name:'), status.lastMigration.migrationName);
        console.log(chalk.gray('  Execution ID:'), status.lastMigration.id);
        console.log(chalk.gray('  Status:'), this.formatStatus(status.lastMigration.status));
        console.log(chalk.gray('  Phase:'), `${status.lastMigration.currentPhase}`);

        if (status.lastMigration.startTime) {
          console.log(chalk.gray('  Started:'), new Date(status.lastMigration.startTime).toLocaleString());
        }

        if (status.lastMigration.endTime) {
          console.log(chalk.gray('  Completed:'), new Date(status.lastMigration.endTime).toLocaleString());
          console.log(chalk.gray('  Duration:'), `${status.lastMigration.endTime - status.lastMigration.startTime!}ms`);
        }

        console.log();
      }

      // Summary
      const completed = status.executions.filter(e => e.status === 'completed').length;
      const failed = status.executions.filter(e => e.status === 'failed').length;
      const rolledBack = status.executions.filter(e => e.status === 'rolled_back').length;

      console.log(chalk.bold('Summary:'));
      console.log(chalk.gray('  Total executions:'), status.executions.length);
      console.log(chalk.green('  Completed:'), completed);
      console.log(chalk.red('  Failed:'), failed);
      console.log(chalk.yellow('  Rolled back:'), rolledBack);
    } catch (error) {
      console.error(chalk.red('Error getting status:'), error);
      throw error;
    }
  }

  /**
   * Rollback migration
   */
  private async rollbackMigration(options: any): Promise<void> {
    try {
      console.log(chalk.yellow('Rollback not yet implemented'));
      console.log(chalk.gray('Use backup restoration for now'));

      // TODO: Implement rollback
      // This requires tracking rollback operations and executing them in reverse
    } catch (error) {
      console.error(chalk.red('Error rolling back migration:'), error);
      throw error;
    }
  }

  /**
   * Verify migration
   */
  private async verifyMigration(file: string): Promise<void> {
    try {
      const filepath = this.resolveMigrationPath(file);

      console.log(chalk.blue('Verifying migration:'), chalk.bold(filepath));
      console.log();

      const result = await this.engine.verify(filepath);

      // Display result
      if (result.safe) {
        console.log(chalk.green('✓ Migration appears safe'));
      } else {
        console.log(chalk.red('✗ Migration has errors'));
      }

      console.log();

      // Display errors
      if (result.errors.length > 0) {
        console.log(chalk.red.bold('Errors:'));
        result.errors.forEach(error => {
          console.log(chalk.red('  ✗'), error);
        });
        console.log();
      }

      // Display warnings
      if (result.warnings.length > 0) {
        console.log(chalk.yellow.bold('Warnings:'));
        result.warnings.forEach(warning => {
          console.log(chalk.yellow('  ⚠'), warning);
        });
        console.log();
      }

      // Display recommendations
      if (result.recommendations.length > 0) {
        console.log(chalk.cyan.bold('Recommendations:'));
        result.recommendations.forEach(rec => {
          console.log(chalk.cyan('  ℹ'), rec);
        });
        console.log();
      }

      if (result.safe && result.warnings.length === 0) {
        console.log(chalk.green('Migration is ready to apply!'));
      }
    } catch (error) {
      console.error(chalk.red('Error verifying migration:'), error);
      throw error;
    }
  }

  /**
   * List migrations
   */
  private async listMigrations(options: any): Promise<void> {
    try {
      const files = await fs.readdir(this.migrationsDir);
      const yamlFiles = files.filter(f => f.endsWith('.yaml') || f.endsWith('.yml'));

      if (yamlFiles.length === 0) {
        console.log(chalk.yellow('No migrations found in'), this.migrationsDir);
        return;
      }

      console.log(chalk.bold('Available Migrations:'));
      console.log();

      const table = new Table({
        head: ['Name', 'File', 'Size', 'Modified'],
        colWidths: [30, 40, 10, 20]
      });

      for (const file of yamlFiles.sort()) {
        const filepath = path.join(this.migrationsDir, file);
        const stats = await fs.stat(filepath);

        // Extract name from filename
        const parts = file.replace(/\.(yaml|yml)$/, '').split('_');
        const name = parts.slice(1).join('_');

        table.push([
          name || file,
          file,
          `${Math.round(stats.size / 1024)}KB`,
          stats.mtime.toLocaleDateString()
        ]);
      }

      console.log(table.toString());
    } catch (error) {
      console.error(chalk.red('Error listing migrations:'), error);
      throw error;
    }
  }

  /**
   * Generate from pattern
   */
  private async generateFromPattern(pattern: string, options: any): Promise<void> {
    try {
      console.log(chalk.blue('Generating migration from pattern:'), chalk.bold(pattern));

      let builder: MigrationBuilder;
      const dbType = this.getActiveDatabaseType();

      switch (pattern) {
        case 'add-nullable-column':
          if (!options.table || !options.column || !options.dataType) {
            throw new Error('Pattern requires --table, --column, and --data-type');
          }
          builder = MigrationPatterns.addNullableColumn(
            options.table,
            options.column,
            options.dataType,
            options.default
          );
          break;

        case 'add-required-column':
          if (!options.table || !options.column || !options.dataType || !options.default) {
            throw new Error('Pattern requires --table, --column, --data-type, and --default');
          }
          builder = MigrationPatterns.addRequiredColumn(
            options.table,
            options.column,
            options.dataType,
            options.default
          );
          break;

        case 'remove-column':
          if (!options.table || !options.column) {
            throw new Error('Pattern requires --table and --column');
          }
          builder = MigrationPatterns.removeColumn(options.table, options.column);
          break;

        case 'rename-column':
          if (!options.table || !options.oldColumn || !options.newColumn || !options.dataType) {
            throw new Error('Pattern requires --table, --old-column, --new-column, and --data-type');
          }
          builder = MigrationPatterns.safeRenameColumn(
            options.table,
            options.oldColumn,
            options.newColumn,
            options.dataType
          );
          break;

        case 'change-type':
          if (!options.table || !options.column || !options.oldType || !options.newType) {
            throw new Error('Pattern requires --table, --column, --old-type, and --new-type');
          }
          builder = MigrationPatterns.changeColumnType(
            options.table,
            options.column,
            options.oldType,
            options.newType
          );
          break;

        case 'add-index':
          if (!options.table || !options.column || !options.columns) {
            throw new Error('Pattern requires --table and --columns');
          }
          const indexName = `idx_${options.table}_${options.columns.replace(/,/g, '_')}`;
          const columns = options.columns.split(',').map((c: string) => c.trim());
          builder = MigrationPatterns.addConcurrentIndex(options.table, indexName, columns);
          break;

        case 'add-foreign-key':
          if (!options.table || !options.column || !options.refTable) {
            throw new Error('Pattern requires --table, --column, and --ref-table');
          }
          builder = MigrationPatterns.addForeignKey(
            options.table,
            options.column,
            options.refTable,
            options.refColumn
          );
          break;

        case 'add-unique':
          if (!options.table || !options.columns) {
            throw new Error('Pattern requires --table and --columns');
          }
          const uniqueColumns = options.columns.split(',').map((c: string) => c.trim());
          builder = MigrationPatterns.addUniqueConstraint(options.table, uniqueColumns);
          break;

        default:
          throw new Error(`Unknown pattern: ${pattern}`);
      }

      const filepath = await builder.commit(this.migrationsDir);

      console.log(chalk.green('Migration generated successfully:'));
      console.log(chalk.gray('  Pattern:'), pattern);
      console.log(chalk.gray('  File:'), filepath);
    } catch (error) {
      console.error(chalk.red('Error generating migration:'), error);
      throw error;
    }
  }

  /**
   * Show history
   */
  private async showHistory(options: any): Promise<void> {
    try {
      const status = await this.engine.getStatus();
      const executions = status.executions
        .sort((a, b) => (b.startTime || 0) - (a.startTime || 0))
        .slice(0, options.limit);

      if (executions.length === 0) {
        console.log(chalk.yellow('No migration history found'));
        return;
      }

      console.log(chalk.bold('Migration History:'));
      console.log();

      const table = new Table({
        head: ['Execution ID', 'Migration', 'Phase', 'Status', 'Started', 'Duration'],
        colWidths: [25, 30, 8, 12, 20, 12]
      });

      executions.forEach(exec => {
        const duration = exec.endTime && exec.startTime ?
          `${exec.endTime - exec.startTime}ms` : '-';

        const started = exec.startTime ?
          new Date(exec.startTime).toLocaleString() : '-';

        table.push([
          exec.id.substring(0, 22) + '...',
          exec.migrationName,
          exec.currentPhase.toString(),
          this.formatStatus(exec.status),
          started,
          duration
        ]);
      });

      console.log(table.toString());
    } catch (error) {
      console.error(chalk.red('Error showing history:'), error);
      throw error;
    }
  }

  // Helper methods

  private resolveMigrationPath(file: string): string {
    if (path.isAbsolute(file)) {
      return file;
    }

    return path.join(this.migrationsDir, file);
  }

  private formatStatus(status: string): string {
    switch (status) {
      case 'completed':
        return chalk.green(status);
      case 'failed':
        return chalk.red(status);
      case 'rolled_back':
        return chalk.yellow(status);
      case 'running':
        return chalk.blue(status);
      default:
        return chalk.gray(status);
    }
  }

  private getActiveDatabaseType(): DatabaseType {
    const connection = this.dbManager.getActive();
    return connection?.type || DatabaseType.POSTGRESQL;
  }
}

/**
 * Create and setup CLI
 */
export function setupMigrationCLI(
  program: Command,
  dbManager: DatabaseConnectionManager,
  stateManager: StateManager,
  backupSystem: BackupSystem
): MigrationCLI {
  const cli = new MigrationCLI(dbManager, stateManager, backupSystem);
  cli.setupCommands(program);
  return cli;
}

export default MigrationCLI;
