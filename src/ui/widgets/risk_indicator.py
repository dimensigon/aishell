"""
Risk Indicator Widget

Visual risk level display with color-coded indicators and progress bar styling.
Shows risk level with appropriate visual feedback (green/yellow/orange/red).
"""

import logging
from typing import Optional, Union

from textual.widgets import Static, ProgressBar
from textual.containers import Horizontal
from rich.text import Text

from ...database.risk_analyzer import RiskLevel


logger = logging.getLogger(__name__)


class RiskIndicator(Static):
    """
    Visual risk level indicator widget.

    Features:
    - Color-coded risk display (green/yellow/orange/red)
    - Progress bar style visual representation
    - Risk level text with emoji indicators
    - Dynamic updates via update_risk method

    Displays risk levels:
    - LOW: Green with ✓ indicator
    - MEDIUM: Yellow with ⚠ indicator
    - HIGH: Orange with ⚠⚠ indicator
    - CRITICAL: Red with ✗ indicator
    """

    CSS = """
    RiskIndicator {
        height: 3;
        width: 100%;
        background: $panel;
        border: solid transparent;
        padding: 0 1;
    }

    RiskIndicator.risk-low {
        background: $success 20%;
        border: solid $success;
    }

    RiskIndicator.risk-medium {
        background: $warning 20%;
        border: solid $warning;
    }

    RiskIndicator.risk-high {
        background: $error 20%;
        border: solid $error;
    }

    RiskIndicator.risk-critical {
        background: red 30%;
        border: solid red;
    }

    #risk-bar {
        width: 100%;
        height: 1;
        margin: 0;
    }

    #risk-text {
        text-align: center;
        text-style: bold;
        margin-top: 1;
    }

    .risk-text-low {
        color: $success;
    }

    .risk-text-medium {
        color: $warning;
    }

    .risk-text-high {
        color: $error;
    }

    .risk-text-critical {
        color: red;
    }
    """

    def __init__(
        self,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None
    ) -> None:
        """
        Initialize the risk indicator.

        Args:
            name: Optional widget name
            id: Optional unique identifier
            classes: Optional CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.current_risk_level: str = RiskLevel.LOW.value
        self.current_message: str = ""

    def compose(self):
        """Compose the widget layout."""
        # Use Static for visual bar instead of ProgressBar for simplicity
        yield Static("", id="risk-bar")
        yield Static("", id="risk-text")

    def update_risk(self, risk_level: str, message: str = "") -> None:
        """
        Update the risk indicator display.

        Args:
            risk_level: Risk level string (LOW/MEDIUM/HIGH/CRITICAL)
            message: Optional descriptive message

        Updates both visual indicator and text display with appropriate
        colors and symbols.
        """
        self.current_risk_level = risk_level
        self.current_message = message

        # Update CSS classes
        self._update_risk_classes(risk_level)

        # Update visual bar
        self._update_bar(risk_level)

        # Update text
        self._update_text(risk_level, message)

        logger.debug(f"Risk indicator updated: {risk_level} - {message}")

    def _update_risk_classes(self, risk_level: str) -> None:
        """
        Update CSS classes based on risk level.

        Args:
            risk_level: Risk level string
        """
        # Remove all risk classes
        for level in ['low', 'medium', 'high', 'critical']:
            self.remove_class(f"risk-{level}")

        # Add current risk class
        self.add_class(f"risk-{risk_level.lower()}")

    def _update_bar(self, risk_level: str) -> None:
        """
        Update the visual risk bar.

        Args:
            risk_level: Risk level string
        """
        # Get bar fill based on risk level
        bar_chars = {
            RiskLevel.LOW.value: "▁▁▁▁▁▁▁▁▁▁",
            RiskLevel.MEDIUM.value: "▄▄▄▄▄▄▄▄▄▄",
            RiskLevel.HIGH.value: "▆▆▆▆▆▆▆▆▆▆",
            RiskLevel.CRITICAL.value: "█████████████"
        }

        # Get color for bar
        colors = {
            RiskLevel.LOW.value: "green",
            RiskLevel.MEDIUM.value: "yellow",
            RiskLevel.HIGH.value: "bright_red",
            RiskLevel.CRITICAL.value: "red"
        }

        bar_text = Text(
            bar_chars.get(risk_level, "▁▁▁▁▁▁▁▁▁▁"),
            style=colors.get(risk_level, "white")
        )

        risk_bar = self.query_one("#risk-bar", Static)
        risk_bar.update(bar_text)

    def _update_text(self, risk_level: str, message: str) -> None:
        """
        Update the risk text display.

        Args:
            risk_level: Risk level string
            message: Descriptive message
        """
        # Get emoji indicator
        indicators = {
            RiskLevel.LOW.value: "✓",
            RiskLevel.MEDIUM.value: "⚠",
            RiskLevel.HIGH.value: "⚠⚠",
            RiskLevel.CRITICAL.value: "✗"
        }

        indicator = indicators.get(risk_level, "?")

        # Build display text
        display_text = f"{indicator} {risk_level}"
        if message:
            display_text += f" - {message}"

        # Get color for text
        colors = {
            RiskLevel.LOW.value: "green",
            RiskLevel.MEDIUM.value: "yellow",
            RiskLevel.HIGH.value: "bright_red",
            RiskLevel.CRITICAL.value: "bold red"
        }

        text_widget = self.query_one("#risk-text", Static)

        # Remove all text color classes
        for level in ['low', 'medium', 'high', 'critical']:
            text_widget.remove_class(f"risk-text-{level}")

        # Add current text color class
        text_widget.add_class(f"risk-text-{risk_level.lower()}")

        # Create rich text with color
        rich_text = Text(display_text, style=colors.get(risk_level, "white"))
        text_widget.update(rich_text)

    def get_risk_level(self) -> str:
        """
        Get the current risk level.

        Returns:
            Current risk level string
        """
        return self.current_risk_level

    def get_message(self) -> str:
        """
        Get the current message.

        Returns:
            Current message string
        """
        return self.current_message

    def reset(self) -> None:
        """Reset the indicator to LOW risk state."""
        self.update_risk(RiskLevel.LOW.value, "")
