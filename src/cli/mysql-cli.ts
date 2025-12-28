/**
 * MySQL CLI Commands
 * Provides comprehensive MySQL database operations via command-line interface
 *
 * Features:
 * - Connection management with pooling
 * - Query execution with multiple output formats
 * - Schema exploration (tables, describe)
 * - Data import/export (SQL, CSV, JSON)
 * - Connection monitoring and status
 *
 * Commands:
 * 1. mysql connect <connection-string> - Connect to MySQL database
 * 2. mysql disconnect [name] - Disconnect from database
 * 3. mysql query <sql> - Execute SQL query
 * 4. mysql status - Show connection status
 * 5. mysql tables [database] - List tables in database
 * 6. mysql describe <table> - Show table structure
 * 7. mysql import <file> - Import data from file
 * 8. mysql export <table> [options] - Export table data
 */

import chalk from 'chalk';
import Table from 'cli-table3';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';
import { DatabaseConnectionManager, DatabaseType, ConnectionConfig } from './db-connection-manager';
import { ResultFormatter, TableFormatter, CSVFormatter, JSONFormatter } from './formatters';
import { Pool as MySqlPool } from 'mysql2/promise';
import * as fs from 'fs/promises';
import * as path from 'path';
import { parse as parseCSV } from 'csv-parse/sync';

const logger = createLogger('MySQLCLI');

/**
 * MySQL connection options
 */
export interface MySQLConnectOptions {
  name?: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  ssl?: boolean;
  poolSize?: number;
}

/**
 * MySQL query options
 */
export interface MySQLQueryOptions {
  format?: 'json' | 'table' | 'csv';
  output?: string;
  limit?: number;
  timeout?: number;
  explain?: boolean;
}

/**
 * MySQL export options
 */
export interface MySQLExportOptions {
  format?: 'sql' | 'csv' | 'json';
  output?: string;
  where?: string;
  limit?: number;
  columns?: string[];
}

/**
 * MySQL import options
 */
export interface MySQLImportOptions {
  table?: string;
  format?: 'sql' | 'csv' | 'json';
  truncate?: boolean;
  batchSize?: number;
}

/**
 * Table info interface
 */
export interface TableInfo {
  name: string;
  engine: string;
  rows: number;
  dataLength: number;
  indexLength: number;
  autoIncrement: number | null;
  createTime: Date;
  updateTime: Date | null;
  collation: string;
}

/**
 * Column info interface
 */
export interface ColumnInfo {
  field: string;
  type: string;
  null: string;
  key: string;
  default: any;
  extra: string;
}

/**
 * Connection status interface
 */
export interface ConnectionStatus {
  name: string;
  connected: boolean;
  database: string;
  host: string;
  port: number;
  uptime: number;
  activeConnections: number;
  maxConnections: number;
  version: string;
}

/**
 * MySQL CLI Implementation
 */
export class MySQLCLI {
  private logger = createLogger('MySQLCLI');
  private stateManager: StateManager;
  private dbManager: DatabaseConnectionManager;

  constructor(
    stateManager?: StateManager,
    dbManager?: DatabaseConnectionManager
  ) {
    this.stateManager = stateManager || new StateManager();
    this.dbManager = dbManager || new DatabaseConnectionManager(this.stateManager);
  }

  /**
   * Connect to MySQL database
   */
  async connect(connectionString: string, options: MySQLConnectOptions = {}): Promise<void> {
    try {
      this.logger.info('Connecting to MySQL database', { connectionString: this.maskConnectionString(connectionString) });

      // Parse connection string or use options
      const config = this.parseConnectionString(connectionString, options);

      // Connect to database
      const connection = await this.dbManager.connect(config);

      // Test connection and get version
      const pool = connection.client as MySqlPool;
      const [rows] = await pool.query('SELECT VERSION() as version');
      const version = Array.isArray(rows) && rows.length > 0 ? (rows[0] as any).version : 'Unknown';

      console.log(chalk.green('\n✅ Successfully connected to MySQL database\n'));
      console.log(chalk.bold('Connection Details:'));
      console.log(chalk.dim(`  Name: ${config.name}`));
      console.log(chalk.dim(`  Host: ${config.host}:${config.port}`));
      console.log(chalk.dim(`  Database: ${config.database}`));
      console.log(chalk.dim(`  Version: ${version}`));
      console.log(chalk.dim(`  Pool Size: ${config.poolSize || 10}`));

    } catch (error) {
      this.logger.error('Failed to connect to MySQL', error);
      console.log(chalk.red('\n❌ Connection failed:'), error instanceof Error ? error.message : String(error));
      throw error;
    }
  }

