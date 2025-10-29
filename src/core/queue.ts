/**
 * Async queue system for command processing
 * Handles concurrent command execution with priority and rate limiting
 */

import { EventEmitter } from 'events';
import { QueuedCommand, CommandResult, CommandContext } from '../types';
import { CommandProcessor } from './processor';

export interface QueueOptions {
  concurrency?: number;
  rateLimit?: number; // Commands per second
  maxQueueSize?: number;
}

export class AsyncCommandQueue extends EventEmitter {
  private queue: QueuedCommand[] = [];
  private processing = 0;
  private processingCommands: Map<string, QueuedCommand> = new Map();
  private concurrency: number;
  private rateLimit: number;
  private maxQueueSize: number;
  private lastExecutionTime = 0;
  private processor: CommandProcessor;

  constructor(processor: CommandProcessor, options: QueueOptions = {}) {
    super();
    this.processor = processor;
    this.concurrency = options.concurrency || 1;
    this.rateLimit = options.rateLimit || 10;
    this.maxQueueSize = options.maxQueueSize || 100;
  }

  /**
   * Add command to queue
   */
  public async enqueue(
    command: string,
    context: CommandContext,
    priority = 0
  ): Promise<CommandResult> {
    // Check total capacity: queued + processing
    if (this.queue.length + this.processing >= this.maxQueueSize) {
      throw new Error(
        `Queue is full (max: ${this.maxQueueSize}). Please wait for commands to complete.`
      );
    }

    return new Promise<CommandResult>((resolve, reject) => {
      const queuedCommand: QueuedCommand = {
        id: this.generateId(),
        command,
        priority,
        timestamp: new Date(),
        resolve: (result: CommandResult) => {
          this.emit('commandComplete', { command, result });
          resolve(result);
        },
        reject: (error: Error) => {
          this.emit('commandError', { command, error });
          reject(error);
        },
      };

      // Insert by priority (higher priority first)
      const insertIndex = this.queue.findIndex(
        (item) => item.priority < priority
      );
      if (insertIndex === -1) {
        this.queue.push(queuedCommand);
      } else {
        this.queue.splice(insertIndex, 0, queuedCommand);
      }

      this.emit('commandQueued', { command, queueSize: this.queue.length });

      // Defer processing to allow priority ordering to work correctly
      // Use setImmediate/nextTick equivalent for browser/node compatibility
      setTimeout(() => this.processNext(context), 0);
    });
  }

  /**
   * Process next command in queue
   */
  private async processNext(context: CommandContext): Promise<void> {
    // Check if we can start any new commands
    if (this.processing >= this.concurrency || this.queue.length === 0) {
      return;
    }

    // Rate limiting - always enforce minimum interval between command starts
    const now = Date.now();
    const minInterval = 1000 / this.rateLimit;
    const timeSinceLastExecution = now - this.lastExecutionTime;

    if (this.lastExecutionTime > 0 && timeSinceLastExecution < minInterval) {
      setTimeout(
        () => this.processNext(context),
        minInterval - timeSinceLastExecution
      );
      return;
    }

    // Start next command
    const queuedCommand = this.queue.shift();
    if (!queuedCommand) {
      return;
    }

    this.processing++;
    this.processingCommands.set(queuedCommand.id, queuedCommand);
    this.lastExecutionTime = Date.now();

    this.emit('commandStart', {
      command: queuedCommand.command,
      queueSize: this.queue.length,
    });

    // Execute command asynchronously without waiting
    this.executeCommand(queuedCommand, context);

    // Try to start more commands if concurrency allows
    if (this.processing < this.concurrency && this.queue.length > 0) {
      this.processNext(context);
    }
  }

  /**
   * Execute a single command
   */
  private async executeCommand(
    queuedCommand: QueuedCommand,
    context: CommandContext
  ): Promise<void> {
    try {
      // Parse command
      const { command, args } = this.processor.parseCommand(
        queuedCommand.command
      );

      // Execute command
      const result = await this.processor.execute({
        ...context,
        command,
        args,
      });

      queuedCommand.resolve(result);
    } catch (error) {
      queuedCommand.reject(
        error instanceof Error ? error : new Error(String(error))
      );
    } finally {
      this.processing--;
      this.processingCommands.delete(queuedCommand.id);
      this.processNext(context);
    }
  }

  /**
   * Get queue status
   */
  public getStatus(): {
    queueSize: number;
    processing: number;
    concurrency: number;
    rateLimit: number;
  } {
    return {
      queueSize: this.queue.length,
      processing: this.processing,
      concurrency: this.concurrency,
      rateLimit: this.rateLimit,
    };
  }

  /**
   * Clear all queued commands
   */
  public clear(): void {
    // Reject all queued commands
    this.queue.forEach((cmd) => {
      cmd.reject(new Error('Queue cleared'));
    });
    this.queue = [];

    // Reject all currently processing commands
    this.processingCommands.forEach((cmd) => {
      cmd.reject(new Error('Queue cleared'));
    });
    this.processingCommands.clear();

    this.emit('queueCleared');
  }

  /**
   * Update queue options
   */
  public updateOptions(options: Partial<QueueOptions>): void {
    if (options.concurrency !== undefined) {
      this.concurrency = options.concurrency;
    }
    if (options.rateLimit !== undefined) {
      this.rateLimit = options.rateLimit;
    }
    if (options.maxQueueSize !== undefined) {
      this.maxQueueSize = options.maxQueueSize;
    }
  }

  /**
   * Generate unique command ID
   */
  private generateId(): string {
    return `cmd_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Wait for all commands to complete
   */
  public async drain(): Promise<void> {
    return new Promise((resolve) => {
      const checkEmpty = () => {
        if (this.queue.length === 0 && this.processing === 0) {
          resolve();
        } else {
          setTimeout(checkEmpty, 100);
        }
      };
      checkEmpty();
    });
  }
}
