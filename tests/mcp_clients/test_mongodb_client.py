"""
Comprehensive Unit Tests for MongoDB MCP Client

Tests MongoDB client implementation including connection management,
document operations, aggregation pipelines, index management, and error handling.
"""

import pytest
import asyncio
import json
import sys
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from typing import Any, Dict, List


# Mock all pymongo and motor dependencies before any imports
class MockObjectId:
    """Mock ObjectId class"""
    def __init__(self, val='507f1f77bcf86cd799439011'):
        self._id = val

    def __str__(self):
        return str(self._id)

    def __repr__(self):
        return f"ObjectId('{self._id}')"


class MockPyMongoError(Exception):
    """Mock PyMongoError"""
    pass


class MockConnectionFailure(Exception):
    """Mock ConnectionFailure"""
    pass


# Create complete mock modules
mock_bson = MagicMock()
mock_bson.ObjectId = MockObjectId

mock_pymongo_errors = MagicMock()
mock_pymongo_errors.PyMongoError = MockPyMongoError
mock_pymongo_errors.ConnectionFailure = MockConnectionFailure

mock_motor = MagicMock()
mock_motor.AsyncIOMotorClient = MagicMock
mock_motor.AsyncIOMotorDatabase = MagicMock
mock_motor.AsyncIOMotorCollection = MagicMock

# Install mocks into sys.modules
sys.modules['bson'] = mock_bson
sys.modules['pymongo'] = MagicMock()
sys.modules['pymongo.errors'] = mock_pymongo_errors
sys.modules['motor'] = MagicMock()
sys.modules['motor.motor_asyncio'] = mock_motor

# Now safe to import
from src.mcp_clients.base import (
    MCPClientError,
    ConnectionState,
    ConnectionConfig,
    QueryResult
)


# Test Fixtures

@pytest.fixture
def mongodb_config():
    """MongoDB connection configuration"""
    return ConnectionConfig(
        host='localhost',
        port=27017,
        database='testdb',
        username='testuser',
        password='testpass',
        extra_params={'authSource': 'admin'}
    )


@pytest.fixture
def mongodb_config_no_auth():
    """MongoDB connection configuration without authentication"""
    return ConnectionConfig(
        host='localhost',
        port=27017,
        database='testdb',
        username='',
        password='',
        extra_params=None
    )


@pytest.fixture
def mock_mongodb_client():
    """Mock MongoDB motor client"""
    # Create a proper mock that has all attributes as real Mock objects
    client = MagicMock()
    database = MagicMock()
    collection = MagicMock()

    # Mock ping command - ensure admin exists before setting command
    admin = MagicMock()
    admin.command = AsyncMock(return_value={'ok': 1})
    client.admin = admin

    # Mock database access
    def getitem_db(key):
        return database

    def getitem_collection(key):
        return collection

    client.__getitem__ = Mock(side_effect=getitem_db)
    database.__getitem__ = Mock(side_effect=getitem_collection)

    # Mock collection operations
    collection.find = Mock()
    collection.insert_one = AsyncMock()
    collection.insert_many = AsyncMock()
    collection.update_one = AsyncMock()
    collection.update_many = AsyncMock()
    collection.delete_one = AsyncMock()
    collection.delete_many = AsyncMock()
    collection.aggregate = Mock()
    collection.create_index = AsyncMock()
    collection.drop_index = AsyncMock()
    collection.create_indexes = AsyncMock()
    collection.drop = AsyncMock()
    collection.list_indexes = Mock()

    # Mock database operations
    database.list_collection_names = AsyncMock(return_value=[])
    database.command = AsyncMock(return_value={})

    client.close = Mock()

    return client


@pytest.fixture
def mock_cursor():
    """Mock MongoDB cursor"""
    cursor = AsyncMock()
    cursor.skip = Mock(return_value=cursor)
    cursor.limit = Mock(return_value=cursor)
    cursor.sort = Mock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=[
        {'_id': MockObjectId('507f1f77bcf86cd799439011'), 'name': 'test1', 'email': 'test1@example.com'},
        {'_id': MockObjectId('507f1f77bcf86cd799439012'), 'name': 'test2', 'email': 'test2@example.com'}
    ])
    return cursor


