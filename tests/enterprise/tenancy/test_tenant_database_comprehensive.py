"""
Comprehensive tests for tenant_database.py

Tests:
- Database isolation strategies
- Per-tenant connections
- Query isolation
- Cross-tenant data protection
- Database backup and restore
- Tenant database statistics
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from src.enterprise.tenancy.tenant_database import (
    TenantDatabaseManager,
    TenantSchema,
    IsolationStrategy,
)


@pytest.fixture
def temp_db_dir():
    """Create temporary directory for databases"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def db_manager_per_tenant(temp_db_dir):
    """Create manager with DATABASE_PER_TENANT strategy"""
    return TenantDatabaseManager(
        base_db_path=temp_db_dir,
        isolation_strategy=IsolationStrategy.DATABASE_PER_TENANT,
    )


@pytest.fixture
def db_manager_shared(temp_db_dir):
    """Create manager with SHARED_DATABASE strategy"""
    return TenantDatabaseManager(
        base_db_path=temp_db_dir,
        isolation_strategy=IsolationStrategy.SHARED_DATABASE,
    )


@pytest.fixture
def db_manager_schema(temp_db_dir):
    """Create manager with SCHEMA_PER_TENANT strategy"""
    return TenantDatabaseManager(
        base_db_path=temp_db_dir,
        isolation_strategy=IsolationStrategy.SCHEMA_PER_TENANT,
    )


class TestDatabaseCreation:
    """Test tenant database creation"""

    def test_create_database_per_tenant(self, db_manager_per_tenant):
        """Test creating separate database per tenant"""
        schema = db_manager_per_tenant.create_tenant_database("tenant_123")

        assert schema.tenant_id == "tenant_123"
        assert schema.isolation_strategy == IsolationStrategy.DATABASE_PER_TENANT
        assert Path(schema.connection_string).exists()

    def test_create_database_shared(self, db_manager_shared):
        """Test creating tenant in shared database"""
        schema = db_manager_shared.create_tenant_database("tenant_456")

        assert schema.tenant_id == "tenant_456"
        assert schema.isolation_strategy == IsolationStrategy.SHARED_DATABASE
        assert Path(schema.connection_string).exists()

    def test_create_database_schema_per_tenant(self, db_manager_schema):
        """Test creating schema per tenant"""
        schema = db_manager_schema.create_tenant_database("tenant_789")

        assert schema.tenant_id == "tenant_789"
        assert schema.isolation_strategy == IsolationStrategy.SCHEMA_PER_TENANT

    def test_create_database_custom_schema_name(self, db_manager_per_tenant):
        """Test creating database with custom schema name"""
        schema = db_manager_per_tenant.create_tenant_database(
            "tenant_custom",
            schema_name="custom_schema_name"
        )

        assert schema.schema_name == "custom_schema_name"

    def test_multiple_tenants_separate_databases(self, db_manager_per_tenant):
        """Test multiple tenants get separate databases"""
        schema1 = db_manager_per_tenant.create_tenant_database("tenant_a")
        schema2 = db_manager_per_tenant.create_tenant_database("tenant_b")

        assert schema1.connection_string != schema2.connection_string
        assert Path(schema1.connection_string).exists()
        assert Path(schema2.connection_string).exists()


class TestDatabaseConnections:
    """Test database connection management"""

    def test_get_tenant_connection_per_tenant(self, db_manager_per_tenant):
        """Test getting connection for per-tenant database"""
        db_manager_per_tenant.create_tenant_database("tenant_conn")

        conn = db_manager_per_tenant.get_tenant_connection("tenant_conn")

        assert conn is not None
        conn.close()

    def test_get_tenant_connection_readonly(self, db_manager_per_tenant):
        """Test getting read-only connection"""
        db_manager_per_tenant.create_tenant_database("tenant_readonly")

        conn = db_manager_per_tenant.get_tenant_connection(
            "tenant_readonly",
            readonly=True
        )

        assert conn is not None

        # Verify it's read-only by attempting write (should fail)
        with pytest.raises(Exception):
            conn.execute("INSERT INTO queries (query, executed_at) VALUES ('test', 'now')")

        conn.close()

    def test_get_connection_nonexistent_tenant(self, db_manager_per_tenant):
        """Test getting connection for non-existent tenant raises error"""
        with pytest.raises(ValueError, match="not found"):
            db_manager_per_tenant.get_tenant_connection("nonexistent_tenant")

    def test_connection_shared_database(self, db_manager_shared):
        """Test connection for shared database"""
        db_manager_shared.create_tenant_database("tenant_shared")

        conn = db_manager_shared.get_tenant_connection("tenant_shared")

        assert conn is not None
        conn.close()


