"""
Comprehensive tests for tenant_middleware.py

Tests:
- Tenant resolution from headers
- Subdomain-based tenant resolution
- Path-based tenant resolution
- Context management
- Tenant validation
- Decorators (require_tenant, with_tenant)
"""

import pytest
from src.enterprise.tenancy.tenant_middleware import (
    TenantMiddleware,
    TenantContext,
    TenantValidator,
    require_tenant,
    with_tenant,
)
from src.enterprise.tenancy.tenant_manager import TenantManager, TenantTier
import tempfile
import os


@pytest.fixture
def tenant_middleware():
    """Create TenantMiddleware instance"""
    return TenantMiddleware()


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def tenant_manager(temp_db):
    return TenantManager(db_path=temp_db)


@pytest.fixture
def tenant_validator(tenant_manager):
    return TenantValidator(tenant_manager)


class TestTenantResolution:
    """Test tenant resolution from various sources"""

    def test_resolve_from_headers_standard(self, tenant_middleware):
        """Test resolving tenant from standard header"""
        headers = {'X-Tenant-ID': 'acme-corp'}

        tenant_id = tenant_middleware.resolve_tenant_from_headers(headers)

        assert tenant_id == 'acme-corp'

    def test_resolve_from_headers_alternate(self, tenant_middleware):
        """Test resolving tenant from alternate headers"""
        headers = {'X-Tenant': 'test-tenant'}

        tenant_id = tenant_middleware.resolve_tenant_from_headers(headers)

        assert tenant_id == 'test-tenant'

    def test_resolve_from_headers_tenant_id(self, tenant_middleware):
        """Test resolving from Tenant-ID header"""
        headers = {'Tenant-ID': 'another-tenant'}

        tenant_id = tenant_middleware.resolve_tenant_from_headers(headers)

        assert tenant_id == 'another-tenant'

    def test_resolve_from_headers_missing(self, tenant_middleware):
        """Test resolving when header is missing"""
        headers = {}

        tenant_id = tenant_middleware.resolve_tenant_from_headers(headers)

        assert tenant_id is None

    def test_resolve_from_subdomain(self, tenant_middleware):
        """Test resolving tenant from subdomain"""
        tenant_id = tenant_middleware.resolve_tenant_from_subdomain(
            host='acme.example.com',
            base_domain='example.com'
        )

        assert tenant_id == 'acme'

    def test_resolve_from_subdomain_with_port(self, tenant_middleware):
        """Test subdomain resolution with port"""
        tenant_id = tenant_middleware.resolve_tenant_from_subdomain(
            host='tenant.example.com:8080',
            base_domain='example.com'
        )

        assert tenant_id == 'tenant'

    def test_resolve_from_subdomain_www_ignored(self, tenant_middleware):
        """Test www subdomain is ignored"""
        tenant_id = tenant_middleware.resolve_tenant_from_subdomain(
            host='www.example.com',
            base_domain='example.com'
        )

        assert tenant_id is None

    def test_resolve_from_subdomain_no_match(self, tenant_middleware):
        """Test subdomain resolution with no match"""
        tenant_id = tenant_middleware.resolve_tenant_from_subdomain(
            host='example.com',
            base_domain='example.com'
        )

        assert tenant_id is None

    def test_resolve_from_path_tenants_prefix(self, tenant_middleware):
        """Test resolving from /tenants/{id} path"""
        tenant_id = tenant_middleware.resolve_tenant_from_path('/tenants/acme-corp/dashboard')

        assert tenant_id == 'acme-corp'

    def test_resolve_from_path_t_prefix(self, tenant_middleware):
        """Test resolving from /t/{id} path"""
        tenant_id = tenant_middleware.resolve_tenant_from_path('/t/test-tenant/api')

        assert tenant_id == 'test-tenant'

    def test_resolve_from_path_no_match(self, tenant_middleware):
        """Test path resolution with no match"""
        tenant_id = tenant_middleware.resolve_tenant_from_path('/api/users')

        assert tenant_id is None

    def test_resolve_from_path_empty(self, tenant_middleware):
        """Test path resolution with empty path"""
        tenant_id = tenant_middleware.resolve_tenant_from_path('')

        assert tenant_id is None


class TestMultiSourceResolution:
    """Test resolving tenant from multiple sources"""

    def test_resolve_priority_headers_first(self, tenant_middleware):
        """Test headers have priority over other sources"""
        tenant_id = tenant_middleware.resolve_tenant(
            headers={'X-Tenant-ID': 'header-tenant'},
            host='subdomain.example.com',
            path='/tenants/path-tenant',
            base_domain='example.com'
        )

        assert tenant_id == 'header-tenant'

    def test_resolve_priority_subdomain_second(self, tenant_middleware):
        """Test subdomain has priority over path"""
        tenant_id = tenant_middleware.resolve_tenant(
            headers={},
            host='subdomain.example.com',
            path='/tenants/path-tenant',
            base_domain='example.com'
        )

        assert tenant_id == 'subdomain'

    def test_resolve_priority_path_last(self, tenant_middleware):
        """Test path is used as fallback"""
        tenant_id = tenant_middleware.resolve_tenant(
            headers={},
            host='example.com',
            path='/tenants/path-tenant',
            base_domain='example.com'
        )

        assert tenant_id == 'path-tenant'

    def test_resolve_returns_none_when_no_source(self, tenant_middleware):
        """Test returns None when no tenant can be resolved"""
        tenant_id = tenant_middleware.resolve_tenant(
            headers={},
            host='example.com',
            path='/api/users',
            base_domain='example.com'
        )

        assert tenant_id is None


