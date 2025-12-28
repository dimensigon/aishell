/**
 * Query Logger & Analytics
 * Log and analyze query patterns and performance
 */

import { EventEmitter } from 'eventemitter3';
import * as fs from 'fs/promises';
import * as path from 'path';
import { StateManager } from '../core/state-manager';

/**
 * Query log entry
 */
export interface QueryLog {
  id: string;
  query: string;
  duration: number;
  timestamp: number;
  result?: {
    rowCount?: number;
    affectedRows?: number;
    error?: string;
  };
  metadata?: Record<string, any>;
}

/**
 * Query history
 */
export interface QueryHistory {
  logs: QueryLog[];
  total: number;
  page: number;
  pageSize: number;
}

/**
 * Query analytics
 */
export interface QueryAnalytics {
  totalQueries: number;
  averageDuration: number;
  slowestQuery: QueryLog | null;
  fastestQuery: QueryLog | null;
  mostFrequent: Array<{ query: string; count: number; avgDuration: number }>;
  queryTypeDistribution: Record<string, number>;
  peakUsageTimes: Array<{ hour: number; count: number }>;
  errorRate: number;
  performanceTrend: 'improving' | 'degrading' | 'stable';
}

/**
 * Query logger events
 */
export interface QueryLoggerEvents {
  queryLogged: (log: QueryLog) => void;
  slowQuery: (log: QueryLog) => void;
  queryError: (log: QueryLog) => void;
}

/**
 * Query Logger
 */
export class QueryLogger extends EventEmitter<QueryLoggerEvents> {
  private queryCounter = 0;
  private slowQueryThreshold = 1000; // 1 second

  constructor(
    private stateManager: StateManager,
    private readonly config: {
      slowQueryThreshold?: number;
      maxLogsInMemory?: number;
      persistLogs?: boolean;
      logPath?: string;
    } = {}
  ) {
    super();

    if (config.slowQueryThreshold) {
      this.slowQueryThreshold = config.slowQueryThreshold;
    }
  }

  /**
   * Log a query execution
   */
  async logQuery(query: string, duration: number, result?: any): Promise<void> {
    const log: QueryLog = {
      id: `query_${Date.now()}_${++this.queryCounter}`,
      query: query.trim(),
      duration,
      timestamp: Date.now(),
      result: this.formatResult(result),
      metadata: {
        queryType: this.detectQueryType(query)
      }
    };

    // Store in state manager
    this.stateManager.set(`query:${log.id}`, log.timestamp, {
      metadata: { type: 'query-log' }
    });

    this.stateManager.set(`query-log:${log.id}`, log, {
      metadata: { type: 'query-log' },
      ttl: 7 * 24 * 60 * 60 * 1000 // 7 days
    });

    // Emit events
    this.emit('queryLogged', log);

    if (duration >= this.slowQueryThreshold) {
      this.emit('slowQuery', log);
    }

    if (result?.error) {
      this.emit('queryError', log);
    }

    // Persist to disk if enabled
    if (this.config.persistLogs) {
      await this.persistLog(log);
    }

    // Cleanup old logs
    await this.cleanupOldLogs();
  }

  /**
   * Get query history
   */
  async getHistory(limit: number = 20, offset: number = 0): Promise<QueryHistory> {
    const logs = this.stateManager.findByMetadata('type', 'query-log');

    // Sort by timestamp descending
    const sortedLogs = logs
      .map((entry) => entry.value as QueryLog)
      .sort((a, b) => b.timestamp - a.timestamp);

    const total = sortedLogs.length;
    const paginated = sortedLogs.slice(offset, offset + limit);

    return {
      logs: paginated,
      total,
      page: Math.floor(offset / limit) + 1,
      pageSize: limit
    };
  }

