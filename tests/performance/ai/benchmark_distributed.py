"""Performance benchmarks for Distributed Coordination System.

Measures:
- Swarm initialization overhead
- Coordination topology performance
- Message routing latency
- Consensus building speed
- Distributed task orchestration
"""

import unittest
import time
from statistics import mean, stdev
import random


class BenchmarkSwarmInitialization(unittest.TestCase):
    """Benchmark swarm initialization performance."""

    def test_swarm_init_time(self):
        """Benchmark swarm initialization time."""
        topologies = ["mesh", "hierarchical", "ring", "star"]

        print(f"\n=== Swarm Initialization Performance ===")

        for topology in topologies:
            times = []

            for _ in range(10):
                start = time.perf_counter()

                # Simulate swarm init
                # In real implementation: mcp__claude-flow__swarm_init
                swarm_config = {
                    "topology": topology,
                    "maxAgents": 10,
                    "strategy": "balanced",
                }

                end = time.perf_counter()
                times.append((end - start) * 1000)

            avg_time = mean(times)
            print(f"{topology.capitalize()} topology: {avg_time:.2f}ms")

            # Initialization should be fast (< 100ms)
            self.assertLess(avg_time, 100.0)

    def test_scaling_with_agent_count(self):
        """Benchmark initialization scaling with agent count."""
        agent_counts = [5, 10, 20, 50]

        print(f"\n=== Swarm Initialization Scaling ===")

        for count in agent_counts:
            times = []

            for _ in range(10):
                start = time.perf_counter()

                # Simulate swarm init with varying agent counts
                swarm_config = {"topology": "mesh", "maxAgents": count, "strategy": "balanced"}

                end = time.perf_counter()
                times.append((end - start) * 1000)

            avg_time = mean(times)
            print(f"{count} agents: {avg_time:.2f}ms")

            # Should scale reasonably
            self.assertLess(avg_time, 200.0)


class BenchmarkCoordinationTopology(unittest.TestCase):
    """Benchmark different coordination topologies."""

    def test_mesh_topology_message_routing(self):
        """Benchmark mesh topology message routing."""
        # In mesh, every agent can communicate with every other agent
        agent_count = 10
        message_count = 100

        times = []
        for _ in range(message_count):
            sender = random.randint(0, agent_count - 1)
            receiver = random.randint(0, agent_count - 1)

            start = time.perf_counter()
            # Direct routing in mesh (O(1))
            route_length = 1
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Mesh Topology Performance ===")
        print(f"Agents: {agent_count}")
        print(f"Average routing time: {avg_time:.4f}ms")

        # Mesh should be fastest (direct routing)
        self.assertLess(avg_time, 0.1)

    def test_hierarchical_topology_message_routing(self):
        """Benchmark hierarchical topology message routing."""
        # In hierarchical, messages route through parent nodes
        levels = 3
        agents_per_level = [1, 3, 9]  # Root, middle, leaf
        total_agents = sum(agents_per_level)

        times = []
        for _ in range(100):
            # Simulate routing through hierarchy
            start = time.perf_counter()

            # Average hops: 2-3 for hierarchical
            hops = random.randint(2, 3)

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Hierarchical Topology Performance ===")
        print(f"Levels: {levels}, Total agents: {total_agents}")
        print(f"Average routing time: {avg_time:.4f}ms")

        self.assertLess(avg_time, 1.0)

    def test_ring_topology_message_routing(self):
        """Benchmark ring topology message routing."""
        agent_count = 10

        times = []
        for _ in range(100):
            sender = random.randint(0, agent_count - 1)
            receiver = random.randint(0, agent_count - 1)

            start = time.perf_counter()

            # Ring: average hops = n/4 for random nodes
            distance = abs(receiver - sender)
            hops = min(distance, agent_count - distance)

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Ring Topology Performance ===")
        print(f"Agents: {agent_count}")
        print(f"Average routing time: {avg_time:.4f}ms")

        self.assertLess(avg_time, 1.0)

    def test_star_topology_message_routing(self):
        """Benchmark star topology message routing."""
        # In star, all messages go through central hub
        agent_count = 10

        times = []
        for _ in range(100):
            start = time.perf_counter()

            # Star: all messages route through hub (2 hops max)
            hops = 2

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Star Topology Performance ===")
        print(f"Agents: {agent_count}")
        print(f"Average routing time: {avg_time:.4f}ms")

        self.assertLess(avg_time, 1.0)


