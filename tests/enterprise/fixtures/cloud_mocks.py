"""
Mock fixtures for cloud provider APIs

Provides mocked responses for AWS, Azure, and GCP services for testing
without actual cloud API calls.
"""

from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock
import json


class MockAWSClient:
    """Mock AWS SDK client"""

    def __init__(self, service_name: str, region: str = "us-east-1"):
        self.service_name = service_name
        self.region = region
        self._responses = {}

    def get_rds_endpoint(self, instance_id: str) -> str:
        """Mock RDS endpoint retrieval"""
        return f"{instance_id}.{self.region}.rds.amazonaws.com"

    def create_rds_snapshot(self, instance_id: str, snapshot_id: str) -> Dict[str, Any]:
        """Mock RDS snapshot creation"""
        return {
            'DBSnapshot': {
                'DBSnapshotIdentifier': snapshot_id,
                'DBInstanceIdentifier': instance_id,
                'Status': 'creating',
                'SnapshotCreateTime': '2024-01-01T00:00:00Z'
            }
        }

    def put_secret(self, name: str, value: str) -> Dict[str, Any]:
        """Mock Secrets Manager put"""
        return {
            'ARN': f'arn:aws:secretsmanager:{self.region}:123456789012:secret:{name}',
            'Name': name,
            'VersionId': 'mock-version-id'
        }

    def get_secret(self, name: str) -> Dict[str, Any]:
        """Mock Secrets Manager get"""
        return {
            'ARN': f'arn:aws:secretsmanager:{self.region}:123456789012:secret:{name}',
            'Name': name,
            'SecretString': 'mock-secret-value'
        }

    def put_object(self, bucket: str, key: str, body: bytes) -> Dict[str, Any]:
        """Mock S3 put object"""
        return {
            'ETag': '"mock-etag"',
            'VersionId': 'mock-version'
        }

    def get_object(self, bucket: str, key: str) -> Dict[str, Any]:
        """Mock S3 get object"""
        return {
            'Body': Mock(read=lambda: b'mock-data'),
            'ContentLength': 100,
            'ContentType': 'application/octet-stream'
        }

    def put_log_events(self, log_group: str, log_stream: str, events: List[Dict]) -> Dict[str, Any]:
        """Mock CloudWatch Logs put"""
        return {
            'nextSequenceToken': 'mock-token'
        }


class MockAzureClient:
    """Mock Azure SDK client"""

    def __init__(self, subscription_id: str = "mock-subscription"):
        self.subscription_id = subscription_id

    def create_sql_database(self, resource_group: str, server_name: str, db_name: str) -> Dict[str, Any]:
        """Mock Azure SQL Database creation"""
        return {
            'id': f'/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Sql/servers/{server_name}/databases/{db_name}',
            'name': db_name,
            'type': 'Microsoft.Sql/servers/databases',
            'location': 'eastus',
            'status': 'Online'
        }

    def upload_blob(self, container: str, blob_name: str, data: bytes) -> Dict[str, Any]:
        """Mock Azure Blob Storage upload"""
        return {
            'etag': 'mock-etag',
            'last_modified': '2024-01-01T00:00:00Z',
            'version_id': 'mock-version'
        }

    def get_blob(self, container: str, blob_name: str) -> bytes:
        """Mock Azure Blob Storage download"""
        return b'mock-blob-data'

    def create_key_vault_secret(self, vault_url: str, secret_name: str, secret_value: str) -> Dict[str, Any]:
        """Mock Azure Key Vault secret creation"""
        return {
            'id': f'{vault_url}/secrets/{secret_name}',
            'name': secret_name,
            'value': secret_value
        }


class MockGCPClient:
    """Mock Google Cloud SDK client"""

    def __init__(self, project_id: str = "mock-project"):
        self.project_id = project_id

    def create_sql_instance(self, instance_id: str, database_version: str) -> Dict[str, Any]:
        """Mock Cloud SQL instance creation"""
        return {
            'name': instance_id,
            'project': self.project_id,
            'databaseVersion': database_version,
            'region': 'us-central1',
            'state': 'RUNNABLE',
            'ipAddresses': [
                {'ipAddress': '192.0.2.1', 'type': 'PRIMARY'}
            ]
        }

    def upload_to_gcs(self, bucket: str, object_name: str, data: bytes) -> Dict[str, Any]:
        """Mock Google Cloud Storage upload"""
        return {
            'name': object_name,
            'bucket': bucket,
            'size': len(data),
            'generation': '1234567890'
        }

    def download_from_gcs(self, bucket: str, object_name: str) -> bytes:
        """Mock Google Cloud Storage download"""
        return b'mock-gcs-data'

    def create_secret(self, secret_id: str, secret_data: str) -> Dict[str, Any]:
        """Mock Secret Manager secret creation"""
        return {
            'name': f'projects/{self.project_id}/secrets/{secret_id}',
            'replication': {'automatic': {}},
            'createTime': '2024-01-01T00:00:00Z'
        }


@pytest.fixture
def mock_aws_client():
    """Fixture for mock AWS client"""
    return MockAWSClient('mock-service')


@pytest.fixture
def mock_azure_client():
    """Fixture for mock Azure client"""
    return MockAzureClient()


@pytest.fixture
def mock_gcp_client():
    """Fixture for mock GCP client"""
    return MockGCPClient()


def mock_boto3_client(service_name: str, **kwargs):
    """Mock boto3.client() function"""
    return MockAWSClient(service_name, kwargs.get('region_name', 'us-east-1'))


def mock_azure_credential():
    """Mock Azure credential"""
    mock = Mock()
    mock.get_token = Mock(return_value=Mock(token='mock-token'))
    return mock


def mock_gcp_credentials():
    """Mock GCP credentials"""
    mock = Mock()
    mock.project = 'mock-project'
    return mock
