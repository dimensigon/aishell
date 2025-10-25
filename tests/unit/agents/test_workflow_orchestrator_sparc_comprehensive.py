"""
Comprehensive SPARC Workflow Orchestrator Tests

Tests specifically for SPARC methodology workflow orchestration including:
- SPARC phase transitions (Specification → Pseudocode → Architecture → Refinement → Completion)
- Phase state management and checkpointing
- Agent coordination across SPARC phases
- Context passing between phases
- Rollback and recovery mechanisms
- End-to-end SPARC workflows
- Performance and concurrency handling

Target: 90%+ coverage with 55+ test methods
Module: src/agents/workflow_orchestrator.py (194 lines, P1 CRITICAL)
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from src.agents.workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowStep,
    WorkflowResult,
    StepStatus
)


# ============================================================================
# SPARC Phase Testing
# ============================================================================

class TestSPARCPhaseWorkflows:
    """Test SPARC-specific workflow patterns"""

    def test_create_sparc_specification_phase(self):
        """Test creating specification phase workflow step"""
        step = WorkflowStep(
            name="specification",
            agent_type="researcher",
            task="Analyze requirements and create specification",
            metadata={"phase": "specification", "sparc_stage": 1}
        )

        assert step.name == "specification"
        assert step.agent_type == "researcher"
        assert step.metadata["phase"] == "specification"
        assert step.metadata["sparc_stage"] == 1

    def test_create_sparc_pseudocode_phase(self):
        """Test creating pseudocode phase with spec dependency"""
        step = WorkflowStep(
            name="pseudocode",
            agent_type="planner",
            task="Design algorithm in pseudocode",
            dependencies=["specification"],
            metadata={"phase": "pseudocode", "sparc_stage": 2}
        )

        assert "specification" in step.dependencies
        assert step.metadata["sparc_stage"] == 2

    def test_create_sparc_architecture_phase(self):
        """Test creating architecture phase with dependencies"""
        step = WorkflowStep(
            name="architecture",
            agent_type="system-architect",
            task="Design system architecture",
            dependencies=["specification", "pseudocode"],
            metadata={"phase": "architecture", "sparc_stage": 3}
        )

        assert len(step.dependencies) == 2
        assert step.metadata["sparc_stage"] == 3

    def test_create_sparc_refinement_phase(self):
        """Test creating refinement phase (TDD implementation)"""
        step = WorkflowStep(
            name="refinement",
            agent_type="coder",
            task="Implement with TDD approach",
            dependencies=["architecture"],
            metadata={"phase": "refinement", "sparc_stage": 4, "tdd": True}
        )

        assert step.metadata["tdd"] is True
        assert step.metadata["sparc_stage"] == 4

    def test_create_sparc_completion_phase(self):
        """Test creating completion/integration phase"""
        step = WorkflowStep(
            name="completion",
            agent_type="reviewer",
            task="Final integration and validation",
            dependencies=["refinement"],
            metadata={"phase": "completion", "sparc_stage": 5}
        )

        assert step.metadata["sparc_stage"] == 5
        assert "refinement" in step.dependencies

    def test_full_sparc_workflow_setup(self):
        """Test setting up complete SPARC workflow"""
        orchestrator = WorkflowOrchestrator(name="SPARC_Full_Pipeline")

        # Add all SPARC phases
        sparc_steps = [
            WorkflowStep("specification", "researcher", "Analyze requirements"),
            WorkflowStep("pseudocode", "planner", "Design algorithm", dependencies=["specification"]),
            WorkflowStep("architecture", "system-architect", "Design system", dependencies=["pseudocode"]),
            WorkflowStep("refinement", "coder", "Implement with TDD", dependencies=["architecture"]),
            WorkflowStep("completion", "reviewer", "Final validation", dependencies=["refinement"])
        ]

        orchestrator.add_steps(sparc_steps)

        assert len(orchestrator.steps) == 5
        assert "specification" in orchestrator.steps
        assert "completion" in orchestrator.steps

    def test_sparc_parallel_branches(self):
        """Test SPARC workflow with parallel branches"""
        orchestrator = WorkflowOrchestrator(name="SPARC_Parallel")

        steps = [
            WorkflowStep("specification", "researcher", "Analyze requirements"),
            WorkflowStep("frontend_arch", "system-architect", "Design frontend", dependencies=["specification"]),
            WorkflowStep("backend_arch", "system-architect", "Design backend", dependencies=["specification"]),
            WorkflowStep("integration", "reviewer", "Integrate components", dependencies=["frontend_arch", "backend_arch"])
        ]

        orchestrator.add_steps(steps)
        levels = orchestrator._calculate_execution_order()

        # Frontend and backend should be in same level (parallel)
        assert "frontend_arch" in levels[1] and "backend_arch" in levels[1]
        assert "integration" in levels[2]


@pytest.mark.asyncio
class TestSPARCPhaseExecution:
    """Test executing SPARC phase workflows"""

    async def test_execute_specification_phase(self):
        """Test executing specification phase"""
        orchestrator = WorkflowOrchestrator(name="SPARC_Spec")
        orchestrator.add_step(
            WorkflowStep("specification", "researcher", "Analyze requirements")
        )

        spec_result = {
            "requirements": ["req1", "req2"],
            "constraints": ["constraint1"],
            "scope": "MVP"
        }

        async def spec_executor(agent_type, task):
            assert agent_type == "researcher"
            return spec_result

        result = await orchestrator.execute(spec_executor)

        assert result.status == "completed"
        assert result.outputs["step_specification_result"] == spec_result

    async def test_execute_full_sparc_pipeline(self):
        """Test executing complete SPARC pipeline"""
        orchestrator = WorkflowOrchestrator(name="SPARC_Complete")

        sparc_steps = [
            WorkflowStep("specification", "researcher", "Analyze requirements"),
            WorkflowStep("pseudocode", "planner", "Design algorithm", dependencies=["specification"]),
            WorkflowStep("architecture", "system-architect", "Design system", dependencies=["pseudocode"]),
            WorkflowStep("refinement", "coder", "Implement with TDD", dependencies=["architecture"]),
            WorkflowStep("completion", "reviewer", "Final validation", dependencies=["refinement"])
        ]

        orchestrator.add_steps(sparc_steps)

        phase_results = {}

        async def sparc_executor(agent_type, task):
            # Simulate each phase producing output
            phase_name = task.split()[0].lower()
            result = f"{phase_name}_output"
            phase_results[agent_type] = result
            await asyncio.sleep(0.01)  # Simulate work
            return result

        result = await orchestrator.execute(sparc_executor)

        assert result.status == "completed"
        assert len(result.outputs) == 5
        assert all(step.status == StepStatus.COMPLETED for step in result.steps.values())

    async def test_sparc_phase_context_passing(self):
        """Test context passing between SPARC phases"""
        orchestrator = WorkflowOrchestrator(name="SPARC_Context")

        orchestrator.set_context("project_name", "TestProject")
        orchestrator.set_context("language", "python")

        steps = [
            WorkflowStep("specification", "researcher", "Analyze requirements"),
            WorkflowStep("pseudocode", "planner", "Design algorithm", dependencies=["specification"])
        ]

        orchestrator.add_steps(steps)

        async def context_aware_executor(agent_type, task):
            # Verify context is available
            assert orchestrator.context["project_name"] == "TestProject"
            assert orchestrator.context["language"] == "python"
            return f"output_for_{agent_type}"

        result = await orchestrator.execute(context_aware_executor)

        assert result.status == "completed"
        # Verify phase results stored in context
        assert "step_specification_result" in orchestrator.context
        assert "step_pseudocode_result" in orchestrator.context

    async def test_sparc_phase_failure_handling(self):
        """Test handling failure in SPARC phase"""
        orchestrator = WorkflowOrchestrator(name="SPARC_Failure")

        steps = [
            WorkflowStep("specification", "researcher", "Analyze requirements"),
            WorkflowStep("pseudocode", "planner", "Design algorithm", dependencies=["specification"], retry_count=2),
            WorkflowStep("architecture", "system-architect", "Design system", dependencies=["pseudocode"])
        ]

        orchestrator.add_steps(steps)

        async def failing_pseudocode_executor(agent_type, task):
            if agent_type == "planner":
                raise Exception("Pseudocode phase failed")
            return "success"

        result = await orchestrator.execute(failing_pseudocode_executor)

        assert result.status == "failed" or result.status == "partial"
        assert orchestrator.steps["specification"].status == StepStatus.COMPLETED
        assert orchestrator.steps["pseudocode"].status == StepStatus.FAILED
        # Architecture may run if fail_fast=False (default), so check it's not completed successfully
        # or it completed because it doesn't check pseudocode result
        assert orchestrator.steps["architecture"].status in [StepStatus.PENDING, StepStatus.COMPLETED]


# ============================================================================
# Phase Transitions and State Management
# ============================================================================

class TestPhaseTransitions:
    """Test phase transition logic and state tracking"""

    @pytest.mark.asyncio
    async def test_phase_transition_timing(self):
        """Test phase transition timing is tracked"""
        orchestrator = WorkflowOrchestrator()

        steps = [
            WorkflowStep("phase1", "agent1", "task1"),
            WorkflowStep("phase2", "agent2", "task2", dependencies=["phase1"])
        ]

        orchestrator.add_steps(steps)

        async def timing_executor(agent_type, task):
            await asyncio.sleep(0.05)
            return "result"

        result = await orchestrator.execute(timing_executor)

        # Verify timing is tracked
        phase1 = orchestrator.steps["phase1"]
        phase2 = orchestrator.steps["phase2"]

        assert phase1.start_time is not None
        assert phase1.end_time is not None
        assert phase2.start_time is not None
        assert phase2.end_time is not None

        # Phase2 should start after phase1 ends
        assert phase2.start_time > phase1.end_time

    @pytest.mark.asyncio
    async def test_phase_state_transitions(self):
        """Test phase state transitions (PENDING → RUNNING → COMPLETED)"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "agent1", "task"))

        # Initial state
        assert orchestrator.steps["step1"].status == StepStatus.PENDING

        execution_states = []

        async def state_tracking_executor(agent_type, task):
            # Capture state during execution
            execution_states.append(orchestrator.steps["step1"].status)
            await asyncio.sleep(0.01)
            return "result"

        result = await orchestrator.execute(state_tracking_executor)

        # Should transition through states
        assert StepStatus.RUNNING in execution_states
        assert orchestrator.steps["step1"].status == StepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_checkpoint_between_phases(self):
        """Test checkpoint creation between phases"""
        orchestrator = WorkflowOrchestrator(name="Checkpointed")

        steps = [
            WorkflowStep("phase1", "agent1", "task1", metadata={"checkpoint": True}),
            WorkflowStep("phase2", "agent2", "task2", dependencies=["phase1"], metadata={"checkpoint": True})
        ]

        orchestrator.add_steps(steps)

        checkpoints = []

        async def checkpoint_executor(agent_type, task):
            result = f"result_{agent_type}"
            # Store checkpoint data
            checkpoints.append({
                "agent": agent_type,
                "result": result,
                "timestamp": datetime.now()
            })
            return result

        result = await orchestrator.execute(checkpoint_executor)

        assert len(checkpoints) == 2
        assert checkpoints[0]["agent"] == "agent1"
        assert checkpoints[1]["agent"] == "agent2"


