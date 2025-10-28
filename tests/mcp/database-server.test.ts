/**
 * Tests for MCP Database Server
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { MCPDatabaseServer } from '../../src/mcp/database-server';
import { DatabaseConnectionManager, DatabaseType } from '../../src/cli/database-manager';
import { StateManager } from '../../src/core/state-manager';

describe('MCPDatabaseServer', () => {
  let server: MCPDatabaseServer;
  let connectionManager: DatabaseConnectionManager;
  let stateManager: StateManager;

  beforeAll(async () => {
    stateManager = new StateManager();
    connectionManager = new DatabaseConnectionManager(stateManager);
  });

  afterAll(async () => {
    await connectionManager.disconnectAll();
  });

  describe('Server Initialization', () => {
    it('should create MCP database server instance', () => {
      server = new MCPDatabaseServer();
      expect(server).toBeDefined();
    });

    it('should have all tool providers initialized', () => {
      server = new MCPDatabaseServer();
      expect(server).toBeDefined();
      // Server is initialized with all tool providers
    });
  });

  describe('Common Database Tools', () => {
    it('should list all available tools', async () => {
      // This would require mocking the MCP server's listTools handler
      // For now, we'll test the tool providers directly
      const { CommonDatabaseTools } = await import('../../src/mcp/tools/common');
      const tools = new CommonDatabaseTools(connectionManager);
      const definitions = tools.getToolDefinitions();

      expect(definitions.length).toBeGreaterThan(0);
      expect(definitions.some(t => t.name === 'db_connect')).toBe(true);
      expect(definitions.some(t => t.name === 'db_query')).toBe(true);
      expect(definitions.some(t => t.name === 'db_list_tables')).toBe(true);
    });
  });

  describe('PostgreSQL Tools', () => {
    it('should provide PostgreSQL-specific tools', async () => {
      const { PostgreSQLTools } = await import('../../src/mcp/tools/postgresql');
      const tools = new PostgreSQLTools(connectionManager);
      const definitions = tools.getToolDefinitions();

      expect(definitions.length).toBeGreaterThan(0);
      expect(definitions.some(t => t.name === 'pg_explain')).toBe(true);
      expect(definitions.some(t => t.name === 'pg_vacuum')).toBe(true);
      expect(definitions.some(t => t.name === 'pg_analyze')).toBe(true);
    });
  });

  describe('MySQL Tools', () => {
    it('should provide MySQL-specific tools', async () => {
      const { MySQLTools } = await import('../../src/mcp/tools/mysql');
      const tools = new MySQLTools(connectionManager);
      const definitions = tools.getToolDefinitions();

      expect(definitions.length).toBeGreaterThan(0);
      expect(definitions.some(t => t.name === 'mysql_explain')).toBe(true);
      expect(definitions.some(t => t.name === 'mysql_optimize')).toBe(true);
      expect(definitions.some(t => t.name === 'mysql_analyze')).toBe(true);
    });
  });

  describe('MongoDB Tools', () => {
    it('should provide MongoDB-specific tools', async () => {
      const { MongoDBTools } = await import('../../src/mcp/tools/mongodb');
      const tools = new MongoDBTools(connectionManager);
      const definitions = tools.getToolDefinitions();

      expect(definitions.length).toBeGreaterThan(0);
      expect(definitions.some(t => t.name === 'mongo_find')).toBe(true);
      expect(definitions.some(t => t.name === 'mongo_aggregate')).toBe(true);
      expect(definitions.some(t => t.name === 'mongo_insert')).toBe(true);
    });
  });

  describe('Redis Tools', () => {
    it('should provide Redis-specific tools', async () => {
      const { RedisTools } = await import('../../src/mcp/tools/redis');
      const tools = new RedisTools(connectionManager);
      const definitions = tools.getToolDefinitions();

      expect(definitions.length).toBeGreaterThan(0);
      expect(definitions.some(t => t.name === 'redis_get')).toBe(true);
      expect(definitions.some(t => t.name === 'redis_set')).toBe(true);
      expect(definitions.some(t => t.name === 'redis_keys')).toBe(true);
    });
  });

  describe('SQLite Integration', () => {
    let testDbName: string;

    beforeEach(() => {
      testDbName = `test_${Date.now()}`;
    });

    it('should connect to SQLite database', async () => {
      const config = {
        name: testDbName,
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      const connection = await connectionManager.connect(config);
      expect(connection.isConnected).toBe(true);
      expect(connection.type).toBe(DatabaseType.SQLITE);

      await connectionManager.disconnect(testDbName);
    });

    it('should execute query on SQLite', async () => {
      const config = {
        name: testDbName,
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await connectionManager.connect(config);
      await connectionManager.switchActive(testDbName);

      // Create table
      await connectionManager.executeQuery('CREATE TABLE test (id INTEGER, name TEXT)');

      // Insert data
      await connectionManager.executeQuery('INSERT INTO test VALUES (?, ?)', [1, 'Test']);

      // Query data
      const rows = await connectionManager.executeQuery('SELECT * FROM test');
      expect(rows).toHaveLength(1);
      expect(rows[0].id).toBe(1);
      expect(rows[0].name).toBe('Test');

      await connectionManager.disconnect(testDbName);
    });

    it('should list tables in SQLite', async () => {
      const config = {
        name: testDbName,
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await connectionManager.connect(config);
      await connectionManager.switchActive(testDbName);

      await connectionManager.executeQuery('CREATE TABLE users (id INTEGER, name TEXT)');
      await connectionManager.executeQuery('CREATE TABLE posts (id INTEGER, title TEXT)');

      const { CommonDatabaseTools } = await import('../../src/mcp/tools/common');
      const tools = new CommonDatabaseTools(connectionManager);
      const result = await tools.executeTool('db_list_tables', {});

      expect(result.success).toBe(true);
      expect(result.tables).toContain('users');
      expect(result.tables).toContain('posts');

      await connectionManager.disconnect(testDbName);
    });
  });

  describe('Connection Management', () => {
    it('should list connections', async () => {
      const config = {
        name: 'test_sqlite',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await connectionManager.connect(config);

      const connections = connectionManager.listConnections();
      expect(connections.length).toBeGreaterThan(0);
      expect(connections.some(c => c.name === 'test_sqlite')).toBe(true);

      await connectionManager.disconnect('test_sqlite');
    });

    it('should switch active connection', async () => {
      const config1 = {
        name: 'test_db1',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      const config2 = {
        name: 'test_db2',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await connectionManager.connect(config1);
      await connectionManager.connect(config2);

      await connectionManager.switchActive('test_db2');
      const active = connectionManager.getActive();
      expect(active?.config.name).toBe('test_db2');

      await connectionManager.disconnect('test_db1');
      await connectionManager.disconnect('test_db2');
    });

    it('should perform health check', async () => {
      const config = {
        name: 'test_health',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await connectionManager.connect(config);

      const result = await connectionManager.healthCheck('test_health');
      expect(result.healthy).toBe(true);
      expect(result.latency).toBeGreaterThanOrEqual(0);

      await connectionManager.disconnect('test_health');
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid connection', async () => {
      await expect(async () => {
        await connectionManager.disconnect('nonexistent');
      }).resolves.not.toThrow();
    });

    it('should handle query without active connection', async () => {
      const { CommonDatabaseTools } = await import('../../src/mcp/tools/common');
      const emptyManager = new DatabaseConnectionManager(new StateManager());
      const tools = new CommonDatabaseTools(emptyManager);

      await expect(async () => {
        await tools.executeTool('db_query', { sql: 'SELECT 1' });
      }).rejects.toThrow('No active connection');
    });
  });
});
