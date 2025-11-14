/**
 * Backup/Recovery System
 * Automated backup and restore for multiple database types
 * Commands: ai-shell backup, ai-shell restore <backup-id>, ai-shell backup schedule
 */

import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as path from 'path';
import archiver from 'archiver';
import { createWriteStream } from 'fs';

const execAsync = promisify(exec);

interface BackupConfig {
  enabled: boolean;
  schedule: string; // cron format
  retention: number; // days
  compression: boolean;
  location: 'local' | 's3';
  localPath?: string;
  s3Config?: {
    bucket: string;
    region: string;
    accessKeyId: string;
    secretAccessKey: string;
  };
}

interface BackupMetadata {
  id: string;
  timestamp: number;
  database: string;
  type: DatabaseType;
  size: number;
  compressed: boolean;
  location: string;
  status: 'completed' | 'in-progress' | 'failed';
  error?: string;
  duration?: number;
}

interface RestoreOptions {
  pointInTime?: number;
  targetDatabase?: string;
  dryRun?: boolean;
}

export class BackupSystem {
  private logger = createLogger('BackupSystem');
  private backups = new Map<string, BackupMetadata>();
  private config: BackupConfig;
  private scheduleTimer?: NodeJS.Timeout;

  constructor(
    private dbManager: DatabaseConnectionManager,
    private stateManager: StateManager
  ) {
    this.config = this.loadConfig();
    this.loadBackupHistory();
  }

