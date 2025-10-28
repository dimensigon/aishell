"""MongoDB integration tests with real Docker container."""
import asyncio
import pytest
from datetime import datetime
from tests.integration.mcp.config import DOCKER_CONFIGS


class TestMongoDBConnection:
    """Test MongoDB connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mongo_client, mongodb_clean):
        """Test successful connection to MongoDB."""
        config = DOCKER_CONFIGS['mongodb']

        await mongo_client.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            username=config['username'],
            password=config['password']
        )

        assert mongo_client.is_connected()

    @pytest.mark.asyncio
    async def test_connect_invalid_credentials(self, mongo_client):
        """Test connection with invalid credentials."""
        config = DOCKER_CONFIGS['mongodb']

        with pytest.raises(Exception):
            await mongo_client.connect(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                username='invalid',
                password='wrong'
            )

    @pytest.mark.asyncio
    async def test_disconnect(self, mongo_client, mongodb_clean):
        """Test disconnection from MongoDB."""
        config = DOCKER_CONFIGS['mongodb']

        await mongo_client.connect(**config)
        assert mongo_client.is_connected()

        await mongo_client.disconnect()
        assert not mongo_client.is_connected()

    @pytest.mark.asyncio
    async def test_reconnect(self, mongo_client, mongodb_clean):
        """Test reconnection after disconnect."""
        config = DOCKER_CONFIGS['mongodb']

        await mongo_client.connect(**config)
        await mongo_client.disconnect()
        await mongo_client.connect(**config)

        assert mongo_client.is_connected()

    @pytest.mark.asyncio
    async def test_connection_uri_format(self, mongo_client, mongodb_clean):
        """Test connection with URI format."""
        config = DOCKER_CONFIGS['mongodb']
        uri = f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?authSource=admin"

        await mongo_client.connect(uri=uri)

        assert mongo_client.is_connected()


class TestMongoDBCRUD:
    """Test MongoDB CRUD operations."""

    @pytest.mark.asyncio
    async def test_insert_one_document(self, mongo_client, mongodb_clean):
        """Test inserting a single document."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        result = await mongo_client.insert_one(
            collection='users',
            document={'name': 'John Doe', 'email': 'john@example.com', 'age': 30}
        )

        assert result['inserted_id'] is not None

    @pytest.mark.asyncio
    async def test_insert_many_documents(self, mongo_client, mongodb_clean):
        """Test inserting multiple documents."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        documents = [
            {'name': f'User{i}', 'email': f'user{i}@example.com', 'age': 20 + i}
            for i in range(10)
        ]

        result = await mongo_client.insert_many(
            collection='users',
            documents=documents
        )

        assert len(result['inserted_ids']) == 10

    @pytest.mark.asyncio
    async def test_find_one_document(self, mongo_client, mongodb_clean):
        """Test finding a single document."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert test data
        await mongo_client.insert_one(
            collection='users',
            document={'name': 'Jane Smith', 'email': 'jane@example.com', 'age': 25}
        )

        # Find
        result = await mongo_client.find_one(
            collection='users',
            filter={'email': 'jane@example.com'}
        )

        assert result['name'] == 'Jane Smith'
        assert result['age'] == 25

    @pytest.mark.asyncio
    async def test_find_many_documents(self, mongo_client, mongodb_clean):
        """Test finding multiple documents."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert test data
        for i in range(5):
            await mongo_client.insert_one(
                collection='users',
                document={'name': f'User{i}', 'category': 'test', 'age': 20 + i}
            )

        # Find all
        results = await mongo_client.find(
            collection='users',
            filter={'category': 'test'}
        )

        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_update_one_document(self, mongo_client, mongodb_clean):
        """Test updating a single document."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert
        result = await mongo_client.insert_one(
            collection='users',
            document={'name': 'Bob', 'email': 'bob@example.com', 'age': 30}
        )
        doc_id = result['inserted_id']

        # Update
        update_result = await mongo_client.update_one(
            collection='users',
            filter={'_id': doc_id},
            update={'$set': {'age': 31, 'updated': True}}
        )

        assert update_result['modified_count'] == 1

        # Verify
        doc = await mongo_client.find_one(
            collection='users',
            filter={'_id': doc_id}
        )
        assert doc['age'] == 31
        assert doc['updated'] is True

    @pytest.mark.asyncio
    async def test_update_many_documents(self, mongo_client, mongodb_clean):
        """Test updating multiple documents."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert test data
        for i in range(5):
            await mongo_client.insert_one(
                collection='users',
                document={'name': f'User{i}', 'category': 'bulk', 'status': 'active'}
            )

        # Update all
        result = await mongo_client.update_many(
            collection='users',
            filter={'category': 'bulk'},
            update={'$set': {'status': 'inactive'}}
        )

        assert result['modified_count'] == 5

    @pytest.mark.asyncio
    async def test_delete_one_document(self, mongo_client, mongodb_clean):
        """Test deleting a single document."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert
        result = await mongo_client.insert_one(
            collection='users',
            document={'name': 'Alice', 'email': 'alice@example.com'}
        )
        doc_id = result['inserted_id']

        # Delete
        delete_result = await mongo_client.delete_one(
            collection='users',
            filter={'_id': doc_id}
        )

        assert delete_result['deleted_count'] == 1

        # Verify
        doc = await mongo_client.find_one(
            collection='users',
            filter={'_id': doc_id}
        )
        assert doc is None

    @pytest.mark.asyncio
    async def test_delete_many_documents(self, mongo_client, mongodb_clean):
        """Test deleting multiple documents."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert test data
        for i in range(5):
            await mongo_client.insert_one(
                collection='users',
                document={'name': f'DeleteUser{i}', 'to_delete': True}
            )

        # Delete all
        result = await mongo_client.delete_many(
            collection='users',
            filter={'to_delete': True}
        )

        assert result['deleted_count'] == 5


class TestMongoDBQueryOperators:
    """Test MongoDB query operators."""

    @pytest.mark.asyncio
    async def test_comparison_operators(self, mongo_client, mongodb_clean):
        """Test comparison operators ($gt, $gte, $lt, $lte)."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert test data
        for i in range(10):
            await mongo_client.insert_one(
                collection='products',
                document={'name': f'Product{i}', 'price': 10 + i}
            )

        # Query with $gt
        results = await mongo_client.find(
            collection='products',
            filter={'price': {'$gt': 15}}
        )

        assert len(results) == 4  # Products with price > 15

    @pytest.mark.asyncio
    async def test_logical_operators(self, mongo_client, mongodb_clean):
        """Test logical operators ($and, $or, $not)."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert test data
        await mongo_client.insert_one(
            collection='users',
            document={'name': 'John', 'age': 30, 'active': True}
        )
        await mongo_client.insert_one(
            collection='users',
            document={'name': 'Jane', 'age': 25, 'active': False}
        )

        # Query with $or
        results = await mongo_client.find(
            collection='users',
            filter={'$or': [{'age': {'$gt': 28}}, {'active': False}]}
        )

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_array_operators(self, mongo_client, mongodb_clean):
        """Test array operators ($in, $all, $elemMatch)."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert test data
        await mongo_client.insert_one(
            collection='users',
            document={'name': 'User1', 'tags': ['python', 'mongodb', 'async']}
        )

        # Query with $in
        results = await mongo_client.find(
            collection='users',
            filter={'tags': {'$in': ['python']}}
        )

        assert len(results) == 1


