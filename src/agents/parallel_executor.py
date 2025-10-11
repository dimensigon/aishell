"""
Parallel Agent Executor

Executes multiple agents concurrently with synchronization, result aggregation,
and failure handling strategies.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Parallel task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AggregationStrategy(Enum):
    """Result aggregation strategies"""
    ALL = "all"  # Wait for all tasks
    FIRST = "first"  # Return first completed
    MAJORITY = "majority"  # Wait for majority to complete
    THRESHOLD = "threshold"  # Wait for N tasks to complete


@dataclass
class ParallelTask:
    """Represents a task for parallel execution"""
    agent_type: str
    task: str
    name: Optional[str] = None
    priority: int = 0
    timeout: int = 180
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Runtime fields
    task_id: str = field(default_factory=lambda: str(uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: float = 0.0

    def get_name(self) -> str:
        """Get task name or generate from agent type"""
        return self.name or f"{self.agent_type}_task"


@dataclass
class ExecutionResult:
    """Result of parallel execution"""
    execution_id: str
    strategy: AggregationStrategy
    total_tasks: int
    completed: int
    failed: int
    cancelled: int
    tasks: List[ParallelTask]
    results: List[Any]
    errors: List[str]
    start_time: datetime
    end_time: datetime
    total_duration: float
    max_duration: float
    min_duration: float
    avg_duration: float

    def is_successful(self) -> bool:
        """Check if execution was successful"""
        return self.failed == 0 and self.completed > 0

    def get_task_result(self, task_name: str) -> Optional[Any]:
        """Get result from specific task by name"""
        for task in self.tasks:
            if task.get_name() == task_name:
                return task.result
        return None

    def get_successful_results(self) -> List[Any]:
        """Get all successful task results"""
        return [
            task.result for task in self.tasks
            if task.status == TaskStatus.COMPLETED and task.result is not None
        ]


class ParallelExecutor:
    """
    Executes multiple agents concurrently with configurable concurrency limits,
    aggregation strategies, and failure handling.
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        strategy: AggregationStrategy = AggregationStrategy.ALL,
        threshold: Optional[int] = None
    ):
        self.max_concurrent = max_concurrent
        self.strategy = strategy
        self.threshold = threshold
        self.execution_id = str(uuid4())
        self.tasks: List[ParallelTask] = []

        logger.info(
            f"Initialized parallel executor "
            f"(max_concurrent={max_concurrent}, strategy={strategy})"
        )

    def add_task(self, task: ParallelTask) -> 'ParallelExecutor':
        """Add a task to the execution queue"""
        self.tasks.append(task)
        logger.debug(f"Added task '{task.get_name()}' to executor")
        return self

    def add_tasks(self, tasks: List[ParallelTask]) -> 'ParallelExecutor':
        """Add multiple tasks to the execution queue"""
        self.tasks.extend(tasks)
        logger.debug(f"Added {len(tasks)} tasks to executor")
        return self

    def create_task(
        self,
        agent_type: str,
        task: str,
        name: Optional[str] = None,
        priority: int = 0,
        timeout: int = 180,
        **metadata
    ) -> 'ParallelExecutor':
        """
        Create and add a task in one call

        Example:
            executor.create_task("researcher", "Analyze data")
                    .create_task("coder", "Implement feature")
        """
        parallel_task = ParallelTask(
            agent_type=agent_type,
            task=task,
            name=name,
            priority=priority,
            timeout=timeout,
            metadata=metadata
        )
        return self.add_task(parallel_task)

    async def _execute_task(
        self,
        task: ParallelTask,
        agent_executor: Callable[[str, str], Any],
        semaphore: asyncio.Semaphore
    ) -> ParallelTask:
        """Execute a single task with concurrency control"""
        async with semaphore:
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()

            logger.info(f"Executing task '{task.get_name()}' ({task.agent_type})")

            try:
                result = await asyncio.wait_for(
                    agent_executor(task.agent_type, task.task),
                    timeout=task.timeout
                )

                task.result = result
                task.status = TaskStatus.COMPLETED
                logger.info(f"Task '{task.get_name()}' completed successfully")

            except asyncio.TimeoutError:
                error_msg = f"Task '{task.get_name()}' timed out after {task.timeout}s"
                logger.error(error_msg)
                task.error = error_msg
                task.status = TaskStatus.FAILED

            except asyncio.CancelledError:
                logger.warning(f"Task '{task.get_name()}' was cancelled")
                task.status = TaskStatus.CANCELLED
                raise

            except Exception as e:
                error_msg = f"Task '{task.get_name()}' failed: {str(e)}"
                logger.error(error_msg)
                task.error = error_msg
                task.status = TaskStatus.FAILED

            finally:
                task.end_time = datetime.now()
                task.duration = (task.end_time - task.start_time).total_seconds()

            return task

    async def execute(
        self,
        agent_executor: Callable[[str, str], Any]
    ) -> ExecutionResult:
        """
        Execute all tasks according to the aggregation strategy

        Args:
            agent_executor: Async function that executes agent tasks

        Returns:
            ExecutionResult with execution details
        """
        start_time = datetime.now()
        logger.info(
            f"Starting parallel execution: {len(self.tasks)} tasks "
            f"(strategy={self.strategy})"
        )

        if not self.tasks:
            raise ValueError("No tasks to execute")

        # Sort by priority (higher priority first)
        sorted_tasks = sorted(self.tasks, key=lambda t: t.priority, reverse=True)

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Create task coroutines
        task_coros = [
            self._execute_task(task, agent_executor, semaphore)
            for task in sorted_tasks
        ]

        # Execute based on strategy
        if self.strategy == AggregationStrategy.ALL:
            # Wait for all tasks
            completed_tasks = await asyncio.gather(*task_coros, return_exceptions=True)

        elif self.strategy == AggregationStrategy.FIRST:
            # Return when first task completes
            done, pending = await asyncio.wait(
                task_coros,
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel remaining tasks
            for task in pending:
                task.cancel()

            completed_tasks = [t.result() for t in done]

        elif self.strategy == AggregationStrategy.MAJORITY:
            # Wait for majority to complete
            majority = len(self.tasks) // 2 + 1
            done, pending = await asyncio.wait(
                task_coros,
                return_when=asyncio.FIRST_COMPLETED
            )

            while len(done) < majority and pending:
                newly_done, pending = await asyncio.wait(
                    pending,
                    return_when=asyncio.FIRST_COMPLETED
                )
                done.update(newly_done)

            # Cancel remaining
            for task in pending:
                task.cancel()

            completed_tasks = [t.result() for t in done]

        elif self.strategy == AggregationStrategy.THRESHOLD:
            # Wait for N tasks to complete
            if self.threshold is None:
                raise ValueError("Threshold must be set for THRESHOLD strategy")

            threshold = min(self.threshold, len(self.tasks))
            done, pending = await asyncio.wait(
                task_coros,
                return_when=asyncio.FIRST_COMPLETED
            )

            while len(done) < threshold and pending:
                newly_done, pending = await asyncio.wait(
                    pending,
                    return_when=asyncio.FIRST_COMPLETED
                )
                done.update(newly_done)

            # Cancel remaining
            for task in pending:
                task.cancel()

            completed_tasks = [t.result() for t in done]

        else:
            raise ValueError(f"Unknown aggregation strategy: {self.strategy}")

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        # Process results
        results = []
        errors = []
        completed = 0
        failed = 0
        cancelled = 0
        durations = []

        for item in completed_tasks:
            if isinstance(item, ParallelTask):
                if item.status == TaskStatus.COMPLETED:
                    completed += 1
                    if item.result is not None:
                        results.append(item.result)
                    if item.duration > 0:
                        durations.append(item.duration)
                elif item.status == TaskStatus.FAILED:
                    failed += 1
                    if item.error:
                        errors.append(item.error)
                elif item.status == TaskStatus.CANCELLED:
                    cancelled += 1
            elif isinstance(item, Exception):
                failed += 1
                errors.append(str(item))

        # Calculate duration statistics
        max_dur = max(durations) if durations else 0.0
        min_dur = min(durations) if durations else 0.0
        avg_dur = sum(durations) / len(durations) if durations else 0.0

        result = ExecutionResult(
            execution_id=self.execution_id,
            strategy=self.strategy,
            total_tasks=len(self.tasks),
            completed=completed,
            failed=failed,
            cancelled=cancelled,
            tasks=self.tasks.copy(),
            results=results,
            errors=errors,
            start_time=start_time,
            end_time=end_time,
            total_duration=total_duration,
            max_duration=max_dur,
            min_duration=min_dur,
            avg_duration=avg_dur
        )

        logger.info(
            f"Parallel execution completed: "
            f"{completed} completed, {failed} failed, {cancelled} cancelled "
            f"({total_duration:.2f}s total, {avg_dur:.2f}s avg)"
        )

        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of executor configuration"""
        return {
            "execution_id": self.execution_id,
            "max_concurrent": self.max_concurrent,
            "strategy": self.strategy.value,
            "threshold": self.threshold,
            "total_tasks": len(self.tasks),
            "tasks": [
                {
                    "name": task.get_name(),
                    "agent_type": task.agent_type,
                    "priority": task.priority,
                    "status": task.status.value
                }
                for task in self.tasks
            ]
        }
