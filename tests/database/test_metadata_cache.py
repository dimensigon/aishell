"""
Comprehensive tests for DatabaseMetadataCache with FAISS-based semantic search.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import asyncio

from src.database.metadata_cache import DatabaseMetadataCache, TableMetadata, ColumnMetadata


@pytest.fixture
def temp_cache_dir():
    """Create temporary directory for cache."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def cache(temp_cache_dir):
    """Create DatabaseMetadataCache instance."""
    return DatabaseMetadataCache(cache_dir=temp_cache_dir, dimension=384)


@pytest.fixture
def sample_metadata():
    """Sample database metadata for testing."""
    return {
        'tables': [
            {
                'name': 'users',
                'schema': 'public',
                'description': 'User accounts and authentication data',
                'columns': [
                    {
                        'name': 'id',
                        'type': 'integer',
                        'description': 'Primary key',
                        'nullable': False,
                        'is_primary_key': True
                    },
                    {
                        'name': 'email',
                        'type': 'varchar',
                        'description': 'User email address',
                        'nullable': False
                    },
                    {
                        'name': 'created_at',
                        'type': 'timestamp',
                        'description': 'Account creation timestamp',
                        'nullable': False
                    }
                ],
                'indexes': [
                    {'name': 'users_pkey', 'columns': ['id'], 'unique': True},
                    {'name': 'users_email_idx', 'columns': ['email'], 'unique': True}
                ],
                'foreign_keys': [],
                'constraints': [],
                'row_count': 1000,
                'size_bytes': 65536
            },
            {
                'name': 'posts',
                'schema': 'public',
                'description': 'Blog posts and articles',
                'columns': [
                    {
                        'name': 'id',
                        'type': 'integer',
                        'description': 'Primary key',
                        'nullable': False,
                        'is_primary_key': True
                    },
                    {
                        'name': 'user_id',
                        'type': 'integer',
                        'description': 'Author user ID',
                        'nullable': False,
                        'is_foreign_key': True,
                        'foreign_key_ref': 'users.id'
                    },
                    {
                        'name': 'title',
                        'type': 'varchar',
                        'description': 'Post title',
                        'nullable': False
                    },
                    {
                        'name': 'content',
                        'type': 'text',
                        'description': 'Post content body',
                        'nullable': True
                    },
                    {
                        'name': 'published_at',
                        'type': 'timestamp',
                        'description': 'Publication timestamp',
                        'nullable': True
                    }
                ],
                'indexes': [
                    {'name': 'posts_pkey', 'columns': ['id'], 'unique': True},
                    {'name': 'posts_user_id_idx', 'columns': ['user_id'], 'unique': False}
                ],
                'foreign_keys': [
                    {'columns': ['user_id'], 'references': 'users(id)'}
                ],
                'constraints': [],'row_count': 5000,
                'size_bytes': 524288
            },
            {
                'name': 'comments',
                'schema': 'public',
                'description': 'User comments on posts',
                'columns': [
                    {
                        'name': 'id',
                        'type': 'integer',
                        'description': 'Primary key',
                        'nullable': False,
                        'is_primary_key': True
                    },
                    {
                        'name': 'post_id',
                        'type': 'integer',
                        'description': 'Related post ID',
                        'nullable': False,
                        'is_foreign_key': True,
                        'foreign_key_ref': 'posts.id'
                    },
                    {
                        'name': 'user_id',
                        'type': 'integer',
                        'description': 'Comment author user ID',
                        'nullable': False,
                        'is_foreign_key': True,
                        'foreign_key_ref': 'users.id'
                    },
                    {
                        'name': 'text',
                        'type': 'text',
                        'description': 'Comment text',
                        'nullable': False
                    },
                    {
                        'name': 'created_at',
                        'type': 'timestamp',
                        'description': 'Comment creation time',
                        'nullable': False
                    }
                ],
                'indexes': [
                    {'name': 'comments_pkey', 'columns': ['id'], 'unique': True},
                    {'name': 'comments_post_id_idx', 'columns': ['post_id'], 'unique': False}
                ],
                'foreign_keys': [
                    {'columns': ['post_id'], 'references': 'posts(id)'},
                    {'columns': ['user_id'], 'references': 'users(id)'}
                ],
                'constraints': []
            }
        ]
    }