@pytest.fixture
def sample_documents():
    """Sample MongoDB documents"""
    return [
        {'_id': MockObjectId(), 'name': 'test1', 'email': 'test1@example.com', 'age': 25},
        {'_id': MockObjectId(), 'name': 'test2', 'email': 'test2@example.com', 'age': 30},
        {'_id': MockObjectId(), 'name': 'test3', 'email': 'test3@example.com', 'age': 35}
    ]


# Import MongoDB client after mocks are set up
with patch.dict('sys.modules', {
    'bson': mock_bson,
    'pymongo.errors': mock_pymongo_errors,
    'motor.motor_asyncio': mock_motor
}):
    from src.mcp_clients.mongodb_client import MongoDBClient


# Test MongoDB Protocol Compliance

class TestMongoDBProtocolCompliance:
    """Test MCP protocol compliance for MongoDB client"""

    @pytest.mark.asyncio
    async def test_client_has_state_property(self):
        """Test state property exists"""
        client = MongoDBClient()
        assert hasattr(client, 'state')
        assert isinstance(client.state, ConnectionState)
        assert client.state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_client_has_async_methods(self):
        """Test required async methods exist"""
        client = MongoDBClient()
        assert hasattr(client, 'connect')
        assert hasattr(client, 'disconnect')
        assert hasattr(client, 'execute_query')
        assert hasattr(client, 'health_check')

        assert asyncio.iscoroutinefunction(client.connect)
        assert asyncio.iscoroutinefunction(client.disconnect)
        assert asyncio.iscoroutinefunction(client.execute_query)
        assert asyncio.iscoroutinefunction(client.health_check)

    @pytest.mark.asyncio
    async def test_client_has_mongodb_specific_methods(self):
        """Test MongoDB-specific methods exist"""
        client = MongoDBClient()
        assert hasattr(client, 'get_collections')
        assert hasattr(client, 'get_collection_stats')
        assert hasattr(client, 'list_indexes')
        assert hasattr(client, 'create_index')
        assert hasattr(client, 'drop_index')


# Test Connection Management