class TestQueryExecution:
    """Test query execution with tenant isolation"""

    def test_execute_query_insert(self, db_manager_per_tenant):
        """Test executing INSERT query"""
        db_manager_per_tenant.create_tenant_database("tenant_insert")

        result = db_manager_per_tenant.execute_tenant_query(
            "tenant_insert",
            "INSERT INTO queries (query, executed_at) VALUES (?, ?)",
            ("SELECT * FROM users", "2024-01-01T00:00:00")
        )

        assert result[0]['rows_affected'] == 1

    def test_execute_query_select(self, db_manager_per_tenant):
        """Test executing SELECT query"""
        db_manager_per_tenant.create_tenant_database("tenant_select")

        # Insert data
        db_manager_per_tenant.execute_tenant_query(
            "tenant_select",
            "INSERT INTO queries (query, executed_at) VALUES (?, ?)",
            ("SELECT 1", "2024-01-01T00:00:00")
        )

        # Select data
        result = db_manager_per_tenant.execute_tenant_query(
            "tenant_select",
            "SELECT * FROM queries"
        )

        assert len(result) > 0
        assert 'query' in result[0]

    def test_query_isolation_per_tenant(self, db_manager_per_tenant):
        """Test queries are isolated between tenants"""
        db_manager_per_tenant.create_tenant_database("tenant_a")
        db_manager_per_tenant.create_tenant_database("tenant_b")

        # Insert in tenant A
        db_manager_per_tenant.execute_tenant_query(
            "tenant_a",
            "INSERT INTO queries (query, executed_at) VALUES (?, ?)",
            ("Query A", "2024-01-01T00:00:00")
        )

        # Insert in tenant B
        db_manager_per_tenant.execute_tenant_query(
            "tenant_b",
            "INSERT INTO queries (query, executed_at) VALUES (?, ?)",
            ("Query B", "2024-01-01T00:00:00")
        )

        # Verify isolation
        result_a = db_manager_per_tenant.execute_tenant_query(
            "tenant_a",
            "SELECT * FROM queries"
        )
        result_b = db_manager_per_tenant.execute_tenant_query(
            "tenant_b",
            "SELECT * FROM queries"
        )

        assert len(result_a) == 1
        assert len(result_b) == 1
        assert result_a[0]['query'] == "Query A"
        assert result_b[0]['query'] == "Query B"

    def test_query_rewriting_shared_database(self, db_manager_shared):
        """Test query rewriting for shared database isolation"""
        db_manager_shared.create_tenant_database("tenant_x")
        db_manager_shared.create_tenant_database("tenant_y")

        # Insert for both tenants
        db_manager_shared.execute_tenant_query(
            "tenant_x",
            "INSERT INTO queries (tenant_id, query, executed_at) VALUES (?, ?, ?)",
            ("tenant_x", "Query X", "2024-01-01")
        )
        db_manager_shared.execute_tenant_query(
            "tenant_y",
            "INSERT INTO queries (tenant_id, query, executed_at) VALUES (?, ?, ?)",
            ("tenant_y", "Query Y", "2024-01-01")
        )

        # Query should be automatically filtered by tenant_id
        result_x = db_manager_shared.execute_tenant_query(
            "tenant_x",
            "SELECT * FROM queries"
        )

        # Verify only tenant_x data is returned
        assert all(row['tenant_id'] == 'tenant_x' for row in result_x)


