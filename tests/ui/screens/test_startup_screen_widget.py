"""
Tests for MatrixStartupScreen (src/ui/screens/startup_screen.py)

Tests health checks, visual display, async transitions, and error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.ui.screens.startup_screen import MatrixStartupScreen
from src.core.health_checks import HealthCheckRunner, HealthCheckResult, HealthStatus, HealthCheck


class TestMatrixStartupScreen:
    """Test suite for MatrixStartupScreen."""

    @pytest.fixture
    def mock_health_runner(self):
        """Create mock health check runner."""
        runner = Mock(spec=HealthCheckRunner)
        runner.run_all_checks = AsyncMock(return_value=[
            HealthCheckResult("test_check", HealthStatus.PASS, "OK"),
            HealthCheckResult("db_check", HealthStatus.PASS, "Connected"),
            HealthCheckResult("llm_check", HealthStatus.WARN, "Slow response")
        ])
        runner.get_check = Mock(return_value=HealthCheck(
            name="test",
            description="Test check",
            func=lambda: True
        ))
        return runner

    @pytest.fixture
    def startup_screen(self, mock_health_runner):
        """Create MatrixStartupScreen instance."""
        return MatrixStartupScreen(
            name="startup",
            id="startup-screen",
            health_runner=mock_health_runner
        )

    def test_initialization(self, startup_screen, mock_health_runner):
        """Test screen initializes correctly."""
        assert startup_screen.health_runner == mock_health_runner
        assert startup_screen.health_results == []

    def test_initialization_creates_runner_if_none(self):
        """Test screen creates runner if not provided."""
        screen = MatrixStartupScreen()
        assert isinstance(screen.health_runner, HealthCheckRunner)

    def test_css_defined(self):
        """Test CSS is defined."""
        assert hasattr(MatrixStartupScreen, 'CSS')
        assert isinstance(MatrixStartupScreen.CSS, str)
        assert 'MatrixStartupScreen' in MatrixStartupScreen.CSS

    def test_compose_yields_widgets(self, startup_screen):
        """Test compose yields required widgets."""
        widgets = list(startup_screen.compose())

        # Should have container with title, health checks area, progress
        assert len(widgets) > 0

    @pytest.mark.asyncio
    async def test_on_mount_runs_health_checks(self, startup_screen, mock_health_runner):
        """Test on_mount runs health checks."""
        # Mock app.exit to prevent actual exit
        startup_screen.app = Mock()
        startup_screen.app.exit = Mock()

        # Mock query_one to return mocks
        with patch.object(startup_screen, 'query_one', side_effect=[
            Mock(update=Mock()),  # progress label first call
            Mock(update=Mock())   # progress label second call
        ]):
            with patch.object(startup_screen, '_update_health_display'):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    await startup_screen.on_mount()

        mock_health_runner.run_all_checks.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_mount_updates_display(self, startup_screen, mock_health_runner):
        """Test on_mount updates health display."""
        startup_screen.app = Mock()
        startup_screen.app.exit = Mock()

        with patch.object(startup_screen, 'query_one', return_value=Mock(update=Mock())):
            with patch.object(startup_screen, '_update_health_display') as mock_update:
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    await startup_screen.on_mount()

        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_mount_transitions_after_delay(self, startup_screen, mock_health_runner):
        """Test on_mount transitions after 2 seconds."""
        startup_screen.app = Mock()
        startup_screen.app.exit = Mock()

        with patch.object(startup_screen, 'query_one', return_value=Mock(update=Mock())):
            with patch.object(startup_screen, '_update_health_display'):
                with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                    await startup_screen.on_mount()

        # Should sleep for 2 seconds
        mock_sleep.assert_called_once_with(2.0)

    @pytest.mark.asyncio
    async def test_on_mount_calls_app_exit(self, startup_screen, mock_health_runner):
        """Test on_mount calls app.exit."""
        startup_screen.app = Mock()
        startup_screen.app.exit = Mock()

        with patch.object(startup_screen, 'query_one', return_value=Mock(update=Mock())):
            with patch.object(startup_screen, '_update_health_display'):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    await startup_screen.on_mount()

        startup_screen.app.exit.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_mount_handles_errors(self, startup_screen, mock_health_runner):
        """Test on_mount handles errors gracefully."""
        startup_screen.app = Mock()
        startup_screen.app.exit = Mock()

        # Make health checks fail
        mock_health_runner.run_all_checks = AsyncMock(side_effect=Exception("Test error"))

        with patch.object(startup_screen, '_display_error') as mock_error:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await startup_screen.on_mount()

        mock_error.assert_called_once_with("Test error")

    def test_update_health_display_pass(self, startup_screen):
        """Test health display for PASS status."""
        startup_screen.health_results = [
            HealthCheckResult("test_check", HealthStatus.PASS, "All good")
        ]

        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        with patch.object(startup_screen, 'query_one', return_value=mock_container):
            startup_screen._update_health_display()

        # Should mount one health check item
        mock_container.mount.assert_called_once()

        # Check that it includes checkmark
        call_args = str(mock_container.mount.call_args)
        assert "✓" in call_args

    def test_update_health_display_warn(self, startup_screen):
        """Test health display for WARN status."""
        startup_screen.health_results = [
            HealthCheckResult("test_check", HealthStatus.WARN, "Slow")
        ]

        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        with patch.object(startup_screen, 'query_one', return_value=mock_container):
            startup_screen._update_health_display()

        # Check that it includes warning indicator
        call_args = str(mock_container.mount.call_args)
        assert "⚠" in call_args

    def test_update_health_display_fail(self, startup_screen):
        """Test health display for FAIL status."""
        startup_screen.health_results = [
            HealthCheckResult("test_check", HealthStatus.FAIL, "Connection failed")
        ]

        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        with patch.object(startup_screen, 'query_one', return_value=mock_container):
            startup_screen._update_health_display()

        # Check that it includes X indicator
        call_args = str(mock_container.mount.call_args)
        assert "✗" in call_args

    def test_update_health_display_multiple_checks(self, startup_screen):
        """Test health display with multiple checks."""
        startup_screen.health_results = [
            HealthCheckResult("check1", HealthStatus.PASS, "OK"),
            HealthCheckResult("check2", HealthStatus.WARN, "Slow"),
            HealthCheckResult("check3", HealthStatus.FAIL, "Failed")
        ]

        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        with patch.object(startup_screen, 'query_one', return_value=mock_container):
            startup_screen._update_health_display()

        # Should mount three health check items
        assert mock_container.mount.call_count == 3

    def test_update_health_display_clears_previous(self, startup_screen):
        """Test health display clears previous items."""
        startup_screen.health_results = [
            HealthCheckResult("test", HealthStatus.PASS, "OK")
        ]

        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        with patch.object(startup_screen, 'query_one', return_value=mock_container):
            startup_screen._update_health_display()

        mock_container.remove_children.assert_called_once()

    def test_display_error(self, startup_screen):
        """Test error display."""
        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        mock_progress = Mock()
        mock_progress.update = Mock()

        with patch.object(startup_screen, 'query_one', side_effect=[
            mock_container,
            mock_progress
        ]):
            startup_screen._display_error("Test error message")

        # Should mount error
        mock_container.mount.assert_called_once()

        # Should update progress with error
        mock_progress.update.assert_called_once()
        call_arg = str(mock_progress.update.call_args)
        assert "failed" in call_arg.lower()

    def test_display_error_includes_message(self, startup_screen):
        """Test error display includes message."""
        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        with patch.object(startup_screen, 'query_one', side_effect=[
            mock_container,
            Mock(update=Mock())
        ]):
            startup_screen._display_error("Custom error")

        call_arg = str(mock_container.mount.call_args)
        assert "Custom error" in call_arg

    @pytest.mark.asyncio
    async def test_progress_message_shows_passed_count(self, startup_screen, mock_health_runner):
        """Test progress message shows passed/total count."""
        startup_screen.app = Mock()
        startup_screen.app.exit = Mock()

        mock_progress = Mock()
        mock_progress.update = Mock()

        with patch.object(startup_screen, 'query_one', side_effect=[
            mock_progress,  # First call
            mock_progress   # Second call
        ]):
            with patch.object(startup_screen, '_update_health_display'):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    await startup_screen.on_mount()

        # Check final progress message
        final_call = mock_progress.update.call_args_list[-1]
        call_str = str(final_call)
        assert "passed" in call_str.lower()

    def test_health_check_styling_pass(self, startup_screen):
        """Test PASS checks get success styling."""
        startup_screen.health_results = [
            HealthCheckResult("test", HealthStatus.PASS, "OK")
        ]

        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        with patch.object(startup_screen, 'query_one', return_value=mock_container):
            startup_screen._update_health_display()

        call_arg = str(mock_container.mount.call_args)
        assert "status-pass" in call_arg

    def test_health_check_styling_warn(self, startup_screen):
        """Test WARN checks get warning styling."""
        startup_screen.health_results = [
            HealthCheckResult("test", HealthStatus.WARN, "Slow")
        ]

        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        with patch.object(startup_screen, 'query_one', return_value=mock_container):
            startup_screen._update_health_display()

        call_arg = str(mock_container.mount.call_args)
        assert "status-warn" in call_arg

    def test_health_check_styling_fail(self, startup_screen):
        """Test FAIL checks get error styling."""
        startup_screen.health_results = [
            HealthCheckResult("test", HealthStatus.FAIL, "Error")
        ]

        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        with patch.object(startup_screen, 'query_one', return_value=mock_container):
            startup_screen._update_health_display()

        call_arg = str(mock_container.mount.call_args)
        assert "status-fail" in call_arg
