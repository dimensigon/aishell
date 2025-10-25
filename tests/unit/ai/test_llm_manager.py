"""
Comprehensive tests for LLM Manager with full mocking

Tests provider selection, failover, caching, and all LLM operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import json
from typing import Dict, Any

from src.llm.manager import (
    LocalLLMManager,
    IntentType,
    LLMConfig,
    ModelType
)
from src.llm.providers import LocalLLMProvider, OllamaProvider


class TestLLMManagerInitialization:
    """Test LLM Manager initialization scenarios"""

    def test_init_default_values(self):
        """Test initialization with default values"""
        manager = LocalLLMManager()

        assert manager.model_path == "/data0/models"
        assert manager.provider is None
        assert manager.embedding_model is not None
        assert not manager.initialized
        assert manager.anonymization_map == {}
        assert manager.reverse_map == {}

    def test_init_custom_provider(self):
        """Test initialization with custom provider"""
        mock_provider = Mock(spec=LocalLLMProvider)
        manager = LocalLLMManager(provider=mock_provider)

        assert manager.provider is mock_provider

    @patch('src.llm.manager.OllamaProvider')
    @patch('src.llm.manager.EmbeddingModel')
    def test_initialize_ollama_success(self, mock_embedding_cls, mock_provider_cls):
        """Test successful initialization with Ollama provider"""
        # Mock provider initialization
        mock_provider = Mock()
        mock_provider.initialize.return_value = True
        mock_provider_cls.return_value = mock_provider

        # Mock embedding model initialization
        mock_embedding = Mock()
        mock_embedding.initialize.return_value = True
        mock_embedding_cls.return_value = mock_embedding

        manager = LocalLLMManager()
        result = manager.initialize(provider_type="ollama", model_name="llama2")

        assert result is True
        assert manager.initialized is True
        mock_provider_cls.assert_called_once()
        mock_provider.initialize.assert_called_once()

    @patch('src.llm.manager.OllamaProvider')
    @patch('src.llm.manager.EmbeddingModel')
    def test_initialize_provider_failure(self, mock_embedding_cls, mock_provider_cls):
        """Test initialization failure when provider fails"""
        mock_provider = Mock()
        mock_provider.initialize.return_value = False
        mock_provider_cls.return_value = mock_provider

        mock_embedding = Mock()
        mock_embedding.initialize.return_value = True
        mock_embedding_cls.return_value = mock_embedding

        manager = LocalLLMManager()
        result = manager.initialize(provider_type="ollama")

        assert result is False
        assert manager.initialized is False

    @patch('src.llm.manager.OllamaProvider')
    @patch('src.llm.manager.EmbeddingModel')
    def test_initialize_embedding_failure(self, mock_embedding_cls, mock_provider_cls):
        """Test initialization failure when embedding fails"""
        mock_provider = Mock()
        mock_provider.initialize.return_value = True
        mock_provider_cls.return_value = mock_provider

        mock_embedding = Mock()
        mock_embedding.initialize.return_value = False
        mock_embedding_cls.return_value = mock_embedding

        manager = LocalLLMManager()
        result = manager.initialize(provider_type="ollama")

        assert result is False
        assert manager.initialized is False

    def test_initialize_unknown_provider(self):
        """Test initialization with unknown provider type"""
        manager = LocalLLMManager()
        result = manager.initialize(provider_type="unknown_provider")

        assert result is False
        assert manager.initialized is False


class TestIntentAnalysis:
    """Test intent analysis functionality"""

    @pytest.fixture
    def initialized_manager(self):
        """Create initialized manager with mocked dependencies"""
        mock_provider = Mock(spec=LocalLLMProvider)
        mock_provider.initialize.return_value = True

        with patch('src.llm.manager.EmbeddingModel') as mock_emb_cls:
            mock_embedding = Mock()
            mock_embedding.initialize.return_value = True
            mock_emb_cls.return_value = mock_embedding

            manager = LocalLLMManager(provider=mock_provider)
            manager.initialize()

            return manager

    def test_analyze_intent_not_initialized(self):
        """Test intent analysis raises error when not initialized"""
        manager = LocalLLMManager()

        with pytest.raises(RuntimeError, match="not initialized"):
            manager.analyze_intent("SELECT * FROM users")

    def test_analyze_intent_select_query(self, initialized_manager):
        """Test intent analysis for SELECT query"""
        result = initialized_manager.analyze_intent("SELECT * FROM users WHERE id = 1")

        assert result['intent'] == IntentType.QUERY.value
        assert result['confidence'] == 0.9
        assert result['metadata']['operation'] == 'read'
        assert 'original_query' in result

    def test_analyze_intent_insert_mutation(self, initialized_manager):
        """Test intent analysis for INSERT mutation"""
        result = initialized_manager.analyze_intent("INSERT INTO users (name) VALUES ('John')")

        assert result['intent'] == IntentType.MUTATION.value
        assert result['confidence'] == 0.9
        assert result['metadata']['operation'] == 'write'

    def test_analyze_intent_performance_query(self, initialized_manager):
        """Test intent analysis for performance optimization"""
        result = initialized_manager.analyze_intent("CREATE INDEX idx_name ON users(name)")

        assert result['intent'] == IntentType.PERFORMANCE.value
        assert result['confidence'] == 0.9
        assert result['metadata']['operation'] == 'optimization'

    def test_analyze_intent_schema_query(self, initialized_manager):
        """Test intent analysis for schema introspection"""
        result = initialized_manager.analyze_intent("DESCRIBE users")

        assert result['intent'] == IntentType.SCHEMA.value
        assert result['confidence'] >= 0.85

    def test_analyze_intent_llm_fallback(self, initialized_manager):
        """Test LLM-based intent analysis for complex queries"""
        # Mock LLM response
        llm_response = json.dumps({
            'intent': 'query',
            'confidence': 0.75,
            'metadata': {'operation': 'complex', 'details': 'Multi-table join'}
        })
        initialized_manager.provider.generate.return_value = llm_response

        result = initialized_manager.analyze_intent("some complex query")

        # Should call LLM for low-confidence queries
        assert 'intent' in result
        assert 'confidence' in result

    def test_analyze_intent_llm_failure(self, initialized_manager):
        """Test LLM intent analysis handles failures gracefully"""
        initialized_manager.provider.generate.side_effect = Exception("LLM error")

        # Should fall back to UNKNOWN with low confidence
        result = initialized_manager.analyze_intent("complex query")

        assert result['intent'] == IntentType.UNKNOWN.value
        assert result['confidence'] < 0.8


class TestAnonymization:
    """Test query anonymization functionality"""

    @pytest.fixture
    def manager(self):
        return LocalLLMManager()

    def test_anonymize_email(self, manager):
        """Test email anonymization"""
        query = "SELECT * FROM users WHERE email = 'john@example.com'"
        anonymized, mapping = manager.anonymize_query(query)

        assert 'john@example.com' not in anonymized
        assert 'EMAIL_' in anonymized
        assert len(mapping) == 1
        assert 'EMAIL_' in list(mapping.keys())[0]

    def test_anonymize_ssn(self, manager):
        """Test SSN anonymization"""
        query = "SELECT * FROM users WHERE ssn = '123-45-6789'"
        anonymized, mapping = manager.anonymize_query(query)

        assert '123-45-6789' not in anonymized
        assert 'SSN_' in anonymized
        assert len(mapping) == 1

    def test_anonymize_multiple_patterns(self, manager):
        """Test multiple pattern anonymization"""
        query = "SELECT * FROM users WHERE email = 'test@test.com' AND phone = '1234567890'"
        anonymized, mapping = manager.anonymize_query(query)

        assert 'test@test.com' not in anonymized
        assert '1234567890' not in anonymized
        assert len(mapping) == 2

    def test_anonymize_consistent_hashing(self, manager):
        """Test consistent hashing for same values"""
        query1 = "SELECT * WHERE email = 'test@test.com'"
        query2 = "SELECT * WHERE email = 'test@test.com'"

        anon1, map1 = manager.anonymize_query(query1)
        anon2, map2 = manager.anonymize_query(query2)

        # Should generate same placeholder for same value
        assert anon1 == anon2

    def test_deanonymize_result(self, manager):
        """Test deanonymization of results"""
        original = "john@example.com"
        query = f"SELECT * WHERE email = '{original}'"

        anonymized, mapping = manager.anonymize_query(query)

        # Simulate anonymized result
        anonymized_result = f"Result: {list(mapping.keys())[0]}"

        deanonymized = manager.deanonymize_result(anonymized_result, mapping)

        assert original in deanonymized
        assert list(mapping.keys())[0] not in deanonymized

    def test_deanonymize_uses_stored_mapping(self, manager):
        """Test deanonymization uses stored mapping when not provided"""
        query = "SELECT * WHERE email = 'test@test.com'"
        anonymized, _ = manager.anonymize_query(query)

        # Don't pass mapping - should use stored one
        placeholder = list(manager.anonymization_map.keys())[0]
        result = f"Result: {placeholder}"

        deanonymized = manager.deanonymize_result(result)

        assert 'test@test.com' in deanonymized


class TestEmbeddings:
    """Test embedding generation and similarity search"""

    @pytest.fixture
    def initialized_manager(self):
        """Create initialized manager"""
        mock_provider = Mock(spec=LocalLLMProvider)
        mock_provider.initialize.return_value = True

        with patch('src.llm.manager.EmbeddingModel') as mock_emb_cls:
            mock_embedding = Mock()
            mock_embedding.initialize.return_value = True
            mock_emb_cls.return_value = mock_embedding

            manager = LocalLLMManager(provider=mock_provider)
            manager.initialize()

            return manager

    def test_generate_embeddings_not_initialized(self):
        """Test embedding generation requires initialization"""
        manager = LocalLLMManager()

        with pytest.raises(RuntimeError, match="not initialized"):
            manager.generate_embeddings(["test query"])

    def test_generate_embeddings_success(self, initialized_manager):
        """Test successful embedding generation"""
        import numpy as np

        # Mock embeddings
        mock_embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        initialized_manager.embedding_model.encode.return_value = mock_embeddings

        texts = ["query 1", "query 2"]
        result = initialized_manager.generate_embeddings(texts)

        assert len(result) == 2
        assert len(result[0]) == 3
        initialized_manager.embedding_model.encode.assert_called_once_with(texts)

    def test_find_similar_queries_not_initialized(self):
        """Test similar query search requires initialization"""
        manager = LocalLLMManager()

        with pytest.raises(RuntimeError, match="not initialized"):
            manager.find_similar_queries("test", ["query1", "query2"])

    def test_find_similar_queries_success(self, initialized_manager):
        """Test finding similar queries"""
        # Mock similarity results
        mock_results = [
            ("SELECT * FROM users", 0.95),
            ("SELECT id FROM users", 0.87)
        ]
        initialized_manager.embedding_model.find_most_similar.return_value = mock_results

        query = "get users"
        history = ["SELECT * FROM users", "SELECT id FROM users", "DELETE FROM posts"]

        result = initialized_manager.find_similar_queries(query, history, top_k=2)

        assert len(result) == 2
        assert result[0][1] > result[1][1]  # Sorted by similarity
        initialized_manager.embedding_model.find_most_similar.assert_called_once()


class TestQueryExplanation:
    """Test query explanation functionality"""

    @pytest.fixture
    def initialized_manager(self):
        """Create initialized manager"""
        mock_provider = Mock(spec=LocalLLMProvider)
        mock_provider.initialize.return_value = True

        with patch('src.llm.manager.EmbeddingModel') as mock_emb_cls:
            mock_embedding = Mock()
            mock_embedding.initialize.return_value = True
            mock_emb_cls.return_value = mock_embedding

            manager = LocalLLMManager(provider=mock_provider)
            manager.initialize()

            return manager

    def test_explain_query_not_initialized(self):
        """Test explanation requires initialization"""
        manager = LocalLLMManager()

        with pytest.raises(RuntimeError, match="not initialized"):
            manager.explain_query("SELECT * FROM users")

    def test_explain_query_success(self, initialized_manager):
        """Test successful query explanation"""
        mock_explanation = "This query retrieves all users from the database"
        initialized_manager.provider.generate.return_value = mock_explanation

        query = "SELECT * FROM users"
        result = initialized_manager.explain_query(query)

        assert result == mock_explanation
        initialized_manager.provider.generate.assert_called_once()

        # Verify prompt contains query
        call_args = initialized_manager.provider.generate.call_args
        assert query in call_args[0][0]

    def test_explain_query_with_context(self, initialized_manager):
        """Test query explanation with context"""
        initialized_manager.provider.generate.return_value = "Explanation with context"

        query = "SELECT * FROM users"
        context = "Table users has columns: id, name, email"

        result = initialized_manager.explain_query(query, context)

        # Verify context is included in prompt
        call_args = initialized_manager.provider.generate.call_args
        assert context in call_args[0][0]

    def test_explain_query_failure(self, initialized_manager):
        """Test explanation handles LLM failures"""
        initialized_manager.provider.generate.side_effect = Exception("LLM error")

        result = initialized_manager.explain_query("SELECT * FROM users")

        assert result == "Unable to generate explanation."


class TestQueryOptimization:
    """Test query optimization suggestions"""

    @pytest.fixture
    def initialized_manager(self):
        """Create initialized manager"""
        mock_provider = Mock(spec=LocalLLMProvider)
        mock_provider.initialize.return_value = True

        with patch('src.llm.manager.EmbeddingModel') as mock_emb_cls:
            mock_embedding = Mock()
            mock_embedding.initialize.return_value = True
            mock_emb_cls.return_value = mock_embedding

            manager = LocalLLMManager(provider=mock_provider)
            manager.initialize()

            return manager

    def test_suggest_optimization_not_initialized(self):
        """Test optimization requires initialization"""
        manager = LocalLLMManager()

        with pytest.raises(RuntimeError, match="not initialized"):
            manager.suggest_optimization("SELECT * FROM users")

    def test_suggest_optimization_json_response(self, initialized_manager):
        """Test optimization with JSON response"""
        mock_suggestions = json.dumps([
            "Add index on name column",
            "Use specific columns instead of SELECT *",
            "Add WHERE clause to limit results"
        ])
        initialized_manager.provider.generate.return_value = mock_suggestions

        query = "SELECT * FROM users"
        result = initialized_manager.suggest_optimization(query)

        assert len(result) == 3
        assert any("index" in s.lower() for s in result)

    def test_suggest_optimization_text_response(self, initialized_manager):
        """Test optimization with plain text response"""
        mock_response = """
        1. Add index on frequently queried columns
        2. Optimize JOIN operations
        3. Use query caching
        """
        initialized_manager.provider.generate.return_value = mock_response

        result = initialized_manager.suggest_optimization("SELECT * FROM users")

        assert len(result) > 0
        assert len(result) <= 5  # Limited to 5 suggestions

    def test_suggest_optimization_with_execution_plan(self, initialized_manager):
        """Test optimization with execution plan"""
        initialized_manager.provider.generate.return_value = '["Suggestion 1"]'

        query = "SELECT * FROM users"
        plan = "Seq Scan on users (cost=0..100)"

        result = initialized_manager.suggest_optimization(query, execution_plan=plan)

        # Verify execution plan is included in prompt
        call_args = initialized_manager.provider.generate.call_args
        assert plan in call_args[0][0]

    def test_suggest_optimization_failure(self, initialized_manager):
        """Test optimization handles failures"""
        initialized_manager.provider.generate.side_effect = Exception("LLM error")

        result = initialized_manager.suggest_optimization("SELECT * FROM users")

        assert result == []


class TestCleanup:
    """Test resource cleanup"""

    def test_cleanup_resources(self):
        """Test cleanup releases all resources"""
        mock_provider = Mock()
        mock_embedding = Mock()

        with patch('src.llm.manager.EmbeddingModel') as mock_emb_cls:
            mock_emb_cls.return_value = mock_embedding

            manager = LocalLLMManager(provider=mock_provider)
            manager.anonymization_map = {'key': 'value'}
            manager.reverse_map = {'value': 'key'}
            manager.initialized = True

            manager.cleanup()

            mock_provider.cleanup.assert_called_once()
            mock_embedding.cleanup.assert_called_once()
            assert manager.anonymization_map == {}
            assert manager.reverse_map == {}
            assert manager.initialized is False


class TestLLMConfig:
    """Test LLM configuration"""

    def test_llm_config_defaults(self):
        """Test LLMConfig default values"""
        config = LLMConfig()

        assert config.provider_type == "ollama"
        assert config.model_name == "llama2"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048

    def test_llm_config_custom_values(self):
        """Test LLMConfig with custom values"""
        config = LLMConfig(
            provider_type="openai",
            model_name="gpt-4",
            temperature=0.5,
            max_tokens=4096
        )

        assert config.provider_type == "openai"
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 4096
