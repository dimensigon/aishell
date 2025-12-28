/**
 * Context Management System
 * Save and load query contexts, sessions, and configurations
 *
 * Features:
 * - Context save/load with merge/overwrite options
 * - Session management and restoration
 * - Export/import with JSON and YAML support
 * - Context comparison and diffing
 * - Query history and alias persistence
 */

import { createLogger } from '../core/logger';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';
import { EventEmitter } from 'eventemitter3';

/**
 * Context interface representing saved state
 */
export interface Context {
  name: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
  database?: string;
  queryHistory?: QueryHistoryEntry[];
  aliases?: Record<string, string>;
  configuration?: Record<string, any>;
  variables?: Record<string, any>;
  connections?: ConnectionInfo[];
  metadata?: Record<string, any>;
}

/**
 * Query history entry
 */
export interface QueryHistoryEntry {
  query: string;
  timestamp: number;
  duration?: number;
  success: boolean;
  error?: string;
}

/**
 * Connection information
 */
export interface ConnectionInfo {
  name: string;
  host?: string;
  port?: number;
  database?: string;
  user?: string;
  // password should never be stored in context
}

/**
 * Session interface for session management
 */
export interface Session {
  id: string;
  name: string;
  startTime: Date;
  endTime?: Date;
  context: Context;
  commandHistory: string[];
  statistics?: SessionStatistics;
}

/**
 * Session statistics
 */
export interface SessionStatistics {
  queriesExecuted: number;
  totalDuration: number;
  errorsCount: number;
  successRate: number;
}

/**
 * Options for saving context
 */
export interface SaveContextOptions {
  description?: string;
  includeHistory?: boolean;
  includeAliases?: boolean;
  includeConfig?: boolean;
  includeVariables?: boolean;
  includeConnections?: boolean;
}

/**
 * Context difference result
 */
export interface ContextDiff {
  name1: string;
  name2: string;
  differences: {
    database?: { context1: string; context2: string };
    aliases?: {
      added: string[];
      removed: string[];
      modified: Array<{ key: string; value1: string; value2: string }>;
    };
    configuration?: {
      added: string[];
      removed: string[];
      modified: Array<{ key: string; value1: any; value2: any }>;
    };
    variables?: {
      added: string[];
      removed: string[];
      modified: Array<{ key: string; value1: any; value2: any }>;
    };
    historyCount?: { context1: number; context2: number };
  };
}

/**
 * Context list entry for display
 */
export interface ContextListEntry {
  name: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
  size: number;
  queryCount?: number;
  aliasCount?: number;
}

/**
 * Context Manager Events
 */
export interface ContextManagerEvents {
  contextSaved: (name: string) => void;
  contextLoaded: (name: string) => void;
  contextDeleted: (name: string) => void;
  sessionStarted: (sessionId: string) => void;
  sessionEnded: (sessionId: string) => void;
}

/**
 * Context Manager Class
 * Manages contexts, sessions, and configurations
 */
export class ContextManager extends EventEmitter<ContextManagerEvents> {
  private logger = createLogger('ContextManager');
  private contextDir: string;
  private sessionDir: string;
  private currentContext: Context | null = null;
  private currentSession: Session | null = null;

  constructor(baseDir?: string) {
    super();
    const base = baseDir || path.join(os.homedir(), '.ai-shell');
    this.contextDir = path.join(base, 'contexts');
    this.sessionDir = path.join(base, 'sessions');
  }

  /**
   * Initialize directories
   */
  async initialize(): Promise<void> {
    await this.ensureDirectories();
    this.logger.info('Context manager initialized', {
      contextDir: this.contextDir,
      sessionDir: this.sessionDir
    });
  }

