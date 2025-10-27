/**
 * Workflow Orchestrator
 * Orchestrates complex multi-step workflows with MCP tools, LLM calls, and state management
 */

import { EventEmitter } from 'eventemitter3';
import { MCPToolExecutor, ToolExecutionContext } from '../mcp/tool-executor';
import { LLMMCPBridge } from '../llm/mcp-bridge';
import { StateManager } from './state-manager';

/**
 * Workflow step
 */
export interface WorkflowStep {
  id: string;
  name: string;
  type: 'tool' | 'llm' | 'custom' | 'conditional' | 'parallel';
  config: StepConfig;
  dependencies?: string[];
  retryPolicy?: RetryPolicy;
  timeout?: number;
}

/**
 * Step configuration
 */
export interface StepConfig {
  // Tool step
  tool?: string;
  params?: any;

  // LLM step
  prompt?: string;
  enableTools?: boolean;

  // Custom step
  execute?: (context: WorkflowContext) => Promise<any>;

  // Conditional step
  condition?: (context: WorkflowContext) => boolean;
  ifTrue?: string;
  ifFalse?: string;

  // Parallel step
  steps?: string[];
}

/**
 * Retry policy
 */
export interface RetryPolicy {
  maxAttempts: number;
  delayMs: number;
  backoffMultiplier?: number;
  retryOn?: Array<string | RegExp>;
}

/**
 * Workflow definition
 */
export interface WorkflowDefinition {
  id: string;
  name: string;
  description?: string;
  steps: WorkflowStep[];
  initialState?: Record<string, any>;
  timeout?: number;
}

/**
 * Workflow context
 */
export interface WorkflowContext {
  workflowId: string;
  executionId: string;
  state: StateManager;
  stepResults: Map<string, any>;
  metadata: Record<string, any>;
  abortSignal?: AbortSignal;
}

/**
 * Step execution result
 */
export interface StepExecutionResult {
  stepId: string;
  success: boolean;
  result?: any;
  error?: Error;
  duration: number;
  timestamp: number;
  attempts: number;
}

/**
 * Workflow execution result
 */
export interface WorkflowExecutionResult {
  success: boolean;
  workflowId: string;
  executionId: string;
  steps: StepExecutionResult[];
  finalState: Record<string, any>;
  duration: number;
  timestamp: number;
}

/**
 * Orchestrator events
 */
export interface OrchestratorEvents {
  workflowStart: (workflowId: string, executionId: string) => void;
  workflowComplete: (result: WorkflowExecutionResult) => void;
  workflowError: (workflowId: string, error: Error) => void;
  stepStart: (stepId: string, step: WorkflowStep) => void;
  stepComplete: (result: StepExecutionResult) => void;
  stepRetry: (stepId: string, attempt: number) => void;
  stepSkipped: (stepId: string, reason: string) => void;
}

/**
 * Workflow Orchestrator
 */
export class WorkflowOrchestrator extends EventEmitter<OrchestratorEvents> {
  private workflows = new Map<string, WorkflowDefinition>();
  private activeExecutions = new Map<string, AbortController>();

  constructor(
    private readonly toolExecutor: MCPToolExecutor,
    private readonly llmBridge: LLMMCPBridge,
    private readonly stateManager: StateManager,
    private readonly config: {
      defaultTimeout?: number;
      maxConcurrentSteps?: number;
      enablePersistence?: boolean;
    } = {}
  ) {
    super();
  }

  /**
   * Get state manager instance
   */
  getStateManager(): StateManager {
    return this.stateManager;
  }

  /**
   * Get configuration
   */
  getConfig(): typeof this.config {
    return { ...this.config };
  }

  /**
   * Register workflow
   */
  registerWorkflow(workflow: WorkflowDefinition): void {
    this.validateWorkflow(workflow);
    this.workflows.set(workflow.id, workflow);
  }

