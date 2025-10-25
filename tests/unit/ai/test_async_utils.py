"""
Tests for Async Processing Utilities

Comprehensive tests for async_utils module including:
- Priority queues
- Context managers
- Retry decorators
- Task execution
- Batch processing
- Streaming
- Performance monitoring
"""

import asyncio
import pytest
from datetime import datetime

from src.core.async_utils import (
    AsyncPriorityQueue,
    QueuePriority,
    async_resource_manager,
    async_timeout_manager,
    async_lock_manager,
    async_retry,
    TaskExecutor,
    AsyncBatchProcessor,
    AsyncStreamHandler,
    AsyncPerformanceMonitor,
    get_performance_monitor,
    run_with_timeout,
    gather_with_concurrency
)


# ============================================================================
# Priority Queue Tests
# ============================================================================

@pytest.mark.asyncio
async def test_priority_queue_basic():
    """Test basic priority queue operations"""
    queue = AsyncPriorityQueue(maxsize=10)

    # Add items with different priorities
    await queue.put("low", QueuePriority.LOW)
    await queue.put("high", QueuePriority.HIGH)
    await queue.put("critical", QueuePriority.CRITICAL)
    await queue.put("normal", QueuePriority.NORMAL)

    # Should get in priority order
    assert await queue.get() == "critical"
    assert await queue.get() == "high"
    assert await queue.get() == "normal"
    assert await queue.get() == "low"


@pytest.mark.asyncio
async def test_priority_queue_backpressure():
    """Test backpressure detection"""
    queue = AsyncPriorityQueue(maxsize=10, backpressure_threshold=0.8)

    # Fill to backpressure threshold
    for i in range(8):
        await queue.put(i)

    assert queue.is_backpressure()

    metrics = queue.get_metrics()
    assert metrics['backpressure']
    assert metrics['utilization'] >= 0.8


@pytest.mark.asyncio
async def test_priority_queue_overflow():
    """Test queue overflow handling"""
    queue = AsyncPriorityQueue(maxsize=5)

    # Fill queue
    for i in range(5):
        assert await queue.put(i, block=False)

    # Next item should be dropped
    assert not await queue.put(99, block=False)

    metrics = queue.get_metrics()
    assert metrics['dropped_total'] == 1


# ============================================================================
# Context Manager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_async_resource_manager():
    """Test async resource manager"""
    acquired = []
    released = []

    async def acquire():
        resource = "test_resource"
        acquired.append(resource)
        return resource

    async def release(resource):
        released.append(resource)

    async with async_resource_manager(acquire, release) as resource:
        assert resource == "test_resource"
        assert len(acquired) == 1
        assert len(released) == 0

    assert len(released) == 1


@pytest.mark.asyncio
async def test_async_timeout_manager():
    """Test timeout manager"""
    # Should complete
    async with async_timeout_manager(1.0):
        await asyncio.sleep(0.1)

    # Should timeout
    with pytest.raises(asyncio.TimeoutError):
        async with async_timeout_manager(0.1):
            await asyncio.sleep(1.0)


@pytest.mark.asyncio
async def test_async_lock_manager():
    """Test lock manager"""
    lock = asyncio.Lock()

    async with async_lock_manager(lock) as acquired:
        assert acquired
        assert lock.locked()

    assert not lock.locked()


# ============================================================================
# Retry Decorator Tests
# ============================================================================

@pytest.mark.asyncio
async def test_async_retry_success():
    """Test retry on eventual success"""
    call_count = 0

    @async_retry(max_attempts=3, base_delay=0.01)
    async def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Not yet")
        return "success"

    result = await flaky_function()
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_async_retry_failure():
    """Test retry exhaustion"""
    call_count = 0

    @async_retry(max_attempts=3, base_delay=0.01)
    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError):
        await always_fails()

    assert call_count == 3


@pytest.mark.asyncio
async def test_async_retry_specific_exception():
    """Test retry on specific exceptions"""
    @async_retry(max_attempts=3, base_delay=0.01, retry_on=(ValueError,))
    async def raises_type_error():
        raise TypeError("Should not retry")

    with pytest.raises(TypeError):
        await raises_type_error()


