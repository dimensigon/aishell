"""
AIShell Agent Framework - Phase 12: Agentic AI Workflows

This package provides the foundational framework for autonomous AI agents
that can perform multi-step database operations with safety controls.

Core Components:
- BaseAgent: Abstract base class for all agents
- AgentState: Agent execution states
- AgentCapability: Agent capabilities for tool selection
- AgentConfig: Agent configuration dataclass
- TaskContext: Task execution context
- TaskResult: Task execution result

Usage:
    from src.agents.base import BaseAgent, AgentState, AgentCapability
    from src.agents.base import AgentConfig, TaskContext, TaskResult
"""

from src.agents.base import (
    BaseAgent,
    AgentState,
    AgentCapability,
    AgentConfig,
    TaskContext,
    TaskResult,
)
from src.agents.agent_chain import AgentChain
from src.agents.parallel_executor import (
    ParallelExecutor,
    ParallelTask,
    AggregationStrategy,
    TaskStatus,
)
from src.agents.workflow_orchestrator import WorkflowOrchestrator, WorkflowStep

__all__ = [
    "BaseAgent",
    "AgentState",
    "AgentCapability",
    "AgentConfig",
    "TaskContext",
    "TaskResult",
    "AgentChain",
    "ParallelExecutor",
    "ParallelTask",
    "AggregationStrategy",
    "TaskStatus",
    "WorkflowOrchestrator",
    "WorkflowStep",
]

__version__ = "1.0.0"