class TestTenantDataIsolation:
    """Test cross-tenant data protection"""

    def test_no_cross_tenant_data_leakage(self, db_manager_per_tenant):
        """Test tenants cannot access each other's data"""
        db_manager_per_tenant.create_tenant_database("tenant_1")
        db_manager_per_tenant.create_tenant_database("tenant_2")

        # Insert sensitive data for tenant 1
        db_manager_per_tenant.execute_tenant_query(
            "tenant_1",
            "INSERT INTO user_data (user_id, username, email, created_at) VALUES (?, ?, ?, ?)",
            ("user_1", "alice", "alice@tenant1.com", "2024-01-01")
        )

        # Try to access from tenant 2
        result = db_manager_per_tenant.execute_tenant_query(
            "tenant_2",
            "SELECT * FROM user_data"
        )

        # Should be empty (no data leakage)
        assert len(result) == 0

    def test_shared_database_isolation(self, db_manager_shared):
        """Test shared database properly isolates tenant data"""
        db_manager_shared.create_tenant_database("tenant_alpha")
        db_manager_shared.create_tenant_database("tenant_beta")

        # Insert for alpha
        db_manager_shared.execute_tenant_query(
            "tenant_alpha",
            "INSERT INTO queries (tenant_id, query, executed_at) VALUES (?, ?, ?)",
            ("tenant_alpha", "Alpha Query", "2024-01-01")
        )

        # Query from beta should not see alpha's data
        result = db_manager_shared.execute_tenant_query(
            "tenant_beta",
            "SELECT * FROM queries WHERE query = ?",
            ("Alpha Query",)
        )

        assert len(result) == 0


class TestDatabaseBackup:
    """Test database backup operations"""

    def test_backup_tenant_database(self, db_manager_per_tenant, temp_db_dir):
        """Test backing up tenant database"""
        db_manager_per_tenant.create_tenant_database("tenant_backup")

        # Insert some data
        db_manager_per_tenant.execute_tenant_query(
            "tenant_backup",
            "INSERT INTO queries (query, executed_at) VALUES (?, ?)",
            ("Backup Test", "2024-01-01")
        )

        backup_path = db_manager_per_tenant.backup_tenant_database("tenant_backup")

        assert backup_path is not None
        assert Path(backup_path).exists()
        assert Path(backup_path).stat().st_size > 0

    def test_backup_custom_path(self, db_manager_per_tenant, temp_db_dir):
        """Test backup with custom path"""
        db_manager_per_tenant.create_tenant_database("tenant_custom_backup")

        custom_backup = os.path.join(temp_db_dir, "custom_backup.db")

        backup_path = db_manager_per_tenant.backup_tenant_database(
            "tenant_custom_backup",
            backup_path=custom_backup
        )

        assert backup_path == custom_backup
        assert Path(custom_backup).exists()

    def test_backup_shared_database(self, db_manager_shared):
        """Test backing up tenant data from shared database"""
        db_manager_shared.create_tenant_database("tenant_shared_backup")

        # Insert data
        db_manager_shared.execute_tenant_query(
            "tenant_shared_backup",
            "INSERT INTO queries (tenant_id, query, executed_at) VALUES (?, ?, ?)",
            ("tenant_shared_backup", "Shared Backup", "2024-01-01")
        )

        backup_path = db_manager_shared.backup_tenant_database("tenant_shared_backup")

        assert Path(backup_path).exists()


class TestDatabaseDeletion:
    """Test database deletion operations"""

    def test_delete_tenant_database_per_tenant(self, db_manager_per_tenant):
        """Test deleting per-tenant database"""
        db_manager_per_tenant.create_tenant_database("tenant_delete")

        success = db_manager_per_tenant.delete_tenant_database("tenant_delete")

        assert success

        # Verify database is deleted
        with pytest.raises(ValueError):
            db_manager_per_tenant.get_tenant_connection("tenant_delete")

    def test_delete_tenant_data_shared(self, db_manager_shared):
        """Test deleting tenant data from shared database"""
        db_manager_shared.create_tenant_database("tenant_delete_shared")

        # Insert data
        db_manager_shared.execute_tenant_query(
            "tenant_delete_shared",
            "INSERT INTO queries (tenant_id, query, executed_at) VALUES (?, ?, ?)",
            ("tenant_delete_shared", "To Delete", "2024-01-01")
        )

        success = db_manager_shared.delete_tenant_database("tenant_delete_shared")

        assert success

        # Verify data is deleted
        result = db_manager_shared.execute_tenant_query(
            "tenant_delete_shared",
            "SELECT * FROM queries"
        )
        assert len(result) == 0


