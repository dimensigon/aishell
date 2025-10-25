# AI-Shell Architecture Summary

## Overview

AI-Shell is an intelligent command-line interface system that seamlessly integrates AI capabilities through MCP (Model Context Protocol) and local LLM providers. The architecture is designed for modularity, extensibility, and high performance.

## Architecture Documents

1. **[System Architecture](./SYSTEM_ARCHITECTURE.md)** - Comprehensive system design with layers, components, and interfaces
2. **[Module Specifications](./MODULE_SPECIFICATIONS.md)** - Detailed module implementations with code examples
3. **[C4 Diagrams](./C4_DIAGRAMS.md)** - Visual architecture diagrams at multiple abstraction levels

## Core Architecture

### Five-Layer Design

```
┌─────────────────────────────────┐
│   1. User Interface Layer       │  ← CLI Parser, REPL, Formatter
├─────────────────────────────────┤
│   2. Command Processing Layer   │  ← Interpreter, Classifier, Executor
├─────────────────────────────────┤
│   3. AI Integration Layer       │  ← MCP Client, LLM Provider, Orchestrator
├─────────────────────────────────┤
│   4. Provider Layer             │  ← MCP Servers, Ollama, LlamaCPP
├─────────────────────────────────┤
│   5. Infrastructure Layer       │  ← Memory, Config, Plugins
└─────────────────────────────────┘
```

### Key Components

#### User Interface
- **CLI Parser**: Command-line argument parsing with Commander.js
- **REPL Shell**: Interactive shell with autocomplete and history
- **Output Formatter**: Terminal output formatting with themes

#### Command Processing
- **Interpreter**: Converts raw input to structured commands
- **Intent Classifier**: ML-based classification (direct/AI/query/task)
- **Executor**: Async command execution with streaming support

#### AI Integration
- **MCP Client Manager**: Manages MCP server connections via stdio/HTTP/WebSocket
- **LLM Provider Abstraction**: Unified interface for Ollama, LlamaCPP, custom providers
- **AI Orchestrator**: Coordinates LLM inference with tool execution

#### Infrastructure
- **Memory Store**: SQLite-based persistent storage with namespaces
- **Config Manager**: JSON schema-validated configuration
- **Plugin System**: Dynamic plugin loading with lifecycle management

## Data Flow

```
User Input → Parser → Classifier → Router
                                      ├→ Direct Execution → System
                                      └→ AI Processing → LLM + MCP Tools → Result
```

## Key Design Patterns

### 1. Provider Pattern
All LLM providers implement a common interface:
```typescript
interface LLMProvider {
  generate(prompt: string, options?: GenerationOptions): Promise<GenerationResult>;
  stream(prompt: string, options?: GenerationOptions): AsyncIterator<string>;
  embed(text: string): Promise<number[]>;
  models(): Promise<ModelInfo[]>;
}
```

### 2. Plugin Architecture
Extensibility through plugins:
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

### 3. Pipeline Pattern
Command processing as composable middleware:
```typescript
interface Pipeline {
  use(middleware: Middleware): Pipeline;
  execute(input: PipelineInput): Promise<PipelineOutput>;
}
```

### 4. Service Container
Dependency injection for loose coupling:
```typescript
interface ServiceContainer {
  register<T>(token: string, factory: () => T): void;
  singleton<T>(token: string, factory: () => T): void;
  resolve<T>(token: string): T;
}
```

## MCP Integration

### Protocol Support
- **Stdio Transport**: For local Node.js/Python MCP servers
- **HTTP Transport**: For remote MCP services
- **WebSocket Transport**: For real-time MCP connections

### Capabilities
- **Tools**: Execute MCP-provided tools with argument passing
- **Resources**: Access file systems, databases, APIs
- **Prompts**: Utilize pre-built prompt templates

