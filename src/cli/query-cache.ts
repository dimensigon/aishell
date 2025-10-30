/**
 * Query Cache
 * Redis-based query caching with smart invalidation
 * Commands: ai-shell cache enable, ai-shell cache stats, ai-shell cache clear
 */

import { DatabaseConnectionManager } from './database-manager';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';
import Redis from 'ioredis';
import crypto from 'crypto';
import { promisify } from 'util';
import { gzip, gunzip } from 'zlib';

const gzipAsync = promisify(gzip);
const gunzipAsync = promisify(gunzip);

interface CacheConfig {
  enabled: boolean;
  ttl: number; // seconds
  maxSize: number; // bytes
  redisUrl?: string;
  invalidationStrategy: 'time' | 'manual' | 'smart';
  autoInvalidateTables: string[];
  compressionEnabled: boolean;
  compressionThreshold: number; // bytes, default 1024
  compressionLevel: number; // 1-9, default 6
}

interface CacheStats {
  hits: number;
  misses: number;
  hitRate: number;
  totalKeys: number;
  memoryUsed: number;
  evictions: number;
  compressionStats?: {
    compressedEntries: number;
    totalOriginalSize: number;
    totalCompressedSize: number;
    averageCompressionRatio: number;
    memoryByteSavings: number;
  };
}

interface CacheEntry {
  key: string;
  query: string;
  result: any;
  timestamp: number;
  ttl: number;
  size: number;
  hits: number;
}

export class QueryCache {
  private logger = createLogger('QueryCache');
  private redis: Redis | null = null;
  private config: CacheConfig;
  private stats = {
    hits: 0,
    misses: 0,
    evictions: 0
  };
  private compressionStats = {
    compressedEntries: 0,
    totalOriginalSize: 0,
    totalCompressedSize: 0
  };
  private localCache = new Map<string, CacheEntry>();

  constructor(
    private dbManager: DatabaseConnectionManager,
    private stateManager: StateManager
  ) {
    this.config = this.loadConfig();

    if (this.config.enabled) {
      this.initializeRedis();
    }
  }

  /**
   * Initialize Redis connection
   */
  private async initializeRedis(): Promise<void> {
    try {
      const redisUrl = this.config.redisUrl || 'redis://localhost:6379';

      this.redis = new Redis(redisUrl, {
        maxRetriesPerRequest: 3,
        retryStrategy: (times) => {
          if (times > 3) {
            this.logger.error('Redis connection failed after 3 retries');
            return null;
          }
          return Math.min(times * 200, 2000);
        }
      });

      this.redis.on('error', (error) => {
        this.logger.error('Redis error', error);
        this.fallbackToLocalCache();
      });

      this.redis.on('connect', () => {
        this.logger.info('Redis connected successfully');
      });

      await this.redis.ping();
    } catch (error) {
      this.logger.error('Failed to initialize Redis', error);
      this.fallbackToLocalCache();
    }
  }

  /**
   * Fallback to local in-memory cache
   */
  private fallbackToLocalCache(): void {
    this.logger.warn('Falling back to local in-memory cache');
    this.redis = null;
  }

  /**
   * Enable caching
   */
  async enable(redisUrl?: string): Promise<void> {
    if (redisUrl) {
      this.config.redisUrl = redisUrl;
    }

    this.config.enabled = true;
    this.saveConfig();

    if (!this.redis) {
      await this.initializeRedis();
    }

    this.logger.info('Query caching enabled');
  }

  /**
   * Disable caching
   */
  async disable(): Promise<void> {
    this.config.enabled = false;
    this.saveConfig();

    if (this.redis) {
      await this.redis.quit();
      this.redis = null;
    }

    this.localCache.clear();

    this.logger.info('Query caching disabled');
  }

