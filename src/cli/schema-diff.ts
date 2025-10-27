/**
 * Schema Diff Tool
 * Compare schemas and generate sync migrations
 * Commands: ai-shell diff <db1> <db2>, ai-shell sync-schema
 */

import { DatabaseConnectionManager, DatabaseType } from './db-connection-manager';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';
import * as fs from 'fs/promises';

interface SchemaInfo {
  database: string;
  type: DatabaseType;
  tables: TableInfo[];
  indexes: IndexInfo[];
  constraints: ConstraintInfo[];
}

interface TableInfo {
  name: string;
  columns: ColumnInfo[];
}

interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  default?: string;
  isPrimaryKey: boolean;
  isUnique: boolean;
  extra?: string;
}

interface IndexInfo {
  name: string;
  table: string;
  columns: string[];
  unique: boolean;
  type?: string;
}

interface ConstraintInfo {
  name: string;
  table: string;
  type: 'PRIMARY KEY' | 'FOREIGN KEY' | 'UNIQUE' | 'CHECK';
  definition: string;
}

interface TableDifference {
  table: string;
  type: 'added' | 'removed' | 'modified';
  columnChanges?: ColumnChange[];
}

interface ColumnChange {
  column: string;
  type: 'added' | 'removed' | 'modified';
  oldDefinition?: ColumnInfo;
  newDefinition?: ColumnInfo;
}

interface IndexDifference {
  index: string;
  table: string;
  type: 'added' | 'removed' | 'modified';
  oldDefinition?: IndexInfo;
  newDefinition?: IndexInfo;
}

interface ConstraintDifference {
  constraint: string;
  table: string;
  type: 'added' | 'removed' | 'modified';
  oldDefinition?: ConstraintInfo;
  newDefinition?: ConstraintInfo;
}

interface DiffSummary {
  tablesAdded: number;
  tablesRemoved: number;
  tablesModified: number;
  columnsAdded: number;
  columnsRemoved: number;
  columnsModified: number;
  indexesAdded: number;
  indexesRemoved: number;
  constraintsAdded: number;
  constraintsRemoved: number;
}

export interface SchemaDiffResult {
  source: string;
  target: string;
  identical: boolean;
  tableDifferences: TableDifference[];
  indexDifferences: IndexDifference[];
  constraintDifferences: ConstraintDifference[];
  summary: DiffSummary;
}

export class SchemaDiff {
  private logger = createLogger('SchemaDiff');

  constructor(
    private dbManager: DatabaseConnectionManager,
    private _stateManager: StateManager
  ) {}

  /**
   * Compare two database schemas
   */
  async compareSchemas(sourceDb: string, targetDb: string): Promise<SchemaDiffResult> {
    this.logger.info('Comparing schemas', { sourceDb, targetDb });

    try {
      // Get schema information for both databases
      const sourceSchema = await this.getSchemaInfo(sourceDb);
      const targetSchema = await this.getSchemaInfo(targetDb);

      // Compare schemas
      const diff = this.calculateDifferences(sourceSchema, targetSchema);

      this.logger.info('Schema comparison complete', {
        identical: diff.identical,
        tablesChanged: diff.summary.tablesAdded + diff.summary.tablesRemoved + diff.summary.tablesModified
      });

      return diff;
    } catch (error) {
      this.logger.error('Failed to compare schemas', error);
      throw error;
    }
  }

