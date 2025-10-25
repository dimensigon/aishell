"""
Tests for Redis MCP Client

Covers caching, pub/sub, and session management.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from src.mcp_clients.redis_client import RedisClient
from src.mcp_clients.base import ConnectionConfig, MCPClientError, ConnectionState


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
def mock_redis_client():
    """Create mock Redis client"""
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()
    return mock_client


@pytest.mark.asyncio
class TestRedisClient:
    """Test Redis client functionality"""

    async def test_connection(self, connection_config, mock_redis_client):
        """Test Redis connection"""
        client = RedisClient()

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            result = await client.connect(connection_config)

            assert result is True
            assert client.state == ConnectionState.CONNECTED
            assert client.is_connected
            mock_redis_client.ping.assert_called_once()

    async def test_connection_failure(self, connection_config):
        """Test Redis connection failure"""
        client = RedisClient()

        with patch('src.mcp_clients.redis_client.aioredis.Redis') as mock_class:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(side_effect=Exception("Connection refused"))
            mock_class.return_value = mock_client

            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(connection_config)

            assert "CONNECTION_FAILED" in str(exc_info.value.error_code)

    async def test_disconnect(self, connection_config, mock_redis_client):
        """Test Redis disconnection"""
        client = RedisClient()

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)
            result = await client.disconnect()

            assert result is True
            mock_redis_client.close.assert_called()

    async def test_get_operation(self, connection_config, mock_redis_client):
        """Test GET operation"""
        client = RedisClient()
        mock_redis_client.get = AsyncMock(return_value="test_value")

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            query = {'command': 'get', 'key': 'test_key'}
            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 1
            assert result.rows[0][1] == "test_value"

    async def test_set_operation(self, connection_config, mock_redis_client):
        """Test SET operation"""
        client = RedisClient()
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            query = {'command': 'set', 'key': 'test_key', 'value': 'test_value', 'ex': 3600}
            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 1
            mock_redis_client.set.assert_called_once()

    async def test_delete_operation(self, connection_config, mock_redis_client):
        """Test DELETE operation"""
        client = RedisClient()
        mock_redis_client.delete = AsyncMock(return_value=2)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            query = {'command': 'delete', 'keys': ['key1', 'key2']}
            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 2

    async def test_hset_operation(self, connection_config, mock_redis_client):
        """Test HSET operation"""
        client = RedisClient()
        mock_redis_client.hset = AsyncMock(return_value=1)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            query = {'command': 'hset', 'key': 'user:1', 'field': 'name', 'value': 'Alice'}
            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 1

    async def test_hgetall_operation(self, connection_config, mock_redis_client):
        """Test HGETALL operation"""
        client = RedisClient()
        mock_redis_client.hgetall = AsyncMock(return_value={'name': 'Alice', 'age': '30'})

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            query = {'command': 'hgetall', 'key': 'user:1'}
            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 2

    async def test_lpush_operation(self, connection_config, mock_redis_client):
        """Test LPUSH operation"""
        client = RedisClient()
        mock_redis_client.lpush = AsyncMock(return_value=3)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            query = {'command': 'lpush', 'key': 'queue', 'values': ['item1', 'item2']}
            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 1

    async def test_lrange_operation(self, connection_config, mock_redis_client):
        """Test LRANGE operation"""
        client = RedisClient()
        mock_redis_client.lrange = AsyncMock(return_value=['item1', 'item2', 'item3'])

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            query = {'command': 'lrange', 'key': 'queue', 'start': 0, 'stop': -1}
            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 3

    async def test_zadd_operation(self, connection_config, mock_redis_client):
        """Test ZADD operation"""
        client = RedisClient()
        mock_redis_client.zadd = AsyncMock(return_value=2)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            query = {'command': 'zadd', 'key': 'leaderboard', 'mapping': {'player1': 100, 'player2': 200}}
            result = await client.execute_query(str(query).replace("'", '"').replace('": "', '": '))

            assert result.rowcount == 2

    async def test_cache_set(self, connection_config, mock_redis_client):
        """Test cache_set high-level method"""
        client = RedisClient()
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            result = await client.cache_set('user:1', {'name': 'Alice', 'age': 30}, ttl=3600)

            assert result is True
            mock_redis_client.set.assert_called_once()

    async def test_cache_get(self, connection_config, mock_redis_client):
        """Test cache_get high-level method"""
        client = RedisClient()
        mock_redis_client.get = AsyncMock(return_value='{"name": "Alice", "age": 30}')

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            result = await client.cache_get('user:1')

            assert result == {'name': 'Alice', 'age': 30}

    async def test_cache_delete(self, connection_config, mock_redis_client):
        """Test cache_delete high-level method"""
        client = RedisClient()
        mock_redis_client.delete = AsyncMock(return_value=2)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            result = await client.cache_delete('key1', 'key2')

            assert result == 2

    async def test_session_create(self, connection_config, mock_redis_client):
        """Test session creation"""
        client = RedisClient()
        mock_redis_client.set = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            result = await client.session_create('session123', {'user_id': 1, 'username': 'alice'})

            assert result is True

    async def test_session_get(self, connection_config, mock_redis_client):
        """Test session retrieval"""
        client = RedisClient()
        mock_redis_client.get = AsyncMock(return_value='{"user_id": 1, "username": "alice"}')

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            result = await client.session_get('session123')

            assert result['username'] == 'alice'

    async def test_session_delete(self, connection_config, mock_redis_client):
        """Test session deletion"""
        client = RedisClient()
        mock_redis_client.delete = AsyncMock(return_value=1)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            result = await client.session_delete('session123')

            assert result is True

    async def test_session_extend(self, connection_config, mock_redis_client):
        """Test session TTL extension"""
        client = RedisClient()
        mock_redis_client.expire = AsyncMock(return_value=True)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            result = await client.session_extend('session123', ttl=7200)

            assert result is True

    async def test_publish(self, connection_config, mock_redis_client):
        """Test pub/sub publish"""
        client = RedisClient()
        mock_redis_client.publish = AsyncMock(return_value=5)

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            result = await client.publish('notifications', 'Test message')

            assert result == 5

    async def test_invalid_command(self, connection_config, mock_redis_client):
        """Test invalid command"""
        client = RedisClient()

        with patch('src.mcp_clients.redis_client.aioredis.Redis', return_value=mock_redis_client):
            await client.connect(connection_config)

            query = {'command': 'invalid_cmd', 'key': 'test'}

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_query(str(query).replace("'", '"'))

            assert "Unsupported command" in str(exc_info.value)
