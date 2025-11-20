"""
End-to-end integration tests for FAISS-based vector search and metadata caching.

Tests the complete workflow: database connection → metadata indexing → semantic search → usage in queries.
"""

import pytest
import asyncio
import numpy as np
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.database.metadata_cache import DatabaseMetadataCache
from src.vector.store import VectorDatabase


@pytest.fixture
def mock_database_connection():
    """Mock database connection."""
    conn = Mock()
    conn.connection_id = 'test_postgres'
    conn.get_tables = AsyncMock(return_value=[
        {
            'name': 'users',
            'schema': 'public',
            'description': 'User accounts',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Primary key'},
                {'name': 'email', 'type': 'varchar', 'description': 'Email address'},
                {'name': 'username', 'type': 'varchar', 'description': 'Username'},
            ]
        },
        {
            'name': 'orders',
            'schema': 'public',
            'description': 'Customer orders',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Order ID'},
                {'name': 'user_id', 'type': 'integer', 'description': 'User reference'},
                {'name': 'total', 'type': 'decimal', 'description': 'Order total'},
            ]
        },
        {
            'name': 'products',
            'schema': 'public',
            'description': 'Product catalog',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Product ID'},
                {'name': 'name', 'type': 'varchar', 'description': 'Product name'},
                {'name': 'price', 'type': 'decimal', 'description': 'Product price'},
            ]
        },
    ])
    return conn


@pytest.mark.asyncio
async def test_end_to_end_workflow(faiss_cache_dir, mock_database_connection):
    """Test complete workflow: connect → index → search → use results."""
    # Step 1: Create metadata cache
    cache = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)

    # Step 2: Connect to database and get metadata
    tables = await mock_database_connection.get_tables()
    metadata = {'tables': tables}

    # Step 3: Index metadata
    await cache.index_database(mock_database_connection.connection_id, metadata)

    # Step 4: Semantic search for tables
    search_results = await cache.search_tables(
        query='user accounts and authentication',
        connection_id=mock_database_connection.connection_id,
        limit=5,
        threshold=0.1
    )

    # Step 5: Use results (verify 'users' table found)
    assert len(search_results) > 0
    table_names = [r['name'] for r in search_results]
    assert 'users' in table_names

    # Step 6: Search for specific columns
    column_results = await cache.search_columns(
        query='email contact information',
        connection_id=mock_database_connection.connection_id,
        limit=5,
        threshold=0.1
    )

    # Step 7: Verify email column found
    assert len(column_results) > 0
    column_names = [r['name'] for r in column_results]
    assert 'email' in column_names


@pytest.mark.asyncio
async def test_cli_cache_management_workflow(faiss_cache_dir, mock_database_connection):
    """Test CLI commands for cache management."""
    cache = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)

    # Simulate: aishell cache index
    tables = await mock_database_connection.get_tables()
    await cache.index_database('test_conn', {'tables': tables})

    # Simulate: aishell cache stats
    stats = cache.get_stats()
    assert stats['total_tables'] > 0
    assert stats['total_columns'] > 0

    # Simulate: aishell cache save
    await cache.save_to_disk()

    # Simulate: aishell cache load (new instance)
    new_cache = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)
    loaded = await new_cache.load_from_disk()
    assert loaded is True

    # Simulate: aishell cache clear
    new_cache.clear_all()
    stats = new_cache.get_stats()
    assert stats['total_tables'] == 0


@pytest.mark.asyncio
async def test_interactive_mode_cache_operations(faiss_cache_dir):
    """Test cache operations in interactive mode."""
    cache = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)

    # User connects to database
    connection_id = 'interactive_conn'

    # User requests table suggestions
    metadata = {
        'tables': [
            {
                'name': 'employees',
                'schema': 'hr',
                'description': 'Employee records',
                'columns': [
                    {'name': 'id', 'type': 'integer', 'description': 'Employee ID'},
                    {'name': 'name', 'type': 'varchar', 'description': 'Full name'},
                    {'name': 'department', 'type': 'varchar', 'description': 'Department'},
                ]
            }
        ]
    }

    await cache.index_database(connection_id, metadata)

    # User types: "SELECT * FROM emp..."
    # System suggests tables
    suggestions = await cache.search_tables(
        query='employee',
        connection_id=connection_id,
        limit=5,
        threshold=0.1
    )

    assert len(suggestions) > 0
    assert suggestions[0]['name'] == 'employees'

    # User types: "SELECT name, dept..."
    # System suggests columns
    column_suggestions = await cache.search_columns(
        query='department',
        connection_id=connection_id,
        table_name='employees',
        limit=5,
        threshold=0.1
    )

    assert len(column_suggestions) > 0
    column_names = [c['name'] for c in column_suggestions]
    assert 'department' in column_names


