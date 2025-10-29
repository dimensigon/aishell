/**
 * Command processor for AI-Shell
 * Handles command execution, AI integration, and result processing
 */

import { spawn, ChildProcess } from 'child_process';
import { CommandContext, CommandResult, ShellConfig } from '../types';
import * as fs from 'fs';
import * as path from 'path';
import { createLogger, auditLogger } from './logger';

export class CommandProcessor {
  private config: ShellConfig;
  private executionHistory: CommandResult[] = [];
  private logger = createLogger('CommandProcessor');

  // Whitelist of safe commands to prevent command injection
  private static readonly SAFE_COMMANDS = [
    'ls', 'cat', 'grep', 'find', 'echo', 'pwd', 'mkdir', 'rm', 'cp', 'mv',
    'touch', 'chmod', 'chown', 'head', 'tail', 'wc', 'sort', 'uniq', 'cut',
    'sed', 'awk', 'tar', 'gzip', 'gunzip', 'zip', 'unzip', 'curl', 'wget',
    'git', 'npm', 'node', 'python', 'python3', 'pip', 'pip3', 'make',
    'docker', 'kubectl', 'terraform', 'ansible', 'ssh', 'scp', 'rsync',
    'ps', 'top', 'htop', 'df', 'du', 'free', 'uptime', 'whoami', 'which',
    'man', 'less', 'more', 'vi', 'vim', 'nano', 'date', 'cal', 'bc'
  ];

  // Dangerous characters that could be used for command injection
  // Note: Since we use spawn() without shell:true, we only need to check
  // for shell metacharacters that could be dangerous in the command name itself
  // Arguments are passed safely to the child process and don't need strict filtering
  private static readonly DANGEROUS_CHARS = /[;&|`]/;

  constructor(config: ShellConfig) {
    this.config = config;
  }

  /**
   * Validate if a command is in the whitelist
   */
  private validateCommand(command: string): boolean {
    // Extract base command (handle paths like /usr/bin/ls)
    const baseCommand = path.basename(command);
    return CommandProcessor.SAFE_COMMANDS.includes(baseCommand);
  }

  /**
   * Sanitize input to prevent shell injection
   * Note: This is primarily for the command name. Arguments are safe
   * because we use spawn() without shell:true, so they're passed directly
   * to the process without shell interpretation.
   */
  private sanitizeInput(input: string): string {
    // Since we're not using shell:true, arguments are safe from injection
    // We only check for null bytes which could cause issues at the OS level
    if (input.includes('\0')) {
      throw new Error(
        'Input contains null bytes which are not allowed'
      );
    }
    return input;
  }

  /**
   * Execute a shell command
   */
  public async execute(context: CommandContext): Promise<CommandResult> {
    const startTime = Date.now();

    return new Promise((resolve, reject) => {
      const { command, args, workingDirectory, environment } = context;

      // Security: Validate command is in whitelist
      if (!this.validateCommand(command)) {
        reject(
          new Error(
            `Security: Command '${command}' is not in the whitelist of safe commands. ` +
            `This is to prevent command injection attacks.`
          )
        );
        return;
      }

      // Security: Sanitize all arguments
      try {
        args.forEach((arg, index) => {
          args[index] = this.sanitizeInput(arg);
        });
      } catch (error) {
        reject(error);
        return;
      }

      // Log execution if verbose
      if (this.config.verbose) {
        this.logger.info('Executing command', {
          command,
          args,
          workingDirectory
        });
      }

      // Audit log for command execution
      auditLogger.info('Command execution', {
        command,
        args: args.join(' '),
        workingDirectory,
        timestamp: Date.now()
      });

      // Security: DO NOT use shell: true to prevent command injection
      const child: ChildProcess = spawn(command, args, {
        cwd: workingDirectory,
        env: { ...process.env, ...environment },
        // shell: true REMOVED - this was the critical vulnerability
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
          const duration = Date.now() - startTime;
          this.logger.info('Command completed', {
            exitCode: code,
            duration,
            success: code === 0
          });
          this.logger.perf('command_execution', duration, {
            command,
            exitCode: code
          });
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
