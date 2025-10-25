"""
Database Tools for Agentic AI Workflows

This module implements database operation tools including backup creation,
schema analysis, and backup validation for the AIShell agent system.
"""

import os
import hashlib
import time
from typing import Dict, Any, Optional


def calculate_checksum(file_path: str) -> str:
    """
    Calculate MD5 checksum of a file

    Args:
        file_path: Path to the file to checksum

    Returns:
        Hexadecimal MD5 checksum string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read

    Example:
        >>> checksum = calculate_checksum("/backups/db_backup.sql.gz")
        >>> print(f"Checksum: {checksum}")
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    md5_hash = hashlib.md5()

    try:
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {str(e)}") from e

    return md5_hash.hexdigest()


async def backup_database_full(params: Dict[str, Any],
                                context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create full database backup

    This tool creates a complete backup of the specified database with
    optional compression. The backup file is validated with a checksum
    and metadata is returned for verification and cataloging.

    Parameters:
        database (str): Database name to backup
        destination (str): Backup destination path
        compression (bool, optional): Enable compression (default: True)

    Returns:
        Dict containing:
            backup_path (str): Path to created backup file
            size_bytes (int): Backup file size in bytes
            duration_seconds (float): Backup duration in seconds
            checksum (str): MD5 checksum of backup file

    Raises:
        ValueError: If required parameters are missing
        RuntimeError: If backup creation fails

    Example:
        >>> result = await backup_database_full(
        ...     {"database": "production", "destination": "/backups/prod.sql.gz"},
        ...     {"database_module": db_module}
        ... )
        >>> print(f"Backup created: {result['backup_path']}")
    """
    # Validate required parameters
    database = params.get('database')
    destination = params.get('destination')

    if not database:
        raise ValueError("Parameter 'database' is required")
    if not destination:
        raise ValueError("Parameter 'destination' is required")

    compression = params.get('compression', True)

    # Start timing
    start_time = time.time()

    # Mock implementation - in production, this would call the database module
    # database_module = context.get('database_module')
    # if not database_module:
    #     raise RuntimeError("database_module not available in context")

    # Simulate backup creation
    # In real implementation:
    # backup_path = await database_module.create_backup(
    #     database=database,
    #     backup_type='full',
    #     destination=destination,
    #     compression=compression
    # )

    # Mock: Create placeholder backup file for demonstration
    backup_extension = ".sql.gz" if compression else ".sql"
    backup_path = destination if destination.endswith(backup_extension) else f"{destination}{backup_extension}"

    # Ensure directory exists
    os.makedirs(os.path.dirname(backup_path) or '.', exist_ok=True)

    # Create mock backup file with sample data
    try:
        with open(backup_path, 'wb') as f:
            # Write sample backup data
            sample_data = f"-- Database Backup: {database}\n"
            sample_data += f"-- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            sample_data += f"-- Compression: {compression}\n"
            sample_data += "-- Mock backup data\n"
            f.write(sample_data.encode('utf-8'))
    except IOError as e:
        raise RuntimeError(f"Failed to create backup file: {str(e)}") from e

    # Calculate file size
    size_bytes = os.path.getsize(backup_path)

    # Calculate checksum
    try:
        checksum = calculate_checksum(backup_path)
    except Exception as e:
        raise RuntimeError(f"Failed to calculate checksum: {str(e)}") from e

    # Calculate duration
    duration_seconds = time.time() - start_time

    return {
        'backup_path': backup_path,
        'size_bytes': size_bytes,
        'duration_seconds': round(duration_seconds, 2),
        'checksum': checksum
    }


