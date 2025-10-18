# Agentic AI-Shell Documentation

![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)
![Test Coverage](https://img.shields.io/badge/coverage-22.60%25-yellow)
![Tests](https://img.shields.io/badge/tests-3396%20passing-brightgreen)
![Test Files](https://img.shields.io/badge/test%20files-134-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![FAISS](https://img.shields.io/badge/FAISS-1.12.0-orange)
![MCP](https://img.shields.io/badge/MCP-Discovery-purple)
![LLM](https://img.shields.io/badge/LLM-Integrated-green)

## Overview

Agentic AI-Shell (AI$) is a next-generation intelligent command-line interface that seamlessly integrates AI capabilities, MCP (Model Context Protocol) server discovery, and autonomous agent execution. With built-in LLM integration and automatic MCP tool discovery, AI-Shell transforms your terminal into an intelligent assistant capable of understanding natural language, executing complex tasks in parallel, and automatically leveraging available tools and services on your network.

### Key Features

#### 🚀 NEW in v2.0: Consolidated AI + MCP Integration
- **🔍 MCP Auto-Discovery**: Automatically discovers and connects to MCP servers on your network
- **🤖 Built-in AI Commands**: Natural language interface with `ai`, `explain`, `suggest` commands
- **🔗 Seamless Integration**: Agents automatically use discovered MCP tools without configuration
- **⚡ Parallel Agent Execution**: Execute complex tasks with multiple agents working concurrently
- **🎯 Context-Aware AI**: LLM queries enriched with MCP resources and command history

#### 🧠 NEW: Cognitive Features (Self-Learning & Autonomous)
- **💾 Cognitive Shell Memory (CogShell)**: Semantic command search with FAISS vectors, pattern recognition, and learning from feedback
- **🚨 Anomaly Detection & Self-Healing**: Statistical anomaly detection (Z-score), auto-remediation with rate limiting, rollback support
- **🤖 Autonomous DevOps Agent (ADA)**: Infrastructure optimization, predictive scaling, cost reduction, self-learning from outcomes

#### Core Capabilities
- **📊 Multi-Database Support**: MCP-based clients for Oracle, PostgreSQL, and extensible architecture
- **🔐 Secure Credential Management**: Encrypted vault system with automatic redaction
- **🎨 Dynamic UI**: Adaptive panel sizing based on content and user activity
- **🔍 Intelligent Auto-completion**: Vector-based semantic search with FAISS
- **📝 Enhanced History**: Queryable command history with exit codes and context
- **🌐 Web Interface**: Optional Flask-based web UI for graphical interaction
- **🏥 Health Check System**: Comprehensive async health monitoring with parallel checks
- **🛠️ Tool Registry**: Centralized tool management with 5-level risk assessment
- **🔒 Safety & Approvals**: Multi-layer protection with automatic risk validation

## 📚 Tutorials

New to AI-Shell? Start with our comprehensive tutorial series:

1. **[Health Check System](./tutorials/01-health-checks-tutorial.md)** - Master async health monitoring (30 min)
2. **[Building Custom Agents](./tutorials/02-building-custom-agents.md)** - Create autonomous AI agents (60 min)
3. **[Tool Registry System](./tutorials/03-tool-registry-guide.md)** - Manage and validate agent tools (45 min)
4. **[Safety & Approvals](./tutorials/04-safety-and-approvals.md)** - Implement multi-layer protection (40 min)

📖 **[View Complete Tutorial Index →](./tutorials/README.md)**

## Quick Start

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

# Initialize configuration with AI and MCP enabled
agentic-aishell --init --enable-ai --enable-mcp
```

### 🚀 Quick Examples

#### 1. AI-Powered Natural Language Commands
```bash
# Ask AI for help with any task
AI$ > ai how do I find all Python files modified in the last week?

# AI responds with the command and explanation:
# You can use the find command: find . -name "*.py" -mtime -7
# This searches for Python files (.py) modified within 7 days

# Get explanations for previous commands
AI$ > ls -la | grep config
AI$ > explain
# The command listed all files and filtered for ones containing "config"...

# Get command suggestions based on intent
AI$ > suggest optimize database performance
# 1. ANALYZE TABLE to update statistics
# 2. CREATE INDEX on frequently queried columns
# 3. VACUUM FULL to reclaim space...
```

#### 2. MCP Server Discovery and Management
```bash
# Scan for MCP servers on your network
AI$ > mcp scan
Found 3 MCP servers:
  - GitHub Assistant (websocket://192.168.1.10:3000)
    Tools: create_pr, review_code, manage_issues
  - Database Manager (stdio://localhost:3749)
    Tools: backup_db, optimize_query, analyze_schema
  - Cloud Deployer (websocket://192.168.1.15:8080)
    Tools: deploy_app, scale_service, monitor_health

# Check connection status
AI$ > mcp status
MCP Discovery Status:
  Total Servers: 3
  Connected: 2
  Available Tools: 15
  Available Resources: 8

# List all available tools from connected servers
AI$ > mcp tools
GitHub Assistant:
  - create_pr: Create a pull request
  - review_code: Perform code review
  - manage_issues: Manage GitHub issues
Database Manager:
  - backup_db: Create database backup
  - optimize_query: Optimize SQL queries
```

#### 3. Agent-Based Task Execution
```bash
# Execute complex tasks with agents using MCP tools
AI$ > agent review all Python files and create a code quality report

Agent Execution Results (3 tasks):
✓ Task 1: Scanning Python files
  Output: Found 47 Python files in project
  Duration: 0.5s

✓ Task 2: Running code analysis
  Output: Analyzing with pylint, black, and mypy...
  Duration: 3.2s

✓ Task 3: Generating report
  Output: Report saved to code_quality_report.md
  Duration: 1.1s

# Agents automatically use discovered MCP tools
AI$ > agent backup production database and upload to S3

Agent automatically discovers and uses:
- Database Manager's backup_db tool
- Cloud Deployer's upload_to_s3 tool
```

#### 4. Cognitive Features - Self-Learning System
```bash
# Cognitive Memory: Remember and recall command patterns
AI$ > python -m src.main memory recall "git commit"
┌─────────────────────────────────────────────────────────────┐
│ Memories matching: git commit                               │
├──────────────────────────────┬─────────┬────────┬──────────┤
│ Command                      │ Success │ Import │ Freq     │
├──────────────────────────────┼─────────┼────────┼──────────┤
│ git commit -m "feat: add..." │    ✓    │  0.85  │    15    │
│ git commit --amend           │    ✓    │  0.72  │     8    │
└──────────────────────────────┴─────────┴────────┴──────────┘

# Get intelligent command suggestions
AI$ > python -m src.main memory suggest -c '{"cwd": "/project"}'
Command Suggestions:
  1. git commit -m "update" (confidence: 89%)
  2. git push origin main (confidence: 76%)
  3. npm test (confidence: 62%)

# Anomaly Detection: Automatic system monitoring
AI$ > python -m src.main anomaly start --interval 60
┌────────────────────────────────────────┐
│ Anomaly Detection Started             │
│ • Check Interval: 60s                  │
│ • Auto-Fix: Enabled                    │
│ • Press Ctrl+C to stop                 │
└────────────────────────────────────────┘

⚠ 2 anomalies detected
  • resource_usage: High memory usage (85%)
    ✓ Auto-fixed: Cleared system caches
  • performance_degradation: Response time increased 2.3x
    ✓ Auto-fixed: Restarted connection pool

# Autonomous DevOps: Self-optimizing infrastructure
AI$ > python -m src.main ada analyze
Services:
┌─────────────┬──────────┬──────┬──────┬────────┬────────┐
│ Service     │ Version  │ Inst │ CPU% │ Memory%│ Health │
├─────────────┼──────────┼──────┼──────┼────────┼────────┤
│ api-gateway │ 1.2.3    │  3   │ 75.2 │  82.1  │  0.65  │
│ auth-svc    │ 2.1.0    │  2   │ 45.8 │  51.3  │  0.89  │
└─────────────┴──────────┴──────┴──────┴────────┴────────┘

AI$ > python -m src.main ada optimize --type cost --dry-run
Found Optimization:
  • Type: cost
  • Target: worker-service
  • Action: downsize
  • Reason: Low resource utilization (CPU: 15%, Memory: 20%)
  • Potential Savings: $12.50/hour
  • Monthly savings: ~$9,000
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

# AI Commands - Natural language interface
AI$ > ai what files were changed in the last commit?
AI$ > explain  # Explains the previous command
AI$ > suggest find memory leaks  # Get command suggestions

# MCP Server Management
AI$ > mcp scan  # Discover available MCP servers
AI$ > mcp status  # Show connection status
AI$ > mcp tools  # List all available tools
AI$ > mcp resources  # List available resources

# Agent Execution - Complex task automation
AI$ > agent analyze codebase and generate documentation
AI$ > agent optimize all SQL queries in the project

# Health Monitoring
AI$ > health  # Run all health checks
AI$ > health llm  # Check specific component

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

# NEW: MCP Discovery Configuration
mcp_discovery:
  enabled: true
  auto_connect: true
  multicast_address: "239.255.255.250"
  port: 3749
  discovery_interval: 30  # seconds
  capability_filter: []  # Empty = accept all

# LLM Configuration
llm:
  enabled: true
  provider: ollama  # ollama, openai, anthropic, deepseek
  model: "llama2:7b"
  api_key: ${OPENAI_API_KEY}  # For cloud providers
  base_url: "http://localhost:11434"  # For local providers
  temperature: 0.7
  max_tokens: 1000
  fallback_provider: "openai"  # Fallback if primary unavailable

# Agent Configuration
agents:
  enabled: true
  max_parallel: 5
  timeout: 180  # seconds per agent
  auto_decompose: true  # Use LLM to break down complex tasks
  show_progress: true

# MCP Clients (Manual Configuration)
mcp:
  servers:
    - name: "github-assistant"
      command: "npx"
      args: ["@modelcontextprotocol/github-server"]
      type: "stdio"
    - name: "database-manager"
      command: "mcp-database"
      args: ["--port", "3749"]
      type: "websocket"

# Tool Registry
tools:
  risk_assessment: true
  require_approval:
    - HIGH
    - CRITICAL
  rate_limiting:
    enabled: true
    window: 60  # seconds
  audit_logging: true

# Security
security:
  vault_backend: keyring  # keyring, file, custom
  auto_redaction: true
  require_confirmation_for:
    - rm
    - DROP
    - DELETE
    - TRUNCATE
  auto_approve_risk_level: "LOW"  # Auto-approve LOW risk operations

# Performance
performance:
  async_workers: 4
  cache_size: 1000
  vector_db_dimension: 384
  command_history_size: 100
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
