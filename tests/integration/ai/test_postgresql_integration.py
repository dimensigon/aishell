"""
Integration Tests for PostgreSQL MCP Client

Tests end-to-end scenarios with REAL PostgreSQL database.
Connection: postgresql://postgres:MyPostgresPass123@localhost:5432/postgres

These tests require:
- PostgreSQL server running on localhost:5432
- Database 'postgres' accessible
- User 'postgres' with password 'MyPostgresPass123'
"""

import pytest
import asyncio
import yaml
import os
from pathlib import Path
from typing import Dict, Any

from src.mcp_clients.postgresql_client import PostgreSQLClient
from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended
from src.mcp_clients.base import ConnectionConfig, MCPClientError, ConnectionState


# Load test database configuration

@pytest.fixture
def test_db_config():
    """Load test database configuration from YAML"""
    config_path = Path(__file__).parent.parent / 'config' / 'test_databases.yaml'

    if not config_path.exists():
        pytest.skip(f"Test config not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config['databases']['postgres']


@pytest.fixture
def postgres_connection_config(test_db_config):
    """Create PostgreSQL connection config from test config"""
    conn = test_db_config['connection']
    return ConnectionConfig(
        host=conn['host'],
        port=conn['port'],
        database=conn['database'],
        username=conn['user'],
        password=conn['password']
    )


@pytest.fixture
async def connected_client(postgres_connection_config):
    """Create and connect PostgreSQL client"""
    client = PostgreSQLClient()

    try:
        await client.connect(postgres_connection_config)
        yield client
    except Exception as e:
        pytest.skip(f"Cannot connect to PostgreSQL: {e}")
    finally:
        if client.is_connected:
            await client.disconnect()


@pytest.fixture
async def extended_client():
    """Create extended PostgreSQL client"""
    client = PostgreSQLClientExtended(
        host='localhost',
        port=5432,
        database='postgres',
        user='postgres',
        password='MyPostgresPass123',
        timeout=30.0,
        connect_timeout=10.0,
        query_timeout=60.0,
        auto_reconnect=True
    )

    try:
        await client.connect()
        yield client
    except Exception as e:
        pytest.skip(f"Cannot connect to PostgreSQL: {e}")
    finally:
        if client.is_connected:
            await client.disconnect()


# Basic Connectivity Tests

class TestPostgreSQLBasicConnectivity:
    """Test basic connection functionality with real database"""

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, postgres_connection_config):
        """Test basic connect and disconnect"""
        client = PostgreSQLClient()

        # Connect
        result = await client.connect(postgres_connection_config)
        assert result is True
        assert client.state == ConnectionState.CONNECTED
        assert client.is_connected is True

        # Disconnect
        result = await client.disconnect()
        assert result is True
        assert client.state == ConnectionState.CLOSED
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_with_connection_string(self):
        """Test connection using connection string"""
        client = PostgreSQLClient()

        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        result = await client.connect(config)
        assert result is True

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_connect_invalid_credentials(self):
        """Test connection with invalid credentials"""
        client = PostgreSQLClient()

        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='invalid_user',
            password='wrong_password'
        )

        with pytest.raises(MCPClientError):
            await client.connect(config)

        assert client.state == ConnectionState.ERROR

    @pytest.mark.asyncio
    async def test_connect_invalid_database(self):
        """Test connection to non-existent database"""
        client = PostgreSQLClient()

        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='nonexistent_db_12345',
            username='postgres',
            password='MyPostgresPass123'
        )

        with pytest.raises(MCPClientError):
            await client.connect(config)

    @pytest.mark.asyncio
    async def test_multiple_connections(self, postgres_connection_config):
        """Test multiple sequential connections"""
        client = PostgreSQLClient()

        # First connection
        await client.connect(postgres_connection_config)
        await client.disconnect()

        # Second connection
        await client.connect(postgres_connection_config)
        assert client.is_connected is True
        await client.disconnect()


# Query Execution Tests

