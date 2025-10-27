/**
 * MCP Context Adapter
 * Manages context transformation, compression, validation, and versioning
 */

import { EventEmitter } from 'eventemitter3';
import { v4 as uuidv4 } from 'uuid';
import { MCPContext, ContextFormat } from './types';
import * as zlib from 'zlib';
import { promisify } from 'util';

const gzipAsync = promisify(zlib.gzip);
const gunzipAsync = promisify(zlib.gunzip);
const brotliCompressAsync = promisify(zlib.brotliCompress);
const brotliDecompressAsync = promisify(zlib.brotliDecompress);

// Re-export ContextFormat for convenience
export { ContextFormat } from './types';

/**
 * Context Adapter Configuration
 */
export interface ContextAdapterConfig {
  format?: ContextFormat;
  maxSize?: number;
  compression?: boolean;
  maxVersions?: number;
}

/**
 * Merge Options
 */
export interface MergeOptions {
  arrayMergeStrategy?: 'replace' | 'concat';
}

/**
 * Context Diff Result
 */
export interface ContextDiff {
  changed: Array<{
    path: string;
    oldValue: any;
    newValue: any;
  }>;
  added: string[];
  removed: string[];
}

/**
 * Context Version Entry
 */
interface ContextVersion {
  sessionId: string;
  version: string;
  context: MCPContext;
  timestamp: number;
}

/**
 * Context Adapter
 * Handles context transformation, compression, validation, and versioning
 */
export class ContextAdapter {
  private config: Required<ContextAdapterConfig>;
  private transformCache: Map<string, any> = new Map();
  private versions: Map<string, ContextVersion[]> = new Map();
  private sensitiveFields = ['password', 'apiKey', 'secret', 'token', 'accessToken', 'refreshToken'];

  constructor(config: ContextAdapterConfig = {}) {
    this.config = {
      format: config.format || ContextFormat.JSON,
      maxSize: config.maxSize || 1024 * 1024, // 1MB default
      compression: config.compression !== undefined ? config.compression : false,
      maxVersions: config.maxVersions || 10,
    };
  }

