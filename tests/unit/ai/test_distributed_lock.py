"""
Comprehensive tests for distributed locking

Tests lock acquisition/release, deadlock prevention, timeout handling,
and distributed coordination with Redis.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, Mock
from src.coordination.distributed_lock import (
    DistributedLock,
    LockManager,
    LockInfo
)


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = AsyncMock()
    redis.set = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock(return_value=1)
    redis.eval = AsyncMock(return_value=1)
    redis.ttl = AsyncMock(return_value=30)
    redis.scan = AsyncMock(return_value=(0, []))
    return redis


class TestDistributedLockBasics:
    """Test basic distributed lock operations."""

    @pytest.mark.asyncio
    async def test_lock_initialization(self, mock_redis):
        """Test lock initialization."""
        lock = DistributedLock(mock_redis, "test_lock", ttl=30)

        assert lock.lock_name == "lock:test_lock"
        assert lock.ttl == 30
        assert lock.is_locked is False

    @pytest.mark.asyncio
    async def test_acquire_lock(self, mock_redis):
        """Test acquiring lock."""
        mock_redis.set.return_value = True
        lock = DistributedLock(mock_redis, "test_lock")

        acquired = await lock.acquire(blocking=False)

        assert acquired is True
        assert lock.is_locked is True
        assert lock.acquired_at is not None

    @pytest.mark.asyncio
    async def test_acquire_locked(self, mock_redis):
        """Test acquiring already locked resource."""
        mock_redis.set.return_value = False
        lock = DistributedLock(mock_redis, "test_lock", retry_count=1)

        acquired = await lock.acquire(blocking=False)

        assert acquired is False
        assert lock.is_locked is False


class TestLockRelease:
    """Test lock release operations."""

    @pytest.mark.asyncio
    async def test_release_lock(self, mock_redis):
        """Test releasing lock."""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1
        
        lock = DistributedLock(mock_redis, "test_lock")
        await lock.acquire(blocking=False)

        released = await lock.release()

        assert released is True
        assert lock.is_locked is False

    @pytest.mark.asyncio
    async def test_release_non_acquired(self, mock_redis):
        """Test releasing non-acquired lock."""
        lock = DistributedLock(mock_redis, "test_lock")

        released = await lock.release()

        assert released is False

    @pytest.mark.asyncio
    async def test_release_only_own_lock(self, mock_redis):
        """Test can only release own lock."""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 0  # Lock owned by someone else
        
        lock = DistributedLock(mock_redis, "test_lock")
        await lock.acquire(blocking=False)

        released = await lock.release()

        assert released is False


class TestLockRetry:
    """Test lock retry behavior."""

    @pytest.mark.asyncio
    async def test_blocking_acquire(self, mock_redis):
        """Test blocking acquire with retries."""
        call_count = [0]
        
        def set_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                return False
            return True
        
        mock_redis.set.side_effect = set_side_effect
        
        lock = DistributedLock(mock_redis, "test_lock", retry_delay=0.01)

        acquired = await lock.acquire(blocking=True)

        assert acquired is True
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_redis):
        """Test max retries exceeded."""
        mock_redis.set.return_value = False
        
        lock = DistributedLock(
            mock_redis,
            "test_lock",
            retry_count=2,
            retry_delay=0.01
        )

        acquired = await lock.acquire(blocking=True)

        assert acquired is False


class TestLockExtension:
    """Test lock TTL extension."""

    @pytest.mark.asyncio
    async def test_extend_lock(self, mock_redis):
        """Test extending lock TTL."""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1
        
        lock = DistributedLock(mock_redis, "test_lock")
        await lock.acquire(blocking=False)

        extended = await lock.extend(30)

        assert extended is True

    @pytest.mark.asyncio
    async def test_extend_non_acquired(self, mock_redis):
        """Test extending non-acquired lock."""
        lock = DistributedLock(mock_redis, "test_lock")

        extended = await lock.extend(30)

        assert extended is False


class TestLockContext:
    """Test lock context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_redis):
        """Test using lock as context manager."""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1
        
        lock = DistributedLock(mock_redis, "test_lock")

        async with lock(blocking=False):
            assert lock.is_locked is True

        assert lock.is_locked is False

    @pytest.mark.asyncio
    async def test_context_manager_exception(self, mock_redis):
        """Test context manager releases lock on exception."""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1
        
        lock = DistributedLock(mock_redis, "test_lock")

        try:
            async with lock(blocking=False):
                raise ValueError("Test error")
        except ValueError:
            pass

        assert lock.is_locked is False

    @pytest.mark.asyncio
    async def test_context_manager_fails_acquire(self, mock_redis):
        """Test context manager when acquire fails."""
        mock_redis.set.return_value = False
        
        lock = DistributedLock(mock_redis, "test_lock", retry_count=1)

        with pytest.raises(RuntimeError, match="Failed to acquire lock"):
            async with lock(blocking=False):
                pass


