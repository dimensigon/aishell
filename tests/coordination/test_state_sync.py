"""
Comprehensive tests for state synchronization

Tests cross-instance state sync, race conditions, version-based conflict resolution,
and distributed coordination.
"""

import asyncio
import pytest
import json
import time
from unittest.mock import AsyncMock, Mock, MagicMock
from src.coordination.state_sync import (
    StateSync,
    StateSyncManager,
    StateUpdate,
    SyncStrategy
)


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = AsyncMock()
    redis.hset = AsyncMock()
    redis.hget = AsyncMock()
    redis.hdel = AsyncMock()
    redis.hgetall = AsyncMock(return_value={})
    redis.hincrby = AsyncMock(return_value=1)
    redis.publish = AsyncMock()
    redis.expire = AsyncMock()
    
    # Mock pubsub
    pubsub = AsyncMock()
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.close = AsyncMock()
    pubsub.get_message = AsyncMock(return_value=None)
    redis.pubsub = Mock(return_value=pubsub)
    
    return redis


class TestStateSyncBasics:
    """Test basic state synchronization."""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_redis):
        """Test state sync initialization."""
        sync = StateSync(mock_redis, namespace="test")

        assert sync.namespace == "test"
        assert sync.instance_id is not None
        assert sync.state_key == "test:state"
        assert sync.version_key == "test:versions"

    @pytest.mark.asyncio
    async def test_start_stop(self, mock_redis):
        """Test starting and stopping sync."""
        sync = StateSync(mock_redis)

        await sync.start()
        assert sync.listening is True

        await sync.stop()
        assert sync.listening is False


class TestStateOperations:
    """Test state set/get operations."""

    @pytest.mark.asyncio
    async def test_set_state(self, mock_redis):
        """Test setting state value."""
        mock_redis.hget.return_value = None  # No previous version
        sync = StateSync(mock_redis)

        result = await sync.set("key1", "value1")

        assert result is True
        mock_redis.hset.assert_called()
        mock_redis.publish.assert_called()

    @pytest.mark.asyncio
    async def test_get_state(self, mock_redis):
        """Test getting state value."""
        mock_redis.hget.return_value = json.dumps("value1")
        sync = StateSync(mock_redis)

        value = await sync.get("key1")

        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_with_default(self, mock_redis):
        """Test getting non-existent key with default."""
        mock_redis.hget.return_value = None
        sync = StateSync(mock_redis)

        value = await sync.get("non_existent", default="default_value")

        assert value == "default_value"


class TestVersioning:
    """Test version-based conflict resolution."""

    @pytest.mark.asyncio
    async def test_version_increments(self, mock_redis):
        """Test version increments on update."""
        mock_redis.hget.side_effect = [None, b"1", b"2"]
        sync = StateSync(mock_redis)

        await sync.set("key1", "value1")
        await sync.set("key1", "value2")
        await sync.set("key1", "value3")

        # Should increment versions
        assert mock_redis.hset.call_count >= 3

    @pytest.mark.asyncio
    async def test_conflict_resolution(self, mock_redis):
        """Test version-based conflict resolution."""
        sync = StateSync(mock_redis)
        sync.local_versions["key1"] = 5

        # Simulate receiving update with lower version
        update = StateUpdate(
            update_id="update_1",
            instance_id="other_instance",
            key="key1",
            value="old_value",
            timestamp=time.time(),
            version=3
        )

        await sync._handle_update(update)

        # Should ignore outdated update
        assert sync.local_state.get("key1") != "old_value"


class TestPubSubCommunication:
    """Test pub/sub communication between instances."""

    @pytest.mark.asyncio
    async def test_publish_update(self, mock_redis):
        """Test publishing state update."""
        mock_redis.hget.return_value = None
        sync = StateSync(mock_redis)

        await sync.set("key1", "value1")

        # Should publish update
        mock_redis.publish.assert_called()
        call_args = mock_redis.publish.call_args[0]
        assert call_args[0] == sync.channel

    @pytest.mark.asyncio
    async def test_receive_update(self, mock_redis):
        """Test receiving update from another instance."""
        sync = StateSync(mock_redis)
        sync.instance_id = "instance_1"

        update = StateUpdate(
            update_id="update_1",
            instance_id="instance_2",  # Different instance
            key="key1",
            value="value1",
            timestamp=time.time(),
            version=1
        )

        await sync._handle_update(update)

        assert sync.local_state.get("key1") == "value1"


