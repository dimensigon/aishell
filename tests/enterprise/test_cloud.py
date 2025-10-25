"""Tests for cloud integration"""

import pytest
import tempfile
import os

from src.enterprise.cloud.aws_integration import AWSIntegration, AWSConfig
from src.enterprise.cloud.azure_integration import AzureIntegration, AzureConfig
from src.enterprise.cloud.gcp_integration import GCPIntegration, GCPConfig
from src.enterprise.cloud.cloud_backup import CloudBackupManager, BackupConfig, CloudProvider


class TestAWSIntegration:
    """Test AWS integration"""

    @pytest.fixture
    def aws(self):
        config = AWSConfig(region="us-east-1")
        return AWSIntegration(config)

    def test_get_rds_connection_string(self, aws):
        """Test RDS connection string generation"""
        conn_str = aws.get_rds_connection_string(
            "my-instance",
            "mydb",
        )

        assert "my-instance" in conn_str
        assert "rds.amazonaws.com" in conn_str
        assert "mydb" in conn_str

    def test_store_secret(self, aws):
        """Test secret storage (mocked)"""
        success = aws.store_secret(
            "test-secret",
            "secret-value",
        )

        assert success

    def test_upload_to_s3(self, aws):
        """Test S3 upload (mocked)"""
        success = aws.upload_to_s3(
            bucket="test-bucket",
            key="test-key",
            data=b"test data",
        )

        assert success


class TestAzureIntegration:
    """Test Azure integration"""

    @pytest.fixture
    def azure(self):
        config = AzureConfig()
        return AzureIntegration(config)

    def test_get_sql_connection_string(self, azure):
        """Test Azure SQL connection string"""
        conn_str = azure.get_sql_connection_string(
            "my-server",
            "mydb",
        )

        assert "my-server" in conn_str
        assert "mydb" in conn_str

    def test_store_secret(self, azure):
        """Test Key Vault secret storage (mocked)"""
        success = azure.store_secret(
            "my-vault",
            "test-secret",
            "secret-value",
        )

        assert success


class TestGCPIntegration:
    """Test GCP integration"""

    @pytest.fixture
    def gcp(self):
        config = GCPConfig(project_id="my-project")
        return GCPIntegration(config)

    def test_get_cloudsql_connection_string(self, gcp):
        """Test Cloud SQL connection string"""
        conn_str = gcp.get_cloudsql_connection_string(
            "my-instance",
            "mydb",
        )

        assert "my-project" in conn_str
        assert "my-instance" in conn_str

    def test_store_secret(self, gcp):
        """Test Secret Manager storage (mocked)"""
        success = gcp.store_secret(
            "test-secret",
            "secret-value",
        )

        assert success


class TestCloudBackup:
    """Test cloud backup manager"""

    @pytest.fixture
    def backup_manager(self):
        config = BackupConfig(
            provider=CloudProvider.LOCAL,
            schedule="0 2 * * *",  # 2 AM daily
            retention_days=30,
        )
        return CloudBackupManager(config)

    def test_create_backup(self, backup_manager):
        """Test backup creation"""
        # Create temp database file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test database content")
            db_path = f.name

        try:
            backup_id = backup_manager.create_backup(
                tenant_id="tenant_1",
                database_path=db_path,
            )

            assert backup_id is not None
            assert "tenant_1" in backup_id
        finally:
            os.unlink(db_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
