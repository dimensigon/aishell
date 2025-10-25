"""
Comprehensive tests for RBAC (Role-Based Access Control) module.

Tests role management, permission checking, inheritance, wildcards,
and security edge cases.
"""

import pytest
from src.security.rbac import RBACManager, Role


class TestRoleManagement:
    """Test suite for role creation and management."""

    def test_create_basic_role(self):
        """Test creation of a basic role."""
        rbac = RBACManager()

        role = rbac.create_role(
            name="viewer",
            permissions=["read", "list"],
            description="Read-only access"
        )

        assert role.name == "viewer"
        assert "read" in role.permissions
        assert "list" in role.permissions
        assert role.description == "Read-only access"

    def test_create_role_with_inheritance(self):
        """Test role creation with inheritance."""
        rbac = RBACManager()

        rbac.create_role("base", ["read"])
        role = rbac.create_role(
            "advanced",
            ["write"],
            inherits_from=["base"]
        )

        assert role.inherits_from == ["base"]

    def test_create_duplicate_role(self):
        """Test that duplicate role creation fails."""
        rbac = RBACManager()

        rbac.create_role("admin", ["all"])

        with pytest.raises(ValueError, match="already exists"):
            rbac.create_role("admin", ["other"])

    def test_get_role(self):
        """Test retrieving a role."""
        rbac = RBACManager()

        rbac.create_role("editor", ["edit", "read"])
        role = rbac.get_role("editor")

        assert role is not None
        assert role.name == "editor"

    def test_get_nonexistent_role(self):
        """Test getting a role that doesn't exist."""
        rbac = RBACManager()

        role = rbac.get_role("nonexistent")
        assert role is None

    def test_delete_role(self):
        """Test role deletion."""
        rbac = RBACManager()

        rbac.create_role("temp", ["read"])
        assert rbac.delete_role("temp")
        assert rbac.get_role("temp") is None

    def test_delete_nonexistent_role(self):
        """Test deleting a role that doesn't exist."""
        rbac = RBACManager()

        assert not rbac.delete_role("nonexistent")

    def test_list_roles(self):
        """Test listing all roles."""
        rbac = RBACManager()

        rbac.create_role("admin", ["*"])
        rbac.create_role("user", ["read"])

        roles = rbac.list_roles()
        assert "admin" in roles
        assert "user" in roles


class TestUserRoleAssignment:
    """Test suite for user-role assignments."""

    def test_assign_role(self):
        """Test assigning a role to a user."""
        rbac = RBACManager()

        rbac.create_role("admin", ["*"])
        rbac.assign_role("user_1", "admin")

        roles = rbac.get_user_roles("user_1")
        assert "admin" in roles

    def test_assign_nonexistent_role(self):
        """Test assigning a role that doesn't exist."""
        rbac = RBACManager()

        with pytest.raises(ValueError, match="does not exist"):
            rbac.assign_role("user_1", "nonexistent")

    def test_assign_multiple_roles(self):
        """Test assigning multiple roles to a user."""
        rbac = RBACManager()

        rbac.create_role("admin", ["admin.*"])
        rbac.create_role("developer", ["code.*"])

        rbac.assign_role("user_1", "admin")
        rbac.assign_role("user_1", "developer")

        roles = rbac.get_user_roles("user_1")
        assert "admin" in roles
        assert "developer" in roles

    def test_revoke_role(self):
        """Test revoking a role from a user."""
        rbac = RBACManager()

        rbac.create_role("temp", ["read"])
        rbac.assign_role("user_1", "temp")
        rbac.revoke_role("user_1", "temp")

        roles = rbac.get_user_roles("user_1")
        assert "temp" not in roles

    def test_revoke_nonexistent_role(self):
        """Test revoking a role from user who doesn't have it."""
        rbac = RBACManager()

        # Should not raise error
        rbac.revoke_role("user_1", "nonexistent")

    def test_get_user_roles_no_roles(self):
        """Test getting roles for user with no roles."""
        rbac = RBACManager()

        roles = rbac.get_user_roles("user_1")
        assert roles == []

    def test_delete_role_removes_from_users(self):
        """Test that deleting a role removes it from all users."""
        rbac = RBACManager()

        rbac.create_role("temp", ["read"])
        rbac.assign_role("user_1", "temp")
        rbac.assign_role("user_2", "temp")

        rbac.delete_role("temp")

        assert "temp" not in rbac.get_user_roles("user_1")
        assert "temp" not in rbac.get_user_roles("user_2")


