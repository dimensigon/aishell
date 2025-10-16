/**
 * MCP Error Handler
 * Comprehensive error handling and recovery for MCP operations
 */

import { EventEmitter } from 'eventemitter3';
import { MCPError } from './types';
import { MCPMessageBuilder } from './messages';

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
 * MCP Error Handler
 */
export class MCPErrorHandler extends EventEmitter<ErrorHandlerEvents> {
  private errorHistory: ErrorEvent[] = [];
  private maxHistorySize = 100;

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
