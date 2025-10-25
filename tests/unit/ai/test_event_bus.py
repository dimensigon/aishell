"""
Comprehensive tests for AsyncEventBus

Tests event publishing, subscription, priority handling, backpressure,
and async event processing.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock
from src.core.event_bus import (
    AsyncEventBus,
    Event,
    EventPriority
)


@pytest.fixture
async def event_bus():
    """Create event bus fixture."""
    bus = AsyncEventBus(max_queue_size=10)
    await bus.start()
    yield bus
    await bus.stop()


@pytest.fixture
def mock_handler():
    """Create mock async handler."""
    return AsyncMock()


class TestEvent:
    """Test Event class."""

    def test_event_creation(self):
        """Test event creation with defaults."""
        event = Event("test_event", {"key": "value"})

        assert event.type == "test_event"
        assert event.data == {"key": "value"}
        assert event.priority == EventPriority.NORMAL
        assert event.critical is False
        assert event.timestamp > 0

    def test_event_with_priority(self):
        """Test event creation with priority."""
        event = Event(
            "high_priority",
            {"urgent": True},
            priority=EventPriority.HIGH,
            critical=True
        )

        assert event.priority == EventPriority.HIGH
        assert event.critical is True

    def test_event_ordering(self):
        """Test event ordering by priority and timestamp."""
        event1 = Event("event1", priority=EventPriority.HIGH)
        import time
        time.sleep(0.01)  # Ensure different timestamp
        event2 = Event("event2", priority=EventPriority.LOW)

        # Higher priority (lower number) comes first
        assert event1 < event2


class TestEventBusBasics:
    """Test basic event bus operations."""

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping event bus."""
        bus = AsyncEventBus()

        assert not bus.processing

        await bus.start()
        assert bus.processing
        assert bus.processor_task is not None

        await bus.stop()
        assert not bus.processing

    @pytest.mark.asyncio
    async def test_double_start(self, event_bus):
        """Test starting already running bus."""
        # Already started in fixture
        await event_bus.start()  # Should not raise error
        assert event_bus.processing

    @pytest.mark.asyncio
    async def test_stop_non_running_bus(self):
        """Test stopping non-running bus."""
        bus = AsyncEventBus()
        await bus.stop()  # Should not raise error


class TestSubscription:
    """Test event subscription."""

    @pytest.mark.asyncio
    async def test_subscribe(self, event_bus, mock_handler):
        """Test subscribing to event type."""
        event_bus.subscribe("test_event", mock_handler)

        assert event_bus.get_subscriber_count("test_event") == 1

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_bus):
        """Test multiple subscribers for same event."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        handler3 = AsyncMock()

        event_bus.subscribe("test_event", handler1)
        event_bus.subscribe("test_event", handler2)
        event_bus.subscribe("test_event", handler3)

        assert event_bus.get_subscriber_count("test_event") == 3

    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus, mock_handler):
        """Test unsubscribing from event type."""
        event_bus.subscribe("test_event", mock_handler)
        assert event_bus.get_subscriber_count("test_event") == 1

        event_bus.unsubscribe("test_event", mock_handler)
        assert event_bus.get_subscriber_count("test_event") == 0

    @pytest.mark.asyncio
    async def test_unsubscribe_non_existent(self, event_bus, mock_handler):
        """Test unsubscribing non-existent handler."""
        event_bus.unsubscribe("test_event", mock_handler)  # Should not raise


class TestEventPublishing:
    """Test event publishing."""

    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus, mock_handler):
        """Test publishing event."""
        event_bus.subscribe("test_event", mock_handler)

        event = Event("test_event", {"data": "value"})
        await event_bus.publish(event)

        # Wait for processing
        await asyncio.sleep(0.1)

        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[0][0]
        assert call_args.type == "test_event"
        assert call_args.data == {"data": "value"}

    @pytest.mark.asyncio
    async def test_publish_multiple_events(self, event_bus, mock_handler):
        """Test publishing multiple events."""
        event_bus.subscribe("test_event", mock_handler)

        for i in range(5):
            event = Event("test_event", {"index": i})
            await event_bus.publish(event)

        await asyncio.sleep(0.2)

        assert mock_handler.call_count == 5

    @pytest.mark.asyncio
    async def test_publish_to_multiple_subscribers(self, event_bus):
        """Test event delivered to all subscribers."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        handler3 = AsyncMock()

        event_bus.subscribe("test_event", handler1)
        event_bus.subscribe("test_event", handler2)
        event_bus.subscribe("test_event", handler3)

        event = Event("test_event", {"data": "broadcast"})
        await event_bus.publish(event)

        await asyncio.sleep(0.1)

        handler1.assert_called_once()
        handler2.assert_called_once()
        handler3.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_no_subscribers(self, event_bus):
        """Test publishing event with no subscribers."""
        event = Event("test_event", {"data": "orphan"})
        await event_bus.publish(event)

        await asyncio.sleep(0.1)

        # Should not raise error
        stats = event_bus.get_stats()
        assert stats['events_published'] == 1


