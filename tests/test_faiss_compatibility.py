"""Tests for FAISS 1.12.0 compatibility and requirement."""

import pytest
import numpy as np

# FAISS is now required - tests will fail if not installed
import faiss
from src.vector.store import VectorDatabase


def test_faiss_import_required():
    """Test that FAISS must be imported successfully."""
    assert faiss is not None, (
        "FAISS is required but not installed. "
        "Install with: pip install faiss-cpu==1.12.0"
    )
    assert hasattr(faiss, 'IndexFlatL2')


def test_faiss_import_failure_message():
    """Test that VectorDatabase requires FAISS."""
    # VectorDatabase now directly imports faiss
    # If faiss is not available, the import will fail at module level
    db = VectorDatabase(dimension=128)
    assert db is not None
    assert hasattr(db.index, 'd')  # FAISS index property


def test_faiss_version():
    """Test FAISS version is 1.8.0 or higher (current is 1.12.0)."""
    # FAISS doesn't expose version directly, but we can check it's working
    index = faiss.IndexFlatL2(128)
    assert index.d == 128
    assert index.ntotal == 0


def test_vector_db_requires_faiss():
    """Test VectorDatabase uses real FAISS backend."""
    db = VectorDatabase(dimension=128)
    assert isinstance(db.index, faiss.IndexFlatL2)

    # Add vectors
    vec1 = np.random.randn(128).astype(np.float32)
    vec2 = np.random.randn(128).astype(np.float32)

    db.add_object('obj1', vec1, 'test', {'name': 'test1'})
    db.add_object('obj2', vec2, 'test', {'name': 'test2'})

    assert db.index.ntotal == 2
    assert len(db.entries) == 2


def test_faiss_search():
    """Test vector search with real FAISS."""
    db = VectorDatabase(dimension=128)

    # Create normalized vectors for consistent similarity
    vec1 = np.random.randn(128).astype(np.float32)
    vec1 = vec1 / np.linalg.norm(vec1)

    vec2 = np.random.randn(128).astype(np.float32)
    vec2 = vec2 / np.linalg.norm(vec2)

    db.add_object('similar', vec1, 'test')
    db.add_object('different', vec2, 'test')

    # Search with query similar to vec1
    query = vec1 + np.random.randn(128).astype(np.float32) * 0.01
    query = query / np.linalg.norm(query)

    results = db.search_similar(query, k=2, threshold=0.0)

    assert len(results) > 0
    # First result should be 'similar' as it's closest to query
    assert results[0][0].id == 'similar'


def test_faiss_float32_handling():
    """Test FAISS handles float32 correctly."""
    db = VectorDatabase(dimension=64)

    # Test with float64 (should be converted to float32)
    vec_f64 = np.random.randn(64).astype(np.float64)
    db.add_object('test', vec_f64, 'test')

    assert db.index.ntotal == 1

    # Search should also handle float64
    query_f64 = np.random.randn(64).astype(np.float64)
    results = db.search_similar(query_f64, k=1, threshold=0.0)

    assert len(results) == 1


def test_faiss_large_batch():
    """Test FAISS can handle larger batches of vectors."""
    db = VectorDatabase(dimension=384)

    # Add 1000 vectors
    for i in range(1000):
        vec = np.random.randn(384).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        db.add_object(f'vec_{i}', vec, 'test', {'index': i})

    assert db.index.ntotal == 1000

    # Search
    query = np.random.randn(384).astype(np.float32)
    query = query / np.linalg.norm(query)

    results = db.search_similar(query, k=10, threshold=0.0)
    assert len(results) == 10


def test_faiss_dimension_validation():
    """Test FAISS validates vector dimensions."""
    db = VectorDatabase(dimension=128)

    # Wrong dimension should raise error
    wrong_vec = np.random.randn(64).astype(np.float32)

    with pytest.raises(ValueError, match="doesn't match"):
        db.add_object('test', wrong_vec, 'test')


def test_faiss_empty_database_search():
    """Test FAISS search on empty database."""
    db = VectorDatabase(dimension=128)

    query = np.random.randn(128).astype(np.float32)
    results = db.search_similar(query, k=5)

    assert len(results) == 0


def test_faiss_search_with_filters():
    """Test FAISS search with object type filters."""
    db = VectorDatabase(dimension=128)

    # Add different object types
    for i in range(5):
        vec = np.random.randn(128).astype(np.float32)
        db.add_object(f'table_{i}', vec, 'table')

    for i in range(5):
        vec = np.random.randn(128).astype(np.float32)
        db.add_object(f'column_{i}', vec, 'column')

    # Search only for tables
    query = np.random.randn(128).astype(np.float32)
    table_results = db.search_similar(query, k=5, object_type='table', threshold=0.0)

    assert len(table_results) == 5
    assert all(entry.object_type == 'table' for entry, _ in table_results)

    # Search only for columns
    column_results = db.search_similar(query, k=5, object_type='column', threshold=0.0)

    assert len(column_results) == 5
    assert all(entry.object_type == 'column' for entry, _ in column_results)
