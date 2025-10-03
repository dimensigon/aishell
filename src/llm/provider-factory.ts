/**
 * Provider Factory - Creates and manages LLM provider instances
 */

import { ILLMProvider } from './provider.js';
import { OllamaProvider } from './providers/ollama.js';
import { LlamaCppProvider } from './providers/llamacpp.js';
import { LLMConfig } from '../types/llm.js';

export class ProviderFactory {
  private static providers: Map<string, ILLMProvider> = new Map();

  /**
   * Create an LLM provider based on configuration
   */
  static createProvider(config: LLMConfig): ILLMProvider {
    const key = `${config.provider}:${config.baseUrl}:${config.model}`;

    // Return cached provider if exists
    if (this.providers.has(key)) {
      return this.providers.get(key)!;
    }

    let provider: ILLMProvider;

    switch (config.provider) {
      case 'ollama':
        provider = new OllamaProvider(
          config.baseUrl,
          config.model,
          config.timeout
        );
        break;

      case 'llamacpp':
        provider = new LlamaCppProvider(
          config.baseUrl,
          config.model,
          config.timeout
        );
        break;

      default:
        throw new Error(`Unsupported provider: ${config.provider}`);
    }

    // Cache the provider
    this.providers.set(key, provider);
    return provider;
  }

  /**
   * Auto-detect available providers
   */
  static async detectProviders(): Promise<Array<{ provider: string; baseUrl: string; available: boolean }>> {
    const results = [];

    // Test Ollama on default port
    try {
      const ollama = new OllamaProvider('http://localhost:11434', 'llama2');
      const available = await ollama.testConnection();
      results.push({
        provider: 'ollama',
        baseUrl: 'http://localhost:11434',
        available,
      });
    } catch {
      results.push({
        provider: 'ollama',
        baseUrl: 'http://localhost:11434',
        available: false,
      });
    }

    // Test LlamaCPP on default port
    try {
      const llamacpp = new LlamaCppProvider('http://localhost:8080', 'default');
      const available = await llamacpp.testConnection();
      results.push({
        provider: 'llamacpp',
        baseUrl: 'http://localhost:8080',
        available,
      });
    } catch {
      results.push({
        provider: 'llamacpp',
        baseUrl: 'http://localhost:8080',
        available: false,
      });
    }

    return results;
  }

  /**
   * Get default configuration for a provider
   */
  static getDefaultConfig(provider: 'ollama' | 'llamacpp'): LLMConfig {
    switch (provider) {
      case 'ollama':
        return {
          provider: 'ollama',
          baseUrl: 'http://localhost:11434',
          model: 'llama2',
          temperature: 0.7,
          maxTokens: 2000,
          stream: false,
          timeout: 30000,
        };

      case 'llamacpp':
        return {
          provider: 'llamacpp',
          baseUrl: 'http://localhost:8080',
          model: 'default',
          temperature: 0.7,
          maxTokens: 2000,
          stream: false,
          timeout: 30000,
        };

      default:
        throw new Error(`Unknown provider: ${provider}`);
    }
  }

  /**
   * Clear provider cache
   */
  static clearCache(): void {
    this.providers.clear();
  }
}
