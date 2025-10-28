# High Availability Setup Guide

**Version:** 2.0.0
**Last Updated:** October 28, 2025
**Target Audience:** DevOps engineers, system administrators

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture for High Availability](#architecture-for-high-availability)
3. [Load Balancing Configuration](#load-balancing-configuration)
4. [Database Clustering](#database-clustering)
5. [Failover Configuration](#failover-configuration)
6. [Monitoring and Health Checks](#monitoring-and-health-checks)
7. [Testing HA Setup](#testing-ha-setup)
8. [Disaster Recovery](#disaster-recovery)
9. [Performance Tuning](#performance-tuning)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers deploying AI-Shell in a high-availability (HA) configuration to ensure maximum uptime, fault tolerance, and scalability for production environments.

### Goals

- **99.99% Uptime**: Minimize service interruptions
- **Auto-Recovery**: Automatic failover on component failure
- **Horizontal Scalability**: Scale out to handle increased load
- **Zero-Downtime Deployments**: Update without service interruption
- **Data Integrity**: No data loss during failures

### Target SLAs

| Metric | Target | Description |
|--------|--------|-------------|
| Availability | 99.99% | ~4 minutes downtime/month |
| RTO (Recovery Time Objective) | < 5 minutes | Time to restore service |
| RPO (Recovery Point Objective) | < 1 minute | Maximum data loss |
| Response Time (p95) | < 200ms | 95th percentile response time |
| Throughput | 10,000+ qps | Queries per second |

---

## Architecture for High Availability

### Reference Architecture

```
                    ┌─────────────────────┐
                    │   DNS / CDN         │
                    │   (Route53/CloudFlare)│
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Global Load        │
                    │  Balancer (ALB/ELB) │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐    ┌───────▼────────┐    ┌───────▼────────┐
│  AI-Shell      │    │  AI-Shell      │    │  AI-Shell      │
│  Instance 1    │    │  Instance 2    │    │  Instance 3    │
│  (AZ-1a)       │    │  (AZ-1b)       │    │  (AZ-1c)       │
└───────┬────────┘    └───────┬────────┘    └───────┬────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Internal LB        │
                    │  (for services)     │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐    ┌───────▼────────┐    ┌───────▼────────┐
│  PostgreSQL    │◄──►│  PostgreSQL    │◄──►│  PostgreSQL    │
│  Primary       │    │  Standby-1     │    │  Standby-2     │
│  (AZ-1a)       │    │  (AZ-1b)       │    │  (AZ-1c)       │
└────────────────┘    └────────────────┘    └────────────────┘
        │
        ▼
┌────────────────────────────────────┐
│  Shared Services (HA)              │
│  ┌──────────┐  ┌──────────┐       │
│  │  Redis   │  │  Redis   │       │
│  │  Primary │  │  Replica │       │
│  └──────────┘  └──────────┘       │
│  ┌──────────┐  ┌──────────┐       │
│  │  Vector  │  │  Vector  │       │
│  │  Store 1 │  │  Store 2 │       │
│  └──────────┘  └──────────┘       │
└────────────────────────────────────┘
```

### Key Components

1. **Multiple Availability Zones**: Deploy across 3+ AZs
2. **Load Balancing**: Distribute traffic across instances
3. **Database Replication**: Primary with multiple standbys
4. **Shared Services**: Replicated Redis and vector stores
5. **Health Monitoring**: Continuous health checks
6. **Auto-Scaling**: Automatic capacity adjustment

### Redundancy Levels

- **N+1**: One extra instance beyond capacity needs
- **N+2**: Two extra instances (recommended for production)
- **2N**: Full duplication (for critical systems)

---

## Load Balancing Configuration

### AWS Application Load Balancer (ALB)

#### CloudFormation Template

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'AI-Shell HA Load Balancer'

Resources:
  # Application Load Balancer
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: aishell-alb
      Type: application
      Scheme: internet-facing
      IpAddressType: ipv4
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
        - !Ref PublicSubnet3
      Tags:
        - Key: Name
          Value: aishell-alb

  # Target Group
  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: aishell-targets
      Port: 8000
      Protocol: HTTP
      VpcId: !Ref VPC
      HealthCheckEnabled: true
      HealthCheckPath: /health
      HealthCheckProtocol: HTTP
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
      TargetGroupAttributes:
        - Key: deregistration_delay.timeout_seconds
          Value: '30'
        - Key: stickiness.enabled
          Value: 'true'
        - Key: stickiness.type
          Value: 'lb_cookie'
        - Key: stickiness.lb_cookie.duration_seconds
          Value: '3600'

  # Listener
  HTTPSListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 443
      Protocol: HTTPS
      SslPolicy: ELBSecurityPolicy-TLS-1-2-2017-01
      Certificates:
        - CertificateArn: !Ref SSLCertificate
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup

  # HTTP to HTTPS Redirect
  HTTPListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 80
      Protocol: HTTP
      DefaultActions:
        - Type: redirect
          RedirectConfig:
            Protocol: HTTPS
            Port: '443'
            StatusCode: HTTP_301
```

#### Terraform Configuration

```hcl
# Load Balancer
resource "aws_lb" "aishell" {
  name               = "aishell-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id

  enable_deletion_protection = true
  enable_http2              = true
  enable_cross_zone_load_balancing = true

  tags = {
    Name        = "aishell-alb"
    Environment = var.environment
  }
}

# Target Group
resource "aws_lb_target_group" "aishell" {
  name     = "aishell-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 3600
    enabled         = true
  }

  deregistration_delay = 30
}

# Listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.aishell.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.aishell.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.aishell.arn
  }
}
```

### NGINX Load Balancer

#### Configuration File

```nginx
# /etc/nginx/nginx.conf

upstream aishell_backend {
    # Load balancing method
    least_conn;  # or: ip_hash, round_robin

    # Backend servers
    server 10.0.1.10:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8000 max_fails=3 fail_timeout=30s;

    # Health check
    keepalive 32;
    keepalive_timeout 60s;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name aishell.example.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name aishell.example.com;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/aishell.crt;
    ssl_certificate_key /etc/nginx/ssl/aishell.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/aishell_access.log;
    error_log /var/log/nginx/aishell_error.log;

    # Proxy settings
    location / {
        proxy_pass http://aishell_backend;
        proxy_http_version 1.1;

        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://aishell_backend/health;
        access_log off;
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://aishell_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### HAProxy Configuration

```haproxy
# /etc/haproxy/haproxy.cfg

global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

    # SSL
    ssl-default-bind-ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384
    ssl-default-bind-options no-sslv3 no-tlsv10 no-tlsv11
    tune.ssl.default-dh-param 2048

defaults
    log global
    mode http
    option httplog
    option dontlognull
    option http-server-close
    option forwardfor except 127.0.0.0/8
    option redispatch
    retries 3
    timeout connect 5000
    timeout client 50000
    timeout server 50000

# Stats interface
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
    stats admin if LOCALHOST

# Frontend
frontend aishell_frontend
    bind *:80
    bind *:443 ssl crt /etc/haproxy/certs/aishell.pem

    # Redirect HTTP to HTTPS
    redirect scheme https code 301 if !{ ssl_fc }

    # ACLs
    acl is_health path /health

    # Use backend
    default_backend aishell_backend

# Backend
backend aishell_backend
    balance leastconn
    option httpchk GET /health
    http-check expect status 200

    # Server health checks
    default-server inter 3s rise 2 fall 3

    # Backend servers
    server app1 10.0.1.10:8000 check
    server app2 10.0.1.11:8000 check
    server app3 10.0.1.12:8000 check

    # Backup server
    server app4 10.0.1.13:8000 check backup
```

---

## Database Clustering

### PostgreSQL High Availability

#### Streaming Replication Setup

**Primary Server Configuration:**

```ini
# /etc/postgresql/14/main/postgresql.conf

# Replication settings
wal_level = replica
max_wal_senders = 5
max_replication_slots = 5
wal_keep_size = 1GB
hot_standby = on
hot_standby_feedback = on

# Performance
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 20MB
min_wal_size = 2GB
max_wal_size = 8GB

# Connection pooling
max_connections = 200
```

```ini
# /etc/postgresql/14/main/pg_hba.conf

# Replication connections
host    replication     replicator      10.0.1.0/24     md5
```

**Create Replication User:**

```sql
-- On primary server
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'secure_password';
```

**Standby Server Configuration:**

```bash
# Stop PostgreSQL on standby
sudo systemctl stop postgresql

# Remove existing data directory
sudo rm -rf /var/lib/postgresql/14/main/*

# Create base backup from primary
sudo -u postgres pg_basebackup \
    -h 10.0.1.10 \
    -D /var/lib/postgresql/14/main \
    -U replicator \
    -P -v -R

# Start PostgreSQL on standby
sudo systemctl start postgresql
```

**Standby Configuration:**

```ini
# /var/lib/postgresql/14/main/postgresql.auto.conf

primary_conninfo = 'host=10.0.1.10 port=5432 user=replicator password=secure_password'
primary_slot_name = 'standby_1'
```

#### Automatic Failover with Patroni

**Patroni Configuration:**

```yaml
# /etc/patroni/patroni.yml

scope: aishell-cluster
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.1.10:8008

etcd:
  hosts:
    - 10.0.2.10:2379
    - 10.0.2.11:2379
    - 10.0.2.12:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 200
        shared_buffers: 4GB
        effective_cache_size: 12GB

  initdb:
    - encoding: UTF8
    - data-checksums

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 10.0.1.10:5432
  data_dir: /var/lib/postgresql/14/main
  pgpass: /tmp/pgpass
  authentication:
    replication:
      username: replicator
      password: secure_password
    superuser:
      username: postgres
      password: secure_password

  parameters:
    unix_socket_directories: '/var/run/postgresql'

tags:
  nofailover: false
  noloadbalance: false
  clonefrom: false
  nosync: false
```

**Start Patroni Cluster:**

```bash
# Install Patroni
pip install patroni[etcd] psycopg2-binary

# Start Patroni on each node
patroni /etc/patroni/patroni.yml

# Check cluster status
patronictl -c /etc/patroni/patroni.yml list
```

### Redis High Availability

#### Redis Sentinel Setup

**Redis Configuration:**

```ini
# /etc/redis/redis.conf

# Primary server
bind 0.0.0.0
port 6379
protected-mode yes
requirepass secure_redis_password

# Replication
replicaof 10.0.1.10 6379
masterauth secure_redis_password

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfilename "appendonly.aof"
```

**Sentinel Configuration:**

```ini
# /etc/redis/sentinel.conf

port 26379
sentinel monitor aishell-redis 10.0.1.10 6379 2
sentinel auth-pass aishell-redis secure_redis_password
sentinel down-after-milliseconds aishell-redis 5000
sentinel parallel-syncs aishell-redis 1
sentinel failover-timeout aishell-redis 10000
```

**Start Sentinel:**

```bash
# Start Redis on each node
sudo systemctl start redis

# Start Sentinel on each node
redis-sentinel /etc/redis/sentinel.conf
```

---

## Failover Configuration

### Automatic Failover

#### Health Check Script

```bash
#!/bin/bash
# /usr/local/bin/aishell-health-check.sh

HEALTH_URL="http://localhost:8000/health"
MAX_RETRIES=3
RETRY_INTERVAL=5

check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")
    if [ "$response" = "200" ]; then
        return 0
    else
        return 1
    fi
}

# Retry logic
for i in $(seq 1 $MAX_RETRIES); do
    if check_health; then
        echo "Health check passed"
        exit 0
    fi

    if [ $i -lt $MAX_RETRIES ]; then
        echo "Health check failed, retrying in ${RETRY_INTERVAL}s..."
        sleep $RETRY_INTERVAL
    fi
done

echo "Health check failed after $MAX_RETRIES attempts"
exit 1
```

#### Keepalived Configuration

```ini
# /etc/keepalived/keepalived.conf

vrrp_script check_aishell {
    script "/usr/local/bin/aishell-health-check.sh"
    interval 10
    weight -20
    fall 3
    rise 2
}

vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass secure_password
    }

    virtual_ipaddress {
        10.0.1.100/24
    }

    track_script {
        check_aishell
    }

    notify_master "/usr/local/bin/aishell-promote-master.sh"
    notify_backup "/usr/local/bin/aishell-demote-backup.sh"
    notify_fault "/usr/local/bin/aishell-fault-handler.sh"
}
```

### Database Failover

**Promotion Script:**

```bash
#!/bin/bash
# /usr/local/bin/promote-standby.sh

set -e

STANDBY_HOST="10.0.1.11"
PRIMARY_HOST="10.0.1.10"

# Promote standby to primary
ssh postgres@$STANDBY_HOST "pg_ctl promote -D /var/lib/postgresql/14/main"

# Wait for promotion
sleep 5

# Update application configuration
sed -i "s/$PRIMARY_HOST/$STANDBY_HOST/g" /etc/aishell/database.conf

# Restart application
systemctl restart aishell

echo "Failover completed successfully"
```

---

## Monitoring and Health Checks

### Health Check Endpoint

```typescript
// src/health/health-check.ts

import { HealthCheckService } from './health-check-service';

export interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: {
    [key: string]: ComponentHealth;
  };
}

export interface ComponentHealth {
  status: 'up' | 'down' | 'degraded';
  responseTime?: number;
  message?: string;
}

export class HealthCheckEndpoint {
  async check(): Promise<HealthCheckResult> {
    const checks = await Promise.allSettled([
      this.checkDatabase(),
      this.checkRedis(),
      this.checkVectorStore(),
      this.checkLLM(),
    ]);

    const components = {
      database: this.parseResult(checks[0]),
      redis: this.parseResult(checks[1]),
      vectorStore: this.parseResult(checks[2]),
      llm: this.parseResult(checks[3]),
    };

    const overallStatus = this.determineOverallStatus(components);

    return {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      components,
    };
  }

  private async checkDatabase(): Promise<ComponentHealth> {
    const start = Date.now();
    try {
      await pool.query('SELECT 1');
      return {
        status: 'up',
        responseTime: Date.now() - start,
      };
    } catch (error) {
      return {
        status: 'down',
        message: error.message,
      };
    }
  }

  private async checkRedis(): Promise<ComponentHealth> {
    const start = Date.now();
    try {
      await redis.ping();
      return {
        status: 'up',
        responseTime: Date.now() - start,
      };
    } catch (error) {
      return {
        status: 'down',
        message: error.message,
      };
    }
  }

  private determineOverallStatus(components: Record<string, ComponentHealth>): string {
    const statuses = Object.values(components).map(c => c.status);

    if (statuses.every(s => s === 'up')) return 'healthy';
    if (statuses.some(s => s === 'down')) return 'unhealthy';
    return 'degraded';
  }
}
```

### Prometheus Metrics

```typescript
// src/monitoring/metrics.ts

import { Counter, Histogram, Gauge } from 'prom-client';

export const metrics = {
  // Request metrics
  httpRequestsTotal: new Counter({
    name: 'aishell_http_requests_total',
    help: 'Total number of HTTP requests',
    labelNames: ['method', 'route', 'status'],
  }),

  httpRequestDuration: new Histogram({
    name: 'aishell_http_request_duration_seconds',
    help: 'HTTP request duration in seconds',
    labelNames: ['method', 'route'],
    buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10],
  }),

  // Database metrics
  dbConnectionsActive: new Gauge({
    name: 'aishell_db_connections_active',
    help: 'Number of active database connections',
  }),

  dbQueryDuration: new Histogram({
    name: 'aishell_db_query_duration_seconds',
    help: 'Database query duration in seconds',
    buckets: [0.01, 0.05, 0.1, 0.5, 1, 5],
  }),

  // System metrics
  memoryUsage: new Gauge({
    name: 'aishell_memory_usage_bytes',
    help: 'Memory usage in bytes',
  }),

  cpuUsage: new Gauge({
    name: 'aishell_cpu_usage_percent',
    help: 'CPU usage percentage',
  }),
};
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "AI-Shell HA Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(aishell_http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(aishell_http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(aishell_http_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      },
      {
        "title": "Database Connections",
        "targets": [
          {
            "expr": "aishell_db_connections_active"
          }
        ]
      }
    ]
  }
}
```

---

## Testing HA Setup

### Chaos Engineering

**Test Scenarios:**

1. **Instance Failure**
```bash
# Simulate instance failure
sudo systemctl stop aishell

# Verify failover
curl -v https://aishell.example.com/health

# Check load balancer logs
tail -f /var/log/nginx/access.log
```

2. **Database Failover**
```bash
# Stop primary database
sudo systemctl stop postgresql

# Verify standby promotion
patronictl -c /etc/patroni/patroni.yml failover
patronictl -c /etc/patroni/patroni.yml list

# Check application connectivity
curl https://aishell.example.com/health
```

3. **Network Partition**
```bash
# Simulate network partition using iptables
sudo iptables -A INPUT -s 10.0.1.11 -j DROP
sudo iptables -A OUTPUT -d 10.0.1.11 -j DROP

# Verify cluster behavior
# Restore network
sudo iptables -F
```

### Load Testing

```bash
# Install load testing tools
npm install -g autocannon

# Run load test
autocannon -c 100 -d 60 -p 10 https://aishell.example.com/api/v1/query

# Apache Bench
ab -n 10000 -c 100 https://aishell.example.com/

# k6 load test
k6 run --vus 100 --duration 60s load-test.js
```

**k6 Script:**

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  let response = http.get('https://aishell.example.com/health');

  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });

  sleep(1);
}
```

---

## Disaster Recovery

### Backup Strategy

```bash
# Automated backup script
#!/bin/bash
# /usr/local/bin/backup-aishell.sh

BACKUP_DIR="/backups/aishell"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="s3://aishell-backups"

# Database backup
pg_dump -h localhost -U postgres aishell_production \
    | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# Upload to S3
aws s3 cp "$BACKUP_DIR/db_$TIMESTAMP.sql.gz" \
    "$S3_BUCKET/database/" --storage-class STANDARD_IA

# Verify backup
aws s3 ls "$S3_BUCKET/database/db_$TIMESTAMP.sql.gz"

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

### Recovery Procedures

```bash
# Restore from backup
#!/bin/bash
# /usr/local/bin/restore-aishell.sh

BACKUP_FILE="$1"
S3_BUCKET="s3://aishell-backups"

# Download backup from S3
aws s3 cp "$S3_BUCKET/database/$BACKUP_FILE" /tmp/

# Stop application
systemctl stop aishell

# Restore database
gunzip < "/tmp/$BACKUP_FILE" | psql -h localhost -U postgres aishell_production

# Start application
systemctl start aishell

echo "Restore completed"
```

---

## Performance Tuning

### Connection Pooling

```typescript
// Connection pool configuration
const pool = new Pool({
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT),
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,

  // Pool settings
  min: 10,              // Minimum connections
  max: 100,             // Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,

  // Performance
  keepAlive: true,
  keepAliveInitialDelayMillis: 10000,
});
```

### Caching Strategy

```typescript
// Multi-level caching
class CacheManager {
  private l1Cache: Map<string, any>;  // In-memory
  private l2Cache: Redis;              // Redis

  async get(key: string): Promise<any> {
    // L1: Memory cache
    if (this.l1Cache.has(key)) {
      return this.l1Cache.get(key);
    }

    // L2: Redis cache
    const cached = await this.l2Cache.get(key);
    if (cached) {
      this.l1Cache.set(key, cached);
      return cached;
    }

    return null;
  }

  async set(key: string, value: any, ttl: number = 3600): Promise<void> {
    // Set in both caches
    this.l1Cache.set(key, value);
    await this.l2Cache.setex(key, ttl, JSON.stringify(value));
  }
}
```

---

## Troubleshooting

### Common Issues

**Split-Brain Scenario:**
- Use quorum-based voting (etcd, Consul)
- Implement fencing mechanisms
- Monitor cluster health continuously

**Connection Exhaustion:**
- Increase max_connections in PostgreSQL
- Implement connection pooling (PgBouncer)
- Set proper pool limits in application

**Replication Lag:**
- Monitor replication lag: `SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) FROM pg_stat_replication;`
- Increase wal_keep_size
- Use replication slots

---

## Resources

- [PostgreSQL HA Documentation](https://www.postgresql.org/docs/current/high-availability.html)
- [Patroni Documentation](https://patroni.readthedocs.io/)
- [Redis Sentinel](https://redis.io/topics/sentinel)
- [Prometheus Monitoring](https://prometheus.io/docs/introduction/overview/)

---

**Document Version:** 2.0.0
**Last Updated:** October 28, 2025
**Next Review:** January 2026
