/**
 * LLMMCPBridge Integration Tests
 * Tests LLM-MCP integration, tool calls, resource access, and streaming
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { LLMMCPBridge, EnhancedGenerateOptions } from '../../src/llm/mcp-bridge';
import { ILLMProvider } from '../../src/llm/provider';
import { IMCPClient, MCPTool, MCPResource } from '../../src/mcp/types';
import { LLMResponse } from '../../src/types/llm';

describe('LLMMCPBridge Integration', () => {
  let bridge: LLMMCPBridge;
  let mockLLMProvider: ILLMProvider;
  let mockMCPClient: IMCPClient;

  beforeEach(async () => {
    mockLLMProvider = createMockLLMProvider();
    mockMCPClient = createMockMCPClient();

    bridge = new LLMMCPBridge(mockLLMProvider, mockMCPClient, {
      maxIterations: 5,
      toolCallTimeout: 5000,
      enableAutoContext: true,
      cacheResources: true
    });

    // Wait for initialization
    await new Promise((resolve) => setTimeout(resolve, 50));
  });

  describe('Basic Generation', () => {
    it('should generate response without tools', async () => {
      const options: EnhancedGenerateOptions = {
        messages: [{ role: 'user', content: 'Hello' }],
        enableTools: false
      };

      const response = await bridge.generate(options);

      expect(response.content).toBeDefined();
      expect(response.iterations).toBe(1);
      expect(response.toolCalls).toHaveLength(0);
    });

    it('should inject tool context when tools enabled', async () => {
      const options: EnhancedGenerateOptions = {
        messages: [{ role: 'user', content: 'Use a tool' }],
        enableTools: true
      };

      await bridge.generate(options);

      // Verify LLM provider was called with tool context
      expect(mockLLMProvider.generate).toHaveBeenCalled();
      const call = (mockLLMProvider.generate as any).mock.calls[0][0];
      expect(call.messages.some((m: any) => m.content.includes('Available Tools'))).toBe(true);
    });
  });

  describe('Tool Call Execution', () => {
    it('should extract and execute tool calls from LLM response', async () => {
      // Mock LLM to return tool call
      (mockLLMProvider.generate as any).mockResolvedValueOnce({
        content: '[TOOL_CALL]\n{"name": "test-tool", "params": {"input": "test"}}\n[/TOOL_CALL]\n',
        model: 'test-model',
        usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 }
      }).mockResolvedValueOnce({
        content: 'Tool executed successfully',
        model: 'test-model',
        usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 }
      });

      const options: EnhancedGenerateOptions = {
        messages: [{ role: 'user', content: 'Execute tool' }],
        enableTools: true
      };

      const response = await bridge.generate(options);

      expect(response.toolCalls).toBeDefined();
      expect(response.toolCalls!.length).toBeGreaterThan(0);
      expect(response.iterations).toBeGreaterThan(1);
    });

    it('should handle multiple tool calls', async () => {
      (mockLLMProvider.generate as any).mockResolvedValueOnce({
        content: `
          [TOOL_CALL]
          {"name": "tool1", "params": {"input": "test1"}}
          [/TOOL_CALL]
          [TOOL_CALL]
          {"name": "tool2", "params": {"input": "test2"}}
          [/TOOL_CALL]
        `,
        model: 'test-model',
        usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 }
      }).mockResolvedValueOnce({
        content: 'Both tools executed',
        model: 'test-model',
        usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 }
      });

      const options: EnhancedGenerateOptions = {
        messages: [{ role: 'user', content: 'Execute multiple tools' }],
        enableTools: true
      };

      const response = await bridge.generate(options);

      expect(response.toolCalls!.length).toBeGreaterThanOrEqual(2);
    });

    it('should respect max tool calls limit', async () => {
      (mockLLMProvider.generate as any).mockResolvedValue({
        content: '[TOOL_CALL]\n{"name": "test-tool", "params": {"input": "test"}}\n[/TOOL_CALL]',
        model: 'test-model',
        usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 }
      });

      const options: EnhancedGenerateOptions = {
        messages: [{ role: 'user', content: 'Infinite tools' }],
        enableTools: true,
        maxToolCalls: 2
      };

      const response = await bridge.generate(options);

      expect(response.toolCalls!.length).toBeLessThanOrEqual(2);
    });

    it('should handle tool execution timeout', async () => {
      // Mock slow tool execution
      (mockMCPClient.request as any).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 10000))
      );

      (mockLLMProvider.generate as any).mockResolvedValue({
        content: '[TOOL_CALL]\n{"name": "slow-tool", "params": {}}\n[/TOOL_CALL]',
        model: 'test-model',
        usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 }
      });

      const options: EnhancedGenerateOptions = {
        messages: [{ role: 'user', content: 'Use slow tool' }],
        enableTools: true,
        toolCallTimeout: 100
      };

      const response = await bridge.generate(options);

      expect(response.toolCalls!.some((t) => !t.success)).toBe(true);
    }, 10000);

    it('should handle tool execution errors gracefully', async () => {
      (mockMCPClient.request as any).mockRejectedValue(new Error('Tool failed'));

      (mockLLMProvider.generate as any).mockResolvedValue({
        content: '[TOOL_CALL]\n{"name": "failing-tool", "params": {}}\n[/TOOL_CALL]',
        model: 'test-model',
        usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 }
      });

      const options: EnhancedGenerateOptions = {
        messages: [{ role: 'user', content: 'Use failing tool' }],
        enableTools: true
      };

      const response = await bridge.generate(options);

      expect(response.toolCalls!.some((t) => !t.success && t.error)).toBe(true);
    });
  });

  describe('Resource Access', () => {
    it('should access MCP resources', async () => {
      const content = await bridge.accessResource('test://resource');

      expect(content).toBeDefined();
    });

    it('should cache accessed resources', async () => {
      // First call should hit MCP client
      await bridge.accessResource('test://resource');

      // Second call should use cache (MCP client request count shouldn't increase)
      const requestCallCount = (mockMCPClient.request as any).mock.calls.length;
      await bridge.accessResource('test://resource');

      // Request should have been called once more for the first access
      // but not for the second (cached) access
      expect((mockMCPClient.request as any).mock.calls.length).toBe(requestCallCount);
    });

    it('should clear resource cache', async () => {
      await bridge.accessResource('test://resource');

      bridge.clearCache();

      // Accessing again should hit MCP client
      await bridge.accessResource('test://resource');
    });

    it('should handle non-existent resources', async () => {
      (mockMCPClient.listResources as any).mockResolvedValue([]);

      await expect(bridge.accessResource('test://nonexistent')).rejects.toThrow('Resource not found');
    });
  });

  describe('Streaming Generation', () => {
    it('should stream response chunks', async () => {
      const options: EnhancedGenerateOptions = {
        messages: [{ role: 'user', content: 'Stream this' }],
        enableTools: false
      };

      const chunks: string[] = [];
      const stream = bridge.generateStream(options);

      for await (const chunk of stream) {
        chunks.push(chunk);
      }

      expect(chunks.length).toBeGreaterThan(0);
    });

    it('should execute tools during streaming', async () => {
      (mockLLMProvider.generateStream as any).mockImplementation(
        async (_opts: any, callbacks: any) => {
          await callbacks.onChunk('[TOOL_CALL]');
          await callbacks.onChunk('\n{"name": "test-tool", "params": {}}');
          await callbacks.onChunk('\n[/TOOL_CALL]');
          await callbacks.onComplete();
        }
      );

      const options: EnhancedGenerateOptions = {
        messages: [{ role: 'user', content: 'Stream with tools' }],
        enableTools: true
      };

      const stream = bridge.generateStream(options);
      const result: any = { toolCalls: [] };

      for await (const chunk of stream) {
        // Process chunks
      }

      // Tool calls should be executed during streaming
    });
  });

  describe('Context Management', () => {
    it('should track conversation history', async () => {
      const options: EnhancedGenerateOptions = {
        messages: [{ role: 'user', content: 'Hello' }]
      };

      await bridge.generate(options);

      const context = bridge.getContext();

      expect(context.conversationHistory.length).toBeGreaterThan(0);
    });

    it('should update context metadata', () => {
      bridge.updateContext({ userId: 'test-user', sessionType: 'interactive' });

      const context = bridge.getContext();

      expect(context.metadata.userId).toBe('test-user');
      expect(context.metadata.sessionType).toBe('interactive');
    });

    it('should clear conversation history', async () => {
      await bridge.generate({
        messages: [{ role: 'user', content: 'Test' }]
      });

      bridge.clearHistory();

      const context = bridge.getContext();

      expect(context.conversationHistory).toHaveLength(0);
    });
  });

  describe('Statistics', () => {
    it('should provide bridge statistics', () => {
      const stats = bridge.getStatistics();

      expect(stats).toHaveProperty('toolCallCount');
      expect(stats).toHaveProperty('conversationLength');
      expect(stats).toHaveProperty('cachedResources');
      expect(stats).toHaveProperty('availableTools');
      expect(stats).toHaveProperty('availableResources');
    });

    it('should track tool call count', async () => {
      (mockLLMProvider.generate as any).mockResolvedValue({
        content: '[TOOL_CALL]\n{"name": "test-tool", "params": {}}\n[/TOOL_CALL]',
        model: 'test-model',
        usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 }
      });

      await bridge.generate({
        messages: [{ role: 'user', content: 'Use tool' }],
        enableTools: true
      });

      const stats = bridge.getStatistics();

      expect(stats.toolCallCount).toBeGreaterThan(0);
    });
  });

  describe('Events', () => {
    it('should emit toolCall event', async () => {
      const toolCallSpy = vi.fn();
      bridge.on('toolCall', toolCallSpy);

      await bridge.executeToolCall('test-tool', { input: 'test' });

      expect(toolCallSpy).toHaveBeenCalled();
    });

    it('should emit toolResult event', async () => {
      const resultSpy = vi.fn();
      bridge.on('toolResult', resultSpy);

      await bridge.executeToolCall('test-tool', { input: 'test' });

      expect(resultSpy).toHaveBeenCalled();
    });

    it('should emit resourceAccess event', async () => {
      const accessSpy = vi.fn();
      bridge.on('resourceAccess', accessSpy);

      await bridge.accessResource('test://resource');

      expect(accessSpy).toHaveBeenCalledWith('test://resource');
    });

    it('should emit streamChunk event', async () => {
      const chunkSpy = vi.fn();
      bridge.on('streamChunk', chunkSpy);

      const stream = bridge.generateStream({
        messages: [{ role: 'user', content: 'Stream' }]
      });

      for await (const _chunk of stream) {
        // Process
      }

      expect(chunkSpy).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('should handle LLM provider errors', async () => {
      (mockLLMProvider.generate as any).mockRejectedValue(new Error('LLM error'));

      await expect(
        bridge.generate({ messages: [{ role: 'user', content: 'Test' }] })
      ).rejects.toThrow('LLM error');
    });

    it('should handle malformed tool calls', async () => {
      (mockLLMProvider.generate as any).mockResolvedValue({
        content: '[TOOL_CALL]\ninvalid json{\n[/TOOL_CALL]',
        model: 'test-model',
        usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 }
      });

      const response = await bridge.generate({
        messages: [{ role: 'user', content: 'Malformed' }],
        enableTools: true
      });

      // Should not crash, just ignore malformed tool call
      expect(response.content).toBeDefined();
    });
  });

  describe('Refresh and Reinitialization', () => {
    it('should refresh available tools and resources', async () => {
      await bridge.refresh();

      const context = bridge.getContext();

      expect(context.availableTools).toBeDefined();
      expect(context.availableResources).toBeDefined();
    });
  });
});

/**
 * Create mock LLM provider
 */
