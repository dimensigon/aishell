/**
 * ResourceManager - MCP Resource Management with Caching
 * Implements resource registration, caching with LRU eviction, and watching capabilities
 */

import { EventEmitter } from 'eventemitter3';
import { MCPResource, ResourceType } from './types';

/**
 * Resource Metadata
 */
interface ResourceMetadata {
  createdAt: Date;
  lastAccessedAt: Date;
  accessCount: number;
  size?: number;
}

/**
 * Cache Entry
 */
interface CacheEntry {
  content: any;
  timestamp: number;
  ttl: number;
}

/**
 * Resource Manager Configuration
 */
export interface ResourceManagerConfig {
  cacheEnabled?: boolean;
  cacheTTL?: number;
  maxCacheSize?: number;
}

/**
 * Cache Statistics
 */
export interface CacheStats {
  size: number;
  hits: number;
  misses: number;
  hitRate: number;
}

/**
 * Resource Statistics
 */
export interface ResourceStats {
  total: number;
  byType: Record<string, number>;
}

/**
 * Usage Report Entry
 */
interface UsageReportEntry {
  uri: string;
  name: string;
  accessCount: number;
  lastAccessed: Date;
}

/**
 * Usage Report
 */
export interface UsageReport {
  mostAccessed: UsageReportEntry[];
  totalAccesses: number;
  uniqueResources: number;
}

/**
 * Valid MIME Types
 */
const VALID_MIME_TYPES = [
  'text/plain',
  'text/html',
  'text/css',
  'text/javascript',
  'application/json',
  'application/xml',
  'application/octet-stream',
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/gif',
  'image/svg+xml',
];

/**
 * ResourceManager
 * Manages MCP resources with caching, watching, and dependency tracking
 */
export class ResourceManager extends EventEmitter {
  private resources: Map<string, MCPResource>;
  private metadata: Map<string, ResourceMetadata>;
  private cache: Map<string, CacheEntry>;
  private watchers: Map<string, Set<Function>>;
  private config: Required<ResourceManagerConfig>;
  private cacheHits: number;
  private cacheMisses: number;

  constructor(config: ResourceManagerConfig = {}) {
    super();
    this.resources = new Map();
    this.metadata = new Map();
    this.cache = new Map();
    this.watchers = new Map();
    this.cacheHits = 0;
    this.cacheMisses = 0;
    this.config = {
      cacheEnabled: config.cacheEnabled ?? true,
      cacheTTL: config.cacheTTL ?? 5000,
      maxCacheSize: config.maxCacheSize ?? 100,
    };
  }

  /**
   * Register a resource
   */
  register(resource: MCPResource): void {
    // Validate resource
    if (!resource.uri || resource.uri.trim() === '') {
      throw new Error('Invalid resource URI');
    }

    // Validate URI format
    if (!this.isValidURI(resource.uri)) {
      throw new Error('Invalid URI format');
    }

    // Validate MIME type
    if (resource.mimeType && !this.isValidMimeType(resource.mimeType)) {
      throw new Error('Invalid MIME type');
    }

    // Validate resource structure
    if (!this.validate(resource)) {
      throw new Error('Invalid resource structure');
    }

    // Store resource
    this.resources.set(resource.uri, resource);

    // Initialize or update metadata
    const existing = this.metadata.get(resource.uri);
    if (!existing) {
      this.metadata.set(resource.uri, {
        createdAt: new Date(),
        lastAccessedAt: new Date(),
        accessCount: 0,
      });
    }

    // Notify watchers
    this.notifyResourceWatchers(resource.uri, resource);
  }

  /**
   * Register multiple resources
   */
  registerBatch(resources: MCPResource[]): void {
    for (const resource of resources) {
      this.register(resource);
    }
  }

  /**
   * Get a resource by URI
   */
  get(uri: string): MCPResource | undefined {
    const resource = this.resources.get(uri);

    if (resource) {
      // Update access metadata
      const meta = this.metadata.get(uri);
      if (meta) {
        meta.lastAccessedAt = new Date();
        meta.accessCount++;
      }
    }

    return resource;
  }

  /**
   * Get or fetch resource with caching
   */
  async getOrFetch(uri: string, fetchFn: () => Promise<any>): Promise<any> {
    // Check cache first
    if (this.config.cacheEnabled) {
      const cached = this.cache.get(uri);
      if (cached && this.isCacheEntryValid(cached)) {
        this.cacheHits++;
        return cached.content;
      }
    }

    // Cache miss - fetch content
    this.cacheMisses++;
    const content = await fetchFn();

    // Store in cache
    if (this.config.cacheEnabled) {
      this.addToCache(uri, content);
    }

    return content;
  }

  /**
   * Check if cache entry is valid
   */
  private isCacheEntryValid(entry: CacheEntry): boolean {
    const now = Date.now();
    return now - entry.timestamp < entry.ttl;
  }

  /**
   * Add content to cache
   */
  private addToCache(uri: string, content: any): void {
    // Check if cache is full
    if (this.cache.size >= this.config.maxCacheSize) {
      // Evict oldest entry (LRU)
      this.evictOldestCacheEntry();
    }

    this.cache.set(uri, {
      content,
      timestamp: Date.now(),
      ttl: this.config.cacheTTL,
    });
  }

  /**
   * Evict oldest cache entry
   */
  private evictOldestCacheEntry(): void {
    let oldestUri: string | null = null;
    let oldestTimestamp = Infinity;

    for (const [uri, entry] of this.cache.entries()) {
      if (entry.timestamp < oldestTimestamp) {
        oldestTimestamp = entry.timestamp;
        oldestUri = uri;
      }
    }

    if (oldestUri) {
      this.cache.delete(oldestUri);
    }
  }

