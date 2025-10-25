# AI-Shell Module Specifications

## Core Modules

### 1. CLI Module (`src/core/cli/`)

#### parser.ts
```typescript
export interface CLIParser {
  parse(argv: string[]): ParseResult;
  parseInteractive(line: string): ParseResult;
}

export interface ParseResult {
  command: string;
  subcommand?: string;
  args: string[];
  flags: Map<string, any>;
  isAIRequest: boolean;
  rawInput: string;
}

export class CommandParser implements CLIParser {
  private grammar: Grammar;
  private aiPatterns: RegExp[];

  constructor(config: ParserConfig) {
    this.grammar = this.buildGrammar(config);
    this.aiPatterns = [
      /^(how|what|why|when|where|can|should|would)/i,
      /^(help me|show me|explain)/i,
      /\?$/
    ];
  }

  parse(argv: string[]): ParseResult {
    const program = new Command();
    // Configure commander.js
    return this.parseProgram(program, argv);
  }

  parseInteractive(line: string): ParseResult {
    if (this.isAIRequest(line)) {
      return {
        command: 'ai',
        args: [line],
        flags: new Map(),
        isAIRequest: true,
        rawInput: line
      };
    }
    return this.parseCommandLine(line);
  }

  private isAIRequest(input: string): boolean {
    return this.aiPatterns.some(p => p.test(input));
  }
}
```

#### repl.ts
```typescript
export interface REPLShell {
  start(): Promise<void>;
  stop(): void;
  evaluate(line: string): Promise<void>;
}

export class InteractiveShell implements REPLShell {
  private rl: readline.Interface;
  private history: string[] = [];
  private completer: AutoCompleter;

  constructor(
    private executor: CommandExecutor,
    private formatter: OutputFormatter,
    private config: REPLConfig
  ) {
    this.setupReadline();
    this.setupCompleter();
  }

  async start(): Promise<void> {
    this.displayWelcome();
    this.prompt();

    this.rl.on('line', async (line) => {
      await this.evaluate(line);
      this.prompt();
    });
  }

  async evaluate(line: string): Promise<void> {
    this.history.push(line);

    try {
      const result = await this.executor.execute(
        await this.parser.parseInteractive(line)
      );
      this.formatter.display(result);
    } catch (error) {
      this.formatter.displayError(error);
    }
  }

  private setupCompleter(): void {
    this.completer = new AutoCompleter({
      commands: this.getAvailableCommands(),
      mcpTools: this.getMCPTools(),
      history: this.history
    });
  }

  private getCompletions(line: string): string[] {
    return this.completer.complete(line);
  }
}

export class AutoCompleter {
  constructor(private sources: CompletionSources) {}

  complete(partial: string): string[] {
    const tokens = partial.split(' ');
    const lastToken = tokens[tokens.length - 1];

    if (tokens.length === 1) {
      return this.completeCommand(lastToken);
    }

    return this.completeArgument(tokens);
  }

  private completeCommand(partial: string): string[] {
    return [
      ...this.sources.commands,
      ...this.sources.mcpTools.map(t => `mcp:${t}`)
    ].filter(c => c.startsWith(partial));
  }
}
```

#### formatter.ts
```typescript
export interface OutputFormatter {
  display(result: ExecutionResult): void;
  displayError(error: Error): void;
  displayStream(stream: AsyncIterator<ExecutionChunk>): Promise<void>;
}

export class ConsoleFormatter implements OutputFormatter {
  private theme: Theme;

  constructor(config: FormatterConfig) {
    this.theme = this.loadTheme(config.theme);
  }

  display(result: ExecutionResult): void {
    if (result.format === 'table') {
      this.displayTable(result.data);
    } else if (result.format === 'tree') {
      this.displayTree(result.data);
    } else {
      this.displayText(result.output);
    }

    if (result.metadata) {
      this.displayMetadata(result.metadata);
    }
  }

  displayError(error: Error): void {
    console.error(
      chalk.red('✗ Error: ') + chalk.dim(error.message)
    );

    if (error instanceof AIShellError && error.suggestion) {
      console.log(chalk.yellow('\n💡 Suggestion: ') + error.suggestion);
    }
  }

  async displayStream(stream: AsyncIterator<ExecutionChunk>): Promise<void> {
    for await (const chunk of stream) {
      if (chunk.type === 'llm_output') {
        process.stdout.write(chalk.cyan(chunk.data));
      } else if (chunk.type === 'command_output') {
        console.log('\n' + this.formatCommandOutput(chunk.data));
      }
    }
  }

  private displayTable(data: any[]): void {
    const table = new Table({
      head: Object.keys(data[0]).map(k => chalk.cyan(k)),
      style: { head: [], border: [] }
    });

    data.forEach(row => {
      table.push(Object.values(row));
    });

    console.log(table.toString());
  }
}
```

