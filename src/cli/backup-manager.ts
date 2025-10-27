/**
 * Backup Manager
 * Automated backup and restore with compression, metadata tracking, and scheduling
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import archiver from 'archiver';
import { createWriteStream } from 'fs';
import { EventEmitter } from 'eventemitter3';

const execAsync = promisify(exec);

/**
 * Backup options
 */
export interface BackupOptions {
  database: string;
  host?: string;
  port?: number;
  user?: string;
  password?: string;
  tables?: string[];
  format?: 'sql' | 'json' | 'csv';
  compress?: boolean;
  incremental?: boolean;
  lastBackupTimestamp?: number;
}

/**
 * Restore options
 */
export interface RestoreOptions {
  targetDatabase?: string;
  tables?: string[];
  dryRun?: boolean;
  dropExisting?: boolean;
  continueOnError?: boolean;
}

/**
 * Backup information
 */
export interface BackupInfo {
  id: string;
  timestamp: number;
  database: string;
  format: string;
  compressed: boolean;
  size: number;
  tables: string[];
  path: string;
  metadata: {
    host?: string;
    port?: number;
    incremental?: boolean;
    baseBackupId?: string;
    checksum?: string;
  };
}

/**
 * Schedule configuration
 */
export interface ScheduleConfig {
  cron: string;
  enabled: boolean;
  options: BackupOptions;
}

/**
 * Backup events
 */
export interface BackupEvents {
  backupStart: (id: string) => void;
  backupProgress: (id: string, progress: number) => void;
  backupComplete: (info: BackupInfo) => void;
  backupError: (error: Error) => void;
  restoreStart: (backupPath: string) => void;
  restoreProgress: (progress: number) => void;
  restoreComplete: () => void;
  restoreError: (error: Error) => void;
}

/**
 * Backup Manager
 */
export class BackupManager extends EventEmitter<BackupEvents> {
  private schedules = new Map<string, NodeJS.Timeout>();

  constructor(
    private readonly config: {
      defaultBackupDir?: string;
      retentionDays?: number;
      maxBackups?: number;
    } = {}
  ) {
    super();
    this.config.defaultBackupDir = this.config.defaultBackupDir || './backups';
    this.config.retentionDays = this.config.retentionDays || 30;
    this.config.maxBackups = this.config.maxBackups || 10;
  }

  /**
   * Create backup
   */
  async createBackup(options: BackupOptions): Promise<BackupInfo> {
    const backupId = this.generateBackupId();
    const timestamp = Date.now();

    this.emit('backupStart', backupId);

    try {
      // Ensure backup directory exists
      const backupDir = path.join(this.config.defaultBackupDir!, options.database);
      await fs.mkdir(backupDir, { recursive: true });

      // Generate backup filename
      const format = options.format || 'sql';
      const extension = format === 'sql' ? 'sql' : format;
      const filename = `${options.database}_${timestamp}_${backupId}.${extension}`;
      const backupPath = path.join(backupDir, filename);

      // Perform backup based on format
      let tables: string[];
      let size: number;

      switch (format) {
        case 'sql':
          ({ tables, size } = await this.backupToSQL(options, backupPath));
          break;
        case 'json':
          ({ tables, size } = await this.backupToJSON(options, backupPath));
          break;
        case 'csv':
          ({ tables, size } = await this.backupToCSV(options, backupPath));
          break;
        default:
          throw new Error(`Unsupported backup format: ${format}`);
      }

      // Compress if requested
      let finalPath = backupPath;
      let finalSize = size;

      if (options.compress) {
        const compressedPath = `${backupPath}.gz`;
        await this.compressFile(backupPath, compressedPath);
        await fs.unlink(backupPath);
        finalPath = compressedPath;

        const stats = await fs.stat(compressedPath);
        finalSize = stats.size;
      }

      // Generate checksum
      const checksum = await this.generateChecksum(finalPath);

      // Create backup info
      const backupInfo: BackupInfo = {
        id: backupId,
        timestamp,
        database: options.database,
        format,
        compressed: options.compress || false,
        size: finalSize,
        tables,
        path: finalPath,
        metadata: {
          host: options.host,
          port: options.port,
          incremental: options.incremental,
          checksum
        }
      };

      // Save metadata
      await this.saveBackupMetadata(backupInfo);

      // Cleanup old backups
      await this.cleanupOldBackups(options.database);

      this.emit('backupComplete', backupInfo);
      return backupInfo;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.emit('backupError', err);
      throw err;
    }
  }

