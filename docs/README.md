# AI-Shell Documentation

## Overview

AI-Shell is an intelligent command-line interface that combines AI-powered assistance with database management, multi-agent systems, and advanced LLM integration.

## Features

- **Intelligent Agent System**: Delegate complex tasks to specialized AI agents
- **Multi-Provider LLM Support**: Switch between Ollama, OpenAI, Anthropic, and more
- **MCP Protocol**: Universal connectivity to databases, APIs, storage, and message queues
- **Context-Aware Suggestions**: Smart command recommendations based on usage patterns
- **Performance Optimization**: Built-in query optimization and caching
- **Secure Vault**: Encrypted credential management

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AIShell.git
cd AIShell

# Install dependencies
pip install -r requirements.txt

# Run in mock mode (no external dependencies)
python -m src.main --mock
```

### Basic Usage

```bash
# Start AI-Shell
python -m src.main

# Get command suggestions
ai-shell> suggest

# Get help
ai-shell> help

# Execute SQL query
ai-shell> query SELECT * FROM users

# Ask AI for assistance
ai-shell> ask How do I optimize this query?

# Delegate to agents
ai-shell> agent Analyze database performance
```

## Command Reference

### Database Commands
- `query <sql>` - Execute SQL query
- `show tables` - List all tables
- `describe <table>` - Show table structure
- `analyze <query>` - Analyze query performance

### AI Commands
- `ask <question>` - Ask AI assistant
- `agent <task>` - Delegate task to agents
- `agents` - List available agents
- `llm generate <prompt>` - Generate text with LLM

### MCP Commands
- `mcp resources` - List available resources
- `mcp tools` - List available tools
- `mcp connect <type>` - Create connection
- `mcp status` - Show connection status

### LLM Commands
- `llm providers` - List LLM providers
- `llm switch <provider>` - Switch provider
- `llm status` - Show current provider
- `llm generate <text>` - Generate text

### System Commands
- `suggest` - Get command suggestions
- `help [command]` - Get help
- `history` - Show command history
- `health` - Check system health
- `metrics` - Show performance metrics
- `exit` - Exit shell

## Configuration

### Config File

Create `config/ai-shell-config.yaml`:

```yaml
database:
  default_connection: postgresql
  pool_size: 10
  timeout: 30

llm:
  provider: ollama
  model: llama2
  temperature: 0.7

security:
  vault_key: your-secure-key-here

performance:
  cache_enabled: true
  cache_ttl: 300
```

### Environment Variables

```bash
export OPENAI_API_KEY=your-key
export ANTHROPIC_API_KEY=your-key
export AI_SHELL_CONFIG=/path/to/config.yaml
```

## Architecture

### Core Components

1. **Agent System**
   - Research Agent: Information gathering
   - Code Agent: Code generation and analysis
   - Command Agent: System command execution
   - Analysis Agent: Data analysis

2. **LLM Integration**
   - Provider abstraction layer
   - Multi-provider support
   - Streaming and async operations

3. **MCP Protocol**
   - Database connections
   - REST API integration
   - File storage (S3, etc.)
   - Message queues

4. **Command Suggester**
   - Context-aware recommendations
   - Command history tracking
   - Error recovery suggestions
   - Fuzzy matching

## Database Support

### PostgreSQL
```bash
ai-shell> mcp connect postgresql
Host: localhost
Port: 5432
Database: mydb
Username: user
Password: ****
```

### MySQL
```bash
ai-shell> mcp connect mysql
Host: localhost
Port: 3306
Database: mydb
Username: root
Password: ****
```

### Oracle
```bash
ai-shell> mcp connect oracle
Host: localhost
Port: 1521
Service: FREEPDB1
Username: SYS
Password: ****
```

## Agent System

### Available Agents

- **ResearchAgent**: Gathers information and analyzes data
- **CodeAgent**: Generates and reviews code
- **CommandAgent**: Executes system commands
- **AnalysisAgent**: Performs data analysis

### Using Agents

```bash
# Delegate a task
ai-shell> agent analyze database schema and suggest improvements

# List agents
ai-shell> agents

# Agent task examples
ai-shell> agent optimize slow queries
ai-shell> agent generate API documentation
ai-shell> agent analyze security vulnerabilities
```

## LLM Providers

### Ollama (Local)
```bash
ai-shell> llm switch ollama llama2
```

### OpenAI
```bash
ai-shell> llm switch openai gpt-4 YOUR_API_KEY
```

### Anthropic
```bash
ai-shell> llm switch anthropic claude-3 YOUR_API_KEY
```

### Mock (Testing)
```bash
ai-shell> llm switch mock
```

## Command Suggestions

The intelligent suggestion system learns from your usage:

- **Shortcuts**: `q` → query, `h` → help, `m` → metrics
- **Sequences**: Suggests next logical command
- **Context**: Recommends based on current state
- **Recovery**: Helps recover from errors

## Performance

### Query Optimization
- Automatic query analysis
- Index recommendations
- Execution plan visualization

### Caching
- Result caching with TTL
- Cache statistics in metrics
- Manual cache control

### Monitoring
```bash
ai-shell> metrics
Performance Metrics:
  Queries: 42
  Avg Time: 0.234s
  Cache Hit Rate: 87.5%
```

## Security

### Vault System
- Encrypted credential storage
- Master password protection
- Secure credential retrieval

### Best Practices
- Never hardcode credentials
- Use environment variables
- Enable vault encryption
- Regular credential rotation

## Testing

### Run Tests
```bash
# All tests
pytest

# Specific module
pytest tests/agents/
pytest tests/llm/
pytest tests/ai/

# With coverage
pytest --cov=src
```

### Mock Mode
```bash
python -m src.main --mock
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   ```bash
   ai-shell> mcp status
   ai-shell> mcp connect postgresql
   ```

2. **LLM Not Working**
   ```bash
   ai-shell> llm status
   ai-shell> llm switch mock
   ```

3. **No Suggestions**
   ```bash
   ai-shell> help
   ai-shell> history
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details