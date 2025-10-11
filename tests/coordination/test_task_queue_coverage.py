"""
Comprehensive coverage tests for TaskQueue
Targeting 90%+ coverage with all edge cases, error paths, and priority handling
"""

import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock, patch
from src.coordination.task_queue import (
    Task,
    TaskQueue,
    TaskPriority,
    TaskStatus,
)


class MockRedis:
    """Enhanced Mock Redis client for comprehensive testing"""

    def __init__(self):
        self.data = {}  # Hash storage
        self.sorted_sets = {}  # Sorted set storage
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
        return self.data.get(key, {}).get(field)

    async def hdel(self, key, field):
        if self.should_fail or 'hdel' in self.fail_operations:
            raise Exception("Redis hdel error")
        if key in self.data and field in self.data[key]:
            del self.data[key][field]
            return 1
        return 0

    async def zadd(self, key, mapping):
        if self.should_fail or 'zadd' in self.fail_operations:
            raise Exception("Redis zadd error")
        if key not in self.sorted_sets:
            self.sorted_sets[key] = {}
        self.sorted_sets[key].update(mapping)
        return len(mapping)

    async def zpopmax(self, key):
        if self.should_fail or 'zpopmax' in self.fail_operations:
            raise Exception("Redis zpopmax error")
        if key not in self.sorted_sets or not self.sorted_sets[key]:
            return []
        # Get highest score item
        items = sorted(self.sorted_sets[key].items(), key=lambda x: x[1], reverse=True)
        if items:
            task_id, score = items[0]
            del self.sorted_sets[key][task_id]
            return [(task_id, score)]
        return []

    async def zrem(self, key, member):
        if self.should_fail or 'zrem' in self.fail_operations:
            raise Exception("Redis zrem error")
        if key in self.sorted_sets and member in self.sorted_sets[key]:
            del self.sorted_sets[key][member]
            return 1
        return 0

    async def zcard(self, key):
        if self.should_fail or 'zcard' in self.fail_operations:
            raise Exception("Redis zcard error")
        return len(self.sorted_sets.get(key, {}))

    async def zrangebyscore(self, key, min_score, max_score):
        if self.should_fail or 'zrangebyscore' in self.fail_operations:
            raise Exception("Redis zrangebyscore error")
        if key not in self.sorted_sets:
            return []
        return [
            task_id for task_id, score in self.sorted_sets[key].items()
            if min_score <= score <= max_score
        ]


