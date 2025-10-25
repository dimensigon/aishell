"""
Migration Tools for Database Schema Changes

Provides tools for creating, executing, and verifying database migrations
with rollback capabilities and safety checks.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib


async def create_migration_script(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a migration script with rollback capabilities.

    Args:
        params: Migration parameters
            - operation: str (add_column, drop_column, add_index, etc.)
            - table: str
            - details: Dict (column_name, data_type, constraints, etc.)
        context: Execution context

    Returns:
        Dict containing:
            - migration_sql: SQL for forward migration
            - rollback_sql: SQL for rollback
            - estimated_duration: Estimated execution time
            - safety_warnings: List of warnings
    """
    # Validate parameters
    required = ['operation', 'table', 'details']
    missing = [p for p in required if p not in params]
    if missing:
        raise ValueError(f"Missing required parameters: {missing}")

    operation = params['operation']
    table = params['table']
    details = params['details']

    # Simulate migration script generation
    await asyncio.sleep(0.1)

    migration_sql = ""
    rollback_sql = ""
    warnings = []

    if operation == 'add_column':
        column_name = details.get('column_name')
        data_type = details.get('data_type')
        nullable = details.get('nullable', True)
        default = details.get('default')

        null_clause = "NULL" if nullable else "NOT NULL"
        default_clause = f"DEFAULT {default}" if default else ""

        migration_sql = f"""
-- Add column {column_name} to {table}
ALTER TABLE {table}
ADD COLUMN {column_name} {data_type} {null_clause} {default_clause};
""".strip()

        rollback_sql = f"""
-- Remove column {column_name} from {table}
ALTER TABLE {table}
DROP COLUMN {column_name};
""".strip()

        if not nullable and not default:
            warnings.append("Adding NOT NULL column without default may fail on non-empty table")

    elif operation == 'drop_column':
        column_name = details.get('column_name')

        migration_sql = f"""
-- Drop column {column_name} from {table}
ALTER TABLE {table}
DROP COLUMN {column_name};
""".strip()

        rollback_sql = f"""
-- Note: Cannot restore dropped column data
-- Manual intervention required for rollback
""".strip()

        warnings.append("Dropping column is irreversible - data will be lost")

    elif operation == 'add_index':
        index_name = details.get('index_name')
        columns = details.get('columns', [])
        unique = details.get('unique', False)

        unique_clause = "UNIQUE" if unique else ""
        columns_str = ", ".join(columns)

        migration_sql = f"""
-- Create index {index_name} on {table}
CREATE {unique_clause} INDEX {index_name}
ON {table} ({columns_str});
""".strip()

        rollback_sql = f"""
-- Drop index {index_name}
DROP INDEX {index_name};
""".strip()

    elif operation == 'rename_column':
        old_name = details.get('old_name')
        new_name = details.get('new_name')

        migration_sql = f"""
-- Rename column {old_name} to {new_name} in {table}
ALTER TABLE {table}
RENAME COLUMN {old_name} TO {new_name};
""".strip()

        rollback_sql = f"""
-- Rename column {new_name} back to {old_name} in {table}
ALTER TABLE {table}
RENAME COLUMN {new_name} TO {old_name};
""".strip()

    elif operation == 'modify_column':
        column_name = details.get('column_name')
        new_type = details.get('new_type')
        using_clause = details.get('using_clause', '')

        using = f"USING {using_clause}" if using_clause else ""

        migration_sql = f"""
-- Modify column {column_name} in {table}
ALTER TABLE {table}
ALTER COLUMN {column_name} TYPE {new_type} {using};
""".strip()

        rollback_sql = f"""
-- Note: Type conversion may not be reversible
-- Manual intervention may be required
""".strip()

        warnings.append("Type conversion may lose data precision")

    else:
        raise ValueError(f"Unsupported operation: {operation}")

    # Estimate duration based on operation
    duration_map = {
        'add_column': '< 1 second',
        'drop_column': '< 1 second',
        'add_index': '5-30 seconds',
        'rename_column': '< 1 second',
        'modify_column': '10-60 seconds'
    }

    return {
        'migration_sql': migration_sql,
        'rollback_sql': rollback_sql,
        'estimated_duration': duration_map.get(operation, '< 5 seconds'),
        'safety_warnings': warnings,
        'operation': operation,
        'table': table,
        'checksum': hashlib.md5(migration_sql.encode()).hexdigest()
    }


