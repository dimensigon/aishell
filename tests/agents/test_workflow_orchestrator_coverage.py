"""
Comprehensive coverage tests for WorkflowOrchestrator
Targeting uncovered branches, error paths, and edge cases
"""

import pytest
import asyncio
from datetime import datetime
from src.agents.workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowStep,
    WorkflowResult,
    StepStatus,
)


class TestWorkflowStepEdgeCases:
    """Test WorkflowStep edge cases and error paths"""

    def test_step_with_empty_dependencies(self):
        """Test step with empty dependency list"""
        step = WorkflowStep(
            name="test",
            agent_type="coder",
            task="test task",
            dependencies=[]
        )
        assert step.dependencies == []
        assert step.status == StepStatus.PENDING

    def test_step_with_zero_retry_count(self):
        """Test step with zero retry count"""
        step = WorkflowStep(
            name="test",
            agent_type="coder",
            task="test task",
            retry_count=0
        )
        assert step.retry_count == 0

    def test_step_with_zero_timeout(self):
        """Test step with zero timeout"""
        step = WorkflowStep(
            name="test",
            agent_type="coder",
            task="test task",
            timeout=0
        )
        assert step.timeout == 0

    def test_step_with_very_long_task_description(self):
        """Test step with very long task description"""
        long_task = "x" * 10000
        step = WorkflowStep(
            name="test",
            agent_type="coder",
            task=long_task
        )
        assert len(step.task) == 10000

    def test_step_with_complex_metadata(self):
        """Test step with complex nested metadata"""
        metadata = {
            "nested": {"level1": {"level2": {"level3": "value"}}},
            "list": [1, 2, 3],
            "mixed": {"a": [1, 2], "b": {"c": 3}}
        }
        step = WorkflowStep(
            name="test",
            agent_type="coder",
            task="test",
            metadata=metadata
        )
        assert step.metadata == metadata

    def test_step_status_transitions(self):
        """Test all possible status transitions"""
        step = WorkflowStep(name="test", agent_type="coder", task="test")

        assert step.status == StepStatus.PENDING

        step.status = StepStatus.RUNNING
        assert step.status == StepStatus.RUNNING

        step.status = StepStatus.COMPLETED
        assert step.status == StepStatus.COMPLETED

        step.status = StepStatus.FAILED
        assert step.status == StepStatus.FAILED

        step.status = StepStatus.SKIPPED
        assert step.status == StepStatus.SKIPPED

        step.status = StepStatus.CANCELLED
        assert step.status == StepStatus.CANCELLED

    def test_step_with_none_condition(self):
        """Test step with None condition explicitly set"""
        step = WorkflowStep(
            name="test",
            agent_type="coder",
            task="test",
            condition=None
        )
        assert step.condition is None

    def test_step_auto_generated_id_uniqueness(self):
        """Test that auto-generated step IDs are unique"""
        steps = [
            WorkflowStep(name=f"test{i}", agent_type="coder", task="test")
            for i in range(100)
        ]
        step_ids = [s.step_id for s in steps]
        assert len(set(step_ids)) == 100

    def test_step_with_negative_retry_count(self):
        """Test step with negative retry count"""
        step = WorkflowStep(
            name="test",
            agent_type="coder",
            task="test",
            retry_count=-1
        )
        assert step.retry_count == -1


class TestWorkflowResultEdgeCases:
    """Test WorkflowResult edge cases"""

    def test_result_with_empty_steps(self):
        """Test result with no steps"""
        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0
        )
        assert result.is_successful()

    def test_result_with_empty_errors_list(self):
        """Test result with explicitly empty errors"""
        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0,
            errors=[]
        )
        assert result.is_successful()

    def test_result_with_single_error(self):
        """Test result with one error"""
        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0,
            errors=["single error"]
        )
        assert not result.is_successful()

    def test_result_with_multiple_errors(self):
        """Test result with multiple errors"""
        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0,
            errors=["error1", "error2", "error3"]
        )
        assert not result.is_successful()

    def test_get_step_result_nonexistent_step(self):
        """Test getting result from nonexistent step"""
        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0
        )
        assert result.get_step_result("nonexistent") is None

    def test_get_step_result_with_none_result(self):
        """Test getting step with None result"""
        step = WorkflowStep(name="test", agent_type="coder", task="test")
        step.result = None

        result = WorkflowResult(
            workflow_id="test",
            status="completed",
            steps={"test": step},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0
        )
        assert result.get_step_result("test") is None

    def test_failed_status_with_no_errors(self):
        """Test failed status but no errors in list"""
        result = WorkflowResult(
            workflow_id="test",
            status="failed",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0,
            errors=[]
        )
        assert not result.is_successful()

    def test_partial_status(self):
        """Test partial completion status"""
        result = WorkflowResult(
            workflow_id="test",
            status="partial",
            steps={},
            outputs={},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0
        )
        assert not result.is_successful()


