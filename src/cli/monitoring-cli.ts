/**
 * Monitoring CLI - Sprint 4 Analytics & Monitoring Commands
 *
 * Provides 15 comprehensive monitoring commands for system health,
 * metrics, alerts, performance analysis, and observability integration.
 *
 * Commands:
 * 1. ai-shell health [database]
 * 2. ai-shell monitor start [options]
 * 3. ai-shell monitor stop
 * 4. ai-shell metrics show [metric]
 * 5. ai-shell metrics export [format]
 * 6. ai-shell alerts setup
 * 7. ai-shell alerts list
 * 8. ai-shell alerts test <alert-id>
 * 9. ai-shell performance analyze
 * 10. ai-shell performance report [period]
 * 11. ai-shell dashboard start
 * 12. ai-shell grafana setup
 * 13. ai-shell grafana deploy-dashboards
 * 14. ai-shell prometheus configure
 * 15. ai-shell anomaly detect [options]
 *
 * @module monitoring-cli
 */

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import * as WebSocket from 'ws';
import * as http from 'http';
import * as fs from 'fs/promises';
import * as path from 'path';
import { EventEmitter } from 'eventemitter3';
import { StateManager } from '../core/state-manager';
import { DatabaseConnectionManager } from './database-manager';
import { HealthMonitor } from './health-monitor';
import { PerformanceMonitor, PerformanceMetrics } from './performance-monitor';
import { PrometheusIntegration } from './prometheus-integration';
import { GrafanaClient, DashboardTemplates } from './grafana-integration';
import { createLogger } from '../core/logger';

// ============================================================================
// Types and Interfaces
// ============================================================================

interface MonitoringOptions {
  interval?: number;
  metrics?: string[];
  output?: 'console' | 'json' | 'csv';
  continuous?: boolean;
  websocket?: boolean;
}

interface MetricsExportOptions {
  format: 'json' | 'csv' | 'prometheus' | 'grafana';
  output?: string;
  timeRange?: string;
  metrics?: string[];
}

interface AlertConfig {
  enabled: boolean;
  channels: {
    slack?: {
      webhookUrl: string;
      enabled: boolean;
    };
    email?: {
      to: string[];
      smtp: {
        host: string;
        port: number;
        user: string;
        password: string;
      };
      enabled: boolean;
    };
    webhook?: {
      url: string;
      enabled: boolean;
    };
  };
  thresholds: {
    responseTime: number;
    errorRate: number;
    cpuUsage: number;
    memoryUsage: number;
    diskSpace: number;
  };
}

interface AnomalyDetectionOptions {
  metric?: string;
  threshold?: number; // Standard deviations (3-sigma default)
  window?: number; // Time window in minutes
  sensitivity?: 'low' | 'medium' | 'high';
}

interface AnomalyResult {
  timestamp: number;
  metric: string;
  value: number;
  mean: number;
  stdDev: number;
  zScore: number;
  isAnomaly: boolean;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

interface DashboardConfig {
  port: number;
  host: string;
  enableWebSocket: boolean;
  updateInterval: number;
}

interface PerformanceReport {
  period: string;
  startTime: number;
  endTime: number;
  summary: {
    totalRequests: number;
    avgResponseTime: number;
    p95ResponseTime: number;
    p99ResponseTime: number;
    errorRate: number;
    uptime: number;
  };
  metrics: PerformanceMetrics[];
  slowestQueries: Array<{
    query: string;
    time: number;
    count: number;
  }>;
  recommendations: string[];
}

// ============================================================================
// Anomaly Detection Engine
// ============================================================================

export class AnomalyDetector {
  private logger = createLogger('AnomalyDetector');

  constructor(private stateManager: StateManager) {}

  /**
   * Detect anomalies using 3-sigma rule
   */
  async detectAnomalies(options: AnomalyDetectionOptions): Promise<AnomalyResult[]> {
    const window = options.window || 60; // 1 hour default
    const threshold = this.getSigmaThreshold(options.threshold, options.sensitivity);

    this.logger.info('Detecting anomalies', { window, threshold, metric: options.metric });

    const metrics = await this.getMetricsHistory(options.metric, window);
    if (metrics.length < 10) {
      throw new Error('Insufficient data for anomaly detection (minimum 10 samples required)');
    }

    const results: AnomalyResult[] = [];
    const metricKeys = options.metric ? [options.metric] : this.getAllMetricKeys(metrics);

    for (const key of metricKeys) {
      const values = metrics.map(m => this.extractMetricValue(m, key)).filter(v => v !== null) as number[];

      if (values.length < 10) continue;

      const { mean, stdDev } = this.calculateStatistics(values);

      for (let i = 0; i < values.length; i++) {
        const value = values[i];
        const zScore = (value - mean) / stdDev;
        const isAnomaly = Math.abs(zScore) > threshold;

        if (isAnomaly) {
          results.push({
            timestamp: metrics[i].timestamp,
            metric: key,
            value,
            mean,
            stdDev,
            zScore,
            isAnomaly,
            severity: this.calculateSeverity(zScore, threshold)
          });
        }
      }
    }

    this.logger.info('Anomaly detection complete', {
      total: results.length,
      metrics: metricKeys.length
    });

    return results.sort((a, b) => Math.abs(b.zScore) - Math.abs(a.zScore));
  }

  /**
   * Calculate mean and standard deviation
   */
  private calculateStatistics(values: number[]): { mean: number; stdDev: number } {
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    return { mean, stdDev };
  }

  /**
   * Get sigma threshold based on sensitivity
   */
  private getSigmaThreshold(threshold?: number, sensitivity?: string): number {
    if (threshold) return threshold;

    switch (sensitivity) {
      case 'low': return 4; // 4-sigma (99.99%)
      case 'medium': return 3; // 3-sigma (99.7%)
      case 'high': return 2; // 2-sigma (95%)
      default: return 3; // Default 3-sigma
    }
  }