class TestDatabaseMetadataCacheBasics:
    """Test basic functionality of DatabaseMetadataCache."""

    def test_initialization(self, cache, temp_cache_dir):
        """Test cache initialization."""
        assert cache.dimension == 384
        assert cache.cache_dir == Path(temp_cache_dir)
        assert len(cache.tables) == 0
        assert len(cache.columns) == 0
        assert cache.vector_db is not None

    def test_cache_directory_creation(self):
        """Test that cache directory is created if it doesn't exist."""
        temp_dir = tempfile.mkdtemp()
        cache_path = Path(temp_dir) / "nonexistent" / "cache"

        cache = DatabaseMetadataCache(cache_dir=str(cache_path))

        assert cache_path.exists()
        assert cache_path.is_dir()

        # Cleanup
        shutil.rmtree(temp_dir)


class TestIndexing:
    """Test metadata indexing functionality."""

    @pytest.mark.asyncio
    async def test_index_database(self, cache, sample_metadata):
        """Test indexing database metadata."""
        connection_id = "test_db"

        await cache.index_database(connection_id, sample_metadata)

        # Verify tables were indexed
        assert len(cache.tables) == 3
        assert connection_id in cache.last_refresh

        # Verify columns were indexed
        # 3 columns in users + 5 in posts + 5 in comments = 13 total
        assert len(cache.columns) == 13

        # Verify vector database has entries
        stats = cache.vector_db.get_stats()
        assert stats['total_entries'] == 16  # 3 tables + 13 columns

    @pytest.mark.asyncio
    async def test_index_multiple_connections(self, cache, sample_metadata):
        """Test indexing metadata from multiple connections."""
        await cache.index_database("db1", sample_metadata)
        await cache.index_database("db2", sample_metadata)

        # Should have double the data
        assert len(cache.tables) == 6
        assert len(cache.columns) == 26
        assert len(cache.last_refresh) == 2

    @pytest.mark.asyncio
    async def test_index_empty_metadata(self, cache):
        """Test indexing empty metadata."""
        await cache.index_database("empty_db", {'tables': []})

        assert len(cache.tables) == 0
        assert len(cache.columns) == 0
        assert "empty_db" in cache.last_refresh


class TestSemanticSearch:
    """Test semantic search functionality."""

    @pytest.mark.asyncio
    async def test_search_tables_basic(self, cache, sample_metadata):
        """Test basic table search."""
        await cache.index_database("test_db", sample_metadata)

        # Search for user-related tables
        results = await cache.search_tables("user accounts", k=5)

        assert len(results) > 0
        # Should find 'users' table
        table_names = [r['name'] for r in results]
        assert 'users' in table_names

    @pytest.mark.asyncio
    async def test_search_tables_with_connection_filter(self, cache, sample_metadata):
        """Test table search with connection ID filter."""
        await cache.index_database("db1", sample_metadata)
        await cache.index_database("db2", sample_metadata)

        # Search only in db1
        results = await cache.search_tables("posts", connection_id="db1", k=5)

        # All results should be from db1
        for result in results:
            assert result['connection_id'] == "db1"

    @pytest.mark.asyncio
    async def test_search_tables_limit(self, cache, sample_metadata):
        """Test that k parameter limits results."""
        await cache.index_database("test_db", sample_metadata)

        results = await cache.search_tables("tables", k=2)

        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_search_columns_basic(self, cache, sample_metadata):
        """Test basic column search."""
        await cache.index_database("test_db", sample_metadata)

        # Search for timestamp columns
        results = await cache.search_columns("timestamp", k=5)

        assert len(results) > 0
        # Should find timestamp columns
        column_names = [r['name'] for r in results]
        assert any('created_at' in name or 'published_at' in name for name in column_names)

    @pytest.mark.asyncio
    async def test_search_columns_with_table_filter(self, cache, sample_metadata):
        """Test column search with table filter."""
        await cache.index_database("test_db", sample_metadata)

        # Search for columns only in 'users' table
        results = await cache.search_columns("columns", table="users", k=10)

        # All results should be from users table
        for result in results:
            assert result['table_name'] == "users"

    @pytest.mark.asyncio
    async def test_search_columns_by_type(self, cache, sample_metadata):
        """Test searching columns by data type."""
        await cache.index_database("test_db", sample_metadata)

        # Search for integer columns
        results = await cache.search_columns("integer primary key", k=5)

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_returns_similarity_scores(self, cache, sample_metadata):
        """Test that search results include similarity scores."""
        await cache.index_database("test_db", sample_metadata)

        results = await cache.search_tables("users", k=3)

        for result in results:
            assert 'similarity' in result
            assert 0.0 <= result['similarity'] <= 1.0