  /**
   * Restore from backup
   */
  async restoreBackup(backupPath: string, options: RestoreOptions = {}): Promise<void> {
    this.emit('restoreStart', backupPath);

    try {
      // Verify backup file exists
      await fs.access(backupPath);

      // Load backup metadata
      const metadata = await this.loadBackupMetadata(backupPath);

      if (!metadata) {
        throw new Error('Backup metadata not found');
      }

      // Verify checksum
      if (metadata.metadata.checksum) {
        const checksum = await this.generateChecksum(backupPath);
        if (checksum !== metadata.metadata.checksum) {
          throw new Error('Backup file corrupted (checksum mismatch)');
        }
      }

      let restorePath = backupPath;

      // Decompress if needed
      if (metadata.compressed) {
        restorePath = backupPath.replace(/\.gz$/, '');
        await this.decompressFile(backupPath, restorePath);
      }

      // Dry run check
      if (options.dryRun) {
        console.log('Dry run - would restore from:', restorePath);
        console.log('Target database:', options.targetDatabase || metadata.database);
        console.log('Tables:', options.tables || metadata.tables);
        return;
      }

      // Perform restore based on format
      switch (metadata.format) {
        case 'sql':
          await this.restoreFromSQL(restorePath, metadata, options);
          break;
        case 'json':
          await this.restoreFromJSON(restorePath, metadata, options);
          break;
        case 'csv':
          await this.restoreFromCSV(restorePath, metadata, options);
          break;
        default:
          throw new Error(`Unsupported restore format: ${metadata.format}`);
      }

      // Cleanup decompressed file if it was created
      if (metadata.compressed && restorePath !== backupPath) {
        await fs.unlink(restorePath);
      }

      this.emit('restoreComplete');
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.emit('restoreError', err);
      throw err;
    }
  }

  /**
   * List backups in directory
   */
  async listBackups(directory?: string): Promise<BackupInfo[]> {
    const backupDir = directory || this.config.defaultBackupDir!;

    try {
      const entries = await fs.readdir(backupDir, { withFileTypes: true });
      const backups: BackupInfo[] = [];

      for (const entry of entries) {
        if (entry.isDirectory()) {
          const dbBackupDir = path.join(backupDir, entry.name);
          const metadataFiles = await fs.readdir(dbBackupDir);

          for (const file of metadataFiles) {
            if (file.endsWith('.metadata.json')) {
              const metadataPath = path.join(dbBackupDir, file);
              const metadata = JSON.parse(await fs.readFile(metadataPath, 'utf-8'));
              backups.push(metadata);
            }
          }
        }
      }

      // Sort by timestamp (newest first)
      return backups.sort((a, b) => b.timestamp - a.timestamp);
    } catch (error) {
      console.error('Failed to list backups:', error);
      return [];
    }
  }

  /**
   * Schedule backup
   */
  async scheduleBackup(cron: string, options: BackupOptions): Promise<void> {
    // Note: For production, use node-cron library
    // This is a simplified version
    const scheduleId = `${options.database}_${Date.now()}`;

    // Parse simple cron format: "0 0 * * *" (daily at midnight)
    const interval = this.parseCronToMilliseconds(cron);

    const timer = setInterval(async () => {
      try {
        await this.createBackup(options);
      } catch (error) {
        console.error('Scheduled backup failed:', error);
      }
    }, interval);

    this.schedules.set(scheduleId, timer);
  }

