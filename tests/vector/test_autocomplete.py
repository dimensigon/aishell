"""Comprehensive tests for semantic autocomplete functionality.

Tests cover:
- Intelligent completion candidates
- Vector-based semantic search
- Pattern-based completions
- Syntax-aware completions
- History-based suggestions
- Context-aware completions
- Query expansion
- Deduplication and scoring
"""

import pytest
import numpy as np
from typing import List
from unittest.mock import Mock, patch

from src.vector.store import VectorDatabase
from src.vector.autocomplete import (
    IntelligentCompleter,
    CompletionCandidate
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def vector_db():
    """Create vector database fixture."""
    return VectorDatabase(dimension=384, use_faiss=False)


@pytest.fixture
def completer(vector_db):
    """Create intelligent completer fixture."""
    return IntelligentCompleter(vector_db)


@pytest.fixture
def populated_completer(vector_db):
    """Create completer with populated vector database."""
    completer = IntelligentCompleter(vector_db)

    def mock_embedding(text):
        np.random.seed(sum(ord(c) for c in text))
        vec = np.random.randn(384)
        return vec / np.linalg.norm(vec)

    # Index sample database objects
    tables = [
        {
            'name': 'users',
            'description': 'User accounts and profiles',
            'schema': 'public',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'User ID'},
                {'name': 'email', 'type': 'varchar', 'description': 'Email address'},
                {'name': 'name', 'type': 'varchar', 'description': 'Full name'}
            ]
        },
        {
            'name': 'orders',
            'description': 'Customer orders',
            'schema': 'public',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Order ID'},
                {'name': 'user_id', 'type': 'integer', 'description': 'User reference'},
                {'name': 'total', 'type': 'decimal', 'description': 'Order total'}
            ]
        },
        {
            'name': 'products',
            'description': 'Product catalog',
            'schema': 'public',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Product ID'},
                {'name': 'name', 'type': 'varchar', 'description': 'Product name'},
                {'name': 'price', 'type': 'decimal', 'description': 'Unit price'}
            ]
        }
    ]

    vector_db.index_database_objects(tables, mock_embedding)
    return completer


def create_random_vector(dim=384):
    """Create random normalized vector."""
    vec = np.random.randn(dim)
    return vec / np.linalg.norm(vec)


# ============================================================================
# Initialization Tests
# ============================================================================


class TestCompleterInit:
    """Tests for IntelligentCompleter initialization."""

    def test_initialization(self, completer, vector_db):
        """Test basic initialization."""
        assert completer.vector_db is vector_db
        assert len(completer.completion_history) == 0
        assert len(completer.pattern_cache) == 0
        assert completer.max_history == 100

    def test_custom_max_history(self, vector_db):
        """Test custom max history setting."""
        completer = IntelligentCompleter(vector_db)
        completer.max_history = 50

        assert completer.max_history == 50


# ============================================================================
# History Management Tests
# ============================================================================


class TestHistoryManagement:
    """Tests for completion history management."""

    def test_add_to_history(self, completer):
        """Test adding completions to history."""
        completer.add_to_history('SELECT * FROM users')
        completer.add_to_history('SELECT id FROM orders')

        assert len(completer.completion_history) == 2
        assert completer.completion_history[0] == 'SELECT * FROM users'
        assert completer.completion_history[1] == 'SELECT id FROM orders'

    def test_history_max_limit(self, completer):
        """Test history respects maximum limit."""
        completer.max_history = 5

        for i in range(10):
            completer.add_to_history(f'query_{i}')

        assert len(completer.completion_history) == 5
        # Should keep most recent
        assert completer.completion_history[-1] == 'query_9'
        assert 'query_0' not in completer.completion_history

    def test_history_fifo_behavior(self, completer):
        """Test FIFO behavior when exceeding limit."""
        completer.max_history = 3

        completer.add_to_history('first')
        completer.add_to_history('second')
        completer.add_to_history('third')
        completer.add_to_history('fourth')

        assert completer.completion_history == ['second', 'third', 'fourth']

    def test_empty_history(self, completer):
        """Test behavior with empty history."""
        query_vec = create_random_vector()
        candidates = completer._get_history_completions('SELECT')

        assert len(candidates) == 0


