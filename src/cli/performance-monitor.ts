/**
 * Performance Monitor
 * Real-time performance monitoring and query analytics
 */

import { EventEmitter } from 'eventemitter3';
import { StateManager } from '../core/state-manager';
import { LLMMCPBridge } from '../llm/mcp-bridge';

/**
 * Monitor options
 */
export interface MonitorOptions {
  interval?: number; // Update interval in seconds
  metrics?: string[]; // Specific metrics to display
  maxHistory?: number; // Max history items to keep
}

/**
 * Performance metrics
 */
export interface PerformanceMetrics {
  timestamp: number;
  activeConnections: number;
  queriesPerSecond: number;
  averageQueryTime: number;
  slowQueriesCount: number;
  cacheHitRate: number;
  databaseSize: number;
  growthRate: number;
  lockWaits: number;
  cpuUsage: number;
  memoryUsage: number;
}

/**
 * Slow query
 */
export interface SlowQuery {
  query: string;
  executionTime: number;
  frequency: number;
  lastExecuted: number;
  optimizations?: string[];
}

/**
 * Query analysis
 */
export interface QueryAnalysis {
  query: string;
  executionPlan: any;
  estimatedCost: number;
  missingIndexes: string[];
  optimizationSuggestions: string[];
  rewriteSuggestion?: string;
}

/**
 * Index suggestion
 */
export interface IndexSuggestion {
  table: string;
  columns: string[];
  reason: string;
  estimatedImprovement: string;
  createStatement: string;
}

/**
 * Connection pool statistics
 */
export interface PoolStats {
  totalConnections: number;
  activeConnections: number;
  idleConnections: number;
  waitingQueries: number;
  averageWaitTime: number;
  maxWaitTime: number;
}

/**
 * Performance monitoring events
 */
export interface PerformanceMonitorEvents {
  metricsUpdate: (metrics: PerformanceMetrics) => void;
  slowQueryDetected: (query: SlowQuery) => void;
  alert: (type: string, message: string, severity: 'info' | 'warning' | 'error') => void;
}

/**
 * Performance Monitor
 */
export class PerformanceMonitor extends EventEmitter<PerformanceMonitorEvents> {
  private metricsHistory: PerformanceMetrics[] = [];
  private monitoringInterval?: NodeJS.Timeout;

  constructor(
    private stateManager: StateManager,
    private mcpBridge?: LLMMCPBridge
  ) {
    super();
  }

  /**
   * Start real-time monitoring
   */
  async monitor(options: MonitorOptions = {}): Promise<void> {
    const interval = (options.interval || 5) * 1000;
    const maxHistory = options.maxHistory || 100;

    console.log('🔍 Starting performance monitoring...');
    console.log(`Update interval: ${interval / 1000}s\n`);

    // Initial metrics
    await this.updateMetrics();

    // Start monitoring interval
    this.monitoringInterval = setInterval(async () => {
      await this.updateMetrics();

      // Keep history limited
      if (this.metricsHistory.length > maxHistory) {
        this.metricsHistory = this.metricsHistory.slice(-maxHistory);
      }

      // Display current metrics
      this.displayMetrics(options.metrics);
    }, interval);

    // Keep process alive
    return new Promise(() => {
      // Run until interrupted
    });
  }

  /**
   * Update performance metrics
   */
  private async updateMetrics(): Promise<void> {
    const metrics: PerformanceMetrics = {
      timestamp: Date.now(),
      activeConnections: await this.getActiveConnections(),
      queriesPerSecond: await this.getQueriesPerSecond(),
      averageQueryTime: await this.getAverageQueryTime(),
      slowQueriesCount: await this.getSlowQueriesCount(),
      cacheHitRate: await this.getCacheHitRate(),
      databaseSize: await this.getDatabaseSize(),
      growthRate: await this.getGrowthRate(),
      lockWaits: await this.getLockWaits(),
      cpuUsage: await this.getCPUUsage(),
      memoryUsage: await this.getMemoryUsage()
    };

    this.metricsHistory.push(metrics);
    this.emit('metricsUpdate', metrics);

    // Store in state manager
    this.stateManager.set('perf:latest', metrics, {
      metadata: { type: 'performance-metrics' }
    });

    // Check for alerts
    this.checkAlerts(metrics);
  }

