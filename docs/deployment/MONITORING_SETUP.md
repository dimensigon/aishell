# Monitoring Setup Guide

Complete observability configuration for AIShell production deployments including Prometheus, Grafana, log aggregation, and health check endpoints.

## Table of Contents

1. [Prometheus Configuration](#prometheus-configuration)
2. [Grafana Dashboard Deployment](#grafana-dashboard-deployment)
3. [Alert Manager Setup](#alert-manager-setup)
4. [Log Aggregation](#log-aggregation)
5. [Health Check Endpoints](#health-check-endpoints)
6. [Metrics Collection](#metrics-collection)
7. [Distributed Tracing](#distributed-tracing)
8. [Monitoring Best Practices](#monitoring-best-practices)

---

## Prometheus Configuration

### Install Prometheus

```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Create user
sudo useradd --no-create-home --shell /bin/false prometheus

# Create directories
sudo mkdir /etc/prometheus
sudo mkdir /var/lib/prometheus

# Move files
sudo mv prometheus /usr/local/bin/
sudo mv promtool /usr/local/bin/
sudo mv consoles /etc/prometheus
sudo mv console_libraries /etc/prometheus

# Set ownership
sudo chown -R prometheus:prometheus /etc/prometheus /var/lib/prometheus
```

### Prometheus Configuration

```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s              # Scrape targets every 15 seconds
  evaluation_interval: 15s          # Evaluate rules every 15 seconds
  external_labels:
    cluster: 'ai-shell-production'
    region: 'us-east-1'

# Alert manager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

# Load rules
rule_files:
  - "/etc/prometheus/rules/*.yml"

# Scrape configurations
scrape_configs:
  # AIShell application metrics
  - job_name: 'ai-shell'
    scrape_interval: 30s
    static_configs:
      - targets:
          - 'localhost:9090'
          - 'app-server-1:9090'
          - 'app-server-2:9090'
          - 'app-server-3:9090'
    metrics_path: '/metrics'
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance

  # PostgreSQL metrics (using postgres_exporter)
  - job_name: 'postgres'
    static_configs:
      - targets:
          - 'localhost:9187'
    relabel_configs:
      - source_labels: [__address__]
        target_label: database
        replacement: 'ai-shell-prod'

  # Redis metrics (using redis_exporter)
  - job_name: 'redis'
    static_configs:
      - targets:
          - 'localhost:9121'

  # Node metrics (system resources)
  - job_name: 'node'
    static_configs:
      - targets:
          - 'localhost:9100'
          - 'app-server-1:9100'
          - 'app-server-2:9100'

  # Blackbox monitoring (health checks)
  - job_name: 'blackbox'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://api.ai-shell.example.com/health
          - https://api.ai-shell.example.com/health/database
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9115
```

### Prometheus Service

```ini
# /etc/systemd/system/prometheus.service
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
  --config.file /etc/prometheus/prometheus.yml \
  --storage.tsdb.path /var/lib/prometheus/ \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --storage.tsdb.retention.time=90d \
  --web.enable-lifecycle

[Install]
WantedBy=multi-user.target
```

```bash
# Start Prometheus
sudo systemctl daemon-reload
sudo systemctl start prometheus
sudo systemctl enable prometheus
sudo systemctl status prometheus

# Access UI
curl http://localhost:9090
```

### Alert Rules

```yaml
# /etc/prometheus/rules/ai-shell-alerts.yml
groups:
  - name: ai-shell-alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(ai_shell_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}% over the last 5 minutes"

      # Database connection pool exhaustion
      - alert: DatabasePoolExhausted
        expr: (ai_shell_db_connections_active / ai_shell_db_connections_max) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "Using {{ $value }}% of available connections"

      # High query latency
      - alert: HighQueryLatency
        expr: histogram_quantile(0.95, ai_shell_query_duration_seconds) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High query latency detected"
          description: "P95 query latency is {{ $value }}s"

      # Memory usage
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"

      # Disk usage
      - alert: HighDiskUsage
        expr: (node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High disk usage"
          description: "Disk usage is {{ $value }}% on {{ $labels.device }}"

      # Service down
      - alert: ServiceDown
        expr: up{job="ai-shell"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "AIShell service is down"
          description: "{{ $labels.instance }} is unreachable"

      # Cache hit ratio low
      - alert: LowCacheHitRatio
        expr: rate(ai_shell_cache_hits_total[5m]) / (rate(ai_shell_cache_hits_total[5m]) + rate(ai_shell_cache_misses_total[5m])) < 0.7
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit ratio"
          description: "Cache hit ratio is {{ $value }}%"

      # Backup failure
      - alert: BackupFailed
        expr: ai_shell_backup_last_success_timestamp < (time() - 86400)
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Backup has not succeeded in 24 hours"
          description: "Last successful backup was {{ $value }}s ago"
```

---

## Grafana Dashboard Deployment

### Install Grafana

```bash
# Add Grafana repository
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -

# Install Grafana
sudo apt-get update
sudo apt-get install grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

### Grafana Configuration

```ini
# /etc/grafana/grafana.ini
[server]
protocol = https
http_port = 3000
domain = grafana.ai-shell.example.com
root_url = https://grafana.ai-shell.example.com/
cert_file = /etc/ssl/certs/grafana.crt
cert_key = /etc/ssl/private/grafana.key

[database]
type = postgres
host = postgres.internal:5432
name = grafana
user = grafana
password = ${GRAFANA_DB_PASSWORD}

[security]
admin_user = admin
admin_password = ${GRAFANA_ADMIN_PASSWORD}
secret_key = ${GRAFANA_SECRET_KEY}
disable_gravatar = true
cookie_secure = true
cookie_samesite = strict

[auth]
disable_login_form = false
disable_signout_menu = false
oauth_auto_login = false

[users]
allow_sign_up = false
allow_org_create = false
auto_assign_org = true
auto_assign_org_role = Viewer

[alerting]
enabled = true
execute_alerts = true

[unified_alerting]
enabled = true

[smtp]
enabled = true
host = smtp.example.com:587
user = grafana@example.com
password = ${SMTP_PASSWORD}
from_address = grafana@example.com
from_name = Grafana
```

### AIShell Dashboard JSON

```json
{
  "dashboard": {
    "title": "AIShell Production Dashboard",
    "tags": ["ai-shell", "production"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_shell_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_shell_errors_total[5m])",
            "legendFormat": "{{error_type}}"
          }
        ]
      },
      {
        "title": "Query Duration (P95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, ai_shell_query_duration_seconds)",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, ai_shell_query_duration_seconds)",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "ai_shell_db_connections_active",
            "legendFormat": "Active"
          },
          {
            "expr": "ai_shell_db_connections_idle",
            "legendFormat": "Idle"
          }
        ]
      },
      {
        "title": "Cache Hit Ratio",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(ai_shell_cache_hits_total[5m]) / (rate(ai_shell_cache_hits_total[5m]) + rate(ai_shell_cache_misses_total[5m])) * 100"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "process_resident_memory_bytes",
            "legendFormat": "RSS"
          },
          {
            "expr": "nodejs_heap_size_total_bytes",
            "legendFormat": "Heap Total"
          },
          {
            "expr": "nodejs_heap_size_used_bytes",
            "legendFormat": "Heap Used"
          }
        ]
      }
    ]
  }
}
```

### Dashboard Provisioning

```yaml
# /etc/grafana/provisioning/dashboards/ai-shell.yaml
apiVersion: 1

