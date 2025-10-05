"""
CoordinatorAgent - Multi-Agent Workflow Orchestration

This module provides the CoordinatorAgent class for coordinating complex workflows
that require multiple specialized agents working together.

The CoordinatorAgent:
- Decomposes high-level tasks into subtasks
- Identifies required specialized agents
- Manages dependencies between subtasks
- Delegates work to specialized agents
- Aggregates results from all agents

Classes:
    CoordinatorAgent: Agent for multi-agent workflow coordination
"""

import json
from typing import Dict, Any, List, Optional
from src.agents.base import (
    BaseAgent,
    AgentConfig,
    TaskContext,
    TaskResult,
    AgentCapability
)


class CoordinatorAgent(BaseAgent):
    """
    Multi-agent workflow coordinator

    The CoordinatorAgent orchestrates complex workflows by decomposing high-level
    tasks into subtasks and delegating them to specialized agents. It manages
    dependencies, execution order, and result aggregation across multiple agents.

    Unlike specialized agents, the CoordinatorAgent doesn't directly execute tools.
    Instead, it uses LLM-powered planning to identify required agents and create
    a dependency graph for execution.

    Coordination Patterns:
    - Sequential: Execute agents one after another
    - Parallel: Execute multiple agents concurrently
    - Conditional: Branch based on results

    Planning Logic:
    - Parse high-level task description
    - Identify required specialized agents (BackupAgent, MigrationAgent, OptimizerAgent)
    - Create dependency graph
    - Determine execution order

    Delegation:
    - Spawn specialized agents
    - Pass context and data between agents
    - Aggregate results from all agents

    Safety Validation:
    - Risk = highest risk of delegated agents
    - Approval required if any sub-agent requires approval

    Example:
        config = AgentConfig(
            agent_id="coordinator_001",
            agent_type="coordinator",
            capabilities=[],  # Coordinator uses other agents
            llm_config={"model": "llama2", "temperature": 0.3},
            safety_level="strict"
        )

        agent = CoordinatorAgent(config, llm_manager, tool_registry, state_manager)

        task = TaskContext(
            task_id="complex_workflow_001",
            task_description='''
                Prepare production database for new feature deployment:
                1. Create backup
                2. Apply schema migration
                3. Optimize related queries
                4. Verify data integrity
            ''',
            input_data={
                'feature': 'user_notifications',
                'migration_scripts': [...],
                'affected_queries': [...]
            },
            database_config={'database': 'production', 'host': 'localhost'}
        )

        result = await agent.run(task)
    """

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create multi-agent execution plan for complex task

        Uses LLM to decompose a complex task into subtasks that can be
        delegated to specialized agents. The plan includes agent type,
        task description, input data, and dependencies for each subtask.

        The LLM analyzes the task description and identifies:
        - Which specialized agents are needed (BackupAgent, MigrationAgent, OptimizerAgent)
        - What each agent should do
        - Dependencies between subtasks
        - Data flow between agents

        Args:
            task: TaskContext containing:
                - task_description: High-level workflow description
                - input_data: Workflow input parameters
                - database_config: Database connection configuration

        Returns:
            List of subtask definitions, each containing:
            - agent_type: Type of agent to delegate to
            - task_description: Specific task for the agent
            - input_data: Data to pass to the agent
            - dependencies: List of prior subtask indices this depends on

        Example:
            task = TaskContext(
                task_id="deploy_001",
                task_description="Prepare database for feature deployment",
                input_data={'migration_sql': '...', 'queries': [...]}
            )

            plan = await coordinator.plan(task)
            # [
            #     {
            #         'agent_type': 'backup',
            #         'task_description': 'Create full backup before migration',
            #         'input_data': {'backup_type': 'full', 'destination': '/backups'},
            #         'dependencies': []
            #     },
            #     {
            #         'agent_type': 'migration',
            #         'task_description': 'Apply schema migration',
            #         'input_data': {'migration_sql': '...'},
            #         'dependencies': [0]
            #     },
            #     {
            #         'agent_type': 'optimizer',
            #         'task_description': 'Optimize queries for new schema',
            #         'input_data': {'queries': [...]},
            #         'dependencies': [1]
            #     }
            # ]
        """
        # Use LLM to decompose complex task into subtasks
        decomposition_prompt = f"""
Decompose this database task into subtasks for specialized agents.

Task: {task.task_description}

Input Data: {json.dumps(task.input_data, indent=2)}