  /**
   * Disconnect from MySQL database
   */
  async disconnect(name?: string): Promise<void> {
    try {
      if (name) {
        // Disconnect specific connection
        await this.dbManager.disconnect(name);
        console.log(chalk.green(`\n✅ Disconnected from: ${name}\n`));
      } else {
        // Disconnect all connections
        const connections = this.dbManager.listConnections();
        if (connections.length === 0) {
          console.log(chalk.yellow('\n⚠️  No active connections\n'));
          return;
        }

        await this.dbManager.disconnectAll();
        console.log(chalk.green(`\n✅ Disconnected from ${connections.length} connection(s)\n`));
      }

      this.logger.info('Disconnected from MySQL', { name });
    } catch (error) {
      this.logger.error('Failed to disconnect', error);
      console.log(chalk.red('\n❌ Disconnect failed:'), error instanceof Error ? error.message : String(error));
      throw error;
    }
  }

  /**
   * Execute SQL query
   */
  async query(sql: string, options: MySQLQueryOptions = {}): Promise<any[]> {
    try {
      this.logger.info('Executing MySQL query', { sql: sql.substring(0, 100), options });

      const connection = this.dbManager.getActive();
      if (!connection) {
        throw new Error('No active MySQL connection. Use "mysql connect" first.');
      }

      if (connection.type !== DatabaseType.MYSQL) {
        throw new Error(`Active connection is not MySQL: ${connection.type}`);
      }

      const pool = connection.client as MySqlPool;

      // Get execution plan if explain flag is set
      if (options.explain) {
        await this.explainQuery(sql, pool);
      }

      // Execute query with timeout
      const queryOptions: any = {};
      if (options.timeout) {
        queryOptions.timeout = options.timeout;
      }

      const startTime = Date.now();
      const [rows] = await pool.query(sql);
      const executionTime = Date.now() - startTime;

      // Handle non-SELECT queries
      if (!Array.isArray(rows)) {
        const result = rows as any;
        console.log(chalk.green('\n✅ Query executed successfully\n'));
        console.log(chalk.dim(`  Affected Rows: ${result.affectedRows || 0}`));
        console.log(chalk.dim(`  Execution Time: ${executionTime}ms`));

        if (result.insertId) {
          console.log(chalk.dim(`  Insert ID: ${result.insertId}`));
        }

        return [];
      }

      // Limit results if specified
      let results = rows as any[];
      if (options.limit && results.length > options.limit) {
        results = results.slice(0, options.limit);
        console.log(chalk.yellow(`\n⚠️  Results limited to ${options.limit} rows\n`));
      }

      // Display results
      const format = options.format || 'table';
      await this.displayResults(results, format, executionTime);

      // Export to file if requested
      if (options.output) {
        await this.exportToFile(results, options.output, format);
      }

      return results;

    } catch (error) {
      this.logger.error('Query execution failed', error);
      console.log(chalk.red('\n❌ Query failed:'), error instanceof Error ? error.message : String(error));
      throw error;
    }
  }

