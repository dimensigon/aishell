/**
 * PostgreSQL Advanced Commands - Utility functions and command builders
 * Provides helper functions for PostgreSQL advanced operations
 */

import { Pool as PgPool } from 'pg';

/**
 * VACUUM command builder
 */
export class VacuumCommandBuilder {
  private options: string[] = [];
  private targetTable?: string;

  full(): this {
    this.options.push('FULL');
    return this;
  }

  freeze(): this {
    this.options.push('FREEZE');
    return this;
  }

  analyze(): this {
    this.options.push('ANALYZE');
    return this;
  }

  verbose(): this {
    this.options.push('VERBOSE');
    return this;
  }

  skipLocked(): this {
    this.options.push('SKIP_LOCKED');
    return this;
  }

  indexCleanup(enabled: boolean): this {
    this.options.push(`INDEX_CLEANUP ${enabled ? 'ON' : 'OFF'}`);
    return this;
  }

  truncate(enabled: boolean): this {
    this.options.push(`TRUNCATE ${enabled ? 'ON' : 'OFF'}`);
    return this;
  }

  parallel(workers: number): this {
    if (workers < 0) {
      throw new Error('Parallel workers must be non-negative');
    }
    this.options.push(`PARALLEL ${workers}`);
    return this;
  }

  table(tableName: string): this {
    this.targetTable = tableName;
    return this;
  }

  build(): string {
    const parts: string[] = ['VACUUM'];

    if (this.options.length > 0) {
      parts.push(`(${this.options.join(', ')})`);
    }

    if (this.targetTable) {
      parts.push(this.targetTable);
    }

    return parts.join(' ');
  }
}

/**
 * ANALYZE command builder
 */
export class AnalyzeCommandBuilder {
  private options: string[] = [];
  private targetTable?: string;

  verbose(): this {
    this.options.push('VERBOSE');
    return this;
  }

  skipLocked(): this {
    this.options.push('SKIP_LOCKED');
    return this;
  }

  table(tableName: string): this {
    this.targetTable = tableName;
    return this;
  }

  build(): string {
    const parts: string[] = ['ANALYZE'];

    if (this.options.length > 0) {
      parts.push(`(${this.options.join(', ')})`);
    }

    if (this.targetTable) {
      parts.push(this.targetTable);
    }

    return parts.join(' ');
  }
}

/**
 * REINDEX command builder
 */
export class ReindexCommandBuilder {
  private options: string[] = [];
  private targetType?: string;
  private targetName?: string;

  concurrently(): this {
    this.options.push('CONCURRENTLY');
    return this;
  }

  verbose(): this {
    this.options.push('VERBOSE');
    return this;
  }

  index(indexName: string): this {
    this.targetType = 'INDEX';
    this.targetName = indexName;
    return this;
  }

  table(tableName: string): this {
    this.targetType = 'TABLE';
    this.targetName = tableName;
    return this;
  }

  database(databaseName: string): this {
    this.targetType = 'DATABASE';
    this.targetName = databaseName;
    return this;
  }

  schema(schemaName: string): this {
    this.targetType = 'SCHEMA';
    this.targetName = schemaName;
    return this;
  }

  build(): string {
    if (!this.targetType || !this.targetName) {
      throw new Error('Target type and name are required for REINDEX');
    }

    const parts: string[] = ['REINDEX'];

    if (this.options.length > 0) {
      parts.push(`(${this.options.join(', ')})`);
    }

    parts.push(this.targetType);
    parts.push(this.targetName);

    return parts.join(' ');
  }
}

/**
 * PostgreSQL system catalog queries
 */
export class PostgreSQLSystemCatalogs {
  constructor(private pool: PgPool) {}

  /**
   * Get table bloat estimate
   */
  async getTableBloat(schema: string = 'public'): Promise<any[]> {
    const query = `
      SELECT
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
        pg_size_pretty((pg_total_relation_size(schemaname||'.'||tablename) -
          pg_relation_size(schemaname||'.'||tablename))) AS bloat
      FROM pg_tables
      WHERE schemaname = $1
      ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    `;

    const result = await this.pool.query(query, [schema]);
    return result.rows;
  }

  /**
   * Get index usage statistics
   */
  async getIndexUsage(schema: string = 'public'): Promise<any[]> {
    const query = `
      SELECT
        schemaname,
        tablename,
        indexname,
        idx_scan,
        idx_tup_read,
        idx_tup_fetch,
        pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
      FROM pg_stat_user_indexes
      WHERE schemaname = $1
      ORDER BY idx_scan ASC
    `;

    const result = await this.pool.query(query, [schema]);
    return result.rows;
  }

  /**
   * Get unused indexes
   */
  async getUnusedIndexes(schema: string = 'public'): Promise<any[]> {
    const query = `
      SELECT
        schemaname,
        tablename,
        indexname,
        pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
      FROM pg_stat_user_indexes
      WHERE schemaname = $1
        AND idx_scan = 0
        AND indexrelname NOT LIKE '%_pkey'
      ORDER BY pg_relation_size(indexrelid) DESC
    `;

    const result = await this.pool.query(query, [schema]);
    return result.rows;
  }