class TestMongoDBConnection:
    """Test MongoDB connection management"""

    @pytest.mark.asyncio
    async def test_connect_success_with_auth(self, mongodb_config, mock_mongodb_client):
        """Test successful MongoDB connection with authentication"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            result = await client.connect(mongodb_config)

            assert result is True
            assert client.state == ConnectionState.CONNECTED
            assert client.is_connected is True
            assert client._client is not None
            assert client._database is not None

    @pytest.mark.asyncio
    async def test_connect_success_no_auth(self, mongodb_config_no_auth, mock_mongodb_client):
        """Test successful MongoDB connection without authentication"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            result = await client.connect(mongodb_config_no_auth)

            assert result is True
            assert client.state == ConnectionState.CONNECTED

    @pytest.mark.asyncio
    async def test_connect_with_extra_params(self, mongodb_config, mock_mongodb_client):
        """Test connection with extra parameters"""
        client = MongoDBClient()
        mongodb_config.extra_params = {'replicaSet': 'rs0', 'retryWrites': 'true'}

        with patch('motor.motor_asyncio.AsyncIOMotorClient', return_value=mock_mongodb_client) as mock_motor:
            await client.connect(mongodb_config)

            # Verify URI includes extra params
            call_args = mock_motor.call_args[0][0]
            assert 'replicaSet=rs0' in call_args
            assert 'retryWrites=true' in call_args

    @pytest.mark.asyncio
    async def test_connect_failure(self, mongodb_config):
        """Test MongoDB connection failure handling"""
        client = MongoDBClient()

        mock_client = AsyncMock()
        mock_client.admin.command = AsyncMock(side_effect=MockConnectionFailure("Connection refused"))

        with patch('motor.motor_asyncio.AsyncIOMotorClient', return_value=mock_client):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(mongodb_config)

            assert exc_info.value.error_code == "CONNECTION_FAILED"
            assert client.state == ConnectionState.ERROR
            assert "Connection refused" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_disconnect(self, mongodb_config, mock_mongodb_client):
        """Test MongoDB disconnect"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)
            result = await client.disconnect()

            assert result is True
            assert client.state == ConnectionState.CLOSED
            assert client._client is None
            assert client._database is None
            mock_mongodb_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self):
        """Test disconnect when not connected"""
        client = MongoDBClient()
        result = await client.disconnect()

        assert result is True
        assert client.state == ConnectionState.CLOSED

    @pytest.mark.asyncio
    async def test_is_connected_property(self, mongodb_config, mock_mongodb_client):
        """Test is_connected property"""
        client = MongoDBClient()

        assert client.is_connected is False

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)
            assert client.is_connected is True

            await client.disconnect()
            assert client.is_connected is False


# Test Document Operations - Find

class TestMongoDBFind:
    """Test MongoDB find operations"""

    @pytest.mark.asyncio
    async def test_find_all_documents(self, mongodb_config, mock_mongodb_client, mock_cursor):
        """Test finding all documents"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.find = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'find',
                'collection': 'users',
                'filter': {}
            })

            result = await client.execute_query(query)

            assert result.columns == ['_id', 'name', 'email']
            assert result.rowcount == 2
            assert len(result.rows) == 2
            assert result.metadata['collection'] == 'users'
            assert result.metadata['operation'] == 'find'

    @pytest.mark.asyncio
    async def test_find_with_filter(self, mongodb_config, mock_mongodb_client, mock_cursor):
        """Test finding documents with filter"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.find = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'find',
                'collection': 'users',
                'filter': {'name': 'test1'}
            })

            result = await client.execute_query(query)

            collection.find.assert_called_once()
            assert result.rowcount == 2

    @pytest.mark.asyncio
    async def test_find_with_projection(self, mongodb_config, mock_mongodb_client, mock_cursor):
        """Test finding documents with projection"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.find = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'find',
                'collection': 'users',
                'filter': {},
                'projection': {'name': 1, 'email': 1}
            })

            result = await client.execute_query(query)

            call_args = collection.find.call_args
            assert call_args[0][0] == {}
            assert call_args[0][1] == {'name': 1, 'email': 1}

    @pytest.mark.asyncio
    async def test_find_with_limit_and_skip(self, mongodb_config, mock_mongodb_client, mock_cursor):
        """Test finding documents with limit and skip"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.find = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'find',
                'collection': 'users',
                'filter': {},
                'limit': 10,
                'skip': 5
            })

            result = await client.execute_query(query)

            mock_cursor.limit.assert_called_once_with(10)
            mock_cursor.skip.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_find_with_sort(self, mongodb_config, mock_mongodb_client, mock_cursor):
        """Test finding documents with sort"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.find = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'find',
                'collection': 'users',
                'filter': {},
                'sort': [('name', 1)]
            })

            result = await client.execute_query(query)

            mock_cursor.sort.assert_called_once_with([('name', 1)])

    @pytest.mark.asyncio
    async def test_find_empty_result(self, mongodb_config, mock_mongodb_client):
        """Test finding with no results"""
        client = MongoDBClient()

        empty_cursor = AsyncMock()
        empty_cursor.skip = Mock(return_value=empty_cursor)
        empty_cursor.limit = Mock(return_value=empty_cursor)
        empty_cursor.sort = Mock(return_value=empty_cursor)
        empty_cursor.to_list = AsyncMock(return_value=[])

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.find = Mock(return_value=empty_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'find',
                'collection': 'users',
                'filter': {'name': 'nonexistent'}
            })

            result = await client.execute_query(query)

            assert result.rowcount == 0
            assert len(result.rows) == 0
            assert result.columns == []


# Test Document Operations - Insert

