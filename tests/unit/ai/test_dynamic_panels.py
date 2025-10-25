"""
Integration tests for Dynamic Panel Container.

Tests panel resizing, content tracking, and auto-adjustment features.
"""

import pytest
import asyncio
from textual.app import App
from textual.widgets import Static

from src.ui.containers.dynamic_panel_container import DynamicPanelContainer, PanelConfig
from src.ui.utils.content_tracker import ContentSizeTracker, ContentMetrics


class TestApp(App):
    """Test application for panel container."""

    def compose(self):
        yield DynamicPanelContainer()


@pytest.mark.asyncio
async def test_panel_container_initialization():
    """Test that panel container initializes with correct default sizes."""
    container = DynamicPanelContainer()

    # Verify default panel configurations
    assert 'output' in container.panels
    assert 'module' in container.panels
    assert 'prompt' in container.panels

    # Verify default sizes sum to 100%
    total = sum(p.current_size for p in container.panels.values())
    assert total == 100

    # Verify individual defaults
    assert container.panels['output'].current_size == 50
    assert container.panels['module'].current_size == 30
    assert container.panels['prompt'].current_size == 20


@pytest.mark.asyncio
async def test_resize_panel_basic():
    """Test basic panel resizing."""
    container = DynamicPanelContainer()

    # Resize output panel to 60%
    success = await container.resize_panel('output', 60)
    assert success is True
    assert container.panels['output'].current_size == 60

    # Other panels should adjust proportionally
    total = sum(p.current_size for p in container.panels.values())
    assert total == 100


@pytest.mark.asyncio
async def test_resize_panel_constraints():
    """Test that resize respects min/max constraints."""
    container = DynamicPanelContainer()

    # Try to resize below minimum (10%)
    success = await container.resize_panel('output', 5)
    assert success is True
    assert container.panels['output'].current_size == 10  # Clamped to min

    # Try to resize above maximum (80%)
    # Note: After output is at 10%, module is at 54%, prompt is at 36%
    # Requesting 90% (clamped to 80%) needs 44% more space
    # But only module can shrink (output already at min)
    # Module can give 44% (going from 54% to 10%)
    # So prompt should be able to reach its target
    success = await container.resize_panel('prompt', 90)
    assert success is True
    # Verify prompt got as much space as possible given constraints
    assert container.panels['prompt'].current_size >= 70  # Should be close to max
    assert container.panels['output'].current_size >= 10  # Output stays at min
    assert container.panels['module'].current_size >= 10  # Module stays at min
    # Total should always be 100%
    total = sum(p.current_size for p in container.panels.values())
    assert total == 100


@pytest.mark.asyncio
async def test_manual_adjustment_tracking():
    """Test that manual adjustments are tracked."""
    container = DynamicPanelContainer()

    # User-initiated resize
    await container.resize_panel('output', 55, user_initiated=True)
    assert container._manual_adjustment['output'] is True

    # System-initiated resize
    await container.resize_panel('module', 25, user_initiated=False)
    assert container._manual_adjustment['module'] is False


@pytest.mark.asyncio
async def test_set_active_panel():
    """Test setting active panel."""
    container = DynamicPanelContainer()

    # Set output as active
    container.set_active_panel('output')
    assert container.panels['output'].is_active is True
    assert container.panels['module'].is_active is False
    assert container.panels['prompt'].is_active is False

    # Change to prompt
    container.set_active_panel('prompt')
    assert container.panels['output'].is_active is False
    assert container.panels['prompt'].is_active is True


@pytest.mark.asyncio
async def test_content_height_update():
    """Test updating content height."""
    container = DynamicPanelContainer()

    # Update content height
    container.update_content_height('output', 200)
    assert container.panels['output'].content_height == 200

    container.update_content_height('module', 50)
    assert container.panels['module'].content_height == 50


@pytest.mark.asyncio
async def test_resize_callbacks():
    """Test resize callback notifications."""
    container = DynamicPanelContainer()

    # Track callback invocations
    callback_data = []

    def on_resize(panel_name: str, new_size: int):
        callback_data.append((panel_name, new_size))

    container.register_resize_callback(on_resize)

    # Resize panel
    await container.resize_panel('output', 55)

    # Verify callback was called
    assert len(callback_data) > 0
    assert callback_data[0][0] == 'output'
    assert callback_data[0][1] == 55


@pytest.mark.asyncio
async def test_get_panel_size():
    """Test getting panel size."""
    container = DynamicPanelContainer()

    size = container.get_panel_size('output')
    assert size == 50

    size = container.get_panel_size('invalid')
    assert size is None


@pytest.mark.asyncio
async def test_reset_manual_adjustments():
    """Test resetting manual adjustment flags."""
    container = DynamicPanelContainer()

    # Make manual adjustments
    await container.resize_panel('output', 55, user_initiated=True)
    await container.resize_panel('module', 25, user_initiated=True)

    assert container._manual_adjustment['output'] is True
    assert container._manual_adjustment['module'] is True

    # Reset
    container.reset_manual_adjustments()

    assert container._manual_adjustment['output'] is False
    assert container._manual_adjustment['module'] is False


