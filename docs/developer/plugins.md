# Plugin Development Guide

**Version:** 2.0.0
**Last Updated:** October 28, 2025
**Target Audience:** Plugin developers, contributors

---

## Table of Contents

1. [Overview](#overview)
2. [Plugin Architecture](#plugin-architecture)
3. [Getting Started](#getting-started)
4. [Plugin API Reference](#plugin-api-reference)
5. [Creating Custom Plugins](#creating-custom-plugins)
6. [Testing Plugins](#testing-plugins)
7. [Publishing Plugins](#publishing-plugins)
8. [Example Plugin Implementations](#example-plugin-implementations)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

AI-Shell features a powerful plugin architecture based on the Model Context Protocol (MCP) that enables developers to extend functionality without modifying core code. Plugins can add new tools, resources, prompts, and capabilities to AI-Shell.

### What Can Plugins Do?

- **Add Tools**: Create new commands and operations
- **Provide Resources**: Expose data sources and APIs
- **Extend Prompts**: Add custom AI prompt templates
- **Enhance Context**: Contribute contextual information
- **Enable Streaming**: Support real-time data flows

### Plugin Benefits

- **Modularity**: Isolated, independent functionality
- **Hot Reload**: Load/unload without restarting
- **Version Control**: Semantic versioning support
- **Dependency Management**: Declare dependencies explicitly
- **Event-Driven**: React to system events
- **Security**: Sandboxed execution environment

---

## Plugin Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI-Shell Core                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │          MCP Plugin Manager                        │    │
│  │  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │  Discovery   │  │  Lifecycle   │              │    │
│  │  │  Engine      │  │  Manager     │              │    │
│  │  └──────────────┘  └──────────────┘              │    │
│  └────────────────────────────────────────────────────┘    │
│                        │                                     │
│         ┌──────────────┼──────────────┐                    │
│         │              │              │                     │
│    ┌────▼────┐    ┌───▼────┐    ┌───▼────┐              │
│    │ Plugin  │    │ Plugin │    │ Plugin │              │
│    │   A     │    │   B    │    │   C    │              │
│    └─────────┘    └────────┘    └────────┘              │
│         │              │              │                     │
└─────────┼──────────────┼──────────────┼─────────────────────┘
          │              │              │
    ┌─────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
    │ MCP Server │ │MCP Server│ │ MCP Server │
    │     A      │ │    B     │ │     C      │
    └────────────┘ └──────────┘ └────────────┘
```

### Plugin Lifecycle

```
UNLOADED → LOADING → LOADED → ACTIVE
    ↓                            ↓
  ERROR ←──────────────────────┘
    ↓
DISABLED
```

**States:**

- **UNLOADED**: Plugin discovered but not loaded
- **LOADING**: Plugin being initialized
- **LOADED**: Plugin initialized successfully
- **ACTIVE**: Plugin connected and operational
- **ERROR**: Plugin encountered an error
- **DISABLED**: Plugin intentionally disabled

### Plugin Components

```typescript
// Plugin Metadata
interface PluginMetadata {
  name: string;              // Unique plugin identifier
  version: string;           // Semantic version (e.g., "1.0.0")
  description?: string;      // Human-readable description
  author?: string;           // Plugin author
  homepage?: string;         // Documentation URL
  keywords?: string[];       // Searchable tags
  dependencies?: Record<string, string>;  // NPM dependencies
  capabilities: PluginCapability[];       // Plugin capabilities
}

// Plugin Capabilities
enum PluginCapability {
  TOOLS = 'tools',           // Provides executable tools
  RESOURCES = 'resources',   // Exposes data resources
  PROMPTS = 'prompts',       // Adds prompt templates
  CONTEXT = 'context',       // Contributes context
  STREAMING = 'streaming'    // Supports real-time data
}

// Plugin Instance
interface PluginInstance {
  metadata: PluginMetadata;
  serverConfig: MCPServerConfig;
  state: PluginState;
  loadTime: number;
  tools?: MCPTool[];
  resources?: MCPResource[];
  error?: Error;
}
```

---

## Getting Started

### Prerequisites

- Node.js 18.0 or higher
- npm 9.0 or higher
- TypeScript 5.3 or higher (for TypeScript plugins)
- Basic understanding of MCP (Model Context Protocol)

### Development Environment Setup

```bash
# Clone AI-Shell repository
git clone https://github.com/your-org/ai-shell.git
cd ai-shell

# Install dependencies
npm install

# Create plugin directory
mkdir -p plugins/my-first-plugin
cd plugins/my-first-plugin

# Initialize plugin
npm init -y
```

### Plugin Structure

```
my-first-plugin/
├── plugin.json          # Plugin metadata (required)
├── index.js             # Main entry point (required)
├── package.json         # NPM package configuration
├── README.md            # Plugin documentation
├── src/
│   ├── tools/          # Tool implementations
│   ├── resources/      # Resource providers
│   └── handlers/       # Event handlers
├── tests/
│   └── index.test.js   # Plugin tests
└── examples/
    └── usage.md        # Usage examples
```

### Minimal Plugin Example

**plugin.json:**

```json
{
  "name": "my-first-plugin",
  "version": "1.0.0",
  "description": "My first AI-Shell plugin",
  "author": "Your Name",
  "homepage": "https://github.com/username/my-first-plugin",
  "keywords": ["example", "tutorial"],
  "capabilities": ["tools"]
}
```

**index.js:**

```javascript
#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { z } = require('zod');

// Create MCP server
const server = new Server(
  {
    name: 'my-first-plugin',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Register tool
server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'hello_world',
        description: 'Says hello to someone',
        inputSchema: z.object({
          name: z.string().describe('Name to greet'),
        }),
      },
    ],
  };
});

// Handle tool execution
server.setRequestHandler('tools/call', async (request) => {
  if (request.params.name === 'hello_world') {
    const { name } = request.params.arguments;
    return {
      content: [
        {
          type: 'text',
          text: `Hello, ${name}! Welcome to AI-Shell plugins.`,
        },
      ],
    };
  }

  throw new Error(`Unknown tool: ${request.params.name}`);
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('My First Plugin MCP server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
```

---

## Plugin API Reference

### MCPPluginManager

Main class for plugin management.

#### Constructor

```typescript
constructor(
  discoveryPaths: string[] = [],
  pluginOptions: {
    autoLoad?: boolean;        // Auto-load discovered plugins
    cacheEnabled?: boolean;    // Enable metadata caching
    validateSignatures?: boolean; // Validate plugin signatures
  } = {}
)
```

#### Methods

**Discovery:**

```typescript
// Add plugin discovery path
addDiscoveryPath(pluginPath: string): void

// Discover plugins in configured paths
async discoverPlugins(): Promise<DiscoveryResult>

// Discovery result
interface DiscoveryResult {
  found: number;
  loaded: number;
  errors: Array<{ plugin: string; error: Error }>;
  plugins: Map<string, PluginInstance>;
}
```

**Lifecycle Management:**

```typescript
// Load a plugin
async loadPlugin(metadata: PluginMetadata): Promise<PluginInstance>

// Unload a plugin
async unloadPlugin(pluginName: string): Promise<void>

// Reload a plugin
async reloadPlugin(pluginName: string): Promise<void>

// Enable plugin
async enablePlugin(pluginName: string): Promise<void>

// Disable plugin
async disablePlugin(pluginName: string): Promise<void>
```

**Query Methods:**

```typescript
// Get plugin by name
getPlugin(pluginName: string): PluginInstance | undefined

// Get all plugins
getAllPlugins(): PluginInstance[]

// Get plugins by capability
getPluginsByCapability(capability: PluginCapability): PluginInstance[]

// Get plugins by state
getPluginsByState(state: PluginState): PluginInstance[]

// Get plugin statistics
getStatistics(): {
  total: number;
  loaded: number;
  active: number;
  error: number;
  disabled: number;
  byCapability: Record<string, number>;
}
```

**Configuration:**

```typescript
// Set MCP client
setMCPClient(client: IMCPClient): void

// Get plugin options
getPluginOptions(): PluginOptions

// Export configuration
exportConfiguration(): string
```

#### Events

```typescript
interface PluginManagerEvents {
  pluginDiscovered: (name: string, metadata: PluginMetadata) => void;
  pluginLoaded: (name: string, instance: PluginInstance) => void;
  pluginUnloaded: (name: string) => void;
  pluginError: (name: string, error: Error) => void;
  pluginStateChange: (name: string, state: PluginState) => void;
}

// Listen to events
pluginManager.on('pluginLoaded', (name, instance) => {
  console.log(`Plugin ${name} loaded successfully`);
});
```

### MCP Server Configuration

```typescript
interface MCPServerConfig {
  name: string;              // Server name
  command: string;           // Executable command
  args: string[];            // Command arguments
  type: 'stdio' | 'sse';    // Transport type
  reconnect?: {
    enabled: boolean;
    maxAttempts: number;
    delayMs: number;
    backoffMultiplier: number;
  };
}
```

---

## Creating Custom Plugins

### Step-by-Step Guide

#### 1. Create Plugin Structure

```bash
mkdir -p plugins/database-utils
cd plugins/database-utils
npm init -y
```

#### 2. Install Dependencies

```bash
npm install @modelcontextprotocol/sdk zod
```

#### 3. Define Plugin Metadata

**plugin.json:**

```json
{
  "name": "database-utils",
  "version": "1.0.0",
  "description": "Database utility tools for AI-Shell",
  "author": "Your Name <you@example.com>",
  "homepage": "https://github.com/username/database-utils",
  "keywords": ["database", "postgresql", "mysql", "utilities"],
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "zod": "^3.22.0",
    "pg": "^8.11.0"
  },
  "capabilities": ["tools", "resources"]
}
```

#### 4. Implement Plugin Server

**index.js:**

```javascript
#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { z } = require('zod');
const { Pool } = require('pg');

// Configuration
const config = {
  database: {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || '',
  },
};

// Database connection pool
const pool = new Pool(config.database);

// Create MCP server
const server = new Server(
  {
    name: 'database-utils',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// Register tools
server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'query_database',
        description: 'Execute SQL query on PostgreSQL database',
        inputSchema: z.object({
          query: z.string().describe('SQL query to execute'),
          params: z.array(z.any()).optional().describe('Query parameters'),
        }),
      },
      {
        name: 'list_tables',
        description: 'List all tables in the database',
        inputSchema: z.object({}),
      },
      {
        name: 'describe_table',
        description: 'Get table schema information',
        inputSchema: z.object({
          tableName: z.string().describe('Name of the table'),
        }),
      },
    ],
  };
});

// Handle tool execution
server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'query_database':
        return await handleQueryDatabase(args);

      case 'list_tables':
        return await handleListTables();

      case 'describe_table':
        return await handleDescribeTable(args);

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Tool handlers
async function handleQueryDatabase({ query, params = [] }) {
  const result = await pool.query(query, params);
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(result.rows, null, 2),
      },
    ],
  };
}

async function handleListTables() {
  const result = await pool.query(`
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name
  `);

  return {
    content: [
      {
        type: 'text',
        text: result.rows.map(row => row.table_name).join('\n'),
      },
    ],
  };
}

async function handleDescribeTable({ tableName }) {
  const result = await pool.query(`
    SELECT
      column_name,
      data_type,
      is_nullable,
      column_default
    FROM information_schema.columns
    WHERE table_name = $1
    ORDER BY ordinal_position
  `, [tableName]);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(result.rows, null, 2),
      },
    ],
  };
}

