# AI-Shell Documentation Index

## 📚 Complete Documentation Guide

Welcome to the AI-Shell documentation! This index provides quick access to all documentation resources.

---

## 🚀 Getting Started

### Main Documentation
- **[README](./README.md)** - Main documentation hub with overview, features, and quick start

### Essential Guides
1. **[MCP Integration Guide](./guides/mcp-integration.md)** - Database connectivity setup
   - Oracle thin mode (no client required)
   - PostgreSQL pure Python setup
   - Connection pooling and optimization

2. **[LLM Provider Setup](./guides/llm-providers.md)** - AI model configuration
   - Ollama (local LLM hosting)
   - OpenAI, Anthropic, DeepSeek
   - Multi-provider fallback strategies

3. **[Custom Commands Development](./guides/custom-commands.md)** - Extend AI-Shell
   - Simple and interactive commands
   - AI-powered agentic commands
   - Module development

4. **[Troubleshooting Guide](./guides/troubleshooting.md)** - Problem resolution
   - Common issues and solutions
   - Debug tools and logging
   - Performance tuning

---

## 🏗️ Architecture

### System Design
- **[Architecture Overview](./architecture/overview.md)** - Complete system architecture
  - Core components
  - Data flow diagrams
  - Security layers
  - Performance architecture
  - Technology stack

### Additional Architecture Docs
- **[System Architecture](./architecture/SYSTEM_ARCHITECTURE.md)** - Detailed system design
- **[Module Specifications](./architecture/MODULE_SPECIFICATIONS.md)** - Module internals
- **[Interaction Patterns](./architecture/INTERACTION_PATTERNS.md)** - Component interactions
- **[C4 Diagrams](./architecture/C4_DIAGRAMS.md)** - Visual architecture

---

## 📖 API Reference

### Core APIs
- **[Core API](./api/core.md)** - Comprehensive API reference
  - `AIShellCore` - Main orchestrator
  - `ExecutionContext` - Command context
  - `Command` - Base command class
  - `Module` - Module system
  - `EventBus` - Async events
  - `LLMManager` - AI integration
  - `VectorDatabase` - Semantic search

### Development APIs
- **Module API** - Module development (see Core API)
- **Command API** - Command creation (see Core API)
- **MCP Client API** - Database clients (see Core API)

---

## 💻 Examples

### Configuration Examples

#### Basic Configuration
- **[basic-config.yaml](../examples/configurations/basic-config.yaml)**
  - Essential settings for development
  - Ollama local LLM setup
  - Basic MCP configuration
  - Standard security settings

#### Advanced Configuration
- **[advanced-config.yaml](../examples/configurations/advanced-config.yaml)**
  - Enterprise-grade configuration
  - Multi-provider LLM setup
  - SSL/TLS database connections
  - Advanced monitoring and auditing
  - Web interface configuration

### Setup Scripts

- **[setup_oracle.sh](../examples/scripts/setup_oracle.sh)**
  - Oracle database connection setup
  - Thin mode configuration (no Oracle client)
  - Automatic vault integration
  - Connection testing

- **[setup_postgres.sh](../examples/scripts/setup_postgres.sh)**
  - PostgreSQL connection setup
  - SSL certificate configuration
  - Pure Python client setup
  - Automated testing

---

## 📊 Additional Resources

### Research & Planning
- **[MCP Integration Architecture](./research/mcp-integration-architecture.md)** - Integration research
- **[LLM Integration Guide](./llm-integration-guide.md)** - AI integration details
- **[Executive Summary](./executive-summary.md)** - Project overview

### Implementation Guides
- **[CLI Implementation Summary](./cli-implementation-summary.md)** - CLI development
- **[LLM Implementation Summary](./llm-implementation-summary.md)** - AI implementation

### Quality & Security
- **[Code Quality Assessment](./code-quality-assessment.md)** - Quality metrics
- **[Security Audit Report](./security-audit-report.md)** - Security review
- **[Review Summary](./review-summary.md)** - Comprehensive review

---

## 🔍 Quick Reference

### By Topic