  /**
   * Get schema information for a database
   */
  private async getSchemaInfo(databaseName: string): Promise<SchemaInfo> {
    const connection = this.dbManager.getConnection(databaseName);

    if (!connection) {
      throw new Error(`Database connection not found: ${databaseName}`);
    }

    // Switch to this database
    await this.dbManager.switchActive(databaseName);

    const schema: SchemaInfo = {
      database: databaseName,
      type: connection.type,
      tables: [],
      indexes: [],
      constraints: []
    };

    try {
      switch (connection.type) {
        case DatabaseType.POSTGRESQL:
          await this.getPostgreSQLSchema(schema, connection.client);
          break;

        case DatabaseType.MYSQL:
          await this.getMySQLSchema(schema, connection.client);
          break;

        case DatabaseType.SQLITE:
          await this.getSQLiteSchema(schema, connection.client);
          break;

        default:
          throw new Error(`Unsupported database type: ${connection.type}`);
      }
    } catch (error) {
      this.logger.error('Failed to get schema info', error, { databaseName });
      throw error;
    }

    return schema;
  }

  /**
   * Get PostgreSQL schema
   */
  private async getPostgreSQLSchema(schema: SchemaInfo, client: any): Promise<void> {
    // Get tables and columns
    const tablesResult = await client.query(`
      SELECT
        t.table_name,
        c.column_name,
        c.data_type,
        c.is_nullable,
        c.column_default,
        CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
        CASE WHEN u.column_name IS NOT NULL THEN true ELSE false END as is_unique
      FROM information_schema.tables t
      LEFT JOIN information_schema.columns c
        ON t.table_name = c.table_name
      LEFT JOIN (
        SELECT kcu.column_name, kcu.table_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY'
      ) pk ON c.column_name = pk.column_name AND c.table_name = pk.table_name
      LEFT JOIN (
        SELECT kcu.column_name, kcu.table_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'UNIQUE'
      ) u ON c.column_name = u.column_name AND c.table_name = u.table_name
      WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
      ORDER BY t.table_name, c.ordinal_position
    `);

    schema.tables = this.groupTableColumns(tablesResult.rows);

    // Get indexes
    const indexesResult = await client.query(`
      SELECT
        i.relname as index_name,
        t.relname as table_name,
        ix.indisunique as is_unique,
        array_agg(a.attname ORDER BY a.attnum) as columns
      FROM pg_class t
      JOIN pg_index ix ON t.oid = ix.indrelid
      JOIN pg_class i ON i.oid = ix.indexrelid
      JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
      WHERE t.relkind = 'r'
      GROUP BY i.relname, t.relname, ix.indisunique
    `);

    schema.indexes = indexesResult.rows.map((row: any) => ({
      name: row.index_name,
      table: row.table_name,
      columns: row.columns,
      unique: row.is_unique
    }));
  }

  /**
   * Get MySQL schema
   */
  private async getMySQLSchema(schema: SchemaInfo, client: any): Promise<void> {
    // Get tables and columns
    const [tablesResult] = await client.query(`
      SELECT
        c.TABLE_NAME as table_name,
        c.COLUMN_NAME as column_name,
        c.DATA_TYPE as data_type,
        c.IS_NULLABLE as is_nullable,
        c.COLUMN_DEFAULT as column_default,
        CASE WHEN c.COLUMN_KEY = 'PRI' THEN true ELSE false END as is_primary_key,
        CASE WHEN c.COLUMN_KEY = 'UNI' THEN true ELSE false END as is_unique,
        c.EXTRA as extra
      FROM information_schema.COLUMNS c
      WHERE c.TABLE_SCHEMA = DATABASE()
      ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
    `);

    schema.tables = this.groupTableColumns(tablesResult);

    // Get indexes
    const [indexesResult] = await client.query(`
      SELECT
        INDEX_NAME as index_name,
        TABLE_NAME as table_name,
        NON_UNIQUE as non_unique,
        GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as columns
      FROM information_schema.STATISTICS
      WHERE TABLE_SCHEMA = DATABASE()
      GROUP BY INDEX_NAME, TABLE_NAME, NON_UNIQUE
    `);

    schema.indexes = indexesResult.map((row: any) => ({
      name: row.index_name,
      table: row.table_name,
      columns: row.columns.split(','),
      unique: !row.non_unique
    }));
  }

