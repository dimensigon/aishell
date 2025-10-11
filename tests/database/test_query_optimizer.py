"""
Comprehensive Unit Tests for Query Optimizer

Tests query analysis, optimization suggestions, and performance improvements.
"""

import pytest
from typing import List

from src.database.query_optimizer import (
    QueryOptimizer,
    OptimizationSuggestion,
    OptimizationType,
    OptimizationLevel
)


# Test Fixtures

@pytest.fixture
def optimizer():
    """Create query optimizer instance"""
    return QueryOptimizer(database_type='postgresql')


@pytest.fixture
def mysql_optimizer():
    """Create MySQL query optimizer"""
    return QueryOptimizer(database_type='mysql')


# Test Basic Functionality

class TestQueryOptimizerBasics:
    """Test basic query optimizer functionality"""

    def test_optimizer_initialization(self):
        """Test optimizer initialization"""
        optimizer = QueryOptimizer(database_type='postgresql')
        assert optimizer.database_type == 'postgresql'

    def test_optimizer_database_types(self):
        """Test different database types"""
        pg_optimizer = QueryOptimizer(database_type='postgresql')
        mysql_optimizer = QueryOptimizer(database_type='mysql')
        oracle_optimizer = QueryOptimizer(database_type='oracle')

        assert pg_optimizer.database_type == 'postgresql'
        assert mysql_optimizer.database_type == 'mysql'
        assert oracle_optimizer.database_type == 'oracle'


# Test SELECT * Detection

class TestSelectStarDetection:
    """Test SELECT * optimization detection"""

    def test_detect_select_star(self, optimizer):
        """Test SELECT * detection"""
        query = "SELECT * FROM users"
        suggestions = optimizer.analyze_query(query)

        select_star_suggestions = [s for s in suggestions if s.type == OptimizationType.SELECT_STAR]
        assert len(select_star_suggestions) > 0
        assert select_star_suggestions[0].level == OptimizationLevel.WARNING

    def test_no_select_star_with_columns(self, optimizer):
        """Test no warning when columns are specified"""
        query = "SELECT id, name FROM users"
        suggestions = optimizer.analyze_query(query)

        select_star_suggestions = [s for s in suggestions if s.type == OptimizationType.SELECT_STAR]
        assert len(select_star_suggestions) == 0


# Test Missing WHERE Clause

class TestMissingWhereDetection:
    """Test missing WHERE clause detection"""

    def test_detect_missing_where_select(self, optimizer):
        """Test missing WHERE in SELECT"""
        query = "SELECT * FROM users"
        suggestions = optimizer.analyze_query(query)

        where_suggestions = [s for s in suggestions if s.type == OptimizationType.MISSING_WHERE]
        assert len(where_suggestions) > 0
        assert where_suggestions[0].level == OptimizationLevel.WARNING

    def test_detect_missing_where_delete(self, optimizer):
        """Test missing WHERE in DELETE (critical)"""
        query = "DELETE FROM users"
        suggestions = optimizer.analyze_query(query)

        where_suggestions = [s for s in suggestions if s.type == OptimizationType.MISSING_WHERE]
        assert len(where_suggestions) > 0
        assert where_suggestions[0].level == OptimizationLevel.CRITICAL

    def test_detect_missing_where_update(self, optimizer):
        """Test missing WHERE in UPDATE (critical)"""
        query = "UPDATE users SET active = true"
        suggestions = optimizer.analyze_query(query)

        where_suggestions = [s for s in suggestions if s.type == OptimizationType.MISSING_WHERE]
        assert len(where_suggestions) > 0
        assert where_suggestions[0].level == OptimizationLevel.CRITICAL

    def test_no_warning_with_where(self, optimizer):
        """Test no warning when WHERE clause exists"""
        query = "SELECT * FROM users WHERE id = 1"
        suggestions = optimizer.analyze_query(query)

        where_suggestions = [s for s in suggestions if s.type == OptimizationType.MISSING_WHERE]
        assert len(where_suggestions) == 0


# Test Index Suggestions

