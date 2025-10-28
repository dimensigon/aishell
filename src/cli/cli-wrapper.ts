/**
 * CLI Wrapper Framework
 * Bridges the gap between REPL-only commands and standalone CLI commands
 *
 * Features:
 * - Command routing and execution
 * - Flexible output formatting (JSON, table, CSV)
 * - Global flags support (--format, --json, --verbose, --explain, --dry-run)
 * - Environment variable integration
 * - Piping support for command chaining
 * - Comprehensive error handling
 */

import { FeatureCommands } from './feature-commands';
import { createLogger, Logger, LogLevel } from '../core/logger';
import { StateManager } from '../core/state-manager';
import chalk from 'chalk';
import Table from 'cli-table3';
import { PassThrough } from 'stream';

/**
 * CLI Options interface for global flags
 */
export interface CLIOptions {
  /** Output format (json, table, csv) */
  format?: 'json' | 'table' | 'csv';

  /** Enable verbose logging */
  verbose?: boolean;

  /** Show AI explanation of what will happen */
  explain?: boolean;

  /** Simulate without making changes */
  dryRun?: boolean;

  /** Database connection URL or name */
  database?: string;

  /** Limit results count */
  limit?: number;

  /** Output to file instead of stdout */
  output?: string;

  /** Enable raw mode (no formatting) */
  raw?: boolean;

  /** Timeout in milliseconds */
  timeout?: number;

  /** Show timestamps in output */
  timestamps?: boolean;
}

/**
 * Command result interface
 */
export interface CommandResult {
  /** Command execution success status */
  success: boolean;

  /** Result data */
  data?: any;

  /** Error information if failed */
  error?: Error | string;

  /** Execution duration in milliseconds */
  duration?: number;

  /** Metadata about the command execution */
  metadata?: {
    command: string;
    args: string[];
    timestamp: Date;
    [key: string]: any;
  };

  /** Warning messages */
  warnings?: string[];

  /** Info messages */
  info?: string[];
}

/**
 * Command context for passing execution state
 */
export interface CommandContext {
  /** Current working database */
  database?: string;

  /** User ID if authenticated */
  userId?: string;

  /** Request ID for tracking */
  requestId: string;

  /** Environment variables */
  env: Record<string, string>;

  /** Previous command results (for piping) */
  previousResult?: CommandResult;
}

/**
 * Command handler function type
 */
export type CommandHandler = (
  args: string[],
  options: CLIOptions,
  context: CommandContext
) => Promise<CommandResult>;

/**
 * Command registry entry
 */
interface CommandRegistration {
  /** Command name */
  name: string;

  /** Command aliases */
  aliases: string[];

  /** Command handler function */
  handler: CommandHandler;

  /** Command description */
  description: string;

  /** Required arguments count */
  requiredArgs?: number;

  /** Whether command modifies data */
  mutates?: boolean;
}

/**
 * CLI Wrapper class - main command execution framework
 */
export class CLIWrapper {
  private features: FeatureCommands;
  private logger: Logger;
  private stateManager: StateManager;
  private commandRegistry: Map<string, CommandRegistration>;
  private aliasMap: Map<string, string>;

  constructor() {
    this.features = new FeatureCommands();
    this.logger = createLogger('CLIWrapper');
    this.stateManager = new StateManager();
    this.commandRegistry = new Map();
    this.aliasMap = new Map();

    // Register all available commands
    this.registerCommands();
  }

