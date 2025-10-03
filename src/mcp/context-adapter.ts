/**
 * MCP Context Adapter
 * Manages context synchronization between AI-Shell and MCP servers
 */

import { EventEmitter } from 'eventemitter3';
import { v4 as uuidv4 } from 'uuid';
import { MCPContext } from './types';

/**
 * Context Change Event
 */
export interface ContextChangeEvent {
  type: 'update' | 'merge' | 'reset';
  context: Partial<MCPContext>;
  timestamp: number;
}

/**
 * Context Adapter Events
 */
export interface ContextAdapterEvents {
  contextChanged: (event: ContextChangeEvent) => void;
  contextSynced: (context: MCPContext) => void;
  contextError: (error: Error) => void;
}

/**
 * Context Snapshot
 */
export interface ContextSnapshot {
  id: string;
  context: MCPContext;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

/**
 * MCP Context Adapter
 */
export class MCPContextAdapter extends EventEmitter<ContextAdapterEvents> {
  private currentContext: MCPContext;
  private snapshots: ContextSnapshot[] = [];
  private maxSnapshots = 10;

  constructor(initialContext?: Partial<MCPContext>) {
    super();
    this.currentContext = this.createDefaultContext(initialContext);
  }

  /**
   * Create default context
   */
  private createDefaultContext(partial?: Partial<MCPContext>): MCPContext {
    return {
      sessionId: partial?.sessionId || uuidv4(),
      workingDirectory: partial?.workingDirectory || process.cwd(),
      environment: partial?.environment || { ...process.env },
      metadata: partial?.metadata || {},
      timestamp: Date.now()
    };
  }

  /**
   * Get current context
   */
  getContext(): MCPContext {
    return { ...this.currentContext };
  }

  /**
   * Update context
   */
  updateContext(updates: Partial<MCPContext>): MCPContext {
    const previousContext = { ...this.currentContext };

    this.currentContext = {
      ...this.currentContext,
      ...updates,
      timestamp: Date.now()
    };

    this.emit('contextChanged', {
      type: 'update',
      context: updates,
      timestamp: this.currentContext.timestamp
    });

    this.createSnapshot(previousContext);
    return this.getContext();
  }

  /**
   * Merge context data
   */
  mergeContext(partial: Partial<MCPContext>): MCPContext {
    const previousContext = { ...this.currentContext };

    // Deep merge metadata
    const mergedMetadata = {
      ...this.currentContext.metadata,
      ...partial.metadata
    };

    // Deep merge environment
    const mergedEnvironment = {
      ...this.currentContext.environment,
      ...partial.environment
    };

    this.currentContext = {
      ...this.currentContext,
      ...partial,
      metadata: mergedMetadata,
      environment: mergedEnvironment,
      timestamp: Date.now()
    };

    this.emit('contextChanged', {
      type: 'merge',
      context: partial,
      timestamp: this.currentContext.timestamp
    });

    this.createSnapshot(previousContext);
    return this.getContext();
  }

  /**
   * Reset context to defaults
   */
  resetContext(partial?: Partial<MCPContext>): MCPContext {
    const previousContext = { ...this.currentContext };
    this.currentContext = this.createDefaultContext(partial);

    this.emit('contextChanged', {
      type: 'reset',
      context: this.currentContext,
      timestamp: this.currentContext.timestamp
    });

    this.createSnapshot(previousContext);
    return this.getContext();
  }

  /**
   * Update working directory
   */
  setWorkingDirectory(directory: string): void {
    this.updateContext({ workingDirectory: directory });
  }

  /**
   * Update environment variables
   */
  setEnvironment(env: Record<string, string>): void {
    this.updateContext({ environment: env });
  }

  /**
   * Update metadata
   */
  setMetadata(metadata: Record<string, unknown>): void {
    this.updateContext({ metadata });
  }

  /**
   * Add metadata field
   */
  addMetadata(key: string, value: unknown): void {
    this.mergeContext({
      metadata: {
        [key]: value
      }
    });
  }

