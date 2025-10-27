/**
 * Comprehensive Error Handler
 * Centralized error handling with recovery strategies, logging, and metrics
 */

import { EventEmitter } from 'eventemitter3';

/**
 * Error severity levels
 */
export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

/**
 * Error category
 */
export enum ErrorCategory {
  NETWORK = 'network',
  VALIDATION = 'validation',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  TIMEOUT = 'timeout',
  RESOURCE = 'resource',
  SYSTEM = 'system',
  UNKNOWN = 'unknown'
}

/**
 * Error context
 */
export interface ErrorContext {
  operation: string;
  component: string;
  userId?: string;
  sessionId?: string;
  metadata?: Record<string, any>;
  stackTrace?: string;
  timestamp: number;
}

/**
 * Error entry
 */
export interface ErrorEntry {
  id: string;
  error: Error;
  category: ErrorCategory;
  severity: ErrorSeverity;
  context: ErrorContext;
  recovered: boolean;
  recoveryStrategy?: string;
  timestamp: number;
}

/**
 * Recovery strategy
 */
export interface RecoveryStrategy {
  name: string;
  canRecover: (error: Error, context: ErrorContext) => boolean;
  recover: (error: Error, context: ErrorContext) => Promise<any>;
  priority?: number;
}

/**
 * Error handler events
 */
export interface ErrorHandlerEvents {
  error: (entry: ErrorEntry) => void;
  recovery: (entryId: string, strategy: string, success: boolean) => void;
  criticalError: (entry: ErrorEntry) => void;
}

/**
 * Error Handler Configuration
 */
export interface ErrorHandlerConfig {
  enableLogging?: boolean;
  enableMetrics?: boolean;
  maxErrorHistory?: number;
  retryAttempts?: number;
  retryDelay?: number;
}

/**
 * Comprehensive Error Handler
 */
export class ErrorHandler extends EventEmitter<ErrorHandlerEvents> {
  private errorHistory: ErrorEntry[] = [];
  private recoveryStrategies: RecoveryStrategy[] = [];
  private errorCounts = new Map<string, number>();
  private config: Required<ErrorHandlerConfig>;

  constructor(config: ErrorHandlerConfig = {}) {
    super();
    this.config = {
      enableLogging: config.enableLogging !== false,
      enableMetrics: config.enableMetrics !== false,
      maxErrorHistory: config.maxErrorHistory || 1000,
      retryAttempts: config.retryAttempts || 3,
      retryDelay: config.retryDelay || 1000
    };

    this.registerDefaultStrategies();
  }

  /**
   * Handle error with recovery
   */
  async handle<T = any>(
    error: Error,
    context: ErrorContext,
    defaultValue?: T
  ): Promise<T | undefined> {
    const category = this.categorizeError(error);
    const severity = this.assessSeverity(error, category);

    const entry: ErrorEntry = {
      id: this.generateErrorId(),
      error,
      category,
      severity,
      context: {
        ...context,
        stackTrace: error.stack,
        timestamp: Date.now()
      },
      recovered: false,
      timestamp: Date.now()
    };

    // Log error
    if (this.config.enableLogging) {
      this.logError(entry);
    }

    // Update metrics
    if (this.config.enableMetrics) {
      this.updateMetrics(entry);
    }

    // Store in history
    this.addToHistory(entry);

    // Emit event
    this.emit('error', entry);

    // Emit critical error event
    if (severity === ErrorSeverity.CRITICAL) {
      this.emit('criticalError', entry);
    }

    // Attempt recovery
    try {
      const recovered = await this.attemptRecovery(entry);
      if (recovered !== undefined) {
        entry.recovered = true;
        return recovered as T;
      }
    } catch (recoveryError) {
      console.error('Recovery failed:', recoveryError);
    }

    // Return default value if provided
    if (defaultValue !== undefined) {
      return defaultValue;
    }

    // Re-throw if critical and no recovery
    if (severity === ErrorSeverity.CRITICAL) {
      throw error;
    }

    return undefined;
  }

  /**
   * Wrap async function with error handling
   */
  wrap<TArgs extends any[], TReturn>(
    fn: (...args: TArgs) => Promise<TReturn>,
    context: Partial<ErrorContext>
  ): (...args: TArgs) => Promise<TReturn | undefined> {
    return async (...args: TArgs) => {
      try {
        return await fn(...args);
      } catch (error) {
        return this.handle(
          error instanceof Error ? error : new Error(String(error)),
          {
            operation: context.operation || 'unknown',
            component: context.component || 'unknown',
            ...context,
            timestamp: Date.now()
          }
        );
      }
    };
  }