class TestWorkflowValidationEdgeCases:
    """Test workflow validation edge cases"""

    def test_validate_empty_workflow(self):
        """Test validation of workflow with no steps"""
        orchestrator = WorkflowOrchestrator("empty")
        # Should not raise error for empty workflow
        orchestrator._validate_workflow()

    def test_validate_workflow_with_self_dependency(self):
        """Test step depending on itself"""
        orchestrator = WorkflowOrchestrator("self_dep")

        step = WorkflowStep(
            name="self_dep",
            agent_type="coder",
            task="test",
            dependencies=["self_dep"]
        )
        orchestrator.add_step(step)

        with pytest.raises(ValueError, match="Circular dependency"):
            orchestrator._validate_workflow()

    def test_validate_workflow_with_deep_circular_dependency(self):
        """Test deep circular dependency chain A->B->C->A"""
        orchestrator = WorkflowOrchestrator("deep_cycle")

        orchestrator.add_step(WorkflowStep(
            name="A", agent_type="coder", task="test", dependencies=["C"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="B", agent_type="coder", task="test", dependencies=["A"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="C", agent_type="coder", task="test", dependencies=["B"]
        ))

        with pytest.raises(ValueError, match="Circular dependency"):
            orchestrator._validate_workflow()

    def test_validate_workflow_with_complex_circular_dependency(self):
        """Test complex circular dependency"""
        orchestrator = WorkflowOrchestrator("complex")

        orchestrator.add_step(WorkflowStep(
            name="A", agent_type="coder", task="test", dependencies=["B", "C"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="B", agent_type="coder", task="test", dependencies=["D"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="C", agent_type="coder", task="test", dependencies=["D"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="D", agent_type="coder", task="test", dependencies=["A"]
        ))

        with pytest.raises(ValueError, match="Circular dependency"):
            orchestrator._validate_workflow()


class TestWorkflowExecutionOrderEdgeCases:
    """Test execution order calculation edge cases"""

    def test_execution_order_single_step(self):
        """Test execution order with single step"""
        orchestrator = WorkflowOrchestrator("single")
        orchestrator.add_step(WorkflowStep(
            name="only", agent_type="coder", task="test"
        ))

        levels = orchestrator._calculate_execution_order()
        assert len(levels) == 1
        assert levels[0] == ["only"]

    def test_execution_order_all_independent(self):
        """Test execution order with all independent steps"""
        orchestrator = WorkflowOrchestrator("independent")

        for i in range(10):
            orchestrator.add_step(WorkflowStep(
                name=f"step{i}", agent_type="coder", task="test"
            ))

        levels = orchestrator._calculate_execution_order()
        assert len(levels) == 1
        assert len(levels[0]) == 10

    def test_execution_order_linear_chain(self):
        """Test execution order with linear dependency chain"""
        orchestrator = WorkflowOrchestrator("linear")

        orchestrator.add_step(WorkflowStep(
            name="step1", agent_type="coder", task="test"
        ))
        for i in range(2, 11):
            orchestrator.add_step(WorkflowStep(
                name=f"step{i}",
                agent_type="coder",
                task="test",
                dependencies=[f"step{i-1}"]
            ))

        levels = orchestrator._calculate_execution_order()
        assert len(levels) == 10

    def test_execution_order_diamond_pattern(self):
        """Test diamond dependency pattern"""
        orchestrator = WorkflowOrchestrator("diamond")

        orchestrator.add_step(WorkflowStep(
            name="top", agent_type="coder", task="test"
        ))
        orchestrator.add_step(WorkflowStep(
            name="left", agent_type="coder", task="test", dependencies=["top"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="right", agent_type="coder", task="test", dependencies=["top"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="bottom",
            agent_type="coder",
            task="test",
            dependencies=["left", "right"]
        ))

        levels = orchestrator._calculate_execution_order()
        assert len(levels) == 3
        assert "top" in levels[0]
        assert set(levels[1]) == {"left", "right"}
        assert "bottom" in levels[2]


@pytest.mark.asyncio
class TestWorkflowExecutionEdgeCases:
    """Test workflow execution edge cases"""

    async def test_execute_with_immediate_failure_no_retry(self):
        """Test execution with immediate failure and no retries"""
        orchestrator = WorkflowOrchestrator("no_retry")

        step = WorkflowStep(
            name="fail",
            agent_type="coder",
            task="test",
            retry_count=1  # Will try once and fail
        )
        orchestrator.add_step(step)

        async def failing_executor(agent_type, task):
            raise Exception("Immediate failure")

        result = await orchestrator.execute(failing_executor)

        assert result.status == "failed"
        assert orchestrator.steps["fail"].status == StepStatus.FAILED

    async def test_execute_with_timeout_on_first_attempt(self):
        """Test step timing out on first attempt"""
        orchestrator = WorkflowOrchestrator("timeout")

        step = WorkflowStep(
            name="timeout",
            agent_type="coder",
            task="test",
            timeout=0.1,  # Very short timeout
            retry_count=1
        )
        orchestrator.add_step(step)

        async def slow_executor(agent_type, task):
            await asyncio.sleep(1)  # Longer than timeout
            return "done"

        result = await orchestrator.execute(slow_executor)

        assert result.status == "failed"
        assert orchestrator.steps["timeout"].status == StepStatus.FAILED
        assert "timed out" in orchestrator.steps["timeout"].error

    async def test_execute_all_steps_skipped_by_conditions(self):
        """Test workflow where all steps are skipped"""
        orchestrator = WorkflowOrchestrator("all_skipped")

        orchestrator.add_step(WorkflowStep(
            name="step1",
            agent_type="coder",
            task="test",
            condition=lambda ctx: False
        ))
        orchestrator.add_step(WorkflowStep(
            name="step2",
            agent_type="coder",
            task="test",
            condition=lambda ctx: False
        ))

        async def executor(agent_type, task):
            return "done"

        result = await orchestrator.execute(executor)

        assert all(
            s.status == StepStatus.SKIPPED
            for s in orchestrator.steps.values()
        )

    async def test_execute_with_conditional_dependencies(self):
        """Test conditional execution affecting dependencies"""
        orchestrator = WorkflowOrchestrator("conditional_deps")

        orchestrator.add_step(WorkflowStep(
            name="step1",
            agent_type="coder",
            task="test",
            condition=lambda ctx: False  # Skipped
        ))
        orchestrator.add_step(WorkflowStep(
            name="step2",
            agent_type="coder",
            task="test",
            dependencies=["step1"]  # Depends on skipped step
        ))

        async def executor(agent_type, task):
            return "done"

        result = await orchestrator.execute(executor)

        assert orchestrator.steps["step1"].status == StepStatus.SKIPPED
        assert orchestrator.steps["step2"].status == StepStatus.COMPLETED

    async def test_execute_fail_fast_stops_on_first_failure(self):
        """Test fail_fast stops execution immediately"""
        orchestrator = WorkflowOrchestrator("fail_fast")

        orchestrator.add_step(WorkflowStep(
            name="fail", agent_type="coder", task="test"
        ))
        orchestrator.add_step(WorkflowStep(
            name="never_run", agent_type="coder", task="test"
        ))

        async def executor(agent_type, task):
            if task == "test" and agent_type == "coder":
                raise Exception("First failure")
            return "done"

        result = await orchestrator.execute(executor, fail_fast=True)

        assert result.status == "failed"
        assert len(result.errors) > 0

    async def test_execute_with_very_high_max_concurrent(self):
        """Test with very high concurrent limit"""
        orchestrator = WorkflowOrchestrator("high_concurrent", max_concurrent=1000)

        for i in range(50):
            orchestrator.add_step(WorkflowStep(
                name=f"step{i}", agent_type="coder", task="test"
            ))

        execution_count = []

        async def executor(agent_type, task):
            execution_count.append(1)
            await asyncio.sleep(0.01)
            return "done"

        result = await orchestrator.execute(executor)

        assert result.status == "completed"
        assert len(execution_count) == 50

    async def test_execute_stores_intermediate_results_in_context(self):
        """Test that step results are stored in context"""
        orchestrator = WorkflowOrchestrator("context_test")

        orchestrator.add_step(WorkflowStep(
            name="step1", agent_type="coder", task="test"
        ))
        orchestrator.add_step(WorkflowStep(
            name="step2",
            agent_type="coder",
            task="test",
            dependencies=["step1"]
        ))

        async def executor(agent_type, task):
            return f"result_{agent_type}"

        result = await orchestrator.execute(executor)

        assert "step_step1_result" in orchestrator.context
        assert "step_step2_result" in orchestrator.context

    async def test_execute_with_exception_in_executor(self):
        """Test handling of exceptions in executor"""
        orchestrator = WorkflowOrchestrator("exception")

        orchestrator.add_step(WorkflowStep(
            name="exception_step",
            agent_type="coder",
            task="test",
            retry_count=1
        ))

        async def executor(agent_type, task):
            raise ValueError("Test exception")

        result = await orchestrator.execute(executor)

        assert result.status == "failed"
        assert len(result.errors) > 0


class TestWorkflowVisualizationEdgeCases:
    """Test visualization edge cases"""

    def test_visualize_empty_workflow(self):
        """Test visualizing empty workflow"""
        orchestrator = WorkflowOrchestrator("empty")
        viz = orchestrator.visualize()

        assert "empty" in viz
        assert "Workflow:" in viz

    def test_visualize_workflow_with_no_dependencies(self):
        """Test visualizing workflow with independent steps"""
        orchestrator = WorkflowOrchestrator("independent")

        for i in range(5):
            orchestrator.add_step(WorkflowStep(
                name=f"step{i}", agent_type="coder", task="test"
            ))

        viz = orchestrator.visualize()

        assert "Level 1:" in viz
        for i in range(5):
            assert f"step{i}" in viz

    def test_visualize_workflow_with_conditionals(self):
        """Test visualizing workflow with conditional steps"""
        orchestrator = WorkflowOrchestrator("conditional")

        orchestrator.add_step(WorkflowStep(
            name="conditional",
            agent_type="coder",
            task="test",
            condition=lambda ctx: True
        ))

        viz = orchestrator.visualize()

        assert "conditional" in viz
        assert "Conditional: yes" in viz

    def test_visualize_complex_workflow(self):
        """Test visualizing complex multi-level workflow"""
        orchestrator = WorkflowOrchestrator("complex")

        orchestrator.add_step(WorkflowStep(
            name="L1_A", agent_type="coder", task="test"
        ))
        orchestrator.add_step(WorkflowStep(
            name="L1_B", agent_type="coder", task="test"
        ))
        orchestrator.add_step(WorkflowStep(
            name="L2_A",
            agent_type="reviewer",
            task="test",
            dependencies=["L1_A"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="L2_B",
            agent_type="tester",
            task="test",
            dependencies=["L1_B"]
        ))
        orchestrator.add_step(WorkflowStep(
            name="L3_Final",
            agent_type="coordinator",
            task="test",
            dependencies=["L2_A", "L2_B"],
            condition=lambda ctx: True
        ))

        viz = orchestrator.visualize()

        assert "Level 1:" in viz
        assert "Level 2:" in viz
        assert "Level 3:" in viz
        assert "coordinator" in viz


class TestWorkflowContextManagement:
    """Test context management"""

    def test_set_context_simple_values(self):
        """Test setting simple context values"""
        orchestrator = WorkflowOrchestrator("context")

        orchestrator.set_context("key1", "value1")
        orchestrator.set_context("key2", 42)
        orchestrator.set_context("key3", True)

        assert orchestrator.context["key1"] == "value1"
        assert orchestrator.context["key2"] == 42
        assert orchestrator.context["key3"] is True

    def test_set_context_complex_values(self):
        """Test setting complex context values"""
        orchestrator = WorkflowOrchestrator("context")

        orchestrator.set_context("dict", {"nested": {"value": 1}})
        orchestrator.set_context("list", [1, 2, 3])
        orchestrator.set_context("mixed", {"list": [1, 2], "dict": {"a": 1}})

        assert orchestrator.context["dict"]["nested"]["value"] == 1
        assert len(orchestrator.context["list"]) == 3

    def test_set_context_overwrites_existing(self):
        """Test that context can be overwritten"""
        orchestrator = WorkflowOrchestrator("context")

        orchestrator.set_context("key", "value1")
        assert orchestrator.context["key"] == "value1"

        orchestrator.set_context("key", "value2")
        assert orchestrator.context["key"] == "value2"

    def test_context_persists_across_steps(self):
        """Test context is shared across workflow"""
        orchestrator = WorkflowOrchestrator("context")

        orchestrator.set_context("shared", "data")
        orchestrator.add_step(WorkflowStep(
            name="step1", agent_type="coder", task="test"
        ))

        assert orchestrator.context["shared"] == "data"


class TestWorkflowStepManagement:
    """Test step management operations"""

    def test_add_multiple_steps_fluently(self):
        """Test fluent interface for adding steps"""
        orchestrator = WorkflowOrchestrator("fluent")

        result = (orchestrator
                  .add_step(WorkflowStep(name="s1", agent_type="coder", task="t"))
                  .add_step(WorkflowStep(name="s2", agent_type="coder", task="t"))
                  .add_step(WorkflowStep(name="s3", agent_type="coder", task="t")))

        assert result is orchestrator
        assert len(orchestrator.steps) == 3

    def test_add_steps_bulk(self):
        """Test adding multiple steps at once"""
        orchestrator = WorkflowOrchestrator("bulk")

        steps = [
            WorkflowStep(name=f"step{i}", agent_type="coder", task="test")
            for i in range(10)
        ]

        orchestrator.add_steps(steps)

        assert len(orchestrator.steps) == 10

    def test_cannot_add_duplicate_step_name(self):
        """Test that duplicate step names are rejected"""
        orchestrator = WorkflowOrchestrator("duplicate")

        orchestrator.add_step(WorkflowStep(
            name="duplicate", agent_type="coder", task="test"
        ))

        with pytest.raises(ValueError, match="already exists"):
            orchestrator.add_step(WorkflowStep(
                name="duplicate", agent_type="reviewer", task="other"
            ))
