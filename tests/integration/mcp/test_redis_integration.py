"""Redis integration tests with real Docker container."""
import asyncio
import pytest
import time
from tests.integration.mcp.config import DOCKER_CONFIGS


class TestRedisConnection:
    """Test Redis connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_success(self, redis_mcp_client, redis_clean):
        """Test successful connection to Redis."""
        config = DOCKER_CONFIGS['redis']

        await redis_mcp_client.connect(
            host=config['host'],
            port=config['port'],
            password=config['password']
        )

        assert redis_mcp_client.is_connected()

    @pytest.mark.asyncio
    async def test_connect_invalid_password(self, redis_mcp_client):
        """Test connection with invalid password."""
        config = DOCKER_CONFIGS['redis']

        with pytest.raises(Exception):
            await redis_mcp_client.connect(
                host=config['host'],
                port=config['port'],
                password='wrong_password'
            )

    @pytest.mark.asyncio
    async def test_disconnect(self, redis_mcp_client, redis_clean):
        """Test disconnection from Redis."""
        config = DOCKER_CONFIGS['redis']

        await redis_mcp_client.connect(**config)
        assert redis_mcp_client.is_connected()

        await redis_mcp_client.disconnect()
        assert not redis_mcp_client.is_connected()

    @pytest.mark.asyncio
    async def test_reconnect(self, redis_mcp_client, redis_clean):
        """Test reconnection after disconnect."""
        config = DOCKER_CONFIGS['redis']

        await redis_mcp_client.connect(**config)
        await redis_mcp_client.disconnect()
        await redis_mcp_client.connect(**config)

        assert redis_mcp_client.is_connected()

    @pytest.mark.asyncio
    async def test_ping(self, redis_mcp_client, redis_clean):
        """Test ping command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        result = await redis_mcp_client.ping()

        assert result is True or result == 'PONG'


class TestRedisStringOperations:
    """Test Redis string operations."""

    @pytest.mark.asyncio
    async def test_set_get(self, redis_mcp_client, redis_clean):
        """Test SET and GET commands."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.set('test_key', 'test_value')
        value = await redis_mcp_client.get('test_key')

        assert value == 'test_value'

    @pytest.mark.asyncio
    async def test_set_with_expiration(self, redis_mcp_client, redis_clean):
        """Test SET with expiration time."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.set('expire_key', 'expire_value', ex=1)

        # Verify value exists
        value = await redis_mcp_client.get('expire_key')
        assert value == 'expire_value'

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Verify value expired
        value = await redis_mcp_client.get('expire_key')
        assert value is None

    @pytest.mark.asyncio
    async def test_setex(self, redis_mcp_client, redis_clean):
        """Test SETEX command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.setex('setex_key', 2, 'setex_value')

        value = await redis_mcp_client.get('setex_key')
        assert value == 'setex_value'

    @pytest.mark.asyncio
    async def test_setnx(self, redis_mcp_client, redis_clean):
        """Test SETNX command (set if not exists)."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        # First set should succeed
        result1 = await redis_mcp_client.setnx('setnx_key', 'value1')
        assert result1 is True

        # Second set should fail
        result2 = await redis_mcp_client.setnx('setnx_key', 'value2')
        assert result2 is False

        # Value should be unchanged
        value = await redis_mcp_client.get('setnx_key')
        assert value == 'value1'

    @pytest.mark.asyncio
    async def test_getset(self, redis_mcp_client, redis_clean):
        """Test GETSET command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.set('getset_key', 'old_value')

        old_value = await redis_mcp_client.getset('getset_key', 'new_value')

        assert old_value == 'old_value'

        new_value = await redis_mcp_client.get('getset_key')
        assert new_value == 'new_value'

    @pytest.mark.asyncio
    async def test_incr_decr(self, redis_mcp_client, redis_clean):
        """Test INCR and DECR commands."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.set('counter', '10')

        # Increment
        new_value = await redis_mcp_client.incr('counter')
        assert new_value == 11

        # Decrement
        new_value = await redis_mcp_client.decr('counter')
        assert new_value == 10

    @pytest.mark.asyncio
    async def test_incrby_decrby(self, redis_mcp_client, redis_clean):
        """Test INCRBY and DECRBY commands."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.set('counter', '100')

        # Increment by 50
        new_value = await redis_mcp_client.incrby('counter', 50)
        assert new_value == 150

        # Decrement by 25
        new_value = await redis_mcp_client.decrby('counter', 25)
        assert new_value == 125

    @pytest.mark.asyncio
    async def test_delete_key(self, redis_mcp_client, redis_clean):
        """Test DEL command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.set('delete_key', 'delete_value')

        # Delete
        deleted_count = await redis_mcp_client.delete('delete_key')
        assert deleted_count == 1

        # Verify deletion
        value = await redis_mcp_client.get('delete_key')
        assert value is None


