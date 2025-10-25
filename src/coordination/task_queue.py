"""
Distributed Task Queue

Redis-based distributed task queue for coordinating work across multiple instances
with priority handling, retries, and dead letter queue.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskStatus(Enum):
    """Task status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass
class Task:
    """Distributed task definition"""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    timeout: int = 300
    created_at: float = field(default_factory=time.time)

    # Runtime fields
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    last_error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    worker_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary"""
        data = data.copy()
        data['priority'] = TaskPriority(data['priority'])
        data['status'] = TaskStatus(data['status'])
        return cls(**data)


class TaskQueue:
    """
    Distributed task queue using Redis sorted sets for priority handling.

    Features:
    - Priority-based task scheduling
    - Automatic retry with exponential backoff
    - Dead letter queue for failed tasks
    - Task visibility timeout
    - Worker health monitoring
    """

    def __init__(
        self,
        redis_client: any,
        queue_name: str = "default",
        visibility_timeout: int = 300
    ):
        """
        Initialize task queue

        Args:
            redis_client: Redis client instance
            queue_name: Name of the queue
            visibility_timeout: Task visibility timeout in seconds
        """
        self.redis = redis_client
        self.queue_name = queue_name
        self.visibility_timeout = visibility_timeout
        self.worker_id = str(uuid4())

        # Redis keys
        self.pending_key = f"queue:{queue_name}:pending"
        self.processing_key = f"queue:{queue_name}:processing"
        self.completed_key = f"queue:{queue_name}:completed"
        self.failed_key = f"queue:{queue_name}:failed"
        self.dlq_key = f"queue:{queue_name}:dlq"
        self.tasks_key = f"queue:{queue_name}:tasks"

        logger.info(
            f"Initialized task queue '{queue_name}' "
            f"(worker_id={self.worker_id[:8]}...)"
        )

    async def enqueue(self, task: Task) -> str:
        """
        Add task to queue

        Args:
            task: Task to enqueue

        Returns:
            Task ID
        """
        try:
            # Store task data
            await self.redis.hset(
                self.tasks_key,
                task.task_id,
                json.dumps(task.to_dict())
            )

            # Add to pending queue with priority as score
            score = task.priority.value * 1000000 + time.time()
            await self.redis.zadd(self.pending_key, {task.task_id: score})

            logger.info(
                f"Enqueued task {task.task_id} "
                f"(type={task.task_type}, priority={task.priority.name})"
            )

            return task.task_id

        except Exception as e:
            logger.error(f"Failed to enqueue task: {e}")
            raise

    async def dequeue(
        self,
        timeout: Optional[float] = None
    ) -> Optional[Task]:
        """
        Dequeue next task

        Args:
            timeout: Wait timeout in seconds (None = non-blocking)

        Returns:
            Task or None if queue is empty
        """
        start_time = time.time()

        while True:
            try:
                # Get highest priority pending task
                result = await self.redis.zpopmax(self.pending_key)

                if not result:
                    # No tasks available
                    if timeout is None or (time.time() - start_time) >= timeout:
                        return None

                    # Wait and retry
                    await asyncio.sleep(0.1)
                    continue

                task_id, _ = result[0]
                task_id = task_id.decode() if isinstance(task_id, bytes) else task_id

                # Get task data
                task_data = await self.redis.hget(self.tasks_key, task_id)
                if not task_data:
                    logger.warning(f"Task data not found for {task_id}")
                    continue

                task_dict = json.loads(task_data)
                task = Task.from_dict(task_dict)

                # Mark as processing
                task.status = TaskStatus.PROCESSING
                task.started_at = time.time()
                task.worker_id = self.worker_id
                task.attempts += 1

                await self.redis.hset(
                    self.tasks_key,
                    task.task_id,
                    json.dumps(task.to_dict())
                )

                # Add to processing queue with timeout score
                timeout_score = time.time() + self.visibility_timeout
                await self.redis.zadd(
                    self.processing_key,
                    {task.task_id: timeout_score}
                )

                logger.info(
                    f"Dequeued task {task.task_id} "
                    f"(type={task.task_type}, attempt={task.attempts})"
                )

                return task

            except Exception as e:
                logger.error(f"Error dequeuing task: {e}")
                if timeout is None or (time.time() - start_time) >= timeout:
                    return None

                await asyncio.sleep(0.1)

    async def complete_task(self, task_id: str, result: Any = None) -> bool:
        """
        Mark task as completed

        Args:
            task_id: Task ID
            result: Task result (optional)

        Returns:
            True if completed successfully
        """
        try:
            # Get task data
            task_data = await self.redis.hget(self.tasks_key, task_id)
            if not task_data:
                logger.warning(f"Task {task_id} not found")
                return False

            task_dict = json.loads(task_data)
            task = Task.from_dict(task_dict)

            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()

            # Store updated task
            await self.redis.hset(
                self.tasks_key,
                task_id,
                json.dumps(task.to_dict())
            )

            # Remove from processing queue
            await self.redis.zrem(self.processing_key, task_id)

            # Add to completed queue
            await self.redis.zadd(
                self.completed_key,
                {task_id: task.completed_at}
            )

            duration = task.completed_at - task.started_at if task.started_at else 0
            logger.info(
                f"Completed task {task_id} "
                f"(duration={duration:.2f}s, attempts={task.attempts})"
            )

            return True

        except Exception as e:
            logger.error(f"Error completing task: {e}")
            return False

    async def fail_task(
        self,
        task_id: str,
        error: str,
        retry: bool = True
    ) -> bool:
        """
        Mark task as failed

        Args:
            task_id: Task ID
            error: Error message
            retry: Retry task if retries remaining

        Returns:
            True if handled successfully
        """
        try:
            # Get task data
            task_data = await self.redis.hget(self.tasks_key, task_id)
            if not task_data:
                logger.warning(f"Task {task_id} not found")
                return False

            task_dict = json.loads(task_data)
            task = Task.from_dict(task_dict)

            # Update task with error
            task.last_error = error

            # Remove from processing queue
            await self.redis.zrem(self.processing_key, task_id)

            # Check if should retry
            if retry and task.attempts < task.max_retries:
                # Re-queue with exponential backoff
                delay = 2 ** task.attempts
                score = (task.priority.value * 1000000 +
                        time.time() + delay)

                task.status = TaskStatus.PENDING

                await self.redis.hset(
                    self.tasks_key,
                    task_id,
                    json.dumps(task.to_dict())
                )

                await self.redis.zadd(self.pending_key, {task_id: score})

                logger.warning(
                    f"Task {task_id} failed, retrying in {delay}s "
                    f"(attempt {task.attempts}/{task.max_retries}): {error}"
                )

            else:
                # Move to dead letter queue
                task.status = TaskStatus.DEAD_LETTER
                task.completed_at = time.time()

                await self.redis.hset(
                    self.tasks_key,
                    task_id,
                    json.dumps(task.to_dict())
                )

                await self.redis.zadd(
                    self.dlq_key,
                    {task_id: task.completed_at}
                )

                logger.error(
                    f"Task {task_id} moved to dead letter queue "
                    f"after {task.attempts} attempts: {error}"
                )

            return True

        except Exception as e:
            logger.error(f"Error failing task: {e}")
            return False

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            pending = await self.redis.zcard(self.pending_key)
            processing = await self.redis.zcard(self.processing_key)
            completed = await self.redis.zcard(self.completed_key)
            failed = await self.redis.zcard(self.failed_key)
            dlq = await self.redis.zcard(self.dlq_key)

            return {
                "queue_name": self.queue_name,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "dead_letter": dlq,
                "total": pending + processing + completed + failed + dlq
            }

        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}

    async def recover_stale_tasks(self) -> int:
        """
        Recover tasks stuck in processing state

        Returns:
            Number of tasks recovered
        """
        try:
            current_time = time.time()

            # Get all processing tasks with timeout < now
            stale_tasks = await self.redis.zrangebyscore(
                self.processing_key,
                0,
                current_time
            )

            recovered = 0
            for task_id in stale_tasks:
                task_id = task_id.decode() if isinstance(task_id, bytes) else task_id

                # Get task data
                task_data = await self.redis.hget(self.tasks_key, task_id)
                if not task_data:
                    await self.redis.zrem(self.processing_key, task_id)
                    continue

                task_dict = json.loads(task_data)
                task = Task.from_dict(task_dict)

                # Re-queue task
                await self.fail_task(
                    task_id,
                    "Task timed out (visibility timeout exceeded)",
                    retry=True
                )
                recovered += 1

            if recovered > 0:
                logger.info(f"Recovered {recovered} stale tasks")

            return recovered

        except Exception as e:
            logger.error(f"Error recovering stale tasks: {e}")
            return 0

    async def purge_completed(self, older_than: int = 3600) -> int:
        """
        Purge old completed tasks

        Args:
            older_than: Purge tasks completed more than N seconds ago

        Returns:
            Number of tasks purged
        """
        try:
            cutoff_time = time.time() - older_than

            # Get old completed tasks
            old_tasks = await self.redis.zrangebyscore(
                self.completed_key,
                0,
                cutoff_time
            )

            purged = 0
            for task_id in old_tasks:
                task_id = task_id.decode() if isinstance(task_id, bytes) else task_id

                await self.redis.hdel(self.tasks_key, task_id)
                await self.redis.zrem(self.completed_key, task_id)
                purged += 1

            if purged > 0:
                logger.info(f"Purged {purged} completed tasks")

            return purged

        except Exception as e:
            logger.error(f"Error purging completed tasks: {e}")
            return 0
