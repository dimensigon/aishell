# MCP Client Integration

This module provides a complete Model Context Protocol (MCP) client implementation for AI-Shell.

## Features

- **Connection Management**: Automatic connection, reconnection, and lifecycle management
- **Message Protocol**: Full JSON-RPC 2.0 protocol support with request/response handling
- **Context Synchronization**: Automatic context sync across MCP servers
- **Resource Management**: Resource caching, validation, and lifecycle management
- **Error Handling**: Comprehensive error handling with automatic recovery strategies
- **Reconnection Logic**: Exponential backoff reconnection with configurable retry policies

## Architecture

### Core Components

1. **MCPClient** (`client.ts`)
   - Main client class managing server connections
   - Connection pooling and lifecycle management
   - Request/response handling with timeout support
   - Automatic context synchronization
   - Event-driven architecture

2. **MCPMessageBuilder** (`messages.ts`)
   - Protocol-compliant message construction
   - JSON-RPC 2.0 message validation
   - Request/response/notification builders
   - Error message handling

3. **MCPContextAdapter** (`context-adapter.ts`)
   - Context state management
   - Context snapshots and restoration
   - Context diffing and merging
   - Import/export functionality

4. **MCPErrorHandler** (`error-handler.ts`)
   - Error classification by severity
   - Automatic recovery strategy determination
   - Retry logic with exponential backoff
   - Error history and statistics

5. **MCPResourceManager** (`resource-manager.ts`)
   - Resource registration and discovery
   - LRU caching with TTL support
   - Resource filtering and querying
   - Cache statistics and optimization

## Integration Points

### 1. AI-Shell Core Integration

```typescript
import { createMCPClientFromConfig } from './mcp';

// Initialize MCP client from .mcp.json
const mcpClient = createMCPClientFromConfig('.mcp.json');

// Connect to all servers
await mcpClient.connect();

// Listen for events
mcpClient.on('connected', (serverName) => {
  console.log(`Connected to ${serverName}`);
});

mcpClient.on('error', (serverName, error) => {
  console.error(`Error from ${serverName}:`, error);
});
```

### 2. Context Synchronization

```typescript
import { MCPContextAdapter } from './mcp';

// Create context adapter
const contextAdapter = new MCPContextAdapter({
  sessionId: 'ai-shell-session-123',
  workingDirectory: process.cwd(),
  environment: process.env,
  metadata: {
    shell: 'ai-shell',
    version: '1.0.0'
  }
});

// Sync context to all MCP servers
await mcpClient.syncContext(contextAdapter.getContext());

// Update context when environment changes
contextAdapter.on('contextChanged', async (event) => {
  await mcpClient.syncContext(contextAdapter.getContext());
});
```

### 3. Tool Discovery and Execution

```typescript
// List available tools from all servers
const tools = await mcpClient.listTools();

console.log('Available MCP tools:', tools);

// Execute a tool
const result = await mcpClient.request(
  'claude-flow',
  'tools/call',
  {
    name: 'swarm_init',
    arguments: {
      topology: 'mesh',
      maxAgents: 5
    }
  }
);
```

### 4. Resource Management

```typescript
import { MCPResourceManager } from './mcp';

// Create resource manager
const resourceManager = new MCPResourceManager({
  maxCacheSize: 100,
  defaultTTL: 3600000, // 1 hour
  enableAutoRefresh: true
});

// List and cache resources
const resources = await mcpClient.listResources();

resources.forEach((resource) => {
  resourceManager.registerResource(resource);
});

// Query resources
const sqlResources = resourceManager.findByMimeType('application/sql');
const dbResources = resourceManager.findByName(/database/i);
```

### 5. Error Handling