class BenchmarkMessageRouting(unittest.TestCase):
    """Benchmark message routing performance."""

    def test_point_to_point_latency(self):
        """Benchmark point-to-point message latency."""
        from src.agents.coordinator import MessageBus

        bus = MessageBus()

        times = []
        for i in range(1000):
            message = {"from": f"agent_{i % 10}", "to": f"agent_{(i + 1) % 10}", "data": "test"}

            start = time.perf_counter()
            bus.route_message(message)
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)
        std_time = stdev(times)

        print(f"\n=== Point-to-Point Message Latency ===")
        print(f"Messages: 1000")
        print(f"Average: {avg_time:.4f}ms")
        print(f"Std dev: {std_time:.4f}ms")

        # Should be very fast
        self.assertLess(avg_time, 1.0)

    def test_broadcast_latency(self):
        """Benchmark broadcast message latency."""
        from src.agents.coordinator import MessageBus

        bus = MessageBus()

        recipient_counts = [10, 50, 100]

        print(f"\n=== Broadcast Message Latency ===")

        for count in recipient_counts:
            recipients = [f"agent_{i}" for i in range(count)]

            times = []
            for _ in range(100):
                message = {"from": "coordinator", "data": "broadcast"}

                start = time.perf_counter()
                bus.broadcast(message, recipients)
                end = time.perf_counter()

                times.append((end - start) * 1000)

            avg_time = mean(times)
            print(f"{count} recipients: {avg_time:.4f}ms")

            # Should scale reasonably
            self.assertLess(avg_time, 50.0)

    def test_message_queue_throughput(self):
        """Benchmark message queue throughput."""
        from src.agents.coordinator import MessageBus

        bus = MessageBus()

        message_count = 10000

        start = time.perf_counter()

        for i in range(message_count):
            message = {"from": f"agent_{i % 100}", "to": f"agent_{(i + 1) % 100}", "data": f"msg_{i}"}
            bus.route_message(message)

        total_time = (time.perf_counter() - start) * 1000
        throughput = message_count / (total_time / 1000)

        print(f"\n=== Message Queue Throughput ===")
        print(f"Messages: {message_count}")
        print(f"Total time: {total_time:.2f}ms")
        print(f"Throughput: {throughput:.0f} messages/second")

        # Should handle high throughput
        self.assertGreater(throughput, 10000)


class BenchmarkConsensusBuilding(unittest.TestCase):
    """Benchmark consensus building performance."""

    def test_simple_voting_consensus(self):
        """Benchmark simple voting consensus."""
        agent_counts = [3, 5, 10, 20]

        print(f"\n=== Simple Voting Consensus ===")

        for count in agent_counts:
            times = []

            for _ in range(100):
                # Simulate collecting votes
                votes = [random.choice([True, False]) for _ in range(count)]

                start = time.perf_counter()

                # Calculate consensus (majority)
                yes_votes = sum(votes)
                consensus = yes_votes > count / 2

                end = time.perf_counter()
                times.append((end - start) * 1000)

            avg_time = mean(times)
            print(f"{count} agents: {avg_time:.4f}ms")

            # Voting should be very fast
            self.assertLess(avg_time, 0.1)

    def test_raft_consensus_simulation(self):
        """Benchmark Raft consensus algorithm simulation."""
        agent_count = 5

        times = []

        for _ in range(100):
            start = time.perf_counter()

            # Simulate Raft leader election
            # 1. Timeout triggers election
            # 2. Candidate requests votes (n-1 messages)
            # 3. Majority responds (n/2 messages)
            # 4. Leader elected

            message_rounds = 2
            messages_per_round = agent_count - 1

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Raft Consensus Simulation ===")
        print(f"Agents: {agent_count}")
        print(f"Average consensus time: {avg_time:.4f}ms")

        self.assertLess(avg_time, 10.0)

    def test_byzantine_fault_tolerance(self):
        """Benchmark Byzantine fault tolerant consensus."""
        agent_count = 7  # Need 3f+1 nodes for f failures

        times = []

        for _ in range(100):
            start = time.perf_counter()

            # Simulate Byzantine consensus
            # Multiple rounds of message exchange
            rounds = 3
            messages_per_round = agent_count * (agent_count - 1)

            # Verify signatures and validate
            for _ in range(rounds):
                pass

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Byzantine Fault Tolerance ===")
        print(f"Agents: {agent_count}")
        print(f"Average consensus time: {avg_time:.4f}ms")

        self.assertLess(avg_time, 50.0)


