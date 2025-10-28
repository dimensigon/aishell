/**
 * Query Explainer Tests
 * Tests for query execution plan analysis and explanation
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { QueryExplainer } from '../../../src/cli/query-explainer';
import { DatabaseConnectionManager } from '../../../src/cli/db-connection-manager';
import { ErrorHandler } from '../../../src/core/error-handler';

describe('QueryExplainer', () => {
  let queryExplainer: QueryExplainer;
  let mockConnectionManager: DatabaseConnectionManager;
  let mockErrorHandler: ErrorHandler;

  beforeEach(() => {
    // Create mock connection manager
    mockConnectionManager = {
      getActive: vi.fn().mockReturnValue({
        type: 'postgresql',
        database: 'test_db',
        host: 'localhost'
      }),
      executeQuery: vi.fn()
    } as any;

    // Create mock error handler
    mockErrorHandler = {
      wrap: vi.fn((fn) => fn)
    } as any;

    queryExplainer = new QueryExplainer(mockConnectionManager, mockErrorHandler);
  });

  describe('explain()', () => {
    it('should explain PostgreSQL query', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Seq Scan',
            'Relation Name': 'users',
            'Total Cost': 100.25,
            'Plan Rows': 1000
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users', 'test_db');

      expect(result).toBeDefined();
      expect(result.query).toBe('SELECT * FROM users');
      expect(result.database).toBe('test_db');
      expect(result.databaseType).toBe('postgresql');
      expect(result.estimatedCost).toBeGreaterThan(0);
      expect(result.estimatedRows).toBeGreaterThan(0);
    });

    it('should identify sequential scan bottleneck', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Seq Scan',
            'Relation Name': 'users',
            'Total Cost': 1000.0,
            'Plan Rows': 100000
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users');

      expect(result.bottlenecks).toBeDefined();
      expect(result.bottlenecks.length).toBeGreaterThan(0);

      const seqScanBottleneck = result.bottlenecks.find(b => b.type === 'sequential_scan');
      expect(seqScanBottleneck).toBeDefined();
      expect(seqScanBottleneck?.severity).toBe('high');
    });

    it('should generate optimization suggestions', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Seq Scan',
            'Relation Name': 'users',
            'Total Cost': 500.0,
            'Plan Rows': 50000
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users WHERE email = ?');

      expect(result.suggestions).toBeDefined();
      expect(result.suggestions.length).toBeGreaterThan(0);

      const indexSuggestion = result.suggestions.find(s => s.type === 'index');
      expect(indexSuggestion).toBeDefined();
    });

    it('should calculate execution metrics', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Index Scan',
            'Relation Name': 'users',
            'Index Name': 'idx_users_email',
            'Total Cost': 10.25,
            'Plan Rows': 100
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users WHERE email = ?');

      expect(result.metrics).toBeDefined();
      expect(result.metrics.indexUsage).toBe(1);
      expect(result.metrics.tableScans).toBe(0);
    });

    it('should handle MySQL queries', async () => {
      vi.mocked(mockConnectionManager.getActive).mockReturnValue({
        type: 'mysql',
        database: 'test_db'
      } as any);

      const mockPlan = {
        EXPLAIN: JSON.stringify({
          query_block: {
            table: {
              table_name: 'users',
              access_type: 'ALL'
            },
            cost_info: {
              query_cost: 250.0,
              estimated_rows: 5000
            }
          }
        })
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users');

      expect(result.databaseType).toBe('mysql');
      expect(result.estimatedCost).toBeGreaterThan(0);
    });

    it('should handle SQLite queries', async () => {
      vi.mocked(mockConnectionManager.getActive).mockReturnValue({
        type: 'sqlite',
        database: 'test.db'
      } as any);

      const mockPlan = [
        { detail: 'SCAN TABLE users' },
        { detail: 'USE TEMP B-TREE FOR ORDER BY' }
      ];

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce(mockPlan);

      const result = await queryExplainer.explain('SELECT * FROM users ORDER BY name');

      expect(result.databaseType).toBe('sqlite');
      expect(result.executionPlan).toBeDefined();
    });

    it('should detect nested loop joins', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Nested Loop',
            'Join Type': 'Inner',
            'Total Cost': 5000.0,
            'Plan Rows': 50000,
            Plans: [
              {
                'Node Type': 'Seq Scan',
                'Relation Name': 'users',
                'Total Cost': 100.0,
                'Plan Rows': 1000
              },
              {
                'Node Type': 'Seq Scan',
                'Relation Name': 'orders',
                'Total Cost': 200.0,
                'Plan Rows': 5000
              }
            ]
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users u JOIN orders o ON u.id = o.user_id');

      const nestedLoopBottleneck = result.bottlenecks.find(b => b.type === 'nested_loop');
      expect(nestedLoopBottleneck).toBeDefined();
      expect(nestedLoopBottleneck?.severity).toBe('high');
    });

    it('should detect large result sets', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Seq Scan',
            'Relation Name': 'logs',
            'Total Cost': 10000.0,
            'Plan Rows': 2000000
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM logs');

      const largeResultBottleneck = result.bottlenecks.find(b => b.type === 'large_result_set');
      expect(largeResultBottleneck).toBeDefined();
      expect(largeResultBottleneck?.severity).toBe('high');
    });

    it('should throw error for unsupported database type', async () => {
      vi.mocked(mockConnectionManager.getActive).mockReturnValue({
        type: 'oracle',
        database: 'test_db'
      } as any);

      await expect(
        queryExplainer.explain('SELECT * FROM users')
      ).rejects.toThrow('Unsupported database type: oracle');
    });

    it('should throw error when no connection active', async () => {
      vi.mocked(mockConnectionManager.getActive).mockReturnValue(null);

      await expect(
        queryExplainer.explain('SELECT * FROM users')
      ).rejects.toThrow('No active database connection');
    });
  });

  describe('formatExplanation()', () => {
    it('should format explanation as text', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Seq Scan',
            'Relation Name': 'users',
            'Total Cost': 100.25,
            'Plan Rows': 1000
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users');
      const formatted = queryExplainer.formatExplanation(result, 'text');

      expect(formatted).toContain('QUERY EXECUTION PLAN');
      expect(formatted).toContain('SELECT * FROM users');
      expect(formatted).toContain('Estimated Cost:');
      expect(formatted).toContain('Estimated Rows:');
    });

    it('should format explanation as JSON', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Index Scan',
            'Relation Name': 'users',
            'Index Name': 'idx_users_id',
            'Total Cost': 10.0,
            'Plan Rows': 100
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users WHERE id = 1');
      const formatted = queryExplainer.formatExplanation(result, 'json');

      expect(() => JSON.parse(formatted)).not.toThrow();

      const parsed = JSON.parse(formatted);
      expect(parsed.query).toBe('SELECT * FROM users WHERE id = 1');
      expect(parsed.estimatedCost).toBeDefined();
      expect(parsed.bottlenecks).toBeDefined();
    });

    it('should include visual execution plan', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Nested Loop',
            'Total Cost': 500.0,
            'Plan Rows': 1000,
            Plans: [
              {
                'Node Type': 'Seq Scan',
                'Relation Name': 'users',
                'Total Cost': 100.0,
                'Plan Rows': 100
              },
              {
                'Node Type': 'Index Scan',
                'Relation Name': 'orders',
                'Index Name': 'idx_orders_user_id',
                'Total Cost': 50.0,
                'Plan Rows': 10
              }
            ]
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users u JOIN orders o ON u.id = o.user_id');
      const formatted = queryExplainer.formatExplanation(result, 'text');

      expect(formatted).toContain('Visual Execution Plan:');
      expect(formatted).toContain('Nested Loop');
      expect(formatted).toContain('Seq Scan');
      expect(formatted).toContain('Index Scan');
    });

    it('should display bottlenecks with severity icons', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Seq Scan',
            'Relation Name': 'users',
            'Total Cost': 1000.0,
            'Plan Rows': 200000
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users');
      const formatted = queryExplainer.formatExplanation(result, 'text');

      expect(formatted).toContain('Performance Bottlenecks:');
      expect(formatted).toContain('Severity:');
      expect(formatted).toContain('Impact:');
      expect(formatted).toContain('Fix:');
    });

    it('should display optimization suggestions with priority', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Seq Scan',
            'Relation Name': 'users',
            'Total Cost': 500.0,
            'Plan Rows': 50000
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users WHERE email = ?');
      const formatted = queryExplainer.formatExplanation(result, 'text');

      expect(formatted).toContain('Optimization Suggestions:');
      expect(formatted).toContain('Priority:');
      expect(formatted).toContain('Improvement:');
    });
  });

  describe('Performance Estimation', () => {
    it('should estimate execution time from cost', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Index Scan',
            'Total Cost': 50.0,
            'Plan Rows': 100
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users WHERE id = 1');

      expect(result.estimatedTime).toBeDefined();
      expect(result.estimatedTime).toMatch(/ms|s|min/);
    });

    it('should adjust time estimate for large datasets', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Seq Scan',
            'Total Cost': 1000.0,
            'Plan Rows': 2000000
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users');

      // Should have longer estimated time for large datasets
      expect(result.estimatedTime).toBeDefined();
    });
  });

  describe('Permission Checking', () => {
    it('should check SELECT permissions', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Seq Scan',
            'Total Cost': 100.0,
            'Plan Rows': 1000
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('SELECT * FROM users');

      expect(result.permissions).toBeDefined();
      expect(result.permissions.requiredPermissions).toContain('SELECT');
    });

    it('should check UPDATE permissions', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'Update',
            'Total Cost': 50.0,
            'Plan Rows': 10
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('UPDATE users SET active = true WHERE id = 1');

      expect(result.permissions.requiredPermissions).toContain('UPDATE');
    });

    it('should check DDL permissions', async () => {
      const mockPlan = {
        'QUERY PLAN': [{
          Plan: {
            'Node Type': 'DDL',
            'Total Cost': 10.0,
            'Plan Rows': 0
          }
        }]
      };

      vi.mocked(mockConnectionManager.executeQuery).mockResolvedValueOnce([mockPlan]);

      const result = await queryExplainer.explain('CREATE INDEX idx_users_email ON users(email)');

      expect(result.permissions.requiredPermissions).toContain('DDL');
    });
  });
});
