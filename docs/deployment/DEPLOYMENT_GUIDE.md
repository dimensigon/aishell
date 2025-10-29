# AIShell Deployment Guide

Complete guide for deploying AIShell in production environments including installation methods, configuration, and cloud provider integration.

## Table of Contents

1. [Installation Methods](#installation-methods)
2. [Configuration Setup](#configuration-setup)
3. [Database Configuration](#database-configuration)
4. [Environment Variables](#environment-variables)
5. [SSL/TLS Setup](#ssltls-setup)
6. [Cloud Provider Integration](#cloud-provider-integration)
7. [High Availability Setup](#high-availability-setup)
8. [Load Balancing](#load-balancing-considerations)
9. [Deployment Scenarios](#deployment-scenarios)
10. [Troubleshooting](#troubleshooting)

---

## Installation Methods

### Method 1: NPM Installation (Recommended)

```bash
# Install globally
npm install -g ai-shell

# Verify installation
ai-shell --version

# Install in project
npm install ai-shell --save

# For development
npm install ai-shell --save-dev
```

### Method 2: Docker Deployment

#### Using Pre-built Image

```bash
# Pull official image
docker pull aishell/ai-shell:latest

# Run container
docker run -d \
  --name ai-shell \
  -p 3000:3000 \
  -e ANTHROPIC_API_KEY="your-api-key" \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -v /path/to/config:/app/config \
  -v /path/to/logs:/app/logs \
  aishell/ai-shell:latest

# View logs
docker logs -f ai-shell

# Access shell
docker exec -it ai-shell ai-shell
```

#### Building Custom Image

```dockerfile
# Dockerfile
FROM node:20-alpine

# Install dependencies
RUN apk add --no-cache \
    postgresql-client \
    mysql-client \
    mongodb-tools \
    redis \
    openssl

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build TypeScript
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S aishell && \
    adduser -S aishell -u 1001

# Set ownership
RUN chown -R aishell:aishell /app

# Switch to non-root user
USER aishell

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => { process.exit(r.statusCode === 200 ? 0 : 1); });"

# Start application
CMD ["node", "dist/cli/index.js"]
```

```bash
# Build image
docker build -t ai-shell:custom .

# Run custom image
docker run -d --name ai-shell-prod ai-shell:custom
```

#### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  ai-shell:
    image: aishell/ai-shell:latest
    container_name: ai-shell
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=info
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - ai-shell-data:/app/data
    depends_on:
      - postgres
      - redis
    networks:
      - ai-shell-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15-alpine
    container_name: ai-shell-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=ai_shell
      - POSTGRES_USER=ai_shell
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - ai-shell-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ai_shell"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: ai-shell-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - ai-shell-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  ai-shell-data:
  postgres-data:
  redis-data:

networks:
  ai-shell-network:
    driver: bridge
```

```bash
# Deploy with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale ai-shell=3

# Stop services
docker-compose down

# Remove volumes
docker-compose down -v
```

### Method 3: Source Installation

```bash
# Clone repository
git clone https://github.com/your-org/ai-shell.git
cd ai-shell

# Install dependencies
npm install

# Build TypeScript
npm run build

# Run tests
npm test

# Start production
NODE_ENV=production npm start

# Or use PM2 for process management
npm install -g pm2
pm2 start dist/cli/index.js --name ai-shell
pm2 save
pm2 startup
```

---

## Configuration Setup

### Configuration File Structure

Create `/etc/ai-shell/config.yaml` or `~/.ai-shell/config.yaml`:

```yaml
# AI-Shell Production Configuration

# Application Settings
app:
  name: ai-shell
  version: 1.0.0
  environment: production
  port: 3000
  host: 0.0.0.0

# Database Connections
databases:
  production:
    type: postgres
    host: db.production.internal
    port: 5432
    database: ai_shell_prod
    username: ai_shell_user
    # Use vault or environment variable for password
    ssl:
      enabled: true
      rejectUnauthorized: true
      ca: /path/to/ca-certificate.crt
    pool:
      min: 10
      max: 100
      acquireTimeoutMillis: 30000
      idleTimeoutMillis: 30000
      createTimeoutMillis: 3000
      destroyTimeoutMillis: 5000
      reapIntervalMillis: 1000

  staging:
    type: postgres
    host: db.staging.internal
    port: 5432
    database: ai_shell_staging
    username: ai_shell_user
    pool:
      min: 5
      max: 20

# LLM Configuration
llm:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
  temperature: 0.1
  maxTokens: 4096
  timeout: 30000
  retries: 3
  backoff:
    type: exponential
    initial: 1000
    max: 10000
    multiplier: 2

# Caching
cache:
  enabled: true
  provider: redis
  url: redis://redis.production.internal:6379
  ttl: 3600
  maxSize: 1000
  keyPrefix: ai-shell:
  strategies:
    frequent:
      ttl: 7200
    static:
      ttl: 86400
    analytical:
      ttl: 600

# Security
security:
  vault:
    enabled: true
    encryption: aes-256-gcm
    keyDerivation: pbkdf2
    iterations: 100000
    saltLength: 32
  audit:
    enabled: true
    destination: /var/log/ai-shell/audit.log
    rotation:
      enabled: true
      frequency: daily
      maxFiles: 90
      maxSize: 100m
    format: json
  sql_injection_prevention: true
  rate_limiting:
    enabled: true
    window: 60000
    max_requests: 100
    max_requests_per_hour: 1000
    block_duration: 3600000
  input_validation:
    enabled: true
    max_query_length: 10000
    sanitize: true
  pii_detection:
    enabled: true
    redact: true
    patterns:
      - ssn
      - credit_card
      - email
      - phone

# Logging
logging:
  level: info
  format: json
  destination: /var/log/ai-shell/app.log
  rotation:
    enabled: true
    frequency: daily
    maxFiles: 30
    maxSize: 100m
  transports:
    - type: file
      level: info
    - type: console
      level: warn
    - type: daily-rotate-file
      level: info
      datePattern: YYYY-MM-DD
      zippedArchive: true

# Monitoring
monitoring:
  enabled: true
  interval: 60000
  metrics:
    enabled: true
    port: 9090
    path: /metrics
  health_check:
    enabled: true
    path: /health
    timeout: 5000
  exporters:
    prometheus:
      enabled: true
      port: 9090
      endpoint: /metrics
    grafana:
      enabled: false

# Backup
backup:
  enabled: true
  schedule:
    full:
      cron: "0 2 * * 0"
      retention: 4
    incremental:
      cron: "0 2 * * 1-6"
      retention: 7
  compression: gzip
  encryption: aes-256
  destination: /backups/ai-shell
  cloud:
    enabled: true
    provider: aws-s3
    bucket: ai-shell-backups
    region: us-east-1
    encryption: AES256
    storage_class: STANDARD_IA

# Performance
performance:
  query_timeout: 30000
  connection_timeout: 5000
  idle_timeout: 60000
  max_query_size: 1048576  # 1MB
  pool_size: 100
  worker_threads: 4
  optimization:
    auto_optimize: true
    threshold_ms: 1000
    cache_plans: true

# Notifications
notifications:
  email:
    enabled: true
    smtp:
      host: smtp.production.internal
      port: 587
      secure: true
      auth:
        user: ai-shell@example.com
    from: ai-shell@example.com
    to:
      - ops-team@example.com
      - dba-team@example.com
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
    channel: "#ai-shell-alerts"
    username: "AI-Shell Bot"
```

### Load Configuration

```bash
# From default location
ai-shell --config ~/.ai-shell/config.yaml

# From custom location
ai-shell --config /etc/ai-shell/production.yaml

# Validate configuration
ai-shell config validate

# Show current configuration
ai-shell config show
```

---

## Database Configuration

### PostgreSQL Setup (Production Ready)

#### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get install postgresql-15 postgresql-contrib

# RHEL/CentOS
sudo dnf install postgresql15-server postgresql15-contrib

# Initialize database
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 2. Create Database and User

```sql
-- Connect as postgres user
sudo -u postgres psql

-- Create database
CREATE DATABASE ai_shell_prod;

-- Create user
CREATE USER ai_shell_user WITH ENCRYPTED PASSWORD 'secure-password-here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ai_shell_prod TO ai_shell_user;

-- Connect to database
\c ai_shell_prod

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO ai_shell_user;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

#### 3. Configure Connection Pooling (PgBouncer)

```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
ai_shell_prod = host=localhost port=5432 dbname=ai_shell_prod

[pgbouncer]
listen_port = 6432
listen_addr = *
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 100
max_user_connections = 100
server_idle_timeout = 600
server_lifetime = 3600
server_connect_timeout = 15
query_timeout = 30
client_idle_timeout = 600
```

```bash
# Start PgBouncer
sudo systemctl start pgbouncer
sudo systemctl enable pgbouncer

# Connection string with PgBouncer
DATABASE_URL="postgresql://ai_shell_user:password@localhost:6432/ai_shell_prod"
```

#### 4. PostgreSQL Performance Tuning

```sql
-- postgresql.conf
shared_buffers = 4GB                    # 25% of RAM
effective_cache_size = 12GB             # 75% of RAM
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1                  # For SSD
effective_io_concurrency = 200          # For SSD
work_mem = 64MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4
```

### MySQL Setup (Partial Support)

```sql
-- Create database
CREATE DATABASE ai_shell_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'ai_shell_user'@'%' IDENTIFIED BY 'secure-password';

-- Grant privileges
GRANT ALL PRIVILEGES ON ai_shell_prod.* TO 'ai_shell_user'@'%';
FLUSH PRIVILEGES;
```

```ini
# /etc/mysql/my.cnf
[mysqld]
max_connections = 500
innodb_buffer_pool_size = 8G
innodb_log_file_size = 512M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT
```

### MongoDB Setup (Client Ready)

```javascript
// MongoDB connection
use ai_shell_prod

db.createUser({
  user: "ai_shell_user",
  pwd: "secure-password",
  roles: [
    { role: "readWrite", db: "ai_shell_prod" },
    { role: "dbAdmin", db: "ai_shell_prod" }
  ]
})
```

```yaml
# mongod.conf
storage:
  dbPath: /var/lib/mongodb
  engine: wiredTiger
  wiredTiger:
    engineConfig:
      cacheSizeGB: 8

replication:
  replSetName: ai_shell_rs

net:
  port: 27017
  bindIp: 0.0.0.0

security:
  authorization: enabled
```

### Redis Setup (Client Ready)

```bash
# /etc/redis/redis.conf
bind 0.0.0.0
port 6379
requirepass secure-redis-password
maxmemory 512mb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000
```

---

## Environment Variables

### Production Environment Variables

```bash
# Create .env.production
cat > .env.production << 'EOF'
# Application
NODE_ENV=production
APP_NAME=ai-shell
APP_VERSION=1.0.0
PORT=3000
HOST=0.0.0.0

# Database
DATABASE_URL=postgresql://user:pass@db.prod.internal:5432/ai_shell_prod
DB_POOL_MIN=10
DB_POOL_MAX=100
DB_SSL=true

# LLM Provider
ANTHROPIC_API_KEY=your-anthropic-api-key-here
AI_MODEL=claude-sonnet-4-5-20250929
AI_TEMPERATURE=0.1
AI_MAX_TOKENS=4096
AI_TIMEOUT=30000

# Redis Cache
REDIS_URL=redis://:password@redis.prod.internal:6379
REDIS_CACHE_TTL=3600
REDIS_MAX_CONNECTIONS=50

# Security
ENCRYPTION_KEY=generate-strong-32-byte-key-here
JWT_SECRET=generate-strong-jwt-secret-here
SESSION_SECRET=generate-strong-session-secret-here

# Logging
LOG_LEVEL=info
LOG_FORMAT=json
LOG_DESTINATION=/var/log/ai-shell/app.log

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_PATH=/health

# Backup
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * 0"
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
BACKUP_BUCKET=ai-shell-backups

# Notifications
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=ai-shell@example.com
SMTP_PASS=smtp-password-here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your-webhook

# Performance
QUERY_TIMEOUT=30000
CONNECTION_TIMEOUT=5000
IDLE_TIMEOUT=60000
MAX_CONNECTIONS=100

# Rate Limiting
RATE_LIMIT_WINDOW=60000
RATE_LIMIT_MAX=100
RATE_LIMIT_MAX_HOUR=1000
EOF
```

### Load Environment Variables

```bash
# Export from file
export $(cat .env.production | grep -v '^#' | xargs)

# Or use dotenv
npm install -g dotenv-cli
dotenv -e .env.production -- ai-shell

# Verify loaded variables
env | grep AI_
env | grep DATABASE_URL
```

---

## SSL/TLS Setup

### Database SSL Connections

#### PostgreSQL SSL

```yaml
# config.yaml
databases:
  production:
    ssl:
      enabled: true
      rejectUnauthorized: true
      ca: /path/to/ca-certificate.crt
      key: /path/to/client-key.key
      cert: /path/to/client-cert.crt
```

```sql
-- PostgreSQL server configuration
ssl = on
ssl_ca_file = '/etc/postgresql/ca-certificate.crt'
ssl_cert_file = '/etc/postgresql/server-certificate.crt'
ssl_key_file = '/etc/postgresql/server-key.key'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
ssl_prefer_server_ciphers = on
ssl_min_protocol_version = 'TLSv1.2'
```

#### MySQL SSL

```yaml
databases:
  mysql_prod:
    ssl:
      ca: /path/to/ca.pem
      key: /path/to/client-key.pem
      cert: /path/to/client-cert.pem
```

#### MongoDB SSL

```yaml
databases:
  mongo_prod:
    ssl:
      enabled: true
      tlsCAFile: /path/to/ca.pem
      tlsCertificateKeyFile: /path/to/client.pem
```

### Application HTTPS

```javascript
// src/server.ts
import * as https from 'https';
import * as fs from 'fs';

const options = {
  key: fs.readFileSync('/path/to/privkey.pem'),
  cert: fs.readFileSync('/path/to/cert.pem'),
  ca: fs.readFileSync('/path/to/chain.pem'),
  minVersion: 'TLSv1.2',
  ciphers: 'HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA'
};

https.createServer(options, app).listen(443);
```

### Let's Encrypt SSL Certificates

```bash
# Install Certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone \
  -d ai-shell.example.com \
  --email admin@example.com \
  --agree-tos

# Auto-renewal
sudo crontab -e
# Add: 0 0 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## Cloud Provider Integration

### AWS Deployment

#### 1. AWS EC2 Setup

```bash
# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.large \
  --key-name ai-shell-prod \
  --security-group-ids sg-xxxxxxxx \
  --subnet-id subnet-xxxxxxxx \
  --iam-instance-profile Name=ai-shell-role \
  --user-data file://install-script.sh

# install-script.sh
#!/bin/bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g ai-shell
# ... continue setup
```

#### 2. AWS RDS PostgreSQL

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier ai-shell-prod \
  --db-instance-class db.r5.large \
  --engine postgres \
  --engine-version 15.3 \
  --master-username admin \
  --master-user-password SecurePassword123 \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --backup-retention-period 30 \
  --multi-az \
  --vpc-security-group-ids sg-xxxxxxxx
```

#### 3. AWS S3 Backup

```yaml
# config.yaml
backup:
  cloud:
    enabled: true
    provider: aws-s3
    bucket: ai-shell-backups-prod
    region: us-east-1
    encryption: AES256
    storage_class: STANDARD_IA
    lifecycle:
      transition_to_glacier: 90
      expiration: 365
```

#### 4. AWS ECS Deployment

```json
// task-definition.json
{
  "family": "ai-shell",
  "taskRoleArn": "arn:aws:iam::123456789:role/ai-shell-task",
  "executionRoleArn": "arn:aws:iam::123456789:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "containerDefinitions": [{
    "name": "ai-shell",
    "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/ai-shell:latest",
    "cpu": 2048,
    "memory": 4096,
    "essential": true,
    "portMappings": [{
      "containerPort": 3000,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "NODE_ENV", "value": "production"}
    ],
    "secrets": [
      {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
      {"name": "ANTHROPIC_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/ai-shell",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"],
      "interval": 30,
      "timeout": 5,
      "retries": 3
    }
  }],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096"
}
```

### Azure Deployment

#### 1. Azure VM

```bash
# Create resource group
az group create --name ai-shell-rg --location eastus

# Create VM
az vm create \
  --resource-group ai-shell-rg \
  --name ai-shell-vm \
  --image UbuntuLTS \
  --size Standard_D4s_v3 \
  --admin-username azureuser \
  --generate-ssh-keys

# Open port
az vm open-port --port 3000 --resource-group ai-shell-rg --name ai-shell-vm
```

#### 2. Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group ai-shell-rg \
  --name ai-shell-db \
  --location eastus \
  --admin-user adminuser \
  --admin-password SecurePassword123 \
  --sku-name Standard_D4s_v3 \
  --tier GeneralPurpose \
  --storage-size 128 \
  --version 15
```

#### 3. Azure Container Instances

```bash
# Deploy container
az container create \
  --resource-group ai-shell-rg \
  --name ai-shell \
  --image aishell/ai-shell:latest \
  --cpu 2 \
  --memory 4 \
  --ports 3000 \
  --environment-variables \
    NODE_ENV=production \
  --secure-environment-variables \
    DATABASE_URL=postgresql://... \
    ANTHROPIC_API_KEY=...
```

### Google Cloud Platform

#### 1. GCE Instance

```bash
# Create instance
gcloud compute instances create ai-shell-instance \
  --machine-type=n1-standard-4 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB \
  --zone=us-central1-a

# Configure firewall
gcloud compute firewall-rules create allow-ai-shell \
  --allow tcp:3000 \
  --source-ranges 0.0.0.0/0 \
  --target-tags ai-shell
```

#### 2. Cloud SQL PostgreSQL

```bash
# Create instance
gcloud sql instances create ai-shell-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-4-16384 \
  --region=us-central1 \
  --network=default \
  --backup \
  --backup-start-time=02:00
```

#### 3. Google Kubernetes Engine

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-shell
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-shell
  template:
    metadata:
      labels:
        app: ai-shell
    spec:
      containers:
      - name: ai-shell
        image: gcr.io/project-id/ai-shell:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ai-shell-secrets
              key: database-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ai-shell-service
spec:
  selector:
    app: ai-shell
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer
```

---

## High Availability Setup

### Multi-Node Deployment

```yaml
# HA Architecture with 3 nodes
version: '3.8'

services:
  ai-shell-1:
    image: aishell/ai-shell:latest
    environment:
      - NODE_ID=1
      - CLUSTER_ENABLED=true
      - CLUSTER_NODES=ai-shell-1,ai-shell-2,ai-shell-3

  ai-shell-2:
    image: aishell/ai-shell:latest
    environment:
      - NODE_ID=2
      - CLUSTER_ENABLED=true
      - CLUSTER_NODES=ai-shell-1,ai-shell-2,ai-shell-3

  ai-shell-3:
    image: aishell/ai-shell:latest
    environment:
      - NODE_ID=3
      - CLUSTER_ENABLED=true
      - CLUSTER_NODES=ai-shell-1,ai-shell-2,ai-shell-3

  haproxy:
    image: haproxy:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
```

### Database Replication

#### PostgreSQL Streaming Replication

```sql
-- Primary server (postgresql.conf)
wal_level = replica
max_wal_senders = 10
wal_keep_size = 1GB
synchronous_commit = on

-- Create replication user
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replica-password';

-- pg_hba.conf
host replication replicator standby-ip/32 md5
```

```bash
# Standby server setup
pg_basebackup -h primary-ip -D /var/lib/postgresql/data -U replicator -P -v -R
```

### Redis Sentinel

```bash
# sentinel.conf
sentinel monitor mymaster redis-master 6379 2
sentinel auth-pass mymaster your-redis-password
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 10000

# Start sentinel
redis-sentinel /etc/redis/sentinel.conf
```

---

## Load Balancing Considerations

### HAProxy Configuration

```
# /etc/haproxy/haproxy.cfg
global
    maxconn 4096
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

defaults
    log global
    mode http
    option httplog
    option dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000

frontend ai-shell-frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/ai-shell.pem
    redirect scheme https if !{ ssl_fc }
    default_backend ai-shell-backend

    # Health check endpoint
    acl is_health_check path /health
    use_backend health_backend if is_health_check

backend ai-shell-backend
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200

    server ai-shell-1 10.0.1.10:3000 check inter 5000 rise 2 fall 3
    server ai-shell-2 10.0.1.11:3000 check inter 5000 rise 2 fall 3
    server ai-shell-3 10.0.1.12:3000 check inter 5000 rise 2 fall 3

backend health_backend
    server health 127.0.0.1:3000

listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
    stats auth admin:secure-password
```

### NGINX Load Balancer

```nginx
# /etc/nginx/nginx.conf
upstream ai-shell-cluster {
    least_conn;
    server 10.0.1.10:3000 weight=1 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:3000 weight=1 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:3000 weight=1 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 80;
    listen 443 ssl http2;
    server_name ai-shell.example.com;

    ssl_certificate /etc/ssl/certs/ai-shell.crt;
    ssl_certificate_key /etc/ssl/private/ai-shell.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Redirect HTTP to HTTPS
    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }

    location / {
        proxy_pass http://ai-shell-cluster;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://ai-shell-cluster;
        access_log off;
    }
}
```

---

## Deployment Scenarios

### Scenario 1: Single Server Deployment

**Best for:** Development, small teams, testing

```bash
# Install on single server
npm install -g ai-shell

# Configure
ai-shell config setup

# Start with PM2
pm2 start ai-shell --name "ai-shell" -i max
pm2 save
pm2 startup
```

### Scenario 2: Docker Deployment

**Best for:** Containerized environments, easy scaling

```bash
# Run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Scale application
docker-compose up -d --scale ai-shell=3
```

### Scenario 3: Kubernetes Deployment

**Best for:** Large-scale production, microservices

```bash
# Deploy to Kubernetes
kubectl apply -f kubernetes/

# Scale deployment
kubectl scale deployment ai-shell --replicas=5

# Update deployment
kubectl set image deployment/ai-shell ai-shell=aishell/ai-shell:v1.1.0
```

### Scenario 4: Multi-Region Deployment

**Best for:** Global applications, high availability

- Deploy in multiple AWS regions
- Use Route53 for DNS failover
- Configure cross-region database replication
- Implement global load balancing

---

## Troubleshooting

### Common Issues

#### 1. Connection Failures

```bash
# Test database connection
ai-shell connect postgresql://... --test

# Check network connectivity
telnet db-host 5432
nc -zv db-host 5432

# Verify DNS
nslookup db-host

# Check SSL certificates
openssl s_client -connect db-host:5432 -starttls postgres
```

#### 2. Performance Issues

```bash
# Monitor connections
ai-shell connections --health

# Check resource usage
htop
iostat -x 1

# Analyze slow queries
ai-shell slow-queries --threshold 1000

# View logs
tail -f /var/log/ai-shell/app.log
```

#### 3. Memory Leaks

```bash
# Increase Node.js heap
export NODE_OPTIONS="--max-old-space-size=8192"

# Monitor memory
node --inspect dist/cli/index.js

# Generate heap snapshot
kill -USR2 <pid>
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=debug
export AI_SHELL_VERBOSE=true

# Run with debugging
node --inspect-brk dist/cli/index.js
```

### Health Checks

```bash
# Application health
curl http://localhost:3000/health

# Database health
ai-shell health-check --database

# System health
ai-shell health-check --all --verbose
```

---

## Next Steps

After deployment:

1. Review [MONITORING_SETUP.md](./MONITORING_SETUP.md)
2. Follow [SECURITY_HARDENING.md](./SECURITY_HARDENING.md)
3. Configure [PRODUCTION_CONFIGURATION.md](./PRODUCTION_CONFIGURATION.md)
4. Review [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)

---

**Document Version:** 1.0.0
**Last Updated:** October 29, 2025
**Maintained By:** AIShell DevOps Team
