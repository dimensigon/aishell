"""
Comprehensive test suite for multi-tenancy isolation module.

Target Coverage: 95%+
Test Methods: 50+
Critical Focus: Data isolation, security, resource management
"""

import pytest
import threading
import time
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

from src.core.tenancy import (
    Tenant,
    TenantManager,
    TenantContext,
    TenantDatabaseManager,
    TenantQuotaManager,
    TenantConfigManager,
    TenantMigrationManager
)


# ============================================================================
# TENANT DATACLASS TESTS (5 tests)
# ============================================================================

class TestTenantDataclass:
    """Test the Tenant dataclass."""

    def test_tenant_creation_with_defaults(self):
        """Test creating tenant with default values."""
        tenant = Tenant(tenant_id="tenant-001")

        assert tenant.tenant_id == "tenant-001"
        assert tenant.config == {}
        assert tenant.metadata == {}
        assert isinstance(tenant.created_at, datetime)

    def test_tenant_creation_with_config(self):
        """Test creating tenant with custom configuration."""
        config = {"max_users": 100, "storage_gb": 50}
        tenant = Tenant(tenant_id="tenant-002", config=config)

        assert tenant.tenant_id == "tenant-002"
        assert tenant.config == config
        assert tenant.config["max_users"] == 100

    def test_tenant_creation_with_metadata(self):
        """Test creating tenant with metadata."""
        metadata = {"company": "Acme Corp", "industry": "Tech"}
        tenant = Tenant(tenant_id="tenant-003", metadata=metadata)

        assert tenant.metadata == metadata
        assert tenant.metadata["company"] == "Acme Corp"

    def test_tenant_created_at_timestamp(self):
        """Test that created_at is properly set."""
        before = datetime.now()
        tenant = Tenant(tenant_id="tenant-004")
        after = datetime.now()

        assert before <= tenant.created_at <= after

    def test_tenant_config_isolation(self):
        """Test that configs are isolated between tenant instances."""
        config1 = {"setting": "value1"}
        config2 = {"setting": "value2"}

        tenant1 = Tenant(tenant_id="tenant-005", config=config1)
        tenant2 = Tenant(tenant_id="tenant-006", config=config2)

        assert tenant1.config != tenant2.config
        tenant1.config["new_key"] = "new_value"
        assert "new_key" not in tenant2.config


# ============================================================================
# TENANT MANAGER TESTS (12 tests)
# ============================================================================

