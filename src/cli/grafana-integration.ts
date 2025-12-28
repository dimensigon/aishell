#!/usr/bin/env node

/**
 * Grafana Integration for AI-Shell
 *
 * Provides comprehensive Grafana dashboard management with:
 * - Automatic data source configuration
 * - Pre-built dashboard templates
 * - Panel generation for key metrics
 * - Alert rule creation
 * - Dashboard JSON export/import
 * - Multi-dashboard support
 *
 * @module grafana-integration
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import * as fs from 'fs/promises';
import * as path from 'path';
import { Command } from 'commander';

// ============================================================================
// Types and Interfaces
// ============================================================================

interface GrafanaConfig {
  url: string;
  apiKey: string;
  organizationId?: number;
  timeout?: number;
}

interface DataSource {
  id?: number;
  uid?: string;
  name: string;
  type: string;
  url: string;
  access: 'proxy' | 'direct';
  basicAuth: boolean;
  isDefault: boolean;
  jsonData?: Record<string, any>;
}

interface Panel {
  id: number;
  title: string;
  type: string;
  gridPos: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  targets: PanelTarget[];
  options?: Record<string, any>;
  fieldConfig?: any;
  alert?: AlertRule;
}

interface PanelTarget {
  expr: string;
  legendFormat?: string;
  refId: string;
  interval?: string;
}

interface AlertRule {
  name: string;
  conditions: AlertCondition[];
  frequency: string;
  handler: number;
  notifications: AlertNotification[];
}

interface AlertCondition {
  evaluator: {
    params: number[];
    type: string;
  };
  operator: {
    type: string;
  };
  query: {
    params: string[];
  };
  reducer: {
    params: [];
    type: string;
  };
  type: string;
}

interface AlertNotification {
  uid: string;
}

interface Dashboard {
  uid?: string;
  title: string;
  tags: string[];
  timezone: string;
  panels: Panel[];
  templating: {
    list: DashboardVariable[];
  };
  time: {
    from: string;
    to: string;
  };
  refresh: string;
  schemaVersion: number;
  version: number;
}

interface DashboardVariable {
  name: string;
  type: string;
  datasource: string;
  query: string;
  refresh: number;
  multi: boolean;
  includeAll: boolean;
}

interface DashboardResponse {
  dashboard: Dashboard;
  meta: {
    type: string;
    canSave: boolean;
    canEdit: boolean;
    canDelete: boolean;
  };
}

// ============================================================================
// Grafana API Client
// ============================================================================

export class GrafanaClient {
  private client: AxiosInstance;
  private config: GrafanaConfig;

  constructor(config: GrafanaConfig) {
    this.config = config;
    this.client = axios.create({
      baseURL: config.url,
      timeout: config.timeout || 30000,
      headers: {
        'Authorization': `Bearer ${config.apiKey}`,
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Test connection to Grafana
   */
  async testConnection(): Promise<boolean> {
    try {
      const response = await this.client.get('/api/health');
      return response.status === 200;
    } catch (error) {
      this.handleError(error, 'Failed to connect to Grafana');
      return false;
    }
  }

  /**
   * Get or create Prometheus data source
   */
  async setupDataSource(prometheusUrl: string): Promise<DataSource> {
    try {
      // Check if data source exists
      const existing = await this.client.get('/api/datasources/name/AI-Shell-Prometheus');
      return existing.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        // Create new data source
        const dataSource: DataSource = {
          name: 'AI-Shell-Prometheus',
          type: 'prometheus',
          url: prometheusUrl,
          access: 'proxy',
          basicAuth: false,
          isDefault: true,
          jsonData: {
            httpMethod: 'POST',
            timeInterval: '15s',
          },
        };
        const response = await this.client.post('/api/datasources', dataSource);
        return response.data;
      }
      throw error;
    }
  }

  /**
   * Create or update dashboard
   */
  async saveDashboard(dashboard: Dashboard, folderId?: number): Promise<DashboardResponse> {
    try {
      const payload = {
        dashboard,
        folderId: folderId || 0,
        overwrite: true,
      };
      const response = await this.client.post('/api/dashboards/db', payload);
      return response.data;
    } catch (error) {
      this.handleError(error, 'Failed to save dashboard');
      throw error;
    }
  }

  /**
   * Get dashboard by UID
   */
  async getDashboard(uid: string): Promise<DashboardResponse> {
    try {
      const response = await this.client.get(`/api/dashboards/uid/${uid}`);
      return response.data;
    } catch (error) {
      this.handleError(error, 'Failed to get dashboard');
      throw error;
    }
  }

  /**
   * Delete dashboard
   */
  async deleteDashboard(uid: string): Promise<void> {
    try {
      await this.client.delete(`/api/dashboards/uid/${uid}`);
    } catch (error) {
      this.handleError(error, 'Failed to delete dashboard');
      throw error;
    }
  }

  /**
   * Search dashboards
   */
  async searchDashboards(tag?: string): Promise<any[]> {
    try {
      const params: any = { type: 'dash-db' };
      if (tag) params.tag = tag;
      const response = await this.client.get('/api/search', { params });
      return response.data;
    } catch (error) {
      this.handleError(error, 'Failed to search dashboards');
      throw error;
    }
  }

  /**
   * Create alert notification channel
   */
  async createNotificationChannel(name: string, type: string, settings: any): Promise<any> {
    try {
      const payload = {
        name,
        type,
        isDefault: false,
        sendReminder: true,
        settings,
      };
      const response = await this.client.post('/api/alert-notifications', payload);
      return response.data;
    } catch (error) {
      this.handleError(error, 'Failed to create notification channel');
      throw error;
    }
  }

  private handleError(error: unknown, message: string): void {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      console.error(`${message}:`, axiosError.response?.data || axiosError.message);
    } else {
      console.error(`${message}:`, error);
    }
  }
}