  /**
   * Get SQLite schema
   */
  private async getSQLiteSchema(schema: SchemaInfo, client: any): Promise<void> {
    return new Promise((resolve, reject) => {
      client.all(
        "SELECT name FROM sqlite_master WHERE type='table'",
        async (err: Error, tables: any[]) => {
          if (err) {
            reject(err);
            return;
          }

          for (const table of tables) {
            await new Promise<void>((resolveTable) => {
              client.all(
                `PRAGMA table_info(${table.name})`,
                (err: Error, columns: any[]) => {
                  if (!err) {
                    schema.tables.push({
                      name: table.name,
                      columns: columns.map((col) => ({
                        name: col.name,
                        type: col.type,
                        nullable: !col.notnull,
                        isPrimaryKey: col.pk === 1,
                        isUnique: false,
                        default: col.dflt_value
                      }))
                    });
                  }
                  resolveTable();
                }
              );
            });
          }

          resolve();
        }
      );
    });
  }

  /**
   * Group columns by table
   */
  private groupTableColumns(rows: any[]): TableInfo[] {
    const tables = new Map<string, TableInfo>();

    rows.forEach((row) => {
      if (!tables.has(row.table_name)) {
        tables.set(row.table_name, {
          name: row.table_name,
          columns: []
        });
      }

      const table = tables.get(row.table_name)!;
      table.columns.push({
        name: row.column_name,
        type: row.data_type,
        nullable: row.is_nullable === 'YES' || row.is_nullable === true,
        default: row.column_default,
        isPrimaryKey: row.is_primary_key === true || row.is_primary_key === 1,
        isUnique: row.is_unique === true || row.is_unique === 1,
        extra: row.extra
      });
    });

    return Array.from(tables.values());
  }

  /**
   * Calculate differences between schemas
   */
  private calculateDifferences(source: SchemaInfo, target: SchemaInfo): SchemaDiffResult {
    const diff: SchemaDiffResult = {
      source: source.database,
      target: target.database,
      identical: true,
      tableDifferences: [],
      indexDifferences: [],
      constraintDifferences: [],
      summary: {
        tablesAdded: 0,
        tablesRemoved: 0,
        tablesModified: 0,
        columnsAdded: 0,
        columnsRemoved: 0,
        columnsModified: 0,
        indexesAdded: 0,
        indexesRemoved: 0,
        constraintsAdded: 0,
        constraintsRemoved: 0
      }
    };

    // Compare tables
    this.compareTables(source.tables, target.tables, diff);

    // Compare indexes
    this.compareIndexes(source.indexes, target.indexes, diff);

    // Update identical flag
    diff.identical = diff.tableDifferences.length === 0 &&
                      diff.indexDifferences.length === 0 &&
                      diff.constraintDifferences.length === 0;

    return diff;
  }

  /**
   * Compare tables
   */
  private compareTables(sourceTables: TableInfo[], targetTables: TableInfo[], diff: {
    tableDifferences: TableDifference[];
    summary: DiffSummary;
  }): void {
    const sourceMap = new Map(sourceTables.map((t) => [t.name, t]));
    const targetMap = new Map(targetTables.map((t) => [t.name, t]));

    // Find added tables
    for (const [name, table] of targetMap) {
      if (!sourceMap.has(name)) {
        diff.tableDifferences.push({
          table: name,
          type: 'added'
        });
        diff.summary.tablesAdded++;
        diff.summary.columnsAdded += table.columns.length;
      }
    }

    // Find removed and modified tables
    for (const [name, sourceTable] of sourceMap) {
      if (!targetMap.has(name)) {
        diff.tableDifferences.push({
          table: name,
          type: 'removed'
        });
        diff.summary.tablesRemoved++;
        diff.summary.columnsRemoved += sourceTable.columns.length;
      } else {
        // Compare columns
        const targetTable = targetMap.get(name)!;
        const columnChanges = this.compareColumns(sourceTable.columns, targetTable.columns);

        if (columnChanges.length > 0) {
          diff.tableDifferences.push({
            table: name,
            type: 'modified',
            columnChanges
          });
          diff.summary.tablesModified++;

          columnChanges.forEach((change) => {
            if (change.type === 'added') diff.summary.columnsAdded++;
            if (change.type === 'removed') diff.summary.columnsRemoved++;
            if (change.type === 'modified') diff.summary.columnsModified++;
          });
        }
      }
    }
  }