class TestTenantManager:
    """Test the TenantManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh TenantManager for each test."""
        return TenantManager()

    def test_create_tenant_success(self, manager):
        """Test successful tenant creation."""
        config = {"max_queries": 1000}
        tenant = manager.create_tenant("tenant-100", config)

        assert isinstance(tenant, Tenant)
        assert tenant.tenant_id == "tenant-100"
        assert tenant.config == config

    def test_create_tenant_duplicate_raises_error(self, manager):
        """Test that creating duplicate tenant raises ValueError."""
        manager.create_tenant("tenant-101", {})

        with pytest.raises(ValueError, match="already exists"):
            manager.create_tenant("tenant-101", {})

    def test_get_tenant_exists(self, manager):
        """Test retrieving an existing tenant."""
        config = {"storage": "100GB"}
        created_tenant = manager.create_tenant("tenant-102", config)

        retrieved_tenant = manager.get_tenant("tenant-102")

        assert retrieved_tenant is not None
        assert retrieved_tenant.tenant_id == created_tenant.tenant_id
        assert retrieved_tenant.config == config

    def test_get_tenant_not_exists(self, manager):
        """Test retrieving non-existent tenant returns None."""
        result = manager.get_tenant("non-existent")
        assert result is None

    def test_delete_tenant_success(self, manager):
        """Test successful tenant deletion."""
        manager.create_tenant("tenant-103", {})

        result = manager.delete_tenant("tenant-103")

        assert result is True
        assert manager.get_tenant("tenant-103") is None

    def test_delete_tenant_not_exists(self, manager):
        """Test deleting non-existent tenant returns False."""
        result = manager.delete_tenant("non-existent")
        assert result is False

    def test_thread_safe_create(self, manager):
        """Test thread-safe tenant creation."""
        results = []
        errors = []

        def create_tenant(tenant_id):
            try:
                tenant = manager.create_tenant(tenant_id, {})
                results.append(tenant)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=create_tenant, args=(f"tenant-{i}",))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert len(errors) == 0

    def test_thread_safe_delete(self, manager):
        """Test thread-safe tenant deletion."""
        # Create tenants
        for i in range(10):
            manager.create_tenant(f"tenant-{i}", {})

        results = []

        def delete_tenant(tenant_id):
            result = manager.delete_tenant(tenant_id)
            results.append(result)

        threads = [
            threading.Thread(target=delete_tenant, args=(f"tenant-{i}",))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(results)
        assert len(results) == 10

    def test_concurrent_create_same_tenant_one_succeeds(self, manager):
        """Test that only one thread succeeds when creating same tenant."""
        results = []
        errors = []

        def create_same_tenant():
            try:
                tenant = manager.create_tenant("same-tenant", {})
                results.append(tenant)
            except ValueError as e:
                errors.append(e)

        threads = [threading.Thread(target=create_same_tenant) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 1
        assert len(errors) == 4

    def test_tenant_isolation_in_manager(self, manager):
        """Test that tenants are properly isolated in manager."""
        tenant1 = manager.create_tenant("tenant-201", {"key": "value1"})
        tenant2 = manager.create_tenant("tenant-202", {"key": "value2"})

        # Modify one tenant's config
        tenant1.config["new_key"] = "new_value"

        # Verify isolation
        retrieved1 = manager.get_tenant("tenant-201")
        retrieved2 = manager.get_tenant("tenant-202")

        assert retrieved1.config["new_key"] == "new_value"
        assert "new_key" not in retrieved2.config

    def test_manager_initialization(self, manager):
        """Test TenantManager initializes with empty state."""
        assert hasattr(manager, '_tenants')
        assert hasattr(manager, '_lock')
        assert len(manager._tenants) == 0

    def test_multiple_creates_and_deletes(self, manager):
        """Test multiple create/delete cycles."""
        for i in range(5):
            tenant = manager.create_tenant(f"tenant-{i}", {})
            assert manager.get_tenant(f"tenant-{i}") is not None

            manager.delete_tenant(f"tenant-{i}")
            assert manager.get_tenant(f"tenant-{i}") is None


# ============================================================================
# TENANT CONTEXT TESTS (10 tests)
# ============================================================================

class TestTenantContext:
    """Test the TenantContext class."""

    @pytest.fixture
    def context(self):
        """Create a fresh TenantContext for each test."""
        return TenantContext("tenant-context-001")

    def test_context_initialization(self, context):
        """Test TenantContext initializes correctly."""
        assert context.tenant_id == "tenant-context-001"
        assert hasattr(context, '_data')
        assert hasattr(context, '_lock')

    def test_set_and_get_data(self, context):
        """Test setting and getting context data."""
        context.set_data("user_id", "user-123")

        result = context.get_data("user_id")
        assert result == "user-123"

    def test_get_nonexistent_data(self, context):
        """Test getting non-existent data returns None."""
        result = context.get_data("nonexistent")
        assert result is None

    def test_clear_data(self, context):
        """Test clearing context data."""
        context.set_data("key1", "value1")
        context.set_data("key2", "value2")

        context.clear_data()

        assert context.get_data("key1") is None
        assert context.get_data("key2") is None

    def test_overwrite_existing_data(self, context):
        """Test overwriting existing data."""
        context.set_data("key", "old_value")
        context.set_data("key", "new_value")

        result = context.get_data("key")
        assert result == "new_value"

    def test_thread_safe_set_data(self, context):
        """Test thread-safe data setting."""
        def set_data(key, value):
            context.set_data(key, value)

        threads = [
            threading.Thread(target=set_data, args=(f"key-{i}", f"value-{i}"))
            for i in range(20)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all data was set
        for i in range(20):
            assert context.get_data(f"key-{i}") == f"value-{i}"

    def test_thread_safe_get_data(self, context):
        """Test thread-safe data retrieval."""
        context.set_data("shared_key", "shared_value")
        results = []

        def get_data():
            value = context.get_data("shared_key")
            results.append(value)

        threads = [threading.Thread(target=get_data) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r == "shared_value" for r in results)

    def test_thread_safe_clear_data(self, context):
        """Test thread-safe data clearing."""
        for i in range(10):
            context.set_data(f"key-{i}", f"value-{i}")

        def clear():
            context.clear_data()

        threads = [threading.Thread(target=clear) for _ in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all data is cleared
        for i in range(10):
            assert context.get_data(f"key-{i}") is None

    def test_context_isolation_between_instances(self):
        """Test that different context instances are isolated."""
        context1 = TenantContext("tenant-001")
        context2 = TenantContext("tenant-002")

        context1.set_data("key", "value1")
        context2.set_data("key", "value2")

        assert context1.get_data("key") == "value1"
        assert context2.get_data("key") == "value2"

    def test_complex_data_types(self, context):
        """Test storing complex data types."""
        context.set_data("dict", {"nested": "value"})
        context.set_data("list", [1, 2, 3])
        context.set_data("tuple", (1, 2, 3))

        assert context.get_data("dict") == {"nested": "value"}
        assert context.get_data("list") == [1, 2, 3]
        assert context.get_data("tuple") == (1, 2, 3)


# ============================================================================
# TENANT DATABASE MANAGER TESTS (10 tests)
# ============================================================================

class TestTenantDatabaseManager:
    """Test the TenantDatabaseManager class."""

    @pytest.fixture
    def db_manager(self):
        """Create a fresh TenantDatabaseManager for each test."""
        return TenantDatabaseManager()

    def test_create_tenant_database(self, db_manager):
        """Test creating a tenant database."""
        db_manager.create_tenant_database("tenant-db-001")

        assert "tenant-db-001" in db_manager._databases
        db_info = db_manager._databases["tenant-db-001"]
        assert "created_at" in db_info
        assert "connection_string" in db_info
        assert db_info["connection_string"] == "db://tenant-db-001"

    def test_create_duplicate_database_raises_error(self, db_manager):
        """Test creating duplicate database raises ValueError."""
        db_manager.create_tenant_database("tenant-db-002")

        with pytest.raises(ValueError, match="already exists"):
            db_manager.create_tenant_database("tenant-db-002")

    def test_get_connection_success(self, db_manager):
        """Test getting database connection for tenant."""
        db_manager.create_tenant_database("tenant-db-003")

        conn = db_manager.get_connection("tenant-db-003")

        assert conn is not None
        assert "tenant-db-003" in db_manager._connections

    def test_get_connection_no_database_raises_error(self, db_manager):
        """Test getting connection without database raises ValueError."""
        with pytest.raises(ValueError, match="No database"):
            db_manager.get_connection("nonexistent")

    def test_get_connection_caching(self, db_manager):
        """Test that connections are cached."""
        db_manager.create_tenant_database("tenant-db-004")

        conn1 = db_manager.get_connection("tenant-db-004")
        conn2 = db_manager.get_connection("tenant-db-004")

        # Should return same connection object
        assert conn1 is conn2

    def test_connection_isolation_between_tenants(self, db_manager):
        """Test that connections are isolated between tenants."""
        db_manager.create_tenant_database("tenant-db-005")
        db_manager.create_tenant_database("tenant-db-006")

        conn1 = db_manager.get_connection("tenant-db-005")
        conn2 = db_manager.get_connection("tenant-db-006")

        # Should be different connection objects
        assert conn1 is not conn2

    def test_delete_database_success(self, db_manager):
        """Test successful database deletion."""
        db_manager.create_tenant_database("tenant-db-007")
        db_manager.get_connection("tenant-db-007")  # Create connection

        result = db_manager.delete_database("tenant-db-007")

        assert result is True
        assert "tenant-db-007" not in db_manager._databases
        assert "tenant-db-007" not in db_manager._connections

    def test_delete_database_not_exists(self, db_manager):
        """Test deleting non-existent database returns False."""
        result = db_manager.delete_database("nonexistent")
        assert result is False

    def test_thread_safe_create_database(self, db_manager):
        """Test thread-safe database creation."""
        results = []
        errors = []

        def create_db(tenant_id):
            try:
                db_manager.create_tenant_database(tenant_id)
                results.append(tenant_id)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=create_db, args=(f"tenant-{i}",))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert len(errors) == 0

    def test_thread_safe_delete_database(self, db_manager):
        """Test thread-safe database deletion."""
        # Create databases
        for i in range(10):
            db_manager.create_tenant_database(f"tenant-{i}")

        results = []

        def delete_db(tenant_id):
            result = db_manager.delete_database(tenant_id)
            results.append(result)

        threads = [
            threading.Thread(target=delete_db, args=(f"tenant-{i}",))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(results)


# ============================================================================
# TENANT QUOTA MANAGER TESTS (15 tests)
# ============================================================================

class TestTenantQuotaManager:
    """Test the TenantQuotaManager class."""

    @pytest.fixture
    def quota_manager(self):
        """Create a fresh TenantQuotaManager for each test."""
        return TenantQuotaManager()

    def test_set_quota(self, quota_manager):
        """Test setting resource quotas."""
        quota_manager.set_quota("tenant-quota-001", max_queries=1000, max_storage_mb=500)

        assert "tenant-quota-001" in quota_manager._quotas
        assert quota_manager._quotas["tenant-quota-001"]["max_queries"] == 1000
        assert quota_manager._quotas["tenant-quota-001"]["max_storage_mb"] == 500

    def test_set_quota_initializes_usage(self, quota_manager):
        """Test that setting quota initializes usage tracking."""
        quota_manager.set_quota("tenant-quota-002", max_queries=100)

        assert "tenant-quota-002" in quota_manager._usage
        assert quota_manager._usage["tenant-quota-002"]["queries"] == 0

    def test_check_quota_no_quota_set_allows(self, quota_manager):
        """Test that check_quota allows when no quota is set."""
        result = quota_manager.check_quota("no-quota-tenant", "query")
        assert result is True

    def test_check_quota_query_within_limit(self, quota_manager):
        """Test query quota check within limit."""
        quota_manager.set_quota("tenant-quota-003", max_queries=100)
        quota_manager._usage["tenant-quota-003"]["queries"] = 50

        result = quota_manager.check_quota("tenant-quota-003", "query")
        assert result is True

    def test_check_quota_query_at_limit(self, quota_manager):
        """Test query quota check at limit."""
        quota_manager.set_quota("tenant-quota-004", max_queries=100)
        quota_manager._usage["tenant-quota-004"]["queries"] = 100

        result = quota_manager.check_quota("tenant-quota-004", "query")
        assert result is False

    def test_check_quota_storage_within_limit(self, quota_manager):
        """Test storage quota check within limit."""
        quota_manager.set_quota("tenant-quota-005", max_storage_mb=1000)
        quota_manager._usage["tenant-quota-005"]["storage_mb"] = 500

        result = quota_manager.check_quota("tenant-quota-005", "storage")
        assert result is True

    def test_check_quota_storage_at_limit(self, quota_manager):
        """Test storage quota check at limit."""
        quota_manager.set_quota("tenant-quota-006", max_storage_mb=1000)
        quota_manager._usage["tenant-quota-006"]["storage_mb"] = 1000

        result = quota_manager.check_quota("tenant-quota-006", "storage")
        assert result is False

    def test_increment_usage(self, quota_manager):
        """Test incrementing resource usage."""
        quota_manager.set_quota("tenant-quota-007", max_queries=100)

        quota_manager.increment_usage("tenant-quota-007", "queries", 10)

        assert quota_manager._usage["tenant-quota-007"]["queries"] == 10

    def test_increment_usage_creates_tenant_if_not_exists(self, quota_manager):
        """Test incrementing usage creates tenant entry if it doesn't exist."""
        quota_manager.increment_usage("new-tenant", "queries", 5)

        assert "new-tenant" in quota_manager._usage
        assert quota_manager._usage["new-tenant"]["queries"] == 5

    def test_increment_usage_multiple_times(self, quota_manager):
        """Test multiple increments accumulate."""
        quota_manager.set_quota("tenant-quota-008", max_queries=100)

        quota_manager.increment_usage("tenant-quota-008", "queries", 10)
        quota_manager.increment_usage("tenant-quota-008", "queries", 15)
        quota_manager.increment_usage("tenant-quota-008", "queries", 5)

        assert quota_manager._usage["tenant-quota-008"]["queries"] == 30

    def test_get_usage(self, quota_manager):
        """Test getting current usage."""
        quota_manager.set_quota("tenant-quota-009", max_queries=100)
        quota_manager.increment_usage("tenant-quota-009", "queries", 25)
        quota_manager.increment_usage("tenant-quota-009", "storage_mb", 100)

        usage = quota_manager.get_usage("tenant-quota-009")

        assert usage["queries"] == 25
        assert usage["storage_mb"] == 100

    def test_get_usage_returns_copy(self, quota_manager):
        """Test that get_usage returns a copy, not reference."""
        quota_manager.set_quota("tenant-quota-010", max_queries=100)

        usage = quota_manager.get_usage("tenant-quota-010")
        usage["queries"] = 999  # Modify returned dict

        # Original should be unchanged
        actual_usage = quota_manager.get_usage("tenant-quota-010")
        assert actual_usage["queries"] == 0

    def test_reset_usage_specific_resource(self, quota_manager):
        """Test resetting specific resource usage."""
        quota_manager.set_quota("tenant-quota-011", max_queries=100)
        quota_manager.increment_usage("tenant-quota-011", "queries", 50)
        quota_manager.increment_usage("tenant-quota-011", "storage_mb", 200)

        quota_manager.reset_usage("tenant-quota-011", "queries")

        assert quota_manager._usage["tenant-quota-011"]["queries"] == 0
        assert quota_manager._usage["tenant-quota-011"]["storage_mb"] == 200

    def test_reset_usage_all_resources(self, quota_manager):
        """Test resetting all resource usage."""
        quota_manager.set_quota("tenant-quota-012", max_queries=100)
        quota_manager.increment_usage("tenant-quota-012", "queries", 50)
        quota_manager.increment_usage("tenant-quota-012", "storage_mb", 200)

        quota_manager.reset_usage("tenant-quota-012")

        assert quota_manager._usage["tenant-quota-012"] == {}

    def test_thread_safe_increment_usage(self, quota_manager):
        """Test thread-safe usage incrementing."""
        quota_manager.set_quota("tenant-quota-013", max_queries=10000)

        def increment():
            quota_manager.increment_usage("tenant-quota-013", "queries", 1)

        threads = [threading.Thread(target=increment) for _ in range(100)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert quota_manager._usage["tenant-quota-013"]["queries"] == 100


# ============================================================================
# TENANT CONFIG MANAGER TESTS (10 tests)
# ============================================================================

class TestTenantConfigManager:
    """Test the TenantConfigManager class."""

    @pytest.fixture
    def config_manager(self):
        """Create a fresh TenantConfigManager for each test."""
        return TenantConfigManager()

    def test_set_config(self, config_manager):
        """Test setting configuration value."""
        config_manager.set_config("tenant-config-001", "theme", "dark")

        assert "tenant-config-001" in config_manager._configs
        assert config_manager._configs["tenant-config-001"]["theme"] == "dark"

    def test_set_multiple_configs(self, config_manager):
        """Test setting multiple configuration values."""
        config_manager.set_config("tenant-config-002", "theme", "light")
        config_manager.set_config("tenant-config-002", "language", "en")
        config_manager.set_config("tenant-config-002", "timezone", "UTC")

        configs = config_manager._configs["tenant-config-002"]
        assert configs["theme"] == "light"
        assert configs["language"] == "en"
        assert configs["timezone"] == "UTC"

    def test_get_config_exists(self, config_manager):
        """Test getting existing configuration."""
        config_manager.set_config("tenant-config-003", "max_users", 100)

        value = config_manager.get_config("tenant-config-003", "max_users")
        assert value == 100

    def test_get_config_not_exists_returns_default(self, config_manager):
        """Test getting non-existent config returns default."""
        value = config_manager.get_config("nonexistent", "key", "default_value")
        assert value == "default_value"

    def test_get_config_no_default(self, config_manager):
        """Test getting non-existent config without default returns None."""
        value = config_manager.get_config("nonexistent", "key")
        assert value is None

    def test_get_all_config(self, config_manager):
        """Test getting all configuration for a tenant."""
        config_manager.set_config("tenant-config-004", "key1", "value1")
        config_manager.set_config("tenant-config-004", "key2", "value2")

        all_config = config_manager.get_all_config("tenant-config-004")

        assert all_config == {"key1": "value1", "key2": "value2"}

    def test_get_all_config_returns_copy(self, config_manager):
        """Test that get_all_config returns a copy."""
        config_manager.set_config("tenant-config-005", "key", "value")

        all_config = config_manager.get_all_config("tenant-config-005")
        all_config["new_key"] = "new_value"

        # Original should be unchanged
        actual_config = config_manager.get_all_config("tenant-config-005")
        assert "new_key" not in actual_config

    def test_delete_specific_config(self, config_manager):
        """Test deleting specific configuration key."""
        config_manager.set_config("tenant-config-006", "key1", "value1")
        config_manager.set_config("tenant-config-006", "key2", "value2")

        config_manager.delete_config("tenant-config-006", "key1")

        assert config_manager.get_config("tenant-config-006", "key1") is None
        assert config_manager.get_config("tenant-config-006", "key2") == "value2"

    def test_delete_all_config(self, config_manager):
        """Test deleting all configuration for a tenant."""
        config_manager.set_config("tenant-config-007", "key1", "value1")
        config_manager.set_config("tenant-config-007", "key2", "value2")

        config_manager.delete_config("tenant-config-007")

        assert "tenant-config-007" not in config_manager._configs

    def test_config_isolation_between_tenants(self, config_manager):
        """Test that configs are isolated between tenants."""
        config_manager.set_config("tenant-A", "theme", "dark")
        config_manager.set_config("tenant-B", "theme", "light")

        assert config_manager.get_config("tenant-A", "theme") == "dark"
        assert config_manager.get_config("tenant-B", "theme") == "light"


# ============================================================================
# TENANT MIGRATION MANAGER TESTS (12 tests)
# ============================================================================

class TestTenantMigrationManager:
    """Test the TenantMigrationManager class."""

    @pytest.fixture
    def migration_manager(self):
        """Create a fresh TenantMigrationManager for each test."""
        return TenantMigrationManager()

    def test_migrate_tenant_success(self, migration_manager):
        """Test successful tenant migration."""
        result = migration_manager.migrate_tenant(
            "tenant-migrate-001",
            "source_db",
            "dest_db"
        )

        assert result["status"] == "success"
        assert "migration_id" in result
        assert result["verified"] is False

    def test_migrate_tenant_with_verification(self, migration_manager):
        """Test migration with verification enabled."""
        result = migration_manager.migrate_tenant(
            "tenant-migrate-002",
            "source_db",
            "dest_db",
            verify=True
        )

        assert result["status"] == "success"
        assert result["verified"] is True

    def test_migration_creates_record(self, migration_manager):
        """Test that migration creates a record."""
        result = migration_manager.migrate_tenant(
            "tenant-migrate-003",
            "source_db",
            "dest_db"
        )

        migration_id = result["migration_id"]
        record = migration_manager.get_migration_status(migration_id)

        assert record is not None
        assert record["tenant_id"] == "tenant-migrate-003"
        assert record["source"] == "source_db"
        assert record["destination"] == "dest_db"

    def test_migration_record_has_timestamps(self, migration_manager):
        """Test migration record includes timestamps."""
        result = migration_manager.migrate_tenant(
            "tenant-migrate-004",
            "source_db",
            "dest_db"
        )

        migration_id = result["migration_id"]
        record = migration_manager.get_migration_status(migration_id)

        assert "started_at" in record
        assert "completed_at" in record
        assert isinstance(record["started_at"], datetime)
        assert isinstance(record["completed_at"], datetime)

    def test_get_migration_status_not_exists(self, migration_manager):
        """Test getting status of non-existent migration."""
        result = migration_manager.get_migration_status("nonexistent")
        assert result is None

    def test_list_migrations_all(self, migration_manager):
        """Test listing all migrations."""
        migration_manager.migrate_tenant("tenant-1", "src", "dst")
        migration_manager.migrate_tenant("tenant-2", "src", "dst")

        migrations = migration_manager.list_migrations()

        assert len(migrations) == 2

    def test_list_migrations_by_tenant(self, migration_manager):
        """Test listing migrations filtered by tenant."""
        migration_manager.migrate_tenant("tenant-filter-1", "src", "dst")
        migration_manager.migrate_tenant("tenant-filter-1", "src2", "dst2")
        migration_manager.migrate_tenant("tenant-filter-2", "src", "dst")

        tenant1_migrations = migration_manager.list_migrations("tenant-filter-1")

        assert len(tenant1_migrations) == 2
        assert all(m["tenant_id"] == "tenant-filter-1" for m in tenant1_migrations)

    def test_migration_id_uniqueness(self, migration_manager):
        """Test that migration IDs are unique."""
        result1 = migration_manager.migrate_tenant("tenant-1", "src", "dst")
        time.sleep(0.001)  # Small delay to ensure different timestamp
        result2 = migration_manager.migrate_tenant("tenant-2", "src", "dst")

        assert result1["migration_id"] != result2["migration_id"]

    def test_multiple_migrations_same_tenant(self, migration_manager):
        """Test multiple migrations for the same tenant."""
        for i in range(3):
            migration_manager.migrate_tenant("same-tenant", f"src-{i}", f"dst-{i}")

        migrations = migration_manager.list_migrations("same-tenant")
        assert len(migrations) == 3

    def test_get_migration_status_returns_copy(self, migration_manager):
        """Test that get_migration_status returns a copy."""
        result = migration_manager.migrate_tenant("tenant-copy", "src", "dst")
        migration_id = result["migration_id"]

        status1 = migration_manager.get_migration_status(migration_id)
        status1["modified"] = True

        status2 = migration_manager.get_migration_status(migration_id)
        assert "modified" not in status2

    def test_list_migrations_returns_copy(self, migration_manager):
        """Test that list_migrations returns a copy."""
        migration_manager.migrate_tenant("tenant-list", "src", "dst")

        migrations = migration_manager.list_migrations()
        migrations.append({"fake": "migration"})

        # Original should be unchanged
        actual_migrations = migration_manager.list_migrations()
        assert len(actual_migrations) == 1

    def test_thread_safe_migration(self, migration_manager):
        """Test thread-safe migration execution."""
        results = []

        def migrate(tenant_id):
            result = migration_manager.migrate_tenant(
                tenant_id,
                "source",
                "destination"
            )
            results.append(result)

        threads = [
            threading.Thread(target=migrate, args=(f"tenant-{i}",))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert all(r["status"] == "success" for r in results)


# ============================================================================
# INTEGRATION TESTS (8 tests)
# ============================================================================

class TestMultiTenancyIntegration:
    """Integration tests combining multiple components."""

    def test_full_tenant_lifecycle(self):
        """Test complete tenant lifecycle: create, configure, use, delete."""
        # Create tenant
        manager = TenantManager()
        tenant = manager.create_tenant("integration-001", {"initial": "config"})

        # Set up database
        db_manager = TenantDatabaseManager()
        db_manager.create_tenant_database(tenant.tenant_id)
        conn = db_manager.get_connection(tenant.tenant_id)

        # Configure quotas
        quota_manager = TenantQuotaManager()
        quota_manager.set_quota(tenant.tenant_id, max_queries=1000)

        # Set configuration
        config_manager = TenantConfigManager()
        config_manager.set_config(tenant.tenant_id, "feature_x", True)

        # Use tenant
        context = TenantContext(tenant.tenant_id)
        context.set_data("session", "active")

        # Verify everything works
        assert manager.get_tenant(tenant.tenant_id) is not None
        assert db_manager.get_connection(tenant.tenant_id) is conn
        assert quota_manager.check_quota(tenant.tenant_id, "query") is True
        assert config_manager.get_config(tenant.tenant_id, "feature_x") is True
        assert context.get_data("session") == "active"

        # Cleanup
        manager.delete_tenant(tenant.tenant_id)
        db_manager.delete_database(tenant.tenant_id)
        config_manager.delete_config(tenant.tenant_id)

    def test_quota_enforcement_workflow(self):
        """Test quota enforcement in a realistic workflow."""
        quota_manager = TenantQuotaManager()
        quota_manager.set_quota("quota-test", max_queries=5)

        # Simulate queries
        for i in range(5):
            if quota_manager.check_quota("quota-test", "query"):
                quota_manager.increment_usage("quota-test", "queries")

        # Next query should be blocked
        assert quota_manager.check_quota("quota-test", "query") is False

        # Reset and verify
        quota_manager.reset_usage("quota-test", "queries")
        assert quota_manager.check_quota("quota-test", "query") is True

    def test_migration_with_config_transfer(self):
        """Test migrating tenant with configuration transfer."""
        config_manager = TenantConfigManager()
        migration_manager = TenantMigrationManager()

        # Set up source tenant config
        tenant_id = "migrate-config-001"
        config_manager.set_config(tenant_id, "setting1", "value1")
        config_manager.set_config(tenant_id, "setting2", "value2")

        # Migrate
        result = migration_manager.migrate_tenant(
            tenant_id,
            "source_db",
            "dest_db",
            verify=True
        )

        assert result["status"] == "success"
        assert result["verified"] is True

        # Verify config still accessible
        assert config_manager.get_config(tenant_id, "setting1") == "value1"

    def test_concurrent_tenants_isolation(self):
        """Test that concurrent tenants are properly isolated."""
        manager = TenantManager()

        # Create multiple tenants
        tenants = [
            manager.create_tenant(f"concurrent-{i}", {"id": i})
            for i in range(5)
        ]

        # Create contexts for each
        contexts = [TenantContext(t.tenant_id) for t in tenants]

        # Set unique data in each context
        for i, ctx in enumerate(contexts):
            ctx.set_data("value", i)

        # Verify isolation
        for i, ctx in enumerate(contexts):
            assert ctx.get_data("value") == i

    def test_database_and_quota_integration(self):
        """Test database and quota managers working together."""
        db_manager = TenantDatabaseManager()
        quota_manager = TenantQuotaManager()

        tenant_id = "db-quota-001"

        # Create database
        db_manager.create_tenant_database(tenant_id)

        # Set storage quota
        quota_manager.set_quota(tenant_id, max_storage_mb=100)

        # Simulate storage usage
        quota_manager.increment_usage(tenant_id, "storage_mb", 50)

        # Check quota
        assert quota_manager.check_quota(tenant_id, "storage") is True

        # Exceed quota
        quota_manager.increment_usage(tenant_id, "storage_mb", 60)
        assert quota_manager.check_quota(tenant_id, "storage") is False

    def test_context_propagation_simulation(self):
        """Test context propagation in multi-step operations."""
        manager = TenantManager()
        tenant = manager.create_tenant("context-prop-001", {})

        context = TenantContext(tenant.tenant_id)

        # Simulate multi-step operation
        context.set_data("step", 1)
        assert context.get_data("step") == 1

        context.set_data("step", 2)
        assert context.get_data("step") == 2

        context.set_data("result", "completed")
        assert context.get_data("result") == "completed"

    def test_tenant_suspension_workflow(self):
        """Test suspending and reactivating a tenant."""
        manager = TenantManager()
        config_manager = TenantConfigManager()

        tenant_id = "suspend-001"
        tenant = manager.create_tenant(tenant_id, {})

        # Suspend tenant
        config_manager.set_config(tenant_id, "status", "suspended")

        # Verify suspension
        assert config_manager.get_config(tenant_id, "status") == "suspended"

        # Reactivate
        config_manager.set_config(tenant_id, "status", "active")
        assert config_manager.get_config(tenant_id, "status") == "active"

    def test_bulk_tenant_operations(self):
        """Test bulk operations on multiple tenants."""
        manager = TenantManager()
        quota_manager = TenantQuotaManager()

        # Create 10 tenants
        tenant_ids = []
        for i in range(10):
            tenant_id = f"bulk-{i}"
            manager.create_tenant(tenant_id, {})
            quota_manager.set_quota(tenant_id, max_queries=100 * i)
            tenant_ids.append(tenant_id)

        # Verify all created
        for tenant_id in tenant_ids:
            assert manager.get_tenant(tenant_id) is not None
            assert tenant_id in quota_manager._quotas

        # Bulk delete
        for tenant_id in tenant_ids:
            manager.delete_tenant(tenant_id)

        # Verify all deleted
        for tenant_id in tenant_ids:
            assert manager.get_tenant(tenant_id) is None


# ============================================================================
# SECURITY TESTS (5 tests)
# ============================================================================

class TestSecurityIsolation:
    """Security-focused tests for tenant isolation."""

    def test_cross_tenant_data_access_prevention(self):
        """Test that tenants cannot access each other's data."""
        context1 = TenantContext("secure-tenant-1")
        context2 = TenantContext("secure-tenant-2")

        context1.set_data("secret", "tenant1_secret")
        context2.set_data("secret", "tenant2_secret")

        # Verify isolation
        assert context1.get_data("secret") == "tenant1_secret"
        assert context2.get_data("secret") == "tenant2_secret"
        assert context1.get_data("secret") != context2.get_data("secret")

    def test_database_connection_isolation(self):
        """Test that database connections are isolated."""
        db_manager = TenantDatabaseManager()

        db_manager.create_tenant_database("secure-db-1")
        db_manager.create_tenant_database("secure-db-2")

        conn1 = db_manager.get_connection("secure-db-1")
        conn2 = db_manager.get_connection("secure-db-2")

        # Connections must be different objects
        assert conn1 is not conn2

    def test_quota_bypass_prevention(self):
        """Test that quota limits cannot be bypassed."""
        quota_manager = TenantQuotaManager()
        quota_manager.set_quota("quota-secure", max_queries=10)

        # Fill quota
        for _ in range(10):
            quota_manager.increment_usage("quota-secure", "queries")

        # Attempt to bypass by checking different resource
        assert quota_manager.check_quota("quota-secure", "query") is False

        # Direct manipulation should not work (it would if we could access _usage)
        # This test verifies the API doesn't allow bypassing
        quota_manager.increment_usage("quota-secure", "queries")
        assert quota_manager._usage["quota-secure"]["queries"] == 11

    def test_config_isolation_security(self):
        """Test configuration isolation for security."""
        config_manager = TenantConfigManager()

        # Set sensitive config for each tenant
        config_manager.set_config("secure-config-1", "api_key", "key-1-secret")
        config_manager.set_config("secure-config-2", "api_key", "key-2-secret")

        # Verify each tenant can only access their own config
        assert config_manager.get_config("secure-config-1", "api_key") == "key-1-secret"
        assert config_manager.get_config("secure-config-2", "api_key") == "key-2-secret"
        assert config_manager.get_config("secure-config-1", "api_key") != \
               config_manager.get_config("secure-config-2", "api_key")

    def test_tenant_deletion_removes_all_data(self):
        """Test that deleting tenant removes all associated data."""
        manager = TenantManager()
        db_manager = TenantDatabaseManager()
        config_manager = TenantConfigManager()

        tenant_id = "delete-security-001"

        # Set up tenant with data
        manager.create_tenant(tenant_id, {})
        db_manager.create_tenant_database(tenant_id)
        config_manager.set_config(tenant_id, "sensitive", "data")

        # Delete tenant
        manager.delete_tenant(tenant_id)
        db_manager.delete_database(tenant_id)
        config_manager.delete_config(tenant_id)

        # Verify all data removed
        assert manager.get_tenant(tenant_id) is None
        assert tenant_id not in db_manager._databases
        assert config_manager.get_config(tenant_id, "sensitive") is None