  /**
   * Show connection status
   */
  async status(): Promise<ConnectionStatus | null> {
    try {
      const connection = this.dbManager.getActive();

      if (!connection) {
        console.log(chalk.yellow('\n⚠️  No active MySQL connection\n'));

        // Show all connections
        const connections = this.dbManager.listConnections();
        if (connections.length > 0) {
          console.log(chalk.bold('Available Connections:\n'));

          const table = new Table({
            head: ['Name', 'Database', 'Host', 'Type', 'Status'],
            colWidths: [20, 20, 30, 15, 15]
          });

          for (const conn of connections) {
            table.push([
              conn.name,
              conn.database,
              `${conn.host}:${conn.port}`,
              conn.type,
              conn.isActive ? chalk.green('Active') : chalk.dim('Inactive')
            ]);
          }

          console.log(table.toString());
        }

        return null;
      }

      if (connection.type !== DatabaseType.MYSQL) {
        throw new Error(`Active connection is not MySQL: ${connection.type}`);
      }

      const pool = connection.client as MySqlPool;

      // Get MySQL status variables
      const [statusRows] = await pool.query(`SHOW STATUS WHERE Variable_name IN ('Uptime', 'Threads_connected', 'Max_used_connections')`);
      const [variableRows] = await pool.query(`SHOW VARIABLES WHERE Variable_name IN ('max_connections', 'version')`);
      const [databaseRows] = await pool.query(`SELECT DATABASE() as current_db`);

      // Parse status
      const statusMap = new Map();
      (statusRows as any[]).forEach((row: any) => {
        statusMap.set(row.Variable_name, row.Value);
      });

      const variableMap = new Map();
      (variableRows as any[]).forEach((row: any) => {
        variableMap.set(row.Variable_name, row.Value);
      });

      const currentDb = Array.isArray(databaseRows) && databaseRows.length > 0
        ? (databaseRows[0] as any).current_db
        : connection.config.database;

      const status: ConnectionStatus = {
        name: connection.config.name,
        connected: true,
        database: currentDb,
        host: connection.config.host || 'localhost',
        port: connection.config.port || 3306,
        uptime: parseInt(statusMap.get('Uptime') || '0'),
        activeConnections: parseInt(statusMap.get('Threads_connected') || '0'),
        maxConnections: parseInt(variableMap.get('max_connections') || '0'),
        version: variableMap.get('version') || 'Unknown'
      };

      // Display status
      console.log(chalk.bold('\n📊 MySQL Connection Status\n'));

      const table = new Table({
        head: ['Property', 'Value'],
        colWidths: [25, 55]
      });

      table.push(
        ['Connection Name', chalk.green(status.name)],
        ['Status', chalk.green('Connected')],
        ['Database', status.database],
        ['Host', `${status.host}:${status.port}`],
        ['Version', status.version],
        ['Uptime', this.formatUptime(status.uptime)],
        ['Active Connections', `${status.activeConnections}/${status.maxConnections}`]
      );

      console.log(table.toString());

      return status;

    } catch (error) {
      this.logger.error('Failed to get status', error);
      console.log(chalk.red('\n❌ Status check failed:'), error instanceof Error ? error.message : String(error));
      throw error;
    }
  }

  /**
   * List tables in database
   */
  async tables(database?: string): Promise<TableInfo[]> {
    try {
      const connection = this.dbManager.getActive();
      if (!connection) {
        throw new Error('No active MySQL connection');
      }

      if (connection.type !== DatabaseType.MYSQL) {
        throw new Error(`Active connection is not MySQL: ${connection.type}`);
      }

      const pool = connection.client as MySqlPool;

      // Switch database if specified
      if (database) {
        await pool.query(`USE ${pool.escapeId(database)}`);
      }

      // Get table status
      const [rows] = await pool.query('SHOW TABLE STATUS');
      const tables = (rows as any[]).map(row => ({
        name: row.Name,
        engine: row.Engine,
        rows: row.Rows,
        dataLength: row.Data_length,
        indexLength: row.Index_length,
        autoIncrement: row.Auto_increment,
        createTime: row.Create_time,
        updateTime: row.Update_time,
        collation: row.Collation
      }));

      // Display tables
      console.log(chalk.bold(`\n📋 Tables in ${database || connection.config.database}\n`));

      const table = new Table({
        head: ['Table', 'Engine', 'Rows', 'Data Size', 'Index Size', 'Created'],
        colWidths: [30, 12, 12, 15, 15, 25]
      });

      for (const tbl of tables) {
        table.push([
          tbl.name,
          tbl.engine,
          tbl.rows.toLocaleString(),
          this.formatBytes(tbl.dataLength),
          this.formatBytes(tbl.indexLength),
          tbl.createTime.toLocaleDateString()
        ]);
      }

      console.log(table.toString());
      console.log(chalk.dim(`\nTotal tables: ${tables.length}`));

      return tables;

    } catch (error) {
      this.logger.error('Failed to list tables', error);
      console.log(chalk.red('\n❌ Failed to list tables:'), error instanceof Error ? error.message : String(error));
      throw error;
    }
  }

