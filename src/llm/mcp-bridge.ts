/**
 * LLM-MCP Bridge
 * Seamless integration between LLM providers and MCP tools/resources
 */

import { EventEmitter } from 'eventemitter3';
import { ILLMProvider } from './provider';
import { IMCPClient, MCPTool, MCPResource } from '../mcp/types';
import { LLMMessage, LLMResponse, GenerateOptions } from '../types/llm';

/**
 * Tool execution result
 */
export interface ToolExecutionResult {
  toolName: string;
  success: boolean;
  result?: any;
  error?: Error;
  duration: number;
  timestamp: number;
}

/**
 * Bridge context
 */
export interface BridgeContext {
  sessionId: string;
  conversationHistory: LLMMessage[];
  availableTools: MCPTool[];
  availableResources: MCPResource[];
  metadata: Record<string, any>;
}

/**
 * Bridge events
 */
export interface BridgeEvents {
  toolCall: (toolName: string, params: any) => void;
  toolResult: (result: ToolExecutionResult) => void;
  resourceAccess: (uri: string) => void;
  contextUpdate: (context: BridgeContext) => void;
  streamChunk: (chunk: string) => void;
  error: (error: Error) => void;
}

/**
 * LLM request with MCP tools
 */
export interface EnhancedGenerateOptions extends GenerateOptions {
  enableTools?: boolean;
  enableResources?: boolean;
  maxToolCalls?: number;
  toolCallTimeout?: number;
  resourceCache?: boolean;
}

/**
 * Enhanced LLM response with tool usage
 */
export interface EnhancedLLMResponse extends LLMResponse {
  toolCalls?: ToolExecutionResult[];
  resourcesAccessed?: string[];
  iterations: number;
}

/**
 * LLM-MCP Bridge
 */
export class LLMMCPBridge extends EventEmitter<BridgeEvents> {
  private context: BridgeContext;
  private toolCallCount = 0;
  private resourceCache = new Map<string, any>();

  constructor(
    private llmProvider: ILLMProvider,
    private mcpClient: IMCPClient,
    private readonly config: {
      maxIterations?: number;
      toolCallTimeout?: number;
      enableAutoContext?: boolean;
      cacheResources?: boolean;
    } = {}
  ) {
    super();

    this.context = {
      sessionId: this.generateSessionId(),
      conversationHistory: [],
      availableTools: [],
      availableResources: [],
      metadata: {}
    };

    this.initializeContext();
  }

  /**
   * Initialize bridge context
   */
  private async initializeContext(): Promise<void> {
    try {
      // Load available tools and resources
      this.context.availableTools = await this.mcpClient.listTools();
      this.context.availableResources = await this.mcpClient.listResources();

      this.emit('contextUpdate', this.context);
    } catch (error) {
      console.error('Failed to initialize bridge context:', error);
    }
  }

  /**
   * Generate response with MCP tool integration
   */
  async generate(options: EnhancedGenerateOptions): Promise<EnhancedLLMResponse> {
    const maxIterations = this.config.maxIterations || 10;
    const maxToolCalls = options.maxToolCalls || 10;

    let iterations = 0;
    let messages = [...options.messages];
    const toolCalls: ToolExecutionResult[] = [];
    const resourcesAccessed: string[] = [];

    // Add tool context to system message if enabled
    if (options.enableTools && this.context.availableTools.length > 0) {
      messages = this.injectToolContext(messages);
    }

    while (iterations < maxIterations) {
      iterations++;

      // Generate LLM response
      const response = await this.llmProvider.generate({
        ...options,
        messages
      });

      // Update conversation history
      this.context.conversationHistory.push({
        role: 'assistant',
        content: response.content
      });

      // Check for tool calls in response
      const toolCallsFound = this.extractToolCalls(response.content);

      if (toolCallsFound.length === 0 || !options.enableTools) {
        // No tool calls, return final response
        return {
          ...response,
          toolCalls,
          resourcesAccessed,
          iterations
        };
      }

      // Execute tool calls
      for (const toolCall of toolCallsFound) {
        if (this.toolCallCount >= maxToolCalls) {
          console.warn(`Maximum tool calls (${maxToolCalls}) reached`);
          break;
        }

        const result = await this.executeToolCall(
          toolCall.name,
          toolCall.params,
          options.toolCallTimeout
        );

        toolCalls.push(result);
        this.toolCallCount++;

        // Add tool result to messages
        messages.push({
          role: 'assistant',
          content: `Tool call: ${toolCall.name}`
        });

        messages.push({
          role: 'user',
          content: `Tool result: ${JSON.stringify(result.result)}`
        });
      }

      // Check if max iterations reached
      if (iterations >= maxIterations) {
        console.warn(`Maximum iterations (${maxIterations}) reached`);
        break;
      }
    }

    // Return final response from last iteration
    const finalResponse = await this.llmProvider.generate({
      ...options,
      messages
    });

    return {
      ...finalResponse,
      toolCalls,
      resourcesAccessed,
      iterations
    };
  }

