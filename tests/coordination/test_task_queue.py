"""
Comprehensive tests for distributed task queue

Tests priority handling, retries, dead letter queue, task visibility,
and distributed task coordination.
"""

import asyncio
import pytest
import json
import time
from unittest.mock import AsyncMock, Mock, MagicMock
from src.coordination.task_queue import (
    Task,
    TaskPriority,
    TaskStatus,
    TaskQueue
)


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = AsyncMock()
    redis.hset = AsyncMock()
    redis.hget = AsyncMock()
    redis.hdel = AsyncMock()
    redis.zadd = AsyncMock()
    redis.zpopmax = AsyncMock()
    redis.zrem = AsyncMock()
    redis.zcard = AsyncMock()
    redis.zrangebyscore = AsyncMock(return_value=[])
    return redis


class TestTask:
    """Test Task dataclass."""

    def test_task_creation(self):
        """Test creating task."""
        task = Task(
            task_id="task_1",
            task_type="process_data",
            payload={"data": "value"},
            priority=TaskPriority.HIGH
        )

        assert task.task_id == "task_1"
        assert task.task_type == "process_data"
        assert task.payload == {"data": "value"}
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.attempts == 0

    def test_task_with_defaults(self):
        """Test task with default values."""
        task = Task(
            task_id="task_1",
            task_type="test",
            payload={}
        )

        assert task.priority == TaskPriority.NORMAL
        assert task.max_retries == 3
        assert task.timeout == 300
        assert task.status == TaskStatus.PENDING

    def test_task_to_dict(self):
        """Test converting task to dictionary."""
        task = Task(
            task_id="task_1",
            task_type="test",
            payload={"key": "value"}
        )

        data = task.to_dict()

        assert data['task_id'] == "task_1"
        assert data['task_type'] == "test"
        assert data['payload'] == {"key": "value"}
        assert data['priority'] == TaskPriority.NORMAL.value
        assert data['status'] == TaskStatus.PENDING.value

    def test_task_from_dict(self):
        """Test creating task from dictionary."""
        data = {
            'task_id': 'task_1',
            'task_type': 'test',
            'payload': {'key': 'value'},
            'priority': TaskPriority.HIGH.value,
            'max_retries': 5,
            'timeout': 600,
            'created_at': time.time(),
            'status': TaskStatus.PENDING.value,
            'attempts': 0,
            'last_error': None,
            'started_at': None,
            'completed_at': None,
            'worker_id': None
        }

        task = Task.from_dict(data)

        assert task.task_id == 'task_1'
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING


class TestTaskQueueBasics:
    """Test basic task queue operations."""

    @pytest.mark.asyncio
    async def test_queue_initialization(self, mock_redis):
        """Test task queue initialization."""
        queue = TaskQueue(mock_redis, queue_name="test_queue")

        assert queue.queue_name == "test_queue"
        assert queue.visibility_timeout == 300
        assert queue.worker_id is not None

    @pytest.mark.asyncio
    async def test_queue_keys(self, mock_redis):
        """Test queue uses correct Redis keys."""
        queue = TaskQueue(mock_redis, queue_name="my_queue")

        assert queue.pending_key == "queue:my_queue:pending"
        assert queue.processing_key == "queue:my_queue:processing"
        assert queue.completed_key == "queue:my_queue:completed"
        assert queue.failed_key == "queue:my_queue:failed"
        assert queue.dlq_key == "queue:my_queue:dlq"
        assert queue.tasks_key == "queue:my_queue:tasks"


