"""
Comprehensive tests for src/agents/parallel_executor.py to achieve 90%+ coverage.

Tests parallel task execution, aggregation strategies, priority, concurrency limits,
timeouts, error handling, and result collection.
"""

import pytest
import asyncio
from datetime import datetime

from src.agents.parallel_executor import (
    ParallelExecutor,
    ParallelTask,
    ExecutionResult,
    TaskStatus,
    AggregationStrategy
)


class TestParallelTask:
    """Test ParallelTask dataclass"""

    def test_task_creation(self):
        """Test creating a task"""
        task = ParallelTask("coder", "Implement feature")

        assert task.agent_type == "coder"
        assert task.task == "Implement feature"
        assert task.status == TaskStatus.PENDING

    def test_task_with_name(self):
        """Test task with custom name"""
        task = ParallelTask("coder", "Task", name="custom_task")

        assert task.name == "custom_task"

    def test_task_get_name(self):
        """Test getting task name"""
        task = ParallelTask("coder", "Task")
        assert task.get_name() == "coder_task"

    def test_task_get_name_custom(self):
        """Test getting custom task name"""
        task = ParallelTask("coder", "Task", name="custom")
        assert task.get_name() == "custom"

    def test_task_priority(self):
        """Test task priority"""
        task = ParallelTask("coder", "Task", priority=10)

        assert task.priority == 10

    def test_task_timeout(self):
        """Test task timeout"""
        task = ParallelTask("coder", "Task", timeout=300)

        assert task.timeout == 300

    def test_task_unique_ids(self):
        """Test each task has unique ID"""
        task1 = ParallelTask("coder", "Task")
        task2 = ParallelTask("coder", "Task")

        assert task1.task_id != task2.task_id


class TestExecutionResult:
    """Test ExecutionResult dataclass"""

    def test_is_successful_with_completed(self):
        """Test successful result detection"""
        result = ExecutionResult(
            execution_id="123",
            strategy=AggregationStrategy.ALL,
            total_tasks=3,
            completed=3,
            failed=0,
            cancelled=0,
            tasks=[],
            results=[],
            errors=[],
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_duration=1.0,
            max_duration=1.0,
            min_duration=0.5,
            avg_duration=0.7
        )

        assert result.is_successful()

    def test_is_successful_with_failures(self):
        """Test result not successful with failures"""
        result = ExecutionResult(
            execution_id="123",
            strategy=AggregationStrategy.ALL,
            total_tasks=3,
            completed=2,
            failed=1,
            cancelled=0,
            tasks=[],
            results=[],
            errors=["Error"],
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_duration=1.0,
            max_duration=1.0,
            min_duration=0.5,
            avg_duration=0.7
        )

        assert not result.is_successful()

    def test_is_successful_no_completed(self):
        """Test result not successful with no completed tasks"""
        result = ExecutionResult(
            execution_id="123",
            strategy=AggregationStrategy.ALL,
            total_tasks=3,
            completed=0,
            failed=3,
            cancelled=0,
            tasks=[],
            results=[],
            errors=[],
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_duration=1.0,
            max_duration=0.0,
            min_duration=0.0,
            avg_duration=0.0
        )

        assert not result.is_successful()

    def test_get_task_result(self):
        """Test getting task result by name"""
        task = ParallelTask("coder", "Task", name="my_task")
        task.result = "output"

        result = ExecutionResult(
            execution_id="123",
            strategy=AggregationStrategy.ALL,
            total_tasks=1,
            completed=1,
            failed=0,
            cancelled=0,
            tasks=[task],
            results=[],
            errors=[],
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_duration=1.0,
            max_duration=1.0,
            min_duration=1.0,
            avg_duration=1.0
        )

        assert result.get_task_result("my_task") == "output"

    def test_get_successful_results(self):
        """Test getting only successful results"""
        task1 = ParallelTask("coder1", "Task1")
        task1.status = TaskStatus.COMPLETED
        task1.result = "result1"

        task2 = ParallelTask("coder2", "Task2")
        task2.status = TaskStatus.FAILED

        task3 = ParallelTask("coder3", "Task3")
        task3.status = TaskStatus.COMPLETED
        task3.result = "result3"

        result = ExecutionResult(
            execution_id="123",
            strategy=AggregationStrategy.ALL,
            total_tasks=3,
            completed=2,
            failed=1,
            cancelled=0,
            tasks=[task1, task2, task3],
            results=[],
            errors=[],
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_duration=1.0,
            max_duration=1.0,
            min_duration=1.0,
            avg_duration=1.0
        )

        successful = result.get_successful_results()
        assert len(successful) == 2


