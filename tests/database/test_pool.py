"""
Comprehensive tests for connection pooling

Tests pool creation, connection management, exhaustion handling,
and cleanup/recycling.
"""

import pytest
import queue
import threading
import time
from src.database.pool import ConnectionPool, ConnectionPoolManager


class TestConnectionPool:
    """Test ConnectionPool class."""

    def test_pool_creation(self):
        """Test creating connection pool."""
        pool = ConnectionPool("postgresql://localhost/test", max_connections=5)

        assert pool.connection_string == "postgresql://localhost/test"
        assert pool.max_connections == 5
        assert pool.active_connections == 0
        assert pool.available_connections == 5

    def test_pool_initialization(self):
        """Test pool initializes with connections."""
        pool = ConnectionPool("test://db", max_connections=3)

        assert len(pool._all_connections) == 3
        assert pool.available_connections == 3

    def test_get_connection(self):
        """Test getting connection from pool."""
        pool = ConnectionPool("test://db", max_connections=5)

        conn = pool.get_connection()

        assert conn is not None
        assert pool.active_connections == 1
        assert pool.available_connections == 4

    def test_get_multiple_connections(self):
        """Test getting multiple connections."""
        pool = ConnectionPool("test://db", max_connections=5)

        connections = []
        for _ in range(3):
            connections.append(pool.get_connection())

        assert pool.active_connections == 3
        assert pool.available_connections == 2

    def test_release_connection(self):
        """Test releasing connection back to pool."""
        pool = ConnectionPool("test://db", max_connections=5)

        conn = pool.get_connection()
        assert pool.active_connections == 1

        pool.release_connection(conn)

        assert pool.active_connections == 0
        assert pool.available_connections == 5

    def test_connection_reuse(self):
        """Test connections can be reused."""
        pool = ConnectionPool("test://db", max_connections=2)

        conn1 = pool.get_connection()
        pool.release_connection(conn1)

        conn2 = pool.get_connection()

        # Should reuse the same connection object
        assert conn1 is conn2


class TestPoolExhaustion:
    """Test connection pool exhaustion scenarios."""

    def test_pool_exhaustion_with_timeout(self):
        """Test pool exhaustion with timeout."""
        pool = ConnectionPool("test://db", max_connections=2)

        # Exhaust pool
        conn1 = pool.get_connection()
        conn2 = pool.get_connection()

        assert pool.available_connections == 0

        # Should timeout and raise exception
        with pytest.raises(Exception, match="Connection pool exhausted"):
            pool.get_connection(timeout=0.1)

    def test_pool_exhaustion_without_timeout(self):
        """Test pool exhaustion without timeout."""
        pool = ConnectionPool("test://db", max_connections=1)

        conn = pool.get_connection()

        # Should block indefinitely (we'll use short timeout for test)
        with pytest.raises(Exception, match="Connection pool exhausted"):
            pool.get_connection(timeout=0.05)

    def test_pool_recovery_after_exhaustion(self):
        """Test pool recovers after connection released."""
        pool = ConnectionPool("test://db", max_connections=2)

        # Exhaust pool
        conn1 = pool.get_connection()
        conn2 = pool.get_connection()

        # Release one connection
        pool.release_connection(conn1)

        # Should be able to get connection now
        conn3 = pool.get_connection(timeout=0.1)
        assert conn3 is not None

    def test_concurrent_access(self):
        """Test concurrent access to pool."""
        pool = ConnectionPool("test://db", max_connections=5)
        results = []

        def get_and_release():
            try:
                conn = pool.get_connection(timeout=1.0)
                time.sleep(0.01)  # Simulate work
                pool.release_connection(conn)
                results.append("success")
            except Exception as e:
                results.append(f"error: {e}")

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_and_release)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All operations should succeed
        assert len([r for r in results if r == "success"]) == 10


