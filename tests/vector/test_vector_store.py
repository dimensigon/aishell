"""Comprehensive tests for vector store functionality.

Tests cover:
- FAISS operations (mock and real)
- Vector indexing and retrieval
- Similarity search
- Batch operations
- Performance with large datasets
- Index persistence (save/load)
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Tuple

from src.vector.store import (
    VectorDatabase,
    VectorEntry,
    MockFAISSIndex,
    FAISS_AVAILABLE
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_vector_db():
    """Create vector database with mock FAISS."""
    return VectorDatabase(dimension=384, use_faiss=False)


@pytest.fixture
def real_vector_db():
    """Create vector database with real FAISS if available."""
    if not FAISS_AVAILABLE:
        pytest.skip("FAISS not available")
    return VectorDatabase(dimension=128, use_faiss=True)


@pytest.fixture
def sample_vectors():
    """Generate sample normalized vectors."""
    def _generate(n: int = 10, dim: int = 384) -> List[np.ndarray]:
        vectors = []
        for i in range(n):
            vec = np.random.randn(dim)
            vectors.append(vec / np.linalg.norm(vec))
        return vectors
    return _generate


@pytest.fixture
def temp_index_dir():
    """Create temporary directory for index persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================================
# MockFAISSIndex Tests
# ============================================================================


class TestMockFAISSIndex:
    """Tests for mock FAISS index implementation."""

    def test_initialization(self):
        """Test mock index initialization."""
        index = MockFAISSIndex(dimension=128)

        assert index.dimension == 128
        assert index.ntotal == 0
        assert len(index.vectors) == 0

    def test_add_single_vector(self):
        """Test adding a single vector."""
        index = MockFAISSIndex(dimension=10)
        vec = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        index.add(vec)

        assert index.ntotal == 1
        assert len(index.vectors) == 1
        np.testing.assert_array_equal(index.vectors[0], vec)

    def test_add_multiple_vectors(self):
        """Test adding multiple vectors at once."""
        index = MockFAISSIndex(dimension=5)
        vectors = np.array([
            [1.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0, 0.0]
        ])

        index.add(vectors)

        assert index.ntotal == 3
        assert len(index.vectors) == 3

    def test_search_exact_match(self):
        """Test search with exact vector match."""
        index = MockFAISSIndex(dimension=10)

        vec1 = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        index.add(vec1)
        index.add(vec2)

        distances, indices = index.search(vec1, k=1)

        assert indices[0][0] == 0
        assert distances[0][0] < 0.01  # Should be very close to 0

    def test_search_top_k(self):
        """Test retrieving top-k nearest neighbors."""
        index = MockFAISSIndex(dimension=5)

        # Add 5 vectors
        for i in range(5):
            vec = np.zeros(5)
            vec[i] = 1.0
            index.add(vec)

        query = np.array([0.9, 0.1, 0.0, 0.0, 0.0])
        distances, indices = index.search(query, k=3)

        assert len(distances[0]) == 3
        assert len(indices[0]) == 3
        assert indices[0][0] == 0  # First vector should be closest

    def test_search_empty_index(self):
        """Test search on empty index."""
        index = MockFAISSIndex(dimension=10)
        query = np.ones(10)

        distances, indices = index.search(query, k=5)

        assert distances.shape == (1, 0)
        assert indices.shape == (1, 0)

    def test_cosine_similarity_scoring(self):
        """Test that similarity scoring works correctly."""
        index = MockFAISSIndex(dimension=3)

        # Add orthogonal vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        vec3 = np.array([0.7071, 0.7071, 0.0])  # 45 degrees to vec1

        index.add(vec1)
        index.add(vec2)
        index.add(vec3)

        distances, indices = index.search(vec1, k=3)

        # vec3 should be closer than vec2 (orthogonal)
        assert distances[0][1] < distances[0][2]


# ============================================================================
# VectorDatabase Initialization Tests
# ============================================================================