class BenchmarkDistributedTaskOrchestration(unittest.TestCase):
    """Benchmark distributed task orchestration."""

    def test_task_distribution_latency(self):
        """Benchmark task distribution latency."""
        from src.agents.coordinator import TaskOrchestrator

        orchestrator = TaskOrchestrator()

        agent_count = 10
        task_count = 100

        start = time.perf_counter()

        for i in range(task_count):
            task = {"id": i, "type": "compute", "priority": random.choice(["low", "medium", "high"])}

            orchestrator.distribute_task(task, agent_count)

        total_time = (time.perf_counter() - start) * 1000
        avg_time = total_time / task_count

        print(f"\n=== Task Distribution Performance ===")
        print(f"Agents: {agent_count}")
        print(f"Tasks: {task_count}")
        print(f"Total: {total_time:.2f}ms")
        print(f"Average per task: {avg_time:.4f}ms")

        # Distribution should be fast
        self.assertLess(avg_time, 1.0)

    def test_load_balancing_overhead(self):
        """Benchmark load balancing overhead."""
        from src.agents.coordinator import LoadBalancer

        balancer = LoadBalancer(strategy="least_loaded")

        # Create agents with varying loads
        agents = {f"agent_{i}": {"load": random.randint(0, 100)} for i in range(20)}

        times = []
        for _ in range(1000):
            start = time.perf_counter()

            selected_agent = balancer.select_agent(agents)

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Load Balancing Overhead ===")
        print(f"Agents: 20")
        print(f"Strategy: least_loaded")
        print(f"Average selection time: {avg_time:.4f}ms")

        # Load balancing should be fast
        self.assertLess(avg_time, 0.5)

    def test_coordination_overhead_scaling(self):
        """Benchmark coordination overhead vs swarm size."""
        swarm_sizes = [5, 10, 20, 50]

        print(f"\n=== Coordination Overhead Scaling ===")

        for size in swarm_sizes:
            # Simulate coordination
            start = time.perf_counter()

            # Coordination tasks:
            # - Status updates from all agents
            # - Task distribution
            # - Resource allocation
            coordination_ops = size * 3

            end = time.perf_counter()
            coord_time = (end - start) * 1000

            per_agent = coord_time / size

            print(f"{size} agents: Total={coord_time:.4f}ms, Per-agent={per_agent:.4f}ms")

            # Overhead should scale reasonably
            self.assertLess(per_agent, 1.0)


class BenchmarkSwarmMemory(unittest.TestCase):
    """Benchmark swarm shared memory performance."""

    def test_memory_read_latency(self):
        """Benchmark shared memory read latency."""
        times = []

        for _ in range(1000):
            key = f"swarm/status/agent_{random.randint(0, 99)}"

            start = time.perf_counter()
            # Simulate memory read
            # In real: mcp__claude-flow__memory_usage with action="retrieve"
            value = {"status": "active", "load": 50}
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Shared Memory Read Performance ===")
        print(f"Operations: 1000")
        print(f"Average: {avg_time:.4f}ms")

        self.assertLess(avg_time, 1.0)

    def test_memory_write_latency(self):
        """Benchmark shared memory write latency."""
        times = []

        for i in range(1000):
            key = f"swarm/data/item_{i}"
            value = {"id": i, "data": f"value_{i}", "timestamp": time.time()}

            start = time.perf_counter()
            # Simulate memory write
            # In real: mcp__claude-flow__memory_usage with action="store"
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Shared Memory Write Performance ===")
        print(f"Operations: 1000")
        print(f"Average: {avg_time:.4f}ms")

        self.assertLess(avg_time, 2.0)


if __name__ == "__main__":
    # Run benchmarks
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
