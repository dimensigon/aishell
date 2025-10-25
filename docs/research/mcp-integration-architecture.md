# MCP Client Integration Architecture for AI-Shell

## Executive Summary

This comprehensive research document outlines Model Context Protocol (MCP) client integration patterns, best practices, and architectural recommendations for AI-Shell implementation. The findings are based on analysis of official MCP specifications (2025-03-26), TypeScript SDK patterns, and production implementations.

---

## 1. MCP Architecture Overview

### 1.1 Core Architecture Pattern

**Client-Server Model:**
```typescript
// Architecture Components
Host Application (AI-Shell CLI)
    ↓
MCP Client (Integration Layer)
    ↓
Multiple MCP Servers (Database, File System, Tools)
```

**Key Characteristics:**
- **Bidirectional Communication**: JSON-RPC 2.0 over stdio/SSE
- **Multi-Server Support**: Single client can connect to multiple MCP servers
- **Transport Flexibility**: stdio (local) or SSE/HTTP (remote)
- **Capability Negotiation**: Explicit feature declaration during initialization

### 1.2 Transport Types

| Transport | Use Case | Connection Pattern | Best For |
|-----------|----------|-------------------|----------|
| **stdio** | Local MCP servers | stdin/stdout communication | Development, local tools |
| **SSE/HTTP** | Remote MCP servers | Streamable HTTP events | Production, distributed systems |

---

## 2. Client Initialization & Lifecycle Management

### 2.1 Lifecycle Phases

**Phase 1: Initialization** (MUST be first interaction)
```typescript
// Client sends initialize request
const initRequest = {
  jsonrpc: "2.0",
  method: "initialize",
  params: {
    protocolVersion: "2025-03-26",
    capabilities: {
      experimental: {},
      sampling: {}
    },
    clientInfo: {
      name: "ai-shell",
      version: "1.0.0"
    }
  },
  id: 1
};

// Server responds with capabilities
const initResponse = {
  protocolVersion: "2025-03-26",
  capabilities: {
    logging: {},
    prompts: { listChanged: true },
    resources: { subscribe: true, listChanged: true },
    tools: { listChanged: true }
  },
  serverInfo: {
    name: "database-mcp",
    version: "1.0.0"
  }
};

// Client sends initialized notification
await client.send({
  jsonrpc: "2.0",
  method: "notifications/initialized"
});
```

**Phase 2: Normal Operations**
- Client can send requests after receiving initialize response
- Server can send requests after receiving initialized notification
- Only ping requests allowed before initialization completes

**Phase 3: Shutdown**
```typescript
// For stdio transport:
// 1. Close input stream to child process
process.stdin.end();

// 2. Wait for server exit (with timeout)
await Promise.race([
  serverProcess.exit,
  new Promise(resolve => setTimeout(resolve, 5000))
]);

// 3. Send SIGTERM if server doesn't exit
if (serverProcess.exitCode === null) {
  serverProcess.kill('SIGTERM');
}
```

### 2.2 Connection Manager Pattern

```typescript
import { MCPConnectionManager } from '@modelcontextprotocol/sdk/client';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

class AIShellMCPManager {
  private connections: Map<string, Client>;
  private transports: Map<string, Transport>;

  async initialize(configPath: string): Promise<void> {
    const config = await this.loadConfig(configPath);

    for (const [name, serverConfig] of Object.entries(config.mcpServers)) {
      // Create transport
      const transport = new StdioClientTransport({
        command: serverConfig.command,
        args: serverConfig.args,
        env: serverConfig.env
      });

      // Create client with capabilities
      const client = new Client({
        name: 'ai-shell',
        version: '1.0.0'
      }, {
        capabilities: {
          experimental: {},
          sampling: {},
          roots: { listChanged: true }
        }
      });

      // Connect
      await client.connect(transport);

      this.connections.set(name, client);
      this.transports.set(name, transport);
    }
  }

  getClient(serverName: string): Client | undefined {
    return this.connections.get(serverName);
  }

  async shutdown(): Promise<void> {
    for (const [name, client] of this.connections) {
      await client.close();
      const transport = this.transports.get(name);
      await transport?.close();
    }
  }
}
```

---

## 3. Async Message Handling & Error Recovery

### 3.1 Error Handling Patterns

