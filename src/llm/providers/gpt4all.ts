/**
 * GPT4All Provider Implementation
 * https://docs.gpt4all.io/gpt4all_python.html
 */

import axios, { AxiosInstance } from 'axios';
import { BaseLLMProvider } from '../provider.js';
import { LLMResponse, GenerateOptions, StreamCallback } from '../../types/llm.js';

export class GPT4AllProvider extends BaseLLMProvider {
  readonly name = 'gpt4all';
  private client: AxiosInstance;

  constructor(baseUrl: string = 'http://localhost:4891', model: string = 'ggml-gpt4all-j-v1.3-groovy', timeout: number = 30000) {
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
      const prompt = this.formatMessagesToPrompt(options.messages);

      const response = await this.client.post('/v1/completions', {
        model: this.model,
        prompt: prompt,
        temperature: options.temperature ?? 0.7,
        max_tokens: options.maxTokens ?? 2000,
        stop: options.stopSequences,
        stream: false,
      });

      const choice = response.data.choices?.[0];

      return {
        content: choice?.text?.trim() || '',
        model: this.model,
        usage: {
          prompt_tokens: response.data.usage?.prompt_tokens || 0,
          completion_tokens: response.data.usage?.completion_tokens || 0,
          total_tokens: response.data.usage?.total_tokens || 0,
        },
        finish_reason: choice?.finish_reason || 'stop',
      };
    } catch (error) {
      throw this.handleError(error, 'generation');
    }
  }

  async generateStream(options: GenerateOptions, callback: StreamCallback): Promise<void> {
    try {
      const prompt = this.formatMessagesToPrompt(options.messages);

      const response = await this.client.post(
        '/v1/completions',
        {
          model: this.model,
          prompt: prompt,
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
            const data = line.substring(6).trim();

            if (data === '[DONE]') {
              callback.onComplete?.(fullResponse);
              return;
            }

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices?.[0]?.text || '';

              if (content) {
                fullResponse += content;
                callback.onChunk(content);
              }
            } catch (e) {
              // Skip invalid JSON
            }
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
      const response = await this.client.get('/v1/models');
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  async listModels(): Promise<string[]> {
    try {
      const response = await this.client.get('/v1/models');
      return response.data.data?.map((m: any) => m.id) || [];
    } catch (error) {
      throw this.handleError(error, 'listing models');
    }
  }

  /**
   * Get model information
   */
  async getModelInfo(modelName?: string): Promise<any> {
    try {
      const model = modelName || this.model;
      const response = await this.client.get(`/v1/models/${model}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'getting model info');
    }
  }

  /**
   * Chat completion (OpenAI-compatible endpoint)
   */
  async chatCompletion(options: GenerateOptions): Promise<LLMResponse> {
    try {
      const response = await this.client.post('/v1/chat/completions', {
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

      const choice = response.data.choices?.[0];

      return {
        content: choice?.message?.content || '',
        model: this.model,
        usage: {
          prompt_tokens: response.data.usage?.prompt_tokens || 0,
          completion_tokens: response.data.usage?.completion_tokens || 0,
          total_tokens: response.data.usage?.total_tokens || 0,
        },
        finish_reason: choice?.finish_reason || 'stop',
      };
    } catch (error) {
      throw this.handleError(error, 'chat completion');
    }
  }
}