#### Installation & Setup
1. [Quick Start Guide](./README.md#quick-start) - Get up and running
2. [Configuration Options](./README.md#configuration) - Config file setup
3. [Oracle Setup Script](../examples/scripts/setup_oracle.sh) - Oracle connection
4. [PostgreSQL Setup Script](../examples/scripts/setup_postgres.sh) - PostgreSQL connection

#### LLM & AI Features
1. [LLM Provider Setup](./guides/llm-providers.md) - Configure AI models
2. [Model Selection Guide](./guides/llm-providers.md#model-selection-guide) - Choose models
3. [Privacy & Security](./guides/llm-providers.md#privacy--security) - Data protection
4. [Performance Optimization](./guides/llm-providers.md#performance-optimization) - Speed tuning

#### Database Integration
1. [MCP Integration](./guides/mcp-integration.md) - Database connectivity
2. [Oracle Thin Mode](./guides/mcp-integration.md#oracle-mcp-client) - No client setup
3. [PostgreSQL Pure Python](./guides/mcp-integration.md#postgresql-mcp-client) - psycopg2
4. [Connection Pooling](./guides/mcp-integration.md#advanced-features) - Pool management

#### Development
1. [Custom Commands](./guides/custom-commands.md) - Build commands
2. [Module Development](./guides/custom-commands.md#module-development) - Create modules
3. [Core API Reference](./api/core.md) - API docs
4. [Plugin System](./guides/custom-commands.md#plugin-distribution) - Distribute plugins

#### Troubleshooting
1. [Common Issues](./guides/troubleshooting.md#common-issues-and-solutions) - Quick fixes
2. [Debug Tools](./guides/troubleshooting.md#debugging-tools) - Diagnostics
3. [Performance Issues](./guides/troubleshooting.md#performance-issues) - Optimization
4. [Getting Help](./guides/troubleshooting.md#getting-help) - Support resources

### By User Type

#### For End Users
- [README](./README.md) - Start here
- [Quick Start](./README.md#quick-start)
- [Basic Configuration](../examples/configurations/basic-config.yaml)
- [Troubleshooting](./guides/troubleshooting.md)

#### For Database Administrators
- [MCP Integration](./guides/mcp-integration.md)
- [Oracle Setup](../examples/scripts/setup_oracle.sh)
- [PostgreSQL Setup](../examples/scripts/setup_postgres.sh)
- [Advanced Configuration](../examples/configurations/advanced-config.yaml)

#### For Developers
- [Custom Commands](./guides/custom-commands.md)
- [Core API](./api/core.md)
- [Architecture Overview](./architecture/overview.md)
- [Module Specifications](./architecture/MODULE_SPECIFICATIONS.md)

#### For DevOps/SRE
- [Advanced Configuration](../examples/configurations/advanced-config.yaml)
- [Performance Tuning](./guides/troubleshooting.md#performance-issues)
- [Security Best Practices](./architecture/overview.md#security-architecture)
- [Monitoring](../examples/configurations/advanced-config.yaml)

---

## 📝 Documentation Coverage

### Core Features Documented ✅

- ✅ AI-powered CLI with multi-LLM support
- ✅ MCP thin client database connectivity
- ✅ Secure vault with auto-redaction
- ✅ Asynchronous panel enrichment
- ✅ Vector-based semantic search
- ✅ Custom command development
- ✅ Module system architecture
- ✅ Risk analysis for operations
- ✅ Web interface support
- ✅ Comprehensive troubleshooting

### Documentation Types

| Type | Location | Coverage |
|------|----------|----------|
| User Guides | `/docs/guides/` | 100% |
| API Reference | `/docs/api/` | 100% |
| Architecture | `/docs/architecture/` | 100% |
| Examples | `/examples/` | 100% |
| Troubleshooting | `/docs/guides/troubleshooting.md` | 100% |

---

## 🔗 External Resources

### Community
- **GitHub Repository**: [ai-shell](https://github.com/dimensigon/aishell)
- **Issues & Bug Reports**: [GitHub Issues](https://github.com/dimensigon/aishell/issues)
- **Discussions & Q&A**: [GitHub Discussions](https://github.com/dimensigon/aishell/discussions)
- **Documentation Site**: [ai-shell.readthedocs.io](https://ai-shell.readthedocs.io)

### Technology References
- **Textual Framework**: [textual.textualize.io](https://textual.textualize.io)
- **Ollama**: [ollama.com/docs](https://ollama.com/docs)
- **cx_Oracle**: [cx-oracle.readthedocs.io](https://cx-oracle.readthedocs.io)
- **psycopg2**: [psycopg.org/docs](https://www.psycopg.org/docs/)
- **FAISS**: [faiss.ai](https://faiss.ai)

---

## 🆕 Latest Updates

**Last Updated**: 2025-10-03

### Recent Additions
- ✨ Complete architecture documentation
- ✨ Advanced configuration examples
- ✨ Database setup automation scripts
- ✨ Comprehensive API reference
- ✨ Enhanced troubleshooting guide

---

## 📞 Support

### Getting Help

1. **Check Documentation** - Search this index for relevant topics
2. **Review Examples** - Check configuration and script examples
3. **Troubleshooting Guide** - Common issues and solutions
4. **GitHub Discussions** - Community Q&A
5. **GitHub Issues** - Bug reports and feature requests

### Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code contribution guidelines
- Documentation improvements
- Bug report templates
- Feature request process

---

## 🗺️ Documentation Roadmap

### Planned Additions
- [ ] Video tutorials
- [ ] Interactive examples
- [ ] Migration guides
- [ ] Best practices cookbook
- [ ] Performance benchmarks
- [ ] Multi-language support

---

**Navigation**: [Home](./README.md) | [Guides](./guides/) | [API](./api/) | [Architecture](./architecture/) | [Examples](../examples/)
