/**
 * Anthropic Provider Implementation
 * LLM provider for Anthropic's Claude API
 */

import Anthropic from '@anthropic-ai/sdk';
import { ILLMProvider } from './provider';
import { LLMMessage, LLMResponse, GenerateOptions, StreamCallback } from '../types/llm';

export class AnthropicProvider implements ILLMProvider {
  readonly name = 'anthropic';
  readonly baseUrl: string;
  readonly model: string;
  private client: Anthropic;

  constructor(config: { apiKey: string; model?: string; baseUrl?: string }) {
    this.model = config.model || 'claude-3-5-sonnet-20241022';
    this.baseUrl = config.baseUrl || 'https://api.anthropic.com';

    this.client = new Anthropic({
      apiKey: config.apiKey
    });
  }

  async generate(options: GenerateOptions): Promise<LLMResponse> {
    try {
      const messages = this.convertMessages(options.messages);

      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: options.maxTokens || 4096,
        temperature: options.temperature || 0.7,
        messages
      });

      const content = response.content
        .filter((block) => block.type === 'text')
        .map((block: any) => block.text)
        .join('\n');

      return {
        content,
        model: this.model,
        usage: {
          prompt_tokens: response.usage.input_tokens,
          completion_tokens: response.usage.output_tokens,
          total_tokens: response.usage.input_tokens + response.usage.output_tokens
        }
      };
    } catch (error) {
      throw new Error(`Anthropic generation failed: ${error}`);
    }
  }

  async generateStream(options: GenerateOptions, callback: StreamCallback): Promise<void> {
    try {
      const messages = this.convertMessages(options.messages);

      const stream = await this.client.messages.create({
        model: this.model,
        max_tokens: options.maxTokens || 4096,
        temperature: options.temperature || 0.7,
        messages,
        stream: true
      });

      for await (const event of stream) {
        if (event.type === 'content_block_delta') {
          if (event.delta.type === 'text_delta') {
            callback.onChunk(event.delta.text);
          }
        }
      }

      callback.onComplete();
    } catch (error) {
      callback.onError(error instanceof Error ? error : new Error(String(error)));
    }
  }

  async testConnection(): Promise<boolean> {
    try {
      await this.client.messages.create({
        model: this.model,
        max_tokens: 10,
        messages: [{ role: 'user', content: 'test' }]
      });
      return true;
    } catch {
      return false;
    }
  }

  async listModels(): Promise<string[]> {
    // Anthropic doesn't have a list models endpoint
    return [
      'claude-3-5-sonnet-20241022',
      'claude-3-opus-20240229',
      'claude-3-sonnet-20240229',
      'claude-3-haiku-20240307'
    ];
  }

  private convertMessages(messages: LLMMessage[]): Array<{ role: string; content: string }> {
    return messages
      .filter((m) => m.role !== 'system')
      .map((m) => ({
        role: m.role,
        content: m.content
      }));
  }
}
