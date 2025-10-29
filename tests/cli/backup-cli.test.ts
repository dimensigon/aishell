/**
 * Backup CLI Tests
 * Comprehensive test suite for backup and recovery operations
 */

import { BackupCLI, BackupFilter, BackupResult, VerificationResult } from '../../src/cli/backup-cli';
import { BackupInfo } from '../../src/cli/backup-manager';
import * as fs from 'fs/promises';
import * as path from 'path';
import { vi, Mock } from 'vitest';

// Mock database manager at module level
vi.mock('../../src/cli/database-manager', () => {
  return {
    DatabaseConnectionManager: class {
      constructor() {}
      getConnection(name: string) {
        return { database: name, connected: true };
      }
    }
  };
});

// Mock backup manager
vi.mock('../../src/cli/backup-manager', () => {
  return {
    BackupManager: class {
      createBackup = vi.fn();
      restoreBackup = vi.fn();
      listBackups = vi.fn(() => Promise.resolve([]));
      verifyBackup = vi.fn(() => Promise.resolve(true));
      shutdown = vi.fn();
      constructor() {}
    }
  };
});

// Mock backup system
vi.mock('../../src/cli/backup-system', () => {
  return {
    BackupSystem: class {
      constructor() {}
    }
  };
});

// Mock state manager
vi.mock('../../src/core/state-manager', () => {
  return {
    StateManager: class {
      private state = new Map();
      get(key: string) { return this.state.get(key); }
      set(key: string, value: any) { this.state.set(key, value); }
    }
  };
});

// Mock node-cron
vi.mock('node-cron', () => ({
  default: {
    schedule: vi.fn(() => ({ stop: vi.fn() })),
    validate: vi.fn(() => true)
  }
}));
import { vi } from 'vitest';

// Mock modules
vi.mock('../../src/cli/backup-manager', () => {
  const mockBackupManager = {
    createBackup: vi.fn(),
    restoreBackup: vi.fn(),
    listBackups: vi.fn(),
    verifyBackup: vi.fn(),
    shutdown: vi.fn()
  };
  return {
    BackupManager: vi.fn(() => mockBackupManager)
  };
});

vi.mock('../../src/cli/backup-system', () => {
  return {
    BackupSystem: vi.fn(() => ({}))
  };
});

vi.mock('../../src/cli/database-manager', () => {
  return {
    DatabaseConnectionManager: vi.fn(() => ({
      getConnection: vi.fn((dbName: string) => ({ database: dbName, connected: true }))
    }))
  };
});

vi.mock('../../src/core/state-manager', () => {
  return {
    StateManager: vi.fn(() => ({
      get: vi.fn(),
      set: vi.fn()
    }))
  };
});

// Mock fs operations
vi.mock('fs/promises', async () => {
  const actual = await vi.importActual('fs/promises') as any;
  return {
    ...actual,
    access: vi.fn(),
    stat: vi.fn(),
    mkdir: vi.fn(),
    rm: vi.fn(),
    readdir: vi.fn(),
    readFile: vi.fn(),
    writeFile: vi.fn(),
    unlink: vi.fn(),
    copyFile: vi.fn()
  };
});

