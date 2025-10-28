/**
 * Federation Engine Tests
 * Comprehensive test suite for cross-database JOINs
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { FederationEngine } from '../../src/cli/federation-engine';
import { DatabaseConnectionManager, DatabaseType } from '../../src/cli/database-manager';
import { StateManager } from '../../src/core/state-manager';

describe('FederationEngine', () => {
  let engine: FederationEngine;
  let dbManager: DatabaseConnectionManager;
  let stateManager: StateManager;

  beforeEach(() => {
    stateManager = new StateManager();
    dbManager = new DatabaseConnectionManager(stateManager);
    engine = new FederationEngine(dbManager, stateManager);
  });

  afterEach(async () => {
    await dbManager.disconnectAll();
  });

  describe('SQL Parsing', () => {
    it('should parse simple SELECT query', async () => {
      const sql = 'SELECT id, name FROM users';

      // Access private method for testing
      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.type).toBe('SELECT');
      expect(parsed.select).toHaveLength(2);
      expect(parsed.select[0].expression).toBe('id');
      expect(parsed.select[1].expression).toBe('name');
      expect(parsed.from[0].table).toBe('users');
    });

    it('should parse cross-database query', async () => {
      const sql = 'SELECT u.name, o.total FROM db1.users u JOIN db2.orders o ON u.id = o.user_id';

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.type).toBe('SELECT');
      expect(parsed.from[0].database).toBe('db1');
      expect(parsed.from[0].table).toBe('users');
      expect(parsed.joins).toHaveLength(1);
      expect(parsed.joins[0].database).toBe('db2');
      expect(parsed.joins[0].table).toBe('orders');
      expect(parsed.joins[0].type).toBe('INNER');
    });

    it('should parse LEFT JOIN', async () => {
      const sql = 'SELECT * FROM db1.users u LEFT JOIN db2.orders o ON u.id = o.user_id';

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.joins[0].type).toBe('LEFT');
      expect(parsed.joins[0].on.left.table).toBe('u');
      expect(parsed.joins[0].on.left.column).toBe('id');
      expect(parsed.joins[0].on.right.table).toBe('o');
      expect(parsed.joins[0].on.right.column).toBe('user_id');
    });

    it('should parse RIGHT JOIN', async () => {
      const sql = 'SELECT * FROM db1.users u RIGHT JOIN db2.orders o ON u.id = o.user_id';

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.joins[0].type).toBe('RIGHT');
    });

    it('should parse FULL OUTER JOIN', async () => {
      const sql = 'SELECT * FROM db1.users u FULL OUTER JOIN db2.orders o ON u.id = o.user_id';

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.joins[0].type).toBe('FULL');
    });

    it('should parse query with WHERE clause', async () => {
      const sql = "SELECT * FROM db1.users u JOIN db2.orders o ON u.id = o.user_id WHERE o.total > 100";

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.where).toBeDefined();
      expect(parsed.where?.raw).toContain('o . total > 100'); // Tokens are space-separated
    });

    it('should parse query with GROUP BY', async () => {
      const sql = 'SELECT category, COUNT(*) FROM db1.products GROUP BY category';

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.groupBy).toBeDefined();
      expect(parsed.groupBy?.columns).toContain('category');
    });

    it('should parse query with ORDER BY', async () => {
      const sql = 'SELECT * FROM db1.users ORDER BY name ASC, age DESC';

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.orderBy).toBeDefined();
      expect(parsed.orderBy?.columns).toHaveLength(2);
      expect(parsed.orderBy?.columns[0].column).toBe('name');
      expect(parsed.orderBy?.columns[0].direction).toBe('ASC');
      expect(parsed.orderBy?.columns[1].column).toBe('age');
      expect(parsed.orderBy?.columns[1].direction).toBe('DESC');
    });

    it('should parse query with LIMIT and OFFSET', async () => {
      const sql = 'SELECT * FROM db1.users LIMIT 10 OFFSET 20';

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.limit).toBe(10);
      expect(parsed.offset).toBe(20);
    });

    it('should parse aggregate functions', async () => {
      const sql = 'SELECT COUNT(*), SUM(amount), AVG(price) FROM db1.orders';

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.select[0].isAggregate).toBe(true);
      expect(parsed.select[0].aggregateFunction).toBe('COUNT');
      expect(parsed.select[1].aggregateFunction).toBe('SUM');
      expect(parsed.select[2].aggregateFunction).toBe('AVG');
    });

    it('should parse multiple JOINs', async () => {
      const sql = `
        SELECT u.name, o.total, p.name
        FROM db1.users u
        JOIN db2.orders o ON u.id = o.user_id
        JOIN db3.products p ON o.product_id = p.id
      `;

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.joins).toHaveLength(2);
      expect(parsed.joins[0].database).toBe('db2');
      expect(parsed.joins[1].database).toBe('db3');
    });

    it('should parse table aliases', async () => {
      const sql = 'SELECT u.name FROM db1.users AS u';

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.from[0].alias).toBe('u');
    });
  });

  describe('SQL Tokenization', () => {
    it('should tokenize keywords', () => {
      const sql = 'SELECT FROM WHERE';
      const tokens = (engine as any).tokenize(sql);

      expect(tokens[0].type).toBe('KEYWORD');
      expect(tokens[0].value).toBe('SELECT');
      expect(tokens[1].type).toBe('KEYWORD');
      expect(tokens[1].value).toBe('FROM');
      expect(tokens[2].type).toBe('KEYWORD');
      expect(tokens[2].value).toBe('WHERE');
    });

    it('should tokenize identifiers', () => {
      const sql = 'users name id';
      const tokens = (engine as any).tokenize(sql);

      tokens.forEach(token => {
        expect(token.type).toBe('IDENTIFIER');
      });
    });

    it('should tokenize operators', () => {
      const sql = '= != < > <= >=';
      const tokens = (engine as any).tokenize(sql);

      tokens.forEach(token => {
        expect(token.type).toBe('OPERATOR');
      });
    });

    it('should tokenize string literals', () => {
      const sql = "'hello' \"world\"";
      const tokens = (engine as any).tokenize(sql);

      expect(tokens[0].type).toBe('LITERAL');
      expect(tokens[0].value).toBe("'hello'");
      expect(tokens[1].type).toBe('LITERAL');
      expect(tokens[1].value).toBe('"world"');
    });

    it('should tokenize numbers', () => {
      const sql = '123 45.67 0.89';
      const tokens = (engine as any).tokenize(sql);

      tokens.forEach(token => {
        expect(token.type).toBe('LITERAL');
      });
    });

    it('should tokenize punctuation', () => {
      const sql = '(,);.';
      const tokens = (engine as any).tokenize(sql);

      tokens.forEach(token => {
        expect(token.type).toBe('PUNCTUATION');
      });
    });
  });

  describe('Query Validation', () => {
    it('should validate cross-database query', () => {
      // Mock connections
      vi.spyOn(dbManager, 'getConnection').mockImplementation((name) => {
        return {
          config: { name, type: DatabaseType.POSTGRESQL } as any,
          client: {} as any,
          type: DatabaseType.POSTGRESQL,
          isConnected: true
        };
      });

      const parsed = {
        type: 'SELECT' as const,
        select: [],
        from: [{ database: 'db1', table: 'users' }],
        joins: [{ database: 'db2', table: 'orders', type: 'INNER' as const, on: {} as any }]
      };

      expect(() => (engine as any).validateCrossDatabaseQuery(parsed)).not.toThrow();
    });

    it('should reject single-database query', () => {
      const parsed = {
        type: 'SELECT' as const,
        select: [],
        from: [{ database: 'db1', table: 'users' }],
        joins: []
      };

      expect(() => (engine as any).validateCrossDatabaseQuery(parsed)).toThrow('at least 2 databases');
    });

    it('should reject query with non-existent connection', () => {
      vi.spyOn(dbManager, 'getConnection').mockReturnValue(undefined);

      const parsed = {
        type: 'SELECT' as const,
        select: [],
        from: [{ database: 'db1', table: 'users' }],
        joins: [{ database: 'db2', table: 'orders', type: 'INNER' as const, on: {} as any }]
      };

      expect(() => (engine as any).validateCrossDatabaseQuery(parsed)).toThrow('connection not found');
    });
  });

  describe('JOIN Operations', () => {
    it('should perform INNER JOIN', () => {
      const leftData = [
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' },
        { id: 3, name: 'Charlie' }
      ];

      const rightData = [
        { user_id: 1, total: 100 },
        { user_id: 2, total: 200 }
      ];

      const result = (engine as any).performJoin(
        leftData,
        rightData,
        { leftColumn: 'id', rightColumn: 'user_id' },
        'INNER'
      );

      expect(result).toHaveLength(2);
      expect(result[0]).toEqual({ id: 1, name: 'Alice', user_id: 1, total: 100 });
      expect(result[1]).toEqual({ id: 2, name: 'Bob', user_id: 2, total: 200 });
    });

    it('should perform LEFT JOIN', () => {
      const leftData = [
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' },
        { id: 3, name: 'Charlie' }
      ];

      const rightData = [
        { user_id: 1, total: 100 }
      ];

      const result = (engine as any).performJoin(
        leftData,
        rightData,
        { leftColumn: 'id', rightColumn: 'user_id' },
        'LEFT'
      );

      expect(result).toHaveLength(3);
      expect(result[0]).toEqual({ id: 1, name: 'Alice', user_id: 1, total: 100 });
      expect(result[1].id).toBe(2);
      expect(result[1].total).toBeNull();
      expect(result[2].id).toBe(3);
      expect(result[2].total).toBeNull();
    });

    it('should perform RIGHT JOIN', () => {
      const leftData = [
        { id: 1, name: 'Alice' }
      ];

      const rightData = [
        { user_id: 1, total: 100 },
        { user_id: 2, total: 200 },
        { user_id: 3, total: 300 }
      ];

      const result = (engine as any).performJoin(
        leftData,
        rightData,
        { leftColumn: 'id', rightColumn: 'user_id' },
        'RIGHT'
      );

      expect(result).toHaveLength(3);
      expect(result[0]).toEqual({ id: 1, name: 'Alice', user_id: 1, total: 100 });
      expect(result[1].user_id).toBe(2);
      expect(result[1].name).toBeNull();
      expect(result[2].user_id).toBe(3);
      expect(result[2].name).toBeNull();
    });

    it('should perform FULL OUTER JOIN', () => {
      const leftData = [
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' }
      ];

      const rightData = [
        { user_id: 2, total: 200 },
        { user_id: 3, total: 300 }
      ];

      const result = (engine as any).performJoin(
        leftData,
        rightData,
        { leftColumn: 'id', rightColumn: 'user_id' },
        'FULL'
      );

      expect(result).toHaveLength(3);
      expect(result.some(r => r.id === 1 && r.total === null)).toBe(true);
      expect(result.some(r => r.id === 2 && r.total === 200)).toBe(true);
      expect(result.some(r => r.id === null && r.user_id === 3)).toBe(true);
    });

    it('should handle one-to-many relationships', () => {
      const leftData = [
        { id: 1, name: 'Alice' }
      ];

      const rightData = [
        { user_id: 1, total: 100 },
        { user_id: 1, total: 200 },
        { user_id: 1, total: 300 }
      ];

      const result = (engine as any).performJoin(
        leftData,
        rightData,
        { leftColumn: 'id', rightColumn: 'user_id' },
        'INNER'
      );

      expect(result).toHaveLength(3);
      result.forEach(row => {
        expect(row.id).toBe(1);
        expect(row.name).toBe('Alice');
      });
    });

    it('should handle empty result sets', () => {
      const leftData: any[] = [];
      const rightData = [{ user_id: 1, total: 100 }];

      const result = (engine as any).performJoin(
        leftData,
        rightData,
        { leftColumn: 'id', rightColumn: 'user_id' },
        'INNER'
      );

      expect(result).toHaveLength(0);
    });
  });

  describe('Aggregate Operations', () => {
    it('should perform GROUP BY aggregation', async () => {
      const inputData = [
        { category: 'A', value: 10 },
        { category: 'A', value: 20 },
        { category: 'B', value: 30 },
        { category: 'B', value: 40 }
      ];

      const step = {
        id: 'aggregate',
        type: 'aggregate' as const,
        operation: 'GROUP BY category',
        dependencies: ['input'],
        estimatedRows: 2,
        estimatedCost: 1
      };

      const intermediateResults = new Map([['input', inputData]]);
      const result = await (engine as any).executeAggregate(step, intermediateResults);

      expect(result).toHaveLength(2);
      expect(result[0].category).toBe('A');
      expect(result[0].count_value).toBe(2);
      expect(result[0].sum_value).toBe(30);
      expect(result[0].avg_value).toBe(15);
      expect(result[1].category).toBe('B');
      expect(result[1].sum_value).toBe(70);
    });

    it('should calculate MIN and MAX', async () => {
      const inputData = [
        { group: '1', value: 5 },
        { group: '1', value: 15 },
        { group: '1', value: 10 }
      ];

      const step = {
        id: 'aggregate',
        type: 'aggregate' as const,
        operation: 'GROUP BY group',
        dependencies: ['input'],
        estimatedRows: 1,
        estimatedCost: 1
      };

      const intermediateResults = new Map([['input', inputData]]);
      const result = await (engine as any).executeAggregate(step, intermediateResults);

      expect(result[0].min_value).toBe(5);
      expect(result[0].max_value).toBe(15);
    });
  });

  describe('Sorting and Limiting', () => {
    it('should sort by single column ASC', async () => {
      const inputData = [
        { name: 'Charlie', age: 30 },
        { name: 'Alice', age: 25 },
        { name: 'Bob', age: 35 }
      ];

      const step = {
        id: 'sort',
        type: 'sort' as const,
        operation: 'ORDER BY name ASC',
        dependencies: ['input'],
        estimatedRows: 3,
        estimatedCost: 0.1
      };

      const intermediateResults = new Map([['input', inputData]]);
      const result = await (engine as any).executeSort(step, intermediateResults);

      expect(result[0].name).toBe('Alice');
      expect(result[1].name).toBe('Bob');
      expect(result[2].name).toBe('Charlie');
    });

    it('should sort by single column DESC', async () => {
      const inputData = [
        { name: 'Alice', age: 25 },
        { name: 'Bob', age: 35 },
        { name: 'Charlie', age: 30 }
      ];

      const step = {
        id: 'sort',
        type: 'sort' as const,
        operation: 'ORDER BY age DESC',
        dependencies: ['input'],
        estimatedRows: 3,
        estimatedCost: 0.1
      };

      const intermediateResults = new Map([['input', inputData]]);
      const result = await (engine as any).executeSort(step, intermediateResults);

      expect(result[0].age).toBe(35);
      expect(result[1].age).toBe(30);
      expect(result[2].age).toBe(25);
    });

    it('should sort by multiple columns', async () => {
      const inputData = [
        { category: 'A', value: 20 },
        { category: 'B', value: 10 },
        { category: 'A', value: 10 }
      ];

      const step = {
        id: 'sort',
        type: 'sort' as const,
        operation: 'ORDER BY category ASC, value DESC',
        dependencies: ['input'],
        estimatedRows: 3,
        estimatedCost: 0.1
      };

      const intermediateResults = new Map([['input', inputData]]);
      const result = await (engine as any).executeSort(step, intermediateResults);

      expect(result[0]).toEqual({ category: 'A', value: 20 });
      expect(result[1]).toEqual({ category: 'A', value: 10 });
      expect(result[2]).toEqual({ category: 'B', value: 10 });
    });

    it('should apply LIMIT', async () => {
      const inputData = Array.from({ length: 100 }, (_, i) => ({ id: i }));

      const step = {
        id: 'limit',
        type: 'limit' as const,
        operation: 'LIMIT 10',
        dependencies: ['input'],
        estimatedRows: 10,
        estimatedCost: 0.01
      };

      const intermediateResults = new Map([['input', inputData]]);
      const result = await (engine as any).executeLimit(step, intermediateResults);

      expect(result).toHaveLength(10);
    });

    it('should apply LIMIT with OFFSET', async () => {
      const inputData = Array.from({ length: 100 }, (_, i) => ({ id: i }));

      const step = {
        id: 'limit',
        type: 'limit' as const,
        operation: 'LIMIT 10 OFFSET 20',
        dependencies: ['input'],
        estimatedRows: 10,
        estimatedCost: 0.01
      };

      const intermediateResults = new Map([['input', inputData]]);
      const result = await (engine as any).executeLimit(step, intermediateResults);

      expect(result).toHaveLength(10);
      expect(result[0].id).toBe(20);
      expect(result[9].id).toBe(29);
    });
  });

  describe('Query Explanation', () => {
    it('should generate execution plan explanation', async () => {
      const sql = 'SELECT u.name, o.total FROM db1.users u JOIN db2.orders o ON u.id = o.user_id';

      // Mock connections
      vi.spyOn(dbManager, 'getConnection').mockImplementation((name) => ({
        config: { name, type: DatabaseType.POSTGRESQL } as any,
        client: {} as any,
        type: DatabaseType.POSTGRESQL,
        isConnected: true
      }));

      // Mock estimateTableSize
      vi.spyOn(engine as any, 'estimateTableSize').mockResolvedValue({
        rowCount: 1000,
        sizeBytes: 100000
      });

      const explanation = await engine.explainQuery(sql);

      expect(explanation).toContain('FEDERATED QUERY EXECUTION PLAN');
      expect(explanation).toContain('Strategy:');
      expect(explanation).toContain('Estimated Cost:');
      expect(explanation).toContain('Databases:');
    });
  });

  describe('Statistics', () => {
    it('should track query statistics', () => {
      const stats = engine.getStatistics();

      expect(stats).toHaveProperty('totalDataTransferred');
      expect(stats).toHaveProperty('queriesExecuted');
      expect(stats).toHaveProperty('cacheHits');
      expect(stats).toHaveProperty('cacheMisses');
      expect(stats).toHaveProperty('databases');
    });

    it('should reset statistics', () => {
      engine.resetStatistics();
      const stats = engine.getStatistics();

      expect(stats.totalDataTransferred).toBe(0);
      expect(stats.queriesExecuted).toBe(0);
      expect(stats.cacheHits).toBe(0);
      expect(stats.cacheMisses).toBe(0);
    });
  });

  describe('Caching', () => {
    it('should clear caches', () => {
      expect(() => engine.clearCaches()).not.toThrow();
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid SQL syntax', () => {
      const sql = 'SELECT FROM';

      expect(() => (engine as any).parseSQL(sql)).toThrow();
    });

    it('should handle missing JOIN condition', () => {
      const sql = 'SELECT * FROM db1.users u JOIN db2.orders o';

      expect(() => (engine as any).parseSQL(sql)).toThrow();
    });

    it('should handle circular dependencies in execution plan', async () => {
      const plan = {
        id: 'plan-1',
        query: '',
        databases: ['db1', 'db2'],
        steps: [
          {
            id: 'step-1',
            type: 'fetch' as const,
            dependencies: ['step-2'],
            estimatedRows: 100,
            estimatedCost: 1
          },
          {
            id: 'step-2',
            type: 'fetch' as const,
            dependencies: ['step-1'],
            estimatedRows: 100,
            estimatedCost: 1
          }
        ],
        estimatedCost: 2,
        strategy: 'nested-loop' as const,
        createdAt: Date.now()
      };

      await expect((engine as any).executePlan(plan)).rejects.toThrow('Circular dependency');
    });
  });

  describe('Performance', () => {
    it('should handle large result sets efficiently', () => {
      const leftData = Array.from({ length: 10000 }, (_, i) => ({ id: i, name: `User${i}` }));
      const rightData = Array.from({ length: 10000 }, (_, i) => ({ user_id: i, value: i * 10 }));

      const startTime = Date.now();
      const result = (engine as any).performJoin(
        leftData,
        rightData,
        { leftColumn: 'id', rightColumn: 'user_id' },
        'INNER'
      );
      const duration = Date.now() - startTime;

      expect(result).toHaveLength(10000);
      expect(duration).toBeLessThan(1000); // Should complete in less than 1 second
    });

    it('should handle complex multi-table JOINs', async () => {
      const sql = `
        SELECT u.name, o.total, p.name, c.name
        FROM db1.users u
        JOIN db2.orders o ON u.id = o.user_id
        JOIN db3.products p ON o.product_id = p.id
        JOIN db4.categories c ON p.category_id = c.id
        WHERE o.total > 100
        ORDER BY o.total DESC
        LIMIT 10
      `;

      // Mock connections
      vi.spyOn(dbManager, 'getConnection').mockImplementation((name) => ({
        config: { name, type: DatabaseType.POSTGRESQL } as any,
        client: {} as any,
        type: DatabaseType.POSTGRESQL,
        isConnected: true
      }));

      const parsed = (engine as any).parseSQL(sql);

      expect(parsed.joins).toHaveLength(3);
      expect(parsed.where).toBeDefined();
      expect(parsed.orderBy).toBeDefined();
      expect(parsed.limit).toBe(10);
    });
  });
});
