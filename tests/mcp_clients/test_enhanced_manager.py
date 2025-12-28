"""
Tests for Enhanced MCP Connection Manager
"""

import pytest
import asyncio
from typing import Dict, Any

from src.mcp_clients.enhanced_manager import (
    EnhancedConnectionManager,
    ProtocolType,
    MCPResource,
    APIClient,
    FileStorageClient,
    MessageQueueClient
)
from src.mcp_clients.base import ConnectionConfig, ConnectionState, MCPClientError


class TestEnhancedConnectionManager:
    """Test suite for enhanced MCP connection manager"""

    @pytest.fixture
    async def manager(self):
        """Create manager instance"""
        return EnhancedConnectionManager(max_connections=10)

    @pytest.mark.asyncio
    async def test_initialization(self, manager):
        """Test manager initialization"""
        assert manager._max_connections == 10
        assert len(manager._connections) == 0
        assert len(manager._resources) > 0
        assert 'api' in manager.CLIENT_REGISTRY
        assert 'storage' in manager.CLIENT_REGISTRY
        assert 'queue' in manager.CLIENT_REGISTRY

    @pytest.mark.asyncio
    async def test_list_resources(self, manager):
        """Test resource listing"""
        resources = await manager.list_resources()

        assert len(resources) > 0
        assert any(r.protocol == ProtocolType.DATABASE for r in resources)
        assert any(r.protocol == ProtocolType.REST_API for r in resources)
        assert any(r.protocol == ProtocolType.FILE_STORAGE for r in resources)
        assert any(r.protocol == ProtocolType.MESSAGE_QUEUE for r in resources)

    @pytest.mark.asyncio
    async def test_list_tools(self, manager):
        """Test tool listing"""
        tools = await manager.list_tools()

        assert len(tools) > 0
        tool_names = [t.name for t in tools]
        assert 'execute_sql' in tool_names
        assert 'api_request' in tool_names
        assert 'read_file' in tool_names
        assert 'publish_message' in tool_names

    @pytest.mark.asyncio
    async def test_create_api_connection(self, manager):
        """Test creating API connection"""
        config = ConnectionConfig(
            host="api.example.com",
            port=443,
            database="",
            username="user",
            password="api_key",
            extra_params={"headers": {"X-Custom": "value"}}
        )

        conn_id = await manager.create_connection(
            connection_id="test-api",
            client_type="api",
            config=config
        )

        assert conn_id == "test-api"
        assert "test-api" in manager._connections

        conn_info = manager._connections["test-api"]
        assert isinstance(conn_info.client, APIClient)
        assert conn_info.client.state == ConnectionState.CONNECTED

    @pytest.mark.asyncio
    async def test_create_storage_connection(self, manager):
        """Test creating storage connection"""
        config = ConnectionConfig(
            host="s3.amazonaws.com",
            port=443,
            database="my-bucket",
            username="access_key",
            password="secret_key",
            extra_params={"storage_type": "s3"}
        )

        conn_id = await manager.create_connection(
            connection_id="test-storage",
            client_type="storage",
            config=config
        )

        assert conn_id == "test-storage"
        conn_info = manager._connections["test-storage"]
        assert isinstance(conn_info.client, FileStorageClient)
        assert conn_info.client.bucket == "my-bucket"

    @pytest.mark.asyncio
    async def test_create_queue_connection(self, manager):
        """Test creating message queue connection"""
        config = ConnectionConfig(
            host="rabbitmq.example.com",
            port=5672,
            database="my-queue",
            username="user",
            password="pass",
            extra_params={"queue_type": "rabbitmq"}
        )

        conn_id = await manager.create_connection(
            connection_id="test-queue",
            client_type="queue",
            config=config
        )

        assert conn_id == "test-queue"
        conn_info = manager._connections["test-queue"]
        assert isinstance(conn_info.client, MessageQueueClient)
        assert conn_info.client.queue_name == "my-queue"

    @pytest.mark.asyncio
    async def test_execute_api_tool(self, manager):
        """Test executing API request tool"""
        # Create API connection
        config = ConnectionConfig(
            host="api.example.com",
            port=443,
            database="",
            username="user",
            password="api_key"
        )

        await manager.create_connection("test-api", "api", config)

        # Execute API request tool
        result = await manager.execute_tool(
            tool_name="api_request",
            connection_id="test-api",
            params={
                "method": "GET",
                "endpoint": "/users",
                "body": None
            }
        )

        assert result is not None
        assert result.rowcount == 1

    @pytest.mark.asyncio
    async def test_connection_stats(self, manager):
        """Test getting connection statistics"""
        # Create multiple connections
        configs = [
            ("api1", "api", ConnectionConfig("api1.com", 443, "", "u", "p")),
            ("api2", "api", ConnectionConfig("api2.com", 443, "", "u", "p")),
            ("storage1", "storage", ConnectionConfig("s3.com", 443, "bucket", "u", "p")),
        ]

        for conn_id, conn_type, config in configs:
            await manager.create_connection(conn_id, conn_type, config)

        stats = await manager.get_connection_stats()

        assert stats["total_connections"] == 3
        assert stats["connections_by_type"]["api"] == 2
        assert stats["connections_by_type"]["storage"] == 1
        assert stats["connections_by_state"]["connected"] == 3
        assert stats["resources_available"] > 0
        assert stats["tools_available"] > 0

    @pytest.mark.asyncio
    async def test_max_connections_limit(self, manager):
        """Test maximum connections limit"""
        manager._max_connections = 2

        # Create 2 connections (should work)
        for i in range(2):
            await manager.create_connection(
                f"conn{i}",
                "api",
                ConnectionConfig(f"api{i}.com", 443, "", "u", "p")
            )

        # Third connection should fail
        with pytest.raises(MCPClientError) as exc_info:
            await manager.create_connection(
                "conn3",
                "api",
                ConnectionConfig("api3.com", 443, "", "u", "p")
            )

        assert "Maximum connections" in str(exc_info.value)