// ============================================================================
// Dashboard Builder
// ============================================================================

export class DashboardBuilder {
  private dashboard: Dashboard;
  private panelId: number = 1;

  constructor(title: string, tags: string[] = []) {
    this.dashboard = {
      title,
      tags: ['ai-shell', ...tags],
      timezone: 'browser',
      panels: [],
      templating: {
        list: [],
      },
      time: {
        from: 'now-6h',
        to: 'now',
      },
      refresh: '30s',
      schemaVersion: 27,
      version: 1,
    };
  }

  /**
   * Add variable to dashboard
   */
  addVariable(variable: DashboardVariable): this {
    this.dashboard.templating.list.push(variable);
    return this;
  }

  /**
   * Add panel to dashboard
   */
  addPanel(panel: Omit<Panel, 'id'>): this {
    this.dashboard.panels.push({
      ...panel,
      id: this.panelId++,
    });
    return this;
  }

  /**
   * Create graph panel
   */
  addGraphPanel(
    title: string,
    targets: PanelTarget[],
    x: number,
    y: number,
    w: number = 12,
    h: number = 8
  ): this {
    return this.addPanel({
      title,
      type: 'timeseries',
      gridPos: { x, y, w, h },
      targets,
      options: {
        legend: {
          displayMode: 'list',
          placement: 'bottom',
        },
        tooltip: {
          mode: 'multi',
        },
      },
      fieldConfig: {
        defaults: {
          custom: {
            lineWidth: 2,
            fillOpacity: 10,
          },
        },
      },
    });
  }

  /**
   * Create stat panel
   */
  addStatPanel(
    title: string,
    expr: string,
    x: number,
    y: number,
    w: number = 6,
    h: number = 4
  ): this {
    return this.addPanel({
      title,
      type: 'stat',
      gridPos: { x, y, w, h },
      targets: [{ expr, refId: 'A' }],
      options: {
        reduceOptions: {
          values: false,
          calcs: ['lastNotNull'],
        },
        textMode: 'auto',
        colorMode: 'value',
        graphMode: 'area',
      },
      fieldConfig: {
        defaults: {
          thresholds: {
            mode: 'absolute',
            steps: [
              { value: 0, color: 'green' },
              { value: 80, color: 'yellow' },
              { value: 90, color: 'red' },
            ],
          },
        },
      },
    });
  }

  /**
   * Create gauge panel
   */
  addGaugePanel(
    title: string,
    expr: string,
    x: number,
    y: number,
    w: number = 6,
    h: number = 6
  ): this {
    return this.addPanel({
      title,
      type: 'gauge',
      gridPos: { x, y, w, h },
      targets: [{ expr, refId: 'A' }],
      options: {
        reduceOptions: {
          values: false,
          calcs: ['lastNotNull'],
        },
        showThresholdLabels: true,
        showThresholdMarkers: true,
      },
      fieldConfig: {
        defaults: {
          min: 0,
          max: 100,
          thresholds: {
            mode: 'absolute',
            steps: [
              { value: 0, color: 'green' },
              { value: 70, color: 'yellow' },
              { value: 90, color: 'red' },
            ],
          },
          unit: 'percent',
        },
      },
    });
  }

