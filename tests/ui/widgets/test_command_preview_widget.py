"""
Tests for CommandPreviewWidget (src/ui/widgets/command_preview.py)

Tests async risk analysis, real-time updates, visual display, and performance.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.ui.widgets.command_preview import CommandPreviewWidget
from src.ui.widgets.risk_indicator import RiskIndicator
from src.database.risk_analyzer import SQLRiskAnalyzer, RiskLevel


class TestCommandPreviewWidget:
    """Test suite for CommandPreviewWidget."""

    @pytest.fixture
    def mock_risk_analyzer(self):
        """Create mock risk analyzer."""
        analyzer = Mock(spec=SQLRiskAnalyzer)
        analyzer.analyze = Mock(return_value={
            'risk_level': RiskLevel.LOW.value,
            'warnings': [],
            'issues': []
        })
        return analyzer

    @pytest.fixture
    def preview_widget(self, mock_risk_analyzer):
        """Create CommandPreviewWidget instance."""
        return CommandPreviewWidget(
            risk_analyzer=mock_risk_analyzer,
            auto_hide_low_risk=True,
            id="test-preview"
        )

    def test_initialization(self, preview_widget, mock_risk_analyzer):
        """Test widget initializes correctly."""
        assert preview_widget.risk_analyzer == mock_risk_analyzer
        assert preview_widget.auto_hide_low_risk is True
        assert preview_widget.last_analysis is None
        assert preview_widget.analysis_task is None

    def test_initialization_creates_analyzer_if_none(self):
        """Test widget creates analyzer if not provided."""
        widget = CommandPreviewWidget()
        assert isinstance(widget.risk_analyzer, SQLRiskAnalyzer)

    def test_reactive_properties(self, preview_widget):
        """Test reactive properties are defined."""
        assert hasattr(preview_widget, 'current_command')
        assert hasattr(preview_widget, 'is_visible')

    @pytest.mark.asyncio
    async def test_update_preview_empty_command_hides(self, preview_widget):
        """Test empty command hides preview."""
        with patch.object(preview_widget, '_hide', new_callable=AsyncMock) as mock_hide:
            await preview_widget.update_preview("")

        mock_hide.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_preview_whitespace_command_hides(self, preview_widget):
        """Test whitespace-only command hides preview."""
        with patch.object(preview_widget, '_hide', new_callable=AsyncMock) as mock_hide:
            await preview_widget.update_preview("   \n\t  ")

        mock_hide.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_preview_sets_current_command(self, preview_widget):
        """Test update sets current command."""
        await preview_widget.update_preview("SELECT * FROM users")
        assert preview_widget.current_command == "SELECT * FROM users"

    @pytest.mark.asyncio
    async def test_update_preview_cancels_pending_task(self, preview_widget):
        """Test update cancels pending analysis task."""
        # Create a fake task
        fake_task = AsyncMock()
        fake_task.done = Mock(return_value=False)
        fake_task.cancel = Mock()
        preview_widget.analysis_task = fake_task

        await preview_widget.update_preview("SELECT * FROM users")

        fake_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_analysis_calls_analyzer(self, preview_widget, mock_risk_analyzer):
        """Test _run_analysis calls risk analyzer."""
        mock_risk_analyzer.analyze = Mock(return_value={
            'risk_level': RiskLevel.LOW.value,
            'warnings': [],
            'issues': []
        })

        with patch.object(preview_widget, '_update_display', new_callable=AsyncMock):
            with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
                mock_thread.return_value = mock_risk_analyzer.analyze.return_value

                await preview_widget._run_analysis("SELECT * FROM users")

        # Check that analyzer was called via to_thread
        mock_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_analysis_updates_last_analysis(self, preview_widget, mock_risk_analyzer):
        """Test _run_analysis updates last_analysis."""
        analysis_result = {
            'risk_level': RiskLevel.MEDIUM.value,
            'warnings': ['No WHERE clause'],
            'issues': []
        }

        with patch.object(preview_widget, '_update_display', new_callable=AsyncMock):
            with patch('asyncio.to_thread', new_callable=AsyncMock, return_value=analysis_result):
                await preview_widget._run_analysis("SELECT * FROM users")

        assert preview_widget.last_analysis == analysis_result

    @pytest.mark.asyncio
    async def test_run_analysis_handles_cancellation(self, preview_widget):
        """Test _run_analysis handles cancellation gracefully."""
        with patch('asyncio.to_thread', new_callable=AsyncMock, side_effect=asyncio.CancelledError):
            with pytest.raises(asyncio.CancelledError):
                await preview_widget._run_analysis("SELECT * FROM users")

    @pytest.mark.asyncio
    async def test_run_analysis_handles_errors(self, preview_widget):
        """Test _run_analysis handles errors."""
        with patch('asyncio.to_thread', new_callable=AsyncMock, side_effect=Exception("Test error")):
            with patch.object(preview_widget, '_display_error', new_callable=AsyncMock) as mock_error:
                await preview_widget._run_analysis("SELECT * FROM users")

        mock_error.assert_called_once_with("Test error")

    @pytest.mark.asyncio
    async def test_update_display_updates_command_text(self, preview_widget):
        """Test _update_display updates command text."""
        preview_widget.current_command = "SELECT * FROM users WHERE id = 1"

        mock_static = Mock()
        mock_static.update = Mock()

        analysis = {
            'risk_level': RiskLevel.LOW.value,
            'warnings': [],
            'issues': []
        }

        with patch.object(preview_widget, 'query_one', return_value=mock_static):
            with patch.object(preview_widget, 'risk_indicator', Mock(update_risk=Mock())):
                with patch.object(preview_widget, '_update_risk_classes'):
                    with patch.object(preview_widget, '_update_visibility', new_callable=AsyncMock):
                        await preview_widget._update_display(analysis)

        # Should be called with truncated command
        mock_static.update.assert_called_once()
        call_arg = str(mock_static.update.call_args)
        assert "SELECT * FROM users" in call_arg

    @pytest.mark.asyncio
    async def test_update_display_updates_risk_indicator(self, preview_widget):
        """Test _update_display updates risk indicator."""
        mock_indicator = Mock(spec=RiskIndicator)
        mock_indicator.update_risk = Mock()
        preview_widget.risk_indicator = mock_indicator

        analysis = {
            'risk_level': RiskLevel.HIGH.value,
            'warnings': ['Dangerous operation'],
            'issues': ['No WHERE clause']
        }

        with patch.object(preview_widget, 'query_one', return_value=Mock(update=Mock())):
            with patch.object(preview_widget, '_update_risk_classes'):
                with patch.object(preview_widget, '_update_visibility', new_callable=AsyncMock):
                    await preview_widget._update_display(analysis)

        mock_indicator.update_risk.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_display_shows_warnings(self, preview_widget):
        """Test _update_display shows warnings."""
        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        analysis = {
            'risk_level': RiskLevel.MEDIUM.value,
            'warnings': ['Warning 1', 'Warning 2'],
            'issues': []
        }

        with patch.object(preview_widget, 'query_one', side_effect=[
            Mock(update=Mock()),  # command-text
            mock_container,  # warnings-section
            Mock(update=Mock())  # impact-section
        ]):
            with patch.object(preview_widget, 'risk_indicator', Mock(update_risk=Mock())):
                with patch.object(preview_widget, '_update_risk_classes'):
                    with patch.object(preview_widget, '_update_visibility', new_callable=AsyncMock):
                        await preview_widget._update_display(analysis)

        # Should mount warnings
        assert mock_container.mount.call_count == 2

    @pytest.mark.asyncio
    async def test_update_display_shows_issues(self, preview_widget):
        """Test _update_display shows issues."""
        mock_container = Mock()
        mock_container.remove_children = Mock()
        mock_container.mount = Mock()

        analysis = {
            'risk_level': RiskLevel.HIGH.value,
            'warnings': [],
            'issues': ['Issue 1', 'Issue 2']
        }

        with patch.object(preview_widget, 'query_one', side_effect=[
            Mock(update=Mock()),  # command-text
            mock_container,  # warnings-section
            Mock(update=Mock())  # impact-section
        ]):
            with patch.object(preview_widget, 'risk_indicator', Mock(update_risk=Mock())):
                with patch.object(preview_widget, '_update_risk_classes'):
                    with patch.object(preview_widget, '_update_visibility', new_callable=AsyncMock):
                        await preview_widget._update_display(analysis)

        assert mock_container.mount.call_count == 2

    @pytest.mark.asyncio
    async def test_update_visibility_hides_low_risk_when_enabled(self, preview_widget):
        """Test auto-hide for LOW risk when enabled."""
        preview_widget.auto_hide_low_risk = True

        with patch.object(preview_widget, '_hide', new_callable=AsyncMock) as mock_hide:
            await preview_widget._update_visibility(RiskLevel.LOW.value)

        mock_hide.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_visibility_shows_high_risk(self, preview_widget):
        """Test always shows HIGH risk."""
        with patch.object(preview_widget, '_show', new_callable=AsyncMock) as mock_show:
            await preview_widget._update_visibility(RiskLevel.HIGH.value)

        mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_visibility_shows_low_risk_when_disabled(self):
        """Test shows LOW risk when auto_hide disabled."""
        widget = CommandPreviewWidget(auto_hide_low_risk=False)

        with patch.object(widget, '_show', new_callable=AsyncMock) as mock_show:
            await widget._update_visibility(RiskLevel.LOW.value)

        mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_sets_visible(self, preview_widget):
        """Test _show sets is_visible."""
        preview_widget.is_visible = False

        await preview_widget._show()

        assert preview_widget.is_visible is True

    @pytest.mark.asyncio
    async def test_hide_clears_state(self, preview_widget):
        """Test _hide clears state."""
        preview_widget.is_visible = True
        preview_widget.current_command = "SELECT * FROM users"
        preview_widget.last_analysis = {'risk_level': 'HIGH'}

        await preview_widget._hide()

        assert preview_widget.is_visible is False
        assert preview_widget.current_command == ""
        assert preview_widget.last_analysis is None

    @pytest.mark.asyncio
    async def test_display_error_shows_widget(self, preview_widget):
        """Test _display_error shows widget."""
        with patch.object(preview_widget, 'query_one', return_value=Mock(update=Mock())):
            with patch.object(preview_widget, 'risk_indicator', Mock(update_risk=Mock())):
                with patch.object(preview_widget, '_show', new_callable=AsyncMock) as mock_show:
                    await preview_widget._display_error("Test error")

        mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_display_error_sets_medium_risk(self, preview_widget):
        """Test _display_error sets MEDIUM risk."""
        mock_indicator = Mock(spec=RiskIndicator)
        mock_indicator.update_risk = Mock()
        preview_widget.risk_indicator = mock_indicator

        with patch.object(preview_widget, 'query_one', return_value=Mock(update=Mock())):
            with patch.object(preview_widget, '_show', new_callable=AsyncMock):
                await preview_widget._display_error("Test error")

        mock_indicator.update_risk.assert_called_once()
        call_args = mock_indicator.update_risk.call_args
        assert call_args[0][0] == RiskLevel.MEDIUM.value

    def test_get_risk_message_low(self, preview_widget):
        """Test risk message for LOW level."""
        msg = preview_widget._get_risk_message(RiskLevel.LOW.value)
        assert "safe" in msg.lower() or "read" in msg.lower()

    def test_get_risk_message_medium(self, preview_widget):
        """Test risk message for MEDIUM level."""
        msg = preview_widget._get_risk_message(RiskLevel.MEDIUM.value)
        assert "review" in msg.lower() or "caution" in msg.lower()

    def test_get_risk_message_high(self, preview_widget):
        """Test risk message for HIGH level."""
        msg = preview_widget._get_risk_message(RiskLevel.HIGH.value)
        assert "high" in msg.lower() or "risk" in msg.lower()

    def test_get_risk_message_critical(self, preview_widget):
        """Test risk message for CRITICAL level."""
        msg = preview_widget._get_risk_message(RiskLevel.CRITICAL.value)
        assert "critical" in msg.lower() or "destructive" in msg.lower()

    @pytest.mark.asyncio
    async def test_set_impact_estimation(self, preview_widget):
        """Test setting impact estimation."""
        mock_static = Mock()
        mock_static.update = Mock()

        with patch.object(preview_widget, 'query_one', return_value=mock_static):
            await preview_widget.set_impact_estimation(1500, 0.85)

        # Should include estimated rows and confidence
        call_arg = str(mock_static.update.call_args)
        assert "1500" in call_arg
        assert "85" in call_arg

    def test_get_last_analysis(self, preview_widget):
        """Test getting last analysis result."""
        analysis = {'risk_level': RiskLevel.MEDIUM.value}
        preview_widget.last_analysis = analysis

        result = preview_widget.get_last_analysis()

        assert result == analysis

    def test_get_last_analysis_none(self, preview_widget):
        """Test getting last analysis when none exists."""
        result = preview_widget.get_last_analysis()
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_hides_widget(self, preview_widget):
        """Test clear hides widget."""
        with patch.object(preview_widget, '_hide', new_callable=AsyncMock) as mock_hide:
            await preview_widget.clear()

        mock_hide.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cancels_task(self, preview_widget):
        """Test clear cancels pending task."""
        fake_task = AsyncMock()
        fake_task.done = Mock(return_value=False)
        fake_task.cancel = Mock()
        preview_widget.analysis_task = fake_task

        await preview_widget.clear()

        fake_task.cancel.assert_called_once()

    def test_css_defined(self):
        """Test CSS is defined."""
        assert hasattr(CommandPreviewWidget, 'CSS')
        assert isinstance(CommandPreviewWidget.CSS, str)
        assert 'CommandPreviewWidget' in CommandPreviewWidget.CSS

    def test_update_risk_classes(self, preview_widget):
        """Test _update_risk_classes updates CSS classes."""
        with patch.object(preview_widget, 'remove_class') as mock_remove:
            with patch.object(preview_widget, 'add_class') as mock_add:
                preview_widget._update_risk_classes(RiskLevel.HIGH.value)

        # Should remove all and add risk-high
        assert mock_remove.call_count >= 4
        mock_add.assert_called_with("risk-high")
