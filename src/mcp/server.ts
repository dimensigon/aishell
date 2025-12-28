#!/usr/bin/env node
/**
 * MCP Database Server Launcher
 * CLI for starting the MCP database server with different transports
 */

import { Command } from 'commander';
import { MCPDatabaseServer } from './database-server';
import { createLogger } from '../core/logger';

const logger = createLogger('MCPServerLauncher');

const program = new Command();

program
  .name('ai-shell-mcp-server')
  .description('AI-Shell MCP Database Server')
  .version('1.0.0');

program
  .command('start')
  .description('Start the MCP server with stdio transport')
  .action(async () => {
    try {
      logger.info('Starting MCP Database Server...');
      const server = new MCPDatabaseServer();

      // Handle graceful shutdown
      const shutdown = async () => {
        logger.info('Received shutdown signal');
        await server.shutdown();
        process.exit(0);
      };

      process.on('SIGINT', shutdown);
      process.on('SIGTERM', shutdown);

      await server.start();
      logger.info('MCP Database Server is running');
    } catch (error) {
      logger.error('Failed to start server', error as Error);
      process.exit(1);
    }
  });

program
  .command('info')
  .description('Show server information')
  .action(() => {
    console.log(`
AI-Shell MCP Database Server
Version: 1.0.0

Supported Databases:
  - PostgreSQL
  - MySQL
  - SQLite
  - MongoDB
  - Redis

Available Tools:
  Common:    db_connect, db_disconnect, db_query, db_execute, db_list_tables, etc.
  PostgreSQL: pg_explain, pg_vacuum, pg_analyze, pg_get_stats, etc.
  MySQL:     mysql_explain, mysql_optimize, mysql_analyze, etc.
  MongoDB:   mongo_find, mongo_aggregate, mongo_insert, mongo_update, etc.
  Redis:     redis_get, redis_set, redis_keys, redis_info, etc.

Resources:
  - db://connection/{name}     Connection information
  - db://schema/{db}/{table}   Table schema
  - db://query/{id}            Query results

For Claude Desktop integration, add to your claude_desktop_config.json:
{
  "mcpServers": {
    "ai-shell-database": {
      "command": "node",
      "args": ["/path/to/ai-shell/dist/mcp/server.js", "start"]
    }
  }
}
    `);
  });

program
  .command('test-connection')
  .description('Test database connection')
  .requiredOption('-t, --type <type>', 'Database type (postgresql, mysql, sqlite, mongodb, redis)')
  .option('-h, --host <host>', 'Database host')
  .option('-p, --port <port>', 'Database port', parseInt)
  .option('-d, --database <database>', 'Database name')
  .option('-u, --username <username>', 'Username')
  .option('-w, --password <password>', 'Password')
  .option('-c, --connection-string <string>', 'Connection string')
  .action(async (options) => {
    try {
      const { DatabaseConnectionManager } = await import('../cli/database-manager');
      const { StateManager } = await import('../core/state-manager');

      const stateManager = new StateManager();
      const connectionManager = new DatabaseConnectionManager(stateManager);

      const config: any = {
        name: 'test',
        type: options.type,
        host: options.host,
        port: options.port,
        database: options.database,
        username: options.username,
        password: options.password,
        connectionString: options.connectionString
      };

      console.log('Testing connection...');
      const result = await connectionManager.testConnection(config);

      if (result.healthy) {
        console.log(`✓ Connection successful (${result.latency}ms)`);
      } else {
        console.log(`✗ Connection failed: ${result.error}`);
      }

      await connectionManager.disconnectAll();
    } catch (error) {
      console.error('Error testing connection:', error);
      process.exit(1);
    }
  });

// Default action - start server
if (process.argv.length === 2) {
  process.argv.push('start');
}

program.parse();
