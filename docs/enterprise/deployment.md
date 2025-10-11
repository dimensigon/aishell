# Enterprise Deployment Guide

## Overview

This guide covers deploying AI-Shell Enterprise Edition in production environments with high availability, security, and scalability.

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 12+ or MySQL 8+ (for production databases)
- Redis 6+ (for caching and session management)
- Load balancer (nginx, HAProxy, or cloud LB)
- Cloud provider account (AWS, Azure, or GCP) - optional

## Installation

### 1. Install AI-Shell

```bash
# Clone repository
git clone https://github.com/yourusername/AIShell.git
cd AIShell

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with enterprise features
pip install -e ".[dev,docs]"
```

### 2. Install Enterprise Dependencies

```bash
# Install cloud SDKs (optional, based on your provider)
pip install boto3              # AWS
pip install azure-sdk-python   # Azure
pip install google-cloud       # GCP
```

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aishell_production
DB_USER=aishell_user
DB_PASSWORD=secure_password_here

# Enterprise Features
MULTI_TENANCY_ENABLED=true
RBAC_ENABLED=true
AUDIT_ENABLED=true

# Tenant Database Strategy
TENANT_ISOLATION_STRATEGY=schema_per_tenant  # or database_per_tenant

# Cloud Integration
CLOUD_PROVIDER=aws  # or azure, gcp
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Security
SECRET_KEY=generate_a_secure_random_key_here
MASTER_PASSWORD=secure_vault_password

# Logging
LOG_LEVEL=INFO
AUDIT_LOG_RETENTION_DAYS=365

# Performance
MAX_CONNECTIONS_PER_TENANT=10
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```

### Configuration File

Create `config/enterprise.yaml`:

```yaml
enterprise:
  multi_tenancy:
    enabled: true
    isolation_strategy: schema_per_tenant
    default_tier: free
    trial_days: 30

  rbac:
    enabled: true
    enforce_permissions: true
    default_role: viewer

  audit:
    enabled: true
    log_all_requests: true
    retention_days: 365
    compliance_frameworks:
      - soc2
      - hipaa
      - gdpr

  quotas:
    free_tier:
      queries_per_hour: 100
      storage_mb: 100
      max_users: 5
    professional_tier:
      queries_per_hour: 1000
      storage_mb: 1000
      max_users: 50
    enterprise_tier:
      queries_per_hour: 10000
      storage_mb: 10000
      max_users: unlimited

  cloud:
    backup:
      enabled: true
      schedule: "0 2 * * *"  # 2 AM daily
      retention_days: 30
      compression: true
      encryption: true
```

## Database Setup

### PostgreSQL Setup

```sql
-- Create database
CREATE DATABASE aishell_production;

-- Create user
CREATE USER aishell_user WITH ENCRYPTED PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE aishell_production TO aishell_user;

-- Enable extensions
\c aishell_production
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### Initialize Schema

```bash
# Run migrations
python -m src.enterprise.scripts.init_database

# Create default roles
python -m src.enterprise.scripts.init_roles

# Create first tenant (optional)
python -m src.enterprise.scripts.create_tenant \
    --name "Example Corp" \
    --slug "example" \
    --tier enterprise
```

## Deployment Options

### Option 1: Single Server Deployment

Suitable for small to medium deployments.

```
┌─────────────────────────────────────┐
│         Single Server               │
│  ┌────────────────────────────┐    │
│  │     nginx (reverse proxy)  │    │
│  └────────────┬───────────────┘    │
│               │                     │
│  ┌────────────▼───────────────┐    │
│  │   AI-Shell Application     │    │
│  │   (Gunicorn + workers)     │    │
│  └────────────┬───────────────┘    │
│               │                     │
│  ┌────────────▼───────────────┐    │
│  │    PostgreSQL Database     │    │
│  └────────────────────────────┘    │
└─────────────────────────────────────┘
```

Setup:

```bash
# Install nginx
sudo apt install nginx

# Configure nginx
sudo nano /etc/nginx/sites-available/aishell

# nginx configuration
server {
    listen 80;
    server_name aishell.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Tenant-ID $http_x_tenant_id;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/aishell /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Run application with Gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 src.main:app
```

### Option 2: Multi-Server Deployment

Suitable for high-traffic production environments.

```
┌─────────────────────────────────────────────────────────┐
│                   Load Balancer                         │
│              (nginx / HAProxy / ALB)                    │
└────────────────┬─────────────┬──────────────────────────┘
                 │             │
      ┌──────────▼──────┐  ┌──▼──────────────┐
      │   App Server 1  │  │  App Server 2   │
      │                 │  │                 │
      └──────────┬──────┘  └──┬──────────────┘
                 │             │
                 └──────┬──────┘
                        │
      ┌─────────────────▼──────────────────┐
      │        PostgreSQL Cluster          │
      │   (Primary + Read Replicas)        │
      └────────────────────────────────────┘
```