  /**
   * Get cached query result
   */
  async get(query: string, params?: any[]): Promise<any | null> {
    if (!this.config.enabled) {
      return null;
    }

    const key = this.generateCacheKey(query, params);

    try {
      let result: any = null;

      if (this.redis) {
        const cached = await this.redis.get(key);
        if (cached) {
          const meta = await this.redis.get(`${key}:meta`);
          const metaData = meta ? JSON.parse(meta) : { compressed: false };

          // Decompress if needed
          if (metaData.compressed) {
            try {
              const buffer = Buffer.from(cached, 'base64');
              const decompressed = await gunzipAsync(buffer);
              result = JSON.parse(decompressed.toString('utf-8'));

              this.logger.debug('Decompressed cache entry', {
                key,
                compressedSize: buffer.length,
                originalSize: metaData.originalSize
              });
            } catch (error) {
              this.logger.error('Failed to decompress cache entry', error);
              // Try to parse as uncompressed data (backward compatibility)
              result = JSON.parse(cached);
            }
          } else {
            result = JSON.parse(cached);
          }

          await this.redis.incr(`${key}:hits`);
        }
      } else {
        const entry = this.localCache.get(key);
        if (entry && !this.isExpired(entry)) {
          result = entry.result;
          entry.hits++;
        }
      }

      if (result) {
        this.stats.hits++;
        this.logger.debug('Cache hit', { key, query: query.substring(0, 100) });
        return result;
      } else {
        this.stats.misses++;
        this.logger.debug('Cache miss', { key, query: query.substring(0, 100) });
        return null;
      }
    } catch (error) {
      this.logger.error('Failed to get from cache', error);
      return null;
    }
  }

  /**
   * Set cached query result
   */
  async set(query: string, params: any[] | undefined, result: any): Promise<void> {
    if (!this.config.enabled) {
      return;
    }

    const key = this.generateCacheKey(query, params);
    const serialized = JSON.stringify(result);
    const originalSize = serialized.length;

    // Check max size
    if (originalSize > this.config.maxSize) {
      this.logger.warn('Result too large to cache', { size: originalSize, maxSize: this.config.maxSize });
      return;
    }

    try {
      if (this.redis) {
        let data: string | Buffer = serialized;
        let compressed = false;
        let compressedSize = originalSize;

        // Compress if enabled and above threshold
        if (this.config.compressionEnabled && originalSize > this.config.compressionThreshold) {
          try {
            const buffer = await gzipAsync(serialized, { level: this.config.compressionLevel });
            data = buffer.toString('base64');
            compressed = true;
            compressedSize = buffer.length;

            // Update compression stats
            this.compressionStats.compressedEntries++;
            this.compressionStats.totalOriginalSize += originalSize;
            this.compressionStats.totalCompressedSize += compressedSize;

            const compressionRatio = (compressedSize / originalSize * 100).toFixed(1);
            const savings = originalSize - compressedSize;

            this.logger.debug('Compressed cache entry', {
              key,
              originalSize,
              compressedSize,
              ratio: `${compressionRatio}%`,
              savings: `${savings} bytes`,
              savingsPercent: `${((savings / originalSize) * 100).toFixed(1)}%`
            });
          } catch (error) {
            this.logger.warn('Compression failed, storing uncompressed', { error });
            compressed = false;
          }
        }

        // Store the data
        await this.redis.setex(key, this.config.ttl, data);
        await this.redis.set(`${key}:meta`, JSON.stringify({
          query: query.substring(0, 500),
          timestamp: Date.now(),
          size: originalSize,
          compressed,
          compressedSize,
          originalSize
        }), 'EX', this.config.ttl);
      } else {
        const entry: CacheEntry = {
          key,
          query: query.substring(0, 500),
          result,
          timestamp: Date.now(),
          ttl: this.config.ttl,
          size: originalSize,
          hits: 0
        };

        this.localCache.set(key, entry);

        // Evict old entries if needed
        this.evictIfNeeded();
      }

      this.logger.debug('Result cached', { key, size: originalSize, ttl: this.config.ttl });
    } catch (error) {
      this.logger.error('Failed to set cache', error);
    }
  }