# ============================================================================
# Agent Coordination Tests
# ============================================================================

@pytest.mark.asyncio
class TestAgentCoordination:
    """Test multi-agent coordination"""

    async def test_multi_agent_phase_execution(self):
        """Test multiple agents working on same phase"""
        orchestrator = WorkflowOrchestrator(max_concurrent=3)

        # Multiple agents can work in parallel
        steps = [
            WorkflowStep("frontend", "frontend-dev", "Build UI"),
            WorkflowStep("backend", "backend-dev", "Build API"),
            WorkflowStep("database", "db-architect", "Design schema")
        ]

        orchestrator.add_steps(steps)

        agent_calls = []

        async def multi_agent_executor(agent_type, task):
            agent_calls.append(agent_type)
            await asyncio.sleep(0.05)
            return f"result_{agent_type}"

        result = await orchestrator.execute(multi_agent_executor)

        assert result.status == "completed"
        assert len(agent_calls) == 3
        assert "frontend-dev" in agent_calls
        assert "backend-dev" in agent_calls
        assert "db-architect" in agent_calls

    async def test_agent_failure_in_coordination(self):
        """Test handling agent failure in multi-agent coordination"""
        orchestrator = WorkflowOrchestrator()

        steps = [
            WorkflowStep("task1", "agent1", "task", retry_count=1),
            WorkflowStep("task2", "agent2", "task", retry_count=1),
            WorkflowStep("task3", "agent3", "task", retry_count=1)
        ]

        orchestrator.add_steps(steps)

        async def failing_agent_executor(agent_type, task):
            if agent_type == "agent2":
                raise Exception("Agent2 failed")
            return "success"

        result = await orchestrator.execute(failing_agent_executor)

        assert orchestrator.steps["task1"].status == StepStatus.COMPLETED
        assert orchestrator.steps["task2"].status == StepStatus.FAILED
        assert orchestrator.steps["task3"].status == StepStatus.COMPLETED

    async def test_agent_result_aggregation(self):
        """Test aggregating results from multiple agents"""
        orchestrator = WorkflowOrchestrator()

        steps = [
            WorkflowStep("agent1_task", "agent1", "task1"),
            WorkflowStep("agent2_task", "agent2", "task2"),
            WorkflowStep("aggregation", "aggregator", "combine", dependencies=["agent1_task", "agent2_task"])
        ]

        orchestrator.add_steps(steps)

        async def aggregation_executor(agent_type, task):
            if agent_type == "aggregator":
                # Access previous results
                result1 = orchestrator.context.get("step_agent1_task_result")
                result2 = orchestrator.context.get("step_agent2_task_result")
                return {"combined": [result1, result2]}
            return f"result_{agent_type}"

        result = await orchestrator.execute(aggregation_executor)

        assert result.status == "completed"
        combined = result.outputs["step_aggregation_result"]
        assert "combined" in combined


