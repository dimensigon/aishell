# Module Dependency Graph

**Project:** AIShell
**Generated:** 2025-10-25
**Purpose:** Visual dependency mapping for development planning

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
│  - CLI REPL (TypeScript)                                        │
│  - Terminal UI (Python/Textual)                                 │
│  - Web API (FastAPI + GraphQL)                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                      Application Layer                           │
│  - Command Processor                                            │
│  - Async Queue System                                           │
│  - Configuration Manager                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────┴──────┐ ┌─────┴──────┐ ┌─────┴──────────┐
│   MCP Layer   │ │  LLM Layer │ │  Agent Layer   │
│               │ │            │ │                │
│ - Client      │ │ - Providers│ │ - BaseAgent    │
│ - Messages    │ │ - Factory  │ │ - Coordinator  │
│ - Types       │ │ - Context  │ │ - Tools        │
└───────┬───────┘ └─────┬──────┘ └─────┬──────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────────┐
│                      Database Layer                              │
│  - Oracle Client                                                │
│  - PostgreSQL Client                                            │
│  - MySQL Client                                                 │
│  - MongoDB Client                                               │
│  - Redis Client                                                 │
│  - Connection Manager                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## TypeScript Module Dependencies

### CLI Module (`src/cli/`)
```
cli/index.ts (AIShell)
├── Depends on:
│   ├── core/config.ts (ConfigManager)
│   ├── core/processor.ts (CommandProcessor)
│   ├── core/queue.ts (AsyncCommandQueue)
│   └── types/index.ts (REPLState, CommandContext)
└── Provides:
    ├── REPL interface
    ├── Command mode execution
    └── Signal handling
```

### Core Module (`src/core/`)
```
core/config.ts (ConfigManager)
├── Depends on:
│   ├── fs (native)
│   └── path (native)
└── Provides:
    └── Configuration loading/saving

core/processor.ts (CommandProcessor)
├── Depends on:
│   ├── child_process (native)
│   └── types/index.ts
└── Provides:
    ├── Command execution
    ├── Command parsing
    └── Built-in command handling

core/queue.ts (AsyncCommandQueue)
├── Depends on:
│   ├── events (native)
│   ├── types/index.ts
│   └── core/processor.ts
└── Provides:
    ├── Priority queue
    ├── Concurrency control
    └── Rate limiting
```

### MCP Module (`src/mcp/`)
```
mcp/client.ts (MCPClient)
├── Depends on:
│   ├── eventemitter3
│   ├── child_process (native)
│   ├── mcp/types.ts
│   └── mcp/messages.ts
└── Provides:
    ├── Multi-server connection management
    ├── Request/response handling
    ├── Automatic reconnection
    └── Context synchronization

mcp/types.ts
├── Depends on:
│   └── eventemitter3
└── Provides:
    ├── MCPMessage
    ├── MCPServerConfig
    ├── MCPTool
    ├── MCPResource
    └── ConnectionState

mcp/messages.ts (MCPMessageBuilder)
├── Depends on:
│   ├── uuid
│   └── mcp/types.ts
└── Provides:
    ├── Message construction
    ├── Message serialization
    └── Message parsing

mcp/context-adapter.ts
├── Depends on:
│   └── mcp/types.ts
└── Provides:
    └── Context format conversion

mcp/error-handler.ts
├── Depends on:
│   └── mcp/types.ts
└── Provides:
    └── MCP error handling

mcp/resource-manager.ts
├── Depends on:
│   └── mcp/types.ts
└── Provides:
    └── Resource lifecycle management
```

### LLM Module (`src/llm/`)
```
llm/provider.ts (ILLMProvider, BaseLLMProvider)
├── Depends on:
│   └── types/llm.ts
└── Provides:
    └── LLM provider interface

llm/provider-factory.ts
├── Depends on:
│   ├── llm/provider.ts
│   └── llm/providers/*
└── Provides:
    └── Provider instantiation

llm/providers/ollama.ts (OllamaProvider)
├── Depends on:
│   ├── axios
│   ├── llm/provider.ts
│   └── types/llm.ts
└── Provides:
    └── Ollama integration

llm/providers/llamacpp.ts (LlamaCppProvider)
├── Depends on:
│   ├── axios
│   ├── llm/provider.ts
│   └── types/llm.ts
└── Provides:
    └── LlamaCPP integration

llm/providers/gpt4all.ts (GPT4AllProvider)
├── Depends on:
│   ├── axios
│   ├── llm/provider.ts
│   └── types/llm.ts
└── Provides:
    └── GPT4All integration

llm/providers/localai.ts (LocalAIProvider)
├── Depends on:
│   ├── axios
│   ├── llm/provider.ts
│   └── types/llm.ts
└── Provides:
    └── LocalAI integration

llm/context-formatter.ts
├── Depends on:
│   └── types/llm.ts
└── Provides:
    └── Context formatting

llm/response-parser.ts
├── Depends on:
│   └── types/llm.ts
└── Provides:
    └── Response parsing
```

