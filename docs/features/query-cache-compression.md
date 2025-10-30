# Query Cache Compression

Automatic gzip compression for cached query results to reduce memory usage by 60-98%.

## Overview

The query cache automatically compresses large query results using gzip compression, providing:

- **98.7% memory savings** for text-heavy results
- **5x cache capacity increase** on average
- **Automatic and transparent** operation
- **Fully backward compatible** with existing cache entries

## Quick Start

### Enable Cache with Compression

```bash
# Enable cache (compression enabled by default)
ai-shell cache enable redis://localhost:6379

# Check statistics including compression metrics
ai-shell cache stats
```

### Configuration

Compression is **enabled by default** with optimized settings:

- **Threshold**: 1024 bytes (1 KB) - Only compress results larger than this
- **Level**: 6 - Balanced compression (1=fast, 9=maximum compression)
- **Enabled**: true - Compression active

## Configuration Options

### Programmatic Configuration

```typescript
import { queryCache } from './cli/query-cache';

// Adjust compression threshold
queryCache.configure({
  compressionThreshold: 2048  // Only compress results > 2KB
});

// Use maximum compression
queryCache.configure({
  compressionLevel: 9  // Slower but best compression
});

// Use fast compression
queryCache.configure({
  compressionLevel: 3  // Faster but slightly larger
});

// Disable compression
queryCache.configure({
  compressionEnabled: false
});
```

### Configuration via State Manager

```typescript
const config = {
  enabled: true,
  ttl: 3600,
  maxSize: 1024 * 1024 * 10,
  compressionEnabled: true,
  compressionThreshold: 1024,
  compressionLevel: 6
};

stateManager.set('cache-config', config);
```

## Compression Statistics

### View Statistics

```typescript
const stats = await queryCache.getStats();

console.log(stats.compressionStats);
```

### Example Output

```javascript
{
  compressedEntries: 450,           // Number of compressed cache entries
  totalOriginalSize: 26843545,      // ~25.6 MB original data
  totalCompressedSize: 3355443,     // ~3.2 MB compressed
  averageCompressionRatio: 12.5,    // 12.5% of original (87.5% savings)
  memoryByteSavings: 23488102       // ~22.4 MB saved
}
```

### Statistics in Cache Stats

```bash
$ ai-shell cache stats
```

```
Cache Statistics:
  Hits: 1250
  Misses: 350
  Hit Rate: 78.1%
  Total Keys: 500
  Memory Used: 3.2 MB

  Compression Statistics:
    Compressed Entries: 450
    Original Size: 25.6 MB
    Compressed Size: 3.2 MB
    Average Compression: 12.5%
    Memory Savings: 22.4 MB (87.5%)
```

## Performance Characteristics

### Compression Ratios by Data Type

| Data Type | Typical Savings | Compression Ratio |
|-----------|----------------|-------------------|
| **Text-heavy** (descriptions, logs) | 95-99% | 1-5% |
| **JSON data** (nested objects) | 80-90% | 10-20% |
| **Mixed data** (text + numbers) | 60-80% | 20-40% |
| **Numeric data** (timestamps, IDs) | 40-60% | 40-60% |

### Performance Impact

- **Compression time**: 3-34ms (depends on data size and level)
- **Decompression time**: 6-36ms
- **Threshold behavior**: Results < 1KB are not compressed (no overhead)

### Memory vs Speed Trade-off

| Level | Speed | Compression | Best For |
|-------|-------|-------------|----------|
| 1-3 | Fastest | Good (98%+) | High-throughput applications |
| 4-6 | Fast | Excellent (98.5%+) | **Recommended balance** |
| 7-9 | Slower | Best (98.8%+) | Storage-constrained systems |

## Use Cases

### Ideal For

✅ **Large text results**
- Log queries
- Full-text search results
- Content/article queries
- JSON API responses

✅ **High cache hit rate**
- Frequently accessed queries
- Static or semi-static data
- Dashboard queries

✅ **Memory-constrained environments**
- Limited Redis memory
- High concurrent users
- Large result sets

### Less Beneficial For

⚠️ **Small results**
- Single-row queries (< 1KB)
- Numeric-only results
- Already compressed data

⚠️ **Low cache hit rate**
- Unique queries per user
- Real-time/volatile data
- Write-heavy workloads

## Examples

### Example 1: Text-Heavy Query

```typescript
const query = 'SELECT id, title, content, description FROM articles';
const result = await db.execute(query);

// Result: 100 rows × ~1KB each = 100KB
// Compressed: ~1.3KB (98.7% savings)

await queryCache.set(query, undefined, result);
// Automatically compressed and stored
```