class TestPostgreSQLQueryExecution:
    """Test query execution with real database"""

    @pytest.mark.asyncio
    async def test_simple_select(self, connected_client, test_db_config):
        """Test simple SELECT query"""
        query = test_db_config['test_queries'][0]  # "SELECT 1"
        result = await connected_client.execute_query(query)

        assert result.columns == ['?column?']
        assert len(result.rows) == 1
        assert result.rows[0][0] == 1

    @pytest.mark.asyncio
    async def test_version_query(self, connected_client, test_db_config):
        """Test PostgreSQL version query"""
        query = test_db_config['test_queries'][1]  # "SELECT version()"
        result = await connected_client.execute_query(query)

        assert len(result.rows) == 1
        version_string = result.rows[0][0]
        assert 'PostgreSQL' in version_string

    @pytest.mark.asyncio
    async def test_current_database(self, connected_client, test_db_config):
        """Test current database query"""
        query = test_db_config['test_queries'][2]  # "SELECT current_database()"
        result = await connected_client.execute_query(query)

        assert len(result.rows) == 1
        assert result.rows[0][0] == 'postgres'

    @pytest.mark.asyncio
    async def test_create_and_query_table(self, connected_client):
        """Test creating table and querying it"""
        # Create table
        create_sql = """
        CREATE TEMPORARY TABLE test_users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        await connected_client.execute_ddl(create_sql)

        # Insert data
        insert_sql = """
        INSERT INTO test_users (name, email)
        VALUES (%(name)s, %(email)s)
        """
        await connected_client.execute_query(insert_sql, {'name': 'John Doe', 'email': 'john@example.com'})
        await connected_client.execute_query(insert_sql, {'name': 'Jane Smith', 'email': 'jane@example.com'})

        # Query data
        select_sql = "SELECT id, name, email FROM test_users ORDER BY id"
        result = await connected_client.execute_query(select_sql)

        assert len(result.rows) == 2
        assert result.rows[0][1] == 'John Doe'
        assert result.rows[1][1] == 'Jane Smith'

    @pytest.mark.asyncio
    async def test_parameterized_query(self, connected_client):
        """Test parameterized queries"""
        # Create temporary table
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_params (
                id SERIAL PRIMARY KEY,
                value INTEGER
            )
        """)

        # Insert with parameters
        insert_sql = "INSERT INTO test_params (value) VALUES (%(value)s)"
        await connected_client.execute_query(insert_sql, {'value': 42})

        # Select with parameters
        select_sql = "SELECT value FROM test_params WHERE value = %(value)s"
        result = await connected_client.execute_query(select_sql, {'value': 42})

        assert len(result.rows) == 1
        assert result.rows[0][0] == 42

    @pytest.mark.asyncio
    async def test_update_query(self, connected_client):
        """Test UPDATE query"""
        # Create and populate table
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_update (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100)
            )
        """)
        await connected_client.execute_query("INSERT INTO test_update (name) VALUES ('original')")

        # Update
        update_sql = "UPDATE test_update SET name = %(name)s WHERE id = 1"
        result = await connected_client.execute_query(update_sql, {'name': 'updated'})

        assert result.rowcount == 1

        # Verify update
        select_sql = "SELECT name FROM test_update WHERE id = 1"
        result = await connected_client.execute_query(select_sql)
        assert result.rows[0][0] == 'updated'

    @pytest.mark.asyncio
    async def test_delete_query(self, connected_client):
        """Test DELETE query"""
        # Create and populate table
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_delete (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100)
            )
        """)
        await connected_client.execute_query("INSERT INTO test_delete (name) VALUES ('test1')")
        await connected_client.execute_query("INSERT INTO test_delete (name) VALUES ('test2')")

        # Delete
        delete_sql = "DELETE FROM test_delete WHERE name = %(name)s"
        result = await connected_client.execute_query(delete_sql, {'name': 'test1'})

        assert result.rowcount == 1

        # Verify deletion
        select_sql = "SELECT COUNT(*) FROM test_delete"
        result = await connected_client.execute_query(select_sql)
        assert result.rows[0][0] == 1


# DDL and Schema Tests