  /**
   * Invalidate cache for specific resource
   */
  invalidateCache(uri: string): void {
    this.cache.delete(uri);
  }

  /**
   * Clear all cache
   */
  clearCache(): void {
    this.cache.clear();
    this.cacheHits = 0;
    this.cacheMisses = 0;
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): CacheStats {
    const total = this.cacheHits + this.cacheMisses;
    const hitRate = total > 0 ? this.cacheHits / total : 0;

    return {
      size: this.cache.size,
      hits: this.cacheHits,
      misses: this.cacheMisses,
      hitRate,
    };
  }

  /**
   * Check if resource exists
   */
  has(uri: string): boolean {
    return this.resources.has(uri);
  }

  /**
   * Remove a resource
   */
  remove(uri: string): boolean {
    const existed = this.resources.delete(uri);
    this.metadata.delete(uri);
    this.cache.delete(uri);
    this.watchers.delete(uri);
    return existed;
  }

  /**
   * List all resources
   */
  list(): MCPResource[] {
    return Array.from(this.resources.values());
  }

  /**
   * List resources by type
   */
  listByType(type: ResourceType): MCPResource[] {
    return this.list().filter((r) => r.type === type);
  }

  /**
   * Search resources by name pattern
   */
  search(pattern: string): MCPResource[] {
    const lowerPattern = pattern.toLowerCase();
    return this.list().filter((r) =>
      r.name.toLowerCase().includes(lowerPattern)
    );
  }

  /**
   * Watch a resource for changes
   */
  watch(uri: string, callback: Function): void {
    if (!this.watchers.has(uri)) {
      this.watchers.set(uri, new Set());
    }
    this.watchers.get(uri)!.add(callback);
  }

  /**
   * Unwatch a resource
   */
  unwatch(uri: string, callback: Function): void {
    const callbacks = this.watchers.get(uri);
    if (callbacks) {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.watchers.delete(uri);
      }
    }
  }

  /**
   * Notify watchers of resource changes
   */
  private notifyResourceWatchers(uri: string, resource: MCPResource): void {
    const callbacks = this.watchers.get(uri);
    if (callbacks) {
      for (const callback of callbacks) {
        callback(resource);
      }
    }
  }

  /**
   * Validate resource structure
   */
  validate(resource: any): boolean {
    if (!resource) return false;
    if (!resource.uri || typeof resource.uri !== 'string') return false;
    if (!resource.name || typeof resource.name !== 'string') return false;
    if (!resource.type || !Object.values(ResourceType).includes(resource.type))
      return false;
    if (!resource.mimeType || typeof resource.mimeType !== 'string')
      return false;
    return true;
  }

  /**
   * Validate URI format
   */
  private isValidURI(uri: string): boolean {
    // Must contain ://
    if (!uri.includes('://')) return false;

    // Basic URI validation
    const parts = uri.split('://');
    if (parts.length !== 2) return false;

    const [scheme, path] = parts;
    if (!scheme || !path) return false;

    return true;
  }

  /**
   * Validate MIME type
   */
  private isValidMimeType(mimeType: string): boolean {
    // Check against known MIME types
    return VALID_MIME_TYPES.includes(mimeType);
  }

  /**
   * Get resource metadata
   */
  getMetadata(uri: string): ResourceMetadata | undefined {
    return this.metadata.get(uri);
  }

  /**
   * Update resource metadata
   */
  updateMetadata(uri: string, updates: Partial<ResourceMetadata>): void {
    const meta = this.metadata.get(uri);
    if (meta) {
      Object.assign(meta, updates);
    }
  }

  /**
   * Get resource dependencies
   */
  getDependencies(uri: string): string[] {
    const resource = this.resources.get(uri);
    return resource?.dependencies || [];
  }

  /**
   * Resolve dependency tree
   */
  resolveDependencyTree(uri: string, visited = new Set<string>()): string[] {
    // Check for circular dependencies
    if (visited.has(uri)) {
      throw new Error('Circular dependency detected');
    }

    visited.add(uri);
    const dependencies = this.getDependencies(uri);
    const resolved: string[] = [uri];

    for (const dep of dependencies) {
      const depTree = this.resolveDependencyTree(dep, new Set(visited));
      resolved.push(...depTree.filter((d) => !resolved.includes(d)));
    }

    return resolved;
  }

  /**
   * Get resource statistics
   */
  getStats(): ResourceStats {
    const byType: Record<string, number> = {};

    for (const resource of this.resources.values()) {
      const typeKey = resource.type as string;
      byType[typeKey] = (byType[typeKey] || 0) + 1;
    }

    return {
      total: this.resources.size,
      byType,
    };
  }

  /**
   * Generate usage report
   */
  generateUsageReport(): UsageReport {
    const entries: UsageReportEntry[] = [];

    for (const [uri, resource] of this.resources.entries()) {
      const meta = this.metadata.get(uri);
      if (meta && meta.accessCount > 0) {
        entries.push({
          uri,
          name: resource.name,
          accessCount: meta.accessCount,
          lastAccessed: meta.lastAccessedAt,
        });
      }
    }

    // Sort by access count descending
    entries.sort((a, b) => b.accessCount - a.accessCount);

    const totalAccesses = entries.reduce((sum, e) => sum + e.accessCount, 0);

    return {
      mostAccessed: entries,
      totalAccesses,
      uniqueResources: entries.length,
    };
  }

  /**
   * Clear all resources and metadata
   */
  clear(): void {
    this.resources.clear();
    this.metadata.clear();
    this.cache.clear();
    this.watchers.clear();
    this.cacheHits = 0;
    this.cacheMisses = 0;
  }

  /**
   * Get resource count
   */
  size(): number {
    return this.resources.size;
  }
}