class TestSchemaRetrieval:
    """Test schema retrieval methods."""

    @pytest.mark.asyncio
    async def test_get_table_schema(self, cache, sample_metadata):
        """Test getting table schema by name."""
        await cache.index_database("test_db", sample_metadata)

        # Get users table schema
        schema = await cache.get_table_schema("users", connection_id="test_db")

        assert schema is not None
        assert schema['name'] == 'users'
        assert schema['schema'] == 'public'
        assert len(schema['columns']) == 3
        assert len(schema['indexes']) == 2

    @pytest.mark.asyncio
    async def test_get_table_schema_not_found(self, cache, sample_metadata):
        """Test getting non-existent table schema."""
        await cache.index_database("test_db", sample_metadata)

        schema = await cache.get_table_schema("nonexistent", connection_id="test_db")

        assert schema is None

    @pytest.mark.asyncio
    async def test_get_table_schema_without_connection_id(self, cache, sample_metadata):
        """Test getting table schema without connection ID filter."""
        await cache.index_database("test_db", sample_metadata)

        schema = await cache.get_table_schema("users")

        assert schema is not None
        assert schema['name'] == 'users'

    def test_get_table_direct(self, cache):
        """Test getting table metadata directly."""
        # Create test table
        table = TableMetadata(
            connection_id="test_db",
            schema="public",
            name="test_table",
            description="Test table"
        )
        key = cache._make_table_key("test_db", "public", "test_table")
        cache.tables[key] = table

        result = cache.get_table("test_db", "public", "test_table")

        assert result is not None
        assert result.name == "test_table"

    def test_get_column_direct(self, cache):
        """Test getting column metadata directly."""
        # Create test column
        column = ColumnMetadata(
            connection_id="test_db",
            schema="public",
            table_name="test_table",
            name="test_column",
            data_type="integer"
        )
        key = cache._make_column_key("test_db", "public", "test_table", "test_column")
        cache.columns[key] = column

        result = cache.get_column("test_db", "public", "test_table", "test_column")

        assert result is not None
        assert result.name == "test_column"
        assert result.data_type == "integer"


class TestStatistics:
    """Test statistics and monitoring."""

    @pytest.mark.asyncio
    async def test_get_database_stats(self, cache, sample_metadata):
        """Test getting database-specific statistics."""
        await cache.index_database("test_db", sample_metadata)

        stats = await cache.get_database_stats("test_db")

        assert stats['connection_id'] == "test_db"
        assert stats['total_tables'] == 3
        assert stats['total_columns'] == 13
        assert 'table_names' in stats
        assert len(stats['table_names']) == 3
        assert stats['last_refresh'] is not None

    @pytest.mark.asyncio
    async def test_get_database_stats_empty(self, cache):
        """Test getting stats for non-existent connection."""
        stats = await cache.get_database_stats("nonexistent")

        assert stats['total_tables'] == 0
        assert stats['total_columns'] == 0

    def test_get_overall_stats(self, cache):
        """Test getting overall cache statistics."""
        stats = cache.get_stats()

        assert 'total_tables' in stats
        assert 'total_columns' in stats
        assert 'connections_cached' in stats
        assert 'vector_db_stats' in stats