  /**
   * Create table panel
   */
  addTablePanel(
    title: string,
    targets: PanelTarget[],
    x: number,
    y: number,
    w: number = 12,
    h: number = 8
  ): this {
    return this.addPanel({
      title,
      type: 'table',
      gridPos: { x, y, w, h },
      targets,
      options: {
        showHeader: true,
        sortBy: [],
      },
      fieldConfig: {
        defaults: {
          custom: {
            align: 'auto',
            displayMode: 'auto',
          },
        },
      },
    });
  }

  /**
   * Create heatmap panel
   */
  addHeatmapPanel(
    title: string,
    expr: string,
    x: number,
    y: number,
    w: number = 12,
    h: number = 8
  ): this {
    return this.addPanel({
      title,
      type: 'heatmap',
      gridPos: { x, y, w, h },
      targets: [{ expr, refId: 'A', legendFormat: '{{le}}' }],
      options: {
        calculate: true,
        calculation: {
          xBuckets: {
            mode: 'size',
            value: '1m',
          },
        },
        color: {
          mode: 'scheme',
          scheme: 'Spectral',
        },
        tooltip: {
          show: true,
          yHistogram: false,
        },
      },
    });
  }

  /**
   * Build final dashboard
   */
  build(): Dashboard {
    return this.dashboard;
  }
}

// ============================================================================
// Dashboard Templates
// ============================================================================

export class DashboardTemplates {
  /**
   * Create Overview Dashboard (12 panels)
   */
  static createOverviewDashboard(): Dashboard {
    const builder = new DashboardBuilder('AI-Shell Overview', ['overview']);

    // Add variables
    builder.addVariable({
      name: 'instance',
      type: 'query',
      datasource: 'AI-Shell-Prometheus',
      query: 'label_values(aishell_requests_total, instance)',
      refresh: 1,
      multi: false,
      includeAll: false,
    });

    // Row 1: Key Metrics (4 stat panels)
    builder.addStatPanel(
      'Total Requests',
      'sum(aishell_requests_total{instance=~"$instance"})',
      0, 0, 6, 4
    );

    builder.addStatPanel(
      'Active Sessions',
      'aishell_active_sessions{instance=~"$instance"}',
      6, 0, 6, 4
    );

    builder.addStatPanel(
      'Success Rate',
      '100 * sum(rate(aishell_requests_total{status="success",instance=~"$instance"}[5m])) / sum(rate(aishell_requests_total{instance=~"$instance"}[5m]))',
      12, 0, 6, 4
    );

    builder.addStatPanel(
      'Avg Response Time',
      'avg(rate(aishell_response_duration_seconds_sum{instance=~"$instance"}[5m]) / rate(aishell_response_duration_seconds_count{instance=~"$instance"}[5m])) * 1000',
      18, 0, 6, 4
    );

    // Row 2: Request Rate
    builder.addGraphPanel(
      'Request Rate',
      [
        {
          expr: 'sum(rate(aishell_requests_total{instance=~"$instance"}[5m])) by (type)',
          legendFormat: '{{type}}',
          refId: 'A',
        },
      ],
      0, 4, 12, 8
    );

    builder.addGraphPanel(
      'Error Rate',
      [
        {
          expr: 'sum(rate(aishell_requests_total{status="error",instance=~"$instance"}[5m])) by (error_type)',
          legendFormat: '{{error_type}}',
          refId: 'A',
        },
      ],
      12, 4, 12, 8
    );

    // Row 3: Performance
    builder.addGraphPanel(
      'Response Time (p95)',
      [
        {
          expr: 'histogram_quantile(0.95, sum(rate(aishell_response_duration_seconds_bucket{instance=~"$instance"}[5m])) by (le, endpoint))',
          legendFormat: '{{endpoint}}',
          refId: 'A',
        },
      ],
      0, 12, 12, 8
    );

    builder.addGraphPanel(
      'Memory Usage',
      [
        {
          expr: 'aishell_memory_usage_bytes{instance=~"$instance"} / 1024 / 1024',
          legendFormat: 'Memory (MB)',
          refId: 'A',
        },
      ],
      12, 12, 12, 8
    );

    // Row 4: Resource Utilization
    builder.addGaugePanel(
      'CPU Usage',
      'aishell_cpu_usage_percent{instance=~"$instance"}',
      0, 20, 6, 6
    );

    builder.addGaugePanel(
      'Memory Usage',
      '100 * aishell_memory_usage_bytes{instance=~"$instance"} / aishell_memory_total_bytes{instance=~"$instance"}',
      6, 20, 6, 6
    );

    builder.addStatPanel(
      'Cache Hit Rate',
      '100 * sum(rate(aishell_cache_hits_total{instance=~"$instance"}[5m])) / (sum(rate(aishell_cache_hits_total{instance=~"$instance"}[5m])) + sum(rate(aishell_cache_misses_total{instance=~"$instance"}[5m])))',
      12, 20, 6, 6
    );

    builder.addStatPanel(
      'Active Connections',
      'aishell_active_connections{instance=~"$instance"}',
      18, 20, 6, 6
    );

    return builder.build();
  }

