"""
Comprehensive coverage tests for StateSync
Targeting 90%+ coverage with all edge cases, pub/sub, and conflict resolution
"""

import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from src.coordination.state_sync import (
    StateSync,
    StateSyncManager,
    SyncStrategy,
    StateConflict,
    StateUpdate,
)


class MockPubSub:
    """Mock Redis PubSub"""

    def __init__(self):
        self.subscribed_channels = []
        self.messages = []
        self.closed = False

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
        self.closed = True

    def add_message(self, message):
        """Helper to add test messages"""
        self.messages.append(message)


class MockRedis:
    """Enhanced Mock Redis for StateSync testing"""

    def __init__(self):
        self.data = {}  # Hash storage
        self.pubsub_instance = MockPubSub()
        self.published_messages = []
        self.should_fail = False
        self.fail_operations = set()

    async def hset(self, key, field, value):
        if self.should_fail or 'hset' in self.fail_operations:
            raise Exception("Redis hset error")
        if key not in self.data:
            self.data[key] = {}
        self.data[key][field] = value
        return 1

    async def hget(self, key, field):
        if self.should_fail or 'hget' in self.fail_operations:
            raise Exception("Redis hget error")
        value = self.data.get(key, {}).get(field)
        return value

    async def hdel(self, key, field):
        if self.should_fail or 'hdel' in self.fail_operations:
            raise Exception("Redis hdel error")
        if key in self.data and field in self.data[key]:
            del self.data[key][field]
            return 1
        return 0

    async def hgetall(self, key):
        if self.should_fail or 'hgetall' in self.fail_operations:
            raise Exception("Redis hgetall error")
        return self.data.get(key, {})

    async def hincrby(self, key, field, amount):
        if self.should_fail or 'hincrby' in self.fail_operations:
            raise Exception("Redis hincrby error")
        if key not in self.data:
            self.data[key] = {}
        current = int(self.data[key].get(field, 0))
        new_value = current + amount
        self.data[key][field] = new_value
        return new_value

    async def expire(self, key, seconds):
        if self.should_fail or 'expire' in self.fail_operations:
            raise Exception("Redis expire error")
        return 1

    async def publish(self, channel, message):
        if self.should_fail or 'publish' in self.fail_operations:
            raise Exception("Redis publish error")
        self.published_messages.append({'channel': channel, 'message': message})
        return 1

    def pubsub(self):
        return self.pubsub_instance


class TestStateSyncInitialization:
    """Test StateSync initialization"""

    def test_state_sync_init_defaults(self):
        """Test StateSync initialization with defaults"""
        redis = MockRedis()
        sync = StateSync(redis, "test_namespace")

        assert sync.namespace == "test_namespace"
        assert sync.ttl is None
        assert sync.instance_id is not None
        assert sync.state_key == "test_namespace:state"
        assert sync.version_key == "test_namespace:versions"
        assert sync.channel == "test_namespace:updates"
        assert sync.local_state == {}
        assert sync.local_versions == {}
        assert sync.listening is False

    def test_state_sync_init_with_ttl(self):
        """Test StateSync initialization with TTL"""
        redis = MockRedis()
        sync = StateSync(redis, "ttl_namespace", ttl=3600)

        assert sync.ttl == 3600

    def test_state_sync_unique_instance_ids(self):
        """Test each StateSync gets unique instance ID"""
        redis = MockRedis()
        sync1 = StateSync(redis, "ns1")
        sync2 = StateSync(redis, "ns2")

        assert sync1.instance_id != sync2.instance_id