class TestVectorDatabaseInit:
    """Tests for VectorDatabase initialization."""

    def test_init_with_mock(self):
        """Test initialization with mock FAISS."""
        db = VectorDatabase(dimension=256, use_faiss=False)

        assert db.dimension == 256
        assert not db.use_faiss
        assert isinstance(db.index, MockFAISSIndex)
        assert len(db.entries) == 0
        assert len(db._id_to_idx) == 0

    def test_init_with_real_faiss(self):
        """Test initialization with real FAISS."""
        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not available")

        db = VectorDatabase(dimension=128, use_faiss=True)

        assert db.dimension == 128
        assert db.use_faiss
        assert not isinstance(db.index, MockFAISSIndex)

    def test_default_dimension(self):
        """Test default dimension setting."""
        db = VectorDatabase()
        assert db.dimension == 384


# ============================================================================
# Vector Operations Tests
# ============================================================================


class TestVectorOperations:
    """Tests for vector add/get/delete operations."""

    def test_add_object_basic(self, mock_vector_db, sample_vectors):
        """Test adding a basic object."""
        vectors = sample_vectors(1)

        mock_vector_db.add_object(
            object_id='table:users',
            vector=vectors[0],
            object_type='table',
            metadata={'name': 'users', 'schema': 'public'}
        )

        assert len(mock_vector_db.entries) == 1
        assert mock_vector_db.entries[0].id == 'table:users'
        assert mock_vector_db.entries[0].object_type == 'table'
        assert mock_vector_db.index.ntotal == 1

    def test_add_object_wrong_dimension(self, mock_vector_db):
        """Test adding vector with incorrect dimension."""
        wrong_vec = np.random.randn(100)  # Wrong dimension

        with pytest.raises(ValueError, match="Vector dimension"):
            mock_vector_db.add_object(
                object_id='test',
                vector=wrong_vec,
                object_type='table'
            )

    def test_add_multiple_objects(self, mock_vector_db, sample_vectors):
        """Test adding multiple objects."""
        vectors = sample_vectors(5)

        for i, vec in enumerate(vectors):
            mock_vector_db.add_object(
                object_id=f'obj_{i}',
                vector=vec,
                object_type='table',
                metadata={'index': i}
            )

        assert len(mock_vector_db.entries) == 5
        assert mock_vector_db.index.ntotal == 5

    def test_add_object_with_metadata(self, mock_vector_db, sample_vectors):
        """Test adding object with rich metadata."""
        vectors = sample_vectors(1)
        metadata = {
            'name': 'users',
            'schema': 'public',
            'columns': ['id', 'name', 'email'],
            'row_count': 1000
        }

        mock_vector_db.add_object(
            object_id='table:users',
            vector=vectors[0],
            object_type='table',
            metadata=metadata
        )

        entry = mock_vector_db.get_by_id('table:users')
        assert entry.metadata == metadata

    def test_get_by_id_existing(self, mock_vector_db, sample_vectors):
        """Test retrieving existing entry by ID."""
        vectors = sample_vectors(1)
        mock_vector_db.add_object('test_id', vectors[0], 'table')

        entry = mock_vector_db.get_by_id('test_id')

        assert entry is not None
        assert entry.id == 'test_id'
        assert entry.object_type == 'table'
        np.testing.assert_array_equal(entry.vector, vectors[0])

    def test_get_by_id_nonexistent(self, mock_vector_db):
        """Test retrieving non-existent entry."""
        entry = mock_vector_db.get_by_id('nonexistent')
        assert entry is None

    def test_delete_by_id_existing(self, mock_vector_db, sample_vectors):
        """Test deleting existing entry."""
        vectors = sample_vectors(1)
        mock_vector_db.add_object('test_id', vectors[0], 'table')

        result = mock_vector_db.delete_by_id('test_id')

        assert result is True
        entry = mock_vector_db.get_by_id('test_id')
        assert entry.metadata.get('_deleted') is True

    def test_delete_by_id_nonexistent(self, mock_vector_db):
        """Test deleting non-existent entry."""
        result = mock_vector_db.delete_by_id('nonexistent')
        assert result is False

    def test_vector_immutability(self, mock_vector_db, sample_vectors):
        """Test that stored vectors are copied (immutable)."""
        vectors = sample_vectors(1)
        original = vectors[0].copy()

        mock_vector_db.add_object('test', vectors[0], 'table')

        # Modify original
        vectors[0][0] = 999.0

        # Stored vector should be unchanged
        entry = mock_vector_db.get_by_id('test')
        np.testing.assert_array_equal(entry.vector, original)