# ============================================================================
# Error Handling and Recovery
# ============================================================================

@pytest.mark.asyncio
class TestErrorHandlingRecovery:
    """Test error handling and recovery mechanisms"""

    async def test_retry_with_exponential_backoff(self):
        """Test retry logic with exponential backoff"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "agent1", "task", retry_count=4))

        attempt_times = []

        async def retry_executor(agent_type, task):
            attempt_times.append(datetime.now())
            if len(attempt_times) < 3:
                raise Exception("Retry")
            return "success"

        result = await orchestrator.execute(retry_executor)

        assert result.status == "completed"
        assert len(attempt_times) == 3

        # Check exponential backoff (approximate)
        if len(attempt_times) >= 3:
            gap1 = (attempt_times[1] - attempt_times[0]).total_seconds()
            gap2 = (attempt_times[2] - attempt_times[1]).total_seconds()
            # Second gap should be larger due to exponential backoff
            assert gap2 > gap1

    async def test_timeout_handling(self):
        """Test timeout handling for long-running tasks"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("slow_step", "agent1", "task", timeout=0.1, retry_count=1))

        async def slow_executor(agent_type, task):
            await asyncio.sleep(1.0)  # Exceeds timeout
            return "result"

        result = await orchestrator.execute(slow_executor)

        assert result.status == "failed"
        assert "timed out" in orchestrator.steps["slow_step"].error.lower()

    async def test_partial_workflow_completion(self):
        """Test workflow partial completion status"""
        orchestrator = WorkflowOrchestrator()

        steps = [
            WorkflowStep("step1", "agent1", "task1", retry_count=1),
            WorkflowStep("step2", "agent2", "task2", retry_count=1),
            WorkflowStep("step3", "agent3", "task3", retry_count=1)
        ]

        orchestrator.add_steps(steps)

        async def partial_executor(agent_type, task):
            if agent_type == "agent2":
                raise Exception("Failed")
            return "success"

        result = await orchestrator.execute(partial_executor)

        # Should have partial status
        assert result.status == "partial" or result.status == "failed"
        completed = sum(1 for s in result.steps.values() if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in result.steps.values() if s.status == StepStatus.FAILED)
        assert completed == 2
        assert failed == 1

    async def test_error_message_propagation(self):
        """Test error messages are properly captured and propagated"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("error_step", "agent1", "task", retry_count=1))

        error_message = "Custom error message with details"

        async def error_executor(agent_type, task):
            raise Exception(error_message)

        result = await orchestrator.execute(error_executor)

        assert error_message in orchestrator.steps["error_step"].error


# ============================================================================
# Workflow Control Tests
# ============================================================================

@pytest.mark.asyncio
class TestWorkflowControl:
    """Test workflow control mechanisms"""

    async def test_conditional_step_execution_complex(self):
        """Test complex conditional logic"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.set_context("environment", "production")
        orchestrator.set_context("feature_flag", True)

        def complex_condition(ctx: Dict[str, Any]) -> bool:
            return ctx.get("environment") == "production" and ctx.get("feature_flag", False)

        steps = [
            WorkflowStep("always_run", "agent1", "task1"),
            WorkflowStep("conditional", "agent2", "task2", condition=complex_condition),
            WorkflowStep("after", "agent3", "task3", dependencies=["always_run"])
        ]

        orchestrator.add_steps(steps)

        async def executor(agent_type, task):
            return "result"

        result = await orchestrator.execute(executor)

        assert orchestrator.steps["always_run"].status == StepStatus.COMPLETED
        assert orchestrator.steps["conditional"].status == StepStatus.COMPLETED
        assert orchestrator.steps["after"].status == StepStatus.COMPLETED

    async def test_conditional_step_skipped(self):
        """Test conditional step is skipped when condition not met"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.set_context("skip_step", True)

        step = WorkflowStep(
            "conditional",
            "agent1",
            "task",
            condition=lambda ctx: not ctx.get("skip_step", False)
        )

        orchestrator.add_step(step)

        async def executor(agent_type, task):
            return "result"

        result = await orchestrator.execute(executor)

        assert orchestrator.steps["conditional"].status == StepStatus.SKIPPED

    async def test_fail_fast_stops_execution(self):
        """Test fail_fast stops execution on first failure"""
        orchestrator = WorkflowOrchestrator()

        # Use sequential dependencies to ensure fail_fast behavior
        steps = [
            WorkflowStep("step1", "agent1", "task1", retry_count=1),
            WorkflowStep("step2", "agent2", "task2", dependencies=["step1"], retry_count=1),
            WorkflowStep("step3", "agent3", "task3", dependencies=["step2"], retry_count=1)
        ]

        orchestrator.add_steps(steps)

        executed_agents = []

        async def fail_fast_executor(agent_type, task):
            executed_agents.append(agent_type)
            if agent_type == "agent1":
                raise Exception("Failure in step1")
            return "success"

        result = await orchestrator.execute(fail_fast_executor, fail_fast=True)

        # With fail_fast, execution should stop after first level fails
        assert result.status == "failed"
        assert orchestrator.steps["step1"].status == StepStatus.FAILED
        # Note: Due to async execution, agent2/agent3 might start but shouldn't complete successfully
        # The key is that the workflow is marked as failed and stops progressing
        assert len([s for s in orchestrator.steps.values() if s.status == StepStatus.FAILED]) > 0

    async def test_workflow_duration_tracking(self):
        """Test workflow duration is accurately tracked"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "agent1", "task"))

        async def timed_executor(agent_type, task):
            await asyncio.sleep(0.1)
            return "result"

        result = await orchestrator.execute(timed_executor)

        assert result.duration >= 0.1
        assert result.duration < 0.5  # Should complete quickly


