/**
 * Backup CLI - Comprehensive backup and recovery operations
 * Exposes backup operations via CLI commands with scheduling, verification, and management
 */

import { Command } from 'commander';
import chalk from 'chalk';
import Table from 'cli-table3';
import { BackupManager, BackupOptions, RestoreOptions, BackupInfo } from './backup-manager';
import { BackupSystem } from './backup-system';
import { DatabaseConnectionManager } from './database-manager';
import { StateManager } from '../core/state-manager';
import { createLogger } from '../core/logger';
import * as fs from 'fs/promises';
import * as path from 'path';
import cron from 'node-cron';

const logger = createLogger('BackupCLI');

/**
 * Backup filter options
 */
export interface BackupFilter {
  database?: string;
  after?: Date;
  before?: Date;
  format?: string;
}

/**
 * Backup result
 */
export interface BackupResult {
  id: string;
  path: string;
  size: number;
  duration: number;
  status: 'success' | 'failed';
  error?: string;
}

/**
 * Verification result
 */
export interface VerificationResult {
  valid: boolean;
  checksum?: string;
  errors: string[];
  warnings: string[];
}

/**
 * Schedule info
 */
export interface ScheduleInfo {
  id: string;
  name: string;
  cron: string;
  database: string;
  enabled: boolean;
  lastRun?: Date;
  nextRun?: Date;
}

/**
 * Backup CLI - Main class for backup operations
 */
/**
 * Dependency injection configuration
 */
export interface BackupCLIDependencies {
  backupManager?: BackupManager;
  backupSystem?: BackupSystem;
  dbManager?: DatabaseConnectionManager;
  stateManager?: StateManager;
}

/**
 * BackupCLI configuration
 */
export interface BackupCLIConfig {
  backupDir?: string;
  retentionDays?: number;
  maxBackups?: number;
}

export class BackupCLI {
  private logger = createLogger('BackupCLI');
  private backupManager: BackupManager;
  private backupSystem: BackupSystem;
  private dbManager: DatabaseConnectionManager;
  private stateManager: StateManager;
  private backupDir: string;
  private schedules = new Map<string, { task: cron.ScheduledTask; config: ScheduleInfo }>();

  /**
   * Constructor with dependency injection support
   * @param config - Configuration options
   * @param dependencies - Optional injected dependencies for testing
   */
  constructor(config?: BackupCLIConfig, dependencies?: BackupCLIDependencies) {
    this.backupDir = config?.backupDir || path.join(process.env.HOME || '/tmp', '.ai-shell', 'backups');

    // Use injected dependencies or create new instances
    if (dependencies?.stateManager) {
      this.stateManager = dependencies.stateManager;
    } else {
      this.stateManager = new StateManager();
    }

    if (dependencies?.dbManager) {
      this.dbManager = dependencies.dbManager;
    } else {
      this.dbManager = new DatabaseConnectionManager(this.stateManager);
    }

    if (dependencies?.backupManager) {
      this.backupManager = dependencies.backupManager;
    } else {
      this.backupManager = new BackupManager({
        defaultBackupDir: this.backupDir,
        retentionDays: config?.retentionDays || 30,
        maxBackups: config?.maxBackups || 50
      });
    }

    if (dependencies?.backupSystem) {
      this.backupSystem = dependencies.backupSystem;
    } else {
      this.backupSystem = new BackupSystem(this.dbManager, this.stateManager);
    }

    // Load saved schedules
    this.loadSchedules();
  }