### Option 3: Cloud Deployment (AWS Example)

```
┌─────────────────────────────────────────────────────────┐
│                 Application Load Balancer                │
└────────────────┬─────────────┬──────────────────────────┘
                 │             │
      ┌──────────▼──────┐  ┌──▼──────────────┐
      │   ECS/Fargate   │  │  ECS/Fargate    │
      │   Container 1   │  │  Container 2    │
      └──────────┬──────┘  └──┬──────────────┘
                 │             │
                 └──────┬──────┘
                        │
      ┌─────────────────▼──────────────────┐
      │            Amazon RDS              │
      │     (Multi-AZ PostgreSQL)          │
      └────────────────────────────────────┘
                        │
      ┌─────────────────▼──────────────────┐
      │        S3 (Backups & Logs)         │
      └────────────────────────────────────┘
```

#### AWS CloudFormation Template

```yaml
# cloudformation/aishell-enterprise.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'AI-Shell Enterprise on AWS'

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues:
      - production
      - staging
      - development

Resources:
  # VPC
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Sub aishell-${Environment}-vpc

  # RDS Database
  Database:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: !Sub aishell-${Environment}-db
      Engine: postgres
      EngineVersion: '14.5'
      DBInstanceClass: db.t3.medium
      AllocatedStorage: 100
      StorageEncrypted: true
      MultiAZ: true
      MasterUsername: aishell
      MasterUserPassword: !Ref DBPassword

  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub aishell-${Environment}

  # Application Load Balancer
  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub aishell-${Environment}-alb
      Type: application
      Scheme: internet-facing
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2

  # S3 Backup Bucket
  BackupBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub aishell-${Environment}-backups
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldBackups
            Status: Enabled
            ExpirationInDays: 30
```

Deploy with:

```bash
aws cloudformation create-stack \
    --stack-name aishell-enterprise \
    --template-body file://cloudformation/aishell-enterprise.yaml \
    --parameters ParameterKey=Environment,ParameterValue=production
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install application
RUN pip install -e .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "src.main:app"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=aishell
      - DB_USER=aishell
      - DB_PASSWORD=secure_password
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: aishell
      POSTGRES_USER: aishell
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

Run with:

```bash
docker-compose up -d
```

## Monitoring & Health Checks

### Health Check Endpoint

The application exposes a health check at `/health`:

```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": check_database(),
        "cache": check_redis(),
        "timestamp": datetime.now().isoformat()
    }
```

### Prometheus Metrics

Enable metrics export:

```python
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('aishell_requests_total', 'Total requests')
request_duration = Histogram('aishell_request_duration_seconds', 'Request duration')

@app.get("/metrics")
def metrics():
    return generate_latest()
```

## Backup & Recovery

### Automated Backups

```bash
# Configure automated backups
python -m src.enterprise.scripts.configure_backups \
    --provider aws \
    --schedule "0 2 * * *" \
    --retention-days 30

# Manual backup
python -m src.enterprise.scripts.backup \
    --tenant-id tenant_1 \
    --output-path /backups/tenant_1.db
```

### Restore

```bash
# Restore from backup
python -m src.enterprise.scripts.restore \
    --backup-id backup_123 \
    --tenant-id tenant_1
```

## Scaling

### Horizontal Scaling

Add more application servers behind the load balancer:

```bash
# Scale ECS service
aws ecs update-service \
    --cluster aishell-production \
    --service aishell-app \
    --desired-count 4
```

### Database Scaling

- Enable read replicas for read-heavy workloads
- Use connection pooling (PgBouncer)
- Implement caching layer (Redis)

## Security Hardening

See [security.md](security.md) for detailed security configuration.

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check firewall rules
   - Verify credentials
   - Check database server status

2. **High memory usage**
   - Adjust worker count
   - Enable query result caching
   - Review slow queries

3. **Tenant isolation issues**
   - Verify tenant middleware configuration
   - Check database connection routing
   - Review audit logs

### Logs

```bash
# Application logs
tail -f /var/log/aishell/application.log

# Audit logs
tail -f /var/log/aishell/audit.log

# Query logs in database
SELECT * FROM audit_log
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

## Maintenance

### Regular Tasks

- Review and rotate logs
- Update dependencies
- Review security patches
- Backup verification
- Performance optimization

### Updates

```bash
# Pull latest code
git pull origin main

# Install updates
pip install -e ".[dev,docs]" --upgrade

# Run migrations
python -m src.enterprise.scripts.migrate

# Restart services
sudo systemctl restart aishell
```

## Support

For enterprise support:
- Email: enterprise@aishell.example.com
- Slack: #aishell-enterprise
- Documentation: https://docs.aishell.io/enterprise
