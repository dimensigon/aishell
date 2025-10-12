"""
Agent-Tool Integration Tests (Phase 11/12)

Tests realistic scenarios where agents use tools to accomplish complex tasks:
- Database backup workflows
- Schema migration planning
- Performance optimization
- Multi-tool orchestration
- Error recovery scenarios
"""

import pytest
import asyncio
import tempfile
import os
from typing import Dict, Any, List

from src.agents.base import (
    BaseAgent,
    AgentState,
    AgentCapability,
    AgentConfig,
    TaskContext,
    TaskResult
)
from src.agents.tools import create_default_registry


# Mock State Manager for testing
class MockStateManager:
    """Mock state manager that implements checkpoint functionality"""

    def __init__(self, storage_path=None):
        self.storage_path = storage_path
        self._checkpoints = {}
        self._checkpoint_list = {}

    async def save_checkpoint(self, task_id: str, checkpoint_name: str, data) -> None:
        """Save a checkpoint"""
        key = f"{task_id}:{checkpoint_name}"
        self._checkpoints[key] = data

        if task_id not in self._checkpoint_list:
            self._checkpoint_list[task_id] = []
        if checkpoint_name not in self._checkpoint_list[task_id]:
            self._checkpoint_list[task_id].append(checkpoint_name)

    async def load_checkpoint(self, task_id: str, checkpoint_name: str):
        """Load a checkpoint"""
        key = f"{task_id}:{checkpoint_name}"
        return self._checkpoints.get(key)

    async def get_checkpoints(self, task_id: str):
        """Get list of checkpoint names for a task"""
        return self._checkpoint_list.get(task_id, [])

    def save_state(self, agent_id: str, state) -> None:
        """Save agent state"""
        key = f"state:{agent_id}"
        self._checkpoints[key] = state

    def load_state(self, agent_id: str):
        """Load agent state"""
        key = f"state:{agent_id}"
        return self._checkpoints.get(key)


class MockLLMManager:
    """Mock LLM for integration testing"""

    async def generate(self, prompt: str, max_tokens: int = 200) -> str:
        """Generate contextual responses based on prompt"""
        if "backup" in prompt.lower():
            return "Created full database backup with compression and verified integrity"
        elif "schema" in prompt.lower():
            return "Analyzed database schema, found 3 tables with proper indexes"
        elif "migration" in prompt.lower():
            return "Generated migration script with rollback capabilities"
        elif "optimization" in prompt.lower():
            return "Identified slow queries and recommended index optimizations"
        else:
            return "Task completed successfully according to plan"


class DatabaseBackupAgent(BaseAgent):
    """Agent specialized in database backup operations"""

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """Create backup workflow plan"""
        database = task.input_data.get('database', 'production')
        destination = task.input_data.get('destination', f'/backups/{database}_backup.sql.gz')

        return [
            {
                'tool': 'analyze_schema',
                'params': {
                    'database': database,
                    'include_indexes': True,
                    'include_constraints': True
                },
                'rationale': 'Analyze schema before backup to assess data size'
            },
            {
                'tool': 'backup_database_full',
                'params': {
                    'database': database,
                    'destination': destination,
                    'compression': True
                },
                'rationale': 'Create compressed full backup'
            },
            {
                'tool': 'validate_backup',
                'params': {
                    'backup_path': destination
                },
                'rationale': 'Validate backup integrity'
            }
        ]

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute backup workflow step"""
        tool = self.tool_registry.get_tool(step['tool'])
        if not tool:
            raise RuntimeError(f"Tool not found: {step['tool']}")

        context = {'database_module': None, 'llm_manager': self.llm_manager}
        return await tool.execute(step['params'], context)

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Validate step safety"""
        tool = self.tool_registry.get_tool(step['tool'])
        if not tool:
            return {'requires_approval': False, 'safe': False}

        return {
            'requires_approval': tool.requires_approval,
            'safe': True,
            'risk_level': tool.risk_level.value
        }


