"""
Tests for MongoDB MCP Client

Covers CRUD operations, aggregation pipelines, and index management.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from bson import ObjectId

from src.mcp_clients.mongodb_client import MongoDBClient
from src.mcp_clients.base import ConnectionConfig, MCPClientError, ConnectionState


@pytest.fixture
def connection_config():
    """Create test connection configuration"""
    return ConnectionConfig(
        host="localhost",
        port=27017,
        database="test_db",
        username="test_user",
        password="test_pass"
    )


@pytest.fixture
def mock_motor_client():
    """Create mock motor client"""
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_client.__getitem__.return_value = mock_db

    # Mock admin command for ping
    mock_admin = MagicMock()
    mock_admin.command = AsyncMock(return_value={'ok': 1})
    mock_client.admin = mock_admin

    return mock_client


@pytest.mark.asyncio
class TestMongoDBClient:
    """Test MongoDB client functionality"""

    async def test_connection(self, connection_config, mock_motor_client):
        """Test MongoDB connection"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            result = await client.connect(connection_config)

            assert result is True
            assert client.state == ConnectionState.CONNECTED
            assert client.is_connected

    async def test_connection_failure(self, connection_config):
        """Test MongoDB connection failure"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient') as mock_class:
            mock_client = AsyncMock()
            mock_admin = MagicMock()
            mock_admin.command = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client.admin = mock_admin
            mock_class.return_value = mock_client

            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(connection_config)

            assert "CONNECTION_FAILED" in str(exc_info.value.error_code)

    async def test_disconnect(self, connection_config, mock_motor_client):
        """Test MongoDB disconnection"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)
            result = await client.disconnect()

            assert result is True
            mock_motor_client.close.assert_called_once()

    async def test_find_operation(self, connection_config, mock_motor_client):
        """Test find operation"""
        client = MongoDBClient()

        # Setup mock collection
        mock_collection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {'_id': ObjectId('507f1f77bcf86cd799439011'), 'name': 'Alice', 'age': 30},
            {'_id': ObjectId('507f1f77bcf86cd799439012'), 'name': 'Bob', 'age': 25}
        ])
        mock_collection.find = Mock(return_value=mock_cursor)

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_motor_client.__getitem__.return_value = mock_db

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)

            query = {
                'operation': 'find',
                'collection': 'users',
                'filter': {'age': {'$gte': 25}},
                'limit': 10
            }

            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 2
            assert len(result.rows) == 2
            assert 'name' in result.columns

    async def test_insert_one_operation(self, connection_config, mock_motor_client):
        """Test insert_one operation"""
        client = MongoDBClient()

        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId('507f1f77bcf86cd799439013')

        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_motor_client.__getitem__.return_value = mock_db

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)

            query = {
                'operation': 'insert_one',
                'collection': 'users',
                'document': {'name': 'Charlie', 'age': 35}
            }

            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 1
            assert 'inserted_id' in result.columns

    async def test_update_many_operation(self, connection_config, mock_motor_client):
        """Test update_many operation"""
        client = MongoDBClient()

        mock_result = MagicMock()
        mock_result.matched_count = 5
        mock_result.modified_count = 5
        mock_result.upserted_id = None

        mock_collection = AsyncMock()
        mock_collection.update_many = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_motor_client.__getitem__.return_value = mock_db

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)

            query = {
                'operation': 'update_many',
                'collection': 'users',
                'filter': {'age': {'$lt': 30}},
                'update': {'$set': {'status': 'young'}}
            }

            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 5

    async def test_delete_many_operation(self, connection_config, mock_motor_client):
        """Test delete_many operation"""
        client = MongoDBClient()

        mock_result = MagicMock()
        mock_result.deleted_count = 3

        mock_collection = AsyncMock()
        mock_collection.delete_many = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_motor_client.__getitem__.return_value = mock_db

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)

            query = {
                'operation': 'delete_many',
                'collection': 'users',
                'filter': {'status': 'inactive'}
            }

            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 3

    async def test_aggregate_operation(self, connection_config, mock_motor_client):
        """Test aggregation pipeline"""
        client = MongoDBClient()

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {'_id': 'young', 'count': 10, 'avg_age': 25},
            {'_id': 'old', 'count': 5, 'avg_age': 45}
        ])

        mock_collection = AsyncMock()
        mock_collection.aggregate = Mock(return_value=mock_cursor)

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_motor_client.__getitem__.return_value = mock_db

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)

            query = {
                'operation': 'aggregate',
                'collection': 'users',
                'pipeline': [
                    {'$group': {'_id': '$status', 'count': {'$sum': 1}, 'avg_age': {'$avg': '$age'}}}
                ]
            }

            result = await client.execute_query(str(query).replace("'", '"'))

            assert result.rowcount == 2
            assert 'count' in result.columns

    async def test_create_index(self, connection_config, mock_motor_client):
        """Test index creation"""
        client = MongoDBClient()

        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock(return_value='age_1')

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_motor_client.__getitem__.return_value = mock_db

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)

            index_name = await client.create_index(
                'users',
                [('age', 1)],
                unique=False
            )

            assert index_name == 'age_1'
            mock_collection.create_index.assert_called_once()

    async def test_list_collections(self, connection_config, mock_motor_client):
        """Test listing collections"""
        client = MongoDBClient()

        mock_db = MagicMock()
        mock_db.list_collection_names = AsyncMock(return_value=['users', 'orders', 'products'])
        mock_motor_client.__getitem__.return_value = mock_db

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)

            collections = await client.get_collections()

            assert len(collections) == 3
            assert 'users' in collections

    async def test_collection_stats(self, connection_config, mock_motor_client):
        """Test getting collection statistics"""
        client = MongoDBClient()

        mock_db = MagicMock()
        mock_db.command = AsyncMock(return_value={
            'count': 100,
            'size': 10240,
            'avgObjSize': 102,
            'storageSize': 20480,
            'nindexes': 3,
            'totalIndexSize': 4096
        })
        mock_motor_client.__getitem__.return_value = mock_db

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)

            stats = await client.get_collection_stats('users')

            assert stats['count'] == 100
            assert stats['indexes'] == 3

    async def test_count_documents(self, connection_config, mock_motor_client):
        """Test document counting"""
        client = MongoDBClient()

        mock_collection = AsyncMock()
        mock_collection.count_documents = AsyncMock(return_value=42)

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_motor_client.__getitem__.return_value = mock_db

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)

            count = await client.count_documents('users', {'age': {'$gte': 18}})

            assert count == 42

    async def test_invalid_operation(self, connection_config, mock_motor_client):
        """Test invalid operation"""
        client = MongoDBClient()

        mock_db = MagicMock()
        mock_motor_client.__getitem__.return_value = mock_db

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)

            query = {
                'operation': 'invalid_op',
                'collection': 'users'
            }

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_query(str(query).replace("'", '"'))

            assert "Unsupported operation" in str(exc_info.value)

    async def test_health_check(self, connection_config, mock_motor_client):
        """Test health check"""
        client = MongoDBClient()

        mock_collection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_collection.find = Mock(return_value=mock_cursor)

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_motor_client.__getitem__.return_value = mock_db

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_motor_client):
            await client.connect(connection_config)

            health = await client.health_check()

            assert health['connected'] is True
            assert health['state'] == 'connected'
