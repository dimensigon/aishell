"""
Shared fixtures and mocking utilities for LLM tests

Provides reusable mocks, fixtures, and test utilities for LLM integration testing.
"""

import pytest
from unittest.mock import Mock, MagicMock
import numpy as np
from typing import Dict, Any, List


# ============================================================================
# Provider Mocks
# ============================================================================

@pytest.fixture
def mock_ollama_client():
    """Create mock Ollama client"""
    mock_client = Mock()

    mock_client.generate = Mock(return_value={
        "response": "This is a mocked Ollama response"
    })

    mock_client.chat = Mock(return_value={
        "message": {
            "content": "This is a mocked chat response"
        }
    })

    mock_client.list = Mock(return_value={
        "models": [
            {"name": "llama2"},
            {"name": "codellama"}
        ]
    })

    return mock_client


@pytest.fixture
def mock_transformers_pipeline():
    """Create mock transformers pipeline"""
    mock_pipeline = Mock()

    def mock_generate(prompt, **kwargs):
        return [{
            "generated_text": f"{prompt} [generated continuation]"
        }]

    mock_pipeline.side_effect = mock_generate

    return mock_pipeline


@pytest.fixture
def mock_anthropic_client():
    """Create mock Anthropic client"""
    mock_client = Mock()

    # Mock messages.create
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = "Mocked Claude response"

    mock_client.messages.create = Mock(return_value=mock_response)

    # Mock streaming
    mock_stream = Mock()
    mock_stream.__enter__ = Mock(return_value=mock_stream)
    mock_stream.__exit__ = Mock(return_value=False)
    mock_stream.text_stream = ["Streaming ", "response ", "chunks"]

    mock_client.messages.stream = Mock(return_value=mock_stream)

    return mock_client


# ============================================================================
# Embedding Mocks
# ============================================================================

@pytest.fixture
def mock_sentence_transformer():
    """Create mock SentenceTransformer model"""
    mock_model = Mock()

    def mock_encode(texts, **kwargs):
        if isinstance(texts, str):
            texts = [texts]
        # Generate consistent fake embeddings
        return np.random.randn(len(texts), 384).astype(np.float32)

    mock_model.encode = Mock(side_effect=mock_encode)

    return mock_model


@pytest.fixture
def mock_embedding_model():
    """Create initialized mock embedding model"""
    from src.llm.embeddings import EmbeddingModel

    mock_model = Mock()
    mock_model.encode.return_value = np.random.randn(3, 384).astype(np.float32)

    embedding = EmbeddingModel()
    embedding.model = mock_model
    embedding.initialized = True

    return embedding


# ============================================================================
# LLM Manager Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_provider():
    """Create generic mock LLM provider"""
    mock_provider = Mock()
    mock_provider.initialize = Mock(return_value=True)
    mock_provider.generate = Mock(return_value="Generated text")
    mock_provider.chat = Mock(return_value="Chat response")
    mock_provider.cleanup = Mock()
    mock_provider.initialized = True

    return mock_provider


@pytest.fixture
def initialized_llm_manager(mock_llm_provider, mock_embedding_model):
    """Create fully initialized LLM manager"""
    from src.llm.manager import LocalLLMManager

    manager = LocalLLMManager(provider=mock_llm_provider)
    manager.embedding_model = mock_embedding_model
    manager.initialized = True

    return manager


# ============================================================================
# Query Assistant Fixtures
# ============================================================================

@pytest.fixture
def query_context():
    """Create test query context"""
    from src.ai.query_assistant import QueryContext

    return QueryContext(
        database_type="postgresql",
        schema_info={
            "users": {
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": ["PRIMARY KEY"]},
                    {"name": "email", "type": "TEXT", "constraints": ["UNIQUE"]},
                    {"name": "name", "type": "TEXT", "constraints": []}
                ]
            },
            "orders": {
                "columns": [
                    {"name": "id", "type": "INTEGER", "constraints": ["PRIMARY KEY"]},
                    {"name": "user_id", "type": "INTEGER", "constraints": ["FOREIGN KEY"]},
                    {"name": "total", "type": "DECIMAL", "constraints": []}
                ]
            }
        },
        table_names=["users", "orders", "products"],
        recent_queries=[
            "SELECT * FROM users WHERE active = 1",
            "SELECT COUNT(*) FROM orders"
        ]
    )


