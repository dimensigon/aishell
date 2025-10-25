"""
UI Event Integration Coordinator

Coordinates UI events with AsyncEventBus, routes events to appropriate handlers,
manages event priorities, and implements debouncing for frequent events.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from src.core.event_bus import AsyncEventBus, Event, EventPriority

logger = logging.getLogger(__name__)


class UIEventIntegration:
    """
    Coordinates UI events with AsyncEventBus.

    Handles:
    - Event routing to appropriate UI handlers
    - Event priority management (typing > preview > suggestions)
    - Debouncing for frequent events
    - Task cancellation for superseded operations

    Event types:
    - typing_state_changed: User typing state updates
    - command_preview_request: Request preview update
    - risk_analysis_complete: Risk analysis results ready
    - suggestion_request: Request autocomplete suggestions
    - suggestions_ready: Suggestions available for display
    """

    def __init__(
        self,
        event_bus: AsyncEventBus,
        command_preview: Optional[Any] = None,
        suggestion_list: Optional[Any] = None
    ):
        """
        Initialize event coordinator.

        Args:
            event_bus: AsyncEventBus instance for pub/sub
            command_preview: CommandPreviewWidget instance (optional)
            suggestion_list: SmartSuggestionList instance (optional)
        """
        self.event_bus = event_bus
        self.command_preview = command_preview
        self.suggestion_list = suggestion_list

        # Debounce timers and tasks
        self._typing_task: Optional[asyncio.Task] = None
        self._preview_task: Optional[asyncio.Task] = None
        self._suggestion_task: Optional[asyncio.Task] = None

        # Debounce delays (in seconds)
        self.typing_debounce = 0.2  # 200ms
        self.preview_debounce = 0.3  # 300ms
        self.suggestion_debounce = 0.15  # 150ms

        # Last event timestamps for debouncing
        self._last_typing_event = 0.0
        self._last_preview_event = 0.0
        self._last_suggestion_event = 0.0

        # Event statistics
        self.stats = {
            'typing_events': 0,
            'preview_events': 0,
            'suggestion_events': 0,
            'risk_events': 0,
            'debounced_events': 0
        }

        # Subscribe to events
        self._subscribe_to_events()

        logger.info("UI Event Integration initialized")

    def _subscribe_to_events(self) -> None:
        """Subscribe to all relevant UI events"""
        self.event_bus.subscribe('typing_state_changed', self.handle_typing)
        self.event_bus.subscribe('command_preview_request', self.handle_preview_request)
        self.event_bus.subscribe('suggestion_request', self.handle_suggestion_request)
        self.event_bus.subscribe('risk_analysis_complete', self.handle_risk_complete)
        self.event_bus.subscribe('suggestions_ready', self.handle_suggestions_ready)

        logger.debug("Subscribed to UI events")

    async def handle_typing(self, event: Event) -> None:
        """
        Handle typing state changes with debouncing.

        Triggers preview and suggestions after debounce period.

        Args:
            event: Event with data={'is_typing': bool, 'command': str}
        """
        self.stats['typing_events'] += 1

        # Cancel previous typing task
        if self._typing_task and not self._typing_task.done():
            self._typing_task.cancel()
            self.stats['debounced_events'] += 1

        # Check if we need to debounce
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self._last_typing_event

        if time_since_last < self.typing_debounce:
            # Debounce: wait for the full period
            delay = self.typing_debounce - time_since_last
            logger.debug(f"Debouncing typing event by {delay:.3f}s")
            await asyncio.sleep(delay)

        self._last_typing_event = datetime.now().timestamp()

        # Create debounced task
        self._typing_task = asyncio.create_task(
            self._process_typing(event.data)
        )

        try:
            await self._typing_task
        except asyncio.CancelledError:
            logger.debug("Typing task cancelled by newer input")

    async def _process_typing(self, data: Dict[str, Any]) -> None:
        """
        Process typing event after debounce.

        Args:
            data: Event data containing command and typing state
        """
        is_typing = data.get('is_typing', False)
        command = data.get('command', '')

        if not is_typing or not command:
            return

        logger.debug(f"Processing typing event: '{command[:50]}...'")

        # Trigger preview update (high priority)
        await self.event_bus.publish(
            Event(
                'command_preview_request',
                {'command': command},
                priority=EventPriority.HIGH
            )
        )

        # Trigger suggestion request (normal priority)
        await self.event_bus.publish(
            Event(
                'suggestion_request',
                {'query': command},
                priority=EventPriority.NORMAL
            )
        )

    async def handle_preview_request(self, event: Event) -> None:
        """
        Handle command preview requests with debouncing.

        Args:
            event: Event with data={'command': str}
        """
        self.stats['preview_events'] += 1

        # Cancel previous preview task
        if self._preview_task and not self._preview_task.done():
            self._preview_task.cancel()
            self.stats['debounced_events'] += 1

        # Check if we need to debounce
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self._last_preview_event

        if time_since_last < self.preview_debounce:
            # Debounce: wait for the full period
            delay = self.preview_debounce - time_since_last
            logger.debug(f"Debouncing preview request by {delay:.3f}s")
            await asyncio.sleep(delay)

        self._last_preview_event = datetime.now().timestamp()

        # Create debounced task
        self._preview_task = asyncio.create_task(
            self._process_preview(event.data)
        )

        try:
            await self._preview_task
        except asyncio.CancelledError:
            logger.debug("Preview task cancelled by newer request")

    async def _process_preview(self, data: Dict[str, Any]) -> None:
        """
        Process preview request after debounce.

        Args:
            data: Event data containing command
        """
        command = data.get('command', '')

        if not command or not self.command_preview:
            return

        logger.debug(f"Processing preview request: '{command[:50]}...'")

        # Update preview widget (widget handles async analysis)
        if hasattr(self.command_preview, 'analyze_command'):
            await self.command_preview.analyze_command(command)
        else:
            logger.warning("CommandPreviewWidget missing analyze_command method")

    async def handle_suggestion_request(self, event: Event) -> None:
        """
        Handle suggestion requests with debouncing.

        Args:
            event: Event with data={'query': str, 'context': Dict}
        """
        self.stats['suggestion_events'] += 1

        # Cancel previous suggestion task
        if self._suggestion_task and not self._suggestion_task.done():
            self._suggestion_task.cancel()
            self.stats['debounced_events'] += 1

        # Check if we need to debounce
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self._last_suggestion_event

        if time_since_last < self.suggestion_debounce:
            # Debounce: wait for the full period
            delay = self.suggestion_debounce - time_since_last
            logger.debug(f"Debouncing suggestion request by {delay:.3f}s")
            await asyncio.sleep(delay)

        self._last_suggestion_event = datetime.now().timestamp()

        # Create debounced task
        self._suggestion_task = asyncio.create_task(
            self._process_suggestions(event.data)
        )

        try:
            await self._suggestion_task
        except asyncio.CancelledError:
            logger.debug("Suggestion task cancelled by newer request")

    async def _process_suggestions(self, data: Dict[str, Any]) -> None:
        """
        Process suggestion request after debounce.

        Args:
            data: Event data containing query and optional context
        """
        query = data.get('query', '')
        context = data.get('context', {})

        if not query or not self.suggestion_list:
            return

        logger.debug(f"Processing suggestion request: '{query[:50]}...'")

        # Update suggestion widget (widget handles async search)
        if hasattr(self.suggestion_list, 'search_suggestions'):
            await self.suggestion_list.search_suggestions(query, context)
        else:
            logger.warning("SmartSuggestionList missing search_suggestions method")

    async def handle_risk_complete(self, event: Event) -> None:
        """
        Handle risk analysis completion.

        Args:
            event: Event with data={'analysis': Dict, 'command': str}
        """
        self.stats['risk_events'] += 1

        analysis = event.data.get('analysis', {})
        command = event.data.get('command', '')

        logger.debug(
            f"Risk analysis complete for '{command[:50]}...': "
            f"{analysis.get('risk_level', 'UNKNOWN')}"
        )

        # Update preview widget with analysis results
        if self.command_preview and hasattr(self.command_preview, 'update_analysis'):
            await self.command_preview.update_analysis(analysis)

    async def handle_suggestions_ready(self, event: Event) -> None:
        """
        Handle suggestions ready event.

        Args:
            event: Event with data={'candidates': List[CompletionCandidate]}
        """
        candidates = event.data.get('candidates', [])

        logger.debug(f"Suggestions ready: {len(candidates)} candidates")

        # Update suggestion list with candidates
        if self.suggestion_list and hasattr(self.suggestion_list, 'update_suggestions'):
            await self.suggestion_list.update_suggestions(candidates)

    def set_command_preview(self, widget: Any) -> None:
        """
        Set or update the command preview widget.

        Args:
            widget: CommandPreviewWidget instance
        """
        self.command_preview = widget
        logger.debug("Command preview widget updated")

    def set_suggestion_list(self, widget: Any) -> None:
        """
        Set or update the suggestion list widget.

        Args:
            widget: SmartSuggestionList instance
        """
        self.suggestion_list = widget
        logger.debug("Suggestion list widget updated")

    def get_stats(self) -> Dict[str, int]:
        """
        Get event processing statistics.

        Returns:
            Dictionary of event counts and metrics
        """
        return {
            **self.stats,
            'event_bus_stats': self.event_bus.get_stats()
        }

    async def shutdown(self) -> None:
        """
        Shutdown the event coordinator.

        Cancels all pending tasks and cleans up resources.
        """
        logger.info("Shutting down UI Event Integration")

        # Cancel all pending tasks
        tasks = [
            self._typing_task,
            self._preview_task,
            self._suggestion_task
        ]

        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info("UI Event Integration shutdown complete")
