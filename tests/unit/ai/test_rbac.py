"""Tests for RBAC features"""

import pytest
import tempfile
import os

from src.enterprise.rbac.role_manager import RoleManager, Role, RoleType
from src.enterprise.rbac.permission_engine import PermissionEngine, Permission
from src.enterprise.rbac.policy_evaluator import PolicyEvaluator, Policy, PolicyEffect


class TestRoleManager:
    """Test role management"""

    @pytest.fixture
    def manager(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            db_path = f.name
        yield RoleManager(db_path=db_path)
        os.unlink(db_path)

    def test_create_role(self, manager):
        """Test role creation"""
        role = manager.create_role(
            name="Custom Admin",
            role_type=RoleType.CUSTOM,
            permissions=["database:read", "database:write"],
        )

        assert role.id is not None
        assert role.name == "Custom Admin"
        assert "database:read" in role.permissions

    def test_get_role(self, manager):
        """Test retrieving role"""
        created = manager.create_role(
            name="Test Role",
            role_type=RoleType.CUSTOM,
        )

        retrieved = manager.get_role(created.id)
        assert retrieved.id == created.id

    def test_update_role(self, manager):
        """Test updating role"""
        role = manager.create_role(
            name="Old Name",
            role_type=RoleType.CUSTOM,
        )

        success = manager.update_role(
            role.id,
            name="New Name",
            permissions=["new:permission"],
        )

        assert success
        updated = manager.get_role(role.id)
        assert updated.name == "New Name"

    def test_system_roles(self, manager):
        """Test system roles exist"""
        admin_role = manager.get_role("role_super_admin")
        assert admin_role is not None
        assert admin_role.is_system

    def test_assign_role(self, manager):
        """Test role assignment"""
        role = manager.create_role("Test", RoleType.CUSTOM)

        success = manager.assign_role("user_1", role.id)
        assert success

        user_roles = manager.get_user_roles("user_1")
        assert len(user_roles) > 0

    def test_revoke_role(self, manager):
        """Test role revocation"""
        role = manager.create_role("Test", RoleType.CUSTOM)
        manager.assign_role("user_1", role.id)

        success = manager.revoke_role("user_1", role.id)
        assert success

        user_roles = manager.get_user_roles("user_1")
        assert len(user_roles) == 0

    def test_effective_permissions(self, manager):
        """Test effective permissions with inheritance"""
        # Create role with permissions
        role = manager.create_role(
            name="Developer",
            role_type=RoleType.CUSTOM,
            permissions=["database:read", "database:write"],
        )

        manager.assign_role("user_1", role.id)

        permissions = manager.get_effective_permissions("user_1")
        assert "database:read" in permissions
        assert "database:write" in permissions


class TestPermissionEngine:
    """Test permission engine"""

    @pytest.fixture
    def engine(self):
        return PermissionEngine()

    def test_check_exact_permission(self, engine):
        """Test exact permission match"""
        user_perms = {"database:read", "query:execute"}

        assert engine.check_permission(user_perms, "database:read")
        assert not engine.check_permission(user_perms, "database:write")

    def test_wildcard_permission(self, engine):
        """Test wildcard permissions"""
        user_perms = {"database:*"}

        assert engine.check_permission(user_perms, "database:read")
        assert engine.check_permission(user_perms, "database:write")
        assert engine.check_permission(user_perms, "database:delete")

    def test_super_admin(self, engine):
        """Test super admin wildcard"""
        user_perms = {"*"}

        assert engine.check_permission(user_perms, "anything:anywhere")

    def test_hierarchical_permissions(self, engine):
        """Test permission hierarchy"""
        user_perms = {"database:admin"}

        # Admin implies read, write, etc.
        assert engine.check_permission(user_perms, "database:read")
        assert engine.check_permission(user_perms, "database:write")

    def test_multiple_permissions(self, engine):
        """Test checking multiple permissions"""
        user_perms = {"database:read", "query:execute"}

        # All required
        assert engine.check_multiple_permissions(
            user_perms,
            ["database:read", "query:execute"],
            require_all=True,
        )

        # Any required
        assert engine.check_multiple_permissions(
            user_perms,
            ["database:read", "nonexistent:perm"],
            require_all=False,
        )

    def test_get_resource_permissions(self, engine):
        """Test getting resource permissions"""
        user_perms = {"database:read", "database:write"}

        actions = engine.get_resource_permissions("database", user_perms)
        assert "read" in actions
        assert "write" in actions

    def test_explain_permission(self, engine):
        """Test permission explanation"""
        user_perms = {"database:*"}

        explanation = engine.explain_permission_check(user_perms, "database:read")
        assert explanation['granted']
        assert "wildcard" in explanation['reason'].lower()


class TestPolicyEvaluator:
    """Test ABAC policy evaluator"""

    @pytest.fixture
    def evaluator(self):
        return PolicyEvaluator()

    def test_evaluate_allow_policy(self, evaluator):
        """Test ALLOW policy evaluation"""
        policy = Policy(
            id="policy_1",
            name="Allow Read",
            effect=PolicyEffect.ALLOW,
            resources=["database_1"],
            actions=["read"],
            conditions={"department": "engineering"},
        )

        context = {"department": "engineering"}

        result = evaluator.evaluate(
            [policy],
            resource="database_1",
            action="read",
            context=context,
        )

        assert result

    def test_evaluate_deny_policy(self, evaluator):
        """Test DENY policy evaluation"""
        policy = Policy(
            id="policy_1",
            name="Deny Write",
            effect=PolicyEffect.DENY,
            resources=["database_1"],
            actions=["write"],
            conditions={},
        )

        result = evaluator.evaluate(
            [policy],
            resource="database_1",
            action="write",
            context={},
        )

        assert not result

    def test_policy_with_conditions(self, evaluator):
        """Test policy with conditions"""
        policy = Policy(
            id="policy_1",
            name="Conditional Access",
            effect=PolicyEffect.ALLOW,
            resources=["*"],
            actions=["read"],
            conditions={"ip_range": "10.0.0.0/8"},
        )

        # Matching conditions
        result1 = evaluator.evaluate(
            [policy],
            resource="any_resource",
            action="read",
            context={"ip_range": "10.0.0.0/8"},
        )
        assert result1

        # Non-matching conditions
        result2 = evaluator.evaluate(
            [policy],
            resource="any_resource",
            action="read",
            context={"ip_range": "192.168.0.0/16"},
        )
        assert not result2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