class MigrationPlannerAgent(BaseAgent):
    """Agent specialized in migration planning"""

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """Create migration planning workflow"""
        operation = task.input_data.get('operation', 'add_column')
        table = task.input_data.get('table', 'users')
        details = task.input_data.get('details', {})

        steps = [
            {
                'tool': 'analyze_schema',
                'params': {
                    'database': task.input_data.get('database', 'production'),
                    'include_indexes': True,
                    'include_constraints': True
                },
                'rationale': 'Analyze current schema state'
            }
        ]

        # Add migration-specific steps if tools are available
        if self.tool_registry.get_tool('create_migration_script'):
            steps.append({
                'tool': 'create_migration_script',
                'params': {
                    'operation': operation,
                    'table': table,
                    'details': details
                },
                'rationale': 'Generate migration script with rollback'
            })

        return steps

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute migration planning step"""
        tool = self.tool_registry.get_tool(step['tool'])
        if not tool:
            raise RuntimeError(f"Tool not found: {step['tool']}")

        context = {'database_module': None, 'llm_manager': self.llm_manager}
        return await tool.execute(step['params'], context)

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Validate migration step safety"""
        tool = self.tool_registry.get_tool(step['tool'])
        if not tool:
            return {'requires_approval': True, 'safe': False}

        return {
            'requires_approval': tool.requires_approval,
            'safe': True,
            'risk_level': tool.risk_level.value
        }


class PerformanceOptimizerAgent(BaseAgent):
    """Agent specialized in performance optimization"""

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """Create performance optimization workflow"""
        database = task.input_data.get('database', 'production')

        steps = [
            {
                'tool': 'analyze_schema',
                'params': {
                    'database': database,
                    'include_indexes': True,
                    'include_constraints': True
                },
                'rationale': 'Analyze current schema and indexes'
            }
        ]

        # Add optimizer tools if available
        if self.tool_registry.get_tool('analyze_slow_queries'):
            steps.append({
                'tool': 'analyze_slow_queries',
                'params': {
                    'database': database,
                    'threshold_ms': 1000,
                    'limit': 10,
                    'include_explain': True
                },
                'rationale': 'Identify slow queries'
            })

        if self.tool_registry.get_tool('recommend_indexes'):
            steps.append({
                'tool': 'recommend_indexes',
                'params': {
                    'database': database,
                    'min_impact_score': 0.7
                },
                'rationale': 'Get index recommendations'
            })

        return steps

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimization step"""
        tool = self.tool_registry.get_tool(step['tool'])
        if not tool:
            raise RuntimeError(f"Tool not found: {step['tool']}")

        context = {'database_module': None, 'llm_manager': self.llm_manager}
        return await tool.execute(step['params'], context)

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Validate optimization step safety"""
        tool = self.tool_registry.get_tool(step['tool'])
        if not tool:
            return {'requires_approval': False, 'safe': False}

        return {
            'requires_approval': tool.requires_approval,
            'safe': True,
            'risk_level': tool.risk_level.value
        }


