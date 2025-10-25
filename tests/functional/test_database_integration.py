"""
Simplified functional tests for AI-Shell with real database connections.

Tests all major features against live Oracle and PostgreSQL databases.
"""

import pytest
import asyncio
from src.mcp_clients.base import ConnectionConfig
from src.mcp_clients.oracle_client import OracleClient
from src.mcp_clients.postgresql_client import PostgreSQLClient


# Database configurations
POSTGRESQL_CONFIG = ConnectionConfig(
    host='localhost',
    port=5432,
    database='postgres',
    username='postgres',
    password='MyPostgresPass123'
)

ORACLE_CDB_CONFIG = ConnectionConfig(
    host='localhost',
    port=1521,
    database='free',  # service_name
    username='SYS',
    password='MyOraclePass123',
    extra_params={'mode': 'SYSDBA'}
)

ORACLE_PDB_CONFIG = ConnectionConfig(
    host='localhost',
    port=1521,
    database='freepdb1',  # service_name
    username='SYS',
    password='MyOraclePass123',
    extra_params={'mode': 'SYSDBA'}
)


class TestDatabaseConnections:
    """Test basic database connectivity."""

    @pytest.mark.asyncio
    async def test_postgresql_connection(self):
        """Test connection to PostgreSQL."""
        client = PostgreSQLClient()

        try:
            success = await client.connect(POSTGRESQL_CONFIG)
            assert success is True

            health = await client.health_check()
            assert health['connected'] is True
            assert health['state'] == 'connected'
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_oracle_cdb_connection(self):
        """Test connection to Oracle CDB$ROOT."""
        client = OracleClient()

        try:
            success = await client.connect(ORACLE_CDB_CONFIG)
            assert success is True

            health = await client.health_check()
            assert health['connected'] is True
            assert health['state'] == 'connected'
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_oracle_pdb_connection(self):
        """Test connection to Oracle FREEPDB1."""
        client = OracleClient()

        try:
            success = await client.connect(ORACLE_PDB_CONFIG)
            assert success is True

            health = await client.health_check()
            assert health['connected'] is True
            assert health['state'] == 'connected'
        finally:
            await client.disconnect()