  /**
   * Compare columns
   */
  private compareColumns(sourceColumns: ColumnInfo[], targetColumns: ColumnInfo[]): ColumnChange[] {
    const changes: ColumnChange[] = [];
    const sourceMap = new Map(sourceColumns.map((c) => [c.name, c]));
    const targetMap = new Map(targetColumns.map((c) => [c.name, c]));

    // Find added columns
    for (const [name, column] of targetMap) {
      if (!sourceMap.has(name)) {
        changes.push({
          column: name,
          type: 'added',
          newDefinition: column
        });
      }
    }

    // Find removed and modified columns
    for (const [name, sourceColumn] of sourceMap) {
      if (!targetMap.has(name)) {
        changes.push({
          column: name,
          type: 'removed',
          oldDefinition: sourceColumn
        });
      } else {
        const targetColumn = targetMap.get(name)!;

        if (!this.areColumnsEqual(sourceColumn, targetColumn)) {
          changes.push({
            column: name,
            type: 'modified',
            oldDefinition: sourceColumn,
            newDefinition: targetColumn
          });
        }
      }
    }

    return changes;
  }

  /**
   * Check if columns are equal
   */
  private areColumnsEqual(col1: ColumnInfo, col2: ColumnInfo): boolean {
    return (
      col1.type === col2.type &&
      col1.nullable === col2.nullable &&
      col1.default === col2.default &&
      col1.isPrimaryKey === col2.isPrimaryKey &&
      col1.isUnique === col2.isUnique
    );
  }

  /**
   * Compare indexes
   */
  private compareIndexes(sourceIndexes: IndexInfo[], targetIndexes: IndexInfo[], diff: {
    indexDifferences: IndexDifference[];
    summary: DiffSummary;
  }): void {
    const sourceMap = new Map(sourceIndexes.map((i) => [i.name, i]));
    const targetMap = new Map(targetIndexes.map((i) => [i.name, i]));

    // Find added indexes
    for (const [name, index] of targetMap) {
      if (!sourceMap.has(name)) {
        diff.indexDifferences.push({
          index: name,
          table: index.table,
          type: 'added',
          newDefinition: index
        });
        diff.summary.indexesAdded++;
      }
    }

    // Find removed indexes
    for (const [name, index] of sourceMap) {
      if (!targetMap.has(name)) {
        diff.indexDifferences.push({
          index: name,
          table: index.table,
          type: 'removed',
          oldDefinition: index
        });
        diff.summary.indexesRemoved++;
      }
    }
  }

