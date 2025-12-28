/**
 * AI-Shell MCP Integration Module
 * Exports all MCP client integration components
 */

// MCP Components
export { MCPPluginManager, PluginMetadata, PluginCapability, PluginState } from '../mcp/plugin-manager';
export { MCPToolExecutor, ToolExecutionContext, ToolExecutionResult, SecurityPolicy } from '../mcp/tool-executor';

// Core Components
export { AsyncPipeline, CommandPipeline, PipelineStage, PipelineContext, PipelineResult } from '../core/async-pipeline';
export { StateManager, StateEntry, StateSnapshot } from '../core/state-manager';
export { WorkflowOrchestrator, WorkflowDefinition, WorkflowStep, WorkflowContext } from '../core/workflow-orchestrator';
export { ErrorHandler, ErrorSeverity, ErrorCategory, ErrorEntry, RecoveryStrategy } from '../core/error-handler';

// LLM Components
export { LLMMCPBridge, BridgeContext, EnhancedGenerateOptions, EnhancedLLMResponse } from '../llm/mcp-bridge';

// MCP Types
export {
  IMCPClient,
  MCPClientConfig,
  MCPServerConfig,
  MCPTool,
  MCPResource,
  MCPContext,
  ConnectionState
} from '../mcp/types';
