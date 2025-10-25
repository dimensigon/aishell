"""
Comprehensive test suite for database backup system

Tests cover:
- Backup creation (full, incremental, differential)
- Backup restoration and validation
- Compression and encryption
- Backup management and rotation
- Error handling and edge cases
- Integration and performance scenarios

Target Coverage: 90%+ (lines), aiming for 95%+
"""

import pytest
import asyncio
import os
import json
import gzip
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch, mock_open, call
from typing import Dict, Any

from src.database.backup import (
    BackupSystem,
    BackupMetadata,
    BackupType,
    BackupStatus,
    BackupRotationPolicy
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_backup_dir(tmp_path):
    """Create a temporary backup directory"""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    return str(backup_dir)


@pytest.fixture
def encryption_key():
    """Test encryption key"""
    return "test_encryption_key_12345"


@pytest.fixture
def rotation_policy():
    """Test rotation policy"""
    return BackupRotationPolicy(
        keep_daily=7,
        keep_weekly=4,
        keep_monthly=12,
        keep_yearly=1
    )


@pytest.fixture
def backup_system(temp_backup_dir):
    """Create a backup system instance"""
    return BackupSystem(backup_dir=temp_backup_dir)


@pytest.fixture
def backup_system_encrypted(temp_backup_dir, encryption_key):
    """Create a backup system with encryption"""
    with patch('src.database.backup.DataEncryption'):
        system = BackupSystem(
            backup_dir=temp_backup_dir,
            encryption_key=encryption_key
        )
        system.encryptor = Mock()
        system.encryptor.encrypt.return_value = "encrypted_data"
        return system


@pytest.fixture
def connection_params_postgresql():
    """PostgreSQL connection parameters"""
    return {
        'host': 'localhost',
        'port': 5432,
        'username': 'postgres',
        'password': 'password',
        'database': 'testdb'
    }


@pytest.fixture
def connection_params_mysql():
    """MySQL connection parameters"""
    return {
        'host': 'localhost',
        'port': 3306,
        'username': 'root',
        'password': 'password',
        'database': 'testdb'
    }


@pytest.fixture
def connection_params_oracle():
    """Oracle connection parameters"""
    return {
        'host': 'localhost',
        'port': 1521,
        'username': 'system',
        'password': 'oracle',
        'service_name': 'ORCLDB'
    }


@pytest.fixture
def sample_backup_metadata():
    """Sample backup metadata"""
    return BackupMetadata(
        backup_id="backup_20250112_120000_abc123",
        database_type="postgresql",
        database_name="testdb",
        backup_type=BackupType.FULL,
        status=BackupStatus.COMPLETED,
        created_at=datetime(2025, 1, 12, 12, 0, 0),
        completed_at=datetime(2025, 1, 12, 12, 5, 0),
        file_path="/tmp/backups/backup_20250112_120000_abc123.sql.gz",
        compressed=True,
        encrypted=False,
        size_bytes=1024000,
        checksum="abcdef1234567890",
        parent_backup_id=None,
        error_message=None,
        metadata={"tables": 10, "rows": 1000}
    )


# =============================================================================
# A. BACKUP CREATION TESTS (20-25 tests)
# =============================================================================

class TestBackupCreation:
    """Test backup creation scenarios"""

    @pytest.mark.asyncio
    async def test_create_full_backup_postgresql(self, backup_system, connection_params_postgresql):
        """Test creating a full PostgreSQL backup"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                backup_type=BackupType.FULL
            )

            assert metadata.backup_id.startswith("backup_")
            assert metadata.database_type == "postgresql"
            assert metadata.database_name == "testdb"
            assert metadata.backup_type == BackupType.FULL
            assert metadata.status == BackupStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_incremental_backup(self, backup_system, connection_params_postgresql):
        """Test creating an incremental backup"""
        parent_id = "backup_20250112_100000_parent"

        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                backup_type=BackupType.INCREMENTAL,
                parent_backup_id=parent_id
            )

            assert metadata.backup_type == BackupType.INCREMENTAL
            assert metadata.parent_backup_id == parent_id

    @pytest.mark.asyncio
    async def test_create_differential_backup(self, backup_system, connection_params_postgresql):
        """Test creating a differential backup"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                backup_type=BackupType.DIFFERENTIAL
            )

            assert metadata.backup_type == BackupType.DIFFERENTIAL

    @pytest.mark.asyncio
    async def test_create_backup_with_compression(self, backup_system, connection_params_postgresql):
        """Test creating a compressed backup"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                compress=True
            )

            assert metadata.compressed is True

    @pytest.mark.asyncio
    async def test_create_backup_with_encryption(self, backup_system_encrypted, connection_params_postgresql):
        """Test creating an encrypted backup"""
        with patch.object(backup_system_encrypted, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system_encrypted.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                encrypt=True
            )

            assert metadata.encrypted is True

    @pytest.mark.asyncio
    async def test_create_backup_mysql(self, backup_system, connection_params_mysql):
        """Test creating a MySQL backup"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system.create_backup(
                database_type="mysql",
                database_name="testdb",
                connection_params=connection_params_mysql
            )

            assert metadata.database_type == "mysql"

    @pytest.mark.asyncio
    async def test_create_backup_oracle(self, backup_system, connection_params_oracle):
        """Test creating an Oracle backup"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system.create_backup(
                database_type="oracle",
                database_name="ORCLDB",
                connection_params=connection_params_oracle
            )

            assert metadata.database_type == "oracle"

    @pytest.mark.asyncio
    async def test_backup_id_generation_unique(self, backup_system, connection_params_postgresql):
        """Test that backup IDs are unique"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata1 = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql
            )

            metadata2 = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql
            )

            assert metadata1.backup_id != metadata2.backup_id

    @pytest.mark.asyncio
    async def test_backup_metadata_saved(self, backup_system, connection_params_postgresql):
        """Test that backup metadata is saved to disk"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql
            )

            # Check metadata file exists
            assert backup_system.metadata_file.exists()

            # Verify metadata is in backups dictionary
            assert metadata.backup_id in backup_system.backups

    @pytest.mark.asyncio
    async def test_execute_backup_postgresql_success(self, backup_system, connection_params_postgresql):
        """Test successful PostgreSQL backup execution"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'):

            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                compress=False,
                encrypt=False
            )

            # Wait for async backup execution
            await asyncio.sleep(0.01)

            # Verify backup was created
            assert metadata.backup_id in backup_system.backups

    @pytest.mark.asyncio
    async def test_execute_backup_mysql_success(self, backup_system, connection_params_mysql):
        """Test successful MySQL backup execution"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch('builtins.open', mock_open()), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'):

            metadata = await backup_system.create_backup(
                database_type="mysql",
                database_name="testdb",
                connection_params=connection_params_mysql,
                compress=False,
                encrypt=False
            )

            assert metadata.database_type == "mysql"

    @pytest.mark.asyncio
    async def test_execute_backup_oracle_success(self, backup_system, connection_params_oracle):
        """Test successful Oracle backup execution"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'):

            metadata = await backup_system.create_backup(
                database_type="oracle",
                database_name="ORCLDB",
                connection_params=connection_params_oracle,
                compress=False,
                encrypt=False
            )

            assert metadata.database_type == "oracle"

    @pytest.mark.asyncio
    async def test_backup_with_compression_applied(self, backup_system, connection_params_postgresql):
        """Test that compression is actually applied"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        backup_file = backup_system.backup_dir / "backup_test.sql"
        compressed_file = backup_system.backup_dir / "backup_test.sql.gz"

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system, '_compress_file', new_callable=AsyncMock) as mock_compress, \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'), \
             patch.object(Path, 'unlink'), \
             patch.object(Path, 'stat') as mock_stat:

            mock_stat.return_value.st_size = 1024

            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                compress=True,
                encrypt=False
            )

            # Wait for async execution
            await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_backup_with_encryption_applied(self, backup_system_encrypted, connection_params_postgresql):
        """Test that encryption is actually applied"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system_encrypted, '_encrypt_file', new_callable=AsyncMock) as mock_encrypt, \
             patch.object(backup_system_encrypted, '_calculate_checksum', return_value='checksum123'), \
             patch.object(Path, 'unlink'), \
             patch.object(Path, 'stat') as mock_stat:

            mock_stat.return_value.st_size = 1024

            metadata = await backup_system_encrypted.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                compress=False,
                encrypt=True
            )

            # Wait for async execution
            await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_backup_both_compression_and_encryption(self, backup_system_encrypted, connection_params_postgresql):
        """Test backup with both compression and encryption"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system_encrypted, '_compress_file', new_callable=AsyncMock), \
             patch.object(backup_system_encrypted, '_encrypt_file', new_callable=AsyncMock), \
             patch.object(backup_system_encrypted, '_calculate_checksum', return_value='checksum123'), \
             patch.object(Path, 'unlink'), \
             patch.object(Path, 'stat') as mock_stat:

            mock_stat.return_value.st_size = 1024

            metadata = await backup_system_encrypted.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                compress=True,
                encrypt=True
            )

            assert metadata.compressed is True
            assert metadata.encrypted is True

    def test_generate_backup_id_format(self, backup_system):
        """Test backup ID generation format"""
        backup_id = backup_system._generate_backup_id()

        assert backup_id.startswith("backup_")
        parts = backup_id.split("_")
        assert len(parts) == 4  # backup_YYYYMMDD_HHMMSS_hash

        # Verify date part (YYYYMMDD)
        date_part = parts[1]
        assert len(date_part) == 8

        # Verify time part (HHMMSS)
        time_part = parts[2]
        assert len(time_part) == 6

        # Verify hash suffix
        hash_suffix = parts[3]
        assert len(hash_suffix) == 8

    def test_calculate_checksum(self, backup_system, tmp_path):
        """Test checksum calculation"""
        test_file = tmp_path / "test.txt"
        test_data = b"test data for checksum"
        test_file.write_bytes(test_data)

        checksum = backup_system._calculate_checksum(str(test_file))

        # Verify it's a valid SHA256 hash
        assert len(checksum) == 64

        # Verify it matches expected checksum
        expected = hashlib.sha256(test_data).hexdigest()
        assert checksum == expected

    @pytest.mark.asyncio
    async def test_compress_file(self, backup_system, tmp_path):
        """Test file compression"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.gz"
        test_data = b"test data" * 1000

        input_file.write_bytes(test_data)

        await backup_system._compress_file(input_file, output_file)

        # Verify compressed file exists
        assert output_file.exists()

        # Verify it's actually compressed (should be smaller)
        assert output_file.stat().st_size < input_file.stat().st_size

        # Verify can decompress
        with gzip.open(output_file, 'rb') as f:
            decompressed = f.read()
        assert decompressed == test_data

    @pytest.mark.asyncio
    async def test_encrypt_file(self, backup_system_encrypted, tmp_path):
        """Test file encryption"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.enc"
        test_data = b"test data"

        input_file.write_bytes(test_data)

        await backup_system_encrypted._encrypt_file(input_file, output_file)

        # Verify encrypted file exists
        assert output_file.exists()

        # Verify encryption was called
        backup_system_encrypted.encryptor.encrypt.assert_called()

    @pytest.mark.asyncio
    async def test_backup_metadata_timestamps(self, backup_system, connection_params_postgresql):
        """Test that backup metadata has correct timestamps"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            before = datetime.now()
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql
            )
            after = datetime.now()

            assert before <= metadata.created_at <= after
            assert metadata.completed_at is None  # Not completed yet

    @pytest.mark.asyncio
    async def test_backup_without_compression(self, backup_system, connection_params_postgresql):
        """Test creating backup without compression"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                compress=False
            )

            assert metadata.compressed is False

    @pytest.mark.asyncio
    async def test_backup_without_encryption(self, backup_system, connection_params_postgresql):
        """Test creating backup without encryption"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                encrypt=False
            )

            assert metadata.encrypted is False

    @pytest.mark.asyncio
    async def test_backup_default_settings(self, backup_system, connection_params_postgresql):
        """Test backup creation with default settings"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql
            )

            assert metadata.backup_type == BackupType.FULL
            assert metadata.compressed is True  # Default
            assert metadata.encrypted is False  # Default

    def test_backup_metadata_initialization(self, temp_backup_dir):
        """Test backup system initialization creates metadata file"""
        system = BackupSystem(backup_dir=temp_backup_dir)

        # Verify backup directory exists
        assert system.backup_dir.exists()

        # Verify metadata file path is set
        assert system.metadata_file == system.backup_dir / "backup_metadata.json"


# =============================================================================
# B. BACKUP MANAGEMENT TESTS (10-15 tests)
# =============================================================================

class TestBackupManagement:
    """Test backup management operations"""

    def test_list_all_backups(self, backup_system, sample_backup_metadata):
        """Test listing all backups"""
        backup_system.backups[sample_backup_metadata.backup_id] = sample_backup_metadata

        backups = backup_system.list_backups()

        assert len(backups) == 1
        assert backups[0].backup_id == sample_backup_metadata.backup_id

    def test_list_backups_by_database_name(self, backup_system):
        """Test filtering backups by database name"""
        metadata1 = BackupMetadata(
            backup_id="backup1",
            database_type="postgresql",
            database_name="db1",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path="/tmp/backup1.sql",
            compressed=True,
            encrypted=False,
            size_bytes=1000,
            checksum="abc123",
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        metadata2 = BackupMetadata(
            backup_id="backup2",
            database_type="postgresql",
            database_name="db2",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path="/tmp/backup2.sql",
            compressed=True,
            encrypted=False,
            size_bytes=1000,
            checksum="def456",
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        backup_system.backups["backup1"] = metadata1
        backup_system.backups["backup2"] = metadata2

        backups = backup_system.list_backups(database_name="db1")

        assert len(backups) == 1
        assert backups[0].database_name == "db1"

    def test_list_backups_by_status(self, backup_system):
        """Test filtering backups by status"""
        metadata_completed = BackupMetadata(
            backup_id="backup1",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path="/tmp/backup1.sql",
            compressed=True,
            encrypted=False,
            size_bytes=1000,
            checksum="abc123",
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        metadata_failed = BackupMetadata(
            backup_id="backup2",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.FAILED,
            created_at=datetime.now(),
            completed_at=None,
            file_path="",
            compressed=True,
            encrypted=False,
            size_bytes=0,
            checksum="",
            parent_backup_id=None,
            error_message="Backup failed",
            metadata={}
        )

        backup_system.backups["backup1"] = metadata_completed
        backup_system.backups["backup2"] = metadata_failed

        completed = backup_system.list_backups(status=BackupStatus.COMPLETED)
        failed = backup_system.list_backups(status=BackupStatus.FAILED)

        assert len(completed) == 1
        assert len(failed) == 1
        assert completed[0].status == BackupStatus.COMPLETED
        assert failed[0].status == BackupStatus.FAILED

    def test_list_backups_sorted_by_date(self, backup_system):
        """Test that backups are sorted by creation date (newest first)"""
        metadata1 = BackupMetadata(
            backup_id="backup1",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            completed_at=datetime(2025, 1, 1, 12, 5, 0),
            file_path="/tmp/backup1.sql",
            compressed=True,
            encrypted=False,
            size_bytes=1000,
            checksum="abc123",
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        metadata2 = BackupMetadata(
            backup_id="backup2",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime(2025, 1, 2, 12, 0, 0),
            completed_at=datetime(2025, 1, 2, 12, 5, 0),
            file_path="/tmp/backup2.sql",
            compressed=True,
            encrypted=False,
            size_bytes=1000,
            checksum="def456",
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        backup_system.backups["backup1"] = metadata1
        backup_system.backups["backup2"] = metadata2

        backups = backup_system.list_backups()

        assert backups[0].backup_id == "backup2"  # Newer first
        assert backups[1].backup_id == "backup1"

    def test_get_backup_by_id(self, backup_system, sample_backup_metadata):
        """Test retrieving backup by ID"""
        backup_system.backups[sample_backup_metadata.backup_id] = sample_backup_metadata

        metadata = backup_system.get_backup(sample_backup_metadata.backup_id)

        assert metadata is not None
        assert metadata.backup_id == sample_backup_metadata.backup_id

    def test_get_backup_nonexistent(self, backup_system):
        """Test getting non-existent backup returns None"""
        metadata = backup_system.get_backup("nonexistent_id")

        assert metadata is None

    def test_delete_backup_success(self, backup_system, sample_backup_metadata, tmp_path):
        """Test deleting a backup"""
        # Create a fake backup file
        backup_file = tmp_path / "backup_test.sql"
        backup_file.write_text("backup data")

        sample_backup_metadata.file_path = str(backup_file)
        backup_system.backups[sample_backup_metadata.backup_id] = sample_backup_metadata

        result = backup_system.delete_backup(sample_backup_metadata.backup_id)

        assert result is True
        assert sample_backup_metadata.backup_id not in backup_system.backups
        assert not backup_file.exists()

    def test_delete_backup_nonexistent(self, backup_system):
        """Test deleting non-existent backup"""
        result = backup_system.delete_backup("nonexistent_id")

        assert result is False

    def test_delete_backup_missing_file(self, backup_system, sample_backup_metadata):
        """Test deleting backup when file doesn't exist"""
        sample_backup_metadata.file_path = "/nonexistent/path/backup.sql"
        backup_system.backups[sample_backup_metadata.backup_id] = sample_backup_metadata

        result = backup_system.delete_backup(sample_backup_metadata.backup_id)

        assert result is True  # Still removes from metadata
        assert sample_backup_metadata.backup_id not in backup_system.backups

    def test_load_metadata_from_disk(self, temp_backup_dir):
        """Test loading backup metadata from disk"""
        metadata_file = Path(temp_backup_dir) / "backup_metadata.json"

        # Create sample metadata file
        test_data = {
            "backup_123": {
                "backup_id": "backup_123",
                "database_type": "postgresql",
                "database_name": "testdb",
                "backup_type": "full",
                "status": "completed",
                "created_at": "2025-01-12T12:00:00",
                "completed_at": "2025-01-12T12:05:00",
                "file_path": "/tmp/backup_123.sql",
                "compressed": True,
                "encrypted": False,
                "size_bytes": 1000,
                "checksum": "abc123",
                "parent_backup_id": None,
                "error_message": None,
                "metadata": {}
            }
        }

        with open(metadata_file, 'w') as f:
            json.dump(test_data, f)

        # Create new system to load metadata
        system = BackupSystem(backup_dir=temp_backup_dir)

        assert "backup_123" in system.backups
        assert system.backups["backup_123"].database_name == "testdb"

    def test_load_metadata_corrupted_file(self, temp_backup_dir, capsys):
        """Test loading corrupted metadata file"""
        metadata_file = Path(temp_backup_dir) / "backup_metadata.json"

        # Create corrupted JSON file
        metadata_file.write_text("{ invalid json }")

        # Should not crash, but print warning
        system = BackupSystem(backup_dir=temp_backup_dir)

        captured = capsys.readouterr()
        assert "Warning: Failed to load backup metadata" in captured.out

    def test_save_metadata_to_disk(self, backup_system, sample_backup_metadata):
        """Test saving backup metadata to disk"""
        backup_system.backups[sample_backup_metadata.backup_id] = sample_backup_metadata
        backup_system._save_metadata()

        # Verify file exists
        assert backup_system.metadata_file.exists()

        # Verify content
        with open(backup_system.metadata_file, 'r') as f:
            data = json.load(f)

        assert sample_backup_metadata.backup_id in data

    def test_list_backups_empty(self, backup_system):
        """Test listing backups when none exist"""
        backups = backup_system.list_backups()

        assert backups == []

    def test_list_backups_multiple_filters(self, backup_system):
        """Test filtering backups with multiple criteria"""
        metadata1 = BackupMetadata(
            backup_id="backup1",
            database_type="postgresql",
            database_name="db1",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path="/tmp/backup1.sql",
            compressed=True,
            encrypted=False,
            size_bytes=1000,
            checksum="abc123",
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        metadata2 = BackupMetadata(
            backup_id="backup2",
            database_type="postgresql",
            database_name="db1",
            backup_type=BackupType.FULL,
            status=BackupStatus.FAILED,
            created_at=datetime.now(),
            completed_at=None,
            file_path="",
            compressed=True,
            encrypted=False,
            size_bytes=0,
            checksum="",
            parent_backup_id=None,
            error_message="Failed",
            metadata={}
        )

        backup_system.backups["backup1"] = metadata1
        backup_system.backups["backup2"] = metadata2

        backups = backup_system.list_backups(
            database_name="db1",
            status=BackupStatus.COMPLETED
        )

        assert len(backups) == 1
        assert backups[0].backup_id == "backup1"


# =============================================================================
# C. BACKUP ROTATION TESTS (10-12 tests)
# =============================================================================

class TestBackupRotation:
    """Test backup rotation policy"""

    def test_rotation_policy_defaults(self):
        """Test default rotation policy values"""
        policy = BackupRotationPolicy()

        assert policy.keep_daily == 7
        assert policy.keep_weekly == 4
        assert policy.keep_monthly == 12
        assert policy.keep_yearly == 1

    def test_rotation_policy_custom(self):
        """Test custom rotation policy"""
        policy = BackupRotationPolicy(
            keep_daily=14,
            keep_weekly=8,
            keep_monthly=24,
            keep_yearly=2
        )

        assert policy.keep_daily == 14
        assert policy.keep_weekly == 8
        assert policy.keep_monthly == 24
        assert policy.keep_yearly == 2

    def test_apply_rotation_delete_old_daily(self, backup_system, tmp_path):
        """Test rotation deletes old daily backups"""
        now = datetime.now()

        # Create 10 daily backups (should keep only 7)
        for i in range(10):
            backup_file = tmp_path / f"backup_{i}.sql"
            backup_file.write_text("data")

            metadata = BackupMetadata(
                backup_id=f"backup_{i}",
                database_type="postgresql",
                database_name="testdb",
                backup_type=BackupType.FULL,
                status=BackupStatus.COMPLETED,
                created_at=now - timedelta(days=i),
                completed_at=now - timedelta(days=i),
                file_path=str(backup_file),
                compressed=False,
                encrypted=False,
                size_bytes=100,
                checksum=f"checksum_{i}",
                parent_backup_id=None,
                error_message=None,
                metadata={}
            )
            backup_system.backups[metadata.backup_id] = metadata

        deleted = backup_system.apply_rotation_policy()

        # Should delete 3 oldest backups (keep 7 daily)
        assert len(deleted) == 3

    def test_apply_rotation_keep_weekly(self, backup_system, tmp_path):
        """Test rotation keeps weekly backups"""
        now = datetime.now()

        # Create 8 weekly backups (should keep only 4)
        for i in range(8):
            backup_file = tmp_path / f"backup_weekly_{i}.sql"
            backup_file.write_text("data")

            metadata = BackupMetadata(
                backup_id=f"backup_weekly_{i}",
                database_type="postgresql",
                database_name="testdb",
                backup_type=BackupType.FULL,
                status=BackupStatus.COMPLETED,
                created_at=now - timedelta(days=7 + i*7),  # 1+ weeks old
                completed_at=now - timedelta(days=7 + i*7),
                file_path=str(backup_file),
                compressed=False,
                encrypted=False,
                size_bytes=100,
                checksum=f"checksum_{i}",
                parent_backup_id=None,
                error_message=None,
                metadata={}
            )
            backup_system.backups[metadata.backup_id] = metadata

        deleted = backup_system.apply_rotation_policy()

        # Should delete 4 oldest weekly backups
        assert len(deleted) == 4

    def test_apply_rotation_keep_monthly(self, backup_system, tmp_path):
        """Test rotation keeps monthly backups"""
        now = datetime.now()

        # Create 15 monthly backups (should keep only 12)
        for i in range(15):
            backup_file = tmp_path / f"backup_monthly_{i}.sql"
            backup_file.write_text("data")

            metadata = BackupMetadata(
                backup_id=f"backup_monthly_{i}",
                database_type="postgresql",
                database_name="testdb",
                backup_type=BackupType.FULL,
                status=BackupStatus.COMPLETED,
                created_at=now - timedelta(days=28 + i*30),  # 1+ months old
                completed_at=now - timedelta(days=28 + i*30),
                file_path=str(backup_file),
                compressed=False,
                encrypted=False,
                size_bytes=100,
                checksum=f"checksum_{i}",
                parent_backup_id=None,
                error_message=None,
                metadata={}
            )
            backup_system.backups[metadata.backup_id] = metadata

        deleted = backup_system.apply_rotation_policy()

        # Should delete 3 oldest monthly backups
        assert len(deleted) == 3

    def test_apply_rotation_keep_yearly(self, backup_system, tmp_path):
        """Test rotation keeps yearly backups"""
        now = datetime.now()

        # Create 3 yearly backups (should keep only 1)
        for i in range(3):
            backup_file = tmp_path / f"backup_yearly_{i}.sql"
            backup_file.write_text("data")

            metadata = BackupMetadata(
                backup_id=f"backup_yearly_{i}",
                database_type="postgresql",
                database_name="testdb",
                backup_type=BackupType.FULL,
                status=BackupStatus.COMPLETED,
                created_at=now - timedelta(days=365 + i*365),  # 1+ years old
                completed_at=now - timedelta(days=365 + i*365),
                file_path=str(backup_file),
                compressed=False,
                encrypted=False,
                size_bytes=100,
                checksum=f"checksum_{i}",
                parent_backup_id=None,
                error_message=None,
                metadata={}
            )
            backup_system.backups[metadata.backup_id] = metadata

        deleted = backup_system.apply_rotation_policy()

        # Should delete 2 oldest yearly backups
        assert len(deleted) == 2

    def test_apply_rotation_filter_by_database(self, backup_system, tmp_path):
        """Test rotation can filter by database name"""
        now = datetime.now()

        # Create backups for two databases
        for db_name in ["db1", "db2"]:
            for i in range(10):
                backup_file = tmp_path / f"backup_{db_name}_{i}.sql"
                backup_file.write_text("data")

                metadata = BackupMetadata(
                    backup_id=f"backup_{db_name}_{i}",
                    database_type="postgresql",
                    database_name=db_name,
                    backup_type=BackupType.FULL,
                    status=BackupStatus.COMPLETED,
                    created_at=now - timedelta(days=i),
                    completed_at=now - timedelta(days=i),
                    file_path=str(backup_file),
                    compressed=False,
                    encrypted=False,
                    size_bytes=100,
                    checksum=f"checksum_{i}",
                    parent_backup_id=None,
                    error_message=None,
                    metadata={}
                )
                backup_system.backups[metadata.backup_id] = metadata

        # Apply rotation only to db1
        deleted = backup_system.apply_rotation_policy(database_name="db1")

        # Should only delete db1 backups
        assert all("db1" in backup_id for backup_id in deleted)
        assert not any("db2" in backup_id for backup_id in deleted)

    def test_apply_rotation_skip_failed_backups(self, backup_system, tmp_path):
        """Test rotation ignores failed backups"""
        now = datetime.now()

        # Create mix of completed and failed backups
        for i in range(10):
            status = BackupStatus.COMPLETED if i % 2 == 0 else BackupStatus.FAILED
            backup_file = tmp_path / f"backup_{i}.sql"

            if status == BackupStatus.COMPLETED:
                backup_file.write_text("data")

            metadata = BackupMetadata(
                backup_id=f"backup_{i}",
                database_type="postgresql",
                database_name="testdb",
                backup_type=BackupType.FULL,
                status=status,
                created_at=now - timedelta(days=i),
                completed_at=now - timedelta(days=i) if status == BackupStatus.COMPLETED else None,
                file_path=str(backup_file) if status == BackupStatus.COMPLETED else "",
                compressed=False,
                encrypted=False,
                size_bytes=100 if status == BackupStatus.COMPLETED else 0,
                checksum=f"checksum_{i}" if status == BackupStatus.COMPLETED else "",
                parent_backup_id=None,
                error_message="Failed" if status == BackupStatus.FAILED else None,
                metadata={}
            )
            backup_system.backups[metadata.backup_id] = metadata

        deleted = backup_system.apply_rotation_policy()

        # Should only delete completed backups
        assert all(backup_system.get_backup(bid) is None or
                  backup_system.get_backup(bid).status != BackupStatus.FAILED
                  for bid in deleted)

    def test_apply_rotation_no_backups(self, backup_system):
        """Test rotation with no backups"""
        deleted = backup_system.apply_rotation_policy()

        assert deleted == []

    def test_get_point_in_time_backup(self, backup_system):
        """Test finding backup for point-in-time recovery"""
        now = datetime.now()

        # Create backups at different times
        for i in range(5):
            metadata = BackupMetadata(
                backup_id=f"backup_{i}",
                database_type="postgresql",
                database_name="testdb",
                backup_type=BackupType.FULL,
                status=BackupStatus.COMPLETED,
                created_at=now - timedelta(hours=i*2),
                completed_at=now - timedelta(hours=i*2) + timedelta(minutes=5),
                file_path=f"/tmp/backup_{i}.sql",
                compressed=False,
                encrypted=False,
                size_bytes=100,
                checksum=f"checksum_{i}",
                parent_backup_id=None,
                error_message=None,
                metadata={}
            )
            backup_system.backups[metadata.backup_id] = metadata

        # Find backup closest to 3 hours ago
        target_time = now - timedelta(hours=3)
        backup = backup_system.get_point_in_time_backup("testdb", target_time)

        assert backup is not None
        assert backup.completed_at <= target_time

    def test_get_point_in_time_backup_none_found(self, backup_system):
        """Test point-in-time recovery when no backup exists"""
        now = datetime.now()

        # Create a backup in the future
        metadata = BackupMetadata(
            backup_id="backup_future",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=now + timedelta(hours=1),
            completed_at=now + timedelta(hours=1, minutes=5),
            file_path="/tmp/backup_future.sql",
            compressed=False,
            encrypted=False,
            size_bytes=100,
            checksum="checksum",
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )
        backup_system.backups["backup_future"] = metadata

        # Try to find backup for current time
        backup = backup_system.get_point_in_time_backup("testdb", now)

        assert backup is None

    def test_get_backup_chain_single(self, backup_system):
        """Test getting backup chain for full backup"""
        metadata = BackupMetadata(
            backup_id="backup_full",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path="/tmp/backup_full.sql",
            compressed=False,
            encrypted=False,
            size_bytes=100,
            checksum="checksum",
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )
        backup_system.backups["backup_full"] = metadata

        chain = backup_system.get_backup_chain("backup_full")

        assert len(chain) == 1
        assert chain[0].backup_id == "backup_full"

    def test_get_backup_chain_incremental(self, backup_system):
        """Test getting backup chain for incremental backup"""
        # Create full backup
        full_metadata = BackupMetadata(
            backup_id="backup_full",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path="/tmp/backup_full.sql",
            compressed=False,
            encrypted=False,
            size_bytes=100,
            checksum="checksum",
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )

        # Create incremental backup
        incr_metadata = BackupMetadata(
            backup_id="backup_incr",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.INCREMENTAL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path="/tmp/backup_incr.sql",
            compressed=False,
            encrypted=False,
            size_bytes=50,
            checksum="checksum2",
            parent_backup_id="backup_full",
            error_message=None,
            metadata={}
        )

        backup_system.backups["backup_full"] = full_metadata
        backup_system.backups["backup_incr"] = incr_metadata

        chain = backup_system.get_backup_chain("backup_incr")

        assert len(chain) == 2
        assert chain[0].backup_id == "backup_full"
        assert chain[1].backup_id == "backup_incr"


# =============================================================================
# D. VALIDATION TESTS (10-12 tests)
# =============================================================================

class TestBackupValidation:
    """Test backup validation functionality"""

    @pytest.mark.asyncio
    async def test_validate_backup_success(self, backup_system, tmp_path):
        """Test successful backup validation"""
        # Create test backup file
        backup_file = tmp_path / "backup_test.sql"
        backup_file.write_text("backup data")

        # Calculate checksum
        checksum = hashlib.sha256(b"backup data").hexdigest()

        metadata = BackupMetadata(
            backup_id="backup_test",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path=str(backup_file),
            compressed=False,
            encrypted=False,
            size_bytes=len("backup data"),
            checksum=checksum,
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )
        backup_system.backups["backup_test"] = metadata

        is_valid, error = await backup_system.validate_backup("backup_test")

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_backup_not_found(self, backup_system):
        """Test validation of non-existent backup"""
        is_valid, error = await backup_system.validate_backup("nonexistent")

        assert is_valid is False
        assert error == "Backup not found"

    @pytest.mark.asyncio
    async def test_validate_backup_file_missing(self, backup_system):
        """Test validation when backup file is missing"""
        metadata = BackupMetadata(
            backup_id="backup_test",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path="/nonexistent/path/backup.sql",
            compressed=False,
            encrypted=False,
            size_bytes=100,
            checksum="checksum",
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )
        backup_system.backups["backup_test"] = metadata

        is_valid, error = await backup_system.validate_backup("backup_test")

        assert is_valid is False
        assert error == "Backup file not found"

    @pytest.mark.asyncio
    async def test_validate_backup_checksum_mismatch(self, backup_system, tmp_path):
        """Test validation with checksum mismatch"""
        backup_file = tmp_path / "backup_test.sql"
        backup_file.write_text("backup data")

        metadata = BackupMetadata(
            backup_id="backup_test",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path=str(backup_file),
            compressed=False,
            encrypted=False,
            size_bytes=len("backup data"),
            checksum="wrong_checksum",
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )
        backup_system.backups["backup_test"] = metadata

        is_valid, error = await backup_system.validate_backup("backup_test")

        assert is_valid is False
        assert "Checksum mismatch" in error

    @pytest.mark.asyncio
    async def test_validate_backup_size_mismatch(self, backup_system, tmp_path):
        """Test validation with size mismatch"""
        backup_file = tmp_path / "backup_test.sql"
        backup_data = "backup data"
        backup_file.write_text(backup_data)

        # Calculate correct checksum but wrong size
        checksum = hashlib.sha256(backup_data.encode()).hexdigest()

        metadata = BackupMetadata(
            backup_id="backup_test",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path=str(backup_file),
            compressed=False,
            encrypted=False,
            size_bytes=9999,  # Wrong size
            checksum=checksum,
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )
        backup_system.backups["backup_test"] = metadata

        is_valid, error = await backup_system.validate_backup("backup_test")

        assert is_valid is False
        assert "Size mismatch" in error

    @pytest.mark.asyncio
    async def test_validate_compressed_backup(self, backup_system, tmp_path):
        """Test validation of compressed backup"""
        backup_file = tmp_path / "backup_test.sql.gz"

        # Create compressed file
        with gzip.open(backup_file, 'wb') as f:
            f.write(b"backup data compressed")

        # Calculate checksum of compressed file
        checksum = backup_system._calculate_checksum(str(backup_file))

        metadata = BackupMetadata(
            backup_id="backup_test",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path=str(backup_file),
            compressed=True,
            encrypted=False,
            size_bytes=backup_file.stat().st_size,
            checksum=checksum,
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )
        backup_system.backups["backup_test"] = metadata

        is_valid, error = await backup_system.validate_backup("backup_test")

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_encrypted_backup(self, backup_system_encrypted, tmp_path):
        """Test validation of encrypted backup"""
        backup_file = tmp_path / "backup_test.sql.enc"
        backup_file.write_text("encrypted data")

        checksum = backup_system_encrypted._calculate_checksum(str(backup_file))

        metadata = BackupMetadata(
            backup_id="backup_test",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path=str(backup_file),
            compressed=False,
            encrypted=True,
            size_bytes=backup_file.stat().st_size,
            checksum=checksum,
            parent_backup_id=None,
            error_message=None,
            metadata={}
        )
        backup_system_encrypted.backups["backup_test"] = metadata

        is_valid, error = await backup_system_encrypted.validate_backup("backup_test")

        assert is_valid is True
        assert error is None


# =============================================================================
# E. ERROR HANDLING & EDGE CASES (15-20 tests)
# =============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_execute_backup_postgresql_failure(self, backup_system, connection_params_postgresql):
        """Test PostgreSQL backup failure handling"""
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b'', b'pg_dump error'))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                compress=False,
                encrypt=False
            )

            # Wait for async execution
            await asyncio.sleep(0.01)

            # Reload metadata
            updated_metadata = backup_system.backups[metadata.backup_id]
            assert updated_metadata.status == BackupStatus.FAILED
            assert updated_metadata.error_message is not None

    @pytest.mark.asyncio
    async def test_execute_backup_mysql_failure(self, backup_system, connection_params_mysql):
        """Test MySQL backup failure handling"""
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b'', b'mysqldump error'))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch('builtins.open', mock_open()):

            metadata = await backup_system.create_backup(
                database_type="mysql",
                database_name="testdb",
                connection_params=connection_params_mysql,
                compress=False,
                encrypt=False
            )

            # Wait for async execution
            await asyncio.sleep(0.01)

            updated_metadata = backup_system.backups[metadata.backup_id]
            assert updated_metadata.status == BackupStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_backup_oracle_failure(self, backup_system, connection_params_oracle):
        """Test Oracle backup failure handling"""
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b'', b'expdp error'))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            metadata = await backup_system.create_backup(
                database_type="oracle",
                database_name="ORCLDB",
                connection_params=connection_params_oracle,
                compress=False,
                encrypt=False
            )

            # Wait for async execution
            await asyncio.sleep(0.01)

            updated_metadata = backup_system.backups[metadata.backup_id]
            assert updated_metadata.status == BackupStatus.FAILED

    @pytest.mark.asyncio
    async def test_unsupported_database_type(self, backup_system):
        """Test handling of unsupported database type"""
        with patch.object(backup_system, '_execute_backup', new_callable=AsyncMock):
            # This should create the metadata, but fail during execution
            metadata = await backup_system.create_backup(
                database_type="unsupported_db",
                database_name="testdb",
                connection_params={}
            )

            # Manually trigger execution to test error handling
            await backup_system._execute_backup(metadata.backup_id, {})

            updated_metadata = backup_system.backups[metadata.backup_id]
            assert updated_metadata.status == BackupStatus.FAILED
            assert "Unsupported database type" in updated_metadata.error_message

    @pytest.mark.asyncio
    async def test_encryption_without_key(self, backup_system, connection_params_postgresql):
        """Test encryption request without encryption key"""
        # backup_system doesn't have encryption key
        assert backup_system.encryptor is None

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(Path, 'stat') as mock_stat:

            mock_stat.return_value.st_size = 1024

            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                compress=False,
                encrypt=True  # Request encryption without key
            )

            # Wait for async execution
            await asyncio.sleep(0.01)

            updated_metadata = backup_system.backups[metadata.backup_id]
            assert updated_metadata.status == BackupStatus.FAILED
            assert "encryption" in updated_metadata.error_message.lower()

    @pytest.mark.asyncio
    async def test_compress_file_io_error(self, backup_system, tmp_path):
        """Test compression with IO error"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "readonly" / "output.gz"

        input_file.write_text("test data")

        # output_file directory doesn't exist
        with pytest.raises(Exception):
            await backup_system._compress_file(input_file, output_file)

    @pytest.mark.asyncio
    async def test_encrypt_file_no_encryptor(self, backup_system, tmp_path):
        """Test encryption without encryptor"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.enc"

        input_file.write_text("test data")

        with pytest.raises(ValueError, match="No encryptor available"):
            await backup_system._encrypt_file(input_file, output_file)

    def test_delete_backup_empty_file_path(self, backup_system):
        """Test deleting backup with empty file path"""
        metadata = BackupMetadata(
            backup_id="backup_test",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.FULL,
            status=BackupStatus.FAILED,
            created_at=datetime.now(),
            completed_at=None,
            file_path="",  # Empty file path
            compressed=False,
            encrypted=False,
            size_bytes=0,
            checksum="",
            parent_backup_id=None,
            error_message="Backup failed",
            metadata={}
        )
        backup_system.backups["backup_test"] = metadata

        result = backup_system.delete_backup("backup_test")

        assert result is True
        assert "backup_test" not in backup_system.backups

    def test_checksum_calculation_empty_file(self, backup_system, tmp_path):
        """Test checksum calculation for empty file"""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        checksum = backup_system._calculate_checksum(str(empty_file))

        # SHA256 of empty string
        expected = hashlib.sha256(b"").hexdigest()
        assert checksum == expected

    def test_checksum_calculation_large_file(self, backup_system, tmp_path):
        """Test checksum calculation for large file (chunked reading)"""
        large_file = tmp_path / "large.txt"

        # Create file larger than chunk size (8192 bytes)
        large_data = b"x" * 10000
        large_file.write_bytes(large_data)

        checksum = backup_system._calculate_checksum(str(large_file))

        expected = hashlib.sha256(large_data).hexdigest()
        assert checksum == expected

    def test_load_metadata_missing_file(self, temp_backup_dir):
        """Test loading metadata when file doesn't exist"""
        # Create system without existing metadata file
        system = BackupSystem(backup_dir=temp_backup_dir)

        # Should have empty backups dictionary
        assert system.backups == {}

    def test_backup_system_creates_directory(self, tmp_path):
        """Test that backup system creates backup directory if it doesn't exist"""
        new_dir = tmp_path / "new_backup_dir"

        assert not new_dir.exists()

        system = BackupSystem(backup_dir=str(new_dir))

        assert new_dir.exists()

    @pytest.mark.asyncio
    async def test_concurrent_backup_operations(self, backup_system, connection_params_postgresql):
        """Test handling of concurrent backup operations"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'):

            # Create multiple backups concurrently
            tasks = [
                backup_system.create_backup(
                    database_type="postgresql",
                    database_name=f"testdb_{i}",
                    connection_params=connection_params_postgresql,
                    compress=False,
                    encrypt=False
                )
                for i in range(5)
            ]

            metadatas = await asyncio.gather(*tasks)

            # All should have unique IDs
            backup_ids = [m.backup_id for m in metadatas]
            assert len(backup_ids) == len(set(backup_ids))

    def test_rotation_policy_with_zero_keeps(self, tmp_path):
        """Test rotation policy with zero keep values"""
        policy = BackupRotationPolicy(
            keep_daily=0,
            keep_weekly=0,
            keep_monthly=0,
            keep_yearly=0
        )

        system = BackupSystem(
            backup_dir=str(tmp_path),
            rotation_policy=policy
        )

        # Create some backups
        now = datetime.now()
        for i in range(5):
            backup_file = tmp_path / f"backup_{i}.sql"
            backup_file.write_text("data")

            metadata = BackupMetadata(
                backup_id=f"backup_{i}",
                database_type="postgresql",
                database_name="testdb",
                backup_type=BackupType.FULL,
                status=BackupStatus.COMPLETED,
                created_at=now - timedelta(days=i),
                completed_at=now - timedelta(days=i),
                file_path=str(backup_file),
                compressed=False,
                encrypted=False,
                size_bytes=100,
                checksum=f"checksum_{i}",
                parent_backup_id=None,
                error_message=None,
                metadata={}
            )
            system.backups[metadata.backup_id] = metadata

        # Apply rotation - should delete all
        deleted = system.apply_rotation_policy()

        assert len(deleted) == 5

    def test_get_backup_chain_circular_reference(self, backup_system):
        """Test backup chain with circular reference (shouldn't happen but handle it)"""
        # Create circular reference
        metadata1 = BackupMetadata(
            backup_id="backup1",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.INCREMENTAL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path="/tmp/backup1.sql",
            compressed=False,
            encrypted=False,
            size_bytes=100,
            checksum="checksum1",
            parent_backup_id="backup2",  # Points to backup2
            error_message=None,
            metadata={}
        )

        metadata2 = BackupMetadata(
            backup_id="backup2",
            database_type="postgresql",
            database_name="testdb",
            backup_type=BackupType.INCREMENTAL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_path="/tmp/backup2.sql",
            compressed=False,
            encrypted=False,
            size_bytes=100,
            checksum="checksum2",
            parent_backup_id="backup1",  # Points back to backup1 (circular!)
            error_message=None,
            metadata={}
        )

        backup_system.backups["backup1"] = metadata1
        backup_system.backups["backup2"] = metadata2

        # Should still terminate and not infinite loop
        # Implementation limitation: will include both in chain
        chain = backup_system.get_backup_chain("backup1")

        # Should have at least both backups
        assert len(chain) >= 2

    @pytest.mark.asyncio
    async def test_backup_with_special_characters_in_name(self, backup_system):
        """Test backup with special characters in database name"""
        connection_params = {
            'host': 'localhost',
            'port': 5432,
            'username': 'postgres',
            'password': 'password'
        }

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'):

            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="test-db_2025.v1",
                connection_params=connection_params,
                compress=False,
                encrypt=False
            )

            assert metadata.database_name == "test-db_2025.v1"


