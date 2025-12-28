/**
 * MCP Error Handler
 * Comprehensive error handling and recovery for MCP operations
 */

import { EventEmitter } from 'eventemitter3';
import { MCPError } from './types';
import { MCPMessageBuilder } from './messages';

/**
 * Error Codes
 */
export enum ErrorCode {
  CONNECTION_ERROR = 'CONNECTION_ERROR',
  TIMEOUT = 'TIMEOUT',
  PARSE_ERROR = 'PARSE_ERROR',
  AUTH_ERROR = 'AUTH_ERROR',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  NOT_FOUND = 'NOT_FOUND',
  RATE_LIMIT = 'RATE_LIMIT',
  UNKNOWN = 'UNKNOWN',
}

/**
 * Error Severity Levels
 */
export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

/**
 * Error Recovery Strategy
 */
export enum RecoveryStrategy {
  RETRY = 'retry',
  RECONNECT = 'reconnect',
  FALLBACK = 'fallback',
  ABORT = 'abort',
  IGNORE = 'ignore'
}

/**
 * Error Context
 */
export interface ErrorContext {
  serverName: string;
  operation: string;
  params?: unknown;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

/**
 * Error Event
 */
export interface ErrorEvent {
  error: Error | MCPError;
  severity: ErrorSeverity;
  context: ErrorContext;
  recovery?: RecoveryStrategy;
}

/**
 * Error Handler Events
 */
export interface ErrorHandlerEvents {
  error: (event: ErrorEvent) => void;
  recovery: (event: ErrorEvent, strategy: RecoveryStrategy) => void;
  criticalError: (event: ErrorEvent) => void;
}

/**
 * Retry Options
 */
export interface RetryOptions {
  maxAttempts: number;
  delayMs: number;
  backoffMultiplier: number;
  retryableErrors?: number[];
}

/**
 * MCPErrorHandler Config
 */
export interface MCPErrorHandlerConfig {
  maxRetries?: number;
  retryDelay?: number;
  backoffMultiplier?: number;
  verbose?: boolean;
  circuitBreaker?: {
    enabled: boolean;
    threshold: number;
    timeout: number;
  };
}

/**
 * Enhanced MCP Error
 */
export interface EnhancedMCPError extends Error {
  code: ErrorCode;
  retryable: boolean;
  cause?: Error;
  context?: Record<string, any>;
}

/**
 * Error Statistics
 */
export interface ErrorStats {
  totalErrors: number;
  errorsByType: Record<string, number>;
  errorsByServer: Record<string, number>;
}

/**
 * Internal Error Tracking
 */
interface InternalErrorStats {
  totalErrors: number;
  errorsByType: Record<string, number>;
  errorsByMessage: Record<string, number>;
  errorsByServer: Record<string, number>;
}

/**
 * Aggregated Error
 */
export interface AggregatedError {
  count: number;
  message: string;
  code: ErrorCode;
}

/**
 * MCP Error Handler
 */
export class MCPErrorHandler extends EventEmitter<ErrorHandlerEvents> {
  private errorHistory: ErrorEvent[] = [];
  private maxHistorySize = 100;
  private config: MCPErrorHandlerConfig;
  private errorStats: InternalErrorStats = {
    totalErrors: 0,
    errorsByType: {},
    errorsByMessage: {},
    errorsByServer: {}
  };
  private customHandlers = new Map<string, (error: Error) => Error>();
  private circuitState: 'closed' | 'open' | 'half-open' = 'closed';
  private circuitFailureCount = 0;
  private circuitLastFailureTime = 0;

  constructor(config: MCPErrorHandlerConfig = {}) {
    super();
    this.config = {
      maxRetries: config.maxRetries ?? 3,
      retryDelay: config.retryDelay ?? 100,
      backoffMultiplier: config.backoffMultiplier ?? 2,
      verbose: config.verbose ?? false,
      circuitBreaker: config.circuitBreaker
    };
  }

