/**
 * Enhanced Monitoring Dashboard with Real-Time TUI
 * Production-ready dashboard with comprehensive metrics, alerts, and visualizations
 * Priority: P3 Feature
 */

import * as blessed from 'blessed';
import { EventEmitter } from 'eventemitter3';
import * as fs from 'fs/promises';
import * as path from 'path';
import { PerformanceMonitor, PerformanceMetrics } from './performance-monitor';
import { HealthMonitor } from './health-monitor';
import { QueryLogger, QueryLog } from './query-logger';
import { StateManager } from '../core/state-manager';

/**
 * Dashboard layout configuration
 */
export interface DashboardLayout {
  name: string;
  description: string;
  panels: {
    connections?: { position: PanelPosition; size: PanelSize };
    performance?: { position: PanelPosition; size: PanelSize };
    alerts?: { position: PanelPosition; size: PanelSize };
    queryLog?: { position: PanelPosition; size: PanelSize };
    systemHealth?: { position: PanelPosition; size: PanelSize };
    charts?: { position: PanelPosition; size: PanelSize };
  };
}

interface PanelPosition {
  top: number | string;
  left: number | string;
}

interface PanelSize {
  width: number | string;
  height: number | string;
}

/**
 * Dashboard configuration
 */
export interface DashboardConfig {
  refreshInterval?: number; // milliseconds
  layout?: string;
  theme?: 'dark' | 'light' | 'ocean' | 'forest';
  showTimestamps?: boolean;
  enableAlerts?: boolean;
  historySize?: number;
  exportPath?: string;
}

/**
 * Alert with severity
 */
export interface DashboardAlert {
  id: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  timestamp: number;
  source: string;
  resolved: boolean;
}

/**
 * Chart data point
 */
interface ChartDataPoint {
  timestamp: number;
  value: number;
  label?: string;
}

/**
 * Dashboard statistics
 */
interface DashboardStats {
  uptime: number;
  totalQueries: number;
  activeConnections: number;
  avgResponseTime: number;
  errorRate: number;
  cacheHitRate: number;
}

/**
 * Enhanced Dashboard Events
 */
interface DashboardEvents {
  started: () => void;
  stopped: () => void;
  layoutChanged: (layout: string) => void;
  exported: (filepath: string) => void;
  error: (error: Error) => void;
}

/**
 * Enhanced Monitoring Dashboard
 * Real-time TUI with metrics, alerts, and visualizations
 */
export class EnhancedDashboard extends EventEmitter<DashboardEvents> {
  private screen?: blessed.Widgets.Screen;
  private widgets: Map<string, blessed.Widgets.BlessedElement> = new Map();
  private panels: Map<string, DashboardPanel> = new Map();

  private config: Required<DashboardConfig>;
  private currentLayout: DashboardLayout;
  private refreshInterval?: NodeJS.Timeout;
  private isRunning = false;

  private alerts: DashboardAlert[] = [];
  private metricsHistory: Map<string, ChartDataPoint[]> = new Map();
  private _stats: DashboardStats;
  private startTime: number = Date.now();

  // Panel focus management
  private focusedPanelIndex = 0;
  private panelList: string[] = [];

  // Getter for stats that always returns current uptime
  private get stats(): DashboardStats {
    return {
      ...this._stats,
      uptime: this.isRunning ? Date.now() - this.startTime : this._stats.uptime
    };
  }

  // Setter for stats
  private set stats(value: DashboardStats) {
    this._stats = value;
  }

  constructor(
    private performanceMonitor: PerformanceMonitor,
    private healthMonitor: HealthMonitor,
    private queryLogger: QueryLogger,
    private stateManager: StateManager,
    config: DashboardConfig = {}
  ) {
    super();

    this.config = {
      refreshInterval: config.refreshInterval || 2000,
      layout: config.layout || 'default',
      theme: config.theme || 'dark',
      showTimestamps: config.showTimestamps !== false,
      enableAlerts: config.enableAlerts !== false,
      historySize: config.historySize || 100,
      exportPath: config.exportPath || './dashboard-exports'
    };

    this.currentLayout = this.getLayout(this.config.layout);

    this._stats = {
      uptime: 0,
      totalQueries: 0,
      activeConnections: 0,
      avgResponseTime: 0,
      errorRate: 0,
      cacheHitRate: 0
    };

    this.setupEventListeners();
  }

  /**
   * Start the dashboard
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      throw new Error('Dashboard is already running');
    }

    this.isRunning = true;
    this.startTime = Date.now();

    // Initialize stats immediately
    try {
      await this.updateStats();
    } catch (error) {
      // Emit error but continue startup
      this.emit('error', error as Error);
    }

    // Initialize blessed screen
    this.initializeScreen();

    // Create panels based on layout
    this.createPanels();

    // Setup keyboard navigation
    this.setupKeyboardHandling();

    // Start refresh interval
    this.startRefreshLoop();

    // Initial render
    await this.refresh();

    this.emit('started');
  }

  /**
   * Stop the dashboard
   */
  stop(): void {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;

    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = undefined;
    }

    if (this.screen) {
      this.screen.destroy();
      this.screen = undefined;
    }

    this.widgets.clear();
    this.panels.clear();

