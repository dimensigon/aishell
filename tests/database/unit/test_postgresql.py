"""
Unit tests for PostgreSQL database operations.

Tests connection, CRUD operations, transactions, and PostgreSQL-specific features.
"""

import pytest
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


@pytest.mark.postgres
class TestPostgreSQLConnection:
    """Test PostgreSQL connection establishment and management."""

    def test_connection_establishment(self, postgres_conn_string):
        """Test successful connection to PostgreSQL."""
        conn = None
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            assert conn is not None
            assert not conn.closed

            # Verify connection works
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            assert "PostgreSQL" in version
            cursor.close()

        finally:
            if conn:
                conn.close()

    def test_connection_pooling(self):
        """Test connection pooling works correctly."""
        connection_pool = None
        try:
            # Create connection pool
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=2,
                maxconn=5,
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            assert connection_pool is not None

            # Get connections from pool
            conn1 = connection_pool.getconn()
            conn2 = connection_pool.getconn()

            assert conn1 is not None
            assert conn2 is not None
            assert conn1 != conn2

            # Return connections to pool
            connection_pool.putconn(conn1)
            connection_pool.putconn(conn2)

        finally:
            if connection_pool:
                connection_pool.closeall()

    def test_connection_with_invalid_credentials(self):
        """Test connection fails with invalid credentials."""
        with pytest.raises(psycopg2.OperationalError):
            psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="WrongPassword"
            )

    def test_connection_context_manager(self):
        """Test connection using context manager."""
        with psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="MyPostgresPass123"
        ) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()[0]
            assert result == 1
            cursor.close()