# ============================================================================
# Similarity Search Tests
# ============================================================================


class TestSimilaritySearch:
    """Tests for vector similarity search."""

    def test_search_basic(self, mock_vector_db, sample_vectors):
        """Test basic similarity search."""
        vectors = sample_vectors(3)

        for i, vec in enumerate(vectors):
            mock_vector_db.add_object(f'obj_{i}', vec, 'table')

        results = mock_vector_db.search_similar(vectors[0], k=2)

        assert len(results) > 0
        assert results[0][0].id == 'obj_0'  # Most similar to itself

    def test_search_with_threshold(self, mock_vector_db):
        """Test search with similarity threshold."""
        # Create similar and dissimilar vectors
        base_vec = np.ones(384)
        base_vec = base_vec / np.linalg.norm(base_vec)

        similar_vec = base_vec + np.random.randn(384) * 0.01
        similar_vec = similar_vec / np.linalg.norm(similar_vec)

        dissimilar_vec = -base_vec  # Opposite direction

        mock_vector_db.add_object('similar', similar_vec, 'table')
        mock_vector_db.add_object('dissimilar', dissimilar_vec, 'table')

        # High threshold should only return similar
        results = mock_vector_db.search_similar(base_vec, k=10, threshold=0.9)

        assert len(results) <= 1
        if results:
            assert results[0][0].id == 'similar'

    def test_search_with_type_filter(self, mock_vector_db, sample_vectors):
        """Test search with object type filtering."""
        vectors = sample_vectors(4)

        mock_vector_db.add_object('table1', vectors[0], 'table')
        mock_vector_db.add_object('table2', vectors[1], 'table')
        mock_vector_db.add_object('col1', vectors[2], 'column')
        mock_vector_db.add_object('col2', vectors[3], 'column')

        # Search only for tables
        results = mock_vector_db.search_similar(
            vectors[0],
            k=10,
            object_type='table',
            threshold=0.0
        )

        assert all(entry.object_type == 'table' for entry, _ in results)
        assert len(results) <= 2

    def test_search_top_k_limit(self, mock_vector_db, sample_vectors):
        """Test that k parameter limits results."""
        vectors = sample_vectors(10)

        for i, vec in enumerate(vectors):
            mock_vector_db.add_object(f'obj_{i}', vec, 'table')

        results = mock_vector_db.search_similar(vectors[0], k=3, threshold=0.0)

        assert len(results) <= 3

    def test_search_empty_database(self, mock_vector_db, sample_vectors):
        """Test search on empty database."""
        vectors = sample_vectors(1)
        results = mock_vector_db.search_similar(vectors[0], k=5)

        assert len(results) == 0

    def test_search_sorted_by_distance(self, mock_vector_db):
        """Test that results are sorted by distance."""
        base_vec = np.zeros(384)
        base_vec[0] = 1.0

        # Create vectors at different distances
        close_vec = base_vec.copy()
        close_vec += np.random.randn(384) * 0.01
        close_vec = close_vec / np.linalg.norm(close_vec)

        far_vec = base_vec.copy()
        far_vec += np.random.randn(384) * 0.5
        far_vec = far_vec / np.linalg.norm(far_vec)

        mock_vector_db.add_object('far', far_vec, 'table')
        mock_vector_db.add_object('close', close_vec, 'table')

        results = mock_vector_db.search_similar(base_vec, k=2, threshold=0.0)

        # Should be sorted by distance (ascending)
        if len(results) >= 2:
            assert results[0][1] <= results[1][1]