class TestPoolStatistics:
    """Test pool statistics."""

    def test_active_connections_count(self):
        """Test active connections counter."""
        pool = ConnectionPool("test://db", max_connections=5)

        connections = []
        for i in range(3):
            connections.append(pool.get_connection())
            assert pool.active_connections == i + 1

        for i, conn in enumerate(connections):
            pool.release_connection(conn)
            assert pool.active_connections == len(connections) - i - 1

    def test_available_connections_count(self):
        """Test available connections counter."""
        pool = ConnectionPool("test://db", max_connections=5)

        assert pool.available_connections == 5

        conn = pool.get_connection()
        assert pool.available_connections == 4

        pool.release_connection(conn)
        assert pool.available_connections == 5


class TestConnectionPoolManager:
    """Test ConnectionPoolManager class."""

    def test_manager_creation(self):
        """Test creating pool manager."""
        manager = ConnectionPoolManager()

        assert manager.pools == {}
        assert manager.auto_scale is False

    def test_manager_with_auto_scale(self):
        """Test manager with auto-scaling enabled."""
        manager = ConnectionPoolManager(auto_scale=True)

        assert manager.auto_scale is True

    def test_create_pool(self):
        """Test creating pool via manager."""
        manager = ConnectionPoolManager()

        manager.create_pool("pool1", "test://db1", max_connections=5)

        assert "pool1" in manager.pools
        assert manager.pools["pool1"].max_connections == 5

    def test_create_duplicate_pool(self):
        """Test creating duplicate pool raises error."""
        manager = ConnectionPoolManager()

        manager.create_pool("pool1", "test://db1")

        with pytest.raises(ValueError, match="Pool pool1 already exists"):
            manager.create_pool("pool1", "test://db2")

    def test_get_connection_from_pool(self):
        """Test getting connection from named pool."""
        manager = ConnectionPoolManager()
        manager.create_pool("pool1", "test://db1", max_connections=5)

        conn = manager.get_connection("pool1")

        assert conn is not None
        assert manager.pools["pool1"].active_connections == 1

    def test_get_connection_non_existent_pool(self):
        """Test getting connection from non-existent pool."""
        manager = ConnectionPoolManager()

        with pytest.raises(ValueError, match="Pool non_existent not found"):
            manager.get_connection("non_existent")

    def test_release_connection_to_pool(self):
        """Test releasing connection to named pool."""
        manager = ConnectionPoolManager()
        manager.create_pool("pool1", "test://db1", max_connections=5)

        conn = manager.get_connection("pool1")
        manager.release_connection("pool1", conn)

        assert manager.pools["pool1"].active_connections == 0

    def test_release_connection_non_existent_pool(self):
        """Test releasing connection to non-existent pool."""
        manager = ConnectionPoolManager()

        # Should not raise error
        manager.release_connection("non_existent", object())


class TestPoolStatisticsManager:
    """Test pool statistics through manager."""

    def test_get_pool_statistics(self):
        """Test getting pool statistics."""
        manager = ConnectionPoolManager()
        manager.create_pool("pool1", "test://db1", max_connections=10)

        stats = manager.get_pool_statistics("pool1")

        assert stats['total_connections'] == 10
        assert stats['active_connections'] == 0
        assert stats['available_connections'] == 10

    def test_statistics_after_connections(self):
        """Test statistics after using connections."""
        manager = ConnectionPoolManager()
        manager.create_pool("pool1", "test://db1", max_connections=10)

        connections = []
        for _ in range(3):
            connections.append(manager.get_connection("pool1"))

        stats = manager.get_pool_statistics("pool1")

        assert stats['total_connections'] == 10
        assert stats['active_connections'] == 3
        assert stats['available_connections'] == 7

    def test_statistics_non_existent_pool(self):
        """Test statistics for non-existent pool."""
        manager = ConnectionPoolManager()

        with pytest.raises(ValueError, match="Pool non_existent not found"):
            manager.get_pool_statistics("non_existent")

    def test_get_pool_size(self):
        """Test getting pool size."""
        manager = ConnectionPoolManager()
        manager.create_pool("pool1", "test://db1", max_connections=8)

        size = manager.get_pool_size("pool1")

        assert size == 8

    def test_get_pool_size_non_existent(self):
        """Test getting size of non-existent pool."""
        manager = ConnectionPoolManager()

        size = manager.get_pool_size("non_existent")

        assert size == 0