  /**
   * Display metrics in terminal
   */
  private displayMetrics(specificMetrics?: string[]): void {
    const latest = this.metricsHistory[this.metricsHistory.length - 1];
    if (!latest) return;

    console.clear();
    console.log('═══════════════════════════════════════════════════════════');
    console.log('                  PERFORMANCE DASHBOARD');
    console.log('═══════════════════════════════════════════════════════════');
    console.log(`Timestamp: ${new Date(latest.timestamp).toISOString()}\n`);

    const shouldShow = (metric: string) =>
      !specificMetrics || specificMetrics.includes(metric);

    if (shouldShow('connections')) {
      console.log(`🔗 Active Connections: ${latest.activeConnections}`);
    }

    if (shouldShow('qps')) {
      console.log(`⚡ Queries/Second: ${latest.queriesPerSecond.toFixed(2)}`);
    }

    if (shouldShow('query-time')) {
      console.log(`⏱️  Average Query Time: ${latest.averageQueryTime.toFixed(2)}ms`);
    }

    if (shouldShow('slow-queries')) {
      const indicator = latest.slowQueriesCount > 0 ? '⚠️' : '✓';
      console.log(`${indicator} Slow Queries: ${latest.slowQueriesCount}`);
    }

    if (shouldShow('cache')) {
      const cachePercent = (latest.cacheHitRate * 100).toFixed(1);
      console.log(`💾 Cache Hit Rate: ${cachePercent}%`);
    }

    if (shouldShow('size')) {
      console.log(`📊 Database Size: ${this.formatBytes(latest.databaseSize)}`);
    }

    if (shouldShow('growth')) {
      console.log(`📈 Growth Rate: ${this.formatBytes(latest.growthRate)}/day`);
    }

    if (shouldShow('locks')) {
      const lockIndicator = latest.lockWaits > 0 ? '⚠️' : '✓';
      console.log(`${lockIndicator} Lock Waits: ${latest.lockWaits}`);
    }

    if (shouldShow('cpu')) {
      console.log(`💻 CPU Usage: ${latest.cpuUsage.toFixed(1)}%`);
    }

    if (shouldShow('memory')) {
      console.log(`🧠 Memory Usage: ${latest.memoryUsage.toFixed(1)}%`);
    }

    console.log('\n═══════════════════════════════════════════════════════════');
    console.log('Press Ctrl+C to stop monitoring');
  }

  /**
   * Get slow queries
   */
  async slowQueries(threshold: number = 1000, limit: number = 10): Promise<SlowQuery[]> {
    const queries = this.stateManager.findByMetadata('type', 'query-log');
    const slowQueries: Map<string, SlowQuery> = new Map();

    for (const entry of queries) {
      const log = entry.value;
      if (log.duration >= threshold) {
        const existing = slowQueries.get(log.query);
        if (existing) {
          existing.frequency++;
          existing.lastExecuted = Math.max(existing.lastExecuted, log.timestamp);
          if (log.duration > existing.executionTime) {
            existing.executionTime = log.duration;
          }
        } else {
          slowQueries.set(log.query, {
            query: log.query,
            executionTime: log.duration,
            frequency: 1,
            lastExecuted: log.timestamp
          });
        }
      }
    }

    // Sort by frequency * execution time (impact)
    const sorted = Array.from(slowQueries.values())
      .sort((a, b) => b.frequency * b.executionTime - a.frequency * a.executionTime)
      .slice(0, limit);

    // Add optimization suggestions using LLM if available
    if (this.mcpBridge) {
      for (const query of sorted) {
        query.optimizations = await this.suggestOptimizations(query.query);
      }
    }

    return sorted;
  }

