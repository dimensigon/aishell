"""
Unit tests for MySQL database operations.

Tests connection, CRUD operations, transactions, and MySQL-specific features.
"""

import pytest
import pymysql
from pymysql import cursors


@pytest.mark.mysql
class TestMySQLConnection:
    """Test MySQL connection establishment and management."""

    def test_connection_establishment(self, mysql_conn_string):
        """Test successful connection to MySQL."""
        conn = None
        try:
            conn = pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="MyMySQLPass123",
                cursorclass=cursors.DictCursor
            )

            assert conn is not None
            assert conn.open

            # Verify connection works
            with conn.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()["VERSION()"]
                assert version is not None

        finally:
            if conn:
                conn.close()

    def test_connection_with_invalid_credentials(self):
        """Test connection fails with invalid credentials."""
        with pytest.raises(pymysql.err.OperationalError):
            pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="WrongPassword"
            )

    def test_connection_context_manager(self):
        """Test connection using context manager."""
        with pymysql.connect(
            host="localhost",
            port=3307,
            database="mysql",
            user="root",
            password="MyMySQLPass123"
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS value")
                result = cursor.fetchone()[0]
                assert result == 1


@pytest.mark.mysql
class TestMySQLCRUDOperations:
    """Test CRUD operations on MySQL."""

    @pytest.fixture
    def db_connection(self):
        """Provide database connection for tests."""
        conn = pymysql.connect(
            host="localhost",
            port=3307,
            database="mysql",
            user="root",
            password="MyMySQLPass123",
            autocommit=False
        )
        yield conn
        conn.close()

    def test_create_table(self, db_connection, test_table_name):
        """Test CREATE TABLE operation."""
        with db_connection.cursor() as cursor:
            try:
                # Create table
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        name VARCHAR(100) NOT NULL,
                        age INT,
                        email VARCHAR(255)
                    ) ENGINE=InnoDB
                """)
                db_connection.commit()

                # Verify table exists
                cursor.execute(f"""
                    SELECT COUNT(*) as count
                    FROM information_schema.tables
                    WHERE table_schema = 'mysql'
                    AND table_name = '{test_table_name}'
                """)

                result = cursor.fetchone()
                assert result[0] == 1

            finally:
                # Cleanup
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                    db_connection.commit()
                except:
                    pass

    def test_insert_data(self, db_connection, test_table_name, sample_data):
        """Test INSERT operation."""
        with db_connection.cursor() as cursor:
            try:
                # Create table
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100),
                        age INT,
                        email VARCHAR(255)
                    ) ENGINE=InnoDB
                """)

                # Insert data
                cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, name, age, email)
                    VALUES (%(id)s, %(name)s, %(age)s, %(email)s)
                """, sample_data[0])

                db_connection.commit()

                # Verify insert
                cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                count = cursor.fetchone()[0]
                assert count == 1

            finally:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                    db_connection.commit()
                except:
                    pass

    def test_select_data(self, db_connection, test_table_name, sample_data):
        """Test SELECT operation."""
        with db_connection.cursor() as cursor:
            try:
                # Setup
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100),
                        age INT,
                        email VARCHAR(255)
                    ) ENGINE=InnoDB
                """)

                cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, name, age, email)
                    VALUES (%(id)s, %(name)s, %(age)s, %(email)s)
                """, sample_data[0])
                db_connection.commit()

                # Test SELECT
                cursor.execute(f"""
                    SELECT * FROM {test_table_name} WHERE id = %s
                """, (1,))
                row = cursor.fetchone()

                assert row is not None
                assert row[0] == sample_data[0]["id"]
                assert row[1] == sample_data[0]["name"]

            finally:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                    db_connection.commit()
                except:
                    pass

    def test_update_data(self, db_connection, test_table_name, sample_data):
        """Test UPDATE operation."""
        with db_connection.cursor() as cursor:
            try:
                # Setup
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100),
                        age INT,
                        email VARCHAR(255)
                    ) ENGINE=InnoDB
                """)

                cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, name, age, email)
                    VALUES (%(id)s, %(name)s, %(age)s, %(email)s)
                """, sample_data[0])
                db_connection.commit()

                # Test UPDATE
                cursor.execute(f"""
                    UPDATE {test_table_name}
                    SET age = %s
                    WHERE id = %s
                """, (31, 1))
                db_connection.commit()

                # Verify update
                cursor.execute(f"""
                    SELECT age FROM {test_table_name} WHERE id = %s
                """, (1,))
                age = cursor.fetchone()[0]
                assert age == 31

            finally:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                    db_connection.commit()
                except:
                    pass

    def test_delete_data(self, db_connection, test_table_name, sample_data):
        """Test DELETE operation."""
        with db_connection.cursor() as cursor:
            try:
                # Setup
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100),
                        age INT,
                        email VARCHAR(255)
                    ) ENGINE=InnoDB
                """)

                cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, name, age, email)
                    VALUES (%(id)s, %(name)s, %(age)s, %(email)s)
                """, sample_data[0])
                db_connection.commit()

                # Test DELETE
                cursor.execute(f"""
                    DELETE FROM {test_table_name} WHERE id = %s
                """, (1,))
                db_connection.commit()

                # Verify delete
                cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                count = cursor.fetchone()[0]
                assert count == 0

            finally:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                    db_connection.commit()
                except:
                    pass


@pytest.mark.mysql
class TestMySQLTransactions:
    """Test transaction handling in MySQL."""

    @pytest.fixture
    def db_connection(self):
        """Provide database connection for tests."""
        conn = pymysql.connect(
            host="localhost",
            port=3307,
            database="mysql",
            user="root",
            password="MyMySQLPass123",
            autocommit=False
        )
        yield conn
        conn.close()

    def test_commit_transaction(self, db_connection, test_table_name):
        """Test transaction commit."""
        with db_connection.cursor() as cursor:
            try:
                # Setup
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100)
                    ) ENGINE=InnoDB
                """)

                # Insert with commit
                cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, name)
                    VALUES (%s, %s)
                """, (1, "Test"))

                db_connection.commit()

                # Verify data persisted
                cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                count = cursor.fetchone()[0]
                assert count == 1

            finally:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                    db_connection.commit()
                except:
                    pass

    def test_rollback_transaction(self, db_connection, test_table_name):
        """Test transaction rollback."""
        with db_connection.cursor() as cursor:
            try:
                # Setup
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100)
                    ) ENGINE=InnoDB
                """)
                db_connection.commit()

                # Insert without commit
                cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, name)
                    VALUES (%s, %s)
                """, (1, "Test"))

                # Rollback
                db_connection.rollback()

                # Verify data not persisted
                cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                count = cursor.fetchone()[0]
                assert count == 0

            finally:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                    db_connection.commit()
                except:
                    pass

    def test_transaction_isolation(self, test_table_name):
        """Test transaction isolation between connections."""
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

            with conn1.cursor() as cursor1:
                # Setup
                cursor1.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        value INT
                    ) ENGINE=InnoDB
                """)
                conn1.commit()

                # Insert in conn1 without commit
                cursor1.execute(f"""
                    INSERT INTO {test_table_name} (id, value)
                    VALUES (1, 100)
                """)

                # Try to read from conn2
                with conn2.cursor() as cursor2:
                    cursor2.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                    count = cursor2.fetchone()[0]

                    # Should not see uncommitted data
                    assert count == 0

                # Commit in conn1
                conn1.commit()

                # Now conn2 should see the data
                with conn2.cursor() as cursor2:
                    cursor2.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                    count = cursor2.fetchone()[0]
                    assert count == 1

                # Cleanup
                cursor1.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                conn1.commit()

        finally:
            if conn1:
                conn1.close()
            if conn2:
                conn2.close()


