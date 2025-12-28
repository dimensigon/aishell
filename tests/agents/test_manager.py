"""
Comprehensive unit tests for AgentManager

Tests agent lifecycle, task management, communication, and coordination.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from src.agents.manager import (
    AgentInfo,
    AgentManager,
    AgentMessage,
    AgentType,
    CommunicationType,
    ManagedTask,
    TaskStatus,
)
from src.agents.base import (
    AgentCapability,
    AgentState,
    TaskContext,
    TaskResult,
)


@pytest.fixture
def mock_llm_manager():
    """Mock LLM manager"""
    manager = Mock()
    manager.generate = AsyncMock(return_value="Generated response")
    manager.explain_query = Mock(return_value="Query explanation")
    return manager


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry"""
    registry = Mock()
    registry.get_tool = Mock()
    return registry


@pytest.fixture
def mock_state_manager():
    """Mock state manager"""
    manager = AsyncMock()
    manager.save_checkpoint = AsyncMock()
    manager.get_checkpoints = AsyncMock(return_value=[])
    return manager


@pytest.fixture
def mock_performance_monitor():
    """Mock performance monitor"""
    monitor = Mock()
    monitor.record_query = Mock()
    return monitor


@pytest.fixture
async def agent_manager(
    mock_llm_manager, mock_tool_registry, mock_state_manager, mock_performance_monitor
):
    """Create agent manager instance"""
    manager = AgentManager(
        llm_manager=mock_llm_manager,
        tool_registry=mock_tool_registry,
        state_manager=mock_state_manager,
        performance_monitor=mock_performance_monitor,
        max_concurrent_tasks=5,
    )
    await manager.start()
    yield manager
    await manager.stop()


class TestAgentManagerInitialization:
    """Test AgentManager initialization"""

    def test_initialization(
        self,
        mock_llm_manager,
        mock_tool_registry,
        mock_state_manager,
        mock_performance_monitor,
    ):
        """Test manager initializes correctly"""
        manager = AgentManager(
            llm_manager=mock_llm_manager,
            tool_registry=mock_tool_registry,
            state_manager=mock_state_manager,
            performance_monitor=mock_performance_monitor,
            max_concurrent_tasks=10,
        )

        assert manager.llm_manager == mock_llm_manager
        assert manager.tool_registry == mock_tool_registry
        assert manager.state_manager == mock_state_manager
        assert manager.performance_monitor == mock_performance_monitor
        assert manager.max_concurrent_tasks == 10
        assert len(manager._agents) == 0
        assert not manager._running

    @pytest.mark.asyncio
    async def test_start_stop(self, agent_manager):
        """Test manager start and stop"""
        assert agent_manager._running
        assert len(agent_manager._worker_tasks) > 0

        await agent_manager.stop()
        assert not agent_manager._running


class TestAgentLifecycle:
    """Test agent lifecycle management"""

    @pytest.mark.asyncio
    async def test_create_agent(self, agent_manager):
        """Test creating an agent"""
        agent_id = await agent_manager.create_agent(
            agent_type=AgentType.COMMAND,
            capabilities=[AgentCapability.FILE_READ],
            config={"allowed_commands": ["ls", "cat"]},
        )

        assert agent_id in agent_manager._agents
        agent_info = agent_manager._agents[agent_id]
        assert agent_info.agent_type == AgentType.COMMAND
        assert AgentCapability.FILE_READ in agent_info.capabilities
        assert agent_info.status == AgentState.IDLE

    @pytest.mark.asyncio
    async def test_create_agent_custom_id(self, agent_manager):
        """Test creating agent with custom ID"""
        custom_id = "my-custom-agent"
        agent_id = await agent_manager.create_agent(
            agent_type=AgentType.RESEARCH,
            agent_id=custom_id,
        )

        assert agent_id == custom_id
        assert custom_id in agent_manager._agents

    @pytest.mark.asyncio
    async def test_create_duplicate_agent_fails(self, agent_manager):
        """Test creating duplicate agent fails"""
        agent_id = await agent_manager.create_agent(agent_type=AgentType.CODE)

        with pytest.raises(ValueError, match="already exists"):
            await agent_manager.create_agent(
                agent_type=AgentType.CODE, agent_id=agent_id
            )

    @pytest.mark.asyncio
    async def test_destroy_agent(self, agent_manager):
        """Test destroying an agent"""
        agent_id = await agent_manager.create_agent(agent_type=AgentType.ANALYSIS)

        assert agent_id in agent_manager._agents

        success = await agent_manager.destroy_agent(agent_id)

        assert success
        assert agent_id not in agent_manager._agents

    @pytest.mark.asyncio
    async def test_destroy_nonexistent_agent(self, agent_manager):
        """Test destroying nonexistent agent"""
        success = await agent_manager.destroy_agent("nonexistent")
        assert not success

    @pytest.mark.asyncio
    async def test_start_agent(self, agent_manager):
        """Test starting an agent"""
        agent_id = await agent_manager.create_agent(agent_type=AgentType.COMMAND)

        success = await agent_manager.start_agent(agent_id)

        assert success
        agent_info = agent_manager._agents[agent_id]
        assert agent_info.status == AgentState.IDLE

    @pytest.mark.asyncio
    async def test_stop_agent(self, agent_manager):
        """Test stopping an agent"""
        agent_id = await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        await agent_manager.start_agent(agent_id)

        success = await agent_manager.stop_agent(agent_id)

        assert success
        agent_info = agent_manager._agents[agent_id]
        assert agent_info.status == AgentState.PAUSED