```typescript
import { MCPErrorHandler, ErrorSeverity } from './mcp';

// Create error handler
const errorHandler = new MCPErrorHandler();

// Listen for errors
errorHandler.on('error', (event) => {
  console.log(`Error: ${event.error.message}`);
  console.log(`Severity: ${event.severity}`);
  console.log(`Recovery: ${event.recovery}`);
});

errorHandler.on('criticalError', (event) => {
  // Handle critical errors
  console.error('CRITICAL:', event.error);
  process.exit(1);
});

// Handle operation with automatic retry
try {
  const result = await errorHandler.handleError(
    new Error('Timeout'),
    {
      serverName: 'claude-flow',
      operation: 'swarm_init',
      timestamp: Date.now()
    },
    async () => {
      return await mcpClient.request('claude-flow', 'swarm_init', {
        topology: 'mesh'
      });
    }
  );
} catch (error) {
  // All retries failed
  console.error('Operation failed after retries:', error);
}
```

## Configuration

### Server Configuration (.mcp.json)

```json
{
  "mcpServers": {
    "claude-flow": {
      "command": "npx",
      "args": ["claude-flow@alpha", "mcp", "start"],
      "type": "stdio",
      "env": {
        "DEBUG": "claude-flow:*"
      }
    },
    "ruv-swarm": {
      "command": "npx",
      "args": ["ruv-swarm", "mcp", "start"],
      "type": "stdio"
    }
  }
}
```

### Client Configuration

```typescript
const config: MCPClientConfig = {
  servers: [
    {
      name: 'claude-flow',
      command: 'npx',
      args: ['claude-flow@alpha', 'mcp', 'start'],
      type: 'stdio',
      reconnect: {
        enabled: true,
        maxAttempts: 5,
        delayMs: 1000,
        backoffMultiplier: 2
      }
    }
  ],
  timeout: 30000,
  maxConcurrentRequests: 10,
  contextSyncInterval: 60000
};
```

## Usage Examples

### Basic Setup

```typescript
import { createMCPClient, MCPContextAdapter } from './mcp';

async function initializeMCP() {
  // Create client
  const client = createMCPClient({
    servers: [/* server configs */],
    timeout: 30000
  });

  // Connect
  await client.connect();

  // Create context
  const context = new MCPContextAdapter();
  await client.syncContext(context.getContext());

  return { client, context };
}
```

### Advanced Error Handling

```typescript
import { MCPClient, MCPErrorHandler } from './mcp';

const client = new MCPClient(config);
const errorHandler = new MCPErrorHandler();

// Wrap requests with error handling
async function safeRequest(
  serverName: string,
  method: string,
  params?: unknown
) {
  return errorHandler.handleError(
    new Error('Request'),
    { serverName, operation: method, timestamp: Date.now() },
    () => client.request(serverName, method, params)
  );
}
```

## Event System

The MCP client uses an event-driven architecture:

- `connected` - Server connection established
- `disconnected` - Server connection lost
- `reconnecting` - Attempting reconnection
- `error` - Error occurred
- `message` - Message received
- `stateChange` - Connection state changed
- `contextSync` - Context synchronized
- `toolsUpdated` - Tool list updated
- `resourcesUpdated` - Resource list updated

## Testing

The implementation includes comprehensive error scenarios and edge cases:

- Connection failures and timeouts
- Message parsing errors
- Invalid protocol messages
- Automatic reconnection
- Concurrent request handling
- Context synchronization conflicts

## Performance Considerations

- **Connection Pooling**: Maintains persistent connections to MCP servers
- **Request Queueing**: Manages concurrent requests with configurable limits
- **Resource Caching**: LRU cache with TTL for frequently accessed resources
- **Lazy Loading**: Connects to servers on-demand
- **Event Throttling**: Prevents event flooding during high-frequency updates

## Security

- **Input Validation**: All messages validated against JSON-RPC 2.0 spec
- **Error Isolation**: Errors in one server don't affect others
- **Timeout Protection**: All requests have configurable timeouts
- **Environment Isolation**: Server processes run with isolated environments

## Future Enhancements

- WebSocket transport support
- Message compression
- Request batching
- Advanced routing strategies
- Load balancing across servers
- Server health monitoring
- Metrics and observability

## Dependencies

- `@modelcontextprotocol/sdk` - MCP SDK
- `ws` - WebSocket support (future)
- `uuid` - Unique identifiers
- `eventemitter3` - Event system
