"""Tests for AgentChain"""

import pytest
import asyncio
from src.agents import AgentChain


@pytest.fixture
async def mock_executor():
    """Mock agent executor"""
    async def executor(agent_type: str, task: str):
        await asyncio.sleep(0.1)
        return f"Result from {agent_type}: {task}"
    return executor


@pytest.mark.asyncio
async def test_chain_creation():
    """Test chain creation"""
    chain = AgentChain(name="test_chain", initial_input="Start")
    assert chain.name == "test_chain"
    assert chain.initial_input == "Start"
    assert len(chain.links) == 0


@pytest.mark.asyncio
async def test_add_link():
    """Test adding links"""
    chain = AgentChain()
    chain.add_link("coder", name="code_link")
    assert len(chain.links) == 1
    assert chain.links[0].agent_type == "coder"


@pytest.mark.asyncio
async def test_fluent_interface():
    """Test fluent interface"""
    chain = AgentChain().then("researcher").then("coder").then("tester")
    assert len(chain.links) == 3
    assert chain.links[0].agent_type == "researcher"
    assert chain.links[1].agent_type == "coder"
    assert chain.links[2].agent_type == "tester"


@pytest.mark.asyncio
async def test_chain_execution(mock_executor):
    """Test chain execution"""
    chain = AgentChain(initial_input="Start task")
    chain.then("researcher").then("coder").then("tester")

    result = await chain.execute(mock_executor)

    assert result.success is True
    assert len(result.links) == 3
    assert all(link.success for link in result.links)


@pytest.mark.asyncio
async def test_transform_function(mock_executor):
    """Test transform function"""
    chain = AgentChain(initial_input="test")
    chain.then("coder", transform=lambda x: f"Transform: {x}")

    result = await chain.execute(mock_executor)

    assert result.success is True
    assert "Transform: test" in str(result.links[0].input_data)


@pytest.mark.asyncio
async def test_validation_function(mock_executor):
    """Test validation function"""
    chain = AgentChain(initial_input="test")
    chain.then("coder", validation=lambda x: len(str(x)) > 10)

    result = await chain.execute(mock_executor, stop_on_error=True)

    assert result.success is True


@pytest.mark.asyncio
async def test_chain_visualization():
    """Test chain visualization"""
    chain = AgentChain(name="test")
    chain.then("researcher").then("coder")

    viz = chain.visualize()

    assert "test" in viz
    assert "researcher" in viz
    assert "coder" in viz
