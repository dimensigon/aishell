# AI-Shell Command Cheatsheet

Quick reference for all AI-Shell CLI commands. Copy and paste these commands directly.

**Last Updated:** October 30, 2025 | **Version:** 1.0.0

---

## Table of Contents
- [Database Connections](#database-connections)
- [Natural Language Queries](#natural-language-queries)
- [Query Optimization](#query-optimization)
- [Security (Vault, RBAC, Audit)](#security)
- [Health Monitoring](#health-monitoring)
- [Backup & Restore](#backup--restore)
- [Schema Management](#schema-management)
- [Performance Profiling](#performance-profiling)
- [Federation](#federation)
- [Database-Specific Commands](#database-specific-commands)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)

---

## Database Connections

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell connect <uri>` | Connect to database | `ai-shell connect postgresql://user:pass@localhost/db` |
| `ai-shell connect --name <alias> <uri>` | Named connection | `ai-shell connect --name prod postgresql://...` |
| `ai-shell connections` | List all connections | `ai-shell connections` |
| `ai-shell connections switch <name>` | Switch active connection | `ai-shell connections switch prod` |
| `ai-shell disconnect` | Disconnect current | `ai-shell disconnect` |

**Supported Database URI Formats:**
```bash
# PostgreSQL
postgresql://user:password@host:5432/database

# MySQL
mysql://user:password@host:3306/database

# MongoDB
mongodb://user:password@host:27017/database

# Redis
redis://host:6379

# Oracle
oracle://user:password@host:1521/service

# SQLite
sqlite:///path/to/database.sqlite
```

**Using Vault Credentials:**
```bash
# Store password in vault first
ai-shell vault add prod-pass "myPassword" --encrypt

# Use in connection string
ai-shell connect postgresql://user:{{vault:prod-pass}}@host:5432/db
```

---

## Natural Language Queries

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell translate "<query>"` | Translate natural language to SQL | `ai-shell translate "show me all users"` |
| `ai-shell translate "<query>" --execute` | Translate and execute | `ai-shell translate "find recent orders" --execute` |
| `ai-shell translate "<query>" --explain` | Show translation explanation | `ai-shell translate "top customers" --explain` |
| `ai-shell translate "<query>" --dry-run` | Preview SQL without executing | `ai-shell translate "delete old records" --dry-run` |

**Example Queries:**
```bash
# Basic queries
ai-shell translate "show me all users"
ai-shell translate "count total orders"
ai-shell translate "describe the users table"

# Filtering and conditions
ai-shell translate "find customers who spent over $1000"
ai-shell translate "show orders from last 7 days"
ai-shell translate "find products with low inventory"

# Aggregations
ai-shell translate "top 10 customers by revenue"
ai-shell translate "average order value by month"
ai-shell translate "total sales by category"

# Joins
ai-shell translate "show users with their recent orders"
ai-shell translate "find products never ordered"
```

---

## Query Optimization

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell optimize "<sql>"` | Analyze and optimize query | `ai-shell optimize "SELECT * FROM users"` |
| `ai-shell explain "<sql>"` | Show query execution plan | `ai-shell explain "SELECT * FROM orders"` |
| `ai-shell analyze slow-queries` | Analyze all slow queries | `ai-shell analyze slow-queries --threshold 1000ms` |
| `ai-shell analyze slow-queries --since <time>` | Analyze recent slow queries | `ai-shell analyze slow-queries --since 24h` |
| `ai-shell index suggest <table>` | Suggest indexes for table | `ai-shell index suggest users` |
| `ai-shell index create <table> <column>` | Create index | `ai-shell index create users email` |

**Optimization Workflow:**
```bash
# 1. Find slow queries
ai-shell analyze slow-queries --threshold 1000ms

# 2. Optimize specific query
ai-shell optimize "SELECT * FROM users WHERE email LIKE '%@gmail.com'"

# 3. Check execution plan
ai-shell explain "SELECT * FROM users WHERE email = 'test@example.com'"

# 4. Apply suggested indexes
ai-shell index create users email
```

---

## Security

### Vault (Credential Management)

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell vault add <name> <value>` | Add credential | `ai-shell vault add db-pass "secret123"` |
| `ai-shell vault add <name> --encrypt` | Add with encryption | `ai-shell vault add api-key --encrypt` |
| `ai-shell vault list` | List all credentials | `ai-shell vault list` |
| `ai-shell vault list --show-passwords` | List with values | `ai-shell vault list --show-passwords` |
| `ai-shell vault get <name>` | Get specific credential | `ai-shell vault get db-pass` |
| `ai-shell vault delete <name>` | Delete credential | `ai-shell vault delete old-key` |
| `ai-shell vault search <pattern>` | Search credentials | `ai-shell vault search "prod-*"` |
| `ai-shell vault import <file>` | Bulk import | `ai-shell vault import creds.json` |
| `ai-shell vault export <file>` | Bulk export | `ai-shell vault export backup.json` |
| `ai-shell vault rotate` | Rotate encryption key | `ai-shell vault rotate` |

### RBAC (Role-Based Access Control)

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell role create <name>` | Create role | `ai-shell role create developer` |
| `ai-shell role create <name> --desc "<text>"` | Create with description | `ai-shell role create admin --desc "Full access"` |
| `ai-shell role list` | List all roles | `ai-shell role list` |
| `ai-shell role delete <name>` | Delete role | `ai-shell role delete old-role` |
| `ai-shell role assign <user> <role>` | Assign role to user | `ai-shell role assign john developer` |
| `ai-shell role unassign <user> <role>` | Unassign role | `ai-shell role unassign john developer` |
| `ai-shell role hierarchy <role>` | View role hierarchy | `ai-shell role hierarchy admin` |

### Permissions

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell permission grant <role> <resource>` | Grant permission | `ai-shell permission grant dev db:read` |
| `ai-shell permission grant <role> <resource> --actions <list>` | Grant specific actions | `ai-shell permission grant dev users --actions read,write` |
| `ai-shell permission revoke <role> <resource>` | Revoke permission | `ai-shell permission revoke dev db:delete` |
| `ai-shell permission list` | List all permissions | `ai-shell permission list` |
| `ai-shell permission list <user>` | List user permissions | `ai-shell permission list john` |
| `ai-shell permission check <user> <resource> <action>` | Check permission | `ai-shell permission check john db:write` |

### Audit Logging

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell audit show` | Show audit log | `ai-shell audit show` |
| `ai-shell audit show --limit <n>` | Show last N entries | `ai-shell audit show --limit 100` |
| `ai-shell audit show --user <name>` | Filter by user | `ai-shell audit show --user john` |
| `ai-shell audit show --action <type>` | Filter by action | `ai-shell audit show --action login` |
| `ai-shell audit export <file>` | Export logs | `ai-shell audit export audit-2025.json` |
| `ai-shell audit export <file> --format csv` | Export as CSV | `ai-shell audit export logs.csv --format csv` |
| `ai-shell audit stats` | Show statistics | `ai-shell audit stats` |
| `ai-shell audit search <query>` | Search logs | `ai-shell audit search "user:john"` |
| `ai-shell audit clear --before <date>` | Clear old logs | `ai-shell audit clear --before 2025-01-01` |
| `ai-shell audit verify` | Verify integrity | `ai-shell audit verify` |

### Security Operations

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell security status` | Security dashboard | `ai-shell security status` |
| `ai-shell security scan` | Security scan | `ai-shell security scan` |
| `ai-shell security scan --deep` | Deep security scan | `ai-shell security scan --deep` |
| `ai-shell security scan --output <file>` | Save scan report | `ai-shell security scan --output report.json` |
| `ai-shell security vulnerabilities` | List vulnerabilities | `ai-shell security vulnerabilities` |
| `ai-shell security compliance <std>` | Check compliance | `ai-shell security compliance gdpr` |
| `ai-shell security detect-pii "<text>"` | Detect PII | `ai-shell security detect-pii "SSN: 123-45-6789"` |
| `ai-shell encrypt "<data>"` | Encrypt value | `ai-shell encrypt "sensitive data"` |
| `ai-shell decrypt "<encrypted>"` | Decrypt value | `ai-shell decrypt "encrypted..."` |

**Compliance Standards:**
- `gdpr` - General Data Protection Regulation
- `sox` - Sarbanes-Oxley Act
- `hipaa` - Health Insurance Portability and Accountability Act
- `all` - Check all standards

---

## Health Monitoring

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell health-check` | Basic health check | `ai-shell health-check` |
| `ai-shell health-check --deep` | Deep health check | `ai-shell health-check --deep` |
| `ai-shell monitor` | Real-time monitoring | `ai-shell monitor` |
| `ai-shell monitor --interval <time>` | Custom interval | `ai-shell monitor --interval 30s` |
| `ai-shell monitor --alert-email <email>` | With email alerts | `ai-shell monitor --alert-email ops@company.com` |
| `ai-shell health metrics` | Show metrics | `ai-shell health metrics` |
| `ai-shell health alerts` | Configure alerts | `ai-shell health alerts` |
| `ai-shell health alerts --threshold cpu=80` | Set thresholds | `ai-shell health alerts --threshold cpu=80` |
| `ai-shell dashboard` | View metrics dashboard | `ai-shell dashboard` |

**Health Metrics Tracked:**
- Connection count
- Response time
- Error rate
- CPU usage
- Memory usage
- Disk space
- Active queries
- Cache hit rate

---

## Backup & Restore

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell backup create <db>` | Create backup | `ai-shell backup create mydb` |
| `ai-shell backup create <db> --output <file>` | Backup to specific file | `ai-shell backup create mydb --output backup.sql` |
| `ai-shell backup create <db> --format <type>` | Custom format | `ai-shell backup create mydb --format tar` |
| `ai-shell backup list` | List all backups | `ai-shell backup list` |
| `ai-shell backup list --database <db>` | Filter by database | `ai-shell backup list --database mydb` |
| `ai-shell backup restore <file>` | Restore backup | `ai-shell backup restore backup.sql` |
| `ai-shell backup restore <file> --database <db>` | Restore to specific DB | `ai-shell backup restore backup.sql --database newdb` |
| `ai-shell backup verify <file>` | Verify backup integrity | `ai-shell backup verify backup.sql` |
| `ai-shell backup delete <id>` | Delete backup | `ai-shell backup delete backup-123` |

### Backup Scheduling

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell backup schedule <db> --daily` | Daily at midnight | `ai-shell backup schedule mydb --daily` |
| `ai-shell backup schedule <db> --weekly` | Weekly on Sunday | `ai-shell backup schedule mydb --weekly` |
| `ai-shell backup schedule <db> --cron "<expr>"` | Custom schedule | `ai-shell backup schedule mydb --cron "0 2 * * *"` |
| `ai-shell backup schedule <db> --retain <days>` | Set retention | `ai-shell backup schedule mydb --daily --retain 30` |
| `ai-shell backup schedule list` | List schedules | `ai-shell backup schedule list` |
| `ai-shell backup schedule delete <id>` | Delete schedule | `ai-shell backup schedule delete sched-123` |

**Cron Schedule Examples:**
```bash
# Every day at 2 AM
ai-shell backup schedule mydb --cron "0 2 * * *"

# Every 6 hours
ai-shell backup schedule mydb --cron "0 */6 * * *"

# Every Sunday at 3 AM
ai-shell backup schedule mydb --cron "0 3 * * 0"

# First day of month at 1 AM
ai-shell backup schedule mydb --cron "0 1 1 * *"
```

---

## Schema Management

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell schema inspect` | Inspect current schema | `ai-shell schema inspect` |
| `ai-shell schema inspect <table>` | Inspect specific table | `ai-shell schema inspect users` |
| `ai-shell schema design` | Schema design assistant | `ai-shell schema design` |
| `ai-shell schema design --entities "<list>"` | Design with entities | `ai-shell schema design --entities "users,orders,products"` |
| `ai-shell schema diff <source> <target>` | Compare schemas | `ai-shell schema diff dev prod` |
| `ai-shell schema export` | Export schema | `ai-shell schema export` |
| `ai-shell schema export --output <file>` | Export to file | `ai-shell schema export --output schema.sql` |

### Migrations

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell migration generate <name>` | Generate migration | `ai-shell migration generate add_user_email` |
| `ai-shell migration run` | Run pending migrations | `ai-shell migration run` |
| `ai-shell migration rollback` | Rollback last migration | `ai-shell migration rollback` |
| `ai-shell migration status` | Show migration status | `ai-shell migration status` |
| `ai-shell migration test <file>` | Test migration | `ai-shell migration test ./migrations/001.sql` |
| `ai-shell migration test <file> --dry-run` | Test without applying | `ai-shell migration test ./migrations/001.sql --dry-run` |

---

## Performance Profiling

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell profile query "<sql>"` | Profile query | `ai-shell profile query "SELECT * FROM large_table"` |
| `ai-shell profile analyze` | Analyze performance | `ai-shell profile analyze` |
| `ai-shell profile analyze --duration <time>` | Analyze time period | `ai-shell profile analyze --duration 1h` |
| `ai-shell cache stats` | Cache statistics | `ai-shell cache stats` |
| `ai-shell cache clear` | Clear cache | `ai-shell cache clear` |
| `ai-shell cache warm` | Warm up cache | `ai-shell cache warm` |

---

## Federation

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell federation add <name> <uri>` | Add database to federation | `ai-shell federation add mysql1 mysql://...` |
| `ai-shell federation list` | List federated databases | `ai-shell federation list` |
| `ai-shell federation remove <name>` | Remove from federation | `ai-shell federation remove mysql1` |
| `ai-shell federation status` | Show federation status | `ai-shell federation status` |

**Federated Query Examples:**
```bash
# Query across multiple databases
ai-shell translate "show users from postgres_db and orders from mysql_db where user_id matches"

# Join data from different sources
ai-shell translate "combine customer data from crm_db with orders from sales_db"
```

---

## Database-Specific Commands

### PostgreSQL Commands

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell pg-analyze <table>` | Analyze table statistics | `ai-shell pg-analyze users` |
| `ai-shell pg-vacuum <table>` | Vacuum table | `ai-shell pg-vacuum users` |
| `ai-shell pg-vacuum <table> --full` | Full vacuum | `ai-shell pg-vacuum users --full` |
| `ai-shell pg-reindex <index>` | Rebuild index | `ai-shell pg-reindex idx_users_email` |
| `ai-shell pg-stats <table>` | Show table statistics | `ai-shell pg-stats users` |
| `ai-shell pg-bloat` | Check table bloat | `ai-shell pg-bloat` |

### MySQL Commands

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell mysql-analyze <table>` | Analyze table | `ai-shell mysql-analyze users` |
| `ai-shell mysql-optimize <table>` | Optimize table | `ai-shell mysql-optimize users` |
| `ai-shell mysql-repair <table>` | Repair corrupted table | `ai-shell mysql-repair users` |
| `ai-shell mysql-check <table>` | Check table integrity | `ai-shell mysql-check users` |
| `ai-shell mysql-status` | Show server status | `ai-shell mysql-status` |

### MongoDB Commands

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell mongo-stats <collection>` | Collection statistics | `ai-shell mongo-stats users` |
| `ai-shell mongo-index-analyze <coll>` | Index usage analysis | `ai-shell mongo-index-analyze users` |
| `ai-shell mongo-compact <collection>` | Compact collection | `ai-shell mongo-compact users` |
| `ai-shell mongo-validate <collection>` | Validate collection | `ai-shell mongo-validate users` |
| `ai-shell mongo-profile` | Show profiling data | `ai-shell mongo-profile` |

### Redis Commands

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell redis-info` | Server information | `ai-shell redis-info` |
| `ai-shell redis-memory` | Memory usage | `ai-shell redis-memory` |
| `ai-shell redis-slowlog` | Slow query log | `ai-shell redis-slowlog` |
| `ai-shell redis-keys <pattern>` | Find keys by pattern | `ai-shell redis-keys "user:*"` |
| `ai-shell redis-flushdb` | Clear current database | `ai-shell redis-flushdb` |

---

## Configuration

| Command | Description | Example |
|---------|-------------|---------|
| `ai-shell config show` | Show configuration | `ai-shell config show` |
| `ai-shell config set <key> <value>` | Set config value | `ai-shell config set log.level debug` |
| `ai-shell config get <key>` | Get config value | `ai-shell config get cache.ttl` |
| `ai-shell config reset` | Reset to defaults | `ai-shell config reset` |
| `ai-shell config export <file>` | Export config | `ai-shell config export config.yaml` |
| `ai-shell config import <file>` | Import config | `ai-shell config import config.yaml` |

**Common Config Keys:**
```bash
# Caching
ai-shell config set cache.enabled true
ai-shell config set cache.ttl 3600

# Logging
ai-shell config set log.level info
ai-shell config set log.file /var/log/ai-shell.log

# Query settings
ai-shell config set query.timeout 30000
ai-shell config set query.defaultLimit 100
ai-shell config set query.slowThreshold 1000

# Security
ai-shell config set security.vault.encryption aes-256-gcm
ai-shell config set security.audit.enabled true

# Monitoring
ai-shell config set monitoring.enabled true
ai-shell config set monitoring.interval 5000
```

---

## Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | none | `sk-ant-...` |
| `OPENAI_API_KEY` | OpenAI API key | none | `sk-...` |
| `DATABASE_URL` | Default database URL | none | `postgresql://...` |
| `AI_SHELL_CONFIG` | Config file path | `~/.ai-shell/config.yaml` | `/etc/ai-shell/config.yaml` |
| `AI_SHELL_LOG_LEVEL` | Logging level | `info` | `debug` |
| `AI_SHELL_LOG_FILE` | Log file path | `~/.ai-shell/logs/app.log` | `/var/log/ai-shell.log` |
| `AI_SHELL_VAULT_KEY` | Vault encryption key | auto-generated | custom key |
| `AI_SHELL_QUERY_TIMEOUT` | Query timeout (ms) | `30000` | `60000` |
| `AI_SHELL_MAX_CONNECTIONS` | Max DB connections | `10` | `20` |
| `AI_SHELL_POOL_SIZE` | Connection pool size | `5` | `10` |

**Setup Example:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
export AI_SHELL_LOG_LEVEL="info"
export AI_SHELL_QUERY_TIMEOUT="30000"

# Reload shell
source ~/.bashrc
```

---

## Quick Workflows

### Morning Health Check Routine
```bash
ai-shell health-check
ai-shell analyze slow-queries --since 24h
ai-shell backup status
ai-shell security status
```

### Optimize Database Performance
```bash
# 1. Find slow queries
ai-shell analyze slow-queries --threshold 1000ms

# 2. Optimize worst query
ai-shell optimize "SELECT * FROM users WHERE email LIKE '%@gmail.com'"

# 3. Apply suggested indexes
ai-shell index create users email

# 4. Verify improvement
ai-shell profile query "SELECT * FROM users WHERE email = 'test@example.com'"
```

### Setup New Database Connection
```bash
# 1. Store credentials securely
ai-shell vault add prod-db-pass "secretPassword" --encrypt

# 2. Connect with vault reference
ai-shell connect postgresql://admin:{{vault:prod-db-pass}}@prod.db.com:5432/app --name production

# 3. Test connection
ai-shell health-check --connection production

# 4. Setup automated backups
ai-shell backup schedule app --cron "0 2 * * *" --retain 30
```

### Security Audit Workflow
```bash
# 1. Check security status
ai-shell security status

# 2. Run comprehensive scan
ai-shell security scan --deep --output security-report.json

# 3. Check compliance
ai-shell security compliance all

# 4. Verify audit logs
ai-shell audit verify

# 5. Review recent activity
ai-shell audit show --limit 100
```

---

## Getting Help

| Command | Description |
|---------|-------------|
| `ai-shell help` | Show general help |
| `ai-shell help <command>` | Command-specific help |
| `ai-shell --help` | List all commands |
| `ai-shell version` | Show version |
| `ai-shell docs` | Open documentation |

---

## Tips & Tricks

### Using Aliases
```bash
# Create shell aliases for common commands
alias ash='ai-shell'
alias ash-connect='ai-shell connect'
alias ash-query='ai-shell translate'
alias ash-health='ai-shell health-check'
alias ash-backup='ai-shell backup create'
```

### Query Templates
```bash
# Save frequently used queries
ai-shell config set templates.users "SELECT * FROM users WHERE status = 'active'"
ai-shell translate "$(ai-shell config get templates.users)"
```

### Batch Operations
```bash
# Optimize multiple queries
for query in "SELECT * FROM users" "SELECT * FROM orders"; do
  ai-shell optimize "$query"
done

# Backup multiple databases
for db in app_db analytics_db logs_db; do
  ai-shell backup create "$db" --output "backup-$db-$(date +%Y%m%d).sql"
done
```

### Output Formatting
```bash
# JSON output for scripting
ai-shell connections --format json | jq '.[] | select(.active==true)'

# CSV export for analysis
ai-shell audit show --format csv > audit.csv

# Table output for readability
ai-shell health-check --format table
```

---

## Common Error Solutions

### "Connection Failed"
```bash
# Verify connection string format
ai-shell connect postgresql://user:pass@host:5432/db

# Test database accessibility
ping <database-host>
telnet <database-host> <port>

# Check credentials
ai-shell vault get db-credentials
```

### "Query Timeout"
```bash
# Increase timeout
ai-shell config set query.timeout 60000

# Or use environment variable
export AI_SHELL_QUERY_TIMEOUT=60000

# Optimize the query
ai-shell optimize "your slow query here"
```

### "Insufficient Permissions"
```bash
# Check user permissions
ai-shell permission list <username>

# Grant necessary permissions
ai-shell permission grant <role> <resource> --actions read,write
```

---

## Quick Reference Card

**Most Used Commands:**
```bash
# Connect
ai-shell connect <uri>

# Query
ai-shell translate "<natural language>" --execute

# Optimize
ai-shell optimize "<SQL query>"

# Health
ai-shell health-check

# Backup
ai-shell backup create <database>

# Security
ai-shell vault add <name> <value>
ai-shell security status

# Monitor
ai-shell monitor --interval 30s
```

---

## Documentation Links

- **[Quickstart Guide](./QUICKSTART.md)** - Get started in 5 minutes
- **[User Guide](./guides/USER_GUIDE.md)** - Comprehensive feature guide
- **[API Reference](./API_REFERENCE.md)** - Complete API documentation
- **[Security Guide](./guides/SECURITY_BEST_PRACTICES.md)** - Security hardening
- **[Troubleshooting](./TROUBLESHOOTING.md)** - Common issues and solutions

---

**Version:** 1.0.0
**Documentation:** https://github.com/your-org/ai-shell
**Support:** support@ai-shell.dev

---

*This cheatsheet covers 100+ commands across all AI-Shell modules. For detailed usage and examples, see the complete documentation.*