  /**
   * Save context to file
   */
  async saveContext(
    name: string,
    options: SaveContextOptions = {}
  ): Promise<void> {
    await this.ensureDirectories();

    const existingContext = await this.loadContextSafe(name);
    const timestamp = new Date();

    const context: Context = {
      name,
      description: options.description || existingContext?.description,
      createdAt: existingContext?.createdAt || timestamp,
      updatedAt: timestamp,
      database: this.currentContext?.database,
      queryHistory: options.includeHistory
        ? this.currentContext?.queryHistory || []
        : existingContext?.queryHistory || [],
      aliases: options.includeAliases
        ? this.currentContext?.aliases || {}
        : existingContext?.aliases || {},
      configuration: options.includeConfig
        ? this.currentContext?.configuration || {}
        : existingContext?.configuration || {},
      variables: options.includeVariables
        ? this.currentContext?.variables || {}
        : existingContext?.variables || {},
      connections: options.includeConnections
        ? this.currentContext?.connections || []
        : existingContext?.connections || [],
      metadata: this.currentContext?.metadata || {}
    };

    const contextPath = this.getContextPath(name);
    await fs.writeFile(
      contextPath,
      JSON.stringify(context, null, 2),
      'utf-8'
    );

    this.logger.info('Context saved', { name, path: contextPath });
    this.emit('contextSaved', name);
  }

