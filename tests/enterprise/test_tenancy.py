"""Tests for multi-tenancy features"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from src.enterprise.tenancy.tenant_manager import (
    TenantManager,
    Tenant,
    TenantStatus,
    TenantTier,
)
from src.enterprise.tenancy.resource_quota import (
    ResourceQuotaManager,
    QuotaType,
)
from src.enterprise.tenancy.tenant_database import (
    TenantDatabaseManager,
    IsolationStrategy,
)
from src.enterprise.tenancy.tenant_middleware import (
    TenantMiddleware,
    TenantValidator,
    with_tenant,
)


class TestTenantManager:
    """Test tenant management"""

    @pytest.fixture
    def manager(self):
        """Create tenant manager with temp database"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            db_path = f.name
        yield TenantManager(db_path=db_path)
        os.unlink(db_path)

    def test_create_tenant(self, manager):
        """Test tenant creation"""
        tenant = manager.create_tenant(
            name="Acme Corp",
            slug="acme",
            owner_id="user_1",
            tier=TenantTier.PROFESSIONAL,
        )

        assert tenant.id is not None
        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme"
        assert tenant.tier == TenantTier.PROFESSIONAL
        assert tenant.is_active()

    def test_get_tenant(self, manager):
        """Test retrieving tenant"""
        created = manager.create_tenant(
            name="Test Corp",
            slug="test",
            owner_id="user_1",
        )

        retrieved = manager.get_tenant(created.id)
        assert retrieved.id == created.id
        assert retrieved.name == "Test Corp"

    def test_get_tenant_by_slug(self, manager):
        """Test retrieving tenant by slug"""
        manager.create_tenant(
            name="Test Corp",
            slug="testcorp",
            owner_id="user_1",
        )

        tenant = manager.get_tenant_by_slug("testcorp")
        assert tenant is not None
        assert tenant.slug == "testcorp"

    def test_update_tenant(self, manager):
        """Test updating tenant"""
        tenant = manager.create_tenant(
            name="Old Name",
            slug="test",
            owner_id="user_1",
        )

        success = manager.update_tenant(
            tenant.id,
            name="New Name",
            max_users=50,
        )

        assert success
        updated = manager.get_tenant(tenant.id)
        assert updated.name == "New Name"
        assert updated.max_users == 50

    def test_delete_tenant(self, manager):
        """Test tenant deletion"""
        tenant = manager.create_tenant(
            name="To Delete",
            slug="delete",
            owner_id="user_1",
        )

        # Soft delete (archive)
        manager.delete_tenant(tenant.id, hard_delete=False)
        archived = manager.get_tenant(tenant.id)
        assert archived.status == TenantStatus.ARCHIVED

    def test_list_tenants(self, manager):
        """Test listing tenants"""
        manager.create_tenant("Tenant 1", "t1", "user_1")
        manager.create_tenant("Tenant 2", "t2", "user_1")

        tenants = manager.list_tenants()
        assert len(tenants) >= 2

    def test_tenant_features(self, manager):
        """Test tenant feature flags"""
        tenant = manager.create_tenant(
            name="Feature Test",
            slug="features",
            owner_id="user_1",
            tier=TenantTier.ENTERPRISE,
        )

        assert tenant.has_feature("audit_logs")
        assert tenant.has_feature("sso")
        assert not tenant.has_feature("nonexistent_feature")

    def test_trial_expiration(self, manager):
        """Test trial tenant expiration"""
        tenant = manager.create_tenant(
            name="Trial Tenant",
            slug="trial",
            owner_id="user_1",
            tier=TenantTier.FREE,
            trial_days=0,  # Expired immediately
        )

        # Set expiration to past
        manager.update_tenant(
            tenant.id,
            trial_ends_at=(datetime.now() - timedelta(days=1)).isoformat(),
        )

        expired_tenant = manager.get_tenant(tenant.id)
        assert not expired_tenant.is_active()