class TestMongoDBInsert:
    """Test MongoDB insert operations"""

    @pytest.mark.asyncio
    async def test_insert_one(self, mongodb_config, mock_mongodb_client):
        """Test inserting one document"""
        client = MongoDBClient()

        mock_result = AsyncMock()
        mock_result.inserted_id = MockObjectId('507f1f77bcf86cd799439011')

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.insert_one = AsyncMock(return_value=mock_result)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'insert_one',
                'collection': 'users',
                'document': {'name': 'test', 'email': 'test@example.com'}
            })

            result = await client.execute_query(query)

            assert result.columns == ['inserted_id']
            assert result.rowcount == 1
            assert len(result.rows) == 1
            collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_many(self, mongodb_config, mock_mongodb_client):
        """Test inserting multiple documents"""
        client = MongoDBClient()

        mock_result = AsyncMock()
        mock_result.inserted_ids = [
            MockObjectId('507f1f77bcf86cd799439011'),
            MockObjectId('507f1f77bcf86cd799439012')
        ]

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.insert_many = AsyncMock(return_value=mock_result)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'insert_many',
                'collection': 'users',
                'documents': [
                    {'name': 'test1', 'email': 'test1@example.com'},
                    {'name': 'test2', 'email': 'test2@example.com'}
                ]
            })

            result = await client.execute_query(query)

            assert result.columns == ['inserted_count', 'inserted_ids']
            assert result.rowcount == 2
            collection.insert_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_many_empty_list(self, mongodb_config, mock_mongodb_client):
        """Test inserting empty list"""
        client = MongoDBClient()

        mock_result = AsyncMock()
        mock_result.inserted_ids = []

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.insert_many = AsyncMock(return_value=mock_result)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'insert_many',
                'collection': 'users',
                'documents': []
            })

            result = await client.execute_query(query)

            assert result.rowcount == 0


# Test Document Operations - Update

class TestMongoDBUpdate:
    """Test MongoDB update operations"""

    @pytest.mark.asyncio
    async def test_update_one(self, mongodb_config, mock_mongodb_client):
        """Test updating one document"""
        client = MongoDBClient()

        mock_result = AsyncMock()
        mock_result.matched_count = 1
        mock_result.modified_count = 1
        mock_result.upserted_id = None

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.update_one = AsyncMock(return_value=mock_result)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'update_one',
                'collection': 'users',
                'filter': {'name': 'test'},
                'update': {'$set': {'email': 'newemail@example.com'}}
            })

            result = await client.execute_query(query)

            assert result.columns == ['matched_count', 'modified_count', 'upserted_id']
            assert result.rowcount == 1
            assert result.rows[0][0] == 1  # matched_count
            assert result.rows[0][1] == 1  # modified_count
            collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_one_with_upsert(self, mongodb_config, mock_mongodb_client):
        """Test update with upsert"""
        client = MongoDBClient()

        mock_result = AsyncMock()
        mock_result.matched_count = 0
        mock_result.modified_count = 0
        mock_result.upserted_id = MockObjectId('507f1f77bcf86cd799439011')

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.update_one = AsyncMock(return_value=mock_result)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'update_one',
                'collection': 'users',
                'filter': {'name': 'nonexistent'},
                'update': {'$set': {'email': 'new@example.com'}},
                'upsert': True
            })

            result = await client.execute_query(query)

            assert result.rows[0][2] is not None  # upserted_id
            collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_many(self, mongodb_config, mock_mongodb_client):
        """Test updating multiple documents"""
        client = MongoDBClient()

        mock_result = AsyncMock()
        mock_result.matched_count = 5
        mock_result.modified_count = 5

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.update_many = AsyncMock(return_value=mock_result)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'update_many',
                'collection': 'users',
                'filter': {'active': True},
                'update': {'$set': {'status': 'verified'}}
            })

            result = await client.execute_query(query)

            assert result.columns == ['matched_count', 'modified_count']
            assert result.rowcount == 5
            assert result.rows[0][0] == 5
            collection.update_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_many_no_matches(self, mongodb_config, mock_mongodb_client):
        """Test update_many with no matching documents"""
        client = MongoDBClient()

        mock_result = AsyncMock()
        mock_result.matched_count = 0
        mock_result.modified_count = 0

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.update_many = AsyncMock(return_value=mock_result)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'update_many',
                'collection': 'users',
                'filter': {'name': 'nonexistent'},
                'update': {'$set': {'status': 'updated'}}
            })

            result = await client.execute_query(query)

            assert result.rowcount == 0


# Test Document Operations - Delete

