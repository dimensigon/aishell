/**
 * MCP Database Server Implementation
 * Provides database operations as MCP tools and resources
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema
} from '@modelcontextprotocol/sdk/types.js';

import { DatabaseConnectionManager } from '../cli/database-manager';
import { StateManager } from '../core/state-manager';
import { createLogger } from '../core/logger';

import { CommonDatabaseTools } from './tools/common';
import { PostgreSQLTools } from './tools/postgresql';
import { MySQLTools } from './tools/mysql';
import { MongoDBTools } from './tools/mongodb';
import { RedisTools } from './tools/redis';

const logger = createLogger('MCPDatabaseServer');

/**
 * MCP Database Server
 */
export class MCPDatabaseServer {
  private server: Server;
  private connectionManager: DatabaseConnectionManager;
  private stateManager: StateManager;

  // Tool providers
  private commonTools: CommonDatabaseTools;
  private postgresTools: PostgreSQLTools;
  private mysqlTools: MySQLTools;
  private mongoTools: MongoDBTools;
  private redisTools: RedisTools;

  // Query result cache for resources
  private queryResults = new Map<string, any>();
  private queryIdCounter = 0;

  constructor() {
    // Initialize state manager
    this.stateManager = new StateManager();

    // Initialize connection manager
    this.connectionManager = new DatabaseConnectionManager(this.stateManager);

    // Initialize tool providers
    this.commonTools = new CommonDatabaseTools(this.connectionManager);
    this.postgresTools = new PostgreSQLTools(this.connectionManager);
    this.mysqlTools = new MySQLTools(this.connectionManager);
    this.mongoTools = new MongoDBTools(this.connectionManager);
    this.redisTools = new RedisTools(this.connectionManager);

    // Create MCP server
    this.server = new Server(
      {
        name: 'ai-shell-database',
        version: '1.0.0'
      },
      {
        capabilities: {
          tools: {},
          resources: {}
        }
      }
    );

    this.setupHandlers();
    logger.info('MCP Database Server initialized');
  }

  /**
   * Setup MCP request handlers
   */
  private setupHandlers(): void {
    // Tools list handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      const tools = [
        ...this.commonTools.getToolDefinitions(),
        ...this.postgresTools.getToolDefinitions(),
        ...this.mysqlTools.getToolDefinitions(),
        ...this.mongoTools.getToolDefinitions(),
        ...this.redisTools.getToolDefinitions()
      ];

      logger.info('Listed tools', { count: tools.length });
      return { tools };
    });

    // Tool call handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      logger.info('Tool called', { name, args });

      try {
        let result: any;

        // Route to appropriate tool provider
        if (name.startsWith('db_') && !name.startsWith('db_')) {
          result = await this.commonTools.executeTool(name, args);
        } else if (name.startsWith('pg_')) {
          result = await this.postgresTools.executeTool(name, args);
        } else if (name.startsWith('mysql_')) {
          result = await this.mysqlTools.executeTool(name, args);
        } else if (name.startsWith('mongo_')) {
          result = await this.mongoTools.executeTool(name, args);
        } else if (name.startsWith('redis_')) {
          result = await this.redisTools.executeTool(name, args);
        } else if (name.startsWith('db_')) {
          result = await this.commonTools.executeTool(name, args);
        } else {
          throw new Error(`Unknown tool: ${name}`);
        }

        // Cache query results for resource access
        if (name === 'db_query' || name.includes('_find') || name.includes('_aggregate')) {
          const queryId = this.cacheQueryResult(result);
          result.queryId = queryId;
          result.resourceUri = `db://query/${queryId}`;
        }

        logger.info('Tool executed successfully', { name, success: true });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }
          ]
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logger.error('Tool execution failed', error instanceof Error ? error : new Error(errorMessage), { name });

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: false,
                error: errorMessage
              }, null, 2)
            }
          ],
          isError: true
        };
      }
    });

    // Resources list handler
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      const resources: any[] = [];

      // Add connection resources
      const connections = this.connectionManager.listConnections();
      connections.forEach(conn => {
        resources.push({
          uri: `db://connection/${conn.name}`,
          name: `Connection: ${conn.name}`,
          description: `${conn.type} database connection`,
          mimeType: 'application/json'
        });
      });

      // Add query result resources
      this.queryResults.forEach((result, id) => {
        resources.push({
          uri: `db://query/${id}`,
          name: `Query Result ${id}`,
          description: 'Cached query result',
          mimeType: 'application/json'
        });
      });

      logger.info('Listed resources', { count: resources.length });
      return { resources };
    });

    // Resource read handler
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;

      logger.info('Resource read requested', { uri });

      try {
        let content: any;

        if (uri.startsWith('db://connection/')) {
          const connectionName = uri.replace('db://connection/', '');
          const connection = this.connectionManager.getConnection(connectionName);

          if (!connection) {
            throw new Error(`Connection not found: ${connectionName}`);
          }

          content = {
            name: connection.config.name,
            type: connection.type,
            database: connection.config.database,
            host: connection.config.host,
            port: connection.config.port,
            isConnected: connection.isConnected,
            lastHealthCheck: connection.lastHealthCheck
          };
        } else if (uri.startsWith('db://query/')) {
          const queryId = uri.replace('db://query/', '');
          content = this.queryResults.get(queryId);

          if (!content) {
            throw new Error(`Query result not found: ${queryId}`);
          }
        } else if (uri.startsWith('db://schema/')) {
          // Format: db://schema/{database}/{table}
          const parts = uri.replace('db://schema/', '').split('/');
          if (parts.length !== 2) {
            throw new Error('Invalid schema URI format. Expected: db://schema/{database}/{table}');
          }

          const [database, table] = parts;

          // Get schema using common tools
          content = await this.commonTools.executeTool('db_describe_table', { table });
        } else {
          throw new Error(`Unknown resource URI: ${uri}`);
        }

        logger.info('Resource read successfully', { uri });

        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify(content, null, 2)
            }
          ]
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logger.error('Resource read failed', error instanceof Error ? error : new Error(errorMessage), { uri });

        throw new Error(`Failed to read resource: ${errorMessage}`);
      }
    });

    logger.info('MCP request handlers configured');
  }

  /**
   * Cache query result and return ID
   */
  private cacheQueryResult(result: any): string {
    const id = `${++this.queryIdCounter}`;
    this.queryResults.set(id, result);

    // Limit cache size
    if (this.queryResults.size > 100) {
      const firstKey = this.queryResults.keys().next().value;
      this.queryResults.delete(firstKey);
    }

    return id;
  }

  /**
   * Start the server with stdio transport
   */
  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);

    logger.info('MCP Database Server started with stdio transport');
  }

  /**
   * Cleanup and shutdown
   */
  async shutdown(): Promise<void> {
    logger.info('Shutting down MCP Database Server');
    await this.connectionManager.disconnectAll();
    await this.server.close();
    logger.info('MCP Database Server stopped');
  }
}

/**
 * Main entry point
 */
async function main() {
  const server = new MCPDatabaseServer();

  // Handle graceful shutdown
  process.on('SIGINT', async () => {
    await server.shutdown();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    await server.shutdown();
    process.exit(0);
  });

  await server.start();
}

// Run server if executed directly
if (require.main === module) {
  main().catch((error) => {
    logger.error('Failed to start server', error);
    process.exit(1);
  });
}

export default MCPDatabaseServer;
