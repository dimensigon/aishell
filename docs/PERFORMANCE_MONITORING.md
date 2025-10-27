# Performance Monitoring & Analytics

AI-Shell now includes comprehensive performance monitoring and database health check features.

## Features

### 1. Real-Time Performance Monitoring

Monitor your database performance in real-time with detailed metrics:

```bash
# Start basic monitoring (updates every 5 seconds)
ai-shell perf monitor

# Custom update interval
ai-shell perf monitor --interval 10

# Show specific metrics only
ai-shell perf monitor --metrics connections,qps,query-time

# Launch visual dashboard
ai-shell perf monitor --dashboard
```

**Metrics Tracked:**
- Active connections
- Queries per second (QPS)
- Average query time
- Slow queries count
- Cache hit rate
- Database size and growth
- Lock waits
- CPU and memory usage

### 2. Slow Query Detection & Analysis

Identify and optimize slow queries:

```bash
# Find queries slower than 1 second
ai-shell perf slow-queries

# Custom threshold (500ms)
ai-shell perf slow-queries --threshold 500

# Show top 20 slow queries
ai-shell perf slow-queries --limit 20
```

**Features:**
- Automatic slow query detection
- Frequency tracking
- AI-powered optimization suggestions
- Query rewrite recommendations

### 3. Query Performance Analysis

Deep dive into query performance:

```bash
# Analyze a specific query
ai-shell perf analyze "SELECT * FROM users WHERE email = 'test@example.com'"
```

**Analysis Includes:**
- Execution plan (EXPLAIN output)
- Estimated cost
- Missing indexes
- Optimization suggestions
- AI-generated query rewrites

### 4. Index Recommendations

Get smart index recommendations based on query patterns:

```bash
# Analyze query patterns and suggest indexes
ai-shell perf indexes
```

**Provides:**
- Most beneficial indexes
- Estimated performance improvement
- CREATE INDEX statements
- Reasoning for each recommendation

### 5. Connection Pool Monitoring

Monitor connection pool health:

```bash
# Show connection pool statistics
ai-shell perf pool
```

**Statistics:**
- Total/active/idle connections
- Waiting queries
- Average and max wait times

### 6. Database Health Checks

Comprehensive database health monitoring:

```bash
# Run full health check
ai-shell health check

# Get actionable recommendations
ai-shell health recommendations

# Auto-fix issues
ai-shell health fix --auto

# Fix specific issues
ai-shell health fix --issues issue_1,issue_2
```

**Checks Include:**
- Database connectivity
- Disk space usage
- Table bloat
- Missing indexes on foreign keys
- Unused indexes
- Outdated statistics
- Replication lag (if applicable)
- Lock contentions

**Health Score:**
- 100-80: Healthy ✓
- 79-50: Warning ⚠️
- <50: Critical ✗

### 7. Query History & Analytics

Track and analyze all queries:

```bash
# Show recent query history
ai-shell history list

# Show more queries with pagination
ai-shell history list --limit 50 --offset 0

# Analyze query patterns
ai-shell history analyze

# Search query logs
ai-shell history search "SELECT.*users" --ignore-case

# Export query logs
ai-shell history export json ./queries.json
ai-shell history export csv ./queries.csv

# Clear old logs
ai-shell history clear
```

**Analytics Include:**
- Total queries and average duration
- Slowest/fastest queries
- Most frequent queries
- Query type distribution (SELECT, INSERT, etc.)
- Peak usage times
- Error rate
- Performance trend (improving/degrading/stable)

### 8. Interactive Dashboard

Launch a full-featured terminal dashboard:

```bash
# Launch dashboard with 5-second refresh
ai-shell dashboard

# Custom refresh interval
ai-shell dashboard --interval 10
```

**Dashboard Features:**
- Real-time metrics display
- Live query log
- Slow query alerts
- Resource usage graphs
- Interactive terminal UI
- Keyboard shortcuts

## Implementation Details

### Architecture

```
src/cli/
├── performance-monitor.ts   # Real-time monitoring & metrics
├── query-logger.ts          # Query logging & analytics
├── health-checker.ts        # Health checks & auto-fix
├── dashboard-ui.ts          # Terminal dashboard UI
├── commands.ts              # CLI command definitions
└── performance.ts           # Module exports
```

### Key Components

**PerformanceMonitor:**
- Collects real-time metrics
- Detects slow queries
- Provides optimization suggestions
- Uses LLM for intelligent recommendations

**QueryLogger:**
- Logs all queries with timing
- Stores in StateManager with TTL
- Provides analytics and search
- Exports to CSV/JSON

**HealthChecker:**
- Runs comprehensive checks
- Generates recommendations
- Auto-fixes common issues
- Prioritizes by impact

**DashboardUI:**
- Uses blessed for terminal UI
- Real-time metric updates
- ASCII charts and graphs
- Interactive navigation

### Integration with Existing Components