  /**
   * Calculate anomaly severity
   */
  private calculateSeverity(zScore: number, threshold: number): 'low' | 'medium' | 'high' | 'critical' {
    const absZ = Math.abs(zScore);

    if (absZ > threshold * 2) return 'critical';
    if (absZ > threshold * 1.5) return 'high';
    if (absZ > threshold * 1.2) return 'medium';
    return 'low';
  }

  /**
   * Get metrics history from state manager
   */
  private async getMetricsHistory(metric: string | undefined, windowMinutes: number): Promise<any[]> {
    const cutoff = Date.now() - (windowMinutes * 60 * 1000);
    const allMetrics = this.stateManager.findByMetadata('type', 'performance-metrics');

    return allMetrics
      .filter(m => m.value.timestamp >= cutoff)
      .map(m => m.value)
      .sort((a, b) => a.timestamp - b.timestamp);
  }

  /**
   * Get all metric keys from metrics
   */
  private getAllMetricKeys(metrics: any[]): string[] {
    const keys = new Set<string>();
    for (const metric of metrics) {
      Object.keys(metric).forEach(key => {
        if (key !== 'timestamp' && typeof metric[key] === 'number') {
          keys.add(key);
        }
      });
    }
    return Array.from(keys);
  }

  /**
   * Extract metric value from object
   */
  private extractMetricValue(metric: any, key: string): number | null {
    if (key in metric && typeof metric[key] === 'number') {
      return metric[key];
    }
    return null;
  }
}

// ============================================================================
// Dashboard Server (WebSocket)
// ============================================================================

export class DashboardServer extends EventEmitter {
  private logger = createLogger('DashboardServer');
  private server?: http.Server;
  private wss?: WebSocket.Server;
  private clients = new Set<WebSocket>();
  private updateInterval?: NodeJS.Timeout;

  constructor(
    private config: DashboardConfig,
    private perfMonitor: PerformanceMonitor,
    private healthMonitor: HealthMonitor
  ) {
    super();
  }

