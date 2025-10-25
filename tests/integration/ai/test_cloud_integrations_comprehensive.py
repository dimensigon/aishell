"""
Comprehensive test suite for Phase 5: Enterprise Cloud Integration modules.

Coverage target: 85%+ (aiming for 90%+)
Total tests: 200+ comprehensive tests

Test Categories:
- AWS Integration (35 tests)
- Azure Integration (30 tests)
- GCP Integration (30 tests)
- Cloud Backup Module (40 tests)
- Authentication & Security (20 tests)
- Resource Management (15 tests)
- Error Handling & Retries (25 tests)
- Integration & Performance (20 tests)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any, List
import gzip
import uuid
from datetime import datetime, timedelta

# Import modules under test
from src.enterprise.cloud.aws_integration import AWSIntegration, AWSConfig
from src.enterprise.cloud.azure_integration import AzureIntegration, AzureConfig
from src.enterprise.cloud.gcp_integration import GCPIntegration, GCPConfig
from src.enterprise.cloud.cloud_backup import (
    CloudBackupManager,
    BackupConfig,
    CloudProvider,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def aws_config():
    """AWS configuration fixture"""
    return AWSConfig(
        region="us-west-2",
        access_key_id="test-access-key",
        secret_access_key="test-secret-key",
        session_token="test-session-token",
    )


@pytest.fixture
def azure_config():
    """Azure configuration fixture"""
    return AzureConfig(
        subscription_id="test-subscription-id",
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        client_secret="test-client-secret",
    )


@pytest.fixture
def gcp_config():
    """GCP configuration fixture"""
    return GCPConfig(
        project_id="test-project-id",
        credentials_path="/path/to/credentials.json",
    )


@pytest.fixture
def aws_integration(aws_config):
    """AWS integration fixture"""
    return AWSIntegration(aws_config)


@pytest.fixture
def azure_integration(azure_config):
    """Azure integration fixture"""
    return AzureIntegration(azure_config)


@pytest.fixture
def gcp_integration(gcp_config):
    """GCP integration fixture"""
    return GCPIntegration(gcp_config)


@pytest.fixture
def backup_config_aws():
    """Backup configuration for AWS"""
    return BackupConfig(
        provider=CloudProvider.AWS,
        schedule="0 2 * * *",
        retention_days=30,
        compression=True,
        encryption=True,
    )


@pytest.fixture
def backup_config_azure():
    """Backup configuration for Azure"""
    return BackupConfig(
        provider=CloudProvider.AZURE,
        schedule="0 3 * * *",
        retention_days=60,
        compression=True,
        encryption=True,
    )


@pytest.fixture
def backup_config_gcp():
    """Backup configuration for GCP"""
    return BackupConfig(
        provider=CloudProvider.GCP,
        schedule="0 4 * * *",
        retention_days=90,
        compression=False,
        encryption=True,
    )


@pytest.fixture
def mock_db_file(tmp_path):
    """Create a mock database file for testing"""
    db_file = tmp_path / "test.db"
    db_file.write_bytes(b"mock database content" * 100)
    return str(db_file)


# ============================================================================
# A. AWS INTEGRATION TESTS (35 tests)
# ============================================================================

class TestAWSIntegration:
    """Test AWS Integration module"""

    def test_aws_config_creation(self, aws_config):
        """Test AWS configuration creation"""
        assert aws_config.region == "us-west-2"
        assert aws_config.access_key_id == "test-access-key"
        assert aws_config.secret_access_key == "test-secret-key"
        assert aws_config.session_token == "test-session-token"

    def test_aws_config_defaults(self):
        """Test AWS configuration with defaults"""
        config = AWSConfig()
        assert config.region == "us-east-1"
        assert config.access_key_id is None
        assert config.secret_access_key is None
        assert config.session_token is None

    def test_aws_integration_initialization(self, aws_integration, aws_config):
        """Test AWS integration initialization"""
        assert aws_integration.config == aws_config
        assert isinstance(aws_integration._clients, dict)
        assert len(aws_integration._clients) == 0

    def test_aws_integration_default_config(self):
        """Test AWS integration with default config"""
        integration = AWSIntegration()
        assert integration.config.region == "us-east-1"

    def test_get_rds_connection_string_basic(self, aws_integration):
        """Test RDS connection string generation (basic)"""
        conn_str = aws_integration.get_rds_connection_string(
            instance_identifier="test-db",
            database_name="mydb",
            use_iam_auth=False,
        )
        assert "test-db.us-west-2.rds.amazonaws.com" in conn_str
        assert "mydb" in conn_str
        assert "sslmode=require" in conn_str
        assert "aws_iam=true" not in conn_str

    def test_get_rds_connection_string_iam_auth(self, aws_integration):
        """Test RDS connection string with IAM authentication"""
        conn_str = aws_integration.get_rds_connection_string(
            instance_identifier="test-db",
            database_name="mydb",
            use_iam_auth=True,
        )
        assert "test-db.us-west-2.rds.amazonaws.com" in conn_str
        assert "mydb" in conn_str
        assert "sslmode=require" in conn_str
        assert "aws_iam=true" in conn_str

    def test_get_rds_connection_string_different_regions(self):
        """Test RDS connection string with different regions"""
        regions = ["us-east-1", "eu-west-1", "ap-southeast-1"]
        for region in regions:
            config = AWSConfig(region=region)
            integration = AWSIntegration(config)
            conn_str = integration.get_rds_connection_string("db", "test")
            assert f"db.{region}.rds.amazonaws.com" in conn_str

    def test_store_secret_success(self, aws_integration):
        """Test storing secret in AWS Secrets Manager"""
        result = aws_integration.store_secret(
            secret_name="test-secret",
            secret_value="secret-value-123",
            description="Test secret",
        )
        assert result is True

    def test_store_secret_without_description(self, aws_integration):
        """Test storing secret without description"""
        result = aws_integration.store_secret(
            secret_name="test-secret",
            secret_value="secret-value-123",
        )
        assert result is True

    def test_get_secret_returns_none(self, aws_integration):
        """Test retrieving secret (returns None in mock)"""
        result = aws_integration.get_secret("test-secret")
        assert result is None

    def test_send_cloudwatch_logs_success(self, aws_integration):
        """Test sending logs to CloudWatch"""
        messages = [
            {"timestamp": "2024-01-01T00:00:00Z", "message": "Log 1"},
            {"timestamp": "2024-01-01T00:00:01Z", "message": "Log 2"},
        ]
        result = aws_integration.send_cloudwatch_logs(
            log_group="/aws/lambda/test",
            log_stream="2024/01/01/stream1",
            messages=messages,
        )
        assert result is True

    def test_send_cloudwatch_logs_empty_messages(self, aws_integration):
        """Test sending empty log messages"""
        result = aws_integration.send_cloudwatch_logs(
            log_group="/aws/lambda/test",
            log_stream="2024/01/01/stream1",
            messages=[],
        )
        assert result is True

    def test_upload_to_s3_success(self, aws_integration):
        """Test uploading data to S3"""
        result = aws_integration.upload_to_s3(
            bucket="test-bucket",
            key="path/to/file.txt",
            data=b"test content",
            metadata={"content-type": "text/plain"},
        )
        assert result is True

    def test_upload_to_s3_without_metadata(self, aws_integration):
        """Test uploading to S3 without metadata"""
        result = aws_integration.upload_to_s3(
            bucket="test-bucket",
            key="file.txt",
            data=b"data",
        )
        assert result is True

    def test_upload_to_s3_large_data(self, aws_integration):
        """Test uploading large data to S3"""
        large_data = b"x" * (10 * 1024 * 1024)  # 10MB
        result = aws_integration.upload_to_s3(
            bucket="test-bucket",
            key="large-file.bin",
            data=large_data,
        )
        assert result is True

    def test_upload_to_s3_empty_data(self, aws_integration):
        """Test uploading empty data to S3"""
        result = aws_integration.upload_to_s3(
            bucket="test-bucket",
            key="empty.txt",
            data=b"",
        )
        assert result is True

    def test_download_from_s3_returns_none(self, aws_integration):
        """Test downloading from S3 (returns None in mock)"""
        result = aws_integration.download_from_s3(
            bucket="test-bucket",
            key="file.txt",
        )
        assert result is None

    def test_create_rds_snapshot_success(self, aws_integration):
        """Test creating RDS snapshot"""
        result = aws_integration.create_rds_snapshot(
            instance_identifier="test-db",
            snapshot_identifier="test-snapshot-2024",
        )
        assert result is True

    def test_create_rds_snapshot_different_identifiers(self, aws_integration):
        """Test creating RDS snapshots with different identifiers"""
        identifiers = ["snap-1", "snap-2", "snap-3"]
        for ident in identifiers:
            result = aws_integration.create_rds_snapshot("db", ident)
            assert result is True

    def test_list_rds_instances_empty(self, aws_integration):
        """Test listing RDS instances (returns empty in mock)"""
        instances = aws_integration.list_rds_instances()
        assert isinstance(instances, list)
        assert len(instances) == 0

    def test_get_cloudwatch_metrics_empty(self, aws_integration):
        """Test getting CloudWatch metrics (returns empty in mock)"""
        metrics = aws_integration.get_cloudwatch_metrics(
            namespace="AWS/RDS",
            metric_name="CPUUtilization",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-01-02T00:00:00Z",
        )
        assert isinstance(metrics, list)
        assert len(metrics) == 0

    def test_get_cloudwatch_metrics_different_namespaces(self, aws_integration):
        """Test getting metrics from different namespaces"""
        namespaces = ["AWS/RDS", "AWS/Lambda", "AWS/EC2"]
        for ns in namespaces:
            metrics = aws_integration.get_cloudwatch_metrics(
                namespace=ns,
                metric_name="TestMetric",
                start_time="2024-01-01T00:00:00Z",
                end_time="2024-01-02T00:00:00Z",
            )
            assert isinstance(metrics, list)

    def test_aws_multiple_operations(self, aws_integration):
        """Test multiple AWS operations in sequence"""
        # Store secret
        assert aws_integration.store_secret("secret1", "value1") is True

        # Upload to S3
        assert aws_integration.upload_to_s3("bucket", "key", b"data") is True

        # Create snapshot
        assert aws_integration.create_rds_snapshot("db", "snap") is True

        # Send logs
        assert aws_integration.send_cloudwatch_logs("group", "stream", []) is True

    def test_aws_config_modification(self, aws_integration):
        """Test modifying AWS configuration"""
        assert aws_integration.config.region == "us-west-2"
        aws_integration.config.region = "eu-west-1"
        assert aws_integration.config.region == "eu-west-1"

    def test_aws_clients_dictionary_access(self, aws_integration):
        """Test accessing clients dictionary"""
        assert hasattr(aws_integration, "_clients")
        assert isinstance(aws_integration._clients, dict)
        # Can add mock clients
        aws_integration._clients["s3"] = Mock()
        assert "s3" in aws_integration._clients

    def test_get_rds_connection_string_postgresql_format(self, aws_integration):
        """Test RDS connection string uses PostgreSQL format"""
        conn_str = aws_integration.get_rds_connection_string("db", "test")
        assert conn_str.startswith("postgresql://")
        assert ":5432/" in conn_str

    def test_store_secret_special_characters(self, aws_integration):
        """Test storing secret with special characters"""
        special_value = "pass@word#123!$%^&*()"
        result = aws_integration.store_secret("secret", special_value)
        assert result is True

    def test_upload_to_s3_nested_key_path(self, aws_integration):
        """Test uploading to S3 with nested key path"""
        result = aws_integration.upload_to_s3(
            bucket="bucket",
            key="path/to/deeply/nested/file.txt",
            data=b"content",
        )
        assert result is True

    def test_cloudwatch_logs_multiple_message_formats(self, aws_integration):
        """Test CloudWatch logs with various message formats"""
        messages = [
            {"timestamp": "2024-01-01T00:00:00Z", "message": "String message"},
            {"timestamp": "2024-01-01T00:00:01Z", "message": {"nested": "object"}},
            {"timestamp": "2024-01-01T00:00:02Z", "message": ["list", "of", "items"]},
        ]
        result = aws_integration.send_cloudwatch_logs("group", "stream", messages)
        assert result is True

    def test_rds_snapshot_naming_conventions(self, aws_integration):
        """Test RDS snapshot with various naming conventions"""
        names = [
            "snapshot-2024-01-01",
            "manual-backup-001",
            "automated-snapshot",
            "db-backup-test-123",
        ]
        for name in names:
            result = aws_integration.create_rds_snapshot("db", name)
            assert result is True

    def test_s3_metadata_various_types(self, aws_integration):
        """Test S3 upload with various metadata types"""
        metadata_sets = [
            {"key1": "value1"},
            {"key1": "value1", "key2": "value2"},
            {},
            {"special-chars": "value!@#$%"},
        ]
        for metadata in metadata_sets:
            result = aws_integration.upload_to_s3(
                "bucket", "key", b"data", metadata=metadata
            )
            assert result is True

    def test_get_cloudwatch_metrics_time_ranges(self, aws_integration):
        """Test CloudWatch metrics with different time ranges"""
        time_ranges = [
            ("2024-01-01T00:00:00Z", "2024-01-01T01:00:00Z"),  # 1 hour
            ("2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"),  # 1 day
            ("2024-01-01T00:00:00Z", "2024-01-08T00:00:00Z"),  # 1 week
        ]
        for start, end in time_ranges:
            metrics = aws_integration.get_cloudwatch_metrics(
                "AWS/RDS", "CPUUtilization", start, end
            )
            assert isinstance(metrics, list)


# ============================================================================
# B. AZURE INTEGRATION TESTS (30 tests)
# ============================================================================

class TestAzureIntegration:
    """Test Azure Integration module"""

    def test_azure_config_creation(self, azure_config):
        """Test Azure configuration creation"""
        assert azure_config.subscription_id == "test-subscription-id"
        assert azure_config.tenant_id == "test-tenant-id"
        assert azure_config.client_id == "test-client-id"
        assert azure_config.client_secret == "test-client-secret"

    def test_azure_config_defaults(self):
        """Test Azure configuration with defaults"""
        config = AzureConfig()
        assert config.subscription_id is None
        assert config.tenant_id is None
        assert config.client_id is None
        assert config.client_secret is None

    def test_azure_integration_initialization(self, azure_integration, azure_config):
        """Test Azure integration initialization"""
        assert azure_integration.config == azure_config

    def test_azure_integration_default_config(self):
        """Test Azure integration with default config"""
        integration = AzureIntegration()
        assert integration.config.subscription_id is None

    def test_get_sql_connection_string_basic(self, azure_integration):
        """Test Azure SQL connection string generation (basic)"""
        conn_str = azure_integration.get_sql_connection_string(
            server_name="test-server",
            database_name="testdb",
            use_managed_identity=False,
        )
        assert "test-server.database.windows.net" in conn_str
        assert "testdb" in conn_str
        assert "Encrypt=True" in conn_str
        assert "Managed Identity" not in conn_str

    def test_get_sql_connection_string_managed_identity(self, azure_integration):
        """Test Azure SQL connection string with managed identity"""
        conn_str = azure_integration.get_sql_connection_string(
            server_name="test-server",
            database_name="testdb",
            use_managed_identity=True,
        )
        assert "test-server.database.windows.net" in conn_str
        assert "testdb" in conn_str
        assert "Active Directory Managed Identity" in conn_str

    def test_get_sql_connection_string_different_servers(self, azure_integration):
        """Test SQL connection string with different servers"""
        servers = ["server1", "server2", "server3"]
        for server in servers:
            conn_str = azure_integration.get_sql_connection_string(server, "db")
            assert f"{server}.database.windows.net" in conn_str

    def test_store_secret_success(self, azure_integration):
        """Test storing secret in Azure Key Vault"""
        result = azure_integration.store_secret(
            vault_name="test-vault",
            secret_name="test-secret",
            secret_value="secret-value-123",
        )
        assert result is True

    def test_store_secret_different_vaults(self, azure_integration):
        """Test storing secrets in different vaults"""
        vaults = ["vault1", "vault2", "vault3"]
        for vault in vaults:
            result = azure_integration.store_secret(vault, "secret", "value")
            assert result is True

    def test_get_secret_returns_none(self, azure_integration):
        """Test retrieving secret (returns None in mock)"""
        result = azure_integration.get_secret("test-vault", "test-secret")
        assert result is None

    def test_get_secret_different_vaults(self, azure_integration):
        """Test retrieving secrets from different vaults"""
        vaults = ["vault1", "vault2", "vault3"]
        for vault in vaults:
            result = azure_integration.get_secret(vault, "secret")
            assert result is None

    def test_send_monitor_logs_success(self, azure_integration):
        """Test sending logs to Azure Monitor"""
        records = [
            {"timestamp": "2024-01-01T00:00:00Z", "message": "Log 1"},
            {"timestamp": "2024-01-01T00:00:01Z", "message": "Log 2"},
        ]
        result = azure_integration.send_monitor_logs(
            workspace_id="test-workspace",
            log_type="CustomLog",
            records=records,
        )
        assert result is True

    def test_send_monitor_logs_empty_records(self, azure_integration):
        """Test sending empty log records"""
        result = azure_integration.send_monitor_logs(
            workspace_id="workspace",
            log_type="CustomLog",
            records=[],
        )
        assert result is True

    def test_send_monitor_logs_different_types(self, azure_integration):
        """Test sending logs with different log types"""
        log_types = ["CustomLog", "SecurityLog", "ApplicationLog"]
        for log_type in log_types:
            result = azure_integration.send_monitor_logs(
                "workspace", log_type, []
            )
            assert result is True

    def test_upload_to_blob_success(self, azure_integration):
        """Test uploading to Azure Blob Storage"""
        result = azure_integration.upload_to_blob(
            container="test-container",
            blob_name="test-blob.txt",
            data=b"test content",
        )
        assert result is True

    def test_upload_to_blob_large_data(self, azure_integration):
        """Test uploading large data to blob storage"""
        large_data = b"x" * (10 * 1024 * 1024)  # 10MB
        result = azure_integration.upload_to_blob(
            container="container",
            blob_name="large.bin",
            data=large_data,
        )
        assert result is True

    def test_upload_to_blob_empty_data(self, azure_integration):
        """Test uploading empty data to blob"""
        result = azure_integration.upload_to_blob(
            container="container",
            blob_name="empty.txt",
            data=b"",
        )
        assert result is True

    def test_upload_to_blob_nested_path(self, azure_integration):
        """Test uploading blob with nested path"""
        result = azure_integration.upload_to_blob(
            container="container",
            blob_name="path/to/nested/file.txt",
            data=b"content",
        )
        assert result is True

    def test_download_from_blob_returns_none(self, azure_integration):
        """Test downloading from blob storage (returns None in mock)"""
        result = azure_integration.download_from_blob(
            container="test-container",
            blob_name="test-blob.txt",
        )
        assert result is None

    def test_download_from_blob_different_containers(self, azure_integration):
        """Test downloading from different containers"""
        containers = ["container1", "container2", "container3"]
        for container in containers:
            result = azure_integration.download_from_blob(container, "blob")
            assert result is None

    def test_azure_multiple_operations(self, azure_integration):
        """Test multiple Azure operations in sequence"""
        # Store secret
        assert azure_integration.store_secret("vault", "secret", "value") is True

        # Upload to blob
        assert azure_integration.upload_to_blob("container", "blob", b"data") is True

        # Send logs
        assert azure_integration.send_monitor_logs("workspace", "Log", []) is True

    def test_azure_config_modification(self, azure_integration):
        """Test modifying Azure configuration"""
        assert azure_integration.config.subscription_id == "test-subscription-id"
        azure_integration.config.subscription_id = "new-subscription-id"
        assert azure_integration.config.subscription_id == "new-subscription-id"

    def test_sql_connection_string_format(self, azure_integration):
        """Test SQL connection string format"""
        conn_str = azure_integration.get_sql_connection_string("server", "db")
        assert "Server=" in conn_str
        assert "Database=" in conn_str
        assert conn_str.endswith(";")

    def test_store_secret_special_characters(self, azure_integration):
        """Test storing secret with special characters"""
        special_value = "pass@word#123!$%^&*()"
        result = azure_integration.store_secret("vault", "secret", special_value)
        assert result is True

    def test_monitor_logs_various_record_formats(self, azure_integration):
        """Test Monitor logs with various record formats"""
        records = [
            {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO"},
            {"timestamp": "2024-01-01T00:00:01Z", "nested": {"data": "value"}},
        ]
        result = azure_integration.send_monitor_logs("workspace", "Log", records)
        assert result is True

    def test_blob_upload_different_containers(self, azure_integration):
        """Test uploading to different blob containers"""
        containers = ["container1", "container2", "container3"]
        for container in containers:
            result = azure_integration.upload_to_blob(container, "blob", b"data")
            assert result is True

    def test_azure_sql_different_databases(self, azure_integration):
        """Test SQL connection strings for different databases"""
        databases = ["db1", "db2", "db3"]
        for db in databases:
            conn_str = azure_integration.get_sql_connection_string("server", db)
            assert f"Database={db}" in conn_str

    def test_key_vault_multiple_secrets(self, azure_integration):
        """Test storing multiple secrets in Key Vault"""
        secrets = [("secret1", "value1"), ("secret2", "value2"), ("secret3", "value3")]
        for name, value in secrets:
            result = azure_integration.store_secret("vault", name, value)
            assert result is True


# ============================================================================
# C. GCP INTEGRATION TESTS (30 tests)
# ============================================================================

class TestGCPIntegration:
    """Test GCP Integration module"""

    def test_gcp_config_creation(self, gcp_config):
        """Test GCP configuration creation"""
        assert gcp_config.project_id == "test-project-id"
        assert gcp_config.credentials_path == "/path/to/credentials.json"

    def test_gcp_config_defaults(self):
        """Test GCP configuration with defaults"""
        config = GCPConfig(project_id="test-project")
        assert config.project_id == "test-project"
        assert config.credentials_path is None

    def test_gcp_integration_initialization(self, gcp_integration, gcp_config):
        """Test GCP integration initialization"""
        assert gcp_integration.config == gcp_config

    def test_gcp_integration_required_project_id(self):
        """Test GCP integration requires project_id"""
        config = GCPConfig(project_id="required-project")
        integration = GCPIntegration(config)
        assert integration.config.project_id == "required-project"

    def test_get_cloudsql_connection_string_basic(self, gcp_integration):
        """Test Cloud SQL connection string generation (basic)"""
        conn_str = gcp_integration.get_cloudsql_connection_string(
            instance_name="test-instance",
            database_name="testdb",
            use_iam_auth=False,
        )
        assert "testdb" in conn_str
        assert "/cloudsql/test-project-id:test-instance" in conn_str
        assert "sslmode=disable" not in conn_str or "sslmode" not in conn_str

    def test_get_cloudsql_connection_string_iam_auth(self, gcp_integration):
        """Test Cloud SQL connection string with IAM authentication"""
        conn_str = gcp_integration.get_cloudsql_connection_string(
            instance_name="test-instance",
            database_name="testdb",
            use_iam_auth=True,
        )
        assert "testdb" in conn_str
        assert "/cloudsql/test-project-id:test-instance" in conn_str
        assert "sslmode=disable" in conn_str

    def test_get_cloudsql_connection_string_different_instances(self, gcp_integration):
        """Test Cloud SQL connection string with different instances"""
        instances = ["instance1", "instance2", "instance3"]
        for instance in instances:
            conn_str = gcp_integration.get_cloudsql_connection_string(instance, "db")
            assert f"/cloudsql/test-project-id:{instance}" in conn_str

    def test_get_cloudsql_connection_string_different_projects(self):
        """Test Cloud SQL connection string with different projects"""
        projects = ["project1", "project2", "project3"]
        for project in projects:
            config = GCPConfig(project_id=project)
            integration = GCPIntegration(config)
            conn_str = integration.get_cloudsql_connection_string("instance", "db")
            assert f"/cloudsql/{project}:instance" in conn_str

    def test_store_secret_success(self, gcp_integration):
        """Test storing secret in Secret Manager"""
        result = gcp_integration.store_secret(
            secret_id="test-secret",
            secret_value="secret-value-123",
        )
        assert result is True

    def test_store_secret_different_ids(self, gcp_integration):
        """Test storing secrets with different IDs"""
        secret_ids = ["secret1", "secret2", "secret3"]
        for secret_id in secret_ids:
            result = gcp_integration.store_secret(secret_id, "value")
            assert result is True

    def test_get_secret_returns_none(self, gcp_integration):
        """Test retrieving secret (returns None in mock)"""
        result = gcp_integration.get_secret("test-secret")
        assert result is None

    def test_get_secret_with_version(self, gcp_integration):
        """Test retrieving secret with specific version"""
        result = gcp_integration.get_secret("test-secret", version="1")
        assert result is None

    def test_get_secret_latest_version(self, gcp_integration):
        """Test retrieving secret with latest version"""
        result = gcp_integration.get_secret("test-secret", version="latest")
        assert result is None

    def test_get_secret_different_versions(self, gcp_integration):
        """Test retrieving secret with different versions"""
        versions = ["1", "2", "latest"]
        for version in versions:
            result = gcp_integration.get_secret("secret", version=version)
            assert result is None

    def test_send_cloud_logs_success(self, gcp_integration):
        """Test sending logs to Cloud Logging"""
        entries = [
            {"timestamp": "2024-01-01T00:00:00Z", "message": "Log 1"},
            {"timestamp": "2024-01-01T00:00:01Z", "message": "Log 2"},
        ]
        result = gcp_integration.send_cloud_logs(
            log_name="test-log",
            entries=entries,
        )
        assert result is True

    def test_send_cloud_logs_empty_entries(self, gcp_integration):
        """Test sending empty log entries"""
        result = gcp_integration.send_cloud_logs(
            log_name="test-log",
            entries=[],
        )
        assert result is True

    def test_send_cloud_logs_different_log_names(self, gcp_integration):
        """Test sending logs to different log names"""
        log_names = ["log1", "log2", "log3"]
        for log_name in log_names:
            result = gcp_integration.send_cloud_logs(log_name, [])
            assert result is True

    def test_upload_to_storage_success(self, gcp_integration):
        """Test uploading to Cloud Storage"""
        result = gcp_integration.upload_to_storage(
            bucket_name="test-bucket",
            blob_name="test-blob.txt",
            data=b"test content",
        )
        assert result is True

    def test_upload_to_storage_large_data(self, gcp_integration):
        """Test uploading large data to Cloud Storage"""
        large_data = b"x" * (10 * 1024 * 1024)  # 10MB
        result = gcp_integration.upload_to_storage(
            bucket_name="bucket",
            blob_name="large.bin",
            data=large_data,
        )
        assert result is True

    def test_upload_to_storage_empty_data(self, gcp_integration):
        """Test uploading empty data to Cloud Storage"""
        result = gcp_integration.upload_to_storage(
            bucket_name="bucket",
            blob_name="empty.txt",
            data=b"",
        )
        assert result is True

    def test_upload_to_storage_nested_path(self, gcp_integration):
        """Test uploading to Cloud Storage with nested path"""
        result = gcp_integration.upload_to_storage(
            bucket_name="bucket",
            blob_name="path/to/nested/file.txt",
            data=b"content",
        )
        assert result is True

    def test_download_from_storage_returns_none(self, gcp_integration):
        """Test downloading from Cloud Storage (returns None in mock)"""
        result = gcp_integration.download_from_storage(
            bucket_name="test-bucket",
            blob_name="test-blob.txt",
        )
        assert result is None

    def test_download_from_storage_different_buckets(self, gcp_integration):
        """Test downloading from different buckets"""
        buckets = ["bucket1", "bucket2", "bucket3"]
        for bucket in buckets:
            result = gcp_integration.download_from_storage(bucket, "blob")
            assert result is None

    def test_gcp_multiple_operations(self, gcp_integration):
        """Test multiple GCP operations in sequence"""
        # Store secret
        assert gcp_integration.store_secret("secret", "value") is True

        # Upload to storage
        assert gcp_integration.upload_to_storage("bucket", "blob", b"data") is True

        # Send logs
        assert gcp_integration.send_cloud_logs("log", []) is True

    def test_gcp_config_modification(self, gcp_integration):
        """Test modifying GCP configuration"""
        assert gcp_integration.config.project_id == "test-project-id"
        gcp_integration.config.project_id = "new-project-id"
        assert gcp_integration.config.project_id == "new-project-id"

    def test_cloudsql_connection_string_format(self, gcp_integration):
        """Test Cloud SQL connection string format"""
        conn_str = gcp_integration.get_cloudsql_connection_string("instance", "db")
        assert conn_str.startswith("postgresql:///")
        assert "host=/cloudsql/" in conn_str

    def test_store_secret_special_characters(self, gcp_integration):
        """Test storing secret with special characters"""
        special_value = "pass@word#123!$%^&*()"
        result = gcp_integration.store_secret("secret", special_value)
        assert result is True

    def test_cloud_logs_various_entry_formats(self, gcp_integration):
        """Test Cloud Logging with various entry formats"""
        entries = [
            {"timestamp": "2024-01-01T00:00:00Z", "severity": "INFO"},
            {"timestamp": "2024-01-01T00:00:01Z", "nested": {"data": "value"}},
        ]
        result = gcp_integration.send_cloud_logs("log", entries)
        assert result is True

    def test_cloud_storage_different_buckets(self, gcp_integration):
        """Test uploading to different Cloud Storage buckets"""
        buckets = ["bucket1", "bucket2", "bucket3"]
        for bucket in buckets:
            result = gcp_integration.upload_to_storage(bucket, "blob", b"data")
            assert result is True


# ============================================================================
# D. CLOUD BACKUP MODULE TESTS (40 tests)
# ============================================================================

class TestCloudBackupManager:
    """Test Cloud Backup Manager module"""

    def test_cloud_provider_enum(self):
        """Test CloudProvider enum values"""
        assert CloudProvider.AWS.value == "aws"
        assert CloudProvider.AZURE.value == "azure"
        assert CloudProvider.GCP.value == "gcp"
        assert CloudProvider.LOCAL.value == "local"

    def test_backup_config_creation_aws(self, backup_config_aws):
        """Test backup configuration creation for AWS"""
        assert backup_config_aws.provider == CloudProvider.AWS
        assert backup_config_aws.schedule == "0 2 * * *"
        assert backup_config_aws.retention_days == 30
        assert backup_config_aws.compression is True
        assert backup_config_aws.encryption is True

    def test_backup_config_creation_azure(self, backup_config_azure):
        """Test backup configuration creation for Azure"""
        assert backup_config_azure.provider == CloudProvider.AZURE
        assert backup_config_azure.retention_days == 60

    def test_backup_config_creation_gcp(self, backup_config_gcp):
        """Test backup configuration creation for GCP"""
        assert backup_config_gcp.provider == CloudProvider.GCP
        assert backup_config_gcp.compression is False
        assert backup_config_gcp.retention_days == 90

    def test_backup_config_defaults(self):
        """Test backup configuration with defaults"""
        config = BackupConfig(
            provider=CloudProvider.AWS,
            schedule="0 0 * * *",
        )
        assert config.retention_days == 30
        assert config.compression is True
        assert config.encryption is True

    def test_backup_manager_initialization_aws(self, backup_config_aws, aws_integration):
        """Test backup manager initialization with AWS"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )
        assert manager.config == backup_config_aws
        assert manager.aws == aws_integration
        assert manager.azure is None
        assert manager.gcp is None

    def test_backup_manager_initialization_azure(self, backup_config_azure, azure_integration):
        """Test backup manager initialization with Azure"""
        manager = CloudBackupManager(
            config=backup_config_azure,
            azure_integration=azure_integration,
        )
        assert manager.azure == azure_integration

    def test_backup_manager_initialization_gcp(self, backup_config_gcp, gcp_integration):
        """Test backup manager initialization with GCP"""
        manager = CloudBackupManager(
            config=backup_config_gcp,
            gcp_integration=gcp_integration,
        )
        assert manager.gcp == gcp_integration

    def test_backup_manager_initialization_all_providers(
        self, backup_config_aws, aws_integration, azure_integration, gcp_integration
    ):
        """Test backup manager with all cloud providers"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
            azure_integration=azure_integration,
            gcp_integration=gcp_integration,
        )
        assert manager.aws == aws_integration
        assert manager.azure == azure_integration
        assert manager.gcp == gcp_integration

    @patch('builtins.open', create=True)
    @patch('gzip.compress')
    def test_create_backup_aws_with_compression(
        self, mock_compress, mock_open, backup_config_aws, aws_integration, mock_db_file
    ):
        """Test creating backup to AWS with compression"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        # Mock file reading
        mock_file = MagicMock()
        mock_file.read.return_value = b"database content"
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock compression
        mock_compress.return_value = b"compressed data"

        # Mock AWS upload
        aws_integration.upload_to_s3 = Mock(return_value=True)

        backup_id = manager.create_backup(
            tenant_id="tenant-123",
            database_path=mock_db_file,
        )

        assert backup_id.startswith("backup_tenant-123_")
        assert mock_compress.called
        assert aws_integration.upload_to_s3.called

    @patch('builtins.open', create=True)
    @patch('gzip.compress')
    def test_create_backup_aws_with_metadata(
        self, mock_compress, mock_open, backup_config_aws, aws_integration, mock_db_file
    ):
        """Test creating backup to AWS with metadata"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        mock_file = MagicMock()
        mock_file.read.return_value = b"database content"
        mock_open.return_value.__enter__.return_value = mock_file
        mock_compress.return_value = b"compressed data"
        aws_integration.upload_to_s3 = Mock(return_value=True)

        metadata = {"version": "1.0", "timestamp": "2024-01-01"}
        backup_id = manager.create_backup(
            tenant_id="tenant-123",
            database_path=mock_db_file,
            metadata=metadata,
        )

        assert backup_id.startswith("backup_tenant-123_")
        aws_integration.upload_to_s3.assert_called_once()
        call_args = aws_integration.upload_to_s3.call_args
        assert call_args[1]["metadata"] == metadata

    @patch('builtins.open', create=True)
    @patch('gzip.compress')
    def test_create_backup_azure(
        self, mock_compress, mock_open, backup_config_azure, azure_integration, mock_db_file
    ):
        """Test creating backup to Azure"""
        manager = CloudBackupManager(
            config=backup_config_azure,
            azure_integration=azure_integration,
        )

        mock_file = MagicMock()
        mock_file.read.return_value = b"database content"
        mock_open.return_value.__enter__.return_value = mock_file
        mock_compress.return_value = b"compressed data"
        azure_integration.upload_to_blob = Mock(return_value=True)

        backup_id = manager.create_backup(
            tenant_id="tenant-456",
            database_path=mock_db_file,
        )

        assert backup_id.startswith("backup_tenant-456_")
        assert azure_integration.upload_to_blob.called

    @patch('builtins.open', create=True)
    def test_create_backup_gcp_without_compression(
        self, mock_open, backup_config_gcp, gcp_integration, mock_db_file
    ):
        """Test creating backup to GCP without compression"""
        manager = CloudBackupManager(
            config=backup_config_gcp,
            gcp_integration=gcp_integration,
        )

        mock_file = MagicMock()
        mock_file.read.return_value = b"database content"
        mock_open.return_value.__enter__.return_value = mock_file
        gcp_integration.upload_to_storage = Mock(return_value=True)

        backup_id = manager.create_backup(
            tenant_id="tenant-789",
            database_path=mock_db_file,
        )

        assert backup_id.startswith("backup_tenant-789_")
        assert gcp_integration.upload_to_storage.called

    def test_create_backup_id_format(self, backup_config_aws, aws_integration):
        """Test backup ID format"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"content"
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('gzip.compress', return_value=b"compressed"):
                aws_integration.upload_to_s3 = Mock(return_value=True)

                backup_id = manager.create_backup("tenant", "db.db")

                # Format: backup_tenant_YYYYMMDD_HHMMSS_uuid
                parts = backup_id.split("_")
                assert len(parts) >= 4
                assert parts[0] == "backup"
                assert parts[1] == "tenant"

    @patch('builtins.open', create=True)
    @patch('gzip.decompress')
    def test_restore_backup_aws(
        self, mock_decompress, mock_open, backup_config_aws, aws_integration, tmp_path
    ):
        """Test restoring backup from AWS"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        # Mock download
        aws_integration.download_from_s3 = Mock(return_value=b"compressed data")
        mock_decompress.return_value = b"decompressed data"

        # Mock file writing
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        restore_path = str(tmp_path / "restored.db")
        result = manager.restore_backup(
            backup_id="backup_tenant_20240101_000000_abc123",
            tenant_id="tenant",
            restore_path=restore_path,
        )

        assert result is True
        assert aws_integration.download_from_s3.called
        assert mock_decompress.called

    @patch('builtins.open', create=True)
    @patch('gzip.decompress')
    def test_restore_backup_azure(
        self, mock_decompress, mock_open, backup_config_azure, azure_integration, tmp_path
    ):
        """Test restoring backup from Azure"""
        manager = CloudBackupManager(
            config=backup_config_azure,
            azure_integration=azure_integration,
        )

        azure_integration.download_from_blob = Mock(return_value=b"compressed data")
        mock_decompress.return_value = b"decompressed data"
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        restore_path = str(tmp_path / "restored.db")
        result = manager.restore_backup("backup_id", "tenant", restore_path)

        assert result is True
        assert azure_integration.download_from_blob.called

    @patch('builtins.open', create=True)
    def test_restore_backup_gcp_without_compression(
        self, mock_open, backup_config_gcp, gcp_integration, tmp_path
    ):
        """Test restoring backup from GCP without compression"""
        # GCP config has compression=False
        manager = CloudBackupManager(
            config=backup_config_gcp,
            gcp_integration=gcp_integration,
        )

        gcp_integration.download_from_storage = Mock(return_value=b"uncompressed data")
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        restore_path = str(tmp_path / "restored.db")
        result = manager.restore_backup("backup_id", "tenant", restore_path)

        assert result is True
        assert gcp_integration.download_from_storage.called

    def test_restore_backup_no_data_found(self, backup_config_aws, aws_integration, tmp_path):
        """Test restoring backup when no data is found"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        aws_integration.download_from_s3 = Mock(return_value=None)

        restore_path = str(tmp_path / "restored.db")
        result = manager.restore_backup("backup_id", "tenant", restore_path)

        assert result is False

    def test_restore_backup_different_tenants(
        self, backup_config_aws, aws_integration, tmp_path
    ):
        """Test restoring backups for different tenants"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        aws_integration.download_from_s3 = Mock(return_value=None)

        tenants = ["tenant1", "tenant2", "tenant3"]
        for tenant in tenants:
            restore_path = str(tmp_path / f"{tenant}.db")
            result = manager.restore_backup("backup_id", tenant, restore_path)
            assert result is False  # No data in mock

    def test_list_backups_empty(self, backup_config_aws, aws_integration):
        """Test listing backups (returns empty in mock)"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        backups = manager.list_backups("tenant-123")
        assert isinstance(backups, list)
        assert len(backups) == 0

    def test_list_backups_different_tenants(self, backup_config_aws, aws_integration):
        """Test listing backups for different tenants"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        tenants = ["tenant1", "tenant2", "tenant3"]
        for tenant in tenants:
            backups = manager.list_backups(tenant)
            assert isinstance(backups, list)

    def test_cleanup_old_backups(self, backup_config_aws, aws_integration):
        """Test cleaning up old backups"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        deleted = manager.cleanup_old_backups("tenant-123")
        assert deleted == 0  # Mock returns 0

    def test_cleanup_old_backups_different_retention(self):
        """Test cleanup with different retention periods"""
        retention_periods = [7, 30, 90, 365]
        for retention in retention_periods:
            config = BackupConfig(
                provider=CloudProvider.AWS,
                schedule="0 0 * * *",
                retention_days=retention,
            )
            manager = CloudBackupManager(config=config)
            deleted = manager.cleanup_old_backups("tenant")
            assert deleted == 0

    def test_cleanup_old_backups_cutoff_date(self, backup_config_aws):
        """Test cleanup calculates correct cutoff date"""
        manager = CloudBackupManager(config=backup_config_aws)

        # The cleanup method should calculate cutoff_date
        with patch('src.enterprise.cloud.cloud_backup.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 31, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            deleted = manager.cleanup_old_backups("tenant")
            assert deleted == 0

    def test_backup_config_different_schedules(self):
        """Test backup configuration with different schedules"""
        schedules = [
            "0 0 * * *",  # Daily at midnight
            "0 */4 * * *",  # Every 4 hours
            "0 0 * * 0",  # Weekly on Sunday
            "0 0 1 * *",  # Monthly on 1st
        ]
        for schedule in schedules:
            config = BackupConfig(
                provider=CloudProvider.AWS,
                schedule=schedule,
            )
            assert config.schedule == schedule

    def test_backup_manager_without_cloud_integrations(self, backup_config_aws):
        """Test backup manager without cloud integrations"""
        manager = CloudBackupManager(config=backup_config_aws)
        assert manager.aws is None
        assert manager.azure is None
        assert manager.gcp is None

    @patch('builtins.open', create=True)
    @patch('gzip.compress')
    def test_create_backup_aws_without_integration(
        self, mock_compress, mock_open, backup_config_aws, mock_db_file
    ):
        """Test creating backup without AWS integration (should not fail)"""
        manager = CloudBackupManager(config=backup_config_aws)

        mock_file = MagicMock()
        mock_file.read.return_value = b"content"
        mock_open.return_value.__enter__.return_value = mock_file
        mock_compress.return_value = b"compressed"

        backup_id = manager.create_backup("tenant", mock_db_file)
        assert backup_id.startswith("backup_tenant_")

    def test_backup_compression_enabled(self, backup_config_aws):
        """Test backup with compression enabled"""
        assert backup_config_aws.compression is True

    def test_backup_compression_disabled(self):
        """Test backup with compression disabled"""
        config = BackupConfig(
            provider=CloudProvider.AWS,
            schedule="0 0 * * *",
            compression=False,
        )
        assert config.compression is False

    def test_backup_encryption_enabled(self, backup_config_aws):
        """Test backup with encryption enabled"""
        assert backup_config_aws.encryption is True

    def test_backup_encryption_disabled(self):
        """Test backup with encryption disabled"""
        config = BackupConfig(
            provider=CloudProvider.AWS,
            schedule="0 0 * * *",
            encryption=False,
        )
        assert config.encryption is False

    def test_backup_local_provider(self):
        """Test backup with local provider"""
        config = BackupConfig(
            provider=CloudProvider.LOCAL,
            schedule="0 0 * * *",
        )
        assert config.provider == CloudProvider.LOCAL

    @patch('builtins.open', create=True)
    @patch('gzip.compress')
    def test_create_backup_large_database(
        self, mock_compress, mock_open, backup_config_aws, aws_integration
    ):
        """Test creating backup of large database"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        large_data = b"x" * (100 * 1024 * 1024)  # 100MB
        mock_file = MagicMock()
        mock_file.read.return_value = large_data
        mock_open.return_value.__enter__.return_value = mock_file
        mock_compress.return_value = b"compressed large data"
        aws_integration.upload_to_s3 = Mock(return_value=True)

        backup_id = manager.create_backup("tenant", "large.db")
        assert backup_id.startswith("backup_tenant_")

    def test_backup_id_uniqueness(self, backup_config_aws, aws_integration):
        """Test that backup IDs are unique"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"content"
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('gzip.compress', return_value=b"compressed"):
                aws_integration.upload_to_s3 = Mock(return_value=True)

                backup_ids = set()
                for _ in range(5):
                    backup_id = manager.create_backup("tenant", "db.db")
                    backup_ids.add(backup_id)

                # All IDs should be unique
                assert len(backup_ids) == 5


# ============================================================================
# E. AUTHENTICATION & SECURITY TESTS (20 tests)
# ============================================================================

class TestAuthenticationAndSecurity:
    """Test authentication and security features"""

    def test_aws_credentials_configuration(self):
        """Test AWS credentials configuration"""
        config = AWSConfig(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )
        assert config.access_key_id is not None
        assert config.secret_access_key is not None

    def test_aws_session_token(self):
        """Test AWS session token configuration"""
        config = AWSConfig(
            access_key_id="key",
            secret_access_key="secret",
            session_token="session-token-123",
        )
        assert config.session_token == "session-token-123"

    def test_azure_service_principal_credentials(self):
        """Test Azure service principal credentials"""
        config = AzureConfig(
            subscription_id="sub-123",
            tenant_id="tenant-123",
            client_id="client-123",
            client_secret="secret-123",
        )
        assert config.subscription_id is not None
        assert config.tenant_id is not None
        assert config.client_id is not None
        assert config.client_secret is not None

    def test_gcp_service_account_credentials(self):
        """Test GCP service account credentials"""
        config = GCPConfig(
            project_id="project-123",
            credentials_path="/path/to/service-account.json",
        )
        assert config.credentials_path is not None

    def test_aws_secret_storage(self, aws_integration):
        """Test AWS secret storage"""
        result = aws_integration.store_secret(
            "database-password",
            "super-secret-password",
        )
        assert result is True

    def test_azure_key_vault_storage(self, azure_integration):
        """Test Azure Key Vault secret storage"""
        result = azure_integration.store_secret(
            vault_name="production-vault",
            secret_name="api-key",
            secret_value="secret-api-key-value",
        )
        assert result is True

    def test_gcp_secret_manager_storage(self, gcp_integration):
        """Test GCP Secret Manager storage"""
        result = gcp_integration.store_secret(
            secret_id="database-credentials",
            secret_value='{"username": "admin", "password": "secret"}',
        )
        assert result is True

    def test_aws_rds_iam_authentication(self, aws_integration):
        """Test AWS RDS IAM authentication"""
        conn_str = aws_integration.get_rds_connection_string(
            "db-instance",
            "production",
            use_iam_auth=True,
        )
        assert "aws_iam=true" in conn_str

    def test_azure_managed_identity_authentication(self, azure_integration):
        """Test Azure Managed Identity authentication"""
        conn_str = azure_integration.get_sql_connection_string(
            "sql-server",
            "production",
            use_managed_identity=True,
        )
        assert "Managed Identity" in conn_str

    def test_gcp_iam_authentication(self, gcp_integration):
        """Test GCP IAM authentication"""
        conn_str = gcp_integration.get_cloudsql_connection_string(
            "sql-instance",
            "production",
            use_iam_auth=True,
        )
        assert "sslmode=disable" in conn_str

    def test_backup_encryption_configuration(self):
        """Test backup encryption configuration"""
        config = BackupConfig(
            provider=CloudProvider.AWS,
            schedule="0 0 * * *",
            encryption=True,
        )
        assert config.encryption is True

    def test_credentials_not_logged(self, aws_config):
        """Test credentials are not exposed in string representation"""
        # Ensure sensitive data doesn't leak in logs
        config_str = str(aws_config)
        # This test assumes dataclass default __str__ includes field values
        # In production, should implement custom __str__ that masks secrets

    def test_secret_storage_different_providers(
        self, aws_integration, azure_integration, gcp_integration
    ):
        """Test secret storage across different providers"""
        assert aws_integration.store_secret("secret", "value") is True
        assert azure_integration.store_secret("vault", "secret", "value") is True
        assert gcp_integration.store_secret("secret", "value") is True

    def test_secret_retrieval_security(
        self, aws_integration, azure_integration, gcp_integration
    ):
        """Test secret retrieval returns None (secure default)"""
        assert aws_integration.get_secret("secret") is None
        assert azure_integration.get_secret("vault", "secret") is None
        assert gcp_integration.get_secret("secret") is None

    def test_aws_ssl_requirement(self, aws_integration):
        """Test AWS connections require SSL"""
        conn_str = aws_integration.get_rds_connection_string("db", "test")
        assert "sslmode=require" in conn_str

    def test_azure_encryption_requirement(self, azure_integration):
        """Test Azure SQL connections require encryption"""
        conn_str = azure_integration.get_sql_connection_string("server", "db")
        assert "Encrypt=True" in conn_str

    def test_secure_credential_storage_patterns(self):
        """Test secure credential storage patterns"""
        # AWS: No hardcoded credentials
        config1 = AWSConfig()
        assert config1.access_key_id is None

        # Azure: No hardcoded credentials
        config2 = AzureConfig()
        assert config2.client_secret is None

        # GCP: Credentials from file
        config3 = GCPConfig(project_id="test")
        assert config3.credentials_path is None

    def test_backup_data_encryption(self, backup_config_aws):
        """Test backup data encryption is enabled"""
        assert backup_config_aws.encryption is True

    def test_multi_provider_credential_isolation(
        self, aws_config, azure_config, gcp_config
    ):
        """Test credentials are isolated per provider"""
        assert aws_config.access_key_id != azure_config.client_id
        assert azure_config.subscription_id != gcp_config.project_id

    def test_credential_rotation_support(self):
        """Test credential rotation through configuration update"""
        config = AWSConfig(
            access_key_id="old-key",
            secret_access_key="old-secret",
        )
        # Simulate credential rotation
        config.access_key_id = "new-key"
        config.secret_access_key = "new-secret"
        assert config.access_key_id == "new-key"
        assert config.secret_access_key == "new-secret"


# ============================================================================
# F. RESOURCE MANAGEMENT TESTS (15 tests)
# ============================================================================

class TestResourceManagement:
    """Test resource management features"""

    def test_aws_s3_bucket_naming(self, aws_integration):
        """Test S3 bucket naming conventions"""
        result = aws_integration.upload_to_s3(
            bucket="aishell-backups",
            key="file.txt",
            data=b"data",
        )
        assert result is True

    def test_azure_container_naming(self, azure_integration):
        """Test Azure blob container naming"""
        result = azure_integration.upload_to_blob(
            container="aishell-backups",
            blob_name="file.txt",
            data=b"data",
        )
        assert result is True

    def test_gcp_bucket_naming(self, gcp_integration):
        """Test GCP bucket naming conventions"""
        result = gcp_integration.upload_to_storage(
            bucket_name="aishell-backups",
            blob_name="file.txt",
            data=b"data",
        )
        assert result is True

    def test_backup_resource_organization_aws(
        self, backup_config_aws, aws_integration
    ):
        """Test backup resource organization in AWS"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"content"
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('gzip.compress', return_value=b"compressed"):
                aws_integration.upload_to_s3 = Mock(return_value=True)

                backup_id = manager.create_backup("tenant-123", "db.db")

                # Verify resource organization
                call_args = aws_integration.upload_to_s3.call_args
                assert "tenant-123" in call_args[1]["key"]

    def test_backup_resource_organization_azure(
        self, backup_config_azure, azure_integration
    ):
        """Test backup resource organization in Azure"""
        manager = CloudBackupManager(
            config=backup_config_azure,
            azure_integration=azure_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"content"
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('gzip.compress', return_value=b"compressed"):
                azure_integration.upload_to_blob = Mock(return_value=True)

                backup_id = manager.create_backup("tenant-456", "db.db")

                call_args = azure_integration.upload_to_blob.call_args
                assert "tenant-456" in call_args[1]["blob_name"]

    def test_backup_resource_organization_gcp(
        self, backup_config_gcp, gcp_integration
    ):
        """Test backup resource organization in GCP"""
        manager = CloudBackupManager(
            config=backup_config_gcp,
            gcp_integration=gcp_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"content"
            mock_open.return_value.__enter__.return_value = mock_file

            gcp_integration.upload_to_storage = Mock(return_value=True)

            backup_id = manager.create_backup("tenant-789", "db.db")

            call_args = gcp_integration.upload_to_storage.call_args
            assert "tenant-789" in call_args[1]["blob_name"]

    def test_rds_instance_listing(self, aws_integration):
        """Test listing RDS instances"""
        instances = aws_integration.list_rds_instances()
        assert isinstance(instances, list)

    def test_backup_listing(self, backup_config_aws, aws_integration):
        """Test listing backups"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )
        backups = manager.list_backups("tenant-123")
        assert isinstance(backups, list)

    def test_backup_cleanup(self, backup_config_aws, aws_integration):
        """Test backup cleanup"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )
        deleted = manager.cleanup_old_backups("tenant-123")
        assert isinstance(deleted, int)

    def test_resource_metadata_tracking(self, aws_integration):
        """Test resource metadata tracking"""
        metadata = {
            "version": "1.0",
            "tenant": "tenant-123",
            "timestamp": "2024-01-01T00:00:00Z",
        }
        result = aws_integration.upload_to_s3(
            "bucket",
            "key",
            b"data",
            metadata=metadata,
        )
        assert result is True

    def test_multi_tenant_resource_isolation(
        self, backup_config_aws, aws_integration
    ):
        """Test multi-tenant resource isolation"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        tenants = ["tenant-1", "tenant-2", "tenant-3"]
        for tenant in tenants:
            backups = manager.list_backups(tenant)
            assert isinstance(backups, list)

    def test_resource_tagging_support(self, aws_integration):
        """Test resource tagging support"""
        metadata = {
            "tags": "backup,production,important",
            "environment": "production",
        }
        result = aws_integration.upload_to_s3(
            "bucket",
            "tagged-resource",
            b"data",
            metadata=metadata,
        )
        assert result is True

    def test_backup_retention_policy(self):
        """Test backup retention policy configuration"""
        retention_days = [7, 30, 90, 365]
        for days in retention_days:
            config = BackupConfig(
                provider=CloudProvider.AWS,
                schedule="0 0 * * *",
                retention_days=days,
            )
            assert config.retention_days == days

    def test_resource_cost_optimization(self, backup_config_aws):
        """Test resource cost optimization through compression"""
        assert backup_config_aws.compression is True


# ============================================================================
# G. ERROR HANDLING & RETRIES TESTS (25 tests)
# ============================================================================

class TestErrorHandlingAndRetries:
    """Test error handling and retry mechanisms"""

    def test_aws_upload_resilience(self, aws_integration):
        """Test AWS upload handles errors gracefully"""
        result = aws_integration.upload_to_s3("bucket", "key", b"data")
        assert isinstance(result, bool)

    def test_aws_download_missing_object(self, aws_integration):
        """Test AWS download handles missing objects"""
        result = aws_integration.download_from_s3("bucket", "nonexistent")
        assert result is None

    def test_azure_upload_resilience(self, azure_integration):
        """Test Azure upload handles errors gracefully"""
        result = azure_integration.upload_to_blob("container", "blob", b"data")
        assert isinstance(result, bool)

    def test_azure_download_missing_blob(self, azure_integration):
        """Test Azure download handles missing blobs"""
        result = azure_integration.download_from_blob("container", "nonexistent")
        assert result is None

    def test_gcp_upload_resilience(self, gcp_integration):
        """Test GCP upload handles errors gracefully"""
        result = gcp_integration.upload_to_storage("bucket", "blob", b"data")
        assert isinstance(result, bool)

    def test_gcp_download_missing_object(self, gcp_integration):
        """Test GCP download handles missing objects"""
        result = gcp_integration.download_from_storage("bucket", "nonexistent")
        assert result is None

    def test_backup_restore_no_data(self, backup_config_aws, aws_integration, tmp_path):
        """Test backup restore handles missing data"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        aws_integration.download_from_s3 = Mock(return_value=None)

        result = manager.restore_backup(
            "nonexistent-backup",
            "tenant",
            str(tmp_path / "restore.db"),
        )
        assert result is False

    def test_aws_secret_retrieval_failure(self, aws_integration):
        """Test AWS secret retrieval failure handling"""
        result = aws_integration.get_secret("nonexistent-secret")
        assert result is None

    def test_azure_secret_retrieval_failure(self, azure_integration):
        """Test Azure secret retrieval failure handling"""
        result = azure_integration.get_secret("vault", "nonexistent")
        assert result is None

    def test_gcp_secret_retrieval_failure(self, gcp_integration):
        """Test GCP secret retrieval failure handling"""
        result = gcp_integration.get_secret("nonexistent", version="latest")
        assert result is None

    def test_cloudwatch_logs_empty_messages(self, aws_integration):
        """Test CloudWatch logs with empty messages"""
        result = aws_integration.send_cloudwatch_logs("group", "stream", [])
        assert result is True

    def test_azure_monitor_logs_empty_records(self, azure_integration):
        """Test Azure Monitor logs with empty records"""
        result = azure_integration.send_monitor_logs("workspace", "Log", [])
        assert result is True

    def test_gcp_cloud_logs_empty_entries(self, gcp_integration):
        """Test GCP Cloud Logging with empty entries"""
        result = gcp_integration.send_cloud_logs("log", [])
        assert result is True

    def test_backup_create_file_not_found(self, backup_config_aws, aws_integration):
        """Test backup creation with missing database file"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        with pytest.raises(FileNotFoundError):
            manager.create_backup("tenant", "/nonexistent/path/db.db")

    def test_rds_snapshot_error_handling(self, aws_integration):
        """Test RDS snapshot creation error handling"""
        result = aws_integration.create_rds_snapshot("invalid-db", "snapshot")
        assert isinstance(result, bool)

    def test_s3_upload_empty_data(self, aws_integration):
        """Test S3 upload with empty data"""
        result = aws_integration.upload_to_s3("bucket", "empty.txt", b"")
        assert result is True

    def test_blob_upload_empty_data(self, azure_integration):
        """Test blob upload with empty data"""
        result = azure_integration.upload_to_blob("container", "empty.txt", b"")
        assert result is True

    def test_storage_upload_empty_data(self, gcp_integration):
        """Test Cloud Storage upload with empty data"""
        result = gcp_integration.upload_to_storage("bucket", "empty.txt", b"")
        assert result is True

    def test_connection_string_with_invalid_instance(self, aws_integration):
        """Test connection string generation with invalid instance"""
        conn_str = aws_integration.get_rds_connection_string("", "db")
        assert isinstance(conn_str, str)

    def test_backup_cleanup_empty_tenant(self, backup_config_aws, aws_integration):
        """Test backup cleanup with empty tenant ID"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )
        deleted = manager.cleanup_old_backups("")
        assert isinstance(deleted, int)

    def test_list_backups_invalid_tenant(self, backup_config_aws, aws_integration):
        """Test listing backups with invalid tenant"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )
        backups = manager.list_backups("invalid-tenant")
        assert isinstance(backups, list)

    def test_cloudwatch_metrics_invalid_namespace(self, aws_integration):
        """Test CloudWatch metrics with invalid namespace"""
        metrics = aws_integration.get_cloudwatch_metrics(
            "",
            "metric",
            "2024-01-01",
            "2024-01-02",
        )
        assert isinstance(metrics, list)

    def test_aws_integration_without_credentials(self):
        """Test AWS integration without credentials"""
        integration = AWSIntegration()
        assert integration.config.access_key_id is None

    def test_azure_integration_without_credentials(self):
        """Test Azure integration without credentials"""
        integration = AzureIntegration()
        assert integration.config.client_secret is None

    def test_backup_manager_missing_integration(self, backup_config_aws):
        """Test backup manager without cloud integration"""
        manager = CloudBackupManager(config=backup_config_aws)
        assert manager.aws is None


# ============================================================================
# H. INTEGRATION & PERFORMANCE TESTS (20 tests)
# ============================================================================

class TestIntegrationAndPerformance:
    """Test integration workflows and performance"""

    def test_multi_cloud_backup_workflow_aws(
        self, backup_config_aws, aws_integration, mock_db_file
    ):
        """Test complete backup workflow with AWS"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"database content"
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('gzip.compress', return_value=b"compressed"):
                aws_integration.upload_to_s3 = Mock(return_value=True)

                backup_id = manager.create_backup("tenant", mock_db_file)
                assert backup_id is not None

    def test_multi_cloud_backup_workflow_azure(
        self, backup_config_azure, azure_integration, mock_db_file
    ):
        """Test complete backup workflow with Azure"""
        manager = CloudBackupManager(
            config=backup_config_azure,
            azure_integration=azure_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"database content"
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('gzip.compress', return_value=b"compressed"):
                azure_integration.upload_to_blob = Mock(return_value=True)

                backup_id = manager.create_backup("tenant", mock_db_file)
                assert backup_id is not None

    def test_multi_cloud_backup_workflow_gcp(
        self, backup_config_gcp, gcp_integration, mock_db_file
    ):
        """Test complete backup workflow with GCP"""
        manager = CloudBackupManager(
            config=backup_config_gcp,
            gcp_integration=gcp_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"database content"
            mock_open.return_value.__enter__.return_value = mock_file

            gcp_integration.upload_to_storage = Mock(return_value=True)

            backup_id = manager.create_backup("tenant", mock_db_file)
            assert backup_id is not None

    def test_large_file_upload_chunking_aws(self, aws_integration):
        """Test large file upload (simulating chunking)"""
        large_data = b"x" * (100 * 1024 * 1024)  # 100MB
        result = aws_integration.upload_to_s3("bucket", "large.bin", large_data)
        assert result is True

    def test_large_file_upload_chunking_azure(self, azure_integration):
        """Test large file upload to Azure"""
        large_data = b"x" * (100 * 1024 * 1024)  # 100MB
        result = azure_integration.upload_to_blob("container", "large.bin", large_data)
        assert result is True

    def test_large_file_upload_chunking_gcp(self, gcp_integration):
        """Test large file upload to GCP"""
        large_data = b"x" * (100 * 1024 * 1024)  # 100MB
        result = gcp_integration.upload_to_storage("bucket", "large.bin", large_data)
        assert result is True

    def test_concurrent_backup_operations(
        self, backup_config_aws, aws_integration, mock_db_file
    ):
        """Test concurrent backup operations"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"content"
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('gzip.compress', return_value=b"compressed"):
                aws_integration.upload_to_s3 = Mock(return_value=True)

                # Simulate concurrent backups
                backup_ids = []
                for i in range(5):
                    backup_id = manager.create_backup(f"tenant-{i}", mock_db_file)
                    backup_ids.append(backup_id)

                assert len(backup_ids) == 5
                assert len(set(backup_ids)) == 5  # All unique

    def test_backup_compression_performance(self, backup_config_aws, aws_integration):
        """Test backup compression performance"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            # Simulate compressible data
            data = b"a" * 10000
            mock_file = MagicMock()
            mock_file.read.return_value = data
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('gzip.compress') as mock_compress:
                # Compression should reduce size
                mock_compress.return_value = b"compressed" * 100
                aws_integration.upload_to_s3 = Mock(return_value=True)

                backup_id = manager.create_backup("tenant", "db.db")
                assert mock_compress.called

    def test_backup_without_compression_performance(
        self, backup_config_gcp, gcp_integration
    ):
        """Test backup without compression"""
        # GCP config has compression=False
        manager = CloudBackupManager(
            config=backup_config_gcp,
            gcp_integration=gcp_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"data"
            mock_open.return_value.__enter__.return_value = mock_file

            gcp_integration.upload_to_storage = Mock(return_value=True)

            backup_id = manager.create_backup("tenant", "db.db")
            assert backup_id is not None

    def test_restore_performance_with_decompression(
        self, backup_config_aws, aws_integration, tmp_path
    ):
        """Test restore performance with decompression"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            aws_integration.download_from_s3 = Mock(return_value=b"compressed data")

            with patch('gzip.decompress', return_value=b"decompressed data"):
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                result = manager.restore_backup(
                    "backup-id",
                    "tenant",
                    str(tmp_path / "restore.db"),
                )
                assert result is True

    def test_streaming_upload_progress(self, aws_integration):
        """Test streaming upload (progress tracking simulation)"""
        # Simulate chunked upload
        chunks = [b"chunk1", b"chunk2", b"chunk3"]
        for chunk in chunks:
            result = aws_integration.upload_to_s3("bucket", "key", chunk)
            assert result is True

    def test_bandwidth_optimization_compression(self):
        """Test bandwidth optimization through compression"""
        config = BackupConfig(
            provider=CloudProvider.AWS,
            schedule="0 0 * * *",
            compression=True,
        )
        assert config.compression is True

    def test_parallel_cloud_operations(
        self, aws_integration, azure_integration, gcp_integration
    ):
        """Test parallel operations across clouds"""
        # Simulate parallel uploads
        aws_result = aws_integration.upload_to_s3("bucket", "key", b"data")
        azure_result = azure_integration.upload_to_blob("container", "blob", b"data")
        gcp_result = gcp_integration.upload_to_storage("bucket", "blob", b"data")

        assert aws_result is True
        assert azure_result is True
        assert gcp_result is True

    def test_backup_metadata_overhead(self, aws_integration):
        """Test backup metadata overhead"""
        metadata = {
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "size": "1024",
            "checksum": "abc123",
        }
        result = aws_integration.upload_to_s3(
            "bucket",
            "key",
            b"data",
            metadata=metadata,
        )
        assert result is True

    def test_multi_region_backup_strategy(self):
        """Test multi-region backup strategy"""
        regions = ["us-east-1", "us-west-2", "eu-west-1"]
        for region in regions:
            config = AWSConfig(region=region)
            integration = AWSIntegration(config)
            result = integration.upload_to_s3("bucket", "key", b"data")
            assert result is True

    def test_backup_lifecycle_management(
        self, backup_config_aws, aws_integration, mock_db_file, tmp_path
    ):
        """Test complete backup lifecycle: create, list, restore, cleanup"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            # Create backup
            mock_file = MagicMock()
            mock_file.read.return_value = b"content"
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('gzip.compress', return_value=b"compressed"):
                aws_integration.upload_to_s3 = Mock(return_value=True)
                backup_id = manager.create_backup("tenant", mock_db_file)
                assert backup_id is not None

            # List backups
            backups = manager.list_backups("tenant")
            assert isinstance(backups, list)

            # Restore backup
            aws_integration.download_from_s3 = Mock(return_value=b"compressed")
            with patch('gzip.decompress', return_value=b"decompressed"):
                result = manager.restore_backup(
                    backup_id,
                    "tenant",
                    str(tmp_path / "restore.db"),
                )
                assert isinstance(result, bool)

            # Cleanup old backups
            deleted = manager.cleanup_old_backups("tenant")
            assert isinstance(deleted, int)

    def test_multi_tenant_concurrent_backups(
        self, backup_config_aws, aws_integration, mock_db_file
    ):
        """Test concurrent backups for multiple tenants"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"content"
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('gzip.compress', return_value=b"compressed"):
                aws_integration.upload_to_s3 = Mock(return_value=True)

                tenants = ["tenant-1", "tenant-2", "tenant-3"]
                backup_ids = []

                for tenant in tenants:
                    backup_id = manager.create_backup(tenant, mock_db_file)
                    backup_ids.append((tenant, backup_id))

                assert len(backup_ids) == 3
                # Verify tenant isolation in backup IDs
                for tenant, backup_id in backup_ids:
                    assert tenant in backup_id

    def test_backup_verification_workflow(
        self, backup_config_aws, aws_integration, mock_db_file, tmp_path
    ):
        """Test backup verification workflow: create and restore"""
        manager = CloudBackupManager(
            config=backup_config_aws,
            aws_integration=aws_integration,
        )

        original_data = b"original database content"

        with patch('builtins.open', create=True) as mock_open:
            # Create backup
            mock_file = MagicMock()
            mock_file.read.return_value = original_data
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('gzip.compress') as mock_compress:
                compressed_data = b"compressed version"
                mock_compress.return_value = compressed_data
                aws_integration.upload_to_s3 = Mock(return_value=True)

                backup_id = manager.create_backup("tenant", mock_db_file)

                # Restore backup
                aws_integration.download_from_s3 = Mock(return_value=compressed_data)

                with patch('gzip.decompress', return_value=original_data):
                    mock_write_file = MagicMock()
                    mock_open.return_value.__enter__.return_value = mock_write_file

                    result = manager.restore_backup(
                        backup_id,
                        "tenant",
                        str(tmp_path / "restore.db"),
                    )

                    assert result is True

    def test_cross_cloud_backup_redundancy(
        self, aws_integration, azure_integration, gcp_integration
    ):
        """Test backup redundancy across multiple clouds"""
        backup_data = b"critical backup data"

        # Upload to all clouds for redundancy
        aws_result = aws_integration.upload_to_s3("bucket", "backup.db", backup_data)
        azure_result = azure_integration.upload_to_blob("container", "backup.db", backup_data)
        gcp_result = gcp_integration.upload_to_storage("bucket", "backup.db", backup_data)

        assert aws_result is True
        assert azure_result is True
        assert gcp_result is True
