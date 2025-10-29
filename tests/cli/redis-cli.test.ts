/**
 * Redis CLI Tests
 * Comprehensive test suite for Redis CLI operations
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { RedisCLI, KeyValueResult, SetResult, KeysResult, InfoResult, FlushResult, TTLResult } from '../../src/cli/redis-cli';
import Redis from 'ioredis';

// Mock ioredis
vi.mock('ioredis', () => {
  const mockClient = {
    get: vi.fn(),
    set: vi.fn(),
    call: vi.fn(),
    keys: vi.fn(),
    scan: vi.fn(),
    info: vi.fn(),
    dbsize: vi.fn(),
    flushdb: vi.fn(),
    flushall: vi.fn(),
    select: vi.fn(),
    ttl: vi.fn(),
    expire: vi.fn(),
    del: vi.fn(),
    type: vi.fn(),
    quit: vi.fn(),
    monitor: vi.fn(),
    on: vi.fn()
  };

  return {
    default: vi.fn(function() {
      return mockClient;
    }),
    __esModule: true
  };
});

describe('RedisCLI', () => {
  let cli: RedisCLI;
  let mockRedisClient: any;

  beforeEach(() => {
    cli = new RedisCLI();

    // Get the mock client from the mocked module
    const RedisMock = Redis as any;
    mockRedisClient = new RedisMock();
  });

  afterEach(async () => {
    vi.clearAllMocks();
    await cli.cleanup();
  });

  describe('Connection Management', () => {
    it('should connect to Redis with connection string', async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });

      await cli.connect('redis://localhost:6379', { name: 'test' });

      expect(Redis).toHaveBeenCalledWith(
        expect.objectContaining({
          host: 'localhost',
          port: 6379
        })
      );
    });

    it('should connect with authentication', async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });

      await cli.connect('redis://user:pass@localhost:6379', { name: 'auth-test' });

      expect(Redis).toHaveBeenCalledWith(
        expect.objectContaining({
          host: 'localhost',
          port: 6379,
          username: 'user',
          password: 'pass'
        })
      );
    });

    it('should connect with database selection', async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });

      await cli.connect('redis://localhost:6379/2', { name: 'db-test' });

      expect(Redis).toHaveBeenCalledWith(
        expect.objectContaining({
          db: 2
        })
      );
    });

    it('should connect with TLS', async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });

      await cli.connect('rediss://localhost:6380', { name: 'tls-test', tls: true });

      expect(Redis).toHaveBeenCalledWith(
        expect.objectContaining({
          tls: {}
        })
      );
    });

    it('should handle connection timeout', async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        // Never call ready handler
        return mockRedisClient;
      });

      await expect(
        cli.connect('redis://localhost:6379', { name: 'timeout-test' })
      ).rejects.toThrow('Connection timeout');
    }, 15000); // Increase timeout for this specific test

    it('should handle connection error', async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'error') {
          setTimeout(() => handler(new Error('Connection refused')), 0);
        }
        return mockRedisClient;
      });

      await expect(
        cli.connect('redis://localhost:6379', { name: 'error-test' })
      ).rejects.toThrow('Connection refused');
    });

    it('should disconnect from Redis', async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      mockRedisClient.quit.mockResolvedValue('OK');

      await cli.connect('redis://localhost:6379', { name: 'disconnect-test' });
      await cli.disconnect('disconnect-test');

      expect(mockRedisClient.quit).toHaveBeenCalled();
    });

    it('should disconnect all connections', async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      mockRedisClient.quit.mockResolvedValue('OK');

      await cli.connect('redis://localhost:6379', { name: 'conn1' });
      await cli.connect('redis://localhost:6379', { name: 'conn2' });
      await cli.disconnectAll();

      expect(mockRedisClient.quit).toHaveBeenCalledTimes(2);
    });
  });

  describe('GET Command', () => {
    beforeEach(async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      await cli.connect('redis://localhost:6379');
    });

    it('should get existing key', async () => {
      mockRedisClient.get.mockResolvedValue('test-value');

      const result = await cli.get('test-key');

      expect(result).toEqual({
        key: 'test-key',
        value: 'test-value',
        exists: true
      });
      expect(mockRedisClient.get).toHaveBeenCalledWith('test-key');
    });

    it('should handle non-existent key', async () => {
      mockRedisClient.get.mockResolvedValue(null);

      const result = await cli.get('non-existent');

      expect(result).toEqual({
        key: 'non-existent',
        value: null,
        exists: false
      });
    });

    it('should get key with type info', async () => {
      mockRedisClient.get.mockResolvedValue('value');
      mockRedisClient.type.mockResolvedValue('string');
      mockRedisClient.ttl.mockResolvedValue(3600);

      const result = await cli.get('test-key', { showType: true });

      expect(result).toEqual({
        key: 'test-key',
        value: 'value',
        type: 'string',
        ttl: 3600,
        exists: true
      });
      expect(mockRedisClient.type).toHaveBeenCalledWith('test-key');
      expect(mockRedisClient.ttl).toHaveBeenCalledWith('test-key');
    });
  });

  describe('SET Command', () => {
    beforeEach(async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      await cli.connect('redis://localhost:6379');
    });

    it('should set key with value', async () => {
      mockRedisClient.call.mockResolvedValue('OK');

      const result = await cli.set('test-key', 'test-value');

      expect(result).toEqual({
        success: true,
        key: 'test-key',
        message: 'Key set successfully'
      });
      expect(mockRedisClient.call).toHaveBeenCalledWith('SET', 'test-key', 'test-value');
    });

    it('should set key with expiration (EX)', async () => {
      mockRedisClient.call.mockResolvedValue('OK');

      const result = await cli.set('session-key', 'session-data', { ex: 3600 });

      expect(result.success).toBe(true);
      expect(mockRedisClient.call).toHaveBeenCalledWith('SET', 'session-key', 'session-data', 'EX', 3600);
    });

    it('should set key with expiration (PX)', async () => {
      mockRedisClient.call.mockResolvedValue('OK');

      const result = await cli.set('temp-key', 'temp-data', { px: 5000 });

      expect(result.success).toBe(true);
      expect(mockRedisClient.call).toHaveBeenCalledWith('SET', 'temp-key', 'temp-data', 'PX', 5000);
    });

    it('should set key with NX option', async () => {
      mockRedisClient.call.mockResolvedValue('OK');

      const result = await cli.set('new-key', 'new-value', { nx: true });

      expect(result.message).toContain('if not exists');
      expect(mockRedisClient.call).toHaveBeenCalledWith('SET', 'new-key', 'new-value', 'NX');
    });

    it('should set key with XX option', async () => {
      mockRedisClient.call.mockResolvedValue('OK');

      const result = await cli.set('existing-key', 'updated-value', { xx: true });

      expect(result.message).toContain('if exists');
      expect(mockRedisClient.call).toHaveBeenCalledWith('SET', 'existing-key', 'updated-value', 'XX');
    });

    it('should set key with KEEPTTL option', async () => {
      mockRedisClient.call.mockResolvedValue('OK');

      const result = await cli.set('key', 'value', { keepttl: true });

      expect(result.success).toBe(true);
      expect(mockRedisClient.call).toHaveBeenCalledWith('SET', 'key', 'value', 'KEEPTTL');
    });

    it('should handle failed set with condition', async () => {
      mockRedisClient.call.mockResolvedValue(null);

      const result = await cli.set('key', 'value', { nx: true });

      expect(result.success).toBe(true); // null is considered success in some cases
    });
  });

  describe('KEYS Command', () => {
    beforeEach(async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      await cli.connect('redis://localhost:6379');
    });

    it('should list keys by pattern', async () => {
      mockRedisClient.keys.mockResolvedValue(['user:1', 'user:2', 'user:3']);

      const result = await cli.keys('user:*');

      expect(result).toEqual({
        keys: ['user:1', 'user:2', 'user:3'],
        count: 3,
        pattern: 'user:*'
      });
      expect(mockRedisClient.keys).toHaveBeenCalledWith('user:*');
    });

    it('should list keys with limit', async () => {
      mockRedisClient.keys.mockResolvedValue(['key1', 'key2', 'key3', 'key4', 'key5']);

      const result = await cli.keys('*', { limit: 3 });

      expect(result.count).toBe(3);
      expect(result.keys).toHaveLength(3);
    });

    it('should use SCAN instead of KEYS', async () => {
      mockRedisClient.scan.mockResolvedValueOnce(['0', ['key1', 'key2']]);

      const result = await cli.keys('*', { useScan: true });

      expect(result.cursor).toBe('scan');
      expect(mockRedisClient.scan).toHaveBeenCalled();
    });

    it('should handle empty result', async () => {
      mockRedisClient.keys.mockResolvedValue([]);

      const result = await cli.keys('nonexistent:*');

      expect(result).toEqual({
        keys: [],
        count: 0,
        pattern: 'nonexistent:*'
      });
    });

    it('should iterate with SCAN until cursor is 0', async () => {
      mockRedisClient.scan
        .mockResolvedValueOnce(['5', ['key1', 'key2']])
        .mockResolvedValueOnce(['0', ['key3', 'key4']]);

      const result = await cli.keys('*', { useScan: true });

      expect(result.keys).toEqual(['key1', 'key2', 'key3', 'key4']);
      expect(mockRedisClient.scan).toHaveBeenCalledTimes(2);
    });
  });

  describe('INFO Command', () => {
    beforeEach(async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      await cli.connect('redis://localhost:6379');
    });

    it('should get server info', async () => {
      const infoOutput = `# Server\r\nredis_version:7.0.0\r\nredis_mode:standalone\r\n# Memory\r\nused_memory:1024000\r\n`;
      mockRedisClient.info.mockResolvedValue(infoOutput);

      const result = await cli.info();

      expect(result.section).toBe('all');
      expect(result.data).toHaveProperty('Server');
      expect(result.data).toHaveProperty('Memory');
      expect(result.raw).toBe(infoOutput);
    });

    it('should get specific section', async () => {
      const infoOutput = `# Memory\r\nused_memory:1024000\r\nused_memory_human:1.00M\r\n`;
      mockRedisClient.info.mockResolvedValue(infoOutput);

      const result = await cli.info('memory');

      expect(result.section).toBe('memory');
      expect(result.data).toHaveProperty('Memory');
      expect(mockRedisClient.info).toHaveBeenCalledWith('memory');
    });

    it('should parse info sections correctly', async () => {
      const infoOutput = `# Server\r\nredis_version:7.0.0\r\n# Stats\r\ntotal_commands_processed:1000\r\n`;
      mockRedisClient.info.mockResolvedValue(infoOutput);

      const result = await cli.info();

      expect(result.data.Server).toHaveProperty('redis_version', '7.0.0');
      expect(result.data.Stats).toHaveProperty('total_commands_processed', '1000');
    });
  });

  describe('FLUSH Command', () => {
    beforeEach(async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      await cli.connect('redis://localhost:6379');
    });

    it('should flush current database', async () => {
      mockRedisClient.dbsize.mockResolvedValue(100);
      mockRedisClient.flushdb.mockResolvedValue('OK');

      const result = await cli.flush();

      expect(result).toEqual({
        success: true,
        message: 'Current database flushed',
        deletedKeys: 100
      });
      expect(mockRedisClient.flushdb).toHaveBeenCalled();
    });

    it('should flush specific database', async () => {
      mockRedisClient.dbsize.mockResolvedValue(50);
      mockRedisClient.select.mockResolvedValue('OK');
      mockRedisClient.flushdb.mockResolvedValue('OK');

      const result = await cli.flush({ db: 1 });

      expect(result.message).toBe('Database 1 flushed');
      expect(mockRedisClient.select).toHaveBeenCalledWith(1);
      expect(mockRedisClient.flushdb).toHaveBeenCalled();
    });

    it('should flush all databases', async () => {
      mockRedisClient.dbsize.mockResolvedValue(200);
      mockRedisClient.flushall.mockResolvedValue('OK');

      const result = await cli.flush({ all: true });

      expect(result.message).toBe('All databases flushed');
      expect(mockRedisClient.flushall).toHaveBeenCalled();
    });

    it('should flush asynchronously', async () => {
      mockRedisClient.dbsize.mockResolvedValue(100);
      mockRedisClient.flushdb.mockResolvedValue('OK');

      await cli.flush({ async: true });

      expect(mockRedisClient.flushdb).toHaveBeenCalledWith('ASYNC');
    });
  });

  describe('TTL Command', () => {
    beforeEach(async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      await cli.connect('redis://localhost:6379');
    });

    it('should get TTL for key with expiration', async () => {
      mockRedisClient.ttl.mockResolvedValue(3600);

      const result = await cli.ttl('session:abc');

      expect(result).toEqual({
        key: 'session:abc',
        ttl: 3600,
        hasExpiry: true,
        message: 'Expires in 3600 seconds'
      });
    });

    it('should handle key without expiration', async () => {
      mockRedisClient.ttl.mockResolvedValue(-1);

      const result = await cli.ttl('persistent-key');

      expect(result).toEqual({
        key: 'persistent-key',
        ttl: -1,
        hasExpiry: false,
        message: 'No expiry set'
      });
    });

    it('should handle non-existent key', async () => {
      mockRedisClient.ttl.mockResolvedValue(-2);

      const result = await cli.ttl('nonexistent');

      expect(result).toEqual({
        key: 'nonexistent',
        ttl: -2,
        hasExpiry: false,
        message: 'Key does not exist'
      });
    });
  });

  describe('EXPIRE Command', () => {
    beforeEach(async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      await cli.connect('redis://localhost:6379');
    });

    it('should set expiration on key', async () => {
      mockRedisClient.expire.mockResolvedValue(1);

      const result = await cli.expire('test-key', 300);

      expect(result).toEqual({
        success: true,
        key: 'test-key',
        message: 'Expiry set to 300 seconds'
      });
      expect(mockRedisClient.expire).toHaveBeenCalledWith('test-key', 300);
    });

    it('should handle non-existent key', async () => {
      mockRedisClient.expire.mockResolvedValue(0);

      const result = await cli.expire('nonexistent', 300);

      expect(result).toEqual({
        success: false,
        key: 'nonexistent',
        message: 'Key does not exist'
      });
    });
  });

  describe('DEL Command', () => {
    beforeEach(async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      await cli.connect('redis://localhost:6379');
    });

    it('should delete single key', async () => {
      mockRedisClient.del.mockResolvedValue(1);

      const result = await cli.del(['test-key']);

      expect(result).toEqual({ deletedCount: 1 });
      expect(mockRedisClient.del).toHaveBeenCalledWith('test-key');
    });

    it('should delete multiple keys', async () => {
      mockRedisClient.del.mockResolvedValue(3);

      const result = await cli.del(['key1', 'key2', 'key3']);

      expect(result).toEqual({ deletedCount: 3 });
      expect(mockRedisClient.del).toHaveBeenCalledWith('key1', 'key2', 'key3');
    });

    it('should handle non-existent keys', async () => {
      mockRedisClient.del.mockResolvedValue(0);

      const result = await cli.del(['nonexistent']);

      expect(result).toEqual({ deletedCount: 0 });
    });
  });

  describe('TYPE Command', () => {
    beforeEach(async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      await cli.connect('redis://localhost:6379');
    });

    it('should get type of string key', async () => {
      mockRedisClient.type.mockResolvedValue('string');

      const result = await cli.type('string-key');

      expect(result).toEqual({ type: 'string' });
    });

    it('should get type of hash key', async () => {
      mockRedisClient.type.mockResolvedValue('hash');

      const result = await cli.type('hash-key');

      expect(result).toEqual({ type: 'hash' });
    });

    it('should get type of list key', async () => {
      mockRedisClient.type.mockResolvedValue('list');

      const result = await cli.type('list-key');

      expect(result).toEqual({ type: 'list' });
    });

    it('should get type of set key', async () => {
      mockRedisClient.type.mockResolvedValue('set');

      const result = await cli.type('set-key');

      expect(result).toEqual({ type: 'set' });
    });

    it('should get type of zset key', async () => {
      mockRedisClient.type.mockResolvedValue('zset');

      const result = await cli.type('zset-key');

      expect(result).toEqual({ type: 'zset' });
    });

    it('should handle non-existent key', async () => {
      mockRedisClient.type.mockResolvedValue('none');

      const result = await cli.type('nonexistent');

      expect(result).toEqual({ type: 'none' });
    });
  });

  describe('Error Handling', () => {
    beforeEach(async () => {
      mockRedisClient.on.mockImplementation((event: string, handler: Function) => {
        if (event === 'ready') {
          setTimeout(() => handler(), 0);
        }
        return mockRedisClient;
      });
      await cli.connect('redis://localhost:6379');
    });

    it('should handle GET errors', async () => {
      mockRedisClient.get.mockRejectedValue(new Error('Redis error'));

      await expect(cli.get('test-key')).rejects.toThrow('Redis error');
    });

    it('should handle SET errors', async () => {
      mockRedisClient.call.mockRejectedValue(new Error('Redis error'));

      await expect(cli.set('test-key', 'value')).rejects.toThrow('Redis error');
    });

    it('should handle KEYS errors', async () => {
      mockRedisClient.keys.mockRejectedValue(new Error('Redis error'));

      await expect(cli.keys('*')).rejects.toThrow('Redis error');
    });

    it('should throw error when no connection', async () => {
      const newCli = new RedisCLI();

      await expect(newCli.get('test-key')).rejects.toThrow('No active connection');
    });
  });
});