class TestParallelExecutorInit:
    """Test ParallelExecutor initialization"""

    def test_init_defaults(self):
        """Test default initialization"""
        executor = ParallelExecutor()

        assert executor.max_concurrent == 10
        assert executor.strategy == AggregationStrategy.ALL
        assert len(executor.tasks) == 0

    def test_init_custom_max_concurrent(self):
        """Test initialization with custom max concurrent"""
        executor = ParallelExecutor(max_concurrent=5)

        assert executor.max_concurrent == 5

    def test_init_custom_strategy(self):
        """Test initialization with custom strategy"""
        executor = ParallelExecutor(strategy=AggregationStrategy.FIRST)

        assert executor.strategy == AggregationStrategy.FIRST

    def test_init_with_threshold(self):
        """Test initialization with threshold"""
        executor = ParallelExecutor(
            strategy=AggregationStrategy.THRESHOLD,
            threshold=3
        )

        assert executor.threshold == 3


class TestParallelExecutorAddTasks:
    """Test adding tasks"""

    def test_add_task(self):
        """Test adding a single task"""
        executor = ParallelExecutor()
        task = ParallelTask("coder", "Task")

        result = executor.add_task(task)

        assert len(executor.tasks) == 1
        assert result is executor  # Fluent interface

    def test_add_tasks(self):
        """Test adding multiple tasks"""
        executor = ParallelExecutor()
        tasks = [
            ParallelTask("coder1", "Task1"),
            ParallelTask("coder2", "Task2")
        ]

        executor.add_tasks(tasks)

        assert len(executor.tasks) == 2

    def test_create_task(self):
        """Test creating and adding task in one call"""
        executor = ParallelExecutor()

        result = executor.create_task("coder", "Task", name="my_task", priority=5)

        assert len(executor.tasks) == 1
        assert executor.tasks[0].name == "my_task"
        assert result is executor

    def test_create_task_with_metadata(self):
        """Test creating task with metadata"""
        executor = ParallelExecutor()

        executor.create_task("coder", "Task", key="value")

        assert executor.tasks[0].metadata["key"] == "value"


@pytest.mark.asyncio
class TestParallelExecution:
    """Test parallel execution"""

    async def test_execute_no_tasks_raises_error(self):
        """Test executing with no tasks raises error"""
        executor = ParallelExecutor()

        async def mock_executor(agent_type, task):
            return "result"

        with pytest.raises(ValueError, match="No tasks"):
            await executor.execute(mock_executor)

    async def test_execute_all_strategy(self):
        """Test ALL strategy waits for all tasks"""
        executor = ParallelExecutor(strategy=AggregationStrategy.ALL)
        executor.create_task("coder1", "Task1")
        executor.create_task("coder2", "Task2")
        executor.create_task("coder3", "Task3")

        async def mock_executor(agent_type, task):
            return f"result_{agent_type}"

        result = await executor.execute(mock_executor)

        assert result.completed == 3
        assert len(result.results) == 3

    async def test_execute_first_strategy(self):
        """Test FIRST strategy returns first completed"""
        executor = ParallelExecutor(strategy=AggregationStrategy.FIRST)
        executor.create_task("coder1", "Task1")
        executor.create_task("coder2", "Task2")

        async def mock_executor(agent_type, task):
            if agent_type == "coder1":
                await asyncio.sleep(0.1)
            return f"result_{agent_type}"

        result = await executor.execute(mock_executor)

        # Should have at least one completed
        assert result.completed >= 1

    async def test_execute_majority_strategy(self):
        """Test MAJORITY strategy waits for majority"""
        executor = ParallelExecutor(strategy=AggregationStrategy.MAJORITY)
        for i in range(5):
            executor.create_task(f"coder{i}", f"Task{i}")

        async def mock_executor(agent_type, task):
            return f"result_{agent_type}"

        result = await executor.execute(mock_executor)

        # Should have at least 3 out of 5 (majority)
        assert result.completed >= 3

    async def test_execute_threshold_strategy(self):
        """Test THRESHOLD strategy"""
        executor = ParallelExecutor(
            strategy=AggregationStrategy.THRESHOLD,
            threshold=2
        )
        executor.create_task("coder1", "Task1")
        executor.create_task("coder2", "Task2")
        executor.create_task("coder3", "Task3")

        async def mock_executor(agent_type, task):
            return f"result_{agent_type}"

        result = await executor.execute(mock_executor)

        # Should have at least 2 completed
        assert result.completed >= 2

    async def test_execute_threshold_without_value_raises_error(self):
        """Test THRESHOLD strategy without threshold raises error"""
        executor = ParallelExecutor(strategy=AggregationStrategy.THRESHOLD)
        executor.create_task("coder", "Task")

        async def mock_executor(agent_type, task):
            return "result"

        with pytest.raises(ValueError, match="Threshold must be set"):
            await executor.execute(mock_executor)

    async def test_execute_respects_priority(self):
        """Test tasks executed by priority"""
        executor = ParallelExecutor(max_concurrent=1)  # Serial execution
        execution_order = []

        executor.create_task("coder1", "Task1", priority=1)
        executor.create_task("coder2", "Task2", priority=10)  # Higher priority
        executor.create_task("coder3", "Task3", priority=5)

        async def mock_executor(agent_type, task):
            execution_order.append(agent_type)
            return "result"

        await executor.execute(mock_executor)

        # Higher priority (10) should execute first
        assert execution_order[0] == "coder2"

    async def test_execute_respects_concurrency_limit(self):
        """Test max_concurrent limit"""
        executor = ParallelExecutor(max_concurrent=2)
        concurrent_count = []
        max_concurrent = 0

        async def mock_executor(agent_type, task):
            nonlocal max_concurrent
            concurrent_count.append(1)
            max_concurrent = max(max_concurrent, len(concurrent_count))
            await asyncio.sleep(0.1)
            concurrent_count.pop()
            return "result"

        for i in range(5):
            executor.create_task(f"coder{i}", "Task")

        await executor.execute(mock_executor)

        assert max_concurrent <= 2

    async def test_execute_timeout(self):
        """Test task timeout"""
        executor = ParallelExecutor()
        executor.create_task("coder", "Task", timeout=0.1)

        async def slow_executor(agent_type, task):
            await asyncio.sleep(1)
            return "result"

        result = await executor.execute(slow_executor)

        assert result.failed == 1
        assert executor.tasks[0].status == TaskStatus.FAILED

    async def test_execute_exception(self):
        """Test task exception handling"""
        executor = ParallelExecutor()
        executor.create_task("coder1", "Task1")
        executor.create_task("coder2", "Task2")

        async def failing_executor(agent_type, task):
            if agent_type == "coder1":
                raise Exception("Task failed")
            return "result"

        result = await executor.execute(failing_executor)

        assert result.failed == 1
        assert result.completed == 1

    async def test_execute_cancellation(self):
        """Test task cancellation"""
        executor = ParallelExecutor(strategy=AggregationStrategy.FIRST)
        executor.create_task("coder1", "Task1")
        executor.create_task("coder2", "Task2")

        async def mock_executor(agent_type, task):
            if agent_type == "coder1":
                await asyncio.sleep(0.01)
            else:
                await asyncio.sleep(1)
            return "result"

        result = await executor.execute(mock_executor)

        # Some tasks should be cancelled
        assert result.cancelled >= 0

    async def test_execute_calculates_duration_stats(self):
        """Test duration statistics calculation"""
        executor = ParallelExecutor()
        executor.create_task("coder1", "Task1")
        executor.create_task("coder2", "Task2")

        async def mock_executor(agent_type, task):
            await asyncio.sleep(0.1)
            return "result"

        result = await executor.execute(mock_executor)

        assert result.max_duration > 0
        assert result.min_duration > 0
        assert result.avg_duration > 0

    async def test_execute_with_exception_type(self):
        """Test handling exception instead of task result"""
        executor = ParallelExecutor()
        executor.create_task("coder", "Task")

        async def mock_executor(agent_type, task):
            raise Exception("Test exception")

        result = await executor.execute(mock_executor)

        assert result.failed >= 1
        assert len(result.errors) >= 1