class TestDatabaseStatistics:
    """Test database statistics"""

    def test_get_tenant_stats_per_tenant(self, db_manager_per_tenant):
        """Test getting statistics for per-tenant database"""
        db_manager_per_tenant.create_tenant_database("tenant_stats")

        # Insert some queries
        for i in range(5):
            db_manager_per_tenant.execute_tenant_query(
                "tenant_stats",
                "INSERT INTO queries (query, executed_at) VALUES (?, ?)",
                (f"Query {i}", "2024-01-01")
            )

        stats = db_manager_per_tenant.get_tenant_stats("tenant_stats")

        assert stats['tenant_id'] == "tenant_stats"
        assert stats['query_count'] == 5
        assert stats['database_size_bytes'] > 0
        assert stats['isolation_strategy'] == IsolationStrategy.DATABASE_PER_TENANT.value

    def test_get_tenant_stats_shared(self, db_manager_shared):
        """Test statistics for shared database"""
        db_manager_shared.create_tenant_database("tenant_stats_shared")

        # Insert queries
        for i in range(3):
            db_manager_shared.execute_tenant_query(
                "tenant_stats_shared",
                "INSERT INTO queries (tenant_id, query, executed_at) VALUES (?, ?, ?)",
                ("tenant_stats_shared", f"Query {i}", "2024-01-01")
            )

        stats = db_manager_shared.get_tenant_stats("tenant_stats_shared")

        assert stats['query_count'] == 3
        assert stats['isolation_strategy'] == IsolationStrategy.SHARED_DATABASE.value


class TestIsolationStrategies:
    """Test different isolation strategies"""

    def test_database_per_tenant_strategy(self, temp_db_dir):
        """Test DATABASE_PER_TENANT creates separate files"""
        manager = TenantDatabaseManager(
            base_db_path=temp_db_dir,
            isolation_strategy=IsolationStrategy.DATABASE_PER_TENANT
        )

        manager.create_tenant_database("tenant_1")
        manager.create_tenant_database("tenant_2")

        db_files = list(Path(temp_db_dir).glob("*.db"))
        assert len(db_files) >= 2

    def test_shared_database_strategy(self, temp_db_dir):
        """Test SHARED_DATABASE uses single file"""
        manager = TenantDatabaseManager(
            base_db_path=temp_db_dir,
            isolation_strategy=IsolationStrategy.SHARED_DATABASE
        )

        manager.create_tenant_database("tenant_1")
        manager.create_tenant_database("tenant_2")

        # Should have single shared.db file
        shared_db = Path(temp_db_dir) / "shared.db"
        assert shared_db.exists()

    def test_schema_per_tenant_strategy(self, temp_db_dir):
        """Test SCHEMA_PER_TENANT isolation"""
        manager = TenantDatabaseManager(
            base_db_path=temp_db_dir,
            isolation_strategy=IsolationStrategy.SCHEMA_PER_TENANT
        )

        schema1 = manager.create_tenant_database("tenant_1")
        schema2 = manager.create_tenant_database("tenant_2")

        assert schema1.isolation_strategy == IsolationStrategy.SCHEMA_PER_TENANT
        assert schema2.isolation_strategy == IsolationStrategy.SCHEMA_PER_TENANT
        assert schema1.connection_string != schema2.connection_string


class TestTenantSchemaDataclass:
    """Test TenantSchema dataclass"""

    def test_tenant_schema_creation(self):
        """Test creating TenantSchema instance"""
        schema = TenantSchema(
            tenant_id="test_tenant",
            schema_name="test_schema",
            isolation_strategy=IsolationStrategy.DATABASE_PER_TENANT,
            connection_string="/path/to/db.db",
            max_connections=10
        )

        assert schema.tenant_id == "test_tenant"
        assert schema.schema_name == "test_schema"
        assert schema.max_connections == 10
        assert schema.metadata == {}

    def test_tenant_schema_metadata(self):
        """Test TenantSchema with metadata"""
        schema = TenantSchema(
            tenant_id="test",
            schema_name="test",
            isolation_strategy=IsolationStrategy.SHARED_DATABASE,
            connection_string="connection",
            metadata={'key': 'value'}
        )

        assert schema.metadata['key'] == 'value'