  /**
   * Register all available CLI commands
   */
  private registerCommands(): void {
    // Query optimization commands
    this.registerCommand({
      name: 'optimize',
      aliases: ['opt'],
      description: 'Optimize SQL query using AI',
      requiredArgs: 1,
      handler: this.handleOptimize.bind(this)
    });

    this.registerCommand({
      name: 'analyze-slow-queries',
      aliases: ['slow'],
      description: 'Analyze slow queries from log',
      handler: this.handleAnalyzeSlowQueries.bind(this)
    });

    // Health monitoring commands
    this.registerCommand({
      name: 'health-check',
      aliases: ['health'],
      description: 'Perform database health check',
      handler: this.handleHealthCheck.bind(this)
    });

    this.registerCommand({
      name: 'monitor',
      aliases: ['mon'],
      description: 'Start real-time monitoring',
      handler: this.handleMonitor.bind(this)
    });

    // Backup commands
    this.registerCommand({
      name: 'backup',
      aliases: ['bak'],
      description: 'Create database backup',
      handler: this.handleBackup.bind(this),
      mutates: true
    });

    this.registerCommand({
      name: 'restore',
      aliases: ['res'],
      description: 'Restore from backup',
      requiredArgs: 1,
      handler: this.handleRestore.bind(this),
      mutates: true
    });

    this.registerCommand({
      name: 'backup-list',
      aliases: ['backups'],
      description: 'List all backups',
      handler: this.handleBackupList.bind(this)
    });

    // Federation commands
    this.registerCommand({
      name: 'federate',
      aliases: ['fed'],
      description: 'Execute federated query',
      requiredArgs: 1,
      handler: this.handleFederate.bind(this)
    });

    // Schema commands
    this.registerCommand({
      name: 'design-schema',
      aliases: ['design'],
      description: 'Interactive schema design',
      handler: this.handleDesignSchema.bind(this)
    });

    this.registerCommand({
      name: 'validate-schema',
      aliases: ['validate'],
      description: 'Validate schema file',
      requiredArgs: 1,
      handler: this.handleValidateSchema.bind(this)
    });

    this.registerCommand({
      name: 'diff',
      aliases: ['schema-diff'],
      description: 'Compare schemas',
      requiredArgs: 2,
      handler: this.handleSchemaDiff.bind(this)
    });

    // Cache commands
    this.registerCommand({
      name: 'cache-enable',
      aliases: ['cache-on'],
      description: 'Enable query caching',
      handler: this.handleCacheEnable.bind(this)
    });

    this.registerCommand({
      name: 'cache-stats',
      aliases: ['cache-info'],
      description: 'Show cache statistics',
      handler: this.handleCacheStats.bind(this)
    });

    this.registerCommand({
      name: 'cache-clear',
      aliases: ['cache-flush'],
      description: 'Clear query cache',
      handler: this.handleCacheClear.bind(this),
      mutates: true
    });

    // Migration commands
    this.registerCommand({
      name: 'test-migration',
      aliases: ['test-mig'],
      description: 'Test migration file',
      requiredArgs: 1,
      handler: this.handleTestMigration.bind(this)
    });

    // SQL explainer commands
    this.registerCommand({
      name: 'explain',
      aliases: ['exp'],
      description: 'Explain SQL query',
      requiredArgs: 1,
      handler: this.handleExplain.bind(this)
    });

    this.registerCommand({
      name: 'translate',
      aliases: ['nl2sql'],
      description: 'Translate natural language to SQL',
      requiredArgs: 1,
      handler: this.handleTranslate.bind(this)
    });

    // Cost optimization commands
    this.registerCommand({
      name: 'analyze-costs',
      aliases: ['costs'],
      description: 'Analyze database costs',
      requiredArgs: 2,
      handler: this.handleAnalyzeCosts.bind(this)
    });
  }

  /**
   * Register a command with the CLI wrapper
   */
  private registerCommand(registration: CommandRegistration): void {
    this.commandRegistry.set(registration.name, registration);

    // Register aliases
    for (const alias of registration.aliases) {
      this.aliasMap.set(alias, registration.name);
    }
  }

  /**
   * Execute a command with given arguments and options
   */
  async executeCommand(
    command: string,
    args: string[],
    options: CLIOptions = {}
  ): Promise<CommandResult> {
    const startTime = Date.now();
    const requestId = this.generateRequestId();

    try {
      // Setup logging based on options
      if (options.verbose) {
        this.logger.setLevel(LogLevel.DEBUG);
        this.logger.debug('Verbose mode enabled');
      }

      // Create execution context
      const context = this.createContext(requestId, options);

      // Resolve command (handle aliases)
      const resolvedCommand = this.resolveCommand(command);
      if (!resolvedCommand) {
        throw new Error(`Unknown command: ${command}`);
      }

      // Get command registration
      const registration = this.commandRegistry.get(resolvedCommand);
      if (!registration) {
        throw new Error(`Command not registered: ${resolvedCommand}`);
      }

      // Validate arguments
      if (registration.requiredArgs && args.length < registration.requiredArgs) {
        throw new Error(
          `Command '${command}' requires ${registration.requiredArgs} argument(s), got ${args.length}`
        );
      }

      // Show explanation if requested
      if (options.explain) {
        await this.explainCommand(resolvedCommand, args, options);
        if (options.dryRun) {
          return {
            success: true,
            data: { explained: true, dryRun: true },
            duration: Date.now() - startTime,
            metadata: {
              command: resolvedCommand,
              args,
              timestamp: new Date()
            }
          };
        }
      }

      // Check for dry-run mode with mutating commands
      if (options.dryRun && registration.mutates) {
        this.logger.info('Dry-run mode: Simulating command without changes');
        console.log(chalk.yellow(`\n[DRY RUN] Would execute: ${resolvedCommand} ${args.join(' ')}\n`));
        return {
          success: true,
          data: { simulated: true },
          duration: Date.now() - startTime,
          warnings: ['Command not executed (dry-run mode)'],
          metadata: {
            command: resolvedCommand,
            args,
            timestamp: new Date()
          }
        };
      }

      // Execute the command
      this.logger.info('Executing command', {
        command: resolvedCommand,
        args,
        options,
        requestId
      });

      const result = await this.executeWithTimeout(
        () => registration.handler(args, options, context),
        options.timeout || 300000 // 5 minutes default
      );

      // Log execution time
      const duration = Date.now() - startTime;
      this.logger.info('Command completed', {
        command: resolvedCommand,
        duration,
        success: result.success,
        requestId
      });

      result.duration = duration;
      result.metadata = {
        command: resolvedCommand,
        args,
        timestamp: new Date(),
        requestId
      };

      // Format and output result
      await this.outputResult(result, options);

      return result;

    } catch (error) {
      const duration = Date.now() - startTime;
      this.logger.error('Command execution failed', error, {
        command,
        args,
        duration,
        requestId
      });

      const result: CommandResult = {
        success: false,
        error: error instanceof Error ? error : String(error),
        duration,
        metadata: {
          command,
          args,
          timestamp: new Date(),
          requestId
        }
      };

      await this.outputResult(result, options);
      return result;
    }
  }

