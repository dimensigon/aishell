# AI-Shell MCP Database Server

Production-ready Model Context Protocol (MCP) server for database operations in AI-Shell.

## Quick Links

- 🚀 [Quick Start Guide](CLAUDE_DESKTOP_CONFIG.md) - Get started in 5 minutes
- 📚 [Complete Documentation](DATABASE_SERVER.md) - Full reference for all 70+ tools
- 📋 [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Technical overview
- 🧪 [Tests](../../tests/mcp/database-server.test.ts) - Test suite

## What is This?

An MCP server that exposes all AI-Shell database functionality to Claude Desktop and other MCP clients. Connect to PostgreSQL, MySQL, SQLite, MongoDB, and Redis databases directly from Claude conversations.

## Features

✅ **70+ Database Tools** - Complete database operations
✅ **5 Database Types** - PostgreSQL, MySQL, SQLite, MongoDB, Redis
✅ **Connection Management** - Pooling, health checks, auto-reconnect
✅ **Resource Providers** - Access connections, schemas, and query results
✅ **Type-Safe** - Full TypeScript implementation
✅ **Production Ready** - Comprehensive testing and error handling
✅ **Claude Desktop** - Seamless integration via MCP protocol

## Quick Start

### 1. Install & Build

```bash
cd /path/to/ai-shell
npm install
npm run build
```

### 2. Configure Claude Desktop

Edit your `claude_desktop_config.json`:

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

**Config locations:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

### 3. Restart Claude Desktop

That's it! Claude now has access to your databases.

## Support

- 📖 [Full Documentation](DATABASE_SERVER.md)
- 🐛 [Report Issues](https://github.com/your-org/ai-shell/issues)

---

**Made with ❤️ for the Claude Code community**
