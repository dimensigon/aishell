"""
Tests for ContentSizeTracker (src/ui/utils/content_tracker.py)

Tests content tracking, size recommendations, callbacks, and monitoring.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import time

from src.ui.utils.content_tracker import (
    ContentSizeTracker,
    ContentMetrics
)


class TestContentMetrics:
    """Test suite for ContentMetrics dataclass."""

    def test_metrics_creation(self):
        """Test creating content metrics."""
        metrics = ContentMetrics(
            panel_id="output",
            current_height=150,
            previous_height=100,
            peak_height=200,
            last_update=1234567890.0,
            growth_rate=5.0,
            stable_count=3
        )

        assert metrics.panel_id == "output"
        assert metrics.current_height == 150
        assert metrics.growth_rate == 5.0

    def test_metrics_defaults(self):
        """Test metrics default values."""
        metrics = ContentMetrics(panel_id="output")

        assert metrics.current_height == 0
        assert metrics.previous_height == 0
        assert metrics.peak_height == 0
        assert metrics.growth_rate == 0.0
        assert metrics.stable_count == 0

    def test_update_calculates_growth_rate(self):
        """Test update calculates growth rate."""
        metrics = ContentMetrics(panel_id="output")

        # First update
        changed = metrics.update(50)

        assert metrics.current_height == 50
        assert changed is True

    def test_update_detects_stable_content(self):
        """Test update detects stable content."""
        metrics = ContentMetrics(panel_id="output")

        # Multiple updates with same height
        for _ in range(6):
            metrics.update(50)
            time.sleep(0.01)

        # Should detect stability
        assert metrics.stable_count >= 5

    def test_update_updates_peak_height(self):
        """Test update tracks peak height."""
        metrics = ContentMetrics(panel_id="output")

        metrics.update(50)
        metrics.update(100)
        metrics.update(75)  # Decrease

        assert metrics.peak_height == 100

    def test_update_significant_change_threshold(self):
        """Test update detects significant changes."""
        metrics = ContentMetrics(panel_id="output")

        # Small change (< 10%)
        metrics.update(50)
        changed = metrics.update(52)

        # Should not be significant
        assert changed is False

        # Large change
        changed = metrics.update(70)

        # Should be significant
        assert changed is True


class TestContentSizeTracker:
    """Test suite for ContentSizeTracker."""

    @pytest.fixture
    def tracker(self):
        """Create ContentSizeTracker instance."""
        return ContentSizeTracker()

    def test_initialization(self, tracker):
        """Test tracker initializes correctly."""
        assert tracker.metrics == {}
        assert tracker.callbacks == []
        assert tracker._monitoring is False

    def test_track_content_creates_metrics(self, tracker):
        """Test track_content creates metrics for new panel."""
        tracker.track_content("output", 150)

        assert "output" in tracker.metrics
        assert tracker.metrics["output"].current_height == 150

    def test_track_content_updates_existing(self, tracker):
        """Test track_content updates existing metrics."""
        tracker.track_content("output", 100)
        tracker.track_content("output", 150)

        assert tracker.metrics["output"].current_height == 150

    def test_track_content_triggers_callbacks(self, tracker):
        """Test track_content triggers callbacks on significant change."""
        callback = Mock()
        tracker.register_callback(callback)

        # First update
        tracker.track_content("output", 100)
        # Large change
        tracker.track_content("output", 200)

        # Should have triggered callback
        assert callback.call_count >= 1

    def test_get_recommended_size_empty_content(self, tracker):
        """Test recommendation for empty content."""
        size = tracker.get_recommended_size("nonexistent")

        assert size == tracker.EMPTY_SIZE_PERCENT

    def test_get_recommended_size_zero_height(self, tracker):
        """Test recommendation for zero height."""
        tracker.track_content("output", 0)

        size = tracker.get_recommended_size("output")

        assert size == tracker.EMPTY_SIZE_PERCENT

    def test_get_recommended_size_high_growth(self, tracker):
        """Test recommendation for high growth rate."""
        tracker.track_content("output", 100)

        # Simulate high growth
        metrics = tracker.metrics["output"]
        metrics.growth_rate = 15.0  # > HIGH_GROWTH_RATE (10)

        size = tracker.get_recommended_size("output")

        assert size >= tracker.GROWING_SIZE_PERCENT

    def test_get_recommended_size_stable_content(self, tracker):
        """Test recommendation for stable content."""
        # Add multiple updates with same size
        for _ in range(10):
            tracker.track_content("output", 100)
            time.sleep(0.01)

        size = tracker.get_recommended_size("output")

        # Should recommend stable size
        assert size >= tracker.STABLE_SIZE_PERCENT

    def test_get_recommended_size_small_content(self, tracker):
        """Test recommendation for small content."""
        tracker.track_content("output", 20)  # ~40 lines visible

        size = tracker.get_recommended_size("output")

        # Should be small size
        assert size <= tracker.STABLE_SIZE_PERCENT

    def test_get_recommended_size_large_content(self, tracker):
        """Test recommendation for large content."""
        tracker.track_content("output", 200)  # Much larger than visible

        size = tracker.get_recommended_size("output")

        # Should be larger size
        assert size >= tracker.GROWING_SIZE_PERCENT

    def test_get_recommended_size_bounded(self, tracker):
        """Test recommendation is within bounds."""
        # Try with extreme values
        tracker.track_content("output", 1000)

        size = tracker.get_recommended_size("output")

        assert tracker.MIN_SIZE_PERCENT <= size <= tracker.MAX_SIZE_PERCENT

    def test_register_callback(self, tracker):
        """Test registering callback."""
        callback = Mock()

        tracker.register_callback(callback)

        assert callback in tracker.callbacks

    def test_register_callback_no_duplicates(self, tracker):
        """Test callback not registered twice."""
        callback = Mock()

        tracker.register_callback(callback)
        tracker.register_callback(callback)

        # Should only be registered once
        count = tracker.callbacks.count(callback)
        assert count == 1

    def test_unregister_callback(self, tracker):
        """Test unregistering callback."""
        callback = Mock()
        tracker.register_callback(callback)

        tracker.unregister_callback(callback)

        assert callback not in tracker.callbacks

    def test_callback_notification(self, tracker):
        """Test _notify_callbacks calls all callbacks."""
        callback1 = Mock()
        callback2 = Mock()

        tracker.register_callback(callback1)
        tracker.register_callback(callback2)

        tracker._notify_callbacks("output", 50)

        callback1.assert_called_once_with("output", 50)
        callback2.assert_called_once_with("output", 50)

    def test_callback_errors_ignored(self, tracker):
        """Test callback errors don't break tracking."""
        def bad_callback(panel_id, size):
            raise Exception("Test error")

        good_callback = Mock()

        tracker.register_callback(bad_callback)
        tracker.register_callback(good_callback)

        # Should not raise
        tracker._notify_callbacks("output", 50)

        # Good callback should still be called
        good_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_monitoring(self, tracker):
        """Test start_monitoring creates task."""
        await tracker.start_monitoring(interval=0.1)

        assert tracker._monitoring is True
        assert tracker._monitor_task is not None

        # Clean up
        await tracker.stop_monitoring()

    @pytest.mark.asyncio
    async def test_start_monitoring_already_started(self, tracker):
        """Test start_monitoring when already monitoring."""
        await tracker.start_monitoring()

        # Start again
        await tracker.start_monitoring()

        # Should still be monitoring
        assert tracker._monitoring is True

        await tracker.stop_monitoring()

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, tracker):
        """Test stop_monitoring stops task."""
        await tracker.start_monitoring(interval=0.1)

        await tracker.stop_monitoring()

        assert tracker._monitoring is False

    @pytest.mark.asyncio
    async def test_monitor_loop_checks_stability(self, tracker):
        """Test monitor loop checks content stability."""
        tracker.track_content("output", 100)

        await tracker.start_monitoring(interval=0.05)

        # Let it run briefly
        await asyncio.sleep(0.15)

        await tracker.stop_monitoring()

        # Should have checked stability
        # (We can't easily verify internals, but ensure no errors)

    def test_get_metrics(self, tracker):
        """Test get_metrics returns metrics."""
        tracker.track_content("output", 150)

        metrics = tracker.get_metrics("output")

        assert metrics is not None
        assert isinstance(metrics, ContentMetrics)
        assert metrics.current_height == 150

    def test_get_metrics_nonexistent(self, tracker):
        """Test get_metrics for nonexistent panel."""
        metrics = tracker.get_metrics("nonexistent")

        assert metrics is None

    def test_reset_metrics_specific(self, tracker):
        """Test reset_metrics for specific panel."""
        tracker.track_content("output", 150)
        tracker.track_content("module", 100)

        tracker.reset_metrics("output")

        # Output should be reset
        assert tracker.metrics["output"].current_height == 0
        # Module should be unchanged
        assert tracker.metrics["module"].current_height == 100

    def test_reset_metrics_all(self, tracker):
        """Test reset_metrics for all panels."""
        tracker.track_content("output", 150)
        tracker.track_content("module", 100)

        tracker.reset_metrics()

        # All should be cleared
        assert len(tracker.metrics) == 0

    def test_get_all_recommendations(self, tracker):
        """Test get_all_recommendations returns dict."""
        tracker.track_content("output", 150)
        tracker.track_content("module", 50)
        tracker.track_content("prompt", 20)

        recommendations = tracker.get_all_recommendations()

        assert isinstance(recommendations, dict)
        assert "output" in recommendations
        assert "module" in recommendations
        assert "prompt" in recommendations

    def test_get_all_recommendations_empty(self, tracker):
        """Test get_all_recommendations with no panels."""
        recommendations = tracker.get_all_recommendations()

        assert recommendations == {}

    def test_content_ratio_calculation(self, tracker):
        """Test content ratio affects recommendations."""
        # Small content (fits in visible area)
        tracker.track_content("output", 30)
        small_size = tracker.get_recommended_size("output")

        # Reset
        tracker.reset_metrics()

        # Large content (doesn't fit)
        tracker.track_content("output", 150)
        large_size = tracker.get_recommended_size("output")

        # Large content should get larger size
        assert large_size > small_size

    def test_multiple_panels_independent(self, tracker):
        """Test multiple panels track independently."""
        tracker.track_content("output", 150)
        tracker.track_content("module", 50)
        tracker.track_content("prompt", 20)

        output_size = tracker.get_recommended_size("output")
        module_size = tracker.get_recommended_size("module")
        prompt_size = tracker.get_recommended_size("prompt")

        # Sizes should be different
        assert output_size != module_size
        assert module_size != prompt_size

    def test_constants_defined(self):
        """Test size constants are defined."""
        assert hasattr(ContentSizeTracker, 'MIN_SIZE_PERCENT')
        assert hasattr(ContentSizeTracker, 'MAX_SIZE_PERCENT')
        assert hasattr(ContentSizeTracker, 'EMPTY_SIZE_PERCENT')
        assert hasattr(ContentSizeTracker, 'STABLE_SIZE_PERCENT')
        assert hasattr(ContentSizeTracker, 'GROWING_SIZE_PERCENT')
        assert hasattr(ContentSizeTracker, 'HIGH_GROWTH_RATE')
        assert hasattr(ContentSizeTracker, 'STABLE_THRESHOLD')
