/**
 * PostgreSQL Advanced CLI - Advanced PostgreSQL operations
 * Implements vacuum, analyze, reindex, stats, locks, activity, extensions, and partitions
 */

import { Command } from 'commander';
import chalk from 'chalk';
import Table from 'cli-table3';
import { Pool as PgPool } from 'pg';
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { StateManager } from '../core/state-manager';
import { createLogger } from '../core/logger';

const logger = createLogger('PostgresAdvancedCLI');

/**
 * VACUUM operation options
 */
export interface VacuumOptions {
  table?: string;
  full?: boolean;
  freeze?: boolean;
  analyze?: boolean;
  verbose?: boolean;
  skipLocked?: boolean;
  indexCleanup?: boolean;
  truncate?: boolean;
  parallel?: number;
}

/**
 * ANALYZE options
 */
export interface AnalyzeOptions {
  table?: string;
  verbose?: boolean;
  skipLocked?: boolean;
}

/**
 * REINDEX options
 */
export interface ReindexOptions {
  type: 'index' | 'table' | 'database' | 'schema';
  name: string;
  concurrently?: boolean;
  verbose?: boolean;
}

/**
 * Table statistics result
 */
export interface TableStats {
  schemaname: string;
  tablename: string;
  seq_scan: number;
  seq_tup_read: number;
  idx_scan: number;
  idx_tup_fetch: number;
  n_tup_ins: number;
  n_tup_upd: number;
  n_tup_del: number;
  n_live_tup: number;
  n_dead_tup: number;
  last_vacuum: Date | null;
  last_autovacuum: Date | null;
  last_analyze: Date | null;
  last_autoanalyze: Date | null;
  vacuum_count: number;
  autovacuum_count: number;
  analyze_count: number;
  autoanalyze_count: number;
}

/**
 * Lock information
 */
export interface LockInfo {
  locktype: string;
  database: string;
  relation: string;
  page: number | null;
  tuple: number | null;
  virtualxid: string | null;
  transactionid: string | null;
  pid: number;
  mode: string;
  granted: boolean;
  fastpath: boolean;
  waitstart: Date | null;
}

/**
 * Activity information
 */
export interface ActivityInfo {
  pid: number;
  usename: string;
  application_name: string;
  client_addr: string | null;
  client_hostname: string | null;
  client_port: number | null;
  backend_start: Date;
  xact_start: Date | null;
  query_start: Date | null;
  state_change: Date | null;
  wait_event_type: string | null;
  wait_event: string | null;
  state: string;
  backend_xid: string | null;
  backend_xmin: string | null;
  query: string;
  backend_type: string;
}

/**
 * Extension information
 */
export interface ExtensionInfo {
  name: string;
  default_version: string;
  installed_version: string | null;
  comment: string;
}

/**
 * Partition information
 */
export interface PartitionInfo {
  schemaname: string;
  tablename: string;
  partitionname: string;
  partition_expression: string;
  partition_strategy: string;
  partition_start: string | null;
  partition_end: string | null;
  parent_table: string;
}

/**
 * PostgreSQL Advanced CLI - Main class for advanced operations
 */
export class PostgresAdvancedCLI {
  private logger = createLogger('PostgresAdvancedCLI');
  private dbManager: DatabaseConnectionManager;
  private stateManager: StateManager;

  constructor() {
    this.stateManager = new StateManager();
    this.dbManager = new DatabaseConnectionManager(this.stateManager);
  }

  /**
   * Get PostgreSQL connection
   */
  private getConnection(database?: string): PgPool {
    const connection = database
      ? this.dbManager.getConnection(database)
      : this.dbManager.getActive();

    if (!connection) {
      throw new Error('No active PostgreSQL connection. Use "ai-shell connect" first.');
    }

    if (connection.type !== DatabaseType.POSTGRESQL) {
      throw new Error(`Not a PostgreSQL connection. Connected to: ${connection.type}`);
    }

    return connection.client as PgPool;
  }

