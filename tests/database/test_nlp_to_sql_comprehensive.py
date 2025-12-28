"""
Comprehensive tests for src/database/nlp_to_sql.py to achieve 85%+ coverage.

Tests NLP query conversion, pattern matching, parameter extraction,
suggestions, and all SQL template patterns.
"""

import pytest
from src.database.nlp_to_sql import NLPToSQL


class TestNLPToSQLInit:
    """Test NLPToSQL initialization"""

    def test_init(self):
        """Test initialization"""
        converter = NLPToSQL()

        assert converter is not None
        assert len(converter.compiled_patterns) > 0

    def test_patterns_compiled(self):
        """Test all patterns are compiled"""
        converter = NLPToSQL()

        for pattern in converter.compiled_patterns:
            assert 'regex' in pattern
            assert 'template' in pattern
            assert 'params' in pattern


class TestNLPToSQLSelectPatterns:
    """Test SELECT query patterns"""

    def test_show_me_pattern(self):
        """Test 'show me' pattern"""
        converter = NLPToSQL()
        result = converter.convert("show me users")

        assert result['sql'] == "SELECT * FROM users;"
        assert result['confidence'] == 'high'

    def test_show_all_pattern(self):
        """Test 'show all' pattern"""
        converter = NLPToSQL()
        result = converter.convert("show all products")

        assert result['sql'] == "SELECT * FROM products;"

    def test_get_all_from_pattern(self):
        """Test 'get all from' pattern"""
        converter = NLPToSQL()
        result = converter.convert("get all name from customers")

        assert "SELECT" in result['sql']
        assert "FROM customers" in result['sql']

    def test_list_pattern(self):
        """Test 'list' pattern"""
        converter = NLPToSQL()
        result = converter.convert("list orders")

        assert result['sql'] == "SELECT * FROM orders;"

    def test_find_where_pattern(self):
        """Test 'find where' pattern"""
        converter = NLPToSQL()
        result = converter.convert("find users where status is active")

        assert "SELECT * FROM users" in result['sql']
        assert "WHERE status = active" in result['sql']

    def test_find_where_equals_pattern(self):
        """Test 'find where equals' pattern"""
        converter = NLPToSQL()
        result = converter.convert("find products where price equals 100")

        assert "WHERE price = 100" in result['sql']


class TestNLPToSQLCountPatterns:
    """Test COUNT query patterns"""

    def test_count_all_pattern(self):
        """Test 'count all' pattern"""
        converter = NLPToSQL()
        result = converter.convert("count all users")

        assert result['sql'] == "SELECT COUNT(*) FROM users;"

    def test_count_pattern(self):
        """Test 'count' pattern"""
        converter = NLPToSQL()
        result = converter.convert("count orders")

        assert result['sql'] == "SELECT COUNT(*) FROM orders;"

    def test_how_many_pattern(self):
        """Test 'how many' pattern"""
        converter = NLPToSQL()
        result = converter.convert("how many products")

        assert result['sql'] == "SELECT COUNT(*) FROM products;"


class TestNLPToSQLInsertPatterns:
    """Test INSERT query patterns"""

    def test_add_pattern(self):
        """Test 'add' pattern"""
        converter = NLPToSQL()
        result = converter.convert("add user with name=John")

        assert "INSERT INTO user" in result['sql']

    def test_insert_pattern(self):
        """Test 'insert' pattern"""
        converter = NLPToSQL()
        result = converter.convert("insert product with name=Widget")

        assert "INSERT INTO product" in result['sql']

    def test_create_pattern(self):
        """Test 'create' pattern"""
        converter = NLPToSQL()
        result = converter.convert("create order where customer_id=123")

        assert "INSERT INTO order" in result['sql']


class TestNLPToSQLUpdatePatterns:
    """Test UPDATE query patterns"""

    def test_update_set_where_pattern(self):
        """Test 'update set where' pattern"""
        converter = NLPToSQL()
        result = converter.convert("update users set status to active where id is 1")

        assert "UPDATE users" in result['sql']
        assert "SET status = active" in result['sql']
        assert "WHERE id = 1" in result['sql']

    def test_update_set_equals_pattern(self):
        """Test 'update set' with equals"""
        converter = NLPToSQL()
        result = converter.convert("update products set price = 99.99 where sku = ABC123")

        assert "UPDATE products" in result['sql']