@pytest.mark.mysql
class TestMySQLPreparedStatements:
    """Test prepared statements and SQL injection prevention."""

    @pytest.fixture
    def db_connection(self):
        """Provide database connection for tests."""
        conn = pymysql.connect(
            host="localhost",
            port=3307,
            database="mysql",
            user="root",
            password="MyMySQLPass123",
            autocommit=False
        )
        yield conn
        conn.close()

    def test_prepared_statement_with_parameters(self, db_connection, test_table_name):
        """Test prepared statements with bind parameters."""
        with db_connection.cursor() as cursor:
            try:
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100)
                    ) ENGINE=InnoDB
                """)

                # Use parameterized query
                cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, name)
                    VALUES (%s, %s)
                """, (1, "Test"))

                db_connection.commit()

                cursor.execute(f"""
                    SELECT name FROM {test_table_name} WHERE id = %s
                """, (1,))

                name = cursor.fetchone()[0]
                assert name == "Test"

            finally:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                    db_connection.commit()
                except:
                    pass

    def test_sql_injection_prevention(self, db_connection, test_table_name):
        """Test that parameterized queries prevent SQL injection."""
        with db_connection.cursor() as cursor:
            try:
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100)
                    ) ENGINE=InnoDB
                """)

                cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, name)
                    VALUES (%s, %s)
                """, (1, "Test"))
                db_connection.commit()

                # Attempt SQL injection via parameter
                malicious_input = "1 OR 1=1; DROP TABLE users; --"

                cursor.execute(f"""
                    SELECT * FROM {test_table_name} WHERE id = %s
                """, (malicious_input,))

                # Should return no results instead of executing injection
                result = cursor.fetchall()
                assert len(result) == 0

                # Verify table still exists
                cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                count = cursor.fetchone()[0]
                assert count == 1

            finally:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                    db_connection.commit()
                except:
                    pass


@pytest.mark.mysql
class TestMySQLPerformance:
    """Test MySQL performance characteristics."""

    @pytest.fixture
    def db_connection(self):
        """Provide database connection for tests."""
        conn = pymysql.connect(
            host="localhost",
            port=3307,
            database="mysql",
            user="root",
            password="MyMySQLPass123",
            autocommit=False
        )
        yield conn
        conn.close()

    def test_bulk_insert_performance(self, db_connection, test_table_name):
        """Test bulk insert operations."""
        import time

        with db_connection.cursor() as cursor:
            try:
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        value VARCHAR(100)
                    ) ENGINE=InnoDB
                """)

                # Prepare bulk data
                data = [(i, f"Value_{i}") for i in range(100)]

                # Time bulk insert
                start_time = time.time()
                cursor.executemany(
                    f"INSERT INTO {test_table_name} (id, value) VALUES (%s, %s)",
                    data
                )
                db_connection.commit()
                duration = time.time() - start_time

                # Verify all rows inserted
                cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                count = cursor.fetchone()[0]
                assert count == 100

                # Performance assertion
                assert duration < 5.0, f"Bulk insert took {duration:.2f}s, expected <5s"

            finally:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                    db_connection.commit()
                except:
                    pass