  /**
   * Generate streaming response with MCP tool integration
   */
  async *generateStream(
    options: EnhancedGenerateOptions
  ): AsyncGenerator<string, EnhancedLLMResponse, undefined> {
    const messages = options.enableTools
      ? this.injectToolContext([...options.messages])
      : [...options.messages];

    const toolCalls: ToolExecutionResult[] = [];
    let accumulatedContent = '';

    // Stream from LLM
    await this.llmProvider.generateStream(
      { ...options, messages },
      {
        onChunk: (chunk) => {
          accumulatedContent += chunk;
          this.emit('streamChunk', chunk);
        },
        onComplete: () => {
          // Complete
        },
        onError: (error) => {
          this.emit('error', error);
          throw error;
        }
      }
    );

    // Check for tool calls in accumulated content
    const toolCallsFound = this.extractToolCalls(accumulatedContent);

    if (toolCallsFound.length > 0 && options.enableTools) {
      yield '\n\n[Executing tools...]\n';

      for (const toolCall of toolCallsFound) {
        const result = await this.executeToolCall(toolCall.name, toolCall.params);
        toolCalls.push(result);

        yield `\n[Tool: ${toolCall.name}] ${result.success ? '✓' : '✗'}\n`;
      }
    }

    return {
      content: accumulatedContent,
      model: 'unknown',
      toolCalls,
      resourcesAccessed: [],
      iterations: 1,
      usage: {
        prompt_tokens: 0,
        completion_tokens: 0,
        total_tokens: 0
      }
    };
  }

  /**
   * Execute MCP tool call
   */
  async executeToolCall(
    toolName: string,
    params: any,
    timeout?: number
  ): Promise<ToolExecutionResult> {
    const startTime = Date.now();
    this.emit('toolCall', toolName, params);

    try {
      // Find the server that has this tool
      const servers: string[] = [];
      let result: any = null;

      for (const server of servers) {
        const tools = await this.mcpClient.listTools(server);
        const tool = tools.find((t) => t.name === toolName);

        if (tool) {
          // Execute tool call with timeout
          const executePromise = this.mcpClient.request(server, 'tools/call', {
            name: toolName,
            arguments: params
          });

          if (timeout) {
            result = await this.executeWithTimeout(executePromise, timeout);
          } else {
            result = await executePromise;
          }
          break;
        }
      }

      if (result === null) {
        throw new Error(`Tool not found: ${toolName}`);
      }

      const executionResult: ToolExecutionResult = {
        toolName,
        success: true,
        result,
        duration: Date.now() - startTime,
        timestamp: Date.now()
      };

      this.emit('toolResult', executionResult);
      return executionResult;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      const executionResult: ToolExecutionResult = {
        toolName,
        success: false,
        error: err,
        duration: Date.now() - startTime,
        timestamp: Date.now()
      };

      this.emit('toolResult', executionResult);
      return executionResult;
    }
  }

