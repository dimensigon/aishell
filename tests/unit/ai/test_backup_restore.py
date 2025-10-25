"""
Tests for Backup and Restore Systems

Covers backup creation, restoration, and validation.
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.database.backup import (
    BackupSystem, BackupType, BackupStatus, BackupRotationPolicy, BackupMetadata
)
from src.database.restore import RestoreSystem, RestoreStatus


@pytest.fixture
def backup_dir():
    """Create temporary backup directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def backup_system(backup_dir):
    """Create backup system instance"""
    return BackupSystem(
        backup_dir=backup_dir,
        encryption_key="test-encryption-key-12345678"
    )


@pytest.fixture
def restore_system(backup_system):
    """Create restore system instance"""
    return RestoreSystem(
        backup_system=backup_system,
        encryption_key="test-encryption-key-12345678"
    )


@pytest.fixture
def mock_db_client():
    """Create mock database client"""
    client = AsyncMock()
    client.execute_ddl = AsyncMock()
    return client


@pytest.mark.asyncio
class TestBackupSystem:
    """Test backup system functionality"""

    async def test_create_backup_metadata(self, backup_system, mock_db_client):
        """Test backup metadata creation"""
        connection_params = {
            'host': 'localhost',
            'port': 5432,
            'username': 'postgres',
            'password': 'password'
        }

        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system.create_backup(
                database_type='postgresql',
                database_name='test_db',
                connection_params=connection_params,
                backup_type=BackupType.FULL
            )

            assert metadata.database_type == 'postgresql'
            assert metadata.database_name == 'test_db'
            assert metadata.backup_type == BackupType.FULL
            assert metadata.status == BackupStatus.PENDING

    async def test_backup_postgresql(self, backup_system):
        """Test PostgreSQL backup execution"""
        metadata = BackupMetadata(
            backup_id='test_backup_001',
            database_type='postgresql',
            database_name='test_db',
            backup_type=BackupType.FULL,
            status=BackupStatus.PENDING,
            created_at=datetime.now(),
            completed_at=None,
            file_path='',
            compressed=False,
            encrypted=False,
            size_bytes=0,
            checksum='',
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        output_file = Path(backup_system.backup_dir) / 'test.sql'

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b'', b''))
        mock_process.returncode = 0

        with patch('src.database.backup.asyncio.create_subprocess_exec', return_value=mock_process):
            await backup_system._backup_postgresql(
                output_file,
                {'host': 'localhost', 'port': 5432, 'username': 'postgres', 'password': 'pass'},
                metadata
            )

            # Verify pg_dump was called
            assert mock_process.communicate.called

    async def test_backup_compression(self, backup_system):
        """Test backup compression"""
        test_file = Path(backup_system.backup_dir) / 'test.sql'
        compressed_file = Path(backup_system.backup_dir) / 'test.sql.gz'

        # Create test file
        with open(test_file, 'w') as f:
            f.write('CREATE TABLE test (id INT);')

        await backup_system._compress_file(test_file, compressed_file)

        assert compressed_file.exists()
        assert compressed_file.stat().st_size > 0

    async def test_backup_encryption(self, backup_system):
        """Test backup encryption"""
        test_file = Path(backup_system.backup_dir) / 'test.sql'
        encrypted_file = Path(backup_system.backup_dir) / 'test.sql.enc'

        # Create test file
        with open(test_file, 'w') as f:
            f.write('CREATE TABLE test (id INT);')

        await backup_system._encrypt_file(test_file, encrypted_file)

        assert encrypted_file.exists()
        assert encrypted_file.stat().st_size > 0

    def test_list_backups(self, backup_system):
        """Test listing backups"""
        # Create test metadata
        metadata1 = BackupMetadata(
            backup_id='backup_001',
            database_type='postgresql',
            database_name='test_db',
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path='/tmp/backup_001.sql',
            compressed=False,
            encrypted=False,
            size_bytes=1024,
            checksum='abc123',
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        backup_system.backups['backup_001'] = metadata1

        backups = backup_system.list_backups()

        assert len(backups) == 1
        assert backups[0].backup_id == 'backup_001'

    def test_list_backups_filtered(self, backup_system):
        """Test listing backups with filters"""
        # Create test metadata
        metadata1 = BackupMetadata(
            backup_id='backup_001',
            database_type='postgresql',
            database_name='test_db',
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path='/tmp/backup_001.sql',
            compressed=False,
            encrypted=False,
            size_bytes=1024,
            checksum='abc123',
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        metadata2 = BackupMetadata(
            backup_id='backup_002',
            database_type='postgresql',
            database_name='other_db',
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path='/tmp/backup_002.sql',
            compressed=False,
            encrypted=False,
            size_bytes=2048,
            checksum='def456',
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        backup_system.backups['backup_001'] = metadata1
        backup_system.backups['backup_002'] = metadata2

        backups = backup_system.list_backups(database_name='test_db')

        assert len(backups) == 1
        assert backups[0].database_name == 'test_db'

    def test_get_point_in_time_backup(self, backup_system):
        """Test getting point-in-time backup"""
        now = datetime.now()

        metadata1 = BackupMetadata(
            backup_id='backup_001',
            database_type='postgresql',
            database_name='test_db',
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=2),
            file_path='/tmp/backup_001.sql',
            compressed=False,
            encrypted=False,
            size_bytes=1024,
            checksum='abc123',
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        metadata2 = BackupMetadata(
            backup_id='backup_002',
            database_type='postgresql',
            database_name='test_db',
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=now - timedelta(hours=1),
            completed_at=now - timedelta(hours=1),
            file_path='/tmp/backup_002.sql',
            compressed=False,
            encrypted=False,
            size_bytes=2048,
            checksum='def456',
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        backup_system.backups['backup_001'] = metadata1
        backup_system.backups['backup_002'] = metadata2

        target_time = now - timedelta(minutes=30)
        backup = backup_system.get_point_in_time_backup('test_db', target_time)

        assert backup is not None
        assert backup.backup_id == 'backup_002'

    async def test_validate_backup(self, backup_system):
        """Test backup validation"""
        # Create a real backup file
        backup_file = Path(backup_system.backup_dir) / 'test_backup.sql'
        with open(backup_file, 'w') as f:
            f.write('CREATE TABLE test (id INT);')

        checksum = backup_system._calculate_checksum(str(backup_file))

        metadata = BackupMetadata(
            backup_id='test_backup',
            database_type='postgresql',
            database_name='test_db',
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path=str(backup_file),
            compressed=False,
            encrypted=False,
            size_bytes=backup_file.stat().st_size,
            checksum=checksum,
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        backup_system.backups['test_backup'] = metadata

        is_valid, error = await backup_system.validate_backup('test_backup')

        assert is_valid is True
        assert error is None

    def test_rotation_policy(self, backup_system):
        """Test backup rotation policy"""
        now = datetime.now()

        # Create old backups
        for i in range(10):
            metadata = BackupMetadata(
                backup_id=f'backup_{i:03d}',
                database_type='postgresql',
                database_name='test_db',
                backup_type=BackupType.FULL,
                status=BackupStatus.COMPLETED,
                created_at=now - timedelta(days=i),
                completed_at=now - timedelta(days=i),
                file_path=f'/tmp/backup_{i:03d}.sql',
                compressed=False,
                encrypted=False,
                size_bytes=1024,
                checksum=f'hash_{i}',
                parent_backup_id=None,
                error_message=None,
                metadata={}
            )
            backup_system.backups[f'backup_{i:03d}'] = metadata

        # Apply rotation with keep_daily=3
        backup_system.rotation_policy.keep_daily = 3
        deleted = backup_system.apply_rotation_policy('test_db')

        # Should delete backups older than 3 days (within daily range)
        assert len(deleted) > 0


@pytest.mark.asyncio
class TestRestoreSystem:
    """Test restore system functionality"""

    async def test_restore_backup(self, restore_system, backup_system, mock_db_client):
        """Test backup restoration"""
        # Create a backup first
        backup_file = Path(backup_system.backup_dir) / 'test_backup.sql'
        with open(backup_file, 'w') as f:
            f.write('CREATE TABLE test (id INT);')

        metadata = BackupMetadata(
            backup_id='test_backup',
            database_type='postgresql',
            database_name='test_db',
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path=str(backup_file),
            compressed=False,
            encrypted=False,
            size_bytes=backup_file.stat().st_size,
            checksum=backup_system._calculate_checksum(str(backup_file)),
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        backup_system.backups['test_backup'] = metadata

        connection_params = {
            'host': 'localhost',
            'port': 5432,
            'username': 'postgres',
            'password': 'password'
        }

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b'', b''))
        mock_process.returncode = 0

        with patch('src.database.restore.asyncio.create_subprocess_exec', return_value=mock_process):
            result = await restore_system.restore_backup(
                'test_backup',
                connection_params,
                validate=True
            )

            assert result.status == RestoreStatus.COMPLETED
            assert result.validation_passed is True

    async def test_restore_point_in_time(self, restore_system, backup_system):
        """Test point-in-time restore"""
        now = datetime.now()

        backup_file = Path(backup_system.backup_dir) / 'test_backup.sql'
        with open(backup_file, 'w') as f:
            f.write('CREATE TABLE test (id INT);')

        metadata = BackupMetadata(
            backup_id='test_backup',
            database_type='postgresql',
            database_name='test_db',
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=now - timedelta(hours=1),
            completed_at=now - timedelta(hours=1),
            file_path=str(backup_file),
            compressed=False,
            encrypted=False,
            size_bytes=backup_file.stat().st_size,
            checksum=backup_system._calculate_checksum(str(backup_file)),
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        backup_system.backups['test_backup'] = metadata

        connection_params = {
            'host': 'localhost',
            'port': 5432,
            'username': 'postgres',
            'password': 'password'
        }

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b'', b''))
        mock_process.returncode = 0

        with patch('src.database.restore.asyncio.create_subprocess_exec', return_value=mock_process):
            result = await restore_system.restore_point_in_time(
                'test_db',
                now - timedelta(minutes=30),
                connection_params
            )

            assert result.database_name == 'test_db'

    async def test_restore_with_decryption(self, restore_system, backup_system):
        """Test restore with decryption"""
        # This tests the decryption flow
        backup_file = Path(backup_system.backup_dir) / 'test_backup.sql.enc'

        # Create encrypted test file
        original_content = 'CREATE TABLE test (id INT);'
        encrypted_content = backup_system.encryptor.encrypt(original_content)

        with open(backup_file, 'w') as f:
            f.write(encrypted_content)

        metadata = BackupMetadata(
            backup_id='test_backup',
            database_type='postgresql',
            database_name='test_db',
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path=str(backup_file),
            compressed=False,
            encrypted=True,
            size_bytes=backup_file.stat().st_size,
            checksum='test_checksum',
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        # Test decryption
        decrypted_file = await restore_system._prepare_restore_file(metadata)

        assert os.path.exists(decrypted_file)
        with open(decrypted_file, 'r') as f:
            content = f.read()
            assert 'CREATE TABLE test' in content