### 2. Command Module (`src/core/command/`)

#### interpreter.ts
```typescript
export interface CommandInterpreter {
  interpret(parsed: ParseResult): InterpretedCommand;
  enrich(command: InterpretedCommand, context: Context): EnrichedCommand;
}

export class SmartInterpreter implements CommandInterpreter {
  constructor(
    private classifier: IntentClassifier,
    private contextManager: ContextManager
  ) {}

  interpret(parsed: ParseResult): InterpretedCommand {
    const intent = this.classifier.classify(
      parsed.rawInput,
      this.contextManager.getCurrentContext()
    );

    return {
      parsed,
      intent,
      requiresAI: intent.type !== IntentType.DIRECT_COMMAND,
      suggestedAction: this.determineSuggestedAction(intent)
    };
  }

  enrich(command: InterpretedCommand, context: Context): EnrichedCommand {
    return {
      ...command,
      context: {
        workingDirectory: context.workingDirectory,
        environment: context.environment,
        history: context.history.slice(-5), // Last 5 commands
        mcpCapabilities: this.getMCPCapabilities(context)
      },
      timestamp: Date.now()
    };
  }

  private determineSuggestedAction(intent: Intent): string {
    switch (intent.type) {
      case IntentType.QUESTION:
        return 'query_llm';
      case IntentType.TASK_DESCRIPTION:
        return 'generate_commands';
      case IntentType.CONTEXT_QUERY:
        return 'search_context';
      default:
        return 'execute_direct';
    }
  }
}
```

#### classifier.ts
```typescript
export interface IntentClassifier {
  classify(input: string, context: Context): Intent;
  train(examples: TrainingExample[]): void;
}

export class MLIntentClassifier implements IntentClassifier {
  private model: ClassificationModel;
  private vectorizer: Vectorizer;

  constructor() {
    this.vectorizer = new TFIDFVectorizer();
    this.model = this.loadPretrainedModel();
  }

  classify(input: string, context: Context): Intent {
    const features = this.extractFeatures(input, context);
    const prediction = this.model.predict(features);

    return {
      type: this.mapPredictionToIntent(prediction.class),
      confidence: prediction.confidence,
      entities: this.extractEntities(input),
      suggestedAction: this.mapToAction(prediction.class)
    };
  }

  private extractFeatures(input: string, context: Context): Features {
    return {
      // Linguistic features
      tokens: this.tokenize(input),
      embeddings: this.vectorizer.transform(input),

      // Syntactic features
      hasQuestionMark: input.includes('?'),
      startsWithQuestion: /^(how|what|why|when|where)/i.test(input),
      hasImperativeVerb: this.hasImperativeVerb(input),

      // Contextual features
      previousCommandType: context.history[0]?.intent.type,
      similarToPrevious: this.computeSimilarity(
        input,
        context.history[0]?.input
      ),

      // Domain features
      containsFilePath: this.containsFilePath(input),
      containsGitTerms: this.containsGitTerms(input),
      containsDBTerms: this.containsDBTerms(input)
    };
  }

  private extractEntities(input: string): Map<string, any> {
    const entities = new Map();

    // File paths
    const filePaths = input.match(/[\/\w.-]+\.(js|ts|py|md|json)/g);
    if (filePaths) entities.set('files', filePaths);

    // Commands
    const commands = input.match(/\b(git|npm|docker|kubectl)\s+\w+/g);
    if (commands) entities.set('commands', commands);

    // Numbers
    const numbers = input.match(/\d+/g);
    if (numbers) entities.set('numbers', numbers);

    return entities;
  }
}
```

