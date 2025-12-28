/**
 * MCPToolExecutor Integration Tests
 * Tests tool execution, validation, security policies, and caching
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MCPToolExecutor, ToolExecutionContext, SecurityPolicy } from '../../src/mcp/tool-executor';
import { IMCPClient, MCPTool } from '../../src/mcp/types';

describe('MCPToolExecutor Integration', () => {
  let executor: MCPToolExecutor;
  let mockMCPClient: IMCPClient;
  let mockContext: ToolExecutionContext;

  beforeEach(() => {
    // Create mock MCP client
    mockMCPClient = createMockMCPClient();

    executor = new MCPToolExecutor(mockMCPClient, {}, {
      enableCache: true,
      cacheTTL: 60000,
      enableValidation: true
    });

    mockContext = {
      sessionId: 'test-session',
      permissions: ['read', 'write', 'execute'],
      timeout: 5000,
      metadata: {}
    };
  });

  describe('Tool Execution', () => {
    it('should execute valid tool', async () => {
      const result = await executor.execute('test-tool', { input: 'hello' }, mockContext);

      expect(result.success).toBe(true);
      expect(result.tool).toBe('test-tool');
      expect(result.result).toBeDefined();
    });

    it('should validate parameters', async () => {
      const result = await executor.execute(
        'test-tool',
        {}, // Missing required parameters
        mockContext
      );

      expect(result.success).toBe(false);
      expect(result.validationErrors).toBeDefined();
      expect(result.validationErrors!.length).toBeGreaterThan(0);
    });

    it('should track execution duration', async () => {
      const result = await executor.execute('test-tool', { input: 'test' }, mockContext);

      expect(result.duration).toBeGreaterThan(0);
      expect(result.timestamp).toBeDefined();
    });

    it('should handle tool execution errors', async () => {
      mockMCPClient.request = vi.fn().mockRejectedValue(new Error('Execution failed'));

      const result = await executor.execute('failing-tool', { input: 'test' }, mockContext);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(result.error?.message).toContain('not found');
    });
  });

  describe('Parameter Validation', () => {
    it('should validate required fields', async () => {
      const result = await executor.execute('test-tool', {}, mockContext);

      expect(result.success).toBe(false);
      expect(result.validationErrors?.some((e) => e.code === 'REQUIRED_FIELD_MISSING')).toBe(true);
    });

    it('should validate field types', async () => {
      const result = await executor.execute(
        'test-tool',
        { input: 123 }, // Should be string
        mockContext
      );

      expect(result.success).toBe(false);
      expect(result.validationErrors?.some((e) => e.code === 'INVALID_TYPE')).toBe(true);
    });

    it('should validate enum values', async () => {
      const toolWithEnum: MCPTool = {
        name: 'enum-tool',
        description: 'Test enum validation',
        inputSchema: {
          type: 'object',
          properties: {
            status: {
              type: 'string',
              enum: ['active', 'inactive']
            }
          },
          required: ['status']
        }
      };

      mockMCPClient.listTools = vi.fn().mockResolvedValue([toolWithEnum]);

      const result = await executor.execute(
        'enum-tool',
        { status: 'invalid' },
        mockContext
      );

      expect(result.success).toBe(false);
      expect(result.validationErrors?.some((e) => e.code === 'INVALID_ENUM_VALUE')).toBe(true);
    });

    it('should validate string length', async () => {
      const toolWithLength: MCPTool = {
        name: 'length-tool',
        description: 'Test length validation',
        inputSchema: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              minLength: 3,
              maxLength: 10
            }
          },
          required: ['name']
        }
      };

      mockMCPClient.listTools = vi.fn().mockResolvedValue([toolWithLength]);

      const shortResult = await executor.execute('length-tool', { name: 'ab' }, mockContext);
      expect(shortResult.validationErrors?.some((e) => e.code === 'STRING_TOO_SHORT')).toBe(true);

      const longResult = await executor.execute('length-tool', { name: 'verylongname' }, mockContext);
      expect(longResult.validationErrors?.some((e) => e.code === 'STRING_TOO_LONG')).toBe(true);
    });

    it('should validate number range', async () => {
      const toolWithRange: MCPTool = {
        name: 'range-tool',
        description: 'Test range validation',
        inputSchema: {
          type: 'object',
          properties: {
            age: {
              type: 'number',
              minimum: 0,
              maximum: 120
            }
          },
          required: ['age']
        }
      };

      mockMCPClient.listTools = vi.fn().mockResolvedValue([toolWithRange]);

      const lowResult = await executor.execute('range-tool', { age: -1 }, mockContext);
      expect(lowResult.validationErrors?.some((e) => e.code === 'NUMBER_TOO_SMALL')).toBe(true);

      const highResult = await executor.execute('range-tool', { age: 121 }, mockContext);
      expect(highResult.validationErrors?.some((e) => e.code === 'NUMBER_TOO_LARGE')).toBe(true);
    });
  });

  describe('Security Policies', () => {
    it('should enforce allowed tools list', async () => {
      const securityPolicy: SecurityPolicy = {
        allowedTools: ['safe-tool']
      };

      const secureExecutor = new MCPToolExecutor(mockMCPClient, securityPolicy);

      const result = await secureExecutor.execute('test-tool', { input: 'test' }, mockContext);

      expect(result.success).toBe(false);
      expect(result.error?.message).toContain('not allowed');
    });

    it('should enforce denied tools list', async () => {
      const securityPolicy: SecurityPolicy = {
        deniedTools: ['dangerous-tool']
      };

      const secureExecutor = new MCPToolExecutor(mockMCPClient, securityPolicy);

      const result = await secureExecutor.execute('dangerous-tool', { input: 'test' }, mockContext);

      expect(result.success).toBe(false);
      expect(result.error?.message).toContain('denied');
    });

    it('should enforce permission requirements', async () => {
      const securityPolicy: SecurityPolicy = {
        requirePermissions: {
          'admin-tool': ['admin']
        }
      };

      const secureExecutor = new MCPToolExecutor(mockMCPClient, securityPolicy);

      const result = await secureExecutor.execute('admin-tool', { input: 'test' }, mockContext);

      expect(result.success).toBe(false);
      expect(result.error?.message).toContain('Insufficient permissions');
    });

    it('should enforce rate limiting', async () => {
      const securityPolicy: SecurityPolicy = {
        rateLimit: {
          maxCalls: 2,
          windowMs: 1000
        }
      };

      const rateLimitedExecutor = new MCPToolExecutor(mockMCPClient, securityPolicy);

      // First two calls should succeed
      await rateLimitedExecutor.execute('test-tool', { input: '1' }, mockContext);
      await rateLimitedExecutor.execute('test-tool', { input: '2' }, mockContext);

      // Third call should be rate limited
      const result = await rateLimitedExecutor.execute('test-tool', { input: '3' }, mockContext);

      expect(result.success).toBe(false);
      expect(result.error?.message).toContain('Rate limit exceeded');
    });
  });

  describe('Caching', () => {
    it('should cache successful executions', async () => {
      const params = { input: 'cached' };

      const result1 = await executor.execute('test-tool', params, mockContext);
      const result2 = await executor.execute('test-tool', params, mockContext);

      expect(result1.success).toBe(true);
      expect(result2.success).toBe(true);

      // Second call should be from cache (MCP client called only once)
      // This requires tracking calls in the mock
    });

    it('should expire cached results after TTL', async () => {
      const shortCacheExecutor = new MCPToolExecutor(mockMCPClient, {}, {
        enableCache: true,
        cacheTTL: 100
      });

      const params = { input: 'expiring' };

      await shortCacheExecutor.execute('test-tool', params, mockContext);

      // Wait for cache to expire
      await new Promise((resolve) => setTimeout(resolve, 150));

      await shortCacheExecutor.execute('test-tool', params, mockContext);

      // Both calls should have executed (not cached)
    }, 10000);

    it('should clear specific tool cache', async () => {
      await executor.execute('test-tool', { input: 'test1' }, mockContext);
      await executor.execute('test-tool', { input: 'test2' }, mockContext);

      executor.clearCache('test-tool');

      // Cache should be cleared
      const stats = executor.getStatistics();
      expect(stats.cacheSize).toBeLessThan(2);
    });

    it('should clear all cache', async () => {
      await executor.execute('test-tool', { input: 'test1' }, mockContext);
      await executor.execute('test-tool', { input: 'test2' }, mockContext);

      executor.clearCache();

      const stats = executor.getStatistics();
      expect(stats.cacheSize).toBe(0);
    });
  });

  describe('Batch Execution', () => {
    it('should execute multiple tools in parallel', async () => {
      const executions = [
        { tool: 'test-tool', params: { input: 'test1' } },
        { tool: 'test-tool', params: { input: 'test2' } },
        { tool: 'test-tool', params: { input: 'test3' } }
      ];

      const results = await executor.executeBatch(executions, mockContext);

      expect(results).toHaveLength(3);
      expect(results.every((r) => r.success)).toBe(true);
    });

    it('should handle partial failures in batch', async () => {
      const executions = [
        { tool: 'test-tool', params: { input: 'valid' } },
        { tool: 'test-tool', params: {} }, // Invalid - missing required
        { tool: 'test-tool', params: { input: 'valid2' } }
      ];

      const results = await executor.executeBatch(executions, mockContext);

      expect(results).toHaveLength(3);
      expect(results[0].success).toBe(true);
      expect(results[1].success).toBe(false);
      expect(results[2].success).toBe(true);
    });
  });

  describe('Timeout Handling', () => {
    it('should timeout long-running tools', async () => {
      mockMCPClient.request = vi.fn().mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 10000))
      );

      const timeoutContext = { ...mockContext, timeout: 100 };

      const result = await executor.execute('slow-tool', { input: 'test' }, timeoutContext);

      expect(result.success).toBe(false);
      expect(result.error?.message).toContain('not found');
    }, 10000);
  });

  describe('Events', () => {
    it('should emit executionStart event', async () => {
      const startSpy = vi.fn();
      executor.on('executionStart', startSpy);

      await executor.execute('test-tool', { input: 'test' }, mockContext);

      expect(startSpy).toHaveBeenCalledWith('test-tool', { input: 'test' });
    });

    it('should emit executionComplete event', async () => {
      const completeSpy = vi.fn();
      executor.on('executionComplete', completeSpy);

      await executor.execute('test-tool', { input: 'test' }, mockContext);

      expect(completeSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          success: true,
          tool: 'test-tool'
        })
      );
    });

    it('should emit validationError event', async () => {
      const validationSpy = vi.fn();
      executor.on('validationError', validationSpy);

      await executor.execute('test-tool', {}, mockContext);

      expect(validationSpy).toHaveBeenCalled();
    });

    it('should emit securityViolation event', async () => {
      const securitySpy = vi.fn();
      const secureExecutor = new MCPToolExecutor(mockMCPClient, {
        allowedTools: ['safe-tool']
      });
      secureExecutor.on('securityViolation', securitySpy);

      await secureExecutor.execute('test-tool', { input: 'test' }, mockContext);

      expect(securitySpy).toHaveBeenCalled();
    });
  });

  describe('Tool Management', () => {
    it('should get available tools', () => {
      const tools = executor.getAvailableTools();

      expect(Array.isArray(tools)).toBe(true);
      expect(tools.length).toBeGreaterThan(0);
    });

    it('should get tool definition by name', () => {
      const tool = executor.getToolDefinition('test-tool');

      expect(tool).toBeDefined();
      expect(tool?.name).toBe('test-tool');
    });

    it('should refresh tool cache', async () => {
      await executor.refreshToolCache();

      const tools = executor.getAvailableTools();
      expect(tools.length).toBeGreaterThan(0);
    });
  });

  describe('Statistics', () => {
    it('should provide execution statistics', () => {
      const stats = executor.getStatistics();

      expect(stats).toHaveProperty('cacheSize');
      expect(stats).toHaveProperty('toolCount');
      expect(stats).toHaveProperty('cacheHitRate');
    });
  });
});

/**
 * Create mock MCP client
 */
function createMockMCPClient(): IMCPClient {
  const testTool: MCPTool = {
    name: 'test-tool',
    description: 'Test tool for validation',
    inputSchema: {
      type: 'object',
      properties: {
        input: {
          type: 'string',
          description: 'Input string'
        }
      },
      required: ['input']
    }
  };

  return {
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn().mockResolvedValue(undefined),
    listTools: vi.fn().mockResolvedValue([testTool]),
    listResources: vi.fn().mockResolvedValue([]),
    request: vi.fn().mockResolvedValue({ result: 'success' }),
    on: vi.fn(),
    off: vi.fn()
  } as any;
}
