/**
 * Migration Commands - Handler logic for all migration operations
 *
 * Implements the 8 core migration commands:
 * 1. create - Create new migration file
 * 2. up - Run pending migrations
 * 3. down - Rollback migrations
 * 4. status - Show migration state
 * 5. rollback - Rollback last migration
 * 6. reset - Rollback all migrations
 * 7. fresh - Drop all and re-run
 * 8. redo - Rollback and re-run last
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { StateManager } from '../core/state-manager';
import { createLogger } from '../core/logger';
import chalk from 'chalk';

const logger = createLogger('MigrationCommands');

/**
 * Migration record in tracking table
 */
export interface MigrationRecord {
  id: number;
  migration: string;
  batch: number;
  executed_at: Date;
}

/**
 * Migration file metadata
 */
export interface MigrationFile {
  filename: string;
  filepath: string;
  timestamp: number;
  name: string;
  executed: boolean;
  batch?: number;
}

/**
 * Migration Commands Handler
 */
export class MigrationCommands {
  private migrationsTable = 'schema_migrations';
  private logger = createLogger('MigrationCommands');

  constructor(
    private dbManager: DatabaseConnectionManager,
    private stateManager: StateManager,
    private migrationsDir: string
  ) {}

  /**
   * Initialize migrations table
   */
  async initialize(): Promise<void> {
    const connection = this.dbManager.getActive();
    if (!connection) {
      throw new Error('No active database connection');
    }

    const sql = this.getCreateTableSQL(connection.type);
    await this.dbManager.executeQuery(sql);

    this.logger.info('Migrations table initialized');
  }

  /**
   * Create new migration file
   */
  async create(name: string, options: { template?: 'sql' | 'js' } = {}): Promise<string> {
    const timestamp = Date.now();
    const sanitizedName = name.replace(/\s+/g, '_').toLowerCase();
    const filename = `${timestamp}_${sanitizedName}`;

    const ext = options.template === 'js' ? '.js' : '.sql';
    const filepath = path.join(this.migrationsDir, filename + ext);

    // Generate migration content
    const content = options.template === 'js'
      ? this.getJavaScriptTemplate(sanitizedName)
      : this.getSQLTemplate(sanitizedName);

    await fs.writeFile(filepath, content, 'utf-8');

    this.logger.info('Migration created', { filename, filepath });
    return filepath;
  }

  /**
   * Run pending migrations
   */
  async up(count?: number): Promise<{ executed: MigrationFile[], batch: number }> {
    await this.initialize();

    const pending = await this.getPendingMigrations();

    if (pending.length === 0) {
      console.log(chalk.yellow('No pending migrations to run'));
      return { executed: [], batch: await this.getNextBatch() };
    }

    const toExecute = count ? pending.slice(0, count) : pending;
    const batch = await this.getNextBatch();
    const executed: MigrationFile[] = [];

    console.log(chalk.blue(`Running ${toExecute.length} migration(s)...`));
    console.log();

    for (const migration of toExecute) {
      try {
        console.log(chalk.gray('Migrating:'), migration.filename);
        await this.executeMigration(migration, 'up');
        await this.recordMigration(migration.filename, batch);
        executed.push(migration);
        console.log(chalk.green('✓ Migrated:'), migration.filename);
      } catch (error) {
        console.error(chalk.red('✗ Failed:'), migration.filename);
        console.error(chalk.red('Error:'), error);
        throw error;
      }
    }

    console.log();
    console.log(chalk.green(`Successfully executed ${executed.length} migration(s)`));

    return { executed, batch };
  }

