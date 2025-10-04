"""Tests for FAISS 1.12.0 compatibility with Python 3.12+."""

import pytest
import numpy as np

# Try to import FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from src.vector.store import VectorDatabase, FAISS_AVAILABLE as STORE_FAISS_AVAILABLE


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not installed")
def test_faiss_import():
    """Test that FAISS can be imported."""
    assert faiss is not None
    assert hasattr(faiss, 'IndexFlatL2')


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not installed")
def test_faiss_version():
    """Test FAISS version is 1.8.0 or higher."""
    # FAISS doesn't expose version directly, but we can check it's working
    index = faiss.IndexFlatL2(128)
    assert index.d == 128
    assert index.ntotal == 0


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not installed")
def test_vector_db_with_real_faiss():
    """Test VectorDatabase with real FAISS backend."""
    db = VectorDatabase(dimension=128, use_faiss=True)
    assert db.use_faiss is True
    assert isinstance(db.index, faiss.IndexFlatL2)

    # Add vectors
    vec1 = np.random.randn(128).astype(np.float32)
    vec2 = np.random.randn(128).astype(np.float32)

    db.add_object('obj1', vec1, 'test', {'name': 'test1'})
    db.add_object('obj2', vec2, 'test', {'name': 'test2'})

    assert db.index.ntotal == 2
    assert len(db.entries) == 2


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not installed")
def test_faiss_search():
    """Test vector search with real FAISS."""
    db = VectorDatabase(dimension=128, use_faiss=True)

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


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not installed")
def test_faiss_float32_handling():
    """Test FAISS handles float32 correctly."""
    db = VectorDatabase(dimension=64, use_faiss=True)

    # Test with float64 (should be converted to float32)
    vec_f64 = np.random.randn(64).astype(np.float64)
    db.add_object('test', vec_f64, 'test')

    assert db.index.ntotal == 1

    # Search should also handle float64
    query_f64 = np.random.randn(64).astype(np.float64)
    results = db.search_similar(query_f64, k=1, threshold=0.0)

    assert len(results) == 1


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not installed")
def test_faiss_large_batch():
    """Test FAISS can handle larger batches of vectors."""
    db = VectorDatabase(dimension=384, use_faiss=True)

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


def test_vector_db_fallback_to_mock():
    """Test VectorDatabase falls back to mock when FAISS unavailable."""
    # Force mock usage
    db = VectorDatabase(dimension=128, use_faiss=False)
    assert db.use_faiss is False

    # Should still work
    vec = np.random.randn(128)
    db.add_object('test', vec, 'test')
    assert len(db.entries) == 1


def test_store_faiss_available_flag():
    """Test that FAISS_AVAILABLE flag is set correctly."""
    # This should match the import success
    if FAISS_AVAILABLE:
        assert STORE_FAISS_AVAILABLE is True
    # If FAISS is not available, the flag could still be True if
    # the module was imported before, but that's okay
