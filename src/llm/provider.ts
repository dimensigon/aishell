/**
 * LLM Provider Interface - Abstract base for all LLM integrations
 * Supports Ollama, LlamaCPP, and future providers
 */

import { LLMMessage, LLMResponse, GenerateOptions, StreamCallback } from '../types/llm.js';

export interface ILLMProvider {
  /**
   * Provider name
   */
  readonly name: string;

  /**
   * Base URL for the provider API
   */
  readonly baseUrl: string;

  /**
   * Model identifier
   */
  readonly model: string;

  /**
   * Generate a response from the LLM
   * @param options - Generation options including messages and parameters
   * @returns Promise with the complete response
   */
  generate(options: GenerateOptions): Promise<LLMResponse>;

  /**
   * Generate a streaming response from the LLM
   * @param options - Generation options including messages and parameters
   * @param callback - Callback handlers for stream events
   */
  generateStream(options: GenerateOptions, callback: StreamCallback): Promise<void>;

  /**
   * Test connection to the provider
   * @returns Promise<boolean> indicating if connection is successful
   */
  testConnection(): Promise<boolean>;

  /**
   * List available models from the provider
   * @returns Promise with array of model names
   */
  listModels(): Promise<string[]>;
}

/**
 * Base abstract class implementing common provider functionality
 */
export abstract class BaseLLMProvider implements ILLMProvider {
  abstract readonly name: string;

  constructor(
    public readonly baseUrl: string,
    public readonly model: string,
    protected readonly timeout: number = 30000
  ) {}

  abstract generate(options: GenerateOptions): Promise<LLMResponse>;
  abstract generateStream(options: GenerateOptions, callback: StreamCallback): Promise<void>;
  abstract testConnection(): Promise<boolean>;
  abstract listModels(): Promise<string[]>;

  /**
   * Format messages into a single prompt string
   */
  protected formatMessagesToPrompt(messages: LLMMessage[]): string {
    return messages
      .map(msg => {
        switch (msg.role) {
          case 'system':
            return `System: ${msg.content}`;
          case 'user':
            return `User: ${msg.content}`;
          case 'assistant':
            return `Assistant: ${msg.content}`;
          default:
            return msg.content;
        }
      })
      .join('\n\n');
  }

  /**
   * Handle HTTP errors consistently
   */
  protected handleError(error: any, context: string): Error {
    if (error.response) {
      return new Error(
        `${this.name} ${context} failed: ${error.response.status} - ${error.response.data?.error || error.message}`
      );
    } else if (error.request) {
      return new Error(
        `${this.name} ${context} failed: No response from ${this.baseUrl}`
      );
    }
    return new Error(`${this.name} ${context} failed: ${error.message}`);
  }
}