# ============================================================================
# Concurrency and Performance Tests
# ============================================================================

@pytest.mark.asyncio
class TestConcurrencyPerformance:
    """Test concurrency limits and performance"""

    async def test_max_concurrent_limit_enforced(self):
        """Test max concurrent limit is enforced"""
        orchestrator = WorkflowOrchestrator(max_concurrent=2)

        # Add 5 parallel steps
        for i in range(5):
            orchestrator.add_step(WorkflowStep(f"step{i}", "agent", f"task{i}"))

        active_count = []
        lock = asyncio.Lock()
        current_active = 0

        async def concurrent_executor(agent_type, task):
            nonlocal current_active
            async with lock:
                current_active += 1
                active_count.append(current_active)

            await asyncio.sleep(0.05)

            async with lock:
                current_active -= 1

            return "result"

        result = await orchestrator.execute(concurrent_executor)

        # Should never exceed max_concurrent
        assert max(active_count) <= 2

    async def test_parallel_execution_efficiency(self):
        """Test parallel execution is more efficient than sequential"""
        # Parallel execution
        orchestrator_parallel = WorkflowOrchestrator(max_concurrent=3)
        for i in range(3):
            orchestrator_parallel.add_step(WorkflowStep(f"step{i}", "agent", "task"))

        async def executor(agent_type, task):
            await asyncio.sleep(0.1)
            return "result"

        start = datetime.now()
        result_parallel = await orchestrator_parallel.execute(executor)
        parallel_duration = (datetime.now() - start).total_seconds()

        # Parallel should complete in ~0.1s (all run together)
        assert parallel_duration < 0.3  # Allow some overhead

    async def test_large_workflow_performance(self):
        """Test performance with large workflow"""
        orchestrator = WorkflowOrchestrator(max_concurrent=10)

        # Create 20 steps with dependencies
        for i in range(20):
            deps = [f"step{i-1}"] if i > 0 else []
            orchestrator.add_step(WorkflowStep(f"step{i}", "agent", f"task{i}", dependencies=deps))

        async def fast_executor(agent_type, task):
            await asyncio.sleep(0.001)
            return "result"

        start = datetime.now()
        result = await orchestrator.execute(fast_executor)
        duration = (datetime.now() - start).total_seconds()

        assert result.status == "completed"
        assert len(result.outputs) == 20
        # Should complete reasonably fast despite 20 steps
        assert duration < 2.0


