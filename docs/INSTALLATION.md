# Installation Guide

Complete installation guide for AI-Shell database management platform.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Install](#quick-install)
- [Installation Methods](#installation-methods)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

## Prerequisites

### System Requirements

**Operating Systems:**
- Linux (Ubuntu 18.04+, CentOS 7+, Debian 9+)
- macOS 10.15+
- Windows 10+ with WSL2

**Hardware Requirements:**
- **Minimum**: 2 CPU cores, 4 GB RAM, 1 GB disk
- **Recommended**: 4 CPU cores, 8 GB RAM, 10 GB disk

### Software Dependencies

#### Required

**Node.js 18.0.0 or higher**
```bash
# Check Node.js version
node --version  # Should be v18.0.0 or higher

# If not installed, install via nvm (recommended):
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

**npm or yarn**
```bash
# Check npm version
npm --version  # Should be 9.0.0 or higher

# Or use yarn
yarn --version
```

#### Optional

**Docker** (for containerized deployment)
```bash
docker --version  # Docker 20.10.0+
docker-compose --version  # 1.29.0+
```

**Git** (for source installation)
```bash
git --version  # Git 2.0+
```

### Database Support

AI-Shell connects to existing databases. Install the database you need:

**PostgreSQL** (recommended)
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-client

# macOS
brew install postgresql

# Verify
psql --version  # PostgreSQL 12+
```

**MySQL**
```bash
# Ubuntu/Debian
sudo apt-get install mysql-server mysql-client

# macOS
brew install mysql

# Verify
mysql --version  # MySQL 8.0+
```

**MongoDB**
```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# macOS
brew tap mongodb/brew
brew install mongodb-community

# Verify
mongod --version  # MongoDB 5.0+
```

**Redis**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Verify
redis-server --version  # Redis 6.0+
```

### API Keys

**Anthropic API Key** (required for AI features)
1. Sign up at https://console.anthropic.com
2. Create an API key
3. Set environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Quick Install

The fastest way to get started:

```bash
# Install via npm (recommended)
npm install -g ai-shell

# Verify installation
ai-shell --version

# Set up environment
export ANTHROPIC_API_KEY="your-api-key"

# Connect to your database
ai-shell connect postgres://localhost:5432/mydb
```

Done! You can now use AI-Shell.

## Installation Methods

### Method 1: NPM Install (Recommended)

Install globally for command-line usage:

```bash
# Install latest stable version
npm install -g ai-shell

# Or install specific version
npm install -g ai-shell@1.0.0

# Verify installation
ai-shell --version
which ai-shell
```

### Method 2: From Source

For development or latest features:

```bash
# Clone repository
git clone https://github.com/your-org/ai-shell.git
cd ai-shell

# Install dependencies
npm install

# Build TypeScript
npm run build

# Link for global usage
npm link

# Or use directly
npm start -- --help
```

**Development Mode:**
```bash
# Watch mode for development
npm run dev

# Run tests
npm test

# Type checking
npm run typecheck

# Linting
npm run lint
```

### Method 3: Docker Image

Run AI-Shell in a container:

```bash
# Pull latest image (when available)
# docker pull ai-shell/ai-shell:latest

# Currently: Build from source
git clone https://github.com/your-org/ai-shell.git
cd ai-shell

# Create Dockerfile (example)
cat > Dockerfile <<EOF
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
ENTRYPOINT ["node", "dist/cli/index.js"]
CMD ["--help"]
EOF

# Build image
docker build -t ai-shell:latest .

# Run container
docker run -it --rm \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -e DATABASE_URL="postgres://host.docker.internal:5432/mydb" \
  ai-shell:latest connect $DATABASE_URL
```

**Docker Compose:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  ai-shell:
    build: .
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    command: interactive
```

```bash
# Run with docker-compose
docker-compose up
```

### Method 4: Binary Distribution

Download pre-built binaries (when available):

```bash
# Download for your platform
# Linux
curl -LO https://github.com/your-org/ai-shell/releases/download/v1.0.0/ai-shell-linux-x64

# macOS
curl -LO https://github.com/your-org/ai-shell/releases/download/v1.0.0/ai-shell-macos-x64

# Windows
curl -LO https://github.com/your-org/ai-shell/releases/download/v1.0.0/ai-shell-windows-x64.exe

# Make executable (Linux/macOS)
chmod +x ai-shell-*

# Move to PATH
sudo mv ai-shell-* /usr/local/bin/ai-shell

# Verify
ai-shell --version
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Optional - Default database
export DATABASE_URL="postgres://user:pass@localhost:5432/mydb"

# Optional - Configuration
export AI_SHELL_CONFIG="$HOME/.ai-shell/config.yaml"
export AI_SHELL_LOG_LEVEL="info"  # debug, info, warn, error
export AI_SHELL_LOG_PATH="$HOME/.ai-shell/logs"

# Optional - Redis for caching
export REDIS_URL="redis://localhost:6379"

# Optional - Performance tuning
export AI_SHELL_QUERY_TIMEOUT="30000"  # ms
export AI_SHELL_MAX_CONNECTIONS="10"
export AI_SHELL_POOL_SIZE="5"
```

**For Bash/Zsh:**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

**For Fish:**
```bash
# Add to ~/.config/fish/config.fish
set -gx ANTHROPIC_API_KEY "your-key"
```

### Configuration File

Create `~/.ai-shell/config.yaml`:

```yaml
# AI-Shell Configuration File

# Database Connections
databases:
  production:
    type: postgresql
    host: prod-db.company.com
    port: 5432
    database: production
    username: admin
    # Use vault for passwords (never hardcode!)
    # password: stored-in-vault
    ssl:
      enabled: true
      rejectUnauthorized: true
      ca: /path/to/ca-cert.pem
    poolSize: 10
    connectionTimeout: 30000

  staging:
    type: postgresql
    host: staging-db.company.com
    port: 5432
    database: staging
    username: dev
    poolSize: 5

  analytics:
    type: mongodb
    connectionString: mongodb+srv://user@cluster.mongodb.net/analytics
    poolSize: 5

  cache:
    type: redis
    host: localhost
    port: 6379
    database: 0

# LLM Configuration
llm:
  provider: anthropic
  model: claude-3-sonnet-20240229
  temperature: 0.1
  maxTokens: 4096
  apiKey: ${ANTHROPIC_API_KEY}  # Read from environment

# Security Settings
security:
  vault:
    enabled: true
    encryption: aes-256-gcm
    keyDerivation: pbkdf2
    iterations: 100000

  audit:
    enabled: true
    destination: ~/.ai-shell/logs/audit.log
    rotation: daily
    retention: 90  # days

  rbac:
    enabled: true
    defaultRole: viewer

  sql_injection_prevention: true

  rateLimit:
    enabled: true
    windowMs: 900000  # 15 minutes
    maxRequests: 100

# Query Settings
query:
  timeout: 30000  # ms
  slowQueryThreshold: 1000  # ms
  maxResultSize: 10000  # rows
  defaultLimit: 100

# Performance Monitoring
monitoring:
  enabled: true
  interval: 5000  # ms
  metrics:
    - cpu
    - memory
    - connections
    - queryCount

  alerts:
    enabled: true
    channels:
      email:
        enabled: false
        to: []
      slack:
        enabled: false
        webhookUrl: ""

# Caching
cache:
  enabled: true
  provider: redis
  ttl: 3600  # seconds
  maxSize: 100  # MB

# Logging
logging:
  level: info  # debug, info, warn, error
  format: json  # json, text
  destination: file
  file:
    path: ~/.ai-shell/logs
    maxSize: 10485760  # 10MB
    maxFiles: 10
    compression: true

# Features
features:
  queryOptimization: true
  healthMonitoring: true
  backupSystem: true
  federation: true
  schemaDesign: true
  queryCache: true
  migrationTesting: true
  sqlExplainer: true
  schemaDiff: true
  costOptimization: true
```

### Directory Structure

AI-Shell creates the following directory structure:

```
~/.ai-shell/
├── config.yaml          # Main configuration
├── state.json           # Application state
├── vault/               # Encrypted credentials
│   └── credentials.enc
├── logs/                # Log files
│   ├── audit.log
│   ├── application.log
│   └── error.log
├── cache/               # Query cache
├── backups/             # Database backups
├── contexts/            # Saved contexts
└── sessions/            # Session data
```

## Verification

### Test Installation

```bash
# Check version
ai-shell --version

# Check help
ai-shell --help

# List features
ai-shell features
```

### Test Database Connection

```bash
# Test PostgreSQL
ai-shell connect postgres://localhost:5432/postgres --test

# Test MySQL
ai-shell connect mysql://root@localhost:3306/mysql --test

# Test MongoDB
ai-shell connect mongodb://localhost:27017/test --test

# Test Redis
ai-shell connect redis://localhost:6379 --test
```

### Run Health Check

```bash
# Create a test connection
ai-shell connect postgres://localhost:5432/postgres --name test

# Run health check
ai-shell health-check
```

### Test Basic Commands

```bash
# Connect to database
ai-shell connect postgres://localhost:5432/mydb --name local

# List connections
ai-shell connections

# Run a simple query
ai-shell optimize "SELECT 1"

# Check monitoring
ai-shell health-check
```

## Troubleshooting

### Common Issues

#### Issue: "command not found: ai-shell"

**Solution:**
```bash
# Check if npm global bin is in PATH
npm config get prefix

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$PATH:$(npm config get prefix)/bin"

# Or reinstall globally
npm install -g ai-shell
```

#### Issue: "Cannot find module..."

**Solution:**
```bash
# Rebuild node modules
cd /path/to/ai-shell
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### Issue: "Database connection failed"

**Solution:**
```bash
# Check database is running
# PostgreSQL
pg_isready -h localhost

# MySQL
mysqladmin ping -h localhost

# MongoDB
mongosh --eval "db.adminCommand('ping')"

# Redis
redis-cli ping

# Check connection string format
# PostgreSQL: postgres://user:pass@host:port/database
# MySQL: mysql://user:pass@host:port/database
# MongoDB: mongodb://host:port/database
# Redis: redis://host:port/database
```

#### Issue: "ANTHROPIC_API_KEY not set"

**Solution:**
```bash
# Set environment variable
export ANTHROPIC_API_KEY="sk-ant-..."

# Or add to ~/.bashrc
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc

# Verify
echo $ANTHROPIC_API_KEY
```

#### Issue: "Permission denied"

**Solution:**
```bash
# Linux/macOS - Check file permissions
ls -la $(which ai-shell)

# Fix permissions
sudo chmod +x $(which ai-shell)

# Or reinstall without sudo
npm config set prefix ~/.npm-global
export PATH=~/.npm-global/bin:$PATH
npm install -g ai-shell
```

#### Issue: "Port already in use"

**Solution:**
```bash
# Check what's using the port
# Linux
sudo lsof -i :5432

# macOS
lsof -i :5432

# Kill process or change port
ai-shell connect postgres://localhost:5433/mydb
```

#### Issue: "SSL/TLS connection error"

**Solution:**
```bash
# Disable SSL for testing (not recommended for production)
ai-shell connect "postgres://localhost:5432/mydb?sslmode=disable"

# Or configure SSL properly
ai-shell connect postgres://localhost:5432/mydb --name prod <<EOF
ssl:
  enabled: true
  rejectUnauthorized: false  # For self-signed certs
EOF
```

### Log Files

Check logs for detailed error information:

```bash
# View application logs
cat ~/.ai-shell/logs/application.log

# View error logs
cat ~/.ai-shell/logs/error.log

# View audit logs
cat ~/.ai-shell/logs/audit.log

# Follow logs in real-time
tail -f ~/.ai-shell/logs/application.log
```

### Debug Mode

Enable verbose logging:

```bash
# Set log level
export AI_SHELL_LOG_LEVEL="debug"

# Or use --verbose flag
ai-shell --verbose connect postgres://localhost:5432/mydb
```

### Reset Configuration

If configuration is corrupted:

```bash
# Backup current config
cp -r ~/.ai-shell ~/.ai-shell.backup

# Remove configuration
rm -rf ~/.ai-shell

# Reinstall
npm install -g ai-shell

# Reconfigure
ai-shell connect postgres://localhost:5432/mydb
```

### Get Help

If issues persist:

1. **Check Documentation**: https://github.com/your-org/ai-shell
2. **Search Issues**: https://github.com/your-org/ai-shell/issues
3. **Ask Community**: https://github.com/your-org/ai-shell/discussions
4. **Report Bug**: https://github.com/your-org/ai-shell/issues/new

## Next Steps

After successful installation:

### 1. Read Getting Started Guide
```bash
# View getting started guide
cat docs/GETTING_STARTED.md
```

### 2. Connect to Your Database
```bash
# Interactive connection setup
ai-shell connect postgres://localhost:5432/mydb --name production
```

### 3. Explore Features
```bash
# List all features
ai-shell features

# Try query optimization
ai-shell optimize "SELECT * FROM users WHERE active = true"

# Run health check
ai-shell health-check

# Start monitoring
ai-shell monitor
```

### 4. Configure Security
```bash
# Set up vault
ai-shell vault-add production "your-password" --encrypt

# Enable audit logging
# Edit ~/.ai-shell/config.yaml
security:
  audit:
    enabled: true
```

### 5. Review Tutorials
- [Natural Language Queries](./tutorials/natural-language-queries.md)
- [Query Optimization](./tutorials/query-optimization.md)
- [Performance Monitoring](./tutorials/performance-monitoring.md)
- [Security Setup](./tutorials/security.md)

## Platform-Specific Notes

### Linux

**Ubuntu/Debian:**
```bash
# Install build essentials (if building from source)
sudo apt-get install build-essential

# Install PostgreSQL client libraries
sudo apt-get install libpq-dev
```

**CentOS/RHEL:**
```bash
# Install development tools
sudo yum groupinstall "Development Tools"

# Install PostgreSQL development packages
sudo yum install postgresql-devel
```

### macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Use Homebrew for dependencies
brew install node postgresql mysql mongodb redis
```

### Windows (WSL2)

```bash
# Install WSL2
wsl --install

# Install Ubuntu
wsl --install -d Ubuntu

# Inside WSL, follow Linux instructions
sudo apt-get update
sudo apt-get install nodejs npm postgresql-client
```

**Native Windows:**
- Install Node.js from https://nodejs.org
- Use Windows Terminal for best experience
- PostgreSQL: https://www.postgresql.org/download/windows/
- MySQL: https://dev.mysql.com/downloads/installer/

## Production Deployment

For production environments:

### 1. Use Process Manager

**PM2:**
```bash
# Install PM2
npm install -g pm2

# Start AI-Shell as service
pm2 start ai-shell -- interactive
pm2 save
pm2 startup
```

**systemd (Linux):**
```bash
# Create service file
sudo nano /etc/systemd/system/ai-shell.service

[Unit]
Description=AI-Shell Database Manager
After=network.target

[Service]
Type=simple
User=ai-shell
Environment="ANTHROPIC_API_KEY=sk-ant-..."
ExecStart=/usr/local/bin/ai-shell interactive
Restart=on-failure

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable ai-shell
sudo systemctl start ai-shell
```

### 2. Configure Monitoring

Set up health checks and monitoring:
```bash
# Configure alerts in config.yaml
monitoring:
  alerts:
    email:
      enabled: true
      to: ["ops@company.com"]
```

### 3. Secure Credentials

Never commit secrets:
```bash
# Use vault for all credentials
ai-shell vault-add prod-db "password" --encrypt

# Use environment variables
export DATABASE_URL="postgres://..."

# Use secret management (AWS Secrets Manager, HashiCorp Vault, etc.)
```

## Support

- **Documentation**: https://github.com/your-org/ai-shell
- **Issues**: https://github.com/your-org/ai-shell/issues
- **Discussions**: https://github.com/your-org/ai-shell/discussions
- **Email**: support@ai-shell.dev

---

**Last Updated**: October 28, 2025
**Version**: 1.0.0
