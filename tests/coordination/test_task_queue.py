"""Tests for TaskQueue"""

import pytest
import json
from unittest.mock import AsyncMock


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.hset = AsyncMock()
    redis.hget = AsyncMock()
    redis.zadd = AsyncMock()
    redis.zpopmax = AsyncMock(return_value=[])
    redis.zcard = AsyncMock(return_value=0)
    return redis


@pytest.mark.asyncio
async def test_task_creation():
    """Test task creation"""
    from src.coordination import Task, TaskPriority

    task = Task(
        task_id="test_id",
        task_type="test",
        payload={"key": "value"},
        priority=TaskPriority.HIGH
    )

    assert task.task_id == "test_id"
    assert task.priority == TaskPriority.HIGH


@pytest.mark.asyncio
async def test_task_serialization():
    """Test task serialization"""
    from src.coordination import Task, TaskPriority

    task = Task(
        task_id="test_id",
        task_type="test",
        payload={"key": "value"}
    )

    task_dict = task.to_dict()
    restored_task = Task.from_dict(task_dict)

    assert restored_task.task_id == task.task_id
    assert restored_task.task_type == task.task_type


@pytest.mark.asyncio
async def test_queue_enqueue(mock_redis):
    """Test task enqueueing"""
    from src.coordination import TaskQueue, Task, TaskPriority

    queue = TaskQueue(mock_redis, "test_queue")
    task = Task(
        task_id="test_id",
        task_type="test",
        payload={}
    )

    task_id = await queue.enqueue(task)

    assert task_id == "test_id"
    mock_redis.hset.assert_called()
    mock_redis.zadd.assert_called()


@pytest.mark.asyncio
async def test_queue_stats(mock_redis):
    """Test queue statistics"""
    from src.coordination import TaskQueue

    queue = TaskQueue(mock_redis, "test_queue")
    stats = await queue.get_queue_stats()

    assert "queue_name" in stats
    assert "pending" in stats
    assert "processing" in stats