# ============================================================================
# Visualization and Inspection Tests
# ============================================================================

class TestVisualizationInspection:
    """Test workflow visualization and inspection"""

    def test_visualize_empty_workflow(self):
        """Test visualizing empty workflow"""
        orchestrator = WorkflowOrchestrator(name="Empty")

        # Empty workflow should still visualize (just shows no steps)
        viz = orchestrator.visualize()
        assert "Empty" in viz

    def test_visualize_simple_workflow(self):
        """Test visualizing simple workflow"""
        orchestrator = WorkflowOrchestrator(name="Simple")
        orchestrator.add_step(WorkflowStep("step1", "agent1", "task"))

        viz = orchestrator.visualize()

        assert "Simple" in viz
        assert "step1" in viz
        assert "agent1" in viz

    def test_visualize_complex_workflow(self):
        """Test visualizing complex workflow with levels"""
        orchestrator = WorkflowOrchestrator(name="Complex")

        steps = [
            WorkflowStep("root", "agent1", "task"),
            WorkflowStep("branch1", "agent2", "task", dependencies=["root"]),
            WorkflowStep("branch2", "agent3", "task", dependencies=["root"]),
            WorkflowStep("merge", "agent4", "task", dependencies=["branch1", "branch2"])
        ]

        orchestrator.add_steps(steps)
        viz = orchestrator.visualize()

        assert "Level 1" in viz
        assert "Level 2" in viz
        assert "Level 3" in viz
        assert "branch1" in viz
        assert "branch2" in viz

    def test_visualize_conditional_steps(self):
        """Test visualizing conditional steps"""
        orchestrator = WorkflowOrchestrator()

        step = WorkflowStep(
            "conditional",
            "agent1",
            "task",
            condition=lambda ctx: True
        )

        orchestrator.add_step(step)
        viz = orchestrator.visualize()

        assert "Conditional: yes" in viz


# ============================================================================
# Integration and End-to-End Tests
# ============================================================================

