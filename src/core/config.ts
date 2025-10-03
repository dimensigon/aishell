/**
 * Configuration management for AI-Shell
 * Handles loading, validation, and merging of configuration from multiple sources
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { ShellConfig } from '../types';

const DEFAULT_CONFIG: ShellConfig = {
  mode: 'interactive',
  historyFile: path.join(os.homedir(), '.ai-shell-history'),
  maxHistorySize: 1000,
  aiProvider: 'anthropic',
  model: 'claude-sonnet-4-5-20250929',
  timeout: 30000,
  verbose: false,
};

export class ConfigManager {
  private config: ShellConfig;
  private configPaths: string[];

  constructor() {
    this.configPaths = [
      path.join(os.homedir(), '.ai-shell.json'),
      path.join(process.cwd(), '.ai-shell.json'),
      path.join(process.cwd(), 'ai-shell.config.json'),
    ];
    this.config = { ...DEFAULT_CONFIG };
  }

  /**
   * Load configuration from files and environment variables
   */
  public async load(): Promise<ShellConfig> {
    // Load from config files
    for (const configPath of this.configPaths) {
      if (fs.existsSync(configPath)) {
        try {
          const fileConfig = JSON.parse(
            fs.readFileSync(configPath, 'utf-8')
          ) as Partial<ShellConfig>;
          this.merge(fileConfig);
        } catch (error) {
          console.warn(`Failed to load config from ${configPath}:`, error);
        }
      }
    }

    // Load from environment variables
    this.loadFromEnv();

    // Validate configuration
    this.validate();

    return this.config;
  }

  /**
   * Merge partial configuration into current config
   */
  public merge(partial: Partial<ShellConfig>): void {
    this.config = {
      ...this.config,
      ...partial,
    };
  }

  /**
   * Load configuration from environment variables
   */
  private loadFromEnv(): void {
    const envConfig: Partial<ShellConfig> = {};

    if (process.env.AI_SHELL_MODE) {
      envConfig.mode = process.env.AI_SHELL_MODE as 'interactive' | 'command';
    }

    if (process.env.AI_SHELL_PROVIDER) {
      envConfig.aiProvider = process.env.AI_SHELL_PROVIDER as
        | 'anthropic'
        | 'openai';
    }

    if (process.env.AI_SHELL_API_KEY || process.env.ANTHROPIC_API_KEY) {
      envConfig.apiKey =
        process.env.AI_SHELL_API_KEY || process.env.ANTHROPIC_API_KEY;
    }

    if (process.env.AI_SHELL_MODEL) {
      envConfig.model = process.env.AI_SHELL_MODEL;
    }

    if (process.env.AI_SHELL_TIMEOUT) {
      envConfig.timeout = parseInt(process.env.AI_SHELL_TIMEOUT, 10);
    }

    if (process.env.AI_SHELL_VERBOSE) {
      envConfig.verbose = process.env.AI_SHELL_VERBOSE === 'true';
    }

    this.merge(envConfig);
  }

  /**
   * Validate configuration
   */
  private validate(): void {
    if (!this.config.apiKey) {
      throw new Error(
        'API key is required. Set ANTHROPIC_API_KEY or AI_SHELL_API_KEY environment variable.'
      );
    }

    if (this.config.timeout < 1000) {
      throw new Error('Timeout must be at least 1000ms');
    }

    if (this.config.maxHistorySize < 1) {
      throw new Error('maxHistorySize must be at least 1');
    }

    if (!['anthropic', 'openai'].includes(this.config.aiProvider)) {
      throw new Error(
        `Invalid AI provider: ${this.config.aiProvider}. Must be 'anthropic' or 'openai'`
      );
    }
  }

  /**
   * Get current configuration
   */
  public getConfig(): ShellConfig {
    return { ...this.config };
  }

  /**
   * Update configuration value
   */
  public set<K extends keyof ShellConfig>(
    key: K,
    value: ShellConfig[K]
  ): void {
    this.config[key] = value;
    this.validate();
  }

  /**
   * Save configuration to file
   */
  public async save(configPath?: string): Promise<void> {
    const targetPath =
      configPath || path.join(os.homedir(), '.ai-shell.json');

    const configToSave = { ...this.config };
    delete configToSave.apiKey; // Never save API key to file

    fs.writeFileSync(
      targetPath,
      JSON.stringify(configToSave, null, 2),
      'utf-8'
    );
  }

  /**
   * Get default configuration
   */
  public static getDefaults(): ShellConfig {
    return { ...DEFAULT_CONFIG };
  }
}
