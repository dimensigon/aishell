/**
 * Terminal Dashboard UI
 * Beautiful terminal dashboard using blessed (pure blessed implementation)
 */

import * as blessed from 'blessed';
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
  private widgets: {
    metrics?: blessed.Widgets.BoxElement;
    qpsLine?: blessed.Widgets.BoxElement;
    queryLog?: blessed.Widgets.BoxElement;
    slowQueries?: blessed.Widgets.BoxElement;
    resources?: blessed.Widgets.BoxElement;
  } = {};
  private qpsData: Array<{ x: string; y: number }> = [];

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
      this.qpsData.push({
        x: new Date().toLocaleTimeString(),
        y: metrics.queriesPerSecond
      });
      // Keep last 20 data points
      if (this.qpsData.length > 20) {
        this.qpsData.shift();
      }
      const chartContent = this.formatLineChart(this.qpsData);
      this.widgets.qpsLine.setContent(chartContent);
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

    const content = queries.slice(0, 10).map((q, i) => {
      const time = new Date(q.timestamp).toLocaleTimeString();
      const duration = `${q.duration}ms`;
      const query = q.query.substring(0, 40) + (q.query.length > 40 ? '...' : '');
      return `${i + 1}. ${time} | ${duration.padEnd(8)} | ${query}`;
    }).join('\n');

    this.widgets.queryLog.setContent(content || 'No queries yet');
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
    if (!this.screen) return;

    // Metrics box (top left)
    this.widgets.metrics = blessed.box({
      parent: this.screen,
      top: 0,
      left: 0,
      width: '50%',
      height: '33%',
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
    this.widgets.resources = blessed.box({
      parent: this.screen,
      top: 0,
      left: '50%',
      width: '50%',
      height: '33%',
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
    this.widgets.qpsLine = blessed.box({
      parent: this.screen,
      top: '33%',
      left: 0,
      width: '100%',
      height: '33%',
      label: '⚡ Queries Per Second',
      content: 'No data yet',
      tags: true,
      border: { type: 'line' },
      style: {
        fg: 'yellow',
        border: { fg: 'yellow' }
      }
    });

    // Query log table (bottom left)
    this.widgets.queryLog = blessed.box({
      parent: this.screen,
      top: '66%',
      left: 0,
      width: '60%',
      height: '34%',
      label: '📝 Recent Queries',
      content: 'No queries yet',
      tags: true,
      border: { type: 'line' },
      style: {
        fg: 'white',
        border: { fg: 'green' }
      },
      scrollable: true,
      alwaysScroll: true,
      scrollbar: {
        ch: ' ',
        style: { bg: 'green' }
      }
    });

    // Slow queries box (bottom right)
    this.widgets.slowQueries = blessed.box({
      parent: this.screen,
      top: '66%',
      left: '60%',
      width: '40%',
      height: '34%',
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
   * Format line chart data as ASCII art
   */
  private formatLineChart(data: Array<{ x: string; y: number }>): string {
    if (data.length === 0) return 'No data yet';

    const maxY = Math.max(...data.map(d => d.y), 1);
    const height = 10;
    const width = data.length;

    let chart = '';
    for (let row = height; row >= 0; row--) {
      const threshold = (row / height) * maxY;
      let line = `${threshold.toFixed(0).padStart(4)} │ `;

      for (let col = 0; col < width; col++) {
        const value = data[col].y;
        if (value >= threshold) {
          line += '█';
        } else if (value >= threshold - (maxY / height / 2)) {
          line += '▄';
        } else {
          line += ' ';
        }
      }
      chart += line + '\n';
    }

    chart += '     └' + '─'.repeat(width) + '\n';
    chart += '      ' + data.map(d => d.x.substring(0, 5)).join('').substring(0, width);

    return chart;
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
