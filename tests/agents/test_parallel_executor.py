"""Tests for ParallelExecutor"""

import pytest
import asyncio
from src.agents import ParallelExecutor, ParallelTask, AggregationStrategy, TaskStatus


@pytest.fixture
async def mock_executor():
    """Mock agent executor"""
    async def executor(agent_type: str, task: str):
        await asyncio.sleep(0.1)
        return {"agent": agent_type, "task": task}
    return executor


@pytest.mark.asyncio
async def test_executor_creation():
    """Test executor creation"""
    executor = ParallelExecutor(max_concurrent=5)
    assert executor.max_concurrent == 5
    assert executor.strategy == AggregationStrategy.ALL


@pytest.mark.asyncio
async def test_add_task():
    """Test adding tasks"""
    executor = ParallelExecutor()
    task = ParallelTask(agent_type="coder", task="Test task")
    executor.add_task(task)
    assert len(executor.tasks) == 1


@pytest.mark.asyncio
async def test_create_task():
    """Test fluent task creation"""
    executor = ParallelExecutor()
    executor.create_task("researcher", "Task 1").create_task("coder", "Task 2")
    assert len(executor.tasks) == 2


@pytest.mark.asyncio
async def test_parallel_execution(mock_executor):
    """Test parallel execution"""
    executor = ParallelExecutor(max_concurrent=3)
    executor.create_task("coder", "Task 1")
    executor.create_task("coder", "Task 2")
    executor.create_task("coder", "Task 3")

    result = await executor.execute(mock_executor)

    assert result.completed == 3
    assert result.failed == 0
    assert result.is_successful()


@pytest.mark.asyncio
async def test_priority_ordering(mock_executor):
    """Test priority-based task ordering"""
    executor = ParallelExecutor(max_concurrent=1)
    executor.create_task("coder", "Low", priority=TaskPriority.LOW)
    executor.create_task("coder", "High", priority=TaskPriority.HIGH)
    executor.create_task("coder", "Critical", priority=TaskPriority.CRITICAL)

    result = await executor.execute(mock_executor)

    # Critical should execute first
    assert result.tasks[0].priority == TaskPriority.CRITICAL


@pytest.mark.asyncio
async def test_first_strategy(mock_executor):
    """Test FIRST aggregation strategy"""
    executor = ParallelExecutor(strategy=AggregationStrategy.FIRST)
    for i in range(5):
        executor.create_task("coder", f"Task {i}")

    result = await executor.execute(mock_executor)

    # At least one completed, others may be cancelled
    assert result.completed >= 1


@pytest.mark.asyncio
async def test_get_summary():
    """Test executor summary"""
    executor = ParallelExecutor()
    executor.create_task("coder", "Task 1")
    executor.create_task("tester", "Task 2")

    summary = executor.get_summary()

    assert summary["total_tasks"] == 2
    assert len(summary["tasks"]) == 2