class TestContextManagement:
    """Test tenant context management"""

    def test_create_context(self, tenant_middleware):
        """Test creating tenant context"""
        context = tenant_middleware.create_context(
            tenant_id='test-tenant',
            user_id='user-123',
            request_id='req-456'
        )

        assert isinstance(context, TenantContext)
        assert context.tenant_id == 'test-tenant'
        assert context.user_id == 'user-123'
        assert context.request_id == 'req-456'

    def test_create_context_with_metadata(self, tenant_middleware):
        """Test creating context with metadata"""
        context = tenant_middleware.create_context(
            tenant_id='test',
            metadata={'key': 'value'}
        )

        assert context.metadata['key'] == 'value'

    def test_set_and_get_current_tenant(self, tenant_middleware):
        """Test setting and getting current tenant"""
        TenantMiddleware.set_current_tenant('current-tenant')

        tenant_id = TenantMiddleware.get_current_tenant()

        assert tenant_id == 'current-tenant'

    def test_set_and_get_current_user(self, tenant_middleware):
        """Test setting and getting current user"""
        TenantMiddleware.set_current_user('user-123')

        user_id = TenantMiddleware.get_current_user()

        assert user_id == 'user-123'

    def test_clear_context(self, tenant_middleware):
        """Test clearing context"""
        TenantMiddleware.set_current_tenant('tenant')
        TenantMiddleware.set_current_user('user')

        TenantMiddleware.clear_context()

        assert TenantMiddleware.get_current_tenant() is None
        assert TenantMiddleware.get_current_user() is None


class TestTenantContextDataclass:
    """Test TenantContext dataclass"""

    def test_tenant_context_minimal(self):
        """Test creating context with minimal fields"""
        context = TenantContext(tenant_id='test')

        assert context.tenant_id == 'test'
        assert context.user_id is None
        assert context.metadata == {}

    def test_tenant_context_full(self):
        """Test creating context with all fields"""
        context = TenantContext(
            tenant_id='test',
            user_id='user',
            request_id='req',
            metadata={'key': 'value'}
        )

        assert context.tenant_id == 'test'
        assert context.user_id == 'user'
        assert context.request_id == 'req'
        assert context.metadata['key'] == 'value'


class TestRequireTenantDecorator:
    """Test require_tenant decorator"""

    def test_require_tenant_with_context(self):
        """Test decorated function works with tenant context"""
        @require_tenant
        def test_function():
            return "success"

        TenantMiddleware.set_current_tenant('test-tenant')

        result = test_function()

        assert result == "success"

        TenantMiddleware.clear_context()

    def test_require_tenant_without_context(self):
        """Test decorated function fails without tenant context"""
        @require_tenant
        def test_function():
            return "success"

        TenantMiddleware.clear_context()

        with pytest.raises(ValueError, match="No tenant context"):
            test_function()

    def test_require_tenant_preserves_function_name(self):
        """Test decorator preserves function metadata"""
        @require_tenant
        def test_function():
            """Test docstring"""
            pass

        assert test_function.__name__ == 'test_function'
        assert test_function.__doc__ == "Test docstring"


class TestWithTenantDecorator:
    """Test with_tenant decorator"""

    def test_with_tenant_sets_context(self):
        """Test decorator sets tenant context"""
        @with_tenant('decorator-tenant')
        def test_function():
            return TenantMiddleware.get_current_tenant()

        result = test_function()

        assert result == 'decorator-tenant'

    def test_with_tenant_restores_previous_context(self):
        """Test decorator restores previous context"""
        TenantMiddleware.set_current_tenant('original-tenant')

        @with_tenant('temporary-tenant')
        def test_function():
            assert TenantMiddleware.get_current_tenant() == 'temporary-tenant'

        test_function()

        # Should be restored
        assert TenantMiddleware.get_current_tenant() == 'original-tenant'

        TenantMiddleware.clear_context()

    def test_with_tenant_handles_no_previous_context(self):
        """Test decorator works when no previous context"""
        TenantMiddleware.clear_context()

        @with_tenant('test-tenant')
        def test_function():
            return TenantMiddleware.get_current_tenant()

        result = test_function()

        assert result == 'test-tenant'
        assert TenantMiddleware.get_current_tenant() is None

    def test_with_tenant_handles_exceptions(self):
        """Test decorator restores context even on exception"""
        TenantMiddleware.set_current_tenant('original')

        @with_tenant('temporary')
        def failing_function():
            raise RuntimeError("Test error")

        with pytest.raises(RuntimeError):
            failing_function()

        # Context should be restored
        assert TenantMiddleware.get_current_tenant() == 'original'

        TenantMiddleware.clear_context()


