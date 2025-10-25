"""
Comprehensive coverage tests for RBAC Permission Engine
Targeting uncovered branches, error paths, and edge cases
"""

import pytest
from src.enterprise.rbac.permission_engine import (
    PermissionEngine,
    Permission,
    PermissionScope,
)


class TestPermissionDataclass:
    """Test Permission dataclass"""

    def test_permission_creation_minimal(self):
        """Test creating permission with minimal data"""
        perm = Permission(resource="database", action="read")

        assert perm.resource == "database"
        assert perm.action == "read"
        assert perm.scope == PermissionScope.RESOURCE
        assert perm.conditions is None

    def test_permission_creation_full(self):
        """Test creating permission with all fields"""
        conditions = {"tenant_id": "123"}
        perm = Permission(
            resource="query",
            action="execute",
            scope=PermissionScope.TENANT,
            conditions=conditions
        )

        assert perm.resource == "query"
        assert perm.action == "execute"
        assert perm.scope == PermissionScope.TENANT
        assert perm.conditions == conditions

    def test_permission_to_string(self):
        """Test converting permission to string"""
        perm = Permission(resource="database", action="read")

        assert perm.to_string() == "database:read"

    def test_permission_from_string_valid(self):
        """Test creating permission from string"""
        perm = Permission.from_string("database:write")

        assert perm.resource == "database"
        assert perm.action == "write"

    def test_permission_from_string_invalid_no_colon(self):
        """Test from_string with invalid format"""
        with pytest.raises(ValueError, match="Invalid permission format"):
            Permission.from_string("invalid")

    def test_permission_from_string_invalid_empty(self):
        """Test from_string with empty parts"""
        with pytest.raises(ValueError):
            Permission.from_string(":")

    def test_permission_from_string_wildcard(self):
        """Test from_string with wildcard"""
        perm = Permission.from_string("database:*")

        assert perm.resource == "database"
        assert perm.action == "*"

    def test_permission_scope_enum_values(self):
        """Test all permission scope values"""
        assert PermissionScope.SYSTEM.value == "system"
        assert PermissionScope.TENANT.value == "tenant"
        assert PermissionScope.DATABASE.value == "database"
        assert PermissionScope.RESOURCE.value == "resource"


class TestPermissionEngineBasicChecks:
    """Test basic permission checking"""

    def test_engine_initialization(self):
        """Test engine initialization"""
        engine = PermissionEngine()

        assert engine.action_hierarchy is not None
        assert "admin" in engine.action_hierarchy
        assert "write" in engine.action_hierarchy
        assert "read" in engine.action_hierarchy

    def test_check_permission_super_admin_wildcard(self):
        """Test super admin wildcard grants all permissions"""
        engine = PermissionEngine()

        assert engine.check_permission({"*"}, "database:read")
        assert engine.check_permission({"*"}, "query:execute")
        assert engine.check_permission({"*"}, "anything:anything")

    def test_check_permission_super_admin_colon_wildcard(self):
        """Test *:* wildcard grants all permissions"""
        engine = PermissionEngine()

        assert engine.check_permission({"*:*"}, "database:read")
        assert engine.check_permission({"*:*"}, "anything:anything")

    def test_check_permission_exact_match(self):
        """Test exact permission match"""
        engine = PermissionEngine()

        assert engine.check_permission(
            {"database:read"},
            "database:read"
        )

    def test_check_permission_no_match(self):
        """Test permission check fails with no match"""
        engine = PermissionEngine()

        assert not engine.check_permission(
            {"database:read"},
            "database:write"
        )

    def test_check_permission_resource_wildcard(self):
        """Test resource wildcard permission"""
        engine = PermissionEngine()

        assert engine.check_permission(
            {"database:*"},
            "database:read"
        )
        assert engine.check_permission(
            {"database:*"},
            "database:write"
        )

    def test_check_permission_invalid_required_format(self):
        """Test invalid required permission format"""
        engine = PermissionEngine()

        assert not engine.check_permission(
            {"database:read"},
            "invalid_format"
        )

    def test_check_permission_empty_user_permissions(self):
        """Test with empty user permissions"""
        engine = PermissionEngine()

        assert not engine.check_permission(
            set(),
            "database:read"
        )


