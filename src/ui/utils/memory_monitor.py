"""
Memory Monitor for UI Components

Tracks UI memory usage, monitors widget lifecycle, detects memory leaks,
and manages resource cleanup.
"""

import asyncio
import logging
import psutil
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage at a point in time"""
    timestamp: float
    total_mb: float
    rss_mb: float
    vms_mb: float
    percent: float
    widget_count: int
    event_queue_size: int
    cache_sizes: Dict[str, int] = field(default_factory=dict)


@dataclass
class WidgetMemoryTracker:
    """Tracks memory usage for a specific widget"""
    widget_id: str
    widget_type: str
    created_at: float
    last_updated: float
    estimated_size_bytes: int = 0
    update_count: int = 0


class MemoryMonitor:
    """
    Monitors UI memory usage and manages resource cleanup.

    Features:
    - Track overall UI memory usage
    - Monitor individual widget lifecycle
    - Detect memory leaks
    - Automatic resource cleanup
    - Threshold-based alerts

    Target: < 100MB baseline increase for UI
    """

    def __init__(
        self,
        warning_threshold_mb: int = 150,
        critical_threshold_mb: int = 200,
        cleanup_interval: int = 5,
        max_snapshots: int = 100
    ):
        """
        Initialize memory monitor.

        Args:
            warning_threshold_mb: Memory threshold for warnings
            critical_threshold_mb: Memory threshold for forced cleanup
            cleanup_interval: Seconds between cleanup checks
            max_snapshots: Maximum snapshots to retain
        """
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self.cleanup_interval = cleanup_interval
        self.max_snapshots = max_snapshots

        # Process handle for memory tracking
        self.process = psutil.Process()

        # Baseline memory (captured at start)
        self.baseline_mb = 0.0

        # Memory snapshots over time
        self.snapshots: List[MemorySnapshot] = []

        # Widget tracking
        self.widgets: Dict[str, WidgetMemoryTracker] = {}

        # Cache size tracking
        self.cache_sizes: Dict[str, int] = {}

        # Event queue size tracking
        self.event_queue_size = 0

        # Monitoring state
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            'snapshots_taken': 0,
            'warnings_triggered': 0,
            'cleanups_performed': 0,
            'widgets_tracked': 0,
            'widgets_cleaned': 0,
            'memory_leaks_detected': 0
        }

        # Cleanup callbacks
        self.cleanup_callbacks: List[Any] = []

        logger.info(
            f"Memory monitor initialized: "
            f"warning={warning_threshold_mb}MB, "
            f"critical={critical_threshold_mb}MB"
        )

    def start_monitoring(self) -> None:
        """
        Start memory monitoring.

        Captures baseline and begins periodic monitoring.
        """
        if self.monitoring:
            logger.warning("Memory monitoring already active")
            return

        # Capture baseline memory
        mem_info = self.process.memory_info()
        self.baseline_mb = mem_info.rss / 1024 / 1024

        logger.info(f"Memory baseline captured: {self.baseline_mb:.2f} MB")

        # Start monitoring task
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())

        logger.info("Memory monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop memory monitoring"""
        if not self.monitoring:
            logger.warning("Memory monitoring not active")
            return

        self.monitoring = False

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Memory monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """
        Continuous monitoring loop.

        Periodically checks memory usage and triggers cleanup if needed.
        """
        logger.info("Memory monitoring loop started")

        while self.monitoring:
            try:
                # Take memory snapshot
                snapshot = self._take_snapshot()

                # Check thresholds
                if self.check_threshold():
                    await self.trigger_cleanup()

                # Detect memory leaks
                self._detect_leaks()

                # Wait for next check
                await asyncio.sleep(self.cleanup_interval)

            except asyncio.CancelledError:
                logger.info("Memory monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.cleanup_interval)

        logger.info("Memory monitoring loop stopped")

    def _take_snapshot(self) -> MemorySnapshot:
        """
        Take a memory usage snapshot.

        Returns:
            MemorySnapshot with current memory metrics
        """
        mem_info = self.process.memory_info()
        mem_percent = self.process.memory_percent()

        snapshot = MemorySnapshot(
            timestamp=datetime.now().timestamp(),
            total_mb=mem_info.rss / 1024 / 1024,
            rss_mb=mem_info.rss / 1024 / 1024,
            vms_mb=mem_info.vms / 1024 / 1024,
            percent=mem_percent,
            widget_count=len(self.widgets),
            event_queue_size=self.event_queue_size,
            cache_sizes=self.cache_sizes.copy()
        )

        # Add to history
        self.snapshots.append(snapshot)

        # Limit snapshot history
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots:]

        self.stats['snapshots_taken'] += 1

        return snapshot

    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics.

        Returns:
            Dictionary with memory metrics
        """
        mem_info = self.process.memory_info()
        current_mb = mem_info.rss / 1024 / 1024
        increase_mb = current_mb - self.baseline_mb

        return {
            'baseline_mb': self.baseline_mb,
            'current_mb': current_mb,
            'increase_mb': increase_mb,
            'rss_mb': mem_info.rss / 1024 / 1024,
            'vms_mb': mem_info.vms / 1024 / 1024,
            'percent': self.process.memory_percent(),
            'widget_count': len(self.widgets),
            'event_queue_size': self.event_queue_size,
            'cache_sizes': self.cache_sizes.copy(),
            'within_target': increase_mb < 100  # Target: < 100MB increase
        }

    def check_threshold(self) -> bool:
        """
        Check if memory usage exceeds thresholds.

        Returns:
            True if threshold exceeded, False otherwise
        """
        usage = self.get_memory_usage()
        increase_mb = usage['increase_mb']

        if increase_mb >= self.critical_threshold_mb:
            logger.critical(
                f"Memory CRITICAL: {increase_mb:.2f}MB increase "
                f"(threshold: {self.critical_threshold_mb}MB)"
            )
            self.stats['warnings_triggered'] += 1
            return True

        elif increase_mb >= self.warning_threshold_mb:
            logger.warning(
                f"Memory WARNING: {increase_mb:.2f}MB increase "
                f"(threshold: {self.warning_threshold_mb}MB)"
            )
            self.stats['warnings_triggered'] += 1
            return True

        return False

    async def trigger_cleanup(self) -> None:
        """
        Force resource cleanup.

        Calls all registered cleanup callbacks and cleans up stale widgets.
        """
        logger.info("Triggering memory cleanup")

        # Execute cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Cleanup callback error: {e}", exc_info=True)

        # Clean up stale widgets
        self._cleanup_stale_widgets()

        # Trim snapshot history
        if len(self.snapshots) > self.max_snapshots // 2:
            self.snapshots = self.snapshots[-(self.max_snapshots // 2):]

        self.stats['cleanups_performed'] += 1

        # Log cleanup results
        usage = self.get_memory_usage()
        logger.info(
            f"Cleanup complete. Memory: {usage['current_mb']:.2f}MB "
            f"(+{usage['increase_mb']:.2f}MB from baseline)"
        )

    def register_cleanup_callback(self, callback: Any) -> None:
        """
        Register a cleanup callback.

        Args:
            callback: Function to call during cleanup (sync or async)
        """
        self.cleanup_callbacks.append(callback)
        logger.debug(f"Cleanup callback registered: {callback.__name__}")

    def track_widget(
        self,
        widget_id: str,
        widget_type: str,
        estimated_size_bytes: int = 0
    ) -> None:
        """
        Start tracking a widget's memory usage.

        Args:
            widget_id: Unique widget identifier
            widget_type: Type/class name of widget
            estimated_size_bytes: Estimated memory size
        """
        tracker = WidgetMemoryTracker(
            widget_id=widget_id,
            widget_type=widget_type,
            created_at=datetime.now().timestamp(),
            last_updated=datetime.now().timestamp(),
            estimated_size_bytes=estimated_size_bytes
        )

        self.widgets[widget_id] = tracker
        self.stats['widgets_tracked'] += 1

        logger.debug(f"Tracking widget: {widget_id} ({widget_type})")

    def update_widget(self, widget_id: str) -> None:
        """
        Update widget last activity timestamp.

        Args:
            widget_id: Widget identifier
        """
        if widget_id in self.widgets:
            tracker = self.widgets[widget_id]
            tracker.last_updated = datetime.now().timestamp()
            tracker.update_count += 1

    def untrack_widget(self, widget_id: str) -> None:
        """
        Stop tracking a widget.

        Args:
            widget_id: Widget identifier
        """
        if widget_id in self.widgets:
            del self.widgets[widget_id]
            self.stats['widgets_cleaned'] += 1
            logger.debug(f"Untracked widget: {widget_id}")

    def _cleanup_stale_widgets(self, stale_threshold: int = 300) -> None:
        """
        Clean up widgets that haven't been updated recently.

        Args:
            stale_threshold: Seconds before widget considered stale
        """
        current_time = datetime.now().timestamp()
        stale_widgets = []

        for widget_id, tracker in self.widgets.items():
            time_since_update = current_time - tracker.last_updated
            if time_since_update > stale_threshold:
                stale_widgets.append(widget_id)

        for widget_id in stale_widgets:
            logger.debug(f"Cleaning up stale widget: {widget_id}")
            self.untrack_widget(widget_id)

    def update_cache_size(self, cache_name: str, size: int) -> None:
        """
        Update tracked cache size.

        Args:
            cache_name: Name of the cache
            size: Current size (items or bytes)
        """
        self.cache_sizes[cache_name] = size

    def update_event_queue_size(self, size: int) -> None:
        """
        Update event queue size.

        Args:
            size: Current queue size
        """
        self.event_queue_size = size

    def _detect_leaks(self) -> None:
        """
        Detect potential memory leaks.

        Analyzes snapshots for sustained memory growth.
        """
        if len(self.snapshots) < 10:
            return  # Need enough data

        # Get recent snapshots
        recent = self.snapshots[-10:]

        # Check for sustained growth
        growth_count = 0
        for i in range(1, len(recent)):
            if recent[i].total_mb > recent[i-1].total_mb:
                growth_count += 1

        # If memory grew in 80%+ of samples, possible leak
        if growth_count >= 8:
            start_mb = recent[0].total_mb
            end_mb = recent[-1].total_mb
            growth = end_mb - start_mb

            if growth > 10:  # More than 10MB growth
                logger.warning(
                    f"Potential memory leak detected: "
                    f"{growth:.2f}MB growth over {len(recent)} samples"
                )
                self.stats['memory_leaks_detected'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get monitoring statistics.

        Returns:
            Dictionary of monitoring metrics
        """
        return {
            **self.stats,
            'memory_usage': self.get_memory_usage(),
            'snapshot_count': len(self.snapshots),
            'active_widgets': len(self.widgets),
            'tracked_caches': len(self.cache_sizes)
        }

    def get_widget_stats(self) -> Dict[str, Any]:
        """
        Get per-widget statistics.

        Returns:
            Dictionary of widget tracking data
        """
        widget_types = defaultdict(int)
        total_estimated_size = 0

        for tracker in self.widgets.values():
            widget_types[tracker.widget_type] += 1
            total_estimated_size += tracker.estimated_size_bytes

        return {
            'total_widgets': len(self.widgets),
            'widgets_by_type': dict(widget_types),
            'estimated_total_bytes': total_estimated_size,
            'estimated_total_mb': total_estimated_size / 1024 / 1024
        }
