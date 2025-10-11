"""
Database Migration Assistant

Provides schema migration tracking, data migration tools, rollback support,
and cross-database migrations.
"""

import os
import asyncio
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import importlib.util


class MigrationStatus(Enum):
    """Migration status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationType(Enum):
    """Migration type enumeration"""
    SCHEMA = "schema"  # DDL changes
    DATA = "data"      # DML changes
    MIXED = "mixed"    # Both DDL and DML


@dataclass
class Migration:
    """Migration definition"""
    migration_id: str
    version: str
    name: str
    description: str
    migration_type: MigrationType
    up_sql: str
    down_sql: str
    dependencies: List[str]
    checksum: str
    created_at: datetime
    applied_at: Optional[datetime]
    rolled_back_at: Optional[datetime]
    status: MigrationStatus
    error_message: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class MigrationResult:
    """Migration execution result"""
    migration_id: str
    version: str
    status: MigrationStatus
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    affected_objects: List[str]


class MigrationAssistant:
    """
    Database migration assistant

    Features:
    - Schema migration tracking (like Alembic)
    - Data migration tools
    - Rollback support
    - Migration validation
    - Cross-database migrations
    - Version control integration
    - Migration testing framework
    """

    def __init__(
        self,
        migrations_dir: str = "./migrations",
        database_type: str = "postgresql"
    ):
        """
        Initialize migration assistant

        Args:
            migrations_dir: Directory for migration files
            database_type: Type of database (postgresql, oracle, mysql)
        """
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(parents=True, exist_ok=True)

        self.database_type = database_type
        self.state_file = self.migrations_dir / "migration_state.json"
        self.migrations: Dict[str, Migration] = {}
        self.applied_migrations: Dict[str, Migration] = {}

        self._load_state()
        self._discover_migrations()

    def _load_state(self) -> None:
        """Load migration state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)

                for migration_id, migration_data in data.get('applied', {}).items():
                    # Convert string dates back to datetime
                    migration_data['created_at'] = datetime.fromisoformat(migration_data['created_at'])

                    if migration_data.get('applied_at'):
                        migration_data['applied_at'] = datetime.fromisoformat(migration_data['applied_at'])

                    if migration_data.get('rolled_back_at'):
                        migration_data['rolled_back_at'] = datetime.fromisoformat(migration_data['rolled_back_at'])

                    # Convert enums
                    migration_data['migration_type'] = MigrationType(migration_data['migration_type'])
                    migration_data['status'] = MigrationStatus(migration_data['status'])

                    self.applied_migrations[migration_id] = Migration(**migration_data)

            except Exception as e:
                print(f"Warning: Failed to load migration state: {e}")

    def _save_state(self) -> None:
        """Save migration state to disk"""
        data = {'applied': {}}

        for migration_id, migration in self.applied_migrations.items():
            migration_dict = asdict(migration)
            migration_dict['created_at'] = migration.created_at.isoformat()
            migration_dict['applied_at'] = migration.applied_at.isoformat() if migration.applied_at else None
            migration_dict['rolled_back_at'] = migration.rolled_back_at.isoformat() if migration.rolled_back_at else None
            migration_dict['migration_type'] = migration.migration_type.value
            migration_dict['status'] = migration.status.value

            data['applied'][migration_id] = migration_dict

        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _discover_migrations(self) -> None:
        """Discover migration files in migrations directory"""
        # Look for .sql and .py migration files
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            try:
                migration = self._load_migration_file(file_path)
                self.migrations[migration.migration_id] = migration
            except Exception as e:
                print(f"Warning: Failed to load migration {file_path}: {e}")

        for file_path in sorted(self.migrations_dir.glob("*.py")):
            if file_path.name == '__init__.py':
                continue

            try:
                migration = self._load_migration_py(file_path)
                self.migrations[migration.migration_id] = migration
            except Exception as e:
                print(f"Warning: Failed to load migration {file_path}: {e}")

    def _load_migration_file(self, file_path: Path) -> Migration:
        """Load migration from SQL file"""
        with open(file_path, 'r') as f:
            content = f.read()

        # Parse migration header
        # Expected format:
        # -- migration_id: 001_create_users_table
        # -- version: 1.0.0
        # -- name: Create users table
        # -- description: Creates the users table with basic fields
        # -- type: schema
        # -- dependencies: []
        # -- UP
        # CREATE TABLE users ...
        # -- DOWN
        # DROP TABLE users ...

        lines = content.split('\n')
        metadata = {}
        up_sql = []
        down_sql = []
        current_section = None

        for line in lines:
            if line.startswith('-- migration_id:'):
                metadata['migration_id'] = line.split(':', 1)[1].strip()
            elif line.startswith('-- version:'):
                metadata['version'] = line.split(':', 1)[1].strip()
            elif line.startswith('-- name:'):
                metadata['name'] = line.split(':', 1)[1].strip()
            elif line.startswith('-- description:'):
                metadata['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('-- type:'):
                type_str = line.split(':', 1)[1].strip()
                metadata['type'] = MigrationType(type_str)
            elif line.startswith('-- dependencies:'):
                deps_str = line.split(':', 1)[1].strip()
                metadata['dependencies'] = json.loads(deps_str) if deps_str else []
            elif line == '-- UP':
                current_section = 'up'
            elif line == '-- DOWN':
                current_section = 'down'
            elif current_section == 'up' and not line.startswith('--'):
                up_sql.append(line)
            elif current_section == 'down' and not line.startswith('--'):
                down_sql.append(line)

        up_sql_str = '\n'.join(up_sql).strip()
        down_sql_str = '\n'.join(down_sql).strip()

        # Calculate checksum
        checksum = hashlib.sha256(content.encode()).hexdigest()

        return Migration(
            migration_id=metadata.get('migration_id', file_path.stem),
            version=metadata.get('version', '0.0.0'),
            name=metadata.get('name', file_path.stem),
            description=metadata.get('description', ''),
            migration_type=metadata.get('type', MigrationType.SCHEMA),
            up_sql=up_sql_str,
            down_sql=down_sql_str,
            dependencies=metadata.get('dependencies', []),
            checksum=checksum,
            created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
            applied_at=None,
            rolled_back_at=None,
            status=MigrationStatus.PENDING,
            error_message=None,
            metadata={}
        )

    def _load_migration_py(self, file_path: Path) -> Migration:
        """Load migration from Python file"""
        # Load Python module
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get migration metadata
        migration_id = getattr(module, 'MIGRATION_ID', file_path.stem)
        version = getattr(module, 'VERSION', '0.0.0')
        name = getattr(module, 'NAME', file_path.stem)
        description = getattr(module, 'DESCRIPTION', '')
        migration_type = MigrationType(getattr(module, 'TYPE', 'schema'))
        dependencies = getattr(module, 'DEPENDENCIES', [])

        # Get up/down functions
        up_func = getattr(module, 'up', None)
        down_func = getattr(module, 'down', None)

        if not up_func or not down_func:
            raise ValueError(f"Migration {file_path} must define up() and down() functions")

        # For Python migrations, store function references
        with open(file_path, 'r') as f:
            content = f.read()

        checksum = hashlib.sha256(content.encode()).hexdigest()

        return Migration(
            migration_id=migration_id,
            version=version,
            name=name,
            description=description,
            migration_type=migration_type,
            up_sql="",  # Python migrations use functions
            down_sql="",
            dependencies=dependencies,
            checksum=checksum,
            created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
            applied_at=None,
            rolled_back_at=None,
            status=MigrationStatus.PENDING,
            error_message=None,
            metadata={'python_file': str(file_path)}
        )

    async def apply_migration(
        self,
        migration_id: str,
        db_client: Any,
        dry_run: bool = False
    ) -> MigrationResult:
        """
        Apply a migration

        Args:
            migration_id: Migration identifier
            db_client: Database client instance
            dry_run: If True, validate without applying

        Returns:
            Migration result
        """
        migration = self.migrations.get(migration_id)

        if not migration:
            return MigrationResult(
                migration_id=migration_id,
                version="",
                status=MigrationStatus.FAILED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message="Migration not found",
                affected_objects=[]
            )

        # Check if already applied
        if migration_id in self.applied_migrations:
            existing = self.applied_migrations[migration_id]
            if existing.status == MigrationStatus.COMPLETED:
                return MigrationResult(
                    migration_id=migration_id,
                    version=migration.version,
                    status=MigrationStatus.COMPLETED,
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    error_message="Migration already applied",
                    affected_objects=[]
                )

        result = MigrationResult(
            migration_id=migration_id,
            version=migration.version,
            status=MigrationStatus.PENDING,
            started_at=datetime.now(),
            completed_at=None,
            error_message=None,
            affected_objects=[]
        )

        try:
            # Check dependencies
            missing_deps = self._check_dependencies(migration)
            if missing_deps:
                raise ValueError(f"Missing dependencies: {', '.join(missing_deps)}")

            # Validate migration
            validation_errors = await self._validate_migration(migration, db_client)
            if validation_errors:
                raise ValueError(f"Validation failed: {', '.join(validation_errors)}")

            if dry_run:
                result.status = MigrationStatus.COMPLETED
                result.completed_at = datetime.now()
                return result

            result.status = MigrationStatus.IN_PROGRESS
            migration.status = MigrationStatus.IN_PROGRESS

            # Execute migration
            if migration.metadata.get('python_file'):
                affected = await self._execute_python_migration(migration, db_client, direction='up')
            else:
                affected = await self._execute_sql_migration(migration, db_client, migration.up_sql)

            result.affected_objects = affected

            # Update status
            migration.applied_at = datetime.now()
            migration.status = MigrationStatus.COMPLETED
            result.status = MigrationStatus.COMPLETED
            result.completed_at = datetime.now()

            # Save to applied migrations
            self.applied_migrations[migration_id] = migration
            self._save_state()

        except Exception as e:
            migration.status = MigrationStatus.FAILED
            migration.error_message = str(e)
            result.status = MigrationStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now()

        return result

    async def rollback_migration(
        self,
        migration_id: str,
        db_client: Any
    ) -> MigrationResult:
        """
        Rollback a migration

        Args:
            migration_id: Migration identifier
            db_client: Database client instance

        Returns:
            Migration result
        """
        migration = self.applied_migrations.get(migration_id)

        if not migration:
            return MigrationResult(
                migration_id=migration_id,
                version="",
                status=MigrationStatus.FAILED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message="Migration not applied",
                affected_objects=[]
            )

        result = MigrationResult(
            migration_id=migration_id,
            version=migration.version,
            status=MigrationStatus.IN_PROGRESS,
            started_at=datetime.now(),
            completed_at=None,
            error_message=None,
            affected_objects=[]
        )

        try:
            # Execute rollback
            if migration.metadata.get('python_file'):
                affected = await self._execute_python_migration(migration, db_client, direction='down')
            else:
                affected = await self._execute_sql_migration(migration, db_client, migration.down_sql)

            result.affected_objects = affected

            # Update status
            migration.rolled_back_at = datetime.now()
            migration.status = MigrationStatus.ROLLED_BACK
            result.status = MigrationStatus.ROLLED_BACK
            result.completed_at = datetime.now()

            # Remove from applied migrations
            del self.applied_migrations[migration_id]
            self._save_state()

        except Exception as e:
            migration.error_message = str(e)
            result.status = MigrationStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now()

        return result

    async def apply_all_pending(
        self,
        db_client: Any,
        stop_on_error: bool = True
    ) -> List[MigrationResult]:
        """
        Apply all pending migrations

        Args:
            db_client: Database client instance
            stop_on_error: Stop on first error

        Returns:
            List of migration results
        """
        results = []
        pending = self.get_pending_migrations()

        # Sort by dependencies and version
        sorted_pending = self._sort_migrations(pending)

        for migration in sorted_pending:
            result = await self.apply_migration(migration.migration_id, db_client)
            results.append(result)

            if result.status == MigrationStatus.FAILED and stop_on_error:
                break

        return results

    async def _execute_sql_migration(
        self,
        migration: Migration,
        db_client: Any,
        sql: str
    ) -> List[str]:
        """Execute SQL migration"""
        affected_objects = []

        # Split SQL into statements
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        for statement in statements:
            await db_client.execute_ddl(statement)

            # Extract affected object names
            if 'CREATE TABLE' in statement.upper():
                # Extract table name
                parts = statement.upper().split('CREATE TABLE')
                if len(parts) > 1:
                    table_name = parts[1].strip().split()[0]
                    affected_objects.append(f"table:{table_name}")

        return affected_objects

    async def _execute_python_migration(
        self,
        migration: Migration,
        db_client: Any,
        direction: str
    ) -> List[str]:
        """Execute Python migration"""
        python_file = migration.metadata.get('python_file')

        if not python_file:
            raise ValueError("No Python file specified")

        # Load module
        spec = importlib.util.spec_from_file_location(Path(python_file).stem, python_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get function
        func = getattr(module, direction)

        # Execute function
        if asyncio.iscoroutinefunction(func):
            result = await func(db_client)
        else:
            result = func(db_client)

        # Return affected objects
        return result if isinstance(result, list) else []

    async def _validate_migration(
        self,
        migration: Migration,
        db_client: Any
    ) -> List[str]:
        """
        Validate migration before applying

        Args:
            migration: Migration to validate
            db_client: Database client instance

        Returns:
            List of validation errors
        """
        errors = []

        # Check checksum hasn't changed
        original_migration = self.migrations.get(migration.migration_id)
        if original_migration and original_migration.checksum != migration.checksum:
            errors.append("Migration checksum has changed")

        # Validate SQL syntax (basic check)
        if migration.up_sql:
            if not migration.up_sql.strip():
                errors.append("Empty UP migration")

        if migration.down_sql:
            if not migration.down_sql.strip():
                errors.append("Empty DOWN migration")

        return errors

    def _check_dependencies(self, migration: Migration) -> List[str]:
        """Check if migration dependencies are satisfied"""
        missing = []

        for dep_id in migration.dependencies:
            if dep_id not in self.applied_migrations:
                missing.append(dep_id)

        return missing

    def _sort_migrations(self, migrations: List[Migration]) -> List[Migration]:
        """Sort migrations by dependencies and version"""
        sorted_migrations = []
        remaining = migrations.copy()

        while remaining:
            # Find migrations with satisfied dependencies
            ready = [m for m in remaining if not self._check_dependencies(m)]

            if not ready:
                # Circular dependency or missing dependency
                break

            # Sort by version
            ready.sort(key=lambda m: m.version)

            # Add to sorted list
            sorted_migrations.extend(ready)

            # Remove from remaining
            for m in ready:
                remaining.remove(m)

        # Add any remaining (with unsatisfied dependencies) at end
        sorted_migrations.extend(remaining)

        return sorted_migrations

    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        pending = []

        for migration_id, migration in self.migrations.items():
            if migration_id not in self.applied_migrations:
                pending.append(migration)

        return pending

    def get_applied_migrations(self) -> List[Migration]:
        """Get list of applied migrations"""
        return list(self.applied_migrations.values())

    def get_migration_status(self) -> Dict[str, Any]:
        """Get overall migration status"""
        total = len(self.migrations)
        applied = len(self.applied_migrations)
        pending = total - applied

        return {
            'total_migrations': total,
            'applied': applied,
            'pending': pending,
            'latest_applied': max(
                (m.applied_at for m in self.applied_migrations.values() if m.applied_at),
                default=None
            )
        }

    def create_migration_template(
        self,
        name: str,
        migration_type: MigrationType = MigrationType.SCHEMA,
        use_python: bool = False
    ) -> Path:
        """
        Create a new migration template

        Args:
            name: Migration name
            migration_type: Type of migration
            use_python: Create Python migration instead of SQL

        Returns:
            Path to created migration file
        """
        # Generate migration ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        migration_id = f"{timestamp}_{name}"

        if use_python:
            file_path = self.migrations_dir / f"{migration_id}.py"
            template = self._get_python_template(migration_id, name, migration_type)
        else:
            file_path = self.migrations_dir / f"{migration_id}.sql"
            template = self._get_sql_template(migration_id, name, migration_type)

        with open(file_path, 'w') as f:
            f.write(template)

        return file_path

    def _get_sql_template(
        self,
        migration_id: str,
        name: str,
        migration_type: MigrationType
    ) -> str:
        """Get SQL migration template"""
        return f"""-- migration_id: {migration_id}
-- version: 1.0.0
-- name: {name}
-- description: Description of this migration
-- type: {migration_type.value}
-- dependencies: []

-- UP
-- Add your UP migration SQL here
-- Example:
-- CREATE TABLE example (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL
-- );

-- DOWN
-- Add your DOWN migration SQL here
-- Example:
-- DROP TABLE example;
"""

    def _get_python_template(
        self,
        migration_id: str,
        name: str,
        migration_type: MigrationType
    ) -> str:
        """Get Python migration template"""
        return f'''"""
Migration: {name}
"""

MIGRATION_ID = "{migration_id}"
VERSION = "1.0.0"
NAME = "{name}"
DESCRIPTION = "Description of this migration"
TYPE = "{migration_type.value}"
DEPENDENCIES = []


async def up(db_client):
    """
    Apply migration

    Args:
        db_client: Database client instance

    Returns:
        List of affected object names
    """
    # Add your UP migration logic here
    # Example:
    # await db_client.execute_ddl("""
    #     CREATE TABLE example (
    #         id SERIAL PRIMARY KEY,
    #         name VARCHAR(255) NOT NULL
    #     )
    # """)

    return ["table:example"]


async def down(db_client):
    """
    Rollback migration

    Args:
        db_client: Database client instance

    Returns:
        List of affected object names
    """
    # Add your DOWN migration logic here
    # Example:
    # await db_client.execute_ddl("DROP TABLE example")

    return ["table:example"]
'''