class TestCacheInvalidation:
    """Test cache invalidation and refresh."""

    @pytest.mark.asyncio
    async def test_invalidate_connection(self, cache, sample_metadata):
        """Test invalidating cache for a connection."""
        await cache.index_database("test_db", sample_metadata)

        # Verify data is there
        assert len(cache.tables) == 3

        # Invalidate
        await cache.invalidate_connection("test_db")

        # Verify data is gone
        assert len(cache.tables) == 0
        assert len(cache.columns) == 0
        assert "test_db" not in cache.last_refresh

    @pytest.mark.asyncio
    async def test_invalidate_one_of_many_connections(self, cache, sample_metadata):
        """Test invalidating one connection among many."""
        await cache.index_database("db1", sample_metadata)
        await cache.index_database("db2", sample_metadata)

        # Invalidate only db1
        await cache.invalidate_connection("db1")

        # db2 data should remain
        assert len(cache.tables) == 3
        assert "db2" in cache.last_refresh
        assert "db1" not in cache.last_refresh

    @pytest.mark.asyncio
    async def test_refresh_connection(self, cache, sample_metadata):
        """Test refreshing cache for a connection."""
        await cache.index_database("test_db", sample_metadata)

        original_refresh_time = cache.last_refresh["test_db"]

        # Wait a moment
        await asyncio.sleep(0.1)

        # Refresh with updated metadata
        updated_metadata = sample_metadata.copy()
        updated_metadata['tables'] = updated_metadata['tables'][:2]  # Only 2 tables now

        await cache.refresh_connection("test_db", updated_metadata)

        # Should have new data
        assert len(cache.tables) == 2
        assert cache.last_refresh["test_db"] > original_refresh_time

    def test_clear_all(self, cache):
        """Test clearing all cached data."""
        # Add some data
        table = TableMetadata(
            connection_id="test_db",
            schema="public",
            name="test_table",
            description="Test"
        )
        cache.tables["key"] = table

        cache.clear_all()

        assert len(cache.tables) == 0
        assert len(cache.columns) == 0
        assert len(cache.last_refresh) == 0


class TestPersistence:
    """Test cache persistence to disk."""

    @pytest.mark.asyncio
    async def test_save_to_disk(self, cache, sample_metadata, temp_cache_dir):
        """Test saving cache to disk."""
        await cache.index_database("test_db", sample_metadata)

        await cache.save_to_disk()

        # Check that files were created
        metadata_file = Path(temp_cache_dir) / 'metadata.json'
        vector_file = Path(temp_cache_dir) / 'vectors.pkl'

        assert metadata_file.exists()
        assert vector_file.exists()

    @pytest.mark.asyncio
    async def test_load_from_disk(self, cache, sample_metadata, temp_cache_dir):
        """Test loading cache from disk."""
        await cache.index_database("test_db", sample_metadata)
        await cache.save_to_disk()

        # Create new cache instance
        new_cache = DatabaseMetadataCache(cache_dir=temp_cache_dir)
        loaded = await new_cache.load_from_disk()

        assert loaded is True
        assert len(new_cache.tables) == 3
        assert len(new_cache.columns) == 13
        assert "test_db" in new_cache.last_refresh

    @pytest.mark.asyncio
    async def test_load_from_disk_no_cache(self, cache):
        """Test loading when no cache exists."""
        loaded = await cache.load_from_disk()

        assert loaded is False

    @pytest.mark.asyncio
    async def test_persistence_preserves_search_capability(self, cache, sample_metadata, temp_cache_dir):
        """Test that search works after loading from disk."""
        await cache.index_database("test_db", sample_metadata)
        await cache.save_to_disk()

        # Create new cache and load
        new_cache = DatabaseMetadataCache(cache_dir=temp_cache_dir)
        await new_cache.load_from_disk()

        # Search should work
        results = await new_cache.search_tables("users", k=5)

        assert len(results) > 0


