# AI-Shell MCP Database Server

Complete Model Context Protocol (MCP) server implementation for database operations in AI-Shell.

## Overview

The MCP Database Server exposes all AI-Shell database functionality as MCP tools and resources, enabling seamless integration with Claude Desktop and other MCP clients.

## Features

- **Multi-Database Support**: PostgreSQL, MySQL, SQLite, MongoDB, Redis
- **70+ MCP Tools**: Common operations and database-specific optimizations
- **Resource Providers**: Access connection info, schemas, and query results
- **Connection Management**: Pool management, health checks, auto-reconnect
- **Type-Safe**: Full TypeScript implementation with type definitions

## Installation

### Install AI-Shell

```bash
npm install -g ai-shell
# or clone the repository
git clone https://github.com/your-org/ai-shell.git
cd ai-shell
npm install
npm run build
```

### Configure Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-shell-database": {
      "command": "node",
      "args": ["/path/to/ai-shell/dist/mcp/server.js", "start"]
    }
  }
}
```

**Config file locations:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

## Usage

### Starting the Server

```bash
# Start with stdio transport (for Claude Desktop)
node dist/mcp/server.js start

# Or using the CLI directly
ai-shell-mcp-server start

# Show server information
ai-shell-mcp-server info

# Test database connection
ai-shell-mcp-server test-connection \
  --type postgresql \
  --host localhost \
  --port 5432 \
  --database mydb \
  --username user \
  --password pass
```

### Programmatic Usage

```typescript
import { MCPDatabaseServer } from 'ai-shell/mcp/database-server';

const server = new MCPDatabaseServer();
await server.start();

