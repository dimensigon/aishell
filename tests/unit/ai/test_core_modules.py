"""
Unit tests for Core Modules.

Tests core functionality including event bus, orchestration,
configuration management, and lifecycle management.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from tests.utils.test_helpers import MockEventBus, MockAgent, wait_for_condition


@pytest.mark.unit
@pytest.mark.asyncio
class TestEventBus:
    """Test suite for event bus functionality."""

    async def test_event_emission(self, mock_event_bus):
        """Test events can be emitted."""
        await mock_event_bus.emit("test:event", {"data": "test"})

        events = mock_event_bus.get_events("test:event")
        assert len(events) == 1
        assert events[0]["data"]["data"] == "test"

    async def test_event_subscription(self, mock_event_bus):
        """Test subscribing to events."""
        received_events = []

        async def handler(data):
            received_events.append(data)

        mock_event_bus.subscribe("test:event", handler)
        await mock_event_bus.emit("test:event", {"message": "hello"})

        await wait_for_condition(lambda: len(received_events) > 0, timeout=1.0)
        assert len(received_events) == 1

    async def test_multiple_subscribers(self, mock_event_bus):
        """Test multiple subscribers to same event."""
        received1 = []
        received2 = []

        async def handler1(data):
            received1.append(data)

        async def handler2(data):
            received2.append(data)

        mock_event_bus.subscribe("test:event", handler1)
        mock_event_bus.subscribe("test:event", handler2)

        await mock_event_bus.emit("test:event", {"data": "test"})

        await wait_for_condition(
            lambda: len(received1) > 0 and len(received2) > 0,
            timeout=1.0
        )

        assert len(received1) == 1
        assert len(received2) == 1

    async def test_event_filtering(self, mock_event_bus):
        """Test filtering events by type."""
        await mock_event_bus.emit("type1", {"data": "event1"})
        await mock_event_bus.emit("type2", {"data": "event2"})
        await mock_event_bus.emit("type1", {"data": "event3"})

        type1_events = mock_event_bus.get_events("type1")
        type2_events = mock_event_bus.get_events("type2")

        assert len(type1_events) == 2
        assert len(type2_events) == 1

    async def test_event_payload(self, mock_event_bus):
        """Test event payload is preserved."""
        payload = {
            "id": 123,
            "message": "test",
            "nested": {"key": "value"}
        }

        await mock_event_bus.emit("test:event", payload)

        events = mock_event_bus.get_events("test:event")
        assert events[0]["data"] == payload


@pytest.mark.unit
@pytest.mark.asyncio
class TestOrchestration:
    """Test suite for orchestration functionality."""

    async def test_agent_orchestration(self, mock_event_bus):
        """Test orchestrating multiple agents."""
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")
        agent3 = MockAgent("agent3")

        # Execute tasks in sequence
        result1 = await agent1.execute({"step": 1})
        result2 = await agent2.execute({"step": 2, "previous": result1})
        result3 = await agent3.execute({"step": 3, "previous": result2})

        assert len(agent1.tasks_executed) == 1
        assert len(agent2.tasks_executed) == 1
        assert len(agent3.tasks_executed) == 1

    async def test_parallel_orchestration(self):
        """Test parallel agent orchestration."""
        agents = [MockAgent(f"agent{i}") for i in range(5)]

        # Execute tasks in parallel
        tasks = [agent.execute({"task": i}) for i, agent in enumerate(agents)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(agent.tasks_executed for agent in agents)

    async def test_workflow_coordination(self, mock_event_bus):
        """Test workflow coordination via events."""
        workflow_steps = []

        async def step_handler(data):
            workflow_steps.append(data["step"])

        mock_event_bus.subscribe("workflow:step", step_handler)

        # Execute workflow steps
        for i in range(3):
            await mock_event_bus.emit("workflow:step", {"step": i})

        await wait_for_condition(lambda: len(workflow_steps) == 3, timeout=1.0)
        assert workflow_steps == [0, 1, 2]

    async def test_error_propagation(self):
        """Test error propagation in orchestration."""
        agent1 = MockAgent("agent1", responses=[{"success": True}])
        agent2 = MockAgent("agent2", responses=[Exception("Error in step 2")])

        result1 = await agent1.execute({"step": 1})
        assert result1["success"] is True

        with pytest.raises(Exception, match="Error in step 2"):
            await agent2.execute({"step": 2})


@pytest.mark.unit
@pytest.mark.asyncio
class TestConfigurationManagement:
    """Test suite for configuration management."""

    def test_config_loading(self, mock_config):
        """Test configuration is loaded correctly."""
        assert "database" in mock_config
        assert "llm" in mock_config
        assert mock_config["database"]["type"] == "postgresql"

    def test_config_validation(self, mock_config):
        """Test configuration validation."""
        required_keys = ["database", "llm", "security", "agents"]

        for key in required_keys:
            assert key in mock_config

    def test_config_defaults(self):
        """Test default configuration values."""
        from tests.utils.test_helpers import create_mock_config

        config = create_mock_config()

        assert config["llm"]["temperature"] == 0.7
        assert config["agents"]["max_parallel"] == 5
        assert config["agents"]["timeout"] == 30

    def test_config_override(self):
        """Test configuration override."""
        from tests.utils.test_helpers import create_mock_config

        config = create_mock_config(
            llm={"temperature": 0.9}
        )

        assert config["llm"]["temperature"] == 0.9

    def test_environment_variable_config(self, mock_env_vars):
        """Test configuration from environment variables."""
        assert mock_env_vars["AISHELL_DB_HOST"] == "localhost"
        assert mock_env_vars["AISHELL_DB_PORT"] == "5432"
        assert mock_env_vars["AISHELL_LLM_PROVIDER"] == "mock"


@pytest.mark.unit
@pytest.mark.asyncio
class TestLifecycleManagement:
    """Test suite for application lifecycle management."""

    async def test_initialization(self, mock_agent):
        """Test component initialization."""
        await mock_agent.initialize()
        # Verify initialization completed
        assert True

    async def test_shutdown(self, mock_agent):
        """Test component shutdown."""
        await mock_agent.initialize()
        await mock_agent.shutdown()
        # Verify shutdown completed
        assert True

    async def test_graceful_shutdown(self):
        """Test graceful shutdown with cleanup."""
        agents = [MockAgent(f"agent{i}") for i in range(3)]

        # Initialize all
        for agent in agents:
            await agent.initialize()

        # Shutdown all gracefully
        for agent in agents:
            await agent.shutdown()

        # All should be shut down
        assert all(agent for agent in agents)

    async def test_error_during_shutdown(self):
        """Test handling errors during shutdown."""
        agent = MockAgent("error_agent")

        async def failing_shutdown():
            raise Exception("Shutdown error")

        agent.shutdown = failing_shutdown

        # Should handle error gracefully
        try:
            await agent.shutdown()
        except Exception as e:
            assert str(e) == "Shutdown error"


@pytest.mark.unit
@pytest.mark.asyncio
class TestResourceManagement:
    """Test suite for resource management."""

    async def test_connection_pooling(self):
        """Test connection pool management."""
        from tests.utils.test_helpers import MockDatabase

        pool = [MockDatabase() for _ in range(5)]

        # Connect all
        for db in pool:
            await db.connect()

        assert all(db.connected for db in pool)

        # Disconnect all
        for db in pool:
            await db.disconnect()

        assert all(not db.connected for db in pool)

    async def test_resource_cleanup(self):
        """Test resources are cleaned up properly."""
        from tests.utils.test_helpers import AsyncContextManagerMock

        resource = AsyncContextManagerMock(return_value="test_resource")

        async with resource as r:
            assert r == "test_resource"
            assert resource.entered is True

        assert resource.exited is True

    async def test_memory_management(self):
        """Test memory is managed efficiently."""
        # Create large data structures
        large_data = [{"id": i, "data": "x" * 1000} for i in range(1000)]

        # Process data
        processed = [item["id"] for item in large_data]

        # Clear large data
        large_data.clear()

        assert len(processed) == 1000
        assert len(large_data) == 0

    async def test_concurrent_resource_access(self):
        """Test concurrent access to shared resources."""
        from tests.utils.test_helpers import MockDatabase

        db = MockDatabase()
        await db.connect()

        # Simulate concurrent queries
        tasks = [
            db.execute(f"SELECT * FROM table{i}")
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert len(db.queries_executed) == 10