# ============================================================================
# Pattern-Based Completion Tests
# ============================================================================


class TestPatternCompletions:
    """Tests for pattern-based completions."""

    def test_select_pattern(self, completer):
        """Test SELECT keyword pattern."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('sel', query_vec)

        select_candidates = [c for c in candidates if c.text == 'SELECT']
        assert len(select_candidates) > 0
        assert select_candidates[0].source == 'pattern'
        assert select_candidates[0].score >= 0.9

    def test_where_pattern(self, completer):
        """Test WHERE keyword pattern."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('wh', query_vec)

        where_candidates = [c for c in candidates if c.text == 'WHERE']
        assert len(where_candidates) > 0
        assert where_candidates[0].source == 'pattern'

    def test_from_pattern(self, completer):
        """Test FROM keyword pattern."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('fr', query_vec)

        from_candidates = [c for c in candidates if c.text == 'FROM']
        assert len(from_candidates) > 0
        assert from_candidates[0].source == 'pattern'

    def test_join_patterns(self, completer):
        """Test JOIN keyword patterns."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('join', query_vec)

        join_types = ['INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN']
        join_candidates = [c for c in candidates if c.text in join_types]

        assert len(join_candidates) > 0
        assert all(c.source == 'pattern' for c in join_candidates)

    def test_function_pattern(self, completer):
        """Test function completion pattern."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('SELECT COUNT(', query_vec)

        star_candidates = [c for c in candidates if '*' in c.text]
        assert len(star_candidates) > 0

    def test_case_insensitive_patterns(self, completer):
        """Test patterns work case-insensitively."""
        query_vec = create_random_vector()

        lower_candidates = completer.get_completions('select', query_vec)
        upper_candidates = completer.get_completions('SELECT', query_vec)
        mixed_candidates = completer.get_completions('SeLeCt', query_vec)

        # All should produce SELECT suggestions
        assert any(c.text == 'SELECT' for c in lower_candidates)
        assert any(c.text == 'SELECT' for c in upper_candidates)
        assert any(c.text == 'SELECT' for c in mixed_candidates)

    def test_pattern_registration(self, completer):
        """Test registering custom patterns."""
        completer.register_pattern('CUSTOM', ['CUSTOM1', 'CUSTOM2', 'CUSTOM3'])

        assert 'CUSTOM' in completer.pattern_cache
        assert len(completer.pattern_cache['CUSTOM']) == 3
        assert 'CUSTOM1' in completer.pattern_cache['CUSTOM']


# ============================================================================
# Syntax-Based Completion Tests
# ============================================================================


class TestSyntaxCompletions:
    """Tests for syntax-aware completions."""

    def test_unclosed_parenthesis(self, completer):
        """Test completion for unclosed parenthesis."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('SELECT COUNT(', query_vec)

        close_paren = [c for c in candidates if c.text == ')']
        assert len(close_paren) > 0
        assert close_paren[0].source == 'syntax'

    def test_multiple_unclosed_parentheses(self, completer):
        """Test multiple unclosed parentheses."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('SELECT MAX(COUNT(', query_vec)

        close_paren = [c for c in candidates if c.text == ')']
        assert len(close_paren) > 0

    def test_unclosed_quote(self, completer):
        """Test completion for unclosed quote."""
        query_vec = create_random_vector()
        candidates = completer.get_completions("SELECT * FROM users WHERE name='test", query_vec)

        close_quote = [c for c in candidates if c.text == "'"]
        assert len(close_quote) > 0
        assert close_quote[0].source == 'syntax'

    def test_balanced_parentheses(self, completer):
        """Test no suggestion when parentheses balanced."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('SELECT COUNT(*)', query_vec)

        # Should not suggest closing paren
        syntax_parens = [c for c in candidates if c.text == ')' and c.source == 'syntax']
        assert len(syntax_parens) == 0

    def test_balanced_quotes(self, completer):
        """Test no suggestion when quotes balanced."""
        query_vec = create_random_vector()
        candidates = completer.get_completions("SELECT * FROM users WHERE name='test'", query_vec)

        # Should not suggest closing quote
        syntax_quotes = [c for c in candidates if c.text == "'" and c.source == 'syntax']
        assert len(syntax_quotes) == 0

    def test_syntax_scoring(self, completer):
        """Test syntax completions have appropriate scores."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('SELECT COUNT(', query_vec)

        syntax_candidates = [c for c in candidates if c.source == 'syntax']
        for candidate in syntax_candidates:
            assert 0.7 <= candidate.score <= 0.9


# ============================================================================
# History-Based Completion Tests
# ============================================================================


class TestHistoryCompletions:
    """Tests for history-based completions."""

    def test_history_matching(self, completer):
        """Test history-based completions."""
        completer.add_to_history('SELECT * FROM users WHERE active = true')
        completer.add_to_history('SELECT id FROM orders')

        query_vec = create_random_vector()
        candidates = completer.get_completions('SELECT', query_vec)

        history_candidates = [c for c in candidates if c.source == 'history']
        assert len(history_candidates) > 0

    def test_history_prefix_matching(self, completer):
        """Test history completions match prefix."""
        completer.add_to_history('SELECT * FROM users')
        completer.add_to_history('INSERT INTO users VALUES')
        completer.add_to_history('DELETE FROM orders')

        query_vec = create_random_vector()
        candidates = completer.get_completions('SEL', query_vec)

        history_candidates = [c for c in candidates if c.source == 'history']
        # Should only suggest SELECT query
        assert all('SELECT' in c.text for c in history_candidates)

    def test_history_recency_scoring(self, completer):
        """Test more recent history has higher scores."""
        completer.add_to_history('SELECT old')
        completer.add_to_history('SELECT newer')
        completer.add_to_history('SELECT newest')

        query_vec = create_random_vector()
        candidates = completer._get_history_completions('SELECT')

        # More recent should have higher scores
        if len(candidates) >= 2:
            newest = [c for c in candidates if 'newest' in c.text]
            older = [c for c in candidates if 'old' in c.text and 'older' not in c.text]
            if newest and older:
                assert newest[0].score >= older[0].score

    def test_history_excludes_exact_match(self, completer):
        """Test history doesn't suggest exact current query."""
        completer.add_to_history('SELECT * FROM users')

        query_vec = create_random_vector()
        candidates = completer._get_history_completions('SELECT * FROM users')

        # Should not suggest exact match
        assert not any(c.text == 'SELECT * FROM users' for c in candidates)

    def test_history_limit(self, completer):
        """Test history only uses recent entries."""
        # Add many entries
        for i in range(100):
            completer.add_to_history(f'SELECT query_{i}')

        query_vec = create_random_vector()
        candidates = completer._get_history_completions('SELECT')

        # Should only check last 20
        old_queries = [c for c in candidates if 'query_0' in c.text]
        assert len(old_queries) == 0