// Server runs with stdio transport
// Graceful shutdown on SIGINT/SIGTERM
```

## MCP Tools Reference

### Common Database Tools

#### `db_connect`
Connect to a database.

```json
{
  "name": "mydb",
  "type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "testdb",
  "username": "user",
  "password": "pass",
  "ssl": true,
  "poolSize": 10
}
```

#### `db_disconnect`
Disconnect from a database.

```json
{
  "name": "mydb"
}
```

#### `db_list_connections`
List all active connections.

```json
{}
```

#### `db_switch_active`
Switch the active database connection.

```json
{
  "name": "mydb"
}
```

#### `db_health_check`
Check database connection health.

```json
{
  "name": "mydb"
}
```

#### `db_query`
Execute a SELECT query (PostgreSQL, MySQL, SQLite).

```json
{
  "sql": "SELECT * FROM users WHERE age > $1",
  "params": [18],
  "connection": "mydb"
}
```

#### `db_execute`
Execute DDL/DML statements.

```json
{
  "sql": "INSERT INTO users (name, email) VALUES ($1, $2)",
  "params": ["John", "john@example.com"]
}
```

#### `db_list_tables`
List all tables/collections.

```json
{
  "schema": "public"
}
```

#### `db_describe_table`
Get table schema.

```json
{
  "table": "users",
  "schema": "public"
}
```

#### `db_get_indexes`
List table indexes.

```json
{
  "table": "users",
  "schema": "public"
}
```

### PostgreSQL-Specific Tools

#### `pg_explain`
Analyze query execution plan.

```json
{
  "sql": "SELECT * FROM users WHERE age > 18",
  "analyze": true,
  "verbose": true,
  "buffers": true,
  "format": "json"
}
```

#### `pg_vacuum`
Reclaim storage and update statistics.

```json
{
  "table": "users",
  "full": false,
  "analyze": true,
  "verbose": true
}
```

#### `pg_analyze`
Update query planner statistics.

```json
{
  "table": "users",
  "verbose": true
}
```

#### `pg_get_stats`
Get detailed table statistics.

```json
{
  "table": "users",
  "schema": "public"
}
```

#### `pg_table_size`
Get table and index sizes.

```json
{
  "table": "users",
  "schema": "public"
}
```

#### `pg_active_queries`
List currently running queries.

```json
{}
```

#### `pg_kill_query`
Terminate a running query.

```json
{
  "pid": 12345
}
```

### MySQL-Specific Tools

#### `mysql_explain`
Get query execution plan.

```json
{
  "sql": "SELECT * FROM users WHERE age > 18",
  "format": "json"
}
```

#### `mysql_optimize`
Optimize table storage.

```json
{
  "table": "users"
}
```

#### `mysql_analyze`
Analyze table statistics.

```json
{
  "table": "users"
}
```

#### `mysql_table_status`
Get table status information.

```json
{
  "table": "users"
}
```

#### `mysql_processlist`
Show running queries.

```json
{
  "full": true
}
```

#### `mysql_kill_query`
Kill a query or connection.

```json
{
  "id": 123
}
```

#### `mysql_variables`
Show system variables.

```json
{
  "pattern": "innodb%"
}
```

### MongoDB-Specific Tools

#### `mongo_list_databases`
List all databases.

```json
{}
```

#### `mongo_list_collections`
List collections in database.

```json
{
  "database": "mydb"
}
```

#### `mongo_find`
Find documents in collection.

```json
{
  "collection": "users",
  "filter": { "age": { "$gt": 18 } },
  "limit": 10,
  "sort": { "name": 1 },
  "projection": { "name": 1, "email": 1 }
}
```

#### `mongo_aggregate`
Run aggregation pipeline.

```json
{
  "collection": "users",
  "pipeline": [
    { "$match": { "age": { "$gt": 18 } } },
    { "$group": { "_id": "$city", "count": { "$sum": 1 } } },
    { "$sort": { "count": -1 } }
  ]
}
```

#### `mongo_insert`
Insert documents.

```json
{
  "collection": "users",
  "documents": [
    { "name": "John", "email": "john@example.com" }
  ]
}
```

#### `mongo_update`
Update documents.

```json
{
  "collection": "users",
  "filter": { "name": "John" },
  "update": { "$set": { "age": 30 } },
  "upsert": false,
  "multi": false
}
```

#### `mongo_delete`
Delete documents.

```json
{
  "collection": "users",
  "filter": { "age": { "$lt": 18 } },
  "multi": true
}
```

#### `mongo_create_index`
Create collection index.

```json
{
  "collection": "users",
  "keys": { "email": 1 },
  "options": { "unique": true }
}
```

#### `mongo_list_indexes`
List collection indexes.

```json
{
  "collection": "users"
}
```

#### `mongo_get_stats`
Get collection statistics.

```json
{
  "collection": "users"
}
```

### Redis-Specific Tools

#### `redis_get`
Get key value.

```json
{
  "key": "user:123"
}
```

#### `redis_set`
Set key value.

```json
{
  "key": "user:123",
  "value": "John Doe",
  "ex": 3600,
  "nx": true
}
```

#### `redis_del`
Delete keys.

```json
{
  "keys": ["user:123", "user:456"]
}
```

#### `redis_keys`
Find keys by pattern.

```json
{
  "pattern": "user:*"
}
```

#### `redis_scan`
Incrementally iterate keys.

```json
{
  "cursor": 0,
  "match": "user:*",
  "count": 100
}
```

#### `redis_exists`
Check if keys exist.

```json
{
  "keys": ["user:123", "user:456"]
}
```

#### `redis_ttl`
Get key expiration time.

```json
{
  "key": "user:123"
}
```

#### `redis_expire`
Set key expiration.

```json
{
  "key": "user:123",
  "seconds": 3600
}
```

#### `redis_hgetall`
Get all hash fields.

```json
{
  "key": "user:123"
}
```

#### `redis_hset`
Set hash field.

```json
{
  "key": "user:123",
  "field": "name",
  "value": "John"
}
```

#### `redis_lrange`
Get list range.

```json
{
  "key": "queue",
  "start": 0,
  "stop": -1
}
```

#### `redis_lpush`
Prepend to list.

```json
{
  "key": "queue",
  "values": ["item1", "item2"]
}
```

#### `redis_info`
Get server information.

```json
{
  "section": "memory"
}
```

#### `redis_dbsize`
Get database key count.

```json
{}
```

#### `redis_flushdb`
Delete all keys in database.

```json
{
  "async": true
}
```

## MCP Resources

### Connection Resource
`db://connection/{name}`

Get information about a database connection.

```json
{
  "name": "mydb",
  "type": "postgresql",
  "database": "testdb",
  "host": "localhost",
  "port": 5432,
  "isConnected": true,
  "lastHealthCheck": 1234567890
}
```

### Schema Resource
`db://schema/{database}/{table}`

Get table schema definition.

```json
{
  "success": true,
  "table": "users",
  "columns": [
    {
      "column_name": "id",
      "data_type": "integer",
      "is_nullable": "NO",
      "column_default": "nextval('users_id_seq'::regclass)"
    }
  ],
  "columnCount": 5
}
```

### Query Result Resource
`db://query/{id}`

Access cached query results. Query results are automatically cached when using `db_query`, `mongo_find`, or `mongo_aggregate` tools.

```json
{
  "success": true,
  "rowCount": 10,
  "rows": [...],
  "queryId": "123",
  "resourceUri": "db://query/123"
}
```

## Connection Examples

### PostgreSQL