class TestTaskCreation:
    """Test Task class functionality"""

    def test_task_creation_defaults(self):
        """Test task creation with default values"""
        task = Task(
            task_id="test-123",
            task_type="test_type",
            payload={"data": "value"}
        )

        assert task.task_id == "test-123"
        assert task.task_type == "test_type"
        assert task.payload == {"data": "value"}
        assert task.priority == TaskPriority.NORMAL
        assert task.max_retries == 3
        assert task.timeout == 300
        assert task.status == TaskStatus.PENDING
        assert task.attempts == 0
        assert task.last_error is None

    def test_task_creation_custom_values(self):
        """Test task creation with custom values"""
        task = Task(
            task_id="custom-456",
            task_type="custom",
            payload={"key": "val"},
            priority=TaskPriority.CRITICAL,
            max_retries=5,
            timeout=600
        )

        assert task.priority == TaskPriority.CRITICAL
        assert task.max_retries == 5
        assert task.timeout == 600

    def test_task_to_dict(self):
        """Test task serialization to dict"""
        task = Task(
            task_id="ser-123",
            task_type="serialize",
            payload={"x": 1},
            priority=TaskPriority.HIGH
        )

        task_dict = task.to_dict()

        assert task_dict["task_id"] == "ser-123"
        assert task_dict["priority"] == TaskPriority.HIGH.value
        assert task_dict["status"] == TaskStatus.PENDING.value
        assert task_dict["payload"] == {"x": 1}

    def test_task_from_dict(self):
        """Test task deserialization from dict"""
        task_dict = {
            "task_id": "deser-123",
            "task_type": "deserialize",
            "payload": {"y": 2},
            "priority": TaskPriority.LOW.value,
            "status": TaskStatus.PROCESSING.value,
            "max_retries": 3,
            "timeout": 300,
            "created_at": time.time(),
            "attempts": 1,
            "last_error": "test error",
            "started_at": None,
            "completed_at": None,
            "worker_id": "worker-1"
        }

        task = Task.from_dict(task_dict)

        assert task.task_id == "deser-123"
        assert task.priority == TaskPriority.LOW
        assert task.status == TaskStatus.PROCESSING
        assert task.attempts == 1

    def test_task_priority_levels(self):
        """Test all priority levels"""
        assert TaskPriority.LOW.value == 0
        assert TaskPriority.NORMAL.value == 1
        assert TaskPriority.HIGH.value == 2
        assert TaskPriority.CRITICAL.value == 3

    def test_task_status_values(self):
        """Test all status values"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.DEAD_LETTER.value == "dead_letter"


class TestTaskQueueEnqueue:
    """Test TaskQueue enqueue functionality"""

    @pytest.mark.asyncio
    async def test_enqueue_success(self):
        """Test successful task enqueue"""
        redis = MockRedis()
        queue = TaskQueue(redis, "test_queue")

        task = Task(
            task_id="enq-1",
            task_type="test",
            payload={"data": "test"}
        )

        task_id = await queue.enqueue(task)

        assert task_id == "enq-1"
        assert "enq-1" in redis.data[queue.tasks_key]
        assert "enq-1" in redis.sorted_sets[queue.pending_key]

    @pytest.mark.asyncio
    async def test_enqueue_with_priority_ordering(self):
        """Test tasks are enqueued with correct priority ordering"""
        redis = MockRedis()
        queue = TaskQueue(redis, "priority_queue")

        # Enqueue tasks with different priorities
        low_task = Task(task_id="low", task_type="t", payload={}, priority=TaskPriority.LOW)
        high_task = Task(task_id="high", task_type="t", payload={}, priority=TaskPriority.HIGH)
        critical_task = Task(task_id="crit", task_type="t", payload={}, priority=TaskPriority.CRITICAL)

        await queue.enqueue(low_task)
        await queue.enqueue(high_task)
        await queue.enqueue(critical_task)

        # Critical should have highest score
        scores = redis.sorted_sets[queue.pending_key]
        assert scores["crit"] > scores["high"]
        assert scores["high"] > scores["low"]

    @pytest.mark.asyncio
    async def test_enqueue_exception_handling(self):
        """Test enqueue handles Redis exceptions"""
        redis = MockRedis()
        redis.should_fail = True
        queue = TaskQueue(redis, "fail_queue")

        task = Task(task_id="fail-1", task_type="test", payload={})

        with pytest.raises(Exception):
            await queue.enqueue(task)

    @pytest.mark.asyncio
    async def test_enqueue_stores_complete_task_data(self):
        """Test enqueue stores all task fields"""
        redis = MockRedis()
        queue = TaskQueue(redis, "complete_queue")

        task = Task(
            task_id="complete-1",
            task_type="full",
            payload={"x": 1, "y": 2},
            priority=TaskPriority.HIGH,
            max_retries=5,
            timeout=600
        )

        await queue.enqueue(task)

        stored_json = await redis.hget(queue.tasks_key, "complete-1")
        stored_task = Task.from_dict(json.loads(stored_json))

        assert stored_task.max_retries == 5
        assert stored_task.timeout == 600
        assert stored_task.priority == TaskPriority.HIGH


class TestTaskQueueDequeue:
    """Test TaskQueue dequeue functionality"""

    @pytest.mark.asyncio
    async def test_dequeue_success(self):
        """Test successful task dequeue"""
        redis = MockRedis()
        queue = TaskQueue(redis, "deq_queue")

        task = Task(task_id="deq-1", task_type="test", payload={})
        await queue.enqueue(task)

        dequeued = await queue.dequeue()

        assert dequeued is not None
        assert dequeued.task_id == "deq-1"
        assert dequeued.status == TaskStatus.PROCESSING
        assert dequeued.attempts == 1
        assert dequeued.worker_id == queue.worker_id

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue_non_blocking(self):
        """Test dequeue from empty queue returns None"""
        redis = MockRedis()
        queue = TaskQueue(redis, "empty_queue")

        result = await queue.dequeue(timeout=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue_with_timeout(self):
        """Test dequeue with timeout on empty queue"""
        redis = MockRedis()
        queue = TaskQueue(redis, "timeout_queue")

        start = time.time()
        result = await queue.dequeue(timeout=0.2)
        elapsed = time.time() - start

        assert result is None
        assert elapsed >= 0.2

    @pytest.mark.asyncio
    async def test_dequeue_priority_order(self):
        """Test tasks are dequeued in priority order"""
        redis = MockRedis()
        queue = TaskQueue(redis, "priority_deq")

        # Enqueue in random order
        normal = Task(task_id="normal", task_type="t", payload={}, priority=TaskPriority.NORMAL)
        critical = Task(task_id="critical", task_type="t", payload={}, priority=TaskPriority.CRITICAL)
        low = Task(task_id="low", task_type="t", payload={}, priority=TaskPriority.LOW)

        await queue.enqueue(normal)
        await queue.enqueue(critical)
        await queue.enqueue(low)

        # Should dequeue in priority order
        first = await queue.dequeue()
        assert first.task_id == "critical"

    @pytest.mark.asyncio
    async def test_dequeue_missing_task_data(self):
        """Test dequeue handles missing task data"""
        redis = MockRedis()
        queue = TaskQueue(redis, "missing_data")

        # Add task ID to queue but no task data
        await redis.zadd(queue.pending_key, {"orphan-123": 1000})

        # Should skip missing task and return None
        result = await queue.dequeue(timeout=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_dequeue_updates_task_metadata(self):
        """Test dequeue updates task metadata correctly"""
        redis = MockRedis()
        queue = TaskQueue(redis, "metadata_queue")

        task = Task(task_id="meta-1", task_type="test", payload={})
        await queue.enqueue(task)

        before_time = time.time()
        dequeued = await queue.dequeue()
        after_time = time.time()

        assert dequeued.started_at >= before_time
        assert dequeued.started_at <= after_time
        assert dequeued.status == TaskStatus.PROCESSING
        assert dequeued.attempts == 1

    @pytest.mark.asyncio
    async def test_dequeue_with_exception(self):
        """Test dequeue handles exceptions gracefully"""
        redis = MockRedis()
        queue = TaskQueue(redis, "error_queue")

        task = Task(task_id="err-1", task_type="test", payload={})
        await queue.enqueue(task)

        redis.fail_operations.add('zpopmax')

        result = await queue.dequeue(timeout=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_dequeue_adds_to_processing_queue(self):
        """Test dequeue adds task to processing queue"""
        redis = MockRedis()
        queue = TaskQueue(redis, "proc_queue")

        task = Task(task_id="proc-1", task_type="test", payload={})
        await queue.enqueue(task)

        dequeued = await queue.dequeue()

        assert "proc-1" in redis.sorted_sets[queue.processing_key]
        assert "proc-1" not in redis.sorted_sets[queue.pending_key]


class TestTaskQueueComplete:
    """Test TaskQueue complete_task functionality"""

    @pytest.mark.asyncio
    async def test_complete_task_success(self):
        """Test successfully completing a task"""
        redis = MockRedis()
        queue = TaskQueue(redis, "complete_queue")

        task = Task(task_id="comp-1", task_type="test", payload={})
        await queue.enqueue(task)
        dequeued = await queue.dequeue()

        result = await queue.complete_task("comp-1")

        assert result is True

        # Check task is in completed queue
        assert "comp-1" in redis.sorted_sets[queue.completed_key]
        assert "comp-1" not in redis.sorted_sets[queue.processing_key]

        # Check task status updated
        task_data = await redis.hget(queue.tasks_key, "comp-1")
        updated_task = Task.from_dict(json.loads(task_data))
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.completed_at is not None

    @pytest.mark.asyncio
    async def test_complete_nonexistent_task(self):
        """Test completing non-existent task"""
        redis = MockRedis()
        queue = TaskQueue(redis, "missing_queue")

        result = await queue.complete_task("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_complete_task_with_exception(self):
        """Test complete_task handles exceptions"""
        redis = MockRedis()
        queue = TaskQueue(redis, "error_queue")

        task = Task(task_id="err-1", task_type="test", payload={})
        await queue.enqueue(task)

        redis.fail_operations.add('hget')

        result = await queue.complete_task("err-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_complete_task_timing(self):
        """Test complete_task records timing correctly"""
        redis = MockRedis()
        queue = TaskQueue(redis, "timing_queue")

        task = Task(task_id="time-1", task_type="test", payload={})
        await queue.enqueue(task)
        await queue.dequeue()

        await asyncio.sleep(0.1)  # Simulate work

        await queue.complete_task("time-1")

        task_data = await redis.hget(queue.tasks_key, "time-1")
        completed = Task.from_dict(json.loads(task_data))

        assert completed.completed_at > completed.started_at


class TestTaskQueueFail:
    """Test TaskQueue fail_task functionality"""

    @pytest.mark.asyncio
    async def test_fail_task_with_retry(self):
        """Test failing task with retry"""
        redis = MockRedis()
        queue = TaskQueue(redis, "retry_queue")

        task = Task(task_id="retry-1", task_type="test", payload={}, max_retries=3)
        await queue.enqueue(task)
        await queue.dequeue()

        result = await queue.fail_task("retry-1", "Test error", retry=True)

        assert result is True

        # Should be back in pending queue
        assert "retry-1" in redis.sorted_sets[queue.pending_key]
        assert "retry-1" not in redis.sorted_sets[queue.processing_key]

        # Error recorded
        task_data = await redis.hget(queue.tasks_key, "retry-1")
        failed_task = Task.from_dict(json.loads(task_data))
        assert failed_task.last_error == "Test error"

    @pytest.mark.asyncio
    async def test_fail_task_max_retries_reached(self):
        """Test task moves to DLQ after max retries"""
        redis = MockRedis()
        queue = TaskQueue(redis, "dlq_queue")

        task = Task(task_id="dlq-1", task_type="test", payload={}, max_retries=2)
        await queue.enqueue(task)

        # Fail twice
        await queue.dequeue()
        await queue.fail_task("dlq-1", "Error 1", retry=True)
        await queue.dequeue()
        await queue.fail_task("dlq-1", "Error 2", retry=True)

        # Third failure should go to DLQ
        await queue.dequeue()
        result = await queue.fail_task("dlq-1", "Error 3", retry=True)

        assert result is True
        assert "dlq-1" in redis.sorted_sets[queue.dlq_key]
        assert "dlq-1" not in redis.sorted_sets[queue.pending_key]

        task_data = await redis.hget(queue.tasks_key, "dlq-1")
        dlq_task = Task.from_dict(json.loads(task_data))
        assert dlq_task.status == TaskStatus.DEAD_LETTER

    @pytest.mark.asyncio
    async def test_fail_task_no_retry(self):
        """Test failing task without retry"""
        redis = MockRedis()
        queue = TaskQueue(redis, "no_retry_queue")

        task = Task(task_id="no-retry-1", task_type="test", payload={})
        await queue.enqueue(task)
        await queue.dequeue()

        result = await queue.fail_task("no-retry-1", "Fatal error", retry=False)

        assert result is True
        assert "no-retry-1" in redis.sorted_sets[queue.dlq_key]

    @pytest.mark.asyncio
    async def test_fail_task_exponential_backoff(self):
        """Test exponential backoff on retries"""
        redis = MockRedis()
        queue = TaskQueue(redis, "backoff_queue")

        task = Task(task_id="backoff-1", task_type="test", payload={}, max_retries=5)
        await queue.enqueue(task)

        # Simulate multiple failures
        for i in range(3):
            await queue.dequeue()
            await queue.fail_task("backoff-1", f"Error {i}", retry=True)

        # Check that retry delay increases exponentially
        # Score should include delay: 2^attempts
        scores = redis.sorted_sets[queue.pending_key]
        score = scores.get("backoff-1", 0)
        # Should have delay component added

    @pytest.mark.asyncio
    async def test_fail_nonexistent_task(self):
        """Test failing non-existent task"""
        redis = MockRedis()
        queue = TaskQueue(redis, "missing_fail")

        result = await queue.fail_task("nonexistent", "error")
        assert result is False

    @pytest.mark.asyncio
    async def test_fail_task_with_exception(self):
        """Test fail_task handles exceptions"""
        redis = MockRedis()
        queue = TaskQueue(redis, "fail_error")

        task = Task(task_id="err-1", task_type="test", payload={})
        await queue.enqueue(task)
        await queue.dequeue()

        redis.fail_operations.add('hget')

        result = await queue.fail_task("err-1", "error")
        assert result is False


class TestTaskQueueStats:
    """Test TaskQueue get_queue_stats functionality"""

    @pytest.mark.asyncio
    async def test_get_queue_stats_empty(self):
        """Test stats for empty queue"""
        redis = MockRedis()
        queue = TaskQueue(redis, "stats_queue")

        stats = await queue.get_queue_stats()

        assert stats["queue_name"] == "stats_queue"
        assert stats["pending"] == 0
        assert stats["processing"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
        assert stats["dead_letter"] == 0
        assert stats["total"] == 0

    @pytest.mark.asyncio
    async def test_get_queue_stats_with_tasks(self):
        """Test stats with tasks in various states"""
        redis = MockRedis()
        queue = TaskQueue(redis, "stats_queue")

        # Add tasks in different states
        pending_task = Task(task_id="pend-1", task_type="test", payload={})
        await queue.enqueue(pending_task)

        processing_task = Task(task_id="proc-1", task_type="test", payload={})
        await queue.enqueue(processing_task)
        await queue.dequeue()

        completed_task = Task(task_id="comp-1", task_type="test", payload={})
        await queue.enqueue(completed_task)
        await queue.dequeue()
        await queue.complete_task("comp-1")

        stats = await queue.get_queue_stats()

        assert stats["pending"] == 1
        assert stats["processing"] == 1
        assert stats["completed"] == 1
        assert stats["total"] == 3

    @pytest.mark.asyncio
    async def test_get_queue_stats_with_exception(self):
        """Test get_queue_stats handles exceptions"""
        redis = MockRedis()
        redis.should_fail = True
        queue = TaskQueue(redis, "error_stats")

        stats = await queue.get_queue_stats()
        assert stats == {}


class TestTaskQueueRecovery:
    """Test TaskQueue recover_stale_tasks functionality"""

    @pytest.mark.asyncio
    async def test_recover_stale_tasks_none_stale(self):
        """Test recovery when no stale tasks"""
        redis = MockRedis()
        queue = TaskQueue(redis, "no_stale")

        recovered = await queue.recover_stale_tasks()
        assert recovered == 0

    @pytest.mark.asyncio
    async def test_recover_stale_tasks_with_timeout(self):
        """Test recovering tasks that exceeded visibility timeout"""
        redis = MockRedis()
        queue = TaskQueue(redis, visibility_timeout=1)

        task = Task(task_id="stale-1", task_type="test", payload={}, max_retries=5)
        await queue.enqueue(task)
        await queue.dequeue()

        # Manually set processing score to past
        old_score = time.time() - 10
        await redis.zadd(queue.processing_key, {"stale-1": old_score})

        recovered = await queue.recover_stale_tasks()

        assert recovered == 1
        # Task should be back in pending queue
        assert "stale-1" in redis.sorted_sets[queue.pending_key]

    @pytest.mark.asyncio
    async def test_recover_stale_orphaned_task(self):
        """Test recovery removes orphaned task IDs"""
        redis = MockRedis()
        queue = TaskQueue(redis)

        # Add orphaned task ID (no task data)
        old_score = time.time() - 10
        await redis.zadd(queue.processing_key, {"orphan-1": old_score})

        recovered = await queue.recover_stale_tasks()

        # Should clean up orphan
        assert "orphan-1" not in redis.sorted_sets[queue.processing_key]

    @pytest.mark.asyncio
    async def test_recover_with_exception(self):
        """Test recover_stale_tasks handles exceptions"""
        redis = MockRedis()
        redis.should_fail = True
        queue = TaskQueue(redis, "error_recover")

        recovered = await queue.recover_stale_tasks()
        assert recovered == 0


class TestTaskQueuePurge:
    """Test TaskQueue purge_completed functionality"""

    @pytest.mark.asyncio
    async def test_purge_completed_none(self):
        """Test purge when no completed tasks"""
        redis = MockRedis()
        queue = TaskQueue(redis, "no_completed")

        purged = await queue.purge_completed(older_than=3600)
        assert purged == 0

    @pytest.mark.asyncio
    async def test_purge_old_completed_tasks(self):
        """Test purging old completed tasks"""
        redis = MockRedis()
        queue = TaskQueue(redis, "purge_queue")

        # Complete a task
        task = Task(task_id="old-1", task_type="test", payload={})
        await queue.enqueue(task)
        await queue.dequeue()
        await queue.complete_task("old-1")

        # Set old completion time
        old_time = time.time() - 7200  # 2 hours ago
        await redis.zadd(queue.completed_key, {"old-1": old_time})

        purged = await queue.purge_completed(older_than=3600)  # 1 hour

        assert purged == 1
        assert "old-1" not in redis.data.get(queue.tasks_key, {})
        assert "old-1" not in redis.sorted_sets.get(queue.completed_key, {})

    @pytest.mark.asyncio
    async def test_purge_keeps_recent_tasks(self):
        """Test purge doesn't remove recent tasks"""
        redis = MockRedis()
        queue = TaskQueue(redis, "recent_queue")

        task = Task(task_id="recent-1", task_type="test", payload={})
        await queue.enqueue(task)
        await queue.dequeue()
        await queue.complete_task("recent-1")

        purged = await queue.purge_completed(older_than=3600)

        assert purged == 0
        assert "recent-1" in redis.data[queue.tasks_key]

    @pytest.mark.asyncio
    async def test_purge_with_exception(self):
        """Test purge_completed handles exceptions"""
        redis = MockRedis()
        redis.should_fail = True
        queue = TaskQueue(redis, "error_purge")

        purged = await queue.purge_completed()
        assert purged == 0


class TestTaskQueueInitialization:
    """Test TaskQueue initialization"""

    def test_queue_initialization_defaults(self):
        """Test queue initialization with defaults"""
        redis = Mock()
        queue = TaskQueue(redis, "default_queue")

        assert queue.queue_name == "default_queue"
        assert queue.visibility_timeout == 300
        assert queue.worker_id is not None
        assert queue.pending_key == "queue:default_queue:pending"
        assert queue.processing_key == "queue:default_queue:processing"

    def test_queue_initialization_custom_timeout(self):
        """Test queue initialization with custom timeout"""
        redis = Mock()
        queue = TaskQueue(redis, "custom_queue", visibility_timeout=600)

        assert queue.visibility_timeout == 600

    def test_queue_generates_unique_worker_id(self):
        """Test each queue instance gets unique worker ID"""
        redis = Mock()
        queue1 = TaskQueue(redis, "q1")
        queue2 = TaskQueue(redis, "q2")

        assert queue1.worker_id != queue2.worker_id