class TestAgentDiscovery:
    """Test agent discovery and querying"""

    @pytest.mark.asyncio
    async def test_get_agent(self, agent_manager):
        """Test getting agent info"""
        agent_id = await agent_manager.create_agent(agent_type=AgentType.RESEARCH)

        agent_info = agent_manager.get_agent(agent_id)

        assert agent_info is not None
        assert agent_info.agent_id == agent_id
        assert agent_info.agent_type == AgentType.RESEARCH

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, agent_manager):
        """Test getting nonexistent agent"""
        agent_info = agent_manager.get_agent("nonexistent")
        assert agent_info is None

    @pytest.mark.asyncio
    async def test_list_all_agents(self, agent_manager):
        """Test listing all agents"""
        await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        await agent_manager.create_agent(agent_type=AgentType.RESEARCH)
        await agent_manager.create_agent(agent_type=AgentType.CODE)

        agents = agent_manager.list_agents()

        assert len(agents) == 3

    @pytest.mark.asyncio
    async def test_list_agents_by_type(self, agent_manager):
        """Test listing agents by type"""
        await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        await agent_manager.create_agent(agent_type=AgentType.RESEARCH)

        command_agents = agent_manager.list_agents(agent_type=AgentType.COMMAND)
        research_agents = agent_manager.list_agents(agent_type=AgentType.RESEARCH)

        assert len(command_agents) == 2
        assert len(research_agents) == 1

    @pytest.mark.asyncio
    async def test_list_agents_by_capability(self, agent_manager):
        """Test listing agents by capability"""
        await agent_manager.create_agent(
            agent_type=AgentType.COMMAND,
            capabilities=[AgentCapability.FILE_READ],
        )
        await agent_manager.create_agent(
            agent_type=AgentType.RESEARCH,
            capabilities=[AgentCapability.FILE_READ, AgentCapability.DATABASE_READ],
        )
        await agent_manager.create_agent(
            agent_type=AgentType.CODE,
            capabilities=[AgentCapability.DATABASE_READ],
        )

        file_agents = agent_manager.list_agents(capability=AgentCapability.FILE_READ)
        db_agents = agent_manager.list_agents(capability=AgentCapability.DATABASE_READ)

        assert len(file_agents) == 2
        assert len(db_agents) == 2

    @pytest.mark.asyncio
    async def test_list_agents_by_status(self, agent_manager):
        """Test listing agents by status"""
        agent_id1 = await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        agent_id2 = await agent_manager.create_agent(agent_type=AgentType.RESEARCH)

        await agent_manager.stop_agent(agent_id2)

        idle_agents = agent_manager.list_agents(status=AgentState.IDLE)
        paused_agents = agent_manager.list_agents(status=AgentState.PAUSED)

        assert len(idle_agents) == 1
        assert len(paused_agents) == 1

    @pytest.mark.asyncio
    async def test_find_agent_for_task(self, agent_manager):
        """Test finding suitable agent for task"""
        await agent_manager.create_agent(
            agent_type=AgentType.COMMAND,
            capabilities=[AgentCapability.FILE_READ],
        )

        task_context = TaskContext(
            task_id="test-task",
            task_description="Read a file",
            input_data={},
            metadata={"required_capabilities": [AgentCapability.FILE_READ]},
        )

        agent_id = agent_manager.find_agent_for_task(task_context)

        assert agent_id is not None
        agent_info = agent_manager.get_agent(agent_id)
        assert AgentCapability.FILE_READ in agent_info.capabilities


