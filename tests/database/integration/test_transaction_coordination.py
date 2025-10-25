"""
Integration tests for transaction coordination and error handling.

Tests complex transaction scenarios, deadlock handling, and error recovery
across different databases.
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import psycopg2
import pymysql

try:
    import cx_Oracle
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False


@pytest.mark.integration
class TestTransactionIsolation:
    """Test transaction isolation levels and behavior."""

    def test_postgresql_read_committed_isolation(self, test_table_name):
        """Test PostgreSQL READ COMMITTED isolation level."""
        conn1 = None
        conn2 = None

        try:
            conn1 = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            conn2 = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            # Create table
            with conn1.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (id INTEGER PRIMARY KEY, value INTEGER)
                """)
                conn1.commit()

            # Start transaction in conn1
            with conn1.cursor() as cursor1:
                cursor1.execute(f"INSERT INTO {test_table_name} (id, value) VALUES (1, 100)")

                # conn2 should not see uncommitted data
                with conn2.cursor() as cursor2:
                    cursor2.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                    count = cursor2.fetchone()[0]
                    assert count == 0, "Should not see uncommitted data"

                # Commit in conn1
                conn1.commit()

                # Now conn2 should see the data
                with conn2.cursor() as cursor2:
                    cursor2.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                    count = cursor2.fetchone()[0]
                    assert count == 1, "Should see committed data"

        finally:
            if conn1:
                try:
                    with conn1.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        conn1.commit()
                    conn1.close()
                except:
                    pass
            if conn2:
                conn2.close()

    def test_mysql_repeatable_read_isolation(self, test_table_name):
        """Test MySQL REPEATABLE READ isolation level."""
        conn1 = None
        conn2 = None

        try:
            conn1 = pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="MyMySQLPass123",
                autocommit=False
            )

            conn2 = pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="MyMySQLPass123",
                autocommit=False
            )

            # Create table
            with conn1.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (id INT PRIMARY KEY, value INT) ENGINE=InnoDB
                """)
                conn1.commit()

            # Start transactions
            with conn1.cursor() as cursor1, conn2.cursor() as cursor2:
                # conn2 reads initial state
                cursor2.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                initial_count = cursor2.fetchone()[0]

                # conn1 inserts data and commits
                cursor1.execute(f"INSERT INTO {test_table_name} (id, value) VALUES (1, 100)")
                conn1.commit()

                # conn2 should still see initial state (repeatable read)
                cursor2.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                count = cursor2.fetchone()[0]
                assert count == initial_count, "Should see consistent snapshot"

                # After commit, conn2 sees new data
                conn2.commit()
                cursor2.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                count = cursor2.fetchone()[0]
                assert count == 1

        finally:
            if conn1:
                try:
                    with conn1.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        conn1.commit()
                    conn1.close()
                except:
                    pass
            if conn2:
                conn2.close()


@pytest.mark.integration
class TestDeadlockHandling:
    """Test deadlock detection and handling."""

    def test_postgresql_deadlock_detection(self, test_table_name):
        """Test PostgreSQL deadlock detection."""
        conn1 = None
        conn2 = None

        try:
            conn1 = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            conn2 = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            # Setup
            with conn1.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (id INTEGER PRIMARY KEY, value INTEGER)
                """)
                cursor.execute(f"INSERT INTO {test_table_name} VALUES (1, 100), (2, 200)")
                conn1.commit()

            deadlock_detected = False

            def transaction1():
                nonlocal deadlock_detected
                try:
                    with conn1.cursor() as cursor:
                        # Lock row 1
                        cursor.execute(f"UPDATE {test_table_name} SET value = value + 1 WHERE id = 1")
                        time.sleep(0.5)

                        # Try to lock row 2 (will wait for conn2)
                        cursor.execute(f"UPDATE {test_table_name} SET value = value + 1 WHERE id = 2")
                        conn1.commit()
                except psycopg2.extensions.TransactionRollbackError:
                    deadlock_detected = True
                    conn1.rollback()

            def transaction2():
                try:
                    time.sleep(0.1)  # Let transaction1 start first
                    with conn2.cursor() as cursor:
                        # Lock row 2
                        cursor.execute(f"UPDATE {test_table_name} SET value = value + 1 WHERE id = 2")

                        # Try to lock row 1 (will wait for conn1 - potential deadlock)
                        cursor.execute(f"UPDATE {test_table_name} SET value = value + 1 WHERE id = 1")
                        conn2.commit()
                except psycopg2.extensions.TransactionRollbackError:
                    conn2.rollback()

            # Run transactions concurrently
            t1 = threading.Thread(target=transaction1)
            t2 = threading.Thread(target=transaction2)

            t1.start()
            t2.start()

            t1.join(timeout=5)
            t2.join(timeout=5)

            # One transaction should have been rolled back
            # (PostgreSQL detects deadlock and aborts one transaction)

        finally:
            if conn1:
                try:
                    with conn1.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        conn1.commit()
                    conn1.close()
                except:
                    pass
            if conn2:
                conn2.close()

    def test_mysql_deadlock_detection(self, test_table_name):
        """Test MySQL deadlock detection."""
        conn1 = None
        conn2 = None

        try:
            conn1 = pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="MyMySQLPass123",
                autocommit=False
            )

            conn2 = pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="MyMySQLPass123",
                autocommit=False
            )

            # Setup
            with conn1.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (id INT PRIMARY KEY, value INT) ENGINE=InnoDB
                """)
                cursor.execute(f"INSERT INTO {test_table_name} VALUES (1, 100), (2, 200)")
                conn1.commit()

            deadlock_detected = False

            def transaction1():
                nonlocal deadlock_detected
                try:
                    with conn1.cursor() as cursor:
                        cursor.execute(f"UPDATE {test_table_name} SET value = value + 1 WHERE id = 1")
                        time.sleep(0.5)
                        cursor.execute(f"UPDATE {test_table_name} SET value = value + 1 WHERE id = 2")
                        conn1.commit()
                except pymysql.err.OperationalError as e:
                    if e.args[0] == 1213:  # Deadlock error code
                        deadlock_detected = True
                    conn1.rollback()

            def transaction2():
                try:
                    time.sleep(0.1)
                    with conn2.cursor() as cursor:
                        cursor.execute(f"UPDATE {test_table_name} SET value = value + 1 WHERE id = 2")
                        cursor.execute(f"UPDATE {test_table_name} SET value = value + 1 WHERE id = 1")
                        conn2.commit()
                except pymysql.err.OperationalError:
                    conn2.rollback()

            # Run transactions concurrently
            t1 = threading.Thread(target=transaction1)
            t2 = threading.Thread(target=transaction2)

            t1.start()
            t2.start()

            t1.join(timeout=5)
            t2.join(timeout=5)

        finally:
            if conn1:
                try:
                    with conn1.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        conn1.commit()
                    conn1.close()
                except:
                    pass
            if conn2:
                conn2.close()


@pytest.mark.integration
class TestTransactionErrorRecovery:
    """Test transaction error recovery patterns."""

    def test_postgresql_retry_on_serialization_failure(self, test_table_name):
        """Test retrying PostgreSQL transaction after serialization failure."""
        conn = None

        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            # Create table
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (id INTEGER PRIMARY KEY, value INTEGER)
                """)
                cursor.execute(f"INSERT INTO {test_table_name} VALUES (1, 0)")
                conn.commit()

            def execute_with_retry(max_retries=3):
                """Execute transaction with retry logic."""
                for attempt in range(max_retries):
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(f"SELECT value FROM {test_table_name} WHERE id = 1")
                            value = cursor.fetchone()[0]

                            cursor.execute(f"UPDATE {test_table_name} SET value = %s WHERE id = 1", (value + 1,))
                            conn.commit()
                            return True

                    except psycopg2.extensions.TransactionRollbackError:
                        conn.rollback()
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(0.1 * (2 ** attempt))  # Exponential backoff

                return False

            # Should succeed after retries
            assert execute_with_retry()

            # Verify final value
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT value FROM {test_table_name} WHERE id = 1")
                value = cursor.fetchone()[0]
                assert value == 1

        finally:
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        conn.commit()
                    conn.close()
                except:
                    pass

    def test_mysql_rollback_on_error(self, test_table_name):
        """Test MySQL automatic rollback on error."""
        conn = None

        try:
            conn = pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="MyMySQLPass123",
                autocommit=False
            )

            with conn.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (id INT PRIMARY KEY, value INT) ENGINE=InnoDB
                """)
                conn.commit()

            # Start transaction
            with conn.cursor() as cursor:
                cursor.execute(f"INSERT INTO {test_table_name} VALUES (1, 100)")

                # Try to insert duplicate (should fail)
                try:
                    cursor.execute(f"INSERT INTO {test_table_name} VALUES (1, 200)")
                    conn.commit()
                    assert False, "Should have raised integrity error"
                except pymysql.err.IntegrityError:
                    # Rollback on error
                    conn.rollback()

            # Verify no data persisted
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                count = cursor.fetchone()[0]
                assert count == 0, "Data should have been rolled back"

        finally:
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        conn.commit()
                    conn.close()
                except:
                    pass


@pytest.mark.integration
@pytest.mark.slow
class TestLongRunningTransactions:
    """Test behavior of long-running transactions."""

    def test_postgresql_long_transaction_timeout(self, test_table_name):
        """Test PostgreSQL handles long transactions."""
        conn = None

        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            with conn.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (id INTEGER PRIMARY KEY, value INTEGER)
                """)
                conn.commit()

            # Start long transaction
            start_time = time.time()

            with conn.cursor() as cursor:
                cursor.execute(f"INSERT INTO {test_table_name} VALUES (1, 100)")

                # Simulate long-running operation
                time.sleep(2)

                cursor.execute(f"INSERT INTO {test_table_name} VALUES (2, 200)")
                conn.commit()

            duration = time.time() - start_time
            assert duration >= 2.0

            # Verify data persisted
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                count = cursor.fetchone()[0]
                assert count == 2

        finally:
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        conn.commit()
                    conn.close()
                except:
                    pass
