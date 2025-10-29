/**
 * Redis Integration Tests
 *
 * Comprehensive test suite for Redis client operations using Docker test environment.
 * Tests all major Redis features including basic operations, advanced data structures,
 * pub/sub, transactions, pipelining, and more.
 *
 * Prerequisites:
 * - Redis server running on redis://localhost:6379
 * - Docker container or local Redis instance
 *
 * @requires ioredis
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import Redis from 'ioredis';
import { testDatabaseConfig } from '../../config/databases.test';

// Test configuration from centralized config
const REDIS_CONFIG = testDatabaseConfig.redis;

// Test timeout for operations
const OPERATION_TIMEOUT = 5000;

describe('Redis Integration Tests', () => {
  let redis: Redis;
  let pubClient: Redis;
  let subClient: Redis;

  // Setup: Create Redis connections
  beforeAll(async () => {
    redis = new Redis(REDIS_CONFIG);
    await redis.connect();

    // Verify connection
    const ping = await redis.ping();
    expect(ping).toBe('PONG');

    console.log('✅ Redis connection established');
  }, 10000);

  // Cleanup: Close connections
  afterAll(async () => {
    try {
      if (redis && redis.status !== 'end') {
        await redis.quit();
      }
    } catch (err) {
      // Connection already closed
    }

    try {
      if (pubClient && pubClient.status !== 'end') {
        await pubClient.quit();
      }
    } catch (err) {
      // Connection already closed
    }

    try {
      if (subClient && subClient.status !== 'end') {
        await subClient.quit();
      }
    } catch (err) {
      // Connection already closed
    }

    console.log('✅ Redis connections closed');
  });

  // Clear test data before each test
  beforeEach(async () => {
    await redis.flushdb();
  });

  describe('1. Connection Management', () => {
    it('should establish connection successfully', async () => {
      const result = await redis.ping();
      expect(result).toBe('PONG');
    });

    it('should select different database', async () => {
      await redis.select(1);
      await redis.set('test_db', 'database_1');

      await redis.select(15);
      const value = await redis.get('test_db');
      expect(value).toBeNull();
    });

    it('should handle connection errors gracefully', async () => {
      const badClient = new Redis({
        host: 'localhost',
        port: 9999, // Invalid port
        maxRetriesPerRequest: 1,
        retryStrategy: () => null, // Don't retry
        lazyConnect: true,
      });

      // Add error event listener to prevent unhandled error warnings
      const errorHandler = (err: Error) => {
        // Expected error - suppress it
      };
      badClient.on('error', errorHandler);

      await expect(badClient.connect()).rejects.toThrow();

      // Clean up
      badClient.off('error', errorHandler);
      badClient.disconnect();
    });

    it('should get server info', async () => {
      const info = await redis.info();
      expect(info).toContain('redis_version');
      expect(info).toContain('connected_clients');
    });
  });

  describe('2. String Operations', () => {
    it('should SET and GET string values', async () => {
      await redis.set('key1', 'value1');
      const value = await redis.get('key1');
      expect(value).toBe('value1');
    });

    it('should SET with expiration (EX)', async () => {
      await redis.set('expiring_key', 'temp_value', 'EX', 2);
      const value1 = await redis.get('expiring_key');
      expect(value1).toBe('temp_value');

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 2100));
      const value2 = await redis.get('expiring_key');
      expect(value2).toBeNull();
    });

    it('should SETNX (set if not exists)', async () => {
      const result1 = await redis.setnx('unique_key', 'first_value');
      expect(result1).toBe(1);

      const result2 = await redis.setnx('unique_key', 'second_value');
      expect(result2).toBe(0);

      const value = await redis.get('unique_key');
      expect(value).toBe('first_value');
    });

    it('should INCR and DECR numeric values', async () => {
      await redis.set('counter', '10');

      const incr1 = await redis.incr('counter');
      expect(incr1).toBe(11);

      const incrby = await redis.incrby('counter', 5);
      expect(incrby).toBe(16);

      const decr1 = await redis.decr('counter');
      expect(decr1).toBe(15);

      const decrby = await redis.decrby('counter', 3);
      expect(decrby).toBe(12);
    });

    it('should APPEND to string', async () => {
      await redis.set('message', 'Hello');
      const length = await redis.append('message', ' World');
      expect(length).toBe(11);

      const value = await redis.get('message');
      expect(value).toBe('Hello World');
    });

    it('should get string length', async () => {
      await redis.set('text', 'Hello Redis');
      const length = await redis.strlen('text');
      expect(length).toBe(11);
    });

    it('should GETRANGE (substring)', async () => {
      await redis.set('greeting', 'Hello Redis World');
      const substring = await redis.getrange('greeting', 6, 10);
      expect(substring).toBe('Redis');
    });

    it('should MSET and MGET (multiple keys)', async () => {
      await redis.mset('key1', 'value1', 'key2', 'value2', 'key3', 'value3');

      const values = await redis.mget('key1', 'key2', 'key3', 'nonexistent');
      expect(values).toEqual(['value1', 'value2', 'value3', null]);
    });
  });

  describe('3. Hash Operations', () => {
    it('should HSET and HGET hash fields', async () => {
      await redis.hset('user:1000', 'name', 'John Doe');
      await redis.hset('user:1000', 'email', 'john@example.com');

      const name = await redis.hget('user:1000', 'name');
      expect(name).toBe('John Doe');
    });

    it('should HMSET (set multiple fields)', async () => {
      await redis.hmset('user:2000', {
        name: 'Jane Smith',
        email: 'jane@example.com',
        age: '30',
      });

      const user = await redis.hgetall('user:2000');
      expect(user).toEqual({
        name: 'Jane Smith',
        email: 'jane@example.com',
        age: '30',
      });
    });

    it('should HGETALL retrieve all fields', async () => {
      await redis.hset('product:100', 'name', 'Laptop');
      await redis.hset('product:100', 'price', '999.99');
      await redis.hset('product:100', 'stock', '50');

      const product = await redis.hgetall('product:100');
      expect(product.name).toBe('Laptop');
      expect(product.price).toBe('999.99');
      expect(product.stock).toBe('50');
    });

    it('should HINCRBY increment hash field', async () => {
      await redis.hset('stats:game', 'score', '100');

      const newScore = await redis.hincrby('stats:game', 'score', 50);
      expect(newScore).toBe(150);
    });

    it('should HINCRBYFLOAT increment by float', async () => {
      await redis.hset('metrics:cpu', 'usage', '45.5');

      const newUsage = await redis.hincrbyfloat('metrics:cpu', 'usage', 2.3);
      expect(newUsage).toBeCloseTo(47.8, 1);
    });

    it('should HEXISTS check field existence', async () => {
      await redis.hset('user:3000', 'name', 'Bob');

      const exists1 = await redis.hexists('user:3000', 'name');
      expect(exists1).toBe(1);

      const exists2 = await redis.hexists('user:3000', 'email');
      expect(exists2).toBe(0);
    });

    it('should HDEL delete hash fields', async () => {
      await redis.hmset('user:4000', { name: 'Alice', email: 'alice@test.com', age: '25' });

      const deleted = await redis.hdel('user:4000', 'email', 'age');
      expect(deleted).toBe(2);

      const remaining = await redis.hgetall('user:4000');
      expect(remaining).toEqual({ name: 'Alice' });
    });

    it('should HKEYS get all field names', async () => {
      await redis.hmset('config', { host: 'localhost', port: '6379', timeout: '5000' });

      const keys = await redis.hkeys('config');
      expect(keys.sort()).toEqual(['host', 'port', 'timeout'].sort());
    });

    it('should HVALS get all values', async () => {
      await redis.hmset('settings', { theme: 'dark', language: 'en', notifications: 'on' });

      const values = await redis.hvals('settings');
      expect(values.sort()).toEqual(['dark', 'en', 'on'].sort());
    });
  });

  describe('4. List Operations', () => {
    it('should LPUSH and RPUSH add elements', async () => {
      await redis.lpush('queue', 'first');
      await redis.rpush('queue', 'last');

      const list = await redis.lrange('queue', 0, -1);
      expect(list).toEqual(['first', 'last']);
    });

    it('should LPOP and RPOP remove elements', async () => {
      await redis.rpush('stack', 'a', 'b', 'c');

      const right = await redis.rpop('stack');
      expect(right).toBe('c');

      const left = await redis.lpop('stack');
      expect(left).toBe('a');

      const remaining = await redis.lrange('stack', 0, -1);
      expect(remaining).toEqual(['b']);
    });

    it('should LRANGE get list slice', async () => {
      await redis.rpush('numbers', '1', '2', '3', '4', '5');

      const all = await redis.lrange('numbers', 0, -1);
      expect(all).toEqual(['1', '2', '3', '4', '5']);

      const slice = await redis.lrange('numbers', 1, 3);
      expect(slice).toEqual(['2', '3', '4']);
    });

    it('should LLEN get list length', async () => {
      await redis.rpush('items', 'a', 'b', 'c');

      const length = await redis.llen('items');
      expect(length).toBe(3);
    });

    it('should LINDEX get element by index', async () => {
      await redis.rpush('colors', 'red', 'green', 'blue');

      const color = await redis.lindex('colors', 1);
      expect(color).toBe('green');
    });

    it('should LSET set element by index', async () => {
      await redis.rpush('fruits', 'apple', 'banana', 'cherry');

      await redis.lset('fruits', 1, 'orange');

      const fruits = await redis.lrange('fruits', 0, -1);
      expect(fruits).toEqual(['apple', 'orange', 'cherry']);
    });

    it('should LTRIM trim list', async () => {
      await redis.rpush('log', 'entry1', 'entry2', 'entry3', 'entry4', 'entry5');

      await redis.ltrim('log', 0, 2);

      const trimmed = await redis.lrange('log', 0, -1);
      expect(trimmed).toEqual(['entry1', 'entry2', 'entry3']);
    });

    it('should LREM remove elements', async () => {
      await redis.rpush('tasks', 'task1', 'remove', 'task2', 'remove', 'task3');

      const removed = await redis.lrem('tasks', 0, 'remove');
      expect(removed).toBe(2);

      const remaining = await redis.lrange('tasks', 0, -1);
      expect(remaining).toEqual(['task1', 'task2', 'task3']);
    });
  });

  describe('5. Set Operations', () => {
    it('should SADD add members to set', async () => {
      const added = await redis.sadd('tags', 'javascript', 'typescript', 'node');
      expect(added).toBe(3);

      const duplicate = await redis.sadd('tags', 'javascript');
      expect(duplicate).toBe(0);
    });

    it('should SMEMBERS get all members', async () => {
      await redis.sadd('skills', 'coding', 'testing', 'design');

      const members = await redis.smembers('skills');
      expect(members.sort()).toEqual(['coding', 'design', 'testing'].sort());
    });

    it('should SISMEMBER check membership', async () => {
      await redis.sadd('roles', 'admin', 'user', 'guest');

      const isAdmin = await redis.sismember('roles', 'admin');
      expect(isAdmin).toBe(1);

      const isSuperuser = await redis.sismember('roles', 'superuser');
      expect(isSuperuser).toBe(0);
    });

    it('should SCARD get set cardinality', async () => {
      await redis.sadd('numbers', '1', '2', '3', '4', '5');

      const count = await redis.scard('numbers');
      expect(count).toBe(5);
    });

    it('should SREM remove members', async () => {
      await redis.sadd('items', 'a', 'b', 'c', 'd');

      const removed = await redis.srem('items', 'b', 'd');
      expect(removed).toBe(2);

      const remaining = await redis.smembers('items');
      expect(remaining.sort()).toEqual(['a', 'c'].sort());
    });

    it('should SINTER get intersection', async () => {
      await redis.sadd('set1', 'a', 'b', 'c');
      await redis.sadd('set2', 'b', 'c', 'd');

      const intersection = await redis.sinter('set1', 'set2');
      expect(intersection.sort()).toEqual(['b', 'c'].sort());
    });

    it('should SUNION get union', async () => {
      await redis.sadd('fruits1', 'apple', 'banana');
      await redis.sadd('fruits2', 'banana', 'cherry');

      const union = await redis.sunion('fruits1', 'fruits2');
      expect(union.sort()).toEqual(['apple', 'banana', 'cherry'].sort());
    });

    it('should SDIFF get difference', async () => {
      await redis.sadd('all_users', 'user1', 'user2', 'user3', 'user4');
      await redis.sadd('active_users', 'user1', 'user3');

      const inactive = await redis.sdiff('all_users', 'active_users');
      expect(inactive.sort()).toEqual(['user2', 'user4'].sort());
    });

    it('should SPOP remove random member', async () => {
      await redis.sadd('lottery', '1', '2', '3', '4', '5');

      const winner = await redis.spop('lottery');
      expect(winner).toBeTruthy();

      const remaining = await redis.scard('lottery');
      expect(remaining).toBe(4);
    });
  });

  describe('6. Sorted Set Operations', () => {
    it('should ZADD add members with scores', async () => {
      await redis.zadd('leaderboard', 100, 'player1', 200, 'player2', 150, 'player3');

      const count = await redis.zcard('leaderboard');
      expect(count).toBe(3);
    });

    it('should ZRANGE get members by rank', async () => {
      await redis.zadd('scores', 10, 'alice', 20, 'bob', 15, 'charlie');

      const ascending = await redis.zrange('scores', 0, -1);
      expect(ascending).toEqual(['alice', 'charlie', 'bob']);
    });

    it('should ZREVRANGE get members in reverse order', async () => {
      await redis.zadd('ranking', 100, 'a', 200, 'b', 150, 'c');

      const descending = await redis.zrevrange('ranking', 0, -1);
      expect(descending).toEqual(['b', 'c', 'a']);
    });

    it('should ZRANK get rank of member', async () => {
      await redis.zadd('competition', 500, 'team1', 300, 'team2', 400, 'team3');

      const rank = await redis.zrank('competition', 'team3');
      expect(rank).toBe(1); // 0-based index
    });

    it('should ZSCORE get score of member', async () => {
      await redis.zadd('grades', 85, 'student1', 92, 'student2');

      const score = await redis.zscore('grades', 'student2');
      expect(parseFloat(score!)).toBe(92);
    });

    it('should ZINCRBY increment score', async () => {
      await redis.zadd('points', 100, 'user1');

      const newScore = await redis.zincrby('points', 50, 'user1');
      expect(parseFloat(newScore)).toBe(150);
    });

    it('should ZRANGEBYSCORE get members by score range', async () => {
      await redis.zadd('prices', 10.5, 'item1', 25.0, 'item2', 15.75, 'item3', 30.0, 'item4');

      const affordable = await redis.zrangebyscore('prices', 10, 20);
      expect(affordable.sort()).toEqual(['item1', 'item3'].sort());
    });

    it('should ZREM remove members', async () => {
      await redis.zadd('tasks', 1, 'task1', 2, 'task2', 3, 'task3');

      const removed = await redis.zrem('tasks', 'task2');
      expect(removed).toBe(1);

      const remaining = await redis.zrange('tasks', 0, -1);
      expect(remaining).toEqual(['task1', 'task3']);
    });

    it('should ZPOPMAX remove highest score', async () => {
      await redis.zadd('queue', 1, 'low', 5, 'high', 3, 'medium');

      const highest = await redis.zpopmax('queue');
      expect(highest).toEqual(['high', '5']);
    });

    it('should ZPOPMIN remove lowest score', async () => {
      await redis.zadd('priority', 10, 'urgent', 1, 'low', 5, 'normal');

      const lowest = await redis.zpopmin('priority');
      expect(lowest).toEqual(['low', '1']);
    });
  });

  describe('7. Key Expiration', () => {
    it('should EXPIRE set key expiration', async () => {
      await redis.set('temp_key', 'temporary_value');
      await redis.expire('temp_key', 1);

      const ttl = await redis.ttl('temp_key');
      expect(ttl).toBeGreaterThan(0);
      expect(ttl).toBeLessThanOrEqual(1);
    });

    it('should TTL get remaining time', async () => {
      await redis.set('expiring', 'value');
      await redis.expire('expiring', 10);

      const ttl = await redis.ttl('expiring');
      expect(ttl).toBeGreaterThan(0);
      expect(ttl).toBeLessThanOrEqual(10);
    });

    it('should handle expired keys', async () => {
      await redis.set('short_lived', 'value', 'EX', 1);

      const before = await redis.get('short_lived');
      expect(before).toBe('value');

      await new Promise(resolve => setTimeout(resolve, 1100));

      const after = await redis.get('short_lived');
      expect(after).toBeNull();
    });

    it('should PERSIST remove expiration', async () => {
      await redis.set('persistent', 'value');
      await redis.expire('persistent', 10);

      const removed = await redis.persist('persistent');
      expect(removed).toBe(1);

      const ttl = await redis.ttl('persistent');
      expect(ttl).toBe(-1); // -1 means no expiration
    });

    it('should PEXPIRE set millisecond expiration', async () => {
      await redis.set('ms_key', 'value');
      await redis.pexpire('ms_key', 500);

      const pttl = await redis.pttl('ms_key');
      expect(pttl).toBeGreaterThan(0);
      expect(pttl).toBeLessThanOrEqual(500);
    });

    it('should EXPIREAT set absolute expiration time', async () => {
      await redis.set('scheduled', 'value');

      const futureTimestamp = Math.floor(Date.now() / 1000) + 5;
      await redis.expireat('scheduled', futureTimestamp);

      const ttl = await redis.ttl('scheduled');
      expect(ttl).toBeGreaterThan(0);
      expect(ttl).toBeLessThanOrEqual(5);
    });
  });

  describe('8. Pub/Sub Messaging', () => {
    beforeEach(async () => {
      // Create dedicated pub/sub clients
      pubClient = new Redis(REDIS_CONFIG);
      subClient = new Redis(REDIS_CONFIG);
      await pubClient.connect();
      await subClient.connect();
    });

    afterEach(async () => {
      if (subClient) {
        await subClient.quit();
      }
      if (pubClient) {
        await pubClient.quit();
      }
    });

    it('should publish and subscribe to messages', async () => {
      const messages: string[] = [];

      await subClient.subscribe('news');

      subClient.on('message', (channel, message) => {
        if (channel === 'news') {
          messages.push(message);
        }
      });

      // Wait for subscription to be ready
      await new Promise(resolve => setTimeout(resolve, 100));

      await pubClient.publish('news', 'Breaking news!');
      await pubClient.publish('news', 'Update available');

      // Wait for messages to be received
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(messages).toContain('Breaking news!');
      expect(messages).toContain('Update available');
    });

    it('should unsubscribe from channel', async () => {
      const messages: string[] = [];

      await subClient.subscribe('events');

      subClient.on('message', (channel, message) => {
        messages.push(message);
      });

      await new Promise(resolve => setTimeout(resolve, 100));
      await pubClient.publish('events', 'event1');

      await subClient.unsubscribe('events');
      await new Promise(resolve => setTimeout(resolve, 100));

      await pubClient.publish('events', 'event2');
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(messages).toContain('event1');
      expect(messages).not.toContain('event2');
    });

    it('should pattern subscribe', async () => {
      const messages: Array<{ pattern: string; channel: string; message: string }> = [];

      await subClient.psubscribe('user:*');

      subClient.on('pmessage', (pattern, channel, message) => {
        messages.push({ pattern, channel, message });
      });

      await new Promise(resolve => setTimeout(resolve, 100));

      await pubClient.publish('user:login', 'User logged in');
      await pubClient.publish('user:logout', 'User logged out');
      await pubClient.publish('system:alert', 'System message');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(messages).toHaveLength(2);
      expect(messages[0].message).toBe('User logged in');
      expect(messages[1].message).toBe('User logged out');
    });
  });

  describe('9. Transactions (MULTI/EXEC)', () => {
    it('should execute transaction successfully', async () => {
      const pipeline = redis.multi();

      pipeline.set('key1', 'value1');
      pipeline.set('key2', 'value2');
      pipeline.incr('counter');
      pipeline.get('key1');

      const results = await pipeline.exec();

      expect(results).toHaveLength(4);
      expect(results![3][1]).toBe('value1'); // Last command result
    });

    it('should DISCARD transaction', async () => {
      await redis.set('balance', '100');

      const pipeline = redis.multi();
      pipeline.decrby('balance', 50);
      pipeline.set('status', 'withdrawn');

      // Discard the transaction
      await pipeline.discard();

      const balance = await redis.get('balance');
      expect(balance).toBe('100'); // Unchanged
    });

    it('should handle transaction errors', async () => {
      const pipeline = redis.multi();

      pipeline.set('valid_key', 'value');
      pipeline.lpush('valid_key', 'item'); // This will fail - wrong type
      pipeline.set('another_key', 'value2');

      const results = await pipeline.exec();

      expect(results).toBeTruthy();
      expect(results![0][0]).toBeNull(); // First command succeeded
      expect(results![1][0]).toBeTruthy(); // Second command failed
    });

    it('should WATCH for optimistic locking', async () => {
      await redis.set('watched_key', '100');

      // Start watching
      await redis.watch('watched_key');

      // Simulate concurrent modification
      const otherClient = new Redis(REDIS_CONFIG);
      await otherClient.connect();
      await otherClient.set('watched_key', '200');
      await otherClient.quit();

      // Try to execute transaction
      const pipeline = redis.multi();
      pipeline.set('watched_key', '300');

      const results = await pipeline.exec();

      // Transaction should fail because key was modified
      expect(results).toBeNull();

      const value = await redis.get('watched_key');
      expect(value).toBe('200'); // Should have the concurrent value
    });
  });

  describe('10. Pipelining', () => {
    it('should execute pipelined commands efficiently', async () => {
      const pipeline = redis.pipeline();

      for (let i = 0; i < 100; i++) {
        pipeline.set(`key:${i}`, `value:${i}`);
      }

      const results = await pipeline.exec();

      expect(results).toHaveLength(100);
      results!.forEach(([err, result]) => {
        expect(err).toBeNull();
        expect(result).toBe('OK');
      });
    });

    it('should batch GET operations', async () => {
      // Setup test data
      await redis.mset('a', '1', 'b', '2', 'c', '3', 'd', '4', 'e', '5');

      const pipeline = redis.pipeline();
      ['a', 'b', 'c', 'd', 'e'].forEach(key => {
        pipeline.get(key);
      });

      const results = await pipeline.exec();

      expect(results).toHaveLength(5);
      expect(results!.map(r => r[1])).toEqual(['1', '2', '3', '4', '5']);
    });

    it('should handle pipeline with mixed commands', async () => {
      const pipeline = redis.pipeline();

      pipeline.set('str', 'hello');
      pipeline.hset('hash', 'field', 'value');
      pipeline.lpush('list', 'item');
      pipeline.sadd('set', 'member');
      pipeline.zadd('zset', 1, 'element');

      const results = await pipeline.exec();

      expect(results).toHaveLength(5);
      results!.forEach(([err]) => {
        expect(err).toBeNull();
      });
    });
  });

  describe('11. Lua Scripting', () => {
    it('should EVAL execute Lua script', async () => {
      const script = `
        local key = KEYS[1]
        local value = ARGV[1]
        redis.call('SET', key, value)
        return redis.call('GET', key)
      `;

      const result = await redis.eval(script, 1, 'mykey', 'myvalue');
      expect(result).toBe('myvalue');
    });

    it('should execute atomic increment with limit', async () => {
      await redis.set('limited_counter', '5');

      const script = `
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local current = tonumber(redis.call('GET', key))

        if current < limit then
          return redis.call('INCR', key)
        else
          return nil
        end
      `;

      const result1 = await redis.eval(script, 1, 'limited_counter', '10');
      expect(result1).toBe(6);

      await redis.set('limited_counter', '10');
      const result2 = await redis.eval(script, 1, 'limited_counter', '10');
      expect(result2).toBeNull();
    });

    it('should EVALSHA execute cached script', async () => {
      const script = 'return ARGV[1]';

      // Load script and get SHA
      const sha = await redis.script('LOAD', script);
      expect(sha).toBeTruthy();
      expect(typeof sha).toBe('string');

      // Execute using SHA (type assertion for TypeScript)
      const result = await redis.evalsha(sha as string, 0, 'test_value');
      expect(result).toBe('test_value');
    });

    it('should implement rate limiter with Lua', async () => {
      const rateLimitScript = `
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])

        local current = redis.call('INCR', key)

        if current == 1 then
          redis.call('EXPIRE', key, window)
        end

        if current > limit then
          return 0
        else
          return 1
        end
      `;

      const allow1 = await redis.eval(rateLimitScript, 1, 'rate:user1', '3', '60');
      expect(allow1).toBe(1);

      await redis.eval(rateLimitScript, 1, 'rate:user1', '3', '60');
      await redis.eval(rateLimitScript, 1, 'rate:user1', '3', '60');

      const allow4 = await redis.eval(rateLimitScript, 1, 'rate:user1', '3', '60');
      expect(allow4).toBe(0); // Exceeded limit
    });
  });

  describe('12. Persistence Operations', () => {
    it('should SAVE create snapshot', async () => {
      await redis.set('important_data', 'must_persist');

      // SAVE is blocking, use BGSAVE for production
      const result = await redis.bgsave();
      expect(result).toBe('Background saving started');
    });

    it('should get last save time', async () => {
      const timestamp = await redis.lastsave();
      expect(timestamp).toBeGreaterThan(0);
      expect(timestamp).toBeLessThanOrEqual(Math.floor(Date.now() / 1000));
    });

    it('should check persistence configuration', async () => {
      const config = await redis.config('GET', 'save');
      expect(config).toBeTruthy();
    });
  });

  describe('13. Redis Streams', () => {
    it('should XADD add entry to stream', async () => {
      const id = await redis.xadd('events', '*', 'action', 'login', 'user', 'john');
      expect(id).toBeTruthy();
      expect(id).toContain('-'); // Format: timestamp-sequence
    });

    it('should XREAD read from stream', async () => {
      await redis.xadd('notifications', '*', 'type', 'email', 'to', 'user@test.com');
      await redis.xadd('notifications', '*', 'type', 'sms', 'to', '+1234567890');

      const messages = await redis.xread('STREAMS', 'notifications', '0');

      expect(messages).toBeTruthy();
      expect(messages).toHaveLength(1);
      expect(messages![0][1]).toHaveLength(2);
    });

    it('should XLEN get stream length', async () => {
      await redis.xadd('log', '*', 'level', 'info', 'message', 'test1');
      await redis.xadd('log', '*', 'level', 'warn', 'message', 'test2');
      await redis.xadd('log', '*', 'level', 'error', 'message', 'test3');

      const length = await redis.xlen('log');
      expect(length).toBe(3);
    });

    it('should XRANGE get entries in range', async () => {
      const id1 = await redis.xadd('timeline', '*', 'event', 'start');
      await new Promise(resolve => setTimeout(resolve, 10));
      const id2 = await redis.xadd('timeline', '*', 'event', 'middle');
      await new Promise(resolve => setTimeout(resolve, 10));
      const id3 = await redis.xadd('timeline', '*', 'event', 'end');

      const range = await redis.xrange('timeline', '-', '+');
      expect(range).toHaveLength(3);
    });

    it('should XTRIM limit stream size', async () => {
      for (let i = 0; i < 10; i++) {
        await redis.xadd('limited_stream', '*', 'value', `${i}`);
      }

      await redis.xtrim('limited_stream', 'MAXLEN', 5);

      const length = await redis.xlen('limited_stream');
      expect(length).toBeLessThanOrEqual(5);
    });

    it('should XGROUP create consumer group', async () => {
      await redis.xadd('tasks', '*', 'task', 'process_data');

      const result = await redis.xgroup('CREATE', 'tasks', 'workers', '0', 'MKSTREAM');
      expect(result).toBe('OK');
    });
  });

  describe('14. HyperLogLog Operations', () => {
    it('should PFADD add elements to HyperLogLog', async () => {
      const added1 = await redis.pfadd('unique_visitors', 'user1', 'user2', 'user3');
      expect(added1).toBe(1);

      const added2 = await redis.pfadd('unique_visitors', 'user2', 'user3'); // Duplicates
      expect(added2).toBe(0);
    });

    it('should PFCOUNT estimate cardinality', async () => {
      await redis.pfadd('daily_visitors', 'ip1', 'ip2', 'ip3', 'ip4', 'ip5');

      const count = await redis.pfcount('daily_visitors');
      expect(count).toBe(5);
    });

    it('should PFMERGE merge HyperLogLogs', async () => {
      await redis.pfadd('visitors:monday', 'user1', 'user2', 'user3');
      await redis.pfadd('visitors:tuesday', 'user2', 'user3', 'user4');

      await redis.pfmerge('visitors:week', 'visitors:monday', 'visitors:tuesday');

      const totalUnique = await redis.pfcount('visitors:week');
      expect(totalUnique).toBe(4); // user1, user2, user3, user4
    });

    it('should handle large cardinality estimation', async () => {
      const elements: string[] = [];
      for (let i = 0; i < 10000; i++) {
        elements.push(`user${i}`);
      }

      // Add in batches
      const batchSize = 1000;
      for (let i = 0; i < elements.length; i += batchSize) {
        const batch = elements.slice(i, i + batchSize);
        await redis.pfadd('large_set', ...batch);
      }

      const estimate = await redis.pfcount('large_set');

      // HyperLogLog has ~0.81% standard error
      const expectedCount = 10000;
      const errorMargin = expectedCount * 0.02; // 2% margin

      expect(estimate).toBeGreaterThan(expectedCount - errorMargin);
      expect(estimate).toBeLessThan(expectedCount + errorMargin);
    });
  });

  describe('15. Advanced Key Operations', () => {
    it('should KEYS find keys by pattern', async () => {
      await redis.mset(
        'user:1:name', 'Alice',
        'user:2:name', 'Bob',
        'user:1:email', 'alice@test.com',
        'product:1', 'Laptop'
      );

      const userKeys = await redis.keys('user:*:name');
      expect(userKeys.sort()).toEqual(['user:1:name', 'user:2:name'].sort());
    });

    it('should SCAN iterate keys safely', async () => {
      // Add test data
      for (let i = 0; i < 50; i++) {
        await redis.set(`scan_key:${i}`, `value${i}`);
      }

      const allKeys: string[] = [];
      let cursor = '0';

      do {
        const result = await redis.scan(cursor, 'MATCH', 'scan_key:*', 'COUNT', 10);
        cursor = result[0];
        allKeys.push(...result[1]);
      } while (cursor !== '0');

      expect(allKeys.length).toBe(50);
    });

    it('should DEL delete keys', async () => {
      await redis.mset('del1', 'v1', 'del2', 'v2', 'del3', 'v3');

      const deleted = await redis.del('del1', 'del2', 'del3');
      expect(deleted).toBe(3);

      const exists = await redis.exists('del1', 'del2', 'del3');
      expect(exists).toBe(0);
    });

    it('should EXISTS check key existence', async () => {
      await redis.set('existing', 'value');

      const exists = await redis.exists('existing', 'nonexistent');
      expect(exists).toBe(1);
    });

    it('should TYPE get key type', async () => {
      await redis.set('string_key', 'value');
      await redis.hset('hash_key', 'field', 'value');
      await redis.lpush('list_key', 'item');

      expect(await redis.type('string_key')).toBe('string');
      expect(await redis.type('hash_key')).toBe('hash');
      expect(await redis.type('list_key')).toBe('list');
    });

    it('should RENAME key', async () => {
      await redis.set('old_name', 'value');

      await redis.rename('old_name', 'new_name');

      const oldExists = await redis.exists('old_name');
      expect(oldExists).toBe(0);

      const value = await redis.get('new_name');
      expect(value).toBe('value');
    });

    it('should RENAMENX rename only if new key does not exist', async () => {
      await redis.set('key1', 'value1');
      await redis.set('key2', 'value2');

      const result = await redis.renamenx('key1', 'key2');
      expect(result).toBe(0); // Failed because key2 exists

      const result2 = await redis.renamenx('key1', 'key3');
      expect(result2).toBe(1); // Success
    });
  });

  describe('16. Performance and Benchmarking', () => {
    it('should handle bulk operations efficiently', async () => {
      const startTime = Date.now();

      const pipeline = redis.pipeline();
      for (let i = 0; i < 1000; i++) {
        pipeline.set(`perf:${i}`, `value${i}`);
      }
      await pipeline.exec();

      const duration = Date.now() - startTime;

      // Should complete 1000 operations in reasonable time
      expect(duration).toBeLessThan(1000); // Less than 1 second
    });

    it('should measure GET operation latency', async () => {
      await redis.set('latency_test', 'value');

      const iterations = 100;
      const startTime = Date.now();

      for (let i = 0; i < iterations; i++) {
        await redis.get('latency_test');
      }

      const duration = Date.now() - startTime;
      const avgLatency = duration / iterations;

      expect(avgLatency).toBeLessThan(10); // Average < 10ms per operation
    });
  });

  describe('17. Error Handling and Edge Cases', () => {
    it('should handle non-existent keys gracefully', async () => {
      const value = await redis.get('nonexistent_key');
      expect(value).toBeNull();
    });

    it('should handle type errors', async () => {
      await redis.set('string_key', 'value');

      await expect(redis.lpush('string_key', 'item')).rejects.toThrow();
    });

    it('should handle connection timeout', async () => {
      const timeoutClient = new Redis({
        ...REDIS_CONFIG,
        connectTimeout: 100,
        host: '10.255.255.1', // Non-routable IP
        lazyConnect: true,
      });

      // Add error event listener to prevent unhandled error warnings
      const errorHandler = (err: Error) => {
        // Expected error - suppress it
      };
      timeoutClient.on('error', errorHandler);

      await expect(timeoutClient.connect()).rejects.toThrow();

      // Clean up
      timeoutClient.off('error', errorHandler);
      timeoutClient.disconnect();
    });

    it('should handle large values', async () => {
      const largeValue = 'x'.repeat(1024 * 1024); // 1MB string

      await redis.set('large_value', largeValue);
      const retrieved = await redis.get('large_value');

      expect(retrieved).toBe(largeValue);
      expect(retrieved!.length).toBe(1024 * 1024);
    });
  });
});