class TestMongoDBDelete:
    """Test MongoDB delete operations"""

    @pytest.mark.asyncio
    async def test_delete_one(self, mongodb_config, mock_mongodb_client):
        """Test deleting one document"""
        client = MongoDBClient()

        mock_result = AsyncMock()
        mock_result.deleted_count = 1

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.delete_one = AsyncMock(return_value=mock_result)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'delete_one',
                'collection': 'users',
                'filter': {'name': 'test'}
            })

            result = await client.execute_query(query)

            assert result.columns == ['deleted_count']
            assert result.rowcount == 1
            assert result.rows[0][0] == 1
            collection.delete_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_one_no_match(self, mongodb_config, mock_mongodb_client):
        """Test delete_one with no matching document"""
        client = MongoDBClient()

        mock_result = AsyncMock()
        mock_result.deleted_count = 0

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.delete_one = AsyncMock(return_value=mock_result)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'delete_one',
                'collection': 'users',
                'filter': {'name': 'nonexistent'}
            })

            result = await client.execute_query(query)

            assert result.rowcount == 0

    @pytest.mark.asyncio
    async def test_delete_many(self, mongodb_config, mock_mongodb_client):
        """Test deleting multiple documents"""
        client = MongoDBClient()

        mock_result = AsyncMock()
        mock_result.deleted_count = 5

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.delete_many = AsyncMock(return_value=mock_result)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'delete_many',
                'collection': 'users',
                'filter': {'active': False}
            })

            result = await client.execute_query(query)

            assert result.columns == ['deleted_count']
            assert result.rowcount == 5
            assert result.rows[0][0] == 5
            collection.delete_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_many_all(self, mongodb_config, mock_mongodb_client):
        """Test deleting all documents"""
        client = MongoDBClient()

        mock_result = AsyncMock()
        mock_result.deleted_count = 100

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.delete_many = AsyncMock(return_value=mock_result)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'delete_many',
                'collection': 'users',
                'filter': {}
            })

            result = await client.execute_query(query)

            assert result.rowcount == 100


# Test Aggregation Pipeline

class TestMongoDBAggregate:
    """Test MongoDB aggregation operations"""

    @pytest.mark.asyncio
    async def test_aggregate_simple(self, mongodb_config, mock_mongodb_client):
        """Test simple aggregation pipeline"""
        client = MongoDBClient()

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {'_id': 'test', 'count': 10},
            {'_id': 'test2', 'count': 5}
        ])

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.aggregate = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'aggregate',
                'collection': 'users',
                'pipeline': [
                    {'$group': {'_id': '$name', 'count': {'$sum': 1}}}
                ]
            })

            result = await client.execute_query(query)

            assert result.columns == ['_id', 'count']
            assert result.rowcount == 2
            collection.aggregate.assert_called_once()

    @pytest.mark.asyncio
    async def test_aggregate_complex(self, mongodb_config, mock_mongodb_client):
        """Test complex aggregation pipeline"""
        client = MongoDBClient()

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {'_id': 'category1', 'total': 1000, 'avg': 250}
        ])

        collection = mock_mongodb_client[mongodb_config.database]['orders']
        collection.aggregate = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'aggregate',
                'collection': 'orders',
                'pipeline': [
                    {'$match': {'status': 'completed'}},
                    {'$group': {
                        '_id': '$category',
                        'total': {'$sum': '$amount'},
                        'avg': {'$avg': '$amount'}
                    }},
                    {'$sort': {'total': -1}}
                ]
            })

            result = await client.execute_query(query)

            assert result.rowcount == 1
            pipeline_arg = collection.aggregate.call_args[0][0]
            assert len(pipeline_arg) == 3
            assert '$match' in pipeline_arg[0]

    @pytest.mark.asyncio
    async def test_aggregate_empty_result(self, mongodb_config, mock_mongodb_client):
        """Test aggregation with empty result"""
        client = MongoDBClient()

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.aggregate = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'aggregate',
                'collection': 'users',
                'pipeline': [{'$match': {'name': 'nonexistent'}}]
            })

            result = await client.execute_query(query)

            assert result.rowcount == 0
            assert result.columns == []


# Test Index Management