class TestTaskManagement:
    """Test task management"""

    @pytest.mark.asyncio
    async def test_submit_task(self, agent_manager):
        """Test submitting a task"""
        task_context = TaskContext(
            task_id="task-1",
            task_description="Test task",
            input_data={"test": "data"},
        )

        task_id = await agent_manager.submit_task(task_context, priority=2)

        assert task_id == "task-1"
        assert task_id in agent_manager._tasks
        managed_task = agent_manager._tasks[task_id]
        assert managed_task.status == TaskStatus.PENDING
        assert managed_task.priority == 2

    @pytest.mark.asyncio
    async def test_submit_task_with_agent(self, agent_manager):
        """Test submitting task with specific agent"""
        agent_id = await agent_manager.create_agent(agent_type=AgentType.COMMAND)

        task_context = TaskContext(
            task_id="task-2",
            task_description="Test task",
            input_data={},
        )

        task_id = await agent_manager.submit_task(
            task_context, priority=1, agent_id=agent_id
        )

        managed_task = agent_manager._tasks[task_id]
        assert managed_task.assigned_agent == agent_id
        assert managed_task.status == TaskStatus.ASSIGNED

    @pytest.mark.asyncio
    async def test_submit_duplicate_task_fails(self, agent_manager):
        """Test submitting duplicate task fails"""
        task_context = TaskContext(
            task_id="task-3",
            task_description="Test task",
            input_data={},
        )

        await agent_manager.submit_task(task_context)

        with pytest.raises(ValueError, match="already exists"):
            await agent_manager.submit_task(task_context)

    @pytest.mark.asyncio
    async def test_get_task_status(self, agent_manager):
        """Test getting task status"""
        task_context = TaskContext(
            task_id="task-4",
            task_description="Test task",
            input_data={},
        )

        await agent_manager.submit_task(task_context)
        status = await agent_manager.get_task_status("task-4")

        assert status is not None
        assert status["task_id"] == "task-4"
        assert status["status"] == TaskStatus.PENDING.value
        assert status["created_at"] is not None

    @pytest.mark.asyncio
    async def test_get_nonexistent_task_status(self, agent_manager):
        """Test getting nonexistent task status"""
        status = await agent_manager.get_task_status("nonexistent")
        assert status is None


class TestInterAgentCommunication:
    """Test inter-agent communication"""

    @pytest.mark.asyncio
    async def test_send_message(self, agent_manager):
        """Test sending message between agents"""
        agent1 = await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        agent2 = await agent_manager.create_agent(agent_type=AgentType.RESEARCH)

        message_id = await agent_manager.send_message(
            from_agent=agent1,
            to_agent=agent2,
            message_type=CommunicationType.REQUEST,
            payload={"data": "test"},
        )

        assert message_id is not None
        assert message_id.startswith("msg-")

    @pytest.mark.asyncio
    async def test_broadcast_message(self, agent_manager):
        """Test broadcasting message to all agents"""
        await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        await agent_manager.create_agent(agent_type=AgentType.RESEARCH)
        await agent_manager.create_agent(agent_type=AgentType.CODE)

        message_id = await agent_manager.send_message(
            from_agent="sender",
            to_agent=None,  # Broadcast
            message_type=CommunicationType.BROADCAST,
            payload={"announcement": "test"},
        )

        assert message_id is not None

    @pytest.mark.asyncio
    async def test_register_message_handler(self, agent_manager):
        """Test registering message handler"""
        agent_id = await agent_manager.create_agent(agent_type=AgentType.COMMAND)

        received_messages = []

        def handler(message: AgentMessage):
            received_messages.append(message)

        agent_manager.register_message_handler(agent_id, handler)

        assert agent_id in agent_manager._message_handlers
        assert len(agent_manager._message_handlers[agent_id]) == 1

    @pytest.mark.asyncio
    async def test_message_delivery(self, agent_manager):
        """Test message is delivered to handler"""
        agent1 = await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        agent2 = await agent_manager.create_agent(agent_type=AgentType.RESEARCH)

        received_messages = []

        def handler(message: AgentMessage):
            received_messages.append(message)

        agent_manager.register_message_handler(agent2, handler)

        await agent_manager.send_message(
            from_agent=agent1,
            to_agent=agent2,
            message_type=CommunicationType.NOTIFY,
            payload={"test": "data"},
        )

        # Wait for message processing
        await asyncio.sleep(0.2)

        assert len(received_messages) == 1
        assert received_messages[0].from_agent == agent1
        assert received_messages[0].payload["test"] == "data"