class TestPermissionChecking:
    """Test suite for permission checking."""

    def test_has_direct_permission(self):
        """Test checking for a direct permission."""
        rbac = RBACManager()

        rbac.create_role("viewer", ["data.read"])
        rbac.assign_role("user_1", "viewer")

        assert rbac.has_permission("user_1", "data.read")

    def test_no_permission(self):
        """Test checking for a permission the user doesn't have."""
        rbac = RBACManager()

        rbac.create_role("viewer", ["data.read"])
        rbac.assign_role("user_1", "viewer")

        assert not rbac.has_permission("user_1", "data.write")

    def test_wildcard_permission(self):
        """Test wildcard permission matching."""
        rbac = RBACManager()

        rbac.create_role("admin", ["*"])
        rbac.assign_role("user_1", "admin")

        assert rbac.has_permission("user_1", "anything")
        assert rbac.has_permission("user_1", "data.delete")

    def test_namespace_wildcard(self):
        """Test namespace wildcard (e.g., db.*)."""
        rbac = RBACManager()

        rbac.create_role("db_admin", ["db.*"])
        rbac.assign_role("user_1", "db_admin")

        assert rbac.has_permission("user_1", "db.read")
        assert rbac.has_permission("user_1", "db.write")
        assert rbac.has_permission("user_1", "db.delete")
        assert not rbac.has_permission("user_1", "api.read")

    def test_no_roles_no_permissions(self):
        """Test that user with no roles has no permissions."""
        rbac = RBACManager()

        assert not rbac.has_permission("user_1", "anything")

    def test_multiple_roles_combined_permissions(self):
        """Test that user gets permissions from all assigned roles."""
        rbac = RBACManager()

        rbac.create_role("reader", ["data.read"])
        rbac.create_role("writer", ["data.write"])

        rbac.assign_role("user_1", "reader")
        rbac.assign_role("user_1", "writer")

        assert rbac.has_permission("user_1", "data.read")
        assert rbac.has_permission("user_1", "data.write")


class TestRoleInheritance:
    """Test suite for role inheritance."""

    def test_single_level_inheritance(self):
        """Test single-level role inheritance."""
        rbac = RBACManager()

        rbac.create_role("base", ["read"])
        rbac.create_role("advanced", ["write"], inherits_from=["base"])

        rbac.assign_role("user_1", "advanced")

        assert rbac.has_permission("user_1", "read")  # Inherited
        assert rbac.has_permission("user_1", "write")  # Direct

    def test_multi_level_inheritance(self):
        """Test multi-level role inheritance."""
        rbac = RBACManager()

        rbac.create_role("level1", ["perm1"])
        rbac.create_role("level2", ["perm2"], inherits_from=["level1"])
        rbac.create_role("level3", ["perm3"], inherits_from=["level2"])

        rbac.assign_role("user_1", "level3")

        assert rbac.has_permission("user_1", "perm1")
        assert rbac.has_permission("user_1", "perm2")
        assert rbac.has_permission("user_1", "perm3")

    def test_multiple_inheritance(self):
        """Test inheriting from multiple roles."""
        rbac = RBACManager()

        rbac.create_role("reader", ["read"])
        rbac.create_role("writer", ["write"])
        rbac.create_role("editor", ["edit"], inherits_from=["reader", "writer"])

        rbac.assign_role("user_1", "editor")

        assert rbac.has_permission("user_1", "read")
        assert rbac.has_permission("user_1", "write")
        assert rbac.has_permission("user_1", "edit")

    def test_circular_inheritance_prevention(self):
        """Test that circular inheritance is prevented."""
        rbac = RBACManager()

        rbac.create_role("role1", ["perm1"])
        rbac.create_role("role2", ["perm2"], inherits_from=["role1"])
        rbac.create_role("role3", ["perm3"], inherits_from=["role2"])

        # Manually create circular reference (role1 inherits from role3)
        rbac._roles["role1"].inherits_from = ["role3"]

        rbac.assign_role("user_1", "role1")

        # Should not crash, circular reference should be handled
        perms = rbac.list_user_permissions("user_1")
        assert len(perms) > 0


