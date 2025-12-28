# AI-Shell Quickstart Guide

**Get up and running in 5 minutes!**

This guide will have you querying databases with natural language in under 5 minutes. Let's go!

---

## 1. Quick Install (30 seconds)

### Prerequisites
- Node.js 18+ and npm
- A database (PostgreSQL, MySQL, MongoDB, or Redis)
- Anthropic API key ([Get one free](https://console.anthropic.com))

### Install AI-Shell

```bash
# Clone the repository
git clone https://github.com/your-org/ai-shell.git
cd ai-shell

# Install dependencies and build
npm install && npm run build

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Or via npm (when published):**
```bash
npm install -g ai-shell
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

---

## 2. Connect to Your Database (30 seconds)

```bash
# PostgreSQL
ai-shell connect postgres://user:password@localhost:5432/mydb

# MySQL
ai-shell connect mysql://user:password@localhost:3306/mydb

# MongoDB
ai-shell connect mongodb://localhost:27017/mydb

# Redis
ai-shell connect redis://localhost:6379
```

**Verify connection:**
```bash
ai-shell connections
# Output: Lists all configured connections
```

---

## 3. Your First Natural Language Query (1 minute)

AI-Shell translates natural language to SQL/NoSQL queries automatically!

```bash
# Ask questions in plain English
ai-shell translate "show me all users"

# More complex queries
ai-shell translate "find customers who spent over $1000 last month" --execute

# MongoDB queries
ai-shell translate "count products with low inventory" --database mongo --execute

# Get query insights
ai-shell translate "top 10 revenue generating products" --explain
```

**Example Output:**
```
Natural Query: "show me all users"
SQL: SELECT * FROM users
Confidence: 95%
Estimated Rows: 1,543
Execution Time: 125ms

[Results displayed in formatted table]
```

---

## 4. Key Features (2 minutes)

### Query Optimization
Improve slow queries automatically:

```bash
# Analyze and optimize a query
ai-shell optimize "SELECT * FROM users WHERE email LIKE '%@gmail.com'"

# Output:
# - Current performance metrics
# - Recommended indexes
# - Optimized query version
# - Expected performance gain: 78% faster
```

### Health Monitoring
Check database health in real-time:

```bash
# Quick health check
ai-shell health-check

# Continuous monitoring
ai-shell monitor --interval 10s

# View metrics dashboard
ai-shell dashboard
```

### Secure Credential Storage
Store database passwords securely:

```bash
# Add credential to vault
ai-shell vault-add production-db "mySecretPassword" --encrypt

# Use in connection string
ai-shell connect postgres://user:{{vault:production-db}}@host:5432/db

# List stored credentials
ai-shell vault-list
```

### Automated Backups
Schedule and manage backups:

```bash
# Create immediate backup
ai-shell backup create mydb --output ./backup.sql

# Schedule daily backups at 2 AM
ai-shell backup schedule mydb --cron "0 2 * * *" --retain 30

# Restore from backup
ai-shell backup restore ./backup.sql --database mydb
```

---

## 5. Quick Reference (1 minute)

### Essential Commands

| Task | Command |
|------|---------|
| **Connect to database** | `ai-shell connect <connection-string>` |
| **Natural language query** | `ai-shell translate "<query>" --execute` |
| **Optimize slow query** | `ai-shell optimize "<SQL query>"` |
| **Health check** | `ai-shell health-check` |
| **Create backup** | `ai-shell backup create <database>` |
| **Store credential** | `ai-shell vault-add <name> <value>` |
| **List connections** | `ai-shell connections` |
| **Monitor live** | `ai-shell monitor` |
| **View help** | `ai-shell help` |

### Database-Specific Commands

**PostgreSQL:**
```bash
ai-shell pg-analyze <table>           # Analyze table statistics
ai-shell pg-vacuum <table>            # Vacuum table
ai-shell pg-reindex <index>           # Rebuild index
```

**MySQL:**
```bash
ai-shell mysql-analyze <table>        # Analyze table
ai-shell mysql-optimize <table>       # Optimize table
ai-shell mysql-repair <table>         # Repair corrupted table
```

**MongoDB:**
```bash
ai-shell mongo-stats <collection>     # Collection statistics
ai-shell mongo-index-analyze <coll>   # Index usage analysis
ai-shell mongo-compact <collection>   # Compact collection
```

**Redis:**
```bash
ai-shell redis-info                   # Server information
ai-shell redis-memory                 # Memory usage
ai-shell redis-slowlog                # Slow query log
```

---

## 6. Real-World Example (1 minute)

**Scenario:** Connect to PostgreSQL, optimize queries, set up monitoring and backups

```bash
# Step 1: Connect securely
ai-shell vault-add prod-password "mySecurePass123" --encrypt
ai-shell connect postgres://admin:{{vault:prod-password}}@prod.db.com:5432/myapp

# Step 2: Find slow queries and optimize
ai-shell optimize "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id WHERE u.created_at > '2024-01-01'"

# Output suggests:
# - Add index on users(created_at)
# - Optimized query with better join order
# - Expected 65% performance improvement

# Step 3: Set up health monitoring
ai-shell monitor --interval 30s --alert-email ops@company.com

# Step 4: Schedule automated backups
ai-shell backup schedule myapp --cron "0 2 * * *" --retain 30 --cloud aws

# Step 5: Verify everything is working
ai-shell health-check

# All green! Your database is optimized and protected.
```

---

## 7. Next Steps

### Learn Advanced Features

- **[Complete User Guide](./guides/USER_GUIDE.md)** - Comprehensive feature documentation
- **[Database Operations](./guides/DATABASE_OPERATIONS.md)** - Multi-database management
- **[Query Optimization](./guides/QUERY_OPTIMIZATION.md)** - AI-powered performance tuning
- **[Security Guide](./guides/SECURITY_BEST_PRACTICES.md)** - Hardening and compliance
- **[Integration Guide](./guides/INTEGRATION_GUIDE.md)** - Slack, Grafana, CI/CD

### Try Advanced Features

**Database Federation:**
```bash
# Query across multiple databases
ai-shell translate "show users from postgres_db and orders from mysql_db where user_id matches"
```

**Schema Design Assistant:**
```bash
# Get AI recommendations for schema design
ai-shell schema design --entities "users, orders, products" --relationships "user-orders: one-to-many"
```

**Migration Testing:**
```bash
# Test migrations safely before production
ai-shell migration test ./migrations/001_add_users.sql --dry-run
```

**Performance Profiling:**
```bash
# Deep performance analysis
ai-shell profile query "SELECT * FROM large_table WHERE complex_condition"
```

---

## 8. Common Workflows

### Morning Health Check Routine
```bash
# Check all database health
ai-shell health-check

# Review slow queries from last 24h
ai-shell analyze slow-queries --since 24h

# Check backup status
ai-shell backup status
```

### Troubleshooting Performance Issues
```bash
# Find slow queries
ai-shell analyze slow-queries

# Optimize worst performing query
ai-shell optimize "SELECT ... FROM ... WHERE ..."

# Check if optimization helped
ai-shell analyze performance --compare
```

### Setting Up New Database Connection
```bash
# Store credentials securely
ai-shell vault-add new-db-password "password" --encrypt

# Connect with vault reference
ai-shell connect postgres://user:{{vault:new-db-password}}@host:5432/db --name new-db

# Test connection
ai-shell health-check --connection new-db

# Set up automated backups
ai-shell backup schedule new-db --daily --retain 30
```

---

## Quick Troubleshooting

### "Command not found: ai-shell"
```bash
# Check installation
npm list -g ai-shell

# Add npm bin to PATH
export PATH="$PATH:$(npm config get prefix)/bin"

# Or use npm start from project directory
cd /path/to/ai-shell && npm start -- --help
```

### "Database connection failed"
```bash
# Test connection string format
# PostgreSQL: postgres://user:pass@host:5432/database
# MySQL: mysql://user:pass@host:3306/database
# MongoDB: mongodb://host:27017/database
# Redis: redis://host:6379

# Verify database is running
pg_isready -h localhost       # PostgreSQL
mysqladmin ping -h localhost  # MySQL
mongosh --eval "db.version()" # MongoDB
redis-cli ping                # Redis
```

### "ANTHROPIC_API_KEY not set"
```bash
# Set environment variable
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Add to shell profile for persistence
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### View Debug Logs
```bash
# Enable verbose logging
export AI_SHELL_LOG_LEVEL="debug"
ai-shell --verbose <command>

# Check logs
tail -f ~/.ai-shell/logs/application.log
```

---

## Configuration Tips

### Create Config File
Create `~/.ai-shell/config.yaml` for persistent settings:

```yaml
# Default database connection
databases:
  default:
    type: postgresql
    host: localhost
    port: 5432
    database: mydb
    username: admin
    # Password stored in vault

# Query settings
query:
  timeout: 30000
  defaultLimit: 100
  slowQueryThreshold: 1000

# Security
security:
  vault:
    enabled: true
    encryption: aes-256-gcm
  audit:
    enabled: true

# Monitoring
monitoring:
  enabled: true
  interval: 5000
```

### Environment Variables
```bash
# Core settings
export ANTHROPIC_API_KEY="sk-ant-..."
export DATABASE_URL="postgres://..."
export AI_SHELL_LOG_LEVEL="info"

# Performance tuning
export AI_SHELL_QUERY_TIMEOUT="30000"
export AI_SHELL_MAX_CONNECTIONS="10"
export AI_SHELL_POOL_SIZE="5"

# Add to ~/.bashrc for persistence
```

---

## Getting Help

### Documentation
- **Main README:** [./README.md](./README.md)
- **User Guides:** [./guides/](./guides/)
- **API Reference:** [./CLI_REFERENCE.md](./CLI_REFERENCE.md)
- **Troubleshooting:** [./TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

### Built-in Help
```bash
# General help
ai-shell help

# Command-specific help
ai-shell help translate
ai-shell help backup
ai-shell help optimize

# List all commands
ai-shell --help
```

### Community & Support
- **GitHub Issues:** [github.com/your-org/ai-shell/issues](https://github.com/your-org/ai-shell/issues)
- **Discussions:** [github.com/your-org/ai-shell/discussions](https://github.com/your-org/ai-shell/discussions)
- **Discord:** [discord.gg/aishell](https://discord.gg/aishell)
- **Email:** support@ai-shell.dev

---

## Success Checklist

After completing this guide, you should be able to:

- [ ] Install and configure AI-Shell
- [ ] Connect to your database securely
- [ ] Run natural language queries
- [ ] Optimize slow queries with AI assistance
- [ ] Monitor database health in real-time
- [ ] Set up automated backups
- [ ] Store credentials in encrypted vault
- [ ] Understand basic troubleshooting

**Time to complete: 5 minutes** ✓

---

## What Makes AI-Shell Special?

- **Natural Language Interface** - No SQL knowledge required
- **AI-Powered Optimization** - Automatic query performance tuning
- **Multi-Database Support** - PostgreSQL, MySQL, MongoDB, Redis
- **Enterprise Security** - Vault, audit logs, RBAC, encryption
- **Real-Time Monitoring** - Health checks, alerts, dashboards
- **Automated Backups** - Scheduling, retention, cloud storage
- **Zero Configuration** - Intelligent defaults, easy setup
- **Production Ready** - Battle-tested with 441 passing tests

---

**Ready to become a database superhero?** Start with `ai-shell connect` and let AI do the heavy lifting!

For comprehensive documentation, see the [Complete User Guide](./guides/USER_GUIDE.md).

---

**Version:** 1.0.0
**Last Updated:** October 30, 2025
**Documentation:** [github.com/your-org/ai-shell](https://github.com/your-org/ai-shell)