async def execute_migration(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a migration script with safety checks.

    Args:
        params: Execution parameters
            - migration_sql: str
            - dry_run: bool (default: True)
            - use_transaction: bool (default: True)
            - timeout: int (seconds, default: 300)
        context: Execution context

    Returns:
        Dict containing:
            - success: bool
            - rows_affected: int
            - execution_time: float (seconds)
            - rollback_point: str (transaction ID)
            - output: str
    """
    # Validate parameters
    if 'migration_sql' not in params:
        raise ValueError("Missing required parameter: migration_sql")

    migration_sql = params['migration_sql']
    dry_run = params.get('dry_run', True)
    use_transaction = params.get('use_transaction', True)
    timeout = params.get('timeout', 300)

    start_time = datetime.now()

    # Simulate migration execution
    await asyncio.sleep(0.2)

    if dry_run:
        output = f"""
DRY RUN - No changes made
=========================
SQL to be executed:
{migration_sql}

Estimated changes: 0-1000 rows
Transaction: {'ENABLED' if use_transaction else 'DISABLED'}
Timeout: {timeout}s
""".strip()

        execution_time = (datetime.now() - start_time).total_seconds()

        return {
            'success': True,
            'rows_affected': 0,
            'execution_time': execution_time,
            'rollback_point': None,
            'output': output,
            'dry_run': True
        }

    # Simulate actual execution
    rollback_point = f"txn_{datetime.now().timestamp()}"
    rows_affected = 0

    # Parse SQL to estimate rows affected
    if 'ALTER TABLE' in migration_sql.upper():
        rows_affected = 1  # Schema changes
    elif 'CREATE INDEX' in migration_sql.upper():
        rows_affected = 0  # Index creation

    execution_time = (datetime.now() - start_time).total_seconds()

    output = f"""
Migration executed successfully
==============================
Rows affected: {rows_affected}
Execution time: {execution_time:.3f}s
Transaction: {rollback_point if use_transaction else 'N/A'}

{migration_sql}
""".strip()

    return {
        'success': True,
        'rows_affected': rows_affected,
        'execution_time': execution_time,
        'rollback_point': rollback_point if use_transaction else None,
        'output': output,
        'dry_run': False
    }


async def verify_migration(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify that a migration was applied correctly.

    Args:
        params: Verification parameters
            - table: str
            - expected_changes: Dict (columns, indexes, constraints)
        context: Execution context

    Returns:
        Dict containing:
            - verified: bool
            - actual_schema: Dict
            - issues: List[str]
            - recommendations: List[str]
    """
    # Validate parameters
    required = ['table', 'expected_changes']
    missing = [p for p in required if p not in params]
    if missing:
        raise ValueError(f"Missing required parameters: {missing}")

    table = params['table']
    expected_changes = params['expected_changes']

    # Simulate schema verification
    await asyncio.sleep(0.15)

    # Mock actual schema
    actual_schema = {
        'columns': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
            {'name': 'name', 'type': 'VARCHAR(255)', 'nullable': False},
            {'name': 'email', 'type': 'VARCHAR(255)', 'nullable': True},
            {'name': 'created_at', 'type': 'TIMESTAMP', 'nullable': False}
        ],
        'indexes': [
            {'name': 'pk_id', 'columns': ['id'], 'unique': True},
            {'name': 'idx_email', 'columns': ['email'], 'unique': False}
        ],
        'constraints': [
            {'name': 'pk_id', 'type': 'PRIMARY KEY', 'columns': ['id']}
        ]
    }

    issues = []
    recommendations = []

    # Verify expected columns
    if 'columns' in expected_changes:
        expected_cols = {col['name']: col for col in expected_changes['columns']}
        actual_cols = {col['name']: col for col in actual_schema['columns']}

        for col_name, col_def in expected_cols.items():
            if col_name not in actual_cols:
                issues.append(f"Missing column: {col_name}")
            else:
                actual_col = actual_cols[col_name]
                if actual_col['type'] != col_def['type']:
                    issues.append(f"Column {col_name} type mismatch: expected {col_def['type']}, got {actual_col['type']}")

    # Verify expected indexes
    if 'indexes' in expected_changes:
        expected_idx = {idx['name']: idx for idx in expected_changes['indexes']}
        actual_idx = {idx['name']: idx for idx in actual_schema['indexes']}

        for idx_name, idx_def in expected_idx.items():
            if idx_name not in actual_idx:
                issues.append(f"Missing index: {idx_name}")
                recommendations.append(f"Create index: CREATE INDEX {idx_name} ON {table}({', '.join(idx_def['columns'])})")

    # Check for unnecessary indexes
    if len(actual_schema['indexes']) > 10:
        recommendations.append("Consider removing unused indexes to improve write performance")

    verified = len(issues) == 0

    return {
        'verified': verified,
        'actual_schema': actual_schema,
        'issues': issues,
        'recommendations': recommendations,
        'table': table,
        'verification_timestamp': datetime.now().isoformat()
    }