  /**
   * Execute VACUUM operation
   */
  async vacuum(options: VacuumOptions): Promise<{ success: boolean; message: string; details?: any }> {
    const startTime = Date.now();

    try {
      const pool = this.getConnection();

      // Build VACUUM command with options
      const parts: string[] = ['VACUUM'];
      const opts: string[] = [];

      if (options.full) opts.push('FULL');
      if (options.freeze) opts.push('FREEZE');
      if (options.analyze) opts.push('ANALYZE');
      if (options.verbose) opts.push('VERBOSE');
      if (options.skipLocked) opts.push('SKIP_LOCKED');
      if (options.indexCleanup !== undefined) opts.push(`INDEX_CLEANUP ${options.indexCleanup ? 'ON' : 'OFF'}`);
      if (options.truncate !== undefined) opts.push(`TRUNCATE ${options.truncate ? 'ON' : 'OFF'}`);
      if (options.parallel) opts.push(`PARALLEL ${options.parallel}`);

      if (opts.length > 0) {
        parts.push(`(${opts.join(', ')})`);
      }

      if (options.table) {
        parts.push(options.table);
      }

      const vacuumQuery = parts.join(' ');
      logger.info('Executing VACUUM', { query: vacuumQuery });

      const result = await pool.query(vacuumQuery);

      const duration = Date.now() - startTime;

      return {
        success: true,
        message: `VACUUM completed${options.table ? ` on ${options.table}` : ''} in ${duration}ms`,
        details: options.verbose ? result.rows : undefined
      };
    } catch (error) {
      logger.error('VACUUM failed', error);
      throw error;
    }
  }

  /**
   * Execute ANALYZE operation
   */
  async analyze(options: AnalyzeOptions): Promise<{ success: boolean; message: string; details?: any }> {
    const startTime = Date.now();

    try {
      const pool = this.getConnection();

      // Build ANALYZE command
      const parts: string[] = ['ANALYZE'];
      const opts: string[] = [];

      if (options.verbose) opts.push('VERBOSE');
      if (options.skipLocked) opts.push('SKIP_LOCKED');

      if (opts.length > 0) {
        parts.push(`(${opts.join(', ')})`);
      }

      if (options.table) {
        parts.push(options.table);
      }

      const analyzeQuery = parts.join(' ');
      logger.info('Executing ANALYZE', { query: analyzeQuery });

      const result = await pool.query(analyzeQuery);

      const duration = Date.now() - startTime;

      return {
        success: true,
        message: `ANALYZE completed${options.table ? ` on ${options.table}` : ' on all tables'} in ${duration}ms`,
        details: options.verbose ? result.rows : undefined
      };
    } catch (error) {
      logger.error('ANALYZE failed', error);
      throw error;
    }
  }

  /**
   * Execute REINDEX operation
   */
  async reindex(options: ReindexOptions): Promise<{ success: boolean; message: string }> {
    const startTime = Date.now();

    try {
      const pool = this.getConnection();

      // Build REINDEX command
      const parts: string[] = ['REINDEX'];
      const opts: string[] = [];

      if (options.concurrently) opts.push('CONCURRENTLY');
      if (options.verbose) opts.push('VERBOSE');

      if (opts.length > 0) {
        parts.push(`(${opts.join(', ')})`);
      }

      parts.push(options.type.toUpperCase());
      parts.push(options.name);

      const reindexQuery = parts.join(' ');
      logger.info('Executing REINDEX', { query: reindexQuery });

      await pool.query(reindexQuery);

      const duration = Date.now() - startTime;

      return {
        success: true,
        message: `REINDEX ${options.type.toUpperCase()} ${options.name} completed in ${duration}ms`
      };
    } catch (error) {
      logger.error('REINDEX failed', error);
      throw error;
    }
  }

  /**
   * Get table statistics
   */
  async getTableStats(table?: string, schema: string = 'public'): Promise<TableStats[]> {
    try {
      const pool = this.getConnection();

      let query = `
        SELECT
          schemaname,
          tablename,
          seq_scan,
          seq_tup_read,
          idx_scan,
          idx_tup_fetch,
          n_tup_ins,
          n_tup_upd,
          n_tup_del,
          n_live_tup,
          n_dead_tup,
          last_vacuum,
          last_autovacuum,
          last_analyze,
          last_autoanalyze,
          vacuum_count,
          autovacuum_count,
          analyze_count,
          autoanalyze_count
        FROM pg_stat_user_tables
      `;

      const params: any[] = [];
      const conditions: string[] = [];

      if (table) {
        conditions.push(`tablename = $${params.length + 1}`);
        params.push(table);
      }

      if (schema) {
        conditions.push(`schemaname = $${params.length + 1}`);
        params.push(schema);
      }

      if (conditions.length > 0) {
        query += ` WHERE ${conditions.join(' AND ')}`;
      }

      query += ' ORDER BY schemaname, tablename';

      const result = await pool.query(query, params);

      return result.rows as TableStats[];
    } catch (error) {
      logger.error('Failed to get table stats', error);
      throw error;
    }
  }