**JSON-RPC Error Codes:**
```typescript
enum MCPErrorCode {
  ParseError = -32700,
  InvalidRequest = -32600,
  MethodNotFound = -32601,
  InvalidParams = -32602,
  InternalError = -32603,
  // Custom codes: -32000 to -32099
}

// Try-Catch Wrapper Pattern
async function executeWithErrorHandling<T>(
  operation: () => Promise<T>,
  context: string
): Promise<{ success: boolean; data?: T; error?: string }> {
  try {
    const data = await operation();
    return { success: true, data };
  } catch (error) {
    logger.error(`${context} failed:`, error);

    if (error instanceof MCPError) {
      // Protocol-level error
      return {
        success: false,
        error: `MCP Error ${error.code}: ${error.message}`
      };
    }

    // Unknown error
    return {
      success: false,
      error: `Unexpected error: ${error.message}`
    };
  }
}
```

**Circuit Breaker Pattern:**
```typescript
class CircuitBreaker {
  private failureCount = 0;
  private lastFailureTime?: Date;
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';

  constructor(
    private threshold: number = 5,
    private timeout: number = 60000 // 1 minute
  ) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime!.getTime() > this.timeout) {
        this.state = 'HALF_OPEN';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    this.state = 'CLOSED';
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = new Date();

    if (this.failureCount >= this.threshold) {
      this.state = 'OPEN';
    }
  }
}
```

**Timeout Handling:**
```typescript
async function withTimeout<T>(
  operation: Promise<T>,
  timeoutMs: number,
  operationName: string
): Promise<T> {
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => {
      logger.error(`Operation timeout: ${operationName} (${timeoutMs}ms)`);
      reject(new Error(`Operation timed out: ${operationName}`));
    }, timeoutMs);
  });

  return Promise.race([operation, timeoutPromise]);
}

// Usage
const result = await withTimeout(
  mcpClient.callTool('query_database', { sql: 'SELECT * FROM users' }),
  30000, // 30 second timeout
  'database query'
);
```

**Retry Strategy for Transient Failures:**
```typescript
async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  let lastError: Error;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;

      // Check if error is retryable
      if (!isTransientError(error)) {
        throw error;
      }

      // Exponential backoff
      const delay = initialDelay * Math.pow(2, i);
      logger.warn(`Retry ${i + 1}/${maxRetries} after ${delay}ms`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError!;
}

function isTransientError(error: any): boolean {
  return (
    error.code === 'ECONNREFUSED' ||
    error.code === 'ETIMEDOUT' ||
    error.message?.includes('timeout') ||
    error.message?.includes('connection')
  );
}
```

### 3.2 Async Event Bus Pattern

```typescript
import { EventEmitter } from 'events';

class AsyncEventBus extends EventEmitter {
  private processingQueue: Array<{
    event: string;
    data: any;
    critical: boolean;
  }> = [];

  private processing = true;

  async start(): Promise<void> {
    while (this.processing) {
      if (this.processingQueue.length === 0) {
        await new Promise(resolve => setTimeout(resolve, 100));
        continue;
      }

      const { event, data, critical } = this.processingQueue.shift()!;
      const listeners = this.listeners(event);

      if (critical) {
        // Wait for all listeners to complete
        await Promise.all(
          listeners.map(listener => listener(data))
        );
      } else {
        // Fire and forget
        Promise.all(
          listeners.map(listener => listener(data))
        ).catch(error => {
          console.error(`Event ${event} listener error:`, error);
        });
      }
    }
  }

  emitAsync(event: string, data: any, critical = false): void {
    this.processingQueue.push({ event, data, critical });
  }

  stop(): void {
    this.processing = false;
  }
}
```

---

## 4. Context Sharing Between CLI and LLM

### 4.1 Resource Abstraction Pattern

