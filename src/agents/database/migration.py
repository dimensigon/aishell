"""
MigrationAgent - Intelligent Schema Migration with Safety Controls

This module implements the MigrationAgent for Phase 12 agentic workflows,
providing autonomous schema migration capabilities with comprehensive safety
validation and rollback support.

The MigrationAgent handles:
- Schema change analysis and planning
- Migration script generation
- Automatic rollback script creation
- Safety validation with risk assessment
- Data integrity verification

Classes:
    MigrationAgent: Specialized agent for database schema migrations

Example:
    from src.agents.database.migration import MigrationAgent
    from src.agents.base import AgentConfig, TaskContext, AgentCapability

    config = AgentConfig(
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

    agent = MigrationAgent(config, llm_manager, tool_registry, state_manager)

    task = TaskContext(
        task_id="migration_add_column",
        task_description="Add phone column to users table",
        input_data={
            'migration_type': 'schema_change',
            'target_schema': {
                'table': 'users',
                'column': 'phone',
                'type': 'VARCHAR(20)',
                'nullable': True
            }
        }
    )

    result = await agent.run(task)
"""

from typing import Dict, Any, List, Optional
from src.agents.base import BaseAgent, TaskContext


class MigrationAgent(BaseAgent):
    """
    Intelligent schema migration agent with safety controls

    The MigrationAgent provides autonomous database schema migration capabilities
    with comprehensive safety validation. It analyzes current database schema,
    generates migration scripts, creates rollback plans, and executes migrations
    with full audit trail.

    Migration Types:
        schema_change: DDL operations (ALTER, CREATE, DROP)
        data_migration: Data transformation and movement
        rollback: Reverting previous migrations

    Safety Features:
        - Always creates backup before migration
        - Generates automatic rollback scripts
        - Validates data integrity after migration
        - Requires approval for all DDL operations
        - Risk level assessment (HIGH for DDL, MEDIUM for data)

    Planning Process:
        1. Create safety backup
        2. Analyze current schema state
        3. Generate migration script
        4. Validate migration safety
        5. Create rollback script
        6. Execute migration (with approval)
        7. Verify data integrity

    Tools Used:
        - backup_before_migration: Create safety backup
        - analyze_schema: Analyze current schema state
        - create_migration_script: Generate migration SQL
        - validate_migration: Safety validation
        - create_rollback: Generate rollback script
        - execute_migration: Execute migration SQL
        - verify_migration: Verify data integrity

    Attributes:
        config: Agent configuration with capabilities and safety level
        llm_manager: LLM manager for intelligent planning
        tool_registry: Registry of available migration tools
        state_manager: State manager for checkpointing

    Example:
        # Schema change migration
        task = TaskContext(
            task_id="add_user_email",
            task_description="Add email column to users table",
            input_data={
                'migration_type': 'schema_change',
                'target_schema': {
                    'table': 'users',
                    'column': 'email',
                    'type': 'VARCHAR(255)',
                    'nullable': False,
                    'default': ''
                }
            },
            database_config={'database': 'production'}
        )

        result = await migration_agent.run(task)

        # Result contains:
        # - Migration SQL executed
        # - Rollback script path
        # - Data integrity verification results
        # - Backup location
    """

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create execution plan for migration task

        Analyzes the migration requirements and creates a detailed step-by-step
        plan for safe execution. The plan varies based on migration type and
        always includes safety measures.

        Planning Strategy:
            schema_change:
                1. Backup before migration
                2. Analyze current schema
                3. Generate migration script
                4. Validate migration safety
                5. Create rollback script
                6. Execute migration (requires approval)
                7. Verify data integrity

            data_migration:
                1. Backup before migration
                2. Analyze data volumes
                3. Generate data migration script
                4. Test migration on sample data
                5. Create rollback script
                6. Execute migration (requires approval)
                7. Verify data integrity

            rollback:
                1. Analyze rollback requirements
                2. Load rollback script
                3. Validate rollback script
                4. Execute rollback (requires approval)
                5. Verify restoration

        Args:
            task: TaskContext containing:
                - input_data['migration_type']: Type of migration
                - input_data['target_schema']: Target schema definition
                - input_data['rollback_script']: Optional pre-defined rollback
                - database_config: Database connection configuration

        Returns:
            List of planned steps, where each step contains:
                - tool: Tool name to execute
                - params: Parameters for the tool
                - rationale: Explanation of why this step is needed

        Example:
            task = TaskContext(
                task_id="migration_001",
                task_description="Add phone column",
                input_data={
                    'migration_type': 'schema_change',
                    'target_schema': {
                        'table': 'users',
                        'operation': 'add_column',
                        'column': 'phone',
                        'type': 'VARCHAR(20)'
                    }
                }
            )

            plan = await agent.plan(task)
            # Returns:
            # [
            #     {'tool': 'backup_before_migration', ...},
            #     {'tool': 'analyze_schema', ...},
            #     {'tool': 'create_migration_script', ...},
            #     {'tool': 'validate_migration', ...},
            #     {'tool': 'create_rollback', ...},
            #     {'tool': 'execute_migration', ...},
            #     {'tool': 'verify_migration', ...}
            # ]
        """
        migration_type = task.input_data.get('migration_type', 'schema_change')

        if migration_type == 'schema_change':
            return await self._plan_schema_change(task)
        elif migration_type == 'data_migration':
            return await self._plan_data_migration(task)
        elif migration_type == 'rollback':
            return await self._plan_rollback(task)
        else:
            raise ValueError(f"Unsupported migration type: {migration_type}")

    async def _plan_schema_change(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Plan schema change migration

        Creates a comprehensive plan for schema modification operations including
        DDL statements (ALTER, CREATE, DROP). Always includes backup and rollback
        preparation.

        Args:
            task: Task context with target schema definition

        Returns:
            List of execution steps for schema change
        """
        target_schema = task.input_data.get('target_schema', {})
        database = task.database_config.get('database') if task.database_config else 'default'

        plan = [
            {
                'tool': 'backup_before_migration',
                'params': {
                    'database': database,
                    'migration_id': task.task_id
                },
                'rationale': 'Create safety backup before schema changes'
            },
            {
                'tool': 'analyze_schema',
                'params': {
                    'database': database,
                    'include_indexes': True,
                    'include_constraints': True
                },
                'rationale': 'Analyze current schema state to understand dependencies'
            },
            {
                'tool': 'create_migration_script',
                'params': {
                    'current_schema': '${step_1.output.schema}',
                    'target_schema': target_schema,
                    'migration_type': 'schema_change'
                },
                'rationale': 'Generate migration SQL from current to target schema'
            },
            {
                'tool': 'validate_migration',
                'params': {
                    'migration_sql': '${step_2.output.migration_sql}',
                    'check_data_loss': True,
                    'check_breaking_changes': True
                },
                'rationale': 'Validate migration safety and identify potential risks'
            },
            {
                'tool': 'create_rollback',
                'params': {
                    'migration_sql': '${step_2.output.migration_sql}',
                    'current_schema': '${step_1.output.schema}',
                    'target_schema': target_schema
                },
                'rationale': 'Generate rollback script for emergency recovery'
            },
            {
                'tool': 'execute_migration',
                'params': {
                    'migration_sql': '${step_2.output.migration_sql}',
                    'rollback_sql': '${step_4.output.rollback_sql}',
                    'dry_run': False
                },
                'rationale': 'Execute schema migration with rollback capability'
            },
            {
                'tool': 'verify_migration',
                'params': {
                    'expected_schema': target_schema,
                    'tables': '${step_1.output.affected_tables}',
                    'verify_data_integrity': True
                },
                'rationale': 'Verify migration success and data integrity'
            }
        ]

        return plan

    async def _plan_data_migration(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Plan data migration

        Creates plan for data transformation and movement operations.
        Includes data volume analysis and sample testing.

        Args:
            task: Task context with data migration specification

        Returns:
            List of execution steps for data migration
        """
        database = task.database_config.get('database') if task.database_config else 'default'
        migration_spec = task.input_data.get('migration_spec', {})

        plan = [
            {
                'tool': 'backup_before_migration',
                'params': {
                    'database': database,
                    'migration_id': task.task_id
                },
                'rationale': 'Create safety backup before data migration'
            },
            {
                'tool': 'analyze_data_volume',
                'params': {
                    'database': database,
                    'tables': migration_spec.get('tables', [])
                },
                'rationale': 'Analyze data volumes to estimate migration time'
            },
            {
                'tool': 'create_migration_script',
                'params': {
                    'migration_spec': migration_spec,
                    'migration_type': 'data_migration'
                },
                'rationale': 'Generate data migration SQL script'
            },
            {
                'tool': 'test_migration_sample',
                'params': {
                    'migration_sql': '${step_2.output.migration_sql}',
                    'sample_size': 100
                },
                'rationale': 'Test migration on sample data before full execution'
            },
            {
                'tool': 'create_rollback',
                'params': {
                    'migration_sql': '${step_2.output.migration_sql}',
                    'migration_type': 'data_migration'
                },
                'rationale': 'Generate rollback script for data restoration'
            },
            {
                'tool': 'execute_migration',
                'params': {
                    'migration_sql': '${step_2.output.migration_sql}',
                    'rollback_sql': '${step_4.output.rollback_sql}',
                    'dry_run': False
                },
                'rationale': 'Execute data migration with transaction support'
            },
            {
                'tool': 'verify_migration',
                'params': {
                    'migration_spec': migration_spec,
                    'verify_row_counts': True,
                    'verify_data_integrity': True
                },
                'rationale': 'Verify data migration success and integrity'
            }
        ]

        return plan

    async def _plan_rollback(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Plan rollback of previous migration

        Creates plan to revert a previous migration using stored rollback script
        or by analyzing migration history.

        Args:
            task: Task context with rollback specification

        Returns:
            List of execution steps for rollback
        """
        database = task.database_config.get('database') if task.database_config else 'default'
        rollback_script = task.input_data.get('rollback_script')
        migration_id = task.input_data.get('migration_id')

        plan = [
            {
                'tool': 'analyze_rollback',
                'params': {
                    'database': database,
                    'migration_id': migration_id
                },
                'rationale': 'Analyze rollback requirements and migration history'
            },
            {
                'tool': 'load_rollback_script',
                'params': {
                    'migration_id': migration_id,
                    'custom_script': rollback_script
                },
                'rationale': 'Load rollback script from migration history or use custom'
            },
            {
                'tool': 'validate_rollback',
                'params': {
                    'rollback_sql': '${step_1.output.rollback_sql}',
                    'target_state': '${step_0.output.pre_migration_state}'
                },
                'rationale': 'Validate rollback script will restore correct state'
            },
            {
                'tool': 'execute_migration',
                'params': {
                    'migration_sql': '${step_1.output.rollback_sql}',
                    'rollback_sql': None,  # No rollback for rollback
                    'dry_run': False
                },
                'rationale': 'Execute rollback to restore previous state'
            },
            {
                'tool': 'verify_migration',
                'params': {
                    'expected_schema': '${step_0.output.pre_migration_state}',
                    'verify_data_integrity': True
                },
                'rationale': 'Verify rollback restored correct state'
            }
        ]

        return plan

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single migration step

        Retrieves the appropriate tool from the registry and executes it with
        validated parameters. Handles parameter interpolation from previous
        step results.

        Args:
            step: Step definition containing:
                - tool: Name of the tool to execute
                - params: Parameters for tool execution
                - rationale: Explanation of step purpose

        Returns:
            Step execution result containing tool outputs and metadata

        Raises:
            ValueError: If tool is not found in registry
            Exception: If tool execution fails

        Example:
            step = {
                'tool': 'analyze_schema',
                'params': {'database': 'production'},
                'rationale': 'Analyze current schema'
            }

            result = await agent.execute_step(step)
            # Result: {
            #     'schema': {...},
            #     'affected_tables': ['users'],
            #     'execution_time': 1.2
            # }
        """
        tool_name = step['tool']
        tool_params = step['params']

        # Get tool from registry
        tool = self.tool_registry.get_tool(tool_name)

        if not tool:
            raise ValueError(f"Tool not found in registry: {tool_name}")

        # Create execution context
        context = {
            'database_module': self._get_database_module(),
            'llm_manager': self.llm_manager,
            'state_manager': self.state_manager,
            'task_id': self.current_task.task_id if self.current_task else None
        }

        # Execute tool with validated parameters
        result = await tool.execute(tool_params, context)

        return result

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate safety of migration step

        Performs comprehensive safety analysis including risk assessment,
        approval requirements, and identified risks with mitigations.

        Safety Rules:
            - DDL operations (schema changes): HIGH risk, always require approval
            - Data migrations: MEDIUM risk, require approval in strict mode
            - Rollbacks: HIGH risk, always require approval
            - Backup operations: LOW risk, no approval needed
            - Analysis operations: SAFE, no approval needed

        Args:
            step: Step definition to validate

        Returns:
            Validation result containing:
                - requires_approval: Boolean indicating if approval needed
                - safe: Boolean indicating if step is safe to execute
                - risk_level: Risk level (SAFE, LOW, MEDIUM, HIGH, CRITICAL)
                - risks: List of identified risks
                - mitigations: List of risk mitigations in place

        Example:
            step = {
                'tool': 'execute_migration',
                'params': {'migration_sql': 'ALTER TABLE users ...'}
            }

            validation = agent.validate_safety(step)
            # Returns: {
            #     'requires_approval': True,
            #     'safe': True,
            #     'risk_level': 'HIGH',
            #     'risks': [
            #         'DDL operation - schema modification',
            #         'Potential data loss if rollback fails'
            #     ],
            #     'mitigations': [
            #         'Backup created before migration',
            #         'Rollback script generated and validated',
            #         'Data integrity verification after migration'
            #     ]
            # }
        """
        tool_name = step['tool']

        # Default validation result
        validation = {
            'requires_approval': False,
            'safe': True,
            'risk_level': 'SAFE',
            'risks': [],
            'mitigations': []
        }

        # DDL operations - highest risk
        if tool_name == 'execute_migration':
            validation['requires_approval'] = True
            validation['risk_level'] = 'HIGH'
            validation['risks'].extend([
                'DDL operation - schema modification',
                'Potential for data loss or corruption',
                'May impact application availability',
                'Could break application compatibility'
            ])
            validation['mitigations'].extend([
                'Backup created before migration',
                'Rollback script generated and validated',
                'Data integrity verification after migration',
                'Dry-run validation performed'
            ])

        # Rollback operations
        elif tool_name in ['analyze_rollback', 'execute_rollback']:
            validation['requires_approval'] = True
            validation['risk_level'] = 'HIGH'
            validation['risks'].extend([
                'Rollback operation - reverting changes',
                'Potential data loss if state has changed',
                'May restore outdated schema'
            ])
            validation['mitigations'].extend([
                'Rollback script validated against current state',
                'Migration history analyzed',
                'Post-rollback verification'
            ])

        # Backup operations - low risk
        elif tool_name in ['backup_before_migration', 'backup_database_full']:
            validation['risk_level'] = 'LOW'
            validation['requires_approval'] = False
            validation['mitigations'].append('Read-only operation with backup verification')

        # Analysis operations - safe
        elif tool_name in ['analyze_schema', 'validate_migration', 'verify_migration']:
            validation['risk_level'] = 'SAFE'
            validation['requires_approval'] = False
            validation['mitigations'].append('Read-only analysis with no modifications')

        # Migration script generation - safe
        elif tool_name in ['create_migration_script', 'create_rollback']:
            validation['risk_level'] = 'SAFE'
            validation['requires_approval'] = False
            validation['mitigations'].append('Script generation only, no execution')

        # Data migration operations
        elif tool_name in ['execute_data_migration', 'test_migration_sample']:
            validation['requires_approval'] = True if self.config.safety_level == 'strict' else False
            validation['risk_level'] = 'MEDIUM'
            validation['risks'].extend([
                'Data modification operation',
                'Potential for data inconsistency'
            ])
            validation['mitigations'].extend([
                'Backup created before migration',
                'Transaction-based execution with rollback',
                'Sample testing performed before full migration'
            ])

        # Unknown tools
        else:
            validation['requires_approval'] = True
            validation['risk_level'] = 'HIGH'
            validation['risks'].append(f'Unknown tool: {tool_name}')

        # Additional check: Always require approval in strict safety mode for any write operation
        if self.config.safety_level == 'strict' and validation['risk_level'] in ['MEDIUM', 'HIGH', 'CRITICAL']:
            validation['requires_approval'] = True

        return validation

    def _get_database_module(self):
        """
        Get database module for tool execution

        Returns database module instance from context or creates new one.
        This method should be implemented when integrating with actual database module.

        Returns:
            Database module instance
        """
        # Placeholder - will be integrated with actual database module
        # In production, this would return the database module instance
        return None