### Server Discovery
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/allowed/path"]
    },
    "database": {
      "command": "python",
      "args": ["-m", "mcp_database_server"]
    }
  }
}
```

## LLM Provider Support

### Ollama
- REST API integration (localhost:11434)
- Model management
- Streaming support
- Embeddings

### LlamaCPP
- Native C++ bindings
- Local model loading (GGUF)
- Low-latency inference
- Custom sampling

### Custom Providers
- Extensible provider interface
- OpenAI-compatible APIs
- Cloud LLM services

## Memory Architecture

### Namespace-Based Storage
```
swarm-ai-shell/
├── architecture/         # Architecture decisions
├── context/             # Session context
├── history/             # Command history
└── plugins/             # Plugin data
```

### Features
- SQLite-backed persistence
- TTL-based expiration
- Pattern-based search
- Cross-session memory

## Security Considerations

### Command Validation
- Blocked pattern detection
- Command sanitization
- Confirmation requirements
- Sandbox execution

### MCP Security
- Server authentication
- Capability negotiation
- Resource access control
- Input validation

## Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Command Latency | < 100ms | Async processing, caching |
| AI Response | < 2s first token | Local LLMs, streaming |
| Memory Usage | < 100MB | Efficient data structures |
| Startup Time | < 500ms | Lazy loading, pre-compilation |
| Concurrent Ops | 10+ parallel | Promise.all, worker threads |

## Architecture Decisions (ADRs)

### ADR-001: MCP as Primary Integration
- **Decision**: Use MCP for all tool/resource integration
- **Rationale**: Standard protocol, growing ecosystem, vendor-neutral
- **Trade-offs**: Requires MCP server implementations

### ADR-002: Provider Abstraction
- **Decision**: Abstract LLM providers behind common interface
- **Rationale**: Support multiple backends, easy switching, testability
- **Trade-offs**: Additional abstraction layer overhead

### ADR-003: SQLite for Memory
- **Decision**: Use SQLite for persistent storage
- **Rationale**: Embedded, zero-config, SQL capabilities, reliable
- **Trade-offs**: File-based, potential locking in high concurrency

### ADR-004: Plugin-Based Extensibility
- **Decision**: Plugin architecture for all extensions
- **Rationale**: Community contributions, modularity, isolation
- **Trade-offs**: API stability requirements, version management

### ADR-005: Async-First Design
- **Decision**: Async/await throughout codebase
- **Rationale**: Non-blocking I/O, better concurrency, modern Node.js
- **Trade-offs**: Complex error handling, debugging challenges

## Module Structure

```
src/
├── core/
│   ├── cli/              # User interface components
│   ├── command/          # Command processing
│   └── context/          # Context management
├── ai/
│   ├── mcp/              # MCP client implementation
│   ├── llm/              # LLM providers
│   └── orchestrator.ts   # AI coordination
├── infrastructure/
│   ├── memory/           # Memory store
│   ├── config/           # Configuration
│   └── plugin/           # Plugin system
└── utils/                # Shared utilities
```

## Extensibility Points

### 1. Custom Commands
```typescript
pluginContext.registerCommand({
  name: 'custom-cmd',
  description: 'Custom command',
  handler: async (args) => { /* implementation */ }
});
```

### 2. Custom Providers
```typescript
class CustomLLM implements LLMProvider {
  async generate(prompt: string) { /* implementation */ }
  async stream(prompt: string) { /* implementation */ }
}
```

### 3. Middleware
```typescript
pluginContext.registerMiddleware(async (input, next) => {
  // Pre-processing
  const result = await next();
  // Post-processing
  return result;
});
```

### 4. Custom MCP Servers
```typescript
const customServer: MCPServerConfig = {
  name: 'custom',
  command: 'node',
  args: ['./custom-mcp-server.js'],
  env: { API_KEY: process.env.API_KEY }
};
```

## Testing Strategy

### Unit Tests
- Component isolation
- Mock external dependencies
- Edge case coverage

### Integration Tests
- MCP server integration
- LLM provider integration
- End-to-end flows

### Performance Tests
- Benchmark command execution
- Memory profiling
- Concurrency stress tests

## Deployment

### Local Installation
```bash
npm install -g ai-shell
ai-shell init
ai-shell config set llm.provider ollama
ai-shell config add-mcp filesystem npx @modelcontextprotocol/server-filesystem
```

### Configuration
```json
{
  "llm": {
    "defaultProvider": "ollama",
    "providers": [
      {
        "name": "ollama",
        "type": "ollama",
        "config": { "baseUrl": "http://localhost:11434" }
      }
    ]
  },
  "mcp": {
    "autoConnect": true,
    "servers": { /* ... */ }
  },
  "plugins": {
    "enabled": ["@ai-shell/git", "@ai-shell/docker"],
    "paths": ["./local-plugins"]
  }
}
```

## Future Roadmap

### Phase 1: Core Features (v1.0)
- ✅ Basic CLI with async processing
- ✅ MCP client integration
- ✅ Ollama/LlamaCPP support
- ✅ Context management
- ✅ Plugin system

### Phase 2: Enhanced AI (v1.5)
- Multi-model orchestration
- Advanced tool calling
- Reasoning chains
- Memory optimization

### Phase 3: Ecosystem (v2.0)
- Plugin marketplace
- Cloud MCP servers
- Collaborative sessions
- Visual interface option

### Phase 4: Enterprise (v2.5)
- Team features
- Audit logging
- SSO integration
- Custom deployments

## Success Metrics

- **Adoption**: 10k+ installs in first 6 months
- **Reliability**: 95%+ command success rate
- **Performance**: Meet all latency targets
- **Community**: 50+ community plugins
- **Satisfaction**: 4.5+ star rating

## Resources

### Documentation
- [System Architecture](./SYSTEM_ARCHITECTURE.md)
- [Module Specifications](./MODULE_SPECIFICATIONS.md)
- [C4 Diagrams](./C4_DIAGRAMS.md)

### External References
- [MCP Specification](https://modelcontextprotocol.io)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [LlamaCPP](https://github.com/ggerganov/llama.cpp)

### Memory Storage
- **Namespace**: `swarm-ai-shell`
- **Key**: `architecture`
- **Location**: `.swarm/memory.db`

---

**Architecture Version**: 1.0.0
**Last Updated**: 2025-10-03
**Status**: Initial Design Complete
**Next Steps**: Module implementation, prototype development
