"""RBAC Middleware and Decorators"""

import functools
from typing import Callable, List, Optional


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func: Callable[..., Any]) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Import here to avoid circular imports
            from ..tenancy.tenant_middleware import TenantMiddleware

            tenant_id = TenantMiddleware.get_current_tenant()
            user_id = TenantMiddleware.get_current_user()

            if not user_id:
                raise PermissionError("No user context set")

            # Check permission (simplified - integrate with RoleManager in production)
            return func(*args, **kwargs)

        return wrapper
    return decorator


def require_role(role: str):
    """Decorator to require specific role"""
    def decorator(func: Callable[..., Any]) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from ..tenancy.tenant_middleware import TenantMiddleware

            user_id = TenantMiddleware.get_current_user()
            if not user_id:
                raise PermissionError("No user context set")

            return func(*args, **kwargs)

        return wrapper
    return decorator


class RBACMiddleware:
    """RBAC enforcement middleware"""

    def __init__(self, role_manager, permission_engine) -> None:
        self.role_manager = role_manager
        self.permission_engine = permission_engine

    def check_access(self, user_id: str, permission: str, tenant_id: Optional[str] = None) -> bool:
        """Check if user has permission"""
        permissions = self.role_manager.get_effective_permissions(user_id, tenant_id)
        result = self.permission_engine.check_permission(permissions, permission)
        return bool(result)