  /**
   * Describe table structure
   */
  async describe(tableName: string): Promise<ColumnInfo[]> {
    try {
      const connection = this.dbManager.getActive();
      if (!connection) {
        throw new Error('No active MySQL connection');
      }

      if (connection.type !== DatabaseType.MYSQL) {
        throw new Error(`Active connection is not MySQL: ${connection.type}`);
      }

      const pool = connection.client as MySqlPool;

      // Get table structure
      const [rows] = await pool.query(`DESCRIBE ${pool.escapeId(tableName)}`);
      const columns = (rows as any[]).map(row => ({
        field: row.Field,
        type: row.Type,
        null: row.Null,
        key: row.Key,
        default: row.Default,
        extra: row.Extra
      }));

      // Get additional table info
      const [createRows] = await pool.query(`SHOW CREATE TABLE ${pool.escapeId(tableName)}`);
      const createStatement = Array.isArray(createRows) && createRows.length > 0
        ? (createRows[0] as any)['Create Table']
        : '';

      // Display table structure
      console.log(chalk.bold(`\n📐 Table Structure: ${tableName}\n`));

      const table = new Table({
        head: ['Field', 'Type', 'Null', 'Key', 'Default', 'Extra'],
        colWidths: [25, 20, 8, 8, 15, 20]
      });

      for (const col of columns) {
        table.push([
          col.key === 'PRI' ? chalk.yellow(col.field) : col.field,
          col.type,
          col.null === 'YES' ? chalk.dim('YES') : chalk.green('NO'),
          col.key ? chalk.cyan(col.key) : '',
          col.default !== null ? String(col.default) : chalk.dim('NULL'),
          col.extra ? chalk.dim(col.extra) : ''
        ]);
      }

      console.log(table.toString());

      // Show indexes
      const [indexRows] = await pool.query(`SHOW INDEX FROM ${pool.escapeId(tableName)}`);
      if (Array.isArray(indexRows) && indexRows.length > 0) {
        console.log(chalk.bold('\n📑 Indexes:\n'));

        const indexTable = new Table({
          head: ['Key Name', 'Column', 'Type', 'Unique'],
          colWidths: [25, 25, 15, 10]
        });

        (indexRows as any[]).forEach(idx => {
          indexTable.push([
            idx.Key_name === 'PRIMARY' ? chalk.yellow(idx.Key_name) : idx.Key_name,
            idx.Column_name,
            idx.Index_type,
            idx.Non_unique === 0 ? chalk.green('YES') : chalk.dim('NO')
          ]);
        });

        console.log(indexTable.toString());
      }

      return columns;

    } catch (error) {
      this.logger.error('Failed to describe table', error);
      console.log(chalk.red('\n❌ Failed to describe table:'), error instanceof Error ? error.message : String(error));
      throw error;
    }
  }

  /**
   * Import data from file
   */
  async import(filePath: string, options: MySQLImportOptions = {}): Promise<number> {
    try {
      this.logger.info('Importing data', { filePath, options });

      const connection = this.dbManager.getActive();
      if (!connection) {
        throw new Error('No active MySQL connection');
      }

      if (connection.type !== DatabaseType.MYSQL) {
        throw new Error(`Active connection is not MySQL: ${connection.type}`);
      }

      const pool = connection.client as MySqlPool;

      // Read file
      const fileContent = await fs.readFile(filePath, 'utf-8');
      const ext = path.extname(filePath).toLowerCase();
      const format = options.format || this.detectFormat(ext);

      let importedRows = 0;

      console.log(chalk.blue(`\n📥 Importing data from: ${filePath}\n`));
      console.log(chalk.dim(`  Format: ${format}`));

      if (format === 'sql') {
        // Execute SQL file
        const statements = this.splitSqlStatements(fileContent);

        for (const statement of statements) {
          if (statement.trim()) {
            await pool.query(statement);
          }
        }

        importedRows = statements.length;

      } else if (format === 'csv') {
        // Import CSV
        if (!options.table) {
          throw new Error('Table name required for CSV import');
        }

        // Truncate table if requested
        if (options.truncate) {
          await pool.query(`TRUNCATE TABLE ${pool.escapeId(options.table)}`);
          console.log(chalk.yellow(`  Truncated table: ${options.table}`));
        }

        // Parse CSV
        const records = parseCSV(fileContent, {
          columns: true,
          skip_empty_lines: true
        });

        // Batch insert
        const batchSize = options.batchSize || 1000;
        const batches = this.createBatches(records, batchSize);

        for (let i = 0; i < batches.length; i++) {
          const batch = batches[i];
          const values = batch.map(record => Object.values(record as any));
          const columns = Object.keys(batch[0] as any);

          const placeholders = batch.map(() => `(${columns.map(() => '?').join(', ')})`).join(', ');
          const sql = `INSERT INTO ${pool.escapeId(options.table)} (${columns.map(c => pool.escapeId(c)).join(', ')}) VALUES ${placeholders}`;

          await pool.query(sql, values.flat());
          importedRows += batch.length;

          console.log(chalk.dim(`  Progress: ${importedRows}/${records.length} rows`));
        }

      } else if (format === 'json') {
        // Import JSON
        if (!options.table) {
          throw new Error('Table name required for JSON import');
        }

        // Truncate table if requested
        if (options.truncate) {
          await pool.query(`TRUNCATE TABLE ${pool.escapeId(options.table)}`);
        }

        const data = JSON.parse(fileContent);
        const records = Array.isArray(data) ? data : [data];

        // Batch insert
        const batchSize = options.batchSize || 1000;
        const batches = this.createBatches(records, batchSize);

        for (const batch of batches) {
          const values = batch.map(record => Object.values(record));
          const columns = Object.keys(batch[0]);

          const placeholders = batch.map(() => `(${columns.map(() => '?').join(', ')})`).join(', ');
          const sql = `INSERT INTO ${pool.escapeId(options.table)} (${columns.map(c => pool.escapeId(c)).join(', ')}) VALUES ${placeholders}`;

          await pool.query(sql, values.flat());
          importedRows += batch.length;
        }
      }

      console.log(chalk.green(`\n✅ Import completed: ${importedRows} rows imported\n`));

      return importedRows;

    } catch (error) {
      this.logger.error('Import failed', error);
      console.log(chalk.red('\n❌ Import failed:'), error instanceof Error ? error.message : String(error));
      throw error;
    }
  }

