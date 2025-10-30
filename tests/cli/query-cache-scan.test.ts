/**
 * Tests for Redis SCAN-based query cache implementation
 * Verifies P0 fix: Replace blocking KEYS with non-blocking SCAN
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { QueryCache } from '../../src/cli/query-cache';
import { DatabaseConnectionManager } from '../../src/cli/database-manager';
import { StateManager } from '../../src/core/state-manager';
import Redis from 'ioredis';

// Mock Redis
vi.mock('ioredis');

// Mock dependencies
vi.mock('../../src/cli/database-manager');
vi.mock('../../src/core/state-manager');

describe('QueryCache - SCAN Implementation', () => {
  let queryCache: QueryCache;
  let mockRedis: any;
  let mockDbManager: any;
  let mockStateManager: any;

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();

    // Create mock instances
    mockDbManager = new DatabaseConnectionManager(
      {} as any,
      {} as any
    ) as any;

    mockStateManager = new StateManager({} as any) as any;

    // Mock StateManager.get to return cache config
    mockStateManager.get = vi.fn().mockReturnValue({
      enabled: true,
      ttl: 3600,
      maxSize: 1024 * 1024 * 10,
      invalidationStrategy: 'time',
      autoInvalidateTables: [],
      redisUrl: 'redis://localhost:6379'
    });

    mockStateManager.set = vi.fn();

    // Mock Redis instance
    mockRedis = {
      scan: vi.fn(),
      get: vi.fn(),
      del: vi.fn(),
      ping: vi.fn().mockResolvedValue('PONG'),
      info: vi.fn(),
      on: vi.fn(),
      quit: vi.fn().mockResolvedValue(undefined)
    } as any;

    // Mock Redis constructor
    (Redis as any).mockImplementation(() => mockRedis);

    // Create QueryCache instance
    queryCache = new QueryCache(mockDbManager, mockStateManager);
  });

  afterEach(async () => {
    await queryCache.cleanup();
  });

  describe('scanKeys async generator', () => {
    it('should iterate through all keys using SCAN', async () => {
      // Enable cache and initialize Redis
      await queryCache.enable('redis://localhost:6379');

      // Mock SCAN to return keys in batches
      mockRedis.scan
        .mockResolvedValueOnce(['1', ['query:key1', 'query:key2']])
        .mockResolvedValueOnce(['2', ['query:key3', 'query:key4']])
        .mockResolvedValueOnce(['0', ['query:key5']]); // cursor 0 = done

      // Access private method through any cast for testing
      const cache = queryCache as any;
      const keys: string[] = [];

      for await (const batch of cache.scanKeys('query:*', 100)) {
        keys.push(...batch);
      }

      expect(keys).toEqual([
        'query:key1',
        'query:key2',
        'query:key3',
        'query:key4',
        'query:key5'
      ]);

      expect(mockRedis.scan).toHaveBeenCalledTimes(3);
      expect(mockRedis.scan).toHaveBeenCalledWith('0', 'MATCH', 'query:*', 'COUNT', '100');
      expect(mockRedis.scan).toHaveBeenCalledWith('1', 'MATCH', 'query:*', 'COUNT', '100');
      expect(mockRedis.scan).toHaveBeenCalledWith('2', 'MATCH', 'query:*', 'COUNT', '100');
    });

    it('should handle empty batches', async () => {
      await queryCache.enable('redis://localhost:6379');

      // Mock SCAN to return empty batches
      mockRedis.scan
        .mockResolvedValueOnce(['1', []])
        .mockResolvedValueOnce(['2', ['query:key1']])
        .mockResolvedValueOnce(['0', []]);

      const cache = queryCache as any;
      const keys: string[] = [];

      for await (const batch of cache.scanKeys('query:*', 100)) {
        keys.push(...batch);
      }

      expect(keys).toEqual(['query:key1']);
      expect(mockRedis.scan).toHaveBeenCalledTimes(3);
    });

    it('should use custom count parameter', async () => {
      await queryCache.enable('redis://localhost:6379');

      mockRedis.scan.mockResolvedValueOnce(['0', ['query:key1']]);

      const cache = queryCache as any;
      const keys: string[] = [];

      for await (const batch of cache.scanKeys('query:*', 500)) {
        keys.push(...batch);
      }

      expect(mockRedis.scan).toHaveBeenCalledWith('0', 'MATCH', 'query:*', 'COUNT', '500');
    });
  });

  describe('invalidateTable with SCAN', () => {
    it('should invalidate all entries for a table using SCAN', async () => {
      await queryCache.enable('redis://localhost:6379');

      // Mock SCAN to return keys in batches
      mockRedis.scan
        .mockResolvedValueOnce(['1', ['query:hash1', 'query:hash2']])
        .mockResolvedValueOnce(['0', ['query:hash3']]);

      // Mock metadata retrieval
      mockRedis.get
        .mockResolvedValueOnce(JSON.stringify({ query: 'SELECT * FROM users' }))
        .mockResolvedValueOnce(JSON.stringify({ query: 'SELECT * FROM orders' }))
        .mockResolvedValueOnce(JSON.stringify({ query: 'UPDATE users SET name = ?' }));

      mockRedis.del.mockResolvedValue(1);

      await queryCache.invalidateTable('users');

      // Verify SCAN was used instead of KEYS
      expect(mockRedis.scan).toHaveBeenCalled();

      // Verify batch processing of metadata
      expect(mockRedis.get).toHaveBeenCalledWith('query:hash1:meta');
      expect(mockRedis.get).toHaveBeenCalledWith('query:hash2:meta');
      expect(mockRedis.get).toHaveBeenCalledWith('query:hash3:meta');

      // Verify deletion of matching keys
      expect(mockRedis.del).toHaveBeenCalledWith('query:hash1');
      expect(mockRedis.del).toHaveBeenCalledWith('query:hash1:meta');
      expect(mockRedis.del).toHaveBeenCalledWith('query:hash1:hits');
      expect(mockRedis.del).toHaveBeenCalledWith('query:hash3');
      expect(mockRedis.del).toHaveBeenCalledWith('query:hash3:meta');
      expect(mockRedis.del).toHaveBeenCalledWith('query:hash3:hits');

      // Orders key should NOT be deleted
      expect(mockRedis.del).not.toHaveBeenCalledWith('query:hash2');
    });

    it('should handle malformed metadata gracefully', async () => {
      await queryCache.enable('redis://localhost:6379');

      mockRedis.scan.mockResolvedValueOnce(['0', ['query:hash1', 'query:hash2']]);

      // One valid, one malformed metadata
      mockRedis.get
        .mockResolvedValueOnce(JSON.stringify({ query: 'SELECT * FROM users' }))
        .mockResolvedValueOnce('invalid json');

      mockRedis.del.mockResolvedValue(1);

      await queryCache.invalidateTable('users');

      // Should only delete the valid entry
      expect(mockRedis.del).toHaveBeenCalledWith('query:hash1');
      expect(mockRedis.del).not.toHaveBeenCalledWith('query:hash2');
    });

    it('should handle case-insensitive table names', async () => {
      await queryCache.enable('redis://localhost:6379');

      mockRedis.scan.mockResolvedValueOnce(['0', ['query:hash1']]);
      mockRedis.get.mockResolvedValueOnce(JSON.stringify({ query: 'SELECT * FROM USERS' }));
      mockRedis.del.mockResolvedValue(1);

      await queryCache.invalidateTable('users');

      expect(mockRedis.del).toHaveBeenCalledWith('query:hash1');
    });
  });

  describe('clear with SCAN', () => {
    it('should clear all cache entries using SCAN', async () => {
      await queryCache.enable('redis://localhost:6379');

      // Mock SCAN to return keys in batches
      mockRedis.scan
        .mockResolvedValueOnce(['1', ['query:key1', 'query:key2']])
        .mockResolvedValueOnce(['0', ['query:key3']]);

      mockRedis.del.mockResolvedValue(1);

      await queryCache.clear();

      // Verify SCAN was used
      expect(mockRedis.scan).toHaveBeenCalled();

      // Verify batch deletion
      expect(mockRedis.del).toHaveBeenCalledWith('query:key1', 'query:key2');
      expect(mockRedis.del).toHaveBeenCalledWith('query:key3');
    });

    it('should reset stats after clearing', async () => {
      await queryCache.enable('redis://localhost:6379');

      mockRedis.scan.mockResolvedValueOnce(['0', []]);

      await queryCache.clear();

      const stats = await queryCache.getStats();
      expect(stats.hits).toBe(0);
      expect(stats.misses).toBe(0);
      expect(stats.evictions).toBe(0);
    });
  });

  describe('getStats with SCAN', () => {
    it('should count keys using SCAN instead of KEYS', async () => {
      await queryCache.enable('redis://localhost:6379');

      // Mock SCAN to return keys in batches
      mockRedis.scan
        .mockResolvedValueOnce(['1', ['query:key1', 'query:key2']])
        .mockResolvedValueOnce(['0', ['query:key3']]);

      mockRedis.info.mockResolvedValue('used_memory:1024000');

      const stats = await queryCache.getStats();

      // Verify SCAN was used
      expect(mockRedis.scan).toHaveBeenCalled();

      // Verify total key count
      expect(stats.totalKeys).toBe(3);
      expect(stats.memoryUsed).toBe(1024000);
    });

    it('should handle empty cache', async () => {
      await queryCache.enable('redis://localhost:6379');

      mockRedis.scan.mockResolvedValueOnce(['0', []]);
      mockRedis.info.mockResolvedValue('used_memory:1024');

      const stats = await queryCache.getStats();

      expect(stats.totalKeys).toBe(0);
      expect(stats.memoryUsed).toBe(1024);
    });
  });

  describe('exportCache with SCAN', () => {
    it('should export all entries using SCAN', async () => {
      await queryCache.enable('redis://localhost:6379');

      // Mock SCAN to return keys in batches
      mockRedis.scan
        .mockResolvedValueOnce(['1', ['query:hash1', 'query:hash2']])
        .mockResolvedValueOnce(['0', ['query:hash3']]);

      // Mock data retrieval for each key
      mockRedis.get
        // Batch 1 - key 1
        .mockResolvedValueOnce(JSON.stringify({ rows: [{ id: 1 }] }))
        .mockResolvedValueOnce(JSON.stringify({ query: 'SELECT 1', timestamp: 1000, size: 100 }))
        .mockResolvedValueOnce('5')
        // Batch 1 - key 2
        .mockResolvedValueOnce(JSON.stringify({ rows: [{ id: 2 }] }))
        .mockResolvedValueOnce(JSON.stringify({ query: 'SELECT 2', timestamp: 2000, size: 200 }))
        .mockResolvedValueOnce('10')
        // Batch 2 - key 3
        .mockResolvedValueOnce(JSON.stringify({ rows: [{ id: 3 }] }))
        .mockResolvedValueOnce(JSON.stringify({ query: 'SELECT 3', timestamp: 3000, size: 300 }))
        .mockResolvedValueOnce('15');

      const entries = await queryCache.exportCache();

      expect(entries).toHaveLength(3);
      expect(entries[0].key).toBe('query:hash1');
      expect(entries[0].query).toBe('SELECT 1');
      expect(entries[0].hits).toBe(5);
      expect(entries[1].key).toBe('query:hash2');
      expect(entries[2].key).toBe('query:hash3');

      // Verify SCAN was used
      expect(mockRedis.scan).toHaveBeenCalled();
    });

    it('should skip malformed entries during export', async () => {
      await queryCache.enable('redis://localhost:6379');

      mockRedis.scan.mockResolvedValueOnce(['0', ['query:hash1', 'query:hash2']]);

      // Valid entry for hash1, malformed for hash2
      mockRedis.get
        .mockResolvedValueOnce(JSON.stringify({ rows: [{ id: 1 }] }))
        .mockResolvedValueOnce(JSON.stringify({ query: 'SELECT 1', timestamp: 1000, size: 100 }))
        .mockResolvedValueOnce('5')
        .mockResolvedValueOnce(null) // Missing result
        .mockResolvedValueOnce(JSON.stringify({ query: 'SELECT 2', timestamp: 2000, size: 200 }))
        .mockResolvedValueOnce('10');

      const entries = await queryCache.exportCache();

      expect(entries).toHaveLength(1);
      expect(entries[0].key).toBe('query:hash1');
    });
  });

  describe('Performance characteristics', () => {
    it('should not block Redis with large key sets', async () => {
      await queryCache.enable('redis://localhost:6379');

      // Simulate large dataset with many SCAN iterations
      const mockScanResults: Array<[string, string[]]> = [];
      for (let i = 1; i <= 10; i++) {
        const keys = Array.from({ length: 100 }, (_, j) => `query:key${i * 100 + j}`);
        mockScanResults.push([i.toString(), keys]);
      }
      mockScanResults.push(['0', []]); // Final cursor

      mockScanResults.forEach(result => {
        mockRedis.scan.mockResolvedValueOnce(result);
      });

      mockRedis.del.mockResolvedValue(1);

      const startTime = Date.now();
      await queryCache.clear();
      const duration = Date.now() - startTime;

      // Verify SCAN was called multiple times (non-blocking)
      expect(mockRedis.scan).toHaveBeenCalledTimes(11);

      // Verify batch deletion (more efficient than individual deletes)
      expect(mockRedis.del).toHaveBeenCalledTimes(10);

      // Performance should be reasonable (this is a unit test, so it should be fast)
      expect(duration).toBeLessThan(1000);
    });

    it('should batch Redis operations for efficiency', async () => {
      await queryCache.enable('redis://localhost:6379');

      // Mock large batch
      const keys = Array.from({ length: 100 }, (_, i) => `query:key${i}`);
      mockRedis.scan.mockResolvedValueOnce(['0', keys]);

      // Mock metadata for all keys
      const metaData = keys.map(() => JSON.stringify({ query: 'SELECT * FROM users' }));
      metaData.forEach(meta => {
        mockRedis.get.mockResolvedValueOnce(meta);
      });

      mockRedis.del.mockResolvedValue(1);

      await queryCache.invalidateTable('users');

      // Verify batch fetching of metadata (single Promise.all call)
      expect(mockRedis.get).toHaveBeenCalledTimes(100);

      // Verify batch deletion (should be done in parallel)
      expect(mockRedis.del).toHaveBeenCalledTimes(300); // 100 keys × 3 (key + meta + hits)
    });
  });

  describe('Backward compatibility', () => {
    it('should maintain same API surface', async () => {
      // Verify all public methods still exist and have correct signatures
      expect(typeof queryCache.enable).toBe('function');
      expect(typeof queryCache.disable).toBe('function');
      expect(typeof queryCache.get).toBe('function');
      expect(typeof queryCache.set).toBe('function');
      expect(typeof queryCache.invalidate).toBe('function');
      expect(typeof queryCache.invalidateTable).toBe('function');
      expect(typeof queryCache.clear).toBe('function');
      expect(typeof queryCache.getStats).toBe('function');
      expect(typeof queryCache.exportCache).toBe('function');
    });

    it('should produce same results as KEYS-based implementation', async () => {
      await queryCache.enable('redis://localhost:6379');

      // Mock scenario: invalidate table with mixed queries
      mockRedis.scan.mockResolvedValueOnce(['0', ['query:hash1', 'query:hash2', 'query:hash3']]);

      mockRedis.get
        .mockResolvedValueOnce(JSON.stringify({ query: 'SELECT * FROM users' }))
        .mockResolvedValueOnce(JSON.stringify({ query: 'SELECT * FROM orders' }))
        .mockResolvedValueOnce(JSON.stringify({ query: 'UPDATE users SET active = 1' }));

      mockRedis.del.mockResolvedValue(1);

      await queryCache.invalidateTable('users');

      // Verify same keys are deleted as would be with KEYS
      expect(mockRedis.del).toHaveBeenCalledWith('query:hash1');
      expect(mockRedis.del).toHaveBeenCalledWith('query:hash3');
      expect(mockRedis.del).not.toHaveBeenCalledWith('query:hash2');
    });
  });
});
