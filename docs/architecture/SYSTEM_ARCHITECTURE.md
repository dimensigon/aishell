# AI-Shell System Architecture

## Executive Summary

AI-Shell is an intelligent command-line interface system that combines traditional CLI capabilities with AI-powered assistance through MCP (Model Context Protocol) integration and local LLM support. The architecture emphasizes modularity, extensibility, and performance while maintaining a clean separation of concerns.

## Architecture Overview

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ CLI Parser   │  │ REPL Shell   │  │ Output Formatter │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 Command Processing Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Command      │  │ Intent       │  │ Command          │  │
│  │ Interpreter  │  │ Classifier   │  │ Executor         │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   AI Integration Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ MCP Client   │  │ LLM Provider │  │ Context Manager  │  │
│  │ Manager      │  │ Abstraction  │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Provider Layer                            │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ MCP         │  │ Ollama       │  │ LlamaCPP/Other    │  │
│  │ Servers     │  │ Provider     │  │ Providers         │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Memory Store │  │ Config Mgmt  │  │ Plugin System    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. User Interface Layer

#### 1.1 CLI Parser
- **Responsibility**: Parse user input and command-line arguments
- **Technology**: Commander.js or Yargs
- **Key Features**:
  - Command syntax parsing
  - Flag/option handling
  - Subcommand routing
  - Input validation

#### 1.2 REPL Shell
- **Responsibility**: Interactive shell experience
- **Technology**: Inquirer.js or custom readline implementation
- **Key Features**:
  - Interactive prompts
  - Command history
  - Auto-completion
  - Multi-line input support

#### 1.3 Output Formatter
- **Responsibility**: Format and display results
- **Technology**: Chalk, Boxen, Table
- **Key Features**:
  - Syntax highlighting
  - Structured output (tables, trees)
  - Progress indicators
  - Error formatting

### 2. Command Processing Layer

#### 2.1 Command Interpreter
```typescript
interface CommandInterpreter {
  parse(input: string): ParsedCommand;
  validate(command: ParsedCommand): ValidationResult;
  enrich(command: ParsedCommand, context: Context): EnrichedCommand;
}

interface ParsedCommand {
  type: 'direct' | 'ai_assisted' | 'ai_generated';
  command: string;
  args: string[];
  flags: Record<string, any>;
  rawInput: string;
}
```

#### 2.2 Intent Classifier
```typescript
interface IntentClassifier {
  classify(input: string, context: Context): Intent;
  confidence(intent: Intent): number;
}

enum IntentType {
  DIRECT_COMMAND = 'direct_command',
  QUESTION = 'question',
  TASK_DESCRIPTION = 'task_description',
  CONTEXT_QUERY = 'context_query',
  SYSTEM_COMMAND = 'system_command'
}

interface Intent {
  type: IntentType;
  entities: Map<string, any>;
  confidence: number;
  suggestedAction: string;
}
```

#### 2.3 Command Executor
```typescript
interface CommandExecutor {
  execute(command: EnrichedCommand): Promise<ExecutionResult>;
  stream(command: EnrichedCommand): AsyncIterator<ExecutionChunk>;
  cancel(executionId: string): void;
}

interface ExecutionResult {
  success: boolean;
  output: string;
  error?: Error;
  metadata: ExecutionMetadata;
}
```

### 3. AI Integration Layer

#### 3.1 MCP Client Manager
```typescript
interface MCPClientManager {
  connect(serverConfig: MCPServerConfig): Promise<MCPClient>;
  listServers(): MCPServer[];
  executeRequest(server: string, request: MCPRequest): Promise<MCPResponse>;
  listResources(server: string): Promise<Resource[]>;
  listTools(server: string): Promise<Tool[]>;
}

interface MCPServerConfig {
  name: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
  autoStart?: boolean;
}

interface MCPClient {
  id: string;
  name: string;
  status: 'connected' | 'disconnected' | 'error';
  capabilities: Capabilities;
  sendRequest(request: MCPRequest): Promise<MCPResponse>;
  subscribe(event: string, handler: EventHandler): void;
}
```