class TestPermissionHierarchy:
    """Test hierarchical permission checking"""

    def test_admin_implies_write(self):
        """Test admin action implies write"""
        engine = PermissionEngine()

        assert engine.check_permission(
            {"database:admin"},
            "database:write"
        )

    def test_admin_implies_read(self):
        """Test admin action implies read"""
        engine = PermissionEngine()

        assert engine.check_permission(
            {"database:admin"},
            "database:read"
        )

    def test_admin_implies_execute(self):
        """Test admin action implies execute"""
        engine = PermissionEngine()

        assert engine.check_permission(
            {"database:admin"},
            "database:execute"
        )

    def test_admin_implies_delete(self):
        """Test admin action implies delete"""
        engine = PermissionEngine()

        assert engine.check_permission(
            {"database:admin"},
            "database:delete"
        )

    def test_write_implies_read(self):
        """Test write action implies read"""
        engine = PermissionEngine()

        assert engine.check_permission(
            {"database:write"},
            "database:read"
        )

    def test_write_implies_create(self):
        """Test write action implies create"""
        engine = PermissionEngine()

        assert engine.check_permission(
            {"database:write"},
            "database:create"
        )

    def test_write_implies_update(self):
        """Test write action implies update"""
        engine = PermissionEngine()

        assert engine.check_permission(
            {"database:write"},
            "database:update"
        )

    def test_execute_implies_read(self):
        """Test execute action implies read"""
        engine = PermissionEngine()

        assert engine.check_permission(
            {"query:execute"},
            "query:read"
        )

    def test_delete_implies_read(self):
        """Test delete action implies read"""
        engine = PermissionEngine()

        assert engine.check_permission(
            {"record:delete"},
            "record:read"
        )

    def test_read_implies_nothing(self):
        """Test read action implies no other actions"""
        engine = PermissionEngine()

        assert not engine.check_permission(
            {"database:read"},
            "database:write"
        )
        assert not engine.check_permission(
            {"database:read"},
            "database:delete"
        )

    def test_hierarchy_different_resources(self):
        """Test hierarchy doesn't apply across resources"""
        engine = PermissionEngine()

        assert not engine.check_permission(
            {"database:admin"},
            "query:read"
        )


class TestMultiplePermissions:
    """Test checking multiple permissions"""

    def test_check_multiple_require_all_success(self):
        """Test checking multiple permissions with require_all=True"""
        engine = PermissionEngine()

        assert engine.check_multiple_permissions(
            {"database:read", "database:write"},
            ["database:read", "database:write"],
            require_all=True
        )

    def test_check_multiple_require_all_failure(self):
        """Test require_all fails if one missing"""
        engine = PermissionEngine()

        assert not engine.check_multiple_permissions(
            {"database:read"},
            ["database:read", "database:write"],
            require_all=True
        )

    def test_check_multiple_require_any_success(self):
        """Test require_any succeeds with one match"""
        engine = PermissionEngine()

        assert engine.check_multiple_permissions(
            {"database:read"},
            ["database:read", "database:write"],
            require_all=False
        )

    def test_check_multiple_require_any_failure(self):
        """Test require_any fails with no matches"""
        engine = PermissionEngine()

        assert not engine.check_multiple_permissions(
            {"database:read"},
            ["database:write", "database:delete"],
            require_all=False
        )

    def test_check_multiple_empty_required(self):
        """Test with empty required permissions"""
        engine = PermissionEngine()

        assert engine.check_multiple_permissions(
            {"database:read"},
            [],
            require_all=True
        )

    def test_check_multiple_with_wildcards(self):
        """Test multiple checks with wildcards"""
        engine = PermissionEngine()

        assert engine.check_multiple_permissions(
            {"database:*"},
            ["database:read", "database:write", "database:delete"],
            require_all=True
        )