class TestTenantValidator:
    """Test TenantValidator class"""

    def test_validate_existing_active_tenant(self, tenant_validator, tenant_manager):
        """Test validating active tenant"""
        tenant = tenant_manager.create_tenant(
            name="Valid Tenant",
            slug="valid-tenant",
            owner_id="user_123",
            tier=TenantTier.STARTER
        )

        is_valid = tenant_validator.validate_tenant(tenant.id)

        assert is_valid

    def test_validate_nonexistent_tenant(self, tenant_validator):
        """Test validating non-existent tenant"""
        is_valid = tenant_validator.validate_tenant("nonexistent")

        assert not is_valid

    def test_validate_suspended_tenant(self, tenant_validator, tenant_manager):
        """Test validating suspended tenant"""
        from src.enterprise.tenancy.tenant_manager import TenantStatus

        tenant = tenant_manager.create_tenant(
            name="Suspended",
            slug="suspended",
            owner_id="user",
            tier=TenantTier.STARTER
        )

        tenant_manager.update_tenant(tenant.id, status=TenantStatus.SUSPENDED)

        is_valid = tenant_validator.validate_tenant(tenant.id)

        assert not is_valid

    def test_validate_tenant_access(self, tenant_validator, tenant_manager):
        """Test validating user access to tenant"""
        tenant = tenant_manager.create_tenant(
            name="Access Test",
            slug="access-test",
            owner_id="user_owner",
            tier=TenantTier.STARTER
        )

        has_access = tenant_validator.validate_tenant_access(tenant.id, "user_owner")

        assert has_access

    def test_validate_feature_access_available(self, tenant_validator, tenant_manager):
        """Test validating feature access when available"""
        tenant = tenant_manager.create_tenant(
            name="Feature Test",
            slug="feature-test",
            owner_id="user",
            tier=TenantTier.ENTERPRISE
        )

        has_feature = tenant_validator.validate_feature_access(tenant.id, 'sso')

        assert has_feature

    def test_validate_feature_access_unavailable(self, tenant_validator, tenant_manager):
        """Test validating feature access when unavailable"""
        tenant = tenant_manager.create_tenant(
            name="Limited",
            slug="limited",
            owner_id="user",
            tier=TenantTier.FREE
        )

        has_feature = tenant_validator.validate_feature_access(tenant.id, 'sso')

        assert not has_feature

    def test_validate_feature_nonexistent_tenant(self, tenant_validator):
        """Test feature validation for non-existent tenant"""
        has_feature = tenant_validator.validate_feature_access("nonexistent", "any_feature")

        assert not has_feature


class TestCustomTenantHeaders:
    """Test custom tenant header configuration"""

    def test_custom_tenant_header(self):
        """Test using custom tenant header"""
        middleware = TenantMiddleware(tenant_header='X-Custom-Tenant')

        headers = {'X-Custom-Tenant': 'custom-tenant'}
        tenant_id = middleware.resolve_tenant_from_headers(headers)

        assert tenant_id == 'custom-tenant'

    def test_custom_user_header(self):
        """Test using custom user header"""
        middleware = TenantMiddleware(user_header='X-Custom-User')

        # This would be used in actual request processing
        assert middleware.user_header == 'X-Custom-User'

    def test_require_tenant_flag(self):
        """Test require_tenant configuration"""
        middleware = TenantMiddleware(require_tenant=True)

        assert middleware.require_tenant is True

        middleware_optional = TenantMiddleware(require_tenant=False)

        assert middleware_optional.require_tenant is False


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_resolve_subdomain_none_parameters(self, tenant_middleware):
        """Test subdomain resolution with None parameters"""
        tenant_id = tenant_middleware.resolve_tenant_from_subdomain(None, None)

        assert tenant_id is None

    def test_resolve_path_with_trailing_slash(self, tenant_middleware):
        """Test path resolution with trailing slash"""
        tenant_id = tenant_middleware.resolve_tenant_from_path('/tenants/test/')

        assert tenant_id == 'test'

    def test_resolve_path_without_leading_slash(self, tenant_middleware):
        """Test path resolution without leading slash"""
        tenant_id = tenant_middleware.resolve_tenant_from_path('tenants/test/page')

        assert tenant_id == 'test'

    def test_context_isolation_between_requests(self):
        """Test contexts are properly isolated"""
        TenantMiddleware.set_current_tenant('tenant-1')
        TenantMiddleware.set_current_user('user-1')

        # Simulate new request
        TenantMiddleware.clear_context()
        TenantMiddleware.set_current_tenant('tenant-2')

        assert TenantMiddleware.get_current_tenant() == 'tenant-2'
        assert TenantMiddleware.get_current_user() is None

        TenantMiddleware.clear_context()