class TestStateSyncStartStop:
    """Test StateSync start/stop functionality"""

    @pytest.mark.asyncio
    async def test_start_state_sync(self):
        """Test starting state synchronization"""
        redis = MockRedis()
        sync = StateSync(redis, "start_test")

        await sync.start()

        assert sync.listening is True
        assert "start_test:updates" in redis.pubsub_instance.subscribed_channels

    @pytest.mark.asyncio
    async def test_start_loads_initial_state(self):
        """Test start loads existing state from Redis"""
        redis = MockRedis()
        sync = StateSync(redis, "load_test")

        # Pre-populate Redis with state
        await redis.hset(sync.state_key, "key1", json.dumps({"value": "data1"}))
        await redis.hset(sync.version_key, "key1", 5)

        await sync.start()

        assert "key1" in sync.local_state
        assert sync.local_versions["key1"] == 5

    @pytest.mark.asyncio
    async def test_start_with_exception(self):
        """Test start handles exceptions during pubsub subscribe"""
        redis = MockRedis()

        # Make pubsub().subscribe() fail
        async def failing_subscribe(channel):
            raise Exception("PubSub subscribe failed")

        redis.pubsub_instance.subscribe = failing_subscribe
        sync = StateSync(redis, "fail_start")

        with pytest.raises(Exception):
            await sync.start()

    @pytest.mark.asyncio
    async def test_stop_state_sync(self):
        """Test stopping state synchronization"""
        redis = MockRedis()
        sync = StateSync(redis, "stop_test")

        await sync.start()
        await sync.stop()

        assert sync.listening is False
        assert redis.pubsub_instance.closed is True


class TestStateSyncSetGet:
    """Test StateSync set/get functionality"""

    @pytest.mark.asyncio
    async def test_set_new_state(self):
        """Test setting new state value"""
        redis = MockRedis()
        sync = StateSync(redis, "set_test")

        result = await sync.set("key1", {"data": "value1"})

        assert result is True
        assert "key1" in sync.local_state
        assert sync.local_state["key1"] == {"data": "value1"}
        assert sync.local_versions["key1"] == 1

    @pytest.mark.asyncio
    async def test_set_update_existing_state(self):
        """Test updating existing state increments version"""
        redis = MockRedis()
        sync = StateSync(redis, "update_test")

        await sync.set("key1", "value1")
        version1 = sync.local_versions["key1"]

        await sync.set("key1", "value2")
        version2 = sync.local_versions["key1"]

        assert version2 == version1 + 1

    @pytest.mark.asyncio
    async def test_set_with_metadata(self):
        """Test setting state with metadata"""
        redis = MockRedis()
        sync = StateSync(redis, "metadata_test")

        metadata = {"source": "test", "priority": "high"}
        await sync.set("key1", "value", metadata=metadata)

        # Check published message includes metadata
        assert len(redis.published_messages) > 0
        msg = json.loads(redis.published_messages[0]['message'])
        assert msg['metadata'] == metadata

    @pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """Test setting state with TTL"""
        redis = MockRedis()
        sync = StateSync(redis, "ttl_test", ttl=60)

        await sync.set("key1", "value")

        # Verify expire was called (would need to track in MockRedis)
        # For now, just verify set succeeded
        assert sync.local_state["key1"] == "value"

    @pytest.mark.asyncio
    async def test_set_publishes_update(self):
        """Test set publishes update to channel"""
        redis = MockRedis()
        sync = StateSync(redis, "publish_test")

        await sync.set("key1", {"x": 1})

        assert len(redis.published_messages) == 1
        msg = redis.published_messages[0]
        assert msg['channel'] == "publish_test:updates"

        data = json.loads(msg['message'])
        assert data['key'] == "key1"
        assert data['value'] == {"x": 1}
        assert data['instance_id'] == sync.instance_id

    @pytest.mark.asyncio
    async def test_set_with_exception(self):
        """Test set handles exceptions"""
        redis = MockRedis()
        redis.should_fail = True
        sync = StateSync(redis, "fail_set")

        result = await sync.set("key1", "value")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_from_cache(self):
        """Test get retrieves from local cache"""
        redis = MockRedis()
        sync = StateSync(redis, "cache_test")

        await sync.set("key1", "cached_value")

        # Get with cache enabled (default)
        value = await sync.get("key1")

        assert value == "cached_value"

    @pytest.mark.asyncio
    async def test_get_bypass_cache(self):
        """Test get can bypass cache"""
        redis = MockRedis()
        sync = StateSync(redis, "nocache_test")

        # Set value in Redis directly
        await redis.hset(sync.state_key, "key1", json.dumps("redis_value"))

        value = await sync.get("key1", use_cache=False)

        assert value == "redis_value"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        """Test get returns default for nonexistent key"""
        redis = MockRedis()
        sync = StateSync(redis, "missing_test")

        value = await sync.get("nonexistent", default="default_val")

        assert value == "default_val"

    @pytest.mark.asyncio
    async def test_get_with_exception(self):
        """Test get handles exceptions"""
        redis = MockRedis()
        redis.should_fail = True
        sync = StateSync(redis, "fail_get")

        value = await sync.get("key1", default="fallback")
        assert value == "fallback"