class TestEnqueueTask:
    """Test task enqueueing."""

    @pytest.mark.asyncio
    async def test_enqueue_task(self, mock_redis):
        """Test enqueueing task."""
        queue = TaskQueue(mock_redis)

        task = Task(
            task_id="task_1",
            task_type="test",
            payload={"data": "value"}
        )

        task_id = await queue.enqueue(task)

        assert task_id == "task_1"
        mock_redis.hset.assert_called()
        mock_redis.zadd.assert_called()

    @pytest.mark.asyncio
    async def test_enqueue_stores_task_data(self, mock_redis):
        """Test enqueue stores task data in Redis."""
        queue = TaskQueue(mock_redis)

        task = Task(
            task_id="task_1",
            task_type="test",
            payload={"key": "value"}
        )

        await queue.enqueue(task)

        # Verify task data stored
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == queue.tasks_key
        assert call_args[0][1] == "task_1"

        # Verify JSON serialization
        stored_data = json.loads(call_args[0][2])
        assert stored_data['task_id'] == "task_1"

    @pytest.mark.asyncio
    async def test_enqueue_with_priority(self, mock_redis):
        """Test enqueue respects priority."""
        queue = TaskQueue(mock_redis)

        high_priority_task = Task(
            task_id="task_high",
            task_type="test",
            payload={},
            priority=TaskPriority.HIGH
        )

        await queue.enqueue(high_priority_task)

        # Verify priority in score
        zadd_call = mock_redis.zadd.call_args[0]
        score = list(zadd_call[1].values())[0]

        # High priority (2) * 1000000 + timestamp
        assert score >= TaskPriority.HIGH.value * 1000000


class TestDequeueTask:
    """Test task dequeueing."""

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self, mock_redis):
        """Test dequeuing from empty queue."""
        mock_redis.zpopmax.return_value = None

        queue = TaskQueue(mock_redis)

        task = await queue.dequeue(timeout=None)

        assert task is None

    @pytest.mark.asyncio
    async def test_dequeue_task(self, mock_redis):
        """Test dequeuing task."""
        task_data = Task(
            task_id="task_1",
            task_type="test",
            payload={"data": "value"}
        )

        mock_redis.zpopmax.return_value = [(b"task_1", 1000000.0)]
        mock_redis.hget.return_value = json.dumps(task_data.to_dict())

        queue = TaskQueue(mock_redis)

        task = await queue.dequeue(timeout=None)

        assert task is not None
        assert task.task_id == "task_1"
        assert task.status == TaskStatus.PROCESSING
        assert task.attempts == 1

    @pytest.mark.asyncio
    async def test_dequeue_marks_processing(self, mock_redis):
        """Test dequeue marks task as processing."""
        task_data = Task(
            task_id="task_1",
            task_type="test",
            payload={}
        )

        mock_redis.zpopmax.return_value = [(b"task_1", 1000000.0)]
        mock_redis.hget.return_value = json.dumps(task_data.to_dict())

        queue = TaskQueue(mock_redis)

        task = await queue.dequeue()

        assert task.status == TaskStatus.PROCESSING
        assert task.worker_id == queue.worker_id
        assert task.started_at is not None

    @pytest.mark.asyncio
    async def test_dequeue_with_timeout(self, mock_redis):
        """Test dequeue with timeout."""
        mock_redis.zpopmax.return_value = None

        queue = TaskQueue(mock_redis)

        start = time.time()
        task = await queue.dequeue(timeout=0.1)
        duration = time.time() - start

        assert task is None
        assert duration >= 0.1


class TestCompleteTask:
    """Test task completion."""

    @pytest.mark.asyncio
    async def test_complete_task(self, mock_redis):
        """Test completing task."""
        task_data = Task(
            task_id="task_1",
            task_type="test",
            payload={},
            status=TaskStatus.PROCESSING,
            started_at=time.time()
        )

        mock_redis.hget.return_value = json.dumps(task_data.to_dict())

        queue = TaskQueue(mock_redis)

        result = await queue.complete_task("task_1")

        assert result is True
        mock_redis.zrem.assert_called_with(queue.processing_key, "task_1")
        mock_redis.zadd.assert_called()

    @pytest.mark.asyncio
    async def test_complete_updates_status(self, mock_redis):
        """Test complete updates task status."""
        task_data = Task(
            task_id="task_1",
            task_type="test",
            payload={},
            status=TaskStatus.PROCESSING
        )

        mock_redis.hget.return_value = json.dumps(task_data.to_dict())

        queue = TaskQueue(mock_redis)

        await queue.complete_task("task_1")

        # Verify status updated to COMPLETED
        hset_call = mock_redis.hset.call_args[0]
        updated_data = json.loads(hset_call[2])
        assert updated_data['status'] == TaskStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_complete_non_existent_task(self, mock_redis):
        """Test completing non-existent task."""
        mock_redis.hget.return_value = None

        queue = TaskQueue(mock_redis)

        result = await queue.complete_task("non_existent")

        assert result is False