class TestWildcardExpansion:
    """Test wildcard permission expansion"""

    def test_expand_wildcards_action_wildcard(self):
        """Test expanding action wildcard"""
        engine = PermissionEngine()

        expanded = engine.expand_wildcards({"database:*"})

        assert "database:read" in expanded
        assert "database:write" in expanded
        assert "database:execute" in expanded
        assert "database:delete" in expanded
        assert "database:admin" in expanded

    def test_expand_wildcards_resource_wildcard(self):
        """Test resource wildcard is kept as-is"""
        engine = PermissionEngine()

        expanded = engine.expand_wildcards({"*:read"})

        assert "*:read" in expanded

    def test_expand_wildcards_specific_permission(self):
        """Test specific permissions pass through"""
        engine = PermissionEngine()

        expanded = engine.expand_wildcards({"database:read", "query:execute"})

        assert "database:read" in expanded
        assert "query:execute" in expanded

    def test_expand_wildcards_no_colon(self):
        """Test permissions without colon pass through"""
        engine = PermissionEngine()

        expanded = engine.expand_wildcards({"admin", "user"})

        assert "admin" in expanded
        assert "user" in expanded

    def test_expand_wildcards_mixed(self):
        """Test expanding mixed permissions"""
        engine = PermissionEngine()

        expanded = engine.expand_wildcards({
            "database:*",
            "query:read",
            "admin"
        })

        assert "database:read" in expanded
        assert "database:write" in expanded
        assert "query:read" in expanded
        assert "admin" in expanded


class TestPermissionFiltering:
    """Test filtering items by permission"""

    def test_filter_by_permission_all_allowed(self):
        """Test filtering when user has permission for all"""
        engine = PermissionEngine()

        items = [
            {"id": "db1", "name": "Database 1"},
            {"id": "db2", "name": "Database 2"},
        ]

        filtered = engine.filter_by_permission(
            items,
            {"database:*"},
            "id",
            "database:{id}:read"
        )

        assert len(filtered) == 2

    def test_filter_by_permission_partial_allowed(self):
        """Test filtering with partial permissions"""
        engine = PermissionEngine()

        items = [
            {"id": "db1", "name": "Database 1"},
            {"id": "db2", "name": "Database 2"},
        ]

        filtered = engine.filter_by_permission(
            items,
            {"database:db1:read"},
            "id",
            "database:{id}:read"
        )

        assert len(filtered) == 1
        assert filtered[0]["id"] == "db1"

    def test_filter_by_permission_none_allowed(self):
        """Test filtering when no permissions"""
        engine = PermissionEngine()

        items = [
            {"id": "db1", "name": "Database 1"},
            {"id": "db2", "name": "Database 2"},
        ]

        filtered = engine.filter_by_permission(
            items,
            set(),
            "id",
            "database:{id}:read"
        )

        assert len(filtered) == 0

    def test_filter_by_permission_missing_key(self):
        """Test filtering with missing permission key"""
        engine = PermissionEngine()

        items = [
            {"name": "Database 1"},  # No 'id' key
            {"id": "db2", "name": "Database 2"},
        ]

        filtered = engine.filter_by_permission(
            items,
            {"database:*"},
            "id",
            "database:{id}:read"
        )

        assert len(filtered) == 1


class TestPermissionDetails:
    """Test getting permission details"""

    def test_get_permission_details_valid(self):
        """Test getting details for valid permission"""
        engine = PermissionEngine()

        details = engine.get_permission_details("database:admin")

        assert details["permission"] == "database:admin"
        assert details["resource"] == "database"
        assert details["action"] == "admin"
        assert details["scope"] == "resource"
        assert details["is_wildcard"] is False
        assert "write" in details["implied_actions"]
        assert "read" in details["implied_actions"]

    def test_get_permission_details_wildcard(self):
        """Test getting details for wildcard permission"""
        engine = PermissionEngine()

        details = engine.get_permission_details("database:*")

        assert details["is_wildcard"] is True

    def test_get_permission_details_invalid(self):
        """Test getting details for invalid permission"""
        engine = PermissionEngine()

        details = engine.get_permission_details("invalid")

        assert "error" in details
        assert details["permission"] == "invalid"

    def test_get_permission_details_read_action(self):
        """Test details for read action"""
        engine = PermissionEngine()

        details = engine.get_permission_details("database:read")

        assert details["implied_actions"] == []


class TestPermissionValidation:
    """Test permission format validation"""

    def test_validate_permission_format_valid(self):
        """Test validating valid permission formats"""
        engine = PermissionEngine()

        assert engine.validate_permission_format("database:read")
        assert engine.validate_permission_format("query:execute")
        assert engine.validate_permission_format("resource-name:action")
        assert engine.validate_permission_format("resource_name:action_name")

    def test_validate_permission_format_wildcard(self):
        """Test validating wildcard permissions"""
        engine = PermissionEngine()

        assert engine.validate_permission_format("database:*")
        assert engine.validate_permission_format("*:read")

    def test_validate_permission_format_invalid(self):
        """Test validating invalid formats"""
        engine = PermissionEngine()

        assert not engine.validate_permission_format("invalid")
        assert not engine.validate_permission_format(":")
        assert not engine.validate_permission_format("resource:")
        assert not engine.validate_permission_format(":action")
        assert not engine.validate_permission_format("resource:action:extra")


