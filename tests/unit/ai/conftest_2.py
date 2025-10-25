"""
Pytest fixtures for coordination tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
import json


class MockPubSub:
    """Mock Redis PubSub for testing"""

    def __init__(self):
        self.subscribed_channels = []
        self.messages = []
        self._pubsub_messages = []

    async def subscribe(self, channel):
        self.subscribed_channels.append(channel)

    async def unsubscribe(self, channel):
        if channel in self.subscribed_channels:
            self.subscribed_channels.remove(channel)

    async def get_message(self, ignore_subscribe_messages=False, timeout=1.0):
        if self.messages:
            return self.messages.pop(0)
        await asyncio.sleep(0.01)
        return None

    async def close(self):
        pass


class MockRedisClient:
    """Mock Redis client for testing"""

    def __init__(self):
        self.data = {}  # Hash storage
        self.versions = {}
        self._pubsub = MockPubSub()
        self._pubsub_messages = []

    async def hset(self, key, field, value):
        if key not in self.data:
            self.data[key] = {}
        self.data[key][field] = value
        return 1

    async def hget(self, key, field):
        return self.data.get(key, {}).get(field)

    async def hdel(self, key, field):
        if key in self.data and field in self.data[key]:
            del self.data[key][field]
            return 1
        return 0

    async def hgetall(self, key):
        return self.data.get(key, {})

    async def hincrby(self, key, field, amount):
        if key not in self.data:
            self.data[key] = {}
        current = int(self.data[key].get(field, 0))
        new_value = current + amount
        self.data[key][field] = new_value
        return new_value

    async def expire(self, key, seconds):
        return 1

    async def publish(self, channel, message):
        self._pubsub_messages.append({'channel': channel, 'message': message})
        return 1

    def pubsub(self):
        return self._pubsub

    async def set(self, key, value, nx=False, ex=None):
        if nx and key in self.data:
            return None
        self.data[key] = value
        return True

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, key):
        if key in self.data:
            del self.data[key]
            return 1
        return 0

    async def ttl(self, key):
        return -1

    async def zadd(self, key, mapping):
        if key not in self.data:
            self.data[key] = {}
        self.data[key].update(mapping)
        return len(mapping)

    async def zcard(self, key):
        return len(self.data.get(key, {}))

    async def zrem(self, key, member):
        if key in self.data and member in self.data[key]:
            del self.data[key][member]
            return 1
        return 0


@pytest.fixture
def mock_redis_client():
    """Fixture providing mock Redis client"""
    return MockRedisClient()


@pytest.fixture
async def mock_state_sync(mock_redis_client):
    """Fixture providing mock StateSync instance"""
    from src.coordination.state_sync import StateSync

    sync = StateSync(
        redis_client=mock_redis_client,
        namespace='test',
        ttl=None
    )
    return sync
