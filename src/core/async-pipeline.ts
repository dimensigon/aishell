/**
 * Async Processing Pipeline
 * Advanced command processing with streaming, middleware, and error recovery
 *
 * Features:
 * - Stage-based execution with priority ordering
 * - Retry logic with exponential backoff
 * - Streaming support for real-time processing
 * - Performance monitoring and metrics
 * - Abort signals for cancellation
 * - Error recovery with custom handlers
 */

import { EventEmitter } from 'eventemitter3';
import { CommandContext, CommandResult } from '../types';
import { ErrorHandler } from './error-handler';
import { createLogger } from './logger';

/**
 * Pipeline stage
 */
export interface PipelineStage<TInput = any, TOutput = any> {
  name: string;
  priority?: number;
  execute: (input: TInput, context: PipelineContext) => Promise<TOutput>;
  canHandle?: (input: TInput) => boolean;
  onError?: (error: Error, input: TInput) => Promise<TOutput | null>;
}

/**
 * Pipeline context
 */
export interface PipelineContext {
  id: string;
  metadata: Record<string, any>;
  state: Map<string, any>;
  abortSignal?: AbortSignal;
  timestamp: number;
}

/**
 * Pipeline result
 */
export interface PipelineResult<T = any> {
  success: boolean;
  data?: T;
  error?: Error;
  stages: StageResult[];
  duration: number;
  context: PipelineContext;
}

/**
 * Stage execution result
 */
export interface StageResult {
  stage: string;
  success: boolean;
  duration: number;
  error?: Error;
  output?: any;
}

/**
 * Stream chunk
 */
export interface StreamChunk<T = any> {
  stage: string;
  data: T;
  isComplete: boolean;
  timestamp: number;
}

/**
 * Pipeline events
 */
export interface PipelineEvents {
  stageStart: (stage: string, context: PipelineContext) => void;
  stageComplete: (stage: string, result: StageResult) => void;
  stageError: (stage: string, error: Error) => void;
  pipelineComplete: (result: PipelineResult) => void;
  pipelineError: (error: Error) => void;
  streamChunk: (chunk: StreamChunk) => void;
}

/**
 * Pipeline configuration
 */
export interface PipelineConfig {
  maxConcurrentStages?: number;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  enableStreaming?: boolean;
  abortOnError?: boolean;
}

/**
 * Async Processing Pipeline
 */
export class AsyncPipeline<TInput = any, TOutput = any> extends EventEmitter<PipelineEvents> {
  private stages: PipelineStage[] = [];
  private config: Required<PipelineConfig>;
  private activeExecutions = new Map<string, AbortController>();
  private readonly errorHandler: ErrorHandler;
  private readonly logger = createLogger('AsyncPipeline');
  private metrics = {
    totalExecutions: 0,
    successfulExecutions: 0,
    failedExecutions: 0,
    averageDuration: 0,
    stageMetrics: new Map<string, { executions: number; failures: number; avgDuration: number }>()
  };

  constructor(config: PipelineConfig = {}, errorHandler?: ErrorHandler) {
    super();
    this.config = {
      maxConcurrentStages: config.maxConcurrentStages || 5,
      timeout: config.timeout || 30000,
      retryAttempts: config.retryAttempts || 2,
      retryDelay: config.retryDelay || 1000,
      enableStreaming: config.enableStreaming || false,
      abortOnError: config.abortOnError || false
    };
    this.errorHandler = errorHandler || new ErrorHandler();
  }

  /**
   * Get error handler instance
   */
  getErrorHandler(): ErrorHandler {
    return this.errorHandler;
  }

  /**
   * Add stage to pipeline
   */
  addStage(stage: PipelineStage): this {
    this.stages.push(stage);
    // Sort by priority (higher first)
    this.stages.sort((a, b) => (b.priority || 0) - (a.priority || 0));
    return this;
  }

  /**
   * Remove stage from pipeline
   */
  removeStage(stageName: string): this {
    this.stages = this.stages.filter((s) => s.name !== stageName);
    return this;
  }

