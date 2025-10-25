# Agentic AI-Shell Documentation

![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)
![Test Coverage](https://img.shields.io/badge/coverage-22.60%25-yellow)
![Tests](https://img.shields.io/badge/tests-3396%20passing-brightgreen)
![Test Files](https://img.shields.io/badge/test%20files-134-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![FAISS](https://img.shields.io/badge/FAISS-1.12.0-orange)

## 🚀 What's New

### Latest Updates (v2.0.0)
- **🎭 Mock Mode**: Test the UX without backend services using `--mock` flag
- **🧠 Enhanced LLM Integration**: Auto-discovery, intelligent routing, semantic caching
- **⚡ 10x Performance**: Async improvements with priority queues and connection pooling
- **🔌 Advanced MCP Support**: Health monitoring, tool discovery, connection pooling
- **🛡️ Security Hardening**: SQL injection protection, input validation, safe command execution
- **🎮 Multi-Modal Shell**: Natural language, command, hybrid, assistant, and mock modes

## Overview

Agentic AI-Shell (AI$) is an intelligent command-line interface that represents a paradigm shift in CLI-based system administration. It combines traditional shell functionality with agentic AI-powered assistance, Model Context Protocol (MCP) clients, local LLMs, and asynchronous processing to create an intelligent, context-aware terminal experience with modular extensibility and autonomous agent capabilities.

### Key Features

- **🤖 AI-Powered Interface**: Local and cloud LLM integration for intent analysis and command suggestions
- **📊 Multi-Database Support**: MCP-based clients for Oracle, PostgreSQL, and extensible architecture for additional databases
- **🔐 Secure Credential Management**: Encrypted vault system with automatic redaction
- **⚡ Asynchronous Processing**: Non-blocking background enrichment and multi-threaded execution
- **🎨 Dynamic UI**: Adaptive panel sizing based on content and user activity
- **🔍 Intelligent Auto-completion**: Vector-based semantic search for commands and database objects
- **📝 Enhanced History**: Queryable command history with exit codes and context
- **🌐 Web Interface**: Optional Flask-based web UI for graphical interaction
- **🏥 Health Check System**: Comprehensive async health monitoring with parallel checks
- **🤖 Custom AI Agents**: Build autonomous agents with multi-step workflows
- **🛠️ Tool Registry**: Centralized tool management with safety validation
- **🔒 Safety & Approvals**: Multi-layer protection with risk assessment and approval workflows

## 📚 Tutorials

New to AI-Shell? Start with our comprehensive tutorial series:

1. **[Health Check System](./tutorials/01-health-checks-tutorial.md)** - Master async health monitoring (30 min)
2. **[Building Custom Agents](./tutorials/02-building-custom-agents.md)** - Create autonomous AI agents (60 min)
3. **[Tool Registry System](./tutorials/03-tool-registry-guide.md)** - Manage and validate agent tools (45 min)
4. **[Safety & Approvals](./tutorials/04-safety-and-approvals.md)** - Implement multi-layer protection (40 min)

📖 **[View Complete Tutorial Index →](./tutorials/README.md)**

## Quick Start

**New users**: Follow the **[Health Check Tutorial](./tutorials/01-health-checks-tutorial.md)** for a guided introduction!

### Installation

```bash
# Clone the repository
git clone https://github.com/dimensigon/aishell.git
cd AIShell

# Create virtual environment (Python 3.9-3.14 supported)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
agentic-aishell --init
```

### Python Version Support

- ✅ Python 3.9
- ✅ Python 3.10
- ✅ Python 3.11
- ✅ Python 3.12 (NEW - Full FAISS support)
- ✅ Python 3.13 (NEW)
- ✅ Python 3.14 (NEW)

### First Run

```bash
# Start AI-Shell
agentic-aishell

# You'll see a Matrix-style startup animation
# checking AI model availability and system health
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run specific test category
python -m pytest tests/ -m unit          # Unit tests only
python -m pytest tests/ -m integration   # Integration tests only

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**Current Test Statistics**:
- Total Tests: 3,396 test cases
- Test Files: 134 test modules
- Overall Coverage: 22.60%
- Lines Covered: 9,496 out of 42,025

For detailed testing information, see:
- [Testing Guide](docs/TESTING_GUIDE.md) - Comprehensive testing documentation
- [CI/CD Integration](docs/CI_CD_INTEGRATION.md) - CI/CD setup and configuration
- [Contributing Guide](CONTRIBUTING.md) - Testing requirements for PRs

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
AIShell/
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

Create or edit `~/.agentic-aishell/config.yaml`:

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

## Phase 11 & 12 Features

### 🏥 Advanced Health Check System (Phase 11)

AI-Shell now includes a comprehensive health monitoring system:

- **Parallel Execution**: All checks run concurrently for speed
- **Timeout Protection**: No single check can hang the system (< 2s)
- **Async-First Design**: Non-blocking for high performance
- **Built-in Checks**: LLM, Database, Filesystem, and Memory checks
- **Custom Checks**: Easy extensibility for application-specific needs

```python
from core.health_check_manager import HealthCheckManager

# Run all checks in parallel
results = await health_manager.run_all_checks()
# ✅ LLM: healthy (0.45s)
# ✅ Database: healthy (0.23s)
# ✅ Memory: healthy (0.12s)
```

📖 **[Health Check Tutorial →](./tutorials/01-health-checks-tutorial.md)**

### 🤖 Custom AI Agents (Phase 11)

Build autonomous agents with multi-step workflows:

- **Intelligent Planning**: LLM-powered task decomposition
- **Tool-Based Execution**: Use validated tools from registry
- **Safety Controls**: Multi-layer approval workflows
- **State Persistence**: Checkpoint and recovery for long tasks
- **Error Recovery**: Automatic retry and rollback capabilities

```python
class DatabaseMaintenanceAgent(BaseAgent):
    async def plan(self, task: str) -> List[ExecutionStep]:
        # Agent decomposes task into steps
        return steps

    async def execute_step(self, step: ExecutionStep) -> StepResult:
        # Execute with safety validation
        return result
```

📖 **[Agent Building Tutorial →](./tutorials/02-building-custom-agents.md)**

### 🛠️ Tool Registry System (Phase 11)

Centralized tool management with validation:

- **Parameter Validation**: JSON Schema-based validation
- **Risk Assessment**: Five-level risk classification
- **Capability Matching**: Ensure agents have required capabilities
- **LLM Integration**: Generate tool descriptions for AI
- **Audit Trails**: Complete execution logging
- **Rate Limiting**: Prevent resource exhaustion

```python
@tool_registry.register(
    category="database",
    risk_level=RiskLevel.HIGH,
    capabilities=["database_write"]
)
async def backup_database(target_db: str, backup_path: str):
    # Tool automatically validated and logged
    pass
```

📖 **[Tool Registry Guide →](./tutorials/03-tool-registry-guide.md)**

### 🔒 Safety & Approval System (Phase 12)

Multi-layer protection for autonomous operations:

- **Risk Assessment**: Automatic operation risk evaluation
- **Approval Workflows**: Human-in-the-loop for critical operations
- **SQL Analysis**: Deep inspection of database queries
- **Audit Logging**: Complete trail of all decisions
- **Safety Constraints**: Configurable rules and policies

```python
# High-risk operations require approval
result = await safety_controller.validate_and_execute(
    operation="DROP TABLE users",
    risk_level=RiskLevel.CRITICAL,
    approval_required=True
)
# 🔒 CRITICAL operation requires approval
# Type 'I approve' to continue: _
```

📖 **[Safety Tutorial →](./tutorials/04-safety-and-approvals.md)**

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

- Documentation: https://agentic-aishell.readthedocs.io
- Issues: https://github.com/dimensigon/aishell/issues
- Discussions: https://github.com/dimensigon/aishell/discussions

---

**Version**: 1.0.0
**Last Updated**: 2025-10-03
**Authors**: AI-Shell Development Team

## 📦 PyPI Installation

Install the latest stable version from PyPI:

```bash
pip install agentic-aishell
```

Or install with all optional dependencies:

```bash
pip install agentic-aishell[all]
```

Development installation:

```bash
pip install agentic-aishell[dev]
```