  /**
   * Rollback migrations
   */
  async down(count: number = 1): Promise<{ rolledBack: MigrationFile[], batch: number }> {
    await this.initialize();

    const executed = await this.getExecutedMigrations();
    const lastBatch = await this.getLastBatch();

    if (executed.length === 0) {
      console.log(chalk.yellow('No migrations to rollback'));
      return { rolledBack: [], batch: 0 };
    }

    // Get migrations from the last N batches
    const batches = new Set(executed.map(m => m.batch!).sort((a, b) => b - a).slice(0, count));
    const toRollback = executed.filter(m => batches.has(m.batch!)).reverse();

    console.log(chalk.blue(`Rolling back ${toRollback.length} migration(s)...`));
    console.log();

    const rolledBack: MigrationFile[] = [];

    for (const migration of toRollback) {
      try {
        console.log(chalk.gray('Rolling back:'), migration.filename);
        await this.executeMigration(migration, 'down');
        await this.removeMigration(migration.filename);
        rolledBack.push(migration);
        console.log(chalk.green('✓ Rolled back:'), migration.filename);
      } catch (error) {
        console.error(chalk.red('✗ Failed:'), migration.filename);
        console.error(chalk.red('Error:'), error);
        throw error;
      }
    }

    console.log();
    console.log(chalk.green(`Successfully rolled back ${rolledBack.length} migration(s)`));

    return { rolledBack, batch: lastBatch };
  }

  /**
   * Get migration status
   */
  async status(): Promise<{ executed: MigrationFile[], pending: MigrationFile[] }> {
    await this.initialize();

    const allFiles = await this.getAllMigrations();
    const executed = await this.getExecutedMigrations();
    const pending = await this.getPendingMigrations();

    return { executed, pending };
  }

  /**
   * Rollback last batch
   */
  async rollback(): Promise<{ rolledBack: MigrationFile[] }> {
    const result = await this.down(1);
    return { rolledBack: result.rolledBack };
  }

  /**
   * Rollback all migrations
   */
  async reset(): Promise<{ rolledBack: MigrationFile[] }> {
    await this.initialize();

    const executed = await this.getExecutedMigrations();

    if (executed.length === 0) {
      console.log(chalk.yellow('No migrations to reset'));
      return { rolledBack: [] };
    }

    console.log(chalk.blue(`Resetting all ${executed.length} migration(s)...`));
    console.log();

    const rolledBack: MigrationFile[] = [];

    // Rollback in reverse order
    for (const migration of executed.reverse()) {
      try {
        console.log(chalk.gray('Rolling back:'), migration.filename);
        await this.executeMigration(migration, 'down');
        await this.removeMigration(migration.filename);
        rolledBack.push(migration);
        console.log(chalk.green('✓ Rolled back:'), migration.filename);
      } catch (error) {
        console.error(chalk.red('✗ Failed:'), migration.filename);
        console.error(chalk.red('Error:'), error);
        throw error;
      }
    }

    console.log();
    console.log(chalk.green(`Successfully reset ${rolledBack.length} migration(s)`));

    return { rolledBack };
  }

  /**
   * Drop all tables and re-run migrations
   */
  async fresh(): Promise<{ tables: string[], executed: MigrationFile[] }> {
    console.log(chalk.yellow('Warning: This will drop all tables!'));
    console.log();

    // Get all tables before dropping
    const tables = await this.getAllTables();

    console.log(chalk.blue(`Dropping ${tables.length} table(s)...`));

    // Drop all tables
    for (const table of tables) {
      try {
        await this.dropTable(table);
        console.log(chalk.gray('✓ Dropped:'), table);
      } catch (error) {
        console.log(chalk.yellow('⚠ Could not drop:'), table);
      }
    }

    console.log();
    console.log(chalk.blue('Running all migrations...'));
    console.log();

    // Re-run all migrations
    const result = await this.up();

    return {
      tables,
      executed: result.executed
    };
  }

  /**
   * Rollback and re-run last migration
   */
  async redo(): Promise<{ migration: MigrationFile | null }> {
    await this.initialize();

    const executed = await this.getExecutedMigrations();

    if (executed.length === 0) {
      console.log(chalk.yellow('No migrations to redo'));
      return { migration: null };
    }

    const lastMigration = executed[executed.length - 1];

    console.log(chalk.blue('Redoing last migration:'), lastMigration.filename);
    console.log();

    // Rollback
    console.log(chalk.gray('Rolling back...'));
    await this.executeMigration(lastMigration, 'down');
    await this.removeMigration(lastMigration.filename);
    console.log(chalk.green('✓ Rolled back'));

    console.log();

    // Re-run
    console.log(chalk.gray('Re-running...'));
    const batch = await this.getNextBatch();
    await this.executeMigration(lastMigration, 'up');
    await this.recordMigration(lastMigration.filename, batch);
    console.log(chalk.green('✓ Migrated'));

    console.log();
    console.log(chalk.green('Successfully redid migration'));

    return { migration: lastMigration };
  }

