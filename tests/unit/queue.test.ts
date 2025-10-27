/**
 * AsyncCommandQueue Unit Tests
 * Tests concurrent command execution, rate limiting, and priority queue behavior
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AsyncCommandQueue } from '../../src/core/queue';
import { CommandProcessor } from '../../src/core/processor';
import { CommandContext, CommandResult } from '../../src/types';

describe('AsyncCommandQueue', () => {
  let processor: CommandProcessor;
  let queue: AsyncCommandQueue;
  let mockContext: CommandContext;

  beforeEach(() => {
    const mockConfig = {
      mode: 'interactive' as const,
      aiProvider: 'ollama',
      model: 'test-model',
      timeout: 5000,
      maxHistorySize: 100,
      verbose: false,
    };

    processor = new CommandProcessor(mockConfig);
    mockContext = {
      command: 'test',
      args: [],
      workingDirectory: process.cwd(),
      environment: {},
    };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Queue Operations', () => {
    it('should initialize with default options', () => {
      queue = new AsyncCommandQueue(processor);
      const status = queue.getStatus();

      expect(status.concurrency).toBe(1);
      expect(status.rateLimit).toBe(10);
      expect(status.queueSize).toBe(0);
      expect(status.processing).toBe(0);
    });

    it('should initialize with custom options', () => {
      queue = new AsyncCommandQueue(processor, {
        concurrency: 5,
        rateLimit: 20,
        maxQueueSize: 50,
      });

      const status = queue.getStatus();
      expect(status.concurrency).toBe(5);
      expect(status.rateLimit).toBe(20);
    });

    it('should enqueue and process commands in order', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockResolvedValue({
        success: true,
        output: 'test output',
        exitCode: 0,
        timestamp: new Date(),
      });

      const promise1 = queue.enqueue('echo test1', mockContext);
      const promise2 = queue.enqueue('echo test2', mockContext);

      const results = await Promise.all([promise1, promise2]);

      expect(results).toHaveLength(2);
      expect(executeSpy).toHaveBeenCalledTimes(2);
    });

    it('should respect priority ordering', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const executionOrder: string[] = [];
      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockImplementation(async (ctx) => {
        executionOrder.push(ctx.command);
        return {
          success: true,
          output: 'done',
          exitCode: 0,
          timestamp: new Date(),
        };
      });

      // Enqueue commands with different priorities
      queue.enqueue('low', mockContext, 1);
      queue.enqueue('high', mockContext, 10);
      queue.enqueue('medium', mockContext, 5);

      await queue.drain();

      // High priority should execute first
      expect(executionOrder[0]).toBe('high');
      expect(executionOrder[1]).toBe('medium');
      expect(executionOrder[2]).toBe('low');
    });
  });

  describe('Concurrency Control', () => {
    it('should respect concurrency limit', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 2 });

      let activeCount = 0;
      let maxActive = 0;

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockImplementation(async () => {
        activeCount++;
        maxActive = Math.max(maxActive, activeCount);

        // Simulate async work
        await new Promise((resolve) => setTimeout(resolve, 50));

        activeCount--;
        return {
          success: true,
          output: 'done',
          exitCode: 0,
          timestamp: new Date(),
        };
      });

      // Enqueue 5 commands
      const promises = Array.from({ length: 5 }, (_, i) =>
        queue.enqueue(`command-${i}`, mockContext)
      );

      await Promise.all(promises);

      // Should never exceed concurrency limit
      expect(maxActive).toBeLessThanOrEqual(2);
      expect(executeSpy).toHaveBeenCalledTimes(5);
    });

    it('should process commands in parallel when concurrency allows', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 3 });

      const startTimes: number[] = [];
      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockImplementation(async () => {
        startTimes.push(Date.now());
        await new Promise((resolve) => setTimeout(resolve, 100));
        return {
          success: true,
          output: 'done',
          exitCode: 0,
          timestamp: new Date(),
        };
      });

      const promises = Array.from({ length: 3 }, (_, i) =>
        queue.enqueue(`parallel-${i}`, mockContext)
      );

      await Promise.all(promises);

      // All three should start within a small time window
      const timeDiff = Math.max(...startTimes) - Math.min(...startTimes);
      expect(timeDiff).toBeLessThan(50); // Started nearly simultaneously
    });
  });

  describe('Rate Limiting', () => {
    it('should enforce rate limit', async () => {
      queue = new AsyncCommandQueue(processor, {
        concurrency: 10,
        rateLimit: 5, // 5 commands per second
      });

      const executionTimes: number[] = [];
      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockImplementation(async () => {
        executionTimes.push(Date.now());
        return {
          success: true,
          output: 'done',
          exitCode: 0,
          timestamp: new Date(),
        };
      });

      // Enqueue 10 commands
      const promises = Array.from({ length: 10 }, (_, i) =>
        queue.enqueue(`rate-test-${i}`, mockContext)
      );

      await Promise.all(promises);

      // Check that commands are spaced according to rate limit
      // At 5 commands/sec, interval should be ~200ms
      for (let i = 1; i < 5; i++) {
        const interval = executionTimes[i] - executionTimes[i - 1];
        expect(interval).toBeGreaterThanOrEqual(180); // Allow some tolerance
      }
    });
  });

  describe('Queue Size Limits', () => {
    it('should reject commands when queue is full', async () => {
      queue = new AsyncCommandQueue(processor, {
        concurrency: 1,
        maxQueueSize: 3,
      });

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockImplementation(
        async () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  success: true,
                  output: 'done',
                  exitCode: 0,
                  timestamp: new Date(),
                }),
              100
            )
          )
      );

      // Fill the queue
      queue.enqueue('cmd1', mockContext);
      queue.enqueue('cmd2', mockContext);
      queue.enqueue('cmd3', mockContext);

      // This should throw because queue is full
      await expect(queue.enqueue('cmd4', mockContext)).rejects.toThrow(
        /Queue is full/
      );
    });
  });

  describe('Error Handling', () => {
    it('should handle command execution errors', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockRejectedValue(new Error('Execution failed'));

      await expect(queue.enqueue('failing-command', mockContext)).rejects.toThrow(
        'Execution failed'
      );
    });

    it('should continue processing after error', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy
        .mockRejectedValueOnce(new Error('First command fails'))
        .mockResolvedValueOnce({
          success: true,
          output: 'second command succeeds',
          exitCode: 0,
          timestamp: new Date(),
        });

      const promise1 = queue.enqueue('fail', mockContext);
      const promise2 = queue.enqueue('success', mockContext);

      await expect(promise1).rejects.toThrow('First command fails');
      await expect(promise2).resolves.toMatchObject({ success: true });
    });

    it('should handle parsing errors gracefully', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const parseSpy = vi.spyOn(processor, 'parseCommand');
      parseSpy.mockImplementation(() => {
        throw new Error('Parse error');
      });

      await expect(queue.enqueue('invalid command', mockContext)).rejects.toThrow(
        'Parse error'
      );
    });
  });

  describe('Queue Management', () => {
    it('should clear queue and reject pending commands', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockImplementation(
        async () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  success: true,
                  output: 'done',
                  exitCode: 0,
                  timestamp: new Date(),
                }),
              1000
            )
          )
      );

      const promise1 = queue.enqueue('cmd1', mockContext);
      const promise2 = queue.enqueue('cmd2', mockContext);
      const promise3 = queue.enqueue('cmd3', mockContext);

      // Clear immediately
      queue.clear();

      // All should be rejected
      await expect(promise1).rejects.toThrow('Queue cleared');
      await expect(promise2).rejects.toThrow('Queue cleared');
      await expect(promise3).rejects.toThrow('Queue cleared');
    });

    it('should update options dynamically', () => {
      queue = new AsyncCommandQueue(processor, {
        concurrency: 1,
        rateLimit: 10,
        maxQueueSize: 100,
      });

      queue.updateOptions({
        concurrency: 5,
        rateLimit: 20,
      });

      const status = queue.getStatus();
      expect(status.concurrency).toBe(5);
      expect(status.rateLimit).toBe(20);
    });

    it('should drain and wait for all commands to complete', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 2 });

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockImplementation(
        async () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  success: true,
                  output: 'done',
                  exitCode: 0,
                  timestamp: new Date(),
                }),
              50
            )
          )
      );

      // Enqueue multiple commands
      queue.enqueue('cmd1', mockContext);
      queue.enqueue('cmd2', mockContext);
      queue.enqueue('cmd3', mockContext);

      // Drain should wait for all to complete
      await queue.drain();

      const status = queue.getStatus();
      expect(status.queueSize).toBe(0);
      expect(status.processing).toBe(0);
    });
  });

  describe('Events', () => {
    it('should emit commandQueued event', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const queuedListener = vi.fn();
      queue.on('commandQueued', queuedListener);

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockResolvedValue({
        success: true,
        output: 'done',
        exitCode: 0,
        timestamp: new Date(),
      });

      await queue.enqueue('test', mockContext);

      expect(queuedListener).toHaveBeenCalledWith(
        expect.objectContaining({
          command: 'test',
          queueSize: expect.any(Number),
        })
      );
    });

    it('should emit commandStart event', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const startListener = vi.fn();
      queue.on('commandStart', startListener);

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockResolvedValue({
        success: true,
        output: 'done',
        exitCode: 0,
        timestamp: new Date(),
      });

      await queue.enqueue('test', mockContext);

      expect(startListener).toHaveBeenCalled();
    });

    it('should emit commandComplete event', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const completeListener = vi.fn();
      queue.on('commandComplete', completeListener);

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockResolvedValue({
        success: true,
        output: 'done',
        exitCode: 0,
        timestamp: new Date(),
      });

      await queue.enqueue('test', mockContext);

      expect(completeListener).toHaveBeenCalledWith(
        expect.objectContaining({
          command: 'test',
          result: expect.objectContaining({ success: true }),
        })
      );
    });

    it('should emit commandError event on failure', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const errorListener = vi.fn();
      queue.on('commandError', errorListener);

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockRejectedValue(new Error('Test error'));

      await expect(queue.enqueue('failing', mockContext)).rejects.toThrow();

      expect(errorListener).toHaveBeenCalledWith(
        expect.objectContaining({
          command: 'failing',
          error: expect.any(Error),
        })
      );
    });

    it('should emit queueCleared event', () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const clearListener = vi.fn();
      queue.on('queueCleared', clearListener);

      queue.clear();

      expect(clearListener).toHaveBeenCalled();
    });
  });

  describe('Status Reporting', () => {
    it('should accurately report queue status', async () => {
      queue = new AsyncCommandQueue(processor, {
        concurrency: 2,
        rateLimit: 10,
      });

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockImplementation(
        async () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  success: true,
                  output: 'done',
                  exitCode: 0,
                  timestamp: new Date(),
                }),
              100
            )
          )
      );

      // Enqueue commands but don't await
      queue.enqueue('cmd1', mockContext);
      queue.enqueue('cmd2', mockContext);
      queue.enqueue('cmd3', mockContext);

      // Check status immediately
      const status = queue.getStatus();
      expect(status.queueSize).toBeGreaterThan(0);
      expect(status.processing).toBeGreaterThan(0);

      await queue.drain();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty command string', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const parseSpy = vi.spyOn(processor, 'parseCommand');
      parseSpy.mockImplementation(() => {
        throw new Error('Empty command');
      });

      await expect(queue.enqueue('', mockContext)).rejects.toThrow('Empty command');
    });

    it('should handle very long queue times', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 1 });

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockImplementation(
        async () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  success: true,
                  output: 'done',
                  exitCode: 0,
                  timestamp: new Date(),
                }),
              200
            )
          )
      );

      const promises = Array.from({ length: 5 }, (_, i) =>
        queue.enqueue(`long-wait-${i}`, mockContext)
      );

      const results = await Promise.all(promises);
      expect(results).toHaveLength(5);
      results.forEach((result) => expect(result.success).toBe(true));
    });

    it('should handle rapid sequential enqueues', async () => {
      queue = new AsyncCommandQueue(processor, { concurrency: 3 });

      const executeSpy = vi.spyOn(processor, 'execute');
      executeSpy.mockResolvedValue({
        success: true,
        output: 'done',
        exitCode: 0,
        timestamp: new Date(),
      });

      // Rapidly enqueue 20 commands
      const promises = Array.from({ length: 20 }, (_, i) =>
        queue.enqueue(`rapid-${i}`, mockContext)
      );

      const results = await Promise.all(promises);
      expect(results).toHaveLength(20);
      expect(executeSpy).toHaveBeenCalledTimes(20);
    });
  });
});
