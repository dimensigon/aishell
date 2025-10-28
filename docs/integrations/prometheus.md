# Prometheus Integration - AI-Shell P3 Feature

**Status**: Priority 3 (P3) Integration
**Version**: 2.0.0
**Last Updated**: 2025-10-28

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Metrics Exported](#metrics-exported)
- [Configuration](#configuration)
- [Dashboards](#dashboards)
- [Alerting Rules](#alerting-rules)
- [Use Cases](#use-cases)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

The Prometheus integration enables comprehensive monitoring of AI-Shell database operations through metrics export, enabling:

- **Real-Time Monitoring**: Expose metrics for Prometheus scraping
- **Historical Analysis**: Long-term metric storage and analysis  
- **Alerting**: Set up alerts based on metric thresholds
- **Visualization**: Create dashboards in Grafana
- **SLI/SLO Tracking**: Monitor service level indicators
- **Capacity Planning**: Analyze trends for future planning

### Key Benefits

✅ **Standard Metrics Format**: Prometheus-compatible metrics
✅ **Auto-Discovery**: Service discovery integration
✅ **High Performance**: Efficient metric collection
✅ **Flexible Labels**: Rich dimensional data
✅ **Alerting Integration**: Native AlertManager support
✅ **Grafana Ready**: Pre-built dashboards available

---

## Features

### Core Capabilities

1. **Metrics Endpoint**
   - HTTP metrics endpoint on `/metrics`
   - Prometheus text format
   - Automatic metric registration
   - Multi-database support
   - Custom label support

2. **Database Metrics**
   - Query performance (QPS, latency, errors)
   - Connection pool status
   - Cache hit rates
   - Table sizes and growth
   - Replication lag
   - Lock statistics

3. **Application Metrics**
   - Request rates
   - Response times
   - Error rates  
   - Resource utilization
   - Feature usage
   - API endpoints

4. **Custom Metrics**
   - User-defined metrics
   - Business KPIs
   - Custom counters/gauges/histograms
   - Derived metrics

5. **Service Discovery**
   - Auto-registration with Prometheus
   - Dynamic target updates
   - Multiple instance support
   - Health check integration

---

## Installation

### Prerequisites

```bash
# Install Prometheus
# macOS
brew install prometheus

# Linux
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Start Prometheus
./prometheus --config.file=prometheus.yml
```

### Install AI-Shell Prometheus Exporter

```bash
# Install exporter module
npm install -g @aishell/prometheus-exporter

# Enable Prometheus integration
aishell config set integrations.prometheus.enabled true
aishell config set integrations.prometheus.port 9090
aishell config set integrations.prometheus.path /metrics

# Start metrics exporter
aishell prometheus start

# Output:
# ✓ Prometheus exporter started
# ✓ Metrics endpoint: http://localhost:9090/metrics
# ✓ Ready for scraping
```

### Verify Installation

```bash
# Test metrics endpoint
curl http://localhost:9090/metrics

# Expected output:
# HELP aishell_query_total Total number of queries executed
# TYPE aishell_query_total counter
# aishell_query_total{database="postgres",type="SELECT"} 1234

# HELP aishell_query_duration_seconds Query execution duration
# TYPE aishell_query_duration_seconds histogram
# aishell_query_duration_seconds_bucket{le="0.1"} 567
# aishell_query_duration_seconds_bucket{le="0.5"} 890
# ...
```

---

## Quick Start

### Example 1: Basic Setup

```bash
# Start AI-Shell with Prometheus
aishell prometheus start --port 9090

# Configure Prometheus to scrape AI-Shell
# Add to prometheus.yml:
cat >> prometheus.yml << 'EOF'
scrape_configs:
  - job_name: 'aishell'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s
EOF

# Restart Prometheus
pkill prometheus
./prometheus --config.file=prometheus.yml &

# Verify scraping
curl http://localhost:9091/api/v1/targets | jq
```

### Example 2: Query Prometheus

```bash
# Query current QPS
curl 'http://localhost:9091/api/v1/query?query=rate(aishell_query_total[5m])'

# Query average latency
curl 'http://localhost:9091/api/v1/query?query=aishell_query_duration_seconds_avg'

# Query by database
curl 'http://localhost:9091/api/v1/query?query=aishell_query_total{database="postgres"}'
```

### Example 3: Alert on High QPS

```yaml
# alerts.yml
groups:
  - name: aishell_alerts
    rules:
      - alert: HighQueryRate
        expr: rate(aishell_query_total[5m]) > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High query rate detected"
          description: "Query rate is {{ $value }} qps"
```

---

## Metrics Exported

### Query Metrics

```prometheus
# Total queries
aishell_query_total{database, type, status}

# Query duration histogram
aishell_query_duration_seconds{database, type}

# Query duration summary
aishell_query_duration_summary{database, quantile}

# Slow queries
aishell_slow_query_total{database, threshold}

# Query errors
aishell_query_errors_total{database, type, error}

# Queries per second (derived)
rate(aishell_query_total[5m])
```

### Connection Metrics

```prometheus
# Active connections
aishell_connections_active{database}

# Connection pool size
aishell_connections_pool_size{database}

# Connection wait time
aishell_connection_wait_seconds{database}

# Connection errors
aishell_connection_errors_total{database, error}

# Connection utilization
aishell_connections_active / aishell_connections_pool_size
```

### Performance Metrics

```prometheus
# Cache hit rate
aishell_cache_hit_rate{database}

# Database size
aishell_database_size_bytes{database, table}

# Table sizes
aishell_table_size_bytes{database, table}

# Index sizes  
aishell_index_size_bytes{database, table, index}

# Growth rate
deriv(aishell_database_size_bytes[1d])
```

### System Metrics

```prometheus
# CPU usage
aishell_cpu_usage_percent

# Memory usage
aishell_memory_usage_bytes
aishell_memory_available_bytes

# Disk I/O
aishell_disk_reads_total
aishell_disk_writes_total

# Network I/O
aishell_network_bytes_received
aishell_network_bytes_sent
```

### Application Metrics

```prometheus
# Request rate
aishell_http_requests_total{method, endpoint, status}

# Request duration
aishell_http_request_duration_seconds{method, endpoint}

# Active users
aishell_active_users{role}

# Feature usage
aishell_feature_usage_total{feature}
```

---

## Configuration

### AI-Shell Configuration

`~/.aishell/config/prometheus.yaml`:

```yaml
prometheus:
  enabled: true
  port: 9090
  path: /metrics
  host: 0.0.0.0
  
  # Metric collection
  collect_interval: 15  # seconds
  
  # Metrics to export
  metrics:
    queries: true
    connections: true
    performance: true
    system: true
    custom: true
  
  # Label configuration
  labels:
    environment: production
    region: us-west-2
    cluster: main
  
  # Metric naming
  prefix: aishell
  
  # Buckets for histograms
  buckets:
    query_duration: [0.01, 0.05, 0.1, 0.5, 1, 5, 10]
    request_size: [100, 1000, 10000, 100000, 1000000]
  
  # Custom metrics
  custom_metrics:
    - name: business_transactions
      type: counter
      help: "Total business transactions"
      labels: [type, status]
    - name: revenue
      type: gauge
      help: "Current revenue"
      labels: [product]
```

### Prometheus Configuration

`prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'ai-shell-monitor'

scrape_configs:
  - job_name: 'aishell'
    static_configs:
      - targets:
          - 'localhost:9090'
          - 'db-server-1:9090'
          - 'db-server-2:9090'
    scrape_interval: 15s
    scrape_timeout: 10s
    metrics_path: /metrics
    
    # Relabeling
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
      - source_labels: [__address__]
        regex: '([^:]+).*'
        target_label: host
        replacement: '$1'
    
    # Service discovery (Kubernetes)
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - aishell
    
    # Service discovery (Consul)
    consul_sd_configs:
      - server: 'consul:8500'
        services: ['aishell']

# Alerting
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'alertmanager:9093'

rule_files:
  - 'alerts.yml'
  - 'recording_rules.yml'
```

---

## Dashboards

### Grafana Dashboard Import

```bash
# Export AI-Shell dashboard for Grafana
aishell prometheus export-dashboard --output aishell-dashboard.json

# Import to Grafana
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @aishell-dashboard.json
```

### Dashboard Panels

**Overview Panel**:
```promql
# QPS
rate(aishell_query_total[5m])

# Avg Latency
rate(aishell_query_duration_seconds_sum[5m]) / rate(aishell_query_duration_seconds_count[5m])

# Error Rate
rate(aishell_query_errors_total[5m])

# Active Connections
aishell_connections_active
```

**Performance Panel**:
```promql
# P50, P95, P99 Latency
histogram_quantile(0.50, rate(aishell_query_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(aishell_query_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(aishell_query_duration_seconds_bucket[5m]))

# Slow Query Rate
rate(aishell_slow_query_total[5m])

# Cache Hit Rate
aishell_cache_hit_rate
```

**Resource Panel**:
```promql
# CPU Usage
aishell_cpu_usage_percent

# Memory Usage
(aishell_memory_usage_bytes / (aishell_memory_usage_bytes + aishell_memory_available_bytes)) * 100

# Disk Usage
rate(aishell_disk_writes_total[5m])
```

---

## Alerting Rules

### Alert Rules File

`alerts.yml`:

```yaml
groups:
  - name: aishell_performance
    interval: 30s
    rules:
      - alert: HighQueryRate
        expr: rate(aishell_query_total[5m]) > 1000
        for: 5m
        labels:
          severity: warning
          component: database
        annotations:
          summary: "High query rate on {{ $labels.database }}"
          description: "Query rate is {{ $value }} qps (threshold: 1000)"
          
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(aishell_query_duration_seconds_bucket[5m])) > 1
        for: 10m
        labels:
          severity: warning
          component: database
        annotations:
          summary: "High query latency on {{ $labels.database }}"
          description: "P95 latency is {{ $value }}s"
          
      - alert: HighErrorRate
        expr: rate(aishell_query_errors_total[5m]) / rate(aishell_query_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
          component: database
        annotations:
          summary: "High error rate on {{ $labels.database }}"
          description: "Error rate is {{ $value | humanizePercentage }}"
          
      - alert: ConnectionPoolExhausted
        expr: aishell_connections_active / aishell_connections_pool_size > 0.9
        for: 5m
        labels:
          severity: critical
          component: database
        annotations:
          summary: "Connection pool near exhaustion"
          description: "{{ $value | humanizePercentage }} of connections in use"

  - name: aishell_resources
    interval: 30s
    rules:
      - alert: HighCPU
        expr: aishell_cpu_usage_percent > 90
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"
          
      - alert: HighMemory
        expr: (aishell_memory_usage_bytes / (aishell_memory_usage_bytes + aishell_memory_available_bytes)) > 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

  - name: aishell_slo
    interval: 5m
    rules:
      - alert: SLOViolation
        expr: |
          (
            sum(rate(aishell_query_total{status="success"}[5m]))
            /
            sum(rate(aishell_query_total[5m]))
          ) < 0.999
        for: 15m
        labels:
          severity: critical
          slo: availability
        annotations:
          summary: "SLO violation: Availability below 99.9%"
          description: "Current availability: {{ $value | humanizePercentage }}"
```

### Recording Rules

`recording_rules.yml`:

```yaml
groups:
  - name: aishell_aggregations
    interval: 30s
    rules:
      # QPS by database
      - record: aishell:query_rate:5m
        expr: rate(aishell_query_total[5m])
      
      # Avg latency by database
      - record: aishell:query_duration:avg:5m
        expr: rate(aishell_query_duration_seconds_sum[5m]) / rate(aishell_query_duration_seconds_count[5m])
      
      # Error rate
      - record: aishell:error_rate:5m
        expr: rate(aishell_query_errors_total[5m]) / rate(aishell_query_total[5m])
      
      # Cache efficiency
      - record: aishell:cache_efficiency
        expr: aishell_cache_hit_rate
      
      # Connection utilization
      - record: aishell:connection_utilization
        expr: aishell_connections_active / aishell_connections_pool_size
```

---

## Use Cases

### Use Case 1: Performance Monitoring

```bash
# Start monitoring
aishell prometheus start

# View metrics in browser
open http://localhost:9090/metrics

# Query in Prometheus
# Navigate to http://localhost:9091
# Query: rate(aishell_query_total[5m])

# Set up alerts
cat > alerts.yml << 'EOF'
groups:
  - name: performance
    rules:
      - alert: SlowQueries
        expr: rate(aishell_slow_query_total[5m]) > 10
        labels:
          severity: warning
EOF
```

### Use Case 2: Capacity Planning

```promql
# Growth trend (daily)
deriv(aishell_database_size_bytes[1d])

# Forecast storage needs (30 days)
predict_linear(aishell_database_size_bytes[7d], 30 * 24 * 3600)

# Connection pool utilization trend
avg_over_time(aishell:connection_utilization[7d])
```

### Use Case 3: SLO Tracking

```yaml
# Define SLOs
slo:
  availability:
    target: 0.999  # 99.9%
    window: 30d
    
  latency:
    target: 0.1  # 100ms
    percentile: 0.95
    window: 30d

# Query SLO compliance
(
  sum(rate(aishell_query_total{status="success"}[30d]))
  /
  sum(rate(aishell_query_total[30d]))
) > 0.999
```

---

## Troubleshooting

### Issue 1: Metrics Not Showing

```bash
# Check exporter status
aishell prometheus status

# Test metrics endpoint
curl -v http://localhost:9090/metrics

# Check Prometheus targets
curl http://localhost:9091/api/v1/targets

# Verify scrape config
grep -A 10 "job_name: 'aishell'" prometheus.yml
```

### Issue 2: High Cardinality

```bash
# Check metric cardinality
curl 'http://localhost:9091/api/v1/label/__name__/values' | jq

# Reduce labels
aishell config set prometheus.labels.limit 10

# Drop high-cardinality labels
aishell config set prometheus.drop_labels "user_id,session_id"
```

### Issue 3: Scrape Timeout

```bash
# Increase timeout in prometheus.yml
scrape_timeout: 30s

# Optimize metric collection
aishell config set prometheus.collect_interval 30

# Reduce metrics
aishell config set prometheus.metrics.custom false
```

---

## Best Practices

1. **Use Recording Rules** for expensive queries
2. **Set Appropriate Retention** (15d for metrics)
3. **Monitor Prometheus Itself** (meta-monitoring)
4. **Use Service Discovery** for dynamic environments
5. **Implement SLOs** and alert on violations
6. **Regular Backup** of Prometheus data
7. **Optimize Cardinality** - avoid user IDs in labels
8. **Use Grafana** for visualization
9. **Document Alert Runbooks**
10. **Test Alerts** before production

---

## Summary

Prometheus integration provides:

- 📊 **Comprehensive Metrics** - All database and app metrics
- 🚨 **Flexible Alerting** - Custom alert rules
- 📈 **Time Series Data** - Historical trend analysis
- 🎯 **SLO Tracking** - Service level monitoring
- 🔗 **Easy Integration** - Standard Prometheus format
- 📊 **Grafana Ready** - Pre-built dashboards

For more information:
- [Grafana Integration](./grafana.md)
- [Enhanced Dashboard](../features/enhanced-dashboard.md)
- [Pattern Detection](../features/pattern-detection.md)

---

**Need Help?**
- 📖 [Prometheus Docs](https://prometheus.io/docs/)
- 💬 [Community Forum](https://github.com/yourusername/aishell/discussions)
- 🐛 [Report Issues](https://github.com/yourusername/aishell/issues)
