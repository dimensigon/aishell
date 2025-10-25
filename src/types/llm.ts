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

export interface LLMConfig {
  provider: 'ollama' | 'llamacpp' | 'gpt4all' | 'localai';
  baseUrl: string;
  model: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  stream?: boolean;
  timeout?: number;
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
