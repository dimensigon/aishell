#!/usr/bin/env python3
"""
Complex Workflow Example

Demonstrates advanced agentic workflows with multi-agent coordination,
parallel execution, and distributed task management.
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Mock agent executor for demonstration
async def mock_agent_executor(agent_type: str, task: str):
    """Simulate agent execution"""
    logger.info(f"[{agent_type}] Executing: {task[:100]}...")
    await asyncio.sleep(1)  # Simulate work
    return {
        'agent_type': agent_type,
        'task': task,
        'result': f"Completed {task[:50]}...",
        'timestamp': datetime.now().isoformat()
    }


async def workflow_orchestrator_example():
    """Demonstrate workflow orchestrator"""
    from src.agents import WorkflowOrchestrator, WorkflowStep

    logger.info("=" * 60)
    logger.info("WORKFLOW ORCHESTRATOR EXAMPLE")
    logger.info("=" * 60)

    # Create workflow
    workflow = WorkflowOrchestrator(name="data_pipeline", max_concurrent=3)

    # Define workflow steps with dependencies
    steps = [
        WorkflowStep(
            name="collect_data",
            agent_type="researcher",
            task="Collect data from multiple sources",
            dependencies=[]
        ),
        WorkflowStep(
            name="validate_data",
            agent_type="coder",
            task="Validate and clean collected data",
            dependencies=["collect_data"]
        ),
        WorkflowStep(
            name="analyze_data",
            agent_type="researcher",
            task="Analyze validated data patterns",
            dependencies=["validate_data"]
        ),
        WorkflowStep(
            name="generate_report",
            agent_type="coder",
            task="Generate comprehensive analysis report",
            dependencies=["analyze_data"]
        ),
        WorkflowStep(
            name="create_visualizations",
            agent_type="coder",
            task="Create data visualizations and charts",
            dependencies=["analyze_data"]
        ),
        WorkflowStep(
            name="review_output",
            agent_type="reviewer",
            task="Review final report and visualizations",
            dependencies=["generate_report", "create_visualizations"]
        ),
    ]

    workflow.add_steps(steps)

    # Visualize workflow
    print("\n" + workflow.visualize())

    # Execute workflow
    result = await workflow.execute(mock_agent_executor, fail_fast=False)

    # Print results
    print(f"\nWorkflow Status: {result.status}")
    print(f"Duration: {result.duration:.2f}s")
    print(f"Completed Steps: {sum(1 for s in result.steps.values() if s.status.value == 'completed')}/{len(result.steps)}")

    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for error in result.errors:
            print(f"  - {error}")


async def agent_chain_example():
    """Demonstrate agent chain"""
    from src.agents import AgentChain

    logger.info("\n" + "=" * 60)
    logger.info("AGENT CHAIN EXAMPLE")
    logger.info("=" * 60)

    # Create agent chain
    chain = AgentChain(
        name="code_review_pipeline",
        initial_input="Review authentication module"
    )

    # Define sequential pipeline
    chain.then(
        "researcher",
        name="analyze_requirements",
        transform=lambda x: f"Analyze requirements for: {x}"
    ).then(
        "coder",
        name="implement_changes",
        transform=lambda x: f"Implement based on analysis: {x['result']}"
    ).then(
        "tester",
        name="run_tests",
        transform=lambda x: f"Test implementation: {x['result']}"
    ).then(
        "reviewer",
        name="final_review",
        transform=lambda x: f"Final review of: {x['result']}"
    )

    # Visualize chain
    print("\n" + chain.visualize())

    # Execute chain
    result = await chain.execute(mock_agent_executor, stop_on_error=False)

    # Print results
    print(f"\nChain Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Total Duration: {result.total_duration:.2f}s")

    for idx, link in enumerate(result.links):
        status = "✓" if link.success else "✗"
        print(f"  {idx + 1}. {status} {link.get_name()} ({link.duration:.2f}s)")
        if link.error:
            print(f"     Error: {link.error}")


async def parallel_executor_example():
    """Demonstrate parallel executor"""
    from src.agents import ParallelExecutor, ParallelTask, AggregationStrategy, TaskPriority

    logger.info("\n" + "=" * 60)
    logger.info("PARALLEL EXECUTOR EXAMPLE")
    logger.info("=" * 60)

    # Create parallel executor
    executor = ParallelExecutor(
        max_concurrent=5,
        strategy=AggregationStrategy.ALL
    )

    # Create multiple tasks with different priorities
    tasks = [
        ParallelTask(
            agent_type="researcher",
            task="Research best practices for API design",
            name="research_api",
            priority=TaskPriority.HIGH
        ),
        ParallelTask(
            agent_type="researcher",
            task="Research database optimization techniques",
            name="research_db",
            priority=TaskPriority.NORMAL
        ),
        ParallelTask(
            agent_type="coder",
            task="Implement REST API endpoints",
            name="implement_api",
            priority=TaskPriority.HIGH
        ),
        ParallelTask(
            agent_type="coder",
            task="Implement database migrations",
            name="implement_db",
            priority=TaskPriority.NORMAL
        ),
        ParallelTask(
            agent_type="tester",
            task="Create API integration tests",
            name="test_api",
            priority=TaskPriority.NORMAL
        ),
        ParallelTask(
            agent_type="tester",
            task="Create database performance tests",
            name="test_db",
            priority=TaskPriority.LOW
        ),
    ]

    executor.add_tasks(tasks)

    # Execute all tasks in parallel
    result = await executor.execute(mock_agent_executor)

    # Print results
    print(f"\nExecution Summary:")
    print(f"  Total Tasks: {result.total_tasks}")
    print(f"  Completed: {result.completed}")
    print(f"  Failed: {result.failed}")
    print(f"  Total Duration: {result.total_duration:.2f}s")
    print(f"  Avg Duration: {result.avg_duration:.2f}s")
    print(f"  Max Duration: {result.max_duration:.2f}s")
    print(f"  Min Duration: {result.min_duration:.2f}s")

    print("\nTask Results:")
    for task in result.tasks:
        status = "✓" if task.status.value == "completed" else "✗"
        print(f"  {status} {task.get_name()} ({task.duration:.2f}s, priority={task.priority.name})")


async def combined_workflow_example():
    """Demonstrate combining all orchestration patterns"""
    from src.agents import (
        WorkflowOrchestrator,
        WorkflowStep,
        ParallelExecutor,
        ParallelTask,
        TaskPriority
    )

    logger.info("\n" + "=" * 60)
    logger.info("COMBINED WORKFLOW EXAMPLE")
    logger.info("=" * 60)

    # Create main workflow
    workflow = WorkflowOrchestrator(name="full_stack_feature", max_concurrent=3)

    # Step 1: Research phase (parallel)
    async def research_phase(agent_type: str, task: str):
        executor = ParallelExecutor(max_concurrent=3)
        executor.create_task("researcher", "Research frontend patterns", priority=2)
        executor.create_task("researcher", "Research backend patterns", priority=2)
        executor.create_task("researcher", "Research testing strategies", priority=1)
        result = await executor.execute(mock_agent_executor)
        return {"research_results": len(result.results)}

    # Step 2: Implementation phase (parallel)
    async def implementation_phase(agent_type: str, task: str):
        executor = ParallelExecutor(max_concurrent=3)
        executor.create_task("coder", "Implement frontend", priority=2)
        executor.create_task("coder", "Implement backend", priority=2)
        executor.create_task("coder", "Setup CI/CD", priority=1)
        result = await executor.execute(mock_agent_executor)
        return {"implementations": len(result.results)}

    # Define workflow
    steps = [
        WorkflowStep(
            name="research",
            agent_type="coordinator",
            task="Coordinate research phase",
            dependencies=[]
        ),
        WorkflowStep(
            name="design",
            agent_type="reviewer",
            task="Design system architecture",
            dependencies=["research"]
        ),
        WorkflowStep(
            name="implement",
            agent_type="coordinator",
            task="Coordinate implementation phase",
            dependencies=["design"]
        ),
        WorkflowStep(
            name="test",
            agent_type="tester",
            task="Run comprehensive test suite",
            dependencies=["implement"]
        ),
        WorkflowStep(
            name="review",
            agent_type="reviewer",
            task="Final code review",
            dependencies=["test"]
        ),
    ]

    workflow.add_steps(steps)

    # Execute
    result = await workflow.execute(mock_agent_executor)

    print(f"\nCombined Workflow Status: {result.status}")
    print(f"Total Duration: {result.duration:.2f}s")
    print(f"Steps Completed: {sum(1 for s in result.steps.values() if s.status.value == 'completed')}/{len(result.steps)}")


async def main():
    """Run all examples"""
    try:
        # Run individual examples
        await workflow_orchestrator_example()
        await agent_chain_example()
        await parallel_executor_example()
        await combined_workflow_example()

        logger.info("\n" + "=" * 60)
        logger.info("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
