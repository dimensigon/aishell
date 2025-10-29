# AI-Shell CLI - Complete User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation and Setup](#installation-and-setup)
3. [Basic Concepts](#basic-concepts)
4. [Command Categories](#command-categories)
5. [Getting Started](#getting-started)
6. [Common Workflows](#common-workflows)
7. [Configuration](#configuration)
8. [Best Practices](#best-practices)
9. [Troubleshooting Quick Reference](#troubleshooting-quick-reference)

---

## Introduction

### What is AI-Shell CLI?

AI-Shell is a comprehensive command-line interface for managing databases, monitoring systems, and automating database operations. It provides a unified interface for working with multiple database types including PostgreSQL, MySQL, MongoDB, and Redis.

### Key Features

- **Multi-Database Support**: Connect and manage PostgreSQL, MySQL, MongoDB, and Redis
- **Intelligent Query Optimization**: AI-powered query analysis and optimization suggestions
- **Automated Backups**: Schedule and manage backups across multiple databases
- **Real-Time Monitoring**: Health checks, performance metrics, and alerting
- **Security First**: Vault-based credential management and audit logging
- **Natural Language**: Convert natural language to SQL queries
- **Cloud Integration**: AWS, Azure, and GCP backup storage
- **Federation**: Manage distributed database clusters
- **ADA (Autonomous Database Agent)**: AI-powered database management

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     AI-Shell CLI Interface                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Connection│  │  Query   │  │  Backup  │  │ Monitor  │  │
│  │ Manager  │  │Optimizer │  │  System  │  │  System  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Vault   │  │Analytics │  │  Alert   │  │   ADA    │  │
│  │  System  │  │  Engine  │  │  System  │  │   AI     │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│              Database Connector Layer                       │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL  │    MySQL    │   MongoDB   │     Redis       │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation and Setup

### Prerequisites

- **Node.js**: Version 18.0.0 or higher
- **npm**: Version 8.0.0 or higher
- **Operating System**: Linux, macOS, or Windows (with WSL2)
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Disk Space**: 500MB for installation

### Installation Methods

#### Method 1: NPM Global Install (Recommended)

```bash
# Install globally
npm install -g @aishell/cli

# Verify installation
aishell --version

# Check available commands
aishell --help
```

#### Method 2: NPX (No Installation)

```bash
# Run directly without installing
npx @aishell/cli --help

# Create alias for convenience
alias aishell="npx @aishell/cli"
```

#### Method 3: From Source

```bash
# Clone repository
git clone https://github.com/your-org/aishell.git
cd aishell

# Install dependencies
npm install

# Build project
npm run build

# Link globally
npm link

# Verify
aishell --version
```

### Initial Setup

#### 1. Configuration Initialization

```bash
# Initialize AI-Shell configuration
aishell init

# This creates:
# ~/.aishell/config.json       - Main configuration
# ~/.aishell/vault/            - Credential storage
# ~/.aishell/logs/             - Log files
# ~/.aishell/backups/          - Local backup storage
```

#### 2. Configure Database Connections

```bash
# Add a PostgreSQL connection
aishell connection add \
  --name prod-db \
  --type postgresql \
  --host db.example.com \
  --port 5432 \
  --database myapp \
  --username dbuser

# Add a MySQL connection
aishell connection add \
  --name mysql-prod \
  --type mysql \
  --host mysql.example.com \
  --port 3306 \
  --database orders

# Add a MongoDB connection
aishell connection add \
  --name mongo-cluster \
  --type mongodb \
  --host mongodb://mongo1.example.com:27017 \
  --database analytics

# Add a Redis connection
aishell connection add \
  --name redis-cache \
  --type redis \
  --host redis.example.com \
  --port 6379
```

#### 3. Verify Connections

```bash
# List all connections
aishell connection list

# Test a specific connection
aishell connection test prod-db

# Show connection details
aishell connection show prod-db
```

#### 4. Configure Vault (Secure Credential Storage)

```bash
# Initialize vault with master password
aishell vault init

# Store database credentials
aishell vault store \
  --key prod-db-password \
  --value "your-secure-password"

# Verify vault is working
aishell vault list
```

---

## Basic Concepts

### Connections

Connections represent database endpoints you want to manage. Each connection includes:

- **Name**: Unique identifier (e.g., "prod-db", "staging-mysql")
- **Type**: Database type (postgresql, mysql, mongodb, redis)
- **Host**: Database server hostname or IP
- **Port**: Connection port
- **Database**: Database name (not required for Redis)
- **Credentials**: Stored securely in vault

```
Connection Lifecycle:
┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐
│ Add  │──>│ Test │──>│ Use  │──>│Update│──>│Remove│
└──────┘   └──────┘   └──────┘   └──────┘   └──────┘
```

### Queries

Queries are SQL or NoSQL commands executed against databases:

- **Direct Execution**: Run SQL/NoSQL queries immediately
- **Query Analysis**: Analyze query performance before execution
- **Optimization**: Get AI-powered optimization suggestions
- **Natural Language**: Convert English to SQL
- **Query History**: Track all executed queries

### Backups

Backups are point-in-time snapshots of your databases:

- **Manual Backups**: On-demand backup creation
- **Scheduled Backups**: Automated backup schedules
- **Incremental**: Only backup changed data
- **Encrypted**: Optional encryption for security
- **Cloud Storage**: Upload to AWS S3, Azure Blob, or GCP Storage
- **Retention Policies**: Automatic cleanup of old backups

```
Backup Strategy:
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Daily Full Backup (7 days retention)              │
│  ├── Day 1: Full backup (10GB)                     │
│  ├── Day 2: Full backup (10.2GB)                   │
│  └── Day 7: Full backup (11GB)                     │
│                                                     │
│  Hourly Incremental (24 hours retention)           │
│  ├── 09:00: +500MB                                 │
│  ├── 10:00: +300MB                                 │
│  └── 17:00: +1GB                                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Monitoring

Real-time tracking of database health and performance:

- **Health Checks**: Database availability and connectivity
- **Metrics**: CPU, memory, connections, query performance
- **Alerts**: Automated notifications for issues
- **Dashboards**: Visual representation of metrics
- **Historical Data**: Track trends over time

---

## Command Categories

AI-Shell CLI commands are organized into logical categories:

### 1. Connection Management

```bash
aishell connection <subcommand>
├── add          # Add new database connection
├── list         # List all connections
├── show         # Show connection details
├── test         # Test connection
├── update       # Update connection settings
├── remove       # Remove connection
└── export       # Export connection config
```

### 2. Query Operations

```bash
aishell query <subcommand>
├── run          # Execute SQL/NoSQL query
├── analyze      # Analyze query performance
├── optimize     # Get optimization suggestions
├── explain      # Show query execution plan
├── history      # View query history
├── nl2sql       # Convert natural language to SQL
└── validate     # Validate query syntax
```

### 3. Backup & Recovery

```bash
aishell backup <subcommand>
├── create       # Create backup
├── list         # List all backups
├── restore      # Restore from backup
├── schedule     # Schedule automated backups
├── verify       # Verify backup integrity
├── upload       # Upload to cloud storage
└── download     # Download from cloud
```

### 4. Monitoring & Health

```bash
aishell monitor <subcommand>
├── health       # Database health check
├── metrics      # Show performance metrics
├── dashboard    # Launch monitoring dashboard
├── alerts       # Manage alert rules
├── logs         # View database logs
└── realtime     # Real-time monitoring
```

### 5. Security & Vault

```bash
aishell vault <subcommand>
├── init         # Initialize vault
├── store        # Store credential
├── retrieve     # Retrieve credential
├── list         # List stored keys
├── rotate       # Rotate credentials
└── audit        # View audit logs
```

### 6. Optimization

```bash
aishell optimize <subcommand>
├── indexes      # Analyze and suggest indexes
├── slow-queries # Find slow queries
├── vacuum       # Database maintenance
├── analyze-tables # Update statistics
└── suggest      # Get AI recommendations
```

### 7. Integration

```bash
aishell integration <subcommand>
├── slack        # Configure Slack notifications
├── email        # Configure email alerts
├── grafana      # Setup Grafana integration
├── prometheus   # Setup Prometheus metrics
└── webhook      # Configure webhook notifications
```

### 8. Federation

```bash
aishell federation <subcommand>
├── init         # Initialize federation
├── add-node     # Add database node
├── status       # Show federation status
├── sync         # Synchronize schemas
└── query        # Query across federation
```

### 9. ADA (Autonomous Agent)

```bash
aishell ada <subcommand>
├── start        # Start ADA agent
├── status       # Show ADA status
├── configure    # Configure ADA behavior
├── logs         # View ADA activity logs
└── stop         # Stop ADA agent
```

---

## Getting Started

### Quick Start Tutorial (15 Minutes)

#### Step 1: Add Your First Connection (2 minutes)

```bash
# Add a PostgreSQL database
aishell connection add \
  --name my-first-db \
  --type postgresql \
  --host localhost \
  --port 5432 \
  --database testdb \
  --username postgres

# You'll be prompted for the password
# Password will be securely stored in vault
```

#### Step 2: Test the Connection (1 minute)

```bash
# Verify connection works
aishell connection test my-first-db

# Expected output:
# ✓ Connection successful
# ✓ Database: testdb
# ✓ PostgreSQL version: 14.5
# ✓ Ping: 12ms
```

#### Step 3: Run Your First Query (2 minutes)

```bash
# Simple SELECT query
aishell query run my-first-db \
  --sql "SELECT * FROM users LIMIT 10"

# Use natural language
aishell query nl2sql my-first-db \
  --prompt "Show me all active users from the last week"
```

#### Step 4: Analyze Query Performance (3 minutes)

```bash
# Analyze a query before running it
aishell query analyze my-first-db \
  --sql "SELECT * FROM orders WHERE user_id = 123"

# Get optimization suggestions
aishell optimize suggest my-first-db \
  --sql "SELECT * FROM orders WHERE user_id = 123"
```

#### Step 5: Create Your First Backup (3 minutes)

```bash
# Create a backup
aishell backup create my-first-db \
  --name initial-backup \
  --compress

# List backups
aishell backup list my-first-db

# Verify backup
aishell backup verify my-first-db \
  --name initial-backup
```

#### Step 6: Set Up Monitoring (4 minutes)

```bash
# Check database health
aishell monitor health my-first-db

# View real-time metrics
aishell monitor metrics my-first-db --realtime

# Set up an alert for high CPU
aishell monitor alerts create my-first-db \
  --metric cpu \
  --threshold 80 \
  --action email
```

---

## Common Workflows

### Workflow 1: Daily Database Maintenance

```bash
#!/bin/bash
# daily-maintenance.sh

# 1. Health check all databases
aishell monitor health --all

# 2. Find and analyze slow queries
aishell optimize slow-queries prod-db --threshold 1000ms

# 3. Update statistics
aishell optimize analyze-tables prod-db

# 4. Create backup
aishell backup create prod-db \
  --name "daily-$(date +%Y%m%d)" \
  --compress \
  --upload s3

# 5. Clean up old backups (keep 7 days)
aishell backup cleanup prod-db --keep-days 7

# 6. Generate daily report
aishell monitor report prod-db --period 24h > /var/log/db-report.txt
```

### Workflow 2: Query Optimization Process

```bash
# Step 1: Identify slow queries
aishell optimize slow-queries prod-db \
  --threshold 500ms \
  --limit 10

# Step 2: Analyze specific query
aishell query analyze prod-db \
  --sql "SELECT * FROM orders o JOIN users u ON o.user_id = u.id WHERE o.created_at > '2024-01-01'"

# Step 3: Get optimization suggestions
aishell optimize suggest prod-db \
  --sql "SELECT * FROM orders o JOIN users u ON o.user_id = u.id WHERE o.created_at > '2024-01-01'"

# Step 4: Check if indexes would help
aishell optimize indexes prod-db \
  --table orders \
  --analyze

# Step 5: Validate proposed changes
aishell query validate prod-db \
  --sql "CREATE INDEX idx_orders_created_at ON orders(created_at)"

# Step 6: Apply optimization
aishell query run prod-db \
  --sql "CREATE INDEX idx_orders_created_at ON orders(created_at)"

# Step 7: Re-analyze to verify improvement
aishell query analyze prod-db \
  --sql "SELECT * FROM orders o JOIN users u ON o.user_id = u.id WHERE o.created_at > '2024-01-01'"
```

### Workflow 3: Backup and Restore

```bash
# Scenario: Migrate database to new server

# On old server:
# 1. Create full backup
aishell backup create old-prod-db \
  --name migration-backup \
  --compress \
  --encrypt \
  --upload s3://backups/migration/

# 2. Verify backup integrity
aishell backup verify old-prod-db \
  --name migration-backup

# 3. Export connection config
aishell connection export old-prod-db > connection-config.json

# On new server:
# 4. Import connection config
aishell connection import new-prod-db < connection-config.json

# 5. Download backup from S3
aishell backup download new-prod-db \
  --source s3://backups/migration/migration-backup

# 6. Restore database
aishell backup restore new-prod-db \
  --name migration-backup \
  --verify

# 7. Test new database
aishell connection test new-prod-db

# 8. Compare databases
aishell federation compare \
  --source old-prod-db \
  --target new-prod-db
```

### Workflow 4: Multi-Database Monitoring

```bash
# Monitor multiple databases simultaneously

# 1. Set up federation
aishell federation init my-cluster

# 2. Add all databases to federation
aishell federation add-node my-cluster prod-db-1
aishell federation add-node my-cluster prod-db-2
aishell federation add-node my-cluster prod-db-3

# 3. Monitor entire cluster
aishell monitor dashboard my-cluster --realtime

# 4. Set up cluster-wide alerts
aishell monitor alerts create my-cluster \
  --metric cluster-health \
  --threshold warning \
  --action slack

# 5. Query across all databases
aishell federation query my-cluster \
  --sql "SELECT COUNT(*) FROM users"

# 6. Generate cluster report
aishell monitor report my-cluster \
  --period 7d \
  --format pdf
```

### Workflow 5: Security Audit

```bash
# Complete security audit workflow

# 1. Check vault security
aishell vault audit --full

# 2. Rotate all credentials
aishell vault rotate --all --dry-run

# 3. Review connection permissions
aishell connection audit prod-db

# 4. Check query audit logs
aishell query history prod-db \
  --filter "DROP TABLE|DELETE FROM|TRUNCATE" \
  --days 30

# 5. Verify encryption settings
aishell backup list prod-db \
  --show-encryption

# 6. Generate security report
aishell security report \
  --all-connections \
  --format pdf > security-audit.pdf
```

### Workflow 6: Disaster Recovery Test

```bash
# Test disaster recovery procedures

# 1. Create baseline backup
aishell backup create prod-db \
  --name dr-test-baseline \
  --upload s3

# 2. Set up test environment
aishell connection add \
  --name dr-test-db \
  --type postgresql \
  --host test-server.example.com

# 3. Restore to test environment
aishell backup restore dr-test-db \
  --source s3://backups/dr-test-baseline

# 4. Verify data integrity
aishell backup verify dr-test-db \
  --compare-with prod-db

# 5. Run validation queries
aishell query run dr-test-db \
  --sql "SELECT COUNT(*) FROM users" \
  --compare-with prod-db

# 6. Measure recovery time
aishell backup benchmark dr-test-db \
  --restore-test \
  --iterations 3

# 7. Document results
aishell backup report dr-test-db \
  --test-results > dr-test-report.md
```

---

## Configuration

### Configuration File Structure

Location: `~/.aishell/config.json`

```json
{
  "version": "2.0.0",
  "connections": {
    "default": "prod-db",
    "timeout": 30000,
    "retries": 3,
    "pool": {
      "min": 2,
      "max": 10
    }
  },
  "vault": {
    "enabled": true,
    "encryption": "AES-256-GCM",
    "keyRotation": "30d"
  },
  "backup": {
    "defaultFormat": "custom",
    "compression": true,
    "encryption": false,
    "retention": {
      "daily": 7,
      "weekly": 4,
      "monthly": 12
    },
    "cloud": {
      "provider": "s3",
      "bucket": "my-backups",
      "region": "us-east-1"
    }
  },
  "monitoring": {
    "enabled": true,
    "interval": 60,
    "metrics": ["cpu", "memory", "connections", "queries"],
    "alerts": {
      "channels": ["slack", "email"],
      "throttle": 300
    }
  },
  "optimization": {
    "autoAnalyze": true,
    "suggestIndexes": true,
    "slowQueryThreshold": 1000
  },
  "logging": {
    "level": "info",
    "file": "~/.aishell/logs/aishell.log",
    "rotation": "7d",
    "maxSize": "100MB"
  }
}
```

### Environment Variables

```bash
# Database connections
export AISHELL_DB_HOST="db.example.com"
export AISHELL_DB_PORT="5432"
export AISHELL_DB_NAME="myapp"
export AISHELL_DB_USER="dbuser"
export AISHELL_DB_PASSWORD="secret"  # Not recommended, use vault

# Vault configuration
export AISHELL_VAULT_MASTER_KEY="path/to/master.key"
export AISHELL_VAULT_AUTO_UNLOCK="true"

# Cloud credentials
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"

# Monitoring
export AISHELL_SLACK_WEBHOOK="https://hooks.slack.com/services/..."
export AISHELL_EMAIL_SMTP="smtp.gmail.com:587"
export AISHELL_EMAIL_FROM="alerts@example.com"

# Performance
export AISHELL_MAX_CONNECTIONS="20"
export AISHELL_QUERY_TIMEOUT="60000"
export AISHELL_ENABLE_CACHE="true"
```

### Advanced Configuration

#### Connection Profiles

Create profile-specific configurations:

```bash
# Development profile
cat > ~/.aishell/profiles/dev.json << EOF
{
  "connections": {
    "timeout": 10000,
    "pool": {"min": 1, "max": 3}
  },
  "logging": {
    "level": "debug"
  }
}
EOF

# Production profile
cat > ~/.aishell/profiles/prod.json << EOF
{
  "connections": {
    "timeout": 30000,
    "pool": {"min": 5, "max": 20}
  },
  "monitoring": {
    "interval": 30
  },
  "backup": {
    "autoBackup": true,
    "schedule": "0 2 * * *"
  }
}
EOF

# Use profile
aishell --profile prod connection list
```

---

## Best Practices

### Security Best Practices

1. **Always Use Vault for Credentials**
   ```bash
   # ✓ GOOD
   aishell vault store --key db-password
   aishell connection add --name prod-db --use-vault

   # ✗ BAD
   aishell connection add --password "plain-text-password"
   ```

2. **Enable Connection Encryption**
   ```bash
   aishell connection add prod-db \
     --ssl-mode require \
     --ssl-cert /path/to/cert.pem
   ```

3. **Rotate Credentials Regularly**
   ```bash
   # Monthly credential rotation
   aishell vault rotate --all --schedule monthly
   ```

4. **Enable Audit Logging**
   ```bash
   aishell config set logging.audit.enabled true
   aishell config set logging.audit.level verbose
   ```

### Performance Best Practices

1. **Use Connection Pooling**
   ```bash
   aishell config set connections.pool.min 5
   aishell config set connections.pool.max 20
   ```

2. **Enable Query Caching**
   ```bash
   aishell config set optimization.cache.enabled true
   aishell config set optimization.cache.ttl 300
   ```

3. **Optimize Slow Queries Regularly**
   ```bash
   # Weekly slow query review
   aishell optimize slow-queries --all --threshold 500ms
   ```

### Backup Best Practices

1. **Follow 3-2-1 Rule**
   - 3 copies of data
   - 2 different storage types
   - 1 off-site backup

   ```bash
   # Local backup
   aishell backup create prod-db --name daily

   # Cloud backup (AWS)
   aishell backup upload prod-db daily --target s3

   # Cloud backup (Azure)
   aishell backup upload prod-db daily --target azure
   ```

2. **Test Restores Regularly**
   ```bash
   # Monthly restore test
   aishell backup restore test-db --verify --dry-run
   ```

3. **Implement Retention Policies**
   ```bash
   aishell backup schedule prod-db \
     --daily 7 \
     --weekly 4 \
     --monthly 12
   ```

### Monitoring Best Practices

1. **Set Up Proactive Alerts**
   ```bash
   # CPU alert
   aishell monitor alerts create prod-db \
     --metric cpu --threshold 80 --action slack

   # Disk space alert
   aishell monitor alerts create prod-db \
     --metric disk --threshold 90 --action email

   # Connection pool alert
   aishell monitor alerts create prod-db \
     --metric connections --threshold 80% --action pagerduty
   ```

2. **Monitor Key Metrics**
   - CPU and Memory usage
   - Active connections
   - Query performance
   - Replication lag
   - Disk I/O

3. **Use Dashboards**
   ```bash
   # Start real-time dashboard
   aishell monitor dashboard prod-db --realtime --refresh 5s
   ```

---

## Troubleshooting Quick Reference

### Connection Issues

```bash
# Test connection
aishell connection test prod-db --verbose

# Check network connectivity
aishell connection ping prod-db

# Verify credentials
aishell vault retrieve prod-db-password

# Reset connection pool
aishell connection reset prod-db
```

### Query Issues

```bash
# Check query syntax
aishell query validate prod-db --sql "SELECT * FROM users"

# Analyze slow query
aishell query analyze prod-db --sql "..." --explain

# Check query history
aishell query history prod-db --limit 10
```

### Backup Issues

```bash
# Verify backup integrity
aishell backup verify prod-db --name backup-name

# Check backup logs
aishell backup logs prod-db --name backup-name

# Test restore
aishell backup restore test-db --dry-run
```

### Performance Issues

```bash
# Find bottlenecks
aishell optimize analyze prod-db

# Check slow queries
aishell optimize slow-queries prod-db

# Analyze indexes
aishell optimize indexes prod-db --suggest
```

For more detailed troubleshooting, see [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)

---

## Next Steps

- Read [Database Operations Guide](./DATABASE_OPERATIONS.md) for detailed database management
- Learn [Query Optimization](./QUERY_OPTIMIZATION.md) techniques
- Set up [Backup & Recovery](./BACKUP_RECOVERY.md) procedures
- Configure [Monitoring & Analytics](./MONITORING_ANALYTICS.md)
- Review [Security Best Practices](./SECURITY_BEST_PRACTICES.md)
- Explore [Integration Guide](./INTEGRATION_GUIDE.md) for third-party tools

---

## Support and Resources

- **Documentation**: https://docs.aishell.dev
- **GitHub**: https://github.com/your-org/aishell
- **Discord**: https://discord.gg/aishell
- **Stack Overflow**: Tag `aishell-cli`
- **Email Support**: support@aishell.dev

---

*Last Updated: 2024-01-15 | Version: 2.0.0*