# ============================================================================
# Task Executor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_task_executor_single():
    """Test single task execution"""
    executor = TaskExecutor(max_concurrent=5)

    async def task(value):
        await asyncio.sleep(0.01)
        return value * 2

    result = await executor.execute_task(task, 5)
    assert result == 10

    stats = executor.get_stats()
    assert stats['completed'] == 1
    assert stats['failed'] == 0


@pytest.mark.asyncio
async def test_task_executor_many():
    """Test concurrent task execution"""
    executor = TaskExecutor(max_concurrent=5)

    async def task(value):
        await asyncio.sleep(0.01)
        return value * 2

    tasks = [(task, (i,), {}) for i in range(10)]
    results = await executor.execute_many(tasks)

    assert len(results) == 10
    assert results[5] == 10

    stats = executor.get_stats()
    assert stats['completed'] == 10


@pytest.mark.asyncio
async def test_task_executor_map():
    """Test map function"""
    executor = TaskExecutor(max_concurrent=5)

    async def double(x):
        await asyncio.sleep(0.01)
        return x * 2

    items = list(range(10))
    results = await executor.map(double, items)

    assert len(results) == 10
    assert results[5] == 10


# ============================================================================
# Batch Processor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_batch_processor_size_trigger():
    """Test batch processing on size trigger"""
    batches_processed = []

    async def process_batch(items):
        batches_processed.append(items.copy())
        return [item * 2 for item in items]

    processor = AsyncBatchProcessor(
        process_batch,
        batch_size=5,
        batch_timeout=1.0
    )

    # Add items to fill one batch
    for i in range(5):
        await processor.add(i)

    await asyncio.sleep(0.1)  # Let processing complete

    assert len(batches_processed) == 1
    assert len(batches_processed[0]) == 5


@pytest.mark.asyncio
async def test_batch_processor_timeout_trigger():
    """Test batch processing on timeout"""
    batches_processed = []

    async def process_batch(items):
        batches_processed.append(items.copy())
        return items

    processor = AsyncBatchProcessor(
        process_batch,
        batch_size=10,
        batch_timeout=0.1
    )

    # Add fewer items than batch size
    await processor.add(1)
    await processor.add(2)

    # Wait for timeout
    await asyncio.sleep(0.2)

    assert len(batches_processed) == 1
    assert len(batches_processed[0]) == 2


@pytest.mark.asyncio
async def test_batch_processor_flush():
    """Test manual batch flush"""
    batches_processed = []

    async def process_batch(items):
        batches_processed.append(items.copy())
        return items

    processor = AsyncBatchProcessor(
        process_batch,
        batch_size=10,
        batch_timeout=10.0
    )

    await processor.add(1)
    await processor.add(2)
    await processor.flush()

    assert len(batches_processed) == 1
    assert len(batches_processed[0]) == 2


# ============================================================================
# Stream Handler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_stream_handler_basic():
    """Test basic stream operations"""
    stream = AsyncStreamHandler(buffer_size=10)

    # Write items
    for i in range(5):
        await stream.write(i)

    # Read items
    items = []
    for _ in range(5):
        item = await stream.read()
        if item is not None:
            items.append(item)

    assert items == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_stream_handler_read_many():
    """Test reading multiple items"""
    stream = AsyncStreamHandler(buffer_size=10)

    # Write items
    for i in range(5):
        await stream.write(i)

    # Read many
    items = await stream.read_many(max_items=10, timeout=0.1)
    assert len(items) == 5
    assert items == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_stream_handler_iterator():
    """Test stream iterator"""
    stream = AsyncStreamHandler(buffer_size=10)

    # Write items
    async def writer():
        for i in range(5):
            await stream.write(i)
        stream.close()

    asyncio.create_task(writer())

    # Read via iterator
    items = []
    async for item in stream.stream():
        items.append(item)

    assert items == [0, 1, 2, 3, 4]


