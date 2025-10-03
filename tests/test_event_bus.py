"""
Tests for Async Event Bus
"""

import pytest
import asyncio
from src.core.event_bus import AsyncEventBus, Event, EventPriority


@pytest.mark.asyncio
async def test_event_subscription():
    """Test event subscription and delivery"""
    bus = AsyncEventBus()
    await bus.start()

    received_events = []

    async def handler(event):
        received_events.append(event)

    bus.subscribe("test_event", handler)
    await bus.publish(Event("test_event", data={"test": "data"}))

    await asyncio.sleep(0.1)  # Allow processing

    assert len(received_events) == 1
    assert received_events[0].type == "test_event"
    assert received_events[0].data["test"] == "data"

    await bus.stop()


@pytest.mark.asyncio
async def test_event_priority():
    """Test high-priority events processed first"""
    bus = AsyncEventBus()
    await bus.start()

    processing_order = []

    async def handler(event):
        processing_order.append(event.priority)

    bus.subscribe("priority_test", handler)

    # Publish in reverse priority order
    await bus.publish(Event("priority_test", priority=EventPriority.LOW))
    await bus.publish(Event("priority_test", priority=EventPriority.CRITICAL))
    await bus.publish(Event("priority_test", priority=EventPriority.NORMAL))

    await asyncio.sleep(0.2)

    # Should be processed in priority order: CRITICAL (1), NORMAL (3), LOW (4)
    assert processing_order == [EventPriority.CRITICAL, EventPriority.NORMAL, EventPriority.LOW]

    await bus.stop()


@pytest.mark.asyncio
async def test_multiple_subscribers():
    """Test multiple subscribers receive same event"""
    bus = AsyncEventBus()
    await bus.start()

    results = []

    async def handler1(event):
        results.append("handler1")

    async def handler2(event):
        results.append("handler2")

    bus.subscribe("multi_sub", handler1)
    bus.subscribe("multi_sub", handler2)

    await bus.publish(Event("multi_sub"))
    await asyncio.sleep(0.1)

    assert "handler1" in results
    assert "handler2" in results
    assert len(results) == 2

    await bus.stop()


@pytest.mark.asyncio
async def test_unsubscribe():
    """Test unsubscribing from events"""
    bus = AsyncEventBus()
    await bus.start()

    call_count = 0

    async def handler(event):
        nonlocal call_count
        call_count += 1

    bus.subscribe("unsub_test", handler)
    await bus.publish(Event("unsub_test"))
    await asyncio.sleep(0.1)

    assert call_count == 1

    bus.unsubscribe("unsub_test", handler)
    await bus.publish(Event("unsub_test"))
    await asyncio.sleep(0.1)

    assert call_count == 1  # Should not increase

    await bus.stop()


@pytest.mark.asyncio
async def test_critical_event_processing():
    """Test critical events are always processed"""
    bus = AsyncEventBus()
    await bus.start()

    received = []

    async def handler(event):
        received.append(event.critical)

    bus.subscribe("critical_test", handler)

    await bus.publish(Event("critical_test", critical=True))
    await bus.publish(Event("critical_test", critical=False))

    await asyncio.sleep(0.2)

    assert True in received
    assert False in received

    await bus.stop()


@pytest.mark.asyncio
async def test_event_stats():
    """Test event statistics tracking"""
    bus = AsyncEventBus()
    await bus.start()

    async def handler(event):
        pass

    bus.subscribe("stats_test", handler)

    await bus.publish(Event("stats_test"))
    await bus.publish(Event("stats_test"))
    await asyncio.sleep(0.1)

    stats = bus.get_stats()
    assert stats['events_published'] == 2
    assert stats['events_processed'] == 2

    await bus.stop()


@pytest.mark.asyncio
async def test_no_subscribers():
    """Test event with no subscribers doesn't error"""
    bus = AsyncEventBus()
    await bus.start()

    # Should not raise error
    await bus.publish(Event("no_subs"))
    await asyncio.sleep(0.1)

    stats = bus.get_stats()
    assert stats['events_published'] == 1

    await bus.stop()


@pytest.mark.asyncio
async def test_subscriber_count():
    """Test getting subscriber count"""
    bus = AsyncEventBus()

    async def handler1(event):
        pass

    async def handler2(event):
        pass

    bus.subscribe("count_test", handler1)
    bus.subscribe("count_test", handler2)

    count = bus.get_subscriber_count("count_test")
    assert count == 2

    count_none = bus.get_subscriber_count("nonexistent")
    assert count_none == 0


@pytest.mark.asyncio
async def test_queue_backpressure():
    """Test queue backpressure handling"""
    bus = AsyncEventBus(max_queue_size=5)
    await bus.start()

    # Fill queue with non-critical events
    for i in range(5):
        await bus.publish(Event(f"event_{i}"))

    # Next non-critical event should raise QueueFull
    with pytest.raises(asyncio.QueueFull):
        await bus.publish(Event("overflow", critical=False))

    # But critical event should still work
    await bus.publish(Event("critical_overflow", critical=True))

    await bus.stop()
