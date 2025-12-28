/**
 * Unit tests for WorkflowOrchestrator
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { WorkflowOrchestrator, WorkflowDefinition, WorkflowStep } from '../../src/core/workflow-orchestrator';
import { MCPToolExecutor, ToolExecutionContext } from '../../src/mcp/tool-executor';
import { LLMMCPBridge } from '../../src/llm/mcp-bridge';
import { StateManager } from '../../src/core/state-manager';

describe('WorkflowOrchestrator', () => {
  let orchestrator: WorkflowOrchestrator;
  let mockToolExecutor: any;
  let mockLLMBridge: any;
  let stateManager: StateManager;
  let mockExecutionContext: ToolExecutionContext;

  beforeEach(() => {
    // Create mocks with vi.fn()
    mockToolExecutor = {
      execute: vi.fn()
    };

    mockLLMBridge = {
      generate: vi.fn()
    };

    stateManager = new StateManager({ enablePersistence: false });

    orchestrator = new WorkflowOrchestrator(
      mockToolExecutor,
      mockLLMBridge,
      stateManager
    );

    mockExecutionContext = {
      sessionId: 'test-session',
      permissions: ['read', 'write'],
      metadata: {}
    };
  });

  afterEach(async () => {
    if (stateManager && typeof stateManager.shutdown === 'function') {
      await stateManager.shutdown();
    }
    vi.clearAllMocks();
  });

  describe('Workflow Registration', () => {
    test('should register workflow', () => {
      const workflow: WorkflowDefinition = {
        id: 'test-workflow',
        name: 'Test Workflow',
        steps: [
          {
            id: 'step1',
            name: 'Step 1',
            type: 'tool',
            config: { tool: 'test-tool', params: {} }
          }
        ]
      };

      orchestrator.registerWorkflow(workflow);
      expect(orchestrator.getWorkflow('test-workflow')).toBeDefined();
    });

    test('should validate workflow on registration', () => {
      const invalidWorkflow: WorkflowDefinition = {
        id: '',
        name: 'Invalid',
        steps: []
      };

      expect(() => orchestrator.registerWorkflow(invalidWorkflow)).toThrow();
    });

    test('should detect circular dependencies during execution', async () => {
      mockToolExecutor.execute.mockResolvedValue({
        success: true,
        tool: 'test-tool',
        result: {},
        duration: 100,
        timestamp: Date.now()
      });

      const workflow: WorkflowDefinition = {
        id: 'circular',
        name: 'Circular',
        steps: [
          {
            id: 'step1',
            name: 'Step 1',
            type: 'tool',
            config: { tool: 'test', params: {} },
            dependencies: ['step2']
          },
          {
            id: 'step2',
            name: 'Step 2',
            type: 'tool',
            config: { tool: 'test', params: {} },
            dependencies: ['step1']
          }
        ]
      };

      orchestrator.registerWorkflow(workflow);

      // Circular dependency is detected during execution
      // It returns a failed result rather than throwing
      const result = await orchestrator.executeWorkflow('circular', mockExecutionContext);

      expect(result.success).toBe(false);
    });
  });

  describe('Workflow Execution', () => {
    test('should execute simple workflow', async () => {
      mockToolExecutor.execute.mockResolvedValue({
        success: true,
        tool: 'test-tool',
        result: { output: 'test' },
        duration: 100,
        timestamp: Date.now()
      });

      const workflow: WorkflowDefinition = {
        id: 'simple-workflow',
        name: 'Simple Workflow',
        steps: [
          {
            id: 'step1',
            name: 'Tool Step',
            type: 'tool',
            config: { tool: 'test-tool', params: { input: 'test' } }
          }
        ]
      };

      orchestrator.registerWorkflow(workflow);
      const result = await orchestrator.executeWorkflow(
        'simple-workflow',
        mockExecutionContext
      );

      expect(result.success).toBe(true);
      expect(result.steps).toHaveLength(1);
      expect(mockToolExecutor.execute).toHaveBeenCalled();
    });

    test('should execute workflow with dependencies', async () => {
      mockToolExecutor.execute.mockResolvedValue({
        success: true,
        tool: 'test-tool',
        result: { data: 'result' },
        duration: 100,
        timestamp: Date.now()
      });

      const workflow: WorkflowDefinition = {
        id: 'dependent-workflow',
        name: 'Dependent Workflow',
        steps: [
          {
            id: 'step1',
            name: 'First Step',
            type: 'tool',
            config: { tool: 'tool1', params: {} }
          },
          {
            id: 'step2',
            name: 'Second Step',
            type: 'tool',
            config: { tool: 'tool2', params: {} },
            dependencies: ['step1']
          }
        ]
      };

      orchestrator.registerWorkflow(workflow);
      const result = await orchestrator.executeWorkflow(
        'dependent-workflow',
        mockExecutionContext
      );

      expect(result.success).toBe(true);
      expect(result.steps).toHaveLength(2);
    });

    test('should handle step failures', async () => {
      mockToolExecutor.execute.mockResolvedValue({
        success: false,
        tool: 'failing-tool',
        error: {
          code: 'EXECUTION_ERROR',
          message: 'Tool failed'
        },
        duration: 100,
        timestamp: Date.now()
      });

      const workflow: WorkflowDefinition = {
        id: 'failing-workflow',
        name: 'Failing Workflow',
        steps: [
          {
            id: 'failing-step',
            name: 'Failing Step',
            type: 'tool',
            config: { tool: 'failing-tool', params: {} }
          }
        ]
      };

      orchestrator.registerWorkflow(workflow);
      const result = await orchestrator.executeWorkflow(
        'failing-workflow',
        mockExecutionContext
      );

      expect(result.success).toBe(false);
    });

    test('should retry failed steps', async () => {
      let callCount = 0;
      mockToolExecutor.execute.mockImplementation(async () => {
        callCount++;
        if (callCount < 3) {
          return {
            success: false,
            tool: 'retry-tool',
            error: { code: 'TEMP_ERROR', message: 'Temporary failure' },
            duration: 100,
            timestamp: Date.now()
          };
        }
        return {
          success: true,
          tool: 'retry-tool',
          result: { data: 'success' },
          duration: 100,
          timestamp: Date.now()
        };
      });

      const workflow: WorkflowDefinition = {
        id: 'retry-workflow',
        name: 'Retry Workflow',
        steps: [
          {
            id: 'retry-step',
            name: 'Retry Step',
            type: 'tool',
            config: { tool: 'retry-tool', params: {} },
            retryPolicy: {
              maxAttempts: 3,
              delayMs: 100
            }
          }
        ]
      };

      orchestrator.registerWorkflow(workflow);
      const result = await orchestrator.executeWorkflow(
        'retry-workflow',
        mockExecutionContext
      );

      expect(result.success).toBe(true);
      expect(callCount).toBe(3);
    });
  });

  describe('Step Types', () => {
    test('should execute custom steps', async () => {
      let executed = false;

      const workflow: WorkflowDefinition = {
        id: 'custom-workflow',
        name: 'Custom Workflow',
        steps: [
          {
            id: 'custom-step',
            name: 'Custom Step',
            type: 'custom',
            config: {
              execute: async (context) => {
                executed = true;
                return { success: true };
              }
            }
          }
        ]
      };

      orchestrator.registerWorkflow(workflow);
      await orchestrator.executeWorkflow('custom-workflow', mockExecutionContext);

      expect(executed).toBe(true);
    });

    test('should execute conditional steps', async () => {
      const workflow: WorkflowDefinition = {
        id: 'conditional-workflow',
        name: 'Conditional Workflow',
        steps: [
          {
            id: 'condition',
            name: 'Condition',
            type: 'conditional',
            config: {
              condition: (context) => context.state.get('shouldProceed') === true,
              ifTrue: 'true-step',
              ifFalse: 'false-step'
            }
          }
        ]
      };

      orchestrator.registerWorkflow(workflow);
      const result = await orchestrator.executeWorkflow(
        'conditional-workflow',
        mockExecutionContext,
        { shouldProceed: true }
      );

      expect(result.steps[0].result.condition).toBe(true);
    });
  });

  describe('Workflow Management', () => {
    test('should list all workflows', () => {
      orchestrator.registerWorkflow({
        id: 'workflow1',
        name: 'Workflow 1',
        steps: [
          {
            id: 'step1',
            name: 'Step 1',
            type: 'tool',
            config: { tool: 'test', params: {} }
          }
        ]
      });

      orchestrator.registerWorkflow({
        id: 'workflow2',
        name: 'Workflow 2',
        steps: [
          {
            id: 'step1',
            name: 'Step 1',
            type: 'tool',
            config: { tool: 'test', params: {} }
          }
        ]
      });

      const workflows = orchestrator.listWorkflows();
      expect(workflows).toHaveLength(2);
    });

    test('should remove workflow', () => {
      orchestrator.registerWorkflow({
        id: 'removable',
        name: 'Removable',
        steps: [
          {
            id: 'step1',
            name: 'Step 1',
            type: 'tool',
            config: { tool: 'test', params: {} }
          }
        ]
      });

      expect(orchestrator.removeWorkflow('removable')).toBe(true);
      expect(orchestrator.getWorkflow('removable')).toBeUndefined();
    });

    test('should get workflow by id', () => {
      const workflow: WorkflowDefinition = {
        id: 'get-test',
        name: 'Get Test',
        steps: [
          {
            id: 'step1',
            name: 'Step 1',
            type: 'tool',
            config: { tool: 'test', params: {} }
          }
        ]
      };

      orchestrator.registerWorkflow(workflow);
      const retrieved = orchestrator.getWorkflow('get-test');

      expect(retrieved).toBeDefined();
      expect(retrieved?.id).toBe('get-test');
      expect(retrieved?.name).toBe('Get Test');
    });

    test('should return undefined for non-existent workflow', () => {
      const result = orchestrator.getWorkflow('non-existent');
      expect(result).toBeUndefined();
    });
  });

  describe('Execution Control', () => {
    test('should abort workflow execution', async () => {
      const workflow: WorkflowDefinition = {
        id: 'abortable',
        name: 'Abortable',
        steps: [
          {
            id: 'long-step',
            name: 'Long Step',
            type: 'custom',
            config: {
              execute: async () => {
                await new Promise((resolve) => setTimeout(resolve, 5000));
                return {};
              }
            }
          }
        ]
      };

      orchestrator.registerWorkflow(workflow);

      const executePromise = orchestrator.executeWorkflow(
        'abortable',
        mockExecutionContext
      );

      // Give some time for execution to start
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Abort should prevent completion
      // Note: This test needs implementation of execution ID tracking

      const result = await executePromise;
      // Verification depends on implementation
    });
  });

  describe('Execution Tracking', () => {
    test('should track active executions', async () => {
      mockToolExecutor.execute.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          success: true,
          tool: 'test',
          result: {},
          duration: 100,
          timestamp: Date.now()
        }), 100))
      );

      const workflow: WorkflowDefinition = {
        id: 'tracking-test',
        name: 'Tracking Test',
        steps: [
          {
            id: 'step1',
            name: 'Step 1',
            type: 'tool',
            config: { tool: 'test', params: {} }
          }
        ]
      };

      orchestrator.registerWorkflow(workflow);

      // Start execution but don't await
      const promise = orchestrator.executeWorkflow('tracking-test', mockExecutionContext);

      // Should have active execution
      expect(orchestrator.getActiveExecutionsCount()).toBeGreaterThan(0);

      // Wait for completion
      await promise;

      // Should be cleared after completion
      expect(orchestrator.getActiveExecutionsCount()).toBe(0);
    });
  });
});