  /**
   * Analyze query performance
   */
  async analyzeQuery(sql: string): Promise<QueryAnalysis> {
    console.log(`🔍 Analyzing query:\n${sql}\n`);

    // Mock execution plan (in real implementation, use EXPLAIN)
    const executionPlan = {
      type: 'Sequential Scan',
      table: 'users',
      rowsEstimated: 1000,
      cost: 42.5
    };

    const missingIndexes: string[] = [];
    const optimizationSuggestions: string[] = [];

    // Detect missing indexes
    const whereMatch = sql.match(/WHERE\s+(\w+)/i);
    if (whereMatch && !sql.toLowerCase().includes('index')) {
      missingIndexes.push(whereMatch[1]);
      optimizationSuggestions.push(`Consider adding index on column: ${whereMatch[1]}`);
    }

    // Check for SELECT *
    if (sql.toLowerCase().includes('select *')) {
      optimizationSuggestions.push('Avoid SELECT *, specify only required columns');
    }

    // Check for JOIN without indexes
    if (sql.toLowerCase().includes('join')) {
      optimizationSuggestions.push('Ensure JOIN columns are indexed');
    }

    // Use LLM for advanced suggestions
    let rewriteSuggestion: string | undefined;
    if (this.mcpBridge) {
      rewriteSuggestion = await this.getLLMRewrite(sql);
      const llmSuggestions = await this.suggestOptimizations(sql);
      optimizationSuggestions.push(...llmSuggestions);
    }

    return {
      query: sql,
      executionPlan,
      estimatedCost: executionPlan.cost,
      missingIndexes,
      optimizationSuggestions,
      rewriteSuggestion
    };
  }

  /**
   * Get index recommendations
   */
  async indexRecommendations(): Promise<IndexSuggestion[]> {
    const queries = this.stateManager.findByMetadata('type', 'query-log');
    const columnUsage: Map<string, { table: string; count: number }> = new Map();

    // Analyze query patterns
    for (const entry of queries) {
      const query = entry.value.query.toLowerCase();

      // Extract WHERE clauses
      const whereMatch = query.match(/where\s+(\w+)\.(\w+)/i);
      if (whereMatch) {
        const table = whereMatch[1];
        const column = whereMatch[2];
        const key = `${table}.${column}`;

        const existing = columnUsage.get(key);
        if (existing) {
          existing.count++;
        } else {
          columnUsage.set(key, { table, count: 1 });
        }
      }
    }

    // Generate recommendations
    const recommendations: IndexSuggestion[] = [];
    const entries = Array.from(columnUsage.entries());
    for (const [key, usage] of entries) {
      const [table, ...columns] = key.split('.');
      if (usage.count >= 5) {
        // Suggest if used frequently
        recommendations.push({
          table,
          columns,
          reason: `Column used in ${usage.count} queries`,
          estimatedImprovement: `${Math.min(usage.count * 10, 90)}% faster lookups`,
          createStatement: `CREATE INDEX idx_${table}_${columns.join('_')} ON ${table}(${columns.join(', ')});`
        });
      }
    }

    return recommendations.sort((a, b) => {
      const aUsage = columnUsage.get(`${a.table}.${a.columns.join('.')}`)?.count || 0;
      const bUsage = columnUsage.get(`${b.table}.${b.columns.join('.')}`)?.count || 0;
      return bUsage - aUsage;
    });
  }

  /**
   * Get connection pool statistics
   */
  async connectionPool(): Promise<PoolStats> {
    // Mock data (in real implementation, query actual pool)
    return {
      totalConnections: 20,
      activeConnections: await this.getActiveConnections(),
      idleConnections: 15,
      waitingQueries: 2,
      averageWaitTime: 45,
      maxWaitTime: 120
    };
  }