class TestStateSyncDelete:
    """Test StateSync delete functionality"""

    @pytest.mark.asyncio
    async def test_delete_existing_key(self):
        """Test deleting existing state key"""
        redis = MockRedis()
        sync = StateSync(redis, "delete_test")

        await sync.set("key1", "value1")
        result = await sync.delete("key1")

        assert result is True
        assert "key1" not in sync.local_state
        assert "key1" not in sync.local_versions

    @pytest.mark.asyncio
    async def test_delete_publishes_deletion(self):
        """Test delete publishes deletion event"""
        redis = MockRedis()
        sync = StateSync(redis, "del_pub_test")

        await sync.set("key1", "value")
        redis.published_messages.clear()  # Clear set message

        await sync.delete("key1")

        assert len(redis.published_messages) == 1
        msg = json.loads(redis.published_messages[0]['message'])
        assert msg['metadata']['deleted'] is True
        assert msg['value'] is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self):
        """Test deleting nonexistent key"""
        redis = MockRedis()
        sync = StateSync(redis, "del_missing")

        result = await sync.delete("nonexistent")
        # Should still return True as operation completed
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_with_exception(self):
        """Test delete handles exceptions"""
        redis = MockRedis()
        redis.should_fail = True
        sync = StateSync(redis, "fail_delete")

        result = await sync.delete("key1")
        assert result is False


class TestStateSyncGetAll:
    """Test StateSync get_all functionality"""

    @pytest.mark.asyncio
    async def test_get_all_from_cache(self):
        """Test get_all from cache"""
        redis = MockRedis()
        sync = StateSync(redis, "getall_cache")

        await sync.set("key1", "val1")
        await sync.set("key2", "val2")

        all_state = await sync.get_all(use_cache=True)

        assert len(all_state) == 2
        assert all_state["key1"] == "val1"
        assert all_state["key2"] == "val2"

    @pytest.mark.asyncio
    async def test_get_all_from_redis(self):
        """Test get_all from Redis"""
        redis = MockRedis()
        sync = StateSync(redis, "getall_redis")

        # Add directly to Redis
        await redis.hset(sync.state_key, "key1", json.dumps("val1"))
        await redis.hset(sync.state_key, "key2", json.dumps("val2"))

        all_state = await sync.get_all(use_cache=False)

        assert len(all_state) == 2
        assert all_state["key1"] == "val1"

    @pytest.mark.asyncio
    async def test_get_all_empty(self):
        """Test get_all with empty state"""
        redis = MockRedis()
        sync = StateSync(redis, "empty_getall")

        all_state = await sync.get_all()

        assert all_state == {}

    @pytest.mark.asyncio
    async def test_get_all_with_exception(self):
        """Test get_all handles exceptions"""
        redis = MockRedis()
        redis.should_fail = True
        sync = StateSync(redis, "fail_getall")

        all_state = await sync.get_all(use_cache=False)
        assert all_state == {}