providers:
  - name: 'AIShell'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards/ai-shell
```

### Data Source Provisioning

```yaml
# /etc/grafana/provisioning/datasources/prometheus.yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: "15s"
      queryTimeout: "60s"
```

---

## Alert Manager Setup

### Install Alert Manager

```bash
# Download
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xvfz alertmanager-*.tar.gz
cd alertmanager-*

# Install
sudo mv alertmanager /usr/local/bin/
sudo mv amtool /usr/local/bin/
sudo mkdir /etc/alertmanager
sudo mkdir /var/lib/alertmanager

# Set ownership
sudo chown -R prometheus:prometheus /etc/alertmanager /var/lib/alertmanager
```

### Alert Manager Configuration

```yaml
# /etc/alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@ai-shell.example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: '${SMTP_PASSWORD}'
  slack_api_url: '${SLACK_WEBHOOK_URL}'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

# Alert routing
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'team'
  routes:
    # Critical alerts go to PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    # Database alerts
    - match:
        category: database
      receiver: 'dba-team'

    # Security alerts
    - match:
        category: security
      receiver: 'security-team'

# Alert receivers
receivers:
  - name: 'team'
    email_configs:
      - to: 'team@example.com'
        headers:
          subject: '[AIShell] {{ .GroupLabels.alertname }}'
    slack_configs:
      - channel: '#ai-shell-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
        severity: '{{ .GroupLabels.severity }}'
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'

  - name: 'dba-team'
    email_configs:
      - to: 'dba@example.com'
    slack_configs:
      - channel: '#dba-alerts'

  - name: 'security-team'
    email_configs:
      - to: 'security@example.com'
    slack_configs:
      - channel: '#security-alerts'