class TestRedisHashOperations:
    """Test Redis hash operations."""

    @pytest.mark.asyncio
    async def test_hset_hget(self, redis_mcp_client, redis_clean):
        """Test HSET and HGET commands."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.hset('user:1', 'name', 'John Doe')
        await redis_mcp_client.hset('user:1', 'email', 'john@example.com')

        name = await redis_mcp_client.hget('user:1', 'name')
        email = await redis_mcp_client.hget('user:1', 'email')

        assert name == 'John Doe'
        assert email == 'john@example.com'

    @pytest.mark.asyncio
    async def test_hmset_hmget(self, redis_mcp_client, redis_clean):
        """Test HMSET and HMGET commands."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        # Set multiple fields
        await redis_mcp_client.hmset('user:2', {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'age': '30'
        })

        # Get multiple fields
        values = await redis_mcp_client.hmget('user:2', 'name', 'email', 'age')

        assert values == ['Jane Smith', 'jane@example.com', '30']

    @pytest.mark.asyncio
    async def test_hgetall(self, redis_mcp_client, redis_clean):
        """Test HGETALL command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.hmset('user:3', {
            'name': 'Bob',
            'email': 'bob@example.com',
            'age': '25'
        })

        all_fields = await redis_mcp_client.hgetall('user:3')

        assert all_fields['name'] == 'Bob'
        assert all_fields['email'] == 'bob@example.com'
        assert all_fields['age'] == '25'

    @pytest.mark.asyncio
    async def test_hdel(self, redis_mcp_client, redis_clean):
        """Test HDEL command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.hmset('user:4', {'name': 'Alice', 'email': 'alice@example.com'})

        # Delete field
        deleted = await redis_mcp_client.hdel('user:4', 'email')
        assert deleted == 1

        # Verify deletion
        email = await redis_mcp_client.hget('user:4', 'email')
        assert email is None

    @pytest.mark.asyncio
    async def test_hexists(self, redis_mcp_client, redis_clean):
        """Test HEXISTS command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.hset('user:5', 'name', 'Test User')

        exists = await redis_mcp_client.hexists('user:5', 'name')
        assert exists is True

        not_exists = await redis_mcp_client.hexists('user:5', 'nonexistent')
        assert not_exists is False


class TestRedisListOperations:
    """Test Redis list operations."""

    @pytest.mark.asyncio
    async def test_lpush_lrange(self, redis_mcp_client, redis_clean):
        """Test LPUSH and LRANGE commands."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.lpush('list1', 'item1', 'item2', 'item3')

        items = await redis_mcp_client.lrange('list1', 0, -1)

        assert items == ['item3', 'item2', 'item1']  # LPUSH adds to front

    @pytest.mark.asyncio
    async def test_rpush(self, redis_mcp_client, redis_clean):
        """Test RPUSH command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.rpush('list2', 'item1', 'item2', 'item3')

        items = await redis_mcp_client.lrange('list2', 0, -1)

        assert items == ['item1', 'item2', 'item3']  # RPUSH adds to end

    @pytest.mark.asyncio
    async def test_lpop_rpop(self, redis_mcp_client, redis_clean):
        """Test LPOP and RPOP commands."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.rpush('list3', 'a', 'b', 'c', 'd')

        left = await redis_mcp_client.lpop('list3')
        right = await redis_mcp_client.rpop('list3')

        assert left == 'a'
        assert right == 'd'

        remaining = await redis_mcp_client.lrange('list3', 0, -1)
        assert remaining == ['b', 'c']

    @pytest.mark.asyncio
    async def test_llen(self, redis_mcp_client, redis_clean):
        """Test LLEN command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.rpush('list4', 'a', 'b', 'c')

        length = await redis_mcp_client.llen('list4')

        assert length == 3

    @pytest.mark.asyncio
    async def test_lindex(self, redis_mcp_client, redis_clean):
        """Test LINDEX command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.rpush('list5', 'a', 'b', 'c')

        item = await redis_mcp_client.lindex('list5', 1)

        assert item == 'b'


