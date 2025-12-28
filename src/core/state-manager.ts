/**
 * Context-Aware State Manager
 * Manages application state with persistence, versioning, and context tracking
 *
 * Features:
 * - In-memory state storage with versioning
 * - File-based persistence with auto-save
 * - Snapshot management for rollback
 * - TTL support for temporary state
 * - Query capabilities with metadata
 * - Event-driven state changes
 * - Transaction support for atomic updates
 */

import { EventEmitter } from 'eventemitter3';
import * as fs from 'fs/promises';
import * as path from 'path';

/**
 * State entry
 */
export interface StateEntry<T = any> {
  key: string;
  value: T;
  version: number;
  timestamp: number;
  metadata: Record<string, any>;
  ttl?: number;
}

/**
 * State snapshot
 */
export interface StateSnapshot {
  id: string;
  state: Map<string, StateEntry>;
  timestamp: number;
  description?: string;
}

/**
 * State change event
 */
export interface StateChange<T = any> {
  key: string;
  oldValue?: T;
  newValue: T;
  version: number;
  timestamp: number;
}

/**
 * State manager events
 */
export interface StateManagerEvents {
  stateChange: (change: StateChange) => void;
  stateSet: (key: string, value: any) => void;
  stateDelete: (key: string) => void;
  stateClear: () => void;
  snapshotCreated: (snapshot: StateSnapshot) => void;
  snapshotRestored: (snapshotId: string) => void;
  persistence: (action: 'save' | 'load', success: boolean) => void;
}

/**
 * State manager configuration
 */
export interface StateManagerConfig {
  enablePersistence?: boolean;
  persistencePath?: string;
  autoSaveInterval?: number;
  maxSnapshots?: number;
  enableVersioning?: boolean;
  enableTTL?: boolean;
  ttlCheckInterval?: number;
}

/**
 * Context-Aware State Manager
 */
export class StateManager extends EventEmitter<StateManagerEvents> {
  private state = new Map<string, StateEntry>();
  private snapshots: StateSnapshot[] = [];
  private config: Required<StateManagerConfig>;
  private autoSaveTimer: NodeJS.Timeout | null = null;
  private ttlCheckTimer: NodeJS.Timeout | null = null;
  private versionCounter = 0;

  constructor(config: StateManagerConfig = {}) {
    super();
    this.config = {
      enablePersistence: config.enablePersistence !== false,
      persistencePath: config.persistencePath || './.state',
      autoSaveInterval: config.autoSaveInterval || 5000,
      maxSnapshots: config.maxSnapshots || 10,
      enableVersioning: config.enableVersioning !== false,
      enableTTL: config.enableTTL !== false,
      ttlCheckInterval: config.ttlCheckInterval || 10000
    };

    this.initialize();
  }

  /**
   * Initialize state manager
   */
  private async initialize(): Promise<void> {
    // Load persisted state
    if (this.config.enablePersistence) {
      await this.load();
      this.startAutoSave();
    }

    // Start TTL checker
    if (this.config.enableTTL) {
      this.startTTLChecker();
    }
  }

  /**
   * Set state value
   */
  set<T = any>(key: string, value: T, options?: { ttl?: number; metadata?: Record<string, any> }): void {
    const oldEntry = this.state.get(key);
    const version = this.config.enableVersioning ? ++this.versionCounter : 1;

    const entry: StateEntry<T> = {
      key,
      value,
      version,
      timestamp: Date.now(),
      metadata: options?.metadata || {},
      ttl: options?.ttl
    };

    this.state.set(key, entry);

    // Emit events
    this.emit('stateSet', key, value);

    if (oldEntry) {
      this.emit('stateChange', {
        key,
        oldValue: oldEntry.value,
        newValue: value,
        version,
        timestamp: entry.timestamp
      });
    }
  }

  /**
   * Get state value
   */
  get<T = any>(key: string): T | undefined {
    const entry = this.state.get(key);

    if (!entry) {
      return undefined;
    }

    // Check TTL
    if (this.config.enableTTL && entry.ttl) {
      const age = Date.now() - entry.timestamp;
      if (age > entry.ttl) {
        this.delete(key);
        return undefined;
      }
    }

    return entry.value as T;
  }