  /**
   * Classify error into error code
   */
  classify(error: Error | null | undefined): EnhancedMCPError {
    if (!error) {
      const unknownError = new Error('Unknown error') as EnhancedMCPError;
      unknownError.code = ErrorCode.UNKNOWN;
      unknownError.retryable = false;
      return unknownError;
    }

    const message = error.message?.toLowerCase() || '';
    let code = ErrorCode.UNKNOWN;
    let retryable = false;

    // Connection errors
    if (message.includes('connection') || message.includes('refused') ||
        message.includes('econnrefused') || message.includes('network')) {
      code = ErrorCode.CONNECTION_ERROR;
      retryable = true;
    }
    // Timeout errors
    else if (message.includes('timeout') || message.includes('timed out')) {
      code = ErrorCode.TIMEOUT;
      retryable = true;
    }
    // Parse errors
    else if (error instanceof SyntaxError || message.includes('parse') ||
             message.includes('unexpected token')) {
      code = ErrorCode.PARSE_ERROR;
      retryable = false;
    }
    // Authentication errors
    else if (message.includes('authentication') || message.includes('auth') ||
             message.includes('unauthorized')) {
      code = ErrorCode.AUTH_ERROR;
      retryable = false;
    }
    // Permission errors
    else if (message.includes('permission') || message.includes('denied') ||
             message.includes('forbidden')) {
      code = ErrorCode.PERMISSION_DENIED;
      retryable = false;
    }
    // Not found errors
    else if (message.includes('not found') || message.includes('enoent')) {
      code = ErrorCode.NOT_FOUND;
      retryable = false;
    }
    // Rate limit errors
    else if (message.includes('rate limit') || message.includes('too many')) {
      code = ErrorCode.RATE_LIMIT;
      retryable = true;
    }

    const mcpError = error as EnhancedMCPError;
    mcpError.code = code;
    mcpError.retryable = retryable;

    // Preserve error cause
    if ('cause' in error && error.cause instanceof Error) {
      mcpError.cause = error.cause;
    }

    return mcpError;
  }

  /**
   * Execute operation with retry logic
   */
  async executeWithRetry<T>(operation: () => Promise<T>): Promise<T> {
    // Check circuit breaker
    if (this.config.circuitBreaker?.enabled && this.circuitState === 'open') {
      const now = Date.now();
      const timeSinceLastFailure = now - this.circuitLastFailureTime;

      if (timeSinceLastFailure < this.config.circuitBreaker.timeout) {
        throw new Error('Circuit breaker is open');
      }

      // Try half-open
      this.circuitState = 'half-open';
    }

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.config.maxRetries!; attempt++) {
      try {
        const result = await operation();

        // Reset circuit breaker on success
        if (this.config.circuitBreaker?.enabled) {
          this.circuitFailureCount = 0;
          this.circuitState = 'closed';
        }

        return result;
      } catch (error) {
        lastError = error as Error;
        const classified = this.classify(lastError);

        // Don't retry non-retryable errors
        if (!classified.retryable) {
          throw lastError;
        }

        // Don't retry on last attempt
        if (attempt === this.config.maxRetries) {
          // Update circuit breaker
          if (this.config.circuitBreaker?.enabled) {
            this.circuitFailureCount++;
            this.circuitLastFailureTime = Date.now();

            if (this.circuitFailureCount >= this.config.circuitBreaker.threshold) {
              this.circuitState = 'open';
            }
          }
          break;
        }

        // Apply exponential backoff
        const delay = this.config.retryDelay! * Math.pow(this.config.backoffMultiplier!, attempt);
        await this.sleep(delay);
      }
    }

    throw lastError;
  }

  /**
   * Get recovery suggestions for an error
   */
  getSuggestions(mcpError: EnhancedMCPError): string[] {
    const suggestions: string[] = [];

    switch (mcpError.code) {
      case ErrorCode.CONNECTION_ERROR:
        suggestions.push('Check network connectivity');
        suggestions.push('Verify server is running');
        break;
      case ErrorCode.TIMEOUT:
        suggestions.push('Increase timeout value');
        suggestions.push('Check server responsiveness');
        break;
      case ErrorCode.AUTH_ERROR:
        suggestions.push('Verify credentials');
        suggestions.push('Check API key');
        break;
      case ErrorCode.RATE_LIMIT:
        suggestions.push('Reduce request frequency');
        suggestions.push('Implement rate limiting');
        break;
    }

    return suggestions;
  }