```typescript
// MCP Resource Types
interface MCPResource {
  uri: string;
  name: string;
  mimeType?: string;
  description?: string;
}

interface TextContent {
  type: 'text';
  text: string;
  annotations?: {
    audience?: string[];
    priority?: number;
  };
}

interface ImageContent {
  type: 'image';
  data: string; // base64
  mimeType: string;
}

interface EmbeddedResource {
  type: 'resource';
  resource: {
    uri: string;
    text: string;
    blob?: string;
  };
}

// Context Manager for AI-Shell
class MCPContextManager {
  private resources: Map<string, MCPResource> = new Map();
  private embeddings: Map<string, number[]> = new Map();

  async gatherContext(
    userInput: string,
    mcpClients: Map<string, Client>
  ): Promise<ContextBundle> {
    const relevantResources: MCPResource[] = [];

    // Get embeddings for user input
    const inputEmbedding = await this.generateEmbedding(userInput);

    // Search for relevant resources across all MCP servers
    for (const [serverName, client] of mcpClients) {
      const resources = await client.listResources();

      for (const resource of resources) {
        const similarity = this.cosineSimilarity(
          inputEmbedding,
          await this.getResourceEmbedding(resource)
        );

        if (similarity > 0.7) {
          relevantResources.push(resource);
        }
      }
    }

    // Fetch resource contents
    const contents = await Promise.all(
      relevantResources.map(r => this.fetchResourceContent(r, mcpClients))
    );

    return {
      userInput,
      resources: relevantResources,
      contents,
      timestamp: new Date()
    };
  }

  private async fetchResourceContent(
    resource: MCPResource,
    clients: Map<string, Client>
  ): Promise<string> {
    // Parse URI to determine which MCP server to use
    const [serverName] = resource.uri.split('://');
    const client = clients.get(serverName);

    if (!client) {
      throw new Error(`No client for server: ${serverName}`);
    }

    const result = await client.readResource({ uri: resource.uri });
    return result.contents[0].text || '';
  }
}
```

### 4.2 LLM Integration Pattern

```typescript
interface LLMContextProvider {
  getSystemPrompt(context: ContextBundle): string;
  getUserPrompt(userInput: string): string;
  getTools(): ToolDefinition[];
}

class MCPLLMIntegration implements LLMContextProvider {
  constructor(
    private mcpManager: AIShellMCPManager,
    private contextManager: MCPContextManager
  ) {}

  async processUserInput(input: string): Promise<LLMResponse> {
    // Gather context from MCP servers
    const context = await this.contextManager.gatherContext(
      input,
      this.mcpManager.getAllClients()
    );

    // Build prompts
    const systemPrompt = this.getSystemPrompt(context);
    const userPrompt = this.getUserPrompt(input);

    // Get available tools from MCP servers
    const tools = await this.getAvailableTools();

    // Call LLM with context and tools
    const response = await this.callLLM({
      system: systemPrompt,
      user: userPrompt,
      tools
    });

    // Execute tool calls if present
    if (response.toolCalls) {
      const toolResults = await this.executeToolCalls(response.toolCalls);

      // Get final response with tool results
      return this.callLLM({
        system: systemPrompt,
        user: userPrompt,
        tools,
        toolResults
      });
    }

    return response;
  }

  private async getAvailableTools(): Promise<ToolDefinition[]> {
    const allTools: ToolDefinition[] = [];

    for (const client of this.mcpManager.getAllClients().values()) {
      const { tools } = await client.listTools();

      allTools.push(...tools.map(tool => ({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema
      })));
    }

    return allTools;
  }

  private async executeToolCalls(
    toolCalls: ToolCall[]
  ): Promise<ToolResult[]> {
    return Promise.all(
      toolCalls.map(async (call) => {
        const client = await this.findClientForTool(call.name);

        try {
          const result = await client.callTool({
            name: call.name,
            arguments: call.arguments
          });

          return {
            toolCallId: call.id,
            content: result.content
          };
        } catch (error) {
          return {
            toolCallId: call.id,
            content: [{
              type: 'text',
              text: `Error executing tool: ${error.message}`
            }],
            isError: true
          };
        }
      })
    );
  }
}
```

---

## 5. Security Best Practices (2025 Updates)

### 5.1 OAuth Resource Server Pattern

