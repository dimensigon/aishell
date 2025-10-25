"""
Content Size Tracker for monitoring panel content changes.

Tracks content size changes in real-time and calculates optimal panel sizes
based on content growth patterns.
"""

import asyncio
from typing import Dict, Callable, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import time


@dataclass
class ContentMetrics:
    """Metrics for tracked content."""
    panel_id: str
    current_height: int = 0
    previous_height: int = 0
    peak_height: int = 0
    last_update: float = field(default_factory=time.time)
    growth_rate: float = 0.0  # Lines per second
    stable_count: int = 0  # Consecutive updates with no change

    def update(self, new_height: int) -> bool:
        """
        Update metrics with new height.

        Returns:
            bool: True if height changed significantly
        """
        now = time.time()
        time_delta = now - self.last_update

        # Update previous height
        self.previous_height = self.current_height
        self.current_height = new_height

        # Update peak
        self.peak_height = max(self.peak_height, new_height)

        # Calculate growth rate
        if time_delta > 0 and new_height != self.previous_height:
            height_delta = new_height - self.previous_height
            self.growth_rate = height_delta / time_delta
            self.stable_count = 0
        else:
            # Content is stable
            self.stable_count += 1
            if self.stable_count > 5:
                self.growth_rate *= 0.9  # Decay growth rate

        self.last_update = now

        # Significant change threshold: 10% or 5 lines
        threshold = max(self.previous_height * 0.1, 5)
        return abs(new_height - self.previous_height) >= threshold


class ContentSizeTracker:
    """
    Real-time content size tracking and optimization.

    Monitors content changes in panels and calculates optimal sizes
    based on content growth patterns and user activity.

    Features:
    - Real-time size tracking
    - Growth rate analysis
    - Stability detection
    - Recommended size calculation
    - Event callbacks

    Usage:
        tracker = ContentSizeTracker()
        tracker.register_callback(on_resize_needed)
        tracker.track_content("output", 150)
        recommended = tracker.get_recommended_size("output")
    """

    # Size recommendation constants
    MIN_SIZE_PERCENT = 10
    MAX_SIZE_PERCENT = 80
    EMPTY_SIZE_PERCENT = 15
    STABLE_SIZE_PERCENT = 30
    GROWING_SIZE_PERCENT = 50

    # Growth thresholds
    HIGH_GROWTH_RATE = 10  # lines/second
    STABLE_THRESHOLD = 5  # updates with no change

    def __init__(self) -> None:
        """Initialize the content size tracker."""
        self.metrics: Dict[str, ContentMetrics] = {}
        self.callbacks: List[Callable[[str, int], None]] = []
        self._monitor_task: Optional[asyncio.Task] = None
        self._monitoring = False

    def track_content(self, panel_id: str, content_height: int) -> None:
        """
        Track content size for a panel.

        Args:
            panel_id: Identifier for the panel
            content_height: Current height in lines
        """
        # Get or create metrics
        if panel_id not in self.metrics:
            self.metrics[panel_id] = ContentMetrics(panel_id=panel_id)

        metrics = self.metrics[panel_id]

        # Update metrics
        changed = metrics.update(content_height)

        # Trigger callbacks if significant change
        if changed:
            recommended = self.get_recommended_size(panel_id)
            self._notify_callbacks(panel_id, recommended)

    def get_recommended_size(self, panel_id: str) -> int:
        """
        Calculate recommended size for a panel.

        Args:
            panel_id: Identifier for the panel

        Returns:
            int: Recommended size as percentage (10-80)
        """
        if panel_id not in self.metrics:
            return self.EMPTY_SIZE_PERCENT

        metrics = self.metrics[panel_id]

        # Empty content → minimum size
        if metrics.current_height == 0:
            return self.EMPTY_SIZE_PERCENT

        # High growth rate → expand
        if metrics.growth_rate > self.HIGH_GROWTH_RATE:
            return min(self.GROWING_SIZE_PERCENT, self.MAX_SIZE_PERCENT)

        # Stable content → maintain
        if metrics.stable_count >= self.STABLE_THRESHOLD:
            return self.STABLE_SIZE_PERCENT

        # Calculate based on content ratio
        # Assume ~40 lines visible in typical panel
        visible_lines = 40
        content_ratio = metrics.current_height / visible_lines

        # Map ratio to percentage
        if content_ratio <= 1.0:
            # Content fits → small size
            recommended = self.EMPTY_SIZE_PERCENT + int(content_ratio * 15)
        elif content_ratio <= 3.0:
            # Moderate content → medium size
            recommended = self.STABLE_SIZE_PERCENT + int((content_ratio - 1) * 10)
        else:
            # Large content → large size
            recommended = self.GROWING_SIZE_PERCENT

        # Enforce bounds
        return max(self.MIN_SIZE_PERCENT, min(self.MAX_SIZE_PERCENT, recommended))

    def register_callback(
        self,
        callback: Callable[[str, int], None]
    ) -> None:
        """
        Register a callback for resize events.

        Callback signature: callback(panel_id: str, recommended_size: int)

        Args:
            callback: Function to call when resize is recommended
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unregister_callback(
        self,
        callback: Callable[[str, int], None]
    ) -> None:
        """
        Unregister a callback.

        Args:
            callback: Function to remove
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def _notify_callbacks(self, panel_id: str, recommended_size: int) -> None:
        """
        Notify all callbacks of a recommended resize.

        Args:
            panel_id: Panel that needs resizing
            recommended_size: Recommended size percentage
        """
        for callback in self.callbacks:
            try:
                callback(panel_id, recommended_size)
            except Exception:
                pass  # Ignore callback errors

    async def start_monitoring(self, interval: float = 1.0) -> None:
        """
        Start periodic monitoring of content stability.

        Args:
            interval: Check interval in seconds (default: 1.0)
        """
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(
            self._monitor_loop(interval)
        )

    async def stop_monitoring(self) -> None:
        """Stop periodic monitoring."""
        self._monitoring = False
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self, interval: float) -> None:
        """
        Periodic monitoring loop.

        Checks for content stability and decay growth rates.
        """
        try:
            while self._monitoring:
                await asyncio.sleep(interval)

                # Check each panel's metrics
                for panel_id, metrics in self.metrics.items():
                    # Decay growth rate for stable content
                    if metrics.stable_count > self.STABLE_THRESHOLD:
                        if metrics.growth_rate > 0:
                            metrics.growth_rate *= 0.8

                    # Check if resize is needed
                    current_recommended = self.get_recommended_size(panel_id)
                    self._notify_callbacks(panel_id, current_recommended)

        except asyncio.CancelledError:
            pass

    def get_metrics(self, panel_id: str) -> Optional[ContentMetrics]:
        """
        Get metrics for a panel.

        Args:
            panel_id: Panel identifier

        Returns:
            ContentMetrics or None if panel not tracked
        """
        return self.metrics.get(panel_id)

    def reset_metrics(self, panel_id: Optional[str] = None) -> None:
        """
        Reset metrics for a panel or all panels.

        Args:
            panel_id: Specific panel to reset, or None for all
        """
        if panel_id:
            if panel_id in self.metrics:
                self.metrics[panel_id] = ContentMetrics(panel_id=panel_id)
        else:
            self.metrics.clear()

    def get_all_recommendations(self) -> Dict[str, int]:
        """
        Get recommended sizes for all tracked panels.

        Returns:
            Dict mapping panel_id to recommended size percentage
        """
        return {
            panel_id: self.get_recommended_size(panel_id)
            for panel_id in self.metrics
        }
