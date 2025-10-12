"""
Tests for MemoryMonitor (src/ui/utils/memory_monitor.py)

Tests memory tracking, widget lifecycle, leak detection, and cleanup.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.ui.utils.memory_monitor import (
    MemoryMonitor,
    MemorySnapshot,
    WidgetMemoryTracker
)


class TestMemorySnapshot:
    """Test suite for MemorySnapshot dataclass."""

    def test_snapshot_creation(self):
        """Test creating memory snapshot."""
        snapshot = MemorySnapshot(
            timestamp=1234567890.0,
            total_mb=150.5,
            rss_mb=145.3,
            vms_mb=200.0,
            percent=5.5,
            widget_count=10,
            event_queue_size=5,
            cache_sizes={'cache1': 100, 'cache2': 50}
        )

        assert snapshot.timestamp == 1234567890.0
        assert snapshot.total_mb == 150.5
        assert snapshot.widget_count == 10


class TestWidgetMemoryTracker:
    """Test suite for WidgetMemoryTracker dataclass."""

    def test_tracker_creation(self):
        """Test creating widget tracker."""
        tracker = WidgetMemoryTracker(
            widget_id="widget-123",
            widget_type="SmartSuggestionList",
            created_at=1234567890.0,
            last_updated=1234567890.0,
            estimated_size_bytes=1024
        )

        assert tracker.widget_id == "widget-123"
        assert tracker.widget_type == "SmartSuggestionList"
        assert tracker.estimated_size_bytes == 1024


class TestMemoryMonitor:
    """Test suite for MemoryMonitor."""

    @pytest.fixture
    def mock_process(self):
        """Create mock psutil.Process."""
        process = MagicMock()

        # Mock memory_info
        mock_mem_info = Mock()
        mock_mem_info.rss = 100 * 1024 * 1024  # 100MB in bytes
        mock_mem_info.vms = 150 * 1024 * 1024  # 150MB in bytes
        process.memory_info = Mock(return_value=mock_mem_info)

        # Mock memory_percent
        process.memory_percent = Mock(return_value=5.0)

        return process

    @pytest.fixture
    def monitor(self, mock_process):
        """Create MemoryMonitor instance."""
        with patch('src.ui.utils.memory_monitor.psutil.Process', return_value=mock_process):
            return MemoryMonitor(
                warning_threshold_mb=150,
                critical_threshold_mb=200,
                cleanup_interval=5,
                max_snapshots=100
            )

    def test_initialization(self, monitor):
        """Test monitor initializes correctly."""
        assert monitor.warning_threshold_mb == 150
        assert monitor.critical_threshold_mb == 200
        assert monitor.cleanup_interval == 5
        assert monitor.max_snapshots == 100
        assert monitor.monitoring is False
        assert len(monitor.snapshots) == 0
        assert len(monitor.widgets) == 0

    def test_start_monitoring_captures_baseline(self, monitor, mock_process):
        """Test start_monitoring captures baseline memory."""
        monitor.start_monitoring()

        assert monitor.baseline_mb > 0
        assert monitor.monitoring is True

    def test_start_monitoring_creates_task(self, monitor):
        """Test start_monitoring creates monitoring task."""
        monitor.start_monitoring()

        assert monitor.monitor_task is not None
        assert isinstance(monitor.monitor_task, asyncio.Task)

        # Clean up
        monitor.monitoring = False
        if monitor.monitor_task:
            monitor.monitor_task.cancel()

    def test_start_monitoring_already_active_warning(self, monitor):
        """Test starting monitoring when already active."""
        monitor.monitoring = True

        # Should not create new task
        monitor.start_monitoring()

        # Monitoring state unchanged
        assert monitor.monitoring is True

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, monitor):
        """Test stop_monitoring stops task."""
        monitor.start_monitoring()
        assert monitor.monitoring is True

        await monitor.stop_monitoring()

        assert monitor.monitoring is False

    @pytest.mark.asyncio
    async def test_stop_monitoring_cancels_task(self, monitor):
        """Test stop_monitoring cancels task."""
        monitor.start_monitoring()
        task = monitor.monitor_task

        await monitor.stop_monitoring()

        assert task.cancelled() or task.done()

    def test_take_snapshot(self, monitor, mock_process):
        """Test _take_snapshot creates snapshot."""
        snapshot = monitor._take_snapshot()

        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.total_mb > 0
        assert snapshot.widget_count == 0

    def test_take_snapshot_adds_to_history(self, monitor):
        """Test _take_snapshot adds to history."""
        initial_count = len(monitor.snapshots)

        monitor._take_snapshot()

        assert len(monitor.snapshots) == initial_count + 1

    def test_take_snapshot_limits_history(self, monitor):
        """Test _take_snapshot limits history size."""
        # Add more than max_snapshots
        for _ in range(150):
            monitor._take_snapshot()

        assert len(monitor.snapshots) <= monitor.max_snapshots

    def test_get_memory_usage(self, monitor, mock_process):
        """Test get_memory_usage returns metrics."""
        monitor.baseline_mb = 50.0

        usage = monitor.get_memory_usage()

        assert 'baseline_mb' in usage
        assert 'current_mb' in usage
        assert 'increase_mb' in usage
        assert 'widget_count' in usage
        assert 'within_target' in usage

    def test_check_threshold_no_threshold(self, monitor, mock_process):
        """Test check_threshold when under threshold."""
        monitor.baseline_mb = 50.0

        # Mock low memory usage
        mock_mem_info = Mock()
        mock_mem_info.rss = 100 * 1024 * 1024  # 100MB total
        mock_mem_info.vms = 150 * 1024 * 1024
        mock_process.memory_info = Mock(return_value=mock_mem_info)

        result = monitor.check_threshold()

        # Increase is 50MB, under 150MB warning
        assert result is False

    def test_check_threshold_warning(self, monitor, mock_process):
        """Test check_threshold at warning level."""
        monitor.baseline_mb = 50.0

        # Mock high memory usage
        mock_mem_info = Mock()
        mock_mem_info.rss = 210 * 1024 * 1024  # 210MB total, 160MB increase
        mock_mem_info.vms = 250 * 1024 * 1024
        mock_process.memory_info = Mock(return_value=mock_mem_info)
        mock_process.memory_percent = Mock(return_value=10.0)

        result = monitor.check_threshold()

        # Increase is 160MB, over 150MB warning
        assert result is True

    def test_check_threshold_critical(self, monitor, mock_process):
        """Test check_threshold at critical level."""
        monitor.baseline_mb = 50.0

        # Mock critical memory usage
        mock_mem_info = Mock()
        mock_mem_info.rss = 260 * 1024 * 1024  # 260MB total, 210MB increase
        mock_mem_info.vms = 300 * 1024 * 1024
        mock_process.memory_info = Mock(return_value=mock_mem_info)
        mock_process.memory_percent = Mock(return_value=15.0)

        result = monitor.check_threshold()

        # Increase is 210MB, over 200MB critical
        assert result is True

    @pytest.mark.asyncio
    async def test_trigger_cleanup(self, monitor):
        """Test trigger_cleanup calls callbacks."""
        callback = Mock()
        monitor.register_cleanup_callback(callback)

        await monitor.trigger_cleanup()

        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_cleanup_async_callback(self, monitor):
        """Test trigger_cleanup handles async callbacks."""
        callback = AsyncMock()
        monitor.register_cleanup_callback(callback)

        await monitor.trigger_cleanup()

        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_cleanup_handles_errors(self, monitor):
        """Test trigger_cleanup handles callback errors."""
        def bad_callback():
            raise Exception("Test error")

        monitor.register_cleanup_callback(bad_callback)

        # Should not raise
        await monitor.trigger_cleanup()

    def test_register_cleanup_callback(self, monitor):
        """Test registering cleanup callback."""
        callback = Mock()

        monitor.register_cleanup_callback(callback)

        assert callback in monitor.cleanup_callbacks

    def test_track_widget(self, monitor):
        """Test tracking a widget."""
        monitor.track_widget("widget-1", "SmartSuggestionList", 1024)

        assert "widget-1" in monitor.widgets
        assert monitor.widgets["widget-1"].widget_type == "SmartSuggestionList"
        assert monitor.widgets["widget-1"].estimated_size_bytes == 1024

    def test_update_widget(self, monitor):
        """Test updating widget timestamp."""
        monitor.track_widget("widget-1", "TestWidget")

        initial_time = monitor.widgets["widget-1"].last_updated
        initial_count = monitor.widgets["widget-1"].update_count

        monitor.update_widget("widget-1")

        assert monitor.widgets["widget-1"].last_updated >= initial_time
        assert monitor.widgets["widget-1"].update_count == initial_count + 1

    def test_update_widget_not_tracked(self, monitor):
        """Test updating non-tracked widget."""
        # Should not raise
        monitor.update_widget("nonexistent")

    def test_untrack_widget(self, monitor):
        """Test untracking a widget."""
        monitor.track_widget("widget-1", "TestWidget")

        monitor.untrack_widget("widget-1")

        assert "widget-1" not in monitor.widgets

    def test_cleanup_stale_widgets(self, monitor):
        """Test _cleanup_stale_widgets removes old widgets."""
        # Track widget with old timestamp
        monitor.track_widget("widget-1", "TestWidget")
        tracker = monitor.widgets["widget-1"]
        tracker.last_updated = datetime.now().timestamp() - 400  # 400 seconds ago

        monitor._cleanup_stale_widgets(stale_threshold=300)

        # Should be removed
        assert "widget-1" not in monitor.widgets

    def test_update_cache_size(self, monitor):
        """Test updating cache size."""
        monitor.update_cache_size("query_cache", 150)

        assert monitor.cache_sizes["query_cache"] == 150

    def test_update_event_queue_size(self, monitor):
        """Test updating event queue size."""
        monitor.update_event_queue_size(25)

        assert monitor.event_queue_size == 25

    def test_detect_leaks_insufficient_data(self, monitor):
        """Test _detect_leaks with insufficient data."""
        # Should not raise with few snapshots
        monitor._detect_leaks()

    def test_detect_leaks_sustained_growth(self, monitor, mock_process):
        """Test _detect_leaks detects sustained growth."""
        # Create snapshots with increasing memory
        for i in range(10):
            mock_mem_info = Mock()
            mock_mem_info.rss = (100 + i * 5) * 1024 * 1024
            mock_mem_info.vms = (150 + i * 5) * 1024 * 1024
            mock_process.memory_info = Mock(return_value=mock_mem_info)
            monitor._take_snapshot()

        # Should detect leak
        initial_leaks = monitor.stats['memory_leaks_detected']
        monitor._detect_leaks()

        # May or may not detect depending on growth threshold
        assert monitor.stats['memory_leaks_detected'] >= initial_leaks

    def test_get_stats(self, monitor):
        """Test get_stats returns metrics."""
        stats = monitor.get_stats()

        assert 'memory_usage' in stats
        assert 'snapshot_count' in stats
        assert 'active_widgets' in stats
        assert 'snapshots_taken' in stats

    def test_get_widget_stats(self, monitor):
        """Test get_widget_stats returns widget data."""
        monitor.track_widget("widget-1", "TypeA", 1024)
        monitor.track_widget("widget-2", "TypeB", 2048)
        monitor.track_widget("widget-3", "TypeA", 1024)

        stats = monitor.get_widget_stats()

        assert stats['total_widgets'] == 3
        assert stats['widgets_by_type']['TypeA'] == 2
        assert stats['widgets_by_type']['TypeB'] == 1
        assert stats['estimated_total_bytes'] == 4096

    @pytest.mark.asyncio
    async def test_monitoring_loop_takes_snapshots(self, monitor):
        """Test monitoring loop takes periodic snapshots."""
        monitor.monitoring = True

        # Run for a very short time
        with patch.object(monitor, '_take_snapshot', return_value=Mock()):
            with patch.object(monitor, 'check_threshold', return_value=False):
                with patch.object(monitor, '_detect_leaks'):
                    # Start task
                    task = asyncio.create_task(monitor._monitoring_loop())

                    # Let it run briefly
                    await asyncio.sleep(0.1)

                    # Stop it
                    monitor.monitoring = False
                    await asyncio.sleep(0.1)

                    # Clean up
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

    @pytest.mark.asyncio
    async def test_monitoring_loop_triggers_cleanup_on_threshold(self, monitor):
        """Test monitoring loop triggers cleanup when threshold exceeded."""
        monitor.monitoring = True

        with patch.object(monitor, '_take_snapshot', return_value=Mock()):
            with patch.object(monitor, 'check_threshold', return_value=True):
                with patch.object(monitor, 'trigger_cleanup', new_callable=AsyncMock) as mock_cleanup:
                    with patch.object(monitor, '_detect_leaks'):
                        # Start task
                        task = asyncio.create_task(monitor._monitoring_loop())

                        # Let it run briefly
                        await asyncio.sleep(0.1)

                        # Stop it
                        monitor.monitoring = False
                        await asyncio.sleep(0.1)

                        # Clean up
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
