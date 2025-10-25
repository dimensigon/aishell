"""
Test utility helpers for AI-Shell test suite.

Provides common test utilities, mocks, and helpers for consistent testing.
"""

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock
import pytest


class MockDatabase:
    """Mock database for testing."""

    def __init__(self, data: Optional[Dict[str, List[Dict]]] = None):
        self.data = data or {}
        self.queries_executed = []
        self.connected = False

    async def connect(self):
        """Simulate database connection."""
        self.connected = True

    async def disconnect(self):
        """Simulate database disconnection."""
        self.connected = False

    async def execute(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute mock query."""
        self.queries_executed.append((query, params))
        table_name = self._extract_table_name(query)
        return self.data.get(table_name, [])

    def _extract_table_name(self, query: str) -> str:
        """Extract table name from SQL query."""
        query_lower = query.lower()
        if "from" in query_lower:
            parts = query_lower.split("from")[1].strip().split()
            return parts[0] if parts else "unknown"
        return "unknown"


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self, responses: Optional[List[str]] = None):
        self.responses = responses or ["Mock response"]
        self.current_index = 0
        self.calls = []

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate mock response."""
        self.calls.append({"prompt": prompt, "kwargs": kwargs})
        response = self.responses[self.current_index % len(self.responses)]
        self.current_index += 1
        return response

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate mock embedding."""
        # Return deterministic embedding based on text length
        return [float(i * len(text)) for i in range(384)]


class MockEventBus:
    """Mock event bus for testing."""

    def __init__(self):
        self.events = []
        self.subscribers = {}

    async def emit(self, event_type: str, data: Any):
        """Emit mock event."""
        self.events.append({"type": event_type, "data": data})

        # Notify subscribers
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                await callback(data)

    def subscribe(self, event_type: str, callback):
        """Subscribe to events."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def get_events(self, event_type: Optional[str] = None) -> List[Dict]:
        """Get emitted events."""
        if event_type:
            return [e for e in self.events if e["type"] == event_type]
        return self.events


class MockAgent:
    """Mock agent for testing."""

    def __init__(self, name: str, responses: Optional[List[Any]] = None):
        self.name = name
        self.responses = responses or [{"success": True}]
        self.current_index = 0
        self.tasks_executed = []

    async def execute(self, task: Dict[str, Any]) -> Any:
        """Execute mock task."""
        self.tasks_executed.append(task)
        response = self.responses[self.current_index % len(self.responses)]
        self.current_index += 1
        return response

    async def initialize(self):
        """Mock initialization."""
        pass

    async def shutdown(self):
        """Mock shutdown."""
        pass


def create_mock_config(**kwargs) -> Dict[str, Any]:
    """Create mock configuration."""
    default_config = {
        "database": {
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "name": "test_db",
            "user": "test_user",
            "password": "test_pass"
        },
        "llm": {
            "provider": "mock",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "security": {
            "encryption_enabled": True,
            "audit_logging": True
        },
        "agents": {
            "max_parallel": 5,
            "timeout": 30
        }
    }
    default_config.update(kwargs)
    return default_config


async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
    """
    Wait for a condition to become true.

    Args:
        condition_func: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds
    """
    elapsed = 0.0
    while elapsed < timeout:
        if condition_func():
            return True
        await asyncio.sleep(interval)
        elapsed += interval
    return False


def assert_sql_safe(query: str):
    """Assert that SQL query is safe (no injection attempts)."""
    dangerous_patterns = [
        "DROP TABLE",
        "DROP DATABASE",
        "DELETE FROM",
        "'; --",
        "1=1",
        "UNION SELECT",
        "INSERT INTO",
        "UPDATE ",
        "ALTER TABLE"
    ]

    query_upper = query.upper()
    for pattern in dangerous_patterns:
        assert pattern not in query_upper, f"Potentially dangerous SQL pattern found: {pattern}"


def assert_no_secrets(data: Any):
    """Assert that data contains no secrets or sensitive information."""
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = key.lower()
            assert "password" not in key_lower or value == "***REDACTED***", \
                f"Unredacted password found in key: {key}"
            assert "secret" not in key_lower or value == "***REDACTED***", \
                f"Unredacted secret found in key: {key}"
            assert "token" not in key_lower or value == "***REDACTED***", \
                f"Unredacted token found in key: {key}"

            if isinstance(value, (dict, list)):
                assert_no_secrets(value)

    elif isinstance(data, list):
        for item in data:
            assert_no_secrets(item)


class AsyncContextManagerMock:
    """Mock for async context managers."""

    def __init__(self, return_value=None):
        self.return_value = return_value
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        self.entered = True
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.exited = True
        return False


def create_async_mock(*args, **kwargs):
    """Create an AsyncMock with default behavior."""
    mock = AsyncMock(*args, **kwargs)
    return mock


class MockMCPClient:
    """Mock MCP client for testing."""

    def __init__(self, responses: Optional[Dict[str, Any]] = None):
        self.responses = responses or {}
        self.requests = []
        self.connected = False

    async def connect(self):
        """Mock connect."""
        self.connected = True

    async def disconnect(self):
        """Mock disconnect."""
        self.connected = False

    async def send_request(self, method: str, params: Dict[str, Any]) -> Any:
        """Mock send request."""
        self.requests.append({"method": method, "params": params})
        return self.responses.get(method, {"status": "success"})


class PerformanceTimer:
    """Context manager for performance timing."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = asyncio.get_event_loop().time()
        self.duration = self.end_time - self.start_time
        return False

    async def __aenter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = asyncio.get_event_loop().time()
        self.duration = self.end_time - self.start_time
        return False


def generate_test_data(table_name: str, count: int = 10) -> List[Dict[str, Any]]:
    """Generate test data for a table."""
    data = []
    for i in range(count):
        record = {
            "id": i + 1,
            "name": f"Test {table_name} {i + 1}",
            "created_at": f"2025-01-{(i % 28) + 1:02d}",
            "active": i % 2 == 0
        }
        data.append(record)
    return data
