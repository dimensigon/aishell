# Installation Guide

Complete installation guide for AI-Shell - the world's first Claude-powered, multi-database federation platform.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
  - [NPM Installation (Recommended)](#npm-installation-recommended)
  - [Docker Installation](#docker-installation)
  - [Building from Source](#building-from-source)
- [Platform-Specific Instructions](#platform-specific-instructions)
  - [Linux](#linux)
  - [macOS](#macos)
  - [Windows](#windows)
- [Post-Installation Setup](#post-installation-setup)
- [Verification Steps](#verification-steps)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **Node.js** | 18.0 or higher |
| **npm** | 9.0 or higher |
| **RAM** | 512MB minimum |
| **Storage** | 200MB for installation |
| **Operating System** | Linux, macOS, Windows 10+ |

### Recommended Requirements

| Component | Recommendation |
|-----------|----------------|
| **Node.js** | 20.0 or higher |
| **npm** | 10.0 or higher |
| **RAM** | 2GB or more |
| **Storage** | 1GB for installation + cache |
| **Operating System** | Linux (Ubuntu 20.04+), macOS 12+, Windows 11 |

### Supported Databases

AI-Shell supports multiple database systems:

- **PostgreSQL** 10+ (fully supported)
- **MySQL/MariaDB** 5.7+ / 10.3+ (fully supported)
- **MongoDB** 4.4+ (fully supported)
- **Redis** 6.0+ (fully supported)
- **Oracle Database** 12c+ (fully supported)
- **Apache Cassandra** 3.11+ (beta support)
- **Neo4j** 4.0+ (beta support)

**Note**: You need at least one database system installed to use AI-Shell effectively.

---

## Installation Methods

### NPM Installation (Recommended)

The easiest way to install AI-Shell is through npm.

#### Global Installation

```bash
# Install globally (recommended for CLI usage)
npm install -g ai-shell

# Verify installation
ai-shell --version
```

**Expected Output:**
```
ai-shell v1.0.0
```

#### Local Installation

```bash
# Install in your project
npm install ai-shell --save

# Run via npx
npx ai-shell --version
```

#### Installation Without Administrative Rights

If you don't have sudo/admin privileges:

```bash
# Install to user directory
npm install -g ai-shell --prefix ~/.local

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

---

### Docker Installation

Run AI-Shell in an isolated container without installing Node.js.

#### Quick Start with Docker

```bash
# Pull the latest image
docker pull aishell/ai-shell:latest

# Run interactively
docker run -it --rm aishell/ai-shell:latest

# Run with environment variables
docker run -it --rm \
  -e ANTHROPIC_API_KEY="your-api-key" \
  aishell/ai-shell:latest
```

#### Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  ai-shell:
    image: aishell/ai-shell:latest
    container_name: ai-shell
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AI_SHELL_LOG_LEVEL=info
    volumes:
      - ./data:/app/data
      - ./config:/app/.ai-shell
    networks:
      - ai-shell-network
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    container_name: ai-shell-postgres
    environment:
      - POSTGRES_DB=aishell
      - POSTGRES_USER=aishell
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - ai-shell-network

  redis:
    image: redis:7-alpine
    container_name: ai-shell-redis
    volumes:
      - redis-data:/data
    networks:
      - ai-shell-network

volumes:
  postgres-data:
  redis-data:

networks:
  ai-shell-network:
    driver: bridge
```

Start the stack:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f ai-shell

# Execute commands
docker-compose exec ai-shell ai-shell query "show databases"

# Stop services
docker-compose down
```

#### Building Custom Docker Image

```bash
# Clone repository
git clone https://github.com/your-org/ai-shell.git
cd ai-shell

# Build custom image
docker build -t ai-shell-custom:latest .

# Run custom image
docker run -it --rm ai-shell-custom:latest
```

---

### Building from Source

For developers who want to contribute or customize AI-Shell.

#### Prerequisites

```bash
# Verify Node.js version
node --version  # Should be 18.0 or higher

# Verify npm version
npm --version   # Should be 9.0 or higher

# Install build tools (Linux)
sudo apt-get install build-essential python3

# Install build tools (macOS)
xcode-select --install

# Install build tools (Windows)
# Download and install Visual Studio Build Tools
# https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
```

#### Clone and Build

```bash
# Clone the repository
git clone https://github.com/your-org/ai-shell.git
cd ai-shell

# Install dependencies
npm install

# Build the project
npm run build

# Run tests to verify build
npm test

# Link for global usage
npm link

# Verify installation
ai-shell --version
```

#### Development Build

```bash
# Install development dependencies
npm install

# Run in development mode with auto-reload
npm run dev

# Run tests in watch mode
npm run test:watch

# Run linting
npm run lint

# Run type checking
npm run typecheck
```

---

## Platform-Specific Instructions

### Linux

#### Ubuntu/Debian

```bash
# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version

# Install AI-Shell
sudo npm install -g ai-shell

# Verify AI-Shell installation
ai-shell --version
```

#### RHEL/CentOS/Fedora

```bash
# Install Node.js 20.x
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install -y nodejs

# Verify installation
node --version
npm --version

# Install AI-Shell
sudo npm install -g ai-shell

# Verify AI-Shell installation
ai-shell --version
```

#### Arch Linux

```bash
# Install Node.js
sudo pacman -S nodejs npm

# Install AI-Shell
sudo npm install -g ai-shell

# Verify installation
ai-shell --version
```

#### Common Linux Issues

**Issue: Permission denied during npm install**
```bash
# Solution 1: Use npx (no installation)
npx ai-shell

# Solution 2: Configure npm to use user directory
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
npm install -g ai-shell
```

**Issue: Missing build tools**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3

# RHEL/CentOS
sudo yum groupinstall "Development Tools"
sudo yum install python3
```

---

### macOS

#### Using Homebrew (Recommended)

```bash
# Install Node.js via Homebrew
brew install node

# Verify installation
node --version
npm --version

# Install AI-Shell
npm install -g ai-shell

# Verify AI-Shell installation
ai-shell --version
```

#### Using Node Version Manager (nvm)

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Reload shell configuration
source ~/.zshrc  # or ~/.bash_profile for bash

# Install Node.js 20
nvm install 20
nvm use 20
nvm alias default 20

# Verify installation
node --version
npm --version

# Install AI-Shell
npm install -g ai-shell

# Verify AI-Shell installation
ai-shell --version
```

#### macOS-Specific Issues

**Issue: Command not found after installation**
```bash
# Add npm global bin to PATH
echo 'export PATH="$(npm config get prefix)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Issue: Permission errors on macOS Catalina+**
```bash
# Use npx instead of global install
npx ai-shell

# Or fix npm permissions
sudo chown -R $(whoami) ~/.npm
```

---

### Windows

#### Using Node.js Installer (Recommended)

1. Download Node.js from [https://nodejs.org/](https://nodejs.org/)
2. Run the installer (choose LTS version)
3. Follow installation wizard (accept defaults)
4. Open Command Prompt or PowerShell as Administrator
5. Install AI-Shell:

```powershell
# Install globally
npm install -g ai-shell

# Verify installation
ai-shell --version
```

#### Using Windows Subsystem for Linux (WSL)

```bash
# In WSL terminal, follow Linux instructions
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g ai-shell
ai-shell --version
```

#### Using Chocolatey

```powershell
# Install Chocolatey (if not installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Node.js
choco install nodejs-lts

# Refresh environment variables
refreshenv

# Install AI-Shell
npm install -g ai-shell

# Verify installation
ai-shell --version
```

#### Windows-Specific Issues

**Issue: Execution policy prevents script execution**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Retry installation
npm install -g ai-shell
```

**Issue: Python/build tools missing**
```powershell
# Install Windows Build Tools
npm install -g windows-build-tools

# Or install Visual Studio Build Tools manually
# https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
```

**Issue: Long path names causing errors**
```powershell
# Enable long paths in Windows 10/11
# Run as Administrator in PowerShell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Restart computer
```

---

## Post-Installation Setup

### 1. Configure Anthropic API Key

AI-Shell requires an Anthropic API key for AI-powered features.

```bash
# Set environment variable (Linux/macOS)
export ANTHROPIC_API_KEY="your-api-key-here"

# Add to shell profile for persistence
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# Set environment variable (Windows PowerShell)
$env:ANTHROPIC_API_KEY="your-api-key-here"

# Set permanently (Windows)
setx ANTHROPIC_API_KEY "your-api-key-here"
```

**Get your API key**: [https://console.anthropic.com/](https://console.anthropic.com/)

### 2. Run Interactive Setup Wizard

```bash
# Launch setup wizard
ai-shell setup
```

The wizard will guide you through:
- Database connection configuration
- LLM provider settings
- Security preferences
- Performance tuning
- Feature enablement

### 3. Manual Configuration

Create configuration file at `~/.ai-shell/config.yaml`:

```yaml
# Database connections
databases:
  default:
    type: postgres
    host: localhost
    port: 5432
    database: mydb
    username: myuser
    # Password will be prompted or use vault

# LLM configuration
llm:
  provider: anthropic
  model: claude-3-sonnet
  temperature: 0.1
  maxTokens: 4096

# Security settings
security:
  vault:
    enabled: true
    encryption: aes-256
  audit:
    enabled: true
    logPath: ~/.ai-shell/logs/audit.log

# Performance settings
performance:
  queryTimeout: 30000
  cacheSize: 5000
  parallelQueries: 4
```

### 4. Configure Database Connections

```bash
# Add database connection
ai-shell config set database.default postgres://user:pass@localhost:5432/mydb

# Or use vault for secure storage
ai-shell vault add production --interactive

# List configured databases
ai-shell config list databases

# Test connection
ai-shell test-connection default
```

---

## Verification Steps

### 1. Check Installation

```bash
# Verify AI-Shell is installed
ai-shell --version

# Expected output: ai-shell v1.0.0
```

### 2. Check Dependencies

```bash
# Check Node.js version
node --version
# Should be v18.0.0 or higher

# Check npm version
npm --version
# Should be 9.0.0 or higher
```

### 3. Verify Configuration

```bash
# Display current configuration
ai-shell config show

# Check LLM provider configuration
ai-shell config get llm.provider
# Should return: anthropic

# Verify API key is set
ai-shell config validate
```

### 4. Test Database Connection

```bash
# Connect to database
ai-shell connect postgres://localhost:5432/testdb

# Or test existing connection
ai-shell test-connection default
```

**Expected Output:**
```
✓ Successfully connected to postgres://localhost:5432/testdb
✓ Database version: PostgreSQL 16.0
✓ Connection pool initialized (5 connections)
```

### 5. Run Test Query

```bash
# Simple test query
ai-shell query "show databases"

# Natural language query
ai-shell query "show me the current date"
```

### 6. Check System Status

```bash
# Display system diagnostics
ai-shell status

# Run health check
ai-shell health-check
```

**Expected Output:**
```
✓ AI-Shell v1.0.0
✓ Node.js v20.10.0
✓ LLM Provider: Anthropic (Claude)
✓ Active Connections: 1
✓ Cache Status: 0/5000 entries
✓ System Health: OK
```

---

## Troubleshooting

### Installation Issues

#### Problem: npm install fails with EACCES error

**Cause**: Permission issues with npm global directory

**Solution**:
```bash
# Option 1: Use npx (no installation needed)
npx ai-shell

# Option 2: Configure npm to use user directory
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
npm install -g ai-shell

# Option 3: Fix permissions (not recommended)
sudo chown -R $(whoami) $(npm config get prefix)/{lib/node_modules,bin,share}
```

#### Problem: Command not found after installation

**Cause**: npm bin directory not in PATH

**Solution**:
```bash
# Find npm bin directory
npm config get prefix

# Add to PATH (replace with your path)
echo 'export PATH="/path/to/npm/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify
which ai-shell
```

#### Problem: Build fails with node-gyp errors

**Cause**: Missing build tools

**Solution**:
```bash
# Linux (Ubuntu/Debian)
sudo apt-get install build-essential python3

# Linux (RHEL/CentOS)
sudo yum groupinstall "Development Tools"

# macOS
xcode-select --install

# Windows
npm install -g windows-build-tools
```

### Configuration Issues

#### Problem: ANTHROPIC_API_KEY not found

**Cause**: Environment variable not set

**Solution**:
```bash
# Set temporarily
export ANTHROPIC_API_KEY="your-key-here"

# Set permanently (Linux/macOS)
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc

# Set permanently (Windows)
setx ANTHROPIC_API_KEY "your-key-here"
# Restart terminal
```

#### Problem: Cannot connect to database

**Cause**: Incorrect connection string or database not running

**Solution**:
```bash
# Verify database is running
# For PostgreSQL:
pg_isready -h localhost -p 5432

# For MySQL:
mysqladmin ping -h localhost

# Check connection string format
# PostgreSQL: postgres://user:pass@host:port/database
# MySQL: mysql://user:pass@host:port/database
# MongoDB: mongodb://user:pass@host:port/database

# Test connection with verbose output
ai-shell connect postgres://localhost:5432/mydb --verbose
```

### Runtime Issues

#### Problem: Out of memory errors

**Cause**: Insufficient RAM or memory leak

**Solution**:
```bash
# Increase Node.js heap size
export NODE_OPTIONS="--max-old-space-size=4096"

# Or run with increased memory
node --max-old-space-size=4096 $(which ai-shell) query "your query"

# Clear cache
ai-shell cache clear
```

#### Problem: Slow query performance

**Cause**: Network latency, database performance, or LLM processing

**Solution**:
```bash
# Enable caching
ai-shell config set performance.cacheEnabled true

# Increase connection pool
ai-shell config set database.default.pool.max 20

# Use local LLM for better performance (if available)
ai-shell config set llm.provider local
```

### Getting Help

If you encounter issues not covered here:

1. **Check Documentation**: [docs.ai-shell.dev](https://docs.ai-shell.dev)
2. **Search GitHub Issues**: [github.com/your-org/ai-shell/issues](https://github.com/your-org/ai-shell/issues)
3. **Ask Community**: [discord.gg/ai-shell](https://discord.gg/ai-shell)
4. **Report Bug**: [github.com/your-org/ai-shell/issues/new](https://github.com/your-org/ai-shell/issues/new)

**When reporting issues, include**:
- AI-Shell version (`ai-shell --version`)
- Node.js version (`node --version`)
- Operating system
- Error messages
- Steps to reproduce

---

## Next Steps

After successful installation:

1. **Follow Quick Start Guide**: [docs/quick-start.md](./quick-start.md)
2. **Configure Security**: [docs/tutorials/security.md](./tutorials/security.md)
3. **Learn Natural Language Queries**: [docs/tutorials/natural-language-queries.md](./tutorials/natural-language-queries.md)
4. **Explore Features**: [README.md](../README.md#features)

---

**Need help?** Join our community on [Discord](https://discord.gg/ai-shell) or [GitHub Discussions](https://github.com/your-org/ai-shell/discussions).
