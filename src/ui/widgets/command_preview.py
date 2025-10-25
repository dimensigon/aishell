"""
Command Preview Widget with Real-time Risk Analysis

Displays command being typed with asynchronous risk analysis visualization.
Updates in real-time (< 200ms target) with overlay positioning above prompt.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from textual.widgets import Static
from textual.containers import Container
from textual.reactive import reactive

from ...database.risk_analyzer import SQLRiskAnalyzer, RiskLevel
from .risk_indicator import RiskIndicator


logger = logging.getLogger(__name__)


class CommandPreviewWidget(Static):
    """
    Command preview widget with real-time risk visualization.

    Features:
    - Displays command being typed
    - Shows risk analysis results asynchronously
    - Updates within 200ms target
    - Overlay positioning (appears above prompt)
    - Auto-hides when not typing or low risk
    - Integration with SQLRiskAnalyzer

    Attributes:
        risk_analyzer: SQLRiskAnalyzer instance for risk detection
        current_command: Currently displayed command
        is_visible: Whether the widget is currently visible
        last_analysis: Most recent risk analysis result
        analysis_task: Current async analysis task
    """

    CSS = """
    CommandPreviewWidget {
        display: none;
        dock: top;
        height: auto;
        width: 100%;
        background: $panel;
        border: solid $primary;
        padding: 1 2;
        margin-bottom: 1;
    }

    CommandPreviewWidget.visible {
        display: block;
    }

    CommandPreviewWidget.risk-low {
        border: solid $success;
        background: $success 10%;
    }

    CommandPreviewWidget.risk-medium {
        border: solid $warning;
        background: $warning 10%;
    }

    CommandPreviewWidget.risk-high {
        border: solid $error;
        background: $error 10%;
    }

    CommandPreviewWidget.risk-critical {
        border: solid red;
        background: red 20%;
    }

    #command-text {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    #risk-section {
        height: auto;
        margin-top: 1;
    }

    #warnings-section {
        height: auto;
        margin-top: 1;
    }

    .warning-item {
        color: $warning;
        margin: 0 1;
    }

    .issue-item {
        color: $error;
        margin: 0 1;
    }

    #impact-section {
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
    }
    """

    current_command = reactive("")
    is_visible = reactive(False)

    def __init__(
        self,
        risk_analyzer: Optional[SQLRiskAnalyzer] = None,
        auto_hide_low_risk: bool = True,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None
    ) -> None:
        """
        Initialize the command preview widget.

        Args:
            risk_analyzer: SQLRiskAnalyzer instance (creates new if None)
            auto_hide_low_risk: Auto-hide widget for low-risk commands
            name: Optional widget name
            id: Optional unique identifier
            classes: Optional CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.risk_analyzer = risk_analyzer or SQLRiskAnalyzer()
        self.auto_hide_low_risk = auto_hide_low_risk
        self.last_analysis: Optional[Dict[str, Any]] = None
        self.analysis_task: Optional[asyncio.Task] = None
        self.risk_indicator: Optional[RiskIndicator] = None

    def compose(self):
        """Compose the widget layout."""
        yield Static("", id="command-text")
        yield Container(
            RiskIndicator(id="risk-indicator"),
            id="risk-section"
        )
        yield Container(id="warnings-section")
        yield Static("", id="impact-section")

    def on_mount(self) -> None:
        """Initialize widget state when mounted."""
        self.risk_indicator = self.query_one("#risk-indicator", RiskIndicator)

    async def update_preview(self, command: str) -> None:
        """
        Update preview with new command and trigger risk analysis.

        This is the main entry point for real-time updates.
        Cancels any pending analysis and starts a new one.

        Args:
            command: SQL command to analyze

        Performance: Targets < 200ms update time
        """
        # Skip empty commands
        if not command or not command.strip():
            await self._hide()
            return

        self.current_command = command

        # Cancel any pending analysis
        if self.analysis_task and not self.analysis_task.done():
            self.analysis_task.cancel()

        # Start new analysis task
        self.analysis_task = asyncio.create_task(self._run_analysis(command))

    async def _run_analysis(self, command: str) -> None:
        """
        Run risk analysis asynchronously.

        Uses asyncio.to_thread to prevent blocking the UI thread.

        Args:
            command: SQL command to analyze
        """
        start_time = datetime.now()

        try:
            # Run analysis in thread pool to avoid blocking UI
            analysis = await asyncio.to_thread(
                self.risk_analyzer.analyze,
                command
            )

            self.last_analysis = analysis

            # Update display with results
            await self._update_display(analysis)

            # Log performance
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.debug(f"Risk analysis completed in {duration_ms:.1f}ms")

            if duration_ms > 200:
                logger.warning(
                    f"Risk analysis exceeded 200ms target: {duration_ms:.1f}ms"
                )

        except asyncio.CancelledError:
            logger.debug("Risk analysis cancelled - new command received")
            raise
        except Exception as e:
            logger.error(f"Error during risk analysis: {e}")
            await self._display_error(str(e))

    async def _update_display(self, analysis: Dict[str, Any]) -> None:
        """
        Update widget display with analysis results.

        Args:
            analysis: Risk analysis result from SQLRiskAnalyzer
        """
        risk_level = analysis['risk_level']
        warnings = analysis.get('warnings', [])
        issues = analysis.get('issues', [])

        # Update command text
        command_text = self.query_one("#command-text", Static)
        command_text.update(f"Command: {self.current_command[:80]}...")

        # Update risk indicator
        if self.risk_indicator:
            risk_msg = self._get_risk_message(risk_level)
            self.risk_indicator.update_risk(risk_level, risk_msg)

        # Update warnings section
        warnings_container = self.query_one("#warnings-section", Container)
        warnings_container.remove_children()

        for warning in warnings:
            warnings_container.mount(Static(warning, classes="warning-item"))

        for issue in issues:
            warnings_container.mount(Static(f"⚠ {issue}", classes="issue-item"))

        # Update impact estimation placeholder
        impact_text = self.query_one("#impact-section", Static)
        impact_text.update("Impact estimation: Calculating...")

        # Update CSS classes for risk level
        self._update_risk_classes(risk_level)

        # Show/hide based on risk level
        await self._update_visibility(risk_level)

    def _update_risk_classes(self, risk_level: str) -> None:
        """
        Update CSS classes based on risk level.

        Args:
            risk_level: Risk level string (LOW/MEDIUM/HIGH/CRITICAL)
        """
        # Remove all risk classes
        for level in ['low', 'medium', 'high', 'critical']:
            self.remove_class(f"risk-{level}")

        # Add current risk class
        self.add_class(f"risk-{risk_level.lower()}")

    async def _update_visibility(self, risk_level: str) -> None:
        """
        Update widget visibility based on risk level.

        Args:
            risk_level: Risk level string
        """
        # Auto-hide for LOW risk if configured
        if self.auto_hide_low_risk and risk_level == RiskLevel.LOW.value:
            await self._hide()
        else:
            await self._show()

    async def _show(self) -> None:
        """Show the preview widget."""
        if not self.is_visible:
            self.is_visible = True
            self.add_class("visible")

    async def _hide(self) -> None:
        """Hide the preview widget."""
        if self.is_visible:
            self.is_visible = False
            self.remove_class("visible")
            self.current_command = ""
            self.last_analysis = None

    async def _display_error(self, error_message: str) -> None:
        """
        Display error message in the preview.

        Args:
            error_message: Error description
        """
        command_text = self.query_one("#command-text", Static)
        command_text.update(f"Error analyzing command: {error_message}")

        if self.risk_indicator:
            self.risk_indicator.update_risk(
                RiskLevel.MEDIUM.value,
                "Analysis error - proceed with caution"
            )

        await self._show()

    def _get_risk_message(self, risk_level: str) -> str:
        """
        Get descriptive message for risk level.

        Args:
            risk_level: Risk level string

        Returns:
            Human-readable risk message
        """
        messages = {
            RiskLevel.LOW.value: "Safe to execute - read operation",
            RiskLevel.MEDIUM.value: "Review carefully - data modification",
            RiskLevel.HIGH.value: "High risk - affects multiple rows",
            RiskLevel.CRITICAL.value: "CRITICAL - destructive operation!"
        }
        return messages.get(risk_level, "Unknown risk level")

    async def set_impact_estimation(self, estimated_rows: int, confidence: float) -> None:
        """
        Update impact estimation display.

        Args:
            estimated_rows: Estimated number of affected rows
            confidence: Confidence level (0.0 - 1.0)
        """
        impact_text = self.query_one("#impact-section", Static)
        confidence_pct = int(confidence * 100)
        impact_text.update(
            f"Estimated impact: ~{estimated_rows} rows affected "
            f"(confidence: {confidence_pct}%)"
        )

    def get_last_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent risk analysis result.

        Returns:
            Last analysis dictionary or None
        """
        return self.last_analysis

    async def clear(self) -> None:
        """Clear the preview and reset state."""
        await self._hide()
        if self.analysis_task and not self.analysis_task.done():
            self.analysis_task.cancel()
