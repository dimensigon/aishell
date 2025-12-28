# Production Configuration Guide

Comprehensive configuration guide for AIShell production deployments with recommended settings, performance tuning parameters, and best practices.

## Table of Contents

1. [Database Connection Pooling](#database-connection-pooling)
2. [Query Timeout Configuration](#query-timeout-configuration)
3. [Backup Scheduling](#backup-scheduling)
4. [Alert Thresholds](#alert-thresholds)
5. [Log Rotation](#log-rotation)
6. [Performance Tuning Parameters](#performance-tuning-parameters)
7. [Resource Limits](#resource-limits)
8. [Caching Strategy](#caching-strategy)

---

## Database Connection Pooling

### PostgreSQL Connection Pool (Recommended)

```yaml
databases:
  production:
    type: postgres
    host: db.production.internal
    port: 5432
    database: ai_shell_prod
    pool:
      # Minimum idle connections in pool
      min: 10                          # Recommended: 10-20

      # Maximum total connections
      max: 100                         # Adjust based on server capacity

      # Timeout for acquiring connection (ms)
      acquireTimeoutMillis: 30000      # 30 seconds

      # Time before idle connection is closed (ms)
      idleTimeoutMillis: 30000         # 30 seconds

      # Timeout for creating new connection (ms)
      createTimeoutMillis: 3000        # 3 seconds

      # Timeout for destroying connection (ms)
      destroyTimeoutMillis: 5000       # 5 seconds

      # Interval for checking idle connections (ms)
      reapIntervalMillis: 1000         # 1 second

      # Retry interval for failed connection attempts (ms)
      createRetryIntervalMillis: 100   # 100 milliseconds
```

### Connection Pool Sizing Guidelines

**Traffic-Based Sizing:**
```yaml
# Low Traffic (< 100 requests/min)
low_traffic:
  min: 5
  max: 20

# Medium Traffic (100-1,000 requests/min)
medium_traffic:
  min: 10
  max: 50

# High Traffic (1,000-10,000 requests/min)
high_traffic:
  min: 20
  max: 100

# Very High Traffic (> 10,000 requests/min)
very_high_traffic:
  min: 50
  max: 200
```

**Server-Based Sizing:**
```yaml
# Based on server resources
formula: |
  max_connections = (available_cpu_cores * 2) + effective_spindle_count
  # For SSD: effective_spindle_count = 1
  # For HDD RAID: effective_spindle_count = number_of_disks

  Example with 8 CPU cores + SSD:
  max_connections = (8 * 2) + 1 = 17
  # Round up with buffer: 20-30 connections
```

### PgBouncer Configuration (Highly Recommended)

```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
ai_shell_prod = host=localhost port=5432 dbname=ai_shell_prod

[pgbouncer]
# Connection pooling mode
pool_mode = transaction              # Best for most workloads
# pool_mode = session                # For applications requiring session state
# pool_mode = statement              # For maximum connection reuse (advanced)

# Client connections
max_client_conn = 1000               # Maximum client connections
default_pool_size = 20               # Default pool size per database
min_pool_size = 10                   # Minimum pool size
reserve_pool_size = 5                # Reserved connections for emergencies
reserve_pool_timeout = 3             # Seconds before using reserve pool

# Database connections
max_db_connections = 100             # Must match PostgreSQL max_connections
max_user_connections = 100           # Per-user connection limit

# Timeouts
server_idle_timeout = 600            # 10 minutes
server_lifetime = 3600               # 1 hour - force connection renewal
server_connect_timeout = 15          # 15 seconds
query_timeout = 30                   # 30 seconds per query
client_idle_timeout = 600            # 10 minutes

# Security
auth_type = md5                      # or scram-sha-256 for PostgreSQL 10+
auth_file = /etc/pgbouncer/userlist.txt

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

### MySQL Connection Pool

```yaml
databases:
  mysql_prod:
    type: mysql
    host: mysql.production.internal
    port: 3306
    database: ai_shell_prod
    pool:
      connectionLimit: 100            # Maximum connections
      queueLimit: 0                   # Unlimited queue (0 = no limit)
      waitForConnections: true        # Queue requests when pool is full
      connectTimeout: 10000           # 10 seconds
      acquireTimeout: 10000           # 10 seconds
      timeout: 60000                  # 60 seconds idle timeout
```

### MongoDB Connection Pool

```yaml
databases:
  mongo_prod:
    type: mongodb
    url: mongodb://mongo.production.internal:27017/ai_shell_prod
    pool:
      minPoolSize: 10                 # Minimum connections
      maxPoolSize: 100                # Maximum connections
      maxIdleTimeMS: 30000            # 30 seconds
      waitQueueTimeoutMS: 30000       # 30 seconds
      serverSelectionTimeoutMS: 5000  # 5 seconds
```

### Redis Connection Pool

```yaml
cache:
  provider: redis
  url: redis://redis.production.internal:6379
  pool:
    min: 10                           # Minimum connections
    max: 50                           # Maximum connections
    acquireTimeoutMillis: 10000       # 10 seconds
    idleTimeoutMillis: 30000          # 30 seconds
    maxWaitingClients: 100            # Maximum queued requests
```

---

## Query Timeout Configuration

### Tiered Timeout Strategy

```yaml
performance:
  queryTimeout:
    # Default timeout for all queries
    default: 30000                    # 30 seconds

    # Read operations (SELECT)
    read: 15000                       # 15 seconds

    # Write operations (INSERT, UPDATE, DELETE)
    write: 45000                      # 45 seconds

    # Analytical/complex queries
    analytical: 300000                # 5 minutes

    # Administrative operations
    admin: 600000                     # 10 minutes

    # Backup/restore operations
    backup: 3600000                   # 1 hour
```

### Query-Type Specific Timeouts

```yaml
query_timeouts:
  # Simple lookups
  simple_select:
    timeout: 5000                     # 5 seconds
    pattern: "^SELECT .* FROM .* WHERE .* = \\?"

  # Aggregations
  aggregation:
    timeout: 30000                    # 30 seconds
    pattern: "^SELECT .* GROUP BY|COUNT\\(|SUM\\(|AVG\\("

  # Joins
  join_query:
    timeout: 60000                    # 1 minute
    pattern: "JOIN|INNER JOIN|LEFT JOIN|RIGHT JOIN"

  # Full table scans (discouraged)
  full_scan:
    timeout: 120000                   # 2 minutes
    pattern: "^SELECT .* FROM .* WHERE 1=1|^SELECT \\* FROM .* LIMIT"
    warning: true                     # Log warning
```

### Connection-Level Timeouts

```yaml
connection:
  # Initial connection establishment
  connectTimeout: 5000                # 5 seconds

  # Time to wait for query response
  socketTimeout: 30000                # 30 seconds

  # Idle connection timeout
  idleTimeout: 60000                  # 60 seconds

  # Statement timeout (PostgreSQL)
  statementTimeout: 30000             # 30 seconds

  # Lock timeout (PostgreSQL)
  lockTimeout: 10000                  # 10 seconds
```

---

## Backup Scheduling

### Backup Strategy Configuration

```yaml
backup:
  enabled: true

  # Full backup schedule
  full:
    enabled: true
    cron: "0 2 * * 0"                 # Every Sunday at 2 AM
    retention: 4                      # Keep 4 weekly full backups
    compression: gzip                 # gzip, bzip2, or none
    compressionLevel: 6               # 1-9 (9 = best compression)

  # Incremental backup schedule
  incremental:
    enabled: true
    cron: "0 2 * * 1-6"               # Monday-Saturday at 2 AM
    retention: 7                      # Keep 7 daily incrementals
    compression: gzip
    compressionLevel: 6

  # Transaction log backups (PostgreSQL WAL)
  transaction_log:
    enabled: true
    interval: 300000                  # Every 5 minutes
    retention: 7                      # Keep 7 days of logs

  # Configuration backup
  config:
    enabled: true
    cron: "0 3 * * *"                 # Daily at 3 AM
    retention: 30                     # Keep 30 days
```

### Cloud Backup Configuration

```yaml
backup:
  cloud:
    enabled: true

    # Primary cloud provider
    primary:
      provider: aws-s3                # aws-s3, azure-blob, or gcp-storage
      bucket: ai-shell-backups-prod
      region: us-east-1
      encryption: AES256              # Server-side encryption
      storageClass: STANDARD_IA       # STANDARD, STANDARD_IA, or GLACIER
      versioning: true                # Enable object versioning

    # Secondary cloud provider (geo-redundancy)
    secondary:
      provider: azure-blob
      container: ai-shell-backups-prod
      region: eastus
      encryption: true

  # Lifecycle policies
  lifecycle:
    transitionToArchive: 90           # Days before archiving
    transitionToDeepArchive: 180      # Days before deep archive
    expiration: 365                   # Days before deletion
```

### Backup Verification

```yaml
backup:
  verification:
    enabled: true

    # Verify backup integrity
    checksum: true                    # Calculate and verify checksums
    testRestore: true                 # Perform test restore
    testRestoreSchedule: "0 4 * * 0"  # Weekly on Sunday at 4 AM
    testRestoreRetention: 7           # Keep test results for 7 days

    # Notification on verification failure
    notifications:
      email: true
      slack: true
      pagerduty: true
```

---

## Alert Thresholds

### System Resource Alerts

```yaml
alerts:
  # CPU usage
  cpu:
    warning:
      threshold: 70                   # 70% CPU usage
      duration: 300000                # Sustained for 5 minutes
      action: notify
    critical:
      threshold: 90                   # 90% CPU usage
      duration: 60000                 # Sustained for 1 minute
      action: [notify, page]

  # Memory usage
  memory:
    warning:
      threshold: 80                   # 80% memory used
      duration: 300000                # Sustained for 5 minutes
      action: notify
    critical:
      threshold: 95                   # 95% memory used
      duration: 60000                 # Sustained for 1 minute
      action: [notify, page]

  # Disk usage
  disk:
    warning:
      threshold: 80                   # 80% disk used
      duration: 600000                # Check every 10 minutes
      action: notify
    critical:
      threshold: 90                   # 90% disk used
      duration: 300000                # Check every 5 minutes
      action: [notify, page, scale]

  # Disk I/O
  disk_io:
    warning:
      iops: 5000                      # 5000 IOPS
      latency: 10                     # 10ms average latency
      action: notify
    critical:
      iops: 10000                     # 10000 IOPS
      latency: 50                     # 50ms average latency
      action: [notify, page]
```

### Database Performance Alerts

```yaml
alerts:
  # Connection pool
  database_connections:
    warning:
      threshold: 70                   # 70% of max connections
      duration: 300000                # Sustained for 5 minutes
      action: notify
    critical:
      threshold: 90                   # 90% of max connections
      duration: 60000                 # Sustained for 1 minute
      action: [notify, page, scale]

  # Query latency
  query_latency:
    warning:
      p95: 1000                       # 95th percentile > 1 second
      p99: 2000                       # 99th percentile > 2 seconds
      action: notify
    critical:
      p95: 5000                       # 95th percentile > 5 seconds
      p99: 10000                      # 99th percentile > 10 seconds
      action: [notify, page]

  # Slow queries
  slow_queries:
    warning:
      count: 10                       # 10 slow queries per minute
      threshold: 1000                 # Queries over 1 second
      action: [notify, log]
    critical:
      count: 50                       # 50 slow queries per minute
      threshold: 5000                 # Queries over 5 seconds
      action: [notify, page, log]

  # Database replication lag
  replication_lag:
    warning:
      threshold: 30                   # 30 seconds lag
      action: notify
    critical:
      threshold: 300                  # 5 minutes lag
      action: [notify, page]
```

### Application Health Alerts

```yaml
alerts:
  # Error rate
  error_rate:
    warning:
      threshold: 1                    # 1% error rate
      window: 300000                  # Over 5 minutes
      action: notify
    critical:
      threshold: 5                    # 5% error rate
      window: 60000                   # Over 1 minute
      action: [notify, page]

  # Request rate
  request_rate:
    warning:
      threshold: 1000                 # 1000 requests/second
      action: [notify, scale]
    critical:
      threshold: 5000                 # 5000 requests/second
      action: [notify, page, scale]

  # Cache hit ratio
  cache_hit_ratio:
    warning:
      threshold: 70                   # Below 70% hit rate
      duration: 600000                # Sustained for 10 minutes
      action: notify
    critical:
      threshold: 50                   # Below 50% hit rate
      duration: 300000                # Sustained for 5 minutes
      action: [notify, investigate]
```

### Alert Channels

```yaml
notifications:
  # Email notifications
  email:
    enabled: true
    from: alerts@ai-shell.example.com
    to:
      warning:
        - team@example.com
      critical:
        - team@example.com
        - oncall@example.com
    smtp:
      host: smtp.example.com
      port: 587
      secure: true

  # Slack notifications
  slack:
    enabled: true
    webhook: ${SLACK_WEBHOOK_URL}
    channel:
      warning: "#ai-shell-warnings"
      critical: "#ai-shell-critical"
    mentions:
      critical: "@here"

  # PagerDuty (for critical alerts)
  pagerduty:
    enabled: true
    apiKey: ${PAGERDUTY_API_KEY}
    serviceKey: ${PAGERDUTY_SERVICE_KEY}
    escalationPolicy: ai-shell-oncall

  # Webhooks
  webhook:
    enabled: true
    url: https://monitoring.example.com/webhooks/alerts
    method: POST
    headers:
      Authorization: "Bearer ${WEBHOOK_TOKEN}"
```

---

## Log Rotation

### Application Logs

```yaml
logging:
  # Main application log
  application:
    destination: /var/log/ai-shell/app.log
    level: info
    format: json
    rotation:
      enabled: true
      frequency: daily               # daily, weekly, or size-based
      datePattern: YYYY-MM-DD
      maxFiles: 30                   # Keep 30 days
      maxSize: 100m                  # Max file size before rotation
      compress: true                 # gzip old logs
      zippedArchive: true

  # Error log
  error:
    destination: /var/log/ai-shell/error.log
    level: error
    format: json
    rotation:
      enabled: true
      frequency: daily
      maxFiles: 90                   # Keep 90 days
      maxSize: 50m
      compress: true
```

### Audit Logs

```yaml
security:
  audit:
    enabled: true
    destination: /var/log/ai-shell/audit.log
    format: json
    rotation:
      enabled: true
      frequency: daily
      maxFiles: 365                  # Keep 1 year (compliance)
      maxSize: 100m
      compress: true
      archiveTo: s3://audit-logs-archive/
      retentionPolicy:
        s3: 2555                     # 7 years in S3 (compliance)
        glacier: 3650                # 10 years in Glacier
```

### Query Logs

```yaml
query_logging:
  enabled: true
  destination: /var/log/ai-shell/query.log
  format: json
  includeParameters: false           # Security: don't log query parameters
  rotation:
    enabled: true
    frequency: daily
    maxFiles: 7                      # Keep 7 days
    maxSize: 500m
    compress: true
```

### Access Logs

```yaml
access_logging:
  enabled: true
  destination: /var/log/ai-shell/access.log
  format: combined                   # Apache combined log format
  rotation:
    enabled: true
    frequency: daily
    maxFiles: 30
    maxSize: 200m
    compress: true
```

---

## Performance Tuning Parameters

### Node.js Runtime Optimization

```bash
# Environment variables
export NODE_ENV=production
export NODE_OPTIONS="--max-old-space-size=4096"  # 4GB heap
export UV_THREADPOOL_SIZE=16                     # Increase thread pool
```

```yaml
# Configuration
performance:
  runtime:
    heapSize: 4096                   # MB
    threadPoolSize: 16               # UV_THREADPOOL_SIZE
    gcInterval: 300000               # Force GC every 5 minutes
    maxSockets: 1000                 # Max concurrent sockets
    keepAlive: true                  # Keep TCP connections alive
    keepAliveInitialDelay: 300000    # 5 minutes
```

### Query Execution Optimization

```yaml
performance:
  queries:
    # Query execution
    timeout: 30000                   # 30 seconds default
    maxQuerySize: 1048576            # 1MB max query size
    maxResultSize: 10485760          # 10MB max result size

    # Query caching
    cacheEnabled: true
    cacheTTL: 3600                   # 1 hour
    cacheMaxSize: 1000               # Max cached queries

    # Query optimization
    autoOptimize: true               # Enable auto-optimization
    optimizationThreshold: 1000      # Optimize queries over 1 second
    explainAnalyze: true             # Use EXPLAIN ANALYZE

    # Parallel execution
    parallelQueries: true
    maxParallel: 4                   # Max parallel queries

    # Result streaming
    streamResults: true              # Stream large result sets
    streamChunkSize: 1000            # Rows per chunk
```

### Caching Configuration

```yaml
caching:
  enabled: true
  provider: redis

  # Connection
  url: redis://redis.production.internal:6379
  password: ${REDIS_PASSWORD}
  db: 0

  # Pool
  pool:
    min: 10
    max: 50

  # TTL strategies
  strategies:
    default:
      ttl: 3600                      # 1 hour
    frequent:
      ttl: 7200                      # 2 hours for frequently accessed
    static:
      ttl: 86400                     # 24 hours for static data
    analytical:
      ttl: 600                       # 10 minutes for analytics

  # Cache invalidation
  invalidation:
    onWrite: true                    # Invalidate on data changes
    onSchema: true                   # Invalidate on schema changes
    pattern: true                    # Pattern-based invalidation

  # Memory management
  maxMemory: 512mb                   # Max Redis memory
  maxMemoryPolicy: allkeys-lru       # Eviction policy

  # Persistence
  persistence:
    enabled: true
    strategy: aof                    # AOF or RDB
    fsync: everysec                  # every sec, always, or no
```

---

## Resource Limits

### System Resource Limits

```yaml
resources:
  # CPU
  cpu:
    limit: 8                         # CPU cores
    request: 2                       # Minimum cores
    throttling: false                # Disable CPU throttling

  # Memory
  memory:
    limit: 16Gi                      # Maximum memory
    request: 4Gi                     # Minimum memory
    swappiness: 10                   # Reduce swapping

  # Disk
  disk:
    limit: 500Gi                     # Maximum disk space
    iops: 10000                      # Provisioned IOPS
    throughput: 500                  # MB/s

  # Network
  network:
    bandwidth: 1000                  # Mbps
    maxConnections: 10000            # Max TCP connections
```

### Application Limits

```yaml
limits:
  # Requests
  maxConcurrentRequests: 1000        # Max concurrent requests
  requestQueueSize: 5000             # Max queued requests
  maxRequestSize: 10485760           # 10MB max request size
  maxResponseSize: 104857600         # 100MB max response size

  # Connections
  maxDatabaseConnections: 100        # Per database
  maxRedisConnections: 50
  maxHttpConnections: 500

  # Rate limiting
  rateLimitPerMinute: 100            # Per IP
  rateLimitPerHour: 1000
  rateLimitPerDay: 10000

  # File operations
  maxFileSize: 104857600             # 100MB max upload
  maxFiles: 100                      # Max files per request
```

### PostgreSQL Tuning

```sql
-- postgresql.conf (for 16GB RAM server)
max_connections = 200
shared_buffers = 4GB                 -- 25% of RAM
effective_cache_size = 12GB          -- 75% of RAM
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1               -- For SSD
effective_io_concurrency = 200       -- For SSD
work_mem = 64MB                      -- Per operation
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4
```

---

## Caching Strategy

### Multi-Layer Caching

```yaml
caching:
  # Layer 1: In-memory cache (application)
  memory:
    enabled: true
    maxSize: 100                     # 100 items
    ttl: 60000                       # 1 minute
    strategy: lru

  # Layer 2: Redis cache (shared)
  redis:
    enabled: true
    maxSize: 10000                   # 10,000 items
    ttl: 3600                        # 1 hour
    strategy: allkeys-lru

  # Layer 3: Database query results
  database:
    enabled: true
    preparedStatements: true
    resultCache: true
    resultCacheTTL: 300              # 5 minutes
```

### Cache Warming

```yaml
cache_warming:
  enabled: true
  schedule: "0 1 * * *"              # Daily at 1 AM
  queries:
    - name: "frequent_users"
      query: "SELECT * FROM users WHERE active = true"
      ttl: 86400                     # 24 hours
    - name: "dashboard_stats"
      query: "SELECT COUNT(*) FROM orders GROUP BY status"
      ttl: 3600                      # 1 hour
```

---

**Document Version:** 1.0.0
**Last Updated:** October 29, 2025
**Maintained By:** AIShell DevOps Team