  /**
   * Load context from file
   */
  async loadContext(name: string, merge: boolean = false): Promise<Context> {
    const contextPath = this.getContextPath(name);

    try {
      const content = await fs.readFile(contextPath, 'utf-8');
      const context = JSON.parse(content) as Context;

      // Convert date strings back to Date objects
      context.createdAt = new Date(context.createdAt);
      context.updatedAt = new Date(context.updatedAt);

      if (merge && this.currentContext) {
        // Merge with current context
        this.currentContext = this.mergeContexts(this.currentContext, context);
      } else {
        // Replace current context
        this.currentContext = context;
      }

      this.logger.info('Context loaded', { name, merge });
      this.emit('contextLoaded', name);

      return context;
    } catch (error) {
      this.logger.error('Failed to load context', error, { name });
      throw new Error(`Failed to load context "${name}": ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * List all available contexts
   */
  async listContexts(verbose: boolean = false): Promise<ContextListEntry[]> {
    await this.ensureDirectories();

    try {
      const files = await fs.readdir(this.contextDir);
      const contextFiles = files.filter(f => f.endsWith('.json'));

      const contexts: ContextListEntry[] = [];

      for (const file of contextFiles) {
        const filePath = path.join(this.contextDir, file);
        const stats = await fs.stat(filePath);

        if (verbose) {
          try {
            const content = await fs.readFile(filePath, 'utf-8');
            const context = JSON.parse(content) as Context;
            contexts.push({
              name: context.name,
              description: context.description,
              createdAt: new Date(context.createdAt),
              updatedAt: new Date(context.updatedAt),
              size: stats.size,
              queryCount: context.queryHistory?.length || 0,
              aliasCount: Object.keys(context.aliases || {}).length
            });
          } catch (error) {
            this.logger.warn('Failed to parse context file', { file, error });
          }
        } else {
          contexts.push({
            name: path.basename(file, '.json'),
            createdAt: stats.birthtime,
            updatedAt: stats.mtime,
            size: stats.size
          });
        }
      }

      return contexts.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
    } catch (error) {
      this.logger.error('Failed to list contexts', error);
      return [];
    }
  }

  /**
   * Delete context
   */
  async deleteContext(name: string, force: boolean = false): Promise<void> {
    const contextPath = this.getContextPath(name);

    try {
      await fs.access(contextPath);

      if (!force && this.currentContext?.name === name) {
        throw new Error('Cannot delete current context without --force flag');
      }

      await fs.unlink(contextPath);

      if (this.currentContext?.name === name) {
        this.currentContext = null;
      }

      this.logger.info('Context deleted', { name });
      this.emit('contextDeleted', name);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        throw new Error(`Context "${name}" not found`);
      }
      throw error;
    }
  }

  /**
   * Export context to file
   */
  async exportContext(
    name: string,
    file: string,
    format: 'json' | 'yaml' = 'json'
  ): Promise<void> {
    const context = await this.loadContextSafe(name);
    if (!context) {
      throw new Error(`Context "${name}" not found`);
    }

    let content: string;
    if (format === 'yaml') {
      // For YAML, we'll use a simple JSON.stringify and convert
      // In production, you'd use js-yaml library
      content = this.jsonToYaml(context);
    } else {
      content = JSON.stringify(context, null, 2);
    }

    await fs.writeFile(file, content, 'utf-8');
    this.logger.info('Context exported', { name, file, format });
  }

  /**
   * Import context from file
   */
  async importContext(file: string, name?: string): Promise<void> {
    const content = await fs.readFile(file, 'utf-8');

    let context: Context;

    // Try JSON first
    try {
      context = JSON.parse(content);
    } catch {
      // Try YAML
      context = this.yamlToJson(content);
    }

    // Override name if provided
    if (name) {
      context.name = name;
    }

    // Validate context structure
    if (!context.name) {
      throw new Error('Invalid context: missing name');
    }

    // Save as new context
    const contextPath = this.getContextPath(context.name);
    await fs.writeFile(
      contextPath,
      JSON.stringify(context, null, 2),
      'utf-8'
    );

    this.logger.info('Context imported', { name: context.name, file });
  }

  /**
   * Get current context
   */
  async getCurrentContext(): Promise<Context | null> {
    return this.currentContext;
  }

  /**
   * Show context details
   */
  async showContext(name?: string): Promise<Context> {
    if (!name && !this.currentContext) {
      throw new Error('No context specified and no current context');
    }

    if (!name) {
      return this.currentContext!;
    }

    return await this.loadContextSafe(name) ||
      await this.loadContext(name, false);
  }

  /**
   * Compare two contexts
   */
  async diffContexts(
    context1Name: string,
    context2Name: string
  ): Promise<ContextDiff> {
    const ctx1 = await this.loadContextSafe(context1Name);
    const ctx2 = await this.loadContextSafe(context2Name);

    if (!ctx1) throw new Error(`Context "${context1Name}" not found`);
    if (!ctx2) throw new Error(`Context "${context2Name}" not found`);

    const diff: ContextDiff = {
      name1: context1Name,
      name2: context2Name,
      differences: {}
    };

    // Compare database
    if (ctx1.database !== ctx2.database) {
      diff.differences.database = {
        context1: ctx1.database || 'none',
        context2: ctx2.database || 'none'
      };
    }

    // Compare aliases
    diff.differences.aliases = this.diffObjects(
      ctx1.aliases || {},
      ctx2.aliases || {}
    );

    // Compare configuration
    diff.differences.configuration = this.diffObjects(
      ctx1.configuration || {},
      ctx2.configuration || {}
    );

    // Compare variables
    diff.differences.variables = this.diffObjects(
      ctx1.variables || {},
      ctx2.variables || {}
    );

    // Compare history count
    const hist1 = ctx1.queryHistory?.length || 0;
    const hist2 = ctx2.queryHistory?.length || 0;
    if (hist1 !== hist2) {
      diff.differences.historyCount = {
        context1: hist1,
        context2: hist2
      };
    }

    return diff;
  }

  /**
   * Start a new session
   */
  async startSession(name: string): Promise<string> {
    await this.ensureDirectories();

    const sessionId = this.generateSessionId();
    const session: Session = {
      id: sessionId,
      name,
      startTime: new Date(),
      context: this.currentContext || this.createEmptyContext(name),
      commandHistory: [],
      statistics: {
        queriesExecuted: 0,
        totalDuration: 0,
        errorsCount: 0,
        successRate: 100
      }
    };

    this.currentSession = session;
    this.logger.info('Session started', { sessionId, name });
    this.emit('sessionStarted', sessionId);

    return sessionId;
  }

  /**
   * End current session
   */
  async endSession(): Promise<void> {
    if (!this.currentSession) {
      throw new Error('No active session');
    }

    this.currentSession.endTime = new Date();

    // Save session to file
    const sessionPath = path.join(
      this.sessionDir,
      `${this.currentSession.id}.json`
    );
    await fs.writeFile(
      sessionPath,
      JSON.stringify(this.currentSession, null, 2),
      'utf-8'
    );

    this.logger.info('Session ended', { sessionId: this.currentSession.id });
    this.emit('sessionEnded', this.currentSession.id);

    this.currentSession = null;
  }

  /**
   * List all sessions
   */
  async listSessions(): Promise<Session[]> {
    await this.ensureDirectories();

    try {
      const files = await fs.readdir(this.sessionDir);
      const sessionFiles = files.filter(f => f.endsWith('.json'));

      const sessions: Session[] = [];

      for (const file of sessionFiles) {
        try {
          const content = await fs.readFile(
            path.join(this.sessionDir, file),
            'utf-8'
          );
          const session = JSON.parse(content) as Session;
          session.startTime = new Date(session.startTime);
          if (session.endTime) {
            session.endTime = new Date(session.endTime);
          }
          sessions.push(session);
        } catch (error) {
          this.logger.warn('Failed to parse session file', { file, error });
        }
      }

      return sessions.sort((a, b) =>
        b.startTime.getTime() - a.startTime.getTime()
      );
    } catch (error) {
      this.logger.error('Failed to list sessions', error);
      return [];
    }
  }

  /**
   * Restore session
   */
  async restoreSession(name: string): Promise<void> {
    const sessions = await this.listSessions();
    const session = sessions.find(s => s.name === name || s.id === name);

    if (!session) {
      throw new Error(`Session "${name}" not found`);
    }

    this.currentContext = session.context;
    this.currentSession = {
      ...session,
      id: this.generateSessionId(),
      startTime: new Date(),
      endTime: undefined
    };

    this.logger.info('Session restored', { name, sessionId: this.currentSession.id });
  }

  /**
   * Export session
   */
  async exportSession(name: string, file: string): Promise<void> {
    const sessions = await this.listSessions();
    const session = sessions.find(s => s.name === name || s.id === name);

    if (!session) {
      throw new Error(`Session "${name}" not found`);
    }

    await fs.writeFile(
      file,
      JSON.stringify(session, null, 2),
      'utf-8'
    );

    this.logger.info('Session exported', { name, file });
  }

  /**
   * Update current context
   */
  updateCurrentContext(updates: Partial<Context>): void {
    if (!this.currentContext) {
      this.currentContext = this.createEmptyContext('default');
    }

    this.currentContext = {
      ...this.currentContext,
      ...updates,
      updatedAt: new Date()
    };
  }

  /**
   * Add query to history
   */
  addQueryToHistory(entry: QueryHistoryEntry): void {
    if (!this.currentContext) {
      this.currentContext = this.createEmptyContext('default');
    }

    if (!this.currentContext.queryHistory) {
      this.currentContext.queryHistory = [];
    }

    this.currentContext.queryHistory.push(entry);

    // Keep only last 1000 queries
    if (this.currentContext.queryHistory.length > 1000) {
      this.currentContext.queryHistory = this.currentContext.queryHistory.slice(-1000);
    }

    // Update session statistics
    if (this.currentSession?.statistics) {
      this.currentSession.statistics.queriesExecuted++;
      if (entry.duration) {
        this.currentSession.statistics.totalDuration += entry.duration;
      }
      if (!entry.success) {
        this.currentSession.statistics.errorsCount++;
      }
      this.currentSession.statistics.successRate =
        ((this.currentSession.statistics.queriesExecuted -
          this.currentSession.statistics.errorsCount) /
          this.currentSession.statistics.queriesExecuted) *
        100;
    }
  }

  /**
   * Add or update alias
   */
  setAlias(name: string, value: string): void {
    if (!this.currentContext) {
      this.currentContext = this.createEmptyContext('default');
    }

    if (!this.currentContext.aliases) {
      this.currentContext.aliases = {};
    }

    this.currentContext.aliases[name] = value;
  }

  /**
   * Set configuration value
   */
  setConfig(key: string, value: any): void {
    if (!this.currentContext) {
      this.currentContext = this.createEmptyContext('default');
    }

    if (!this.currentContext.configuration) {
      this.currentContext.configuration = {};
    }

    this.currentContext.configuration[key] = value;
  }

  /**
   * Set variable value
   */
  setVariable(key: string, value: any): void {
    if (!this.currentContext) {
      this.currentContext = this.createEmptyContext('default');
    }

    if (!this.currentContext.variables) {
      this.currentContext.variables = {};
    }

    this.currentContext.variables[key] = value;
  }

  // Private helper methods

  private async ensureDirectories(): Promise<void> {
    await fs.mkdir(this.contextDir, { recursive: true });
    await fs.mkdir(this.sessionDir, { recursive: true });
  }

  private getContextPath(name: string): string {
    return path.join(this.contextDir, `${name}.json`);
  }

  private async loadContextSafe(name: string): Promise<Context | null> {
    try {
      const contextPath = this.getContextPath(name);
      const content = await fs.readFile(contextPath, 'utf-8');
      const context = JSON.parse(content) as Context;
      context.createdAt = new Date(context.createdAt);
      context.updatedAt = new Date(context.updatedAt);
      return context;
    } catch {
      return null;
    }
  }

  private mergeContexts(current: Context, loaded: Context): Context {
    return {
      ...current,
      name: loaded.name,
      description: loaded.description || current.description,
      updatedAt: new Date(),
      database: loaded.database || current.database,
      queryHistory: [
        ...(current.queryHistory || []),
        ...(loaded.queryHistory || [])
      ],
      aliases: {
        ...(current.aliases || {}),
        ...(loaded.aliases || {})
      },
      configuration: {
        ...(current.configuration || {}),
        ...(loaded.configuration || {})
      },
      variables: {
        ...(current.variables || {}),
        ...(loaded.variables || {})
      },
      connections: [
        ...(current.connections || []),
        ...(loaded.connections || [])
      ],
      metadata: {
        ...(current.metadata || {}),
        ...(loaded.metadata || {})
      }
    };
  }

  private diffObjects(
    obj1: Record<string, any>,
    obj2: Record<string, any>
  ): {
    added: string[];
    removed: string[];
    modified: Array<{ key: string; value1: any; value2: any }>;
  } {
    const keys1 = Object.keys(obj1);
    const keys2 = Object.keys(obj2);

    const added = keys2.filter(k => !keys1.includes(k));
    const removed = keys1.filter(k => !keys2.includes(k));
    const modified: Array<{ key: string; value1: any; value2: any }> = [];

    for (const key of keys1.filter(k => keys2.includes(k))) {
      if (JSON.stringify(obj1[key]) !== JSON.stringify(obj2[key])) {
        modified.push({
          key,
          value1: obj1[key],
          value2: obj2[key]
        });
      }
    }

    return { added, removed, modified };
  }

  private createEmptyContext(name: string): Context {
    return {
      name,
      createdAt: new Date(),
      updatedAt: new Date(),
      queryHistory: [],
      aliases: {},
      configuration: {},
      variables: {},
      connections: [],
      metadata: {}
    };
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private jsonToYaml(obj: any, indent: number = 0): string {
    const spaces = '  '.repeat(indent);
    let yaml = '';

    for (const [key, value] of Object.entries(obj)) {
      if (value === null || value === undefined) {
        yaml += `${spaces}${key}: null\n`;
      } else if (Array.isArray(value)) {
        yaml += `${spaces}${key}:\n`;
        for (const item of value) {
          if (typeof item === 'object') {
            yaml += `${spaces}  -\n${this.jsonToYaml(item, indent + 2)}`;
          } else {
            yaml += `${spaces}  - ${item}\n`;
          }
        }
      } else if (typeof value === 'object') {
        yaml += `${spaces}${key}:\n${this.jsonToYaml(value, indent + 1)}`;
      } else if (typeof value === 'string') {
        yaml += `${spaces}${key}: "${value}"\n`;
      } else {
        yaml += `${spaces}${key}: ${value}\n`;
      }
    }

    return yaml;
  }

  private yamlToJson(yaml: string): any {
    // Simple YAML parser for basic structures
    // In production, use js-yaml library
    const lines = yaml.split('\n').filter(l => l.trim());
    const result: any = {};
    let currentKey = '';
    let currentIndent = 0;

    for (const line of lines) {
      const indent = line.search(/\S/);
      const content = line.trim();

      if (content.startsWith('#')) continue;

      const match = content.match(/^(\w+):\s*(.*)$/);
      if (match) {
        const [, key, value] = match;
        if (value) {
          result[key] = value.replace(/^["']|["']$/g, '');
        } else {
          currentKey = key;
          currentIndent = indent;
        }
      }
    }

    return result;
  }
}

/**
 * Export singleton instance
 */
export const contextManager = new ContextManager();
