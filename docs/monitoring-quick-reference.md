# AI-Shell Monitoring Commands - Quick Reference

## Health & Status

```bash
# Check database health
ai-shell health
ai-shell health postgres-prod

# View current metrics
ai-shell metrics show
ai-shell metrics show cpuUsage
```

## Real-time Monitoring

```bash
# Start monitoring (console output)
ai-shell monitor start

# Custom interval and format
ai-shell monitor start --interval 10 --output json

# Stop monitoring
ai-shell monitor stop
```

## Metrics Export

```bash
# Export to JSON
ai-shell metrics export json --output metrics.json

# Export to CSV
ai-shell metrics export csv --output metrics.csv

# Export for Prometheus
ai-shell metrics export prometheus

# Export for Grafana
ai-shell metrics export grafana
```

## Alert Management

```bash
# Configure alerts
ai-shell alerts setup

# List active alerts
ai-shell alerts list

# Test alert notification
ai-shell alerts test alert-id-123
```

## Performance Analysis

```bash
# Analyze performance
ai-shell performance analyze

# Generate report (1 hour)
ai-shell performance report 1h

# Generate report (24 hours)
ai-shell performance report 24h

# Generate report (7 days)
ai-shell performance report 7d
```

## Dashboard

```bash
# Start web dashboard
ai-shell dashboard start

# Custom port/host
ai-shell dashboard start --port 8080 --host localhost

# Open in browser: http://localhost:3000
```

## Grafana Integration

```bash
# Setup Grafana connection
ai-shell grafana setup \
  --url http://localhost:3000 \
  --api-key your-api-key-here \
  --prometheus-url http://localhost:9090

# Deploy all dashboards
ai-shell grafana deploy-dashboards
```

## Prometheus Integration

```bash
# Start Prometheus endpoint
ai-shell prometheus configure

# Custom port
ai-shell prometheus configure --port 9091

# Metrics available at: http://0.0.0.0:9090/metrics
```

## Anomaly Detection

```bash
# Detect anomalies (default: 3-sigma, 60 min window)
ai-shell anomaly detect

# Specific metric
ai-shell anomaly detect --metric cpuUsage

# Custom threshold (4-sigma)
ai-shell anomaly detect --threshold 4

# High sensitivity (2-sigma)
ai-shell anomaly detect --sensitivity high

# Custom time window (2 hours)
ai-shell anomaly detect --window 120
```

## Common Workflows

### Setup Monitoring Stack

```bash
# 1. Start Prometheus
ai-shell prometheus configure --port 9090

# 2. Configure Grafana
ai-shell grafana setup \
  --url http://localhost:3000 \
  --api-key xxx \
  --prometheus-url http://localhost:9090

# 3. Deploy dashboards
ai-shell grafana deploy-dashboards

# 4. Setup alerts
ai-shell alerts setup
```

### Daily Monitoring

```bash
# Check health
ai-shell health

# View metrics
ai-shell metrics show

# Check for alerts
ai-shell alerts list

# Run performance analysis
ai-shell performance analyze
```

### Troubleshooting

```bash
# Generate performance report
ai-shell performance report 24h

# Detect anomalies
ai-shell anomaly detect --sensitivity high

# Export metrics for analysis
ai-shell metrics export csv --output debug-metrics.csv
```

## Alert Thresholds (Default)

| Metric | Warning | Critical |
|--------|---------|----------|
| Response Time | 1000ms | 2000ms |
| Error Rate | 5% | 10% |
| CPU Usage | 80% | 90% |
| Memory Usage | 85% | 95% |
| Disk Space | 90% | 95% |

## Dashboard Panels

### Overview Dashboard (9 panels)
- Total Requests
- Active Connections
- Avg Response Time
- Cache Hit Rate
- Request Rate Chart
- Error Rate Chart
- CPU Usage Gauge
- Memory Usage Gauge
- Response Time Chart

### Performance Dashboard (15 panels)
- Response time percentiles (p50, p90, p95, p99)
- Response time heatmap
- Request throughput
- Token throughput
- Database query duration
- Database pool usage
- Cache performance
- CPU/Memory over time
- Network I/O

### Security Dashboard (10 panels)
- Failed auth attempts
- Blocked IPs
- Active sessions
- Security alerts
- Authentication events
- Rate limiting events
- Suspicious activity
- Access patterns

### Query Analytics Dashboard (14 panels)
- Query volume
- Query rate by model
- Query duration percentiles
- Token usage
- Query success rate
- Context window utilization
- Slowest queries
- Most frequent patterns

## Export Formats

### JSON
```json
[
  {
    "timestamp": 1635789600000,
    "activeConnections": 25,
    "queriesPerSecond": 45.2,
    "cpuUsage": 68.5
  }
]
```

### CSV
```csv
timestamp,activeConnections,queriesPerSecond,cpuUsage
1635789600000,25,45.2,68.5
```

### Prometheus
```
# HELP ai_shell_queries_total Total queries
# TYPE ai_shell_queries_total counter
ai_shell_queries_total{instance="localhost"} 1234
```

## Environment Variables

```bash
# Dashboard port
export AISHELL_DASHBOARD_PORT=3000

# Prometheus port
export AISHELL_PROMETHEUS_PORT=9090

# Monitoring interval
export AISHELL_MONITOR_INTERVAL=5

# Alert webhook URL
export AISHELL_ALERT_WEBHOOK_URL=https://hooks.slack.com/...
```

## Tips & Best Practices

1. **Regular Monitoring**: Run `ai-shell health` daily
2. **Performance Reports**: Generate weekly reports with `performance report 7d`
3. **Anomaly Detection**: Run hourly for critical metrics
4. **Dashboard**: Keep running for real-time visibility
5. **Alerts**: Configure Slack/Email for critical alerts
6. **Metrics Export**: Regular CSV exports for trend analysis
7. **Grafana**: Use pre-built dashboards for visualization

## Troubleshooting

### Dashboard won't start
```bash
# Check if port is in use
lsof -i :3000

# Try different port
ai-shell dashboard start --port 8080
```

### Prometheus not scraping
```bash
# Check endpoint is accessible
curl http://localhost:9090/metrics

# Verify Prometheus configuration
cat /etc/prometheus/prometheus.yml
```

### No metrics available
```bash
# Ensure monitoring is running
ai-shell monitor start

# Check metric storage
ai-shell metrics show
```

### Grafana connection failed
```bash
# Verify Grafana is running
curl http://localhost:3000/api/health

# Check API key permissions
# API key needs: Admin or Editor role
```

## Support

For issues or questions:
- Check logs: `tail -f ~/.aishell/logs/monitoring.log`
- Documentation: `/docs/reports/phase2-cli-implementation/sprint4-analytics.md`
- GitHub Issues: [Create Issue](https://github.com/your-repo/issues)
