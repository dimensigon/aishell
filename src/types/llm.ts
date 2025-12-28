/**
 * Core LLM type definitions for AI-Shell
 */

export interface LLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface LLMStreamChunk {
  content: string;
  done: boolean;
  model?: string;
  created_at?: string;
}

export interface LLMResponse {
  content: string;
  model: string;
  usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
  finish_reason?: string;
}

export type LLMProvider = 'ollama' | 'llamacpp' | 'openai' | 'anthropic' | 'deepseek';

export interface LLMConfig {
  provider: LLMProvider;
  baseUrl: string;
  model: string;
  apiKey?: string;  // For public API providers
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  stream?: boolean;
  timeout?: number;
}

export interface FunctionProviderConfig {
  provider: LLMProvider;
  model: string;
  apiKey?: string;
  baseUrl?: string;
}

export interface DualModeConfig {
  intent?: FunctionProviderConfig;
  completion?: FunctionProviderConfig;
  anonymizer?: FunctionProviderConfig;
}

export interface StreamCallback {
  onChunk: (chunk: string) => void;
  onComplete?: (fullResponse: string) => void;
  onError?: (error: Error) => void;
}

export interface GenerateOptions {
  messages: LLMMessage[];
  stream?: boolean;
  temperature?: number;
  maxTokens?: number;
  stopSequences?: string[];
}