class TestMongoDBIndexes:
    """Test MongoDB index management"""

    @pytest.mark.asyncio
    async def test_create_index_simple(self, mongodb_config, mock_mongodb_client):
        """Test creating simple index"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.create_index = AsyncMock(return_value='email_1')

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            index_name = await client.create_index('users', [('email', 1)])

            assert index_name == 'email_1'
            collection.create_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_index_with_options(self, mongodb_config, mock_mongodb_client):
        """Test creating index with options"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.create_index = AsyncMock(return_value='email_unique')

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            index_name = await client.create_index(
                'users',
                [('email', 1)],
                unique=True,
                sparse=True
            )

            assert index_name == 'email_unique'
            call_args = collection.create_index.call_args
            assert call_args[1]['unique'] is True
            assert call_args[1]['sparse'] is True

    @pytest.mark.asyncio
    async def test_create_compound_index(self, mongodb_config, mock_mongodb_client):
        """Test creating compound index"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.create_index = AsyncMock(return_value='name_1_email_1')

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            index_name = await client.create_index(
                'users',
                [('name', 1), ('email', 1)]
            )

            assert index_name == 'name_1_email_1'
            call_args = collection.create_index.call_args[0][0]
            assert call_args == [('name', 1), ('email', 1)]

    @pytest.mark.asyncio
    async def test_list_indexes(self, mongodb_config, mock_mongodb_client):
        """Test listing indexes"""
        client = MongoDBClient()

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {'name': '_id_', 'key': {'_id': 1}},
            {'name': 'email_1', 'key': {'email': 1}, 'unique': True}
        ])

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.list_indexes = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            indexes = await client.list_indexes('users')

            assert len(indexes) == 2
            assert indexes[0]['name'] == '_id_'
            assert indexes[1]['name'] == 'email_1'

    @pytest.mark.asyncio
    async def test_drop_index(self, mongodb_config, mock_mongodb_client):
        """Test dropping index"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.drop_index = AsyncMock()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            await client.drop_index('users', 'email_1')

            collection.drop_index.assert_called_once_with('email_1')

    @pytest.mark.asyncio
    async def test_create_index_via_ddl(self, mongodb_config, mock_mongodb_client):
        """Test creating index via DDL operation"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.create_index = AsyncMock(return_value='email_1')

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            ddl = json.dumps({
                'operation': 'create_index',
                'collection': 'users',
                'keys': [('email', 1)],
                'options': {'unique': True}
            })

            await client.execute_ddl(ddl)

            collection.create_index.assert_called_once()


# Test Collection Operations

class TestMongoDBCollections:
    """Test MongoDB collection operations"""

    @pytest.mark.asyncio
    async def test_get_collections(self, mongodb_config, mock_mongodb_client):
        """Test getting list of collections"""
        client = MongoDBClient()

        database = mock_mongodb_client[mongodb_config.database]
        database.list_collection_names = AsyncMock(return_value=['users', 'orders', 'products'])

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            collections = await client.get_collections()

            assert len(collections) == 3
            assert 'users' in collections
            assert 'orders' in collections
            assert 'products' in collections

    @pytest.mark.asyncio
    async def test_get_collections_empty(self, mongodb_config, mock_mongodb_client):
        """Test getting empty collection list"""
        client = MongoDBClient()

        database = mock_mongodb_client[mongodb_config.database]
        database.list_collection_names = AsyncMock(return_value=[])

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            collections = await client.get_collections()

            assert len(collections) == 0

    @pytest.mark.asyncio
    async def test_get_collection_stats(self, mongodb_config, mock_mongodb_client):
        """Test getting collection statistics"""
        client = MongoDBClient()

        database = mock_mongodb_client[mongodb_config.database]
        database.command = AsyncMock(return_value={
            'count': 1000,
            'size': 50000,
            'storageSize': 100000,
            'totalIndexSize': 10000,
            'nindexes': 3
        })

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            stats = await client.get_collection_stats('users')

            assert stats['name'] == 'users'
            assert stats['count'] == 1000
            assert stats['size'] == 50000
            assert 'indexes' in stats

    @pytest.mark.asyncio
    async def test_drop_collection_via_ddl(self, mongodb_config, mock_mongodb_client):
        """Test dropping collection via DDL"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.drop = AsyncMock()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            ddl = json.dumps({
                'operation': 'drop_collection',
                'collection': 'users'
            })

            await client.execute_ddl(ddl)

            collection.drop.assert_called_once()


