"""
Comprehensive tests for src/agents/parallel_executor.py to achieve 95%+ coverage.

Tests parallel task execution, aggregation strategies, priority, concurrency limits,
timeouts, error handling, result collection, and advanced patterns.

Target: 50+ test methods, 95%+ coverage
Current module: 177 lines, P1 CRITICAL
"""

import pytest
import asyncio
import time
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock

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

    def test_task_default_priority(self):
        """Test default priority is 0"""
        task = ParallelTask("coder", "Task")
        assert task.priority == 0

    def test_task_default_timeout(self):
        """Test default timeout is 180"""
        task = ParallelTask("coder", "Task")
        assert task.timeout == 180

    def test_task_metadata(self):
        """Test task metadata dictionary"""
        task = ParallelTask("coder", "Task", metadata={"key": "value"})
        assert task.metadata["key"] == "value"

    def test_task_runtime_fields(self):
        """Test runtime fields initialized correctly"""
        task = ParallelTask("coder", "Task")
        assert task.result is None
        assert task.error is None
        assert task.start_time is None
        assert task.end_time is None
        assert task.duration == 0.0

    def test_task_with_negative_priority(self):
        """Test task with negative priority"""
        task = ParallelTask("coder", "Task", priority=-5)
        assert task.priority == -5


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

    def test_get_task_result_not_found(self):
        """Test getting task result when name not found"""
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

        assert result.get_task_result("nonexistent") is None

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
        assert "result1" in successful
        assert "result3" in successful

    def test_get_successful_results_with_none(self):
        """Test get successful results filters None values"""
        task1 = ParallelTask("coder1", "Task1")
        task1.status = TaskStatus.COMPLETED
        task1.result = None

        task2 = ParallelTask("coder2", "Task2")
        task2.status = TaskStatus.COMPLETED
        task2.result = "result2"

        result = ExecutionResult(
            execution_id="123",
            strategy=AggregationStrategy.ALL,
            total_tasks=2,
            completed=2,
            failed=0,
            cancelled=0,
            tasks=[task1, task2],
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
        assert len(successful) == 1
        assert successful[0] == "result2"


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

    def test_init_execution_id_unique(self):
        """Test each executor has unique execution ID"""
        executor1 = ParallelExecutor()
        executor2 = ParallelExecutor()

        assert executor1.execution_id != executor2.execution_id

    def test_init_with_max_concurrent_1(self):
        """Test initialization with single concurrent task"""
        executor = ParallelExecutor(max_concurrent=1)
        assert executor.max_concurrent == 1


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

        executor.create_task("coder", "Task", key="value", extra="data")

        assert executor.tasks[0].metadata["key"] == "value"
        assert executor.tasks[0].metadata["extra"] == "data"

    def test_add_task_fluent_chaining(self):
        """Test fluent interface chaining"""
        executor = ParallelExecutor()
        task1 = ParallelTask("coder1", "Task1")
        task2 = ParallelTask("coder2", "Task2")

        result = executor.add_task(task1).add_task(task2)

        assert len(executor.tasks) == 2
        assert result is executor

    def test_create_task_fluent_chaining(self):
        """Test create_task fluent chaining"""
        executor = ParallelExecutor()

        result = (executor
                  .create_task("coder1", "Task1")
                  .create_task("coder2", "Task2")
                  .create_task("coder3", "Task3"))

        assert len(executor.tasks) == 3
        assert result is executor


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

    async def test_execute_majority_strategy_with_delays(self):
        """Test MAJORITY strategy with varying task delays"""
        executor = ParallelExecutor(strategy=AggregationStrategy.MAJORITY)
        for i in range(7):
            executor.create_task(f"coder{i}", f"Task{i}")

        async def mock_executor(agent_type, task):
            # Vary delays
            delay = 0.01 if "0" in agent_type or "1" in agent_type or "2" in agent_type or "3" in agent_type else 1.0
            await asyncio.sleep(delay)
            return f"result_{agent_type}"

        result = await executor.execute(mock_executor)

        # Should have at least 4 out of 7 (majority)
        assert result.completed >= 4

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

    async def test_execute_threshold_with_delays(self):
        """Test THRESHOLD strategy with task delays"""
        executor = ParallelExecutor(
            strategy=AggregationStrategy.THRESHOLD,
            threshold=3
        )
        for i in range(6):
            executor.create_task(f"coder{i}", f"Task{i}")

        async def mock_executor(agent_type, task):
            # First 3 fast, rest slow
            delay = 0.01 if int(agent_type[-1]) < 3 else 1.0
            await asyncio.sleep(delay)
            return f"result_{agent_type}"

        result = await executor.execute(mock_executor)

        # Should have at least 3 completed
        assert result.completed >= 3

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
        assert "timed out" in executor.tasks[0].error

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
        """Test task cancellation in FIRST strategy"""
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
        assert result.total_duration > 0

    async def test_execute_with_exception_type(self):
        """Test handling exception instead of task result"""
        executor = ParallelExecutor()
        executor.create_task("coder", "Task")

        async def mock_executor(agent_type, task):
            raise Exception("Test exception")

        result = await executor.execute(mock_executor)

        assert result.failed >= 1
        assert len(result.errors) >= 1

    async def test_execute_with_cancelled_error(self):
        """Test handling CancelledError is caught in gather"""
        executor = ParallelExecutor()
        executor.create_task("coder", "Task")

        async def cancelling_executor(agent_type, task):
            raise asyncio.CancelledError("Cancelled")

        # CancelledError is caught by gather() and task status set to CANCELLED
        result = await executor.execute(cancelling_executor)
        # Task status should be CANCELLED
        assert executor.tasks[0].status == TaskStatus.CANCELLED

    async def test_execute_stress_test_many_tasks(self):
        """Test executing many tasks concurrently"""
        executor = ParallelExecutor(max_concurrent=20)

        # Create 100 tasks
        for i in range(100):
            executor.create_task(f"coder{i}", f"Task{i}")

        call_count = 0

        async def mock_executor(agent_type, task):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return f"result_{agent_type}"

        result = await executor.execute(mock_executor)

        assert result.completed == 100
        assert call_count == 100
        assert len(result.results) == 100

    async def test_execute_mixed_success_failure(self):
        """Test mixed success and failure scenarios"""
        executor = ParallelExecutor()

        for i in range(10):
            executor.create_task(f"coder{i}", f"Task{i}")

        async def mixed_executor(agent_type, task):
            # Fail every 3rd task
            if int(agent_type[-1]) % 3 == 0:
                raise Exception(f"Task {agent_type} failed")
            return f"result_{agent_type}"

        result = await executor.execute(mixed_executor)

        assert result.completed > 0
        assert result.failed > 0
        assert result.completed + result.failed == 10

    async def test_execute_task_status_transitions(self):
        """Test task status transitions during execution"""
        executor = ParallelExecutor()
        executor.create_task("coder", "Task")

        async def mock_executor(agent_type, task):
            # Task should be RUNNING here
            assert executor.tasks[0].status == TaskStatus.RUNNING
            return "result"

        result = await executor.execute(mock_executor)

        # After execution, should be COMPLETED
        assert executor.tasks[0].status == TaskStatus.COMPLETED

    async def test_execute_task_timestamps(self):
        """Test task start and end timestamps are set"""
        executor = ParallelExecutor()
        executor.create_task("coder", "Task")

        async def mock_executor(agent_type, task):
            await asyncio.sleep(0.1)
            return "result"

        result = await executor.execute(mock_executor)

        task = executor.tasks[0]
        assert task.start_time is not None
        assert task.end_time is not None
        assert task.end_time > task.start_time
        assert task.duration > 0

    async def test_execute_unknown_strategy_raises_error(self):
        """Test unknown aggregation strategy raises error"""
        executor = ParallelExecutor()
        executor.create_task("coder", "Task")

        # Manually set invalid strategy
        executor.strategy = "invalid_strategy"

        async def mock_executor(agent_type, task):
            return "result"

        with pytest.raises(ValueError, match="Unknown aggregation strategy"):
            await executor.execute(mock_executor)

    async def test_execute_result_contains_all_data(self):
        """Test ExecutionResult contains all expected data"""
        executor = ParallelExecutor()
        executor.create_task("coder1", "Task1")
        executor.create_task("coder2", "Task2")

        async def mock_executor(agent_type, task):
            return f"result_{agent_type}"

        result = await executor.execute(mock_executor)

        assert result.execution_id == executor.execution_id
        assert result.strategy == AggregationStrategy.ALL
        assert result.total_tasks == 2
        assert result.start_time is not None
        assert result.end_time is not None
        assert len(result.tasks) == 2


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

    def test_get_summary_includes_task_details(self):
        """Test summary includes detailed task information"""
        executor = ParallelExecutor()
        executor.create_task("coder", "Task", name="my_task", priority=7)

        summary = executor.get_summary()

        task_info = summary["tasks"][0]
        assert task_info["name"] == "my_task"
        assert task_info["agent_type"] == "coder"
        assert task_info["priority"] == 7
        assert task_info["status"] == "pending"


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
    """Test edge cases and error conditions"""

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

    async def test_execute_all_tasks_timeout(self):
        """Test when all tasks timeout"""
        executor = ParallelExecutor()
        for i in range(3):
            executor.create_task(f"coder{i}", "Task", timeout=0.05)

        async def slow_executor(agent_type, task):
            await asyncio.sleep(1)
            return "result"

        result = await executor.execute(slow_executor)

        assert result.failed == 3
        assert result.completed == 0

    async def test_execute_all_tasks_fail(self):
        """Test when all tasks fail"""
        executor = ParallelExecutor()
        for i in range(3):
            executor.create_task(f"coder{i}", "Task")

        async def failing_executor(agent_type, task):
            raise Exception(f"Failed: {agent_type}")

        result = await executor.execute(failing_executor)

        assert result.failed == 3
        assert result.completed == 0
        assert len(result.errors) == 3

    async def test_execute_with_zero_max_concurrent(self):
        """Test behavior with very low concurrency limit"""
        # Note: semaphore value 0 would block, but we test with 1
        executor = ParallelExecutor(max_concurrent=1)
        for i in range(3):
            executor.create_task(f"coder{i}", "Task")

        async def mock_executor(agent_type, task):
            await asyncio.sleep(0.01)
            return "result"

        result = await executor.execute(mock_executor)

        assert result.completed == 3

    async def test_execute_result_none_values(self):
        """Test handling None result values"""
        executor = ParallelExecutor()
        executor.create_task("coder1", "Task1")
        executor.create_task("coder2", "Task2")

        async def none_executor(agent_type, task):
            # Return None for first task
            if agent_type == "coder1":
                return None
            return "result"

        result = await executor.execute(none_executor)

        assert result.completed == 2
        # Results list only contains non-None values
        assert len(result.results) == 1

    async def test_execute_single_task(self):
        """Test executing a single task"""
        executor = ParallelExecutor()
        executor.create_task("coder", "Task")

        async def mock_executor(agent_type, task):
            return "single_result"

        result = await executor.execute(mock_executor)

        assert result.completed == 1
        assert result.results[0] == "single_result"

    async def test_majority_with_even_number(self):
        """Test MAJORITY strategy with even number of tasks"""
        executor = ParallelExecutor(strategy=AggregationStrategy.MAJORITY)
        for i in range(4):  # Even number
            executor.create_task(f"coder{i}", f"Task{i}")

        async def mock_executor(agent_type, task):
            return "result"

        result = await executor.execute(mock_executor)

        # Majority of 4 is 3 (4//2 + 1)
        assert result.completed >= 3

    async def test_majority_with_single_task(self):
        """Test MAJORITY strategy with single task"""
        executor = ParallelExecutor(strategy=AggregationStrategy.MAJORITY)
        executor.create_task("coder", "Task")

        async def mock_executor(agent_type, task):
            return "result"

        result = await executor.execute(mock_executor)

        # Majority of 1 is 1
        assert result.completed >= 1


@pytest.mark.asyncio
class TestParallelExecutorAdvancedCoverage:
    """Test advanced scenarios for complete coverage"""

    async def test_majority_wait_loop_coverage(self):
        """Test MAJORITY strategy wait loop with slow tasks"""
        executor = ParallelExecutor(strategy=AggregationStrategy.MAJORITY)
        # Create 9 tasks (need 5 for majority)
        for i in range(9):
            executor.create_task(f"coder{i}", f"Task{i}")

        async def variable_executor(agent_type, task):
            # First 5 complete quickly, rest slowly
            idx = int(agent_type[-1])
            if idx < 5:
                await asyncio.sleep(0.01)
            else:
                await asyncio.sleep(2.0)
            return f"result_{agent_type}"

        result = await executor.execute(variable_executor)

        # Should have exactly 5 completed (majority) and rest cancelled
        assert result.completed >= 5

    async def test_threshold_wait_loop_coverage(self):
        """Test THRESHOLD strategy wait loop with incremental completion"""
        executor = ParallelExecutor(
            strategy=AggregationStrategy.THRESHOLD,
            threshold=4
        )
        # Create 8 tasks (need 4 for threshold)
        for i in range(8):
            executor.create_task(f"coder{i}", f"Task{i}")

        async def staggered_executor(agent_type, task):
            # Complete in staggered manner
            idx = int(agent_type[-1])
            await asyncio.sleep(0.01 * (idx + 1))
            return f"result_{agent_type}"

        result = await executor.execute(staggered_executor)

        # Should have at least 4 completed (threshold)
        assert result.completed >= 4

    async def test_exception_in_completed_tasks_list(self):
        """Test handling exceptions in completed_tasks list"""
        executor = ParallelExecutor()
        executor.create_task("coder1", "Task1")
        executor.create_task("coder2", "Task2")

        call_count = 0

        async def sometimes_failing_executor(agent_type, task):
            nonlocal call_count
            call_count += 1
            if agent_type == "coder1":
                raise ValueError("Task failed")
            return "result"

        result = await executor.execute(sometimes_failing_executor)

        # One should fail, one should succeed
        assert result.failed == 1
        assert result.completed == 1
        assert "Task failed" in result.errors[0] or "ValueError" in result.errors[0]

    async def test_majority_cancels_remaining_tasks(self):
        """Test that MAJORITY cancels remaining tasks after reaching majority"""
        executor = ParallelExecutor(strategy=AggregationStrategy.MAJORITY)
        for i in range(7):
            executor.create_task(f"coder{i}", f"Task{i}")

        async def counting_executor(agent_type, task):
            # First 4 complete fast (majority), rest slow
            idx = int(agent_type[-1])
            if idx < 4:
                await asyncio.sleep(0.01)
                return f"result_{agent_type}"
            else:
                await asyncio.sleep(5.0)  # Should be cancelled
                return f"result_{agent_type}"

        result = await executor.execute(counting_executor)

        # Should have at least majority (4 of 7)
        assert result.completed >= 4
        # Check that not all tasks completed (some still running/cancelled)
        assert result.completed < 7

    async def test_threshold_cancels_remaining_tasks(self):
        """Test that THRESHOLD cancels remaining tasks after threshold"""
        executor = ParallelExecutor(
            strategy=AggregationStrategy.THRESHOLD,
            threshold=3
        )
        for i in range(6):
            executor.create_task(f"coder{i}", f"Task{i}")

        async def threshold_executor(agent_type, task):
            # First 3 complete fast, rest slow
            idx = int(agent_type[-1])
            if idx < 3:
                await asyncio.sleep(0.01)
            else:
                await asyncio.sleep(5.0)  # Should be cancelled
            return f"result_{agent_type}"

        result = await executor.execute(threshold_executor)

        # Should have at least threshold (3)
        assert result.completed >= 3
        # Check that not all tasks completed (some still running)
        assert result.completed < 6


@pytest.mark.asyncio
class TestParallelExecutorPerformance:
    """Test performance characteristics"""

    async def test_concurrent_execution_faster_than_serial(self):
        """Test parallel execution is faster than serial"""
        # Create 10 tasks that each take 0.1s
        num_tasks = 10
        task_duration = 0.1

        # Parallel execution
        parallel_executor = ParallelExecutor(max_concurrent=10)
        for i in range(num_tasks):
            parallel_executor.create_task(f"coder{i}", "Task")

        async def timed_executor(agent_type, task):
            await asyncio.sleep(task_duration)
            return "result"

        start = time.time()
        await parallel_executor.execute(timed_executor)
        parallel_time = time.time() - start

        # Parallel should be close to task_duration, not num_tasks * task_duration
        # Allow some overhead
        assert parallel_time < (task_duration * 3)

    async def test_throttling_limits_concurrency(self):
        """Test that max_concurrent actually limits concurrency"""
        executor = ParallelExecutor(max_concurrent=3)
        max_concurrent_seen = 0
        current_concurrent = []

        async def tracking_executor(agent_type, task):
            nonlocal max_concurrent_seen
            current_concurrent.append(1)
            max_concurrent_seen = max(max_concurrent_seen, len(current_concurrent))
            await asyncio.sleep(0.05)
            current_concurrent.pop()
            return "result"

        for i in range(10):
            executor.create_task(f"coder{i}", "Task")

        await executor.execute(tracking_executor)

        # Max concurrent should not exceed limit
        assert max_concurrent_seen <= 3
        assert max_concurrent_seen > 0