  /**
   * Transform context to specified format
   */
  transform(context: any, format: ContextFormat): any {
    switch (format) {
      case ContextFormat.JSON:
        return JSON.stringify(context);

      case ContextFormat.BINARY:
        const jsonStr = JSON.stringify(context);
        return Buffer.from(jsonStr, 'utf8');

      case ContextFormat.MSGPACK:
        // Simple MessagePack-like encoding (basic implementation)
        const json = JSON.stringify(context);
        const buffer = Buffer.from(json, 'utf8');
        // Add a simple header to distinguish from regular binary
        const header = Buffer.from([0x93]); // MessagePack array marker
        return Buffer.concat([header, buffer]);

      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }

  /**
   * Parse transformed context
   */
  parse(data: any, format: ContextFormat): any {
    try {
      switch (format) {
        case ContextFormat.JSON:
          return JSON.parse(data);

        case ContextFormat.BINARY:
          if (!Buffer.isBuffer(data)) {
            throw new Error('Invalid binary data');
          }
          const jsonStr = data.toString('utf8');
          return JSON.parse(jsonStr);

        case ContextFormat.MSGPACK:
          if (!Buffer.isBuffer(data)) {
            throw new Error('Invalid MessagePack data');
          }
          // Skip the header byte if present
          const payload = data[0] === 0x93 ? data.slice(1) : data;
          const str = payload.toString('utf8');
          return JSON.parse(str);

        default:
          throw new Error(`Unsupported format: ${format}`);
      }
    } catch (error) {
      throw new Error(`Failed to parse ${format} data: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Compress context data
   */
  compress(context: any): Buffer {
    const json = typeof context === 'string' ? context : JSON.stringify(context);
    return zlib.gzipSync(json);
  }

  /**
   * Decompress context data
   */
  decompress(data: Buffer): any {
    try {
      const decompressed = zlib.gunzipSync(data);
      const json = decompressed.toString('utf8');
      return JSON.parse(json);
    } catch (error) {
      throw new Error(`Failed to decompress data: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Validate context structure and size
   */
  validate(context: any, schema?: object): boolean {
    if (typeof context !== 'object' || context === null) {
      return false;
    }

    // Check for required fields
    if (!context.sessionId || typeof context.sessionId !== 'string') {
      return false;
    }

    // Check userId type if present
    if (context.userId !== undefined && typeof context.userId !== 'string') {
      return false;
    }

    // Check size limit
    const size = JSON.stringify(context).length;
    if (size > this.config.maxSize) {
      throw new Error(`Context size ${size} exceeds maximum size ${this.config.maxSize}`);
    }

    // If schema is provided, validate against it
    if (schema) {
      // Basic schema validation (can be extended)
      return this.validateSchema(context, schema);
    }

    return true;
  }

  /**
   * Basic schema validation
   */
  private validateSchema(data: any, schema: any): boolean {
    if (schema.type) {
      const actualType = Array.isArray(data) ? 'array' : typeof data;
      if (schema.type !== actualType) {
        return false;
      }
    }

    if (schema.properties && typeof data === 'object') {
      for (const [key, propSchema] of Object.entries(schema.properties as any)) {
        if (data[key] !== undefined && !this.validateSchema(data[key], propSchema)) {
          return false;
        }
      }
    }

    return true;
  }

  /**
   * Sanitize context by removing dangerous values
   */
  sanitize(context: any, options?: object): any {
    const sanitized = this.deepClone(context);
    this.sanitizeRecursive(sanitized);
    return sanitized;
  }

  /**
   * Recursively sanitize object
   */
  private sanitizeRecursive(obj: any): void {
    if (typeof obj !== 'object' || obj === null) {
      return;
    }

    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === 'string') {
        // Remove script tags
        obj[key] = value.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
        // Remove SQL injection patterns
        obj[key] = obj[key].replace(/(\bDROP\s+TABLE\b|\bDELETE\s+FROM\b|\bINSERT\s+INTO\b)/gi, '');
      } else if (typeof value === 'object' && value !== null) {
        this.sanitizeRecursive(value);
      }
    }
  }

  /**
   * Merge two contexts
   */
  merge(context1: any, context2: any, options?: MergeOptions): any {
    const strategy = options?.arrayMergeStrategy || 'replace';
    return this.deepMerge(context1, context2, strategy);
  }

  /**
   * Deep merge objects
   */
  private deepMerge(target: any, source: any, arrayStrategy: 'replace' | 'concat'): any {
    const result = { ...target };

    for (const key of Object.keys(source)) {
      if (source[key] === undefined) {
        continue;
      }

      if (Array.isArray(source[key])) {
        if (arrayStrategy === 'concat' && Array.isArray(target[key])) {
          result[key] = [...target[key], ...source[key]];
        } else {
          result[key] = source[key];
        }
      } else if (typeof source[key] === 'object' && source[key] !== null && !Buffer.isBuffer(source[key])) {
        if (typeof target[key] === 'object' && target[key] !== null) {
          result[key] = this.deepMerge(target[key], source[key], arrayStrategy);
        } else {
          result[key] = source[key];
        }
      } else {
        result[key] = source[key];
      }
    }

    return result;
  }

  /**
   * Calculate diff between two contexts
   */
  diff(context1: any, context2: any): ContextDiff {
    const diff: ContextDiff = {
      changed: [],
      added: [],
      removed: [],
    };

    this.diffRecursive(context1, context2, '', diff);

    return diff;
  }

  /**
   * Recursively calculate diff
   */
  private diffRecursive(obj1: any, obj2: any, path: string, diff: ContextDiff): void {
    const keys1 = obj1 && typeof obj1 === 'object' ? Object.keys(obj1) : [];
    const keys2 = obj2 && typeof obj2 === 'object' ? Object.keys(obj2) : [];
    const allKeys = new Set([...keys1, ...keys2]);

    for (const key of allKeys) {
      const currentPath = path ? `${path}.${key}` : key;
      const val1 = obj1?.[key];
      const val2 = obj2?.[key];

      if (!(key in obj1)) {
        diff.added.push(currentPath);
      } else if (!(key in obj2)) {
        diff.removed.push(currentPath);
      } else if (typeof val1 === 'object' && typeof val2 === 'object' && val1 !== null && val2 !== null) {
        if (JSON.stringify(val1) !== JSON.stringify(val2)) {
          if (Array.isArray(val1) || Array.isArray(val2)) {
            if (JSON.stringify(val1) !== JSON.stringify(val2)) {
              diff.changed.push({ path: currentPath, oldValue: val1, newValue: val2 });
            }
          } else {
            this.diffRecursive(val1, val2, currentPath, diff);
          }
        }
      } else if (val1 !== val2) {
        diff.changed.push({ path: currentPath, oldValue: val1, newValue: val2 });
      }
    }
  }

  /**
   * Apply diff to context
   */
  applyDiff(context: any, diff: ContextDiff): any {
    const result = this.deepClone(context);

    // Apply changes
    for (const change of diff.changed) {
      this.setValueByPath(result, change.path, change.newValue);
    }

    return result;
  }

  /**
   * Set value by path
   */
  private setValueByPath(obj: any, path: string, value: any): void {
    const parts = path.split('.');
    let current = obj;

    for (let i = 0; i < parts.length - 1; i++) {
      if (!(parts[i] in current)) {
        current[parts[i]] = {};
      }
      current = current[parts[i]];
    }

    current[parts[parts.length - 1]] = value;
  }

  /**
   * Save context version
   */
  saveVersion(context: MCPContext, version: string): void {
    const sessionId = context.sessionId;

    if (!this.versions.has(sessionId)) {
      this.versions.set(sessionId, []);
    }

    const versions = this.versions.get(sessionId)!;

    versions.push({
      sessionId,
      version,
      context: this.deepClone(context),
      timestamp: Date.now(),
    });

    // Limit versions
    if (versions.length > this.config.maxVersions) {
      versions.shift();
    }
  }

  /**
   * List versions for a session
   */
  listVersions(sessionId: string): string[] {
    const versions = this.versions.get(sessionId) || [];
    return versions.map(v => v.version);
  }

  /**
   * Restore context from version
   */
  restoreVersion(sessionId: string, version: string): MCPContext {
    const versions = this.versions.get(sessionId) || [];
    const versionEntry = versions.find(v => v.version === version);

    if (!versionEntry) {
      throw new Error(`Version ${version} not found for session ${sessionId}`);
    }

    return this.deepClone(versionEntry.context);
  }

  /**
   * Serialize context to string
   */
  serialize(context: any, options?: object): string {
    return JSON.stringify(context, this.getCircularReplacer());
  }

  /**
   * Deserialize context from string
   */
  deserialize(data: string, options?: object): any {
    return JSON.parse(data);
  }

  /**
   * Get circular reference replacer
   */
  private getCircularReplacer() {
    const seen = new WeakSet();
    return (key: string, value: any) => {
      if (typeof value === 'object' && value !== null) {
        if (seen.has(value)) {
          return '[Circular]';
        }
        seen.add(value);
      }
      return value;
    };
  }

  /**
   * Filter sensitive fields
   */
  filterSensitive(context: any, customFields?: string[]): any {
    const filtered = this.deepClone(context);
    const fields = customFields || this.sensitiveFields;
    this.filterSensitiveRecursive(filtered, fields);
    return filtered;
  }

  /**
   * Recursively filter sensitive fields
   */
  private filterSensitiveRecursive(obj: any, fields: string[]): void {
    if (typeof obj !== 'object' || obj === null) {
      return;
    }

    for (const [key, value] of Object.entries(obj)) {
      if (fields.some(field => key.toLowerCase().includes(field.toLowerCase()))) {
        obj[key] = '[REDACTED]';
      } else if (typeof value === 'object' && value !== null) {
        this.filterSensitiveRecursive(value, fields);
      }
    }
  }

  /**
   * Apply custom filter
   */
  filter(context: any, predicate: (key: string, value: any) => boolean): any {
    const filtered = this.deepClone(context);
    this.filterRecursive(filtered, predicate);
    return filtered;
  }

  /**
   * Recursively apply filter
   */
  private filterRecursive(obj: any, predicate: (key: string, value: any) => boolean): void {
    if (typeof obj !== 'object' || obj === null) {
      return;
    }

    for (const [key, value] of Object.entries(obj)) {
      if (!predicate(key, value)) {
        delete obj[key];
      } else if (typeof value === 'object' && value !== null) {
        this.filterRecursive(value, predicate);
      }
    }
  }

  /**
   * Deep clone context
   */
  clone(context: any): any {
    return this.deepClone(context);
  }

  /**
   * Clone with modifications
   */
  cloneWith(context: any, modifications: any): any {
    const cloned = this.deepClone(context);
    return this.deepMerge(cloned, modifications, 'replace');
  }

  /**
   * Deep clone helper
   */
  private deepClone(obj: any): any {
    if (obj === null || typeof obj !== 'object') {
      return obj;
    }

    if (obj instanceof Date) {
      return new Date(obj.getTime());
    }

    if (obj instanceof Buffer) {
      return Buffer.from(obj);
    }

    if (Array.isArray(obj)) {
      return obj.map(item => this.deepClone(item));
    }

    const cloned: any = {};
    for (const [key, value] of Object.entries(obj)) {
      cloned[key] = this.deepClone(value);
    }

    return cloned;
  }

  /**
   * Transform with caching
   */
  transformCached(context: any, format: ContextFormat): any {
    const key = JSON.stringify(context) + format;

    if (this.transformCache.has(key)) {
      return this.transformCache.get(key);
    }

    const transformed = this.transform(context, format);
    this.transformCache.set(key, transformed);

    // Limit cache size
    if (this.transformCache.size > 100) {
      const firstKey = this.transformCache.keys().next().value;
      if (firstKey !== undefined) {
        this.transformCache.delete(firstKey);
      }
    }

    return transformed;
  }

  /**
   * Clear transform cache
   */
  clearCache(): void {
    this.transformCache.clear();
  }
}

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
 * MCP Context Adapter (Legacy)
 * Maintains backward compatibility
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
    // Filter out undefined values from process.env
    const env: Record<string, string> = {};
    for (const [key, value] of Object.entries(process.env)) {
      if (value !== undefined) {
        env[key] = value;
      }
    }

    return {
      sessionId: partial?.sessionId || uuidv4(),
      workingDirectory: partial?.workingDirectory || process.cwd(),
      environment: partial?.environment || env,
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
      timestamp: this.currentContext.timestamp ?? Date.now()
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
      timestamp: this.currentContext.timestamp ?? Date.now()
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
      timestamp: this.currentContext.timestamp ?? Date.now()
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
    for (const [key, value] of Object.entries(context2.environment ?? {})) {
      if (context1.environment?.[key] !== value) {
        envDiff[key] = value;
      }
    }
    if (Object.keys(envDiff).length > 0) {
      diff.environment = envDiff;
    }

    // Compare metadata
    const metaDiff: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(context2.metadata ?? {})) {
      if (JSON.stringify(context1.metadata?.[key]) !== JSON.stringify(value)) {
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
    // Filter out undefined values from process.env
    const env: Record<string, string> = {};
    for (const [key, value] of Object.entries(process.env)) {
      if (value !== undefined) {
        env[key] = value;
      }
    }

    return {
      sessionId: sessionId || uuidv4(),
      workingDirectory: process.cwd(),
      environment: env,
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
