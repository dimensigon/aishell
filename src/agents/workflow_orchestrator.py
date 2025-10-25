"""
Multi-Agent Workflow Orchestrator

Coordinates complex workflows involving multiple agents with dependencies,
conditional execution, and error recovery.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4


logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Workflow step execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""
    name: str
    agent_type: str
    task: str
    dependencies: List[str] = field(default_factory=list)
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    retry_count: int = 3
    timeout: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Runtime fields
    step_id: str = field(default_factory=lambda: str(uuid4()))
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attempts: int = 0


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    workflow_id: str
    status: str
    steps: Dict[str, WorkflowStep]
    outputs: Dict[str, Any]
    start_time: datetime
    end_time: datetime
    duration: float
    errors: List[str] = field(default_factory=list)

    def is_successful(self) -> bool:
        """Check if workflow completed successfully"""
        return self.status == "completed" and not self.errors

    def get_step_result(self, step_name: str) -> Optional[Any]:
        """Get result from specific step"""
        step = self.steps.get(step_name)
        return step.result if step else None


class WorkflowOrchestrator:
    """
    Orchestrates complex multi-agent workflows with dependency management,
    conditional execution, and error recovery.
    """

    def __init__(self, name: str = "workflow", max_concurrent: int = 5) -> None:
        self.name = name
        self.workflow_id = str(uuid4())
        self.max_concurrent = max_concurrent
        self.steps: Dict[str, WorkflowStep] = {}
        self.execution_order: List[str] = []
        self.context: Dict[str, Any] = {}

        logger.info(f"Initialized workflow orchestrator: {name} ({self.workflow_id})")

    def add_step(self, step: WorkflowStep) -> 'WorkflowOrchestrator':
        """Add a step to the workflow"""
        if step.name in self.steps:
            raise ValueError(f"Step '{step.name}' already exists in workflow")

        self.steps[step.name] = step
        logger.debug(f"Added step '{step.name}' to workflow {self.name}")
        return self

    def add_steps(self, steps: List[WorkflowStep]) -> 'WorkflowOrchestrator':
        """Add multiple steps to the workflow"""
        for step in steps:
            self.add_step(step)
        return self

    def set_context(self, key: str, value: Any) -> None:
        """Set context variable for workflow"""
        self.context[key] = value

    def _validate_workflow(self) -> None:
        """Validate workflow for circular dependencies and missing steps"""
        # Check all dependencies exist
        for step in self.steps.values():
            for dep in step.dependencies:
                if dep not in self.steps:
                    raise ValueError(
                        f"Step '{step.name}' depends on non-existent step '{dep}'"
                    )

        # Check for circular dependencies
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def has_cycle(step_name: str) -> bool:
            visited.add(step_name)
            rec_stack.add(step_name)

            step = self.steps[step_name]
            for dep in step.dependencies:
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(step_name)
            return False

        for step_name in self.steps:
            if step_name not in visited:
                if has_cycle(step_name):
                    raise ValueError(f"Circular dependency detected in workflow")

    def _calculate_execution_order(self) -> List[List[str]]:
        """Calculate execution order using topological sort with levels"""
        # Calculate in-degree for each step
        in_degree: Dict[str, int] = {name: 0 for name in self.steps}
        for step in self.steps.values():
            for dep in step.dependencies:
                in_degree[step.name] += 1

        # Group steps by level (steps with no dependencies can run in parallel)
        levels: List[List[str]] = []
        remaining = set(self.steps.keys())

        while remaining:
            # Find all steps with no remaining dependencies
            current_level = [
                name for name in remaining
                if all(dep not in remaining for dep in self.steps[name].dependencies)
            ]

            if not current_level:
                raise ValueError("Unable to resolve execution order - possible cycle")

            levels.append(current_level)
            remaining -= set(current_level)

        return levels

    async def _execute_step(
        self,
        step: WorkflowStep,
        agent_executor: Callable[[str, str], Any]
    ) -> bool:
        """Execute a single workflow step with retry logic"""
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()

        logger.info(f"Executing step '{step.name}' (agent: {step.agent_type})")

        for attempt in range(step.retry_count):
            step.attempts = attempt + 1

            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    agent_executor(step.agent_type, step.task),
                    timeout=step.timeout
                )

                step.result = result
                step.status = StepStatus.COMPLETED
                step.end_time = datetime.now()

                # Store result in context
                self.context[f"step_{step.name}_result"] = result

                logger.info(
                    f"Step '{step.name}' completed successfully "
                    f"(attempt {attempt + 1}/{step.retry_count})"
                )
                return True

            except asyncio.TimeoutError:
                error_msg = f"Step '{step.name}' timed out after {step.timeout}s"
                logger.warning(f"{error_msg} (attempt {attempt + 1}/{step.retry_count})")
                step.error = error_msg

            except Exception as e:
                error_msg = f"Step '{step.name}' failed: {str(e)}"
                logger.warning(f"{error_msg} (attempt {attempt + 1}/{step.retry_count})")
                step.error = error_msg

            if attempt < step.retry_count - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        step.status = StepStatus.FAILED
        step.end_time = datetime.now()
        logger.error(f"Step '{step.name}' failed after {step.retry_count} attempts")
        return False

    async def execute(
        self,
        agent_executor: Callable[[str, str], Any],
        fail_fast: bool = False
    ) -> WorkflowResult:
        """
        Execute the workflow

        Args:
            agent_executor: Async function that executes agent tasks
            fail_fast: If True, stop execution on first failure

        Returns:
            WorkflowResult with execution details
        """
        start_time = datetime.now()
        logger.info(f"Starting workflow execution: {self.name}")

        # Validate workflow
        self._validate_workflow()

        # Calculate execution order
        levels = self._calculate_execution_order()
        logger.debug(f"Execution plan: {len(levels)} levels")

        errors: List[str] = []

        # Execute levels
        for level_idx, level in enumerate(levels):
            logger.info(f"Executing level {level_idx + 1}/{len(levels)}: {level}")

            # Filter steps based on conditions
            steps_to_run = []
            for step_name in level:
                step = self.steps[step_name]

                if step.condition and not step.condition(self.context):
                    step.status = StepStatus.SKIPPED
                    logger.info(f"Skipping step '{step_name}' (condition not met)")
                    continue

                steps_to_run.append(step)

            # Execute steps in parallel (up to max_concurrent)
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def run_with_semaphore(step: WorkflowStep):
                async with semaphore:
                    return await self._execute_step(step, agent_executor)

            results = await asyncio.gather(
                *[run_with_semaphore(step) for step in steps_to_run],
                return_exceptions=True
            )

            # Check for failures
            for step, result in zip(steps_to_run, results):
                if isinstance(result, Exception):
                    error_msg = f"Step '{step.name}' raised exception: {result}"
                    errors.append(error_msg)
                    logger.error(error_msg)

                    if fail_fast:
                        break
                elif not result:
                    if fail_fast:
                        break

            if fail_fast and errors:
                logger.error("Stopping workflow execution (fail_fast=True)")
                break

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Determine overall status
        completed = sum(1 for s in self.steps.values() if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in self.steps.values() if s.status == StepStatus.FAILED)

        if failed > 0:
            status = "failed"
        elif completed == len(self.steps):
            status = "completed"
        else:
            status = "partial"

        result = WorkflowResult(
            workflow_id=self.workflow_id,
            status=status,
            steps=self.steps.copy(),
            outputs={
                k: v for k, v in self.context.items()
                if k.startswith("step_") and k.endswith("_result")
            },
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            errors=errors
        )

        logger.info(
            f"Workflow completed: {status} "
            f"({completed} completed, {failed} failed, {duration:.2f}s)"
        )

        return result

    def visualize(self) -> str:
        """Generate a text visualization of the workflow"""
        lines = [f"Workflow: {self.name}"]
        lines.append("=" * 50)

        levels = self._calculate_execution_order()
        for level_idx, level in enumerate(levels):
            lines.append(f"\nLevel {level_idx + 1}:")
            for step_name in level:
                step = self.steps[step_name]
                deps = ", ".join(step.dependencies) if step.dependencies else "none"
                lines.append(f"  - {step_name} ({step.agent_type})")
                lines.append(f"    Dependencies: {deps}")
                if step.condition:
                    lines.append(f"    Conditional: yes")

        return "\n".join(lines)
