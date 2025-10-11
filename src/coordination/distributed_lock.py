"""
Distributed Locking with Redis

Provides distributed locking mechanisms using Redis to coordinate
access to shared resources across multiple instances.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Optional
from uuid import uuid4


logger = logging.getLogger(__name__)


@dataclass
class LockInfo:
    """Information about an acquired lock"""
    lock_name: str
    lock_id: str
    acquired_at: float
    ttl: int
    owner: str


class DistributedLock:
    """
    Redis-based distributed lock using SET NX with automatic expiration.

    Implements the Redlock algorithm for reliable distributed locking.
    """

    def __init__(
        self,
        redis_client: any,
        lock_name: str,
        ttl: int = 30,
        retry_delay: float = 0.1,
        retry_count: int = 10
    ):
        """
        Initialize distributed lock

        Args:
            redis_client: Redis client instance
            lock_name: Name of the lock
            ttl: Time to live in seconds
            retry_delay: Delay between retries
            retry_count: Maximum retry attempts
        """
        self.redis = redis_client
        self.lock_name = f"lock:{lock_name}"
        self.ttl = ttl
        self.retry_delay = retry_delay
        self.retry_count = retry_count
        self.lock_id = str(uuid4())
        self.is_locked = False
        self.acquired_at: Optional[float] = None

        logger.debug(f"Initialized distributed lock: {lock_name}")

    async def acquire(self, blocking: bool = True) -> bool:
        """
        Acquire the lock

        Args:
            blocking: If True, retry until lock is acquired or max retries reached

        Returns:
            True if lock was acquired, False otherwise
        """
        attempts = 0

        while attempts < self.retry_count or not blocking:
            try:
                # Try to set the lock with NX (only if not exists) and EX (expiration)
                result = await self.redis.set(
                    self.lock_name,
                    self.lock_id,
                    nx=True,
                    ex=self.ttl
                )

                if result:
                    self.is_locked = True
                    self.acquired_at = time.time()
                    logger.info(
                        f"Acquired lock '{self.lock_name}' "
                        f"(id={self.lock_id[:8]}..., ttl={self.ttl}s)"
                    )
                    return True

                if not blocking:
                    return False

                # Lock is held by someone else, wait and retry
                attempts += 1
                logger.debug(
                    f"Lock '{self.lock_name}' busy, retry {attempts}/{self.retry_count}"
                )
                await asyncio.sleep(self.retry_delay)

            except Exception as e:
                logger.error(f"Error acquiring lock: {e}")
                return False

        logger.warning(
            f"Failed to acquire lock '{self.lock_name}' after {self.retry_count} attempts"
        )
        return False

    async def release(self) -> bool:
        """
        Release the lock

        Returns:
            True if lock was released, False otherwise
        """
        if not self.is_locked:
            logger.warning(f"Attempting to release non-acquired lock '{self.lock_name}'")
            return False

        try:
            # Lua script to atomically check and delete the lock only if we own it
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """

            result = await self.redis.eval(lua_script, 1, self.lock_name, self.lock_id)

            if result == 1:
                self.is_locked = False
                duration = time.time() - self.acquired_at if self.acquired_at else 0
                logger.info(
                    f"Released lock '{self.lock_name}' "
                    f"(held for {duration:.2f}s)"
                )
                return True
            else:
                logger.warning(
                    f"Lock '{self.lock_name}' was not owned by this instance "
                    f"(id={self.lock_id[:8]}...)"
                )
                return False

        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
            return False

    async def extend(self, additional_ttl: int) -> bool:
        """
        Extend lock TTL

        Args:
            additional_ttl: Additional seconds to extend

        Returns:
            True if extended successfully
        """
        if not self.is_locked:
            return False

        try:
            # Lua script to extend TTL only if we own the lock
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """

            result = await self.redis.eval(
                lua_script,
                1,
                self.lock_name,
                self.lock_id,
                additional_ttl
            )

            if result == 1:
                logger.debug(f"Extended lock '{self.lock_name}' by {additional_ttl}s")
                return True
            else:
                logger.warning(f"Failed to extend lock '{self.lock_name}'")
                return False

        except Exception as e:
            logger.error(f"Error extending lock: {e}")
            return False

    async def is_locked_by_me(self) -> bool:
        """Check if lock is held by this instance"""
        try:
            value = await self.redis.get(self.lock_name)
            return value == self.lock_id if value else False
        except Exception as e:
            logger.error(f"Error checking lock ownership: {e}")
            return False

    async def get_lock_info(self) -> Optional[LockInfo]:
        """Get information about the current lock"""
        try:
            value = await self.redis.get(self.lock_name)
            if not value:
                return None

            ttl = await self.redis.ttl(self.lock_name)

            return LockInfo(
                lock_name=self.lock_name,
                lock_id=value,
                acquired_at=self.acquired_at or 0,
                ttl=ttl,
                owner="self" if value == self.lock_id else "other"
            )

        except Exception as e:
            logger.error(f"Error getting lock info: {e}")
            return None

    @asynccontextmanager
    async def __call__(self, blocking: bool = True) -> None:  # type: ignore
        """Context manager support for async with lock() syntax."""
        acquired = await self.acquire(blocking=blocking)
        if not acquired:
            raise RuntimeError(f"Failed to acquire lock '{self.lock_name}'")

        try:
            yield self
        finally:
            await self.release()


class LockManager:
    """Manager for multiple distributed locks with automatic cleanup."""

    def __init__(self, redis_client: Any) -> None:
        """
        Initialize lock manager

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.locks: dict[str, DistributedLock] = {}
        logger.info("Initialized distributed lock manager")

    def get_lock(
        self,
        lock_name: str,
        ttl: int = 30,
        retry_delay: float = 0.1,
        retry_count: int = 10
    ) -> DistributedLock:
        """
        Get or create a distributed lock

        Args:
            lock_name: Name of the lock
            ttl: Time to live in seconds
            retry_delay: Delay between retries
            retry_count: Maximum retry attempts

        Returns:
            DistributedLock instance
        """
        if lock_name not in self.locks:
            self.locks[lock_name] = DistributedLock(
                redis_client=self.redis,
                lock_name=lock_name,
                ttl=ttl,
                retry_delay=retry_delay,
                retry_count=retry_count
            )

        return self.locks[lock_name]

    @asynccontextmanager
    async def lock(
        self,
        lock_name: str,
        ttl: int = 30,
        blocking: bool = True
    ):
        """
        Acquire lock using context manager

        Example:
            async with lock_manager.lock("my_resource"):
                # Critical section
                pass
        """
        lock = self.get_lock(lock_name, ttl=ttl)

        async with lock(blocking=blocking):
            yield lock

    async def release_all(self) -> int:
        """
        Release all locks held by this manager

        Returns:
            Number of locks released
        """
        released = 0
        for lock in self.locks.values():
            if lock.is_locked:
                if await lock.release():
                    released += 1

        logger.info(f"Released {released} locks")
        return released

    async def get_all_locks_info(self) -> dict[str, Optional[LockInfo]]:
        """Get information about all managed locks"""
        info = {}
        for name, lock in self.locks.items():
            info[name] = await lock.get_lock_info()
        return info

    async def cleanup_expired_locks(self, prefix: str = "lock:") -> int:
        """
        Clean up expired locks

        Args:
            prefix: Lock key prefix

        Returns:
            Number of locks cleaned up
        """
        try:
            # Scan for all lock keys
            cursor = 0
            cleaned = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor,
                    match=f"{prefix}*",
                    count=100
                )

                for key in keys:
                    ttl = await self.redis.ttl(key)
                    if ttl == -1:  # No expiration set
                        await self.redis.delete(key)
                        cleaned += 1
                        logger.debug(f"Cleaned up expired lock: {key}")

                if cursor == 0:
                    break

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired locks")

            return cleaned

        except Exception as e:
            logger.error(f"Error cleaning up locks: {e}")
            return 0