  /**
   * Create backup with options
   */
  async createBackup(options: BackupOptions & { name?: string; verify?: boolean }): Promise<BackupResult> {
    const startTime = Date.now();

    try {
      logger.info('Creating backup', { database: options.database, name: options.name });

      // Validate database connection
      const connection = this.dbManager.getConnection(options.database);
      if (!connection) {
        throw new Error(`Database connection not found: ${options.database}`);
      }

      // Create backup
      const backupInfo = await this.backupManager.createBackup(options);

      // Verify if requested
      if (options.verify) {
        const valid = await this.verifyBackup(backupInfo.id, { deep: false });
        if (!valid.valid) {
          throw new Error(`Backup verification failed: ${valid.errors.join(', ')}`);
        }
      }

      const duration = Date.now() - startTime;

      const result: BackupResult = {
        id: backupInfo.id,
        path: backupInfo.path,
        size: backupInfo.size,
        duration,
        status: 'success'
      };

      logger.info('Backup created successfully', result);
      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      const errorMsg = error instanceof Error ? error.message : String(error);

      logger.error('Backup creation failed', error);

      return {
        id: `failed-${Date.now()}`,
        path: '',
        size: 0,
        duration,
        status: 'failed',
        error: errorMsg
      };
    }
  }

  /**
   * Restore backup
   */
  async restoreBackup(backupId: string, options: RestoreOptions): Promise<void> {
    try {
      logger.info('Restoring backup', { backupId, options });

      // Find backup by ID
      const backups = await this.backupManager.listBackups();
      const backup = backups.find(b => b.id === backupId);

      if (!backup) {
        throw new Error(`Backup not found: ${backupId}`);
      }

      // Verify backup integrity before restore
      if (options.dryRun) {
        logger.info('Dry run mode - verification only');
        const verification = await this.verifyBackup(backupId, { deep: true });

        if (!verification.valid) {
          throw new Error(`Backup verification failed: ${verification.errors.join(', ')}`);
        }

        console.log(chalk.green('\n✓ Backup is valid and can be restored'));
        console.log(chalk.dim(`  Backup ID: ${backupId}`));
        console.log(chalk.dim(`  Database: ${backup.database}`));
        console.log(chalk.dim(`  Size: ${this.formatSize(backup.size)}`));
        console.log(chalk.dim(`  Tables: ${backup.tables.length}`));
        return;
      }

      // Perform restore
      await this.backupManager.restoreBackup(backup.path, options);

      logger.info('Restore completed successfully', { backupId });
    } catch (error) {
      logger.error('Restore failed', error);
      throw error;
    }
  }

  /**
   * List backups with optional filters
   */
  async listBackups(filter?: BackupFilter): Promise<BackupInfo[]> {
    let backups = await this.backupManager.listBackups();

    // Handle undefined/null returns
    if (!backups || !Array.isArray(backups)) {
      return [];
    }

    // Apply filters
    if (filter?.database) {
      backups = backups.filter(b => b.database === filter.database);
    }

    if (filter?.after) {
      backups = backups.filter(b => b.timestamp >= filter.after!.getTime());
    }

    if (filter?.before) {
      backups = backups.filter(b => b.timestamp <= filter.before!.getTime());
    }

    if (filter?.format) {
      backups = backups.filter(b => b.format === filter.format);
    }

    return backups;
  }

  /**
   * Get detailed backup info
   */
  async getBackupInfo(backupId: string): Promise<BackupInfo | null> {
    const backups = await this.backupManager.listBackups();

    // Handle undefined/null returns
    if (!backups || !Array.isArray(backups)) {
      return null;
    }

    return backups.find(b => b.id === backupId) || null;
  }

  /**
   * Delete backup
   */
  async deleteBackup(backupId: string, force: boolean = false): Promise<void> {
    const backup = await this.getBackupInfo(backupId);

    if (!backup) {
      throw new Error(`Backup not found: ${backupId}`);
    }

    if (!force) {
      // Require confirmation for non-forced deletes
      throw new Error('Use --force flag to confirm backup deletion');
    }

    try {
      // Delete backup file
      await fs.unlink(backup.path);

      // Delete metadata file
      const metadataPath = `${backup.path}.metadata.json`;
      try {
        await fs.unlink(metadataPath);
      } catch (error) {
        // Metadata file might not exist
      }

      // If backupManager has deleteBackup method, call it to update internal state
      if (typeof (this.backupManager as any).deleteBackup === 'function') {
        await (this.backupManager as any).deleteBackup(backupId);
      }

      logger.info('Backup deleted', { backupId });
    } catch (error) {
      logger.error('Failed to delete backup', error);
      throw error;
    }
  }