class TestAtomicOperations:
    """Test atomic operations."""

    @pytest.mark.asyncio
    async def test_increment(self, mock_redis):
        """Test atomic increment."""
        mock_redis.hincrby.side_effect = [1, 2, 3]
        sync = StateSync(mock_redis)

        result1 = await sync.increment("counter", 1)
        result2 = await sync.increment("counter", 1)
        result3 = await sync.increment("counter", 1)

        assert result1 == 1
        assert result2 == 2
        assert result3 == 3

    @pytest.mark.asyncio
    async def test_increment_with_amount(self, mock_redis):
        """Test increment with custom amount."""
        mock_redis.hincrby.return_value = 10
        sync = StateSync(mock_redis)

        result = await sync.increment("counter", 10)

        assert result == 10
        mock_redis.hincrby.assert_called()


class TestCaching:
    """Test local caching."""

    @pytest.mark.asyncio
    async def test_cache_on_set(self, mock_redis):
        """Test local cache updated on set."""
        mock_redis.hget.return_value = None
        sync = StateSync(mock_redis)

        await sync.set("key1", "value1")

        assert sync.local_state["key1"] == "value1"

    @pytest.mark.asyncio
    async def test_get_from_cache(self, mock_redis):
        """Test getting from cache."""
        sync = StateSync(mock_redis)
        sync.local_state["key1"] = "cached_value"

        value = await sync.get("key1", use_cache=True)

        assert value == "cached_value"
        # Should not call Redis
        mock_redis.hget.assert_not_called()


class TestStateSyncManager:
    """Test state sync manager."""

    @pytest.mark.asyncio
    async def test_get_sync_instance(self, mock_redis):
        """Test getting sync instance."""
        manager = StateSyncManager(mock_redis)

        sync = await manager.get_sync("namespace1", auto_start=False)

        assert sync.namespace == "namespace1"

    @pytest.mark.asyncio
    async def test_multiple_namespaces(self, mock_redis):
        """Test managing multiple namespaces."""
        manager = StateSyncManager(mock_redis)

        sync1 = await manager.get_sync("ns1", auto_start=False)
        sync2 = await manager.get_sync("ns2", auto_start=False)

        assert sync1.namespace == "ns1"
        assert sync2.namespace == "ns2"
        assert sync1 != sync2

    @pytest.mark.asyncio
    async def test_stop_all(self, mock_redis):
        """Test stopping all sync instances."""
        manager = StateSyncManager(mock_redis)

        await manager.get_sync("ns1", auto_start=False)
        await manager.get_sync("ns2", auto_start=False)

        await manager.stop_all()

        # All should be stopped
        for sync in manager.instances.values():
            assert sync.listening is False


class TestEventHandlers:
    """Test event handlers."""

    @pytest.mark.asyncio
    async def test_register_handler(self, mock_redis):
        """Test registering update handler."""
        sync = StateSync(mock_redis)
        handler_called = []

        def handler(update):
            handler_called.append(update)

        sync.on_update(handler)

        assert len(sync.update_handlers) == 1

    @pytest.mark.asyncio
    async def test_handler_called_on_update(self, mock_redis):
        """Test handler called when update received."""
        sync = StateSync(mock_redis)
        updates_received = []

        def handler(update):
            updates_received.append(update.key)

        sync.on_update(handler)

        update = StateUpdate(
            update_id="update_1",
            instance_id="other_instance",
            key="test_key",
            value="test_value",
            timestamp=time.time(),
            version=1
        )

        await sync._handle_update(update)

        assert "test_key" in updates_received


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_delete_state(self, mock_redis):
        """Test deleting state."""
        sync = StateSync(mock_redis)
        sync.local_state["key1"] = "value1"

        result = await sync.delete("key1")

        assert result is True
        assert "key1" not in sync.local_state
        mock_redis.hdel.assert_called()

    @pytest.mark.asyncio
    async def test_get_all_state(self, mock_redis):
        """Test getting all state."""
        mock_redis.hgetall.return_value = {
            b"key1": json.dumps("value1").encode(),
            b"key2": json.dumps("value2").encode()
        }
        sync = StateSync(mock_redis)

        all_state = await sync.get_all(use_cache=False)

        assert all_state["key1"] == "value1"
        assert all_state["key2"] == "value2"

    @pytest.mark.asyncio
    async def test_ttl_on_set(self, mock_redis):
        """Test TTL set when specified."""
        mock_redis.hget.return_value = None
        sync = StateSync(mock_redis, ttl=3600)

        await sync.set("key1", "value1")

        # Should set expiration
        mock_redis.expire.assert_called()