**June 2025 Specification Updates:**
```typescript
// MCP servers as OAuth Resource Servers
interface MCPAuthConfig {
  authorizationServer: string;
  resourceIndicator: string; // RFC 8707
  scopes: string[];
}

class SecureMCPClient {
  private accessToken?: string;

  async authorize(config: MCPAuthConfig): Promise<void> {
    // Request token with resource indicator
    const tokenResponse = await fetch(`${config.authorizationServer}/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        resource: config.resourceIndicator, // RFC 8707
        scope: config.scopes.join(' ')
      })
    });

    const { access_token } = await tokenResponse.json();
    this.accessToken = access_token;
  }

  async callTool(name: string, args: any): Promise<any> {
    // Explicit user consent check
    const approved = await this.getUserConsent({
      tool: name,
      description: `Execute ${name} with provided arguments`,
      arguments: args
    });

    if (!approved) {
      throw new Error('User denied tool execution');
    }

    // Execute with authorized token
    return this.executeWithAuth(name, args);
  }
}
```

### 5.2 Credential Management

```typescript
import { Keyring } from '@modelcontextprotocol/sdk/security';

class SecureCredentialVault {
  private keyring: Keyring;
  private redactionPatterns: RegExp[] = [];

  async storeCredential(
    name: string,
    value: string,
    type: 'password' | 'token' | 'apikey'
  ): Promise<void> {
    // Store in OS keyring
    await this.keyring.setPassword('ai-shell', name, value);

    // Add to redaction patterns
    this.redactionPatterns.push(new RegExp(this.escapeRegex(value), 'g'));
  }

  async retrieveCredential(name: string): Promise<string> {
    return this.keyring.getPassword('ai-shell', name);
  }

  autoRedact(text: string): string {
    let redacted = text;

    for (const pattern of this.redactionPatterns) {
      redacted = redacted.replace(pattern, '***REDACTED***');
    }

    return redacted;
  }
}
```

---

## 6. AI-Shell Specific Implementation Recommendations

### 6.1 Architecture Overview

```
┌─────────────────────────────────────────────┐
│           AI-Shell CLI Interface            │
│  (prompt-toolkit / Textual UI Framework)    │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         MCP Integration Layer               │
│  ┌──────────────────────────────────────┐   │
│  │   AIShellMCPManager                  │   │
│  │   - Connection pooling               │   │
│  │   - Lifecycle management             │   │
│  │   - Error recovery                   │   │
│  └──────────────────────────────────────┘   │
└─────────────────┬───────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼──────┐ ┌───▼──────┐ ┌───▼──────┐
│ Database │ │   File   │ │  Tools   │
│   MCP    │ │  System  │ │   MCP    │
│  Server  │ │   MCP    │ │  Server  │
└──────────┘ └──────────┘ └──────────┘
```

### 6.2 Module Panel Enrichment Strategy

```typescript
class ModulePanelEnricher {
  private updateQueue: AsyncQueue<EnrichmentRequest>;
  private circuitBreaker: CircuitBreaker;

  constructor(
    private mcpManager: AIShellMCPManager,
    private llm: LocalLLMManager
  ) {
    this.updateQueue = new AsyncQueue();
    this.circuitBreaker = new CircuitBreaker(5, 60000);
  }

  async enrichContinuously(): Promise<void> {
    while (true) {
      const request = await this.updateQueue.dequeue();

      try {
        // Analyze user intent with local LLM
        const intent = await this.llm.analyzeIntent(
          request.userInput,
          request.context
        );

        // Gather relevant MCP resources using circuit breaker
        const resources = await this.circuitBreaker.execute(() =>
          this.gatherRelevantResources(intent)
        );

        // Update panel asynchronously (non-blocking)
        this.updatePanel({
          intent,
          resources,
          suggestions: await this.generateSuggestions(intent, resources)
        });

      } catch (error) {
        logger.error('Enrichment failed:', error);
        this.updatePanel({ error: error.message });
      }
    }
  }

  private async gatherRelevantResources(
    intent: Intent
  ): Promise<MCPResource[]> {
    const resources: MCPResource[] = [];

    // Parallel resource gathering from multiple MCP servers
    const promises = Array.from(
      this.mcpManager.getAllClients().entries()
    ).map(async ([name, client]) => {
      if (intent.relevantServers.includes(name)) {
        const serverResources = await client.listResources();
        resources.push(...serverResources);
      }
    });

    await Promise.all(promises);
    return resources;
  }
}
```

### 6.3 Database MCP Integration

```typescript
interface DatabaseMCPConfig {
  type: 'oracle' | 'postgresql';
  connection: {
    host: string;
    port: number;
    database?: string;
    service?: string;
  };
  pooling: {
    min: number;
    max: number;
    idleTimeout: number;
  };
}

