# Production Deployment Checklist

## Pre-Deployment Requirements

### System Requirements

#### Minimum Requirements
- **Operating System**: Linux (Ubuntu 20.04+, RHEL 8+, Debian 11+)
- **Node.js**: v18.0.0 or higher (LTS recommended)
- **Memory**: 4GB RAM minimum
- **CPU**: 2 cores minimum
- **Disk Space**: 20GB available
- **Network**: 100 Mbps connection

#### Recommended Production Requirements
- **Operating System**: Linux (Ubuntu 22.04 LTS or RHEL 9)
- **Node.js**: v20.x LTS
- **Memory**: 16GB RAM
- **CPU**: 8 cores
- **Disk Space**: 100GB SSD
- **Network**: 1 Gbps connection
- **Database**: Dedicated database server

### Database Prerequisites

#### PostgreSQL (Production Ready - 100% Tests Passing)
- PostgreSQL 14+ installed and configured
- Connection pooling enabled (recommend: pgbouncer)
- Max connections: 200+ recommended
- Shared buffers: 25% of system RAM
- Effective cache size: 75% of system RAM
- Work memory: 64MB per connection
- Maintenance work memory: 2GB

#### MySQL (Partial Support - Testing Ongoing)
- MySQL 8.0+ or MariaDB 10.6+
- InnoDB buffer pool: 70-80% of RAM
- Max connections: 150+
- Query cache enabled (if MySQL < 8.0)

#### MongoDB (Client Ready - CLI Integration Needed)
- MongoDB 5.0+ or 6.0+
- WiredTiger storage engine
- Replication set configured
- Connection pool: 100+

#### Redis (Client Ready - CLI Integration Needed)
- Redis 6.0+ or 7.0+
- Max memory policy: allkeys-lru
- Persistence: AOF enabled for production
- Connection pool: 50+

### Environment Variables Checklist

```bash
# Required
export ANTHROPIC_API_KEY="your-api-key-here"
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Optional but Recommended
export AI_SHELL_LOG_LEVEL="info"
export AI_SHELL_TIMEOUT="30000"
export AI_SHELL_MAX_CONNECTIONS="100"
export NODE_ENV="production"
export LOG_ROTATION="daily"
export LOG_MAX_FILES="30"

# Redis Cache (if using query cache)
export REDIS_URL="redis://localhost:6379"
export REDIS_MAX_CONNECTIONS="50"

# Email Notifications (if configured)
export SMTP_HOST="smtp.example.com"
export SMTP_PORT="587"
export SMTP_USER="notifications@example.com"
export SMTP_PASS="secure-password"

# Slack Notifications (if configured)
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Cloud Backup (if configured)
export AWS_ACCESS_KEY_ID="your-aws-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret"
export AWS_REGION="us-east-1"
export BACKUP_BUCKET="ai-shell-backups"
```

### Dependency Installation

```bash
# Production dependencies
npm ci --production

# Verify installation
npm list --depth=0

# Check for vulnerabilities
npm audit --production

# Update critical dependencies
npm audit fix --only=prod
```

## Configuration Validation

### Configuration File Checklist

#### 1. Database Configuration
```yaml
# ~/.ai-shell/config.yaml
databases:
  production:
    type: postgres
    host: db.production.internal
    port: 5432
    database: production_db
    username: ai_shell_user
    # Use vault for password - DO NOT hardcode
    pool:
      min: 10
      max: 100
      acquireTimeoutMillis: 30000
      idleTimeoutMillis: 30000
      createTimeoutMillis: 3000
      destroyTimeoutMillis: 5000
      reapIntervalMillis: 1000
      createRetryIntervalMillis: 100
```

#### 2. LLM Configuration
```yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
  temperature: 0.1
  maxTokens: 4096
  timeout: 30000
  retries: 3
  backoff: exponential
```

#### 3. Security Configuration
```yaml
security:
  vault:
    encryption: aes-256
    keyDerivation: pbkdf2
    iterations: 100000
  audit:
    enabled: true
    destination: /var/log/ai-shell/audit.log
    rotation: daily
    maxFiles: 90
  sql_injection_prevention: true
  rate_limiting:
    enabled: true
    max_requests_per_minute: 100
    max_requests_per_hour: 1000
```

