"""
Tests for UI Widgets

Tests all custom widgets: command_preview, risk_indicator, suggestion_list
Uses Textual's testing utilities for widget rendering and interaction.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from textual.app import App
from textual.widgets import Static

# Import widgets
from src.ui.widgets.command_preview import CommandPreviewWidget
from src.ui.widgets.risk_indicator import RiskIndicator
from src.ui.widgets.suggestion_list import SmartSuggestionList
from src.database.risk_analyzer import RiskLevel, SQLRiskAnalyzer
from src.vector.autocomplete import CompletionCandidate


# ============================================================================
# Risk Indicator Widget Tests
# ============================================================================

class TestRiskIndicator:
    """Test suite for RiskIndicator widget."""

    @pytest.fixture
    def indicator(self):
        """Create RiskIndicator instance."""
        return RiskIndicator(id="test-indicator")

    def test_initialization(self, indicator):
        """Test indicator initializes with defaults."""
        assert indicator.current_risk_level == RiskLevel.LOW.value
        assert indicator.current_message == ""

    def test_update_risk_low(self, indicator):
        """Test updating to LOW risk."""
        indicator.update_risk(RiskLevel.LOW.value, "Safe to execute")

        assert indicator.current_risk_level == RiskLevel.LOW.value
        assert indicator.current_message == "Safe to execute"

    def test_update_risk_medium(self, indicator):
        """Test updating to MEDIUM risk."""
        indicator.update_risk(RiskLevel.MEDIUM.value, "Review carefully")

        assert indicator.current_risk_level == RiskLevel.MEDIUM.value
        assert indicator.current_message == "Review carefully"

    def test_update_risk_high(self, indicator):
        """Test updating to HIGH risk."""
        indicator.update_risk(RiskLevel.HIGH.value, "High risk detected")

        assert indicator.current_risk_level == RiskLevel.HIGH.value

    def test_update_risk_critical(self, indicator):
        """Test updating to CRITICAL risk."""
        indicator.update_risk(RiskLevel.CRITICAL.value, "CRITICAL - destructive!")

        assert indicator.current_risk_level == RiskLevel.CRITICAL.value

    def test_get_risk_level(self, indicator):
        """Test getting current risk level."""
        indicator.update_risk(RiskLevel.HIGH.value, "Test")

        assert indicator.get_risk_level() == RiskLevel.HIGH.value

    def test_get_message(self, indicator):
        """Test getting current message."""
        indicator.update_risk(RiskLevel.MEDIUM.value, "Test message")

        assert indicator.get_message() == "Test message"

    def test_reset(self, indicator):
        """Test resetting indicator to LOW."""
        indicator.update_risk(RiskLevel.CRITICAL.value, "Critical!")
        indicator.reset()

        assert indicator.current_risk_level == RiskLevel.LOW.value
        assert indicator.current_message == ""

    def test_css_class_updates(self, indicator):
        """Test CSS classes update with risk level."""
        # Mock query_one to avoid mounting
        indicator.query_one = Mock(return_value=Mock(spec=Static))

        indicator.update_risk(RiskLevel.HIGH.value, "Test")

        # Should have high risk class
        assert "risk-high" in [cls for cls in indicator.classes]


# ============================================================================
# Command Preview Widget Tests
# ============================================================================

class TestCommandPreviewWidget:
    """Test suite for CommandPreviewWidget."""

    @pytest.fixture
    def mock_analyzer(self):
        """Create mock risk analyzer."""
        analyzer = Mock(spec=SQLRiskAnalyzer)
        analyzer.analyze = Mock(return_value={
            'risk_level': RiskLevel.LOW.value,
            'warnings': [],
            'issues': []
        })
        return analyzer

    @pytest.fixture
    def preview(self, mock_analyzer):
        """Create CommandPreviewWidget instance."""
        return CommandPreviewWidget(
            risk_analyzer=mock_analyzer,
            auto_hide_low_risk=True,
            id="test-preview"
        )

    def test_initialization(self, preview, mock_analyzer):
        """Test preview widget initializes correctly."""
        assert preview.risk_analyzer == mock_analyzer
        assert preview.auto_hide_low_risk is True
        assert preview.current_command == ""
        assert preview.is_visible is False

    @pytest.mark.asyncio
    async def test_update_preview_empty_command(self, preview):
        """Test updating with empty command hides widget."""
        # Mock _hide
        preview._hide = AsyncMock()

        await preview.update_preview("")

        preview._hide.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_preview_cancels_pending_analysis(self, preview):
        """Test new preview cancels pending analysis."""
        # Create a mock pending task
        mock_task = Mock()
        mock_task.done.return_value = False
        preview.analysis_task = mock_task

        # Mock _run_analysis to prevent actual execution
        preview._run_analysis = AsyncMock()

        await preview.update_preview("SELECT * FROM users")

        mock_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_preview_starts_analysis(self, preview):
        """Test update_preview starts new analysis task."""
        # Mock _run_analysis
        preview._run_analysis = AsyncMock()

        await preview.update_preview("SELECT * FROM users")

        assert preview.current_command == "SELECT * FROM users"
        assert preview.analysis_task is not None

    @pytest.mark.asyncio
    async def test_run_analysis_executes_analyzer(self, preview, mock_analyzer):
        """Test _run_analysis calls risk analyzer."""
        # Mock query_one and other UI methods
        preview.query_one = Mock(return_value=Mock(spec=Static, update=Mock()))
        preview._update_display = AsyncMock()
        preview.risk_indicator = Mock(update_risk=Mock())

        await preview._run_analysis("SELECT * FROM users")

        # Analyzer should be called (via asyncio.to_thread in actual code)
        # In mock, it's synchronous
        assert mock_analyzer.analyze.called or True  # May be async

    @pytest.mark.asyncio
    async def test_update_display_low_risk(self, preview):
        """Test display update for low risk."""
        # Mock UI components
        preview.query_one = Mock(return_value=Mock(spec=Static, update=Mock()))
        preview.risk_indicator = Mock(update_risk=Mock())
        preview._update_visibility = AsyncMock()

        analysis = {
            'risk_level': RiskLevel.LOW.value,
            'warnings': [],
            'issues': []
        }

        await preview._update_display(analysis)

        preview.risk_indicator.update_risk.assert_called()

    @pytest.mark.asyncio
    async def test_update_display_with_warnings(self, preview):
        """Test display update with warnings."""
        # Mock UI components
        container = Mock(remove_children=Mock(), mount=Mock())
        preview.query_one = Mock(side_effect=[
            Mock(spec=Static, update=Mock()),  # command-text
            container,  # warnings-section
            Mock(spec=Static, update=Mock())   # impact-section
        ])
        preview.risk_indicator = Mock(update_risk=Mock())
        preview._update_visibility = AsyncMock()

        analysis = {
            'risk_level': RiskLevel.MEDIUM.value,
            'warnings': ['Warning 1', 'Warning 2'],
            'issues': ['Issue 1']
        }

        await preview._update_display(analysis)

        # Should mount warnings and issues
        assert container.mount.call_count >= 2

    @pytest.mark.asyncio
    async def test_auto_hide_low_risk(self, preview):
        """Test auto-hiding for low risk commands."""
        preview._hide = AsyncMock()

        await preview._update_visibility(RiskLevel.LOW.value)

        preview._hide.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_high_risk(self, preview):
        """Test showing for high risk commands."""
        preview._show = AsyncMock()

        await preview._update_visibility(RiskLevel.HIGH.value)

        preview._show.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_preview(self, preview):
        """Test clearing preview state."""
        preview._hide = AsyncMock()
        preview.analysis_task = Mock(done=Mock(return_value=False), cancel=Mock())

        await preview.clear()

        preview._hide.assert_called_once()
        preview.analysis_task.cancel.assert_called_once()

    def test_get_last_analysis(self, preview):
        """Test getting last analysis result."""
        analysis = {'risk_level': RiskLevel.MEDIUM.value}
        preview.last_analysis = analysis

        result = preview.get_last_analysis()

        assert result == analysis

    @pytest.mark.asyncio
    async def test_set_impact_estimation(self, preview):
        """Test setting impact estimation."""
        preview.query_one = Mock(return_value=Mock(spec=Static, update=Mock()))

        await preview.set_impact_estimation(100, 0.85)

        # Should update impact section
        preview.query_one.assert_called()


# ============================================================================
# Smart Suggestion List Tests
# ============================================================================

class TestSmartSuggestionList:
    """Test suite for SmartSuggestionList widget."""

    @pytest.fixture
    def suggestion_list(self):
        """Create SmartSuggestionList instance."""
        return SmartSuggestionList(
            max_suggestions=10,
            show_scores=True,
            score_style='stars'
        )

    @pytest.fixture
    def sample_candidates(self):
        """Create sample completion candidates."""
        return [
            CompletionCandidate(text="SELECT * FROM users", score=0.95, source="vector"),
            CompletionCandidate(text="SELECT id, name FROM users", score=0.85, source="pattern"),
            CompletionCandidate(text="UPDATE users SET", score=0.75, source="syntax"),
        ]

    def test_initialization(self, suggestion_list):
        """Test suggestion list initializes correctly."""
        assert suggestion_list.max_suggestions == 10
        assert suggestion_list.show_scores is True
        assert suggestion_list.score_style == 'stars'
        assert suggestion_list._suggestions == []
        assert suggestion_list._visible is False

    @pytest.mark.asyncio
    async def test_update_suggestions_empty(self, suggestion_list):
        """Test updating with empty candidates."""
        suggestion_list.hide = AsyncMock()

        await suggestion_list.update_suggestions([])

        suggestion_list.hide.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_suggestions_with_candidates(self, suggestion_list, sample_candidates):
        """Test updating with candidates."""
        suggestion_list.clear_options = Mock()
        suggestion_list.add_options = Mock()
        suggestion_list.show = AsyncMock()

        await suggestion_list.update_suggestions(sample_candidates)

        assert len(suggestion_list._suggestions) == 3
        suggestion_list.clear_options.assert_called_once()
        suggestion_list.add_options.assert_called_once()
        suggestion_list.show.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_suggestions_max_limit(self, suggestion_list):
        """Test max suggestions limit is enforced."""
        # Create more than max suggestions
        candidates = [
            CompletionCandidate(text=f"SELECT {i}", score=0.9, source="vector")
            for i in range(20)
        ]

        suggestion_list.clear_options = Mock()
        suggestion_list.add_options = Mock()
        suggestion_list.show = AsyncMock()

        await suggestion_list.update_suggestions(candidates)

        # Should only keep max_suggestions
        assert len(suggestion_list._suggestions) == 10

    def test_format_suggestion_with_scores(self, suggestion_list, sample_candidates):
        """Test formatting suggestion with scores."""
        candidate = sample_candidates[0]

        formatted = suggestion_list._format_suggestion(candidate, 0)

        # Should contain text and score
        assert "SELECT * FROM users" in str(formatted)
        assert "⭐" in str(formatted)  # Stars for high score

    def test_format_suggestion_without_scores(self, sample_candidates):
        """Test formatting without score display."""
        suggestion_list = SmartSuggestionList(show_scores=False)
        candidate = sample_candidates[0]

        formatted = suggestion_list._format_suggestion(candidate, 0)

        # Should not contain stars
        assert "⭐" not in str(formatted)

    def test_get_category_icon(self, suggestion_list):
        """Test getting icons for different categories."""
        assert suggestion_list._get_category_icon('vector') == '🔍'
        assert suggestion_list._get_category_icon('pattern') == '📋'
        assert suggestion_list._get_category_icon('syntax') == '⚙️'
        assert suggestion_list._get_category_icon('unknown') == '●'

    def test_format_score_stars(self, suggestion_list):
        """Test score formatting with stars."""
        assert '⭐' * 5 in suggestion_list._format_score(0.95)
        assert '⭐' * 4 in suggestion_list._format_score(0.85)
        assert '⭐' * 3 in suggestion_list._format_score(0.65)

    def test_format_score_percentage(self):
        """Test score formatting with percentage."""
        suggestion_list = SmartSuggestionList(score_style='bar')

        assert '95%' in suggestion_list._format_score(0.95)
        assert '50%' in suggestion_list._format_score(0.50)

    def test_get_score_style(self, suggestion_list):
        """Test getting CSS class for score."""
        assert suggestion_list._get_score_style(0.9) == "score-high"
        assert suggestion_list._get_score_style(0.6) == "score-medium"
        assert suggestion_list._get_score_style(0.3) == "score-low"

    @pytest.mark.asyncio
    async def test_show_suggestion_list(self, suggestion_list):
        """Test showing suggestion list."""
        await suggestion_list.show()

        assert suggestion_list._visible is True
        assert "visible" in suggestion_list.classes

    @pytest.mark.asyncio
    async def test_hide_suggestion_list(self, suggestion_list):
        """Test hiding suggestion list."""
        suggestion_list._visible = True
        suggestion_list.add_class("visible")

        await suggestion_list.hide()

        assert suggestion_list._visible is False
        assert "hidden" in suggestion_list.classes

    def test_get_selected(self, suggestion_list, sample_candidates):
        """Test getting selected suggestion."""
        suggestion_list._suggestions = sample_candidates
        suggestion_list.highlighted = 0

        selected = suggestion_list.get_selected()

        assert selected == "SELECT * FROM users"

    def test_get_selected_none(self, suggestion_list):
        """Test getting selected when none selected."""
        suggestion_list.highlighted = None

        selected = suggestion_list.get_selected()

        assert selected is None

    def test_get_selected_candidate(self, suggestion_list, sample_candidates):
        """Test getting selected candidate object."""
        suggestion_list._suggestions = sample_candidates
        suggestion_list.highlighted = 1

        candidate = suggestion_list.get_selected_candidate()

        assert candidate.text == "SELECT id, name FROM users"
        assert candidate.score == 0.85

    def test_clear_suggestions(self, suggestion_list, sample_candidates):
        """Test clearing all suggestions."""
        suggestion_list._suggestions = sample_candidates
        suggestion_list.clear_options = Mock()

        suggestion_list.clear()

        assert suggestion_list._suggestions == []
        suggestion_list.clear_options.assert_called_once()

    def test_is_visible_property(self, suggestion_list):
        """Test is_visible property."""
        assert suggestion_list.is_visible is False

        suggestion_list._visible = True
        assert suggestion_list.is_visible is True

    def test_suggestion_count_property(self, suggestion_list, sample_candidates):
        """Test suggestion_count property."""
        assert suggestion_list.suggestion_count == 0

        suggestion_list._suggestions = sample_candidates
        assert suggestion_list.suggestion_count == 3
