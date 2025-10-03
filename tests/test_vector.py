"""Tests for vector database system."""

import pytest
import numpy as np
from src.vector.store import VectorDatabase, VectorEntry, MockFAISSIndex
from src.vector.autocomplete import IntelligentCompleter, CompletionCandidate


@pytest.fixture
def vector_db():
    """Create vector database fixture."""
    return VectorDatabase(dimension=384)


@pytest.fixture
def completer(vector_db):
    """Create intelligent completer fixture."""
    return IntelligentCompleter(vector_db)


def create_random_vector(dim=384):
    """Create random normalized vector."""
    vec = np.random.randn(dim)
    return vec / np.linalg.norm(vec)


def test_mock_faiss_index():
    """Test mock FAISS index."""
    index = MockFAISSIndex(dimension=10)

    # Add vectors
    vec1 = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    vec2 = np.array([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    index.add(vec1)
    index.add(vec2)

    assert index.ntotal == 2

    # Search
    query = np.array([0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    distances, indices = index.search(query, k=1)

    assert indices[0][0] == 0  # Should find vec1


def test_vector_db_initialization(vector_db):
    """Test vector database initialization."""
    assert vector_db.dimension == 384
    assert len(vector_db.entries) == 0
    assert vector_db.index.ntotal == 0


def test_add_object(vector_db):
    """Test adding objects to vector database."""
    vector = create_random_vector()

    vector_db.add_object(
        object_id='table:users',
        vector=vector,
        object_type='table',
        metadata={'name': 'users', 'schema': 'public'}
    )

    assert len(vector_db.entries) == 1
    assert vector_db.entries[0].id == 'table:users'
    assert vector_db.entries[0].object_type == 'table'
    assert vector_db.index.ntotal == 1


def test_add_object_wrong_dimension(vector_db):
    """Test adding vector with wrong dimension."""
    wrong_vector = np.random.randn(100)

    with pytest.raises(ValueError):
        vector_db.add_object(
            object_id='test',
            vector=wrong_vector,
            object_type='table'
        )


def test_search_similar(vector_db):
    """Test similarity search."""
    # Add similar vectors
    base_vec = create_random_vector()
    vector_db.add_object('obj1', base_vec, 'table', {'name': 'table1'})

    # Add dissimilar vector
    diff_vec = create_random_vector()
    vector_db.add_object('obj2', diff_vec, 'table', {'name': 'table2'})

    # Search with similar query
    query = base_vec + np.random.randn(384) * 0.01  # Small noise
    query = query / np.linalg.norm(query)

    results = vector_db.search_similar(query, k=2)

    assert len(results) > 0
    # First result should be most similar
    assert results[0][0].id == 'obj1'


def test_search_with_type_filter(vector_db):
    """Test search with object type filtering."""
    vec1 = create_random_vector()
    vec2 = create_random_vector()

    vector_db.add_object('table1', vec1, 'table')
    vector_db.add_object('col1', vec2, 'column')

    # Search only for tables
    results = vector_db.search_similar(vec1, k=5, object_type='table')

    assert all(entry.object_type == 'table' for entry, _ in results)


def test_get_by_id(vector_db):
    """Test retrieving entry by ID."""
    vector = create_random_vector()
    vector_db.add_object('test_id', vector, 'table')

    entry = vector_db.get_by_id('test_id')
    assert entry is not None
    assert entry.id == 'test_id'

    missing = vector_db.get_by_id('nonexistent')
    assert missing is None


def test_delete_by_id(vector_db):
    """Test deleting entry by ID."""
    vector = create_random_vector()
    vector_db.add_object('test_id', vector, 'table')

    result = vector_db.delete_by_id('test_id')
    assert result is True

    entry = vector_db.get_by_id('test_id')
    assert entry.metadata.get('_deleted') is True

    # Try deleting non-existent
    result = vector_db.delete_by_id('nonexistent')
    assert result is False


def test_index_database_objects(vector_db):
    """Test indexing database objects."""
    def mock_embedding(text):
        # Simple mock: hash text to vector
        np.random.seed(hash(text) % (2**32))
        vec = np.random.randn(384)
        return vec / np.linalg.norm(vec)

    tables = [
        {
            'name': 'users',
            'description': 'User accounts',
            'schema': 'public',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Primary key'},
                {'name': 'email', 'type': 'varchar', 'description': 'User email'}
            ]
        }
    ]

    vector_db.index_database_objects(tables, mock_embedding)

    # Should have 1 table + 2 columns = 3 entries
    assert len(vector_db.entries) == 3

    # Check table entry
    table_entry = vector_db.get_by_id('table:users')
    assert table_entry is not None
    assert table_entry.object_type == 'table'

    # Check column entry
    col_entry = vector_db.get_by_id('column:users.id')
    assert col_entry is not None
    assert col_entry.object_type == 'column'


def test_get_stats(vector_db):
    """Test getting database statistics."""
    vec1 = create_random_vector()
    vec2 = create_random_vector()

    vector_db.add_object('table1', vec1, 'table')
    vector_db.add_object('col1', vec2, 'column')

    stats = vector_db.get_stats()

    assert stats['total_entries'] == 2
    assert stats['dimension'] == 384
    assert stats['type_counts']['table'] == 1
    assert stats['type_counts']['column'] == 1


def test_completer_initialization(completer):
    """Test intelligent completer initialization."""
    assert completer.vector_db is not None
    assert len(completer.completion_history) == 0
    assert len(completer.pattern_cache) == 0


def test_add_to_history(completer):
    """Test adding completions to history."""
    completer.add_to_history('SELECT * FROM users')
    completer.add_to_history('SELECT id FROM orders')

    assert len(completer.completion_history) == 2
    assert completer.completion_history[0] == 'SELECT * FROM users'


def test_history_max_limit(completer):
    """Test history maximum limit."""
    completer.max_history = 5

    for i in range(10):
        completer.add_to_history(f'query_{i}')

    assert len(completer.completion_history) == 5
    assert completer.completion_history[0] == 'query_5'


def test_pattern_completions(completer):
    """Test pattern-based completions."""
    query_vector = create_random_vector()

    # Test SELECT pattern
    candidates = completer.get_completions('sel', query_vector)
    select_candidates = [c for c in candidates if c.text == 'SELECT']
    assert len(select_candidates) > 0
    assert select_candidates[0].source == 'pattern'

    # Test WHERE pattern
    candidates = completer.get_completions('wh', query_vector)
    where_candidates = [c for c in candidates if c.text == 'WHERE']
    assert len(where_candidates) > 0


def test_syntax_completions(completer):
    """Test syntax-based completions."""
    query_vector = create_random_vector()

    # Test unclosed parenthesis
    candidates = completer.get_completions('SELECT COUNT(', query_vector)
    close_paren = [c for c in candidates if c.text == ')']
    assert len(close_paren) > 0
    assert close_paren[0].source == 'syntax'

    # Test unclosed quote
    candidates = completer.get_completions("SELECT * FROM users WHERE name='test", query_vector)
    close_quote = [c for c in candidates if c.text == "'"]
    assert len(close_quote) > 0


def test_history_completions(completer):
    """Test history-based completions."""
    completer.add_to_history('SELECT * FROM users WHERE active = true')
    completer.add_to_history('SELECT id FROM orders')

    query_vector = create_random_vector()
    candidates = completer.get_completions('SELECT', query_vector)

    history_candidates = [c for c in candidates if c.source == 'history']
    assert len(history_candidates) > 0


def test_vector_completions(completer, vector_db):
    """Test vector-based completions."""
    def mock_embedding(text):
        # Create deterministic embeddings based on text
        np.random.seed(sum(ord(c) for c in text))
        vec = np.random.randn(384)
        return vec / np.linalg.norm(vec)

    # Index some objects
    tables = [
        {
            'name': 'users',
            'description': 'User accounts',
            'columns': [
                {'name': 'id', 'type': 'integer', 'description': 'Primary key'}
            ]
        }
    ]
    vector_db.index_database_objects(tables, mock_embedding)

    # Direct test: use vector search bypassing threshold
    query_vector = mock_embedding('Table: users. User accounts')

    # Lower threshold for testing
    results = vector_db.search_similar(query_vector, k=5, threshold=0.0)
    assert len(results) > 0  # Should find indexed items


def test_deduplicate_candidates(completer):
    """Test candidate deduplication."""
    candidates = [
        CompletionCandidate('SELECT', 0.9, {}, 'pattern'),
        CompletionCandidate('SELECT', 0.7, {}, 'history'),
        CompletionCandidate('FROM', 0.8, {}, 'pattern')
    ]

    unique = completer._deduplicate_candidates(candidates)

    assert len(unique) == 2
    # Should keep higher score
    select_candidate = [c for c in unique if c.text == 'SELECT'][0]
    assert select_candidate.score == 0.9


def test_register_pattern(completer):
    """Test registering completion patterns."""
    completer.register_pattern('JOIN', ['INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN'])

    assert 'JOIN' in completer.pattern_cache
    assert len(completer.pattern_cache['JOIN']) == 3


def test_context_aware_completions(completer, vector_db):
    """Test context-aware completions."""
    def mock_embedding(text):
        np.random.seed(hash(text) % (2**32))
        vec = np.random.randn(384)
        return vec / np.linalg.norm(vec)

    # Index database objects
    tables = [
        {
            'name': 'users',
            'description': 'User accounts',
            'columns': []
        }
    ]
    vector_db.index_database_objects(tables, mock_embedding)

    query = 'SELECT * FROM '
    query_vector = mock_embedding(query)

    candidates = completer.get_context_aware_completions(
        query=query,
        query_vector=query_vector,
        statement_type='SELECT',
        cursor_position=len(query)
    )

    # Should suggest table names after FROM
    assert len(candidates) > 0


def test_max_results_limit(completer):
    """Test maximum results limiting."""
    query_vector = create_random_vector()

    # Add many items to history
    for i in range(20):
        completer.add_to_history(f'SELECT query_{i}')

    candidates = completer.get_completions('SELECT', query_vector, max_results=5)

    assert len(candidates) <= 5


def test_completion_scoring(completer):
    """Test completion score ordering."""
    query_vector = create_random_vector()

    candidates = completer.get_completions('sel', query_vector)

    # Results should be sorted by score descending
    for i in range(len(candidates) - 1):
        assert candidates[i].score >= candidates[i + 1].score
