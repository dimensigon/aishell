"""
Comprehensive tests for src/core/event_bus.py to achieve 90%+ coverage.

Tests event publishing, subscription, priority queue, backpressure,
event processing, statistics, and all edge cases.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.core.event_bus import AsyncEventBus, Event, EventPriority


class TestEventClass:
    """Test Event class"""

    def test_event_creation_defaults(self):
        """Test creating event with defaults"""
        event = Event("test.event")

        assert event.type == "test.event"
        assert event.data == {}
        assert event.priority == EventPriority.NORMAL
        assert not event.critical
        assert event.timestamp > 0

    def test_event_creation_with_data(self):
        """Test creating event with data"""
        event = Event("test.event", data={'key': 'value'})

        assert event.data == {'key': 'value'}

    def test_event_creation_with_priority(self):
        """Test creating event with custom priority"""
        event = Event("test.event", priority=EventPriority.HIGH)

        assert event.priority == EventPriority.HIGH

    def test_event_creation_critical(self):
        """Test creating critical event"""
        event = Event("test.event", critical=True)

        assert event.critical

    def test_event_timestamp(self):
        """Test event has timestamp"""
        before = datetime.now().timestamp()
        event = Event("test.event")
        after = datetime.now().timestamp()

        assert before <= event.timestamp <= after


class TestEventPriority:
    """Test EventPriority enum"""

    def test_priority_values(self):
        """Test priority values"""
        assert EventPriority.CRITICAL == 1
        assert EventPriority.HIGH == 2
        assert EventPriority.NORMAL == 3
        assert EventPriority.LOW == 4

    def test_priority_ordering(self):
        """Test priority ordering (lower number = higher priority)"""
        assert EventPriority.CRITICAL < EventPriority.HIGH
        assert EventPriority.HIGH < EventPriority.NORMAL
        assert EventPriority.NORMAL < EventPriority.LOW


class TestAsyncEventBusInit:
    """Test AsyncEventBus initialization"""

    def test_init_defaults(self):
        """Test default initialization"""
        bus = AsyncEventBus()

        assert bus.event_queue.maxsize == 1000
        assert not bus.processing
        assert bus.processor_task is None
        assert bus.stats['events_published'] == 0

    def test_init_custom_queue_size(self):
        """Test initialization with custom queue size"""
        bus = AsyncEventBus(max_queue_size=500)

        assert bus.event_queue.maxsize == 500

    def test_init_subscribers_empty(self):
        """Test subscribers start empty"""
        bus = AsyncEventBus()

        assert len(bus.subscribers) == 0


class TestAsyncEventBusStartStop:
    """Test bus start and stop"""

    @pytest.mark.asyncio
    async def test_start_bus(self):
        """Test starting event bus"""
        bus = AsyncEventBus()

        await bus.start()

        assert bus.processing
        assert bus.processor_task is not None

        await bus.stop()

    @pytest.mark.asyncio
    async def test_start_already_running(self):
        """Test starting bus that's already running"""
        bus = AsyncEventBus()

        await bus.start()

        with patch('src.core.event_bus.logger') as mock_logger:
            await bus.start()  # Start again
            mock_logger.warning.assert_called_with("Event bus already running")

        await bus.stop()

    @pytest.mark.asyncio
    async def test_stop_bus(self):
        """Test stopping event bus"""
        bus = AsyncEventBus()

        await bus.start()
        await bus.stop()

        assert not bus.processing

    @pytest.mark.asyncio
    async def test_stop_not_running(self):
        """Test stopping bus that's not running"""
        bus = AsyncEventBus()

        with patch('src.core.event_bus.logger') as mock_logger:
            await bus.stop()
            mock_logger.warning.assert_called_with("Event bus not running")

    @pytest.mark.asyncio
    async def test_stop_cancels_processor(self):
        """Test stop cancels processor task"""
        bus = AsyncEventBus()

        await bus.start()
        processor_task = bus.processor_task

        await bus.stop()

        assert processor_task.cancelled() or processor_task.done()