class TestNLPToSQLDeletePatterns:
    """Test DELETE query patterns"""

    def test_delete_from_where_pattern(self):
        """Test 'delete from where' pattern"""
        converter = NLPToSQL()
        result = converter.convert("delete from logs where date is 2024-01-01")

        assert "DELETE FROM logs" in result['sql']
        assert "WHERE date = 2024-01-01" in result['sql']

    def test_delete_where_pattern(self):
        """Test 'delete where' pattern"""
        converter = NLPToSQL()
        result = converter.convert("delete users where status is inactive")

        assert "DELETE FROM users" in result['sql']

    def test_remove_pattern(self):
        """Test 'remove' pattern"""
        converter = NLPToSQL()
        result = converter.convert("remove from orders where id = 456")

        assert "DELETE FROM orders" in result['sql']


class TestNLPToSQLParameters:
    """Test parameter extraction"""

    def test_parameters_extracted(self):
        """Test parameters are extracted correctly"""
        converter = NLPToSQL()
        result = converter.convert("find users where status is active")

        assert 'parameters' in result
        assert result['parameters']['table'] == 'users'
        assert result['parameters']['column'] == 'status'
        assert result['parameters']['value'] == 'active'

    def test_parameters_with_quotes_stripped(self):
        """Test quotes are stripped from parameters"""
        converter = NLPToSQL()
        result = converter.convert("find users where name is 'John'")

        # Quotes should be stripped (lowercase due to conversion)
        assert result['parameters']['value'].lower() == 'john'

    def test_matched_pattern_included(self):
        """Test matched pattern is included in result"""
        converter = NLPToSQL()
        result = converter.convert("show me users")

        assert 'matched_pattern' in result


class TestNLPToSQLConfidence:
    """Test confidence levels"""

    def test_high_confidence_on_match(self):
        """Test high confidence when pattern matches"""
        converter = NLPToSQL()
        result = converter.convert("show me users")

        assert result['confidence'] == 'high'

    def test_no_confidence_on_no_match(self):
        """Test no confidence when no pattern matches"""
        converter = NLPToSQL()
        result = converter.convert("this is not a valid query")

        assert result['confidence'] == 'none'


class TestNLPToSQLNoMatch:
    """Test queries that don't match patterns"""

    def test_no_match_returns_none_sql(self):
        """Test no match returns None for SQL"""
        converter = NLPToSQL()
        result = converter.convert("invalid query text")

        assert result['sql'] is None

    def test_no_match_returns_error(self):
        """Test no match returns error message"""
        converter = NLPToSQL()
        result = converter.convert("invalid query")

        assert 'error' in result
        assert "Could not convert" in result['error']

    def test_no_match_returns_suggestions(self):
        """Test no match returns suggestions"""
        converter = NLPToSQL()
        result = converter.convert("invalid query")

        assert 'suggestions' in result
        assert len(result['suggestions']) > 0

    def test_no_match_includes_original_query(self):
        """Test original query is included in result"""
        converter = NLPToSQL()
        original = "my original query"
        result = converter.convert(original)

        assert result['original_query'] == original.lower()


class TestNLPToSQLSuggestions:
    """Test suggestion generation"""

    def test_get_suggestions_includes_examples(self):
        """Test suggestions include examples"""
        converter = NLPToSQL()
        suggestions = converter._get_suggestions("some query")

        assert any("show me" in s for s in suggestions)
        assert any("count" in s for s in suggestions)

    def test_get_suggestions_detects_table_names(self):
        """Test suggestions detect potential table names"""
        converter = NLPToSQL()
        suggestions = converter._get_suggestions("do something with users table")

        # Should detect "users" as potential table
        suggestion_text = ' '.join(suggestions)
        assert 'users' in suggestion_text

    def test_get_suggestions_ignores_short_words(self):
        """Test suggestions ignore very short words"""
        converter = NLPToSQL()
        suggestions = converter._get_suggestions("a to is the")

        # Should not include short words
        suggestion_text = ' '.join(suggestions)
        assert 'potential table names' not in suggestion_text.lower()


class TestNLPToSQLIsSupported:
    """Test is_supported method"""

    def test_is_supported_returns_true_for_valid(self):
        """Test is_supported returns True for valid query"""
        converter = NLPToSQL()

        assert converter.is_supported("show me users")

    def test_is_supported_returns_false_for_invalid(self):
        """Test is_supported returns False for invalid query"""
        converter = NLPToSQL()

        assert not converter.is_supported("invalid query text")