#### 4. Performance Configuration
```yaml
performance:
  queryTimeout: 30000
  maxConnections: 100
  connectionTimeout: 5000
  idleTimeout: 60000
  caching:
    enabled: true
    ttl: 3600
    maxSize: 1000
  monitoring:
    enabled: true
    interval: 60000
    metricsRetention: 2592000  # 30 days
```

### Validation Commands

```bash
# Validate configuration syntax
ai-shell config validate

# Test database connections
ai-shell connect postgresql://... --test

# Verify environment variables
env | grep AI_SHELL
env | grep DATABASE_URL
env | grep ANTHROPIC_API_KEY

# Check file permissions
ls -la ~/.ai-shell/
ls -la /var/log/ai-shell/

# Verify Node.js version
node --version  # Should be >= v18.0.0

# Check npm version
npm --version

# Verify build
npm run build
ls -la dist/

# Run configuration health check
ai-shell health-check --config
```

## Security Hardening Pre-Deployment

### 1. Credential Management
- [ ] All API keys stored in vault
- [ ] Database passwords encrypted
- [ ] No hardcoded credentials in config files
- [ ] Environment variables secured
- [ ] Secrets rotation policy defined
- [ ] Vault encryption key backed up securely

### 2. Access Control
- [ ] RBAC configured for all users
- [ ] Principle of least privilege applied
- [ ] Service accounts created with minimal permissions
- [ ] Database user permissions reviewed
- [ ] Network access restricted to necessary IPs
- [ ] Firewall rules configured

### 3. Audit Logging
- [ ] Audit logging enabled
- [ ] Log rotation configured
- [ ] Log retention policy defined (90 days recommended)
- [ ] Sensitive data redaction enabled
- [ ] Log shipping to SIEM configured (if applicable)
- [ ] Log integrity verification enabled

### 4. SQL Injection Prevention
- [ ] SQL injection prevention enabled (default: true)
- [ ] Input validation configured
- [ ] Parameterized queries enforced
- [ ] Query risk assessment enabled
- [ ] Dangerous operations logged and monitored

### 5. Network Security
- [ ] TLS/SSL enabled for all database connections
- [ ] Certificate validation enabled
- [ ] Minimum TLS version: 1.2
- [ ] Strong cipher suites configured
- [ ] VPN or private network for database access
- [ ] API endpoints secured with authentication

## Performance Tuning

### Database Connection Pooling

#### PostgreSQL Tuning
```yaml
# Production settings
databases:
  production:
    pool:
      min: 10              # Minimum idle connections
      max: 100             # Maximum pool size
      acquireTimeout: 30000
      idleTimeout: 30000
      createTimeout: 3000
      reapInterval: 1000
```

#### Recommended Connection Pool Sizes
- **Low traffic** (< 100 req/min): min=5, max=20
- **Medium traffic** (100-1000 req/min): min=10, max=50
- **High traffic** (> 1000 req/min): min=20, max=100

### Query Timeout Configuration

```yaml
# Tiered timeout strategy
performance:
  queryTimeout:
    default: 30000       # 30 seconds
    read: 15000          # 15 seconds for SELECT
    write: 45000         # 45 seconds for INSERT/UPDATE/DELETE
    analytical: 300000   # 5 minutes for complex analytics
```

### Caching Strategy

```yaml
caching:
  enabled: true
  provider: redis
  ttl: 3600              # 1 hour default
  maxSize: 1000          # Maximum cached queries
  strategies:
    frequent:
      ttl: 7200          # 2 hours for frequently accessed
    static:
      ttl: 86400         # 24 hours for static data
    analytical:
      ttl: 600           # 10 minutes for analytics
```

### Memory Configuration

```bash
# Node.js memory settings
export NODE_OPTIONS="--max-old-space-size=4096"  # 4GB heap

# For high-memory production servers
export NODE_OPTIONS="--max-old-space-size=8192"  # 8GB heap
```

## Monitoring Setup Pre-Flight

### Health Check Endpoints

