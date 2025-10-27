/**
 * MCPPluginManager Integration Tests
 * Tests plugin discovery, loading, lifecycle management, and security
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  MCPPluginManager,
  PluginMetadata,
  PluginCapability,
  PluginState
} from '../../src/mcp/plugin-manager';
import * as fs from 'fs/promises';
import * as path from 'path';

describe('MCPPluginManager Integration', () => {
  let pluginManager: MCPPluginManager;
  let testPluginsDir: string;

  beforeEach(async () => {
    testPluginsDir = path.join(__dirname, '../.test-plugins');

    pluginManager = new MCPPluginManager([testPluginsDir], {
      autoLoad: false,
      cacheEnabled: true
    });

    // Create test plugins directory
    await fs.mkdir(testPluginsDir, { recursive: true });
  });

  afterEach(async () => {
    // Clean up test plugins directory
    try {
      await fs.rm(testPluginsDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  describe('Plugin Discovery', () => {
    it('should discover plugins in configured paths', async () => {
      await createTestPlugin(testPluginsDir, 'test-plugin', {
        name: 'test-plugin',
        version: '1.0.0',
        description: 'Test plugin',
        capabilities: [PluginCapability.TOOLS]
      });

      const result = await pluginManager.discoverPlugins();

      expect(result.found).toBe(1);
      expect(result.errors).toHaveLength(0);
    });

    it('should handle multiple plugins', async () => {
      await createTestPlugin(testPluginsDir, 'plugin1', {
        name: 'plugin1',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      });

      await createTestPlugin(testPluginsDir, 'plugin2', {
        name: 'plugin2',
        version: '1.0.0',
        capabilities: [PluginCapability.RESOURCES]
      });

      const result = await pluginManager.discoverPlugins();

      expect(result.found).toBe(2);
    });

    it('should skip invalid plugin directories', async () => {
      // Create directory without plugin.json
      await fs.mkdir(path.join(testPluginsDir, 'invalid-plugin'), { recursive: true });

      await createTestPlugin(testPluginsDir, 'valid-plugin', {
        name: 'valid-plugin',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      });

      const result = await pluginManager.discoverPlugins();

      // Should find 1 valid plugin and skip the invalid one
      expect(result.found).toBe(1);
    });

    it('should handle malformed plugin.json', async () => {
      const malformedDir = path.join(testPluginsDir, 'malformed');
      await fs.mkdir(malformedDir, { recursive: true });
      await fs.writeFile(path.join(malformedDir, 'plugin.json'), 'invalid json{', 'utf-8');

      const result = await pluginManager.discoverPlugins();

      expect(result.found).toBe(0);
    });
  });

  describe('Plugin Loading', () => {
    it('should load valid plugin', async () => {
      const metadata: PluginMetadata = {
        name: 'loadable-plugin',
        version: '1.0.0',
        description: 'Loadable test plugin',
        capabilities: [PluginCapability.TOOLS]
      };

      const instance = await pluginManager.loadPlugin(metadata);

      expect(instance.state).toBe(PluginState.LOADED);
      expect(instance.metadata.name).toBe('loadable-plugin');
    });

    it('should validate plugin metadata', async () => {
      const invalidMetadata: any = {
        // Missing required fields
        description: 'Invalid plugin'
      };

      await expect(pluginManager.loadPlugin(invalidMetadata)).rejects.toThrow();
    });

    it('should validate plugin version format', async () => {
      const invalidVersion: PluginMetadata = {
        name: 'invalid-version',
        version: 'not-semver',
        capabilities: [PluginCapability.TOOLS]
      };

      await expect(pluginManager.loadPlugin(invalidVersion)).rejects.toThrow('Invalid version format');
    });

    it('should require at least one capability', async () => {
      const noCapabilities: PluginMetadata = {
        name: 'no-caps',
        version: '1.0.0',
        capabilities: []
      };

      await expect(pluginManager.loadPlugin(noCapabilities)).rejects.toThrow('at least one capability');
    });
  });

  describe('Plugin Security', () => {
    it('should sanitize plugin names to prevent path traversal', async () => {
      const maliciousMetadata: PluginMetadata = {
        name: '../../../etc/passwd',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      };

      await expect(pluginManager.loadPlugin(maliciousMetadata)).rejects.toThrow('Invalid plugin name');
    });

    it('should reject plugin names with slashes', async () => {
      const slashName: PluginMetadata = {
        name: 'path/to/plugin',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      };

      await expect(pluginManager.loadPlugin(slashName)).rejects.toThrow('Invalid plugin name');
    });

    it('should reject empty plugin names', async () => {
      const emptyName: any = {
        name: '',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      };

      await expect(pluginManager.loadPlugin(emptyName)).rejects.toThrow();
    });

    it('should only allow alphanumeric, dash, and underscore in names', async () => {
      const validNames = ['plugin-name', 'plugin_name', 'plugin123', 'Plugin-Name_123'];

      for (const name of validNames) {
        const metadata: PluginMetadata = {
          name,
          version: '1.0.0',
          capabilities: [PluginCapability.TOOLS]
        };

        const instance = await pluginManager.loadPlugin(metadata);
        expect(instance.metadata.name).toBe(name);
      }
    });

    it('should reject special characters in plugin names', async () => {
      const invalidNames = ['plugin@name', 'plugin#name', 'plugin$name'];

      for (const name of invalidNames) {
        const metadata: PluginMetadata = {
          name,
          version: '1.0.0',
          capabilities: [PluginCapability.TOOLS]
        };

        await expect(pluginManager.loadPlugin(metadata)).rejects.toThrow('Invalid plugin name');
      }
    });
  });

  describe('Plugin Lifecycle', () => {
    it('should unload loaded plugin', async () => {
      const metadata: PluginMetadata = {
        name: 'unloadable',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      };

      await pluginManager.loadPlugin(metadata);
      await pluginManager.unloadPlugin('unloadable');

      expect(pluginManager.getPlugin('unloadable')).toBeUndefined();
    });

    it('should throw when unloading non-existent plugin', async () => {
      await expect(pluginManager.unloadPlugin('nonexistent')).rejects.toThrow('Plugin not found');
    });

    it('should enable disabled plugin', async () => {
      const metadata: PluginMetadata = {
        name: 'enableable',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      };

      const instance = await pluginManager.loadPlugin(metadata);
      await pluginManager.disablePlugin('enableable');

      expect(instance.state).toBe(PluginState.DISABLED);

      await pluginManager.enablePlugin('enableable');

      expect(instance.state).toBe(PluginState.ACTIVE);
    });

    it('should disable active plugin', async () => {
      const metadata: PluginMetadata = {
        name: 'disableable',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      };

      await pluginManager.loadPlugin(metadata);

      // Plugin needs to be active first
      await pluginManager.enablePlugin('disableable');
      await pluginManager.disablePlugin('disableable');

      const plugin = pluginManager.getPlugin('disableable');

      expect(plugin?.state).toBe(PluginState.DISABLED);
    });

    it('should reload plugin', async () => {
      const metadata: PluginMetadata = {
        name: 'reloadable',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      };

      await pluginManager.loadPlugin(metadata);

      const before = pluginManager.getPlugin('reloadable');

      await pluginManager.reloadPlugin('reloadable');

      const after = pluginManager.getPlugin('reloadable');

      expect(after).toBeDefined();
      expect(after?.loadTime).toBeGreaterThan(0);
    });
  });

  describe('Plugin Queries', () => {
    beforeEach(async () => {
      await pluginManager.loadPlugin({
        name: 'tools-plugin',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      });

      await pluginManager.loadPlugin({
        name: 'resources-plugin',
        version: '1.0.0',
        capabilities: [PluginCapability.RESOURCES]
      });

      await pluginManager.loadPlugin({
        name: 'multi-plugin',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS, PluginCapability.RESOURCES]
      });
    });

    it('should get all plugins', () => {
      const all = pluginManager.getAllPlugins();

      expect(all).toHaveLength(3);
    });

    it('should get plugins by capability', () => {
      const toolPlugins = pluginManager.getPluginsByCapability(PluginCapability.TOOLS);

      expect(toolPlugins).toHaveLength(2); // tools-plugin and multi-plugin
      expect(toolPlugins.every((p) => p.metadata.capabilities.includes(PluginCapability.TOOLS))).toBe(true);
    });

    it('should get plugins by state', () => {
      const loaded = pluginManager.getPluginsByState(PluginState.LOADED);

      expect(loaded.length).toBeGreaterThan(0);
      expect(loaded.every((p) => p.state === PluginState.LOADED)).toBe(true);
    });
  });

  describe('Statistics and Export', () => {
    beforeEach(async () => {
      await pluginManager.loadPlugin({
        name: 'plugin1',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      });

      await pluginManager.loadPlugin({
        name: 'plugin2',
        version: '1.0.0',
        capabilities: [PluginCapability.RESOURCES, PluginCapability.PROMPTS]
      });
    });

    it('should provide statistics', () => {
      const stats = pluginManager.getStatistics();

      expect(stats.total).toBe(2);
      expect(stats.loaded).toBe(2);
      expect(stats.byCapability[PluginCapability.TOOLS]).toBe(1);
      expect(stats.byCapability[PluginCapability.RESOURCES]).toBe(1);
    });

    it('should export configuration', () => {
      const config = pluginManager.exportConfiguration();
      const parsed = JSON.parse(config);

      expect(parsed.plugins).toHaveLength(2);
      expect(parsed.statistics).toBeDefined();
      expect(parsed.statistics.total).toBe(2);
    });
  });

  describe('Events', () => {
    it('should emit pluginLoaded event', async () => {
      const loadedSpy = vi.fn();
      pluginManager.on('pluginLoaded', loadedSpy);

      const metadata: PluginMetadata = {
        name: 'event-plugin',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      };

      await pluginManager.loadPlugin(metadata);

      expect(loadedSpy).toHaveBeenCalledWith('event-plugin', expect.any(Object));
    });

    it('should emit pluginUnloaded event', async () => {
      const unloadedSpy = vi.fn();
      pluginManager.on('pluginUnloaded', unloadedSpy);

      await pluginManager.loadPlugin({
        name: 'unload-event',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      });

      await pluginManager.unloadPlugin('unload-event');

      expect(unloadedSpy).toHaveBeenCalledWith('unload-event');
    });

    it('should emit pluginError event', async () => {
      const errorSpy = vi.fn();
      pluginManager.on('pluginError', errorSpy);

      const invalidMetadata: any = {
        version: '1.0.0'
        // Missing required fields
      };

      try {
        await pluginManager.loadPlugin(invalidMetadata);
      } catch {
        // Expected error
      }

      expect(errorSpy).toHaveBeenCalled();
    });

    it('should emit pluginStateChange event', async () => {
      const stateChangeSpy = vi.fn();
      pluginManager.on('pluginStateChange', stateChangeSpy);

      await pluginManager.loadPlugin({
        name: 'state-change',
        version: '1.0.0',
        capabilities: [PluginCapability.TOOLS]
      });

      expect(stateChangeSpy).toHaveBeenCalledWith('state-change', PluginState.LOADING);
      expect(stateChangeSpy).toHaveBeenCalledWith('state-change', PluginState.LOADED);
    });
  });
});

/**
 * Helper function to create test plugin
 */
async function createTestPlugin(
  baseDir: string,
  name: string,
  metadata: PluginMetadata
): Promise<void> {
  const pluginDir = path.join(baseDir, name);
  await fs.mkdir(pluginDir, { recursive: true });

  const metadataPath = path.join(pluginDir, 'plugin.json');
  await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2), 'utf-8');
}