### Types Module (`src/types/`)
```
types/index.ts
├── Depends on: (none)
└── Provides:
    ├── CommandResult
    ├── CommandContext
    ├── ShellConfig
    ├── QueuedCommand
    ├── REPLState
    └── PluginInterface

types/llm.ts
├── Depends on: (none)
└── Provides:
    ├── LLMMessage
    ├── LLMResponse
    ├── GenerateOptions
    └── StreamCallback
```

---

## Python Module Dependencies

### Agent Module (`src/agents/`)
```
agents/base.py (BaseAgent)
├── Depends on:
│   ├── abc (native)
│   ├── dataclasses (native)
│   └── asyncio (native)
└── Provides:
    ├── AgentState
    ├── AgentCapability
    ├── AgentConfig
    ├── TaskContext
    ├── TaskResult
    └── BaseAgent (ABC)

agents/coordinator.py
├── Depends on:
│   ├── concurrent.futures (native)
│   ├── threading (native)
│   └── dataclasses (native)
└── Provides:
    ├── AgentCoordinator
    ├── AgentMessage
    ├── WorkflowRecovery
    └── ParallelExecutor

agents/workflow_orchestrator.py
├── Depends on:
│   ├── agents/base.py
│   └── agents/coordinator.py
└── Provides:
    └── Workflow orchestration

agents/tools/registry.py
├── Depends on:
│   └── typing (native)
└── Provides:
    └── Tool registration and discovery

agents/state/manager.py
├── Depends on:
│   ├── typing (native)
│   └── dataclasses (native)
└── Provides:
    └── State persistence and checkpointing

agents/database/optimizer.py
├── Depends on:
│   ├── agents/base.py
│   └── agents/tools/optimizer_tools.py
└── Provides:
    └── Query optimization agent

agents/database/migration.py
├── Depends on:
│   ├── agents/base.py
│   └── agents/tools/migration_tools.py
└── Provides:
    └── Schema migration agent

agents/database/backup.py
├── Depends on:
│   ├── agents/base.py
│   └── agents/database/backup_manager.py
└── Provides:
    └── Backup/restore agent

agents/safety/controller.py
├── Depends on:
│   └── agents/base.py
└── Provides:
    └── Safety validation
```

### Database Client Module (`src/mcp_clients/`)
```
mcp_clients/base.py (MCPClient)
├── Depends on:
│   ├── abc (native)
│   └── enum (native)
└── Provides:
    ├── MCPClient (ABC)
    ├── MCPClientError
    └── ConnectionState

mcp_clients/oracle_client.py (OracleClient)
├── Depends on:
│   ├── mcp_clients/base.py
│   └── oracledb (external)
└── Provides:
    └── Oracle database integration

mcp_clients/postgresql_client.py (PostgreSQLClient)
├── Depends on:
│   ├── mcp_clients/base.py
│   └── psycopg2 (external)
└── Provides:
    └── PostgreSQL integration

mcp_clients/mysql_client.py (MySQLClient)
├── Depends on:
│   ├── mcp_clients/base.py
│   └── mysql-connector (external)
└── Provides:
    └── MySQL integration

mcp_clients/mongodb_client.py (MongoDBClient)
├── Depends on:
│   ├── mcp_clients/base.py
│   └── pymongo (external)
└── Provides:
    └── MongoDB integration

mcp_clients/redis_client.py (RedisClient)
├── Depends on:
│   ├── mcp_clients/base.py
│   └── redis (external)
└── Provides:
    └── Redis integration

mcp_clients/manager.py (ConnectionManager)
├── Depends on:
│   └── mcp_clients/base.py
└── Provides:
    └── Connection pooling and lifecycle
```

### AI Module (`src/ai/`)
```
ai/query_assistant.py
├── Depends on:
│   └── typing (native)
└── Provides:
    └── LLM-powered query assistance

ai/prompt_templates.py
├── Depends on: (none)
└── Provides:
    └── Prompt template library

ai/conversation_manager.py
├── Depends on:
│   └── typing (native)
└── Provides:
    └── Conversation state management
```

### Cognitive Module (`src/cognitive/`)
```
cognitive/pattern_recognition.py
├── Depends on:
│   └── typing (native)
└── Provides:
    └── Usage pattern analysis

cognitive/learning.py
├── Depends on:
│   └── typing (native)
└── Provides:
    └── Learning algorithms

cognitive/recommendations.py
├── Depends on:
│   └── typing (native)
└── Provides:
    └── Query recommendations
```

---

## Cross-Language Dependencies

### TypeScript → Python
```
CLI (TS) → Python Agents
├── Method: Subprocess spawn
├── Communication: JSON-RPC over stdio
└── Use case: Agent task execution

MCP Client (TS) → Database Clients (Python)
├── Method: MCP protocol
├── Communication: JSON-RPC 2.0
└── Use case: Database operations
```

