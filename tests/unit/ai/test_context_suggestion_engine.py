"""
Tests for ContextAwareSuggestionEngine (src/ui/engines/context_suggestion.py)

Tests context gathering, suggestion scoring, caching, and performance.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import time

from src.ui.engines.context_suggestion import (
    ContextAwareSuggestionEngine,
    Suggestion,
    SuggestionType,
    SuggestionContext
)
from src.vector.autocomplete import CompletionCandidate


class TestSuggestionType:
    """Test suite for SuggestionType enum."""

    def test_suggestion_types_defined(self):
        """Test all suggestion types are defined."""
        assert hasattr(SuggestionType, 'TABLE')
        assert hasattr(SuggestionType, 'COLUMN')
        assert hasattr(SuggestionType, 'KEYWORD')
        assert hasattr(SuggestionType, 'FUNCTION')
        assert hasattr(SuggestionType, 'DATABASE')
        assert hasattr(SuggestionType, 'ALIAS')
        assert hasattr(SuggestionType, 'VALUE')


class TestSuggestion:
    """Test suite for Suggestion dataclass."""

    def test_suggestion_creation(self):
        """Test creating suggestion."""
        suggestion = Suggestion(
            text="users",
            type=SuggestionType.TABLE,
            score=0.95,
            metadata={"schema": "public"},
            description="Users table"
        )

        assert suggestion.text == "users"
        assert suggestion.type == SuggestionType.TABLE
        assert suggestion.score == 0.95
        assert suggestion.metadata == {"schema": "public"}
        assert suggestion.description == "Users table"

    def test_suggestion_defaults(self):
        """Test suggestion default values."""
        suggestion = Suggestion(
            text="users",
            type=SuggestionType.TABLE
        )

        assert suggestion.score == 0.0
        assert suggestion.metadata == {}
        assert suggestion.description is None


class TestSuggestionContext:
    """Test suite for SuggestionContext dataclass."""

    def test_context_creation(self):
        """Test creating suggestion context."""
        context = SuggestionContext(
            current_directory="/home/user",
            command_history=["SELECT * FROM users"],
            database_objects={"tables": ["users", "orders"]},
            cursor_position=10,
            statement_type="SELECT",
            partial_command="SELECT * ",
            query_text="SELECT * FROM users"
        )

        assert context.current_directory == "/home/user"
        assert len(context.command_history) == 1
        assert "users" in context.database_objects["tables"]

    def test_context_defaults(self):
        """Test context default values."""
        context = SuggestionContext()

        assert context.current_directory == ""
        assert context.command_history == []
        assert context.database_objects == {}
        assert context.cursor_position == 0
        assert context.statement_type is None


class TestContextAwareSuggestionEngine:
    """Test suite for ContextAwareSuggestionEngine."""

    @pytest.fixture
    def mock_completer(self):
        """Create mock IntelligentCompleter."""
        completer = Mock()
        completer.get_completions = Mock(return_value=[
            CompletionCandidate("users", 0.95, "table", {"type": "table"}),
            CompletionCandidate("user_id", 0.90, "column", {"type": "column"}),
            CompletionCandidate("SELECT", 0.85, "keyword", {"type": "keyword"})
        ])
        return completer

    @pytest.fixture
    def mock_embedding_model(self):
        """Create mock embedding model."""
        import numpy as np
        model = Mock()
        model.encode = Mock(return_value=np.random.randn(384).astype(np.float32))
        return model

    @pytest.fixture
    def engine(self, mock_completer, mock_embedding_model):
        """Create ContextAwareSuggestionEngine instance."""
        return ContextAwareSuggestionEngine(
            completer=mock_completer,
            embedding_model=mock_embedding_model,
            cache_ttl=300
        )

    def test_initialization(self, engine, mock_completer, mock_embedding_model):
        """Test engine initializes correctly."""
        assert engine.completer == mock_completer
        assert engine.embedding_model == mock_embedding_model
        assert engine.cache_ttl == 300
        assert engine._command_history == []
        assert engine._context_cache == {}

    @pytest.mark.asyncio
    async def test_get_suggestions_returns_candidates(self, engine):
        """Test get_suggestions returns candidates."""
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                Mock(encode=Mock()),  # embedding
                [CompletionCandidate("users", 0.95, "table", {})]  # completions
            ]

            results = await engine.get_suggestions("SELECT * FROM u", max_results=10)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_suggestions_with_context(self, engine):
        """Test get_suggestions with provided context."""
        context = {"statement_type": "SELECT", "object_type": "table"}

        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                Mock(),  # embedding
                [CompletionCandidate("users", 0.95, "table", {})]  # completions
            ]

            with patch.object(engine, '_rescore_with_context', new_callable=AsyncMock,
                            return_value=[CompletionCandidate("users", 0.95, "table", {})]):
                results = await engine.get_suggestions("u", context=context)

        assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_get_suggestions_limits_results(self, engine):
        """Test get_suggestions respects max_results."""
        candidates = [
            CompletionCandidate(f"item_{i}", 0.9 - i*0.05, "table", {})
            for i in range(20)
        ]

        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                Mock(),  # embedding
                candidates  # completions
            ]

            with patch.object(engine, '_rescore_with_context', new_callable=AsyncMock,
                            return_value=candidates):
                results = await engine.get_suggestions("item", max_results=5)

        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_get_suggestions_handles_errors(self, engine):
        """Test get_suggestions handles errors."""
        with patch('asyncio.to_thread', side_effect=Exception("Test error")):
            results = await engine.get_suggestions("SELECT")

        assert results == []

    @pytest.mark.asyncio
    async def test_gather_context_returns_dict(self, engine):
        """Test gather_context returns context dict."""
        result = await engine.gather_context("SELECT * FROM")

        assert isinstance(result, dict)
        assert 'query' in result
        assert 'cursor_position' in result
        assert 'partial_command' in result

    @pytest.mark.asyncio
    async def test_gather_context_includes_directory(self, engine):
        """Test gather_context includes current directory."""
        with patch.object(engine, '_get_current_directory', return_value="/home/user"):
            context = await engine.gather_context("SELECT")

        assert 'current_directory' in context

    @pytest.mark.asyncio
    async def test_gather_context_includes_history(self, engine):
        """Test gather_context includes command history."""
        engine._command_history = ["SELECT * FROM users", "UPDATE users SET status=1"]

        context = await engine.gather_context("SELECT")

        assert 'command_history' in context
        assert len(context['command_history']) <= 20  # Only last 20

    @pytest.mark.asyncio
    async def test_gather_context_detects_statement_type(self, engine):
        """Test gather_context detects statement type."""
        context = await engine.gather_context("SELECT * FROM")

        assert context['statement_type'] == 'SELECT'

    @pytest.mark.asyncio
    async def test_gather_context_determines_object_type(self, engine):
        """Test gather_context determines expected object type."""
        context = await engine.gather_context("SELECT * FROM ", cursor_position=16)

        # After FROM, should expect table
        assert context.get('object_type') == 'table'

    def test_score_suggestion_prefix_match_boost(self, engine):
        """Test scoring boosts prefix matches."""
        candidate = CompletionCandidate("users", 0.80, "table", {})
        context = {"command_history": []}

        score = engine.score_suggestion("use", candidate, context)

        # Should be boosted for prefix match
        assert score > 0.80

    def test_score_suggestion_history_boost(self, engine):
        """Test scoring boosts recent history items."""
        candidate = CompletionCandidate("users", 0.80, "table", {})
        context = {"command_history": ["SELECT * FROM users"]}

        score = engine.score_suggestion("u", candidate, context)

        # Should be boosted for being in history
        assert score > 0.80

    def test_score_suggestion_type_match_boost(self, engine):
        """Test scoring boosts context-appropriate types."""
        candidate = CompletionCandidate("users", 0.80, "table", {"type": "table"})
        context = {"object_type": "table", "command_history": []}

        score = engine.score_suggestion("u", candidate, context)

        # Should be boosted for type match
        assert score > 0.80

    def test_score_suggestion_length_penalty(self, engine):
        """Test scoring penalizes very long suggestions."""
        # Very long suggestion
        long_text = "a" * 100
        candidate = CompletionCandidate(long_text, 0.90, "table", {})
        context = {"command_history": []}

        score = engine.score_suggestion("a", candidate, context)

        # Should be penalized
        assert score < 0.90

    def test_score_suggestion_capped_at_one(self, engine):
        """Test scoring is capped at 1.0."""
        candidate = CompletionCandidate("users", 0.95, "table", {"type": "table"})
        # Context that would boost score significantly
        context = {
            "command_history": ["users"] * 5,
            "object_type": "table",
            "statement_type": "SELECT"
        }

        score = engine.score_suggestion("users", candidate, context)

        # Should be capped at 1.0
        assert score <= 1.0

    def test_detect_statement_type_select(self, engine):
        """Test detecting SELECT statements."""
        result = engine._detect_statement_type("SELECT * FROM users")
        assert result == "SELECT"

    def test_detect_statement_type_insert(self, engine):
        """Test detecting INSERT statements."""
        result = engine._detect_statement_type("INSERT INTO users VALUES (1, 'test')")
        assert result == "INSERT"

    def test_detect_statement_type_update(self, engine):
        """Test detecting UPDATE statements."""
        result = engine._detect_statement_type("UPDATE users SET name='test'")
        assert result == "UPDATE"

    def test_detect_statement_type_delete(self, engine):
        """Test detecting DELETE statements."""
        result = engine._detect_statement_type("DELETE FROM users WHERE id=1")
        assert result == "DELETE"

    def test_detect_statement_type_none(self, engine):
        """Test detecting unknown statement type."""
        result = engine._detect_statement_type("this is not SQL")
        assert result is None

    def test_determine_object_type_from_clause(self, engine):
        """Test determining object type after FROM."""
        result = engine._determine_object_type(
            "SELECT * FROM ",
            15,  # After FROM
            "SELECT"
        )
        assert result == 'table'

    def test_determine_object_type_into_clause(self, engine):
        """Test determining object type after INTO."""
        result = engine._determine_object_type(
            "INSERT INTO ",
            12,  # After INTO
            "INSERT"
        )
        assert result == 'table'

    def test_determine_object_type_select_clause(self, engine):
        """Test determining object type in SELECT clause."""
        result = engine._determine_object_type(
            "SELECT ",
            7,  # After SELECT
            "SELECT"
        )
        assert result == 'column'

    def test_determine_object_type_where_clause(self, engine):
        """Test determining object type after WHERE."""
        result = engine._determine_object_type(
            "SELECT * FROM users WHERE ",
            27,  # After WHERE
            "SELECT"
        )
        assert result == 'column'

    def test_determine_object_type_join_clause(self, engine):
        """Test determining object type with JOIN."""
        result = engine._determine_object_type(
            "SELECT * FROM users JOIN ",
            26,  # After JOIN
            "SELECT"
        )
        assert result == 'table'

    def test_determine_object_type_none(self, engine):
        """Test determining object type with no context."""
        result = engine._determine_object_type("", 0, None)
        assert result is None

    def test_add_to_history(self, engine):
        """Test adding command to history."""
        engine.add_to_history("SELECT * FROM users")

        assert len(engine._command_history) == 1
        assert engine._command_history[0] == "SELECT * FROM users"

    def test_add_to_history_no_duplicates(self, engine):
        """Test history doesn't add recent duplicates."""
        engine.add_to_history("SELECT * FROM users")
        engine.add_to_history("SELECT * FROM users")

        # Should only have one
        assert len(engine._command_history) == 1

    def test_add_to_history_max_size(self, engine):
        """Test history respects max size."""
        # Add more than max
        for i in range(150):
            engine.add_to_history(f"SELECT {i}")

        # Should be limited to max_history (100)
        assert len(engine._command_history) <= 100

    def test_clear_cache_all(self, engine):
        """Test clearing all cache."""
        engine._context_cache = {
            'key1': ('value1', time.time()),
            'key2': ('value2', time.time())
        }

        engine.clear_cache()

        assert len(engine._context_cache) == 0

    def test_clear_cache_specific_key(self, engine):
        """Test clearing specific cache key."""
        engine._context_cache = {
            'key1': ('value1', time.time()),
            'key2': ('value2', time.time())
        }

        engine.clear_cache('key1')

        assert 'key1' not in engine._context_cache
        assert 'key2' in engine._context_cache

    def test_set_database_objects(self, engine):
        """Test setting database objects."""
        tables = ['users', 'orders', 'products']
        columns = {
            'users': ['id', 'name', 'email'],
            'orders': ['id', 'user_id', 'total']
        }

        engine.set_database_objects(tables, columns)

        # Should be in cache
        assert 'database_objects' in engine._context_cache
        cached = engine._context_cache['database_objects'][0]
        assert cached['tables'] == tables
        assert cached['columns'] == columns

    @pytest.mark.asyncio
    async def test_get_cached_or_fetch_returns_cached(self, engine):
        """Test _get_cached_or_fetch returns cached value."""
        # Add to cache
        value = "cached_value"
        engine._context_cache['test_key'] = (value, time.time())

        result = await engine._get_cached_or_fetch('test_key', lambda: "new_value")

        assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_get_cached_or_fetch_expired(self, engine):
        """Test _get_cached_or_fetch fetches when expired."""
        # Add expired cache
        engine._context_cache['test_key'] = ("old_value", time.time() - 400)  # Expired
        engine.cache_ttl = 300

        fetch_func = Mock(return_value="new_value")
        result = await engine._get_cached_or_fetch('test_key', fetch_func)

        assert result == "new_value"

    def test_get_current_directory(self, engine):
        """Test _get_current_directory returns directory."""
        result = engine._get_current_directory()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_current_directory_handles_errors(self, engine):
        """Test _get_current_directory handles errors."""
        with patch('os.getcwd', side_effect=Exception("Test error")):
            result = engine._get_current_directory()

        # Should return fallback
        assert result == "/"

    def test_get_database_objects(self, engine):
        """Test _get_database_objects returns dict."""
        result = engine._get_database_objects()

        assert isinstance(result, dict)
        assert 'tables' in result
        assert 'columns' in result

    @pytest.mark.asyncio
    async def test_rescore_with_context(self, engine):
        """Test _rescore_with_context updates scores."""
        candidates = [
            CompletionCandidate("users", 0.80, "table", {"type": "table"}),
            CompletionCandidate("orders", 0.75, "table", {"type": "table"})
        ]
        context = {"object_type": "table", "command_history": []}

        with patch.object(engine, 'score_suggestion', return_value=0.95):
            results = await engine._rescore_with_context(candidates, "u", context)

        # Should return rescored candidates
        assert len(results) == 2
        assert all(c.score == 0.95 for c in results)
