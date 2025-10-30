# Query Cache Tutorial

Learn how to use AI-Shell's intelligent query cache to dramatically improve database query performance and reduce database load.

## Table of Contents

1. [What You'll Learn](#what-youll-learn)
2. [Prerequisites](#prerequisites)
3. [Part 1: Understanding Query Cache](#part-1-understanding-query-cache-5-min)
4. [Part 2: Basic Setup](#part-2-basic-setup-5-min)
5. [Part 3: Advanced Configuration](#part-3-advanced-configuration-10-min)
6. [Part 4: Cache Strategies](#part-4-cache-strategies-10-min)
7. [Part 5: Monitoring and Optimization](#part-5-monitoring-and-optimization-10-min)
8. [Part 6: Production Deployment](#part-6-production-deployment-10-min)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Next Steps](#next-steps)

## What You'll Learn

By the end of this tutorial, you will:

- Understand query cache architecture and benefits
- Configure and enable query caching
- Implement cache invalidation strategies
- Monitor cache performance and hit rates
- Optimize cache settings for production
- Handle distributed caching with Redis
- Implement smart cache warming
- Debug cache-related issues

**Estimated Time:** 50 minutes

## Prerequisites

Before starting this tutorial, ensure you have:

- AI-Shell installed and configured
- A database connection set up
- Basic understanding of SQL queries
- Node.js 18+ or TypeScript knowledge
- Optional: Redis for distributed caching
- 50 minutes of focused time

## Part 1: Understanding Query Cache (5 min)

### What is Query Cache?

Query caching is a performance optimization technique that stores the results of database queries in memory. When the same query is executed again, AI-Shell returns the cached result instead of querying the database, resulting in:

- **10-100x faster response times** for cached queries
- **Reduced database load** by up to 80%
- **Lower infrastructure costs** through reduced database usage
- **Improved user experience** with instant responses

### Cache Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI-Shell Query Cache                       │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │   Cache    │  │  Invalidation│  │   Compression      │  │
│  │   Store    │  │   Strategy   │  │   & Serialization  │  │
│  └────────────┘  └──────────────┘  └────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌──────────────┐          ┌──────────────────┐
│  In-Memory   │          │  Redis Cache     │
│  Cache (LRU) │          │  (Distributed)   │
└──────────────┘          └──────────────────┘
        │                           │
        └─────────────┬─────────────┘
                      ▼
            ┌──────────────────┐
            │    Database      │
            └──────────────────┘
```

### How It Works

1. **Query Execution**: Application sends SQL query to AI-Shell
2. **Cache Key Generation**: AI-Shell generates unique key from query + parameters
3. **Cache Lookup**: Check if result exists in cache
4. **Cache Hit**: Return cached result immediately (microseconds)
5. **Cache Miss**: Execute query on database, store result, return to app
6. **TTL Management**: Automatically expire stale entries
7. **Invalidation**: Clear cache when data changes

### When to Use Caching

**Ideal Use Cases:**

✅ **Read-Heavy Queries**
- Dashboard statistics
- Product catalogs
- User profiles
- Configuration data
- Reference tables

✅ **Expensive Queries**
- Complex joins (5+ tables)
- Aggregations over large datasets
- Full-text searches
- Geographic distance calculations
- Report generation

✅ **Frequently Accessed Data**
- Homepage content
- Navigation menus
- Category listings
- Popular products
- Trending content

**When NOT to Cache:**

❌ **Real-Time Data**
- Stock prices
- Live sports scores
- Chat messages
- Auction bids
- Real-time analytics

❌ **User-Specific Sensitive Data**
- Personal financial data
- Medical records
- Authentication tokens
- Payment information

❌ **Write-Heavy Tables**
- Activity logs
- Event streams
- Time-series data
- Frequently updated counters

### Performance Expectations

| Query Type | Without Cache | With Cache | Improvement |
|------------|--------------|------------|-------------|
| Simple SELECT | 50ms | 0.5ms | 100x faster |
| Complex JOIN | 500ms | 2ms | 250x faster |
| Aggregation | 2000ms | 5ms | 400x faster |
| Full-text Search | 1000ms | 3ms | 333x faster |

## Part 2: Basic Setup (5 min)

### Step 1: Enable Query Cache

Create or update your AI-Shell configuration file:

```typescript
// config/database.ts
import { DatabaseConfig } from 'ai-shell';

export const config: DatabaseConfig = {
  connection: {
    host: process.env.DB_HOST,
    port: 5432,
    database: process.env.DB_NAME,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
  },

  cache: {
    enabled: true,                    // Enable caching
    ttl: 3600,                        // Time to live: 1 hour
    maxSize: 100 * 1024 * 1024,      // Max cache size: 100 MB
    checkPeriod: 600,                 // Check for expired entries: 10 min
  },
};
```

### Step 2: Test Basic Caching

Create a test script to verify caching works:

```typescript
// test-cache.ts
import { AIShell } from 'ai-shell';

const shell = new AIShell(config);

async function testCache() {
  console.log('Testing query cache...\n');

  const query = 'SELECT * FROM products WHERE category = $1 LIMIT 100';
  const params = ['electronics'];

  // First execution (cache miss)
  console.log('First execution (no cache):');
  const start1 = Date.now();
  const result1 = await shell.query(query, params);
  const time1 = Date.now() - start1;
  console.log(`Time: ${time1}ms`);
  console.log(`Rows: ${result1.rows.length}`);
  console.log(`Cache hit: ${result1.cached}\n`);

  // Second execution (cache hit)
  console.log('Second execution (cached):');
  const start2 = Date.now();
  const result2 = await shell.query(query, params);
  const time2 = Date.now() - start2;
  console.log(`Time: ${time2}ms`);
  console.log(`Rows: ${result2.rows.length}`);
  console.log(`Cache hit: ${result2.cached}\n`);

  console.log(`Performance improvement: ${(time1 / time2).toFixed(1)}x faster`);
}

testCache().catch(console.error);
```

Run the test:

```bash
npx ts-node test-cache.ts
```

**Expected Output:**

```
Testing query cache...

First execution (no cache):
Time: 245ms
Rows: 100
Cache hit: false

Second execution (cached):
Time: 2ms
Rows: 100
Cache hit: true

Performance improvement: 122.5x faster
```

### Step 3: Verify Cache is Working

Use the CLI to check cache statistics:

```bash
ai-shell cache stats
```

**Example Output:**

```
Query Cache Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Queries:        150
Cache Hits:           142 (94.7%)
Cache Misses:         8 (5.3%)
Hit Rate:             94.7%

Cache Size:           24.5 MB / 100 MB (24.5%)
Cached Entries:       45
Average Entry Size:   558 KB

Time Saved:           12.5 seconds
Avg Hit Time:         1.2ms
Avg Miss Time:        156ms

Evictions:            3
Expired Entries:      12
```

## Part 3: Advanced Configuration (10 min)

### Cache Storage Options

AI-Shell supports multiple cache storage backends:

#### Option 1: In-Memory Cache (Default)

Fast, simple, but limited to single process:

```typescript
cache: {
  enabled: true,
  storage: 'memory',
  ttl: 3600,
  maxSize: 200 * 1024 * 1024,  // 200 MB

  // LRU eviction policy
  evictionPolicy: 'lru',

  // Check for expired entries every 10 minutes
  checkPeriod: 600,
}
```

#### Option 2: Redis Cache (Distributed)

Shared across multiple servers, persistent:

```typescript
cache: {
  enabled: true,
  storage: 'redis',
  ttl: 7200,

  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: 6379,
    password: process.env.REDIS_PASSWORD,
    db: 0,

    // Connection pool
    maxConnections: 50,
    minConnections: 5,

    // Cluster mode
    cluster: true,
    clusterNodes: [
      { host: 'redis-1', port: 6379 },
      { host: 'redis-2', port: 6379 },
      { host: 'redis-3', port: 6379 },
    ],

    // Sentinel mode for HA
    sentinel: {
      sentinels: [
        { host: 'sentinel-1', port: 26379 },
        { host: 'sentinel-2', port: 26379 },
      ],
      name: 'mymaster',
    },
  },
}
```

#### Option 3: Hybrid Cache (Two-Tier)

L1 in-memory + L2 Redis for best performance:

```typescript
cache: {
  enabled: true,
  storage: 'hybrid',
  ttl: 3600,

  // L1: Fast in-memory cache
  l1: {
    maxSize: 50 * 1024 * 1024,  // 50 MB
    ttl: 300,                    // 5 minutes
  },

  // L2: Persistent Redis cache
  l2: {
    maxSize: 500 * 1024 * 1024, // 500 MB
    ttl: 3600,                   // 1 hour
    redis: {
      host: 'localhost',
      port: 6379,
    },
  },
}
```

### Compression Options

Reduce memory usage with compression:

```typescript
cache: {
  enabled: true,
  ttl: 3600,

  // Enable compression for large results
  compression: {
    enabled: true,
    algorithm: 'gzip',           // 'gzip', 'brotli', 'lz4'
    threshold: 10 * 1024,        // Compress if > 10 KB
    level: 6,                    // Compression level (1-9)
  },
}
```

**Compression Algorithms Comparison:**

| Algorithm | Compression Ratio | Speed | CPU Usage | Best For |
|-----------|------------------|-------|-----------|----------|
| LZ4 | 2.0x | Very Fast | Low | Real-time data |
| Gzip | 3.5x | Fast | Medium | General purpose |
| Brotli | 4.2x | Slow | High | Static data |

### Serialization Options

Choose how data is serialized:

```typescript
cache: {
  enabled: true,
  ttl: 3600,

  serialization: {
    format: 'msgpack',  // 'json', 'msgpack', 'cbor', 'protobuf'

    // Custom serializer
    serialize: (data) => msgpack.encode(data),
    deserialize: (data) => msgpack.decode(data),

    // Preserve data types
    preserveTypes: true,
  },
}
```

### Per-Query Cache Control

Override cache settings for specific queries:

```typescript
// Cache for 10 minutes
const products = await shell.query(
  'SELECT * FROM products WHERE featured = true',
  [],
  {
    cache: {
      ttl: 600,
      key: 'featured-products',  // Custom cache key
    }
  }
);

// Cache for 24 hours
const categories = await shell.query(
  'SELECT * FROM categories ORDER BY name',
  [],
  {
    cache: {
      ttl: 86400,
      key: 'all-categories',
    }
  }
);

// Disable caching for this query
const liveData = await shell.query(
  'SELECT * FROM live_prices WHERE symbol = $1',
  ['AAPL'],
  {
    cache: {
      enabled: false,
    }
  }
);

// Force cache refresh
const freshData = await shell.query(
  'SELECT COUNT(*) FROM orders WHERE status = $1',
  ['pending'],
  {
    cache: {
      refresh: true,  // Bypass cache and update it
    }
  }
);
```

## Part 4: Cache Strategies (10 min)

### Strategy 1: Time-Based Invalidation (TTL)

Simplest strategy - cache expires after fixed time:

```typescript
cache: {
  enabled: true,

  // Global TTL
  ttl: 3600,  // 1 hour

  // Per-table TTL overrides
  tableTTL: {
    products: 1800,      // 30 minutes (changes often)
    categories: 86400,   // 24 hours (rarely changes)
    users: 300,          // 5 minutes (profile updates)
    config: 604800,      // 1 week (very stable)
  },
}
```

**Use Cases:**
- Data with predictable update patterns
- Content that can tolerate some staleness
- High-traffic read-heavy tables

### Strategy 2: Manual Invalidation

Explicitly clear cache when data changes:

```typescript
import { AIShell } from 'ai-shell';

const shell = new AIShell(config);

// Update product
async function updateProduct(id: number, data: any) {
  // Update database
  await shell.query(
    'UPDATE products SET name = $1, price = $2 WHERE id = $3',
    [data.name, data.price, id]
  );

  // Invalidate related cache entries
  await shell.cache.invalidate({
    tables: ['products'],
    keys: [
      `product:${id}`,
      'products:list',
      'products:featured',
      `category:${data.categoryId}:products`,
    ],
  });

  console.log('Product updated and cache invalidated');
}

// Clear all cache for a table
await shell.cache.invalidateTable('products');

// Clear specific cache entry
await shell.cache.invalidateKey('featured-products');

// Clear multiple tables
await shell.cache.invalidateTables(['products', 'categories', 'inventory']);

// Clear entire cache
await shell.cache.clear();
```

### Strategy 3: Smart Invalidation

Automatically detect and invalidate affected queries:

```typescript
cache: {
  enabled: true,
  ttl: 3600,

  smartInvalidation: {
    enabled: true,

    // Track table dependencies
    trackDependencies: true,

    // Invalidate on write operations
    invalidateOnWrite: true,

    // Analyze query patterns
    learnPatterns: true,

    // Propagate invalidation to related queries
    propagate: true,
  },
}
```

**How Smart Invalidation Works:**

1. **Dependency Tracking**: AI-Shell analyzes queries to identify table relationships
2. **Write Detection**: Monitors INSERT, UPDATE, DELETE operations
3. **Cascade Invalidation**: Clears cache for affected queries
4. **Pattern Learning**: Learns common query patterns over time

**Example:**

```typescript
// Query 1: Cached with dependency tracking
const products = await shell.query(`
  SELECT p.*, c.name as category_name
  FROM products p
  JOIN categories c ON p.category_id = c.id
  WHERE c.slug = $1
`, ['electronics']);

// Dependencies tracked: products, categories

// Later: Update a product
await shell.query(`
  UPDATE products SET price = $1 WHERE id = $2
`, [299.99, 123]);

// Smart invalidation automatically clears:
// - All queries touching products table
// - Related join queries (products + categories)
// - Aggregate queries on products
```

### Strategy 4: Cache Warming

Pre-populate cache with frequently accessed data:

```typescript
import { AIShell } from 'ai-shell';

const shell = new AIShell(config);

async function warmCache() {
  console.log('Warming query cache...');

  const queries = [
    // Homepage data
    {
      query: 'SELECT * FROM products WHERE featured = true ORDER BY priority LIMIT 10',
      params: [],
      key: 'featured-products',
    },

    // Navigation
    {
      query: 'SELECT * FROM categories WHERE parent_id IS NULL ORDER BY position',
      params: [],
      key: 'main-categories',
    },

    // Popular searches
    {
      query: 'SELECT * FROM products WHERE category_id = $1 LIMIT 20',
      params: [5],
      key: 'category-5-products',
    },

    // User counts
    {
      query: 'SELECT COUNT(*) as total FROM users WHERE active = true',
      params: [],
      key: 'active-users-count',
    },
  ];

  // Execute all queries in parallel
  await Promise.all(
    queries.map(({ query, params, key }) =>
      shell.query(query, params, { cache: { key } })
    )
  );

  console.log(`Cache warmed: ${queries.length} queries pre-loaded`);
}

// Warm cache on startup
warmCache().catch(console.error);

// Refresh cache periodically
setInterval(warmCache, 30 * 60 * 1000); // Every 30 minutes
```

### Strategy 5: Conditional Caching

Cache based on query characteristics:

```typescript
cache: {
  enabled: true,
  ttl: 3600,

  conditionalCaching: {
    // Only cache queries with these characteristics
    rules: [
      {
        // Cache expensive queries
        condition: 'executionTime > 100',  // > 100ms
        ttl: 3600,
      },
      {
        // Cache queries with many rows
        condition: 'rowCount > 100',
        ttl: 1800,
      },
      {
        // Cache queries on specific tables
        condition: 'tables IN ["products", "categories"]',
        ttl: 3600,
      },
      {
        // Don't cache user-specific queries
        condition: 'NOT tables IN ["user_sessions", "shopping_carts"]',
        ttl: 0,  // Disable caching
      },
    ],
  },
}
```

### Strategy 6: Tag-Based Invalidation

Group cache entries with tags for bulk invalidation:

```typescript
// Tag queries during execution
await shell.query(
  'SELECT * FROM products WHERE category_id = $1',
  [categoryId],
  {
    cache: {
      tags: ['products', `category:${categoryId}`, 'catalog'],
    }
  }
);

// Later: Invalidate all queries with a tag
await shell.cache.invalidateByTag('products');
await shell.cache.invalidateByTag(`category:${categoryId}`);
await shell.cache.invalidateByTags(['products', 'catalog']);
```

## Part 5: Monitoring and Optimization (10 min)

### Real-Time Cache Monitoring

Monitor cache performance in real-time:

```typescript
import { AIShell } from 'ai-shell';

const shell = new AIShell(config);

// Get cache statistics
const stats = await shell.cache.getStats();
console.log('Cache Statistics:', stats);

// Output:
// {
//   hits: 1523,
//   misses: 87,
//   hitRate: 0.946,
//   size: 45678901,
//   entries: 234,
//   evictions: 12,
//   expired: 45,
//   avgHitTime: 1.2,
//   avgMissTime: 156.7,
//   timeSaved: 240567
// }
```

### Cache Performance Metrics

Track key performance indicators:

```typescript
// Enable metrics collection
cache: {
  enabled: true,
  ttl: 3600,

  metrics: {
    enabled: true,
    interval: 60000,  // Collect every minute

    // Export to monitoring service
    exporters: [
      {
        type: 'prometheus',
        endpoint: '/metrics',
      },
      {
        type: 'datadog',
        apiKey: process.env.DATADOG_API_KEY,
      },
      {
        type: 'cloudwatch',
        region: 'us-east-1',
        namespace: 'AIShell/Cache',
      },
    ],
  },
}
```

**Key Metrics to Monitor:**

1. **Hit Rate**: Percentage of queries served from cache
   - Target: > 80% for read-heavy workloads
   - Alert: < 60%

2. **Response Time**: Average time to return cached results
   - Target: < 5ms
   - Alert: > 10ms

3. **Memory Usage**: Cache size vs. maximum
   - Target: 60-80% utilization
   - Alert: > 90%

4. **Eviction Rate**: Entries removed due to size limits
   - Target: < 5% of hits
   - Alert: > 15%

5. **Time Saved**: Total database time avoided
   - Track to measure ROI

### Cache Analysis Dashboard

Create a monitoring dashboard:

```typescript
// analysis-dashboard.ts
import { AIShell } from 'ai-shell';

const shell = new AIShell(config);

async function generateCacheReport() {
  const report = await shell.cache.analyze();

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('               CACHE PERFORMANCE REPORT              ');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log();

  console.log('📊 Overall Statistics:');
  console.log(`   Hit Rate:        ${(report.hitRate * 100).toFixed(1)}%`);
  console.log(`   Total Queries:   ${report.totalQueries.toLocaleString()}`);
  console.log(`   Cache Hits:      ${report.hits.toLocaleString()}`);
  console.log(`   Cache Misses:    ${report.misses.toLocaleString()}`);
  console.log();

  console.log('⚡ Performance:');
  console.log(`   Avg Hit Time:    ${report.avgHitTime.toFixed(2)}ms`);
  console.log(`   Avg Miss Time:   ${report.avgMissTime.toFixed(2)}ms`);
  console.log(`   Time Saved:      ${(report.timeSaved / 1000).toFixed(2)}s`);
  console.log(`   Speedup:         ${(report.avgMissTime / report.avgHitTime).toFixed(1)}x`);
  console.log();

  console.log('💾 Memory Usage:');
  console.log(`   Cache Size:      ${(report.size / 1024 / 1024).toFixed(2)} MB`);
  console.log(`   Max Size:        ${(report.maxSize / 1024 / 1024).toFixed(2)} MB`);
  console.log(`   Utilization:     ${(report.size / report.maxSize * 100).toFixed(1)}%`);
  console.log(`   Entries:         ${report.entries.toLocaleString()}`);
  console.log(`   Avg Entry Size:  ${(report.size / report.entries / 1024).toFixed(2)} KB`);
  console.log();

  console.log('🔄 Cache Activity:');
  console.log(`   Evictions:       ${report.evictions.toLocaleString()}`);
  console.log(`   Expired:         ${report.expired.toLocaleString()}`);
  console.log(`   Invalidations:   ${report.invalidations.toLocaleString()}`);
  console.log();

  console.log('🏆 Top Cached Queries:');
  report.topQueries.forEach((q, i) => {
    console.log(`   ${i + 1}. ${q.query.substring(0, 60)}...`);
    console.log(`      Hits: ${q.hits}, Time Saved: ${(q.timeSaved / 1000).toFixed(2)}s`);
  });
  console.log();

  console.log('⚠️  Recommendations:');
  report.recommendations.forEach(r => {
    console.log(`   • ${r}`);
  });
  console.log();

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
}

// Run report every hour
setInterval(generateCacheReport, 60 * 60 * 1000);
```

### Optimization Techniques

#### Technique 1: Adjust TTL Based on Hit Rate

```typescript
import { AIShell } from 'ai-shell';

const shell = new AIShell(config);

async function optimizeTTL() {
  const analysis = await shell.cache.analyzeHitRates();

  for (const [table, metrics] of Object.entries(analysis.byTable)) {
    if (metrics.hitRate < 0.5) {
      // Low hit rate - increase TTL
      await shell.cache.setTableTTL(table, metrics.currentTTL * 2);
      console.log(`Increased TTL for ${table}: ${metrics.currentTTL}s → ${metrics.currentTTL * 2}s`);
    } else if (metrics.hitRate > 0.95 && metrics.evictionRate < 0.01) {
      // Very high hit rate - can reduce TTL to save memory
      await shell.cache.setTableTTL(table, metrics.currentTTL * 0.75);
      console.log(`Decreased TTL for ${table}: ${metrics.currentTTL}s → ${metrics.currentTTL * 0.75}s`);
    }
  }
}

// Run optimization daily
setInterval(optimizeTTL, 24 * 60 * 60 * 1000);
```

#### Technique 2: Identify Cache-Worthy Queries

```typescript
async function findCacheOpportunities() {
  const analysis = await shell.cache.analyzeQueries({
    period: '7d',
    minExecutionTime: 50,  // Queries taking > 50ms
    minFrequency: 10,      // Executed at least 10 times
  });

  console.log('Cache Opportunities:');
  console.log();

  analysis.opportunities.forEach((opp, i) => {
    console.log(`${i + 1}. Query: ${opp.query.substring(0, 80)}...`);
    console.log(`   Frequency:       ${opp.frequency} executions`);
    console.log(`   Avg Exec Time:   ${opp.avgTime.toFixed(2)}ms`);
    console.log(`   Potential Savings: ${(opp.potentialSavings / 1000).toFixed(2)}s`);
    console.log(`   Recommendation:  Cache with TTL ${opp.recommendedTTL}s`);
    console.log();
  });
}
```

#### Technique 3: Memory Optimization

```typescript
// Reduce memory usage with compression and eviction tuning
cache: {
  enabled: true,
  maxSize: 200 * 1024 * 1024,  // 200 MB

  // Aggressive eviction policy
  evictionPolicy: 'lru',
  evictionPercentage: 20,  // Evict 20% when full

  // Compression
  compression: {
    enabled: true,
    algorithm: 'lz4',      // Fast compression
    threshold: 5 * 1024,   // Compress entries > 5 KB
  },

  // Size limits per entry
  maxEntrySize: 10 * 1024 * 1024,  // 10 MB max

  // Exclude large result sets
  excludeLargeResults: true,
  largeResultThreshold: 1000,  // Don't cache > 1000 rows
}
```

## Part 6: Production Deployment (10 min)

### Production Configuration

Recommended settings for production:

```typescript
// config/production.ts
export const productionCacheConfig = {
  cache: {
    enabled: true,
    storage: 'redis',
    ttl: 3600,

    redis: {
      host: process.env.REDIS_HOST,
      port: 6379,
      password: process.env.REDIS_PASSWORD,
      db: 0,

      // Connection pool
      maxConnections: 100,
      minConnections: 10,

      // Timeouts
      connectTimeout: 10000,
      commandTimeout: 5000,

      // Retry strategy
      retryStrategy: (times) => {
        if (times > 3) return null;
        return Math.min(times * 1000, 3000);
      },

      // Cluster mode
      cluster: true,
      clusterNodes: process.env.REDIS_CLUSTER_NODES.split(',').map(node => {
        const [host, port] = node.split(':');
        return { host, port: parseInt(port) };
      }),

      // High availability
      sentinel: {
        sentinels: process.env.REDIS_SENTINELS.split(',').map(s => {
          const [host, port] = s.split(':');
          return { host, port: parseInt(port) };
        }),
        name: 'mymaster',
      },
    },

    // Compression
    compression: {
      enabled: true,
      algorithm: 'gzip',
      threshold: 10 * 1024,
      level: 6,
    },

    // Smart invalidation
    smartInvalidation: {
      enabled: true,
      trackDependencies: true,
      invalidateOnWrite: true,
      propagate: true,
    },

    // Metrics
    metrics: {
      enabled: true,
      interval: 60000,
      exporters: [
        {
          type: 'prometheus',
          endpoint: '/metrics',
        },
        {
          type: 'datadog',
          apiKey: process.env.DATADOG_API_KEY,
          tags: ['env:production', 'service:ai-shell'],
        },
      ],
    },

    // Logging
    logging: {
      enabled: true,
      level: 'info',
      logHits: false,        // Don't log every hit (too verbose)
      logMisses: true,       // Log misses for analysis
      logEvictions: true,    // Track eviction patterns
      logErrors: true,
    },
  },
};
```

### Health Checks

Implement cache health monitoring:

```typescript
// health-check.ts
import { AIShell } from 'ai-shell';

export async function cacheHealthCheck() {
  const shell = new AIShell(config);

  try {
    // Check cache is responding
    const start = Date.now();
    const stats = await shell.cache.getStats();
    const responseTime = Date.now() - start;

    // Health criteria
    const health = {
      healthy: true,
      checks: {
        responsive: responseTime < 100,
        hitRate: stats.hitRate > 0.7,
        memoryUsage: stats.size / stats.maxSize < 0.9,
        errorRate: stats.errors / stats.totalQueries < 0.01,
      },
      metrics: {
        responseTime,
        hitRate: stats.hitRate,
        memoryUsage: stats.size / stats.maxSize,
        errorRate: stats.errors / stats.totalQueries,
      },
    };

    health.healthy = Object.values(health.checks).every(v => v);

    return health;
  } catch (error) {
    return {
      healthy: false,
      error: error.message,
    };
  }
}

// Express health endpoint
app.get('/health/cache', async (req, res) => {
  const health = await cacheHealthCheck();
  const status = health.healthy ? 200 : 503;
  res.status(status).json(health);
});
```

### Graceful Degradation

Handle cache failures gracefully:

```typescript
import { AIShell } from 'ai-shell';

const shell = new AIShell({
  ...config,
  cache: {
    ...config.cache,

    // Fallback behavior
    fallbackOnError: true,  // Query database if cache fails

    // Circuit breaker
    circuitBreaker: {
      enabled: true,
      threshold: 5,         // Open circuit after 5 failures
      timeout: 60000,       // Try again after 1 minute
      resetTimeout: 300000, // Fully reset after 5 minutes
    },

    // Error handling
    onError: (error, context) => {
      console.error('Cache error:', error);

      // Alert if cache is down
      if (context.consecutive > 10) {
        alertOps('Cache system degraded', error);
      }

      // Metrics
      metrics.increment('cache.errors', {
        type: error.type,
        operation: context.operation,
      });
    },
  },
});
```

### Deployment Checklist

Before deploying cache to production:

- [ ] Configure Redis with replication and clustering
- [ ] Set appropriate TTL values based on testing
- [ ] Enable compression for large result sets
- [ ] Configure smart invalidation for write-heavy tables
- [ ] Set up monitoring and alerting
- [ ] Implement health checks
- [ ] Enable circuit breaker for resilience
- [ ] Test failover scenarios
- [ ] Document cache warming procedures
- [ ] Set up automated cache analysis reports
- [ ] Configure backup and disaster recovery
- [ ] Load test cache under production traffic
- [ ] Establish cache performance baselines
- [ ] Create runbooks for common issues

## Best Practices

### Do's ✅

1. **Cache Read-Heavy Queries**
   - Prioritize queries executed > 100 times/hour
   - Focus on expensive joins and aggregations
   - Cache frequently accessed reference data

2. **Set Appropriate TTLs**
   - Short TTL (5-15 min) for frequently changing data
   - Medium TTL (1-6 hours) for daily updated data
   - Long TTL (24+ hours) for static reference data

3. **Monitor Hit Rates**
   - Target > 80% hit rate for read-heavy workloads
   - Investigate if hit rate drops below 60%
   - Track hit rates per table and query pattern

4. **Use Compression**
   - Enable for result sets > 10 KB
   - Use LZ4 for speed, Gzip for balance, Brotli for size
   - Monitor compression ratio and CPU usage

5. **Implement Smart Invalidation**
   - Enable dependency tracking
   - Use tag-based invalidation for related queries
   - Invalidate proactively on writes

6. **Warm Critical Caches**
   - Pre-load homepage and navigation queries
   - Refresh periodically before expiration
   - Warm cache after deployments

7. **Use Redis in Production**
   - Enable clustering for high availability
   - Configure sentinel for automatic failover
   - Use connection pooling

8. **Test Cache Behavior**
   - Verify TTL expiration works correctly
   - Test invalidation strategies
   - Validate cache warming procedures

### Don'ts ❌

1. **Don't Cache Everything**
   - Avoid caching real-time data
   - Don't cache user-specific sensitive data
   - Skip write-heavy tables with poor hit rates

2. **Don't Use Excessive TTLs**
   - Long TTLs lead to stale data
   - Wastes memory on unused entries
   - Makes invalidation harder

3. **Don't Ignore Memory Limits**
   - Set maxSize appropriately for your server
   - Monitor memory usage and eviction rates
   - Use compression to reduce memory footprint

4. **Don't Skip Monitoring**
   - Always enable metrics collection
   - Set up alerts for degraded performance
   - Review cache statistics regularly

5. **Don't Cache Large Result Sets**
   - Set maxEntrySize limit (e.g., 10 MB)
   - Use pagination instead of caching huge results
   - Consider streaming for very large datasets

6. **Don't Hardcode Cache Keys**
   - Use consistent key generation
   - Include query parameters in keys
   - Avoid collisions with unique prefixes

7. **Don't Deploy Without Testing**
   - Test under production-like load
   - Validate failover scenarios
   - Verify cache warming works

8. **Don't Forget Security**
   - Secure Redis with authentication
   - Use TLS for Redis connections
   - Don't cache sensitive data without encryption

## Troubleshooting

### Problem: Low Hit Rate (< 60%)

**Symptoms:**
- Cache hit rate below 60%
- High database load despite caching
- Slow query response times

**Diagnosis:**

```typescript
// Check hit rate by table
const analysis = await shell.cache.analyzeHitRates();
console.log('Hit Rates by Table:', analysis.byTable);

// Check query patterns
const patterns = await shell.cache.analyzeQueryPatterns();
console.log('Common Patterns:', patterns);
```

**Solutions:**

1. **Increase TTL for stable data:**
   ```typescript
   cache: {
     tableTTL: {
       products: 3600,    // Increase from 1800
       categories: 86400, // Increase from 3600
     }
   }
   ```

2. **Enable cache warming:**
   ```typescript
   // Warm cache on startup and periodically
   await warmCache();
   setInterval(warmCache, 30 * 60 * 1000);
   ```

3. **Check for cache key collisions:**
   ```typescript
   // Use unique cache keys
   const result = await shell.query(query, params, {
     cache: {
       key: `products:category:${categoryId}:page:${page}`,
     }
   });
   ```

### Problem: High Memory Usage

**Symptoms:**
- Cache using > 90% of maxSize
- Frequent evictions
- Out of memory errors

**Diagnosis:**

```typescript
const stats = await shell.cache.getStats();
console.log('Memory Usage:', {
  size: stats.size,
  maxSize: stats.maxSize,
  utilization: (stats.size / stats.maxSize * 100).toFixed(1) + '%',
  avgEntrySize: (stats.size / stats.entries / 1024).toFixed(2) + ' KB',
  evictions: stats.evictions,
});
```

**Solutions:**

1. **Enable compression:**
   ```typescript
   cache: {
     compression: {
       enabled: true,
       algorithm: 'gzip',
       threshold: 5 * 1024,
     }
   }
   ```

2. **Reduce TTLs:**
   ```typescript
   cache: {
     ttl: 1800,  // Reduce from 3600
   }
   ```

3. **Limit entry size:**
   ```typescript
   cache: {
     maxEntrySize: 5 * 1024 * 1024,  // 5 MB max
     excludeLargeResults: true,
     largeResultThreshold: 500,      // Don't cache > 500 rows
   }
   ```

4. **Increase max size or eviction:**
   ```typescript
   cache: {
     maxSize: 500 * 1024 * 1024,  // Increase to 500 MB
     evictionPercentage: 25,       // Evict 25% when full
   }
   ```

### Problem: Cache Not Working

**Symptoms:**
- All queries show cache miss
- Cache hit rate = 0%
- No entries in cache

**Diagnosis:**

```bash
# Check cache is enabled
ai-shell cache status

# Check configuration
ai-shell cache config

# Test basic caching
ai-shell cache test
```

**Solutions:**

1. **Verify cache is enabled:**
   ```typescript
   cache: {
     enabled: true,  // Must be true
   }
   ```

2. **Check cache storage is accessible:**
   ```bash
   # For Redis
   redis-cli ping

   # Test connection
   redis-cli -h $REDIS_HOST -p 6379 -a $REDIS_PASSWORD ping
   ```

3. **Check TTL is not 0:**
   ```typescript
   cache: {
     ttl: 3600,  // Must be > 0
   }
   ```

4. **Verify cache middleware is registered:**
   ```typescript
   import { AIShell } from 'ai-shell';

   const shell = new AIShell(config);
   await shell.initialize();  // Ensure initialization is called
   ```

### Problem: Stale Data

**Symptoms:**
- Application showing old data
- Updates not reflected immediately
- User complaints about incorrect information

**Diagnosis:**

```typescript
// Check when cache entry was created
const entry = await shell.cache.getEntry('featured-products');
console.log('Cached:', new Date(entry.cachedAt));
console.log('Expires:', new Date(entry.expiresAt));
console.log('Age:', Math.floor((Date.now() - entry.cachedAt) / 1000), 'seconds');
```

**Solutions:**

1. **Reduce TTL:**
   ```typescript
   cache: {
     ttl: 300,  // 5 minutes instead of 1 hour
   }
   ```

2. **Enable smart invalidation:**
   ```typescript
   cache: {
     smartInvalidation: {
       enabled: true,
       invalidateOnWrite: true,
     }
   }
   ```

3. **Manual invalidation on updates:**
   ```typescript
   // After updating data
   await shell.cache.invalidateTable('products');
   ```

4. **Force cache refresh:**
   ```typescript
   const result = await shell.query(query, params, {
     cache: { refresh: true }
   });
   ```

### Problem: Redis Connection Failures

**Symptoms:**
- "Connection refused" errors
- "ECONNREFUSED" in logs
- Cache not working in production

**Diagnosis:**

```bash
# Test Redis connectivity
redis-cli -h $REDIS_HOST -p 6379 ping

# Check Redis is running
redis-cli info server

# Check network connectivity
telnet $REDIS_HOST 6379
```

**Solutions:**

1. **Enable fallback mode:**
   ```typescript
   cache: {
     fallbackOnError: true,  // Query database if Redis fails
   }
   ```

2. **Configure retry strategy:**
   ```typescript
   cache: {
     redis: {
       retryStrategy: (times) => {
         if (times > 5) return null;
         return Math.min(times * 1000, 5000);
       },
     }
   }
   ```

3. **Enable circuit breaker:**
   ```typescript
   cache: {
     circuitBreaker: {
       enabled: true,
       threshold: 5,
       timeout: 60000,
     }
   }
   ```

4. **Check firewall rules:**
   ```bash
   # Allow Redis port
   sudo ufw allow 6379/tcp
   ```

## Next Steps

### Advanced Topics

Now that you understand query caching basics, explore these advanced topics:

1. **[Distributed Caching Architecture](./distributed-caching.md)**
   - Multi-region caching
   - Cache coherence protocols
   - Global cache synchronization

2. **[Cache Invalidation Patterns](./cache-invalidation-patterns.md)**
   - Event-driven invalidation
   - CDC (Change Data Capture)
   - Message queue integration

3. **[Performance Tuning Guide](./cache-performance-tuning.md)**
   - Benchmarking methodology
   - Optimization strategies
   - Capacity planning

4. **[Security Best Practices](./cache-security.md)**
   - Encrypting cached data
   - Access control
   - Audit logging

### Related Tutorials

- **[Migration Tester](./migration-tester-tutorial.md)** - Test schema changes safely
- **[SQL Explainer](./sql-explainer-tutorial.md)** - Understand query performance
- **[Cost Optimizer](./cost-optimizer-tutorial.md)** - Reduce query costs

### API Reference

- **[Cache API Documentation](../../api/cache-api.md)**
- **[Configuration Reference](../../api/configuration.md)**
- **[CLI Commands](../../cli/cache-commands.md)**

### Getting Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/ai-shell/issues)
- **Discord Community**: [Join our community](https://discord.gg/ai-shell)
- **Stack Overflow**: Tag questions with `ai-shell` and `query-cache`
- **Documentation**: [Full documentation](https://docs.ai-shell.io)

### Feedback

Help us improve this tutorial! Submit feedback:

```bash
ai-shell feedback --tutorial query-cache --rating 5 --comment "Great tutorial!"
```

---

**Tutorial Version:** 1.0.0
**Last Updated:** 2025-10-30
**Estimated Time:** 50 minutes
**Difficulty:** Intermediate

**Contributors:**
- AI-Shell Team
- Community Contributors

**License:** MIT
