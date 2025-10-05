"""
BackupAgent - Automated Database Backup and Restoration

This module provides the BackupAgent class for autonomous database backup
operations with intelligent planning, safety validation, and integrity checking.

The BackupAgent supports:
- Full database backups
- Incremental backups
- Backup restoration
- Automated validation and integrity checking
- Compression and size estimation

Classes:
    BackupAgent: Specialized agent for database backup operations
"""

from typing import Dict, Any, List, Optional
from ..base import (
    BaseAgent,
    AgentConfig,
    TaskContext,
    AgentCapability
)


class BackupAgent(BaseAgent):
    """
    Automated database backup agent with intelligent scheduling and validation

    The BackupAgent provides autonomous execution of database backup workflows
    including full backups, incremental backups, and restoration operations.
    It automatically validates backup integrity and manages retention policies.

    Capabilities:
    - Full database backups
    - Incremental/differential backups
    - Point-in-time recovery preparation
    - Backup integrity validation
    - Automated retention management
    - Compression and size estimation

    Tools Used:
    - backup_database_full: Create full backup
    - backup_database_incremental: Create incremental backup
    - validate_backup: Verify backup integrity
    - list_backups: List available backups
    - restore_backup: Restore from backup (requires approval)
    - calculate_backup_size: Estimate backup size
    - compress_backup: Compress backup files

    Safety Levels:
    - Full backups: Low risk, no approval needed
    - Restore operations: High risk, requires approval
    - Cleanup operations: Medium risk, requires approval if deleting recent backups

    Example:
        config = AgentConfig(
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

        agent = BackupAgent(config, llm_manager, tool_registry, state_manager)

        task = TaskContext(
            task_id="backup_task_001",
            task_description="Create full backup of production database",
            input_data={
                'backup_type': 'full',
                'destination': '/backups/prod',
                'compression': True,
                'cleanup_old': True,
                'retention_days': 30
            },
            database_config={'database': 'production', 'host': 'localhost'}
        )

        result = await agent.run(task)
    """

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create execution plan for backup task

        Analyzes the task requirements and creates a detailed execution plan
        based on the backup type. The plan includes size calculation, backup
        execution, validation, compression, and optional cleanup steps.

        Plan Generation Logic:
        - Full backup: calculate size → create backup → compress → validate
        - Incremental backup: calculate size → create incremental → compress → validate
        - Restore: verify backup exists → restore → verify integrity
        - Cleanup: list backups → filter by retention → cleanup old backups

        Args:
            task: TaskContext containing:
                - input_data['backup_type']: Type of backup ('full', 'incremental', 'restore')
                - input_data['destination']: Backup destination path
                - input_data['compression']: Enable compression (default: True)
                - input_data['cleanup_old']: Enable old backup cleanup (default: False)
                - input_data['retention_days']: Retention period in days (default: 30)
                - input_data['backup_path']: Path for restore operations
                - database_config['database']: Database name

        Returns:
            List of planned steps, each containing:
            - tool: Tool name to execute
            - params: Tool parameters
            - rationale: Explanation of the step (optional)

        Example:
            # Full backup plan
            [
                {
                    'tool': 'calculate_backup_size',
                    'params': {'database': 'production'},
                    'rationale': 'Estimate backup size for storage planning'
                },
                {
                    'tool': 'backup_database_full',
                    'params': {
                        'database': 'production',
                        'destination': '/backups/prod.sql',
                        'compression': True
                    },
                    'rationale': 'Create full database backup with compression'
                },
                {
                    'tool': 'validate_backup',
                    'params': {'backup_path': '${step_1.output.backup_path}'},
                    'rationale': 'Verify backup integrity and completeness'
                }
            ]
        """
        backup_type = task.input_data.get('backup_type', 'full')
        database = task.database_config.get('database') if task.database_config else 'unknown'

        plan = []

        if backup_type == 'full':
            # Full backup workflow
            plan = [
                {
                    'tool': 'calculate_backup_size',
                    'params': {'database': database},
                    'rationale': 'Estimate backup size for storage planning'
                },
                {
                    'tool': 'backup_database_full',
                    'params': {
                        'database': database,
                        'destination': task.input_data.get('destination'),
                        'compression': task.input_data.get('compression', True)
                    },
                    'rationale': 'Create full database backup with compression'
                },
                {
                    'tool': 'validate_backup',
                    'params': {'backup_path': '${step_1.output.backup_path}'},
                    'rationale': 'Verify backup integrity and completeness'
                }
            ]

        elif backup_type == 'incremental':
            # Incremental backup workflow
            plan = [
                {
                    'tool': 'calculate_backup_size',
                    'params': {'database': database, 'incremental': True},
                    'rationale': 'Estimate incremental backup size'
                },
                {
                    'tool': 'backup_database_incremental',
                    'params': {
                        'database': database,
                        'destination': task.input_data.get('destination'),
                        'compression': task.input_data.get('compression', True),
                        'base_backup': task.input_data.get('base_backup')
                    },
                    'rationale': 'Create incremental backup based on last full backup'
                },
                {
                    'tool': 'validate_backup',
                    'params': {'backup_path': '${step_1.output.backup_path}'},
                    'rationale': 'Verify incremental backup integrity'
                }
            ]

        elif backup_type == 'restore':
            # Restore workflow
            backup_path = task.input_data.get('backup_path')
            plan = [
                {
                    'tool': 'validate_backup',
                    'params': {'backup_path': backup_path},
                    'rationale': 'Verify backup exists and is valid before restore'
                },
                {
                    'tool': 'restore_backup',
                    'params': {
                        'backup_path': backup_path,
                        'database': database,
                        'overwrite': task.input_data.get('overwrite', False)
                    },
                    'rationale': 'Restore database from backup'
                },
                {
                    'tool': 'verify_data_integrity',
                    'params': {'database': database},
                    'rationale': 'Verify data integrity after restoration'
                }
            ]

        # Add retention cleanup if configured
        if task.input_data.get('cleanup_old', False):
            retention_days = task.input_data.get('retention_days', 30)
            plan.append({
                'tool': 'cleanup_old_backups',
                'params': {
                    'backup_directory': task.input_data.get('destination'),
                    'retention_days': retention_days
                },
                'rationale': f'Remove backups older than {retention_days} days'
            })

        return plan

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single backup operation step

        Retrieves the appropriate tool from the tool registry and executes it
        with the provided parameters. Handles variable substitution for
        dependencies between steps (e.g., using output from previous steps).

        Args:
            step: Step definition containing:
                - tool: Tool name to execute
                - params: Tool parameters (may contain variable references)
                - rationale: Step explanation (optional)

        Returns:
            Step execution result containing tool outputs and metadata

        Raises:
            ValueError: If tool is not found in registry
            Exception: If tool execution fails

        Example:
            step = {
                'tool': 'backup_database_full',
                'params': {
                    'database': 'production',
                    'destination': '/backups/prod.sql.gz',
                    'compression': True
                }
            }
            result = await self.execute_step(step)
            # result = {
            #     'backup_path': '/backups/prod.sql.gz',
            #     'size_bytes': 1024000,
            #     'duration_seconds': 45.2,
            #     'checksum': 'abc123...'
            # }
        """
        tool_name = step['tool']
        params = step['params']

        # Get tool from registry
        tool = self.tool_registry.get_tool(tool_name)

        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry")

        # Execute tool with parameters
        # Context should include database module, current task, etc.
        context = {
            'agent_id': self.config.agent_id,
            'task_id': self.current_task.task_id if self.current_task else None,
            'database_config': self.current_task.database_config if self.current_task else None,
            'llm_manager': self.llm_manager
        }

        result = await tool.execute(params, context)

        return result

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate safety of backup operation step

        Assesses the risk level of the planned step and determines if human
        approval is required based on the operation type and agent safety level.

        Safety Rules:
        - Full/incremental backups: Low risk, no approval needed
        - Backup validation: Safe, no approval needed
        - Restore operations: High risk, always requires approval
        - Cleanup operations: Medium risk, requires approval if deleting backups < 7 days old
        - Size calculation: Safe, no approval needed

        Args:
            step: Step definition to validate

        Returns:
            Validation result containing:
            - requires_approval: Boolean indicating if approval is needed
            - safe: Boolean indicating if step is safe to execute
            - risk_level: Risk level ('safe', 'low', 'medium', 'high', 'critical')
            - risks: List of identified risks
            - mitigations: List of risk mitigation measures

        Example:
            step = {'tool': 'restore_backup', 'params': {...}}
            validation = self.validate_safety(step)
            # validation = {
            #     'requires_approval': True,
            #     'safe': True,
            #     'risk_level': 'high',
            #     'risks': [
            #         'Will overwrite existing database',
            #         'Data loss possible if backup is corrupted'
            #     ],
            #     'mitigations': [
            #         'Backup validated before restore',
            #         'Integrity check after restore'
            #     ]
            # }
        """
        tool_name = step['tool']
        params = step['params']

        # Default validation result
        validation = {
            'requires_approval': False,
            'safe': True,
            'risk_level': 'safe',
            'risks': [],
            'mitigations': []
        }

        # Safe operations (read-only or low risk)
        safe_tools = [
            'calculate_backup_size',
            'list_backups',
            'validate_backup'
        ]

        if tool_name in safe_tools:
            validation['risk_level'] = 'safe'
            return validation

        # Low risk backup creation operations
        if tool_name in ['backup_database_full', 'backup_database_incremental', 'compress_backup']:
            validation['risk_level'] = 'low'
            validation['risks'] = ['Disk space consumption', 'Potential performance impact']
            validation['mitigations'] = [
                'Size calculated before backup',
                'Compression enabled to save space'
            ]

            # No approval needed for backups
            validation['requires_approval'] = False
            return validation

        # High risk restore operations
        if tool_name == 'restore_backup':
            validation['risk_level'] = 'high'
            validation['requires_approval'] = True
            validation['risks'] = [
                'Will overwrite existing database',
                'Data loss possible if backup is corrupted',
                'Service disruption during restore'
            ]
            validation['mitigations'] = [
                'Backup validated before restore',
                'Integrity check after restore',
                'Current state should be backed up first'
            ]

            # Always require approval for restore
            return validation

        # Medium risk cleanup operations
        if tool_name == 'cleanup_old_backups':
            retention_days = params.get('retention_days', 30)
            validation['risk_level'] = 'medium'
            validation['risks'] = [
                'Permanent deletion of backup files',
                'Potential loss of recovery points'
            ]
            validation['mitigations'] = [
                f'Only deleting backups older than {retention_days} days',
                'Recent backups are preserved'
            ]

            # Require approval if deleting backups less than 7 days old
            if retention_days < 7:
                validation['requires_approval'] = True
                validation['risk_level'] = 'high'
                validation['risks'].append('Deleting very recent backups (< 7 days)')
            else:
                # Check safety level for moderate risk operations
                if self.config.safety_level == 'strict':
                    validation['requires_approval'] = True
                else:
                    validation['requires_approval'] = False

            return validation

        # Unknown tool - require approval for safety
        validation['risk_level'] = 'unknown'
        validation['requires_approval'] = True
        validation['risks'] = ['Unknown operation type']
        validation['mitigations'] = ['Manual review required']

        return validation

    def _aggregate_results(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results from backup workflow actions

        Combines results from all backup steps into a cohesive summary,
        including backup paths, sizes, checksums, and operation statistics.

        Args:
            actions: List of executed action results

        Returns:
            Aggregated output data with backup summary information

        Example:
            aggregated = {
                'actions_count': 3,
                'backup_type': 'full',
                'backup_path': '/backups/prod.sql.gz',
                'size_bytes': 1024000,
                'size_mb': 1.0,
                'duration_seconds': 45.2,
                'checksum': 'abc123...',
                'validation_status': 'passed',
                'compression_ratio': 0.65
            }
        """
        aggregated = {
            'actions_count': len(actions),
            'backup_type': self.current_task.input_data.get('backup_type', 'unknown') if self.current_task else 'unknown'
        }

        # Extract key backup information from actions
        for action in actions:
            if 'result' in action and isinstance(action['result'], dict):
                result = action['result']

                # Backup path and size
                if 'backup_path' in result:
                    aggregated['backup_path'] = result['backup_path']

                if 'size_bytes' in result:
                    aggregated['size_bytes'] = result['size_bytes']
                    aggregated['size_mb'] = round(result['size_bytes'] / (1024 * 1024), 2)

                # Duration and performance
                if 'duration_seconds' in result:
                    aggregated['duration_seconds'] = result['duration_seconds']

                # Checksum and validation
                if 'checksum' in result:
                    aggregated['checksum'] = result['checksum']

                if 'validation_status' in result:
                    aggregated['validation_status'] = result['validation_status']

                # Compression information
                if 'compression_ratio' in result:
                    aggregated['compression_ratio'] = result['compression_ratio']

                # Cleanup results
                if 'deleted_count' in result:
                    aggregated['cleaned_up_backups'] = result['deleted_count']

                # Restore results
                if 'restore_status' in result:
                    aggregated['restore_status'] = result['restore_status']

                if 'integrity_check' in result:
                    aggregated['integrity_check'] = result['integrity_check']

        return aggregated
