/**
 * Terminal Dashboard UI
 * Beautiful terminal dashboard using blessed
 */

import * as blessed from 'blessed';
import * as contrib from 'blessed-contrib';
import { PerformanceMetrics } from './performance-monitor';
import { QueryLog } from './query-logger';

/**
 * Dashboard configuration
 */
export interface DashboardConfig {
  refreshInterval?: number;
  showGrid?: boolean;
  theme?: 'dark' | 'light';
}

/**
 * Dashboard UI
 */
export class DashboardUI {
  private screen?: blessed.Widgets.Screen;
  private grid?: any;
  private widgets: {
    metrics?: any;
    qpsLine?: any;
    queryLog?: any;
    slowQueries?: any;
    resources?: any;
  } = {};

  constructor(_config: DashboardConfig = {}) {}

  /**
   * Initialize and render dashboard
   */
  render(): void {
    // Create screen
    this.screen = blessed.screen({
      smartCSR: true,
      title: 'AI Shell - Performance Dashboard'
    });

    // Create grid layout
    this.grid = new contrib.grid({
      rows: 12,
      cols: 12,
      screen: this.screen
    });

    // Create widgets
    this.createWidgets();

    // Handle keyboard
    this.screen.key(['escape', 'q', 'C-c'], () => {
      this.destroy();
      process.exit(0);
    });

    // Initial render
    this.screen.render();
  }

  /**
   * Update dashboard with new metrics
   */
  updateMetrics(metrics: PerformanceMetrics): void {
    if (!this.screen) return;

    // Update metrics box
    if (this.widgets.metrics) {
      const content = this.formatMetrics(metrics);
      this.widgets.metrics.setContent(content);
    }

    // Update QPS line chart
    if (this.widgets.qpsLine) {
      // Add data point
      // Note: blessed-contrib has specific API for updating charts
    }

    // Update resource gauges
    if (this.widgets.resources) {
      const content = this.formatResources(metrics);
      this.widgets.resources.setContent(content);
    }

    this.screen.render();
  }

  /**
   * Update query log
   */
  updateQueryLog(queries: QueryLog[]): void {
    if (!this.screen || !this.widgets.queryLog) return;

    const rows = queries.slice(0, 10).map((q) => [
      new Date(q.timestamp).toLocaleTimeString(),
      `${q.duration}ms`,
      q.query.substring(0, 50) + (q.query.length > 50 ? '...' : '')
    ]);

    this.widgets.queryLog.setData({
      headers: ['Time', 'Duration', 'Query'],
      data: rows
    });

    this.screen.render();
  }

  /**
   * Update slow queries
   */
  updateSlowQueries(queries: any[]): void {
    if (!this.screen || !this.widgets.slowQueries) return;

    const content = queries
      .slice(0, 5)
      .map((q, i) => `${i + 1}. ${q.executionTime}ms - ${q.query.substring(0, 40)}...`)
      .join('\n');

    this.widgets.slowQueries.setContent(content || 'No slow queries');
    this.screen.render();
  }

  /**
   * Create dashboard widgets
   */
  private createWidgets(): void {
    if (!this.grid) return;

    // Metrics box (top left)
    this.widgets.metrics = this.grid.set(0, 0, 4, 6, blessed.box, {
      label: '📊 Performance Metrics',
      content: 'Loading...',
      tags: true,
      border: { type: 'line' },
      style: {
        fg: 'white',
        border: { fg: 'cyan' }
      }
    });

    // Resources box (top right)
    this.widgets.resources = this.grid.set(0, 6, 4, 6, blessed.box, {
      label: '💻 System Resources',
      content: 'Loading...',
      tags: true,
      border: { type: 'line' },
      style: {
        fg: 'white',
        border: { fg: 'cyan' }
      }
    });

    // QPS line chart (middle)
    this.widgets.qpsLine = this.grid.set(4, 0, 4, 12, contrib.line, {
      label: '⚡ Queries Per Second',
      showLegend: true,
      legend: { width: 12 },
      style: {
        line: 'yellow',
        text: 'green',
        baseline: 'white'
      }
    });

    // Query log table (bottom left)
    this.widgets.queryLog = this.grid.set(8, 0, 4, 7, contrib.table, {
      label: '📝 Recent Queries',
      keys: true,
      fg: 'white',
      selectedFg: 'white',
      selectedBg: 'blue',
      interactive: false,
      columnSpacing: 2,
      columnWidth: [10, 10, 50]
    });

    // Slow queries box (bottom right)
    this.widgets.slowQueries = this.grid.set(8, 7, 4, 5, blessed.box, {
      label: '⚠️  Slow Queries',
      content: 'No slow queries',
      tags: true,
      border: { type: 'line' },
      style: {
        fg: 'white',
        border: { fg: 'yellow' }
      },
      scrollable: true,
      alwaysScroll: true,
      scrollbar: {
        ch: ' ',
        style: { bg: 'yellow' }
      }
    });
  }