  /**
   * Get state entry with metadata
   */
  getEntry(key: string): StateEntry | undefined {
    return this.state.get(key);
  }

  /**
   * Check if key exists
   */
  has(key: string): boolean {
    return this.state.has(key);
  }

  /**
   * Delete state value
   */
  delete(key: string): boolean {
    const deleted = this.state.delete(key);
    if (deleted) {
      this.emit('stateDelete', key);
    }
    return deleted;
  }

  /**
   * Clear all state
   */
  clear(): void {
    this.state.clear();
    this.emit('stateClear');
  }

  /**
   * Get all keys
   */
  keys(): string[] {
    return Array.from(this.state.keys());
  }

  /**
   * Get all values
   */
  values(): any[] {
    return Array.from(this.state.values()).map((entry) => entry.value);
  }

  /**
   * Get all entries
   */
  entries(): Array<[string, any]> {
    return Array.from(this.state.entries()).map(([key, entry]) => [key, entry.value]);
  }

  /**
   * Get state size
   */
  size(): number {
    return this.state.size;
  }

  /**
   * Update existing state value
   */
  update<T = any>(key: string, updater: (current: T) => T): void {
    const current = this.get<T>(key);
    if (current !== undefined) {
      const updated = updater(current);
      this.set(key, updated);
    }
  }

  /**
   * Set if not exists
   */
  setIfNotExists<T = any>(key: string, value: T, options?: { ttl?: number; metadata?: Record<string, any> }): boolean {
    if (!this.has(key)) {
      this.set(key, value, options);
      return true;
    }
    return false;
  }

  /**
   * Get or set default value
   */
  getOrSet<T = any>(key: string, defaultValue: T, options?: { ttl?: number; metadata?: Record<string, any> }): T {
    let value = this.get<T>(key);
    if (value === undefined) {
      this.set(key, defaultValue, options);
      value = defaultValue;
    }
    return value;
  }

  /**
   * Create state snapshot
   */
  createSnapshot(description?: string): StateSnapshot {
    const snapshot: StateSnapshot = {
      id: this.generateSnapshotId(),
      state: new Map(this.state),
      timestamp: Date.now(),
      description
    };

    this.snapshots.push(snapshot);

    // Limit snapshots
    if (this.snapshots.length > this.config.maxSnapshots) {
      this.snapshots.shift();
    }

    this.emit('snapshotCreated', snapshot);
    return snapshot;
  }

  /**
   * Restore from snapshot
   */
  restoreSnapshot(snapshotId: string): boolean {
    const snapshot = this.snapshots.find((s) => s.id === snapshotId);

    if (!snapshot) {
      return false;
    }

    this.state = new Map(snapshot.state);
    this.emit('snapshotRestored', snapshotId);
    return true;
  }

  /**
   * Get all snapshots
   */
  getSnapshots(): StateSnapshot[] {
    return [...this.snapshots];
  }

  /**
   * Get snapshot by ID
   */
  getSnapshot(snapshotId: string): StateSnapshot | undefined {
    return this.snapshots.find((s) => s.id === snapshotId);
  }

  /**
   * Delete snapshot
   */
  deleteSnapshot(snapshotId: string): boolean {
    const index = this.snapshots.findIndex((s) => s.id === snapshotId);
    if (index >= 0) {
      this.snapshots.splice(index, 1);
      return true;
    }
    return false;
  }

  /**
   * Query state by predicate
   */
  query<T = any>(predicate: (entry: StateEntry) => boolean): Array<StateEntry<T>> {
    const results: Array<StateEntry<T>> = [];

    for (const entry of this.state.values()) {
      if (predicate(entry)) {
        results.push(entry as StateEntry<T>);
      }
    }

    return results;
  }

  /**
   * Find state by metadata
   */
  findByMetadata(metadataKey: string, metadataValue: any): StateEntry[] {
    return this.query((entry) => entry.metadata[metadataKey] === metadataValue);
  }