@pytest.mark.postgres
class TestPostgreSQLCRUDOperations:
    """Test CRUD operations on PostgreSQL."""

    @pytest.fixture
    def db_connection(self):
        """Provide database connection for tests."""
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="MyPostgresPass123"
        )
        yield conn
        conn.close()

    def test_create_table(self, db_connection, test_table_name):
        """Test CREATE TABLE operation."""
        cursor = db_connection.cursor()

        try:
            # Create table
            cursor.execute(sql.SQL("""
                CREATE TABLE {} (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    age INTEGER,
                    email VARCHAR(255)
                )
            """).format(sql.Identifier(test_table_name)))
            db_connection.commit()

            # Verify table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                )
            """, (test_table_name,))

            exists = cursor.fetchone()[0]
            assert exists is True

        finally:
            # Cleanup
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                    sql.Identifier(test_table_name)
                ))
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_insert_data(self, db_connection, test_table_name, sample_data):
        """Test INSERT operation."""
        cursor = db_connection.cursor()

        try:
            # Create table
            cursor.execute(sql.SQL("""
                CREATE TABLE {} (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    age INTEGER,
                    email VARCHAR(255)
                )
            """).format(sql.Identifier(test_table_name)))

            # Insert data
            cursor.execute(sql.SQL("""
                INSERT INTO {} (id, name, age, email)
                VALUES (%(id)s, %(name)s, %(age)s, %(email)s)
            """).format(sql.Identifier(test_table_name)), sample_data[0])

            db_connection.commit()

            # Verify insert
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(test_table_name)
            ))
            count = cursor.fetchone()[0]
            assert count == 1

        finally:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                    sql.Identifier(test_table_name)
                ))
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_select_data(self, db_connection, test_table_name, sample_data):
        """Test SELECT operation."""
        cursor = db_connection.cursor()

        try:
            # Setup
            cursor.execute(sql.SQL("""
                CREATE TABLE {} (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    age INTEGER,
                    email VARCHAR(255)
                )
            """).format(sql.Identifier(test_table_name)))

            cursor.execute(sql.SQL("""
                INSERT INTO {} (id, name, age, email)
                VALUES (%(id)s, %(name)s, %(age)s, %(email)s)
            """).format(sql.Identifier(test_table_name)), sample_data[0])
            db_connection.commit()

            # Test SELECT
            cursor.execute(sql.SQL("""
                SELECT * FROM {} WHERE id = %s
            """).format(sql.Identifier(test_table_name)), (1,))
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == sample_data[0]["id"]
            assert row[1] == sample_data[0]["name"]

        finally:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                    sql.Identifier(test_table_name)
                ))
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_update_data(self, db_connection, test_table_name, sample_data):
        """Test UPDATE operation."""
        cursor = db_connection.cursor()

        try:
            # Setup
            cursor.execute(sql.SQL("""
                CREATE TABLE {} (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    age INTEGER,
                    email VARCHAR(255)
                )
            """).format(sql.Identifier(test_table_name)))

            cursor.execute(sql.SQL("""
                INSERT INTO {} (id, name, age, email)
                VALUES (%(id)s, %(name)s, %(age)s, %(email)s)
            """).format(sql.Identifier(test_table_name)), sample_data[0])
            db_connection.commit()

            # Test UPDATE
            cursor.execute(sql.SQL("""
                UPDATE {} SET age = %s WHERE id = %s
            """).format(sql.Identifier(test_table_name)), (31, 1))
            db_connection.commit()

            # Verify update
            cursor.execute(sql.SQL("""
                SELECT age FROM {} WHERE id = %s
            """).format(sql.Identifier(test_table_name)), (1,))
            age = cursor.fetchone()[0]
            assert age == 31

        finally:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                    sql.Identifier(test_table_name)
                ))
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_delete_data(self, db_connection, test_table_name, sample_data):
        """Test DELETE operation."""
        cursor = db_connection.cursor()

        try:
            # Setup
            cursor.execute(sql.SQL("""
                CREATE TABLE {} (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    age INTEGER,
                    email VARCHAR(255)
                )
            """).format(sql.Identifier(test_table_name)))

            cursor.execute(sql.SQL("""
                INSERT INTO {} (id, name, age, email)
                VALUES (%(id)s, %(name)s, %(age)s, %(email)s)
            """).format(sql.Identifier(test_table_name)), sample_data[0])
            db_connection.commit()

            # Test DELETE
            cursor.execute(sql.SQL("""
                DELETE FROM {} WHERE id = %s
            """).format(sql.Identifier(test_table_name)), (1,))
            db_connection.commit()

            # Verify delete
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(test_table_name)
            ))
            count = cursor.fetchone()[0]
            assert count == 0

        finally:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                    sql.Identifier(test_table_name)
                ))
                db_connection.commit()
            except:
                pass
            cursor.close()


@pytest.mark.postgres
class TestPostgreSQLTransactions:
    """Test transaction handling in PostgreSQL."""

    @pytest.fixture
    def db_connection(self):
        """Provide database connection for tests."""
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="MyPostgresPass123"
        )
        yield conn
        conn.close()

    def test_commit_transaction(self, db_connection, test_table_name):
        """Test transaction commit."""
        cursor = db_connection.cursor()

        try:
            # Setup
            cursor.execute(sql.SQL("""
                CREATE TABLE {} (id INTEGER PRIMARY KEY, name VARCHAR(100))
            """).format(sql.Identifier(test_table_name)))

            # Insert with commit
            cursor.execute(sql.SQL("""
                INSERT INTO {} (id, name) VALUES (%s, %s)
            """).format(sql.Identifier(test_table_name)), (1, "Test"))

            db_connection.commit()

            # Verify data persisted
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(test_table_name)
            ))
            count = cursor.fetchone()[0]
            assert count == 1

        finally:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                    sql.Identifier(test_table_name)
                ))
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_rollback_transaction(self, db_connection, test_table_name):
        """Test transaction rollback."""
        cursor = db_connection.cursor()

        try:
            # Setup
            cursor.execute(sql.SQL("""
                CREATE TABLE {} (id INTEGER PRIMARY KEY, name VARCHAR(100))
            """).format(sql.Identifier(test_table_name)))
            db_connection.commit()

            # Insert without commit
            cursor.execute(sql.SQL("""
                INSERT INTO {} (id, name) VALUES (%s, %s)
            """).format(sql.Identifier(test_table_name)), (1, "Test"))

            # Rollback
            db_connection.rollback()

            # Verify data not persisted
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(test_table_name)
            ))
            count = cursor.fetchone()[0]
            assert count == 0

        finally:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                    sql.Identifier(test_table_name)
                ))
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_isolation_levels(self, db_connection):
        """Test different transaction isolation levels."""
        # Test read committed (default)
        assert db_connection.isolation_level == psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED

        # Change isolation level
        db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
        assert db_connection.isolation_level == psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE


@pytest.mark.postgres
class TestPostgreSQLPreparedStatements:
    """Test prepared statements and SQL injection prevention."""

    @pytest.fixture
    def db_connection(self):
        """Provide database connection for tests."""
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="MyPostgresPass123"
        )
        yield conn
        conn.close()

    def test_prepared_statement_with_parameters(self, db_connection, test_table_name):
        """Test prepared statements with bind parameters."""
        cursor = db_connection.cursor()

        try:
            cursor.execute(sql.SQL("""
                CREATE TABLE {} (id INTEGER PRIMARY KEY, name VARCHAR(100))
            """).format(sql.Identifier(test_table_name)))

            # Use parameterized query
            cursor.execute(sql.SQL("""
                INSERT INTO {} (id, name) VALUES (%s, %s)
            """).format(sql.Identifier(test_table_name)), (1, "Test"))

            db_connection.commit()

            cursor.execute(sql.SQL("""
                SELECT name FROM {} WHERE id = %s
            """).format(sql.Identifier(test_table_name)), (1,))

            name = cursor.fetchone()[0]
            assert name == "Test"

        finally:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                    sql.Identifier(test_table_name)
                ))
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_sql_injection_prevention(self, db_connection, test_table_name):
        """Test that parameterized queries prevent SQL injection."""
        cursor = db_connection.cursor()

        try:
            cursor.execute(sql.SQL("""
                CREATE TABLE {} (id INTEGER PRIMARY KEY, name VARCHAR(100))
            """).format(sql.Identifier(test_table_name)))

            cursor.execute(sql.SQL("""
                INSERT INTO {} (id, name) VALUES (%s, %s)
            """).format(sql.Identifier(test_table_name)), (1, "Test"))
            db_connection.commit()

            # Attempt SQL injection via parameter
            malicious_input = "1 OR 1=1; DROP TABLE users; --"

            cursor.execute(sql.SQL("""
                SELECT * FROM {} WHERE id = %s
            """).format(sql.Identifier(test_table_name)), (malicious_input,))

            # Should return no results (type mismatch) instead of executing injection
            result = cursor.fetchall()
            assert len(result) == 0

            # Verify table still exists
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(test_table_name)
            ))
            count = cursor.fetchone()[0]
            assert count == 1

        finally:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                    sql.Identifier(test_table_name)
                ))
                db_connection.commit()
            except:
                pass
            cursor.close()


@pytest.mark.postgres
class TestPostgreSQLAdvancedFeatures:
    """Test PostgreSQL-specific advanced features."""

    @pytest.fixture
    def db_connection(self):
        """Provide database connection for tests."""
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="MyPostgresPass123"
        )
        yield conn
        conn.close()

    def test_json_data_type(self, db_connection, test_table_name):
        """Test PostgreSQL JSON data type support."""
        import json

        cursor = db_connection.cursor()

        try:
            cursor.execute(sql.SQL("""
                CREATE TABLE {} (
                    id INTEGER PRIMARY KEY,
                    data JSONB
                )
            """).format(sql.Identifier(test_table_name)))

            test_data = {"name": "Test", "value": 123, "tags": ["a", "b"]}

            cursor.execute(sql.SQL("""
                INSERT INTO {} (id, data) VALUES (%s, %s)
            """).format(sql.Identifier(test_table_name)),
            (1, json.dumps(test_data)))

            db_connection.commit()

            cursor.execute(sql.SQL("""
                SELECT data FROM {} WHERE id = %s
            """).format(sql.Identifier(test_table_name)), (1,))

            result = cursor.fetchone()[0]
            assert result["name"] == "Test"
            assert result["value"] == 123

        finally:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                    sql.Identifier(test_table_name)
                ))
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_array_data_type(self, db_connection, test_table_name):
        """Test PostgreSQL array data type."""
        cursor = db_connection.cursor()

        try:
            cursor.execute(sql.SQL("""
                CREATE TABLE {} (
                    id INTEGER PRIMARY KEY,
                    tags TEXT[]
                )
            """).format(sql.Identifier(test_table_name)))

            cursor.execute(sql.SQL("""
                INSERT INTO {} (id, tags) VALUES (%s, %s)
            """).format(sql.Identifier(test_table_name)),
            (1, ["tag1", "tag2", "tag3"]))

            db_connection.commit()

            cursor.execute(sql.SQL("""
                SELECT tags FROM {} WHERE id = %s
            """).format(sql.Identifier(test_table_name)), (1,))

            tags = cursor.fetchone()[0]
            assert len(tags) == 3
            assert "tag1" in tags

        finally:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(
                    sql.Identifier(test_table_name)
                ))
                db_connection.commit()
            except:
                pass
            cursor.close()
