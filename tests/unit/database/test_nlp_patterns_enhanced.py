"""
Comprehensive Tests for Enhanced NLP Patterns

Tests all 23+ NLP patterns including new JOIN, GROUP BY, ORDER BY,
LIMIT, DISTINCT, BETWEEN, LIKE, and IN patterns.
"""

import pytest
from src.database.nlp_to_sql import NLPToSQL


@pytest.fixture
def nlp_converter():
    """Create NLP to SQL converter"""
    return NLPToSQL()


# Test Basic SELECT Patterns (Existing)

class TestBasicSelectPatterns:
    """Test basic SELECT patterns"""

    def test_show_table(self, nlp_converter):
        """Test 'show' pattern"""
        result = nlp_converter.convert("show users")
        assert result['sql'] == "SELECT * FROM users;"
        assert result['confidence'] == 'high'

    def test_list_table(self, nlp_converter):
        """Test 'list' pattern"""
        result = nlp_converter.convert("list products")
        assert result['sql'] == "SELECT * FROM products;"

    def test_get_columns_from_table(self, nlp_converter):
        """Test 'get columns from table' pattern"""
        result = nlp_converter.convert("get name from users")
        assert 'SELECT' in result['sql']
        assert 'users' in result['sql'].lower()


# Test JOIN Patterns (New)

class TestJoinPatterns:
    """Test JOIN pattern support"""

    def test_get_with_their(self, nlp_converter):
        """Test 'get X with their Y' pattern"""
        result = nlp_converter.convert("get users with their orders")
        assert result['sql'] is not None
        assert 'JOIN' in result['sql']
        assert 'users' in result['sql'].lower()
        assert 'orders' in result['sql'].lower()

    def test_show_and_their(self, nlp_converter):
        """Test 'show X and their Y' pattern"""
        result = nlp_converter.convert("show customers and their purchases")
        assert result['sql'] is not None
        assert 'JOIN' in result['sql']

    def test_join_with(self, nlp_converter):
        """Test 'join X with Y' pattern"""
        result = nlp_converter.convert("join employees with departments")
        assert result['sql'] is not None
        assert 'JOIN' in result['sql']


# Test GROUP BY Patterns (New)

class TestGroupByPatterns:
    """Test GROUP BY pattern support"""

    def test_total_by_column(self, nlp_converter):
        """Test 'show total X by Y' pattern"""
        result = nlp_converter.convert("show total sales by region")
        assert result['sql'] is not None
        assert 'GROUP BY' in result['sql']
        assert 'SUM' in result['sql']

    def test_get_total_by(self, nlp_converter):
        """Test 'get total X by Y' pattern"""
        result = nlp_converter.convert("get total revenue by category")
        assert result['sql'] is not None
        assert 'GROUP BY' in result['sql']

    def test_count_by(self, nlp_converter):
        """Test 'count X by Y' pattern"""
        result = nlp_converter.convert("count orders by customer")
        assert result['sql'] is not None
        assert 'GROUP BY' in result['sql']
        assert 'COUNT' in result['sql']

    def test_group_by(self, nlp_converter):
        """Test 'group X by Y' pattern"""
        result = nlp_converter.convert("group products by category")
        assert result['sql'] is not None
        assert 'GROUP BY' in result['sql']


# Test Aggregate Function Patterns (New)

class TestAggregateFunctionPatterns:
    """Test aggregate function patterns"""

    def test_average_pattern(self, nlp_converter):
        """Test 'average' pattern"""
        result = nlp_converter.convert("average price of products")
        assert result['sql'] is not None
        assert 'AVG' in result['sql']
        assert 'price' in result['sql'].lower()

    def test_max_pattern(self, nlp_converter):
        """Test 'max/maximum' pattern"""
        result = nlp_converter.convert("maximum salary from employees")
        assert result['sql'] is not None
        assert 'MAX' in result['sql']

    def test_min_pattern(self, nlp_converter):
        """Test 'min/minimum' pattern"""
        result = nlp_converter.convert("minimum age of users")
        assert result['sql'] is not None
        assert 'MIN' in result['sql']

    def test_sum_pattern(self, nlp_converter):
        """Test 'sum' pattern"""
        result = nlp_converter.convert("sum of revenue from sales")
        assert result['sql'] is not None
        assert 'SUM' in result['sql']


# Test ORDER BY Patterns (New)

class TestOrderByPatterns:
    """Test ORDER BY pattern support"""

    def test_sorted_by(self, nlp_converter):
        """Test 'sorted by' pattern"""
        result = nlp_converter.convert("list users sorted by name")
        assert result['sql'] is not None
        assert 'ORDER BY' in result['sql']
        assert 'name' in result['sql'].lower()

    def test_sort_by(self, nlp_converter):
        """Test 'sort by' pattern"""
        result = nlp_converter.convert("sort products by price")
        assert result['sql'] is not None
        assert 'ORDER BY' in result['sql']

    def test_descending_order(self, nlp_converter):
        """Test 'descending order' pattern"""
        result = nlp_converter.convert("show orders in descending order by date")
        assert result['sql'] is not None
        assert 'ORDER BY' in result['sql']
        assert 'DESC' in result['sql']