```bash
# Configure health check
ai-shell health-check --configure

# Endpoints to verify
# - /health (HTTP 200 if healthy)
# - /health/database (database connectivity)
# - /health/llm (Anthropic API connectivity)
# - /health/memory (system memory usage)
# - /health/disk (disk space)
```

### Metrics Collection

```yaml
monitoring:
  enabled: true
  interval: 60000        # Collect metrics every 60 seconds
  metrics:
    - database_connections
    - query_execution_time
    - cache_hit_ratio
    - memory_usage
    - cpu_usage
    - disk_usage
    - error_rate
    - request_rate
  exporters:
    - prometheus
    - grafana
```

### Alert Thresholds

```yaml
alerts:
  database_connections:
    warning: 70          # 70% of max connections
    critical: 90         # 90% of max connections
  query_latency:
    warning: 1000        # 1 second
    critical: 5000       # 5 seconds
  error_rate:
    warning: 1           # 1% error rate
    critical: 5          # 5% error rate
  memory_usage:
    warning: 80          # 80% memory used
    critical: 95         # 95% memory used
  disk_usage:
    warning: 80          # 80% disk used
    critical: 90         # 90% disk used
```

## Backup Procedures

### Pre-Production Backup Setup

```bash
# Configure backup system
ai-shell backup configure \
  --schedule "0 2 * * *" \
  --retention 30 \
  --compression gzip \
  --encryption aes-256

# Test backup creation
ai-shell backup create --dry-run
ai-shell backup create --test

# Verify backup integrity
ai-shell backup verify --latest

# Test restoration process
ai-shell restore --backup-id test-123 --dry-run
```

### Backup Schedule

```yaml
backup:
  schedule:
    full:
      cron: "0 2 * * 0"      # Weekly full backup (Sunday 2 AM)
      retention: 4            # Keep 4 weekly backups
    incremental:
      cron: "0 2 * * 1-6"    # Daily incremental (Mon-Sat 2 AM)
      retention: 7            # Keep 7 daily backups
  cloud:
    enabled: true
    provider: aws-s3
    bucket: ai-shell-backups
    region: us-east-1
    encryption: true
```

## Rollback Plan

### Rollback Checklist

#### 1. Version Control
- [ ] Current production version documented
- [ ] Previous stable version tagged
- [ ] Rollback procedure documented
- [ ] Rollback tested in staging

#### 2. Data Rollback
- [ ] Database backup verified
- [ ] Data migration scripts reversible
- [ ] Rollback scripts tested
- [ ] Data integrity checks prepared

#### 3. Configuration Rollback
- [ ] Previous configuration backed up
- [ ] Configuration rollback procedure documented
- [ ] Environment variables documented
- [ ] Service dependencies documented

#### 4. Monitoring During Rollback
- [ ] Alert system configured
- [ ] Rollback monitoring dashboard ready
- [ ] Team communication plan established
- [ ] Escalation procedures defined

### Rollback Procedures

```bash
# 1. Stop current service
sudo systemctl stop ai-shell

# 2. Rollback code version
git checkout v1.0.0-stable
npm ci --production
npm run build

# 3. Rollback configuration
cp ~/.ai-shell/config.yaml.backup ~/.ai-shell/config.yaml

# 4. Rollback database (if needed)
ai-shell restore --backup-id pre-deployment-20251029

# 5. Restart service
sudo systemctl start ai-shell

# 6. Verify health
ai-shell health-check
```

## Pre-Deployment Testing

### Smoke Tests

```bash
# 1. Connection tests
ai-shell connect postgresql://... --test
ai-shell connect mysql://... --test
ai-shell connect mongodb://... --test

# 2. Query execution test
ai-shell query "SELECT 1" --test

# 3. Health check
ai-shell health-check --all

# 4. Configuration validation
ai-shell config validate

# 5. Security scan
ai-shell security-scan --production

# 6. Performance test
ai-shell benchmark --queries 100 --concurrency 10

# 7. Backup test
ai-shell backup create --test
ai-shell restore --latest --dry-run
```

### Integration Tests

```bash
# Run full integration test suite
npm run test:integration

# Run production smoke tests
npm run test:smoke

# Run security tests
npm run test:security

# Run performance tests
npm run test:performance
```

