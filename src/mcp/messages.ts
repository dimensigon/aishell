/**
 * MCP Message Builder
 * Constructs protocol-compliant messages for MCP communication
 */

import { v4 as uuidv4 } from 'uuid';
import {
  MCPMessage,
  MCPRequest,
  MCPResponse,
  MCPError,
  MCPMethod,
  MCPContext,
  MCP_PROTOCOL_VERSION
} from './types';

/**
 * MCP Message Builder Class
 */
export class MCPMessageBuilder {
  /**
   * Create a JSON-RPC 2.0 request message
   */
  static createRequest(
    method: string,
    params?: unknown,
    id?: string | number
  ): MCPRequest {
    return {
      jsonrpc: '2.0',
      id: id ?? uuidv4(),
      method,
      params
    };
  }

  /**
   * Create a JSON-RPC 2.0 response message
   */
  static createResponse(
    id: string | number,
    result?: unknown,
    error?: MCPError
  ): MCPResponse {
    const response: MCPResponse = {
      jsonrpc: '2.0',
      id
    };

    if (error) {
      response.error = error;
    } else {
      response.result = result;
    }

    return response;
  }

  /**
   * Create a notification message (no response expected)
   */
  static createNotification(method: string, params?: unknown): MCPMessage {
    return {
      jsonrpc: '2.0',
      method,
      params
    };
  }

  /**
   * Create an error response
   */
  static createError(
    id: string | number,
    code: number,
    message: string,
    data?: unknown
  ): MCPResponse {
    return {
      jsonrpc: '2.0',
      id,
      error: {
        code,
        message,
        data
      }
    };
  }

  /**
   * Create initialization request
   */
  static createInitializeRequest(
    clientInfo: {
      name: string;
      version: string;
    },
    capabilities?: {
      tools?: boolean;
      resources?: boolean;
      prompts?: boolean;
    }
  ): MCPRequest {
    return this.createRequest(MCPMethod.INITIALIZE, {
      protocolVersion: MCP_PROTOCOL_VERSION,
      clientInfo,
      capabilities: capabilities || {
        tools: true,
        resources: true,
        prompts: true
      }
    });
  }

  /**
   * Create tools/list request
   */
  static createToolsListRequest(): MCPRequest {
    return this.createRequest(MCPMethod.TOOLS_LIST);
  }

  /**
   * Create tools/call request
   */
  static createToolsCallRequest(
    toolName: string,
    args?: Record<string, unknown>
  ): MCPRequest {
    return this.createRequest(MCPMethod.TOOLS_CALL, {
      name: toolName,
      arguments: args || {}
    });
  }

  /**
   * Create resources/list request
   */
  static createResourcesListRequest(): MCPRequest {
    return this.createRequest(MCPMethod.RESOURCES_LIST);
  }

  /**
   * Create resources/read request
   */
  static createResourcesReadRequest(uri: string): MCPRequest {
    return this.createRequest(MCPMethod.RESOURCES_READ, {
      uri
    });
  }

  /**
   * Create prompts/list request
   */
  static createPromptsListRequest(): MCPRequest {
    return this.createRequest(MCPMethod.PROMPTS_LIST);
  }

  /**
   * Create prompts/get request
   */
  static createPromptsGetRequest(
    name: string,
    args?: Record<string, unknown>
  ): MCPRequest {
    return this.createRequest(MCPMethod.PROMPTS_GET, {
      name,
      arguments: args || {}
    });
  }

  /**
   * Create context/update notification
   */
  static createContextUpdateNotification(context: Partial<MCPContext>): MCPMessage {
    return this.createNotification(MCPMethod.CONTEXT_UPDATE, {
      context: {
        ...context,
        timestamp: Date.now()
      }
    });
  }

  /**
   * Create context/sync request
   */
  static createContextSyncRequest(context: MCPContext): MCPRequest {
    return this.createRequest(MCPMethod.CONTEXT_SYNC, {
      context
    });
  }

  /**
   * Create shutdown notification
   */
  static createShutdownNotification(): MCPMessage {
    return this.createNotification(MCPMethod.SHUTDOWN);
  }

  /**
   * Validate message structure
   */
  static isValidMessage(message: unknown): message is MCPMessage {
    if (typeof message !== 'object' || message === null) {
      return false;
    }

    const msg = message as Partial<MCPMessage>;

    // Must have jsonrpc: "2.0"
    if (msg.jsonrpc !== '2.0') {
      return false;
    }

    // Request: must have method
    if (msg.method && typeof msg.method === 'string') {
      return true;
    }

    // Response: must have id and (result or error)
    if (msg.id !== undefined && (msg.result !== undefined || msg.error !== undefined)) {
      return true;
    }

    return false;
  }

  /**
   * Parse message from JSON string
   */
  static parseMessage(json: string): MCPMessage {
    try {
      const message = JSON.parse(json);

      if (!this.isValidMessage(message)) {
        throw new Error('Invalid MCP message structure');
      }

      return message;
    } catch (error) {
      throw new Error(
        `Failed to parse MCP message: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Serialize message to JSON string
   */
  static serializeMessage(message: MCPMessage): string {
    if (!this.isValidMessage(message)) {
      throw new Error('Cannot serialize invalid MCP message');
    }

    return JSON.stringify(message);
  }

  /**
   * Extract error from response
   */
  static extractError(response: MCPResponse): MCPError | null {
    return response.error || null;
  }

  /**
   * Check if message is a request
   */
  static isRequest(message: MCPMessage): message is MCPRequest {
    return message.method !== undefined && message.id !== undefined;
  }

  /**
   * Check if message is a response
   */
  static isResponse(message: MCPMessage): message is MCPResponse {
    return message.id !== undefined && (message.result !== undefined || message.error !== undefined);
  }

  /**
   * Check if message is a notification
   */
  static isNotification(message: MCPMessage): boolean {
    return message.method !== undefined && message.id === undefined;
  }

  /**
   * Create standard error codes
   */
  static readonly ErrorCodes = {
    PARSE_ERROR: -32700,
    INVALID_REQUEST: -32600,
    METHOD_NOT_FOUND: -32601,
    INVALID_PARAMS: -32602,
    INTERNAL_ERROR: -32603,
    SERVER_ERROR: -32000,
    TIMEOUT_ERROR: -32001,
    CONNECTION_ERROR: -32002,
    RESOURCE_NOT_FOUND: -32003
  } as const;
}