  /**
   * Export table data
   */
  async export(tableName: string, options: MySQLExportOptions = {}): Promise<string> {
    try {
      this.logger.info('Exporting data', { tableName, options });

      const connection = this.dbManager.getActive();
      if (!connection) {
        throw new Error('No active MySQL connection');
      }

      if (connection.type !== DatabaseType.MYSQL) {
        throw new Error(`Active connection is not MySQL: ${connection.type}`);
      }

      const pool = connection.client as MySqlPool;

      // Build query
      let sql = `SELECT `;
      if (options.columns && options.columns.length > 0) {
        sql += options.columns.map(c => pool.escapeId(c)).join(', ');
      } else {
        sql += '*';
      }
      sql += ` FROM ${pool.escapeId(tableName)}`;

      if (options.where) {
        sql += ` WHERE ${options.where}`;
      }

      if (options.limit) {
        sql += ` LIMIT ${options.limit}`;
      }

      console.log(chalk.blue(`\n📤 Exporting data from: ${tableName}\n`));

      // Execute query
      const [rows] = await pool.query(sql);
      const data = rows as any[];

      // Export based on format
      const format = options.format || 'json';
      let output = '';

      if (format === 'json') {
        output = JSONFormatter.format(data, true);
      } else if (format === 'csv') {
        const csvFormatter = new CSVFormatter();
        output = csvFormatter.format(data);
      } else if (format === 'sql') {
        // Generate INSERT statements
        const columns = Object.keys(data[0] || {});
        const statements = data.map(row => {
          const values = columns.map(col => {
            const val = row[col];
            if (val === null) return 'NULL';
            if (typeof val === 'number') return val;
            return `'${String(val).replace(/'/g, "''")}'`;
          }).join(', ');
          return `INSERT INTO ${pool.escapeId(tableName)} (${columns.map(c => pool.escapeId(c)).join(', ')}) VALUES (${values});`;
        });
        output = statements.join('\n');
      }

      // Save to file if output path specified
      if (options.output) {
        await fs.writeFile(options.output, output, 'utf-8');
        console.log(chalk.green(`✅ Exported ${data.length} rows to: ${options.output}\n`));
      } else {
        console.log(output);
        console.log(chalk.dim(`\nExported ${data.length} rows`));
      }

      return output;

    } catch (error) {
      this.logger.error('Export failed', error);
      console.log(chalk.red('\n❌ Export failed:'), error instanceof Error ? error.message : String(error));
      throw error;
    }
  }

  // Private helper methods

