/**
 * MCP Tool Executor
 * Validates and executes MCP tools with type checking, security, and error handling
 */

import { EventEmitter } from 'eventemitter3';
import { IMCPClient, MCPTool } from './types';

/**
 * Tool execution context
 */
export interface ToolExecutionContext {
  userId?: string;
  sessionId: string;
  permissions: string[];
  timeout?: number;
  metadata: Record<string, any>;
}

/**
 * Tool execution result
 */
export interface ToolExecutionResult<T = any> {
  success: boolean;
  tool: string;
  result?: T;
  error?: ExecutionError;
  duration: number;
  timestamp: number;
  validationErrors?: ValidationError[];
}

/**
 * Validation error
 */
export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

/**
 * Execution error
 */
export interface ExecutionError {
  code: string;
  message: string;
  details?: any;
  stack?: string;
}

/**
 * Tool validator
 */
export interface ToolValidator {
  validate(tool: MCPTool, params: any): ValidationError[];
}

/**
 * Security policy
 */
export interface SecurityPolicy {
  allowedTools?: string[];
  deniedTools?: string[];
  requirePermissions?: Record<string, string[]>;
  rateLimit?: {
    maxCalls: number;
    windowMs: number;
  };
}

/**
 * Executor events
 */
export interface ToolExecutorEvents {
  executionStart: (tool: string, params: any) => void;
  executionComplete: (result: ToolExecutionResult) => void;
  executionError: (tool: string, error: ExecutionError) => void;
  validationError: (tool: string, errors: ValidationError[]) => void;
  rateLimitExceeded: (tool: string) => void;
  securityViolation: (tool: string, reason: string) => void;
}

/**
 * Rate limiter
 */
class RateLimiter {
  private calls = new Map<string, number[]>();

  constructor(
    private maxCalls: number,
    private windowMs: number
  ) {}

  isAllowed(key: string): boolean {
    const now = Date.now();
    const calls = this.calls.get(key) || [];

    // Remove old calls outside window
    const validCalls = calls.filter((timestamp) => now - timestamp < this.windowMs);

    if (validCalls.length >= this.maxCalls) {
      return false;
    }

    validCalls.push(now);
    this.calls.set(key, validCalls);
    return true;
  }

  reset(key?: string): void {
    if (key) {
      this.calls.delete(key);
    } else {
      this.calls.clear();
    }
  }
}

/**
 * JSON Schema Validator
 */
class JSONSchemaValidator implements ToolValidator {
  validate(tool: MCPTool, params: any): ValidationError[] {
    const errors: ValidationError[] = [];
    const schema = tool.inputSchema;

    if (!schema || !schema.properties) {
      return errors;
    }

    // Check required fields
    if (schema.required) {
      for (const field of schema.required) {
        if (!(field in params)) {
          errors.push({
            field,
            message: `Required field '${field}' is missing`,
            code: 'REQUIRED_FIELD_MISSING'
          });
        }
      }
    }

    // Validate field types
    for (const [field, fieldSchema] of Object.entries(schema.properties)) {
      if (field in params) {
        const value = params[field];
        const fieldSchemaObj = fieldSchema as any;

        if (fieldSchemaObj.type) {
          const actualType = Array.isArray(value) ? 'array' : typeof value;
          if (actualType !== fieldSchemaObj.type && fieldSchemaObj.type !== 'object') {
            errors.push({
              field,
              message: `Field '${field}' should be of type '${fieldSchemaObj.type}' but got '${actualType}'`,
              code: 'INVALID_TYPE'
            });
          }
        }

        // Validate enum
        if (fieldSchemaObj.enum && !fieldSchemaObj.enum.includes(value)) {
          errors.push({
            field,
            message: `Field '${field}' must be one of: ${fieldSchemaObj.enum.join(', ')}`,
            code: 'INVALID_ENUM_VALUE'
          });
        }

        // Validate string length
        if (fieldSchemaObj.type === 'string' && typeof value === 'string') {
          if (fieldSchemaObj.minLength && value.length < fieldSchemaObj.minLength) {
            errors.push({
              field,
              message: `Field '${field}' must be at least ${fieldSchemaObj.minLength} characters`,
              code: 'STRING_TOO_SHORT'
            });
          }
          if (fieldSchemaObj.maxLength && value.length > fieldSchemaObj.maxLength) {
            errors.push({
              field,
              message: `Field '${field}' must be at most ${fieldSchemaObj.maxLength} characters`,
              code: 'STRING_TOO_LONG'
            });
          }
        }

        // Validate number range
        if (fieldSchemaObj.type === 'number' && typeof value === 'number') {
          if (fieldSchemaObj.minimum !== undefined && value < fieldSchemaObj.minimum) {
            errors.push({
              field,
              message: `Field '${field}' must be at least ${fieldSchemaObj.minimum}`,
              code: 'NUMBER_TOO_SMALL'
            });
          }
          if (fieldSchemaObj.maximum !== undefined && value > fieldSchemaObj.maximum) {
            errors.push({
              field,
              message: `Field '${field}' must be at most ${fieldSchemaObj.maximum}`,
              code: 'NUMBER_TOO_LARGE'
            });
          }
        }
      }
    }

    return errors;
  }
}

