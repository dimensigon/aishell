# Grafana Integration - AI-Shell P3 Feature

**Status**: Priority 3 (P3) Integration
**Version**: 1.0.0
**Last Updated**: 2025-10-28

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Pre-built Dashboards](#pre-built-dashboards)
- [Custom Dashboards](#custom-dashboards)
- [Data Sources](#data-sources)
- [Alerting](#alerting)
- [Variables & Templating](#variables--templating)
- [Use Cases](#use-cases)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

Grafana integration provides beautiful, interactive dashboards for AI-Shell metrics visualization. Features include:

- **Pre-built Dashboards**: Ready-to-use dashboard templates
- **Custom Visualizations**: Build your own dashboards
- **Real-Time Updates**: Live data refresh
- **Multi-Source**: Combine Prometheus, databases, logs
- **Alerting**: Visual alerts and notifications
- **Sharing**: Share dashboards with teams
- **Variables**: Dynamic dashboard filtering

### Key Benefits

✅ **Visual Analytics**: Beautiful charts and graphs
✅ **Interactive**: Drill-down and explore data
✅ **Customizable**: Full control over layouts
✅ **Multi-Tenant**: Separate dashboards per team
✅ **Mobile Friendly**: Responsive design
✅ **Export & Share**: PDF, PNG, JSON export

---

## Installation

### Install Grafana

```bash
# macOS
brew install grafana
brew services start grafana

# Linux (Ubuntu/Debian)
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
sudo apt-get update
sudo apt-get install grafana
sudo systemctl start grafana-server

# Docker
docker run -d -p 3000:3000 --name=grafana grafana/grafana

# Access Grafana
open http://localhost:3000
# Default credentials: admin/admin
```

### Install AI-Shell Grafana Plugin

```bash
# Install plugin
grafana-cli plugins install aishell-datasource

# Restart Grafana
sudo systemctl restart grafana-server

# Verify installation
curl http://admin:admin@localhost:3000/api/plugins/aishell-datasource
```

### Configure Data Source

```bash
# Add Prometheus data source
curl -X POST http://admin:admin@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI-Shell Prometheus",
    "type": "prometheus",
    "url": "http://localhost:9091",
    "access": "proxy",
    "isDefault": true
  }'

# Add AI-Shell direct data source
curl -X POST http://admin:admin@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI-Shell Direct",
    "type": "aishell-datasource",
    "url": "http://localhost:8080",
    "access": "proxy",
    "basicAuth": true,
    "basicAuthUser": "admin",
    "secureJsonData": {
      "basicAuthPassword": "password"
    }
  }'
```

---

## Quick Start

### Example 1: Import Pre-built Dashboard

```bash
# Export dashboard from AI-Shell
aishell grafana export --dashboard performance --output perf-dashboard.json

# Import to Grafana via UI:
# 1. Navigate to http://localhost:3000
# 2. Click + → Import
# 3. Upload perf-dashboard.json
# 4. Select data source
# 5. Click Import

# Or import via API:
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @perf-dashboard.json
```

### Example 2: Create Simple Panel

```bash
# Create dashboard via API
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "title": "AI-Shell Overview",
      "panels": [
        {
          "title": "Queries Per Second",
          "type": "graph",
          "targets": [
            {
              "expr": "rate(aishell_query_total[5m])"
            }
          ],
          "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8}
        }
      ]
    },
    "overwrite": false
  }'
```

### Example 3: View Dashboard

```bash
# Get dashboard list
curl http://admin:admin@localhost:3000/api/search?query=aishell

# Open dashboard
open "http://localhost:3000/d/<dashboard-uid>/ai-shell-overview"
```

---

## Pre-built Dashboards

### Performance Dashboard

Monitors query performance and system health.

**Panels**:
- Queries per second (QPS)
- Average latency (P50, P95, P99)
- Slow query count
- Error rate
- Connection pool status
- Cache hit rate

**Import**:
```bash
aishell grafana export --dashboard performance | \
  curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
    -H "Content-Type: application/json" \
    -d @-
```

### DBA Dashboard

For database administrators.

**Panels**:
- Database size and growth
- Table sizes
- Index usage
- Replication lag
- Lock statistics
- Backup status

**Import**:
```bash
aishell grafana import --dashboard dba
```

### Application Dashboard

Application-level metrics.

**Panels**:
- Request rate
- Response time distribution
- Active users
- Feature usage
- API endpoint performance
- Business KPIs

### Security Dashboard

Security monitoring.

**Panels**:
- Failed authentication attempts
- Suspicious query patterns
- Access by user role
- SQL injection attempts
- Unusual activity alerts

---

## Custom Dashboards

### Dashboard JSON Structure

```json
{
  "dashboard": {
    "title": "Custom AI-Shell Dashboard",
    "tags": ["aishell", "custom"],
    "timezone": "browser",
    "schemaVersion": 38,
    "version": 1,
    "refresh": "30s",
    
    "panels": [
      {
        "id": 1,
        "title": "Query Rate",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "datasource": "AI-Shell Prometheus",
            "expr": "rate(aishell_query_total[5m])",
            "legendFormat": "{{database}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {"mode": "palette-classic"},
            "custom": {"lineWidth": 2},
            "unit": "ops"
          }
        }
      }
    ],
    
    "templating": {
      "list": [
        {
          "name": "database",
          "type": "query",
          "datasource": "AI-Shell Prometheus",
          "query": "label_values(aishell_query_total, database)",
          "multi": true,
          "includeAll": true
        }
      ]
    }
  }
}
```

### Create Dashboard Programmatically

```typescript
import { GrafanaDashboard } from '@aishell/grafana';

const dashboard = new GrafanaDashboard({
  title: 'My Custom Dashboard',
  tags: ['aishell', 'custom'],
  refresh: '30s'
});

// Add QPS panel
dashboard.addPanel({
  title: 'Queries Per Second',
  type: 'timeseries',
  queries: [
    'rate(aishell_query_total[5m])'
  ],
  position: { x: 0, y: 0, w: 12, h: 8 }
});

// Add latency panel
dashboard.addPanel({
  title: 'Query Latency (P95)',
  type: 'gauge',
  queries: [
    'histogram_quantile(0.95, rate(aishell_query_duration_seconds_bucket[5m]))'
  ],
  position: { x: 12, y: 0, w: 6, h: 8 },
  thresholds: [
    { value: 0, color: 'green' },
    { value: 0.5, color: 'yellow' },
    { value: 1, color: 'red' }
  ]
});

// Export
await dashboard.export('custom-dashboard.json');

// Upload to Grafana
await dashboard.upload('http://localhost:3000', {
  username: 'admin',
  password: 'admin'
});
```

---

## Data Sources

### Prometheus Data Source

**Configuration**:
```yaml
datasources:
  - name: AI-Shell Prometheus
    type: prometheus
    url: http://localhost:9091
    access: proxy
    isDefault: true
    jsonData:
      timeInterval: 15s
      queryTimeout: 60s
```

**Example Queries**:
```promql
# QPS
rate(aishell_query_total[5m])

# Latency percentiles
histogram_quantile(0.95, rate(aishell_query_duration_seconds_bucket[5m]))

# Error rate
rate(aishell_query_errors_total[5m]) / rate(aishell_query_total[5m])
```

### AI-Shell Direct Data Source

**Configuration**:
```yaml
datasources:
  - name: AI-Shell Direct
    type: aishell-datasource
    url: http://localhost:8080
    access: proxy
    basicAuth: true
    basicAuthUser: admin
    secureJsonData:
      basicAuthPassword: password
```

**Example Queries**:
```sql
-- Recent queries
SELECT timestamp, query, duration
FROM query_log
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC
LIMIT 100

-- Slow queries
SELECT query, AVG(duration) as avg_duration, COUNT(*) as count
FROM query_log
WHERE duration > 1000
GROUP BY query
ORDER BY avg_duration DESC
LIMIT 10
```

---

## Alerting

### Configure Alert Rules

```yaml
# In Grafana UI: Panel → Alert tab

# Alert conditions
- Name: High Query Rate
  Condition:
    - Query: rate(aishell_query_total[5m])
    - Reducer: last
    - Evaluator: is above 1000
  For: 5m
  
# Notifications
  Send to: 
    - Email: dba-team@company.com
    - Slack: #database-alerts
    - PagerDuty: database-oncall
  
# Alert annotations
  message: |
    Query rate is {{ $value }} qps
    Dashboard: {{ $dashboardLink }}
```

### Alert Notification Channels

```bash
# Create Slack notification channel
curl -X POST http://admin:admin@localhost:3000/api/alert-notifications \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Slack Alerts",
    "type": "slack",
    "isDefault": true,
    "settings": {
      "url": "https://hooks.slack.com/services/XXX",
      "channel": "#database-alerts"
    }
  }'

# Create email notification channel
curl -X POST http://admin:admin@localhost:3000/api/alert-notifications \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Email Alerts",
    "type": "email",
    "isDefault": false,
    "settings": {
      "addresses": "dba-team@company.com;dev-team@company.com"
    }
  }'
```

---

## Variables & Templating

### Dashboard Variables

```json
{
  "templating": {
    "list": [
      {
        "name": "database",
        "type": "query",
        "datasource": "AI-Shell Prometheus",
        "query": "label_values(aishell_query_total, database)",
        "multi": true,
        "includeAll": true,
        "current": {
          "text": "All",
          "value": "$__all"
        }
      },
      {
        "name": "interval",
        "type": "interval",
        "options": [
          {"text": "1m", "value": "1m"},
          {"text": "5m", "value": "5m"},
          {"text": "15m", "value": "15m"},
          {"text": "1h", "value": "1h"}
        ],
        "current": {
          "text": "5m",
          "value": "5m"
        }
      }
    ]
  }
}
```

### Use Variables in Queries

```promql
# Use $database variable
rate(aishell_query_total{database=~"$database"}[$interval])

# Use $__interval (auto-interval)
rate(aishell_query_total[$__interval])

# Use $__range (time range)
avg_over_time(aishell_query_duration_seconds_avg[$__range])
```

---

## Use Cases

### Use Case 1: Real-Time Monitoring

Create dashboard for real-time monitoring:

1. **Create dashboard** with 30s refresh
2. **Add panels**: QPS, latency, errors
3. **Set alerts**: High QPS, high latency
4. **Share** with team
5. **Display** on TV/monitor

### Use Case 2: Performance Analysis

Analyze performance over time:

1. **Select time range** (last 7 days)
2. **Compare metrics** (before/after deployment)
3. **Identify patterns** (peak hours, trends)
4. **Export data** for reports
5. **Share** findings

### Use Case 3: Capacity Planning

Plan for future capacity:

1. **View growth trends** (database size, QPS)
2. **Forecast** future needs
3. **Compare** current vs. predicted
4. **Plan** upgrades
5. **Present** to stakeholders

---

## Troubleshooting

### Issue 1: No Data in Panels

```bash
# Check data source connection
curl http://admin:admin@localhost:3000/api/datasources

# Test query
curl -X POST http://admin:admin@localhost:3000/api/ds/query \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [{
      "datasource": "AI-Shell Prometheus",
      "expr": "aishell_query_total"
    }]
  }'

# Check Prometheus
curl http://localhost:9091/api/v1/query?query=aishell_query_total
```

### Issue 2: Slow Dashboard

```bash
# Reduce refresh rate
# In dashboard settings: Refresh → 1m or 5m

# Optimize queries
# Use recording rules in Prometheus

# Limit time range
# Default to last 6h or 24h

# Reduce number of panels
# Split into multiple dashboards
```

### Issue 3: Alert Not Firing

```bash
# Check alert rule
curl http://admin:admin@localhost:3000/api/alerts

# Test notification channel
curl -X POST http://admin:admin@localhost:3000/api/alert-notifications/test \
  -H "Content-Type: application/json" \
  -d '{"id": 1}'

# Check alert history
# Navigate to Alerting → Alert Rules → View history
```

---

## Best Practices

1. **Use Variables** for flexibility
2. **Set Appropriate Refresh** rates (30s-5m)
3. **Organize Panels** logically
4. **Use Folders** for dashboard organization
5. **Document** dashboards with text panels
6. **Version Control** dashboard JSON files
7. **Test Alerts** before deployment
8. **Export Regularly** for backup
9. **Use Playlists** for rotation
10. **Mobile-Friendly** layouts

---

## Summary

Grafana integration provides:

- 📊 **Beautiful Dashboards** - Professional visualizations
- 🎨 **Customizable** - Full control over layout
- 🔔 **Alerting** - Visual alerts and notifications
- 📱 **Mobile Friendly** - Responsive design
- 🔗 **Multi-Source** - Combine multiple data sources
- 📤 **Export & Share** - PDF, PNG, JSON export

For more information:
- [Prometheus Integration](./prometheus.md)
- [Enhanced Dashboard](../features/enhanced-dashboard.md)
- [Pattern Detection](../features/pattern-detection.md)

---

**Need Help?**
- 📖 [Grafana Docs](https://grafana.com/docs/)
- 💬 [Community Forum](https://github.com/yourusername/aishell/discussions)
- 🐛 [Report Issues](https://github.com/yourusername/aishell/issues)
