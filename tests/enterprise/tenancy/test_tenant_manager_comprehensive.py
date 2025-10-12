"""
Comprehensive tests for tenant_manager.py

Tests:
- Tenant CRUD operations
- Hierarchical tenant structures
- Feature flag management
- Tenant lifecycle (trial, active, suspended, archived)
- Tenant validation and isolation
- Slug uniqueness
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from src.enterprise.tenancy.tenant_manager import (
    TenantManager,
    Tenant,
    TenantStatus,
    TenantTier,
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def tenant_manager(temp_db):
    """Create TenantManager instance"""
    return TenantManager(db_path=temp_db)


class TestTenantCreation:
    """Test tenant creation scenarios"""

    def test_create_basic_tenant(self, tenant_manager):
        """Test creating a basic tenant"""
        tenant = tenant_manager.create_tenant(
            name="Acme Corp",
            slug="acme-corp",
            owner_id="user_123",
        )

        assert tenant.id is not None
        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme-corp"
        assert tenant.owner_id == "user_123"
        assert tenant.status == TenantStatus.TRIAL
        assert tenant.tier == TenantTier.FREE

    def test_create_enterprise_tenant(self, tenant_manager):
        """Test creating enterprise tier tenant"""
        tenant = tenant_manager.create_tenant(
            name="Enterprise Inc",
            slug="enterprise-inc",
            owner_id="user_456",
            tier=TenantTier.ENTERPRISE,
            contact_email="admin@enterprise.com",
        )

        assert tenant.tier == TenantTier.ENTERPRISE
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.contact_email == "admin@enterprise.com"
        assert 'sso' in tenant.features
        assert 'compliance_reports' in tenant.features

    def test_create_tenant_with_custom_features(self, tenant_manager):
        """Test creating tenant with custom feature flags"""
        features = ['feature_a', 'feature_b', 'custom_integration']
        tenant = tenant_manager.create_tenant(
            name="Custom Co",
            slug="custom-co",
            owner_id="user_789",
            features=features,
        )

        assert set(features).issubset(set(tenant.features))

    def test_create_tenant_with_trial_period(self, tenant_manager):
        """Test trial period is set correctly"""
        tenant = tenant_manager.create_tenant(
            name="Trial Co",
            slug="trial-co",
            owner_id="user_trial",
            trial_days=14,
        )

        assert tenant.trial_ends_at is not None
        trial_end = datetime.fromisoformat(tenant.trial_ends_at)
        expected_end = datetime.now() + timedelta(days=14)

        # Allow 1 minute difference for test execution time
        assert abs((trial_end - expected_end).total_seconds()) < 60

    def test_create_hierarchical_tenant(self, tenant_manager):
        """Test creating child tenant in hierarchy"""
        parent = tenant_manager.create_tenant(
            name="Parent Corp",
            slug="parent-corp",
            owner_id="user_parent",
        )

        child = tenant_manager.create_tenant(
            name="Child Division",
            slug="child-division",
            owner_id="user_child",
            parent_tenant_id=parent.id,
        )

        assert child.parent_tenant_id == parent.id


class TestTenantRetrieval:
    """Test tenant retrieval operations"""

    def test_get_tenant_by_id(self, tenant_manager):
        """Test retrieving tenant by ID"""
        created = tenant_manager.create_tenant(
            name="Test Corp",
            slug="test-corp",
            owner_id="user_test",
        )

        retrieved = tenant_manager.get_tenant(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_nonexistent_tenant(self, tenant_manager):
        """Test retrieving non-existent tenant returns None"""
        result = tenant_manager.get_tenant("nonexistent-id")
        assert result is None

    def test_get_tenant_by_slug(self, tenant_manager):
        """Test retrieving tenant by slug"""
        tenant_manager.create_tenant(
            name="Slug Test",
            slug="slug-test",
            owner_id="user_slug",
        )

        retrieved = tenant_manager.get_tenant_by_slug("slug-test")

        assert retrieved is not None
        assert retrieved.slug == "slug-test"

    def test_get_tenant_by_slug_case_sensitive(self, tenant_manager):
        """Test slug retrieval is case-sensitive"""
        tenant_manager.create_tenant(
            name="Case Test",
            slug="case-test",
            owner_id="user_case",
        )

        # Slug is lowercase
        result = tenant_manager.get_tenant_by_slug("Case-Test")
        assert result is None


class TestTenantUpdate:
    """Test tenant update operations"""

    def test_update_tenant_name(self, tenant_manager):
        """Test updating tenant name"""
        tenant = tenant_manager.create_tenant(
            name="Original Name",
            slug="update-test",
            owner_id="user_update",
        )

        success = tenant_manager.update_tenant(
            tenant.id,
            name="Updated Name",
        )

        assert success
        updated = tenant_manager.get_tenant(tenant.id)
        assert updated.name == "Updated Name"

    def test_update_tenant_status(self, tenant_manager):
        """Test updating tenant status"""
        tenant = tenant_manager.create_tenant(
            name="Status Test",
            slug="status-test",
            owner_id="user_status",
        )

        success = tenant_manager.update_tenant(
            tenant.id,
            status=TenantStatus.SUSPENDED,
        )

        assert success
        updated = tenant_manager.get_tenant(tenant.id)
        assert updated.status == TenantStatus.SUSPENDED

    def test_update_tenant_features(self, tenant_manager):
        """Test updating tenant features"""
        tenant = tenant_manager.create_tenant(
            name="Features Test",
            slug="features-test",
            owner_id="user_features",
        )

        new_features = ['new_feature_1', 'new_feature_2']
        success = tenant_manager.update_tenant(
            tenant.id,
            features=new_features,
        )

        assert success
        updated = tenant_manager.get_tenant(tenant.id)
        assert set(new_features).issubset(set(updated.features))

    def test_update_tenant_quotas(self, tenant_manager):
        """Test updating tenant resource quotas"""
        tenant = tenant_manager.create_tenant(
            name="Quota Test",
            slug="quota-test",
            owner_id="user_quota",
        )

        success = tenant_manager.update_tenant(
            tenant.id,
            max_users=50,
            max_databases=20,
        )

        assert success
        updated = tenant_manager.get_tenant(tenant.id)
        assert updated.max_users == 50
        assert updated.max_databases == 20

    def test_update_nonexistent_tenant(self, tenant_manager):
        """Test updating non-existent tenant returns False"""
        success = tenant_manager.update_tenant(
            "nonexistent-id",
            name="Should Fail",
        )

        assert not success


class TestTenantDeletion:
    """Test tenant deletion operations"""

    def test_soft_delete_tenant(self, tenant_manager):
        """Test soft deleting tenant (archiving)"""
        tenant = tenant_manager.create_tenant(
            name="Delete Test",
            slug="delete-test",
            owner_id="user_delete",
        )

        success = tenant_manager.delete_tenant(tenant.id, hard_delete=False)

        assert success
        archived = tenant_manager.get_tenant(tenant.id)
        assert archived.status == TenantStatus.ARCHIVED

    def test_hard_delete_tenant(self, tenant_manager):
        """Test permanently deleting tenant"""
        tenant = tenant_manager.create_tenant(
            name="Hard Delete Test",
            slug="hard-delete-test",
            owner_id="user_hard_delete",
        )

        success = tenant_manager.delete_tenant(tenant.id, hard_delete=True)

        assert success
        deleted = tenant_manager.get_tenant(tenant.id)
        assert deleted is None


class TestTenantListing:
    """Test tenant listing and filtering"""

    def test_list_all_tenants(self, tenant_manager):
        """Test listing all tenants"""
        for i in range(5):
            tenant_manager.create_tenant(
                name=f"Tenant {i}",
                slug=f"tenant-{i}",
                owner_id=f"user_{i}",
            )

        tenants = tenant_manager.list_tenants()
        assert len(tenants) >= 5

    def test_list_tenants_by_status(self, tenant_manager):
        """Test filtering tenants by status"""
        active_tenant = tenant_manager.create_tenant(
            name="Active Tenant",
            slug="active-tenant",
            owner_id="user_active",
            tier=TenantTier.STARTER,
        )

        trial_tenant = tenant_manager.create_tenant(
            name="Trial Tenant",
            slug="trial-tenant",
            owner_id="user_trial",
        )

        active_tenants = tenant_manager.list_tenants(status=TenantStatus.ACTIVE)
        trial_tenants = tenant_manager.list_tenants(status=TenantStatus.TRIAL)

        assert any(t.id == active_tenant.id for t in active_tenants)
        assert any(t.id == trial_tenant.id for t in trial_tenants)

    def test_list_tenants_by_tier(self, tenant_manager):
        """Test filtering tenants by tier"""
        tenant_manager.create_tenant(
            name="Free Tier",
            slug="free-tier",
            owner_id="user_free",
            tier=TenantTier.FREE,
        )

        tenant_manager.create_tenant(
            name="Enterprise Tier",
            slug="enterprise-tier",
            owner_id="user_enterprise",
            tier=TenantTier.ENTERPRISE,
        )

        free_tenants = tenant_manager.list_tenants(tier=TenantTier.FREE)
        enterprise_tenants = tenant_manager.list_tenants(tier=TenantTier.ENTERPRISE)

        assert len(free_tenants) > 0
        assert len(enterprise_tenants) > 0

    def test_list_tenants_pagination(self, tenant_manager):
        """Test tenant listing pagination"""
        for i in range(15):
            tenant_manager.create_tenant(
                name=f"Pagination {i}",
                slug=f"pagination-{i}",
                owner_id=f"user_{i}",
            )

        page1 = tenant_manager.list_tenants(limit=10, offset=0)
        page2 = tenant_manager.list_tenants(limit=10, offset=10)

        assert len(page1) == 10
        assert len(page2) >= 5


class TestTenantHierarchy:
    """Test hierarchical tenant operations"""

    def test_get_tenant_hierarchy(self, tenant_manager):
        """Test retrieving entire tenant hierarchy"""
        parent = tenant_manager.create_tenant(
            name="Parent",
            slug="parent",
            owner_id="user_parent",
        )

        child1 = tenant_manager.create_tenant(
            name="Child 1",
            slug="child-1",
            owner_id="user_child1",
            parent_tenant_id=parent.id,
        )

        child2 = tenant_manager.create_tenant(
            name="Child 2",
            slug="child-2",
            owner_id="user_child2",
            parent_tenant_id=parent.id,
        )

        grandchild = tenant_manager.create_tenant(
            name="Grandchild",
            slug="grandchild",
            owner_id="user_grandchild",
            parent_tenant_id=child1.id,
        )

        hierarchy = tenant_manager.get_tenant_hierarchy(parent.id)

        assert len(hierarchy) == 3
        assert any(t.id == child1.id for t in hierarchy)
        assert any(t.id == child2.id for t in hierarchy)
        assert any(t.id == grandchild.id for t in hierarchy)


class TestTenantValidation:
    """Test tenant validation logic"""

    def test_tenant_is_active_when_active_status(self, tenant_manager):
        """Test active tenant returns True for is_active()"""
        tenant = tenant_manager.create_tenant(
            name="Active Test",
            slug="active-test",
            owner_id="user_active",
            tier=TenantTier.STARTER,
        )

        assert tenant.is_active()

    def test_tenant_is_active_when_trial(self, tenant_manager):
        """Test trial tenant with valid period returns True"""
        tenant = tenant_manager.create_tenant(
            name="Trial Test",
            slug="trial-test",
            owner_id="user_trial",
            trial_days=30,
        )

        assert tenant.is_active()

    def test_tenant_not_active_when_suspended(self, tenant_manager):
        """Test suspended tenant returns False"""
        tenant = tenant_manager.create_tenant(
            name="Suspended Test",
            slug="suspended-test",
            owner_id="user_suspended",
        )

        tenant_manager.update_tenant(tenant.id, status=TenantStatus.SUSPENDED)
        updated = tenant_manager.get_tenant(tenant.id)

        assert not updated.is_active()

    def test_tenant_has_feature(self, tenant_manager):
        """Test checking if tenant has specific feature"""
        tenant = tenant_manager.create_tenant(
            name="Feature Check",
            slug="feature-check",
            owner_id="user_feature",
            tier=TenantTier.ENTERPRISE,
        )

        assert tenant.has_feature('sso')
        assert tenant.has_feature('compliance_reports')
        assert not tenant.has_feature('nonexistent_feature')


class TestTenantStatistics:
    """Test tenant statistics"""

    def test_get_tenant_stats(self, tenant_manager):
        """Test retrieving tenant statistics"""
        # Create various tenants
        tenant_manager.create_tenant(
            name="Active 1", slug="active-1", owner_id="u1", tier=TenantTier.STARTER
        )
        tenant_manager.create_tenant(
            name="Active 2", slug="active-2", owner_id="u2", tier=TenantTier.ENTERPRISE
        )
        tenant_manager.create_tenant(
            name="Trial 1", slug="trial-1", owner_id="u3", tier=TenantTier.FREE
        )

        stats = tenant_manager.get_stats()

        assert stats['total_tenants'] >= 3
        assert stats['active_tenants'] >= 2
        assert stats['trial_tenants'] >= 1
        assert stats['enterprise_tier_tenants'] >= 1


class TestTenantSerialization:
    """Test tenant serialization"""

    def test_tenant_to_dict(self, tenant_manager):
        """Test converting tenant to dictionary"""
        tenant = tenant_manager.create_tenant(
            name="Serialize Test",
            slug="serialize-test",
            owner_id="user_serialize",
        )

        tenant_dict = tenant.to_dict()

        assert tenant_dict['id'] == tenant.id
        assert tenant_dict['name'] == tenant.name
        assert tenant_dict['status'] == tenant.status.value
        assert tenant_dict['tier'] == tenant.tier.value

    def test_tenant_from_dict(self):
        """Test creating tenant from dictionary"""
        data = {
            'id': 'test-id',
            'name': 'Test',
            'slug': 'test',
            'status': 'active',
            'tier': 'enterprise',
            'owner_id': 'user_123',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

        tenant = Tenant.from_dict(data)

        assert tenant.id == 'test-id'
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.tier == TenantTier.ENTERPRISE


class TestTenantIsolation:
    """Test tenant isolation scenarios"""

    def test_tenants_are_isolated(self, tenant_manager):
        """Test that tenants are properly isolated"""
        tenant1 = tenant_manager.create_tenant(
            name="Tenant 1", slug="tenant-1", owner_id="user_1"
        )
        tenant2 = tenant_manager.create_tenant(
            name="Tenant 2", slug="tenant-2", owner_id="user_2"
        )

        # Update tenant1
        tenant_manager.update_tenant(tenant1.id, metadata={'key': 'value1'})

        # Verify tenant2 is not affected
        retrieved2 = tenant_manager.get_tenant(tenant2.id)
        assert retrieved2.metadata.get('key') != 'value1'

    def test_slug_uniqueness(self, tenant_manager):
        """Test that slugs must be unique"""
        tenant_manager.create_tenant(
            name="First", slug="unique-slug", owner_id="user_1"
        )

        # Attempting to create another with same slug should fail
        # (In production, this would raise an error; here we test database constraint)
        with pytest.raises(Exception):
            tenant_manager.create_tenant(
                name="Second", slug="unique-slug", owner_id="user_2"
            )