class TestIndexSuggestions:
    """Test index suggestion generation"""

    def test_suggest_index_for_where(self, optimizer):
        """Test index suggestion for WHERE clause"""
        query = "SELECT * FROM users WHERE email = 'test@example.com'"
        suggestions = optimizer.analyze_query(query)

        index_suggestions = [s for s in suggestions if s.type == OptimizationType.MISSING_INDEX]
        assert len(index_suggestions) > 0
        assert 'email' in index_suggestions[0].message.lower()

    def test_suggest_index_for_join(self, optimizer):
        """Test index suggestion for JOIN"""
        query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        suggestions = optimizer.analyze_query(query)

        index_suggestions = [s for s in suggestions if s.type == OptimizationType.MISSING_INDEX]
        assert len(index_suggestions) > 0

    def test_index_suggestion_includes_sql(self, optimizer):
        """Test index suggestion includes CREATE INDEX SQL"""
        query = "SELECT * FROM users WHERE email = 'test@example.com'"
        suggestions = optimizer.analyze_query(query)

        index_suggestions = [s for s in suggestions if s.type == OptimizationType.MISSING_INDEX]
        assert len(index_suggestions) > 0
        assert index_suggestions[0].suggested_query is not None
        assert 'CREATE INDEX' in index_suggestions[0].suggested_query


# Test Full Table Scan Detection

class TestFullTableScanDetection:
    """Test full table scan detection"""

    def test_detect_leading_wildcard_like(self, optimizer):
        """Test detection of LIKE with leading wildcard"""
        query = "SELECT * FROM users WHERE email LIKE '%@gmail.com'"
        suggestions = optimizer.analyze_query(query)

        scan_suggestions = [s for s in suggestions if s.type == OptimizationType.FULL_TABLE_SCAN]
        assert len(scan_suggestions) > 0
        assert 'wildcard' in scan_suggestions[0].message.lower()

    def test_detect_function_on_column(self, optimizer):
        """Test detection of function on indexed column"""
        query = "SELECT * FROM users WHERE UPPER(name) = 'JOHN'"
        suggestions = optimizer.analyze_query(query)

        scan_suggestions = [s for s in suggestions if s.type == OptimizationType.FULL_TABLE_SCAN]
        assert len(scan_suggestions) > 0
        assert 'function' in scan_suggestions[0].message.lower()


# Test Join Optimization

class TestJoinOptimization:
    """Test JOIN optimization suggestions"""

    def test_detect_many_joins(self, optimizer):
        """Test detection of excessive JOINs"""
        query = """
            SELECT * FROM t1
            JOIN t2 ON t1.id = t2.t1_id
            JOIN t3 ON t2.id = t3.t2_id
            JOIN t4 ON t3.id = t4.t3_id
            JOIN t5 ON t4.id = t5.t4_id
            JOIN t6 ON t5.id = t6.t5_id
            JOIN t7 ON t6.id = t7.t6_id
        """
        suggestions = optimizer.analyze_query(query)

        join_suggestions = [s for s in suggestions if s.type == OptimizationType.INEFFICIENT_JOIN]
        assert len(join_suggestions) > 0

    def test_detect_outer_join(self, optimizer):
        """Test detection of OUTER JOIN"""
        query = "SELECT * FROM users LEFT OUTER JOIN orders ON users.id = orders.user_id"
        suggestions = optimizer.analyze_query(query)

        join_suggestions = [s for s in suggestions if s.type == OptimizationType.INEFFICIENT_JOIN]
        assert len(join_suggestions) > 0
        assert 'OUTER JOIN' in join_suggestions[0].message


# Test Subquery Optimization

class TestSubqueryOptimization:
    """Test subquery optimization suggestions"""

    def test_detect_in_subquery(self, optimizer):
        """Test detection of IN subquery"""
        query = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        suggestions = optimizer.analyze_query(query)

        subquery_suggestions = [s for s in suggestions if s.type == OptimizationType.SUBQUERY_OPTIMIZATION]
        assert len(subquery_suggestions) > 0
        assert 'EXISTS' in subquery_suggestions[0].message or 'JOIN' in subquery_suggestions[0].message

    def test_detect_subquery(self, optimizer):
        """Test detection of subqueries"""
        query = "SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE id = 1)"
        suggestions = optimizer.analyze_query(query)

        subquery_suggestions = [s for s in suggestions if s.type == OptimizationType.SUBQUERY_OPTIMIZATION]
        assert len(subquery_suggestions) > 0


# Test Missing LIMIT

class TestMissingLimitDetection:
    """Test missing LIMIT detection"""

    def test_detect_missing_limit(self, optimizer):
        """Test detection of SELECT without LIMIT"""
        query = "SELECT * FROM users"
        suggestions = optimizer.analyze_query(query)

        limit_suggestions = [s for s in suggestions if s.type == OptimizationType.MISSING_LIMIT]
        assert len(limit_suggestions) > 0

    def test_no_warning_with_limit(self, optimizer):
        """Test no warning when LIMIT is present"""
        query = "SELECT * FROM users LIMIT 100"
        suggestions = optimizer.analyze_query(query)

        limit_suggestions = [s for s in suggestions if s.type == OptimizationType.MISSING_LIMIT]
        assert len(limit_suggestions) == 0


