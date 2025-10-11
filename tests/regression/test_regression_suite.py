"""
Regression Test Suite for AI-Shell

This suite ensures that previously working functionality
continues to work as expected across version updates.

Version Coverage: v1.0.1 → v2.0.0
"""

import pytest
import asyncio
from typing import Dict, Any


class TestDatabaseConnectivityRegression:
    """Regression tests for database connectivity (v1.0.1)."""

    @pytest.mark.asyncio
    async def test_postgresql_connection_lifecycle(self):
        """Verify PostgreSQL connection can connect and disconnect."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.base import ConnectionConfig

        client = PostgreSQLClient()
        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        # Connect
        success = await client.connect(config)
        assert success is True

        # Health check
        health = await client.health_check()
        assert health['connected'] is True
        assert health['state'] == 'connected'

        # Disconnect
        await client.disconnect()
        health = await client.health_check()
        assert health['connected'] is False

    @pytest.mark.asyncio
    async def test_oracle_cdb_connection_regression(self):
        """Verify Oracle CDB connection stability."""
        from src.mcp_clients.oracle_client import OracleClient
        from src.mcp_clients.base import ConnectionConfig

        client = OracleClient()
        config = ConnectionConfig(
            host='localhost',
            port=1521,
            database='free',
            username='SYS',
            password='MyOraclePass123',
            extra_params={'mode': 'SYSDBA'}
        )

        try:
            await client.connect(config)
            health = await client.health_check()
            assert health['connected'] is True
        finally:
            await client.disconnect()


class TestCRUDOperationsRegression:
    """Regression tests for CRUD operations (v1.0.1)."""

    @pytest.mark.asyncio
    async def test_postgresql_create_table(self):
        """Verify CREATE TABLE works without errors."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.base import ConnectionConfig

        client = PostgreSQLClient()
        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        try:
            await client.connect(config)

            result = await client.execute_query("""
                CREATE TEMP TABLE regression_test (
                    id SERIAL PRIMARY KEY,
                    data VARCHAR(100)
                )
            """)

            # DDL returns -1 or 0 for rowcount
            assert result.rowcount >= -1
            assert result.metadata['query_type'] == 'DDL'

        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_postgresql_insert_select_cycle(self):
        """Verify INSERT → SELECT data flow."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.base import ConnectionConfig

        client = PostgreSQLClient()
        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        try:
            await client.connect(config)

            # CREATE
            await client.execute_query("""
                CREATE TEMP TABLE data_test (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50)
                )
            """)

            # INSERT
            await client.execute_query(
                "INSERT INTO data_test (name) VALUES (%s)",
                ("TestValue",)
            )

            # SELECT
            result = await client.execute_query("SELECT name FROM data_test")

            assert len(result.rows) == 1
            assert result.rows[0][0] == "TestValue"

        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_postgresql_update_delete(self):
        """Verify UPDATE and DELETE operations."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.base import ConnectionConfig

        client = PostgreSQLClient()
        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        try:
            await client.connect(config)

            # Setup
            await client.execute_query("""
                CREATE TEMP TABLE update_test (
                    id SERIAL PRIMARY KEY,
                    status VARCHAR(20)
                )
            """)
            await client.execute_query(
                "INSERT INTO update_test (status) VALUES (%s)",
                ("active",)
            )

            # UPDATE
            result = await client.execute_query(
                "UPDATE update_test SET status = %s WHERE status = %s",
                ("inactive", "active")
            )
            assert result.rowcount == 1

            # DELETE
            result = await client.execute_query(
                "DELETE FROM update_test WHERE status = %s",
                ("inactive",)
            )
            assert result.rowcount == 1

            # Verify empty
            result = await client.execute_query("SELECT COUNT(*) FROM update_test")
            assert result.rows[0][0] == 0

        finally:
            await client.disconnect()


