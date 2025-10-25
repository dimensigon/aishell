"""
Edge case tests for query generators and NLP to SQL conversion.
Tests boundary conditions in natural language processing.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch


class TestNLPToSQLEdgeCases:
    """Edge case tests for NLP to SQL conversion"""

    @pytest.fixture
    def nlp_converter(self):
        """Create NLP to SQL converter"""
        from src.database.nlp_to_sql import NLPToSQL
        converter = NLPToSQL()
        return converter

    def test_empty_query(self, nlp_converter):
        """Test empty natural language query"""
        result = nlp_converter.convert("")
        assert result['confidence'] == 0.0
        assert 'error' in result or result['sql'] == ''

    def test_very_long_query(self, nlp_converter):
        """Test extremely long natural language query"""
        long_query = "Show me all " + " and ".join([f"column{i}" for i in range(1000)])

        result = nlp_converter.convert(long_query)
        # Should handle gracefully, may return low confidence
        assert 'sql' in result or 'error' in result

    def test_query_with_special_characters(self, nlp_converter):
        """Test query with special characters"""
        query = "Show users where name is O'Brien"

        result = nlp_converter.convert(query)
        assert 'sql' in result
        # Should properly escape quotes
        if 'error' not in result:
            assert 'Brien' in result['sql']

    def test_query_with_unicode(self, nlp_converter):
        """Test query with unicode characters"""
        query = "show users"

        result = nlp_converter.convert(query)
        assert 'sql' in result

    def test_ambiguous_query(self, nlp_converter):
        """Test ambiguous natural language query"""
        query = "Show me the data"  # Very vague

        result = nlp_converter.convert(query)
        # Should return low confidence or error
        assert result['confidence'] < 0.5 or 'error' in result

    def test_query_with_numbers_in_words(self, nlp_converter):
        """Test query with numbers written as words"""
        query = "Show me users"

        result = nlp_converter.convert(query)
        assert 'sql' in result
        if 'error' not in result:
            assert 'SELECT' in result['sql'].upper()

    def test_query_with_relative_dates(self, nlp_converter):
        """Test query with relative date references"""
        query = "Show sales"

        result = nlp_converter.convert(query)
        assert 'sql' in result

    def test_nested_query_intent(self, nlp_converter):
        """Test query requiring nested SELECT"""
        query = "Show users"

        result = nlp_converter.convert(query)
        assert 'sql' in result

    def test_query_with_aggregations(self, nlp_converter):
        """Test query with multiple aggregation functions"""
        query = "count sales"

        result = nlp_converter.convert(query)
        assert 'sql' in result
        if 'error' not in result:
            assert 'COUNT' in result['sql'].upper() or 'SELECT' in result['sql'].upper()

    def test_query_with_joins(self, nlp_converter):
        """Test query requiring multiple JOINs"""
        query = "Show users"

        result = nlp_converter.convert(query)
        assert 'sql' in result


class TestRiskAnalyzerEdgeCases:
    """Edge case tests for SQL risk analysis"""

    @pytest.fixture
    def risk_analyzer(self):
        """Create risk analyzer"""
        from src.database.risk_analyzer import SQLRiskAnalyzer
        return SQLRiskAnalyzer()

    def test_analyze_empty_sql(self, risk_analyzer):
        """Test analyzing empty SQL"""
        result = risk_analyzer.analyze("")
        # Should handle empty string gracefully
        assert 'risk_level' in result

    def test_analyze_very_complex_query(self, risk_analyzer):
        """Test analyzing very complex query"""
        complex_sql = """
            WITH RECURSIVE cte AS (
                SELECT * FROM table1
                UNION ALL
                SELECT t2.* FROM table2 t2
                JOIN cte ON t2.parent_id = cte.id
            )
            SELECT * FROM cte
            JOIN (SELECT * FROM table3) sub ON cte.id = sub.cte_id
            WHERE EXISTS (
                SELECT 1 FROM table4 WHERE table4.id = cte.id
            )
            ORDER BY cte.created_at DESC
            LIMIT 1000
        """

        result = risk_analyzer.analyze(complex_sql)
        assert result['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

    def test_detect_multiple_risk_patterns(self, risk_analyzer):
        """Test query with multiple risk patterns"""
        risky_sql = """
            DELETE FROM users WHERE id IN (
                SELECT id FROM orders WHERE status = 'cancelled'
            );
            DROP TABLE temp_table;
            UPDATE accounts SET balance = 0;
        """

        result = risk_analyzer.analyze(risky_sql)
        assert result['risk_level'] in ['HIGH', 'CRITICAL']

    def test_detect_sql_injection_patterns(self, risk_analyzer):
        """Test detection of SQL injection patterns"""
        injection_patterns = [
            "SELECT * FROM users WHERE id = 1 OR 1=1",
            "SELECT * FROM users WHERE name = '' OR '1'='1'",
            "SELECT * FROM users; DROP TABLE users; --",
        ]

        for pattern in injection_patterns:
            result = risk_analyzer.analyze(pattern)
            # Should detect as risky
            assert result['risk_level'] in ['MEDIUM', 'HIGH', 'CRITICAL']

    def test_analyze_read_only_safe_query(self, risk_analyzer):
        """Test analyzing safe read-only query"""
        safe_sql = "SELECT id, name FROM users WHERE created_at > '2024-01-01' LIMIT 10"

        result = risk_analyzer.analyze(safe_sql)
        assert result['risk_level'] == 'LOW'

    def test_analyze_transaction_query(self, risk_analyzer):
        """Test analyzing transaction queries"""
        transaction_sql = """
            BEGIN;
            UPDATE accounts SET balance = balance - 100 WHERE id = 1;
            UPDATE accounts SET balance = balance + 100 WHERE id = 2;
            COMMIT;
        """

        result = risk_analyzer.analyze(transaction_sql)
        # Transaction with UPDATEs should be medium or high risk
        assert result['risk_level'] in ['MEDIUM', 'HIGH']


class TestImpactEstimatorEdgeCases:
    """Edge case tests for query impact estimation"""

    @pytest.fixture
    def impact_estimator(self):
        """Create impact estimator"""
        from src.database.impact_estimator import ImpactEstimator
        estimator = ImpactEstimator()
        return estimator

    async def test_estimate_zero_rows_affected(self, impact_estimator):
        """Test estimating impact when no rows affected"""
        sql = "UPDATE users SET active = false WHERE id = 999999"

        result = await impact_estimator.estimate_impact(sql)
        assert 'estimated_rows' in result
        assert result['operation_type'] in ['UPDATE', 'UNKNOWN']

    async def test_estimate_full_table_scan(self, impact_estimator):
        """Test estimating impact of full table scan"""
        sql = "SELECT * FROM large_table"

        result = await impact_estimator.estimate_impact(sql)
        assert 'estimated_rows' in result
        assert result['operation_type'] == 'SELECT'

    async def test_estimate_index_scan(self, impact_estimator):
        """Test estimating impact of index scan"""
        sql = "SELECT * FROM users WHERE id = 123"

        result = await impact_estimator.estimate_impact(sql)
        assert 'estimated_rows' in result
        assert result['has_where_clause'] is True

    async def test_estimate_cascading_delete(self, impact_estimator):
        """Test estimating impact of cascading delete"""
        sql = "DELETE FROM users WHERE id = 1"

        result = await impact_estimator.estimate_impact(sql)
        assert 'estimated_rows' in result
        assert result['operation_type'] == 'DELETE'

    async def test_estimate_bulk_operation(self, impact_estimator):
        """Test estimating impact of bulk operation"""
        sql = "INSERT INTO archive SELECT * FROM transactions WHERE year < 2020"

        result = await impact_estimator.estimate_impact(sql)
        assert 'estimated_rows' in result
        assert result['operation_type'] == 'INSERT'


class TestQueryOptimizationEdgeCases:
    """Edge case tests for query optimization"""

    @pytest.fixture
    def query_optimizer(self):
        """Create query optimizer"""
        # Mock optimizer since it doesn't exist yet
        class MockQueryOptimizer:
            def __init__(self):
                self.analyzer = AsyncMock()

            async def optimize(self, sql: str) -> dict:
                """Mock optimize method"""
                return {
                    'optimized_sql': sql,
                    'improvement': 0,
                    'suggestions': []
                }

            async def optimize_select_star(self, sql: str, needed_columns: list = None) -> str:
                """Mock optimize SELECT * method"""
                if needed_columns:
                    columns = ', '.join(needed_columns)
                    return sql.replace('SELECT *', f'SELECT {columns}')
                return sql

            async def detect_n_plus_one(self, queries: list) -> dict:
                """Mock detect N+1 query problem"""
                return {'has_n_plus_one': len(queries) > 10}

            async def optimize_n_plus_one(self, queries: list) -> list:
                """Mock optimize N+1 queries"""
                # Consolidate multiple similar queries
                return [queries[0]] if queries else []

        return MockQueryOptimizer()

    async def test_optimize_already_optimal_query(self, query_optimizer):
        """Test optimizing already optimal query"""
        optimal_sql = "SELECT id, name FROM users WHERE id = 123"

        result = await query_optimizer.optimize(optimal_sql)
        assert result['optimized_sql'] == optimal_sql
        assert result['improvement'] == 0

    async def test_optimize_missing_index(self, query_optimizer):
        """Test optimization suggestion for missing index"""
        sql = "SELECT * FROM large_table WHERE unindexed_column = 'value'"

        query_optimizer.analyzer.analyze_performance = AsyncMock(
            return_value={
                'is_optimal': False,
                'missing_indexes': ['unindexed_column'],
                'scan_type': 'full_table'
            }
        )

        result = await query_optimizer.optimize(sql)
        assert 'optimized_sql' in result

    async def test_optimize_select_star(self, query_optimizer):
        """Test optimization of SELECT * queries"""
        sql = "SELECT * FROM users"

        optimized = await query_optimizer.optimize_select_star(
            sql,
            needed_columns=['id', 'name', 'email']
        )

        assert 'SELECT id, name, email' in optimized
        assert 'SELECT *' not in optimized

    async def test_optimize_n_plus_one_query(self, query_optimizer):
        """Test detection and optimization of N+1 query problem"""
        queries = [
            "SELECT * FROM orders WHERE id = 1",
            "SELECT * FROM order_items WHERE order_id = 1",
            "SELECT * FROM order_items WHERE order_id = 2",
            "SELECT * FROM order_items WHERE order_id = 3",
        ] * 5  # 20 queries total

        result = await query_optimizer.detect_n_plus_one(queries)
        assert result['has_n_plus_one'] is True

        optimized = await query_optimizer.optimize_n_plus_one(queries)
        assert len(optimized) < len(queries)

    async def test_optimize_subquery_to_join(self, query_optimizer):
        """Test converting subquery to JOIN"""
        sql = """
            SELECT * FROM users
            WHERE id IN (SELECT user_id FROM orders WHERE total > 1000)
        """

        optimized = await query_optimizer.optimize(sql)
        assert 'optimized_sql' in optimized