  /**
   * Execute workflow
   */
  async executeWorkflow(
    workflowId: string,
    executionContext: ToolExecutionContext,
    initialState?: Record<string, any>
  ): Promise<WorkflowExecutionResult> {
    const startTime = Date.now();
    const workflow = this.workflows.get(workflowId);

    if (!workflow) {
      throw new Error(`Workflow not found: ${workflowId}`);
    }

    const executionId = this.generateExecutionId();
    const abortController = new AbortController();
    this.activeExecutions.set(executionId, abortController);

    // Create workflow context
    const context: WorkflowContext = {
      workflowId,
      executionId,
      state: new StateManager(),
      stepResults: new Map(),
      metadata: {},
      abortSignal: abortController.signal
    };

    // Initialize state
    if (workflow.initialState) {
      Object.entries(workflow.initialState).forEach(([key, value]) => {
        context.state.set(key, value);
      });
    }

    if (initialState) {
      Object.entries(initialState).forEach(([key, value]) => {
        context.state.set(key, value);
      });
    }

    this.emit('workflowStart', workflowId, executionId);

    const stepResults: StepExecutionResult[] = [];

    try {
      // Build execution order
      const executionOrder = this.buildExecutionOrder(workflow.steps);

      // Execute steps
      for (const stepId of executionOrder) {
        // Check for abort
        if (context.abortSignal?.aborted) {
          throw new Error('Workflow execution aborted');
        }

        const step = workflow.steps.find((s) => s.id === stepId);
        if (!step) continue;

        // Check dependencies
        const dependenciesMet = this.checkDependencies(step, context);
        if (!dependenciesMet) {
          this.emit('stepSkipped', stepId, 'Dependencies not met');
          continue;
        }

        // Execute step
        const result = await this.executeStep(step, context, executionContext);
        stepResults.push(result);

        // Store result in context
        context.stepResults.set(stepId, result.result);

        // Stop if step failed and no retry succeeded
        if (!result.success) {
          throw new Error(`Step ${stepId} failed: ${result.error?.message}`);
        }
      }

      const executionResult: WorkflowExecutionResult = {
        success: true,
        workflowId,
        executionId,
        steps: stepResults,
        finalState: context.state.export() as any,
        duration: Date.now() - startTime,
        timestamp: Date.now()
      };

      this.emit('workflowComplete', executionResult);
      return executionResult;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.emit('workflowError', workflowId, err);

      return {
        success: false,
        workflowId,
        executionId,
        steps: stepResults,
        finalState: context.state.export() as any,
        duration: Date.now() - startTime,
        timestamp: Date.now()
      };
    } finally {
      this.activeExecutions.delete(executionId);
    }
  }

