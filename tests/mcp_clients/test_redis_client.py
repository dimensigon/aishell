"""
Comprehensive Test Suite for Redis MCP Client

Tests all major Redis functionality including:
- Connection management
- Key-value operations
- Hash operations
- List operations
- Set operations
- Sorted set operations
- Pub/sub messaging
- Transactions
- Pipeline operations
- Caching integration
- Session management
- Error handling
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call, MagicMock as MM
from datetime import datetime

# Mock problematic imports before importing the module
mock_motor = MM()
mock_pymongo = MM()
mock_pymongo.errors = MM()
mock_pymongo.errors.PyMongoError = Exception
mock_pymongo.errors.ConnectionFailure = Exception

sys.modules['motor'] = mock_motor
sys.modules['motor.motor_asyncio'] = mock_motor
sys.modules['pymongo'] = mock_pymongo
sys.modules['pymongo.errors'] = mock_pymongo.errors

# Now we can safely import
from src.mcp_clients.redis_client import RedisClient
from src.mcp_clients.base import ConnectionConfig, MCPClientError, ConnectionState


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def connection_config():
    """Create test connection configuration"""
    return ConnectionConfig(
        host="localhost",
        port=6379,
        database="0",
        username="",
        password=""
    )


@pytest.fixture
def connection_config_with_auth():
    """Create test connection configuration with authentication"""
    return ConnectionConfig(
        host="localhost",
        port=6379,
        database="0",
        username="testuser",
        password="testpass123"
    )


@pytest.fixture
def connection_config_with_db():
    """Create test connection configuration with specific database"""
    return ConnectionConfig(
        host="localhost",
        port=6379,
        database="5",
        username="",
        password=""
    )


@pytest.fixture
def mock_redis_client():
    """Create comprehensive mock Redis client"""
    mock_client = AsyncMock()

    # Connection methods
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()

    # Key-value operations
    mock_client.get = AsyncMock(return_value="test_value")
    mock_client.set = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock(return_value=1)
    mock_client.exists = AsyncMock(return_value=1)
    mock_client.expire = AsyncMock(return_value=True)
    mock_client.ttl = AsyncMock(return_value=3600)
    mock_client.keys = AsyncMock(return_value=["key1", "key2", "key3"])
    mock_client.incr = AsyncMock(return_value=1)
    mock_client.decr = AsyncMock(return_value=-1)

    # Hash operations
    mock_client.hget = AsyncMock(return_value="field_value")
    mock_client.hset = AsyncMock(return_value=1)
    mock_client.hgetall = AsyncMock(return_value={"field1": "value1", "field2": "value2"})
    mock_client.hdel = AsyncMock(return_value=1)

    # List operations
    mock_client.lpush = AsyncMock(return_value=3)
    mock_client.rpush = AsyncMock(return_value=3)
    mock_client.lpop = AsyncMock(return_value="item1")
    mock_client.rpop = AsyncMock(return_value="item3")
    mock_client.lrange = AsyncMock(return_value=["item1", "item2", "item3"])

    # Set operations
    mock_client.sadd = AsyncMock(return_value=2)
    mock_client.srem = AsyncMock(return_value=1)
    mock_client.smembers = AsyncMock(return_value={"member1", "member2", "member3"})
    mock_client.sismember = AsyncMock(return_value=True)

    # Sorted set operations
    mock_client.zadd = AsyncMock(return_value=2)
    mock_client.zrem = AsyncMock(return_value=1)
    mock_client.zrange = AsyncMock(return_value=["player1", "player2"])
    mock_client.zscore = AsyncMock(return_value=100.0)

    # Pub/sub operations
    mock_client.publish = AsyncMock(return_value=5)
    mock_pubsub = AsyncMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_client.pubsub = MagicMock(return_value=mock_pubsub)

    # Transaction operations
    mock_pipeline = AsyncMock()
    mock_pipeline.execute = AsyncMock(return_value=[True, True, 3])
    mock_pipeline.set = MagicMock(return_value=mock_pipeline)
    mock_pipeline.get = MagicMock(return_value=mock_pipeline)
    mock_pipeline.incr = MagicMock(return_value=mock_pipeline)
    mock_client.pipeline = MagicMock(return_value=mock_pipeline)

    # DDL operations
    mock_client.flushdb = AsyncMock()
    mock_client.flushall = AsyncMock()
    mock_client.select = AsyncMock()

    return mock_client


@pytest.fixture
def redis_client():
    """Create Redis client instance"""
    return RedisClient()


# ============================================================================
# Connection Management Tests
# ============================================================================

@pytest.mark.asyncio
class TestConnectionManagement:
    """Test Redis connection management"""

    async def test_basic_connection(self, redis_client, connection_config, mock_redis_client):
        """Test basic Redis connection"""
        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            result = await redis_client.connect(connection_config)

            assert result is True
            assert redis_client.state == ConnectionState.CONNECTED
            assert redis_client.is_connected
            mock_redis_client.ping.assert_called_once()

    async def test_connection_with_authentication(self, redis_client, connection_config_with_auth, mock_redis_client):
        """Test Redis connection with authentication"""
        with patch('src.mcp_clients.redis_client.aioredis.Redis') as mock_class:
            mock_class.return_value = mock_redis_client

            result = await redis_client.connect(connection_config_with_auth)

            assert result is True
            # Verify password was passed
            call_args = mock_class.call_args
            assert 'password' in call_args[1]
            assert call_args[1]['password'] == "testpass123"

    async def test_connection_with_specific_database(self, redis_client, connection_config_with_db, mock_redis_client):
        """Test Redis connection with specific database"""
        with patch('src.mcp_clients.redis_client.aioredis.Redis') as mock_class:
            mock_class.return_value = mock_redis_client

            result = await redis_client.connect(connection_config_with_db)

            assert result is True
            # Verify database was set
            call_args = mock_class.call_args
            assert call_args[1]['db'] == 5

    async def test_connection_failure_refused(self, redis_client, connection_config):
        """Test Redis connection failure - connection refused"""
        with patch('src.mcp_clients.redis_client.aioredis.Redis') as mock_class:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(side_effect=ConnectionError("Connection refused"))
            mock_class.return_value = mock_client

            with pytest.raises(MCPClientError) as exc_info:
                await redis_client.connect(connection_config)

            assert "CONNECTION_FAILED" in str(exc_info.value.error_code)
            assert "Connection refused" in str(exc_info.value)

    async def test_connection_failure_timeout(self, redis_client, connection_config):
        """Test Redis connection failure - timeout"""
        with patch('src.mcp_clients.redis_client.aioredis.Redis') as mock_class:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_class.return_value = mock_client

            with pytest.raises(MCPClientError) as exc_info:
                await redis_client.connect(connection_config)

            assert "CONNECTION_FAILED" in str(exc_info.value.error_code)

    async def test_disconnect(self, redis_client, connection_config, mock_redis_client):
        """Test Redis disconnection"""
        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)
            result = await redis_client.disconnect()

            assert result is True
            assert redis_client.state == ConnectionState.CLOSED
            mock_redis_client.close.assert_called_once()

    async def test_disconnect_with_pubsub(self, redis_client, connection_config, mock_redis_client):
        """Test disconnection with active pub/sub"""
        mock_pubsub = AsyncMock()
        mock_pubsub.close = AsyncMock()

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)
            redis_client._pubsub = mock_pubsub

            result = await redis_client.disconnect()

            assert result is True
            mock_pubsub.close.assert_called_once()
            mock_redis_client.close.assert_called_once()

    async def test_reconnection(self, redis_client, connection_config, mock_redis_client):
        """Test reconnection after disconnect"""
        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            # First connection
            await redis_client.connect(connection_config)
            await redis_client.disconnect()

            # Reconnect
            result = await redis_client.connect(connection_config)

            assert result is True
            assert redis_client.is_connected


# ============================================================================
# Key-Value Operation Tests
# ============================================================================

@pytest.mark.asyncio
class TestKeyValueOperations:
    """Test Redis key-value operations"""

    async def test_get_existing_key(self, redis_client, connection_config, mock_redis_client):
        """Test GET operation for existing key"""
        mock_redis_client.get = AsyncMock(return_value="test_value")

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'get', 'key': 'test_key'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            assert result.rows[0][1] == "test_value"
            mock_redis_client.get.assert_called_once_with('test_key')

    async def test_get_non_existing_key(self, redis_client, connection_config, mock_redis_client):
        """Test GET operation for non-existing key"""
        mock_redis_client.get = AsyncMock(return_value=None)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'get', 'key': 'missing_key'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 0

    async def test_set_basic(self, redis_client, connection_config, mock_redis_client):
        """Test basic SET operation"""
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'set', 'key': 'test_key', 'value': 'test_value'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            mock_redis_client.set.assert_called_once()

    async def test_set_with_expiration(self, redis_client, connection_config, mock_redis_client):
        """Test SET operation with expiration"""
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'set', 'key': 'test_key', 'value': 'test_value', 'ex': 3600}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            call_args = mock_redis_client.set.call_args
            assert call_args[1]['ex'] == 3600

    async def test_set_nx_not_exists(self, redis_client, connection_config, mock_redis_client):
        """Test SET with NX flag (only if not exists)"""
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'set', 'key': 'new_key', 'value': 'value', 'nx': True}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            call_args = mock_redis_client.set.call_args
            assert call_args[1]['nx'] is True

    async def test_set_xx_exists(self, redis_client, connection_config, mock_redis_client):
        """Test SET with XX flag (only if exists)"""
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'set', 'key': 'existing_key', 'value': 'new_value', 'xx': True}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            call_args = mock_redis_client.set.call_args
            assert call_args[1]['xx'] is True

    async def test_delete_single_key(self, redis_client, connection_config, mock_redis_client):
        """Test DELETE operation for single key"""
        mock_redis_client.delete = AsyncMock(return_value=1)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'delete', 'keys': ['test_key']}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1

    async def test_delete_multiple_keys(self, redis_client, connection_config, mock_redis_client):
        """Test DELETE operation for multiple keys"""
        mock_redis_client.delete = AsyncMock(return_value=3)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'delete', 'keys': ['key1', 'key2', 'key3']}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 3

    async def test_exists_single_key(self, redis_client, connection_config, mock_redis_client):
        """Test EXISTS operation for single key"""
        mock_redis_client.exists = AsyncMock(return_value=1)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'exists', 'keys': ['test_key']}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1

    async def test_exists_multiple_keys(self, redis_client, connection_config, mock_redis_client):
        """Test EXISTS operation for multiple keys"""
        mock_redis_client.exists = AsyncMock(return_value=2)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'exists', 'keys': ['key1', 'key2', 'key3']}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 2

    async def test_expire_key(self, redis_client, connection_config, mock_redis_client):
        """Test EXPIRE operation"""
        mock_redis_client.expire = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'expire', 'key': 'test_key', 'seconds': 300}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            mock_redis_client.expire.assert_called_once_with('test_key', 300)

    async def test_ttl_key(self, redis_client, connection_config, mock_redis_client):
        """Test TTL operation"""
        mock_redis_client.ttl = AsyncMock(return_value=3600)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'ttl', 'key': 'test_key'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            assert result.rows[0][1] == 3600

    async def test_keys_pattern(self, redis_client, connection_config, mock_redis_client):
        """Test KEYS operation with pattern"""
        mock_redis_client.keys = AsyncMock(return_value=["user:1", "user:2", "user:3"])

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'keys', 'pattern': 'user:*'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 3
            mock_redis_client.keys.assert_called_once_with('user:*')

    async def test_incr_operation(self, redis_client, connection_config, mock_redis_client):
        """Test INCR operation"""
        mock_redis_client.incr = AsyncMock(return_value=5)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'incr', 'key': 'counter'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            assert result.rows[0][0] == 5

    async def test_decr_operation(self, redis_client, connection_config, mock_redis_client):
        """Test DECR operation"""
        mock_redis_client.decr = AsyncMock(return_value=3)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'decr', 'key': 'counter'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            assert result.rows[0][0] == 3


# ============================================================================
# Hash Operation Tests
# ============================================================================

@pytest.mark.asyncio
class TestHashOperations:
    """Test Redis hash operations"""

    async def test_hget_field(self, redis_client, connection_config, mock_redis_client):
        """Test HGET operation"""
        mock_redis_client.hget = AsyncMock(return_value="Alice")

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'hget', 'key': 'user:1', 'field': 'name'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            assert result.rows[0][1] == "Alice"

    async def test_hset_field(self, redis_client, connection_config, mock_redis_client):
        """Test HSET operation"""
        mock_redis_client.hset = AsyncMock(return_value=1)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'hset', 'key': 'user:1', 'field': 'name', 'value': 'Alice'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            mock_redis_client.hset.assert_called_once_with('user:1', 'name', 'Alice')

    async def test_hgetall_hash(self, redis_client, connection_config, mock_redis_client):
        """Test HGETALL operation"""
        mock_redis_client.hgetall = AsyncMock(return_value={
            'name': 'Alice',
            'age': '30',
            'city': 'New York'
        })

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'hgetall', 'key': 'user:1'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 3
            assert len(result.rows) == 3

    async def test_hget_non_existing_field(self, redis_client, connection_config, mock_redis_client):
        """Test HGET for non-existing field"""
        mock_redis_client.hget = AsyncMock(return_value=None)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'hget', 'key': 'user:1', 'field': 'missing'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 0


# ============================================================================
# List Operation Tests
# ============================================================================

@pytest.mark.asyncio
class TestListOperations:
    """Test Redis list operations"""

    async def test_lpush_single_value(self, redis_client, connection_config, mock_redis_client):
        """Test LPUSH with single value"""
        mock_redis_client.lpush = AsyncMock(return_value=1)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'lpush', 'key': 'queue', 'values': ['item1']}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1

    async def test_lpush_multiple_values(self, redis_client, connection_config, mock_redis_client):
        """Test LPUSH with multiple values"""
        mock_redis_client.lpush = AsyncMock(return_value=3)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'lpush', 'key': 'queue', 'values': ['item1', 'item2', 'item3']}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1

    async def test_rpush_values(self, redis_client, connection_config, mock_redis_client):
        """Test RPUSH operation"""
        mock_redis_client.rpush = AsyncMock(return_value=2)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'rpush', 'key': 'queue', 'values': ['item1', 'item2']}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1

    async def test_lpop_value(self, redis_client, connection_config, mock_redis_client):
        """Test LPOP operation"""
        mock_redis_client.lpop = AsyncMock(return_value="first_item")

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'lpop', 'key': 'queue'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            assert result.rows[0][0] == "first_item"

    async def test_rpop_value(self, redis_client, connection_config, mock_redis_client):
        """Test RPOP operation"""
        mock_redis_client.rpop = AsyncMock(return_value="last_item")

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'rpop', 'key': 'queue'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1
            assert result.rows[0][0] == "last_item"

    async def test_lrange_full_list(self, redis_client, connection_config, mock_redis_client):
        """Test LRANGE for full list"""
        mock_redis_client.lrange = AsyncMock(return_value=["item1", "item2", "item3"])

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'lrange', 'key': 'queue', 'start': 0, 'stop': -1}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 3

    async def test_lrange_partial_list(self, redis_client, connection_config, mock_redis_client):
        """Test LRANGE for partial list"""
        mock_redis_client.lrange = AsyncMock(return_value=["item1", "item2"])

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'lrange', 'key': 'queue', 'start': 0, 'stop': 1}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 2

    async def test_lpop_empty_list(self, redis_client, connection_config, mock_redis_client):
        """Test LPOP on empty list"""
        mock_redis_client.lpop = AsyncMock(return_value=None)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'lpop', 'key': 'empty_queue'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 0


# ============================================================================
# Set Operation Tests
# ============================================================================

@pytest.mark.asyncio
class TestSetOperations:
    """Test Redis set operations"""

    async def test_sadd_members(self, redis_client, connection_config, mock_redis_client):
        """Test SADD operation"""
        mock_redis_client.sadd = AsyncMock(return_value=3)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'sadd', 'key': 'tags', 'members': ['tag1', 'tag2', 'tag3']}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 3

    async def test_smembers_set(self, redis_client, connection_config, mock_redis_client):
        """Test SMEMBERS operation"""
        mock_redis_client.smembers = AsyncMock(return_value={"tag1", "tag2", "tag3"})

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'smembers', 'key': 'tags'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 3

    async def test_sadd_duplicate_members(self, redis_client, connection_config, mock_redis_client):
        """Test SADD with duplicate members (should only add unique)"""
        mock_redis_client.sadd = AsyncMock(return_value=1)  # Only 1 new member added

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'sadd', 'key': 'tags', 'members': ['tag1', 'tag1', 'tag2']}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 1


# ============================================================================
# Sorted Set Operation Tests
# ============================================================================

@pytest.mark.asyncio
class TestSortedSetOperations:
    """Test Redis sorted set operations"""

    async def test_zadd_members(self, redis_client, connection_config, mock_redis_client):
        """Test ZADD operation"""
        mock_redis_client.zadd = AsyncMock(return_value=2)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'zadd', 'key': 'leaderboard', 'mapping': {'player1': 100, 'player2': 200}}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 2

    async def test_zrange_without_scores(self, redis_client, connection_config, mock_redis_client):
        """Test ZRANGE without scores"""
        mock_redis_client.zrange = AsyncMock(return_value=["player1", "player2", "player3"])

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'zrange', 'key': 'leaderboard', 'start': 0, 'stop': -1, 'withscores': False}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 3

    async def test_zrange_with_scores(self, redis_client, connection_config, mock_redis_client):
        """Test ZRANGE with scores"""
        # When withscores=True, Redis returns interleaved values and scores
        mock_redis_client.zrange = AsyncMock(return_value=["player1", 100, "player2", 200])

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'zrange', 'key': 'leaderboard', 'start': 0, 'stop': -1, 'withscores': True}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 2
            assert 'score' in result.columns


# ============================================================================
# Pub/Sub Tests
# ============================================================================

@pytest.mark.asyncio
class TestPubSub:
    """Test Redis pub/sub functionality"""

    async def test_publish_message(self, redis_client, connection_config, mock_redis_client):
        """Test publishing a message"""
        mock_redis_client.publish = AsyncMock(return_value=5)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.publish('notifications', 'Test message')

            assert result == 5
            mock_redis_client.publish.assert_called_once_with('notifications', 'Test message')

    async def test_subscribe_channel(self, redis_client, connection_config, mock_redis_client):
        """Test subscribing to a channel"""
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_redis_client.pubsub = MagicMock(return_value=mock_pubsub)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            callback = AsyncMock()

            # Mock the listen coroutine
            with patch.object(redis_client, '_listen_pubsub', new_callable=AsyncMock):
                await redis_client.subscribe('notifications', callback)

            mock_pubsub.subscribe.assert_called_once_with('notifications')
            assert 'notifications' in redis_client._subscribers

    async def test_unsubscribe_channel(self, redis_client, connection_config, mock_redis_client):
        """Test unsubscribing from a channel"""
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_redis_client.pubsub = MagicMock(return_value=mock_pubsub)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            callback = AsyncMock()

            # Subscribe first
            with patch.object(redis_client, '_listen_pubsub', new_callable=AsyncMock):
                await redis_client.subscribe('notifications', callback)
                await redis_client.unsubscribe('notifications')

            mock_pubsub.unsubscribe.assert_called_once_with('notifications')
            assert 'notifications' not in redis_client._subscribers

    async def test_publish_no_subscribers(self, redis_client, connection_config, mock_redis_client):
        """Test publishing with no subscribers"""
        mock_redis_client.publish = AsyncMock(return_value=0)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.publish('empty_channel', 'Message')

            assert result == 0


# ============================================================================
# Caching Integration Tests
# ============================================================================

@pytest.mark.asyncio
class TestCachingIntegration:
    """Test high-level caching methods"""

    async def test_cache_set_simple_value(self, redis_client, connection_config, mock_redis_client):
        """Test cache_set with simple value"""
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.cache_set('user:1', {'name': 'Alice', 'age': 30})

            assert result is True
            mock_redis_client.set.assert_called_once()

    async def test_cache_set_with_ttl(self, redis_client, connection_config, mock_redis_client):
        """Test cache_set with TTL"""
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.cache_set('temp_key', 'value', ttl=300)

            assert result is True
            call_args = mock_redis_client.set.call_args
            assert call_args[1]['ex'] == 300

    async def test_cache_get_existing(self, redis_client, connection_config, mock_redis_client):
        """Test cache_get for existing key"""
        mock_redis_client.get = AsyncMock(return_value='{"name": "Alice", "age": 30}')

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.cache_get('user:1')

            assert result == {'name': 'Alice', 'age': 30}

    async def test_cache_get_non_existing(self, redis_client, connection_config, mock_redis_client):
        """Test cache_get for non-existing key"""
        mock_redis_client.get = AsyncMock(return_value=None)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.cache_get('missing_key')

            assert result is None

    async def test_cache_get_no_deserialize(self, redis_client, connection_config, mock_redis_client):
        """Test cache_get without deserialization"""
        mock_redis_client.get = AsyncMock(return_value='raw_string_value')

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.cache_get('key', deserialize=False)

            assert result == 'raw_string_value'

    async def test_cache_delete_single(self, redis_client, connection_config, mock_redis_client):
        """Test cache_delete with single key"""
        mock_redis_client.delete = AsyncMock(return_value=1)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.cache_delete('key1')

            assert result == 1

    async def test_cache_delete_multiple(self, redis_client, connection_config, mock_redis_client):
        """Test cache_delete with multiple keys"""
        mock_redis_client.delete = AsyncMock(return_value=3)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.cache_delete('key1', 'key2', 'key3')

            assert result == 3

    async def test_cache_exists_keys(self, redis_client, connection_config, mock_redis_client):
        """Test cache_exists method"""
        mock_redis_client.exists = AsyncMock(return_value=2)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.cache_exists('key1', 'key2', 'key3')

            assert result == 2


# ============================================================================
# Session Management Tests
# ============================================================================

@pytest.mark.asyncio
class TestSessionManagement:
    """Test session management functionality"""

    async def test_session_create(self, redis_client, connection_config, mock_redis_client):
        """Test creating a session"""
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.session_create(
                'session123',
                {'user_id': 1, 'username': 'alice'}
            )

            assert result is True
            # Verify the key has session: prefix
            call_args = mock_redis_client.set.call_args
            assert 'session:session123' in str(call_args)

    async def test_session_create_with_custom_ttl(self, redis_client, connection_config, mock_redis_client):
        """Test creating a session with custom TTL"""
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.session_create(
                'session123',
                {'user_id': 1},
                ttl=7200
            )

            assert result is True
            call_args = mock_redis_client.set.call_args
            assert call_args[1]['ex'] == 7200

    async def test_session_get_existing(self, redis_client, connection_config, mock_redis_client):
        """Test retrieving an existing session"""
        mock_redis_client.get = AsyncMock(return_value='{"user_id": 1, "username": "alice"}')

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.session_get('session123')

            assert result is not None
            assert result['username'] == 'alice'
            assert result['user_id'] == 1

    async def test_session_get_non_existing(self, redis_client, connection_config, mock_redis_client):
        """Test retrieving a non-existing session"""
        mock_redis_client.get = AsyncMock(return_value=None)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.session_get('missing_session')

            assert result is None

    async def test_session_update(self, redis_client, connection_config, mock_redis_client):
        """Test updating a session"""
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.session_update(
                'session123',
                {'user_id': 1, 'username': 'alice', 'last_activity': '2025-01-01'}
            )

            assert result is True

    async def test_session_delete_existing(self, redis_client, connection_config, mock_redis_client):
        """Test deleting an existing session"""
        mock_redis_client.delete = AsyncMock(return_value=1)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.session_delete('session123')

            assert result is True

    async def test_session_delete_non_existing(self, redis_client, connection_config, mock_redis_client):
        """Test deleting a non-existing session"""
        mock_redis_client.delete = AsyncMock(return_value=0)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.session_delete('missing_session')

            assert result is False

    async def test_session_extend(self, redis_client, connection_config, mock_redis_client):
        """Test extending session TTL"""
        mock_redis_client.expire = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            result = await redis_client.session_extend('session123', ttl=7200)

            assert result is True
            mock_redis_client.expire.assert_called_once()


# ============================================================================
# DDL Operation Tests
# ============================================================================

@pytest.mark.asyncio
class TestDDLOperations:
    """Test DDL-like operations"""

    async def test_flushdb(self, redis_client, connection_config, mock_redis_client):
        """Test FLUSHDB operation"""
        mock_redis_client.flushdb = AsyncMock()

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            ddl = {'operation': 'flushdb'}
            await redis_client.execute_ddl(json.dumps(ddl))

            mock_redis_client.flushdb.assert_called_once()

    async def test_flushall(self, redis_client, connection_config, mock_redis_client):
        """Test FLUSHALL operation"""
        mock_redis_client.flushall = AsyncMock()

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            ddl = {'operation': 'flushall'}
            await redis_client.execute_ddl(json.dumps(ddl))

            mock_redis_client.flushall.assert_called_once()

    async def test_select_database(self, redis_client, connection_config, mock_redis_client):
        """Test SELECT database operation"""
        mock_redis_client.select = AsyncMock()

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            ddl = {'operation': 'select', 'db': 5}
            await redis_client.execute_ddl(json.dumps(ddl))

            mock_redis_client.select.assert_called_once_with(5)

    async def test_unsupported_ddl_operation(self, redis_client, connection_config, mock_redis_client):
        """Test unsupported DDL operation"""
        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            ddl = {'operation': 'invalid_operation'}

            with pytest.raises(MCPClientError) as exc_info:
                await redis_client.execute_ddl(json.dumps(ddl))

            # Base class wraps all DDL errors as DDL_FAILED
            assert "DDL_FAILED" in str(exc_info.value.error_code)


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling scenarios"""

    async def test_execute_query_not_connected(self, redis_client):
        """Test executing query without connection"""
        query = {'command': 'get', 'key': 'test'}

        with pytest.raises(MCPClientError) as exc_info:
            await redis_client.execute_query(json.dumps(query))

        assert "NOT_CONNECTED" in str(exc_info.value.error_code)

    async def test_invalid_json_command(self, redis_client, connection_config, mock_redis_client):
        """Test invalid JSON command"""
        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            with pytest.raises(MCPClientError) as exc_info:
                await redis_client.execute_query('invalid json{')

            # Base class wraps all query errors as QUERY_FAILED
            assert "QUERY_FAILED" in str(exc_info.value.error_code)

    async def test_unsupported_command(self, redis_client, connection_config, mock_redis_client):
        """Test unsupported Redis command"""
        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'unsupported_cmd', 'key': 'test'}

            with pytest.raises(MCPClientError) as exc_info:
                await redis_client.execute_query(json.dumps(query))

            assert "Unsupported command" in str(exc_info.value)

    async def test_redis_error_during_query(self, redis_client, connection_config, mock_redis_client):
        """Test Redis error during query execution"""
        from redis.exceptions import RedisError

        mock_redis_client.get = AsyncMock(side_effect=RedisError("Connection lost"))

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'get', 'key': 'test'}

            with pytest.raises(MCPClientError) as exc_info:
                await redis_client.execute_query(json.dumps(query))

            # Base class wraps all query errors as QUERY_FAILED
            assert "QUERY_FAILED" in str(exc_info.value.error_code)

    async def test_cache_set_not_connected(self, redis_client):
        """Test cache_set without connection"""
        with pytest.raises(MCPClientError) as exc_info:
            await redis_client.cache_set('key', 'value')

        assert "NOT_CONNECTED" in str(exc_info.value.error_code)

    async def test_publish_not_connected(self, redis_client):
        """Test publish without connection"""
        with pytest.raises(MCPClientError) as exc_info:
            await redis_client.publish('channel', 'message')

        assert "NOT_CONNECTED" in str(exc_info.value.error_code)

    async def test_subscribe_not_connected(self, redis_client):
        """Test subscribe without connection"""
        with pytest.raises(MCPClientError) as exc_info:
            await redis_client.subscribe('channel', AsyncMock())

        assert "NOT_CONNECTED" in str(exc_info.value.error_code)

    async def test_ddl_not_connected(self, redis_client):
        """Test DDL operation without connection"""
        ddl = {'operation': 'flushdb'}

        with pytest.raises(MCPClientError) as exc_info:
            await redis_client.execute_ddl(json.dumps(ddl))

        assert "NOT_CONNECTED" in str(exc_info.value.error_code)