# Test Cartesian Product Detection

class TestCartesianProductDetection:
    """Test Cartesian product detection"""

    def test_detect_cartesian_product(self, optimizer):
        """Test detection of Cartesian product"""
        query = "SELECT * FROM users, orders, products WHERE users.id = 1"
        suggestions = optimizer.analyze_query(query)

        cartesian_suggestions = [s for s in suggestions if s.type == OptimizationType.CARTESIAN_PRODUCT]
        assert len(cartesian_suggestions) > 0
        assert cartesian_suggestions[0].level == OptimizationLevel.CRITICAL

    def test_no_warning_with_explicit_joins(self, optimizer):
        """Test no warning with explicit JOINs"""
        query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        suggestions = optimizer.analyze_query(query)

        cartesian_suggestions = [s for s in suggestions if s.type == OptimizationType.CARTESIAN_PRODUCT]
        assert len(cartesian_suggestions) == 0


# Test EXPLAIN Plan Analysis

class TestExplainPlanAnalysis:
    """Test EXPLAIN plan analysis"""

    def test_analyze_seq_scan(self, optimizer):
        """Test detection of sequential scan in EXPLAIN"""
        explain_output = """
        Seq Scan on users  (cost=0.00..155.00 rows=10000 width=50)
        """
        suggestions = optimizer.analyze_explain_plan(explain_output)

        scan_suggestions = [s for s in suggestions if s.type == OptimizationType.FULL_TABLE_SCAN]
        assert len(scan_suggestions) > 0

    def test_analyze_high_cost(self, optimizer):
        """Test detection of high cost in EXPLAIN"""
        explain_output = """
        Hash Join  (cost=5000.00..25000.00 rows=10000 width=50)
        """
        suggestions = optimizer.analyze_explain_plan(explain_output)

        cost_suggestions = [s for s in suggestions if s.type == OptimizationType.QUERY_REWRITE]
        assert len(cost_suggestions) > 0


# Test Optimization Report

class TestOptimizationReport:
    """Test comprehensive optimization report"""

    def test_generate_report(self, optimizer):
        """Test optimization report generation"""
        query = "SELECT * FROM users"
        report = optimizer.get_optimization_report(query)

        assert 'query' in report
        assert 'total_suggestions' in report
        assert 'critical_issues' in report
        assert 'warnings' in report
        assert 'info' in report
        assert 'suggestions' in report
        assert 'optimization_score' in report

        assert report['query'] == query
        assert report['total_suggestions'] >= 0
        assert 0 <= report['optimization_score'] <= 100

    def test_report_with_explain(self, optimizer):
        """Test report with EXPLAIN output"""
        query = "SELECT * FROM users"
        explain_output = "Seq Scan on users  (cost=0.00..155.00 rows=10000 width=50)"

        report = optimizer.get_optimization_report(query, explain_output)

        assert report['total_suggestions'] > 0

    def test_report_categorization(self, optimizer):
        """Test report suggestion categorization"""
        query = "DELETE FROM users"  # Critical: missing WHERE
        report = optimizer.get_optimization_report(query)

        assert report['critical_issues'] > 0
        assert 'critical' in report['suggestions']
        assert isinstance(report['suggestions']['critical'], list)

    def test_optimization_score_calculation(self, optimizer):
        """Test optimization score calculation"""
        good_query = "SELECT id, name FROM users WHERE id = 1 LIMIT 10"
        bad_query = "SELECT * FROM users, orders, products"

        good_report = optimizer.get_optimization_report(good_query)
        bad_report = optimizer.get_optimization_report(bad_query)

        assert good_report['optimization_score'] > bad_report['optimization_score']


# Test Database-Specific Features