  /**
   * Stop monitoring
   */
  stop(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }
    console.log('\n✓ Monitoring stopped');
  }

  /**
   * Get performance metrics history
   */
  getHistory(limit?: number): PerformanceMetrics[] {
    return limit ? this.metricsHistory.slice(-limit) : [...this.metricsHistory];
  }

  // Private helper methods

  private async getActiveConnections(): Promise<number> {
    // Mock implementation
    return Math.floor(Math.random() * 10) + 5;
  }

  private async getQueriesPerSecond(): Promise<number> {
    const recent = this.stateManager.getByPrefix('query:');
    const oneSecondAgo = Date.now() - 1000;
    let count = 0;

    const entries = Array.from(recent.entries());
    for (const [, timestamp] of entries) {
      if (timestamp > oneSecondAgo) count++;
    }

    return count;
  }

  private async getAverageQueryTime(): Promise<number> {
    const queries = this.stateManager.findByMetadata('type', 'query-log');
    if (queries.length === 0) return 0;

    const recentQueries = queries.slice(-100);
    const totalTime = recentQueries.reduce((sum, q) => sum + (q.value.duration || 0), 0);
    return totalTime / recentQueries.length;
  }

  private async getSlowQueriesCount(): Promise<number> {
    const queries = this.stateManager.findByMetadata('type', 'query-log');
    return queries.filter((q) => q.value.duration > 1000).length;
  }

  private async getCacheHitRate(): Promise<number> {
    // Mock implementation
    return 0.75 + Math.random() * 0.2;
  }

  private async getDatabaseSize(): Promise<number> {
    // Mock implementation - return bytes
    return 1024 * 1024 * 1024 * 2.5; // 2.5 GB
  }

  private async getGrowthRate(): Promise<number> {
    // Mock implementation - bytes per day
    return 1024 * 1024 * 50; // 50 MB/day
  }

  private async getLockWaits(): Promise<number> {
    // Mock implementation
    return Math.random() > 0.8 ? Math.floor(Math.random() * 5) : 0;
  }

  private async getCPUUsage(): Promise<number> {
    // Use process CPU usage
    const usage = process.cpuUsage();
    return ((usage.user + usage.system) / 1000000) % 100;
  }

  private async getMemoryUsage(): Promise<number> {
    const mem = process.memoryUsage();
    return (mem.heapUsed / mem.heapTotal) * 100;
  }

  private checkAlerts(metrics: PerformanceMetrics): void {
    // High query time
    if (metrics.averageQueryTime > 500) {
      this.emit('alert', 'query-time', 'Average query time is high', 'warning');
    }

    // Low cache hit rate
    if (metrics.cacheHitRate < 0.5) {
      this.emit('alert', 'cache', 'Cache hit rate is low', 'warning');
    }

    // Lock contention
    if (metrics.lockWaits > 10) {
      this.emit('alert', 'locks', 'High lock contention detected', 'error');
    }

    // High CPU
    if (metrics.cpuUsage > 80) {
      this.emit('alert', 'cpu', 'CPU usage is high', 'warning');
    }

    // High memory
    if (metrics.memoryUsage > 90) {
      this.emit('alert', 'memory', 'Memory usage is critical', 'error');
    }
  }

  private formatBytes(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`;
  }

  private async suggestOptimizations(query: string): Promise<string[]> {
    if (!this.mcpBridge) return [];

    try {
      const response = await this.mcpBridge.generate({
        messages: [
          {
            role: 'system',
            content: 'You are a database optimization expert. Provide concise optimization suggestions.'
          },
          {
            role: 'user',
            content: `Suggest optimizations for this SQL query:\n\n${query}\n\nProvide 3-5 bullet points.`
          }
        ],
        enableTools: false
      });

      const suggestions = response.content
        .split('\n')
        .filter((line) => line.trim().startsWith('-') || line.trim().startsWith('•'))
        .map((line) => line.replace(/^[-•]\s*/, '').trim());

      return suggestions.slice(0, 5);
    } catch (error) {
      console.error('Failed to get LLM suggestions:', error);
      return [];
    }
  }

  private async getLLMRewrite(query: string): Promise<string | undefined> {
    if (!this.mcpBridge) return undefined;

    try {
      const response = await this.mcpBridge.generate({
        messages: [
          {
            role: 'system',
            content: 'You are a database optimization expert. Rewrite queries for better performance.'
          },
          {
            role: 'user',
            content: `Rewrite this SQL query for optimal performance:\n\n${query}\n\nProvide only the rewritten query without explanation.`
          }
        ],
        enableTools: false
      });

      return response.content.trim();
    } catch (error) {
      console.error('Failed to get LLM rewrite:', error);
      return undefined;
    }
  }
}