  /**
   * Create Performance Dashboard (14 panels)
   */
  static createPerformanceDashboard(): Dashboard {
    const builder = new DashboardBuilder('AI-Shell Performance', ['performance']);

    // Add variables
    builder.addVariable({
      name: 'instance',
      type: 'query',
      datasource: 'AI-Shell-Prometheus',
      query: 'label_values(aishell_requests_total, instance)',
      refresh: 1,
      multi: false,
      includeAll: false,
    });

    builder.addVariable({
      name: 'endpoint',
      type: 'query',
      datasource: 'AI-Shell-Prometheus',
      query: 'label_values(aishell_response_duration_seconds_bucket, endpoint)',
      refresh: 1,
      multi: true,
      includeAll: true,
    });

    // Row 1: Response Time Percentiles
    builder.addGraphPanel(
      'Response Time Percentiles',
      [
        {
          expr: 'histogram_quantile(0.50, sum(rate(aishell_response_duration_seconds_bucket{instance=~"$instance",endpoint=~"$endpoint"}[5m])) by (le)) * 1000',
          legendFormat: 'p50',
          refId: 'A',
        },
        {
          expr: 'histogram_quantile(0.90, sum(rate(aishell_response_duration_seconds_bucket{instance=~"$instance",endpoint=~"$endpoint"}[5m])) by (le)) * 1000',
          legendFormat: 'p90',
          refId: 'B',
        },
        {
          expr: 'histogram_quantile(0.95, sum(rate(aishell_response_duration_seconds_bucket{instance=~"$instance",endpoint=~"$endpoint"}[5m])) by (le)) * 1000',
          legendFormat: 'p95',
          refId: 'C',
        },
        {
          expr: 'histogram_quantile(0.99, sum(rate(aishell_response_duration_seconds_bucket{instance=~"$instance",endpoint=~"$endpoint"}[5m])) by (le)) * 1000',
          legendFormat: 'p99',
          refId: 'D',
        },
      ],
      0, 0, 24, 8
    );

    // Row 2: Response Time Heatmap
    builder.addHeatmapPanel(
      'Response Time Distribution',
      'sum(rate(aishell_response_duration_seconds_bucket{instance=~"$instance",endpoint=~"$endpoint"}[5m])) by (le)',
      0, 8, 24, 8
    );

    // Row 3: Throughput
    builder.addGraphPanel(
      'Request Throughput',
      [
        {
          expr: 'sum(rate(aishell_requests_total{instance=~"$instance",endpoint=~"$endpoint"}[5m])) by (endpoint)',
          legendFormat: '{{endpoint}}',
          refId: 'A',
        },
      ],
      0, 16, 12, 8
    );

    builder.addGraphPanel(
      'Token Throughput',
      [
        {
          expr: 'sum(rate(aishell_tokens_processed_total{instance=~"$instance"}[5m])) by (type)',
          legendFormat: '{{type}} tokens/s',
          refId: 'A',
        },
      ],
      12, 16, 12, 8
    );

    // Row 4: Database Performance
    builder.addGraphPanel(
      'Database Query Duration',
      [
        {
          expr: 'histogram_quantile(0.95, sum(rate(aishell_db_query_duration_seconds_bucket{instance=~"$instance"}[5m])) by (le, operation))',
          legendFormat: '{{operation}}',
          refId: 'A',
        },
      ],
      0, 24, 12, 8
    );

    builder.addGraphPanel(
      'Database Pool Usage',
      [
        {
          expr: 'aishell_db_pool_active_connections{instance=~"$instance"}',
          legendFormat: 'Active',
          refId: 'A',
        },
        {
          expr: 'aishell_db_pool_idle_connections{instance=~"$instance"}',
          legendFormat: 'Idle',
          refId: 'B',
        },
      ],
      12, 24, 12, 8
    );

    // Row 5: Cache Performance
    builder.addGraphPanel(
      'Cache Hit/Miss Rate',
      [
        {
          expr: 'sum(rate(aishell_cache_hits_total{instance=~"$instance"}[5m]))',
          legendFormat: 'Hits',
          refId: 'A',
        },
        {
          expr: 'sum(rate(aishell_cache_misses_total{instance=~"$instance"}[5m]))',
          legendFormat: 'Misses',
          refId: 'B',
        },
      ],
      0, 32, 12, 8
    );

    builder.addStatPanel(
      'Cache Hit Ratio',
      '100 * sum(rate(aishell_cache_hits_total{instance=~"$instance"}[5m])) / (sum(rate(aishell_cache_hits_total{instance=~"$instance"}[5m])) + sum(rate(aishell_cache_misses_total{instance=~"$instance"}[5m])))',
      12, 32, 6, 8
    );

    builder.addStatPanel(
      'Cache Size',
      'aishell_cache_size_bytes{instance=~"$instance"} / 1024 / 1024',
      18, 32, 6, 8
    );

    // Row 6: Resource Usage
    builder.addGraphPanel(
      'CPU Usage Over Time',
      [
        {
          expr: 'aishell_cpu_usage_percent{instance=~"$instance"}',
          legendFormat: 'CPU %',
          refId: 'A',
        },
      ],
      0, 40, 8, 8
    );

    builder.addGraphPanel(
      'Memory Usage Over Time',
      [
        {
          expr: 'aishell_memory_usage_bytes{instance=~"$instance"} / 1024 / 1024',
          legendFormat: 'Memory (MB)',
          refId: 'A',
        },
      ],
      8, 40, 8, 8
    );

    builder.addGraphPanel(
      'Goroutine Count',
      [
        {
          expr: 'aishell_goroutines{instance=~"$instance"}',
          legendFormat: 'Goroutines',
          refId: 'A',
        },
      ],
      16, 40, 8, 8
    );

    // Row 7: Network I/O
    builder.addGraphPanel(
      'Network I/O',
      [
        {
          expr: 'rate(aishell_network_bytes_sent_total{instance=~"$instance"}[5m])',
          legendFormat: 'Sent',
          refId: 'A',
        },
        {
          expr: 'rate(aishell_network_bytes_received_total{instance=~"$instance"}[5m])',
          legendFormat: 'Received',
          refId: 'B',
        },
      ],
      0, 48, 12, 8
    );

    builder.addGraphPanel(
      'Connection Pool',
      [
        {
          expr: 'aishell_connection_pool_size{instance=~"$instance"}',
          legendFormat: 'Pool Size',
          refId: 'A',
        },
        {
          expr: 'aishell_active_connections{instance=~"$instance"}',
          legendFormat: 'Active',
          refId: 'B',
        },
      ],
      12, 48, 12, 8
    );

    return builder.build();
  }

