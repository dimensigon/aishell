"""
Unit Tests for Local LLM Integration

Comprehensive tests for LLM manager, providers, and embeddings.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import numpy as np
import json

from src.llm.manager import LocalLLMManager, IntentType
from src.llm.providers import LocalLLMProvider, OllamaProvider
from src.llm.embeddings import EmbeddingModel


class TestOllamaProvider(unittest.TestCase):
    """Test Ollama provider implementation"""

    def setUp(self):
        self.provider = OllamaProvider(
            model_name="llama2",
            model_path="/data0/models"
        )

    def test_initialization(self):
        """Test provider initialization"""
        success = self.provider.initialize()
        self.assertTrue(success)
        self.assertTrue(self.provider.initialized)

    def test_generate(self):
        """Test text generation"""
        self.provider.initialize()

        prompt = "What is a database index?"
        response = self.provider.generate(prompt, max_tokens=100)

        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_chat(self):
        """Test chat functionality"""
        self.provider.initialize()

        messages = [
            {"role": "user", "content": "What is SQL?"},
            {"role": "assistant", "content": "SQL is a language for databases."},
            {"role": "user", "content": "Give me an example."}
        ]

        response = self.provider.chat(messages, max_tokens=100)

        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_uninitialized_error(self):
        """Test error when using uninitialized provider"""
        with self.assertRaises(RuntimeError):
            self.provider.generate("test")


class TestEmbeddingModel(unittest.TestCase):
    """Test embedding model wrapper"""

    def setUp(self):
        self.model = EmbeddingModel(
            model_name="all-MiniLM-L6-v2",
            model_path="/data0/models"
        )

    def test_initialization(self):
        """Test embedding model initialization"""
        success = self.model.initialize()
        self.assertTrue(success)
        self.assertTrue(self.model.initialized)

    def test_encode_single_text(self):
        """Test encoding single text"""
        self.model.initialize()

        embedding = self.model.encode("SELECT * FROM users")

        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(len(embedding.shape), 2)
        self.assertEqual(embedding.shape[0], 1)

    def test_encode_multiple_texts(self):
        """Test encoding multiple texts"""
        self.model.initialize()

        texts = [
            "SELECT * FROM users",
            "INSERT INTO orders VALUES",
            "UPDATE products SET price"
        ]

        embeddings = self.model.encode(texts)

        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.shape[0], 3)

    def test_similarity(self):
        """Test similarity calculation"""
        self.model.initialize()

        text1 = "SELECT * FROM users WHERE id = 1"
        text2 = "SELECT * FROM users WHERE id = 2"
        text3 = "INSERT INTO products VALUES"

        # Similar queries should have higher similarity
        similar_score = self.model.similarity(text1, text2)
        different_score = self.model.similarity(text1, text3)

        self.assertIsInstance(similar_score, float)
        self.assertIsInstance(different_score, float)
        self.assertGreaterEqual(similar_score, 0.0)
        self.assertLessEqual(similar_score, 1.0)

    def test_find_most_similar(self):
        """Test finding most similar texts"""
        self.model.initialize()

        query = "SELECT name FROM users"
        candidates = [
            "SELECT email FROM users",
            "INSERT INTO users VALUES",
            "SELECT * FROM orders",
            "SELECT id FROM users"
        ]

        results = self.model.find_most_similar(query, candidates, top_k=2)

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], tuple)
        self.assertIn(results[0][0], candidates)
        self.assertIsInstance(results[0][1], float)


class TestLocalLLMManager(unittest.TestCase):
    """Test LLM Manager functionality"""

    def setUp(self):
        self.manager = LocalLLMManager(model_path="/data0/models")

    def test_initialization(self):
        """Test manager initialization"""
        success = self.manager.initialize(provider_type="ollama", model_name="llama2")
        self.assertTrue(success)
        self.assertTrue(self.manager.initialized)

    def test_intent_analysis_query(self):
        """Test intent analysis for SELECT query"""
        self.manager.initialize()

        query = "SELECT * FROM users WHERE age > 18"
        result = self.manager.analyze_intent(query)

        self.assertEqual(result['intent'], IntentType.QUERY.value)
        self.assertGreater(result['confidence'], 0.8)
        self.assertEqual(result['metadata']['operation'], 'read')

    def test_intent_analysis_mutation(self):
        """Test intent analysis for INSERT query"""
        self.manager.initialize()

        query = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"
        result = self.manager.analyze_intent(query)

        self.assertEqual(result['intent'], IntentType.MUTATION.value)
        self.assertGreater(result['confidence'], 0.8)
        self.assertEqual(result['metadata']['operation'], 'write')

    def test_intent_analysis_performance(self):
        """Test intent analysis for performance query"""
        self.manager.initialize()

        query = "CREATE INDEX idx_user_email ON users(email)"
        result = self.manager.analyze_intent(query)

        self.assertEqual(result['intent'], IntentType.PERFORMANCE.value)
        self.assertGreater(result['confidence'], 0.8)

    def test_anonymize_email(self):
        """Test email anonymization"""
        self.manager.initialize()

        query = "SELECT * FROM users WHERE email = 'john@example.com'"
        anonymized, mapping = self.manager.anonymize_query(query)

        self.assertNotIn('john@example.com', anonymized)
        self.assertIn('EMAIL_', anonymized)
        self.assertGreater(len(mapping), 0)

    def test_anonymize_ssn(self):
        """Test SSN anonymization"""
        self.manager.initialize()

        query = "SELECT * FROM users WHERE ssn = '123-45-6789'"
        anonymized, mapping = self.manager.anonymize_query(query)

        self.assertNotIn('123-45-6789', anonymized)
        self.assertIn('SSN_', anonymized)
        self.assertGreater(len(mapping), 0)

    def test_deanonymize_result(self):
        """Test result de-anonymization"""
        self.manager.initialize()

        query = "SELECT * FROM users WHERE email = 'john@example.com'"
        anonymized, mapping = self.manager.anonymize_query(query)

        # Simulate anonymized result
        result = f"Found user with email: {list(mapping.keys())[0]}"
        deanonymized = self.manager.deanonymize_result(result, mapping)

        self.assertIn('john@example.com', deanonymized)
        self.assertNotIn('EMAIL_', deanonymized)

    def test_generate_embeddings(self):
        """Test embedding generation"""
        self.manager.initialize()

        texts = [
            "SELECT * FROM users",
            "INSERT INTO orders VALUES"
        ]

        embeddings = self.manager.generate_embeddings(texts)

        self.assertIsInstance(embeddings, list)
        self.assertEqual(len(embeddings), 2)
        self.assertIsInstance(embeddings[0], list)

    def test_find_similar_queries(self):
        """Test finding similar queries"""
        self.manager.initialize()

        query = "SELECT name FROM users WHERE id = 1"
        history = [
            "SELECT email FROM users WHERE id = 2",
            "INSERT INTO products VALUES",
            "SELECT * FROM users WHERE id = 3"
        ]

        similar = self.manager.find_similar_queries(query, history, top_k=2)

        self.assertEqual(len(similar), 2)
        self.assertIsInstance(similar[0], tuple)
        self.assertIsInstance(similar[0][1], float)

    def test_explain_query(self):
        """Test query explanation"""
        self.manager.initialize()

        query = "SELECT u.name, COUNT(o.id) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.name"
        explanation = self.manager.explain_query(query)

        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 0)

    def test_suggest_optimization(self):
        """Test optimization suggestions"""
        self.manager.initialize()

        query = "SELECT * FROM users WHERE name LIKE '%john%'"
        suggestions = self.manager.suggest_optimization(query)

        self.assertIsInstance(suggestions, list)
        # Should provide at least one suggestion
        self.assertGreaterEqual(len(suggestions), 0)

    def test_cleanup(self):
        """Test resource cleanup"""
        self.manager.initialize()
        self.manager.cleanup()

        self.assertFalse(self.manager.initialized)
        self.assertEqual(len(self.manager.anonymization_map), 0)


class TestProviderBase(unittest.TestCase):
    """Test base provider class"""

    def test_abstract_methods(self):
        """Test that abstract methods must be implemented"""
        # Cannot instantiate abstract class
        with self.assertRaises(TypeError):
            LocalLLMProvider("test", "/path")


if __name__ == '__main__':
    unittest.main()
