#!/usr/bin/env node

/**
 * AI-Shell CLI Entry Point
 * Main command-line interface with REPL mode and async command execution
 */

import * as readline from 'readline';
import * as process from 'process';
import * as os from 'os';
import { ConfigManager } from '../core/config';
import { CommandProcessor } from '../core/processor';
import { AsyncCommandQueue } from '../core/queue';
import { REPLState, CommandContext } from '../types';

class AIShell {
  private config!: ConfigManager;
  private processor!: CommandProcessor;
  private queue!: AsyncCommandQueue;
  private rl!: readline.Interface;
  private state: REPLState = {
    running: false,
    history: [],
    currentDirectory: process.cwd(),
  };

  /**
   * Initialize the AI Shell
   */
  public async initialize(): Promise<void> {
    try {
      // Load configuration
      this.config = new ConfigManager();
      const shellConfig = await this.config.load();

      // Initialize processor and queue
      this.processor = new CommandProcessor(shellConfig);
      this.queue = new AsyncCommandQueue(this.processor, {
        concurrency: 3,
        rateLimit: 10,
        maxQueueSize: 50,
      });

      // Setup event listeners
      this.setupQueueEvents();

      console.log('🤖 AI-Shell initialized');
      if (shellConfig.verbose) {
        console.log(`   Provider: ${shellConfig.aiProvider}`);
        console.log(`   Model: ${shellConfig.model}`);
        console.log(`   Mode: ${shellConfig.mode}`);
      }
    } catch (error) {
      console.error('Failed to initialize AI-Shell:', error);
      process.exit(1);
    }
  }

  /**
   * Setup queue event listeners
   */
  private setupQueueEvents(): void {
    this.queue.on('commandQueued', ({ queueSize }) => {
      if (this.config.getConfig().verbose) {
        console.log(`📋 Command queued (queue size: ${queueSize})`);
      }
    });

    this.queue.on('commandStart', ({ command, queueSize }) => {
      if (this.config.getConfig().verbose) {
        console.log(`▶️  Executing: ${command} (${queueSize} remaining)`);
      }
    });

    this.queue.on('commandComplete', ({ result }) => {
      if (!result.success && result.error) {
        console.error(`❌ Error: ${result.error}`);
      }
    });

    this.queue.on('commandError', ({ command, error }) => {
      console.error(`💥 Command failed: ${command}`);
      console.error(error.message);
    });
  }

