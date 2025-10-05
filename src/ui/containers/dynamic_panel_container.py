"""
Dynamic Panel Container for adaptive layout management.

Manages three panels (Output, Module, Prompt) with content-aware resizing,
activity-based adaptation, and smooth animations.
"""

import asyncio
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from textual.containers import Container, Vertical
from textual.widget import Widget
from textual.reactive import reactive
from textual.css.query import NoMatches


@dataclass
class PanelConfig:
    """Configuration for a single panel."""
    name: str
    default_size: int  # Percentage of total height
    min_size: int = 10  # Minimum 10%
    max_size: int = 80  # Maximum 80%
    current_size: int = 0
    content_height: int = 0
    is_active: bool = False

    def __post_init__(self):
        if self.current_size == 0:
            self.current_size = self.default_size


class DynamicPanelContainer(Container):
    """
    Adaptive panel layout system with content-aware resizing.

    Features:
    - Three panels: OutputPanel (50%), ModulePanel (30%), PromptPanel (20%)
    - Content-aware resizing (panels grow/shrink based on content)
    - Activity-based adaptation (expand active panel)
    - Smooth CSS animations (100ms transitions)
    - Min/max size constraints per panel

    Usage:
        container = DynamicPanelContainer()
        container.set_panel_content("output", output_widget)
        container.resize_panel("prompt", 30)  # Resize to 30%
        await container.auto_adjust()  # Automatic optimization
    """

    DEFAULT_CSS = """
    DynamicPanelContainer {
        layout: vertical;
        height: 100%;
        width: 100%;
    }

    DynamicPanelContainer > .panel {
        width: 100%;
        transition: height 100ms;
        overflow-y: auto;
    }

    DynamicPanelContainer > .panel-output {
        background: $surface;
        border: solid $primary;
    }

    DynamicPanelContainer > .panel-module {
        background: $surface;
        border: solid $secondary;
    }

    DynamicPanelContainer > .panel-prompt {
        background: $surface;
        border: solid $accent;
    }

    DynamicPanelContainer > .panel.active {
        border: double $primary;
    }
    """

    # Reactive properties for tracking panel states
    active_panel: reactive[Optional[str]] = reactive(None)

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
        disabled: bool = False,
    ) -> None:
        """Initialize the Dynamic Panel Container."""
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

        # Panel configurations
        self.panels: Dict[str, PanelConfig] = {
            'output': PanelConfig(name='output', default_size=50),
            'module': PanelConfig(name='module', default_size=30),
            'prompt': PanelConfig(name='prompt', default_size=20),
        }

        # Panel widgets (Container for each panel)
        self._panel_widgets: Dict[str, Vertical] = {}

        # Animation and resize state
        self._resize_task: Optional[asyncio.Task] = None
        self._manual_adjustment: Dict[str, bool] = {
            'output': False,
            'module': False,
            'prompt': False,
        }

        # Callbacks for size changes
        self._resize_callbacks: list[Callable[[str, int], None]] = []

    def compose(self):
        """Compose the panel widgets."""
        # Create panel containers
        for panel_name in ['output', 'module', 'prompt']:
            panel = Vertical(classes=f"panel panel-{panel_name}")
            panel.id = f"panel-{panel_name}"
            self._panel_widgets[panel_name] = panel
            yield panel

    def on_mount(self) -> None:
        """Initialize panels after mounting."""
        self._apply_panel_sizes()

    def _apply_panel_sizes(self) -> None:
        """Apply current panel sizes to widgets."""
        total_size = sum(p.current_size for p in self.panels.values())

        # Normalize sizes to 100%
        if total_size != 100:
            scale = 100 / total_size
            for panel in self.panels.values():
                panel.current_size = int(panel.current_size * scale)

        # Apply sizes to widgets
        for panel_name, config in self.panels.items():
            if panel_name in self._panel_widgets:
                widget = self._panel_widgets[panel_name]
                widget.styles.height = f"{config.current_size}%"

    async def resize_panel(
        self,
        panel_name: str,
        new_size: int,
        animate: bool = True,
        user_initiated: bool = True,
    ) -> bool:
        """
        Resize a panel with optional animation.

        Args:
            panel_name: Name of panel to resize ('output', 'module', 'prompt')
            new_size: New size as percentage (10-80)
            animate: Whether to animate the transition (default: True)
            user_initiated: Whether this is a manual user adjustment

        Returns:
            bool: True if resize was successful
        """
        if panel_name not in self.panels:
            return False

        config = self.panels[panel_name]

        # Enforce min/max constraints
        new_size = max(config.min_size, min(config.max_size, new_size))

        # Calculate size change
        size_diff = new_size - config.current_size

        if size_diff == 0:
            return True

        # Mark as manual adjustment if user-initiated
        if user_initiated:
            self._manual_adjustment[panel_name] = True

        # Distribute size change to other panels
        other_panels = [p for p in self.panels.values() if p.name != panel_name]
        total_other = sum(p.current_size for p in other_panels)

        if total_other - size_diff < len(other_panels) * 10:
            # Not enough space in other panels
            return False

        # Proportionally adjust other panels
        remaining_adjustment = size_diff
        for i, other_panel in enumerate(other_panels):
            if i == len(other_panels) - 1:
                # Last panel gets any remaining adjustment to ensure exact total
                adjustment = remaining_adjustment
            else:
                ratio = other_panel.current_size / total_other
                adjustment = int(size_diff * ratio)

            other_panel.current_size -= adjustment
            remaining_adjustment -= adjustment

            # Ensure constraints
            other_panel.current_size = max(
                other_panel.min_size,
                min(other_panel.max_size, other_panel.current_size)
            )

        # Update target panel
        config.current_size = new_size

        # Final normalization to ensure total is exactly 100%
        total_size = sum(p.current_size for p in self.panels.values())
        if total_size != 100:
            # Adjust the target panel to compensate for rounding
            diff = 100 - total_size
            config.current_size += diff
            # Re-enforce constraints
            config.current_size = max(
                config.min_size,
                min(config.max_size, config.current_size)
            )

        # Apply changes
        self._apply_panel_sizes()

        # Trigger callbacks
        for callback in self._resize_callbacks:
            try:
                callback(panel_name, new_size)
            except Exception:
                pass  # Ignore callback errors

        return True

    async def auto_adjust(self) -> None:
        """
        Automatically adjust panel sizes based on content and activity.

        Uses ContentSizeTracker data to optimize panel sizes:
        - Empty content → Minimum size
        - Growing content → Gradual expansion
        - Active panel → Slight preference
        """
        # Cancel any pending auto-adjust
        if self._resize_task and not self._resize_task.done():
            self._resize_task.cancel()

        # Run adjustment in background
        self._resize_task = asyncio.create_task(self._run_auto_adjust())

    async def _run_auto_adjust(self) -> None:
        """Internal auto-adjust implementation."""
        try:
            # Calculate recommended sizes based on content
            recommendations: Dict[str, int] = {}

            for panel_name, config in self.panels.items():
                # Skip panels with manual adjustments
                if self._manual_adjustment.get(panel_name, False):
                    recommendations[panel_name] = config.current_size
                    continue

                # Calculate recommended size
                if config.content_height == 0:
                    # Empty content → minimum size
                    recommended = config.min_size
                elif config.is_active:
                    # Active panel → prefer expansion
                    recommended = min(config.current_size + 10, config.max_size)
                else:
                    # Stable content → maintain or slightly reduce
                    recommended = max(config.current_size - 5, config.min_size)

                recommendations[panel_name] = recommended

            # Normalize recommendations to 100%
            total_recommended = sum(recommendations.values())
            if total_recommended > 0:
                for panel_name in recommendations:
                    recommendations[panel_name] = int(
                        (recommendations[panel_name] / total_recommended) * 100
                    )

            # Apply recommended sizes
            for panel_name, recommended_size in recommendations.items():
                if recommended_size != self.panels[panel_name].current_size:
                    await self.resize_panel(
                        panel_name,
                        recommended_size,
                        animate=True,
                        user_initiated=False,
                    )

        except asyncio.CancelledError:
            pass  # Task was cancelled
        except Exception:
            pass  # Silently handle errors in auto-adjust

    def set_panel_content(
        self,
        panel_name: str,
        content: Widget,
        content_height: Optional[int] = None,
    ) -> bool:
        """
        Update the content of a panel.

        Args:
            panel_name: Name of panel to update
            content: Widget to set as panel content
            content_height: Optional height hint for the content

        Returns:
            bool: True if update was successful
        """
        if panel_name not in self._panel_widgets:
            return False

        panel_widget = self._panel_widgets[panel_name]

        # Clear existing content
        panel_widget.remove_children()

        # Mount new content
        panel_widget.mount(content)

        # Update content height if provided
        if content_height is not None:
            config = self.panels[panel_name]
            config.content_height = content_height

        return True

    def set_active_panel(self, panel_name: Optional[str]) -> None:
        """
        Mark a panel as active (receiving user focus).

        Args:
            panel_name: Name of panel to activate, or None to deactivate all
        """
        # Clear all active states
        for config in self.panels.values():
            config.is_active = False
            if config.name in self._panel_widgets:
                widget = self._panel_widgets[config.name]
                widget.remove_class("active")

        # Set new active panel
        if panel_name and panel_name in self.panels:
            self.panels[panel_name].is_active = True
            self.active_panel = panel_name

            if panel_name in self._panel_widgets:
                widget = self._panel_widgets[panel_name]
                widget.add_class("active")

    def update_content_height(self, panel_name: str, height: int) -> None:
        """
        Update the content height for a panel.

        Called by ContentSizeTracker to report content changes.

        Args:
            panel_name: Name of panel
            height: New content height in lines
        """
        if panel_name in self.panels:
            self.panels[panel_name].content_height = height

    def register_resize_callback(
        self,
        callback: Callable[[str, int], None]
    ) -> None:
        """
        Register a callback to be notified of panel resizes.

        Args:
            callback: Function(panel_name, new_size) to call on resize
        """
        if callback not in self._resize_callbacks:
            self._resize_callbacks.append(callback)

    def unregister_resize_callback(
        self,
        callback: Callable[[str, int], None]
    ) -> None:
        """
        Unregister a resize callback.

        Args:
            callback: Function to remove from callbacks
        """
        if callback in self._resize_callbacks:
            self._resize_callbacks.remove(callback)

    def get_panel_size(self, panel_name: str) -> Optional[int]:
        """
        Get the current size of a panel.

        Args:
            panel_name: Name of panel

        Returns:
            int: Current size as percentage, or None if panel not found
        """
        if panel_name in self.panels:
            return self.panels[panel_name].current_size
        return None

    def reset_manual_adjustments(self) -> None:
        """Reset all manual adjustment flags to allow auto-adjustment."""
        for panel_name in self._manual_adjustment:
            self._manual_adjustment[panel_name] = False