class DatabaseMCPClient {
  private client: Client;
  private circuitBreaker: CircuitBreaker;

  async executeSQLWithAnalysis(sql: string): Promise<QueryResult> {
    // Risk assessment
    const risk = await this.assessRisk(sql);

    if (risk.level > RiskLevel.MEDIUM) {
      // Get AI recommendation
      const recommendation = await this.getAIRecommendation(sql, risk);

      // Require user confirmation
      const confirmed = await this.confirmWithUser({
        sql,
        risk,
        recommendation
      });

      if (!confirmed) {
        throw new Error('User cancelled high-risk operation');
      }
    }

    // Execute via MCP with circuit breaker
    return this.circuitBreaker.execute(async () => {
      const result = await this.client.callTool('execute_sql', {
        sql,
        params: []
      });

      return {
        rows: result.content,
        metadata: {
          executionTime: result.metadata?.executionTime,
          rowCount: result.metadata?.rowCount
        }
      };
    });
  }
}
```

---

## 7. Performance Optimization Strategies

### 7.1 Connection Pooling

```typescript
class MCPConnectionPool {
  private pool: Map<string, Client[]> = new Map();
  private available: Map<string, Client[]> = new Map();

  async acquire(serverName: string): Promise<Client> {
    const availableClients = this.available.get(serverName) || [];

    if (availableClients.length > 0) {
      return availableClients.pop()!;
    }

    // Create new client if pool not exhausted
    const poolClients = this.pool.get(serverName) || [];
    if (poolClients.length < this.maxPoolSize) {
      const client = await this.createClient(serverName);
      poolClients.push(client);
      this.pool.set(serverName, poolClients);
      return client;
    }

    // Wait for client to become available
    return new Promise((resolve) => {
      const checkInterval = setInterval(() => {
        const available = this.available.get(serverName) || [];
        if (available.length > 0) {
          clearInterval(checkInterval);
          resolve(available.pop()!);
        }
      }, 100);
    });
  }

  release(serverName: string, client: Client): void {
    const available = this.available.get(serverName) || [];
    available.push(client);
    this.available.set(serverName, available);
  }
}
```

### 7.2 Caching Strategy

```typescript
class MCPResourceCache {
  private cache: Map<string, CacheEntry> = new Map();
  private ttl: number = 300000; // 5 minutes

  async get(uri: string, fetcher: () => Promise<any>): Promise<any> {
    const cached = this.cache.get(uri);

    if (cached && Date.now() - cached.timestamp < this.ttl) {
      return cached.value;
    }

    // Fetch and cache
    const value = await fetcher();
    this.cache.set(uri, { value, timestamp: Date.now() });

    return value;
  }

  invalidate(pattern: string): void {
    for (const [uri] of this.cache) {
      if (uri.includes(pattern)) {
        this.cache.delete(uri);
      }
    }
  }
}
```

---

## 8. Monitoring & Observability

### 8.1 Metrics Collection

```typescript
interface MCPMetrics {
  requests: {
    total: number;
    success: number;
    failure: number;
    avgDuration: number;
  };
  connections: {
    active: number;
    idle: number;
    failed: number;
  };
  resources: {
    cached: number;
    fetched: number;
    cacheHitRate: number;
  };
}

class MCPMonitor {
  private metrics: MCPMetrics = {
    requests: { total: 0, success: 0, failure: 0, avgDuration: 0 },
    connections: { active: 0, idle: 0, failed: 0 },
    resources: { cached: 0, fetched: 0, cacheHitRate: 0 }
  };

  async recordRequest(
    serverName: string,
    operation: string,
    duration: number,
    success: boolean
  ): Promise<void> {
    this.metrics.requests.total++;

    if (success) {
      this.metrics.requests.success++;
    } else {
      this.metrics.requests.failure++;
    }

    // Update average duration
    this.metrics.requests.avgDuration =
      (this.metrics.requests.avgDuration * (this.metrics.requests.total - 1) + duration) /
      this.metrics.requests.total;

    // Log to monitoring system
    logger.info('MCP Request', {
      server: serverName,
      operation,
      duration,
      success
    });
  }