describe('BackupCLI', () => {
  let backupCLI: BackupCLI;
  let testBackupDir: string;
  let mockBackupManager: any;

  beforeEach(() => {
    vi.clearAllMocks();

    testBackupDir = path.join(__dirname, '..', '..', 'test-backups');
    backupCLI = new BackupCLI({
      backupDir: testBackupDir,
      retentionDays: 7,
      maxBackups: 10
    });

    // Get the mock instance
    const { BackupManager } = require('../../src/cli/backup-manager');
    mockBackupManager = BackupManager.mock.results[BackupManager.mock.results.length - 1].value;

    // Setup default mock responses
    (fs.mkdir as any).mockResolvedValue(undefined);
    (fs.rm as any).mockResolvedValue(undefined);
    (fs.access as any).mockResolvedValue(undefined);
    (fs.stat as any).mockResolvedValue({ size: 1024 });
  });

  afterEach(async () => {
    await backupCLI.cleanup();
    vi.clearAllMocks();
  });

  describe('createBackup', () => {
    it('should create a backup successfully', async () => {
      const mockBackupInfo: BackupInfo = {
        id: 'test-backup-id',
        timestamp: Date.now(),
        database: 'test_db',
        format: 'sql',
        compressed: true,
        size: 1024,
        tables: ['users', 'posts'],
        path: '/path/to/backup.sql.gz',
        metadata: { checksum: 'abc123' }
      };

      mockBackupManager.createBackup.mockResolvedValue(mockBackupInfo);

      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'test_backup',
        compress: true,
        format: 'sql'
      });

      expect(result.status).toBe('success');
      expect(result.id).toBeDefined();
      expect(result.path).toBeDefined();
      expect(result.duration).toBeGreaterThan(0);
    });

    it('should create backup with verification', async () => {
      const mockBackupInfo: BackupInfo = {
        id: 'verified-backup-id',
        timestamp: Date.now(),
        database: 'test_db',
        format: 'sql',
        compressed: true,
        size: 2048,
        tables: ['users'],
        path: '/path/to/verified.sql.gz',
        metadata: { checksum: 'def456' }
      };

      mockBackupManager.createBackup.mockResolvedValue(mockBackupInfo);
      mockBackupManager.verifyBackup.mockResolvedValue(true);

      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'verified_backup',
        compress: true,
        verify: true,
        format: 'sql'
      });

      expect(result.status).toBe('success');
    });

    it('should create incremental backup', async () => {
      const baseBackupInfo: BackupInfo = {
        id: 'base-backup-id',
        timestamp: Date.now(),
        database: 'test_db',
        format: 'sql',
        compressed: false,
        size: 1024,
        tables: ['users'],
        path: '/path/to/base.sql',
        metadata: {}
      };

      const incrementalBackupInfo: BackupInfo = {
        id: 'incremental-backup-id',
        timestamp: Date.now(),
        database: 'test_db',
        format: 'sql',
        compressed: false,
        size: 512,
        tables: ['users'],
        path: '/path/to/incremental.sql',
        metadata: { incremental: true, baseBackupId: 'base-backup-id' }
      };

      mockBackupManager.createBackup
        .mockResolvedValueOnce(baseBackupInfo)
        .mockResolvedValueOnce(incrementalBackupInfo);

      // Create base backup
      const baseBackup = await backupCLI.createBackup({
        database: 'test_db',
        name: 'base_backup',
        format: 'sql'
      });

      expect(baseBackup.status).toBe('success');

      // Create incremental backup
      const incrementalBackup = await backupCLI.createBackup({
        database: 'test_db',
        name: 'incremental_backup',
        incremental: true,
        lastBackupTimestamp: Date.now() - 3600000, // 1 hour ago
        format: 'sql'
      });

      expect(incrementalBackup.status).toBe('success');
    });

    it('should create backup with different formats', async () => {
      const formats = ['sql', 'json', 'csv'];

      for (const format of formats) {
        const mockBackupInfo: BackupInfo = {
          id: `backup-${format}-id`,
          timestamp: Date.now(),
          database: 'test_db',
          format,
          compressed: false,
          size: 1024,
          tables: ['users'],
          path: `/path/to/backup.${format}`,
          metadata: {}
        };

        mockBackupManager.createBackup.mockResolvedValue(mockBackupInfo);

        const result = await backupCLI.createBackup({
          database: 'test_db',
          name: `backup_${format}`,
          format: format as 'sql' | 'json' | 'csv'
        });

        expect(result.status).toBe('success');
      }
    });

    it('should handle backup creation failure', async () => {
      // Mock database connection not found by returning null
      const { DatabaseConnectionManager } = require('../../src/cli/database-manager');
      const mockDbManager = DatabaseConnectionManager.mock.results[DatabaseConnectionManager.mock.results.length - 1].value;
      mockDbManager.getConnection.mockReturnValueOnce(null);

      const result = await backupCLI.createBackup({
        database: 'nonexistent_db',
        name: 'failed_backup',
        format: 'sql'
      });

      expect(result.status).toBe('failed');
      expect(result.error).toBeDefined();
    });

    it('should create compressed backup', async () => {
      const mockBackupInfo: BackupInfo = {
        id: 'compressed-backup-id',
        timestamp: Date.now(),
        database: 'test_db',
        format: 'sql',
        compressed: true,
        size: 512,
        tables: ['users'],
        path: '/path/to/backup.sql.gz',
        metadata: {}
      };

      mockBackupManager.createBackup.mockResolvedValue(mockBackupInfo);

      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'compressed_backup',
        compress: true,
        format: 'sql'
      });

      expect(result.status).toBe('success');
      expect(result.path).toContain('.gz');
    });
  });

  describe('restoreBackup', () => {
    let backupId: string;
    let mockBackupInfo: BackupInfo;

    beforeEach(async () => {
      mockBackupInfo = {
        id: 'restore-test-id',
        timestamp: Date.now(),
        database: 'test_db',
        format: 'sql',
        compressed: false,
        size: 1024,
        tables: ['users', 'posts'],
        path: '/path/to/restore.sql',
        metadata: { checksum: 'xyz789' }
      };

      mockBackupManager.createBackup.mockResolvedValue(mockBackupInfo);
      mockBackupManager.listBackups.mockResolvedValue([mockBackupInfo]);
      mockBackupManager.restoreBackup.mockResolvedValue(undefined);

      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'restore_test',
        format: 'sql'
      });
      backupId = result.id;
    });

    it('should restore backup successfully', async () => {
      await expect(backupCLI.restoreBackup(backupId, {})).resolves.not.toThrow();
      expect(mockBackupManager.restoreBackup).toHaveBeenCalled();
    });

    it('should perform dry-run restore', async () => {
      mockBackupManager.verifyBackup.mockResolvedValue(true);

      await expect(
        backupCLI.restoreBackup(backupId, { dryRun: true })
      ).resolves.not.toThrow();

      expect(mockBackupManager.restoreBackup).not.toHaveBeenCalled();
    });

    it('should restore to different database', async () => {
      await expect(
        backupCLI.restoreBackup(backupId, { targetDatabase: 'target_db' })
      ).resolves.not.toThrow();

      expect(mockBackupManager.restoreBackup).toHaveBeenCalledWith(
        mockBackupInfo.path,
        expect.objectContaining({ targetDatabase: 'target_db' })
      );
    });

    it('should fail restore for nonexistent backup', async () => {
      mockBackupManager.listBackups.mockResolvedValue([]);

      await expect(
        backupCLI.restoreBackup('nonexistent-id', {})
      ).rejects.toThrow('Backup not found');
    });

    it('should restore with point-in-time', async () => {
      await expect(
        backupCLI.restoreBackup(backupId, {
          targetDatabase: 'test_db_restored'
        })
      ).resolves.not.toThrow();
    });
  });

  describe('listBackups', () => {
    beforeEach(async () => {
      const mockBackups: BackupInfo[] = [
        {
          id: 'backup1-id',
          timestamp: Date.now(),
          database: 'db1',
          format: 'sql',
          compressed: false,
          size: 1024,
          tables: ['users'],
          path: '/path/to/backup1.sql',
          metadata: {}
        },
        {
          id: 'backup2-id',
          timestamp: Date.now(),
          database: 'db2',
          format: 'sql',
          compressed: false,
          size: 2048,
          tables: ['posts'],
          path: '/path/to/backup2.sql',
          metadata: {}
        },
        {
          id: 'backup3-id',
          timestamp: Date.now(),
          database: 'db1',
          format: 'json',
          compressed: false,
          size: 512,
          tables: ['comments'],
          path: '/path/to/backup3.json',
          metadata: {}
        }
      ];

      mockBackupManager.listBackups.mockResolvedValue(mockBackups);
    });

    it('should list all backups', async () => {
      const backups = await backupCLI.listBackups();
      expect(backups.length).toBeGreaterThanOrEqual(3);
    });

    it('should filter backups by database', async () => {
      const filter: BackupFilter = { database: 'db1' };
      const backups = await backupCLI.listBackups(filter);

      expect(backups.every(b => b.database === 'db1')).toBe(true);
    });

    it('should filter backups by date range', async () => {
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

      const filter: BackupFilter = {
        after: yesterday,
        before: now
      };

      const backups = await backupCLI.listBackups(filter);
      expect(backups.length).toBeGreaterThan(0);
    });

    it('should filter backups by format', async () => {
      const filter: BackupFilter = { format: 'sql' };
      const backups = await backupCLI.listBackups(filter);

      expect(backups.every(b => b.format === 'sql')).toBe(true);
    });

    it('should return empty list when no backups match', async () => {
      const filter: BackupFilter = { database: 'nonexistent_db' };
      const backups = await backupCLI.listBackups(filter);

      expect(backups).toHaveLength(0);
    });
  });

  describe('getBackupInfo', () => {
    let backupId: string;

    beforeEach(async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'info_test',
        format: 'sql'
      });
      backupId = result.id;
    });

    it('should get backup info', async () => {
      const info = await backupCLI.getBackupInfo(backupId);

      expect(info).toBeDefined();
      expect(info?.id).toBe(backupId);
      expect(info?.database).toBe('test_db');
    });

    it('should return null for nonexistent backup', async () => {
      const info = await backupCLI.getBackupInfo('nonexistent-id');
      expect(info).toBeNull();
    });

    it('should include metadata', async () => {
      const info = await backupCLI.getBackupInfo(backupId);

      expect(info?.metadata).toBeDefined();
      expect(info?.metadata.checksum).toBeDefined();
    });
  });

  describe('deleteBackup', () => {
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

    it('should fail without force flag', async () => {
      await expect(backupCLI.deleteBackup(backupId, false)).rejects.toThrow();
    });

    it('should fail for nonexistent backup', async () => {
      await expect(backupCLI.deleteBackup('nonexistent-id', true)).rejects.toThrow();
    });
  });

  describe('exportBackup', () => {
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

    afterEach(async () => {
      try {
        await fs.rm(path.join(testBackupDir, 'exports'), { recursive: true, force: true });
      } catch (error) {
        // Ignore cleanup errors
      }
    });

    it('should export backup to external location', async () => {
      await expect(backupCLI.exportBackup(backupId, exportPath)).resolves.not.toThrow();

      // Verify exported file exists
      await expect(fs.access(exportPath)).resolves.not.toThrow();
    });

    it('should export metadata with backup', async () => {
      await backupCLI.exportBackup(backupId, exportPath);

      const metadataPath = `${exportPath}.metadata.json`;
      await expect(fs.access(metadataPath)).resolves.not.toThrow();
    });

    it('should fail for nonexistent backup', async () => {
      await expect(
        backupCLI.exportBackup('nonexistent-id', exportPath)
      ).rejects.toThrow();
    });
  });

  describe('importBackup', () => {
    let importPath: string;

    beforeEach(async () => {
      // Create a backup to export
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'import_test',
        format: 'sql'
      });

      importPath = path.join(testBackupDir, 'imports', 'backup.sql');
      await backupCLI.exportBackup(result.id, importPath);
    });

    it('should import backup from external location', async () => {
      const imported = await backupCLI.importBackup(importPath);

      expect(imported).toBeDefined();
      expect(imported.id).toBeDefined();
      expect(imported.database).toBe('test_db');
    });

    it('should import backup without metadata', async () => {
      // Remove metadata file
      const metadataPath = `${importPath}.metadata.json`;
      await fs.unlink(metadataPath);

      const imported = await backupCLI.importBackup(importPath);
      expect(imported).toBeDefined();
    });

    it('should fail for nonexistent file', async () => {
      await expect(
        backupCLI.importBackup('/nonexistent/backup.sql')
      ).rejects.toThrow();
    });
  });

  describe('verifyBackup', () => {
    let backupId: string;

    beforeEach(async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'verify_test',
        compress: true,
        format: 'sql'
      });
      backupId = result.id;
    });

    it('should verify backup successfully', async () => {
      const result = await backupCLI.verifyBackup(backupId, { deep: false });

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should perform deep verification', async () => {
      const result = await backupCLI.verifyBackup(backupId, { deep: true });

      expect(result.valid).toBe(true);
      expect(result.checksum).toBeDefined();
    });

    it('should fail for nonexistent backup', async () => {
      const result = await backupCLI.verifyBackup('nonexistent-id', { deep: false });

      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('should detect corrupted backup', async () => {
      const info = await backupCLI.getBackupInfo(backupId);

      // Corrupt the backup file
      if (info) {
        await fs.writeFile(info.path, 'corrupted data');
      }

      const result = await backupCLI.verifyBackup(backupId, { deep: true });
      expect(result.valid).toBe(false);
    });
  });

  describe('scheduleBackup', () => {
    it('should schedule backup with valid cron expression', async () => {
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

    it('should fail with invalid cron expression', async () => {
      await expect(
        backupCLI.scheduleBackup('invalid cron', {
          name: 'invalid_schedule',
          database: 'test_db'
        })
      ).rejects.toThrow();
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
  });

  describe('listSchedules', () => {
    beforeEach(async () => {
      await backupCLI.scheduleBackup('0 2 * * *', {
        name: 'schedule1',
        database: 'db1'
      });

      await backupCLI.scheduleBackup('0 3 * * *', {
        name: 'schedule2',
        database: 'db2'
      });
    });

    it('should list all schedules', async () => {
      const schedules = backupCLI.listSchedules();
      expect(schedules.length).toBeGreaterThanOrEqual(2);
    });

    it('should include schedule details', async () => {
      const schedules = backupCLI.listSchedules();
      const schedule = schedules[0];

      expect(schedule.id).toBeDefined();
      expect(schedule.name).toBeDefined();
      expect(schedule.cron).toBeDefined();
      expect(schedule.database).toBeDefined();
    });
  });

  describe('deleteSchedule', () => {
    let scheduleId: string;

    beforeEach(async () => {
      const schedule = await backupCLI.scheduleBackup('0 5 * * *', {
        name: 'delete_schedule_test',
        database: 'test_db'
      });
      scheduleId = schedule.id;
    });

    it('should delete schedule', async () => {
      await expect(backupCLI.deleteSchedule(scheduleId)).resolves.not.toThrow();

      const schedules = backupCLI.listSchedules();
      expect(schedules.find(s => s.id === scheduleId)).toBeUndefined();
    });

    it('should fail for nonexistent schedule', async () => {
      await expect(backupCLI.deleteSchedule('nonexistent-id')).rejects.toThrow();
    });
  });

  describe('testBackup', () => {
    let backupId: string;

    beforeEach(async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'test_backup',
        compress: true,
        format: 'sql'
      });
      backupId = result.id;
    });

    it('should test backup successfully', async () => {
      const result = await backupCLI.testBackup(backupId, {});

      expect(result.success).toBe(true);
      expect(result.tests.length).toBeGreaterThan(0);
    });

    it('should run all verification tests', async () => {
      const result = await backupCLI.testBackup(backupId, {
        validateData: true
      });

      expect(result.tests).toContainEqual(
        expect.objectContaining({ name: 'Backup exists', passed: true })
      );
      expect(result.tests).toContainEqual(
        expect.objectContaining({ name: 'File integrity', passed: true })
      );
      expect(result.tests).toContainEqual(
        expect.objectContaining({ name: 'Metadata', passed: true })
      );
    });

    it('should test compressed backup', async () => {
      const result = await backupCLI.testBackup(backupId, {});

      expect(result.tests).toContainEqual(
        expect.objectContaining({ name: 'Compression' })
      );
    });

    it('should fail tests for corrupted backup', async () => {
      const info = await backupCLI.getBackupInfo(backupId);

      // Corrupt the backup
      if (info) {
        await fs.writeFile(info.path, 'corrupted');
      }

      const result = await backupCLI.testBackup(backupId, {});
      expect(result.success).toBe(false);
    });
  });

  describe('Edge Cases', () => {
    it('should handle concurrent backup operations', async () => {
      const backups = await Promise.all([
        backupCLI.createBackup({ database: 'db1', name: 'concurrent1', format: 'sql' }),
        backupCLI.createBackup({ database: 'db2', name: 'concurrent2', format: 'sql' }),
        backupCLI.createBackup({ database: 'db3', name: 'concurrent3', format: 'sql' })
      ]);

      expect(backups.every(b => b.status === 'success')).toBe(true);
    });

    it('should handle large backup files', async () => {
      const result = await backupCLI.createBackup({
        database: 'large_db',
        name: 'large_backup',
        compress: true,
        format: 'sql'
      });

      expect(result.status).toBe('success');
    });

    it('should handle backup with special characters in name', async () => {
      const result = await backupCLI.createBackup({
        database: 'test_db',
        name: 'backup-with-special-chars_2024',
        format: 'sql'
      });

      expect(result.status).toBe('success');
    });

    it('should enforce retention policy', async () => {
      // Create multiple backups
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
  });

  describe('Performance', () => {
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
  });
});
