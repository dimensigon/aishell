"""
Tests for AI Query Assistant
"""

import pytest
from unittest.mock import Mock, patch
from src.ai.query_assistant import (
    QueryAssistant,
    QueryContext,
    QueryResponse,
    QueryIntent
)


@pytest.fixture
def query_context():
    """Create test query context"""
    return QueryContext(
        database_type="sqlite",
        schema_info={
            'users': {
                'columns': [
                    {'name': 'id', 'type': 'INTEGER', 'constraints': ['PRIMARY KEY']},
                    {'name': 'email', 'type': 'TEXT', 'constraints': ['UNIQUE']},
                    {'name': 'name', 'type': 'TEXT', 'constraints': []},
                    {'name': 'created_at', 'type': 'TIMESTAMP', 'constraints': []}
                ]
            }
        },
        table_names=['users', 'orders', 'products']
    )


@pytest.fixture
def query_assistant():
    """Create QueryAssistant instance"""
    return QueryAssistant(api_key=None)  # No API key for fallback testing


class TestQueryAssistant:
    """Test QueryAssistant functionality"""

    def test_initialization(self, query_assistant):
        """Test QueryAssistant initialization"""
        assert query_assistant is not None
        assert query_assistant.model is not None
        assert query_assistant.prompts is not None

    def test_fallback_generate_sql(self, query_assistant, query_context):
        """Test fallback SQL generation without API"""
        result = query_assistant.generate_sql(
            "show me all users",
            query_context
        )

        assert isinstance(result, QueryResponse)
        assert result.success
        assert result.sql_query is not None
        assert "SELECT" in result.sql_query.upper()

    def test_fallback_explain_query(self, query_assistant):
        """Test fallback query explanation"""
        sql = "SELECT * FROM users WHERE email = 'test@example.com'"
        result = query_assistant.explain_query(sql, QueryContext())

        assert isinstance(result, QueryResponse)
        assert result.success
        assert result.explanation is not None
        assert len(result.explanation) > 0

    def test_fallback_optimize_query(self, query_assistant):
        """Test fallback query optimization"""
        sql = "SELECT * FROM users"
        result = query_assistant.optimize_query(sql, QueryContext())

        assert isinstance(result, QueryResponse)
        assert result.success
        assert len(result.optimization_suggestions) > 0

    @patch('anthropic.Anthropic')
    def test_generate_sql_with_api(self, mock_anthropic, query_context):
        """Test SQL generation with API (mocked)"""
        # Mock API response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text='```json\n{"sql": "SELECT * FROM users", "explanation": "Test", "confidence": 0.9}\n```')]
        mock_client.messages.create.return_value = mock_response

        assistant = QueryAssistant()
        assistant.client = mock_client
        assistant.available = True

        result = assistant.generate_sql("show all users", query_context)

        assert isinstance(result, QueryResponse)
        assert result.success
        assert result.sql_query == "SELECT * FROM users"

    def test_query_context_to_dict(self, query_context):
        """Test QueryContext serialization"""
        context_dict = query_context.to_dict()

        assert 'database_type' in context_dict
        assert 'schema_info' in context_dict
        assert 'table_names' in context_dict
        assert context_dict['database_type'] == 'sqlite'


class TestPromptTemplates:
    """Test prompt template generation"""

    def test_generate_sql_prompt(self, query_context):
        """Test SQL generation prompt"""
        from src.ai.prompt_templates import PromptTemplates
        prompts = PromptTemplates()

        prompt = prompts.generate_sql_prompt(
            "get all active users",
            query_context
        )

        assert "get all active users" in prompt
        assert "sqlite" in prompt.lower()
        assert "users" in prompt

    def test_explain_query_prompt(self, query_context):
        """Test query explanation prompt"""
        from src.ai.prompt_templates import PromptTemplates
        prompts = PromptTemplates()

        sql = "SELECT * FROM users WHERE active = 1"
        prompt = prompts.explain_query_prompt(sql, query_context, "medium")

        assert sql in prompt
        assert "medium" in prompt.lower()

    def test_optimize_query_prompt(self, query_context):
        """Test query optimization prompt"""
        from src.ai.prompt_templates import PromptTemplates
        prompts = PromptTemplates()

        sql = "SELECT * FROM users"
        performance_data = {'execution_time': 1.5, 'rows_affected': 1000}

        prompt = prompts.optimize_query_prompt(sql, query_context, performance_data)

        assert sql in prompt
        assert "1.5" in prompt


class TestConversationManager:
    """Test conversation management"""

    def test_start_session(self):
        """Test starting conversation session"""
        from src.ai.conversation_manager import ConversationManager
        manager = ConversationManager()

        session_id = manager.start_session()
        assert session_id is not None
        assert session_id in manager.conversations

    def test_add_messages(self):
        """Test adding messages to conversation"""
        from src.ai.conversation_manager import ConversationManager
        manager = ConversationManager()

        session_id = manager.start_session()
        manager.add_user_message("Hello", session_id)
        manager.add_assistant_message("Hi there!", session_id)

        history = manager.get_conversation_history(session_id)
        assert len(history) == 2
        assert history[0].role == 'user'
        assert history[1].role == 'assistant'

    def test_conversation_summary(self):
        """Test getting conversation summary"""
        from src.ai.conversation_manager import ConversationManager
        manager = ConversationManager()

        session_id = manager.start_session()
        manager.add_user_message("Test message 1", session_id)
        manager.add_assistant_message("Response 1", session_id)

        summary = manager.get_conversation_summary(session_id)
        assert summary['total_messages'] == 2
        assert summary['user_messages'] == 1
        assert summary['assistant_messages'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