  /**
   * Format error with context
   */
  formatError(error: Error, context?: Record<string, any>): string {
    let formatted = error.message;

    // Sanitize sensitive information
    formatted = formatted.replace(/sk-ant-api\d+-[a-zA-Z0-9]+/g, '[REDACTED]');
    formatted = formatted.replace(/Bearer [a-zA-Z0-9_-]+/gi, 'Bearer [REDACTED]');
    formatted = formatted.replace(/api[_-]?key[:\s]+[a-zA-Z0-9_-]+/gi, 'api_key: [REDACTED]');

    // Truncate very long messages
    if (formatted.length > 500) {
      formatted = formatted.substring(0, 497) + '...';
    }

    // Add context fields directly
    if (context) {
      // Add specific context fields to the message
      if (context.server) {
        formatted += `\nServer: ${context.server}`;
      }
      if (context.operation) {
        formatted += `\nOperation: ${context.operation}`;
      }

      // Add full context as JSON
      try {
        const contextStr = JSON.stringify(context, (key, value) => {
          // Handle circular references
          if (value && typeof value === 'object') {
            if (value === context) return '[Circular]';
          }
          return value;
        });
        formatted += `\nContext: ${contextStr}`;
      } catch (e) {
        formatted += '\nContext: [Unable to stringify]';
      }
    }

    // Add stack trace in verbose mode
    if (this.config.verbose && error.stack) {
      formatted += `\nStack trace:\n${error.stack}`;
    }

    return formatted;
  }

  /**
   * Track error occurrence
   */
  track(error: Error, context?: { server?: string }): void {
    const classified = this.classify(error);

    // Update total errors
    this.errorStats.totalErrors++;

    // Update by type (for getStats)
    const typeName = classified.code;
    this.errorStats.errorsByType[typeName] = (this.errorStats.errorsByType[typeName] || 0) + 1;

    // Update by message (for aggregation)
    const key = `${typeName}:${error.message}`;
    this.errorStats.errorsByMessage[key] = (this.errorStats.errorsByMessage[key] || 0) + 1;

    // Update by server
    if (context?.server) {
      this.errorStats.errorsByServer[context.server] =
        (this.errorStats.errorsByServer[context.server] || 0) + 1;
    }
  }

  /**
   * Get error statistics
   */
  getStats(): ErrorStats {
    return {
      totalErrors: this.errorStats.totalErrors,
      errorsByType: { ...this.errorStats.errorsByType },
      errorsByServer: { ...this.errorStats.errorsByServer }
    };
  }

  /**
   * Reset error statistics
   */
  resetStats(): void {
    this.errorStats = {
      totalErrors: 0,
      errorsByType: {},
      errorsByMessage: {},
      errorsByServer: {}
    };
  }

  /**
   * Handle error with custom handlers
   */
  handle(error: Error): Error {
    const classified = this.classify(error);
    const handler = this.customHandlers.get(classified.code);

    if (handler) {
      return handler(error);
    }

    return classified;
  }

  /**
   * Add custom error handler
   */
  addCustomHandler(errorCode: string, handler: (error: Error) => Error): void {
    this.customHandlers.set(errorCode, handler);
  }

  /**
   * Get error chain
   */
  getErrorChain(error: Error): Error[] {
    const chain: Error[] = [];
    let current: Error | undefined = error;

    while (current) {
      chain.push(current);
      current = (current as any).cause;
    }

    return chain;
  }

  /**
   * Get aggregated errors
   */
  getAggregatedErrors(): AggregatedError[] {
    const aggregated = new Map<string, AggregatedError>();

    for (const [key, count] of Object.entries(this.errorStats.errorsByMessage)) {
      // Parse the key to extract code and message
      const colonIndex = key.indexOf(':');
      const code = colonIndex > 0 ? key.substring(0, colonIndex) : key;
      const message = colonIndex > 0 ? key.substring(colonIndex + 1) : key;

      aggregated.set(key, {
        count,
        message: message,
        code: code as ErrorCode
      });
    }

    // Sort by frequency
    return Array.from(aggregated.values()).sort((a, b) => b.count - a.count);
  }