  /**
   * Start interactive REPL mode
   */
  public async startREPL(): Promise<void> {
    this.state.running = true;

    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: this.getPrompt(),
      historySize: this.config.getConfig().maxHistorySize,
    });

    // Setup signal handlers
    this.setupSignalHandlers();

    // Display welcome message
    this.displayWelcome();

    this.rl.prompt();

    this.rl.on('line', async (line) => {
      const input = line.trim();

      if (!input) {
        this.rl.prompt();
        return;
      }

      // Add to history
      this.state.history.push(input);

      try {
        await this.handleInput(input);
      } catch (error) {
        console.error(
          '❌ Error:',
          error instanceof Error ? error.message : String(error)
        );
      }

      this.rl.setPrompt(this.getPrompt());
      this.rl.prompt();
    });

    this.rl.on('close', () => {
      this.shutdown();
    });
  }

  /**
   * Handle user input
   */
  private async handleInput(input: string): Promise<void> {
    const { command, args } = this.processor.parseCommand(input);

    // Handle exit command
    if (command === 'exit' || command === 'quit') {
      this.shutdown();
      return;
    }

    // Handle built-in commands
    if (this.processor.isBuiltIn(command)) {
      const result = await this.processor.executeBuiltIn(
        command,
        args,
        this.state.currentDirectory
      );

      if (result.output) {
        console.log(result.output);
      }

      // Update current directory for cd command
      if (command === 'cd' && result.success) {
        this.state.currentDirectory = result.output;
      }

      return;
    }

    // Queue command for execution
    const context: CommandContext = {
      command,
      args,
      workingDirectory: this.state.currentDirectory,
      environment: process.env,
    };

    try {
      const result = await this.queue.enqueue(input, context, 0);

      if (result.output) {
        console.log(result.output);
      }

      if (result.error) {
        console.error(`stderr: ${result.error}`);
      }
    } catch (error) {
      console.error(
        'Failed to execute command:',
        error instanceof Error ? error.message : String(error)
      );
    }
  }

  /**
   * Execute single command (non-interactive mode)
   */
  public async executeCommand(command: string): Promise<void> {
    try {
      const context: CommandContext = {
        command: '',
        args: [],
        workingDirectory: this.state.currentDirectory,
        environment: process.env,
      };

      const { command: cmd, args } = this.processor.parseCommand(command);

      if (this.processor.isBuiltIn(cmd)) {
        const result = await this.processor.executeBuiltIn(
          cmd,
          args,
          this.state.currentDirectory
        );
        if (result.output) {
          console.log(result.output);
        }
        process.exit(result.exitCode);
        return;
      }

      const result = await this.queue.enqueue(command, context, 10);

      if (result.output) {
        console.log(result.output);
      }

      if (result.error) {
        console.error(result.error);
      }

      await this.queue.drain();
      process.exit(result.exitCode);
    } catch (error) {
      console.error(
        'Command execution failed:',
        error instanceof Error ? error.message : String(error)
      );
      process.exit(1);
    }
  }

  /**
   * Setup signal handlers (Ctrl+C, etc.)
   */
  private setupSignalHandlers(): void {
    process.on('SIGINT', () => {
      console.log('\n🛑 Received SIGINT, shutting down gracefully...');
      this.shutdown();
    });

    process.on('SIGTERM', () => {
      console.log('\n🛑 Received SIGTERM, shutting down gracefully...');
      this.shutdown();
    });

    process.on('uncaughtException', (error) => {
      console.error('💥 Uncaught exception:', error);
      this.shutdown(1);
    });

    process.on('unhandledRejection', (reason) => {
      console.error('💥 Unhandled rejection:', reason);
      this.shutdown(1);
    });
  }

  /**
   * Get shell prompt
   */
  private getPrompt(): string {
    const cwd = this.state.currentDirectory.replace(os.homedir(), '~');
    return `\x1b[36mai-shell\x1b[0m:\x1b[33m${cwd}\x1b[0m$ `;
  }

  /**
   * Display welcome message
   */
  private displayWelcome(): void {
    console.log('\n╔═══════════════════════════════════════════╗');
    console.log('║   🤖 Welcome to AI-Shell                 ║');
    console.log('║   AI-Powered Command Line Interface      ║');
    console.log('╚═══════════════════════════════════════════╝\n');
    console.log('Type "help" for available commands');
    console.log('Type "exit" or press Ctrl+C to quit\n');
  }

  /**
   * Shutdown the shell
   */
  private async shutdown(exitCode = 0): Promise<void> {
    if (!this.state.running) {
      return;
    }

    this.state.running = false;

    console.log('\n👋 Shutting down AI-Shell...');

    // Wait for queue to drain
    if (this.queue) {
      const status = this.queue.getStatus();
      if (status.queueSize > 0 || status.processing > 0) {
        console.log('⏳ Waiting for commands to complete...');
        await this.queue.drain();
      }
    }

    // Close readline interface
    if (this.rl) {
      this.rl.close();
    }

    console.log('✅ Goodbye!\n');
    process.exit(exitCode);
  }
}

/**
 * Main entry point
 */
async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const shell = new AIShell();

  await shell.initialize();

  if (args.length > 0) {
    // Command mode: execute single command
    const command = args.join(' ');
    await shell.executeCommand(command);
  } else {
    // Interactive REPL mode
    await shell.startREPL();
  }
}

// Run the shell
if (require.main === module) {
  main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { AIShell };
