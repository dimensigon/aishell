"""
GraphQL Subscriptions for Real-Time Data

Provides WebSocket-based subscriptions for live data updates.
"""

from typing import Dict, List, Optional, Any, AsyncIterator, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """A subscription instance"""
    id: str
    topic: str
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class SubscriptionManager:
    """
    Manages GraphQL subscriptions for real-time updates

    Features:
    - WebSocket-based pub/sub
    - Topic-based filtering
    - Connection management
    - Automatic cleanup
    """

    def __init__(self):
        """Initialize subscription manager"""
        # Topic subscribers: topic -> set of subscriber IDs
        self.subscribers: Dict[str, Set[str]] = {}

        # Active subscriptions: subscriber_id -> Subscription
        self.subscriptions: Dict[str, Subscription] = {}

        # Message queues for each subscriber
        self.queues: Dict[str, asyncio.Queue] = {}

    async def subscribe(
        self,
        subscriber_id: str,
        topic: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """
        Subscribe to a topic

        Args:
            subscriber_id: Unique subscriber identifier
            topic: Topic to subscribe to
            filters: Optional filters for events

        Returns:
            Subscription instance
        """
        subscription = Subscription(
            id=subscriber_id,
            topic=topic,
            filters=filters or {}
        )

        # Add to subscribers
        if topic not in self.subscribers:
            self.subscribers[topic] = set()
        self.subscribers[topic].add(subscriber_id)

        # Store subscription
        self.subscriptions[subscriber_id] = subscription

        # Create message queue
        if subscriber_id not in self.queues:
            self.queues[subscriber_id] = asyncio.Queue()

        logger.info(f"Subscriber {subscriber_id} subscribed to {topic}")
        return subscription

    async def unsubscribe(self, subscriber_id: str):
        """
        Unsubscribe from all topics

        Args:
            subscriber_id: Subscriber to unsubscribe
        """
        if subscriber_id not in self.subscriptions:
            return

        subscription = self.subscriptions[subscriber_id]

        # Remove from topic subscribers
        if subscription.topic in self.subscribers:
            self.subscribers[subscription.topic].discard(subscriber_id)
            if not self.subscribers[subscription.topic]:
                del self.subscribers[subscription.topic]

        # Remove subscription
        del self.subscriptions[subscriber_id]

        # Remove queue
        if subscriber_id in self.queues:
            del self.queues[subscriber_id]

        logger.info(f"Subscriber {subscriber_id} unsubscribed from {subscription.topic}")

    async def publish(
        self,
        topic: str,
        data: Any,
        metadata: Optional[Dict] = None
    ):
        """
        Publish data to topic subscribers

        Args:
            topic: Topic to publish to
            data: Data to send
            metadata: Optional metadata
        """
        if topic not in self.subscribers:
            return

        message = {
            'topic': topic,
            'data': data,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }

        # Send to all subscribers
        for subscriber_id in self.subscribers[topic]:
            if subscriber_id in self.queues:
                subscription = self.subscriptions.get(subscriber_id)

                # Apply filters
                if subscription and self._matches_filters(data, subscription.filters):
                    await self.queues[subscriber_id].put(message)

        logger.debug(f"Published to {topic}: {len(self.subscribers[topic])} subscribers")

    async def listen(self, subscriber_id: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Listen for messages (async generator for subscriptions)

        Args:
            subscriber_id: Subscriber ID

        Yields:
            Messages for subscriber
        """
        if subscriber_id not in self.queues:
            logger.error(f"No queue for subscriber {subscriber_id}")
            return

        queue = self.queues[subscriber_id]

        try:
            while True:
                # Wait for message
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            logger.info(f"Subscription cancelled for {subscriber_id}")
        except Exception as e:
            logger.error(f"Error in subscription {subscriber_id}: {e}")

    def get_subscriber_count(self, topic: Optional[str] = None) -> int:
        """
        Get number of subscribers

        Args:
            topic: Optional topic filter

        Returns:
            Subscriber count
        """
        if topic:
            return len(self.subscribers.get(topic, set()))
        return len(self.subscriptions)

    def get_topics(self) -> List[str]:
        """
        Get list of active topics

        Returns:
            List of topic names
        """
        return list(self.subscribers.keys())

    def _matches_filters(self, data: Any, filters: Dict[str, Any]) -> bool:
        """
        Check if data matches subscription filters

        Args:
            data: Data to check
            filters: Filter criteria

        Returns:
            True if matches
        """
        if not filters:
            return True

        # Simple filter matching (can be extended)
        if not isinstance(data, dict):
            return True

        for key, value in filters.items():
            if key not in data:
                return False
            if data[key] != value:
                return False

        return True


# Strawberry subscription examples
def create_database_subscriptions(subscription_manager: SubscriptionManager):
    """
    Create subscription resolvers for database events

    Args:
        subscription_manager: SubscriptionManager instance

    Returns:
        Dictionary of subscription resolvers
    """
    try:
        import strawberry
    except ImportError:
        logger.error("strawberry-graphql not available")
        return {}

    @strawberry.type
    class Subscription:
        """GraphQL Subscription type"""

        @strawberry.subscription
        async def table_changes(
            self,
            info: strawberry.types.Info,
            table_name: str,
            operation: Optional[str] = None
        ) -> AsyncIterator[Dict[str, Any]]:
            """
            Subscribe to table changes

            Args:
                table_name: Table to monitor
                operation: Optional operation filter (INSERT, UPDATE, DELETE)

            Yields:
                Change events
            """
            subscriber_id = f"table_{table_name}_{id(info)}"
            filters = {'operation': operation} if operation else {}

            await subscription_manager.subscribe(
                subscriber_id,
                f"table:{table_name}",
                filters
            )

            try:
                async for message in subscription_manager.listen(subscriber_id):
                    yield message['data']
            finally:
                await subscription_manager.unsubscribe(subscriber_id)

        @strawberry.subscription
        async def query_results(
            self,
            info: strawberry.types.Info,
            query_id: str
        ) -> AsyncIterator[Dict[str, Any]]:
            """
            Subscribe to query result updates

            Args:
                query_id: Query identifier

            Yields:
                Updated query results
            """
            subscriber_id = f"query_{query_id}_{id(info)}"

            await subscription_manager.subscribe(
                subscriber_id,
                f"query:{query_id}"
            )

            try:
                async for message in subscription_manager.listen(subscriber_id):
                    yield message['data']
            finally:
                await subscription_manager.unsubscribe(subscriber_id)

        @strawberry.subscription
        async def security_events(
            self,
            info: strawberry.types.Info,
            threat_level: Optional[str] = None
        ) -> AsyncIterator[Dict[str, Any]]:
            """
            Subscribe to security events

            Args:
                threat_level: Optional threat level filter

            Yields:
                Security event notifications
            """
            subscriber_id = f"security_{id(info)}"
            filters = {'threat_level': threat_level} if threat_level else {}

            await subscription_manager.subscribe(
                subscriber_id,
                "security:events",
                filters
            )

            try:
                async for message in subscription_manager.listen(subscriber_id):
                    yield message['data']
            finally:
                await subscription_manager.unsubscribe(subscriber_id)

    return Subscription


class DatabaseChangeNotifier:
    """
    Notifies subscribers of database changes

    Integrates with DatabaseModule to publish change events.
    """

    def __init__(self, subscription_manager: SubscriptionManager):
        """
        Initialize notifier

        Args:
            subscription_manager: SubscriptionManager instance
        """
        self.subscription_manager = subscription_manager

    async def notify_insert(
        self,
        table_name: str,
        record_id: Any,
        data: Dict[str, Any]
    ):
        """
        Notify subscribers of INSERT

        Args:
            table_name: Table name
            record_id: Inserted record ID
            data: Inserted data
        """
        await self.subscription_manager.publish(
            f"table:{table_name}",
            {
                'operation': 'INSERT',
                'table': table_name,
                'record_id': record_id,
                'data': data
            }
        )

    async def notify_update(
        self,
        table_name: str,
        record_id: Any,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ):
        """
        Notify subscribers of UPDATE

        Args:
            table_name: Table name
            record_id: Updated record ID
            old_data: Old data
            new_data: New data
        """
        await self.subscription_manager.publish(
            f"table:{table_name}",
            {
                'operation': 'UPDATE',
                'table': table_name,
                'record_id': record_id,
                'old_data': old_data,
                'new_data': new_data
            }
        )

    async def notify_delete(
        self,
        table_name: str,
        record_id: Any,
        data: Dict[str, Any]
    ):
        """
        Notify subscribers of DELETE

        Args:
            table_name: Table name
            record_id: Deleted record ID
            data: Deleted data
        """
        await self.subscription_manager.publish(
            f"table:{table_name}",
            {
                'operation': 'DELETE',
                'table': table_name,
                'record_id': record_id,
                'data': data
            }
        )
