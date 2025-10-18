# AI-Shell Documentation Index

Welcome to the AI-Shell documentation. This index provides organized access to all documentation resources.

## 📚 Getting Started

- **[README](../README.md)** - Project overview, installation, and quick start
- **[Quick Reference](QUICK_REFERENCE.md)** - Common commands and patterns
- **[Release Notes](RELEASE_NOTES.md)** - Version history and changes

## 🎯 User Guides

### Cognitive Features (v1.2.0+)
- **[Cognitive Memory](howto/COGNITIVE_MEMORY.md)** - Learn from command history with semantic search
- **[Anomaly Detection](howto/ANOMALY_DETECTION.md)** - Self-healing and monitoring
- **[Autonomous DevOps](howto/AUTONOMOUS_DEVOPS.md)** - Infrastructure optimization

### Core Features
- **[Custom Commands](guides/custom-commands.md)** - Create and manage custom shell commands
- **[LLM Providers](guides/llm-providers.md)** - Configure and use AI providers (OpenAI, Anthropic, Ollama)
- **[MCP Integration](guides/mcp-integration.md)** - Model Context Protocol setup and usage
- **[Agent Integration](agent_manager_usage.md)** - Use AI agents with MCP tools
- **[LLM Integration Guide](llm-integration-guide.md)** - Comprehensive LLM setup
- **[LLM Testing Patterns](llm-testing-patterns.md)** - Testing with LLM providers

### Advanced Features
- **[Claude Code Implementation](claude-code-implementation-guide.md)** - Claude Code integration patterns
- **[Enhanced Features](enhanced-features.md)** - Advanced shell capabilities

## 🔧 API Documentation

- **[Complete API Reference](API.md)** - Full API documentation
- **[Core API](api/core.md)** - Core module reference
- **[CLI API](api/cli.md)** - Command-line interface reference
- **[Database API](api/database.md)** - Database clients and utilities

## 🏗️ Architecture & Design

- **[System Architecture](ARCHITECTURE.md)** - Overall system design
- **[MCP Architecture](ai-shell-mcp-architecture.md)** - Model Context Protocol integration
- **[AIShell Design](AIShell.md)** - Core shell design principles

## 🔨 Development

- **[Testing Guide](TESTING_GUIDE.md)** - Comprehensive testing documentation
- **[CI/CD Guide](CI_CD_GUIDE.md)** - Continuous integration and deployment
- **[Implementation Plan](IMPLEMENTATION_PLAN.md)** - Development roadmap
- **[Pending Features](PENDING_FEATURES.md)** - Planned enhancements and status

## 📖 How-To Guides

Located in `docs/howto/`:
- **[Cognitive Memory](howto/COGNITIVE_MEMORY.md)** - Semantic command search
- **[Anomaly Detection](howto/ANOMALY_DETECTION.md)** - Self-healing setup
- **[Autonomous DevOps](howto/AUTONOMOUS_DEVOPS.md)** - Infrastructure automation
- **[Automated Monitoring](howto/automated-monitoring.md)** - System monitoring
- **[Code Review](howto/code-review.md)** - Automated code reviews
- **[Custom LLM Provider](howto/custom-llm-provider.md)** - Build custom LLM providers
- **[MCP Discovery](howto/mcp-discovery.md)** - Discover and use MCP servers
- **[Query Optimization](howto/query-optimization.md)** - Database query optimization

## 📋 Reference Materials

- **[FAISS Upgrade Notes](FAISS_UPGRADE_NOTES.md)** - Vector search migration guide
- **[Index](INDEX.md)** - Legacy documentation index

## 🗂️ Archive

Historical documentation (phase reports, status updates, old guides) is available in `docs/archive/`:
- `phase-reports/` - Development phase completion reports
- `status-reports/` - Project status and progress reports
- `old-architecture/` - Previous architecture documents
- `old-guides/` - Superseded guides and tutorials

## 📂 Directory Structure

```
docs/
├── DOCUMENTATION_INDEX.md        # This file
├── README.md                     # Project overview
├── QUICK_REFERENCE.md            # Quick reference guide
├── RELEASE_NOTES.md              # Version history
├── PENDING_FEATURES.md           # Roadmap and status
├── API.md                        # Complete API reference
├── ARCHITECTURE.md               # System architecture
├── TESTING_GUIDE.md              # Testing documentation
├── CI_CD_GUIDE.md                # CI/CD setup
├── api/                          # API reference docs
│   ├── core.md
│   ├── cli.md
│   └── database.md
├── guides/                       # User guides
│   ├── custom-commands.md
│   ├── llm-providers.md
│   └── mcp-integration.md
├── howto/                        # How-to tutorials
│   ├── COGNITIVE_MEMORY.md
│   ├── ANOMALY_DETECTION.md
│   └── AUTONOMOUS_DEVOPS.md
└── archive/                      # Historical documentation
    ├── phase-reports/
    ├── status-reports/
    ├── old-architecture/
    └── old-guides/
```

## 🔍 Finding Documentation

- **New users**: Start with [README](../README.md) → [Quick Reference](QUICK_REFERENCE.md)
- **Feature documentation**: See [User Guides](#-user-guides) section
- **API reference**: See [API Documentation](#-api-documentation) section
- **Development**: See [Development](#-development) section
- **How-to guides**: See [How-To Guides](#-how-to-guides) section

## 📝 Contributing to Documentation

When adding new documentation:
1. Place user guides in `docs/guides/`
2. Place how-to tutorials in `docs/howto/`
3. Place API docs in `docs/api/`
4. Update this index
5. Link from README.md if it's a major feature

## 🆘 Getting Help

- Check [Quick Reference](QUICK_REFERENCE.md) for common tasks
- Review [User Guides](#-user-guides) for detailed feature documentation
- See [API Documentation](#-api-documentation) for code-level details
- Browse [How-To Guides](#-how-to-guides) for step-by-step tutorials

---

**Last Updated**: 2025-10-18
**Documentation Version**: 1.2.0
