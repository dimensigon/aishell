/**
 * LlamaCPP Provider Implementation
 * https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md
 */

import axios, { AxiosInstance } from 'axios';
import { BaseLLMProvider } from '../provider.js';
import { LLMMessage, LLMResponse, GenerateOptions, StreamCallback } from '../../types/llm.js';

export class LlamaCppProvider extends BaseLLMProvider {
  readonly name = 'llamacpp';
  private client: AxiosInstance;

  constructor(baseUrl: string = 'http://localhost:8080', model: string = 'default', timeout: number = 30000) {
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

      const response = await this.client.post('/completion', {
        prompt: prompt,
        temperature: options.temperature ?? 0.7,
        n_predict: options.maxTokens ?? 2000,
        stop: options.stopSequences || ['User:', 'System:'],
        stream: false,
      });

      return {
        content: response.data.content.trim(),
        model: this.model,
        usage: {
          prompt_tokens: response.data.tokens_evaluated || 0,
          completion_tokens: response.data.tokens_predicted || 0,
          total_tokens: (response.data.tokens_evaluated || 0) + (response.data.tokens_predicted || 0),
        },
        finish_reason: response.data.stopped_eos ? 'stop' : 'length',
      };
    } catch (error) {
      throw this.handleError(error, 'generation');
    }
  }

  async generateStream(options: GenerateOptions, callback: StreamCallback): Promise<void> {
    try {
      const prompt = this.formatMessagesToPrompt(options.messages);

      const response = await this.client.post(
        '/completion',
        {
          prompt: prompt,
          temperature: options.temperature ?? 0.7,
          n_predict: options.maxTokens ?? 2000,
          stop: options.stopSequences || ['User:', 'System:'],
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
            try {
              const data = JSON.parse(line.substring(6));

              if (data.content) {
                fullResponse += data.content;
                callback.onChunk(data.content);
              }

              if (data.stop) {
                callback.onComplete?.(fullResponse);
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
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch (error) {
      // Fallback: try to get props endpoint
      try {
        const response = await this.client.get('/props');
        return response.status === 200;
      } catch {
        return false;
      }
    }
  }

  async listModels(): Promise<string[]> {
    // LlamaCPP typically runs a single model instance
    // Return the configured model
    return [this.model];
  }

  /**
   * Get model properties and configuration
   */
  async getModelInfo(): Promise<any> {
    try {
      const response = await this.client.get('/props');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'getting model info');
    }
  }

  /**
   * Tokenize input text
   */
  async tokenize(text: string): Promise<number[]> {
    try {
      const response = await this.client.post('/tokenize', {
        content: text,
      });
      return response.data.tokens || [];
    } catch (error) {
      throw this.handleError(error, 'tokenization');
    }
  }

  /**
   * Detokenize token IDs to text
   */
  async detokenize(tokens: number[]): Promise<string> {
    try {
      const response = await this.client.post('/detokenize', {
        tokens: tokens,
      });
      return response.data.content || '';
    } catch (error) {
      throw this.handleError(error, 'detokenization');
    }
  }
}