# Test LIMIT Patterns (New)

class TestLimitPatterns:
    """Test LIMIT pattern support"""

    def test_top_n(self, nlp_converter):
        """Test 'top N' pattern"""
        result = nlp_converter.convert("show top 10 products")
        assert result['sql'] is not None
        assert 'LIMIT' in result['sql']
        assert '10' in result['sql']

    def test_get_top_n(self, nlp_converter):
        """Test 'get top N' pattern"""
        result = nlp_converter.convert("get top 5 users")
        assert result['sql'] is not None
        assert 'LIMIT' in result['sql']
        assert '5' in result['sql']

    def test_first_n(self, nlp_converter):
        """Test 'first N' pattern"""
        result = nlp_converter.convert("show first 20 orders")
        assert result['sql'] is not None
        assert 'LIMIT' in result['sql']
        assert '20' in result['sql']


# Test DISTINCT Patterns (New)

class TestDistinctPatterns:
    """Test DISTINCT pattern support"""

    def test_unique_table(self, nlp_converter):
        """Test 'unique table' pattern"""
        result = nlp_converter.convert("get unique categories")
        assert result['sql'] is not None
        assert 'DISTINCT' in result['sql']

    def test_show_unique(self, nlp_converter):
        """Test 'show unique' pattern"""
        result = nlp_converter.convert("show unique cities")
        assert result['sql'] is not None
        assert 'DISTINCT' in result['sql']

    def test_distinct_column(self, nlp_converter):
        """Test 'distinct column from table' pattern"""
        result = nlp_converter.convert("get distinct status from orders")
        assert result['sql'] is not None
        assert 'DISTINCT' in result['sql']
        assert 'status' in result['sql'].lower()


# Test BETWEEN Patterns (New)

class TestBetweenPatterns:
    """Test BETWEEN pattern support"""

    def test_between_values(self, nlp_converter):
        """Test 'between X and Y' pattern"""
        result = nlp_converter.convert("get orders between 100 and 500")
        assert result['sql'] is not None
        assert 'BETWEEN' in result['sql']
        assert '100' in result['sql']
        assert '500' in result['sql']

    def test_find_between(self, nlp_converter):
        """Test 'find column from table between X and Y' pattern"""
        result = nlp_converter.convert("find price from products between 10.00 and 50.00")
        assert result['sql'] is not None
        assert 'BETWEEN' in result['sql']


# Test LIKE Patterns (New)

class TestLikePatterns:
    """Test LIKE pattern support"""

    def test_find_with_like(self, nlp_converter):
        """Test 'find with containing' pattern"""
        result = nlp_converter.convert("find users with email containing gmail")
        assert result['sql'] is not None
        assert 'LIKE' in result['sql']
        assert 'gmail' in result['sql'].lower()

    def test_search_for(self, nlp_converter):
        """Test 'search for' pattern"""
        result = nlp_converter.convert("search products for laptop")
        assert result['sql'] is not None
        assert 'LIKE' in result['sql']
        assert 'laptop' in result['sql'].lower()


# Test IN Patterns (New)

class TestInPatterns:
    """Test IN pattern support"""

    def test_in_categories(self, nlp_converter):
        """Test 'in categories' pattern"""
        result = nlp_converter.convert("get products in categories electronics")
        assert result['sql'] is not None
        assert 'IN' in result['sql']

    def test_where_in(self, nlp_converter):
        """Test 'where column in values' pattern"""
        result = nlp_converter.convert("find users where status in active")
        assert result['sql'] is not None
        assert 'IN' in result['sql']


# Test COUNT Patterns (Existing)

class TestCountPatterns:
    """Test COUNT patterns"""

    def test_count_table(self, nlp_converter):
        """Test 'count table' pattern"""
        result = nlp_converter.convert("count users")
        assert result['sql'] == "SELECT COUNT(*) FROM users;"

    def test_how_many(self, nlp_converter):
        """Test 'how many' pattern"""
        result = nlp_converter.convert("how many orders")
        assert result['sql'] == "SELECT COUNT(*) FROM orders;"


# Test WHERE Patterns (Existing)

class TestWherePatterns:
    """Test WHERE clause patterns"""

    def test_find_where(self, nlp_converter):
        """Test 'find where' pattern"""
        result = nlp_converter.convert("find users where status is active")
        assert result['sql'] is not None
        assert 'WHERE' in result['sql']
        assert 'status' in result['sql'].lower()


# Test INSERT Patterns (Existing)

