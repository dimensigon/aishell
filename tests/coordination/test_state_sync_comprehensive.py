"""
Comprehensive tests for StateSync

Tests cover:
- State synchronization initialization
- State get/set operations
- State deletion
- Version-based conflict resolution
- Pub/sub event handling
- Update notifications
- Atomic operations
- Multiple instances coordination
- Edge cases and error handling
"""

import asyncio
import json
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, call

from src.coordination.state_sync import (
    StateSync, StateSyncManager, StateUpdate, StateConflict, SyncStrategy
)


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    redis = AsyncMock()
    redis.hget = AsyncMock(return_value=None)
    redis.hset = AsyncMock(return_value=1)
    redis.hdel = AsyncMock(return_value=1)
    redis.hgetall = AsyncMock(return_value={})
    redis.publish = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=1)

    # Mock pubsub
    pubsub = AsyncMock()
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.close = AsyncMock()
    pubsub.get_message = AsyncMock(return_value=None)
    redis.pubsub = MagicMock(return_value=pubsub)

    return redis


@pytest.fixture
def state_sync(mock_redis):
    """Create StateSync instance"""
    return StateSync(mock_redis, namespace="test")


@pytest.fixture
async def started_state_sync(mock_redis):
    """Create and start StateSync instance"""
    sync = StateSync(mock_redis, namespace="test")
    await sync.start()
    yield sync
    await sync.stop()


class TestStateSyncInit:
    """Test StateSync initialization"""

    def test_init_default_params(self, mock_redis):
        """Test initialization with default parameters"""
        sync = StateSync(mock_redis)

        assert sync.redis == mock_redis
        assert sync.namespace == "state"
        assert sync.ttl is None
        assert sync.instance_id is not None
        assert sync.local_state == {}
        assert sync.local_versions == {}

    def test_init_custom_params(self, mock_redis):
        """Test initialization with custom parameters"""
        sync = StateSync(mock_redis, namespace="custom", ttl=3600)

        assert sync.namespace == "custom"
        assert sync.ttl == 3600

    def test_redis_keys_generated(self, state_sync):
        """Test Redis keys are properly generated"""
        assert state_sync.state_key == "test:state"
        assert state_sync.version_key == "test:versions"
        assert state_sync.channel == "test:updates"


class TestStateSyncStartStop:
    """Test start and stop operations"""

    @pytest.mark.asyncio
    async def test_start(self, state_sync, mock_redis):
        """Test starting state sync"""
        await state_sync.start()

        assert state_sync.listening is True
        assert state_sync.pubsub is not None
        state_sync.pubsub.subscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self, started_state_sync):
        """Test stopping state sync"""
        await started_state_sync.stop()

        assert started_state_sync.listening is False
        started_state_sync.pubsub.unsubscribe.assert_called_once()
        started_state_sync.pubsub.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_loads_initial_state(self, mock_redis):
        """Test start loads initial state"""
        initial_state = {
            b'key1': b'{"value": "test1"}',
            b'key2': b'{"value": "test2"}'
        }
        mock_redis.hgetall.return_value = initial_state

        sync = StateSync(mock_redis)
        await sync.start()

        assert len(sync.local_state) == 2
        await sync.stop()