# Test Error Handling

class TestMongoDBErrorHandling:
    """Test MongoDB error handling"""

    @pytest.mark.asyncio
    async def test_query_without_collection(self, mongodb_config, mock_mongodb_client):
        """Test query without collection name"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'find',
                'filter': {}
            })

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_query(query)

            assert exc_info.value.error_code == "INVALID_QUERY"
            assert "Collection name required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unsupported_operation(self, mongodb_config, mock_mongodb_client):
        """Test unsupported operation"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'invalid_operation',
                'collection': 'users'
            })

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_query(query)

            assert exc_info.value.error_code == "INVALID_OPERATION"

    @pytest.mark.asyncio
    async def test_invalid_json_query(self, mongodb_config, mock_mongodb_client):
        """Test invalid JSON query"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_query("invalid json {}")

            assert exc_info.value.error_code == "INVALID_QUERY"

    @pytest.mark.asyncio
    async def test_query_not_connected(self):
        """Test query execution when not connected"""
        client = MongoDBClient()

        query = json.dumps({
            'operation': 'find',
            'collection': 'users',
            'filter': {}
        })

        with pytest.raises(MCPClientError) as exc_info:
            await client.execute_query(query)

        assert exc_info.value.error_code == "NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_ddl_not_connected(self):
        """Test DDL execution when not connected"""
        client = MongoDBClient()

        ddl = json.dumps({
            'operation': 'create_index',
            'collection': 'users',
            'keys': [('email', 1)]
        })

        with pytest.raises(MCPClientError) as exc_info:
            await client.execute_ddl(ddl)

        assert exc_info.value.error_code == "NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_invalid_ddl_json(self, mongodb_config, mock_mongodb_client):
        """Test invalid DDL JSON"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_ddl("invalid json")

            assert exc_info.value.error_code == "INVALID_DDL"

    @pytest.mark.asyncio
    async def test_ddl_without_collection(self, mongodb_config, mock_mongodb_client):
        """Test DDL without collection name"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            ddl = json.dumps({
                'operation': 'create_index',
                'keys': [('email', 1)]
            })

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_ddl(ddl)

            assert exc_info.value.error_code == "INVALID_DDL"

    @pytest.mark.asyncio
    async def test_unsupported_ddl_operation(self, mongodb_config, mock_mongodb_client):
        """Test unsupported DDL operation"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            ddl = json.dumps({
                'operation': 'invalid_ddl',
                'collection': 'users'
            })

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_ddl(ddl)

            assert exc_info.value.error_code == "INVALID_DDL"

    @pytest.mark.asyncio
    async def test_pymongo_error_handling(self, mongodb_config, mock_mongodb_client):
        """Test PyMongo error handling"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(side_effect=MockPyMongoError("Database error"))
        collection.find = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'find',
                'collection': 'users',
                'filter': {}
            })

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_query(query)

            assert exc_info.value.error_code == "QUERY_FAILED"
            assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_collections_not_connected(self):
        """Test getting collections when not connected"""
        client = MongoDBClient()

        with pytest.raises(MCPClientError) as exc_info:
            await client.get_collections()

        assert exc_info.value.error_code == "NOT_CONNECTED"


# Test Health Check

class TestMongoDBHealthCheck:
    """Test MongoDB health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_connected(self, mongodb_config, mock_mongodb_client):
        """Test health check for connected client"""
        client = MongoDBClient()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)
            health = await client.health_check()

            assert health['state'] == 'connected'
            assert health['connected'] is True
            assert 'connection_time' in health
            assert health['ping_successful'] is True

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self):
        """Test health check for disconnected client"""
        client = MongoDBClient()
        health = await client.health_check()

        assert health['state'] == 'disconnected'
        assert health['connected'] is False
        assert health['connection_time'] is None

    @pytest.mark.asyncio
    async def test_health_check_error_state(self, mongodb_config):
        """Test health check for error state"""
        client = MongoDBClient()

        mock_client = AsyncMock()
        mock_client.admin.command = AsyncMock(side_effect=MockConnectionFailure("Connection failed"))

        with patch('motor.motor_asyncio.AsyncIOMotorClient', return_value=mock_client):
            try:
                await client.connect(mongodb_config)
            except MCPClientError:
                pass

            health = await client.health_check()

            assert health['state'] == 'error'
            assert health['connected'] is False


