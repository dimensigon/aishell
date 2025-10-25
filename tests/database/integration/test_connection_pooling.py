"""
Integration tests for database connection pooling.

Tests connection pool behavior, resilience, and performance across
Oracle, PostgreSQL, and MySQL databases.
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg2
from psycopg2 import pool as pg_pool
import pymysql

try:
    import cx_Oracle
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False


@pytest.mark.integration
class TestConnectionPoolBasics:
    """Test basic connection pool operations."""

    def test_postgresql_connection_pool_creation(self):
        """Test creating PostgreSQL connection pool."""
        pool = None
        try:
            pool = pg_pool.SimpleConnectionPool(
                minconn=2,
                maxconn=10,
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            assert pool is not None

            # Get connection from pool
            conn = pool.getconn()
            assert conn is not None

            # Verify connection works
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()[0]
                assert result == 1

            # Return connection
            pool.putconn(conn)

        finally:
            if pool:
                pool.closeall()

    @pytest.mark.skipif(not ORACLE_AVAILABLE, reason="cx_Oracle not installed")
    def test_oracle_connection_pool_creation(self):
        """Test creating Oracle connection pool."""
        pool = None
        try:
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="free")

            pool = cx_Oracle.SessionPool(
                user="SYS",
                password="MyOraclePass123",
                dsn=dsn,
                min=2,
                max=10,
                increment=1,
                mode=cx_Oracle.SYSDBA
            )

            assert pool is not None

            # Acquire connection
            conn = pool.acquire()
            assert conn is not None

            # Verify connection
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            result = cursor.fetchone()[0]
            assert result == 1
            cursor.close()

            # Release connection
            pool.release(conn)

        finally:
            if pool:
                pool.close()

    def test_mysql_connection_reuse(self):
        """Test MySQL connection reuse pattern."""
        connections = []

        try:
            # Create multiple connections
            for i in range(5):
                conn = pymysql.connect(
                    host="localhost",
                    port=3307,
                    database="mysql",
                    user="root",
                    password="MyMySQLPass123"
                )
                connections.append(conn)

            # Verify all connections work
            for conn in connections:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()[0]
                    assert result == 1

        finally:
            for conn in connections:
                conn.close()


@pytest.mark.integration
class TestConnectionPoolConcurrency:
    """Test connection pool behavior under concurrent load."""

    def test_postgresql_pool_concurrent_access(self):
        """Test PostgreSQL pool with concurrent connections."""
        pool = None

        try:
            pool = pg_pool.SimpleConnectionPool(
                minconn=2,
                maxconn=10,
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            def worker(pool, worker_id):
                """Worker function to acquire and use connection."""
                conn = pool.getconn()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT %s", (worker_id,))
                        result = cursor.fetchone()[0]
                        assert result == worker_id
                    return True
                finally:
                    pool.putconn(conn)

            # Run 50 concurrent workers
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(worker, pool, i) for i in range(50)]

                results = [f.result() for f in as_completed(futures)]
                assert all(results)

        finally:
            if pool:
                pool.closeall()

    @pytest.mark.skipif(not ORACLE_AVAILABLE, reason="cx_Oracle not installed")
    def test_oracle_pool_concurrent_access(self):
        """Test Oracle pool with concurrent connections."""
        pool = None

        try:
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="free")

            pool = cx_Oracle.SessionPool(
                user="SYS",
                password="MyOraclePass123",
                dsn=dsn,
                min=2,
                max=10,
                increment=1,
                mode=cx_Oracle.SYSDBA,
                threaded=True
            )

            def worker(pool, worker_id):
                """Worker function to acquire and use connection."""
                conn = pool.acquire()
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT :id FROM DUAL", {"id": worker_id})
                    result = cursor.fetchone()[0]
                    cursor.close()
                    assert result == worker_id
                    return True
                finally:
                    pool.release(conn)

            # Run 50 concurrent workers
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(worker, pool, i) for i in range(50)]

                results = [f.result() for f in as_completed(futures)]
                assert all(results)

        finally:
            if pool:
                pool.close()


@pytest.mark.integration
@pytest.mark.slow
class TestConnectionPoolResilience:
    """Test connection pool resilience and recovery."""

    def test_postgresql_pool_connection_recovery(self):
        """Test PostgreSQL pool recovers from connection failures."""
        pool = None

        try:
            pool = pg_pool.SimpleConnectionPool(
                minconn=2,
                maxconn=10,
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            # Get connection and simulate failure
            conn = pool.getconn()

            # Force close connection
            conn.close()

            # Try to return bad connection
            try:
                pool.putconn(conn, close=True)
            except:
                pass

            # Get new connection - pool should recover
            conn2 = pool.getconn()
            assert conn2 is not None

            # Verify new connection works
            with conn2.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()[0]
                assert result == 1

            pool.putconn(conn2)

        finally:
            if pool:
                pool.closeall()

    @pytest.mark.skipif(not ORACLE_AVAILABLE, reason="cx_Oracle not installed")
    def test_oracle_pool_max_connections_handling(self):
        """Test Oracle pool behavior when max connections reached."""
        pool = None

        try:
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="free")

            # Create pool with very low max
            pool = cx_Oracle.SessionPool(
                user="SYS",
                password="MyOraclePass123",
                dsn=dsn,
                min=1,
                max=3,
                increment=1,
                mode=cx_Oracle.SYSDBA,
                getmode=cx_Oracle.SPOOL_ATTRVAL_WAIT,
                timeout=5
            )

            connections = []

            try:
                # Acquire up to max connections
                for i in range(3):
                    conn = pool.acquire()
                    connections.append(conn)

                # Try to acquire one more - should wait and succeed eventually
                # (when we release one below)
                def acquire_with_timeout():
                    time.sleep(0.5)
                    # Release one connection
                    pool.release(connections[0])
                    connections.pop(0)

                # Start thread to release connection
                release_thread = threading.Thread(target=acquire_with_timeout)
                release_thread.start()

                # This should succeed after release
                conn4 = pool.acquire()
                assert conn4 is not None
                connections.append(conn4)

                release_thread.join()

            finally:
                # Release all connections
                for conn in connections:
                    try:
                        pool.release(conn)
                    except:
                        pass

        finally:
            if pool:
                pool.close()


@pytest.mark.integration
class TestConnectionPoolPerformance:
    """Test connection pool performance characteristics."""

    def test_postgresql_pool_performance(self):
        """Test PostgreSQL connection pool performance."""
        pool = None

        try:
            pool = pg_pool.SimpleConnectionPool(
                minconn=5,
                maxconn=20,
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            def execute_query(pool):
                """Execute simple query using pooled connection."""
                conn = pool.getconn()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM pg_tables")
                        cursor.fetchone()
                finally:
                    pool.putconn(conn)

            # Time 100 queries with connection pooling
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(execute_query, pool) for _ in range(100)]
                for f in as_completed(futures):
                    f.result()

            duration = time.time() - start_time

            # Should be reasonably fast with pooling
            assert duration < 10.0, f"Pooled queries took {duration:.2f}s, expected <10s"

        finally:
            if pool:
                pool.closeall()

    def test_mysql_connection_overhead(self):
        """Test MySQL connection creation overhead vs reuse."""
        def create_new_connections(count):
            """Create new connection for each operation."""
            start_time = time.time()

            for i in range(count):
                conn = pymysql.connect(
                    host="localhost",
                    port=3307,
                    database="mysql",
                    user="root",
                    password="MyMySQLPass123"
                )

                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

                conn.close()

            return time.time() - start_time

        def reuse_connection(count):
            """Reuse single connection."""
            start_time = time.time()

            conn = pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="MyMySQLPass123"
            )

            try:
                for i in range(count):
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
            finally:
                conn.close()

            return time.time() - start_time

        # Test with 50 operations
        new_conn_time = create_new_connections(50)
        reuse_conn_time = reuse_connection(50)

        # Reuse should be significantly faster
        assert reuse_conn_time < new_conn_time, \
            f"Connection reuse ({reuse_conn_time:.2f}s) should be faster than " \
            f"creating new ({new_conn_time:.2f}s)"