class TestPostgreSQLDDLOperations:
    """Test DDL operations with real database"""

    @pytest.mark.asyncio
    async def test_create_table(self, connected_client):
        """Test CREATE TABLE"""
        create_sql = """
        CREATE TEMPORARY TABLE test_ddl (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        result = await connected_client.execute_ddl(create_sql)
        assert result is True

    @pytest.mark.asyncio
    async def test_alter_table(self, connected_client):
        """Test ALTER TABLE"""
        # Create table
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_alter (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100)
            )
        """)

        # Alter table
        alter_sql = "ALTER TABLE test_alter ADD COLUMN email VARCHAR(100)"
        result = await connected_client.execute_ddl(alter_sql)
        assert result is True

    @pytest.mark.asyncio
    async def test_create_index(self, connected_client):
        """Test CREATE INDEX"""
        # Create table
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_index (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100)
            )
        """)

        # Create index
        index_sql = "CREATE INDEX idx_test_name ON test_index(name)"
        result = await connected_client.execute_ddl(index_sql)
        assert result is True


# Metadata Operations Tests

class TestPostgreSQLMetadataOperations:
    """Test metadata retrieval operations"""

    @pytest.mark.asyncio
    async def test_get_schemas(self, connected_client):
        """Test retrieving schemas"""
        schemas = await connected_client.get_schemas()

        assert isinstance(schemas, list)
        assert 'public' in schemas
        # System schemas should be filtered out
        assert 'pg_catalog' not in schemas
        assert 'information_schema' not in schemas

    @pytest.mark.asyncio
    async def test_get_table_list(self, connected_client):
        """Test retrieving table list"""
        # Create a temporary table
        await connected_client.execute_ddl("""
            CREATE TABLE test_metadata_temp (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100)
            )
        """)

        try:
            tables = await connected_client.get_table_list('public')
            assert isinstance(tables, list)
            assert 'test_metadata_temp' in tables
        finally:
            # Cleanup
            await connected_client.execute_ddl("DROP TABLE IF EXISTS test_metadata_temp")

    @pytest.mark.asyncio
    async def test_get_table_info(self, connected_client):
        """Test retrieving table information"""
        # Create a test table
        await connected_client.execute_ddl("""
            CREATE TABLE test_table_info (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100),
                age INTEGER DEFAULT 0
            )
        """)

        try:
            table_info = await connected_client.get_table_info('test_table_info', 'public')

            assert table_info['table_name'] == 'test_table_info'
            assert table_info['schema'] == 'public'
            assert len(table_info['columns']) >= 3

            # Find columns
            columns = {col['name']: col for col in table_info['columns']}

            assert 'id' in columns
            assert 'name' in columns
            assert 'email' in columns

            # Check nullable status
            assert columns['name']['nullable'] is False
            assert columns['email']['nullable'] is True
        finally:
            # Cleanup
            await connected_client.execute_ddl("DROP TABLE IF EXISTS test_table_info")


# Health Check Tests

class TestPostgreSQLHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check(self, connected_client):
        """Test health check on connected client"""
        health = await connected_client.health_check()

        assert health['state'] == 'connected'
        assert health['connected'] is True
        assert health['ping_successful'] is True
        assert 'connection_time' in health
        assert health['connection_time'] is not None


# Extended Client Tests

class TestPostgreSQLExtendedClient:
    """Test extended PostgreSQL client features"""

    @pytest.mark.asyncio
    async def test_extended_client_connect(self, extended_client):
        """Test extended client connection"""
        assert extended_client.is_connected is True

    @pytest.mark.asyncio
    async def test_execute_with_retry(self, extended_client):
        """Test query execution with retry"""
        result = await extended_client.execute_with_retry(
            "SELECT 1 as value",
            max_retries=3
        )

        assert len(result) == 1
        assert result[0]['value'] == 1

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, extended_client):
        """Test query execution with timeout"""
        result = await extended_client.execute_with_timeout(
            "SELECT 1 as value",
            timeout=5.0
        )

        assert len(result) == 1
        assert result[0]['value'] == 1

    @pytest.mark.asyncio
    async def test_timeout_on_slow_query(self, extended_client):
        """Test timeout on slow query"""
        with pytest.raises(asyncio.TimeoutError):
            await extended_client.execute_with_timeout(
                "SELECT pg_sleep(10)",  # 10 second sleep
                timeout=1.0  # 1 second timeout
            )

    @pytest.mark.asyncio
    async def test_transaction_context(self, extended_client):
        """Test transaction context manager"""
        async with await extended_client.transaction():
            result = await extended_client.execute("SELECT 1 as value")
            assert len(result) == 1


# Concurrent Operations Tests

class TestPostgreSQLConcurrentOperations:
    """Test concurrent operations"""

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, connected_client):
        """Test multiple concurrent queries"""
        queries = [
            "SELECT 1 as num",
            "SELECT 2 as num",
            "SELECT 3 as num",
            "SELECT 4 as num",
            "SELECT 5 as num"
        ]

        tasks = [connected_client.execute_query(q) for q in queries]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for i, result in enumerate(results, 1):
            assert result.rows[0][0] == i

    @pytest.mark.asyncio
    async def test_concurrent_inserts(self, connected_client):
        """Test concurrent insert operations"""
        # Create table
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_concurrent (
                id SERIAL PRIMARY KEY,
                value INTEGER
            )
        """)

        # Concurrent inserts
        insert_sql = "INSERT INTO test_concurrent (value) VALUES (%(value)s)"
        tasks = [
            connected_client.execute_query(insert_sql, {'value': i})
            for i in range(10)
        ]

        await asyncio.gather(*tasks)

        # Verify all inserts
        result = await connected_client.execute_query(
            "SELECT COUNT(*) FROM test_concurrent"
        )
        assert result.rows[0][0] == 10