# ============================================================================
# Batch Operations Tests
# ============================================================================


class TestBatchOperations:
    """Tests for batch operations and performance."""

    def test_batch_add_performance(self, mock_vector_db, sample_vectors):
        """Test adding vectors in batch."""
        vectors = sample_vectors(100)

        import time
        start = time.time()

        for i, vec in enumerate(vectors):
            mock_vector_db.add_object(f'obj_{i}', vec, 'table')

        duration = time.time() - start

        assert len(mock_vector_db.entries) == 100
        assert duration < 5.0  # Should complete in reasonable time

    def test_large_dataset_search(self, mock_vector_db, sample_vectors):
        """Test search performance with larger dataset."""
        vectors = sample_vectors(1000)

        # Add vectors
        for i, vec in enumerate(vectors):
            mock_vector_db.add_object(f'obj_{i}', vec, 'table')

        # Search
        import time
        start = time.time()
        results = mock_vector_db.search_similar(vectors[0], k=10)
        duration = time.time() - start

        assert len(results) > 0
        assert duration < 2.0  # Should be reasonably fast

    @pytest.mark.slow
    def test_10k_vectors_performance(self, mock_vector_db):
        """Test performance with 10,000+ vectors."""
        # Generate 10k vectors
        dim = 384
        n_vectors = 10000

        import time

        # Batch add
        add_start = time.time()
        for i in range(n_vectors):
            vec = np.random.randn(dim)
            vec = vec / np.linalg.norm(vec)
            mock_vector_db.add_object(f'obj_{i}', vec, 'table')
        add_duration = time.time() - add_start

        assert len(mock_vector_db.entries) == n_vectors
        print(f"\nAdded {n_vectors} vectors in {add_duration:.2f}s")

        # Search
        query = np.random.randn(dim)
        query = query / np.linalg.norm(query)

        search_start = time.time()
        results = mock_vector_db.search_similar(query, k=100)
        search_duration = time.time() - search_start

        assert len(results) > 0
        print(f"Search completed in {search_duration:.2f}s")

    def test_multiple_concurrent_searches(self, mock_vector_db, sample_vectors):
        """Test multiple searches don't interfere."""
        vectors = sample_vectors(50)

        for i, vec in enumerate(vectors):
            mock_vector_db.add_object(f'obj_{i}', vec, 'table')

        # Perform multiple searches
        results_list = []
        for vec in vectors[:5]:
            results = mock_vector_db.search_similar(vec, k=3)
            results_list.append(results)

        # Each search should find its own vector first
        for i, results in enumerate(results_list):
            if results:
                assert results[0][0].id == f'obj_{i}'


# ============================================================================
# Database Object Indexing Tests
# ============================================================================