# Test ObjectId Handling

class TestMongoDBObjectIdHandling:
    """Test ObjectId conversion handling"""

    @pytest.mark.asyncio
    async def test_objectid_conversion_in_find(self, mongodb_config, mock_mongodb_client):
        """Test ObjectId is converted to string in find results"""
        client = MongoDBClient()

        mock_cursor = AsyncMock()
        mock_cursor.skip = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[
            {'_id': MockObjectId('507f1f77bcf86cd799439011'), 'name': 'test1'}
        ])

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.find = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'find',
                'collection': 'users',
                'filter': {}
            })

            result = await client.execute_query(query)

            # Check that _id is a string
            assert isinstance(result.rows[0][0], str)
            assert result.rows[0][0] == '507f1f77bcf86cd799439011'

    @pytest.mark.asyncio
    async def test_objectid_conversion_in_aggregate(self, mongodb_config, mock_mongodb_client):
        """Test ObjectId is converted to string in aggregation results"""
        client = MongoDBClient()

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {'_id': MockObjectId('507f1f77bcf86cd799439011'), 'count': 10}
        ])

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.aggregate = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'aggregate',
                'collection': 'users',
                'pipeline': [{'$group': {'_id': '$category', 'count': {'$sum': 1}}}]
            })

            result = await client.execute_query(query)

            # Check that _id is a string
            assert isinstance(result.rows[0][0], str)


# Test Concurrent Operations

class TestMongoDBConcurrent:
    """Test concurrent MongoDB operations"""

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, mongodb_config, mock_mongodb_client, mock_cursor):
        """Test concurrent query execution"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.find = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            # Execute multiple queries concurrently
            tasks = [
                client.execute_query(json.dumps({'operation': 'find', 'collection': 'users', 'filter': {}})),
                client.execute_query(json.dumps({'operation': 'find', 'collection': 'users', 'filter': {}})),
                client.execute_query(json.dumps({'operation': 'find', 'collection': 'users', 'filter': {}}))
            ]

            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            for result in results:
                assert result.rowcount == 2


# Test Edge Cases

class TestMongoDBEdgeCases:
    """Test MongoDB edge cases"""

    @pytest.mark.asyncio
    async def test_query_with_dict_instead_of_json(self, mongodb_config, mock_mongodb_client, mock_cursor):
        """Test query execution with dict instead of JSON string"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.find = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            # Pass dict directly instead of JSON string
            query_dict = {
                'operation': 'find',
                'collection': 'users',
                'filter': {}
            }

            result = await client.execute_query(query_dict)

            assert result.rowcount == 2

    @pytest.mark.asyncio
    async def test_ddl_with_dict_instead_of_json(self, mongodb_config, mock_mongodb_client):
        """Test DDL execution with dict instead of JSON string"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.drop = AsyncMock()

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            # Pass dict directly
            ddl_dict = {
                'operation': 'drop_collection',
                'collection': 'users'
            }

            await client.execute_ddl(ddl_dict)

            collection.drop.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_with_zero_limit(self, mongodb_config, mock_mongodb_client, mock_cursor):
        """Test find with limit=0 (no limit)"""
        client = MongoDBClient()

        collection = mock_mongodb_client[mongodb_config.database]['users']
        collection.find = Mock(return_value=mock_cursor)

        with patch('src.mcp_clients.mongodb_client.AsyncIOMotorClient', return_value=mock_mongodb_client):
            await client.connect(mongodb_config)

            query = json.dumps({
                'operation': 'find',
                'collection': 'users',
                'filter': {},
                'limit': 0
            })

            result = await client.execute_query(query)

            # Limit should not be called when limit is 0
            assert result.rowcount == 2