  /**
   * Handle error with automatic recovery
   */
  async handleError(
    error: Error | MCPError,
    context: ErrorContext,
    retryCallback?: () => Promise<unknown>
  ): Promise<unknown> {
    const severity = this.determineSeverity(error);
    const recovery = this.determineRecovery(error, severity);

    const event: ErrorEvent = {
      error,
      severity,
      context,
      recovery
    };

    this.recordError(event);
    this.emit('error', event);

    if (severity === ErrorSeverity.CRITICAL) {
      this.emit('criticalError', event);
    }

    // Execute recovery strategy
    switch (recovery) {
      case RecoveryStrategy.RETRY:
        if (retryCallback) {
          return this.executeRetry(retryCallback, event);
        }
        break;

      case RecoveryStrategy.RECONNECT:
        // Signal reconnection needed
        this.emit('recovery', event, RecoveryStrategy.RECONNECT);
        break;

      case RecoveryStrategy.FALLBACK:
        // Use fallback mechanism
        this.emit('recovery', event, RecoveryStrategy.FALLBACK);
        break;

      case RecoveryStrategy.ABORT:
        throw this.createEnhancedError(error, context);

      case RecoveryStrategy.IGNORE:
        // Log and continue
        break;
    }

    throw this.createEnhancedError(error, context);
  }

  /**
   * Execute retry logic with exponential backoff
   */
  private async executeRetry(
    callback: () => Promise<unknown>,
    event: ErrorEvent,
    options: RetryOptions = {
      maxAttempts: 3,
      delayMs: 1000,
      backoffMultiplier: 2
    }
  ): Promise<unknown> {
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= options.maxAttempts; attempt++) {
      try {
        const delay = options.delayMs * Math.pow(options.backoffMultiplier, attempt - 1);

        if (attempt > 1) {
          await this.sleep(delay);
          this.emit('recovery', event, RecoveryStrategy.RETRY);
        }

        return await callback();
      } catch (error) {
        lastError = error as Error;

        if (attempt === options.maxAttempts) {
          break;
        }

        // Check if error is retryable
        if (!this.isRetryable(error as Error, options)) {
          break;
        }
      }
    }