class TestEventPriority:
    """Test event priority handling."""

    @pytest.mark.asyncio
    async def test_priority_ordering(self, event_bus):
        """Test events processed by priority."""
        call_order = []

        async def handler(event):
            call_order.append(event.data['priority'])

        event_bus.subscribe("test_event", handler)

        # Publish in random order
        await event_bus.publish(Event("test_event", {"priority": "low"}, priority=EventPriority.LOW))
        await event_bus.publish(Event("test_event", {"priority": "critical"}, priority=EventPriority.CRITICAL))
        await event_bus.publish(Event("test_event", {"priority": "normal"}, priority=EventPriority.NORMAL))
        await event_bus.publish(Event("test_event", {"priority": "high"}, priority=EventPriority.HIGH))

        await asyncio.sleep(0.3)

        # Should be processed by priority: critical, high, normal, low
        assert call_order == ["critical", "high", "normal", "low"]

    @pytest.mark.asyncio
    async def test_critical_event(self, event_bus, mock_handler):
        """Test critical event handling."""
        event_bus.subscribe("critical_event", mock_handler)

        event = Event("critical_event", {"critical": True}, critical=True)
        await event_bus.publish(event)

        await asyncio.sleep(0.1)

        mock_handler.assert_called_once()


class TestBackpressure:
    """Test backpressure handling."""

    @pytest.mark.asyncio
    async def test_queue_full_non_critical(self):
        """Test queue full with non-critical event."""
        bus = AsyncEventBus(max_queue_size=2)
        await bus.start()

        try:
            # Fill queue
            await bus.publish(Event("test", {"id": 1}))
            await bus.publish(Event("test", {"id": 2}))

            # Should raise QueueFull
            with pytest.raises(asyncio.QueueFull):
                await bus.publish(Event("test", {"id": 3}))

            stats = bus.get_stats()
            assert stats['events_dropped'] == 1

        finally:
            await bus.stop()

    @pytest.mark.asyncio
    async def test_queue_full_critical_event(self):
        """Test critical event bypasses queue limit."""
        bus = AsyncEventBus(max_queue_size=2)
        await bus.start()

        try:
            # Fill queue
            await bus.publish(Event("test", {"id": 1}))
            await bus.publish(Event("test", {"id": 2}))

            # Critical event should still be added
            await bus.publish(Event("test", {"id": 3}, critical=True))

            stats = bus.get_stats()
            assert stats['events_published'] == 3
            assert stats['events_dropped'] == 0

        finally:
            await bus.stop()


class TestAsyncHandling:
    """Test async event handling."""

    @pytest.mark.asyncio
    async def test_slow_handler(self, event_bus):
        """Test slow async handler."""
        processed = []

        async def slow_handler(event):
            await asyncio.sleep(0.1)
            processed.append(event.data['id'])

        event_bus.subscribe("test_event", slow_handler)

        await event_bus.publish(Event("test_event", {"id": 1}))
        await event_bus.publish(Event("test_event", {"id": 2}))

        await asyncio.sleep(0.3)

        assert len(processed) == 2
        assert processed == [1, 2]

    @pytest.mark.asyncio
    async def test_handler_exception(self, event_bus):
        """Test handler that raises exception."""
        async def failing_handler(event):
            raise ValueError("Handler error")

        successful_handler = AsyncMock()

        event_bus.subscribe("test_event", failing_handler)
        event_bus.subscribe("test_event", successful_handler)

        await event_bus.publish(Event("test_event", {"data": "test"}))

        await asyncio.sleep(0.1)

        # Other handlers should still be called
        successful_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_handlers(self, event_bus):
        """Test concurrent handler execution."""
        call_times = []

        async def handler(event):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.05)

        # Add multiple handlers
        for _ in range(3):
            event_bus.subscribe("test_event", handler)

        start_time = asyncio.get_event_loop().time()
        await event_bus.publish(Event("test_event", {"data": "test"}))

        await asyncio.sleep(0.2)

        # All handlers should be called
        assert len(call_times) == 3

        # Should execute concurrently (within short time window)
        time_spread = max(call_times) - min(call_times)
        assert time_spread < 0.1  # Called nearly simultaneously


