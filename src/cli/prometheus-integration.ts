/**
 * Prometheus Integration for AI-Shell
 * Exports metrics in Prometheus format for monitoring and alerting
 * Commands: ai-shell prometheus start/stop/status/configure
 */

import http, { IncomingMessage, ServerResponse } from 'http';
import { URL } from 'url';
import { createHash, randomBytes } from 'crypto';
import { EventEmitter } from 'eventemitter3';
import { HealthMonitor } from './health-monitor';
import { DatabaseConnectionManager } from './database-manager';
import { StateManager } from '../core/state-manager';
import { createLogger } from '../core/logger';

// Prometheus metric types
enum MetricType {
  COUNTER = 'counter',
  GAUGE = 'gauge',
  HISTOGRAM = 'histogram',
  SUMMARY = 'summary'
}

// Metric value with labels
interface MetricValue {
  value: number;
  labels: Record<string, string>;
  timestamp?: number;
}

// Metric definition
interface Metric {
  name: string;
  type: MetricType;
  help: string;
  values: MetricValue[];
}

// Histogram bucket definition
interface HistogramBucket {
  le: number; // less than or equal
  count: number;
}

// Histogram metric
interface HistogramMetric extends Metric {
  buckets: Map<string, HistogramBucket[]>; // Key: label combination
  sum: Map<string, number>;
  count: Map<string, number>;
}

// Prometheus server configuration
interface PrometheusConfig {
  enabled: boolean;
  port: number;
  host: string;
  path: string;
  scrapeInterval: number; // seconds
  authentication: {
    enabled: boolean;
    type: 'basic' | 'bearer' | 'api-key';
    credentials?: {
      username?: string;
      password?: string;
      token?: string;
      apiKey?: string;
    };
  };
  labels: Record<string, string>; // Global labels
  retention: number; // How long to keep metrics in memory (seconds)
}

// Authentication result
interface AuthResult {
  authenticated: boolean;
  error?: string;
}

// Server status
interface ServerStatus {
  running: boolean;
  uptime: number;
  metricsCount: number;
  scrapeCount: number;
  lastScrape?: number;
  config: PrometheusConfig;
}

/**
 * Prometheus Metrics Collector
 * Collects and formats metrics in Prometheus exposition format
 */
