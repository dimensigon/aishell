# AI-Shell System Architecture

**Version:** 1.0.0
**Last Updated:** October 11, 2025
**Status:** Production

## Table of Contents

1. [Overview](#overview)
2. [System Components](#system-components)
3. [Architecture Patterns](#architecture-patterns)
4. [Data Flow](#data-flow)
5. [Module Specifications](#module-specifications)
6. [Security Architecture](#security-architecture)
7. [Performance Architecture](#performance-architecture)
8. [Deployment Architecture](#deployment-architecture)
9. [Extension Points](#extension-points)

---

## Overview

AI-Shell is an intelligent command-line interface that combines traditional shell functionality with AI-powered assistance, database management, and autonomous agent orchestration. Built on asynchronous Python with a modular plugin architecture, it provides a context-aware terminal experience with enterprise-grade security and reliability.

### Design Philosophy

1. **Modularity First:** Everything is a plugin or module
2. **Async by Default:** Non-blocking I/O throughout
3. **Security Always:** Multiple layers of protection
4. **Fail Gracefully:** Degraded mode operation when components fail
5. **Extensibility:** Plugin architecture for customization

### Key Characteristics

- **Language:** Python 3.9+ (supports 3.9-3.14)
- **Async Framework:** asyncio
- **UI Framework:** Textual (TUI) + prompt-toolkit
- **Vector Store:** FAISS 1.12.0
- **Database Protocol:** MCP (Model Context Protocol)
- **LLM Integration:** Local (Ollama) + Cloud (OpenAI, Anthropic)

---

## System Components

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI-Shell Application                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  User Input  │  │   AI Agent   │  │  Health      │          │
│  │  Processing  │  │  System      │  │  Monitor     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────┬───────┴──────────┬──────┘                  │
│                    ▼                   ▼                          │
│            ┌───────────────────────────────────┐                 │
│            │      Event Bus (Async)            │                 │
│            └───────────────────────────────────┘                 │
│                    │                   │                          │
│         ┌──────────┼───────────────────┼──────────┐             │
│         ▼          ▼                   ▼          ▼             │
│   ┌─────────┐ ┌─────────┐      ┌─────────┐ ┌─────────┐        │
│   │ LLM     │ │Database │      │Security │ │ Vector  │        │
│   │ Manager │ │ Module  │      │ Module  │ │ Store   │        │
│   └─────────┘ └─────────┘      └─────────┘ └─────────┘        │
│         │          │                   │          │              │
│         └──────────┴───────┬───────────┴──────────┘             │
│                            ▼                                      │
│                    ┌───────────────┐                            │
│                    │  MCP Clients  │                            │
│                    │  (Thin)       │                            │
│                    └───────────────┘                            │
│                            │                                      │
└────────────────────────────┼──────────────────────────────────┘
                             ▼
                    ┌─────────────────┐
                    │   Databases     │
                    │ Oracle, PG,     │
                    │ MySQL, Mongo    │
                    └─────────────────┘
```

### Component Layers

#### Layer 1: Presentation (UI)
- **Textual TUI:** Dynamic panels, widgets, screens
- **prompt-toolkit:** Command input with autocomplete
- **Rich:** Styled output formatting

#### Layer 2: Application (Core)
- **AIShellCore:** Central orchestrator
- **Event Bus:** Asynchronous message passing
- **Config Manager:** Configuration management
- **Health Monitor:** System health tracking

#### Layer 3: Business Logic (Modules)
- **Database Module:** Query execution and optimization
- **LLM Manager:** AI operations and intent analysis
- **Agent System:** Autonomous task execution
- **Tool Registry:** Managed tool execution
- **Safety Controller:** Risk assessment and approval

#### Layer 4: Integration (MCP Clients)
- **Oracle Client:** python-oracledb thin mode
- **PostgreSQL Client:** asyncpg
- **MySQL Client:** aiomysql
- **MongoDB Client:** motor
- **Redis Client:** redis-py
- **Cassandra, Neo4j, DynamoDB:** Specialized clients

#### Layer 5: Infrastructure
- **Security Vault:** Encrypted credential storage
- **Vector Store:** FAISS semantic search
- **Cache Layer:** Query and result caching
- **Audit Logger:** Compliance tracking

---

## Architecture Patterns

### 1. Plugin Architecture

**Pattern:** Strategy + Factory

```python
# Module registration
class AIShellCore:
    def register_module(self, module: BaseModule):
        """Register a module plugin"""
        self.modules[module.name] = module

# Module interface
class BaseModule(ABC):
    @abstractmethod
    def initialize(self) -> bool: ...

    @abstractmethod
    def execute(self, command: str) -> Result: ...

    @abstractmethod
    def shutdown(self) -> None: ...
```

**Benefits:**
- Hot-pluggable modules
- Independent module development
- Easy testing and mocking
- Runtime module loading

### 2. Event-Driven Architecture

**Pattern:** Publisher-Subscriber

```python
# Event bus
class AsyncEventBus:
    async def publish(self, event: Event):
        """Publish event to all subscribers"""
        for subscriber in self.subscribers[event.type]:
            await subscriber.handle(event)

    async def subscribe(self, event_type: str, handler):
        """Subscribe to event type"""
        self.subscribers[event_type].append(handler)
```

**Benefits:**
- Loose coupling between components
- Non-blocking operations
- Easy to add new event handlers
- Better testability

### 3. MCP (Model Context Protocol)

**Pattern:** Adapter

```python
class BaseMCPClient(ABC):
    """Abstract MCP client interface"""

    @abstractmethod
    async def connect(self, connection_string: str): ...

    @abstractmethod
    async def execute(self, query: str) -> Result: ...

    @abstractmethod
    async def disconnect(self): ...
```

**Benefits:**
- Uniform database interface
- Easy to add new databases
- Consistent error handling
- Connection pooling abstraction

### 4. Agent Coordination

**Pattern:** Chain of Responsibility + Template Method

```python
class BaseAgent(ABC):
    async def execute(self, task: Task) -> Result:
        """Template method for agent execution"""
        # 1. Plan
        steps = await self.plan(task)

        # 2. Execute each step
        results = []
        for step in steps:
            result = await self.execute_step(step)
            results.append(result)

        # 3. Aggregate
        return await self.aggregate(results)

    @abstractmethod
    async def plan(self, task: Task) -> List[Step]: ...

    @abstractmethod
    async def execute_step(self, step: Step) -> Result: ...
```

**Benefits:**
- Standardized agent interface
- Easy to create new agents
- Built-in error handling
- State management included

### 5. Security Layering

**Pattern:** Decorator + Chain of Responsibility

```python
# Multiple security layers
@require_authentication
@check_authorization
@validate_input
@audit_log
async def execute_query(query: str) -> Result:
    return await database.execute(query)
```

**Benefits:**
- Composable security controls
- Easy to add/remove layers
- Clear security boundaries
- Audit trail by default

---

## Data Flow

### User Query Execution Flow

```
User Input → Intent Analysis → Module Routing → Execution → Output

1. User Input
   ├─ Command parsing
   ├─ Syntax validation
   └─ History recording

2. Intent Analysis (LLM)
   ├─ Query type detection (SELECT/INSERT/etc)
   ├─ Risk assessment
   └─ Context enrichment

3. Module Routing
   ├─ Database module for SQL
   ├─ AI helper for natural language
   ├─ Vault for credential operations
   └─ System commands for shell

4. Execution
   ├─ Safety validation
   ├─ Query optimization
   ├─ Connection pool management
   └─ Result formatting

5. Output
   ├─ Result rendering
   ├─ Error handling
   └─ Audit logging
```

### Agent Workflow Execution

```
Task → Planning → Tool Selection → Execution → Aggregation

1. Task Reception
   ├─ Task parsing
   ├─ Context gathering
   └─ Priority assignment

2. Planning (LLM-powered)
   ├─ Task decomposition
   ├─ Step ordering
   ├─ Dependency analysis
   └─ Resource estimation

3. Tool Selection
   ├─ Capability matching
   ├─ Risk assessment
   ├─ Tool validation
   └─ Parameter binding

4. Execution
   ├─ Step-by-step execution
   ├─ Checkpoint creation
   ├─ Error recovery
   └─ Approval requests (if needed)

5. Aggregation
   ├─ Result compilation
   ├─ Success validation
   └─ Audit logging
```

### Health Check Flow

```
Trigger → Parallel Checks → Aggregation → Status Report

1. Health Check Trigger
   ├─ Scheduled (every 60s)
   ├─ On-demand (user request)
   └─ On startup

2. Parallel Execution (<2s total)
   ├─ LLM availability check
   ├─ Database connectivity
   ├─ Filesystem health
   ├─ Memory usage
   └─ Custom checks

3. Result Aggregation
   ├─ Timeout handling
   ├─ Status normalization
   └─ Priority ordering

4. Status Report
   ├─ Overall status (healthy/degraded/critical)
   ├─ Component details
   └─ Recommendation generation
```

---

## Module Specifications

### Core Module (`src/core/`)

**Responsibilities:**
- Application lifecycle management
- Module registration and coordination
- Event bus orchestration
- Configuration management
- Health monitoring

**Key Classes:**
- `AIShellCore` - Central orchestrator
- `AsyncEventBus` - Event publication/subscription
- `ConfigManager` - Configuration loading and validation
- `HealthCheckManager` - Parallel health checks
- `DegradedModeManager` - Graceful degradation

**Dependencies:**
- asyncio (standard library)
- pyyaml (configuration)
- aiofiles (async file I/O)

### Database Module (`src/database/`)

**Responsibilities:**
- SQL execution and optimization
- Connection pool management
- Query risk analysis
- Natural language to SQL
- Query history tracking

**Key Classes:**
- `DatabaseModule` - Main database interface
- `SQLRiskAnalyzer` - Risk assessment
- `QueryOptimizer` - Query optimization
- `NLPtoSQL` - Natural language processing
- `SQLHistory` - Query history management

**Dependencies:**
- MCP clients (database drivers)
- LLM manager (for NLP)
- Security module (for validation)

### Security Module (`src/security/`)

**Responsibilities:**
- Credential encryption and storage
- Sensitive data redaction
- Command sanitization
- Path validation
- Audit logging

**Key Classes:**
- `SecureVault` - Encrypted credential vault
- `RedactionEngine` - PII/sensitive data removal
- `CommandSanitizer` - Safe command execution
- `PathValidator` - Path traversal prevention
- `AuditLogger` - Compliance logging

**Dependencies:**
- cryptography (Fernet encryption)
- keyring (OS credential storage)

### LLM Module (`src/llm/`)

**Responsibilities:**
- Local and cloud LLM integration
- Intent analysis
- Embedding generation
- Provider management
- Anonymization

**Key Classes:**
- `LocalLLMManager` - LLM orchestration
- `OllamaProvider` - Local LLM provider
- `EmbeddingModel` - Vector embedding generation
- `AnonymizationEngine` - Data anonymization

**Dependencies:**
- ollama (local LLM)
- openai (cloud LLM)
- anthropic (cloud LLM)
- sentence-transformers (embeddings)

### Agent Module (`src/agents/`)

**Responsibilities:**
- Autonomous task execution
- Multi-step workflow coordination
- Tool management
- Safety validation
- State persistence

**Key Classes:**
- `BaseAgent` - Agent base class
- `CoordinatorAgent` - Multi-agent orchestration
- `ToolRegistry` - Tool management
- `SafetyController` - Risk and approval
- `StateManager` - Agent state persistence

**Dependencies:**
- LLM module (planning)
- Database module (data operations)
- Security module (validation)

### UI Module (`src/ui/`)

**Responsibilities:**
- Terminal user interface
- Panel management
- Command input handling
- Result formatting
- Real-time updates

**Key Classes:**
- `AIShellApp` - Main Textual application
- `PanelManager` - Dynamic panel sizing
- `CommandInput` - Input widget with autocomplete
- `ContextSuggestionEngine` - AI-powered suggestions
- `MemoryMonitor` - Resource usage tracking

**Dependencies:**
- textual (TUI framework)
- prompt-toolkit (input handling)
- rich (output formatting)

### MCP Clients (`src/mcp_clients/`)

**Responsibilities:**
- Database connectivity
- Query execution
- Transaction management
- Connection pooling
- Error translation

**Key Classes:**
- `BaseMCPClient` - Abstract client interface
- `PostgreSQLClient` - PostgreSQL thin client
- `OracleClient` - Oracle thin client (no Oracle install)
- `MySQLClient` - MySQL/MariaDB client
- `MongoDBClient` - MongoDB client
- `RedisClient` - Redis client

**Dependencies:**
- asyncpg (PostgreSQL)
- python-oracledb (Oracle)
- aiomysql (MySQL)
- motor (MongoDB)
- redis (Redis)

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Input Validation                               │
│ - Command sanitization                                  │
│ - SQL injection prevention                              │
│ - Path traversal blocking                               │
└─────────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Authentication & Authorization                 │
│ - Credential vault (encrypted)                          │
│ - Permission checking                                   │
│ - Rate limiting                                         │
└─────────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Execution Safety                               │
│ - Risk assessment                                       │
│ - Approval workflows                                    │
│ - Sandboxed execution                                   │
└─────────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 4: Data Protection                                │
│ - Sensitive data redaction                              │
│ - Encryption at rest                                    │
│ - Secure communication                                  │
└─────────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Audit & Compliance                             │
│ - Complete audit trail                                  │
│ - Compliance reporting                                  │
│ - Anomaly detection                                     │
└─────────────────────────────────────────────────────────┘
```

### Credential Storage

**Encryption:** Fernet (symmetric)
- **Key Derivation:** PBKDF2-HMAC-SHA256
- **Iterations:** 100,000
- **Salt:** Unique per vault (cryptographically secure random)
- **Key Length:** 256 bits

**Vault Structure:**
```json
{
  "version": "2.0",
  "credentials": {
    "prod_db": {
      "id": "uuid",
      "type": "database",
      "encrypted_data": "...",
      "created_at": "2025-10-11T12:00:00Z",
      "metadata": {...}
    }
  }
}
```

### Access Control

**Risk Levels:**
1. **NONE:** Safe operations (SELECT, SHOW)
2. **LOW:** Limited impact (INSERT single row)
3. **MEDIUM:** Moderate impact (UPDATE with WHERE)
4. **HIGH:** Significant impact (DELETE, DROP)
5. **CRITICAL:** Irreversible impact (DROP DATABASE)

**Approval Requirements:**
- NONE/LOW: Auto-execute
- MEDIUM: Confirmation required
- HIGH: Typed approval required
- CRITICAL: Typed approval + second factor

---

## Performance Architecture

### Asynchronous Operations

**Event Loop:** asyncio
- Non-blocking I/O throughout
- Concurrent task execution
- Efficient resource utilization

**Key Performance Patterns:**

1. **Parallel Health Checks:**
```python
# All checks run concurrently
results = await asyncio.gather(
    check_llm(),
    check_database(),
    check_filesystem(),
    check_memory(),
    return_exceptions=True
)
```

2. **Connection Pooling:**
```python
# Reuse database connections
pool = await asyncpg.create_pool(
    dsn=connection_string,
    min_size=5,
    max_size=20
)
```

3. **Query Caching:**
```python
# Cache frequent queries
@cache(ttl=300)
async def execute_query(sql: str):
    return await database.execute(sql)
```

### Optimization Strategies

1. **Lazy Loading:** Load modules on-demand
2. **Vector Search:** FAISS for fast similarity search
3. **Result Streaming:** Stream large result sets
4. **Background Tasks:** Non-blocking enrichment
5. **Memory Management:** Automatic cleanup

### Benchmarks (v2.0.0)

| Operation | Time | Notes |
|-----------|------|-------|
| Health checks (parallel) | 1.8s | 4 checks concurrently |
| Agent planning | 0.9s | LLM-powered decomposition |
| Query optimization | 180ms | Pattern-based |
| Vector search (1000 items) | 45ms | FAISS similarity search |
| Startup time | 1.3s | Module initialization |
| Memory footprint | 98MB | Base application |

---

## Deployment Architecture

### Standalone Deployment

```
┌──────────────────────────────────────┐
│         User Workstation             │
│  ┌────────────────────────────────┐  │
│  │      AI-Shell Process          │  │
│  │  ┌──────────┐  ┌─────────┐    │  │
│  │  │   Core   │  │ Modules │    │  │
│  │  └──────────┘  └─────────┘    │  │
│  │  ┌──────────┐  ┌─────────┐    │  │
│  │  │ Ollama   │  │ FAISS   │    │  │
│  │  │ (Local)  │  │ Vector  │    │  │
│  │  └──────────┘  └─────────┘    │  │
│  └────────────────────────────────┘  │
│                │                      │
└────────────────┼──────────────────────┘
                 ▼
        ┌────────────────┐
        │   Databases    │
        │ (Remote/Local) │
        └────────────────┘
```

### Client-Server Deployment

```
┌───────────────┐         ┌───────────────┐
│   Clients     │         │   AI-Shell    │
│  (Multiple)   │◄───────►│   Server      │
│               │  REST   │               │
└───────────────┘  API    └───────┬───────┘
                                  │
                         ┌────────┴────────┐
                         ▼                 ▼
                   ┌──────────┐    ┌──────────┐
                   │ Databases│    │   LLM    │
                   │  (Pool)  │    │ Service  │
                   └──────────┘    └──────────┘
```

### Enterprise Deployment

```
┌─────────────────────────────────────────────────────────┐
│              Load Balancer / API Gateway                │
└──────────┬─────────────────────────────┬────────────────┘
           │                             │
      ┌────▼────┐                   ┌───▼────┐
      │ AI-Shell│                   │AI-Shell│
      │ Instance│                   │Instance│
      │    1    │                   │   N    │
      └────┬────┘                   └───┬────┘
           │                            │
           └──────────┬─────────────────┘
                      ▼
           ┌──────────────────┐
           │  Shared Services │
           │ ┌──────────────┐ │
           │ │  Vault       │ │
           │ │  (Shared)    │ │
           │ └──────────────┘ │
           │ ┌──────────────┐ │
           │ │  Vector DB   │ │
           │ │  (Shared)    │ │
           │ └──────────────┘ │
           │ ┌──────────────┐ │
           │ │  Audit Log   │ │
           │ │  (Central)   │ │
           │ └──────────────┘ │
           └──────────────────┘
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
    ┌──────────┐         ┌──────────┐
    │ Database │         │   LLM    │
    │  Cluster │         │  Cluster │
    └──────────┘         └──────────┘
```

### Container Deployment (Docker)

```yaml
services:
  aishell:
    image: aishell:2.0.0
    environment:
      - AISHELL_CONFIG=/config/config.yaml
      - AISHELL_LOG_LEVEL=INFO
    volumes:
      - ./config:/config
      - ./vault:/vault
      - ./logs:/logs
    ports:
      - "8000:8000"  # API port

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ./models:/models

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=secure_password
```

---

## Extension Points

### Creating Custom Modules

```python
from src.core.base_module import BaseModule

class CustomModule(BaseModule):
    name = "custom"
    version = "1.0.0"

    async def initialize(self) -> bool:
        """Initialize module"""
        return True

    async def execute(self, command: str) -> dict:
        """Execute module command"""
        return {"result": "success"}

    async def shutdown(self) -> None:
        """Cleanup resources"""
        pass

# Register module
core.register_module(CustomModule())
```

### Creating Custom Agents

```python
from src.agents.base import BaseAgent

class CustomAgent(BaseAgent):
    async def plan(self, task: str) -> List[Step]:
        """Break task into steps"""
        return [
            Step(action="fetch_data", params={}),
            Step(action="process", params={}),
            Step(action="save", params={})
        ]

    async def execute_step(self, step: Step) -> Result:
        """Execute a single step"""
        # Your logic here
        return Result(success=True, data={})
```

### Creating Custom Tools

```python
from src.agents.tools.registry import tool_registry, RiskLevel

@tool_registry.register(
    category="data",
    risk_level=RiskLevel.MEDIUM,
    capabilities=["data_export"]
)
async def export_data(table: str, format: str) -> dict:
    """Export table data to file"""
    # Your implementation
    return {"status": "success", "file": "export.csv"}
```

### Creating Custom MCP Clients

```python
from src.mcp_clients.base import BaseMCPClient

class CustomDBClient(BaseMCPClient):
    async def connect(self, connection_string: str):
        """Connect to database"""
        self._connection = await custom_driver.connect(connection_string)

    async def execute(self, query: str) -> dict:
        """Execute query"""
        result = await self._connection.execute(query)
        return self._format_result(result)

    async def disconnect(self):
        """Close connection"""
        await self._connection.close()
```

---

## Design Decisions

### Why Asyncio?

**Decision:** Use asyncio for all I/O operations

**Rationale:**
- Non-blocking operations improve responsiveness
- Better resource utilization
- Native Python support (no external dependencies)
- Easier to reason about than threading

**Trade-offs:**
- Steeper learning curve
- Requires async libraries throughout
- Some legacy libraries need wrapping

### Why Textual for UI?

**Decision:** Use Textual instead of curses or terminal direct control

**Rationale:**
- Modern, reactive UI framework
- Better abstraction than curses
- Rich widget library
- Cross-platform compatibility
- Active development

**Trade-offs:**
- Larger dependency
- Requires Python 3.9+
- Learning curve for contributors

### Why FAISS for Vector Search?

**Decision:** Use FAISS instead of alternatives (Annoy, Hnswlib)

**Rationale:**
- Industry-standard for similarity search
- Excellent performance
- Facebook Research backing
- GPU support available
- Wide Python version support (3.9-3.14 with v1.12.0)

**Trade-offs:**
- Larger memory footprint
- Build complexity (C++ dependency)
- Overkill for small datasets

### Why Thin Database Clients?

**Decision:** Use thin database clients (no server-side installation)

**Rationale:**
- Easier deployment (no Oracle client needed!)
- Smaller footprint
- Better portability
- Faster startup

**Trade-offs:**
- Slightly slower than thick clients
- Limited advanced features
- Network overhead

---

## Future Architecture

### v2.1.0 Enhancements

1. **Multi-tenancy Support**
   - Tenant isolation
   - Resource quotas
   - Separate configurations

2. **Distributed Agent Coordination**
   - Agent communication protocol
   - Distributed state management
   - Consensus algorithms

3. **Advanced Caching**
   - Redis-backed distributed cache
   - Cache invalidation strategies
   - Cache warming

### v3.0.0 Vision

1. **Microservices Architecture**
   - Service mesh integration
   - gRPC communication
   - Service discovery

2. **Cloud-Native Design**
   - Kubernetes operators
   - Auto-scaling
   - Health probes

3. **Event Sourcing**
   - Complete audit trail
   - Event replay
   - CQRS pattern

---

## Appendix

### Technology Stack

**Core:**
- Python 3.9-3.14
- asyncio (standard library)
- typing (type hints)

**UI:**
- textual 0.47.1 (TUI framework)
- prompt-toolkit 3.0.43 (input handling)
- rich 13.7.0 (formatting)

**Database:**
- asyncpg 0.29.0 (PostgreSQL)
- python-oracledb 2.5.0 (Oracle)
- aiomysql 0.2.0 (MySQL)
- motor 3.3.2 (MongoDB)
- redis 5.0.1 (Redis)

**AI/ML:**
- faiss-cpu 1.9.0 (vector search)
- sentence-transformers 2.2.2 (embeddings)
- ollama 0.1.6 (local LLM)
- openai 1.7.2 (cloud LLM)
- anthropic 0.8.1 (cloud LLM)

**Security:**
- cryptography 41.0.7 (encryption)
- pydantic 2.5.3 (validation)

### Performance Tuning

**Memory:**
- Vector dimension: 384 (default)
- Cache size: 5000 queries
- Connection pool: 5-20 connections
- Max workers: 4 async workers

**Timeouts:**
- Health check: 2s per check
- Query execution: 30s
- Agent step: 60s
- LLM generation: 30s

### Monitoring Metrics

**Health:**
- Component availability
- Response times
- Error rates
- Resource usage

**Performance:**
- Query execution time
- Cache hit rate
- Connection pool usage
- Memory consumption

**Security:**
- Failed authentication attempts
- High-risk operations
- Approval rates
- Audit log volume

---

**Document Version:** 1.0.0
**Last Reviewed:** October 11, 2025
**Next Review:** January 2026
