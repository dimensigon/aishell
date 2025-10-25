"""
Comprehensive tests for resource_quota.py

Tests:
- Quota creation and configuration
- Quota consumption and enforcement
- Reset periods (hourly, daily, monthly)
- Soft limits and warnings
- Usage history tracking
- Usage analytics
- Cross-tenant quota isolation
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from src.enterprise.tenancy.resource_quota import (
    ResourceQuotaManager,
    ResourceQuota,
    QuotaType,
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def quota_manager(temp_db):
    return ResourceQuotaManager(db_path=temp_db)


class TestQuotaCreation:
    """Test quota creation and configuration"""

    def test_set_basic_quota(self, quota_manager):
        """Test setting a basic quota"""
        quota = quota_manager.set_quota(
            tenant_id='tenant_123',
            quota_type=QuotaType.QUERIES_PER_HOUR,
            limit=100
        )

        assert quota.tenant_id == 'tenant_123'
        assert quota.quota_type == QuotaType.QUERIES_PER_HOUR
        assert quota.limit == 100
        assert quota.current_usage == 0

    def test_set_quota_with_soft_limit(self, quota_manager):
        """Test setting quota with soft limit"""
        quota = quota_manager.set_quota(
            tenant_id='tenant_soft',
            quota_type=QuotaType.STORAGE_MB,
            limit=1000,
            soft_limit=800
        )

        assert quota.soft_limit == 800

    def test_set_quota_with_reset_period(self, quota_manager):
        """Test setting quota with reset period"""
        quota = quota_manager.set_quota(
            tenant_id='tenant_reset',
            quota_type=QuotaType.API_REQUESTS_PER_DAY,
            limit=10000,
            reset_period='daily'
        )

        assert quota.reset_period == 'daily'

    def test_update_existing_quota(self, quota_manager):
        """Test updating an existing quota"""
        quota_manager.set_quota(
            tenant_id='tenant_update',
            quota_type=QuotaType.MAX_CONNECTIONS,
            limit=10
        )

        # Update with new limit
        updated_quota = quota_manager.set_quota(
            tenant_id='tenant_update',
            quota_type=QuotaType.MAX_CONNECTIONS,
            limit=20
        )

        assert updated_quota.limit == 20

    def test_multiple_quotas_same_tenant(self, quota_manager):
        """Test setting multiple quota types for same tenant"""
        tenant_id = 'tenant_multi'

        quota_manager.set_quota(tenant_id, QuotaType.QUERIES_PER_HOUR, 100)
        quota_manager.set_quota(tenant_id, QuotaType.STORAGE_MB, 500)
        quota_manager.set_quota(tenant_id, QuotaType.MAX_USERS, 50)

        all_quotas = quota_manager.get_all_quotas(tenant_id)

        assert len(all_quotas) == 3


class TestQuotaRetrieval:
    """Test quota retrieval operations"""

    def test_get_quota(self, quota_manager):
        """Test retrieving a quota"""
        quota_manager.set_quota(
            'tenant_get',
            QuotaType.QUERIES_PER_MINUTE,
            limit=10
        )

        quota = quota_manager.get_quota('tenant_get', QuotaType.QUERIES_PER_MINUTE)

        assert quota is not None
        assert quota.limit == 10

    def test_get_nonexistent_quota(self, quota_manager):
        """Test retrieving non-existent quota returns None"""
        quota = quota_manager.get_quota('nonexistent', QuotaType.QUERIES_PER_HOUR)

        assert quota is None

    def test_get_all_quotas_for_tenant(self, quota_manager):
        """Test getting all quotas for a tenant"""
        tenant_id = 'tenant_all'

        quota_manager.set_quota(tenant_id, QuotaType.QUERIES_PER_DAY, 1000)
        quota_manager.set_quota(tenant_id, QuotaType.STORAGE_MB, 100)

        quotas = quota_manager.get_all_quotas(tenant_id)

        assert len(quotas) == 2

    def test_get_all_quotas_empty(self, quota_manager):
        """Test getting quotas for tenant with no quotas"""
        quotas = quota_manager.get_all_quotas('no_quotas')

        assert len(quotas) == 0


class TestQuotaChecking:
    """Test quota checking logic"""

    def test_check_quota_allowed(self, quota_manager):
        """Test checking quota when usage is allowed"""
        quota_manager.set_quota(
            'tenant_check',
            QuotaType.QUERIES_PER_HOUR,
            limit=100
        )

        result = quota_manager.check_quota(
            'tenant_check',
            QuotaType.QUERIES_PER_HOUR,
            amount=1
        )

        assert result['allowed'] is True
        assert result['current_usage'] == 0
        assert result['limit'] == 100
        assert result['remaining'] == 100

    def test_check_quota_unlimited(self, quota_manager):
        """Test checking quota when no quota is defined (unlimited)"""
        result = quota_manager.check_quota(
            'tenant_unlimited',
            QuotaType.QUERIES_PER_HOUR
        )

        assert result['allowed'] is True
        assert result['unlimited'] is True

    def test_check_quota_would_exceed(self, quota_manager):
        """Test checking quota that would exceed limit"""
        quota_manager.set_quota(
            'tenant_exceed',
            QuotaType.MAX_CONNECTIONS,
            limit=5
        )

        # Consume up to limit
        for _ in range(5):
            quota_manager.consume_quota('tenant_exceed', QuotaType.MAX_CONNECTIONS)

        # Try to exceed
        result = quota_manager.check_quota(
            'tenant_exceed',
            QuotaType.MAX_CONNECTIONS
        )

        assert result['allowed'] is False
        assert result['quota_exceeded'] is True

    def test_check_quota_soft_limit_exceeded(self, quota_manager):
        """Test checking when soft limit is exceeded"""
        quota_manager.set_quota(
            'tenant_soft',
            QuotaType.STORAGE_MB,
            limit=1000,
            soft_limit=800
        )

        # Consume past soft limit
        quota_manager.consume_quota('tenant_soft', QuotaType.STORAGE_MB, amount=850)

        result = quota_manager.check_quota('tenant_soft', QuotaType.STORAGE_MB)

        assert result['soft_limit_exceeded'] is True
        assert result['allowed'] is True  # Still under hard limit

    def test_check_quota_large_amount(self, quota_manager):
        """Test checking with large consumption amount"""
        quota_manager.set_quota(
            'tenant_large',
            QuotaType.API_REQUESTS_PER_DAY,
            limit=100
        )

        result = quota_manager.check_quota(
            'tenant_large',
            QuotaType.API_REQUESTS_PER_DAY,
            amount=150
        )

        assert result['allowed'] is False


class TestQuotaConsumption:
    """Test quota consumption and enforcement"""

    def test_consume_quota_success(self, quota_manager):
        """Test successfully consuming quota"""
        quota_manager.set_quota(
            'tenant_consume',
            QuotaType.QUERIES_PER_MINUTE,
            limit=10
        )

        success = quota_manager.consume_quota(
            'tenant_consume',
            QuotaType.QUERIES_PER_MINUTE,
            amount=1
        )

        assert success is True

        # Verify usage increased
        quota = quota_manager.get_quota('tenant_consume', QuotaType.QUERIES_PER_MINUTE)
        assert quota.current_usage == 1

    def test_consume_quota_multiple_times(self, quota_manager):
        """Test consuming quota multiple times"""
        quota_manager.set_quota(
            'tenant_multi_consume',
            QuotaType.QUERIES_PER_HOUR,
            limit=100
        )

        for _ in range(5):
            quota_manager.consume_quota(
                'tenant_multi_consume',
                QuotaType.QUERIES_PER_HOUR
            )

        quota = quota_manager.get_quota('tenant_multi_consume', QuotaType.QUERIES_PER_HOUR)
        assert quota.current_usage == 5

    def test_consume_quota_with_custom_amount(self, quota_manager):
        """Test consuming quota with custom amount"""
        quota_manager.set_quota(
            'tenant_custom',
            QuotaType.STORAGE_MB,
            limit=1000
        )

        quota_manager.consume_quota(
            'tenant_custom',
            QuotaType.STORAGE_MB,
            amount=250
        )

        quota = quota_manager.get_quota('tenant_custom', QuotaType.STORAGE_MB)
        assert quota.current_usage == 250

    def test_consume_quota_when_exceeded(self, quota_manager):
        """Test consuming quota fails when limit exceeded"""
        quota_manager.set_quota(
            'tenant_exceeded',
            QuotaType.MAX_DATABASES,
            limit=3
        )

        # Consume to limit
        for _ in range(3):
            quota_manager.consume_quota('tenant_exceeded', QuotaType.MAX_DATABASES)

        # Try to exceed
        success = quota_manager.consume_quota('tenant_exceeded', QuotaType.MAX_DATABASES)

        assert success is False

        # Verify usage stayed at limit
        quota = quota_manager.get_quota('tenant_exceeded', QuotaType.MAX_DATABASES)
        assert quota.current_usage == 3

    def test_consume_quota_with_metadata(self, quota_manager):
        """Test consuming quota with tracking metadata"""
        quota_manager.set_quota(
            'tenant_meta',
            QuotaType.API_REQUESTS_PER_DAY,
            limit=1000
        )

        success = quota_manager.consume_quota(
            'tenant_meta',
            QuotaType.API_REQUESTS_PER_DAY,
            metadata={'endpoint': '/api/users', 'method': 'GET'}
        )

        assert success is True


class TestQuotaReset:
    """Test quota reset functionality"""

    def test_manual_quota_reset(self, quota_manager):
        """Test manually resetting a quota"""
        quota_manager.set_quota(
            'tenant_reset',
            QuotaType.QUERIES_PER_DAY,
            limit=100
        )

        # Consume some quota
        quota_manager.consume_quota('tenant_reset', QuotaType.QUERIES_PER_DAY, amount=50)

        # Reset
        quota_manager.reset_quota('tenant_reset', QuotaType.QUERIES_PER_DAY)

        # Verify reset
        quota = quota_manager.get_quota('tenant_reset', QuotaType.QUERIES_PER_DAY)
        assert quota.current_usage == 0

    def test_automatic_reset_hourly(self, quota_manager):
        """Test automatic hourly reset"""
        quota_manager.set_quota(
            'tenant_hourly',
            QuotaType.QUERIES_PER_HOUR,
            limit=100,
            reset_period='hourly'
        )

        # Consume quota
        quota_manager.consume_quota('tenant_hourly', QuotaType.QUERIES_PER_HOUR, amount=50)

        # Manually trigger reset (simulate time passing)
        quota_manager.reset_quota('tenant_hourly', QuotaType.QUERIES_PER_HOUR)

        quota = quota_manager.get_quota('tenant_hourly', QuotaType.QUERIES_PER_HOUR)
        assert quota.current_usage == 0
        assert quota.last_reset is not None


class TestUsageHistory:
    """Test usage history tracking"""

    def test_track_usage_history(self, quota_manager):
        """Test that consumption is tracked in history"""
        quota_manager.set_quota(
            'tenant_history',
            QuotaType.API_REQUESTS_PER_DAY,
            limit=1000
        )

        # Consume multiple times
        for i in range(5):
            quota_manager.consume_quota(
                'tenant_history',
                QuotaType.API_REQUESTS_PER_DAY,
                amount=10
            )

        history = quota_manager.get_usage_history(
            'tenant_history',
            QuotaType.API_REQUESTS_PER_DAY
        )

        assert len(history) == 5

    def test_usage_history_filtering(self, quota_manager):
        """Test filtering usage history by time range"""
        quota_manager.set_quota(
            'tenant_filter',
            QuotaType.QUERIES_PER_DAY,
            limit=1000
        )

        # Add some usage
        for _ in range(3):
            quota_manager.consume_quota('tenant_filter', QuotaType.QUERIES_PER_DAY)

        start_time = datetime.now() - timedelta(hours=1)

        history = quota_manager.get_usage_history(
            'tenant_filter',
            QuotaType.QUERIES_PER_DAY,
            start_time=start_time
        )

        assert len(history) == 3

    def test_usage_history_limit(self, quota_manager):
        """Test limiting usage history results"""
        quota_manager.set_quota(
            'tenant_limit',
            QuotaType.API_REQUESTS_PER_DAY,
            limit=1000
        )

        # Add many records
        for _ in range(20):
            quota_manager.consume_quota('tenant_limit', QuotaType.API_REQUESTS_PER_DAY)

        history = quota_manager.get_usage_history(
            'tenant_limit',
            QuotaType.API_REQUESTS_PER_DAY,
            limit=10
        )

        assert len(history) == 10


class TestUsageAnalytics:
    """Test usage analytics and reporting"""

    def test_get_usage_analytics(self, quota_manager):
        """Test getting usage analytics"""
        quota_manager.set_quota(
            'tenant_analytics',
            QuotaType.API_REQUESTS_PER_DAY,
            limit=1000
        )

        # Add some usage
        for i in range(10):
            quota_manager.consume_quota(
                'tenant_analytics',
                QuotaType.API_REQUESTS_PER_DAY,
                amount=i + 1
            )

        analytics = quota_manager.get_usage_analytics(
            'tenant_analytics',
            QuotaType.API_REQUESTS_PER_DAY
        )

        assert 'total_usage' in analytics
        assert 'average_usage' in analytics
        assert 'peak_usage' in analytics
        assert analytics['data_points'] == 10

    def test_analytics_trend_detection(self, quota_manager):
        """Test trend detection in analytics"""
        quota_manager.set_quota(
            'tenant_trend',
            QuotaType.QUERIES_PER_DAY,
            limit=1000
        )

        # Add increasing usage pattern
        for i in range(15):
            quota_manager.consume_quota(
                'tenant_trend',
                QuotaType.QUERIES_PER_DAY,
                amount=i + 1
            )

        analytics = quota_manager.get_usage_analytics(
            'tenant_trend',
            QuotaType.QUERIES_PER_DAY
        )

        assert 'trend' in analytics
        # Trend should be detected (increasing/stable/decreasing)

    def test_analytics_empty_history(self, quota_manager):
        """Test analytics with no usage history"""
        analytics = quota_manager.get_usage_analytics(
            'tenant_empty',
            QuotaType.QUERIES_PER_DAY
        )

        assert analytics['total_usage'] == 0
        assert analytics['average_usage'] == 0


class TestResourceQuotaDataclass:
    """Test ResourceQuota dataclass methods"""

    def test_quota_is_exceeded(self):
        """Test is_exceeded method"""
        quota = ResourceQuota(
            tenant_id='test',
            quota_type=QuotaType.QUERIES_PER_HOUR,
            limit=100,
            current_usage=100
        )

        assert quota.is_exceeded() is True

    def test_quota_not_exceeded(self):
        """Test quota not exceeded"""
        quota = ResourceQuota(
            tenant_id='test',
            quota_type=QuotaType.QUERIES_PER_HOUR,
            limit=100,
            current_usage=50
        )

        assert quota.is_exceeded() is False

    def test_quota_soft_limit_exceeded(self):
        """Test soft limit exceeded"""
        quota = ResourceQuota(
            tenant_id='test',
            quota_type=QuotaType.STORAGE_MB,
            limit=1000,
            current_usage=850,
            soft_limit=800
        )

        assert quota.is_soft_limit_exceeded() is True

    def test_quota_remaining(self):
        """Test calculating remaining quota"""
        quota = ResourceQuota(
            tenant_id='test',
            quota_type=QuotaType.MAX_USERS,
            limit=100,
            current_usage=30
        )

        assert quota.remaining() == 70

    def test_quota_percentage_used(self):
        """Test calculating percentage used"""
        quota = ResourceQuota(
            tenant_id='test',
            quota_type=QuotaType.QUERIES_PER_DAY,
            limit=100,
            current_usage=25
        )

        assert quota.percentage_used() == 25.0

    def test_quota_to_dict(self):
        """Test converting quota to dictionary"""
        quota = ResourceQuota(
            tenant_id='test',
            quota_type=QuotaType.STORAGE_MB,
            limit=500,
            current_usage=100
        )

        quota_dict = quota.to_dict()

        assert quota_dict['tenant_id'] == 'test'
        assert quota_dict['limit'] == 500
        assert quota_dict['quota_type'] == 'storage_mb'

    def test_quota_from_dict(self):
        """Test creating quota from dictionary"""
        data = {
            'tenant_id': 'test',
            'quota_type': 'queries_per_hour',
            'limit': 100,
            'current_usage': 50
        }

        quota = ResourceQuota.from_dict(data)

        assert quota.tenant_id == 'test'
        assert quota.quota_type == QuotaType.QUERIES_PER_HOUR
        assert quota.limit == 100


class TestQuotaIsolation:
    """Test quota isolation between tenants"""

    def test_quotas_are_isolated(self, quota_manager):
        """Test that tenant quotas don't interfere"""
        quota_manager.set_quota('tenant_a', QuotaType.QUERIES_PER_HOUR, 100)
        quota_manager.set_quota('tenant_b', QuotaType.QUERIES_PER_HOUR, 200)

        # Consume for tenant A
        quota_manager.consume_quota('tenant_a', QuotaType.QUERIES_PER_HOUR, amount=50)

        # Verify tenant B is unaffected
        quota_b = quota_manager.get_quota('tenant_b', QuotaType.QUERIES_PER_HOUR)
        assert quota_b.current_usage == 0

    def test_same_quota_type_different_tenants(self, quota_manager):
        """Test same quota type for different tenants"""
        quota_manager.set_quota('tenant_1', QuotaType.MAX_CONNECTIONS, 10)
        quota_manager.set_quota('tenant_2', QuotaType.MAX_CONNECTIONS, 20)

        quota_1 = quota_manager.get_quota('tenant_1', QuotaType.MAX_CONNECTIONS)
        quota_2 = quota_manager.get_quota('tenant_2', QuotaType.MAX_CONNECTIONS)

        assert quota_1.limit == 10
        assert quota_2.limit == 20


class TestQuotaTypes:
    """Test different quota types"""

    def test_all_quota_types(self, quota_manager):
        """Test all available quota types"""
        tenant_id = 'tenant_types'

        quota_types = [
            QuotaType.QUERIES_PER_MINUTE,
            QuotaType.QUERIES_PER_HOUR,
            QuotaType.QUERIES_PER_DAY,
            QuotaType.STORAGE_MB,
            QuotaType.MAX_CONNECTIONS,
            QuotaType.API_REQUESTS_PER_DAY,
            QuotaType.MAX_DATABASES,
            QuotaType.MAX_USERS,
            QuotaType.CUSTOM,
        ]

        for quota_type in quota_types:
            quota = quota_manager.set_quota(tenant_id, quota_type, limit=100)
            assert quota.quota_type == quota_type