class TestMongoDBIndexing:
    """Test MongoDB indexing operations."""

    @pytest.mark.asyncio
    async def test_create_index(self, mongo_client, mongodb_clean):
        """Test creating an index."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Create index
        result = await mongo_client.create_index(
            collection='users',
            keys=[('email', 1)],
            unique=True
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_create_compound_index(self, mongo_client, mongodb_clean):
        """Test creating a compound index."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Create compound index
        result = await mongo_client.create_index(
            collection='users',
            keys=[('name', 1), ('age', -1)]
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_list_indexes(self, mongo_client, mongodb_clean):
        """Test listing indexes."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Create index
        await mongo_client.create_index(
            collection='users',
            keys=[('email', 1)]
        )

        # List indexes
        indexes = await mongo_client.list_indexes(collection='users')

        assert len(indexes) >= 2  # _id index + email index

    @pytest.mark.asyncio
    async def test_drop_index(self, mongo_client, mongodb_clean):
        """Test dropping an index."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Create index
        await mongo_client.create_index(
            collection='users',
            keys=[('email', 1)],
            name='email_idx'
        )

        # Drop index
        await mongo_client.drop_index(
            collection='users',
            name='email_idx'
        )

        # Verify
        indexes = await mongo_client.list_indexes(collection='users')
        index_names = [idx['name'] for idx in indexes]
        assert 'email_idx' not in index_names


class TestMongoDBAggregation:
    """Test MongoDB aggregation pipeline."""

    @pytest.mark.asyncio
    async def test_simple_aggregation(self, mongo_client, mongodb_clean):
        """Test simple aggregation pipeline."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert test data
        for i in range(10):
            await mongo_client.insert_one(
                collection='orders',
                document={'product': f'Product{i % 3}', 'amount': 10 + i, 'quantity': 1 + i}
            )

        # Aggregate
        pipeline = [
            {'$group': {
                '_id': '$product',
                'total_amount': {'$sum': '$amount'},
                'total_quantity': {'$sum': '$quantity'}
            }}
        ]

        results = await mongo_client.aggregate(
            collection='orders',
            pipeline=pipeline
        )

        assert len(results) == 3  # 3 unique products

    @pytest.mark.asyncio
    async def test_aggregation_with_match_sort(self, mongo_client, mongodb_clean):
        """Test aggregation with $match and $sort stages."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert test data
        for i in range(10):
            await mongo_client.insert_one(
                collection='users',
                document={'name': f'User{i}', 'age': 20 + i, 'score': 100 - i * 5}
            )

        # Aggregate
        pipeline = [
            {'$match': {'age': {'$gte': 25}}},
            {'$sort': {'score': -1}},
            {'$limit': 3}
        ]

        results = await mongo_client.aggregate(
            collection='users',
            pipeline=pipeline
        )

        assert len(results) == 3
        # Verify sorting
        assert results[0]['score'] >= results[1]['score']

    @pytest.mark.asyncio
    async def test_aggregation_with_lookup(self, mongo_client, mongodb_clean):
        """Test aggregation with $lookup (join)."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert users
        user_result = await mongo_client.insert_one(
            collection='users',
            document={'name': 'John', 'user_id': 1}
        )

        # Insert orders
        await mongo_client.insert_one(
            collection='orders',
            document={'order_id': 1, 'user_id': 1, 'amount': 100}
        )

        # Aggregate with lookup
        pipeline = [
            {'$lookup': {
                'from': 'orders',
                'localField': 'user_id',
                'foreignField': 'user_id',
                'as': 'user_orders'
            }}
        ]

        results = await mongo_client.aggregate(
            collection='users',
            pipeline=pipeline
        )

        assert len(results) >= 1
        assert 'user_orders' in results[0]
        assert len(results[0]['user_orders']) >= 1


class TestMongoDBTransactions:
    """Test MongoDB transactions (requires replica set)."""

    @pytest.mark.asyncio
    async def test_transaction_commit(self, mongo_client, mongodb_clean):
        """Test transaction commit."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Start transaction
        session = await mongo_client.start_session()

        try:
            await session.start_transaction()

            # Insert documents in transaction
            await mongo_client.insert_one(
                collection='users',
                document={'name': 'TX User', 'email': 'tx@example.com'},
                session=session
            )

            # Commit
            await session.commit_transaction()

            # Verify
            doc = await mongo_client.find_one(
                collection='users',
                filter={'email': 'tx@example.com'}
            )
            assert doc is not None

        finally:
            await session.end_session()

    @pytest.mark.asyncio
    async def test_transaction_abort(self, mongo_client, mongodb_clean):
        """Test transaction abort."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        session = await mongo_client.start_session()

        try:
            await session.start_transaction()

            # Insert documents in transaction
            await mongo_client.insert_one(
                collection='users',
                document={'name': 'Abort User', 'email': 'abort@example.com'},
                session=session
            )

            # Abort
            await session.abort_transaction()

            # Verify (should not exist)
            doc = await mongo_client.find_one(
                collection='users',
                filter={'email': 'abort@example.com'}
            )
            assert doc is None

        finally:
            await session.end_session()


class TestMongoDBChangeStreams:
    """Test MongoDB change streams."""

    @pytest.mark.asyncio
    async def test_watch_collection_changes(self, mongo_client, mongodb_clean):
        """Test watching collection changes."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        changes = []

        async def watch_changes():
            async with mongo_client.watch(collection='users') as stream:
                async for change in stream:
                    changes.append(change)
                    break  # Exit after first change

        async def make_change():
            await asyncio.sleep(0.1)
            await mongo_client.insert_one(
                collection='users',
                document={'name': 'Change User', 'email': 'change@example.com'}
            )

        await asyncio.gather(watch_changes(), make_change())

        assert len(changes) == 1
        assert changes[0]['operationType'] == 'insert'


class TestMongoDBGridFS:
    """Test MongoDB GridFS for file operations."""

    @pytest.mark.asyncio
    async def test_upload_file(self, mongo_client, mongodb_clean, tmp_path):
        """Test uploading file to GridFS."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test file content")

        # Upload
        file_id = await mongo_client.gridfs_upload(
            filename='test.txt',
            file_path=str(test_file)
        )

        assert file_id is not None

    @pytest.mark.asyncio
    async def test_download_file(self, mongo_client, mongodb_clean, tmp_path):
        """Test downloading file from GridFS."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Create and upload test file
        upload_file = tmp_path / "upload.txt"
        upload_file.write_text("Download test content")

        file_id = await mongo_client.gridfs_upload(
            filename='download.txt',
            file_path=str(upload_file)
        )

        # Download
        download_file = tmp_path / "download.txt"
        await mongo_client.gridfs_download(
            file_id=file_id,
            destination=str(download_file)
        )

        assert download_file.exists()
        assert download_file.read_text() == "Download test content"

    @pytest.mark.asyncio
    async def test_delete_file(self, mongo_client, mongodb_clean, tmp_path):
        """Test deleting file from GridFS."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Upload test file
        test_file = tmp_path / "delete_test.txt"
        test_file.write_text("Delete test")

        file_id = await mongo_client.gridfs_upload(
            filename='delete_test.txt',
            file_path=str(test_file)
        )

        # Delete
        await mongo_client.gridfs_delete(file_id=file_id)

        # Verify
        with pytest.raises(Exception):
            await mongo_client.gridfs_download(
                file_id=file_id,
                destination=str(tmp_path / "should_not_exist.txt")
            )


class TestMongoDBHealthCheck:
    """Test MongoDB health checks."""

    @pytest.mark.asyncio
    async def test_health_check_connected(self, mongo_client, mongodb_clean):
        """Test health check when connected."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        health = await mongo_client.health_check()

        assert health['healthy'] is True
        assert 'mongodb' in health['database_type'].lower()
        assert health['connected'] is True

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, mongo_client):
        """Test health check when disconnected."""
        health = await mongo_client.health_check()

        assert health['healthy'] is False
        assert health['connected'] is False

    @pytest.mark.asyncio
    async def test_health_check_with_metrics(self, mongo_client, mongodb_clean):
        """Test health check with database metrics."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        health = await mongo_client.health_check(include_metrics=True)

        assert 'metrics' in health
        assert 'collections_count' in health['metrics'] or 'database_size' in health['metrics']


class TestMongoDBErrorHandling:
    """Test MongoDB error handling."""

    @pytest.mark.asyncio
    async def test_duplicate_key_error(self, mongo_client, mongodb_clean):
        """Test handling duplicate key errors."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Create unique index
        await mongo_client.create_index(
            collection='users',
            keys=[('email', 1)],
            unique=True
        )

        # Insert document
        await mongo_client.insert_one(
            collection='users',
            document={'name': 'User', 'email': 'unique@example.com'}
        )

        # Try to insert duplicate
        with pytest.raises(Exception) as exc_info:
            await mongo_client.insert_one(
                collection='users',
                document={'name': 'Another User', 'email': 'unique@example.com'}
            )

        assert 'duplicate' in str(exc_info.value).lower() or 'unique' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_invalid_query_error(self, mongo_client, mongodb_clean):
        """Test handling invalid query errors."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        with pytest.raises(Exception):
            await mongo_client.find(
                collection='users',
                filter={'$invalidOperator': 'value'}
            )

    @pytest.mark.asyncio
    async def test_connection_timeout(self, mongo_client):
        """Test connection timeout handling."""
        with pytest.raises(Exception):
            await mongo_client.connect(
                host='192.0.2.1',  # Non-routable IP
                port=27017,
                timeout=1
            )
