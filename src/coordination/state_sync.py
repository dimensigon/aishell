"""
State Synchronization

Cross-instance state synchronization using Redis pub/sub and shared state.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4


logger = logging.getLogger(__name__)


class SyncStrategy(Enum):
    """State synchronization strategy"""
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    VERSION_BASED = "version_based"
    MERGE = "merge"


@dataclass
class StateConflict:
    """State conflict information"""
    key: str
    local_value: Any
    remote_value: Any
    local_version: int
    remote_version: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class StateUpdate:
    """State update event"""
    update_id: str
    instance_id: str
    key: str
    value: Any
    timestamp: float
    version: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateSync:
    """
    Distributed state synchronization with pub/sub and conflict resolution.

    Features:
    - Automatic state replication
    - Conflict resolution via versioning
    - Event notifications
    - Atomic operations
    """

    def __init__(
        self,
        redis_client: any,
        namespace: str = "state",
        ttl: Optional[int] = None
    ):
        """
        Initialize state synchronization

        Args:
            redis_client: Redis client instance
            namespace: State namespace
            ttl: Optional TTL for state keys
        """
        self.redis = redis_client
        self.namespace = namespace
        self.ttl = ttl
        self.instance_id = str(uuid4())

        # Redis keys
        self.state_key = f"{namespace}:state"
        self.version_key = f"{namespace}:versions"
        self.channel = f"{namespace}:updates"

        # Local state cache
        self.local_state: Dict[str, Any] = {}
        self.local_versions: Dict[str, int] = {}

        # Event handlers
        self.update_handlers: List[Callable[[StateUpdate], None]] = []

        # Pub/sub
        self.pubsub = None
        self.listening = False

        logger.info(
            f"Initialized state sync "
            f"(namespace={namespace}, instance_id={self.instance_id[:8]}...)"
        )

    async def start(self) -> None:
        """Start state synchronization"""
        try:
            # Load initial state
            await self._load_state()

            # Start pub/sub listener
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(self.channel)
            self.listening = True

            # Start listener task
            asyncio.create_task(self._listen_for_updates())

            logger.info("Started state synchronization")

        except Exception as e:
            logger.error(f"Failed to start state sync: {e}")
            raise

    async def stop(self) -> None:
        """Stop state synchronization"""
        self.listening = False

        if self.pubsub:
            await self.pubsub.unsubscribe(self.channel)
            await self.pubsub.close()

        logger.info("Stopped state synchronization")

    async def set(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set state value

        Args:
            key: State key
            value: State value
            metadata: Optional metadata

        Returns:
            True if set successfully
        """
        try:
            # Get current version
            current_version = await self.redis.hget(self.version_key, key)
            new_version = (int(current_version) + 1) if current_version else 1

            # Set state
            value_json = json.dumps(value)
            await self.redis.hset(self.state_key, key, value_json)
            await self.redis.hset(self.version_key, key, new_version)

            if self.ttl:
                await self.redis.expire(f"{self.state_key}:{key}", self.ttl)

            # Update local cache
            self.local_state[key] = value
            self.local_versions[key] = new_version

            # Publish update
            update = StateUpdate(
                update_id=str(uuid4()),
                instance_id=self.instance_id,
                key=key,
                value=value,
                timestamp=time.time(),
                version=new_version,
                metadata=metadata or {}
            )

            await self.redis.publish(
                self.channel,
                json.dumps({
                    'update_id': update.update_id,
                    'instance_id': update.instance_id,
                    'key': update.key,
                    'value': update.value,
                    'timestamp': update.timestamp,
                    'version': update.version,
                    'metadata': update.metadata
                })
            )

            logger.debug(
                f"Set state {key} to version {new_version} "
                f"(instance={self.instance_id[:8]}...)"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to set state {key}: {e}")
            return False

    async def get(
        self,
        key: str,
        default: Any = None,
        use_cache: bool = True
    ) -> Any:
        """
        Get state value

        Args:
            key: State key
            default: Default value if not found
            use_cache: Use local cache if available

        Returns:
            State value or default
        """
        try:
            # Check local cache first
            if use_cache and key in self.local_state:
                return self.local_state[key]

            # Get from Redis
            value_json = await self.redis.hget(self.state_key, key)
            if value_json:
                value = json.loads(value_json)
                self.local_state[key] = value
                return value

            return default

        except Exception as e:
            logger.error(f"Failed to get state {key}: {e}")
            return default

    async def delete(self, key: str) -> bool:
        """Delete state key"""
        try:
            await self.redis.hdel(self.state_key, key)
            await self.redis.hdel(self.version_key, key)

            self.local_state.pop(key, None)
            self.local_versions.pop(key, None)

            # Publish deletion
            update = StateUpdate(
                update_id=str(uuid4()),
                instance_id=self.instance_id,
                key=key,
                value=None,
                timestamp=time.time(),
                version=0,
                metadata={'deleted': True}
            )

            await self.redis.publish(
                self.channel,
                json.dumps({
                    'update_id': update.update_id,
                    'instance_id': update.instance_id,
                    'key': update.key,
                    'value': None,
                    'timestamp': update.timestamp,
                    'version': 0,
                    'metadata': update.metadata
                })
            )

            logger.debug(f"Deleted state key {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete state {key}: {e}")
            return False

    async def get_all(self, use_cache: bool = False) -> Dict[str, Any]:
        """Get all state"""
        if use_cache:
            return self.local_state.copy()

        try:
            all_state = await self.redis.hgetall(self.state_key)
            result = {}

            for key, value_json in all_state.items():
                key = key.decode() if isinstance(key, bytes) else key
                value_json = value_json.decode() if isinstance(value_json, bytes) else value_json
                result[key] = json.loads(value_json)

            self.local_state = result.copy()
            return result

        except Exception as e:
            logger.error(f"Failed to get all state: {e}")
            return {}

    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment value"""
        try:
            # Use Redis HINCRBY for atomic increment
            new_value = await self.redis.hincrby(self.state_key, key, amount)

            # Update version
            version = await self.redis.hincrby(self.version_key, key, 1)

            self.local_state[key] = new_value
            self.local_versions[key] = version

            # Publish update
            await self._publish_update(key, new_value, version)

            return new_value

        except Exception as e:
            logger.error(f"Failed to increment {key}: {e}")
            raise

    def on_update(self, handler: Callable[[StateUpdate], None]) -> None:
        """Register update event handler"""
        self.update_handlers.append(handler)
        logger.debug(f"Registered update handler: {handler.__name__}")

    async def _load_state(self) -> None:
        """Load state from Redis"""
        try:
            self.local_state = await self.get_all(use_cache=False)

            # Load versions
            all_versions = await self.redis.hgetall(self.version_key)
            for key, version in all_versions.items():
                key = key.decode() if isinstance(key, bytes) else key
                version = int(version.decode() if isinstance(version, bytes) else version)
                self.local_versions[key] = version

            logger.debug(f"Loaded {len(self.local_state)} state keys")

        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    async def _listen_for_updates(self) -> None:
        """Listen for state updates via pub/sub"""
        logger.debug("Started listening for state updates")

        try:
            while self.listening:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )

                if message and message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        update = StateUpdate(**data)

                        # Skip updates from this instance
                        if update.instance_id == self.instance_id:
                            continue

                        # Handle update
                        await self._handle_update(update)

                    except Exception as e:
                        logger.error(f"Error processing update: {e}")

                await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            logger.debug("Update listener cancelled")
        except Exception as e:
            logger.error(f"Error in update listener: {e}")

    async def _handle_update(self, update: StateUpdate) -> None:
        """Handle incoming state update"""
        try:
            # Check version for conflict resolution
            local_version = self.local_versions.get(update.key, 0)

            if update.version > local_version:
                # Update is newer, apply it
                if update.metadata.get('deleted'):
                    self.local_state.pop(update.key, None)
                    self.local_versions.pop(update.key, None)
                else:
                    self.local_state[update.key] = update.value
                    self.local_versions[update.key] = update.version

                logger.debug(
                    f"Applied state update for {update.key} "
                    f"(version {local_version} → {update.version})"
                )

                # Notify handlers
                for handler in self.update_handlers:
                    try:
                        handler(update)
                    except Exception as e:
                        logger.error(f"Error in update handler: {e}")

            elif update.version < local_version:
                logger.debug(
                    f"Ignored outdated update for {update.key} "
                    f"(version {update.version} < {local_version})"
                )

        except Exception as e:
            logger.error(f"Error handling update: {e}")

    async def _publish_update(
        self,
        key: str,
        value: Any,
        version: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Publish state update"""
        try:
            update = StateUpdate(
                update_id=str(uuid4()),
                instance_id=self.instance_id,
                key=key,
                value=value,
                timestamp=time.time(),
                version=version,
                metadata=metadata or {}
            )

            await self.redis.publish(
                self.channel,
                json.dumps({
                    'update_id': update.update_id,
                    'instance_id': update.instance_id,
                    'key': update.key,
                    'value': update.value,
                    'timestamp': update.timestamp,
                    'version': update.version,
                    'metadata': update.metadata
                })
            )

        except Exception as e:
            logger.error(f"Failed to publish update: {e}")


class StateSyncManager:
    """Manager for multiple state sync instances"""

    def __init__(self, redis_client: any) -> None:
        """Initialize state sync manager"""
        self.redis = redis_client
        self.instances: Dict[str, StateSync] = {}
        logger.info("Initialized state sync manager")

    async def get_sync(
        self,
        namespace: str,
        ttl: Optional[int] = None,
        auto_start: bool = True
    ) -> StateSync:
        """Get or create state sync instance"""
        if namespace not in self.instances:
            sync = StateSync(self.redis, namespace, ttl)
            self.instances[namespace] = sync

            if auto_start:
                await sync.start()

        return self.instances[namespace]

    async def stop_all(self) -> None:
        """Stop all state sync instances"""
        for sync in self.instances.values():
            await sync.stop()

        logger.info("Stopped all state sync instances")