@pytest.mark.asyncio
async def test_multi_database_connection_workflow(faiss_cache_dir):
    """Test workflow with multiple database connections."""
    cache = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)

    # Connection 1: PostgreSQL
    postgres_metadata = {
        'tables': [
            {
                'name': 'users',
                'schema': 'public',
                'description': 'PostgreSQL user data',
                'columns': [
                    {'name': 'id', 'type': 'integer', 'description': 'User ID'},
                ]
            }
        ]
    }
    await cache.index_database('postgres_conn', postgres_metadata)

    # Connection 2: MySQL
    mysql_metadata = {
        'tables': [
            {
                'name': 'customers',
                'schema': 'main',
                'description': 'MySQL customer data',
                'columns': [
                    {'name': 'id', 'type': 'int', 'description': 'Customer ID'},
                ]
            }
        ]
    }
    await cache.index_database('mysql_conn', mysql_metadata)

    # Search in PostgreSQL connection only
    pg_results = await cache.search_tables(
        query='user',
        connection_id='postgres_conn',
        limit=5
    )
    assert len(pg_results) > 0
    assert all(r['connection_id'] == 'postgres_conn' for r in pg_results)

    # Search in MySQL connection only
    mysql_results = await cache.search_tables(
        query='customer',
        connection_id='mysql_conn',
        limit=5
    )
    assert len(mysql_results) > 0
    assert all(r['connection_id'] == 'mysql_conn' for r in mysql_results)

    # Search across all connections
    all_results = await cache.search_tables(
        query='data',
        limit=10
    )
    assert len(all_results) > 0


@pytest.mark.asyncio
async def test_cache_refresh_on_schema_change(faiss_cache_dir):
    """Test cache refresh when database schema changes."""
    cache = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)

    # Initial schema
    initial_metadata = {
        'tables': [
            {
                'name': 'users',
                'schema': 'public',
                'description': 'User data',
                'columns': [
                    {'name': 'id', 'type': 'integer', 'description': 'User ID'},
                ]
            }
        ]
    }
    await cache.index_database('test_conn', initial_metadata)

    # Verify initial state
    initial_stats = cache.get_stats()
    assert initial_stats['total_tables'] == 1

    # Schema changes: new table added
    updated_metadata = {
        'tables': [
            {
                'name': 'users',
                'schema': 'public',
                'description': 'User data',
                'columns': [
                    {'name': 'id', 'type': 'integer', 'description': 'User ID'},
                ]
            },
            {
                'name': 'posts',
                'schema': 'public',
                'description': 'User posts',
                'columns': [
                    {'name': 'id', 'type': 'integer', 'description': 'Post ID'},
                ]
            }
        ]
    }

    # Refresh cache
    cache.refresh_cache('test_conn', updated_metadata)

    # Verify updated state
    updated_stats = cache.get_stats()
    assert updated_stats['total_tables'] == 2

    # Search for new table
    results = await cache.search_tables(
        query='posts',
        connection_id='test_conn',
        limit=5
    )
    assert len(results) > 0
    assert any(r['name'] == 'posts' for r in results)


@pytest.mark.asyncio
async def test_query_optimization_with_cache(faiss_cache_dir):
    """Test using cache to optimize query generation."""
    cache = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)

    # Index database schema
    metadata = {
        'tables': [
            {
                'name': 'orders',
                'schema': 'sales',
                'description': 'Sales orders and transactions',
                'columns': [
                    {'name': 'id', 'type': 'integer', 'description': 'Order ID'},
                    {'name': 'customer_id', 'type': 'integer', 'description': 'Customer reference'},
                    {'name': 'order_date', 'type': 'date', 'description': 'Order date'},
                    {'name': 'total_amount', 'type': 'decimal', 'description': 'Total amount'},
                ]
            },
            {
                'name': 'customers',
                'schema': 'sales',
                'description': 'Customer information',
                'columns': [
                    {'name': 'id', 'type': 'integer', 'description': 'Customer ID'},
                    {'name': 'name', 'type': 'varchar', 'description': 'Customer name'},
                    {'name': 'email', 'type': 'varchar', 'description': 'Email address'},
                ]
            }
        ]
    }
    await cache.index_database('sales_db', metadata)

    # User query: "Show me all orders from customers"
    # Step 1: Find relevant tables
    table_results = await cache.search_tables(
        query='orders customers',
        connection_id='sales_db',
        limit=5,
        threshold=0.1
    )

    assert len(table_results) >= 2
    table_names = [r['name'] for r in table_results]
    assert 'orders' in table_names
    assert 'customers' in table_names

    # Step 2: Find join columns
    join_column_results = await cache.search_columns(
        query='customer reference id',
        connection_id='sales_db',
        limit=10,
        threshold=0.1
    )

    assert len(join_column_results) > 0
    # Should find customer_id in orders and id in customers