async def generate_rollback_script(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a rollback script for a migration with safety checks.

    Args:
        params: Rollback parameters
            - migration_sql: str (original migration SQL)
            - migration_type: str (optional, for better analysis)
        context: Execution context

    Returns:
        Dict containing:
            - rollback_sql: str
            - safety_checks: List[str]
            - warnings: List[str]
            - reversible: bool
    """
    # Validate parameters
    if 'migration_sql' not in params:
        raise ValueError("Missing required parameter: migration_sql")

    migration_sql = params['migration_sql']
    migration_type = params.get('migration_type', 'unknown')

    # Simulate rollback script generation
    await asyncio.sleep(0.1)

    rollback_sql = ""
    safety_checks = []
    warnings = []
    reversible = True

    # Analyze migration SQL
    sql_upper = migration_sql.upper()

    if 'ADD COLUMN' in sql_upper:
        # Extract table and column name (simplified parsing)
        lines = migration_sql.split('\n')
        for line in lines:
            if 'ALTER TABLE' in line.upper():
                parts = line.split()
                if len(parts) >= 3:
                    table = parts[2]
            if 'ADD COLUMN' in line.upper():
                parts = line.split()
                col_idx = parts.index('COLUMN') if 'COLUMN' in parts else -1
                if col_idx >= 0 and col_idx + 1 < len(parts):
                    column = parts[col_idx + 1]

                    rollback_sql = f"""
-- Rollback: Remove added column
ALTER TABLE {table}
DROP COLUMN {column};
""".strip()

                    safety_checks.append(f"Verify column {column} exists in {table}")
                    safety_checks.append(f"Backup data if column contains important information")
                    warnings.append("Dropping column will permanently delete data")

    elif 'DROP COLUMN' in sql_upper:
        rollback_sql = """
-- WARNING: Cannot restore dropped column
-- Manual data restoration required
-- Please restore from backup
""".strip()

        safety_checks.append("Ensure recent backup exists")
        safety_checks.append("Verify backup integrity")
        warnings.append("This migration is NOT automatically reversible")
        reversible = False

    elif 'CREATE INDEX' in sql_upper:
        # Extract index name
        lines = migration_sql.split('\n')
        for line in lines:
            if 'CREATE' in line.upper() and 'INDEX' in line.upper():
                parts = line.split()
                idx_pos = parts.index('INDEX') if 'INDEX' in parts else -1
                if idx_pos >= 0 and idx_pos + 1 < len(parts):
                    index_name = parts[idx_pos + 1]

                    rollback_sql = f"""
-- Rollback: Drop created index
DROP INDEX {index_name};
""".strip()

                    safety_checks.append(f"Verify index {index_name} exists")

    elif 'ALTER COLUMN' in sql_upper:
        rollback_sql = """
-- WARNING: Type conversion may not be fully reversible
-- Data precision may have been lost
-- Manual verification required
""".strip()

        safety_checks.append("Verify data integrity after rollback")
        safety_checks.append("Check for truncated or converted values")
        warnings.append("Type conversions may lose data precision")
        reversible = False

    else:
        rollback_sql = """
-- Unable to automatically generate rollback script
-- Manual rollback required
""".strip()

        safety_checks.append("Review original migration SQL")
        safety_checks.append("Create custom rollback script")
        warnings.append("Automatic rollback not supported for this operation")
        reversible = False

    # Add general safety checks
    safety_checks.extend([
        "Create database backup before rollback",
        "Test rollback in non-production environment first",
        "Notify team before executing rollback"
    ])

    return {
        'rollback_sql': rollback_sql,
        'safety_checks': safety_checks,
        'warnings': warnings,
        'reversible': reversible,
        'original_migration': migration_sql,
        'checksum': hashlib.md5(rollback_sql.encode()).hexdigest()
    }


# Tool registration metadata
MIGRATION_TOOLS = [
    {
        'name': 'create_migration_script',
        'func': create_migration_script,
        'schema': {
            'type': 'object',
            'required': ['operation', 'table', 'details'],
            'properties': {
                'operation': {
                    'type': 'string',
                    'enum': ['add_column', 'drop_column', 'add_index', 'rename_column', 'modify_column']
                },
                'table': {'type': 'string'},
                'details': {'type': 'object'}
            }
        }
    },
    {
        'name': 'execute_migration',
        'func': execute_migration,
        'schema': {
            'type': 'object',
            'required': ['migration_sql'],
            'properties': {
                'migration_sql': {'type': 'string'},
                'dry_run': {'type': 'boolean', 'default': True},
                'use_transaction': {'type': 'boolean', 'default': True},
                'timeout': {'type': 'integer', 'default': 300}
            }
        }
    },
    {
        'name': 'verify_migration',
        'func': verify_migration,
        'schema': {
            'type': 'object',
            'required': ['table', 'expected_changes'],
            'properties': {
                'table': {'type': 'string'},
                'expected_changes': {'type': 'object'}
            }
        }
    },
    {
        'name': 'generate_rollback_script',
        'func': generate_rollback_script,
        'schema': {
            'type': 'object',
            'required': ['migration_sql'],
            'properties': {
                'migration_sql': {'type': 'string'},
                'migration_type': {'type': 'string'}
            }
        }
    }
]
