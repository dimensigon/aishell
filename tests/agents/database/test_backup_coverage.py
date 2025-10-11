"""
Comprehensive tests for BackupAgent to achieve 90%+ coverage

Tests backup planning, execution, safety validation, and result aggregation
for all backup operation types.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock

from src.agents.database.backup import BackupAgent
from src.agents.base import AgentConfig, TaskContext, AgentCapability


@pytest.fixture
def backup_config():
    """Create backup agent configuration"""
    return AgentConfig(
        agent_id="backup_001",
        agent_type="backup",
        capabilities=[
            AgentCapability.DATABASE_READ,
            AgentCapability.BACKUP_CREATE,
            AgentCapability.BACKUP_RESTORE,
            AgentCapability.FILE_WRITE
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
    registry.get_tool = Mock(return_value=AsyncMock(execute=AsyncMock(return_value={})))
    return registry


@pytest.fixture
def mock_state_manager():
    """Create mock state manager"""
    return Mock()


@pytest.fixture
def backup_agent(backup_config, mock_llm_manager, mock_tool_registry, mock_state_manager):
    """Create BackupAgent instance"""
    return BackupAgent(
        config=backup_config,
        llm_manager=mock_llm_manager,
        tool_registry=mock_tool_registry,
        state_manager=mock_state_manager
    )


class TestBackupAgentFullBackupPlanning:
    """Test full backup planning"""

    @pytest.mark.asyncio
    async def test_plan_full_backup(self, backup_agent):
        """Test planning for full backup"""
        task = TaskContext(
            task_id="backup_001",
            task_description="Create full backup",
            input_data={
                'backup_type': 'full',
                'destination': '/backups/prod.sql',
                'compression': True
            },
            database_config={'database': 'production'}
        )

        plan = await backup_agent.plan(task)

        assert len(plan) == 3
        assert plan[0]['tool'] == 'calculate_backup_size'
        assert plan[1]['tool'] == 'backup_database_full'
        assert plan[2]['tool'] == 'validate_backup'

    @pytest.mark.asyncio
    async def test_full_backup_includes_compression(self, backup_agent):
        """Test full backup plan includes compression parameter"""
        task = TaskContext(
            task_id="backup_001",
            task_description="Create compressed backup",
            input_data={
                'backup_type': 'full',
                'destination': '/backups/prod.sql.gz',
                'compression': True
            },
            database_config={'database': 'production'}
        )

        plan = await backup_agent.plan(task)

        backup_step = plan[1]
        assert backup_step['params']['compression'] is True

    @pytest.mark.asyncio
    async def test_full_backup_without_compression(self, backup_agent):
        """Test full backup without compression"""
        task = TaskContext(
            task_id="backup_001",
            task_description="Create uncompressed backup",
            input_data={
                'backup_type': 'full',
                'destination': '/backups/prod.sql',
                'compression': False
            },
            database_config={'database': 'production'}
        )

        plan = await backup_agent.plan(task)

        backup_step = plan[1]
        assert backup_step['params']['compression'] is False


class TestBackupAgentIncrementalBackupPlanning:
    """Test incremental backup planning"""

    @pytest.mark.asyncio
    async def test_plan_incremental_backup(self, backup_agent):
        """Test planning for incremental backup"""
        task = TaskContext(
            task_id="backup_002",
            task_description="Create incremental backup",
            input_data={
                'backup_type': 'incremental',
                'destination': '/backups/incremental',
                'compression': True,
                'base_backup': '/backups/full_backup.sql'
            },
            database_config={'database': 'production'}
        )

        plan = await backup_agent.plan(task)

        assert len(plan) == 3
        assert plan[0]['tool'] == 'calculate_backup_size'
        assert plan[0]['params']['incremental'] is True
        assert plan[1]['tool'] == 'backup_database_incremental'
        assert plan[2]['tool'] == 'validate_backup'

    @pytest.mark.asyncio
    async def test_incremental_backup_includes_base(self, backup_agent):
        """Test incremental backup includes base backup reference"""
        task = TaskContext(
            task_id="backup_002",
            task_description="Create incremental backup",
            input_data={
                'backup_type': 'incremental',
                'destination': '/backups/inc',
                'base_backup': '/backups/base.sql'
            },
            database_config={'database': 'production'}
        )

        plan = await backup_agent.plan(task)

        backup_step = plan[1]
        assert backup_step['params']['base_backup'] == '/backups/base.sql'


class TestBackupAgentRestorePlanning:
    """Test backup restore planning"""

    @pytest.mark.asyncio
    async def test_plan_restore(self, backup_agent):
        """Test planning for restore operation"""
        task = TaskContext(
            task_id="restore_001",
            task_description="Restore from backup",
            input_data={
                'backup_type': 'restore',
                'backup_path': '/backups/prod_backup.sql',
                'overwrite': True
            },
            database_config={'database': 'production'}
        )

        plan = await backup_agent.plan(task)

        assert len(plan) == 3
        assert plan[0]['tool'] == 'validate_backup'
        assert plan[1]['tool'] == 'restore_backup'
        assert plan[2]['tool'] == 'verify_data_integrity'

    @pytest.mark.asyncio
    async def test_restore_validates_before_executing(self, backup_agent):
        """Test restore validates backup before restoring"""
        task = TaskContext(
            task_id="restore_001",
            task_description="Restore from backup",
            input_data={
                'backup_type': 'restore',
                'backup_path': '/backups/backup.sql'
            },
            database_config={'database': 'test'}
        )

        plan = await backup_agent.plan(task)

        # First step should validate backup
        assert plan[0]['tool'] == 'validate_backup'
        assert plan[0]['rationale'] == 'Verify backup exists and is valid before restore'

    @pytest.mark.asyncio
    async def test_restore_with_overwrite_false(self, backup_agent):
        """Test restore with overwrite disabled"""
        task = TaskContext(
            task_id="restore_001",
            task_description="Restore without overwrite",
            input_data={
                'backup_type': 'restore',
                'backup_path': '/backups/backup.sql',
                'overwrite': False
            },
            database_config={'database': 'test'}
        )

        plan = await backup_agent.plan(task)

        restore_step = plan[1]
        assert restore_step['params']['overwrite'] is False


class TestBackupAgentCleanupPlanning:
    """Test backup cleanup planning"""

    @pytest.mark.asyncio
    async def test_cleanup_added_to_full_backup(self, backup_agent):
        """Test cleanup step added to full backup when configured"""
        task = TaskContext(
            task_id="backup_001",
            task_description="Create backup and cleanup old backups",
            input_data={
                'backup_type': 'full',
                'destination': '/backups/prod.sql',
                'cleanup_old': True,
                'retention_days': 30
            },
            database_config={'database': 'production'}
        )

        plan = await backup_agent.plan(task)

        # Should have extra cleanup step
        assert len(plan) == 4
        cleanup_step = plan[-1]
        assert cleanup_step['tool'] == 'cleanup_old_backups'
        assert cleanup_step['params']['retention_days'] == 30

    @pytest.mark.asyncio
    async def test_cleanup_not_added_by_default(self, backup_agent):
        """Test cleanup step not added when cleanup_old is False"""
        task = TaskContext(
            task_id="backup_001",
            task_description="Create backup",
            input_data={
                'backup_type': 'full',
                'destination': '/backups/prod.sql',
                'cleanup_old': False
            },
            database_config={'database': 'production'}
        )

        plan = await backup_agent.plan(task)

        # No cleanup step
        assert len(plan) == 3
        tool_names = [step['tool'] for step in plan]
        assert 'cleanup_old_backups' not in tool_names


class TestBackupAgentExecuteStep:
    """Test step execution"""

    @pytest.mark.asyncio
    async def test_execute_step_calls_tool(self, backup_agent, mock_tool_registry):
        """Test execute_step retrieves and executes tool"""
        mock_tool = AsyncMock()
        mock_tool.execute = AsyncMock(return_value={'backup_path': '/backups/test.sql'})
        mock_tool_registry.get_tool.return_value = mock_tool

        backup_agent.current_task = TaskContext(
            task_id="test_001",
            task_description="Test",
            input_data={},
            database_config={'database': 'test'}
        )

        step = {
            'tool': 'backup_database_full',
            'params': {'database': 'test', 'destination': '/backups/test.sql'}
        }

        result = await backup_agent.execute_step(step)

        mock_tool_registry.get_tool.assert_called_once_with('backup_database_full')
        mock_tool.execute.assert_called_once()
        assert result['backup_path'] == '/backups/test.sql'

    @pytest.mark.asyncio
    async def test_execute_step_tool_not_found(self, backup_agent, mock_tool_registry):
        """Test execute_step raises error when tool not found"""
        mock_tool_registry.get_tool.return_value = None

        step = {'tool': 'nonexistent_tool', 'params': {}}

        with pytest.raises(ValueError, match="Tool 'nonexistent_tool' not found"):
            await backup_agent.execute_step(step)


class TestBackupAgentSafetyValidation:
    """Test safety validation"""

    def test_validate_safe_tools(self, backup_agent):
        """Test validation of safe read-only tools"""
        safe_tools = [
            'calculate_backup_size',
            'list_backups',
            'validate_backup'
        ]

        for tool_name in safe_tools:
            step = {'tool': tool_name, 'params': {}}
            validation = backup_agent.validate_safety(step)

            assert validation['safe'] is True
            assert validation['risk_level'] == 'safe'
            assert validation['requires_approval'] is False

    def test_validate_backup_creation_low_risk(self, backup_agent):
        """Test backup creation is low risk"""
        backup_tools = [
            'backup_database_full',
            'backup_database_incremental',
            'compress_backup'
        ]

        for tool_name in backup_tools:
            step = {'tool': tool_name, 'params': {}}
            validation = backup_agent.validate_safety(step)

            assert validation['risk_level'] == 'low'
            assert validation['requires_approval'] is False
            assert 'Disk space consumption' in validation['risks']

    def test_validate_restore_high_risk(self, backup_agent):
        """Test restore is high risk and requires approval"""
        step = {'tool': 'restore_backup', 'params': {}}
        validation = backup_agent.validate_safety(step)

        assert validation['risk_level'] == 'high'
        assert validation['requires_approval'] is True
        assert 'Will overwrite existing database' in validation['risks']

    def test_validate_cleanup_medium_risk(self, backup_agent):
        """Test cleanup with normal retention is medium risk"""
        step = {
            'tool': 'cleanup_old_backups',
            'params': {'retention_days': 30}
        }
        validation = backup_agent.validate_safety(step)

        assert validation['risk_level'] == 'medium'
        assert 'Permanent deletion of backup files' in validation['risks']

    def test_validate_cleanup_aggressive_retention(self, backup_agent):
        """Test cleanup with short retention requires approval"""
        step = {
            'tool': 'cleanup_old_backups',
            'params': {'retention_days': 3}
        }
        validation = backup_agent.validate_safety(step)

        assert validation['risk_level'] == 'high'
        assert validation['requires_approval'] is True
        assert any('recent backups' in risk.lower() for risk in validation['risks'])

    def test_validate_cleanup_strict_mode(self):
        """Test cleanup requires approval in strict mode"""
        config = AgentConfig(
            agent_id="backup_001",
            agent_type="backup",
            capabilities=[],
            llm_config={},
            safety_level="strict"
        )
        agent = BackupAgent(config, Mock(), Mock(), Mock())

        step = {
            'tool': 'cleanup_old_backups',
            'params': {'retention_days': 30}
        }
        validation = agent.validate_safety(step)

        assert validation['requires_approval'] is True

    def test_validate_unknown_tool(self, backup_agent):
        """Test unknown tool requires approval"""
        step = {'tool': 'unknown_operation', 'params': {}}
        validation = backup_agent.validate_safety(step)

        assert validation['risk_level'] == 'unknown'
        assert validation['requires_approval'] is True


class TestBackupAgentResultAggregation:
    """Test result aggregation"""

    def test_aggregate_backup_results(self, backup_agent):
        """Test aggregating results from backup workflow"""
        backup_agent.current_task = TaskContext(
            task_id="test_001",
            task_description="Test",
            input_data={'backup_type': 'full'}
        )

        actions = [
            {'result': {'size_bytes': 1024000}},
            {'result': {'backup_path': '/backups/prod.sql', 'duration_seconds': 45.2}},
            {'result': {'validation_status': 'passed', 'checksum': 'abc123'}}
        ]

        aggregated = backup_agent._aggregate_results(actions)

        assert aggregated['actions_count'] == 3
        assert aggregated['backup_type'] == 'full'
        assert aggregated['backup_path'] == '/backups/prod.sql'
        assert aggregated['size_bytes'] == 1024000
        assert aggregated['size_mb'] == 1.0
        assert aggregated['duration_seconds'] == 45.2
        assert aggregated['validation_status'] == 'passed'
        assert aggregated['checksum'] == 'abc123'

    def test_aggregate_with_compression_info(self, backup_agent):
        """Test aggregation includes compression information"""
        backup_agent.current_task = TaskContext(
            task_id="test_001",
            task_description="Test",
            input_data={'backup_type': 'full'}
        )

        actions = [
            {'result': {'compression_ratio': 0.65}}
        ]

        aggregated = backup_agent._aggregate_results(actions)

        assert aggregated['compression_ratio'] == 0.65

    def test_aggregate_cleanup_results(self, backup_agent):
        """Test aggregation includes cleanup results"""
        backup_agent.current_task = TaskContext(
            task_id="test_001",
            task_description="Test",
            input_data={'backup_type': 'full'}
        )

        actions = [
            {'result': {'deleted_count': 5}}
        ]

        aggregated = backup_agent._aggregate_results(actions)

        assert aggregated['cleaned_up_backups'] == 5

    def test_aggregate_restore_results(self, backup_agent):
        """Test aggregation includes restore information"""
        backup_agent.current_task = TaskContext(
            task_id="test_001",
            task_description="Test",
            input_data={'backup_type': 'restore'}
        )

        actions = [
            {'result': {'restore_status': 'completed', 'integrity_check': 'passed'}}
        ]

        aggregated = backup_agent._aggregate_results(actions)

        assert aggregated['restore_status'] == 'completed'
        assert aggregated['integrity_check'] == 'passed'

    def test_aggregate_empty_actions(self, backup_agent):
        """Test aggregating empty actions list"""
        backup_agent.current_task = TaskContext(
            task_id="test_001",
            task_description="Test",
            input_data={'backup_type': 'full'}
        )

        actions = []

        aggregated = backup_agent._aggregate_results(actions)

        assert aggregated['actions_count'] == 0
        assert aggregated['backup_type'] == 'full'


class TestBackupAgentEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_plan_with_no_database_config(self, backup_agent):
        """Test planning without database config"""
        task = TaskContext(
            task_id="backup_001",
            task_description="Create backup",
            input_data={'backup_type': 'full', 'destination': '/backups/test.sql'},
            database_config=None
        )

        plan = await backup_agent.plan(task)

        # Should use 'unknown' as database name
        assert plan[0]['params']['database'] == 'unknown'

    @pytest.mark.asyncio
    async def test_plan_with_default_backup_type(self, backup_agent):
        """Test planning with default backup type"""
        task = TaskContext(
            task_id="backup_001",
            task_description="Create backup",
            input_data={'destination': '/backups/test.sql'},  # No backup_type specified
            database_config={'database': 'test'}
        )

        plan = await backup_agent.plan(task)

        # Should default to full backup
        assert plan[1]['tool'] == 'backup_database_full'

    @pytest.mark.asyncio
    async def test_execute_without_current_task(self, backup_agent, mock_tool_registry):
        """Test execute_step when current_task is None"""
        mock_tool = AsyncMock()
        mock_tool.execute = AsyncMock(return_value={})
        mock_tool_registry.get_tool.return_value = mock_tool

        backup_agent.current_task = None

        step = {'tool': 'validate_backup', 'params': {}}

        # Should not raise error even without current_task
        result = await backup_agent.execute_step(step)

        assert result == {}

    def test_aggregate_without_current_task(self, backup_agent):
        """Test aggregation when current_task is None"""
        backup_agent.current_task = None

        actions = [{'result': {'backup_path': '/test.sql'}}]

        aggregated = backup_agent._aggregate_results(actions)

        assert aggregated['backup_type'] == 'unknown'
        assert aggregated['backup_path'] == '/test.sql'


class TestBackupAgentPlanRationale:
    """Test plan step rationale"""

    @pytest.mark.asyncio
    async def test_full_backup_rationale(self, backup_agent):
        """Test rationale is included in full backup plan"""
        task = TaskContext(
            task_id="backup_001",
            task_description="Create backup",
            input_data={'backup_type': 'full', 'destination': '/backups/test.sql'},
            database_config={'database': 'test'}
        )

        plan = await backup_agent.plan(task)

        assert 'rationale' in plan[0]
        assert 'rationale' in plan[1]
        assert 'rationale' in plan[2]
        assert 'Estimate backup size' in plan[0]['rationale']
        assert 'Create full database backup' in plan[1]['rationale']
        assert 'Verify backup integrity' in plan[2]['rationale']

    @pytest.mark.asyncio
    async def test_incremental_backup_rationale(self, backup_agent):
        """Test rationale for incremental backup"""
        task = TaskContext(
            task_id="backup_002",
            task_description="Create incremental backup",
            input_data={'backup_type': 'incremental', 'destination': '/backups/inc.sql'},
            database_config={'database': 'test'}
        )

        plan = await backup_agent.plan(task)

        assert 'incremental backup' in plan[0]['rationale'].lower()
        assert 'incremental backup' in plan[1]['rationale'].lower()

    @pytest.mark.asyncio
    async def test_restore_rationale(self, backup_agent):
        """Test rationale for restore operation"""
        task = TaskContext(
            task_id="restore_001",
            task_description="Restore backup",
            input_data={'backup_type': 'restore', 'backup_path': '/backups/test.sql'},
            database_config={'database': 'test'}
        )

        plan = await backup_agent.plan(task)

        assert 'before restore' in plan[0]['rationale'].lower()
        assert 'Restore database' in plan[1]['rationale']
        assert 'integrity after restoration' in plan[2]['rationale'].lower()