#### 3.2 LLM Provider Abstraction
```typescript
interface LLMProvider {
  generate(prompt: string, options?: GenerationOptions): Promise<GenerationResult>;
  stream(prompt: string, options?: GenerationOptions): AsyncIterator<string>;
  embed(text: string): Promise<number[]>;
  models(): Promise<ModelInfo[]>;
}

interface GenerationOptions {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  stopSequences?: string[];
  systemPrompt?: string;
  tools?: Tool[];
}

// Concrete implementations
class OllamaProvider implements LLMProvider { }
class LlamaCPPProvider implements LLMProvider { }
class OpenAICompatibleProvider implements LLMProvider { }
```

#### 3.3 Context Manager
```typescript
interface ContextManager {
  getCurrentContext(): Context;
  updateContext(update: Partial<Context>): void;
  getHistory(limit?: number): HistoryEntry[];
  clearContext(): void;
  saveSnapshot(name: string): void;
  loadSnapshot(name: string): Context;
}

interface Context {
  workingDirectory: string;
  environment: Record<string, string>;
  history: HistoryEntry[];
  session: SessionInfo;
  mcpServers: MCPServerInfo[];
  activeProvider: string;
  variables: Record<string, any>;
}

interface HistoryEntry {
  id: string;
  timestamp: Date;
  input: string;
  output: string;
  intent: Intent;
  executionTime: number;
  success: boolean;
}
```

### 4. Provider Layer

#### 4.1 MCP Server Integration
```typescript
interface MCPServerAdapter {
  start(): Promise<void>;
  stop(): Promise<void>;
  health(): Promise<HealthStatus>;
  request<T>(method: string, params: any): Promise<T>;
}

class StdioMCPAdapter implements MCPServerAdapter {
  private process: ChildProcess;
  private messageQueue: MessageQueue;

  async start() {
    this.process = spawn(this.config.command, this.config.args);
    await this.initializeProtocol();
  }
}
```

#### 4.2 Ollama Provider
```typescript
class OllamaProvider implements LLMProvider {
  private baseUrl: string;
  private client: HttpClient;

  async generate(prompt: string, options?: GenerationOptions) {
    const response = await this.client.post('/api/generate', {
      model: options?.model || 'llama2',
      prompt,
      options: this.mapOptions(options)
    });
    return this.parseResponse(response);
  }

  async stream(prompt: string, options?: GenerationOptions) {
    const stream = await this.client.streamPost('/api/generate', {
      model: options?.model || 'llama2',
      prompt,
      stream: true
    });
    return this.parseStream(stream);
  }
}
```

#### 4.3 LlamaCPP Provider
```typescript
class LlamaCPPProvider implements LLMProvider {
  private modelPath: string;
  private nativeBinding: any;

  async generate(prompt: string, options?: GenerationOptions) {
    const result = await this.nativeBinding.complete({
      prompt,
      n_predict: options?.maxTokens || 512,
      temperature: options?.temperature || 0.7
    });
    return this.formatResult(result);
  }
}
```

### 5. Infrastructure Layer

#### 5.1 Memory Store
```typescript
interface MemoryStore {
  set(key: string, value: any, ttl?: number): Promise<void>;
  get<T>(key: string): Promise<T | null>;
  delete(key: string): Promise<void>;
  search(pattern: string): Promise<Array<{ key: string; value: any }>>;
  namespace(name: string): MemoryStore;
}

class SQLiteMemoryStore implements MemoryStore {
  private db: Database;
  private currentNamespace: string;

  namespace(name: string): MemoryStore {
    return new SQLiteMemoryStore(this.db, name);
  }
}
```

#### 5.2 Configuration Management
```typescript
interface ConfigManager {
  get<T>(path: string, defaultValue?: T): T;
  set(path: string, value: any): void;
  load(configPath: string): Promise<void>;
  save(configPath?: string): Promise<void>;
  validate(): ValidationResult;
}

interface AIShellConfig {
  llm: {
    defaultProvider: 'ollama' | 'llamacpp' | 'custom';
    providers: ProviderConfig[];
  };
  mcp: {
    servers: MCPServerConfig[];
    autoConnect: boolean;
  };
  interface: {
    theme: string;
    historySize: number;
    autoComplete: boolean;
  };
  plugins: {
    enabled: string[];
    paths: string[];
  };
}
```

