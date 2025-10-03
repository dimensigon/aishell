/**
 * MCP Protocol Types and Interfaces
 * Defines core types for Model Context Protocol integration
 */

import { EventEmitter } from 'eventemitter3';

/**
 * MCP Protocol Version
 */
export const MCP_PROTOCOL_VERSION = '2024-11-05';

/**
 * MCP Message Types
 */
export enum MCPMessageType {
  REQUEST = 'request',
  RESPONSE = 'response',
  NOTIFICATION = 'notification',
  ERROR = 'error'
}

/**
 * MCP Method Names
 */
export enum MCPMethod {
  INITIALIZE = 'initialize',
  INITIALIZED = 'initialized',
  SHUTDOWN = 'shutdown',
  TOOLS_LIST = 'tools/list',
  TOOLS_CALL = 'tools/call',
  RESOURCES_LIST = 'resources/list',
  RESOURCES_READ = 'resources/read',
  PROMPTS_LIST = 'prompts/list',
  PROMPTS_GET = 'prompts/get',
  CONTEXT_UPDATE = 'context/update',
  CONTEXT_SYNC = 'context/sync'
}

/**
 * Connection State
 */
export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

/**
 * Base MCP Message
 */
export interface MCPMessage {
  jsonrpc: '2.0';
  id?: string | number;
  method?: string;
  params?: unknown;
  result?: unknown;
  error?: MCPError;
}

/**
 * MCP Error
 */
export interface MCPError {
  code: number;
  message: string;
  data?: unknown;
}

/**
 * MCP Request Message
 */
export interface MCPRequest extends MCPMessage {
  method: string;
  params?: unknown;
}

/**
 * MCP Response Message
 */
export interface MCPResponse extends MCPMessage {
  id: string | number;
  result?: unknown;
  error?: MCPError;
}

/**
 * MCP Server Configuration
 */
export interface MCPServerConfig {
  name: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
  type: 'stdio' | 'websocket';
  reconnect?: {
    enabled: boolean;
    maxAttempts: number;
    delayMs: number;
    backoffMultiplier: number;
  };
}

/**
 * MCP Client Configuration
 */
export interface MCPClientConfig {
  servers: MCPServerConfig[];
  timeout?: number;
  maxConcurrentRequests?: number;
  contextSyncInterval?: number;
}

/**
 * MCP Tool Definition
 */
export interface MCPTool {
  name: string;
  description?: string;
  inputSchema: {
    type: 'object';
    properties?: Record<string, unknown>;
    required?: string[];
  };
}

/**
 * MCP Resource Definition
 */
export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

/**
 * MCP Context
 */
export interface MCPContext {
  sessionId: string;
  workingDirectory: string;
  environment: Record<string, string>;
  metadata: Record<string, unknown>;
  timestamp: number;
}

/**
 * Connection Event Types
 */
export interface ConnectionEvents {
  connected: (serverName: string) => void;
  disconnected: (serverName: string, error?: Error) => void;
  reconnecting: (serverName: string, attempt: number) => void;
  error: (serverName: string, error: Error) => void;
  message: (serverName: string, message: MCPMessage) => void;
  stateChange: (serverName: string, state: ConnectionState) => void;
}

/**
 * MCP Client Events Interface
 */
export interface MCPClientEvents extends ConnectionEvents {
  contextSync: (context: MCPContext) => void;
  toolsUpdated: (serverName: string, tools: MCPTool[]) => void;
  resourcesUpdated: (serverName: string, resources: MCPResource[]) => void;
}

/**
 * MCP Client Interface
 */
export interface IMCPClient extends EventEmitter<MCPClientEvents> {
  connect(serverName?: string): Promise<void>;
  disconnect(serverName?: string): Promise<void>;
  request(serverName: string, method: string, params?: unknown): Promise<unknown>;
  notify(serverName: string, method: string, params?: unknown): Promise<void>;
  getConnectionState(serverName: string): ConnectionState;
  listTools(serverName?: string): Promise<MCPTool[]>;
  listResources(serverName?: string): Promise<MCPResource[]>;
  syncContext(context: MCPContext): Promise<void>;
}

/**
 * Reconnection Options
 */
export interface ReconnectionOptions {
  enabled: boolean;
  maxAttempts: number;
  delayMs: number;
  backoffMultiplier: number;
}

/**
 * Request Options
 */
export interface RequestOptions {
  timeout?: number;
  retries?: number;
  priority?: 'low' | 'normal' | 'high';
}
