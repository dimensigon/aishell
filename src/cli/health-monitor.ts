/**
 * Health Dashboard with Alerts
 * Real-time monitoring and alerting for database health
 * Commands: ai-shell monitor, ai-shell health-check, ai-shell alerts setup
 */

import { EventEmitter } from 'eventemitter3';
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';
import axios from 'axios';

interface HealthMetric {
  name: string;
  value: number;
  unit: string;
  status: 'healthy' | 'warning' | 'critical';
  timestamp: number;
}

interface HealthCheck {
  connectionCount: HealthMetric;
  responseTime: HealthMetric;
  errorRate: HealthMetric;
  cpuUsage?: HealthMetric;
  memoryUsage?: HealthMetric;
  diskSpace?: HealthMetric;
  activeQueries?: HealthMetric;
  cacheHitRate?: HealthMetric;
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
    responseTime: number; // ms
    errorRate: number; // percentage
    cpuUsage: number; // percentage
    memoryUsage: number; // percentage
    diskSpace: number; // percentage
  };
}

interface Alert {
  id: string;
  type: 'warning' | 'critical';
  metric: string;
  message: string;
  value: number;
  threshold: number;
  timestamp: number;
  resolved: boolean;
}

export class HealthMonitor extends EventEmitter {
  private logger = createLogger('HealthMonitor');
  private metrics = new Map<string, HealthMetric[]>();
  private alerts = new Map<string, Alert>();
  private alertConfig: AlertConfig;
  private monitoringInterval?: NodeJS.Timeout;
  private isMonitoring = false;

  constructor(
    private dbManager: DatabaseConnectionManager,
    private stateManager: StateManager
  ) {
    super();
    this.alertConfig = this.loadAlertConfig();
  }

  /**
   * Start monitoring
   */
  startMonitoring(intervalMs: number = 5000): void {
    if (this.isMonitoring) {
      this.logger.warn('Monitoring already active');
      return;
    }

    this.logger.info('Starting health monitoring', { intervalMs });
    this.isMonitoring = true;

    this.monitoringInterval = setInterval(async () => {
      try {
        await this.collectMetrics();
        this.checkThresholds();
      } catch (error) {
        this.logger.error('Error collecting metrics', error);
      }
    }, intervalMs);

    this.emit('monitoringStarted');
  }

  /**
   * Stop monitoring
   */
  stopMonitoring(): void {
    if (!this.isMonitoring) {
      return;
    }

    this.logger.info('Stopping health monitoring');

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }

    this.isMonitoring = false;
    this.emit('monitoringStopped');
  }

  /**
   * Perform comprehensive health check
   */
  async performHealthCheck(): Promise<HealthCheck> {
    this.logger.info('Performing health check');

    const startTime = Date.now();
    const connection = this.dbManager.getActive();

    if (!connection) {
      throw new Error('No active database connection');
    }

    try {
      // Test query response time
      const queryStart = Date.now();
      await this.testQuery(connection.type, connection.client);
      const responseTime = Date.now() - queryStart;

      // Get connection stats
      const stats = this.dbManager.getStatistics();

      // Get database-specific metrics
      const dbMetrics = await this.getDatabaseMetrics(connection.type, connection.client);

      const healthCheck: HealthCheck = {
        connectionCount: {
          name: 'Active Connections',
          value: stats.totalConnections,
          unit: 'connections',
          status: stats.totalConnections > 0 ? 'healthy' : 'warning',
          timestamp: Date.now()
        },
        responseTime: {
          name: 'Response Time',
          value: responseTime,
          unit: 'ms',
          status: this.getResponseTimeStatus(responseTime),
          timestamp: Date.now()
        },
        errorRate: {
          name: 'Error Rate',
          value: 0, // TODO: Track errors over time
          unit: '%',
          status: 'healthy',
          timestamp: Date.now()
        },
        ...dbMetrics
      };

      // Store metrics
      this.storeMetrics(healthCheck);

      this.logger.info('Health check complete', {
        duration: Date.now() - startTime,
        status: this.getOverallStatus(healthCheck)
      });

      return healthCheck;
    } catch (error) {
      this.logger.error('Health check failed', error);
      throw error;
    }
  }

  /**
   * Collect metrics periodically
   */
  private async collectMetrics(): Promise<void> {
    try {
      const healthCheck = await this.performHealthCheck();
      this.emit('metricsCollected', healthCheck);
    } catch (error) {
      this.logger.error('Failed to collect metrics', error);
    }
  }

  /**
   * Test database query
   */
  private async testQuery(type: DatabaseType, client: any): Promise<void> {
    switch (type) {
      case DatabaseType.POSTGRESQL:
        await client.query('SELECT 1');
        break;

      case DatabaseType.MYSQL:
        await client.query('SELECT 1');
        break;

      case DatabaseType.SQLITE:
        await new Promise((resolve, reject) => {
          client.get('SELECT 1', (err: Error, row: any) => {
            if (err) reject(err);
            else resolve(row);
          });
        });
        break;

      case DatabaseType.MONGODB:
        await client.db().admin().ping();
        break;
    }
  }

  /**
   * Get database-specific metrics
   */
  private async getDatabaseMetrics(
    type: DatabaseType,
    client: any
  ): Promise<Partial<HealthCheck>> {
    try {
      switch (type) {
        case DatabaseType.POSTGRESQL:
          return await this.getPostgreSQLMetrics(client);

        case DatabaseType.MYSQL:
          return await this.getMySQLMetrics(client);

        case DatabaseType.MONGODB:
          return await this.getMongoDBMetrics(client);

        default:
          return {};
      }
    } catch (error) {
      this.logger.warn('Failed to get database metrics', { error });
      return {};
    }
  }

  /**
   * Get PostgreSQL metrics
   */
  private async getPostgreSQLMetrics(client: any): Promise<Partial<HealthCheck>> {
    const result = await client.query(`
      SELECT
        count(*) as active_queries,
        (SELECT count(*) FROM pg_stat_database WHERE datname = current_database()) as connections
      FROM pg_stat_activity
      WHERE state = 'active'
    `);

    return {
      activeQueries: {
        name: 'Active Queries',
        value: parseInt(result.rows[0].active_queries),
        unit: 'queries',
        status: 'healthy',
        timestamp: Date.now()
      }
    };
  }

  /**
   * Get MySQL metrics
   */
  private async getMySQLMetrics(client: any): Promise<Partial<HealthCheck>> {
    const [result] = await client.query('SHOW STATUS LIKE "Threads_connected"');

    return {
      activeQueries: {
        name: 'Active Connections',
        value: parseInt((result as any[])[0].Value),
        unit: 'connections',
        status: 'healthy',
        timestamp: Date.now()
      }
    };
  }

  /**
   * Get MongoDB metrics
   */
  private async getMongoDBMetrics(client: any): Promise<Partial<HealthCheck>> {
    const stats = await client.db().stats();

    return {
      memoryUsage: {
        name: 'Memory Usage',
        value: stats.dataSize / (1024 * 1024),
        unit: 'MB',
        status: 'healthy',
        timestamp: Date.now()
      }
    };
  }

  /**
   * Check metric thresholds and trigger alerts
   */
  private checkThresholds(): void {
    const connection = this.dbManager.getActive();
    if (!connection) return;

    // Get latest metrics
    const latestMetrics = this.getLatestMetrics();

    // Check response time
    const responseTime = latestMetrics.get('responseTime');
    if (responseTime && responseTime.value > this.alertConfig.thresholds.responseTime) {
      this.triggerAlert({
        type: 'warning',
        metric: 'responseTime',
        message: `Response time (${responseTime.value}ms) exceeds threshold`,
        value: responseTime.value,
        threshold: this.alertConfig.thresholds.responseTime
      });
    }

    // Check error rate
    const errorRate = latestMetrics.get('errorRate');
    if (errorRate && errorRate.value > this.alertConfig.thresholds.errorRate) {
      this.triggerAlert({
        type: 'critical',
        metric: 'errorRate',
        message: `Error rate (${errorRate.value}%) exceeds threshold`,
        value: errorRate.value,
        threshold: this.alertConfig.thresholds.errorRate
      });
    }
  }

  /**
   * Trigger alert
   */
  private async triggerAlert(alertData: Omit<Alert, 'id' | 'timestamp' | 'resolved'>): Promise<void> {
    const alert: Alert = {
      id: `${alertData.metric}-${Date.now()}`,
      timestamp: Date.now(),
      resolved: false,
      ...alertData
    };

    this.alerts.set(alert.id, alert);
    this.logger.warn('Alert triggered', alert);

    // Send notifications
    await this.sendAlertNotifications(alert);

    this.emit('alertTriggered', alert);
  }

  /**
   * Send alert notifications
   */
  private async sendAlertNotifications(alert: Alert): Promise<void> {
    if (!this.alertConfig.enabled) {
      return;
    }

    // Slack notification
    if (this.alertConfig.channels.slack?.enabled) {
      await this.sendSlackAlert(alert);
    }

    // Email notification
    if (this.alertConfig.channels.email?.enabled) {
      await this.sendEmailAlert(alert);
    }

    // Webhook notification
    if (this.alertConfig.channels.webhook?.enabled) {
      await this.sendWebhookAlert(alert);
    }
  }

  /**
   * Send Slack alert
   */
  private async sendSlackAlert(alert: Alert): Promise<void> {
    try {
      const webhookUrl = this.alertConfig.channels.slack?.webhookUrl;
      if (!webhookUrl) return;

      await axios.post(webhookUrl, {
        text: `🚨 *${alert.type.toUpperCase()} Alert*`,
        attachments: [
          {
            color: alert.type === 'critical' ? 'danger' : 'warning',
            fields: [
              { title: 'Metric', value: alert.metric, short: true },
              { title: 'Value', value: `${alert.value}`, short: true },
              { title: 'Threshold', value: `${alert.threshold}`, short: true },
              { title: 'Message', value: alert.message }
            ],
            timestamp: Math.floor(alert.timestamp / 1000)
          }
        ]
      });

      this.logger.info('Slack alert sent', { alertId: alert.id });
    } catch (error) {
      this.logger.error('Failed to send Slack alert', error);
    }
  }

  /**
   * Send email alert (placeholder - requires email library)
   */
  private async sendEmailAlert(alert: Alert): Promise<void> {
    this.logger.info('Email alert (not implemented)', { alertId: alert.id });
    // TODO: Implement with nodemailer
  }

  /**
   * Send webhook alert
   */
  private async sendWebhookAlert(alert: Alert): Promise<void> {
    try {
      const webhookUrl = this.alertConfig.channels.webhook?.url;
      if (!webhookUrl) return;

      await axios.post(webhookUrl, alert);
      this.logger.info('Webhook alert sent', { alertId: alert.id });
    } catch (error) {
      this.logger.error('Failed to send webhook alert', error);
    }
  }

  /**
   * Configure alerts
   */
  configureAlerts(config: Partial<AlertConfig>): void {
    this.alertConfig = {
      ...this.alertConfig,
      ...config
    };

    this.saveAlertConfig();
    this.logger.info('Alert configuration updated');
  }

  /**
   * Get alert configuration
   */
  getAlertConfig(): AlertConfig {
    return this.alertConfig;
  }

  /**
   * Get active alerts
   */
  getActiveAlerts(): Alert[] {
    return Array.from(this.alerts.values()).filter((a) => !a.resolved);
  }

  /**
   * Resolve alert
   */
  resolveAlert(alertId: string): void {
    const alert = this.alerts.get(alertId);
    if (alert) {
      alert.resolved = true;
      this.emit('alertResolved', alert);
      this.logger.info('Alert resolved', { alertId });
    }
  }

  /**
   * Get metrics history
   */
  getMetricsHistory(metricName: string, limit: number = 100): HealthMetric[] {
    const history = this.metrics.get(metricName) || [];
    return history.slice(-limit);
  }

  /**
   * Store metrics
   */
  private storeMetrics(healthCheck: HealthCheck): void {
    Object.values(healthCheck).forEach((metric) => {
      if (!metric) return;

      const history = this.metrics.get(metric.name) || [];
      history.push(metric);

      // Keep only last 1000 entries
      if (history.length > 1000) {
        history.shift();
      }

      this.metrics.set(metric.name, history);
    });
  }

  /**
   * Get latest metrics
   */
  private getLatestMetrics(): Map<string, HealthMetric> {
    const latest = new Map<string, HealthMetric>();

    for (const [name, history] of this.metrics.entries()) {
      if (history.length > 0) {
        latest.set(name, history[history.length - 1]);
      }
    }

    return latest;
  }

  /**
   * Get response time status
   */
  private getResponseTimeStatus(responseTime: number): 'healthy' | 'warning' | 'critical' {
    if (responseTime < 100) return 'healthy';
    if (responseTime < 500) return 'warning';
    return 'critical';
  }

  /**
   * Get overall health status
   */
  private getOverallStatus(healthCheck: HealthCheck): 'healthy' | 'warning' | 'critical' {
    const statuses = Object.values(healthCheck)
      .filter((m): m is HealthMetric => m !== undefined)
      .map((m) => m.status);

    if (statuses.includes('critical')) return 'critical';
    if (statuses.includes('warning')) return 'warning';
    return 'healthy';
  }

  /**
   * Load alert config from state
   */
  private loadAlertConfig(): AlertConfig {
    try {
      const stored = this.stateManager.get('alert-config');
      if (stored) {
        return stored as AlertConfig;
      }
    } catch (error) {
      this.logger.warn('Failed to load alert config', { error });
    }

    // Default configuration
    return {
      enabled: false,
      channels: {},
      thresholds: {
        responseTime: 1000,
        errorRate: 5,
        cpuUsage: 80,
        memoryUsage: 85,
        diskSpace: 90
      }
    };
  }

  /**
   * Save alert config to state
   */
  private saveAlertConfig(): void {
    try {
      this.stateManager.set('alert-config', this.alertConfig, {
        metadata: { type: 'alert-configuration' }
      });
    } catch (error) {
      this.logger.error('Failed to save alert config', error);
    }
  }
}