#### 5.3 Plugin System
```typescript
interface Plugin {
  name: string;
  version: string;
  init(context: PluginContext): Promise<void>;
  commands?: CommandDefinition[];
  providers?: ProviderDefinition[];
  middleware?: Middleware[];
}

interface PluginContext {
  config: ConfigManager;
  memory: MemoryStore;
  logger: Logger;
  registerCommand(def: CommandDefinition): void;
  registerProvider(def: ProviderDefinition): void;
  registerMiddleware(middleware: Middleware): void;
}

interface PluginManager {
  load(pluginPath: string): Promise<Plugin>;
  unload(pluginName: string): void;
  list(): Plugin[];
  enable(pluginName: string): void;
  disable(pluginName: string): void;
}
```

## Data Flow Architecture

### Command Processing Pipeline

```
User Input
    ↓
┌────────────────┐
│ Input Parser   │ → Parse raw input
└────────────────┘
    ↓
┌────────────────┐
│ Intent         │ → Classify intent (direct/AI/query)
│ Classifier     │
└────────────────┘
    ↓
┌────────────────────────────────────┐
│ Decision Router                    │
│                                    │
│  ┌──────────┐  ┌──────────────┐  │
│  │ Direct   │  │ AI-Assisted  │  │
│  │ Execute  │  │ Processing   │  │
│  └──────────┘  └──────────────┘  │
└────────────────────────────────────┘
    ↓                    ↓
┌─────────┐      ┌──────────────────┐
│ System  │      │ LLM Provider     │
│ Execute │      │  ↓               │
└─────────┘      │ MCP Integration  │
    ↓            │  ↓               │
┌─────────┐      │ Command Gen      │
│ Output  │      └──────────────────┘
└─────────┘              ↓
    ↑            ┌───────────────┐
    └────────────│ Execute & Log │
                 └───────────────┘
```

### Context Flow

```
Session Start
    ↓
┌──────────────────┐
│ Load Context     │ ← Memory Store
│  - History       │
│  - Environment   │
│  - MCP Servers   │
└──────────────────┘
    ↓
┌──────────────────┐
│ Each Command     │
│  ↓               │
│ Update Context   │ → Memory Store
│  - Add history   │
│  - Update vars   │
└──────────────────┘
    ↓
┌──────────────────┐
│ Session End      │
│  ↓               │
│ Save Snapshot    │ → Persistent Store
└──────────────────┘
```

### MCP Integration Flow

```
AI-Shell Startup
    ↓
┌──────────────────────┐
│ MCP Server Discovery │ ← Config file
└──────────────────────┘
    ↓
┌──────────────────────┐
│ Auto-Start Servers   │
│  - Spawn processes   │
│  - Stdio connections │
└──────────────────────┘
    ↓
┌──────────────────────┐
│ Capability Exchange  │
│  - List tools        │
│  - List resources    │
│  - Register prompts  │
└──────────────────────┘
    ↓
┌──────────────────────┐
│ Runtime Requests     │
│  - Tool execution    │
│  - Resource access   │
│  - Prompt completion │
└──────────────────────┘
```

## Module Design

### Core Modules Structure

```
src/
├── core/
│   ├── cli/
│   │   ├── parser.ts          # Command parsing
│   │   ├── repl.ts            # Interactive shell
│   │   └── formatter.ts       # Output formatting
│   ├── command/
│   │   ├── interpreter.ts     # Command interpretation
│   │   ├── classifier.ts      # Intent classification
│   │   ├── executor.ts        # Command execution
│   │   └── pipeline.ts        # Processing pipeline
│   └── context/
│       ├── manager.ts         # Context management
│       ├── history.ts         # History tracking
│       └── session.ts         # Session handling
├── ai/
│   ├── mcp/
│   │   ├── client.ts          # MCP client implementation
│   │   ├── manager.ts         # Server management
│   │   ├── adapter.ts         # Protocol adapter
│   │   └── types.ts           # MCP type definitions
│   ├── llm/
│   │   ├── provider.ts        # Provider interface
│   │   ├── ollama.ts          # Ollama implementation
│   │   ├── llamacpp.ts        # LlamaCPP implementation
│   │   └── factory.ts         # Provider factory
│   └── orchestrator.ts        # AI orchestration layer
├── infrastructure/
│   ├── memory/
│   │   ├── store.ts           # Memory store interface
│   │   ├── sqlite.ts          # SQLite implementation
│   │   └── cache.ts           # Caching layer
│   ├── config/
│   │   ├── manager.ts         # Config management
│   │   ├── schema.ts          # Config schema
│   │   └── validator.ts       # Config validation
│   └── plugin/
│       ├── manager.ts         # Plugin management
│       ├── loader.ts          # Plugin loading
│       └── registry.ts        # Plugin registry
└── utils/
    ├── logger.ts              # Logging utilities
    ├── async.ts               # Async helpers
    └── errors.ts              # Error definitions
```

