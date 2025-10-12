"""
Comprehensive tests for role_manager.py

Tests:
- Role CRUD operations
- Role hierarchies and inheritance
- User-role assignments
- Permission aggregation
- System roles protection
- Role expiration
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from src.enterprise.rbac.role_manager import (
    RoleManager,
    Role,
    RoleType,
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def role_manager(temp_db):
    return RoleManager(db_path=temp_db)


class TestRoleCreation:
    """Test role creation"""

    def test_create_custom_role(self, role_manager):
        """Test creating a custom role"""
        role = role_manager.create_role(
            name="Custom Role",
            role_type=RoleType.CUSTOM,
            tenant_id="tenant_123",
            permissions=["database:read", "query:execute"]
        )

        assert role.name == "Custom Role"
        assert role.role_type == RoleType.CUSTOM
        assert "database:read" in role.permissions

    def test_create_role_with_inheritance(self, role_manager):
        """Test creating role with parent roles"""
        parent = role_manager.create_role(
            name="Parent Role",
            role_type=RoleType.CUSTOM,
            permissions=["base:permission"]
        )

        child = role_manager.create_role(
            name="Child Role",
            role_type=RoleType.CUSTOM,
            parent_roles=[parent.id],
            permissions=["child:permission"]
        )

        assert parent.id in child.parent_roles

    def test_system_roles_initialized(self, role_manager):
        """Test system roles are initialized"""
        super_admin = role_manager.get_role('role_super_admin')
        tenant_admin = role_manager.get_role('role_tenant_admin')

        assert super_admin is not None
        assert tenant_admin is not None
        assert super_admin.is_system

    def test_create_tenant_specific_role(self, role_manager):
        """Test creating tenant-specific role"""
        role = role_manager.create_role(
            name="Tenant Role",
            role_type=RoleType.CUSTOM,
            tenant_id="tenant_abc",
            permissions=["custom:action"]
        )

        assert role.tenant_id == "tenant_abc"


class TestRoleRetrieval:
    """Test role retrieval"""

    def test_get_role_by_id(self, role_manager):
        """Test getting role by ID"""
        created = role_manager.create_role(
            name="Test Role",
            role_type=RoleType.ANALYST
        )

        retrieved = role_manager.get_role(created.id)

        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_nonexistent_role(self, role_manager):
        """Test getting non-existent role"""
        role = role_manager.get_role("nonexistent_id")

        assert role is None

    def test_list_roles(self, role_manager):
        """Test listing roles"""
        role_manager.create_role(name="Role 1", role_type=RoleType.DEVELOPER)
        role_manager.create_role(name="Role 2", role_type=RoleType.ANALYST)

        roles = role_manager.list_roles()

        assert len(roles) >= 2

    def test_list_roles_by_tenant(self, role_manager):
        """Test filtering roles by tenant"""
        role_manager.create_role(
            name="Tenant Role",
            role_type=RoleType.CUSTOM,
            tenant_id="tenant_1"
        )

        roles = role_manager.list_roles(tenant_id="tenant_1")

        assert any(r.tenant_id == "tenant_1" for r in roles)

    def test_list_roles_by_type(self, role_manager):
        """Test filtering roles by type"""
        role_manager.create_role(name="Dev Role", role_type=RoleType.DEVELOPER)

        roles = role_manager.list_roles(role_type=RoleType.DEVELOPER)

        assert all(r.role_type == RoleType.DEVELOPER for r in roles)


class TestRoleUpdate:
    """Test role updates"""

    def test_update_role_name(self, role_manager):
        """Test updating role name"""
        role = role_manager.create_role(
            name="Original Name",
            role_type=RoleType.CUSTOM
        )

        success = role_manager.update_role(role.id, name="Updated Name")

        assert success
        updated = role_manager.get_role(role.id)
        assert updated.name == "Updated Name"

    def test_update_role_permissions(self, role_manager):
        """Test updating role permissions"""
        role = role_manager.create_role(
            name="Update Permissions",
            role_type=RoleType.CUSTOM,
            permissions=["old:permission"]
        )

        success = role_manager.update_role(
            role.id,
            permissions=["new:permission", "another:permission"]
        )

        assert success
        updated = role_manager.get_role(role.id)
        assert "new:permission" in updated.permissions

    def test_update_system_role_fails(self, role_manager):
        """Test updating system role fails"""
        success = role_manager.update_role(
            'role_super_admin',
            name="Hacked Name"
        )

        assert not success

    def test_update_nonexistent_role(self, role_manager):
        """Test updating non-existent role"""
        success = role_manager.update_role("nonexistent", name="Test")

        assert not success


class TestRoleDeletion:
    """Test role deletion"""

    def test_delete_custom_role(self, role_manager):
        """Test deleting custom role"""
        role = role_manager.create_role(
            name="Delete Me",
            role_type=RoleType.CUSTOM
        )

        success = role_manager.delete_role(role.id)

        assert success
        assert role_manager.get_role(role.id) is None

    def test_delete_system_role_fails(self, role_manager):
        """Test deleting system role fails"""
        success = role_manager.delete_role('role_super_admin')

        assert not success

    def test_delete_role_removes_assignments(self, role_manager):
        """Test deleting role removes user assignments"""
        role = role_manager.create_role(
            name="Assigned Role",
            role_type=RoleType.CUSTOM
        )

        role_manager.assign_role("user_123", role.id)
        role_manager.delete_role(role.id)

        # User should have no roles now
        roles = role_manager.get_user_roles("user_123")
        assert len(roles) == 0


class TestUserRoleAssignment:
    """Test user-role assignment"""

    def test_assign_role_to_user(self, role_manager):
        """Test assigning role to user"""
        role = role_manager.create_role(
            name="Test Role",
            role_type=RoleType.DEVELOPER
        )

        success = role_manager.assign_role("user_123", role.id)

        assert success

    def test_assign_role_with_tenant(self, role_manager):
        """Test assigning role with tenant context"""
        role = role_manager.create_role(
            name="Tenant Role",
            role_type=RoleType.CUSTOM
        )

        success = role_manager.assign_role(
            "user_456",
            role.id,
            tenant_id="tenant_abc"
        )

        assert success

    def test_assign_role_with_expiration(self, role_manager):
        """Test assigning role with expiration"""
        role = role_manager.create_role(
            name="Temp Role",
            role_type=RoleType.CUSTOM
        )

        expires_at = (datetime.now() + timedelta(days=30)).isoformat()

        success = role_manager.assign_role(
            "user_temp",
            role.id,
            expires_at=expires_at
        )

        assert success

    def test_assign_nonexistent_role_fails(self, role_manager):
        """Test assigning non-existent role fails"""
        success = role_manager.assign_role("user_123", "nonexistent_role")

        assert not success


class TestUserRoleRevocation:
    """Test role revocation"""

    def test_revoke_role_from_user(self, role_manager):
        """Test revoking role from user"""
        role = role_manager.create_role(
            name="Revoke Test",
            role_type=RoleType.DEVELOPER
        )

        role_manager.assign_role("user_revoke", role.id)
        success = role_manager.revoke_role("user_revoke", role.id)

        assert success

        roles = role_manager.get_user_roles("user_revoke")
        assert len(roles) == 0

    def test_revoke_role_with_tenant(self, role_manager):
        """Test revoking role in tenant context"""
        role = role_manager.create_role(
            name="Tenant Role",
            role_type=RoleType.CUSTOM
        )

        role_manager.assign_role("user_123", role.id, tenant_id="tenant_1")
        success = role_manager.revoke_role("user_123", role.id, tenant_id="tenant_1")

        assert success


class TestGetUserRoles:
    """Test getting user roles"""

    def test_get_user_roles(self, role_manager):
        """Test getting all roles for a user"""
        role1 = role_manager.create_role(name="Role 1", role_type=RoleType.DEVELOPER)
        role2 = role_manager.create_role(name="Role 2", role_type=RoleType.ANALYST)

        role_manager.assign_role("user_multi", role1.id)
        role_manager.assign_role("user_multi", role2.id)

        roles = role_manager.get_user_roles("user_multi")

        assert len(roles) == 2

    def test_get_user_roles_with_tenant_filter(self, role_manager):
        """Test getting user roles filtered by tenant"""
        role = role_manager.create_role(name="Tenant Role", role_type=RoleType.CUSTOM)

        role_manager.assign_role("user_tenant", role.id, tenant_id="tenant_1")

        roles = role_manager.get_user_roles("user_tenant", tenant_id="tenant_1")

        assert len(roles) > 0

    def test_get_user_roles_excludes_expired(self, role_manager):
        """Test expired roles are excluded"""
        role = role_manager.create_role(name="Expired Role", role_type=RoleType.CUSTOM)

        # Assign with past expiration
        expires_at = (datetime.now() - timedelta(days=1)).isoformat()
        role_manager.assign_role("user_expired", role.id, expires_at=expires_at)

        roles = role_manager.get_user_roles("user_expired")

        assert len(roles) == 0


class TestEffectivePermissions:
    """Test effective permissions calculation"""

    def test_get_effective_permissions_single_role(self, role_manager):
        """Test getting permissions from single role"""
        role = role_manager.create_role(
            name="Single Role",
            role_type=RoleType.CUSTOM,
            permissions=["database:read", "query:execute"]
        )

        role_manager.assign_role("user_single", role.id)

        permissions = role_manager.get_effective_permissions("user_single")

        assert "database:read" in permissions
        assert "query:execute" in permissions

    def test_get_effective_permissions_multiple_roles(self, role_manager):
        """Test aggregating permissions from multiple roles"""
        role1 = role_manager.create_role(
            name="Role 1",
            role_type=RoleType.CUSTOM,
            permissions=["permission:a"]
        )
        role2 = role_manager.create_role(
            name="Role 2",
            role_type=RoleType.CUSTOM,
            permissions=["permission:b"]
        )

        role_manager.assign_role("user_multi_perm", role1.id)
        role_manager.assign_role("user_multi_perm", role2.id)

        permissions = role_manager.get_effective_permissions("user_multi_perm")

        assert "permission:a" in permissions
        assert "permission:b" in permissions

    def test_get_effective_permissions_with_inheritance(self, role_manager):
        """Test permissions include inherited ones"""
        parent = role_manager.create_role(
            name="Parent",
            role_type=RoleType.CUSTOM,
            permissions=["parent:permission"]
        )

        child = role_manager.create_role(
            name="Child",
            role_type=RoleType.CUSTOM,
            parent_roles=[parent.id],
            permissions=["child:permission"]
        )

        role_manager.assign_role("user_inherit", child.id)

        permissions = role_manager.get_effective_permissions("user_inherit")

        assert "child:permission" in permissions
        assert "parent:permission" in permissions


class TestRoleHierarchy:
    """Test role hierarchy and inheritance"""

    def test_multi_level_hierarchy(self, role_manager):
        """Test multi-level role hierarchy"""
        grandparent = role_manager.create_role(
            name="Grandparent",
            role_type=RoleType.CUSTOM,
            permissions=["grandparent:perm"]
        )

        parent = role_manager.create_role(
            name="Parent",
            role_type=RoleType.CUSTOM,
            parent_roles=[grandparent.id],
            permissions=["parent:perm"]
        )

        child = role_manager.create_role(
            name="Child",
            role_type=RoleType.CUSTOM,
            parent_roles=[parent.id],
            permissions=["child:perm"]
        )

        assert parent.id in child.parent_roles


class TestRoleSerialization:
    """Test role serialization"""

    def test_role_to_dict(self):
        """Test converting role to dict"""
        role = Role(
            id="test_id",
            name="Test Role",
            role_type=RoleType.DEVELOPER,
            tenant_id=None,
            permissions=["test:permission"]
        )

        role_dict = role.to_dict()

        assert role_dict['id'] == "test_id"
        assert role_dict['role_type'] == 'developer'

    def test_role_from_dict(self):
        """Test creating role from dict"""
        data = {
            'id': 'test',
            'name': 'Test',
            'role_type': 'developer',
            'tenant_id': None,
            'permissions': [],
            'parent_roles': [],
            'metadata': {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_system': False
        }

        role = Role.from_dict(data)

        assert role.role_type == RoleType.DEVELOPER


class TestRoleValidation:
    """Test role validation logic"""

    def test_role_has_permission(self):
        """Test role.has_permission method"""
        role = Role(
            id="test",
            name="Test",
            role_type=RoleType.CUSTOM,
            tenant_id=None,
            permissions=["database:read", "query:execute"]
        )

        assert role.has_permission("database:read")
        assert not role.has_permission("nonexistent:permission")