  /**
   * Create backup
   */
  async createBackup(connectionName?: string): Promise<BackupMetadata> {
    const startTime = Date.now();
    const connection = connectionName
      ? this.dbManager.getConnection(connectionName)
      : this.dbManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    const backupId = `backup-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const backupDir = this.config.localPath || './backups';

    this.logger.info('Creating backup', {
      backupId,
      database: connection.config.database,
      type: connection.type
    });

    // Create backup directory
    await fs.mkdir(backupDir, { recursive: true });

    const metadata: BackupMetadata = {
      id: backupId,
      timestamp: Date.now(),
      database: connection.config.database || 'default',
      type: connection.type,
      size: 0,
      compressed: this.config.compression,
      location: backupDir,
      status: 'in-progress'
    };

    this.backups.set(backupId, metadata);

    try {
      let backupPath: string;

      switch (connection.type) {
        case DatabaseType.POSTGRESQL:
          backupPath = await this.backupPostgreSQL(connection.config, backupDir, backupId);
          break;

        case DatabaseType.MYSQL:
          backupPath = await this.backupMySQL(connection.config, backupDir, backupId);
          break;

        case DatabaseType.SQLITE:
          backupPath = await this.backupSQLite(connection.config, backupDir, backupId);
          break;

        case DatabaseType.MONGODB:
          backupPath = await this.backupMongoDB(connection.config, backupDir, backupId);
          break;

        default:
          throw new Error(`Unsupported database type: ${connection.type}`);
      }

      // Compress if enabled
      if (this.config.compression) {
        backupPath = await this.compressBackup(backupPath);
      }

      // Get file size
      const stats = await fs.stat(backupPath);
      metadata.size = stats.size;
      metadata.status = 'completed';
      metadata.duration = Date.now() - startTime;
      metadata.location = backupPath;

      this.backups.set(backupId, metadata);
      this.saveBackupHistory();

      this.logger.info('Backup completed', {
        backupId,
        size: metadata.size,
        duration: metadata.duration
      });

      // Upload to S3 if configured
      if (this.config.location === 's3' && this.config.s3Config) {
        await this.uploadToS3(backupPath, backupId);
      }

      // Clean old backups
      await this.cleanOldBackups();

      return metadata;
    } catch (error) {
      metadata.status = 'failed';
      metadata.error = error instanceof Error ? error.message : String(error);
      this.backups.set(backupId, metadata);
      this.saveBackupHistory();

      this.logger.error('Backup failed', error, { backupId });
      throw error;
    }
  }

  /**
   * Backup PostgreSQL
   */
  private async backupPostgreSQL(
    config: any,
    backupDir: string,
    backupId: string
  ): Promise<string> {
    const backupFile = path.join(backupDir, `${backupId}.sql`);

    const pgDumpCmd = [
      'pg_dump',
      `-h ${config.host || 'localhost'}`,
      `-p ${config.port || 5432}`,
      `-U ${config.username}`,
      `-d ${config.database}`,
      `--file=${backupFile}`,
      '--format=plain',
      '--no-owner',
      '--no-acl'
    ].join(' ');

    await execAsync(pgDumpCmd, {
      env: { ...process.env, PGPASSWORD: config.password }
    });

    return backupFile;
  }

  /**
   * Backup MySQL
   */
  private async backupMySQL(
    config: any,
    backupDir: string,
    backupId: string
  ): Promise<string> {
    const backupFile = path.join(backupDir, `${backupId}.sql`);

    const mysqldumpCmd = [
      'mysqldump',
      `-h ${config.host || 'localhost'}`,
      `-P ${config.port || 3306}`,
      `-u ${config.username}`,
      `-p${config.password}`,
      config.database,
      `> ${backupFile}`
    ].join(' ');

    await execAsync(mysqldumpCmd);

    return backupFile;
  }

  /**
   * Backup SQLite
   */
  private async backupSQLite(
    config: any,
    backupDir: string,
    backupId: string
  ): Promise<string> {
    const backupFile = path.join(backupDir, `${backupId}.db`);
    await fs.copyFile(config.database, backupFile);
    return backupFile;
  }

  /**
   * Backup MongoDB
   */
  private async backupMongoDB(
    config: any,
    backupDir: string,
    backupId: string
  ): Promise<string> {
    const backupPath = path.join(backupDir, backupId);

    const mongodumpCmd = [
      'mongodump',
      `--host=${config.host || 'localhost'}`,
      `--port=${config.port || 27017}`,
      `--db=${config.database}`,
      `--out=${backupPath}`,
      config.username ? `--username=${config.username}` : '',
      config.password ? `--password=${config.password}` : ''
    ]
      .filter(Boolean)
      .join(' ');

    await execAsync(mongodumpCmd);

    return backupPath;
  }

  /**
   * Compress backup
   */
  private async compressBackup(backupPath: string): Promise<string> {
    const outputPath = `${backupPath}.tar.gz`;

    return new Promise((resolve, reject) => {
      const output = createWriteStream(outputPath);
      const archive = archiver('tar', { gzip: true, gzipOptions: { level: 9 } });

      output.on('close', () => resolve(outputPath));
      archive.on('error', reject);

      archive.pipe(output);

      // Add file or directory
      fs.stat(backupPath).then((stats) => {
        if (stats.isDirectory()) {
          archive.directory(backupPath, false);
        } else {
          archive.file(backupPath, { name: path.basename(backupPath) });
        }
        archive.finalize();
      });
    });
  }

  /**
   * Upload to S3
   */
  private async uploadToS3(_backupPath: string, backupId: string): Promise<void> {
    // TODO: Implement S3 upload with AWS SDK
    this.logger.info('S3 upload (not implemented)', { backupId });
  }

  /**
   * Restore backup
   */
  async restoreBackup(backupId: string, options: RestoreOptions = {}): Promise<void> {
    const backup = this.backups.get(backupId);

    if (!backup) {
      throw new Error(`Backup not found: ${backupId}`);
    }

    if (backup.status !== 'completed') {
      throw new Error(`Backup is not in completed state: ${backup.status}`);
    }

    this.logger.info('Restoring backup', { backupId, options });

    if (options.dryRun) {
      this.logger.info('Dry run - no changes will be made');
      return;
    }

    const connection = this.dbManager.getActive();
    if (!connection) {
      throw new Error('No active connection');
    }

    try {
      let backupPath = backup.location;

      // Decompress if needed
      if (backup.compressed && backupPath.endsWith('.tar.gz')) {
        backupPath = await this.decompressBackup(backupPath);
      }

      switch (backup.type) {
        case DatabaseType.POSTGRESQL:
          await this.restorePostgreSQL(connection.config, backupPath);
          break;

        case DatabaseType.MYSQL:
          await this.restoreMySQL(connection.config, backupPath);
          break;

        case DatabaseType.SQLITE:
          await this.restoreSQLite(connection.config, backupPath);
          break;

        case DatabaseType.MONGODB:
          await this.restoreMongoDB(connection.config, backupPath);
          break;
      }

      this.logger.info('Restore completed', { backupId });
    } catch (error) {
      this.logger.error('Restore failed', error, { backupId });
      throw error;
    }
  }

  /**
   * Decompress backup
   */
  private async decompressBackup(compressedPath: string): Promise<string> {
    const outputPath = compressedPath.replace('.tar.gz', '');
    await execAsync(`tar -xzf ${compressedPath} -C ${path.dirname(outputPath)}`);
    return outputPath;
  }

  /**
   * Restore PostgreSQL
   */
  private async restorePostgreSQL(config: any, backupPath: string): Promise<void> {
    const psqlCmd = [
      'psql',
      `-h ${config.host || 'localhost'}`,
      `-p ${config.port || 5432}`,
      `-U ${config.username}`,
      `-d ${config.database}`,
      `-f ${backupPath}`
    ].join(' ');

    await execAsync(psqlCmd, {
      env: { ...process.env, PGPASSWORD: config.password }
    });
  }

  /**
   * Restore MySQL
   */
  private async restoreMySQL(config: any, backupPath: string): Promise<void> {
    const mysqlCmd = [
      'mysql',
      `-h ${config.host || 'localhost'}`,
      `-P ${config.port || 3306}`,
      `-u ${config.username}`,
      `-p${config.password}`,
      config.database,
      `< ${backupPath}`
    ].join(' ');

    await execAsync(mysqlCmd);
  }

  /**
   * Restore SQLite
   */
  private async restoreSQLite(config: any, backupPath: string): Promise<void> {
    await fs.copyFile(backupPath, config.database);
  }

  /**
   * Restore MongoDB
   */
  private async restoreMongoDB(config: any, backupPath: string): Promise<void> {
    const mongorestoreCmd = [
      'mongorestore',
      `--host=${config.host || 'localhost'}`,
      `--port=${config.port || 27017}`,
      `--db=${config.database}`,
      backupPath,
      config.username ? `--username=${config.username}` : '',
      config.password ? `--password=${config.password}` : '',
      '--drop'
    ]
      .filter(Boolean)
      .join(' ');

    await execAsync(mongorestoreCmd);
  }

  /**
   * Schedule automated backups
   */
  scheduleBackups(cronExpression: string): void {
    if (this.scheduleTimer) {
      clearInterval(this.scheduleTimer);
    }

    // Simple interval-based scheduling (for production, use node-cron)
    const intervalMs = this.parseCronToMs(cronExpression);

    this.scheduleTimer = setInterval(async () => {
      try {
        await this.createBackup();
      } catch (error) {
        this.logger.error('Scheduled backup failed', error);
      }
    }, intervalMs);

    this.config.schedule = cronExpression;
    this.config.enabled = true;
    this.saveConfig();

    this.logger.info('Backup schedule configured', { cronExpression });
  }

  /**
   * Stop scheduled backups
   */
  stopScheduledBackups(): void {
    if (this.scheduleTimer) {
      clearInterval(this.scheduleTimer);
      this.scheduleTimer = undefined;
    }

    this.config.enabled = false;
    this.saveConfig();

    this.logger.info('Scheduled backups stopped');
  }

  /**
   * List backups
   */
  listBackups(limit?: number): BackupMetadata[] {
    const backups = Array.from(this.backups.values())
      .sort((a, b) => b.timestamp - a.timestamp);

    return limit ? backups.slice(0, limit) : backups;
  }

  /**
   * Delete backup
   */
  async deleteBackup(backupId: string): Promise<void> {
    const backup = this.backups.get(backupId);

    if (!backup) {
      throw new Error(`Backup not found: ${backupId}`);
    }

    try {
      // Delete file
      await fs.unlink(backup.location);

      // Remove from map
      this.backups.delete(backupId);
      this.saveBackupHistory();

      this.logger.info('Backup deleted', { backupId });
    } catch (error) {
      this.logger.error('Failed to delete backup', error, { backupId });
      throw error;
    }
  }

  /**
   * Clean old backups based on retention policy
   */
  private async cleanOldBackups(): Promise<void> {
    const retentionMs = this.config.retention * 24 * 60 * 60 * 1000;
    const cutoffTime = Date.now() - retentionMs;

    const oldBackups = Array.from(this.backups.values()).filter(
      (b) => b.timestamp < cutoffTime && b.status === 'completed'
    );

    for (const backup of oldBackups) {
      try {
        await this.deleteBackup(backup.id);
      } catch (error) {
        this.logger.error('Failed to clean old backup', error, { backupId: backup.id });
      }
    }

    if (oldBackups.length > 0) {
      this.logger.info('Old backups cleaned', { count: oldBackups.length });
    }
  }

  /**
   * Get backup statistics
   */
  getStatistics(): {
    totalBackups: number;
    totalSize: number;
    latestBackup?: BackupMetadata;
    oldestBackup?: BackupMetadata;
    successRate: number;
  } {
    const backups = Array.from(this.backups.values());
    const completed = backups.filter((b) => b.status === 'completed');

    const totalSize = completed.reduce((sum, b) => sum + b.size, 0);

    const sorted = completed.sort((a, b) => b.timestamp - a.timestamp);

    return {
      totalBackups: backups.length,
      totalSize,
      latestBackup: sorted[0],
      oldestBackup: sorted[sorted.length - 1],
      successRate: backups.length > 0 ? (completed.length / backups.length) * 100 : 0
    };
  }

  /**
   * Parse cron expression to milliseconds (simplified)
   */
  private parseCronToMs(cron: string): number {
    // Simplified: just support "every X hours/minutes"
    // For production, use node-cron library
    if (cron.includes('hour')) {
      const hours = parseInt(cron) || 24;
      return hours * 60 * 60 * 1000;
    }
    if (cron.includes('minute')) {
      const minutes = parseInt(cron) || 60;
      return minutes * 60 * 1000;
    }
    // Default: daily
    return 24 * 60 * 60 * 1000;
  }

  /**
   * Load config from state
   */
  private loadConfig(): BackupConfig {
    try {
      const stored = this.stateManager.get('backup-config');
      if (stored) {
        return stored as BackupConfig;
      }
    } catch (error) {
      this.logger.warn('Failed to load backup config', { error });
    }

    return {
      enabled: false,
      schedule: '0 2 * * *', // Daily at 2 AM
      retention: 30,
      compression: true,
      location: 'local',
      localPath: './backups'
    };
  }

  /**
   * Save config to state
   */
  private saveConfig(): void {
    try {
      this.stateManager.set('backup-config', this.config, {
        metadata: { type: 'backup-configuration' }
      });
    } catch (error) {
      this.logger.error('Failed to save backup config', error);
    }
  }

  /**
   * Load backup history from state
   */
  private loadBackupHistory(): void {
    try {
      const stored = this.stateManager.get('backup-history');
      if (stored && Array.isArray(stored)) {
        stored.forEach((backup: BackupMetadata) => {
          this.backups.set(backup.id, backup);
        });
        this.logger.info('Loaded backup history', { count: this.backups.size });
      }
    } catch (error) {
      this.logger.warn('Failed to load backup history', { error });
    }
  }

  /**
   * Save backup history to state
   */
  private saveBackupHistory(): void {
    try {
      const backups = Array.from(this.backups.values());
      this.stateManager.set('backup-history', backups, {
        metadata: { type: 'backup-history' }
      });
    } catch (error) {
      this.logger.error('Failed to save backup history', error);
    }
  }
}