  /**
   * Analyze query patterns
   */
  async analyze(): Promise<QueryAnalytics> {
    const logs = this.stateManager
      .findByMetadata('type', 'query-log')
      .map((entry) => entry.value as QueryLog);

    if (logs.length === 0) {
      return this.getEmptyAnalytics();
    }

    // Basic statistics
    const totalQueries = logs.length;
    const totalDuration = logs.reduce((sum, log) => sum + log.duration, 0);
    const averageDuration = totalDuration / totalQueries;

    // Find slowest and fastest
    const sortedByDuration = [...logs].sort((a, b) => b.duration - a.duration);
    const slowestQuery = sortedByDuration[0] || null;
    const fastestQuery = sortedByDuration[sortedByDuration.length - 1] || null;

    // Most frequent queries
    const queryFrequency = new Map<string, { count: number; totalDuration: number }>();
    for (const log of logs) {
      const normalized = this.normalizeQuery(log.query);
      const existing = queryFrequency.get(normalized);
      if (existing) {
        existing.count++;
        existing.totalDuration += log.duration;
      } else {
        queryFrequency.set(normalized, { count: 1, totalDuration: log.duration });
      }
    }

    const mostFrequent = Array.from(queryFrequency.entries())
      .map(([query, stats]) => ({
        query,
        count: stats.count,
        avgDuration: stats.totalDuration / stats.count
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    // Query type distribution
    const queryTypeDistribution: Record<string, number> = {};
    for (const log of logs) {
      const type = log.metadata?.queryType || 'unknown';
      queryTypeDistribution[type] = (queryTypeDistribution[type] || 0) + 1;
    }

    // Peak usage times
    const hourCounts = new Array(24).fill(0);
    for (const log of logs) {
      const hour = new Date(log.timestamp).getHours();
      hourCounts[hour]++;
    }

    const peakUsageTimes = hourCounts
      .map((count, hour) => ({ hour, count }))
      .filter((item) => item.count > 0)
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    // Error rate
    const errorCount = logs.filter((log) => log.result?.error).length;
    const errorRate = errorCount / totalQueries;

    // Performance trend
    const performanceTrend = this.calculateTrend(logs);

    return {
      totalQueries,
      averageDuration,
      slowestQuery,
      fastestQuery,
      mostFrequent,
      queryTypeDistribution,
      peakUsageTimes,
      errorRate,
      performanceTrend
    };
  }

  /**
   * Export query logs
   */
  async export(format: 'csv' | 'json', filepath: string): Promise<void> {
    const logs = this.stateManager
      .findByMetadata('type', 'query-log')
      .map((entry) => entry.value as QueryLog);

    let content: string;

    if (format === 'csv') {
      content = this.exportAsCSV(logs);
    } else {
      content = JSON.stringify(logs, null, 2);
    }

    await fs.mkdir(path.dirname(filepath), { recursive: true });
    await fs.writeFile(filepath, content, 'utf-8');

    console.log(`✓ Exported ${logs.length} query logs to ${filepath}`);
  }

  /**
   * Clear all query logs
   */
  clearLogs(): number {
    return this.stateManager.deleteByPrefix('query-log:');
  }

  /**
   * Search query logs
   */
  search(pattern: string, options: { caseSensitive?: boolean; limit?: number } = {}): QueryLog[] {
    const logs = this.stateManager
      .findByMetadata('type', 'query-log')
      .map((entry) => entry.value as QueryLog);

    const regex = new RegExp(pattern, options.caseSensitive ? '' : 'i');
    const results = logs.filter((log) => regex.test(log.query));

    return options.limit ? results.slice(0, options.limit) : results;
  }

  /**
   * Get slow queries
   */
  getSlowQueries(threshold?: number, limit: number = 10): QueryLog[] {
    const logs = this.stateManager
      .findByMetadata('type', 'query-log')
      .map((entry) => entry.value as QueryLog);

    const slowThreshold = threshold || this.slowQueryThreshold;

    return logs
      .filter((log) => log.duration >= slowThreshold)
      .sort((a, b) => b.duration - a.duration)
      .slice(0, limit);
  }

  /**
   * Get queries by type
   */
  getByType(type: string, limit?: number): QueryLog[] {
    const logs = this.stateManager
      .findByMetadata('type', 'query-log')
      .map((entry) => entry.value as QueryLog);

    const filtered = logs.filter((log) => log.metadata?.queryType === type);
    return limit ? filtered.slice(0, limit) : filtered;
  }

  // Private helper methods

  private formatResult(result: any): QueryLog['result'] {
    if (!result) return undefined;

    return {
      rowCount: result.rowCount,
      affectedRows: result.affectedRows,
      error: result.error?.message
    };
  }

  private detectQueryType(query: string): string {
    const normalized = query.trim().toLowerCase();

    if (normalized.startsWith('select')) return 'SELECT';
    if (normalized.startsWith('insert')) return 'INSERT';
    if (normalized.startsWith('update')) return 'UPDATE';
    if (normalized.startsWith('delete')) return 'DELETE';
    if (normalized.startsWith('create')) return 'CREATE';
    if (normalized.startsWith('drop')) return 'DROP';
    if (normalized.startsWith('alter')) return 'ALTER';
    if (normalized.startsWith('truncate')) return 'TRUNCATE';

    return 'OTHER';
  }

  private normalizeQuery(query: string): string {
    // Remove specific values to group similar queries
    return query
      .replace(/\d+/g, '?') // Replace numbers
      .replace(/'[^']*'/g, '?') // Replace string literals
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();
  }

  private calculateTrend(logs: QueryLog[]): 'improving' | 'degrading' | 'stable' {
    if (logs.length < 10) return 'stable';

    // Split into two halves
    const mid = Math.floor(logs.length / 2);
    const firstHalf = logs.slice(0, mid);
    const secondHalf = logs.slice(mid);

    const avgFirst = firstHalf.reduce((sum, log) => sum + log.duration, 0) / firstHalf.length;
    const avgSecond = secondHalf.reduce((sum, log) => sum + log.duration, 0) / secondHalf.length;

    const change = ((avgSecond - avgFirst) / avgFirst) * 100;

    if (change < -10) return 'improving';
    if (change > 10) return 'degrading';
    return 'stable';
  }

  private async persistLog(log: QueryLog): Promise<void> {
    if (!this.config.logPath) return;

    try {
      const logFile = path.join(this.config.logPath, `queries-${this.getDateString()}.jsonl`);
      await fs.mkdir(path.dirname(logFile), { recursive: true });
      await fs.appendFile(logFile, JSON.stringify(log) + '\n', 'utf-8');
    } catch (error) {
      console.error('Failed to persist query log:', error);
    }
  }

  private async cleanupOldLogs(): Promise<void> {
    const maxLogs = this.config.maxLogsInMemory || 10000;
    const logs = this.stateManager.findByMetadata('type', 'query-log');

    if (logs.length > maxLogs) {
      // Remove oldest logs
      const sorted = logs.sort((a, b) => a.timestamp - b.timestamp);
      const toRemove = sorted.slice(0, logs.length - maxLogs);

      for (const entry of toRemove) {
        this.stateManager.delete(`query-log:${entry.value.id}`);
      }
    }
  }

  private getDateString(): string {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  }

  private exportAsCSV(logs: QueryLog[]): string {
    const headers = ['ID', 'Query', 'Duration (ms)', 'Timestamp', 'Type', 'Rows', 'Error'];
    const rows = logs.map((log) => [
      log.id,
      `"${log.query.replace(/"/g, '""')}"`,
      log.duration.toString(),
      new Date(log.timestamp).toISOString(),
      log.metadata?.queryType || '',
      log.result?.rowCount?.toString() || '',
      log.result?.error || ''
    ]);

    return [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
  }

  private getEmptyAnalytics(): QueryAnalytics {
    return {
      totalQueries: 0,
      averageDuration: 0,
      slowestQuery: null,
      fastestQuery: null,
      mostFrequent: [],
      queryTypeDistribution: {},
      peakUsageTimes: [],
      errorRate: 0,
      performanceTrend: 'stable'
    };
  }
}
