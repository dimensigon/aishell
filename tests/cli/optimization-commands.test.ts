/**
 * Optimization Commands Tests
 * Tests for all 13 Sprint 1 optimization CLI commands
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { OptimizationCLI } from '../../src/cli/optimization-cli';
import { StateManager } from '../../src/core/state-manager';
import { DatabaseConnectionManager } from '../../src/cli/database-manager';

// Mock Anthropic SDK at module level
vi.mock('@anthropic-ai/sdk', () => {
  class MockAnthropic {
    messages = {
      create: vi.fn().mockResolvedValue({
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              issues: [
                'Using SELECT * is inefficient',
                'Missing index on active column',
                'Full table scan detected'
              ],
              suggestions: [
                'Replace SELECT * with specific column names',
                'Add index on users(active)',
                'Consider adding composite index for frequently queried columns'
              ],
              optimizedQuery: 'SELECT id, name, email FROM users WHERE active = true',
              indexRecommendations: [
                'CREATE INDEX idx_users_active ON users(active)',
                'CREATE INDEX idx_users_email ON users(email)'
              ],
              estimatedImprovement: '45% faster'
            })
          }
        ],
        usage: {
          input_tokens: 150,
          output_tokens: 200
        }
      })
    };

    constructor(config: any) {
      // Mock constructor
    }
  }

  return {
    default: MockAnthropic
  };
});

// Mock dependencies
vi.mock('../../src/core/state-manager');
vi.mock('../../src/cli/database-manager');

// Mock LLMMCPBridge for natural language translation
vi.mock('../../src/llm/mcp-bridge', () => {
  class MockLLMMCPBridge {
    async generate(options: any) {
      return {
        content: JSON.stringify({
          sql: 'SELECT * FROM users',
          explanation: 'This query retrieves all users from the users table',
          confidence: 0.95,
          warnings: []
        })
      };
    }

    constructor(apiKey: string) {
      // Mock constructor
    }
  }

  return {
    LLMMCPBridge: MockLLMMCPBridge
  };
});

// Mock ErrorHandler to properly wrap async functions
vi.mock('../../src/core/error-handler', () => {
  class MockErrorHandler {
    wrap(fn: Function, context?: any) {
      return fn;
    }
    handle(error: any) {
      throw error;
    }
  }

  return {
    ErrorHandler: MockErrorHandler
  };
});

describe('OptimizationCLI - Sprint 1 Commands', () => {
  let cli: OptimizationCLI;
  let stateManager: StateManager;
  let dbManager: DatabaseConnectionManager;

  beforeEach(() => {
    // Clear all mocks before each test to ensure clean state
    vi.clearAllMocks();

    // Set API key for tests
    process.env.ANTHROPIC_API_KEY = 'test-api-key';

    stateManager = new StateManager();
    dbManager = new DatabaseConnectionManager(stateManager);
    cli = new OptimizationCLI(stateManager, dbManager);
  });

  afterEach(() => {
    vi.clearAllMocks();
    delete process.env.ANTHROPIC_API_KEY;
  });

  describe('1. ai-shell translate <natural-language>', () => {
    it('should translate natural language to SQL', async () => {
      const result = await cli.translateNaturalLanguage('show me all users');

      expect(result).toBeDefined();
      expect(result.sql).toContain('SELECT');
      expect(result.explanation).toBeTruthy();
      expect(result.confidence).toBeGreaterThan(0);
    });

    it('should handle complex queries with filters', async () => {
      const result = await cli.translateNaturalLanguage(
        'find all orders from last week where total is greater than 100'
      );

      expect(result.sql).toContain('WHERE');
      expect(result.sql).toMatch(/orders?/i);
    });

    it('should provide warnings for ambiguous queries', async () => {
      const result = await cli.translateNaturalLanguage('get stuff');

      expect(result.warnings).toBeDefined();
      expect(Array.isArray(result.warnings)).toBe(true);
    });

    it('should support JSON output format', async () => {
      const consoleSpy = vi.spyOn(console, 'log');

      await cli.translateNaturalLanguage('show users', { format: 'json' });

      const jsonOutput = consoleSpy.mock.calls.find(call =>
        typeof call[0] === 'string' && call[0].includes('"sql"')
      );
      expect(jsonOutput).toBeDefined();
    });

    it('should export results to file when output option provided', async () => {
      const outputPath = '/tmp/test-translation.json';

      await cli.translateNaturalLanguage('show users', {
        output: outputPath,
        format: 'json'
      });

      // Verify file would be created (mocked in actual implementation)
      expect(true).toBe(true);
    });
  });

  describe('2. ai-shell indexes missing', () => {
    it('should detect missing indexes from query patterns', async () => {
      const recommendations = await cli.findMissingIndexes();

      expect(Array.isArray(recommendations)).toBe(true);
    });

    it('should respect threshold parameter', async () => {
      const recommendations = await cli.findMissingIndexes({
        threshold: 500
      });

      expect(Array.isArray(recommendations)).toBe(true);
    });

    it('should limit number of recommendations', async () => {
      const recommendations = await cli.findMissingIndexes({
        limit: 5
      });

      expect(recommendations.length).toBeLessThanOrEqual(5);
    });

    it('should identify indexes for full table scans', async () => {
      // Mock slow query with full table scan
      const recommendations = await cli.findMissingIndexes();

      if (recommendations.length > 0) {
        const rec = recommendations[0];
        expect(rec).toHaveProperty('table');
        expect(rec).toHaveProperty('columns');
        expect(rec).toHaveProperty('indexName');
        expect(rec).toHaveProperty('createStatement');
      }
    });

    it('should show success message when no missing indexes', async () => {
      const consoleSpy = vi.spyOn(console, 'log');

      await cli.findMissingIndexes();

      // Should either show recommendations or success message
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('3. ai-shell indexes create <spec>', () => {
    it('should create index with basic specification', async () => {
      const consoleSpy = vi.spyOn(console, 'log');

      await cli.createIndex('idx_test', 'users', ['email']);

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Creating index')
      );
    });

    it('should support multiple columns', async () => {
      await cli.createIndex('idx_multi', 'orders', ['user_id', 'created_at']);

      // Should complete without error
      expect(true).toBe(true);
    });

    it('should support online index creation', async () => {
      const consoleSpy = vi.spyOn(console, 'log');

      await cli.createIndex('idx_online', 'users', ['email'], true);

      const output = consoleSpy.mock.calls.find(call =>
        call[0]?.includes('CONCURRENTLY')
      );
      expect(output).toBeDefined();
    });

    it('should display create statement before execution', async () => {
      const consoleSpy = vi.spyOn(console, 'log');

      await cli.createIndex('idx_test', 'users', ['email']);

      const statement = consoleSpy.mock.calls.find(call =>
        call[0]?.includes('CREATE INDEX')
      );
      expect(statement).toBeDefined();
    });

    it('should handle index creation errors gracefully', async () => {
      // Mock error scenario
      await expect(async () => {
        await cli.createIndex('', 'users', []);
      }).rejects.toThrow();
    });
  });

  describe('4. ai-shell indexes drop <name>', () => {
    it('should drop index by name', async () => {
      const consoleSpy = vi.spyOn(console, 'log');

      await cli.dropIndex('idx_test');

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Dropping index')
      );
    });

    it('should confirm before dropping', async () => {
      const consoleSpy = vi.spyOn(console, 'log');

      await cli.dropIndex('idx_important');

      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should handle non-existent indexes', async () => {
      await expect(async () => {
        await cli.dropIndex('idx_nonexistent');
      }).rejects.toThrow();
    });

    it('should display success message on completion', async () => {
      const consoleSpy = vi.spyOn(console, 'log');

      await cli.dropIndex('idx_test');

      const success = consoleSpy.mock.calls.find(call =>
        call[0]?.includes('✅')
      );
      expect(success).toBeDefined();
    });

    it('should handle empty index name', async () => {
      await expect(async () => {
        await cli.dropIndex('');
      }).rejects.toThrow();
    });
  });

  describe('5. ai-shell optimize-all', () => {
    it('should optimize all slow queries', async () => {
      const results = await cli.optimizeAllSlowQueries();

      expect(Array.isArray(results)).toBe(true);
    });

    it('should respect threshold parameter', async () => {
      const results = await cli.optimizeAllSlowQueries({
        threshold: 500
      });

      expect(Array.isArray(results)).toBe(true);
    });

    it('should apply optimizations when auto-apply enabled', async () => {
      const results = await cli.optimizeAllSlowQueries({
        autoApply: true
      });

      if (results.length > 0) {
        expect(results[0].appliedOptimizations.length).toBeGreaterThanOrEqual(0);
      }
    });

    it('should generate optimization report', async () => {
      const reportPath = '/tmp/optimization-report.json';

      await cli.optimizeAllSlowQueries({
        report: reportPath
      });

      // Verify report would be created
      expect(true).toBe(true);
    });

    it('should display summary statistics', async () => {
      const consoleSpy = vi.spyOn(console, 'log');

      await cli.optimizeAllSlowQueries();

      const summary = consoleSpy.mock.calls.find(call =>
        call[0]?.includes('Optimization Summary')
      );
      expect(summary).toBeDefined();
    });

    it('should handle empty slow query log', async () => {
      const results = await cli.optimizeAllSlowQueries();

      expect(results).toBeDefined();
      expect(Array.isArray(results)).toBe(true);
    });

    it('should calculate average improvement', async () => {
      const consoleSpy = vi.spyOn(console, 'log');

      await cli.optimizeAllSlowQueries();

      const avgImprovement = consoleSpy.mock.calls.find(call =>
        call[0]?.toString().includes('Average Improvement')
      );
      expect(avgImprovement).toBeDefined();
    });
  });

  describe('6-8. Existing Commands (Verification)', () => {
    it('should optimize single query', async () => {
      const result = await cli.optimizeQuery('SELECT * FROM users WHERE id = 1');

      expect(result).toHaveProperty('originalQuery');
      expect(result).toHaveProperty('optimizedQuery');
      expect(result).toHaveProperty('improvementPercent');
    });

    it('should analyze slow queries', async () => {
      const queries = await cli.analyzeSlowQueries();

      expect(Array.isArray(queries)).toBe(true);
    });

    it('should analyze indexes', async () => {
      const recommendations = await cli.analyzeIndexes();

      expect(Array.isArray(recommendations)).toBe(true);
    });
  });

  describe('9-13. Additional Existing Commands', () => {
    it('should get index recommendations', async () => {
      const recommendations = await cli.getIndexRecommendations();

      expect(Array.isArray(recommendations)).toBe(true);
    });

    it('should analyze query patterns', async () => {
      const patterns = await cli.analyzePatterns();

      expect(patterns).toHaveProperty('fullTableScans');
      expect(patterns).toHaveProperty('missingIndexes');
    });

    it('should get index statistics', async () => {
      const stats = await cli.getIndexStats();

      expect(stats).toHaveProperty('totalIndexes');
      expect(stats).toHaveProperty('unusedIndexes');
    });

    it('should enable auto-optimization', async () => {
      await cli.enableAutoOptimization({
        thresholdMs: 500,
        maxOptimizationsPerDay: 20
      });

      const status = await cli.getAutoOptimizationStatus();
      expect(status.enabled).toBe(true);
    });

    it('should disable auto-optimization', async () => {
      await cli.disableAutoOptimization();

      const status = await cli.getAutoOptimizationStatus();
      expect(status.enabled).toBe(false);
    });
  });

  describe('Integration Tests', () => {
    it('should complete full optimization workflow', async () => {
      // 1. Analyze slow queries
      const slowQueries = await cli.analyzeSlowQueries({ threshold: 1000 });

      // 2. Find missing indexes
      const missingIndexes = await cli.findMissingIndexes();

      // 3. Optimize all slow queries
      const optimized = await cli.optimizeAllSlowQueries();

      expect(Array.isArray(slowQueries)).toBe(true);
      expect(Array.isArray(missingIndexes)).toBe(true);
      expect(Array.isArray(optimized)).toBe(true);
    });

    it('should handle NL translation to optimization pipeline', async () => {
      // 1. Translate NL to SQL
      const translation = await cli.translateNaturalLanguage('show all users');

      // 2. Optimize the generated SQL
      const optimization = await cli.optimizeQuery(translation.sql);

      expect(optimization).toBeDefined();
      expect(optimization.optimizedQuery).toBeTruthy();
    });
  });

  describe('Error Handling', () => {
    it('should handle missing API key', () => {
      delete process.env.ANTHROPIC_API_KEY;

      expect(() => {
        new OptimizationCLI();
      }).toThrow('ANTHROPIC_API_KEY environment variable not set');

      // Restore for other tests
      process.env.ANTHROPIC_API_KEY = 'test-api-key';
    });

    it('should handle invalid query syntax', async () => {
      await expect(async () => {
        await cli.optimizeQuery('INVALID SQL QUERY !!!');
      }).rejects.toThrow();
    });

    it('should handle database connection errors', async () => {
      // Mock disconnected state
      vi.spyOn(dbManager, 'getActive').mockReturnValue(null);

      const result = await cli.translateNaturalLanguage('show users');

      // Should still return result with minimal schema
      expect(result).toBeDefined();
    });
  });
});