# ============================================================================
# Vector-Based Completion Tests
# ============================================================================


class TestVectorCompletions:
    """Tests for vector-based semantic completions."""

    def test_vector_completions_basic(self, populated_completer):
        """Test basic vector-based completions."""
        def mock_embedding(text):
            np.random.seed(sum(ord(c) for c in text))
            vec = np.random.randn(384)
            return vec / np.linalg.norm(vec)

        query = 'user accounts'
        query_vector = mock_embedding(query)

        candidates = populated_completer._get_vector_completions(
            query_vector,
            context={},
            max_results=5
        )

        assert len(candidates) > 0
        # Should find users table due to semantic similarity
        user_candidates = [c for c in candidates if 'users' in c.text.lower()]
        assert len(user_candidates) > 0

    def test_vector_completions_with_type_filter(self, populated_completer):
        """Test vector completions with type filter."""
        def mock_embedding(text):
            np.random.seed(sum(ord(c) for c in text))
            vec = np.random.randn(384)
            return vec / np.linalg.norm(vec)

        query_vector = mock_embedding('table')
        candidates = populated_completer._get_vector_completions(
            query_vector,
            context={'object_type': 'table'},
            max_results=10
        )

        # Should only return tables
        assert all(c.metadata.get('name') in ['users', 'orders', 'products']
                   for c in candidates if 'table' in c.metadata.get('type', '').lower()
                   or len(c.metadata) > 0)

    def test_vector_completions_scoring(self, populated_completer):
        """Test vector completions have proper scoring."""
        def mock_embedding(text):
            np.random.seed(sum(ord(c) for c in text))
            vec = np.random.randn(384)
            return vec / np.linalg.norm(vec)

        query_vector = mock_embedding('users')
        candidates = populated_completer._get_vector_completions(
            query_vector,
            context={},
            max_results=5
        )

        # All scores should be reasonable
        for candidate in candidates:
            assert 0.0 <= candidate.score <= 1.0

    def test_vector_completions_empty_db(self, completer):
        """Test vector completions with empty database."""
        query_vector = create_random_vector()
        candidates = completer._get_vector_completions(
            query_vector,
            context={},
            max_results=5
        )

        assert len(candidates) == 0