class TestSecurityRegression:
    """Regression tests for security features (v1.0.1)."""

    def test_sql_injection_detection_regression(self):
        """Verify SQL injection detection remains effective."""
        from src.security.sql_guard import SQLGuard

        guard = SQLGuard()

        # Safe query
        result = guard.validate_query("SELECT * FROM users WHERE id = ?")
        assert result['is_safe'] is True

        # OR 1=1 attack
        result = guard.validate_query("SELECT * FROM users WHERE id = '1' OR '1'='1'")
        assert result['is_safe'] is False
        assert result['threat_type'] == 'SQL Injection'

        # DROP TABLE attack
        result = guard.validate_query("SELECT *; DROP TABLE users;")
        assert result['is_safe'] is False
        assert result['severity'] in ['critical', 'high']

    def test_input_sanitization_regression(self):
        """Verify input sanitization prevents attacks."""
        from src.security.sql_guard import SQLGuard

        guard = SQLGuard()

        dangerous = "admin'; DROP TABLE users; --"
        sanitized = guard.sanitize_input(dangerous)

        # Should escape quotes and remove dangerous patterns
        assert dangerous != sanitized
        assert (sanitized.count("'") == 0) or ("''" in sanitized)


class TestNLPToSQLRegression:
    """Regression tests for NLP-to-SQL conversion (v1.1.0)."""

    def test_basic_select_patterns(self):
        """Verify basic SELECT patterns still work."""
        from src.database.nlp_to_sql import NLPToSQL

        nlp = NLPToSQL()

        # Pattern 1: show all <table>
        result = nlp.convert("show all users")
        assert result['sql'] is not None
        assert 'SELECT' in result['sql'].upper()
        assert 'users' in result['sql'].lower()
        assert result['confidence'] == 'high'

        # Pattern 2: list <table>
        result = nlp.convert("list products")
        assert result['sql'] is not None
        assert 'SELECT' in result['sql'].upper()
        assert 'products' in result['sql'].lower()

    def test_count_patterns(self):
        """Verify COUNT patterns work correctly."""
        from src.database.nlp_to_sql import NLPToSQL

        nlp = NLPToSQL()

        result = nlp.convert("count users")
        assert result['sql'] is not None
        assert 'COUNT(*)' in result['sql'].upper()

        result = nlp.convert("how many orders")
        assert result['sql'] is not None
        assert 'COUNT' in result['sql'].upper()

    def test_where_clause_patterns(self):
        """Verify WHERE clause generation."""
        from src.database.nlp_to_sql import NLPToSQL

        nlp = NLPToSQL()

        result = nlp.convert("find users where status is active")
        assert result['sql'] is not None
        assert 'WHERE' in result['sql'].upper()
        assert 'status' in result['sql'].lower()

    def test_unsupported_query_suggestions(self):
        """Verify unsupported queries return suggestions."""
        from src.database.nlp_to_sql import NLPToSQL

        nlp = NLPToSQL()

        result = nlp.convert("do something complex")
        assert result['sql'] is None
        assert result['confidence'] == 'none'
        assert 'error' in result
        assert 'suggestions' in result
        assert len(result['suggestions']) > 0

    def test_join_patterns(self):
        """Verify JOIN pattern support (v1.1.0+)."""
        from src.database.nlp_to_sql import NLPToSQL

        nlp = NLPToSQL()

        result = nlp.convert("show users and their orders")
        assert result['sql'] is not None
        assert 'JOIN' in result['sql'].upper()

    def test_aggregate_functions(self):
        """Verify aggregate function patterns."""
        from src.database.nlp_to_sql import NLPToSQL

        nlp = NLPToSQL()

        # AVG
        result = nlp.convert("average salary of employees")
        assert result['sql'] is not None
        assert 'AVG' in result['sql'].upper()

        # MAX
        result = nlp.convert("max price from products")
        assert result['sql'] is not None
        assert 'MAX' in result['sql'].upper()