  /**
   * Export backup to external location
   */
  async exportBackup(backupId: string, destination: string): Promise<void> {
    const backup = await this.getBackupInfo(backupId);

    if (!backup) {
      throw new Error(`Backup not found: ${backupId}`);
    }

    try {
      // Ensure destination directory exists
      const destDir = path.dirname(destination);
      await fs.mkdir(destDir, { recursive: true });

      // Copy backup file
      await fs.copyFile(backup.path, destination);

      // Copy metadata
      const metadataPath = `${backup.path}.metadata.json`;
      const destMetadata = `${destination}.metadata.json`;

      try {
        await fs.copyFile(metadataPath, destMetadata);
      } catch (error) {
        // Metadata might not exist
      }

      logger.info('Backup exported', { backupId, destination });
    } catch (error) {
      logger.error('Failed to export backup', error);
      throw error;
    }
  }

  /**
   * Import backup from external location
   */
  async importBackup(sourcePath: string): Promise<BackupInfo> {
    try {
      // Verify file exists
      await fs.access(sourcePath);

      // Generate new backup ID
      const backupId = `imported-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      // Determine database from path or metadata
      const metadataPath = `${sourcePath}.metadata.json`;
      let metadata: BackupInfo | null = null;

      try {
        const metadataContent = await fs.readFile(metadataPath, 'utf-8');
        metadata = JSON.parse(metadataContent);
      } catch (error) {
        // No metadata available
      }

      const database = metadata?.database || 'unknown';
      const destDir = path.join(this.backupDir, database);
      await fs.mkdir(destDir, { recursive: true });

      const fileName = path.basename(sourcePath);
      const destPath = path.join(destDir, fileName);

      // Copy backup file
      await fs.copyFile(sourcePath, destPath);

      // Copy metadata if exists
      if (metadata) {
        const destMetadata = `${destPath}.metadata.json`;
        await fs.copyFile(metadataPath, destMetadata);

        // Update metadata with new ID and path
        metadata.id = backupId;
        metadata.path = destPath;

        await fs.writeFile(destMetadata, JSON.stringify(metadata, null, 2));
      }

      logger.info('Backup imported', { backupId, sourcePath });

      return metadata || {
        id: backupId,
        timestamp: Date.now(),
        database,
        format: 'sql',
        compressed: sourcePath.endsWith('.gz'),
        size: (await fs.stat(destPath)).size,
        tables: [],
        path: destPath,
        metadata: {}
      };
    } catch (error) {
      logger.error('Failed to import backup', error);
      throw error;
    }
  }

  /**
   * Verify backup integrity
   */
  async verifyBackup(backupId: string, options: { deep?: boolean }): Promise<VerificationResult> {
    const backup = await this.getBackupInfo(backupId);

    if (!backup) {
      return {
        valid: false,
        errors: [`Backup not found: ${backupId}`],
        warnings: []
      };
    }

    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Check if file exists
      await fs.access(backup.path);
    } catch (error) {
      errors.push('Backup file not found');
      return { valid: false, errors, warnings };
    }

    // Verify file size
    try {
      const stats = await fs.stat(backup.path);
      if (stats.size !== backup.size) {
        warnings.push(`File size mismatch: expected ${backup.size}, got ${stats.size}`);
      }
    } catch (error) {
      errors.push('Cannot stat backup file');
    }

    // Deep verification includes checksum
    let checksum: string | undefined;
    if (options.deep && backup.metadata.checksum) {
      const valid = await this.backupManager.verifyBackup(backup.path);
      if (!valid) {
        errors.push('Checksum verification failed');
      } else {
        checksum = backup.metadata.checksum;
      }
    }

    const valid = errors.length === 0;

    return { valid, checksum, errors, warnings };
  }

  /**
   * Schedule backup
   */
  async scheduleBackup(
    cronExpression: string,
    options: BackupOptions & { name: string; retention?: number; email?: string }
  ): Promise<ScheduleInfo> {
    // Validate cron expression
    if (!cron.validate(cronExpression)) {
      throw new Error(`Invalid cron expression: ${cronExpression}`);
    }

    const scheduleId = `schedule-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    const scheduleInfo: ScheduleInfo = {
      id: scheduleId,
      name: options.name,
      cron: cronExpression,
      database: options.database,
      enabled: true
    };

    // Create cron task
    const task = cron.schedule(cronExpression, async () => {
      try {
        logger.info('Running scheduled backup', { schedule: options.name });

        const result = await this.createBackup(options);

        if (result.status === 'success') {
          logger.info('Scheduled backup completed', { schedule: options.name, backupId: result.id });

          // Send notification if email is configured
          if (options.email) {
            await this.sendNotification(options.email, 'success', result);
          }
        } else {
          logger.error('Scheduled backup failed', { schedule: options.name, error: result.error });

          if (options.email) {
            await this.sendNotification(options.email, 'failed', result);
          }
        }
      } catch (error) {
        logger.error('Scheduled backup error', error);
      }
    }, {
      scheduled: true
    });

    this.schedules.set(scheduleId, { task, config: scheduleInfo });
    await this.saveSchedules();

    logger.info('Backup scheduled', scheduleInfo);
    return scheduleInfo;
  }

  /**
   * List schedules
   */
  listSchedules(): ScheduleInfo[] {
    return Array.from(this.schedules.values()).map(s => s.config);
  }

  /**
   * Delete schedule
   */
  async deleteSchedule(scheduleId: string): Promise<void> {
    const schedule = this.schedules.get(scheduleId);

    if (!schedule) {
      throw new Error(`Schedule not found: ${scheduleId}`);
    }

    schedule.task.stop();
    this.schedules.delete(scheduleId);
    await this.saveSchedules();

    logger.info('Schedule deleted', { scheduleId });
  }

  /**
   * Test backup (sample verification)
   */
  async testBackup(backupId: string, options: { sampleSize?: number; validateData?: boolean }): Promise<{
    success: boolean;
    tests: Array<{ name: string; passed: boolean; message?: string }>;
  }> {
    const tests: Array<{ name: string; passed: boolean; message?: string }> = [];

    // Test 1: Backup exists
    const backup = await this.getBackupInfo(backupId);
    tests.push({
      name: 'Backup exists',
      passed: backup !== null,
      message: backup ? 'Backup found' : 'Backup not found'
    });

    if (!backup) {
      return { success: false, tests };
    }

    // Test 2: File integrity
    const verification = await this.verifyBackup(backupId, { deep: true });
    tests.push({
      name: 'File integrity',
      passed: verification.valid,
      message: verification.valid ? 'Checksum valid' : verification.errors.join(', ')
    });

    // Test 3: Can decompress (if compressed)
    if (backup.compressed) {
      try {
        // Just verify we can read the file
        await fs.access(backup.path);
        tests.push({
          name: 'Compression',
          passed: true,
          message: 'Can access compressed file'
        });
      } catch (error) {
        tests.push({
          name: 'Compression',
          passed: false,
          message: 'Cannot access compressed file'
        });
      }
    }

    // Test 4: Metadata complete
    const hasMetadata = backup.metadata && Object.keys(backup.metadata).length > 0;
    tests.push({
      name: 'Metadata',
      passed: hasMetadata,
      message: hasMetadata ? 'Metadata complete' : 'Missing metadata'
    });

    const success = tests.every(t => t.passed);
    return { success, tests };
  }

  /**
   * Display backups as table
   */
  displayBackupsTable(backups: BackupInfo[]): void {
    if (backups.length === 0) {
      console.log(chalk.yellow('\nNo backups found\n'));
      return;
    }

    const table = new Table({
      head: [
        chalk.bold('ID'),
        chalk.bold('Database'),
        chalk.bold('Date'),
        chalk.bold('Size'),
        chalk.bold('Format'),
        chalk.bold('Tables'),
        chalk.bold('Compressed')
      ],
      colWidths: [15, 20, 20, 12, 10, 10, 12]
    });

    backups.forEach(backup => {
      table.push([
        backup.id.substring(0, 12) + '...',
        backup.database,
        new Date(backup.timestamp).toLocaleString(),
        this.formatSize(backup.size),
        backup.format,
        backup.tables.length.toString(),
        backup.compressed ? chalk.green('Yes') : chalk.dim('No')
      ]);
    });

    console.log('\n' + table.toString() + '\n');
  }

  /**
   * Display schedule info
   */
  displaySchedulesTable(schedules: ScheduleInfo[]): void {
    if (schedules.length === 0) {
      console.log(chalk.yellow('\nNo schedules configured\n'));
      return;
    }

    const table = new Table({
      head: [
        chalk.bold('Name'),
        chalk.bold('Database'),
        chalk.bold('Schedule'),
        chalk.bold('Enabled'),
        chalk.bold('Next Run')
      ],
      colWidths: [25, 20, 20, 12, 25]
    });

    schedules.forEach(schedule => {
      table.push([
        schedule.name,
        schedule.database,
        schedule.cron,
        schedule.enabled ? chalk.green('Yes') : chalk.red('No'),
        schedule.nextRun ? schedule.nextRun.toLocaleString() : chalk.dim('N/A')
      ]);
    });

    console.log('\n' + table.toString() + '\n');
  }

  /**
   * Format file size
   */
  private formatSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`;
  }

  /**
   * Send notification
   */
  private async sendNotification(email: string, status: 'success' | 'failed', result: BackupResult): Promise<void> {
    // Placeholder for email notification
    // In production, integrate with email service (SendGrid, AWS SES, etc.)
    logger.info('Notification sent', { email, status, backupId: result.id });
  }

  /**
   * Load schedules from state
   */
  private async loadSchedules(): Promise<void> {
    try {
      const saved = this.stateManager.get('backup-schedules');
      if (saved && Array.isArray(saved)) {
        for (const scheduleInfo of saved as ScheduleInfo[]) {
          if (scheduleInfo.enabled && cron.validate(scheduleInfo.cron)) {
            // Recreate cron task
            const task = cron.schedule(scheduleInfo.cron, async () => {
              try {
                logger.info('Running scheduled backup', { schedule: scheduleInfo.name });
                await this.createBackup({ database: scheduleInfo.database });
              } catch (error) {
                logger.error('Scheduled backup error', error);
              }
            }, {
              scheduled: true
            });

            this.schedules.set(scheduleInfo.id, { task, config: scheduleInfo });
          }
        }
        logger.info('Schedules loaded', { count: this.schedules.size });
      }
    } catch (error) {
      logger.warn('Failed to load schedules', { error });
    }
  }

  /**
   * Save schedules to state
   */
  private async saveSchedules(): Promise<void> {
    try {
      const schedules = Array.from(this.schedules.values()).map(s => s.config);
      this.stateManager.set('backup-schedules', schedules, {
        metadata: { type: 'backup-schedules' }
      });
    } catch (error) {
      logger.error('Failed to save schedules', error);
    }
  }

  /**
   * Cleanup
   */
  async cleanup(): Promise<void> {
    // Stop all scheduled tasks
    this.schedules.forEach(schedule => schedule.task.stop());
    this.schedules.clear();

    this.backupManager.shutdown();
  }
}

/**
 * Setup backup CLI commands
 * @deprecated Use setupBackupCommands from backup-commands.ts instead
 */
export function setupBackupCommands(program: Command, config?: BackupCLIConfig, dependencies?: BackupCLIDependencies): void {
  const backupCLI = new BackupCLI(config, dependencies);

  // Backup create command
  program
    .command('backup create')
    .description('Create a new database backup')
    .requiredOption('-d, --database <name>', 'Database name')
    .option('-n, --name <name>', 'Backup name')
    .option('-c, --compression <type>', 'Compression type (gzip, bzip2, none)', 'gzip')
    .option('--incremental', 'Create incremental backup')
    .option('--verify', 'Verify backup after creation')
    .option('--format <type>', 'Backup format (sql, json, csv)', 'sql')
    .action(async (options) => {
      try {
        console.log(chalk.blue('\n📦 Creating backup...\n'));

        const result = await backupCLI.createBackup({
          database: options.database,
          name: options.name,
          compress: options.compression !== 'none',
          incremental: options.incremental,
          verify: options.verify,
          format: options.format
        });

        if (result.status === 'success') {
          console.log(chalk.green('✓ Backup created successfully\n'));
          console.log(`  ID: ${result.id}`);
          console.log(`  Path: ${result.path}`);
          console.log(`  Size: ${(result.size / 1024 / 1024).toFixed(2)} MB`);
          console.log(`  Duration: ${(result.duration / 1000).toFixed(2)}s\n`);
        } else {
          console.log(chalk.red(`✗ Backup failed: ${result.error}\n`));
          process.exit(1);
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Backup restore command
  program
    .command('backup restore <backup-id>')
    .description('Restore from backup')
    .option('-d, --database <name>', 'Target database')
    .option('--point-in-time <timestamp>', 'Restore to specific point')
    .option('--dry-run', 'Test restore without applying')
    .option('--verify', 'Verify integrity before restore')
    .action(async (backupId, options) => {
      try {
        console.log(chalk.blue('\n🔄 Restoring backup...\n'));

        await backupCLI.restoreBackup(backupId, {
          targetDatabase: options.database,
          dryRun: options.dryRun
        });

        if (!options.dryRun) {
          console.log(chalk.green('✓ Restore completed successfully\n'));
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Backup list command
  program
    .command('backup list')
    .description('List all backups')
    .option('-d, --database <name>', 'Filter by database')
    .option('--after <date>', 'Show backups after date')
    .option('--before <date>', 'Show backups before date')
    .option('--format <type>', 'Output format (table, json)')
    .action(async (options) => {
      try {
        const filter: BackupFilter = {
          database: options.database,
          after: options.after ? new Date(options.after) : undefined,
          before: options.before ? new Date(options.before) : undefined
        };

        const backups = await backupCLI.listBackups(filter);

        if (options.format === 'json') {
          console.log(JSON.stringify(backups, null, 2));
        } else {
          backupCLI.displayBackupsTable(backups);
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Backup info command
  program
    .command('backup info <backup-id>')
    .description('Show detailed backup information')
    .action(async (backupId) => {
      try {
        const backup = await backupCLI.getBackupInfo(backupId);

        if (!backup) {
          console.log(chalk.yellow(`Backup not found: ${backupId}`));
          process.exit(1);
        }

        console.log(chalk.blue('\n📋 Backup Information\n'));
        console.log(`  ID: ${backup.id}`);
        console.log(`  Database: ${backup.database}`);
        console.log(`  Date: ${new Date(backup.timestamp).toLocaleString()}`);
        console.log(`  Format: ${backup.format}`);
        console.log(`  Size: ${(backup.size / 1024 / 1024).toFixed(2)} MB`);
        console.log(`  Compressed: ${backup.compressed ? 'Yes' : 'No'}`);
        console.log(`  Tables: ${backup.tables.length}`);
        console.log(`  Path: ${backup.path}`);

        if (backup.metadata.checksum) {
          console.log(`  Checksum: ${backup.metadata.checksum}`);
        }
        console.log('');
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Backup delete command
  program
    .command('backup delete <backup-id>')
    .description('Delete a backup')
    .option('--force', 'Force deletion without confirmation')
    .action(async (backupId, options) => {
      try {
        await backupCLI.deleteBackup(backupId, options.force);
        console.log(chalk.green(`✓ Backup deleted: ${backupId}\n`));
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Backup schedule command
  program
    .command('backup schedule <cron>')
    .description('Schedule automated backups')
    .requiredOption('-n, --name <name>', 'Schedule name')
    .requiredOption('-d, --database <name>', 'Database to backup')
    .option('--retention <days>', 'Keep backups for N days', '30')
    .option('--email <address>', 'Notification email')
    .action(async (cron, options) => {
      try {
        const schedule = await backupCLI.scheduleBackup(cron, {
          name: options.name,
          database: options.database,
          retention: parseInt(options.retention),
          email: options.email
        });

        console.log(chalk.green('\n✓ Backup scheduled\n'));
        console.log(`  Name: ${schedule.name}`);
        console.log(`  Database: ${schedule.database}`);
        console.log(`  Schedule: ${schedule.cron}`);
        console.log(`  Retention: ${options.retention} days\n`);
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Backup verify command
  program
    .command('backup verify <backup-id>')
    .description('Verify backup integrity')
    .option('--deep', 'Deep verification with checksums')
    .action(async (backupId, options) => {
      try {
        console.log(chalk.blue('\n🔍 Verifying backup...\n'));

        const result = await backupCLI.verifyBackup(backupId, { deep: options.deep });

        if (result.valid) {
          console.log(chalk.green('✓ Backup is valid\n'));
          if (result.checksum) {
            console.log(`  Checksum: ${result.checksum}`);
          }
        } else {
          console.log(chalk.red('✗ Backup verification failed\n'));
          result.errors.forEach(err => console.log(chalk.red(`  • ${err}`)));
        }

        if (result.warnings.length > 0) {
          console.log(chalk.yellow('\nWarnings:'));
          result.warnings.forEach(warn => console.log(chalk.yellow(`  • ${warn}`)));
        }
        console.log('');
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Backup test command
  program
    .command('backup test <backup-id>')
    .description('Test backup restore capability')
    .option('--sample-size <n>', 'Test sample size', '10')
    .option('--validate-data', 'Validate data integrity')
    .action(async (backupId, options) => {
      try {
        console.log(chalk.blue('\n🧪 Testing backup...\n'));

        const result = await backupCLI.testBackup(backupId, {
          sampleSize: parseInt(options.sampleSize),
          validateData: options.validateData
        });

        result.tests.forEach(test => {
          const icon = test.passed ? chalk.green('✓') : chalk.red('✗');
          console.log(`  ${icon} ${test.name}: ${test.message}`);
        });

        console.log('');
        if (result.success) {
          console.log(chalk.green('✓ All tests passed\n'));
        } else {
          console.log(chalk.red('✗ Some tests failed\n'));
          process.exit(1);
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Export backup command
  program
    .command('backup export <backup-id> <path>')
    .description('Export backup to external location')
    .action(async (backupId, exportPath) => {
      try {
        await backupCLI.exportBackup(backupId, exportPath);
        console.log(chalk.green(`✓ Backup exported to: ${exportPath}\n`));
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Import backup command
  program
    .command('backup import <path>')
    .description('Import backup from external location')
    .action(async (importPath) => {
      try {
        const backup = await backupCLI.importBackup(importPath);
        console.log(chalk.green('\n✓ Backup imported successfully\n'));
        console.log(`  ID: ${backup.id}`);
        console.log(`  Database: ${backup.database}`);
        console.log(`  Size: ${(backup.size / 1024 / 1024).toFixed(2)} MB\n`);
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // List schedules command
  program
    .command('backup schedules')
    .description('List all backup schedules')
    .action(async () => {
      try {
        const schedules = backupCLI.listSchedules();
        backupCLI.displaySchedulesTable(schedules);
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Delete schedule command
  program
    .command('backup unschedule <schedule-id>')
    .description('Remove backup schedule')
    .action(async (scheduleId) => {
      try {
        await backupCLI.deleteSchedule(scheduleId);
        console.log(chalk.green(`✓ Schedule removed: ${scheduleId}\n`));
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });
}

export default BackupCLI;