def test_vector_database_direct_usage():
    """Test VectorDatabase for custom use cases."""
    db = VectorDatabase(dimension=384, use_faiss=True)

    # Add custom vectors
    custom_vectors = {
        'query_pattern_1': 'SELECT * FROM users WHERE id = ?',
        'query_pattern_2': 'UPDATE users SET email = ? WHERE id = ?',
        'query_pattern_3': 'DELETE FROM users WHERE id = ?',
    }

    def simple_embedding(text):
        """Simple deterministic embedding for testing."""
        np.random.seed(sum(ord(c) for c in text))
        vec = np.random.randn(384).astype(np.float32)
        return vec / np.linalg.norm(vec)

    for query_id, query_text in custom_vectors.items():
        vector = simple_embedding(query_text)
        db.add_object(query_id, vector, 'query_pattern', {'text': query_text})

    # Search for similar query patterns
    new_query = 'SELECT id, email FROM users WHERE id = 5'
    query_vector = simple_embedding(new_query)

    results = db.search_similar(query_vector, k=3, threshold=0.0)

    assert len(results) > 0
    # Should find SELECT query as most similar
    assert 'query_pattern_1' in [entry.id for entry, _ in results]


@pytest.mark.asyncio
async def test_cache_persistence_workflow(faiss_cache_dir):
    """Test cache persistence across sessions."""
    # Session 1: Create and populate cache
    cache1 = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)

    metadata = {
        'tables': [
            {
                'name': 'sessions',
                'schema': 'public',
                'description': 'User sessions',
                'columns': [
                    {'name': 'id', 'type': 'uuid', 'description': 'Session ID'},
                    {'name': 'user_id', 'type': 'integer', 'description': 'User reference'},
                ]
            }
        ]
    }

    await cache1.index_database('session_conn', metadata)
    await cache1.save_to_disk()

    # Session 2: Load cache
    cache2 = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)
    loaded = await cache2.load_from_disk()

    assert loaded is True

    # Verify data is available
    table = cache2.get_table('session_conn', 'public', 'sessions')
    assert table is not None
    assert table.name == 'sessions'

    # Search works with loaded cache
    results = await cache2.search_tables(
        query='sessions',
        connection_id='session_conn',
        limit=5
    )

    assert len(results) > 0


@pytest.mark.asyncio
async def test_error_handling_workflow(faiss_cache_dir):
    """Test error handling in various scenarios."""
    cache = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)

    # Test 1: Empty metadata
    empty_metadata = {'tables': []}
    await cache.index_database('empty_conn', empty_metadata)
    stats = cache.get_stats()
    assert stats['total_tables'] == 0

    # Test 2: Search on empty cache
    results = await cache.search_tables(
        query='anything',
        connection_id='empty_conn',
        limit=5
    )
    assert len(results) == 0

    # Test 3: Invalid connection ID
    results = await cache.search_tables(
        query='test',
        connection_id='nonexistent_conn',
        limit=5
    )
    assert len(results) == 0


@pytest.mark.asyncio
async def test_performance_with_large_dataset(faiss_cache_dir):
    """Test performance with large metadata dataset."""
    import time

    cache = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)

    # Create large metadata (100 tables, 10 columns each)
    large_metadata = {
        'tables': [
            {
                'name': f'table_{i}',
                'schema': 'public',
                'description': f'Table {i} for testing',
                'columns': [
                    {
                        'name': f'column_{j}',
                        'type': 'varchar',
                        'description': f'Column {j}'
                    }
                    for j in range(10)
                ]
            }
            for i in range(100)
        ]
    }

    # Measure indexing time
    start_time = time.time()
    await cache.index_database('large_conn', large_metadata)
    index_time = time.time() - start_time

    # Indexing should complete in reasonable time (< 5 seconds)
    assert index_time < 5.0

    # Measure search time
    start_time = time.time()
    results = await cache.search_tables(
        query='table 50',
        connection_id='large_conn',
        limit=10
    )
    search_time = time.time() - start_time

    # Search should be fast (< 0.1 seconds)
    assert search_time < 0.1
    assert len(results) > 0


@pytest.mark.asyncio
async def test_concurrent_cache_operations(faiss_cache_dir):
    """Test concurrent cache operations."""
    cache = DatabaseMetadataCache(cache_dir=str(faiss_cache_dir), dimension=384)

    # Index initial data
    metadata = {
        'tables': [
            {
                'name': 'concurrent_test',
                'schema': 'public',
                'description': 'Concurrency test table',
                'columns': [
                    {'name': 'id', 'type': 'integer', 'description': 'ID'},
                ]
            }
        ]
    }
    await cache.index_database('concurrent_conn', metadata)

    # Perform multiple concurrent searches
    async def search_task(query):
        return await cache.search_tables(
            query=query,
            connection_id='concurrent_conn',
            limit=5
        )

    tasks = [
        search_task('concurrent'),
        search_task('test'),
        search_task('table'),
    ]

    results = await asyncio.gather(*tasks)

    # All searches should complete successfully
    assert len(results) == 3
    for result in results:
        assert isinstance(result, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
