"""Tests for WorkflowOrchestrator"""

import pytest
import asyncio
from src.agents import WorkflowOrchestrator, WorkflowStep


@pytest.fixture
async def mock_executor():
    """Mock agent executor"""
    async def executor(agent_type: str, task: str):
        await asyncio.sleep(0.1)
        return {"agent": agent_type, "task": task, "status": "completed"}
    return executor


@pytest.mark.asyncio
async def test_workflow_creation():
    """Test workflow creation"""
    workflow = WorkflowOrchestrator(name="test_workflow")
    assert workflow.name == "test_workflow"
    assert len(workflow.steps) == 0


@pytest.mark.asyncio
async def test_add_step():
    """Test adding workflow steps"""
    workflow = WorkflowOrchestrator()
    step = WorkflowStep(name="step1", agent_type="coder", task="Test task")
    workflow.add_step(step)
    assert len(workflow.steps) == 1
    assert "step1" in workflow.steps


@pytest.mark.asyncio
async def test_simple_workflow_execution(mock_executor):
    """Test simple workflow execution"""
    workflow = WorkflowOrchestrator()
    workflow.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
    workflow.add_step(WorkflowStep(name="step2", agent_type="tester", task="Task 2", dependencies=["step1"]))

    result = await workflow.execute(mock_executor)

    assert result.status == "completed"
    assert len(result.steps) == 2
    assert result.steps["step1"].status.value == "completed"
    assert result.steps["step2"].status.value == "completed"


@pytest.mark.asyncio
async def test_parallel_execution(mock_executor):
    """Test parallel step execution"""
    workflow = WorkflowOrchestrator(max_concurrent=3)
    workflow.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
    workflow.add_step(WorkflowStep(name="step2", agent_type="coder", task="Task 2"))
    workflow.add_step(WorkflowStep(name="step3", agent_type="coder", task="Task 3"))

    result = await workflow.execute(mock_executor)

    assert result.status == "completed"
    assert len(result.steps) == 3


@pytest.mark.asyncio
async def test_dependency_resolution(mock_executor):
    """Test dependency resolution"""
    workflow = WorkflowOrchestrator()
    workflow.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
    workflow.add_step(WorkflowStep(name="step2", agent_type="coder", task="Task 2", dependencies=["step1"]))
    workflow.add_step(WorkflowStep(name="step3", agent_type="coder", task="Task 3", dependencies=["step2"]))

    result = await workflow.execute(mock_executor)

    assert result.steps["step1"].end_time < result.steps["step2"].start_time
    assert result.steps["step2"].end_time < result.steps["step3"].start_time


@pytest.mark.asyncio
async def test_conditional_execution(mock_executor):
    """Test conditional step execution"""
    workflow = WorkflowOrchestrator()
    workflow.set_context("should_run", False)

    workflow.add_step(WorkflowStep(
        name="step1",
        agent_type="coder",
        task="Task 1",
        condition=lambda ctx: ctx.get("should_run", False)
    ))

    result = await workflow.execute(mock_executor)

    assert result.steps["step1"].status.value == "skipped"


@pytest.mark.asyncio
async def test_circular_dependency_detection():
    """Test circular dependency detection"""
    workflow = WorkflowOrchestrator()
    workflow.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1", dependencies=["step2"]))
    workflow.add_step(WorkflowStep(name="step2", agent_type="coder", task="Task 2", dependencies=["step1"]))

    with pytest.raises(ValueError, match="Circular dependency"):
        await workflow.execute(lambda x, y: None)


@pytest.mark.asyncio
async def test_workflow_visualization():
    """Test workflow visualization"""
    workflow = WorkflowOrchestrator(name="test")
    workflow.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
    workflow.add_step(WorkflowStep(name="step2", agent_type="coder", task="Task 2", dependencies=["step1"]))

    viz = workflow.visualize()

    assert "test" in viz
    assert "step1" in viz
    assert "step2" in viz
