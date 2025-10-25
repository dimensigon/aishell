"""
Mock classes for agent coordination testing.

Provides lightweight mock implementations for testing performance
without requiring full system initialization.
"""

from typing import Dict, Any, List, Optional, Deque, Callable
from collections import deque
import time


class TaskQueue:
    """Mock task queue for testing."""

    def __init__(self) -> None:
        self._queue: Deque[Dict[str, Any]] = deque()

    def enqueue(self, task: Dict[str, Any]) -> None:
        """Add task to queue."""
        self._queue.append(task)

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """Remove and return task from queue."""
        if self._queue:
            return self._queue.popleft()
        return None

    def size(self) -> int:
        """Get queue size."""
        return len(self._queue)


class AgentCoordinator:
    """Mock agent coordinator for testing."""

    def __init__(self) -> None:
        self._agents: Dict[str, Any] = {}
        self._task_assignments: List[Dict[str, Any]] = []

    def register_agent(self, agent: Any) -> None:
        """Register an agent."""
        agent_id: str = agent.config.agent_id if hasattr(agent, 'config') else agent.agent_id
        self._agents[agent_id] = agent

    def assign_task(self, task: Dict[str, Any]) -> str:
        """Assign task to least loaded agent."""
        if not self._agents:
            raise ValueError("No agents registered")

        # Simple round-robin assignment
        agent_id: str = list(self._agents.keys())[len(self._task_assignments) % len(self._agents)]
        self._task_assignments.append({
            'task': task,
            'agent_id': agent_id,
            'timestamp': time.time()
        })

        return agent_id


class AgentMessage:
    """Mock agent message."""

    def __init__(self, sender: str, receiver: str, message_type: str, payload: Dict[str, Any]) -> None:
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type
        self.payload = payload
        self.timestamp = time.time()


class MessageBus:
    """Mock message bus for testing."""

    def __init__(self) -> None:
        self._messages: Dict[str, List[AgentMessage]] = {}  # agent_id -> list of messages

    def send_message(self, message: AgentMessage) -> None:
        """Send message to receiver."""
        if message.receiver not in self._messages:
            self._messages[message.receiver] = []
        self._messages[message.receiver].append(message)

    def get_messages(self, agent_id: str) -> List[AgentMessage]:
        """Get messages for agent."""
        return self._messages.get(agent_id, [])

    def broadcast(self, message: Dict[str, Any], agent_ids: List[str]) -> None:
        """Broadcast message to multiple agents."""
        for agent_id in agent_ids:
            msg = AgentMessage(
                sender='broadcast',
                receiver=agent_id,
                message_type='broadcast',
                payload=message
            )
            self.send_message(msg)

    def route_message(self, message: Dict[str, Any]) -> None:
        """Route a message."""
        msg = AgentMessage(
            sender=message.get('from', 'unknown'),
            receiver=message.get('to', 'unknown'),
            message_type='direct',
            payload=message.get('data', {})
        )
        self.send_message(msg)


class TaskOrchestrator:
    """Mock task orchestrator for testing."""

    def __init__(self) -> None:
        self._tasks: List[Dict[str, Any]] = []

    def distribute_task(self, task: Dict[str, Any], agent_count: int) -> None:
        """Distribute task across agents."""
        self._tasks.append({
            'task': task,
            'agent_count': agent_count,
            'timestamp': time.time()
        })


class LoadBalancer:
    """Mock load balancer for testing."""

    def __init__(self, strategy: str = "least_loaded") -> None:
        self.strategy = strategy

    def select_agent(self, agents: Dict[str, Dict[str, Any]]) -> str:
        """Select agent based on strategy."""
        if not agents:
            raise ValueError("No agents available")

        if self.strategy == "least_loaded":
            # Find agent with lowest load
            return min(agents.items(), key=lambda x: x[1].get('load', 0))[0]
        elif self.strategy == "round_robin":
            # Simple round-robin
            return list(agents.keys())[0]
        else:
            # Default to first agent
            return list(agents.keys())[0]


class ParallelExecutor:
    """Mock parallel executor for testing."""

    def __init__(self, max_workers: int = 10) -> None:
        self.max_workers = max_workers

    def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """Execute tasks in parallel (simulated)."""
        results: List[Any] = []
        for task in tasks:
            # Simulate execution
            executor: Optional[Callable[..., Any]] = task.get('executor')
            args: tuple[Any, ...] = task.get('args', ())
            if executor:
                result: Any = executor(*args)
                results.append(result)
        return results