  /**
   * Get lock information
   */
  async getLocks(database?: string): Promise<LockInfo[]> {
    try {
      const pool = this.getConnection();

      const query = `
        SELECT
          l.locktype,
          d.datname as database,
          COALESCE(c.relname, l.relation::text) as relation,
          l.page,
          l.tuple,
          l.virtualxid,
          l.transactionid::text,
          l.pid,
          l.mode,
          l.granted,
          l.fastpath,
          a.wait_event_type || ':' || a.wait_event as waitstart
        FROM pg_locks l
        LEFT JOIN pg_database d ON l.database = d.oid
        LEFT JOIN pg_class c ON l.relation = c.oid
        LEFT JOIN pg_stat_activity a ON l.pid = a.pid
        WHERE l.pid != pg_backend_pid()
        ${database ? `AND d.datname = $1` : ''}
        ORDER BY l.granted DESC, l.pid
      `;

      const params = database ? [database] : [];
      const result = await pool.query(query, params);

      return result.rows as LockInfo[];
    } catch (error) {
      logger.error('Failed to get locks', error);
      throw error;
    }
  }

  /**
   * Get activity information
   */
  async getActivity(showAll: boolean = false): Promise<ActivityInfo[]> {
    try {
      const pool = this.getConnection();

      const query = `
        SELECT
          pid,
          usename,
          application_name,
          client_addr::text,
          client_hostname,
          client_port,
          backend_start,
          xact_start,
          query_start,
          state_change,
          wait_event_type,
          wait_event,
          state,
          backend_xid::text,
          backend_xmin::text,
          query,
          backend_type
        FROM pg_stat_activity
        WHERE pid != pg_backend_pid()
        ${showAll ? '' : "AND state != 'idle'"}
        ORDER BY query_start DESC NULLS LAST
      `;

      const result = await pool.query(query);

      return result.rows as ActivityInfo[];
    } catch (error) {
      logger.error('Failed to get activity', error);
      throw error;
    }
  }

  /**
   * List available extensions
   */
  async listExtensions(includeInstalled: boolean = true): Promise<ExtensionInfo[]> {
    try {
      const pool = this.getConnection();

      const query = `
        SELECT
          ae.name,
          ae.default_version,
          e.extversion as installed_version,
          ae.comment
        FROM pg_available_extensions ae
        LEFT JOIN pg_extension e ON ae.name = e.extname
        ${includeInstalled ? '' : 'WHERE e.extname IS NULL'}
        ORDER BY ae.name
      `;

      const result = await pool.query(query);

      return result.rows as ExtensionInfo[];
    } catch (error) {
      logger.error('Failed to list extensions', error);
      throw error;
    }
  }

  /**
   * Enable extension
   */
  async enableExtension(extensionName: string, schema?: string): Promise<{ success: boolean; message: string }> {
    try {
      const pool = this.getConnection();

      let query = `CREATE EXTENSION IF NOT EXISTS "${extensionName}"`;
      if (schema) {
        query += ` SCHEMA ${schema}`;
      }

      await pool.query(query);

      logger.info('Extension enabled', { extension: extensionName, schema });

      return {
        success: true,
        message: `Extension "${extensionName}" enabled successfully`
      };
    } catch (error) {
      logger.error('Failed to enable extension', error);
      throw error;
    }
  }

  /**
   * Disable extension
   */
  async disableExtension(extensionName: string, cascade: boolean = false): Promise<{ success: boolean; message: string }> {
    try {
      const pool = this.getConnection();

      const query = `DROP EXTENSION IF EXISTS "${extensionName}"${cascade ? ' CASCADE' : ''}`;

      await pool.query(query);

      logger.info('Extension disabled', { extension: extensionName, cascade });

      return {
        success: true,
        message: `Extension "${extensionName}" disabled successfully`
      };
    } catch (error) {
      logger.error('Failed to disable extension', error);
      throw error;
    }
  }

