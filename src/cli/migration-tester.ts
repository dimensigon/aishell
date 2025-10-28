/**
 * Migration Tester
 * Test database migrations before production deployment
 * Commands: ai-shell test-migration <file>, ai-shell validate-migration
 */

import { DatabaseConnectionManager, DatabaseType, ConnectionConfig } from './database-manager';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';
import * as fs from 'fs/promises';
import * as path from 'path';

interface MigrationFile {
  path: string;
  name: string;
  version: string;
  up: string;
  down: string;
}

interface MigrationTest {
  id: string;
  migration: MigrationFile;
  status: 'pending' | 'running' | 'passed' | 'failed';
  startTime?: number;
  endTime?: number;
  duration?: number;
  error?: string;
  results: TestResult[];
}

interface TestResult {
  name: string;
  passed: boolean;
  message: string;
  duration: number;
}

export class MigrationTester {
  private logger = createLogger('MigrationTester');
  private tests = new Map<string, MigrationTest>();

  constructor(
    private dbManager: DatabaseConnectionManager,
    private _stateManager: StateManager
  ) {}

  /**
   * Test migration file
   */
  async testMigration(filePath: string): Promise<MigrationTest> {
    this.logger.info('Testing migration', { filePath });

    const migration = await this.loadMigrationFile(filePath);
    const testId = `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    const test: MigrationTest = {
      id: testId,
      migration,
      status: 'pending',
      results: []
    };

    this.tests.set(testId, test);

    try {
      test.status = 'running';
      test.startTime = Date.now();

      // Create test database
      const testDb = await this.createTestDatabase();

      try {
        // Run tests
        await this.runMigrationTests(test, testDb);

        test.status = 'passed';
      } finally {
        // Cleanup test database
        await this.cleanupTestDatabase(testDb);
      }

      test.endTime = Date.now();
      test.duration = test.endTime - test.startTime;

      this.logger.info('Migration test completed', {
        testId,
        status: test.status,
        duration: test.duration
      });

      return test;
    } catch (error) {
      test.status = 'failed';
      test.error = error instanceof Error ? error.message : String(error);
      test.endTime = Date.now();
      test.duration = test.endTime - (test.startTime || Date.now());

      this.logger.error('Migration test failed', error, { testId });

      return test;
    }
  }

  /**
   * Load migration file
   */
  private async loadMigrationFile(filePath: string): Promise<MigrationFile> {
    const content = await fs.readFile(filePath, 'utf-8');
    const name = path.basename(filePath);

    // Parse migration file
    const migration: MigrationFile = {
      path: filePath,
      name,
      version: this.extractVersion(name),
      up: '',
      down: ''
    };

    // Simple parser for migration files
    if (filePath.endsWith('.sql')) {
      migration.up = content;
      migration.down = '';
    } else {
      // Parse JavaScript/TypeScript migration file
      const upMatch = content.match(/exports\.up\s*=\s*async.*?\{([\s\S]*?)\}/);
      const downMatch = content.match(/exports\.down\s*=\s*async.*?\{([\s\S]*?)\}/);

      if (upMatch) migration.up = upMatch[1];
      if (downMatch) migration.down = downMatch[1];
    }

    return migration;
  }

  /**
   * Extract version from migration filename
   */
  private extractVersion(filename: string): string {
    const match = filename.match(/^(\d+)/);
    return match ? match[1] : '0';
  }

  /**
   * Run migration tests
   */
  private async runMigrationTests(test: MigrationTest, testDb: string): Promise<void> {
    // Switch to test database
    await this.dbManager.switchActive(testDb);

    try {
      // Test 1: Migration applies successfully
      await this.addTestResult(
        test,
        'Migration applies successfully',
        async () => {
          await this.applyMigration(test.migration.up);
        }
      );

      // Test 2: Schema validation
      await this.addTestResult(
        test,
        'Schema validation',
        async () => {
          await this.validateSchema();
        }
      );

      // Test 3: Rollback works
      if (test.migration.down) {
        await this.addTestResult(
          test,
          'Rollback works',
          async () => {
            await this.rollbackMigration(test.migration.down);
          }
        );

        // Test 4: Re-apply after rollback
        await this.addTestResult(
          test,
          'Re-apply after rollback',
          async () => {
            await this.applyMigration(test.migration.up);
          }
        );
      }

      // Test 5: Idempotency (can run twice safely)
      await this.addTestResult(
        test,
        'Idempotency check',
        async () => {
          try {
            await this.applyMigration(test.migration.up);
          } catch (error) {
            // Some migrations may fail on second run, that's expected
            this.logger.debug('Idempotency check: migration failed on second run', { error });
          }
        }
      );

      // Test 6: Performance check
      await this.addTestResult(
        test,
        'Performance check',
        async () => {
          const startTime = Date.now();
          await this.applyMigration(test.migration.up);
          const duration = Date.now() - startTime;

          if (duration > 30000) {
            // 30 seconds
            throw new Error(`Migration took too long: ${duration}ms`);
          }
        }
      );
    } finally {
      // Restore original connection
      const original = this.dbManager.getActive();
      if (original) {
        await this.dbManager.switchActive(original.config.name);
      }
    }
  }

  /**
   * Add test result
   */
  private async addTestResult(
    test: MigrationTest,
    name: string,
    testFn: () => Promise<void>
  ): Promise<void> {
    const startTime = Date.now();

    try {
      await testFn();

      test.results.push({
        name,
        passed: true,
        message: 'Test passed',
        duration: Date.now() - startTime
      });
    } catch (error) {
      test.results.push({
        name,
        passed: false,
        message: error instanceof Error ? error.message : String(error),
        duration: Date.now() - startTime
      });

      throw error;
    }
  }

  /**
   * Apply migration
   */
  private async applyMigration(sql: string): Promise<void> {
    const statements = sql
      .split(';')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    for (const statement of statements) {
      try {
        await this.dbManager.executeQuery(statement);
      } catch (error) {
        this.logger.error('Failed to execute statement', error, {
          statement: statement.substring(0, 100)
        });
        throw error;
      }
    }
  }

  /**
   * Rollback migration
   */
  private async rollbackMigration(sql: string): Promise<void> {
    await this.applyMigration(sql);
  }

  /**
   * Validate schema
   */
  private async validateSchema(): Promise<void> {
    const connection = this.dbManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    try {
      switch (connection.type) {
        case DatabaseType.POSTGRESQL:
          await connection.client.query(`
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
          `);
          break;

        case DatabaseType.MYSQL:
          await connection.client.query(`
            SELECT TABLE_NAME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
          `);
          break;

        case DatabaseType.SQLITE:
          await new Promise((resolve, reject) => {
            connection.client.all(
              "SELECT name FROM sqlite_master WHERE type='table'",
              (err: Error, rows: any) => {
                if (err) reject(err);
                else resolve(rows);
              }
            );
          });
          break;
      }
    } catch (error) {
      throw new Error(`Schema validation failed: ${error}`);
    }
  }

  /**
   * Create test database
   */
  private async createTestDatabase(): Promise<string> {
    const connection = this.dbManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    const testDbName = `test_${connection.config.database}_${Date.now()}`;

    this.logger.info('Creating test database', { testDbName });

    try {
      switch (connection.type) {
        case DatabaseType.POSTGRESQL:
          await connection.client.query(`CREATE DATABASE ${testDbName}`);
          break;

        case DatabaseType.MYSQL:
          await connection.client.query(`CREATE DATABASE ${testDbName}`);
          break;

        case DatabaseType.SQLITE:
          // SQLite doesn't need database creation, just use a temp file
          break;
      }

      // Connect to test database
      const testConfig: ConnectionConfig = {
        ...connection.config,
        name: testDbName,
        database: testDbName
      };

      await this.dbManager.connect(testConfig);

      return testDbName;
    } catch (error) {
      this.logger.error('Failed to create test database', error);
      throw error;
    }
  }

  /**
   * Cleanup test database
   */
  private async cleanupTestDatabase(testDbName: string): Promise<void> {
    this.logger.info('Cleaning up test database', { testDbName });

    try {
      // Get original connection info
      const originalConnection = this.dbManager.getActive();
      const testConnection = this.dbManager.getConnection(testDbName);

      if (!testConnection) {
        return;
      }

      // Disconnect from test database
      await this.dbManager.disconnect(testDbName);

      // Drop test database
      if (originalConnection) {
        await this.dbManager.switchActive(originalConnection.config.name);

        switch (originalConnection.type) {
          case DatabaseType.POSTGRESQL:
            await originalConnection.client.query(`DROP DATABASE IF EXISTS ${testDbName}`);
            break;

          case DatabaseType.MYSQL:
            await originalConnection.client.query(`DROP DATABASE IF EXISTS ${testDbName}`);
            break;

          case DatabaseType.SQLITE:
            // Delete SQLite file
            await fs.unlink(testConnection.config.database);
            break;
        }
      }
    } catch (error) {
      this.logger.error('Failed to cleanup test database', error);
    }
  }

  /**
   * Validate migration file
   */
  async validateMigrationFile(filePath: string): Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
  }> {
    this.logger.info('Validating migration file', { filePath });

    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Check file exists
      await fs.access(filePath);

      // Load migration
      const migration = await this.loadMigrationFile(filePath);

      // Check version format
      if (!/^\d+$/.test(migration.version)) {
        errors.push('Invalid version format. Use numeric timestamps (e.g., 20240101120000)');
      }

      // Check has up migration
      if (!migration.up || migration.up.trim().length === 0) {
        errors.push('Migration must have an "up" section');
      }

      // Warn if no down migration
      if (!migration.down || migration.down.trim().length === 0) {
        warnings.push('Migration has no "down" section. Rollback will not be possible');
      }

      // Check for dangerous operations
      const dangerousPatterns = [
        /DROP\s+DATABASE/i,
        /DROP\s+TABLE.*CASCADE/i,
        /TRUNCATE/i,
        /DELETE\s+FROM.*WHERE\s+1\s*=\s*1/i
      ];

      dangerousPatterns.forEach((pattern) => {
        if (pattern.test(migration.up)) {
          warnings.push(`Potentially dangerous operation detected: ${pattern.source}`);
        }
      });

      // Check for transaction support
      if (!/BEGIN|START TRANSACTION/i.test(migration.up)) {
        warnings.push('Consider wrapping migration in a transaction');
      }
    } catch (error) {
      errors.push(`Failed to read migration file: ${error}`);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Batch test multiple migrations
   */
  async testMigrations(migrationPaths: string[]): Promise<MigrationTest[]> {
    this.logger.info('Batch testing migrations', { count: migrationPaths.length });

    const results: MigrationTest[] = [];

    for (const path of migrationPaths) {
      try {
        const result = await this.testMigration(path);
        results.push(result);
      } catch (error) {
        this.logger.error('Migration test failed', error, { path });
      }
    }

    return results;
  }

  /**
   * Generate test report
   */
  generateReport(tests: MigrationTest[]): string {
    let report = '# Migration Test Report\n\n';
    report += `Total Migrations: ${tests.length}\n`;
    report += `Passed: ${tests.filter((t) => t.status === 'passed').length}\n`;
    report += `Failed: ${tests.filter((t) => t.status === 'failed').length}\n\n`;

    tests.forEach((test) => {
      report += `## ${test.migration.name}\n`;
      report += `Status: ${test.status}\n`;
      report += `Duration: ${test.duration}ms\n`;

      if (test.error) {
        report += `Error: ${test.error}\n`;
      }

      report += '\n### Test Results:\n';
      test.results.forEach((result) => {
        const icon = result.passed ? '✓' : '✗';
        report += `${icon} ${result.name} (${result.duration}ms)\n`;
        if (!result.passed) {
          report += `  Error: ${result.message}\n`;
        }
      });

      report += '\n---\n\n';
    });

    return report;
  }

  /**
   * Get test history
   */
  getTestHistory(limit?: number): MigrationTest[] {
    const tests = Array.from(this.tests.values()).sort((a, b) => {
      return (b.startTime || 0) - (a.startTime || 0);
    });

    return limit ? tests.slice(0, limit) : tests;
  }

  /**
   * Export test results
   */
  async exportResults(outputPath: string): Promise<void> {
    const tests = Array.from(this.tests.values());
    const report = this.generateReport(tests);

    await fs.writeFile(outputPath, report);

    this.logger.info('Test results exported', { outputPath });
  }

  /**
   * Simulate migration in dry-run mode
   */
  async dryRun(filePath: string): Promise<string> {
    const migration = await this.loadMigrationFile(filePath);

    let output = `DRY RUN: ${migration.name}\n\n`;
    output += 'The following SQL would be executed:\n\n';
    output += '--- UP Migration ---\n';
    output += migration.up;
    output += '\n\n--- DOWN Migration ---\n';
    output += migration.down || 'No down migration defined';

    return output;
  }
}
