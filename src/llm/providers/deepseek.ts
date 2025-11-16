/**
 * DeepSeek Provider Implementation
 * https://platform.deepseek.com/api-docs/
 */

import axios, { AxiosInstance } from 'axios';
import { BaseLLMProvider } from '../provider.js';
import { LLMResponse, GenerateOptions, StreamCallback } from '../../types/llm.js';

export class DeepSeekProvider extends BaseLLMProvider {
  readonly name = 'deepseek';
  private client: AxiosInstance;
  private apiKey: string;

  constructor(
    apiKey: string = process.env.DEEPSEEK_API_KEY || '',
    model: string = 'deepseek-chat',
    baseUrl: string = 'https://api.deepseek.com/v1',
    timeout: number = 30000
  ) {
    super(baseUrl, model, timeout);
    this.apiKey = apiKey;

    if (!this.apiKey) {
      throw new Error('DeepSeek API key is required. Set DEEPSEEK_API_KEY environment variable.');
    }

    this.client = axios.create({
      baseURL: baseUrl,
      timeout: timeout,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
    });
  }

  async generate(options: GenerateOptions): Promise<LLMResponse> {
    try {
      const response = await this.client.post('/chat/completions', {
        model: this.model,
        messages: options.messages.map(msg => ({
          role: msg.role,
          content: msg.content,
        })),
        temperature: options.temperature ?? 0.7,
        max_tokens: options.maxTokens ?? 2000,
        stop: options.stopSequences,
        stream: false,
      });

      return {
        content: response.data.choices[0].message.content,
        model: response.data.model,
        usage: {
          prompt_tokens: response.data.usage?.prompt_tokens || 0,
          completion_tokens: response.data.usage?.completion_tokens || 0,
          total_tokens: response.data.usage?.total_tokens || 0,
        },
        finish_reason: response.data.choices[0].finish_reason || 'stop',
      };
    } catch (error) {
      throw this.handleError(error, 'generation');
    }
  }

  async generateStream(options: GenerateOptions, callback: StreamCallback): Promise<void> {
    try {
      const response = await this.client.post(
        '/chat/completions',
        {
          model: this.model,
          messages: options.messages.map(msg => ({
            role: msg.role,
            content: msg.content,
          })),
          temperature: options.temperature ?? 0.7,
          max_tokens: options.maxTokens ?? 2000,
          stop: options.stopSequences,
          stream: true,
        },
        {
          responseType: 'stream',
        }
      );

      let fullResponse = '';

      response.data.on('data', (chunk: Buffer) => {
        const lines = chunk.toString().split('\n').filter(line => line.trim());

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);  // Remove 'data: ' prefix

            if (data === '[DONE]') {
              callback.onComplete?.(fullResponse);
              return;
            }

            try {
              const parsed = JSON.parse(data);
              const delta = parsed.choices?.[0]?.delta?.content;

              if (delta) {
                fullResponse += delta;
                callback.onChunk(delta);
              }
            } catch (e) {
              // Skip invalid JSON lines
            }
          }
        }
      });

      response.data.on('error', (error: Error) => {
        callback.onError?.(error);
      });

      response.data.on('end', () => {
        callback.onComplete?.(fullResponse);
      });

    } catch (error) {
      const err = this.handleError(error, 'streaming generation');
      callback.onError?.(err);
      throw err;
    }
  }

  async testConnection(): Promise<boolean> {
    try {
      // DeepSeek doesn't have a /models endpoint, so we'll try a minimal generation
      const response = await this.client.post('/chat/completions', {
        model: this.model,
        messages: [{ role: 'user', content: 'test' }],
        max_tokens: 1,
      });
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  async listModels(): Promise<string[]> {
    // DeepSeek currently supports these models
    return ['deepseek-chat', 'deepseek-coder'];
  }
}