  /**
   * Get state by key prefix
   */
  getByPrefix<T = any>(prefix: string): Map<string, T> {
    const results = new Map<string, T>();

    for (const [key, entry] of this.state.entries()) {
      if (key.startsWith(prefix)) {
        results.set(key, entry.value as T);
      }
    }

    return results;
  }

  /**
   * Delete by key prefix
   */
  deleteByPrefix(prefix: string): number {
    let count = 0;

    for (const key of this.state.keys()) {
      if (key.startsWith(prefix)) {
        this.delete(key);
        count++;
      }
    }

    return count;
  }

  /**
   * Save state to disk
   */
  async save(): Promise<void> {
    if (!this.config.enablePersistence) {
      return;
    }

    try {
      const data = {
        state: Array.from(this.state.entries()),
        snapshots: this.snapshots,
        version: this.versionCounter,
        timestamp: Date.now()
      };

      const json = JSON.stringify(data, null, 2);
      await fs.mkdir(path.dirname(this.config.persistencePath), { recursive: true });
      await fs.writeFile(this.config.persistencePath, json, 'utf-8');

      this.emit('persistence', 'save', true);
    } catch (error) {
      console.error('Failed to save state:', error);
      this.emit('persistence', 'save', false);
      throw error;
    }
  }

  /**
   * Load state from disk
   */
  async load(): Promise<void> {
    if (!this.config.enablePersistence) {
      return;
    }

    try {
      const json = await fs.readFile(this.config.persistencePath, 'utf-8');
      const data = JSON.parse(json);

      this.state = new Map(data.state);
      this.snapshots = data.snapshots || [];
      this.versionCounter = data.version || 0;

      this.emit('persistence', 'load', true);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') {
        console.error('Failed to load state:', error);
        this.emit('persistence', 'load', false);
      }
    }
  }

  /**
   * Start auto-save timer
   */
  private startAutoSave(): void {
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer);
    }

    this.autoSaveTimer = setInterval(() => {
      this.save().catch((error) => {
        console.error('Auto-save failed:', error);
      });
    }, this.config.autoSaveInterval);
  }

  /**
   * Stop auto-save timer
   */
  private stopAutoSave(): void {
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer);
      this.autoSaveTimer = null;
    }
  }

  /**
   * Start TTL checker
   */
  private startTTLChecker(): void {
    if (this.ttlCheckTimer) {
      clearInterval(this.ttlCheckTimer);
    }

    this.ttlCheckTimer = setInterval(() => {
      this.checkTTL();
    }, this.config.ttlCheckInterval);
  }

  /**
   * Stop TTL checker
   */
  private stopTTLChecker(): void {
    if (this.ttlCheckTimer) {
      clearInterval(this.ttlCheckTimer);
      this.ttlCheckTimer = null;
    }
  }

  /**
   * Check and remove expired entries
   */
  private checkTTL(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [key, entry] of this.state.entries()) {
      if (entry.ttl) {
        const age = now - entry.timestamp;
        if (age > entry.ttl) {
          expiredKeys.push(key);
        }
      }
    }

    // Delete expired entries
    expiredKeys.forEach((key) => this.delete(key));
  }

  /**
   * Generate snapshot ID
   */
  private generateSnapshotId(): string {
    return `snapshot_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get statistics
   */
  getStatistics(): {
    size: number;
    snapshots: number;
    version: number;
    oldestEntry: number | null;
    newestEntry: number | null;
    averageAge: number;
  } {
    const entries = Array.from(this.state.values());
    const timestamps = entries.map((e) => e.timestamp);

    return {
      size: this.state.size,
      snapshots: this.snapshots.length,
      version: this.versionCounter,
      oldestEntry: timestamps.length > 0 ? Math.min(...timestamps) : null,
      newestEntry: timestamps.length > 0 ? Math.max(...timestamps) : null,
      averageAge:
        timestamps.length > 0 ? (Date.now() - timestamps.reduce((a, b) => a + b, 0) / timestamps.length) : 0
    };
  }

  /**
   * Export state as JSON
   */
  export(): string {
    const data = {
      state: Object.fromEntries(this.state.entries()),
      statistics: this.getStatistics()
    };
    return JSON.stringify(data, null, 2);
  }

  /**
   * Import state from JSON
   */
  import(json: string): void {
    try {
      const data = JSON.parse(json);
      this.state = new Map(Object.entries(data.state));
    } catch (error) {
      throw new Error(`Failed to import state: ${error}`);
    }
  }

  /**
   * Begin transaction
   */
  beginTransaction(): StateTransaction {
    return new StateTransaction(this);
  }

  /**
   * Batch update multiple keys
   */
  batchSet(entries: Array<{ key: string; value: any; options?: { ttl?: number; metadata?: Record<string, any> } }>): void {
    for (const entry of entries) {
      this.set(entry.key, entry.value, entry.options);
    }
  }

  /**
   * Batch delete multiple keys
   */
  batchDelete(keys: string[]): number {
    let deleted = 0;
    for (const key of keys) {
      if (this.delete(key)) {
        deleted++;
      }
    }
    return deleted;
  }

  /**
   * Merge state from another state manager
   */
  merge(other: StateManager, overwrite = false): void {
    for (const [key, entry] of other.state.entries()) {
      if (!this.has(key) || overwrite) {
        this.state.set(key, { ...entry });
      }
    }
  }

  /**
   * Diff two state snapshots
   */
  diff(snapshotId1: string, snapshotId2: string): {
    added: string[];
    removed: string[];
    changed: string[];
  } {
    const snapshot1 = this.getSnapshot(snapshotId1);
    const snapshot2 = this.getSnapshot(snapshotId2);

    if (!snapshot1 || !snapshot2) {
      throw new Error('One or both snapshots not found');
    }

    const keys1 = new Set(snapshot1.state.keys());
    const keys2 = new Set(snapshot2.state.keys());

    const added: string[] = [];
    const removed: string[] = [];
    const changed: string[] = [];

    // Find added and changed
    for (const key of keys2) {
      if (!keys1.has(key)) {
        added.push(key);
      } else {
        const val1 = snapshot1.state.get(key)?.value;
        const val2 = snapshot2.state.get(key)?.value;
        if (JSON.stringify(val1) !== JSON.stringify(val2)) {
          changed.push(key);
        }
      }
    }

    // Find removed
    for (const key of keys1) {
      if (!keys2.has(key)) {
        removed.push(key);
      }
    }

    return { added, removed, changed };
  }

  /**
   * Shutdown state manager
   */
  async shutdown(): Promise<void> {
    this.stopAutoSave();
    this.stopTTLChecker();

    if (this.config.enablePersistence) {
      await this.save();
    }
  }
}

/**
 * State transaction for atomic updates
 */
export class StateTransaction {
  private operations: Array<{ type: 'set' | 'delete'; key: string; value?: any; options?: any }> = [];
  private executed = false;

  constructor(private stateManager: StateManager) {}

  /**
   * Add set operation to transaction
   */
  set<T = any>(key: string, value: T, options?: { ttl?: number; metadata?: Record<string, any> }): this {
    if (this.executed) {
      throw new Error('Transaction already executed');
    }
    this.operations.push({ type: 'set', key, value, options });
    return this;
  }

  /**
   * Add delete operation to transaction
   */
  delete(key: string): this {
    if (this.executed) {
      throw new Error('Transaction already executed');
    }
    this.operations.push({ type: 'delete', key });
    return this;
  }

  /**
   * Execute all operations atomically
   */
  commit(): void {
    if (this.executed) {
      throw new Error('Transaction already executed');
    }

    // Create snapshot for rollback
    const snapshot = this.stateManager.createSnapshot('transaction-backup');

    try {
      for (const op of this.operations) {
        if (op.type === 'set') {
          this.stateManager.set(op.key, op.value, op.options);
        } else if (op.type === 'delete') {
          this.stateManager.delete(op.key);
        }
      }
      this.executed = true;
    } catch (error) {
      // Rollback on error
      this.stateManager.restoreSnapshot(snapshot.id);
      throw error;
    }
  }

  /**
   * Cancel transaction
   */
  rollback(): void {
    this.operations = [];
    this.executed = true;
  }
}
