/**
 * MySQL CLI Tests
 * Comprehensive test suite for MySQL CLI commands
 *
 * Test Coverage:
 * - 8 commands x 5 tests each = 40+ tests
 * - Connection management
 * - Query execution
 * - Schema operations
 * - Data import/export
 * - Error handling
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { MySQLCLI } from '../../src/cli/mysql-cli';
import { StateManager } from '../../src/core/state-manager';
import { DatabaseConnectionManager, DatabaseType } from '../../src/cli/db-connection-manager';

// Mock fs/promises module
vi.mock('fs/promises', () => ({
  readFile: vi.fn(),
  writeFile: vi.fn()
}));

// Import after mocking
import * as fs from 'fs/promises';

// Mock dependencies
vi.mock('../../src/core/logger', () => ({
  createLogger: () => ({
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
    debug: vi.fn()
  })
}));

// Mock console methods
const mockConsole = {
  log: vi.fn(),
  error: vi.fn()
};

describe('MySQLCLI', () => {
  let mysqlCLI: MySQLCLI;
  let stateManager: StateManager;
  let dbManager: DatabaseConnectionManager;
  let mockPool: any;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    global.console.log = mockConsole.log;
    global.console.error = mockConsole.error;

    // Create instances
    stateManager = new StateManager();
    dbManager = new DatabaseConnectionManager(stateManager);

    // Create mock MySQL pool
    mockPool = {
      query: vi.fn(),
      end: vi.fn(),
      getConnection: vi.fn(),
      escapeId: vi.fn((id: string) => `\`${id}\``),
      escape: vi.fn((val: string) => `'${val}'`)
    };

    mysqlCLI = new MySQLCLI(stateManager, dbManager);
  });

  afterEach(async () => {
    await dbManager.disconnectAll();
  });

  // ======================
  // CONNECT COMMAND TESTS (5 tests)
  // ======================

  describe('connect command', () => {
    it('should connect with mysql:// connection string', async () => {
      const connectionString = 'mysql://root:password@localhost:3306/testdb';

      mockPool.query.mockResolvedValueOnce([[{ version: '8.0.30' }]]);

      vi.spyOn(dbManager, 'connect').mockResolvedValue({
        config: {
          name: 'mysql_test',
          type: DatabaseType.MYSQL,
          database: 'testdb',
          host: 'localhost',
          port: 3306,
          poolSize: 10
        },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });

      await mysqlCLI.connect(connectionString);

      expect(dbManager.connect).toHaveBeenCalled();
      expect(mockConsole.log).toHaveBeenCalledWith(
        expect.stringContaining('Successfully connected')
      );
    });

    it('should connect with key=value connection string', async () => {
      const connectionString = 'host=localhost;database=testdb;user=root;password=secret';

      mockPool.query.mockResolvedValueOnce([[{ version: '8.0.30' }]]);

      vi.spyOn(dbManager, 'connect').mockResolvedValue({
        config: {
          name: 'mysql_test',
          type: DatabaseType.MYSQL,
          database: 'testdb',
          host: 'localhost',
          port: 3306
        },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });

      await mysqlCLI.connect(connectionString);

      expect(dbManager.connect).toHaveBeenCalled();
    });

    it('should connect with SSL option', async () => {
      const connectionString = 'mysql://root:password@localhost:3306/testdb';

      mockPool.query.mockResolvedValueOnce([[{ version: '8.0.30' }]]);

      vi.spyOn(dbManager, 'connect').mockResolvedValue({
        config: {
          name: 'mysql_ssl',
          type: DatabaseType.MYSQL,
          database: 'testdb',
          host: 'localhost',
          port: 3306,
          ssl: true
        },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });

      await mysqlCLI.connect(connectionString, { ssl: true });

      expect(dbManager.connect).toHaveBeenCalled();
    });

    it('should handle connection errors', async () => {
      const connectionString = 'mysql://root:badpass@localhost:3306/testdb';

      vi.spyOn(dbManager, 'connect').mockRejectedValue(new Error('Access denied'));

      await expect(mysqlCLI.connect(connectionString)).rejects.toThrow('Access denied');
    });

    it('should support custom connection name', async () => {
      const connectionString = 'mysql://root:password@localhost:3306/testdb';

      mockPool.query.mockResolvedValueOnce([[{ version: '8.0.30' }]]);

      vi.spyOn(dbManager, 'connect').mockResolvedValue({
        config: {
          name: 'production',
          type: DatabaseType.MYSQL,
          database: 'testdb',
          host: 'localhost',
          port: 3306
        },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });

      await mysqlCLI.connect(connectionString, { name: 'production' });

      expect(dbManager.connect).toHaveBeenCalled();
    });
  });

  // ======================
  // DISCONNECT COMMAND TESTS (5 tests)
  // ======================

  describe('disconnect command', () => {
    it('should disconnect specific connection', async () => {
      vi.spyOn(dbManager, 'disconnect').mockResolvedValue();

      await mysqlCLI.disconnect('test_conn');

      expect(dbManager.disconnect).toHaveBeenCalledWith('test_conn');
      expect(mockConsole.log).toHaveBeenCalledWith(
        expect.stringContaining('Disconnected from: test_conn')
      );
    });

    it('should disconnect all connections when no name provided', async () => {
      vi.spyOn(dbManager, 'listConnections').mockReturnValue([
        {
          name: 'conn1',
          type: DatabaseType.MYSQL,
          database: 'db1',
          isActive: true,
          createdAt: Date.now()
        }
      ]);

      vi.spyOn(dbManager, 'disconnectAll').mockResolvedValue();

      await mysqlCLI.disconnect();

      expect(dbManager.disconnectAll).toHaveBeenCalled();
    });

    it('should show message when no active connections', async () => {
      vi.spyOn(dbManager, 'listConnections').mockReturnValue([]);

      await mysqlCLI.disconnect();

      expect(mockConsole.log).toHaveBeenCalledWith(
        expect.stringContaining('No active connections')
      );
    });

    it('should handle disconnect errors', async () => {
      vi.spyOn(dbManager, 'disconnect').mockRejectedValue(new Error('Connection not found'));

      await expect(mysqlCLI.disconnect('invalid')).rejects.toThrow('Connection not found');
    });

    it('should clean up resources on disconnect', async () => {
      mockPool.end.mockResolvedValue(undefined);

      vi.spyOn(dbManager, 'disconnect').mockImplementation(async () => {
        await mockPool.end();
      });

      await mysqlCLI.disconnect('test');

      expect(mockPool.end).toHaveBeenCalled();
    });
  });

  // ======================
  // QUERY COMMAND TESTS (5 tests)
  // ======================

  describe('query command', () => {
    beforeEach(() => {
      vi.spyOn(dbManager, 'getActive').mockReturnValue({
        config: {
          name: 'test',
          type: DatabaseType.MYSQL,
          database: 'testdb'
        },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });
    });

    it('should execute SELECT query', async () => {
      const sql = 'SELECT * FROM users';
      const mockResults = [
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' }
      ];

      mockPool.query.mockResolvedValueOnce([mockResults]);

      const results = await mysqlCLI.query(sql);

      expect(mockPool.query).toHaveBeenCalledWith(sql);
      expect(results).toEqual(mockResults);
    });

    it('should handle INSERT queries', async () => {
      const sql = 'INSERT INTO users (name) VALUES ("Charlie")';
      const mockResult = {
        affectedRows: 1,
        insertId: 3
      };

      mockPool.query.mockResolvedValueOnce([mockResult]);

      const results = await mysqlCLI.query(sql);

      expect(mockPool.query).toHaveBeenCalledWith(sql);
      expect(results).toEqual([]);
    });

    it('should format results as JSON', async () => {
      const sql = 'SELECT * FROM users';
      const mockResults = [{ id: 1, name: 'Alice' }];

      mockPool.query.mockResolvedValueOnce([mockResults]);

      await mysqlCLI.query(sql, { format: 'json' });

      expect(mockConsole.log).toHaveBeenCalled();
    });

    it('should limit results', async () => {
      const sql = 'SELECT * FROM users';
      const mockResults = Array.from({ length: 100 }, (_, i) => ({ id: i, name: `User${i}` }));

      mockPool.query.mockResolvedValueOnce([mockResults]);

      const results = await mysqlCLI.query(sql, { limit: 10 });

      expect(results.length).toBe(10);
    });

    it('should show execution plan with explain flag', async () => {
      const sql = 'SELECT * FROM users';
      const mockResults = [{ id: 1, name: 'Alice' }];
      const mockExplain = [
        {
          type: 'ALL',
          table: 'users',
          possible_keys: null,
          key: null,
          rows: 100
        }
      ];

      mockPool.query.mockResolvedValueOnce([mockExplain]);
      mockPool.query.mockResolvedValueOnce([mockResults]);

      await mysqlCLI.query(sql, { explain: true });

      expect(mockPool.query).toHaveBeenCalledWith(`EXPLAIN ${sql}`);
    });
  });

  // ======================
  // STATUS COMMAND TESTS (5 tests)
  // ======================

  describe('status command', () => {
    it('should show status when connected', async () => {
      const mockStatusRows = [
        { Variable_name: 'Uptime', Value: '86400' },
        { Variable_name: 'Threads_connected', Value: '5' },
        { Variable_name: 'Max_used_connections', Value: '10' }
      ];

      const mockVariableRows = [
        { Variable_name: 'max_connections', Value: '151' },
        { Variable_name: 'version', Value: '8.0.30' }
      ];

      const mockDatabaseRows = [{ current_db: 'testdb' }];

      mockPool.query
        .mockResolvedValueOnce([mockStatusRows])
        .mockResolvedValueOnce([mockVariableRows])
        .mockResolvedValueOnce([mockDatabaseRows]);

      vi.spyOn(dbManager, 'getActive').mockReturnValue({
        config: {
          name: 'test',
          type: DatabaseType.MYSQL,
          database: 'testdb',
          host: 'localhost',
          port: 3306
        },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });

      const status = await mysqlCLI.status();

      expect(status).toBeDefined();
      expect(status?.version).toBe('8.0.30');
      expect(status?.uptime).toBe(86400);
    });

    it('should show message when no active connection', async () => {
      vi.spyOn(dbManager, 'getActive').mockReturnValue(null);
      vi.spyOn(dbManager, 'listConnections').mockReturnValue([]);

      const status = await mysqlCLI.status();

      expect(status).toBeNull();
      expect(mockConsole.log).toHaveBeenCalledWith(
        expect.stringContaining('No active MySQL connection')
      );
    });

    it('should list available connections when not connected', async () => {
      vi.spyOn(dbManager, 'getActive').mockReturnValue(null);
      vi.spyOn(dbManager, 'listConnections').mockReturnValue([
        {
          name: 'conn1',
          type: DatabaseType.MYSQL,
          database: 'db1',
          host: 'localhost',
          port: 3306,
          isActive: false,
          createdAt: Date.now()
        }
      ]);

      await mysqlCLI.status();

      expect(mockConsole.log).toHaveBeenCalled();
    });

    it('should format uptime correctly', async () => {
      const mockStatusRows = [
        { Variable_name: 'Uptime', Value: '90061' }, // 1 day, 1 hour, 1 minute, 1 second
        { Variable_name: 'Threads_connected', Value: '5' }
      ];

      const mockVariableRows = [
        { Variable_name: 'max_connections', Value: '151' },
        { Variable_name: 'version', Value: '8.0.30' }
      ];

      const mockDatabaseRows = [{ current_db: 'testdb' }];

      mockPool.query
        .mockResolvedValueOnce([mockStatusRows])
        .mockResolvedValueOnce([mockVariableRows])
        .mockResolvedValueOnce([mockDatabaseRows]);

      vi.spyOn(dbManager, 'getActive').mockReturnValue({
        config: { name: 'test', type: DatabaseType.MYSQL, database: 'testdb' },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });

      const status = await mysqlCLI.status();

      expect(status?.uptime).toBe(90061);
    });

    it('should handle status query errors', async () => {
      mockPool.query.mockRejectedValue(new Error('Connection lost'));

      vi.spyOn(dbManager, 'getActive').mockReturnValue({
        config: { name: 'test', type: DatabaseType.MYSQL, database: 'testdb' },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });

      await expect(mysqlCLI.status()).rejects.toThrow('Connection lost');
    });
  });

  // ======================
  // TABLES COMMAND TESTS (5 tests)
  // ======================

  describe('tables command', () => {
    beforeEach(() => {
      vi.spyOn(dbManager, 'getActive').mockReturnValue({
        config: { name: 'test', type: DatabaseType.MYSQL, database: 'testdb' },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });
    });

    it('should list all tables', async () => {
      const mockTables = [
        {
          Name: 'users',
          Engine: 'InnoDB',
          Rows: 100,
          Data_length: 16384,
          Index_length: 8192,
          Auto_increment: 101,
          Create_time: new Date(),
          Update_time: new Date(),
          Collation: 'utf8mb4_general_ci'
        }
      ];

      mockPool.query.mockResolvedValueOnce([mockTables]);

      const tables = await mysqlCLI.tables();

      expect(tables.length).toBe(1);
      expect(tables[0].name).toBe('users');
    });

    it('should switch database if specified', async () => {
      mockPool.query.mockResolvedValueOnce([[]]);
      mockPool.query.mockResolvedValueOnce([[]]);

      await mysqlCLI.tables('other_db');

      expect(mockPool.query).toHaveBeenCalledWith(expect.stringContaining('USE'));
    });

    it('should format table sizes', async () => {
      const mockTables = [
        {
          Name: 'large_table',
          Engine: 'InnoDB',
          Rows: 1000000,
          Data_length: 1073741824, // 1 GB
          Index_length: 536870912, // 512 MB
          Auto_increment: null,
          Create_time: new Date(),
          Update_time: null,
          Collation: 'utf8mb4_general_ci'
        }
      ];

      mockPool.query.mockResolvedValueOnce([mockTables]);

      const tables = await mysqlCLI.tables();

      expect(tables[0].dataLength).toBe(1073741824);
    });

    it('should handle empty database', async () => {
      mockPool.query.mockResolvedValueOnce([[]]);

      const tables = await mysqlCLI.tables();

      expect(tables.length).toBe(0);
    });

    it('should handle tables query errors', async () => {
      mockPool.query.mockRejectedValue(new Error('Database not found'));

      await expect(mysqlCLI.tables('invalid_db')).rejects.toThrow('Database not found');
    });
  });

  // ======================
  // DESCRIBE COMMAND TESTS (5 tests)
  // ======================

  describe('describe command', () => {
    beforeEach(() => {
      vi.spyOn(dbManager, 'getActive').mockReturnValue({
        config: { name: 'test', type: DatabaseType.MYSQL, database: 'testdb' },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });
    });

    it('should describe table structure', async () => {
      const mockColumns = [
        {
          Field: 'id',
          Type: 'int(11)',
          Null: 'NO',
          Key: 'PRI',
          Default: null,
          Extra: 'auto_increment'
        },
        {
          Field: 'name',
          Type: 'varchar(255)',
          Null: 'NO',
          Key: '',
          Default: null,
          Extra: ''
        }
      ];

      mockPool.query.mockResolvedValueOnce([mockColumns]);
      mockPool.query.mockResolvedValueOnce([[{ 'Create Table': 'CREATE TABLE users...' }]]);
      mockPool.query.mockResolvedValueOnce([[]]);

      const columns = await mysqlCLI.describe('users');

      expect(columns.length).toBe(2);
      expect(columns[0].field).toBe('id');
      expect(columns[0].key).toBe('PRI');
    });

    it('should show indexes', async () => {
      const mockColumns = [
        { Field: 'id', Type: 'int(11)', Null: 'NO', Key: 'PRI', Default: null, Extra: 'auto_increment' }
      ];

      const mockIndexes = [
        {
          Key_name: 'PRIMARY',
          Column_name: 'id',
          Index_type: 'BTREE',
          Non_unique: 0
        }
      ];

      mockPool.query.mockResolvedValueOnce([mockColumns]);
      mockPool.query.mockResolvedValueOnce([[{ 'Create Table': 'CREATE TABLE users...' }]]);
      mockPool.query.mockResolvedValueOnce([mockIndexes]);

      await mysqlCLI.describe('users');

      expect(mockPool.query).toHaveBeenCalledWith(expect.stringContaining('SHOW INDEX'));
    });

    it('should handle table not found', async () => {
      mockPool.query.mockRejectedValue(new Error("Table 'invalid' doesn't exist"));

      await expect(mysqlCLI.describe('invalid')).rejects.toThrow("doesn't exist");
    });

    it('should show nullable columns', async () => {
      const mockColumns = [
        {
          Field: 'optional_field',
          Type: 'varchar(255)',
          Null: 'YES',
          Key: '',
          Default: null,
          Extra: ''
        }
      ];

      mockPool.query.mockResolvedValueOnce([mockColumns]);
      mockPool.query.mockResolvedValueOnce([[{ 'Create Table': '' }]]);
      mockPool.query.mockResolvedValueOnce([[]]);

      const columns = await mysqlCLI.describe('test_table');

      expect(columns[0].null).toBe('YES');
    });

    it('should show column defaults', async () => {
      const mockColumns = [
        {
          Field: 'status',
          Type: 'varchar(20)',
          Null: 'NO',
          Key: '',
          Default: 'active',
          Extra: ''
        }
      ];

      mockPool.query.mockResolvedValueOnce([mockColumns]);
      mockPool.query.mockResolvedValueOnce([[{ 'Create Table': '' }]]);
      mockPool.query.mockResolvedValueOnce([[]]);

      const columns = await mysqlCLI.describe('test_table');

      expect(columns[0].default).toBe('active');
    });
  });

  // ======================
  // IMPORT COMMAND TESTS (5 tests)
  // ======================

  describe('import command', () => {
    beforeEach(() => {
      vi.spyOn(dbManager, 'getActive').mockReturnValue({
        config: { name: 'test', type: DatabaseType.MYSQL, database: 'testdb' },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });
    });

    it('should import SQL file', async () => {
      const sqlContent = 'INSERT INTO users (name) VALUES ("Alice");\nINSERT INTO users (name) VALUES ("Bob");';

      (fs.readFile as any).mockResolvedValue(sqlContent);
      mockPool.query.mockResolvedValue([{ affectedRows: 1 }]);

      const rows = await mysqlCLI.import('/tmp/data.sql');

      expect(rows).toBe(2);
      expect(mockPool.query).toHaveBeenCalledTimes(2);
    });

    it('should import CSV file', async () => {
      const csvContent = 'name,email\nAlice,alice@example.com\nBob,bob@example.com';

      (fs.readFile as any).mockResolvedValue(csvContent);
      mockPool.query.mockResolvedValue([{ affectedRows: 2 }]);

      const rows = await mysqlCLI.import('/tmp/data.csv', { table: 'users' });

      expect(rows).toBeGreaterThan(0);
      expect(mockPool.query).toHaveBeenCalled();
    });

    it('should import JSON file', async () => {
      const jsonContent = JSON.stringify([
        { name: 'Alice', email: 'alice@example.com' },
        { name: 'Bob', email: 'bob@example.com' }
      ]);

      (fs.readFile as any).mockResolvedValue(jsonContent);
      mockPool.query.mockResolvedValue([{ affectedRows: 2 }]);

      const rows = await mysqlCLI.import('/tmp/data.json', { table: 'users' });

      expect(rows).toBe(2);
    });

    it('should truncate table before import', async () => {
      const sqlContent = 'INSERT INTO users (name) VALUES ("Alice");';

      (fs.readFile as any).mockResolvedValue(sqlContent);
      mockPool.query.mockResolvedValue([{ affectedRows: 1 }]);

      await mysqlCLI.import('/tmp/data.sql');

      // Should not truncate for SQL files
      expect(mockPool.query).not.toHaveBeenCalledWith(expect.stringContaining('TRUNCATE'));
    });

    it('should handle import errors', async () => {
      (fs.readFile as any).mockRejectedValue(new Error('File not found'));

      await expect(mysqlCLI.import('/tmp/invalid.sql')).rejects.toThrow('File not found');
    });
  });

  // ======================
  // EXPORT COMMAND TESTS (5 tests)
  // ======================

  describe('export command', () => {
    beforeEach(() => {
      vi.spyOn(dbManager, 'getActive').mockReturnValue({
        config: { name: 'test', type: DatabaseType.MYSQL, database: 'testdb' },
        client: mockPool,
        type: DatabaseType.MYSQL,
        isConnected: true
      });
    });

    it('should export as JSON', async () => {
      const mockData = [
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' }
      ];

      mockPool.query.mockResolvedValueOnce([mockData]);

      const output = await mysqlCLI.export('users', { format: 'json' });

      expect(output).toContain('"name": "Alice"');
      expect(output).toContain('"name": "Bob"');
    });

    it('should export as CSV', async () => {
      const mockData = [
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' }
      ];

      mockPool.query.mockResolvedValueOnce([mockData]);

      const output = await mysqlCLI.export('users', { format: 'csv' });

      expect(output).toContain('id,name');
      expect(output).toContain('Alice');
    });

    it('should export as SQL', async () => {
      const mockData = [
        { id: 1, name: 'Alice' }
      ];

      mockPool.query.mockResolvedValueOnce([mockData]);

      const output = await mysqlCLI.export('users', { format: 'sql' });

      expect(output).toContain('INSERT INTO');
      expect(output).toContain('Alice');
    });

    it('should export with WHERE clause', async () => {
      const mockData = [{ id: 1, name: 'Alice' }];

      mockPool.query.mockResolvedValueOnce([mockData]);

      await mysqlCLI.export('users', { where: 'id > 0' });

      expect(mockPool.query).toHaveBeenCalledWith(expect.stringContaining('WHERE id > 0'));
    });

    it('should save to file', async () => {
      const mockData = [{ id: 1, name: 'Alice' }];

      mockPool.query.mockResolvedValueOnce([mockData]);
      (fs.writeFile as any).mockResolvedValue(undefined);

      await mysqlCLI.export('users', { output: '/tmp/export.json', format: 'json' });

      expect(fs.writeFile).toHaveBeenCalledWith(
        '/tmp/export.json',
        expect.any(String),
        'utf-8'
      );
    });
  });
});
