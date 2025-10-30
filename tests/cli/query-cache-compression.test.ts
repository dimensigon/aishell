/**
 * Query Cache Compression Tests
 * Tests for gzip compression feature in query caching
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { QueryCache } from '../../src/cli/query-cache';
import { DatabaseConnectionManager } from '../../src/cli/database-manager';
import { StateManager } from '../../src/core/state-manager';
import Redis from 'ioredis';
import { promisify } from 'util';
import { gzip, gunzip } from 'zlib';

const gzipAsync = promisify(gzip);
const gunzipAsync = promisify(gunzip);

// Mock dependencies
vi.mock('ioredis');
vi.mock('../../src/core/logger', () => ({
  createLogger: () => ({
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn()
  })
}));

describe('QueryCache Compression', () => {
  let queryCache: QueryCache;
  let mockRedis: any;
  let mockDbManager: any;
  let mockStateManager: any;

  beforeEach(() => {
    // Setup mocks
    mockRedis = {
      ping: vi.fn().mockResolvedValue('PONG'),
      get: vi.fn(),
      set: vi.fn(),
      setex: vi.fn(),
      incr: vi.fn(),
      del: vi.fn(),
      scan: vi.fn(),
      info: vi.fn(),
      quit: vi.fn(),
      on: vi.fn()
    };

    vi.mocked(Redis).mockImplementation(() => mockRedis);

    mockDbManager = {
      getActive: vi.fn().mockReturnValue({
        config: { database: 'test-db' }
      })
    };

    mockStateManager = {
      get: vi.fn().mockReturnValue({
        enabled: true,
        ttl: 3600,
        maxSize: 1024 * 1024 * 10,
        invalidationStrategy: 'time',
        autoInvalidateTables: [],
        compressionEnabled: true,
        compressionThreshold: 1024,
        compressionLevel: 6
      }),
      set: vi.fn()
    };

    queryCache = new QueryCache(mockDbManager, mockStateManager);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Compression Configuration', () => {
    it('should have compression enabled by default', () => {
      const config = queryCache.getConfig();
      expect(config.compressionEnabled).toBe(true);
      expect(config.compressionThreshold).toBe(1024);
      expect(config.compressionLevel).toBe(6);
    });

    it('should allow configuring compression settings', () => {
      queryCache.configure({
        compressionEnabled: false,
        compressionThreshold: 2048,
        compressionLevel: 9
      });

      const config = queryCache.getConfig();
      expect(config.compressionEnabled).toBe(false);
      expect(config.compressionThreshold).toBe(2048);
      expect(config.compressionLevel).toBe(9);
    });
  });

  describe('Compression Logic', () => {
    it('should compress data larger than threshold', async () => {
      await queryCache.enable();

      // Create large result (> 1KB)
      const largeResult = {
        rows: Array(100).fill(null).map((_, i) => ({
          id: i,
          name: `User ${i}`,
          email: `user${i}@example.com`,
          description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. '.repeat(10)
        }))
      };

      const query = 'SELECT * FROM users';
      const serialized = JSON.stringify(largeResult);
      const originalSize = serialized.length;

      expect(originalSize).toBeGreaterThan(1024);

      mockRedis.setex.mockResolvedValue('OK');
      mockRedis.set.mockResolvedValue('OK');

      await queryCache.set(query, undefined, largeResult);

      // Verify compression was attempted
      expect(mockRedis.setex).toHaveBeenCalled();
      const [, , compressedData] = mockRedis.setex.mock.calls[0];

      // Compressed data should be base64 encoded
      expect(typeof compressedData).toBe('string');

      // Verify metadata includes compression info
      expect(mockRedis.set).toHaveBeenCalledWith(
        expect.stringContaining(':meta'),
        expect.stringContaining('"compressed":true'),
        'EX',
        3600
      );
    });

    it('should not compress data smaller than threshold', async () => {
      await queryCache.enable();

      // Create small result (< 1KB)
      const smallResult = {
        rows: [{ id: 1, name: 'User 1' }]
      };

      const query = 'SELECT * FROM users WHERE id = 1';
      const serialized = JSON.stringify(smallResult);
      const originalSize = serialized.length;

      expect(originalSize).toBeLessThan(1024);

      mockRedis.setex.mockResolvedValue('OK');
      mockRedis.set.mockResolvedValue('OK');

      await queryCache.set(query, undefined, smallResult);

      // Verify data is stored uncompressed
      expect(mockRedis.setex).toHaveBeenCalledWith(
        expect.any(String),
        3600,
        serialized
      );

      // Verify metadata indicates no compression
      expect(mockRedis.set).toHaveBeenCalledWith(
        expect.stringContaining(':meta'),
        expect.stringContaining('"compressed":false'),
        'EX',
        3600
      );
    });

    it('should achieve 60-80% compression ratio for text-heavy data', async () => {
      await queryCache.enable();

      // Create text-heavy result
      const textHeavyResult = {
        rows: Array(50).fill(null).map((_, i) => ({
          id: i,
          content: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. '.repeat(20),
          title: 'Sample Title with Repeated Text ',
          description: 'This is a description with lots of repeated words and patterns. '.repeat(10)
        }))
      };

      const serialized = JSON.stringify(textHeavyResult);
      const originalSize = serialized.length;

      // Manually compress to verify ratio
      const compressed = await gzipAsync(serialized, { level: 6 });
      const compressedSize = compressed.length;
      const compressionRatio = (compressedSize / originalSize) * 100;

      // Should achieve 20-40% of original size (60-80% savings)
      expect(compressionRatio).toBeLessThan(40);
      expect(compressionRatio).toBeGreaterThan(15);

      console.log(`Compression ratio: ${compressionRatio.toFixed(1)}%`);
      console.log(`Original size: ${originalSize} bytes`);
      console.log(`Compressed size: ${compressedSize} bytes`);
      console.log(`Savings: ${((1 - compressionRatio / 100) * 100).toFixed(1)}%`);
    });
  });

  describe('Decompression Logic', () => {
    it('should decompress compressed data on retrieval', async () => {
      await queryCache.enable();

      const originalData = {
        rows: Array(100).fill(null).map((_, i) => ({
          id: i,
          name: `User ${i}`,
          data: 'Lorem ipsum dolor sit amet. '.repeat(20)
        }))
      };

      const query = 'SELECT * FROM users';
      const serialized = JSON.stringify(originalData);

      // Compress the data
      const compressed = await gzipAsync(serialized, { level: 6 });
      const base64Compressed = compressed.toString('base64');

      // Mock Redis responses
      mockRedis.get.mockImplementation((key: string) => {
        if (key.endsWith(':meta')) {
          return Promise.resolve(JSON.stringify({
            query: query.substring(0, 500),
            timestamp: Date.now(),
            size: serialized.length,
            compressed: true,
            compressedSize: compressed.length,
            originalSize: serialized.length
          }));
        }
        return Promise.resolve(base64Compressed);
      });

      mockRedis.incr.mockResolvedValue(1);

      // Retrieve and verify
      const result = await queryCache.get(query);

      expect(result).toEqual(originalData);
      expect(mockRedis.get).toHaveBeenCalledTimes(2); // data + meta
    });

    it('should handle decompression errors gracefully', async () => {
      await queryCache.enable();

      const query = 'SELECT * FROM users';

      // Mock corrupted compressed data
      mockRedis.get.mockImplementation((key: string) => {
        if (key.endsWith(':meta')) {
          return Promise.resolve(JSON.stringify({
            compressed: true,
            originalSize: 1000
          }));
        }
        // Return invalid base64/compressed data
        return Promise.resolve('invalid-compressed-data');
      });

      const result = await queryCache.get(query);

      // Should return null on decompression error
      expect(result).toBeNull();
    });
  });

  describe('Backward Compatibility', () => {
    it('should read uncompressed data stored before compression feature', async () => {
      await queryCache.enable();

      const oldData = { rows: [{ id: 1, name: 'Old User' }] };
      const query = 'SELECT * FROM old_table';

      // Mock old-style uncompressed data (no compression metadata)
      mockRedis.get.mockImplementation((key: string) => {
        if (key.endsWith(':meta')) {
          return Promise.resolve(JSON.stringify({
            query: query.substring(0, 500),
            timestamp: Date.now(),
            size: JSON.stringify(oldData).length
            // No 'compressed' field - old format
          }));
        }
        return Promise.resolve(JSON.stringify(oldData));
      });

      mockRedis.incr.mockResolvedValue(1);

      const result = await queryCache.get(query);

      expect(result).toEqual(oldData);
    });

    it('should handle missing metadata gracefully', async () => {
      await queryCache.enable();

      const data = { rows: [{ id: 1 }] };
      const query = 'SELECT * FROM table';

      // Mock missing metadata
      mockRedis.get.mockImplementation((key: string) => {
        if (key.endsWith(':meta')) {
          return Promise.resolve(null);
        }
        return Promise.resolve(JSON.stringify(data));
      });

      mockRedis.incr.mockResolvedValue(1);

      const result = await queryCache.get(query);

      expect(result).toEqual(data);
    });
  });

  describe('Compression Statistics', () => {
    it('should track compression statistics', async () => {
      await queryCache.enable();

      // Store multiple compressed entries
      const largeResults = Array(5).fill(null).map((_, i) => ({
        rows: Array(50).fill(null).map((_, j) => ({
          id: j,
          data: `Data ${j} `.repeat(100)
        }))
      }));

      mockRedis.setex.mockResolvedValue('OK');
      mockRedis.set.mockResolvedValue('OK');

      for (let i = 0; i < largeResults.length; i++) {
        await queryCache.set(`SELECT * FROM table${i}`, undefined, largeResults[i]);
      }

      // Mock stats retrieval
      mockRedis.scan.mockResolvedValue(['0', []]);
      mockRedis.info.mockResolvedValue('used_memory:1000000');

      const stats = await queryCache.getStats();

      expect(stats.compressionStats).toBeDefined();
      expect(stats.compressionStats!.compressedEntries).toBe(5);
      expect(stats.compressionStats!.totalOriginalSize).toBeGreaterThan(0);
      expect(stats.compressionStats!.totalCompressedSize).toBeGreaterThan(0);
      expect(stats.compressionStats!.averageCompressionRatio).toBeLessThan(100);
      expect(stats.compressionStats!.memoryByteSavings).toBeGreaterThan(0);
    });

    it('should not show compression stats if no entries compressed', async () => {
      await queryCache.enable();

      mockRedis.scan.mockResolvedValue(['0', []]);
      mockRedis.info.mockResolvedValue('used_memory:1000000');

      const stats = await queryCache.getStats();

      expect(stats.compressionStats).toBeUndefined();
    });

    it('should reset compression stats on clear', async () => {
      await queryCache.enable();

      // Add some compressed entries
      const largeResult = {
        rows: Array(100).fill(null).map((_, i) => ({ id: i, data: 'x'.repeat(100) }))
      };

      mockRedis.setex.mockResolvedValue('OK');
      mockRedis.set.mockResolvedValue('OK');

      await queryCache.set('SELECT * FROM users', undefined, largeResult);

      // Clear cache
      mockRedis.scan.mockResolvedValue(['0', ['query:test']]);
      mockRedis.del.mockResolvedValue(1);
      mockRedis.info.mockResolvedValue('used_memory:0');

      await queryCache.clear();

      const stats = await queryCache.getStats();
      expect(stats.compressionStats).toBeUndefined();
    });
  });

  describe('Performance', () => {
    it('should compress and decompress within 10ms performance target', async () => {
      await queryCache.enable();

      const largeResult = {
        rows: Array(100).fill(null).map((_, i) => ({
          id: i,
          name: `User ${i}`,
          email: `user${i}@example.com`,
          data: 'Lorem ipsum dolor sit amet. '.repeat(50)
        }))
      };

      const query = 'SELECT * FROM users';
      const serialized = JSON.stringify(largeResult);

      // Measure compression time
      const compressStart = Date.now();
      const compressed = await gzipAsync(serialized, { level: 6 });
      const compressTime = Date.now() - compressStart;

      // Measure decompression time
      const decompressStart = Date.now();
      const decompressed = await gunzipAsync(compressed);
      const decompressTime = Date.now() - decompressStart;

      console.log(`Compression time: ${compressTime}ms`);
      console.log(`Decompression time: ${decompressTime}ms`);

      // Should be well under 10ms for typical query results
      expect(compressTime).toBeLessThan(10);
      expect(decompressTime).toBeLessThan(10);

      // Verify data integrity
      expect(decompressed.toString('utf-8')).toBe(serialized);
    });

    it('should handle different compression levels', async () => {
      const testData = {
        rows: Array(100).fill(null).map((_, i) => ({
          id: i,
          data: 'Test data with some repetition. '.repeat(20)
        }))
      };

      const serialized = JSON.stringify(testData);

      // Test compression levels 1-9
      const results = [];

      for (let level = 1; level <= 9; level++) {
        const start = Date.now();
        const compressed = await gzipAsync(serialized, { level });
        const time = Date.now() - start;

        results.push({
          level,
          size: compressed.length,
          time,
          ratio: (compressed.length / serialized.length * 100).toFixed(1)
        });
      }

      // Level 6 should provide good balance
      const level6 = results.find(r => r.level === 6)!;

      console.log('Compression level comparison:');
      results.forEach(r => {
        console.log(`Level ${r.level}: ${r.size} bytes (${r.ratio}%) in ${r.time}ms`);
      });

      // Level 6 should be reasonably fast and effective
      expect(level6.time).toBeLessThan(10);
      expect(parseFloat(level6.ratio)).toBeLessThan(50);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty results', async () => {
      await queryCache.enable();

      const emptyResult = { rows: [] };
      const query = 'SELECT * FROM users WHERE id = -1';

      mockRedis.setex.mockResolvedValue('OK');
      mockRedis.set.mockResolvedValue('OK');

      await queryCache.set(query, undefined, emptyResult);

      // Should not compress (below threshold)
      expect(mockRedis.setex).toHaveBeenCalledWith(
        expect.any(String),
        3600,
        JSON.stringify(emptyResult)
      );
    });

    it('should handle very large results at max size', async () => {
      await queryCache.enable();

      // Create result just under max size (10MB)
      const maxSizeResult = {
        rows: Array(10000).fill(null).map((_, i) => ({
          id: i,
          data: 'x'.repeat(1000)
        }))
      };

      const serialized = JSON.stringify(maxSizeResult);
      const size = serialized.length;

      // Adjust to be just under max size
      if (size > 10 * 1024 * 1024) {
        maxSizeResult.rows = maxSizeResult.rows.slice(0, 5000);
      }

      mockRedis.setex.mockResolvedValue('OK');
      mockRedis.set.mockResolvedValue('OK');

      await queryCache.set('SELECT * FROM huge_table', undefined, maxSizeResult);

      expect(mockRedis.setex).toHaveBeenCalled();
    });

    it('should skip compression when disabled', async () => {
      queryCache.configure({ compressionEnabled: false });
      await queryCache.enable();

      const largeResult = {
        rows: Array(100).fill(null).map((_, i) => ({
          id: i,
          data: 'x'.repeat(100)
        }))
      };

      const query = 'SELECT * FROM users';
      const serialized = JSON.stringify(largeResult);

      mockRedis.setex.mockResolvedValue('OK');
      mockRedis.set.mockResolvedValue('OK');

      await queryCache.set(query, undefined, largeResult);

      // Should store uncompressed
      expect(mockRedis.setex).toHaveBeenCalledWith(
        expect.any(String),
        3600,
        serialized
      );

      // Verify metadata indicates no compression
      expect(mockRedis.set).toHaveBeenCalledWith(
        expect.stringContaining(':meta'),
        expect.stringContaining('"compressed":false'),
        'EX',
        3600
      );
    });

    it('should handle compression threshold edge case', async () => {
      await queryCache.enable();

      // Create result exactly at threshold (1024 bytes)
      let testResult = { rows: [{ data: '' }] };
      let serialized = JSON.stringify(testResult);

      // Adjust to be exactly at threshold
      const targetSize = 1024;
      const currentSize = serialized.length;
      const padding = 'x'.repeat(Math.max(0, targetSize - currentSize - 10));
      testResult.rows[0].data = padding;

      serialized = JSON.stringify(testResult);
      const size = serialized.length;

      expect(size).toBeGreaterThanOrEqual(1024);

      mockRedis.setex.mockResolvedValue('OK');
      mockRedis.set.mockResolvedValue('OK');

      await queryCache.set('SELECT * FROM threshold_test', undefined, testResult);

      expect(mockRedis.setex).toHaveBeenCalled();
    });
  });

  describe('Integration with Cache Operations', () => {
    it('should maintain compression through cache invalidation', async () => {
      await queryCache.enable();

      const largeResult = {
        rows: Array(100).fill(null).map((_, i) => ({ id: i, data: 'x'.repeat(100) }))
      };

      mockRedis.setex.mockResolvedValue('OK');
      mockRedis.set.mockResolvedValue('OK');
      mockRedis.del.mockResolvedValue(1);

      // Set and invalidate
      await queryCache.set('SELECT * FROM users', undefined, largeResult);
      await queryCache.invalidate('SELECT * FROM users');

      expect(mockRedis.del).toHaveBeenCalledTimes(3); // key, meta, hits
    });

    it('should handle compression with query parameters', async () => {
      await queryCache.enable();

      const result = {
        rows: Array(50).fill(null).map((_, i) => ({ id: i, data: 'x'.repeat(100) }))
      };

      const query = 'SELECT * FROM users WHERE id = ?';
      const params = [42];

      mockRedis.setex.mockResolvedValue('OK');
      mockRedis.set.mockResolvedValue('OK');

      await queryCache.set(query, params, result);

      expect(mockRedis.setex).toHaveBeenCalled();
      expect(mockRedis.set).toHaveBeenCalledWith(
        expect.stringContaining(':meta'),
        expect.stringContaining('"compressed":true'),
        'EX',
        3600
      );
    });
  });
});