```typescript
// Using connection string
{
  "name": "prod-db",
  "type": "postgresql",
  "connectionString": "postgresql://user:pass@localhost:5432/mydb?ssl=true"
}

// Using individual parameters
{
  "name": "prod-db",
  "type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "pass",
  "ssl": true,
  "poolSize": 20
}
```

### MySQL

```typescript
{
  "name": "mysql-db",
  "type": "mysql",
  "host": "localhost",
  "port": 3306,
  "database": "mydb",
  "username": "root",
  "password": "password",
  "poolSize": 10
}
```

### SQLite

```typescript
// File-based
{
  "name": "local-db",
  "type": "sqlite",
  "database": "/path/to/database.db"
}

// In-memory
{
  "name": "temp-db",
  "type": "sqlite",
  "database": ":memory:"
}
```

### MongoDB

```typescript
// Connection string
{
  "name": "mongo-db",
  "type": "mongodb",
  "connectionString": "mongodb://user:pass@localhost:27017/mydb?authSource=admin"
}

// Atlas cluster
{
  "name": "atlas-db",
  "type": "mongodb",
  "connectionString": "mongodb+srv://user:pass@cluster0.mongodb.net/mydb"
}
```

### Redis

```typescript
// Standard connection
{
  "name": "redis-cache",
  "type": "redis",
  "host": "localhost",
  "port": 6379,
  "password": "password",
  "database": "0"
}

// Redis Cloud
{
  "name": "redis-cloud",
  "type": "redis",
  "connectionString": "rediss://user:pass@redis-12345.cloud.redislabs.com:12345"
}
```

## Development

### Building

```bash
npm run build
```

### Testing

```bash
# Run all tests
npm test

# Run MCP server tests
npm test tests/mcp/database-server.test.ts

# Run with coverage
npm run test:coverage
```

### Running Locally

```bash
# Development mode with ts-node
ts-node src/mcp/server.ts start

# Production mode
node dist/mcp/server.js start
```

## Architecture

```
src/mcp/
├── database-server.ts    # Main MCP server implementation
├── server.ts             # CLI launcher
└── tools/
    ├── common.ts         # Common database tools
    ├── postgresql.ts     # PostgreSQL-specific tools
    ├── mysql.ts          # MySQL-specific tools
    ├── mongodb.ts        # MongoDB-specific tools
    └── redis.ts          # Redis-specific tools
```

### Component Flow

```
Claude Desktop
    │
    ├─> MCP Client (stdio)
    │
    ├─> MCPDatabaseServer
    │   ├─> Tool Providers (70+ tools)
    │   ├─> Resource Providers (connections, schemas, queries)
    │   └─> Connection Manager
    │
    └─> Database Clients
        ├─> PostgreSQL (pg)
        ├─> MySQL (mysql2)
        ├─> SQLite (sqlite3)
        ├─> MongoDB (mongodb)
        └─> Redis (ioredis)
```

## Security Considerations

- **No Password Storage**: Passwords are not persisted to disk
- **Connection Pooling**: Automatic connection management
- **SSL/TLS Support**: Secure connections for all databases
- **Parameterized Queries**: Protection against SQL injection
- **Resource Limits**: Query result cache size limits

## Troubleshooting

### Server Not Starting

```bash
# Check if server is accessible
node dist/mcp/server.js info

# Test connection directly
node dist/mcp/server.js test-connection --type sqlite --database ":memory:"
```

### Claude Desktop Not Connecting

1. Check config file location and syntax
2. Verify absolute path to server.js
3. Check Claude Desktop logs:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`
   - Linux: `~/.local/share/Claude/logs/`

### Database Connection Issues

```bash
# Test connection outside of MCP
ai-shell-mcp-server test-connection \
  --type postgresql \
  --host localhost \
  --port 5432 \
  --database testdb \
  --username user \
  --password pass
```

## Performance Tips

- **Connection Pooling**: Use appropriate pool sizes (default: 10)
- **Query Limits**: Add LIMIT clauses to large queries
- **Index Usage**: Use `pg_explain` or `mysql_explain` to optimize queries
- **Resource Cache**: Query results cached for resource access (max 100)
- **Health Checks**: Automatic health checks every 30 seconds

## Contributing

Contributions welcome! Please see the main AI-Shell repository for contribution guidelines.

## License

MIT License - see LICENSE file for details.

## Related Documentation

- [AI-Shell Main Documentation](../README.md)
- [Database Connection Manager](../../src/cli/database-manager.ts)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/claude/docs/mcp)

## Support

- GitHub Issues: https://github.com/your-org/ai-shell/issues
- Documentation: https://github.com/your-org/ai-shell/docs
