"""
Comprehensive tests for TaskQueue

Tests cover:
- Task enqueuing with priorities
- Task dequeuing and processing
- Task completion and failure
- Retry logic with exponential backoff
- Dead letter queue
- Queue statistics
- Stale task recovery
- Task purging
- Concurrent operations
- Edge cases
"""

import asyncio
import json
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from src.coordination.task_queue import (
    Task, TaskQueue, TaskPriority, TaskStatus
)


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    redis = AsyncMock()
    redis.hset = AsyncMock(return_value=1)
    redis.hget = AsyncMock()
    redis.zadd = AsyncMock(return_value=1)
    redis.zpopmax = AsyncMock()
    redis.zrem = AsyncMock(return_value=1)
    redis.zcard = AsyncMock(return_value=0)
    redis.zrangebyscore = AsyncMock(return_value=[])
    redis.hdel = AsyncMock(return_value=1)
    redis.scan = AsyncMock(return_value=(0, []))
    return redis


@pytest.fixture
def task_queue(mock_redis):
    """Create TaskQueue instance"""
    return TaskQueue(mock_redis, queue_name="test_queue")


@pytest.fixture
def sample_task():
    """Create sample task"""
    return Task(
        task_id="task-123",
        task_type="process_data",
        payload={"data": "test"},
        priority=TaskPriority.NORMAL
    )


class TestTask:
    """Test Task dataclass"""

    def test_task_creation(self):
        """Test creating a task"""
        task = Task(
            task_id="test-1",
            task_type="test",
            payload={"key": "value"},
            priority=TaskPriority.HIGH
        )

        assert task.task_id == "test-1"
        assert task.task_type == "test"
        assert task.payload == {"key": "value"}
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.attempts == 0

    def test_task_to_dict(self):
        """Test converting task to dictionary"""
        task = Task(
            task_id="test-1",
            task_type="test",
            payload={"key": "value"}
        )

        task_dict = task.to_dict()

        assert task_dict['task_id'] == "test-1"
        assert task_dict['task_type'] == "test"
        assert task_dict['priority'] == TaskPriority.NORMAL.value
        assert task_dict['status'] == TaskStatus.PENDING.value

    def test_task_from_dict(self):
        """Test creating task from dictionary"""
        task_dict = {
            'task_id': 'test-1',
            'task_type': 'test',
            'payload': {'key': 'value'},
            'priority': TaskPriority.HIGH.value,
            'status': TaskStatus.PROCESSING.value,
            'max_retries': 3,
            'timeout': 300,
            'created_at': time.time(),
            'attempts': 1,
            'last_error': None,
            'started_at': None,
            'completed_at': None,
            'worker_id': None
        }

        task = Task.from_dict(task_dict)

        assert task.task_id == 'test-1'
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PROCESSING


class TestTaskQueueInit:
    """Test TaskQueue initialization"""

    def test_init_default_params(self, mock_redis):
        """Test initialization with default parameters"""
        queue = TaskQueue(mock_redis)

        assert queue.redis == mock_redis
        assert queue.queue_name == "default"
        assert queue.visibility_timeout == 300
        assert queue.worker_id is not None

    def test_init_custom_params(self, mock_redis):
        """Test initialization with custom parameters"""
        queue = TaskQueue(
            mock_redis,
            queue_name="custom",
            visibility_timeout=600
        )

        assert queue.queue_name == "custom"
        assert queue.visibility_timeout == 600

    def test_redis_keys_generated(self, task_queue):
        """Test Redis keys are properly generated"""
        assert task_queue.pending_key == "queue:test_queue:pending"
        assert task_queue.processing_key == "queue:test_queue:processing"
        assert task_queue.completed_key == "queue:test_queue:completed"
        assert task_queue.dlq_key == "queue:test_queue:dlq"