  /**
   * Resolve command name (handle aliases)
   */
  private resolveCommand(command: string): string | undefined {
    return this.aliasMap.get(command) || (this.commandRegistry.has(command) ? command : undefined);
  }

  /**
   * Create execution context
   */
  private createContext(requestId: string, options: CLIOptions): CommandContext {
    return {
      requestId,
      database: options.database || process.env.DATABASE_URL,
      env: {
        DATABASE_URL: process.env.DATABASE_URL || '',
        ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || '',
        REDIS_URL: process.env.REDIS_URL || '',
        ...process.env
      }
    };
  }

  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Execute command with timeout
   */
  private async executeWithTimeout<T>(
    fn: () => Promise<T>,
    timeout: number
  ): Promise<T> {
    return Promise.race([
      fn(),
      new Promise<T>((_, reject) =>
        setTimeout(() => reject(new Error(`Command timeout after ${timeout}ms`)), timeout)
      )
    ]);
  }

  /**
   * Explain what a command will do
   */
  private async explainCommand(
    command: string,
    args: string[],
    options: CLIOptions
  ): Promise<void> {
    const registration = this.commandRegistry.get(command);
    if (!registration) return;

    console.log(chalk.cyan.bold('\n🤖 AI Explanation:\n'));
    console.log(chalk.bold('Command:'), command);
    console.log(chalk.bold('Description:'), registration.description);

    if (args.length > 0) {
      console.log(chalk.bold('Arguments:'), args.join(', '));
    }

    if (registration.mutates) {
      console.log(chalk.yellow.bold('\n⚠️  WARNING: This command will modify data'));
    }

    if (options.dryRun) {
      console.log(chalk.green('\n✓ Dry-run mode enabled - no changes will be made'));
    }

    console.log('');
  }

  /**
   * Format and output command result
   */
  private async outputResult(result: CommandResult, options: CLIOptions): Promise<void> {
    // Handle output file
    if (options.output) {
      await this.writeToFile(result, options);
      return;
    }

    // Handle error results
    if (!result.success) {
      console.error(chalk.red('\n❌ Command failed:'));
      console.error(chalk.red(result.error instanceof Error ? result.error.message : String(result.error)));
      if (result.error instanceof Error && result.error.stack && options.verbose) {
        console.error(chalk.dim(result.error.stack));
      }
      return;
    }

    // Handle success results
    if (!result.data) return;

    // Choose format
    const format = options.format || (options.raw ? 'raw' : 'table');

    // Add timestamps if requested
    if (options.timestamps && result.metadata) {
      console.log(chalk.dim(`[${result.metadata.timestamp.toISOString()}]`));
    }

    // Format output
    const formatted = this.formatOutput(result.data, format, options);
    console.log(formatted);

    // Show warnings
    if (result.warnings && result.warnings.length > 0) {
      console.log(chalk.yellow('\n⚠️  Warnings:'));
      result.warnings.forEach(w => console.log(chalk.yellow(`  • ${w}`)));
    }

    // Show info messages
    if (result.info && result.info.length > 0) {
      console.log(chalk.blue('\nℹ️  Info:'));
      result.info.forEach(i => console.log(chalk.blue(`  • ${i}`)));
    }

    // Show duration if verbose
    if (options.verbose && result.duration) {
      console.log(chalk.dim(`\nCompleted in ${result.duration}ms`));
    }
  }

  /**
   * Format output data based on format type
   */
  private formatOutput(data: any, format: string, options: CLIOptions): string {
    switch (format) {
      case 'json':
        return this.formatJSON(data, options);
      case 'table':
        return this.formatTable(data, options);
      case 'csv':
        return this.formatCSV(data, options);
      case 'raw':
        return this.formatRaw(data);
      default:
        return this.formatTable(data, options);
    }
  }

