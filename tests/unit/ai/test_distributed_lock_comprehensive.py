"""
Comprehensive tests for DistributedLock

Tests cover:
- Lock acquisition and release
- Lock expiration and TTL
- Redlock algorithm implementation
- Context manager usage
- Lock extension
- Concurrent lock attempts
- Lock ownership verification
- LockManager functionality
- Edge cases and error handling
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from src.coordination.distributed_lock import (
    DistributedLock, LockManager, LockInfo
)


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    redis = AsyncMock()
    redis.set = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock(return_value=1)
    redis.eval = AsyncMock(return_value=1)
    redis.ttl = AsyncMock(return_value=30)
    redis.scan = AsyncMock(return_value=(0, []))
    return redis


@pytest.fixture
def distributed_lock(mock_redis):
    """Create DistributedLock instance"""
    return DistributedLock(
        mock_redis,
        lock_name="test_lock",
        ttl=30
    )


class TestDistributedLockInit:
    """Test DistributedLock initialization"""

    def test_init_default_params(self, mock_redis):
        """Test initialization with default parameters"""
        lock = DistributedLock(mock_redis, "test")

        assert lock.redis == mock_redis
        assert lock.lock_name == "lock:test"
        assert lock.ttl == 30
        assert lock.retry_delay == 0.1
        assert lock.retry_count == 10
        assert lock.is_locked is False

    def test_init_custom_params(self, mock_redis):
        """Test initialization with custom parameters"""
        lock = DistributedLock(
            mock_redis,
            "custom",
            ttl=60,
            retry_delay=0.5,
            retry_count=5
        )

        assert lock.lock_name == "lock:custom"
        assert lock.ttl == 60
        assert lock.retry_delay == 0.5
        assert lock.retry_count == 5

    def test_lock_id_generated(self, distributed_lock):
        """Test lock ID is generated"""
        assert distributed_lock.lock_id is not None
        assert len(distributed_lock.lock_id) > 0


class TestDistributedLockAcquire:
    """Test lock acquisition"""

    @pytest.mark.asyncio
    async def test_acquire_success(self, distributed_lock, mock_redis):
        """Test successful lock acquisition"""
        mock_redis.set.return_value = True

        result = await distributed_lock.acquire(blocking=False)

        assert result is True
        assert distributed_lock.is_locked is True
        assert distributed_lock.acquired_at is not None
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_failure(self, distributed_lock, mock_redis):
        """Test failed lock acquisition"""
        mock_redis.set.return_value = False

        result = await distributed_lock.acquire(blocking=False)

        assert result is False
        assert distributed_lock.is_locked is False

    @pytest.mark.asyncio
    async def test_acquire_blocking_retry(self, distributed_lock, mock_redis):
        """Test blocking acquire with retries"""
        # First 2 attempts fail, third succeeds
        mock_redis.set.side_effect = [False, False, True]

        result = await distributed_lock.acquire(blocking=True)

        assert result is True
        assert distributed_lock.is_locked is True
        assert mock_redis.set.call_count == 3

    @pytest.mark.asyncio
    async def test_acquire_max_retries_exceeded(self, distributed_lock, mock_redis):
        """Test acquire fails after max retries"""
        mock_redis.set.return_value = False

        result = await distributed_lock.acquire(blocking=True)

        assert result is False
        assert mock_redis.set.call_count == distributed_lock.retry_count

    @pytest.mark.asyncio
    async def test_acquire_with_nx_and_ex(self, distributed_lock, mock_redis):
        """Test acquire uses NX and EX flags"""
        mock_redis.set.return_value = True

        await distributed_lock.acquire(blocking=False)

        call_args = mock_redis.set.call_args
        assert call_args[1]['nx'] is True
        assert call_args[1]['ex'] == distributed_lock.ttl

    @pytest.mark.asyncio
    async def test_acquire_error_handling(self, distributed_lock, mock_redis):
        """Test acquire handles Redis errors"""
        mock_redis.set.side_effect = Exception("Redis error")

        result = await distributed_lock.acquire(blocking=False)

        assert result is False


class TestDistributedLockRelease:
    """Test lock release"""

    @pytest.mark.asyncio
    async def test_release_success(self, distributed_lock, mock_redis):
        """Test successful lock release"""
        # Acquire first
        mock_redis.set.return_value = True
        await distributed_lock.acquire(blocking=False)

        # Release
        mock_redis.eval.return_value = 1
        result = await distributed_lock.release()

        assert result is True
        assert distributed_lock.is_locked is False
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_release_not_owned(self, distributed_lock, mock_redis):
        """Test releasing lock not owned by this instance"""
        # Acquire first
        mock_redis.set.return_value = True
        await distributed_lock.acquire(blocking=False)

        # Simulate lock not owned by us
        mock_redis.eval.return_value = 0
        result = await distributed_lock.release()

        assert result is False

    @pytest.mark.asyncio
    async def test_release_without_acquiring(self, distributed_lock):
        """Test releasing non-acquired lock"""
        result = await distributed_lock.release()

        assert result is False

    @pytest.mark.asyncio
    async def test_release_uses_lua_script(self, distributed_lock, mock_redis):
        """Test release uses Lua script for atomicity"""
        mock_redis.set.return_value = True
        await distributed_lock.acquire(blocking=False)

        await distributed_lock.release()

        # Verify Lua script was used
        call_args = mock_redis.eval.call_args
        assert call_args is not None
        assert "redis.call" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_release_error_handling(self, distributed_lock, mock_redis):
        """Test release handles errors"""
        mock_redis.set.return_value = True
        await distributed_lock.acquire(blocking=False)

        mock_redis.eval.side_effect = Exception("Redis error")
        result = await distributed_lock.release()

        assert result is False


class TestDistributedLockExtend:
    """Test lock extension"""

    @pytest.mark.asyncio
    async def test_extend_success(self, distributed_lock, mock_redis):
        """Test successful lock extension"""
        # Acquire first
        mock_redis.set.return_value = True
        await distributed_lock.acquire(blocking=False)

        # Extend
        mock_redis.eval.return_value = 1
        result = await distributed_lock.extend(30)

        assert result is True
        mock_redis.eval.assert_called()

    @pytest.mark.asyncio
    async def test_extend_not_locked(self, distributed_lock):
        """Test extending non-acquired lock"""
        result = await distributed_lock.extend(30)

        assert result is False

    @pytest.mark.asyncio
    async def test_extend_not_owned(self, distributed_lock, mock_redis):
        """Test extending lock not owned"""
        mock_redis.set.return_value = True
        await distributed_lock.acquire(blocking=False)

        # Simulate lock not owned
        mock_redis.eval.return_value = 0
        result = await distributed_lock.extend(30)

        assert result is False

    @pytest.mark.asyncio
    async def test_extend_uses_lua_script(self, distributed_lock, mock_redis):
        """Test extend uses Lua script"""
        mock_redis.set.return_value = True
        await distributed_lock.acquire(blocking=False)

        await distributed_lock.extend(30)

        call_args = mock_redis.eval.call_args
        assert "expire" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_extend_error_handling(self, distributed_lock, mock_redis):
        """Test extend handles errors"""
        mock_redis.set.return_value = True
        await distributed_lock.acquire(blocking=False)

        mock_redis.eval.side_effect = Exception("Redis error")
        result = await distributed_lock.extend(30)

        assert result is False


class TestDistributedLockOwnership:
    """Test lock ownership verification"""

    @pytest.mark.asyncio
    async def test_is_locked_by_me_true(self, distributed_lock, mock_redis):
        """Test checking if lock is owned by this instance"""
        mock_redis.set.return_value = True
        await distributed_lock.acquire(blocking=False)

        mock_redis.get.return_value = distributed_lock.lock_id
        result = await distributed_lock.is_locked_by_me()

        assert result is True

    @pytest.mark.asyncio
    async def test_is_locked_by_me_false(self, distributed_lock, mock_redis):
        """Test checking lock owned by another instance"""
        mock_redis.get.return_value = "other-lock-id"
        result = await distributed_lock.is_locked_by_me()

        assert result is False

    @pytest.mark.asyncio
    async def test_is_locked_by_me_no_lock(self, distributed_lock, mock_redis):
        """Test checking when no lock exists"""
        mock_redis.get.return_value = None
        result = await distributed_lock.is_locked_by_me()

        assert result is False

    @pytest.mark.asyncio
    async def test_get_lock_info(self, distributed_lock, mock_redis):
        """Test getting lock information"""
        mock_redis.set.return_value = True
        await distributed_lock.acquire(blocking=False)

        mock_redis.get.return_value = distributed_lock.lock_id
        mock_redis.ttl.return_value = 25

        info = await distributed_lock.get_lock_info()

        assert info is not None
        assert isinstance(info, LockInfo)
        assert info.lock_name == distributed_lock.lock_name
        assert info.ttl == 25

    @pytest.mark.asyncio
    async def test_get_lock_info_no_lock(self, distributed_lock, mock_redis):
        """Test getting info when no lock exists"""
        mock_redis.get.return_value = None

        info = await distributed_lock.get_lock_info()

        assert info is None


class TestDistributedLockContextManager:
    """Test context manager usage"""

    @pytest.mark.asyncio
    async def test_context_manager_success(self, distributed_lock, mock_redis):
        """Test using lock as context manager"""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1

        async with distributed_lock(blocking=False):
            assert distributed_lock.is_locked is True

        assert distributed_lock.is_locked is False

    @pytest.mark.asyncio
    async def test_context_manager_acquire_failure(self, distributed_lock, mock_redis):
        """Test context manager when acquire fails"""
        mock_redis.set.return_value = False

        with pytest.raises(RuntimeError):
            async with distributed_lock(blocking=False):
                pass

    @pytest.mark.asyncio
    async def test_context_manager_releases_on_exception(self, distributed_lock, mock_redis):
        """Test context manager releases lock on exception"""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1

        try:
            async with distributed_lock(blocking=False):
                raise ValueError("Test error")
        except ValueError:
            pass

        # Lock should be released
        mock_redis.eval.assert_called()


class TestLockManager:
    """Test LockManager"""

    def test_manager_init(self, mock_redis):
        """Test manager initialization"""
        manager = LockManager(mock_redis)

        assert manager.redis == mock_redis
        assert manager.locks == {}

    def test_get_lock_creates_new(self, mock_redis):
        """Test get_lock creates new lock"""
        manager = LockManager(mock_redis)

        lock = manager.get_lock("test_lock")

        assert "test_lock" in manager.locks
        assert isinstance(lock, DistributedLock)

    def test_get_lock_returns_existing(self, mock_redis):
        """Test get_lock returns existing lock"""
        manager = LockManager(mock_redis)

        lock1 = manager.get_lock("test_lock")
        lock2 = manager.get_lock("test_lock")

        assert lock1 is lock2

    def test_get_lock_with_custom_params(self, mock_redis):
        """Test get_lock with custom parameters"""
        manager = LockManager(mock_redis)

        lock = manager.get_lock("test", ttl=60, retry_count=5)

        assert lock.ttl == 60
        assert lock.retry_count == 5

    @pytest.mark.asyncio
    async def test_manager_context_manager(self, mock_redis):
        """Test manager lock context manager"""
        manager = LockManager(mock_redis)
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1

        async with manager.lock("test_lock"):
            lock = manager.locks["test_lock"]
            assert lock.is_locked is True

    @pytest.mark.asyncio
    async def test_release_all(self, mock_redis):
        """Test releasing all locks"""
        manager = LockManager(mock_redis)
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1

        # Acquire multiple locks
        lock1 = manager.get_lock("lock1")
        lock2 = manager.get_lock("lock2")
        await lock1.acquire(blocking=False)
        await lock2.acquire(blocking=False)

        released = await manager.release_all()

        assert released == 2

    @pytest.mark.asyncio
    async def test_get_all_locks_info(self, mock_redis):
        """Test getting info for all locks"""
        manager = LockManager(mock_redis)
        mock_redis.set.return_value = True
        mock_redis.get.return_value = "lock-id"
        mock_redis.ttl.return_value = 30

        lock1 = manager.get_lock("lock1")
        lock2 = manager.get_lock("lock2")
        await lock1.acquire(blocking=False)
        await lock2.acquire(blocking=False)

        info = await manager.get_all_locks_info()

        assert len(info) == 2
        assert "lock1" in info
        assert "lock2" in info

    @pytest.mark.asyncio
    async def test_cleanup_expired_locks(self, mock_redis):
        """Test cleaning up expired locks"""
        manager = LockManager(mock_redis)

        # Mock scan to return lock keys
        mock_redis.scan.return_value = (0, [b"lock:expired1", b"lock:expired2"])
        mock_redis.ttl.return_value = -1  # No expiration

        cleaned = await manager.cleanup_expired_locks()

        assert cleaned == 2
        assert mock_redis.delete.call_count == 2


class TestDistributedLockConcurrency:
    """Test concurrent lock operations"""

    @pytest.mark.asyncio
    async def test_concurrent_acquire_one_succeeds(self, mock_redis):
        """Test only one concurrent acquire succeeds"""
        # First acquire succeeds, rest fail
        mock_redis.set.side_effect = [True] + [False] * 9

        locks = [
            DistributedLock(mock_redis, "shared", ttl=30)
            for _ in range(10)
        ]

        results = await asyncio.gather(*[
            lock.acquire(blocking=False)
            for lock in locks
        ])

        # Only one should succeed
        assert sum(results) == 1

    @pytest.mark.asyncio
    async def test_concurrent_release(self, mock_redis):
        """Test concurrent release operations"""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1

        locks = [
            DistributedLock(mock_redis, f"lock{i}", ttl=30)
            for i in range(5)
        ]

        # Acquire all
        for lock in locks:
            await lock.acquire(blocking=False)

        # Release concurrently
        results = await asyncio.gather(*[
            lock.release()
            for lock in locks
        ])

        assert all(results)


class TestDistributedLockEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_lock_with_zero_ttl(self, mock_redis):
        """Test lock with zero TTL"""
        lock = DistributedLock(mock_redis, "test", ttl=0)
        mock_redis.set.return_value = True

        result = await lock.acquire(blocking=False)

        assert result is True
        assert lock.ttl == 0

    @pytest.mark.asyncio
    async def test_lock_name_with_special_chars(self, mock_redis):
        """Test lock name with special characters"""
        lock = DistributedLock(mock_redis, "test:lock:name", ttl=30)

        assert lock.lock_name == "lock:test:lock:name"

    @pytest.mark.asyncio
    async def test_multiple_acquire_attempts(self, distributed_lock, mock_redis):
        """Test multiple acquire attempts on same lock"""
        mock_redis.set.return_value = True

        await distributed_lock.acquire(blocking=False)

        # Try to acquire again (should still work since it's blocking=True by default)
        mock_redis.set.return_value = False
        result = await distributed_lock.acquire(blocking=False)

        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_after_expiration(self, distributed_lock, mock_redis):
        """Test acquiring lock after it expires"""
        # First acquire
        mock_redis.set.return_value = True
        await distributed_lock.acquire(blocking=False)

        # Simulate expiration
        distributed_lock.is_locked = False

        # Second acquire should succeed
        result = await distributed_lock.acquire(blocking=False)

        assert result is True

    @pytest.mark.asyncio
    async def test_lock_timing(self, distributed_lock, mock_redis):
        """Test lock tracks timing correctly"""
        mock_redis.set.return_value = True

        before = time.time()
        await distributed_lock.acquire(blocking=False)
        after = time.time()

        assert distributed_lock.acquired_at >= before
        assert distributed_lock.acquired_at <= after
