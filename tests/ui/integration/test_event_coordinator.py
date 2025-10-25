"""
Tests for UI Event Coordinator (src/ui/integration/event_coordinator.py)

Tests event distribution, async handling, debouncing, and widget coordination.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.ui.integration.event_coordinator import UIEventIntegration
from src.core.event_bus import AsyncEventBus, Event, EventPriority


class TestUIEventIntegration:
    """Test suite for UIEventIntegration."""

    @pytest.fixture
    def event_bus(self):
        """Create AsyncEventBus instance."""
        return AsyncEventBus()

    @pytest.fixture
    def mock_command_preview(self):
        """Create mock command preview widget."""
        widget = Mock()
        widget.analyze_command = AsyncMock()
        widget.update_analysis = AsyncMock()
        return widget

    @pytest.fixture
    def mock_suggestion_list(self):
        """Create mock suggestion list widget."""
        widget = Mock()
        widget.search_suggestions = AsyncMock()
        widget.update_suggestions = AsyncMock()
        return widget

    @pytest.fixture
    def coordinator(self, event_bus, mock_command_preview, mock_suggestion_list):
        """Create UIEventIntegration instance."""
        return UIEventIntegration(
            event_bus=event_bus,
            command_preview=mock_command_preview,
            suggestion_list=mock_suggestion_list
        )

    def test_initialization(self, coordinator, event_bus):
        """Test coordinator initializes correctly."""
        assert coordinator.event_bus == event_bus
        assert coordinator.typing_debounce == 0.2
        assert coordinator.preview_debounce == 0.3
        assert coordinator.suggestion_debounce == 0.15

        # Check stats initialized
        assert coordinator.stats['typing_events'] == 0
        assert coordinator.stats['preview_events'] == 0

    def test_subscribe_to_events(self, coordinator):
        """Test coordinator subscribes to all events."""
        # Event bus should have subscribers
        assert len(coordinator.event_bus._subscribers) > 0

    @pytest.mark.asyncio
    async def test_handle_typing_event(self, coordinator, event_bus):
        """Test handling typing state change event."""
        coordinator._process_typing = AsyncMock()

        event = Event(
            'typing_state_changed',
            {'is_typing': True, 'command': 'SELECT *'},
            priority=EventPriority.HIGH
        )

        await coordinator.handle_typing(event)

        assert coordinator.stats['typing_events'] == 1

    @pytest.mark.asyncio
    async def test_handle_typing_debouncing(self, coordinator):
        """Test typing event debouncing."""
        coordinator._process_typing = AsyncMock()

        event = Event(
            'typing_state_changed',
            {'is_typing': True, 'command': 'SELECT *'}
        )

        # Send multiple events rapidly
        tasks = [
            coordinator.handle_typing(event)
            for _ in range(5)
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        # Should debounce multiple events
        assert coordinator.stats['debounced_events'] > 0

    @pytest.mark.asyncio
    async def test_process_typing_publishes_events(self, coordinator, event_bus):
        """Test typing processing publishes preview and suggestion events."""
        published_events = []

        async def capture_event(event):
            published_events.append(event)

        event_bus.subscribe('command_preview_request', capture_event)
        event_bus.subscribe('suggestion_request', capture_event)

        data = {'is_typing': True, 'command': 'SELECT * FROM users'}

        await coordinator._process_typing(data)

        # Should publish both events
        assert len(published_events) >= 2
        assert any(e.type == 'command_preview_request' for e in published_events)
        assert any(e.type == 'suggestion_request' for e in published_events)

    @pytest.mark.asyncio
    async def test_handle_preview_request(self, coordinator, mock_command_preview):
        """Test handling preview request."""
        event = Event(
            'command_preview_request',
            {'command': 'SELECT * FROM users'}
        )

        await coordinator.handle_preview_request(event)

        assert coordinator.stats['preview_events'] == 1

    @pytest.mark.asyncio
    async def test_process_preview_calls_widget(self, coordinator, mock_command_preview):
        """Test preview processing calls widget method."""
        data = {'command': 'SELECT * FROM users'}

        await coordinator._process_preview(data)

        mock_command_preview.analyze_command.assert_called_once_with(
            'SELECT * FROM users'
        )

    @pytest.mark.asyncio
    async def test_process_preview_empty_command(self, coordinator, mock_command_preview):
        """Test preview processing skips empty command."""
        data = {'command': ''}

        await coordinator._process_preview(data)

        mock_command_preview.analyze_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_suggestion_request(self, coordinator):
        """Test handling suggestion request."""
        event = Event(
            'suggestion_request',
            {'query': 'SELECT', 'context': {}}
        )

        await coordinator.handle_suggestion_request(event)

        assert coordinator.stats['suggestion_events'] == 1

    @pytest.mark.asyncio
    async def test_process_suggestions_calls_widget(self, coordinator, mock_suggestion_list):
        """Test suggestion processing calls widget method."""
        data = {'query': 'SELECT', 'context': {'table': 'users'}}

        await coordinator._process_suggestions(data)

        mock_suggestion_list.search_suggestions.assert_called_once_with(
            'SELECT',
            {'table': 'users'}
        )

    @pytest.mark.asyncio
    async def test_handle_risk_complete(self, coordinator, mock_command_preview):
        """Test handling risk analysis completion."""
        event = Event(
            'risk_analysis_complete',
            {
                'analysis': {'risk_level': 'HIGH', 'warnings': []},
                'command': 'DROP TABLE users'
            }
        )

        await coordinator.handle_risk_complete(event)

        assert coordinator.stats['risk_events'] == 1

    @pytest.mark.asyncio
    async def test_handle_suggestions_ready(self, coordinator, mock_suggestion_list):
        """Test handling suggestions ready event."""
        from src.vector.autocomplete import CompletionCandidate

        candidates = [
            CompletionCandidate(text="SELECT *", score=0.9, source="vector"),
            CompletionCandidate(text="SELECT id", score=0.8, source="pattern"),
        ]

        event = Event(
            'suggestions_ready',
            {'candidates': candidates}
        )

        await coordinator.handle_suggestions_ready(event)

        mock_suggestion_list.update_suggestions.assert_called_once_with(candidates)

    @pytest.mark.asyncio
    async def test_debounce_cancels_previous_task(self, coordinator):
        """Test debouncing cancels previous task."""
        coordinator._process_typing = AsyncMock()

        event = Event(
            'typing_state_changed',
            {'is_typing': True, 'command': 'SELECT'}
        )

        # Start first task
        task1 = asyncio.create_task(coordinator.handle_typing(event))
        await asyncio.sleep(0.05)

        # Start second task (should cancel first)
        task2 = asyncio.create_task(coordinator.handle_typing(event))

        await asyncio.gather(task1, task2, return_exceptions=True)

        # Should have debounced at least once
        assert coordinator.stats['debounced_events'] > 0

    @pytest.mark.asyncio
    async def test_preview_debounce_delay(self, coordinator):
        """Test preview debounce respects delay."""
        coordinator._process_preview = AsyncMock()

        event = Event(
            'command_preview_request',
            {'command': 'SELECT *'}
        )

        start = asyncio.get_event_loop().time()

        # Send events rapidly
        await coordinator.handle_preview_request(event)
        await asyncio.sleep(0.1)
        await coordinator.handle_preview_request(event)

        duration = asyncio.get_event_loop().time() - start

        # Should wait for debounce period
        assert duration >= coordinator.preview_debounce

    def test_set_command_preview(self, coordinator):
        """Test setting command preview widget."""
        new_widget = Mock()

        coordinator.set_command_preview(new_widget)

        assert coordinator.command_preview == new_widget

    def test_set_suggestion_list(self, coordinator):
        """Test setting suggestion list widget."""
        new_widget = Mock()

        coordinator.set_suggestion_list(new_widget)

        assert coordinator.suggestion_list == new_widget

    def test_get_stats(self, coordinator):
        """Test getting event statistics."""
        stats = coordinator.get_stats()

        assert 'typing_events' in stats
        assert 'preview_events' in stats
        assert 'suggestion_events' in stats
        assert 'risk_events' in stats
        assert 'debounced_events' in stats
        assert 'event_bus_stats' in stats

    @pytest.mark.asyncio
    async def test_shutdown_cancels_tasks(self, coordinator):
        """Test shutdown cancels all pending tasks."""
        # Create some pending tasks
        coordinator._typing_task = asyncio.create_task(asyncio.sleep(10))
        coordinator._preview_task = asyncio.create_task(asyncio.sleep(10))
        coordinator._suggestion_task = asyncio.create_task(asyncio.sleep(10))

        await coordinator.shutdown()

        # All tasks should be cancelled
        assert coordinator._typing_task.cancelled()
        assert coordinator._preview_task.cancelled()
        assert coordinator._suggestion_task.cancelled()

    @pytest.mark.asyncio
    async def test_event_priority_handling(self, coordinator, event_bus):
        """Test events respect priority."""
        processed_events = []

        async def track_event(event):
            processed_events.append(event.type)

        event_bus.subscribe('command_preview_request', track_event)
        event_bus.subscribe('suggestion_request', track_event)

        # Publish events with different priorities
        await event_bus.publish(Event(
            'command_preview_request',
            {'command': 'TEST'},
            priority=EventPriority.HIGH
        ))

        await event_bus.publish(Event(
            'suggestion_request',
            {'query': 'TEST'},
            priority=EventPriority.NORMAL
        ))

        # High priority should be processed
        assert 'command_preview_request' in processed_events

    @pytest.mark.asyncio
    async def test_concurrent_event_handling(self, coordinator):
        """Test handling multiple concurrent events."""
        coordinator._process_typing = AsyncMock()
        coordinator._process_preview = AsyncMock()
        coordinator._process_suggestions = AsyncMock()

        # Send multiple events concurrently
        tasks = [
            coordinator.handle_typing(Event('typing_state_changed', {
                'is_typing': True,
                'command': f'SELECT {i}'
            }))
            for i in range(10)
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        # Should handle all events (with debouncing)
        assert coordinator.stats['typing_events'] == 10

    @pytest.mark.asyncio
    async def test_widget_method_missing_graceful(self, coordinator):
        """Test graceful handling when widget method is missing."""
        # Remove method from mock
        coordinator.command_preview = Mock(spec=[])  # No methods

        data = {'command': 'SELECT *'}

        # Should not raise
        await coordinator._process_preview(data)

    @pytest.mark.asyncio
    async def test_empty_query_skipped(self, coordinator, mock_suggestion_list):
        """Test empty query is skipped for suggestions."""
        data = {'query': '', 'context': {}}

        await coordinator._process_suggestions(data)

        mock_suggestion_list.search_suggestions.assert_not_called()

    @pytest.mark.asyncio
    async def test_none_widget_handled(self, coordinator):
        """Test None widget doesn't cause errors."""
        coordinator.command_preview = None
        coordinator.suggestion_list = None

        # Should not raise
        await coordinator._process_preview({'command': 'TEST'})
        await coordinator._process_suggestions({'query': 'TEST', 'context': {}})

    @pytest.mark.asyncio
    async def test_event_statistics_accuracy(self, coordinator):
        """Test event statistics are accurately tracked."""
        event = Event('typing_state_changed', {
            'is_typing': True,
            'command': 'SELECT *'
        })

        # Process multiple events
        for _ in range(5):
            await coordinator.handle_typing(event)
            await asyncio.sleep(0.05)

        assert coordinator.stats['typing_events'] == 5

    @pytest.mark.asyncio
    async def test_debounce_timing_accuracy(self, coordinator):
        """Test debounce timing is accurate."""
        coordinator._process_preview = AsyncMock()

        event = Event('command_preview_request', {'command': 'SELECT *'})

        start = asyncio.get_event_loop().time()

        # Trigger event
        await coordinator.handle_preview_request(event)

        duration = asyncio.get_event_loop().time() - start

        # Should complete within reasonable time (debounce + processing)
        assert duration < 1.0