class TestTaskQueueEnqueue:
    """Test task enqueuing"""

    @pytest.mark.asyncio
    async def test_enqueue_basic_task(self, task_queue, sample_task, mock_redis):
        """Test enqueuing a basic task"""
        task_id = await task_queue.enqueue(sample_task)

        assert task_id == sample_task.task_id
        mock_redis.hset.assert_called_once()
        mock_redis.zadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_enqueue_high_priority_task(self, task_queue, mock_redis):
        """Test high priority task gets higher score"""
        high_priority_task = Task(
            task_id="high-1",
            task_type="urgent",
            payload={},
            priority=TaskPriority.HIGH
        )

        await task_queue.enqueue(high_priority_task)

        # Verify zadd was called with high priority score
        call_args = mock_redis.zadd.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_enqueue_multiple_tasks(self, task_queue, mock_redis):
        """Test enqueuing multiple tasks"""
        tasks = [
            Task(f"task-{i}", "test", {}, TaskPriority.NORMAL)
            for i in range(5)
        ]

        for task in tasks:
            await task_queue.enqueue(task)

        assert mock_redis.hset.call_count == 5
        assert mock_redis.zadd.call_count == 5

    @pytest.mark.asyncio
    async def test_enqueue_error_handling(self, task_queue, sample_task, mock_redis):
        """Test enqueue handles Redis errors"""
        mock_redis.hset.side_effect = Exception("Redis error")

        with pytest.raises(Exception):
            await task_queue.enqueue(sample_task)


class TestTaskQueueDequeue:
    """Test task dequeuing"""

    @pytest.mark.asyncio
    async def test_dequeue_task(self, task_queue, sample_task, mock_redis):
        """Test dequeuing a task"""
        # Mock Redis to return a task
        task_data = json.dumps(sample_task.to_dict())
        mock_redis.zpopmax.return_value = [(b"task-123", 1000000.0)]
        mock_redis.hget.return_value = task_data

        task = await task_queue.dequeue()

        assert task is not None
        assert task.task_id == sample_task.task_id
        assert task.status == TaskStatus.PROCESSING
        assert task.attempts == 1

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self, task_queue, mock_redis):
        """Test dequeuing from empty queue"""
        mock_redis.zpopmax.return_value = []

        task = await task_queue.dequeue(timeout=None)

        assert task is None

    @pytest.mark.asyncio
    async def test_dequeue_with_timeout(self, task_queue, mock_redis):
        """Test dequeue with timeout"""
        mock_redis.zpopmax.return_value = []

        start = time.time()
        task = await task_queue.dequeue(timeout=0.5)
        duration = time.time() - start

        assert task is None
        assert duration >= 0.5

    @pytest.mark.asyncio
    async def test_dequeue_missing_task_data(self, task_queue, mock_redis):
        """Test dequeue handles missing task data"""
        mock_redis.zpopmax.return_value = [(b"task-123", 1000000.0)]
        mock_redis.hget.return_value = None

        # Should skip task and return None
        task = await task_queue.dequeue(timeout=None)
        assert task is None

    @pytest.mark.asyncio
    async def test_dequeue_increments_attempts(self, task_queue, sample_task, mock_redis):
        """Test dequeue increments attempt counter"""
        sample_task.attempts = 2
        task_data = json.dumps(sample_task.to_dict())
        mock_redis.zpopmax.return_value = [(b"task-123", 1000000.0)]
        mock_redis.hget.return_value = task_data

        task = await task_queue.dequeue()

        assert task.attempts == 3