// Register resources
server.setRequestHandler('resources/list', async () => {
  return {
    resources: [
      {
        uri: 'database://schema',
        name: 'Database Schema',
        description: 'Complete database schema information',
        mimeType: 'application/json',
      },
    ],
  };
});

// Handle resource reads
server.setRequestHandler('resources/read', async (request) => {
  const { uri } = request.params;

  if (uri === 'database://schema') {
    const tables = await pool.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'public'
    `);

    const schema = {};
    for (const { table_name } of tables.rows) {
      const columns = await pool.query(`
        SELECT * FROM information_schema.columns
        WHERE table_name = $1
      `, [table_name]);
      schema[table_name] = columns.rows;
    }

    return {
      contents: [
        {
          uri,
          mimeType: 'application/json',
          text: JSON.stringify(schema, null, 2),
        },
      ],
    };
  }

  throw new Error(`Unknown resource: ${uri}`);
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Database Utils MCP server running on stdio');
}

// Cleanup on exit
process.on('SIGINT', async () => {
  await pool.end();
  process.exit(0);
});

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
```

#### 5. Add Tests

**tests/index.test.js:**

```javascript
const { describe, it, expect, beforeAll, afterAll } = require('@jest/globals');
const { spawn } = require('child_process');

describe('Database Utils Plugin', () => {
  let serverProcess;

  beforeAll(() => {
    // Start plugin server
    serverProcess = spawn('node', ['index.js']);
  });

  afterAll(() => {
    if (serverProcess) {
      serverProcess.kill();
    }
  });

  it('should list available tools', async () => {
    // Test implementation
    expect(true).toBe(true);
  });

  it('should execute database queries', async () => {
    // Test implementation
    expect(true).toBe(true);
  });
});
```

---

## Testing Plugins

### Unit Testing

```bash
# Install testing dependencies
npm install --save-dev jest @types/jest

# Run tests
npm test
```

**Example test:**

```javascript
const { MCPPluginManager } = require('../../src/mcp/plugin-manager');

describe('Custom Plugin', () => {
  let pluginManager;

  beforeEach(() => {
    pluginManager = new MCPPluginManager(['./plugins']);
  });

  it('should load plugin successfully', async () => {
    const result = await pluginManager.discoverPlugins();
    expect(result.loaded).toBeGreaterThan(0);
  });

  it('should register tools', async () => {
    const plugin = pluginManager.getPlugin('my-plugin');
    expect(plugin.tools).toBeDefined();
    expect(plugin.tools.length).toBeGreaterThan(0);
  });
});
```

### Integration Testing

```javascript
const { MCPClient } = require('../../src/mcp/client');

describe('Plugin Integration', () => {
  let client;

  beforeAll(async () => {
    client = new MCPClient();
    await client.connect('my-plugin');
  });

  it('should call plugin tool', async () => {
    const result = await client.callTool('my-plugin', 'my_tool', {
      arg1: 'value1',
    });
    expect(result).toBeDefined();
  });
});
```

### Manual Testing

```bash
# Load plugin in AI-Shell
ai-shell plugin load ./plugins/my-plugin

# Test tool execution
ai-shell execute my-plugin my_tool --arg1 value1

# Check plugin status
ai-shell plugin status my-plugin

# View logs
tail -f ~/.ai-shell/logs/plugins/my-plugin.log
```

---

## Publishing Plugins

### NPM Publication

#### 1. Prepare Package

```bash
# Update version
npm version patch  # or minor, major

# Build if needed
npm run build

# Test package
npm pack
tar -xzf *.tgz
```

#### 2. Publish to NPM

```bash
# Login to NPM
npm login

# Publish package
npm publish --access public

# Tag release
git tag v1.0.0
git push origin v1.0.0
```

### AI-Shell Plugin Registry

```bash
# Submit to official registry
ai-shell plugin submit \
  --name my-plugin \
  --repo https://github.com/username/my-plugin \
  --description "My awesome plugin"

# Verify submission
ai-shell plugin search my-plugin
```

### Documentation Requirements

- **README.md**: Installation and usage instructions
- **CHANGELOG.md**: Version history
- **LICENSE**: Software license (MIT recommended)
- **examples/**: Usage examples
- **docs/**: API documentation

### Quality Checklist

- [ ] All tests passing
- [ ] Code coverage > 80%
- [ ] No security vulnerabilities
- [ ] Documentation complete
- [ ] Examples provided
- [ ] Semantic versioning
- [ ] License included
- [ ] CI/CD configured

---

## Example Plugin Implementations

### 1. REST API Plugin

```javascript
const axios = require('axios');

server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'http_request',
        description: 'Make HTTP requests',
        inputSchema: z.object({
          url: z.string().url(),
          method: z.enum(['GET', 'POST', 'PUT', 'DELETE']),
          headers: z.record(z.string()).optional(),
          data: z.any().optional(),
        }),
      },
    ],
  };
});

server.setRequestHandler('tools/call', async (request) => {
  const { url, method, headers, data } = request.params.arguments;

  const response = await axios({
    url,
    method,
    headers,
    data,
  });

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(response.data, null, 2),
      },
    ],
  };
});
```

### 2. File System Plugin

```javascript
const fs = require('fs').promises;
const path = require('path');

server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'read_file',
        description: 'Read file contents',
        inputSchema: z.object({
          path: z.string(),
        }),
      },
      {
        name: 'write_file',
        description: 'Write content to file',
        inputSchema: z.object({
          path: z.string(),
          content: z.string(),
        }),
      },
    ],
  };
});

server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;

  if (name === 'read_file') {
    const content = await fs.readFile(args.path, 'utf-8');
    return { content: [{ type: 'text', text: content }] };
  }

  if (name === 'write_file') {
    await fs.writeFile(args.path, args.content);
    return { content: [{ type: 'text', text: 'File written successfully' }] };
  }
});
```

### 3. Data Processing Plugin

```javascript
const { Transform } = require('stream');

server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'process_csv',
        description: 'Process CSV data',
        inputSchema: z.object({
          data: z.string(),
          transform: z.enum(['uppercase', 'lowercase', 'sort']),
        }),
      },
    ],
  };
});

server.setRequestHandler('tools/call', async (request) => {
  const { data, transform } = request.params.arguments;

  const rows = data.split('\n').map(row => row.split(','));

  switch (transform) {
    case 'uppercase':
      return processRows(rows, cell => cell.toUpperCase());
    case 'lowercase':
      return processRows(rows, cell => cell.toLowerCase());
    case 'sort':
      return processRows(rows.sort(), cell => cell);
  }
});

function processRows(rows, fn) {
  const processed = rows.map(row => row.map(fn));
  return {
    content: [{
      type: 'text',
      text: processed.map(row => row.join(',')).join('\n'),
    }],
  };
}
```

---

## Best Practices

### Security

1. **Input Validation**
   - Always validate and sanitize inputs
   - Use Zod schemas for type safety
   - Prevent path traversal attacks
   - Sanitize SQL queries

2. **Credential Management**
   - Use environment variables for secrets
   - Never hardcode credentials
   - Support credential vault integration

3. **Resource Limits**
   - Implement timeouts
   - Limit memory usage
   - Rate limit operations

### Performance

1. **Connection Pooling**
   ```javascript
   const pool = new Pool({
     max: 20,
     idleTimeoutMillis: 30000,
     connectionTimeoutMillis: 2000,
   });
   ```

2. **Caching**
   ```javascript
   const cache = new Map();

   async function getCached(key, fn) {
     if (cache.has(key)) {
       return cache.get(key);
     }
     const value = await fn();
     cache.set(key, value);
     return value;
   }
   ```

3. **Async Operations**
   - Use async/await consistently
   - Handle promises properly
   - Implement proper error handling

### Error Handling

```javascript
server.setRequestHandler('tools/call', async (request) => {
  try {
    // Tool implementation
  } catch (error) {
    console.error('Tool error:', error);
    return {
      content: [{
        type: 'text',
        text: `Error: ${error.message}`,
      }],
      isError: true,
    };
  }
});
```

### Logging

```javascript
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'plugin.log' }),
  ],
});

logger.info('Plugin operation', { tool: 'my_tool', args });
```

---

## Troubleshooting

### Common Issues

#### Plugin Not Loading

**Problem:** Plugin fails to load

**Solutions:**
- Check plugin.json syntax
- Verify all required capabilities declared
- Check for missing dependencies
- Review plugin logs

```bash
# Check plugin status
ai-shell plugin status my-plugin

# View detailed logs
ai-shell plugin logs my-plugin --verbose
```

#### Connection Failures

**Problem:** Cannot connect to MCP server

**Solutions:**
- Verify server is running
- Check stdio transport configuration
- Review reconnection settings
- Test with manual MCP client

#### Tool Execution Errors

**Problem:** Tool fails during execution

**Solutions:**
- Validate input schemas
- Check error handling
- Review tool implementation
- Test with sample data

### Debug Mode

```bash
# Enable debug logging
export DEBUG=aishell:plugin:*

# Run AI-Shell with verbose output
ai-shell --verbose --log-level debug

# View plugin manager logs
tail -f ~/.ai-shell/logs/plugin-manager.log
```

### Testing Locally

```bash
# Test plugin in isolation
node index.js

# Send test request via stdio
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | node index.js

# Use MCP inspector
npm install -g @modelcontextprotocol/inspector
mcp-inspector node index.js
```

---

## Resources

### Documentation

- [MCP Specification](https://modelcontextprotocol.io/docs)
- [AI-Shell API Reference](../api/core.md)
- [TypeScript Guidelines](https://www.typescriptlang.org/docs/)

### Tools

- [MCP SDK](https://github.com/modelcontextprotocol/sdk)
- [Plugin Template](https://github.com/ai-shell/plugin-template)
- [Testing Utilities](https://github.com/ai-shell/plugin-test-utils)

### Community

- [Discord Server](https://discord.gg/ai-shell)
- [GitHub Discussions](https://github.com/ai-shell/ai-shell/discussions)
- [Plugin Registry](https://plugins.ai-shell.dev)

---

## Appendix

### Plugin Checklist

- [ ] Plugin metadata complete
- [ ] MCP server implemented
- [ ] Tools registered
- [ ] Input validation added
- [ ] Error handling implemented
- [ ] Tests written (>80% coverage)
- [ ] Documentation created
- [ ] Examples provided
- [ ] Security review completed
- [ ] Performance optimized
- [ ] Published to registry

### Version History

- **v2.0.0** (Oct 2025): Complete plugin system with MCP integration
- **v1.5.0** (Sep 2025): Added resource support
- **v1.0.0** (Aug 2025): Initial plugin architecture

---

**Document Version:** 2.0.0
**Last Updated:** October 28, 2025
**Next Review:** January 2026