# ============================================================================
# Performance Monitor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_performance_monitor():
    """Test performance monitoring"""
    monitor = AsyncPerformanceMonitor()

    async def test_operation():
        async with monitor.track("test_op"):
            await asyncio.sleep(0.01)

    # Execute operation multiple times
    for _ in range(5):
        await test_operation()

    metrics = await monitor.get_metrics("test_op")

    assert metrics['operation'] == "test_op"
    assert metrics['total_calls'] == 5
    assert metrics['successful_calls'] == 5
    assert metrics['failed_calls'] == 0
    assert metrics['avg_duration_ms'] > 0


@pytest.mark.asyncio
async def test_performance_monitor_failure():
    """Test monitoring failed operations"""
    monitor = AsyncPerformanceMonitor()

    async def failing_operation():
        async with monitor.track("failing_op"):
            raise ValueError("Test error")

    # Execute failing operation
    for _ in range(3):
        try:
            await failing_operation()
        except ValueError:
            pass

    metrics = await monitor.get_metrics("failing_op")

    assert metrics['total_calls'] == 3
    assert metrics['successful_calls'] == 0
    assert metrics['failed_calls'] == 3


@pytest.mark.asyncio
async def test_performance_monitor_summary():
    """Test performance summary"""
    monitor = AsyncPerformanceMonitor()

    async with monitor.track("op1"):
        await asyncio.sleep(0.01)

    async with monitor.track("op2"):
        await asyncio.sleep(0.01)

    summary = await monitor.get_summary()

    assert summary['operations_tracked'] == 2
    assert summary['total_calls'] == 2
    assert summary['total_successful'] == 2


# ============================================================================
# Convenience Function Tests
# ============================================================================

@pytest.mark.asyncio
async def test_run_with_timeout_success():
    """Test run with timeout success"""
    async def quick_task():
        await asyncio.sleep(0.01)
        return "done"

    result = await run_with_timeout(quick_task(), timeout=1.0)
    assert result == "done"


@pytest.mark.asyncio
async def test_run_with_timeout_failure():
    """Test run with timeout failure"""
    async def slow_task():
        await asyncio.sleep(1.0)
        return "done"

    result = await run_with_timeout(
        slow_task(),
        timeout=0.1,
        default="timeout"
    )
    assert result == "timeout"


@pytest.mark.asyncio
async def test_gather_with_concurrency():
    """Test concurrent gather with limit"""
    counter = {'max': 0, 'current': 0}
    lock = asyncio.Lock()

    async def task(value):
        async with lock:
            counter['current'] += 1
            counter['max'] = max(counter['max'], counter['current'])

        await asyncio.sleep(0.01)

        async with lock:
            counter['current'] -= 1

        return value * 2

    tasks = [task(i) for i in range(20)]
    results = await gather_with_concurrency(
        *tasks,
        max_concurrent=5
    )

    assert len(results) == 20
    assert counter['max'] <= 5  # Never exceeded concurrency limit


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_integration_pipeline():
    """Test complete async processing pipeline"""
    # Create components
    queue = AsyncPriorityQueue(maxsize=100)
    executor = TaskExecutor(max_concurrent=5)
    monitor = AsyncPerformanceMonitor()

    # Producer
    async def producer():
        for i in range(20):
            await queue.put(i, QueuePriority.NORMAL)

    # Consumer
    async def consumer():
        results = []
        for _ in range(20):
            item = await queue.get()
            async with monitor.track("process_item"):
                result = await executor.execute_task(
                    lambda x: asyncio.sleep(0.01) or x * 2,
                    item
                )
            results.append(result)
        return results

    # Run pipeline
    producer_task = asyncio.create_task(producer())
    consumer_task = asyncio.create_task(consumer())

    await producer_task
    results = await consumer_task

    assert len(results) == 20
    assert results[10] == 20

    # Check metrics
    metrics = await monitor.get_metrics("process_item")
    assert metrics['total_calls'] == 20
    assert metrics['successful_calls'] == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
