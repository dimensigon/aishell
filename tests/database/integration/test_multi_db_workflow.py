"""
Integration tests for multi-database workflows.

Tests cross-database operations, data migration, and coordination
across Oracle, PostgreSQL, and MySQL databases.
"""

import pytest
import psycopg2
import pymysql
from typing import Dict, Any, List

try:
    import cx_Oracle
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False


@pytest.mark.integration
class TestCrossDatabaseOperations:
    """Test operations spanning multiple databases."""

    @pytest.fixture
    def all_connections(self):
        """Provide connections to all databases."""
        connections = {}

        # Oracle CDB
        try:
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="free")
            connections["oracle"] = cx_Oracle.connect(
                user="SYS",
                password="MyOraclePass123",
                dsn=dsn,
                mode=cx_Oracle.SYSDBA
            )
        except Exception as e:
            print(f"Oracle connection failed: {e}")

        # PostgreSQL
        try:
            connections["postgres"] = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")

        # MySQL
        try:
            connections["mysql"] = pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="MyMySQLPass123",
                autocommit=False
            )
        except Exception as e:
            print(f"MySQL connection failed: {e}")

        yield connections

        # Cleanup
        for db_name, conn in connections.items():
            try:
                conn.close()
            except:
                pass

    def test_create_table_across_all_databases(self, all_connections, test_table_name):
        """Test creating identical table structure across all databases."""
        table_created = {}

        try:
            # Oracle
            if "oracle" in all_connections:
                cursor = all_connections["oracle"].cursor()
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id NUMBER PRIMARY KEY,
                        name VARCHAR2(100),
                        value NUMBER
                    )
                """)
                all_connections["oracle"].commit()
                table_created["oracle"] = cursor

            # PostgreSQL
            if "postgres" in all_connections:
                cursor = all_connections["postgres"].cursor()
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100),
                        value INTEGER
                    )
                """)
                all_connections["postgres"].commit()
                table_created["postgres"] = cursor

            # MySQL
            if "mysql" in all_connections:
                cursor = all_connections["mysql"].cursor()
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100),
                        value INT
                    ) ENGINE=InnoDB
                """)
                all_connections["mysql"].commit()
                table_created["mysql"] = cursor

            # Verify all tables created
            assert len(table_created) >= 1, "At least one database should be available"

        finally:
            # Cleanup
            for db_name, cursor in table_created.items():
                try:
                    if db_name == "oracle":
                        cursor.execute(f"DROP TABLE {test_table_name}")
                        all_connections[db_name].commit()
                    else:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        all_connections[db_name].commit()
                    cursor.close()
                except:
                    pass

    def test_data_consistency_across_databases(self, all_connections, test_table_name):
        """Test that same data can be inserted and retrieved from all databases."""
        sample_data = {"id": 1, "name": "Test", "value": 100}
        cursors = {}

        try:
            # Create tables and insert data
            if "oracle" in all_connections:
                cursor = all_connections["oracle"].cursor()
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id NUMBER PRIMARY KEY,
                        name VARCHAR2(100),
                        value NUMBER
                    )
                """)
                cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, name, value)
                    VALUES (:id, :name, :value)
                """, sample_data)
                all_connections["oracle"].commit()
                cursors["oracle"] = cursor

            if "postgres" in all_connections:
                cursor = all_connections["postgres"].cursor()
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100),
                        value INTEGER
                    )
                """)
                cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, name, value)
                    VALUES (%(id)s, %(name)s, %(value)s)
                """, sample_data)
                all_connections["postgres"].commit()
                cursors["postgres"] = cursor

            if "mysql" in all_connections:
                cursor = all_connections["mysql"].cursor()
                cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100),
                        value INT
                    ) ENGINE=InnoDB
                """)
                cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, name, value)
                    VALUES (%(id)s, %(name)s, %(value)s)
                """, sample_data)
                all_connections["mysql"].commit()
                cursors["mysql"] = cursor

            # Verify data consistency
            for db_name, cursor in cursors.items():
                cursor.execute(f"SELECT id, name, value FROM {test_table_name} WHERE id = 1")
                row = cursor.fetchone()

                assert row[0] == sample_data["id"]
                assert row[1] == sample_data["name"]
                assert row[2] == sample_data["value"]

        finally:
            # Cleanup
            for db_name, cursor in cursors.items():
                try:
                    if db_name == "oracle":
                        cursor.execute(f"DROP TABLE {test_table_name}")
                    else:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                    all_connections[db_name].commit()
                    cursor.close()
                except:
                    pass


@pytest.mark.integration
@pytest.mark.slow
class TestDataMigrationWorkflows:
    """Test data migration between different databases."""

    def test_migrate_data_postgres_to_mysql(self, test_table_name):
        """Test migrating data from PostgreSQL to MySQL."""
        pg_conn = None
        mysql_conn = None

        try:
            # Connect to PostgreSQL
            pg_conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            # Connect to MySQL
            mysql_conn = pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="MyMySQLPass123",
                autocommit=False
            )

            # Setup source data in PostgreSQL
            with pg_conn.cursor() as pg_cursor:
                pg_cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100),
                        value INTEGER
                    )
                """)

                # Insert test data
                for i in range(10):
                    pg_cursor.execute(f"""
                        INSERT INTO {test_table_name} (id, name, value)
                        VALUES (%s, %s, %s)
                    """, (i, f"Name_{i}", i * 10))

                pg_conn.commit()

            # Create destination table in MySQL
            with mysql_conn.cursor() as mysql_cursor:
                mysql_cursor.execute(f"""
                    CREATE TABLE {test_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100),
                        value INT
                    ) ENGINE=InnoDB
                """)
                mysql_conn.commit()

            # Migrate data
            with pg_conn.cursor() as pg_cursor:
                pg_cursor.execute(f"SELECT id, name, value FROM {test_table_name}")
                rows = pg_cursor.fetchall()

                with mysql_conn.cursor() as mysql_cursor:
                    for row in rows:
                        mysql_cursor.execute(f"""
                            INSERT INTO {test_table_name} (id, name, value)
                            VALUES (%s, %s, %s)
                        """, row)

                    mysql_conn.commit()

            # Verify migration
            with mysql_conn.cursor() as mysql_cursor:
                mysql_cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                count = mysql_cursor.fetchone()[0]
                assert count == 10

        finally:
            # Cleanup
            if pg_conn:
                try:
                    with pg_conn.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        pg_conn.commit()
                    pg_conn.close()
                except:
                    pass

            if mysql_conn:
                try:
                    with mysql_conn.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        mysql_conn.commit()
                    mysql_conn.close()
                except:
                    pass