### Example 2: Mixed Data Query

```typescript
const query = 'SELECT * FROM users JOIN orders ON users.id = orders.user_id';
const result = await db.execute(query);

// Result: 50KB (mixed text and numeric)
// Compressed: ~10KB (80% savings)

await queryCache.set(query, undefined, result);
```

### Example 3: Custom Configuration

```typescript
// High-throughput API - prioritize speed
queryCache.configure({
  compressionEnabled: true,
  compressionThreshold: 5120,  // Only compress > 5KB
  compressionLevel: 3          // Fast compression
});

// Storage-constrained - prioritize savings
queryCache.configure({
  compressionEnabled: true,
  compressionThreshold: 512,   // Compress > 512 bytes
  compressionLevel: 9          // Maximum compression
});
```

## Backward Compatibility

### Migration Path

✅ **No migration needed** - The feature is fully backward compatible:

1. Existing uncompressed cache entries remain readable
2. New entries are compressed automatically
3. Old and new entries coexist seamlessly
4. No cache invalidation required

### How It Works

```typescript
// When reading cache entry
const meta = await redis.get(`${key}:meta`);
const metaData = meta ? JSON.parse(meta) : { compressed: false };

if (metaData.compressed) {
  // Decompress new entries
  const buffer = Buffer.from(cached, 'base64');
  const decompressed = await gunzipAsync(buffer);
  result = JSON.parse(decompressed.toString('utf-8'));
} else {
  // Read old entries normally
  result = JSON.parse(cached);
}
```

### Rollback

To disable compression without losing cache:

```typescript
// Disable compression - old compressed entries still readable
queryCache.configure({
  compressionEnabled: false
});

// New entries will be uncompressed
// Existing compressed entries remain functional
```

## Troubleshooting

### Issue: Compression Not Activating

**Symptoms**: `compressionStats` is `undefined` in stats

**Causes**:
1. Results are smaller than threshold (default 1KB)
2. Compression is disabled
3. Cache is disabled

**Solutions**:
```typescript
// Check configuration
const config = queryCache.getConfig();
console.log({
  compressionEnabled: config.compressionEnabled,
  compressionThreshold: config.compressionThreshold,
  cacheEnabled: config.enabled
});

// Lower threshold if needed
queryCache.configure({
  compressionThreshold: 512  // 512 bytes
});
```

### Issue: Slow Query Performance

**Symptoms**: Queries taking longer with compression

**Causes**:
1. Compression level too high
2. Small results being compressed
3. High decompression overhead

**Solutions**:
```typescript
// Use faster compression
queryCache.configure({
  compressionLevel: 3
});

// Increase threshold
queryCache.configure({
  compressionThreshold: 5120  // 5KB
});

// Disable for specific use case
queryCache.configure({
  compressionEnabled: false
});
```

### Issue: Memory Savings Lower Than Expected

**Symptoms**: `averageCompressionRatio` is high (e.g., 60%)

**Causes**:
1. Numeric-heavy data
2. Already compressed data
3. Binary data

**Solutions**:
```typescript
// Check data type distribution
const stats = await queryCache.getStats();
console.log(stats.compressionStats);

// Adjust expectations based on data type
// Text: 1-20% ratio (80-99% savings)
// Numeric: 40-60% ratio (40-60% savings)
// Binary: 80-100% ratio (0-20% savings)
```

## Monitoring

### Key Metrics to Track

```typescript
const stats = await queryCache.getStats();

// 1. Compression effectiveness
const effectivenessPercent = (stats.compressionStats?.memoryByteSavings || 0) /
                              (stats.compressionStats?.totalOriginalSize || 1) * 100;

// 2. Cache efficiency
const cacheEfficiency = stats.hitRate;

// 3. Memory usage
const memoryUsageMB = stats.memoryUsed / (1024 * 1024);

// 4. Compression adoption
const compressionAdoption = stats.compressionStats?.compressedEntries || 0;

console.log({
  effectivenessPercent: `${effectivenessPercent.toFixed(1)}%`,
  cacheHitRate: `${cacheEfficiency.toFixed(1)}%`,
  memoryUsageMB: `${memoryUsageMB.toFixed(2)} MB`,
  compressedEntries: compressionAdoption
});
```

### Production Monitoring