  /**
   * Format metrics for display
   */
  private formatMetrics(metrics: PerformanceMetrics): string {
    const qpsColor = metrics.queriesPerSecond > 100 ? 'red' : 'green';
    const queryTimeColor = metrics.averageQueryTime > 500 ? 'red' : 'green';
    const cacheColor = metrics.cacheHitRate < 0.5 ? 'red' : 'green';

    return `
{cyan-fg}Active Connections:{/cyan-fg} ${metrics.activeConnections}

{cyan-fg}Queries/Second:{/cyan-fg} {${qpsColor}-fg}${metrics.queriesPerSecond.toFixed(2)}{/${qpsColor}-fg}

{cyan-fg}Avg Query Time:{/cyan-fg} {${queryTimeColor}-fg}${metrics.averageQueryTime.toFixed(2)}ms{/${queryTimeColor}-fg}

{cyan-fg}Slow Queries:{/cyan-fg} ${metrics.slowQueriesCount > 0 ? `{red-fg}${metrics.slowQueriesCount}{/red-fg}` : `{green-fg}0{/green-fg}`}

{cyan-fg}Cache Hit Rate:{/cyan-fg} {${cacheColor}-fg}${(metrics.cacheHitRate * 100).toFixed(1)}%{/${cacheColor}-fg}

{cyan-fg}Database Size:{/cyan-fg} ${this.formatBytes(metrics.databaseSize)}

{cyan-fg}Growth Rate:{/cyan-fg} ${this.formatBytes(metrics.growthRate)}/day
    `.trim();
  }

  /**
   * Format resource usage
   */
  private formatResources(metrics: PerformanceMetrics): string {
    const cpuColor = metrics.cpuUsage > 80 ? 'red' : metrics.cpuUsage > 60 ? 'yellow' : 'green';
    const memColor = metrics.memoryUsage > 90 ? 'red' : metrics.memoryUsage > 70 ? 'yellow' : 'green';
    const lockColor = metrics.lockWaits > 10 ? 'red' : metrics.lockWaits > 0 ? 'yellow' : 'green';

    return `
{cyan-fg}CPU Usage:{/cyan-fg}
{${cpuColor}-fg}${this.createBar(metrics.cpuUsage, 100)}{/${cpuColor}-fg} ${metrics.cpuUsage.toFixed(1)}%

{cyan-fg}Memory Usage:{/cyan-fg}
{${memColor}-fg}${this.createBar(metrics.memoryUsage, 100)}{/${memColor}-fg} ${metrics.memoryUsage.toFixed(1)}%

{cyan-fg}Lock Waits:{/cyan-fg} {${lockColor}-fg}${metrics.lockWaits}{/${lockColor}-fg}

{cyan-fg}Timestamp:{/cyan-fg}
${new Date(metrics.timestamp).toLocaleString()}
    `.trim();
  }

  /**
   * Create ASCII progress bar
   */
  private createBar(value: number, max: number, width: number = 20): string {
    const filled = Math.floor((value / max) * width);
    const empty = width - filled;
    return '█'.repeat(filled) + '░'.repeat(empty);
  }

  /**
   * Format bytes
   */
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

  /**
   * Destroy dashboard
   */
  destroy(): void {
    if (this.screen) {
      this.screen.destroy();
      this.screen = undefined;
    }
  }
}
