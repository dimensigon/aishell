"""Performance benchmarks for Agent Execution System.

Measures:
- Agent spawning overhead
- Task distribution latency
- Inter-agent communication speed
- State persistence performance
- Parallel execution efficiency
"""

import unittest
import time
import asyncio
from statistics import mean, stdev
from concurrent.futures import ThreadPoolExecutor, as_completed


class BenchmarkAgentSpawning(unittest.TestCase):
    """Benchmark agent spawning and initialization."""

    def test_single_agent_spawn_time(self):
        """Benchmark single agent spawn time."""
        from src.agents.test_agent import TestAgent

        times = []
        for _ in range(100):
            start = time.perf_counter()

            agent = TestAgent(agent_id=f"test_agent_{_}", config={})

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)
        std_time = stdev(times)

        print(f"\n=== Single Agent Spawn Performance ===")
        print(f"Iterations: 100")
        print(f"Average time: {avg_time:.4f}ms")
        print(f"Std deviation: {std_time:.4f}ms")

        # Agent spawning should be fast (< 10ms)
        self.assertLess(avg_time, 10.0)

    def test_multiple_agent_spawn_time(self):
        """Benchmark spawning multiple agents."""
        from src.agents.test_agent import TestAgent

        agent_counts = [10, 50, 100]

        print(f"\n=== Multiple Agent Spawn Performance ===")

        for count in agent_counts:
            start = time.perf_counter()

            agents = [TestAgent(agent_id=f"agent_{i}", config={}) for i in range(count)]

            end = time.perf_counter()
            total_time = (end - start) * 1000
            avg_per_agent = total_time / count

            print(f"{count} agents: Total={total_time:.2f}ms, Avg={avg_per_agent:.4f}ms/agent")

            # Should scale linearly
            self.assertLess(avg_per_agent, 10.0)


class BenchmarkTaskDistribution(unittest.TestCase):
    """Benchmark task distribution across agents."""

    def test_task_queue_performance(self):
        """Benchmark task queue operations."""
        from src.agents.coordinator import TaskQueue

        queue = TaskQueue()

        # Benchmark enqueue
        enqueue_times = []
        for i in range(1000):
            task = {"id": i, "type": "test", "data": f"task_{i}"}

            start = time.perf_counter()
            queue.enqueue(task)
            end = time.perf_counter()

            enqueue_times.append((end - start) * 1000)

        # Benchmark dequeue
        dequeue_times = []
        for _ in range(1000):
            start = time.perf_counter()
            task = queue.dequeue()
            end = time.perf_counter()

            dequeue_times.append((end - start) * 1000)

        print(f"\n=== Task Queue Performance ===")
        print(f"Enqueue - Avg: {mean(enqueue_times):.4f}ms, Std: {stdev(enqueue_times):.4f}ms")
        print(f"Dequeue - Avg: {mean(dequeue_times):.4f}ms, Std: {stdev(dequeue_times):.4f}ms")

        # Queue operations should be very fast
        self.assertLess(mean(enqueue_times), 0.1)
        self.assertLess(mean(dequeue_times), 0.1)

    def test_task_assignment_latency(self):
        """Benchmark task assignment latency."""
        from src.agents.coordinator import AgentCoordinator
        from src.agents.test_agent import TestAgent

        coordinator = AgentCoordinator()

        # Create agents
        agents = [TestAgent(agent_id=f"agent_{i}", config={}) for i in range(10)]
        for agent in agents:
            coordinator.register_agent(agent)

        # Benchmark task assignment
        times = []
        for i in range(100):
            task = {"id": i, "type": "test", "priority": "medium"}

            start = time.perf_counter()
            assigned_agent = coordinator.assign_task(task)
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Task Assignment Latency ===")
        print(f"Agents: 10")
        print(f"Tasks: 100")
        print(f"Average assignment time: {avg_time:.4f}ms")

        # Task assignment should be fast (< 5ms)
        self.assertLess(avg_time, 5.0)


class BenchmarkInterAgentCommunication(unittest.TestCase):
    """Benchmark inter-agent communication."""

    def test_message_passing_latency(self):
        """Benchmark message passing between agents."""
        from src.agents.coordinator import AgentMessage, MessageBus

        bus = MessageBus()

        # Benchmark message send
        send_times = []
        for i in range(1000):
            message = AgentMessage(
                sender=f"agent_{i % 10}",
                receiver=f"agent_{(i + 1) % 10}",
                message_type="request",
                payload={"data": f"message_{i}"},
            )

            start = time.perf_counter()
            bus.send_message(message)
            end = time.perf_counter()

            send_times.append((end - start) * 1000)

        # Benchmark message receive
        receive_times = []
        for i in range(1000):
            agent_id = f"agent_{i % 10}"

            start = time.perf_counter()
            messages = bus.get_messages(agent_id)
            end = time.perf_counter()

            receive_times.append((end - start) * 1000)

        print(f"\n=== Inter-Agent Message Passing ===")
        print(f"Send - Avg: {mean(send_times):.4f}ms, Std: {stdev(send_times):.4f}ms")
        print(f"Receive - Avg: {mean(receive_times):.4f}ms, Std: {stdev(receive_times):.4f}ms")

        # Message passing should be fast
        self.assertLess(mean(send_times), 1.0)
        self.assertLess(mean(receive_times), 1.0)

    def test_broadcast_performance(self):
        """Benchmark broadcast to multiple agents."""
        from src.agents.coordinator import MessageBus

        bus = MessageBus()

        # Register multiple agents
        agent_ids = [f"agent_{i}" for i in range(100)]

        times = []
        for i in range(100):
            message = {"type": "broadcast", "data": f"broadcast_{i}"}

            start = time.perf_counter()
            bus.broadcast(message, agent_ids)
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Broadcast Performance (100 agents) ===")
        print(f"Average time: {avg_time:.4f}ms")

        # Broadcasting to 100 agents should be reasonable (< 50ms)
        self.assertLess(avg_time, 50.0)


