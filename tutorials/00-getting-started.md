# Getting Started with AIShell

**Welcome to AIShell!** 🚀

AIShell is an intelligent command-line interface that combines traditional shell functionality with AI-powered assistance, database management, and multi-threaded asynchronous processing. This guide will help you get up and running in minutes.

---

## Table of Contents

1. [What is AIShell?](#what-is-aishell)
2. [Installation](#installation)
3. [First Steps](#first-steps)
4. [Core Concepts](#core-concepts)
5. [Quick Wins](#quick-wins)
6. [Project Structure](#project-structure)
7. [Configuration](#configuration)
8. [Running Your First Agent](#running-your-first-agent)
9. [Next Steps](#next-steps)
10. [Troubleshooting](#troubleshooting)
11. [Quick Reference Card](#quick-reference-card)

---

## What is AIShell?

AIShell (AI$) is a next-generation command-line interface that enhances your terminal experience with:

- **🤖 AI-Powered Intelligence**: Local and cloud LLM integration for natural language commands
- **📊 Database Management**: MCP-based support for Oracle, PostgreSQL, and more
- **🔐 Security First**: Encrypted credential vault with automatic sensitive data redaction
- **⚡ High Performance**: Asynchronous processing with vector-based autocomplete
- **🎨 Modern UI**: Textual-based adaptive panels that respond to your workflow
- **🔍 Smart Search**: Semantic command search using FAISS vector database
- **🌐 Extensible**: Modular architecture with plugin support

### Who is AIShell For?

- **Database Administrators**: Multi-database management with AI-assisted queries
- **DevOps Engineers**: Automated system operations with safety checks
- **Developers**: AI-powered code editing and command assistance
- **System Administrators**: Natural language system commands with risk analysis
- **Power Users**: Enhanced shell with intelligent autocomplete and history

---

## Installation

### Prerequisites

Before installing AIShell, ensure you have:

- **Python 3.9 - 3.14** (we recommend 3.12+)
- **pip** (Python package manager)
- **Git** (for cloning the repository)
- **4GB RAM minimum** (8GB recommended for local LLM)
- **Linux, macOS, or Windows with WSL2**

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.9 | 3.12+ |
| RAM | 4GB | 8GB+ |
| Storage | 2GB | 5GB+ (for models) |
| CPU | 2 cores | 4+ cores |

### Step 1: Clone the Repository

```bash
# Clone AIShell repository
git clone https://github.com/dimensigon/aishell.git
cd aishell

# Verify you're in the correct directory
ls -la
# You should see: aishell.py, requirements.txt, src/, docs/, etc.
```

### Step 2: Create Virtual Environment

```bash
# Create a virtual environment (Python 3.9-3.14 supported)
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows (WSL2):
source venv/bin/activate

# Verify activation (you should see (venv) in your prompt)
which python
# Should output: /path/to/aishell/venv/bin/python
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This will install:
# - prompt-toolkit, textual, rich (UI frameworks)
# - oracledb, psycopg2-binary (database clients)
# - ollama, sentence-transformers (AI/ML)
# - faiss-cpu (vector database)
# - cryptography, keyring (security)
# - pytest (testing)
```

### Step 4: Verify Installation

```bash
# Check Python version
python --version
# Should output: Python 3.9.x or higher

# Verify key packages
python -c "import prompt_toolkit, textual, faiss, ollama; print('✅ All core packages installed')"

# List installed packages
pip list | grep -E "textual|faiss|ollama|oracledb"
```

### Step 5: Configure AIShell

```bash
# Copy default configuration
mkdir -p ~/.ai-shell
cp config/ai-shell-config.yaml ~/.agentic-aishell/config.yaml

# View configuration
cat ~/.agentic-aishell/config.yaml
```

---

## First Steps

### Starting AIShell

```bash
# Method 1: Using the standalone script (recommended)
./aishell.py

# Method 2: Using Python module
python -m src.main

# You should see a Matrix-style startup animation
# with system health checks
```

### Your First 5 Minutes

Once AIShell starts, you'll see the interactive prompt:

```
╔══════════════════════════════════════════════════════════╗
║              Welcome to AI-Shell v1.0                    ║
║  Intelligent CLI with AI-Powered Database Management     ║
╚══════════════════════════════════════════════════════════╝

AI$ >
```

**Try these commands:**

```bash
# 1. Regular shell commands work as expected
AI$ > ls -la
AI$ > pwd
AI$ > echo "Hello AIShell!"

# 2. Get help
AI$ > help

# 3. Check system status
AI$ > status

# 4. Natural language queries (prefix with #)
AI$ > #show current directory

# 5. Exit AIShell
AI$ > exit
```

---

## Core Concepts

### Architecture Overview

AIShell is built on a five-layer architecture:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: User Interface (CLI, REPL, Formatter)         │
├─────────────────────────────────────────────────────────┤
│  Layer 2: Command Processing (Parser, Classifier)       │
├─────────────────────────────────────────────────────────┤
│  Layer 3: AI Integration (LLM, MCP, Context)           │
├─────────────────────────────────────────────────────────┤
│  Layer 4: Providers (Ollama, Databases, Tools)         │
├─────────────────────────────────────────────────────────┤
│  Layer 5: Infrastructure (Memory, Config, Security)     │
└─────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. **AI Agents**
Autonomous agents that perform specific tasks:
- **Database Agents**: Query optimization, schema analysis
- **Safety Agents**: Risk assessment, command validation
- **Tool Agents**: File operations, system commands

#### 2. **LLM Integration**
Local and cloud AI models for intelligence:
- **Ollama**: Local LLM provider (recommended)
- **Intent Classification**: Understand what you want
- **Code Generation**: AI-assisted command creation

#### 3. **Vector Store**
FAISS-powered semantic search:
- **Smart Autocomplete**: Context-aware suggestions
- **Command History**: Semantic search through past commands
- **Database Objects**: Fast lookup of tables, columns

#### 4. **Secure Vault**
Encrypted credential management:
- **Master Password**: Protects all stored secrets
- **Auto-Redaction**: Hides sensitive data in logs
- **Multiple Backends**: Keyring, file-based, custom

#### 5. **Health Checks**
Continuous system monitoring:
- **LLM Availability**: Check model connectivity
- **Database Health**: Connection pool status
- **Memory Usage**: Performance monitoring

---

## Quick Wins

Here are 5 simple examples you can run immediately:

### 1. Natural Language File Search

```bash
AI$ > #find all python files modified in the last 7 days

# AIShell translates this to:
# find . -name "*.py" -mtime -7 -type f
```

### 2. Safe Command Execution

```bash
AI$ > rm -rf /important/directory

# AIShell shows risk analysis:
# ⚠️  HIGH RISK OPERATION
# Impact: Will delete 127 files (2.3 GB)
# Affected: Production logs, backups
# Suggestion: Use 'rm -i' for interactive deletion
# Confirm: Type "Understood and approved" to proceed
```

### 3. Multi-line Commands

```bash
AI$ > echo "Line 1" \
      echo "Line 2" \
      echo "Line 3"

# Supports backslash continuation like standard shells
```

### 4. Environment Variables

```bash
AI$ > export TEST_VAR="Hello AIShell"
AI$ > echo $TEST_VAR
Hello AIShell

# Variables persist within session
```

### 5. Command History Search

```bash
AI$ > history

# Or search history with natural language
AI$ > #show me database commands I ran yesterday
```

---

## UI Features (Phase 11)

AIShell includes modern UI components for enhanced command-line experience:

### Command Preview with Risk Visualization

Before executing risky commands, AIShell shows an intelligent preview:

```bash
AI$ > rm -rf /important/data

╔═══════════════════════════════════════════════════════════════╗
║                   COMMAND RISK PREVIEW                        ║
╠═══════════════════════════════════════════════════════════════╣
║ Command: rm -rf /important/data                               ║
║ Risk Level: ⚠️  HIGH (Score: 8.5/10)                          ║
║                                                                ║
║ Detected Risks:                                                ║
║  • Recursive deletion (127 files, 2.3 GB)                     ║
║  • No confirmation flag (-i)                                   ║
║  • Affects production data directory                          ║
║                                                                ║
║ Safer Alternatives:                                            ║
║  ✓ rm -ri /important/data  (interactive mode)                 ║
║  ✓ mv /important/data /backups/  (move instead)              ║
║                                                                ║
║ Type "Understood and approved" to proceed                     ║
╚═══════════════════════════════════════════════════════════════╝
```

### Smart Suggestions with Relevance Scores

Get context-aware suggestions as you type:

```bash
AI$ > SELECT * FROM users WHERE

Suggestions (relevance score):
  1. email = 'user@example.com'        [95%] - Most common pattern
  2. created_at > '2025-01-01'         [87%] - Recent queries
  3. status = 'active'                 [82%] - Frequent filter
  4. id IN (SELECT...)                 [65%] - Advanced pattern
```

### Adaptive Panel Layout

Dynamic panels adjust based on your workflow:

```
┌─────────────────────────────────────────────────────────────┐
│  Output Panel (50%)                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Command execution results displayed here            │   │
│  │ Auto-resizes based on content                       │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Module Status Panel (30%)                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • LLM: ✓ Connected (llama2:7b)                      │   │
│  │ • Database: ✓ PostgreSQL (production)               │   │
│  │ • Vault: ✓ 5 credentials loaded                     │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Prompt Panel (20%)                                         │
│  AI$ > █                                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent Workflows (Phase 12)

AIShell's intelligent agents automate complex workflows:

### Quick Agent Examples

**Automated Database Backup:**
```bash
AI$ > agent backup --database production --destination /backups --verify

╔═══════════════════════════════════════════════════════════════╗
║              Backup Agent Workflow                            ║
╠═══════════════════════════════════════════════════════════════╣
║ Step 1: Analyzing database size... ✓ (42.5 GB)               ║
║ Step 2: Checking backup space... ✓ (150 GB available)        ║
║ Step 3: Creating backup... ⧗ (15% complete)                  ║
║ Step 4: Verifying backup... [pending]                        ║
║ Step 5: Cleanup old backups... [pending]                     ║
╚═══════════════════════════════════════════════════════════════╝
```

**Database Migration Agent:**
```bash
AI$ > agent migrate --from mysql://old --to postgres://new --tables users,orders

Migration Agent Planning:
  1. Schema analysis (both databases)
  2. Data type mapping (MySQL → PostgreSQL)
  3. Safety backup creation
  4. Incremental data transfer
  5. Constraint verification
  6. Rollback preparation

Estimated time: 2 hours
Proceed? (yes/no):
```

**Performance Optimization Agent:**
```bash
AI$ > agent optimize --database production --target query_speed

Optimization Agent Analysis:
  • Identified 15 slow queries
  • Found 8 missing indexes
  • Detected 23 tables with stale statistics

Recommended Actions:
  1. Create index on users(email) - Est. improvement: 45%
  2. Update statistics for orders table - Est. improvement: 12%
  3. Rewrite query #3 to use JOIN - Est. improvement: 67%

Apply optimizations? (yes/no):
```

### Workflow Coordination Basics

Agents can coordinate complex multi-step workflows:

```python
# Agents automatically coordinate through shared state
# Example: Full maintenance workflow

AI$ > agent coordinator --workflow database_maintenance

Coordinator Agent Orchestrating:

  Phase 1: Analysis
    ├─ Performance Analysis Agent → Scanning queries...
    ├─ Health Check Agent → Database status: HEALTHY
    └─ Security Audit Agent → No vulnerabilities found

  Phase 2: Safety Preparations
    ├─ Backup Agent → Creating safety backup...
    └─ Validation Agent → Backup verified ✓

  Phase 3: Optimizations
    ├─ Optimizer Agent → Creating 5 indexes...
    ├─ Statistics Agent → Updating 23 tables...
    └─ Cleanup Agent → Removing old logs...

  Phase 4: Verification
    └─ Validation Agent → Performance improved 34% ✓

Workflow completed successfully in 12 minutes.
```

---

## Project Structure

Understanding the codebase layout:

```
AIShell/
├── aishell.py                    # Main entry point (run this!)
├── requirements.txt              # Python dependencies
├── config/
│   └── ai-shell-config.yaml     # Default configuration
├── src/                         # Source code (package root)
│   ├── main.py                  # Application initialization
│   ├── core/                    # Core engine
│   │   ├── ai_shell.py         # Shell core logic
│   │   ├── config.py           # Configuration manager
│   │   └── event_bus.py        # Event system
│   ├── agents/                  # AI agents
│   │   ├── base.py             # Base agent class
│   │   ├── database/           # Database agents
│   │   ├── safety/             # Safety check agents
│   │   └── tools/              # Tool execution agents
│   ├── llm/                     # LLM integration
│   │   ├── manager.py          # LLM manager
│   │   └── providers/          # Ollama, custom providers
│   ├── mcp_clients/             # Database clients
│   │   ├── manager.py          # Connection manager
│   │   ├── oracle_thin.py      # Oracle client
│   │   └── postgresql_pure.py  # PostgreSQL client
│   ├── database/                # Database module
│   ├── security/                # Vault and security
│   │   └── vault.py            # Secure credential storage
│   ├── vector/                  # Vector database
│   │   └── autocomplete.py     # FAISS autocomplete
│   ├── ui/                      # User interface
│   └── performance/             # Performance optimization
├── tests/                       # Test suite
│   ├── test_agents.py
│   ├── test_database.py
│   └── integration/
├── docs/                        # Documentation
│   ├── architecture/           # Architecture docs
│   └── guides/                 # User guides
├── tutorials/                   # Tutorial series
│   └── 00-getting-started.md   # This file!
└── examples/                    # Example code
    ├── configurations/         # Config examples
    └── scripts/                # Automation scripts
```

### Key Directories

- **`src/`**: All source code lives here (package root)
- **`src/agents/`**: AI agent implementations
- **`src/llm/`**: LLM provider integrations
- **`src/mcp_clients/`**: Database client implementations
- **`config/`**: Configuration files
- **`tests/`**: Unit and integration tests
- **`docs/`**: Technical documentation
- **`tutorials/`**: Step-by-step guides

---

## Configuration

### Main Configuration File

AIShell uses YAML for configuration. The main file is `~/.agentic-aishell/config.yaml`:

```yaml
# System Settings
system:
  startup_animation: true        # Show Matrix-style startup
  matrix_style: enhanced         # Animation style
  log_level: INFO               # DEBUG, INFO, WARNING, ERROR

# LLM Configuration
llm:
  models:
    intent: "llama2:7b"         # Intent classification model
    completion: "codellama:13b"  # Code completion model
    anonymizer: "mistral:7b"    # Data anonymization model
  ollama_host: "localhost:11434" # Ollama API endpoint
  model_path: "/data0/models"    # Local model storage
  timeout: 30                    # Request timeout (seconds)
  max_retries: 3                 # Retry failed requests

# MCP Database Clients
mcp:
  oracle:
    thin_mode: true              # No Oracle client required
    connection_pool_size: 5
    connection_timeout: 10
    query_timeout: 30
  postgresql:
    connection_pool_size: 5
    connection_timeout: 10
    query_timeout: 30

# UI Settings
ui:
  framework: "textual"           # UI framework
  theme: "cyberpunk"             # Color theme
  panel_priority:
    typing: "prompt"             # Focus prompt when typing
    idle: "balanced"             # Balanced view when idle

# Security
security:
  vault_backend: "keyring"       # keyring, file, custom
  auto_redaction: true           # Redact sensitive data
  sensitive_commands_require_confirmation: true
  password_complexity:
    min_length: 12
    require_special: true
    require_numbers: true

# Performance
performance:
  async_workers: 4               # Background workers
  cache_size: 1000               # Query cache size
  vector_db_dimension: 384       # FAISS dimensions
  max_query_cache_ttl: 300      # Cache TTL (seconds)

# Modules
modules:
  os_base:
    enabled: true
    default_shell: "/bin/bash"
  ai_helper:
    enabled: true
    default_provider: "ollama"
  vault:
    enabled: true
    auto_lock_timeout: 900       # 15 minutes
  database:
    enabled: true
    auto_commit: false
  web_interface:
    enabled: false
    port: 5000
```

### Configuration Locations

AIShell searches for configuration in this order:

1. `~/.agentic-aishell/config.yaml` (user config)
2. `./config/ai-shell-config.yaml` (project default)
3. Environment variable: `AISHELL_CONFIG`

### Customizing Your Config

```bash
# Copy default config to user directory
mkdir -p ~/.ai-shell
cp config/ai-shell-config.yaml ~/.agentic-aishell/config.yaml

# Edit with your favorite editor
nano ~/.agentic-aishell/config.yaml

# Or use AIShell's config command
AI$ > config set llm.models.intent "llama3:8b"
AI$ > config get llm.models.intent
```

---

## Running Your First Agent

### Installing Ollama (Optional but Recommended)

For the best experience, install Ollama for local LLM support:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version

# Pull recommended models
ollama pull llama2:7b          # Intent classification (1.4GB)
ollama pull codellama:13b      # Code completion (7.3GB)
ollama pull mistral:7b         # Data anonymization (4.1GB)

# Test Ollama
ollama run llama2:7b "Hello, how are you?"

# Check Ollama is running
curl http://localhost:11434/api/tags
```

### Example: Database Backup Agent

Let's run a simple database backup agent to see AIShell in action.

**Step 1: Start AIShell**

```bash
./aishell.py
```

**Step 2: Configure Database Credentials**

```bash
AI$ > vault add test_db --type database
# Follow prompts to enter:
# - Username: testuser
# - Password: ****
# - Host: localhost
# - Port: 5432
# - Database: testdb

# Verify stored credentials
AI$ > vault list
```

**Step 3: Run Database Health Check**

```bash
# Check database connectivity
AI$ > db connect test_db

# Run a simple query
AI$ > SELECT version();

# Or use natural language
AI$ > #show me all tables
```

**Step 4: Agent-Powered Tasks**

```bash
# AI-assisted query optimization
AI$ > #find all tables with more than 1 million rows

# AIShell agent will:
# 1. Analyze database schema
# 2. Generate optimized query
# 3. Execute with safety checks
# 4. Format results beautifully
```

**Expected Output:**

```
╔═══════════════════════════════════════════════════════════╗
║  Database Agent Analysis                                  ║
╠═══════════════════════════════════════════════════════════╣
║  Task: Find large tables                                  ║
║  Analysis: Scanning 47 tables in schema                   ║
║  Generated Query:                                          ║
║    SELECT table_name, row_count                           ║
║    FROM information_schema.tables                         ║
║    WHERE row_count > 1000000                              ║
║  Safety Check: ✅ Read-only operation (LOW RISK)         ║
╚═══════════════════════════════════════════════════════════╝

┌──────────────┬────────────┐
│ Table Name   │ Row Count  │
├──────────────┼────────────┤
│ users        │ 2,451,893  │
│ transactions │ 5,123,456  │
│ logs         │ 8,234,567  │
└──────────────┴────────────┘

Execution time: 1.23s
```

---

## Next Steps

Congratulations! You've successfully installed and configured AIShell. Here's where to go next:

### Tutorial Series

1. **✅ 00-getting-started.md** (You are here)
2. **01-ai-powered-commands.md** - Natural language command processing
3. **[02-building-custom-agents.md](./02-building-custom-agents.md)** - Building agents with Phase 12 features
4. **03-security-vault.md** - Secure credential management
5. **04-ui-customization.md** - Customizing Phase 11 UI components
6. **[05-complete-workflow-example.md](./05-complete-workflow-example.md)** - Full workflow with UI and agents
7. **[06-quick-reference.md](./06-quick-reference.md)** - Quick lookup for all features

### Documentation

- **[Architecture Guide](../docs/architecture/ARCHITECTURE_SUMMARY.md)** - System design deep-dive
- **[Module Specifications](../docs/architecture/MODULE_SPECIFICATIONS.md)** - Component details
- **[API Reference](../docs/api/)** - Developer documentation

### Community

- **GitHub Issues**: https://github.com/dimensigon/aishell/issues
- **Discussions**: https://github.com/dimensigon/aishell/discussions
- **Documentation**: https://ai-shell.readthedocs.io

---

## Troubleshooting

### Common Installation Issues

#### **Issue 1: Python Version Mismatch**

```bash
# Error: Python 3.8 or lower detected
python --version

# Solution: Install Python 3.9+
# Ubuntu/Debian:
sudo apt update
sudo apt install python3.12 python3.12-venv

# macOS (with Homebrew):
brew install python@3.12
```

#### **Issue 2: FAISS Installation Fails**

```bash
# Error: Could not build wheels for faiss-cpu

# Solution 1: Use pre-built wheel
pip install faiss-cpu==1.12.0 --prefer-binary

# Solution 2: Install system dependencies
# Ubuntu/Debian:
sudo apt install build-essential python3-dev

# macOS:
xcode-select --install
```

#### **Issue 3: Ollama Connection Failed**

```bash
# Error: Could not connect to Ollama at localhost:11434

# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start Ollama
systemctl start ollama  # Linux
# Or run in terminal: ollama serve

# Verify it's working
ollama list
```

#### **Issue 4: Permission Denied on aishell.py**

```bash
# Error: Permission denied: ./aishell.py

# Solution: Make script executable
chmod +x aishell.py

# Or run with python
python aishell.py
```

#### **Issue 5: Virtual Environment Not Activating**

```bash
# Symptom: (venv) doesn't appear in prompt

# Solution 1: Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Solution 2: Use full path
source /path/to/aishell/venv/bin/activate
```

### Runtime Issues

#### **Issue 6: Database Connection Timeout**

```bash
# Error: Connection timeout for database 'test_db'

# Check credentials
AI$ > vault get test_db

# Verify database is accessible
ping <database-host>
telnet <database-host> <port>

# Increase timeout in config
AI$ > config set mcp.postgresql.connection_timeout 30
```

#### **Issue 7: High Memory Usage**

```bash
# Symptom: AIShell using >4GB RAM

# Solution: Reduce cache size and workers
AI$ > config set performance.cache_size 500
AI$ > config set performance.async_workers 2

# Or use smaller models
AI$ > config set llm.models.intent "llama2:3b"
```

#### **Issue 8: Slow Autocomplete**

```bash
# Symptom: Tab completion takes >2 seconds

# Solution: Rebuild vector index
AI$ > index rebuild

# Or reduce vector dimension
AI$ > config set performance.vector_db_dimension 256
```

### Getting Help

If you encounter issues not listed here:

1. **Check Logs**: `~/.agentic-aishell/logs/aishell.log`
2. **Enable Debug Mode**: `AI$ > config set system.log_level DEBUG`
3. **Run Diagnostics**: `AI$ > diagnose`
4. **GitHub Issues**: Search existing issues or create new one
5. **Community Discord**: Join our support channel

### Diagnostic Commands

```bash
# System health check
AI$ > health

# Show configuration
AI$ > config show

# Check LLM connectivity
AI$ > llm test

# Database connectivity test
AI$ > db test-all

# Vector store status
AI$ > index status

# Memory usage
AI$ > stats memory
```

---

## Quick Reference Card

### Essential Commands

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show help | `AI$ > help` |
| `status` | System status | `AI$ > status` |
| `config` | Configuration | `AI$ > config get llm.models.intent` |
| `vault` | Credentials | `AI$ > vault add prod_db --type database` |
| `db` | Database ops | `AI$ > db connect prod_db` |
| `history` | Command history | `AI$ > history --search "SELECT"` |
| `exit` | Exit AIShell | `AI$ > exit` |

### Natural Language Prefix

Use `#` for natural language commands:

```bash
AI$ > #find large files in current directory
AI$ > #show me database tables
AI$ > #compress all logs from last week
```

### Special Key Bindings

| Key | Action |
|-----|--------|
| `Tab` | Autocomplete |
| `Ctrl+C` | Cancel command |
| `Ctrl+D` | Exit AIShell |
| `Ctrl+R` | Reverse history search |
| `Ctrl+A` | Move to start of line |
| `Ctrl+E` | Move to end of line |
| `Up/Down` | Navigate history |

### Safety Levels

| Level | Confirmation | Examples |
|-------|--------------|----------|
| **LOW** | Auto-execute | `SELECT`, `ls`, `cat` |
| **MEDIUM** | Press key | `UPDATE`, `INSERT`, `mkdir` |
| **HIGH** | Type phrase | `DROP`, `DELETE`, `rm -rf` |

### Configuration Quick Changes

```bash
# Change LLM model
AI$ > config set llm.models.intent "llama3:8b"

# Enable debug logging
AI$ > config set system.log_level DEBUG

# Increase timeout
AI$ > config set llm.timeout 60

# Reload configuration
AI$ > config reload
```

### Vault Quick Reference

```bash
# Add credential
AI$ > vault add <name> --type <database|api|ssh|custom>

# List all
AI$ > vault list

# Get credential
AI$ > vault get <name>

# Delete credential
AI$ > vault delete <name>

# Use in command
AI$ > export DB_PASS=$vault.prod_db.password
```

### Database Quick Commands

```bash
# Connect
AI$ > db connect <vault_name>

# List connections
AI$ > db list

# Switch database
AI$ > db use <connection_name>

# Disconnect
AI$ > db disconnect

# Execute query
AI$ > SELECT * FROM users LIMIT 10;
```

---

## Welcome Aboard! 🎉

You're now ready to explore the power of AIShell! Remember:

- **Start Simple**: Master basic commands before advanced features
- **Experiment**: AIShell has safety checks to prevent accidents
- **Explore Agents**: AI agents can automate complex workflows
- **Customize**: Tailor configuration to your needs
- **Contribute**: Share your experiences and improvements

### What Makes AIShell Special?

```
Traditional Shell              AIShell
─────────────────            ──────────────
Manual commands       →      Natural language
Trial and error       →      AI suggestions
Memory required       →      Semantic search
Credential chaos      →      Secure vault
One-task-at-a-time   →      Parallel agents
Risky operations      →      Safety analysis
```

**Happy Shelling!** 🚀

---

**Document Information**
- **Version**: 1.0.0
- **Last Updated**: 2025-10-05
- **Tutorial Series**: Part 1 of 6
- **Next**: [01-ai-powered-commands.md](./01-ai-powered-commands.md)
- **Feedback**: [GitHub Issues](https://github.com/dimensigon/aishell/issues)
