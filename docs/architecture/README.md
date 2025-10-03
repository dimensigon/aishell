# AI-Shell Architecture Documentation

## 📚 Documentation Index

This directory contains the complete architecture design for AI-Shell, an intelligent CLI system with MCP integration and local LLM support.

### Core Documents

1. **[Architecture Summary](./ARCHITECTURE_SUMMARY.md)** ⭐ START HERE
   - Executive overview
   - Quick reference guide
   - Key concepts and patterns
   - Success metrics

2. **[System Architecture](./SYSTEM_ARCHITECTURE.md)**
   - Detailed system design
   - Layer architecture (5 layers)
   - Component specifications
   - Interface contracts
   - ADRs (Architecture Decision Records)

3. **[Module Specifications](./MODULE_SPECIFICATIONS.md)**
   - Implementation details
   - TypeScript interfaces
   - Code examples
   - Integration patterns
   - Configuration schemas

4. **[C4 Diagrams](./C4_DIAGRAMS.md)**
   - System Context diagram
   - Container diagram
   - Component diagrams
   - Sequence diagrams
   - Deployment diagram

5. **[Interaction Patterns](./INTERACTION_PATTERNS.md)**
   - Command flow patterns
   - MCP integration workflows
   - Error handling strategies
   - Performance optimizations
   - Security patterns

## 🏗️ Architecture Overview

### Five-Layer Design

```
┌─────────────────────────────────────────────────────┐
│ 1. User Interface Layer                             │
│    CLI Parser, REPL Shell, Output Formatter         │
├─────────────────────────────────────────────────────┤
│ 2. Command Processing Layer                         │
│    Interpreter, Intent Classifier, Executor         │
├─────────────────────────────────────────────────────┤
│ 3. AI Integration Layer                             │
│    MCP Client Manager, LLM Provider, Orchestrator   │
├─────────────────────────────────────────────────────┤
│ 4. Provider Layer                                   │
│    MCP Servers, Ollama, LlamaCPP, Custom Providers  │
├─────────────────────────────────────────────────────┤
│ 5. Infrastructure Layer                             │
│    Memory Store, Config Manager, Plugin System      │
└─────────────────────────────────────────────────────┘
```

### Key Features

- ✅ **MCP Integration**: Standard protocol for tools and resources
- ✅ **Local LLM Support**: Ollama, LlamaCPP, custom providers
- ✅ **Context Management**: Session-aware with persistent memory
- ✅ **Plugin Architecture**: Extensible via plugins
- ✅ **Async Processing**: High-performance concurrent execution
- ✅ **Security**: Command validation and sandboxing
- ✅ **Streaming**: Real-time AI responses

## 🚀 Quick Start

### For Developers

1. Read [Architecture Summary](./ARCHITECTURE_SUMMARY.md) for overview
2. Review [System Architecture](./SYSTEM_ARCHITECTURE.md) for design decisions
3. Study [Module Specifications](./MODULE_SPECIFICATIONS.md) for implementation
4. Check [C4 Diagrams](./C4_DIAGRAMS.md) for visual reference
5. Explore [Interaction Patterns](./INTERACTION_PATTERNS.md) for workflows

### For Architects

1. Start with [C4 Diagrams](./C4_DIAGRAMS.md) for visual overview
2. Review [Architecture Summary](./ARCHITECTURE_SUMMARY.md) for ADRs
3. Deep dive [System Architecture](./SYSTEM_ARCHITECTURE.md) for rationale

### For Implementers

1. Begin with [Module Specifications](./MODULE_SPECIFICATIONS.md)
2. Reference [Interaction Patterns](./INTERACTION_PATTERNS.md) for flows
3. Use [System Architecture](./SYSTEM_ARCHITECTURE.md) for context

## 📊 Architecture Metrics

| Metric | Target | Strategy |
|--------|--------|----------|
| Command Latency | < 100ms | Async processing, caching |
| AI Response | < 2s first token | Local LLMs, streaming |
| Memory Usage | < 100MB | Efficient data structures |
| Startup Time | < 500ms | Lazy loading |
| Concurrent Ops | 10+ parallel | Promise.all, workers |

## 🔑 Key Components

### Core Modules

- **CLI Parser** (`src/core/cli/parser.ts`) - Command parsing
- **REPL Shell** (`src/core/cli/repl.ts`) - Interactive shell
- **Interpreter** (`src/core/command/interpreter.ts`) - Command interpretation
- **Classifier** (`src/core/command/classifier.ts`) - Intent classification
- **Executor** (`src/core/command/executor.ts`) - Command execution

### AI Integration

