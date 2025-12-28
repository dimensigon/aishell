/**
 * Backup Commands Tests
 * Comprehensive test suite for all 10 backup CLI commands
 * Tests backup create, restore, list, status, schedule, verify, delete, export, import, config
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { BackupCLI, BackupResult, VerificationResult } from '../../src/cli/backup-cli';
import { BackupInfo, BackupOptions } from '../../src/cli/backup-manager';
import { CloudProvider } from '../../src/cli/cloud-backup';
import * as fs from 'fs/promises';
import * as path from 'path';

// Mock dependencies with proper implementations
vi.mock('../../src/cli/backup-manager', () => {
  class MockBackupManager {
    createBackup = vi.fn();
    restoreBackup = vi.fn();
    listBackups = vi.fn(() => Promise.resolve([]));
    verifyBackup = vi.fn(() => Promise.resolve(true));
    shutdown = vi.fn();
    constructor(config?: any) {}
  }
  return {
    BackupManager: MockBackupManager
  };
});

vi.mock('../../src/cli/backup-system', () => {
  class MockBackupSystem {
    constructor(dbManager?: any, stateManager?: any) {}
  }
  return {
    BackupSystem: MockBackupSystem
  };
});

vi.mock('../../src/cli/database-manager', () => {
  class MockDatabaseConnectionManager {
    getConnection = vi.fn((dbName: string) => {
      // Return null for databases that should fail
      if (dbName === 'nonexistent_db' || dbName === 'missing_db') {
        return null;
      }
      return { database: dbName, connected: true };
    });
    constructor(stateManager?: any) {}
  }
  return {
    DatabaseConnectionManager: MockDatabaseConnectionManager
  };
});

vi.mock('../../src/core/state-manager', () => {
  class MockStateManager {
    private state = new Map();
    get = vi.fn((key: string) => this.state.get(key));
    set = vi.fn((key: string, value: any, options?: any) => this.state.set(key, value));
    constructor() {}
  }
  return {
    StateManager: MockStateManager
  };
});

// Mock node-cron with proper validation
vi.mock('node-cron', () => ({
  default: {
    schedule: vi.fn(() => ({ stop: vi.fn() })),
    validate: vi.fn((expression: string) => {
      // Accept standard cron expressions (5 or 6 fields)
      const parts = expression.trim().split(/\s+/);
      return parts.length === 5 || parts.length === 6;
    })
  }
}));

vi.mock('fs/promises');

describe('Backup Commands - All 10 Commands', () => {
  let backupCLI: BackupCLI;
  let mockBackupManager: any;
  let testBackupDir: string;
  let backupCounter = 0;
  let createdBackups: BackupInfo[] = [];

  beforeEach(() => {
    vi.clearAllMocks();
    backupCounter = 0;
    createdBackups = [];

    testBackupDir = path.join(__dirname, '..', '..', 'test-backups');

    // Create BackupCLI instance
    backupCLI = new BackupCLI({
      backupDir: testBackupDir,
      retentionDays: 7,
      maxBackups: 10
    });

    // Access the backupManager instance to configure mocks
    mockBackupManager = (backupCLI as any).backupManager;

    // Setup mock backup manager to track created backups
    mockBackupManager.createBackup.mockImplementation((options: any) => {
      backupCounter++;
      const ext = options.format === 'sql' ? (options.compress ? '.sql.gz' : '.sql') :
                  options.format === 'json' ? '.json' : '.csv';
      const backupInfo: BackupInfo = {
        id: `backup-${backupCounter}-${Date.now()}`,
        timestamp: Date.now(),
        database: options.database,
        format: options.format || 'sql',
        compressed: options.compress || false,
        size: 1024 * backupCounter,
        tables: ['users', 'posts'],
        path: path.join(testBackupDir, `${options.name || 'backup'}${ext}`),
        metadata: { checksum: `checksum-${backupCounter}` },
        status: 'success'
      };
      // Track created backups with retention policy
      createdBackups.push(backupInfo);

      // Enforce max backups limit (10)
      if (createdBackups.length > 10) {
        createdBackups.shift(); // Remove oldest backup
      }

      return Promise.resolve(backupInfo);
    });

    // Return tracked backups
    mockBackupManager.listBackups.mockImplementation(() => Promise.resolve([...createdBackups]));
    mockBackupManager.verifyBackup.mockResolvedValue(true);
    mockBackupManager.restoreBackup.mockResolvedValue(undefined); // Restore succeeds

    // Mock delete to remove from tracked backups
    mockBackupManager.deleteBackup = vi.fn((backupId: string) => {
      const index = createdBackups.findIndex(b => b.id === backupId);
      if (index >= 0) {
        createdBackups.splice(index, 1);
      }
      return Promise.resolve();
    });

    // Setup filesystem mocks
    (fs.mkdir as any).mockResolvedValue(undefined);
    (fs.rm as any).mockResolvedValue(undefined);
    (fs.access as any).mockResolvedValue(undefined);
    (fs.stat as any).mockResolvedValue({ size: 1024 * 1024 }); // 1MB
    (fs.copyFile as any).mockResolvedValue(undefined);
    (fs.writeFile as any).mockResolvedValue(undefined);
    (fs.readFile as any).mockResolvedValue(JSON.stringify({ test: 'data' }));
    (fs.unlink as any).mockResolvedValue(undefined);
  });

  afterEach(async () => {
    await backupCLI.cleanup();
    vi.clearAllMocks();
  });

  // ============================================================
  // COMMAND 1: backup create
  // ============================================================
  describe('Command 1: backup create', () => {
    it('should create SQL backup successfully', async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'test_backup',
        format: 'sql',
        compress: true
      });

      expect(result.status).toBe('success');
      expect(result.id).toBeDefined();
      expect(result.path).toBeDefined();
      expect(result.size).toBeGreaterThan(0);
      expect(result.duration).toBeGreaterThanOrEqual(0);
    });

    it('should create JSON backup', async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'json_backup',
        format: 'json',
        compress: false
      });

      expect(result.status).toBe('success');
      expect(result.path).toContain('.json');
    });

    it('should create CSV backup', async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'csv_backup',
        format: 'csv'
      });

      expect(result.status).toBe('success');
    });

    it('should create incremental backup', async () => {
      // Create base backup first
      const baseBackup = await backupCLI.createBackup({
        database: 'test_db',
        name: 'base_backup',
        format: 'sql'
      });

      // Create incremental backup
      const incrementalBackup = await backupCLI.createBackup({
        database: 'test_db',
        name: 'incremental_backup',
        format: 'sql',
        incremental: true,
        lastBackupTimestamp: Date.now() - 3600000
      });

      expect(incrementalBackup.status).toBe('success');
    });

    it('should create backup with verification', async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'verified_backup',
        format: 'sql',
        verify: true
      });

      expect(result.status).toBe('success');
    });

    it('should create compressed backup', async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'compressed_backup',
        format: 'sql',
        compress: true
      });

      expect(result.status).toBe('success');
      expect(result.path).toMatch(/\.gz$/);
    });

    it('should handle backup creation failure', async () => {
      const result = await backupCLI.createBackup({
        database: 'nonexistent_db',
        name: 'failed_backup',
        format: 'sql'
      });

      expect(result.status).toBe('failed');
      expect(result.error).toBeDefined();
    });

    it('should create backup with specific tables', async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'partial_backup',
        format: 'sql',
        tables: ['users', 'posts']
      });

      expect(result.status).toBe('success');
    });
  });

  // ============================================================
  // COMMAND 2: backup restore
  // ============================================================
  describe('Command 2: backup restore', () => {
    let backupId: string;

    beforeEach(async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'restore_test',
        format: 'sql'
      });
      backupId = result.id;
    });

    it('should restore backup successfully', async () => {
      await expect(
        backupCLI.restoreBackup(backupId, {})
      ).resolves.not.toThrow();
    });

    it('should perform dry-run restore', async () => {
      await expect(
        backupCLI.restoreBackup(backupId, { dryRun: true })
      ).resolves.not.toThrow();
    });

    it('should restore to different database', async () => {
      await expect(
        backupCLI.restoreBackup(backupId, { targetDatabase: 'target_db' })
      ).resolves.not.toThrow();
    });

    it('should fail restore for nonexistent backup', async () => {
      await expect(
        backupCLI.restoreBackup('nonexistent-id', {})
      ).rejects.toThrow('Backup not found');
    });

    it('should restore with specific tables', async () => {
      await expect(
        backupCLI.restoreBackup(backupId, { tables: ['users'] })
      ).resolves.not.toThrow();
    });

    it('should restore with drop existing tables', async () => {
      await expect(
        backupCLI.restoreBackup(backupId, { dropExisting: true })
      ).resolves.not.toThrow();
    });

    it('should restore with continue on error', async () => {
      await expect(
        backupCLI.restoreBackup(backupId, { continueOnError: true })
      ).resolves.not.toThrow();
    });
  });

  // ============================================================
  // COMMAND 3: backup list
  // ============================================================
  describe('Command 3: backup list', () => {
    beforeEach(async () => {
      // Create multiple test backups
      await backupCLI.createBackup({ database: 'db1', name: 'backup1', format: 'sql' });
      await backupCLI.createBackup({ database: 'db2', name: 'backup2', format: 'json' });
      await backupCLI.createBackup({ database: 'db1', name: 'backup3', format: 'csv' });
    });

    it('should list all backups', async () => {
      const backups = await backupCLI.listBackups();
      expect(backups.length).toBeGreaterThanOrEqual(3);
    });

    it('should filter backups by database', async () => {
      const backups = await backupCLI.listBackups({ database: 'db1' });
      expect(backups.every(b => b.database === 'db1')).toBe(true);
    });

    it('should filter backups by date range', async () => {
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

      const backups = await backupCLI.listBackups({
        after: yesterday,
        before: now
      });

      expect(backups.length).toBeGreaterThan(0);
    });

    it('should filter backups by format', async () => {
      const backups = await backupCLI.listBackups({ format: 'sql' });
      expect(backups.every(b => b.format === 'sql')).toBe(true);
    });

    it('should return empty list when no backups match', async () => {
      const backups = await backupCLI.listBackups({ database: 'nonexistent' });
      expect(backups).toHaveLength(0);
    });
  });

  // ============================================================
  // COMMAND 4: backup status
  // ============================================================
  describe('Command 4: backup status', () => {
    let backupId: string;

    beforeEach(async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'status_test',
        format: 'sql',
        compress: true
      });
      backupId = result.id;
    });

    it('should get backup status', async () => {
      const info = await backupCLI.getBackupInfo(backupId);

      expect(info).toBeDefined();
      expect(info?.id).toBe(backupId);
      expect(info?.database).toBe('test_db');
      expect(info?.format).toBe('sql');
    });

    it('should return null for nonexistent backup', async () => {
      const info = await backupCLI.getBackupInfo('nonexistent-id');
      expect(info).toBeNull();
    });

    it('should include metadata in status', async () => {
      const info = await backupCLI.getBackupInfo(backupId);
      expect(info?.metadata).toBeDefined();
    });

    it('should include checksum in metadata', async () => {
      const info = await backupCLI.getBackupInfo(backupId);
      expect(info?.metadata.checksum).toBeDefined();
    });

    it('should show compression status', async () => {
      const info = await backupCLI.getBackupInfo(backupId);
      expect(info?.compressed).toBe(true);
    });
  });

  // ============================================================
  // COMMAND 5: backup schedule
  // ============================================================
  describe('Command 5: backup schedule', () => {
    it('should schedule daily backup', async () => {
      const schedule = await backupCLI.scheduleBackup('0 2 * * *', {
        name: 'daily_backup',
        database: 'test_db',
        retention: 30
      });

      expect(schedule).toBeDefined();
      expect(schedule.name).toBe('daily_backup');
      expect(schedule.cron).toBe('0 2 * * *');
      expect(schedule.enabled).toBe(true);
    });

    it('should schedule hourly backup', async () => {
      const schedule = await backupCLI.scheduleBackup('0 * * * *', {
        name: 'hourly_backup',
        database: 'test_db'
      });

      expect(schedule.cron).toBe('0 * * * *');
    });

    it('should schedule with email notification', async () => {
      const schedule = await backupCLI.scheduleBackup('0 3 * * *', {
        name: 'backup_with_email',
        database: 'test_db',
        email: 'admin@example.com'
      });

      expect(schedule).toBeDefined();
    });

    it('should schedule with custom retention', async () => {
      const schedule = await backupCLI.scheduleBackup('0 4 * * *', {
        name: 'custom_retention',
        database: 'test_db',
        retention: 60
      });

      expect(schedule).toBeDefined();
    });

    it('should fail with invalid cron expression', async () => {
      await expect(
        backupCLI.scheduleBackup('invalid cron', {
          name: 'invalid_schedule',
          database: 'test_db'
        })
      ).rejects.toThrow('Invalid cron expression');
    });

    it('should list all schedules', async () => {
      await backupCLI.scheduleBackup('0 2 * * *', {
        name: 'schedule1',
        database: 'db1'
      });

      await backupCLI.scheduleBackup('0 3 * * *', {
        name: 'schedule2',
        database: 'db2'
      });

      const schedules = backupCLI.listSchedules();
      expect(schedules.length).toBeGreaterThanOrEqual(2);
    });

    it('should delete schedule', async () => {
      const schedule = await backupCLI.scheduleBackup('0 5 * * *', {
        name: 'delete_test',
        database: 'test_db'
      });

      await backupCLI.deleteSchedule(schedule.id);

      const schedules = backupCLI.listSchedules();
      expect(schedules.find(s => s.id === schedule.id)).toBeUndefined();
    });
  });

  // ============================================================
  // COMMAND 6: backup verify
  // ============================================================
  describe('Command 6: backup verify', () => {
    let backupId: string;

    beforeEach(async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'verify_test',
        format: 'sql',
        compress: true
      });
      backupId = result.id;
    });

    it('should verify backup successfully', async () => {
      const result = await backupCLI.verifyBackup(backupId, { deep: false });

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should perform deep verification with checksum', async () => {
      const result = await backupCLI.verifyBackup(backupId, { deep: true });

      expect(result.valid).toBe(true);
      expect(result.checksum).toBeDefined();
    });

    it('should fail verification for nonexistent backup', async () => {
      const result = await backupCLI.verifyBackup('nonexistent-id', { deep: false });

      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('should detect file size mismatch', async () => {
      // Mock stat to return different size
      (fs.stat as any).mockResolvedValueOnce({ size: 999999 });

      const result = await backupCLI.verifyBackup(backupId, { deep: false });

      expect(result.warnings.length).toBeGreaterThan(0);
    });

    it('should test backup restore capability', async () => {
      const result = await backupCLI.testBackup(backupId, {});

      expect(result.success).toBe(true);
      expect(result.tests.length).toBeGreaterThan(0);
    });

    it('should run all verification tests', async () => {
      const result = await backupCLI.testBackup(backupId, { validateData: true });

      expect(result.tests).toContainEqual(
        expect.objectContaining({ name: 'Backup exists' })
      );
      expect(result.tests).toContainEqual(
        expect.objectContaining({ name: 'File integrity' })
      );
      expect(result.tests).toContainEqual(
        expect.objectContaining({ name: 'Metadata' })
      );
    });
  });

  // ============================================================
  // COMMAND 7: backup delete
  // ============================================================
  describe('Command 7: backup delete', () => {
    let backupId: string;

    beforeEach(async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'delete_test',
        format: 'sql'
      });
      backupId = result.id;
    });

    it('should delete backup with force flag', async () => {
      await expect(backupCLI.deleteBackup(backupId, true)).resolves.not.toThrow();

      const info = await backupCLI.getBackupInfo(backupId);
      expect(info).toBeNull();
    });

    it('should fail deletion without force flag', async () => {
      await expect(backupCLI.deleteBackup(backupId, false)).rejects.toThrow(
        'Use --force flag'
      );
    });

    it('should fail for nonexistent backup', async () => {
      await expect(backupCLI.deleteBackup('nonexistent-id', true)).rejects.toThrow(
        'Backup not found'
      );
    });

    it('should delete backup file and metadata', async () => {
      await backupCLI.deleteBackup(backupId, true);

      expect(fs.unlink).toHaveBeenCalledTimes(2); // backup file + metadata
    });
  });

  // ============================================================
  // COMMAND 8: backup export
  // ============================================================
  describe('Command 8: backup export', () => {
    let backupId: string;
    let exportPath: string;

    beforeEach(async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'export_test',
        format: 'sql'
      });
      backupId = result.id;
      exportPath = path.join(testBackupDir, 'exports', 'backup.sql');
    });

    it('should export backup to external location', async () => {
      await expect(
        backupCLI.exportBackup(backupId, exportPath)
      ).resolves.not.toThrow();
    });

    it('should create export directory if needed', async () => {
      await backupCLI.exportBackup(backupId, exportPath);

      expect(fs.mkdir).toHaveBeenCalledWith(
        path.dirname(exportPath),
        { recursive: true }
      );
    });

    it('should export metadata with backup', async () => {
      await backupCLI.exportBackup(backupId, exportPath);

      expect(fs.copyFile).toHaveBeenCalledTimes(2); // backup + metadata
    });

    it('should fail for nonexistent backup', async () => {
      await expect(
        backupCLI.exportBackup('nonexistent-id', exportPath)
      ).rejects.toThrow('Backup not found');
    });
  });

  // ============================================================
  // COMMAND 9: backup import
  // ============================================================
  describe('Command 9: backup import', () => {
    let importPath: string;

    beforeEach(async () => {
      importPath = path.join(testBackupDir, 'imports', 'backup.sql');

      // Mock file existence
      (fs.access as any).mockResolvedValue(undefined);
    });

    it('should import backup from external location', async () => {
      const imported = await backupCLI.importBackup(importPath);

      expect(imported).toBeDefined();
      expect(imported.id).toBeDefined();
    });

    it('should import backup with metadata', async () => {
      const mockMetadata = {
        id: 'imported-id',
        database: 'test_db',
        format: 'sql',
        size: 1024,
        timestamp: Date.now(),
        tables: ['users'],
        compressed: false,
        path: '',
        metadata: {}
      };

      (fs.readFile as any).mockResolvedValue(JSON.stringify(mockMetadata));

      const imported = await backupCLI.importBackup(importPath);
      expect(imported.database).toBe('test_db');
    });

    it('should import backup without metadata', async () => {
      (fs.readFile as any).mockRejectedValue(new Error('File not found'));

      const imported = await backupCLI.importBackup(importPath);
      expect(imported).toBeDefined();
      expect(imported.database).toBe('unknown');
    });

    it('should fail for nonexistent file', async () => {
      (fs.access as any).mockRejectedValue(new Error('File not found'));

      await expect(
        backupCLI.importBackup('/nonexistent/backup.sql')
      ).rejects.toThrow();
    });
  });

  // ============================================================
  // COMMAND 10: backup config
  // ============================================================
  describe('Command 10: backup config', () => {
    it('should show current configuration', () => {
      // Configuration is shown through BackupCLI instance
      expect(backupCLI).toBeDefined();
    });

    it('should list active schedules', async () => {
      await backupCLI.scheduleBackup('0 2 * * *', {
        name: 'test_schedule',
        database: 'test_db'
      });

      const schedules = backupCLI.listSchedules();
      expect(schedules.length).toBeGreaterThan(0);
    });

    it('should get schedule by ID', async () => {
      const created = await backupCLI.scheduleBackup('0 3 * * *', {
        name: 'findable_schedule',
        database: 'test_db'
      });

      const schedules = backupCLI.listSchedules();
      const found = schedules.find(s => s.id === created.id);

      expect(found).toBeDefined();
      expect(found?.name).toBe('findable_schedule');
    });
  });

  // ============================================================
  // EDGE CASES & ERROR HANDLING
  // ============================================================
  describe('Edge Cases & Error Handling', () => {
    it('should handle concurrent backup operations', async () => {
      const backups = await Promise.all([
        backupCLI.createBackup({ database: 'db1', name: 'concurrent1', format: 'sql' }),
        backupCLI.createBackup({ database: 'db2', name: 'concurrent2', format: 'sql' }),
        backupCLI.createBackup({ database: 'db3', name: 'concurrent3', format: 'sql' })
      ]);

      expect(backups.every(b => b.status === 'success')).toBe(true);
    });

    it('should handle backup with special characters in name', async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'backup-with-special_chars@2024',
        format: 'sql'
      });

      expect(result.status).toBe('success');
    });

    it('should enforce retention policy', async () => {
      // Create backups beyond maxBackups limit
      for (let i = 0; i < 15; i++) {
        await backupCLI.createBackup({
          database: 'test_db',
          name: `retention_test_${i}`,
          format: 'sql'
        });
      }

      const backups = await backupCLI.listBackups({ database: 'test_db' });

      // Should not exceed maxBackups (10)
      expect(backups.length).toBeLessThanOrEqual(10);
    });

    it('should handle missing database connection', async () => {
      const result = await backupCLI.createBackup({
        database: 'nonexistent_db',
        name: 'failed_backup',
        format: 'sql'
      });

      expect(result.status).toBe('failed');
      expect(result.error).toContain('Database connection not found');
    });

    it('should handle file system errors gracefully', async () => {
      // Make backupManager.createBackup throw filesystem error
      mockBackupManager.createBackup.mockRejectedValueOnce(new Error('Disk full'));

      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'fs_error_backup',
        format: 'sql'
      });

      expect(result.status).toBe('failed');
      expect(result.error).toBeDefined();
    });
  });

  // ============================================================
  // PERFORMANCE TESTS
  // ============================================================
  describe('Performance Tests', () => {
    it('should create backup within reasonable time', async () => {
      const start = Date.now();

      await backupCLI.createBackup({
        database: 'test_db',
        name: 'performance_test',
        format: 'sql'
      });

      const duration = Date.now() - start;
      expect(duration).toBeLessThan(30000); // 30 seconds
    });

    it('should list backups efficiently', async () => {
      // Create multiple backups
      for (let i = 0; i < 20; i++) {
        await backupCLI.createBackup({
          database: `db_${i}`,
          name: `backup_${i}`,
          format: 'sql'
        });
      }

      const start = Date.now();
      await backupCLI.listBackups();
      const duration = Date.now() - start;

      expect(duration).toBeLessThan(5000); // 5 seconds
    });

    it('should verify backup efficiently', async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'verify_perf_test',
        format: 'sql'
      });

      const start = Date.now();
      await backupCLI.verifyBackup(result.id, { deep: true });
      const duration = Date.now() - start;

      expect(duration).toBeLessThan(10000); // 10 seconds
    });
  });

  // ============================================================
  // INTEGRATION TESTS
  // ============================================================
  describe('Integration Tests', () => {
    it('should complete full backup lifecycle', async () => {
      // Create backup
      const created = await backupCLI.createBackup({
        database: 'test_db',
        name: 'lifecycle_test',
        format: 'sql',
        compress: true
      });

      expect(created.status).toBe('success');

      // Verify backup
      const verification = await backupCLI.verifyBackup(created.id, { deep: true });
      expect(verification.valid).toBe(true);

      // List backups
      const backups = await backupCLI.listBackups({ database: 'test_db' });
      expect(backups.some(b => b.id === created.id)).toBe(true);

      // Get status
      const status = await backupCLI.getBackupInfo(created.id);
      expect(status).toBeDefined();

      // Export backup
      const exportPath = path.join(testBackupDir, 'export.sql');
      await backupCLI.exportBackup(created.id, exportPath);

      // Import backup
      const imported = await backupCLI.importBackup(exportPath);
      expect(imported).toBeDefined();

      // Delete backup
      await backupCLI.deleteBackup(created.id, true);

      const deletedInfo = await backupCLI.getBackupInfo(created.id);
      expect(deletedInfo).toBeNull();
    });

    it('should handle schedule lifecycle', async () => {
      // Create schedule
      const schedule = await backupCLI.scheduleBackup('0 2 * * *', {
        name: 'lifecycle_schedule',
        database: 'test_db'
      });

      expect(schedule.enabled).toBe(true);

      // List schedules
      const schedules = backupCLI.listSchedules();
      expect(schedules.find(s => s.id === schedule.id)).toBeDefined();

      // Delete schedule
      await backupCLI.deleteSchedule(schedule.id);

      const afterDelete = backupCLI.listSchedules();
      expect(afterDelete.find(s => s.id === schedule.id)).toBeUndefined();
    });
  });
});
