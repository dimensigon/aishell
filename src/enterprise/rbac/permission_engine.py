"""
Permission Engine

Fine-grained permission checking and validation:
- Resource-level permissions
- Action-based permissions
- Conditional permissions
- Permission wildcards
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
import re


class PermissionScope(Enum):
    """Permission scopes"""
    SYSTEM = "system"
    TENANT = "tenant"
    DATABASE = "database"
    RESOURCE = "resource"


@dataclass
class Permission:
    """Permission definition"""
    resource: str  # e.g., "database", "query", "user"
    action: str  # e.g., "read", "write", "delete", "*"
    scope: PermissionScope = PermissionScope.RESOURCE
    conditions: Optional[Dict[str, Any]] = None

    def to_string(self) -> str:
        """Convert to permission string (e.g., 'database:read')"""
        return f"{self.resource}:{self.action}"

    @classmethod
    def from_string(cls, permission_str: str) -> 'Permission':
        """Create from permission string"""
        parts = permission_str.split(':', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid permission format: {permission_str}")

        resource, action = parts[0], parts[1]

        # Validate non-empty parts
        if not resource or not action:
            raise ValueError(f"Invalid permission format: {permission_str}")

        return cls(resource=resource, action=action)


class PermissionEngine:
    """
    Evaluates permissions and access control.

    Features:
    - Wildcard permissions (e.g., database:*)
    - Hierarchical permissions
    - Conditional permissions
    - Permission composition
    """

    def __init__(self) -> None:
        """Initialize permission engine"""
        # Define permission hierarchy
        self.action_hierarchy: Dict[str, List[str]] = {
            'admin': ['write', 'read', 'execute', 'delete', 'create', 'update'],
            'write': ['read', 'create', 'update'],
            'read': [],
            'execute': ['read'],
            'delete': ['read'],
        }

    def check_permission(
        self,
        user_permissions: Set[str],
        required_permission: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Check if user has required permission.

        Args:
            user_permissions: Set of user's permissions
            required_permission: Permission to check (e.g., 'database:read')
            context: Optional context for conditional permissions

        Returns:
            True if permission is granted
        """
        # Check for super admin wildcard
        if '*' in user_permissions or '*:*' in user_permissions:
            return True

        # Parse required permission
        try:
            required = Permission.from_string(required_permission)
        except ValueError:
            return False

        # Check exact match
        if required_permission in user_permissions:
            return True

        # Check resource wildcard (e.g., database:*)
        resource_wildcard = f"{required.resource}:*"
        if resource_wildcard in user_permissions:
            return True

        # Check hierarchical permissions
        for user_perm in user_permissions:
            try:
                user_p = Permission.from_string(user_perm)

                # Same resource?
                if user_p.resource != required.resource:
                    continue

                # Check if user's action implies required action
                if self._action_implies(user_p.action, required.action):
                    return True

            except ValueError:
                continue

        return False

    def check_multiple_permissions(
        self,
        user_permissions: Set[str],
        required_permissions: List[str],
        require_all: bool = True,
    ) -> bool:
        """
        Check multiple permissions.

        Args:
            user_permissions: User's permissions
            required_permissions: List of required permissions
            require_all: If True, all permissions required (AND); else any (OR)

        Returns:
            True if permissions are granted
        """
        if require_all:
            return all(
                self.check_permission(user_permissions, perm)
                for perm in required_permissions
            )
        else:
            return any(
                self.check_permission(user_permissions, perm)
                for perm in required_permissions
            )

    def _action_implies(self, user_action: str, required_action: str) -> bool:
        """
        Check if user's action implies required action via hierarchy.

        Example: 'admin' implies 'write', 'read', 'execute', etc.
        """
        if user_action == required_action:
            return True

        if user_action == '*':
            return True

        implied_actions = self.action_hierarchy.get(user_action, [])
        return required_action in implied_actions

    def expand_wildcards(self, permissions: Set[str]) -> Set[str]:
        """
        Expand wildcard permissions to explicit permissions.

        Args:
            permissions: Permissions with wildcards

        Returns:
            Expanded permission set
        """
        expanded = set()

        for perm in permissions:
            if ':' not in perm:
                expanded.add(perm)
                continue

            resource, action = perm.split(':', 1)

            if action == '*':
                # Expand to all actions
                expanded.add(f"{resource}:read")
                expanded.add(f"{resource}:write")
                expanded.add(f"{resource}:execute")
                expanded.add(f"{resource}:delete")
                expanded.add(f"{resource}:admin")
            elif resource == '*':
                # Keep as-is (all resources)
                expanded.add(perm)
            else:
                expanded.add(perm)

        return expanded

    def filter_by_permission(
        self,
        items: List[Dict[str, Any]],
        user_permissions: Set[str],
        permission_key: str,
        permission_format: str,
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of items based on permissions.

        Args:
            items: List of items to filter
            user_permissions: User's permissions
            permission_key: Key in item dict containing resource ID
            permission_format: Permission format string (e.g., 'database:{id}:read')

        Returns:
            Filtered list of items user has permission to access
        """
        filtered = []

        for item in items:
            resource_id = item.get(permission_key)
            if not resource_id:
                continue

            # Format permission string - only pass the resource_id value
            # to avoid conflicts if item dict also contains 'id' key
            format_vars = {permission_key: resource_id}
            required_perm = permission_format.format(**format_vars)

            if self.check_permission(user_permissions, required_perm):
                filtered.append(item)

        return filtered

    def get_permission_details(self, permission_str: str) -> Dict[str, Any]:
        """
        Get detailed information about a permission.

        Args:
            permission_str: Permission string

        Returns:
            Permission details
        """
        try:
            perm = Permission.from_string(permission_str)

            return {
                'permission': permission_str,
                'resource': perm.resource,
                'action': perm.action,
                'scope': perm.scope.value,
                'is_wildcard': '*' in permission_str,
                'implied_actions': self.action_hierarchy.get(perm.action, []),
            }
        except ValueError as e:
            return {
                'error': str(e),
                'permission': permission_str,
            }

    def validate_permission_format(self, permission_str: str) -> bool:
        """Validate permission string format"""
        # Allow patterns like: database:read, database:*, *:read, db-name:action_name
        pattern = r'^[a-zA-Z0-9_*-]+:[a-zA-Z0-9_*-]+$'
        return bool(re.match(pattern, permission_str))

    def get_resource_permissions(
        self,
        resource: str,
        user_permissions: Set[str],
    ) -> Set[str]:
        """
        Get all actions user can perform on a resource.

        Args:
            resource: Resource name
            user_permissions: User's permissions

        Returns:
            Set of actions user can perform
        """
        actions = set()

        # Check for full wildcard
        if '*' in user_permissions or '*:*' in user_permissions:
            actions.update(['read', 'write', 'execute', 'delete', 'admin'])
            return actions

        # Check for resource wildcard
        if f"{resource}:*" in user_permissions:
            actions.update(['read', 'write', 'execute', 'delete', 'admin'])
            return actions

        # Check specific permissions
        for perm in user_permissions:
            if ':' not in perm:
                continue

            perm_resource, perm_action = perm.split(':', 1)

            if perm_resource == resource:
                actions.add(perm_action)

                # Add implied actions
                implied = self.action_hierarchy.get(perm_action, [])
                actions.update(implied)

        return actions

    def explain_permission_check(
        self,
        user_permissions: Set[str],
        required_permission: str,
    ) -> Dict[str, Any]:
        """
        Explain why a permission check passed or failed.

        Args:
            user_permissions: User's permissions
            required_permission: Required permission

        Returns:
            Explanation dict
        """
        result = self.check_permission(user_permissions, required_permission)

        explanation = {
            'granted': result,
            'required_permission': required_permission,
            'reason': None,
            'matching_permission': None,
        }

        if '*' in user_permissions or '*:*' in user_permissions:
            explanation['reason'] = 'User has super admin wildcard permission'
            explanation['matching_permission'] = '*'
            return explanation

        if required_permission in user_permissions:
            explanation['reason'] = 'Exact permission match'
            explanation['matching_permission'] = required_permission
            return explanation

        try:
            required = Permission.from_string(required_permission)
            resource_wildcard = f"{required.resource}:*"

            if resource_wildcard in user_permissions:
                explanation['reason'] = 'Resource wildcard match'
                explanation['matching_permission'] = resource_wildcard
                return explanation

            # Check for hierarchical match
            for user_perm in user_permissions:
                try:
                    user_p = Permission.from_string(user_perm)

                    if user_p.resource == required.resource:
                        if self._action_implies(user_p.action, required.action):
                            explanation['reason'] = f"Hierarchical permission ('{user_p.action}' implies '{required.action}')"
                            explanation['matching_permission'] = user_perm
                            return explanation

                except ValueError:
                    continue

            explanation['reason'] = 'No matching permissions found'

        except ValueError:
            explanation['reason'] = 'Invalid permission format'

        return explanation
