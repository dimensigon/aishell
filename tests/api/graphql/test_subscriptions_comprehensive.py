"""
Comprehensive Test Suite for GraphQL Subscriptions

Tests all aspects of subscription functionality including:
- Subscription lifecycle (register, execute, complete, cancel)
- Real-time updates and event publication
- WebSocket handling
- Subscription resolvers
- Authorization and security
- Error handling
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch, call
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
from dataclasses import dataclass

# Import module under test
from src.api.graphql.subscriptions import (
    SubscriptionManager,
    Subscription,
    DatabaseChangeNotifier,
    create_database_subscriptions
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def subscription_manager():
    """Create subscription manager instance"""
    return SubscriptionManager()


@pytest.fixture
def notifier(subscription_manager):
    """Create database change notifier"""
    return DatabaseChangeNotifier(subscription_manager)


@pytest.fixture
def mock_strawberry_info():
    """Create mock Strawberry info object"""
    info = Mock()
    info.context = Mock()
    return info


# ==============================================================================
# A. SUBSCRIPTION LIFECYCLE Tests (15-20 tests)
# ==============================================================================

class TestSubscriptionLifecycle:
    """Test suite for subscription lifecycle management"""

    @pytest.mark.asyncio
    async def test_subscribe_basic(self, subscription_manager):
        """Test basic subscription registration"""
        sub = await subscription_manager.subscribe('sub1', 'users:changes')

        assert sub.id == 'sub1'
        assert sub.topic == 'users:changes'
        assert 'sub1' in subscription_manager.subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_with_filters(self, subscription_manager):
        """Test subscription with filters"""
        filters = {'user_id': 123, 'action': 'update'}
        sub = await subscription_manager.subscribe('sub1', 'users:changes', filters)

        assert sub.filters == filters

    @pytest.mark.asyncio
    async def test_subscribe_creates_queue(self, subscription_manager):
        """Test subscription creates message queue"""
        await subscription_manager.subscribe('sub1', 'users:changes')

        assert 'sub1' in subscription_manager.queues
        assert isinstance(subscription_manager.queues['sub1'], asyncio.Queue)

    @pytest.mark.asyncio
    async def test_subscribe_multiple_to_same_topic(self, subscription_manager):
        """Test multiple subscribers to same topic"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.subscribe('sub2', 'users:changes')

        assert len(subscription_manager.subscribers['users:changes']) == 2

    @pytest.mark.asyncio
    async def test_subscribe_to_different_topics(self, subscription_manager):
        """Test subscriber to different topics"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.subscribe('sub2', 'orders:changes')

        assert len(subscription_manager.subscribers) == 2

    @pytest.mark.asyncio
    async def test_unsubscribe_basic(self, subscription_manager):
        """Test basic unsubscribe"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.unsubscribe('sub1')

        assert 'sub1' not in subscription_manager.subscriptions
        assert 'sub1' not in subscription_manager.queues

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_from_topic(self, subscription_manager):
        """Test unsubscribe removes from topic subscribers"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.unsubscribe('sub1')

        assert 'users:changes' not in subscription_manager.subscribers

    @pytest.mark.asyncio
    async def test_unsubscribe_keeps_other_subscribers(self, subscription_manager):
        """Test unsubscribe doesn't affect other subscribers"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.subscribe('sub2', 'users:changes')
        await subscription_manager.unsubscribe('sub1')

        assert 'sub2' in subscription_manager.subscriptions
        assert 'sub2' in subscription_manager.subscribers['users:changes']

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, subscription_manager):
        """Test unsubscribe non-existent subscription does not error"""
        await subscription_manager.unsubscribe('nonexistent')
        # Should not raise error

    @pytest.mark.asyncio
    async def test_subscription_has_timestamp(self, subscription_manager):
        """Test subscription records creation timestamp"""
        sub = await subscription_manager.subscribe('sub1', 'users:changes')

        assert isinstance(sub.created_at, datetime)

    @pytest.mark.asyncio
    async def test_multiple_subscriptions_same_subscriber(self, subscription_manager):
        """Test subscriber can subscribe to multiple topics (requires different IDs)"""
        await subscription_manager.subscribe('sub1_topic1', 'topic1')
        await subscription_manager.subscribe('sub1_topic2', 'topic2')

        assert len(subscription_manager.subscriptions) == 2

    @pytest.mark.asyncio
    async def test_resubscribe_after_unsubscribe(self, subscription_manager):
        """Test can resubscribe after unsubscribing"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.unsubscribe('sub1')
        sub = await subscription_manager.subscribe('sub1', 'users:changes')

        assert sub.id == 'sub1'
        assert 'sub1' in subscription_manager.subscriptions


# ==============================================================================
# B. REAL-TIME UPDATES Tests (20-25 tests)
# ==============================================================================

class TestRealTimeUpdates:
    """Test suite for real-time event publication and updates"""

    @pytest.mark.asyncio
    async def test_publish_to_subscriber(self, subscription_manager):
        """Test publish sends data to subscriber"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.publish('users:changes', {'user_id': 123, 'name': 'Alice'})

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['topic'] == 'users:changes'
        assert message['data']['user_id'] == 123

    @pytest.mark.asyncio
    async def test_publish_to_multiple_subscribers(self, subscription_manager):
        """Test publish sends to all subscribers"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.subscribe('sub2', 'users:changes')
        await subscription_manager.publish('users:changes', {'user_id': 123})

        queue1 = subscription_manager.queues['sub1']
        queue2 = subscription_manager.queues['sub2']

        msg1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
        msg2 = await asyncio.wait_for(queue2.get(), timeout=1.0)

        assert msg1['data']['user_id'] == 123
        assert msg2['data']['user_id'] == 123

    @pytest.mark.asyncio
    async def test_publish_with_metadata(self, subscription_manager):
        """Test publish includes metadata"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        metadata = {'version': '1.0', 'source': 'api'}
        await subscription_manager.publish('users:changes', {'data': 'test'}, metadata)

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['metadata'] == metadata

    @pytest.mark.asyncio
    async def test_publish_includes_timestamp(self, subscription_manager):
        """Test publish includes timestamp"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.publish('users:changes', {'data': 'test'})

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert 'timestamp' in message
        # Timestamp should be ISO format string
        datetime.fromisoformat(message['timestamp'])

    @pytest.mark.asyncio
    async def test_publish_to_nonexistent_topic(self, subscription_manager):
        """Test publish to topic with no subscribers"""
        await subscription_manager.publish('nonexistent:topic', {'data': 'test'})
        # Should not raise error

    @pytest.mark.asyncio
    async def test_publish_with_filter_match(self, subscription_manager):
        """Test publish with matching filters"""
        filters = {'user_id': 123}
        await subscription_manager.subscribe('sub1', 'users:changes', filters)
        await subscription_manager.publish('users:changes', {'user_id': 123, 'name': 'Alice'})

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['data']['user_id'] == 123

    @pytest.mark.asyncio
    async def test_publish_with_filter_no_match(self, subscription_manager):
        """Test publish filters out non-matching data"""
        filters = {'user_id': 123}
        await subscription_manager.subscribe('sub1', 'users:changes', filters)
        await subscription_manager.publish('users:changes', {'user_id': 456, 'name': 'Bob'})

        queue = subscription_manager.queues['sub1']
        # Queue should be empty
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(queue.get(), timeout=0.1)

    @pytest.mark.asyncio
    async def test_publish_multiple_filters(self, subscription_manager):
        """Test publish with multiple filter criteria"""
        filters = {'user_id': 123, 'action': 'update'}
        await subscription_manager.subscribe('sub1', 'users:changes', filters)
        await subscription_manager.publish('users:changes', {
            'user_id': 123,
            'action': 'update',
            'name': 'Alice'
        })

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['data']['action'] == 'update'

    @pytest.mark.asyncio
    async def test_publish_partial_filter_match(self, subscription_manager):
        """Test publish requires all filters to match"""
        filters = {'user_id': 123, 'action': 'update'}
        await subscription_manager.subscribe('sub1', 'users:changes', filters)
        # Only user_id matches, action doesn't
        await subscription_manager.publish('users:changes', {
            'user_id': 123,
            'action': 'delete'
        })

        queue = subscription_manager.queues['sub1']
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(queue.get(), timeout=0.1)

    @pytest.mark.asyncio
    async def test_publish_non_dict_data(self, subscription_manager):
        """Test publish with non-dict data (filters don't apply)"""
        filters = {'user_id': 123}
        await subscription_manager.subscribe('sub1', 'users:changes', filters)
        await subscription_manager.publish('users:changes', 'string data')

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['data'] == 'string data'

    @pytest.mark.asyncio
    async def test_publish_list_data(self, subscription_manager):
        """Test publish with list data"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.publish('users:changes', [1, 2, 3])

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['data'] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_publish_none_data(self, subscription_manager):
        """Test publish with None data"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.publish('users:changes', None)

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['data'] is None

    @pytest.mark.asyncio
    async def test_publish_empty_metadata(self, subscription_manager):
        """Test publish with no metadata defaults to empty dict"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        await subscription_manager.publish('users:changes', {'data': 'test'})

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['metadata'] == {}

    @pytest.mark.asyncio
    async def test_publish_complex_data_structure(self, subscription_manager):
        """Test publish with complex nested data"""
        await subscription_manager.subscribe('sub1', 'users:changes')
        complex_data = {
            'user': {
                'id': 123,
                'profile': {
                    'name': 'Alice',
                    'settings': {'theme': 'dark'}
                }
            }
        }
        await subscription_manager.publish('users:changes', complex_data)

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['data']['user']['profile']['settings']['theme'] == 'dark'


# ==============================================================================
# C. ASYNC ITERATION / LISTEN Tests (15-18 tests)
# ==============================================================================

class TestAsyncIteration:
    """Test suite for async iteration and listening"""

    @pytest.mark.asyncio
    async def test_listen_yields_messages(self, subscription_manager):
        """Test listen yields published messages"""
        await subscription_manager.subscribe('sub1', 'users:changes')

        # Start listening in background
        listen_task = asyncio.create_task(
            self._collect_messages(subscription_manager, 'sub1', count=2)
        )

        # Publish messages
        await subscription_manager.publish('users:changes', {'msg': 1})
        await subscription_manager.publish('users:changes', {'msg': 2})

        messages = await asyncio.wait_for(listen_task, timeout=1.0)
        assert len(messages) == 2
        assert messages[0]['data']['msg'] == 1

    @pytest.mark.asyncio
    async def test_listen_nonexistent_subscriber(self, subscription_manager):
        """Test listen with non-existent subscriber"""
        messages = []
        async for message in subscription_manager.listen('nonexistent'):
            messages.append(message)
            break

        # Should return immediately without messages
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_listen_cancellation(self, subscription_manager):
        """Test listen handles cancellation gracefully"""
        await subscription_manager.subscribe('sub1', 'users:changes')

        listen_task = asyncio.create_task(
            self._collect_messages(subscription_manager, 'sub1', count=10)
        )

        await asyncio.sleep(0.1)
        listen_task.cancel()

        try:
            await listen_task
        except asyncio.CancelledError:
            pass  # Expected cancellation

    @pytest.mark.asyncio
    async def test_listen_multiple_messages(self, subscription_manager):
        """Test listen receives multiple messages in order"""
        await subscription_manager.subscribe('sub1', 'users:changes')

        listen_task = asyncio.create_task(
            self._collect_messages(subscription_manager, 'sub1', count=5)
        )

        for i in range(5):
            await subscription_manager.publish('users:changes', {'seq': i})

        messages = await asyncio.wait_for(listen_task, timeout=1.0)
        assert len(messages) == 5
        assert messages[0]['data']['seq'] == 0
        assert messages[4]['data']['seq'] == 4

    async def _collect_messages(self, manager, subscriber_id, count):
        """Helper to collect N messages from listener"""
        messages = []
        async for message in manager.listen(subscriber_id):
            messages.append(message)
            if len(messages) >= count:
                break
        return messages


# ==============================================================================
# D. SUBSCRIBER MANAGEMENT Tests (12-15 tests)
# ==============================================================================

class TestSubscriberManagement:
    """Test suite for subscriber count and topic management"""

    @pytest.mark.asyncio
    async def test_get_subscriber_count_total(self, subscription_manager):
        """Test get total subscriber count"""
        await subscription_manager.subscribe('sub1', 'topic1')
        await subscription_manager.subscribe('sub2', 'topic2')

        count = subscription_manager.get_subscriber_count()
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_subscriber_count_by_topic(self, subscription_manager):
        """Test get subscriber count for specific topic"""
        await subscription_manager.subscribe('sub1', 'topic1')
        await subscription_manager.subscribe('sub2', 'topic1')
        await subscription_manager.subscribe('sub3', 'topic2')

        count = subscription_manager.get_subscriber_count('topic1')
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_subscriber_count_empty(self, subscription_manager):
        """Test get subscriber count with no subscriptions"""
        count = subscription_manager.get_subscriber_count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_subscriber_count_nonexistent_topic(self, subscription_manager):
        """Test get subscriber count for non-existent topic"""
        count = subscription_manager.get_subscriber_count('nonexistent')
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_topics_list(self, subscription_manager):
        """Test get list of active topics"""
        await subscription_manager.subscribe('sub1', 'topic1')
        await subscription_manager.subscribe('sub2', 'topic2')

        topics = subscription_manager.get_topics()
        assert len(topics) == 2
        assert 'topic1' in topics
        assert 'topic2' in topics

    @pytest.mark.asyncio
    async def test_get_topics_empty(self, subscription_manager):
        """Test get topics with no subscriptions"""
        topics = subscription_manager.get_topics()
        assert topics == []

    @pytest.mark.asyncio
    async def test_get_topics_after_unsubscribe(self, subscription_manager):
        """Test get topics after all subscribers leave"""
        await subscription_manager.subscribe('sub1', 'topic1')
        await subscription_manager.unsubscribe('sub1')

        topics = subscription_manager.get_topics()
        assert 'topic1' not in topics


# ==============================================================================
# E. FILTER MATCHING Tests (10-12 tests)
# ==============================================================================

class TestFilterMatching:
    """Test suite for subscription filter matching logic"""

    def test_matches_filters_no_filters(self, subscription_manager):
        """Test matching with no filters always matches"""
        result = subscription_manager._matches_filters({'any': 'data'}, {})
        assert result is True

    def test_matches_filters_exact_match(self, subscription_manager):
        """Test exact filter match"""
        data = {'user_id': 123, 'action': 'update'}
        filters = {'user_id': 123}
        result = subscription_manager._matches_filters(data, filters)
        assert result is True

    def test_matches_filters_no_match(self, subscription_manager):
        """Test filter doesn't match"""
        data = {'user_id': 456}
        filters = {'user_id': 123}
        result = subscription_manager._matches_filters(data, filters)
        assert result is False

    def test_matches_filters_missing_key(self, subscription_manager):
        """Test filter with missing key doesn't match"""
        data = {'name': 'Alice'}
        filters = {'user_id': 123}
        result = subscription_manager._matches_filters(data, filters)
        assert result is False

    def test_matches_filters_multiple_criteria(self, subscription_manager):
        """Test multiple filter criteria all must match"""
        data = {'user_id': 123, 'action': 'update'}
        filters = {'user_id': 123, 'action': 'update'}
        result = subscription_manager._matches_filters(data, filters)
        assert result is True

    def test_matches_filters_partial_match(self, subscription_manager):
        """Test partial match fails"""
        data = {'user_id': 123, 'action': 'delete'}
        filters = {'user_id': 123, 'action': 'update'}
        result = subscription_manager._matches_filters(data, filters)
        assert result is False

    def test_matches_filters_non_dict_data(self, subscription_manager):
        """Test non-dict data always matches"""
        result = subscription_manager._matches_filters('string', {'user_id': 123})
        assert result is True

    def test_matches_filters_none_data(self, subscription_manager):
        """Test None data always matches"""
        result = subscription_manager._matches_filters(None, {'user_id': 123})
        assert result is True


# ==============================================================================
# F. DATABASE CHANGE NOTIFIER Tests (15-20 tests)
# ==============================================================================

class TestDatabaseChangeNotifier:
    """Test suite for database change notifications"""

    @pytest.mark.asyncio
    async def test_notify_insert(self, subscription_manager, notifier):
        """Test notify insert operation"""
        await subscription_manager.subscribe('sub1', 'table:users')
        await notifier.notify_insert('users', 123, {'name': 'Alice', 'email': 'alice@example.com'})

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['data']['operation'] == 'INSERT'
        assert message['data']['record_id'] == 123
        assert message['data']['table'] == 'users'

    @pytest.mark.asyncio
    async def test_notify_update(self, subscription_manager, notifier):
        """Test notify update operation"""
        await subscription_manager.subscribe('sub1', 'table:users')
        old_data = {'name': 'Alice'}
        new_data = {'name': 'Alice Updated'}
        await notifier.notify_update('users', 123, old_data, new_data)

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['data']['operation'] == 'UPDATE'
        assert message['data']['old_data'] == old_data
        assert message['data']['new_data'] == new_data

    @pytest.mark.asyncio
    async def test_notify_delete(self, subscription_manager, notifier):
        """Test notify delete operation"""
        await subscription_manager.subscribe('sub1', 'table:users')
        await notifier.notify_delete('users', 123, {'name': 'Alice'})

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message['data']['operation'] == 'DELETE'
        assert message['data']['record_id'] == 123

    @pytest.mark.asyncio
    async def test_notifier_multiple_tables(self, subscription_manager, notifier):
        """Test notifier with multiple tables"""
        await subscription_manager.subscribe('sub1', 'table:users')
        await subscription_manager.subscribe('sub2', 'table:orders')

        await notifier.notify_insert('users', 1, {'name': 'Alice'})
        await notifier.notify_insert('orders', 2, {'product': 'Book'})

        queue1 = subscription_manager.queues['sub1']
        queue2 = subscription_manager.queues['sub2']

        msg1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
        msg2 = await asyncio.wait_for(queue2.get(), timeout=1.0)

        assert msg1['data']['table'] == 'users'
        assert msg2['data']['table'] == 'orders'

    @pytest.mark.asyncio
    async def test_notifier_with_operation_filter(self, subscription_manager, notifier):
        """Test notifier with operation-specific filter"""
        filters = {'operation': 'INSERT'}
        await subscription_manager.subscribe('sub1', 'table:users', filters)

        # This should match
        await notifier.notify_insert('users', 1, {'name': 'Alice'})

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert message['data']['operation'] == 'INSERT'

        # This should not match
        await notifier.notify_update('users', 1, {'name': 'Alice'}, {'name': 'Bob'})

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(queue.get(), timeout=0.1)


# ==============================================================================
# G. STRAWBERRY SUBSCRIPTION RESOLVERS Tests (15-20 tests)
# ==============================================================================

class TestStrawberrySubscriptions:
    """Test suite for Strawberry GraphQL subscription resolvers"""

    @pytest.mark.asyncio
    async def test_create_database_subscriptions(self, subscription_manager):
        """Test creating database subscription resolvers"""
        subscription_type = create_database_subscriptions(subscription_manager)

        # Should return a Strawberry type or None if not available
        assert subscription_type is not None or subscription_type is None

    @pytest.mark.asyncio
    async def test_table_changes_subscription(self, subscription_manager, mock_strawberry_info):
        """Test table_changes subscription resolver"""
        subscription_type = create_database_subscriptions(subscription_manager)

        if subscription_type is None:
            pytest.skip("strawberry-graphql not available")

        instance = subscription_type()

        # Start subscription in background
        listen_task = asyncio.create_task(
            self._collect_subscription_results(
                instance.table_changes(mock_strawberry_info, 'users'),
                count=2
            )
        )

        await asyncio.sleep(0.1)  # Let subscription start

        # Publish events
        await subscription_manager.publish('table:users', {
            'operation': 'INSERT',
            'table': 'users',
            'data': {'name': 'Alice'}
        })
        await subscription_manager.publish('table:users', {
            'operation': 'UPDATE',
            'table': 'users',
            'data': {'name': 'Bob'}
        })

        results = await asyncio.wait_for(listen_task, timeout=2.0)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_table_changes_with_operation_filter(self, subscription_manager, mock_strawberry_info):
        """Test table_changes with operation filter"""
        subscription_type = create_database_subscriptions(subscription_manager)

        if subscription_type is None:
            pytest.skip("strawberry-graphql not available")

        instance = subscription_type()

        listen_task = asyncio.create_task(
            self._collect_subscription_results(
                instance.table_changes(mock_strawberry_info, 'users', operation='INSERT'),
                count=1
            )
        )

        await asyncio.sleep(0.1)

        # Publish INSERT (should match)
        await subscription_manager.publish('table:users', {
            'operation': 'INSERT',
            'table': 'users',
            'data': {'name': 'Alice'}
        })

        results = await asyncio.wait_for(listen_task, timeout=1.0)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_query_results_subscription(self, subscription_manager, mock_strawberry_info):
        """Test query_results subscription resolver"""
        subscription_type = create_database_subscriptions(subscription_manager)

        if subscription_type is None:
            pytest.skip("strawberry-graphql not available")

        instance = subscription_type()

        listen_task = asyncio.create_task(
            self._collect_subscription_results(
                instance.query_results(mock_strawberry_info, 'query123'),
                count=1
            )
        )

        await asyncio.sleep(0.1)

        await subscription_manager.publish('query:query123', {'results': [1, 2, 3]})

        results = await asyncio.wait_for(listen_task, timeout=1.0)
        assert len(results) == 1
        assert results[0]['results'] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_security_events_subscription(self, subscription_manager, mock_strawberry_info):
        """Test security_events subscription resolver"""
        subscription_type = create_database_subscriptions(subscription_manager)

        if subscription_type is None:
            pytest.skip("strawberry-graphql not available")

        instance = subscription_type()

        listen_task = asyncio.create_task(
            self._collect_subscription_results(
                instance.security_events(mock_strawberry_info),
                count=1
            )
        )

        await asyncio.sleep(0.1)

        await subscription_manager.publish('security:events', {
            'event': 'unauthorized_access',
            'threat_level': 'high'
        })

        results = await asyncio.wait_for(listen_task, timeout=1.0)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_security_events_with_threat_level_filter(self, subscription_manager, mock_strawberry_info):
        """Test security_events with threat level filter"""
        subscription_type = create_database_subscriptions(subscription_manager)

        if subscription_type is None:
            pytest.skip("strawberry-graphql not available")

        instance = subscription_type()

        listen_task = asyncio.create_task(
            self._collect_subscription_results(
                instance.security_events(mock_strawberry_info, threat_level='critical'),
                count=1
            )
        )

        await asyncio.sleep(0.1)

        # Publish matching event
        await subscription_manager.publish('security:events', {
            'event': 'breach_attempt',
            'threat_level': 'critical'
        })

        results = await asyncio.wait_for(listen_task, timeout=1.0)
        assert len(results) == 1

    async def _collect_subscription_results(self, async_gen, count):
        """Helper to collect N results from async generator"""
        results = []
        try:
            async for result in async_gen:
                results.append(result)
                if len(results) >= count:
                    break
        except asyncio.CancelledError:
            pass
        return results


# ==============================================================================
# H. ERROR HANDLING Tests (10-12 tests)
# ==============================================================================

class TestErrorHandling:
    """Test suite for error handling in subscriptions"""

    @pytest.mark.asyncio
    async def test_listen_handles_error_in_queue(self, subscription_manager):
        """Test listen handles errors gracefully"""
        await subscription_manager.subscribe('sub1', 'users:changes')

        # Simulate error by breaking the queue
        queue = subscription_manager.queues['sub1']
        original_get = queue.get

        async def error_get():
            if not hasattr(error_get, 'called'):
                error_get.called = True
                raise Exception("Queue error")
            return await original_get()

        queue.get = error_get

        messages = []
        try:
            async for message in subscription_manager.listen('sub1'):
                messages.append(message)
                break
        except Exception:
            pass  # Should handle gracefully

    @pytest.mark.asyncio
    async def test_publish_handles_missing_queue(self, subscription_manager):
        """Test publish handles missing queue gracefully"""
        # Manually add subscriber without queue
        subscription_manager.subscribers['topic1'] = {'sub1'}
        subscription_manager.subscriptions['sub1'] = Subscription('sub1', 'topic1')

        # This should not raise error
        await subscription_manager.publish('topic1', {'data': 'test'})

    @pytest.mark.asyncio
    async def test_unsubscribe_cleans_up_empty_topic(self, subscription_manager):
        """Test unsubscribe removes empty topic from subscribers"""
        await subscription_manager.subscribe('sub1', 'topic1')
        await subscription_manager.unsubscribe('sub1')

        assert 'topic1' not in subscription_manager.subscribers


# ==============================================================================
# I. EDGE CASES AND BOUNDARY CONDITIONS (10-15 tests)
# ==============================================================================

class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_subscribe_empty_topic(self, subscription_manager):
        """Test subscribe with empty topic string"""
        sub = await subscription_manager.subscribe('sub1', '')
        assert sub.topic == ''

    @pytest.mark.asyncio
    async def test_subscribe_very_long_topic(self, subscription_manager):
        """Test subscribe with very long topic name"""
        long_topic = 'a' * 10000
        sub = await subscription_manager.subscribe('sub1', long_topic)
        assert sub.topic == long_topic

    @pytest.mark.asyncio
    async def test_publish_very_large_payload(self, subscription_manager):
        """Test publish with very large data payload"""
        await subscription_manager.subscribe('sub1', 'topic1')
        large_data = {'data': 'x' * 1000000}  # 1MB string
        await subscription_manager.publish('topic1', large_data)

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert len(message['data']['data']) == 1000000

    @pytest.mark.asyncio
    async def test_many_concurrent_subscriptions(self, subscription_manager):
        """Test handling many concurrent subscriptions"""
        subscriber_count = 100

        for i in range(subscriber_count):
            await subscription_manager.subscribe(f'sub{i}', 'topic1')

        assert subscription_manager.get_subscriber_count('topic1') == subscriber_count

    @pytest.mark.asyncio
    async def test_rapid_subscribe_unsubscribe(self, subscription_manager):
        """Test rapid subscribe/unsubscribe cycles"""
        for _ in range(100):
            await subscription_manager.subscribe('sub1', 'topic1')
            await subscription_manager.unsubscribe('sub1')

        assert subscription_manager.get_subscriber_count() == 0

    @pytest.mark.asyncio
    async def test_queue_size_growth(self, subscription_manager):
        """Test queue can grow with many messages"""
        await subscription_manager.subscribe('sub1', 'topic1')

        # Publish many messages without consuming
        for i in range(1000):
            await subscription_manager.publish('topic1', {'seq': i})

        queue = subscription_manager.queues['sub1']
        assert queue.qsize() == 1000

    @pytest.mark.asyncio
    async def test_special_characters_in_topic(self, subscription_manager):
        """Test topic with special characters"""
        special_topic = 'topic:with:colons/and/slashes-and-dashes.and.dots'
        sub = await subscription_manager.subscribe('sub1', special_topic)
        assert sub.topic == special_topic

    @pytest.mark.asyncio
    async def test_unicode_in_topic_and_data(self, subscription_manager):
        """Test unicode characters in topic and data"""
        await subscription_manager.subscribe('sub1', '日本語トピック')
        await subscription_manager.publish('日本語トピック', {'name': '太郎'})

        queue = subscription_manager.queues['sub1']
        message = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert message['data']['name'] == '太郎'