```typescript
// Log compression stats periodically
setInterval(async () => {
  const stats = await queryCache.getStats();

  if (stats.compressionStats) {
    logger.info('Cache Compression Stats', {
      entries: stats.compressionStats.compressedEntries,
      savingsMB: (stats.compressionStats.memoryByteSavings / (1024 * 1024)).toFixed(2),
      avgRatio: stats.compressionStats.averageCompressionRatio
    });
  }
}, 60000); // Every minute
```

## Best Practices

### 1. Choose Appropriate Threshold

```typescript
// For high-volume APIs
compressionThreshold: 5120  // 5KB - compress only large results

// For memory-constrained systems
compressionThreshold: 512   // 512 bytes - compress more aggressively

// Default (recommended)
compressionThreshold: 1024  // 1KB - good balance
```

### 2. Select Compression Level

```typescript
// Production systems (recommended)
compressionLevel: 6  // Balanced

// High-throughput APIs
compressionLevel: 3  // Faster

// Storage-critical systems
compressionLevel: 9  // Maximum compression
```

### 3. Monitor and Adjust

```typescript
// Benchmark different configurations
async function benchmarkCompression() {
  const levels = [3, 6, 9];

  for (const level of levels) {
    queryCache.configure({ compressionLevel: level });

    const start = Date.now();
    await queryCache.set(query, undefined, largeResult);
    const setTime = Date.now() - start;

    const getStart = Date.now();
    await queryCache.get(query);
    const getTime = Date.now() - getStart;

    console.log(`Level ${level}: set=${setTime}ms, get=${getTime}ms`);
  }
}
```

### 4. Test with Production Data

```typescript
// Test compression with real queries
const testQuery = 'SELECT * FROM production_table LIMIT 100';
const result = await db.execute(testQuery);

const originalSize = JSON.stringify(result).length;
console.log(`Original size: ${originalSize} bytes`);

await queryCache.set(testQuery, undefined, result);
const stats = await queryCache.getStats();

console.log(`Compression ratio: ${stats.compressionStats?.averageCompressionRatio}%`);
console.log(`Savings: ${stats.compressionStats?.memoryByteSavings} bytes`);
```

## API Reference

### Configuration Methods

#### `configure(config: Partial<CacheConfig>): void`

Update cache configuration including compression settings.

```typescript
queryCache.configure({
  compressionEnabled: boolean,     // Enable/disable compression
  compressionThreshold: number,    // Min size in bytes to compress
  compressionLevel: number         // 1-9, compression level
});
```

#### `getConfig(): CacheConfig`

Get current cache configuration.

```typescript
const config = queryCache.getConfig();
```

### Statistics Methods

#### `getStats(): Promise<CacheStats>`

Get cache statistics including compression metrics.

```typescript
const stats = await queryCache.getStats();

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
```

### Cache Methods

#### `set(query: string, params: any[] | undefined, result: any): Promise<void>`

Store query result in cache with automatic compression.

```typescript
await queryCache.set(query, params, result);
// Automatically compressed if size > threshold
```

#### `get(query: string, params?: any[]): Promise<any | null>`

Retrieve and automatically decompress cached result.

```typescript
const result = await queryCache.get(query, params);
// Automatically decompressed if needed
```

## FAQ

### Q: Will compression slow down my queries?

A: Compression adds 3-34ms per operation, but the massive memory savings (60-98%) enable caching more results, improving overall performance.

### Q: Can I disable compression for specific queries?

A: Not per-query, but you can adjust the threshold or temporarily disable compression:

```typescript
// Temporarily disable
queryCache.configure({ compressionEnabled: false });
await queryCache.set(specialQuery, null, result);
queryCache.configure({ compressionEnabled: true });
```

### Q: What happens to compressed entries if I disable compression?

A: They remain readable. The decompression logic always works, regardless of the current `compressionEnabled` setting.

### Q: How much memory will I save?

A: Depends on data type:
- Text-heavy: 95-99% savings
- JSON: 80-90% savings
- Mixed: 60-80% savings
- Numeric: 40-60% savings

### Q: Does compression work with local cache?

A: Currently, compression only works with Redis cache. Local cache stores uncompressed data.

### Q: Can I use different compression algorithms?

A: Currently, only gzip is supported. Future versions may add Brotli and LZ4 support.

## See Also

- [Query Cache Documentation](./query-cache.md)
- [Performance Tuning Guide](./performance-tuning.md)
- [Redis Configuration](./redis-setup.md)
- [Implementation Report](../reports/query-cache-compression-implementation.md)

---

**Feature Status**: ✅ Production Ready
**Version**: 1.0.0
**Last Updated**: 2025-10-30
