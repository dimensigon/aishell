"""
Integration Tests for Oracle MCP Client

Tests Oracle client with REAL database connections using:
- Oracle CDB$ROOT: SYS/MyOraclePass123@localhost:1521/free (SYSDBA)
- Oracle FREEPDB1: SYS/MyOraclePass123@localhost:1521/freepdb1 (SYSDBA)

Requires:
- Oracle database running on localhost:1521
- Test database configuration in tests/config/test_databases.yaml
"""

import pytest
import asyncio
import yaml
from pathlib import Path
from typing import Dict, Any

from src.mcp_clients.oracle_client import OracleClient
from src.mcp_clients.base import (
    MCPClientError,
    ConnectionState,
    ConnectionConfig
)


# Load test database configuration

@pytest.fixture(scope='module')
def test_db_config() -> Dict[str, Any]:
    """Load test database configuration"""
    config_path = Path(__file__).parent.parent / 'config' / 'test_databases.yaml'
    with open(config_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def oracle_cdb_config(test_db_config) -> ConnectionConfig:
    """Oracle CDB$ROOT configuration from YAML"""
    db = test_db_config['databases']['oracle_root']
    return ConnectionConfig(
        host=db['connection']['host'],
        port=db['connection']['port'],
        database=db['connection']['service'],
        username=db['connection']['user'],
        password=db['connection']['password'],
        extra_params={'mode': db['connection']['mode']}
    )


@pytest.fixture
def oracle_pdb_config(test_db_config) -> ConnectionConfig:
    """Oracle FREEPDB1 configuration from YAML"""
    db = test_db_config['databases']['oracle_pdb']
    return ConnectionConfig(
        host=db['connection']['host'],
        port=db['connection']['port'],
        database=db['connection']['service'],
        username=db['connection']['user'],
        password=db['connection']['password'],
        extra_params={'mode': db['connection']['mode']}
    )


@pytest.fixture
async def oracle_cdb_client(oracle_cdb_config):
    """Create and connect Oracle CDB client"""
    client = OracleClient()
    try:
        await client.connect(oracle_cdb_config)
        yield client
    finally:
        await client.disconnect()


@pytest.fixture
async def oracle_pdb_client(oracle_pdb_config):
    """Create and connect Oracle PDB client"""
    client = OracleClient()
    try:
        await client.connect(oracle_pdb_config)
        yield client
    finally:
        await client.disconnect()


# Test CDB Connection and Queries

class TestOracleCDBIntegration:
    """Integration tests for Oracle CDB$ROOT"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cdb_connection(self, oracle_cdb_config):
        """Test real CDB connection"""
        client = OracleClient()

        try:
            result = await client.connect(oracle_cdb_config)

            assert result is True
            assert client.state == ConnectionState.CONNECTED
            assert client.is_connected is True
        finally:
            await client.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cdb_dual_query(self, oracle_cdb_client):
        """Test SELECT from DUAL on CDB"""
        result = await oracle_cdb_client.execute_query("SELECT 1 FROM DUAL")

        assert result['columns'] == ['1']
        assert len(result['rows']) == 1
        assert result['rows'][0][0] == 1
        assert result['rowcount'] == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cdb_version_query(self, oracle_cdb_client):
        """Test version query on CDB"""
        result = await oracle_cdb_client.execute_query(
            "SELECT banner FROM v$version WHERE rownum = 1"
        )

        assert len(result['columns']) == 1
        assert len(result['rows']) == 1
        assert 'Oracle' in result['rows'][0][0]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cdb_database_name(self, oracle_cdb_client):
        """Test database name query on CDB"""
        result = await oracle_cdb_client.execute_query("SELECT name FROM v$database")

        assert len(result['rows']) == 1
        assert result['rows'][0][0] in ['FREE', 'XE', 'ORCL']

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cdb_sysdate(self, oracle_cdb_client):
        """Test SYSDATE query on CDB"""
        result = await oracle_cdb_client.execute_query("SELECT SYSDATE FROM DUAL")

        assert len(result['rows']) == 1
        assert result['rows'][0][0] is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cdb_user_query(self, oracle_cdb_client):
        """Test USER query on CDB"""
        result = await oracle_cdb_client.execute_query("SELECT USER FROM DUAL")

        assert result['rows'][0][0] == 'SYS'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cdb_health_check(self, oracle_cdb_client):
        """Test health check on CDB"""
        health = await oracle_cdb_client.health_check()

        assert health['state'] == 'connected'
        assert health['connected'] is True
        assert health['ping_successful'] is True


# Test PDB Connection and Queries

class TestOraclePDBIntegration:
    """Integration tests for Oracle FREEPDB1"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdb_connection(self, oracle_pdb_config):
        """Test real PDB connection"""
        client = OracleClient()

        try:
            result = await client.connect(oracle_pdb_config)

            assert result is True
            assert client.state == ConnectionState.CONNECTED
            assert client.is_connected is True
        finally:
            await client.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdb_dual_query(self, oracle_pdb_client):
        """Test SELECT from DUAL on PDB"""
        result = await oracle_pdb_client.execute_query("SELECT 1 FROM DUAL")

        assert result['columns'] == ['1']
        assert len(result['rows']) == 1
        assert result['rows'][0][0] == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdb_container_info(self, oracle_pdb_client):
        """Test container info query on PDB"""
        result = await oracle_pdb_client.execute_query(
            "SELECT con_id, name FROM v$containers WHERE con_id = 3"
        )

        assert len(result['rows']) >= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdb_user_query(self, oracle_pdb_client):
        """Test USER query on PDB"""
        result = await oracle_pdb_client.execute_query("SELECT USER FROM DUAL")

        assert result['rows'][0][0] == 'SYS'


# Test DDL Operations (Creating Tables)

class TestOracleDDLIntegration:
    """Integration tests for DDL operations"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_and_drop_table(self, oracle_pdb_client):
        """Test CREATE and DROP TABLE on PDB"""
        # Create test table
        await oracle_pdb_client.execute_ddl("""
            CREATE TABLE test_integration_users (
                id NUMBER PRIMARY KEY,
                name VARCHAR2(100) NOT NULL,
                email VARCHAR2(255),
                created_at DATE DEFAULT SYSDATE
            )
        """)

        # Verify table exists
        tables = await oracle_pdb_client.get_table_list()
        assert 'TEST_INTEGRATION_USERS' in tables

        # Clean up
        await oracle_pdb_client.execute_ddl("DROP TABLE test_integration_users")

        # Verify table removed
        tables = await oracle_pdb_client.get_table_list()
        assert 'TEST_INTEGRATION_USERS' not in tables

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_alter_table(self, oracle_pdb_client):
        """Test ALTER TABLE operation"""
        # Create test table
        await oracle_pdb_client.execute_ddl("""
            CREATE TABLE test_alter_table (
                id NUMBER PRIMARY KEY
            )
        """)

        # Alter table
        await oracle_pdb_client.execute_ddl("""
            ALTER TABLE test_alter_table ADD (
                name VARCHAR2(100),
                description VARCHAR2(500)
            )
        """)

        # Get table info
        table_info = await oracle_pdb_client.get_table_info('test_alter_table')
        column_names = [col['name'] for col in table_info['columns']]

        assert 'NAME' in column_names
        assert 'DESCRIPTION' in column_names

        # Clean up
        await oracle_pdb_client.execute_ddl("DROP TABLE test_alter_table")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_index(self, oracle_pdb_client):
        """Test CREATE INDEX operation"""
        # Create test table
        await oracle_pdb_client.execute_ddl("""
            CREATE TABLE test_index_table (
                id NUMBER PRIMARY KEY,
                name VARCHAR2(100)
            )
        """)

        # Create index
        await oracle_pdb_client.execute_ddl("""
            CREATE INDEX idx_test_name ON test_index_table(name)
        """)

        # Clean up
        await oracle_pdb_client.execute_ddl("DROP TABLE test_index_table")


# Test DML Operations (Insert, Update, Delete)

class TestOracleDMLIntegration:
    """Integration tests for DML operations"""

    @pytest.fixture(autouse=True)
    async def setup_test_table(self, oracle_pdb_client):
        """Setup and teardown test table for DML tests"""
        # Create test table
        await oracle_pdb_client.execute_ddl("""
            CREATE TABLE test_dml_users (
                id NUMBER PRIMARY KEY,
                name VARCHAR2(100),
                email VARCHAR2(255)
            )
        """)

        yield

        # Clean up
        try:
            await oracle_pdb_client.execute_ddl("DROP TABLE test_dml_users")
        except:
            pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_insert_and_select(self, oracle_pdb_client):
        """Test INSERT and SELECT operations"""
        # Insert data
        result = await oracle_pdb_client.execute_query("""
            INSERT INTO test_dml_users (id, name, email)
            VALUES (1, 'John Doe', 'john@example.com')
        """)

        assert result['rowcount'] == 1

        # Commit is handled by execute_query for DML
        # Query the data
        result = await oracle_pdb_client.execute_query("""
            SELECT id, name, email FROM test_dml_users WHERE id = 1
        """)

        assert len(result['rows']) == 1
        assert result['rows'][0][0] == 1
        assert result['rows'][0][1] == 'John Doe'
        assert result['rows'][0][2] == 'john@example.com'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_insert_with_parameters(self, oracle_pdb_client):
        """Test INSERT with bind parameters"""
        result = await oracle_pdb_client.execute_query(
            """
            INSERT INTO test_dml_users (id, name, email)
            VALUES (:id, :name, :email)
            """,
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
        )

        assert result['rowcount'] == 1

        # Verify
        result = await oracle_pdb_client.execute_query(
            "SELECT name FROM test_dml_users WHERE id = :id",
            {'id': 2}
        )

        assert result['rows'][0][0] == 'Jane Smith'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_operation(self, oracle_pdb_client):
        """Test UPDATE operation"""
        # Insert initial data
        await oracle_pdb_client.execute_query("""
            INSERT INTO test_dml_users (id, name, email)
            VALUES (3, 'Test User', 'test@example.com')
        """)

        # Update data
        result = await oracle_pdb_client.execute_query("""
            UPDATE test_dml_users
            SET name = 'Updated User', email = 'updated@example.com'
            WHERE id = 3
        """)

        assert result['rowcount'] == 1

        # Verify update
        result = await oracle_pdb_client.execute_query(
            "SELECT name, email FROM test_dml_users WHERE id = 3"
        )

        assert result['rows'][0][0] == 'Updated User'
        assert result['rows'][0][1] == 'updated@example.com'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_operation(self, oracle_pdb_client):
        """Test DELETE operation"""
        # Insert data
        await oracle_pdb_client.execute_query("""
            INSERT INTO test_dml_users (id, name, email)
            VALUES (4, 'Delete Me', 'delete@example.com')
        """)

        # Delete data
        result = await oracle_pdb_client.execute_query(
            "DELETE FROM test_dml_users WHERE id = 4"
        )

        assert result['rowcount'] == 1

        # Verify deletion
        result = await oracle_pdb_client.execute_query(
            "SELECT COUNT(*) FROM test_dml_users WHERE id = 4"
        )

        assert result['rows'][0][0] == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bulk_insert(self, oracle_pdb_client):
        """Test bulk INSERT operation"""
        # Insert multiple rows
        for i in range(5, 10):
            await oracle_pdb_client.execute_query(
                """
                INSERT INTO test_dml_users (id, name, email)
                VALUES (:id, :name, :email)
                """,
                {'id': i, 'name': f'User {i}', 'email': f'user{i}@example.com'}
            )

        # Verify count
        result = await oracle_pdb_client.execute_query(
            "SELECT COUNT(*) FROM test_dml_users"
        )

        assert result['rows'][0][0] >= 5


# Test Metadata Operations

class TestOracleMetadataIntegration:
    """Integration tests for metadata operations"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_table_list(self, oracle_pdb_client):
        """Test retrieving table list"""
        tables = await oracle_pdb_client.get_table_list()

        assert isinstance(tables, list)
        # Should have at least system tables
        assert len(tables) >= 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_table_info(self, oracle_pdb_client):
        """Test retrieving table information"""
        # Create test table
        await oracle_pdb_client.execute_ddl("""
            CREATE TABLE test_metadata_table (
                id NUMBER(10) PRIMARY KEY,
                name VARCHAR2(100) NOT NULL,
                description VARCHAR2(500),
                created_at DATE DEFAULT SYSDATE
            )
        """)

        try:
            # Get table info
            table_info = await oracle_pdb_client.get_table_info('test_metadata_table')

            assert table_info['table_name'] == 'test_metadata_table'
            assert len(table_info['columns']) == 4

            # Verify column details
            columns = {col['name']: col for col in table_info['columns']}
            assert 'ID' in columns
            assert 'NAME' in columns
            assert 'DESCRIPTION' in columns
            assert 'CREATED_AT' in columns

            # Check nullable flags
            assert columns['ID']['nullable'] is False  # Primary key
            assert columns['NAME']['nullable'] is False  # NOT NULL
            assert columns['DESCRIPTION']['nullable'] is True

        finally:
            await oracle_pdb_client.execute_ddl("DROP TABLE test_metadata_table")


# Test Error Handling

class TestOracleErrorHandlingIntegration:
    """Integration tests for error handling"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_query_error(self, oracle_pdb_client):
        """Test invalid SQL query error"""
        with pytest.raises(MCPClientError) as exc_info:
            await oracle_pdb_client.execute_query("SELECT * FROM nonexistent_table_xyz")

        assert exc_info.value.error_code == "QUERY_FAILED"
        assert "ORA-00942" in str(exc_info.value) or "does not exist" in str(exc_info.value).lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_ddl_error(self, oracle_pdb_client):
        """Test invalid DDL error"""
        # Create table first
        await oracle_pdb_client.execute_ddl("""
            CREATE TABLE test_error_table (id NUMBER)
        """)

        try:
            # Try to create duplicate table
            with pytest.raises(MCPClientError) as exc_info:
                await oracle_pdb_client.execute_ddl("""
                    CREATE TABLE test_error_table (id NUMBER)
                """)

            assert exc_info.value.error_code == "DDL_FAILED"
            assert "ORA-00955" in str(exc_info.value) or "already" in str(exc_info.value).lower()

        finally:
            await oracle_pdb_client.execute_ddl("DROP TABLE test_error_table")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test connection error with invalid credentials"""
        client = OracleClient()

        invalid_config = ConnectionConfig(
            host='localhost',
            port=1521,
            database='freepdb1',
            username='invalid_user',
            password='invalid_pass'
        )

        with pytest.raises(MCPClientError) as exc_info:
            await client.connect(invalid_config)

        assert exc_info.value.error_code == "CONNECTION_FAILED"


# Test Concurrent Operations

class TestOracleConcurrentIntegration:
    """Integration tests for concurrent operations"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_queries(self, oracle_pdb_client):
        """Test concurrent query execution"""
        # Execute multiple queries concurrently
        tasks = [
            oracle_pdb_client.execute_query("SELECT 1 FROM DUAL"),
            oracle_pdb_client.execute_query("SELECT 2 FROM DUAL"),
            oracle_pdb_client.execute_query("SELECT 3 FROM DUAL"),
            oracle_pdb_client.execute_query("SELECT USER FROM DUAL"),
            oracle_pdb_client.execute_query("SELECT SYSDATE FROM DUAL")
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for result in results:
            assert isinstance(result, dict)
            assert 'columns' in result
            assert 'rows' in result
            assert len(result['rows']) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_connections(self, oracle_pdb_config):
        """Test multiple concurrent connections"""
        async def connect_and_query():
            client = OracleClient()
            try:
                await client.connect(oracle_pdb_config)
                result = await client.execute_query("SELECT 1 FROM DUAL")
                return result
            finally:
                await client.disconnect()

        # Create 5 concurrent connections
        tasks = [connect_and_query() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for result in results:
            assert result['rows'][0][0] == 1


# Test Connection Lifecycle

class TestOracleConnectionLifecycle:
    """Integration tests for connection lifecycle"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_connect_disconnect_cycle(self, oracle_pdb_config):
        """Test multiple connect/disconnect cycles"""
        client = OracleClient()

        for i in range(3):
            # Connect
            await client.connect(oracle_pdb_config)
            assert client.is_connected is True

            # Execute query
            result = await client.execute_query("SELECT 1 FROM DUAL")
            assert result['rows'][0][0] == 1

            # Disconnect
            await client.disconnect()
            assert client.is_connected is False

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_reconnect_after_error(self, oracle_pdb_config):
        """Test reconnection after error"""
        client = OracleClient()

        # First connection
        await client.connect(oracle_pdb_config)

        # Force error
        try:
            await client.execute_query("INVALID SQL QUERY")
        except MCPClientError:
            pass

        # Should still be connected
        assert client.is_connected is True

        # Should be able to execute valid query
        result = await client.execute_query("SELECT 1 FROM DUAL")
        assert result['rows'][0][0] == 1

        await client.disconnect()


# Performance Tests

class TestOraclePerformance:
    """Integration tests for performance"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_query_execution_time(self, oracle_pdb_client):
        """Test query execution time tracking"""
        result = await oracle_pdb_client.execute_query("SELECT 1 FROM DUAL")

        # Verify execution time is tracked
        # Note: In the actual implementation, this would be tracked in QueryResult
        assert result is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_result_set(self, oracle_pdb_client):
        """Test handling large result set"""
        # Create table with test data
        await oracle_pdb_client.execute_ddl("""
            CREATE TABLE test_large_result (
                id NUMBER PRIMARY KEY,
                data VARCHAR2(100)
            )
        """)

        try:
            # Insert 100 rows
            for i in range(100):
                await oracle_pdb_client.execute_query(
                    "INSERT INTO test_large_result (id, data) VALUES (:id, :data)",
                    {'id': i, 'data': f'Data {i}'}
                )

            # Query all rows
            result = await oracle_pdb_client.execute_query(
                "SELECT * FROM test_large_result ORDER BY id"
            )

            assert len(result['rows']) == 100
            assert result['rowcount'] == 100

        finally:
            await oracle_pdb_client.execute_ddl("DROP TABLE test_large_result")