class TestRedisSetOperations:
    """Test Redis set operations."""

    @pytest.mark.asyncio
    async def test_sadd_smembers(self, redis_mcp_client, redis_clean):
        """Test SADD and SMEMBERS commands."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.sadd('set1', 'member1', 'member2', 'member3')

        members = await redis_mcp_client.smembers('set1')

        assert 'member1' in members
        assert 'member2' in members
        assert 'member3' in members

    @pytest.mark.asyncio
    async def test_sismember(self, redis_mcp_client, redis_clean):
        """Test SISMEMBER command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.sadd('set2', 'a', 'b', 'c')

        is_member = await redis_mcp_client.sismember('set2', 'b')
        not_member = await redis_mcp_client.sismember('set2', 'd')

        assert is_member is True
        assert not_member is False

    @pytest.mark.asyncio
    async def test_srem(self, redis_mcp_client, redis_clean):
        """Test SREM command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.sadd('set3', 'a', 'b', 'c')

        removed = await redis_mcp_client.srem('set3', 'b')
        assert removed == 1

        members = await redis_mcp_client.smembers('set3')
        assert 'b' not in members

    @pytest.mark.asyncio
    async def test_scard(self, redis_mcp_client, redis_clean):
        """Test SCARD command (cardinality)."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.sadd('set4', 'a', 'b', 'c', 'd', 'e')

        count = await redis_mcp_client.scard('set4')

        assert count == 5

    @pytest.mark.asyncio
    async def test_sunion(self, redis_mcp_client, redis_clean):
        """Test SUNION command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.sadd('set5a', 'a', 'b', 'c')
        await redis_mcp_client.sadd('set5b', 'c', 'd', 'e')

        union = await redis_mcp_client.sunion('set5a', 'set5b')

        assert len(union) == 5
        assert all(item in union for item in ['a', 'b', 'c', 'd', 'e'])


class TestRedisSortedSetOperations:
    """Test Redis sorted set operations."""

    @pytest.mark.asyncio
    async def test_zadd_zrange(self, redis_mcp_client, redis_clean):
        """Test ZADD and ZRANGE commands."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.zadd('leaderboard', {'player1': 100, 'player2': 200, 'player3': 150})

        # Get all members in order
        members = await redis_mcp_client.zrange('leaderboard', 0, -1)

        assert members == ['player1', 'player3', 'player2']  # Sorted by score

    @pytest.mark.asyncio
    async def test_zscore(self, redis_mcp_client, redis_clean):
        """Test ZSCORE command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.zadd('scores', {'alice': 85.5, 'bob': 92.0})

        score = await redis_mcp_client.zscore('scores', 'alice')

        assert score == 85.5

    @pytest.mark.asyncio
    async def test_zrank(self, redis_mcp_client, redis_clean):
        """Test ZRANK command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.zadd('ranking', {'a': 10, 'b': 20, 'c': 30})

        rank = await redis_mcp_client.zrank('ranking', 'b')

        assert rank == 1  # 0-indexed, 'b' is second

    @pytest.mark.asyncio
    async def test_zincrby(self, redis_mcp_client, redis_clean):
        """Test ZINCRBY command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.zadd('game_scores', {'player1': 100})

        new_score = await redis_mcp_client.zincrby('game_scores', 50, 'player1')

        assert new_score == 150


class TestRedisPubSub:
    """Test Redis pub/sub functionality."""

    @pytest.mark.asyncio
    async def test_publish_subscribe(self, redis_mcp_client, redis_clean):
        """Test PUBLISH and SUBSCRIBE commands."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        messages = []

        async def subscriber():
            pubsub = await redis_mcp_client.subscribe('test_channel')
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    messages.append(message['data'])
                    break

        async def publisher():
            await asyncio.sleep(0.1)
            await redis_mcp_client.publish('test_channel', 'Hello, World!')

        await asyncio.gather(subscriber(), publisher())

        assert len(messages) == 1
        assert messages[0] == 'Hello, World!'

    @pytest.mark.asyncio
    async def test_pattern_subscribe(self, redis_mcp_client, redis_clean):
        """Test pattern-based subscription."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        messages = []

        async def subscriber():
            pubsub = await redis_mcp_client.psubscribe('channel:*')
            async for message in pubsub.listen():
                if message['type'] == 'pmessage':
                    messages.append(message['data'])
                    if len(messages) >= 2:
                        break

        async def publisher():
            await asyncio.sleep(0.1)
            await redis_mcp_client.publish('channel:1', 'Message 1')
            await redis_mcp_client.publish('channel:2', 'Message 2')

        await asyncio.gather(subscriber(), publisher())

        assert len(messages) == 2


class TestRedisStreams:
    """Test Redis streams."""

    @pytest.mark.asyncio
    async def test_xadd_xread(self, redis_mcp_client, redis_clean):
        """Test XADD and XREAD commands."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        # Add entries to stream
        msg_id1 = await redis_mcp_client.xadd('mystream', {'field1': 'value1', 'field2': 'value2'})
        msg_id2 = await redis_mcp_client.xadd('mystream', {'field1': 'value3', 'field2': 'value4'})

        # Read from stream
        messages = await redis_mcp_client.xread({'mystream': '0'}, count=10)

        assert len(messages) >= 2

    @pytest.mark.asyncio
    async def test_xlen(self, redis_mcp_client, redis_clean):
        """Test XLEN command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.xadd('stream2', {'data': 'message1'})
        await redis_mcp_client.xadd('stream2', {'data': 'message2'})

        length = await redis_mcp_client.xlen('stream2')

        assert length == 2


class TestRedisLuaScripts:
    """Test Redis Lua scripting."""

    @pytest.mark.asyncio
    async def test_eval_script(self, redis_mcp_client, redis_clean):
        """Test EVAL command."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        script = """
        return redis.call('SET', KEYS[1], ARGV[1])
        """

        result = await redis_mcp_client.eval(script, 1, 'lua_key', 'lua_value')

        # Verify
        value = await redis_mcp_client.get('lua_key')
        assert value == 'lua_value'

    @pytest.mark.asyncio
    async def test_eval_complex_script(self, redis_mcp_client, redis_clean):
        """Test complex Lua script."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        script = """
        local current = redis.call('GET', KEYS[1])
        if current then
            return redis.call('INCR', KEYS[1])
        else
            redis.call('SET', KEYS[1], ARGV[1])
            return tonumber(ARGV[1])
        end
        """

        result1 = await redis_mcp_client.eval(script, 1, 'counter', '10')
        assert result1 == 10

        result2 = await redis_mcp_client.eval(script, 1, 'counter', '10')
        assert result2 == 11


class TestRedisTransactions:
    """Test Redis transactions (MULTI/EXEC)."""

    @pytest.mark.asyncio
    async def test_multi_exec(self, redis_mcp_client, redis_clean):
        """Test MULTI/EXEC transaction."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        pipeline = redis_mcp_client.pipeline()

        pipeline.set('tx_key1', 'value1')
        pipeline.set('tx_key2', 'value2')
        pipeline.incr('tx_counter')

        results = await pipeline.execute()

        assert len(results) == 3

        # Verify
        value1 = await redis_mcp_client.get('tx_key1')
        value2 = await redis_mcp_client.get('tx_key2')

        assert value1 == 'value1'
        assert value2 == 'value2'

    @pytest.mark.asyncio
    async def test_watch_unwatch(self, redis_mcp_client, redis_clean):
        """Test WATCH/UNWATCH for optimistic locking."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        await redis_mcp_client.set('watched_key', '10')

        await redis_mcp_client.watch('watched_key')

        # Simulate another client modifying the key
        # (In real scenario, another connection would modify it)

        pipeline = redis_mcp_client.pipeline()
        pipeline.incr('watched_key')

        try:
            await pipeline.execute()
        finally:
            await redis_mcp_client.unwatch()


class TestRedisConnectionPooling:
    """Test Redis connection pooling."""

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, redis_mcp_client, redis_clean):
        """Test concurrent Redis operations."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        async def set_value(index):
            await redis_mcp_client.set(f'concurrent_{index}', f'value_{index}')

        # Run 20 concurrent operations
        tasks = [set_value(i) for i in range(20)]
        await asyncio.gather(*tasks)

        # Verify all values
        for i in range(20):
            value = await redis_mcp_client.get(f'concurrent_{i}')
            assert value == f'value_{i}'