#### executor.ts
```typescript
export interface CommandExecutor {
  execute(command: EnrichedCommand): Promise<ExecutionResult>;
  stream(command: EnrichedCommand): AsyncIterator<ExecutionChunk>;
  cancel(executionId: string): void;
}

export class AsyncCommandExecutor implements CommandExecutor {
  private activeExecutions: Map<string, AbortController> = new Map();

  constructor(
    private systemExecutor: SystemCommandExecutor,
    private aiOrchestrator: AIOrchestrator,
    private securityValidator: SecurityValidator
  ) {}

  async execute(command: EnrichedCommand): Promise<ExecutionResult> {
    const executionId = this.generateExecutionId();
    const controller = new AbortController();
    this.activeExecutions.set(executionId, controller);

    try {
      // Validate security
      const validation = await this.securityValidator.validate(command);
      if (!validation.valid) {
        throw new SecurityError(validation.reason);
      }

      // Route to appropriate executor
      if (command.suggestedAction === 'execute_direct') {
        return await this.systemExecutor.execute(
          command.parsed.command,
          command.parsed.args,
          { signal: controller.signal }
        );
      } else {
        return await this.aiOrchestrator.process(command, {
          signal: controller.signal
        });
      }
    } finally {
      this.activeExecutions.delete(executionId);
    }
  }

  async *stream(command: EnrichedCommand): AsyncIterator<ExecutionChunk> {
    if (command.requiresAI) {
      yield* this.aiOrchestrator.stream(command);
    } else {
      const result = await this.execute(command);
      yield { type: 'command_output', data: result.output };
    }
  }

  cancel(executionId: string): void {
    const controller = this.activeExecutions.get(executionId);
    if (controller) {
      controller.abort();
      this.activeExecutions.delete(executionId);
    }
  }
}

export class SystemCommandExecutor {
  async execute(
    command: string,
    args: string[],
    options: ExecutionOptions
  ): Promise<ExecutionResult> {
    const startTime = Date.now();

    try {
      const { stdout, stderr } = await execAsync(
        `${command} ${args.join(' ')}`,
        {
          signal: options.signal,
          timeout: options.timeout || 30000
        }
      );

      return {
        success: true,
        output: stdout,
        error: stderr || undefined,
        metadata: {
          executionTime: Date.now() - startTime,
          command,
          args
        }
      };
    } catch (error) {
      return {
        success: false,
        output: '',
        error: error as Error,
        metadata: {
          executionTime: Date.now() - startTime,
          command,
          args
        }
      };
    }
  }
}
```

### 3. AI Integration Module (`src/ai/`)

#### orchestrator.ts
```typescript
export class AIOrchestrator {
  constructor(
    private llmProvider: LLMProvider,
    private mcpManager: MCPClientManager,
    private contextManager: ContextManager
  ) {}

  async process(
    command: EnrichedCommand,
    options: ProcessingOptions
  ): Promise<ExecutionResult> {
    // Build context-aware prompt
    const prompt = await this.buildPrompt(command);

    // Get available tools from MCP
    const tools = await this.getAvailableTools(command.context);

    // Generate with tool calling
    const response = await this.llmProvider.generate(prompt, {
      tools,
      temperature: 0.7,
      maxTokens: 2000
    });

    // Execute tool calls if any
    if (response.toolCalls) {
      return await this.executeToolCalls(response.toolCalls);
    }

    return {
      success: true,
      output: response.text,
      metadata: {
        model: response.model,
        tokensUsed: response.tokensUsed
      }
    };
  }

  async *stream(command: EnrichedCommand): AsyncIterator<ExecutionChunk> {
    const prompt = await this.buildPrompt(command);
    const stream = this.llmProvider.stream(prompt);

    let buffer = '';
    for await (const chunk of stream) {
      buffer += chunk;
      yield { type: 'llm_output', data: chunk };

      // Check for tool calls in buffer
      const toolCall = this.extractToolCall(buffer);
      if (toolCall) {
        const result = await this.executeMCPTool(toolCall);
        yield { type: 'tool_output', data: result };
        buffer = '';
      }
    }
  }

  private async buildPrompt(command: EnrichedCommand): string {
    const context = command.context;

    return `You are an AI assistant integrated into a command-line shell.

Current Context:
- Working Directory: ${context.workingDirectory}
- Recent Commands: ${context.history.map(h => h.input).join('\n')}

Available Tools:
${context.mcpCapabilities.map(t => `- ${t.name}: ${t.description}`).join('\n')}

User Request: ${command.parsed.rawInput}