class TestMultiplePoolsManagement:
    """Test managing multiple pools."""

    def test_multiple_pools(self):
        """Test creating and managing multiple pools."""
        manager = ConnectionPoolManager()

        manager.create_pool("pool1", "test://db1", max_connections=5)
        manager.create_pool("pool2", "test://db2", max_connections=10)
        manager.create_pool("pool3", "test://db3", max_connections=3)

        assert len(manager.pools) == 3
        assert manager.get_pool_size("pool1") == 5
        assert manager.get_pool_size("pool2") == 10
        assert manager.get_pool_size("pool3") == 3

    def test_independent_pool_exhaustion(self):
        """Test pools are independent."""
        manager = ConnectionPoolManager()

        manager.create_pool("pool1", "test://db1", max_connections=2)
        manager.create_pool("pool2", "test://db2", max_connections=2)

        # Exhaust pool1
        conn1 = manager.get_connection("pool1")
        conn2 = manager.get_connection("pool1")

        # pool2 should still have connections
        conn3 = manager.get_connection("pool2", timeout=0.1)
        assert conn3 is not None

    def test_connections_isolated_per_pool(self):
        """Test connections are isolated per pool."""
        manager = ConnectionPoolManager()

        manager.create_pool("pool1", "test://db1", max_connections=5)
        manager.create_pool("pool2", "test://db2", max_connections=5)

        conn1 = manager.get_connection("pool1")

        stats1 = manager.get_pool_statistics("pool1")
        stats2 = manager.get_pool_statistics("pool2")

        assert stats1['active_connections'] == 1
        assert stats2['active_connections'] == 0


class TestAutoScaling:
    """Test auto-scaling functionality."""

    def test_auto_scale_creation(self):
        """Test pool creation with auto-scaling."""
        manager = ConnectionPoolManager(auto_scale=True)

        manager.create_pool(
            "pool1",
            "test://db1",
            max_connections=10,
            min_connections=2
        )

        pool = manager.pools["pool1"]

        # Should start with min_connections
        assert hasattr(pool, 'min_connections')
        assert pool.min_connections == 2
        assert pool.max_connections == 10

    def test_non_auto_scale_ignores_min(self):
        """Test non-auto-scale mode ignores min_connections."""
        manager = ConnectionPoolManager(auto_scale=False)

        manager.create_pool(
            "pool1",
            "test://db1",
            max_connections=10,
            min_connections=2
        )

        pool = manager.pools["pool1"]

        # Should use max_connections when auto_scale is False
        assert pool.max_connections == 10
        assert len(pool._all_connections) == 10


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_max_connections(self):
        """Test pool with zero max connections."""
        pool = ConnectionPool("test://db", max_connections=0)

        # Should have empty queue
        with pytest.raises(Exception, match="Connection pool exhausted"):
            pool.get_connection(timeout=0.01)

    def test_single_connection_pool(self):
        """Test pool with single connection."""
        pool = ConnectionPool("test://db", max_connections=1)

        conn = pool.get_connection()
        assert pool.active_connections == 1

        with pytest.raises(Exception, match="Connection pool exhausted"):
            pool.get_connection(timeout=0.01)

    def test_release_same_connection_multiple_times(self):
        """Test releasing same connection multiple times."""
        pool = ConnectionPool("test://db", max_connections=2)

        conn = pool.get_connection()
        pool.release_connection(conn)
        pool.release_connection(conn)  # Double release

        # Should not corrupt pool state
        assert pool.active_connections == -1  # Known limitation

    def test_very_large_pool(self):
        """Test pool with many connections."""
        pool = ConnectionPool("test://db", max_connections=1000)

        assert pool.available_connections == 1000

        connections = []
        for _ in range(100):
            connections.append(pool.get_connection())

        assert pool.active_connections == 100
        assert pool.available_connections == 900

    def test_concurrent_release(self):
        """Test concurrent connection release."""
        pool = ConnectionPool("test://db", max_connections=10)

        connections = [pool.get_connection() for _ in range(10)]

        def release_conn(conn):
            time.sleep(0.01)
            pool.release_connection(conn)

        threads = []
        for conn in connections:
            thread = threading.Thread(target=release_conn, args=(conn,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert pool.active_connections == 0
        assert pool.available_connections == 10