  /**
   * Get partition information
   */
  async getPartitions(table: string, schema: string = 'public'): Promise<PartitionInfo[]> {
    try {
      const pool = this.getConnection();

      const query = `
        SELECT
          nmsp_parent.nspname AS schemaname,
          parent.relname AS tablename,
          child.relname AS partitionname,
          pg_get_expr(child.relpartbound, child.oid) AS partition_expression,
          CASE parent.relkind
            WHEN 'p' THEN
              CASE partstrat
                WHEN 'l' THEN 'list'
                WHEN 'r' THEN 'range'
                WHEN 'h' THEN 'hash'
              END
          END AS partition_strategy,
          NULL AS partition_start,
          NULL AS partition_end,
          parent.relname AS parent_table
        FROM pg_inherits
        JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
        JOIN pg_class child ON pg_inherits.inhrelid = child.oid
        JOIN pg_namespace nmsp_parent ON nmsp_parent.oid = parent.relnamespace
        JOIN pg_namespace nmsp_child ON nmsp_child.oid = child.relnamespace
        LEFT JOIN pg_partitioned_table ON pg_partitioned_table.partrelid = parent.oid
        WHERE parent.relname = $1
          AND nmsp_parent.nspname = $2
          AND parent.relkind = 'p'
        ORDER BY child.relname
      `;

      const result = await pool.query(query, [table, schema]);

      return result.rows as PartitionInfo[];
    } catch (error) {
      logger.error('Failed to get partitions', error);
      throw error;
    }
  }

  /**
   * Display table statistics
   */
  displayStatsTable(stats: TableStats[]): void {
    if (stats.length === 0) {
      console.log(chalk.yellow('\nNo statistics found\n'));
      return;
    }

    const table = new Table({
      head: [
        chalk.bold('Schema'),
        chalk.bold('Table'),
        chalk.bold('Seq Scan'),
        chalk.bold('Idx Scan'),
        chalk.bold('Live Tuples'),
        chalk.bold('Dead Tuples'),
        chalk.bold('Last Vacuum'),
        chalk.bold('Last Analyze')
      ],
      colWidths: [15, 25, 12, 12, 15, 15, 20, 20]
    });

    stats.forEach(stat => {
      table.push([
        stat.schemaname,
        stat.tablename,
        stat.seq_scan?.toString() || '0',
        stat.idx_scan?.toString() || '0',
        stat.n_live_tup?.toString() || '0',
        stat.n_dead_tup?.toString() || '0',
        stat.last_vacuum ? new Date(stat.last_vacuum).toLocaleString() : chalk.dim('Never'),
        stat.last_analyze ? new Date(stat.last_analyze).toLocaleString() : chalk.dim('Never')
      ]);
    });

    console.log('\n' + table.toString() + '\n');
  }

  /**
   * Display locks table
   */
  displayLocksTable(locks: LockInfo[]): void {
    if (locks.length === 0) {
      console.log(chalk.yellow('\nNo locks found\n'));
      return;
    }

    const table = new Table({
      head: [
        chalk.bold('PID'),
        chalk.bold('Database'),
        chalk.bold('Relation'),
        chalk.bold('Lock Type'),
        chalk.bold('Mode'),
        chalk.bold('Granted'),
        chalk.bold('Wait Start')
      ],
      colWidths: [8, 15, 25, 15, 20, 10, 20]
    });

    locks.forEach(lock => {
      table.push([
        lock.pid.toString(),
        lock.database || chalk.dim('N/A'),
        lock.relation || chalk.dim('N/A'),
        lock.locktype,
        lock.mode,
        lock.granted ? chalk.green('Yes') : chalk.red('No'),
        lock.waitstart ? new Date(lock.waitstart).toLocaleString() : chalk.dim('N/A')
      ]);
    });

    console.log('\n' + table.toString() + '\n');
  }

  /**
   * Display activity table
   */
  displayActivityTable(activities: ActivityInfo[]): void {
    if (activities.length === 0) {
      console.log(chalk.yellow('\nNo active connections\n'));
      return;
    }

    const table = new Table({
      head: [
        chalk.bold('PID'),
        chalk.bold('User'),
        chalk.bold('App'),
        chalk.bold('State'),
        chalk.bold('Query Start'),
        chalk.bold('Wait Event'),
        chalk.bold('Query')
      ],
      colWidths: [8, 15, 20, 12, 20, 20, 40]
    });

    activities.forEach(activity => {
      const queryPreview = activity.query.length > 37
        ? activity.query.substring(0, 37) + '...'
        : activity.query;

      table.push([
        activity.pid.toString(),
        activity.usename,
        activity.application_name || chalk.dim('N/A'),
        activity.state,
        activity.query_start ? new Date(activity.query_start).toLocaleString() : chalk.dim('N/A'),
        activity.wait_event || chalk.dim('None'),
        queryPreview
      ]);
    });

    console.log('\n' + table.toString() + '\n');
  }