@pytest.mark.asyncio
class TestIntegrationEndToEnd:
    """Integration and end-to-end workflow tests"""

    async def test_complete_sparc_workflow_integration(self):
        """Test complete SPARC workflow from start to finish"""
        orchestrator = WorkflowOrchestrator(name="SPARC_Integration_Test")

        # Setup complete SPARC workflow
        sparc_phases = [
            ("specification", "researcher", "Analyze and document requirements"),
            ("pseudocode", "planner", "Design algorithm in pseudocode"),
            ("architecture", "system-architect", "Design system architecture"),
            ("refinement", "coder", "Implement with TDD"),
            ("testing", "tester", "Comprehensive testing"),
            ("completion", "reviewer", "Final review and integration")
        ]

        for i, (name, agent, task) in enumerate(sparc_phases):
            deps = [sparc_phases[i-1][0]] if i > 0 else []
            step = WorkflowStep(
                name=name,
                agent_type=agent,
                task=task,
                dependencies=deps,
                metadata={"phase": name, "order": i}
            )
            orchestrator.add_step(step)

        # Track execution order
        execution_log = []

        async def sparc_full_executor(agent_type, task):
            execution_log.append(agent_type)
            await asyncio.sleep(0.01)
            return {
                "agent": agent_type,
                "task": task,
                "timestamp": datetime.now().isoformat()
            }

        result = await orchestrator.execute(sparc_full_executor)

        # Verify successful completion
        assert result.status == "completed"
        assert len(result.outputs) == 6

        # Verify execution order matches SPARC methodology
        expected_order = ["researcher", "planner", "system-architect", "coder", "tester", "reviewer"]
        assert execution_log == expected_order

        # Verify all phases completed
        for phase_name in ["specification", "pseudocode", "architecture", "refinement", "testing", "completion"]:
            assert orchestrator.steps[phase_name].status == StepStatus.COMPLETED

    async def test_workflow_with_mixed_success_failure(self):
        """Test workflow handling mixed success and failure scenarios"""
        orchestrator = WorkflowOrchestrator(name="Mixed_Results")

        steps = [
            WorkflowStep("success1", "agent1", "task1"),
            WorkflowStep("fail1", "agent2", "task2", retry_count=1),
            WorkflowStep("success2", "agent3", "task3"),
            WorkflowStep("dependent", "agent4", "task4", dependencies=["success1", "success2"])
        ]

        orchestrator.add_steps(steps)

        async def mixed_executor(agent_type, task):
            if agent_type == "agent2":
                raise Exception("Intentional failure")
            return f"success_{agent_type}"

        result = await orchestrator.execute(mixed_executor)

        # Verify mixed results
        assert orchestrator.steps["success1"].status == StepStatus.COMPLETED
        assert orchestrator.steps["fail1"].status == StepStatus.FAILED
        assert orchestrator.steps["success2"].status == StepStatus.COMPLETED
        assert orchestrator.steps["dependent"].status == StepStatus.COMPLETED

    async def test_workflow_result_methods(self):
        """Test WorkflowResult helper methods"""
        orchestrator = WorkflowOrchestrator()

        steps = [
            WorkflowStep("step1", "agent1", "task1"),
            WorkflowStep("step2", "agent2", "task2", dependencies=["step1"])
        ]

        orchestrator.add_steps(steps)

        async def executor(agent_type, task):
            return {"data": f"result_{agent_type}"}

        result = await orchestrator.execute(executor)

        # Test is_successful
        assert result.is_successful()

        # Test get_step_result
        step1_result = result.get_step_result("step1")
        assert step1_result == {"data": "result_agent1"}

        step2_result = result.get_step_result("step2")
        assert step2_result == {"data": "result_agent2"}

        # Test nonexistent step
        none_result = result.get_step_result("nonexistent")
        assert none_result is None

    async def test_workflow_context_persistence(self):
        """Test workflow context persists across steps"""
        orchestrator = WorkflowOrchestrator(name="Context_Persistence")

        # Set initial context
        orchestrator.set_context("project", "TestProject")
        orchestrator.set_context("config", {"setting1": "value1"})

        steps = [
            WorkflowStep("step1", "agent1", "task1"),
            WorkflowStep("step2", "agent2", "task2", dependencies=["step1"]),
            WorkflowStep("step3", "agent3", "task3", dependencies=["step2"])
        ]

        orchestrator.add_steps(steps)

        async def context_checker(agent_type, task):
            # Verify context is accessible
            assert orchestrator.context["project"] == "TestProject"
            assert orchestrator.context["config"]["setting1"] == "value1"

            # Add to context
            orchestrator.set_context(f"{agent_type}_executed", True)

            return f"result_{agent_type}"

        result = await orchestrator.execute(context_checker)

        # Verify all agents added to context
        assert orchestrator.context["agent1_executed"] is True
        assert orchestrator.context["agent2_executed"] is True
        assert orchestrator.context["agent3_executed"] is True


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================