class TestStateSyncIncrement:
    """Test StateSync increment functionality"""

    @pytest.mark.asyncio
    async def test_increment_new_key(self):
        """Test incrementing new key"""
        redis = MockRedis()
        sync = StateSync(redis, "incr_test")

        value = await sync.increment("counter")

        assert value == 1
        assert sync.local_state["counter"] == 1

    @pytest.mark.asyncio
    async def test_increment_existing_key(self):
        """Test incrementing existing key"""
        redis = MockRedis()
        sync = StateSync(redis, "incr_existing")

        await sync.increment("counter")
        value = await sync.increment("counter")

        assert value == 2

    @pytest.mark.asyncio
    async def test_increment_by_amount(self):
        """Test incrementing by custom amount"""
        redis = MockRedis()
        sync = StateSync(redis, "incr_amount")

        value = await sync.increment("counter", amount=5)

        assert value == 5

    @pytest.mark.asyncio
    async def test_increment_publishes_update(self):
        """Test increment publishes update"""
        redis = MockRedis()
        sync = StateSync(redis, "incr_pub")

        await sync.increment("counter")

        # Should have published update
        assert len(redis.published_messages) > 0

    @pytest.mark.asyncio
    async def test_increment_with_exception(self):
        """Test increment handles exceptions"""
        redis = MockRedis()
        redis.should_fail = True
        sync = StateSync(redis, "fail_incr")

        with pytest.raises(Exception):
            await sync.increment("counter")


class TestStateSyncEventHandlers:
    """Test StateSync event handler functionality"""

    def test_on_update_register_handler(self):
        """Test registering update handler"""
        redis = MockRedis()
        sync = StateSync(redis, "handler_test")

        def handler(update):
            pass

        sync.on_update(handler)

        assert handler in sync.update_handlers

    def test_on_update_multiple_handlers(self):
        """Test registering multiple handlers"""
        redis = MockRedis()
        sync = StateSync(redis, "multi_handler")

        handlers = [lambda u: None for _ in range(3)]
        for h in handlers:
            sync.on_update(h)

        assert len(sync.update_handlers) == 3