  /**
   * Start dashboard server
   */
  async start(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.server = http.createServer((req, res) => {
        if (req.url === '/') {
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(this.getDashboardHTML());
        } else if (req.url === '/health') {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ status: 'healthy', clients: this.clients.size }));
        } else {
          res.writeHead(404);
          res.end('Not Found');
        }
      });

      if (this.config.enableWebSocket) {
        this.wss = new WebSocket.Server({ server: this.server });
        this.setupWebSocket();
      }

      this.server.listen(this.config.port, this.config.host, () => {
        this.logger.info('Dashboard server started', {
          host: this.config.host,
          port: this.config.port,
          websocket: this.config.enableWebSocket
        });

        // Start metric updates
        this.startMetricUpdates();

        resolve();
      });

      this.server.on('error', reject);
    });
  }

  /**
   * Stop dashboard server
   */
  async stop(): Promise<void> {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }

    if (this.wss) {
      this.wss.close();
    }

    return new Promise((resolve, reject) => {
      if (this.server) {
        this.server.close((err) => {
          if (err) reject(err);
          else resolve();
        });
      } else {
        resolve();
      }
    });
  }

  /**
   * Setup WebSocket connections
   */
  private setupWebSocket(): void {
    if (!this.wss) return;

    this.wss.on('connection', (ws: WebSocket) => {
      this.clients.add(ws);
      this.logger.info('WebSocket client connected', { total: this.clients.size });

      ws.on('close', () => {
        this.clients.delete(ws);
        this.logger.info('WebSocket client disconnected', { total: this.clients.size });
      });

      ws.on('error', (error) => {
        this.logger.error('WebSocket error', error);
        this.clients.delete(ws);
      });

      // Send initial data
      this.sendMetricsToClient(ws);
    });
  }

  /**
   * Start periodic metric updates
   */
  private startMetricUpdates(): void {
    this.updateInterval = setInterval(async () => {
      await this.broadcastMetrics();
    }, this.config.updateInterval);
  }

  /**
   * Broadcast metrics to all clients
   */
  private async broadcastMetrics(): Promise<void> {
    const metrics = await this.getLatestMetrics();
    const payload = JSON.stringify({
      type: 'metrics-update',
      timestamp: Date.now(),
      data: metrics
    });

    for (const client of this.clients) {
      if (client.readyState === WebSocket.OPEN) {
        client.send(payload);
      }
    }
  }

  /**
   * Send metrics to single client
   */
  private async sendMetricsToClient(ws: WebSocket): Promise<void> {
    const metrics = await this.getLatestMetrics();
    ws.send(JSON.stringify({
      type: 'metrics-initial',
      timestamp: Date.now(),
      data: metrics
    }));
  }

  /**
   * Get latest metrics
   */
  private async getLatestMetrics(): Promise<any> {
    const perfHistory = this.perfMonitor.getHistory(10);
    const healthCheck = await this.healthMonitor.performHealthCheck();
    const alerts = this.healthMonitor.getActiveAlerts();

    return {
      performance: perfHistory[perfHistory.length - 1] || {},
      health: healthCheck,
      alerts,
      timestamp: Date.now()
    };
  }

  /**
   * Get dashboard HTML
   */
  private getDashboardHTML(): string {
    return `<!DOCTYPE html>
<html>
<head>
  <title>AI-Shell Monitoring Dashboard</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
      background: #0a0e27;
      color: #e0e6ed;
      padding: 20px;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 30px;
      border-radius: 12px;
      margin-bottom: 20px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .header h1 { font-size: 32px; margin-bottom: 8px; }
    .header .status { font-size: 14px; opacity: 0.9; }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-bottom: 20px;
    }
    .card {
      background: #151b3b;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      border: 1px solid #1e2847;
    }
    .card h2 {
      font-size: 18px;
      margin-bottom: 16px;
      color: #667eea;
    }
    .metric {
      display: flex;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid #1e2847;
    }
    .metric:last-child { border-bottom: none; }
    .metric-label { opacity: 0.7; }
    .metric-value {
      font-weight: 600;
      font-size: 18px;
    }
    .metric-value.healthy { color: #10b981; }
    .metric-value.warning { color: #f59e0b; }
    .metric-value.critical { color: #ef4444; }
    .alert {
      background: #ef4444;
      padding: 16px;
      border-radius: 8px;
      margin: 8px 0;
    }
    .alert-warning { background: #f59e0b; }
    .footer {
      text-align: center;
      padding: 20px;
      opacity: 0.5;
      font-size: 12px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🚀 AI-Shell Monitoring Dashboard</h1>
    <div class="status">Real-time system monitoring | Updated: <span id="timestamp">--</span></div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>Performance</h2>
      <div id="performance-metrics"></div>
    </div>

    <div class="card">
      <h2>Health Status</h2>
      <div id="health-metrics"></div>
    </div>

    <div class="card">
      <h2>Active Alerts</h2>
      <div id="alerts"></div>
    </div>
  </div>

  <div class="footer">
    AI-Shell Monitoring Dashboard v1.0.0 | WebSocket Connection: <span id="ws-status">Connecting...</span>
  </div>

  <script>
    const ws = new WebSocket('ws://' + window.location.host);
    const timestampEl = document.getElementById('timestamp');
    const perfEl = document.getElementById('performance-metrics');
    const healthEl = document.getElementById('health-metrics');
    const alertsEl = document.getElementById('alerts');
    const wsStatusEl = document.getElementById('ws-status');

    ws.onopen = () => {
      wsStatusEl.textContent = 'Connected';
      wsStatusEl.style.color = '#10b981';
    };

    ws.onclose = () => {
      wsStatusEl.textContent = 'Disconnected';
      wsStatusEl.style.color = '#ef4444';
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      updateDashboard(data);
    };

    function updateDashboard(data) {
      timestampEl.textContent = new Date(data.timestamp).toLocaleString();

      // Update performance metrics
      if (data.data.performance) {
        const perf = data.data.performance;
        perfEl.innerHTML = [
          createMetric('Active Connections', perf.activeConnections || 0),
          createMetric('Queries/Sec', (perf.queriesPerSecond || 0).toFixed(2)),
          createMetric('Avg Query Time', (perf.averageQueryTime || 0).toFixed(2) + 'ms'),
          createMetric('CPU Usage', (perf.cpuUsage || 0).toFixed(1) + '%', getStatus(perf.cpuUsage, 80, 90)),
          createMetric('Memory Usage', (perf.memoryUsage || 0).toFixed(1) + '%', getStatus(perf.memoryUsage, 80, 90))
        ].join('');
      }

      // Update health metrics
      if (data.data.health) {
        const health = data.data.health;
        healthEl.innerHTML = [
          createMetric('Response Time', health.responseTime.value + 'ms', health.responseTime.status),
          createMetric('Error Rate', health.errorRate.value.toFixed(2) + '%', health.errorRate.status),
          createMetric('Connections', health.connectionCount.value, health.connectionCount.status)
        ].join('');
      }

      // Update alerts
      if (data.data.alerts && data.data.alerts.length > 0) {
        alertsEl.innerHTML = data.data.alerts.map(alert =>
          \`<div class="alert \${alert.type === 'warning' ? 'alert-warning' : ''}">
            <strong>\${alert.type.toUpperCase()}</strong>: \${alert.message}
          </div>\`
        ).join('');
      } else {
        alertsEl.innerHTML = '<div style="opacity: 0.5;">No active alerts</div>';
      }
    }

    function createMetric(label, value, status = 'healthy') {
      return \`<div class="metric">
        <span class="metric-label">\${label}</span>
        <span class="metric-value \${status}">\${value}</span>
      </div>\`;
    }

    function getStatus(value, warningThreshold, criticalThreshold) {
      if (value >= criticalThreshold) return 'critical';
      if (value >= warningThreshold) return 'warning';
      return 'healthy';
    }
  </script>
</body>
</html>`;
  }
}

// ============================================================================
// Monitoring CLI Implementation
// ============================================================================

export class MonitoringCLI {
  private logger = createLogger('MonitoringCLI');
  private stateManager: StateManager;
  private dbManager: DatabaseConnectionManager;
  private healthMonitor: HealthMonitor;
  private perfMonitor: PerformanceMonitor;
  private prometheusIntegration: PrometheusIntegration;
  private anomalyDetector: AnomalyDetector;
  private dashboardServer?: DashboardServer;

  constructor() {
    this.stateManager = new StateManager();
    this.dbManager = new DatabaseConnectionManager(this.stateManager);
    this.healthMonitor = new HealthMonitor(this.dbManager, this.stateManager);
    this.perfMonitor = new PerformanceMonitor(this.stateManager);
    this.prometheusIntegration = new PrometheusIntegration(
      this.stateManager,
      this.healthMonitor,
      this.dbManager
    );
    this.anomalyDetector = new AnomalyDetector(this.stateManager);
  }