  /**
   * Verify backup integrity
   */
  async verifyBackup(backupPath: string): Promise<boolean> {
    try {
      const metadata = await this.loadBackupMetadata(backupPath);

      if (!metadata) {
        return false;
      }

      // Verify file exists
      await fs.access(backupPath);

      // Verify checksum
      if (metadata.metadata.checksum) {
        const checksum = await this.generateChecksum(backupPath);
        return checksum === metadata.metadata.checksum;
      }

      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Backup to SQL format
   */
  private async backupToSQL(options: BackupOptions, outputPath: string): Promise<{ tables: string[]; size: number }> {
    // Build mysqldump command (example for MySQL)
    const parts = ['mysqldump'];

    if (options.host) parts.push(`-h ${options.host}`);
    if (options.port) parts.push(`-P ${options.port}`);
    if (options.user) parts.push(`-u ${options.user}`);
    if (options.password) parts.push(`-p${options.password}`);

    parts.push(options.database);

    if (options.tables && options.tables.length > 0) {
      parts.push(...options.tables);
    }

    parts.push(`> ${outputPath}`);

    const command = parts.join(' ');
    await execAsync(command);

    const stats = await fs.stat(outputPath);

    // Get tables list
    const tables = options.tables || await this.getTablesList(options.database);

    return { tables, size: stats.size };
  }

  /**
   * Backup to JSON format
   */
  private async backupToJSON(options: BackupOptions, outputPath: string): Promise<{ tables: string[]; size: number }> {
    // This is a simplified implementation
    // In production, you'd query each table and export as JSON
    const data = {
      database: options.database,
      timestamp: Date.now(),
      tables: options.tables || [],
      data: {}
    };

    await fs.writeFile(outputPath, JSON.stringify(data, null, 2), 'utf-8');

    const stats = await fs.stat(outputPath);
    return { tables: options.tables || [], size: stats.size };
  }

  /**
   * Backup to CSV format
   */
  private async backupToCSV(options: BackupOptions, outputPath: string): Promise<{ tables: string[]; size: number }> {
    // Create directory for CSV files
    const csvDir = outputPath.replace(/\.csv$/, '');
    await fs.mkdir(csvDir, { recursive: true });

    const tables = options.tables || [];

    // For each table, export to CSV
    // This is a placeholder - actual implementation would query and export

    const stats = await fs.stat(csvDir);
    return { tables, size: stats.size };
  }

  /**
   * Restore from SQL
   */
  private async restoreFromSQL(backupPath: string, metadata: BackupInfo, options: RestoreOptions): Promise<void> {
    const targetDb = options.targetDatabase || metadata.database;

    // Build mysql command
    const parts = ['mysql'];

    if (metadata.metadata.host) parts.push(`-h ${metadata.metadata.host}`);
    if (metadata.metadata.port) parts.push(`-P ${metadata.metadata.port}`);

    parts.push(targetDb);
    parts.push(`< ${backupPath}`);

    const command = parts.join(' ');
    await execAsync(command);
  }

  /**
   * Restore from JSON
   */
  private async restoreFromJSON(backupPath: string, _metadata: BackupInfo, _options: RestoreOptions): Promise<void> {
    const json = await fs.readFile(backupPath, 'utf-8');
    JSON.parse(json); // Parse but don't use yet

    // Restore logic here
    // This would insert data into target database
  }

  /**
   * Restore from CSV
   */
  private async restoreFromCSV(_backupPath: string, _metadata: BackupInfo, _options: RestoreOptions): Promise<void> {
    // CSV restore logic
    // This would read CSV files and insert into database
  }

  /**
   * Compress file using gzip
   */
  private async compressFile(inputPath: string, outputPath: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const archive = archiver('tar', {
        gzip: true,
        gzipOptions: { level: 9 }
      });
      const output = createWriteStream(outputPath);

      output.on('close', () => resolve());
      archive.on('error', reject);

      archive.pipe(output);
      archive.file(inputPath, { name: path.basename(inputPath) });
      archive.finalize();
    });
  }

  /**
   * Decompress file
   */
  private async decompressFile(inputPath: string, outputPath: string): Promise<void> {
    const command = `gunzip -c ${inputPath} > ${outputPath}`;
    await execAsync(command);
  }

  /**
   * Generate checksum for file
   */
  private async generateChecksum(filePath: string): Promise<string> {
    const command = `sha256sum ${filePath} | awk '{print $1}'`;
    const { stdout } = await execAsync(command);
    return stdout.trim();
  }

  /**
   * Save backup metadata
   */
  private async saveBackupMetadata(info: BackupInfo): Promise<void> {
    const metadataPath = `${info.path}.metadata.json`;
    await fs.writeFile(metadataPath, JSON.stringify(info, null, 2), 'utf-8');
  }

  /**
   * Load backup metadata
   */
  private async loadBackupMetadata(backupPath: string): Promise<BackupInfo | null> {
    try {
      const metadataPath = `${backupPath}.metadata.json`;
      const json = await fs.readFile(metadataPath, 'utf-8');
      return JSON.parse(json);
    } catch (error) {
      return null;
    }
  }

  /**
   * Cleanup old backups based on retention policy
   */
  private async cleanupOldBackups(database: string): Promise<void> {
    const backups = await this.listBackups();
    const dbBackups = backups.filter(b => b.database === database);

    // Remove backups older than retention period
    const retentionMs = this.config.retentionDays! * 24 * 60 * 60 * 1000;
    const cutoffTime = Date.now() - retentionMs;

    // Keep only maxBackups most recent backups
    const toDelete = dbBackups
      .filter(b => b.timestamp < cutoffTime)
      .slice(this.config.maxBackups!);

    for (const backup of toDelete) {
      try {
        await fs.unlink(backup.path);
        await fs.unlink(`${backup.path}.metadata.json`);
      } catch (error) {
        console.error(`Failed to delete backup ${backup.id}:`, error);
      }
    }
  }

  /**
   * Get list of tables in database
   */
  private async getTablesList(_database: string): Promise<string[]> {
    // This would query the database to get table list
    // Placeholder implementation
    return [];
  }

  /**
   * Parse simple cron expression to milliseconds
   */
  private parseCronToMilliseconds(_cron: string): number {
    // Simplified: just support daily backups for now
    // Real implementation would use node-cron
    return 24 * 60 * 60 * 1000; // 24 hours
  }

  /**
   * Generate unique backup ID
   */
  private generateBackupId(): string {
    return `backup_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Shutdown and cleanup
   */
  shutdown(): void {
    // Clear all scheduled backups
    this.schedules.forEach((timer) => clearInterval(timer));
    this.schedules.clear();
  }
}