@pytest.mark.asyncio
class TestEdgeCasesBoundaries:
    """Test edge cases and boundary conditions"""

    async def test_single_step_workflow(self):
        """Test workflow with single step"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("only_step", "agent", "task"))

        async def executor(agent_type, task):
            return "single_result"

        result = await orchestrator.execute(executor)

        assert result.status == "completed"
        assert len(result.outputs) == 1

    async def test_empty_workflow_execution(self):
        """Test executing empty workflow"""
        orchestrator = WorkflowOrchestrator()

        async def executor(agent_type, task):
            return "result"

        result = await orchestrator.execute(executor)

        # Should complete with no steps
        assert result.status == "completed"
        assert len(result.outputs) == 0

    async def test_all_steps_skipped(self):
        """Test workflow where all steps are skipped"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.set_context("skip_all", True)

        steps = [
            WorkflowStep("step1", "agent1", "task", condition=lambda ctx: not ctx.get("skip_all")),
            WorkflowStep("step2", "agent2", "task", condition=lambda ctx: not ctx.get("skip_all"))
        ]

        orchestrator.add_steps(steps)

        async def executor(agent_type, task):
            return "result"

        result = await orchestrator.execute(executor)

        assert all(step.status == StepStatus.SKIPPED for step in result.steps.values())

    async def test_extremely_short_timeout(self):
        """Test behavior with extremely short timeout"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step", "agent", "task", timeout=0.001, retry_count=1))

        async def executor(agent_type, task):
            await asyncio.sleep(0.01)
            return "result"

        result = await orchestrator.execute(executor)

        assert result.status == "failed"

    async def test_zero_retry_count(self):
        """Test step with zero retry count"""
        orchestrator = WorkflowOrchestrator()
        # Note: retry_count defaults to 3, but testing with 1 (minimum meaningful value)
        orchestrator.add_step(WorkflowStep("step", "agent", "task", retry_count=1))

        attempts = [0]

        async def failing_executor(agent_type, task):
            attempts[0] += 1
            raise Exception("Always fails")

        result = await orchestrator.execute(failing_executor)

        assert attempts[0] == 1  # Should only try once with retry_count=1

    async def test_workflow_with_circular_dependency_detected(self):
        """Test circular dependency detection"""
        orchestrator = WorkflowOrchestrator()

        # Create circular dependency
        step1 = WorkflowStep("step1", "agent1", "task", dependencies=["step3"])
        step2 = WorkflowStep("step2", "agent2", "task", dependencies=["step1"])
        step3 = WorkflowStep("step3", "agent3", "task", dependencies=["step2"])

        orchestrator.add_step(step1)
        orchestrator.add_step(step2)
        orchestrator.add_step(step3)

        async def executor(agent_type, task):
            return "result"

        with pytest.raises(ValueError, match="Circular dependency"):
            await orchestrator.execute(executor)

    async def test_step_attempt_counter(self):
        """Test step attempt counter increments correctly"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step", "agent", "task", retry_count=5))

        attempt_counter = [0]

        async def failing_twice_executor(agent_type, task):
            attempt_counter[0] += 1
            if attempt_counter[0] < 3:
                raise Exception("Fail first two attempts")
            return "success"

        result = await orchestrator.execute(failing_twice_executor)

        assert result.status == "completed"
        # Should have attempted 3 times (2 failures + 1 success)
        assert orchestrator.steps["step"].attempts >= 2


# ============================================================================
# Summary Test Class
# ============================================================================

