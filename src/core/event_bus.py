"""
Async Event Bus for Inter-Module Communication

Provides pub/sub pattern with priority queue and backpressure handling.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import IntEnum
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class EventPriority(IntEnum):
    """Event priority levels (lower number = higher priority)"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass(order=True)
class Event:
    """
    Event object for pub/sub communication.

    Attributes:
        type: Event type identifier
        priority: Event priority (1=highest, 4=lowest)
        data: Event payload
        timestamp: Event creation timestamp
        critical: Whether event requires guaranteed processing
    """
    priority: int = field(compare=True)
    timestamp: float = field(compare=True)
    type: str = field(compare=False, default="")
    data: Dict[str, Any] = field(compare=False, default_factory=dict)
    critical: bool = field(compare=False, default=False)

    def __init__(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        critical: bool = False
    ):
        self.type = event_type
        self.data = data or {}
        self.priority = priority
        self.critical = critical
        self.timestamp = datetime.now().timestamp()


class AsyncEventBus:
    """
    Asynchronous event bus with priority queue and backpressure handling.

    Features:
    - Priority-based event processing
    - Async subscriber handlers
    - Backpressure management
    - Critical event guarantees
    """

    def __init__(self, max_queue_size: int = 1000) -> None:
        """
        Initialize event bus.

        Args:
            max_queue_size: Maximum events in queue before backpressure
        """
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(
            maxsize=max_queue_size
        )
        self.processing = False
        self.processor_task: Optional[asyncio.Task] = None
        self.stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_dropped': 0
        }

        logger.info(f"Event bus created with queue size {max_queue_size}")

    async def start(self) -> None:
        """Start event processing loop"""
        if self.processing:
            logger.warning("Event bus already running")
            return

        self.processing = True
        self.processor_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop event processing loop"""
        if not self.processing:
            logger.warning("Event bus not running")
            return

        self.processing = False

        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass

        logger.info("Event bus stopped")

    def subscribe(self, event_type: str, handler: Callable[..., Any]) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async function to call when event occurs
        """
        self.subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to '{event_type}' (total: {len(self.subscribers[event_type])})")

    def unsubscribe(self, event_type: str, handler: Callable[..., Any]) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self.subscribers and handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
            logger.debug(f"Unsubscribed from '{event_type}'")

    async def publish(self, event: Event) -> None:
        """
        Publish an event to the bus.

        Args:
            event: Event to publish

        Raises:
            asyncio.QueueFull: If queue is full and event is not critical
        """
        try:
            # Critical events always added, even if queue full
            if event.critical:
                await self.event_queue.put(event)
            else:
                # Non-critical events can be dropped if queue full
                self.event_queue.put_nowait(event)

            self.stats['events_published'] += 1
            logger.debug(f"Event published: {event.type} (priority: {event.priority})")

        except asyncio.QueueFull:
            self.stats['events_dropped'] += 1
            logger.warning(f"Event dropped due to full queue: {event.type}")
            raise

    async def _process_events(self) -> None:
        """
        Continuous event processing loop.

        Processes events from priority queue and dispatches to subscribers.
        """
        logger.info("Event processing loop started")

        while self.processing:
            try:
                # Get next event (blocks until available)
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )

                # Get subscribers for this event type
                handlers = self.subscribers.get(event.type, [])

                if not handlers:
                    logger.debug(f"No subscribers for event: {event.type}")
                    continue

                # Execute all handlers
                tasks = [handler(event) for handler in handlers]

                if event.critical:
                    # Critical events wait for all handlers
                    await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    # Non-critical events fire and forget
                    await asyncio.gather(*tasks, return_exceptions=True)

                self.stats['events_processed'] += 1
                logger.debug(f"Event processed: {event.type}")

            except asyncio.TimeoutError:
                # No events available, continue loop
                continue
            except asyncio.CancelledError:
                logger.info("Event processing loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

        logger.info("Event processing loop stopped")

    def get_stats(self) -> Dict[str, int]:
        """Get event bus statistics"""
        return self.stats.copy()

    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type"""
        return len(self.subscribers.get(event_type, []))