  /**
   * Execute a single step
   */
  private async executeStep(
    step: WorkflowStep,
    context: WorkflowContext,
    executionContext: ToolExecutionContext
  ): Promise<StepExecutionResult> {
    const startTime = Date.now();
    let attempts = 0;
    const maxAttempts = step.retryPolicy?.maxAttempts || 1;

    this.emit('stepStart', step.id, step);

    while (attempts < maxAttempts) {
      attempts++;

      try {
        let result: any;

        switch (step.type) {
          case 'tool':
            result = await this.executeToolStep(step, context, executionContext);
            break;

          case 'llm':
            result = await this.executeLLMStep(step, context);
            break;

          case 'custom':
            result = await this.executeCustomStep(step, context);
            break;

          case 'conditional':
            result = await this.executeConditionalStep(step, context);
            break;

          case 'parallel':
            result = await this.executeParallelStep(step, context, executionContext);
            break;

          default:
            throw new Error(`Unknown step type: ${step.type}`);
        }

        const executionResult: StepExecutionResult = {
          stepId: step.id,
          success: true,
          result,
          duration: Date.now() - startTime,
          timestamp: Date.now(),
          attempts
        };

        this.emit('stepComplete', executionResult);
        return executionResult;
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));

        // Check if should retry
        if (attempts < maxAttempts && this.shouldRetry(err, step.retryPolicy)) {
          this.emit('stepRetry', step.id, attempts);

          // Wait before retry with exponential backoff
          const delay = this.calculateRetryDelay(attempts, step.retryPolicy);
          await this.delay(delay);

          continue;
        }

        // Max retries reached or error not retryable
        const executionResult: StepExecutionResult = {
          stepId: step.id,
          success: false,
          error: err,
          duration: Date.now() - startTime,
          timestamp: Date.now(),
          attempts
        };

        this.emit('stepComplete', executionResult);
        return executionResult;
      }
    }

    throw new Error(`Step ${step.id} failed after ${attempts} attempts`);
  }

  /**
   * Execute tool step
   */
  private async executeToolStep(
    step: WorkflowStep,
    context: WorkflowContext,
    executionContext: ToolExecutionContext
  ): Promise<any> {
    if (!step.config.tool) {
      throw new Error('Tool name is required for tool step');
    }

    // Resolve parameters from context
    const params = this.resolveParameters(step.config.params, context);

    const result = await this.toolExecutor.execute(step.config.tool, params, executionContext);

    if (!result.success) {
      throw new Error(result.error?.message || 'Tool execution failed');
    }

    return result.result;
  }

  /**
   * Execute LLM step
   */
  private async executeLLMStep(step: WorkflowStep, context: WorkflowContext): Promise<any> {
    if (!step.config.prompt) {
      throw new Error('Prompt is required for LLM step');
    }

    // Resolve prompt from context
    const prompt = this.resolveTemplate(step.config.prompt, context);

    const response = await this.llmBridge.generate({
      messages: [{ role: 'user', content: prompt }],
      enableTools: step.config.enableTools
    });

    return response.content;
  }

  /**
   * Execute custom step
   */
  private async executeCustomStep(step: WorkflowStep, context: WorkflowContext): Promise<any> {
    if (!step.config.execute) {
      throw new Error('Execute function is required for custom step');
    }

    return await step.config.execute(context);
  }

  /**
   * Execute conditional step
   */
  private async executeConditionalStep(step: WorkflowStep, context: WorkflowContext): Promise<any> {
    if (!step.config.condition) {
      throw new Error('Condition is required for conditional step');
    }

    const conditionResult = step.config.condition(context);
    const nextStepId = conditionResult ? step.config.ifTrue : step.config.ifFalse;

    return {
      condition: conditionResult,
      nextStep: nextStepId
    };
  }

  /**
   * Execute parallel steps
   */
  private async executeParallelStep(
    step: WorkflowStep,
    context: WorkflowContext,
    executionContext: ToolExecutionContext
  ): Promise<any> {
    if (!step.config.steps || step.config.steps.length === 0) {
      throw new Error('Steps are required for parallel step');
    }

    const workflow = this.workflows.get(context.workflowId);
    if (!workflow) {
      throw new Error('Workflow not found');
    }

    const parallelSteps = step.config.steps
      .map((stepId) => workflow.steps.find((s) => s.id === stepId))
      .filter((s): s is WorkflowStep => s !== undefined);

    const results = await Promise.all(
      parallelSteps.map((s) => this.executeStep(s, context, executionContext))
    );

    return results;
  }

  /**
   * Build execution order from dependencies
   */
  private buildExecutionOrder(steps: WorkflowStep[]): string[] {
    const order: string[] = [];
    const visited = new Set<string>();
    const visiting = new Set<string>();

    const visit = (stepId: string) => {
      if (visited.has(stepId)) return;
      if (visiting.has(stepId)) {
        throw new Error(`Circular dependency detected: ${stepId}`);
      }

      visiting.add(stepId);

      const step = steps.find((s) => s.id === stepId);
      if (step && step.dependencies) {
        for (const dep of step.dependencies) {
          visit(dep);
        }
      }

      visiting.delete(stepId);
      visited.add(stepId);
      order.push(stepId);
    };

    for (const step of steps) {
      visit(step.id);
    }

    return order;
  }

  /**
   * Check if dependencies are met
   */
  private checkDependencies(step: WorkflowStep, context: WorkflowContext): boolean {
    if (!step.dependencies || step.dependencies.length === 0) {
      return true;
    }

    return step.dependencies.every((depId) => {
      const result = context.stepResults.get(depId);
      return result !== undefined;
    });
  }

  /**
   * Resolve parameters from context
   */
  private resolveParameters(params: any, context: WorkflowContext): any {
    if (typeof params === 'string') {
      return this.resolveTemplate(params, context);
    }

    if (Array.isArray(params)) {
      return params.map((p) => this.resolveParameters(p, context));
    }

    if (typeof params === 'object' && params !== null) {
      const resolved: any = {};
      for (const [key, value] of Object.entries(params)) {
        resolved[key] = this.resolveParameters(value, context);
      }
      return resolved;
    }

    return params;
  }

  /**
   * Resolve template string with context values
   */
  private resolveTemplate(template: string, context: WorkflowContext): string {
    return template.replace(/\{\{([^}]+)\}\}/g, (_, path) => {
      const value = this.getValueByPath(context, path.trim());
      return value !== undefined ? String(value) : '';
    });
  }

  /**
   * Get value by path from context
   */
  private getValueByPath(context: WorkflowContext, path: string): any {
    if (path.startsWith('state.')) {
      return context.state.get(path.substring(6));
    }

    if (path.startsWith('result.')) {
      const parts = path.substring(7).split('.');
      const stepId = parts[0];
      const result = context.stepResults.get(stepId);

      if (parts.length === 1) return result;

      let current = result;
      for (let i = 1; i < parts.length; i++) {
        current = current?.[parts[i]];
      }
      return current;
    }

    return undefined;
  }

  /**
   * Check if error should be retried
   */
  private shouldRetry(error: Error, retryPolicy?: RetryPolicy): boolean {
    if (!retryPolicy || !retryPolicy.retryOn) {
      return true;
    }

    return retryPolicy.retryOn.some((pattern) => {
      if (typeof pattern === 'string') {
        return error.message.includes(pattern);
      }
      return pattern.test(error.message);
    });
  }

  /**
   * Calculate retry delay with exponential backoff
   */
  private calculateRetryDelay(attempt: number, retryPolicy?: RetryPolicy): number {
    const baseDelay = retryPolicy?.delayMs || 1000;
    const multiplier = retryPolicy?.backoffMultiplier || 2;

    return baseDelay * Math.pow(multiplier, attempt - 1);
  }

  /**
   * Validate workflow definition
   */
  private validateWorkflow(workflow: WorkflowDefinition): void {
    if (!workflow.id) {
      throw new Error('Workflow ID is required');
    }

    if (!workflow.steps || workflow.steps.length === 0) {
      throw new Error('Workflow must have at least one step');
    }

    // Check for duplicate step IDs
    const stepIds = new Set<string>();
    for (const step of workflow.steps) {
      if (stepIds.has(step.id)) {
        throw new Error(`Duplicate step ID: ${step.id}`);
      }
      stepIds.add(step.id);
    }

    // Validate dependencies
    for (const step of workflow.steps) {
      if (step.dependencies) {
        for (const depId of step.dependencies) {
          if (!stepIds.has(depId)) {
            throw new Error(`Step ${step.id} depends on non-existent step: ${depId}`);
          }
        }
      }
    }
  }

  /**
   * Abort workflow execution
   */
  abortExecution(executionId: string): void {
    const controller = this.activeExecutions.get(executionId);
    if (controller) {
      controller.abort();
      this.activeExecutions.delete(executionId);
    }
  }

  /**
   * Get workflow definition
   */
  getWorkflow(workflowId: string): WorkflowDefinition | undefined {
    return this.workflows.get(workflowId);
  }

  /**
   * List all workflows
   */
  listWorkflows(): WorkflowDefinition[] {
    return Array.from(this.workflows.values());
  }

  /**
   * Remove workflow
   */
  removeWorkflow(workflowId: string): boolean {
    return this.workflows.delete(workflowId);
  }

  /**
   * Generate execution ID
   */
  private generateExecutionId(): string {
    return `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Get active executions count
   */
  getActiveExecutionsCount(): number {
    return this.activeExecutions.size;
  }
}