Available Agents:
- BackupAgent: Database backup and restore operations
  Capabilities: Full backups, incremental backups, backup validation, restoration
  Use when: Need to backup data, restore from backup, ensure data safety

- MigrationAgent: Schema migrations and database structure changes
  Capabilities: Schema analysis, migration planning, DDL execution, rollback preparation
  Use when: Need to modify database schema, add/remove tables/columns, change constraints

- OptimizerAgent: Query and database performance optimization
  Capabilities: Query analysis, index recommendations, statistics updates, performance tuning
  Use when: Need to improve query performance, add indexes, optimize slow queries

Instructions:
1. Analyze the task and determine which agents are needed
2. Create a subtask for each agent with specific instructions
3. Identify dependencies between subtasks (e.g., backup before migration)
4. Ensure data flows correctly between agents

Return JSON with subtasks array:
{{
    "subtasks": [
        {{
            "agent_type": "backup|migration|optimizer",
            "task_description": "Specific task description for this agent",
            "input_data": {{"key": "value"}},
            "dependencies": [0, 1],  // Indices of subtasks this depends on
            "rationale": "Why this agent is needed"
        }}
    ]
}}

Important:
- Use agent_type: "backup", "migration", or "optimizer"
- Include all necessary parameters in input_data
- Set dependencies to [] if no dependencies
- First subtask should usually be a backup for safety
- Ensure dependencies form a valid execution order (no cycles)
"""

        # Generate decomposition using LLM
        response = await self.llm_manager.generate(
            decomposition_prompt,
            max_tokens=1500
        )

        # Parse LLM response
        try:
            decomposition = json.loads(response)
            subtasks = decomposition.get('subtasks', [])

            # Validate subtasks structure
            for i, subtask in enumerate(subtasks):
                if 'agent_type' not in subtask:
                    raise ValueError(f"Subtask {i} missing 'agent_type'")
                if 'task_description' not in subtask:
                    raise ValueError(f"Subtask {i} missing 'task_description'")
                if 'input_data' not in subtask:
                    subtask['input_data'] = {}
                if 'dependencies' not in subtask:
                    subtask['dependencies'] = []

            return subtasks

        except json.JSONDecodeError as e:
            # Fallback: Create simple sequential plan
            return self._create_fallback_plan(task)

    def _create_fallback_plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create fallback plan when LLM decomposition fails

        Creates a conservative sequential plan based on task keywords.
        Always includes backup first for safety.

        Args:
            task: Task context

        Returns:
            Simple sequential plan with backup, migration, and/or optimization
        """
        task_lower = task.task_description.lower()
        subtasks = []

        # Always start with backup for safety
        subtasks.append({
            'agent_type': 'backup',
            'task_description': 'Create safety backup before operations',
            'input_data': {
                'backup_type': 'full',
                'destination': task.input_data.get('backup_destination', '/backups')
            },
            'dependencies': []
        })

        # Check for migration keywords
        if any(keyword in task_lower for keyword in ['migration', 'schema', 'alter', 'modify', 'add column']):
            subtasks.append({
                'agent_type': 'migration',
                'task_description': 'Execute schema migration',
                'input_data': task.input_data,
                'dependencies': [0]  # Depends on backup
            })

        # Check for optimization keywords
        if any(keyword in task_lower for keyword in ['optimize', 'performance', 'index', 'slow query']):
            subtasks.append({
                'agent_type': 'optimizer',
                'task_description': 'Optimize database performance',
                'input_data': task.input_data,
                'dependencies': [len(subtasks) - 1] if len(subtasks) > 1 else [0]
            })

        return subtasks

    def _identify_required_agents(self, task_description: str) -> List[str]:
        """
        Identify required specialized agents based on task description

        Uses LLM to analyze the task description and determine which
        specialized agents are needed to complete the workflow.

        Args:
            task_description: High-level task description

        Returns:
            List of agent type identifiers

        Example:
            agents = self._identify_required_agents(
                "Create backup, apply migration, optimize queries"
            )
            # ['backup', 'migration', 'optimizer']
        """
        prompt = f"""
Analyze this task and identify which specialized agents are needed.

Task: {task_description}

Available Agents:
- backup: For database backup and restore operations
- migration: For schema changes and migrations
- optimizer: For query and performance optimization

Return JSON array of required agent types:
{{"agents": ["backup", "migration", "optimizer"]}}

Only include agents that are actually needed for this task.
"""

        response = self.llm_manager.generate(prompt, max_tokens=100)

        try:
            result = json.loads(response)
            return result.get('agents', [])
        except:
            # Fallback: return all agents
            return ['backup', 'migration', 'optimizer']

    def _create_dependency_graph(self, agents: List[str]) -> Dict[str, List[str]]:
        """
        Create dependency graph for agent execution order

        Builds a directed acyclic graph (DAG) representing dependencies
        between agents. This determines the execution order.

        Default dependencies:
        - backup: No dependencies (runs first)
        - migration: Depends on backup
        - optimizer: Depends on migration (or backup if no migration)

        Args:
            agents: List of agent type identifiers

        Returns:
            Dependency graph as adjacency list

        Example:
            graph = self._create_dependency_graph(['backup', 'migration', 'optimizer'])
            # {
            #     'backup': [],
            #     'migration': ['backup'],
            #     'optimizer': ['migration']
            # }
        """
        graph = {}

        for agent in agents:
            if agent == 'backup':
                # Backup has no dependencies, runs first
                graph[agent] = []
            elif agent == 'migration':
                # Migration depends on backup if present
                if 'backup' in agents:
                    graph[agent] = ['backup']
                else:
                    graph[agent] = []
            elif agent == 'optimizer':
                # Optimizer depends on migration if present, otherwise backup
                if 'migration' in agents:
                    graph[agent] = ['migration']
                elif 'backup' in agents:
                    graph[agent] = ['backup']
                else:
                    graph[agent] = []
            else:
                # Unknown agent - no dependencies
                graph[agent] = []

        return graph

    async def _delegate_to_agent(self, agent_type: str, task: TaskContext) -> TaskResult:
        """
        Delegate task to specialized agent

        Creates and executes a specialized agent to handle a subtask.
        This is a placeholder implementation - actual delegation will be
        handled by the WorkflowOrchestrator.

        Args:
            agent_type: Type of agent to create ('backup', 'migration', 'optimizer')
            task: Task context for the subtask

        Returns:
            Task result from the specialized agent

        Raises:
            NotImplementedError: This is a placeholder for orchestrator integration

        Note:
            In the actual implementation, this method will be replaced by
            orchestrator-level delegation. The CoordinatorAgent's plan()
            method provides the subtasks, and the orchestrator creates and
            executes the specialized agents.
        """
        # This is a placeholder - actual delegation happens at orchestrator level
        raise NotImplementedError(
            "Agent delegation is handled by WorkflowOrchestrator. "
            "CoordinatorAgent provides the execution plan via plan() method."
        )

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute coordination step (delegates to specialized agents)

        For CoordinatorAgent, each step represents delegating to a specialized
        agent. The actual execution is handled by the WorkflowOrchestrator which
        creates the appropriate specialized agent and runs it.

        This method returns metadata about the delegation rather than executing
        tools directly.

        Args:
            step: Step definition containing:
                - agent_type: Type of agent to delegate to
                - task_description: Task for the agent
                - input_data: Data to pass to the agent
                - dependencies: Subtask dependencies

        Returns:
            Delegation metadata (actual execution by orchestrator)

        Example:
            step = {
                'agent_type': 'backup',
                'task_description': 'Create full backup',
                'input_data': {'backup_type': 'full'},
                'dependencies': []
            }
            result = await self.execute_step(step)
            # {
            #     'delegation': 'backup',
            #     'task_description': 'Create full backup',
            #     'status': 'delegated'
            # }
        """
        # CoordinatorAgent doesn't execute tools directly
        # It delegates to specialized agents via the orchestrator
        # Return delegation metadata
        return {
            'delegation': step.get('agent_type'),
            'task_description': step.get('task_description'),
            'input_data': step.get('input_data', {}),
            'dependencies': step.get('dependencies', []),
            'status': 'delegated'
        }

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate safety of delegation step

        For CoordinatorAgent, safety validation aggregates the safety
        requirements of all delegated agents. The risk level is the
        highest risk among all delegated subtasks, and approval is
        required if any subtask requires approval.

        Safety Rules:
        - Risk level = max(all delegated agent risks)
        - Requires approval = any delegated agent requires approval
        - BackupAgent: Low risk
        - MigrationAgent: Critical risk, always requires approval
        - OptimizerAgent: Medium risk, may require approval

        Args:
            step: Step definition containing agent delegation

        Returns:
            Validation result containing:
            - requires_approval: True if any delegated agent needs approval
            - safe: Always True (delegates to safe agents)
            - risk_level: Highest risk level of delegated agents
            - risks: Aggregated risks from all agents
            - mitigations: Aggregated mitigations

        Example:
            step = {'agent_type': 'migration', 'task_description': '...'}
            validation = self.validate_safety(step)
            # {
            #     'requires_approval': True,
            #     'safe': True,
            #     'risk_level': 'critical',
            #     'risks': ['Schema modification', 'Potential data loss'],
            #     'mitigations': ['Backup created first', 'Rollback script ready']
            # }
        """
        agent_type = step.get('agent_type')

        # Define risk levels for each agent type
        agent_risk_levels = {
            'backup': {
                'risk_level': 'low',
                'requires_approval': False,
                'risks': ['Disk space consumption'],
                'mitigations': ['Backup validation performed']
            },
            'migration': {
                'risk_level': 'critical',
                'requires_approval': True,
                'risks': [
                    'Schema modification',
                    'Potential data loss',
                    'Service disruption'
                ],
                'mitigations': [
                    'Backup created before migration',
                    'Rollback script generated',
                    'Migration validated before execution'
                ]
            },
            'optimizer': {
                'risk_level': 'medium',
                'requires_approval': False,  # Unless creating indexes on large tables
                'risks': [
                    'Index creation may lock tables',
                    'Performance impact during optimization'
                ],
                'mitigations': [
                    'Analysis before changes',
                    'Estimated improvement calculated'
                ]
            }
        }

        # Get validation for this agent type
        if agent_type in agent_risk_levels:
            validation = agent_risk_levels[agent_type].copy()
            validation['safe'] = True

            # Override approval requirement based on safety level
            if self.config.safety_level == 'strict':
                if validation['risk_level'] in ['high', 'critical']:
                    validation['requires_approval'] = True
            elif self.config.safety_level == 'moderate':
                if validation['risk_level'] == 'critical':
                    validation['requires_approval'] = True

            return validation

        # Unknown agent type - require approval for safety
        return {
            'requires_approval': True,
            'safe': True,
            'risk_level': 'unknown',
            'risks': [f'Unknown agent type: {agent_type}'],
            'mitigations': ['Manual review required']
        }

    def _aggregate_results(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results from all delegated agents

        Combines results from all specialized agents into a unified
        workflow result. Includes summary statistics and delegation metadata.

        Args:
            actions: List of delegation actions and their results

        Returns:
            Aggregated workflow results

        Example:
            aggregated = {
                'actions_count': 3,
                'agents_used': ['backup', 'migration', 'optimizer'],
                'delegations': [
                    {'agent': 'backup', 'status': 'completed'},
                    {'agent': 'migration', 'status': 'completed'},
                    {'agent': 'optimizer', 'status': 'completed'}
                ],
                'workflow_status': 'completed',
                'total_agents': 3
            }
        """
        aggregated = {
            'actions_count': len(actions),
            'agents_used': [],
            'delegations': [],
            'workflow_status': 'completed'
        }

        # Collect delegation information
        for action in actions:
            if 'result' in action and isinstance(action['result'], dict):
                result = action['result']

                # Track which agents were used
                if 'delegation' in result:
                    agent_type = result['delegation']
                    if agent_type not in aggregated['agents_used']:
                        aggregated['agents_used'].append(agent_type)

                    # Add delegation summary
                    aggregated['delegations'].append({
                        'agent': agent_type,
                        'task': result.get('task_description'),
                        'status': result.get('status', 'unknown')
                    })

                # Merge other result data
                for key, value in result.items():
                    if key not in ['delegation', 'task_description', 'status', 'input_data', 'dependencies']:
                        # Avoid overwriting existing keys, prefix with agent type
                        prefixed_key = f"{result.get('delegation', 'unknown')}_{key}"
                        aggregated[prefixed_key] = value

        # Add summary statistics
        aggregated['total_agents'] = len(aggregated['agents_used'])

        # Determine overall workflow status
        delegation_statuses = [d['status'] for d in aggregated['delegations']]
        if all(s == 'delegated' or s == 'completed' for s in delegation_statuses):
            aggregated['workflow_status'] = 'completed'
        elif any(s == 'failed' for s in delegation_statuses):
            aggregated['workflow_status'] = 'failed'
        else:
            aggregated['workflow_status'] = 'in_progress'

        return aggregated