  // Helper methods

  private async getAllMigrations(): Promise<MigrationFile[]> {
    const files = await fs.readdir(this.migrationsDir);
    const migrationFiles = files.filter(f => f.endsWith('.sql') || f.endsWith('.js'));

    return migrationFiles.map(filename => this.parseMigrationFilename(filename));
  }

  private async getExecutedMigrations(): Promise<MigrationFile[]> {
    const records = await this.getMigrationRecords();
    const allFiles = await this.getAllMigrations();

    return allFiles
      .filter(file => records.some(r => r.migration === file.filename))
      .map(file => {
        const record = records.find(r => r.migration === file.filename);
        return {
          ...file,
          executed: true,
          batch: record?.batch
        };
      })
      .sort((a, b) => a.timestamp - b.timestamp);
  }

  private async getPendingMigrations(): Promise<MigrationFile[]> {
    const records = await this.getMigrationRecords();
    const allFiles = await this.getAllMigrations();

    return allFiles
      .filter(file => !records.some(r => r.migration === file.filename))
      .sort((a, b) => a.timestamp - b.timestamp);
  }

  private async getMigrationRecords(): Promise<MigrationRecord[]> {
    try {
      const result = await this.dbManager.executeQuery(
        `SELECT * FROM ${this.migrationsTable} ORDER BY id ASC`
      );
      return result as MigrationRecord[];
    } catch (error) {
      // Table doesn't exist yet
      return [];
    }
  }

  private async getNextBatch(): Promise<number> {
    const records = await this.getMigrationRecords();
    if (records.length === 0) {
      return 1;
    }
    return Math.max(...records.map(r => r.batch)) + 1;
  }

  private async getLastBatch(): Promise<number> {
    const records = await this.getMigrationRecords();
    if (records.length === 0) {
      return 0;
    }
    return Math.max(...records.map(r => r.batch));
  }

  private async recordMigration(filename: string, batch: number): Promise<void> {
    const connection = this.dbManager.getActive();
    if (!connection) {
      throw new Error('No active database connection');
    }

    const sql = this.getInsertSQL(connection.type, filename, batch);
    await this.dbManager.executeQuery(sql);
  }

  private async removeMigration(filename: string): Promise<void> {
    await this.dbManager.executeQuery(
      `DELETE FROM ${this.migrationsTable} WHERE migration = '${filename}'`
    );
  }

  private async executeMigration(migration: MigrationFile, direction: 'up' | 'down'): Promise<void> {
    const content = await fs.readFile(migration.filepath, 'utf-8');

    if (migration.filename.endsWith('.sql')) {
      await this.executeSQLMigration(content, direction);
    } else if (migration.filename.endsWith('.js')) {
      await this.executeJSMigration(migration.filepath, direction);
    } else {
      throw new Error(`Unsupported migration file type: ${migration.filename}`);
    }
  }

  private async executeSQLMigration(content: string, direction: 'up' | 'down'): Promise<void> {
    // Parse SQL file sections
    const upMatch = content.match(/--\s*@up\s*\n([\s\S]*?)(?:--\s*@down|$)/i);
    const downMatch = content.match(/--\s*@down\s*\n([\s\S]*?)$/i);

    let sql = '';
    if (direction === 'up') {
      sql = upMatch ? upMatch[1].trim() : content;
    } else {
      sql = downMatch ? downMatch[1].trim() : '';
    }

    if (!sql) {
      throw new Error(`No ${direction} migration found in file`);
    }

    // Execute SQL statements
    const statements = sql.split(';').filter(s => s.trim());

    for (const statement of statements) {
      if (statement.trim()) {
        await this.dbManager.executeQuery(statement.trim());
      }
    }
  }

  private async executeJSMigration(filepath: string, direction: 'up' | 'down'): Promise<void> {
    // Dynamic import of JavaScript migration
    const migration = await import(filepath);

    if (!migration[direction]) {
      throw new Error(`Migration file does not export ${direction} function`);
    }

    const connection = this.dbManager.getActive();
    if (!connection) {
      throw new Error('No active database connection');
    }

    // Execute migration function
    await migration[direction](this.dbManager);
  }