  /**
   * Create Security Dashboard (10 panels)
   */
  static createSecurityDashboard(): Dashboard {
    const builder = new DashboardBuilder('AI-Shell Security', ['security']);

    // Add variables
    builder.addVariable({
      name: 'instance',
      type: 'query',
      datasource: 'AI-Shell-Prometheus',
      query: 'label_values(aishell_requests_total, instance)',
      refresh: 1,
      multi: false,
      includeAll: false,
    });

    // Row 1: Security Overview
    builder.addStatPanel(
      'Failed Auth Attempts',
      'sum(increase(aishell_auth_failures_total{instance=~"$instance"}[1h]))',
      0, 0, 6, 4
    );

    builder.addStatPanel(
      'Blocked IPs',
      'aishell_blocked_ips_total{instance=~"$instance"}',
      6, 0, 6, 4
    );

    builder.addStatPanel(
      'Active Sessions',
      'aishell_active_sessions{instance=~"$instance"}',
      12, 0, 6, 4
    );

    builder.addStatPanel(
      'Security Alerts',
      'sum(increase(aishell_security_alerts_total{instance=~"$instance"}[1h]))',
      18, 0, 6, 4
    );

    // Row 2: Authentication Events
    builder.addGraphPanel(
      'Authentication Events',
      [
        {
          expr: 'sum(rate(aishell_auth_attempts_total{instance=~"$instance"}[5m])) by (result)',
          legendFormat: '{{result}}',
          refId: 'A',
        },
      ],
      0, 4, 12, 8
    );

    builder.addGraphPanel(
      'Failed Login Attempts by IP',
      [
        {
          expr: 'topk(10, sum(rate(aishell_auth_failures_total{instance=~"$instance"}[5m])) by (ip))',
          legendFormat: '{{ip}}',
          refId: 'A',
        },
      ],
      12, 4, 12, 8
    );

    // Row 3: Security Threats
    builder.addGraphPanel(
      'Rate Limiting Events',
      [
        {
          expr: 'sum(rate(aishell_rate_limit_exceeded_total{instance=~"$instance"}[5m])) by (endpoint)',
          legendFormat: '{{endpoint}}',
          refId: 'A',
        },
      ],
      0, 12, 12, 8
    );

    builder.addGraphPanel(
      'Suspicious Activity',
      [
        {
          expr: 'sum(rate(aishell_suspicious_activity_total{instance=~"$instance"}[5m])) by (type)',
          legendFormat: '{{type}}',
          refId: 'A',
        },
      ],
      12, 12, 12, 8
    );

    // Row 4: Access Patterns
    builder.addTablePanel(
      'Top Failed Auth IPs',
      [
        {
          expr: 'topk(20, sum by (ip, user) (increase(aishell_auth_failures_total{instance=~"$instance"}[1h])))',
          refId: 'A',
        },
      ],
      0, 20, 12, 8
    );

    builder.addTablePanel(
      'Recent Security Events',
      [
        {
          expr: 'topk(20, aishell_security_alerts_total{instance=~"$instance"})',
          refId: 'A',
        },
      ],
      12, 20, 12, 8
    );

    return builder.build();
  }

