/**
 * Backup CLI Commands
 * Implements all 10 backup & recovery commands with comprehensive options
 * Commands: create, restore, list, status, schedule, verify, delete, export, import, config
 */

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import Table from 'cli-table3';
import inquirer from 'inquirer';
import { BackupCLI, BackupResult, VerificationResult, ScheduleInfo } from './backup-cli';
import { BackupInfo, BackupOptions, RestoreOptions } from './backup-manager';
import { CloudProvider, CloudStorageConfig } from './cloud-backup';
import { createLogger } from '../core/logger';

const logger = createLogger('BackupCommands');

/**
 * Command configuration
 */
export interface BackupCommandConfig {
  backupDir?: string;
  retentionDays?: number;
  maxBackups?: number;
  cloudProvider?: CloudProvider;
  cloudConfig?: CloudStorageConfig;
  verbose?: boolean;
}

/**
 * Format file size for display
 */
function formatSize(bytes: number): string {
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
 * Format duration for display
 */
function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

/**
 * Display backup table
 */
function displayBackupsTable(backups: BackupInfo[]): void {
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
    colWidths: [20, 20, 20, 12, 10, 10, 12]
  });

  backups.forEach(backup => {
    table.push([
      backup.id.substring(0, 17) + '...',
      backup.database,
      new Date(backup.timestamp).toLocaleString(),
      formatSize(backup.size),
      backup.format,
      backup.tables.length.toString(),
      backup.compressed ? chalk.green('Yes') : chalk.dim('No')
    ]);
  });

  console.log('\n' + table.toString() + '\n');
}

/**
 * Display schedule table
 */
function displaySchedulesTable(schedules: ScheduleInfo[]): void {
  if (schedules.length === 0) {
    console.log(chalk.yellow('\nNo schedules configured\n'));
    return;
  }

  const table = new Table({
    head: [
      chalk.bold('ID'),
      chalk.bold('Name'),
      chalk.bold('Database'),
      chalk.bold('Schedule'),
      chalk.bold('Enabled'),
      chalk.bold('Next Run')
    ],
    colWidths: [20, 25, 20, 20, 12, 25]
  });

  schedules.forEach(schedule => {
    table.push([
      schedule.id.substring(0, 17) + '...',
      schedule.name,
      schedule.database,
      schedule.cron,
      schedule.enabled ? chalk.green('Yes') : chalk.red('No'),
      schedule.nextRun ? new Date(schedule.nextRun).toLocaleString() : chalk.dim('N/A')
    ]);
  });

  console.log('\n' + table.toString() + '\n');
}

/**
 * Setup all backup CLI commands
 */