## Interface Contracts

### Core Service Interfaces

```typescript
// Service Locator Pattern
interface ServiceContainer {
  register<T>(token: string, factory: () => T): void;
  resolve<T>(token: string): T;
  singleton<T>(token: string, factory: () => T): void;
}

// Main Application Interface
interface AIShellApp {
  start(config?: Partial<AIShellConfig>): Promise<void>;
  stop(): Promise<void>;
  execute(command: string): Promise<ExecutionResult>;
  interactive(): Promise<void>;
}

// Command Processing Pipeline
interface Pipeline {
  use(middleware: Middleware): Pipeline;
  execute(input: PipelineInput): Promise<PipelineOutput>;
}

type Middleware = (
  input: PipelineInput,
  next: () => Promise<PipelineOutput>
) => Promise<PipelineOutput>;
```

## Extensibility Design

### Plugin Architecture

```typescript
// Example Plugin
export class DatabasePlugin implements Plugin {
  name = 'database';
  version = '1.0.0';

  async init(context: PluginContext) {
    // Register custom commands
    context.registerCommand({
      name: 'db',
      description: 'Database operations',
      handler: async (args) => {
        // Implementation
      }
    });

    // Register LLM provider
    context.registerProvider({
      name: 'custom-db-llm',
      factory: () => new CustomDBLLM()
    });

    // Register middleware
    context.registerMiddleware(async (input, next) => {
      // Pre-processing
      const result = await next();
      // Post-processing
      return result;
    });
  }
}
```

### Provider Extension

```typescript
// Custom LLM Provider
class CustomLLMProvider implements LLMProvider {
  async generate(prompt: string, options?: GenerationOptions) {
    // Custom implementation
  }

  async stream(prompt: string, options?: GenerationOptions) {
    // Custom streaming
  }

  async embed(text: string): Promise<number[]> {
    // Custom embeddings
  }

  async models(): Promise<ModelInfo[]> {
    // Available models
  }
}

// Register provider
pluginContext.registerProvider({
  name: 'custom-provider',
  factory: () => new CustomLLMProvider()
});
```

## Performance Considerations

### Async Processing

```typescript
// Parallel execution where possible
class AsyncCommandExecutor implements CommandExecutor {
  async execute(command: EnrichedCommand): Promise<ExecutionResult> {
    const [contextData, mcpTools, llmModels] = await Promise.all([
      this.context.getCurrentContext(),
      this.mcp.listTools(command.mcpServer),
      this.llm.models()
    ]);

    // Process with gathered data
    return this.processCommand(command, { contextData, mcpTools, llmModels });
  }
}
```

### Caching Strategy

```typescript
interface CacheStrategy {
  shouldCache(request: Request): boolean;
  getCacheKey(request: Request): string;
  getTTL(request: Request): number;
}

class SmartCache {
  private strategy: CacheStrategy;
  private store: Map<string, CachedItem>;

  async get<T>(key: string, factory: () => Promise<T>): Promise<T> {
    if (this.store.has(key) && !this.isExpired(key)) {
      return this.store.get(key).value;
    }

    const value = await factory();
    this.store.set(key, { value, timestamp: Date.now() });
    return value;
  }
}
```

### Streaming Support

```typescript
// Stream execution results
class StreamingExecutor {
  async *stream(command: EnrichedCommand): AsyncIterator<ExecutionChunk> {
    const llmStream = this.llm.stream(command.prompt);

    for await (const chunk of llmStream) {
      yield { type: 'llm_output', data: chunk };

      if (this.shouldExecuteCommand(chunk)) {
        const result = await this.executeSystemCommand(chunk);
        yield { type: 'command_output', data: result };
      }
    }
  }
}
```

## Security Considerations

### Command Validation