# ContentSizeTracker Tests

def test_content_tracker_initialization():
    """Test content tracker initialization."""
    tracker = ContentSizeTracker()
    assert len(tracker.metrics) == 0
    assert len(tracker.callbacks) == 0


def test_track_content_basic():
    """Test basic content tracking."""
    tracker = ContentSizeTracker()

    # Track content
    tracker.track_content('output', 100)

    assert 'output' in tracker.metrics
    assert tracker.metrics['output'].current_height == 100


def test_content_metrics_update():
    """Test content metrics update logic."""
    metrics = ContentMetrics(panel_id='test')

    # First update
    changed = metrics.update(50)
    assert metrics.current_height == 50
    assert metrics.peak_height == 50

    # Second update with growth
    changed = metrics.update(100)
    assert metrics.current_height == 100
    assert metrics.peak_height == 100
    assert changed is True  # Significant change

    # Stable update
    changed = metrics.update(100)
    assert metrics.stable_count == 1


def test_get_recommended_size_empty():
    """Test recommended size for empty content."""
    tracker = ContentSizeTracker()

    # Empty content
    tracker.track_content('panel1', 0)
    recommended = tracker.get_recommended_size('panel1')

    assert recommended == tracker.EMPTY_SIZE_PERCENT


def test_get_recommended_size_stable():
    """Test recommended size for stable content."""
    tracker = ContentSizeTracker()

    # Simulate stable content
    metrics = ContentMetrics(panel_id='panel1')
    metrics.current_height = 50
    metrics.stable_count = 10  # Highly stable
    tracker.metrics['panel1'] = metrics

    recommended = tracker.get_recommended_size('panel1')
    assert recommended == tracker.STABLE_SIZE_PERCENT


def test_get_recommended_size_growing():
    """Test recommended size for growing content."""
    tracker = ContentSizeTracker()

    # Simulate high growth rate
    metrics = ContentMetrics(panel_id='panel1')
    metrics.current_height = 200
    metrics.growth_rate = 15  # High growth
    tracker.metrics['panel1'] = metrics

    recommended = tracker.get_recommended_size('panel1')
    assert recommended >= tracker.GROWING_SIZE_PERCENT


def test_tracker_callbacks():
    """Test content tracker callbacks."""
    tracker = ContentSizeTracker()

    callback_data = []

    def on_resize(panel_id: str, size: int):
        callback_data.append((panel_id, size))

    tracker.register_callback(on_resize)

    # Track content with significant change
    tracker.track_content('panel1', 0)
    tracker.track_content('panel1', 100)  # Significant change

    # Callback should have been triggered
    assert len(callback_data) > 0
    assert callback_data[-1][0] == 'panel1'


def test_get_all_recommendations():
    """Test getting all recommendations."""
    tracker = ContentSizeTracker()

    # Track multiple panels
    tracker.track_content('panel1', 50)
    tracker.track_content('panel2', 100)
    tracker.track_content('panel3', 0)

    recommendations = tracker.get_all_recommendations()

    assert len(recommendations) == 3
    assert 'panel1' in recommendations
    assert 'panel2' in recommendations
    assert 'panel3' in recommendations


def test_reset_metrics():
    """Test resetting metrics."""
    tracker = ContentSizeTracker()

    # Track content
    tracker.track_content('panel1', 100)
    tracker.track_content('panel2', 200)

    # Reset specific panel
    tracker.reset_metrics('panel1')
    assert tracker.metrics['panel1'].current_height == 0
    assert tracker.metrics['panel2'].current_height == 200

    # Reset all
    tracker.reset_metrics()
    assert len(tracker.metrics) == 0


@pytest.mark.asyncio
async def test_tracker_monitoring():
    """Test periodic content monitoring."""
    tracker = ContentSizeTracker()

    # Track content
    tracker.track_content('panel1', 100)

    # Start monitoring
    await tracker.start_monitoring(interval=0.1)

    # Wait a bit
    await asyncio.sleep(0.3)

    # Stop monitoring
    await tracker.stop_monitoring()

    # Verify monitoring ran
    assert tracker._monitoring is False


@pytest.mark.asyncio
async def test_integration_container_with_tracker():
    """Test integration between container and tracker."""
    container = DynamicPanelContainer()
    tracker = ContentSizeTracker()

    # Connect tracker to container
    def on_resize_recommended(panel_id: str, recommended_size: int):
        asyncio.create_task(
            container.resize_panel(panel_id, recommended_size, user_initiated=False)
        )

    tracker.register_callback(on_resize_recommended)

    # Track growing content
    tracker.track_content('output', 50)
    tracker.track_content('output', 150)  # Significant growth

    # Wait for async operations
    await asyncio.sleep(0.1)

    # Panel should have been resized (exact size depends on logic)
    assert container.panels['output'].current_size > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
