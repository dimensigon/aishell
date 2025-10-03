/**
 * Ollama Provider Implementation
 * https://github.com/ollama/ollama/blob/main/docs/api.md
 */

import axios, { AxiosInstance } from 'axios';
import { BaseLLMProvider } from '../provider.js';
import { LLMMessage, LLMResponse, GenerateOptions, StreamCallback } from '../../types/llm.js';

export class OllamaProvider extends BaseLLMProvider {
  readonly name = 'ollama';
  private client: AxiosInstance;

  constructor(baseUrl: string = 'http://localhost:11434', model: string = 'llama2', timeout: number = 30000) {
    super(baseUrl, model, timeout);
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async generate(options: GenerateOptions): Promise<LLMResponse> {
    try {
      const response = await this.client.post('/api/chat', {
        model: this.model,
        messages: options.messages.map(msg => ({
          role: msg.role,
          content: msg.content,
        })),
        stream: false,
        options: {
          temperature: options.temperature ?? 0.7,
          num_predict: options.maxTokens ?? 2000,
          stop: options.stopSequences,
        },
      });

      return {
        content: response.data.message.content,
        model: response.data.model,
        usage: {
          prompt_tokens: response.data.prompt_eval_count,
          completion_tokens: response.data.eval_count,
          total_tokens: (response.data.prompt_eval_count || 0) + (response.data.eval_count || 0),
        },
        finish_reason: response.data.done ? 'stop' : 'length',
      };
    } catch (error) {
      throw this.handleError(error, 'generation');
    }
  }

  async generateStream(options: GenerateOptions, callback: StreamCallback): Promise<void> {
    try {
      const response = await this.client.post(
        '/api/chat',
        {
          model: this.model,
          messages: options.messages.map(msg => ({
            role: msg.role,
            content: msg.content,
          })),
          stream: true,
          options: {
            temperature: options.temperature ?? 0.7,
            num_predict: options.maxTokens ?? 2000,
            stop: options.stopSequences,
          },
        },
        {
          responseType: 'stream',
        }
      );

      let fullResponse = '';

      response.data.on('data', (chunk: Buffer) => {
        const lines = chunk.toString().split('\n').filter(line => line.trim());

        for (const line of lines) {
          try {
            const data = JSON.parse(line);

            if (data.message?.content) {
              const content = data.message.content;
              fullResponse += content;
              callback.onChunk(content);
            }

            if (data.done) {
              callback.onComplete?.(fullResponse);
            }
          } catch (e) {
            // Skip invalid JSON lines
          }
        }
      });

      response.data.on('error', (error: Error) => {
        callback.onError?.(error);
      });

    } catch (error) {
      const err = this.handleError(error, 'streaming generation');
      callback.onError?.(err);
      throw err;
    }
  }

  async testConnection(): Promise<boolean> {
    try {
      const response = await this.client.get('/api/tags');
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  async listModels(): Promise<string[]> {
    try {
      const response = await this.client.get('/api/tags');
      return response.data.models?.map((m: any) => m.name) || [];
    } catch (error) {
      throw this.handleError(error, 'listing models');
    }
  }

  /**
   * Pull a model from Ollama registry
   */
  async pullModel(modelName: string): Promise<void> {
    try {
      await this.client.post('/api/pull', {
        name: modelName,
        stream: false,
      });
    } catch (error) {
      throw this.handleError(error, 'pulling model');
    }
  }

  /**
   * Delete a model from Ollama
   */
  async deleteModel(modelName: string): Promise<void> {
    try {
      await this.client.delete('/api/delete', {
        data: { name: modelName },
      });
    } catch (error) {
      throw this.handleError(error, 'deleting model');
    }
  }
}