  private parseMigrationFilename(filename: string): MigrationFile {
    const parts = filename.split('_');
    const timestamp = parseInt(parts[0]);
    const name = parts.slice(1).join('_').replace(/\.(sql|js)$/, '');

    return {
      filename,
      filepath: path.join(this.migrationsDir, filename),
      timestamp,
      name,
      executed: false
    };
  }

  private async getAllTables(): Promise<string[]> {
    const connection = this.dbManager.getActive();
    if (!connection) {
      return [];
    }

    let sql = '';
    switch (connection.type) {
      case DatabaseType.POSTGRESQL:
        sql = `
          SELECT tablename
          FROM pg_tables
          WHERE schemaname = 'public'
        `;
        break;

      case DatabaseType.MYSQL:
        sql = `
          SELECT table_name
          FROM information_schema.tables
          WHERE table_schema = DATABASE()
        `;
        break;

      case DatabaseType.SQLITE:
        sql = `
          SELECT name
          FROM sqlite_master
          WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
        `;
        break;

      default:
        return [];
    }

    const result = await this.dbManager.executeQuery(sql);
    return result.map((row: any) => Object.values(row)[0] as string);
  }

  private async dropTable(table: string): Promise<void> {
    const connection = this.dbManager.getActive();
    if (!connection) {
      return;
    }

    let sql = `DROP TABLE IF EXISTS ${table}`;

    if (connection.type === DatabaseType.POSTGRESQL) {
      sql += ' CASCADE';
    }

    await this.dbManager.executeQuery(sql);
  }

  private getCreateTableSQL(dbType: DatabaseType): string {
    switch (dbType) {
      case DatabaseType.POSTGRESQL:
        return `
          CREATE TABLE IF NOT EXISTS ${this.migrationsTable} (
            id SERIAL PRIMARY KEY,
            migration VARCHAR(255) NOT NULL UNIQUE,
            batch INTEGER NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          )
        `;

      case DatabaseType.MYSQL:
        return `
          CREATE TABLE IF NOT EXISTS ${this.migrationsTable} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            migration VARCHAR(255) NOT NULL UNIQUE,
            batch INT NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          )
        `;

      case DatabaseType.SQLITE:
        return `
          CREATE TABLE IF NOT EXISTS ${this.migrationsTable} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration TEXT NOT NULL UNIQUE,
            batch INTEGER NOT NULL,
            executed_at DATETIME DEFAULT CURRENT_TIMESTAMP
          )
        `;

      default:
        throw new Error(`Unsupported database type: ${dbType}`);
    }
  }

  private getInsertSQL(dbType: DatabaseType, filename: string, batch: number): string {
    switch (dbType) {
      case DatabaseType.POSTGRESQL:
      case DatabaseType.MYSQL:
      case DatabaseType.SQLITE:
        return `
          INSERT INTO ${this.migrationsTable} (migration, batch)
          VALUES ('${filename}', ${batch})
        `;

      default:
        throw new Error(`Unsupported database type: ${dbType}`);
    }
  }

  private getSQLTemplate(name: string): string {
    return `-- Migration: ${name}
-- Created: ${new Date().toISOString()}

-- @up
-- Write your forward migration here
-- Example:
-- CREATE TABLE example (
--   id SERIAL PRIMARY KEY,
--   name VARCHAR(255) NOT NULL,
--   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- @down
-- Write your rollback migration here
-- Example:
-- DROP TABLE IF EXISTS example;
`;
  }

  private getJavaScriptTemplate(name: string): string {
    return `/**
 * Migration: ${name}
 * Created: ${new Date().toISOString()}
 */

/**
 * Run the migration
 * @param {DatabaseConnectionManager} dbManager
 */
export async function up(dbManager) {
  // Write your forward migration here
  // Example:
  // await dbManager.executeQuery(\`
  //   CREATE TABLE example (
  //     id SERIAL PRIMARY KEY,
  //     name VARCHAR(255) NOT NULL,
  //     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  //   )
  // \`);
}

/**
 * Rollback the migration
 * @param {DatabaseConnectionManager} dbManager
 */
export async function down(dbManager) {
  // Write your rollback migration here
  // Example:
  // await dbManager.executeQuery('DROP TABLE IF EXISTS example');
}
`;
  }
}

export default MigrationCommands;