  /**
   * Display extensions table
   */
  displayExtensionsTable(extensions: ExtensionInfo[]): void {
    if (extensions.length === 0) {
      console.log(chalk.yellow('\nNo extensions found\n'));
      return;
    }

    const table = new Table({
      head: [
        chalk.bold('Name'),
        chalk.bold('Default Version'),
        chalk.bold('Installed Version'),
        chalk.bold('Status'),
        chalk.bold('Comment')
      ],
      colWidths: [25, 18, 18, 12, 40]
    });

    extensions.forEach(ext => {
      table.push([
        ext.name,
        ext.default_version,
        ext.installed_version || chalk.dim('Not installed'),
        ext.installed_version ? chalk.green('Installed') : chalk.dim('Available'),
        ext.comment ? ext.comment.substring(0, 37) + (ext.comment.length > 37 ? '...' : '') : ''
      ]);
    });

    console.log('\n' + table.toString() + '\n');
  }

  /**
   * Display partitions table
   */
  displayPartitionsTable(partitions: PartitionInfo[]): void {
    if (partitions.length === 0) {
      console.log(chalk.yellow('\nNo partitions found (table may not be partitioned)\n'));
      return;
    }

    const table = new Table({
      head: [
        chalk.bold('Schema'),
        chalk.bold('Parent Table'),
        chalk.bold('Partition Name'),
        chalk.bold('Strategy'),
        chalk.bold('Expression')
      ],
      colWidths: [15, 25, 30, 12, 40]
    });

    partitions.forEach(partition => {
      table.push([
        partition.schemaname,
        partition.parent_table,
        partition.partitionname,
        partition.partition_strategy,
        partition.partition_expression || chalk.dim('N/A')
      ]);
    });

    console.log('\n' + table.toString() + '\n');
  }

  /**
   * Cleanup
   */
  async cleanup(): Promise<void> {
    // Cleanup resources if needed
    logger.info('PostgresAdvancedCLI cleanup complete');
  }
}

/**
 * Setup PostgreSQL advanced commands
 */
