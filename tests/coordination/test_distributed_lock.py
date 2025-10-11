"""Tests for DistributedLock"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.set = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.eval = AsyncMock(return_value=1)
    redis.ttl = AsyncMock(return_value=30)
    return redis


@pytest.mark.asyncio
async def test_lock_acquire(mock_redis):
    """Test lock acquisition"""
    from src.coordination import DistributedLock

    lock = DistributedLock(mock_redis, "test_lock")
    result = await lock.acquire(blocking=False)

    assert result is True
    assert lock.is_locked is True
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_lock_release(mock_redis):
    """Test lock release"""
    from src.coordination import DistributedLock

    lock = DistributedLock(mock_redis, "test_lock")
    await lock.acquire(blocking=False)
    result = await lock.release()

    assert result is True
    assert lock.is_locked is False
    mock_redis.eval.assert_called_once()


@pytest.mark.asyncio
async def test_lock_context_manager(mock_redis):
    """Test lock as context manager"""
    from src.coordination import DistributedLock

    lock = DistributedLock(mock_redis, "test_lock")

    async with lock():
        assert lock.is_locked is True

    # Lock should be released after context
    assert lock.is_locked is False


@pytest.mark.asyncio
async def test_lock_manager(mock_redis):
    """Test LockManager"""
    from src.coordination import LockManager

    manager = LockManager(mock_redis)
    lock1 = manager.get_lock("lock1")
    lock2 = manager.get_lock("lock2")

    assert lock1 is not lock2
    assert len(manager.locks) == 2