  /**
   * Access MCP resource
   */
  async accessResource(uri: string): Promise<any> {
    this.emit('resourceAccess', uri);

    // Check cache
    if (this.config.cacheResources && this.resourceCache.has(uri)) {
      return this.resourceCache.get(uri);
    }

    try {
      // Find the server that has this resource
      const servers: string[] = [];

      for (const server of servers) {
        const resources = await this.mcpClient.listResources(server);
        const resource = resources.find((r) => r.uri === uri);

        if (resource) {
          const content = await this.mcpClient.request(server, 'resources/read', {
            uri
          });

          // Cache if enabled
          if (this.config.cacheResources) {
            this.resourceCache.set(uri, content);
          }

          return content;
        }
      }

      throw new Error(`Resource not found: ${uri}`);
    } catch (error) {
      this.emit('error', error instanceof Error ? error : new Error(String(error)));
      throw error;
    }
  }

  /**
   * Inject tool context into messages
   */
  private injectToolContext(messages: LLMMessage[]): LLMMessage[] {
    const toolContext = this.formatToolContext();

    // Find or create system message
    const systemMessageIndex = messages.findIndex((m) => m.role === 'system');

    if (systemMessageIndex >= 0) {
      // Append to existing system message
      messages[systemMessageIndex].content += '\n\n' + toolContext;
    } else {
      // Add new system message
      messages.unshift({
        role: 'system',
        content: toolContext
      });
    }

    return messages;
  }

  /**
   * Format tool context for LLM
   */
  private formatToolContext(): string {
    const toolDescriptions = this.context.availableTools.map((tool) => {
      const params = tool.inputSchema.properties
        ? Object.entries(tool.inputSchema.properties)
            .map(([name, schema]) => `${name}: ${JSON.stringify(schema)}`)
            .join(', ')
        : 'none';

      return `- ${tool.name}: ${tool.description || 'No description'}\n  Parameters: {${params}}`;
    });

    return `
Available Tools:
${toolDescriptions.join('\n')}

To use a tool, include in your response:
[TOOL_CALL]
{
  "name": "tool_name",
  "params": { ... }
}
[/TOOL_CALL]
`.trim();
  }

  /**
   * Extract tool calls from LLM response
   */
  private extractToolCalls(content: string): Array<{ name: string; params: any }> {
    const toolCalls: Array<{ name: string; params: any }> = [];
    const regex = /\[TOOL_CALL\]([\s\S]*?)\[\/TOOL_CALL\]/g;
    let match;

    while ((match = regex.exec(content)) !== null) {
      try {
        const toolCall = JSON.parse(match[1].trim());
        toolCalls.push(toolCall);
      } catch (error) {
        console.error('Failed to parse tool call:', error);
      }
    }

    return toolCalls;
  }

  /**
   * Execute with timeout
   */
  private async executeWithTimeout<T>(promise: Promise<T>, timeout: number): Promise<T> {
    return Promise.race([
      promise,
      new Promise<T>((_, reject) =>
        setTimeout(() => reject(new Error(`Timeout after ${timeout}ms`)), timeout)
      )
    ]);
  }

  /**
   * Update context metadata
   */
  updateContext(metadata: Record<string, any>): void {
    this.context.metadata = { ...this.context.metadata, ...metadata };
    this.emit('contextUpdate', this.context);
  }

  /**
   * Get current context
   */
  getContext(): BridgeContext {
    return { ...this.context };
  }

  /**
   * Clear conversation history
   */
  clearHistory(): void {
    this.context.conversationHistory = [];
    this.toolCallCount = 0;
  }

  /**
   * Clear resource cache
   */
  clearCache(): void {
    this.resourceCache.clear();
  }

  /**
   * Get statistics
   */
  getStatistics(): {
    toolCallCount: number;
    conversationLength: number;
    cachedResources: number;
    availableTools: number;
    availableResources: number;
  } {
    return {
      toolCallCount: this.toolCallCount,
      conversationLength: this.context.conversationHistory.length,
      cachedResources: this.resourceCache.size,
      availableTools: this.context.availableTools.length,
      availableResources: this.context.availableResources.length
    };
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Refresh available tools and resources
   */
  async refresh(): Promise<void> {
    await this.initializeContext();
  }
}