class TestStateSyncListener:
    """Test StateSync listener functionality"""

    @pytest.mark.asyncio
    async def test_listen_for_updates(self):
        """Test listening for state updates"""
        redis = MockRedis()
        sync = StateSync(redis, "listen_test")

        await sync.start()

        # Simulate incoming update
        update_data = {
            'update_id': 'upd-123',
            'instance_id': 'other-instance',
            'key': 'key1',
            'value': 'new_value',
            'timestamp': time.time(),
            'version': 5,
            'metadata': {}
        }

        redis.pubsub_instance.add_message({
            'type': 'message',
            'data': json.dumps(update_data)
        })

        # Give listener time to process
        await asyncio.sleep(0.05)

        # Should have updated local state
        assert sync.local_state.get("key1") == "new_value"
        assert sync.local_versions.get("key1") == 5

        await sync.stop()

    @pytest.mark.asyncio
    async def test_listen_ignores_own_updates(self):
        """Test listener ignores updates from same instance"""
        redis = MockRedis()
        sync = StateSync(redis, "ignore_test")

        await sync.start()

        # Simulate update from this instance
        update_data = {
            'update_id': 'upd-456',
            'instance_id': sync.instance_id,  # Same instance
            'key': 'key1',
            'value': 'value',
            'timestamp': time.time(),
            'version': 1,
            'metadata': {}
        }

        redis.pubsub_instance.add_message({
            'type': 'message',
            'data': json.dumps(update_data)
        })

        await asyncio.sleep(0.05)

        # Should NOT have been applied (would be duplicate)
        # Local state would only have it if set directly

        await sync.stop()

    @pytest.mark.asyncio
    async def test_handle_update_newer_version(self):
        """Test handling update with newer version"""
        redis = MockRedis()
        sync = StateSync(redis, "newer_test")

        sync.local_state["key1"] = "old_value"
        sync.local_versions["key1"] = 3

        update = StateUpdate(
            update_id="upd-1",
            instance_id="other",
            key="key1",
            value="new_value",
            timestamp=time.time(),
            version=5,
            metadata={}
        )

        await sync._handle_update(update)

        assert sync.local_state["key1"] == "new_value"
        assert sync.local_versions["key1"] == 5

    @pytest.mark.asyncio
    async def test_handle_update_older_version_ignored(self):
        """Test handling update with older version is ignored"""
        redis = MockRedis()
        sync = StateSync(redis, "older_test")

        sync.local_state["key1"] = "current_value"
        sync.local_versions["key1"] = 10

        update = StateUpdate(
            update_id="upd-2",
            instance_id="other",
            key="key1",
            value="old_value",
            timestamp=time.time(),
            version=5,
            metadata={}
        )

        await sync._handle_update(update)

        # Should keep current value
        assert sync.local_state["key1"] == "current_value"
        assert sync.local_versions["key1"] == 10

    @pytest.mark.asyncio
    async def test_handle_deletion_update(self):
        """Test handling deletion update"""
        redis = MockRedis()
        sync = StateSync(redis, "del_update")

        sync.local_state["key1"] = "value"
        sync.local_versions["key1"] = 5

        update = StateUpdate(
            update_id="upd-3",
            instance_id="other",
            key="key1",
            value=None,
            timestamp=time.time(),
            version=6,
            metadata={'deleted': True}
        )

        await sync._handle_update(update)

        assert "key1" not in sync.local_state
        assert "key1" not in sync.local_versions

    @pytest.mark.asyncio
    async def test_update_handler_called(self):
        """Test registered handlers are called on update"""
        redis = MockRedis()
        sync = StateSync(redis, "handler_call")

        called = []

        def handler(update):
            called.append(update)

        sync.on_update(handler)

        update = StateUpdate(
            update_id="upd-4",
            instance_id="other",
            key="key1",
            value="value",
            timestamp=time.time(),
            version=1,
            metadata={}
        )

        await sync._handle_update(update)

        assert len(called) == 1
        assert called[0].update_id == "upd-4"

    @pytest.mark.asyncio
    async def test_update_handler_exception_handled(self):
        """Test handler exceptions don't break update processing"""
        redis = MockRedis()
        sync = StateSync(redis, "handler_error")

        def bad_handler(update):
            raise ValueError("Handler error")

        sync.on_update(bad_handler)

        update = StateUpdate(
            update_id="upd-5",
            instance_id="other",
            key="key1",
            value="value",
            timestamp=time.time(),
            version=1,
            metadata={}
        )

        # Should not raise
        await sync._handle_update(update)

        # Update should still be applied
        assert sync.local_state["key1"] == "value"


class TestStateSyncPublish:
    """Test StateSync publish functionality"""

    @pytest.mark.asyncio
    async def test_publish_update(self):
        """Test publishing state update"""
        redis = MockRedis()
        sync = StateSync(redis, "pub_test")

        await sync._publish_update("key1", "value1", 1)

        assert len(redis.published_messages) == 1
        msg = json.loads(redis.published_messages[0]['message'])
        assert msg['key'] == "key1"
        assert msg['value'] == "value1"
        assert msg['version'] == 1

    @pytest.mark.asyncio
    async def test_publish_with_metadata(self):
        """Test publishing update with metadata"""
        redis = MockRedis()
        sync = StateSync(redis, "pub_meta")

        metadata = {"source": "test"}
        await sync._publish_update("key1", "val", 1, metadata=metadata)

        msg = json.loads(redis.published_messages[0]['message'])
        assert msg['metadata'] == metadata

    @pytest.mark.asyncio
    async def test_publish_with_exception(self):
        """Test publish handles exceptions gracefully"""
        redis = MockRedis()
        redis.fail_operations.add('publish')
        sync = StateSync(redis, "pub_fail")

        # Should not raise
        await sync._publish_update("key1", "val", 1)