@pytest.fixture
def mock_query_assistant(mock_anthropic_client):
    """Create mock query assistant with Anthropic client"""
    from src.ai.query_assistant import QueryAssistant

    assistant = QueryAssistant(api_key='test-key')
    assistant.client = mock_anthropic_client
    assistant.available = True

    return assistant


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_sample_queries(count: int = 10) -> List[str]:
    """Generate sample SQL queries for testing"""
    queries = []
    for i in range(count):
        if i % 3 == 0:
            queries.append(f"SELECT * FROM table_{i} WHERE id = {i}")
        elif i % 3 == 1:
            queries.append(f"INSERT INTO table_{i} (name) VALUES ('test_{i}')")
        else:
            queries.append(f"UPDATE table_{i} SET active = 1 WHERE id = {i}")

    return queries


def generate_sample_embeddings(count: int, dimensions: int = 384) -> np.ndarray:
    """Generate sample embeddings for testing"""
    return np.random.randn(count, dimensions).astype(np.float32)


def create_mock_llm_response(
    sql: str = "SELECT * FROM users",
    explanation: str = "Test explanation",
    confidence: float = 0.9,
    suggestions: List[str] = None
) -> Dict[str, Any]:
    """Create mock LLM response in expected format"""
    return {
        "sql": sql,
        "explanation": explanation,
        "confidence": confidence,
        "optimizations": suggestions or [],
        "warnings": []
    }


# ============================================================================
# Mock Response Builders
# ============================================================================

class MockResponseBuilder:
    """Builder for creating complex mock responses"""

    @staticmethod
    def sql_generation_response(
        sql: str = "SELECT * FROM users",
        explanation: str = "Retrieves all users",
        confidence: float = 0.9
    ) -> str:
        """Build SQL generation response"""
        return f'''```json
{{
  "sql": "{sql}",
  "explanation": "{explanation}",
  "optimizations": ["Uses specific columns", "Has WHERE clause"],
  "warnings": ["Consider adding LIMIT"],
  "confidence": {confidence}
}}
```'''

    @staticmethod
    def optimization_response(
        optimized_sql: str,
        suggestions: List[str]
    ) -> str:
        """Build optimization response"""
        suggestion_list = "\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions))

        return f'''**Optimized Query:**
```sql
{optimized_sql}
```

**Optimizations Applied:**
{suggestion_list}

**Expected Improvement:** 40% faster execution'''

    @staticmethod
    def error_fix_response(
        fixed_sql: str,
        error_cause: str,
        explanation: str
    ) -> str:
        """Build error fix response"""
        return f'''```json
{{
  "sql": "{fixed_sql}",
  "explanation": "{explanation}",
  "error_cause": "{error_cause}",
  "best_practices": ["Use syntax highlighting", "Test queries before execution"],
  "confidence": 0.95
}}
```'''


# ============================================================================
# Assertion Helpers
# ============================================================================

def assert_valid_sql_response(response):
    """Assert response has valid SQL response structure"""
    assert response.success is True
    assert response.sql_query is not None
    assert isinstance(response.confidence, float)
    assert 0.0 <= response.confidence <= 1.0


def assert_valid_explanation_response(response):
    """Assert response has valid explanation structure"""
    assert response.success is True
    assert response.explanation is not None
    assert len(response.explanation) > 0


def assert_valid_optimization_response(response):
    """Assert response has valid optimization structure"""
    assert response.success is True
    assert isinstance(response.optimization_suggestions, list)


# ============================================================================
# Parametrize Helpers
# ============================================================================

# Common test parameters for different database types
DATABASE_TYPES = ["sqlite", "postgresql", "mysql", "mariadb"]

# Common SQL query types for testing
SQL_QUERY_TYPES = {
    "select": "SELECT * FROM users WHERE id = 1",
    "insert": "INSERT INTO users (name) VALUES ('test')",
    "update": "UPDATE users SET active = 1 WHERE id = 1",
    "delete": "DELETE FROM users WHERE id = 1",
    "create": "CREATE TABLE users (id INTEGER PRIMARY KEY)",
    "drop": "DROP TABLE users"
}

# Common error scenarios
ERROR_SCENARIOS = {
    "syntax": ("SELCT * FROM users", "Syntax error near SELCT"),
    "table_not_found": ("SELECT * FROM non_existent", "Table 'non_existent' doesn't exist"),
    "column_not_found": ("SELECT xyz FROM users", "Column 'xyz' not found"),
    "type_mismatch": ("INSERT INTO users (id) VALUES ('text')", "Type mismatch")
}


# ============================================================================
# Environment Setup
# ============================================================================

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment before each test"""
    import os

    # Clear any existing API keys from environment
    keys_to_clear = ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY']
    original_values = {}

    for key in keys_to_clear:
        if key in os.environ:
            original_values[key] = os.environ[key]
            del os.environ[key]

    yield

    # Restore original values
    for key, value in original_values.items():
        os.environ[key] = value


@pytest.fixture
def temp_model_path(tmp_path):
    """Create temporary model path for testing"""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    return str(model_dir)