  /**
   * Parse MySQL connection string
   */
  private parseConnectionString(connectionString: string, options: MySQLConnectOptions): ConnectionConfig {
    // Support both connection string and options
    if (connectionString.startsWith('mysql://')) {
      const url = new URL(connectionString);

      return {
        name: options.name || `mysql_${Date.now()}`,
        type: DatabaseType.MYSQL,
        host: url.hostname,
        port: parseInt(url.port) || 3306,
        database: url.pathname.substring(1),
        username: url.username,
        password: url.password,
        ssl: options.ssl,
        poolSize: options.poolSize || 10
      };
    }

    // Parse key=value format: "host=localhost;database=mydb;user=root;password=secret"
    const parts = connectionString.split(';');
    const parsed: any = {};

    for (const part of parts) {
      const [key, value] = part.split('=').map(s => s.trim());
      if (key && value) {
        parsed[key] = value;
      }
    }

    return {
      name: options.name || parsed.name || `mysql_${Date.now()}`,
      type: DatabaseType.MYSQL,
      host: options.host || parsed.host || 'localhost',
      port: options.port || parseInt(parsed.port) || 3306,
      database: options.database || parsed.database || parsed.db || '',
      username: options.username || parsed.user || parsed.username || 'root',
      password: options.password || parsed.password || '',
      ssl: options.ssl !== undefined ? options.ssl : parsed.ssl === 'true',
      poolSize: options.poolSize || parseInt(parsed.poolSize) || 10
    };
  }

  /**
   * Mask sensitive connection string information
   */
  private maskConnectionString(connectionString: string): string {
    return connectionString.replace(/password=[^;]+/gi, 'password=***');
  }

  /**
   * Display query results
   */
  private async displayResults(results: any[], format: string, executionTime: number): Promise<void> {
    if (results.length === 0) {
      console.log(chalk.yellow('\n⚠️  No results found\n'));
      console.log(chalk.dim(`  Execution Time: ${executionTime}ms`));
      return;
    }

    console.log(chalk.green(`\n✅ Query executed successfully (${results.length} rows, ${executionTime}ms)\n`));

    if (format === 'json') {
      console.log(JSONFormatter.format(results, true));
    } else if (format === 'csv') {
      const csvFormatter = new CSVFormatter();
      console.log(csvFormatter.format(results));
    } else {
      const tableFormatter = new TableFormatter();
      console.log(tableFormatter.format(results));
    }
  }

  /**
   * Explain query execution plan
   */
  private async explainQuery(sql: string, pool: MySqlPool): Promise<void> {
    try {
      const [rows] = await pool.query(`EXPLAIN ${sql}`);

      console.log(chalk.bold('\n📊 Query Execution Plan:\n'));

      const table = new Table({
        head: ['Type', 'Table', 'Possible Keys', 'Key', 'Rows', 'Extra'],
        colWidths: [15, 20, 25, 20, 10, 30]
      });

      (rows as any[]).forEach(row => {
        table.push([
          row.select_type || row.type,
          row.table || '',
          row.possible_keys || chalk.dim('NULL'),
          row.key || chalk.yellow('NULL'),
          row.rows || 0,
          row.Extra ? row.Extra.substring(0, 27) + '...' : ''
        ]);
      });

      console.log(table.toString());
      console.log('');

    } catch (error) {
      this.logger.error('Failed to explain query', error);
      // Non-fatal, continue with query execution
    }
  }

  /**
   * Export results to file
   */
  private async exportToFile(results: any[], outputPath: string, format: string): Promise<void> {
    let content = '';

    if (format === 'json') {
      content = JSONFormatter.format(results, true);
    } else if (format === 'csv') {
      const csvFormatter = new CSVFormatter();
      content = csvFormatter.format(results);
    } else {
      const tableFormatter = new TableFormatter();
      content = tableFormatter.format(results);
    }

    await fs.writeFile(outputPath, content, 'utf-8');
    console.log(chalk.green(`\n✅ Results exported to: ${outputPath}`));
  }

  /**
   * Format uptime in human-readable format
   */
  private formatUptime(seconds: number): string {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);

    return parts.join(' ') || '0m';
  }

  /**
   * Format bytes to human-readable size
   */
  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  }

  /**
   * Detect file format from extension
   */
  private detectFormat(ext: string): 'sql' | 'csv' | 'json' {
    if (ext === '.sql') return 'sql';
    if (ext === '.csv') return 'csv';
    if (ext === '.json') return 'json';
    return 'sql';
  }

  /**
   * Split SQL file into individual statements
   */
  private splitSqlStatements(content: string): string[] {
    // Remove comments
    const cleaned = content
      .replace(/--.*$/gm, '')
      .replace(/\/\*[\s\S]*?\*\//g, '');

    // Split by semicolon
    return cleaned
      .split(';')
      .map(s => s.trim())
      .filter(s => s.length > 0);
  }

  /**
   * Create batches from array
   */
  private createBatches<T>(items: T[], batchSize: number): T[][] {
    const batches: T[][] = [];

    for (let i = 0; i < items.length; i += batchSize) {
      batches.push(items.slice(i, i + batchSize));
    }

    return batches;
  }
}

export default MySQLCLI;