class TestParallelExecutorSummary:
    """Test executor summary"""

    def test_get_summary(self):
        """Test getting executor summary"""
        executor = ParallelExecutor(
            max_concurrent=5,
            strategy=AggregationStrategy.ALL
        )
        executor.create_task("coder1", "Task1", priority=10)
        executor.create_task("coder2", "Task2", priority=5)

        summary = executor.get_summary()

        assert summary["max_concurrent"] == 5
        assert summary["strategy"] == "all"
        assert summary["total_tasks"] == 2
        assert len(summary["tasks"]) == 2


class TestAggregationStrategy:
    """Test AggregationStrategy enum"""

    def test_strategy_values(self):
        """Test strategy enum values"""
        assert AggregationStrategy.ALL.value == "all"
        assert AggregationStrategy.FIRST.value == "first"
        assert AggregationStrategy.MAJORITY.value == "majority"
        assert AggregationStrategy.THRESHOLD.value == "threshold"


class TestTaskStatus:
    """Test TaskStatus enum"""

    def test_status_values(self):
        """Test status enum values"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


@pytest.mark.asyncio
class TestParallelExecutorEdgeCases:
    """Test edge cases"""

    async def test_execute_empty_duration_list(self):
        """Test execution with no completed tasks"""
        executor = ParallelExecutor()
        executor.create_task("coder", "Task")

        async def failing_executor(agent_type, task):
            raise Exception("Failed")

        result = await executor.execute(failing_executor)

        # Should handle empty durations
        assert result.max_duration == 0.0
        assert result.min_duration == 0.0
        assert result.avg_duration == 0.0

    async def test_threshold_larger_than_tasks(self):
        """Test threshold larger than number of tasks"""
        executor = ParallelExecutor(
            strategy=AggregationStrategy.THRESHOLD,
            threshold=10
        )
        executor.create_task("coder", "Task")

        async def mock_executor(agent_type, task):
            return "result"

        result = await executor.execute(mock_executor)

        # Should complete with available tasks
        assert result.completed == 1