# ============================================================================
# Deduplication Tests
# ============================================================================


class TestDeduplication:
    """Tests for candidate deduplication."""

    def test_deduplicate_identical_text(self, completer):
        """Test deduplication of identical candidates."""
        candidates = [
            CompletionCandidate('SELECT', 0.9, {}, 'pattern'),
            CompletionCandidate('SELECT', 0.7, {}, 'history'),
            CompletionCandidate('FROM', 0.8, {}, 'pattern')
        ]

        unique = completer._deduplicate_candidates(candidates)

        assert len(unique) == 2
        # Should keep highest score
        select_candidate = [c for c in unique if c.text == 'SELECT'][0]
        assert select_candidate.score == 0.9

    def test_deduplicate_keeps_best_source(self, completer):
        """Test deduplication keeps best scoring source."""
        candidates = [
            CompletionCandidate('users', 0.5, {}, 'history'),
            CompletionCandidate('users', 0.8, {}, 'vector'),
            CompletionCandidate('users', 0.6, {}, 'pattern')
        ]

        unique = completer._deduplicate_candidates(candidates)

        assert len(unique) == 1
        assert unique[0].source == 'vector'
        assert unique[0].score == 0.8

    def test_deduplicate_preserves_different_text(self, completer):
        """Test different text is not deduplicated."""
        candidates = [
            CompletionCandidate('SELECT', 0.9, {}, 'pattern'),
            CompletionCandidate('WHERE', 0.8, {}, 'pattern'),
            CompletionCandidate('FROM', 0.7, {}, 'pattern')
        ]

        unique = completer._deduplicate_candidates(candidates)

        assert len(unique) == 3


# ============================================================================
# Context-Aware Completion Tests
# ============================================================================


class TestContextAwareCompletions:
    """Tests for context-aware completions."""

    def test_select_from_context(self, populated_completer):
        """Test context-aware completions after FROM."""
        def mock_embedding(text):
            np.random.seed(sum(ord(c) for c in text))
            vec = np.random.randn(384)
            return vec / np.linalg.norm(vec)

        query = 'SELECT * FROM '
        query_vector = mock_embedding(query)

        candidates = populated_completer.get_context_aware_completions(
            query=query,
            query_vector=query_vector,
            statement_type='SELECT',
            cursor_position=len(query)
        )

        # Should suggest tables after FROM
        table_names = ['users', 'orders', 'products']
        assert any(any(table in c.text for table in table_names) for c in candidates)

    def test_select_column_context(self, populated_completer):
        """Test context-aware completions after SELECT."""
        def mock_embedding(text):
            np.random.seed(sum(ord(c) for c in text))
            vec = np.random.randn(384)
            return vec / np.linalg.norm(vec)

        query = 'SELECT '
        query_vector = mock_embedding(query)

        candidates = populated_completer.get_context_aware_completions(
            query=query,
            query_vector=query_vector,
            statement_type='SELECT',
            cursor_position=len(query)
        )

        # Context should indicate columns expected
        assert len(candidates) > 0

    def test_insert_table_context(self, populated_completer):
        """Test context-aware completions for INSERT."""
        def mock_embedding(text):
            np.random.seed(sum(ord(c) for c in text))
            vec = np.random.randn(384)
            return vec / np.linalg.norm(vec)

        query = 'INSERT INTO '
        query_vector = mock_embedding(query)

        candidates = populated_completer.get_context_aware_completions(
            query=query,
            query_vector=query_vector,
            statement_type='INSERT',
            cursor_position=len(query)
        )

        # Should suggest tables
        assert len(candidates) > 0