## Go-Live Checklist

### Final Verification (T-0)

- [ ] All smoke tests passing
- [ ] Database connections verified
- [ ] Backup system tested
- [ ] Monitoring dashboards deployed
- [ ] Alert system configured and tested
- [ ] Security scan passed
- [ ] Performance benchmarks acceptable
- [ ] Rollback procedure documented and tested
- [ ] Team trained on new system
- [ ] Documentation updated
- [ ] Support contacts documented
- [ ] Incident response plan ready

### Deployment Window

- [ ] Maintenance window scheduled
- [ ] Stakeholders notified
- [ ] Status page updated
- [ ] Deployment runbook prepared
- [ ] Team assembled (minimum 2 people)
- [ ] Communication channels open

### Post-Deployment Monitoring (T+0 to T+24h)

- [ ] Monitor error rates (first 1 hour)
- [ ] Monitor performance metrics (first 4 hours)
- [ ] Monitor database connections (continuous)
- [ ] Review logs for anomalies (first 8 hours)
- [ ] Verify backup execution (next scheduled backup)
- [ ] Collect user feedback (first 24 hours)
- [ ] Review monitoring dashboards (continuous)

## Production Readiness Scorecard

### Component Readiness Matrix

| Component | Status | Test Coverage | Documentation | Production Ready |
|-----------|--------|---------------|---------------|------------------|
| PostgreSQL Integration | ✅ | 100% (57/57) | ✅ Complete | ✅ Yes |
| Query Optimizer | ✅ | 100% (32/32) | ✅ Complete | ✅ Yes |
| Health Monitor | ✅ | 77.2% | ✅ Good | ⚠️ Staging |
| Backup System | 🚧 | 18.9% failing | ⚠️ Partial | ❌ No |
| MySQL Integration | 🚧 | Partial | ⚠️ Basic | ❌ No |
| MongoDB Integration | 🚧 | Client only | ⚠️ Basic | ❌ No |
| Redis Integration | 🚧 | Client only | ⚠️ Basic | ❌ No |
| MCP Clients | ✅ | 89.8% (53/59) | ✅ Good | ⚠️ Staging |
| Security (Core) | ✅ | 8.5/10 | ✅ Complete | ✅ Yes |
| CLI Commands | 🚧 | Phase 2 ongoing | ✅ Good | ⚠️ Partial |

### Overall Production Readiness: 58%

**Ready for Production:**
- PostgreSQL database operations
- Query optimization and analysis
- Core security features
- Health monitoring (basic)
- Cognitive memory system
- Anomaly detection

**Requires More Work:**
- Multi-database CLI commands
- Backup/restore CLI interface
- Migration CLI
- Performance dashboards
- Full test coverage (target: 85%+)

## Support & Escalation

### Support Contacts

**Primary Support:**
- Email: support@ai-shell.dev
- Slack: #ai-shell-support
- On-call: +1-555-SHELL-01

**Escalation Path:**
1. Level 1: DevOps Team (response: 15 min)
2. Level 2: Engineering Lead (response: 30 min)
3. Level 3: CTO (response: 1 hour)

### Emergency Procedures

**Critical Issues (P0):**
- Database connection failure
- Data corruption
- Security breach
- System outage

**Response:**
1. Alert on-call engineer immediately
2. Initiate rollback if necessary
3. Engage vendor support (Anthropic, database vendor)
4. Document incident in log
5. Post-mortem within 24 hours

## Post-Deployment

### Day 1 Tasks
- Monitor all metrics continuously
- Review logs every 2 hours
- Collect user feedback
- Document any issues
- Update runbook with lessons learned

### Week 1 Tasks
- Review performance trends
- Optimize based on real usage
- Update documentation
- Conduct retrospective
- Plan optimization sprint

### Month 1 Tasks
- Comprehensive performance review
- Security audit
- Backup verification
- Disaster recovery drill
- Capacity planning review

---

**Document Version:** 1.0.0
**Last Updated:** October 29, 2025
**Maintained By:** AIShell DevOps Team
**Review Cycle:** Quarterly