export class PrometheusMetricsCollector extends EventEmitter {
  private logger = createLogger('PrometheusMetrics');
  private metrics = new Map<string, Metric>();
  private histogramBuckets: number[] = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10];

  constructor(private config: PrometheusConfig) {
    super();
    this.initializeDefaultMetrics();
  }

  /**
   * Initialize default AI-Shell metrics
   */
  private initializeDefaultMetrics(): void {
    // Counter: Total queries executed
    this.registerMetric({
      name: 'ai_shell_queries_total',
      type: MetricType.COUNTER,
      help: 'Total number of database queries executed',
      values: []
    });

    // Counter: Total errors
    this.registerMetric({
      name: 'ai_shell_errors_total',
      type: MetricType.COUNTER,
      help: 'Total number of errors encountered',
      values: []
    });

    // Histogram: Query duration
    this.registerHistogram({
      name: 'ai_shell_query_duration_seconds',
      type: MetricType.HISTOGRAM,
      help: 'Query execution duration in seconds',
      values: [],
      buckets: new Map(),
      sum: new Map(),
      count: new Map()
    });

    // Gauge: Active connections
    this.registerMetric({
      name: 'ai_shell_active_connections',
      type: MetricType.GAUGE,
      help: 'Number of active database connections',
      values: []
    });

    // Gauge: Connection pool size
    this.registerMetric({
      name: 'ai_shell_connection_pool_size',
      type: MetricType.GAUGE,
      help: 'Database connection pool size',
      values: []
    });

    // Gauge: Cache hit ratio
    this.registerMetric({
      name: 'ai_shell_cache_hit_ratio',
      type: MetricType.GAUGE,
      help: 'Query cache hit ratio (0-1)',
      values: []
    });

    // Gauge: Optimization score
    this.registerMetric({
      name: 'ai_shell_optimization_score',
      type: MetricType.GAUGE,
      help: 'Query optimization score (0-100)',
      values: []
    });

    // Gauge: Response time
    this.registerMetric({
      name: 'ai_shell_response_time_milliseconds',
      type: MetricType.GAUGE,
      help: 'Database response time in milliseconds',
      values: []
    });

    // Counter: NL query translations
    this.registerMetric({
      name: 'ai_shell_nl_translations_total',
      type: MetricType.COUNTER,
      help: 'Total number of natural language query translations',
      values: []
    });

    // Counter: Cache hits
    this.registerMetric({
      name: 'ai_shell_cache_hits_total',
      type: MetricType.COUNTER,
      help: 'Total number of cache hits',
      values: []
    });

    // Counter: Cache misses
    this.registerMetric({
      name: 'ai_shell_cache_misses_total',
      type: MetricType.COUNTER,
      help: 'Total number of cache misses',
      values: []
    });

    this.logger.info('Default metrics initialized');
  }

  /**
   * Register a new metric
   */
  private registerMetric(metric: Metric): void {
    this.metrics.set(metric.name, metric);
  }

  /**
   * Register a histogram metric
   */
  private registerHistogram(metric: HistogramMetric): void {
    this.metrics.set(metric.name, metric);
  }

  /**
   * Increment counter metric
   */
  incrementCounter(name: string, labels: Record<string, string> = {}, value: number = 1): void {
    const metric = this.metrics.get(name);
    if (!metric || metric.type !== MetricType.COUNTER) {
      this.logger.warn('Counter metric not found', { name });
      return;
    }

    const existingValue = this.findMetricValue(metric, labels);
    if (existingValue) {
      existingValue.value += value;
      existingValue.timestamp = Date.now();
    } else {
      metric.values.push({
        value,
        labels: { ...this.config.labels, ...labels },
        timestamp: Date.now()
      });
    }

    this.emit('metricUpdated', { name, type: 'counter', value, labels });
  }

  /**
   * Set gauge metric
   */
  setGauge(name: string, value: number, labels: Record<string, string> = {}): void {
    const metric = this.metrics.get(name);
    if (!metric || metric.type !== MetricType.GAUGE) {
      this.logger.warn('Gauge metric not found', { name });
      return;
    }

    const existingValue = this.findMetricValue(metric, labels);
    if (existingValue) {
      existingValue.value = value;
      existingValue.timestamp = Date.now();
    } else {
      metric.values.push({
        value,
        labels: { ...this.config.labels, ...labels },
        timestamp: Date.now()
      });
    }

    this.emit('metricUpdated', { name, type: 'gauge', value, labels });
  }

  /**
   * Observe histogram metric
   */
  observeHistogram(name: string, value: number, labels: Record<string, string> = {}): void {
    const metric = this.metrics.get(name) as HistogramMetric;
    if (!metric || metric.type !== MetricType.HISTOGRAM) {
      this.logger.warn('Histogram metric not found', { name });
      return;
    }

    const labelKey = this.getLabelKey({ ...this.config.labels, ...labels });

    // Initialize buckets if needed
    if (!metric.buckets.has(labelKey)) {
      metric.buckets.set(
        labelKey,
        this.histogramBuckets.map((le) => ({ le, count: 0 }))
      );
      metric.sum.set(labelKey, 0);
      metric.count.set(labelKey, 0);
    }

    // Update buckets
    const buckets = metric.buckets.get(labelKey)!;
    for (const bucket of buckets) {
      if (value <= bucket.le) {
        bucket.count++;
      }
    }

    // Update sum and count
    metric.sum.set(labelKey, metric.sum.get(labelKey)! + value);
    metric.count.set(labelKey, metric.count.get(labelKey)! + 1);

    this.emit('metricUpdated', { name, type: 'histogram', value, labels });
  }

  /**
   * Find existing metric value with matching labels
   */
  private findMetricValue(metric: Metric, labels: Record<string, string>): MetricValue | undefined {
    const targetKey = this.getLabelKey({ ...this.config.labels, ...labels });
    return metric.values.find((v) => this.getLabelKey(v.labels) === targetKey);
  }

  /**
   * Get label key for grouping
   */
  private getLabelKey(labels: Record<string, string>): string {
    return Object.keys(labels)
      .sort()
      .map((key) => `${key}="${labels[key]}"`)
      .join(',');
  }

  /**
   * Format metrics in Prometheus exposition format
   */
  formatMetrics(): string {
    const lines: string[] = [];

    for (const metric of this.metrics.values()) {
      // Add HELP line
      lines.push(`# HELP ${metric.name} ${metric.help}`);

      // Add TYPE line
      lines.push(`# TYPE ${metric.name} ${metric.type}`);

      if (metric.type === MetricType.HISTOGRAM) {
        lines.push(...this.formatHistogram(metric as HistogramMetric));
      } else {
        lines.push(...this.formatSimpleMetric(metric));
      }

      lines.push(''); // Empty line between metrics
    }

    return lines.join('\n');
  }

  /**
   * Format simple metric (counter, gauge)
   */
  private formatSimpleMetric(metric: Metric): string[] {
    return metric.values.map((value) => {
      const labelsStr = this.formatLabels(value.labels);
      return `${metric.name}${labelsStr} ${value.value}`;
    });
  }

  /**
   * Format histogram metric
   */
  private formatHistogram(metric: HistogramMetric): string[] {
    const lines: string[] = [];

    for (const [labelKey, buckets] of metric.buckets.entries()) {
      const labels = this.parseLabelKey(labelKey);

      // Add bucket lines
      for (const bucket of buckets) {
        const bucketLabels = { ...labels, le: bucket.le.toString() };
        const labelsStr = this.formatLabels(bucketLabels);
        lines.push(`${metric.name}_bucket${labelsStr} ${bucket.count}`);
      }

      // Add +Inf bucket
      const infLabels = { ...labels, le: '+Inf' };
      const infLabelsStr = this.formatLabels(infLabels);
      const totalCount = metric.count.get(labelKey) || 0;
      lines.push(`${metric.name}_bucket${infLabelsStr} ${totalCount}`);

      // Add sum
      const sumLabelsStr = this.formatLabels(labels);
      const sum = metric.sum.get(labelKey) || 0;
      lines.push(`${metric.name}_sum${sumLabelsStr} ${sum}`);

      // Add count
      lines.push(`${metric.name}_count${sumLabelsStr} ${totalCount}`);
    }

    return lines;
  }

  /**
   * Format labels for Prometheus
   */
  private formatLabels(labels: Record<string, string>): string {
    if (Object.keys(labels).length === 0) {
      return '';
    }

    const pairs = Object.entries(labels)
      .map(([key, value]) => `${key}="${this.escapeLabel(value)}"`)
      .join(',');

    return `{${pairs}}`;
  }

  /**
   * Escape label value for Prometheus format
   */
  private escapeLabel(value: string): string {
    return value
      .replace(/\\/g, '\\\\')
      .replace(/"/g, '\\"')
      .replace(/\n/g, '\\n');
  }

  /**
   * Parse label key back to labels object
   */
  private parseLabelKey(labelKey: string): Record<string, string> {
    const labels: Record<string, string> = {};

    if (!labelKey) return labels;

    const pairs = labelKey.split(',');
    for (const pair of pairs) {
      const match = pair.match(/^(.+?)="(.+)"$/);
      if (match) {
        labels[match[1]] = match[2];
      }
    }

    return labels;
  }

  /**
   * Clean old metrics based on retention policy
   */
  cleanOldMetrics(): void {
    const cutoff = Date.now() - this.config.retention * 1000;
    let cleaned = 0;

    for (const metric of this.metrics.values()) {
      if (metric.type !== MetricType.HISTOGRAM) {
        const before = metric.values.length;
        metric.values = metric.values.filter((v) => !v.timestamp || v.timestamp >= cutoff);
        cleaned += before - metric.values.length;
      }
    }

    if (cleaned > 0) {
      this.logger.debug('Cleaned old metrics', { count: cleaned });
    }
  }

  /**
   * Reset all metrics
   */
  reset(): void {
    for (const metric of this.metrics.values()) {
      metric.values = [];

      if (metric.type === MetricType.HISTOGRAM) {
        const histMetric = metric as HistogramMetric;
        histMetric.buckets.clear();
        histMetric.sum.clear();
        histMetric.count.clear();
      }
    }

    this.logger.info('All metrics reset');
    this.emit('metricsReset');
  }

  /**
   * Get metric by name
   */
  getMetric(name: string): Metric | undefined {
    return this.metrics.get(name);
  }

  /**
   * Get all metrics
   */
  getAllMetrics(): Metric[] {
    return Array.from(this.metrics.values());
  }
}

