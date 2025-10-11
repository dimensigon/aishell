"""Simplified tests for EmbeddingModel without external dependencies"""

import pytest
from unittest.mock import Mock, MagicMock
import sys
import numpy as np


def test_embedding_model_mock_mode_initialization():
    """Test initialization in mock mode when sentence-transformers unavailable"""
    from src.llm.embeddings import EmbeddingModel

    embedding_model = EmbeddingModel()
    result = embedding_model.initialize()

    assert result is True
    assert embedding_model.initialized is True
    assert embedding_model.model is not None


def test_encode_texts_in_mock_mode():
    """Test encoding texts in mock mode"""
    from src.llm.embeddings import EmbeddingModel

    embedding_model = EmbeddingModel()
    embedding_model.initialize()

    texts = ["Text 1", "Text 2", "Text 3"]
    result = embedding_model.encode(texts)

    assert isinstance(result, np.ndarray)
    assert result.shape[0] == 3
    assert result.shape[1] > 0  # Has embedding dimension


def test_encode_single_text_in_mock_mode():
    """Test encoding single text in mock mode"""
    from src.llm.embeddings import EmbeddingModel

    embedding_model = EmbeddingModel()
    embedding_model.initialize()

    result = embedding_model.encode("Single text")

    assert isinstance(result, np.ndarray)
    assert result.shape[0] == 1


def test_similarity_calculation():
    """Test cosine similarity calculation"""
    from src.llm.embeddings import EmbeddingModel

    embedding_model = EmbeddingModel()
    embedding_model.initialize()

    similarity = embedding_model.similarity("Hello world", "Hello there")

    assert isinstance(similarity, float)
    assert -1.0 <= similarity <= 1.0


def test_find_most_similar():
    """Test finding most similar texts"""
    from src.llm.embeddings import EmbeddingModel

    embedding_model = EmbeddingModel()
    embedding_model.initialize()

    query = "SELECT * FROM users"
    candidates = [
        "SELECT id FROM users",
        "INSERT INTO products",
        "SELECT name FROM users"
    ]

    results = embedding_model.find_most_similar(query, candidates, top_k=2)

    assert len(results) == 2
    assert all(isinstance(r, tuple) for r in results)
    assert all(len(r) == 2 for r in results)
    # Check results are sorted by similarity
    assert results[0][1] >= results[1][1]


def test_find_most_similar_empty_candidates():
    """Test find_most_similar with empty candidate list"""
    from src.llm.embeddings import EmbeddingModel

    embedding_model = EmbeddingModel()
    embedding_model.initialize()

    results = embedding_model.find_most_similar("Query", [], top_k=5)

    assert results == []


def test_find_most_similar_respects_top_k():
    """Test that top_k parameter is respected"""
    from src.llm.embeddings import EmbeddingModel

    embedding_model = EmbeddingModel()
    embedding_model.initialize()

    query = "Test query"
    candidates = ["Candidate " + str(i) for i in range(10)]

    results = embedding_model.find_most_similar(query, candidates, top_k=3)

    assert len(results) == 3


def test_encode_not_initialized():
    """Test error when encoding without initialization"""
    from src.llm.embeddings import EmbeddingModel

    embedding_model = EmbeddingModel()

    with pytest.raises(RuntimeError, match="not initialized"):
        embedding_model.encode("Test text")


def test_cleanup():
    """Test cleanup of resources"""
    from src.llm.embeddings import EmbeddingModel

    embedding_model = EmbeddingModel()
    embedding_model.initialize()

    assert embedding_model.initialized is True
    assert embedding_model.model is not None

    embedding_model.cleanup()

    assert embedding_model.initialized is False
    assert embedding_model.model is None


def test_custom_model_name_and_path():
    """Test initialization with custom model name and path"""
    from src.llm.embeddings import EmbeddingModel

    custom_model = "custom-embedding-model"
    custom_path = "/custom/path"

    embedding_model = EmbeddingModel(model_name=custom_model, model_path=custom_path)

    assert embedding_model.model_name == custom_model
    assert embedding_model.model_path == custom_path


def test_batch_encoding():
    """Test batch encoding with custom batch size"""
    from src.llm.embeddings import EmbeddingModel

    embedding_model = EmbeddingModel()
    embedding_model.initialize()

    texts = ["Text " + str(i) for i in range(10)]
    result = embedding_model.encode(texts, batch_size=3)

    assert isinstance(result, np.ndarray)
    assert result.shape[0] == 10
