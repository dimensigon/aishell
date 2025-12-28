/**
 * LLM Integration Layer - Main exports
 */

export { ILLMProvider, BaseLLMProvider } from './provider.js';
export { OllamaProvider } from './providers/ollama.js';
export { LlamaCppProvider } from './providers/llamacpp.js';
export { ContextFormatter, type ContextOptions } from './context-formatter.js';
export { ResponseParser, type ParsedResponse, type CodeBlock, type TableData } from './response-parser.js';
export { ProviderFactory } from './provider-factory.js';

// Re-export types
export type {
  LLMMessage,
  LLMStreamChunk,
  LLMResponse,
  LLMConfig,
  StreamCallback,
  GenerateOptions,
} from '../types/llm.js';