    this.emit('stopped');
  }

  /**
   * Change dashboard layout
   */
  async changeLayout(layoutName: string): Promise<void> {
    const newLayout = this.getLayout(layoutName);

    this.currentLayout = newLayout;
    this.config.layout = layoutName;

    // Recreate panels
    this.clearPanels();
    this.createPanels();

    await this.refresh();

    this.emit('layoutChanged', layoutName);
  }

  /**
   * Export dashboard snapshot
   */
  async export(filename?: string, format?: 'json' | 'csv' | 'html' | 'pdf'): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

    // Determine format from filename or use default
    const exportFormat = format || this.getFormatFromFilename(filename) || 'json';
    const ext = this.getExtensionForFormat(exportFormat);

    const filepath = path.join(
      this.config.exportPath,
      filename || `dashboard-snapshot-${timestamp}.${ext}`
    );

    const snapshot = {
      timestamp: Date.now(),
      layout: this.config.layout,
      stats: this.stats,
      alerts: this.alerts.filter(a => !a.resolved),
      metrics: {
        current: await this.getCurrentMetrics(),
        history: Object.fromEntries(this.metricsHistory)
      },
      queryHistory: await this.queryLogger.getHistory(50)
    };

    await fs.mkdir(path.dirname(filepath), { recursive: true });

    // Export in the specified format
    let content: string;
    switch (exportFormat) {
      case 'json':
        content = JSON.stringify(snapshot, null, 2);
        break;
      case 'csv':
        content = this.convertToCSV(snapshot);
        break;
      case 'html':
        content = this.convertToHTML(snapshot);
        break;
      case 'pdf':
        content = this.convertToPDF(snapshot);
        break;
      default:
        throw new Error(`Unsupported export format: ${exportFormat}`);
    }

    await fs.writeFile(filepath, content, 'utf-8');

    this.emit('exported', filepath);

    return filepath;
  }

  /**
   * Get format from filename extension
   */
  private getFormatFromFilename(filename?: string): 'json' | 'csv' | 'html' | 'pdf' | null {
    if (!filename) return null;

    const ext = path.extname(filename).toLowerCase().slice(1);
    if (['json', 'csv', 'html', 'pdf'].includes(ext)) {
      return ext as 'json' | 'csv' | 'html' | 'pdf';
    }

    return null;
  }

  /**
   * Get file extension for format
   */
  private getExtensionForFormat(format: 'json' | 'csv' | 'html' | 'pdf'): string {
    return format;
  }

  /**
   * Convert snapshot to CSV format
   */
  private convertToCSV(snapshot: any): string {
    const lines: string[] = [];

    // Header
    lines.push('Dashboard Export - ' + new Date(snapshot.timestamp).toISOString());
    lines.push('');

    // Stats
    lines.push('Statistics');
    lines.push('Metric,Value');
    lines.push(`Uptime,${snapshot.stats.uptime}`);
    lines.push(`Total Queries,${snapshot.stats.totalQueries}`);
    lines.push(`Active Connections,${snapshot.stats.activeConnections}`);
    lines.push(`Avg Response Time,${snapshot.stats.avgResponseTime}`);
    lines.push(`Error Rate,${snapshot.stats.errorRate}`);
    lines.push(`Cache Hit Rate,${snapshot.stats.cacheHitRate}`);
    lines.push('');

    // Alerts
    lines.push('Active Alerts');
    lines.push('Severity,Message,Source,Timestamp');
    snapshot.alerts.forEach((alert: DashboardAlert) => {
      const time = new Date(alert.timestamp).toISOString();
      lines.push(`${alert.severity},"${alert.message}",${alert.source},${time}`);
    });
    lines.push('');

    // Recent Queries
    if (snapshot.queryHistory?.logs) {
      lines.push('Recent Queries');
      lines.push('Query,Duration,Timestamp,Error');
      snapshot.queryHistory.logs.slice(0, 20).forEach((q: any) => {
        const time = new Date(q.timestamp).toISOString();
        const error = q.result?.error ? 'Yes' : 'No';
        lines.push(`"${q.query.replace(/"/g, '""')}",${q.duration},${time},${error}`);
      });
    }

    return lines.join('\n');
  }

  /**
   * Convert snapshot to HTML format
   */
  private convertToHTML(snapshot: any): string {
    const uptime = this.formatUptime(snapshot.stats.uptime);

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Export - ${new Date(snapshot.timestamp).toISOString()}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    h1 { color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }
    h2 { color: #555; margin-top: 30px; border-bottom: 2px solid #ddd; padding-bottom: 8px; }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }
    .stat-card { background: #f9f9f9; padding: 15px; border-radius: 6px; border-left: 4px solid #4CAF50; }
    .stat-label { font-weight: bold; color: #666; font-size: 14px; }
    .stat-value { font-size: 24px; color: #333; margin-top: 5px; }
    .alert { padding: 12px; margin: 10px 0; border-radius: 4px; border-left: 4px solid; }
    .alert.critical { background: #ffebee; border-color: #f44336; }
    .alert.warning { background: #fff3e0; border-color: #ff9800; }
    .alert.info { background: #e3f2fd; border-color: #2196F3; }
    table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
    th { background: #4CAF50; color: white; font-weight: bold; }
    tr:hover { background: #f5f5f5; }
    .timestamp { color: #999; font-size: 14px; }
    .error { color: #f44336; font-weight: bold; }
  </style>
</head>
<body>
  <div class="container">
    <h1>📊 Dashboard Export</h1>
    <p class="timestamp">Exported: ${new Date(snapshot.timestamp).toLocaleString()}</p>

    <h2>📈 Statistics</h2>
    <div class="stats">
      <div class="stat-card">
        <div class="stat-label">Uptime</div>
        <div class="stat-value">${uptime}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Queries</div>
        <div class="stat-value">${snapshot.stats.totalQueries.toLocaleString()}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Active Connections</div>
        <div class="stat-value">${snapshot.stats.activeConnections}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Avg Response Time</div>
        <div class="stat-value">${snapshot.stats.avgResponseTime.toFixed(0)}ms</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Error Rate</div>
        <div class="stat-value">${(snapshot.stats.errorRate * 100).toFixed(2)}%</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Cache Hit Rate</div>
        <div class="stat-value">${(snapshot.stats.cacheHitRate * 100).toFixed(1)}%</div>
      </div>
    </div>

    <h2>🚨 Active Alerts</h2>
    ${snapshot.alerts.length === 0
      ? '<p>✅ No active alerts</p>'
      : snapshot.alerts.map((alert: DashboardAlert) => `
        <div class="alert ${alert.severity}">
          <strong>${alert.severity.toUpperCase()}</strong> - ${alert.message}
          <br><span class="timestamp">${new Date(alert.timestamp).toLocaleString()} | Source: ${alert.source}</span>
        </div>
      `).join('')
    }

    <h2>📝 Recent Queries</h2>
    <table>
      <thead>
        <tr>
          <th>Query</th>
          <th>Duration</th>
          <th>Timestamp</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        ${snapshot.queryHistory?.logs?.slice(0, 20).map((q: any) => `
          <tr>
            <td><code>${this.escapeHtml(q.query.substring(0, 80))}${q.query.length > 80 ? '...' : ''}</code></td>
            <td>${q.duration.toFixed(0)}ms</td>
            <td class="timestamp">${new Date(q.timestamp).toLocaleString()}</td>
            <td>${q.result?.error ? '<span class="error">Error</span>' : '✅'}</td>
          </tr>
        `).join('') || '<tr><td colspan="4">No queries recorded</td></tr>'}
      </tbody>
    </table>

    <h2>📊 Current Metrics</h2>
    ${snapshot.metrics?.current ? `
      <table>
        <tr>
          <th>Metric</th>
          <th>Value</th>
        </tr>
        <tr>
          <td>Queries per Second</td>
          <td>${snapshot.metrics.current.queriesPerSecond.toFixed(2)}</td>
        </tr>
        <tr>
          <td>Average Query Time</td>
          <td>${snapshot.metrics.current.averageQueryTime.toFixed(2)}ms</td>
        </tr>
        <tr>
          <td>Slow Queries</td>
          <td>${snapshot.metrics.current.slowQueriesCount}</td>
        </tr>
        <tr>
          <td>Cache Hit Rate</td>
          <td>${(snapshot.metrics.current.cacheHitRate * 100).toFixed(1)}%</td>
        </tr>
        <tr>
          <td>CPU Usage</td>
          <td>${snapshot.metrics.current.cpuUsage.toFixed(1)}%</td>
        </tr>
        <tr>
          <td>Memory Usage</td>
          <td>${snapshot.metrics.current.memoryUsage.toFixed(1)}%</td>
        </tr>
      </table>
    ` : '<p>No current metrics available</p>'}
  </div>
</body>
</html>`;

    return html;
  }

  /**
   * Convert snapshot to PDF format (as text representation)
   * Note: True PDF generation would require a library like pdfkit
   */
  private convertToPDF(snapshot: any): string {
    // For now, we'll create a text-based PDF-like format
    // In production, you'd use a library like pdfkit or puppeteer
    const lines: string[] = [];

    lines.push('='.repeat(80));
    lines.push('DASHBOARD EXPORT REPORT');
    lines.push(`Generated: ${new Date(snapshot.timestamp).toLocaleString()}`);
    lines.push('='.repeat(80));
    lines.push('');

    // Stats
    lines.push('STATISTICS');
    lines.push('-'.repeat(80));
    lines.push(`Uptime:              ${this.formatUptime(snapshot.stats.uptime)}`);
    lines.push(`Total Queries:       ${snapshot.stats.totalQueries.toLocaleString()}`);
    lines.push(`Active Connections:  ${snapshot.stats.activeConnections}`);
    lines.push(`Avg Response Time:   ${snapshot.stats.avgResponseTime.toFixed(0)}ms`);
    lines.push(`Error Rate:          ${(snapshot.stats.errorRate * 100).toFixed(2)}%`);
    lines.push(`Cache Hit Rate:      ${(snapshot.stats.cacheHitRate * 100).toFixed(1)}%`);
    lines.push('');

    // Alerts
    lines.push('ACTIVE ALERTS');
    lines.push('-'.repeat(80));
    if (snapshot.alerts.length === 0) {
      lines.push('✓ No active alerts');
    } else {
      snapshot.alerts.forEach((alert: DashboardAlert, i: number) => {
        lines.push(`${i + 1}. [${alert.severity.toUpperCase()}] ${alert.message}`);
        lines.push(`   Source: ${alert.source} | Time: ${new Date(alert.timestamp).toLocaleString()}`);
        lines.push('');
      });
    }
    lines.push('');

    // Recent Queries
    lines.push('RECENT QUERIES');
    lines.push('-'.repeat(80));
    if (snapshot.queryHistory?.logs) {
      snapshot.queryHistory.logs.slice(0, 15).forEach((q: any, i: number) => {
        const status = q.result?.error ? '[ERROR]' : '[OK]';
        lines.push(`${i + 1}. ${status} ${q.duration.toFixed(0)}ms`);
        lines.push(`   ${q.query.substring(0, 70)}${q.query.length > 70 ? '...' : ''}`);
        lines.push(`   ${new Date(q.timestamp).toLocaleString()}`);
        lines.push('');
      });
    } else {
      lines.push('No queries recorded');
    }
    lines.push('');

    // Current Metrics
    if (snapshot.metrics?.current) {
      lines.push('CURRENT METRICS');
      lines.push('-'.repeat(80));
      lines.push(`Queries/Second:      ${snapshot.metrics.current.queriesPerSecond.toFixed(2)}`);
      lines.push(`Avg Query Time:      ${snapshot.metrics.current.averageQueryTime.toFixed(2)}ms`);
      lines.push(`Slow Queries:        ${snapshot.metrics.current.slowQueriesCount}`);
      lines.push(`Cache Hit Rate:      ${(snapshot.metrics.current.cacheHitRate * 100).toFixed(1)}%`);
      lines.push(`CPU Usage:           ${snapshot.metrics.current.cpuUsage.toFixed(1)}%`);
      lines.push(`Memory Usage:        ${snapshot.metrics.current.memoryUsage.toFixed(1)}%`);
    }

    lines.push('');
    lines.push('='.repeat(80));
    lines.push('END OF REPORT');
    lines.push('='.repeat(80));

    return lines.join('\n');
  }

  /**
   * Format uptime duration
   */
  private formatUptime(milliseconds: number): string {
    const seconds = Math.floor(milliseconds / 1000);
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return `${hours}h ${minutes}m ${secs}s`;
  }

  /**
   * Escape HTML special characters
   */
  private escapeHtml(text: string): string {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }

  /**
   * Configure dashboard
   */
  configure(config: Partial<DashboardConfig>): void {
    this.config = { ...this.config, ...config };

    if (config.layout) {
      this.currentLayout = this.getLayout(config.layout);
    }
  }

  /**
   * Add custom alert
   */
  addAlert(alert: Omit<DashboardAlert, 'id' | 'timestamp'>): void {
    const dashboardAlert: DashboardAlert = {
      ...alert,
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now()
    };

    this.alerts.unshift(dashboardAlert);

    // Keep only recent alerts
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(0, 100);
    }
  }

  /**
   * Initialize blessed screen
   */
  private initializeScreen(): void {
    this.screen = blessed.screen({
      smartCSR: true,
      title: 'AI Shell - Enhanced Monitoring Dashboard',
      fullUnicode: true,
      dockBorders: true
    });

    // Apply theme
    this.applyTheme();
  }

  /**
   * Create dashboard panels
   */
  private createPanels(): void {
    if (!this.screen) return;

    this.panelList = [];

    // Create panels based on current layout
    const layout = this.currentLayout;

    if (layout.panels.connections) {
      this.createConnectionPanel(layout.panels.connections);
      this.panelList.push('connections');
    }

    if (layout.panels.performance) {
      this.createPerformancePanel(layout.panels.performance);
      this.panelList.push('performance');
    }

    if (layout.panels.alerts) {
      this.createAlertsPanel(layout.panels.alerts);
      this.panelList.push('alerts');
    }

    if (layout.panels.queryLog) {
      this.createQueryLogPanel(layout.panels.queryLog);
      this.panelList.push('queryLog');
    }

    if (layout.panels.systemHealth) {
      this.createSystemHealthPanel(layout.panels.systemHealth);
      this.panelList.push('systemHealth');
    }

    if (layout.panels.charts) {
      this.createChartsPanel(layout.panels.charts);
      this.panelList.push('charts');
    }

    // Create help panel
    this.createHelpPanel();

    // Set initial focus
    this.updateFocus();
  }

  /**
   * Create connection panel
   */
  private createConnectionPanel(config: { position: PanelPosition; size: PanelSize }): void {
    const panel = new ConnectionPanel(this.screen!, config.position, config.size, this.config.theme);
    this.panels.set('connections', panel);
  }

  /**
   * Create performance panel
   */
  private createPerformancePanel(config: { position: PanelPosition; size: PanelSize }): void {
    const panel = new PerformancePanel(this.screen!, config.position, config.size, this.config.theme);
    this.panels.set('performance', panel);
  }

  /**
   * Create alerts panel
   */
  private createAlertsPanel(config: { position: PanelPosition; size: PanelSize }): void {
    const panel = new AlertsPanel(this.screen!, config.position, config.size, this.config.theme);
    this.panels.set('alerts', panel);
  }

  /**
   * Create query log panel
   */
  private createQueryLogPanel(config: { position: PanelPosition; size: PanelSize }): void {
    const panel = new QueryLogPanel(this.screen!, config.position, config.size, this.config.theme);
    this.panels.set('queryLog', panel);
  }

  /**
   * Create system health panel
   */
  private createSystemHealthPanel(config: { position: PanelPosition; size: PanelSize }): void {
    const panel = new SystemHealthPanel(this.screen!, config.position, config.size, this.config.theme);
    this.panels.set('systemHealth', panel);
  }

  /**
   * Create charts panel
   */
  private createChartsPanel(config: { position: PanelPosition; size: PanelSize }): void {
    const panel = new ChartsPanel(this.screen!, config.position, config.size, this.config.theme);
    this.panels.set('charts', panel);
  }

  /**
   * Create help panel
   */
  private createHelpPanel(): void {
    const helpBox = blessed.box({
      parent: this.screen,
      bottom: 0,
      left: 0,
      width: '100%',
      height: 1,
      content: ' [Tab] Next Panel | [Shift+Tab] Prev | [L] Layout | [E] Export | [C] Configure | [Q] Quit ',
      style: {
        fg: 'white',
        bg: 'blue'
      }
    });

    this.widgets.set('help', helpBox);
  }

  /**
   * Setup keyboard handling
   */
  private setupKeyboardHandling(): void {
    if (!this.screen) return;

    // Quit
    this.screen.key(['q', 'C-c'], () => {
      this.stop();
      process.exit(0);
    });

    // Tab navigation
    this.screen.key(['tab'], () => {
      this.focusedPanelIndex = (this.focusedPanelIndex + 1) % this.panelList.length;
      this.updateFocus();
    });

    this.screen.key(['S-tab'], () => {
      this.focusedPanelIndex = (this.focusedPanelIndex - 1 + this.panelList.length) % this.panelList.length;
      this.updateFocus();
    });

    // Layout change
    this.screen.key(['l'], async () => {
      const layouts = ['default', 'compact', 'detailed', 'monitoring'];
      const currentIndex = layouts.indexOf(this.config.layout);
      const nextIndex = (currentIndex + 1) % layouts.length;
      await this.changeLayout(layouts[nextIndex]);
    });

    // Export
    this.screen.key(['e'], async () => {
      try {
        const filepath = await this.export();
        this.addAlert({
          severity: 'info',
          message: `Snapshot exported to ${filepath}`,
          source: 'dashboard',
          resolved: false
        });
      } catch (error) {
        this.addAlert({
          severity: 'critical',
          message: `Export failed: ${error}`,
          source: 'dashboard',
          resolved: false
        });
      }
    });

    // Refresh
    this.screen.key(['r'], async () => {
      await this.refresh();
    });

    // Scroll focused panel
    this.screen.key(['up', 'down', 'pageup', 'pagedown'], (ch, key) => {
      const focusedPanelName = this.panelList[this.focusedPanelIndex];
      const panel = this.panels.get(focusedPanelName);
      if (panel) {
        panel.handleScroll(key.name);
      }
    });
  }

  /**
   * Update panel focus
   */
  private updateFocus(): void {
    // Remove focus from all panels
    this.panels.forEach(panel => panel.setFocus(false));

    // Set focus on current panel
    const focusedPanelName = this.panelList[this.focusedPanelIndex];
    const panel = this.panels.get(focusedPanelName);
    if (panel) {
      panel.setFocus(true);
    }

    if (this.screen) {
      this.screen.render();
    }
  }

  /**
   * Start refresh loop
   */
  private startRefreshLoop(): void {
    this.refreshInterval = setInterval(async () => {
      await this.refresh();
    }, this.config.refreshInterval);
  }

  /**
   * Refresh dashboard data
   */
  private async refresh(): Promise<void> {
    if (!this.screen || !this.isRunning) return;

    try {
      // Update stats
      await this.updateStats();

      // Update all panels
      await Promise.all([
        this.updateConnectionPanel(),
        this.updatePerformancePanel(),
        this.updateAlertsPanel(),
        this.updateQueryLogPanel(),
        this.updateSystemHealthPanel(),
        this.updateChartsPanel()
      ]);

      // Render screen
      this.screen.render();
    } catch (error) {
      this.emit('error', error as Error);
    }
  }

  /**
   * Update dashboard statistics
   */
  private async updateStats(): Promise<void> {
    this._stats.uptime = Date.now() - this.startTime;

    const queryHistory = await this.queryLogger.getHistory(100);
    this._stats.totalQueries = queryHistory.total;

    const metrics = await this.getCurrentMetrics();
    if (metrics) {
      this._stats.activeConnections = metrics.activeConnections;
      this._stats.avgResponseTime = metrics.averageQueryTime;
      this._stats.cacheHitRate = metrics.cacheHitRate;

      const errorQueries = queryHistory.logs.filter(q => q.result?.error);
      this._stats.errorRate = queryHistory.logs.length > 0
        ? errorQueries.length / queryHistory.logs.length
        : 0;

      // Store metrics history
      this.recordMetric('qps', metrics.queriesPerSecond);
      this.recordMetric('avgQueryTime', metrics.averageQueryTime);
      this.recordMetric('cpu', metrics.cpuUsage);
      this.recordMetric('memory', metrics.memoryUsage);
    }
  }

  /**
   * Update connection panel
   */
  private async updateConnectionPanel(): Promise<void> {
    const panel = this.panels.get('connections') as ConnectionPanel;
    if (!panel) return;

    const poolStats = await this.performanceMonitor.connectionPool();
    const metrics = await this.getCurrentMetrics();

    panel.update({
      totalConnections: poolStats.totalConnections,
      activeConnections: metrics?.activeConnections || 0,
      idleConnections: poolStats.idleConnections,
      waitingQueries: poolStats.waitingQueries,
      avgWaitTime: poolStats.averageWaitTime,
      maxWaitTime: poolStats.maxWaitTime
    });
  }

  /**
   * Update performance panel
   */
  private async updatePerformancePanel(): Promise<void> {
    const panel = this.panels.get('performance') as PerformancePanel;
    if (!panel) return;

    const metrics = await this.getCurrentMetrics();
    if (!metrics) return;

    panel.update({
      qps: metrics.queriesPerSecond,
      avgQueryTime: metrics.averageQueryTime,
      slowQueries: metrics.slowQueriesCount,
      cacheHitRate: metrics.cacheHitRate,
      lockWaits: metrics.lockWaits
    });
  }

  /**
   * Update alerts panel
   */
  private async updateAlertsPanel(): Promise<void> {
    const panel = this.panels.get('alerts') as AlertsPanel;
    if (!panel) return;

    // Get active alerts
    const activeAlerts = this.alerts.filter(a => !a.resolved);

    panel.update(activeAlerts);
  }

  /**
   * Update query log panel
   */
  private async updateQueryLogPanel(): Promise<void> {
    const panel = this.panels.get('queryLog') as QueryLogPanel;
    if (!panel) return;

    const history = await this.queryLogger.getHistory(20);
    panel.update(history.logs);
  }

  /**
   * Update system health panel
   */
  private async updateSystemHealthPanel(): Promise<void> {
    const panel = this.panels.get('systemHealth') as SystemHealthPanel;
    if (!panel) return;

    const healthCheck = await this.healthMonitor.performHealthCheck();

    panel.update({
      status: this.getOverallHealthStatus(healthCheck),
      uptime: this.stats.uptime,
      cpu: healthCheck.cpuUsage?.value || 0,
      memory: healthCheck.memoryUsage?.value || 0,
      responseTime: healthCheck.responseTime.value,
      errorRate: this.stats.errorRate
    });
  }

  /**
   * Update charts panel
   */
  private async updateChartsPanel(): Promise<void> {
    const panel = this.panels.get('charts') as ChartsPanel;
    if (!panel) return;

    panel.update({
      qps: this.metricsHistory.get('qps') || [],
      avgQueryTime: this.metricsHistory.get('avgQueryTime') || [],
      cpu: this.metricsHistory.get('cpu') || [],
      memory: this.metricsHistory.get('memory') || []
    });
  }

  /**
   * Get current performance metrics
   */
  private async getCurrentMetrics(): Promise<PerformanceMetrics | null> {
    const latest = this.performanceMonitor.getHistory(1);
    return latest.length > 0 ? latest[0] : null;
  }

  /**
   * Record metric for history
   */
  private recordMetric(name: string, value: number): void {
    const history = this.metricsHistory.get(name) || [];

    history.push({
      timestamp: Date.now(),
      value
    });

    // Keep only recent history
    if (history.length > this.config.historySize) {
      history.shift();
    }

    this.metricsHistory.set(name, history);
  }

  /**
   * Get overall health status
   */
  private getOverallHealthStatus(healthCheck: any): 'healthy' | 'warning' | 'critical' {
    const metrics = Object.values(healthCheck).filter(m => m && typeof m === 'object');
    const statuses = metrics.map((m: any) => m.status);

    if (statuses.includes('critical')) return 'critical';
    if (statuses.includes('warning')) return 'warning';
    return 'healthy';
  }

  /**
   * Clear all panels
   */
  private clearPanels(): void {
    this.panels.forEach(panel => panel.destroy());
    this.panels.clear();
    this.widgets.forEach((widget, key) => {
      if (key !== 'help') {
        widget.destroy();
      }
    });
  }

  /**
   * Apply theme to screen
   */
  private applyTheme(): void {
    // Theme is applied at widget level via blessed
    // This method can be extended for global theme settings
  }

  /**
   * Setup event listeners
   */
  private setupEventListeners(): void {
    // Performance monitor events
    this.performanceMonitor.on('alert', (type, message, severity) => {
      // Map 'error' to 'critical' for dashboard alerts
      const dashboardSeverity = severity === 'error' ? 'critical' : severity as 'info' | 'warning' | 'critical';
      this.addAlert({
        severity: dashboardSeverity,
        message: `${type}: ${message}`,
        source: 'performance',
        resolved: false
      });
    });

    // Query logger events
    this.queryLogger.on('slowQuery', (log) => {
      this.addAlert({
        severity: 'warning',
        message: `Slow query detected: ${log.duration}ms`,
        source: 'query',
        resolved: false
      });
    });
  }

  /**
   * Get layout by name
   */
  private getLayout(name: string): DashboardLayout {
    const layouts: Record<string, DashboardLayout> = {
      default: {
        name: 'default',
        description: 'Standard layout with all panels',
        panels: {
          connections: {
            position: { top: 0, left: 0 },
            size: { width: '33%', height: '40%' }
          },
          performance: {
            position: { top: 0, left: '33%' },
            size: { width: '34%', height: '40%' }
          },
          systemHealth: {
            position: { top: 0, left: '67%' },
            size: { width: '33%', height: '40%' }
          },
          alerts: {
            position: { top: '40%', left: 0 },
            size: { width: '50%', height: '30%' }
          },
          queryLog: {
            position: { top: '40%', left: '50%' },
            size: { width: '50%', height: '30%' }
          },
          charts: {
            position: { top: '70%', left: 0 },
            size: { width: '100%', height: '29%' }
          }
        }
      },
      compact: {
        name: 'compact',
        description: 'Compact layout for small screens',
        panels: {
          performance: {
            position: { top: 0, left: 0 },
            size: { width: '50%', height: '50%' }
          },
          systemHealth: {
            position: { top: 0, left: '50%' },
            size: { width: '50%', height: '50%' }
          },
          alerts: {
            position: { top: '50%', left: 0 },
            size: { width: '100%', height: '49%' }
          }
        }
      },
      detailed: {
        name: 'detailed',
        description: 'Detailed view with charts and metrics',
        panels: {
          charts: {
            position: { top: 0, left: 0 },
            size: { width: '60%', height: '50%' }
          },
          performance: {
            position: { top: 0, left: '60%' },
            size: { width: '40%', height: '25%' }
          },
          connections: {
            position: { top: '25%', left: '60%' },
            size: { width: '40%', height: '25%' }
          },
          queryLog: {
            position: { top: '50%', left: 0 },
            size: { width: '70%', height: '49%' }
          },
          alerts: {
            position: { top: '50%', left: '70%' },
            size: { width: '30%', height: '49%' }
          }
        }
      },
      monitoring: {
        name: 'monitoring',
        description: 'Focus on real-time monitoring',
        panels: {
          charts: {
            position: { top: 0, left: 0 },
            size: { width: '100%', height: '50%' }
          },
          performance: {
            position: { top: '50%', left: 0 },
            size: { width: '33%', height: '49%' }
          },
          connections: {
            position: { top: '50%', left: '33%' },
            size: { width: '34%', height: '49%' }
          },
          systemHealth: {
            position: { top: '50%', left: '67%' },
            size: { width: '33%', height: '49%' }
          }
        }
      }
    };

    const layout = layouts[name];
    if (!layout) {
      throw new Error(`Layout '${name}' not found`);
    }

    return layout;
  }
}

/**
 * Base panel class
 */
abstract class DashboardPanel {
  protected box: blessed.Widgets.BoxElement;
  protected isFocused = false;

  constructor(
    protected screen: blessed.Widgets.Screen,
    protected title: string,
    position: PanelPosition,
    size: PanelSize,
    theme: string
  ) {
    this.box = blessed.box({
      parent: screen,
      top: position.top,
      left: position.left,
      width: size.width,
      height: size.height,
      label: ` ${title} `,
      content: '',
      tags: true,
      border: { type: 'line' },
      style: {
        fg: 'white',
        border: { fg: theme === 'light' ? 'blue' : 'cyan' }
      },
      scrollable: true,
      alwaysScroll: true,
      scrollbar: {
        ch: '█',
        style: { bg: 'blue' }
      }
    });
  }

  abstract update(data: any): void;

  setFocus(focused: boolean): void {
    this.isFocused = focused;
    if (this.box) {
      this.box.style.border = {
        fg: focused ? 'yellow' : 'cyan'
      } as any;
    }
  }

  handleScroll(direction: string): void {
    if (!this.box) return;

    switch (direction) {
      case 'up':
        this.box.scroll(-1);
        break;
      case 'down':
        this.box.scroll(1);
        break;
      case 'pageup':
        this.box.scroll(-10);
        break;
      case 'pagedown':
        this.box.scroll(10);
        break;
    }

    this.screen.render();
  }

  destroy(): void {
    if (this.box) {
      this.box.destroy();
    }
  }
}

/**
 * Connection Panel
 */
class ConnectionPanel extends DashboardPanel {
  constructor(
    screen: blessed.Widgets.Screen,
    position: PanelPosition,
    size: PanelSize,
    theme: string
  ) {
    super(screen, '🔗 Connection Pool', position, size, theme);
  }

  update(data: {
    totalConnections: number;
    activeConnections: number;
    idleConnections: number;
    waitingQueries: number;
    avgWaitTime: number;
    maxWaitTime: number;
  }): void {
    const activePercent = (data.activeConnections / data.totalConnections) * 100;
    const activeColor = activePercent > 80 ? 'red' : activePercent > 60 ? 'yellow' : 'green';

    const content = `
{cyan-fg}Total Connections:{/cyan-fg} ${data.totalConnections}

{cyan-fg}Active:{/cyan-fg} {${activeColor}-fg}${data.activeConnections}{/${activeColor}-fg} (${activePercent.toFixed(1)}%)
{cyan-fg}Idle:{/cyan-fg} {green-fg}${data.idleConnections}{/green-fg}
{cyan-fg}Waiting:{/cyan-fg} ${data.waitingQueries > 0 ? `{yellow-fg}${data.waitingQueries}{/yellow-fg}` : '0'}

{cyan-fg}Avg Wait Time:{/cyan-fg} ${data.avgWaitTime.toFixed(0)}ms
{cyan-fg}Max Wait Time:{/cyan-fg} ${data.maxWaitTime.toFixed(0)}ms

{cyan-fg}Pool Utilization:{/cyan-fg}
{${activeColor}-fg}${'█'.repeat(Math.floor(activePercent / 5))}{'░'.repeat(20 - Math.floor(activePercent / 5))}{/${activeColor}-fg}
    `.trim();

    this.box.setContent(content);
  }
}

/**
 * Performance Panel
 */
class PerformancePanel extends DashboardPanel {
  constructor(
    screen: blessed.Widgets.Screen,
    position: PanelPosition,
    size: PanelSize,
    theme: string
  ) {
    super(screen, '⚡ Performance Metrics', position, size, theme);
  }

  update(data: {
    qps: number;
    avgQueryTime: number;
    slowQueries: number;
    cacheHitRate: number;
    lockWaits: number;
  }): void {
    const qpsColor = data.qps > 100 ? 'red' : data.qps > 50 ? 'yellow' : 'green';
    const timeColor = data.avgQueryTime > 500 ? 'red' : data.avgQueryTime > 200 ? 'yellow' : 'green';
    const cacheColor = data.cacheHitRate < 0.5 ? 'red' : data.cacheHitRate < 0.7 ? 'yellow' : 'green';

    const content = `
{cyan-fg}Queries/Second:{/cyan-fg}
{${qpsColor}-fg}${data.qps.toFixed(2)}{/${qpsColor}-fg}

{cyan-fg}Avg Query Time:{/cyan-fg}
{${timeColor}-fg}${data.avgQueryTime.toFixed(2)}ms{/${timeColor}-fg}

{cyan-fg}Slow Queries:{/cyan-fg}
${data.slowQueries > 0 ? `{red-fg}${data.slowQueries}{/red-fg}` : '{green-fg}0{/green-fg}'}

{cyan-fg}Cache Hit Rate:{/cyan-fg}
{${cacheColor}-fg}${(data.cacheHitRate * 100).toFixed(1)}%{/${cacheColor}-fg}

{cyan-fg}Lock Waits:{/cyan-fg}
${data.lockWaits > 0 ? `{yellow-fg}${data.lockWaits}{/yellow-fg}` : '{green-fg}0{/green-fg}'}
    `.trim();

    this.box.setContent(content);
  }
}

/**
 * Alerts Panel
 */
class AlertsPanel extends DashboardPanel {
  constructor(
    screen: blessed.Widgets.Screen,
    position: PanelPosition,
    size: PanelSize,
    theme: string
  ) {
    super(screen, '🚨 Alerts', position, size, theme);
  }

  update(alerts: DashboardAlert[]): void {
    if (alerts.length === 0) {
      this.box.setContent('{green-fg}✓ No active alerts{/green-fg}');
      return;
    }

    const content = alerts.slice(0, 15).map(alert => {
      const icon = alert.severity === 'critical' ? '🔴'
        : alert.severity === 'warning' ? '🟡'
        : '🔵';
      const color = alert.severity === 'critical' ? 'red'
        : alert.severity === 'warning' ? 'yellow'
        : 'cyan';
      const time = new Date(alert.timestamp).toLocaleTimeString();

      return `{${color}-fg}${icon} [${time}] ${alert.message}{/${color}-fg}`;
    }).join('\n\n');

    this.box.setContent(content);
  }
}

/**
 * Query Log Panel
 */
class QueryLogPanel extends DashboardPanel {
  constructor(
    screen: blessed.Widgets.Screen,
    position: PanelPosition,
    size: PanelSize,
    theme: string
  ) {
    super(screen, '📝 Recent Queries', position, size, theme);
  }

  update(queries: QueryLog[]): void {
    if (queries.length === 0) {
      this.box.setContent('No queries yet');
      return;
    }

    const content = queries.slice(0, 15).map((q, i) => {
      const time = new Date(q.timestamp).toLocaleTimeString();
      const duration = q.duration.toFixed(0);
      const durationColor = q.duration > 1000 ? 'red' : q.duration > 500 ? 'yellow' : 'green';
      const query = q.query.substring(0, 60) + (q.query.length > 60 ? '...' : '');
      const errorIcon = q.result?.error ? ' {red-fg}✗{/red-fg}' : '';

      return `{gray-fg}${i + 1}.{/gray-fg} {${durationColor}-fg}[${duration}ms]{/${durationColor}-fg} {cyan-fg}${time}{/cyan-fg}${errorIcon}\n   ${query}`;
    }).join('\n\n');

    this.box.setContent(content);
  }
}

/**
 * System Health Panel
 */
class SystemHealthPanel extends DashboardPanel {
  constructor(
    screen: blessed.Widgets.Screen,
    position: PanelPosition,
    size: PanelSize,
    theme: string
  ) {
    super(screen, '💚 System Health', position, size, theme);
  }

  update(data: {
    status: 'healthy' | 'warning' | 'critical';
    uptime: number;
    cpu: number;
    memory: number;
    responseTime: number;
    errorRate: number;
  }): void {
    const statusIcon = data.status === 'healthy' ? '✓' : data.status === 'warning' ? '⚠' : '✗';
    const statusColor = data.status === 'healthy' ? 'green' : data.status === 'warning' ? 'yellow' : 'red';

    const uptimeSeconds = Math.floor(data.uptime / 1000);
    const hours = Math.floor(uptimeSeconds / 3600);
    const minutes = Math.floor((uptimeSeconds % 3600) / 60);
    const seconds = uptimeSeconds % 60;

    const cpuColor = data.cpu > 80 ? 'red' : data.cpu > 60 ? 'yellow' : 'green';
    const memColor = data.memory > 90 ? 'red' : data.memory > 70 ? 'yellow' : 'green';

    const content = `
{cyan-fg}Status:{/cyan-fg} {${statusColor}-fg}${statusIcon} ${data.status.toUpperCase()}{/${statusColor}-fg}

{cyan-fg}Uptime:{/cyan-fg}
${hours}h ${minutes}m ${seconds}s

{cyan-fg}CPU Usage:{/cyan-fg}
{${cpuColor}-fg}${'█'.repeat(Math.floor(data.cpu / 5))}{'░'.repeat(20 - Math.floor(data.cpu / 5))}{/${cpuColor}-fg} ${data.cpu.toFixed(1)}%

{cyan-fg}Memory Usage:{/cyan-fg}
{${memColor}-fg}${'█'.repeat(Math.floor(data.memory / 5))}{'░'.repeat(20 - Math.floor(data.memory / 5))}{/${memColor}-fg} ${data.memory.toFixed(1)}%

{cyan-fg}Response Time:{/cyan-fg} ${data.responseTime.toFixed(0)}ms
{cyan-fg}Error Rate:{/cyan-fg} ${(data.errorRate * 100).toFixed(2)}%
    `.trim();

    this.box.setContent(content);
  }
}

/**
 * Charts Panel
 */
class ChartsPanel extends DashboardPanel {
  constructor(
    screen: blessed.Widgets.Screen,
    position: PanelPosition,
    size: PanelSize,
    theme: string
  ) {
    super(screen, '📊 Performance Charts', position, size, theme);
  }

  update(data: {
    qps: ChartDataPoint[];
    avgQueryTime: ChartDataPoint[];
    cpu: ChartDataPoint[];
    memory: ChartDataPoint[];
  }): void {
    const qpsChart = this.renderMiniChart('QPS', data.qps, 'green');
    const timeChart = this.renderMiniChart('Avg Query Time (ms)', data.avgQueryTime, 'yellow');
    const cpuChart = this.renderMiniChart('CPU %', data.cpu, 'red');
    const memChart = this.renderMiniChart('Memory %', data.memory, 'blue');

    const content = `${qpsChart}\n\n${timeChart}\n\n${cpuChart}\n\n${memChart}`;
    this.box.setContent(content);
  }

  private renderMiniChart(title: string, data: ChartDataPoint[], color: string): string {
    if (data.length === 0) {
      return `{cyan-fg}${title}:{/cyan-fg} No data`;
    }

    const values = data.map(d => d.value);
    const maxValue = Math.max(...values, 1);
    const minValue = Math.min(...values, 0);
    const height = 5;
    const width = Math.min(data.length, 50);

    let chart = `{cyan-fg}${title}:{/cyan-fg}\n`;

    for (let row = height; row >= 0; row--) {
      const threshold = minValue + ((maxValue - minValue) * row / height);
      let line = `${threshold.toFixed(0).padStart(6)} │ `;

      for (let col = 0; col < width; col++) {
        const value = values[values.length - width + col] || 0;
        if (value >= threshold) {
          line += '{' + color + '-fg}█{/' + color + '-fg}';
        } else {
          line += ' ';
        }
      }
      chart += line + '\n';
    }

    chart += '       └' + '─'.repeat(width);

    return chart;
  }
}

/**
 * Export functions
 */
export async function startDashboard(
  performanceMonitor: PerformanceMonitor,
  healthMonitor: HealthMonitor,
  queryLogger: QueryLogger,
  stateManager: StateManager,
  config?: DashboardConfig
): Promise<EnhancedDashboard> {
  const dashboard = new EnhancedDashboard(
    performanceMonitor,
    healthMonitor,
    queryLogger,
    stateManager,
    config
  );

  await dashboard.start();
  return dashboard;
}