class TestInsertPatterns:
    """Test INSERT patterns"""

    def test_add_with_values(self, nlp_converter):
        """Test 'add' pattern"""
        result = nlp_converter.convert("add user with name John")
        assert result['sql'] is not None
        assert 'INSERT INTO' in result['sql']


# Test UPDATE Patterns (Existing)

class TestUpdatePatterns:
    """Test UPDATE patterns"""

    def test_update_set_where(self, nlp_converter):
        """Test 'update set where' pattern"""
        result = nlp_converter.convert("update users set active to true where id is 1")
        assert result['sql'] is not None
        assert 'UPDATE' in result['sql']
        assert 'SET' in result['sql']
        assert 'WHERE' in result['sql']


# Test DELETE Patterns (Existing)

class TestDeletePatterns:
    """Test DELETE patterns"""

    def test_delete_where(self, nlp_converter):
        """Test 'delete where' pattern"""
        result = nlp_converter.convert("delete from logs where date is 2024-01-01")
        assert result['sql'] is not None
        assert 'DELETE FROM' in result['sql']
        assert 'WHERE' in result['sql']

    def test_remove_where(self, nlp_converter):
        """Test 'remove where' pattern"""
        result = nlp_converter.convert("remove from users where id is 100")
        assert result['sql'] is not None
        assert 'DELETE FROM' in result['sql']


# Test Pattern Count

class TestPatternCount:
    """Test total pattern count"""

    def test_total_patterns(self, nlp_converter):
        """Test that we have at least 23 patterns"""
        assert len(nlp_converter.PATTERNS) >= 23

    def test_pattern_categories(self, nlp_converter):
        """Test pattern categories are present"""
        pattern_str = str(nlp_converter.PATTERNS)

        # Check for new pattern types
        assert 'JOIN' in pattern_str
        assert 'GROUP BY' in pattern_str
        assert 'ORDER BY' in pattern_str
        assert 'LIMIT' in pattern_str
        assert 'DISTINCT' in pattern_str
        assert 'BETWEEN' in pattern_str
        assert 'LIKE' in pattern_str
        assert 'IN' in pattern_str


# Test Complex Queries

class TestComplexPatterns:
    """Test complex query patterns"""

    def test_multiple_patterns_supported(self, nlp_converter):
        """Test that multiple pattern types are supported"""
        queries = [
            "show users",
            "get users with their orders",
            "show total sales by region",
            "average price of products",
            "list users sorted by name",
            "show top 10 products",
            "get unique categories",
            "get orders between 100 and 500",
            "find users with email containing gmail",
            "get products in categories electronics"
        ]

        successful = 0
        for query in queries:
            result = nlp_converter.convert(query)
            if result['sql'] is not None:
                successful += 1

        # At least 8 out of 10 should succeed
        assert successful >= 8


# Test Case Insensitivity

class TestCaseInsensitivity:
    """Test case insensitive pattern matching"""

    def test_uppercase_query(self, nlp_converter):
        """Test uppercase query"""
        result = nlp_converter.convert("SHOW USERS")
        assert result['sql'] is not None

    def test_mixed_case_query(self, nlp_converter):
        """Test mixed case query"""
        result = nlp_converter.convert("Show Users")
        assert result['sql'] is not None


# Test Error Handling

class TestErrorHandling:
    """Test error handling for unsupported queries"""

    def test_unsupported_query(self, nlp_converter):
        """Test unsupported query returns proper error"""
        result = nlp_converter.convert("this is not a valid query pattern")
        assert result['sql'] is None
        assert result['confidence'] == 'none'
        assert 'error' in result

    def test_suggestions_provided(self, nlp_converter):
        """Test suggestions are provided for failed queries"""
        result = nlp_converter.convert("invalid query")
        assert 'suggestions' in result
        assert len(result['suggestions']) > 0


# Test is_supported Method

class TestIsSupportedMethod:
    """Test is_supported method"""

    def test_supported_query(self, nlp_converter):
        """Test is_supported returns True for supported queries"""
        assert nlp_converter.is_supported("show users") is True

    def test_unsupported_query(self, nlp_converter):
        """Test is_supported returns False for unsupported queries"""
        assert nlp_converter.is_supported("invalid query pattern") is False


# Test Pattern Coverage

class TestPatternCoverage:
    """Test comprehensive pattern coverage"""

    def test_all_sql_clauses_covered(self, nlp_converter):
        """Test all major SQL clauses are covered"""
        all_patterns = nlp_converter.PATTERNS

        # Convert to string for searching
        patterns_str = str(all_patterns)

        # Check for all major SQL clauses
        sql_clauses = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE',
            'JOIN', 'WHERE', 'GROUP BY', 'ORDER BY',
            'LIMIT', 'DISTINCT', 'BETWEEN', 'LIKE', 'IN',
            'COUNT', 'SUM', 'AVG', 'MAX', 'MIN'
        ]

        for clause in sql_clauses:
            assert clause in patterns_str, f"Missing pattern for {clause}"
