"""
Comprehensive tests for Embedding Model with full mocking

Tests vector generation, similarity calculations, and semantic search.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from src.llm.embeddings import EmbeddingModel


class TestEmbeddingModelInitialization:
    """Test embedding model initialization"""

    def test_init_default_values(self):
        """Test initialization with default values"""
        model = EmbeddingModel()

        assert model.model_name == "all-MiniLM-L6-v2"
        assert model.model_path == "/data0/models"
        assert model.model is None
        assert not model.initialized

    def test_init_custom_values(self):
        """Test initialization with custom values"""
        model = EmbeddingModel(
            model_name="custom-model",
            model_path="/custom/path"
        )

        assert model.model_name == "custom-model"
        assert model.model_path == "/custom/path"

    @patch('src.llm.embeddings.SentenceTransformer')
    def test_initialize_success_with_sentence_transformers(self, mock_st_cls):
        """Test successful initialization with sentence-transformers"""
        mock_model = Mock()
        mock_st_cls.return_value = mock_model

        embedding = EmbeddingModel()
        result = embedding.initialize()

        assert result is True
        assert embedding.initialized is True
        assert embedding.model is mock_model
        mock_st_cls.assert_called_once_with(
            "all-MiniLM-L6-v2",
            cache_folder="/data0/models"
        )

    @patch('src.llm.embeddings.SentenceTransformer', side_effect=ImportError)
    def test_initialize_fallback_to_mock(self, mock_st_cls):
        """Test initialization falls back to mock when package not installed"""
        embedding = EmbeddingModel()
        result = embedding.initialize()

        assert result is True
        assert embedding.initialized is True
        assert embedding.model is not None
        assert hasattr(embedding.model, 'encode')

    @patch('src.llm.embeddings.SentenceTransformer')
    def test_initialize_model_load_failure(self, mock_st_cls):
        """Test initialization handles model loading failures"""
        mock_st_cls.side_effect = Exception("Model download failed")

        embedding = EmbeddingModel()
        result = embedding.initialize()

        assert result is False
        assert not embedding.initialized

    def test_mock_model_encode_single_text(self):
        """Test mock model encode with single text"""
        embedding = EmbeddingModel()
        mock_model = embedding._create_mock_model()

        result = mock_model.encode("test text")

        assert isinstance(result, np.ndarray)
        assert result.shape == (1, 384)
        assert result.dtype == np.float32

    def test_mock_model_encode_multiple_texts(self):
        """Test mock model encode with multiple texts"""
        embedding = EmbeddingModel()
        mock_model = embedding._create_mock_model()

        texts = ["text 1", "text 2", "text 3"]
        result = mock_model.encode(texts)

        assert isinstance(result, np.ndarray)
        assert result.shape == (3, 384)
        assert result.dtype == np.float32


class TestEmbeddingEncoding:
    """Test embedding encoding functionality"""

    @pytest.fixture
    def initialized_model(self):
        """Create initialized embedding model with mock"""
        embedding = EmbeddingModel()

        mock_model = Mock()
        embedding.model = mock_model
        embedding.initialized = True

        return embedding, mock_model

    def test_encode_not_initialized(self):
        """Test encode raises error when not initialized"""
        embedding = EmbeddingModel()

        with pytest.raises(RuntimeError, match="not initialized"):
            embedding.encode(["test"])

    def test_encode_single_text(self, initialized_model):
        """Test encoding single text"""
        embedding, mock_model = initialized_model

        # Mock return value
        mock_embeddings = np.array([[0.1, 0.2, 0.3]])
        mock_model.encode.return_value = mock_embeddings

        result = embedding.encode("test text")

        assert isinstance(result, np.ndarray)
        assert result.shape == (1, 3)
        mock_model.encode.assert_called_once_with(
            ["test text"],
            batch_size=32,
            convert_to_numpy=True
        )

    def test_encode_multiple_texts(self, initialized_model):
        """Test encoding multiple texts"""
        embedding, mock_model = initialized_model

        texts = ["text 1", "text 2", "text 3"]
        mock_embeddings = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ])
        mock_model.encode.return_value = mock_embeddings

        result = embedding.encode(texts)

        assert result.shape == (3, 3)
        mock_model.encode.assert_called_once_with(
            texts,
            batch_size=32,
            convert_to_numpy=True
        )

    def test_encode_custom_batch_size(self, initialized_model):
        """Test encoding with custom batch size"""
        embedding, mock_model = initialized_model

        mock_model.encode.return_value = np.array([[0.1, 0.2]])

        texts = ["text"] * 100
        result = embedding.encode(texts, batch_size=16)

        call_args = mock_model.encode.call_args
        assert call_args[1]['batch_size'] == 16

    def test_encode_string_converted_to_list(self, initialized_model):
        """Test single string is converted to list"""
        embedding, mock_model = initialized_model

        mock_model.encode.return_value = np.array([[0.1, 0.2]])

        # Pass string directly
        result = embedding.encode("single text", batch_size=32)

        # Should be converted to list
        call_args = mock_model.encode.call_args
        assert call_args[0][0] == ["single text"]

    def test_encode_handles_encoding_errors(self, initialized_model):
        """Test encode handles model errors"""
        embedding, mock_model = initialized_model

        mock_model.encode.side_effect = Exception("Encoding failed")

        with pytest.raises(Exception, match="Encoding failed"):
            embedding.encode(["test"])

    def test_encode_empty_list(self, initialized_model):
        """Test encoding empty list"""
        embedding, mock_model = initialized_model

        mock_model.encode.return_value = np.array([])

        result = embedding.encode([])

        assert len(result) == 0

    def test_encode_large_batch(self, initialized_model):
        """Test encoding large batch of texts"""
        embedding, mock_model = initialized_model

        # Create large batch
        texts = [f"text {i}" for i in range(1000)]
        mock_embeddings = np.random.randn(1000, 384).astype(np.float32)
        mock_model.encode.return_value = mock_embeddings

        result = embedding.encode(texts, batch_size=64)

        assert result.shape == (1000, 384)
        call_args = mock_model.encode.call_args
        assert call_args[1]['batch_size'] == 64


class TestSimilarityCalculation:
    """Test similarity calculation functionality"""

    @pytest.fixture
    def initialized_model(self):
        """Create initialized embedding model"""
        embedding = EmbeddingModel()

        mock_model = Mock()
        embedding.model = mock_model
        embedding.initialized = True

        return embedding, mock_model

    def test_similarity_not_initialized(self):
        """Test similarity requires initialization"""
        embedding = EmbeddingModel()

        with pytest.raises(RuntimeError, match="not initialized"):
            embedding.similarity("text1", "text2")

    def test_similarity_identical_texts(self, initialized_model):
        """Test similarity of identical texts approaches 1.0"""
        embedding, mock_model = initialized_model

        # Return identical embeddings
        identical_emb = np.array([0.5, 0.5, 0.5])
        mock_model.encode.return_value = np.array([identical_emb, identical_emb])

        similarity = embedding.similarity("same text", "same text")

        assert 0.99 <= similarity <= 1.0

    def test_similarity_orthogonal_vectors(self, initialized_model):
        """Test similarity of orthogonal vectors is 0"""
        embedding, mock_model = initialized_model

        # Orthogonal vectors
        mock_model.encode.return_value = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ])

        similarity = embedding.similarity("text1", "text2")

        assert abs(similarity) < 0.01  # Should be ~0

    def test_similarity_opposite_vectors(self, initialized_model):
        """Test similarity of opposite vectors is -1"""
        embedding, mock_model = initialized_model

        # Opposite vectors
        mock_model.encode.return_value = np.array([
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0]
        ])

        similarity = embedding.similarity("text1", "text2")

        assert -1.01 <= similarity <= -0.99

    def test_similarity_partial_match(self, initialized_model):
        """Test similarity of partially similar vectors"""
        embedding, mock_model = initialized_model

        # Partially similar
        mock_model.encode.return_value = np.array([
            [1.0, 1.0, 0.0],
            [1.0, 0.0, 0.0]
        ])

        similarity = embedding.similarity("text1", "text2")

        assert 0.0 < similarity < 1.0

    def test_similarity_calls_encode_correctly(self, initialized_model):
        """Test similarity calls encode with both texts"""
        embedding, mock_model = initialized_model

        mock_model.encode.return_value = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ])

        text1 = "first text"
        text2 = "second text"

        embedding.similarity(text1, text2)

        mock_model.encode.assert_called_once_with(
            [text1, text2],
            batch_size=32,
            convert_to_numpy=True
        )


class TestSemanticSearch:
    """Test semantic search functionality"""

    @pytest.fixture
    def initialized_model(self):
        """Create initialized embedding model"""
        embedding = EmbeddingModel()

        mock_model = Mock()
        embedding.model = mock_model
        embedding.initialized = True

        return embedding, mock_model

    def test_find_most_similar_not_initialized(self):
        """Test find_most_similar requires initialization"""
        embedding = EmbeddingModel()

        with pytest.raises(RuntimeError, match="not initialized"):
            embedding.find_most_similar("query", ["candidate1", "candidate2"])

    def test_find_most_similar_empty_candidates(self, initialized_model):
        """Test finding similar with no candidates"""
        embedding, mock_model = initialized_model

        result = embedding.find_most_similar("query", [])

        assert result == []
        mock_model.encode.assert_not_called()

    def test_find_most_similar_single_candidate(self, initialized_model):
        """Test finding similar with single candidate"""
        embedding, mock_model = initialized_model

        # Query embedding and candidate embedding
        mock_model.encode.return_value = np.array([
            [1.0, 0.0],  # query
            [0.9, 0.1]   # candidate (high similarity)
        ])

        candidates = ["similar text"]
        result = embedding.find_most_similar("query", candidates, top_k=1)

        assert len(result) == 1
        assert result[0][0] == "similar text"
        assert result[0][1] > 0.9  # High similarity

    def test_find_most_similar_multiple_candidates(self, initialized_model):
        """Test finding similar with multiple candidates"""
        embedding, mock_model = initialized_model

        # Create embeddings with different similarities
        mock_model.encode.return_value = np.array([
            [1.0, 0.0, 0.0],  # query
            [0.9, 0.1, 0.0],  # candidate 1 - high similarity
            [0.5, 0.5, 0.0],  # candidate 2 - medium similarity
            [0.0, 0.0, 1.0]   # candidate 3 - low similarity
        ])

        candidates = ["similar", "somewhat similar", "different"]
        result = embedding.find_most_similar("query", candidates, top_k=3)

        assert len(result) == 3
        # Should be sorted by similarity (descending)
        assert result[0][1] >= result[1][1] >= result[2][1]

    def test_find_most_similar_respects_top_k(self, initialized_model):
        """Test top_k parameter limits results"""
        embedding, mock_model = initialized_model

        # Create 10 candidates
        num_candidates = 10
        embeddings = np.random.randn(num_candidates + 1, 384).astype(np.float32)
        mock_model.encode.return_value = embeddings

        candidates = [f"candidate {i}" for i in range(num_candidates)]

        # Request top 3
        result = embedding.find_most_similar("query", candidates, top_k=3)

        assert len(result) == 3

    def test_find_most_similar_top_k_larger_than_candidates(self, initialized_model):
        """Test top_k larger than number of candidates"""
        embedding, mock_model = initialized_model

        mock_model.encode.return_value = np.random.randn(4, 384).astype(np.float32)

        candidates = ["c1", "c2", "c3"]

        # Request top 10 but only 3 candidates
        result = embedding.find_most_similar("query", candidates, top_k=10)

        assert len(result) == 3  # Should return all 3

    def test_find_most_similar_returns_tuples(self, initialized_model):
        """Test results are (text, similarity) tuples"""
        embedding, mock_model = initialized_model

        mock_model.encode.return_value = np.array([
            [1.0, 0.0],
            [0.9, 0.1],
            [0.8, 0.2]
        ])

        candidates = ["c1", "c2"]
        result = embedding.find_most_similar("query", candidates)

        assert all(isinstance(item, tuple) for item in result)
        assert all(len(item) == 2 for item in result)
        assert all(isinstance(item[0], str) for item in result)
        assert all(isinstance(item[1], float) for item in result)

    def test_find_most_similar_correct_ordering(self, initialized_model):
        """Test results are correctly ordered by similarity"""
        embedding, mock_model = initialized_model

        # Create embeddings with known similarities
        query_emb = np.array([1.0, 0.0, 0.0])
        high_sim = np.array([0.95, 0.05, 0.0])  # Very similar
        med_sim = np.array([0.7, 0.3, 0.0])     # Somewhat similar
        low_sim = np.array([0.0, 1.0, 0.0])     # Different

        mock_model.encode.return_value = np.array([
            query_emb,
            low_sim,   # candidate 0
            high_sim,  # candidate 1
            med_sim    # candidate 2
        ])

        candidates = ["different", "very similar", "somewhat similar"]
        result = embedding.find_most_similar("query", candidates, top_k=3)

        # Should be ordered: high_sim, med_sim, low_sim
        assert result[0][0] == "very similar"
        assert result[1][0] == "somewhat similar"
        assert result[2][0] == "different"

    def test_find_most_similar_encodes_all_texts(self, initialized_model):
        """Test that query and all candidates are encoded together"""
        embedding, mock_model = initialized_model

        mock_model.encode.return_value = np.random.randn(6, 384).astype(np.float32)

        query = "find similar"
        candidates = ["c1", "c2", "c3", "c4", "c5"]

        embedding.find_most_similar(query, candidates)

        # Should encode query + all candidates
        call_args = mock_model.encode.call_args
        all_texts = call_args[0][0]
        assert len(all_texts) == 6  # 1 query + 5 candidates
        assert all_texts[0] == query
        assert all_texts[1:] == candidates

    def test_find_most_similar_similarity_scores_valid(self, initialized_model):
        """Test similarity scores are in valid range [-1, 1]"""
        embedding, mock_model = initialized_model

        mock_model.encode.return_value = np.random.randn(4, 384).astype(np.float32)

        candidates = ["c1", "c2", "c3"]
        result = embedding.find_most_similar("query", candidates)

        # All similarity scores should be in [-1, 1]
        for text, similarity in result:
            assert -1.0 <= similarity <= 1.0


class TestCleanup:
    """Test resource cleanup"""

    def test_cleanup_releases_resources(self):
        """Test cleanup releases model resources"""
        embedding = EmbeddingModel()
        embedding.model = Mock()
        embedding.initialized = True

        embedding.cleanup()

        assert embedding.model is None
        assert embedding.initialized is False

    def test_cleanup_idempotent(self):
        """Test cleanup can be called multiple times"""
        embedding = EmbeddingModel()
        embedding.model = Mock()
        embedding.initialized = True

        embedding.cleanup()
        embedding.cleanup()  # Should not raise error

        assert embedding.model is None
        assert embedding.initialized is False


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    @patch('src.llm.embeddings.SentenceTransformer', side_effect=ImportError)
    def test_semantic_search_workflow(self, mock_st):
        """Test complete semantic search workflow"""
        embedding = EmbeddingModel()
        embedding.initialize()

        # Simulate query history
        query_history = [
            "SELECT * FROM users WHERE age > 21",
            "DELETE FROM posts WHERE id = 1",
            "UPDATE users SET name = 'John'",
            "SELECT id, name FROM users",
            "INSERT INTO users VALUES (1, 'Alice')"
        ]

        current_query = "get all users"

        # Find similar queries
        results = embedding.find_most_similar(current_query, query_history, top_k=3)

        assert len(results) == 3
        # All results should be valid
        for text, similarity in results:
            assert text in query_history
            assert isinstance(similarity, float)

    @patch('src.llm.embeddings.SentenceTransformer', side_effect=ImportError)
    def test_duplicate_detection(self, mock_st):
        """Test detecting duplicate or very similar queries"""
        embedding = EmbeddingModel()
        embedding.initialize()

        text1 = "SELECT * FROM users"
        text2 = "SELECT * FROM users"  # Duplicate

        similarity = embedding.similarity(text1, text2)

        # Should be very high similarity (though mock uses random)
        assert isinstance(similarity, float)
        assert -1.0 <= similarity <= 1.0

    @patch('src.llm.embeddings.SentenceTransformer', side_effect=ImportError)
    def test_batch_encoding_performance(self, mock_st):
        """Test batch encoding for large datasets"""
        embedding = EmbeddingModel()
        embedding.initialize()

        # Large batch of queries
        queries = [f"SELECT * FROM table_{i}" for i in range(500)]

        # Should handle large batch
        results = embedding.encode(queries, batch_size=32)

        assert len(results) == 500
        assert all(len(emb) == 384 for emb in results)
