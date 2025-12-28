/**
 * Database Connection Manager Tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { DatabaseConnectionManager, DatabaseType } from '../../src/cli/database-manager';
import { StateManager } from '../../src/core/state-manager';

describe('DatabaseConnectionManager', () => {
  let manager: DatabaseConnectionManager;
  let stateManager: StateManager;

  beforeEach(() => {
    stateManager = new StateManager();
    manager = new DatabaseConnectionManager(stateManager);
  });

  afterEach(async () => {
    await manager.disconnectAll();
  });

  describe('parseConnectionString', () => {
    it('should parse PostgreSQL connection string', () => {
      const result = DatabaseConnectionManager.parseConnectionString(
        'postgresql://user:pass@localhost:5432/mydb'
      );

      expect(result.type).toBe(DatabaseType.POSTGRESQL);
      expect(result.host).toBe('localhost');
      expect(result.port).toBe(5432);
      expect(result.database).toBe('mydb');
      expect(result.username).toBe('user');
      expect(result.password).toBe('pass');
    });

    it('should parse MySQL connection string', () => {
      const result = DatabaseConnectionManager.parseConnectionString(
        'mysql://root:secret@localhost:3306/testdb'
      );

      expect(result.type).toBe(DatabaseType.MYSQL);
      expect(result.host).toBe('localhost');
      expect(result.port).toBe(3306);
      expect(result.database).toBe('testdb');
      expect(result.username).toBe('root');
      expect(result.password).toBe('secret');
    });

    it('should parse MongoDB connection string', () => {
      const result = DatabaseConnectionManager.parseConnectionString(
        'mongodb://localhost:27017/appdb'
      );

      expect(result.type).toBe(DatabaseType.MONGODB);
      expect(result.host).toBe('localhost');
      expect(result.port).toBe(27017);
      expect(result.database).toBe('appdb');
    });

    it('should parse Redis connection string', () => {
      const result = DatabaseConnectionManager.parseConnectionString(
        'redis://localhost:6379'
      );

      expect(result.type).toBe(DatabaseType.REDIS);
      expect(result.host).toBe('localhost');
      expect(result.port).toBe(6379);
    });

    it('should parse SQLite connection string', () => {
      const result = DatabaseConnectionManager.parseConnectionString(
        'sqlite://path/to/database.db'
      );

      expect(result.type).toBe(DatabaseType.SQLITE);
      expect(result.connectionString).toContain('sqlite://');
    });

    it('should detect SSL from connection string', () => {
      const result = DatabaseConnectionManager.parseConnectionString(
        'postgresql://localhost/mydb?ssl=true'
      );

      expect(result.ssl).toBe(true);
    });

    it('should throw error for unsupported protocol', () => {
      expect(() => {
        DatabaseConnectionManager.parseConnectionString('http://localhost');
      }).toThrow('Unsupported protocol');
    });
  });

  describe('SQLite connection', () => {
    it('should connect to in-memory SQLite database', async () => {
      const config = {
        name: 'test-sqlite',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      const connection = await manager.connect(config);

      expect(connection.type).toBe(DatabaseType.SQLITE);
      expect(connection.isConnected).toBe(true);
      expect(manager.listConnections()).toHaveLength(1);
    });

    it('should execute query on SQLite', async () => {
      const config = {
        name: 'test-sqlite',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config);

      const results = await manager.executeQuery('SELECT 1 as value');
      expect(results).toHaveLength(1);
      expect(results[0].value).toBe(1);
    });
  });

  describe('Connection management', () => {
    it('should list connections', async () => {
      const config1 = {
        name: 'conn1',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      const config2 = {
        name: 'conn2',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config1);
      await manager.connect(config2);

      const connections = manager.listConnections();
      expect(connections).toHaveLength(2);
      expect(connections[0].name).toBe('conn1');
      expect(connections[1].name).toBe('conn2');
    });

    it('should set first connection as active', async () => {
      const config = {
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config);

      const active = manager.getActive();
      expect(active).not.toBeNull();
      expect(active?.config.name).toBe('test-conn');
    });

    it('should switch active connection', async () => {
      const config1 = {
        name: 'conn1',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      const config2 = {
        name: 'conn2',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config1);
      await manager.connect(config2);
      await manager.switchActive('conn2');

      const active = manager.getActive();
      expect(active?.config.name).toBe('conn2');
    });

    it('should throw error when switching to non-existent connection', async () => {
      await expect(manager.switchActive('non-existent')).rejects.toThrow('Connection not found');
    });

    it('should disconnect specific connection', async () => {
      const config = {
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config);
      expect(manager.listConnections()).toHaveLength(1);

      await manager.disconnect('test-conn');
      expect(manager.listConnections()).toHaveLength(0);
    });

    it('should disconnect all connections', async () => {
      const config1 = {
        name: 'conn1',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      const config2 = {
        name: 'conn2',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config1);
      await manager.connect(config2);
      expect(manager.listConnections()).toHaveLength(2);

      await manager.disconnectAll();
      expect(manager.listConnections()).toHaveLength(0);
    });

    it('should replace existing connection with same name', async () => {
      const config1 = {
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      const config2 = {
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config1);
      expect(manager.listConnections()).toHaveLength(1);

      await manager.connect(config2);
      expect(manager.listConnections()).toHaveLength(1);
    });
  });

  describe('Health checks', () => {
    it('should perform health check on connection', async () => {
      const config = {
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config);

      const health = await manager.healthCheck('test-conn');
      expect(health.healthy).toBe(true);
      expect(health.latency).toBeGreaterThan(0);
      expect(health.timestamp).toBeGreaterThan(0);
    });

    it('should return unhealthy for non-existent connection', async () => {
      const health = await manager.healthCheck('non-existent');
      expect(health.healthy).toBe(false);
      expect(health.error).toBe('Connection not found');
    });

    it('should test connection without saving', async () => {
      const config = {
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      const result = await manager.testConnection(config);
      expect(result.healthy).toBe(true);
      expect(manager.listConnections()).toHaveLength(0);
    });
  });

  describe('Statistics', () => {
    it('should return connection statistics', async () => {
      const config1 = {
        name: 'conn1',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      const config2 = {
        name: 'conn2',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config1);
      await manager.connect(config2);

      const stats = manager.getStatistics();
      expect(stats.totalConnections).toBe(2);
      expect(stats.activeConnection).toBe('conn1');
      expect(stats.connectionsByType[DatabaseType.SQLITE]).toBe(2);
    });

    it('should track healthy connections', async () => {
      const config = {
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config);
      await manager.healthCheck('test-conn');

      const stats = manager.getStatistics();
      expect(stats.healthyConnections).toBeGreaterThan(0);
    });
  });

  describe('Error handling', () => {
    it('should handle invalid connection string', () => {
      expect(() => {
        DatabaseConnectionManager.parseConnectionString('invalid');
      }).toThrow();
    });

    it('should emit error events on connection failure', async () => {
      const errorSpy = vi.fn();
      manager.on('error', errorSpy);

      const config = {
        name: 'bad-conn',
        type: DatabaseType.POSTGRESQL,
        host: 'invalid-host-12345',
        port: 5432,
        database: 'test',
        username: 'user',
        password: 'pass'
      };

      try {
        await manager.connect(config);
      } catch (error) {
        // Expected to fail
      }

      // Error should have been emitted
      expect(errorSpy).toHaveBeenCalled();
    });

    it('should handle disconnect of non-existent connection gracefully', async () => {
      await expect(manager.disconnect('non-existent')).resolves.toBeUndefined();
    });
  });

  describe('Events', () => {
    it('should emit connected event', async () => {
      const spy = vi.fn();
      manager.on('connected', spy);

      const config = {
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config);
      expect(spy).toHaveBeenCalledWith('test-conn');
    });

    it('should emit disconnected event', async () => {
      const spy = vi.fn();
      manager.on('disconnected', spy);

      const config = {
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config);
      await manager.disconnect('test-conn');

      expect(spy).toHaveBeenCalledWith('test-conn');
    });

    it('should emit activeChanged event', async () => {
      const spy = vi.fn();
      manager.on('activeChanged', spy);

      const config1 = {
        name: 'conn1',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      const config2 = {
        name: 'conn2',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config1);
      await manager.connect(config2);
      await manager.switchActive('conn2');

      expect(spy).toHaveBeenCalledWith('conn2');
    });
  });

  describe('Connection info', () => {
    it('should provide connection info with correct fields', async () => {
      const config = {
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: 'test.db',
        host: 'localhost'
      };

      await manager.connect(config);

      const connections = manager.listConnections();
      expect(connections[0]).toMatchObject({
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: 'test.db',
        isActive: true
      });

      expect(connections[0].createdAt).toBeGreaterThan(0);
    });

    it('should get connection by name', async () => {
      const config = {
        name: 'test-conn',
        type: DatabaseType.SQLITE,
        database: ':memory:'
      };

      await manager.connect(config);

      const connection = manager.getConnection('test-conn');
      expect(connection).not.toBeUndefined();
      expect(connection?.config.name).toBe('test-conn');
    });

    it('should return undefined for non-existent connection', () => {
      const connection = manager.getConnection('non-existent');
      expect(connection).toBeUndefined();
    });
  });
});
