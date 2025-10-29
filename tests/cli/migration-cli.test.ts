/**
 * Migration CLI Tests
 * Comprehensive tests for all 8 migration commands
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { MigrationCLI } from '../../src/cli/migration-cli';
import { MigrationCommands } from '../../src/cli/migration-commands';
import { DatabaseConnectionManager, DatabaseType } from '../../src/cli/database-manager';
import { StateManager } from '../../src/core/state-manager';
import { BackupSystem } from '../../src/cli/backup-system';
import * as fs from 'fs/promises';
import * as path from 'path';
import { mkdtemp } from 'fs/promises';
import { tmpdir } from 'os';

describe('MigrationCLI', () => {
  let cli: MigrationCLI;
  let commands: MigrationCommands;
  let dbManager: DatabaseConnectionManager;
  let stateManager: StateManager;
  let backupSystem: BackupSystem;
  let tempDir: string;
  let migrationsDir: string;

  beforeEach(async () => {
    // Create temporary directory for tests
    tempDir = await mkdtemp(path.join(tmpdir(), 'migration-test-'));
    migrationsDir = path.join(tempDir, 'migrations');
    await fs.mkdir(migrationsDir, { recursive: true });

    // Setup managers
    stateManager = new StateManager({
      enablePersistence: false
    });

    dbManager = new DatabaseConnectionManager(stateManager);

    // Connect to in-memory SQLite database
    await dbManager.connect({
      name: 'test',
      type: DatabaseType.SQLITE,
      database: ':memory:'
    });

    backupSystem = new BackupSystem(dbManager, stateManager, {
      backupDir: path.join(tempDir, 'backups')
    });

    // Initialize CLI
    cli = new MigrationCLI(dbManager, stateManager, backupSystem, {
      migrationsDir
    });

    commands = new MigrationCommands(dbManager, stateManager, migrationsDir);
  });

  afterEach(async () => {
    // Cleanup
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  describe('Migration Commands - Create', () => {
    it('should create SQL migration file with timestamp', async () => {
      const filepath = await commands.create('create_users_table', { template: 'sql' });

      expect(filepath).toContain(migrationsDir);
      expect(filepath).toMatch(/_create_users_table\.sql$/);

      const content = await fs.readFile(filepath, 'utf-8');
      expect(content).toContain('-- @up');
      expect(content).toContain('-- @down');
    });

    it('should create JavaScript migration file', async () => {
      const filepath = await commands.create('add_email_column', { template: 'js' });

      expect(filepath).toContain(migrationsDir);
      expect(filepath).toMatch(/_add_email_column\.js$/);

      const content = await fs.readFile(filepath, 'utf-8');
      expect(content).toContain('export async function up');
      expect(content).toContain('export async function down');
    });

    it('should sanitize migration names', async () => {
      const filepath = await commands.create('Add User Roles', { template: 'sql' });
      expect(filepath).toMatch(/_add_user_roles\.sql$/);
    });

    it('should generate unique timestamps', async () => {
      const file1 = await commands.create('migration1');
      const file2 = await commands.create('migration2');

      const name1 = path.basename(file1).split('_')[0];
      const name2 = path.basename(file2).split('_')[0];

      expect(name1).not.toBe(name2);
    });
  });

  describe('Migration Commands - Up', () => {
    beforeEach(async () => {
      await commands.initialize();
    });

    it('should run pending migrations', async () => {
      // Create test migrations
      const file1 = await commands.create('create_users');
      const file2 = await commands.create('create_posts');

      // Add SQL to migrations
      await fs.writeFile(file1, `
-- @up
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
-- @down
DROP TABLE users;
      `);

      await fs.writeFile(file2, `
-- @up
CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT);
-- @down
DROP TABLE posts;
      `);

      const result = await commands.up();

      expect(result.executed).toHaveLength(2);
      expect(result.batch).toBe(1);

      // Verify tables created
      const tables = await dbManager.executeQuery(`
        SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'posts')
      `);
      expect(tables).toHaveLength(2);
    });

    it('should run limited number of migrations', async () => {
      await commands.create('migration1');
      await commands.create('migration2');
      await commands.create('migration3');

      const result = await commands.up(2);

      expect(result.executed).toHaveLength(2);
    });

    it('should skip already executed migrations', async () => {
      await commands.create('migration1');
      await commands.up();

      // Try to run again
      const result = await commands.up();
      expect(result.executed).toHaveLength(0);
    });

    it('should track migration batches correctly', async () => {
      await commands.create('migration1');
      await commands.up();

      await commands.create('migration2');
      const result = await commands.up();

      expect(result.batch).toBe(2);
    });

    it('should handle migration errors gracefully', async () => {
      const file = await commands.create('bad_migration');
      await fs.writeFile(file, `
-- @up
INVALID SQL STATEMENT;
-- @down
DROP TABLE test;
      `);

      await expect(commands.up()).rejects.toThrow();
    });
  });

  describe('Migration Commands - Down', () => {
    beforeEach(async () => {
      await commands.initialize();

      // Create and run migrations
      const file1 = await commands.create('create_users');
      await fs.writeFile(file1, `
-- @up
CREATE TABLE users (id INTEGER PRIMARY KEY);
-- @down
DROP TABLE users;
      `);

      await commands.up();
    });

    it('should rollback last batch', async () => {
      const result = await commands.down(1);

      expect(result.rolledBack).toHaveLength(1);

      // Verify table dropped
      const tables = await dbManager.executeQuery(`
        SELECT name FROM sqlite_master WHERE type='table' AND name='users'
      `);
      expect(tables).toHaveLength(0);
    });

    it('should rollback multiple batches', async () => {
      // Add more migrations
      const file2 = await commands.create('create_posts');
      await fs.writeFile(file2, `
-- @up
CREATE TABLE posts (id INTEGER PRIMARY KEY);
-- @down
DROP TABLE posts;
      `);
      await commands.up();

      const result = await commands.down(2);

      expect(result.rolledBack).toHaveLength(2);
    });

    it('should handle no migrations to rollback', async () => {
      await commands.down(1);

      const result = await commands.down(1);
      expect(result.rolledBack).toHaveLength(0);
    });
  });

  describe('Migration Commands - Status', () => {
    beforeEach(async () => {
      await commands.initialize();
    });

    it('should show executed and pending migrations', async () => {
      const file1 = await commands.create('migration1');
      const file2 = await commands.create('migration2');
      await fs.writeFile(file1, '-- @up\nCREATE TABLE test1 (id INT);\n-- @down\nDROP TABLE test1;');

      await commands.up(1);

      const status = await commands.status();

      expect(status.executed).toHaveLength(1);
      expect(status.pending).toHaveLength(1);
    });

    it('should show empty status for no migrations', async () => {
      const status = await commands.status();

      expect(status.executed).toHaveLength(0);
      expect(status.pending).toHaveLength(0);
    });

    it('should show all migrations as executed after up', async () => {
      await commands.create('migration1');
      await commands.create('migration2');
      await commands.up();

      const status = await commands.status();

      expect(status.executed).toHaveLength(2);
      expect(status.pending).toHaveLength(0);
    });

    it('should track batch numbers in status', async () => {
      const file = await commands.create('migration1');
      await fs.writeFile(file, '-- @up\nCREATE TABLE test (id INT);\n-- @down\nDROP TABLE test;');
      await commands.up();

      const status = await commands.status();

      expect(status.executed[0].batch).toBe(1);
    });
  });

  describe('Migration Commands - Rollback', () => {
    beforeEach(async () => {
      await commands.initialize();

      const file = await commands.create('create_test');
      await fs.writeFile(file, `
-- @up
CREATE TABLE test (id INTEGER PRIMARY KEY);
-- @down
DROP TABLE test;
      `);
      await commands.up();
    });

    it('should rollback last migration batch', async () => {
      const result = await commands.rollback();

      expect(result.rolledBack).toHaveLength(1);
    });

    it('should be equivalent to down(1)', async () => {
      const result1 = await commands.rollback();

      // Re-run migration
      await commands.up();
      const result2 = await commands.down(1);

      expect(result1.rolledBack.length).toBe(result2.rolledBack.length);
    });
  });

  describe('Migration Commands - Reset', () => {
    beforeEach(async () => {
      await commands.initialize();

      // Create multiple migrations
      const file1 = await commands.create('migration1');
      const file2 = await commands.create('migration2');

      await fs.writeFile(file1, '-- @up\nCREATE TABLE test1 (id INT);\n-- @down\nDROP TABLE test1;');
      await fs.writeFile(file2, '-- @up\nCREATE TABLE test2 (id INT);\n-- @down\nDROP TABLE test2;');

      await commands.up();
    });

    it('should rollback all migrations', async () => {
      const result = await commands.reset();

      expect(result.rolledBack).toHaveLength(2);
    });

    it('should leave database in clean state', async () => {
      await commands.reset();

      const status = await commands.status();
      expect(status.executed).toHaveLength(0);
    });

    it('should handle empty migration list', async () => {
      await commands.reset();

      const result = await commands.reset();
      expect(result.rolledBack).toHaveLength(0);
    });
  });

  describe('Migration Commands - Fresh', () => {
    beforeEach(async () => {
      await commands.initialize();

      // Create table directly
      await dbManager.executeQuery('CREATE TABLE existing_table (id INTEGER PRIMARY KEY)');
    });

    it('should drop all tables and re-run migrations', async () => {
      const file = await commands.create('create_users');
      await fs.writeFile(file, '-- @up\nCREATE TABLE users (id INT);\n-- @down\nDROP TABLE users;');

      const result = await commands.fresh();

      expect(result.tables).toContain('existing_table');
      expect(result.executed).toHaveLength(1);

      // Verify old table dropped
      const oldTables = await dbManager.executeQuery(`
        SELECT name FROM sqlite_master WHERE type='table' AND name='existing_table'
      `);
      expect(oldTables).toHaveLength(0);

      // Verify new table created
      const newTables = await dbManager.executeQuery(`
        SELECT name FROM sqlite_master WHERE type='table' AND name='users'
      `);
      expect(newTables).toHaveLength(1);
    });

    it('should handle errors when dropping tables', async () => {
      // This test verifies graceful handling
      await commands.create('migration1');

      const result = await commands.fresh();

      expect(result.executed).toHaveLength(1);
    });
  });

  describe('Migration Commands - Redo', () => {
    beforeEach(async () => {
      await commands.initialize();

      const file = await commands.create('create_test');
      await fs.writeFile(file, `
-- @up
CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT DEFAULT 'old');
-- @down
DROP TABLE test;
      `);
      await commands.up();
    });

    it('should rollback and re-run last migration', async () => {
      const result = await commands.redo();

      expect(result.migration).toBeDefined();

      // Verify table still exists
      const tables = await dbManager.executeQuery(`
        SELECT name FROM sqlite_master WHERE type='table' AND name='test'
      `);
      expect(tables).toHaveLength(1);
    });

    it('should handle no migrations to redo', async () => {
      await commands.reset();

      const result = await commands.redo();
      expect(result.migration).toBeNull();
    });

    it('should update batch number on redo', async () => {
      await commands.redo();

      const status = await commands.status();
      expect(status.executed[0].batch).toBe(2);
    });
  });

  describe('Migration File Parsing', () => {
    it('should parse migration filename correctly', async () => {
      const file = await commands.create('test_migration');
      const filename = path.basename(file);

      const parts = filename.split('_');
      expect(parts.length).toBeGreaterThanOrEqual(3);
      expect(parseInt(parts[0])).toBeGreaterThan(0);
    });

    it('should extract migration name from filename', async () => {
      const file = await commands.create('create_users_table');
      const filename = path.basename(file, '.sql');
      const name = filename.split('_').slice(1).join('_');

      expect(name).toBe('create_users_table');
    });
  });

  describe('Transaction Support', () => {
    beforeEach(async () => {
      await commands.initialize();
    });

    it('should execute migrations in transaction', async () => {
      const file = await commands.create('transaction_test');
      await fs.writeFile(file, `
-- @up
CREATE TABLE test1 (id INT);
CREATE TABLE test2 (id INT);
-- @down
DROP TABLE test2;
DROP TABLE test1;
      `);

      await commands.up();

      const tables = await dbManager.executeQuery(`
        SELECT name FROM sqlite_master WHERE type='table' AND name IN ('test1', 'test2')
      `);
      expect(tables).toHaveLength(2);
    });

    it('should rollback transaction on error', async () => {
      const file = await commands.create('error_test');
      await fs.writeFile(file, `
-- @up
CREATE TABLE test (id INT);
INVALID SQL;
-- @down
DROP TABLE test;
      `);

      await expect(commands.up()).rejects.toThrow();

      // Verify no tables created
      const tables = await dbManager.executeQuery(`
        SELECT name FROM sqlite_master WHERE type='table' AND name='test'
      `);
      expect(tables).toHaveLength(0);
    });
  });

  describe('Migration Tracking', () => {
    beforeEach(async () => {
      await commands.initialize();
    });

    it('should create migrations tracking table', async () => {
      const tables = await dbManager.executeQuery(`
        SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'
      `);

      expect(tables).toHaveLength(1);
    });

    it('should record migration execution', async () => {
      const file = await commands.create('test_migration');
      await fs.writeFile(file, '-- @up\nCREATE TABLE test (id INT);\n-- @down\nDROP TABLE test;');
      await commands.up();

      const records = await dbManager.executeQuery(`
        SELECT * FROM schema_migrations
      `);

      expect(records).toHaveLength(1);
      expect(records[0].batch).toBe(1);
    });

    it('should remove migration record on rollback', async () => {
      const file = await commands.create('test_migration');
      await fs.writeFile(file, '-- @up\nCREATE TABLE test (id INT);\n-- @down\nDROP TABLE test;');
      await commands.up();
      await commands.down(1);

      const records = await dbManager.executeQuery(`
        SELECT * FROM schema_migrations
      `);

      expect(records).toHaveLength(0);
    });
  });

  describe('Error Handling', () => {
    beforeEach(async () => {
      await commands.initialize();
    });

    it('should handle missing up function', async () => {
      const file = await commands.create('no_up');
      await fs.writeFile(file, '-- @down\nDROP TABLE test;');

      await expect(commands.up()).rejects.toThrow();
    });

    it('should handle missing down function', async () => {
      const file = await commands.create('no_down');
      await fs.writeFile(file, '-- @up\nCREATE TABLE test (id INT);');
      await commands.up();

      await expect(commands.down(1)).rejects.toThrow();
    });

    it('should handle database connection errors', async () => {
      await dbManager.disconnect();

      await expect(commands.up()).rejects.toThrow();
    });

    it('should handle file system errors', async () => {
      await fs.rmdir(migrationsDir, { recursive: true });

      await expect(commands.create('test')).rejects.toThrow();
    });
  });

  describe('JavaScript Migrations', () => {
    beforeEach(async () => {
      await commands.initialize();
    });

    it('should execute JavaScript migration up', async () => {
      const file = await commands.create('js_test', { template: 'js' });
      await fs.writeFile(file, `
export async function up(dbManager) {
  await dbManager.executeQuery('CREATE TABLE js_test (id INTEGER PRIMARY KEY)');
}

export async function down(dbManager) {
  await dbManager.executeQuery('DROP TABLE js_test');
}
      `);

      await commands.up();

      const tables = await dbManager.executeQuery(`
        SELECT name FROM sqlite_master WHERE type='table' AND name='js_test'
      `);
      expect(tables).toHaveLength(1);
    });

    it('should execute JavaScript migration down', async () => {
      const file = await commands.create('js_rollback', { template: 'js' });
      await fs.writeFile(file, `
export async function up(dbManager) {
  await dbManager.executeQuery('CREATE TABLE rollback_test (id INT)');
}

export async function down(dbManager) {
  await dbManager.executeQuery('DROP TABLE rollback_test');
}
      `);

      await commands.up();
      await commands.down(1);

      const tables = await dbManager.executeQuery(`
        SELECT name FROM sqlite_master WHERE type='table' AND name='rollback_test'
      `);
      expect(tables).toHaveLength(0);
    });
  });
});