# Inhibition rules
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
```

---

## Log Aggregation

### ELK Stack Setup

#### Elasticsearch

```yaml
# docker-compose-elk.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.10.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
      - /var/log/ai-shell:/var/log/ai-shell:ro
    environment:
      - "LS_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.10.0
    environment:
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=${ELASTIC_PASSWORD}
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch-data:
```

#### Logstash Pipeline

```ruby
# logstash/pipeline/ai-shell.conf
input {
  file {
    path => "/var/log/ai-shell/app.log"
    codec => "json"
    type => "application"
  }

  file {
    path => "/var/log/ai-shell/error.log"
    codec => "json"
    type => "error"
  }

  file {
    path => "/var/log/ai-shell/audit.log"
    codec => "json"
    type => "audit"
  }

  file {
    path => "/var/log/ai-shell/query.log"
    codec => "json"
    type => "query"
  }
}

filter {
  # Parse timestamp
  date {
    match => ["timestamp", "ISO8601"]
  }

  # Add hostname
  mutate {
    add_field => { "hostname" => "%{HOSTNAME}" }
  }

  # Geolocate IP addresses
  geoip {
    source => "client_ip"
    target => "geoip"
  }

  # Parse user agent
  useragent {
    source => "user_agent"
    target => "user_agent_parsed"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "ai-shell-%{type}-%{+YYYY.MM.dd}"
    user => "elastic"
    password => "${ELASTIC_PASSWORD}"
  }

  # Also output to stdout for debugging
  stdout {
    codec => rubydebug
  }
}
```

### Fluentd Alternative

```yaml
# fluentd/fluent.conf
<source>
  @type tail
  path /var/log/ai-shell/*.log
  pos_file /var/log/ai-shell/fluentd.pos
  tag ai-shell.*
  <parse>
    @type json
    time_key timestamp
    time_format %Y-%m-%dT%H:%M:%S.%LZ
  </parse>
</source>

<filter ai-shell.**>
  @type record_transformer
  <record>
    hostname "#{Socket.gethostname}"
    environment "production"
  </record>
</filter>

<match ai-shell.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  user elastic
  password ${ELASTIC_PASSWORD}
  logstash_format true
  logstash_prefix ai-shell
  include_tag_key true
  type_name _doc
  <buffer>
    @type file
    path /var/log/fluent/buffer
    flush_interval 10s
    flush_thread_count 2
  </buffer>
</match>
```

---

## Health Check Endpoints

### Application Health Checks

```typescript
// src/health/health-check.ts
export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime: number;
  checks: {
    database: HealthStatus;
    redis: HealthStatus;
    disk: HealthStatus;
    memory: HealthStatus;
    llm: HealthStatus;
  };
}

export interface HealthStatus {
  status: 'pass' | 'warn' | 'fail';
  timestamp: string;
  latency?: number;
  message?: string;
}
```

### Health Check Implementation

```yaml
# Health check configuration
health:
  endpoints:
    # Basic health
    - path: /health
      method: GET
      timeout: 5000
      checks:
        - database
        - redis
        - disk

    # Detailed health
    - path: /health/detailed
      method: GET
      timeout: 10000
      checks:
        - database
        - redis
        - disk
        - memory
        - llm
        - cache

    # Liveness probe
    - path: /health/live
      method: GET
      timeout: 1000
      checks:
        - process

    # Readiness probe
    - path: /health/ready
      method: GET
      timeout: 5000
      checks:
        - database
        - redis
```

### Kubernetes Health Checks

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: ai-shell
        livenessProbe:
          httpGet:
            path: /health/live
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /health/ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3

        startupProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 0
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 30
```

---

## Metrics Collection

### Application Metrics

```typescript
// Metrics to collect
export const metrics = {
  // Request metrics
  requests_total: new Counter({
    name: 'ai_shell_requests_total',
    help: 'Total number of requests',
    labelNames: ['method', 'endpoint', 'status']
  }),

  // Request duration
  request_duration: new Histogram({
    name: 'ai_shell_request_duration_seconds',
    help: 'Request duration in seconds',
    labelNames: ['method', 'endpoint'],
    buckets: [0.1, 0.5, 1, 2, 5, 10]
  }),

  // Query metrics
  query_duration: new Histogram({
    name: 'ai_shell_query_duration_seconds',
    help: 'Query execution duration',
    labelNames: ['database', 'operation'],
    buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5]
  }),

  // Database connections
  db_connections_active: new Gauge({
    name: 'ai_shell_db_connections_active',
    help: 'Active database connections'
  }),

  // Cache metrics
  cache_hits: new Counter({
    name: 'ai_shell_cache_hits_total',
    help: 'Total cache hits'
  }),

  cache_misses: new Counter({
    name: 'ai_shell_cache_misses_total',
    help: 'Total cache misses'
  }),

  // Error metrics
  errors_total: new Counter({
    name: 'ai_shell_errors_total',
    help: 'Total errors',
    labelNames: ['error_type', 'severity']
  }),

  // Backup metrics
  backup_last_success: new Gauge({
    name: 'ai_shell_backup_last_success_timestamp',
    help: 'Timestamp of last successful backup'
  })
};
```

---

## Distributed Tracing

### OpenTelemetry Setup

```typescript
// src/tracing/setup.ts
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { JaegerExporter } from '@opentelemetry/exporter-jaeger';

const sdk = new NodeSDK({
  traceExporter: new JaegerExporter({
    endpoint: 'http://jaeger:14268/api/traces'
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-fs': {
        enabled: false
      }
    })
  ]
});

sdk.start();
```

---

## Monitoring Best Practices

1. **Monitor the Four Golden Signals:**
   - Latency
   - Traffic
   - Errors
   - Saturation

2. **Set Appropriate Alert Thresholds:**
   - Avoid alert fatigue
   - Use multi-level alerting (warning, critical)
   - Include actionable context

3. **Implement SLOs (Service Level Objectives):**
   - Define target availability (e.g., 99.9%)
   - Measure error budget
   - Track SLO compliance

4. **Regular Review:**
   - Weekly dashboard reviews
   - Monthly alert tuning
   - Quarterly SLO review

---

**Document Version:** 1.0.0
**Last Updated:** October 29, 2025
**Maintained By:** AIShell DevOps Team
