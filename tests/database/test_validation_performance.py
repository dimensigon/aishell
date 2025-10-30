"""
Performance benchmark for connection validation.

Tests that validation overhead is within acceptable limits (<5ms per validation).
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from src.database.pool import ConnectionPool


class TestValidationPerformanceBenchmark:
    """Benchmark validation performance."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_quick_validation_performance(self, mock_connect):
        """Test quick validation completes in <1ms."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1,
            validate_on_get=True
        )

        # Warm up
        for _ in range(10):
            pool._validate_connection(mock_conn, quick=True)

        # Measure performance
        iterations = 1000
        start_time = time.time()
        for _ in range(iterations):
            pool._validate_connection(mock_conn, quick=True)
        elapsed = time.time() - start_time

        avg_time_ms = (elapsed / iterations) * 1000
        print(f"\nQuick validation average time: {avg_time_ms:.4f}ms")

        # Should be < 1ms per validation
        assert avg_time_ms < 1.0, f"Quick validation too slow: {avg_time_ms}ms"

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_get_connection_overhead(self, mock_connect):
        """Test get_connection validation overhead is <5ms."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=5,
            validate_on_get=True
        )

        # Warm up
        for _ in range(10):
            conn = pool.get_connection()
            pool.release_connection(conn)

        # Measure performance
        iterations = 100
        start_time = time.time()
        for _ in range(iterations):
            conn = pool.get_connection()
            pool.release_connection(conn)
        elapsed = time.time() - start_time

        avg_time_ms = (elapsed / iterations) * 1000
        print(f"\nget_connection() with validation average time: {avg_time_ms:.4f}ms")

        # Should be < 5ms per get_connection call
        assert avg_time_ms < 5.0, f"get_connection() overhead too high: {avg_time_ms}ms"

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_validation_vs_no_validation_overhead(self, mock_connect):
        """Compare performance with and without validation."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Pool without validation
        pool_no_val = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=5,
            validate_on_get=False
        )

        # Measure without validation
        iterations = 100
        start_time = time.time()
        for _ in range(iterations):
            conn = pool_no_val.get_connection()
            pool_no_val.release_connection(conn)
        time_no_val = time.time() - start_time

        # Pool with validation
        pool_with_val = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=5,
            validate_on_get=True
        )

        # Measure with validation
        start_time = time.time()
        for _ in range(iterations):
            conn = pool_with_val.get_connection()
            pool_with_val.release_connection(conn)
        time_with_val = time.time() - start_time

        # Calculate overhead
        overhead_ms = ((time_with_val - time_no_val) / iterations) * 1000
        overhead_percent = ((time_with_val / max(time_no_val, 0.001)) - 1) * 100

        print(f"\nWithout validation: {(time_no_val/iterations)*1000:.4f}ms per call")
        print(f"With validation: {(time_with_val/iterations)*1000:.4f}ms per call")
        print(f"Overhead: {overhead_ms:.4f}ms ({overhead_percent:.2f}%)")

        # Overhead should be reasonable
        assert overhead_ms < 2.0, f"Validation overhead too high: {overhead_ms}ms"

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_statistics_tracking_overhead(self, mock_connect):
        """Test statistics tracking has minimal overhead."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=5,
            validate_on_get=True
        )

        # Measure get_validation_stats performance
        start_time = time.time()
        for _ in range(1000):
            pool.get_validation_stats()
        elapsed = time.time() - start_time

        avg_time_ms = (elapsed / 1000) * 1000
        print(f"\nget_validation_stats() average time: {avg_time_ms:.4f}ms")

        # Should be very fast (< 0.1ms)
        assert avg_time_ms < 0.1, f"Stats retrieval too slow: {avg_time_ms}ms"


if __name__ == "__main__":
    # Run benchmarks
    pytest.main([__file__, "-v", "-s"])
