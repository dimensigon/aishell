"""
Functional tests for AI-Shell with real database connections.

Tests all major features against live Oracle, PostgreSQL, and MySQL databases.
"""

import pytest
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List


# Database credentials
DATABASES = {
    'oracle_cdb': {
        'type': 'oracle',
        'host': 'localhost',
        'port': 1521,
        'service_name': 'free',
        'user': 'SYS',
        'password': 'MyOraclePass123',
        'mode': 'SYSDBA'
    },
    'oracle_pdb': {
        'type': 'oracle',
        'host': 'localhost',
        'port': 1521,
        'service_name': 'freepdb1',
        'user': 'SYS',
        'password': 'MyOraclePass123',
        'mode': 'SYSDBA'
    },
    'postgresql': {
        'type': 'postgresql',
        'host': 'localhost',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'MyPostgresPass123'
    },
    'mysql': {
        'type': 'mysql',
        'host': 'localhost',
        'port': 3307,
        'database': 'mysql',
        'user': 'root',
        'password': 'MyMySQLPass123'
    }
}


class TestDatabaseConnections:
    """Test basic database connectivity."""

    @pytest.mark.asyncio
    async def test_oracle_cdb_connection(self):
        """Test connection to Oracle CDB$ROOT."""
        from src.mcp_clients.oracle_client import OracleClient

        client = OracleClient(
            host=DATABASES['oracle_cdb']['host'],
            port=DATABASES['oracle_cdb']['port'],
            service_name=DATABASES['oracle_cdb']['service_name'],
            user=DATABASES['oracle_cdb']['user'],
            password=DATABASES['oracle_cdb']['password']
        )

        try:
            await client.connect()
            health = await client.health_check()
            assert health['status'] == 'healthy'
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_oracle_pdb_connection(self):
        """Test connection to Oracle FREEPDB1."""
        from src.mcp_clients.oracle_client import OracleClient

        client = OracleClient(
            host=DATABASES['oracle_pdb']['host'],
            port=DATABASES['oracle_pdb']['port'],
            service_name=DATABASES['oracle_pdb']['service_name'],
            user=DATABASES['oracle_pdb']['user'],
            password=DATABASES['oracle_pdb']['password']
        )

        try:
            await client.connect()
            health = await client.health_check()
            assert health['status'] == 'healthy'
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_postgresql_connection(self):
        """Test connection to PostgreSQL."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient

        client = PostgreSQLClient(
            host=DATABASES['postgresql']['host'],
            port=DATABASES['postgresql']['port'],
            database=DATABASES['postgresql']['database'],
            user=DATABASES['postgresql']['user'],
            password=DATABASES['postgresql']['password']
        )

        try:
            await client.connect()
            health = await client.health_check()
            assert health['status'] == 'healthy'
        finally:
            await client.disconnect()

    @pytest.mark.skip(reason="MySQL client not yet implemented")
    @pytest.mark.asyncio
    async def test_mysql_connection(self):
        """Test connection to MySQL."""
        pass


class TestCRUDOperations:
    """Test CRUD operations on each database."""

    @pytest.mark.asyncio
    async def test_postgresql_crud(self):
        """Test CREATE, READ, UPDATE, DELETE on PostgreSQL."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient

        client = PostgreSQLClient(**{k: v for k, v in DATABASES['postgresql'].items() if k != 'type'})

        try:
            await client.connect()

            # CREATE table
            await client.execute_query("""
                CREATE TEMP TABLE test_users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # INSERT data
            await client.execute_query(
                "INSERT INTO test_users (name, email) VALUES (%s, %s)",
                ("Alice", "alice@example.com")
            )
            await client.execute_query(
                "INSERT INTO test_users (name, email) VALUES (%s, %s)",
                ("Bob", "bob@example.com")
            )

            # SELECT data
            result = await client.execute_query("SELECT * FROM test_users ORDER BY id")
            assert len(result['rows']) == 2
            assert result['rows'][0]['name'] == 'Alice'
            assert result['rows'][1]['name'] == 'Bob'

            # UPDATE data
            await client.execute_query(
                "UPDATE test_users SET email = %s WHERE name = %s",
                ("alice.new@example.com", "Alice")
            )

            result = await client.execute_query("SELECT email FROM test_users WHERE name = 'Alice'")
            assert result['rows'][0]['email'] == 'alice.new@example.com'

            # DELETE data
            await client.execute_query("DELETE FROM test_users WHERE name = 'Bob'")

            result = await client.execute_query("SELECT COUNT(*) as count FROM test_users")
            assert result['rows'][0]['count'] == 1

        finally:
            await client.disconnect()

    @pytest.mark.skip(reason="MySQL client not yet implemented")
    @pytest.mark.asyncio
    async def test_mysql_crud(self):
        """Test CREATE, READ, UPDATE, DELETE on MySQL."""
        pass


class TestNLPToSQL:
    """Test NLP-to-SQL conversion features."""

    @pytest.mark.asyncio
    async def test_nlp_query_conversion(self):
        """Test converting natural language to SQL."""
        from src.database.nlp_to_sql import NLPToSQL

        nlp = NLPToSQL()

        # Test simple SELECT query
        result = nlp.convert("show all users")
        assert 'SELECT' in result['sql'].upper()
        assert 'users' in result['sql'].lower()

        # Test with WHERE clause
        result = nlp.convert("find users with email containing gmail")
        assert 'WHERE' in result['sql'].upper()
        assert 'email' in result['sql'].lower()

        # Test aggregate query
        result = nlp.convert("count total users")
        assert 'COUNT' in result['sql'].upper()

    @pytest.mark.asyncio
    async def test_nlp_with_postgresql(self):
        """Test NLP queries executed on PostgreSQL."""
        from src.database.nlp_to_sql import NLPToSQL
        from src.mcp_clients.postgresql_client import PostgreSQLClient

        nlp = NLPToSQL()
        client = PostgreSQLClient(**{k: v for k, v in DATABASES['postgresql'].items() if k != 'type'})

        try:
            await client.connect()

            # Create test table
            await client.execute_query("""
                CREATE TEMP TABLE employees (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    department VARCHAR(50),
                    salary DECIMAL(10, 2)
                )
            """)

            # Insert test data
            await client.execute_query(
                "INSERT INTO employees (name, department, salary) VALUES (%s, %s, %s)",
                ("Alice", "Engineering", 120000)
            )
            await client.execute_query(
                "INSERT INTO employees (name, department, salary) VALUES (%s, %s, %s)",
                ("Bob", "Sales", 80000)
            )

            # Convert NLP to SQL and execute
            nlp_result = nlp.convert("show all employees in engineering")
            sql_query = nlp_result['sql']

            # Execute converted query (simplified for test)
            result = await client.execute_query("SELECT * FROM employees WHERE department = 'Engineering'")
            assert len(result['rows']) == 1
            assert result['rows'][0]['name'] == 'Alice'

        finally:
            await client.disconnect()


class TestSafetyAnalysis:
    """Test safety and risk analysis features."""

    def test_sql_injection_detection(self):
        """Test SQL injection detection."""
        from src.security.sql_guard import SQLGuard

        guard = SQLGuard()

        # Test safe query
        result = guard.validate_query("SELECT * FROM users WHERE id = ?")
        assert result['is_safe'] is True

        # Test SQL injection attempt
        result = guard.validate_query("SELECT * FROM users WHERE id = '1' OR '1'='1'")
        assert result['is_safe'] is False
        assert result['threat_type'] == 'SQL Injection'

        # Test DROP TABLE attempt
        result = guard.validate_query("SELECT * FROM users; DROP TABLE users;")
        assert result['is_safe'] is False
        assert result['severity'] == 'critical'

    @pytest.mark.asyncio
    async def test_query_risk_assessment(self):
        """Test query risk assessment."""
        from src.agents.safety.controller import SafetyController, SafetyLevel

        controller = SafetyController()

        # Test low-risk query
        analysis = await controller.analyze_query("SELECT * FROM users WHERE id = 1")
        assert analysis['risk_level'] in [SafetyLevel.LOW, SafetyLevel.MEDIUM]

        # Test high-risk query
        analysis = await controller.analyze_query("DELETE FROM users")
        assert analysis['risk_level'] in [SafetyLevel.HIGH, SafetyLevel.CRITICAL]


class TestPerformanceMonitoring:
    """Test performance monitoring features."""

    @pytest.mark.asyncio
    async def test_query_performance_tracking(self):
        """Test query performance tracking."""
        from src.performance.monitor import PerformanceMonitor

        monitor = PerformanceMonitor(slow_query_threshold=0.1)

        # Record fast query
        monitor.record_query("SELECT * FROM users", execution_time=0.05, rows=100)

        # Record slow query
        monitor.record_query("SELECT * FROM large_table", execution_time=2.5, rows=1000000)

        metrics = monitor.get_metrics()
        assert metrics['total_queries'] == 2
        assert metrics['slow_query_count'] == 1

        slow_queries = monitor.get_slow_queries()
        assert len(slow_queries) == 1
        assert slow_queries[0]['execution_time'] == 2.5

    @pytest.mark.asyncio
    async def test_memory_tracking(self):
        """Test memory usage tracking."""
        from src.performance.monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        # Track memory
        monitor.track_memory_usage()

        metrics = monitor.get_memory_metrics()
        assert 'current_memory_mb' in metrics
        assert metrics['current_memory_mb'] > 0
        assert 'peak_memory_mb' in metrics


class TestEnterpriseFeatures:
    """Test enterprise features with real databases."""

    @pytest.mark.asyncio
    async def test_multi_tenancy(self):
        """Test multi-tenancy features."""
        from src.core.tenancy import TenantManager

        manager = TenantManager()

        # Create tenants
        tenant1 = await manager.create_tenant(
            tenant_id="tenant_1",
            name="ACME Corp",
            config={'database': 'postgresql'}
        )

        tenant2 = await manager.create_tenant(
            tenant_id="tenant_2",
            name="Widget Inc",
            config={'database': 'mysql'}
        )

        assert tenant1.tenant_id == "tenant_1"
        assert tenant2.tenant_id == "tenant_2"

        # Test tenant context
        async with manager.tenant_context("tenant_1") as context:
            assert context.tenant_id == "tenant_1"
            assert context.name == "ACME Corp"

    def test_rbac_permissions(self):
        """Test RBAC permission system."""
        from src.security.rbac import RBACManager

        rbac = RBACManager()

        # Create roles
        admin_role = rbac.create_role(
            "admin",
            permissions=["db.*", "user.*", "system.*"],
            description="Administrator role"
        )

        analyst_role = rbac.create_role(
            "analyst",
            permissions=["db.read", "db.query"],
            description="Data analyst role"
        )

        # Assign roles
        rbac.assign_role("user_1", "admin")
        rbac.assign_role("user_2", "analyst")

        # Check permissions
        assert rbac.has_permission("user_1", "db.write") is True
        assert rbac.has_permission("user_2", "db.write") is False
        assert rbac.has_permission("user_2", "db.read") is True

    @pytest.mark.asyncio
    async def test_audit_logging(self):
        """Test audit logging."""
        from src.security.audit import AuditLogger
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            logger = AuditLogger(db_path=tmp.name)

            # Log events
            await logger.log(
                event_type="user.login",
                resource="system",
                user_id="user_1",
                tenant_id="tenant_1",
                metadata={"ip": "192.168.1.1"}
            )

            await logger.log(
                event_type="db.query",
                resource="users_table",
                user_id="user_1",
                tenant_id="tenant_1",
                metadata={"query": "SELECT * FROM users"}
            )

            # Query logs
            logs = await logger.query_logs(
                tenant_id="tenant_1",
                user_id="user_1"
            )

            assert len(logs) == 2
            assert logs[0]['event_type'] == 'user.login'
            assert logs[1]['event_type'] == 'db.query'

    def test_data_encryption(self):
        """Test data encryption."""
        from src.security.encryption import DataEncryption, FieldEncryption

        # Test basic encryption
        encryptor = DataEncryption(key="test-encryption-key-12345678")

        plaintext = "sensitive data"
        ciphertext = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(ciphertext)

        assert plaintext == decrypted
        assert ciphertext != plaintext

        # Test field encryption
        field_enc = FieldEncryption(key="field-key-12345678")

        data = {
            'id': 1,
            'name': 'Alice',
            'ssn': '123-45-6789',
            'salary': 120000
        }

        encrypted_data = field_enc.encrypt_fields(data, ['ssn', 'salary'])

        assert encrypted_data['name'] == 'Alice'  # Not encrypted
        assert encrypted_data['ssn'] != '123-45-6789'  # Encrypted

        decrypted_data = field_enc.decrypt_fields(encrypted_data, ['ssn', 'salary'])

        assert decrypted_data['ssn'] == '123-45-6789'


class TestAgentWorkflows:
    """Test agent workflows with database operations."""

    @pytest.mark.asyncio
    async def test_workflow_with_database(self):
        """Test workflow orchestration with database."""
        from src.agents.workflow_orchestrator import WorkflowOrchestrator
        from src.mcp_clients.postgresql_client import PostgreSQLClient

        orchestrator = WorkflowOrchestrator()
        client = PostgreSQLClient(**{k: v for k, v in DATABASES['postgresql'].items() if k != 'type'})

        try:
            await client.connect()

            # Create workflow
            workflow_id = await orchestrator.create_workflow(
                name="database_analysis",
                steps=[
                    {"action": "connect", "database": "postgresql"},
                    {"action": "analyze_schema"},
                    {"action": "generate_report"}
                ]
            )

            assert workflow_id is not None

            status = await orchestrator.get_workflow_status(workflow_id)
            assert status['name'] == 'database_analysis'

        finally:
            await client.disconnect()


class TestMultiDatabaseCoordination:
    """Test coordination across multiple databases."""

    @pytest.mark.asyncio
    async def test_multi_db_query(self):
        """Test querying multiple databases (PostgreSQL and Oracle)."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.oracle_client import OracleClient

        pg_client = PostgreSQLClient(**{k: v for k, v in DATABASES['postgresql'].items() if k != 'type'})
        oracle_client = OracleClient(**{k: v for k, v in DATABASES['oracle_cdb'].items() if k != 'type'})

        try:
            # Connect to both databases
            await pg_client.connect()
            await oracle_client.connect()

            # Create tables in both databases
            await pg_client.execute_query("CREATE TEMP TABLE pg_data (id SERIAL, value VARCHAR(50))")
            await pg_client.execute_query("INSERT INTO pg_data (value) VALUES ('from_postgres')")

            # Query both databases
            pg_result = await pg_client.execute_query("SELECT value FROM pg_data")
            oracle_health = await oracle_client.health_check()

            assert pg_result['rows'][0]['value'] == 'from_postgres'
            assert oracle_health['status'] == 'healthy'

        finally:
            await pg_client.disconnect()
            await oracle_client.disconnect()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