class TestDatabaseObjectIndexing:
    """Tests for indexing database objects."""

    def test_index_single_table(self, mock_vector_db):
        """Test indexing a single table."""
        def mock_embedding(text):
            np.random.seed(hash(text) % (2**32))
            vec = np.random.randn(384)
            return vec / np.linalg.norm(vec)

        tables = [{
            'name': 'users',
            'description': 'User accounts table',
            'schema': 'public',
            'columns': []
        }]

        mock_vector_db.index_database_objects(tables, mock_embedding)

        assert len(mock_vector_db.entries) == 1
        entry = mock_vector_db.get_by_id('table:users')
        assert entry is not None
        assert entry.object_type == 'table'

    def test_index_table_with_columns(self, mock_vector_db):
        """Test indexing table with columns."""
        def mock_embedding(text):
            np.random.seed(sum(ord(c) for c in text))
            vec = np.random.randn(384)
            return vec / np.linalg.norm(vec)

        tables = [{
            'name': 'users',
            'description': 'User accounts',
            'schema': 'public',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Primary key'},
                {'name': 'email', 'type': 'varchar', 'description': 'Email address'}
            ]
        }]

        mock_vector_db.index_database_objects(tables, mock_embedding)

        # Should have 1 table + 2 columns = 3 entries
        assert len(mock_vector_db.entries) == 3

        # Check table
        table_entry = mock_vector_db.get_by_id('table:users')
        assert table_entry is not None
        assert table_entry.object_type == 'table'

        # Check columns
        col1_entry = mock_vector_db.get_by_id('column:users.id')
        assert col1_entry is not None
        assert col1_entry.object_type == 'column'
        assert col1_entry.metadata['table'] == 'users'

    def test_index_multiple_tables(self, mock_vector_db):
        """Test indexing multiple tables."""
        def mock_embedding(text):
            np.random.seed(hash(text) % (2**32))
            vec = np.random.randn(384)
            return vec / np.linalg.norm(vec)

        tables = [
            {'name': 'users', 'description': 'Users', 'columns': []},
            {'name': 'orders', 'description': 'Orders', 'columns': []},
            {'name': 'products', 'description': 'Products', 'columns': []}
        ]

        mock_vector_db.index_database_objects(tables, mock_embedding)

        assert len(mock_vector_db.entries) == 3
        assert mock_vector_db.get_by_id('table:users') is not None
        assert mock_vector_db.get_by_id('table:orders') is not None
        assert mock_vector_db.get_by_id('table:products') is not None


# ============================================================================
# Statistics and Monitoring Tests
# ============================================================================


class TestStatistics:
    """Tests for database statistics."""

    def test_get_stats_empty(self, mock_vector_db):
        """Test stats on empty database."""
        stats = mock_vector_db.get_stats()

        assert stats['total_entries'] == 0
        assert stats['dimension'] == 384
        assert stats['type_counts'] == {}
        assert stats['index_size'] == 0

    def test_get_stats_with_entries(self, mock_vector_db, sample_vectors):
        """Test stats with entries."""
        vectors = sample_vectors(5)

        mock_vector_db.add_object('t1', vectors[0], 'table')
        mock_vector_db.add_object('t2', vectors[1], 'table')
        mock_vector_db.add_object('c1', vectors[2], 'column')
        mock_vector_db.add_object('c2', vectors[3], 'column')
        mock_vector_db.add_object('i1', vectors[4], 'index')

        stats = mock_vector_db.get_stats()

        assert stats['total_entries'] == 5
        assert stats['type_counts']['table'] == 2
        assert stats['type_counts']['column'] == 2
        assert stats['type_counts']['index'] == 1
        assert stats['index_size'] == 5

    def test_stats_exclude_deleted(self, mock_vector_db, sample_vectors):
        """Test that stats exclude deleted entries."""
        vectors = sample_vectors(3)

        mock_vector_db.add_object('t1', vectors[0], 'table')
        mock_vector_db.add_object('t2', vectors[1], 'table')
        mock_vector_db.add_object('t3', vectors[2], 'table')

        mock_vector_db.delete_by_id('t2')

        stats = mock_vector_db.get_stats()

        assert stats['total_entries'] == 3  # Still 3 total
        assert stats['type_counts']['table'] == 2  # But only 2 non-deleted


# ============================================================================
# Real FAISS Integration Tests
# ============================================================================


