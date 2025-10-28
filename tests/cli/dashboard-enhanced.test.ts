/**
 * Enhanced Dashboard Tests
 * Comprehensive test suite for the monitoring dashboard
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { EnhancedDashboard, startDashboard, DashboardConfig } from '../../src/cli/dashboard-enhanced';
import { PerformanceMonitor } from '../../src/cli/performance-monitor';
import { HealthMonitor } from '../../src/cli/health-monitor';
import { QueryLogger } from '../../src/cli/query-logger';
import { StateManager } from '../../src/core/state-manager';
import { EventEmitter } from 'eventemitter3';
import * as fs from 'fs/promises';

// Mock blessed
vi.mock('blessed', () => ({
  default: {
    screen: vi.fn(() => ({
      render: vi.fn(),
      destroy: vi.fn(),
      key: vi.fn(),
      style: {}
    })),
    box: vi.fn(() => ({
      setContent: vi.fn(),
      destroy: vi.fn(),
      scroll: vi.fn(),
      style: { border: {} }
    }))
  },
  screen: vi.fn(() => ({
    render: vi.fn(),
    destroy: vi.fn(),
    key: vi.fn(),
    style: {}
  })),
  box: vi.fn(() => ({
    setContent: vi.fn(),
    destroy: vi.fn(),
    scroll: vi.fn(),
    style: { border: {} }
  }))
}));

describe('EnhancedDashboard', () => {
  let dashboard: EnhancedDashboard;
  let performanceMonitor: PerformanceMonitor;
  let healthMonitor: HealthMonitor;
  let queryLogger: QueryLogger;
  let stateManager: StateManager;

  beforeEach(() => {
    stateManager = new StateManager();

    // Mock performance monitor
    performanceMonitor = {
      getHistory: vi.fn(() => [{
        timestamp: Date.now(),
        activeConnections: 5,
        queriesPerSecond: 10,
        averageQueryTime: 100,
        slowQueriesCount: 0,
        cacheHitRate: 0.8,
        databaseSize: 1024 * 1024 * 100,
        growthRate: 1024 * 1024,
        lockWaits: 0,
        cpuUsage: 50,
        memoryUsage: 60
      }]),
      connectionPool: vi.fn(async () => ({
        totalConnections: 20,
        activeConnections: 5,
        idleConnections: 15,
        waitingQueries: 0,
        averageWaitTime: 10,
        maxWaitTime: 50
      })),
      on: vi.fn(),
      off: vi.fn()
    } as any;

    // Mock health monitor
    healthMonitor = {
      performHealthCheck: vi.fn(async () => ({
        connectionCount: { name: 'Connections', value: 5, unit: 'connections', status: 'healthy', timestamp: Date.now() },
        responseTime: { name: 'Response Time', value: 50, unit: 'ms', status: 'healthy', timestamp: Date.now() },
        errorRate: { name: 'Error Rate', value: 0, unit: '%', status: 'healthy', timestamp: Date.now() },
        cpuUsage: { name: 'CPU', value: 50, unit: '%', status: 'healthy', timestamp: Date.now() },
        memoryUsage: { name: 'Memory', value: 60, unit: '%', status: 'healthy', timestamp: Date.now() }
      })),
      on: vi.fn(),
      off: vi.fn()
    } as any;

    // Mock query logger
    queryLogger = {
      getHistory: vi.fn(async () => ({
        logs: [
          {
            id: 'query1',
            query: 'SELECT * FROM users',
            duration: 100,
            timestamp: Date.now(),
            result: { rowCount: 10 }
          }
        ],
        total: 1,
        page: 1,
        pageSize: 20
      })),
      on: vi.fn(),
      off: vi.fn()
    } as any;

    dashboard = new EnhancedDashboard(
      performanceMonitor,
      healthMonitor,
      queryLogger,
      stateManager
    );
  });

  afterEach(() => {
    if (dashboard) {
      dashboard.stop();
    }
  });

  describe('Dashboard Initialization', () => {
    it('should create dashboard with default config', () => {
      expect(dashboard).toBeDefined();
    });

    it('should create dashboard with custom config', () => {
      const config: DashboardConfig = {
        refreshInterval: 5000,
        layout: 'compact',
        theme: 'ocean',
        showTimestamps: true,
        enableAlerts: true,
        historySize: 200
      };

      const customDashboard = new EnhancedDashboard(
        performanceMonitor,
        healthMonitor,
        queryLogger,
        stateManager,
        config
      );

      expect(customDashboard).toBeDefined();
      customDashboard.stop();
    });

    it('should use default values for missing config', () => {
      const dashboard = new EnhancedDashboard(
        performanceMonitor,
        healthMonitor,
        queryLogger,
        stateManager,
        {}
      );

      expect(dashboard).toBeDefined();
      dashboard.stop();
    });

    it('should initialize with all themes', () => {
      const themes = ['dark', 'light', 'ocean', 'forest'] as const;

      themes.forEach(theme => {
        const d = new EnhancedDashboard(
          performanceMonitor,
          healthMonitor,
          queryLogger,
          stateManager,
          { theme }
        );
        expect(d).toBeDefined();
        d.stop();
      });
    });
  });

  describe('Dashboard Lifecycle', () => {
    it('should start dashboard successfully', async () => {
      const startedHandler = vi.fn();
      dashboard.on('started', startedHandler);

      await dashboard.start();

      expect(startedHandler).toHaveBeenCalled();
    });

    it('should stop dashboard successfully', async () => {
      const stoppedHandler = vi.fn();
      dashboard.on('stopped', stoppedHandler);

      await dashboard.start();
      dashboard.stop();

      expect(stoppedHandler).toHaveBeenCalled();
    });

    it('should throw error when starting already running dashboard', async () => {
      await dashboard.start();

      await expect(dashboard.start()).rejects.toThrow('already running');

      dashboard.stop();
    });

    it('should handle stop when not running', () => {
      expect(() => dashboard.stop()).not.toThrow();
    });

    it('should cleanup resources on stop', async () => {
      await dashboard.start();
      dashboard.stop();

      // Verify cleanup
      expect(dashboard['isRunning']).toBe(false);
      expect(dashboard['screen']).toBeUndefined();
    });
  });

  describe('Layout Management', () => {
    it('should change layout successfully', async () => {
      const layoutHandler = vi.fn();
      dashboard.on('layoutChanged', layoutHandler);

      await dashboard.start();
      await dashboard.changeLayout('compact');

      expect(layoutHandler).toHaveBeenCalledWith('compact');

      dashboard.stop();
    });

    it('should support all predefined layouts', async () => {
      await dashboard.start();

      const layouts = ['default', 'compact', 'detailed', 'monitoring'];

      for (const layout of layouts) {
        await expect(dashboard.changeLayout(layout)).resolves.not.toThrow();
      }

      dashboard.stop();
    });

    it('should throw error for invalid layout', async () => {
      await dashboard.start();

      await expect(dashboard.changeLayout('invalid')).rejects.toThrow('not found');

      dashboard.stop();
    });

    it('should preserve data when changing layout', async () => {
      await dashboard.start();

      dashboard.addAlert({
        severity: 'info',
        message: 'Test alert',
        source: 'test',
        resolved: false
      });

      await dashboard.changeLayout('compact');

      const alerts = dashboard['alerts'];
      expect(alerts.length).toBeGreaterThan(0);

      dashboard.stop();
    });
  });

  describe('Configuration', () => {
    it('should update configuration', () => {
      const newConfig: Partial<DashboardConfig> = {
        refreshInterval: 3000,
        theme: 'ocean'
      };

      dashboard.configure(newConfig);

      expect(dashboard['config'].refreshInterval).toBe(3000);
      expect(dashboard['config'].theme).toBe('ocean');
    });

    it('should handle partial configuration updates', () => {
      dashboard.configure({ refreshInterval: 1000 });

      expect(dashboard['config'].refreshInterval).toBe(1000);
      expect(dashboard['config'].theme).toBeDefined();
    });

    it('should update layout when configured', () => {
      dashboard.configure({ layout: 'compact' });

      expect(dashboard['config'].layout).toBe('compact');
    });
  });

  describe('Alert Management', () => {
    it('should add alert', () => {
      dashboard.addAlert({
        severity: 'warning',
        message: 'Test warning',
        source: 'test',
        resolved: false
      });

      const alerts = dashboard['alerts'];
      expect(alerts.length).toBe(1);
      expect(alerts[0].severity).toBe('warning');
      expect(alerts[0].message).toBe('Test warning');
    });

    it('should add alerts with different severities', () => {
      const severities = ['info', 'warning', 'critical'] as const;

      severities.forEach(severity => {
        dashboard.addAlert({
          severity,
          message: `Test ${severity}`,
          source: 'test',
          resolved: false
        });
      });

      const alerts = dashboard['alerts'];
      expect(alerts.length).toBe(3);
    });

    it('should generate unique alert IDs', () => {
      dashboard.addAlert({
        severity: 'info',
        message: 'Alert 1',
        source: 'test',
        resolved: false
      });

      dashboard.addAlert({
        severity: 'info',
        message: 'Alert 2',
        source: 'test',
        resolved: false
      });

      const alerts = dashboard['alerts'];
      expect(alerts[0].id).not.toBe(alerts[1].id);
    });

    it('should limit alert history size', () => {
      for (let i = 0; i < 150; i++) {
        dashboard.addAlert({
          severity: 'info',
          message: `Alert ${i}`,
          source: 'test',
          resolved: false
        });
      }

      const alerts = dashboard['alerts'];
      expect(alerts.length).toBeLessThanOrEqual(100);
    });

    it('should add timestamp to alerts', () => {
      const before = Date.now();

      dashboard.addAlert({
        severity: 'info',
        message: 'Test',
        source: 'test',
        resolved: false
      });

      const after = Date.now();
      const alert = dashboard['alerts'][0];

      expect(alert.timestamp).toBeGreaterThanOrEqual(before);
      expect(alert.timestamp).toBeLessThanOrEqual(after);
    });
  });

  describe('Export Functionality', () => {
    it('should export dashboard snapshot', async () => {
      vi.spyOn(fs, 'mkdir').mockResolvedValue(undefined);
      vi.spyOn(fs, 'writeFile').mockResolvedValue(undefined);

      const exportedHandler = vi.fn();
      dashboard.on('exported', exportedHandler);

      const filepath = await dashboard.export();

      expect(filepath).toContain('dashboard-snapshot');
      expect(exportedHandler).toHaveBeenCalledWith(filepath);
    });

    it('should export with custom filename', async () => {
      vi.spyOn(fs, 'mkdir').mockResolvedValue(undefined);
      vi.spyOn(fs, 'writeFile').mockResolvedValue(undefined);

      const filepath = await dashboard.export('custom-export.json');

      expect(filepath).toContain('custom-export.json');
    });

    it('should include all data in export', async () => {
      vi.spyOn(fs, 'mkdir').mockResolvedValue(undefined);

      let exportedData: any;
      vi.spyOn(fs, 'writeFile').mockImplementation(async (path, data) => {
        exportedData = JSON.parse(data as string);
      });

      dashboard.addAlert({
        severity: 'info',
        message: 'Test',
        source: 'test',
        resolved: false
      });

      await dashboard.export();

      expect(exportedData).toHaveProperty('timestamp');
      expect(exportedData).toHaveProperty('layout');
      expect(exportedData).toHaveProperty('stats');
      expect(exportedData).toHaveProperty('alerts');
      expect(exportedData).toHaveProperty('metrics');
    });

    it('should create export directory if missing', async () => {
      const mkdirSpy = vi.spyOn(fs, 'mkdir').mockResolvedValue(undefined);
      vi.spyOn(fs, 'writeFile').mockResolvedValue(undefined);

      await dashboard.export();

      expect(mkdirSpy).toHaveBeenCalled();
    });
  });

  describe('Metrics History', () => {
    it('should record metrics', async () => {
      await dashboard.start();

      // Wait for metrics to be recorded
      await new Promise(resolve => setTimeout(resolve, 100));

      const history = dashboard['metricsHistory'];
      expect(history.size).toBeGreaterThan(0);

      dashboard.stop();
    });

    it('should limit history size', () => {
      const maxSize = dashboard['config'].historySize;

      // Add more than max
      for (let i = 0; i < maxSize + 50; i++) {
        dashboard['recordMetric']('test', i);
      }

      const history = dashboard['metricsHistory'].get('test');
      expect(history?.length).toBeLessThanOrEqual(maxSize);
    });

    it('should track multiple metrics', () => {
      dashboard['recordMetric']('qps', 10);
      dashboard['recordMetric']('cpu', 50);
      dashboard['recordMetric']('memory', 60);

      const history = dashboard['metricsHistory'];
      expect(history.has('qps')).toBe(true);
      expect(history.has('cpu')).toBe(true);
      expect(history.has('memory')).toBe(true);
    });
  });

  describe('Statistics', () => {
    it('should update statistics', async () => {
      await dashboard.start();

      // Wait for stats update
      await new Promise(resolve => setTimeout(resolve, 100));

      const stats = dashboard['stats'];
      expect(stats.uptime).toBeGreaterThan(0);

      dashboard.stop();
    });

    it('should track uptime', async () => {
      await dashboard.start();

      await new Promise(resolve => setTimeout(resolve, 100));

      const uptime1 = dashboard['stats'].uptime;

      await new Promise(resolve => setTimeout(resolve, 100));

      const uptime2 = dashboard['stats'].uptime;

      expect(uptime2).toBeGreaterThan(uptime1);

      dashboard.stop();
    });
  });

  describe('Event Handling', () => {
    it('should emit started event', async () => {
      const handler = vi.fn();
      dashboard.on('started', handler);

      await dashboard.start();

      expect(handler).toHaveBeenCalled();

      dashboard.stop();
    });

    it('should emit stopped event', async () => {
      const handler = vi.fn();
      dashboard.on('stopped', handler);

      await dashboard.start();
      dashboard.stop();

      expect(handler).toHaveBeenCalled();
    });

    it('should emit layoutChanged event', async () => {
      const handler = vi.fn();
      dashboard.on('layoutChanged', handler);

      await dashboard.start();
      await dashboard.changeLayout('compact');

      expect(handler).toHaveBeenCalledWith('compact');

      dashboard.stop();
    });

    it('should emit exported event', async () => {
      vi.spyOn(fs, 'mkdir').mockResolvedValue(undefined);
      vi.spyOn(fs, 'writeFile').mockResolvedValue(undefined);

      const handler = vi.fn();
      dashboard.on('exported', handler);

      await dashboard.export();

      expect(handler).toHaveBeenCalled();
    });

    it('should emit error event on failures', async () => {
      const handler = vi.fn();
      dashboard.on('error', handler);

      // Simulate error in refresh
      vi.spyOn(performanceMonitor, 'getHistory').mockImplementation(() => {
        throw new Error('Test error');
      });

      await dashboard.start();

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(handler).toHaveBeenCalled();

      dashboard.stop();
    });
  });

  describe('Theme Support', () => {
    it('should apply dark theme', () => {
      const d = new EnhancedDashboard(
        performanceMonitor,
        healthMonitor,
        queryLogger,
        stateManager,
        { theme: 'dark' }
      );

      expect(d['config'].theme).toBe('dark');
      d.stop();
    });

    it('should apply light theme', () => {
      const d = new EnhancedDashboard(
        performanceMonitor,
        healthMonitor,
        queryLogger,
        stateManager,
        { theme: 'light' }
      );

      expect(d['config'].theme).toBe('light');
      d.stop();
    });

    it('should apply ocean theme', () => {
      const d = new EnhancedDashboard(
        performanceMonitor,
        healthMonitor,
        queryLogger,
        stateManager,
        { theme: 'ocean' }
      );

      expect(d['config'].theme).toBe('ocean');
      d.stop();
    });

    it('should apply forest theme', () => {
      const d = new EnhancedDashboard(
        performanceMonitor,
        healthMonitor,
        queryLogger,
        stateManager,
        { theme: 'forest' }
      );

      expect(d['config'].theme).toBe('forest');
      d.stop();
    });
  });

  describe('startDashboard Helper', () => {
    it('should start dashboard with helper function', async () => {
      const d = await startDashboard(
        performanceMonitor,
        healthMonitor,
        queryLogger,
        stateManager
      );

      expect(d).toBeInstanceOf(EnhancedDashboard);

      d.stop();
    });

    it('should pass config to helper function', async () => {
      const config: DashboardConfig = {
        layout: 'compact',
        theme: 'ocean'
      };

      const d = await startDashboard(
        performanceMonitor,
        healthMonitor,
        queryLogger,
        stateManager,
        config
      );

      expect(d['config'].layout).toBe('compact');
      expect(d['config'].theme).toBe('ocean');

      d.stop();
    });
  });

  describe('Panel Updates', () => {
    it('should update connection panel', async () => {
      await dashboard.start();

      await dashboard['updateConnectionPanel']();

      expect(performanceMonitor.connectionPool).toHaveBeenCalled();

      dashboard.stop();
    });

    it('should update performance panel', async () => {
      await dashboard.start();

      await dashboard['updatePerformancePanel']();

      expect(performanceMonitor.getHistory).toHaveBeenCalled();

      dashboard.stop();
    });

    it('should update query log panel', async () => {
      await dashboard.start();

      await dashboard['updateQueryLogPanel']();

      expect(queryLogger.getHistory).toHaveBeenCalled();

      dashboard.stop();
    });

    it('should update system health panel', async () => {
      await dashboard.start();

      await dashboard['updateSystemHealthPanel']();

      expect(healthMonitor.performHealthCheck).toHaveBeenCalled();

      dashboard.stop();
    });
  });

  describe('Error Handling', () => {
    it('should handle missing performance metrics', async () => {
      vi.spyOn(performanceMonitor, 'getHistory').mockReturnValue([]);

      await dashboard.start();

      await expect(dashboard['refresh']()).resolves.not.toThrow();

      dashboard.stop();
    });

    it('should handle query logger errors', async () => {
      vi.spyOn(queryLogger, 'getHistory').mockRejectedValue(new Error('Query error'));

      await dashboard.start();

      await new Promise(resolve => setTimeout(resolve, 100));

      // Should not crash
      expect(dashboard['isRunning']).toBe(true);

      dashboard.stop();
    });

    it('should handle health check errors', async () => {
      vi.spyOn(healthMonitor, 'performHealthCheck').mockRejectedValue(new Error('Health error'));

      await dashboard.start();

      await new Promise(resolve => setTimeout(resolve, 100));

      // Should not crash
      expect(dashboard['isRunning']).toBe(true);

      dashboard.stop();
    });
  });

  describe('Integration', () => {
    it('should integrate with performance monitor events', async () => {
      let alertCallback: Function;

      vi.spyOn(performanceMonitor, 'on').mockImplementation((event, callback) => {
        if (event === 'alert') {
          alertCallback = callback as Function;
        }
      });

      const d = new EnhancedDashboard(
        performanceMonitor,
        healthMonitor,
        queryLogger,
        stateManager
      );

      // Simulate alert
      alertCallback!('cpu', 'High CPU usage', 'warning');

      const alerts = d['alerts'];
      expect(alerts.some(a => a.message.includes('cpu'))).toBe(true);

      d.stop();
    });

    it('should integrate with query logger events', async () => {
      let slowQueryCallback: Function;

      vi.spyOn(queryLogger, 'on').mockImplementation((event, callback) => {
        if (event === 'slowQuery') {
          slowQueryCallback = callback as Function;
        }
      });

      const d = new EnhancedDashboard(
        performanceMonitor,
        healthMonitor,
        queryLogger,
        stateManager
      );

      // Simulate slow query
      slowQueryCallback!({
        id: 'q1',
        query: 'SELECT * FROM large_table',
        duration: 2000,
        timestamp: Date.now()
      });

      const alerts = d['alerts'];
      expect(alerts.some(a => a.message.includes('Slow query'))).toBe(true);

      d.stop();
    });
  });
});