class TestDataClasses:
    """Test TableMetadata and ColumnMetadata data classes."""

    def test_table_metadata_to_dict(self):
        """Test TableMetadata serialization."""
        table = TableMetadata(
            connection_id="test_db",
            schema="public",
            name="test_table",
            description="Test table",
            columns=[{'name': 'id', 'type': 'integer'}],
            indexes=[{'name': 'pkey', 'columns': ['id']}],
            foreign_keys=[],
            constraints=[],
            row_count=100,
            size_bytes=4096
        )

        data = table.to_dict()

        assert data['name'] == 'test_table'
        assert data['schema'] == 'public'
        assert len(data['columns']) == 1

    def test_table_metadata_from_dict(self):
        """Test TableMetadata deserialization."""
        data = {
            'connection_id': 'test_db',
            'schema': 'public',
            'name': 'test_table',
            'description': 'Test',
            'columns': [],
            'indexes': [],
            'foreign_keys': [],
            'constraints': [],
            'row_count': None,
            'size_bytes': None,
            'last_updated': None
        }

        table = TableMetadata.from_dict(data)

        assert table.name == 'test_table'
        assert table.schema == 'public'

    def test_column_metadata_to_dict(self):
        """Test ColumnMetadata serialization."""
        column = ColumnMetadata(
            connection_id="test_db",
            schema="public",
            table_name="test_table",
            name="test_column",
            data_type="varchar",
            nullable=False,
            is_primary_key=True
        )

        data = column.to_dict()

        assert data['name'] == 'test_column'
        assert data['data_type'] == 'varchar'
        assert data['is_primary_key'] is True

    def test_column_metadata_from_dict(self):
        """Test ColumnMetadata deserialization."""
        data = {
            'connection_id': 'test_db',
            'schema': 'public',
            'table_name': 'test_table',
            'name': 'test_column',
            'data_type': 'integer',
            'nullable': True,
            'default_value': None,
            'description': '',
            'is_primary_key': False,
            'is_foreign_key': False,
            'foreign_key_ref': None
        }

        column = ColumnMetadata.from_dict(data)

        assert column.name == 'test_column'
        assert column.data_type == 'integer'


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_search_empty_cache(self, cache):
        """Test searching in empty cache."""
        results = await cache.search_tables("users", k=5)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_index_malformed_metadata(self, cache):
        """Test indexing with missing required fields."""
        malformed = {
            'tables': [
                {'schema': 'public'},  # Missing 'name'
                {'name': 'valid_table', 'schema': 'public', 'columns': [
                    {'type': 'integer'}  # Missing 'name'
                ]}
            ]
        }

        # Should handle gracefully
        await cache.index_database("test_db", malformed)

        # Only valid table should be indexed
        assert len(cache.tables) == 1

    @pytest.mark.asyncio
    async def test_multiple_schemas(self, cache):
        """Test handling multiple schemas."""
        metadata = {
            'tables': [
                {'name': 'table1', 'schema': 'public', 'columns': []},
                {'name': 'table1', 'schema': 'private', 'columns': []}
            ]
        }

        await cache.index_database("test_db", metadata)

        # Should handle both tables with same name but different schemas
        assert len(cache.tables) == 2

    def test_hash_based_embedding_deterministic(self, cache):
        """Test that hash-based embeddings are deterministic."""
        text = "test table description"

        vec1 = cache._text_to_vector(text)
        vec2 = cache._text_to_vector(text)

        assert (vec1 == vec2).all()

    def test_hash_based_embedding_different_texts(self, cache):
        """Test that different texts produce different embeddings."""
        vec1 = cache._text_to_vector("table1")
        vec2 = cache._text_to_vector("table2")

        assert not (vec1 == vec2).all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