**StateManager:**
- Stores query logs and metrics
- Provides TTL for automatic cleanup
- Enables querying by metadata
- Persists to disk automatically

**LLMMCPBridge:**
- Generates optimization suggestions
- Rewrites queries for better performance
- Provides intelligent recommendations
- Contextual analysis

**EventEmitter:**
- Real-time metric updates
- Slow query alerts
- Health issue notifications
- Dashboard synchronization

## Configuration

### StateManager Configuration

```typescript
const stateManager = new StateManager({
  enablePersistence: true,
  persistencePath: './.ai-shell/state.json',
  autoSaveInterval: 5000,
  enableTTL: true,
  ttlCheckInterval: 10000
});
```

### QueryLogger Configuration

```typescript
const queryLogger = new QueryLogger(stateManager, {
  slowQueryThreshold: 1000,    // 1 second
  maxLogsInMemory: 10000,
  persistLogs: true,
  logPath: './.ai-shell/logs'
});
```

## Usage Examples

### Example 1: Daily Health Check

```bash
# Morning routine
ai-shell health check
ai-shell health recommendations
ai-shell health fix --auto

# Review slow queries
ai-shell perf slow-queries --limit 10
```

### Example 2: Performance Investigation

```bash
# Start monitoring
ai-shell perf monitor --dashboard

# In another terminal, analyze specific query
ai-shell perf analyze "SELECT * FROM orders WHERE created_at > '2024-01-01'"

# Check index recommendations
ai-shell perf indexes
```

### Example 3: Query Pattern Analysis

```bash
# Export all queries for analysis
ai-shell history export json ./queries.json

# Analyze patterns
ai-shell history analyze

# Find specific queries
ai-shell history search "DELETE" --ignore-case
```

## Performance Tips

1. **Monitor Regularly**: Set up daily health checks
2. **Address Slow Queries**: Fix queries over 1 second
3. **Add Missing Indexes**: Follow index recommendations
4. **Watch Bloat**: Run VACUUM on bloated tables
5. **Track Trends**: Monitor performance trend over time
6. **Use Dashboard**: Visual monitoring catches issues early

## Troubleshooting

### High Memory Usage

```bash
# Check query log size
ai-shell history list --limit 1

# Clear old logs if needed
ai-shell history clear
```

### Slow Performance

```bash
# Run health check
ai-shell health check

# Check for missing indexes
ai-shell perf indexes

# Analyze slow queries
ai-shell perf slow-queries
```

### Connection Issues

```bash
# Check pool statistics
ai-shell perf pool

# Monitor active connections
ai-shell perf monitor --metrics connections
```

## API Reference

### PerformanceMonitor

```typescript
class PerformanceMonitor {
  // Monitor performance in real-time
  async monitor(options: MonitorOptions): Promise<void>

  // Get slow queries
  async slowQueries(threshold: number, limit?: number): Promise<SlowQuery[]>

  // Analyze query performance
  async analyzeQuery(sql: string): Promise<QueryAnalysis>

  // Get index recommendations
  async indexRecommendations(): Promise<IndexSuggestion[]>

  // Get connection pool stats
  async connectionPool(): Promise<PoolStats>

  // Stop monitoring
  stop(): void

  // Get metrics history
  getHistory(limit?: number): PerformanceMetrics[]
}
```

### QueryLogger

```typescript
class QueryLogger {
  // Log a query execution
  async logQuery(query: string, duration: number, result?: any): Promise<void>

  // Get query history
  async getHistory(limit?: number, offset?: number): Promise<QueryHistory>

  // Analyze query patterns
  async analyze(): Promise<QueryAnalytics>

  // Export query logs
  async export(format: 'csv' | 'json', filepath: string): Promise<void>

  // Clear all logs
  clearLogs(): number

  // Search query logs
  search(pattern: string, options?: SearchOptions): QueryLog[]

  // Get slow queries
  getSlowQueries(threshold?: number, limit?: number): QueryLog[]
}
```

### HealthChecker

```typescript
class HealthChecker {
  // Run comprehensive health check
  async check(): Promise<HealthReport>

  // Get recommendations
  async recommendations(): Promise<Recommendation[]>

  // Auto-fix issues
  async autoFix(issueIds?: string[], options?: FixOptions): Promise<FixResult[]>
}
```

## Future Enhancements

- [ ] Alerting system with notifications
- [ ] Historical metrics storage
- [ ] Query performance regression detection
- [ ] Automatic index creation
- [ ] Integration with monitoring tools (Prometheus, Grafana)
- [ ] Machine learning for anomaly detection
- [ ] Custom metric thresholds
- [ ] Multi-database support
- [ ] Distributed tracing integration
- [ ] Cost estimation for cloud databases

## Contributing

To add new metrics or checks:

1. Add metric to `PerformanceMetrics` interface
2. Implement collection in `PerformanceMonitor`
3. Update dashboard display
4. Add CLI command if needed
5. Update documentation

## License

MIT
