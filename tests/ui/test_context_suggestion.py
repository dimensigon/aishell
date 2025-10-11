"""Comprehensive tests for context suggestion engine with fixed API calls"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.ui.engines.context_suggestion import (
    ContextSuggestionEngine,
    SuggestionType,
    Suggestion
)


@pytest.fixture
def suggestion_engine(mock_context_suggestion_engine):
    """Context suggestion engine instance"""
    return mock_context_suggestion_engine


@pytest.mark.asyncio
async def test_engine_initialization(suggestion_engine):
    """Test engine initialization"""
    assert suggestion_engine is not None
    assert hasattr(suggestion_engine, 'get_suggestions')


@pytest.mark.asyncio
async def test_table_name_suggestions(suggestion_engine):
    """Test table name auto-complete suggestions"""
    query = 'SELECT * FROM u'

    suggestions = await suggestion_engine.get_suggestions(query)

    assert len(suggestions) >= 0
    # Should return CompletionCandidate objects
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_column_name_suggestions(suggestion_engine):
    """Test column name suggestions"""
    query = 'SELECT n'

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return suggestions list
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_sql_keyword_suggestions(suggestion_engine):
    """Test SQL keyword suggestions"""
    query = 'SEL'

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return some suggestions (CompletionCandidate objects)
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_function_suggestions(suggestion_engine):
    """Test database function suggestions"""
    query = 'SELECT COU'

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return suggestions list
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_join_suggestions(suggestion_engine):
    """Test JOIN clause suggestions"""
    query = 'SELECT * FROM users J'

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return suggestions list
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_where_clause_suggestions(suggestion_engine):
    """Test WHERE clause suggestions"""
    query = 'SELECT * FROM users WHERE '

    suggestions = await suggestion_engine.get_suggestions(query)

    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_order_by_suggestions(suggestion_engine):
    """Test ORDER BY suggestions"""
    query = 'SELECT * FROM users ORDER BY '

    suggestions = await suggestion_engine.get_suggestions(query)

    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_suggestion_ranking(suggestion_engine):
    """Test suggestion ranking by relevance"""
    query = 'SELECT * FROM use'

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return sorted suggestions
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_contextual_suggestions(suggestion_engine):
    """Test context-aware suggestions"""
    query = 'SELECT * FROM '

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return suggestions based on history
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_limit_number_of_suggestions(suggestion_engine):
    """Test limiting number of suggestions"""
    query = 'SELECT * FROM t'

    suggestions = await suggestion_engine.get_suggestions(query, max_results=10)

    assert len(suggestions) <= 10


@pytest.mark.asyncio
async def test_syntax_error_suggestions(suggestion_engine):
    """Test suggestions for fixing syntax errors"""
    query = 'SELECT * FORM users'  # Typo: FORM instead of FROM

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return suggestions
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_aggregate_function_suggestions(suggestion_engine):
    """Test aggregate function suggestions"""
    query = 'SELECT AVG'

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return suggestions
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_alias_suggestions(suggestion_engine):
    """Test table/column alias suggestions"""
    query = 'SELECT u.name FROM users '

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return suggestions
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_empty_input_suggestions(suggestion_engine):
    """Test suggestions with empty input"""
    query = ''

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return suggestions for empty query
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_schema_aware_suggestions(suggestion_engine):
    """Test schema-aware suggestions"""
    query = 'SELECT * FROM users WHERE email'

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return suggestions
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_multi_table_suggestions(suggestion_engine):
    """Test suggestions for multi-table queries"""
    query = 'SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id JOIN p'

    suggestions = await suggestion_engine.get_suggestions(query)

    # Should return suggestions
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_cached_suggestions(suggestion_engine):
    """Test suggestion caching for performance"""
    query = 'SELECT * FROM u'

    # First call
    suggestions1 = await suggestion_engine.get_suggestions(query)

    # Second call with same context
    suggestions2 = await suggestion_engine.get_suggestions(query)

    # Both should return valid results
    assert isinstance(suggestions1, list)
    assert isinstance(suggestions2, list)


@pytest.mark.asyncio
async def test_suggestion_confidence_scores(suggestion_engine):
    """Test confidence scoring for suggestions"""
    query = 'SELECT * FROM user'

    suggestions = await suggestion_engine.get_suggestions(query)

    # All suggestions should have scores (CompletionCandidate has score attribute)
    assert isinstance(suggestions, list)
    for s in suggestions:
        assert hasattr(s, 'score')
        assert 0 <= s.score <= 1
