# Enhanced Monitoring Dashboard

> **Priority:** P3 Feature  
> **Status:** Production Ready  
> **Version:** 1.0.0

## Overview

The Enhanced Monitoring Dashboard is a production-ready, real-time terminal user interface (TUI) for comprehensive database monitoring. Built with the blessed library, it provides rich visualizations, interactive charts, and customizable layouts for monitoring database performance, connections, queries, and system health.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Dashboard Components](#dashboard-components)
- [Layouts](#layouts)
- [Keyboard Navigation](#keyboard-navigation)
- [Configuration](#configuration)
- [Themes](#themes)
- [Alerts](#alerts)
- [Metrics](#metrics)
- [Export & Snapshots](#export--snapshots)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Features

### Core Features

- **Real-Time Monitoring**: Updates every 1-5 seconds with live metrics
- **Multi-Panel Layout**: 6 specialized panels for different aspects of monitoring
- **Interactive Charts**: ASCII-based charts for performance visualization
- **Alert System**: Color-coded alerts with severity indicators
- **Keyboard Navigation**: Full keyboard control with shortcuts
- **Customizable Layouts**: 4 predefined layouts + custom layouts
- **Theme Support**: 4 built-in themes (dark, light, ocean, forest)
- **Export Functionality**: Snapshot exports in JSON format
- **Connection Pool Stats**: Real-time connection tracking
- **Query Performance**: Query execution monitoring and analysis
- **System Health**: CPU, memory, and response time tracking
- **Query History**: Recent queries with filtering

### Advanced Features

- **Metrics History**: Configurable history size (default: 100 points)
- **Auto-Refresh**: Configurable refresh intervals
- **Panel Focus**: Tab-based navigation between panels
- **Scrollable Panels**: Scroll through long data sets
- **Error Resilience**: Graceful handling of connection failures
- **Event System**: Extensible event-based architecture

## Installation

The Enhanced Dashboard is included in AI Shell. No additional installation required.

```bash
# Ensure AI Shell is installed
npm install -g ai-shell

# Or install locally
npm install ai-shell
```

## Quick Start

### Basic Usage

```bash
# Start dashboard with default settings
ai-shell dashboard start

# Start with specific layout
ai-shell dashboard start --layout compact

# Start with custom refresh interval
ai-shell dashboard start --interval 5000

# Start with specific theme
ai-shell dashboard start --theme ocean
```

### Programmatic Usage

```typescript
import { startDashboard } from './src/cli/dashboard-enhanced';
import { PerformanceMonitor } from './src/cli/performance-monitor';
import { HealthMonitor } from './src/cli/health-monitor';
import { QueryLogger } from './src/cli/query-logger';
import { StateManager } from './src/core/state-manager';

// Initialize dependencies
const stateManager = new StateManager();
const performanceMonitor = new PerformanceMonitor(stateManager);
const healthMonitor = new HealthMonitor(dbManager, stateManager);
const queryLogger = new QueryLogger(stateManager);

// Start dashboard
const dashboard = await startDashboard(
  performanceMonitor,
  healthMonitor,
  queryLogger,
  stateManager,
  {
    refreshInterval: 2000,
    layout: 'default',
    theme: 'dark'
  }
);

// Dashboard is now running...
```

## Dashboard Components

### 1. Connection Panel

Displays real-time connection pool statistics:

```
┌─ 🔗 Connection Pool ──────────────┐
│                                   │
│ Total Connections: 20             │
│                                   │
│ Active: 5 (25.0%)                │
│ Idle: 15                         │
│ Waiting: 0                       │
│                                   │
│ Avg Wait Time: 10ms              │
│ Max Wait Time: 50ms              │
│                                   │
│ Pool Utilization:                │
│ █████░░░░░░░░░░░░░░░             │
└───────────────────────────────────┘
```

**Metrics:**
- Total connections in pool
- Active connections (with percentage)
- Idle connections
- Waiting queries
- Average wait time
- Maximum wait time
- Visual utilization bar

**Color Coding:**
- Green: < 60% utilization
- Yellow: 60-80% utilization
- Red: > 80% utilization

### 2. Performance Panel

Shows query performance metrics:

```
┌─ ⚡ Performance Metrics ──────────┐
│                                   │
│ Queries/Second:                  │
│ 10.52                            │
│                                   │
│ Avg Query Time:                  │
│ 124.35ms                         │
│                                   │
│ Slow Queries:                    │
│ 0                                │
│                                   │
│ Cache Hit Rate:                  │
│ 78.5%                            │
│                                   │
│ Lock Waits:                      │
│ 0                                │
└───────────────────────────────────┘
```

**Metrics:**
- Queries per second
- Average query time
- Slow query count
- Cache hit rate
- Lock wait count

**Thresholds:**
- QPS: Green < 50, Yellow 50-100, Red > 100
- Query Time: Green < 200ms, Yellow 200-500ms, Red > 500ms
- Cache Hit: Red < 50%, Yellow 50-70%, Green > 70%

### 3. System Health Panel

Monitors overall system health:

```
┌─ 💚 System Health ────────────────┐
│                                   │
│ Status: ✓ HEALTHY                │
│                                   │
│ Uptime:                          │
│ 2h 34m 15s                       │
│                                   │
│ CPU Usage:                       │
│ ████████░░░░░░░░░░░░ 45.2%       │
│                                   │
│ Memory Usage:                    │
│ ████████████░░░░░░░░ 62.8%       │
│                                   │
│ Response Time: 45ms              │
│ Error Rate: 0.02%                │
└───────────────────────────────────┘
```

**Status Indicators:**
- ✓ Healthy (Green)
- ⚠ Warning (Yellow)
- ✗ Critical (Red)

**Metrics:**
- Overall health status
- System uptime
- CPU usage (with bar)
- Memory usage (with bar)
- Response time
- Error rate

### 4. Alerts Panel

Displays active alerts with severity:

```
┌─ 🚨 Alerts ───────────────────────┐
│                                   │
│ 🔴 [14:32:15] High CPU usage     │
│    detected: 85%                  │
│                                   │
│ 🟡 [14:30:42] Slow query         │
│    detected: 1523ms               │
│                                   │
│ 🔵 [14:28:11] Cache hit rate     │
│    below threshold                │
└───────────────────────────────────┘
```

**Alert Severities:**
- 🔴 Critical (Red)
- 🟡 Warning (Yellow)
- 🔵 Info (Cyan)

**Alert Sources:**
- Performance monitor
- Health checks
- Query logger
- Custom alerts

### 5. Query Log Panel

Shows recent query execution history:

```
┌─ 📝 Recent Queries ───────────────┐
│                                   │
│ 1. [120ms] 14:35:22              │
│    SELECT * FROM users WHERE...  │
│                                   │
│ 2. [45ms] 14:35:20               │
│    UPDATE orders SET status...   │
│                                   │
│ 3. [890ms] 14:35:18 ✗            │
│    SELECT COUNT(*) FROM logs...  │
└───────────────────────────────────┘
```

**Features:**
- Timestamp for each query
- Execution time (color-coded)
- Error indicator (✗)
- Query preview (60 chars)
- Scrollable history

**Color Coding:**
- Green: < 500ms
- Yellow: 500-1000ms
- Red: > 1000ms

### 6. Charts Panel

Visualizes performance trends:

```
┌─ 📊 Performance Charts ───────────┐
│                                   │
│ QPS:                             │
│  20 │ █                          │
│  15 │ ██                         │
│  10 │ ███                        │
│   5 │ ████                       │
│   0 └────────────────            │
│                                   │
│ Avg Query Time (ms):             │
│ 200 │     █                      │
│ 150 │    ██                      │
│ 100 │   ███                      │
│  50 │  ████                      │
│   0 └────────────────            │
└───────────────────────────────────┘
```

**Charts Available:**
- Queries per second
- Average query time
- CPU usage
- Memory usage

**Features:**
- Mini ASCII charts
- Auto-scaling
- Configurable history
- Color-coded trends

## Layouts

The dashboard supports 4 predefined layouts:

### Default Layout

Balanced layout showing all panels:

```
┌─────────────┬─────────────┬─────────────┐
│ Connection  │ Performance │ System      │
│   Pool      │   Metrics   │   Health    │
│             │             │             │
├─────────────┴──────┬──────┴─────────────┤
│      Alerts        │   Query Log        │
│                    │                    │
├────────────────────┴────────────────────┤
│         Performance Charts              │
│                                         │
└─────────────────────────────────────────┘
```

### Compact Layout

Minimalist layout for small screens:

```
┌──────────────┬──────────────┐
│ Performance  │ System       │
│   Metrics    │   Health     │
│              │              │
├──────────────┴──────────────┤
│        Alerts                │
│                              │
└──────────────────────────────┘
```

### Detailed Layout

Focus on charts and analysis:

```
┌────────────────────┬──────────┐
│                    │ Perform  │
│                    │  -ance   │
│   Charts           ├──────────┤
│                    │ Connect  │
│                    │  -ions   │
├────────────────────┼──────────┤
│   Query Log        │ Alerts   │
│                    │          │
└────────────────────┴──────────┘
```

### Monitoring Layout

Real-time monitoring focus:

```
┌────────────────────────────────┐
│     Performance Charts         │
│                                │
├──────────┬──────────┬──────────┤
│ Perform  │ Connect  │ System   │
│  -ance   │  -ions   │  Health  │
└──────────┴──────────┴──────────┘
```

## Keyboard Navigation

### Global Shortcuts

| Key | Action |
|-----|--------|
| `Tab` | Next panel |
| `Shift+Tab` | Previous panel |
| `L` | Change layout |
| `E` | Export snapshot |
| `R` | Refresh now |
| `C` | Configure |
| `Q` | Quit dashboard |
| `Ctrl+C` | Force quit |

### Panel Navigation

| Key | Action |
|-----|--------|
| `↑` | Scroll up |
| `↓` | Scroll down |
| `PgUp` | Page up |
| `PgDn` | Page down |

### Tips

- Use `Tab` to cycle through panels
- Focused panel has yellow border
- Scroll long lists with arrow keys
- Press `L` repeatedly to cycle layouts
- Press `E` to save current state

## Configuration

### Configuration Options

```typescript
interface DashboardConfig {
  refreshInterval?: number;    // Update interval (ms), default: 2000
  layout?: string;             // Layout name, default: 'default'
  theme?: string;              // Theme name, default: 'dark'
  showTimestamps?: boolean;    // Show timestamps, default: true
  enableAlerts?: boolean;      // Enable alerts, default: true
  historySize?: number;        // Metrics history, default: 100
  exportPath?: string;         // Export directory, default: './dashboard-exports'
}
```

### Configuration File

Create `dashboard-config.json`:

```json
{
  "refreshInterval": 3000,
  "layout": "detailed",
  "theme": "ocean",
  "showTimestamps": true,
  "enableAlerts": true,
  "historySize": 200,
  "exportPath": "/var/log/dashboard"
}
```

Load config:

```bash
ai-shell dashboard start --config dashboard-config.json
```

### Programmatic Configuration

```typescript
// Update config at runtime
dashboard.configure({
  refreshInterval: 5000,
  theme: 'forest'
});
```

## Themes

### Available Themes

#### Dark Theme (Default)

```
Background: Black
Foreground: White
Borders: Cyan
```

#### Light Theme

```
Background: White
Foreground: Black
Borders: Blue
```

#### Ocean Theme

```
Background: #001f3f (Deep Blue)
Foreground: #7FDBFF (Light Blue)
Borders: #0074D9 (Blue)
```

#### Forest Theme

```
Background: #001a00 (Deep Green)
Foreground: #2ECC40 (Green)
Borders: #01FF70 (Bright Green)
```

### Custom Themes

Create custom theme:

```typescript
// Add to theme configuration
const customTheme = {
  bg: '#1a1a1a',
  fg: '#e0e0e0',
  border: '#ff6b6b'
};
```

## Alerts

### Alert System

#### Alert Severities

1. **Info** (Blue 🔵)
   - Informational messages
   - Non-critical events
   - Status updates

2. **Warning** (Yellow 🟡)
   - Performance degradation
   - Threshold warnings
   - Resource constraints

3. **Critical** (Red 🔴)
   - Service failures
   - Data integrity issues
   - Security concerns

### Alert Sources

- **Performance Monitor**: QPS, query time, cache hit rate
- **Health Monitor**: CPU, memory, response time
- **Query Logger**: Slow queries, query errors
- **Custom**: User-defined alerts

### Adding Custom Alerts

```typescript
dashboard.addAlert({
  severity: 'warning',
  message: 'Custom alert message',
  source: 'custom-module',
  resolved: false
});
```

### Alert Configuration

```typescript
// Configure alert thresholds
healthMonitor.configureAlerts({
  enabled: true,
  thresholds: {
    responseTime: 1000,    // ms
    errorRate: 5,          // percentage
    cpuUsage: 80,          // percentage
    memoryUsage: 85,       // percentage
    diskSpace: 90          // percentage
  }
});
```

## Metrics

### Tracked Metrics

#### Connection Metrics
- Total connections
- Active connections
- Idle connections
- Waiting queries
- Wait times (avg, max)

#### Performance Metrics
- Queries per second (QPS)
- Average query time
- Slow query count
- Cache hit rate
- Lock waits

#### System Metrics
- CPU usage (%)
- Memory usage (%)
- Response time (ms)
- Error rate (%)
- Uptime

#### Query Metrics
- Query count
- Query types (SELECT, INSERT, UPDATE, DELETE)
- Query duration distribution
- Error count

### Metrics History

Metrics are stored in memory with configurable size:

```typescript
// Configure history size
dashboard.configure({
  historySize: 200  // Keep last 200 data points
});

// Access metrics history programmatically
const qpsHistory = dashboard['metricsHistory'].get('qps');
```

### Metrics Export

Export metrics for analysis:

```typescript
// Export current snapshot
const filepath = await dashboard.export();

// Export with custom filename
const filepath = await dashboard.export('metrics-2024-01-15.json');
```

## Export & Snapshots

### Snapshot Format

Exported snapshots include:

```json
{
  "timestamp": 1705334400000,
  "layout": "default",
  "stats": {
    "uptime": 7200000,
    "totalQueries": 15234,
    "activeConnections": 12,
    "avgResponseTime": 124.5,
    "errorRate": 0.02,
    "cacheHitRate": 0.785
  },
  "alerts": [
    {
      "id": "alert_1705334400_abc123",
      "severity": "warning",
      "message": "High CPU usage detected",
      "timestamp": 1705334380000,
      "source": "performance",
      "resolved": false
    }
  ],
  "metrics": {
    "current": { /* latest metrics */ },
    "history": {
      "qps": [ /* QPS history */ ],
      "avgQueryTime": [ /* Query time history */ ],
      "cpu": [ /* CPU history */ ],
      "memory": [ /* Memory history */ ]
    }
  },
  "queryHistory": {
    "logs": [ /* Recent queries */ ],
    "total": 15234,
    "page": 1,
    "pageSize": 50
  }
}
```

### Export Commands

```bash
# Export via keyboard
# Press 'E' while dashboard is running

# Export via CLI
ai-shell dashboard export output.json

# Export with timestamp
ai-shell dashboard export "snapshot-$(date +%Y%m%d-%H%M%S).json"
```

### Automated Exports

Schedule automatic exports:

```typescript
// Export every hour
setInterval(async () => {
  const timestamp = new Date().toISOString();
  await dashboard.export(`auto-${timestamp}.json`);
}, 3600000);
```

## API Reference

### EnhancedDashboard Class

```typescript
class EnhancedDashboard extends EventEmitter {
  constructor(
    performanceMonitor: PerformanceMonitor,
    healthMonitor: HealthMonitor,
    queryLogger: QueryLogger,
    stateManager: StateManager,
    config?: DashboardConfig
  )

  // Lifecycle
  async start(): Promise<void>
  stop(): void

  // Layout
  async changeLayout(layoutName: string): Promise<void>

  // Configuration
  configure(config: Partial<DashboardConfig>): void

  // Alerts
  addAlert(alert: Omit<DashboardAlert, 'id' | 'timestamp'>): void

  // Export
  async export(filename?: string): Promise<string>

  // Events
  on(event: 'started' | 'stopped' | 'layoutChanged' | 'exported' | 'error', handler: Function): void
}
```

### Helper Functions

```typescript
// Start dashboard (convenience function)
async function startDashboard(
  performanceMonitor: PerformanceMonitor,
  healthMonitor: HealthMonitor,
  queryLogger: QueryLogger,
  stateManager: StateManager,
  config?: DashboardConfig
): Promise<EnhancedDashboard>
```

### Events

```typescript
// Dashboard started
dashboard.on('started', () => {
  console.log('Dashboard started');
});

// Dashboard stopped
dashboard.on('stopped', () => {
  console.log('Dashboard stopped');
});

// Layout changed
dashboard.on('layoutChanged', (layout: string) => {
  console.log(`Layout changed to: ${layout}`);
});

// Snapshot exported
dashboard.on('exported', (filepath: string) => {
  console.log(`Snapshot exported: ${filepath}`);
});

// Error occurred
dashboard.on('error', (error: Error) => {
  console.error('Dashboard error:', error);
});
```

## Examples

### Example 1: Basic Dashboard

```typescript
import { startDashboard } from './src/cli/dashboard-enhanced';
import { PerformanceMonitor } from './src/cli/performance-monitor';
import { HealthMonitor } from './src/cli/health-monitor';
import { QueryLogger } from './src/cli/query-logger';
import { StateManager } from './src/core/state-manager';

async function main() {
  const stateManager = new StateManager();
  const performanceMonitor = new PerformanceMonitor(stateManager);
  const healthMonitor = new HealthMonitor(dbManager, stateManager);
  const queryLogger = new QueryLogger(stateManager);

  const dashboard = await startDashboard(
    performanceMonitor,
    healthMonitor,
    queryLogger,
    stateManager
  );

  console.log('Dashboard started. Press Q to quit.');
}

main();
```

### Example 2: Custom Configuration

```typescript
const dashboard = await startDashboard(
  performanceMonitor,
  healthMonitor,
  queryLogger,
  stateManager,
  {
    refreshInterval: 5000,    // Update every 5 seconds
    layout: 'monitoring',     // Use monitoring layout
    theme: 'ocean',          // Ocean theme
    historySize: 200,        // Keep 200 data points
    exportPath: './exports'  // Custom export path
  }
);
```

### Example 3: Custom Alerts

```typescript
// Add custom alert
dashboard.addAlert({
  severity: 'critical',
  message: 'Database connection pool exhausted',
  source: 'connection-manager',
  resolved: false
});

// Monitor specific condition
setInterval(() => {
  if (someCondition) {
    dashboard.addAlert({
      severity: 'warning',
      message: 'Custom threshold exceeded',
      source: 'custom-monitor',
      resolved: false
    });
  }
}, 10000);
```

### Example 4: Automated Exports

```typescript
// Export every hour
setInterval(async () => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filepath = await dashboard.export(`hourly-${timestamp}.json`);
  console.log(`Exported: ${filepath}`);
}, 3600000);
```

### Example 5: Event Handling

```typescript
dashboard.on('started', () => {
  console.log('📊 Dashboard is running');
});

dashboard.on('error', (error) => {
  console.error('❌ Dashboard error:', error);
  // Send notification, log to file, etc.
});

dashboard.on('exported', (filepath) => {
  console.log(`💾 Snapshot saved: ${filepath}`);
  // Upload to cloud, send notification, etc.
});
```

## Troubleshooting

### Common Issues

#### Dashboard Not Starting

**Problem:** Dashboard fails to start

**Solutions:**
1. Check terminal supports unicode
2. Verify dependencies installed
3. Check screen size (minimum 80x24)
4. Verify database connection active

```bash
# Check terminal capabilities
echo $TERM

# Verify blessed installed
npm list blessed
```

#### High CPU Usage

**Problem:** Dashboard consumes too much CPU

**Solutions:**
1. Increase refresh interval
2. Reduce history size
3. Use compact layout
4. Disable charts

```typescript
dashboard.configure({
  refreshInterval: 5000,  // Slower updates
  historySize: 50,       // Less history
  layout: 'compact'      // Simpler layout
});
```

#### Missing Metrics

**Problem:** Panels show "No data"

**Solutions:**
1. Ensure monitors are running
2. Check database connection
3. Verify query execution
4. Wait for initial data collection

```typescript
// Start monitors before dashboard
await performanceMonitor.monitor();
await healthMonitor.startMonitoring();
```

#### Garbled Display

**Problem:** Display looks corrupted

**Solutions:**
1. Resize terminal window
2. Clear screen and restart
3. Change theme
4. Check terminal encoding

```bash
# Clear and restart
clear && ai-shell dashboard start

# Try different theme
ai-shell dashboard start --theme light
```

### Debug Mode

Enable debug logging:

```typescript
// Set environment variable
process.env.DEBUG = 'dashboard:*';

// Or in bash
export DEBUG=dashboard:*
ai-shell dashboard start
```

### Performance Tips

1. **Optimize Refresh Interval**
   - Use 2-5 seconds for normal monitoring
   - Use 10+ seconds for low-priority monitoring

2. **Manage History Size**
   - Default 100 points is usually sufficient
   - Reduce for memory-constrained systems
   - Increase for detailed analysis

3. **Choose Appropriate Layout**
   - Use 'compact' for small screens
   - Use 'detailed' for analysis
   - Use 'monitoring' for operations

4. **Export Regularly**
   - Schedule periodic exports
   - Archive old exports
   - Use for post-mortem analysis

## Best Practices

### Production Deployment

1. **Use Monitoring Layout**
   ```typescript
   dashboard.configure({ layout: 'monitoring' });
   ```

2. **Configure Alert Thresholds**
   ```typescript
   healthMonitor.configureAlerts({
     thresholds: {
       responseTime: 500,
       cpuUsage: 75,
       memoryUsage: 80
     }
   });
   ```

3. **Schedule Exports**
   ```typescript
   setInterval(() => dashboard.export(), 3600000);
   ```

4. **Monitor Dashboard Health**
   ```typescript
   dashboard.on('error', (error) => {
     alertOps(error);
   });
   ```

### Development

1. **Use Detailed Layout**
   ```typescript
   dashboard.configure({ layout: 'detailed' });
   ```

2. **Fast Refresh**
   ```typescript
   dashboard.configure({ refreshInterval: 1000 });
   ```

3. **Enable All Alerts**
   ```typescript
   dashboard.configure({ enableAlerts: true });
   ```

### Testing

1. **Simulate Load**
   ```typescript
   // Generate test queries
   for (let i = 0; i < 100; i++) {
     await queryLogger.logQuery('SELECT * FROM test', 50 + Math.random() * 100);
   }
   ```

2. **Test Alerts**
   ```typescript
   dashboard.addAlert({
     severity: 'critical',
     message: 'Test alert',
     source: 'test',
     resolved: false
   });
   ```

## Support

### Getting Help

- **Documentation**: See `/docs` directory
- **Issues**: https://github.com/your-repo/issues
- **Examples**: See `/examples` directory

### Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-15  
**Author:** AI Shell Team
