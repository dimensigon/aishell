/**
 * Migration Engine
 * AI-powered database migration with natural language planning and safe execution
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { EventEmitter } from 'eventemitter3';
import { LLMMCPBridge } from '../llm/mcp-bridge';
import { StateManager } from '../core/state-manager';

/**
 * Migration plan
 */
export interface MigrationPlan {
  id: string;
  description: string;
  sql: string;
  rollbackSql: string;
  impact: {
    tables: string[];
    estimatedRows: number;
    risk: 'low' | 'medium' | 'high';
    warnings: string[];
  };
  beforeSchema?: any;
  afterSchema?: any;
}

/**
 * Migration options
 */
export interface MigrationOptions {
  dryRun?: boolean;
  transaction?: boolean;
  timeout?: number;
  continueOnError?: boolean;
}

/**
 * Migration status
 */
export interface MigrationStatus {
  applied: Migration[];
  pending: Migration[];
  failed: Migration[];
  lastMigration?: Migration;
}

/**
 * Migration record
 */
export interface Migration {
  id: string;
  name: string;
  description?: string;
  sql: string;
  rollbackSql?: string;
  appliedAt?: number;
  rolledBackAt?: number;
  status: 'pending' | 'applied' | 'failed' | 'rolled_back';
  error?: string;
}

/**
 * Migration events
 */
export interface MigrationEvents {
  planGenerated: (plan: MigrationPlan) => void;
  migrationStart: (migration: Migration) => void;
  migrationComplete: (migration: Migration) => void;
  migrationError: (migration: Migration, error: Error) => void;
  rollbackStart: (migration: Migration) => void;
  rollbackComplete: (migration: Migration) => void;
}

/**
 * Migration Engine
 */
export class MigrationEngine extends EventEmitter<MigrationEvents> {
  private migrations: Migration[] = [];
  private stateManager: StateManager;

  constructor(
    private readonly llmBridge: LLMMCPBridge,
    private readonly config: {
      migrationsDir?: string;
      trackingTable?: string;
      autoRollback?: boolean;
    } = {}
  ) {
    super();
    this.config.migrationsDir = this.config.migrationsDir || './migrations';
    this.config.trackingTable = this.config.trackingTable || 'schema_migrations';
    this.config.autoRollback = this.config.autoRollback !== false;

    this.stateManager = new StateManager({
      enablePersistence: true,
      persistencePath: path.join(this.config.migrationsDir, '.migration-state')
    });

    this.initialize();
  }

  /**
   * Initialize migration engine
   */
  private async initialize(): Promise<void> {
    // Ensure migrations directory exists
    await fs.mkdir(this.config.migrationsDir!, { recursive: true });

    // Load migration history from state
    await this.loadMigrationHistory();
  }

