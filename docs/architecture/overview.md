# AI-Shell Architecture Overview

**Comprehensive System Architecture Reference**

> This document provides a consolidated overview of AI-Shell's architecture. For detailed specifications, see the linked documents below.

---

## Quick Navigation

- **Detailed Architecture:** [ARCHITECTURE.md](../ARCHITECTURE.md)
- **System Design:** [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)
- **Module Specifications:** [MODULE_SPECIFICATIONS.md](./MODULE_SPECIFICATIONS.md)
- **Interaction Patterns:** [INTERACTION_PATTERNS.md](./INTERACTION_PATTERNS.md)
- **C4 Diagrams:** [C4_DIAGRAMS.md](./C4_DIAGRAMS.md)

---

## System Overview

AI-Shell is an AI-powered database administration platform built with:
- **Python 3.8+** core engine
- **Anthropic Claude** for natural language understanding
- **MCP (Model Context Protocol)** for database integration
- **FAISS** for semantic search and memory
- **Modular architecture** for extensibility

### Key Components

1. **Core Engine** - Central orchestration and command processing
2. **LLM Manager** - AI integration and prompt handling
3. **MCP Clients** - Database connectivity (16+ protocols)
4. **Security Layer** - 15 security modules (vault, RBAC, audit)
5. **Agent System** - 54+ specialized agents for autonomous operations
6. **Cognitive System** - Memory, pattern recognition, anomaly detection

---

## Architecture Layers

### 1. Presentation Layer
- **REPL Interface** - Interactive command-line interface
- **Web UI** (planned) - Web-based dashboard
- **CLI Commands** (in development) - Standalone command execution

### 2. Application Layer
- **Command Processor** - Parse and execute commands
- **Module System** - Extensible module framework
- **Event Bus** - Asynchronous event handling
- **Task Orchestrator** - Multi-agent coordination

### 3. Business Logic Layer
- **Query Optimizer** - SQL optimization engine
- **Schema Manager** - Database schema operations
- **Backup System** - Automated backup and recovery
- **Health Monitor** - System health checks and metrics

### 4. Integration Layer
- **LLM Integration** - Claude API integration
- **MCP Clients** - Multi-database connectivity
- **Agent Framework** - Agent spawning and coordination
- **External APIs** - Third-party integrations (Slack, email)

### 5. Data Layer
- **Vector Database** - FAISS semantic search
- **Configuration Store** - YAML configuration files
- **Audit Logs** - Security audit trail
- **Cache Layer** - Performance caching

### 6. Infrastructure Layer
- **Security Vault** - Encrypted credential storage
- **Logging System** - Winston-based logging
- **Monitoring** - Performance metrics
- **Resource Management** - CPU, memory, disk monitoring

---

## Security Architecture

### Defense in Depth

1. **Input Validation**
   - SQL injection prevention
   - Parameter sanitization
   - Command validation

2. **Authentication & Authorization**
   - Role-Based Access Control (RBAC)
   - Permission management
   - User authentication (planned)

3. **Data Protection**
   - AES-256 encryption
   - PII detection and redaction
   - Secure credential storage

4. **Audit & Compliance**
   - Comprehensive audit logging
   - Security event tracking
   - Compliance reporting (planned)

5. **Risk Management**
   - Query risk assessment
   - Impact analysis
   - Approval workflows (planned)

### Security Modules

```
security/
├── vault.py              # Encrypted credential storage
├── encryption.py         # AES-256 encryption
├── rbac.py              # Role-based access control
├── audit.py             # Audit logging
├── sql_injection.py     # SQL injection prevention
├── pii_detection.py     # PII detection and redaction
├── rate_limiting.py     # Rate limiting
├── input_validation.py  # Input sanitization
└── risk_assessment.py   # Query risk analysis
```

---

## Data Flow

### Command Execution Flow

```
User Input
    ↓
REPL/CLI Interface
    ↓
Command Parser
    ↓
Security Validation
    ↓
LLM Processing (if needed)
    ↓
Query Optimizer
    ↓
MCP Client
    ↓
Database
    ↓
Result Formatter
    ↓
User Output
```

### Agent Coordination Flow