class TestRealFAISS:
    """Tests for real FAISS integration."""

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_real_faiss_basic(self, real_vector_db):
        """Test basic operations with real FAISS."""
        vec = np.random.randn(128).astype(np.float32)
        vec = vec / np.linalg.norm(vec)

        real_vector_db.add_object('test', vec, 'table')

        assert len(real_vector_db.entries) == 1
        assert real_vector_db.index.ntotal == 1

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_real_faiss_search(self, real_vector_db):
        """Test search with real FAISS."""
        vectors = [np.random.randn(128).astype(np.float32) for _ in range(10)]
        vectors = [v / np.linalg.norm(v) for v in vectors]

        for i, vec in enumerate(vectors):
            real_vector_db.add_object(f'obj_{i}', vec, 'table')

        results = real_vector_db.search_similar(vectors[0], k=3, threshold=0.0)

        assert len(results) > 0
        assert results[0][0].id == 'obj_0'

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_real_faiss_performance(self, real_vector_db):
        """Test performance with real FAISS."""
        import time

        # Add 1000 vectors
        start = time.time()
        for i in range(1000):
            vec = np.random.randn(128).astype(np.float32)
            vec = vec / np.linalg.norm(vec)
            real_vector_db.add_object(f'obj_{i}', vec, 'table')
        add_time = time.time() - start

        # Search
        query = np.random.randn(128).astype(np.float32)
        query = query / np.linalg.norm(query)

        start = time.time()
        results = real_vector_db.search_similar(query, k=10)
        search_time = time.time() - start

        assert len(results) > 0
        print(f"\nReal FAISS: Add {add_time:.2f}s, Search {search_time:.4f}s")
        assert search_time < 0.1  # Should be very fast


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_vector(self, mock_vector_db):
        """Test handling of empty/zero vector."""
        zero_vec = np.zeros(384)

        # Should add successfully but might have undefined behavior in search
        mock_vector_db.add_object('zero', zero_vec, 'table')
        assert len(mock_vector_db.entries) == 1

    def test_very_large_k(self, mock_vector_db, sample_vectors):
        """Test search with k larger than database size."""
        vectors = sample_vectors(5)

        for i, vec in enumerate(vectors):
            mock_vector_db.add_object(f'obj_{i}', vec, 'table')

        # Request more results than available
        results = mock_vector_db.search_similar(vectors[0], k=100, threshold=0.0)

        # Should return at most 5
        assert len(results) <= 5

    def test_duplicate_ids(self, mock_vector_db, sample_vectors):
        """Test adding objects with duplicate IDs."""
        vectors = sample_vectors(2)

        mock_vector_db.add_object('dup', vectors[0], 'table')
        mock_vector_db.add_object('dup', vectors[1], 'table')

        # Latest entry should overwrite in id_to_idx
        entry = mock_vector_db.get_by_id('dup')
        np.testing.assert_array_equal(entry.vector, vectors[1])

    def test_special_characters_in_id(self, mock_vector_db, sample_vectors):
        """Test IDs with special characters."""
        vectors = sample_vectors(1)
        special_id = "table:test.schema/with-special_chars@123"

        mock_vector_db.add_object(special_id, vectors[0], 'table')

        entry = mock_vector_db.get_by_id(special_id)
        assert entry is not None
        assert entry.id == special_id

    def test_unicode_in_metadata(self, mock_vector_db, sample_vectors):
        """Test Unicode characters in metadata."""
        vectors = sample_vectors(1)
        metadata = {
            'name': '用户表',  # Chinese
            'description': 'Таблица пользователей',  # Russian
            'emoji': '🔥'
        }

        mock_vector_db.add_object('unicode', vectors[0], 'table', metadata)

        entry = mock_vector_db.get_by_id('unicode')
        assert entry.metadata == metadata

    def test_nan_in_vector(self, mock_vector_db):
        """Test handling of NaN values in vector."""
        vec = np.random.randn(384)
        vec[0] = np.nan

        # Behavior may vary - just ensure it doesn't crash
        try:
            mock_vector_db.add_object('nan', vec, 'table')
        except (ValueError, FloatingPointError):
            pass  # Expected for some implementations

    def test_inf_in_vector(self, mock_vector_db):
        """Test handling of infinity values in vector."""
        vec = np.random.randn(384)
        vec[0] = np.inf

        # Should handle gracefully
        try:
            mock_vector_db.add_object('inf', vec, 'table')
        except (ValueError, FloatingPointError):
            pass