  /**
   * Register recovery strategy
   */
  registerStrategy(strategy: RecoveryStrategy): void {
    this.recoveryStrategies.push(strategy);
    // Sort by priority
    this.recoveryStrategies.sort((a, b) => (b.priority || 0) - (a.priority || 0));
  }

  /**
   * Attempt recovery using registered strategies
   */
  private async attemptRecovery(entry: ErrorEntry): Promise<any> {
    for (const strategy of this.recoveryStrategies) {
      if (strategy.canRecover(entry.error, entry.context)) {
        try {
          const result = await strategy.recover(entry.error, entry.context);
          entry.recoveryStrategy = strategy.name;
          this.emit('recovery', entry.id, strategy.name, true);
          return result;
        } catch (error) {
          console.error(`Recovery strategy '${strategy.name}' failed:`, error);
          this.emit('recovery', entry.id, strategy.name, false);
        }
      }
    }

    return undefined;
  }

  /**
   * Categorize error
   */
  private categorizeError(error: Error): ErrorCategory {
    const message = error.message.toLowerCase();

    if (message.includes('timeout') || message.includes('timed out')) {
      return ErrorCategory.TIMEOUT;
    }

    if (
      message.includes('network') ||
      message.includes('connection') ||
      message.includes('econnrefused')
    ) {
      return ErrorCategory.NETWORK;
    }

    if (message.includes('validation') || message.includes('invalid')) {
      return ErrorCategory.VALIDATION;
    }

    if (message.includes('authentication') || message.includes('unauthorized')) {
      return ErrorCategory.AUTHENTICATION;
    }

    if (message.includes('authorization') || message.includes('forbidden')) {
      return ErrorCategory.AUTHORIZATION;
    }

    if (
      message.includes('resource') ||
      message.includes('not found') ||
      message.includes('enoent')
    ) {
      return ErrorCategory.RESOURCE;
    }

    if (
      message.includes('system') ||
      message.includes('internal') ||
      error.name === 'SystemError'
    ) {
      return ErrorCategory.SYSTEM;
    }

    return ErrorCategory.UNKNOWN;
  }

  /**
   * Assess error severity
   */
  private assessSeverity(error: Error, category: ErrorCategory): ErrorSeverity {
    // Critical errors
    if (
      category === ErrorCategory.SYSTEM ||
      error.name === 'FatalError' ||
      error.message.includes('critical')
    ) {
      return ErrorSeverity.CRITICAL;
    }

    // High severity
    if (
      category === ErrorCategory.AUTHENTICATION ||
      category === ErrorCategory.AUTHORIZATION
    ) {
      return ErrorSeverity.HIGH;
    }

    // Medium severity
    if (
      category === ErrorCategory.NETWORK ||
      category === ErrorCategory.TIMEOUT ||
      category === ErrorCategory.RESOURCE
    ) {
      return ErrorSeverity.MEDIUM;
    }

    // Low severity
    return ErrorSeverity.LOW;
  }

  /**
   * Log error
   */
  private logError(entry: ErrorEntry): void {
    const logLevel = this.getLogLevel(entry.severity);
    const message = `[${logLevel}] ${entry.category} error in ${entry.context.component}.${entry.context.operation}: ${entry.error.message}`;

    console[logLevel](message, {
      id: entry.id,
      error: entry.error,
      context: entry.context,
      timestamp: new Date(entry.timestamp).toISOString()
    });
  }

  /**
   * Get log level from severity
   */
  private getLogLevel(severity: ErrorSeverity): 'error' | 'warn' | 'info' {
    switch (severity) {
      case ErrorSeverity.CRITICAL:
      case ErrorSeverity.HIGH:
        return 'error';
      case ErrorSeverity.MEDIUM:
        return 'warn';
      default:
        return 'info';
    }
  }

  /**
   * Update metrics
   */
  private updateMetrics(entry: ErrorEntry): void {
    const key = `${entry.category}:${entry.severity}`;
    const count = this.errorCounts.get(key) || 0;
    this.errorCounts.set(key, count + 1);
  }

  /**
   * Add to error history
   */
  private addToHistory(entry: ErrorEntry): void {
    this.errorHistory.push(entry);

    // Limit history size
    if (this.errorHistory.length > this.config.maxErrorHistory) {
      this.errorHistory.shift();
    }
  }