  /**
   * Execute pipeline
   */
  async execute(input: TInput, metadata: Record<string, any> = {}): Promise<PipelineResult<TOutput>> {
    const startTime = Date.now();
    const context: PipelineContext = {
      id: this.generateId(),
      metadata,
      state: new Map(),
      timestamp: Date.now()
    };

    const abortController = new AbortController();
    context.abortSignal = abortController.signal;
    this.activeExecutions.set(context.id, abortController);

    const stageResults: StageResult[] = [];
    let currentData: any = input;
    let pipelineError: Error | undefined;

    try {
      // Execute stages sequentially
      for (const stage of this.stages) {
        // Check if stage can handle input
        if (stage.canHandle && !stage.canHandle(currentData)) {
          continue;
        }

        // Check for abort
        if (context.abortSignal?.aborted) {
          throw new Error('Pipeline execution aborted');
        }

        const stageResult = await this.executeStage(stage, currentData, context);
        stageResults.push(stageResult);

        if (!stageResult.success) {
          if (this.config.abortOnError) {
            pipelineError = stageResult.error;
            break;
          }
        } else {
          currentData = stageResult.output;
        }
      }

      const result: PipelineResult<TOutput> = {
        success: !pipelineError,
        data: currentData,
        error: pipelineError,
        stages: stageResults,
        duration: Date.now() - startTime,
        context
      };

      // Update metrics
      this.updateMetrics(result);

      this.emit('pipelineComplete', result);
      return result;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      const result: PipelineResult<TOutput> = {
        success: false,
        error: err,
        stages: stageResults,
        duration: Date.now() - startTime,
        context
      };

      this.emit('pipelineError', err);
      return result;
    } finally {
      this.activeExecutions.delete(context.id);
    }
  }

  /**
   * Execute pipeline with streaming
   */
  async *executeStream(
    input: TInput,
    metadata: Record<string, any> = {}
  ): AsyncGenerator<StreamChunk<any>, PipelineResult<TOutput>, undefined> {
    const startTime = Date.now();
    const context: PipelineContext = {
      id: this.generateId(),
      metadata,
      state: new Map(),
      timestamp: Date.now()
    };

    const abortController = new AbortController();
    context.abortSignal = abortController.signal;
    this.activeExecutions.set(context.id, abortController);

    const stageResults: StageResult[] = [];
    let currentData: any = input;
    let pipelineError: Error | undefined;

    try {
      for (const stage of this.stages) {
        if (stage.canHandle && !stage.canHandle(currentData)) {
          continue;
        }

        if (context.abortSignal?.aborted) {
          throw new Error('Pipeline execution aborted');
        }

        // Emit stream chunk before stage execution
        yield {
          stage: stage.name,
          data: { status: 'started', input: currentData },
          isComplete: false,
          timestamp: Date.now()
        };

        const stageResult = await this.executeStage(stage, currentData, context);
        stageResults.push(stageResult);

        // Emit stream chunk after stage execution
        const chunk: StreamChunk = {
          stage: stage.name,
          data: stageResult.output,
          isComplete: stageResult.success,
          timestamp: Date.now()
        };

        this.emit('streamChunk', chunk);
        yield chunk;

        if (!stageResult.success && this.config.abortOnError) {
          pipelineError = stageResult.error;
          break;
        }

        currentData = stageResult.output;
      }

      return {
        success: !pipelineError,
        data: currentData,
        error: pipelineError,
        stages: stageResults,
        duration: Date.now() - startTime,
        context
      };
    } finally {
      this.activeExecutions.delete(context.id);
    }
  }

  /**
   * Execute a single stage with retry logic
   */
  private async executeStage(
    stage: PipelineStage,
    input: any,
    context: PipelineContext
  ): Promise<StageResult> {
    const startTime = Date.now();
    this.emit('stageStart', stage.name, context);

    let lastError: Error | undefined;
    let attempts = 0;

    while (attempts <= this.config.retryAttempts) {
      try {
        // Execute with timeout
        const output = await this.executeWithTimeout(
          stage.execute(input, context),
          this.config.timeout
        );

        const result: StageResult = {
          stage: stage.name,
          success: true,
          duration: Date.now() - startTime,
          output
        };

        this.emit('stageComplete', stage.name, result);
        return result;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        attempts++;

        if (attempts <= this.config.retryAttempts) {
          // Wait before retry with exponential backoff
          await this.delay(this.config.retryDelay * Math.pow(2, attempts - 1));
        }
      }
    }

    // All retries failed
    const result: StageResult = {
      stage: stage.name,
      success: false,
      duration: Date.now() - startTime,
      error: lastError
    };

    // Try error handler if available
    if (stage.onError) {
      try {
        const recoveredOutput = await stage.onError(lastError!, input);
        if (recoveredOutput !== null) {
          result.success = true;
          result.output = recoveredOutput;
          result.error = undefined;
        }
      } catch (handlerError) {
        this.logger.error('Error handler failed for stage', handlerError, {
          stage: stage.name,
          originalError: lastError?.message
        });
      }
    }

    this.emit('stageError', stage.name, lastError!);
    this.emit('stageComplete', stage.name, result);

    return result;
  }