  /**
   * Plan migration from natural language description
   */
  async planMigration(nlDescription: string): Promise<MigrationPlan> {
    try {
      // Use LLM to generate migration SQL from natural language
      const prompt = `
Generate a database migration SQL script for the following requirement:

${nlDescription}

Please provide:
1. The forward migration SQL (DDL statements)
2. The rollback SQL (to undo the migration)
3. List of affected tables
4. Risk assessment (low/medium/high)
5. Any warnings or considerations

Format your response as JSON with these fields:
{
  "sql": "...",
  "rollbackSql": "...",
  "tables": ["table1", "table2"],
  "risk": "low|medium|high",
  "warnings": ["warning1", "warning2"]
}
`;

      const response = await this.llmBridge.generate({
        messages: [
          {
            role: 'system',
            content: 'You are a database migration expert. Generate safe, production-ready SQL migrations.'
          },
          {
            role: 'user',
            content: prompt
          }
        ]
      });

      // Parse LLM response
      const jsonMatch = response.content.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('Failed to parse migration plan from LLM response');
      }

      const parsed = JSON.parse(jsonMatch[0]);

      const plan: MigrationPlan = {
        id: this.generateMigrationId(),
        description: nlDescription,
        sql: parsed.sql,
        rollbackSql: parsed.rollbackSql,
        impact: {
          tables: parsed.tables || [],
          estimatedRows: 0,
          risk: parsed.risk || 'medium',
          warnings: parsed.warnings || []
        }
      };

      this.emit('planGenerated', plan);
      return plan;
    } catch (error) {
      throw new Error(`Failed to generate migration plan: ${error}`);
    }
  }

  /**
   * Execute migration
   */
  async executeMigration(migrationFile: string, options: MigrationOptions = {}): Promise<void> {
    try {
      // Load migration file
      const migration = await this.loadMigrationFile(migrationFile);

      // Check if already applied
      const existing = this.migrations.find(m => m.id === migration.id);
      if (existing && existing.status === 'applied') {
        console.log(`Migration ${migration.id} already applied`);
        return;
      }

      this.emit('migrationStart', migration);

      // Dry run check
      if (options.dryRun) {
        console.log('Dry run - would execute:');
        console.log(migration.sql);
        return;
      }

      // Execute migration
      if (options.transaction) {
        await this.executeInTransaction(migration, options);
      } else {
        await this.executeDirectly(migration, options);
      }

      // Update migration record
      migration.status = 'applied';
      migration.appliedAt = Date.now();

      // Save to tracking table and state
      await this.recordMigration(migration);

      this.emit('migrationComplete', migration);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));

      // Load the migration to emit error event
      const migration = await this.loadMigrationFile(migrationFile);
      migration.status = 'failed';
      migration.error = err.message;

      this.emit('migrationError', migration, err);

      // Auto-rollback if enabled
      if (this.config.autoRollback && migration.rollbackSql) {
        console.log('Auto-rollback enabled, rolling back migration...');
        await this.rollbackMigration(migration);
      }

      throw err;
    }
  }

  /**
   * Rollback migration(s)
   */
  async rollback(steps: number = 1): Promise<void> {
    const appliedMigrations = this.migrations
      .filter(m => m.status === 'applied')
      .sort((a, b) => (b.appliedAt || 0) - (a.appliedAt || 0))
      .slice(0, steps);

    for (const migration of appliedMigrations) {
      await this.rollbackMigration(migration);
    }
  }

  /**
   * Rollback single migration
   */
  private async rollbackMigration(migration: Migration): Promise<void> {
    if (!migration.rollbackSql) {
      throw new Error(`Migration ${migration.id} has no rollback SQL`);
    }

    this.emit('rollbackStart', migration);

    try {
      // Execute rollback SQL
      await this.executeSQL(migration.rollbackSql);

      migration.status = 'rolled_back';
      migration.rolledBackAt = Date.now();

      await this.recordMigration(migration);

      this.emit('rollbackComplete', migration);
    } catch (error) {
      throw new Error(`Rollback failed for ${migration.id}: ${error}`);
    }
  }

  /**
   * Get migration status
   */
  async status(): Promise<MigrationStatus> {
    const applied = this.migrations.filter(m => m.status === 'applied');
    const pending = this.migrations.filter(m => m.status === 'pending');
    const failed = this.migrations.filter(m => m.status === 'failed');

    const lastMigration = applied.sort((a, b) =>
      (b.appliedAt || 0) - (a.appliedAt || 0)
    )[0];

    return {
      applied,
      pending,
      failed,
      lastMigration
    };
  }

  /**
   * Generate migration template file
   */
  async generateMigration(name: string, type: 'table' | 'column' | 'index'): Promise<string> {
    const timestamp = Date.now();
    const id = `${timestamp}_${name.replace(/\s+/g, '_').toLowerCase()}`;
    const filename = `${id}.sql`;
    const filepath = path.join(this.config.migrationsDir!, filename);

    let template = '';

    switch (type) {
      case 'table':
        template = `-- Migration: Create ${name}
-- Generated: ${new Date().toISOString()}

-- Forward migration
CREATE TABLE ${name} (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rollback
-- DROP TABLE IF EXISTS ${name};
`;
        break;

      case 'column':
        template = `-- Migration: Add column ${name}
-- Generated: ${new Date().toISOString()}

-- Forward migration
-- ALTER TABLE table_name ADD COLUMN ${name} VARCHAR(255);

-- Rollback
-- ALTER TABLE table_name DROP COLUMN ${name};
`;
        break;

      case 'index':
        template = `-- Migration: Create index ${name}
-- Generated: ${new Date().toISOString()}

-- Forward migration
-- CREATE INDEX ${name} ON table_name (column_name);

-- Rollback
-- DROP INDEX IF EXISTS ${name};
`;
        break;
    }

    await fs.writeFile(filepath, template, 'utf-8');

    return filepath;
  }

  /**
   * Execute migration in transaction
   */
  private async executeInTransaction(migration: Migration, _options: MigrationOptions): Promise<void> {
    // Begin transaction
    await this.executeSQL('BEGIN;');

    try {
      await this.executeSQL(migration.sql);

      // Commit transaction
      await this.executeSQL('COMMIT;');
    } catch (error) {
      // Rollback transaction
      await this.executeSQL('ROLLBACK;');
      throw error;
    }
  }

  /**
   * Execute migration directly without transaction
   */
  private async executeDirectly(migration: Migration, _options: MigrationOptions): Promise<void> {
    await this.executeSQL(migration.sql);
  }

  /**
   * Execute SQL statement
   */
  private async executeSQL(sql: string): Promise<void> {
    // This would use the actual database connection
    // Placeholder implementation
    console.log('Executing SQL:', sql);
  }

  /**
   * Load migration file
   */
  private async loadMigrationFile(filepath: string): Promise<Migration> {
    const content = await fs.readFile(filepath, 'utf-8');

    // Parse migration file
    // Format: SQL comments with forward and rollback sections
    const forwardMatch = content.match(/-- Forward migration\n([\s\S]*?)(?:-- Rollback|$)/);
    const rollbackMatch = content.match(/-- Rollback\n([\s\S]*?)$/);

    const sql = forwardMatch ? forwardMatch[1].trim() : content;
    const rollbackSql = rollbackMatch ? rollbackMatch[1].trim() : '';

    const basename = path.basename(filepath, '.sql');
    const parts = basename.split('_');
    const id = parts[0];
    const name = parts.slice(1).join('_');

    return {
      id,
      name,
      sql,
      rollbackSql: rollbackSql.startsWith('--') ? '' : rollbackSql,
      status: 'pending'
    };
  }

  /**
   * Record migration in tracking table and state
   */
  private async recordMigration(migration: Migration): Promise<void> {
    // Update in-memory list
    const index = this.migrations.findIndex(m => m.id === migration.id);
    if (index >= 0) {
      this.migrations[index] = migration;
    } else {
      this.migrations.push(migration);
    }

    // Save to state manager
    this.stateManager.set(`migration:${migration.id}`, migration);
    await this.stateManager.save();

    // Insert/update in tracking table
    // This would execute SQL to update the tracking table
  }

  /**
   * Load migration history from state
   */
  private async loadMigrationHistory(): Promise<void> {
    const migrationKeys = this.stateManager.keys().filter(k => k.startsWith('migration:'));

    this.migrations = migrationKeys.map(key => this.stateManager.get(key)).filter(Boolean);
  }

  /**
   * Generate unique migration ID
   */
  private generateMigrationId(): string {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}