### Python → TypeScript
```
Agents (Python) → LLM Providers (TS)
├── Method: HTTP API
├── Communication: REST/JSON
└── Use case: LLM inference

Database Clients (Python) → MCP Client (TS)
├── Method: MCP protocol
├── Communication: JSON-RPC 2.0
└── Use case: Tool exposure
```

---

## External Dependencies

### TypeScript Dependencies
```
Production:
├── @anthropic-ai/sdk: ^0.32.1
├── @modelcontextprotocol/sdk: ^0.5.0
├── axios: ^1.6.0
├── eventemitter3: ^5.0.1
├── uuid: ^9.0.1
└── ws: ^8.16.0

Development:
├── @types/node: ^20.11.0
├── @types/uuid: ^9.0.7
├── @types/ws: ^8.5.10
├── @typescript-eslint/eslint-plugin: ^6.19.0
├── @typescript-eslint/parser: ^6.19.0
├── eslint: ^8.56.0
├── jest: ^29.7.0
├── ts-jest: ^29.1.2
├── ts-node: ^10.9.2
└── typescript: ^5.3.3
```

### Python Dependencies
```
Production:
├── oracledb
├── psycopg2
├── mysql-connector
├── pymongo
├── redis
├── fastapi
├── uvicorn
├── graphene
├── anthropic
└── textual

Development:
├── pytest
├── pytest-asyncio
├── pytest-cov
├── black
├── mypy
└── pylint
```

---

## Dependency Flow Diagram

```
User Input
    ↓
┌───────────────┐
│  CLI (TS)     │
└───────┬───────┘
        │
        ├──→ ConfigManager → config.json
        │
        ├──→ CommandProcessor → spawn process
        │       ↓
        │   ┌─────────────┐
        │   │ Child Proc  │
        │   └─────────────┘
        │
        └──→ AsyncCommandQueue
                ↓
        ┌───────┴──────┐
        │              │
    ┌───┴───┐    ┌────┴────┐
    │  MCP  │    │   LLM   │
    │Client │    │Provider │
    └───┬───┘    └────┬────┘
        │             │
        │             └──→ Ollama/LlamaCPP
        │                  └──→ HTTP API
        │
        └──→ MCP Servers (Python)
                ↓
        ┌───────┴───────┐
        │               │
    ┌───┴────┐    ┌────┴─────┐
    │ Agents │    │ Database │
    │        │    │ Clients  │
    └───┬────┘    └────┬─────┘
        │              │
        │              └──→ Oracle/PostgreSQL/MySQL
        │
        └──→ Tools Registry
                ↓
            Tool Execution
```

---

## Circular Dependencies (WARNINGS)

### ⚠️ Potential Issues

```
❌ AVOID:
CommandProcessor ←→ AsyncCommandQueue
(Currently: Queue depends on Processor ✅)

❌ AVOID:
MCPClient ←→ ServerConnection
(Currently: Connection is internal to Client ✅)

❌ AVOID:
BaseAgent ←→ StateManager
(Currently: Agent depends on Manager ✅)
```

### ✅ Current State: No Circular Dependencies

---

## Dependency Injection Points

### Recommended DI Patterns

```typescript
// 1. Constructor Injection
class MCPClient {
  constructor(
    private config: MCPClientConfig,
    private logger?: Logger,
    private metrics?: MetricsCollector
  ) {}
}

// 2. Factory Injection
class ProviderFactory {
  createProvider(type: string, config: ProviderConfig): ILLMProvider {
    switch (type) {
      case 'ollama': return new OllamaProvider(config);
      case 'llamacpp': return new LlamaCppProvider(config);
      // ...
    }
  }
}

// 3. Service Container (Future)
class Container {
  register<T>(key: string, factory: () => T): void;
  resolve<T>(key: string): T;
}
```

---

## Module Load Order

### Initialization Sequence

```
1. Load Configuration
   ↓
2. Initialize Core Services
   ├── Logger
   ├── Metrics
   └── Config Manager
   ↓
3. Initialize Providers
   ├── LLM Providers
   └── Database Clients
   ↓
4. Initialize MCP Client
   ├── Connect to servers
   └── Initialize context
   ↓
5. Initialize Command System
   ├── Command Processor
   └── Async Queue
   ↓
6. Initialize CLI/UI
   └── Start REPL or API server
```

---

## Testing Dependencies

### Test Utilities
```
tests/mocks/
├── mockMCPServer.ts → mcp/client.ts
├── mockLLMProvider.ts → llm/provider.ts
└── testHelpers.ts → (various)

tests/setup.ts
└── Global test configuration
```

---

**End of Dependency Graph**

*Use this document to understand module relationships and plan refactoring*
