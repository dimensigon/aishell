"""
Comprehensive tests for src/agents/workflow_orchestrator.py to achieve 90%+ coverage.

Tests workflow creation, step dependencies, execution order, error handling,
retry logic, timeouts, conditional execution, and result aggregation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.agents.workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowStep,
    WorkflowResult,
    StepStatus
)


class TestWorkflowStep:
    """Test WorkflowStep dataclass"""

    def test_step_creation_minimal(self):
        """Test creating step with minimal args"""
        step = WorkflowStep(
            name="test_step",
            agent_type="coder",
            task="Implement feature"
        )

        assert step.name == "test_step"
        assert step.agent_type == "coder"
        assert step.task == "Implement feature"
        assert step.status == StepStatus.PENDING
        assert step.dependencies == []

    def test_step_with_dependencies(self):
        """Test step with dependencies"""
        step = WorkflowStep(
            name="test_step",
            agent_type="coder",
            task="Task",
            dependencies=["step1", "step2"]
        )

        assert len(step.dependencies) == 2

    def test_step_with_condition(self):
        """Test step with condition"""
        condition = lambda ctx: ctx.get('enabled', False)
        step = WorkflowStep(
            name="test_step",
            agent_type="coder",
            task="Task",
            condition=condition
        )

        assert step.condition is not None

    def test_step_custom_retry_count(self):
        """Test step with custom retry count"""
        step = WorkflowStep(
            name="test_step",
            agent_type="coder",
            task="Task",
            retry_count=5
        )

        assert step.retry_count == 5

    def test_step_custom_timeout(self):
        """Test step with custom timeout"""
        step = WorkflowStep(
            name="test_step",
            agent_type="coder",
            task="Task",
            timeout=600
        )

        assert step.timeout == 600

    def test_step_metadata(self):
        """Test step with metadata"""
        step = WorkflowStep(
            name="test_step",
            agent_type="coder",
            task="Task",
            metadata={'key': 'value'}
        )

        assert step.metadata['key'] == 'value'

    def test_step_has_unique_id(self):
        """Test each step has unique ID"""
        step1 = WorkflowStep("step1", "coder", "task")
        step2 = WorkflowStep("step2", "coder", "task")

        assert step1.step_id != step2.step_id


class TestWorkflowResult:
    """Test WorkflowResult dataclass"""

    def test_is_successful_completed(self):
        """Test successful workflow detection"""
        result = WorkflowResult(
            workflow_id="123",
            status="completed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            errors=[]
        )

        assert result.is_successful()

    def test_is_successful_with_errors(self):
        """Test workflow with errors not successful"""
        result = WorkflowResult(
            workflow_id="123",
            status="completed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            errors=["Error 1"]
        )

        assert not result.is_successful()

    def test_is_successful_failed_status(self):
        """Test failed workflow not successful"""
        result = WorkflowResult(
            workflow_id="123",
            status="failed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            errors=[]
        )

        assert not result.is_successful()

    def test_get_step_result(self):
        """Test getting step result"""
        step = WorkflowStep("step1", "coder", "task")
        step.result = {"output": "data"}

        result = WorkflowResult(
            workflow_id="123",
            status="completed",
            steps={"step1": step},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0
        )

        assert result.get_step_result("step1") == {"output": "data"}

    def test_get_step_result_nonexistent(self):
        """Test getting result for nonexistent step"""
        result = WorkflowResult(
            workflow_id="123",
            status="completed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0
        )

        assert result.get_step_result("nonexistent") is None


class TestWorkflowOrchestratorInit:
    """Test WorkflowOrchestrator initialization"""

    def test_init_defaults(self):
        """Test default initialization"""
        orchestrator = WorkflowOrchestrator()

        assert orchestrator.name == "workflow"
        assert orchestrator.max_concurrent == 5
        assert len(orchestrator.steps) == 0

    def test_init_custom_name(self):
        """Test initialization with custom name"""
        orchestrator = WorkflowOrchestrator(name="custom_workflow")

        assert orchestrator.name == "custom_workflow"

    def test_init_custom_max_concurrent(self):
        """Test initialization with custom max concurrent"""
        orchestrator = WorkflowOrchestrator(max_concurrent=10)

        assert orchestrator.max_concurrent == 10

    def test_init_has_workflow_id(self):
        """Test workflow has unique ID"""
        orch1 = WorkflowOrchestrator()
        orch2 = WorkflowOrchestrator()

        assert orch1.workflow_id != orch2.workflow_id


class TestWorkflowOrchestratorAddStep:
    """Test adding steps to workflow"""

    def test_add_step(self):
        """Test adding a single step"""
        orchestrator = WorkflowOrchestrator()
        step = WorkflowStep("step1", "coder", "task")

        result = orchestrator.add_step(step)

        assert "step1" in orchestrator.steps
        assert result is orchestrator  # Fluent interface

    def test_add_multiple_steps(self):
        """Test adding multiple steps"""
        orchestrator = WorkflowOrchestrator()
        steps = [
            WorkflowStep("step1", "coder", "task1"),
            WorkflowStep("step2", "tester", "task2")
        ]

        orchestrator.add_steps(steps)

        assert len(orchestrator.steps) == 2

    def test_add_duplicate_step_raises_error(self):
        """Test adding duplicate step name raises error"""
        orchestrator = WorkflowOrchestrator()
        step1 = WorkflowStep("step1", "coder", "task")
        step2 = WorkflowStep("step1", "tester", "task")

        orchestrator.add_step(step1)

        with pytest.raises(ValueError, match="already exists"):
            orchestrator.add_step(step2)


class TestWorkflowOrchestratorContext:
    """Test workflow context management"""

    def test_set_context(self):
        """Test setting context variable"""
        orchestrator = WorkflowOrchestrator()

        orchestrator.set_context("key", "value")

        assert orchestrator.context["key"] == "value"

    def test_set_multiple_context_vars(self):
        """Test setting multiple context variables"""
        orchestrator = WorkflowOrchestrator()

        orchestrator.set_context("key1", "value1")
        orchestrator.set_context("key2", "value2")

        assert len(orchestrator.context) == 2


class TestWorkflowValidation:
    """Test workflow validation"""

    def test_validate_workflow_missing_dependency(self):
        """Test validation fails for missing dependency"""
        orchestrator = WorkflowOrchestrator()
        step = WorkflowStep("step1", "coder", "task", dependencies=["nonexistent"])
        orchestrator.add_step(step)

        with pytest.raises(ValueError, match="non-existent"):
            orchestrator._validate_workflow()

    def test_validate_workflow_circular_dependency(self):
        """Test validation fails for circular dependency"""
        orchestrator = WorkflowOrchestrator()
        step1 = WorkflowStep("step1", "coder", "task", dependencies=["step2"])
        step2 = WorkflowStep("step2", "coder", "task", dependencies=["step1"])
        orchestrator.add_step(step1)
        orchestrator.add_step(step2)

        with pytest.raises(ValueError, match="Circular dependency"):
            orchestrator._validate_workflow()

    def test_validate_workflow_valid(self):
        """Test validation passes for valid workflow"""
        orchestrator = WorkflowOrchestrator()
        step1 = WorkflowStep("step1", "coder", "task")
        step2 = WorkflowStep("step2", "tester", "task", dependencies=["step1"])
        orchestrator.add_step(step1)
        orchestrator.add_step(step2)

        orchestrator._validate_workflow()  # Should not raise


class TestExecutionOrder:
    """Test execution order calculation"""

    def test_calculate_execution_order_no_dependencies(self):
        """Test execution order with no dependencies"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "coder", "task"))
        orchestrator.add_step(WorkflowStep("step2", "coder", "task"))

        levels = orchestrator._calculate_execution_order()

        assert len(levels) == 1
        assert len(levels[0]) == 2

    def test_calculate_execution_order_linear(self):
        """Test execution order with linear dependencies"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "coder", "task"))
        orchestrator.add_step(WorkflowStep("step2", "coder", "task", dependencies=["step1"]))
        orchestrator.add_step(WorkflowStep("step3", "coder", "task", dependencies=["step2"]))

        levels = orchestrator._calculate_execution_order()

        assert len(levels) == 3

    def test_calculate_execution_order_parallel(self):
        """Test execution order with parallel branches"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "coder", "task"))
        orchestrator.add_step(WorkflowStep("step2", "coder", "task", dependencies=["step1"]))
        orchestrator.add_step(WorkflowStep("step3", "coder", "task", dependencies=["step1"]))
        orchestrator.add_step(WorkflowStep("step4", "coder", "task", dependencies=["step2", "step3"]))

        levels = orchestrator._calculate_execution_order()

        assert "step2" in levels[1] and "step3" in levels[1]  # Parallel


