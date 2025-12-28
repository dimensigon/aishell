/**
 * MySQL Command Registration
 * Registers MySQL CLI commands with the command framework
 */

import { Command } from 'commander';
import { MySQLCLI, MySQLConnectOptions, MySQLQueryOptions, MySQLExportOptions, MySQLImportOptions } from './mysql-cli';
import { StateManager } from '../core/state-manager';
import { DatabaseConnectionManager } from './db-connection-manager';
import chalk from 'chalk';

/**
 * Register MySQL commands
 */
export function registerMySQLCommands(program: Command): void {
  const stateManager = new StateManager();
  const dbManager = new DatabaseConnectionManager(stateManager);
  const mysqlCLI = new MySQLCLI(stateManager, dbManager);

  const mysql = program
    .command('mysql')
    .description('MySQL database operations and management');

  // Command 1: mysql connect
  mysql
    .command('connect <connection-string>')
    .description('Connect to MySQL database')
    .option('-n, --name <name>', 'Connection name (default: auto-generated)')
    .option('-h, --host <host>', 'Database host')
    .option('-p, --port <port>', 'Database port', '3306')
    .option('-d, --database <database>', 'Database name')
    .option('-u, --username <username>', 'Username')
    .option('-P, --password <password>', 'Password')
    .option('--ssl', 'Enable SSL/TLS connection')
    .option('--pool-size <size>', 'Connection pool size', '10')
    .action(async (connectionString: string, options: any) => {
      try {
        const connectOptions: MySQLConnectOptions = {
          name: options.name,
          host: options.host,
          port: options.port ? parseInt(options.port) : undefined,
          database: options.database,
          username: options.username,
          password: options.password,
          ssl: options.ssl,
          poolSize: options.poolSize ? parseInt(options.poolSize) : undefined
        };

        await mysqlCLI.connect(connectionString, connectOptions);
      } catch (error) {
        console.error(chalk.red('Error:'), error instanceof Error ? error.message : String(error));
        process.exit(1);
      }
    });

  // Command 2: mysql disconnect
  mysql
    .command('disconnect [name]')
    .description('Disconnect from MySQL database')
    .action(async (name?: string) => {
      try {
        await mysqlCLI.disconnect(name);
      } catch (error) {
        console.error(chalk.red('Error:'), error instanceof Error ? error.message : String(error));
        process.exit(1);
      }
    });

  // Command 3: mysql query
  mysql
    .command('query <sql>')
    .description('Execute SQL query')
    .option('-f, --format <format>', 'Output format (json|table|csv)', 'table')
    .option('-o, --output <file>', 'Output file path')
    .option('-l, --limit <limit>', 'Limit number of results')
    .option('-t, --timeout <timeout>', 'Query timeout in milliseconds')
    .option('-e, --explain', 'Show query execution plan')
    .action(async (sql: string, options: any) => {
      try {
        const queryOptions: MySQLQueryOptions = {
          format: options.format,
          output: options.output,
          limit: options.limit ? parseInt(options.limit) : undefined,
          timeout: options.timeout ? parseInt(options.timeout) : undefined,
          explain: options.explain
        };

        await mysqlCLI.query(sql, queryOptions);
      } catch (error) {
        console.error(chalk.red('Error:'), error instanceof Error ? error.message : String(error));
        process.exit(1);
      }
    });

  // Command 4: mysql status
  mysql
    .command('status')
    .description('Show MySQL connection status and statistics')
    .action(async () => {
      try {
        await mysqlCLI.status();
      } catch (error) {
        console.error(chalk.red('Error:'), error instanceof Error ? error.message : String(error));
        process.exit(1);
      }
    });

  // Command 5: mysql tables
  mysql
    .command('tables [database]')
    .description('List tables in database')
    .action(async (database?: string) => {
      try {
        await mysqlCLI.tables(database);
      } catch (error) {
        console.error(chalk.red('Error:'), error instanceof Error ? error.message : String(error));
        process.exit(1);
      }
    });

  // Command 6: mysql describe
  mysql
    .command('describe <table>')
    .description('Show table structure and indexes')
    .alias('desc')
    .action(async (table: string) => {
      try {
        await mysqlCLI.describe(table);
      } catch (error) {
        console.error(chalk.red('Error:'), error instanceof Error ? error.message : String(error));
        process.exit(1);
      }
    });

  // Command 7: mysql import
  mysql
    .command('import <file>')
    .description('Import data from file (SQL, CSV, JSON)')
    .option('-t, --table <table>', 'Target table name (required for CSV/JSON)')
    .option('-f, --format <format>', 'File format (sql|csv|json)', 'auto')
    .option('--truncate', 'Truncate table before import')
    .option('-b, --batch-size <size>', 'Batch size for inserts', '1000')
    .action(async (file: string, options: any) => {
      try {
        const importOptions: MySQLImportOptions = {
          table: options.table,
          format: options.format === 'auto' ? undefined : options.format,
          truncate: options.truncate,
          batchSize: options.batchSize ? parseInt(options.batchSize) : undefined
        };

        await mysqlCLI.import(file, importOptions);
      } catch (error) {
        console.error(chalk.red('Error:'), error instanceof Error ? error.message : String(error));
        process.exit(1);
      }
    });

  // Command 8: mysql export
  mysql
    .command('export <table>')
    .description('Export table data to file')
    .option('-f, --format <format>', 'Export format (sql|csv|json)', 'json')
    .option('-o, --output <file>', 'Output file path')
    .option('-w, --where <condition>', 'WHERE clause condition')
    .option('-l, --limit <limit>', 'Limit number of rows')
    .option('-c, --columns <columns>', 'Comma-separated column names')
    .action(async (table: string, options: any) => {
      try {
        const exportOptions: MySQLExportOptions = {
          format: options.format,
          output: options.output,
          where: options.where,
          limit: options.limit ? parseInt(options.limit) : undefined,
          columns: options.columns ? options.columns.split(',').map((c: string) => c.trim()) : undefined
        };

        await mysqlCLI.export(table, exportOptions);
      } catch (error) {
        console.error(chalk.red('Error:'), error instanceof Error ? error.message : String(error));
        process.exit(1);
      }
    });
}

/**
 * Example usage:
 *
 * # Connect to MySQL
 * ai-shell mysql connect "mysql://root:password@localhost:3306/mydb"
 * ai-shell mysql connect "host=localhost;database=mydb;user=root;password=secret" --name prod
 *
 * # Execute queries
 * ai-shell mysql query "SELECT * FROM users LIMIT 10" --format table
 * ai-shell mysql query "SELECT * FROM users" --format json --output users.json
 * ai-shell mysql query "SELECT * FROM orders" --explain
 *
 * # Show status
 * ai-shell mysql status
 *
 * # List tables
 * ai-shell mysql tables
 * ai-shell mysql tables mydb
 *
 * # Describe table
 * ai-shell mysql describe users
 *
 * # Import data
 * ai-shell mysql import data.sql
 * ai-shell mysql import users.csv --table users --truncate
 * ai-shell mysql import products.json --table products --batch-size 500
 *
 * # Export data
 * ai-shell mysql export users --format json --output users.json
 * ai-shell mysql export orders --format csv --where "created_at > '2024-01-01'" --limit 1000
 * ai-shell mysql export products --format sql --columns "id,name,price"
 *
 * # Disconnect
 * ai-shell mysql disconnect
 * ai-shell mysql disconnect prod
 */

export default registerMySQLCommands;
