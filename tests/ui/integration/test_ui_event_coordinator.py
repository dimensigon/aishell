"""
Tests for UIEventIntegration (src/ui/integration/event_coordinator.py)

Tests event routing, debouncing, priority handling, and widget coordination.
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
    async def event_bus(self):
        """Create AsyncEventBus instance."""
        bus = AsyncEventBus()
        await bus.start()
        yield bus
        await bus.stop()

    @pytest.fixture
    def mock_command_preview(self):
        """Create mock command preview widget."""
        preview = Mock()
        preview.analyze_command = AsyncMock()
        preview.update_analysis = AsyncMock()
        return preview

    @pytest.fixture
    def mock_suggestion_list(self):
        """Create mock suggestion list widget."""
        suggestions = Mock()
        suggestions.search_suggestions = AsyncMock()
        suggestions.update_suggestions = AsyncMock()
        return suggestions

    @pytest.fixture
    def coordinator(self, event_bus, mock_command_preview, mock_suggestion_list):
        """Create UIEventIntegration instance."""
        return UIEventIntegration(
            event_bus=event_bus,
            command_preview=mock_command_preview,
            suggestion_list=mock_suggestion_list
        )

    def test_initialization(self, coordinator, event_bus, mock_command_preview, mock_suggestion_list):
        """Test coordinator initializes correctly."""
        assert coordinator.event_bus == event_bus
        assert coordinator.command_preview == mock_command_preview
        assert coordinator.suggestion_list == mock_suggestion_list
        assert coordinator.typing_debounce == 0.2
        assert coordinator.preview_debounce == 0.3
        assert coordinator.suggestion_debounce == 0.15

    @pytest.mark.asyncio
    async def test_handle_typing_debounces(self, coordinator):
        """Test handle_typing debounces rapid events."""
        event = Event(
            'typing_state_changed',
            {'is_typing': True, 'command': 'SELECT'},
            priority=EventPriority.NORMAL
        )

        # Send multiple events rapidly
        tasks = []
        for _ in range(5):
            tasks.append(asyncio.create_task(coordinator.handle_typing(event)))
            await asyncio.sleep(0.05)  # Small delay

        # Wait for debouncing
        await asyncio.sleep(0.3)

        # Check debounced count increased
        assert coordinator.stats['debounced_events'] > 0

    @pytest.mark.asyncio
    async def test_handle_typing_publishes_preview_request(self, coordinator, event_bus):
        """Test handle_typing publishes preview request."""
        with patch.object(event_bus, 'publish', new_callable=AsyncMock) as mock_publish:
            event = Event(
                'typing_state_changed',
                {'is_typing': True, 'command': 'SELECT * FROM users'},
                priority=EventPriority.NORMAL
            )

            await coordinator.handle_typing(event)
            await asyncio.sleep(0.3)  # Wait for debounce

            # Should have published preview request
            assert mock_publish.call_count >= 1

    @pytest.mark.asyncio
    async def test_handle_typing_publishes_suggestion_request(self, coordinator, event_bus):
        """Test handle_typing publishes suggestion request."""
        with patch.object(event_bus, 'publish', new_callable=AsyncMock) as mock_publish:
            event = Event(
                'typing_state_changed',
                {'is_typing': True, 'command': 'SELECT'},
                priority=EventPriority.NORMAL
            )

            await coordinator.handle_typing(event)
            await asyncio.sleep(0.3)  # Wait for debounce

            # Should publish both preview and suggestion requests
            assert mock_publish.call_count >= 2

    @pytest.mark.asyncio
    async def test_handle_typing_ignores_not_typing(self, coordinator, event_bus):
        """Test handle_typing ignores when not typing."""
        with patch.object(event_bus, 'publish', new_callable=AsyncMock) as mock_publish:
            event = Event(
                'typing_state_changed',
                {'is_typing': False, 'command': ''},
                priority=EventPriority.NORMAL
            )

            await coordinator.handle_typing(event)
            await asyncio.sleep(0.3)

            # Should not publish requests
            mock_publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_preview_request_calls_widget(self, coordinator, mock_command_preview):
        """Test handle_preview_request calls command preview widget."""
        event = Event(
            'command_preview_request',
            {'command': 'SELECT * FROM users'},
            priority=EventPriority.HIGH
        )

        await coordinator.handle_preview_request(event)
        await asyncio.sleep(0.4)  # Wait for debounce

        # Should call widget's analyze_command
        mock_command_preview.analyze_command.assert_called()

    @pytest.mark.asyncio
    async def test_handle_preview_request_debounces(self, coordinator):
        """Test handle_preview_request debounces rapid requests."""
        event = Event(
            'command_preview_request',
            {'command': 'SELECT'},
            priority=EventPriority.HIGH
        )

        # Send multiple events rapidly
        for _ in range(5):
            await coordinator.handle_preview_request(event)
            await asyncio.sleep(0.05)

        await asyncio.sleep(0.4)

        # Check debounced count
        assert coordinator.stats['debounced_events'] > 0

    @pytest.mark.asyncio
    async def test_handle_suggestion_request_calls_widget(self, coordinator, mock_suggestion_list):
        """Test handle_suggestion_request calls suggestion widget."""
        event = Event(
            'suggestion_request',
            {'query': 'SELEC', 'context': {}},
            priority=EventPriority.NORMAL
        )

        await coordinator.handle_suggestion_request(event)
        await asyncio.sleep(0.2)  # Wait for debounce

        # Should call widget's search_suggestions
        mock_suggestion_list.search_suggestions.assert_called()

    @pytest.mark.asyncio
    async def test_handle_suggestion_request_debounces(self, coordinator):
        """Test handle_suggestion_request debounces rapid requests."""
        event = Event(
            'suggestion_request',
            {'query': 'S', 'context': {}},
            priority=EventPriority.NORMAL
        )

        # Send multiple events rapidly
        for _ in range(5):
            await coordinator.handle_suggestion_request(event)
            await asyncio.sleep(0.03)

        await asyncio.sleep(0.2)

        # Check debounced count
        assert coordinator.stats['debounced_events'] > 0

    @pytest.mark.asyncio
    async def test_handle_risk_complete(self, coordinator, mock_command_preview):
        """Test handle_risk_complete processes analysis."""
        event = Event(
            'risk_analysis_complete',
            {
                'analysis': {'risk_level': 'HIGH', 'warnings': ['Danger']},
                'command': 'DROP TABLE users'
            },
            priority=EventPriority.NORMAL
        )

        await coordinator.handle_risk_complete(event)

        # Should update preview widget
        mock_command_preview.update_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_suggestions_ready(self, coordinator, mock_suggestion_list):
        """Test handle_suggestions_ready updates widget."""
        from src.vector.autocomplete import CompletionCandidate

        candidates = [
            CompletionCandidate("SELECT", 0.95, "keyword", {}),
            CompletionCandidate("FROM", 0.90, "keyword", {})
        ]

        event = Event(
            'suggestions_ready',
            {'candidates': candidates},
            priority=EventPriority.NORMAL
        )

        await coordinator.handle_suggestions_ready(event)

        # Should update suggestion list
        mock_suggestion_list.update_suggestions.assert_called_once_with(candidates)

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
        """Test get_stats returns statistics."""
        stats = coordinator.get_stats()

        assert 'typing_events' in stats
        assert 'preview_events' in stats
        assert 'suggestion_events' in stats
        assert 'risk_events' in stats
        assert 'debounced_events' in stats

    @pytest.mark.asyncio
    async def test_shutdown_cancels_tasks(self, coordinator):
        """Test shutdown cancels pending tasks."""
        # Create fake tasks
        coordinator._typing_task = asyncio.create_task(asyncio.sleep(10))
        coordinator._preview_task = asyncio.create_task(asyncio.sleep(10))
        coordinator._suggestion_task = asyncio.create_task(asyncio.sleep(10))

        await coordinator.shutdown()

        # All tasks should be cancelled
        assert coordinator._typing_task.cancelled()
        assert coordinator._preview_task.cancelled()
        assert coordinator._suggestion_task.cancelled()

    @pytest.mark.asyncio
    async def test_process_typing_triggers_both_requests(self, coordinator, event_bus):
        """Test _process_typing triggers preview and suggestions."""
        with patch.object(event_bus, 'publish', new_callable=AsyncMock) as mock_publish:
            data = {'is_typing': True, 'command': 'SELECT * FROM'}

            await coordinator._process_typing(data)

            # Should publish 2 events: preview and suggestion
            assert mock_publish.call_count == 2

    @pytest.mark.asyncio
    async def test_process_preview_calls_widget_method(self, coordinator, mock_command_preview):
        """Test _process_preview calls widget method."""
        data = {'command': 'SELECT * FROM users'}

        await coordinator._process_preview(data)

        # Should call analyze_command
        mock_command_preview.analyze_command.assert_called_once_with('SELECT * FROM users')

    @pytest.mark.asyncio
    async def test_process_preview_handles_missing_widget(self, coordinator):
        """Test _process_preview handles missing widget."""
        coordinator.command_preview = None
        data = {'command': 'SELECT'}

        # Should not raise
        await coordinator._process_preview(data)

    @pytest.mark.asyncio
    async def test_process_suggestions_calls_widget_method(self, coordinator, mock_suggestion_list):
        """Test _process_suggestions calls widget method."""
        data = {'query': 'SELE', 'context': {}}

        await coordinator._process_suggestions(data)

        # Should call search_suggestions
        mock_suggestion_list.search_suggestions.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_suggestions_handles_missing_widget(self, coordinator):
        """Test _process_suggestions handles missing widget."""
        coordinator.suggestion_list = None
        data = {'query': 'SELECT'}

        # Should not raise
        await coordinator._process_suggestions(data)

    @pytest.mark.asyncio
    async def test_event_statistics_increment(self, coordinator):
        """Test event statistics increment correctly."""
        initial_typing = coordinator.stats['typing_events']
        initial_preview = coordinator.stats['preview_events']
        initial_suggestion = coordinator.stats['suggestion_events']

        # Trigger events
        await coordinator.handle_typing(Event('typing_state_changed',
                                              {'is_typing': True, 'command': 'S'},
                                              EventPriority.NORMAL))
        await coordinator.handle_preview_request(Event('command_preview_request',
                                                      {'command': 'S'},
                                                      EventPriority.HIGH))
        await coordinator.handle_suggestion_request(Event('suggestion_request',
                                                         {'query': 'S'},
                                                         EventPriority.NORMAL))

        # Stats should increment
        assert coordinator.stats['typing_events'] > initial_typing
        assert coordinator.stats['preview_events'] > initial_preview
        assert coordinator.stats['suggestion_events'] > initial_suggestion

    @pytest.mark.asyncio
    async def test_debounce_delay_configurable(self, event_bus):
        """Test debounce delays are configurable."""
        coordinator = UIEventIntegration(
            event_bus=event_bus,
            command_preview=Mock(),
            suggestion_list=Mock()
        )

        # Modify delays
        coordinator.typing_debounce = 0.5
        coordinator.preview_debounce = 0.4
        coordinator.suggestion_debounce = 0.3

        assert coordinator.typing_debounce == 0.5
        assert coordinator.preview_debounce == 0.4
        assert coordinator.suggestion_debounce == 0.3

    @pytest.mark.asyncio
    async def test_concurrent_event_handling(self, coordinator):
        """Test handling multiple event types concurrently."""
        typing_event = Event('typing_state_changed',
                           {'is_typing': True, 'command': 'SELECT'},
                           EventPriority.NORMAL)
        preview_event = Event('command_preview_request',
                            {'command': 'SELECT'},
                            EventPriority.HIGH)
        suggestion_event = Event('suggestion_request',
                               {'query': 'SELEC'},
                               EventPriority.NORMAL)

        # Handle all concurrently
        tasks = [
            asyncio.create_task(coordinator.handle_typing(typing_event)),
            asyncio.create_task(coordinator.handle_preview_request(preview_event)),
            asyncio.create_task(coordinator.handle_suggestion_request(suggestion_event))
        ]

        await asyncio.gather(*tasks)

        # All should complete without errors
        assert all(task.done() for task in tasks)

    def test_subscribe_to_events_called(self, coordinator, event_bus):
        """Test _subscribe_to_events subscribes to all events."""
        # Create new coordinator to test subscription
        with patch.object(event_bus, 'subscribe') as mock_subscribe:
            new_coordinator = UIEventIntegration(event_bus)

            # Should subscribe to multiple events
            assert mock_subscribe.call_count >= 5
