/**
 * Context Adapter Unit Tests
 * Tests context transformation, state persistence, and synchronization
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ContextAdapter } from '../../src/mcp/context-adapter';
import { MCPContext, ContextFormat } from '../../src/mcp/types';

describe('ContextAdapter', () => {
  let adapter: ContextAdapter;

  beforeEach(() => {
    adapter = new ContextAdapter({
      format: ContextFormat.JSON,
      maxSize: 1024 * 1024, // 1MB
      compression: true,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Context Transformation', () => {
    it('should transform context to JSON format', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          timestamp: Date.now(),
          version: '1.0.0',
        },
      };

      const transformed = adapter.transform(context, ContextFormat.JSON);

      expect(typeof transformed).toBe('string');
      const parsed = JSON.parse(transformed);
      expect(parsed.sessionId).toBe('test-session');
      expect(parsed.userId).toBe('user-123');
    });

    it('should transform context to binary format', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {},
      };

      const transformed = adapter.transform(context, ContextFormat.BINARY);

      expect(transformed).toBeInstanceOf(Buffer);
    });

    it('should transform context to MessagePack format', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: { key: 'value' },
      };

      const transformed = adapter.transform(context, ContextFormat.MSGPACK);

      expect(transformed).toBeDefined();
      expect(transformed.length).toBeGreaterThan(0);
    });

    it('should round-trip transform correctly', () => {
      const original: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          timestamp: Date.now(),
          nested: {
            key: 'value',
            array: [1, 2, 3],
          },
        },
      };

      const transformed = adapter.transform(original, ContextFormat.JSON);
      const restored = adapter.parse(transformed, ContextFormat.JSON);

      expect(restored).toEqual(original);
    });
  });

  describe('Context Compression', () => {
    it('should compress large contexts', () => {
      const largeContext: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          largeData: 'x'.repeat(10000),
        },
      };

      const compressed = adapter.compress(largeContext);
      const uncompressed = JSON.stringify(largeContext);

      expect(compressed.length).toBeLessThan(uncompressed.length);
    });

    it('should decompress correctly', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: { data: 'test data' },
      };

      const compressed = adapter.compress(context);
      const decompressed = adapter.decompress(compressed);

      expect(decompressed).toEqual(context);
    });

    it('should handle already compressed data', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {},
      };

      const compressed = adapter.compress(context);
      const doubleCompressed = adapter.compress(compressed as any);

      expect(() => adapter.decompress(doubleCompressed)).not.toThrow();
    });
  });

  describe('Context Validation', () => {
    it('should validate valid context', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {},
      };

      expect(adapter.validate(context)).toBe(true);
    });

    it('should reject context without session ID', () => {
      const context = {
        userId: 'user-123',
        metadata: {},
      } as any;

      expect(adapter.validate(context)).toBe(false);
    });

    it('should reject context exceeding size limit', () => {
      const largeContext: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          largeData: 'x'.repeat(2 * 1024 * 1024), // 2MB
        },
      };

      expect(() => adapter.validate(largeContext)).toThrow('exceeds maximum size');
    });

    it('should validate nested context structure', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          nested: {
            deeply: {
              nested: {
                value: 'test',
              },
            },
          },
        },
      };

      expect(adapter.validate(context)).toBe(true);
    });

    it('should sanitize dangerous values', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          script: '<script>alert("xss")</script>',
          sql: "'; DROP TABLE users; --",
        },
      };

      const sanitized = adapter.sanitize(context);

      expect(sanitized.metadata.script).not.toContain('<script>');
      expect(sanitized.metadata.sql).not.toContain('DROP TABLE');
    });
  });

  describe('Context Merging', () => {
    it('should merge contexts', () => {
      const context1: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          key1: 'value1',
          shared: 'original',
        },
      };

      const context2: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          key2: 'value2',
          shared: 'updated',
        },
      };

      const merged = adapter.merge(context1, context2);

      expect(merged.metadata.key1).toBe('value1');
      expect(merged.metadata.key2).toBe('value2');
      expect(merged.metadata.shared).toBe('updated'); // Should prefer second
    });

    it('should deep merge nested objects', () => {
      const context1: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          nested: {
            level1: {
              key1: 'value1',
            },
          },
        },
      };

      const context2: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          nested: {
            level1: {
              key2: 'value2',
            },
          },
        },
      };

      const merged = adapter.merge(context1, context2);

      expect(merged.metadata.nested.level1.key1).toBe('value1');
      expect(merged.metadata.nested.level1.key2).toBe('value2');
    });

    it('should handle array merging', () => {
      const context1: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          items: [1, 2, 3],
        },
      };

      const context2: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          items: [4, 5, 6],
        },
      };

      const merged = adapter.merge(context1, context2, { arrayMergeStrategy: 'concat' });

      expect(merged.metadata.items).toEqual([1, 2, 3, 4, 5, 6]);
    });
  });

  describe('Context Diffing', () => {
    it('should detect changes between contexts', () => {
      const context1: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          value: 'original',
        },
      };

      const context2: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          value: 'updated',
        },
      };

      const diff = adapter.diff(context1, context2);

      expect(diff.changed).toHaveLength(1);
      expect(diff.changed[0].path).toBe('metadata.value');
      expect(diff.changed[0].oldValue).toBe('original');
      expect(diff.changed[0].newValue).toBe('updated');
    });

    it('should detect added fields', () => {
      const context1: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {},
      };

      const context2: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          newField: 'value',
        },
      };

      const diff = adapter.diff(context1, context2);

      expect(diff.added).toContain('metadata.newField');
    });

    it('should detect removed fields', () => {
      const context1: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          oldField: 'value',
        },
      };

      const context2: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {},
      };

      const diff = adapter.diff(context1, context2);

      expect(diff.removed).toContain('metadata.oldField');
    });

    it('should apply diff to context', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          value: 'original',
        },
      };

      const diff = {
        changed: [
          {
            path: 'metadata.value',
            oldValue: 'original',
            newValue: 'updated',
          },
        ],
        added: ['metadata.newField'],
        removed: [],
      };

      const updated = adapter.applyDiff(context, diff);

      expect(updated.metadata.value).toBe('updated');
    });
  });

  describe('Context Versioning', () => {
    it('should track context versions', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {},
      };

      adapter.saveVersion(context, 'v1');
      adapter.saveVersion({ ...context, metadata: { updated: true } }, 'v2');

      const versions = adapter.listVersions('test-session');
      expect(versions).toHaveLength(2);
    });

    it('should restore context from version', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: { value: 'original' },
      };

      adapter.saveVersion(context, 'v1');

      const updatedContext = { ...context, metadata: { value: 'updated' } };
      adapter.saveVersion(updatedContext, 'v2');

      const restored = adapter.restoreVersion('test-session', 'v1');
      expect(restored.metadata.value).toBe('original');
    });

    it('should limit version history', () => {
      const limitedAdapter = new ContextAdapter({
        maxVersions: 3,
      });

      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {},
      };

      for (let i = 0; i < 5; i++) {
        limitedAdapter.saveVersion(context, `v${i}`);
      }

      const versions = limitedAdapter.listVersions('test-session');
      expect(versions).toHaveLength(3); // Should keep only last 3
    });
  });

  describe('Context Serialization', () => {
    it('should serialize to JSON correctly', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          date: new Date('2024-01-01'),
          buffer: Buffer.from('test'),
        },
      };

      const serialized = adapter.serialize(context);

      expect(typeof serialized).toBe('string');
      expect(() => JSON.parse(serialized)).not.toThrow();
    });

    it('should handle circular references', () => {
      const context: any = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {},
      };

      context.metadata.circular = context;

      expect(() => adapter.serialize(context)).not.toThrow();
    });

    it('should deserialize correctly', () => {
      const original: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          nested: { key: 'value' },
        },
      };

      const serialized = adapter.serialize(original);
      const deserialized = adapter.deserialize(serialized);

      expect(deserialized).toEqual(original);
    });
  });

  describe('Context Filtering', () => {
    it('should filter sensitive fields', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          password: 'secret',
          apiKey: 'sk-123456',
          publicData: 'visible',
        },
      };

      const filtered = adapter.filterSensitive(context);

      expect(filtered.metadata.password).toBe('[REDACTED]');
      expect(filtered.metadata.apiKey).toBe('[REDACTED]');
      expect(filtered.metadata.publicData).toBe('visible');
    });

    it('should apply custom filters', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          debug: true,
          temporary: 'remove me',
        },
      };

      const filtered = adapter.filter(context, (key, value) => {
        return key !== 'temporary';
      });

      expect(filtered.metadata.debug).toBe(true);
      expect(filtered.metadata.temporary).toBeUndefined();
    });
  });

  describe('Context Cloning', () => {
    it('should deep clone context', () => {
      const original: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          nested: {
            array: [1, 2, 3],
            object: { key: 'value' },
          },
        },
      };

      const clone = adapter.clone(original);

      // Modify clone
      clone.metadata.nested.array.push(4);
      clone.metadata.nested.object.key = 'modified';

      // Original should be unchanged
      expect(original.metadata.nested.array).toHaveLength(3);
      expect(original.metadata.nested.object.key).toBe('value');
    });

    it('should clone with modifications', () => {
      const original: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {},
      };

      const clone = adapter.cloneWith(original, {
        userId: 'user-456',
        metadata: { added: 'field' },
      });

      expect(clone.sessionId).toBe('test-session');
      expect(clone.userId).toBe('user-456');
      expect(clone.metadata.added).toBe('field');
    });
  });

  describe('Performance', () => {
    it('should handle large contexts efficiently', () => {
      const largeContext: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {
          largeArray: Array.from({ length: 10000 }, (_, i) => ({ id: i, data: `item-${i}` })),
        },
      };

      const start = Date.now();
      const transformed = adapter.transform(largeContext, ContextFormat.JSON);
      const parsed = adapter.parse(transformed, ContextFormat.JSON);
      const duration = Date.now() - start;

      expect(duration).toBeLessThan(1000); // Should complete in under 1 second
      expect(parsed.metadata.largeArray).toHaveLength(10000);
    });

    it('should cache transformed contexts', () => {
      const context: MCPContext = {
        sessionId: 'test-session',
        userId: 'user-123',
        metadata: {},
      };

      const transformSpy = vi.spyOn(adapter, 'transform');

      // First call
      adapter.transformCached(context, ContextFormat.JSON);

      // Second call - should use cache
      adapter.transformCached(context, ContextFormat.JSON);

      expect(transformSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe('Error Handling', () => {
    it('should handle malformed JSON', () => {
      const malformed = '{ invalid json }';

      expect(() => adapter.parse(malformed, ContextFormat.JSON)).toThrow();
    });

    it('should handle corrupted binary data', () => {
      const corrupted = Buffer.from('corrupted data');

      expect(() => adapter.parse(corrupted, ContextFormat.BINARY)).toThrow();
    });

    it('should validate context schema', () => {
      const invalid = {
        sessionId: 123, // Should be string
        userId: 'user-123',
        metadata: {},
      } as any;

      expect(adapter.validate(invalid)).toBe(false);
    });
  });
});

// Export types
export enum ContextFormat {
  JSON = 'json',
  BINARY = 'binary',
  MSGPACK = 'msgpack',
}