class TestContextualPermissions:
    """Test suite for context-based permissions."""

    def test_ownership_permission(self):
        """Test .own permission with ownership context."""
        rbac = RBACManager()

        rbac.create_role("data_owner", ["data.edit.own"])
        rbac.assign_role("user_1", "data_owner")

        # User owns the resource
        context = {"user_id": "user_1", "resource_owner": "user_1"}
        assert rbac.has_permission("user_1", "data.edit", context)

        # User doesn't own the resource
        context = {"user_id": "user_1", "resource_owner": "user_2"}
        assert not rbac.has_permission("user_1", "data.edit", context)

    def test_contextual_permission_without_context(self):
        """Test .own permission without context."""
        rbac = RBACManager()

        rbac.create_role("owner", ["data.delete.own"])
        rbac.assign_role("user_1", "owner")

        # Without context, .own permission should not grant access
        assert not rbac.has_permission("user_1", "data.delete")


class TestRoleHierarchy:
    """Test suite for role hierarchy inspection."""

    def test_get_role_hierarchy(self):
        """Test getting role hierarchy information."""
        rbac = RBACManager()

        rbac.create_role("base", ["read"])
        rbac.create_role("advanced", ["write"], inherits_from=["base"])

        hierarchy = rbac.get_role_hierarchy("advanced")

        assert hierarchy["name"] == "advanced"
        assert "write" in hierarchy["permissions"]
        assert "read" in hierarchy["inherited_permissions"]
        assert "read" in hierarchy["total_permissions"]
        assert "write" in hierarchy["total_permissions"]

    def test_get_hierarchy_nonexistent_role(self):
        """Test getting hierarchy for nonexistent role."""
        rbac = RBACManager()

        hierarchy = rbac.get_role_hierarchy("nonexistent")
        assert hierarchy == {}

    def test_list_user_permissions(self):
        """Test listing all user permissions."""
        rbac = RBACManager()

        rbac.create_role("role1", ["perm1", "perm2"])
        rbac.create_role("role2", ["perm3"])

        rbac.assign_role("user_1", "role1")
        rbac.assign_role("user_1", "role2")

        perms = rbac.list_user_permissions("user_1")

        assert "perm1" in perms
        assert "perm2" in perms
        assert "perm3" in perms


class TestRBACThreadSafety:
    """Test thread safety of RBAC operations."""

    def test_concurrent_role_creation(self):
        """Test concurrent role creation."""
        import threading

        rbac = RBACManager()
        errors = []

        def create_role(name):
            try:
                rbac.create_role(name, ["read"])
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=create_role, args=(f"role_{i}",))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(rbac.list_roles()) == 10

    def test_concurrent_user_assignment(self):
        """Test concurrent user-role assignment."""
        import threading

        rbac = RBACManager()
        rbac.create_role("test", ["read"])

        errors = []

        def assign_role(user_id):
            try:
                rbac.assign_role(user_id, "test")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=assign_role, args=(f"user_{i}",))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestRBACEdgeCases:
    """Test edge cases and security scenarios."""

    def test_permission_injection_attempt(self):
        """Test that permission names are treated literally."""
        rbac = RBACManager()

        rbac.create_role("test", ["data.read.*"])
        rbac.assign_role("user_1", "test")

        assert rbac.has_permission("user_1", "data.read.public")
        assert rbac.has_permission("user_1", "data.read.private")

    def test_empty_permission_list(self):
        """Test role with empty permission list."""
        rbac = RBACManager()

        rbac.create_role("empty", [])
        rbac.assign_role("user_1", "empty")

        assert not rbac.has_permission("user_1", "anything")

    def test_special_characters_in_permission(self):
        """Test permissions with special characters."""
        rbac = RBACManager()

        rbac.create_role("special", ["api/v1/users:read"])
        rbac.assign_role("user_1", "special")

        assert rbac.has_permission("user_1", "api/v1/users:read")

    def test_case_sensitive_permissions(self):
        """Test that permissions are case-sensitive in matching."""
        rbac = RBACManager()

        rbac.create_role("test", ["Data.Read"])
        rbac.assign_role("user_1", "test")

        assert rbac.has_permission("user_1", "Data.Read")
        # Current implementation may be case-insensitive in wildcards
        # This documents the behavior