class TestDatabaseSpecificFeatures:
    """Test database-specific optimization features"""

    def test_mysql_index_suggestion(self, mysql_optimizer):
        """Test MySQL-specific index suggestion"""
        query = "SELECT * FROM users WHERE email = 'test@example.com'"
        suggestions = mysql_optimizer.analyze_query(query)

        index_suggestions = [s for s in suggestions if s.type == OptimizationType.MISSING_INDEX]
        assert len(index_suggestions) > 0
        assert 'CREATE INDEX' in index_suggestions[0].suggested_query

    def test_postgresql_index_suggestion(self, optimizer):
        """Test PostgreSQL-specific index suggestion"""
        query = "SELECT * FROM users WHERE email = 'test@example.com'"
        suggestions = optimizer.analyze_query(query)

        index_suggestions = [s for s in suggestions if s.type == OptimizationType.MISSING_INDEX]
        assert len(index_suggestions) > 0
        assert 'CREATE INDEX' in index_suggestions[0].suggested_query


# Test Complex Queries

class TestComplexQueryAnalysis:
    """Test analysis of complex queries"""

    def test_analyze_complex_query(self, optimizer):
        """Test analysis of complex multi-issue query"""
        query = """
            SELECT *
            FROM users, orders, products
            WHERE users.id IN (SELECT user_id FROM orders)
            AND products.name LIKE '%test%'
        """
        suggestions = optimizer.analyze_query(query)

        # Should detect multiple issues
        assert len(suggestions) > 3

        # Should have different types of suggestions
        suggestion_types = {s.type for s in suggestions}
        assert len(suggestion_types) > 1

    def test_analyze_query_with_multiple_tables(self, optimizer):
        """Test query with multiple tables"""
        query = """
            SELECT users.name, orders.total, products.name
            FROM users
            LEFT OUTER JOIN orders ON users.id = orders.user_id
            LEFT OUTER JOIN products ON orders.product_id = products.id
        """
        suggestions = optimizer.analyze_query(query)

        # Should detect OUTER JOIN suggestion
        join_suggestions = [s for s in suggestions if s.type == OptimizationType.INEFFICIENT_JOIN]
        assert len(join_suggestions) > 0


# Test Suggestion Details

class TestSuggestionDetails:
    """Test optimization suggestion details"""

    def test_suggestion_has_all_fields(self, optimizer):
        """Test suggestion contains all required fields"""
        query = "SELECT * FROM users"
        suggestions = optimizer.analyze_query(query)

        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert hasattr(suggestion, 'type')
            assert hasattr(suggestion, 'level')
            assert hasattr(suggestion, 'message')
            assert hasattr(suggestion, 'original_query')
            assert hasattr(suggestion, 'estimated_improvement')
            assert hasattr(suggestion, 'explanation')

    def test_suggestion_explanation_exists(self, optimizer):
        """Test suggestions include explanations"""
        query = "SELECT * FROM users"
        suggestions = optimizer.analyze_query(query)

        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert suggestion.explanation is not None
            assert len(suggestion.explanation) > 0


# Test Edge Cases

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_query(self, optimizer):
        """Test empty query"""
        suggestions = optimizer.analyze_query("")
        assert isinstance(suggestions, list)

    def test_whitespace_query(self, optimizer):
        """Test query with only whitespace"""
        suggestions = optimizer.analyze_query("   \n\t   ")
        assert isinstance(suggestions, list)

    def test_comment_only_query(self, optimizer):
        """Test query with only comments"""
        query = "-- This is a comment"
        suggestions = optimizer.analyze_query(query)
        assert isinstance(suggestions, list)

    def test_case_insensitivity(self, optimizer):
        """Test case insensitive analysis"""
        query_upper = "SELECT * FROM USERS WHERE EMAIL = 'TEST@EXAMPLE.COM'"
        query_lower = "select * from users where email = 'test@example.com'"

        suggestions_upper = optimizer.analyze_query(query_upper)
        suggestions_lower = optimizer.analyze_query(query_lower)

        # Should detect same number of issues
        assert len(suggestions_upper) == len(suggestions_lower)


# Test Performance

class TestOptimizerPerformance:
    """Test optimizer performance"""

    def test_analyze_multiple_queries(self, optimizer):
        """Test analyzing multiple queries"""
        queries = [
            "SELECT * FROM users",
            "SELECT id, name FROM orders WHERE status = 'pending'",
            "UPDATE products SET price = 100 WHERE id = 1",
            "DELETE FROM logs WHERE created_at < '2024-01-01'"
        ]

        for query in queries:
            suggestions = optimizer.analyze_query(query)
            assert isinstance(suggestions, list)

    def test_report_generation_speed(self, optimizer):
        """Test report generation performance"""
        query = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"

        # Should complete quickly
        import time
        start = time.time()
        report = optimizer.get_optimization_report(query)
        duration = time.time() - start

        assert duration < 1.0  # Should complete in under 1 second
        assert report is not None
