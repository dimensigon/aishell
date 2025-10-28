/**
 * Tests for Prometheus Integration
 * Comprehensive test suite for metrics collection, export, and server functionality
 */

import { PrometheusIntegration, PrometheusServer, PrometheusMetricsCollector } from '../../src/cli/prometheus-integration';
import { StateManager } from '../../src/core/state-manager';
import { HealthMonitor } from '../../src/cli/health-monitor';
import { DatabaseConnectionManager } from '../../src/cli/database-manager';
import axios from 'axios';

import { describe, it, test, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock dependencies
vi.mock('../../src/core/logger');
vi.mock('axios');

describe('PrometheusMetricsCollector', () => {
  let collector: PrometheusMetricsCollector;

  beforeEach(() => {
    const config = {
      enabled: true,
      port: 9090,
      host: 'localhost',
      path: '/metrics',
      scrapeInterval: 15,
      authentication: {
        enabled: false,
        type: 'bearer' as const
      },
      labels: { app: 'ai-shell', env: 'test' },
      retention: 3600
    };

    collector = new PrometheusMetricsCollector(config);
  });

  describe('Counter Metrics', () => {
    test('should increment counter metric', () => {
      collector.incrementCounter('ai_shell_queries_total', { database: 'postgres', type: 'select' });

      const metric = collector.getMetric('ai_shell_queries_total');
      expect(metric).toBeDefined();
      expect(metric!.values).toHaveLength(1);
      expect(metric!.values[0].value).toBe(1);
    });

    test('should increment counter with custom value', () => {
      collector.incrementCounter('ai_shell_queries_total', { database: 'mysql' }, 5);

      const metric = collector.getMetric('ai_shell_queries_total');
      expect(metric!.values[0].value).toBe(5);
    });

    test('should accumulate counter increments with same labels', () => {
      collector.incrementCounter('ai_shell_queries_total', { database: 'postgres' });
      collector.incrementCounter('ai_shell_queries_total', { database: 'postgres' });
      collector.incrementCounter('ai_shell_queries_total', { database: 'postgres' });

      const metric = collector.getMetric('ai_shell_queries_total');
      expect(metric!.values).toHaveLength(1);
      expect(metric!.values[0].value).toBe(3);
    });

    test('should track different label combinations separately', () => {
      collector.incrementCounter('ai_shell_queries_total', { database: 'postgres' });
      collector.incrementCounter('ai_shell_queries_total', { database: 'mysql' });

      const metric = collector.getMetric('ai_shell_queries_total');
      expect(metric!.values).toHaveLength(2);
    });

    test('should include global labels', () => {
      collector.incrementCounter('ai_shell_queries_total', { database: 'postgres' });

      const metric = collector.getMetric('ai_shell_queries_total');
      expect(metric!.values[0].labels).toMatchObject({ app: 'ai-shell', env: 'test' });
    });

    test('should emit metricUpdated event on counter increment', (done) => {
      collector.on('metricUpdated', (data) => {
        expect(data.name).toBe('ai_shell_queries_total');
        expect(data.type).toBe('counter');
        expect(data.value).toBe(1);
        done();
      });

      collector.incrementCounter('ai_shell_queries_total', {});
    });
  });

  describe('Gauge Metrics', () => {
    test('should set gauge metric value', () => {
      collector.setGauge('ai_shell_active_connections', 5, { database: 'postgres' });

      const metric = collector.getMetric('ai_shell_active_connections');
      expect(metric!.values[0].value).toBe(5);
    });

    test('should update gauge value for same labels', () => {
      collector.setGauge('ai_shell_active_connections', 5, { database: 'postgres' });
      collector.setGauge('ai_shell_active_connections', 10, { database: 'postgres' });

      const metric = collector.getMetric('ai_shell_active_connections');
      expect(metric!.values).toHaveLength(1);
      expect(metric!.values[0].value).toBe(10);
    });

    test('should track different gauge labels separately', () => {
      collector.setGauge('ai_shell_active_connections', 5, { database: 'postgres' });
      collector.setGauge('ai_shell_active_connections', 3, { database: 'mysql' });

      const metric = collector.getMetric('ai_shell_active_connections');
      expect(metric!.values).toHaveLength(2);
    });

    test('should emit metricUpdated event on gauge set', (done) => {
      collector.on('metricUpdated', (data) => {
        expect(data.name).toBe('ai_shell_active_connections');
        expect(data.type).toBe('gauge');
        expect(data.value).toBe(5);
        done();
      });

      collector.setGauge('ai_shell_active_connections', 5);
    });
  });

  describe('Histogram Metrics', () => {
    test('should observe histogram values', () => {
      collector.observeHistogram('ai_shell_query_duration_seconds', 0.15, { database: 'postgres' });

      const metric = collector.getMetric('ai_shell_query_duration_seconds');
      expect(metric).toBeDefined();
    });

    test('should track histogram buckets correctly', () => {
      collector.observeHistogram('ai_shell_query_duration_seconds', 0.05, { type: 'select' });
      collector.observeHistogram('ai_shell_query_duration_seconds', 0.15, { type: 'select' });
      collector.observeHistogram('ai_shell_query_duration_seconds', 1.5, { type: 'select' });

      const formatted = collector.formatMetrics();
      expect(formatted).toContain('ai_shell_query_duration_seconds_bucket');
      expect(formatted).toContain('ai_shell_query_duration_seconds_sum');
      expect(formatted).toContain('ai_shell_query_duration_seconds_count');
    });

    test('should calculate histogram sum correctly', () => {
      collector.observeHistogram('ai_shell_query_duration_seconds', 0.1, {});
      collector.observeHistogram('ai_shell_query_duration_seconds', 0.2, {});
      collector.observeHistogram('ai_shell_query_duration_seconds', 0.3, {});

      const formatted = collector.formatMetrics();
      expect(formatted).toContain('ai_shell_query_duration_seconds_sum{app="ai-shell",env="test"} 0.6');
    });

    test('should track histogram count correctly', () => {
      collector.observeHistogram('ai_shell_query_duration_seconds', 0.1, {});
      collector.observeHistogram('ai_shell_query_duration_seconds', 0.2, {});

      const formatted = collector.formatMetrics();
      expect(formatted).toContain('ai_shell_query_duration_seconds_count{app="ai-shell",env="test"} 2');
    });

    test('should emit metricUpdated event on histogram observation', (done) => {
      collector.on('metricUpdated', (data) => {
        expect(data.name).toBe('ai_shell_query_duration_seconds');
        expect(data.type).toBe('histogram');
        expect(data.value).toBe(0.15);
        done();
      });

      collector.observeHistogram('ai_shell_query_duration_seconds', 0.15);
    });
  });

  describe('Metrics Formatting', () => {
    test('should format metrics in Prometheus exposition format', () => {
      collector.incrementCounter('ai_shell_queries_total', { database: 'postgres' });
      collector.setGauge('ai_shell_active_connections', 5, {});

      const formatted = collector.formatMetrics();

      expect(formatted).toContain('# HELP ai_shell_queries_total');
      expect(formatted).toContain('# TYPE ai_shell_queries_total counter');
      expect(formatted).toContain('# HELP ai_shell_active_connections');
      expect(formatted).toContain('# TYPE ai_shell_active_connections gauge');
    });

    test('should escape label values correctly', () => {
      collector.incrementCounter('ai_shell_queries_total', { query: 'SELECT * FROM "test"' });

      const formatted = collector.formatMetrics();
      expect(formatted).toContain('query="SELECT * FROM \\"test\\""');
    });

    test('should handle labels with newlines', () => {
      collector.incrementCounter('ai_shell_queries_total', { error: 'Line 1\nLine 2' });

      const formatted = collector.formatMetrics();
      expect(formatted).toContain('error="Line 1\\nLine 2"');
    });

    test('should handle labels with backslashes', () => {
      collector.incrementCounter('ai_shell_queries_total', { path: 'C:\\Users\\test' });

      const formatted = collector.formatMetrics();
      expect(formatted).toContain('path="C:\\\\Users\\\\test"');
    });

    test('should format empty labels correctly', () => {
      collector.incrementCounter('ai_shell_queries_total', {});

      const formatted = collector.formatMetrics();
      expect(formatted).toMatch(/ai_shell_queries_total\{app="ai-shell",env="test"\}/);
    });

    test('should format histogram buckets with le label', () => {
      collector.observeHistogram('ai_shell_query_duration_seconds', 0.15, {});

      const formatted = collector.formatMetrics();
      expect(formatted).toContain('le="0.005"');
      expect(formatted).toContain('le="0.1"');
      expect(formatted).toContain('le="+Inf"');
    });
  });

  describe('Metrics Management', () => {
    test('should reset all metrics', () => {
      collector.incrementCounter('ai_shell_queries_total', {});
      collector.setGauge('ai_shell_active_connections', 5, {});

      collector.reset();

      const formatted = collector.formatMetrics();
      expect(formatted).not.toContain('ai_shell_queries_total{');
      expect(formatted).not.toContain('ai_shell_active_connections{');
    });

    test('should emit metricsReset event', (done) => {
      collector.on('metricsReset', () => {
        done();
      });

      collector.reset();
    });

    test('should clean old metrics based on retention', () => {
      // This test would require mocking Date.now() to test time-based cleanup
      collector.cleanOldMetrics();
      // Verify no errors thrown
    });

    test('should get metric by name', () => {
      const metric = collector.getMetric('ai_shell_queries_total');
      expect(metric).toBeDefined();
      expect(metric!.name).toBe('ai_shell_queries_total');
      expect(metric!.type).toBe('counter');
    });

    test('should get all metrics', () => {
      const metrics = collector.getAllMetrics();
      expect(metrics.length).toBeGreaterThan(0);
      expect(metrics.map(m => m.name)).toContain('ai_shell_queries_total');
      expect(metrics.map(m => m.name)).toContain('ai_shell_active_connections');
    });
  });
});

describe('PrometheusServer', () => {
  let server: PrometheusServer;
  let config: any;

  beforeEach(() => {
    config = {
      enabled: true,
      port: 9191, // Use different port for tests
      host: 'localhost',
      path: '/metrics',
      scrapeInterval: 15,
      authentication: {
        enabled: false,
        type: 'bearer' as const
      },
      labels: { app: 'ai-shell' },
      retention: 3600
    };

    server = new PrometheusServer(config);
  });

  afterEach(async () => {
    if (server.isRunning()) {
      await server.stop();
    }
  });

  describe('Server Lifecycle', () => {
    test('should start server successfully', async () => {
      await server.start();
      expect(server.isRunning()).toBe(true);
    });

    test('should stop server successfully', async () => {
      await server.start();
      await server.stop();
      expect(server.isRunning()).toBe(false);
    });

    test('should emit started event', async (done) => {
      server.on('started', () => {
        done();
      });

      await server.start();
    });

    test('should emit stopped event', async (done) => {
      await server.start();

      server.on('stopped', () => {
        done();
      });

      await server.stop();
    });

    test('should throw error when starting already running server', async () => {
      await server.start();

      await expect(server.start()).rejects.toThrow('already running');
    });
  });

  describe('Metrics Endpoint', () => {
    beforeEach(async () => {
      await server.start();
    });

    test('should serve metrics at configured path', async () => {
      const collector = server.getCollector();
      collector.incrementCounter('ai_shell_queries_total', { database: 'postgres' });

      const response = await axios.get(`http://localhost:${config.port}${config.path}`);
      expect(response.status).toBe(200);
      expect(response.headers['content-type']).toContain('text/plain');
      expect(response.data).toContain('ai_shell_queries_total');
    });

    test('should increment scrape count on each request', async () => {
      await axios.get(`http://localhost:${config.port}${config.path}`);
      await axios.get(`http://localhost:${config.port}${config.path}`);

      const status = server.getStatus();
      expect(status.scrapeCount).toBe(2);
    });

    test('should update last scrape timestamp', async () => {
      const before = Date.now();
      await axios.get(`http://localhost:${config.port}${config.path}`);

      const status = server.getStatus();
      expect(status.lastScrape).toBeGreaterThanOrEqual(before);
    });

    test('should return 404 for unknown paths', async () => {
      try {
        await axios.get(`http://localhost:${config.port}/unknown`);
        fail('Should have thrown 404');
      } catch (error: any) {
        expect(error.response.status).toBe(404);
      }
    });
  });

  describe('Health Endpoint', () => {
    beforeEach(async () => {
      await server.start();
    });

    test('should serve health status', async () => {
      const response = await axios.get(`http://localhost:${config.port}/health`);
      expect(response.status).toBe(200);
      expect(response.data).toMatchObject({
        status: 'healthy',
        uptime: expect.any(Number),
        metricsCount: expect.any(Number)
      });
    });
  });

  describe('Authentication', () => {
    test('should require basic auth when enabled', async () => {
      const authConfig = {
        ...config,
        authentication: {
          enabled: true,
          type: 'basic' as const,
          credentials: {
            username: 'admin',
            password: 'secret'
          }
        }
      };

      const authServer = new PrometheusServer(authConfig);
      await authServer.start();

      try {
        // Request without auth
        await axios.get(`http://localhost:${config.port}${config.path}`);
        fail('Should have required auth');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
      }

      // Request with correct auth
      const response = await axios.get(
        `http://localhost:${config.port}${config.path}`,
        {
          auth: {
            username: 'admin',
            password: 'secret'
          }
        }
      );
      expect(response.status).toBe(200);

      await authServer.stop();
    });

    test('should require bearer token when enabled', async () => {
      const authConfig = {
        ...config,
        authentication: {
          enabled: true,
          type: 'bearer' as const,
          credentials: {
            token: 'test-token-123'
          }
        }
      };

      const authServer = new PrometheusServer(authConfig);
      await authServer.start();

      try {
        await axios.get(`http://localhost:${config.port}${config.path}`);
        fail('Should have required auth');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
      }

      const response = await axios.get(
        `http://localhost:${config.port}${config.path}`,
        {
          headers: {
            Authorization: 'Bearer test-token-123'
          }
        }
      );
      expect(response.status).toBe(200);

      await authServer.stop();
    });

    test('should require API key when enabled', async () => {
      const authConfig = {
        ...config,
        authentication: {
          enabled: true,
          type: 'api-key' as const,
          credentials: {
            apiKey: 'my-api-key'
          }
        }
      };

      const authServer = new PrometheusServer(authConfig);
      await authServer.start();

      try {
        await axios.get(`http://localhost:${config.port}${config.path}`);
        fail('Should have required auth');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
      }

      const response = await axios.get(
        `http://localhost:${config.port}${config.path}`,
        {
          headers: {
            'X-API-Key': 'my-api-key'
          }
        }
      );
      expect(response.status).toBe(200);

      await authServer.stop();
    });
  });

  describe('Server Status', () => {
    test('should return correct status when running', async () => {
      await server.start();

      const status = server.getStatus();
      expect(status.running).toBe(true);
      expect(status.uptime).toBeGreaterThan(0);
      expect(status.metricsCount).toBeGreaterThan(0);
      expect(status.config).toMatchObject(config);
    });

    test('should return correct status when stopped', async () => {
      await server.start();
      await server.stop();

      const status = server.getStatus();
      expect(status.running).toBe(false);
      expect(status.uptime).toBe(0);
    });
  });

  describe('Health Monitor Integration', () => {
    test('should integrate with health monitor', async () => {
      const mockHealthMonitor = {
        on: vi.fn()
      } as any;

      const integratedServer = new PrometheusServer(config, mockHealthMonitor);
      await integratedServer.start();

      expect(mockHealthMonitor.on).toHaveBeenCalledWith('metricsCollected', expect.any(Function));

      await integratedServer.stop();
    });
  });
});

describe('PrometheusIntegration', () => {
  let integration: PrometheusIntegration;
  let mockStateManager: StateManager;

  beforeEach(() => {
    mockStateManager = {
      get: vi.fn().mockReturnValue(null),
      set: vi.fn()
    } as any;

    integration = new PrometheusIntegration(mockStateManager);
  });

  afterEach(async () => {
    const status = integration.getStatus();
    if (status?.running) {
      await integration.stop();
    }
  });

  describe('Configuration Management', () => {
    test('should load default configuration', () => {
      const config = integration.getConfig();
      expect(config).toMatchObject({
        enabled: false,
        port: 9090,
        host: '0.0.0.0',
        path: '/metrics'
      });
    });

    test('should save configuration', () => {
      integration.configure({ port: 9191 });
      expect(mockStateManager.set).toHaveBeenCalledWith(
        'prometheus-config',
        expect.objectContaining({ port: 9191 }),
        expect.any(Object)
      );
    });

    test('should merge configuration updates', () => {
      integration.configure({ port: 9191 });
      integration.configure({ host: '127.0.0.1' });

      const config = integration.getConfig();
      expect(config.port).toBe(9191);
      expect(config.host).toBe('127.0.0.1');
    });
  });

  describe('Server Management', () => {
    test('should start server with default configuration', async () => {
      await integration.start({ port: 9292 }); // Use unique port
      const status = integration.getStatus();
      expect(status?.running).toBe(true);
    });

    test('should stop running server', async () => {
      await integration.start({ port: 9393 });
      await integration.stop();

      const status = integration.getStatus();
      expect(status?.running).toBe(false);
    });

    test('should throw error when starting already running server', async () => {
      await integration.start({ port: 9494 });

      await expect(integration.start()).rejects.toThrow('already running');
    });

    test('should throw error when stopping non-running server', async () => {
      await expect(integration.stop()).rejects.toThrow('not running');
    });
  });

  describe('Metrics Access', () => {
    test('should provide access to collector when running', async () => {
      await integration.start({ port: 9595 });

      const collector = integration.getCollector();
      expect(collector).toBeDefined();
      expect(collector?.getAllMetrics).toBeDefined();
    });

    test('should return undefined collector when not running', () => {
      const collector = integration.getCollector();
      expect(collector).toBeUndefined();
    });
  });

  describe('Authentication Helpers', () => {
    test('should generate API key', () => {
      const apiKey = integration.generateApiKey();
      expect(apiKey).toHaveLength(64); // 32 bytes = 64 hex chars
      expect(/^[0-9a-f]+$/i.test(apiKey)).toBe(true);
    });

    test('should generate bearer token', () => {
      const token = integration.generateBearerToken();
      expect(token.length).toBeGreaterThan(0);
      expect(/^[A-Za-z0-9_-]+$/.test(token)).toBe(true);
    });

    test('should hash password', () => {
      const hash = integration.hashPassword('mypassword');
      expect(hash).toHaveLength(64); // SHA-256 = 64 hex chars
      expect(/^[0-9a-f]+$/i.test(hash)).toBe(true);
    });

    test('should generate different API keys', () => {
      const key1 = integration.generateApiKey();
      const key2 = integration.generateApiKey();
      expect(key1).not.toBe(key2);
    });
  });

  describe('Status Reporting', () => {
    test('should return null status when not running', () => {
      const status = integration.getStatus();
      expect(status).toBeNull();
    });

    test('should return complete status when running', async () => {
      await integration.start({ port: 9696 });

      const status = integration.getStatus();
      expect(status).toMatchObject({
        running: true,
        uptime: expect.any(Number),
        metricsCount: expect.any(Number),
        scrapeCount: expect.any(Number)
      });
    });
  });
});
