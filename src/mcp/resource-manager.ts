/**
 * MCP Resource Manager
 * Manages MCP resources with caching, validation, and lifecycle management
 */

import { EventEmitter } from 'eventemitter3';
import { MCPResource } from './types';

/**
 * Resource Cache Entry
 */
export interface ResourceCacheEntry {
  resource: MCPResource;
  content?: unknown;
  timestamp: number;
  accessCount: number;
  ttl?: number;
}

/**
 * Resource Manager Events
 */
export interface ResourceManagerEvents {
  resourceAdded: (resource: MCPResource) => void;
  resourceRemoved: (uri: string) => void;
  resourceUpdated: (resource: MCPResource) => void;
  cacheHit: (uri: string) => void;
  cacheMiss: (uri: string) => void;
  cacheEvicted: (uri: string) => void;
}

/**
 * Resource Manager Configuration
 */
export interface ResourceManagerConfig {
  maxCacheSize?: number;
  defaultTTL?: number;
  enableAutoRefresh?: boolean;
  refreshIntervalMs?: number;
}

/**
 * MCP Resource Manager
 */
export class MCPResourceManager extends EventEmitter<ResourceManagerEvents> {
  private resources = new Map<string, MCPResource>();
  private cache = new Map<string, ResourceCacheEntry>();
  private config: Required<ResourceManagerConfig>;

  constructor(config?: ResourceManagerConfig) {
    super();
    this.config = {
      maxCacheSize: config?.maxCacheSize || 100,
      defaultTTL: config?.defaultTTL || 3600000, // 1 hour
      enableAutoRefresh: config?.enableAutoRefresh || false,
      refreshIntervalMs: config?.refreshIntervalMs || 300000 // 5 minutes
    };
  }

  /**
   * Register a resource
   */
  registerResource(resource: MCPResource): void {
    this.resources.set(resource.uri, resource);
    this.emit('resourceAdded', resource);
  }

  /**
   * Unregister a resource
   */
  unregisterResource(uri: string): void {
    this.resources.delete(uri);
    this.cache.delete(uri);
    this.emit('resourceRemoved', uri);
  }

  /**
   * Get resource by URI
   */
  getResource(uri: string): MCPResource | undefined {
    return this.resources.get(uri);
  }

  /**
   * Get all resources
   */
  getAllResources(): MCPResource[] {
    return Array.from(this.resources.values());
  }

  /**
   * Filter resources by criteria
   */
  filterResources(
    predicate: (resource: MCPResource) => boolean
  ): MCPResource[] {
    return this.getAllResources().filter(predicate);
  }

  /**
   * Find resources by name pattern
   */
  findByName(pattern: string | RegExp): MCPResource[] {
    const regex = typeof pattern === 'string' ? new RegExp(pattern, 'i') : pattern;
    return this.filterResources((r) => regex.test(r.name));
  }

  /**
   * Find resources by MIME type
   */
  findByMimeType(mimeType: string): MCPResource[] {
    return this.filterResources((r) => r.mimeType === mimeType);
  }

  /**
   * Cache resource content
   */
  cacheContent(uri: string, content: unknown, ttl?: number): void {
    // Check cache size and evict if necessary
    if (this.cache.size >= this.config.maxCacheSize) {
      this.evictLRU();
    }

    const resource = this.resources.get(uri);
    if (!resource) {
      throw new Error(`Resource not found: ${uri}`);
    }

    const entry: ResourceCacheEntry = {
      resource,
      content,
      timestamp: Date.now(),
      accessCount: 0,
      ttl: ttl || this.config.defaultTTL
    };

    this.cache.set(uri, entry);
  }

  /**
   * Get cached content
   */
  getCachedContent(uri: string): unknown | null {
    const entry = this.cache.get(uri);

    if (!entry) {
      this.emit('cacheMiss', uri);
      return null;
    }

    // Check TTL
    if (entry.ttl && Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(uri);
      this.emit('cacheEvicted', uri);
      return null;
    }

    entry.accessCount++;
    this.emit('cacheHit', uri);
    return entry.content;
  }

  /**
   * Invalidate cache entry
   */
  invalidateCache(uri: string): void {
    this.cache.delete(uri);
  }

  /**
   * Clear all cache
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Evict least recently used cache entry
   */
  private evictLRU(): void {
    let oldestEntry: [string, ResourceCacheEntry] | null = null;

    for (const [uri, entry] of this.cache.entries()) {
      if (!oldestEntry || entry.timestamp < oldestEntry[1].timestamp) {
        oldestEntry = [uri, entry];
      }
    }

    if (oldestEntry) {
      this.cache.delete(oldestEntry[0]);
      this.emit('cacheEvicted', oldestEntry[0]);
    }
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): {
    size: number;
    maxSize: number;
    hitRate: number;
    entries: Array<{
      uri: string;
      age: number;
      accessCount: number;
    }>;
  } {
    const entries = Array.from(this.cache.entries()).map(([uri, entry]) => ({
      uri,
      age: Date.now() - entry.timestamp,
      accessCount: entry.accessCount
    }));

    const totalAccess = entries.reduce((sum, e) => sum + e.accessCount, 0);
    const hitRate = totalAccess > 0 ? this.cache.size / totalAccess : 0;

    return {
      size: this.cache.size,
      maxSize: this.config.maxCacheSize,
      hitRate,
      entries
    };
  }

  /**
   * Validate resource structure
   */
  static validateResource(resource: unknown): resource is MCPResource {
    if (typeof resource !== 'object' || resource === null) {
      return false;
    }

    const r = resource as Partial<MCPResource>;

    return (
      typeof r.uri === 'string' &&
      typeof r.name === 'string' &&
      (r.description === undefined || typeof r.description === 'string') &&
      (r.mimeType === undefined || typeof r.mimeType === 'string')
    );
  }

  /**
   * Group resources by MIME type
   */
  groupByMimeType(): Map<string, MCPResource[]> {
    const groups = new Map<string, MCPResource[]>();

    for (const resource of this.resources.values()) {
      const mimeType = resource.mimeType || 'application/octet-stream';
      const group = groups.get(mimeType) || [];
      group.push(resource);
      groups.set(mimeType, group);
    }

    return groups;
  }

  /**
   * Export resources as JSON
   */
  exportResources(): string {
    const resources = this.getAllResources();
    return JSON.stringify(resources, null, 2);
  }

  /**
   * Import resources from JSON
   */
  importResources(json: string): void {
    try {
      const resources = JSON.parse(json) as MCPResource[];

      if (!Array.isArray(resources)) {
        throw new Error('Invalid format: expected array');
      }

      resources.forEach((resource) => {
        if (MCPResourceManager.validateResource(resource)) {
          this.registerResource(resource);
        } else {
          console.warn('Skipping invalid resource:', resource);
        }
      });
    } catch (error) {
      throw new Error(
        `Failed to import resources: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }
}
