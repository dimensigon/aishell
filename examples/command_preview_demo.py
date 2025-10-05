"""
Command Preview Widget Demo

Demonstrates the integration of CommandPreviewWidget with SQLRiskAnalyzer
and ImpactEstimator for real-time risk visualization.

Usage:
    python examples/command_preview_demo.py
"""

import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Header, Footer
from textual.containers import Container, Vertical

from src.ui.widgets.command_preview import CommandPreviewWidget
from src.database.risk_analyzer import SQLRiskAnalyzer
from src.database.impact_estimator import ImpactEstimator


class CommandPreviewDemo(App):
    """
    Demo application for command preview widget.

    Features:
    - Real-time SQL risk analysis as you type
    - Visual risk indicators with color coding
    - Impact estimation (affected rows)
    - Async updates < 200ms target
    """

    CSS = """
    Screen {
        background: $surface;
    }

    #input-container {
        height: auto;
        dock: bottom;
        background: $panel;
        border-top: solid $primary;
        padding: 1 2;
    }

    #sql-input {
        width: 100%;
        margin-bottom: 1;
    }

    #output-container {
        height: 100%;
        padding: 2;
        overflow-y: auto;
    }

    .demo-text {
        color: $text-muted;
        margin: 1 0;
        text-style: italic;
    }

    .example-sql {
        color: $success;
        background: $panel;
        padding: 1;
        margin: 1 0;
        border-left: solid $success;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+l", "clear", "Clear"),
    ]

    def __init__(self):
        super().__init__()
        self.risk_analyzer = SQLRiskAnalyzer()
        self.impact_estimator = ImpactEstimator()

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        with Vertical(id="output-container"):
            yield Static(
                "═══════════════════════════════════════════════════════\n"
                "  COMMAND PREVIEW WIDGET DEMO\n"
                "═══════════════════════════════════════════════════════",
                classes="demo-text"
            )
            yield Static(
                "Type SQL commands below to see real-time risk analysis.\n"
                "The preview widget will show risk level, warnings, and impact estimation.",
                classes="demo-text"
            )
            yield Static(
                "\nExample commands to try:",
                classes="demo-text"
            )
            yield Static(
                "  SELECT * FROM users WHERE id = 1",
                classes="example-sql"
            )
            yield Static(
                "  DELETE FROM users WHERE id > 1000",
                classes="example-sql"
            )
            yield Static(
                "  UPDATE users SET active=1 WHERE login_date < '2024-01-01'",
                classes="example-sql"
            )
            yield Static(
                "  DELETE FROM users  (no WHERE clause - HIGH RISK!)",
                classes="example-sql"
            )
            yield Static(
                "  DROP TABLE users  (CRITICAL RISK!)",
                classes="example-sql"
            )

        with Container(id="input-container"):
            yield CommandPreviewWidget(
                risk_analyzer=self.risk_analyzer,
                auto_hide_low_risk=False,  # Always show for demo
                id="preview"
            )
            yield Input(
                placeholder="Enter SQL command here...",
                id="sql-input"
            )

        yield Footer()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """
        Handle input changes and update preview.

        Args:
            event: Input changed event
        """
        sql_command = event.value

        # Update command preview
        preview = self.query_one("#preview", CommandPreviewWidget)
        await preview.update_preview(sql_command)

        # Also run impact estimation
        if sql_command and sql_command.strip():
            try:
                impact = await self.impact_estimator.estimate_impact(
                    sql_command,
                    None
                )
                await preview.set_impact_estimation(
                    impact['estimated_rows'],
                    impact['confidence']
                )
            except Exception as e:
                self.log(f"Impact estimation error: {e}")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle command submission.

        Args:
            event: Input submitted event
        """
        sql_command = event.value

        if not sql_command or not sql_command.strip():
            return

        # Show what would be executed
        self.notify(
            f"Would execute: {sql_command[:50]}...",
            title="Command Submitted",
            severity="information"
        )

        # Clear input
        input_widget = self.query_one("#sql-input", Input)
        input_widget.value = ""

    def action_clear(self) -> None:
        """Clear the input and preview."""
        input_widget = self.query_one("#sql-input", Input)
        input_widget.value = ""

        preview = self.query_one("#preview", CommandPreviewWidget)
        asyncio.create_task(preview.clear())


async def main():
    """Run the demo application."""
    app = CommandPreviewDemo()
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
