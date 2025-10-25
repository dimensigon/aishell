"""
Performance tests for Async Operations.

Tests performance of async operations including concurrent execution,
throughput, latency, and resource utilization.
"""

import pytest
import asyncio
import time
from tests.utils.test_helpers import MockAgent, MockDatabase, PerformanceTimer


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
class TestAsyncPerformance:
    """Test suite for async operation performance."""

    async def test_concurrent_task_execution(self, performance_thresholds):
        """Test concurrent task execution performance."""
        agents = [MockAgent(f"agent{i}") for i in range(10)]

        start_time = time.time()

        tasks = [agent.execute({"task": i}) for i, agent in enumerate(agents)]
        results = await asyncio.gather(*tasks)

        duration = time.time() - start_time

        assert len(results) == 10
        assert duration < 1.0  # Should complete quickly in parallel

    async def test_high_throughput_operations(self):
        """Test high throughput async operations."""
        db = MockDatabase()
        await db.connect()

        operations_count = 1000

        start_time = time.time()

        tasks = [
            db.execute(f"SELECT * FROM table WHERE id = {i}")
            for i in range(operations_count)
        ]

        await asyncio.gather(*tasks)

        duration = time.time() - start_time
        throughput = operations_count / duration

        assert throughput > 500  # At least 500 ops/sec

    async def test_low_latency_operations(self, performance_thresholds):
        """Test low latency operations."""
        agent = MockAgent("fast_agent")

        latencies = []

        for i in range(100):
            start = time.time()
            await agent.execute({"task": i})
            latency = time.time() - start
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)

        assert avg_latency < 0.01  # < 10ms average
        assert max_latency < 0.05  # < 50ms max

    async def test_connection_pool_performance(self):
        """Test connection pool performance."""
        pool_size = 10
        pool = [MockDatabase() for _ in range(pool_size)]

        # Connect all
        start = time.time()
        await asyncio.gather(*[db.connect() for db in pool])
        connect_duration = time.time() - start

        # Execute queries using pool
        start = time.time()
        tasks = []
        for i in range(100):
            db = pool[i % pool_size]
            tasks.append(db.execute(f"SELECT * FROM table{i}"))

        await asyncio.gather(*tasks)
        query_duration = time.time() - start

        assert connect_duration < 1.0
        assert query_duration < 2.0


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
class TestQueryPerformance:
    """Test suite for query execution performance."""

    async def test_simple_query_performance(self, connected_database, performance_thresholds):
        """Test simple query execution performance."""
        query = "SELECT * FROM users WHERE id = 1"

        async with PerformanceTimer() as timer:
            await connected_database.execute(query)

        assert timer.duration < performance_thresholds["query_execution"]

    async def test_complex_query_performance(self, connected_database):
        """Test complex query performance."""
        query = """
        SELECT u.name, COUNT(o.id) as order_count, SUM(o.total) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.created_at > '2024-01-01'
        GROUP BY u.name
        HAVING COUNT(o.id) > 5
        ORDER BY total_spent DESC
        LIMIT 10
        """

        async with PerformanceTimer() as timer:
            await connected_database.execute(query)

        assert timer.duration < 0.5  # Complex query threshold

    async def test_batch_query_performance(self, connected_database):
        """Test batch query execution performance."""
        queries = [
            f"SELECT * FROM users WHERE id = {i}"
            for i in range(100)
        ]

        async with PerformanceTimer() as timer:
            for query in queries:
                await connected_database.execute(query)

        assert timer.duration < 2.0  # 100 queries in 2 seconds

    async def test_parallel_query_performance(self, connected_database):
        """Test parallel query execution performance."""
        queries = [
            f"SELECT * FROM table{i} WHERE id = 1"
            for i in range(50)
        ]

        async with PerformanceTimer() as timer:
            tasks = [connected_database.execute(q) for q in queries]
            await asyncio.gather(*tasks)

        assert timer.duration < 1.0  # 50 parallel queries in 1 second


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
class TestAgentConcurrency:
    """Test suite for agent concurrency performance."""

    async def test_agent_scalability(self):
        """Test agent scalability with increasing load."""
        agent_counts = [10, 50, 100]
        durations = []

        for count in agent_counts:
            agents = [MockAgent(f"agent{i}") for i in range(count)]

            start = time.time()
            tasks = [agent.execute({"task": i}) for i, agent in enumerate(agents)]
            await asyncio.gather(*tasks)
            duration = time.time() - start

            durations.append(duration)

        # Performance should scale sub-linearly
        assert durations[1] < durations[0] * 5  # 5x agents, < 5x time
        assert durations[2] < durations[0] * 10  # 10x agents, < 10x time

    async def test_agent_coordination_overhead(self, mock_event_bus):
        """Test overhead of agent coordination."""
        agents = [MockAgent(f"agent{i}") for i in range(20)]

        # Without coordination
        start = time.time()
        tasks = [agent.execute({"task": i}) for i, agent in enumerate(agents)]
        await asyncio.gather(*tasks)
        duration_without_coord = time.time() - start

        # With coordination (event emission)
        start = time.time()
        for i, agent in enumerate(agents):
            result = await agent.execute({"task": i})
            await mock_event_bus.emit("task:complete", result)
        duration_with_coord = time.time() - start

        # Coordination overhead should be minimal
        overhead = duration_with_coord - duration_without_coord
        assert overhead < 0.5  # < 500ms overhead

    async def test_agent_resource_efficiency(self):
        """Test agent resource efficiency."""
        agent_count = 100

        # Create and execute many agents
        agents = [MockAgent(f"agent{i}") for i in range(agent_count)]

        start_time = time.time()

        tasks = [agent.execute({"task": i}) for i, agent in enumerate(agents)]
        results = await asyncio.gather(*tasks)

        duration = time.time() - start_time

        # Should handle 100 agents efficiently
        assert len(results) == agent_count
        assert duration < 2.0


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
class TestMemoryPerformance:
    """Test suite for memory performance."""

    async def test_memory_efficiency(self):
        """Test memory usage remains efficient."""
        import sys

        # Create large dataset
        data = [{"id": i, "data": "x" * 100} for i in range(10000)]

        initial_size = sys.getsizeof(data)

        # Process data
        processed = [item["id"] for item in data]

        # Clear original data
        data.clear()

        # Memory should be freed
        assert sys.getsizeof(data) < initial_size

    async def test_connection_memory_management(self):
        """Test connection memory is managed properly."""
        # Create many connections
        connections = [MockDatabase() for _ in range(100)]

        # Connect all
        await asyncio.gather(*[db.connect() for db in connections])

        # Disconnect all
        await asyncio.gather(*[db.disconnect() for db in connections])

        # Connections should be cleaned up
        assert all(not db.connected for db in connections)
