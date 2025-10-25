"""
Pytest fixtures for AI-Shell test suite.

Provides reusable fixtures for database connections, mock services,
and test data setup.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock
from tests.utils.test_helpers import (
    MockDatabase,
    MockLLMProvider,
    MockEventBus,
    MockAgent,
    MockMCPClient,
    create_mock_config
)


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Provide mock configuration."""
    return create_mock_config()


@pytest.fixture
def mock_database():
    """Provide mock database."""
    db = MockDatabase(data={
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ],
        "orders": [
            {"id": 1, "user_id": 1, "total": 100.00},
            {"id": 2, "user_id": 2, "total": 200.00}
        ]
    })
    return db


@pytest.fixture
async def connected_database(mock_database):
    """Provide connected mock database."""
    await mock_database.connect()
    yield mock_database
    await mock_database.disconnect()


@pytest.fixture
def mock_llm():
    """Provide mock LLM provider."""
    return MockLLMProvider(responses=[
        "SELECT * FROM users WHERE id = 1",
        "This is a test response",
        "Query executed successfully"
    ])


@pytest.fixture
def mock_event_bus():
    """Provide mock event bus."""
    return MockEventBus()


@pytest.fixture
def mock_agent():
    """Provide mock agent."""
    return MockAgent(name="test_agent", responses=[
        {"status": "success", "data": {"result": "test"}},
        {"status": "success", "data": {"result": "test2"}}
    ])


@pytest.fixture
def mock_mcp_client():
    """Provide mock MCP client."""
    return MockMCPClient(responses={
        "query": {"data": [{"id": 1, "name": "Test"}]},
        "execute": {"affected_rows": 1},
        "health_check": {"status": "healthy"}
    })


@pytest.fixture
def test_data_users():
    """Provide test user data."""
    return [
        {"id": 1, "name": "Alice", "email": "alice@test.com", "role": "admin"},
        {"id": 2, "name": "Bob", "email": "bob@test.com", "role": "user"},
        {"id": 3, "name": "Charlie", "email": "charlie@test.com", "role": "user"}
    ]


@pytest.fixture
def test_data_orders():
    """Provide test order data."""
    return [
        {"id": 1, "user_id": 1, "total": 150.00, "status": "completed"},
        {"id": 2, "user_id": 2, "total": 200.00, "status": "pending"},
        {"id": 3, "user_id": 1, "total": 75.50, "status": "completed"}
    ]


@pytest.fixture
def mock_security_manager():
    """Provide mock security manager."""
    manager = MagicMock()
    manager.validate_query = AsyncMock(return_value=True)
    manager.encrypt_data = MagicMock(return_value="encrypted_data")
    manager.decrypt_data = MagicMock(return_value="decrypted_data")
    manager.check_permissions = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def mock_audit_logger():
    """Provide mock audit logger."""
    logger = MagicMock()
    logger.log_action = AsyncMock(return_value=None)
    logger.log_query = AsyncMock(return_value=None)
    logger.log_error = AsyncMock(return_value=None)
    return logger


@pytest.fixture
def temp_test_db(tmp_path):
    """Provide temporary test database path."""
    db_path = tmp_path / "test.db"
    return str(db_path)


@pytest.fixture
def mock_vector_store():
    """Provide mock vector store."""
    store = MagicMock()
    store.add_vectors = AsyncMock(return_value={"ids": [1, 2, 3]})
    store.search = AsyncMock(return_value=[
        {"id": 1, "distance": 0.1, "data": {"text": "result 1"}},
        {"id": 2, "distance": 0.2, "data": {"text": "result 2"}}
    ])
    store.delete = AsyncMock(return_value=True)
    return store


@pytest.fixture
def mock_embedding_model():
    """Provide mock embedding model."""
    model = MagicMock()
    model.encode = MagicMock(return_value=[[0.1] * 384])
    return model


@pytest.fixture
async def initialized_agent(mock_agent):
    """Provide initialized mock agent."""
    await mock_agent.initialize()
    yield mock_agent
    await mock_agent.shutdown()


@pytest.fixture
def sample_sql_queries():
    """Provide sample SQL queries for testing."""
    return {
        "safe": [
            "SELECT * FROM users",
            "SELECT name, email FROM users WHERE id = 1",
            "SELECT COUNT(*) FROM orders WHERE status = 'completed'"
        ],
        "unsafe": [
            "SELECT * FROM users WHERE id = 1 OR 1=1",
            "DROP TABLE users",
            "DELETE FROM orders",
            "'; DROP TABLE users; --"
        ],
        "complex": [
            "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.name",
            "WITH recent_orders AS (SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days') SELECT * FROM recent_orders"
        ]
    }


@pytest.fixture
def mock_retry_config():
    """Provide mock retry configuration."""
    return {
        "max_retries": 3,
        "initial_delay": 0.1,
        "max_delay": 1.0,
        "exponential_base": 2
    }


@pytest.fixture
def performance_thresholds():
    """Provide performance test thresholds."""
    return {
        "query_execution": 0.1,  # 100ms
        "agent_response": 0.5,   # 500ms
        "batch_processing": 2.0, # 2s
        "memory_limit_mb": 100   # 100MB
    }
