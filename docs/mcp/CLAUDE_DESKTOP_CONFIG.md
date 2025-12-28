# Claude Desktop Configuration for AI-Shell MCP Server

## Quick Setup

1. **Build AI-Shell**
   ```bash
   cd /path/to/ai-shell
   npm install
   npm run build
   ```

2. **Find your Claude Desktop config file**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

3. **Add AI-Shell MCP server to config**
   ```json
   {
     "mcpServers": {
       "ai-shell-database": {
         "command": "node",
         "args": ["/absolute/path/to/ai-shell/dist/mcp/server.js", "start"]
       }
     }
   }
   ```

4. **Restart Claude Desktop**

## Example Configurations

### Basic Configuration

```json
{
  "mcpServers": {
    "ai-shell-database": {
      "command": "node",
      "args": ["/Users/username/projects/ai-shell/dist/mcp/server.js", "start"]
    }
  }
}
```

### Multiple MCP Servers

```json
{
  "mcpServers": {
    "ai-shell-database": {
      "command": "node",
      "args": ["/path/to/ai-shell/dist/mcp/server.js", "start"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token-here"
      }
    }
  }
}
```

### Using with npm global install

If you install AI-Shell globally:

```bash
npm install -g ai-shell
```

Then you can use:

```json
{
  "mcpServers": {
    "ai-shell-database": {
      "command": "ai-shell-mcp-server",
      "args": ["start"]
    }
  }
}
```

## Using AI-Shell Database Tools in Claude

Once configured, you can ask Claude to perform database operations:

### Examples

**Connect to a database:**
> "Connect to my PostgreSQL database at localhost:5432, database 'myapp', username 'postgres', password 'secret'"

**Query data:**
> "Query all users from the users table where age is greater than 18"

**Get table schema:**
> "Show me the schema for the users table"

**Optimize tables:**
> "Run VACUUM ANALYZE on the users table"

**MongoDB operations:**
> "Find all documents in the 'products' collection where price is greater than 100"

**Redis operations:**
> "Get the value of the key 'user:12345' from Redis"

## Available Tools

After configuration, Claude will have access to 70+ database tools:

### Common Tools (All Databases)
- `db_connect` - Connect to database
- `db_disconnect` - Disconnect
- `db_query` - Execute SELECT queries
- `db_execute` - Execute DDL/DML statements
- `db_list_tables` - List tables/collections
- `db_describe_table` - Get table schema
- `db_get_indexes` - List indexes
- `db_health_check` - Check connection health

### PostgreSQL Tools
- `pg_explain` - Analyze query plans
- `pg_vacuum` - Reclaim storage
- `pg_analyze` - Update statistics
- `pg_get_stats` - Table statistics
- `pg_table_size` - Get table sizes
- `pg_active_queries` - List running queries
- `pg_kill_query` - Terminate queries

### MySQL Tools
- `mysql_explain` - Query execution plans
- `mysql_optimize` - Optimize tables
- `mysql_analyze` - Analyze tables
- `mysql_table_status` - Table status
- `mysql_processlist` - Running queries
- `mysql_variables` - System variables

### MongoDB Tools
- `mongo_find` - Query documents
- `mongo_aggregate` - Aggregation pipelines
- `mongo_insert` - Insert documents
- `mongo_update` - Update documents
- `mongo_delete` - Delete documents
- `mongo_create_index` - Create indexes
- `mongo_list_indexes` - List indexes
- `mongo_get_stats` - Collection statistics

### Redis Tools
- `redis_get`, `redis_set`, `redis_del` - Key operations
- `redis_keys`, `redis_scan` - Key discovery
- `redis_hgetall`, `redis_hset` - Hash operations
- `redis_lrange`, `redis_lpush` - List operations
- `redis_info` - Server information
- `redis_dbsize` - Database size

## Resources

Claude can also access resources:

- `db://connection/{name}` - Connection information
- `db://schema/{database}/{table}` - Table schemas
- `db://query/{id}` - Cached query results

## Troubleshooting

### Server Not Appearing in Claude

1. **Check config file location**
   ```bash
   # macOS
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

   # Linux
   cat ~/.config/Claude/claude_desktop_config.json
   ```

2. **Verify absolute path**
   ```bash
   ls -la /path/to/ai-shell/dist/mcp/server.js
   ```

3. **Test server directly**
   ```bash
   node /path/to/ai-shell/dist/mcp/server.js info
   ```

4. **Check Claude Desktop logs**
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`
   - Linux: `~/.local/share/Claude/logs/`

### Connection Errors

Test database connection outside of MCP:

```bash
ai-shell-mcp-server test-connection \
  --type postgresql \
  --host localhost \
  --port 5432 \
  --database mydb \
  --username user \
  --password pass
```

### Rebuilding After Changes

```bash
cd /path/to/ai-shell
npm run build
# Restart Claude Desktop
```

## Security Notes

- **Passwords not stored**: Connection passwords are not persisted to disk
- **Local execution**: MCP server runs locally on your machine
- **No external network**: Server only communicates with local Claude Desktop
- **Connection pooling**: Automatic connection management and cleanup
- **Parameterized queries**: Protection against SQL injection

## Advanced Configuration

### Custom Environment Variables

```json
{
  "mcpServers": {
    "ai-shell-database": {
      "command": "node",
      "args": ["/path/to/ai-shell/dist/mcp/server.js", "start"],
      "env": {
        "NODE_ENV": "production",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

### Development Mode

For development with hot reload:

```json
{
  "mcpServers": {
    "ai-shell-database": {
      "command": "ts-node",
      "args": ["/path/to/ai-shell/src/mcp/server.ts", "start"]
    }
  }
}
```

## Next Steps

1. Read the [full documentation](DATABASE_SERVER.md)
2. Check available [database tools](DATABASE_SERVER.md#mcp-tools-reference)
3. See [connection examples](DATABASE_SERVER.md#connection-examples)
4. Explore [resource providers](DATABASE_SERVER.md#mcp-resources)

## Support

- GitHub Issues: https://github.com/your-org/ai-shell/issues
- Documentation: https://github.com/your-org/ai-shell/docs
- MCP Specification: https://spec.modelcontextprotocol.io/