class TestFailTask:
    """Test task failure handling."""

    @pytest.mark.asyncio
    async def test_fail_task_with_retry(self, mock_redis):
        """Test failing task with retry."""
        task_data = Task(
            task_id="task_1",
            task_type="test",
            payload={},
            status=TaskStatus.PROCESSING,
            attempts=1,
            max_retries=3
        )

        mock_redis.hget.return_value = json.dumps(task_data.to_dict())

        queue = TaskQueue(mock_redis)

        result = await queue.fail_task("task_1", "Error message", retry=True)

        assert result is True
        # Should re-queue for retry
        mock_redis.zadd.assert_called()

    @pytest.mark.asyncio
    async def test_fail_task_max_retries(self, mock_redis):
        """Test failing task that exceeded max retries."""
        task_data = Task(
            task_id="task_1",
            task_type="test",
            payload={},
            status=TaskStatus.PROCESSING,
            attempts=3,
            max_retries=3
        )

        mock_redis.hget.return_value = json.dumps(task_data.to_dict())

        queue = TaskQueue(mock_redis)

        await queue.fail_task("task_1", "Error message", retry=True)

        # Should move to dead letter queue
        dlq_zadd_call = None
        for call in mock_redis.zadd.call_args_list:
            if call[0][0] == queue.dlq_key:
                dlq_zadd_call = call
                break

        assert dlq_zadd_call is not None

    @pytest.mark.asyncio
    async def test_fail_task_exponential_backoff(self, mock_redis):
        """Test fail uses exponential backoff for retry."""
        task_data = Task(
            task_id="task_1",
            task_type="test",
            payload={},
            attempts=2,
            max_retries=5
        )

        mock_redis.hget.return_value = json.dumps(task_data.to_dict())

        queue = TaskQueue(mock_redis)

        await queue.fail_task("task_1", "Error", retry=True)

        # Verify delay calculation (2^2 = 4 seconds)
        zadd_call = None
        for call in mock_redis.zadd.call_args_list:
            if call[0][0] == queue.pending_key:
                zadd_call = call
                break

        assert zadd_call is not None


class TestQueueStatistics:
    """Test queue statistics."""

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, mock_redis):
        """Test getting queue statistics."""
        mock_redis.zcard.side_effect = [10, 5, 100, 2, 3]

        queue = TaskQueue(mock_redis)

        stats = await queue.get_queue_stats()

        assert stats['queue_name'] == "default"
        assert stats['pending'] == 10
        assert stats['processing'] == 5
        assert stats['completed'] == 100
        assert stats['failed'] == 2
        assert stats['dead_letter'] == 3
        assert stats['total'] == 120


class TestStaleTaskRecovery:
    """Test stale task recovery."""

    @pytest.mark.asyncio
    async def test_recover_stale_tasks(self, mock_redis):
        """Test recovering stale tasks."""
        task_data = Task(
            task_id="stale_task",
            task_type="test",
            payload={},
            status=TaskStatus.PROCESSING,
            attempts=1
        )

        mock_redis.zrangebyscore.return_value = [b"stale_task"]
        mock_redis.hget.return_value = json.dumps(task_data.to_dict())

        queue = TaskQueue(mock_redis)

        recovered = await queue.recover_stale_tasks()

        assert recovered == 1

    @pytest.mark.asyncio
    async def test_recover_no_stale_tasks(self, mock_redis):
        """Test recovery with no stale tasks."""
        mock_redis.zrangebyscore.return_value = []

        queue = TaskQueue(mock_redis)

        recovered = await queue.recover_stale_tasks()

        assert recovered == 0
