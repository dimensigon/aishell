"""
Comprehensive test suite for WorkflowOrchestrator
Target: Increase coverage from 45% to 80%
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from src.agents.workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowStep,
    WorkflowResult,
    StepStatus
)


class TestWorkflowStep:
    """Test WorkflowStep dataclass"""

    def test_workflow_step_creation(self):
        """Test creating a workflow step"""
        step = WorkflowStep(
            name="test_step",
            agent_type="coder",
            task="Write unit tests"
        )

        assert step.name == "test_step"
        assert step.agent_type == "coder"
        assert step.task == "Write unit tests"
        assert step.dependencies == []
        assert step.condition is None
        assert step.retry_count == 3
        assert step.timeout == 300
        assert step.status == StepStatus.PENDING

    def test_workflow_step_with_dependencies(self):
        """Test step with dependencies"""
        step = WorkflowStep(
            name="deploy",
            agent_type="devops",
            task="Deploy application",
            dependencies=["build", "test"]
        )

        assert step.dependencies == ["build", "test"]

    def test_workflow_step_with_condition(self):
        """Test step with conditional execution"""
        condition_fn = lambda ctx: ctx.get("environment") == "production"

        step = WorkflowStep(
            name="validate",
            agent_type="tester",
            task="Run validation",
            condition=condition_fn
        )

        assert step.condition is not None
        assert step.condition({"environment": "production"}) is True
        assert step.condition({"environment": "staging"}) is False

    def test_workflow_step_custom_retry(self):
        """Test step with custom retry count"""
        step = WorkflowStep(
            name="flaky_step",
            agent_type="coder",
            task="Run flaky operation",
            retry_count=5,
            timeout=600
        )

        assert step.retry_count == 5
        assert step.timeout == 600

    def test_workflow_step_auto_id_generation(self):
        """Test automatic step ID generation"""
        step1 = WorkflowStep(name="step1", agent_type="coder", task="Task 1")
        step2 = WorkflowStep(name="step2", agent_type="coder", task="Task 2")

        assert step1.step_id is not None
        assert step2.step_id is not None
        assert step1.step_id != step2.step_id


class TestWorkflowResult:
    """Test WorkflowResult dataclass"""

    def test_workflow_result_creation(self):
        """Test creating workflow result"""
        start_time = datetime.now()
        end_time = datetime.now()

        result = WorkflowResult(
            workflow_id="test-workflow-123",
            status="completed",
            steps={},
            outputs={},
            start_time=start_time,
            end_time=end_time,
            duration=10.5
        )

        assert result.workflow_id == "test-workflow-123"
        assert result.status == "completed"
        assert result.duration == 10.5

    def test_workflow_result_is_successful(self):
        """Test successful workflow detection"""
        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            errors=[]
        )

        assert result.is_successful() is True

    def test_workflow_result_is_not_successful_with_errors(self):
        """Test unsuccessful workflow with errors"""
        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            errors=["Error 1", "Error 2"]
        )

        assert result.is_successful() is False

    def test_workflow_result_get_step_result(self):
        """Test getting specific step result"""
        step = WorkflowStep(name="test_step", agent_type="coder", task="Task")
        step.result = {"output": "test result"}

        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            steps={"test_step": step},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0
        )

        step_result = result.get_step_result("test_step")
        assert step_result == {"output": "test result"}

    def test_workflow_result_get_nonexistent_step(self):
        """Test getting result for non-existent step"""
        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0
        )

        step_result = result.get_step_result("nonexistent")
        assert step_result is None


class TestWorkflowOrchestratorInitialization:
    """Test workflow orchestrator initialization"""

    def test_orchestrator_creation(self):
        """Test creating an orchestrator"""
        orchestrator = WorkflowOrchestrator("test_workflow")

        assert orchestrator.name == "test_workflow"
        assert orchestrator.workflow_id is not None
        assert orchestrator.max_concurrent == 5
        assert isinstance(orchestrator.steps, dict)
        assert isinstance(orchestrator.context, dict)

    def test_orchestrator_custom_concurrent_limit(self):
        """Test orchestrator with custom concurrency limit"""
        orchestrator = WorkflowOrchestrator("test", max_concurrent=10)

        assert orchestrator.max_concurrent == 10

    def test_orchestrator_unique_ids(self):
        """Test that each orchestrator gets unique ID"""
        orch1 = WorkflowOrchestrator("workflow1")
        orch2 = WorkflowOrchestrator("workflow2")

        assert orch1.workflow_id != orch2.workflow_id


class TestWorkflowOrchestratorStepManagement:
    """Test step management operations"""

    def test_add_step(self):
        """Test adding a step"""
        orchestrator = WorkflowOrchestrator("test")
        step = WorkflowStep(name="step1", agent_type="coder", task="Task 1")

        result = orchestrator.add_step(step)

        assert result == orchestrator  # Fluent interface
        assert "step1" in orchestrator.steps
        assert orchestrator.steps["step1"] == step

    def test_add_duplicate_step_raises_error(self):
        """Test that adding duplicate step raises error"""
        orchestrator = WorkflowOrchestrator("test")
        step1 = WorkflowStep(name="step1", agent_type="coder", task="Task 1")
        step2 = WorkflowStep(name="step1", agent_type="tester", task="Task 2")

        orchestrator.add_step(step1)

        with pytest.raises(ValueError, match="already exists"):
            orchestrator.add_step(step2)

    def test_add_multiple_steps(self):
        """Test adding multiple steps"""
        orchestrator = WorkflowOrchestrator("test")
        steps = [
            WorkflowStep(name="step1", agent_type="coder", task="Task 1"),
            WorkflowStep(name="step2", agent_type="tester", task="Task 2"),
            WorkflowStep(name="step3", agent_type="reviewer", task="Task 3")
        ]

        result = orchestrator.add_steps(steps)

        assert result == orchestrator
        assert len(orchestrator.steps) == 3

    def test_set_context(self):
        """Test setting context variables"""
        orchestrator = WorkflowOrchestrator("test")

        orchestrator.set_context("environment", "production")
        orchestrator.set_context("version", "1.0.0")

        assert orchestrator.context["environment"] == "production"
        assert orchestrator.context["version"] == "1.0.0"


class TestWorkflowOrchestratorValidation:
    """Test workflow validation"""

    def test_validate_workflow_success(self):
        """Test successful workflow validation"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
        orchestrator.add_step(WorkflowStep(
            name="step2",
            agent_type="tester",
            task="Task 2",
            dependencies=["step1"]
        ))

        # Should not raise error
        orchestrator._validate_workflow()

    def test_validate_workflow_missing_dependency(self):
        """Test validation with missing dependency"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(
            name="step1",
            agent_type="coder",
            task="Task 1",
            dependencies=["nonexistent"]
        ))

        with pytest.raises(ValueError, match="depends on non-existent"):
            orchestrator._validate_workflow()

    def test_validate_workflow_circular_dependency(self):
        """Test validation with circular dependency"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(
            name="step1",
            agent_type="coder",
            task="Task 1",
            dependencies=["step2"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="step2",
            agent_type="tester",
            task="Task 2",
            dependencies=["step1"]
        ))

        with pytest.raises(ValueError, match="Circular dependency"):
            orchestrator._validate_workflow()

    def test_validate_workflow_complex_circular_dependency(self):
        """Test validation with complex circular dependency"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(
            name="step1",
            agent_type="coder",
            task="Task 1",
            dependencies=["step3"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="step2",
            agent_type="tester",
            task="Task 2",
            dependencies=["step1"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="step3",
            agent_type="reviewer",
            task="Task 3",
            dependencies=["step2"]
        ))

        with pytest.raises(ValueError, match="Circular dependency"):
            orchestrator._validate_workflow()


class TestWorkflowOrchestratorExecutionOrder:
    """Test execution order calculation"""

    def test_calculate_execution_order_linear(self):
        """Test execution order for linear workflow"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
        orchestrator.add_step(WorkflowStep(
            name="step2",
            agent_type="tester",
            task="Task 2",
            dependencies=["step1"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="step3",
            agent_type="reviewer",
            task="Task 3",
            dependencies=["step2"]
        ))

        levels = orchestrator._calculate_execution_order()

        assert len(levels) == 3
        assert levels[0] == ["step1"]
        assert levels[1] == ["step2"]
        assert levels[2] == ["step3"]

    def test_calculate_execution_order_parallel(self):
        """Test execution order for parallel workflow"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
        orchestrator.add_step(WorkflowStep(name="step2", agent_type="tester", task="Task 2"))
        orchestrator.add_step(WorkflowStep(name="step3", agent_type="reviewer", task="Task 3"))

        levels = orchestrator._calculate_execution_order()

        assert len(levels) == 1
        assert set(levels[0]) == {"step1", "step2", "step3"}

    def test_calculate_execution_order_mixed(self):
        """Test execution order for mixed workflow"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(name="build", agent_type="coder", task="Build"))
        orchestrator.add_step(WorkflowStep(
            name="test_unit",
            agent_type="tester",
            task="Unit tests",
            dependencies=["build"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="test_integration",
            agent_type="tester",
            task="Integration tests",
            dependencies=["build"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="deploy",
            agent_type="devops",
            task="Deploy",
            dependencies=["test_unit", "test_integration"]
        ))

        levels = orchestrator._calculate_execution_order()

        assert len(levels) == 3
        assert levels[0] == ["build"]
        assert set(levels[1]) == {"test_unit", "test_integration"}
        assert levels[2] == ["deploy"]


class TestWorkflowOrchestratorExecution:
    """Test workflow execution"""

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self):
        """Test executing a simple workflow"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))

        async def mock_executor(agent_type, task):
            return f"Result from {agent_type}: {task}"

        result = await orchestrator.execute(mock_executor)

        assert result.status == "completed"
        assert orchestrator.steps["step1"].status == StepStatus.COMPLETED
        assert orchestrator.steps["step1"].result is not None

    @pytest.mark.asyncio
    async def test_execute_workflow_with_dependencies(self):
        """Test executing workflow with dependencies"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
        orchestrator.add_step(WorkflowStep(
            name="step2",
            agent_type="tester",
            task="Task 2",
            dependencies=["step1"]
        ))

        async def mock_executor(agent_type, task):
            await asyncio.sleep(0.01)
            return f"Result: {task}"

        result = await orchestrator.execute(mock_executor)

        assert result.status == "completed"
        assert orchestrator.steps["step1"].status == StepStatus.COMPLETED
        assert orchestrator.steps["step2"].status == StepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_parallel_steps(self):
        """Test executing parallel steps"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
        orchestrator.add_step(WorkflowStep(name="step2", agent_type="tester", task="Task 2"))
        orchestrator.add_step(WorkflowStep(name="step3", agent_type="reviewer", task="Task 3"))

        execution_times = []

        async def mock_executor(agent_type, task):
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.1)
            execution_times.append((agent_type, start))
            return f"Result: {task}"

        result = await orchestrator.execute(mock_executor)

        assert result.status == "completed"
        # All three steps should have started around the same time (parallel execution)
        assert len(execution_times) == 3

    @pytest.mark.asyncio
    async def test_execute_with_conditional_step(self):
        """Test executing workflow with conditional step"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
        orchestrator.add_step(WorkflowStep(
            name="step2",
            agent_type="tester",
            task="Task 2",
            condition=lambda ctx: ctx.get("skip") is not True
        ))

        orchestrator.set_context("skip", True)

        async def mock_executor(agent_type, task):
            return f"Result: {task}"

        result = await orchestrator.execute(mock_executor)

        assert result.status == "partial"  # Not all steps completed
        assert orchestrator.steps["step1"].status == StepStatus.COMPLETED
        assert orchestrator.steps["step2"].status == StepStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_execute_with_retry(self):
        """Test step execution with retry logic"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(
            name="flaky_step",
            agent_type="coder",
            task="Flaky task",
            retry_count=3
        ))

        attempt_count = 0

        async def flaky_executor(agent_type, task):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("Temporary failure")
            return "Success"

        result = await orchestrator.execute(flaky_executor)

        assert result.status == "completed"
        assert attempt_count == 2  # Failed once, succeeded on second attempt
        assert orchestrator.steps["flaky_step"].attempts == 2

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self):
        """Test step execution with timeout"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(
            name="slow_step",
            agent_type="coder",
            task="Slow task",
            timeout=0.1,
            retry_count=1
        ))

        async def slow_executor(agent_type, task):
            await asyncio.sleep(1.0)  # Takes longer than timeout
            return "Result"

        result = await orchestrator.execute(flaky_executor)

        assert result.status == "failed"
        assert orchestrator.steps["slow_step"].status == StepStatus.FAILED
        assert "timed out" in orchestrator.steps["slow_step"].error

    @pytest.mark.asyncio
    async def test_execute_fail_fast(self):
        """Test fail-fast execution"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
        orchestrator.add_step(WorkflowStep(name="step2", agent_type="tester", task="Task 2"))

        async def failing_executor(agent_type, task):
            if agent_type == "coder":
                raise Exception("Failure")
            return "Success"

        result = await orchestrator.execute(failing_executor, fail_fast=True)

        assert result.status == "failed"
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_execute_stores_results_in_context(self):
        """Test that step results are stored in context"""
        orchestrator = WorkflowOrchestrator("test")
        orchestrator.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))

        async def mock_executor(agent_type, task):
            return {"output": "test output"}

        result = await orchestrator.execute(mock_executor)

        assert "step_step1_result" in orchestrator.context
        assert orchestrator.context["step_step1_result"] == {"output": "test output"}

    @pytest.mark.asyncio
    async def test_execute_max_concurrent_limit(self):
        """Test that max_concurrent limit is enforced"""
        orchestrator = WorkflowOrchestrator("test", max_concurrent=2)

        # Add 5 parallel steps
        for i in range(5):
            orchestrator.add_step(WorkflowStep(
                name=f"step{i}",
                agent_type="coder",
                task=f"Task {i}"
            ))

        concurrent_count = 0
        max_concurrent_observed = 0

        async def mock_executor(agent_type, task):
            nonlocal concurrent_count, max_concurrent_observed
            concurrent_count += 1
            max_concurrent_observed = max(max_concurrent_observed, concurrent_count)
            await asyncio.sleep(0.1)
            concurrent_count -= 1
            return "Result"

        result = await orchestrator.execute(mock_executor)

        assert result.status == "completed"
        assert max_concurrent_observed <= 2


class TestWorkflowOrchestratorVisualization:
    """Test workflow visualization"""

    def test_visualize_simple_workflow(self):
        """Test visualizing a simple workflow"""
        orchestrator = WorkflowOrchestrator("test_workflow")
        orchestrator.add_step(WorkflowStep(name="step1", agent_type="coder", task="Task 1"))
        orchestrator.add_step(WorkflowStep(
            name="step2",
            agent_type="tester",
            task="Task 2",
            dependencies=["step1"]
        ))

        visualization = orchestrator.visualize()

        assert "test_workflow" in visualization
        assert "step1" in visualization
        assert "step2" in visualization
        assert "coder" in visualization
        assert "tester" in visualization

    def test_visualize_complex_workflow(self):
        """Test visualizing a complex workflow"""
        orchestrator = WorkflowOrchestrator("complex_workflow")
        orchestrator.add_step(WorkflowStep(name="build", agent_type="coder", task="Build"))
        orchestrator.add_step(WorkflowStep(
            name="test",
            agent_type="tester",
            task="Test",
            dependencies=["build"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="deploy",
            agent_type="devops",
            task="Deploy",
            dependencies=["test"],
            condition=lambda ctx: True
        ))

        visualization = orchestrator.visualize()

        assert "Level 1" in visualization
        assert "Level 2" in visualization
        assert "Level 3" in visualization
        assert "Conditional: yes" in visualization


class TestWorkflowOrchestratorIntegration:
    """Test integration scenarios"""

    @pytest.mark.asyncio
    async def test_complete_cicd_workflow(self):
        """Test complete CI/CD workflow"""
        orchestrator = WorkflowOrchestrator("cicd_pipeline")

        # Add steps
        orchestrator.add_step(WorkflowStep(name="checkout", agent_type="devops", task="Checkout code"))
        orchestrator.add_step(WorkflowStep(
            name="build",
            agent_type="coder",
            task="Build application",
            dependencies=["checkout"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="unit_tests",
            agent_type="tester",
            task="Run unit tests",
            dependencies=["build"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="integration_tests",
            agent_type="tester",
            task="Run integration tests",
            dependencies=["build"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="deploy",
            agent_type="devops",
            task="Deploy to production",
            dependencies=["unit_tests", "integration_tests"]
        ))

        async def mock_executor(agent_type, task):
            await asyncio.sleep(0.01)
            return f"Completed: {task}"

        result = await orchestrator.execute(mock_executor)

        assert result.status == "completed"
        assert len(result.steps) == 5
        assert all(step.status == StepStatus.COMPLETED for step in result.steps.values())

    @pytest.mark.asyncio
    async def test_data_pipeline_workflow(self):
        """Test data processing pipeline"""
        orchestrator = WorkflowOrchestrator("data_pipeline")

        orchestrator.add_step(WorkflowStep(name="extract", agent_type="data", task="Extract data"))
        orchestrator.add_step(WorkflowStep(
            name="transform",
            agent_type="data",
            task="Transform data",
            dependencies=["extract"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="validate",
            agent_type="data",
            task="Validate data",
            dependencies=["transform"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="load",
            agent_type="data",
            task="Load data",
            dependencies=["validate"]
        ))

        async def mock_executor(agent_type, task):
            return {"status": "success", "task": task}

        result = await orchestrator.execute(mock_executor)

        assert result.status == "completed"
        assert result.duration > 0