  /**
   * Create Query Analytics Dashboard (14 panels)
   */
  static createQueryAnalyticsDashboard(): Dashboard {
    const builder = new DashboardBuilder('AI-Shell Query Analytics', ['queries', 'analytics']);

    // Add variables
    builder.addVariable({
      name: 'instance',
      type: 'query',
      datasource: 'AI-Shell-Prometheus',
      query: 'label_values(aishell_requests_total, instance)',
      refresh: 1,
      multi: false,
      includeAll: false,
    });

    builder.addVariable({
      name: 'model',
      type: 'query',
      datasource: 'AI-Shell-Prometheus',
      query: 'label_values(aishell_query_duration_seconds, model)',
      refresh: 1,
      multi: true,
      includeAll: true,
    });

    // Row 1: Query Volume
    builder.addStatPanel(
      'Total Queries',
      'sum(aishell_queries_total{instance=~"$instance",model=~"$model"})',
      0, 0, 6, 4
    );

    builder.addStatPanel(
      'Queries/Min',
      'sum(rate(aishell_queries_total{instance=~"$instance",model=~"$model"}[5m])) * 60',
      6, 0, 6, 4
    );

    builder.addStatPanel(
      'Avg Query Time',
      'avg(rate(aishell_query_duration_seconds_sum{instance=~"$instance",model=~"$model"}[5m]) / rate(aishell_query_duration_seconds_count{instance=~"$instance",model=~"$model"}[5m])) * 1000',
      12, 0, 6, 4
    );

    builder.addStatPanel(
      'Total Tokens',
      'sum(aishell_tokens_processed_total{instance=~"$instance",model=~"$model"})',
      18, 0, 6, 4
    );

    // Row 2: Query Rate by Model
    builder.addGraphPanel(
      'Query Rate by Model',
      [
        {
          expr: 'sum(rate(aishell_queries_total{instance=~"$instance",model=~"$model"}[5m])) by (model)',
          legendFormat: '{{model}}',
          refId: 'A',
        },
      ],
      0, 4, 24, 8
    );

    // Row 3: Query Duration
    builder.addGraphPanel(
      'Query Duration Percentiles',
      [
        {
          expr: 'histogram_quantile(0.50, sum(rate(aishell_query_duration_seconds_bucket{instance=~"$instance",model=~"$model"}[5m])) by (le, model)) * 1000',
          legendFormat: 'p50 - {{model}}',
          refId: 'A',
        },
        {
          expr: 'histogram_quantile(0.95, sum(rate(aishell_query_duration_seconds_bucket{instance=~"$instance",model=~"$model"}[5m])) by (le, model)) * 1000',
          legendFormat: 'p95 - {{model}}',
          refId: 'B',
        },
        {
          expr: 'histogram_quantile(0.99, sum(rate(aishell_query_duration_seconds_bucket{instance=~"$instance",model=~"$model"}[5m])) by (le, model)) * 1000',
          legendFormat: 'p99 - {{model}}',
          refId: 'C',
        },
      ],
      0, 12, 24, 8
    );

    // Row 4: Token Usage
    builder.addGraphPanel(
      'Token Usage by Type',
      [
        {
          expr: 'sum(rate(aishell_tokens_processed_total{instance=~"$instance",model=~"$model"}[5m])) by (type)',
          legendFormat: '{{type}}',
          refId: 'A',
        },
      ],
      0, 20, 12, 8
    );

    builder.addGraphPanel(
      'Tokens per Query',
      [
        {
          expr: 'sum(rate(aishell_tokens_processed_total{instance=~"$instance",model=~"$model"}[5m])) by (model) / sum(rate(aishell_queries_total{instance=~"$instance",model=~"$model"}[5m])) by (model)',
          legendFormat: '{{model}}',
          refId: 'A',
        },
      ],
      12, 20, 12, 8
    );

    // Row 5: Query Success Rate
    builder.addGraphPanel(
      'Query Success Rate',
      [
        {
          expr: '100 * sum(rate(aishell_queries_total{status="success",instance=~"$instance",model=~"$model"}[5m])) by (model) / sum(rate(aishell_queries_total{instance=~"$instance",model=~"$model"}[5m])) by (model)',
          legendFormat: '{{model}}',
          refId: 'A',
        },
      ],
      0, 28, 12, 8
    );

    builder.addGraphPanel(
      'Query Errors by Type',
      [
        {
          expr: 'sum(rate(aishell_queries_total{status="error",instance=~"$instance",model=~"$model"}[5m])) by (error_type)',
          legendFormat: '{{error_type}}',
          refId: 'A',
        },
      ],
      12, 28, 12, 8
    );

    // Row 6: Context Window Usage
    builder.addGraphPanel(
      'Context Window Utilization',
      [
        {
          expr: '100 * aishell_context_tokens_used{instance=~"$instance",model=~"$model"} / aishell_context_tokens_limit{instance=~"$instance",model=~"$model"}',
          legendFormat: '{{model}}',
          refId: 'A',
        },
      ],
      0, 36, 12, 8
    );

    builder.addStatPanel(
      'Avg Context Utilization',
      '100 * avg(aishell_context_tokens_used{instance=~"$instance",model=~"$model"} / aishell_context_tokens_limit{instance=~"$instance",model=~"$model"})',
      12, 36, 12, 8
    );

    // Row 7: Top Queries
    builder.addTablePanel(
      'Slowest Queries',
      [
        {
          expr: 'topk(20, avg_over_time(aishell_query_duration_seconds{instance=~"$instance",model=~"$model"}[5m]))',
          refId: 'A',
        },
      ],
      0, 44, 12, 8
    );

    builder.addTablePanel(
      'Most Frequent Query Patterns',
      [
        {
          expr: 'topk(20, sum by (pattern) (rate(aishell_query_patterns_total{instance=~"$instance"}[5m])))',
          refId: 'A',
        },
      ],
      12, 44, 12, 8
    );

    return builder.build();
  }
}