# ============================================================================
# Integrated Completion Tests
# ============================================================================


class TestIntegratedCompletions:
    """Tests for integrated completion system."""

    def test_multi_source_completions(self, populated_completer):
        """Test completions from multiple sources."""
        populated_completer.add_to_history('SELECT * FROM users')

        query_vec = create_random_vector()
        candidates = populated_completer.get_completions('sel', query_vec)

        sources = set(c.source for c in candidates)
        # Should have multiple sources
        assert len(sources) > 1

    def test_max_results_limit(self, populated_completer):
        """Test max_results parameter."""
        # Add lots of history
        for i in range(20):
            populated_completer.add_to_history(f'SELECT query_{i}')

        query_vec = create_random_vector()
        candidates = populated_completer.get_completions('SELECT', query_vec, max_results=5)

        assert len(candidates) <= 5

    def test_completion_sorting(self, populated_completer):
        """Test completions are sorted by score."""
        query_vec = create_random_vector()
        candidates = populated_completer.get_completions('sel', query_vec)

        # Verify descending order
        for i in range(len(candidates) - 1):
            assert candidates[i].score >= candidates[i + 1].score

    def test_empty_query(self, completer):
        """Test completions with empty query."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('', query_vec)

        # Should still return some candidates
        assert isinstance(candidates, list)

    def test_completion_metadata(self, populated_completer):
        """Test completion candidates include metadata."""
        query_vec = create_random_vector()
        candidates = populated_completer.get_completions('sel', query_vec)

        for candidate in candidates:
            assert hasattr(candidate, 'text')
            assert hasattr(candidate, 'score')
            assert hasattr(candidate, 'metadata')
            assert hasattr(candidate, 'source')

    def test_score_ranges(self, populated_completer):
        """Test all scores are in valid range."""
        query_vec = create_random_vector()
        candidates = populated_completer.get_completions('SELECT', query_vec)

        for candidate in candidates:
            assert 0.0 <= candidate.score <= 1.0


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Tests for completion performance."""

    def test_completion_speed(self, populated_completer):
        """Test completion response time."""
        import time

        query_vec = create_random_vector()

        start = time.time()
        candidates = populated_completer.get_completions('SELECT', query_vec, max_results=10)
        duration = time.time() - start

        assert len(candidates) > 0
        assert duration < 0.5  # Should be fast

    def test_large_history_performance(self, populated_completer):
        """Test performance with large history."""
        import time

        # Add many history items
        for i in range(1000):
            populated_completer.add_to_history(f'SELECT * FROM table_{i}')

        query_vec = create_random_vector()

        start = time.time()
        candidates = populated_completer.get_completions('SELECT', query_vec, max_results=10)
        duration = time.time() - start

        assert len(candidates) > 0
        assert duration < 1.0  # Should still be reasonably fast


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_unicode_query(self, completer):
        """Test completions with Unicode query."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('СЕЛЕКТ', query_vec)  # Russian

        assert isinstance(candidates, list)

    def test_very_long_query(self, completer):
        """Test with very long query string."""
        long_query = 'SELECT ' * 100
        query_vec = create_random_vector()

        candidates = completer.get_completions(long_query, query_vec)

        assert isinstance(candidates, list)

    def test_special_characters_query(self, completer):
        """Test query with special characters."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('SELECT@#$%', query_vec)

        assert isinstance(candidates, list)

    def test_whitespace_only_query(self, completer):
        """Test query with only whitespace."""
        query_vec = create_random_vector()
        candidates = completer.get_completions('   ', query_vec)

        assert isinstance(candidates, list)