class TestResourceQuota:
    """Test resource quota management"""

    @pytest.fixture
    def manager(self):
        """Create quota manager"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            db_path = f.name
        yield ResourceQuotaManager(db_path=db_path)
        os.unlink(db_path)

    def test_set_quota(self, manager):
        """Test setting quota"""
        quota = manager.set_quota(
            tenant_id="tenant_1",
            quota_type=QuotaType.QUERIES_PER_HOUR,
            limit=1000,
            soft_limit=800,
        )

        assert quota.tenant_id == "tenant_1"
        assert quota.limit == 1000
        assert quota.soft_limit == 800

    def test_check_quota(self, manager):
        """Test checking quota"""
        manager.set_quota(
            tenant_id="tenant_1",
            quota_type=QuotaType.QUERIES_PER_MINUTE,
            limit=10,
        )

        result = manager.check_quota(
            tenant_id="tenant_1",
            quota_type=QuotaType.QUERIES_PER_MINUTE,
            amount=5,
        )

        assert result['allowed']
        assert result['remaining'] == 10

    def test_consume_quota(self, manager):
        """Test consuming quota"""
        manager.set_quota(
            tenant_id="tenant_1",
            quota_type=QuotaType.QUERIES_PER_MINUTE,
            limit=10,
        )

        # Consume 5
        success = manager.consume_quota(
            tenant_id="tenant_1",
            quota_type=QuotaType.QUERIES_PER_MINUTE,
            amount=5,
        )

        assert success

        # Check remaining
        check = manager.check_quota(
            tenant_id="tenant_1",
            quota_type=QuotaType.QUERIES_PER_MINUTE,
        )

        assert check['remaining'] == 5

    def test_quota_exceeded(self, manager):
        """Test quota exceeded"""
        manager.set_quota(
            tenant_id="tenant_1",
            quota_type=QuotaType.QUERIES_PER_MINUTE,
            limit=5,
        )

        # Try to consume more than limit
        check = manager.check_quota(
            tenant_id="tenant_1",
            quota_type=QuotaType.QUERIES_PER_MINUTE,
            amount=10,
        )

        assert not check['allowed']
        assert check['quota_exceeded']

    def test_reset_quota(self, manager):
        """Test resetting quota"""
        manager.set_quota(
            tenant_id="tenant_1",
            quota_type=QuotaType.QUERIES_PER_MINUTE,
            limit=10,
        )

        # Consume some
        manager.consume_quota(
            tenant_id="tenant_1",
            quota_type=QuotaType.QUERIES_PER_MINUTE,
            amount=5,
        )

        # Reset
        manager.reset_quota(
            tenant_id="tenant_1",
            quota_type=QuotaType.QUERIES_PER_MINUTE,
        )

        # Check reset
        quota = manager.get_quota("tenant_1", QuotaType.QUERIES_PER_MINUTE)
        assert quota.current_usage == 0


class TestTenantDatabase:
    """Test tenant database isolation"""

    @pytest.fixture
    def manager(self):
        """Create database manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield TenantDatabaseManager(
                base_db_path=tmpdir,
                isolation_strategy=IsolationStrategy.DATABASE_PER_TENANT,
            )

    def test_create_tenant_database(self, manager):
        """Test creating tenant database"""
        schema = manager.create_tenant_database("tenant_1")

        assert schema.tenant_id == "tenant_1"
        assert schema.isolation_strategy == IsolationStrategy.DATABASE_PER_TENANT
        assert os.path.exists(schema.connection_string)

    def test_get_tenant_connection(self, manager):
        """Test getting tenant connection"""
        manager.create_tenant_database("tenant_1")
        conn = manager.get_tenant_connection("tenant_1")

        assert conn is not None
        conn.close()

    def test_execute_tenant_query(self, manager):
        """Test executing tenant query"""
        manager.create_tenant_database("tenant_1")

        # Insert data
        results = manager.execute_tenant_query(
            "tenant_1",
            "INSERT INTO queries (query, executed_at, status) VALUES (?, ?, ?)",
            ("SELECT * FROM users", datetime.now().isoformat(), "success"),
        )

        assert results[0]['rows_affected'] > 0

    def test_tenant_isolation(self, manager):
        """Test tenant data isolation"""
        # Create two tenants
        manager.create_tenant_database("tenant_1")
        manager.create_tenant_database("tenant_2")

        # Insert data for tenant 1
        manager.execute_tenant_query(
            "tenant_1",
            "INSERT INTO queries (query, executed_at, status) VALUES (?, ?, ?)",
            ("Tenant 1 Query", datetime.now().isoformat(), "success"),
        )

        # Query tenant 2 (should be empty)
        results = manager.execute_tenant_query(
            "tenant_2",
            "SELECT * FROM queries",
        )

        assert len(results) == 0


class TestTenantMiddleware:
    """Test tenant middleware"""

    def test_resolve_from_headers(self):
        """Test tenant resolution from headers"""
        middleware = TenantMiddleware()

        tenant_id = middleware.resolve_tenant_from_headers({
            'X-Tenant-ID': 'acme',
        })

        assert tenant_id == 'acme'

    def test_resolve_from_subdomain(self):
        """Test tenant resolution from subdomain"""
        middleware = TenantMiddleware()

        tenant_id = middleware.resolve_tenant_from_subdomain(
            'acme.example.com',
            'example.com',
        )

        assert tenant_id == 'acme'

    def test_resolve_from_path(self):
        """Test tenant resolution from path"""
        middleware = TenantMiddleware()

        tenant_id = middleware.resolve_tenant_from_path('/tenants/acme/dashboard')

        assert tenant_id == 'acme'

    def test_context_management(self):
        """Test tenant context management"""
        TenantMiddleware.set_current_tenant('tenant_1')
        assert TenantMiddleware.get_current_tenant() == 'tenant_1'

        TenantMiddleware.clear_context()
        assert TenantMiddleware.get_current_tenant() is None

    def test_with_tenant_decorator(self):
        """Test with_tenant decorator"""
        @with_tenant('test_tenant')
        def test_func():
            return TenantMiddleware.get_current_tenant()

        result = test_func()
        assert result == 'test_tenant'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