class TestNLPToSQLCaseInsensitive:
    """Test case insensitive matching"""

    def test_uppercase_query(self):
        """Test uppercase query is handled"""
        converter = NLPToSQL()
        result = converter.convert("SHOW ME USERS")

        assert result['sql'] is not None

    def test_mixed_case_query(self):
        """Test mixed case query is handled"""
        converter = NLPToSQL()
        result = converter.convert("ShOw Me UsErS")

        assert result['sql'] is not None

    def test_lowercase_query(self):
        """Test lowercase query is handled"""
        converter = NLPToSQL()
        result = converter.convert("show me users")

        assert result['sql'] is not None


class TestNLPToSQLWhitespace:
    """Test whitespace handling"""

    def test_leading_whitespace(self):
        """Test query with leading whitespace"""
        converter = NLPToSQL()
        result = converter.convert("   show me users")

        assert result['sql'] is not None

    def test_trailing_whitespace(self):
        """Test query with trailing whitespace"""
        converter = NLPToSQL()
        result = converter.convert("show me users   ")

        assert result['sql'] is not None

    def test_extra_internal_whitespace(self):
        """Test query with extra internal whitespace"""
        converter = NLPToSQL()
        result = converter.convert("show    me    users")

        # May or may not match depending on pattern, but shouldn't crash
        assert 'sql' in result


class TestNLPToSQLComplexQueries:
    """Test complex query patterns"""

    def test_query_with_numeric_value(self):
        """Test query with numeric values"""
        converter = NLPToSQL()
        result = converter.convert("find products where price is 99.99")

        assert "99.99" in result['sql']

    def test_query_with_date_value(self):
        """Test query with date values"""
        converter = NLPToSQL()
        result = converter.convert("delete from logs where date is 2024-01-01")

        assert "2024-01-01" in result['sql']

    def test_query_with_special_characters(self):
        """Test query with special characters in values"""
        converter = NLPToSQL()
        result = converter.convert("find users where email is john@example.com")

        assert "john@example.com" in result['sql']


class TestNLPToSQLPatternCoverage:
    """Test coverage of all pattern types"""

    def test_all_select_patterns(self):
        """Test all SELECT pattern variants"""
        converter = NLPToSQL()

        queries = [
            "show me users",
            "show all users",
            "list users",
            "get all name from users",
            "find users where status is active"
        ]

        for query in queries:
            result = converter.convert(query)
            assert "SELECT" in result['sql']

    def test_all_count_patterns(self):
        """Test all COUNT pattern variants"""
        converter = NLPToSQL()

        queries = [
            "count users",
            "count all users",
            "how many users"
        ]

        for query in queries:
            result = converter.convert(query)
            assert "COUNT" in result['sql']

    def test_all_insert_patterns(self):
        """Test all INSERT pattern variants"""
        converter = NLPToSQL()

        queries = [
            "add user with data",
            "insert user with data",
            "create user with data"
        ]

        for query in queries:
            result = converter.convert(query)
            assert "INSERT" in result['sql']

    def test_all_delete_patterns(self):
        """Test all DELETE pattern variants"""
        converter = NLPToSQL()

        queries = [
            "delete from users where id is 1",
            "delete users where id is 1",
            "remove from users where id is 1"
        ]

        for query in queries:
            result = converter.convert(query)
            assert "DELETE" in result['sql']


class TestNLPToSQLEdgeCases:
    """Test edge cases"""

    def test_empty_query(self):
        """Test empty query"""
        converter = NLPToSQL()
        result = converter.convert("")

        assert result['sql'] is None

    def test_only_whitespace_query(self):
        """Test query with only whitespace"""
        converter = NLPToSQL()
        result = converter.convert("   ")

        assert result['sql'] is None

    def test_single_word_query(self):
        """Test single word query"""
        converter = NLPToSQL()
        result = converter.convert("users")

        # May or may not match, but shouldn't crash
        assert 'sql' in result

    def test_very_long_query(self):
        """Test very long query"""
        converter = NLPToSQL()
        long_query = "show me users " + "extra " * 100

        result = converter.convert(long_query)

        # Should handle without crashing
        assert 'sql' in result
