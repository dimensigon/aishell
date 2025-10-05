"""
OptimizerAgent for Phase 12: Agentic AI Workflows

This module provides the OptimizerAgent class for intelligent query and database
optimization workflows. The agent performs query performance analysis, index
recommendations, and statistics updates with safety validation.

Classes:
    OptimizerAgent: Agent for database query and performance optimization

The OptimizerAgent provides:
- Query performance analysis
- Index recommendations with impact estimation
- Statistics updates for query optimizer
- Before/after metrics for optimization validation
- Safety validation for DDL operations
"""

from typing import Dict, Any, List, Optional
from ..base import BaseAgent, TaskContext, AgentConfig


class OptimizerAgent(BaseAgent):
    """
    Agent for intelligent query and database optimization

    Performs automated optimization workflows including:
    - Query performance analysis and execution plan review
    - Index recommendations based on query patterns
    - Statistics updates for outdated or missing statistics
    - Performance impact estimation
    - Before/after metrics comparison

    Attributes:
        config: Agent configuration with optimizer capabilities
        llm_manager: LLM manager for intelligent analysis
        tool_registry: Registry of optimization tools
        state_manager: State manager for checkpointing

    Example:
        config = AgentConfig(
            agent_id="optimizer_001",
            agent_type="optimizer",
            capabilities=[
                AgentCapability.DATABASE_READ,
                AgentCapability.QUERY_OPTIMIZE,
                AgentCapability.INDEX_MANAGE,
                AgentCapability.SCHEMA_ANALYZE
            ],
            llm_config={"model": "llama2", "temperature": 0.3},
            safety_level="moderate"
        )

        agent = OptimizerAgent(config, llm_manager, tool_registry, state_manager)

        task = TaskContext(
            task_id="optimize_001",
            task_description="Optimize slow user search query",
            input_data={
                'optimization_type': 'query_analysis',
                'query': 'SELECT * FROM users WHERE email = ?'
            }
        )

        result = await agent.run(task)
    """

    def __init__(
        self,
        config: AgentConfig,
        llm_manager,
        tool_registry,
        state_manager
    ):
        """
        Initialize the OptimizerAgent

        Args:
            config: Agent configuration with optimizer capabilities
            llm_manager: LLM manager instance for intelligent analysis
            tool_registry: Tool registry instance with optimization tools
            state_manager: State manager instance for checkpointing
        """
        super().__init__(config, llm_manager, tool_registry, state_manager)

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create execution plan for optimization task

        Analyzes the optimization type and creates a detailed plan:

        - Query Analysis:
          1. Analyze query performance and execution plan
          2. Identify performance bottlenecks
          3. Recommend optimizations

        - Index Recommendation:
          1. Analyze query patterns
          2. Suggest beneficial indexes
          3. Estimate performance impact

        - Statistics Update:
          1. Identify stale statistics
          2. Update statistics
          3. Verify improvement

        Args:
            task: Task context containing optimization parameters

        Returns:
            List of planned steps with tools and parameters

        Raises:
            ValueError: If optimization_type is invalid

        Example:
            task = TaskContext(
                task_id="opt_001",
                task_description="Optimize query",
                input_data={
                    'optimization_type': 'query_analysis',
                    'query': 'SELECT * FROM users WHERE email = ?'
                }
            )
            plan = await agent.plan(task)
            # Returns steps for query analysis workflow
        """
        optimization_type = task.input_data.get('optimization_type', 'query_analysis')

        if optimization_type == 'query_analysis':
            return await self._plan_query_analysis(task)
        elif optimization_type == 'index_recommendation':
            return await self._plan_index_recommendation(task)
        elif optimization_type == 'statistics_update':
            return await self._plan_statistics_update(task)
        else:
            raise ValueError(
                f"Unknown optimization type: {optimization_type}. "
                f"Valid types: query_analysis, index_recommendation, statistics_update"
            )

    async def _plan_query_analysis(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Plan query performance analysis workflow

        Creates a plan to:
        1. Analyze slow queries to identify performance issues
        2. Identify specific bottlenecks (missing indexes, table scans, etc.)
        3. Recommend optimization fixes

        Args:
            task: Task context with query to analyze

        Returns:
            List of steps for query analysis
        """
        query = task.input_data.get('query')

        plan = [
            {
                'tool': 'analyze_slow_queries',
                'params': {
                    'query': query,
                    'database': task.database_config.get('database') if task.database_config else None,
                    'include_execution_plan': True
                },
                'rationale': 'Analyze query performance and identify bottlenecks'
            },
            {
                'tool': 'recommend_indexes',
                'params': {
                    'query': query,
                    'analysis_results': '${step_0.output.analysis}'
                },
                'rationale': 'Recommend indexes based on query analysis'
            },
            {
                'tool': 'validate_optimization',
                'params': {
                    'query': query,
                    'recommendations': '${step_1.output.recommendations}'
                },
                'rationale': 'Validate optimization recommendations'
            }
        ]

        return plan

    async def _plan_index_recommendation(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Plan index recommendation workflow

        Creates a plan to:
        1. Analyze query patterns to understand access patterns
        2. Suggest beneficial indexes based on patterns
        3. Estimate performance impact of each index

        Args:
            task: Task context with query patterns

        Returns:
            List of steps for index recommendation
        """
        queries = task.input_data.get('queries', [])
        tables = task.input_data.get('tables', [])

        plan = [
            {
                'tool': 'analyze_slow_queries',
                'params': {
                    'queries': queries,
                    'tables': tables,
                    'database': task.database_config.get('database') if task.database_config else None
                },
                'rationale': 'Analyze query patterns and table access patterns'
            },
            {
                'tool': 'recommend_indexes',
                'params': {
                    'query_patterns': '${step_0.output.patterns}',
                    'table_statistics': '${step_0.output.table_stats}',
                    'max_recommendations': task.input_data.get('max_recommendations', 5)
                },
                'rationale': 'Generate index recommendations based on patterns'
            },
            {
                'tool': 'validate_optimization',
                'params': {
                    'recommendations': '${step_1.output.recommendations}',
                    'estimate_impact': True
                },
                'rationale': 'Estimate performance impact of recommended indexes'
            }
        ]

        # Add index creation step if auto_apply is enabled
        if task.input_data.get('auto_apply', False):
            plan.append({
                'tool': 'recommend_indexes',
                'params': {
                    'recommendations': '${step_2.output.validated_recommendations}',
                    'create_indexes': True
                },
                'rationale': 'Create recommended indexes (requires approval)'
            })

        return plan

    async def _plan_statistics_update(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Plan statistics update workflow

        Creates a plan to:
        1. Identify tables with stale statistics
        2. Update statistics to help query optimizer
        3. Verify performance improvement

        Args:
            task: Task context with tables to analyze

        Returns:
            List of steps for statistics update
        """
        tables = task.input_data.get('tables', [])

        plan = [
            {
                'tool': 'analyze_slow_queries',
                'params': {
                    'tables': tables,
                    'check_statistics': True,
                    'database': task.database_config.get('database') if task.database_config else None
                },
                'rationale': 'Identify tables with stale or missing statistics'
            },
            {
                'tool': 'update_statistics',
                'params': {
                    'tables': '${step_0.output.stale_tables}',
                    'full_scan': task.input_data.get('full_scan', False)
                },
                'rationale': 'Update statistics for identified tables'
            },
            {
                'tool': 'validate_optimization',
                'params': {
                    'tables': '${step_1.output.updated_tables}',
                    'verify_improvement': True
                },
                'rationale': 'Verify statistics update improved query plans'
            }
        ]

        return plan

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single optimization step

        Retrieves the specified tool from the registry and executes it
        with the provided parameters. Handles tool execution errors and
        returns structured results.

        Args:
            step: Step definition containing tool name and parameters

        Returns:
            Step execution result with outputs and metadata

        Raises:
            ValueError: If tool is not found in registry
            Exception: If tool execution fails

        Example:
            step = {
                'tool': 'analyze_slow_queries',
                'params': {'query': 'SELECT * FROM users', 'database': 'prod'}
            }
            result = await agent.execute_step(step)
            # result = {
            #     'analysis': {...},
            #     'bottlenecks': [...],
            #     'execution_time': 0.5
            # }
        """
        tool_name = step['tool']
        tool_params = step['params']

        # Get tool from registry
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found in registry: {tool_name}")

        # Execute tool with context
        context = {
            'database_module': getattr(self, 'database_module', None),
            'llm_manager': self.llm_manager,
            'task': self.current_task
        }

        result = await tool.execute(tool_params, context)

        return result

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate safety of optimization step

        Assesses the risk level of the planned step:

        - Query Analysis: SAFE (read-only operation)
        - Index Recommendation (analysis): SAFE (read-only)
        - Index Creation: MEDIUM risk (DDL operation)
        - Statistics Update: LOW risk (metadata update)

        Args:
            step: Step definition to validate

        Returns:
            Validation result dictionary containing:
            - requires_approval: Boolean indicating if approval needed
            - safe: Boolean indicating if step is safe
            - risk_level: Risk level assessment (safe/low/medium/high/critical)
            - risks: List of identified risks
            - mitigations: List of risk mitigations
            - performance_impact: Estimated performance impact

        Example:
            step = {'tool': 'recommend_indexes', 'params': {'create_indexes': True}}
            validation = agent.validate_safety(step)
            # validation = {
            #     'requires_approval': True,
            #     'safe': True,
            #     'risk_level': 'medium',
            #     'risks': ['DDL operation on database'],
            #     'mitigations': ['Index creation is reversible'],
            #     'performance_impact': 'Low during off-peak hours'
            # }
        """
        tool_name = step['tool']
        tool_params = step['params']

        # Default validation
        validation = {
            'requires_approval': False,
            'safe': True,
            'risk_level': 'safe',
            'risks': [],
            'mitigations': [],
            'performance_impact': 'negligible'
        }

        # Query analysis is always safe (read-only)
        if tool_name == 'analyze_slow_queries':
            validation['risk_level'] = 'safe'
            validation['mitigations'].append('Read-only query analysis operation')

        # Index recommendations (analysis only) are safe
        elif tool_name == 'recommend_indexes' and not tool_params.get('create_indexes'):
            validation['risk_level'] = 'safe'
            validation['mitigations'].append('Analysis only, no modifications')

        # Index creation is medium risk
        elif tool_name == 'recommend_indexes' and tool_params.get('create_indexes'):
            validation['risk_level'] = 'medium'
            validation['requires_approval'] = True
            validation['risks'].append('DDL operation - index creation')
            validation['risks'].append('Potential table locking during creation')
            validation['mitigations'].append('Indexes can be dropped if needed')
            validation['mitigations'].append('Create during off-peak hours')
            validation['performance_impact'] = 'medium_during_creation'

        # Statistics update is low risk
        elif tool_name == 'update_statistics':
            validation['risk_level'] = 'low'
            validation['risks'].append('Temporary table lock during statistics gathering')
            validation['mitigations'].append('Quick operation, minimal lock time')
            validation['mitigations'].append('Improves query optimizer decisions')
            validation['performance_impact'] = 'low'

        # Validation operations are safe
        elif tool_name == 'validate_optimization':
            validation['risk_level'] = 'safe'
            validation['mitigations'].append('Read-only validation operation')

        # Apply strict safety level constraints
        if self.config.safety_level == 'strict':
            if validation['risk_level'] in ['medium', 'high', 'critical']:
                validation['requires_approval'] = True

        return validation

    def _aggregate_results(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results from optimization actions

        Combines results from all executed steps into a comprehensive
        optimization report with before/after metrics.

        Args:
            actions: List of action dictionaries with step results

        Returns:
            Aggregated output data with:
            - summary: Overall optimization summary
            - before_metrics: Performance metrics before optimization
            - after_metrics: Performance metrics after optimization
            - recommendations: List of optimization recommendations
            - actions_taken: Count of actions executed
            - improvements: Measured or estimated improvements

        Example:
            actions = [
                {'step_index': 0, 'result': {'slow_queries': [...], 'avg_time': 500}},
                {'step_index': 1, 'result': {'recommended_indexes': [...]}},
                {'step_index': 2, 'result': {'estimated_improvement': '60%'}}
            ]
            result = agent._aggregate_results(actions)
            # result = {
            #     'summary': 'Query optimization completed',
            #     'before_metrics': {'avg_execution_time': 500},
            #     'after_metrics': {'estimated_execution_time': 200},
            #     'recommendations': [...],
            #     'improvements': '60% estimated improvement'
            # }
        """
        aggregated = {
            'actions_count': len(actions),
            'summary': 'Optimization analysis completed',
            'before_metrics': {},
            'after_metrics': {},
            'recommendations': [],
            'improvements': []
        }

        # Extract metrics from actions
        for action in actions:
            if 'result' not in action or not isinstance(action['result'], dict):
                continue

            result = action['result']

            # Collect before metrics
            if 'execution_time' in result:
                aggregated['before_metrics']['execution_time'] = result['execution_time']
            if 'slow_queries' in result:
                aggregated['before_metrics']['slow_query_count'] = len(result['slow_queries'])
            if 'table_stats' in result:
                aggregated['before_metrics']['table_statistics'] = result['table_stats']

            # Collect recommendations
            if 'recommendations' in result:
                if isinstance(result['recommendations'], list):
                    aggregated['recommendations'].extend(result['recommendations'])
                else:
                    aggregated['recommendations'].append(result['recommendations'])

            if 'recommended_indexes' in result:
                aggregated['recommendations'].extend(result['recommended_indexes'])

            # Collect improvement metrics
            if 'estimated_improvement' in result:
                aggregated['improvements'].append(result['estimated_improvement'])

            if 'verified_improvement' in result:
                aggregated['after_metrics']['verified_improvement'] = result['verified_improvement']

            # Collect after metrics
            if 'updated_tables' in result:
                aggregated['after_metrics']['updated_table_count'] = len(result['updated_tables'])

            if 'created_indexes' in result:
                aggregated['after_metrics']['created_index_count'] = len(result['created_indexes'])

        # Calculate overall improvement
        if aggregated['improvements']:
            aggregated['summary'] = (
                f"Optimization completed with {len(aggregated['recommendations'])} "
                f"recommendations and estimated improvements: {', '.join(aggregated['improvements'])}"
            )

        return aggregated