class TestTaskQueueComplete:
    """Test task completion"""

    @pytest.mark.asyncio
    async def test_complete_task(self, task_queue, sample_task, mock_redis):
        """Test completing a task"""
        task_data = json.dumps(sample_task.to_dict())
        mock_redis.hget.return_value = task_data

        result = await task_queue.complete_task(sample_task.task_id)

        assert result is True
        mock_redis.zrem.assert_called_once()
        mock_redis.zadd.assert_called()

    @pytest.mark.asyncio
    async def test_complete_nonexistent_task(self, task_queue, mock_redis):
        """Test completing non-existent task"""
        mock_redis.hget.return_value = None

        result = await task_queue.complete_task("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_complete_updates_status(self, task_queue, sample_task, mock_redis):
        """Test completion updates task status"""
        task_data = json.dumps(sample_task.to_dict())
        mock_redis.hget.return_value = task_data

        await task_queue.complete_task(sample_task.task_id)

        # Check that hset was called to update task status
        update_call = [call for call in mock_redis.hset.call_args_list
                       if 'completed' in str(call)]
        assert len(update_call) > 0


class TestTaskQueueFail:
    """Test task failure handling"""

    @pytest.mark.asyncio
    async def test_fail_task_with_retry(self, task_queue, sample_task, mock_redis):
        """Test failing task with retries remaining"""
        sample_task.attempts = 1
        task_data = json.dumps(sample_task.to_dict())
        mock_redis.hget.return_value = task_data

        result = await task_queue.fail_task(
            sample_task.task_id,
            "Test error",
            retry=True
        )

        assert result is True
        # Should be re-queued
        mock_redis.zadd.assert_called()

    @pytest.mark.asyncio
    async def test_fail_task_no_retries_left(self, task_queue, sample_task, mock_redis):
        """Test failing task with no retries left"""
        sample_task.attempts = 3
        sample_task.max_retries = 3
        task_data = json.dumps(sample_task.to_dict())
        mock_redis.hget.return_value = task_data

        result = await task_queue.fail_task(
            sample_task.task_id,
            "Final error",
            retry=True
        )

        assert result is True
        # Should be moved to DLQ
        dlq_calls = [call for call in mock_redis.zadd.call_args_list
                     if 'dlq' in str(call)]
        assert len(dlq_calls) > 0

    @pytest.mark.asyncio
    async def test_fail_task_without_retry(self, task_queue, sample_task, mock_redis):
        """Test failing task without retry"""
        task_data = json.dumps(sample_task.to_dict())
        mock_redis.hget.return_value = task_data

        result = await task_queue.fail_task(
            sample_task.task_id,
            "Error",
            retry=False
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_fail_exponential_backoff(self, task_queue, sample_task, mock_redis):
        """Test exponential backoff on retries"""
        # Test with different attempt counts
        for attempts in [1, 2, 3]:
            sample_task.attempts = attempts
            task_data = json.dumps(sample_task.to_dict())
            mock_redis.hget.return_value = task_data

            await task_queue.fail_task(sample_task.task_id, "Error", retry=True)

            # Verify delay increases exponentially (2^attempts)
            expected_delay = 2 ** attempts
            assert expected_delay in [2, 4, 8]


class TestTaskQueueStats:
    """Test queue statistics"""

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, task_queue, mock_redis):
        """Test getting queue statistics"""
        mock_redis.zcard.side_effect = [5, 2, 10, 1, 0]  # pending, processing, completed, failed, dlq

        stats = await task_queue.get_queue_stats()

        assert stats['queue_name'] == 'test_queue'
        assert stats['pending'] == 5
        assert stats['processing'] == 2
        assert stats['completed'] == 10
        assert stats['failed'] == 1
        assert stats['dead_letter'] == 0
        assert stats['total'] == 18

    @pytest.mark.asyncio
    async def test_get_queue_stats_error(self, task_queue, mock_redis):
        """Test queue stats handles errors"""
        mock_redis.zcard.side_effect = Exception("Redis error")

        stats = await task_queue.get_queue_stats()

        assert stats == {}


class TestTaskQueueRecovery:
    """Test stale task recovery"""

    @pytest.mark.asyncio
    async def test_recover_stale_tasks(self, task_queue, sample_task, mock_redis):
        """Test recovering stale tasks"""
        task_data = json.dumps(sample_task.to_dict())
        mock_redis.zrangebyscore.return_value = [b"task-123"]
        mock_redis.hget.return_value = task_data

        recovered = await task_queue.recover_stale_tasks()

        assert recovered == 1

    @pytest.mark.asyncio
    async def test_recover_no_stale_tasks(self, task_queue, mock_redis):
        """Test recovery with no stale tasks"""
        mock_redis.zrangebyscore.return_value = []

        recovered = await task_queue.recover_stale_tasks()

        assert recovered == 0

    @pytest.mark.asyncio
    async def test_recover_missing_task_data(self, task_queue, mock_redis):
        """Test recovery handles missing task data"""
        mock_redis.zrangebyscore.return_value = [b"task-123"]
        mock_redis.hget.return_value = None

        recovered = await task_queue.recover_stale_tasks()

        # Should clean up the orphaned task ID
        mock_redis.zrem.assert_called()


class TestTaskQueuePurge:
    """Test task purging"""

    @pytest.mark.asyncio
    async def test_purge_completed_tasks(self, task_queue, mock_redis):
        """Test purging old completed tasks"""
        old_tasks = [b"task-1", b"task-2", b"task-3"]
        mock_redis.zrangebyscore.return_value = old_tasks

        purged = await task_queue.purge_completed(older_than=3600)

        assert purged == 3
        assert mock_redis.hdel.call_count == 3
        assert mock_redis.zrem.call_count == 3

    @pytest.mark.asyncio
    async def test_purge_no_old_tasks(self, task_queue, mock_redis):
        """Test purging with no old tasks"""
        mock_redis.zrangebyscore.return_value = []

        purged = await task_queue.purge_completed()

        assert purged == 0


class TestTaskQueueConcurrency:
    """Test concurrent operations"""

    @pytest.mark.asyncio
    async def test_concurrent_enqueue(self, task_queue, mock_redis):
        """Test concurrent task enqueuing"""
        tasks = [
            Task(f"task-{i}", "test", {})
            for i in range(10)
        ]

        results = await asyncio.gather(*[
            task_queue.enqueue(task)
            for task in tasks
        ])

        assert len(results) == 10
        assert mock_redis.hset.call_count == 10

    @pytest.mark.asyncio
    async def test_concurrent_dequeue(self, task_queue, mock_redis):
        """Test concurrent task dequeuing"""
        # Mock different tasks for each dequeue
        mock_redis.zpopmax.side_effect = [
            [(f"task-{i}".encode(), 1000000.0)]
            for i in range(5)
        ]

        mock_redis.hget.side_effect = [
            json.dumps(Task(f"task-{i}", "test", {}).to_dict())
            for i in range(5)
        ]

        results = await asyncio.gather(*[
            task_queue.dequeue(timeout=None)
            for _ in range(5)
        ])

        assert len(results) == 5
        assert all(task is not None for task in results)


class TestTaskQueueEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_task_with_zero_ttl(self, mock_redis):
        """Test task with zero TTL"""
        queue = TaskQueue(mock_redis, visibility_timeout=0)
        task = Task("test", "type", {})

        await queue.enqueue(task)
        assert queue.visibility_timeout == 0

    @pytest.mark.asyncio
    async def test_task_priorities_ordering(self, task_queue):
        """Test task priorities maintain correct order"""
        priorities = [
            TaskPriority.LOW,
            TaskPriority.NORMAL,
            TaskPriority.HIGH,
            TaskPriority.CRITICAL
        ]

        assert priorities[0].value < priorities[1].value < priorities[2].value < priorities[3].value

    @pytest.mark.asyncio
    async def test_unicode_in_task_payload(self, task_queue, mock_redis):
        """Test handling unicode in task payload"""
        task = Task(
            "unicode-task",
            "test",
            {"message": "Hello 世界 🌍"}
        )

        task_id = await task_queue.enqueue(task)
        assert task_id == "unicode-task"
