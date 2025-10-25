"""
Comprehensive tests for Query Assistant with full API mocking

Tests AI-powered SQL generation, explanation, optimization, and error fixing.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json
from typing import Dict, Any

from src.ai.query_assistant import (
    QueryAssistant,
    QueryContext,
    QueryResponse,
    QueryIntent
)


class TestQueryContextCreation:
    """Test QueryContext dataclass"""

    def test_query_context_defaults(self):
        """Test QueryContext with default values"""
        context = QueryContext()

        assert context.database_type == "sqlite"
        assert context.schema_info == {}
        assert context.table_names == []
        assert context.recent_queries == []
        assert context.user_preferences == {}
        assert context.performance_history == []

    def test_query_context_custom_values(self):
        """Test QueryContext with custom values"""
        context = QueryContext(
            database_type="postgresql",
            schema_info={"users": {"columns": ["id", "name"]}},
            table_names=["users", "posts"],
            recent_queries=["SELECT * FROM users"],
            user_preferences={"limit": 100}
        )

        assert context.database_type == "postgresql"
        assert "users" in context.schema_info
        assert len(context.table_names) == 2
        assert len(context.recent_queries) == 1

    def test_query_context_to_dict(self):
        """Test QueryContext serialization"""
        context = QueryContext(
            database_type="mysql",
            table_names=["users"],
            recent_queries=["q1", "q2", "q3", "q4", "q5", "q6"]
        )

        result = context.to_dict()

        assert result['database_type'] == "mysql"
        assert result['table_names'] == ["users"]
        # Should only include last 5 queries
        assert len(result['recent_queries']) == 5
        assert result['recent_queries'] == ["q2", "q3", "q4", "q5", "q6"]


class TestQueryResponseCreation:
    """Test QueryResponse dataclass"""

    def test_query_response_minimal(self):
        """Test QueryResponse with minimal fields"""
        response = QueryResponse(success=True)

        assert response.success is True
        assert response.sql_query is None
        assert response.explanation is None
        assert response.optimization_suggestions == []
        assert response.warnings == []
        assert response.confidence == 0.0

    def test_query_response_complete(self):
        """Test QueryResponse with all fields"""
        response = QueryResponse(
            success=True,
            sql_query="SELECT * FROM users",
            explanation="Retrieves all users",
            optimization_suggestions=["Add index"],
            warnings=["Use LIMIT"],
            confidence=0.95,
            metadata={"execution_time": "10ms"}
        )

        assert response.success is True
        assert response.sql_query == "SELECT * FROM users"
        assert len(response.optimization_suggestions) == 1
        assert len(response.warnings) == 1
        assert response.confidence == 0.95
        assert "execution_time" in response.metadata


class TestQueryAssistantInitialization:
    """Test QueryAssistant initialization"""

    def test_init_no_api_key(self):
        """Test initialization without API key"""
        with patch.dict('os.environ', {}, clear=True):
            assistant = QueryAssistant()

            assert assistant.api_key is None
            assert assistant.client is None
            # Should still have prompts available
            assert assistant.prompts is not None

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key-123'})
    @patch('src.ai.query_assistant.Anthropic')
    def test_init_with_env_api_key(self, mock_anthropic_cls):
        """Test initialization with API key from environment"""
        mock_client = Mock()
        mock_anthropic_cls.return_value = mock_client

        assistant = QueryAssistant()

        assert assistant.api_key == 'test-key-123'
        assert assistant.client is mock_client
        assert assistant.available is True
        mock_anthropic_cls.assert_called_once_with(api_key='test-key-123')

    @patch('src.ai.query_assistant.Anthropic')
    def test_init_with_explicit_api_key(self, mock_anthropic_cls):
        """Test initialization with explicit API key"""
        mock_client = Mock()
        mock_anthropic_cls.return_value = mock_client

        assistant = QueryAssistant(api_key='explicit-key')

        assert assistant.api_key == 'explicit-key'
        mock_anthropic_cls.assert_called_once_with(api_key='explicit-key')

    @patch('src.ai.query_assistant.Anthropic', side_effect=ImportError)
    def test_init_anthropic_not_installed(self, mock_anthropic):
        """Test initialization when anthropic package not installed"""
        assistant = QueryAssistant(api_key='test-key')

        assert assistant.client is None
        assert assistant.available is False

    def test_init_custom_model_parameters(self):
        """Test initialization with custom parameters"""
        assistant = QueryAssistant(
            api_key='test-key',
            model='claude-3-opus-20240229',
            max_tokens=8192,
            temperature=0.5
        )

        assert assistant.model == 'claude-3-opus-20240229'
        assert assistant.max_tokens == 8192
        assert assistant.temperature == 0.5


class TestGenerateSQL:
    """Test SQL generation from natural language"""

    @pytest.fixture
    def mock_assistant(self):
        """Create assistant with mocked Anthropic client"""
        with patch('src.ai.query_assistant.Anthropic') as mock_cls:
            mock_client = Mock()
            mock_cls.return_value = mock_client

            assistant = QueryAssistant(api_key='test-key')
            return assistant, mock_client

    def test_generate_sql_no_client(self):
        """Test SQL generation falls back when no client available"""
        with patch('src.ai.query_assistant.NLPToSQL') as mock_nlp_cls:
            mock_converter = Mock()
            mock_converter.convert.return_value = {
                'sql': 'SELECT * FROM users',
                'confidence': 0.6
            }
            mock_nlp_cls.return_value = mock_converter

            assistant = QueryAssistant()  # No API key
            context = QueryContext()

            result = assistant.generate_sql("get all users", context)

            assert result.success is True
            assert result.sql_query == 'SELECT * FROM users'
            assert "fallback" in result.explanation.lower()
            assert "ANTHROPIC_API_KEY" in result.warnings[0]

    def test_generate_sql_success_json_response(self, mock_assistant):
        """Test successful SQL generation with JSON response"""
        assistant, mock_client = mock_assistant

        # Mock API response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''```json
{
  "sql": "SELECT id, name FROM users WHERE age > 21",
  "explanation": "Retrieves users over 21",
  "optimizations": ["Uses specific columns", "Has WHERE clause"],
  "warnings": ["Consider adding LIMIT"],
  "confidence": 0.92
}
```'''
        mock_client.messages.create.return_value = mock_response

        context = QueryContext(table_names=["users"])
        result = assistant.generate_sql("get users over 21", context)

        assert result.success is True
        assert "SELECT" in result.sql_query
        assert "age > 21" in result.sql_query
        assert result.explanation is not None
        assert len(result.optimization_suggestions) == 2
        assert len(result.warnings) == 1
        assert result.confidence == 0.92

    def test_generate_sql_success_sql_block_response(self, mock_assistant):
        """Test SQL generation with SQL code block response"""
        assistant, mock_client = mock_assistant

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''```sql
SELECT * FROM users WHERE name = 'John'
```
This query retrieves users named John.'''
        mock_client.messages.create.return_value = mock_response

        context = QueryContext()
        result = assistant.generate_sql("find users named John", context)

        assert result.success is True
        assert "SELECT * FROM users" in result.sql_query
        assert "John" in result.sql_query
        assert "retrieves users named John" in result.explanation

    def test_generate_sql_api_error(self, mock_assistant):
        """Test SQL generation handles API errors"""
        assistant, mock_client = mock_assistant

        mock_client.messages.create.side_effect = Exception("API rate limit exceeded")

        context = QueryContext()
        result = assistant.generate_sql("test query", context)

        assert result.success is False
        assert len(result.warnings) > 0
        assert "API error" in result.warnings[0]

    def test_generate_sql_includes_context_in_prompt(self, mock_assistant):
        """Test SQL generation includes context in prompt"""
        assistant, mock_client = mock_assistant

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '```sql\nSELECT * FROM users\n```'
        mock_client.messages.create.return_value = mock_response

        context = QueryContext(
            database_type="postgresql",
            table_names=["users", "posts"],
            schema_info={"users": {"columns": [{"name": "id"}, {"name": "name"}]}}
        )

        result = assistant.generate_sql("get users", context)

        # Verify context was included in prompt
        call_args = mock_client.messages.create.call_args
        prompt = call_args[1]['messages'][0]['content']

        assert "postgresql" in prompt
        assert "users" in prompt
        assert "posts" in prompt

    def test_generate_sql_streaming_mode(self, mock_assistant):
        """Test SQL generation with streaming enabled"""
        assistant, mock_client = mock_assistant

        # Mock streaming response
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)
        mock_stream.text_stream = ['```sql\n', 'SELECT * FROM users', '\n```']

        mock_client.messages.stream.return_value = mock_stream

        context = QueryContext()
        result = assistant.generate_sql("test query", context, stream=True)

        assert result.success is True
        mock_client.messages.stream.assert_called_once()


class TestExplainQuery:
    """Test SQL query explanation"""

    @pytest.fixture
    def mock_assistant(self):
        """Create assistant with mocked client"""
        with patch('src.ai.query_assistant.Anthropic') as mock_cls:
            mock_client = Mock()
            mock_cls.return_value = mock_client

            assistant = QueryAssistant(api_key='test-key')
            return assistant, mock_client

    def test_explain_query_no_client(self):
        """Test explanation falls back without client"""
        assistant = QueryAssistant()
        context = QueryContext()

        result = assistant.explain_query("SELECT * FROM users", context)

        assert result.success is True
        assert result.explanation is not None
        assert "retrieves data" in result.explanation
        assert "ANTHROPIC_API_KEY" in result.warnings[0]

    def test_explain_query_success(self, mock_assistant):
        """Test successful query explanation"""
        assistant, mock_client = mock_assistant

        explanation_text = "This query retrieves all columns from the users table."
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = explanation_text
        mock_client.messages.create.return_value = mock_response

        context = QueryContext()
        result = assistant.explain_query("SELECT * FROM users", context)

        assert result.success is True
        assert result.explanation == explanation_text
        assert result.sql_query == "SELECT * FROM users"
        assert result.confidence == 0.9

    def test_explain_query_detail_levels(self, mock_assistant):
        """Test different detail levels for explanations"""
        assistant, mock_client = mock_assistant

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Explanation"
        mock_client.messages.create.return_value = mock_response

        context = QueryContext()
        query = "SELECT * FROM users"

        # Test all detail levels
        for level in ['simple', 'medium', 'detailed']:
            result = assistant.explain_query(query, context, detail_level=level)

            assert result.success is True
            assert result.metadata['detail_level'] == level

            # Verify detail level in prompt
            call_args = mock_client.messages.create.call_args
            prompt = call_args[1]['messages'][0]['content']
            assert level.upper() in prompt

    def test_explain_query_includes_schema_context(self, mock_assistant):
        """Test explanation includes schema context"""
        assistant, mock_client = mock_assistant

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Explanation"
        mock_client.messages.create.return_value = mock_response

        context = QueryContext(
            schema_info={"users": {"columns": [{"name": "id"}, {"name": "email"}]}}
        )

        result = assistant.explain_query("SELECT * FROM users", context)

        # Verify schema in prompt
        call_args = mock_client.messages.create.call_args
        prompt = call_args[1]['messages'][0]['content']
        assert "users" in prompt

    def test_explain_query_api_error(self, mock_assistant):
        """Test explanation handles API errors"""
        assistant, mock_client = mock_assistant

        mock_client.messages.create.side_effect = Exception("API error")

        context = QueryContext()
        result = assistant.explain_query("SELECT * FROM users", context)

        assert result.success is False
        assert "API error" in result.warnings[0]

    def test_explain_query_lower_temperature(self, mock_assistant):
        """Test explanation uses lower temperature"""
        assistant, mock_client = mock_assistant

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Explanation"
        mock_client.messages.create.return_value = mock_response

        context = QueryContext()
        assistant.explain_query("SELECT * FROM users", context)

        # Verify lower temperature for more deterministic explanations
        call_args = mock_client.messages.create.call_args
        assert call_args[1]['temperature'] == 0.5


class TestOptimizeQuery:
    """Test query optimization"""

    @pytest.fixture
    def mock_assistant(self):
        """Create assistant with mocked client"""
        with patch('src.ai.query_assistant.Anthropic') as mock_cls:
            mock_client = Mock()
            mock_cls.return_value = mock_client

            assistant = QueryAssistant(api_key='test-key')
            return assistant, mock_client

    def test_optimize_query_no_client(self):
        """Test optimization falls back without client"""
        assistant = QueryAssistant()
        context = QueryContext()

        result = assistant.optimize_query("SELECT * FROM users", context)

        assert result.success is True
        assert len(result.optimization_suggestions) > 0
        assert any("index" in s.lower() for s in result.optimization_suggestions)
        assert "ANTHROPIC_API_KEY" in result.warnings[0]

    def test_optimize_query_success(self, mock_assistant):
        """Test successful query optimization"""
        assistant, mock_client = mock_assistant

        response_text = '''**Optimized Query:**
```sql
SELECT id, name FROM users WHERE active = 1 LIMIT 100
```

**Optimizations Applied:**
1. Use specific columns instead of SELECT *
2. Add index on active column
3. Add LIMIT to reduce result set

**Expected Improvement:** 40% faster execution'''

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = response_text
        mock_client.messages.create.return_value = mock_response

        context = QueryContext()
        result = assistant.optimize_query("SELECT * FROM users", context)

        assert result.success is True
        assert result.sql_query is not None
        assert len(result.optimization_suggestions) >= 3
        assert any("columns" in s for s in result.optimization_suggestions)

    def test_optimize_query_with_performance_data(self, mock_assistant):
        """Test optimization includes performance data"""
        assistant, mock_client = mock_assistant

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "1. Add index\n2. Use joins"
        mock_client.messages.create.return_value = mock_response

        context = QueryContext()
        performance_data = {
            'execution_time': '2.5s',
            'rows_affected': 10000,
            'rows_scanned': 100000
        }

        result = assistant.optimize_query(
            "SELECT * FROM users",
            context,
            performance_data=performance_data
        )

        # Verify performance data in prompt
        call_args = mock_client.messages.create.call_args
        prompt = call_args[1]['messages'][0]['content']

        assert '2.5s' in prompt
        assert '10000' in prompt
        assert '100000' in prompt

    def test_optimize_query_extracts_suggestions(self, mock_assistant):
        """Test extraction of optimization suggestions"""
        assistant, mock_client = mock_assistant

        response_text = '''
1. Add index on user_id column
2. Use JOIN instead of subquery
3. Implement query caching
- Consider partitioning large tables
* Use prepared statements
'''
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = response_text
        mock_client.messages.create.return_value = mock_response

        context = QueryContext()
        result = assistant.optimize_query("SELECT * FROM users", context)

        # Should extract all numbered and bulleted suggestions
        assert len(result.optimization_suggestions) >= 3

    def test_optimize_query_api_error(self, mock_assistant):
        """Test optimization handles API errors"""
        assistant, mock_client = mock_assistant

        mock_client.messages.create.side_effect = Exception("Timeout")

        context = QueryContext()
        result = assistant.optimize_query("SELECT * FROM users", context)

        assert result.success is False
        assert "API error" in result.warnings[0]


class TestFixQuery:
    """Test query error fixing"""

    @pytest.fixture
    def mock_assistant(self):
        """Create assistant with mocked client"""
        with patch('src.ai.query_assistant.Anthropic') as mock_cls:
            mock_client = Mock()
            mock_cls.return_value = mock_client

            assistant = QueryAssistant(api_key='test-key')
            return assistant, mock_client

    def test_fix_query_no_client(self):
        """Test fix query requires API client"""
        assistant = QueryAssistant()
        context = QueryContext()

        result = assistant.fix_query(
            "SELCT * FROM users",
            "Syntax error near SELCT",
            context
        )

        assert result.success is False
        assert "not available" in result.warnings[0]

    def test_fix_query_success(self, mock_assistant):
        """Test successful query fixing"""
        assistant, mock_client = mock_assistant

        fixed_response = '''```json
{
  "sql": "SELECT * FROM users",
  "explanation": "Fixed typo in SELECT keyword",
  "error_cause": "Misspelled SELECT as SELCT",
  "best_practices": ["Use syntax highlighting", "Validate before execution"],
  "confidence": 0.98
}
```'''

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = fixed_response
        mock_client.messages.create.return_value = mock_response

        context = QueryContext()
        result = assistant.fix_query(
            "SELCT * FROM users",
            "Syntax error",
            context
        )

        assert result.success is True
        assert "SELECT * FROM users" in result.sql_query
        assert result.explanation is not None
        assert result.confidence > 0.9

    def test_fix_query_includes_error_message(self, mock_assistant):
        """Test fix query includes error message in prompt"""
        assistant, mock_client = mock_assistant

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '```sql\nSELECT * FROM users\n```'
        mock_client.messages.create.return_value = mock_response

        context = QueryContext()
        error_msg = "Column 'xyz' does not exist"

        result = assistant.fix_query("SELECT xyz FROM users", error_msg, context)

        # Verify error message in prompt
        call_args = mock_client.messages.create.call_args
        prompt = call_args[1]['messages'][0]['content']
        assert error_msg in prompt

    def test_fix_query_api_error(self, mock_assistant):
        """Test fix query handles API errors"""
        assistant, mock_client = mock_assistant

        mock_client.messages.create.side_effect = Exception("API error")

        context = QueryContext()
        result = assistant.fix_query("bad query", "error", context)

        assert result.success is False
        assert "API error" in result.warnings[0]


class TestAnalyzeSchema:
    """Test schema analysis"""

    @pytest.fixture
    def mock_assistant(self):
        """Create assistant with mocked client"""
        with patch('src.ai.query_assistant.Anthropic') as mock_cls:
            mock_client = Mock()
            mock_cls.return_value = mock_client

            assistant = QueryAssistant(api_key='test-key')
            return assistant, mock_client

    def test_analyze_schema_no_client(self):
        """Test schema analysis requires API client"""
        assistant = QueryAssistant()

        result = assistant.analyze_schema({"users": {}})

        assert result.success is False
        assert "not available" in result.warnings[0]

    def test_analyze_schema_success(self, mock_assistant):
        """Test successful schema analysis"""
        assistant, mock_client = mock_assistant

        analysis_text = "The schema is well-normalized with proper foreign keys."
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = analysis_text
        mock_client.messages.create.return_value = mock_response

        schema = {
            "users": {"columns": [{"name": "id"}, {"name": "email"}]},
            "posts": {"columns": [{"name": "id"}, {"name": "user_id"}]}
        }

        result = assistant.analyze_schema(schema)

        assert result.success is True
        assert result.explanation == analysis_text
        assert result.metadata['analysis_type'] == 'general'

    def test_analyze_schema_types(self, mock_assistant):
        """Test different analysis types"""
        assistant, mock_client = mock_assistant

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Analysis"
        mock_client.messages.create.return_value = mock_response

        schema = {"users": {}}

        for analysis_type in ['general', 'relationships', 'optimization']:
            result = assistant.analyze_schema(schema, analysis_type=analysis_type)

            assert result.success is True
            assert result.metadata['analysis_type'] == analysis_type

    def test_analyze_schema_api_error(self, mock_assistant):
        """Test schema analysis handles API errors"""
        assistant, mock_client = mock_assistant

        mock_client.messages.create.side_effect = Exception("API error")

        result = assistant.analyze_schema({"users": {}})

        assert result.success is False
        assert "API error" in result.warnings[0]