class TestStateSyncSet:
    """Test state setting operations"""

    @pytest.mark.asyncio
    async def test_set_simple_value(self, started_state_sync, mock_redis):
        """Test setting simple value"""
        mock_redis.hget.return_value = None  # No previous version

        result = await started_state_sync.set("key1", "value1")

        assert result is True
        assert started_state_sync.local_state["key1"] == "value1"
        assert started_state_sync.local_versions["key1"] == 1
        mock_redis.hset.assert_called()
        mock_redis.publish.assert_called()

    @pytest.mark.asyncio
    async def test_set_with_metadata(self, started_state_sync, mock_redis):
        """Test setting value with metadata"""
        mock_redis.hget.return_value = None

        metadata = {"source": "test", "timestamp": time.time()}
        result = await started_state_sync.set("key1", "value1", metadata)

        assert result is True
        # Check publish was called with metadata
        publish_call = mock_redis.publish.call_args
        assert publish_call is not None

    @pytest.mark.asyncio
    async def test_set_updates_version(self, started_state_sync, mock_redis):
        """Test setting value updates version"""
        # First set
        mock_redis.hget.return_value = None
        await started_state_sync.set("key1", "value1")

        # Second set
        mock_redis.hget.return_value = b"1"
        await started_state_sync.set("key1", "value2")

        assert started_state_sync.local_versions["key1"] == 2

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, mock_redis):
        """Test setting value with TTL"""
        sync = StateSync(mock_redis, ttl=3600)
        await sync.start()

        mock_redis.hget.return_value = None
        await sync.set("key1", "value1")

        mock_redis.expire.assert_called()
        await sync.stop()

    @pytest.mark.asyncio
    async def test_set_complex_value(self, started_state_sync, mock_redis):
        """Test setting complex value (dict/list)"""
        mock_redis.hget.return_value = None

        complex_value = {
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }
        result = await started_state_sync.set("key1", complex_value)

        assert result is True
        assert started_state_sync.local_state["key1"] == complex_value

    @pytest.mark.asyncio
    async def test_set_error_handling(self, started_state_sync, mock_redis):
        """Test set handles Redis errors"""
        mock_redis.hget.side_effect = Exception("Redis error")

        result = await started_state_sync.set("key1", "value1")

        assert result is False


class TestStateSyncGet:
    """Test state getting operations"""

    @pytest.mark.asyncio
    async def test_get_from_cache(self, started_state_sync):
        """Test getting value from local cache"""
        started_state_sync.local_state["key1"] = "value1"

        result = await started_state_sync.get("key1")

        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_from_redis(self, started_state_sync, mock_redis):
        """Test getting value from Redis"""
        mock_redis.hget.return_value = json.dumps("value1")

        result = await started_state_sync.get("key1", use_cache=False)

        assert result == "value1"
        assert started_state_sync.local_state["key1"] == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, started_state_sync, mock_redis):
        """Test getting non-existent key returns default"""
        mock_redis.hget.return_value = None

        result = await started_state_sync.get("nonexistent", default="default")

        assert result == "default"

    @pytest.mark.asyncio
    async def test_get_without_cache(self, started_state_sync, mock_redis):
        """Test getting without using cache"""
        started_state_sync.local_state["key1"] = "cached_value"
        mock_redis.hget.return_value = json.dumps("redis_value")

        result = await started_state_sync.get("key1", use_cache=False)

        assert result == "redis_value"

    @pytest.mark.asyncio
    async def test_get_error_handling(self, started_state_sync, mock_redis):
        """Test get handles errors"""
        mock_redis.hget.side_effect = Exception("Redis error")

        result = await started_state_sync.get("key1", default="default")

        assert result == "default"


class TestStateSyncDelete:
    """Test state deletion"""

    @pytest.mark.asyncio
    async def test_delete_key(self, started_state_sync, mock_redis):
        """Test deleting a key"""
        started_state_sync.local_state["key1"] = "value1"
        started_state_sync.local_versions["key1"] = 1

        result = await started_state_sync.delete("key1")

        assert result is True
        assert "key1" not in started_state_sync.local_state
        assert "key1" not in started_state_sync.local_versions
        mock_redis.hdel.assert_called()
        mock_redis.publish.assert_called()

    @pytest.mark.asyncio
    async def test_delete_publishes_deletion_event(self, started_state_sync, mock_redis):
        """Test deletion publishes event"""
        await started_state_sync.delete("key1")

        publish_call = mock_redis.publish.call_args
        assert publish_call is not None

        # Parse published message
        message = json.loads(publish_call[0][1])
        assert message['metadata']['deleted'] is True

    @pytest.mark.asyncio
    async def test_delete_error_handling(self, started_state_sync, mock_redis):
        """Test delete handles errors"""
        mock_redis.hdel.side_effect = Exception("Redis error")

        result = await started_state_sync.delete("key1")

        assert result is False