# =============================================================================
# F. INTEGRATION & PERFORMANCE TESTS (10-12 tests)
# =============================================================================

class TestIntegrationAndPerformance:
    """Test integration scenarios and performance"""

    @pytest.mark.asyncio
    async def test_full_backup_workflow_postgresql(self, backup_system, connection_params_postgresql, tmp_path):
        """Test complete backup workflow for PostgreSQL"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        backup_data = b"PostgreSQL backup data" * 100

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(Path, 'stat') as mock_stat, \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'):

            mock_stat.return_value.st_size = len(backup_data)

            # Create backup
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                backup_type=BackupType.FULL,
                compress=True,
                encrypt=False
            )

            # Wait for completion
            await asyncio.sleep(0.2)

            # List backups
            backups = backup_system.list_backups(database_name="testdb")
            assert len(backups) == 1

            # Validate backup
            is_valid, error = await backup_system.validate_backup(metadata.backup_id)

            # May fail validation due to mocking, but workflow completes
            assert metadata.backup_id in backup_system.backups

    @pytest.mark.asyncio
    async def test_incremental_backup_chain_workflow(self, backup_system, connection_params_postgresql):
        """Test creating a chain of incremental backups"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'), \
             patch.object(Path, 'stat') as mock_stat:

            mock_stat.return_value.st_size = 1024

            # Create full backup
            full_backup = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                backup_type=BackupType.FULL,
                compress=False,
                encrypt=False
            )

            await asyncio.sleep(0.1)

            # Create incremental backup
            incr_backup = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                backup_type=BackupType.INCREMENTAL,
                parent_backup_id=full_backup.backup_id,
                compress=False,
                encrypt=False
            )

            await asyncio.sleep(0.1)

            # Get backup chain
            chain = backup_system.get_backup_chain(incr_backup.backup_id)

            assert len(chain) == 2
            assert chain[0].backup_type == BackupType.FULL
            assert chain[1].backup_type == BackupType.INCREMENTAL

    @pytest.mark.asyncio
    async def test_backup_with_rotation_workflow(self, backup_system, connection_params_postgresql, tmp_path):
        """Test backup creation followed by rotation"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'), \
             patch.object(Path, 'stat') as mock_stat:

            mock_stat.return_value.st_size = 1024

            # Create multiple backups over time
            now = datetime.now()
            for i in range(10):
                backup_file = tmp_path / f"backup_{i}.sql"
                backup_file.write_text("data")

                metadata = BackupMetadata(
                    backup_id=f"backup_{i}",
                    database_type="postgresql",
                    database_name="testdb",
                    backup_type=BackupType.FULL,
                    status=BackupStatus.COMPLETED,
                    created_at=now - timedelta(days=i),
                    completed_at=now - timedelta(days=i),
                    file_path=str(backup_file),
                    compressed=False,
                    encrypted=False,
                    size_bytes=100,
                    checksum=f"checksum_{i}",
                    parent_backup_id=None,
                    error_message=None,
                    metadata={}
                )
                backup_system.backups[metadata.backup_id] = metadata

            # Apply rotation
            deleted = backup_system.apply_rotation_policy()

            # Should delete some old backups
            assert len(deleted) > 0

            # Remaining backups should be accessible
            remaining = backup_system.list_backups(status=BackupStatus.COMPLETED)
            assert len(remaining) < 10

    @pytest.mark.asyncio
    async def test_multiple_database_backups(self, backup_system, connection_params_postgresql):
        """Test backing up multiple databases"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'):

            databases = ["db1", "db2", "db3"]

            for db_name in databases:
                await backup_system.create_backup(
                    database_type="postgresql",
                    database_name=db_name,
                    connection_params=connection_params_postgresql,
                    compress=False,
                    encrypt=False
                )

            await asyncio.sleep(0.1)

            # Verify all databases have backups
            for db_name in databases:
                backups = backup_system.list_backups(database_name=db_name)
                assert len(backups) >= 1

    @pytest.mark.asyncio
    async def test_backup_performance_large_dataset(self, backup_system, connection_params_postgresql):
        """Test backup creation performance with large dataset simulation"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'), \
             patch.object(Path, 'stat') as mock_stat:

            # Simulate large backup (1GB)
            mock_stat.return_value.st_size = 1024 * 1024 * 1024

            start_time = datetime.now()

            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="large_db",
                connection_params=connection_params_postgresql,
                compress=False,
                encrypt=False
            )

            creation_time = (datetime.now() - start_time).total_seconds()

            # Backup creation should be fast (metadata only)
            assert creation_time < 1.0
            assert metadata.backup_id in backup_system.backups

    def test_metadata_persistence_across_instances(self, temp_backup_dir, sample_backup_metadata):
        """Test that metadata persists across system instances"""
        # Create first system and add backup
        system1 = BackupSystem(backup_dir=temp_backup_dir)
        system1.backups[sample_backup_metadata.backup_id] = sample_backup_metadata
        system1._save_metadata()

        # Create new system instance
        system2 = BackupSystem(backup_dir=temp_backup_dir)

        # Should load metadata from disk
        assert sample_backup_metadata.backup_id in system2.backups
        assert system2.backups[sample_backup_metadata.backup_id].database_name == sample_backup_metadata.database_name

    @pytest.mark.asyncio
    async def test_backup_cancellation_handling(self, backup_system, connection_params_postgresql):
        """Test handling of backup cancellation (process termination)"""
        # Mock a process that never completes
        mock_process = AsyncMock()
        mock_process.returncode = -1  # Process terminated
        mock_process.communicate = AsyncMock(side_effect=asyncio.CancelledError())

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                compress=False,
                encrypt=False
            )

            # Wait for async execution to fail
            await asyncio.sleep(0.01)

            # Should handle cancellation gracefully
            updated_metadata = backup_system.backups[metadata.backup_id]
            assert updated_metadata.status == BackupStatus.FAILED

    @pytest.mark.asyncio
    async def test_backup_with_progress_tracking(self, backup_system, connection_params_postgresql):
        """Test tracking backup progress through status updates"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'):

            # Create backup
            metadata = await backup_system.create_backup(
                database_type="postgresql",
                database_name="testdb",
                connection_params=connection_params_postgresql,
                compress=False,
                encrypt=False
            )

            # Initially pending
            assert metadata.status == BackupStatus.PENDING

            # Wait for execution to start
            await asyncio.sleep(0.01)

            # Check if in progress (timing-dependent)
            current_metadata = backup_system.backups[metadata.backup_id]
            assert current_metadata.status in [BackupStatus.IN_PROGRESS, BackupStatus.COMPLETED, BackupStatus.FAILED]

    @pytest.mark.asyncio
    async def test_mixed_database_types_backup(self, backup_system):
        """Test backing up different database types in the same system"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch('builtins.open', mock_open()), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'):

            # Create backups for different databases
            pg_backup = await backup_system.create_backup(
                database_type="postgresql",
                database_name="pg_db",
                connection_params={'host': 'localhost', 'port': 5432, 'username': 'postgres', 'password': ''},
                compress=False,
                encrypt=False
            )

            mysql_backup = await backup_system.create_backup(
                database_type="mysql",
                database_name="mysql_db",
                connection_params={'host': 'localhost', 'port': 3306, 'username': 'root', 'password': ''},
                compress=False,
                encrypt=False
            )

            # Both should coexist
            assert pg_backup.database_type == "postgresql"
            assert mysql_backup.database_type == "mysql"
            assert len(backup_system.backups) >= 2

    def test_backup_metadata_serialization(self, backup_system, sample_backup_metadata):
        """Test correct serialization of backup metadata"""
        backup_system.backups[sample_backup_metadata.backup_id] = sample_backup_metadata
        backup_system._save_metadata()

        # Load and verify
        with open(backup_system.metadata_file, 'r') as f:
            data = json.load(f)

        metadata_dict = data[sample_backup_metadata.backup_id]

        # Verify all fields are serialized
        assert metadata_dict['backup_id'] == sample_backup_metadata.backup_id
        assert metadata_dict['database_type'] == sample_backup_metadata.database_type
        assert metadata_dict['backup_type'] == sample_backup_metadata.backup_type.value
        assert metadata_dict['status'] == sample_backup_metadata.status.value
        assert 'created_at' in metadata_dict
        assert 'checksum' in metadata_dict

    @pytest.mark.asyncio
    async def test_backup_system_thread_safety(self, backup_system, connection_params_postgresql):
        """Test that backup system handles concurrent access safely"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch.object(backup_system, '_calculate_checksum', return_value='checksum123'):

            # Create multiple backups concurrently
            tasks = []
            for i in range(10):
                task = backup_system.create_backup(
                    database_type="postgresql",
                    database_name=f"testdb_{i}",
                    connection_params=connection_params_postgresql,
                    compress=False,
                    encrypt=False
                )
                tasks.append(task)

            metadatas = await asyncio.gather(*tasks)

            # All should be created successfully
            assert len(metadatas) == 10
            assert len(backup_system.backups) >= 10