class TestEnterpriseRegression:
    """Regression tests for enterprise features (v1.0.1+)."""

    def test_multi_tenancy_regression(self):
        """Verify tenant isolation."""
        from src.core.tenancy import TenantManager

        manager = TenantManager()

        tenant = manager.create_tenant(
            tenant_id="regression_test_1",
            config={'feature': 'value'}
        )

        assert tenant.tenant_id == "regression_test_1"
        assert tenant.config['feature'] == 'value'

        retrieved = manager.get_tenant("regression_test_1")
        assert retrieved is not None
        assert retrieved.tenant_id == "regression_test_1"

    def test_rbac_permissions_regression(self):
        """Verify RBAC permission checking."""
        from src.security.rbac import RBACManager

        rbac = RBACManager()

        # Create admin role
        rbac.create_role(
            "test_admin",
            permissions=["db.*", "user.*"],
            description="Test admin"
        )

        # Create read-only role
        rbac.create_role(
            "test_readonly",
            permissions=["db.read"],
            description="Test readonly"
        )

        # Assign roles
        rbac.assign_role("admin_user", "test_admin")
        rbac.assign_role("readonly_user", "test_readonly")

        # Verify permissions
        assert rbac.has_permission("admin_user", "db.write") is True
        assert rbac.has_permission("readonly_user", "db.write") is False
        assert rbac.has_permission("readonly_user", "db.read") is True

    def test_audit_logging_regression(self):
        """Verify audit log creation and retrieval."""
        from src.security.audit import AuditLogger

        logger = AuditLogger(retention_days=90)

        # Log action
        entry = logger.log_action(
            user="regression_test_user",
            action="regression.test",
            resource="test_resource",
            details={"test": "data"}
        )

        assert entry.user == "regression_test_user"
        assert entry.action == "regression.test"

        # Query logs
        logs = logger.search_logs(user="regression_test_user")
        assert len(logs) >= 1
        assert any(log['action'] == 'regression.test' for log in logs)

    def test_encryption_decryption_cycle(self):
        """Verify data encryption/decryption."""
        from src.security.encryption import DataEncryption

        key = "test-encryption-key-1234567890123"
        encryptor = DataEncryption(key=key)

        plaintext = "sensitive data"
        ciphertext = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(ciphertext)

        assert plaintext == decrypted
        assert ciphertext != plaintext


class TestPerformanceRegression:
    """Regression tests for performance monitoring (v1.0.1)."""

    def test_query_performance_tracking(self):
        """Verify query performance is tracked."""
        from src.performance.monitor import PerformanceMonitor

        monitor = PerformanceMonitor(slow_query_threshold=0.1)

        # Fast query
        monitor.record_query("SELECT 1", execution_time=0.01, rows=1)

        # Slow query
        monitor.record_query("SELECT * FROM large", execution_time=2.5, rows=1000000)

        metrics = monitor.get_metrics()
        assert metrics['total_queries'] == 2
        assert metrics['slow_query_count'] == 1

        slow_queries = monitor.get_slow_queries()
        assert len(slow_queries) == 1
        assert slow_queries[0]['execution_time'] == 2.5

    def test_memory_tracking(self):
        """Verify memory usage tracking."""
        from src.performance.monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        monitor.track_memory_usage()

        metrics = monitor.get_memory_metrics()
        assert 'current_memory_mb' in metrics
        assert metrics['current_memory_mb'] > 0

    def test_metrics_export(self):
        """Verify metrics can be exported."""
        from src.performance.monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        monitor.record_query("SELECT 1", execution_time=0.01, rows=1)
        monitor.track_memory_usage()

        export = monitor.export_metrics(format='json')
        assert 'queries' in export
        assert 'memory' in export


class TestBackupRestoreRegression:
    """Regression tests for backup/restore (v1.2.0)."""

    @pytest.mark.asyncio
    async def test_backup_planning(self):
        """Verify backup plans are created correctly."""
        from src.agents.database.backup import BackupAgent

        agent = BackupAgent()

        plan = await agent.plan_action({
            "action": "backup",
            "type": "full",
            "compression": True
        })

        assert len(plan) > 0
        assert any("backup" in step['action'].lower() for step in plan)

    @pytest.mark.asyncio
    async def test_restore_validation(self):
        """Verify restore plans include validation."""
        from src.agents.database.backup import BackupAgent

        agent = BackupAgent()

        plan = await agent.plan_action({
            "action": "restore",
            "backup_path": "/tmp/backup.sql"
        })

        assert len(plan) > 0
        assert any("validate" in step['action'].lower() for step in plan)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
