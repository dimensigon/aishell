/**
 * MCP Error Handler Unit Tests
 * Tests error handling, retry logic, and error recovery
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MCPErrorHandler } from '../../src/mcp/error-handler';
import { MCPError, ErrorCode } from '../../src/mcp/types';

describe('MCPErrorHandler', () => {
  let errorHandler: MCPErrorHandler;

  beforeEach(() => {
    errorHandler = new MCPErrorHandler({
      maxRetries: 3,
      retryDelay: 100,
      backoffMultiplier: 2,
    });
  });

  describe('Error Classification', () => {
    it('should classify connection errors', () => {
      const error = new Error('Connection refused');
      const mcpError = errorHandler.classify(error);

      expect(mcpError.code).toBe(ErrorCode.CONNECTION_ERROR);
      expect(mcpError.retryable).toBe(true);
    });

    it('should classify timeout errors', () => {
      const error = new Error('Request timeout after 30000ms');
      const mcpError = errorHandler.classify(error);

      expect(mcpError.code).toBe(ErrorCode.TIMEOUT);
      expect(mcpError.retryable).toBe(true);
    });

    it('should classify parse errors', () => {
      const error = new SyntaxError('Unexpected token');
      const mcpError = errorHandler.classify(error);

      expect(mcpError.code).toBe(ErrorCode.PARSE_ERROR);
      expect(mcpError.retryable).toBe(false);
    });

    it('should classify authentication errors', () => {
      const error = new Error('Authentication failed');
      const mcpError = errorHandler.classify(error);

      expect(mcpError.code).toBe(ErrorCode.AUTH_ERROR);
      expect(mcpError.retryable).toBe(false);
    });

    it('should classify permission errors', () => {
      const error = new Error('Permission denied');
      const mcpError = errorHandler.classify(error);

      expect(mcpError.code).toBe(ErrorCode.PERMISSION_DENIED);
      expect(mcpError.retryable).toBe(false);
    });

    it('should classify resource not found errors', () => {
      const error = new Error('Resource not found');
      const mcpError = errorHandler.classify(error);

      expect(mcpError.code).toBe(ErrorCode.NOT_FOUND);
      expect(mcpError.retryable).toBe(false);
    });

    it('should classify rate limit errors', () => {
      const error = new Error('Rate limit exceeded');
      const mcpError = errorHandler.classify(error);

      expect(mcpError.code).toBe(ErrorCode.RATE_LIMIT);
      expect(mcpError.retryable).toBe(true);
    });

    it('should classify unknown errors', () => {
      const error = new Error('Something unexpected happened');
      const mcpError = errorHandler.classify(error);

      expect(mcpError.code).toBe(ErrorCode.UNKNOWN);
      expect(mcpError.retryable).toBe(false);
    });
  });

  describe('Retry Logic', () => {
    it('should retry retryable errors', async () => {
      let attempts = 0;
      const operation = vi.fn(async () => {
        attempts++;
        if (attempts < 3) {
          throw new Error('Connection refused');
        }
        return 'success';
      });

      const result = await errorHandler.executeWithRetry(operation);

      expect(result).toBe('success');
      expect(attempts).toBe(3);
      expect(operation).toHaveBeenCalledTimes(3);
    });

    it('should not retry non-retryable errors', async () => {
      const operation = vi.fn(async () => {
        throw new Error('Authentication failed');
      });

      await expect(errorHandler.executeWithRetry(operation)).rejects.toThrow(
        'Authentication failed'
      );

      expect(operation).toHaveBeenCalledTimes(1);
    });

    it('should respect max retries limit', async () => {
      const operation = vi.fn(async () => {
        throw new Error('Connection refused');
      });

      await expect(errorHandler.executeWithRetry(operation)).rejects.toThrow();

      expect(operation).toHaveBeenCalledTimes(4); // Initial + 3 retries
    });

    it('should apply exponential backoff', async () => {
      const timestamps: number[] = [];
      const operation = vi.fn(async () => {
        timestamps.push(Date.now());
        throw new Error('Connection refused');
      });

      await expect(errorHandler.executeWithRetry(operation)).rejects.toThrow();

      // Check that delays increase exponentially
      for (let i = 1; i < timestamps.length; i++) {
        const delay = timestamps[i] - timestamps[i - 1];
        expect(delay).toBeGreaterThanOrEqual(100 * Math.pow(2, i - 1) - 20); // Allow 20ms tolerance
      }
    });

    it('should reset retry count on success', async () => {
      let attempts = 0;
      const operation = vi.fn(async () => {
        attempts++;
        if (attempts === 2) {
          return 'success';
        }
        throw new Error('Connection refused');
      });

      await errorHandler.executeWithRetry(operation);
      attempts = 0;

      // Second call should start fresh
      await errorHandler.executeWithRetry(operation);
      expect(attempts).toBe(2);
    });
  });

  describe('Error Recovery', () => {
    it('should suggest recovery actions for connection errors', () => {
      const error = new Error('Connection refused');
      const mcpError = errorHandler.classify(error);
      const suggestions = errorHandler.getSuggestions(mcpError);

      expect(suggestions).toContain('Check network connectivity');
      expect(suggestions).toContain('Verify server is running');
    });

    it('should suggest recovery actions for timeout errors', () => {
      const error = new Error('Request timeout');
      const mcpError = errorHandler.classify(error);
      const suggestions = errorHandler.getSuggestions(mcpError);

      expect(suggestions).toContain('Increase timeout value');
      expect(suggestions).toContain('Check server responsiveness');
    });

    it('should suggest recovery actions for auth errors', () => {
      const error = new Error('Authentication failed');
      const mcpError = errorHandler.classify(error);
      const suggestions = errorHandler.getSuggestions(mcpError);

      expect(suggestions).toContain('Verify credentials');
      expect(suggestions).toContain('Check API key');
    });

    it('should suggest recovery actions for rate limit errors', () => {
      const error = new Error('Rate limit exceeded');
      const mcpError = errorHandler.classify(error);
      const suggestions = errorHandler.getSuggestions(mcpError);

      expect(suggestions).toContain('Reduce request frequency');
      expect(suggestions).toContain('Implement rate limiting');
    });
  });

  describe('Error Formatting', () => {
    it('should format error messages with context', () => {
      const error = new Error('Connection refused');
      const formatted = errorHandler.formatError(error, {
        server: 'test-server',
        operation: 'connect',
      });

      expect(formatted).toContain('Connection refused');
      expect(formatted).toContain('test-server');
      expect(formatted).toContain('connect');
    });

    it('should include stack trace in verbose mode', () => {
      const verboseHandler = new MCPErrorHandler({
        verbose: true,
      });

      const error = new Error('Test error');
      const formatted = verboseHandler.formatError(error);

      expect(formatted).toContain('Stack trace:');
    });

    it('should sanitize sensitive information', () => {
      const error = new Error(
        'Authentication failed with token: sk-ant-api03-1234567890'
      );
      const formatted = errorHandler.formatError(error);

      expect(formatted).not.toContain('sk-ant-api03-1234567890');
      expect(formatted).toContain('[REDACTED]');
    });
  });

  describe('Error Tracking', () => {
    it('should track error frequency', () => {
      const error = new Error('Connection refused');

      errorHandler.track(error);
      errorHandler.track(error);
      errorHandler.track(error);

      const stats = errorHandler.getStats();
      expect(stats.totalErrors).toBe(3);
      expect(stats.errorsByType['CONNECTION_ERROR']).toBe(3);
    });

    it('should track errors by server', () => {
      const error1 = new Error('Connection refused');
      const error2 = new Error('Connection refused');

      errorHandler.track(error1, { server: 'server-1' });
      errorHandler.track(error2, { server: 'server-2' });

      const stats = errorHandler.getStats();
      expect(stats.errorsByServer['server-1']).toBe(1);
      expect(stats.errorsByServer['server-2']).toBe(1);
    });

    it('should calculate error rates', () => {
      const error = new Error('Test error');

      for (let i = 0; i < 10; i++) {
        errorHandler.track(error);
      }

      const stats = errorHandler.getStats();
      expect(stats.totalErrors).toBe(10);
    });

    it('should reset stats', () => {
      const error = new Error('Test error');

      errorHandler.track(error);
      errorHandler.track(error);

      errorHandler.resetStats();

      const stats = errorHandler.getStats();
      expect(stats.totalErrors).toBe(0);
    });
  });

  describe('Custom Error Handlers', () => {
    it('should allow custom error handlers', async () => {
      const customHandler = vi.fn((error: Error) => {
        return new Error('Custom handled: ' + error.message);
      });

      errorHandler.addCustomHandler('CONNECTION_ERROR', customHandler);

      const error = new Error('Connection refused');
      const handled = errorHandler.handle(error);

      expect(customHandler).toHaveBeenCalledWith(error);
      expect(handled.message).toContain('Custom handled');
    });

    it('should support multiple custom handlers', async () => {
      const handler1 = vi.fn((error: Error) => error);
      const handler2 = vi.fn((error: Error) => error);

      errorHandler.addCustomHandler('CONNECTION_ERROR', handler1);
      errorHandler.addCustomHandler('TIMEOUT', handler2);

      const connError = new Error('Connection refused');
      const timeoutError = new Error('Request timeout');

      errorHandler.handle(connError);
      errorHandler.handle(timeoutError);

      expect(handler1).toHaveBeenCalled();
      expect(handler2).toHaveBeenCalled();
    });
  });

  describe('Error Chaining', () => {
    it('should preserve error cause chain', () => {
      const rootCause = new Error('Root cause');
      const wrappedError = new Error('Wrapped error', { cause: rootCause });

      const mcpError = errorHandler.classify(wrappedError);

      expect(mcpError.cause).toBe(rootCause);
    });

    it('should extract all errors from chain', () => {
      const error1 = new Error('Level 1');
      const error2 = new Error('Level 2', { cause: error1 });
      const error3 = new Error('Level 3', { cause: error2 });

      const chain = errorHandler.getErrorChain(error3);

      expect(chain).toHaveLength(3);
      expect(chain[0].message).toBe('Level 3');
      expect(chain[1].message).toBe('Level 2');
      expect(chain[2].message).toBe('Level 1');
    });
  });

  describe('Circuit Breaker', () => {
    it('should open circuit after threshold failures', async () => {
      const failingOperation = vi.fn(async () => {
        throw new Error('Connection refused');
      });

      const cbHandler = new MCPErrorHandler({
        circuitBreaker: {
          enabled: true,
          threshold: 3,
          timeout: 1000,
        },
      });

      // Trigger 3 failures
      for (let i = 0; i < 3; i++) {
        await expect(cbHandler.executeWithRetry(failingOperation)).rejects.toThrow();
      }

      // Circuit should be open, operation not attempted
      await expect(cbHandler.executeWithRetry(failingOperation)).rejects.toThrow(
        'Circuit breaker is open'
      );

      expect(failingOperation).toHaveBeenCalledTimes(12); // 3 attempts × 4 (initial + 3 retries)
    });

    it('should reset circuit after timeout', async () => {
      const operation = vi.fn(async () => 'success');

      const cbHandler = new MCPErrorHandler({
        circuitBreaker: {
          enabled: true,
          threshold: 2,
          timeout: 100,
        },
      });

      // Open circuit
      for (let i = 0; i < 2; i++) {
        await expect(
          cbHandler.executeWithRetry(async () => {
            throw new Error('Connection refused');
          })
        ).rejects.toThrow();
      }

      // Wait for circuit to reset
      await new Promise((resolve) => setTimeout(resolve, 150));

      // Should work now
      const result = await cbHandler.executeWithRetry(operation);
      expect(result).toBe('success');
    });
  });

  describe('Error Aggregation', () => {
    it('should aggregate similar errors', () => {
      for (let i = 0; i < 5; i++) {
        errorHandler.track(new Error('Connection refused'));
      }

      const aggregated = errorHandler.getAggregatedErrors();

      expect(aggregated).toHaveLength(1);
      expect(aggregated[0].count).toBe(5);
      expect(aggregated[0].message).toContain('Connection refused');
    });

    it('should separate different error types', () => {
      errorHandler.track(new Error('Connection refused'));
      errorHandler.track(new Error('Request timeout'));
      errorHandler.track(new Error('Authentication failed'));

      const aggregated = errorHandler.getAggregatedErrors();

      expect(aggregated).toHaveLength(3);
    });

    it('should sort by frequency', () => {
      for (let i = 0; i < 5; i++) {
        errorHandler.track(new Error('Connection refused'));
      }
      for (let i = 0; i < 3; i++) {
        errorHandler.track(new Error('Request timeout'));
      }

      const aggregated = errorHandler.getAggregatedErrors();

      expect(aggregated[0].count).toBeGreaterThan(aggregated[1].count);
    });
  });

  describe('Edge Cases', () => {
    it('should handle null/undefined errors', () => {
      expect(() => errorHandler.classify(null as any)).not.toThrow();
      expect(() => errorHandler.classify(undefined as any)).not.toThrow();
    });

    it('should handle errors without message', () => {
      const error = new Error();
      const mcpError = errorHandler.classify(error);

      expect(mcpError.message).toBeDefined();
    });

    it('should handle very long error messages', () => {
      const longMessage = 'x'.repeat(10000);
      const error = new Error(longMessage);

      const formatted = errorHandler.formatError(error);

      expect(formatted.length).toBeLessThan(1000); // Should truncate
    });

    it('should handle circular references in error context', () => {
      const circular: any = { a: 1 };
      circular.self = circular;

      const error = new Error('Test error');
      expect(() => errorHandler.formatError(error, circular)).not.toThrow();
    });
  });
});

// Export types for the error handler
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

export interface MCPError extends Error {
  code: ErrorCode;
  retryable: boolean;
  cause?: Error;
  context?: Record<string, any>;
}
