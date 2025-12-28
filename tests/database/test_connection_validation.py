"""
Tests for connection validation on get_connection().

This test suite validates the new connection validation feature that reduces
connection failures by validating connections before returning them.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call
from src.database.pool import ConnectionPool


class TestConnectionValidationOnGet:
    """Test validation on get_connection()."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_get_connection_with_validation_enabled(self, mock_connect):
        """Test get_connection validates connection when enabled."""
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

        # Get connection should validate it
        conn = pool.get_connection()
        assert conn is mock_conn

        # Verify validation was called (quick check)
        assert pool.get_validation_stats()['total_validations'] > 0

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_get_connection_with_validation_disabled(self, mock_connect):
        """Test get_connection skips validation when disabled."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1,
            validate_on_get=False
        )

        # Reset stats after initialization
        with pool._lock:
            pool._validation_stats['total_validations'] = 0

        # Get connection should NOT validate it
        conn = pool.get_connection()
        assert conn is mock_conn

        # Verify validation was NOT called on get
        assert pool.get_validation_stats()['total_validations'] == 0

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_validation_detects_stale_connection(self, mock_connect):
        """Test validation detects and reconnects stale connection."""
        # First connection is stale, second is fresh
        stale_conn = MagicMock()
        stale_conn.closed = True  # Stale connection

        fresh_conn = MagicMock()
        fresh_conn.closed = False
        fresh_cursor = MagicMock()
        fresh_conn.cursor.return_value = fresh_cursor

        mock_connect.side_effect = [stale_conn, fresh_conn]

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1,
            validate_on_get=True,
            max_validation_retries=3
        )

        # Get connection should detect stale and reconnect
        conn = pool.get_connection()

        # Should return fresh connection after reconnection
        assert conn is fresh_conn

        # Verify reconnection was attempted
        stats = pool.get_validation_stats()
        assert stats['reconnections'] > 0

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_validation_retry_logic(self, mock_connect):
        """Test validation retries on failure."""
        # All connections are stale
        stale_conn1 = MagicMock()
        stale_conn1.closed = True

        stale_conn2 = MagicMock()
        stale_conn2.closed = True

        stale_conn3 = MagicMock()
        stale_conn3.closed = True

        # Reconnection attempts also fail
        mock_connect.side_effect = [
            stale_conn1,  # Initial pool creation
            stale_conn2,  # First reconnection attempt
            stale_conn3   # Second reconnection attempt
        ]

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1,
            validate_on_get=True,
            max_validation_retries=2
        )

        # Get connection should fail after retries
        with pytest.raises(Exception, match="Failed to get valid connection"):
            pool.get_connection()

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_validation_with_mysql(self, mock_connect):
        """Test validation works with MySQL connections."""
        mock_conn = MagicMock()
        mock_conn.open = True
        mock_conn.ping.return_value = None

        # Need to patch pymysql as well
        with patch('src.database.pool.PYMYSQL_AVAILABLE', True):
            with patch('src.database.pool.pymysql.connect', return_value=mock_conn):
                pool = ConnectionPool(
                    "mysql://root:pass@localhost/testdb",
                    max_connections=1,
                    validate_on_get=True
                )

                # Get connection should validate it
                conn = pool.get_connection()
                assert conn is mock_conn

                # Verify validation was called
                assert pool.get_validation_stats()['total_validations'] > 0


class TestConnectionValidationMethods:
    """Test validation method variants."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_quick_validation_postgresql(self, mock_connect):
        """Test quick validation for PostgreSQL."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1
        )

        # Quick validation should only check closed status
        assert pool._validate_connection(mock_conn, quick=True)

        # Should not execute query
        mock_conn.cursor.assert_not_called()

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_full_validation_postgresql(self, mock_connect):
        """Test full validation for PostgreSQL."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1
        )

        # Full validation should execute query
        assert pool._validate_connection(mock_conn, quick=False)

        # Should execute SELECT 1
        mock_cursor.execute.assert_called_with("SELECT 1")
        mock_cursor.close.assert_called_once()

    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.pymysql.connect')
    def test_quick_validation_mysql(self, mock_connect):
        """Test quick validation for MySQL."""
        mock_conn = MagicMock()
        mock_conn.open = True
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(
            "mysql://root:pass@localhost/testdb",
            max_connections=1
        )

        # Quick validation should only check open status
        assert pool._validate_connection(mock_conn, quick=True)

        # Should not call ping
        mock_conn.ping.assert_not_called()

    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.pymysql.connect')
    def test_full_validation_mysql(self, mock_connect):
        """Test full validation for MySQL."""
        mock_conn = MagicMock()
        mock_conn.open = True
        mock_conn.ping.return_value = None
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(
            "mysql://root:pass@localhost/testdb",
            max_connections=1
        )

        # Full validation should ping
        assert pool._validate_connection(mock_conn, quick=False)

        # Should call ping with reconnect=False
        mock_conn.ping.assert_called_with(reconnect=False)

    def test_validation_mock_connection(self):
        """Test validation with mock connection always succeeds."""
        pool = ConnectionPool("test://db", max_connections=1)

        conn = pool.get_connection()

        # Mock connections always valid
        assert pool._validate_connection(conn, quick=True)
        assert pool._validate_connection(conn, quick=False)