class TestStatistics:
    """Test event bus statistics."""

    @pytest.mark.asyncio
    async def test_stats_published(self, event_bus):
        """Test published event statistics."""
        initial_stats = event_bus.get_stats()

        for i in range(5):
            await event_bus.publish(Event("test", {"id": i}))

        stats = event_bus.get_stats()
        assert stats['events_published'] == initial_stats['events_published'] + 5

    @pytest.mark.asyncio
    async def test_stats_processed(self, event_bus, mock_handler):
        """Test processed event statistics."""
        event_bus.subscribe("test_event", mock_handler)

        for i in range(3):
            await event_bus.publish(Event("test_event", {"id": i}))

        await asyncio.sleep(0.2)

        stats = event_bus.get_stats()
        assert stats['events_processed'] >= 3

    @pytest.mark.asyncio
    async def test_stats_dropped(self):
        """Test dropped event statistics."""
        bus = AsyncEventBus(max_queue_size=1)
        await bus.start()

        try:
            await bus.publish(Event("test", {"id": 1}))

            # Should be dropped
            with pytest.raises(asyncio.QueueFull):
                await bus.publish(Event("test", {"id": 2}))

            stats = bus.get_stats()
            assert stats['events_dropped'] == 1

        finally:
            await bus.stop()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_event_data(self, event_bus, mock_handler):
        """Test event with empty data."""
        event_bus.subscribe("test_event", mock_handler)

        event = Event("test_event")
        await event_bus.publish(event)

        await asyncio.sleep(0.1)

        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[0][0]
        assert call_args.data == {}

    @pytest.mark.asyncio
    async def test_subscriber_count_non_existent(self, event_bus):
        """Test subscriber count for non-existent event."""
        count = event_bus.get_subscriber_count("non_existent")
        assert count == 0

    @pytest.mark.asyncio
    async def test_publish_after_stop(self):
        """Test publishing after bus stopped."""
        bus = AsyncEventBus()
        await bus.start()
        await bus.stop()

        # Should still queue event (processing loop stopped)
        await bus.publish(Event("test", {"data": "value"}))

    @pytest.mark.asyncio
    async def test_rapid_fire_events(self, event_bus):
        """Test publishing many events rapidly."""
        handler = AsyncMock()
        event_bus.subscribe("test_event", handler)

        # Publish 100 events rapidly
        for i in range(100):
            await event_bus.publish(Event("test_event", {"id": i}))

        # Wait for processing
        await asyncio.sleep(1.0)

        # Most should be processed (some might be dropped due to queue limit)
        assert handler.call_count >= 10  # At least some processed


class TestCriticalEventGuarantees:
    """Test critical event guarantees."""

    @pytest.mark.asyncio
    async def test_critical_event_waits_for_handlers(self, event_bus):
        """Test critical event waits for all handlers."""
        completed = []

        async def handler(event):
            await asyncio.sleep(0.1)
            completed.append(event.data['id'])

        event_bus.subscribe("critical_event", handler)

        event = Event("critical_event", {"id": 1}, critical=True)
        await event_bus.publish(event)

        # Give processing time
        await asyncio.sleep(0.2)

        assert 1 in completed

    @pytest.mark.asyncio
    async def test_non_critical_fire_and_forget(self, event_bus):
        """Test non-critical events are fire and forget."""
        async def handler(event):
            await asyncio.sleep(0.5)  # Long operation

        event_bus.subscribe("test_event", handler)

        event = Event("test_event", {"data": "test"}, critical=False)
        await event_bus.publish(event)

        # Should return immediately without waiting
        await asyncio.sleep(0.1)  # Short wait

        # Event is queued but handler still running
        stats = event_bus.get_stats()
        assert stats['events_published'] >= 1