class BenchmarkStatePersistence(unittest.TestCase):
    """Benchmark agent state persistence."""

    def test_state_save_performance(self):
        """Benchmark state save operations."""
        from src.agents.state.manager_mock import StateManager

        manager = StateManager()

        # Create various state sizes
        states = {
            "small": {"progress": 50, "status": "running"},
            "medium": {"data": list(range(100)), "config": {"key": "value"}},
            "large": {"results": [{"id": i, "data": f"item_{i}"} for i in range(1000)]},
        }

        print(f"\n=== State Save Performance ===")

        for size_name, state in states.items():
            times = []
            for i in range(100):
                agent_id = f"agent_{i}"

                start = time.perf_counter()
                manager.save_state(agent_id, state)
                end = time.perf_counter()

                times.append((end - start) * 1000)

            avg_time = mean(times)
            print(f"{size_name.capitalize()} state: {avg_time:.4f}ms")

            # State save should be fast
            self.assertLess(avg_time, 10.0)

    def test_state_load_performance(self):
        """Benchmark state load operations."""
        from src.agents.state.manager_mock import StateManager

        manager = StateManager()

        # Pre-populate states
        for i in range(100):
            manager.save_state(f"agent_{i}", {"data": list(range(100))})

        # Benchmark loading
        times = []
        for i in range(100):
            start = time.perf_counter()
            state = manager.load_state(f"agent_{i}")
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== State Load Performance ===")
        print(f"Average time: {avg_time:.4f}ms")

        # State loading should be fast
        self.assertLess(avg_time, 5.0)


class BenchmarkParallelExecution(unittest.TestCase):
    """Benchmark parallel agent execution."""

    def test_parallel_task_execution(self):
        """Benchmark parallel task execution."""
        from concurrent.futures import ThreadPoolExecutor
        import concurrent.futures

        max_workers = 10

        def mock_task(task_id):
            """Simulate task execution."""
            time.sleep(0.01)  # Simulate 10ms work
            return {"task_id": task_id, "result": "completed"}

        # Create tasks
        task_count = 100
        task_ids = list(range(task_count))

        print(f"\n=== Parallel Execution Performance ===")

        # Sequential execution
        start = time.perf_counter()
        for task_id in task_ids:
            mock_task(task_id)
        sequential_time = (time.perf_counter() - start) * 1000

        # Parallel execution using real ThreadPoolExecutor
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(mock_task, task_id) for task_id in task_ids]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        parallel_time = (time.perf_counter() - start) * 1000

        speedup = sequential_time / parallel_time

        print(f"Sequential: {sequential_time:.2f}ms")
        print(f"Parallel ({max_workers} workers): {parallel_time:.2f}ms")
        print(f"Speedup: {speedup:.2f}x")

        # Should see significant speedup (relaxed threshold for real execution)
        self.assertGreater(speedup, 5.0)

    def test_agent_coordination_overhead(self):
        """Benchmark coordination overhead."""
        from src.agents.coordinator import AgentCoordinator
        from src.agents.test_agent import TestAgent

        coordinator = AgentCoordinator()

        # Create agents
        agents = [TestAgent(agent_id=f"agent_{i}", config={}) for i in range(20)]
        for agent in agents:
            coordinator.register_agent(agent)

        # Benchmark coordination
        start = time.perf_counter()

        # Distribute 100 tasks
        for i in range(100):
            task = {"id": i, "type": "test"}
            coordinator.assign_task(task)

        coordination_time = (time.perf_counter() - start) * 1000

        print(f"\n=== Agent Coordination Overhead ===")
        print(f"Agents: 20")
        print(f"Tasks: 100")
        print(f"Total coordination time: {coordination_time:.2f}ms")
        print(f"Per-task overhead: {coordination_time / 100:.4f}ms")

        # Coordination should be efficient
        self.assertLess(coordination_time / 100, 1.0)


class BenchmarkAgentScaling(unittest.TestCase):
    """Benchmark agent scaling performance."""

    def test_scaling_with_agent_count(self):
        """Benchmark performance vs agent count."""
        from src.agents.coordinator import AgentCoordinator
        from src.agents.test_agent import TestAgent

        agent_counts = [10, 50, 100, 200]

        print(f"\n=== Agent Scaling Performance ===")

        for count in agent_counts:
            coordinator = AgentCoordinator()

            # Create agents
            agents = [TestAgent(agent_id=f"agent_{i}", config={}) for i in range(count)]
            for agent in agents:
                coordinator.register_agent(agent)

            # Benchmark task distribution
            start = time.perf_counter()

            for i in range(1000):
                task = {"id": i}
                coordinator.assign_task(task)

            total_time = (time.perf_counter() - start) * 1000
            avg_time = total_time / 1000

            print(f"{count} agents: Total={total_time:.2f}ms, Avg={avg_time:.4f}ms/task")

            # Should scale reasonably
            self.assertLess(avg_time, 5.0)


if __name__ == "__main__":
    # Run benchmarks
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