Provide a helpful response. If you need to execute commands or use tools, use the available tool calling format.`;
  }

  private async getAvailableTools(context: CommandContext): Promise<Tool[]> {
    const mcpTools: Tool[] = [];

    for (const server of context.mcpCapabilities) {
      const tools = await this.mcpManager.listTools(server.name);
      mcpTools.push(...this.convertMCPTools(tools));
    }

    return mcpTools;
  }

  private async executeMCPTool(toolCall: ToolCall): Promise<any> {
    const [server, toolName] = toolCall.name.split(':');

    return await this.mcpManager.executeRequest(server, {
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: toolCall.arguments
      }
    });
  }
}
```

#### mcp/client.ts
```typescript
export class MCPClientManager {
  private clients: Map<string, MCPClient> = new Map();
  private messageId = 0;

  async connect(config: MCPServerConfig): Promise<MCPClient> {
    const adapter = new StdioMCPAdapter(config);
    await adapter.start();

    // Initialize protocol
    const initResponse = await adapter.request('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {
        tools: {},
        resources: {},
        prompts: {}
      },
      clientInfo: {
        name: 'ai-shell',
        version: '1.0.0'
      }
    });

    const client: MCPClient = {
      id: config.name,
      name: config.name,
      status: 'connected',
      capabilities: initResponse.capabilities,
      sendRequest: (req) => adapter.request(req.method, req.params),
      subscribe: (event, handler) => adapter.on(event, handler)
    };

    this.clients.set(config.name, client);
    return client;
  }

  async listTools(serverName: string): Promise<Tool[]> {
    const client = this.clients.get(serverName);
    if (!client) throw new Error(`Server ${serverName} not connected`);

    const response = await client.sendRequest({
      method: 'tools/list',
      params: {}
    });

    return response.tools;
  }

  async listResources(serverName: string): Promise<Resource[]> {
    const client = this.clients.get(serverName);
    if (!client) throw new Error(`Server ${serverName} not connected`);

    const response = await client.sendRequest({
      method: 'resources/list',
      params: {}
    });

    return response.resources;
  }

  async executeRequest(
    serverName: string,
    request: MCPRequest
  ): Promise<MCPResponse> {
    const client = this.clients.get(serverName);
    if (!client) throw new Error(`Server ${serverName} not connected`);

    return await client.sendRequest(request);
  }
}

export class StdioMCPAdapter implements MCPServerAdapter {
  private process: ChildProcess;
  private reader: readline.Interface;
  private pendingRequests: Map<number, PendingRequest> = new Map();
  private messageId = 0;

  constructor(private config: MCPServerConfig) {}

  async start(): Promise<void> {
    this.process = spawn(this.config.command, this.config.args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, ...this.config.env }
    });

    this.reader = readline.createInterface({
      input: this.process.stdout
    });

    this.reader.on('line', (line) => {
      this.handleMessage(JSON.parse(line));
    });

    await this.waitForReady();
  }

  async request<T>(method: string, params: any): Promise<T> {
    const id = ++this.messageId;
    const message = {
      jsonrpc: '2.0',
      id,
      method,
      params
    };

    return new Promise((resolve, reject) => {
      this.pendingRequests.set(id, { resolve, reject });
      this.process.stdin.write(JSON.stringify(message) + '\n');
    });
  }

  private handleMessage(message: any): void {
    if (message.id && this.pendingRequests.has(message.id)) {
      const pending = this.pendingRequests.get(message.id)!;
      this.pendingRequests.delete(message.id);

      if (message.error) {
        pending.reject(new Error(message.error.message));
      } else {
        pending.resolve(message.result);
      }
    }
  }

  async stop(): Promise<void> {
    this.process.kill();
    await new Promise(resolve => this.process.once('exit', resolve));
  }
}
```

