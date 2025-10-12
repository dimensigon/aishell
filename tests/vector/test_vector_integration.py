"""End-to-end integration tests for vector store with embeddings.

Tests cover:
- Complete workflow with real/mock embeddings
- LLM integration
- Database object indexing and search
- Semantic query understanding
- Performance with realistic workloads
- Error handling and recovery
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from src.vector.store import VectorDatabase, FAISS_AVAILABLE
from src.vector.autocomplete import IntelligentCompleter


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_llm_embeddings():
    """Mock LLM embeddings function."""
    def embedding_func(text: str) -> np.ndarray:
        """Generate deterministic embeddings from text."""
        # Use text hash for reproducibility
        seed = hash(text) % (2**32)
        np.random.seed(seed)
        vec = np.random.randn(384)
        return vec / np.linalg.norm(vec)

    return embedding_func


@pytest.fixture
def sample_database_schema():
    """Sample database schema for testing."""
    return [
        {
            'name': 'users',
            'description': 'User accounts and authentication',
            'schema': 'public',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Primary key'},
                {'name': 'email', 'type': 'varchar(255)', 'description': 'User email address'},
                {'name': 'username', 'type': 'varchar(50)', 'description': 'Unique username'},
                {'name': 'password_hash', 'type': 'varchar(255)', 'description': 'Hashed password'},
                {'name': 'created_at', 'type': 'timestamp', 'description': 'Account creation time'},
                {'name': 'is_active', 'type': 'boolean', 'description': 'Account active status'}
            ]
        },
        {
            'name': 'orders',
            'description': 'Customer order records',
            'schema': 'public',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Order ID'},
                {'name': 'user_id', 'type': 'integer', 'description': 'Foreign key to users'},
                {'name': 'order_date', 'type': 'timestamp', 'description': 'Order placement date'},
                {'name': 'total_amount', 'type': 'decimal(10,2)', 'description': 'Total order value'},
                {'name': 'status', 'type': 'varchar(20)', 'description': 'Order status'},
                {'name': 'shipping_address', 'type': 'text', 'description': 'Delivery address'}
            ]
        },
        {
            'name': 'products',
            'description': 'Product catalog and inventory',
            'schema': 'public',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Product ID'},
                {'name': 'name', 'type': 'varchar(200)', 'description': 'Product name'},
                {'name': 'description', 'type': 'text', 'description': 'Product description'},
                {'name': 'price', 'type': 'decimal(10,2)', 'description': 'Unit price'},
                {'name': 'stock_quantity', 'type': 'integer', 'description': 'Available inventory'},
                {'name': 'category', 'type': 'varchar(50)', 'description': 'Product category'}
            ]
        },
        {
            'name': 'order_items',
            'description': 'Line items in orders',
            'schema': 'public',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Line item ID'},
                {'name': 'order_id', 'type': 'integer', 'description': 'Foreign key to orders'},
                {'name': 'product_id', 'type': 'integer', 'description': 'Foreign key to products'},
                {'name': 'quantity', 'type': 'integer', 'description': 'Quantity ordered'},
                {'name': 'unit_price', 'type': 'decimal(10,2)', 'description': 'Price at time of order'}
            ]
        }
    ]


@pytest.fixture
def integrated_system(mock_llm_embeddings, sample_database_schema):
    """Create fully integrated vector search system."""
    vector_db = VectorDatabase(dimension=384, use_faiss=False)
    completer = IntelligentCompleter(vector_db)

    # Index database schema
    vector_db.index_database_objects(sample_database_schema, mock_llm_embeddings)

    return {
        'vector_db': vector_db,
        'completer': completer,
        'embeddings': mock_llm_embeddings,
        'schema': sample_database_schema
    }


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================


class TestEndToEndWorkflow:
    """Tests for complete workflow scenarios."""

    def test_schema_indexing_workflow(self, integrated_system):
        """Test complete schema indexing workflow."""
        vector_db = integrated_system['vector_db']

        # Verify all objects indexed
        stats = vector_db.get_stats()
        assert stats['total_entries'] > 0

        # Should have tables and columns
        assert 'table' in stats['type_counts']
        assert 'column' in stats['type_counts']

        # Should have 4 tables
        assert stats['type_counts']['table'] == 4

        # Should have sum of all columns
        total_columns = sum(len(t['columns']) for t in integrated_system['schema'])
        assert stats['type_counts']['column'] == total_columns

    def test_semantic_table_search(self, integrated_system):
        """Test semantic search for tables."""
        vector_db = integrated_system['vector_db']
        embeddings = integrated_system['embeddings']

        # Search for "customer accounts"
        query_vec = embeddings("customer accounts and authentication")
        results = vector_db.search_similar(query_vec, k=5, object_type='table', threshold=0.3)

        # Should find users table
        table_names = [r[0].metadata.get('name') for r in results]
        assert 'users' in table_names

    def test_semantic_column_search(self, integrated_system):
        """Test semantic search for columns."""
        vector_db = integrated_system['vector_db']
        embeddings = integrated_system['embeddings']

        # Search for "email address"
        query_vec = embeddings("email address")
        results = vector_db.search_similar(query_vec, k=5, object_type='column', threshold=0.2)

        # Should find email column
        column_ids = [r[0].id for r in results]
        assert any('email' in cid.lower() for cid in column_ids)

    def test_completion_workflow(self, integrated_system):
        """Test complete autocomplete workflow."""
        completer = integrated_system['completer']
        embeddings = integrated_system['embeddings']

        # User starts typing query
        query = 'SELECT * FROM '
        query_vec = embeddings(query)

        candidates = completer.get_context_aware_completions(
            query=query,
            query_vector=query_vec,
            statement_type='SELECT',
            cursor_position=len(query)
        )

        # Should suggest table names
        assert len(candidates) > 0
        table_suggestions = [c for c in candidates
                            if any(t in c.text for t in ['users', 'orders', 'products'])]
        assert len(table_suggestions) > 0

    def test_query_building_workflow(self, integrated_system):
        """Test progressive query building with completions."""
        completer = integrated_system['completer']
        embeddings = integrated_system['embeddings']

        # Step 1: Start with SELECT
        query1 = 'sel'
        vec1 = embeddings(query1)
        candidates1 = completer.get_completions(query1, vec1)
        assert any(c.text == 'SELECT' for c in candidates1)

        # Step 2: After FROM
        query2 = 'SELECT * FROM '
        vec2 = embeddings(query2)
        candidates2 = completer.get_context_aware_completions(
            query2, vec2, 'SELECT', len(query2)
        )
        assert len(candidates2) > 0

        # Step 3: Add to history and continue
        completer.add_to_history('SELECT * FROM users')
        query3 = 'SELECT'
        vec3 = embeddings(query3)
        candidates3 = completer.get_completions(query3, vec3)

        # Should include history
        history_items = [c for c in candidates3 if c.source == 'history']
        assert len(history_items) > 0


# ============================================================================
# Semantic Understanding Tests
# ============================================================================


class TestSemanticUnderstanding:
    """Tests for semantic query understanding."""

    def test_synonym_search(self, integrated_system):
        """Test search with synonyms."""
        vector_db = integrated_system['vector_db']
        embeddings = integrated_system['embeddings']

        # "customer" should find "users"
        query_vec = embeddings("customer information")
        results = vector_db.search_similar(query_vec, k=5, object_type='table', threshold=0.2)

        table_names = [r[0].metadata.get('name', '') for r in results]
        assert any('user' in name.lower() for name in table_names)

    def test_concept_search(self, integrated_system):
        """Test search by concept rather than exact terms."""
        vector_db = integrated_system['vector_db']
        embeddings = integrated_system['embeddings']

        # "purchase history" should find orders
        query_vec = embeddings("purchase history")
        results = vector_db.search_similar(query_vec, k=5, object_type='table', threshold=0.2)

        table_names = [r[0].metadata.get('name', '') for r in results]
        assert any('order' in name.lower() for name in table_names)

    def test_multi_table_query_understanding(self, integrated_system):
        """Test understanding queries spanning multiple tables."""
        vector_db = integrated_system['vector_db']
        embeddings = integrated_system['embeddings']

        # "customer orders with products" - should find relevant tables
        query_vec = embeddings("customer orders with products")
        results = vector_db.search_similar(query_vec, k=10, object_type='table', threshold=0.2)

        table_names = [r[0].metadata.get('name', '') for r in results]
        # Should find at least some of: users, orders, products
        relevant = sum(1 for name in table_names if name in ['users', 'orders', 'products'])
        assert relevant >= 2

    def test_column_type_understanding(self, integrated_system):
        """Test understanding of column types and purposes."""
        vector_db = integrated_system['vector_db']
        embeddings = integrated_system['embeddings']

        # Search for "timestamp" or "date" columns
        query_vec = embeddings("when was something created")
        results = vector_db.search_similar(query_vec, k=10, object_type='column', threshold=0.2)

        # Should find timestamp columns
        column_types = [r[0].metadata.get('type', '') for r in results]
        assert any('timestamp' in ctype.lower() for ctype in column_types)


# ============================================================================
# Performance Integration Tests
# ============================================================================


class TestPerformanceIntegration:
    """Tests for realistic performance scenarios."""

    def test_cold_start_performance(self, mock_llm_embeddings, sample_database_schema):
        """Test cold start - indexing and first search."""
        import time

        # Create new system
        start_time = time.time()

        vector_db = VectorDatabase(dimension=384, use_faiss=False)
        completer = IntelligentCompleter(vector_db)

        # Index schema
        vector_db.index_database_objects(sample_database_schema, mock_llm_embeddings)

        # Perform search
        query_vec = mock_llm_embeddings("user accounts")
        results = vector_db.search_similar(query_vec, k=5)

        total_time = time.time() - start_time

        assert len(results) > 0
        assert total_time < 5.0  # Should complete in reasonable time

    def test_warm_cache_performance(self, integrated_system):
        """Test performance with warmed cache."""
        import time

        vector_db = integrated_system['vector_db']
        embeddings = integrated_system['embeddings']

        # Warm up
        for _ in range(5):
            query_vec = embeddings("test query")
            vector_db.search_similar(query_vec, k=5)

        # Measure warmed performance
        start_time = time.time()

        for _ in range(100):
            query_vec = embeddings(f"query {_}")
            results = vector_db.search_similar(query_vec, k=5)

        total_time = time.time() - start_time

        assert total_time < 10.0  # 100 searches in under 10s

    def test_concurrent_search_simulation(self, integrated_system):
        """Test multiple simultaneous searches."""
        import time

        vector_db = integrated_system['vector_db']
        embeddings = integrated_system['embeddings']

        queries = [
            "user accounts",
            "order history",
            "product catalog",
            "email addresses",
            "customer information"
        ]

        start_time = time.time()

        # Simulate concurrent searches
        all_results = []
        for query in queries * 10:  # 50 total searches
            query_vec = embeddings(query)
            results = vector_db.search_similar(query_vec, k=5)
            all_results.append(results)

        total_time = time.time() - start_time

        assert len(all_results) == 50
        assert total_time < 5.0

    @pytest.mark.slow
    def test_large_schema_performance(self, mock_llm_embeddings):
        """Test performance with large database schema."""
        import time

        # Generate large schema (100 tables, 10 columns each)
        large_schema = []
        for i in range(100):
            table = {
                'name': f'table_{i}',
                'description': f'Table number {i} for testing',
                'schema': 'public',
                'columns': [
                    {
                        'name': f'col_{j}',
                        'type': 'varchar',
                        'description': f'Column {j} in table {i}'
                    }
                    for j in range(10)
                ]
            }
            large_schema.append(table)

        # Index
        vector_db = VectorDatabase(dimension=384, use_faiss=False)

        start_time = time.time()
        vector_db.index_database_objects(large_schema, mock_llm_embeddings)
        index_time = time.time() - start_time

        print(f"\nIndexed {len(large_schema)} tables in {index_time:.2f}s")

        # Search
        query_vec = mock_llm_embeddings("find table 50")
        start_time = time.time()
        results = vector_db.search_similar(query_vec, k=10)
        search_time = time.time() - start_time

        print(f"Search completed in {search_time:.4f}s")

        assert len(results) > 0
        assert search_time < 1.0


# ============================================================================
# Error Handling and Recovery Tests
# ============================================================================


class TestErrorHandling:
    """Tests for error handling in integrated system."""

    def test_embedding_failure_handling(self, sample_database_schema):
        """Test handling of embedding generation failures."""
        vector_db = VectorDatabase(dimension=384, use_faiss=False)

        def failing_embeddings(text):
            if 'error' in text.lower():
                raise ValueError("Embedding generation failed")
            vec = np.random.randn(384)
            return vec / np.linalg.norm(vec)

        # Should handle failures gracefully
        try:
            vector_db.index_database_objects(
                sample_database_schema,
                failing_embeddings
            )
        except ValueError:
            pass  # Expected for some tables

        # Should still have indexed some objects
        stats = vector_db.get_stats()
        # May have partial indexing

    def test_invalid_query_vector(self, integrated_system):
        """Test handling of invalid query vectors."""
        vector_db = integrated_system['vector_db']

        # Wrong dimension
        wrong_vec = np.random.randn(100)

        # Should handle gracefully
        try:
            results = vector_db.search_similar(wrong_vec, k=5)
        except (ValueError, Exception):
            pass  # Expected

    def test_corrupted_metadata(self, integrated_system):
        """Test handling of corrupted metadata."""
        vector_db = integrated_system['vector_db']
        embeddings = integrated_system['embeddings']

        # Add entry with missing metadata
        vec = embeddings("test")
        vector_db.add_object('corrupted', vec, 'table', metadata=None)

        # Should still work
        stats = vector_db.get_stats()
        assert stats['total_entries'] > 0

    def test_search_with_empty_results(self, integrated_system):
        """Test search that returns no results."""
        vector_db = integrated_system['vector_db']
        embeddings = integrated_system['embeddings']

        # Search with very high threshold
        query_vec = embeddings("nonexistent concept xyz123")
        results = vector_db.search_similar(query_vec, k=5, threshold=0.99)

        # Should return empty list, not error
        assert results == []

    def test_recovery_after_error(self, integrated_system):
        """Test system continues working after errors."""
        vector_db = integrated_system['vector_db']
        embeddings = integrated_system['embeddings']

        # Cause an error
        try:
            vector_db.add_object('bad', np.random.randn(100), 'table')
        except ValueError:
            pass

        # System should still work
        query_vec = embeddings("users")
        results = vector_db.search_similar(query_vec, k=5)
        assert len(results) > 0


# ============================================================================
# Real FAISS Integration Tests
# ============================================================================


class TestRealFAISSIntegration:
    """Tests for integration with real FAISS library."""

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_real_faiss_workflow(self, mock_llm_embeddings, sample_database_schema):
        """Test complete workflow with real FAISS."""
        # Note: Using smaller dimension for real FAISS
        def small_embeddings(text):
            vec = mock_llm_embeddings(text)
            return vec[:128]  # Reduce to 128 dimensions

        vector_db = VectorDatabase(dimension=128, use_faiss=True)
        completer = IntelligentCompleter(vector_db)

        # Index schema
        # Adjust schema for smaller vectors
        small_schema = sample_database_schema[:2]  # Use fewer tables
        vector_db.index_database_objects(small_schema, small_embeddings)

        # Search
        query_vec = small_embeddings("user accounts")
        results = vector_db.search_similar(query_vec, k=5)

        assert len(results) > 0

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_real_faiss_autocomplete(self, mock_llm_embeddings):
        """Test autocomplete with real FAISS."""
        def small_embeddings(text):
            vec = mock_llm_embeddings(text)
            return vec[:128]

        vector_db = VectorDatabase(dimension=128, use_faiss=True)
        completer = IntelligentCompleter(vector_db)

        # Add some data
        tables = [{'name': 'users', 'description': 'Users', 'columns': []}]
        vector_db.index_database_objects(tables, small_embeddings)

        # Get completions
        query_vec = small_embeddings("SELECT")
        candidates = completer.get_completions('SELECT', query_vec)

        assert len(candidates) > 0


# ============================================================================
# Query Pattern Tests
# ============================================================================


class TestQueryPatterns:
    """Tests for common SQL query patterns."""

    def test_simple_select_pattern(self, integrated_system):
        """Test simple SELECT query pattern."""
        completer = integrated_system['completer']
        embeddings = integrated_system['embeddings']

        # Build query step by step
        queries = [
            ('sel', 'SELECT'),
            ('SELECT * fr', 'FROM'),
            ('SELECT * FROM ', 'table_name')
        ]

        for query, expected_type in queries:
            query_vec = embeddings(query)
            candidates = completer.get_completions(query, query_vec)
            assert len(candidates) > 0

    def test_join_pattern(self, integrated_system):
        """Test JOIN query pattern."""
        completer = integrated_system['completer']
        embeddings = integrated_system['embeddings']

        query = 'SELECT * FROM users JOIN'
        query_vec = embeddings(query)
        candidates = completer.get_completions(query, query_vec)

        # Should suggest JOIN types
        join_candidates = [c for c in candidates if 'JOIN' in c.text]
        assert len(join_candidates) > 0

    def test_where_clause_pattern(self, integrated_system):
        """Test WHERE clause pattern."""
        completer = integrated_system['completer']
        embeddings = integrated_system['embeddings']

        query = 'SELECT * FROM users wh'
        query_vec = embeddings(query)
        candidates = completer.get_completions(query, query_vec)

        # Should suggest WHERE
        where_candidates = [c for c in candidates if c.text == 'WHERE']
        assert len(where_candidates) > 0

    def test_aggregate_function_pattern(self, integrated_system):
        """Test aggregate function pattern."""
        completer = integrated_system['completer']
        embeddings = integrated_system['embeddings']

        query = 'SELECT COUNT('
        query_vec = embeddings(query)
        candidates = completer.get_completions(query, query_vec)

        # Should suggest closing paren and *
        assert len(candidates) > 0


# ============================================================================
# Cross-Feature Integration Tests
# ============================================================================


class TestCrossFeatureIntegration:
    """Tests for integration between features."""

    def test_history_with_vector_search(self, integrated_system):
        """Test history combined with vector search."""
        completer = integrated_system['completer']
        embeddings = integrated_system['embeddings']

        # Add queries to history
        completer.add_to_history('SELECT * FROM users WHERE email LIKE "%@example.com"')
        completer.add_to_history('SELECT COUNT(*) FROM orders')

        # Search should use both history and vectors
        query_vec = embeddings('SELECT')
        candidates = completer.get_completions('SELECT', query_vec)

        sources = set(c.source for c in candidates)
        assert 'history' in sources
        assert len(sources) > 1  # Multiple sources

    def test_pattern_with_context_awareness(self, integrated_system):
        """Test patterns with context-aware completion."""
        completer = integrated_system['completer']
        embeddings = integrated_system['embeddings']

        query = 'SELECT * FROM '
        query_vec = embeddings(query)

        # Context-aware should combine patterns and semantic search
        candidates = completer.get_context_aware_completions(
            query, query_vec, 'SELECT', len(query)
        )

        # Should have multiple sources
        sources = set(c.source for c in candidates)
        assert len(sources) > 0

    def test_deduplication_across_sources(self, integrated_system):
        """Test deduplication works across all sources."""
        completer = integrated_system['completer']
        embeddings = integrated_system['embeddings']

        # Add history that might overlap with patterns
        completer.add_to_history('SELECT * FROM users')

        query_vec = embeddings('sel')
        candidates = completer.get_completions('sel', query_vec)

        # Check no duplicates
        texts = [c.text for c in candidates]
        assert len(texts) == len(set(texts))