/**
 * MCP Tool Executor
 */
export class MCPToolExecutor extends EventEmitter<ToolExecutorEvents> {
  private validator: ToolValidator;
  private rateLimiter: RateLimiter | null = null;
  private executionCache = new Map<string, ToolExecutionResult>();
  private toolCache = new Map<string, MCPTool>();

  constructor(
    private mcpClient: IMCPClient,
    private securityPolicy: SecurityPolicy = {},
    private config: {
      enableCache?: boolean;
      cacheTTL?: number;
      enableValidation?: boolean;
    } = {}
  ) {
    super();
    this.validator = new JSONSchemaValidator();

    // Setup rate limiter
    if (securityPolicy.rateLimit) {
      this.rateLimiter = new RateLimiter(
        securityPolicy.rateLimit.maxCalls,
        securityPolicy.rateLimit.windowMs
      );
    }

    this.initializeToolCache();
  }

  /**
   * Initialize tool cache
   */
  private async initializeToolCache(): Promise<void> {
    try {
      const tools = await this.mcpClient.listTools();
      tools.forEach((tool) => {
        this.toolCache.set(tool.name, tool);
      });
    } catch (error) {
      console.error('Failed to initialize tool cache:', error);
    }
  }

  /**
   * Execute tool
   */
  async execute<T = any>(
    toolName: string,
    params: any,
    context: ToolExecutionContext
  ): Promise<ToolExecutionResult<T>> {
    const startTime = Date.now();
    this.emit('executionStart', toolName, params);

    try {
      // Check cache
      if (this.config.enableCache) {
        const cached = this.getCachedResult<T>(toolName, params);
        if (cached) {
          return cached;
        }
      }

      // Security checks
      await this.performSecurityChecks(toolName, context);

      // Get tool definition
      const tool = await this.getTool(toolName);

      // Validate parameters
      if (this.config.enableValidation !== false) {
        const validationErrors = this.validator.validate(tool, params);
        if (validationErrors.length > 0) {
          this.emit('validationError', toolName, validationErrors);
          return {
            success: false,
            tool: toolName,
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Parameter validation failed',
              details: validationErrors
            },
            duration: Date.now() - startTime,
            timestamp: Date.now(),
            validationErrors
          };
        }
      }

      // Execute tool
      const result = await this.executeWithTimeout(toolName, params, context.timeout);

      const executionResult: ToolExecutionResult<T> = {
        success: true,
        tool: toolName,
        result,
        duration: Date.now() - startTime,
        timestamp: Date.now()
      };

      // Cache result
      if (this.config.enableCache) {
        this.cacheResult(toolName, params, executionResult);
      }

      this.emit('executionComplete', executionResult);
      return executionResult;
    } catch (error) {
      const executionError: ExecutionError = {
        code: error instanceof Error && error.name ? error.name : 'EXECUTION_ERROR',
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined
      };

      const result: ToolExecutionResult<T> = {
        success: false,
        tool: toolName,
        error: executionError,
        duration: Date.now() - startTime,
        timestamp: Date.now()
      };

      this.emit('executionError', toolName, executionError);
      return result;
    }
  }

  /**
   * Execute multiple tools in parallel
   */
  async executeBatch<T = any>(
    executions: Array<{ tool: string; params: any }>,
    context: ToolExecutionContext
  ): Promise<ToolExecutionResult<T>[]> {
    return Promise.all(executions.map((exec) => this.execute<T>(exec.tool, exec.params, context)));
  }

  /**
   * Execute tool with timeout
   */
  private async executeWithTimeout(toolName: string, params: any, timeout?: number): Promise<any> {
    const executePromise = this.executeTool(toolName, params);

    if (timeout) {
      return Promise.race([
        executePromise,
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error(`Tool execution timeout after ${timeout}ms`)), timeout)
        )
      ]);
    }

    return executePromise;
  }

  /**
   * Execute tool via MCP client
   */
  private async executeTool(toolName: string, params: any): Promise<any> {
    // Find server that has this tool
    const servers: string[] = [];

    for (const server of servers) {
      const tools = await this.mcpClient.listTools(server);
      const tool = tools.find((t) => t.name === toolName);

      if (tool) {
        return await this.mcpClient.request(server, 'tools/call', {
          name: toolName,
          arguments: params
        });
      }
    }

    throw new Error(`Tool not found: ${toolName}`);
  }

  /**
   * Perform security checks
   */
  private async performSecurityChecks(toolName: string, context: ToolExecutionContext): Promise<void> {
    // Check allowed/denied tools
    if (this.securityPolicy.allowedTools && !this.securityPolicy.allowedTools.includes(toolName)) {
      this.emit('securityViolation', toolName, 'Tool not in allowed list');
      throw new Error(`Tool '${toolName}' is not allowed`);
    }

    if (this.securityPolicy.deniedTools && this.securityPolicy.deniedTools.includes(toolName)) {
      this.emit('securityViolation', toolName, 'Tool is denied');
      throw new Error(`Tool '${toolName}' is denied`);
    }

    // Check permissions
    if (this.securityPolicy.requirePermissions) {
      const requiredPerms = this.securityPolicy.requirePermissions[toolName];
      if (requiredPerms) {
        const hasPermission = requiredPerms.every((perm) => context.permissions.includes(perm));
        if (!hasPermission) {
          this.emit('securityViolation', toolName, 'Insufficient permissions');
          throw new Error(`Insufficient permissions for tool '${toolName}'`);
        }
      }
    }

    // Check rate limit
    if (this.rateLimiter) {
      const rateLimitKey = `${context.userId || 'anonymous'}:${toolName}`;
      if (!this.rateLimiter.isAllowed(rateLimitKey)) {
        this.emit('rateLimitExceeded', toolName);
        throw new Error(`Rate limit exceeded for tool '${toolName}'`);
      }
    }
  }

  /**
   * Get tool definition
   */
  private async getTool(toolName: string): Promise<MCPTool> {
    // Check cache first
    if (this.toolCache.has(toolName)) {
      return this.toolCache.get(toolName)!;
    }

    // Fetch from MCP client
    const tools = await this.mcpClient.listTools();
    const tool = tools.find((t) => t.name === toolName);

    if (!tool) {
      throw new Error(`Tool not found: ${toolName}`);
    }

    this.toolCache.set(toolName, tool);
    return tool;
  }

  /**
   * Get cached result
   */
  private getCachedResult<T = any>(toolName: string, params: any): ToolExecutionResult<T> | null {
    const cacheKey = this.getCacheKey(toolName, params);
    const cached = this.executionCache.get(cacheKey);

    if (cached) {
      const age = Date.now() - cached.timestamp;
      const ttl = this.config.cacheTTL || 60000;

      if (age < ttl) {
        return cached as ToolExecutionResult<T>;
      } else {
        this.executionCache.delete(cacheKey);
      }
    }

    return null;
  }

  /**
   * Cache execution result
   */
  private cacheResult(toolName: string, params: any, result: ToolExecutionResult): void {
    const cacheKey = this.getCacheKey(toolName, params);
    this.executionCache.set(cacheKey, result);
  }

  /**
   * Generate cache key
   */
  private getCacheKey(toolName: string, params: any): string {
    return `${toolName}:${JSON.stringify(params)}`;
  }

  /**
   * Clear execution cache
   */
  clearCache(toolName?: string): void {
    if (toolName) {
      // Clear specific tool cache
      const keysToDelete: string[] = [];
      for (const key of this.executionCache.keys()) {
        if (key.startsWith(`${toolName}:`)) {
          keysToDelete.push(key);
        }
      }
      keysToDelete.forEach((key) => this.executionCache.delete(key));
    } else {
      // Clear all cache
      this.executionCache.clear();
    }
  }

  /**
   * Refresh tool cache
   */
  async refreshToolCache(): Promise<void> {
    await this.initializeToolCache();
  }

  /**
   * Update security policy
   */
  updateSecurityPolicy(policy: Partial<SecurityPolicy>): void {
    this.securityPolicy = { ...this.securityPolicy, ...policy };

    // Update rate limiter if needed
    if (policy.rateLimit) {
      this.rateLimiter = new RateLimiter(policy.rateLimit.maxCalls, policy.rateLimit.windowMs);
    }
  }

  /**
   * Get available tools
   */
  getAvailableTools(): MCPTool[] {
    return Array.from(this.toolCache.values());
  }

  /**
   * Get tool by name
   */
  getToolDefinition(toolName: string): MCPTool | undefined {
    return this.toolCache.get(toolName);
  }

  /**
   * Get execution statistics
   */
  getStatistics(): {
    cacheSize: number;
    toolCount: number;
    cacheHitRate: number;
  } {
    return {
      cacheSize: this.executionCache.size,
      toolCount: this.toolCache.size,
      cacheHitRate: 0 // TODO: Track hits/misses
    };
  }
}