  /**
   * Command 1: Health check
   */
  async health(database?: string): Promise<void> {
    const spinner = ora('Performing health check...').start();

    try {
      if (database) {
        // Switch to specific database
        const connections = this.dbManager.listConnections();
        const conn = connections.find(c => c.name === database);
        if (conn) {
          await this.dbManager.switchActive(conn.name);
        }
      }

      const healthCheck = await this.healthMonitor.performHealthCheck();
      spinner.succeed('Health check complete');

      console.log(chalk.bold('\n🏥 Health Check Results\n'));
      console.log(chalk.gray('─'.repeat(60)));

      // Display metrics
      Object.values(healthCheck).forEach((metric) => {
        if (!metric) return;

        const icon = metric.status === 'healthy' ? '✓' :
                    metric.status === 'warning' ? '⚠' : '✗';
        const color = metric.status === 'healthy' ? chalk.green :
                     metric.status === 'warning' ? chalk.yellow : chalk.red;

        console.log(color(`${icon} ${metric.name}`));
        console.log(`  Value: ${metric.value} ${metric.unit}`);
        console.log(`  Status: ${metric.status}`);
        console.log();
      });

    } catch (error: any) {
      spinner.fail('Health check failed');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 2: Start monitoring
   */
  async monitorStart(options: MonitoringOptions): Promise<void> {
    console.log(chalk.bold('🔍 Starting real-time monitoring...\n'));

    const interval = options.interval || 5;
    this.healthMonitor.startMonitoring(interval * 1000);

    this.healthMonitor.on('metricsCollected', (metrics) => {
      if (options.output === 'json') {
        console.log(JSON.stringify(metrics, null, 2));
      } else if (options.output === 'csv') {
        this.printMetricsCSV(metrics);
      } else {
        this.printMetricsConsole(metrics);
      }
    });

    this.healthMonitor.on('alertTriggered', (alert) => {
      console.log(chalk.red(`\n🚨 ALERT: ${alert.message}`));
      console.log(chalk.yellow(`   Metric: ${alert.metric}`));
      console.log(chalk.yellow(`   Value: ${alert.value} (threshold: ${alert.threshold})`));
    });

    console.log(chalk.green(`✓ Monitoring started (interval: ${interval}s)`));
    console.log(chalk.gray('Press Ctrl+C to stop\n'));

    // Keep process alive
    await new Promise(() => {});
  }

  /**
   * Command 3: Stop monitoring
   */
  async monitorStop(): Promise<void> {
    const spinner = ora('Stopping monitoring...').start();

    try {
      this.healthMonitor.stopMonitoring();
      spinner.succeed('Monitoring stopped');
    } catch (error: any) {
      spinner.fail('Failed to stop monitoring');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 4: Show metrics
   */
  async metricsShow(metric?: string): Promise<void> {
    const spinner = ora('Fetching metrics...').start();

    try {
      const metrics = await this.perfMonitor.getHistory(100);
      spinner.succeed('Metrics retrieved');

      if (metrics.length === 0) {
        console.log(chalk.yellow('No metrics available'));
        return;
      }

      const latest = metrics[metrics.length - 1];

      console.log(chalk.bold('\n📊 Current Metrics\n'));
      console.log(chalk.gray('─'.repeat(60)));

      if (metric) {
        // Show specific metric
        const value = (latest as any)[metric];
        if (value !== undefined) {
          console.log(chalk.cyan(`${metric}: ${value}`));
        } else {
          console.log(chalk.yellow(`Metric '${metric}' not found`));
        }
      } else {
        // Show all metrics
        console.log(chalk.cyan('Active Connections:'), latest.activeConnections);
        console.log(chalk.cyan('Queries/Second:'), latest.queriesPerSecond.toFixed(2));
        console.log(chalk.cyan('Avg Query Time:'), latest.averageQueryTime.toFixed(2), 'ms');
        console.log(chalk.cyan('Slow Queries:'), latest.slowQueriesCount);
        console.log(chalk.cyan('Cache Hit Rate:'), (latest.cacheHitRate * 100).toFixed(1), '%');
        console.log(chalk.cyan('CPU Usage:'), latest.cpuUsage.toFixed(1), '%');
        console.log(chalk.cyan('Memory Usage:'), latest.memoryUsage.toFixed(1), '%');
      }

      console.log();
    } catch (error: any) {
      spinner.fail('Failed to fetch metrics');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 5: Export metrics
   */
  async metricsExport(format: string, options: MetricsExportOptions): Promise<void> {
    const spinner = ora(`Exporting metrics to ${format}...`).start();

    try {
      const metrics = await this.perfMonitor.getHistory(1000);
      let output: string;

      switch (format) {
        case 'json':
          output = JSON.stringify(metrics, null, 2);
          break;

        case 'csv':
          output = this.convertMetricsToCSV(metrics);
          break;

        case 'prometheus':
          const collector = this.prometheusIntegration.getCollector();
          output = collector?.formatMetrics() || '';
          break;

        case 'grafana':
          output = JSON.stringify(this.convertToGrafanaFormat(metrics), null, 2);
          break;

        default:
          throw new Error(`Unsupported format: ${format}`);
      }

      if (options.output) {
        await fs.writeFile(options.output, output);
        spinner.succeed(`Metrics exported to ${options.output}`);
      } else {
        spinner.succeed('Metrics exported');
        console.log(output);
      }

    } catch (error: any) {
      spinner.fail('Failed to export metrics');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 6: Setup alerts
   */
  async alertsSetup(): Promise<void> {
    console.log(chalk.bold('🔔 Alert Configuration\n'));

    const defaultConfig: AlertConfig = {
      enabled: true,
      channels: {
        slack: {
          webhookUrl: '',
          enabled: false
        },
        email: {
          to: [],
          smtp: {
            host: 'smtp.gmail.com',
            port: 587,
            user: '',
            password: ''
          },
          enabled: false
        },
        webhook: {
          url: '',
          enabled: false
        }
      },
      thresholds: {
        responseTime: 1000,
        errorRate: 5,
        cpuUsage: 80,
        memoryUsage: 85,
        diskSpace: 90
      }
    };

    this.healthMonitor.configureAlerts(defaultConfig);

    console.log(chalk.green('✓ Alerts configured with default settings'));
    console.log(chalk.gray('\nDefault thresholds:'));
    console.log(chalk.cyan('  Response Time:'), '1000ms');
    console.log(chalk.cyan('  Error Rate:'), '5%');
    console.log(chalk.cyan('  CPU Usage:'), '80%');
    console.log(chalk.cyan('  Memory Usage:'), '85%');
    console.log(chalk.cyan('  Disk Space:'), '90%');
    console.log();
  }

  /**
   * Command 7: List alerts
   */
  async alertsList(): Promise<void> {
    const spinner = ora('Fetching alerts...').start();

    try {
      const alerts = this.healthMonitor.getActiveAlerts();
      spinner.succeed('Alerts retrieved');

      if (alerts.length === 0) {
        console.log(chalk.green('✓ No active alerts'));
        return;
      }

      console.log(chalk.bold(`\n🚨 Active Alerts (${alerts.length})\n`));
      console.log(chalk.gray('─'.repeat(60)));

      alerts.forEach((alert, index) => {
        const icon = alert.type === 'critical' ? '🔴' : '🟡';
        const color = alert.type === 'critical' ? chalk.red : chalk.yellow;

        console.log(color(`${icon} Alert #${index + 1}`));
        console.log(`   ID: ${alert.id}`);
        console.log(`   Type: ${alert.type}`);
        console.log(`   Metric: ${alert.metric}`);
        console.log(`   Message: ${alert.message}`);
        console.log(`   Value: ${alert.value} (threshold: ${alert.threshold})`);
        console.log(`   Time: ${new Date(alert.timestamp).toLocaleString()}`);
        console.log();
      });

    } catch (error: any) {
      spinner.fail('Failed to fetch alerts');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 8: Test alert
   */
  async alertsTest(alertId: string): Promise<void> {
    const spinner = ora(`Testing alert ${alertId}...`).start();

    try {
      // Trigger a test alert
      const testAlert = {
        id: alertId,
        type: 'warning' as const,
        metric: 'test',
        message: 'This is a test alert',
        value: 100,
        threshold: 80,
        timestamp: Date.now(),
        resolved: false
      };

      // Send via configured channels
      await this.healthMonitor['sendAlertNotifications'](testAlert);

      spinner.succeed('Test alert sent successfully');
      console.log(chalk.green('\n✓ Alert test complete'));
      console.log(chalk.gray('Check configured notification channels for the test alert'));

    } catch (error: any) {
      spinner.fail('Failed to send test alert');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 9: Performance analysis
   */
  async performanceAnalyze(): Promise<void> {
    const spinner = ora('Analyzing performance...').start();

    try {
      const slowQueries = await this.perfMonitor.slowQueries(1000, 10);
      const indexRecommendations = await this.perfMonitor.indexRecommendations();
      const poolStats = await this.perfMonitor.connectionPool();

      spinner.succeed('Performance analysis complete');

      console.log(chalk.bold('\n⚡ Performance Analysis\n'));
      console.log(chalk.gray('─'.repeat(60)));

      // Slow queries
      console.log(chalk.bold('\n🐌 Slow Queries'));
      if (slowQueries.length > 0) {
        slowQueries.forEach((query, i) => {
          console.log(chalk.yellow(`\n${i + 1}. ${query.query.substring(0, 80)}...`));
          console.log(chalk.gray(`   Execution Time: ${query.executionTime}ms`));
          console.log(chalk.gray(`   Frequency: ${query.frequency}`));
          if (query.optimizations && query.optimizations.length > 0) {
            console.log(chalk.cyan('   Suggestions:'));
            query.optimizations.forEach(opt => console.log(chalk.cyan(`     - ${opt}`)));
          }
        });
      } else {
        console.log(chalk.green('  No slow queries detected'));
      }

      // Index recommendations
      console.log(chalk.bold('\n\n📊 Index Recommendations'));
      if (indexRecommendations.length > 0) {
        indexRecommendations.slice(0, 5).forEach((rec, i) => {
          console.log(chalk.cyan(`\n${i + 1}. ${rec.table}.${rec.columns.join(', ')}`));
          console.log(chalk.gray(`   Reason: ${rec.reason}`));
          console.log(chalk.gray(`   Improvement: ${rec.estimatedImprovement}`));
          console.log(chalk.gray(`   SQL: ${rec.createStatement}`));
        });
      } else {
        console.log(chalk.green('  No index recommendations'));
      }

      // Connection pool
      console.log(chalk.bold('\n\n🔌 Connection Pool'));
      console.log(chalk.cyan('  Total Connections:'), poolStats.totalConnections);
      console.log(chalk.cyan('  Active:'), poolStats.activeConnections);
      console.log(chalk.cyan('  Idle:'), poolStats.idleConnections);
      console.log(chalk.cyan('  Waiting Queries:'), poolStats.waitingQueries);
      console.log(chalk.cyan('  Avg Wait Time:'), poolStats.averageWaitTime, 'ms');

      console.log();

    } catch (error: any) {
      spinner.fail('Performance analysis failed');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 10: Performance report
   */
  async performanceReport(period: string = '1h'): Promise<void> {
    const spinner = ora(`Generating performance report for ${period}...`).start();

    try {
      const periodMs = this.parsePeriod(period);
      const metrics = await this.perfMonitor.getHistory();
      const cutoff = Date.now() - periodMs;
      const filteredMetrics = metrics.filter(m => m.timestamp >= cutoff);

      if (filteredMetrics.length === 0) {
        spinner.warn('No metrics available for specified period');
        return;
      }

      const report: PerformanceReport = {
        period,
        startTime: filteredMetrics[0].timestamp,
        endTime: filteredMetrics[filteredMetrics.length - 1].timestamp,
        summary: this.calculateSummary(filteredMetrics),
        metrics: filteredMetrics,
        slowestQueries: await this.getSlowQueriesForPeriod(periodMs),
        recommendations: this.generateRecommendations(filteredMetrics)
      };

      spinner.succeed('Performance report generated');

      console.log(chalk.bold('\n📈 Performance Report\n'));
      console.log(chalk.gray('─'.repeat(60)));
      console.log(chalk.cyan('Period:'), period);
      console.log(chalk.cyan('Start:'), new Date(report.startTime).toLocaleString());
      console.log(chalk.cyan('End:'), new Date(report.endTime).toLocaleString());

      console.log(chalk.bold('\n\nSummary'));
      console.log(chalk.cyan('  Total Requests:'), report.summary.totalRequests);
      console.log(chalk.cyan('  Avg Response Time:'), report.summary.avgResponseTime.toFixed(2), 'ms');
      console.log(chalk.cyan('  P95 Response Time:'), report.summary.p95ResponseTime.toFixed(2), 'ms');
      console.log(chalk.cyan('  P99 Response Time:'), report.summary.p99ResponseTime.toFixed(2), 'ms');
      console.log(chalk.cyan('  Error Rate:'), report.summary.errorRate.toFixed(2), '%');
      console.log(chalk.cyan('  Uptime:'), (report.summary.uptime / 3600).toFixed(2), 'hours');

      if (report.slowestQueries.length > 0) {
        console.log(chalk.bold('\n\nSlowest Queries'));
        report.slowestQueries.slice(0, 5).forEach((q, i) => {
          console.log(chalk.yellow(`  ${i + 1}. ${q.query.substring(0, 60)}...`));
          console.log(chalk.gray(`     Time: ${q.time}ms | Count: ${q.count}`));
        });
      }

      if (report.recommendations.length > 0) {
        console.log(chalk.bold('\n\nRecommendations'));
        report.recommendations.forEach(rec => {
          console.log(chalk.cyan(`  • ${rec}`));
        });
      }

      console.log();

    } catch (error: any) {
      spinner.fail('Failed to generate performance report');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 11: Start dashboard
   */
  async dashboardStart(port: number = 3000, host: string = 'localhost'): Promise<void> {
    const spinner = ora('Starting dashboard server...').start();

    try {
      const config: DashboardConfig = {
        port,
        host,
        enableWebSocket: true,
        updateInterval: 5000
      };

      this.dashboardServer = new DashboardServer(
        config,
        this.perfMonitor,
        this.healthMonitor
      );

      await this.dashboardServer.start();

      spinner.succeed('Dashboard server started');
      console.log(chalk.bold('\n📊 Dashboard Server\n'));
      console.log(chalk.green(`✓ Server running at http://${host}:${port}`));
      console.log(chalk.gray('Press Ctrl+C to stop\n'));

      // Keep process alive
      await new Promise(() => {});

    } catch (error: any) {
      spinner.fail('Failed to start dashboard');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 12: Grafana setup
   */
  async grafanaSetup(url: string, apiKey: string, prometheusUrl?: string): Promise<void> {
    const spinner = ora('Configuring Grafana...').start();

    try {
      const client = new GrafanaClient({ url, apiKey });

      // Test connection
      const connected = await client.testConnection();
      if (!connected) {
        throw new Error('Failed to connect to Grafana');
      }

      spinner.text = 'Connected to Grafana';

      // Setup Prometheus data source
      if (prometheusUrl) {
        await client.setupDataSource(prometheusUrl);
        spinner.text = 'Prometheus data source configured';
      }

      // Save config
      await fs.writeFile(
        path.join(process.cwd(), '.grafana-config.json'),
        JSON.stringify({ url, apiKey, prometheusUrl }, null, 2)
      );

      spinner.succeed('Grafana configured successfully');
      console.log(chalk.green('\n✓ Grafana setup complete'));
      console.log(chalk.gray(`   URL: ${url}`));
      if (prometheusUrl) {
        console.log(chalk.gray(`   Prometheus: ${prometheusUrl}`));
      }

    } catch (error: any) {
      spinner.fail('Grafana setup failed');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 13: Deploy Grafana dashboards
   */
  async grafanaDeployDashboards(): Promise<void> {
    const spinner = ora('Loading Grafana configuration...').start();

    try {
      const configPath = path.join(process.cwd(), '.grafana-config.json');
      const configData = await fs.readFile(configPath, 'utf-8');
      const config = JSON.parse(configData);

      const client = new GrafanaClient(config);
      spinner.text = 'Deploying dashboards...';

      const dashboards = [
        { name: 'Overview', dashboard: DashboardTemplates.createOverviewDashboard() },
        { name: 'Performance', dashboard: DashboardTemplates.createPerformanceDashboard() },
        { name: 'Security', dashboard: DashboardTemplates.createSecurityDashboard() },
        { name: 'Query Analytics', dashboard: DashboardTemplates.createQueryAnalyticsDashboard() }
      ];

      console.log();
      for (const { name, dashboard } of dashboards) {
        spinner.text = `Deploying ${name} dashboard...`;
        await client.saveDashboard(dashboard);
        console.log(chalk.green(`  ✓ ${name} dashboard deployed`));
      }

      spinner.succeed('All dashboards deployed successfully');

    } catch (error: any) {
      spinner.fail('Failed to deploy dashboards');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 14: Configure Prometheus
   */
  async prometheusConfigure(port: number = 9090, host: string = '0.0.0.0'): Promise<void> {
    const spinner = ora('Configuring Prometheus integration...').start();

    try {
      await this.prometheusIntegration.start({
        enabled: true,
        port,
        host,
        path: '/metrics',
        scrapeInterval: 15,
        authentication: {
          enabled: false,
          type: 'bearer'
        },
        labels: {
          app: 'ai-shell',
          environment: 'production'
        },
        retention: 3600
      });

      spinner.succeed('Prometheus configured successfully');
      console.log(chalk.green('\n✓ Prometheus integration started'));
      console.log(chalk.gray(`   Metrics endpoint: http://${host}:${port}/metrics`));
      console.log(chalk.gray(`   Scrape interval: 15s`));

    } catch (error: any) {
      spinner.fail('Prometheus configuration failed');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  /**
   * Command 15: Anomaly detection
   */
  async anomalyDetect(options: AnomalyDetectionOptions): Promise<void> {
    const spinner = ora('Detecting anomalies...').start();

    try {
      const anomalies = await this.anomalyDetector.detectAnomalies(options);

      spinner.succeed(`Anomaly detection complete (${anomalies.length} anomalies found)`);

      if (anomalies.length === 0) {
        console.log(chalk.green('\n✓ No anomalies detected'));
        return;
      }

      console.log(chalk.bold(`\n🔍 Anomaly Detection Results\n`));
      console.log(chalk.gray('─'.repeat(60)));
      console.log(chalk.cyan('Window:'), options.window || 60, 'minutes');
      console.log(chalk.cyan('Threshold:'), options.threshold || 3, 'sigma');
      console.log(chalk.cyan('Sensitivity:'), options.sensitivity || 'medium');

      console.log(chalk.bold(`\n\nDetected Anomalies (${anomalies.length})\n`));

      anomalies.slice(0, 20).forEach((anomaly, i) => {
        const color = anomaly.severity === 'critical' ? chalk.red :
                     anomaly.severity === 'high' ? chalk.yellow :
                     chalk.cyan;

        console.log(color(`${i + 1}. ${anomaly.metric}`));
        console.log(chalk.gray(`   Time: ${new Date(anomaly.timestamp).toLocaleString()}`));
        console.log(chalk.gray(`   Value: ${anomaly.value.toFixed(2)}`));
        console.log(chalk.gray(`   Expected: ${anomaly.mean.toFixed(2)} ± ${anomaly.stdDev.toFixed(2)}`));
        console.log(chalk.gray(`   Z-Score: ${anomaly.zScore.toFixed(2)}`));
        console.log(color(`   Severity: ${anomaly.severity.toUpperCase()}`));
        console.log();
      });

      if (anomalies.length > 20) {
        console.log(chalk.gray(`... and ${anomalies.length - 20} more anomalies\n`));
      }

    } catch (error: any) {
      spinner.fail('Anomaly detection failed');
      console.error(chalk.red(`Error: ${error.message}`));
      throw error;
    }
  }

  // Helper methods

  private printMetricsConsole(metrics: any): void {
    console.clear();
    console.log(chalk.bold('═══════════════════════════════════════════════════════════'));
    console.log(chalk.bold('                  HEALTH MONITORING'));
    console.log(chalk.bold('═══════════════════════════════════════════════════════════'));
    console.log(`Timestamp: ${new Date().toISOString()}\n`);

    if (metrics.connectionCount) {
      console.log(chalk.cyan('🔗 Active Connections:'), metrics.connectionCount.value);
    }
    if (metrics.responseTime) {
      const status = metrics.responseTime.status;
      const color = status === 'healthy' ? chalk.green :
                   status === 'warning' ? chalk.yellow : chalk.red;
      console.log(color(`⏱️  Response Time:`), metrics.responseTime.value, 'ms');
    }
    if (metrics.errorRate) {
      console.log(chalk.cyan('❌ Error Rate:'), metrics.errorRate.value.toFixed(2), '%');
    }

    console.log('\n═══════════════════════════════════════════════════════════');
  }

  private printMetricsCSV(metrics: any): void {
    const values = Object.values(metrics)
      .filter(m => m && typeof m === 'object' && 'value' in m)
      .map((m: any) => m.value);
    console.log(values.join(','));
  }

  private convertMetricsToCSV(metrics: PerformanceMetrics[]): string {
    const headers = [
      'timestamp',
      'activeConnections',
      'queriesPerSecond',
      'averageQueryTime',
      'slowQueriesCount',
      'cacheHitRate',
      'cpuUsage',
      'memoryUsage'
    ];

    const rows = metrics.map(m => [
      m.timestamp,
      m.activeConnections,
      m.queriesPerSecond,
      m.averageQueryTime,
      m.slowQueriesCount,
      m.cacheHitRate,
      m.cpuUsage,
      m.memoryUsage
    ].join(','));

    return [headers.join(','), ...rows].join('\n');
  }

  private convertToGrafanaFormat(metrics: PerformanceMetrics[]): any {
    return {
      target: 'performance-metrics',
      datapoints: metrics.map(m => [m.averageQueryTime, m.timestamp])
    };
  }

  private parsePeriod(period: string): number {
    const match = period.match(/^(\d+)([smhd])$/);
    if (!match) {
      throw new Error('Invalid period format. Use: 5m, 1h, 7d, etc.');
    }

    const value = parseInt(match[1]);
    const unit = match[2];

    const multipliers: Record<string, number> = {
      's': 1000,
      'm': 60 * 1000,
      'h': 60 * 60 * 1000,
      'd': 24 * 60 * 60 * 1000
    };

    return value * multipliers[unit];
  }

  private calculateSummary(metrics: PerformanceMetrics[]): PerformanceReport['summary'] {
    const avgResponseTime = metrics.reduce((sum, m) => sum + m.averageQueryTime, 0) / metrics.length;
    const sortedTimes = metrics.map(m => m.averageQueryTime).sort((a, b) => a - b);
    const p95Index = Math.floor(sortedTimes.length * 0.95);
    const p99Index = Math.floor(sortedTimes.length * 0.99);

    return {
      totalRequests: metrics.length,
      avgResponseTime,
      p95ResponseTime: sortedTimes[p95Index],
      p99ResponseTime: sortedTimes[p99Index],
      errorRate: 0,
      uptime: (metrics[metrics.length - 1].timestamp - metrics[0].timestamp) / 1000
    };
  }

  private async getSlowQueriesForPeriod(periodMs: number): Promise<any[]> {
    const cutoff = Date.now() - periodMs;
    const allQueries = this.stateManager.findByMetadata('type', 'query-log');

    return allQueries
      .filter(q => q.value.timestamp >= cutoff && q.value.duration > 1000)
      .map(q => ({
        query: q.value.query,
        time: q.value.duration,
        count: 1
      }))
      .sort((a, b) => b.time - a.time)
      .slice(0, 10);
  }

  private generateRecommendations(metrics: PerformanceMetrics[]): string[] {
    const recommendations: string[] = [];
    const latest = metrics[metrics.length - 1];

    if (latest.cpuUsage > 80) {
      recommendations.push('High CPU usage detected. Consider scaling horizontally.');
    }

    if (latest.memoryUsage > 85) {
      recommendations.push('High memory usage. Review memory leaks and optimize queries.');
    }

    if (latest.cacheHitRate < 0.7) {
      recommendations.push('Low cache hit rate. Review cache configuration and TTL settings.');
    }

    if (latest.slowQueriesCount > 10) {
      recommendations.push('Multiple slow queries detected. Run performance analysis for optimization suggestions.');
    }

    if (recommendations.length === 0) {
      recommendations.push('System is performing well. No immediate actions required.');
    }

    return recommendations;
  }
}

// ============================================================================
// Export
// ============================================================================

export function createMonitoringCommands(): Command {
  const program = new Command();
  const cli = new MonitoringCLI();

  // Command 1: Health check
  program
    .command('health [database]')
    .description('Perform database health check')
    .action(async (database) => {
      await cli.health(database);
    });

  // Commands 2-3: Monitor start/stop
  const monitorCmd = program
    .command('monitor')
    .description('Real-time monitoring commands');

  monitorCmd
    .command('start')
    .description('Start real-time monitoring')
    .option('-i, --interval <seconds>', 'Update interval', '5')
    .option('-m, --metrics <metrics>', 'Specific metrics to monitor')
    .option('-o, --output <format>', 'Output format (console, json, csv)', 'console')
    .action(async (options) => {
      await cli.monitorStart({
        interval: parseInt(options.interval),
        metrics: options.metrics?.split(','),
        output: options.output
      });
    });

  monitorCmd
    .command('stop')
    .description('Stop monitoring')
    .action(async () => {
      await cli.monitorStop();
    });

  // Commands 4-5: Metrics show/export
  const metricsCmd = program
    .command('metrics')
    .description('Metrics management commands');

  metricsCmd
    .command('show [metric]')
    .description('Show current metrics')
    .action(async (metric) => {
      await cli.metricsShow(metric);
    });

  metricsCmd
    .command('export <format>')
    .description('Export metrics (json, csv, prometheus, grafana)')
    .option('-o, --output <file>', 'Output file path')
    .option('-t, --time-range <range>', 'Time range')
    .action(async (format, options) => {
      await cli.metricsExport(format, {
        format,
        output: options.output,
        timeRange: options.timeRange
      });
    });

  // Commands 6-8: Alerts setup/list/test
  const alertsCmd = program
    .command('alerts')
    .description('Alert management commands');

  alertsCmd
    .command('setup')
    .description('Configure alert settings')
    .action(async () => {
      await cli.alertsSetup();
    });

  alertsCmd
    .command('list')
    .description('List active alerts')
    .action(async () => {
      await cli.alertsList();
    });

  alertsCmd
    .command('test <alert-id>')
    .description('Test alert notification')
    .action(async (alertId) => {
      await cli.alertsTest(alertId);
    });

  // Commands 9-10: Performance analyze/report
  const performanceCmd = program
    .command('performance')
    .description('Performance analysis commands');

  performanceCmd
    .command('analyze')
    .description('Analyze system performance')
    .action(async () => {
      await cli.performanceAnalyze();
    });

  performanceCmd
    .command('report [period]')
    .description('Generate performance report (e.g., 1h, 24h, 7d)')
    .action(async (period) => {
      await cli.performanceReport(period);
    });

  // Command 11: Dashboard
  program
    .command('dashboard')
    .description('Start monitoring dashboard')
    .option('-p, --port <port>', 'Server port', '3000')
    .option('-h, --host <host>', 'Server host', 'localhost')
    .action(async (options) => {
      await cli.dashboardStart(parseInt(options.port), options.host);
    });

  // Commands 12-13: Grafana setup/deploy
  const grafanaCmd = program
    .command('grafana')
    .description('Grafana integration commands');

  grafanaCmd
    .command('setup')
    .description('Configure Grafana connection')
    .requiredOption('--url <url>', 'Grafana URL')
    .requiredOption('--api-key <key>', 'Grafana API key')
    .option('--prometheus-url <url>', 'Prometheus URL')
    .action(async (options) => {
      await cli.grafanaSetup(options.url, options.apiKey, options.prometheusUrl);
    });

  grafanaCmd
    .command('deploy-dashboards')
    .description('Deploy all dashboards to Grafana')
    .action(async () => {
      await cli.grafanaDeployDashboards();
    });

  // Command 14: Prometheus
  program
    .command('prometheus')
    .description('Configure Prometheus integration')
    .option('-p, --port <port>', 'Metrics port', '9090')
    .option('-h, --host <host>', 'Metrics host', '0.0.0.0')
    .action(async (options) => {
      await cli.prometheusConfigure(parseInt(options.port), options.host);
    });

  // Command 15: Anomaly detection
  program
    .command('anomaly')
    .description('Detect anomalies in metrics')
    .option('-m, --metric <metric>', 'Specific metric to analyze')
    .option('-t, --threshold <sigma>', 'Sigma threshold (default: 3)')
    .option('-w, --window <minutes>', 'Time window in minutes (default: 60)')
    .option('-s, --sensitivity <level>', 'Sensitivity: low, medium, high', 'medium')
    .action(async (options) => {
      await cli.anomalyDetect({
        metric: options.metric,
        threshold: options.threshold ? parseFloat(options.threshold) : undefined,
        window: options.window ? parseInt(options.window) : undefined,
        sensitivity: options.sensitivity
      });
    });

  return program;
}
