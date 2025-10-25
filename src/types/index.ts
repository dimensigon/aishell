/**
 * Core type definitions for AI-Shell
 */

export interface CommandResult {
  success: boolean;
  output: string;
  error?: string;
  exitCode: number;
  timestamp: Date;
}

export interface CommandContext {
  command: string;
  args: string[];
  workingDirectory: string;
  environment: NodeJS.ProcessEnv;
}

export interface ShellConfig {
  mode: 'interactive' | 'command';
  historyFile: string;
  maxHistorySize: number;
  aiProvider: 'anthropic' | 'openai';
  apiKey?: string;
  model: string;
  timeout: number;
  verbose: boolean;
}

export interface QueuedCommand {
  id: string;
  command: string;
  priority: number;
  timestamp: Date;
  resolve: (result: CommandResult) => void;
  reject: (error: Error) => void;
}

export interface REPLState {
  running: boolean;
  history: string[];
  currentDirectory: string;
}

export type CommandHandler = (
  context: CommandContext
) => Promise<CommandResult>;

export interface PluginInterface {
  name: string;
  version: string;
  initialize: () => Promise<void>;
  handleCommand?: CommandHandler;
  shutdown?: () => Promise<void>;
}