  /**
   * Execute promise with timeout
   */
  private async executeWithTimeout<T>(promise: Promise<T>, timeout: number): Promise<T> {
    return Promise.race([
      promise,
      new Promise<T>((_, reject) =>
        setTimeout(() => reject(new Error(`Stage timeout after ${timeout}ms`)), timeout)
      )
    ]);
  }

  /**
   * Abort pipeline execution
   */
  abort(pipelineId: string): void {
    const controller = this.activeExecutions.get(pipelineId);
    if (controller) {
      controller.abort();
      this.activeExecutions.delete(pipelineId);
    }
  }

  /**
   * Abort all active executions
   */
  abortAll(): void {
    this.activeExecutions.forEach((controller, _id) => {
      controller.abort();
    });
    this.activeExecutions.clear();
  }

  /**
   * Get stage by name
   */
  getStage(stageName: string): PipelineStage | undefined {
    return this.stages.find((s) => s.name === stageName);
  }

  /**
   * Get all stages
   */
  getStages(): PipelineStage[] {
    return [...this.stages];
  }

  /**
   * Clear all stages
   */
  clear(): void {
    this.stages = [];
  }

  /**
   * Get active executions count
   */
  getActiveCount(): number {
    return this.activeExecutions.size;
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<PipelineConfig>): void {
    Object.assign(this.config, config);
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `pipeline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Update pipeline metrics
   */
  private updateMetrics(result: PipelineResult): void {
    this.metrics.totalExecutions++;

    if (result.success) {
      this.metrics.successfulExecutions++;
    } else {
      this.metrics.failedExecutions++;
    }

    // Update average duration
    const totalDuration = this.metrics.averageDuration * (this.metrics.totalExecutions - 1) + result.duration;
    this.metrics.averageDuration = totalDuration / this.metrics.totalExecutions;

    // Update stage metrics
    for (const stageResult of result.stages) {
      const existing = this.metrics.stageMetrics.get(stageResult.stage) || {
        executions: 0,
        failures: 0,
        avgDuration: 0
      };

      existing.executions++;
      if (!stageResult.success) {
        existing.failures++;
      }

      const totalStageDuration = existing.avgDuration * (existing.executions - 1) + stageResult.duration;
      existing.avgDuration = totalStageDuration / existing.executions;

      this.metrics.stageMetrics.set(stageResult.stage, existing);
    }
  }

  /**
   * Get pipeline metrics
   */
  getMetrics(): {
    totalExecutions: number;
    successfulExecutions: number;
    failedExecutions: number;
    successRate: number;
    averageDuration: number;
    stageMetrics: Record<string, { executions: number; failures: number; avgDuration: number }>;
  } {
    return {
      ...this.metrics,
      successRate: this.metrics.totalExecutions > 0
        ? this.metrics.successfulExecutions / this.metrics.totalExecutions
        : 0,
      stageMetrics: Object.fromEntries(this.metrics.stageMetrics.entries())
    };
  }

  /**
   * Reset metrics
   */
  resetMetrics(): void {
    this.metrics = {
      totalExecutions: 0,
      successfulExecutions: 0,
      failedExecutions: 0,
      averageDuration: 0,
      stageMetrics: new Map()
    };
  }

  /**
   * Create middleware-style stage
   */
  static createMiddleware<T = any>(
    name: string,
    handler: (input: T, context: PipelineContext, next: () => Promise<T>) => Promise<T>,
    priority?: number
  ): PipelineStage<T, T> {
    return {
      name,
      priority,
      execute: async (input, context) => {
        return handler(input, context, async () => input);
      }
    };
  }
}

/**
 * Command pipeline adapter
 * Adapts the generic pipeline for command processing
 */
export class CommandPipeline extends AsyncPipeline<CommandContext, CommandResult> {
  constructor(config?: PipelineConfig) {
    super(config);
    this.setupDefaultStages();
  }

  /**
   * Setup default command processing stages
   */
  private setupDefaultStages(): void {
    // Pre-processing stage
    this.addStage({
      name: 'preprocess',
      priority: 100,
      execute: async (context) => {
        // Validate context
        if (!context.command) {
          throw new Error('Command is required');
        }
        return context;
      }
    });

    // Post-processing stage
    this.addStage({
      name: 'postprocess',
      priority: -100,
      execute: async (result) => {
        // Add timestamp if not present
        if (!result.timestamp) {
          result.timestamp = new Date();
        }
        return result;
      }
    });
  }
}