  /**
   * Remove metadata field
   */
  removeMetadata(key: string): void {
    const { [key]: _, ...remainingMetadata } = this.currentContext.metadata;
    this.updateContext({ metadata: remainingMetadata });
  }

  /**
   * Get metadata field
   */
  getMetadata(key: string): unknown {
    return this.currentContext.metadata[key];
  }

  /**
   * Create context snapshot
   */
  private createSnapshot(context: MCPContext): void {
    const snapshot: ContextSnapshot = {
      id: uuidv4(),
      context: { ...context },
      timestamp: Date.now()
    };

    this.snapshots.push(snapshot);

    // Limit snapshots
    if (this.snapshots.length > this.maxSnapshots) {
      this.snapshots.shift();
    }
  }

  /**
   * Get context snapshots
   */
  getSnapshots(): ContextSnapshot[] {
    return [...this.snapshots];
  }

  /**
   * Restore from snapshot
   */
  restoreSnapshot(snapshotId: string): MCPContext | null {
    const snapshot = this.snapshots.find((s) => s.id === snapshotId);

    if (!snapshot) {
      return null;
    }

    this.currentContext = { ...snapshot.context };
    this.emit('contextChanged', {
      type: 'reset',
      context: this.currentContext,
      timestamp: Date.now()
    });

    return this.getContext();
  }

  /**
   * Clear all snapshots
   */
  clearSnapshots(): void {
    this.snapshots = [];
  }

  /**
   * Export context as JSON
   */
  exportContext(): string {
    return JSON.stringify(this.currentContext, null, 2);
  }

  /**
   * Import context from JSON
   */
  importContext(json: string): MCPContext {
    try {
      const imported = JSON.parse(json) as MCPContext;
      return this.resetContext(imported);
    } catch (error) {
      const err = new Error(
        `Failed to import context: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
      this.emit('contextError', err);
      throw err;
    }
  }

  /**
   * Create context diff between two contexts
   */
  static diff(
    context1: MCPContext,
    context2: MCPContext
  ): Partial<MCPContext> {
    const diff: Partial<MCPContext> = {};

    if (context1.sessionId !== context2.sessionId) {
      diff.sessionId = context2.sessionId;
    }

    if (context1.workingDirectory !== context2.workingDirectory) {
      diff.workingDirectory = context2.workingDirectory;
    }

    // Compare environment
    const envDiff: Record<string, string> = {};
    for (const [key, value] of Object.entries(context2.environment)) {
      if (context1.environment[key] !== value) {
        envDiff[key] = value;
      }
    }
    if (Object.keys(envDiff).length > 0) {
      diff.environment = envDiff;
    }

    // Compare metadata
    const metaDiff: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(context2.metadata)) {
      if (JSON.stringify(context1.metadata[key]) !== JSON.stringify(value)) {
        metaDiff[key] = value;
      }
    }
    if (Object.keys(metaDiff).length > 0) {
      diff.metadata = metaDiff;
    }

    return diff;
  }

  /**
   * Validate context structure
   */
  static validate(context: unknown): context is MCPContext {
    if (typeof context !== 'object' || context === null) {
      return false;
    }

    const ctx = context as Partial<MCPContext>;

    return (
      typeof ctx.sessionId === 'string' &&
      typeof ctx.workingDirectory === 'string' &&
      typeof ctx.environment === 'object' &&
      ctx.environment !== null &&
      typeof ctx.metadata === 'object' &&
      ctx.metadata !== null &&
      typeof ctx.timestamp === 'number'
    );
  }

  /**
   * Create context from environment
   */
  static fromEnvironment(
    sessionId?: string,
    metadata?: Record<string, unknown>
  ): MCPContext {
    return {
      sessionId: sessionId || uuidv4(),
      workingDirectory: process.cwd(),
      environment: { ...process.env },
      metadata: metadata || {},
      timestamp: Date.now()
    };
  }

  /**
   * Create minimal context
   */
  static createMinimal(sessionId?: string): MCPContext {
    return {
      sessionId: sessionId || uuidv4(),
      workingDirectory: process.cwd(),
      environment: {},
      metadata: {},
      timestamp: Date.now()
    };
  }
}