class TestContextSharing:
    """Test shared context management"""

    @pytest.mark.asyncio
    async def test_set_shared_context(self, agent_manager):
        """Test setting shared context"""
        agent_manager.set_shared_context("key1", "value1")

        assert agent_manager.get_shared_context("key1") == "value1"

    @pytest.mark.asyncio
    async def test_get_shared_context_default(self, agent_manager):
        """Test getting nonexistent context with default"""
        value = agent_manager.get_shared_context("nonexistent", "default")
        assert value == "default"

    @pytest.mark.asyncio
    async def test_update_shared_context(self, agent_manager):
        """Test updating multiple context values"""
        updates = {"key1": "value1", "key2": "value2", "key3": "value3"}

        agent_manager.update_shared_context(updates)

        assert agent_manager.get_shared_context("key1") == "value1"
        assert agent_manager.get_shared_context("key2") == "value2"
        assert agent_manager.get_shared_context("key3") == "value3"

    @pytest.mark.asyncio
    async def test_clear_shared_context(self, agent_manager):
        """Test clearing shared context"""
        agent_manager.set_shared_context("key1", "value1")
        agent_manager.set_shared_context("key2", "value2")

        agent_manager.clear_shared_context()

        assert agent_manager.get_shared_context("key1") is None
        assert agent_manager.get_shared_context("key2") is None


class TestResultAggregation:
    """Test result aggregation"""

    @pytest.mark.asyncio
    async def test_aggregate_results_merge(self, agent_manager):
        """Test merging results"""
        # Create mock tasks with results
        task1 = ManagedTask(
            task_id="task-1",
            context=TaskContext(
                task_id="task-1", task_description="Test", input_data={}
            ),
            status=TaskStatus.COMPLETED,
        )
        task1.result = TaskResult(
            task_id="task-1",
            agent_id="agent-1",
            status="success",
            output_data={"result1": "value1"},
            actions_taken=[],
            reasoning="",
            execution_time=1.0,
            checkpoints=[],
        )

        task2 = ManagedTask(
            task_id="task-2",
            context=TaskContext(
                task_id="task-2", task_description="Test", input_data={}
            ),
            status=TaskStatus.COMPLETED,
        )
        task2.result = TaskResult(
            task_id="task-2",
            agent_id="agent-2",
            status="success",
            output_data={"result2": "value2"},
            actions_taken=[],
            reasoning="",
            execution_time=1.0,
            checkpoints=[],
        )

        agent_manager._tasks["task-1"] = task1
        agent_manager._tasks["task-2"] = task2

        aggregated = await agent_manager.aggregate_results(
            ["task-1", "task-2"], strategy="merge"
        )

        assert "result1" in aggregated
        assert "result2" in aggregated
        assert aggregated["result1"] == "value1"
        assert aggregated["result2"] == "value2"

    @pytest.mark.asyncio
    async def test_aggregate_results_list(self, agent_manager):
        """Test listing results"""
        task1 = ManagedTask(
            task_id="task-1",
            context=TaskContext(
                task_id="task-1", task_description="Test", input_data={}
            ),
            status=TaskStatus.COMPLETED,
        )
        task1.result = TaskResult(
            task_id="task-1",
            agent_id="agent-1",
            status="success",
            output_data={"data": "value1"},
            actions_taken=[],
            reasoning="",
            execution_time=1.0,
            checkpoints=[],
        )

        agent_manager._tasks["task-1"] = task1

        aggregated = await agent_manager.aggregate_results(["task-1"], strategy="list")

        assert "results" in aggregated
        assert "count" in aggregated
        assert aggregated["count"] == 1
        assert len(aggregated["results"]) == 1


class TestMonitoringAndStats:
    """Test monitoring and statistics"""

    @pytest.mark.asyncio
    async def test_get_stats(self, agent_manager):
        """Test getting manager statistics"""
        await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        await agent_manager.create_agent(agent_type=AgentType.RESEARCH)

        stats = agent_manager.get_stats()

        assert "agents" in stats
        assert "tasks" in stats
        assert "communication" in stats
        assert stats["agents"]["total"] == 2
        assert stats["running"] is True

    @pytest.mark.asyncio
    async def test_stats_by_type(self, agent_manager):
        """Test statistics by agent type"""
        await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        await agent_manager.create_agent(agent_type=AgentType.RESEARCH)

        stats = agent_manager.get_stats()

        assert stats["agents"]["by_type"]["command"] == 2
        assert stats["agents"]["by_type"]["research"] == 1

    @pytest.mark.asyncio
    async def test_stats_by_status(self, agent_manager):
        """Test statistics by agent status"""
        agent1 = await agent_manager.create_agent(agent_type=AgentType.COMMAND)
        agent2 = await agent_manager.create_agent(agent_type=AgentType.RESEARCH)

        await agent_manager.stop_agent(agent2)

        stats = agent_manager.get_stats()

        assert stats["agents"]["by_status"]["idle"] == 1
        assert stats["agents"]["by_status"]["paused"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
