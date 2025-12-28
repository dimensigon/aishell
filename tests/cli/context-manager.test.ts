/**
 * Context Manager Test Suite
 * Comprehensive tests for context management functionality
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  ContextManager,
  Context,
  SaveContextOptions,
  QueryHistoryEntry,
  Session
} from '../../src/cli/context-manager';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

describe('ContextManager', () => {
  let contextManager: ContextManager;
  let testDir: string;

  beforeEach(async () => {
    // Create temporary test directory
    testDir = await fs.mkdtemp(path.join(os.tmpdir(), 'context-test-'));
    contextManager = new ContextManager(testDir);
    await contextManager.initialize();
  });

  afterEach(async () => {
    // Clean up test directory
    try {
      await fs.rm(testDir, { recursive: true, force: true });
    } catch (error) {
      // Ignore cleanup errors
    }
  });

  describe('Initialization', () => {
    it('should create context and session directories', async () => {
      const contextDir = path.join(testDir, 'contexts');
      const sessionDir = path.join(testDir, 'sessions');

      const contextDirExists = await fs.access(contextDir).then(() => true).catch(() => false);
      const sessionDirExists = await fs.access(sessionDir).then(() => true).catch(() => false);

      expect(contextDirExists).toBe(true);
      expect(sessionDirExists).toBe(true);
    });

    it('should initialize without errors', async () => {
      const newManager = new ContextManager(testDir);
      await expect(newManager.initialize()).resolves.not.toThrow();
    });
  });

  describe('Context Save/Load', () => {
    it('should save a basic context', async () => {
      const contextName = 'test-context';
      await contextManager.saveContext(contextName);

      const contexts = await contextManager.listContexts();
      expect(contexts).toHaveLength(1);
      expect(contexts[0].name).toBe(contextName);
    });

    it('should save context with description', async () => {
      const contextName = 'test-context';
      const description = 'Test description';

      await contextManager.saveContext(contextName, { description });

      const context = await contextManager.showContext(contextName);
      expect(context.description).toBe(description);
    });

    it('should save context with query history', async () => {
      const contextName = 'test-context';
      const queryEntry: QueryHistoryEntry = {
        query: 'SELECT * FROM users',
        timestamp: Date.now(),
        duration: 100,
        success: true
      };

      contextManager.addQueryToHistory(queryEntry);
      await contextManager.saveContext(contextName, { includeHistory: true });

      const context = await contextManager.showContext(contextName);
      expect(context.queryHistory).toHaveLength(1);
      expect(context.queryHistory![0].query).toBe(queryEntry.query);
    });

    it('should save context with aliases', async () => {
      const contextName = 'test-context';
      contextManager.setAlias('users', 'SELECT * FROM users');

      await contextManager.saveContext(contextName, { includeAliases: true });

      const context = await contextManager.showContext(contextName);
      expect(context.aliases).toHaveProperty('users');
      expect(context.aliases!.users).toBe('SELECT * FROM users');
    });

    it('should save context with configuration', async () => {
      const contextName = 'test-context';
      contextManager.setConfig('theme', 'dark');
      contextManager.setConfig('timeout', 5000);

      await contextManager.saveContext(contextName, { includeConfig: true });

      const context = await contextManager.showContext(contextName);
      expect(context.configuration).toHaveProperty('theme', 'dark');
      expect(context.configuration).toHaveProperty('timeout', 5000);
    });

    it('should save context with variables', async () => {
      const contextName = 'test-context';
      contextManager.setVariable('user_id', 123);
      contextManager.setVariable('debug_mode', true);

      await contextManager.saveContext(contextName, { includeVariables: true });

      const context = await contextManager.showContext(contextName);
      expect(context.variables).toHaveProperty('user_id', 123);
      expect(context.variables).toHaveProperty('debug_mode', true);
    });

    it('should load context', async () => {
      const contextName = 'test-context';
      await contextManager.saveContext(contextName, { description: 'Test' });

      const loadedContext = await contextManager.loadContext(contextName);
      expect(loadedContext.name).toBe(contextName);
      expect(loadedContext.description).toBe('Test');
    });

    it('should merge contexts when loading with merge option', async () => {
      contextManager.setAlias('alias1', 'value1');
      await contextManager.saveContext('context1', { includeAliases: true });

      contextManager.setAlias('alias2', 'value2');
      await contextManager.saveContext('context2', { includeAliases: true });

      await contextManager.loadContext('context1', false);
      await contextManager.loadContext('context2', true);

      const current = await contextManager.getCurrentContext();
      expect(current?.aliases).toHaveProperty('alias1');
      expect(current?.aliases).toHaveProperty('alias2');
    });

    it('should update existing context', async () => {
      const contextName = 'test-context';
      await contextManager.saveContext(contextName, { description: 'Original' });

      await contextManager.saveContext(contextName, { description: 'Updated' });

      const context = await contextManager.showContext(contextName);
      expect(context.description).toBe('Updated');
    });
  });

  describe('Context List', () => {
    it('should list all contexts', async () => {
      await contextManager.saveContext('context1');
      await contextManager.saveContext('context2');
      await contextManager.saveContext('context3');

      const contexts = await contextManager.listContexts();
      expect(contexts).toHaveLength(3);
    });

    it('should list contexts in verbose mode', async () => {
      contextManager.addQueryToHistory({
        query: 'SELECT * FROM users',
        timestamp: Date.now(),
        success: true
      });
      contextManager.setAlias('users', 'SELECT * FROM users');

      await contextManager.saveContext('test', {
        includeHistory: true,
        includeAliases: true
      });

      const contexts = await contextManager.listContexts(true);
      expect(contexts[0].queryCount).toBe(1);
      expect(contexts[0].aliasCount).toBe(1);
    });

    it('should return empty array when no contexts exist', async () => {
      const contexts = await contextManager.listContexts();
      expect(contexts).toEqual([]);
    });

    it('should sort contexts by updated date', async () => {
      await contextManager.saveContext('context1');
      await new Promise(resolve => setTimeout(resolve, 10));
      await contextManager.saveContext('context2');
      await new Promise(resolve => setTimeout(resolve, 10));
      await contextManager.saveContext('context3');

      const contexts = await contextManager.listContexts();
      expect(contexts[0].name).toBe('context3');
      expect(contexts[1].name).toBe('context2');
      expect(contexts[2].name).toBe('context1');
    });
  });

  describe('Context Delete', () => {
    it('should delete context', async () => {
      await contextManager.saveContext('test-context');
      await contextManager.deleteContext('test-context');

      const contexts = await contextManager.listContexts();
      expect(contexts).toHaveLength(0);
    });

    it('should throw error when deleting non-existent context', async () => {
      await expect(
        contextManager.deleteContext('non-existent')
      ).rejects.toThrow('not found');
    });

    it('should prevent deletion of current context without force', async () => {
      await contextManager.saveContext('current');
      await contextManager.loadContext('current');

      await expect(
        contextManager.deleteContext('current')
      ).rejects.toThrow('Cannot delete current context');
    });

    it('should allow deletion of current context with force flag', async () => {
      await contextManager.saveContext('current');
      await contextManager.loadContext('current');

      await expect(
        contextManager.deleteContext('current', true)
      ).resolves.not.toThrow();
    });
  });

  describe('Context Export/Import', () => {
    it('should export context to JSON file', async () => {
      await contextManager.saveContext('test');
      const exportFile = path.join(testDir, 'export.json');

      await contextManager.exportContext('test', exportFile, 'json');

      const fileExists = await fs.access(exportFile).then(() => true).catch(() => false);
      expect(fileExists).toBe(true);

      const content = await fs.readFile(exportFile, 'utf-8');
      const exported = JSON.parse(content);
      expect(exported.name).toBe('test');
    });

    it('should export context to YAML file', async () => {
      await contextManager.saveContext('test', { description: 'Test YAML' });
      const exportFile = path.join(testDir, 'export.yaml');

      await contextManager.exportContext('test', exportFile, 'yaml');

      const fileExists = await fs.access(exportFile).then(() => true).catch(() => false);
      expect(fileExists).toBe(true);

      const content = await fs.readFile(exportFile, 'utf-8');
      expect(content).toContain('name: "test"');
      expect(content).toContain('description: "Test YAML"');
    });

    it('should import context from JSON file', async () => {
      const context: Context = {
        name: 'imported',
        description: 'Imported context',
        createdAt: new Date(),
        updatedAt: new Date(),
        aliases: { test: 'value' }
      };

      const importFile = path.join(testDir, 'import.json');
      await fs.writeFile(importFile, JSON.stringify(context), 'utf-8');

      await contextManager.importContext(importFile);

      const contexts = await contextManager.listContexts();
      expect(contexts.some(c => c.name === 'imported')).toBe(true);
    });

    it('should import context with custom name', async () => {
      const context: Context = {
        name: 'original',
        createdAt: new Date(),
        updatedAt: new Date()
      };

      const importFile = path.join(testDir, 'import.json');
      await fs.writeFile(importFile, JSON.stringify(context), 'utf-8');

      await contextManager.importContext(importFile, 'custom-name');

      const loaded = await contextManager.showContext('custom-name');
      expect(loaded.name).toBe('custom-name');
    });
  });

  describe('Context Diff', () => {
    it('should detect database differences', async () => {
      contextManager.updateCurrentContext({ database: 'db1' });
      await contextManager.saveContext('context1');

      contextManager.updateCurrentContext({ database: 'db2' });
      await contextManager.saveContext('context2');

      const diff = await contextManager.diffContexts('context1', 'context2');
      expect(diff.differences.database).toBeDefined();
      expect(diff.differences.database?.context1).toBe('db1');
      expect(diff.differences.database?.context2).toBe('db2');
    });

    it('should detect alias differences', async () => {
      contextManager.setAlias('alias1', 'value1');
      await contextManager.saveContext('context1', { includeAliases: true });

      contextManager = new ContextManager(testDir);
      await contextManager.initialize();
      contextManager.setAlias('alias2', 'value2');
      await contextManager.saveContext('context2', { includeAliases: true });

      const diff = await contextManager.diffContexts('context1', 'context2');
      expect(diff.differences.aliases?.added).toContain('alias2');
      expect(diff.differences.aliases?.removed).toContain('alias1');
    });

    it('should detect configuration differences', async () => {
      contextManager.setConfig('setting1', 'value1');
      await contextManager.saveContext('context1', { includeConfig: true });

      contextManager = new ContextManager(testDir);
      await contextManager.initialize();
      contextManager.setConfig('setting2', 'value2');
      await contextManager.saveContext('context2', { includeConfig: true });

      const diff = await contextManager.diffContexts('context1', 'context2');
      expect(diff.differences.configuration?.added).toContain('setting2');
      expect(diff.differences.configuration?.removed).toContain('setting1');
    });

    it('should detect modified values', async () => {
      contextManager.setAlias('key', 'value1');
      await contextManager.saveContext('context1', { includeAliases: true });

      contextManager = new ContextManager(testDir);
      await contextManager.initialize();
      contextManager.setAlias('key', 'value2');
      await contextManager.saveContext('context2', { includeAliases: true });

      const diff = await contextManager.diffContexts('context1', 'context2');
      expect(diff.differences.aliases?.modified).toHaveLength(1);
      expect(diff.differences.aliases?.modified[0].key).toBe('key');
    });

    it('should detect query history count differences', async () => {
      contextManager.addQueryToHistory({ query: 'Q1', timestamp: Date.now(), success: true });
      await contextManager.saveContext('context1', { includeHistory: true });

      contextManager = new ContextManager(testDir);
      await contextManager.initialize();
      contextManager.addQueryToHistory({ query: 'Q1', timestamp: Date.now(), success: true });
      contextManager.addQueryToHistory({ query: 'Q2', timestamp: Date.now(), success: true });
      await contextManager.saveContext('context2', { includeHistory: true });

      const diff = await contextManager.diffContexts('context1', 'context2');
      expect(diff.differences.historyCount).toBeDefined();
      expect(diff.differences.historyCount?.context1).toBe(1);
      expect(diff.differences.historyCount?.context2).toBe(2);
    });
  });

  describe('Session Management', () => {
    it('should start a new session', async () => {
      const sessionId = await contextManager.startSession('test-session');
      expect(sessionId).toBeTruthy();
      expect(sessionId).toContain('session_');
    });

    it('should end current session', async () => {
      await contextManager.startSession('test-session');
      await expect(contextManager.endSession()).resolves.not.toThrow();
    });

    it('should throw error when ending non-existent session', async () => {
      await expect(contextManager.endSession()).rejects.toThrow('No active session');
    });

    it('should list sessions', async () => {
      await contextManager.startSession('session1');
      await contextManager.endSession();
      await contextManager.startSession('session2');
      await contextManager.endSession();

      const sessions = await contextManager.listSessions();
      expect(sessions).toHaveLength(2);
    });

    it('should restore session', async () => {
      contextManager.setAlias('test', 'value');
      await contextManager.startSession('test-session');
      await contextManager.endSession();

      contextManager = new ContextManager(testDir);
      await contextManager.initialize();
      await contextManager.restoreSession('test-session');

      const context = await contextManager.getCurrentContext();
      expect(context?.aliases).toHaveProperty('test');
    });

    it('should export session', async () => {
      await contextManager.startSession('test-session');
      await contextManager.endSession();

      const exportFile = path.join(testDir, 'session.json');
      await contextManager.exportSession('test-session', exportFile);

      const fileExists = await fs.access(exportFile).then(() => true).catch(() => false);
      expect(fileExists).toBe(true);
    });

    it('should track session statistics', async () => {
      await contextManager.startSession('test-session');

      contextManager.addQueryToHistory({
        query: 'Q1',
        timestamp: Date.now(),
        duration: 100,
        success: true
      });
      contextManager.addQueryToHistory({
        query: 'Q2',
        timestamp: Date.now(),
        duration: 200,
        success: false
      });

      await contextManager.endSession();

      const sessions = await contextManager.listSessions();
      const session = sessions.find(s => s.name === 'test-session');

      expect(session?.statistics?.queriesExecuted).toBe(2);
      expect(session?.statistics?.errorsCount).toBe(1);
      expect(session?.statistics?.totalDuration).toBe(300);
      expect(session?.statistics?.successRate).toBe(50);
    });
  });

  describe('Current Context', () => {
    it('should return null when no current context', async () => {
      const context = await contextManager.getCurrentContext();
      expect(context).toBeNull();
    });

    it('should return current context after load', async () => {
      await contextManager.saveContext('test');
      await contextManager.loadContext('test');

      const context = await contextManager.getCurrentContext();
      expect(context).not.toBeNull();
      expect(context?.name).toBe('test');
    });

    it('should update current context', () => {
      contextManager.updateCurrentContext({ database: 'test-db' });

      expect(contextManager.getCurrentContext()).resolves.toMatchObject({
        database: 'test-db'
      });
    });
  });

  describe('Query History', () => {
    it('should add query to history', () => {
      const entry: QueryHistoryEntry = {
        query: 'SELECT * FROM users',
        timestamp: Date.now(),
        success: true
      };

      contextManager.addQueryToHistory(entry);

      expect(contextManager.getCurrentContext()).resolves.toMatchObject({
        queryHistory: [entry]
      });
    });

    it('should limit query history to 1000 entries', () => {
      for (let i = 0; i < 1100; i++) {
        contextManager.addQueryToHistory({
          query: `Query ${i}`,
          timestamp: Date.now(),
          success: true
        });
      }

      expect(contextManager.getCurrentContext()).resolves.toHaveProperty(
        'queryHistory',
        expect.arrayContaining([
          expect.objectContaining({ query: expect.stringContaining('Query') })
        ])
      );
    });
  });

  describe('Aliases', () => {
    it('should set alias', async () => {
      contextManager.setAlias('users', 'SELECT * FROM users');

      const context = await contextManager.getCurrentContext();
      expect(context?.aliases).toHaveProperty('users', 'SELECT * FROM users');
    });

    it('should update existing alias', async () => {
      contextManager.setAlias('users', 'SELECT * FROM users');
      contextManager.setAlias('users', 'SELECT id, name FROM users');

      const context = await contextManager.getCurrentContext();
      expect(context?.aliases?.users).toBe('SELECT id, name FROM users');
    });
  });

  describe('Configuration', () => {
    it('should set configuration value', async () => {
      contextManager.setConfig('timeout', 5000);

      const context = await contextManager.getCurrentContext();
      expect(context?.configuration).toHaveProperty('timeout', 5000);
    });

    it('should support different value types', async () => {
      contextManager.setConfig('string', 'value');
      contextManager.setConfig('number', 123);
      contextManager.setConfig('boolean', true);
      contextManager.setConfig('object', { nested: 'value' });

      const context = await contextManager.getCurrentContext();
      expect(context?.configuration).toMatchObject({
        string: 'value',
        number: 123,
        boolean: true,
        object: { nested: 'value' }
      });
    });
  });

  describe('Variables', () => {
    it('should set variable', async () => {
      contextManager.setVariable('user_id', 123);

      const context = await contextManager.getCurrentContext();
      expect(context?.variables).toHaveProperty('user_id', 123);
    });

    it('should support different variable types', async () => {
      contextManager.setVariable('string', 'value');
      contextManager.setVariable('number', 456);
      contextManager.setVariable('array', [1, 2, 3]);

      const context = await contextManager.getCurrentContext();
      expect(context?.variables).toMatchObject({
        string: 'value',
        number: 456,
        array: [1, 2, 3]
      });
    });
  });

  describe('Events', () => {
    it('should emit contextSaved event', async () => {
      const handler = vi.fn();
      contextManager.on('contextSaved', handler);

      await contextManager.saveContext('test');

      expect(handler).toHaveBeenCalledWith('test');
    });

    it('should emit contextLoaded event', async () => {
      await contextManager.saveContext('test');

      const handler = vi.fn();
      contextManager.on('contextLoaded', handler);

      await contextManager.loadContext('test');

      expect(handler).toHaveBeenCalledWith('test');
    });

    it('should emit contextDeleted event', async () => {
      await contextManager.saveContext('test');

      const handler = vi.fn();
      contextManager.on('contextDeleted', handler);

      await contextManager.deleteContext('test');

      expect(handler).toHaveBeenCalledWith('test');
    });

    it('should emit sessionStarted event', async () => {
      const handler = vi.fn();
      contextManager.on('sessionStarted', handler);

      const sessionId = await contextManager.startSession('test');

      expect(handler).toHaveBeenCalledWith(sessionId);
    });

    it('should emit sessionEnded event', async () => {
      const sessionId = await contextManager.startSession('test');

      const handler = vi.fn();
      contextManager.on('sessionEnded', handler);

      await contextManager.endSession();

      expect(handler).toHaveBeenCalledWith(sessionId);
    });
  });
});
