"""
Comprehensive Unit Tests for N+1 Query Detector

Tests N+1 pattern detection, batch query suggestions, and integration
with the query optimizer.
"""

import pytest
from typing import List, Dict, Any

from src.database.n_plus_one_detector import (
    NPlusOneDetector,
    OptimizationSuggestion,
    OptimizationType,
    OptimizationLevel,
    create_detector
)
from src.database.query_optimizer import QueryOptimizer


# Test Fixtures

@pytest.fixture
def detector():
    """Create N+1 detector instance with default settings"""
    return NPlusOneDetector()


@pytest.fixture
def strict_detector():
    """Create detector with strict settings (low threshold)"""
    return NPlusOneDetector(time_window_ms=500, threshold=5)


@pytest.fixture
def lenient_detector():
    """Create detector with lenient settings (high threshold)"""
    return NPlusOneDetector(time_window_ms=2000, threshold=20)


@pytest.fixture
def optimizer():
    """Create query optimizer with N+1 detection"""
    return QueryOptimizer(database_type='postgresql')


# Helper Functions

def create_query_log(
    query_template: str,
    count: int,
    start_time: float = 0.0,
    time_increment: float = 1.0,
    params_generator=None
) -> List[Dict[str, Any]]:
    """
    Helper to create query log for testing.

    Args:
        query_template: SQL query template (use {} for params)
        count: Number of queries to generate
        start_time: Starting timestamp
        time_increment: Time between queries in ms
        params_generator: Function to generate params for each query

    Returns:
        Query log list
    """
    log = []
    for i in range(count):
        params = params_generator(i) if params_generator else [i + 1]
        query = query_template.format(*params) if '{}' in query_template else query_template
        log.append({
            'query': query,
            'timestamp': start_time + (i * time_increment),
            'params': params
        })
    return log


# Test Basic Detection

class TestBasicN1Detection:
    """Test basic N+1 query detection"""

    def test_detect_simple_n_plus_one(self, detector):
        """Test detection of simple N+1 pattern"""
        # Simulate: SELECT * FROM users; then 15 queries for orders
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0
        assert suggestions[0].type == OptimizationType.N_PLUS_ONE
        assert suggestions[0].level == OptimizationLevel.CRITICAL
        assert '15' in suggestions[0].message

    def test_no_detection_below_threshold(self, detector):
        """Test no detection when below threshold"""
        # Only 5 queries (below default threshold of 10)
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=5,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) == 0

    def test_no_detection_outside_time_window(self, detector):
        """Test no detection when queries are spread over long time"""
        # 20 queries but over 5 seconds (outside 1 second window)
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=20,
            start_time=0.0,
            time_increment=250.0,  # 250ms between queries = 5 seconds total
            params_generator=lambda i: [i + 1]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        # Should not detect due to time window
        assert len(suggestions) == 0


# Test Sequential ID Detection

class TestSequentialIDDetection:
    """Test detection of sequential ID patterns"""

    def test_detect_sequential_ids(self, detector):
        """Test detection with sequential IDs"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]  # Sequential: 1, 2, 3, ...
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0
        # Should contain N+1 pattern explanation (various keywords possible)
        explanation = str(suggestions[0].explanation).lower()
        assert any(keyword in explanation for keyword in ['n+1', 'join', 'batch', 'similar queries'])

    def test_detect_non_sequential_distinct_ids(self, detector):
        """Test detection with non-sequential but distinct IDs"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i * 10 + 3]  # 3, 13, 23, 33, ...
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0

    def test_detect_uuid_iteration(self, detector):
        """Test detection with UUID-like parameters"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = '{}'",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [f"uuid-{i:04d}"]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0


# Test Query Template Normalization

class TestQueryNormalization:
    """Test query template normalization"""

    def test_normalize_numeric_params(self, detector):
        """Test normalization of numeric parameters"""
        query1 = "SELECT * FROM orders WHERE user_id = 123"
        query2 = "SELECT * FROM orders WHERE user_id = 456"

        template1 = detector._normalize_to_template(query1)
        template2 = detector._normalize_to_template(query2)

        assert template1 == template2
        assert '?' in template1

    def test_normalize_string_params(self, detector):
        """Test normalization of string parameters"""
        query1 = "SELECT * FROM users WHERE email = 'alice@example.com'"
        query2 = "SELECT * FROM users WHERE email = 'bob@example.com'"

        template1 = detector._normalize_to_template(query1)
        template2 = detector._normalize_to_template(query2)

        assert template1 == template2
        assert '?' in template1

    def test_normalize_case_insensitive(self, detector):
        """Test case-insensitive normalization"""
        query1 = "select * from orders where user_id = 1"
        query2 = "SELECT * FROM orders WHERE user_id = 2"

        template1 = detector._normalize_to_template(query1)
        template2 = detector._normalize_to_template(query2)

        assert template1 == template2
        assert template1.isupper()

    def test_normalize_whitespace(self, detector):
        """Test whitespace normalization"""
        query1 = "SELECT  *  FROM   orders   WHERE user_id = 1"
        query2 = "SELECT * FROM orders WHERE user_id = 2"

        template1 = detector._normalize_to_template(query1)
        template2 = detector._normalize_to_template(query2)

        assert template1 == template2

    def test_normalize_removes_comments(self, detector):
        """Test comment removal in normalization"""
        query1 = "SELECT * FROM orders -- comment\nWHERE user_id = 1"
        query2 = "SELECT * FROM orders WHERE user_id = 2"

        template1 = detector._normalize_to_template(query1)
        template2 = detector._normalize_to_template(query2)

        assert template1 == template2
        assert '--' not in template1


# Test Batch Query Suggestions

class TestBatchQuerySuggestions:
    """Test batch query suggestion generation"""

    def test_suggest_in_clause(self, detector):
        """Test suggestion includes IN clause"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0
        assert 'IN' in suggestions[0].suggested_query
        assert '?' in suggestions[0].suggested_query

    def test_suggest_join_alternative(self, detector):
        """Test suggestion includes JOIN alternative"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0
        # Should mention JOIN as an alternative in explanation
        assert 'JOIN' in suggestions[0].explanation or 'JOIN' in suggestions[0].suggested_query

    def test_suggestion_includes_improvement_estimate(self, detector):
        """Test suggestion includes performance improvement estimate"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=20,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0
        assert suggestions[0].estimated_improvement is not None
        assert '20' in suggestions[0].estimated_improvement


