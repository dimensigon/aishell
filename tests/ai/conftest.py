"""
Shared fixtures for AI tests

Provides reusable fixtures for AI query assistant and conversation testing.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime

from src.ai.query_assistant import QueryContext
from src.ai.conversation_manager import ConversationManager


@pytest.fixture
def basic_query_context():
    """Create basic query context for testing"""
    return QueryContext(
        database_type="sqlite",
        schema_info={
            "users": {
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "email", "type": "TEXT"},
                    {"name": "name", "type": "TEXT"}
                ]
            }
        },
        table_names=["users", "orders"]
    )


@pytest.fixture
def conversation_manager():
    """Create fresh conversation manager for each test"""
    return ConversationManager(max_history=50)


@pytest.fixture
def conversation_with_history(conversation_manager):
    """Create conversation manager with sample history"""
    sid = conversation_manager.start_session("test-session")

    # Add sample conversation
    conversation_manager.add_user_message("What is Python?", sid)
    conversation_manager.add_assistant_message("Python is a programming language.", sid)
    conversation_manager.add_user_message("Tell me more", sid)
    conversation_manager.add_assistant_message("Python is used for web dev, data science, and more.", sid)

    return conversation_manager, sid