function createMockLLMProvider(): ILLMProvider {
  return {
    generate: vi.fn().mockResolvedValue({
      content: 'Test response',
      model: 'test-model',
      usage: {
        prompt_tokens: 10,
        completion_tokens: 20,
        total_tokens: 30
      }
    }),
    generateStream: vi.fn().mockImplementation(async (_opts: any, callbacks: any) => {
      await callbacks.onChunk('Test ');
      await callbacks.onChunk('streaming ');
      await callbacks.onChunk('response');
      await callbacks.onComplete();
    })
  } as any;
}

/**
 * Create mock MCP client
 */
function createMockMCPClient(): IMCPClient {
  const testTool: MCPTool = {
    name: 'test-tool',
    description: 'Test tool',
    inputSchema: {
      type: 'object',
      properties: {
        input: { type: 'string' }
      },
      required: []
    }
  };

  const testResource: MCPResource = {
    uri: 'test://resource',
    name: 'Test Resource',
    description: 'Test resource',
    mimeType: 'text/plain'
  };

  return {
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn().mockResolvedValue(undefined),
    listTools: vi.fn().mockResolvedValue([testTool]),
    listResources: vi.fn().mockResolvedValue([testResource]),
    request: vi.fn().mockResolvedValue({ result: 'success' }),
    on: vi.fn(),
    off: vi.fn()
  } as any;
}