/**
 * Prometheus HTTP Server
 * Serves metrics over HTTP for Prometheus scraping
 */
export class PrometheusServer extends EventEmitter {
  private logger = createLogger('PrometheusServer');
  private server?: http.Server;
  private collector: PrometheusMetricsCollector;
  private scrapeCount = 0;
  private lastScrape?: number;
  private startTime?: number;
  private cleanupInterval?: NodeJS.Timeout;

  constructor(
    private config: PrometheusConfig,
    private healthMonitor?: HealthMonitor
  ) {
    super();
    this.collector = new PrometheusMetricsCollector(config);

    // Forward collector events
    this.collector.on('metricUpdated', (data) => this.emit('metricUpdated', data));
    this.collector.on('metricsReset', () => this.emit('metricsReset'));
  }

  /**
   * Start Prometheus server
   */
  async start(): Promise<void> {
    if (this.server) {
      throw new Error('Prometheus server already running');
    }

    return new Promise((resolve, reject) => {
      try {
        this.server = http.createServer((req, res) => {
          this.handleRequest(req, res);
        });

        this.server.on('error', (error) => {
          this.logger.error('Server error', error);
          this.emit('error', error);
        });

        this.server.listen(this.config.port, this.config.host, () => {
          this.startTime = Date.now();
          this.logger.info('Prometheus server started', {
            host: this.config.host,
            port: this.config.port,
            path: this.config.path
          });

          // Start metrics cleanup interval
          this.cleanupInterval = setInterval(() => {
            this.collector.cleanOldMetrics();
          }, 60000); // Every minute

          // Start health monitoring integration if available
          if (this.healthMonitor) {
            this.startHealthMonitorIntegration();
          }

          this.emit('started');
          resolve();
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Stop Prometheus server
   */
  async stop(): Promise<void> {
    if (!this.server) {
      return;
    }

    return new Promise((resolve, reject) => {
      this.server!.close((error) => {
        if (error) {
          this.logger.error('Error stopping server', error);
          reject(error);
        } else {
          this.server = undefined;
          this.startTime = undefined;

          if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
            this.cleanupInterval = undefined;
          }

          this.logger.info('Prometheus server stopped');
          this.emit('stopped');
          resolve();
        }
      });
    });
  }

  /**
   * Handle HTTP request
   */
  private async handleRequest(req: IncomingMessage, res: ServerResponse): Promise<void> {
    const url = new URL(req.url || '/', `http://${req.headers.host}`);

    // Handle metrics endpoint
    if (url.pathname === this.config.path && req.method === 'GET') {
      await this.handleMetricsRequest(req, res);
      return;
    }

    // Handle health endpoint
    if (url.pathname === '/health' && req.method === 'GET') {
      this.handleHealthRequest(req, res);
      return;
    }

    // 404 for other endpoints
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  }

  /**
   * Handle metrics request
   */
  private async handleMetricsRequest(req: IncomingMessage, res: ServerResponse): Promise<void> {
    try {
      // Authenticate request
      const authResult = await this.authenticateRequest(req);
      if (!authResult.authenticated) {
        res.writeHead(401, {
          'Content-Type': 'text/plain',
          'WWW-Authenticate': this.getAuthenticateHeader()
        });
        res.end(`Unauthorized: ${authResult.error || 'Authentication required'}`);
        return;
      }

      // Update scrape metrics
      this.scrapeCount++;
      this.lastScrape = Date.now();

      // Format metrics
      const metrics = this.collector.formatMetrics();

      // Send response
      res.writeHead(200, {
        'Content-Type': 'text/plain; version=0.0.4',
        'Content-Length': Buffer.byteLength(metrics)
      });
      res.end(metrics);

      this.emit('scraped', { count: this.scrapeCount, timestamp: this.lastScrape });
    } catch (error) {
      this.logger.error('Error handling metrics request', error);
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Internal Server Error');
    }
  }

  /**
   * Handle health request
   */
  private handleHealthRequest(req: IncomingMessage, res: ServerResponse): void {
    const status = this.getStatus();
    const health = {
      status: 'healthy',
      uptime: status.uptime,
      metricsCount: status.metricsCount,
      scrapeCount: status.scrapeCount,
      lastScrape: status.lastScrape
    };

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(health, null, 2));
  }

  /**
   * Authenticate request
   */
  private async authenticateRequest(req: IncomingMessage): Promise<AuthResult> {
    if (!this.config.authentication.enabled) {
      return { authenticated: true };
    }

    const authHeader = req.headers.authorization;
    if (!authHeader) {
      return { authenticated: false, error: 'Missing authorization header' };
    }

    const { type, credentials } = this.config.authentication;

    switch (type) {
      case 'basic':
        return this.authenticateBasic(authHeader, credentials);

      case 'bearer':
        return this.authenticateBearer(authHeader, credentials);

      case 'api-key':
        return this.authenticateApiKey(req, credentials);

      default:
        return { authenticated: false, error: 'Unknown authentication type' };
    }
  }

  /**
   * Authenticate with Basic auth
   */
  private authenticateBasic(authHeader: string, credentials?: any): AuthResult {
    const match = authHeader.match(/^Basic\s+(.+)$/i);
    if (!match) {
      return { authenticated: false, error: 'Invalid Basic auth format' };
    }

    const decoded = Buffer.from(match[1], 'base64').toString('utf-8');
    const [username, password] = decoded.split(':', 2);

    if (
      username === credentials?.username &&
      password === credentials?.password
    ) {
      return { authenticated: true };
    }

    return { authenticated: false, error: 'Invalid credentials' };
  }

  /**
   * Authenticate with Bearer token
   */
  private authenticateBearer(authHeader: string, credentials?: any): AuthResult {
    const match = authHeader.match(/^Bearer\s+(.+)$/i);
    if (!match) {
      return { authenticated: false, error: 'Invalid Bearer token format' };
    }

    const token = match[1];
    if (token === credentials?.token) {
      return { authenticated: true };
    }

    return { authenticated: false, error: 'Invalid token' };
  }

  /**
   * Authenticate with API key
   */
  private authenticateApiKey(req: IncomingMessage, credentials?: any): AuthResult {
    const apiKey = req.headers['x-api-key'] as string;
    if (!apiKey) {
      return { authenticated: false, error: 'Missing API key' };
    }

    if (apiKey === credentials?.apiKey) {
      return { authenticated: true };
    }

    return { authenticated: false, error: 'Invalid API key' };
  }

  /**
   * Get WWW-Authenticate header value
   */
  private getAuthenticateHeader(): string {
    switch (this.config.authentication.type) {
      case 'basic':
        return 'Basic realm="Prometheus Metrics"';

      case 'bearer':
        return 'Bearer realm="Prometheus Metrics"';

      case 'api-key':
        return 'API-Key';

      default:
        return '';
    }
  }

  /**
   * Start health monitor integration
   */
  private startHealthMonitorIntegration(): void {
    if (!this.healthMonitor) return;

    this.healthMonitor.on('metricsCollected', (healthCheck) => {
      // Update gauges from health check
      if (healthCheck.connectionCount) {
        this.collector.setGauge(
          'ai_shell_active_connections',
          healthCheck.connectionCount.value,
          { status: healthCheck.connectionCount.status }
        );
      }

      if (healthCheck.responseTime) {
        this.collector.setGauge(
          'ai_shell_response_time_milliseconds',
          healthCheck.responseTime.value,
          { status: healthCheck.responseTime.status }
        );
      }

      if (healthCheck.cacheHitRate) {
        this.collector.setGauge(
          'ai_shell_cache_hit_ratio',
          healthCheck.cacheHitRate.value / 100,
          {}
        );
      }
    });

    this.logger.info('Health monitor integration started');
  }

  /**
   * Get collector for manual metric updates
   */
  getCollector(): PrometheusMetricsCollector {
    return this.collector;
  }

  /**
   * Get server status
   */
  getStatus(): ServerStatus {
    return {
      running: !!this.server,
      uptime: this.startTime ? Date.now() - this.startTime : 0,
      metricsCount: this.collector.getAllMetrics().length,
      scrapeCount: this.scrapeCount,
      lastScrape: this.lastScrape,
      config: this.config
    };
  }

  /**
   * Check if server is running
   */
  isRunning(): boolean {
    return !!this.server;
  }
}

/**
 * Prometheus Integration Manager
 * Main interface for Prometheus integration
 */
export class PrometheusIntegration {
  private logger = createLogger('PrometheusIntegration');
  private server?: PrometheusServer;
  private config: PrometheusConfig;

  constructor(
    private stateManager: StateManager,
    private healthMonitor?: HealthMonitor,
    private dbManager?: DatabaseConnectionManager
  ) {
    this.config = this.loadConfig();
  }

  /**
   * Start Prometheus server
   */
  async start(options?: Partial<PrometheusConfig>): Promise<void> {
    if (this.server?.isRunning()) {
      throw new Error('Prometheus server already running');
    }

    // Merge options with existing config
    if (options) {
      this.config = { ...this.config, ...options };
      this.saveConfig();
    }

    this.server = new PrometheusServer(this.config, this.healthMonitor);

    // Setup event listeners
    this.server.on('started', () => {
      this.logger.info('Prometheus integration started');
    });

    this.server.on('stopped', () => {
      this.logger.info('Prometheus integration stopped');
    });

    this.server.on('error', (error) => {
      this.logger.error('Prometheus server error', error);
    });

    await this.server.start();
  }

  /**
   * Stop Prometheus server
   */
  async stop(): Promise<void> {
    if (!this.server?.isRunning()) {
      throw new Error('Prometheus server not running');
    }

    await this.server.stop();
    this.server = undefined;
  }

  /**
   * Get server status
   */
  getStatus(): ServerStatus | null {
    if (!this.server) {
      return null;
    }

    return this.server.getStatus();
  }

  /**
   * Configure Prometheus integration
   */
  configure(config: Partial<PrometheusConfig>): void {
    this.config = { ...this.config, ...config };
    this.saveConfig();
    this.logger.info('Prometheus configuration updated');
  }

  /**
   * Get current configuration
   */
  getConfig(): PrometheusConfig {
    return this.config;
  }

  /**
   * Get metrics collector (if server is running)
   */
  getCollector(): PrometheusMetricsCollector | undefined {
    return this.server?.getCollector();
  }

  /**
   * Generate API key for authentication
   */
  generateApiKey(): string {
    return randomBytes(32).toString('hex');
  }

  /**
   * Generate bearer token for authentication
   */
  generateBearerToken(): string {
    return randomBytes(48).toString('base64url');
  }

  /**
   * Hash password for basic auth
   */
  hashPassword(password: string): string {
    return createHash('sha256').update(password).digest('hex');
  }

  /**
   * Load configuration from state
   */
  private loadConfig(): PrometheusConfig {
    try {
      const stored = this.stateManager.get('prometheus-config');
      if (stored) {
        return stored as PrometheusConfig;
      }
    } catch (error) {
      this.logger.warn('Failed to load Prometheus config', { error });
    }

    // Default configuration
    return {
      enabled: false,
      port: 9090,
      host: '0.0.0.0',
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
      retention: 3600 // 1 hour
    };
  }

  /**
   * Save configuration to state
   */
  private saveConfig(): void {
    try {
      this.stateManager.set('prometheus-config', this.config, {
        metadata: { type: 'prometheus-configuration' }
      });
    } catch (error) {
      this.logger.error('Failed to save Prometheus config', error);
    }
  }
}