# ============================================================================
# Integration and Edge Case Tests
# ============================================================================

@pytest.mark.asyncio
class TestIntegrationAndEdgeCases:
    """Test integration scenarios and edge cases"""

    async def test_connection_state_transitions(self, redis_client, connection_config, mock_redis_client):
        """Test connection state transitions"""
        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            # Initial state
            assert redis_client.state == ConnectionState.DISCONNECTED

            # Connect
            await redis_client.connect(connection_config)
            assert redis_client.state == ConnectionState.CONNECTED

            # Disconnect - base class sets state to CLOSED
            await redis_client.disconnect()
            assert redis_client.state == ConnectionState.CLOSED

    async def test_complex_json_serialization(self, redis_client, connection_config, mock_redis_client):
        """Test caching complex nested objects"""
        mock_redis_client.set = AsyncMock(return_value=True)
        mock_redis_client.get = AsyncMock(return_value='{"user": {"id": 1, "profile": {"name": "Alice", "tags": ["admin", "premium"]}}}')

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            # Set complex object
            complex_obj = {
                'user': {
                    'id': 1,
                    'profile': {
                        'name': 'Alice',
                        'tags': ['admin', 'premium']
                    }
                }
            }
            await redis_client.cache_set('user:1', complex_obj)

            # Get complex object
            result = await redis_client.cache_get('user:1')

            assert result['user']['profile']['tags'] == ['admin', 'premium']

    async def test_malformed_json_deserialization(self, redis_client, connection_config, mock_redis_client):
        """Test handling malformed JSON during deserialization"""
        mock_redis_client.get = AsyncMock(return_value='not valid json{')

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            # Should return the raw string if JSON decode fails
            result = await redis_client.cache_get('key')

            assert result == 'not valid json{'

    async def test_empty_list_operations(self, redis_client, connection_config, mock_redis_client):
        """Test list operations on empty lists"""
        mock_redis_client.lrange = AsyncMock(return_value=[])

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'lrange', 'key': 'empty_list', 'start': 0, 'stop': -1}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 0
            assert len(result.rows) == 0

    async def test_empty_set_operations(self, redis_client, connection_config, mock_redis_client):
        """Test set operations on empty sets"""
        mock_redis_client.smembers = AsyncMock(return_value=set())

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'smembers', 'key': 'empty_set'}
            result = await redis_client.execute_query(json.dumps(query))

            assert result.rowcount == 0

    async def test_concurrent_operations(self, redis_client, connection_config, mock_redis_client):
        """Test concurrent Redis operations"""
        mock_redis_client.get = AsyncMock(return_value="value")

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            # Execute multiple operations concurrently
            queries = [
                redis_client.execute_query(json.dumps({'command': 'get', 'key': f'key{i}'}))
                for i in range(10)
            ]

            results = await asyncio.gather(*queries)

            assert len(results) == 10
            assert all(r.rowcount == 1 for r in results)

    async def test_metadata_in_results(self, redis_client, connection_config, mock_redis_client):
        """Test that query results include proper metadata"""
        mock_redis_client.get = AsyncMock(return_value="value")

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await redis_client.connect(connection_config)

            query = {'command': 'get', 'key': 'test'}
            result = await redis_client.execute_query(json.dumps(query))

            assert 'metadata' in result.__dict__
            assert result.metadata['command'] == 'get'
            assert result.metadata['database'] == '0'
