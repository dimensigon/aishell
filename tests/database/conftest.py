"""
Pytest configuration for database tests.

Provides fixtures and shared test utilities for database testing.
"""

import pytest
import os
import asyncio
from typing import Dict, Any, Generator
from contextlib import contextmanager


# Database connection strings from environment
ORACLE_CDB_CONN = "oracle+cx_oracle://SYS:MyOraclePass123@localhost:1521/?mode=SYSDBA&service_name=free"
ORACLE_PDB_CONN = "oracle+cx_oracle://SYS:MyOraclePass123@localhost:1521/?mode=SYSDBA&service_name=freepdb1"
POSTGRES_CONN = "postgresql://postgres:MyPostgresPass123@localhost:5432/postgres"
MYSQL_CONN = "mysql+pymysql://root:MyMySQLPass123@localhost:3307/mysql"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def oracle_cdb_conn_string():
    """Oracle CDB$ROOT connection string."""
    return ORACLE_CDB_CONN


@pytest.fixture(scope="session")
def oracle_pdb_conn_string():
    """Oracle FREEPDB1 connection string."""
    return ORACLE_PDB_CONN


@pytest.fixture(scope="session")
def postgres_conn_string():
    """PostgreSQL connection string."""
    return POSTGRES_CONN


@pytest.fixture(scope="session")
def mysql_conn_string():
    """MySQL connection string."""
    return MYSQL_CONN


@pytest.fixture
def test_table_name():
    """Generate unique test table name."""
    import uuid
    return f"test_table_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def sample_data():
    """Sample test data for CRUD operations."""
    return [
        {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "age": 35, "email": "charlie@example.com"},
    ]


@pytest.fixture
def create_table_sql():
    """SQL template for creating test tables."""
    def _create_sql(table_name: str, db_type: str = "postgres") -> str:
        if db_type in ("postgres", "mysql"):
            return f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                age INTEGER,
                email VARCHAR(255)
            )
            """
        elif db_type == "oracle":
            return f"""
            CREATE TABLE {table_name} (
                id NUMBER PRIMARY KEY,
                name VARCHAR2(100) NOT NULL,
                age NUMBER,
                email VARCHAR2(255)
            )
            """
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    return _create_sql


@pytest.fixture
def insert_data_sql():
    """SQL template for inserting test data."""
    def _insert_sql(table_name: str, data: Dict[str, Any], db_type: str = "postgres") -> str:
        columns = ", ".join(data.keys())

        if db_type == "postgres":
            placeholders = ", ".join([f"%({k})s" for k in data.keys()])
        elif db_type == "mysql":
            placeholders = ", ".join([f"%({k})s" for k in data.keys()])
        elif db_type == "oracle":
            placeholders = ", ".join([f":{k}" for k in data.keys()])
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        return f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    return _insert_sql


@pytest.fixture
def cleanup_table():
    """Fixture to cleanup test tables after tests."""
    tables_to_cleanup = []

    def _register_table(conn, table_name: str):
        """Register a table for cleanup."""
        tables_to_cleanup.append((conn, table_name))

    yield _register_table

    # Cleanup after test
    for conn, table_name in tables_to_cleanup:
        try:
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Warning: Failed to cleanup table {table_name}: {e}")


@pytest.fixture
def connection_retry_config():
    """Configuration for connection retry logic."""
    return {
        "max_retries": 3,
        "retry_delay": 0.5,
        "backoff_factor": 2,
        "timeout": 10
    }


@pytest.fixture
def pool_config():
    """Default connection pool configuration."""
    return {
        "min_connections": 2,
        "max_connections": 10,
        "acquire_timeout": 30.0,
        "idle_timeout": 300.0,
        "max_connection_age": 3600.0
    }


@contextmanager
def assert_execution_time(max_seconds: float):
    """Context manager to assert code executes within time limit."""
    import time
    start = time.time()
    yield
    duration = time.time() - start
    assert duration < max_seconds, f"Execution took {duration:.2f}s, expected <{max_seconds}s"


@pytest.fixture
def assert_fast():
    """Fixture for asserting fast execution."""
    return assert_execution_time


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "oracle: tests requiring Oracle database"
    )
    config.addinivalue_line(
        "markers", "postgres: tests requiring PostgreSQL database"
    )
    config.addinivalue_line(
        "markers", "mysql: tests requiring MySQL database"
    )
    config.addinivalue_line(
        "markers", "slow: slow running tests"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests"
    )
    config.addinivalue_line(
        "markers", "async_test: asynchronous tests"
    )