  /**
   * Register default recovery strategies
   */
  private registerDefaultStrategies(): void {
    // Retry strategy for network errors
    this.registerStrategy({
      name: 'network-retry',
      priority: 10,
      canRecover: (error, _context) => {
        return error.message.toLowerCase().includes('network') ||
               error.message.toLowerCase().includes('econnrefused') ||
               error.message.toLowerCase().includes('enotfound');
      },
      recover: async (error, _context) => {
        // Implement retry logic with backoff
        await this.delay(this.config.retryDelay);
        throw error; // Re-throw to trigger upper-level retry
      }
    });

    // Timeout retry strategy
    this.registerStrategy({
      name: 'timeout-retry',
      priority: 9,
      canRecover: (error) => {
        return error.message.toLowerCase().includes('timeout') ||
               error.message.toLowerCase().includes('timed out');
      },
      recover: async (error) => {
        await this.delay(this.config.retryDelay);
        throw error;
      }
    });

    // Resource not found fallback
    this.registerStrategy({
      name: 'resource-fallback',
      priority: 8,
      canRecover: (error) => {
        return error.message.toLowerCase().includes('not found') ||
               error.message.toLowerCase().includes('enoent');
      },
      recover: async () => {
        return null; // Return null for missing resources
      }
    });

    // Validation fallback strategy
    this.registerStrategy({
      name: 'validation-fallback',
      priority: 7,
      canRecover: (error) => {
        return error.message.toLowerCase().includes('validation');
      },
      recover: async () => {
        return null; // Return null as fallback
      }
    });

    // Rate limit backoff strategy
    this.registerStrategy({
      name: 'rate-limit-backoff',
      priority: 6,
      canRecover: (error) => {
        return error.message.toLowerCase().includes('rate limit') ||
               error.message.toLowerCase().includes('too many requests');
      },
      recover: async (error) => {
        // Exponential backoff for rate limits
        await this.delay(this.config.retryDelay * 3);
        throw error;
      }
    });
  }

  /**
   * Get error history
   */
  getHistory(filters?: {
    category?: ErrorCategory;
    severity?: ErrorSeverity;
    component?: string;
    limit?: number;
  }): ErrorEntry[] {
    let history = [...this.errorHistory];

    if (filters) {
      if (filters.category) {
        history = history.filter((e) => e.category === filters.category);
      }
      if (filters.severity) {
        history = history.filter((e) => e.severity === filters.severity);
      }
      if (filters.component) {
        history = history.filter((e) => e.context.component === filters.component);
      }
      if (filters.limit) {
        history = history.slice(-filters.limit);
      }
    }

    return history;
  }

  /**
   * Get error statistics
   */
  getStatistics(): {
    total: number;
    byCategory: Record<string, number>;
    bySeverity: Record<string, number>;
    recovered: number;
    unrecovered: number;
    criticalErrors: number;
  } {
    const byCategory: Record<string, number> = {};
    const bySeverity: Record<string, number> = {};
    let recovered = 0;
    let criticalErrors = 0;

    for (const entry of this.errorHistory) {
      byCategory[entry.category] = (byCategory[entry.category] || 0) + 1;
      bySeverity[entry.severity] = (bySeverity[entry.severity] || 0) + 1;

      if (entry.recovered) recovered++;
      if (entry.severity === ErrorSeverity.CRITICAL) criticalErrors++;
    }

    return {
      total: this.errorHistory.length,
      byCategory,
      bySeverity,
      recovered,
      unrecovered: this.errorHistory.length - recovered,
      criticalErrors
    };
  }

  /**
   * Clear error history
   */
  clearHistory(): void {
    this.errorHistory = [];
    this.errorCounts.clear();
  }

  /**
   * Export error report
   */
  exportReport(): string {
    const stats = this.getStatistics();
    const recentErrors = this.getHistory({ limit: 10 });

    const report = {
      timestamp: new Date().toISOString(),
      statistics: stats,
      recentErrors: recentErrors.map((e) => ({
        id: e.id,
        category: e.category,
        severity: e.severity,
        message: e.error.message,
        component: e.context.component,
        operation: e.context.operation,
        recovered: e.recovered,
        timestamp: new Date(e.timestamp).toISOString()
      }))
    };

    return JSON.stringify(report, null, 2);
  }

  /**
   * Generate error ID
   */
  private generateErrorId(): string {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Check if error is recoverable
   */
  isRecoverable(error: Error): boolean {
    return this.recoveryStrategies.some((strategy) =>
      strategy.canRecover(error, {
        operation: 'unknown',
        component: 'unknown',
        timestamp: Date.now()
      })
    );
  }
}

/**
 * Global error handler instance
 */
export const globalErrorHandler = new ErrorHandler();
