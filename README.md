# AI-Shell Documentation

## Overview

AI-Shell (AI$) is an intelligent command-line interface that combines traditional shell functionality with AI-powered assistance, database management, and multi-threaded asynchronous processing. Built with Python's `prompt-toolkit` and modern async architecture, it provides a context-aware terminal experience with modular extensibility.

### Key Features

- **🤖 AI-Powered Interface**: Local and cloud LLM integration for intent analysis and command suggestions
- **📊 Multi-Database Support**: MCP-based clients for Oracle, PostgreSQL, and extensible architecture for additional databases
- **🔐 Secure Credential Management**: Encrypted vault system with automatic redaction
- **⚡ Asynchronous Processing**: Non-blocking background enrichment and multi-threaded execution
- **🎨 Dynamic UI**: Adaptive panel sizing based on content and user activity
- **🔍 Intelligent Auto-completion**: Vector-based semantic search for commands and database objects
- **📝 Enhanced History**: Queryable command history with exit codes and context
- **🌐 Web Interface**: Optional Flask-based web UI for graphical interaction

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/dimensigon/aishell.git
cd ai-shell

# Create virtual environment (Python 3.11+ required)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
ai-shell --init
```

### First Run

```bash
# Start AI-Shell
ai-shell

# You'll see a Matrix-style startup animation
# checking AI model availability and system health
```

### Basic Usage

```bash
# Regular shell commands work as expected
AI$ > ls -la
AI$ > cd /home/user/projects

# Natural language queries (start with #)
AI$ > #how do I find large files?

# AI-assisted command analysis (Ctrl+A)
AI$ > rm -rf /important/directory  # Press Ctrl+A for impact analysis

# Access vault credentials
AI$ > export DB_PASSWORD=$vault.prod_db_password

# Multi-line commands (use backslash)
AI$ > SELECT * \
      FROM users \
      WHERE status = 'active'
```

## Architecture

AI-Shell is built on a modular architecture with the following core components:

### Core Components

```
ai-shell/
├── core/                    # Core application logic
│   ├── ui_manager.py       # Textual-based UI management
│   ├── llm_manager.py      # Local/cloud LLM integration
│   ├── vector_store.py     # FAISS-based semantic search
│   └── event_bus.py        # Asynchronous event processing
│
├── modules/                 # Extensible modules
│   ├── os_base/            # File system and OS operations
│   ├── ai_helper/          # AI query and agentic tools
│   ├── vault/              # Credential management
│   ├── database/           # Database core engine
│   └── web_interface/      # Flask web UI
│
├── mcp_clients/            # Model Context Protocol clients
│   ├── oracle_thin.py      # Oracle thin client (no Oracle client required)
│   ├── postgresql_pure.py  # Pure Python PostgreSQL client
│   └── base.py             # Abstract MCP client protocol
│
└── ui/                     # UI components
    ├── panels.py           # Dynamic panel management
    ├── completers.py       # Intelligent auto-completion
    └── formatters.py       # Output formatting
```

### Data Flow

```
User Input → Intent Analysis (Local LLM) → Module Router
                    ↓
         Background Enrichment (Async)
                    ↓
         Module Panel Updates (Non-blocking)
                    ↓
         Command Execution → Output Formatting
```

## Configuration

### Main Configuration File

Create or edit `~/.ai-shell/config.yaml`:

```yaml
# System Configuration
system:
  startup_animation: true
  matrix_style: enhanced
  theme: cyberpunk

# LLM Configuration
llm:
  provider: ollama  # ollama, openai, anthropic, deepseek
  models:
    intent: "llama2:7b"
    completion: "codellama:13b"
    anonymizer: "mistral:7b"
  ollama_host: "localhost:11434"
  fallback_provider: "openai"  # Fallback if local LLM unavailable

# MCP Clients
mcp:
  oracle:
    thin_mode: true
    connection_pool_size: 5
    timeout: 30
  postgresql:
    connection_pool_size: 5
    timeout: 30

# UI Settings
ui:
  framework: textual
  panel_weights:
    output: 0.5
    module: 0.3
    prompt: 0.2
  typing_priority: prompt  # Focus prompt when typing
  idle_priority: balanced  # Balanced view when idle

# Security
security:
  vault_backend: keyring  # keyring, file, custom
  auto_redaction: true
  require_confirmation_for:
    - rm
    - DROP
    - DELETE
    - TRUNCATE
  risk_levels:
    high: confirm_text
    medium: confirm_key
    low: auto_execute

# Performance
performance:
  async_workers: 4
  cache_size: 1000
  vector_db_dimension: 384
  lazy_loading: true