  /**
   * Format as JSON
   */
  private formatJSON(data: any, options: CLIOptions): string {
    const indent = options.verbose ? 2 : 0;
    return JSON.stringify(data, null, indent);
  }

  /**
   * Format as table
   */
  private formatTable(data: any, options: CLIOptions): string {
    if (Array.isArray(data) && data.length > 0) {
      const keys = Object.keys(data[0]);
      const table = new Table({
        head: keys.map(k => chalk.bold(k)),
        style: { head: ['cyan'] }
      });

      const limit = options.limit || data.length;
      data.slice(0, limit).forEach(row => {
        table.push(keys.map(k => String(row[k] || '')));
      });

      return table.toString();
    }

    if (typeof data === 'object' && data !== null) {
      const table = new Table({
        style: { head: ['cyan'] }
      });

      Object.entries(data).forEach(([key, value]) => {
        table.push({ [chalk.bold(key)]: String(value) });
      });

      return table.toString();
    }

    return String(data);
  }

  /**
   * Format as CSV
   */
  private formatCSV(data: any, options: CLIOptions): string {
    if (Array.isArray(data) && data.length > 0) {
      const keys = Object.keys(data[0]);
      const rows: string[] = [keys.join(',')];

      const limit = options.limit || data.length;
      data.slice(0, limit).forEach(row => {
        const values = keys.map(k => {
          const value = row[k];
          const str = String(value || '');
          return str.includes(',') ? `"${str}"` : str;
        });
        rows.push(values.join(','));
      });

      return rows.join('\n');
    }

    return String(data);
  }

  /**
   * Format as raw text
   */
  private formatRaw(data: any): string {
    return String(data);
  }

  /**
   * Write result to file
   */
  private async writeToFile(result: CommandResult, options: CLIOptions): Promise<void> {
    const fs = await import('fs/promises');
    const content = this.formatOutput(result.data, options.format || 'json', options);
    await fs.writeFile(options.output!, content, 'utf-8');
    console.log(chalk.green(`✓ Output written to ${options.output}`));
  }

  // ============================================================================
  // COMMAND HANDLERS
  // ============================================================================

  private async handleOptimize(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    const query = args[0];
    await this.features.optimizeQuery(query);
    return { success: true };
  }

  private async handleAnalyzeSlowQueries(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.analyzeSlowQueries();
    return { success: true };
  }

  private async handleHealthCheck(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.healthCheck();
    return { success: true };
  }

  private async handleMonitor(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    const interval = parseInt(args[0] || '5000');
    await this.features.startMonitoring(interval);
    return { success: true };
  }

  private async handleBackup(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.createBackup(options.database);
    return { success: true };
  }

  private async handleRestore(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.restoreBackup(args[0], options.dryRun || false);
    return { success: true };
  }

  private async handleBackupList(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.listBackups();
    return { success: true };
  }

  private async handleFederate(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    const query = args[0];
    const databases = args.slice(1);
    await this.features.federateQuery(query, databases);
    return { success: true };
  }

  private async handleDesignSchema(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.designSchema();
    return { success: true };
  }

  private async handleValidateSchema(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.validateSchema(args[0]);
    return { success: true };
  }

  private async handleSchemaDiff(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.diffSchemas(args[0], args[1]);
    return { success: true };
  }

  private async handleCacheEnable(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    const redisUrl = args[0] || context.env.REDIS_URL;
    await this.features.enableCache(redisUrl);
    return { success: true };
  }

  private async handleCacheStats(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.cacheStats();
    return { success: true };
  }

  private async handleCacheClear(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.clearCache();
    return { success: true };
  }

  private async handleTestMigration(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.testMigration(args[0]);
    return { success: true };
  }

  private async handleExplain(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.explainSQL(args[0]);
    return { success: true };
  }

  private async handleTranslate(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.translateToSQL(args[0]);
    return { success: true };
  }

  private async handleAnalyzeCosts(
    args: string[],
    options: CLIOptions,
    context: CommandContext
  ): Promise<CommandResult> {
    await this.features.analyzeCosts(args[0], args[1]);
    return { success: true };
  }

  /**
   * Get list of all registered commands
   */
  getRegisteredCommands(): CommandRegistration[] {
    return Array.from(this.commandRegistry.values());
  }

  /**
   * Cleanup resources
   */
  async cleanup(): Promise<void> {
    await this.features.cleanup();
  }
}

/**
 * Create and export singleton instance
 */
export function createCLIWrapper(): CLIWrapper {
  return new CLIWrapper();
}

/**
 * Default export
 */
export default CLIWrapper;