class TestRedisHealthCheck:
    """Test Redis health checks."""

    @pytest.mark.asyncio
    async def test_health_check_connected(self, redis_mcp_client, redis_clean):
        """Test health check when connected."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        health = await redis_mcp_client.health_check()

        assert health['healthy'] is True
        assert 'redis' in health['database_type'].lower()
        assert health['connected'] is True

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, redis_mcp_client):
        """Test health check when disconnected."""
        health = await redis_mcp_client.health_check()

        assert health['healthy'] is False
        assert health['connected'] is False


class TestRedisErrorHandling:
    """Test Redis error handling."""

    @pytest.mark.asyncio
    async def test_wrong_type_operation(self, redis_mcp_client, redis_clean):
        """Test error when performing wrong type operation."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        # Set a string value
        await redis_mcp_client.set('string_key', 'string_value')

        # Try to use list operation on string
        with pytest.raises(Exception) as exc_info:
            await redis_mcp_client.lpush('string_key', 'item')

        assert 'wrong' in str(exc_info.value).lower() or 'type' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connection_timeout(self, redis_mcp_client):
        """Test connection timeout handling."""
        with pytest.raises(Exception):
            await redis_mcp_client.connect(
                host='192.0.2.1',  # Non-routable IP
                port=6379,
                timeout=1
            )