  /**
   * Generate sync migration
   */
  async generateSyncMigration(diff: SchemaDiffResult, targetType: DatabaseType): Promise<string> {
    this.logger.info('Generating sync migration', { targetType });

    let migration = `-- Migration to sync ${diff.source} to ${diff.target}\n\n`;

    // Add tables
    for (const tableDiff of diff.tableDifferences) {
      if (tableDiff.type === 'added') {
        migration += `-- Add table: ${tableDiff.table}\n`;
        migration += `-- TODO: Add CREATE TABLE statement\n\n`;
      } else if (tableDiff.type === 'removed') {
        migration += `DROP TABLE IF EXISTS ${tableDiff.table};\n\n`;
      } else if (tableDiff.type === 'modified' && tableDiff.columnChanges) {
        migration += `-- Modify table: ${tableDiff.table}\n`;

        for (const columnChange of tableDiff.columnChanges) {
          if (columnChange.type === 'added') {
            migration += `ALTER TABLE ${tableDiff.table} ADD COLUMN ${this.formatColumnDefinition(columnChange.newDefinition!, targetType)};\n`;
          } else if (columnChange.type === 'removed') {
            migration += `ALTER TABLE ${tableDiff.table} DROP COLUMN ${columnChange.column};\n`;
          } else if (columnChange.type === 'modified') {
            migration += `ALTER TABLE ${tableDiff.table} MODIFY COLUMN ${this.formatColumnDefinition(columnChange.newDefinition!, targetType)};\n`;
          }
        }

        migration += '\n';
      }
    }

    // Add/remove indexes
    for (const indexDiff of diff.indexDifferences) {
      if (indexDiff.type === 'added' && indexDiff.newDefinition) {
        const unique = indexDiff.newDefinition.unique ? 'UNIQUE ' : '';
        migration += `CREATE ${unique}INDEX ${indexDiff.index} ON ${indexDiff.table} (${indexDiff.newDefinition.columns.join(', ')});\n`;
      } else if (indexDiff.type === 'removed') {
        migration += `DROP INDEX ${indexDiff.index};\n`;
      }
    }

    return migration;
  }

  /**
   * Format column definition for SQL
   */
  private formatColumnDefinition(column: ColumnInfo, _dbType: DatabaseType): string {
    let def = `${column.name} ${column.type}`;

    if (!column.nullable) {
      def += ' NOT NULL';
    }

    if (column.default) {
      def += ` DEFAULT ${column.default}`;
    }

    if (column.isUnique) {
      def += ' UNIQUE';
    }

    return def;
  }

  /**
   * Export diff report
   */
  async exportReport(diff: SchemaDiffResult, outputPath: string): Promise<void> {
    let report = `# Schema Comparison Report\n\n`;
    report += `Source: ${diff.source}\n`;
    report += `Target: ${diff.target}\n`;
    report += `Identical: ${diff.identical}\n\n`;

    report += `## Summary\n\n`;
    report += `- Tables Added: ${diff.summary.tablesAdded}\n`;
    report += `- Tables Removed: ${diff.summary.tablesRemoved}\n`;
    report += `- Tables Modified: ${diff.summary.tablesModified}\n`;
    report += `- Columns Added: ${diff.summary.columnsAdded}\n`;
    report += `- Columns Removed: ${diff.summary.columnsRemoved}\n`;
    report += `- Columns Modified: ${diff.summary.columnsModified}\n`;
    report += `- Indexes Added: ${diff.summary.indexesAdded}\n`;
    report += `- Indexes Removed: ${diff.summary.indexesRemoved}\n\n`;

    report += `## Table Differences\n\n`;
    diff.tableDifferences.forEach((tableDiff) => {
      report += `### ${tableDiff.table} (${tableDiff.type})\n`;

      if (tableDiff.columnChanges) {
        tableDiff.columnChanges.forEach((change) => {
          report += `- Column ${change.column}: ${change.type}\n`;
        });
      }

      report += '\n';
    });

    await fs.writeFile(outputPath, report);

    this.logger.info('Diff report exported', { outputPath });
  }

  /**
   * Apply sync migration
   */
  async applySyncMigration(diff: SchemaDiffResult, targetDb: string): Promise<void> {
    this.logger.info('Applying sync migration', { targetDb });

    const connection = this.dbManager.getConnection(targetDb);
    if (!connection) {
      throw new Error(`Connection not found: ${targetDb}`);
    }

    const migration = await this.generateSyncMigration(diff, connection.type);
    const statements = migration.split(';').filter((s) => s.trim() && !s.trim().startsWith('--'));

    await this.dbManager.switchActive(targetDb);

    for (const statement of statements) {
      try {
        await this.dbManager.executeQuery(statement);
      } catch (error) {
        this.logger.error('Failed to execute statement', error, { statement });
        throw error;
      }
    }

    this.logger.info('Sync migration applied successfully');
  }
}
