"""
Unit tests for Oracle CDB$ROOT database operations.

Tests connection, CRUD operations, transactions, and error handling
for Oracle Container Database (CDB).
"""

import pytest
from typing import Any, Optional

try:
    import cx_Oracle
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not ORACLE_AVAILABLE,
    reason="cx_Oracle not installed - install with: pip install cx_Oracle"
)


@pytest.mark.oracle
class TestOracleCDBConnection:
    """Test Oracle CDB connection establishment and management."""

    def test_connection_establishment(self, oracle_cdb_conn_string):
        """Test successful connection to Oracle CDB."""
        # Parse connection string
        # oracle+cx_oracle://SYS:MyOraclePass123@localhost:1521/?mode=SYSDBA&service_name=free
        conn = None
        try:
            # Connect with SYSDBA privilege
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="free")
            conn = cx_Oracle.connect(
                user="SYS",
                password="MyOraclePass123",
                dsn=dsn,
                mode=cx_Oracle.SYSDBA
            )

            assert conn is not None
            assert conn.version is not None

            # Verify we're connected to CDB
            cursor = conn.cursor()
            cursor.execute("SELECT CDB FROM V$DATABASE")
            result = cursor.fetchone()
            assert result[0] == 'YES', "Not connected to CDB"
            cursor.close()

        finally:
            if conn:
                conn.close()

    def test_connection_pooling(self, oracle_cdb_conn_string):
        """Test connection pooling works correctly."""
        pool = None
        try:
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="free")

            # Create connection pool
            pool = cx_Oracle.SessionPool(
                user="SYS",
                password="MyOraclePass123",
                dsn=dsn,
                min=2,
                max=5,
                increment=1,
                mode=cx_Oracle.SYSDBA
            )

            assert pool is not None

            # Acquire connection from pool
            conn1 = pool.acquire()
            conn2 = pool.acquire()

            assert conn1 is not None
            assert conn2 is not None
            assert conn1 != conn2

            # Release connections
            pool.release(conn1)
            pool.release(conn2)

        finally:
            if pool:
                pool.close()

    def test_connection_timeout(self, oracle_cdb_conn_string):
        """Test connection timeout handling."""
        with pytest.raises(cx_Oracle.Error):
            # Attempt connection to invalid host
            dsn = cx_Oracle.makedsn("invalid-host", 1521, service_name="free")
            cx_Oracle.connect(
                user="SYS",
                password="MyOraclePass123",
                dsn=dsn,
                mode=cx_Oracle.SYSDBA
            )

    def test_connection_with_invalid_credentials(self):
        """Test connection fails with invalid credentials."""
        with pytest.raises(cx_Oracle.Error):
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="free")
            cx_Oracle.connect(
                user="SYS",
                password="WrongPassword",
                dsn=dsn,
                mode=cx_Oracle.SYSDBA
            )


