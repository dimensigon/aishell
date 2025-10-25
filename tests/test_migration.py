"""
Tests for Migration Assistant

Covers schema migrations, data migrations, and rollback support.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from src.database.migration import (
    MigrationAssistant, Migration, MigrationType, MigrationStatus, MigrationResult
)


@pytest.fixture
def migrations_dir():
    """Create temporary migrations directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def migration_assistant(migrations_dir):
    """Create migration assistant instance"""
    return MigrationAssistant(
        migrations_dir=migrations_dir,
        database_type='postgresql'
    )


@pytest.fixture
def mock_db_client():
    """Create mock database client"""
    client = AsyncMock()
    client.execute_ddl = AsyncMock()
    return client


@pytest.mark.asyncio
class TestMigrationAssistant:
    """Test migration assistant functionality"""

    def test_create_sql_migration_template(self, migration_assistant):
        """Test creating SQL migration template"""
        migration_file = migration_assistant.create_migration_template(
            name='create_users_table',
            migration_type=MigrationType.SCHEMA,
            use_python=False
        )

        assert migration_file.exists()
        assert migration_file.suffix == '.sql'

        with open(migration_file, 'r') as f:
            content = f.read()
            assert 'migration_id:' in content
            assert 'create_users_table' in content
            assert '-- UP' in content
            assert '-- DOWN' in content

    def test_create_python_migration_template(self, migration_assistant):
        """Test creating Python migration template"""
        migration_file = migration_assistant.create_migration_template(
            name='migrate_user_data',
            migration_type=MigrationType.DATA,
            use_python=True
        )

        assert migration_file.exists()
        assert migration_file.suffix == '.py'

        with open(migration_file, 'r') as f:
            content = f.read()
            assert 'MIGRATION_ID' in content
            assert 'migrate_user_data' in content
            assert 'async def up' in content
            assert 'async def down' in content

    def test_load_sql_migration(self, migration_assistant, migrations_dir):
        """Test loading SQL migration from file"""
        # Create a test migration file
        migration_content = """-- migration_id: 001_create_users
-- version: 1.0.0
-- name: Create users table
-- description: Creates the users table
-- type: schema
-- dependencies: []

-- UP
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL
);

-- DOWN
DROP TABLE users;
"""
        migration_file = Path(migrations_dir) / '001_create_users.sql'
        with open(migration_file, 'w') as f:
            f.write(migration_content)

        # Reload migrations
        migration_assistant._discover_migrations()

        assert '001_create_users' in migration_assistant.migrations
        migration = migration_assistant.migrations['001_create_users']

        assert migration.name == 'Create users table'
        assert migration.version == '1.0.0'
        assert migration.migration_type == MigrationType.SCHEMA
        assert 'CREATE TABLE users' in migration.up_sql
        assert 'DROP TABLE users' in migration.down_sql

    async def test_apply_migration(self, migration_assistant, migrations_dir, mock_db_client):
        """Test applying a migration"""
        # Create a test migration
        migration_content = """-- migration_id: 001_create_test
-- version: 1.0.0
-- name: Create test table
-- description: Test migration
-- type: schema
-- dependencies: []

-- UP
CREATE TABLE test (id INT);

-- DOWN
DROP TABLE test;
"""
        migration_file = Path(migrations_dir) / '001_create_test.sql'
        with open(migration_file, 'w') as f:
            f.write(migration_content)

        migration_assistant._discover_migrations()

        result = await migration_assistant.apply_migration(
            '001_create_test',
            mock_db_client
        )

        assert result.status == MigrationStatus.COMPLETED
        assert '001_create_test' in migration_assistant.applied_migrations
        assert mock_db_client.execute_ddl.called

    async def test_apply_migration_with_dependencies(self, migration_assistant, migrations_dir, mock_db_client):
        """Test applying migration with dependencies"""
        # Create base migration
        base_content = """-- migration_id: 001_base
-- version: 1.0.0
-- name: Base migration
-- description: Base
-- type: schema
-- dependencies: []

-- UP
CREATE TABLE base (id INT);

-- DOWN
DROP TABLE base;
"""
        base_file = Path(migrations_dir) / '001_base.sql'
        with open(base_file, 'w') as f:
            f.write(base_content)

        # Create dependent migration
        dependent_content = """-- migration_id: 002_dependent
-- version: 1.0.0
-- name: Dependent migration
-- description: Depends on base
-- type: schema
-- dependencies: ["001_base"]

-- UP
CREATE TABLE dependent (id INT, base_id INT);

-- DOWN
DROP TABLE dependent;
"""
        dependent_file = Path(migrations_dir) / '002_dependent.sql'
        with open(dependent_file, 'w') as f:
            f.write(dependent_content)

        migration_assistant._discover_migrations()

        # Try to apply dependent without base (should fail)
        result = await migration_assistant.apply_migration(
            '002_dependent',
            mock_db_client
        )

        assert result.status == MigrationStatus.FAILED
        assert 'dependencies' in result.error_message.lower()

        # Apply base first
        await migration_assistant.apply_migration('001_base', mock_db_client)

        # Now apply dependent (should succeed)
        result = await migration_assistant.apply_migration(
            '002_dependent',
            mock_db_client
        )

        assert result.status == MigrationStatus.COMPLETED

    async def test_rollback_migration(self, migration_assistant, migrations_dir, mock_db_client):
        """Test rolling back a migration"""
        # Create and apply migration
        migration_content = """-- migration_id: 001_test_rollback
-- version: 1.0.0
-- name: Test rollback
-- description: Test
-- type: schema
-- dependencies: []

-- UP
CREATE TABLE test_rollback (id INT);

-- DOWN
DROP TABLE test_rollback;
"""
        migration_file = Path(migrations_dir) / '001_test_rollback.sql'
        with open(migration_file, 'w') as f:
            f.write(migration_content)

        migration_assistant._discover_migrations()

        # Apply migration
        await migration_assistant.apply_migration('001_test_rollback', mock_db_client)

        assert '001_test_rollback' in migration_assistant.applied_migrations

        # Rollback migration
        result = await migration_assistant.rollback_migration('001_test_rollback', mock_db_client)

        assert result.status == MigrationStatus.ROLLED_BACK
        assert '001_test_rollback' not in migration_assistant.applied_migrations

    async def test_apply_all_pending(self, migration_assistant, migrations_dir, mock_db_client):
        """Test applying all pending migrations"""
        # Create multiple migrations
        for i in range(3):
            content = f"""-- migration_id: {i:03d}_migration
-- version: 1.0.{i}
-- name: Migration {i}
-- description: Test migration {i}
-- type: schema
-- dependencies: []

-- UP
CREATE TABLE table_{i} (id INT);

-- DOWN
DROP TABLE table_{i};
"""
            migration_file = Path(migrations_dir) / f'{i:03d}_migration.sql'
            with open(migration_file, 'w') as f:
                f.write(content)

        migration_assistant._discover_migrations()

        results = await migration_assistant.apply_all_pending(mock_db_client)

        assert len(results) == 3
        assert all(r.status == MigrationStatus.COMPLETED for r in results)
        assert len(migration_assistant.applied_migrations) == 3

    def test_get_pending_migrations(self, migration_assistant, migrations_dir):
        """Test getting pending migrations"""
        # Create migrations
        for i in range(2):
            content = f"""-- migration_id: {i:03d}_pending
-- version: 1.0.{i}
-- name: Pending {i}
-- description: Test
-- type: schema
-- dependencies: []

-- UP
CREATE TABLE pending_{i} (id INT);

-- DOWN
DROP TABLE pending_{i};
"""
            migration_file = Path(migrations_dir) / f'{i:03d}_pending.sql'
            with open(migration_file, 'w') as f:
                f.write(content)

        migration_assistant._discover_migrations()

        pending = migration_assistant.get_pending_migrations()

        assert len(pending) == 2

    def test_get_migration_status(self, migration_assistant, migrations_dir, mock_db_client):
        """Test getting migration status"""
        # Create migration
        content = """-- migration_id: 001_status_test
-- version: 1.0.0
-- name: Status test
-- description: Test
-- type: schema
-- dependencies: []

-- UP
CREATE TABLE status_test (id INT);

-- DOWN
DROP TABLE status_test;
"""
        migration_file = Path(migrations_dir) / '001_status_test.sql'
        with open(migration_file, 'w') as f:
            f.write(content)

        migration_assistant._discover_migrations()

        status = migration_assistant.get_migration_status()

        assert status['total_migrations'] == 1
        assert status['applied'] == 0
        assert status['pending'] == 1

    async def test_dry_run(self, migration_assistant, migrations_dir, mock_db_client):
        """Test dry run migration"""
        # Create migration
        content = """-- migration_id: 001_dry_run
-- version: 1.0.0
-- name: Dry run test
-- description: Test
-- type: schema
-- dependencies: []

-- UP
CREATE TABLE dry_run (id INT);

-- DOWN
DROP TABLE dry_run;
"""
        migration_file = Path(migrations_dir) / '001_dry_run.sql'
        with open(migration_file, 'w') as f:
            f.write(content)

        migration_assistant._discover_migrations()

        # Dry run
        result = await migration_assistant.apply_migration(
            '001_dry_run',
            mock_db_client,
            dry_run=True
        )

        assert result.status == MigrationStatus.COMPLETED
        # Should not be in applied migrations
        assert '001_dry_run' not in migration_assistant.applied_migrations

    def test_migration_sorting(self, migration_assistant, migrations_dir):
        """Test migration dependency sorting"""
        # Create migrations with dependencies
        migrations = [
            ('003_third', '1.0.3', ['002_second']),
            ('001_first', '1.0.1', []),
            ('002_second', '1.0.2', ['001_first'])
        ]

        migration_objs = []
        for mig_id, version, deps in migrations:
            migration = Migration(
                migration_id=mig_id,
                version=version,
                name=mig_id,
                description='Test',
                migration_type=MigrationType.SCHEMA,
                up_sql='CREATE TABLE test (id INT);',
                down_sql='DROP TABLE test;',
                dependencies=deps,
                checksum='abc123',
                created_at=datetime.now(),
                applied_at=None,
                rolled_back_at=None,
                status=MigrationStatus.PENDING,
                error_message=None,
                metadata={}
            )
            migration_objs.append(migration)

        # Sort migrations
        sorted_migrations = migration_assistant._sort_migrations(migration_objs)

        # Verify order
        assert sorted_migrations[0].migration_id == '001_first'
        assert sorted_migrations[1].migration_id == '002_second'
        assert sorted_migrations[2].migration_id == '003_third'

    def test_state_persistence(self, migration_assistant, migrations_dir, mock_db_client):
        """Test migration state persistence"""
        # Create and apply migration
        content = """-- migration_id: 001_persist_test
-- version: 1.0.0
-- name: Persist test
-- description: Test
-- type: schema
-- dependencies: []

-- UP
CREATE TABLE persist (id INT);

-- DOWN
DROP TABLE persist;
"""
        migration_file = Path(migrations_dir) / '001_persist_test.sql'
        with open(migration_file, 'w') as f:
            f.write(content)

        migration_assistant._discover_migrations()

        # Apply migration
        import asyncio
        asyncio.run(migration_assistant.apply_migration('001_persist_test', mock_db_client))

        # Save state
        migration_assistant._save_state()

        # Create new assistant to test loading
        new_assistant = MigrationAssistant(
            migrations_dir=migrations_dir,
            database_type='postgresql'
        )

        # Check state was loaded
        assert '001_persist_test' in new_assistant.applied_migrations

    async def test_validation_errors(self, migration_assistant, migrations_dir, mock_db_client):
        """Test migration validation"""
        # Create migration with empty UP
        content = """-- migration_id: 001_invalid
-- version: 1.0.0
-- name: Invalid
-- description: Test
-- type: schema
-- dependencies: []

-- UP

-- DOWN
DROP TABLE test;
"""
        migration_file = Path(migrations_dir) / '001_invalid.sql'
        with open(migration_file, 'w') as f:
            f.write(content)

        migration_assistant._discover_migrations()

        result = await migration_assistant.apply_migration('001_invalid', mock_db_client)

        assert result.status == MigrationStatus.FAILED
        assert 'validation' in result.error_message.lower() or 'empty' in result.error_message.lower()