  /**
   * Get database size
   */
  async getDatabaseSize(): Promise<any> {
    const query = `
      SELECT
        pg_database.datname,
        pg_size_pretty(pg_database_size(pg_database.datname)) AS size
      FROM pg_database
      WHERE datistemplate = false
      ORDER BY pg_database_size(pg_database.datname) DESC
    `;

    const result = await this.pool.query(query);
    return result.rows;
  }

  /**
   * Get table sizes
   */
  async getTableSizes(schema: string = 'public'): Promise<any[]> {
    const query = `
      SELECT
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
        pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
          pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
      FROM pg_tables
      WHERE schemaname = $1
      ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    `;

    const result = await this.pool.query(query, [schema]);
    return result.rows;
  }

  /**
   * Get long-running queries
   */
  async getLongRunningQueries(minDurationSeconds: number = 60): Promise<any[]> {
    const query = `
      SELECT
        pid,
        now() - query_start AS duration,
        usename,
        query,
        state
      FROM pg_stat_activity
      WHERE state != 'idle'
        AND query_start IS NOT NULL
        AND now() - query_start > interval '${minDurationSeconds} seconds'
      ORDER BY duration DESC
    `;

    const result = await this.pool.query(query);
    return result.rows;
  }

  /**
   * Get blocking queries
   */
  async getBlockingQueries(): Promise<any[]> {
    const query = `
      SELECT
        blocked_locks.pid AS blocked_pid,
        blocked_activity.usename AS blocked_user,
        blocking_locks.pid AS blocking_pid,
        blocking_activity.usename AS blocking_user,
        blocked_activity.query AS blocked_statement,
        blocking_activity.query AS current_statement_in_blocking_process
      FROM pg_catalog.pg_locks blocked_locks
      JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
      JOIN pg_catalog.pg_locks blocking_locks
        ON blocking_locks.locktype = blocked_locks.locktype
        AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
        AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
        AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
        AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
        AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
        AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
        AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
        AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
        AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
        AND blocking_locks.pid != blocked_locks.pid
      JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
      WHERE NOT blocked_locks.granted
    `;

    const result = await this.pool.query(query);
    return result.rows;
  }

  /**
   * Get replication status
   */
  async getReplicationStatus(): Promise<any[]> {
    const query = `
      SELECT
        client_addr,
        client_hostname,
        state,
        sync_state,
        pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn)) AS sent_lag,
        pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), write_lsn)) AS write_lag,
        pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), flush_lsn)) AS flush_lag,
        pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)) AS replay_lag
      FROM pg_stat_replication
    `;

    try {
      const result = await this.pool.query(query);
      return result.rows;
    } catch (error) {
      // Replication functions might not be available on all PostgreSQL versions
      return [];
    }
  }
}

/**
 * PostgreSQL maintenance utilities
 */
export class PostgreSQLMaintenanceUtils {
  /**
   * Calculate bloat percentage
   */
  static calculateBloatPercentage(liveRows: number, deadRows: number): number {
    if (liveRows === 0 && deadRows === 0) return 0;
    return (deadRows / (liveRows + deadRows)) * 100;
  }

  /**
   * Determine if VACUUM is recommended
   */
  static shouldVacuum(liveRows: number, deadRows: number, threshold: number = 20): boolean {
    const bloatPercentage = this.calculateBloatPercentage(liveRows, deadRows);
    return bloatPercentage >= threshold;
  }

  /**
   * Determine if ANALYZE is recommended
   */
  static shouldAnalyze(lastAnalyze: Date | null, daysSinceAnalyze: number = 7): boolean {
    if (!lastAnalyze) return true;

    const now = new Date();
    const diffDays = (now.getTime() - lastAnalyze.getTime()) / (1000 * 60 * 60 * 24);

    return diffDays >= daysSinceAnalyze;
  }

  /**
   * Estimate VACUUM duration
   */
  static estimateVacuumDuration(
    tableSize: number,
    deadRows: number,
    mbPerSecond: number = 50
  ): number {
    // Rough estimate based on table size and dead rows
    const estimatedDataToProcess = (tableSize * (deadRows / 1000000)) / 1024 / 1024; // MB
    return Math.ceil(estimatedDataToProcess / mbPerSecond); // seconds
  }

  /**
   * Format duration for display
   */
  static formatDuration(milliseconds: number): string {
    if (milliseconds < 1000) {
      return `${milliseconds}ms`;
    }

    const seconds = Math.floor(milliseconds / 1000);
    if (seconds < 60) {
      return `${seconds}s`;
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    if (minutes < 60) {
      return `${minutes}m ${remainingSeconds}s`;
    }

    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;

    return `${hours}h ${remainingMinutes}m`;
  }

  /**
   * Format bytes for display
   */
  static formatBytes(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`;
  }

  /**
   * Parse PostgreSQL interval
   */
  static parseInterval(interval: string): number {
    // Parse PostgreSQL interval string to milliseconds
    const matches = interval.match(/(\d+):(\d+):(\d+)\.?(\d+)?/);
    if (!matches) return 0;

    const [, hours, minutes, seconds, milliseconds] = matches;
    return (
      parseInt(hours) * 3600000 +
      parseInt(minutes) * 60000 +
      parseInt(seconds) * 1000 +
      parseInt(milliseconds || '0')
    );
  }
}

export default {
  VacuumCommandBuilder,
  AnalyzeCommandBuilder,
  ReindexCommandBuilder,
  PostgreSQLSystemCatalogs,
  PostgreSQLMaintenanceUtils
};