async def analyze_schema(params: Dict[str, Any],
                        context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze database schema

    This tool analyzes the structure of a database, including tables,
    indexes, constraints, and statistics. It provides comprehensive
    schema information for migration planning and optimization.

    Parameters:
        database (str): Database name to analyze
        include_indexes (bool, optional): Include index information (default: True)
        include_constraints (bool, optional): Include constraint information (default: True)

    Returns:
        Dict containing:
            tables (list): List of table definitions with columns and types
            indexes (list): List of indexes (if include_indexes=True)
            constraints (list): List of constraints (if include_constraints=True)
            statistics (dict): Schema statistics (table count, row estimates, etc.)

    Raises:
        ValueError: If required parameters are missing
        RuntimeError: If schema analysis fails

    Example:
        >>> result = await analyze_schema(
        ...     {"database": "production", "include_indexes": True},
        ...     {"database_module": db_module}
        ... )
        >>> print(f"Found {len(result['tables'])} tables")
    """
    # Validate required parameters
    database = params.get('database')
    if not database:
        raise ValueError("Parameter 'database' is required")

    include_indexes = params.get('include_indexes', True)
    include_constraints = params.get('include_constraints', True)

    # Mock implementation - in production, this would query the database
    # database_module = context.get('database_module')
    # if not database_module:
    #     raise RuntimeError("database_module not available in context")

    # Simulate schema analysis
    # In real implementation:
    # schema_info = await database_module.get_schema_info(
    #     database=database,
    #     include_indexes=include_indexes,
    #     include_constraints=include_constraints
    # )

    # Mock schema data
    tables = [
        {
            'name': 'users',
            'columns': [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'username', 'type': 'VARCHAR(255)', 'nullable': False},
                {'name': 'email', 'type': 'VARCHAR(255)', 'nullable': False},
                {'name': 'created_at', 'type': 'TIMESTAMP', 'nullable': False}
            ],
            'row_count_estimate': 10000
        },
        {
            'name': 'orders',
            'columns': [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'user_id', 'type': 'INTEGER', 'nullable': False, 'foreign_key': 'users.id'},
                {'name': 'total', 'type': 'DECIMAL(10,2)', 'nullable': False},
                {'name': 'created_at', 'type': 'TIMESTAMP', 'nullable': False}
            ],
            'row_count_estimate': 50000
        },
        {
            'name': 'products',
            'columns': [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'name', 'type': 'VARCHAR(255)', 'nullable': False},
                {'name': 'price', 'type': 'DECIMAL(10,2)', 'nullable': False},
                {'name': 'stock', 'type': 'INTEGER', 'nullable': False}
            ],
            'row_count_estimate': 5000
        }
    ]

    indexes = []
    if include_indexes:
        indexes = [
            {
                'name': 'idx_users_email',
                'table': 'users',
                'columns': ['email'],
                'unique': True,
                'type': 'btree'
            },
            {
                'name': 'idx_orders_user_id',
                'table': 'orders',
                'columns': ['user_id'],
                'unique': False,
                'type': 'btree'
            },
            {
                'name': 'idx_orders_created_at',
                'table': 'orders',
                'columns': ['created_at'],
                'unique': False,
                'type': 'btree'
            }
        ]

    constraints = []
    if include_constraints:
        constraints = [
            {
                'name': 'pk_users',
                'table': 'users',
                'type': 'PRIMARY KEY',
                'columns': ['id']
            },
            {
                'name': 'uq_users_email',
                'table': 'users',
                'type': 'UNIQUE',
                'columns': ['email']
            },
            {
                'name': 'fk_orders_user_id',
                'table': 'orders',
                'type': 'FOREIGN KEY',
                'columns': ['user_id'],
                'references': {'table': 'users', 'columns': ['id']}
            }
        ]

    statistics = {
        'database_name': database,
        'total_tables': len(tables),
        'total_indexes': len(indexes),
        'total_constraints': len(constraints),
        'total_rows_estimate': sum(t.get('row_count_estimate', 0) for t in tables),
        'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    return {
        'tables': tables,
        'indexes': indexes,
        'constraints': constraints,
        'statistics': statistics
    }


async def validate_backup(params: Dict[str, Any],
                         context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate backup integrity

    This tool validates a backup file by checking its existence, calculating
    its checksum, and verifying the file can be read successfully. This is
    essential for ensuring backups are usable for recovery operations.

    Parameters:
        backup_path (str): Path to backup file to validate

    Returns:
        Dict containing:
            valid (bool): Whether backup is valid
            checksum (str): MD5 checksum of backup file
            size_bytes (int): Backup file size in bytes
            error_message (str|None): Error message if validation failed

    Raises:
        ValueError: If required parameters are missing

    Example:
        >>> result = await validate_backup(
        ...     {"backup_path": "/backups/prod_backup.sql.gz"},
        ...     {}
        ... )
        >>> if result['valid']:
        ...     print(f"Backup is valid, checksum: {result['checksum']}")
    """
    # Validate required parameters
    backup_path = params.get('backup_path')
    if not backup_path:
        raise ValueError("Parameter 'backup_path' is required")

    # Check if file exists
    if not os.path.exists(backup_path):
        return {
            'valid': False,
            'checksum': '',
            'size_bytes': 0,
            'error_message': f"Backup file not found: {backup_path}"
        }

    # Check if file is readable
    if not os.path.isfile(backup_path):
        return {
            'valid': False,
            'checksum': '',
            'size_bytes': 0,
            'error_message': f"Path is not a file: {backup_path}"
        }

    # Get file size
    try:
        size_bytes = os.path.getsize(backup_path)
    except OSError as e:
        return {
            'valid': False,
            'checksum': '',
            'size_bytes': 0,
            'error_message': f"Failed to get file size: {str(e)}"
        }

    # Check if file is not empty
    if size_bytes == 0:
        return {
            'valid': False,
            'checksum': '',
            'size_bytes': 0,
            'error_message': "Backup file is empty"
        }

    # Calculate checksum
    try:
        checksum = calculate_checksum(backup_path)
    except Exception as e:
        return {
            'valid': False,
            'checksum': '',
            'size_bytes': size_bytes,
            'error_message': f"Failed to calculate checksum: {str(e)}"
        }

    # Try to read first few bytes to ensure file is readable
    try:
        with open(backup_path, 'rb') as f:
            f.read(1024)  # Read first 1KB
    except IOError as e:
        return {
            'valid': False,
            'checksum': checksum,
            'size_bytes': size_bytes,
            'error_message': f"File read error: {str(e)}"
        }

    # All validations passed
    return {
        'valid': True,
        'checksum': checksum,
        'size_bytes': size_bytes,
        'error_message': None
    }


def register_database_tools(registry) -> None:
    """
    Register database tools with the tool registry

    This function registers all database-related tools including backup
    creation, schema analysis, and backup validation with the provided
    ToolRegistry instance.

    Args:
        registry: ToolRegistry instance to register tools with

    Example:
        >>> from src.agents.tools.registry import ToolRegistry
        >>> registry = ToolRegistry()
        >>> register_database_tools(registry)
        >>> print(f"Registered {len(registry.list_tools())} tools")
    """
    from .registry import ToolDefinition, ToolCategory, ToolRiskLevel

    # Register backup_database_full tool
    registry.register_tool(ToolDefinition(
        name="backup_database_full",
        description="Create full database backup with optional compression and validation",
        category=ToolCategory.BACKUP,
        risk_level=ToolRiskLevel.LOW,
        required_capabilities=["database_read", "backup_create", "file_write"],
        parameters_schema={
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Database name to backup"
                },
                "destination": {
                    "type": "string",
                    "description": "Backup destination path"
                },
                "compression": {
                    "type": "boolean",
                    "description": "Enable compression (default: true)",
                    "default": True
                }
            },
            "required": ["database", "destination"]
        },
        returns_schema={
            "type": "object",
            "properties": {
                "backup_path": {"type": "string"},
                "size_bytes": {"type": "integer", "minimum": 0},
                "duration_seconds": {"type": "number", "minimum": 0},
                "checksum": {"type": "string", "pattern": "^[a-f0-9]{32}$"}
            },
            "required": ["backup_path", "size_bytes", "duration_seconds", "checksum"]
        },
        implementation=backup_database_full,
        requires_approval=False,
        max_execution_time=3600,
        rate_limit=10,
        examples=[
            {
                "description": "Create compressed full backup",
                "params": {
                    "database": "production",
                    "destination": "/backups/prod_backup.sql.gz",
                    "compression": True
                },
                "expected_output": {
                    "backup_path": "/backups/prod_backup.sql.gz",
                    "size_bytes": 1024000,
                    "duration_seconds": 45.2,
                    "checksum": "abc123def456789012345678901234ab"
                }
            }
        ]
    ))

    # Register analyze_schema tool
    registry.register_tool(ToolDefinition(
        name="analyze_schema",
        description="Analyze database schema structure including tables, indexes, and constraints",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=["database_read", "schema_analyze"],
        parameters_schema={
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Database name to analyze"
                },
                "include_indexes": {
                    "type": "boolean",
                    "description": "Include index information (default: true)",
                    "default": True
                },
                "include_constraints": {
                    "type": "boolean",
                    "description": "Include constraint information (default: true)",
                    "default": True
                }
            },
            "required": ["database"]
        },
        returns_schema={
            "type": "object",
            "properties": {
                "tables": {
                    "type": "array",
                    "items": {"type": "object"}
                },
                "indexes": {
                    "type": "array",
                    "items": {"type": "object"}
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "object"}
                },
                "statistics": {
                    "type": "object"
                }
            },
            "required": ["tables", "indexes", "constraints", "statistics"]
        },
        implementation=analyze_schema,
        requires_approval=False,
        max_execution_time=60,
        rate_limit=30,
        examples=[
            {
                "description": "Analyze schema with indexes and constraints",
                "params": {
                    "database": "production",
                    "include_indexes": True,
                    "include_constraints": True
                },
                "expected_output": {
                    "tables": [{"name": "users", "columns": []}],
                    "indexes": [{"name": "idx_users_email", "table": "users"}],
                    "constraints": [{"name": "pk_users", "type": "PRIMARY KEY"}],
                    "statistics": {"total_tables": 3, "total_rows_estimate": 100000}
                }
            }
        ]
    ))

    # Register validate_backup tool
    registry.register_tool(ToolDefinition(
        name="validate_backup",
        description="Validate backup file integrity by checking existence, size, and checksum",
        category=ToolCategory.BACKUP,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=["file_read"],
        parameters_schema={
            "type": "object",
            "properties": {
                "backup_path": {
                    "type": "string",
                    "description": "Path to backup file to validate"
                }
            },
            "required": ["backup_path"]
        },
        returns_schema={
            "type": "object",
            "properties": {
                "valid": {"type": "boolean"},
                "checksum": {"type": "string"},
                "size_bytes": {"type": "integer", "minimum": 0},
                "error_message": {"type": ["string", "null"]}
            },
            "required": ["valid", "checksum", "size_bytes", "error_message"]
        },
        implementation=validate_backup,
        requires_approval=False,
        max_execution_time=30,
        rate_limit=60,
        examples=[
            {
                "description": "Validate existing backup file",
                "params": {
                    "backup_path": "/backups/prod_backup.sql.gz"
                },
                "expected_output": {
                    "valid": True,
                    "checksum": "abc123def456789012345678901234ab",
                    "size_bytes": 1024000,
                    "error_message": None
                }
            },
            {
                "description": "Validate missing backup file",
                "params": {
                    "backup_path": "/backups/missing.sql.gz"
                },
                "expected_output": {
                    "valid": False,
                    "checksum": "",
                    "size_bytes": 0,
                    "error_message": "Backup file not found: /backups/missing.sql.gz"
                }
            }
        ]
    ))