#### llm/ollama.ts
```typescript
export class OllamaProvider implements LLMProvider {
  private baseUrl: string;
  private defaultModel: string;

  constructor(config: OllamaConfig) {
    this.baseUrl = config.baseUrl || 'http://localhost:11434';
    this.defaultModel = config.defaultModel || 'llama2';
  }

  async generate(
    prompt: string,
    options?: GenerationOptions
  ): Promise<GenerationResult> {
    const response = await fetch(`${this.baseUrl}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: options?.model || this.defaultModel,
        prompt,
        options: {
          temperature: options?.temperature || 0.7,
          num_predict: options?.maxTokens || 512
        },
        stream: false
      })
    });

    const data = await response.json();

    return {
      text: data.response,
      model: data.model,
      tokensUsed: data.eval_count + data.prompt_eval_count,
      toolCalls: this.extractToolCalls(data.response)
    };
  }

  async *stream(
    prompt: string,
    options?: GenerationOptions
  ): AsyncIterator<string> {
    const response = await fetch(`${this.baseUrl}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: options?.model || this.defaultModel,
        prompt,
        stream: true
      })
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(l => l.trim());

      for (const line of lines) {
        const data = JSON.parse(line);
        if (data.response) {
          yield data.response;
        }
      }
    }
  }

  async embed(text: string): Promise<number[]> {
    const response = await fetch(`${this.baseUrl}/api/embeddings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: this.defaultModel,
        prompt: text
      })
    });

    const data = await response.json();
    return data.embedding;
  }

  async models(): Promise<ModelInfo[]> {
    const response = await fetch(`${this.baseUrl}/api/tags`);
    const data = await response.json();

    return data.models.map((m: any) => ({
      name: m.name,
      size: m.size,
      modified: new Date(m.modified_at)
    }));
  }
}
```

### 4. Infrastructure Module (`src/infrastructure/`)

#### memory/sqlite.ts
```typescript
export class SQLiteMemoryStore implements MemoryStore {
  private db: Database;
  private currentNamespace: string;

  constructor(dbPath: string, namespace: string = 'default') {
    this.db = new Database(dbPath);
    this.currentNamespace = namespace;
    this.initialize();
  }

  private initialize(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS memory (
        key TEXT NOT NULL,
        namespace TEXT NOT NULL,
        value TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        expires_at INTEGER,
        PRIMARY KEY (key, namespace)
      );

      CREATE INDEX IF NOT EXISTS idx_namespace ON memory(namespace);
      CREATE INDEX IF NOT EXISTS idx_expires ON memory(expires_at);
    `);
  }

  async set(key: string, value: any, ttl?: number): Promise<void> {
    const now = Date.now();
    const expiresAt = ttl ? now + ttl * 1000 : null;

    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO memory (key, namespace, value, created_at, expires_at)
      VALUES (?, ?, ?, ?, ?)
    `);

    stmt.run(
      key,
      this.currentNamespace,
      JSON.stringify(value),
      now,
      expiresAt
    );
  }

  async get<T>(key: string): Promise<T | null> {
    const stmt = this.db.prepare(`
      SELECT value, expires_at FROM memory
      WHERE key = ? AND namespace = ?
    `);

    const row = stmt.get(key, this.currentNamespace) as any;

    if (!row) return null;

    if (row.expires_at && row.expires_at < Date.now()) {
      await this.delete(key);
      return null;
    }

    return JSON.parse(row.value);
  }

  async search(pattern: string): Promise<Array<{ key: string; value: any }>> {
    const stmt = this.db.prepare(`
      SELECT key, value FROM memory
      WHERE namespace = ? AND key LIKE ?
      AND (expires_at IS NULL OR expires_at > ?)
    `);

    const rows = stmt.all(
      this.currentNamespace,
      pattern.replace('*', '%'),
      Date.now()
    ) as any[];

    return rows.map(row => ({
      key: row.key,
      value: JSON.parse(row.value)
    }));
  }

  namespace(name: string): MemoryStore {
    return new SQLiteMemoryStore(this.db.name, name);
  }
}
```

#### plugin/manager.ts
```typescript
export class PluginManager {
  private plugins: Map<string, LoadedPlugin> = new Map();
  private context: PluginContext;

  constructor(
    private config: ConfigManager,
    private memory: MemoryStore,
    private logger: Logger
  ) {
    this.context = this.createPluginContext();
  }

  async load(pluginPath: string): Promise<Plugin> {
    const module = await import(pluginPath);
    const PluginClass = module.default || module;
    const plugin = new PluginClass() as Plugin;

    await plugin.init(this.context);

    this.plugins.set(plugin.name, {
      plugin,
      path: pluginPath,
      enabled: true
    });

    this.logger.info(`Loaded plugin: ${plugin.name} v${plugin.version}`);
    return plugin;
  }

  async loadAll(): Promise<void> {
    const pluginPaths = this.config.get<string[]>('plugins.paths', []);
    const enabled = this.config.get<string[]>('plugins.enabled', []);

    for (const path of pluginPaths) {
      try {
        const plugin = await this.load(path);
        if (!enabled.includes(plugin.name)) {
          this.disable(plugin.name);
        }
      } catch (error) {
        this.logger.error(`Failed to load plugin from ${path}:`, error);
      }
    }
  }