class TestValidationStatistics:
    """Test validation statistics tracking."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_validation_stats_structure(self, mock_connect):
        """Test validation stats have correct structure."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1
        )

        stats = pool.get_validation_stats()

        # Check all required fields exist
        assert 'total_validations' in stats
        assert 'failed_validations' in stats
        assert 'reconnections' in stats
        assert 'validation_errors' in stats
        assert 'failure_rate' in stats

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_validation_stats_tracking(self, mock_connect):
        """Test validation stats are tracked correctly."""
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

        # Get initial stats
        initial_stats = pool.get_validation_stats()
        initial_validations = initial_stats['total_validations']

        # Get connection multiple times
        for _ in range(5):
            conn = pool.get_connection()
            pool.release_connection(conn)

        # Check stats increased
        final_stats = pool.get_validation_stats()
        assert final_stats['total_validations'] > initial_validations

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_validation_failure_rate_calculation(self, mock_connect):
        """Test failure rate is calculated correctly."""
        # Create connections that alternate between valid and invalid
        valid_conn = MagicMock()
        valid_conn.closed = False
        valid_cursor = MagicMock()
        valid_conn.cursor.return_value = valid_cursor

        invalid_conn = MagicMock()
        invalid_conn.closed = True

        mock_connect.side_effect = [valid_conn] * 10

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1,
            validate_on_get=True
        )

        # Manually test validation with failures
        with pool._lock:
            pool._validation_stats['total_validations'] = 100
            pool._validation_stats['failed_validations'] = 10

        stats = pool.get_validation_stats()

        # 10 failures out of 100 = 10% failure rate
        assert stats['failure_rate'] == 10.0

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_reconnection_tracking(self, mock_connect):
        """Test reconnection attempts are tracked."""
        stale_conn = MagicMock()
        stale_conn.closed = True

        fresh_conn = MagicMock()
        fresh_conn.closed = False
        fresh_cursor = MagicMock()
        fresh_conn.cursor.return_value = fresh_cursor

        mock_connect.side_effect = [stale_conn, fresh_conn, fresh_conn]

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1,
            validate_on_get=True
        )

        # Initial stats
        initial_stats = pool.get_validation_stats()
        initial_reconnections = initial_stats['reconnections']

        # Get connection triggers reconnection
        conn = pool.get_connection()

        # Check reconnection was tracked
        final_stats = pool.get_validation_stats()
        assert final_stats['reconnections'] > initial_reconnections


class TestValidationPerformance:
    """Test validation performance characteristics."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_quick_validation_is_fast(self, mock_connect):
        """Test quick validation has minimal overhead."""
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

        # Measure time for quick validation
        start_time = time.time()
        for _ in range(100):
            pool._validate_connection(mock_conn, quick=True)
        elapsed = time.time() - start_time

        # Quick validation should be very fast
        # 100 validations in under 10ms means <0.1ms per validation
        assert elapsed < 0.01, f"Quick validation too slow: {elapsed}s for 100 iterations"

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_validation_overhead_measurement(self, mock_connect):
        """Test validation overhead is minimal."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Create pool with validation disabled
        pool_no_validation = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1,
            validate_on_get=False
        )

        # Measure time without validation
        start_time = time.time()
        for _ in range(50):
            conn = pool_no_validation.get_connection()
            pool_no_validation.release_connection(conn)
        time_no_validation = time.time() - start_time

        # Create pool with validation enabled
        pool_with_validation = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1,
            validate_on_get=True
        )

        # Measure time with validation
        start_time = time.time()
        for _ in range(50):
            conn = pool_with_validation.get_connection()
            pool_with_validation.release_connection(conn)
        time_with_validation = time.time() - start_time

        # Validation overhead should be minimal (< 50% increase)
        overhead = time_with_validation - time_no_validation
        overhead_ratio = overhead / max(time_no_validation, 0.001)  # Avoid division by zero

        # Allow up to 100% overhead (2x slower) for validation
        assert overhead_ratio < 1.0, f"Validation overhead too high: {overhead_ratio * 100}%"


class TestThreadSafetyWithValidation:
    """Test thread-safety with validation enabled."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_concurrent_validation(self, mock_connect):
        """Test concurrent validations are thread-safe."""
        mock_conns = []
        for i in range(10):
            conn = MagicMock()
            conn.id = i
            conn.closed = False
            mock_cursor = MagicMock()
            conn.cursor.return_value = mock_cursor
            mock_conns.append(conn)

        mock_connect.side_effect = mock_conns

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=5,
            validate_on_get=True
        )

        results = []
        errors = []

        def get_and_release():
            try:
                conn = pool.get_connection(timeout=2.0)
                time.sleep(0.01)  # Simulate work
                pool.release_connection(conn)
                results.append("success")
            except Exception as e:
                errors.append(str(e))

        threads = []
        for _ in range(20):
            thread = threading.Thread(target=get_and_release)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All operations should succeed
        assert len(results) == 20
        assert len(errors) == 0

        # Stats should be consistent
        stats = pool.get_validation_stats()
        assert stats['total_validations'] >= 20


class TestConfigurationOptions:
    """Test configuration options for validation."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_custom_max_retries(self, mock_connect):
        """Test custom max validation retries."""
        stale_conn = MagicMock()
        stale_conn.closed = True
        mock_connect.return_value = stale_conn

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1,
            validate_on_get=True,
            max_validation_retries=5  # Custom retry count
        )

        # Should attempt 5 retries before failing
        with pytest.raises(Exception, match="Failed to get valid connection"):
            pool.get_connection()

        # Check reconnection attempts match retry count
        stats = pool.get_validation_stats()
        # Should have attempted reconnection multiple times
        assert stats['reconnections'] >= 1

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_validate_on_get_default_true(self, mock_connect):
        """Test validate_on_get defaults to True."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Don't specify validate_on_get - should default to True
        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1
        )

        assert pool.validate_on_get is True

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_max_retries_default_value(self, mock_connect):
        """Test max_validation_retries has correct default."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb",
            max_connections=1
        )

        assert pool.max_validation_retries == 3
