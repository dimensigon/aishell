"""
Comprehensive tests for OptimizerAgent to achieve 90%+ coverage

Tests query optimization, index recommendations, statistics updates,
safety validation, and result aggregation.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.agents.database.optimizer import OptimizerAgent
from src.agents.base import AgentConfig, TaskContext, AgentCapability


@pytest.fixture
def optimizer_config():
    """Create optimizer agent configuration"""
    return AgentConfig(
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


@pytest.fixture
def mock_llm_manager():
    """Create mock LLM manager"""
    return AsyncMock()


@pytest.fixture
def mock_tool_registry():
    """Create mock tool registry"""
    registry = Mock()
    tool = AsyncMock()
    tool.execute = AsyncMock(return_value={'analysis': {}, 'recommendations': []})
    registry.get_tool = Mock(return_value=tool)
    return registry


@pytest.fixture
def mock_state_manager():
    """Create mock state manager"""
    return Mock()


@pytest.fixture
def optimizer_agent(optimizer_config, mock_llm_manager, mock_tool_registry, mock_state_manager):
    """Create OptimizerAgent instance"""
    return OptimizerAgent(
        config=optimizer_config,
        llm_manager=mock_llm_manager,
        tool_registry=mock_tool_registry,
        state_manager=mock_state_manager
    )


class TestOptimizerAgentQueryAnalysisPlanning:
    """Test query analysis planning"""

    @pytest.mark.asyncio
    async def test_plan_query_analysis(self, optimizer_agent):
        """Test planning for query analysis"""
        task = TaskContext(
            task_id="optimize_001",
            task_description="Analyze slow query",
            input_data={
                'optimization_type': 'query_analysis',
                'query': 'SELECT * FROM users WHERE email = ?'
            },
            database_config={'database': 'production'}
        )

        plan = await optimizer_agent.plan(task)

        assert len(plan) == 3
        assert plan[0]['tool'] == 'analyze_slow_queries'
        assert plan[1]['tool'] == 'recommend_indexes'
        assert plan[2]['tool'] == 'validate_optimization'

    @pytest.mark.asyncio
    async def test_query_analysis_includes_execution_plan(self, optimizer_agent):
        """Test query analysis requests execution plan"""
        task = TaskContext(
            task_id="optimize_001",
            task_description="Analyze query",
            input_data={
                'optimization_type': 'query_analysis',
                'query': 'SELECT * FROM users'
            },
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        analyze_step = plan[0]
        assert analyze_step['params']['include_execution_plan'] is True

    @pytest.mark.asyncio
    async def test_query_analysis_recommends_indexes(self, optimizer_agent):
        """Test query analysis includes index recommendations"""
        task = TaskContext(
            task_id="optimize_001",
            task_description="Analyze query",
            input_data={
                'optimization_type': 'query_analysis',
                'query': 'SELECT * FROM users WHERE name = ?'
            },
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        recommend_step = plan[1]
        assert recommend_step['tool'] == 'recommend_indexes'
        assert recommend_step['rationale'] == 'Recommend indexes based on query analysis'


class TestOptimizerAgentIndexRecommendationPlanning:
    """Test index recommendation planning"""

    @pytest.mark.asyncio
    async def test_plan_index_recommendation(self, optimizer_agent):
        """Test planning for index recommendation"""
        task = TaskContext(
            task_id="optimize_002",
            task_description="Recommend indexes",
            input_data={
                'optimization_type': 'index_recommendation',
                'queries': ['SELECT * FROM users WHERE email = ?'],
                'tables': ['users']
            },
            database_config={'database': 'production'}
        )

        plan = await optimizer_agent.plan(task)

        assert len(plan) == 3
        assert plan[0]['tool'] == 'analyze_slow_queries'
        assert plan[1]['tool'] == 'recommend_indexes'
        assert plan[2]['tool'] == 'validate_optimization'

    @pytest.mark.asyncio
    async def test_index_recommendation_analyzes_patterns(self, optimizer_agent):
        """Test index recommendation analyzes query patterns"""
        task = TaskContext(
            task_id="optimize_002",
            task_description="Recommend indexes",
            input_data={
                'optimization_type': 'index_recommendation',
                'queries': ['SELECT * FROM users'],
                'tables': ['users']
            },
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        analyze_step = plan[0]
        assert 'query patterns' in analyze_step['rationale'].lower()

    @pytest.mark.asyncio
    async def test_index_recommendation_limits_suggestions(self, optimizer_agent):
        """Test index recommendation respects max_recommendations"""
        task = TaskContext(
            task_id="optimize_002",
            task_description="Recommend indexes",
            input_data={
                'optimization_type': 'index_recommendation',
                'queries': [],
                'tables': [],
                'max_recommendations': 10
            },
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        recommend_step = plan[1]
        assert recommend_step['params']['max_recommendations'] == 10

    @pytest.mark.asyncio
    async def test_index_recommendation_default_max(self, optimizer_agent):
        """Test index recommendation defaults to 5 recommendations"""
        task = TaskContext(
            task_id="optimize_002",
            task_description="Recommend indexes",
            input_data={
                'optimization_type': 'index_recommendation',
                'queries': [],
                'tables': []
            },
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        recommend_step = plan[1]
        assert recommend_step['params']['max_recommendations'] == 5

    @pytest.mark.asyncio
    async def test_index_recommendation_with_auto_apply(self, optimizer_agent):
        """Test index recommendation with auto_apply creates indexes"""
        task = TaskContext(
            task_id="optimize_002",
            task_description="Recommend and apply indexes",
            input_data={
                'optimization_type': 'index_recommendation',
                'queries': [],
                'tables': [],
                'auto_apply': True
            },
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        # Should have extra step for index creation
        assert len(plan) == 4
        create_step = plan[3]
        assert create_step['tool'] == 'recommend_indexes'
        assert create_step['params']['create_indexes'] is True

    @pytest.mark.asyncio
    async def test_index_recommendation_without_auto_apply(self, optimizer_agent):
        """Test index recommendation without auto_apply doesn't create"""
        task = TaskContext(
            task_id="optimize_002",
            task_description="Recommend indexes",
            input_data={
                'optimization_type': 'index_recommendation',
                'queries': [],
                'tables': [],
                'auto_apply': False
            },
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        # No extra create step
        assert len(plan) == 3


class TestOptimizerAgentStatisticsUpdatePlanning:
    """Test statistics update planning"""

    @pytest.mark.asyncio
    async def test_plan_statistics_update(self, optimizer_agent):
        """Test planning for statistics update"""
        task = TaskContext(
            task_id="optimize_003",
            task_description="Update statistics",
            input_data={
                'optimization_type': 'statistics_update',
                'tables': ['users', 'orders']
            },
            database_config={'database': 'production'}
        )

        plan = await optimizer_agent.plan(task)

        assert len(plan) == 3
        assert plan[0]['tool'] == 'analyze_slow_queries'
        assert plan[1]['tool'] == 'update_statistics'
        assert plan[2]['tool'] == 'validate_optimization'

    @pytest.mark.asyncio
    async def test_statistics_update_identifies_stale(self, optimizer_agent):
        """Test statistics update identifies stale statistics"""
        task = TaskContext(
            task_id="optimize_003",
            task_description="Update statistics",
            input_data={
                'optimization_type': 'statistics_update',
                'tables': ['users']
            },
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        analyze_step = plan[0]
        assert analyze_step['params']['check_statistics'] is True

    @pytest.mark.asyncio
    async def test_statistics_update_full_scan(self, optimizer_agent):
        """Test statistics update with full scan option"""
        task = TaskContext(
            task_id="optimize_003",
            task_description="Update statistics",
            input_data={
                'optimization_type': 'statistics_update',
                'tables': ['users'],
                'full_scan': True
            },
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        update_step = plan[1]
        assert update_step['params']['full_scan'] is True

    @pytest.mark.asyncio
    async def test_statistics_update_default_scan(self, optimizer_agent):
        """Test statistics update defaults to non-full scan"""
        task = TaskContext(
            task_id="optimize_003",
            task_description="Update statistics",
            input_data={
                'optimization_type': 'statistics_update',
                'tables': ['users']
            },
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        update_step = plan[1]
        assert update_step['params']['full_scan'] is False


class TestOptimizerAgentPlanMethodRouting:
    """Test plan method routes to correct planning functions"""

    @pytest.mark.asyncio
    async def test_plan_routes_to_query_analysis(self, optimizer_agent):
        """Test plan routes to query analysis"""
        task = TaskContext(
            task_id="test_001",
            task_description="Test",
            input_data={'optimization_type': 'query_analysis', 'query': 'SELECT * FROM users'},
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        # Should call _plan_query_analysis
        assert plan[0]['tool'] == 'analyze_slow_queries'
        assert plan[0]['params']['query'] == 'SELECT * FROM users'

    @pytest.mark.asyncio
    async def test_plan_routes_to_index_recommendation(self, optimizer_agent):
        """Test plan routes to index recommendation"""
        task = TaskContext(
            task_id="test_002",
            task_description="Test",
            input_data={'optimization_type': 'index_recommendation', 'queries': [], 'tables': []},
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        # Should call _plan_index_recommendation
        assert plan[1]['tool'] == 'recommend_indexes'

    @pytest.mark.asyncio
    async def test_plan_routes_to_statistics_update(self, optimizer_agent):
        """Test plan routes to statistics update"""
        task = TaskContext(
            task_id="test_003",
            task_description="Test",
            input_data={'optimization_type': 'statistics_update', 'tables': []},
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        # Should call _plan_statistics_update
        assert plan[1]['tool'] == 'update_statistics'

    @pytest.mark.asyncio
    async def test_plan_default_optimization_type(self, optimizer_agent):
        """Test plan defaults to query_analysis"""
        task = TaskContext(
            task_id="test_004",
            task_description="Test",
            input_data={},  # No optimization_type
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        # Should default to query_analysis
        assert plan[0]['tool'] == 'analyze_slow_queries'

    @pytest.mark.asyncio
    async def test_plan_invalid_type_raises_error(self, optimizer_agent):
        """Test plan raises error for unsupported optimization type"""
        task = TaskContext(
            task_id="test_005",
            task_description="Test",
            input_data={'optimization_type': 'unsupported_type'},
            database_config={'database': 'test'}
        )

        with pytest.raises(ValueError, match="Unknown optimization type"):
            await optimizer_agent.plan(task)


class TestOptimizerAgentExecuteStep:
    """Test step execution"""

    @pytest.mark.asyncio
    async def test_execute_step_calls_tool(self, optimizer_agent, mock_tool_registry):
        """Test execute_step retrieves and executes tool"""
        optimizer_agent.current_task = TaskContext(
            task_id="test_001",
            task_description="Test",
            input_data={},
            database_config={'database': 'test'}
        )

        step = {
            'tool': 'analyze_slow_queries',
            'params': {'query': 'SELECT * FROM users'}
        }

        result = await optimizer_agent.execute_step(step)

        mock_tool_registry.get_tool.assert_called_once_with('analyze_slow_queries')
        assert 'analysis' in result

    @pytest.mark.asyncio
    async def test_execute_step_tool_not_found(self, optimizer_agent, mock_tool_registry):
        """Test execute_step raises error when tool not found"""
        mock_tool_registry.get_tool.return_value = None

        step = {'tool': 'nonexistent_tool', 'params': {}}

        with pytest.raises(ValueError, match="Tool not found in registry"):
            await optimizer_agent.execute_step(step)

    @pytest.mark.asyncio
    async def test_execute_step_without_current_task(self, optimizer_agent, mock_tool_registry):
        """Test execute_step when current_task is None"""
        optimizer_agent.current_task = None

        step = {'tool': 'analyze_slow_queries', 'params': {}}

        # Should not raise error
        result = await optimizer_agent.execute_step(step)

        assert result is not None


class TestOptimizerAgentSafetyValidation:
    """Test safety validation"""

    def test_validate_query_analysis_safe(self, optimizer_agent):
        """Test query analysis is safe"""
        step = {'tool': 'analyze_slow_queries', 'params': {}}

        validation = optimizer_agent.validate_safety(step)

        assert validation['safe'] is True
        assert validation['risk_level'] == 'safe'
        assert validation['requires_approval'] is False

    def test_validate_index_recommendation_analysis_safe(self, optimizer_agent):
        """Test index recommendation without creation is safe"""
        step = {'tool': 'recommend_indexes', 'params': {'create_indexes': False}}

        validation = optimizer_agent.validate_safety(step)

        assert validation['risk_level'] == 'safe'
        assert validation['requires_approval'] is False

    def test_validate_index_creation_medium_risk(self, optimizer_agent):
        """Test index creation is medium risk"""
        step = {'tool': 'recommend_indexes', 'params': {'create_indexes': True}}

        validation = optimizer_agent.validate_safety(step)

        assert validation['risk_level'] == 'medium'
        assert validation['requires_approval'] is True
        assert 'DDL operation' in validation['risks'][0]

    def test_validate_statistics_update_low_risk(self, optimizer_agent):
        """Test statistics update is low risk"""
        step = {'tool': 'update_statistics', 'params': {}}

        validation = optimizer_agent.validate_safety(step)

        assert validation['risk_level'] == 'low'
        assert 'Temporary table lock' in validation['risks'][0]

    def test_validate_optimization_validation_safe(self, optimizer_agent):
        """Test validation operations are safe"""
        step = {'tool': 'validate_optimization', 'params': {}}

        validation = optimizer_agent.validate_safety(step)

        assert validation['risk_level'] == 'safe'
        assert validation['requires_approval'] is False

    def test_validate_strict_mode_medium_risk(self):
        """Test strict mode requires approval for medium risk"""
        config = AgentConfig(
            agent_id="optimizer_001",
            agent_type="optimizer",
            capabilities=[],
            llm_config={},
            safety_level="strict"
        )
        agent = OptimizerAgent(config, Mock(), Mock(), Mock())

        step = {'tool': 'recommend_indexes', 'params': {'create_indexes': True}}
        validation = agent.validate_safety(step)

        assert validation['requires_approval'] is True

    def test_validate_performance_impact_indicators(self, optimizer_agent):
        """Test validation includes performance impact assessment"""
        step = {'tool': 'analyze_slow_queries', 'params': {}}

        validation = optimizer_agent.validate_safety(step)

        assert 'performance_impact' in validation
        assert validation['performance_impact'] == 'negligible'


class TestOptimizerAgentResultAggregation:
    """Test result aggregation"""

    def test_aggregate_query_analysis_results(self, optimizer_agent):
        """Test aggregating query analysis results"""
        actions = [
            {'result': {'slow_queries': [{'query': 'SELECT...', 'time': 500}], 'execution_time': 500}},
            {'result': {'recommendations': ['Add index on email column']}},
            {'result': {'estimated_improvement': '60%'}}
        ]

        aggregated = optimizer_agent._aggregate_results(actions)

        assert aggregated['actions_count'] == 3
        assert 'before_metrics' in aggregated
        assert 'after_metrics' in aggregated
        assert 'recommendations' in aggregated
        assert 'improvements' in aggregated

    def test_aggregate_collects_before_metrics(self, optimizer_agent):
        """Test aggregation collects before metrics"""
        actions = [
            {'result': {'execution_time': 500, 'slow_queries': ['query1', 'query2'], 'table_stats': {'users': 1000}}}
        ]

        aggregated = optimizer_agent._aggregate_results(actions)

        assert aggregated['before_metrics']['execution_time'] == 500
        assert aggregated['before_metrics']['slow_query_count'] == 2
        assert aggregated['before_metrics']['table_statistics'] == {'users': 1000}

    def test_aggregate_collects_recommendations(self, optimizer_agent):
        """Test aggregation collects recommendations"""
        actions = [
            {'result': {'recommendations': ['Index on email', 'Index on created_at']}},
            {'result': {'recommended_indexes': ['users.email_idx']}}
        ]

        aggregated = optimizer_agent._aggregate_results(actions)

        assert len(aggregated['recommendations']) == 3

    def test_aggregate_collects_improvements(self, optimizer_agent):
        """Test aggregation collects improvement metrics"""
        actions = [
            {'result': {'estimated_improvement': '60%'}},
            {'result': {'verified_improvement': '55%'}}
        ]

        aggregated = optimizer_agent._aggregate_results(actions)

        assert '60%' in aggregated['improvements']
        assert aggregated['after_metrics']['verified_improvement'] == '55%'

    def test_aggregate_collects_after_metrics(self, optimizer_agent):
        """Test aggregation collects after metrics"""
        actions = [
            {'result': {'updated_tables': ['users', 'orders']}},
            {'result': {'created_indexes': ['idx_email', 'idx_created_at']}}
        ]

        aggregated = optimizer_agent._aggregate_results(actions)

        assert aggregated['after_metrics']['updated_table_count'] == 2
        assert aggregated['after_metrics']['created_index_count'] == 2

    def test_aggregate_creates_summary(self, optimizer_agent):
        """Test aggregation creates comprehensive summary"""
        actions = [
            {'result': {'recommendations': ['Index 1', 'Index 2']}},
            {'result': {'estimated_improvement': '50%', 'verified_improvement': '45%'}}
        ]

        aggregated = optimizer_agent._aggregate_results(actions)

        assert 'summary' in aggregated
        assert '2 recommendations' in aggregated['summary']

    def test_aggregate_empty_actions(self, optimizer_agent):
        """Test aggregating empty actions list"""
        actions = []

        aggregated = optimizer_agent._aggregate_results(actions)

        assert aggregated['actions_count'] == 0
        assert aggregated['recommendations'] == []
        assert aggregated['improvements'] == []


class TestOptimizerAgentEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_plan_without_database_config(self, optimizer_agent):
        """Test planning without database config"""
        task = TaskContext(
            task_id="optimize_001",
            task_description="Optimize",
            input_data={'optimization_type': 'query_analysis', 'query': 'SELECT * FROM users'},
            database_config=None
        )

        plan = await optimizer_agent.plan(task)

        # Should handle None database_config gracefully
        assert plan[0]['params']['database'] is None

    @pytest.mark.asyncio
    async def test_query_analysis_without_query(self, optimizer_agent):
        """Test query analysis without query parameter"""
        task = TaskContext(
            task_id="optimize_001",
            task_description="Analyze",
            input_data={'optimization_type': 'query_analysis'},  # No query
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        # Should handle missing query
        assert len(plan) > 0

    @pytest.mark.asyncio
    async def test_index_recommendation_without_queries(self, optimizer_agent):
        """Test index recommendation without queries"""
        task = TaskContext(
            task_id="optimize_002",
            task_description="Recommend",
            input_data={'optimization_type': 'index_recommendation'},  # No queries or tables
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        # Should use empty lists as default
        assert plan[0]['params']['queries'] == []
        assert plan[0]['params']['tables'] == []

    @pytest.mark.asyncio
    async def test_statistics_update_without_tables(self, optimizer_agent):
        """Test statistics update without tables"""
        task = TaskContext(
            task_id="optimize_003",
            task_description="Update stats",
            input_data={'optimization_type': 'statistics_update'},  # No tables
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        # Should use empty list as default
        assert plan[0]['params']['tables'] == []


class TestOptimizerAgentPlanRationale:
    """Test plan step rationale"""

    @pytest.mark.asyncio
    async def test_query_analysis_rationale(self, optimizer_agent):
        """Test rationale is included in query analysis plan"""
        task = TaskContext(
            task_id="optimize_001",
            task_description="Analyze query",
            input_data={'optimization_type': 'query_analysis', 'query': 'SELECT * FROM users'},
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        assert all('rationale' in step for step in plan)
        assert 'bottlenecks' in plan[0]['rationale'].lower()

    @pytest.mark.asyncio
    async def test_index_recommendation_rationale(self, optimizer_agent):
        """Test rationale for index recommendation"""
        task = TaskContext(
            task_id="optimize_002",
            task_description="Recommend indexes",
            input_data={'optimization_type': 'index_recommendation', 'queries': [], 'tables': []},
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        assert 'query patterns' in plan[0]['rationale'].lower()
        assert 'index recommendations' in plan[1]['rationale'].lower()

    @pytest.mark.asyncio
    async def test_statistics_update_rationale(self, optimizer_agent):
        """Test rationale for statistics update"""
        task = TaskContext(
            task_id="optimize_003",
            task_description="Update statistics",
            input_data={'optimization_type': 'statistics_update', 'tables': []},
            database_config={'database': 'test'}
        )

        plan = await optimizer_agent.plan(task)

        assert 'stale' in plan[0]['rationale'].lower()
        assert 'Update statistics' in plan[1]['rationale']