  getHealthStatus(): HealthStatus {
    const errorRate = this.metrics.requests.failure / this.metrics.requests.total;

    return {
      status: errorRate < 0.05 ? 'healthy' : 'degraded',
      metrics: this.metrics,
      timestamp: new Date()
    };
  }
}
```

---

## 9. Implementation Roadmap for AI-Shell

### Phase 1: Foundation (Weeks 1-2)
1. **MCP Client Manager Setup**
   - Implement `AIShellMCPManager` with multi-server support
   - Configure stdio transport for local MCP servers
   - Implement lifecycle management (init → operate → shutdown)

2. **Error Handling Infrastructure**
   - Circuit breaker pattern for external services
   - Retry logic with exponential backoff
   - Comprehensive error logging

### Phase 2: Context & Integration (Weeks 3-4)
1. **Context Sharing Layer**
   - Resource abstraction and fetching
   - LLM integration with tool calling
   - Vector similarity search for relevant resources

2. **Database MCP Integration**
   - Oracle MCP client (cx_Oracle thin mode)
   - PostgreSQL MCP client (psycopg2)
   - SQL risk assessment and confirmation flow

### Phase 3: Performance & Security (Weeks 5-6)
1. **Optimization**
   - Connection pooling implementation
   - Resource caching with TTL
   - Async event bus for non-blocking operations

2. **Security Hardening**
   - OAuth Resource Server pattern (RFC 8707)
   - Secure credential vault with auto-redaction
   - Explicit user consent for tool execution

### Phase 4: Monitoring & Production (Week 7)
1. **Observability**
   - Metrics collection and dashboards
   - Health check endpoints
   - Performance monitoring

2. **Production Hardening**
   - Load testing and optimization
   - Documentation and runbooks
   - Deployment automation

---

## 10. Key Takeaways & Recommendations

### Critical Implementation Points

1. **Always Initialize First**: The initialize → initialized handshake is mandatory before any operations

2. **Use Circuit Breakers**: Protect against cascading failures in distributed MCP environments

3. **Implement Timeouts**: Every MCP operation should have a timeout to prevent hung connections

4. **Cache Intelligently**: Use TTL-based caching for frequently accessed resources

5. **Secure by Default**: Implement OAuth Resource Server pattern and explicit user consent

6. **Monitor Everything**: Collect metrics for requests, connections, and resource usage

### Integration Best Practices

- **Multi-Server Architecture**: Design for multiple MCP servers from day one
- **Async-First**: Use async/await patterns throughout for non-blocking operations
- **Graceful Degradation**: Handle MCP server failures without crashing the application
- **Context Awareness**: Leverage vector similarity search to provide relevant resources to LLM
- **User Control**: Always get explicit consent before executing potentially dangerous operations

### AI-Shell Specific Recommendations

1. **Module Panel Enrichment**: Use background async processing to update UI without blocking user input

2. **Database Integration**: Implement unified interface supporting both Oracle and PostgreSQL via MCP

3. **Credential Security**: Store credentials in OS keyring with automatic redaction in logs

4. **Risk Assessment**: Integrate AI-powered SQL risk analysis before execution

5. **Performance**: Target <100ms response time for context gathering through parallel MCP queries

---

## 11. Resources & References

### Official Documentation
- [MCP Specification 2025-03-26](https://modelcontextprotocol.io/specification/2025-03-26)
- [TypeScript SDK Repository](https://github.com/modelcontextprotocol/typescript-sdk)
- [MCP Best Practices Guide](https://modelcontextprotocol.info/docs/best-practices/)

### Security Updates
- [June 2025 Auth Specification](https://auth0.com/blog/mcp-specs-update-all-about-auth/)
- [RFC 8707 Resource Indicators](https://datatracker.ietf.org/doc/html/rfc8707)

### Implementation Examples
- [edanyal/mcp-client](https://github.com/edanyal/mcp-client) - TypeScript client library
- [mcp-use/mcp-use-ts](https://github.com/mcp-use/mcp-use-ts) - LangChain integration

### Related AI-Shell Documentation
- `/home/claude/dbacopilot/ai-shell-mcp-architecture.md` - Existing architecture document
- `/home/claude/dbacopilot/.mcp.json` - Current MCP configuration

---

*Research conducted: October 3, 2025*
*Stored in memory namespace: `swarm-ai-shell` with key: `mcp-patterns`*