  /**
   * Generate cache key
   */
  private generateCacheKey(query: string, params?: any[]): string {
    const connection = this.dbManager.getActive();
    const dbName = connection?.config.database || 'default';

    const normalized = this.normalizeQuery(query);
    const paramsStr = params ? JSON.stringify(params) : '';

    const hash = crypto
      .createHash('md5')
      .update(`${dbName}:${normalized}:${paramsStr}`)
      .digest('hex');

    return `query:${hash}`;
  }

  /**
   * Normalize query for consistent caching
   */
  private normalizeQuery(query: string): string {
    return query
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  /**
   * Invalidate cache for specific query
   */
  async invalidate(query: string, params?: any[]): Promise<void> {
    const key = this.generateCacheKey(query, params);

    try {
      if (this.redis) {
        await this.redis.del(key);
        await this.redis.del(`${key}:meta`);
        await this.redis.del(`${key}:hits`);
      } else {
        this.localCache.delete(key);
      }

      this.logger.info('Cache invalidated', { key });
    } catch (error) {
      this.logger.error('Failed to invalidate cache', error);
    }
  }

  /**
   * Async generator for scanning Redis keys with SCAN command
   * @param pattern - Redis key pattern to match
   * @param count - Number of keys to return per iteration (hint to Redis)
   */
  private async *scanKeys(pattern: string, count: number = 100): AsyncGenerator<string[]> {
    if (!this.redis) {
      return;
    }

    let cursor = '0';
    do {
      const [newCursor, keys] = await this.redis.scan(
        cursor,
        'MATCH',
        pattern,
        'COUNT',
        count.toString()
      );
      cursor = newCursor;
      if (keys.length > 0) {
        yield keys;
      }
    } while (cursor !== '0');
  }

  /**
   * Invalidate all cache entries for a table
   */
  async invalidateTable(tableName: string): Promise<void> {
    this.logger.info('Invalidating cache for table', { tableName });

    try {
      if (this.redis) {
        const lowerTableName = tableName.toLowerCase();
        let totalDeleted = 0;

        // Use SCAN instead of KEYS to avoid blocking
        for await (const keyBatch of this.scanKeys('query:*', 100)) {
          // Batch fetch metadata for all keys
          const metaPromises = keyBatch.map(key =>
            this.redis!.get(`${key}:meta`).catch(() => null)
          );
          const metaResults = await Promise.all(metaPromises);

          // Find keys that match the table name
          const keysToDelete: string[] = [];
          keyBatch.forEach((key, index) => {
            const meta = metaResults[index];
            if (meta) {
              try {
                const parsed = JSON.parse(meta);
                if (parsed.query.toLowerCase().includes(lowerTableName)) {
                  keysToDelete.push(key);
                }
              } catch (err) {
                // Skip malformed metadata
              }
            }
          });

          // Batch delete all matching keys and their metadata
          if (keysToDelete.length > 0) {
            const deletePromises: Promise<any>[] = [];
            for (const key of keysToDelete) {
              deletePromises.push(
                this.redis!.del(key),
                this.redis!.del(`${key}:meta`),
                this.redis!.del(`${key}:hits`)
              );
            }
            await Promise.all(deletePromises);
            totalDeleted += keysToDelete.length;
          }
        }

        this.logger.debug('Table cache invalidation complete', {
          tableName,
          keysDeleted: totalDeleted
        });
      } else {
        const toDelete: string[] = [];

        for (const [key, entry] of this.localCache.entries()) {
          if (entry.query.toLowerCase().includes(tableName.toLowerCase())) {
            toDelete.push(key);
          }
        }

        toDelete.forEach((key) => this.localCache.delete(key));
      }
    } catch (error) {
      this.logger.error('Failed to invalidate table cache', error);
    }
  }

  /**
   * Clear all cache
   */
  async clear(): Promise<void> {
    this.logger.info('Clearing all cache');

    try {
      if (this.redis) {
        let totalDeleted = 0;

        // Use SCAN instead of KEYS to avoid blocking
        for await (const keyBatch of this.scanKeys('query:*', 100)) {
          if (keyBatch.length > 0) {
            // Batch delete all keys in this batch
            await this.redis.del(...keyBatch);
            totalDeleted += keyBatch.length;
          }
        }

        this.logger.debug('Cache clear complete', { keysDeleted: totalDeleted });
      } else {
        this.localCache.clear();
      }

      this.stats.hits = 0;
      this.stats.misses = 0;
      this.stats.evictions = 0;
      this.compressionStats.compressedEntries = 0;
      this.compressionStats.totalOriginalSize = 0;
      this.compressionStats.totalCompressedSize = 0;
    } catch (error) {
      this.logger.error('Failed to clear cache', error);
      throw error;
    }
  }

  /**
   * Get cache statistics
   */
  async getStats(): Promise<CacheStats> {
    try {
      let totalKeys = 0;
      let memoryUsed = 0;

      if (this.redis) {
        // Use SCAN instead of KEYS to count keys without blocking
        for await (const keyBatch of this.scanKeys('query:*', 100)) {
          totalKeys += keyBatch.length;
        }

        const info = await this.redis.info('memory');
        const memMatch = info.match(/used_memory:(\d+)/);
        if (memMatch) {
          memoryUsed = parseInt(memMatch[1]);
        }
      } else {
        totalKeys = this.localCache.size;
        memoryUsed = Array.from(this.localCache.values()).reduce(
          (sum, entry) => sum + entry.size,
          0
        );
      }

      const total = this.stats.hits + this.stats.misses;
      const hitRate = total > 0 ? (this.stats.hits / total) * 100 : 0;

      // Calculate compression stats
      const compressionStats = this.calculateCompressionStats();

      return {
        hits: this.stats.hits,
        misses: this.stats.misses,
        hitRate,
        totalKeys,
        memoryUsed,
        evictions: this.stats.evictions,
        compressionStats
      };
    } catch (error) {
      this.logger.error('Failed to get cache stats', error);
      throw error;
    }
  }

  /**
   * Calculate compression statistics
   */
  private calculateCompressionStats() {
    if (this.compressionStats.compressedEntries === 0) {
      return undefined;
    }

    const totalOriginal = this.compressionStats.totalOriginalSize;
    const totalCompressed = this.compressionStats.totalCompressedSize;
    const averageRatio = (totalCompressed / totalOriginal) * 100;
    const savings = totalOriginal - totalCompressed;

    return {
      compressedEntries: this.compressionStats.compressedEntries,
      totalOriginalSize: totalOriginal,
      totalCompressedSize: totalCompressed,
      averageCompressionRatio: parseFloat(averageRatio.toFixed(2)),
      memoryByteSavings: savings
    };
  }

  /**
   * Smart invalidation on data modification
   */
  async onDataModified(query: string): Promise<void> {
    if (this.config.invalidationStrategy !== 'smart') {
      return;
    }

    // Parse query to detect affected tables
    const tables = this.extractTablesFromQuery(query);

    for (const table of tables) {
      if (this.config.autoInvalidateTables.includes(table)) {
        await this.invalidateTable(table);
      }
    }
  }

  /**
   * Extract table names from query
   */
  private extractTablesFromQuery(query: string): string[] {
    const tables: string[] = [];

    // Simple regex-based extraction (for production, use a SQL parser)
    const updateMatch = query.match(/UPDATE\s+(\w+)/i);
    if (updateMatch) tables.push(updateMatch[1]);

    const insertMatch = query.match(/INSERT\s+INTO\s+(\w+)/i);
    if (insertMatch) tables.push(insertMatch[1]);

    const deleteMatch = query.match(/DELETE\s+FROM\s+(\w+)/i);
    if (deleteMatch) tables.push(deleteMatch[1]);

    return tables;
  }

  /**
   * Check if entry is expired
   */
  private isExpired(entry: CacheEntry): boolean {
    const age = Date.now() - entry.timestamp;
    return age > entry.ttl * 1000;
  }

  /**
   * Evict entries if cache is too large
   */
  private evictIfNeeded(): void {
    const maxEntries = 1000; // Max entries in local cache

    if (this.localCache.size > maxEntries) {
      // Evict oldest entries
      const entries = Array.from(this.localCache.entries()).sort(
        (a, b) => a[1].timestamp - b[1].timestamp
      );

      const toEvict = Math.floor(maxEntries * 0.2); // Evict 20%

      for (let i = 0; i < toEvict; i++) {
        this.localCache.delete(entries[i][0]);
        this.stats.evictions++;
      }

      this.logger.debug('Evicted old cache entries', { count: toEvict });
    }
  }

  /**
   * Estimate size of result
   */
  private estimateSize(result: any): number {
    return JSON.stringify(result).length;
  }

  /**
   * Configure cache
   */
  configure(config: Partial<CacheConfig>): void {
    this.config = { ...this.config, ...config };
    this.saveConfig();
    this.logger.info('Cache configuration updated', config);
  }

  /**
   * Get configuration
   */
  getConfig(): CacheConfig {
    return { ...this.config };
  }

  /**
   * Warm up cache with common queries
   */
  async warmUp(queries: Array<{ query: string; params?: any[] }>): Promise<void> {
    this.logger.info('Warming up cache', { count: queries.length });

    for (const { query, params } of queries) {
      try {
        const result = await this.dbManager.executeQuery(query, params);
        await this.set(query, params, result);
      } catch (error) {
        this.logger.error('Failed to warm up cache for query', error);
      }
    }
  }

  /**
   * Export cache entries
   */
  async exportCache(): Promise<CacheEntry[]> {
    if (this.redis) {
      const entries: CacheEntry[] = [];

      // Use SCAN instead of KEYS to avoid blocking
      for await (const keyBatch of this.scanKeys('query:*', 100)) {
        // Batch fetch all data for keys in parallel
        const fetchPromises = keyBatch.map(async (key) => {
          const [result, meta, hits] = await Promise.all([
            this.redis!.get(key),
            this.redis!.get(`${key}:meta`),
            this.redis!.get(`${key}:hits`)
          ]);

          if (result && meta) {
            try {
              const metaData = JSON.parse(meta);
              return {
                key,
                query: metaData.query,
                result: JSON.parse(result),
                timestamp: metaData.timestamp,
                ttl: this.config.ttl,
                size: metaData.size,
                hits: parseInt(hits || '0')
              } as CacheEntry;
            } catch (err) {
              // Skip malformed entries
              return null;
            }
          }
          return null;
        });

        const batchEntries = await Promise.all(fetchPromises);
        entries.push(...batchEntries.filter((e): e is CacheEntry => e !== null));
      }

      return entries;
    } else {
      return Array.from(this.localCache.values());
    }
  }

  /**
   * Load config from state
   */
  private loadConfig(): CacheConfig {
    try {
      const stored = this.stateManager.get('cache-config');
      if (stored) {
        return stored as CacheConfig;
      }
    } catch (error) {
      this.logger.warn('Failed to load cache config', { error });
    }

    return {
      enabled: false,
      ttl: 3600, // 1 hour
      maxSize: 1024 * 1024 * 10, // 10MB
      invalidationStrategy: 'time',
      autoInvalidateTables: [],
      compressionEnabled: true,
      compressionThreshold: 1024, // 1KB
      compressionLevel: 6 // Balanced compression
    };
  }

  /**
   * Save config to state
   */
  private saveConfig(): void {
    try {
      this.stateManager.set('cache-config', this.config, {
        metadata: { type: 'cache-configuration' }
      });
    } catch (error) {
      this.logger.error('Failed to save cache config', error);
    }
  }

  /**
   * Cleanup on shutdown
   */
  async cleanup(): Promise<void> {
    if (this.redis) {
      await this.redis.quit();
    }
    this.localCache.clear();
  }
}
