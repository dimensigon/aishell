/**
 * ResourceManager Unit Tests
 * Tests MCP resource management, caching, and lifecycle
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ResourceManager } from '../../src/mcp/resource-manager';
import { MCPResource, ResourceType } from '../../src/mcp/types';

describe('ResourceManager', () => {
  let manager: ResourceManager;

  beforeEach(() => {
    manager = new ResourceManager({
      cacheEnabled: true,
      cacheTTL: 5000,
      maxCacheSize: 100,
    });
  });

  afterEach(() => {
    manager.clear();
    vi.clearAllMocks();
  });

  describe('Resource Registration', () => {
    it('should register a new resource', () => {
      const resource: MCPResource = {
        uri: 'test://resource/1',
        name: 'Test Resource',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      };

      manager.register(resource);

      const retrieved = manager.get('test://resource/1');
      expect(retrieved).toEqual(resource);
    });

    it('should register multiple resources', () => {
      const resources: MCPResource[] = [
        {
          uri: 'test://resource/1',
          name: 'Resource 1',
          type: ResourceType.TEXT,
          mimeType: 'text/plain',
        },
        {
          uri: 'test://resource/2',
          name: 'Resource 2',
          type: ResourceType.BINARY,
          mimeType: 'application/octet-stream',
        },
      ];

      manager.registerBatch(resources);

      expect(manager.list()).toHaveLength(2);
    });

    it('should update existing resource', () => {
      const resource: MCPResource = {
        uri: 'test://resource/1',
        name: 'Original Name',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      };

      manager.register(resource);

      const updated = { ...resource, name: 'Updated Name' };
      manager.register(updated);

      const retrieved = manager.get('test://resource/1');
      expect(retrieved?.name).toBe('Updated Name');
    });

    it('should throw on invalid resource URI', () => {
      const resource: MCPResource = {
        uri: '',
        name: 'Invalid',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      };

      expect(() => manager.register(resource)).toThrow('Invalid resource URI');
    });
  });

  describe('Resource Retrieval', () => {
    beforeEach(() => {
      manager.register({
        uri: 'test://resource/1',
        name: 'Test Resource',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
        content: 'test content',
      });
    });

    it('should retrieve resource by URI', () => {
      const resource = manager.get('test://resource/1');

      expect(resource).toBeDefined();
      expect(resource?.name).toBe('Test Resource');
    });

    it('should return undefined for non-existent resource', () => {
      const resource = manager.get('test://nonexistent');

      expect(resource).toBeUndefined();
    });

    it('should list all resources', () => {
      manager.register({
        uri: 'test://resource/2',
        name: 'Resource 2',
        type: ResourceType.BINARY,
        mimeType: 'application/octet-stream',
      });

      const resources = manager.list();

      expect(resources).toHaveLength(2);
    });

    it('should filter resources by type', () => {
      manager.register({
        uri: 'test://resource/2',
        name: 'Binary Resource',
        type: ResourceType.BINARY,
        mimeType: 'application/octet-stream',
      });

      const textResources = manager.listByType(ResourceType.TEXT);
      const binaryResources = manager.listByType(ResourceType.BINARY);

      expect(textResources).toHaveLength(1);
      expect(binaryResources).toHaveLength(1);
    });

    it('should search resources by name pattern', () => {
      manager.register({
        uri: 'test://resource/2',
        name: 'Another Test Resource',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      });

      const results = manager.search('Test');

      expect(results).toHaveLength(2);
    });
  });

  describe('Resource Caching', () => {
    it('should cache resource content', async () => {
      const fetchFn = vi.fn(async () => 'fetched content');

      const content1 = await manager.getOrFetch(
        'test://resource/cached',
        fetchFn
      );
      const content2 = await manager.getOrFetch(
        'test://resource/cached',
        fetchFn
      );

      expect(content1).toBe('fetched content');
      expect(content2).toBe('fetched content');
      expect(fetchFn).toHaveBeenCalledTimes(1); // Only fetched once
    });

    it('should respect cache TTL', async () => {
      const shortTTLManager = new ResourceManager({
        cacheEnabled: true,
        cacheTTL: 100,
      });

      const fetchFn = vi.fn(async () => 'content');

      await shortTTLManager.getOrFetch('test://resource/ttl', fetchFn);

      // Wait for cache to expire
      await new Promise((resolve) => setTimeout(resolve, 150));

      await shortTTLManager.getOrFetch('test://resource/ttl', fetchFn);

      expect(fetchFn).toHaveBeenCalledTimes(2); // Fetched twice due to expiry
    });

    it('should evict old entries when cache is full', async () => {
      const smallCacheManager = new ResourceManager({
        cacheEnabled: true,
        maxCacheSize: 3,
      });

      const fetchFn = vi.fn(async (uri: string) => `content-${uri}`);

      // Fill cache
      await smallCacheManager.getOrFetch('test://1', () => fetchFn('1'));
      await smallCacheManager.getOrFetch('test://2', () => fetchFn('2'));
      await smallCacheManager.getOrFetch('test://3', () => fetchFn('3'));

      // This should evict the oldest entry
      await smallCacheManager.getOrFetch('test://4', () => fetchFn('4'));

      // First entry should have been evicted
      const stats = smallCacheManager.getCacheStats();
      expect(stats.size).toBe(3);
    });

    it('should invalidate cache for specific resource', async () => {
      const fetchFn = vi.fn(async () => 'content');

      await manager.getOrFetch('test://resource/invalidate', fetchFn);
      manager.invalidateCache('test://resource/invalidate');
      await manager.getOrFetch('test://resource/invalidate', fetchFn);

      expect(fetchFn).toHaveBeenCalledTimes(2);
    });

    it('should clear all cache', async () => {
      const fetchFn = vi.fn(async () => 'content');

      await manager.getOrFetch('test://resource/1', fetchFn);
      await manager.getOrFetch('test://resource/2', fetchFn);

      manager.clearCache();

      const stats = manager.getCacheStats();
      expect(stats.size).toBe(0);
    });
  });

  describe('Resource Watching', () => {
    it('should notify watchers on resource changes', () => {
      const watcher = vi.fn();

      manager.watch('test://resource/watch', watcher);

      manager.register({
        uri: 'test://resource/watch',
        name: 'Watched Resource',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      });

      expect(watcher).toHaveBeenCalledWith(
        expect.objectContaining({
          uri: 'test://resource/watch',
        })
      );
    });

    it('should support multiple watchers', () => {
      const watcher1 = vi.fn();
      const watcher2 = vi.fn();

      manager.watch('test://resource/watch', watcher1);
      manager.watch('test://resource/watch', watcher2);

      manager.register({
        uri: 'test://resource/watch',
        name: 'Watched Resource',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      });

      expect(watcher1).toHaveBeenCalled();
      expect(watcher2).toHaveBeenCalled();
    });

    it('should unwatch resources', () => {
      const watcher = vi.fn();

      manager.watch('test://resource/watch', watcher);
      manager.unwatch('test://resource/watch', watcher);

      manager.register({
        uri: 'test://resource/watch',
        name: 'Watched Resource',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      });

      expect(watcher).not.toHaveBeenCalled();
    });
  });

  describe('Resource Validation', () => {
    it('should validate resource structure', () => {
      const validResource: MCPResource = {
        uri: 'test://resource/valid',
        name: 'Valid Resource',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      };

      expect(manager.validate(validResource)).toBe(true);
    });

    it('should reject resources without required fields', () => {
      const invalidResource = {
        uri: 'test://resource/invalid',
        // Missing name
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      } as any;

      expect(manager.validate(invalidResource)).toBe(false);
    });

    it('should validate MIME types', () => {
      const resource: MCPResource = {
        uri: 'test://resource/mime',
        name: 'MIME Resource',
        type: ResourceType.TEXT,
        mimeType: 'invalid-mime-type',
      };

      expect(() => manager.register(resource)).toThrow('Invalid MIME type');
    });

    it('should validate URI format', () => {
      const resource: MCPResource = {
        uri: 'not-a-valid-uri',
        name: 'Invalid URI',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      };

      expect(() => manager.register(resource)).toThrow('Invalid URI format');
    });
  });

  describe('Resource Metadata', () => {
    it('should track creation timestamp', () => {
      const resource: MCPResource = {
        uri: 'test://resource/metadata',
        name: 'Metadata Resource',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      };

      manager.register(resource);

      const metadata = manager.getMetadata('test://resource/metadata');
      expect(metadata?.createdAt).toBeInstanceOf(Date);
    });

    it('should track last access time', async () => {
      const resource: MCPResource = {
        uri: 'test://resource/access',
        name: 'Access Resource',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      };

      manager.register(resource);

      await new Promise((resolve) => setTimeout(resolve, 10));

      manager.get('test://resource/access');

      const metadata = manager.getMetadata('test://resource/access');
      expect(metadata?.lastAccessedAt).toBeInstanceOf(Date);
      expect(metadata?.lastAccessedAt?.getTime()).toBeGreaterThan(
        metadata?.createdAt?.getTime() || 0
      );
    });

    it('should track access count', () => {
      const resource: MCPResource = {
        uri: 'test://resource/count',
        name: 'Count Resource',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      };

      manager.register(resource);

      manager.get('test://resource/count');
      manager.get('test://resource/count');
      manager.get('test://resource/count');

      const metadata = manager.getMetadata('test://resource/count');
      expect(metadata?.accessCount).toBe(3);
    });
  });

  describe('Resource Dependencies', () => {
    it('should track resource dependencies', () => {
      manager.register({
        uri: 'test://resource/parent',
        name: 'Parent',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
        dependencies: ['test://resource/child1', 'test://resource/child2'],
      });

      const dependencies = manager.getDependencies('test://resource/parent');
      expect(dependencies).toHaveLength(2);
    });

    it('should resolve dependency tree', () => {
      manager.register({
        uri: 'test://resource/root',
        name: 'Root',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
        dependencies: ['test://resource/level1'],
      });

      manager.register({
        uri: 'test://resource/level1',
        name: 'Level 1',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
        dependencies: ['test://resource/level2'],
      });

      manager.register({
        uri: 'test://resource/level2',
        name: 'Level 2',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
      });

      const tree = manager.resolveDependencyTree('test://resource/root');
      expect(tree).toHaveLength(3);
    });

    it('should detect circular dependencies', () => {
      manager.register({
        uri: 'test://resource/a',
        name: 'A',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
        dependencies: ['test://resource/b'],
      });

      manager.register({
        uri: 'test://resource/b',
        name: 'B',
        type: ResourceType.TEXT,
        mimeType: 'text/plain',
        dependencies: ['test://resource/a'],
      });

      expect(() =>
        manager.resolveDependencyTree('test://resource/a')
      ).toThrow('Circular dependency detected');
    });
  });

  describe('Statistics and Reporting', () => {
    beforeEach(() => {
      for (let i = 0; i < 5; i++) {
        manager.register({
          uri: `test://resource/${i}`,
          name: `Resource ${i}`,
          type: i % 2 === 0 ? ResourceType.TEXT : ResourceType.BINARY,
          mimeType: i % 2 === 0 ? 'text/plain' : 'application/octet-stream',
        });
      }
    });

    it('should provide resource statistics', () => {
      const stats = manager.getStats();

      expect(stats.total).toBe(5);
      expect(stats.byType[ResourceType.TEXT]).toBe(3);
      expect(stats.byType[ResourceType.BINARY]).toBe(2);
    });

    it('should track cache statistics', () => {
      const stats = manager.getCacheStats();

      expect(stats).toHaveProperty('size');
      expect(stats).toHaveProperty('hits');
      expect(stats).toHaveProperty('misses');
      expect(stats).toHaveProperty('hitRate');
    });

    it('should generate usage report', () => {
      // Access some resources
      manager.get('test://resource/0');
      manager.get('test://resource/0');
      manager.get('test://resource/1');

      const report = manager.generateUsageReport();

      expect(report.mostAccessed).toHaveLength(2);
      expect(report.mostAccessed[0].accessCount).toBe(2);
    });
  });
});

// Export types for the resource manager
export enum ResourceType {
  TEXT = 'text',
  BINARY = 'binary',
  JSON = 'json',
  XML = 'xml',
}
