/**
 * Command processor for AI-Shell
 * Handles command execution, AI integration, and result processing
 */

import { spawn, ChildProcess } from 'child_process';
import { CommandContext, CommandResult, ShellConfig } from '../types';
import * as fs from 'fs';
import * as path from 'path';

export class CommandProcessor {
  private config: ShellConfig;
  private executionHistory: CommandResult[] = [];

  constructor(config: ShellConfig) {
    this.config = config;
  }

  /**
   * Execute a shell command
   */
  public async execute(context: CommandContext): Promise<CommandResult> {
    const startTime = Date.now();

    return new Promise((resolve, reject) => {
      const { command, args, workingDirectory, environment } = context;

      // Log execution if verbose
      if (this.config.verbose) {
        console.log(
          `[EXEC] ${command} ${args.join(' ')} in ${workingDirectory}`
        );
      }

      const child: ChildProcess = spawn(command, args, {
        cwd: workingDirectory,
        env: { ...process.env, ...environment },
        shell: true,
      });

      let stdout = '';
      let stderr = '';

      child.stdout?.on('data', (data) => {
        stdout += data.toString();
        if (this.config.verbose) {
          process.stdout.write(data);
        }
      });

      child.stderr?.on('data', (data) => {
        stderr += data.toString();
        if (this.config.verbose) {
          process.stderr.write(data);
        }
      });

      // Timeout handling
      const timeout = setTimeout(() => {
        child.kill('SIGTERM');
        reject(
          new Error(
            `Command timed out after ${this.config.timeout}ms: ${command}`
          )
        );
      }, this.config.timeout);

      child.on('close', (code) => {
        clearTimeout(timeout);

        const result: CommandResult = {
          success: code === 0,
          output: stdout.trim(),
          error: stderr.trim() || undefined,
          exitCode: code || 0,
          timestamp: new Date(),
        };

        // Store in history
        this.executionHistory.push(result);
        if (this.executionHistory.length > this.config.maxHistorySize) {
          this.executionHistory.shift();
        }

        if (this.config.verbose) {
          console.log(
            `[DONE] Exit code: ${code}, Duration: ${Date.now() - startTime}ms`
          );
        }

        resolve(result);
      });

      child.on('error', (error) => {
        clearTimeout(timeout);
        reject(error);
      });
    });
  }

  /**
   * Parse and validate command input
   */
  public parseCommand(input: string): {
    command: string;
    args: string[];
  } {
    const trimmed = input.trim();
    if (!trimmed) {
      throw new Error('Empty command');
    }

    // Handle quoted arguments
    const parts: string[] = [];
    let current = '';
    let inQuotes = false;
    let quoteChar = '';

    for (let i = 0; i < trimmed.length; i++) {
      const char = trimmed[i];

      if ((char === '"' || char === "'") && !inQuotes) {
        inQuotes = true;
        quoteChar = char;
      } else if (char === quoteChar && inQuotes) {
        inQuotes = false;
        quoteChar = '';
      } else if (char === ' ' && !inQuotes) {
        if (current) {
          parts.push(current);
          current = '';
        }
      } else {
        current += char;
      }
    }

    if (current) {
      parts.push(current);
    }

    if (inQuotes) {
      throw new Error('Unclosed quote in command');
    }

    const [command, ...args] = parts;
    return { command, args };
  }

  /**
   * Check if command is a built-in shell command
   */
  public isBuiltIn(command: string): boolean {
    const builtIns = ['cd', 'exit', 'help', 'history', 'clear', 'config'];
    return builtIns.includes(command);
  }

  /**
   * Execute built-in commands
   */
  public async executeBuiltIn(
    command: string,
    args: string[],
    currentDir: string
  ): Promise<CommandResult> {
    const timestamp = new Date();

    switch (command) {
      case 'cd': {
        const targetDir = args[0] || process.env.HOME || '/';
        const newDir = path.resolve(currentDir, targetDir);

        if (!fs.existsSync(newDir)) {
          return {
            success: false,
            output: '',
            error: `Directory not found: ${newDir}`,
            exitCode: 1,
            timestamp,
          };
        }

        if (!fs.statSync(newDir).isDirectory()) {
          return {
            success: false,
            output: '',
            error: `Not a directory: ${newDir}`,
            exitCode: 1,
            timestamp,
          };
        }

        return {
          success: true,
          output: newDir,
          exitCode: 0,
          timestamp,
        };
      }

      case 'history': {
        const historyOutput = this.executionHistory
          .slice(-20)
          .map((result, idx) => {
            return `${idx + 1}. [${result.timestamp.toISOString()}] Exit: ${result.exitCode}`;
          })
          .join('\n');

        return {
          success: true,
          output: historyOutput,
          exitCode: 0,
          timestamp,
        };
      }

      case 'clear': {
        process.stdout.write('\x1Bc'); // Clear terminal
        return {
          success: true,
          output: '',
          exitCode: 0,
          timestamp,
        };
      }

      case 'help': {
        const helpText = `
AI-Shell - AI-Powered Command Line Interface

Built-in Commands:
  cd [dir]     - Change directory
  exit         - Exit the shell
  help         - Show this help message
  history      - Show command history
  clear        - Clear the terminal
  config       - Show current configuration

Special Commands:
  ai [query]   - Send query to AI assistant
  explain      - Explain the last command
  suggest      - Get command suggestions
        `.trim();

        return {
          success: true,
          output: helpText,
          exitCode: 0,
          timestamp,
        };
      }

      case 'config': {
        const configOutput = JSON.stringify(
          {
            mode: this.config.mode,
            aiProvider: this.config.aiProvider,
            model: this.config.model,
            timeout: this.config.timeout,
            verbose: this.config.verbose,
          },
          null,
          2
        );

        return {
          success: true,
          output: configOutput,
          exitCode: 0,
          timestamp,
        };
      }

      default:
        return {
          success: false,
          output: '',
          error: `Unknown built-in command: ${command}`,
          exitCode: 1,
          timestamp,
        };
    }
  }

  /**
   * Get execution history
   */
  public getHistory(): CommandResult[] {
    return [...this.executionHistory];
  }

  /**
   * Clear execution history
   */
  public clearHistory(): void {
    this.executionHistory = [];
  }

  /**
   * Update processor configuration
   */
  public updateConfig(config: ShellConfig): void {
    this.config = config;
  }
}
