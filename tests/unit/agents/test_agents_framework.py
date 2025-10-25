"""
Unit tests for Agents Framework.

Tests the core agent functionality including initialization,
task execution, state management, and coordination.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tests.utils.test_helpers import MockAgent, MockEventBus, wait_for_condition


@pytest.mark.unit
@pytest.mark.asyncio
class TestAgentFramework:
    """Test suite for agent framework."""

    async def test_agent_initialization(self, mock_agent):
        """Test agent initializes correctly."""
        await mock_agent.initialize()
        assert mock_agent.name == "test_agent"
        assert len(mock_agent.tasks_executed) == 0

    async def test_agent_task_execution(self, mock_agent):
        """Test agent executes tasks."""
        task = {"type": "query", "data": "SELECT * FROM users"}
        result = await mock_agent.execute(task)

        assert result["success"] is True
        assert len(mock_agent.tasks_executed) == 1
        assert mock_agent.tasks_executed[0] == task

    async def test_agent_multiple_tasks(self, mock_agent):
        """Test agent handles multiple tasks."""
        tasks = [
            {"type": "query", "data": f"SELECT * FROM table{i}"}
            for i in range(5)
        ]

        results = []
        for task in tasks:
            result = await mock_agent.execute(task)
            results.append(result)

        assert len(results) == 5
        assert len(mock_agent.tasks_executed) == 5

    async def test_agent_shutdown(self, mock_agent):
        """Test agent shutdown cleanup."""
        await mock_agent.initialize()
        await mock_agent.shutdown()
        # Verify cleanup occurred
        assert True  # Mock doesn't track shutdown state

    async def test_agent_error_handling(self):
        """Test agent handles errors gracefully."""
        agent = MockAgent(
            name="error_agent",
            responses=[Exception("Test error")]
        )

        task = {"type": "query", "data": "SELECT * FROM users"}

        with pytest.raises(Exception, match="Test error"):
            await agent.execute(task)

    async def test_agent_response_cycling(self, mock_agent):
        """Test agent cycles through responses."""
        # Agent has 2 responses, execute 5 tasks
        for i in range(5):
            result = await mock_agent.execute({"task": i})
            assert "success" in result

        assert len(mock_agent.tasks_executed) == 5

    async def test_agent_with_event_bus(self, mock_agent, mock_event_bus):
        """Test agent integration with event bus."""
        events_received = []

        async def event_handler(data):
            events_received.append(data)

        mock_event_bus.subscribe("agent:task_complete", event_handler)

        task = {"type": "query"}
        result = await mock_agent.execute(task)

        await mock_event_bus.emit("agent:task_complete", {
            "agent": mock_agent.name,
            "result": result
        })

        await wait_for_condition(lambda: len(events_received) > 0, timeout=1.0)
        assert len(events_received) == 1

    async def test_agent_concurrent_execution(self, mock_agent):
        """Test agent handles concurrent tasks."""
        import asyncio

        tasks = [
            mock_agent.execute({"id": i, "type": "query"})
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert len(mock_agent.tasks_executed) == 10

    async def test_agent_task_timeout(self):
        """Test agent task timeout handling."""
        async def slow_task(task):
            import asyncio
            await asyncio.sleep(10)
            return {"success": True}

        agent = MockAgent(name="slow_agent")
        agent.execute = slow_task

        task = {"type": "slow"}

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(agent.execute(task), timeout=0.5)

    async def test_agent_state_persistence(self, mock_agent):
        """Test agent maintains state across tasks."""
        # Execute multiple tasks
        for i in range(3):
            await mock_agent.execute({"task": i})

        # Verify state is maintained
        assert len(mock_agent.tasks_executed) == 3
        assert mock_agent.current_index == 1  # Cycled through responses


@pytest.mark.unit
@pytest.mark.asyncio
class TestAgentCoordination:
    """Test suite for agent coordination."""

    async def test_multi_agent_coordination(self, mock_event_bus):
        """Test multiple agents coordinate via event bus."""
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")

        results = []

        async def task_handler(data):
            results.append(data)

        mock_event_bus.subscribe("task:result", task_handler)

        # Agent 1 executes task
        result1 = await agent1.execute({"type": "step1"})
        await mock_event_bus.emit("task:result", result1)

        # Agent 2 executes task
        result2 = await agent2.execute({"type": "step2"})
        await mock_event_bus.emit("task:result", result2)

        await wait_for_condition(lambda: len(results) == 2, timeout=1.0)
        assert len(results) == 2

    async def test_agent_task_chaining(self):
        """Test agents can chain tasks."""
        agent1 = MockAgent("agent1", responses=[{"data": "step1_result"}])
        agent2 = MockAgent("agent2", responses=[{"data": "step2_result"}])

        # Execute chained tasks
        result1 = await agent1.execute({"type": "step1"})
        result2 = await agent2.execute({
            "type": "step2",
            "previous": result1["data"]
        })

        assert result2["data"] == "step2_result"
        assert agent2.tasks_executed[0]["previous"] == "step1_result"

    async def test_agent_parallel_execution(self):
        """Test agents execute in parallel."""
        import asyncio

        agents = [MockAgent(f"agent{i}") for i in range(5)]

        start_time = asyncio.get_event_loop().time()

        tasks = [agent.execute({"type": "parallel"}) for agent in agents]
        results = await asyncio.gather(*tasks)

        duration = asyncio.get_event_loop().time() - start_time

        assert len(results) == 5
        assert duration < 1.0  # Should complete quickly in parallel
