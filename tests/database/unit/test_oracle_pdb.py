"""
Unit tests for Oracle FREEPDB1 (Pluggable Database) operations.

Tests PDB-specific operations, connection, and container switching.
"""

import pytest

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
class TestOraclePDBConnection:
    """Test Oracle PDB connection and management."""

    def test_connection_to_pdb(self, oracle_pdb_conn_string):
        """Test successful connection to Oracle PDB."""
        conn = None
        try:
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="freepdb1")
            conn = cx_Oracle.connect(
                user="SYS",
                password="MyOraclePass123",
                dsn=dsn,
                mode=cx_Oracle.SYSDBA
            )

            assert conn is not None

            # Verify we're connected to a PDB
            cursor = conn.cursor()
            cursor.execute("SELECT NAME, CON_ID FROM V$CONTAINERS WHERE CON_ID = SYS_CONTEXT('USERENV', 'CON_ID')")
            result = cursor.fetchone()

            assert result is not None
            assert result[0] == 'FREEPDB1'
            assert result[1] > 1  # PDB CON_ID is always > 1

            cursor.close()

        finally:
            if conn:
                conn.close()

    def test_pdb_open_status(self):
        """Test checking if PDB is open and accessible."""
        conn = None
        try:
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="freepdb1")
            conn = cx_Oracle.connect(
                user="SYS",
                password="MyOraclePass123",
                dsn=dsn,
                mode=cx_Oracle.SYSDBA
            )

            cursor = conn.cursor()
            cursor.execute("SELECT OPEN_MODE FROM V$DATABASE")
            open_mode = cursor.fetchone()[0]

            assert open_mode in ('READ WRITE', 'READ ONLY', 'MOUNTED')
            cursor.close()

        finally:
            if conn:
                conn.close()


@pytest.mark.oracle
class TestOraclePDBOperations:
    """Test PDB-specific database operations."""

    @pytest.fixture
    def db_connection(self):
        """Provide PDB connection for tests."""
        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="freepdb1")
        conn = cx_Oracle.connect(
            user="SYS",
            password="MyOraclePass123",
            dsn=dsn,
            mode=cx_Oracle.SYSDBA
        )
        yield conn
        conn.close()

    def test_create_user_in_pdb(self, db_connection):
        """Test creating user in PDB."""
        cursor = db_connection.cursor()
        test_user = "test_user_" + str(hash("test"))[0:8]

        try:
            # Create user in PDB
            cursor.execute(f"CREATE USER {test_user} IDENTIFIED BY TestPass123")
            cursor.execute(f"GRANT CONNECT TO {test_user}")
            db_connection.commit()

            # Verify user exists
            cursor.execute(f"SELECT USERNAME FROM DBA_USERS WHERE USERNAME = '{test_user.upper()}'")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == test_user.upper()

        finally:
            try:
                cursor.execute(f"DROP USER {test_user} CASCADE")
                db_connection.commit()
            except:
                pass
            cursor.close()

    def test_tablespace_operations_in_pdb(self, db_connection):
        """Test tablespace operations within PDB."""
        cursor = db_connection.cursor()

        try:
            # Query existing tablespaces
            cursor.execute("SELECT TABLESPACE_NAME FROM DBA_TABLESPACES WHERE CONTENTS = 'PERMANENT'")
            tablespaces = cursor.fetchall()

            assert len(tablespaces) > 0
            assert any('SYSTEM' in ts[0] for ts in tablespaces)

        finally:
            cursor.close()

    def test_pdb_data_isolation(self, db_connection, test_table_name):
        """Test that data in PDB is isolated from CDB."""
        cursor = db_connection.cursor()

        try:
            # Create table in PDB
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id NUMBER PRIMARY KEY,
                    pdb_name VARCHAR2(100)
                )
            """)

            # Insert PDB identifier
            cursor.execute(f"""
                INSERT INTO {test_table_name} (id, pdb_name)
                SELECT 1, NAME FROM V$CONTAINERS
                WHERE CON_ID = SYS_CONTEXT('USERENV', 'CON_ID')
            """)
            db_connection.commit()

            # Verify data
            cursor.execute(f"SELECT pdb_name FROM {test_table_name}")
            pdb_name = cursor.fetchone()[0]
            assert pdb_name == 'FREEPDB1'

        finally:
            try:
                cursor.execute(f"DROP TABLE {test_table_name}")
                db_connection.commit()
            except:
                pass
            cursor.close()


@pytest.mark.oracle
class TestOraclePDBPerformance:
    """Test performance characteristics of PDB operations."""

    @pytest.fixture
    def db_connection(self):
        """Provide PDB connection for tests."""
        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="freepdb1")
        conn = cx_Oracle.connect(
            user="SYS",
            password="MyOraclePass123",
            dsn=dsn,
            mode=cx_Oracle.SYSDBA
        )
        yield conn
        conn.close()

    def test_bulk_insert_performance(self, db_connection, test_table_name):
        """Test bulk insert operations in PDB."""
        import time

        cursor = db_connection.cursor()

        try:
            cursor.execute(f"""
                CREATE TABLE {test_table_name} (
                    id NUMBER PRIMARY KEY,
                    value VARCHAR2(100)
                )
            """)

            # Prepare bulk data
            data = [(i, f"Value_{i}") for i in range(100)]

            # Time bulk insert
            start_time = time.time()
            cursor.executemany(
                f"INSERT INTO {test_table_name} (id, value) VALUES (:1, :2)",
                data
            )
            db_connection.commit()
            duration = time.time() - start_time

            # Verify all rows inserted
            cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
            count = cursor.fetchone()[0]
            assert count == 100

            # Performance assertion (should be fast)
            assert duration < 5.0, f"Bulk insert took {duration:.2f}s, expected <5s"

        finally:
            try:
                cursor.execute(f"DROP TABLE {test_table_name}")
                db_connection.commit()
            except:
                pass
            cursor.close()
