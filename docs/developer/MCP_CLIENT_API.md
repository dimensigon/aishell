# MCP Client API and Plugin Development Guide

**Version:** 2.0.0
**Last Updated:** October 26, 2025
**Status:** Production Ready

## Table of Contents

1. [Overview](#overview)
2. [MCP Client Architecture](#mcp-client-architecture)
3. [TypeScript MCP Client API](#typescript-mcp-client-api)
4. [Python MCP Client API](#python-mcp-client-api)
5. [Plugin Development](#plugin-development)
6. [Advanced Features](#advanced-features)
7. [Best Practices](#best-practices)
8. [API Reference](#api-reference)

---

## Overview

The Model Context Protocol (MCP) provides a standardized interface for database connectivity and AI-Shell integration. This guide covers:

- MCP Client API for both TypeScript and Python
- Building custom MCP plugins
- Tool and resource discovery
- Context synchronization
- Error handling and recovery

### What is MCP?

MCP (Model Context Protocol) is AI-Shell's universal adapter protocol that:
- **Eliminates vendor lock-in**: Single API for multiple databases
- **Enables thin clients**: No native database drivers required
- **Supports async operations**: Non-blocking I/O throughout
- **Provides auto-discovery**: Servers announce capabilities on network
- **Standardizes tools**: Uniform tool and resource interface

---

## MCP Client Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI-Shell Application                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │         MCP Client Manager                       │   │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────┐ │   │
│  │  │ Connection │  │  Message   │  │ Context   │ │   │
│  │  │ Pool       │  │  Handler   │  │ Adapter   │ │   │
│  │  └────────────┘  └────────────┘  └───────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│                         │                                │
│         ┌───────────────┼───────────────┐               │
│         ▼               ▼               ▼               │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐        │
│  │  Oracle   │   │PostgreSQL │   │  Custom   │        │
│  │  Client   │   │  Client   │   │  Client   │        │
│  └───────────┘   └───────────┘   └───────────┘        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │   MCP Server Process   │
            │  (stdio/websocket)     │
            └────────────────────────┘
```

### Component Responsibilities

**1. MCPClient (TypeScript)**
- Server connection management
- Request/response handling with JSON-RPC 2.0
- Automatic reconnection with exponential backoff
- Event-driven architecture
- Context synchronization

**2. BaseMCPClient (Python)**
- Database connection abstraction
- Query execution and result formatting
- Connection pooling
- Transaction management
- Error translation

**3. MCPMessageBuilder**
- JSON-RPC 2.0 message construction
- Request/response validation
- Notification handling

**4. MCPContextAdapter**
- Context state management
- Session tracking
- Environment synchronization

**5. MCPErrorHandler**
- Error classification and recovery
- Retry logic with backoff
- Health monitoring

**6. MCPResourceManager**
- Resource caching with LRU
- Tool discovery and validation
- Capability matching

---

## TypeScript MCP Client API

### Core Interfaces

```typescript
// MCP Client Configuration
interface MCPClientConfig {
  servers: MCPServerConfig[];
  timeout?: number;
  maxConcurrentRequests?: number;
  contextSyncInterval?: number;
}

interface MCPServerConfig {
  name: string;
  command: string;
  args: string[];
  type: 'stdio' | 'websocket';
  env?: Record<string, string>;
  reconnect?: {
    enabled: boolean;
    maxAttempts: number;
    delayMs: number;
    backoffMultiplier: number;
  };
}

// Connection States
enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}
```

### Creating an MCP Client

```typescript
import { createMCPClient, MCPClientConfig } from './mcp';

// Option 1: From configuration object
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

const client = createMCPClient(config);

// Option 2: From .mcp.json file
import { createMCPClientFromConfig } from './mcp';
const client = createMCPClientFromConfig('.mcp.json');

// Option 3: Load default configuration
import { loadDefaultMCPClient } from './mcp';
const client = await loadDefaultMCPClient();
```

### Connection Management

```typescript
// Connect to all servers
await client.connect();

// Connect to specific server
await client.connect('claude-flow');

// Check connection state
const state = client.getConnectionState('claude-flow');
console.log(`State: ${state}`); // 'connected', 'disconnected', etc.

// Get connected servers
const connectedServers = client.getConnectedServers();
console.log(`Connected to: ${connectedServers.join(', ')}`);

// Disconnect from server(s)
await client.disconnect('claude-flow'); // Specific server
await client.disconnect(); // All servers
```

### Sending Requests

```typescript
// Send request and wait for response
const result = await client.request(
  'claude-flow',
  'tools/list',
  {},
  { timeout: 10000 }
);

// Send notification (no response expected)
await client.notify(
  'claude-flow',
  'context/update',
  { context: currentContext }
);

// List available tools
const tools = await client.listTools(); // All servers
const flowTools = await client.listTools('claude-flow'); // Specific server

// List available resources
const resources = await client.listResources();
```

### Context Synchronization

```typescript
import { MCPContextAdapter } from './mcp';

// Create context adapter
const context = new MCPContextAdapter({
  sessionId: 'ai-shell-session-123',
  workingDirectory: process.cwd(),
  environment: process.env,
  metadata: {
    shell: 'ai-shell',
    version: '2.0.0',
    user: process.env.USER
  }
});

// Sync context to all connected servers
await client.syncContext(context.getContext());

// Listen for context changes
context.on('contextChanged', async (event) => {
  console.log(`Context changed: ${event.field}`);
  await client.syncContext(context.getContext());
});

// Update specific context fields
context.updateField('workingDirectory', '/new/path');
context.updateEnvironment({ NEW_VAR: 'value' });
```

### Event Handling

```typescript
// Connection events
client.on('connected', (serverName) => {
  console.log(`✓ Connected to ${serverName}`);
});

client.on('disconnected', (serverName, error) => {
  console.log(`✗ Disconnected from ${serverName}`);
  if (error) console.error(error);
});

client.on('reconnecting', (serverName, attempt) => {
  console.log(`⟳ Reconnecting to ${serverName} (attempt ${attempt})`);
});

// Message events
client.on('message', (serverName, message) => {
  console.log(`Message from ${serverName}:`, message);
});

// State change events
client.on('stateChange', (serverName, state) => {
  console.log(`${serverName} state: ${state}`);
});

// Context synchronization
client.on('contextSync', (context) => {
  console.log('Context synchronized:', context);
});

// Tool updates
client.on('toolsUpdated', (tools) => {
  console.log(`Tools updated: ${tools.length} available`);
});
```

### Error Handling

```typescript
import { MCPErrorHandler, ErrorSeverity } from './mcp';

const errorHandler = new MCPErrorHandler();

// Listen for errors
errorHandler.on('error', (event) => {
  console.log(`Error: ${event.error.message}`);
  console.log(`Severity: ${event.severity}`);
  console.log(`Recovery: ${event.recovery}`);
});

errorHandler.on('criticalError', (event) => {
  console.error('CRITICAL:', event.error);
  // Implement fallback or shutdown logic
});

// Handle operation with automatic retry
try {
  const result = await errorHandler.handleError(
    new Error('Connection timeout'),
    {
      serverName: 'claude-flow',
      operation: 'swarm_init',
      timestamp: Date.now()
    },
    async () => {
      // Retry function
      return await client.request('claude-flow', 'swarm_init', {
        topology: 'mesh'
      });
    }
  );
  console.log('Operation succeeded:', result);
} catch (error) {
  console.error('Operation failed after retries:', error);
}
```

### Resource Management

```typescript
import { MCPResourceManager } from './mcp';

const resourceManager = new MCPResourceManager({
  maxCacheSize: 100,
  defaultTTL: 3600000, // 1 hour
  enableAutoRefresh: true
});

// Register resources
const resources = await client.listResources();
resources.forEach((resource) => {
  resourceManager.registerResource(resource);
});

// Query resources
const sqlResources = resourceManager.findByMimeType('application/sql');
const dbResources = resourceManager.findByName(/database/i);

// Get cached resource
const resource = resourceManager.getResource('db-schema');

// Clear cache
resourceManager.clearCache();

// Get statistics
const stats = resourceManager.getStats();
console.log(`Cache hit rate: ${stats.hitRate}%`);
```

---

## Python MCP Client API

### Base MCP Client Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import asyncio

class BaseMCPClient(ABC):
    """Abstract base class for MCP clients"""

    @abstractmethod
    async def connect(self, connection_string: str) -> None:
        """Establish connection to database"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    async def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute query and return results"""
        pass

    @abstractmethod
    async def query_user_objects(self) -> List[Dict[str, Any]]:
        """Retrieve user database objects"""
        pass

    @abstractmethod
    async def get_table_count(self) -> int:
        """Get number of tables"""
        pass

    @abstractmethod
    def format_result(self, result: Any) -> Dict[str, Any]:
        """Format query result for display"""
        pass
```

### PostgreSQL MCP Client Example

```python
import asyncpg
from typing import Dict, Any, List, Optional
from .base import BaseMCPClient

class PostgreSQLClient(BaseMCPClient):
    """PostgreSQL MCP client implementation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self, connection_string: str) -> None:
        """Connect to PostgreSQL database"""
        self.pool = await asyncpg.create_pool(
            connection_string,
            min_size=self.config.get('min_pool_size', 2),
            max_size=self.config.get('max_pool_size', 10),
            command_timeout=self.config.get('timeout', 30)
        )

    async def disconnect(self) -> None:
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def execute(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> Any:
        """Execute SQL query"""
        async with self.pool.acquire() as conn:
            if params:
                return await conn.fetch(query, *params)
            return await conn.fetch(query)

    async def query_user_objects(self) -> List[Dict[str, Any]]:
        """Get user tables and views"""
        query = """
        SELECT
            schemaname as schema,
            tablename as name,
            'table' as type
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        UNION ALL
        SELECT
            schemaname as schema,
            viewname as name,
            'view' as type
        FROM pg_views
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY name
        """
        results = await self.execute(query)
        return [dict(row) for row in results]

    async def get_table_count(self) -> int:
        """Get total table count"""
        query = """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        """
        result = await self.execute(query)
        return result[0]['count']

    def format_result(self, result: Any) -> Dict[str, Any]:
        """Format query result"""
        if not result:
            return {
                'rows': [],
                'row_count': 0,
                'columns': []
            }

        return {
            'rows': [dict(row) for row in result],
            'row_count': len(result),
            'columns': list(result[0].keys()) if result else []
        }
```

### Oracle Thin Client Example

```python
import oracledb
from typing import Dict, Any, List, Optional
from .base import BaseMCPClient

class OracleThinClient(BaseMCPClient):
    """Oracle thin mode MCP client (no Oracle client required)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool: Optional[oracledb.ConnectionPool] = None

        # Enable thin mode globally
        oracledb.init_oracle_client(lib_dir=None)

    async def connect(self, connection_string: str) -> None:
        """Connect using thin mode"""
        # Parse connection string
        parts = connection_string.split('/')
        user_pass = parts[0].split('@')[0]
        host_info = parts[0].split('@')[1]
        service = parts[1] if len(parts) > 1 else 'ORCL'

        username, password = user_pass.split(':')

        self.pool = oracledb.create_pool(
            user=username,
            password=password,
            dsn=f"{host_info}/{service}",
            min=self.config.get('min_pool_size', 2),
            max=self.config.get('max_pool_size', 10),
            increment=1
        )

    async def execute(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> Any:
        """Execute Oracle SQL"""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.rowcount
            finally:
                cursor.close()

    async def query_user_objects(self) -> List[Dict[str, Any]]:
        """Get user objects"""
        query = """
        SELECT
            object_name as name,
            object_type as type,
            status,
            created,
            last_ddl_time
        FROM user_objects
        WHERE object_type IN ('TABLE', 'VIEW', 'PACKAGE', 'PROCEDURE', 'FUNCTION')
        ORDER BY object_name
        """
        results = await self.execute(query)
        columns = ['name', 'type', 'status', 'created', 'last_ddl_time']
        return [dict(zip(columns, row)) for row in results]

    async def get_table_count(self) -> int:
        """Get table count"""
        query = "SELECT COUNT(*) FROM user_tables"
        result = await self.execute(query)
        return result[0][0]

    def format_result(self, result: Any) -> Dict[str, Any]:
        """Format Oracle result"""
        if not result:
            return {
                'rows': [],
                'row_count': 0,
                'columns': []
            }

        # Convert Oracle data types to Python types
        formatted_rows = []
        for row in result:
            formatted_row = {}
            for i, val in enumerate(row):
                # Handle Oracle-specific types
                if isinstance(val, oracledb.LOB):
                    val = val.read()
                formatted_row[f'col_{i}'] = val
            formatted_rows.append(formatted_row)

        return {
            'rows': formatted_rows,
            'row_count': len(result),
            'columns': [f'col_{i}' for i in range(len(result[0]))]
        }
```

### Using Python MCP Clients

```python
import asyncio
from mcp_clients.postgresql_client import PostgreSQLClient
from mcp_clients.oracle_client import OracleThinClient

async def main():
    # PostgreSQL example
    pg_config = {
        'min_pool_size': 2,
        'max_pool_size': 10,
        'timeout': 30
    }

    pg_client = PostgreSQLClient(pg_config)
    await pg_client.connect('postgresql://user:pass@localhost:5432/dbname')

    # Query database
    tables = await pg_client.query_user_objects()
    print(f"Found {len(tables)} objects")

    # Execute query
    results = await pg_client.execute(
        "SELECT * FROM users WHERE active = $1",
        (True,)
    )
    formatted = pg_client.format_result(results)
    print(f"Rows: {formatted['row_count']}")

    await pg_client.disconnect()

    # Oracle example
    oracle_config = {
        'min_pool_size': 2,
        'max_pool_size': 10
    }

    oracle_client = OracleThinClient(oracle_config)
    await oracle_client.connect('admin:password@localhost:1521/ORCL')

    # Get table count
    count = await oracle_client.get_table_count()
    print(f"Tables: {count}")

    await oracle_client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
```

---

## Plugin Development

### Creating a Custom MCP Plugin

```python
from typing import Dict, Any, List
from src.plugins.base import BasePlugin

class CustomDatabasePlugin(BasePlugin):
    """Custom database MCP plugin"""

    name = "custom_database"
    version = "1.0.0"
    description = "Custom database integration"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None

    async def initialize(self) -> bool:
        """Initialize plugin"""
        try:
            # Import custom MCP client
            from mcp_clients.custom import CustomDBClient

            self.client = CustomDBClient(self.config)
            await self.client.connect(self.config['connection_string'])

            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False

    async def execute(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin command"""
        if command == 'query':
            results = await self.client.execute(args['sql'])
            return self.client.format_result(results)

        elif command == 'list_tables':
            tables = await self.client.query_user_objects()
            return {'tables': tables}

        elif command == 'health':
            try:
                await self.client.execute('SELECT 1')
                return {'status': 'healthy'}
            except:
                return {'status': 'unhealthy'}

        else:
            raise ValueError(f"Unknown command: {command}")

    async def shutdown(self) -> None:
        """Cleanup resources"""
        if self.client:
            await self.client.disconnect()

    def get_capabilities(self) -> List[str]:
        """Return plugin capabilities"""
        return [
            'query_execution',
            'metadata_access',
            'health_check'
        ]
```

### Plugin Registration

```python
# In main application
from src.plugins.plugin_manager import PluginManager

plugin_manager = PluginManager()

# Register plugin
plugin_manager.register_plugin(CustomDatabasePlugin, {
    'connection_string': 'db://localhost:5432/mydb',
    'timeout': 30
})

# Use plugin
result = await plugin_manager.execute_command(
    'custom_database',
    'query',
    {'sql': 'SELECT * FROM users'}
)
```

---

## Advanced Features

### Tool Discovery and Registration

```typescript
import { MCPToolRegistry } from './mcp';

const toolRegistry = new MCPToolRegistry();

// Discover tools from MCP servers
const tools = await client.listTools();

tools.forEach((tool) => {
  toolRegistry.registerTool({
    name: tool.name,
    description: tool.description,
    inputSchema: tool.inputSchema,
    category: tool.category || 'general',
    riskLevel: tool.riskLevel || 'LOW',
    capabilities: tool.capabilities || []
  });
});

// Query registered tools
const queryTools = toolRegistry.findByCategory('database');
const highRiskTools = toolRegistry.findByRiskLevel('HIGH');

// Execute tool
const result = await toolRegistry.executeTool('backup_database', {
  target_db: 'production',
  backup_path: '/backups'
});
```

### Async Workflow Coordination

```typescript
// Parallel tool execution
const results = await Promise.all([
  client.request('server1', 'tool1', params1),
  client.request('server2', 'tool2', params2),
  client.request('server3', 'tool3', params3)
]);

// Sequential with dependencies
const step1 = await client.request('server1', 'analyze', params);
const step2 = await client.request('server2', 'process', {
  ...params,
  analysis: step1
});
const step3 = await client.request('server3', 'report', {
  ...params,
  processed: step2
});
```

### Health Monitoring

```typescript
// Create health check manager
const healthManager = new MCPHealthManager(client);

// Register health checks
healthManager.registerCheck('mcp-servers', async () => {
  const servers = client.getConnectedServers();
  return {
    status: servers.length > 0 ? 'healthy' : 'unhealthy',
    servers: servers,
    count: servers.length
  };
});

// Run all health checks in parallel
const results = await healthManager.runAll();
```

---

## Best Practices

### 1. Connection Pooling

```typescript
// DO: Use connection pools
const client = createMCPClient({
  servers: [...],
  maxConcurrentRequests: 10 // Limit concurrent requests
});

// DON'T: Create new clients for each request
// Bad practice - creates resource leaks
```

### 2. Error Handling

```typescript
// DO: Handle errors gracefully
try {
  const result = await client.request('server', 'method', params);
} catch (error) {
  if (error.code === 'TIMEOUT') {
    // Handle timeout specifically
  } else if (error.code === 'CONNECTION_FAILED') {
    // Handle connection failure
  } else {
    // Log and rethrow
    logger.error('Request failed:', error);
    throw error;
  }
}

// DO: Use error handler for automatic retry
const result = await errorHandler.handleError(
  error,
  context,
  retryFunction
);
```

### 3. Context Management

```typescript
// DO: Keep context synchronized
context.on('contextChanged', async (event) => {
  await client.syncContext(context.getContext());
});

// DO: Update context incrementally
context.updateField('workingDirectory', newPath);

// DON'T: Replace entire context frequently
// Inefficient - sends all data
```

### 4. Resource Cleanup

```typescript
// DO: Clean up resources
process.on('SIGTERM', async () => {
  await client.disconnect();
  process.exit(0);
});

// DO: Use try-finally for cleanup
try {
  await doWork();
} finally {
  await client.disconnect();
}
```

### 5. Performance Optimization

```python
# DO: Use connection pools
async with client.pool.acquire() as conn:
    result = await conn.execute(query)

# DO: Batch operations
async def batch_insert(rows: List[Dict]):
    async with client.pool.acquire() as conn:
        await conn.executemany(query, rows)

# DON'T: Execute queries in a loop
# Bad - creates N round trips
for row in rows:
    await client.execute(insert_query, row)
```

---

## API Reference

### TypeScript Classes

**MCPClient**
- `connect(serverName?: string): Promise<void>`
- `disconnect(serverName?: string): Promise<void>`
- `request(server, method, params?, options?): Promise<unknown>`
- `notify(server, method, params?): Promise<void>`
- `listTools(serverName?): Promise<MCPTool[]>`
- `listResources(serverName?): Promise<MCPResource[]>`
- `syncContext(context): Promise<void>`
- `getConnectionState(server): ConnectionState`
- `getConnectedServers(): string[]`

**MCPContextAdapter**
- `getContext(): MCPContext`
- `updateField(field, value): void`
- `updateEnvironment(env): void`
- `createSnapshot(): ContextSnapshot`
- `restoreSnapshot(snapshot): void`

**MCPErrorHandler**
- `handleError(error, context, retryFn): Promise<any>`
- `classifyError(error): ErrorSeverity`
- `getErrorStats(): ErrorStats`

**MCPResourceManager**
- `registerResource(resource): void`
- `getResource(uri): MCPResource | null`
- `findByMimeType(mimeType): MCPResource[]`
- `findByName(pattern): MCPResource[]`
- `clearCache(): void`
- `getStats(): CacheStats`

### Python Classes

**BaseMCPClient** (Abstract)
- `async connect(connection_string): None`
- `async disconnect(): None`
- `async execute(query, params?): Any`
- `async query_user_objects(): List[Dict]`
- `async get_table_count(): int`
- `format_result(result): Dict`

**PostgreSQLClient extends BaseMCPClient**
- All BaseMCPClient methods
- `async create_pool(): Pool`
- `async test_connection(): bool`

**OracleThinClient extends BaseMCPClient**
- All BaseMCPClient methods
- Oracle-specific methods for packages, procedures, etc.

---

## Example Workflows

### Complete Integration Example

```typescript
import {
  createMCPClient,
  MCPContextAdapter,
  MCPErrorHandler,
  MCPResourceManager
} from './mcp';

async function initializeMCP() {
  // 1. Create client
  const client = createMCPClientFromConfig('.mcp.json');

  // 2. Create supporting components
  const context = new MCPContextAdapter({
    sessionId: crypto.randomUUID(),
    workingDirectory: process.cwd(),
    environment: process.env
  });

  const errorHandler = new MCPErrorHandler();
  const resourceManager = new MCPResourceManager({
    maxCacheSize: 100,
    defaultTTL: 3600000
  });

  // 3. Set up event handlers
  client.on('connected', (server) => {
    console.log(`✓ Connected to ${server}`);
  });

  client.on('error', (server, error) => {
    errorHandler.handleError(error, { serverName: server }, async () => {
      await client.connect(server);
    });
  });

  // 4. Connect and sync context
  await client.connect();
  await client.syncContext(context.getContext());

  // 5. Discover and cache resources
  const resources = await client.listResources();
  resources.forEach(r => resourceManager.registerResource(r));

  return { client, context, errorHandler, resourceManager };
}

// Usage
const { client, context, errorHandler, resourceManager } =
  await initializeMCP();

// Execute workflow
const result = await client.request('claude-flow', 'swarm_init', {
  topology: 'mesh',
  maxAgents: 5
});
```

---

## Troubleshooting

### Common Issues

**Connection Timeout**
```typescript
// Increase timeout
const client = createMCPClient({
  servers: [...],
  timeout: 60000 // 60 seconds
});
```

**Server Not Found**
```bash
# Check .mcp.json configuration
cat .mcp.json

# Verify server is installed
npx claude-flow@alpha --version
```

**Context Sync Failures**
```typescript
// Manually trigger sync
try {
  await client.syncContext(context.getContext());
} catch (error) {
  console.error('Context sync failed:', error);
  // Continue without context sync
}
```

---

## Next Steps

- **[Async Processing Guide](./ASYNC_PROCESSING.md)** - Learn async patterns
- **[LLM Integration](./LLM_INTEGRATION.md)** - Integrate AI features
- **[Configuration Guide](./CONFIGURATION.md)** - Advanced configuration
- **[Deployment Guide](./DEPLOYMENT.md)** - Production deployment

---

**Document Version:** 2.0.0
**Last Updated:** October 26, 2025
**Maintainer:** AI-Shell Development Team