class TestPostgreSQLCRUD:
    """Test CRUD operations on PostgreSQL."""

    @pytest.mark.asyncio
    async def test_create_table(self):
        """Test creating a table."""
        client = PostgreSQLClient()

        try:
            await client.connect(POSTGRESQL_CONFIG)

            result = await client.execute_query("""
                CREATE TEMP TABLE test_users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # DDL statements return -1 for rowcount in PostgreSQL
            assert result.rowcount == -1 or result.rowcount >= 0
            assert result.metadata['query_type'] == 'DDL'
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_insert_and_select(self):
        """Test INSERT and SELECT operations."""
        client = PostgreSQLClient()

        try:
            await client.connect(POSTGRESQL_CONFIG)

            # Create table
            await client.execute_query("""
                CREATE TEMP TABLE test_products (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    price DECIMAL(10, 2)
                )
            """)

            # Insert data
            await client.execute_query(
                "INSERT INTO test_products (name, price) VALUES (%s, %s)",
                ("Widget", 19.99)
            )
            await client.execute_query(
                "INSERT INTO test_products (name, price) VALUES (%s, %s)",
                ("Gadget", 29.99)
            )

            # Select data
            result = await client.execute_query("SELECT * FROM test_products ORDER BY id")

            assert len(result.rows) == 2
            assert result.rows[0][1] == 'Widget'  # name column
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_update_and_delete(self):
        """Test UPDATE and DELETE operations."""
        client = PostgreSQLClient()

        try:
            await client.connect(POSTGRESQL_CONFIG)

            # Create and populate table
            await client.execute_query("""
                CREATE TEMP TABLE test_items (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    status VARCHAR(20)
                )
            """)

            await client.execute_query(
                "INSERT INTO test_items (name, status) VALUES (%s, %s)",
                ("Item1", "active")
            )
            await client.execute_query(
                "INSERT INTO test_items (name, status) VALUES (%s, %s)",
                ("Item2", "inactive")
            )

            # Update
            result = await client.execute_query(
                "UPDATE test_items SET status = %s WHERE name = %s",
                ("archived", "Item1")
            )
            assert result.rowcount == 1

            # Delete
            result = await client.execute_query(
                "DELETE FROM test_items WHERE name = %s",
                ("Item2",)
            )
            assert result.rowcount == 1

            # Verify
            result = await client.execute_query("SELECT COUNT(*) FROM test_items")
            assert result.rows[0][0] == 1
        finally:
            await client.disconnect()


class TestSafetyFeatures:
    """Test safety and security features."""

    def test_sql_injection_detection(self):
        """Test SQL injection detection."""
        from src.security.sql_guard import SQLGuard

        guard = SQLGuard()

        # Safe query
        result = guard.validate_query("SELECT * FROM users WHERE id = ?")
        assert result['is_safe'] is True

        # SQL injection attempt
        result = guard.validate_query("SELECT * FROM users WHERE id = '1' OR '1'='1'")
        assert result['is_safe'] is False
        assert result['threat_type'] == 'SQL Injection'

        # DROP TABLE attempt
        result = guard.validate_query("SELECT * FROM users; DROP TABLE users;")
        assert result['is_safe'] is False
        assert result['severity'] in ['critical', 'high']

    def test_input_sanitization(self):
        """Test input sanitization."""
        from src.security.sql_guard import SQLGuard

        guard = SQLGuard()

        # Test sanitizing dangerous input
        dangerous = "admin'; DROP TABLE users; --"
        sanitized = guard.sanitize_input(dangerous)

        assert "'" not in sanitized or "''" in sanitized
        assert "--" not in sanitized


class TestPerformanceMonitoring:
    """Test performance monitoring features."""

    def test_query_performance_tracking(self):
        """Test query performance tracking."""
        from src.performance.monitor import PerformanceMonitor

        monitor = PerformanceMonitor(slow_query_threshold=0.1)

        # Record queries
        monitor.record_query("SELECT * FROM users", execution_time=0.05, rows=100)
        monitor.record_query("SELECT * FROM large_table", execution_time=2.5, rows=1000000)

        metrics = monitor.get_metrics()
        assert metrics['total_queries'] == 2
        assert metrics['slow_query_count'] == 1

        slow_queries = monitor.get_slow_queries()
        assert len(slow_queries) == 1
        assert slow_queries[0]['execution_time'] == 2.5

    def test_memory_tracking(self):
        """Test memory usage tracking."""
        from src.performance.monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        monitor.track_memory_usage()

        metrics = monitor.get_memory_metrics()
        assert 'current_memory_mb' in metrics
        assert metrics['current_memory_mb'] > 0

    def test_metrics_export(self):
        """Test metrics export functionality."""
        from src.performance.monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        monitor.record_query("SELECT 1", execution_time=0.01, rows=1)
        monitor.track_memory_usage()

        export = monitor.export_metrics(format='json')
        assert 'queries' in export
        assert 'memory' in export


class TestEnterpriseFeatures:
    """Test enterprise features."""

    def test_multi_tenancy(self):
        """Test multi-tenancy features."""
        from src.core.tenancy import TenantManager

        manager = TenantManager()

        # Create tenants
        tenant1 = manager.create_tenant(
            tenant_id="test_tenant_1",
            config={'database': 'postgresql'}
        )

        assert tenant1.tenant_id == "test_tenant_1"
        assert tenant1.config['database'] == 'postgresql'

        # Test get tenant
        retrieved = manager.get_tenant("test_tenant_1")
        assert retrieved is not None
        assert retrieved.tenant_id == "test_tenant_1"

    def test_rbac_permissions(self):
        """Test RBAC permission system."""
        from src.security.rbac import RBACManager

        rbac = RBACManager()

        # Create roles
        rbac.create_role(
            "admin",
            permissions=["db.*", "user.*"],
            description="Admin role"
        )

        rbac.create_role(
            "analyst",
            permissions=["db.read"],
            description="Analyst role"
        )

        # Assign roles
        rbac.assign_role("user_admin", "admin")
        rbac.assign_role("user_analyst", "analyst")

        # Check permissions
        assert rbac.has_permission("user_admin", "db.write") is True
        assert rbac.has_permission("user_analyst", "db.write") is False
        assert rbac.has_permission("user_analyst", "db.read") is True

    def test_audit_logging(self):
        """Test audit logging."""
        from src.security.audit import AuditLogger

        logger = AuditLogger(retention_days=90)

        # Log events
        log_entry = logger.log_action(
            user="test_user",
            action="user.login",
            resource="system",
            details={"ip": "127.0.0.1"}
        )

        assert log_entry.user == "test_user"
        assert log_entry.action == "user.login"

        # Query logs
        logs = logger.search_logs(user="test_user")

        assert len(logs) >= 1
        assert logs[0]['action'] == 'user.login'

    def test_data_encryption(self):
        """Test data encryption."""
        from src.security.encryption import DataEncryption, FieldEncryption

        # Basic encryption
        encryptor = DataEncryption(key="test-key-12345678901234567890")

        plaintext = "sensitive data"
        ciphertext = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(ciphertext)

        assert plaintext == decrypted
        assert ciphertext != plaintext

        # Field encryption
        field_enc = FieldEncryption(key="field-key-1234567890123456")

        data = {
            'id': 1,
            'name': 'Alice',
            'ssn': '123-45-6789'
        }

        encrypted_data = field_enc.encrypt_fields(data, ['ssn'])
        assert encrypted_data['name'] == 'Alice'
        assert encrypted_data['ssn'] != '123-45-6789'

        decrypted_data = field_enc.decrypt_fields(encrypted_data, ['ssn'])
        assert decrypted_data['ssn'] == '123-45-6789'


class TestNLPToSQL:
    """Test NLP-to-SQL conversion."""

    def test_nlp_query_conversion(self):
        """Test converting natural language to SQL."""
        from src.database.nlp_to_sql import NLPToSQL

        nlp = NLPToSQL()

        # Test 1: Simple SELECT - "show all users"
        result = nlp.convert("show all users")
        assert result['sql'] is not None, f"Failed to convert 'show all users': {result}"
        assert 'SELECT' in result['sql'].upper()
        assert 'users' in result['sql'].lower()
        assert result['confidence'] == 'high'

        # Test 2: WHERE clause - "find users where status is active"
        result = nlp.convert("find users where status is active")
        assert result['sql'] is not None, f"Failed to convert WHERE query: {result}"
        assert 'WHERE' in result['sql'].upper()
        assert 'users' in result['sql'].lower()
        assert 'status' in result['sql'].lower()

        # Test 3: Aggregate - "count users"
        result = nlp.convert("count users")
        assert result['sql'] is not None, f"Failed to convert count query: {result}"
        assert 'COUNT' in result['sql'].upper()
        assert 'users' in result['sql'].lower()

        # Test 4: List query - "list products"
        result = nlp.convert("list products")
        assert result['sql'] is not None
        assert 'SELECT' in result['sql'].upper()
        assert 'products' in result['sql'].lower()

        # Test 5: How many query - "how many orders"
        result = nlp.convert("how many orders")
        assert result['sql'] is not None
        assert 'COUNT' in result['sql'].upper()

        # Test 6: Unsupported query returns None with suggestions
        result = nlp.convert("do something complex that won't match")
        assert result['sql'] is None
        assert result['confidence'] == 'none'
        assert 'error' in result
        assert 'suggestions' in result
        assert len(result['suggestions']) > 0


class TestMultiDatabaseCoordination:
    """Test coordination across multiple databases."""

    @pytest.mark.asyncio
    async def test_dual_database_operations(self):
        """Test operations across PostgreSQL and Oracle."""
        pg_client = PostgreSQLClient()
        oracle_client = OracleClient()

        try:
            # Connect to both
            await pg_client.connect(POSTGRESQL_CONFIG)
            await oracle_client.connect(ORACLE_CDB_CONFIG)

            # Test both are healthy
            pg_health = await pg_client.health_check()
            oracle_health = await oracle_client.health_check()

            assert pg_health['connected'] is True
            assert oracle_health['connected'] is True

            # Create table in PostgreSQL
            await pg_client.execute_query("""
                CREATE TEMP TABLE coordination_test (
                    id SERIAL PRIMARY KEY,
                    message VARCHAR(100)
                )
            """)

            await pg_client.execute_query(
                "INSERT INTO coordination_test (message) VALUES (%s)",
                ("Multi-DB success!",)
            )

            result = await pg_client.execute_query("SELECT message FROM coordination_test")
            assert result.rows[0][0] == "Multi-DB success!"

        finally:
            await pg_client.disconnect()
            await oracle_client.disconnect()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