class TestResourcePermissions:
    """Test getting resource-specific permissions"""

    def test_get_resource_permissions_with_wildcard(self):
        """Test getting permissions with full wildcard"""
        engine = PermissionEngine()

        actions = engine.get_resource_permissions(
            "database",
            {"*"}
        )

        assert "read" in actions
        assert "write" in actions
        assert "execute" in actions
        assert "delete" in actions
        assert "admin" in actions

    def test_get_resource_permissions_with_resource_wildcard(self):
        """Test getting permissions with resource wildcard"""
        engine = PermissionEngine()

        actions = engine.get_resource_permissions(
            "database",
            {"database:*"}
        )

        assert len(actions) == 5

    def test_get_resource_permissions_specific(self):
        """Test getting specific resource permissions"""
        engine = PermissionEngine()

        actions = engine.get_resource_permissions(
            "database",
            {"database:read", "database:write"}
        )

        assert "read" in actions
        assert "write" in actions
        assert "create" in actions  # Implied by write
        assert "update" in actions  # Implied by write

    def test_get_resource_permissions_with_admin(self):
        """Test getting permissions with admin action"""
        engine = PermissionEngine()

        actions = engine.get_resource_permissions(
            "database",
            {"database:admin"}
        )

        assert "admin" in actions
        assert "write" in actions
        assert "read" in actions
        assert "execute" in actions
        assert "delete" in actions

    def test_get_resource_permissions_no_match(self):
        """Test getting permissions for unmatched resource"""
        engine = PermissionEngine()

        actions = engine.get_resource_permissions(
            "database",
            {"query:read"}
        )

        assert len(actions) == 0

    def test_get_resource_permissions_invalid_format(self):
        """Test with invalid permission format"""
        engine = PermissionEngine()

        actions = engine.get_resource_permissions(
            "database",
            {"invalid_format", "database:read"}
        )

        assert "read" in actions


class TestPermissionExplanation:
    """Test permission check explanation"""

    def test_explain_permission_granted_wildcard(self):
        """Test explanation for wildcard grant"""
        engine = PermissionEngine()

        explanation = engine.explain_permission_check(
            {"*"},
            "database:read"
        )

        assert explanation["granted"] is True
        assert "wildcard" in explanation["reason"].lower()
        assert explanation["matching_permission"] == "*"

    def test_explain_permission_granted_exact_match(self):
        """Test explanation for exact match"""
        engine = PermissionEngine()

        explanation = engine.explain_permission_check(
            {"database:read"},
            "database:read"
        )

        assert explanation["granted"] is True
        assert "exact" in explanation["reason"].lower()

    def test_explain_permission_granted_resource_wildcard(self):
        """Test explanation for resource wildcard"""
        engine = PermissionEngine()

        explanation = engine.explain_permission_check(
            {"database:*"},
            "database:read"
        )

        assert explanation["granted"] is True
        assert "wildcard" in explanation["reason"].lower()

    def test_explain_permission_granted_hierarchical(self):
        """Test explanation for hierarchical grant"""
        engine = PermissionEngine()

        explanation = engine.explain_permission_check(
            {"database:admin"},
            "database:read"
        )

        assert explanation["granted"] is True
        assert "hierarchical" in explanation["reason"].lower()
        assert "admin" in explanation["reason"]
        assert "read" in explanation["reason"]

    def test_explain_permission_denied(self):
        """Test explanation for denied permission"""
        engine = PermissionEngine()

        explanation = engine.explain_permission_check(
            {"database:read"},
            "database:write"
        )

        assert explanation["granted"] is False
        assert "no matching" in explanation["reason"].lower()

    def test_explain_permission_invalid_format(self):
        """Test explanation for invalid format"""
        engine = PermissionEngine()

        explanation = engine.explain_permission_check(
            {"database:read"},
            "invalid"
        )

        assert explanation["granted"] is False
        assert "invalid" in explanation["reason"].lower()