@pytest.mark.oracle
class TestOracleCDBCRUDOperations:
    """Test CRUD operations on Oracle CDB."""

    @pytest.fixture
    def db_connection(self):
        """Provide database connection for tests."""
        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="free")
        conn = cx_Oracle.connect(
            user="SYS",
            password="MyOraclePass123",
            dsn=dsn,
            mode=cx_Oracle.SYSDBA
        )
        yield conn
        conn.close()

    def test_create_table(self, db_connection, test_table_name):
        """Test CREATE TABLE operation."""
        cursor = db_connection.cursor()

        try:
            # Create table
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id NUMBER PRIMARY KEY,
                    name VARCHAR2(100) NOT NULL,
                    age NUMBER,
                    email VARCHAR2(255)
                )
            """)
            db_connection.commit()

            # Verify table exists
            cursor.execute("""
                SELECT COUNT(*) FROM user_tables
                WHERE table_name = :table_name
            """, {"table_name": test_table_name.upper()})

            count = cursor.fetchone()[0]
            assert count == 1

        finally:
            # Cleanup
            try:
                cursor.execute(f"DROP TABLE {test_table_name}")
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_insert_data(self, db_connection, test_table_name, sample_data):
        """Test INSERT operation."""
        cursor = db_connection.cursor()

        try:
            # Create table
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id NUMBER PRIMARY KEY,
                    name VARCHAR2(100),
                    age NUMBER,
                    email VARCHAR2(255)
                )
            """)

            # Insert data
            cursor.execute(f"""
                INSERT INTO {test_table_name} (id, name, age, email)
                VALUES (:id, :name, :age, :email)
            """, sample_data[0])

            db_connection.commit()

            # Verify insert
            cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
            count = cursor.fetchone()[0]
            assert count == 1

        finally:
            try:
                cursor.execute(f"DROP TABLE {test_table_name}")
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_select_data(self, db_connection, test_table_name, sample_data):
        """Test SELECT operation."""
        cursor = db_connection.cursor()

        try:
            # Setup
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id NUMBER PRIMARY KEY,
                    name VARCHAR2(100),
                    age NUMBER,
                    email VARCHAR2(255)
                )
            """)

            cursor.execute(f"""
                INSERT INTO {test_table_name} (id, name, age, email)
                VALUES (:id, :name, :age, :email)
            """, sample_data[0])
            db_connection.commit()

            # Test SELECT
            cursor.execute(f"SELECT * FROM {test_table_name} WHERE id = :id", {"id": 1})
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == sample_data[0]["id"]
            assert row[1] == sample_data[0]["name"]

        finally:
            try:
                cursor.execute(f"DROP TABLE {test_table_name}")
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_update_data(self, db_connection, test_table_name, sample_data):
        """Test UPDATE operation."""
        cursor = db_connection.cursor()

        try:
            # Setup
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id NUMBER PRIMARY KEY,
                    name VARCHAR2(100),
                    age NUMBER,
                    email VARCHAR2(255)
                )
            """)

            cursor.execute(f"""
                INSERT INTO {test_table_name} (id, name, age, email)
                VALUES (:id, :name, :age, :email)
            """, sample_data[0])
            db_connection.commit()

            # Test UPDATE
            cursor.execute(f"""
                UPDATE {test_table_name}
                SET age = :age
                WHERE id = :id
            """, {"age": 31, "id": 1})
            db_connection.commit()

            # Verify update
            cursor.execute(f"SELECT age FROM {test_table_name} WHERE id = :id", {"id": 1})
            age = cursor.fetchone()[0]
            assert age == 31

        finally:
            try:
                cursor.execute(f"DROP TABLE {test_table_name}")
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_delete_data(self, db_connection, test_table_name, sample_data):
        """Test DELETE operation."""
        cursor = db_connection.cursor()

        try:
            # Setup
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id NUMBER PRIMARY KEY,
                    name VARCHAR2(100),
                    age NUMBER,
                    email VARCHAR2(255)
                )
            """)

            cursor.execute(f"""
                INSERT INTO {test_table_name} (id, name, age, email)
                VALUES (:id, :name, :age, :email)
            """, sample_data[0])
            db_connection.commit()

            # Test DELETE
            cursor.execute(f"DELETE FROM {test_table_name} WHERE id = :id", {"id": 1})
            db_connection.commit()

            # Verify delete
            cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
            count = cursor.fetchone()[0]
            assert count == 0

        finally:
            try:
                cursor.execute(f"DROP TABLE {test_table_name}")
                db_connection.commit()
            except:
                pass
            cursor.close()


@pytest.mark.oracle
class TestOracleCDBTransactions:
    """Test transaction handling in Oracle CDB."""

    @pytest.fixture
    def db_connection(self):
        """Provide database connection for tests."""
        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="free")
        conn = cx_Oracle.connect(
            user="SYS",
            password="MyOraclePass123",
            dsn=dsn,
            mode=cx_Oracle.SYSDBA
        )
        yield conn
        conn.close()

    def test_commit_transaction(self, db_connection, test_table_name, sample_data):
        """Test transaction commit."""
        cursor = db_connection.cursor()

        try:
            # Setup
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id NUMBER PRIMARY KEY,
                    name VARCHAR2(100)
                )
            """)

            # Insert with commit
            cursor.execute(f"""
                INSERT INTO {test_table_name} (id, name)
                VALUES (:id, :name)
            """, {"id": 1, "name": "Test"})

            db_connection.commit()

            # Verify data persisted
            cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
            count = cursor.fetchone()[0]
            assert count == 1

        finally:
            try:
                cursor.execute(f"DROP TABLE {test_table_name}")
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_rollback_transaction(self, db_connection, test_table_name):
        """Test transaction rollback."""
        cursor = db_connection.cursor()

        try:
            # Setup
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id NUMBER PRIMARY KEY,
                    name VARCHAR2(100)
                )
            """)
            db_connection.commit()

            # Insert without commit
            cursor.execute(f"""
                INSERT INTO {test_table_name} (id, name)
                VALUES (:id, :name)
            """, {"id": 1, "name": "Test"})

            # Rollback
            db_connection.rollback()

            # Verify data not persisted
            cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
            count = cursor.fetchone()[0]
            assert count == 0

        finally:
            try:
                cursor.execute(f"DROP TABLE {test_table_name}")
                db_connection.commit()
            except:
                pass
            cursor.close()


@pytest.mark.oracle
class TestOracleCDBPreparedStatements:
    """Test prepared statements and SQL injection prevention."""

    @pytest.fixture
    def db_connection(self):
        """Provide database connection for tests."""
        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="free")
        conn = cx_Oracle.connect(
            user="SYS",
            password="MyOraclePass123",
            dsn=dsn,
            mode=cx_Oracle.SYSDBA
        )
        yield conn
        conn.close()

    def test_prepared_statement_with_parameters(self, db_connection, test_table_name):
        """Test prepared statements with bind parameters."""
        cursor = db_connection.cursor()

        try:
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id NUMBER PRIMARY KEY,
                    name VARCHAR2(100)
                )
            """)

            # Use bind parameters
            cursor.execute(f"""
                INSERT INTO {test_table_name} (id, name)
                VALUES (:id, :name)
            """, {"id": 1, "name": "Test"})

            db_connection.commit()

            cursor.execute(f"""
                SELECT name FROM {test_table_name} WHERE id = :id
            """, {"id": 1})

            name = cursor.fetchone()[0]
            assert name == "Test"

        finally:
            try:
                cursor.execute(f"DROP TABLE {test_table_name}")
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_sql_injection_prevention(self, db_connection, test_table_name):
        """Test that bind parameters prevent SQL injection."""
        cursor = db_connection.cursor()

        try:
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id NUMBER PRIMARY KEY,
                    name VARCHAR2(100)
                )
            """)

            cursor.execute(f"""
                INSERT INTO {test_table_name} (id, name)
                VALUES (:id, :name)
            """, {"id": 1, "name": "Test"})
            db_connection.commit()

            # Attempt SQL injection via bind parameter
            malicious_input = "1; DROP TABLE {test_table_name}; --"

            cursor.execute(f"""
                SELECT * FROM {test_table_name} WHERE id = :id
            """, {"id": malicious_input})

            # Should return no results (type mismatch) instead of executing injection
            result = cursor.fetchall()

            # Verify table still exists
            cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
            count = cursor.fetchone()[0]
            assert count == 1

        finally:
            try:
                cursor.execute(f"DROP TABLE {test_table_name}")
                db_connection.commit()
            except:
                pass
            cursor.close()
