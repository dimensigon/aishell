"""
Comprehensive tests for src/agents/agent_chain.py to achieve 90%+ coverage.

Tests agent chaining, sequential execution, transformations, validations,
error handling, timeouts, and result aggregation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock

from src.agents.agent_chain import AgentChain, ChainLink, ChainResult


class TestChainLink:
    """Test ChainLink dataclass"""

    def test_chain_link_creation(self):
        """Test creating a chain link"""
        link = ChainLink(agent_type="coder", timeout=120)

        assert link.agent_type == "coder"
        assert link.timeout == 120
        assert link.transform is None
        assert link.validation is None

    def test_chain_link_with_transform(self):
        """Test link with transform function"""
        transform = lambda x: f"transformed: {x}"
        link = ChainLink("coder", transform=transform)

        assert link.transform is not None

    def test_chain_link_with_validation(self):
        """Test link with validation function"""
        validation = lambda x: len(x) > 0
        link = ChainLink("coder", validation=validation)

        assert link.validation is not None

    def test_chain_link_get_name(self):
        """Test getting link name"""
        link = ChainLink("coder")
        assert link.get_name() == "coder_link"

    def test_chain_link_get_name_custom(self):
        """Test getting custom link name"""
        link = ChainLink("coder", name="custom_link")
        assert link.get_name() == "custom_link"

    def test_chain_link_unique_ids(self):
        """Test each link has unique ID"""
        link1 = ChainLink("coder")
        link2 = ChainLink("coder")
        assert link1.link_id != link2.link_id


class TestChainResult:
    """Test ChainResult dataclass"""

    def test_get_link_output(self):
        """Test getting link output by index"""
        links = [
            ChainLink("coder"),
            ChainLink("tester")
        ]
        links[0].output_data = "output1"
        links[1].output_data = "output2"

        result = ChainResult(
            chain_id="123",
            chain_name="test",
            success=True,
            links=links,
            final_output="final",
            total_duration=1.0,
            start_time=None,
            end_time=None
        )

        assert result.get_link_output(0) == "output1"
        assert result.get_link_output(1) == "output2"

    def test_get_link_output_invalid_index(self):
        """Test getting output with invalid index"""
        result = ChainResult(
            chain_id="123",
            chain_name="test",
            success=True,
            links=[],
            final_output=None,
            total_duration=1.0,
            start_time=None,
            end_time=None
        )

        assert result.get_link_output(0) is None
        assert result.get_link_output(-1) is None

    def test_get_link_by_name(self):
        """Test getting link by name"""
        link = ChainLink("coder", name="my_link")
        links = [link]

        result = ChainResult(
            chain_id="123",
            chain_name="test",
            success=True,
            links=links,
            final_output=None,
            total_duration=1.0,
            start_time=None,
            end_time=None
        )

        found = result.get_link_by_name("my_link")
        assert found is link

    def test_get_link_by_name_not_found(self):
        """Test getting nonexistent link by name"""
        result = ChainResult(
            chain_id="123",
            chain_name="test",
            success=True,
            links=[],
            final_output=None,
            total_duration=1.0,
            start_time=None,
            end_time=None
        )

        assert result.get_link_by_name("nonexistent") is None


class TestAgentChainInit:
    """Test AgentChain initialization"""

    def test_init_defaults(self):
        """Test default initialization"""
        chain = AgentChain()

        assert chain.name == "agent_chain"
        assert len(chain.links) == 0
        assert chain.initial_input is None

    def test_init_with_name(self):
        """Test initialization with custom name"""
        chain = AgentChain(name="custom_chain")

        assert chain.name == "custom_chain"

    def test_init_with_initial_input(self):
        """Test initialization with initial input"""
        chain = AgentChain(initial_input="start data")

        assert chain.initial_input == "start data"

    def test_init_unique_ids(self):
        """Test each chain has unique ID"""
        chain1 = AgentChain()
        chain2 = AgentChain()

        assert chain1.chain_id != chain2.chain_id


class TestAgentChainAddLink:
    """Test adding links to chain"""

    def test_add_link(self):
        """Test adding a link"""
        chain = AgentChain()

        result = chain.add_link("coder")

        assert len(chain.links) == 1
        assert chain.links[0].agent_type == "coder"
        assert result is chain  # Fluent interface

    def test_add_link_with_transform(self):
        """Test adding link with transform"""
        chain = AgentChain()
        transform = lambda x: f"transformed: {x}"

        chain.add_link("coder", transform=transform)

        assert chain.links[0].transform is not None

    def test_add_link_with_validation(self):
        """Test adding link with validation"""
        chain = AgentChain()
        validation = lambda x: len(x) > 0

        chain.add_link("coder", validation=validation)

        assert chain.links[0].validation is not None

    def test_add_link_with_name(self):
        """Test adding link with custom name"""
        chain = AgentChain()

        chain.add_link("coder", name="my_coder")

        assert chain.links[0].name == "my_coder"

    def test_add_link_with_timeout(self):
        """Test adding link with custom timeout"""
        chain = AgentChain()

        chain.add_link("coder", timeout=300)

        assert chain.links[0].timeout == 300

    def test_then_alias(self):
        """Test then() method as alias"""
        chain = AgentChain()

        result = chain.then("coder").then("tester")

        assert len(chain.links) == 2
        assert result is chain


class TestAgentChainContext:
    """Test chain context management"""

    def test_set_context(self):
        """Test setting context variable"""
        chain = AgentChain()

        chain.set_context("key", "value")

        assert chain.context["key"] == "value"


@pytest.mark.asyncio
class TestAgentChainExecution:
    """Test chain execution"""

    async def test_execute_empty_chain_raises_error(self):
        """Test executing empty chain raises error"""
        chain = AgentChain()

        async def mock_executor(agent_type, task):
            return "result"

        with pytest.raises(ValueError, match="empty chain"):
            await chain.execute(mock_executor)

    async def test_execute_single_link(self):
        """Test executing chain with single link"""
        chain = AgentChain(initial_input="start")
        chain.add_link("coder")

        async def mock_executor(agent_type, task):
            return "result"

        result = await chain.execute(mock_executor)

        assert result.success
        assert result.final_output == "result"

    async def test_execute_multiple_links(self):
        """Test executing chain with multiple links"""
        chain = AgentChain(initial_input="start")
        chain.add_link("researcher")
        chain.add_link("coder")
        chain.add_link("tester")

        async def mock_executor(agent_type, task):
            return f"output_{agent_type}"

        result = await chain.execute(mock_executor)

        assert result.success
        assert len(result.links) == 3
        assert result.final_output == "output_tester"

    async def test_execute_with_transform(self):
        """Test execution with transform"""
        chain = AgentChain(initial_input="data")
        chain.add_link("coder", transform=lambda x: f"Task: {x}")

        calls = []

        async def mock_executor(agent_type, task):
            calls.append(task)
            return "result"

        await chain.execute(mock_executor)

        assert calls[0] == "Task: data"

    async def test_execute_with_validation_success(self):
        """Test execution with successful validation"""
        chain = AgentChain(initial_input="start")
        chain.add_link("coder", validation=lambda x: x == "result")

        async def mock_executor(agent_type, task):
            return "result"

        result = await chain.execute(mock_executor)

        assert result.success

    async def test_execute_with_validation_failure(self):
        """Test execution with failed validation"""
        chain = AgentChain(initial_input="start")
        chain.add_link("coder", validation=lambda x: x == "expected")

        async def mock_executor(agent_type, task):
            return "unexpected"

        result = await chain.execute(mock_executor, stop_on_error=True)

        assert not result.success

    async def test_execute_timeout(self):
        """Test execution timeout"""
        chain = AgentChain(initial_input="start")
        chain.add_link("coder", timeout=0.1)

        async def slow_executor(agent_type, task):
            await asyncio.sleep(1)
            return "result"

        result = await chain.execute(slow_executor, stop_on_error=True)

        assert not result.success
        assert "timed out" in result.errors[0]

    async def test_execute_exception(self):
        """Test execution with exception"""
        chain = AgentChain(initial_input="start")
        chain.add_link("coder")

        async def failing_executor(agent_type, task):
            raise Exception("Execution failed")

        result = await chain.execute(failing_executor, stop_on_error=True)

        assert not result.success
        assert "failed" in result.errors[0]

    async def test_execute_stop_on_error_true(self):
        """Test stop_on_error=True stops chain"""
        chain = AgentChain(initial_input="start")
        chain.add_link("coder1")
        chain.add_link("coder2")
        chain.add_link("coder3")

        async def failing_executor(agent_type, task):
            if agent_type == "coder1":
                raise Exception("Failed")
            return "result"

        result = await chain.execute(failing_executor, stop_on_error=True)

        assert not result.success
        # Only first link should be attempted
        completed = sum(1 for link in result.links if link.success)
        assert completed == 0

    async def test_execute_stop_on_error_false(self):
        """Test stop_on_error=False continues chain"""
        chain = AgentChain(initial_input="start")
        chain.add_link("coder1")
        chain.add_link("coder2")

        call_count = []

        async def executor(agent_type, task):
            call_count.append(agent_type)
            if agent_type == "coder1":
                raise Exception("Failed")
            return "result"

        result = await chain.execute(executor, stop_on_error=False)

        # Both links should be attempted
        assert len(call_count) == 2

    async def test_execute_with_override_input(self):
        """Test execute with override input"""
        chain = AgentChain(initial_input="original")
        chain.add_link("coder")

        calls = []

        async def mock_executor(agent_type, task):
            calls.append(task)
            return "result"

        await chain.execute(mock_executor, initial_input="override")

        assert "override" in calls[0]

    async def test_execute_stores_context(self):
        """Test execution stores results in context"""
        chain = AgentChain(initial_input="start")
        chain.add_link("coder")
        chain.add_link("tester")

        async def mock_executor(agent_type, task):
            return f"result_{agent_type}"

        result = await chain.execute(mock_executor)

        assert "link_0_output" in chain.context
        assert "link_1_output" in chain.context

    async def test_execute_none_input(self):
        """Test execution with None input"""
        chain = AgentChain()
        chain.add_link("coder")

        async def mock_executor(agent_type, task):
            assert task == ""  # None converted to empty string
            return "result"

        result = await chain.execute(mock_executor, initial_input=None)

        assert result.success


class TestAgentChainVisualization:
    """Test chain visualization"""

    def test_visualize_simple_chain(self):
        """Test visualizing simple chain"""
        chain = AgentChain(name="test_chain")
        chain.add_link("researcher")
        chain.add_link("coder")

        viz = chain.visualize()

        assert "test_chain" in viz
        assert "researcher" in viz
        assert "coder" in viz

    def test_visualize_with_transforms(self):
        """Test visualizing chain with transforms"""
        chain = AgentChain()
        chain.add_link("coder", transform=lambda x: x)

        viz = chain.visualize()

        assert "Transform: yes" in viz

    def test_visualize_with_validation(self):
        """Test visualizing chain with validation"""
        chain = AgentChain()
        chain.add_link("coder", validation=lambda x: True)

        viz = chain.visualize()

        assert "Validation: yes" in viz


class TestAgentChainExecutionSummary:
    """Test execution summary"""

    @pytest.mark.asyncio
    async def test_get_execution_summary(self):
        """Test getting execution summary"""
        chain = AgentChain(name="test_chain")
        chain.add_link("coder")
        chain.add_link("tester")

        async def mock_executor(agent_type, task):
            return "result"

        await chain.execute(mock_executor)

        summary = chain.get_execution_summary()

        assert summary["chain_name"] == "test_chain"
        assert summary["total_links"] == 2
        assert summary["completed"] == 2
        assert summary["failed"] == 0

    @pytest.mark.asyncio
    async def test_get_execution_summary_with_failures(self):
        """Test summary with failures"""
        chain = AgentChain()
        chain.add_link("coder1")
        chain.add_link("coder2")

        async def executor(agent_type, task):
            if agent_type == "coder1":
                raise Exception("Failed")
            return "result"

        await chain.execute(executor, stop_on_error=False)

        summary = chain.get_execution_summary()

        assert summary["failed"] >= 1
