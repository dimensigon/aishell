/**
 * Advanced Migration Engine Tests
 * Comprehensive test suite for zero-downtime migrations
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AdvancedMigrationEngine } from '../../src/cli/migration-engine-advanced';
import { MigrationBuilder, MigrationPatterns, migration } from '../../src/cli/migration-dsl';
import { DatabaseConnectionManager, DatabaseType } from '../../src/cli/database-manager';
import { StateManager } from '../../src/core/state-manager';
import { BackupSystem } from '../../src/cli/backup-system';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

describe('AdvancedMigrationEngine', () => {
  let engine: AdvancedMigrationEngine;
  let dbManager: DatabaseConnectionManager;
  let stateManager: StateManager;
  let backupSystem: BackupSystem;
  let tmpDir: string;

  beforeEach(async () => {
    // Create temp directory for migrations
    tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'migration-test-'));

    // Setup mocks
    stateManager = new StateManager({ enablePersistence: false });
    dbManager = new DatabaseConnectionManager(stateManager);
    backupSystem = new BackupSystem(dbManager, stateManager);

    // Mock database operations
    vi.spyOn(dbManager, 'executeQuery').mockResolvedValue([]);
    vi.spyOn(dbManager, 'getActive').mockReturnValue({
      type: DatabaseType.POSTGRESQL,
      config: { name: 'test', database: 'test' },
      client: {} as any
    });

    // Mock backup system
    vi.spyOn(backupSystem, 'createBackup').mockResolvedValue({
      id: 'backup-123',
      timestamp: Date.now(),
      database: 'test',
      type: DatabaseType.POSTGRESQL,
      size: 1024,
      compressed: true,
      location: '/tmp/backup',
      status: 'completed'
    });

    engine = new AdvancedMigrationEngine(dbManager, stateManager, backupSystem, {
      migrationsDir: tmpDir,
      enableAutoBackup: false,
      enableAutoSnapshot: false
    });
  });

  afterEach(async () => {
    // Cleanup
    await fs.rm(tmpDir, { recursive: true, force: true });
    vi.restoreAllMocks();
  });

  describe('Migration Loading', () => {
    it('should load migration from YAML file', async () => {
      const migrationFile = path.join(tmpDir, 'test-migration.yaml');

      const builder = migration('test-migration', DatabaseType.POSTGRESQL)
        .phase('Add column')
        .addColumn('users', 'email_verified', 'BOOLEAN')
        .nullable()
        .withDefault(false);

      await fs.writeFile(migrationFile, builder.toYAML());

      const loaded = await engine.loadMigration(migrationFile);

      expect(loaded.name).toBe('test-migration');
      expect(loaded.database).toBe(DatabaseType.POSTGRESQL);
      expect(loaded.phases).toHaveLength(1);
      expect(loaded.phases[0].operations).toHaveLength(1);
    });

    it('should validate migration definition', async () => {
      const migrationFile = path.join(tmpDir, 'invalid-migration.yaml');

      // Create invalid migration (missing name)
      await fs.writeFile(migrationFile, `
migration:
  database: postgresql
  phases: []
`);

      await expect(engine.loadMigration(migrationFile)).rejects.toThrow('name is required');
    });

    it('should validate phase ordering', async () => {
      const migrationFile = path.join(tmpDir, 'bad-phases.yaml');

      await fs.writeFile(migrationFile, `
migration:
  name: bad-phases
  database: postgresql
  phases:
    - phase: 1
      description: Phase 1
      operations:
        - type: add_column
          table: users
          column: test
          dataType: TEXT
      validation: []
    - phase: 3
      description: Phase 3
      operations:
        - type: drop_column
          table: users
          column: test
      validation: []
`);

      await expect(engine.loadMigration(migrationFile)).rejects.toThrow('sequential');
    });
  });

  describe('Execution Planning', () => {
    it('should generate execution plan', async () => {
      const migrationFile = path.join(tmpDir, 'plan-test.yaml');

      const builder = migration('plan-test')
        .phase('Add column')
        .addColumn('users', 'status', 'VARCHAR(50)')
        .nullable()
        .phase('Backfill')
        .backfill('users', "status = 'active'");

      await fs.writeFile(migrationFile, builder.toYAML());

      const plan = await engine.plan(migrationFile);

      expect(plan.migration.name).toBe('plan-test');
      expect(plan.phases).toHaveLength(2);
      expect(plan.estimatedDuration).toBeGreaterThan(0);
    });

    it('should detect risks in plan', async () => {
      const migrationFile = path.join(tmpDir, 'risky-migration.yaml');

      const builder = migration('risky-migration')
        .phase('Add index without concurrent')
        .addIndex('users', 'idx_email', ['email'], { concurrent: false });

      await fs.writeFile(migrationFile, builder.toYAML());

      const plan = await engine.plan(migrationFile);

      expect(plan.risks.length).toBeGreaterThan(0);
      expect(plan.risks.some(r => r.includes('lock'))).toBe(true);
    });
  });

  describe('Migration Execution', () => {
    it('should execute simple migration', async () => {
      const migrationFile = path.join(tmpDir, 'simple-migration.yaml');

      const builder = migration('simple-migration')
        .phase('Add column')
        .addColumn('users', 'age', 'INTEGER')
        .nullable();

      await fs.writeFile(migrationFile, builder.toYAML());

      const execution = await engine.executeMigration(migrationFile, {
        skipBackup: true,
        skipSnapshot: true
      });

      expect(execution.status).toBe('completed');
      expect(execution.phaseResults).toHaveLength(1);
      expect(execution.phaseResults[0].status).toBe('completed');
    });

    it('should execute multi-phase migration', async () => {
      const migrationFile = path.join(tmpDir, 'multi-phase.yaml');

      const builder = migration('multi-phase')
        .phase('Phase 1')
        .addColumn('users', 'temp_col', 'TEXT')
        .phase('Phase 2')
        .backfill('users', "temp_col = 'default'")
        .phase('Phase 3')
        .dropColumn('users', 'temp_col');

      await fs.writeFile(migrationFile, builder.toYAML());

      const execution = await engine.executeMigration(migrationFile, {
        skipBackup: true,
        skipSnapshot: true
      });

      expect(execution.status).toBe('completed');
      expect(execution.phaseResults).toHaveLength(3);
    });

    it('should execute specific phase only', async () => {
      const migrationFile = path.join(tmpDir, 'phase-specific.yaml');

      const builder = migration('phase-specific')
        .phase('Phase 1')
        .addColumn('users', 'col1', 'TEXT')
        .phase('Phase 2')
        .addColumn('users', 'col2', 'TEXT')
        .phase('Phase 3')
        .addColumn('users', 'col3', 'TEXT');

      await fs.writeFile(migrationFile, builder.toYAML());

      const execution = await engine.executeMigration(migrationFile, {
        phase: 2,
        skipBackup: true,
        skipSnapshot: true
      });

      expect(execution.status).toBe('completed');
      expect(execution.currentPhase).toBe(2);
      expect(execution.phaseResults).toHaveLength(1);
    });

    it('should handle dry run', async () => {
      const migrationFile = path.join(tmpDir, 'dry-run.yaml');

      const builder = migration('dry-run')
        .phase('Add column')
        .addColumn('users', 'test', 'TEXT');

      await fs.writeFile(migrationFile, builder.toYAML());

      const execution = await engine.executeMigration(migrationFile, {
        dryRun: true
      });

      expect(execution.status).toBe('pending');
      expect(dbManager.executeQuery).not.toHaveBeenCalled();
    });
  });

  describe('SQL Generation', () => {
    it('should generate ADD COLUMN SQL', async () => {
      const migrationFile = path.join(tmpDir, 'add-column.yaml');

      const builder = migration('add-column')
        .phase('Add column')
        .addColumn('users', 'nickname', 'VARCHAR(100)')
        .nullable()
        .withDefault('Anonymous');

      await fs.writeFile(migrationFile, builder.toYAML());

      const plan = await engine.plan(migrationFile);
      const sql = plan.phases[0].operations[0];

      expect(sql).toContain('ALTER TABLE users');
      expect(sql).toContain('ADD COLUMN nickname');
      expect(sql).toContain('VARCHAR(100)');
      expect(sql).toContain('NULL');
      expect(sql).toContain("DEFAULT 'Anonymous'");
    });

    it('should generate DROP COLUMN SQL', async () => {
      const migrationFile = path.join(tmpDir, 'drop-column.yaml');

      const builder = migration('drop-column')
        .phase('Drop column')
        .dropColumn('users', 'deprecated_field');

      await fs.writeFile(migrationFile, builder.toYAML());

      const plan = await engine.plan(migrationFile);
      const sql = plan.phases[0].operations[0];

      expect(sql).toContain('ALTER TABLE users');
      expect(sql).toContain('DROP COLUMN deprecated_field');
    });

    it('should generate CREATE INDEX SQL with CONCURRENTLY', async () => {
      const migrationFile = path.join(tmpDir, 'add-index.yaml');

      const builder = migration('add-index')
        .phase('Add index')
        .addIndex('users', 'idx_email', ['email'], { concurrent: true });

      await fs.writeFile(migrationFile, builder.toYAML());

      const plan = await engine.plan(migrationFile);
      const sql = plan.phases[0].operations[0];

      expect(sql).toContain('CREATE INDEX CONCURRENTLY');
      expect(sql).toContain('idx_email');
      expect(sql).toContain('ON users');
      expect(sql).toContain('(email)');
    });

    it('should generate BACKFILL SQL', async () => {
      const migrationFile = path.join(tmpDir, 'backfill.yaml');

      const builder = migration('backfill')
        .phase('Backfill')
        .backfill('users', "status = 'active' WHERE status IS NULL");

      await fs.writeFile(migrationFile, builder.toYAML());

      const plan = await engine.plan(migrationFile);
      const sql = plan.phases[0].operations[0];

      expect(sql).toContain('UPDATE users');
      expect(sql).toContain('SET status');
    });
  });

  describe('Validation', () => {
    it('should validate column exists', async () => {
      const migrationFile = path.join(tmpDir, 'validate-exists.yaml');

      const builder = migration('validate-exists')
        .phase('Add and validate')
        .addColumn('users', 'verified', 'BOOLEAN')
        .validateColumnExists('users', 'verified');

      await fs.writeFile(migrationFile, builder.toYAML());

      // Mock query to return column exists
      vi.spyOn(dbManager, 'executeQuery').mockResolvedValue([
        { column_name: 'verified' }
      ]);

      const execution = await engine.executeMigration(migrationFile, {
        skipBackup: true,
        skipSnapshot: true
      });

      expect(execution.status).toBe('completed');
    });

    it('should fail validation if column missing', async () => {
      const migrationFile = path.join(tmpDir, 'validate-missing.yaml');

      const builder = migration('validate-missing')
        .phase('Validate')
        .validateColumnExists('users', 'nonexistent');

      await fs.writeFile(migrationFile, builder.toYAML());

      // Mock query to return no results
      vi.spyOn(dbManager, 'executeQuery').mockResolvedValue([]);

      await expect(
        engine.executeMigration(migrationFile, {
          skipBackup: true,
          skipSnapshot: true
        })
      ).rejects.toThrow();
    });
  });

  describe('Rollback', () => {
    it('should rollback on failure', async () => {
      const migrationFile = path.join(tmpDir, 'rollback-test.yaml');

      const builder = migration('rollback-test')
        .phase('Phase 1')
        .addColumn('users', 'temp', 'TEXT');

      await fs.writeFile(migrationFile, builder.toYAML());

      // Mock failure on second operation
      let callCount = 0;
      vi.spyOn(dbManager, 'executeQuery').mockImplementation(async () => {
        callCount++;
        if (callCount === 2) {
          throw new Error('Simulated failure');
        }
        return [];
      });

      await expect(
        engine.executeMigration(migrationFile, {
          skipBackup: true,
          skipSnapshot: true
        })
      ).rejects.toThrow('Simulated failure');

      // Verify rollback was attempted
      const status = await engine.getStatus();
      const execution = status.executions[0];
      expect(execution.status).toBe('failed');
    });
  });

  describe('Migration Status', () => {
    it('should track migration status', async () => {
      const migrationFile = path.join(tmpDir, 'status-test.yaml');

      const builder = migration('status-test')
        .phase('Add column')
        .addColumn('users', 'status_field', 'VARCHAR(50)');

      await fs.writeFile(migrationFile, builder.toYAML());

      await engine.executeMigration(migrationFile, {
        skipBackup: true,
        skipSnapshot: true
      });

      const status = await engine.getStatus();

      expect(status.executions.length).toBeGreaterThan(0);
      expect(status.lastMigration).toBeDefined();
      expect(status.lastMigration?.status).toBe('completed');
    });
  });

  describe('Migration Verification', () => {
    it('should verify safe migration', async () => {
      const migrationFile = path.join(tmpDir, 'safe-migration.yaml');

      const builder = migration('safe-migration')
        .phase('Add column')
        .addColumn('users', 'safe_col', 'TEXT')
        .nullable()
        .validate();

      await fs.writeFile(migrationFile, builder.toYAML());

      const result = await engine.verify(migrationFile);

      expect(result.safe).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should detect unsafe operations', async () => {
      const migrationFile = path.join(tmpDir, 'unsafe-migration.yaml');

      const builder = migration('unsafe-migration')
        .phase('Drop column')
        .dropColumn('users', 'important_data');

      await fs.writeFile(migrationFile, builder.toYAML());

      const result = await engine.verify(migrationFile);

      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings.some(w => w.includes('Dropping column'))).toBe(true);
    });

    it('should detect missing rollback operations', async () => {
      const migrationFile = path.join(tmpDir, 'no-rollback.yaml');

      await fs.writeFile(migrationFile, `
migration:
  name: no-rollback
  database: postgresql
  phases:
    - phase: 1
      description: No rollback
      operations:
        - type: add_column
          table: users
          column: test
          dataType: TEXT
      validation: []
`);

      const result = await engine.verify(migrationFile);

      expect(result.warnings.some(w => w.includes('No rollback'))).toBe(true);
    });

    it('should recommend concurrent index creation', async () => {
      const migrationFile = path.join(tmpDir, 'non-concurrent-index.yaml');

      const builder = migration('non-concurrent-index')
        .phase('Add index')
        .addIndex('users', 'idx_test', ['test'], { concurrent: false });

      await fs.writeFile(migrationFile, builder.toYAML());

      const result = await engine.verify(migrationFile);

      expect(result.warnings.some(w => w.includes('not concurrent'))).toBe(true);
      expect(result.recommendations.some(r => r.includes('concurrent: true'))).toBe(true);
    });
  });
});

describe('MigrationDSL', () => {
  describe('MigrationBuilder', () => {
    it('should build simple migration', () => {
      const builder = migration('test-migration')
        .phase('Add column')
        .addColumn('users', 'age', 'INTEGER')
        .nullable();

      const def = builder.build();

      expect(def.name).toBe('test-migration');
      expect(def.phases).toHaveLength(1);
      expect(def.phases[0].operations).toHaveLength(1);
      expect(def.phases[0].operations[0].type).toBe('add_column');
    });

    it('should build multi-phase migration', () => {
      const builder = migration('multi-phase')
        .phase('Phase 1')
        .addColumn('users', 'temp', 'TEXT')
        .phase('Phase 2')
        .backfill('users', "temp = 'default'")
        .phase('Phase 3')
        .dropColumn('users', 'temp');

      const def = builder.build();

      expect(def.phases).toHaveLength(3);
      expect(def.phases[0].phase).toBe(1);
      expect(def.phases[1].phase).toBe(2);
      expect(def.phases[2].phase).toBe(3);
    });

    it('should generate rollback operations', () => {
      const builder = migration('with-rollback')
        .phase('Add column')
        .addColumn('users', 'test', 'TEXT');

      const def = builder.build();

      expect(def.phases[0].rollbackOperations).toBeDefined();
      expect(def.phases[0].rollbackOperations).toHaveLength(1);
      expect(def.phases[0].rollbackOperations![0].type).toBe('drop_column');
    });

    it('should export to YAML', () => {
      const builder = migration('yaml-test')
        .phase('Add column')
        .addColumn('users', 'test', 'TEXT');

      const yaml = builder.toYAML();

      expect(yaml).toContain('migration:');
      expect(yaml).toContain('name: yaml-test');
      expect(yaml).toContain('phases:');
      expect(yaml).toContain('add_column');
    });
  });

  describe('MigrationPatterns', () => {
    it('should create add nullable column pattern', () => {
      const builder = MigrationPatterns.addNullableColumn(
        'users',
        'email',
        'VARCHAR(255)'
      );

      const def = builder.build();

      expect(def.phases).toHaveLength(1);
      expect(def.phases[0].operations[0].nullable).toBe(true);
    });

    it('should create add required column pattern', () => {
      const builder = MigrationPatterns.addRequiredColumn(
        'users',
        'status',
        'VARCHAR(50)',
        'active'
      );

      const def = builder.build();

      expect(def.phases.length).toBeGreaterThanOrEqual(3);
      // Phase 1: Add nullable column
      expect(def.phases[0].operations[0].nullable).toBe(true);
      // Phase 2: Backfill
      expect(def.phases[1].operations[0].type).toBe('backfill');
    });

    it('should create remove column pattern', () => {
      const builder = MigrationPatterns.removeColumn('users', 'deprecated');

      const def = builder.build();

      expect(def.phases.length).toBeGreaterThanOrEqual(3);
      // Last phase should drop the column
      const lastPhase = def.phases[def.phases.length - 1];
      expect(lastPhase.operations.some(op => op.type === 'drop_column')).toBe(true);
    });

    it('should create rename column pattern', () => {
      const builder = MigrationPatterns.safeRenameColumn(
        'users',
        'old_name',
        'new_name',
        'VARCHAR(255)'
      );

      const def = builder.build();

      expect(def.phases.length).toBeGreaterThanOrEqual(5);
      // Should include dual-write phases
      expect(def.phases.some(p =>
        p.operations.some(op => op.type === 'dual_write_enable')
      )).toBe(true);
    });

    it('should create change type pattern', () => {
      const builder = MigrationPatterns.changeColumnType(
        'users',
        'age',
        'VARCHAR(10)',
        'INTEGER'
      );

      const def = builder.build();

      expect(def.phases.length).toBeGreaterThanOrEqual(4);
      // Should create temp column, migrate, and swap
      expect(def.phases.some(p =>
        p.operations.some(op => op.column?.includes('_new'))
      )).toBe(true);
    });

    it('should create concurrent index pattern', () => {
      const builder = MigrationPatterns.addConcurrentIndex(
        'users',
        'idx_email',
        ['email']
      );

      const def = builder.build();

      expect(def.phases).toHaveLength(1);
      expect(def.phases[0].operations[0].concurrent).toBe(true);
    });

    it('should create foreign key pattern', () => {
      const builder = MigrationPatterns.addForeignKey(
        'orders',
        'user_id',
        'users'
      );

      const def = builder.build();

      expect(def.phases).toHaveLength(1);
      expect(def.phases[0].operations[0].type).toBe('add_constraint');
    });

    it('should create unique constraint pattern', () => {
      const builder = MigrationPatterns.addUniqueConstraint(
        'users',
        ['email', 'tenant_id']
      );

      const def = builder.build();

      expect(def.phases).toHaveLength(1);
      expect(def.phases[0].operations[0].type).toBe('add_constraint');
    });
  });
});