@pytest.mark.integration
class TestTransactionCoordination:
    """Test coordinating transactions across multiple databases."""

    def test_coordinated_commits(self, test_table_name):
        """Test coordinated commit across PostgreSQL and MySQL."""
        pg_conn = None
        mysql_conn = None

        try:
            pg_conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            mysql_conn = pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="MyMySQLPass123",
                autocommit=False
            )

            # Create tables
            with pg_conn.cursor() as pg_cursor:
                pg_cursor.execute(f"""
                    CREATE TABLE {test_table_name} (id INTEGER PRIMARY KEY, value INTEGER)
                """)
                pg_conn.commit()

            with mysql_conn.cursor() as mysql_cursor:
                mysql_cursor.execute(f"""
                    CREATE TABLE {test_table_name} (id INT PRIMARY KEY, value INT) ENGINE=InnoDB
                """)
                mysql_conn.commit()

            # Start coordinated transaction
            try:
                with pg_conn.cursor() as pg_cursor:
                    pg_cursor.execute(f"""
                        INSERT INTO {test_table_name} (id, value) VALUES (1, 100)
                    """)

                with mysql_conn.cursor() as mysql_cursor:
                    mysql_cursor.execute(f"""
                        INSERT INTO {test_table_name} (id, value) VALUES (1, 100)
                    """)

                # Both commits succeed
                pg_conn.commit()
                mysql_conn.commit()

                # Verify both inserts
                with pg_conn.cursor() as pg_cursor:
                    pg_cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                    assert pg_cursor.fetchone()[0] == 1

                with mysql_conn.cursor() as mysql_cursor:
                    mysql_cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                    assert mysql_cursor.fetchone()[0] == 1

            except Exception as e:
                # Rollback both if any fails
                pg_conn.rollback()
                mysql_conn.rollback()
                raise

        finally:
            # Cleanup
            if pg_conn:
                try:
                    with pg_conn.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        pg_conn.commit()
                    pg_conn.close()
                except:
                    pass

            if mysql_conn:
                try:
                    with mysql_conn.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        mysql_conn.commit()
                    mysql_conn.close()
                except:
                    pass

    def test_coordinated_rollback(self, test_table_name):
        """Test coordinated rollback across databases."""
        pg_conn = None
        mysql_conn = None

        try:
            pg_conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="MyPostgresPass123"
            )

            mysql_conn = pymysql.connect(
                host="localhost",
                port=3307,
                database="mysql",
                user="root",
                password="MyMySQLPass123",
                autocommit=False
            )

            # Create tables
            with pg_conn.cursor() as pg_cursor:
                pg_cursor.execute(f"""
                    CREATE TABLE {test_table_name} (id INTEGER PRIMARY KEY, value INTEGER)
                """)
                pg_conn.commit()

            with mysql_conn.cursor() as mysql_cursor:
                mysql_cursor.execute(f"""
                    CREATE TABLE {test_table_name} (id INT PRIMARY KEY, value INT) ENGINE=InnoDB
                """)
                mysql_conn.commit()

            # Start transaction and insert data
            with pg_conn.cursor() as pg_cursor:
                pg_cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, value) VALUES (1, 100)
                """)

            with mysql_conn.cursor() as mysql_cursor:
                mysql_cursor.execute(f"""
                    INSERT INTO {test_table_name} (id, value) VALUES (1, 100)
                """)

            # Rollback both
            pg_conn.rollback()
            mysql_conn.rollback()

            # Verify no data persisted
            with pg_conn.cursor() as pg_cursor:
                pg_cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                assert pg_cursor.fetchone()[0] == 0

            with mysql_conn.cursor() as mysql_cursor:
                mysql_cursor.execute(f"SELECT COUNT(*) FROM {test_table_name}")
                assert mysql_cursor.fetchone()[0] == 0

        finally:
            # Cleanup
            if pg_conn:
                try:
                    with pg_conn.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        pg_conn.commit()
                    pg_conn.close()
                except:
                    pass

            if mysql_conn:
                try:
                    with mysql_conn.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table_name}")
                        mysql_conn.commit()
                    mysql_conn.close()
                except:
                    pass
