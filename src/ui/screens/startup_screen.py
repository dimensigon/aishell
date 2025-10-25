"""
Matrix-style Startup Screen for AIShell

Provides a visually appealing startup screen with health check
integration and automatic transition to the main application.
"""

import asyncio
import logging
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Static, Label

from ...core.health_checks import HealthCheckRunner, HealthCheckResult, HealthStatus


logger = logging.getLogger(__name__)


class MatrixStartupScreen(Screen):
    """
    Matrix-style startup screen with health check display.

    Features:
    - Displays AI-SHELL initialization banner
    - Runs parallel health checks asynchronously
    - Shows check results with visual status indicators
    - Automatically transitions to main app after 2 seconds

    Attributes:
        health_runner: HealthCheckRunner instance for system checks
        health_results: List of completed health check results
    """

    CSS = """
    MatrixStartupScreen {
        align: center middle;
        background: $surface;
    }

    #startup-container {
        width: 80;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 2;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $success;
        margin-bottom: 1;
    }

    #health-checks {
        margin-top: 1;
        margin-bottom: 1;
    }

    .health-check-item {
        margin: 0 1;
    }

    .status-pass {
        color: $success;
    }

    .status-warn {
        color: $warning;
    }

    .status-fail {
        color: $error;
    }

    #progress {
        text-align: center;
        text-style: italic;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
        health_runner: Optional[HealthCheckRunner] = None
    ) -> None:
        """
        Initialize the Matrix startup screen.

        Args:
            name: Optional name for the screen
            id: Optional unique identifier
            classes: Optional CSS classes
            health_runner: Optional HealthCheckRunner instance (creates new if None)
        """
        super().__init__(name=name, id=id, classes=classes)
        self.health_runner = health_runner or HealthCheckRunner()
        self.health_results: List[HealthCheckResult] = []

    def compose(self) -> ComposeResult:
        """
        Compose the startup screen layout.

        Returns:
            UI components for the startup screen
        """
        with Container(id="startup-container"):
            yield Label(
                "╔══════════════════════════════════════════╗\n"
                "║     AI-SHELL INITIALIZING SYSTEM...      ║\n"
                "╚══════════════════════════════════════════╝",
                id="title"
            )
            yield Vertical(id="health-checks")
            yield Label("Running health checks...", id="progress")

    async def on_mount(self) -> None:
        """
        Execute startup tasks when screen is mounted.

        Runs health checks in parallel and updates the display,
        then transitions to main application.
        """
        logger.info("Matrix startup screen mounted - running health checks")

        # Run health checks asynchronously
        try:
            self.health_results = await self.health_runner.run_all_checks()
            self._update_health_display()

            # Update progress
            progress_label = self.query_one("#progress", Label)
            passed = sum(1 for r in self.health_results if r.status == HealthStatus.PASS)
            total = len(self.health_results)
            progress_label.update(f"Health checks complete: {passed}/{total} passed")

            # Wait 2 seconds before transitioning
            await asyncio.sleep(2.0)

            logger.info("Startup complete - transitioning to main app")
            # The app will handle the actual screen transition
            self.app.exit()  # Exit startup, main app continues

        except Exception as e:
            logger.error(f"Error during startup health checks: {e}")
            self._display_error(str(e))
            await asyncio.sleep(3.0)
            self.app.exit()

    def _update_health_display(self) -> None:
        """
        Update the health check display with results.

        Shows each check with appropriate status indicator:
        - ✓ for PASS (green)
        - ⚠ for WARN (yellow)
        - ✗ for FAIL (red)
        """
        health_container = self.query_one("#health-checks", Vertical)
        health_container.remove_children()

        for result in self.health_results:
            # Choose status indicator and CSS class
            if result.status == HealthStatus.PASS:
                indicator = "✓"
                css_class = "status-pass"
            elif result.status == HealthStatus.WARN:
                indicator = "⚠"
                css_class = "status-warn"
            else:  # FAIL
                indicator = "✗"
                css_class = "status-fail"

            # Get check description from runner
            check = self.health_runner.get_check(result.name)
            description = check.description if check else result.name

            # Format the display line
            line = f"{indicator} {description:<30} {result.message}"

            label = Static(line, classes=f"health-check-item {css_class}")
            health_container.mount(label)

    def _display_error(self, error_message: str) -> None:
        """
        Display an error message on the startup screen.

        Args:
            error_message: Error description to display
        """
        health_container = self.query_one("#health-checks", Vertical)
        health_container.remove_children()

        error_label = Static(
            f"✗ Startup Error: {error_message}",
            classes="health-check-item status-fail"
        )
        health_container.mount(error_label)

        progress_label = self.query_one("#progress", Label)
        progress_label.update("Initialization failed - please check logs")