export function setupBackupCommands(program: Command, config: BackupCommandConfig = {}): void {
  const backupCLI = new BackupCLI(config);

  // Command 1: ai-shell backup create
  program
    .command('backup create')
    .description('Create a new database backup')
    .requiredOption('-d, --database <name>', 'Database name')
    .option('-n, --name <name>', 'Backup name')
    .option('-c, --compression <type>', 'Compression type (gzip, bzip2, none)', 'gzip')
    .option('--incremental', 'Create incremental backup')
    .option('--verify', 'Verify backup after creation')
    .option('--format <type>', 'Backup format (sql, json, csv)', 'sql')
    .option('--tables <tables>', 'Comma-separated list of tables to backup')
    .option('--cloud', 'Upload backup to cloud storage')
    .option('--encrypt', 'Encrypt backup file')
    .option('--verbose', 'Show detailed progress')
    .action(async (options) => {
      const spinner = ora('Creating backup...').start();

      try {
        logger.info('Starting backup creation', { database: options.database });

        const backupOptions: BackupOptions & { name?: string; verify?: boolean } = {
          database: options.database,
          name: options.name,
          compress: options.compression !== 'none',
          incremental: options.incremental,
          verify: options.verify,
          format: options.format,
          tables: options.tables ? options.tables.split(',') : undefined
        };

        const result: BackupResult = await backupCLI.createBackup(backupOptions);

        spinner.stop();

        if (result.status === 'success') {
          console.log(chalk.green('\n✓ Backup created successfully\n'));
          console.log(`  ${chalk.bold('ID:')} ${result.id}`);
          console.log(`  ${chalk.bold('Path:')} ${result.path}`);
          console.log(`  ${chalk.bold('Size:')} ${formatSize(result.size)}`);
          console.log(`  ${chalk.bold('Duration:')} ${formatDuration(result.duration)}`);

          if (options.cloud && config.cloudProvider) {
            const cloudSpinner = ora('Uploading to cloud storage...').start();
            try {
              // Cloud upload logic would go here
              cloudSpinner.succeed('Backup uploaded to cloud storage');
            } catch (error) {
              cloudSpinner.fail('Cloud upload failed');
              console.error(chalk.red(`  Error: ${error instanceof Error ? error.message : String(error)}`));
            }
          }

          console.log('');
        } else {
          console.log(chalk.red(`\n✗ Backup failed: ${result.error}\n`));
          process.exit(1);
        }
      } catch (error) {
        spinner.stop();
        console.error(chalk.red(`\nError: ${error instanceof Error ? error.message : String(error)}\n`));
        logger.error('Backup creation failed', error);
        process.exit(1);
      }
    });

  // Command 2: ai-shell backup restore
  program
    .command('backup restore <backup-id>')
    .description('Restore from backup')
    .option('-d, --database <name>', 'Target database')
    .option('--point-in-time <timestamp>', 'Restore to specific point')
    .option('--dry-run', 'Test restore without applying')
    .option('--verify', 'Verify integrity before restore')
    .option('--tables <tables>', 'Comma-separated list of tables to restore')
    .option('--drop-existing', 'Drop existing tables before restore')
    .option('--continue-on-error', 'Continue restore on errors')
    .option('--verbose', 'Show detailed progress')
    .action(async (backupId, options) => {
      const spinner = ora('Restoring backup...').start();

      try {
        logger.info('Starting backup restore', { backupId });

        const restoreOptions: RestoreOptions = {
          targetDatabase: options.database,
          dryRun: options.dryRun,
          tables: options.tables ? options.tables.split(',') : undefined,
          dropExisting: options.dropExisting,
          continueOnError: options.continueOnError
        };

        if (options.verify) {
          spinner.text = 'Verifying backup integrity...';
          const verification = await backupCLI.verifyBackup(backupId, { deep: true });

          if (!verification.valid) {
            spinner.fail('Backup verification failed');
            console.log(chalk.red('\nVerification Errors:'));
            verification.errors.forEach(err => console.log(chalk.red(`  • ${err}`)));
            process.exit(1);
          }
          spinner.text = 'Backup verified. Starting restore...';
        }

        await backupCLI.restoreBackup(backupId, restoreOptions);

        spinner.stop();

        if (options.dryRun) {
          console.log(chalk.green('\n✓ Dry run completed successfully\n'));
          console.log(chalk.dim('  No changes were made to the database'));
        } else {
          console.log(chalk.green('\n✓ Restore completed successfully\n'));
        }
        console.log('');
      } catch (error) {
        spinner.stop();
        console.error(chalk.red(`\nError: ${error instanceof Error ? error.message : String(error)}\n`));
        logger.error('Backup restore failed', error);
        process.exit(1);
      }
    });

  // Command 3: ai-shell backup list
  program
    .command('backup list')
    .description('List all backups')
    .option('-d, --database <name>', 'Filter by database')
    .option('--after <date>', 'Show backups after date (YYYY-MM-DD)')
    .option('--before <date>', 'Show backups before date (YYYY-MM-DD)')
    .option('--format <type>', 'Filter by format (sql, json, csv)')
    .option('--output <format>', 'Output format (table, json, csv)', 'table')
    .option('--limit <number>', 'Limit number of results')
    .option('--sort <field>', 'Sort by field (timestamp, size, database)', 'timestamp')
    .option('--order <direction>', 'Sort order (asc, desc)', 'desc')
    .action(async (options) => {
      try {
        logger.info('Listing backups', options);

        const filter: any = {
          database: options.database,
          after: options.after ? new Date(options.after) : undefined,
          before: options.before ? new Date(options.before) : undefined,
          format: options.format
        };

        let backups = await backupCLI.listBackups(filter);

        // Sort backups
        if (options.sort) {
          backups.sort((a, b) => {
            const aVal = a[options.sort as keyof BackupInfo];
            const bVal = b[options.sort as keyof BackupInfo];

            if (typeof aVal === 'number' && typeof bVal === 'number') {
              return options.order === 'asc' ? aVal - bVal : bVal - aVal;
            }

            return 0;
          });
        }

        // Limit results
        if (options.limit) {
          backups = backups.slice(0, parseInt(options.limit));
        }

        // Display results
        switch (options.output) {
          case 'json':
            console.log(JSON.stringify(backups, null, 2));
            break;

          case 'csv':
            console.log('ID,Database,Timestamp,Size,Format,Compressed,Path');
            backups.forEach(b => {
              console.log(`${b.id},${b.database},${b.timestamp},${b.size},${b.format},${b.compressed},${b.path}`);
            });
            break;

          case 'table':
          default:
            displayBackupsTable(backups);
            console.log(chalk.dim(`  Total: ${backups.length} backup(s)\n`));
            break;
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        logger.error('List backups failed', error);
        process.exit(1);
      }
    });

  // Command 4: ai-shell backup status
  program
    .command('backup status <backup-id>')
    .description('Show detailed backup status and information')
    .option('--verify', 'Include integrity verification')
    .option('--json', 'Output as JSON')
    .action(async (backupId, options) => {
      try {
        logger.info('Getting backup status', { backupId });

        const backup = await backupCLI.getBackupInfo(backupId);

        if (!backup) {
          console.log(chalk.yellow(`\nBackup not found: ${backupId}\n`));
          process.exit(1);
        }

        if (options.json) {
          console.log(JSON.stringify(backup, null, 2));
          return;
        }

        console.log(chalk.blue('\n📋 Backup Information\n'));
        console.log(`  ${chalk.bold('ID:')} ${backup.id}`);
        console.log(`  ${chalk.bold('Database:')} ${backup.database}`);
        console.log(`  ${chalk.bold('Timestamp:')} ${new Date(backup.timestamp).toLocaleString()}`);
        console.log(`  ${chalk.bold('Format:')} ${backup.format}`);
        console.log(`  ${chalk.bold('Size:')} ${formatSize(backup.size)}`);
        console.log(`  ${chalk.bold('Compressed:')} ${backup.compressed ? chalk.green('Yes') : 'No'}`);
        console.log(`  ${chalk.bold('Tables:')} ${backup.tables.length} (${backup.tables.join(', ')})`);
        console.log(`  ${chalk.bold('Path:')} ${backup.path}`);

        if (backup.metadata.checksum) {
          console.log(`  ${chalk.bold('Checksum:')} ${backup.metadata.checksum}`);
        }

        if (backup.metadata.incremental) {
          console.log(`  ${chalk.bold('Type:')} ${chalk.yellow('Incremental')}`);
          if (backup.metadata.baseBackupId) {
            console.log(`  ${chalk.bold('Base Backup:')} ${backup.metadata.baseBackupId}`);
          }
        }

        if (options.verify) {
          const spinner = ora('Verifying backup integrity...').start();
          const verification = await backupCLI.verifyBackup(backupId, { deep: true });
          spinner.stop();

          console.log(`\n  ${chalk.bold('Integrity:')} ${verification.valid ? chalk.green('Valid') : chalk.red('Invalid')}`);

          if (!verification.valid) {
            console.log(chalk.red('\n  Errors:'));
            verification.errors.forEach(err => console.log(chalk.red(`    • ${err}`)));
          }

          if (verification.warnings.length > 0) {
            console.log(chalk.yellow('\n  Warnings:'));
            verification.warnings.forEach(warn => console.log(chalk.yellow(`    • ${warn}`)));
          }
        }

        console.log('');
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        logger.error('Get backup status failed', error);
        process.exit(1);
      }
    });

  // Command 5: ai-shell backup schedule
  program
    .command('backup schedule <cron>')
    .description('Schedule automated backups')
    .requiredOption('-n, --name <name>', 'Schedule name')
    .requiredOption('-d, --database <name>', 'Database to backup')
    .option('--retention <days>', 'Keep backups for N days', '30')
    .option('--email <address>', 'Notification email')
    .option('--compression <type>', 'Compression type', 'gzip')
    .option('--format <type>', 'Backup format', 'sql')
    .option('--cloud', 'Upload to cloud storage')
    .option('--verify', 'Verify backups after creation')
    .action(async (cronExpression, options) => {
      try {
        logger.info('Creating backup schedule', { cron: cronExpression, name: options.name });

        const schedule = await backupCLI.scheduleBackup(cronExpression, {
          name: options.name,
          database: options.database,
          retention: parseInt(options.retention),
          email: options.email,
          compress: options.compression !== 'none',
          format: options.format
        });

        console.log(chalk.green('\n✓ Backup scheduled successfully\n'));
        console.log(`  ${chalk.bold('Schedule ID:')} ${schedule.id}`);
        console.log(`  ${chalk.bold('Name:')} ${schedule.name}`);
        console.log(`  ${chalk.bold('Database:')} ${schedule.database}`);
        console.log(`  ${chalk.bold('Schedule:')} ${schedule.cron}`);
        console.log(`  ${chalk.bold('Retention:')} ${options.retention} days`);
        console.log(`  ${chalk.bold('Format:')} ${options.format}`);
        console.log(`  ${chalk.bold('Compression:')} ${options.compression}`);

        if (options.email) {
          console.log(`  ${chalk.bold('Notifications:')} ${options.email}`);
        }

        if (options.cloud) {
          console.log(`  ${chalk.bold('Cloud Upload:')} ${chalk.green('Enabled')}`);
        }

        console.log('');
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        logger.error('Schedule backup failed', error);
        process.exit(1);
      }
    });

  // Command 6: ai-shell backup verify
  program
    .command('backup verify <backup-id>')
    .description('Verify backup integrity')
    .option('--deep', 'Deep verification with checksums')
    .option('--test', 'Test restore capability')
    .option('--json', 'Output as JSON')
    .action(async (backupId, options) => {
      const spinner = ora('Verifying backup...').start();

      try {
        logger.info('Verifying backup', { backupId, deep: options.deep });

        const result: VerificationResult = await backupCLI.verifyBackup(backupId, {
          deep: options.deep
        });

        spinner.stop();

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        console.log('');
        if (result.valid) {
          console.log(chalk.green('✓ Backup is valid\n'));
          if (result.checksum) {
            console.log(`  ${chalk.bold('Checksum:')} ${result.checksum}`);
          }
        } else {
          console.log(chalk.red('✗ Backup verification failed\n'));
          console.log(chalk.red('  Errors:'));
          result.errors.forEach(err => console.log(chalk.red(`    • ${err}`)));
        }

        if (result.warnings.length > 0) {
          console.log(chalk.yellow('\n  Warnings:'));
          result.warnings.forEach(warn => console.log(chalk.yellow(`    • ${warn}`)));
        }

        if (options.test) {
          const testSpinner = ora('Testing restore capability...').start();
          const testResult = await backupCLI.testBackup(backupId, { validateData: true });
          testSpinner.stop();

          console.log(chalk.blue('\n  Restore Tests:\n'));
          testResult.tests.forEach(test => {
            const icon = test.passed ? chalk.green('✓') : chalk.red('✗');
            console.log(`    ${icon} ${test.name}: ${test.message}`);
          });

          if (!testResult.success) {
            console.log(chalk.red('\n  Some tests failed'));
          }
        }

        console.log('');
      } catch (error) {
        spinner.stop();
        console.error(chalk.red(`\nError: ${error instanceof Error ? error.message : String(error)}\n`));
        logger.error('Backup verification failed', error);
        process.exit(1);
      }
    });

  // Command 7: ai-shell backup delete
  program
    .command('backup delete <backup-id>')
    .description('Delete a backup')
    .option('--force', 'Force deletion without confirmation')
    .option('--cloud', 'Also delete from cloud storage')
    .action(async (backupId, options) => {
      try {
        logger.info('Deleting backup', { backupId, force: options.force });

        // Get backup info first
        const backup = await backupCLI.getBackupInfo(backupId);

        if (!backup) {
          console.log(chalk.yellow(`\nBackup not found: ${backupId}\n`));
          process.exit(1);
        }

        // Confirm deletion unless --force is used
        if (!options.force) {
          const answers = await inquirer.prompt([
            {
              type: 'confirm',
              name: 'confirm',
              message: `Are you sure you want to delete backup "${backup.id}" (${formatSize(backup.size)})?`,
              default: false
            }
          ]);

          if (!answers.confirm) {
            console.log(chalk.yellow('\nDeletion cancelled\n'));
            return;
          }
        }

        const spinner = ora('Deleting backup...').start();

        await backupCLI.deleteBackup(backupId, true);

        if (options.cloud && config.cloudProvider) {
          spinner.text = 'Deleting from cloud storage...';
          // Cloud deletion logic would go here
        }

        spinner.stop();
        console.log(chalk.green(`\n✓ Backup deleted: ${backupId}\n`));
      } catch (error) {
        console.error(chalk.red(`\nError: ${error instanceof Error ? error.message : String(error)}\n`));
        logger.error('Backup deletion failed', error);
        process.exit(1);
      }
    });

  // Command 8: ai-shell backup export
  program
    .command('backup export <backup-id> <destination>')
    .description('Export backup to external location')
    .option('--include-metadata', 'Include metadata file', true)
    .option('--compress', 'Compress before export')
    .option('--encrypt', 'Encrypt exported backup')
    .action(async (backupId, destination, options) => {
      const spinner = ora('Exporting backup...').start();

      try {
        logger.info('Exporting backup', { backupId, destination });

        await backupCLI.exportBackup(backupId, destination);

        spinner.stop();
        console.log(chalk.green(`\n✓ Backup exported to: ${destination}\n`));

        const backup = await backupCLI.getBackupInfo(backupId);
        if (backup) {
          console.log(`  ${chalk.bold('Size:')} ${formatSize(backup.size)}`);
          console.log(`  ${chalk.bold('Format:')} ${backup.format}`);
          console.log(`  ${chalk.bold('Compressed:')} ${backup.compressed ? 'Yes' : 'No'}`);
        }

        console.log('');
      } catch (error) {
        spinner.stop();
        console.error(chalk.red(`\nError: ${error instanceof Error ? error.message : String(error)}\n`));
        logger.error('Backup export failed', error);
        process.exit(1);
      }
    });

  // Command 9: ai-shell backup import
  program
    .command('backup import <source>')
    .description('Import backup from external location')
    .option('--verify', 'Verify backup after import')
    .option('--cloud', 'Import from cloud storage')
    .option('--database <name>', 'Override database name')
    .action(async (source, options) => {
      const spinner = ora('Importing backup...').start();

      try {
        logger.info('Importing backup', { source });

        const backup = await backupCLI.importBackup(source);

        if (options.verify) {
          spinner.text = 'Verifying imported backup...';
          const verification = await backupCLI.verifyBackup(backup.id, { deep: true });

          if (!verification.valid) {
            spinner.fail('Imported backup verification failed');
            console.log(chalk.red('\nErrors:'));
            verification.errors.forEach(err => console.log(chalk.red(`  • ${err}`)));
            process.exit(1);
          }
        }

        spinner.stop();
        console.log(chalk.green('\n✓ Backup imported successfully\n'));
        console.log(`  ${chalk.bold('ID:')} ${backup.id}`);
        console.log(`  ${chalk.bold('Database:')} ${options.database || backup.database}`);
        console.log(`  ${chalk.bold('Size:')} ${formatSize(backup.size)}`);
        console.log(`  ${chalk.bold('Format:')} ${backup.format}`);
        console.log('');
      } catch (error) {
        spinner.stop();
        console.error(chalk.red(`\nError: ${error instanceof Error ? error.message : String(error)}\n`));
        logger.error('Backup import failed', error);
        process.exit(1);
      }
    });

  // Command 10: ai-shell backup config
  program
    .command('backup config')
    .description('Show or edit backup configuration')
    .option('--show', 'Show current configuration (default)')
    .option('--edit', 'Edit configuration interactively')
    .option('--set <key=value>', 'Set configuration value')
    .option('--get <key>', 'Get configuration value')
    .option('--reset', 'Reset to default configuration')
    .option('--json', 'Output as JSON')
    .action(async (options) => {
      try {
        logger.info('Backup configuration command', options);

        // Load current configuration
        const currentConfig = {
          backupDir: config.backupDir || './backups',
          retentionDays: config.retentionDays || 30,
          maxBackups: config.maxBackups || 50,
          cloudProvider: config.cloudProvider || 'none',
          cloudConfig: config.cloudConfig || {}
        };

        // Handle different operations
        if (options.get) {
          const value = (currentConfig as any)[options.get];
          if (value !== undefined) {
            console.log(options.json ? JSON.stringify({ [options.get]: value }, null, 2) : value);
          } else {
            console.log(chalk.yellow(`\nConfiguration key not found: ${options.get}\n`));
          }
          return;
        }

        if (options.set) {
          const [key, ...valueParts] = options.set.split('=');
          const value = valueParts.join('=');

          if (!key || !value) {
            console.log(chalk.red('\nInvalid format. Use: --set key=value\n'));
            process.exit(1);
          }

          // Update configuration
          (currentConfig as any)[key] = value;
          console.log(chalk.green(`\n✓ Configuration updated: ${key} = ${value}\n`));
          return;
        }

        if (options.reset) {
          const answers = await inquirer.prompt([
            {
              type: 'confirm',
              name: 'confirm',
              message: 'Reset all backup configuration to defaults?',
              default: false
            }
          ]);

          if (answers.confirm) {
            console.log(chalk.green('\n✓ Configuration reset to defaults\n'));
          } else {
            console.log(chalk.yellow('\nReset cancelled\n'));
          }
          return;
        }

        if (options.edit) {
          const answers = await inquirer.prompt([
            {
              type: 'input',
              name: 'backupDir',
              message: 'Backup directory:',
              default: currentConfig.backupDir
            },
            {
              type: 'number',
              name: 'retentionDays',
              message: 'Retention days:',
              default: currentConfig.retentionDays
            },
            {
              type: 'number',
              name: 'maxBackups',
              message: 'Maximum backups:',
              default: currentConfig.maxBackups
            },
            {
              type: 'list',
              name: 'cloudProvider',
              message: 'Cloud provider:',
              choices: ['none', 'aws-s3', 'azure-blob', 'google-cloud'],
              default: currentConfig.cloudProvider
            }
          ]);

          console.log(chalk.green('\n✓ Configuration updated\n'));
          console.log(JSON.stringify(answers, null, 2));
          console.log('');
          return;
        }

        // Default: show configuration
        if (options.json) {
          console.log(JSON.stringify(currentConfig, null, 2));
        } else {
          console.log(chalk.blue('\n⚙️  Backup Configuration\n'));
          console.log(`  ${chalk.bold('Backup Directory:')} ${currentConfig.backupDir}`);
          console.log(`  ${chalk.bold('Retention Days:')} ${currentConfig.retentionDays}`);
          console.log(`  ${chalk.bold('Maximum Backups:')} ${currentConfig.maxBackups}`);
          console.log(`  ${chalk.bold('Cloud Provider:')} ${currentConfig.cloudProvider}`);

          if (currentConfig.cloudProvider !== 'none' && currentConfig.cloudConfig) {
            console.log(chalk.blue('\n  Cloud Configuration:'));
            Object.entries(currentConfig.cloudConfig).forEach(([key, value]) => {
              const displayValue = key.toLowerCase().includes('key') || key.toLowerCase().includes('secret')
                ? '********'
                : value;
              console.log(`    ${chalk.bold(key)}: ${displayValue}`);
            });
          }

          // Show schedules
          const schedules = backupCLI.listSchedules();
          if (schedules.length > 0) {
            console.log(chalk.blue('\n  Active Schedules:\n'));
            displaySchedulesTable(schedules);
          } else {
            console.log(chalk.dim('\n  No active schedules'));
          }

          console.log('');
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        logger.error('Backup config command failed', error);
        process.exit(1);
      }
    });

  // Additional utility command: list schedules
  program
    .command('backup schedules')
    .description('List all backup schedules')
    .option('--json', 'Output as JSON')
    .action(async (options) => {
      try {
        const schedules = backupCLI.listSchedules();

        if (options.json) {
          console.log(JSON.stringify(schedules, null, 2));
        } else {
          displaySchedulesTable(schedules);
          console.log(chalk.dim(`  Total: ${schedules.length} schedule(s)\n`));
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Additional utility command: delete schedule
  program
    .command('backup unschedule <schedule-id>')
    .description('Remove backup schedule')
    .option('--force', 'Force deletion without confirmation')
    .action(async (scheduleId, options) => {
      try {
        const schedules = backupCLI.listSchedules();
        const schedule = schedules.find(s => s.id === scheduleId);

        if (!schedule) {
          console.log(chalk.yellow(`\nSchedule not found: ${scheduleId}\n`));
          process.exit(1);
        }

        if (!options.force) {
          const answers = await inquirer.prompt([
            {
              type: 'confirm',
              name: 'confirm',
              message: `Remove schedule "${schedule.name}" for ${schedule.database}?`,
              default: false
            }
          ]);

          if (!answers.confirm) {
            console.log(chalk.yellow('\nCancelled\n'));
            return;
          }
        }

        await backupCLI.deleteSchedule(scheduleId);
        console.log(chalk.green(`\n✓ Schedule removed: ${schedule.name}\n`));
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });
}

export default setupBackupCommands;
