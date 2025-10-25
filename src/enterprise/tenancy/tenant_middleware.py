"""
Tenant Middleware

Request-level tenant isolation and context management:
- Automatic tenant resolution from requests
- Tenant context propagation
- Request validation and authorization
- Tenant-aware routing
"""

from typing import Optional, Dict, Any, Callable, TypeVar, cast
from dataclasses import dataclass
from contextvars import ContextVar
import functools


# Context variable for current tenant
_current_tenant: ContextVar[Optional[str]] = ContextVar('current_tenant', default=None)
_current_user: ContextVar[Optional[str]] = ContextVar('current_user', default=None)

# Type variable for generic callables
F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class TenantContext:
    """Tenant context for request processing"""
    tenant_id: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


class TenantMiddleware:
    """
    Middleware for tenant context management.

    Features:
    - Automatic tenant resolution
    - Context propagation
    - Request validation
    - Tenant-aware routing
    """

    def __init__(
        self,
        tenant_header: str = 'X-Tenant-ID',
        user_header: str = 'X-User-ID',
        require_tenant: bool = True,
    ):
        """
        Initialize tenant middleware.

        Args:
            tenant_header: HTTP header containing tenant ID
            user_header: HTTP header containing user ID
            require_tenant: If True, reject requests without tenant ID
        """
        self.tenant_header = tenant_header
        self.user_header = user_header
        self.require_tenant = require_tenant

    def resolve_tenant_from_headers(
        self,
        headers: Dict[str, str],
    ) -> Optional[str]:
        """
        Resolve tenant ID from request headers.

        Args:
            headers: Request headers

        Returns:
            Tenant ID or None
        """
        # Try standard header
        tenant_id = headers.get(self.tenant_header)

        if not tenant_id:
            # Try alternate headers
            tenant_id = headers.get('X-Tenant')
            tenant_id = tenant_id or headers.get('Tenant-ID')

        return tenant_id

    def resolve_tenant_from_subdomain(
        self,
        host: str,
        base_domain: str,
    ) -> Optional[str]:
        """
        Resolve tenant from subdomain.

        Example: acme.example.com -> tenant=acme

        Args:
            host: Request host header
            base_domain: Base domain (e.g., example.com)

        Returns:
            Tenant ID or None
        """
        if not host or not base_domain:
            return None

        # Remove port if present
        host = host.split(':')[0]

        if host.endswith(f'.{base_domain}'):
            # Extract subdomain
            subdomain = host[:-len(f'.{base_domain}')]
            # Ignore www
            if subdomain and subdomain != 'www':
                return subdomain

        return None

    def resolve_tenant_from_path(
        self,
        path: str,
    ) -> Optional[str]:
        """
        Resolve tenant from URL path.

        Example: /tenants/acme/... -> tenant=acme

        Args:
            path: Request path

        Returns:
            Tenant ID or None
        """
        if not path:
            return None

        parts = path.strip('/').split('/')

        # Check for /tenants/{tenant_id}/... pattern
        if len(parts) >= 2 and parts[0] == 'tenants':
            return parts[1]

        # Check for /t/{tenant_id}/... pattern
        if len(parts) >= 2 and parts[0] == 't':
            return parts[1]

        return None

    def resolve_tenant(
        self,
        headers: Optional[Dict[str, str]] = None,
        host: Optional[str] = None,
        path: Optional[str] = None,
        base_domain: Optional[str] = None,
    ) -> Optional[str]:
        """
        Resolve tenant ID using multiple strategies.

        Priority:
        1. Headers
        2. Subdomain
        3. URL path

        Args:
            headers: Request headers
            host: Request host
            path: Request path
            base_domain: Base domain for subdomain resolution

        Returns:
            Tenant ID or None
        """
        # Try headers first
        if headers:
            tenant_id = self.resolve_tenant_from_headers(headers)
            if tenant_id:
                return tenant_id

        # Try subdomain
        if host and base_domain:
            tenant_id = self.resolve_tenant_from_subdomain(host, base_domain)
            if tenant_id:
                return tenant_id

        # Try path
        if path:
            tenant_id = self.resolve_tenant_from_path(path)
            if tenant_id:
                return tenant_id

        return None

    def create_context(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TenantContext:
        """Create tenant context"""
        return TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            metadata=metadata or {},
        )

    @staticmethod
    def set_current_tenant(tenant_id: str) -> None:
        """Set current tenant in context"""
        _current_tenant.set(tenant_id)

    @staticmethod
    def get_current_tenant() -> Optional[str]:
        """Get current tenant from context"""
        return _current_tenant.get()

    @staticmethod
    def set_current_user(user_id: str) -> None:
        """Set current user in context"""
        _current_user.set(user_id)

    @staticmethod
    def get_current_user() -> Optional[str]:
        """Get current user from context"""
        return _current_user.get()

    @staticmethod
    def clear_context() -> None:
        """Clear tenant and user context"""
        _current_tenant.set(None)
        _current_user.set(None)


def require_tenant(func: F) -> F:
    """
    Decorator to require tenant context.

    Raises ValueError if no tenant is set in context.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tenant_id = TenantMiddleware.get_current_tenant()
        if not tenant_id:
            raise ValueError("No tenant context set")
        return func(*args, **kwargs)

    return cast(F, wrapper)


def with_tenant(tenant_id: str) -> Callable[[F], F]:
    """
    Decorator to execute function with specific tenant context.

    Example:
        @with_tenant('acme-corp')
        def process_data():
            # Runs with acme-corp tenant context
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Save previous context
            prev_tenant = TenantMiddleware.get_current_tenant()

            try:
                # Set new context
                TenantMiddleware.set_current_tenant(tenant_id)
                return func(*args, **kwargs)
            finally:
                # Restore previous context
                if prev_tenant:
                    TenantMiddleware.set_current_tenant(prev_tenant)
                else:
                    _current_tenant.set(None)

        return cast(F, wrapper)

    return decorator


class TenantValidator:
    """Validates tenant access and permissions"""

    def __init__(self, tenant_manager: Any) -> None:
        """
        Initialize validator.

        Args:
            tenant_manager: TenantManager instance
        """
        self.tenant_manager = tenant_manager

    def validate_tenant(self, tenant_id: str) -> bool:
        """
        Validate that tenant exists and is active.

        Args:
            tenant_id: Tenant ID

        Returns:
            True if valid
        """
        tenant = self.tenant_manager.get_tenant(tenant_id)

        if not tenant:
            return False

        result: Any = tenant.is_active()
        return bool(result)

    def validate_tenant_access(
        self,
        tenant_id: str,
        user_id: str,
    ) -> bool:
        """
        Validate that user has access to tenant.

        Args:
            tenant_id: Tenant ID
            user_id: User ID

        Returns:
            True if user has access
        """
        # In a real implementation, check user-tenant relationship
        # For now, return True if tenant is valid
        return self.validate_tenant(tenant_id)

    def validate_feature_access(
        self,
        tenant_id: str,
        feature: str,
    ) -> bool:
        """
        Validate that tenant has access to a feature.

        Args:
            tenant_id: Tenant ID
            feature: Feature name

        Returns:
            True if tenant has feature
        """
        tenant = self.tenant_manager.get_tenant(tenant_id)

        if not tenant:
            return False

        result: Any = tenant.has_feature(feature)
        return bool(result)