    throw lastError || new Error('Retry failed');
  }

  /**
   * Determine error severity
   */
  private determineSeverity(error: Error | MCPError): ErrorSeverity {
    if (this.isMCPError(error)) {
      const mcpError = error as MCPError;

      switch (mcpError.code) {
        case MCPMessageBuilder.ErrorCodes.PARSE_ERROR:
        case MCPMessageBuilder.ErrorCodes.INTERNAL_ERROR:
          return ErrorSeverity.CRITICAL;

        case MCPMessageBuilder.ErrorCodes.CONNECTION_ERROR:
        case MCPMessageBuilder.ErrorCodes.SERVER_ERROR:
          return ErrorSeverity.HIGH;

        case MCPMessageBuilder.ErrorCodes.TIMEOUT_ERROR:
        case MCPMessageBuilder.ErrorCodes.METHOD_NOT_FOUND:
          return ErrorSeverity.MEDIUM;

        default:
          return ErrorSeverity.LOW;
      }
    }

    // Check error message for severity indicators
    const errorMessage = error.message.toLowerCase();

    if (errorMessage.includes('fatal') || errorMessage.includes('critical')) {
      return ErrorSeverity.CRITICAL;
    }

    if (errorMessage.includes('connection') || errorMessage.includes('network')) {
      return ErrorSeverity.HIGH;
    }

    if (errorMessage.includes('timeout') || errorMessage.includes('unavailable')) {
      return ErrorSeverity.MEDIUM;
    }

    return ErrorSeverity.LOW;
  }

  /**
   * Determine recovery strategy
   */
  private determineRecovery(
    error: Error | MCPError,
    severity: ErrorSeverity
  ): RecoveryStrategy {
    if (severity === ErrorSeverity.CRITICAL) {
      return RecoveryStrategy.ABORT;
    }

    if (this.isMCPError(error)) {
      const mcpError = error as MCPError;

      switch (mcpError.code) {
        case MCPMessageBuilder.ErrorCodes.CONNECTION_ERROR:
          return RecoveryStrategy.RECONNECT;

        case MCPMessageBuilder.ErrorCodes.TIMEOUT_ERROR:
        case MCPMessageBuilder.ErrorCodes.SERVER_ERROR:
          return RecoveryStrategy.RETRY;

        case MCPMessageBuilder.ErrorCodes.METHOD_NOT_FOUND:
        case MCPMessageBuilder.ErrorCodes.RESOURCE_NOT_FOUND:
          return RecoveryStrategy.FALLBACK;

        default:
          return RecoveryStrategy.RETRY;
      }
    }

    const errorMessage = error.message.toLowerCase();

    if (errorMessage.includes('timeout')) {
      return RecoveryStrategy.RETRY;
    }

    if (errorMessage.includes('connection') || errorMessage.includes('disconnected')) {
      return RecoveryStrategy.RECONNECT;
    }

    if (errorMessage.includes('not found') || errorMessage.includes('unavailable')) {
      return RecoveryStrategy.FALLBACK;
    }

    return RecoveryStrategy.RETRY;
  }

  /**
   * Check if error is retryable
   */
  private isRetryable(error: Error, options: RetryOptions): boolean {
    if (this.isMCPError(error)) {
      const mcpError = error as MCPError;

      if (options.retryableErrors) {
        return options.retryableErrors.includes(mcpError.code);
      }

      // Default retryable errors
      const retryableCodes: number[] = [
        MCPMessageBuilder.ErrorCodes.TIMEOUT_ERROR,
        MCPMessageBuilder.ErrorCodes.CONNECTION_ERROR,
        MCPMessageBuilder.ErrorCodes.SERVER_ERROR
      ];

      return retryableCodes.includes(mcpError.code);
    }

    // Check error message for retryable indicators
    const errorMessage = error.message.toLowerCase();
    return (
      errorMessage.includes('timeout') ||
      errorMessage.includes('temporary') ||
      errorMessage.includes('retry')
    );
  }

  /**
   * Check if error is MCP error
   */
  private isMCPError(error: Error | MCPError): error is MCPError {
    return 'code' in error && typeof (error as MCPError).code === 'number';
  }

  /**
   * Create enhanced error with context
   */
  private createEnhancedError(
    error: Error | MCPError,
    context: ErrorContext
  ): Error {
    const enhanced = new Error(
      `MCP Error in ${context.operation} on ${context.serverName}: ${error.message}`
    );

    (enhanced as any).originalError = error;
    (enhanced as any).context = context;

    return enhanced;
  }

  /**
   * Record error in history
   */
  private recordError(event: ErrorEvent): void {
    this.errorHistory.push(event);

    if (this.errorHistory.length > this.maxHistorySize) {
      this.errorHistory.shift();
    }
  }

  /**
   * Get error history
   */
  getErrorHistory(
    serverName?: string,
    severity?: ErrorSeverity
  ): ErrorEvent[] {
    let history = [...this.errorHistory];

    if (serverName) {
      history = history.filter((e) => e.context.serverName === serverName);
    }

    if (severity) {
      history = history.filter((e) => e.severity === severity);
    }

    return history;
  }

  /**
   * Clear error history
   */
  clearHistory(): void {
    this.errorHistory = [];
  }

  /**
   * Get error statistics
   */
  getStatistics(serverName?: string): {
    total: number;
    bySeverity: Record<ErrorSeverity, number>;
    byRecovery: Record<RecoveryStrategy, number>;
  } {
    const history = serverName
      ? this.errorHistory.filter((e) => e.context.serverName === serverName)
      : this.errorHistory;

    const stats = {
      total: history.length,
      bySeverity: {
        [ErrorSeverity.LOW]: 0,
        [ErrorSeverity.MEDIUM]: 0,
        [ErrorSeverity.HIGH]: 0,
        [ErrorSeverity.CRITICAL]: 0
      },
      byRecovery: {
        [RecoveryStrategy.RETRY]: 0,
        [RecoveryStrategy.RECONNECT]: 0,
        [RecoveryStrategy.FALLBACK]: 0,
        [RecoveryStrategy.ABORT]: 0,
        [RecoveryStrategy.IGNORE]: 0
      }
    };

    history.forEach((event) => {
      stats.bySeverity[event.severity]++;
      if (event.recovery) {
        stats.byRecovery[event.recovery]++;
      }
    });

    return stats;
  }

  /**
   * Sleep utility
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Create error from MCP error response
   */
  static fromMCPError(mcpError: MCPError): Error {
    const error = new Error(mcpError.message) as Error & { code: number; data?: unknown };
    error.code = mcpError.code;
    error.data = mcpError.data;
    return error;
  }
}
