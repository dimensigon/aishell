"""
Comprehensive tests for MigrationAgent to achieve 90%+ coverage

Tests schema migration planning, data migration, rollbacks, safety validation,
and execution for all migration types.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.agents.database.migration import MigrationAgent
from src.agents.base import AgentConfig, TaskContext, AgentCapability


@pytest.fixture
def migration_config():
    """Create migration agent configuration"""
    return AgentConfig(
        agent_id="migration_001",
        agent_type="migration",
        capabilities=[
            AgentCapability.DATABASE_READ,
            AgentCapability.DATABASE_WRITE,
            AgentCapability.DATABASE_DDL,
            AgentCapability.SCHEMA_ANALYZE,
            AgentCapability.SCHEMA_MODIFY
        ],
        llm_config={"model": "llama2", "temperature": 0.3},
        safety_level="strict"
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
    tool.execute = AsyncMock(return_value={'schema': {}, 'migration_sql': 'ALTER TABLE...', 'rollback_sql': 'ALTER TABLE...'})
    registry.get_tool = Mock(return_value=tool)
    return registry


@pytest.fixture
def mock_state_manager():
    """Create mock state manager"""
    return Mock()


@pytest.fixture
def migration_agent(migration_config, mock_llm_manager, mock_tool_registry, mock_state_manager):
    """Create MigrationAgent instance"""
    return MigrationAgent(
        config=migration_config,
        llm_manager=mock_llm_manager,
        tool_registry=mock_tool_registry,
        state_manager=mock_state_manager
    )


class TestMigrationAgentSchemaChangePlanning:
    """Test schema change migration planning"""

    @pytest.mark.asyncio
    async def test_plan_schema_change(self, migration_agent):
        """Test planning for schema change migration"""
        task = TaskContext(
            task_id="migration_001",
            task_description="Add column to users table",
            input_data={
                'migration_type': 'schema_change',
                'target_schema': {
                    'table': 'users',
                    'column': 'phone',
                    'type': 'VARCHAR(20)'
                }
            },
            database_config={'database': 'production'}
        )

        plan = await migration_agent.plan(task)

        assert len(plan) == 7
        assert plan[0]['tool'] == 'backup_before_migration'
        assert plan[1]['tool'] == 'analyze_schema'
        assert plan[2]['tool'] == 'create_migration_script'
        assert plan[3]['tool'] == 'validate_migration'
        assert plan[4]['tool'] == 'create_rollback'
        assert plan[5]['tool'] == 'execute_migration'
        assert plan[6]['tool'] == 'verify_migration'

    @pytest.mark.asyncio
    async def test_schema_change_includes_backup(self, migration_agent):
        """Test schema change starts with backup"""
        task = TaskContext(
            task_id="migration_001",
            task_description="Schema change",
            input_data={
                'migration_type': 'schema_change',
                'target_schema': {}
            },
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        # First step should be backup
        assert plan[0]['tool'] == 'backup_before_migration'
        assert plan[0]['rationale'] == 'Create safety backup before schema changes'

    @pytest.mark.asyncio
    async def test_schema_change_analyzes_current_schema(self, migration_agent):
        """Test schema change includes current schema analysis"""
        task = TaskContext(
            task_id="migration_001",
            task_description="Schema change",
            input_data={
                'migration_type': 'schema_change',
                'target_schema': {}
            },
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        analyze_step = plan[1]
        assert analyze_step['tool'] == 'analyze_schema'
        assert analyze_step['params']['include_indexes'] is True
        assert analyze_step['params']['include_constraints'] is True

    @pytest.mark.asyncio
    async def test_schema_change_creates_rollback(self, migration_agent):
        """Test schema change creates rollback script"""
        task = TaskContext(
            task_id="migration_001",
            task_description="Schema change",
            input_data={
                'migration_type': 'schema_change',
                'target_schema': {'table': 'users'}
            },
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        rollback_step = plan[4]
        assert rollback_step['tool'] == 'create_rollback'
        assert rollback_step['rationale'] == 'Generate rollback script for emergency recovery'


class TestMigrationAgentDataMigrationPlanning:
    """Test data migration planning"""

    @pytest.mark.asyncio
    async def test_plan_data_migration(self, migration_agent):
        """Test planning for data migration"""
        task = TaskContext(
            task_id="migration_002",
            task_description="Migrate user data",
            input_data={
                'migration_type': 'data_migration',
                'migration_spec': {
                    'tables': ['users', 'profiles'],
                    'transformation': 'merge_columns'
                }
            },
            database_config={'database': 'production'}
        )

        plan = await migration_agent.plan(task)

        assert len(plan) == 7
        assert plan[0]['tool'] == 'backup_before_migration'
        assert plan[1]['tool'] == 'analyze_data_volume'
        assert plan[2]['tool'] == 'create_migration_script'
        assert plan[3]['tool'] == 'test_migration_sample'
        assert plan[4]['tool'] == 'create_rollback'
        assert plan[5]['tool'] == 'execute_migration'
        assert plan[6]['tool'] == 'verify_migration'

    @pytest.mark.asyncio
    async def test_data_migration_analyzes_volume(self, migration_agent):
        """Test data migration analyzes data volume"""
        task = TaskContext(
            task_id="migration_002",
            task_description="Migrate data",
            input_data={
                'migration_type': 'data_migration',
                'migration_spec': {'tables': ['users']}
            },
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        volume_step = plan[1]
        assert volume_step['tool'] == 'analyze_data_volume'
        assert 'estimate migration time' in volume_step['rationale'].lower()

    @pytest.mark.asyncio
    async def test_data_migration_tests_sample(self, migration_agent):
        """Test data migration tests on sample data first"""
        task = TaskContext(
            task_id="migration_002",
            task_description="Migrate data",
            input_data={
                'migration_type': 'data_migration',
                'migration_spec': {}
            },
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        test_step = plan[3]
        assert test_step['tool'] == 'test_migration_sample'
        assert test_step['params']['sample_size'] == 100


class TestMigrationAgentRollbackPlanning:
    """Test rollback planning"""

    @pytest.mark.asyncio
    async def test_plan_rollback(self, migration_agent):
        """Test planning for rollback operation"""
        task = TaskContext(
            task_id="rollback_001",
            task_description="Rollback failed migration",
            input_data={
                'migration_type': 'rollback',
                'migration_id': 'migration_001',
                'rollback_script': 'ALTER TABLE users DROP COLUMN...'
            },
            database_config={'database': 'production'}
        )

        plan = await migration_agent.plan(task)

        assert len(plan) == 5
        assert plan[0]['tool'] == 'analyze_rollback'
        assert plan[1]['tool'] == 'load_rollback_script'
        assert plan[2]['tool'] == 'validate_rollback'
        assert plan[3]['tool'] == 'execute_migration'
        assert plan[4]['tool'] == 'verify_migration'

    @pytest.mark.asyncio
    async def test_rollback_loads_script(self, migration_agent):
        """Test rollback loads the rollback script"""
        task = TaskContext(
            task_id="rollback_001",
            task_description="Rollback",
            input_data={
                'migration_type': 'rollback',
                'migration_id': 'migration_001',
                'rollback_script': 'DROP TABLE temp;'
            },
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        load_step = plan[1]
        assert load_step['tool'] == 'load_rollback_script'
        assert load_step['params']['custom_script'] == 'DROP TABLE temp;'

    @pytest.mark.asyncio
    async def test_rollback_has_no_rollback_script(self, migration_agent):
        """Test rollback itself has no rollback script"""
        task = TaskContext(
            task_id="rollback_001",
            task_description="Rollback",
            input_data={
                'migration_type': 'rollback',
                'migration_id': 'migration_001'
            },
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        execute_step = plan[3]
        assert execute_step['params']['rollback_sql'] is None


class TestMigrationAgentPlanMethodRouting:
    """Test plan method routes to correct planning functions"""

    @pytest.mark.asyncio
    async def test_plan_routes_to_schema_change(self, migration_agent):
        """Test plan routes to schema change planning"""
        task = TaskContext(
            task_id="test_001",
            task_description="Test",
            input_data={'migration_type': 'schema_change', 'target_schema': {}},
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        # Should call _plan_schema_change
        assert plan[0]['tool'] == 'backup_before_migration'
        assert plan[1]['tool'] == 'analyze_schema'

    @pytest.mark.asyncio
    async def test_plan_routes_to_data_migration(self, migration_agent):
        """Test plan routes to data migration planning"""
        task = TaskContext(
            task_id="test_002",
            task_description="Test",
            input_data={'migration_type': 'data_migration', 'migration_spec': {}},
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        # Should call _plan_data_migration
        assert plan[1]['tool'] == 'analyze_data_volume'

    @pytest.mark.asyncio
    async def test_plan_routes_to_rollback(self, migration_agent):
        """Test plan routes to rollback planning"""
        task = TaskContext(
            task_id="test_003",
            task_description="Test",
            input_data={'migration_type': 'rollback', 'migration_id': 'test'},
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        # Should call _plan_rollback
        assert plan[0]['tool'] == 'analyze_rollback'

    @pytest.mark.asyncio
    async def test_plan_invalid_type_raises_error(self, migration_agent):
        """Test plan raises error for unsupported migration type"""
        task = TaskContext(
            task_id="test_004",
            task_description="Test",
            input_data={'migration_type': 'unsupported_type'},
            database_config={'database': 'test'}
        )

        with pytest.raises(ValueError, match="Unsupported migration type"):
            await migration_agent.plan(task)


class TestMigrationAgentExecuteStep:
    """Test step execution"""

    @pytest.mark.asyncio
    async def test_execute_step_calls_tool(self, migration_agent, mock_tool_registry):
        """Test execute_step retrieves and executes tool"""
        migration_agent.current_task = TaskContext(
            task_id="test_001",
            task_description="Test",
            input_data={},
            database_config={'database': 'test'}
        )

        step = {
            'tool': 'analyze_schema',
            'params': {'database': 'test'},
            'rationale': 'Analyze schema'
        }

        result = await migration_agent.execute_step(step)

        mock_tool_registry.get_tool.assert_called_once_with('analyze_schema')
        assert 'schema' in result

    @pytest.mark.asyncio
    async def test_execute_step_tool_not_found(self, migration_agent, mock_tool_registry):
        """Test execute_step raises error when tool not found"""
        mock_tool_registry.get_tool.return_value = None

        step = {'tool': 'nonexistent_tool', 'params': {}}

        with pytest.raises(ValueError, match="Tool not found in registry"):
            await migration_agent.execute_step(step)

    @pytest.mark.asyncio
    async def test_execute_step_without_current_task(self, migration_agent, mock_tool_registry):
        """Test execute_step when current_task is None"""
        migration_agent.current_task = None

        step = {'tool': 'analyze_schema', 'params': {}}

        # Should not raise error
        result = await migration_agent.execute_step(step)

        assert result is not None


class TestMigrationAgentSafetyValidation:
    """Test safety validation"""

    def test_validate_execute_migration_high_risk(self, migration_agent):
        """Test execute_migration is high risk"""
        step = {'tool': 'execute_migration', 'params': {}}

        validation = migration_agent.validate_safety(step)

        assert validation['safe'] is True
        assert validation['risk_level'] == 'HIGH'
        assert validation['requires_approval'] is True
        assert 'DDL operation' in validation['risks'][0]

    def test_validate_rollback_operations(self, migration_agent):
        """Test rollback operations are high risk"""
        rollback_tools = ['analyze_rollback', 'execute_rollback']

        for tool_name in rollback_tools:
            step = {'tool': tool_name, 'params': {}}
            validation = migration_agent.validate_safety(step)

            assert validation['risk_level'] == 'HIGH'
            assert validation['requires_approval'] is True

    def test_validate_backup_operations_low_risk(self, migration_agent):
        """Test backup operations are low risk"""
        backup_tools = ['backup_before_migration', 'backup_database_full']

        for tool_name in backup_tools:
            step = {'tool': tool_name, 'params': {}}
            validation = migration_agent.validate_safety(step)

            assert validation['risk_level'] == 'LOW'
            assert validation['requires_approval'] is False

    def test_validate_analysis_operations_safe(self, migration_agent):
        """Test analysis operations are safe"""
        safe_tools = ['analyze_schema', 'validate_migration', 'verify_migration']

        for tool_name in safe_tools:
            step = {'tool': tool_name, 'params': {}}
            validation = migration_agent.validate_safety(step)

            assert validation['risk_level'] == 'SAFE'
            assert validation['requires_approval'] is False

    def test_validate_script_generation_safe(self, migration_agent):
        """Test script generation is safe"""
        script_tools = ['create_migration_script', 'create_rollback']

        for tool_name in script_tools:
            step = {'tool': tool_name, 'params': {}}
            validation = migration_agent.validate_safety(step)

            assert validation['risk_level'] == 'SAFE'
            assert validation['requires_approval'] is False

    def test_validate_data_migration_medium_risk(self, migration_agent):
        """Test data migration operations are medium risk"""
        data_tools = ['execute_data_migration', 'test_migration_sample']

        for tool_name in data_tools:
            step = {'tool': tool_name, 'params': {}}
            validation = migration_agent.validate_safety(step)

            assert validation['risk_level'] == 'MEDIUM'

    def test_validate_data_migration_strict_mode(self):
        """Test data migration requires approval in strict mode"""
        config = AgentConfig(
            agent_id="migration_001",
            agent_type="migration",
            capabilities=[],
            llm_config={},
            safety_level="strict"
        )
        agent = MigrationAgent(config, Mock(), Mock(), Mock())

        step = {'tool': 'execute_data_migration', 'params': {}}
        validation = agent.validate_safety(step)

        assert validation['requires_approval'] is True

    def test_validate_data_migration_moderate_mode(self):
        """Test data migration doesn't require approval in moderate mode"""
        config = AgentConfig(
            agent_id="migration_001",
            agent_type="migration",
            capabilities=[],
            llm_config={},
            safety_level="moderate"
        )
        agent = MigrationAgent(config, Mock(), Mock(), Mock())

        step = {'tool': 'execute_data_migration', 'params': {}}
        validation = agent.validate_safety(step)

        assert validation['requires_approval'] is False

    def test_validate_unknown_tool(self, migration_agent):
        """Test unknown tool is high risk"""
        step = {'tool': 'unknown_operation', 'params': {}}

        validation = migration_agent.validate_safety(step)

        assert validation['risk_level'] == 'HIGH'
        assert validation['requires_approval'] is True


class TestMigrationAgentEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_plan_without_database_config(self, migration_agent):
        """Test planning without database config"""
        task = TaskContext(
            task_id="migration_001",
            task_description="Migrate",
            input_data={'migration_type': 'schema_change', 'target_schema': {}},
            database_config=None
        )

        plan = await migration_agent.plan(task)

        # Should use 'default' as database name
        assert plan[0]['params']['database'] == 'default'

    @pytest.mark.asyncio
    async def test_plan_with_default_migration_type(self, migration_agent):
        """Test planning with default migration type"""
        task = TaskContext(
            task_id="migration_001",
            task_description="Migrate",
            input_data={'target_schema': {}},  # No migration_type
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        # Should default to schema_change
        assert plan[1]['tool'] == 'analyze_schema'

    @pytest.mark.asyncio
    async def test_data_migration_without_spec(self, migration_agent):
        """Test data migration without migration_spec"""
        task = TaskContext(
            task_id="migration_002",
            task_description="Migrate data",
            input_data={'migration_type': 'data_migration'},  # No migration_spec
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        # Should handle empty migration_spec
        assert len(plan) > 0

    @pytest.mark.asyncio
    async def test_rollback_without_custom_script(self, migration_agent):
        """Test rollback without custom script"""
        task = TaskContext(
            task_id="rollback_001",
            task_description="Rollback",
            input_data={'migration_type': 'rollback', 'migration_id': 'test'},
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        load_step = plan[1]
        assert load_step['params']['custom_script'] is None


class TestMigrationAgentPlanDetails:
    """Test detailed plan parameters"""

    @pytest.mark.asyncio
    async def test_schema_change_validation_checks(self, migration_agent):
        """Test schema change includes comprehensive validation"""
        task = TaskContext(
            task_id="migration_001",
            task_description="Schema change",
            input_data={'migration_type': 'schema_change', 'target_schema': {}},
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        validate_step = plan[3]
        assert validate_step['tool'] == 'validate_migration'
        assert validate_step['params']['check_data_loss'] is True
        assert validate_step['params']['check_breaking_changes'] is True

    @pytest.mark.asyncio
    async def test_data_migration_verification(self, migration_agent):
        """Test data migration includes verification steps"""
        task = TaskContext(
            task_id="migration_002",
            task_description="Data migration",
            input_data={'migration_type': 'data_migration', 'migration_spec': {}},
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        verify_step = plan[6]
        assert verify_step['tool'] == 'verify_migration'
        assert verify_step['params']['verify_row_counts'] is True
        assert verify_step['params']['verify_data_integrity'] is True

    @pytest.mark.asyncio
    async def test_rollback_validation(self, migration_agent):
        """Test rollback includes validation step"""
        task = TaskContext(
            task_id="rollback_001",
            task_description="Rollback",
            input_data={'migration_type': 'rollback', 'migration_id': 'test'},
            database_config={'database': 'test'}
        )

        plan = await migration_agent.plan(task)

        validate_step = plan[2]
        assert validate_step['tool'] == 'validate_rollback'


class TestMigrationAgentGetDatabaseModule:
    """Test database module retrieval"""

    def test_get_database_module(self, migration_agent):
        """Test _get_database_module returns None (placeholder)"""
        module = migration_agent._get_database_module()

        # Currently returns None as placeholder
        assert module is None