class TestLockInfo:
    """Test lock information."""

    @pytest.mark.asyncio
    async def test_get_lock_info(self, mock_redis):
        """Test getting lock information."""
        mock_redis.set.return_value = True
        mock_redis.get.return_value = "lock_id_123"
        mock_redis.ttl.return_value = 25
        
        lock = DistributedLock(mock_redis, "test_lock")
        await lock.acquire(blocking=False)

        info = await lock.get_lock_info()

        assert info is not None
        assert info.lock_name == lock.lock_name
        assert info.ttl == 25

    @pytest.mark.asyncio
    async def test_lock_info_no_lock(self, mock_redis):
        """Test getting info when lock doesn't exist."""
        mock_redis.get.return_value = None
        
        lock = DistributedLock(mock_redis, "test_lock")

        info = await lock.get_lock_info()

        assert info is None


class TestLockManager:
    """Test lock manager."""

    @pytest.mark.asyncio
    async def test_get_lock(self, mock_redis):
        """Test getting lock from manager."""
        manager = LockManager(mock_redis)

        lock = manager.get_lock("test_lock")

        assert lock.lock_name == "lock:test_lock"

    @pytest.mark.asyncio
    async def test_get_same_lock(self, mock_redis):
        """Test getting same lock returns same instance."""
        manager = LockManager(mock_redis)

        lock1 = manager.get_lock("test_lock")
        lock2 = manager.get_lock("test_lock")

        assert lock1 is lock2

    @pytest.mark.asyncio
    async def test_manager_context(self, mock_redis):
        """Test manager lock context."""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1
        
        manager = LockManager(mock_redis)

        async with manager.lock("test_lock"):
            # Lock should be acquired
            lock = manager.get_lock("test_lock")
            assert lock.is_locked is True

    @pytest.mark.asyncio
    async def test_release_all_locks(self, mock_redis):
        """Test releasing all locks."""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1
        
        manager = LockManager(mock_redis)

        lock1 = manager.get_lock("lock1")
        lock2 = manager.get_lock("lock2")
        
        await lock1.acquire(blocking=False)
        await lock2.acquire(blocking=False)

        released = await manager.release_all()

        assert released == 2


class TestDeadlockPrevention:
    """Test deadlock prevention features."""

    @pytest.mark.asyncio
    async def test_lock_timeout(self, mock_redis):
        """Test lock automatically expires."""
        mock_redis.set.return_value = True
        
        lock = DistributedLock(mock_redis, "test_lock", ttl=1)
        await lock.acquire(blocking=False)

        # Verify TTL was set
        call_args = mock_redis.set.call_args
        assert call_args[1]['ex'] == 1

    @pytest.mark.asyncio
    async def test_cleanup_expired_locks(self, mock_redis):
        """Test cleaning up expired locks."""
        mock_redis.scan.return_value = (0, [b"lock:test1", b"lock:test2"])
        mock_redis.ttl.side_effect = [-1, 30]  # First has no TTL
        
        manager = LockManager(mock_redis)

        cleaned = await manager.cleanup_expired_locks()

        assert cleaned == 1
        mock_redis.delete.assert_called_once()


class TestConcurrency:
    """Test concurrent lock operations."""

    @pytest.mark.asyncio
    async def test_concurrent_acquire(self, mock_redis):
        """Test concurrent lock acquisition."""
        acquired_count = [0]
        
        def set_side_effect(*args, **kwargs):
            acquired_count[0] += 1
            return acquired_count[0] == 1  # Only first succeeds
        
        mock_redis.set.side_effect = set_side_effect

        lock1 = DistributedLock(mock_redis, "test_lock", retry_count=1)
        lock2 = DistributedLock(mock_redis, "test_lock", retry_count=1)

        result1, result2 = await asyncio.gather(
            lock1.acquire(blocking=False),
            lock2.acquire(blocking=False)
        )

        # Only one should succeed
        assert (result1 and not result2) or (result2 and not result1)


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_very_short_ttl(self, mock_redis):
        """Test lock with very short TTL."""
        mock_redis.set.return_value = True
        
        lock = DistributedLock(mock_redis, "test_lock", ttl=0.1)
        await lock.acquire(blocking=False)

        await asyncio.sleep(0.15)

        # Lock should have expired (though we can't test automatic expiry in mocks)
        assert lock.acquired_at is not None

    @pytest.mark.asyncio
    async def test_lock_with_special_characters(self, mock_redis):
        """Test lock name with special characters."""
        mock_redis.set.return_value = True
        
        lock = DistributedLock(mock_redis, "test:lock:name/with-chars")

        acquired = await lock.acquire(blocking=False)

        assert acquired is True

    @pytest.mark.asyncio
    async def test_is_locked_by_me(self, mock_redis):
        """Test checking if lock is owned."""
        mock_redis.set.return_value = True
        
        lock = DistributedLock(mock_redis, "test_lock")
        await lock.acquire(blocking=False)

        mock_redis.get.return_value = lock.lock_id

        is_mine = await lock.is_locked_by_me()

        assert is_mine is True