export function setupPostgresAdvancedCommands(program: Command): void {
  const pgCLI = new PostgresAdvancedCLI();

  // pg command group
  const pg = program
    .command('pg')
    .description('PostgreSQL advanced operations');

  // VACUUM command
  pg.command('vacuum')
    .description('Run VACUUM to reclaim storage and optionally update statistics')
    .argument('[table]', 'Table name (omit for all tables)')
    .option('--full', 'Perform full vacuum (rewrites entire table)')
    .option('--freeze', 'Freeze row versions')
    .option('--analyze', 'Update statistics after vacuum')
    .option('--verbose', 'Show detailed vacuum information')
    .option('--skip-locked', 'Skip tables that cannot be locked immediately')
    .option('--no-index-cleanup', 'Skip index cleanup phase')
    .option('--no-truncate', 'Do not truncate empty pages at the end')
    .option('--parallel <workers>', 'Use parallel vacuum with N workers', parseInt)
    .action(async (table, options) => {
      try {
        console.log(chalk.blue(`\n🧹 Running VACUUM${table ? ` on ${table}` : ' on all tables'}...\n`));

        const result = await pgCLI.vacuum({
          table,
          full: options.full,
          freeze: options.freeze,
          analyze: options.analyze,
          verbose: options.verbose,
          skipLocked: options.skipLocked,
          indexCleanup: !options.noIndexCleanup,
          truncate: !options.noTruncate,
          parallel: options.parallel
        });

        console.log(chalk.green(`✓ ${result.message}\n`));

        if (result.details && options.verbose) {
          console.log(chalk.dim('Details:'));
          console.log(result.details);
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // ANALYZE command
  pg.command('analyze')
    .description('Update query planner statistics')
    .argument('[table]', 'Table name (omit for all tables)')
    .option('--verbose', 'Show detailed analyze information')
    .option('--skip-locked', 'Skip tables that cannot be locked immediately')
    .action(async (table, options) => {
      try {
        console.log(chalk.blue(`\n📊 Running ANALYZE${table ? ` on ${table}` : ' on all tables'}...\n`));

        const result = await pgCLI.analyze({
          table,
          verbose: options.verbose,
          skipLocked: options.skipLocked
        });

        console.log(chalk.green(`✓ ${result.message}\n`));

        if (result.details && options.verbose) {
          console.log(chalk.dim('Details:'));
          console.log(result.details);
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // REINDEX command
  pg.command('reindex <type> <name>')
    .description('Rebuild indexes (type: index, table, database, schema)')
    .option('--concurrently', 'Rebuild index without locking writes')
    .option('--verbose', 'Show detailed reindex information')
    .action(async (type, name, options) => {
      try {
        if (!['index', 'table', 'database', 'schema'].includes(type.toLowerCase())) {
          throw new Error('Type must be: index, table, database, or schema');
        }

        console.log(chalk.blue(`\n🔧 Reindexing ${type} "${name}"...\n`));

        const result = await pgCLI.reindex({
          type: type.toLowerCase() as 'index' | 'table' | 'database' | 'schema',
          name,
          concurrently: options.concurrently,
          verbose: options.verbose
        });

        console.log(chalk.green(`✓ ${result.message}\n`));
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Stats command
  pg.command('stats')
    .description('Get detailed table statistics from pg_stat_user_tables')
    .argument('[table]', 'Table name (omit for all tables)')
    .option('--schema <name>', 'Schema name', 'public')
    .option('--format <type>', 'Output format (table, json)', 'table')
    .action(async (table, options) => {
      try {
        const stats = await pgCLI.getTableStats(table, options.schema);

        if (options.format === 'json') {
          console.log(JSON.stringify(stats, null, 2));
        } else {
          pgCLI.displayStatsTable(stats);
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Locks command
  pg.command('locks')
    .description('Show current database locks from pg_locks')
    .argument('[database]', 'Database name (omit for all databases)')
    .option('--format <type>', 'Output format (table, json)', 'table')
    .action(async (database, options) => {
      try {
        const locks = await pgCLI.getLocks(database);

        if (options.format === 'json') {
          console.log(JSON.stringify(locks, null, 2));
        } else {
          pgCLI.displayLocksTable(locks);
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Activity command
  pg.command('activity')
    .description('Show active database connections and queries')
    .option('--all', 'Show all connections including idle')
    .option('--format <type>', 'Output format (table, json)', 'table')
    .action(async (options) => {
      try {
        const activities = await pgCLI.getActivity(options.all);

        if (options.format === 'json') {
          console.log(JSON.stringify(activities, null, 2));
        } else {
          pgCLI.displayActivityTable(activities);
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Extensions command
  pg.command('extensions')
    .description('Manage PostgreSQL extensions')
    .argument('[action]', 'Action: list, enable, disable', 'list')
    .argument('[name]', 'Extension name (required for enable/disable)')
    .option('--schema <name>', 'Schema for extension (enable only)')
    .option('--cascade', 'Cascade when disabling extension')
    .option('--all', 'Show all available extensions (list only)')
    .option('--format <type>', 'Output format (table, json)', 'table')
    .action(async (action, name, options) => {
      try {
        if (action === 'list') {
          const extensions = await pgCLI.listExtensions(!options.all);

          if (options.format === 'json') {
            console.log(JSON.stringify(extensions, null, 2));
          } else {
            pgCLI.displayExtensionsTable(extensions);
          }
        } else if (action === 'enable') {
          if (!name) {
            throw new Error('Extension name required for enable action');
          }

          console.log(chalk.blue(`\n📦 Enabling extension "${name}"...\n`));

          const result = await pgCLI.enableExtension(name, options.schema);
          console.log(chalk.green(`✓ ${result.message}\n`));
        } else if (action === 'disable') {
          if (!name) {
            throw new Error('Extension name required for disable action');
          }

          console.log(chalk.blue(`\n📦 Disabling extension "${name}"...\n`));

          const result = await pgCLI.disableExtension(name, options.cascade);
          console.log(chalk.green(`✓ ${result.message}\n`));
        } else {
          throw new Error('Action must be: list, enable, or disable');
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Partitions command
  pg.command('partitions <table>')
    .description('Show partition information for a partitioned table')
    .option('--schema <name>', 'Schema name', 'public')
    .option('--format <type>', 'Output format (table, json)', 'table')
    .action(async (table, options) => {
      try {
        const partitions = await pgCLI.getPartitions(table, options.schema);

        if (options.format === 'json') {
          console.log(JSON.stringify(partitions, null, 2));
        } else {
          pgCLI.displayPartitionsTable(partitions);
        }
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });
}

export default PostgresAdvancedCLI;