class TestAsyncEventBusSubscribe:
    """Test event subscription"""

    def test_subscribe_handler(self):
        """Test subscribing to event type"""
        bus = AsyncEventBus()

        async def handler(event):
            pass

        bus.subscribe("test.event", handler)

        assert "test.event" in bus.subscribers
        assert handler in bus.subscribers["test.event"]

    def test_subscribe_multiple_handlers(self):
        """Test multiple handlers for same event"""
        bus = AsyncEventBus()

        async def handler1(event):
            pass

        async def handler2(event):
            pass

        bus.subscribe("test.event", handler1)
        bus.subscribe("test.event", handler2)

        assert len(bus.subscribers["test.event"]) == 2

    def test_get_subscriber_count(self):
        """Test getting subscriber count"""
        bus = AsyncEventBus()

        async def handler(event):
            pass

        bus.subscribe("test.event", handler)

        assert bus.get_subscriber_count("test.event") == 1

    def test_get_subscriber_count_no_subscribers(self):
        """Test subscriber count for event with no subscribers"""
        bus = AsyncEventBus()

        assert bus.get_subscriber_count("nonexistent") == 0


class TestAsyncEventBusUnsubscribe:
    """Test event unsubscription"""

    def test_unsubscribe_handler(self):
        """Test unsubscribing from event type"""
        bus = AsyncEventBus()

        async def handler(event):
            pass

        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)

        assert handler not in bus.subscribers["test.event"]

    def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing nonexistent handler"""
        bus = AsyncEventBus()

        async def handler(event):
            pass

        bus.unsubscribe("test.event", handler)  # Should not raise error

    def test_unsubscribe_nonexistent_event_type(self):
        """Test unsubscribing from nonexistent event type"""
        bus = AsyncEventBus()

        async def handler(event):
            pass

        bus.unsubscribe("nonexistent", handler)  # Should not raise error


class TestAsyncEventBusPublish:
    """Test event publishing"""

    @pytest.mark.asyncio
    async def test_publish_event(self):
        """Test publishing event"""
        bus = AsyncEventBus()
        event = Event("test.event")

        await bus.publish(event)

        assert bus.stats['events_published'] == 1
        assert not bus.event_queue.empty()

    @pytest.mark.asyncio
    async def test_publish_critical_event(self):
        """Test publishing critical event"""
        bus = AsyncEventBus(max_queue_size=1)
        event1 = Event("test.event1")
        event2 = Event("test.event2", critical=True)

        await bus.publish(event1)

        # Queue full, but critical event should be added
        await bus.publish(event2)

        assert bus.stats['events_published'] == 2

    @pytest.mark.asyncio
    async def test_publish_queue_full_non_critical(self):
        """Test publishing non-critical event when queue full"""
        bus = AsyncEventBus(max_queue_size=1)
        event1 = Event("test.event1")
        event2 = Event("test.event2")

        await bus.publish(event1)

        # Queue full, non-critical event should be dropped
        with pytest.raises(asyncio.QueueFull):
            await bus.publish(event2)

        assert bus.stats['events_dropped'] == 1

    @pytest.mark.asyncio
    async def test_publish_increments_stats(self):
        """Test publish increments statistics"""
        bus = AsyncEventBus()
        event = Event("test.event")

        await bus.publish(event)
        await bus.publish(event)
        await bus.publish(event)

        assert bus.stats['events_published'] == 3


class TestAsyncEventBusProcessEvents:
    """Test event processing"""

    @pytest.mark.asyncio
    async def test_process_events_basic(self):
        """Test basic event processing"""
        bus = AsyncEventBus()
        received_events = []

        async def handler(event):
            received_events.append(event)

        bus.subscribe("test.event", handler)
        await bus.start()

        event = Event("test.event", data={'value': 42})
        await bus.publish(event)

        # Wait for processing
        await asyncio.sleep(0.1)

        await bus.stop()

        assert len(received_events) == 1
        assert received_events[0].type == "test.event"

    @pytest.mark.asyncio
    async def test_process_events_multiple_handlers(self):
        """Test processing with multiple handlers"""
        bus = AsyncEventBus()
        handler1_called = []
        handler2_called = []

        async def handler1(event):
            handler1_called.append(event)

        async def handler2(event):
            handler2_called.append(event)

        bus.subscribe("test.event", handler1)
        bus.subscribe("test.event", handler2)
        await bus.start()

        event = Event("test.event")
        await bus.publish(event)

        await asyncio.sleep(0.1)
        await bus.stop()

        assert len(handler1_called) == 1
        assert len(handler2_called) == 1

    @pytest.mark.asyncio
    async def test_process_events_no_subscribers(self):
        """Test processing event with no subscribers"""
        bus = AsyncEventBus()
        await bus.start()

        event = Event("test.event")
        await bus.publish(event)

        await asyncio.sleep(0.1)
        await bus.stop()

        # Should not raise error

    @pytest.mark.asyncio
    async def test_process_events_priority_order(self):
        """Test events processed by priority"""
        bus = AsyncEventBus()
        processed_order = []

        async def handler(event):
            processed_order.append(event.priority)

        bus.subscribe("test.event", handler)
        await bus.start()

        # Publish events in different priority order
        await bus.publish(Event("test.event", priority=EventPriority.LOW))
        await bus.publish(Event("test.event", priority=EventPriority.CRITICAL))
        await bus.publish(Event("test.event", priority=EventPriority.NORMAL))

        await asyncio.sleep(0.2)
        await bus.stop()

        # Critical should be processed first
        assert processed_order[0] == EventPriority.CRITICAL

    @pytest.mark.asyncio
    async def test_process_critical_event_waits(self):
        """Test critical events wait for all handlers"""
        bus = AsyncEventBus()
        handler_completed = []

        async def slow_handler(event):
            await asyncio.sleep(0.1)
            handler_completed.append(True)

        bus.subscribe("test.event", slow_handler)
        await bus.start()

        event = Event("test.event", critical=True)
        await bus.publish(event)

        await asyncio.sleep(0.2)
        await bus.stop()

        assert len(handler_completed) == 1

    @pytest.mark.asyncio
    async def test_process_non_critical_event(self):
        """Test non-critical events fire and forget"""
        bus = AsyncEventBus()
        handler_called = []

        async def handler(event):
            handler_called.append(True)

        bus.subscribe("test.event", handler)
        await bus.start()

        event = Event("test.event", critical=False)
        await bus.publish(event)

        await asyncio.sleep(0.1)
        await bus.stop()

        assert len(handler_called) == 1

    @pytest.mark.asyncio
    async def test_process_events_handler_exception(self):
        """Test processing continues when handler raises exception"""
        bus = AsyncEventBus()
        handler_called = []

        async def failing_handler(event):
            raise Exception("Handler error")

        async def good_handler(event):
            handler_called.append(True)

        bus.subscribe("test.event", failing_handler)
        bus.subscribe("test.event", good_handler)
        await bus.start()

        event = Event("test.event")
        await bus.publish(event)

        await asyncio.sleep(0.1)
        await bus.stop()

        # Good handler should still be called
        assert len(handler_called) == 1

    @pytest.mark.asyncio
    async def test_process_events_timeout(self):
        """Test event processing timeout"""
        bus = AsyncEventBus()
        await bus.start()

        # Process empty queue (should timeout and continue)
        await asyncio.sleep(1.5)

        await bus.stop()
        # Should not raise error

    @pytest.mark.asyncio
    async def test_process_events_cancelled(self):
        """Test processing loop handles cancellation"""
        bus = AsyncEventBus()
        await bus.start()

        # Stop immediately to cancel processor
        await bus.stop()

        # Should handle CancelledError gracefully


class TestAsyncEventBusStats:
    """Test event bus statistics"""

    def test_get_stats_initial(self):
        """Test initial statistics"""
        bus = AsyncEventBus()
        stats = bus.get_stats()

        assert stats['events_published'] == 0
        assert stats['events_processed'] == 0
        assert stats['events_dropped'] == 0

    @pytest.mark.asyncio
    async def test_get_stats_after_publishing(self):
        """Test statistics after publishing"""
        bus = AsyncEventBus()
        event = Event("test.event")

        await bus.publish(event)

        stats = bus.get_stats()
        assert stats['events_published'] == 1

    @pytest.mark.asyncio
    async def test_get_stats_after_processing(self):
        """Test statistics after processing"""
        bus = AsyncEventBus()

        async def handler(event):
            pass

        bus.subscribe("test.event", handler)
        await bus.start()

        event = Event("test.event")
        await bus.publish(event)

        await asyncio.sleep(0.1)
        await bus.stop()

        stats = bus.get_stats()
        assert stats['events_processed'] == 1

    @pytest.mark.asyncio
    async def test_get_stats_dropped_events(self):
        """Test dropped events statistics"""
        bus = AsyncEventBus(max_queue_size=1)
        event1 = Event("test.event1")
        event2 = Event("test.event2")

        await bus.publish(event1)

        try:
            await bus.publish(event2)
        except asyncio.QueueFull:
            pass

        stats = bus.get_stats()
        assert stats['events_dropped'] == 1

    def test_get_stats_returns_copy(self):
        """Test get_stats returns copy of stats"""
        bus = AsyncEventBus()
        stats1 = bus.get_stats()
        stats2 = bus.get_stats()

        assert stats1 is not stats2
        assert stats1 == stats2


class TestAsyncEventBusEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_multiple_event_types(self):
        """Test handling multiple event types"""
        bus = AsyncEventBus()
        type1_events = []
        type2_events = []

        async def handler1(event):
            type1_events.append(event)

        async def handler2(event):
            type2_events.append(event)

        bus.subscribe("type1", handler1)
        bus.subscribe("type2", handler2)
        await bus.start()

        await bus.publish(Event("type1"))
        await bus.publish(Event("type2"))
        await bus.publish(Event("type1"))

        await asyncio.sleep(0.1)
        await bus.stop()

        assert len(type1_events) == 2
        assert len(type2_events) == 1

    @pytest.mark.asyncio
    async def test_high_volume_events(self):
        """Test handling high volume of events"""
        bus = AsyncEventBus(max_queue_size=5000)
        processed_count = []

        async def handler(event):
            processed_count.append(1)

        bus.subscribe("test.event", handler)
        await bus.start()

        # Publish many events
        for i in range(100):
            await bus.publish(Event("test.event"))

        await asyncio.sleep(0.5)
        await bus.stop()

        assert len(processed_count) == 100

    @pytest.mark.asyncio
    async def test_concurrent_publishing(self):
        """Test concurrent event publishing"""
        bus = AsyncEventBus()

        async def publish_event(event_type):
            await bus.publish(Event(event_type))

        # Publish concurrently
        await asyncio.gather(
            publish_event("type1"),
            publish_event("type2"),
            publish_event("type3")
        )

        assert bus.stats['events_published'] == 3

    @pytest.mark.asyncio
    async def test_event_data_preservation(self):
        """Test event data is preserved during processing"""
        bus = AsyncEventBus()
        received_data = []

        async def handler(event):
            received_data.append(event.data)

        bus.subscribe("test.event", handler)
        await bus.start()

        test_data = {'key': 'value', 'number': 42}
        await bus.publish(Event("test.event", data=test_data))

        await asyncio.sleep(0.1)
        await bus.stop()

        assert received_data[0] == test_data

    @pytest.mark.asyncio
    async def test_empty_event_type(self):
        """Test handling empty event type"""
        bus = AsyncEventBus()
        await bus.start()

        event = Event("")
        await bus.publish(event)

        await asyncio.sleep(0.1)
        await bus.stop()

        # Should handle gracefully

    @pytest.mark.asyncio
    async def test_subscribe_after_start(self):
        """Test subscribing after bus started"""
        bus = AsyncEventBus()
        await bus.start()

        received_events = []

        async def handler(event):
            received_events.append(event)

        bus.subscribe("test.event", handler)

        await bus.publish(Event("test.event"))
        await asyncio.sleep(0.1)

        await bus.stop()

        assert len(received_events) == 1
