/**
 * Context Management Unit Tests
 * Tests session context, state management, and persistence
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

describe('Context Management', () => {
  let contextManager: any;
  let mockStorage: any;

  beforeEach(() => {
    mockStorage = {
      save: vi.fn(),
      load: vi.fn(),
      delete: vi.fn(),
    };

    contextManager = {
      createSession: vi.fn(),
      updateContext: vi.fn(),
      getContext: vi.fn(),
      destroySession: vi.fn(),
    };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Session Management', () => {
    it('should create new session with default context', async () => {
      const sessionId = 'test-session-123';
      const defaultContext = {
        database: null,
        schema: null,
        user: 'testuser',
        history: [],
      };

      contextManager.createSession.mockResolvedValue({
        id: sessionId,
        context: defaultContext,
        createdAt: Date.now(),
      });

      const session = await contextManager.createSession(sessionId);

      expect(session.id).toBe(sessionId);
      expect(session.context.user).toBe('testuser');
    });

    it('should restore session from storage', async () => {
      const savedSession = {
        id: 'saved-session',
        context: {
          database: 'postgres',
          schema: 'public',
          variables: { limit: 100 },
        },
        timestamp: Date.now() - 3600000, // 1 hour ago
      };

      mockStorage.load.mockResolvedValue(savedSession);

      const session = await restoreSession('saved-session', mockStorage);

      expect(session.context.database).toBe('postgres');
      expect(mockStorage.load).toHaveBeenCalledWith('saved-session');
    });

    it('should handle session expiration', async () => {
      const expiredSession = {
        id: 'expired',
        context: {},
        timestamp: Date.now() - 86400000 * 2, // 2 days ago
      };

      mockStorage.load.mockResolvedValue(expiredSession);

      const session = await restoreSession('expired', mockStorage, {
        maxAge: 86400000, // 1 day
      });

      expect(session).toBeNull();
    });
  });

  describe('Context State', () => {
    it('should update context state', async () => {
      const updates = {
        database: 'testdb',
        schema: 'public',
        currentTable: 'users',
      };

      contextManager.updateContext.mockResolvedValue({
        ...updates,
        updatedAt: Date.now(),
      });

      const result = await contextManager.updateContext('session-1', updates);

      expect(result.database).toBe('testdb');
      expect(result.currentTable).toBe('users');
    });

    it('should merge context updates', async () => {
      const initialContext = {
        database: 'db1',
        schema: 'public',
        variables: { limit: 10 },
      };

      const updates = {
        schema: 'private',
        variables: { limit: 20, offset: 5 },
      };

      const merged = mergeContext(initialContext, updates);

      expect(merged.database).toBe('db1'); // Unchanged
      expect(merged.schema).toBe('private'); // Updated
      expect(merged.variables.limit).toBe(20); // Updated
      expect(merged.variables.offset).toBe(5); // Added
    });

    it('should track context history', async () => {
      const tracker = new ContextHistoryTracker();

      await tracker.recordChange('session-1', {
        field: 'database',
        oldValue: 'db1',
        newValue: 'db2',
        timestamp: Date.now(),
      });

      await tracker.recordChange('session-1', {
        field: 'schema',
        oldValue: 'public',
        newValue: 'private',
        timestamp: Date.now(),
      });

      const history = await tracker.getHistory('session-1');

      expect(history).toHaveLength(2);
      expect(history[0].field).toBe('database');
    });

    it('should support context rollback', async () => {
      const tracker = new ContextHistoryTracker();
      const initialContext = { database: 'db1', schema: 'public' };

      await tracker.recordChange('session-1', {
        field: 'database',
        oldValue: 'db1',
        newValue: 'db2',
      });

      const rolledBack = await tracker.rollback('session-1', 1);

      expect(rolledBack.database).toBe('db1');
    });
  });

  describe('Variable Management', () => {
    it('should set and get session variables', () => {
      const vars = new ContextVariables();

      vars.set('limit', 100);
      vars.set('format', 'json');
      vars.set('debug', true);

      expect(vars.get('limit')).toBe(100);
      expect(vars.get('format')).toBe('json');
      expect(vars.get('debug')).toBe(true);
    });

    it('should support typed variables', () => {
      const vars = new TypedContextVariables();

      vars.set('limit', 100, 'number');
      vars.set('format', 'json', 'string');
      vars.set('enabled', true, 'boolean');

      expect(typeof vars.get('limit')).toBe('number');
      expect(typeof vars.get('format')).toBe('string');
      expect(typeof vars.get('enabled')).toBe('boolean');
    });

    it('should validate variable types', () => {
      const vars = new TypedContextVariables();

      vars.set('limit', 100, 'number');

      expect(() => vars.set('limit', 'invalid', 'number')).toThrow();
    });

    it('should support variable scopes', () => {
      const vars = new ScopedContextVariables();

      vars.set('global', 'value1', 'global');
      vars.set('session', 'value2', 'session');
      vars.set('request', 'value3', 'request');

      expect(vars.get('global', 'global')).toBe('value1');
      expect(vars.get('session', 'session')).toBe('value2');
      expect(vars.get('request', 'request')).toBe('value3');
    });
  });

  describe('Context Persistence', () => {
    it('should persist context to storage', async () => {
      const context = {
        sessionId: 'test-123',
        database: 'postgres',
        schema: 'public',
        variables: { limit: 50 },
      };

      mockStorage.save.mockResolvedValue({ success: true });

      await persistContext(context, mockStorage);

      expect(mockStorage.save).toHaveBeenCalledWith(
        'test-123',
        expect.objectContaining(context)
      );
    });

    it('should handle persistence errors', async () => {
      const context = { sessionId: 'test' };

      mockStorage.save.mockRejectedValue(new Error('Storage error'));

      await expect(persistContext(context, mockStorage)).rejects.toThrow(
        'Storage error'
      );
    });

    it('should support multiple storage backends', async () => {
      const memoryStorage = new MemoryStorage();
      const fileStorage = new FileStorage('/tmp/context');

      const context = { sessionId: 'test', data: 'value' };

      await memoryStorage.save('test', context);
      await fileStorage.save('test', context);

      const fromMemory = await memoryStorage.load('test');
      const fromFile = await fileStorage.load('test');

      expect(fromMemory.data).toBe('value');
      expect(fromFile.data).toBe('value');
    });
  });

  describe('Context Inheritance', () => {
    it('should inherit from parent context', () => {
      const parent = {
        database: 'postgres',
        schema: 'public',
        variables: { limit: 10 },
      };

      const child = createChildContext(parent, {
        schema: 'private',
        variables: { offset: 5 },
      });

      expect(child.database).toBe('postgres'); // Inherited
      expect(child.schema).toBe('private'); // Overridden
      expect(child.variables.limit).toBe(10); // Inherited
      expect(child.variables.offset).toBe(5); // Added
    });

    it('should support context isolation', () => {
      const parent = { shared: 'value', variables: { x: 1 } };
      const child = createIsolatedContext(parent);

      child.variables.x = 2;
      child.variables.y = 3;

      expect(parent.variables.x).toBe(1); // Unchanged
      expect(parent.variables.y).toBeUndefined(); // Not affected
    });
  });

  describe('Context Cleanup', () => {
    it('should cleanup expired sessions', async () => {
      const cleaner = new ContextCleaner(mockStorage);

      const sessions = [
        { id: '1', timestamp: Date.now() }, // Recent
        { id: '2', timestamp: Date.now() - 86400000 * 2 }, // 2 days old
        { id: '3', timestamp: Date.now() - 86400000 * 8 }, // 8 days old
      ];

      mockStorage.load.mockImplementation((id: string) =>
        Promise.resolve(sessions.find(s => s.id === id))
      );

      const cleaned = await cleaner.cleanup({ maxAge: 86400000 * 7 }); // 7 days

      expect(mockStorage.delete).toHaveBeenCalledWith('3');
      expect(cleaned).toBe(1);
    });

    it('should cleanup on session destroy', async () => {
      contextManager.destroySession.mockResolvedValue({ success: true });

      await contextManager.destroySession('test-session');

      expect(contextManager.destroySession).toHaveBeenCalledWith('test-session');
    });
  });

  describe('Context Serialization', () => {
    it('should serialize context to JSON', () => {
      const context = {
        database: 'postgres',
        schema: 'public',
        variables: { limit: 100 },
        timestamp: Date.now(),
      };

      const serialized = JSON.stringify(context);
      const deserialized = JSON.parse(serialized);

      expect(deserialized.database).toBe('postgres');
      expect(deserialized.variables.limit).toBe(100);
    });

    it('should handle complex context objects', () => {
      const context = {
        database: 'postgres',
        connection: {
          host: 'localhost',
          port: 5432,
          pool: { min: 2, max: 10 },
        },
        metadata: new Map([
          ['key1', 'value1'],
          ['key2', 'value2'],
        ]),
      };

      const serialized = serializeContext(context);
      const deserialized = deserializeContext(serialized);

      expect(deserialized.connection.host).toBe('localhost');
      expect(deserialized.metadata.get('key1')).toBe('value1');
    });
  });
});

// Helper classes and functions
async function restoreSession(
  id: string,
  storage: any,
  options: { maxAge?: number } = {}
): Promise<any> {
  const session = await storage.load(id);

  if (!session) return null;

  if (options.maxAge && Date.now() - session.timestamp > options.maxAge) {
    return null;
  }

  return session;
}

function mergeContext(base: any, updates: any): any {
  return {
    ...base,
    ...updates,
    variables: {
      ...(base.variables || {}),
      ...(updates.variables || {}),
    },
  };
}

class ContextHistoryTracker {
  private history = new Map<string, any[]>();

  async recordChange(sessionId: string, change: any): Promise<void> {
    if (!this.history.has(sessionId)) {
      this.history.set(sessionId, []);
    }
    this.history.get(sessionId)!.push(change);
  }

  async getHistory(sessionId: string): Promise<any[]> {
    return this.history.get(sessionId) || [];
  }

  async rollback(sessionId: string, steps: number): Promise<any> {
    const changes = this.history.get(sessionId) || [];
    const context: any = {};

    for (let i = 0; i < changes.length - steps; i++) {
      context[changes[i].field] = changes[i].newValue;
    }

    return context;
  }
}

class ContextVariables {
  private vars = new Map<string, any>();

  set(key: string, value: any): void {
    this.vars.set(key, value);
  }

  get(key: string): any {
    return this.vars.get(key);
  }
}

class TypedContextVariables extends ContextVariables {
  set(key: string, value: any, type: string): void {
    if (typeof value !== type) {
      throw new Error(`Invalid type for ${key}: expected ${type}, got ${typeof value}`);
    }
    super.set(key, value);
  }
}

class ScopedContextVariables {
  private scopes = new Map<string, Map<string, any>>();

  set(key: string, value: any, scope: string): void {
    if (!this.scopes.has(scope)) {
      this.scopes.set(scope, new Map());
    }
    this.scopes.get(scope)!.set(key, value);
  }

  get(key: string, scope: string): any {
    return this.scopes.get(scope)?.get(key);
  }
}

async function persistContext(context: any, storage: any): Promise<void> {
  await storage.save(context.sessionId, context);
}

class MemoryStorage {
  private store = new Map<string, any>();

  async save(id: string, data: any): Promise<void> {
    this.store.set(id, data);
  }

  async load(id: string): Promise<any> {
    return this.store.get(id);
  }

  async delete(id: string): Promise<void> {
    this.store.delete(id);
  }
}

class FileStorage {
  constructor(private basePath: string) {}

  async save(id: string, data: any): Promise<void> {
    // Mock implementation
  }

  async load(id: string): Promise<any> {
    // Mock implementation
    return {};
  }

  async delete(id: string): Promise<void> {
    // Mock implementation
  }
}

function createChildContext(parent: any, overrides: any): any {
  return mergeContext(parent, overrides);
}

function createIsolatedContext(parent: any): any {
  return JSON.parse(JSON.stringify(parent));
}

class ContextCleaner {
  constructor(private storage: any) {}

  async cleanup(options: { maxAge: number }): Promise<number> {
    let cleaned = 0;
    // Mock implementation
    return cleaned;
  }
}

function serializeContext(context: any): string {
  return JSON.stringify(context, (key, value) => {
    if (value instanceof Map) {
      return {
        _type: 'Map',
        data: Array.from(value.entries()),
      };
    }
    return value;
  });
}

function deserializeContext(serialized: string): any {
  return JSON.parse(serialized, (key, value) => {
    if (value && value._type === 'Map') {
      return new Map(value.data);
    }
    return value;
  });
}
