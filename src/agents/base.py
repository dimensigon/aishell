"""
Base Agent Class and Core Types for AIShell Agentic Workflows

This module provides the foundational abstract base class for all agentic
workflows, along with core enumerations and dataclasses for agent operation.

Classes:
    AgentState: Enumeration of agent execution states
    AgentCapability: Enumeration of agent capabilities
    AgentConfig: Configuration dataclass for agent instances
    TaskContext: Context dataclass for task execution
    TaskResult: Result dataclass for completed tasks
    BaseAgent: Abstract base class for all agents

The BaseAgent class provides:
- Tool-based execution framework
- State management integration
- LLM-powered reasoning capabilities
- Safety validation mechanisms
- Checkpoint and recovery support
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
import asyncio


class AgentState(Enum):
    """
    Agent execution states

    Represents the current state of an agent during workflow execution.
    Agents transition through these states during their lifecycle.

    States:
        IDLE: Agent is ready but not executing
        PLANNING: Agent is creating an execution plan
        EXECUTING: Agent is executing planned steps
        WAITING_APPROVAL: Agent is waiting for human approval
        PAUSED: Agent execution is temporarily paused
        COMPLETED: Agent has successfully completed execution
        FAILED: Agent execution has failed
    """
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentCapability(Enum):
    """
    Agent capabilities for tool selection

    Defines the capabilities that an agent may possess, which determines
    what tools it can access and what operations it can perform.

    Capabilities:
        DATABASE_READ: Read-only database operations
        DATABASE_WRITE: Database write/update operations
        DATABASE_DDL: Database schema modification (CREATE, ALTER, DROP)
        FILE_READ: File system read operations
        FILE_WRITE: File system write operations
        BACKUP_CREATE: Database backup creation
        BACKUP_RESTORE: Database backup restoration
        SCHEMA_ANALYZE: Schema analysis and inspection
        SCHEMA_MODIFY: Schema modification operations
        QUERY_OPTIMIZE: Query optimization and analysis
        INDEX_MANAGE: Index creation and management
    """
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    DATABASE_DDL = "database_ddl"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    SCHEMA_ANALYZE = "schema_analyze"
    SCHEMA_MODIFY = "schema_modify"
    QUERY_OPTIMIZE = "query_optimize"
    INDEX_MANAGE = "index_manage"


@dataclass
class AgentConfig:
    """
    Agent configuration

    Contains all configuration parameters for an agent instance.

    Attributes:
        agent_id: Unique identifier for the agent instance
        agent_type: Type of agent (e.g., 'backup', 'migration', 'optimizer')
        capabilities: List of capabilities this agent possesses
        llm_config: LLM configuration parameters (model, temperature, etc.)
        safety_level: Safety level ('strict', 'moderate', 'permissive')
        max_retries: Maximum number of retry attempts for failed operations
        timeout_seconds: Maximum execution time in seconds
    """
    agent_id: str
    agent_type: str
    capabilities: List[AgentCapability]
    llm_config: Dict[str, Any]
    safety_level: str = "moderate"  # strict, moderate, permissive
    max_retries: int = 3
    timeout_seconds: int = 300


@dataclass
class TaskContext:
    """
    Context for agent task execution

    Provides all necessary context information for an agent to execute a task.

    Attributes:
        task_id: Unique identifier for the task
        task_description: Natural language description of the task
        input_data: Input parameters and data for the task
        database_config: Database connection configuration (optional)
        workflow_id: Parent workflow identifier (optional)
        parent_task_id: Parent task identifier for subtasks (optional)
        metadata: Additional metadata for the task (optional)
    """
    task_id: str
    task_description: str
    input_data: Dict[str, Any]
    database_config: Optional[Dict[str, Any]] = None
    workflow_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TaskResult:
    """
    Result of agent task execution

    Contains all information about the execution of a task, including
    status, outputs, actions taken, and any errors encountered.

    Attributes:
        task_id: Identifier of the executed task
        agent_id: Identifier of the agent that executed the task
        status: Execution status ('success', 'failure', 'requires_approval')
        output_data: Output data and results from the task
        actions_taken: List of actions performed during execution
        reasoning: Natural language explanation of the execution
        execution_time: Total execution time in seconds
        checkpoints: List of checkpoint identifiers created during execution
        error: Error message if execution failed (optional)
    """
    task_id: str
    agent_id: str
    status: str  # success, failure, requires_approval
    output_data: Dict[str, Any]
    actions_taken: List[Dict[str, Any]]
    reasoning: str
    execution_time: float
    checkpoints: List[str]
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Base class for all agentic workflows

    Provides core functionality for autonomous agent execution including:
    - Tool-based execution with validated tools
    - State management and persistence
    - LLM-powered reasoning and planning
    - Safety validation and approval workflows
    - Checkpoint creation and recovery support

    All concrete agent implementations must inherit from this class and
    implement the abstract methods: plan(), execute_step(), and validate_safety().

    Attributes:
        config: Agent configuration
        llm_manager: LLM manager for reasoning and planning
        tool_registry: Registry of available tools
        state_manager: State manager for checkpointing
        state: Current agent execution state
        current_task: Currently executing task context
        execution_history: History of completed task results

    Example:
        class BackupAgent(BaseAgent):
            async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
                # Create execution plan
                return [{'tool': 'backup_database_full', 'params': {...}}]

            async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
                # Execute a step using tool registry
                tool = self.tool_registry.get_tool(step['tool'])
                return await tool.execute(step['params'], context)

            def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
                # Validate step safety
                return {'requires_approval': False, 'safe': True}
    """

    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None,
                 llm_manager=None, tool_registry=None, state_manager=None) -> None:
        """
        Initialize the base agent

        Args:
            agent_id: Unique agent identifier (for simple initialization)
            config: Agent configuration (can be dict or AgentConfig)
            llm_manager: LLM manager instance for reasoning
            tool_registry: Tool registry instance for tool access
            state_manager: State manager instance for checkpointing
        """
        # Support both simple and complex initialization
        if isinstance(config, AgentConfig):
            self.config = config
        elif isinstance(config, dict):
            # Create simple config from dict
            self.config = type('SimpleConfig', (), {
                'agent_id': agent_id or config.get('agent_id', 'agent'),
                'agent_type': config.get('agent_type', 'base'),
                'capabilities': config.get('capabilities', []),
                'llm_config': config.get('llm_config', {}),
                'safety_level': config.get('safety_level', 'moderate'),
                'max_retries': config.get('max_retries', 3),
                'timeout_seconds': config.get('timeout_seconds', 300)
            })()
        elif agent_id:
            # Create minimal config from agent_id
            self.config = type('SimpleConfig', (), {
                'agent_id': agent_id,
                'agent_type': 'base',
                'capabilities': [],
                'llm_config': {},
                'safety_level': 'moderate',
                'max_retries': 3,
                'timeout_seconds': 300
            })()
        else:
            raise ValueError("Must provide either agent_id or config")

        self.agent_id = self.config.agent_id
        self.llm_manager = llm_manager
        self.tool_registry = tool_registry
        self.state_manager = state_manager

        self.state = AgentState.IDLE
        self.current_task: Optional[TaskContext] = None
        self.execution_history: List[TaskResult] = []

    @abstractmethod
    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create execution plan for task

        This method must be implemented by concrete agent classes to analyze
        a task and create a detailed execution plan consisting of discrete steps.

        Each step should specify:
        - tool: The name of the tool to use
        - params: Parameters for the tool execution
        - rationale: Explanation of why this step is needed (optional)

        Args:
            task: Task context containing task description and input data

        Returns:
            List of planned steps, where each step is a dictionary containing
            tool name, parameters, and optional metadata

        Raises:
            NotImplementedError: If not implemented by subclass

        Example:
            [
                {
                    'tool': 'backup_database_full',
                    'params': {
                        'database': 'production',
                        'destination': '/backups/prod.sql.gz',
                        'compression': True
                    },
                    'rationale': 'Create backup before migration'
                },
                {
                    'tool': 'execute_migration',
                    'params': {'migration_sql': '...'},
                    'rationale': 'Apply schema changes'
                }
            ]
        """
        pass

    @abstractmethod
    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single planned step

        This method must be implemented by concrete agent classes to execute
        one step from the execution plan. The implementation should:
        1. Retrieve the appropriate tool from the tool registry
        2. Validate tool parameters
        3. Execute the tool with proper error handling
        4. Return the execution result

        Args:
            step: Step definition from the execution plan, containing
                  tool name and parameters

        Returns:
            Step execution result containing outputs, status, and any
            relevant metadata

        Raises:
            NotImplementedError: If not implemented by subclass
            Exception: If step execution fails

        Example:
            step = {
                'tool': 'backup_database_full',
                'params': {'database': 'prod', 'destination': '/backup.sql.gz'}
            }
            result = await self.execute_step(step)
            # result = {
            #     'backup_path': '/backup.sql.gz',
            #     'size_bytes': 1024000,
            #     'duration_seconds': 45.2
            # }
        """
        pass

    @abstractmethod
    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate safety of planned step

        This method must be implemented by concrete agent classes to assess
        the safety and risk level of a planned step before execution.

        The validation should check:
        - Tool risk level
        - Operation destructiveness
        - Data modification impact
        - Agent safety level compatibility

        Args:
            step: Step definition to validate

        Returns:
            Validation result dictionary containing:
            - requires_approval: Boolean indicating if approval is needed
            - safe: Boolean indicating if step is safe to execute
            - risk_level: Risk level assessment
            - risks: List of identified risks (optional)
            - mitigations: List of risk mitigations (optional)

        Raises:
            NotImplementedError: If not implemented by subclass

        Example:
            validation = self.validate_safety(step)
            # validation = {
            #     'requires_approval': True,
            #     'safe': True,
            #     'risk_level': 'high',
            #     'risks': ['Schema modification', 'Data loss possible'],
            #     'mitigations': ['Backup created', 'Rollback script ready']
            # }
        """
        pass

    async def run(self, task: TaskContext) -> TaskResult:
        """
        Main execution loop

        Orchestrates the complete task execution process:
        1. Plan task into discrete steps using plan()
        2. Validate each step's safety using validate_safety()
        3. Execute steps sequentially using execute_step()
        4. Handle approval requests for risky operations
        5. Create checkpoints after each step
        6. Aggregate results and return final result

        This is a concrete method that implements the standard execution
        flow for all agents. Subclasses should not override this method
        unless they need significantly different execution logic.

        Args:
            task: Task context to execute

        Returns:
            TaskResult containing execution status, outputs, actions taken,
            reasoning, and any errors

        Example:
            task = TaskContext(
                task_id="backup_001",
                task_description="Create production backup",
                input_data={'backup_type': 'full', 'destination': '/backups'}
            )
            result = await agent.run(task)
            print(f"Status: {result.status}")
            print(f"Actions: {len(result.actions_taken)}")
        """
        self.current_task = task
        self.state = AgentState.PLANNING

        actions_taken = []

        try:
            # Create execution plan
            plan = await self.plan(task)
            await self.state_manager.save_checkpoint(
                task.task_id, "plan_created", {"plan": plan}
            )

            # Execute steps
            self.state = AgentState.EXECUTING

            for i, step in enumerate(plan):
                # Validate safety
                validation = self.validate_safety(step)

                if validation['requires_approval']:
                    self.state = AgentState.WAITING_APPROVAL
                    approval = await self._request_approval(step, validation)

                    if not approval['approved']:
                        raise Exception(f"Step {i} rejected: {approval['reason']}")

                # Execute step
                result = await self.execute_step(step)
                actions_taken.append({
                    'step_index': i,
                    'step': step,
                    'result': result
                })

                # Checkpoint after each step
                await self.state_manager.save_checkpoint(
                    task.task_id, f"step_{i}_completed", result
                )

            # Complete
            self.state = AgentState.COMPLETED
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.config.agent_id,
                status="success",
                output_data=self._aggregate_results(actions_taken),
                actions_taken=actions_taken,
                reasoning=await self._generate_reasoning(plan, actions_taken),
                execution_time=0.0,  # Calculated by orchestrator
                checkpoints=await self.state_manager.get_checkpoints(task.task_id)
            )

        except Exception as e:
            self.state = AgentState.FAILED
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.config.agent_id,
                status="failure",
                output_data={},
                actions_taken=actions_taken,
                reasoning=str(e),
                execution_time=0.0,
                checkpoints=[],
                error=str(e)
            )

    async def _request_approval(self, step: Dict[str, Any],
                               validation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request human approval for risky step

        This method delegates to an approval system (to be implemented)
        to request user approval for operations that are deemed risky
        based on the safety validation.

        Args:
            step: Step definition requiring approval
            validation: Safety validation result

        Returns:
            Approval response containing:
            - approved: Boolean indicating approval status
            - reason: Explanation for approval/rejection
            - approver: Identifier of the approver
            - timestamp: Approval timestamp

        Note:
            Current implementation is a placeholder. Concrete implementation
            will be added when the approval system is integrated.
        """
        # Implementation delegates to approval system
        # This will be implemented when approval system is integrated
        return {
            'approved': False,
            'reason': 'Approval system not yet implemented',
            'approver': 'system',
            'timestamp': None
        }

    def _aggregate_results(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results from all actions

        Combines the results from all executed steps into a single
        output dictionary. This default implementation provides basic
        aggregation. Subclasses can override this method to provide
        more sophisticated result aggregation.

        Args:
            actions: List of action dictionaries with step results

        Returns:
            Aggregated output data dictionary

        Example:
            actions = [
                {'step_index': 0, 'result': {'backup_path': '/backup.sql'}},
                {'step_index': 1, 'result': {'migration_status': 'success'}}
            ]
            result = self._aggregate_results(actions)
            # result = {
            #     'actions_count': 2,
            #     'backup_path': '/backup.sql',
            #     'migration_status': 'success'
            # }
        """
        # Default implementation - can be overridden by subclasses
        aggregated = {'actions_count': len(actions)}

        # Merge all result data
        for action in actions:
            if 'result' in action and isinstance(action['result'], dict):
                aggregated.update(action['result'])

        return aggregated

    async def _generate_reasoning(self, plan: List[Dict[str, Any]],
                                  actions: List[Dict[str, Any]]) -> str:
        """
        Generate natural language reasoning for execution

        Uses the LLM to create a human-readable explanation of what
        was done during task execution and why. This provides transparency
        and auditability of agent actions.

        Args:
            plan: The execution plan that was created
            actions: The actions that were taken

        Returns:
            Natural language explanation of the execution

        Example:
            reasoning = await self._generate_reasoning(plan, actions)
            # "Created a full backup of the production database to
            #  /backups/prod.sql.gz (1.2GB), then executed schema migration
            #  to add the 'phone' column to the users table. Migration
            #  completed successfully with rollback script saved."
        """
        prompt = f"""Explain the execution of this plan:

Plan: {plan}
Actions Taken: {actions}

Provide a clear summary of what was done and why."""

        return await self.llm_manager.generate(prompt, max_tokens=200)