```

## Module System

AI-Shell uses a modular architecture for extensibility. Each module can define:

- **Components (submodules)**: Specialized functionality within a module
- **UI Elements**: Custom panel displays and formatters
- **Event Handlers**: Respond to system events
- **Tools**: Agentic capabilities for AI integration

### Core Modules

#### 1. OS-Base Module

File system navigation, environment management, and command execution.

**Components:**
- Navigator: Natural language file system navigation
- Environment Manager: Visual environment variable editor
- File Editor: AI-assisted code editing
- Command Executor: Enhanced command execution with AI analysis
- History Manager: Queryable command history
- Session Spawner: Multi-user session management

[Read more →](./guides/os-base-module.md)

#### 2. AI-Helper Module

AI query processing and agentic tool execution.

**Components:**
- Synchronous Query: Real-time AI responses
- Asynchronous Query: Background AI processing
- Failover Query: Multi-provider fallback
- Agent: Multi-step task execution
- Tools: File operations, command execution, database queries

[Read more →](./guides/ai-helper-module.md)

#### 3. Vault Module

Secure credential storage with automatic redaction.

**Components:**
- Secret Manager: Encrypted credential storage
- Types: Standard, Database, User-defined schemas
- Auto-redaction: Pattern-based sensitive data removal

[Read more →](./guides/vault-module.md)

#### 4. Database Module

Unified interface for multiple database engines.

**Components:**
- Connection Manager: Multi-database connection pooling
- Risk Analyzer: SQL impact analysis
- Query Optimizer: Database-specific optimization
- NLP Processor: Natural language to SQL
- SQL History: Enhanced query tracking
- Debugging: Logging, tracing, session monitoring

[Read more →](./guides/database-module.md)

## Getting Started

### 1. Install Local LLM (Recommended)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download models
ollama pull llama2:7b
ollama pull codellama:13b
ollama pull mistral:7b
```

### 2. Configure Database Connections

```bash
# Start AI-Shell and add database credentials
AI$ > vault add prod_oracle --type database
Enter username: admin
Enter password: ****
Enter host: oracle-prod.example.com
Enter port: 1521
Enter service: ORCL

# Test connection
AI$ > db connect prod_oracle
AI$ > SELECT * FROM user_tables;
```

### 3. Explore AI Features

```bash
# Ask AI for help
AI$ > #show me all failed login attempts in the last hour

# Get command explanation
AI$ > ps aux | grep nginx  # Press Ctrl+A

# AI-assisted file editing
AI$ > edit app.py
# Inside editor, type: #ai add error handling for database connections
```

## Advanced Features

### Vector-Based Auto-completion

AI-Shell uses FAISS for semantic similarity search, providing intelligent auto-completion:

```bash
# Start typing database objects
AI$ > SELECT * FROM user_  # Tab completion shows relevant tables

# Context-aware suggestions
AI$ > #find processes using port  # AI suggests: lsof -i :PORT
```

### Asynchronous Panel Enrichment

The module panel updates in real-time without blocking input:

```bash
# While you type, the module panel shows:
# - Current directory info
# - Related commands
# - AI-suggested next steps
# - Database connection status
# - Risk analysis results
```

### Command Risk Analysis

High-risk commands trigger automatic AI analysis:

```bash
AI$ > rm -rf /var/log/*

# Module panel shows:
# ⚠️  HIGH RISK OPERATION
# Affected files: 127 log files (2.3 GB)
# Impact: System logging will be disrupted
# Suggestion: Use logrotate instead
# Confirm with: "Understood and approved"
```

### Agentic Workflows

AI can execute multi-step tasks:

```bash
AI$ > #ai create a backup of the database and compress it

# AI Agent executes:
# 1. Connects to database
# 2. Exports schema and data
# 3. Compresses with gzip
# 4. Moves to backup directory
# 5. Verifies integrity
# Each step shown with approval prompts
```

## Integration Guides

- [MCP Integration](./guides/mcp-integration.md) - Model Context Protocol setup
- [LLM Provider Setup](./guides/llm-providers.md) - Configure AI providers
- [Database Setup](./guides/database-setup.md) - Add database engines
- [Custom Commands](./guides/custom-commands.md) - Extend with custom commands
- [Web Interface](./guides/web-interface.md) - Enable web UI

## API Reference

- [Core API](./api/core.md) - Core application interfaces
- [Module API](./api/modules.md) - Module development
- [MCP Client API](./api/mcp-clients.md) - Database client development
- [UI Components](./api/ui-components.md) - Custom UI elements

## Examples

- [Configuration Examples](../examples/configurations/) - Sample configs
- [Custom Module Example](../examples/custom-module/) - Build your own module
- [Integration Scripts](../examples/scripts/) - Automation scripts

## Troubleshooting

### Common Issues

**LLM Connection Failed**
```bash
# Check Ollama is running
systemctl status ollama

# Test connection
curl http://localhost:11434/api/tags
```

**Database Connection Issues**
```bash
# Oracle: Ensure thin mode is enabled in config
mcp:
  oracle:
    thin_mode: true  # No Oracle client required

# PostgreSQL: Check credentials
AI$ > vault get prod_postgres
```

**Performance Issues**
```bash
# Increase async workers
performance:
  async_workers: 8
  cache_size: 2000
```

[More troubleshooting →](./guides/troubleshooting.md)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

AI-Shell is released under the MIT License. See [LICENSE](../LICENSE) for details.

## Support

- Documentation: https://ai-shell.readthedocs.io
- Issues: https://github.com/dimensigon/aishell/issues
- Discussions: https://github.com/dimensigon/aishell/discussions

---

**Version**: 1.0.0
**Last Updated**: 2025-10-03
**Authors**: AI-Shell Development Team