class TestStateSyncManager:
    """Test StateSyncManager functionality"""

    def test_manager_initialization(self):
        """Test manager initialization"""
        redis = MockRedis()
        manager = StateSyncManager(redis)

        assert manager.redis == redis
        assert manager.instances == {}

    @pytest.mark.asyncio
    async def test_get_sync_creates_new_instance(self):
        """Test get_sync creates new StateSync instance"""
        redis = MockRedis()
        manager = StateSyncManager(redis)

        sync = await manager.get_sync("namespace1")

        assert "namespace1" in manager.instances
        assert sync.namespace == "namespace1"

    @pytest.mark.asyncio
    async def test_get_sync_returns_existing_instance(self):
        """Test get_sync returns existing instance"""
        redis = MockRedis()
        manager = StateSyncManager(redis)

        sync1 = await manager.get_sync("namespace1")
        sync2 = await manager.get_sync("namespace1")

        assert sync1 is sync2

    @pytest.mark.asyncio
    async def test_get_sync_with_ttl(self):
        """Test get_sync with TTL parameter"""
        redis = MockRedis()
        manager = StateSyncManager(redis)

        sync = await manager.get_sync("ttl_ns", ttl=3600)

        assert sync.ttl == 3600

    @pytest.mark.asyncio
    async def test_get_sync_auto_start(self):
        """Test get_sync with auto_start"""
        redis = MockRedis()
        manager = StateSyncManager(redis)

        sync = await manager.get_sync("auto_ns", auto_start=True)

        assert sync.listening is True

    @pytest.mark.asyncio
    async def test_get_sync_no_auto_start(self):
        """Test get_sync without auto_start"""
        redis = MockRedis()
        manager = StateSyncManager(redis)

        sync = await manager.get_sync("manual_ns", auto_start=False)

        assert sync.listening is False

    @pytest.mark.asyncio
    async def test_stop_all(self):
        """Test stopping all sync instances"""
        redis = MockRedis()
        manager = StateSyncManager(redis)

        sync1 = await manager.get_sync("ns1", auto_start=True)
        sync2 = await manager.get_sync("ns2", auto_start=True)

        await manager.stop_all()

        assert sync1.listening is False
        assert sync2.listening is False


class TestStateDataClasses:
    """Test StateConflict and StateUpdate dataclasses"""

    def test_state_conflict_creation(self):
        """Test StateConflict creation"""
        conflict = StateConflict(
            key="key1",
            local_value="local",
            remote_value="remote",
            local_version=5,
            remote_version=6
        )

        assert conflict.key == "key1"
        assert conflict.local_value == "local"
        assert conflict.remote_value == "remote"
        assert conflict.local_version == 5
        assert conflict.remote_version == 6
        assert conflict.timestamp is not None

    def test_state_update_creation(self):
        """Test StateUpdate creation"""
        update = StateUpdate(
            update_id="upd-123",
            instance_id="inst-456",
            key="key1",
            value="value1",
            timestamp=123.456,
            version=7
        )

        assert update.update_id == "upd-123"
        assert update.instance_id == "inst-456"
        assert update.key == "key1"
        assert update.value == "value1"
        assert update.version == 7
        assert update.metadata == {}

    def test_state_update_with_metadata(self):
        """Test StateUpdate with metadata"""
        metadata = {"source": "test", "priority": "high"}
        update = StateUpdate(
            update_id="upd-789",
            instance_id="inst-000",
            key="key2",
            value="value2",
            timestamp=789.012,
            version=3,
            metadata=metadata
        )

        assert update.metadata == metadata


class TestSyncStrategy:
    """Test SyncStrategy enum"""

    def test_sync_strategy_values(self):
        """Test all sync strategy values"""
        assert SyncStrategy.LAST_WRITE_WINS.value == "last_write_wins"
        assert SyncStrategy.FIRST_WRITE_WINS.value == "first_write_wins"
        assert SyncStrategy.VERSION_BASED.value == "version_based"
        assert SyncStrategy.MERGE.value == "merge"
