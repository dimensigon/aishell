/**
 * LocalAI Provider Implementation
 * https://localai.io/basics/getting_started/
 */

import axios, { AxiosInstance } from 'axios';
import { BaseLLMProvider } from '../provider.js';
import { LLMResponse, GenerateOptions, StreamCallback } from '../../types/llm.js';

export class LocalAIProvider extends BaseLLMProvider {
  readonly name = 'localai';
  private client: AxiosInstance;

  constructor(baseUrl: string = 'http://localhost:8080', model: string = 'gpt-3.5-turbo', timeout: number = 30000) {
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
      // LocalAI supports both completions and chat endpoints
      // Use chat endpoint for better results
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
        model: response.data.model || this.model,
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
      const response = await this.client.post(
        '/v1/chat/completions',
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
            const data = line.substring(6).trim();

            if (data === '[DONE]') {
              callback.onComplete?.(fullResponse);
              return;
            }

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices?.[0]?.delta?.content || '';

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
      const response = await this.client.get('/readyz');
      return response.status === 200;
    } catch (error) {
      // Try alternative health check
      try {
        const response = await this.client.get('/v1/models');
        return response.status === 200;
      } catch {
        return false;
      }
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
   * Get embeddings from LocalAI
   */
  async createEmbedding(input: string | string[]): Promise<number[][]> {
    try {
      const response = await this.client.post('/v1/embeddings', {
        model: this.model,
        input: input,
      });

      return response.data.data?.map((item: any) => item.embedding) || [];
    } catch (error) {
      throw this.handleError(error, 'creating embeddings');
    }
  }

  /**
   * Generate images (if model supports it)
   */
  async generateImage(prompt: string, options?: {
    size?: string;
    n?: number;
  }): Promise<string[]> {
    try {
      const response = await this.client.post('/v1/images/generations', {
        model: this.model,
        prompt: prompt,
        size: options?.size || '512x512',
        n: options?.n || 1,
      });

      return response.data.data?.map((item: any) => item.url || item.b64_json) || [];
    } catch (error) {
      throw this.handleError(error, 'image generation');
    }
  }

  /**
   * Text to speech (if model supports it)
   */
  async textToSpeech(text: string, voice?: string): Promise<Buffer> {
    try {
      const response = await this.client.post(
        '/v1/audio/speech',
        {
          model: this.model,
          input: text,
          voice: voice || 'default',
        },
        {
          responseType: 'arraybuffer',
        }
      );

      return Buffer.from(response.data);
    } catch (error) {
      throw this.handleError(error, 'text to speech');
    }
  }

  /**
   * Speech to text (if model supports it)
   */
  async speechToText(audioFile: Buffer): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('file', new Blob([audioFile]));
      formData.append('model', this.model);

      const response = await this.client.post('/v1/audio/transcriptions', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data.text || '';
    } catch (error) {
      throw this.handleError(error, 'speech to text');
    }
  }

  /**
   * Get model configuration
   */
  async getModelConfig(): Promise<any> {
    try {
      const response = await this.client.get(`/models/config/${this.model}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'getting model config');
    }
  }
}