- **MCP Client** (`src/ai/mcp/client.ts`) - MCP protocol implementation
- **MCP Manager** (`src/ai/mcp/manager.ts`) - Server management
- **Ollama Provider** (`src/ai/llm/ollama.ts`) - Ollama integration
- **LlamaCPP Provider** (`src/ai/llm/llamacpp.ts`) - LlamaCPP integration
- **Orchestrator** (`src/ai/orchestrator.ts`) - AI coordination

### Infrastructure

- **Memory Store** (`src/infrastructure/memory/sqlite.ts`) - Persistent storage
- **Config Manager** (`src/infrastructure/config/manager.ts`) - Configuration
- **Plugin Manager** (`src/infrastructure/plugin/manager.ts`) - Plugin system

## 🔌 Extensibility

### Plugin Interface

```typescript
interface Plugin {
  name: string;
  version: string;
  init(context: PluginContext): Promise<void>;
  commands?: CommandDefinition[];
  providers?: ProviderDefinition[];
  middleware?: Middleware[];
}
```

### Provider Interface

```typescript
interface LLMProvider {
  generate(prompt: string, options?: GenerationOptions): Promise<GenerationResult>;
  stream(prompt: string, options?: GenerationOptions): AsyncIterator<string>;
  embed(text: string): Promise<number[]>;
  models(): Promise<ModelInfo[]>;
}
```

## 🛡️ Security

### Command Validation
- Pattern-based blocking
- Input sanitization
- Privilege checks
- Optional sandboxing

### MCP Security
- Server authentication
- Capability negotiation
- Resource access control
- Path validation

## 📈 Performance

### Optimization Strategies

1. **Parallel Execution** - Independent operations via Promise.all
2. **Smart Caching** - LLM response caching with TTL
3. **Streaming** - Real-time output for AI responses
4. **Lazy Loading** - On-demand module loading
5. **Connection Pooling** - Reuse MCP connections

## 🧪 Testing

### Test Coverage

- **Unit Tests** - Component isolation, mocks, edge cases
- **Integration Tests** - MCP servers, LLM providers, E2E flows
- **Performance Tests** - Benchmarks, profiling, stress tests

## 📋 ADRs (Architecture Decision Records)

1. **ADR-001**: MCP as Primary Integration Protocol
2. **ADR-002**: Provider Abstraction Layer
3. **ADR-003**: SQLite for Memory Store
4. **ADR-004**: Plugin-Based Extensibility
5. **ADR-005**: Async-First Design

See [System Architecture](./SYSTEM_ARCHITECTURE.md#architecture-decision-records-adrs) for details.

## 🗂️ Project Structure

```
src/
├── core/
│   ├── cli/              # User interface
│   ├── command/          # Command processing
│   └── context/          # Context management
├── ai/
│   ├── mcp/              # MCP integration
│   ├── llm/              # LLM providers
│   └── orchestrator.ts   # AI coordination
├── infrastructure/
│   ├── memory/           # Storage
│   ├── config/           # Configuration
│   └── plugin/           # Plugins
└── utils/                # Utilities
```

## 🔄 Data Flow

```
Input → Parse → Classify → Route
                              ├→ Direct → System Execute
                              └→ AI → LLM + MCP Tools → Result
```

## 🌟 Example Workflows

### Direct Command
```bash
ai-shell> ls -la /home/user
# Executes directly, < 50ms
```

### AI-Assisted
```bash
ai-shell> what are the largest files here?
# AI generates: du -ah . | sort -rh | head -n 10
# Executes and shows results
```

### Tool Calling
```bash
ai-shell> backup database and compress
# AI orchestrates:
# 1. database:backup() via MCP
# 2. filesystem:compress() via MCP
# Returns aggregated results
```

## 📖 Related Documentation

- **MCP Specification**: https://modelcontextprotocol.io
- **Ollama API**: https://github.com/ollama/ollama/blob/main/docs/api.md
- **LlamaCPP**: https://github.com/ggerganov/llama.cpp

## 💾 Memory Storage

Architecture details stored in swarm memory:
- **Namespace**: `swarm-ai-shell`
- **Key**: `architecture`
- **Location**: `.swarm/memory.db`

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-03 | Initial architecture design |

## 🎯 Next Steps

1. **Implementation Phase**
   - Core module development
   - MCP client implementation
   - LLM provider integration

2. **Testing Phase**
   - Unit test coverage
   - Integration testing
   - Performance benchmarks

3. **Documentation Phase**
   - API documentation
   - User guides
   - Plugin development guide

---

**Architecture Status**: ✅ Complete
**Last Updated**: 2025-10-03
**Maintained By**: AI-Shell Architecture Team