class TestAPIClient:
    """Test suite for API client"""

    @pytest.fixture
    async def client(self):
        """Create API client instance"""
        return APIClient()

    @pytest.mark.asyncio
    async def test_connect(self, client):
        """Test API connection"""
        config = ConnectionConfig(
            host="api.example.com",
            port=443,
            database="",
            username="user",
            password="bearer_token"
        )

        connected = await client.connect(config)

        assert connected is True
        assert client.state == ConnectionState.CONNECTED
        assert client.base_url == "https://api.example.com:443"
        assert "Authorization" in client.headers

    @pytest.mark.asyncio
    async def test_execute_query(self, client):
        """Test executing API request"""
        # Connect first
        config = ConnectionConfig("api.example.com", 443, "", "u", "token")
        await client.connect(config)

        # Execute request
        result = await client.execute_query("/users", "GET", {"limit": 10})

        assert result.rowcount == 1
        assert result.metadata["method"] == "GET"
        assert result.metadata["endpoint"] == "/users"

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test API health check"""
        # Connect first
        config = ConnectionConfig("api.example.com", 443, "", "u", "token")
        await client.connect(config)

        health = await client.health_check()

        assert health["healthy"] is True
        assert health["base_url"] == "https://api.example.com:443"
        assert health["connected_at"] is not None


class TestFileStorageClient:
    """Test suite for file storage client"""

    @pytest.fixture
    async def client(self):
        """Create storage client instance"""
        return FileStorageClient()

    @pytest.mark.asyncio
    async def test_connect(self, client):
        """Test storage connection"""
        config = ConnectionConfig(
            host="s3.amazonaws.com",
            port=443,
            database="test-bucket",
            username="access_key",
            password="secret_key",
            extra_params={"storage_type": "s3"}
        )

        connected = await client.connect(config)

        assert connected is True
        assert client.state == ConnectionState.CONNECTED
        assert client.storage_type == "s3"
        assert client.bucket == "test-bucket"

    @pytest.mark.asyncio
    async def test_list_files(self, client):
        """Test file listing"""
        config = ConnectionConfig(
            host="storage", port=443, database="bucket",
            username="u", password="p",
            extra_params={"storage_type": "s3"}
        )
        await client.connect(config)

        files = await client.list_files("data/")

        assert len(files) > 0
        assert all(f.startswith("data/") for f in files)

    @pytest.mark.asyncio
    async def test_read_write_file(self, client):
        """Test file read/write operations"""
        config = ConnectionConfig(
            host="storage", port=443, database="bucket",
            username="u", password="p",
            extra_params={"storage_type": "s3"}
        )
        await client.connect(config)

        # Write file
        content = b"test content"
        written = await client.write_file("test.txt", content)
        assert written is True

        # Read file
        read_content = await client.read_file("test.txt")
        assert read_content is not None


class TestMessageQueueClient:
    """Test suite for message queue client"""

    @pytest.fixture
    async def client(self):
        """Create queue client instance"""
        return MessageQueueClient()

    @pytest.mark.asyncio
    async def test_connect(self, client):
        """Test queue connection"""
        config = ConnectionConfig(
            host="rabbitmq.example.com",
            port=5672,
            database="test-queue",
            username="user",
            password="pass",
            extra_params={"queue_type": "rabbitmq"}
        )

        connected = await client.connect(config)

        assert connected is True
        assert client.state == ConnectionState.CONNECTED
        assert client.queue_type == "rabbitmq"
        assert client.queue_name == "test-queue"

    @pytest.mark.asyncio
    async def test_publish_consume(self, client):
        """Test message publish and consume"""
        config = ConnectionConfig(
            host="queue", port=5672, database="test-queue",
            username="u", password="p",
            extra_params={"queue_type": "rabbitmq"}
        )
        await client.connect(config)

        # Publish message
        message = {"text": "Hello", "id": 123}
        published = await client.publish(message)
        assert published is True

        # Consume message
        messages = await client.consume(1)
        assert len(messages) == 1
        assert messages[0]['message'] == message

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test queue health check"""
        config = ConnectionConfig(
            host="queue", port=5672, database="test-queue",
            username="u", password="p",
            extra_params={"queue_type": "rabbitmq"}
        )
        await client.connect(config)

        # Publish some messages
        await client.publish({"msg": 1})
        await client.publish({"msg": 2})

        health = await client.health_check()

        assert health["healthy"] is True
        assert health["queue_name"] == "test-queue"
        assert health["pending_messages"] == 2