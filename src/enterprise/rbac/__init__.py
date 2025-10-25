"""Advanced Role-Based Access Control (RBAC) for AI-Shell."""

from .role_manager import RoleManager, Role, RoleType
from .permission_engine import PermissionEngine, Permission, PermissionScope
from .policy_evaluator import PolicyEvaluator, Policy, PolicyEffect
from .rbac_middleware import RBACMiddleware, require_permission, require_role

__all__ = [
    "RoleManager",
    "Role",
    "RoleType",
    "PermissionEngine",
    "Permission",
    "PermissionScope",
    "PolicyEvaluator",
    "Policy",
    "PolicyEffect",
    "RBACMiddleware",
    "require_permission",
    "require_role",
]
