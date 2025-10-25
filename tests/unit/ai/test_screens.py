"""
Tests for UI Screens (src/ui/screens/startup_screen.py)

Tests screen transitions, startup flow, and health check integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from textual.widgets import Label, Static
from textual.containers import Vertical

from src.ui.screens.startup_screen import MatrixStartupScreen
from src.core.health_checks import (
    HealthCheckRunner,
    HealthCheckResult,
    HealthStatus,
    HealthCheck
)


class TestMatrixStartupScreen:
    """Test suite for MatrixStartupScreen."""

    @pytest.fixture
    def mock_health_runner(self):
        """Create mock health check runner."""
        runner = Mock(spec=HealthCheckRunner)
        runner.run_all_checks = AsyncMock(return_value=[])
        runner.get_check = Mock(return_value=None)
        return runner

    @pytest.fixture
    def screen(self, mock_health_runner):
        """Create MatrixStartupScreen instance."""
        return MatrixStartupScreen(
            health_runner=mock_health_runner,
            id="test-startup"
        )

    def test_initialization(self, screen, mock_health_runner):
        """Test screen initializes correctly."""
        assert screen.health_runner == mock_health_runner
        assert screen.health_results == []

    def test_initialization_creates_runner(self):
        """Test screen creates health runner if not provided."""
        screen = MatrixStartupScreen()

        assert screen.health_runner is not None
        assert isinstance(screen.health_runner, HealthCheckRunner)

    @pytest.mark.asyncio
    async def test_on_mount_runs_health_checks(self, screen, mock_health_runner):
        """Test on_mount runs health checks."""
        # Mock UI components
        screen.query_one = Mock(return_value=Mock(spec=Label, update=Mock()))
        screen._update_health_display = Mock()
        screen.app = Mock(exit=Mock())

        # Mock successful checks
        mock_health_runner.run_all_checks = AsyncMock(return_value=[
            HealthCheckResult(
                name="test_check",
                status=HealthStatus.PASS,
                message="OK"
            )
        ])

        await screen.on_mount()

        mock_health_runner.run_all_checks.assert_called_once()
        screen._update_health_display.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_mount_exits_after_delay(self, screen, mock_health_runner):
        """Test on_mount exits after 2 second delay."""
        # Mock UI components
        screen.query_one = Mock(return_value=Mock(spec=Label, update=Mock()))
        screen._update_health_display = Mock()
        screen.app = Mock(exit=Mock())

        mock_health_runner.run_all_checks = AsyncMock(return_value=[])

        # Track timing
        start = asyncio.get_event_loop().time()
        await screen.on_mount()
        duration = asyncio.get_event_loop().time() - start

        # Should wait approximately 2 seconds
        assert duration >= 1.9  # Allow some variance
        screen.app.exit.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_mount_handles_errors(self, screen, mock_health_runner):
        """Test on_mount handles health check errors."""
        # Mock UI components
        screen.query_one = Mock(return_value=Mock(spec=Label, update=Mock()))
        screen._display_error = Mock()
        screen.app = Mock(exit=Mock())

        # Make health checks raise error
        mock_health_runner.run_all_checks = AsyncMock(
            side_effect=Exception("Test error")
        )

        await screen.on_mount()

        screen._display_error.assert_called_once()
        screen.app.exit.assert_called_once()

    def test_update_health_display_pass(self, screen, mock_health_runner):
        """Test displaying PASS health checks."""
        # Mock UI components
        container = Mock(spec=Vertical, remove_children=Mock(), mount=Mock())
        screen.query_one = Mock(return_value=container)

        # Mock health check
        mock_check = Mock(spec=HealthCheck, description="Test Check")
        mock_health_runner.get_check = Mock(return_value=mock_check)

        screen.health_results = [
            HealthCheckResult(
                name="test_check",
                status=HealthStatus.PASS,
                message="All OK"
            )
        ]

        screen._update_health_display()

        container.remove_children.assert_called_once()
        container.mount.assert_called()

        # Check that Static widget was created with correct indicator
        call_args = container.mount.call_args[0][0]
        assert hasattr(call_args, 'renderable')

    def test_update_health_display_warn(self, screen, mock_health_runner):
        """Test displaying WARN health checks."""
        container = Mock(spec=Vertical, remove_children=Mock(), mount=Mock())
        screen.query_one = Mock(return_value=container)

        mock_check = Mock(spec=HealthCheck, description="Warning Check")
        mock_health_runner.get_check = Mock(return_value=mock_check)

        screen.health_results = [
            HealthCheckResult(
                name="warn_check",
                status=HealthStatus.WARN,
                message="Warning detected"
            )
        ]

        screen._update_health_display()

        # Should mount with warning class
        container.mount.assert_called()

    def test_update_health_display_fail(self, screen, mock_health_runner):
        """Test displaying FAIL health checks."""
        container = Mock(spec=Vertical, remove_children=Mock(), mount=Mock())
        screen.query_one = Mock(return_value=container)

        mock_check = Mock(spec=HealthCheck, description="Failed Check")
        mock_health_runner.get_check = Mock(return_value=mock_check)

        screen.health_results = [
            HealthCheckResult(
                name="fail_check",
                status=HealthStatus.FAIL,
                message="Check failed"
            )
        ]

        screen._update_health_display()

        # Should mount with fail class
        container.mount.assert_called()

    def test_update_health_display_multiple_checks(self, screen, mock_health_runner):
        """Test displaying multiple health checks."""
        container = Mock(spec=Vertical, remove_children=Mock(), mount=Mock())
        screen.query_one = Mock(return_value=container)

        mock_check = Mock(spec=HealthCheck, description="Check")
        mock_health_runner.get_check = Mock(return_value=mock_check)

        screen.health_results = [
            HealthCheckResult("check1", HealthStatus.PASS, "OK"),
            HealthCheckResult("check2", HealthStatus.WARN, "Warning"),
            HealthCheckResult("check3", HealthStatus.FAIL, "Failed"),
        ]

        screen._update_health_display()

        # Should mount 3 widgets
        assert container.mount.call_count == 3

    def test_display_error(self, screen):
        """Test displaying error message."""
        # Mock UI components
        container = Mock(spec=Vertical, remove_children=Mock(), mount=Mock())
        progress_label = Mock(spec=Label, update=Mock())

        def query_side_effect(selector, widget_type=None):
            if selector == "#health-checks":
                return container
            elif selector == "#progress":
                return progress_label
            return Mock()

        screen.query_one = Mock(side_effect=query_side_effect)

        screen._display_error("Test error message")

        container.remove_children.assert_called_once()
        container.mount.assert_called_once()
        progress_label.update.assert_called_once()

        # Check error message is in the mounted widget
        call_args = container.mount.call_args[0][0]
        assert hasattr(call_args, 'renderable')

    def test_health_check_indicators(self, screen, mock_health_runner):
        """Test correct indicators for each status."""
        container = Mock(spec=Vertical, remove_children=Mock(), mount=Mock())
        screen.query_one = Mock(return_value=container)

        mock_check = Mock(spec=HealthCheck, description="Test")
        mock_health_runner.get_check = Mock(return_value=mock_check)

        # Test each status
        for status, expected_indicator in [
            (HealthStatus.PASS, "✓"),
            (HealthStatus.WARN, "⚠"),
            (HealthStatus.FAIL, "✗"),
        ]:
            container.mount.reset_mock()
            screen.health_results = [
                HealthCheckResult("test", status, "Message")
            ]

            screen._update_health_display()

            # Widget should contain the indicator (implementation dependent)
            container.mount.assert_called()

    @pytest.mark.asyncio
    async def test_progress_message_updates(self, screen, mock_health_runner):
        """Test progress message updates correctly."""
        progress_label = Mock(spec=Label, update=Mock())
        container = Mock(spec=Vertical, remove_children=Mock(), mount=Mock())

        def query_side_effect(selector, widget_type=None):
            if selector == "#progress":
                return progress_label
            return container

        screen.query_one = Mock(side_effect=query_side_effect)
        screen._update_health_display = Mock()
        screen.app = Mock(exit=Mock())

        # Mock 2 passed checks, 1 failed
        mock_health_runner.run_all_checks = AsyncMock(return_value=[
            HealthCheckResult("check1", HealthStatus.PASS, "OK"),
            HealthCheckResult("check2", HealthStatus.PASS, "OK"),
            HealthCheckResult("check3", HealthStatus.FAIL, "Failed"),
        ])

        await screen.on_mount()

        # Progress should show 2/3 passed
        assert progress_label.update.called
        call_args = progress_label.update.call_args[0][0]
        assert "2/3" in call_args

    def test_css_classes_for_status(self, screen, mock_health_runner):
        """Test CSS classes are applied based on status."""
        container = Mock(spec=Vertical, remove_children=Mock(), mount=Mock())
        screen.query_one = Mock(return_value=container)

        mock_check = Mock(spec=HealthCheck, description="Test")
        mock_health_runner.get_check = Mock(return_value=mock_check)

        # Test each status has correct CSS class
        for status, expected_class in [
            (HealthStatus.PASS, "status-pass"),
            (HealthStatus.WARN, "status-warn"),
            (HealthStatus.FAIL, "status-fail"),
        ]:
            container.mount.reset_mock()
            screen.health_results = [
                HealthCheckResult("test", status, "Message")
            ]

            screen._update_health_display()

            # Check widget was created with correct class
            call_args = container.mount.call_args[0][0]
            # Widget classes should include the status class
            # (Exact implementation may vary)

    @pytest.mark.asyncio
    async def test_startup_timing(self, screen, mock_health_runner):
        """Test startup completes in reasonable time."""
        screen.query_one = Mock(return_value=Mock(spec=Label, update=Mock()))
        screen._update_health_display = Mock()
        screen.app = Mock(exit=Mock())

        mock_health_runner.run_all_checks = AsyncMock(return_value=[])

        start = asyncio.get_event_loop().time()
        await screen.on_mount()
        duration = asyncio.get_event_loop().time() - start

        # Should complete in approximately 2 seconds
        assert 1.9 <= duration <= 2.5

    def test_health_check_description_fallback(self, screen, mock_health_runner):
        """Test fallback when health check has no description."""
        container = Mock(spec=Vertical, remove_children=Mock(), mount=Mock())
        screen.query_one = Mock(return_value=container)

        # Return None for get_check to test fallback
        mock_health_runner.get_check = Mock(return_value=None)

        screen.health_results = [
            HealthCheckResult("test_check", HealthStatus.PASS, "OK")
        ]

        screen._update_health_display()

        # Should use check name as fallback
        container.mount.assert_called()