class TestAgentToolIntegration:
    """Integration tests for agent-tool workflows"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def state_manager(self, temp_dir):
        """Create state manager"""
        return MockStateManager(storage_path=temp_dir)

    @pytest.fixture
    def tool_registry(self):
        """Create tool registry with all tools"""
        return create_default_registry()

    @pytest.fixture
    def llm_manager(self):
        """Create mock LLM manager"""
        return MockLLMManager()

    @pytest.mark.asyncio
    async def test_backup_workflow(self, state_manager, tool_registry, llm_manager, temp_dir):
        """Test complete backup workflow"""
        config = AgentConfig(
            agent_id="backup_agent",
            agent_type="backup",
            capabilities=[
                AgentCapability.DATABASE_READ,
                AgentCapability.BACKUP_CREATE,
                AgentCapability.SCHEMA_ANALYZE
            ],
            llm_config={},
            safety_level='moderate'
        )

        agent = DatabaseBackupAgent(
            config=config,
            llm_manager=llm_manager,
            tool_registry=tool_registry,
            state_manager=state_manager
        )

        task = TaskContext(
            task_id="backup_workflow_001",
            task_description="Create and validate database backup",
            input_data={
                'database': 'test_production',
                'destination': os.path.join(temp_dir, 'backup.sql.gz')
            }
        )

        result = await agent.run(task)

        # Verify workflow completed
        assert result.status == "success"
        assert len(result.actions_taken) == 3  # analyze + backup + validate

        # Verify all steps executed
        action_tools = [action['step']['tool'] for action in result.actions_taken]
        assert 'analyze_schema' in action_tools
        assert 'backup_database_full' in action_tools
        assert 'validate_backup' in action_tools

        # Verify output contains key data
        assert 'backup_path' in result.output_data
        assert 'valid' in result.output_data

    @pytest.mark.asyncio
    async def test_migration_planning_workflow(self, state_manager, tool_registry, llm_manager):
        """Test migration planning workflow"""
        config = AgentConfig(
            agent_id="migration_agent",
            agent_type="migration",
            capabilities=[
                AgentCapability.DATABASE_READ,
                AgentCapability.SCHEMA_ANALYZE,
                AgentCapability.SCHEMA_MODIFY
            ],
            llm_config={},
            safety_level='strict'
        )

        agent = MigrationPlannerAgent(
            config=config,
            llm_manager=llm_manager,
            tool_registry=tool_registry,
            state_manager=state_manager
        )

        task = TaskContext(
            task_id="migration_001",
            task_description="Plan migration to add email column",
            input_data={
                'database': 'production',
                'operation': 'add_column',
                'table': 'users',
                'details': {
                    'column_name': 'email',
                    'data_type': 'VARCHAR(255)',
                    'nullable': False,
                    'default': "''"
                }
            }
        )

        result = await agent.run(task)

        assert result.status == "success"
        assert len(result.actions_taken) >= 1  # At least schema analysis

        # Verify schema analysis happened
        first_action = result.actions_taken[0]
        assert first_action['step']['tool'] == 'analyze_schema'

    @pytest.mark.asyncio
    async def test_performance_optimization_workflow(self, state_manager, tool_registry, llm_manager):
        """Test performance optimization workflow"""
        config = AgentConfig(
            agent_id="optimizer_agent",
            agent_type="optimizer",
            capabilities=[
                AgentCapability.DATABASE_READ,
                AgentCapability.SCHEMA_ANALYZE,
                AgentCapability.QUERY_OPTIMIZE
            ],
            llm_config={},
            safety_level='moderate'
        )

        agent = PerformanceOptimizerAgent(
            config=config,
            llm_manager=llm_manager,
            tool_registry=tool_registry,
            state_manager=state_manager
        )

        task = TaskContext(
            task_id="optimization_001",
            task_description="Analyze and optimize database performance",
            input_data={
                'database': 'production'
            }
        )

        result = await agent.run(task)

        assert result.status == "success"
        assert len(result.actions_taken) >= 1

        # Verify schema analysis
        assert result.actions_taken[0]['step']['tool'] == 'analyze_schema'

    @pytest.mark.asyncio
    async def test_error_recovery(self, state_manager, tool_registry, llm_manager):
        """Test error recovery in multi-step workflow"""
        # Create agent that will fail on a specific step
        class ErrorProneAgent(DatabaseBackupAgent):
            async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
                # Fail on second step
                if step['tool'] == 'backup_database_full':
                    raise RuntimeError("Simulated backup failure")
                return await super().execute_step(step)

        config = AgentConfig(
            agent_id="error_agent",
            agent_type="backup",
            capabilities=[AgentCapability.DATABASE_READ, AgentCapability.BACKUP_CREATE],
            llm_config={},
            safety_level='moderate'
        )

        agent = ErrorProneAgent(
            config=config,
            llm_manager=llm_manager,
            tool_registry=tool_registry,
            state_manager=state_manager
        )

        task = TaskContext(
            task_id="error_recovery_001",
            task_description="Create backup (will fail)",
            input_data={'database': 'test_db'}
        )

        result = await agent.run(task)

        # Verify failure was handled
        assert result.status == "failure"
        assert result.error is not None
        assert "backup failure" in result.error.lower()

        # Verify partial execution
        assert len(result.actions_taken) >= 1  # Schema analysis succeeded

    @pytest.mark.asyncio
    async def test_checkpoint_and_recovery(self, state_manager, tool_registry, llm_manager, temp_dir):
        """Test checkpoint creation and recovery"""
        config = AgentConfig(
            agent_id="checkpoint_agent",
            agent_type="backup",
            capabilities=[
                AgentCapability.DATABASE_READ,
                AgentCapability.BACKUP_CREATE
            ],
            llm_config={},
            safety_level='moderate'
        )

        agent = DatabaseBackupAgent(
            config=config,
            llm_manager=llm_manager,
            tool_registry=tool_registry,
            state_manager=state_manager
        )

        task = TaskContext(
            task_id="checkpoint_001",
            task_description="Create backup with checkpoints",
            input_data={
                'database': 'test_db',
                'destination': os.path.join(temp_dir, 'checkpoint_backup.sql.gz')
            }
        )

        result = await agent.run(task)

        # Verify checkpoints were created
        assert len(result.checkpoints) > 0

        # Verify we can load checkpoint data
        plan_checkpoint = await state_manager.load_checkpoint("checkpoint_001", "plan_created")
        assert plan_checkpoint is not None
        assert 'plan' in plan_checkpoint
        assert len(plan_checkpoint['plan']) == 3  # analyze + backup + validate

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self, state_manager, tool_registry, llm_manager, temp_dir):
        """Test coordination between multiple agents"""
        # Agent 1: Create backup
        backup_config = AgentConfig(
            agent_id="backup_coordinator",
            agent_type="backup",
            capabilities=[AgentCapability.DATABASE_READ, AgentCapability.BACKUP_CREATE],
            llm_config={},
            safety_level='moderate'
        )

        backup_agent = DatabaseBackupAgent(
            config=backup_config,
            llm_manager=llm_manager,
            tool_registry=tool_registry,
            state_manager=state_manager
        )

        # Agent 2: Analyze schema
        analyzer_config = AgentConfig(
            agent_id="schema_analyzer",
            agent_type="analyzer",
            capabilities=[AgentCapability.DATABASE_READ, AgentCapability.SCHEMA_ANALYZE],
            llm_config={},
            safety_level='moderate'
        )

        # Create simple analysis agent
        class SchemaAnalyzerAgent(BaseAgent):
            async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
                return [{
                    'tool': 'analyze_schema',
                    'params': {
                        'database': task.input_data.get('database', 'test_db'),
                        'include_indexes': True,
                        'include_constraints': True
                    }
                }]

            async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
                tool = self.tool_registry.get_tool(step['tool'])
                return await tool.execute(step['params'], {})

            def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
                return {'requires_approval': False, 'safe': True, 'risk_level': 'safe'}

        analyzer_agent = SchemaAnalyzerAgent(
            config=analyzer_config,
            llm_manager=llm_manager,
            tool_registry=tool_registry,
            state_manager=state_manager
        )

        # Execute backup workflow
        backup_task = TaskContext(
            task_id="multi_agent_backup",
            task_description="Create backup",
            input_data={
                'database': 'coordination_db',
                'destination': os.path.join(temp_dir, 'coord_backup.sql.gz')
            }
        )

        backup_result = await backup_agent.run(backup_task)
        assert backup_result.status == "success"

        # Execute analysis workflow
        analysis_task = TaskContext(
            task_id="multi_agent_analysis",
            task_description="Analyze schema",
            input_data={'database': 'coordination_db'}
        )

        analysis_result = await analyzer_agent.run(analysis_task)
        assert analysis_result.status == "success"

        # Verify both workflows completed
        assert 'backup_path' in backup_result.output_data
        assert 'tables' in analysis_result.output_data

    @pytest.mark.asyncio
    async def test_tool_parameter_validation_in_workflow(self, state_manager, tool_registry, llm_manager):
        """Test that invalid tool parameters are caught during workflow"""
        class BadParametersAgent(BaseAgent):
            async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
                return [{
                    'tool': 'backup_database_full',
                    'params': {
                        # Missing required 'destination' parameter
                        'database': 'test_db'
                    }
                }]

            async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
                tool = self.tool_registry.get_tool(step['tool'])
                return await tool.execute(step['params'], {})

            def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
                return {'requires_approval': False, 'safe': True, 'risk_level': 'low'}

        config = AgentConfig(
            agent_id="bad_params_agent",
            agent_type="test",
            capabilities=[AgentCapability.BACKUP_CREATE],
            llm_config={},
            safety_level='moderate'
        )

        agent = BadParametersAgent(
            config=config,
            llm_manager=llm_manager,
            tool_registry=tool_registry,
            state_manager=state_manager
        )

        task = TaskContext(
            task_id="bad_params_001",
            task_description="Test bad parameters",
            input_data={}
        )

        result = await agent.run(task)

        # Should fail due to invalid parameters
        assert result.status == "failure"
        assert result.error is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
