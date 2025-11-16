/**
 * OpenAI Provider Implementation
 * https://platform.openai.com/docs/api-reference
 */

import axios, { AxiosInstance } from 'axios';
import { BaseLLMProvider } from '../provider.js';
import { LLMResponse, GenerateOptions, StreamCallback } from '../../types/llm.js';

export class OpenAIProvider extends BaseLLMProvider {
  readonly name = 'openai';
  private client: AxiosInstance;
  private apiKey: string;

  constructor(
    apiKey: string = process.env.OPENAI_API_KEY || '',
    model: string = 'gpt-3.5-turbo',
    baseUrl: string = 'https://api.openai.com/v1',
    timeout: number = 30000
  ) {
    super(baseUrl, model, timeout);
    this.apiKey = apiKey;

    if (!this.apiKey) {
      throw new Error('OpenAI API key is required. Set OPENAI_API_KEY environment variable.');
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
      const response = await this.client.get('/models');
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  async listModels(): Promise<string[]> {
    try {
      const response = await this.client.get('/models');
      return response.data.data?.map((m: any) => m.id) || [];
    } catch (error) {
      throw this.handleError(error, 'listing models');
    }
  }
}