```typescript
interface SecurityPolicy {
  allowedCommands: string[];
  blockedPatterns: RegExp[];
  requireConfirmation: (command: string) => boolean;
  sanitize: (input: string) => string;
}

class SecurityValidator {
  validate(command: ParsedCommand, policy: SecurityPolicy): ValidationResult {
    // Check against policy
    if (policy.blockedPatterns.some(p => p.test(command.rawInput))) {
      return { valid: false, reason: 'Blocked pattern detected' };
    }

    // Sanitize input
    command.rawInput = policy.sanitize(command.rawInput);

    return { valid: true };
  }
}
```

### Sandboxing

```typescript
interface ExecutionEnvironment {
  isolate: boolean;
  allowedPaths: string[];
  allowedNetwork: boolean;
  timeoutMs: number;
}

class SandboxExecutor {
  async execute(command: string, env: ExecutionEnvironment): Promise<Result> {
    if (env.isolate) {
      return this.executeInContainer(command, env);
    }
    return this.executeDirect(command, env);
  }
}
```

## Error Handling Strategy

```typescript
// Error hierarchy
class AIShellError extends Error {
  constructor(
    message: string,
    public code: string,
    public recoverable: boolean = false
  ) {
    super(message);
  }
}

class MCPConnectionError extends AIShellError {
  constructor(serverName: string, cause?: Error) {
    super(
      `Failed to connect to MCP server: ${serverName}`,
      'MCP_CONNECTION_ERROR',
      true
    );
    this.cause = cause;
  }
}

// Error recovery
class ErrorRecoveryManager {
  async recover(error: AIShellError, context: Context): Promise<RecoveryResult> {
    if (!error.recoverable) {
      return { success: false, message: error.message };
    }

    const strategy = this.getRecoveryStrategy(error);
    return strategy.execute(context);
  }
}
```

## Testing Strategy

### Unit Testing
- Individual component testing
- Mock external dependencies
- Test all error paths

### Integration Testing
- MCP server integration
- LLM provider integration
- End-to-end command flow

### Performance Testing
- Benchmark command execution
- Memory usage profiling
- Concurrent request handling

## Deployment Architecture

### Local Installation
```bash
npm install -g ai-shell
ai-shell init
ai-shell config set llm.provider ollama
```

### MCP Server Configuration
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/path/to/allowed"]
    },
    "database": {
      "command": "npx",
      "args": ["@custom/mcp-database-server"]
    }
  }
}
```

## Future Extensibility

### Planned Extensions
1. **Multi-model Orchestration**: Coordinate multiple LLMs
2. **Agent Framework**: Build autonomous agents
3. **Visual Interface**: Web-based UI option
4. **Cloud Integration**: Remote MCP servers
5. **Collaborative Features**: Shared sessions

### Plugin Ecosystem
- Community plugin registry
- Plugin marketplace
- Template library
- Extension API documentation

## Architecture Decision Records (ADRs)

### ADR-001: MCP as Primary Integration Protocol
- **Decision**: Use MCP for tool/resource integration
- **Rationale**: Standard protocol, growing ecosystem
- **Consequences**: Requires MCP server implementations

### ADR-002: Provider Abstraction Layer
- **Decision**: Abstract LLM providers behind common interface
- **Rationale**: Support multiple backends without code changes
- **Consequences**: Additional abstraction overhead

### ADR-003: SQLite for Memory Store
- **Decision**: Use SQLite for persistent memory
- **Rationale**: Embedded, reliable, queryable
- **Consequences**: File-based storage, locking considerations

### ADR-004: Plugin-Based Extensibility
- **Decision**: Plugin architecture for extensibility
- **Rationale**: Community contributions, modularity
- **Consequences**: Plugin API maintenance burden

### ADR-005: Async-First Design
- **Decision**: Async/await throughout
- **Rationale**: Better performance, non-blocking I/O
- **Consequences**: More complex error handling

## Performance Targets

- **Command Latency**: < 100ms for direct commands
- **AI Response Time**: < 2s first token for local LLMs
- **Memory Usage**: < 100MB baseline
- **Startup Time**: < 500ms
- **Concurrent Requests**: Support 10+ parallel operations

## Success Metrics

- **User Engagement**: Daily active users
- **Command Success Rate**: > 95%
- **Error Recovery Rate**: > 80%
- **Plugin Adoption**: Number of community plugins
- **Performance**: Meet latency targets

---

**Architecture Version**: 1.0.0
**Last Updated**: 2025-10-03
**Status**: Initial Design