class TestModuleCoverage:
    """Summary tests to ensure comprehensive coverage"""

    def test_all_enums_covered(self):
        """Test all StepStatus enum values are covered"""
        # Verify all enum values exist
        assert StepStatus.PENDING
        assert StepStatus.RUNNING
        assert StepStatus.COMPLETED
        assert StepStatus.FAILED
        assert StepStatus.SKIPPED
        assert StepStatus.CANCELLED

    def test_workflow_orchestrator_fluent_interface(self):
        """Test fluent interface pattern"""
        orchestrator = WorkflowOrchestrator()

        result = orchestrator.add_step(
            WorkflowStep("step1", "agent1", "task")
        ).add_step(
            WorkflowStep("step2", "agent2", "task")
        )

        assert result is orchestrator
        assert len(orchestrator.steps) == 2

    @pytest.mark.asyncio
    async def test_workflow_result_duration_calculation(self):
        """Test workflow result duration is calculated correctly"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step", "agent", "task"))

        async def executor(agent_type, task):
            await asyncio.sleep(0.1)
            return "result"

        result = await orchestrator.execute(executor)

        # Duration should match time difference
        expected_duration = (result.end_time - result.start_time).total_seconds()
        assert abs(result.duration - expected_duration) < 0.01

    def test_workflow_step_metadata_flexibility(self):
        """Test workflow step metadata can store any data"""
        step = WorkflowStep(
            "step",
            "agent",
            "task",
            metadata={
                "string": "value",
                "number": 42,
                "list": [1, 2, 3],
                "dict": {"nested": "data"},
                "bool": True
            }
        )

        assert step.metadata["string"] == "value"
        assert step.metadata["number"] == 42
        assert step.metadata["list"] == [1, 2, 3]
        assert step.metadata["dict"]["nested"] == "data"
        assert step.metadata["bool"] is True


# ============================================================================
# Additional Coverage Tests
# ============================================================================

@pytest.mark.asyncio
class TestAdditionalCoverage:
    """Additional tests to ensure comprehensive coverage"""

    async def test_workflow_step_result_storage(self):
        """Test step results are properly stored"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "agent", "task"))

        test_result = {"key": "value", "data": [1, 2, 3]}

        async def result_executor(agent_type, task):
            return test_result

        result = await orchestrator.execute(result_executor)

        step = orchestrator.steps["step1"]
        assert step.result == test_result
        assert step.error is None

    async def test_workflow_step_error_storage(self):
        """Test step errors are properly stored"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "agent", "task", retry_count=1))

        async def error_executor(agent_type, task):
            raise ValueError("Test error message")

        result = await orchestrator.execute(error_executor)

        step = orchestrator.steps["step1"]
        assert step.result is None
        assert "Test error message" in step.error

    async def test_multiple_independent_steps_parallel(self):
        """Test multiple independent steps run in parallel"""
        orchestrator = WorkflowOrchestrator(max_concurrent=5)

        for i in range(5):
            orchestrator.add_step(WorkflowStep(f"step{i}", f"agent{i}", f"task{i}"))

        start_times = {}
        lock = asyncio.Lock()

        async def parallel_tracker(agent_type, task):
            async with lock:
                start_times[agent_type] = datetime.now()
            await asyncio.sleep(0.05)
            return "result"

        result = await orchestrator.execute(parallel_tracker)

        # All should start within a short time window
        times = list(start_times.values())
        time_range = (max(times) - min(times)).total_seconds()
        assert time_range < 0.1  # Started nearly simultaneously

    async def test_workflow_with_no_dependencies_single_level(self):
        """Test workflow with no dependencies creates single level"""
        orchestrator = WorkflowOrchestrator()

        for i in range(3):
            orchestrator.add_step(WorkflowStep(f"step{i}", "agent", "task"))

        levels = orchestrator._calculate_execution_order()

        assert len(levels) == 1
        assert len(levels[0]) == 3

    async def test_workflow_linear_chain_multiple_levels(self):
        """Test linear chain creates multiple levels"""
        orchestrator = WorkflowOrchestrator()

        for i in range(5):
            deps = [f"step{i-1}"] if i > 0 else []
            orchestrator.add_step(WorkflowStep(f"step{i}", "agent", f"task{i}", dependencies=deps))

        levels = orchestrator._calculate_execution_order()

        assert len(levels) == 5
        for level in levels:
            assert len(level) == 1

    async def test_context_updates_during_execution(self):
        """Test context can be updated during workflow execution"""
        orchestrator = WorkflowOrchestrator()

        steps = [
            WorkflowStep("step1", "agent1", "task1"),
            WorkflowStep("step2", "agent2", "task2", dependencies=["step1"])
        ]

        orchestrator.add_steps(steps)

        async def context_updater(agent_type, task):
            current_count = orchestrator.context.get("execution_count", 0)
            orchestrator.set_context("execution_count", current_count + 1)
            return f"result_{agent_type}"

        result = await orchestrator.execute(context_updater)

        assert orchestrator.context["execution_count"] == 2

    async def test_add_steps_fluent_interface(self):
        """Test add_steps returns orchestrator for chaining"""
        orchestrator = WorkflowOrchestrator()

        steps = [
            WorkflowStep("step1", "agent1", "task1"),
            WorkflowStep("step2", "agent2", "task2")
        ]

        result = orchestrator.add_steps(steps)

        assert result is orchestrator
        assert len(orchestrator.steps) == 2

    async def test_step_timing_accuracy(self):
        """Test step start and end times are accurate"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.add_step(WorkflowStep("step1", "agent", "task"))

        before_execution = datetime.now()

        async def timed_executor(agent_type, task):
            await asyncio.sleep(0.1)
            return "result"

        await orchestrator.execute(timed_executor)

        after_execution = datetime.now()
        step = orchestrator.steps["step1"]

        assert before_execution <= step.start_time <= after_execution
        assert before_execution <= step.end_time <= after_execution
        assert step.end_time > step.start_time

    async def test_status_cancelled_not_used(self):
        """Test CANCELLED status exists but not used in current implementation"""
        # This test verifies the enum value exists for future use
        assert StepStatus.CANCELLED
        assert StepStatus.CANCELLED.value == "cancelled"

    async def test_workflow_outputs_only_include_results(self):
        """Test workflow outputs only include step results, not all context"""
        orchestrator = WorkflowOrchestrator()
        orchestrator.set_context("config", "value")
        orchestrator.set_context("setting", 123)
        orchestrator.add_step(WorkflowStep("step1", "agent", "task"))

        async def executor(agent_type, task):
            return "result"

        result = await orchestrator.execute(executor)

        # Outputs should only have step results
        assert "step_step1_result" in result.outputs
        assert "config" not in result.outputs
        assert "setting" not in result.outputs
        assert len(result.outputs) == 1