  private createPluginContext(): PluginContext {
    const commands: CommandDefinition[] = [];
    const providers: ProviderDefinition[] = [];
    const middleware: Middleware[] = [];

    return {
      config: this.config,
      memory: this.memory.namespace('plugins'),
      logger: this.logger,

      registerCommand(def: CommandDefinition) {
        commands.push(def);
      },

      registerProvider(def: ProviderDefinition) {
        providers.push(def);
      },

      registerMiddleware(mw: Middleware) {
        middleware.push(mw);
      },

      getRegisteredCommands: () => commands,
      getRegisteredProviders: () => providers,
      getRegisteredMiddleware: () => middleware
    };
  }
}
```

## Integration Points

### Service Container
```typescript
export class ServiceContainer {
  private services: Map<string, any> = new Map();
  private factories: Map<string, () => any> = new Map();
  private singletons: Set<string> = new Set();

  register<T>(token: string, factory: () => T): void {
    this.factories.set(token, factory);
  }

  singleton<T>(token: string, factory: () => T): void {
    this.factories.set(token, factory);
    this.singletons.add(token);
  }

  resolve<T>(token: string): T {
    if (this.services.has(token)) {
      return this.services.get(token);
    }

    const factory = this.factories.get(token);
    if (!factory) {
      throw new Error(`No factory registered for ${token}`);
    }

    const service = factory();

    if (this.singletons.has(token)) {
      this.services.set(token, service);
    }

    return service;
  }
}

// Bootstrap
export function bootstrap(config: AIShellConfig): AIShellApp {
  const container = new ServiceContainer();

  // Register core services
  container.singleton('config', () => new ConfigManager(config));
  container.singleton('memory', () => new SQLiteMemoryStore('.ai-shell/memory.db'));
  container.singleton('logger', () => new Logger());

  // Register AI services
  container.singleton('llmProvider', () => {
    const cfg = container.resolve<ConfigManager>('config');
    return LLMProviderFactory.create(cfg.get('llm'));
  });

  container.singleton('mcpManager', () => new MCPClientManager());
  container.singleton('contextManager', () => new ContextManager(
    container.resolve('memory'),
    container.resolve('config')
  ));

  // Register command services
  container.register('classifier', () => new MLIntentClassifier());
  container.register('interpreter', () => new SmartInterpreter(
    container.resolve('classifier'),
    container.resolve('contextManager')
  ));

  container.register('executor', () => new AsyncCommandExecutor(
    new SystemCommandExecutor(),
    new AIOrchestrator(
      container.resolve('llmProvider'),
      container.resolve('mcpManager'),
      container.resolve('contextManager')
    ),
    new SecurityValidator()
  ));

  // Register app
  container.singleton('app', () => new AIShellApplication(container));

  return container.resolve('app');
}
```

## Configuration Schema

```typescript
export const configSchema = {
  type: 'object',
  required: ['llm', 'mcp'],
  properties: {
    llm: {
      type: 'object',
      required: ['defaultProvider'],
      properties: {
        defaultProvider: {
          type: 'string',
          enum: ['ollama', 'llamacpp', 'custom']
        },
        providers: {
          type: 'array',
          items: {
            type: 'object',
            required: ['name', 'type'],
            properties: {
              name: { type: 'string' },
              type: { type: 'string' },
              config: { type: 'object' }
            }
          }
        }
      }
    },
    mcp: {
      type: 'object',
      properties: {
        autoConnect: { type: 'boolean', default: true },
        servers: {
          type: 'object',
          patternProperties: {
            '.*': {
              type: 'object',
              required: ['command'],
              properties: {
                command: { type: 'string' },
                args: { type: 'array', items: { type: 'string' } },
                env: { type: 'object' }
              }
            }
          }
        }
      }
    },
    interface: {
      type: 'object',
      properties: {
        theme: { type: 'string', default: 'default' },
        historySize: { type: 'number', default: 1000 },
        autoComplete: { type: 'boolean', default: true }
      }
    },
    plugins: {
      type: 'object',
      properties: {
        enabled: { type: 'array', items: { type: 'string' } },
        paths: { type: 'array', items: { type: 'string' } }
      }
    }
  }
};
```

---

**Version**: 1.0.0
**Last Updated**: 2025-10-03