# Error Handling Tests

class TestPostgreSQLErrorHandling:
    """Test error handling with real database"""

    @pytest.mark.asyncio
    async def test_syntax_error(self, connected_client):
        """Test SQL syntax error handling"""
        with pytest.raises(MCPClientError) as exc_info:
            await connected_client.execute_query("INVALID SQL SYNTAX")

        assert exc_info.value.error_code == "QUERY_FAILED"

    @pytest.mark.asyncio
    async def test_table_not_exists(self, connected_client):
        """Test querying non-existent table"""
        with pytest.raises(MCPClientError):
            await connected_client.execute_query(
                "SELECT * FROM nonexistent_table_xyz"
            )

    @pytest.mark.asyncio
    async def test_constraint_violation(self, connected_client):
        """Test constraint violation"""
        # Create table with unique constraint
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_constraint (
                id SERIAL PRIMARY KEY,
                email VARCHAR(100) UNIQUE
            )
        """)

        # First insert succeeds
        await connected_client.execute_query(
            "INSERT INTO test_constraint (email) VALUES (%(email)s)",
            {'email': 'test@example.com'}
        )

        # Second insert with same email should fail
        with pytest.raises(MCPClientError):
            await connected_client.execute_query(
                "INSERT INTO test_constraint (email) VALUES (%(email)s)",
                {'email': 'test@example.com'}
            )


# Performance Tests

class TestPostgreSQLPerformance:
    """Test performance characteristics"""

    @pytest.mark.asyncio
    async def test_large_result_set(self, connected_client):
        """Test handling of large result set"""
        # Create table with many rows
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_large (
                id SERIAL PRIMARY KEY,
                value INTEGER
            )
        """)

        # Insert 1000 rows
        insert_sql = "INSERT INTO test_large (value) VALUES (%(value)s)"
        for i in range(1000):
            await connected_client.execute_query(insert_sql, {'value': i})

        # Query all rows
        result = await connected_client.execute_query(
            "SELECT * FROM test_large"
        )

        assert len(result.rows) == 1000

    @pytest.mark.asyncio
    async def test_query_execution_time(self, connected_client):
        """Test query execution time tracking"""
        result = await connected_client.execute_query("SELECT 1")

        assert result.execution_time >= 0
        assert result.execution_time < 1.0  # Should be fast


# Data Type Tests

class TestPostgreSQLDataTypes:
    """Test various PostgreSQL data types"""

    @pytest.mark.asyncio
    async def test_integer_types(self, connected_client):
        """Test integer data types"""
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_integers (
                small_int SMALLINT,
                int_val INTEGER,
                big_int BIGINT
            )
        """)

        await connected_client.execute_query("""
            INSERT INTO test_integers VALUES (32767, 2147483647, 9223372036854775807)
        """)

        result = await connected_client.execute_query(
            "SELECT * FROM test_integers"
        )

        assert result.rows[0][0] == 32767
        assert result.rows[0][1] == 2147483647

    @pytest.mark.asyncio
    async def test_text_types(self, connected_client):
        """Test text data types"""
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_text (
                char_col CHAR(10),
                varchar_col VARCHAR(100),
                text_col TEXT
            )
        """)

        await connected_client.execute_query("""
            INSERT INTO test_text VALUES ('char', 'varchar', 'text')
        """)

        result = await connected_client.execute_query(
            "SELECT * FROM test_text"
        )

        assert len(result.rows) == 1

    @pytest.mark.asyncio
    async def test_boolean_type(self, connected_client):
        """Test boolean data type"""
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_boolean (
                bool_col BOOLEAN
            )
        """)

        await connected_client.execute_query(
            "INSERT INTO test_boolean VALUES (%(val)s)",
            {'val': True}
        )

        result = await connected_client.execute_query(
            "SELECT * FROM test_boolean"
        )

        assert result.rows[0][0] is True

    @pytest.mark.asyncio
    async def test_null_values(self, connected_client):
        """Test NULL value handling"""
        await connected_client.execute_ddl("""
            CREATE TEMPORARY TABLE test_nulls (
                id SERIAL PRIMARY KEY,
                nullable_col VARCHAR(100)
            )
        """)

        await connected_client.execute_query(
            "INSERT INTO test_nulls (nullable_col) VALUES (NULL)"
        )

        result = await connected_client.execute_query(
            "SELECT nullable_col FROM test_nulls"
        )

        assert result.rows[0][0] is None