class TestStateSyncGetAll:
    """Test getting all state"""

    @pytest.mark.asyncio
    async def test_get_all_from_cache(self, started_state_sync):
        """Test getting all state from cache"""
        started_state_sync.local_state = {"key1": "value1", "key2": "value2"}

        result = await started_state_sync.get_all(use_cache=True)

        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_get_all_from_redis(self, started_state_sync, mock_redis):
        """Test getting all state from Redis"""
        mock_redis.hgetall.return_value = {
            b'key1': b'"value1"',
            b'key2': b'"value2"'
        }

        result = await started_state_sync.get_all(use_cache=False)

        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_get_all_error_handling(self, started_state_sync, mock_redis):
        """Test get_all handles errors"""
        mock_redis.hgetall.side_effect = Exception("Redis error")

        result = await started_state_sync.get_all()

        assert result == {}


class TestStateSyncIncrement:
    """Test atomic increment operations"""

    @pytest.mark.asyncio
    async def test_increment_default(self, started_state_sync, mock_redis):
        """Test increment by default amount"""
        mock_redis.hincrby.return_value = 1

        result = await started_state_sync.increment("counter")

        assert result == 1
        mock_redis.hincrby.assert_called_with(
            started_state_sync.state_key,
            "counter",
            1
        )

    @pytest.mark.asyncio
    async def test_increment_custom_amount(self, started_state_sync, mock_redis):
        """Test increment by custom amount"""
        mock_redis.hincrby.return_value = 10

        result = await started_state_sync.increment("counter", amount=5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_increment_updates_local_cache(self, started_state_sync, mock_redis):
        """Test increment updates local cache"""
        mock_redis.hincrby.return_value = 5
        mock_redis.hincrby.side_effect = None

        await started_state_sync.increment("counter")

        assert started_state_sync.local_state["counter"] == 5

    @pytest.mark.asyncio
    async def test_increment_error_handling(self, started_state_sync, mock_redis):
        """Test increment handles errors"""
        mock_redis.hincrby.side_effect = Exception("Redis error")

        with pytest.raises(Exception):
            await started_state_sync.increment("counter")


class TestStateSyncUpdateHandlers:
    """Test update event handlers"""

    @pytest.mark.asyncio
    async def test_register_update_handler(self, started_state_sync):
        """Test registering update handler"""
        handler_called = []

        def handler(update):
            handler_called.append(update)

        started_state_sync.on_update(handler)

        assert len(started_state_sync.update_handlers) == 1

    @pytest.mark.asyncio
    async def test_update_handler_called(self, started_state_sync):
        """Test update handler is called"""
        updates_received = []

        def handler(update):
            updates_received.append(update)

        started_state_sync.on_update(handler)

        # Simulate update from another instance
        update = StateUpdate(
            update_id="update-1",
            instance_id="other-instance",
            key="key1",
            value="value1",
            timestamp=time.time(),
            version=1
        )

        await started_state_sync._handle_update(update)

        assert len(updates_received) == 1

    @pytest.mark.asyncio
    async def test_multiple_update_handlers(self, started_state_sync):
        """Test multiple update handlers"""
        handler1_called = []
        handler2_called = []

        started_state_sync.on_update(lambda u: handler1_called.append(u))
        started_state_sync.on_update(lambda u: handler2_called.append(u))

        update = StateUpdate(
            update_id="update-1",
            instance_id="other",
            key="key1",
            value="value1",
            timestamp=time.time(),
            version=1
        )

        await started_state_sync._handle_update(update)

        assert len(handler1_called) == 1
        assert len(handler2_called) == 1


class TestStateSyncConflictResolution:
    """Test conflict resolution"""

    @pytest.mark.asyncio
    async def test_newer_version_wins(self, started_state_sync):
        """Test newer version overwrites local state"""
        started_state_sync.local_state["key1"] = "old_value"
        started_state_sync.local_versions["key1"] = 1

        update = StateUpdate(
            update_id="update-1",
            instance_id="other",
            key="key1",
            value="new_value",
            timestamp=time.time(),
            version=2
        )

        await started_state_sync._handle_update(update)

        assert started_state_sync.local_state["key1"] == "new_value"
        assert started_state_sync.local_versions["key1"] == 2

    @pytest.mark.asyncio
    async def test_older_version_ignored(self, started_state_sync):
        """Test older version is ignored"""
        started_state_sync.local_state["key1"] = "current_value"
        started_state_sync.local_versions["key1"] = 5

        update = StateUpdate(
            update_id="update-1",
            instance_id="other",
            key="key1",
            value="old_value",
            timestamp=time.time(),
            version=3
        )

        await started_state_sync._handle_update(update)

        assert started_state_sync.local_state["key1"] == "current_value"
        assert started_state_sync.local_versions["key1"] == 5

    @pytest.mark.asyncio
    async def test_deletion_update(self, started_state_sync):
        """Test handling deletion update"""
        started_state_sync.local_state["key1"] = "value1"
        started_state_sync.local_versions["key1"] = 1

        update = StateUpdate(
            update_id="update-1",
            instance_id="other",
            key="key1",
            value=None,
            timestamp=time.time(),
            version=2,
            metadata={'deleted': True}
        )

        await started_state_sync._handle_update(update)

        assert "key1" not in started_state_sync.local_state
        assert "key1" not in started_state_sync.local_versions


class TestStateSyncManager:
    """Test StateSyncManager"""

    def test_manager_init(self, mock_redis):
        """Test manager initialization"""
        manager = StateSyncManager(mock_redis)

        assert manager.redis == mock_redis
        assert manager.instances == {}

    @pytest.mark.asyncio
    async def test_get_sync_creates_instance(self, mock_redis):
        """Test get_sync creates new instance"""
        manager = StateSyncManager(mock_redis)

        sync = await manager.get_sync("namespace1")

        assert "namespace1" in manager.instances
        assert sync.namespace == "namespace1"
        await sync.stop()

    @pytest.mark.asyncio
    async def test_get_sync_returns_existing(self, mock_redis):
        """Test get_sync returns existing instance"""
        manager = StateSyncManager(mock_redis)

        sync1 = await manager.get_sync("namespace1")
        sync2 = await manager.get_sync("namespace1")

        assert sync1 is sync2
        await manager.stop_all()

    @pytest.mark.asyncio
    async def test_stop_all(self, mock_redis):
        """Test stopping all sync instances"""
        manager = StateSyncManager(mock_redis)

        await manager.get_sync("ns1")
        await manager.get_sync("ns2")
        await manager.get_sync("ns3")

        await manager.stop_all()

        # All should be stopped
        for sync in manager.instances.values():
            assert sync.listening is False


class TestStateSyncEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_concurrent_sets(self, started_state_sync, mock_redis):
        """Test concurrent set operations"""
        mock_redis.hget.return_value = None

        results = await asyncio.gather(*[
            started_state_sync.set(f"key{i}", f"value{i}")
            for i in range(10)
        ])

        assert all(results)
        assert len(started_state_sync.local_state) == 10

    @pytest.mark.asyncio
    async def test_update_from_self_ignored(self, started_state_sync):
        """Test updates from self are ignored"""
        update = StateUpdate(
            update_id="update-1",
            instance_id=started_state_sync.instance_id,
            key="key1",
            value="value1",
            timestamp=time.time(),
            version=1
        )

        # Should not update local state since it's from self
        initial_state = started_state_sync.local_state.copy()
        await started_state_sync._handle_update(update)

        # State should be unchanged
        assert started_state_sync.local_state == initial_state

    @pytest.mark.asyncio
    async def test_unicode_in_state_values(self, started_state_sync, mock_redis):
        """Test handling unicode in state values"""
        mock_redis.hget.return_value = None

        unicode_value = {"message": "Hello 世界 🌍"}
        result = await started_state_sync.set("unicode_key", unicode_value)

        assert result is True
        assert started_state_sync.local_state["unicode_key"] == unicode_value