// ============================================================================
// CLI Implementation
// ============================================================================

export class GrafanaIntegrationCLI {
  private configPath: string;
  private client?: GrafanaClient;

  constructor() {
    this.configPath = path.join(process.env.HOME || '/tmp', '.aishell-grafana.json');
  }

  /**
   * Load configuration
   */
  async loadConfig(): Promise<GrafanaConfig | null> {
    try {
      const data = await fs.readFile(this.configPath, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      return null;
    }
  }

  /**
   * Save configuration
   */
  async saveConfig(config: GrafanaConfig): Promise<void> {
    await fs.writeFile(this.configPath, JSON.stringify(config, null, 2));
  }

  /**
   * Get initialized client
   */
  async getClient(): Promise<GrafanaClient> {
    if (this.client) return this.client;

    const config = await this.loadConfig();
    if (!config) {
      throw new Error('Grafana not configured. Run: grafana setup --url <url> --api-key <key>');
    }

    this.client = new GrafanaClient(config);
    return this.client;
  }

  /**
   * Setup Grafana connection
   */
  async setup(url: string, apiKey: string, prometheusUrl?: string): Promise<void> {
    console.log('Configuring Grafana connection...');

    const config: GrafanaConfig = { url, apiKey };
    const client = new GrafanaClient(config);

    // Test connection
    const connected = await client.testConnection();
    if (!connected) {
      throw new Error('Failed to connect to Grafana. Check URL and API key.');
    }

    console.log('✓ Connected to Grafana');

    // Setup Prometheus data source if URL provided
    if (prometheusUrl) {
      console.log('Setting up Prometheus data source...');
      await client.setupDataSource(prometheusUrl);
      console.log('✓ Prometheus data source configured');
    }

    await this.saveConfig(config);
    console.log('✓ Configuration saved');
  }

  /**
   * Deploy all dashboards
   */
  async deployDashboards(): Promise<void> {
    const client = await this.getClient();
    console.log('Deploying AI-Shell dashboards...');

    const dashboards = [
      { name: 'Overview', dashboard: DashboardTemplates.createOverviewDashboard() },
      { name: 'Performance', dashboard: DashboardTemplates.createPerformanceDashboard() },
      { name: 'Security', dashboard: DashboardTemplates.createSecurityDashboard() },
      { name: 'Query Analytics', dashboard: DashboardTemplates.createQueryAnalyticsDashboard() },
    ];

    for (const { name, dashboard } of dashboards) {
      try {
        await client.saveDashboard(dashboard);
        console.log(`✓ Deployed ${name} dashboard`);
      } catch (error) {
        console.error(`✗ Failed to deploy ${name} dashboard:`, error);
      }
    }

    console.log('✓ All dashboards deployed');
  }

  /**
   * Create specific dashboard
   */
  async createDashboard(type: string): Promise<void> {
    const client = await this.getClient();

    let dashboard: Dashboard;
    switch (type) {
      case 'overview':
        dashboard = DashboardTemplates.createOverviewDashboard();
        break;
      case 'performance':
        dashboard = DashboardTemplates.createPerformanceDashboard();
        break;
      case 'security':
        dashboard = DashboardTemplates.createSecurityDashboard();
        break;
      case 'query-analytics':
        dashboard = DashboardTemplates.createQueryAnalyticsDashboard();
        break;
      default:
        throw new Error(`Unknown dashboard type: ${type}`);
    }

    const result = await client.saveDashboard(dashboard);
    console.log(`✓ Created ${type} dashboard`);
    console.log(`Dashboard URL: ${(await this.loadConfig())?.url}/d/${result.dashboard.uid}`);
  }

  /**
   * Export dashboard
   */
  async exportDashboard(uid: string, outputPath: string): Promise<void> {
    const client = await this.getClient();

    console.log(`Exporting dashboard ${uid}...`);
    const result = await client.getDashboard(uid);

    await fs.writeFile(outputPath, JSON.stringify(result.dashboard, null, 2));
    console.log(`✓ Dashboard exported to ${outputPath}`);
  }

  /**
   * Import dashboard
   */
  async importDashboard(filePath: string): Promise<void> {
    const client = await this.getClient();

    console.log(`Importing dashboard from ${filePath}...`);
    const data = await fs.readFile(filePath, 'utf-8');
    const dashboard: Dashboard = JSON.parse(data);

    const result = await client.saveDashboard(dashboard);
    console.log(`✓ Dashboard imported`);
    console.log(`Dashboard URL: ${(await this.loadConfig())?.url}/d/${result.dashboard.uid}`);
  }

  /**
   * List dashboards
   */
  async listDashboards(): Promise<void> {
    const client = await this.getClient();

    console.log('AI-Shell Dashboards:');
    const dashboards = await client.searchDashboards('ai-shell');

    for (const dashboard of dashboards) {
      console.log(`  - ${dashboard.title} (UID: ${dashboard.uid})`);
      console.log(`    URL: ${(await this.loadConfig())?.url}${dashboard.url}`);
    }
  }
}

// ============================================================================
// CLI Entry Point
// ============================================================================

export function createCLI(): Command {
  const program = new Command();
  const cli = new GrafanaIntegrationCLI();

  program
    .name('aishell-grafana')
    .description('Grafana integration for AI-Shell')
    .version('1.0.0');

  program
    .command('setup')
    .description('Configure Grafana connection')
    .requiredOption('--url <url>', 'Grafana URL')
    .requiredOption('--api-key <key>', 'Grafana API key')
    .option('--prometheus-url <url>', 'Prometheus URL')
    .action(async (options) => {
      await cli.setup(options.url, options.apiKey, options.prometheusUrl);
    });

  program
    .command('deploy-dashboards')
    .description('Deploy all AI-Shell dashboards')
    .action(async () => {
      await cli.deployDashboards();
    });

  program
    .command('create-dashboard')
    .description('Create specific dashboard')
    .argument('<type>', 'Dashboard type (overview, performance, security, query-analytics)')
    .action(async (type) => {
      await cli.createDashboard(type);
    });

  program
    .command('export')
    .description('Export dashboard to JSON')
    .argument('<uid>', 'Dashboard UID')
    .option('--output <path>', 'Output file path', './dashboard.json')
    .action(async (uid, options) => {
      await cli.exportDashboard(uid, options.output);
    });

  program
    .command('import')
    .description('Import dashboard from JSON')
    .argument('<file>', 'Dashboard JSON file')
    .action(async (file) => {
      await cli.importDashboard(file);
    });

  program
    .command('list')
    .description('List all AI-Shell dashboards')
    .action(async () => {
      await cli.listDashboards();
    });

  return program;
}

// Run CLI if executed directly
if (require.main === module) {
  createCLI().parse(process.argv);
}
