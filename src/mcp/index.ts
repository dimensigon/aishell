/**
 * MCP Module Entry Point
 * Exports all MCP client functionality
 */

// Core Client
export { MCPClient } from './client';
export { MCPMessageBuilder } from './messages';
export { MCPContextAdapter } from './context-adapter';
export { MCPErrorHandler } from './error-handler';
export { MCPResourceManager } from './resource-manager';

// Types
export * from './types';

// Re-export commonly used types
export type {
  MCPClientConfig,
  MCPServerConfig,
  MCPContext,
  MCPTool,
  MCPResource,
  MCPMessage,
  MCPRequest,
  MCPResponse,
  MCPError,
  ConnectionState,
  IMCPClient
} from './types';

// Constants
export { MCP_PROTOCOL_VERSION, MCPMessageType, MCPMethod } from './types';

/**
 * Create a configured MCP client instance
 */
import { MCPClient } from './client';
import { MCPClientConfig } from './types';

export function createMCPClient(config: MCPClientConfig): MCPClient {
  return new MCPClient(config);
}

/**
 * Create MCP client from .mcp.json configuration
 */
import { readFileSync } from 'fs';
import { join } from 'path';

export function createMCPClientFromConfig(
  configPath: string = '.mcp.json'
): MCPClient {
  try {
    const configFile = readFileSync(configPath, 'utf-8');
    const config = JSON.parse(configFile);

    if (!config.mcpServers) {
      throw new Error('Invalid MCP configuration: missing mcpServers');
    }

    const servers = Object.entries(config.mcpServers).map(([name, serverConfig]: [string, any]) => ({
      name,
      command: serverConfig.command,
      args: serverConfig.args || [],
      env: serverConfig.env,
      type: serverConfig.type || 'stdio',
      reconnect: {
        enabled: true,
        maxAttempts: 5,
        delayMs: 1000,
        backoffMultiplier: 2
      }
    }));

    return new MCPClient({
      servers,
      timeout: 30000,
      maxConcurrentRequests: 10,
      contextSyncInterval: 60000 // 1 minute
    });
  } catch (error) {
    throw new Error(
      `Failed to create MCP client from config: ${
        error instanceof Error ? error.message : 'Unknown error'
      }`
    );
  }
}

/**
 * Utility: Load MCP client with default configuration
 */
export async function loadDefaultMCPClient(): Promise<MCPClient> {
  const configPaths = [
    join(process.cwd(), '.mcp.json'),
    join(process.env.HOME || '~', '.mcp.json')
  ];

  for (const path of configPaths) {
    try {
      const client = createMCPClientFromConfig(path);
      await client.connect();
      return client;
    } catch (error) {
      // Try next path
      continue;
    }
  }

  throw new Error('No valid MCP configuration found');
}