@pytest.mark.asyncio
class TestWorkflowExecution:
    """Test workflow execution"""

    async def test_execute_single_step(self):
        """Test executing workflow with single step"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "coder", "task"))

        async def mock_executor(agent_type, task):
            return "result"

        result = await orchestrator.execute(mock_executor)

        assert result.status == "completed"
        assert result.outputs.get("step_step1_result") == "result"

    async def test_execute_multiple_steps(self):
        """Test executing multiple steps"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "coder", "task1"))
        orchestrator.add_step(WorkflowStep("step2", "tester", "task2", dependencies=["step1"]))

        async def mock_executor(agent_type, task):
            return f"result_{agent_type}"

        result = await orchestrator.execute(mock_executor)

        assert result.status == "completed"
        assert len(result.outputs) == 2

    async def test_execute_with_retry(self):
        """Test step retry on failure"""
        orchestrator = WorkflowOrchestrator()
        step = WorkflowStep("step1", "coder", "task", retry_count=3)
        orchestrator.add_step(step)

        attempts = []

        async def failing_executor(agent_type, task):
            attempts.append(1)
            if len(attempts) < 3:
                raise Exception("Fail")
            return "success"

        result = await orchestrator.execute(failing_executor)

        assert len(attempts) == 3
        assert result.status == "completed"

    async def test_execute_timeout(self):
        """Test step timeout"""
        orchestrator = WorkflowOrchestrator()
        step = WorkflowStep("step1", "coder", "task", timeout=0.1, retry_count=1)
        orchestrator.add_step(step)

        async def slow_executor(agent_type, task):
            await asyncio.sleep(1)
            return "result"

        result = await orchestrator.execute(slow_executor)

        assert result.status == "failed"
        assert orchestrator.steps["step1"].status == StepStatus.FAILED

    async def test_execute_fail_fast(self):
        """Test fail fast mode"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "coder", "task", retry_count=1))
        orchestrator.add_step(WorkflowStep("step2", "coder", "task", retry_count=1))

        async def failing_executor(agent_type, task):
            raise Exception("Failed")

        result = await orchestrator.execute(failing_executor, fail_fast=True)

        assert result.status == "failed"

    async def test_execute_conditional_step_met(self):
        """Test conditional step when condition is met"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.set_context("run_step", True)
        
        step = WorkflowStep(
            "step1",
            "coder",
            "task",
            condition=lambda ctx: ctx.get("run_step", False)
        )
        orchestrator.add_step(step)

        async def mock_executor(agent_type, task):
            return "result"

        result = await orchestrator.execute(mock_executor)

        assert orchestrator.steps["step1"].status == StepStatus.COMPLETED

    async def test_execute_conditional_step_not_met(self):
        """Test conditional step when condition not met"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.set_context("run_step", False)
        
        step = WorkflowStep(
            "step1",
            "coder",
            "task",
            condition=lambda ctx: ctx.get("run_step", False)
        )
        orchestrator.add_step(step)

        async def mock_executor(agent_type, task):
            return "result"

        result = await orchestrator.execute(mock_executor)

        assert orchestrator.steps["step1"].status == StepStatus.SKIPPED

    async def test_execute_parallel_steps(self):
        """Test parallel step execution"""
        orchestrator = WorkflowOrchestrator(max_concurrent=3)
        orchestrator.add_step(WorkflowStep("step1", "coder", "task1"))
        orchestrator.add_step(WorkflowStep("step2", "coder", "task2"))
        orchestrator.add_step(WorkflowStep("step3", "coder", "task3"))

        execution_times = []

        async def mock_executor(agent_type, task):
            execution_times.append(datetime.now())
            await asyncio.sleep(0.1)
            return "result"

        result = await orchestrator.execute(mock_executor)

        assert result.status == "completed"
        # All should start around same time (parallel)
        time_diff = (execution_times[-1] - execution_times[0]).total_seconds()
        assert time_diff < 0.5


class TestWorkflowVisualization:
    """Test workflow visualization"""

    def test_visualize_simple_workflow(self):
        """Test visualizing simple workflow"""
        orchestrator = WorkflowOrchestrator(name="test_workflow")
        orchestrator.add_step(WorkflowStep("step1", "coder", "task"))

        viz = orchestrator.visualize()

        assert "test_workflow" in viz
        assert "step1" in viz

    def test_visualize_with_dependencies(self):
        """Test visualizing workflow with dependencies"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "coder", "task"))
        orchestrator.add_step(WorkflowStep("step2", "coder", "task", dependencies=["step1"]))

        viz = orchestrator.visualize()

        assert "step1" in viz
        assert "step2" in viz
        assert "Dependencies" in viz

    def test_visualize_with_conditions(self):
        """Test visualizing workflow with conditional steps"""
        orchestrator = WorkflowOrchestrator()
        step = WorkflowStep("step1", "coder", "task", condition=lambda ctx: True)
        orchestrator.add_step(step)

        viz = orchestrator.visualize()

        assert "Conditional" in viz