```
Task Request
    ↓
Task Orchestrator
    ↓
Agent Spawning
    ↓
Parallel Execution
    ↓
Memory Coordination
    ↓
Result Aggregation
    ↓
Task Completion
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.8+ |
| AI Provider | Anthropic Claude | 3.x |
| Vector DB | FAISS | 1.9+ |
| Databases | PostgreSQL, MySQL, MongoDB, Redis | Various |
| Configuration | YAML | - |
| Logging | Winston (Node.js) / Python logging | - |

### Key Dependencies

**Python:**
- `anthropic` - Claude API client
- `faiss-cpu` - Vector similarity search
- `pyyaml` - Configuration parsing
- `cryptography` - Encryption
- `psycopg2` - PostgreSQL client

**Node.js (Optional):**
- `@modelcontextprotocol/sdk` - MCP integration
- `winston` - Logging
- `commander` - CLI framework

---

## Module Architecture

### Core Modules

1. **AIShellCore** - Main orchestration engine
2. **CommandProcessor** - Command parsing and execution
3. **ModuleLoader** - Dynamic module loading
4. **EventBus** - Asynchronous event system
5. **ConfigManager** - Configuration management

### Extensibility

```python
# Custom module example
class CustomModule(BaseModule):
    def initialize(self, core):
        """Initialize module with core reference"""
        self.core = core

    def register_commands(self):
        """Register custom commands"""
        return {
            'custom': CustomCommand
        }
```

---

## Agent System Architecture

### Agent Types (54+)

**Development:**
- coder, reviewer, tester, planner, researcher

**Coordination:**
- hierarchical-coordinator, mesh-coordinator, adaptive-coordinator

**Database:**
- query-optimizer, backup-manager, schema-designer

**Operations:**
- health-monitor, performance-analyzer, security-auditor

### Agent Communication

- **Memory-Based** - Shared memory for state synchronization
- **Event-Driven** - Event bus for notifications
- **Message Queue** - Asynchronous task distribution

---

## Performance Architecture

### Optimization Strategies

1. **Query Caching** - Cache frequently used queries
2. **Connection Pooling** - Reuse database connections
3. **Lazy Loading** - Load modules on demand
4. **Async Processing** - Non-blocking operations
5. **Resource Monitoring** - Track and optimize resource usage

### Scalability

- **Horizontal:** Multiple agent instances
- **Vertical:** Resource optimization
- **Distributed:** Multi-node coordination (planned)

---

## Deployment Architecture

### Supported Environments

1. **Development** - Local development setup
2. **Production** - Production-ready configuration
3. **Docker** (planned) - Containerized deployment
4. **Kubernetes** (planned) - Cloud-native orchestration

### Configuration Management

```yaml
# config.yaml structure
databases:
  production: {...}

llm:
  provider: anthropic
  model: claude-3-sonnet

security:
  vault: {...}
  audit: {...}

performance:
  caching: {...}
  pooling: {...}
```

---

## Monitoring & Observability

### Metrics

- **System Metrics** - CPU, memory, disk, network
- **Database Metrics** - Connection count, query latency
- **LLM Metrics** - Token usage, response time
- **Agent Metrics** - Task completion, error rate

### Health Checks

```python
# Health check system
health_checker.check_all()
# Returns: database, llm, mcp, agents, memory
```

---

## Future Architecture

### Roadmap

**v1.1.0**
- GraphQL API layer
- Enhanced RBAC
- PostgreSQL replication

**v2.0.0**
- Web-based UI
- Distributed agents
- Multi-tenancy

**v3.0.0**
- Microservices architecture
- Kubernetes operators
- Event sourcing

---

## Related Documentation

### Architecture Deep Dives
- [Detailed Architecture](../ARCHITECTURE.md)
- [System Architecture](./SYSTEM_ARCHITECTURE.md)
- [Module Specifications](./MODULE_SPECIFICATIONS.md)
- [Interaction Patterns](./INTERACTION_PATTERNS.md)
- [C4 Diagrams](./C4_DIAGRAMS.md)

### Component Documentation
- [Core API](../api/core.md)
- [Security System](../guides/troubleshooting.md#security)
- [Agent System](../agent_manager_usage.md)

### Implementation Guides
- [MCP Integration](../guides/mcp-integration.md)
- [LLM Providers](../guides/llm-providers.md)
- [Custom Commands](../guides/custom-commands.md)

---

## Architecture Principles

1. **Modularity** - Clean separation of concerns
2. **Security** - Defense in depth, secure by default
3. **Extensibility** - Plugin architecture for customization
4. **Observability** - Comprehensive monitoring and logging
5. **Performance** - Optimized for speed and resource efficiency
6. **Reliability** - Error handling and recovery
7. **Maintainability** - Clean code, comprehensive tests

---

## Getting Started

1. **Read:** [Quick Start Guide](../README.md#quick-start-5-minutes)
2. **Explore:** [API Documentation](../api/core.md)
3. **Extend:** [Custom Commands](../guides/custom-commands.md)
4. **Deploy:** [Configuration Guide](../guides/mcp-integration.md)

---

**Last Updated:** 2025-10-28
**Version:** 1.0.0
**Maintainers:** AI-Shell Core Team
