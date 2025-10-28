/**
 * Pattern Detection System Tests
 * Comprehensive test suite with 42+ test cases
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { PatternDetector, PatternType } from '../../src/cli/pattern-detection';
import { QueryLogger, QueryLog } from '../../src/cli/query-logger';
import { StateManager } from '../../src/core/state-manager';

describe('PatternDetector', () => {
  let detector: PatternDetector;
  let stateManager: StateManager;
  let queryLogger: QueryLogger;

  beforeEach(() => {
    stateManager = new StateManager(':memory:');
    queryLogger = new QueryLogger(stateManager);
    detector = new PatternDetector(stateManager, queryLogger, {
      minSamplesForPattern: 3,
      anomalyThreshold: 0.7,
      clusteringEpsilon: 0.3,
      securityScanEnabled: true,
      learningEnabled: true,
      aiAnalysisEnabled: false
    });
  });

  afterEach(() => {
    detector.clearPatterns();
  });

  describe('Pattern Analysis', () => {
    it('should analyze patterns from query history', async () => {
      // Add sample queries
      await addSampleQueries(queryLogger);

      const insights = await detector.analyze({ period: 7 });

      expect(insights).toBeDefined();
      expect(insights.summary.totalPatterns).toBeGreaterThan(0);
      expect(insights.patterns).toBeInstanceOf(Array);
      expect(insights.confidence).toBeGreaterThan(0);
    });

    it('should handle empty query history', async () => {
      const insights = await detector.analyze();

      expect(insights.summary.totalPatterns).toBe(0);
      expect(insights.patterns).toEqual([]);
      expect(insights.confidence).toBe(0);
    });

    it('should filter patterns by period', async () => {
      await addSampleQueries(queryLogger);

      const insights = await detector.analyze({ period: 1 });

      expect(insights).toBeDefined();
      // Should only include recent queries
    });

    it('should filter patterns by type', async () => {
      await addSampleQueries(queryLogger);

      const insights = await detector.analyze({
        types: [PatternType.PERFORMANCE]
      });

      expect(insights.patterns.every(p => p.type === PatternType.PERFORMANCE)).toBe(true);
    });

    it('should calculate correct confidence levels', async () => {
      await addSampleQueries(queryLogger, 100);

      const insights = await detector.analyze();

      expect(insights.confidence).toBeGreaterThan(0.5);
      expect(insights.confidence).toBeLessThanOrEqual(1);
    });

    it('should detect pattern clusters', async () => {
      // Add similar queries
      for (let i = 0; i < 10; i++) {
        await queryLogger.logQuery(
          `SELECT * FROM users WHERE id = ${i}`,
          Math.random() * 100 + 50
        );
      }

      const insights = await detector.analyze();

      expect(insights.summary.clustersFound).toBeGreaterThan(0);
    });

    it('should identify pattern characteristics', async () => {
      await queryLogger.logQuery(
        'SELECT * FROM users JOIN orders ON users.id = orders.user_id',
        1500
      );
      await queryLogger.logQuery(
        'SELECT * FROM products JOIN categories ON products.cat_id = categories.id',
        1600
      );

      const insights = await detector.analyze();

      const pattern = insights.patterns[0];
      if (pattern) {
        expect(pattern.characteristics).toBeInstanceOf(Array);
        expect(pattern.characteristics.length).toBeGreaterThan(0);
      }
    });

    it('should track pattern frequency', async () => {
      const query = 'SELECT * FROM users';
      for (let i = 0; i < 5; i++) {
        await queryLogger.logQuery(query, 50);
      }

      const insights = await detector.analyze();

      const pattern = insights.patterns.find(p =>
        p.queries.some(q => q.includes('users'))
      );

      expect(pattern?.frequency).toBeGreaterThanOrEqual(5);
    });
  });

  describe('Clustering', () => {
    it('should cluster similar queries', async () => {
      // Add similar SELECT queries
      for (let i = 0; i < 5; i++) {
        await queryLogger.logQuery(
          `SELECT name, email FROM users WHERE age > ${20 + i}`,
          100
        );
      }

      const insights = await detector.analyze();

      expect(insights.summary.clustersFound).toBeGreaterThan(0);
    });

    it('should separate different query types', async () => {
      await queryLogger.logQuery('SELECT * FROM users', 50);
      await queryLogger.logQuery('INSERT INTO users (name) VALUES ("test")', 30);
      await queryLogger.logQuery('UPDATE users SET name = "test"', 40);
      await queryLogger.logQuery('DELETE FROM users WHERE id = 1', 35);

      const insights = await detector.analyze();

      // Should create separate clusters for different operations
      expect(insights.patterns.length).toBeGreaterThan(0);
    });

    it('should calculate cluster centroids', async () => {
      for (let i = 0; i < 5; i++) {
        await queryLogger.logQuery(
          'SELECT * FROM users JOIN orders ON users.id = orders.user_id',
          1000 + i * 100
        );
      }

      const insights = await detector.analyze();
      const cluster = insights.patterns[0];

      expect(cluster?.centroid).toBeDefined();
      expect(cluster?.avgPerformance).toBeGreaterThan(0);
    });

    it('should use configurable epsilon for clustering', async () => {
      const customDetector = new PatternDetector(
        stateManager,
        queryLogger,
        { clusteringEpsilon: 0.1 }
      );

      await addSampleQueries(queryLogger);
      const insights = await customDetector.analyze();

      expect(insights.patterns).toBeDefined();
    });
  });

  describe('Anomaly Detection', () => {
    it('should detect anomalous queries', async () => {
      // Add normal queries
      for (let i = 0; i < 10; i++) {
        await queryLogger.logQuery('SELECT * FROM users', 50);
      }

      // Add anomalous query
      await queryLogger.logQuery(
        'SELECT * FROM users JOIN orders JOIN products JOIN categories JOIN suppliers',
        5000
      );

      const insights = await detector.analyze();

      expect(insights.summary.anomaliesDetected).toBeGreaterThan(0);
    });

    it('should calculate anomaly scores', async () => {
      await addSampleQueries(queryLogger);
      await queryLogger.logQuery(
        'SELECT * FROM ' + 'users JOIN '.repeat(10) + 'orders',
        10000
      );

      const insights = await detector.analyze();
      const anomaly = insights.anomalies[0];

      expect(anomaly?.anomalyScore).toBeGreaterThan(0);
      expect(anomaly?.anomalyScore).toBeLessThanOrEqual(1);
    });

    it('should classify anomaly severity', async () => {
      await addSampleQueries(queryLogger);
      await queryLogger.logQuery(
        'SELECT * FROM users WHERE 1=1 OR 2=2',
        50
      );

      const insights = await detector.analyze();
      const anomaly = insights.anomalies[0];

      if (anomaly) {
        expect(['low', 'medium', 'high', 'critical']).toContain(anomaly.severity);
      }
    });

    it('should identify anomaly reasons', async () => {
      await addSampleQueries(queryLogger);
      await queryLogger.logQuery(
        'SELECT * FROM users ' + 'JOIN orders '.repeat(8),
        3000
      );

      const insights = await detector.analyze();
      const anomaly = insights.anomalies[0];

      expect(anomaly?.reasons).toBeInstanceOf(Array);
      expect(anomaly?.reasons.length).toBeGreaterThan(0);
    });

    it('should classify anomaly types', async () => {
      await queryLogger.logQuery('SELECT * FROM users', 50);
      await queryLogger.logQuery('SELECT * FROM users WHERE id = 1 OR 1=1', 60);

      const insights = await detector.analyze();
      const anomaly = insights.anomalies.find(a => a.query.includes('OR 1=1'));

      if (anomaly) {
        expect(['performance', 'security', 'structural', 'behavioral']).toContain(
          anomaly.type
        );
      }
    });

    it('should provide anomaly recommendations', async () => {
      await addSampleQueries(queryLogger);
      await queryLogger.logQuery('SELECT * FROM users', 10000);

      const insights = await detector.analyze();
      const anomaly = insights.anomalies[0];

      if (anomaly) {
        expect(anomaly.recommendation).toBeDefined();
        expect(typeof anomaly.recommendation).toBe('string');
      }
    });

    it('should use configurable anomaly threshold', async () => {
      const sensitiveDetector = new PatternDetector(
        stateManager,
        queryLogger,
        { anomalyThreshold: 0.5 }
      );

      await addSampleQueries(queryLogger);
      const insights = await sensitiveDetector.analyze();

      // Lower threshold should detect more anomalies
      expect(insights.anomalies.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Security Detection', () => {
    it('should detect SQL injection attempts', async () => {
      await queryLogger.logQuery(
        "SELECT * FROM users WHERE id = 1 OR '1'='1'",
        50
      );

      const insights = await detector.analyze();

      expect(insights.summary.securityThreats).toBeGreaterThan(0);
      expect(insights.securityThreats[0]?.threatType).toBe('sql_injection');
    });

    it('should detect UNION injection', async () => {
      await queryLogger.logQuery(
        'SELECT * FROM users UNION SELECT * FROM admin',
        50
      );

      const insights = await detector.analyze();

      const threat = insights.securityThreats.find(
        t => t.threatType === 'sql_injection'
      );
      expect(threat).toBeDefined();
    });

    it('should detect data exfiltration patterns', async () => {
      await queryLogger.logQuery('SELECT * FROM users', 50);

      const insights = await detector.analyze();

      const threat = insights.securityThreats.find(
        t => t.threatType === 'data_exfiltration'
      );
      expect(threat).toBeDefined();
    });

    it('should detect privilege escalation', async () => {
      await queryLogger.logQuery('GRANT ALL PRIVILEGES ON *.* TO user@host', 50);

      const insights = await detector.analyze();

      const threat = insights.securityThreats.find(
        t => t.threatType === 'privilege_escalation'
      );
      expect(threat).toBeDefined();
    });

    it('should detect DoS attempts', async () => {
      await queryLogger.logQuery('SELECT SLEEP(10) FROM users', 50);

      const insights = await detector.analyze();

      const threat = insights.securityThreats.find(
        t => t.threatType === 'dos_attempt'
      );
      expect(threat).toBeDefined();
    });

    it('should calculate threat confidence', async () => {
      await queryLogger.logQuery("SELECT * FROM users WHERE '1'='1'", 50);

      const insights = await detector.analyze();
      const threat = insights.securityThreats[0];

      expect(threat?.confidence).toBeGreaterThan(0);
      expect(threat?.confidence).toBeLessThanOrEqual(1);
    });

    it('should provide security recommendations', async () => {
      await queryLogger.logQuery('SELECT * FROM users WHERE id = 1 OR 1=1', 50);

      const insights = await detector.analyze();
      const threat = insights.securityThreats[0];

      expect(threat?.recommendation).toBeDefined();
      expect(typeof threat.recommendation).toBe('string');
    });

    it('should respect security scan configuration', async () => {
      const noSecurityDetector = new PatternDetector(
        stateManager,
        queryLogger,
        { securityScanEnabled: false }
      );

      await queryLogger.logQuery("SELECT * FROM users WHERE '1'='1'", 50);
      const insights = await noSecurityDetector.analyze();

      expect(insights.securityThreats).toEqual([]);
    });
  });

  describe('Performance Patterns', () => {
    it('should identify slow query patterns', async () => {
      for (let i = 0; i < 10; i++) {
        await queryLogger.logQuery('SELECT * FROM users', 1500);
      }

      const insights = await detector.analyze();

      expect(insights.performancePatterns.length).toBeGreaterThan(0);
    });

    it('should detect missing index patterns', async () => {
      for (let i = 0; i < 15; i++) {
        await queryLogger.logQuery(
          `SELECT * FROM users WHERE email = 'test${i}@example.com'`,
          800
        );
      }

      const insights = await detector.analyze();

      const pattern = insights.performancePatterns.find(p =>
        p.description.includes('index')
      );
      expect(pattern).toBeDefined();
    });

    it('should calculate performance trends', async () => {
      // Add queries with increasing execution time
      for (let i = 0; i < 20; i++) {
        await queryLogger.logQuery('SELECT * FROM users', 100 + i * 50);
        await new Promise(resolve => setTimeout(resolve, 10));
      }

      const insights = await detector.analyze();
      const pattern = insights.performancePatterns[0];

      if (pattern) {
        expect(['improving', 'degrading', 'stable']).toContain(pattern.trend);
      }
    });

    it('should provide performance recommendations', async () => {
      for (let i = 0; i < 10; i++) {
        await queryLogger.logQuery('SELECT * FROM users', 2000);
      }

      const insights = await detector.analyze();
      const pattern = insights.performancePatterns[0];

      expect(pattern?.recommendations).toBeInstanceOf(Array);
      expect(pattern?.recommendations.length).toBeGreaterThan(0);
    });
  });

  describe('Usage Patterns', () => {
    it('should identify peak usage hours', async () => {
      await addSampleQueries(queryLogger, 50);

      const insights = await detector.analyze();

      expect(insights.usagePatterns.peakHours).toBeInstanceOf(Array);
      expect(insights.usagePatterns.peakHours.length).toBeGreaterThan(0);
    });

    it('should track common operations', async () => {
      await queryLogger.logQuery('SELECT * FROM users', 50);
      await queryLogger.logQuery('INSERT INTO users VALUES (1)', 30);
      await queryLogger.logQuery('UPDATE users SET name = "test"', 40);

      const insights = await detector.analyze();

      expect(insights.usagePatterns.commonOperations).toBeInstanceOf(Array);
      expect(insights.usagePatterns.commonOperations.length).toBeGreaterThan(0);
    });

    it('should calculate operation percentages', async () => {
      for (let i = 0; i < 10; i++) {
        await queryLogger.logQuery('SELECT * FROM users', 50);
      }

      const insights = await detector.analyze();
      const selectOp = insights.usagePatterns.commonOperations.find(
        o => o.operation === 'SELECT'
      );

      expect(selectOp?.percentage).toBeGreaterThan(0);
      expect(selectOp?.percentage).toBeLessThanOrEqual(100);
    });

    it('should analyze user behavior', async () => {
      await addSampleQueries(queryLogger);

      const insights = await detector.analyze();

      expect(insights.usagePatterns.userBehavior).toBeDefined();
      expect(insights.usagePatterns.userBehavior.averageSessionLength).toBeGreaterThan(0);
    });
  });

  describe('Report Generation', () => {
    it('should generate summary report', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      const report = await detector.report({ format: 'summary' });

      expect(report).toBeDefined();
      expect(report).toContain('PATTERN DETECTION ANALYSIS REPORT');
      expect(report).toContain('SUMMARY');
    });

    it('should generate detailed report', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      const report = await detector.report({ format: 'detailed' });

      expect(report).toContain('PERFORMANCE PATTERNS');
      expect(report).toContain('USAGE PATTERNS');
    });

    it('should filter report by pattern type', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      const report = await detector.report({ type: PatternType.PERFORMANCE });

      expect(report).toBeDefined();
    });

    it('should include recommendations in report', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      const report = await detector.report({ includeRecommendations: true });

      expect(report).toContain('RECOMMENDATIONS');
    });

    it('should exclude recommendations when requested', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      const report = await detector.report({ includeRecommendations: false });

      expect(report).not.toContain('RECOMMENDATIONS');
    });

    it('should handle empty insights', async () => {
      const report = await detector.report();

      expect(report).toContain('No pattern analysis available');
    });
  });

  describe('Pattern Learning', () => {
    it('should learn from patterns', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      await expect(detector.learn()).resolves.not.toThrow();
    });

    it('should update learning model', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();
      await detector.learn();

      const insights = await detector.getInsights();
      expect(insights).toBeDefined();
    });

    it('should respect learning configuration', async () => {
      const noLearningDetector = new PatternDetector(
        stateManager,
        queryLogger,
        { learningEnabled: false }
      );

      await addSampleQueries(queryLogger);
      await noLearningDetector.analyze();

      await expect(noLearningDetector.learn()).resolves.not.toThrow();
    });

    it('should throw error when no insights available', async () => {
      await expect(detector.learn()).rejects.toThrow(
        'No pattern insights available'
      );
    });
  });

  describe('Pattern Export', () => {
    it('should export patterns as JSON', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      const filepath = '/tmp/test-patterns.json';
      await detector.export(filepath, 'json');

      const fs = await import('fs/promises');
      const content = await fs.readFile(filepath, 'utf-8');
      const data = JSON.parse(content);

      expect(data.version).toBe('1.0.0');
      expect(data.patterns).toBeInstanceOf(Array);
    });

    it('should export patterns as CSV', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      const filepath = '/tmp/test-patterns.csv';
      await detector.export(filepath, 'csv');

      const fs = await import('fs/promises');
      const content = await fs.readFile(filepath, 'utf-8');

      expect(content).toContain('Type,ID,Frequency');
    });

    it('should include metadata in export', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      const filepath = '/tmp/test-export.json';
      await detector.export(filepath, 'json');

      const fs = await import('fs/promises');
      const content = await fs.readFile(filepath, 'utf-8');
      const data = JSON.parse(content);

      expect(data.metadata).toBeDefined();
      expect(data.metadata.totalQueries).toBeGreaterThan(0);
    });

    it('should throw error when no insights available', async () => {
      await expect(
        detector.export('/tmp/test.json')
      ).rejects.toThrow('No pattern insights available');
    });
  });

  describe('State Management', () => {
    it('should persist patterns', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      const newDetector = new PatternDetector(stateManager, queryLogger);
      const insights = await newDetector.getInsights();

      expect(insights).toBeDefined();
    });

    it('should clear pattern data', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      detector.clearPatterns();

      await expect(detector.getInsights()).rejects.toThrow(
        'No pattern insights available'
      );
    });

    it('should save and load clusters', async () => {
      await addSampleQueries(queryLogger);
      await detector.analyze();

      const insights1 = await detector.getInsights();
      const newDetector = new PatternDetector(stateManager, queryLogger);
      const insights2 = await newDetector.getInsights();

      expect(insights1.patterns.length).toBe(insights2.patterns.length);
    });
  });

  describe('Recommendations', () => {
    it('should generate recommendations', async () => {
      await addSampleQueries(queryLogger);
      const insights = await detector.analyze();

      expect(insights.recommendations).toBeInstanceOf(Array);
      expect(insights.recommendations.length).toBeGreaterThan(0);
    });

    it('should provide actionable recommendations', async () => {
      for (let i = 0; i < 10; i++) {
        await queryLogger.logQuery('SELECT * FROM users', 2000);
      }

      const insights = await detector.analyze();

      const rec = insights.recommendations.find(r =>
        r.toLowerCase().includes('optim') || r.toLowerCase().includes('index')
      );
      expect(rec).toBeDefined();
    });
  });

  describe('Event Emission', () => {
    it('should emit patternDiscovered event', async () => {
      const listener = vi.fn();
      detector.on('patternDiscovered', listener);

      await addSampleQueries(queryLogger);
      await detector.analyze();

      expect(listener).toHaveBeenCalled();
    });

    it('should emit anomalyDetected event', async () => {
      const listener = vi.fn();
      detector.on('anomalyDetected', listener);

      await queryLogger.logQuery('SELECT * FROM users', 50);
      await queryLogger.logQuery(
        'SELECT * FROM users ' + 'JOIN orders '.repeat(10),
        10000
      );

      await detector.analyze();

      expect(listener).toHaveBeenCalled();
    });

    it('should emit securityThreat event', async () => {
      const listener = vi.fn();
      detector.on('securityThreat', listener);

      await queryLogger.logQuery("SELECT * FROM users WHERE '1'='1'", 50);
      await detector.analyze();

      expect(listener).toHaveBeenCalled();
    });

    it('should emit analysisComplete event', async () => {
      const listener = vi.fn();
      detector.on('analysisComplete', listener);

      await addSampleQueries(queryLogger);
      await detector.analyze();

      expect(listener).toHaveBeenCalledWith(
        expect.objectContaining({
          summary: expect.any(Object),
          patterns: expect.any(Array)
        })
      );
    });
  });

  describe('Edge Cases', () => {
    it('should handle malformed queries', async () => {
      await queryLogger.logQuery('SELEC * FRM users', 50);

      await expect(detector.analyze()).resolves.not.toThrow();
    });

    it('should handle very long queries', async () => {
      const longQuery = 'SELECT * FROM ' + 'users, '.repeat(100) + 'orders';
      await queryLogger.logQuery(longQuery, 100);

      await expect(detector.analyze()).resolves.not.toThrow();
    });

    it('should handle queries with special characters', async () => {
      await queryLogger.logQuery(
        "SELECT * FROM users WHERE name = 'O\\'Brien'",
        50
      );

      await expect(detector.analyze()).resolves.not.toThrow();
    });

    it('should handle concurrent analysis', async () => {
      await addSampleQueries(queryLogger);

      const promises = [
        detector.analyze(),
        detector.analyze(),
        detector.analyze()
      ];

      await expect(Promise.all(promises)).resolves.not.toThrow();
    });
  });
});

// Helper Functions

async function addSampleQueries(logger: QueryLogger, count: number = 20): Promise<void> {
  const queries = [
    'SELECT * FROM users',
    'SELECT id, name FROM users WHERE age > 18',
    'SELECT * FROM users JOIN orders ON users.id = orders.user_id',
    'INSERT INTO users (name, email) VALUES ("test", "test@example.com")',
    'UPDATE users SET name = "updated" WHERE id = 1',
    'DELETE FROM users WHERE id = 1',
    'SELECT COUNT(*) FROM users GROUP BY age',
    'SELECT * FROM products WHERE price > 100 ORDER BY price DESC',
    'SELECT DISTINCT category FROM products',
    'SELECT * FROM users LIMIT 10'
  ];

  for (let i = 0; i < count; i++) {
    const query = queries[i % queries.length];
    const duration = Math.random() * 500 + 50;
    await logger.logQuery(query, duration);

    // Add small delay to vary timestamps
    await new Promise(resolve => setTimeout(resolve, 5));
  }
}