# Test Suggestion Details

class TestSuggestionDetails:
    """Test optimization suggestion details"""

    def test_suggestion_includes_pattern_count(self, detector):
        """Test suggestion details include pattern count"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0
        assert 'details' in suggestions[0].__dict__
        assert suggestions[0].details is not None
        assert suggestions[0].details['pattern_count'] == 15

    def test_suggestion_includes_time_window(self, detector):
        """Test suggestion details include time window"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0
        assert 'time_window_ms' in suggestions[0].details
        assert suggestions[0].details['time_window_ms'] >= 0

    def test_suggestion_includes_sample_params(self, detector):
        """Test suggestion details include sample parameters"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0
        assert 'sample_params' in suggestions[0].details
        assert len(suggestions[0].details['sample_params']) <= 5


# Test Configuration

class TestDetectorConfiguration:
    """Test detector configuration options"""

    def test_custom_time_window(self):
        """Test custom time window configuration"""
        detector = NPlusOneDetector(time_window_ms=2000, threshold=10)

        # 15 queries over 1.5 seconds (within 2s window)
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=100.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0

    def test_custom_threshold(self):
        """Test custom threshold configuration"""
        detector = NPlusOneDetector(time_window_ms=1000, threshold=5)

        # Only 7 queries (above threshold of 5)
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=7,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0

    def test_factory_function(self):
        """Test create_detector factory function"""
        detector = create_detector(time_window_ms=500, threshold=5)

        assert detector.time_window_ms == 500
        assert detector.threshold == 5


# Test Integration with Query Optimizer

class TestQueryOptimizerIntegration:
    """Test integration with QueryOptimizer"""

    def test_optimizer_has_n_plus_one_detector(self, optimizer):
        """Test optimizer includes N+1 detector"""
        assert hasattr(optimizer, 'n_plus_one_detector')
        assert isinstance(optimizer.n_plus_one_detector, NPlusOneDetector)

    def test_optimizer_analyze_query_log(self, optimizer):
        """Test optimizer can analyze query logs"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = optimizer.analyze_query_log(query_log)

        assert len(suggestions) > 0
        assert any(s.type == OptimizationType.N_PLUS_ONE for s in suggestions)

    def test_optimizer_detect_n_plus_one_method(self, optimizer):
        """Test optimizer has detect_n_plus_one method"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        suggestions = optimizer.detect_n_plus_one(query_log)

        assert len(suggestions) > 0

    def test_optimizer_custom_parameters(self, optimizer):
        """Test optimizer accepts custom N+1 parameters"""
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=7,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        )

        # Should detect with lower threshold
        suggestions = optimizer.detect_n_plus_one(
            query_log,
            time_window_ms=1000,
            threshold=5
        )

        assert len(suggestions) > 0


# Test Real-World Scenarios

class TestRealWorldScenarios:
    """Test real-world N+1 scenarios"""

    def test_user_orders_n_plus_one(self, detector):
        """Test typical user-orders N+1 pattern"""
        query_log = [
            {
                'query': 'SELECT * FROM users LIMIT 20',
                'timestamp': 0.0,
                'params': []
            }
        ]

        # Add 20 queries for orders
        query_log.extend(create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=20,
            start_time=10.0,
            time_increment=5.0,
            params_generator=lambda i: [i + 1]
        ))

        suggestions = detector.detect_n_plus_one(query_log)

        assert len(suggestions) > 0
        assert 'orders' in suggestions[0].original_query.lower()

    def test_nested_n_plus_one(self, detector):
        """Test nested N+1 pattern (N+N+1)"""
        query_log = []

        # 15 user queries
        query_log.extend(create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=0.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 1]
        ))

        # 15 order_items queries
        query_log.extend(create_query_log(
            "SELECT * FROM order_items WHERE order_id = {}",
            count=15,
            start_time=200.0,
            time_increment=10.0,
            params_generator=lambda i: [i + 100]
        ))

        suggestions = detector.detect_n_plus_one(query_log)

        # Should detect both patterns
        assert len(suggestions) >= 1

    def test_mixed_query_types(self, detector):
        """Test N+1 detection with mixed query types"""
        query_log = []

        # Some unrelated queries
        query_log.append({
            'query': 'SELECT COUNT(*) FROM users',
            'timestamp': 0.0,
            'params': []
        })

        # N+1 pattern
        query_log.extend(create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=15,
            start_time=10.0,
            time_increment=5.0,
            params_generator=lambda i: [i + 1]
        ))

        # More unrelated queries
        query_log.append({
            'query': 'SELECT * FROM products LIMIT 10',
            'timestamp': 500.0,
            'params': []
        })

        suggestions = detector.detect_n_plus_one(query_log)

        # Should detect only the N+1 pattern
        assert len(suggestions) >= 1
        assert suggestions[0].details['pattern_count'] == 15


# Test Edge Cases

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_query_log(self, detector):
        """Test empty query log"""
        suggestions = detector.detect_n_plus_one([])
        assert len(suggestions) == 0

    def test_single_query(self, detector):
        """Test single query in log"""
        query_log = [{
            'query': 'SELECT * FROM users',
            'timestamp': 0.0,
            'params': []
        }]

        suggestions = detector.detect_n_plus_one(query_log)
        assert len(suggestions) == 0

    def test_missing_timestamp(self, detector):
        """Test query log with missing timestamp"""
        query_log = [
            {
                'query': f'SELECT * FROM orders WHERE user_id = {i}',
                'params': [i]
            }
            for i in range(15)
        ]

        # Should handle gracefully (use default timestamp of 0.0)
        suggestions = detector.detect_n_plus_one(query_log)
        assert isinstance(suggestions, list)

    def test_missing_params(self, detector):
        """Test query log with missing params"""
        query_log = [
            {
                'query': f'SELECT * FROM orders WHERE user_id = {i}',
                'timestamp': i * 10.0
            }
            for i in range(15)
        ]

        # Should handle gracefully (use empty params list)
        suggestions = detector.detect_n_plus_one(query_log)
        assert isinstance(suggestions, list)

    def test_malformed_query_entry(self, detector):
        """Test query log with malformed entry"""
        query_log = [
            {'query': None, 'timestamp': 0.0, 'params': []},
            *create_query_log(
                "SELECT * FROM orders WHERE user_id = {}",
                count=15,
                start_time=10.0,
                time_increment=5.0,
                params_generator=lambda i: [i + 1]
            )
        ]

        # Should handle gracefully and detect pattern
        suggestions = detector.detect_n_plus_one(query_log)
        assert len(suggestions) > 0


# Test Performance

class TestPerformance:
    """Test detector performance"""

    def test_large_query_log(self, detector):
        """Test performance with large query log"""
        # Create log with 1000 queries
        query_log = create_query_log(
            "SELECT * FROM orders WHERE user_id = {}",
            count=1000,
            start_time=0.0,
            time_increment=0.5,
            params_generator=lambda i: [i % 50]  # Repeat every 50
        )

        import time
        start = time.time()
        suggestions = detector.detect_n_plus_one(query_log)
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 2.0
        assert isinstance(suggestions, list)

    def test_many_unique_patterns(self, detector):
        """Test performance with many unique query patterns"""
        query_log = []

        # Add 10 different query patterns
        for table_num in range(10):
            query_log.extend(create_query_log(
                f"SELECT * FROM table_{table_num} WHERE id = {{}}",
                count=12,
                start_time=table_num * 200.0,
                time_increment=5.0,
                params_generator=lambda i: [i + 1]
            ))

        import time
        start = time.time()
        suggestions = detector.detect_n_plus_one(query_log)
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 2.0
        # Should detect multiple patterns
        assert len(suggestions) >= 5
