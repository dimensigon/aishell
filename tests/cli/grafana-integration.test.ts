/**
 * Comprehensive tests for Grafana Integration
 *
 * Tests cover:
 * - API client functionality
 * - Dashboard builder
 * - Template generation
 * - CLI operations
 * - Error handling
 * - Edge cases
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import * as fs from 'fs/promises';
import {
  GrafanaClient,
  DashboardBuilder,
  DashboardTemplates,
  GrafanaIntegrationCLI,
} from '../../src/cli/grafana-integration';

// Mock axios
vi.mock('axios');
const mockedAxios = axios as any;

// Mock fs
vi.mock('fs/promises');
const mockedFs = fs as any;

describe('GrafanaClient', () => {
  let client: GrafanaClient;

  beforeEach(() => {
    client = new GrafanaClient({
      url: 'http://localhost:3000',
      apiKey: 'test-api-key',
    });

    mockedAxios.create.mockReturnValue({
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn(),
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('testConnection', () => {
    it('should return true when connection is successful', async () => {
      const mockClient = {
        get: vi.fn().mockResolvedValue({ status: 200 }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      const result = await client.testConnection();

      expect(result).toBe(true);
      expect(mockClient.get).toHaveBeenCalledWith('/api/health');
    });

    it('should return false when connection fails', async () => {
      const mockClient = {
        get: vi.fn().mockRejectedValue(new Error('Connection failed')),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      const result = await client.testConnection();

      expect(result).toBe(false);
    });

    it('should handle timeout errors', async () => {
      const mockClient = {
        get: vi.fn().mockRejectedValue({ code: 'ETIMEDOUT' }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
        timeout: 5000,
      });

      const result = await client.testConnection();

      expect(result).toBe(false);
    });
  });

  describe('setupDataSource', () => {
    it('should return existing data source if found', async () => {
      const existingDataSource = {
        id: 1,
        uid: 'test-uid',
        name: 'AI-Shell-Prometheus',
        type: 'prometheus',
      };

      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: existingDataSource }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      const result = await client.setupDataSource('http://localhost:9090');

      expect(result).toEqual(existingDataSource);
      expect(mockClient.get).toHaveBeenCalledWith('/api/datasources/name/AI-Shell-Prometheus');
    });

    it('should create new data source if not found', async () => {
      const newDataSource = {
        id: 2,
        uid: 'new-uid',
        name: 'AI-Shell-Prometheus',
        type: 'prometheus',
      };

      const mockClient = {
        get: vi.fn().mockRejectedValue({ response: { status: 404 } }),
        post: vi.fn().mockResolvedValue({ data: newDataSource }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      const result = await client.setupDataSource('http://localhost:9090');

      expect(result).toEqual(newDataSource);
      expect(mockClient.post).toHaveBeenCalledWith(
        '/api/datasources',
        expect.objectContaining({
          name: 'AI-Shell-Prometheus',
          type: 'prometheus',
          url: 'http://localhost:9090',
        })
      );
    });

    it('should throw error on other failures', async () => {
      const mockClient = {
        get: vi.fn().mockRejectedValue({ response: { status: 500 } }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      await expect(client.setupDataSource('http://localhost:9090')).rejects.toThrow();
    });
  });

  describe('saveDashboard', () => {
    it('should save dashboard successfully', async () => {
      const dashboard = {
        title: 'Test Dashboard',
        tags: ['test'],
        panels: [],
        templating: { list: [] },
        time: { from: 'now-6h', to: 'now' },
        refresh: '30s',
        timezone: 'browser',
        schemaVersion: 27,
        version: 1,
      };

      const response = {
        dashboard: { ...dashboard, uid: 'test-uid' },
        meta: { type: 'db', canSave: true, canEdit: true, canDelete: true },
      };

      const mockClient = {
        post: vi.fn().mockResolvedValue({ data: response }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      const result = await client.saveDashboard(dashboard);

      expect(result).toEqual(response);
      expect(mockClient.post).toHaveBeenCalledWith('/api/dashboards/db', {
        dashboard,
        folderId: 0,
        overwrite: true,
      });
    });

    it('should save dashboard to specific folder', async () => {
      const dashboard = {
        title: 'Test Dashboard',
        tags: ['test'],
        panels: [],
        templating: { list: [] },
        time: { from: 'now-6h', to: 'now' },
        refresh: '30s',
        timezone: 'browser',
        schemaVersion: 27,
        version: 1,
      };

      const mockClient = {
        post: vi.fn().mockResolvedValue({ data: {} }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      await client.saveDashboard(dashboard, 5);

      expect(mockClient.post).toHaveBeenCalledWith('/api/dashboards/db', {
        dashboard,
        folderId: 5,
        overwrite: true,
      });
    });
  });

  describe('getDashboard', () => {
    it('should retrieve dashboard by UID', async () => {
      const dashboardResponse = {
        dashboard: {
          uid: 'test-uid',
          title: 'Test Dashboard',
        },
        meta: {},
      };

      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: dashboardResponse }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      const result = await client.getDashboard('test-uid');

      expect(result).toEqual(dashboardResponse);
      expect(mockClient.get).toHaveBeenCalledWith('/api/dashboards/uid/test-uid');
    });

    it('should handle dashboard not found', async () => {
      const mockClient = {
        get: vi.fn().mockRejectedValue({ response: { status: 404 } }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      await expect(client.getDashboard('nonexistent')).rejects.toThrow();
    });
  });

  describe('deleteDashboard', () => {
    it('should delete dashboard successfully', async () => {
      const mockClient = {
        delete: vi.fn().mockResolvedValue({ status: 200 }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      await client.deleteDashboard('test-uid');

      expect(mockClient.delete).toHaveBeenCalledWith('/api/dashboards/uid/test-uid');
    });
  });

  describe('searchDashboards', () => {
    it('should search dashboards with tag', async () => {
      const dashboards = [
        { uid: 'uid1', title: 'Dashboard 1' },
        { uid: 'uid2', title: 'Dashboard 2' },
      ];

      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: dashboards }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      const result = await client.searchDashboards('ai-shell');

      expect(result).toEqual(dashboards);
      expect(mockClient.get).toHaveBeenCalledWith('/api/search', {
        params: { type: 'dash-db', tag: 'ai-shell' },
      });
    });

    it('should search all dashboards without tag', async () => {
      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: [] }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      const client = new GrafanaClient({
        url: 'http://localhost:3000',
        apiKey: 'test-api-key',
      });

      await client.searchDashboards();

      expect(mockClient.get).toHaveBeenCalledWith('/api/search', {
        params: { type: 'dash-db' },
      });
    });
  });
});

describe('DashboardBuilder', () => {
  it('should create basic dashboard', () => {
    const builder = new DashboardBuilder('Test Dashboard', ['test', 'example']);
    const dashboard = builder.build();

    expect(dashboard.title).toBe('Test Dashboard');
    expect(dashboard.tags).toContain('ai-shell');
    expect(dashboard.tags).toContain('test');
    expect(dashboard.tags).toContain('example');
    expect(dashboard.panels).toHaveLength(0);
  });

  it('should add variable to dashboard', () => {
    const builder = new DashboardBuilder('Test Dashboard');
    builder.addVariable({
      name: 'instance',
      type: 'query',
      datasource: 'Prometheus',
      query: 'label_values(metric, instance)',
      refresh: 1,
      multi: false,
      includeAll: false,
    });

    const dashboard = builder.build();

    expect(dashboard.templating.list).toHaveLength(1);
    expect(dashboard.templating.list[0].name).toBe('instance');
  });

  it('should add graph panel with correct structure', () => {
    const builder = new DashboardBuilder('Test Dashboard');
    builder.addGraphPanel(
      'Test Graph',
      [
        {
          expr: 'up',
          legendFormat: 'Instance {{instance}}',
          refId: 'A',
        },
      ],
      0,
      0,
      12,
      8
    );

    const dashboard = builder.build();

    expect(dashboard.panels).toHaveLength(1);
    expect(dashboard.panels[0].title).toBe('Test Graph');
    expect(dashboard.panels[0].type).toBe('timeseries');
    expect(dashboard.panels[0].gridPos).toEqual({ x: 0, y: 0, w: 12, h: 8 });
    expect(dashboard.panels[0].targets).toHaveLength(1);
  });

  it('should add stat panel with thresholds', () => {
    const builder = new DashboardBuilder('Test Dashboard');
    builder.addStatPanel('Test Stat', 'metric_total', 0, 0, 6, 4);

    const dashboard = builder.build();

    expect(dashboard.panels).toHaveLength(1);
    expect(dashboard.panels[0].type).toBe('stat');
    expect(dashboard.panels[0].fieldConfig?.defaults?.thresholds).toBeDefined();
  });

  it('should add gauge panel with min/max', () => {
    const builder = new DashboardBuilder('Test Dashboard');
    builder.addGaugePanel('Test Gauge', 'cpu_usage', 0, 0, 6, 6);

    const dashboard = builder.build();

    expect(dashboard.panels).toHaveLength(1);
    expect(dashboard.panels[0].type).toBe('gauge');
    expect(dashboard.panels[0].fieldConfig?.defaults?.min).toBe(0);
    expect(dashboard.panels[0].fieldConfig?.defaults?.max).toBe(100);
  });

  it('should add table panel', () => {
    const builder = new DashboardBuilder('Test Dashboard');
    builder.addTablePanel(
      'Test Table',
      [{ expr: 'metric', refId: 'A' }],
      0,
      0,
      12,
      8
    );

    const dashboard = builder.build();

    expect(dashboard.panels).toHaveLength(1);
    expect(dashboard.panels[0].type).toBe('table');
  });

  it('should add heatmap panel', () => {
    const builder = new DashboardBuilder('Test Dashboard');
    builder.addHeatmapPanel('Test Heatmap', 'histogram_metric', 0, 0, 12, 8);

    const dashboard = builder.build();

    expect(dashboard.panels).toHaveLength(1);
    expect(dashboard.panels[0].type).toBe('heatmap');
  });

  it('should auto-increment panel IDs', () => {
    const builder = new DashboardBuilder('Test Dashboard');
    builder.addStatPanel('Panel 1', 'metric1', 0, 0);
    builder.addStatPanel('Panel 2', 'metric2', 6, 0);
    builder.addStatPanel('Panel 3', 'metric3', 12, 0);

    const dashboard = builder.build();

    expect(dashboard.panels[0].id).toBe(1);
    expect(dashboard.panels[1].id).toBe(2);
    expect(dashboard.panels[2].id).toBe(3);
  });

  it('should support method chaining', () => {
    const builder = new DashboardBuilder('Test Dashboard');

    const dashboard = builder
      .addVariable({
        name: 'var1',
        type: 'query',
        datasource: 'Prometheus',
        query: 'query1',
        refresh: 1,
        multi: false,
        includeAll: false,
      })
      .addStatPanel('Panel 1', 'metric1', 0, 0)
      .addGraphPanel('Panel 2', [{ expr: 'metric2', refId: 'A' }], 0, 4)
      .build();

    expect(dashboard.templating.list).toHaveLength(1);
    expect(dashboard.panels).toHaveLength(2);
  });
});

describe('DashboardTemplates', () => {
  describe('createOverviewDashboard', () => {
    it('should create overview dashboard with 12 panels', () => {
      const dashboard = DashboardTemplates.createOverviewDashboard();

      expect(dashboard.title).toBe('AI-Shell Overview');
      expect(dashboard.tags).toContain('overview');
      expect(dashboard.panels).toHaveLength(12);
    });

    it('should include instance variable', () => {
      const dashboard = DashboardTemplates.createOverviewDashboard();

      expect(dashboard.templating.list).toHaveLength(1);
      expect(dashboard.templating.list[0].name).toBe('instance');
    });

    it('should include key metric panels', () => {
      const dashboard = DashboardTemplates.createOverviewDashboard();

      const titles = dashboard.panels.map((p) => p.title);
      expect(titles).toContain('Total Requests');
      expect(titles).toContain('Active Sessions');
      expect(titles).toContain('Success Rate');
      expect(titles).toContain('Avg Response Time');
    });
  });

  describe('createPerformanceDashboard', () => {
    it('should create performance dashboard with 15 panels', () => {
      const dashboard = DashboardTemplates.createPerformanceDashboard();

      expect(dashboard.title).toBe('AI-Shell Performance');
      expect(dashboard.tags).toContain('performance');
      expect(dashboard.panels).toHaveLength(15);
    });

    it('should include instance and endpoint variables', () => {
      const dashboard = DashboardTemplates.createPerformanceDashboard();

      expect(dashboard.templating.list).toHaveLength(2);
      expect(dashboard.templating.list[0].name).toBe('instance');
      expect(dashboard.templating.list[1].name).toBe('endpoint');
    });

    it('should include response time percentiles', () => {
      const dashboard = DashboardTemplates.createPerformanceDashboard();

      const panel = dashboard.panels.find(
        (p) => p.title === 'Response Time Percentiles'
      );
      expect(panel).toBeDefined();
      expect(panel?.targets).toHaveLength(4); // p50, p90, p95, p99
    });

    it('should include heatmap panel', () => {
      const dashboard = DashboardTemplates.createPerformanceDashboard();

      const heatmap = dashboard.panels.find((p) => p.type === 'heatmap');
      expect(heatmap).toBeDefined();
      expect(heatmap?.title).toBe('Response Time Distribution');
    });
  });

  describe('createSecurityDashboard', () => {
    it('should create security dashboard with 10 panels', () => {
      const dashboard = DashboardTemplates.createSecurityDashboard();

      expect(dashboard.title).toBe('AI-Shell Security');
      expect(dashboard.tags).toContain('security');
      expect(dashboard.panels).toHaveLength(10);
    });

    it('should include security metrics', () => {
      const dashboard = DashboardTemplates.createSecurityDashboard();

      const titles = dashboard.panels.map((p) => p.title);
      expect(titles).toContain('Failed Auth Attempts');
      expect(titles).toContain('Blocked IPs');
      expect(titles).toContain('Security Alerts');
    });

    it('should include table panels for top threats', () => {
      const dashboard = DashboardTemplates.createSecurityDashboard();

      const tables = dashboard.panels.filter((p) => p.type === 'table');
      expect(tables.length).toBeGreaterThan(0);
    });
  });

  describe('createQueryAnalyticsDashboard', () => {
    it('should create query analytics dashboard with 14 panels', () => {
      const dashboard = DashboardTemplates.createQueryAnalyticsDashboard();

      expect(dashboard.title).toBe('AI-Shell Query Analytics');
      expect(dashboard.tags).toContain('queries');
      expect(dashboard.tags).toContain('analytics');
      expect(dashboard.panels).toHaveLength(14);
    });

    it('should include instance and model variables', () => {
      const dashboard = DashboardTemplates.createQueryAnalyticsDashboard();

      expect(dashboard.templating.list).toHaveLength(2);
      expect(dashboard.templating.list[0].name).toBe('instance');
      expect(dashboard.templating.list[1].name).toBe('model');
      expect(dashboard.templating.list[1].multi).toBe(true);
    });

    it('should include token usage panels', () => {
      const dashboard = DashboardTemplates.createQueryAnalyticsDashboard();

      const titles = dashboard.panels.map((p) => p.title);
      expect(titles).toContain('Token Usage by Type');
      expect(titles).toContain('Tokens per Query');
    });

    it('should include query performance panels', () => {
      const dashboard = DashboardTemplates.createQueryAnalyticsDashboard();

      const titles = dashboard.panels.map((p) => p.title);
      expect(titles).toContain('Query Duration Percentiles');
      expect(titles).toContain('Query Success Rate');
    });
  });
});

describe('GrafanaIntegrationCLI', () => {
  let cli: GrafanaIntegrationCLI;

  beforeEach(() => {
    cli = new GrafanaIntegrationCLI();
    mockedFs.readFile = vi.fn();
    mockedFs.writeFile = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('loadConfig', () => {
    it('should load existing configuration', async () => {
      const config = {
        url: 'http://localhost:3000',
        apiKey: 'test-key',
      };

      mockedFs.readFile.mockResolvedValue(JSON.stringify(config));

      const result = await cli.loadConfig();

      expect(result).toEqual(config);
    });

    it('should return null if config does not exist', async () => {
      mockedFs.readFile.mockRejectedValue({ code: 'ENOENT' });

      const result = await cli.loadConfig();

      expect(result).toBeNull();
    });
  });

  describe('saveConfig', () => {
    it('should save configuration to file', async () => {
      const config = {
        url: 'http://localhost:3000',
        apiKey: 'test-key',
      };

      mockedFs.writeFile.mockResolvedValue(undefined);

      await cli.saveConfig(config);

      expect(mockedFs.writeFile).toHaveBeenCalledWith(
        expect.stringContaining('.aishell-grafana.json'),
        JSON.stringify(config, null, 2)
      );
    });
  });

  describe('setup', () => {
    it('should configure Grafana connection', async () => {
      const mockClient = {
        get: vi.fn().mockResolvedValue({ status: 200 }),
      };
      mockedAxios.create.mockReturnValue(mockClient);
      mockedFs.writeFile.mockResolvedValue(undefined);

      await cli.setup('http://localhost:3000', 'test-key');

      expect(mockClient.get).toHaveBeenCalledWith('/api/health');
      expect(mockedFs.writeFile).toHaveBeenCalled();
    });

    it('should setup Prometheus data source when URL provided', async () => {
      const mockClient = {
        get: vi.fn()
          .mockResolvedValueOnce({ status: 200 }) // health check
          .mockRejectedValueOnce({ response: { status: 404 } }), // data source not found
        post: vi.fn().mockResolvedValue({ data: { id: 1 } }),
      };
      mockedAxios.create.mockReturnValue(mockClient);
      mockedFs.writeFile.mockResolvedValue(undefined);

      await cli.setup('http://localhost:3000', 'test-key', 'http://localhost:9090');

      expect(mockClient.post).toHaveBeenCalledWith(
        '/api/datasources',
        expect.objectContaining({
          type: 'prometheus',
          url: 'http://localhost:9090',
        })
      );
    });

    it('should throw error if connection fails', async () => {
      const mockClient = {
        get: vi.fn().mockRejectedValue(new Error('Connection failed')),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      await expect(
        cli.setup('http://localhost:3000', 'test-key')
      ).rejects.toThrow();
    });
  });

  describe('exportDashboard', () => {
    it('should export dashboard to file', async () => {
      const dashboard = {
        uid: 'test-uid',
        title: 'Test Dashboard',
        panels: [],
      };

      mockedFs.readFile.mockResolvedValue(
        JSON.stringify({ url: 'http://localhost:3000', apiKey: 'test-key' })
      );
      mockedFs.writeFile.mockResolvedValue(undefined);

      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: { dashboard } }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      await cli.exportDashboard('test-uid', '/tmp/dashboard.json');

      expect(mockClient.get).toHaveBeenCalledWith('/api/dashboards/uid/test-uid');
      expect(mockedFs.writeFile).toHaveBeenCalledWith(
        '/tmp/dashboard.json',
        JSON.stringify(dashboard, null, 2)
      );
    });
  });

  describe('importDashboard', () => {
    it('should import dashboard from file', async () => {
      const dashboard = {
        title: 'Imported Dashboard',
        panels: [],
        tags: [],
        templating: { list: [] },
        time: { from: 'now-6h', to: 'now' },
        refresh: '30s',
        timezone: 'browser',
        schemaVersion: 27,
        version: 1,
      };

      mockedFs.readFile
        .mockResolvedValueOnce(JSON.stringify(dashboard))
        .mockResolvedValueOnce(
          JSON.stringify({ url: 'http://localhost:3000', apiKey: 'test-key' })
        );

      const mockClient = {
        post: vi.fn().mockResolvedValue({
          data: { dashboard: { ...dashboard, uid: 'new-uid' } },
        }),
      };
      mockedAxios.create.mockReturnValue(mockClient);

      await cli.importDashboard('/tmp/dashboard.json');

      expect(mockClient.post).toHaveBeenCalledWith('/api/dashboards/db', {
        dashboard,
        folderId: 0,
        overwrite: true,
      });
    });
  });
});

describe('Integration Tests', () => {
  it('should create complete dashboard pipeline', () => {
    // Build dashboard
    const builder = new DashboardBuilder('Integration Test');
    builder
      .addVariable({
        name: 'instance',
        type: 'query',
        datasource: 'Prometheus',
        query: 'label_values(up, instance)',
        refresh: 1,
        multi: false,
        includeAll: false,
      })
      .addStatPanel('Uptime', 'up', 0, 0)
      .addGraphPanel('Request Rate', [{ expr: 'rate(requests[5m])', refId: 'A' }], 0, 4);

    const dashboard = builder.build();

    // Validate structure
    expect(dashboard.title).toBe('Integration Test');
    expect(dashboard.templating.list).toHaveLength(1);
    expect(dashboard.panels).toHaveLength(2);

    // Validate panel IDs are sequential
    expect(dashboard.panels[0].id).toBe(1);
    expect(dashboard.panels[1].id).toBe(2);

    // Validate panel positions don't overlap
    const panel1 = dashboard.panels[0];
    const panel2 = dashboard.panels[1];
    expect(panel1.gridPos.y + panel1.gridPos.h).toBeLessThanOrEqual(panel2.gridPos.y);
  });

  it('should generate all dashboard templates without errors', () => {
    const dashboards = [
      DashboardTemplates.createOverviewDashboard(),
      DashboardTemplates.createPerformanceDashboard(),
      DashboardTemplates.createSecurityDashboard(),
      DashboardTemplates.createQueryAnalyticsDashboard(),
    ];

    dashboards.forEach((dashboard) => {
      expect(dashboard.title).toBeTruthy();
      expect(dashboard.panels.length).toBeGreaterThan(0);
      expect(dashboard.tags).toContain('ai-shell');

      // Validate all panels have unique IDs
      const ids = dashboard.panels.map((p) => p.id);
      const uniqueIds = new Set(ids);
      expect(uniqueIds.size).toBe(ids.length);
    });
  });
});
