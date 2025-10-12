"""
Tests for SmartSuggestionList Widget (src/ui/widgets/suggestion_list.py)

Tests suggestion display, keyboard navigation, score formatting, and event handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from textual.widgets.option_list import Option
from textual import events

from src.ui.widgets.suggestion_list import (
    SmartSuggestionList,
    SuggestionDisplay
)
from src.vector.autocomplete import CompletionCandidate


class TestSuggestionDisplay:
    """Test suite for SuggestionDisplay dataclass."""

    def test_suggestion_display_creation(self):
        """Test creating suggestion display."""
        display = SuggestionDisplay(
            text="SELECT * FROM users",
            score=0.95,
            category="vector",
            icon="🔍",
            shortcut="1"
        )

        assert display.text == "SELECT * FROM users"
        assert display.score == 0.95
        assert display.category == "vector"
        assert display.icon == "🔍"
        assert display.shortcut == "1"

    def test_suggestion_display_optional_shortcut(self):
        """Test suggestion display without shortcut."""
        display = SuggestionDisplay(
            text="users",
            score=0.85,
            category="table",
            icon="📊"
        )

        assert display.shortcut is None


class TestSmartSuggestionList:
    """Test suite for SmartSuggestionList widget."""

    @pytest.fixture
    def suggestion_list(self):
        """Create SmartSuggestionList instance for testing."""
        return SmartSuggestionList(
            max_suggestions=10,
            show_scores=True,
            score_style='stars'
        )

    @pytest.fixture
    def sample_candidates(self):
        """Create sample completion candidates."""
        return [
            CompletionCandidate(
                text="SELECT * FROM users",
                score=0.95,
                source="vector",
                metadata={"type": "query"}
            ),
            CompletionCandidate(
                text="users",
                score=0.90,
                source="table",
                metadata={"type": "table"}
            ),
            CompletionCandidate(
                text="user_id",
                score=0.85,
                source="column",
                metadata={"type": "column", "table": "users"}
            ),
            CompletionCandidate(
                text="SELECT",
                score=0.80,
                source="keyword",
                metadata={"type": "keyword"}
            ),
            CompletionCandidate(
                text="COUNT(*)",
                score=0.75,
                source="function",
                metadata={"type": "function"}
            )
        ]

    def test_initialization(self, suggestion_list):
        """Test suggestion list initializes correctly."""
        assert suggestion_list.max_suggestions == 10
        assert suggestion_list.show_scores is True
        assert suggestion_list.score_style == 'stars'
        assert suggestion_list._suggestions == []
        assert suggestion_list._visible is False

    def test_initialization_custom_params(self):
        """Test initialization with custom parameters."""
        widget = SmartSuggestionList(
            max_suggestions=5,
            show_scores=False,
            score_style='bar'
        )

        assert widget.max_suggestions == 5
        assert widget.show_scores is False
        assert widget.score_style == 'bar'

    @pytest.mark.asyncio
    async def test_update_suggestions_displays_candidates(self, suggestion_list, sample_candidates):
        """Test updating suggestions displays candidates."""
        with patch.object(suggestion_list, 'add_options') as mock_add_options:
            with patch.object(suggestion_list, 'clear_options'):
                with patch.object(suggestion_list, 'show', new_callable=AsyncMock):
                    await suggestion_list.update_suggestions(sample_candidates)

        assert len(suggestion_list._suggestions) == 5
        assert mock_add_options.called

    @pytest.mark.asyncio
    async def test_update_suggestions_limits_max(self, suggestion_list):
        """Test suggestions are limited to max_suggestions."""
        # Create 15 candidates
        candidates = [
            CompletionCandidate(f"item_{i}", 0.9 - i*0.05, "vector", {})
            for i in range(15)
        ]

        with patch.object(suggestion_list, 'add_options'):
            with patch.object(suggestion_list, 'clear_options'):
                with patch.object(suggestion_list, 'show', new_callable=AsyncMock):
                    await suggestion_list.update_suggestions(candidates)

        # Should only keep max_suggestions (10)
        assert len(suggestion_list._suggestions) == 10

    @pytest.mark.asyncio
    async def test_update_suggestions_empty_hides_list(self, suggestion_list):
        """Test empty suggestions hide the list."""
        with patch.object(suggestion_list, 'hide', new_callable=AsyncMock) as mock_hide:
            with patch.object(suggestion_list, 'clear_options'):
                await suggestion_list.update_suggestions([])

        mock_hide.assert_called_once()
        assert len(suggestion_list._suggestions) == 0

    def test_format_suggestion_includes_icon(self, suggestion_list):
        """Test suggestion formatting includes category icon."""
        candidate = CompletionCandidate("users", 0.90, "table", {})

        result = suggestion_list._format_suggestion(candidate, 0)

        # Should contain table icon
        assert "📊" in str(result)

    def test_format_suggestion_includes_text(self, suggestion_list):
        """Test suggestion formatting includes text."""
        candidate = CompletionCandidate("users", 0.90, "table", {})

        result = suggestion_list._format_suggestion(candidate, 0)

        assert "users" in str(result)

    def test_format_suggestion_includes_score(self, suggestion_list):
        """Test suggestion formatting includes score when enabled."""
        candidate = CompletionCandidate("users", 0.90, "table", {})

        result = suggestion_list._format_suggestion(candidate, 0)

        # Should contain star rating
        assert "⭐" in str(result)

    def test_format_suggestion_no_score_when_disabled(self):
        """Test suggestion formatting without scores."""
        widget = SmartSuggestionList(show_scores=False)
        candidate = CompletionCandidate("users", 0.90, "table", {})

        result = widget._format_suggestion(candidate, 0)

        # Should not contain star rating
        assert "⭐" not in str(result)

    def test_format_suggestion_includes_shortcut(self, suggestion_list):
        """Test suggestion includes keyboard shortcut."""
        candidate = CompletionCandidate("users", 0.90, "table", {})

        result = suggestion_list._format_suggestion(candidate, 0)

        # Index 0 should get shortcut [1]
        assert "[1]" in str(result)

    def test_format_suggestion_no_shortcut_after_nine(self, suggestion_list):
        """Test suggestions after index 8 have no shortcut."""
        candidate = CompletionCandidate("users", 0.90, "table", {})

        result = suggestion_list._format_suggestion(candidate, 10)

        # Index 10 should not get shortcut
        assert "[" not in str(result) or "[1" not in str(result)

    def test_get_category_icon_vector(self, suggestion_list):
        """Test getting icon for vector source."""
        icon = suggestion_list._get_category_icon('vector')
        assert icon == '🔍'

    def test_get_category_icon_table(self, suggestion_list):
        """Test getting icon for table source."""
        icon = suggestion_list._get_category_icon('table')
        assert icon == '📊'

    def test_get_category_icon_column(self, suggestion_list):
        """Test getting icon for column source."""
        icon = suggestion_list._get_category_icon('column')
        assert icon == '📝'

    def test_get_category_icon_keyword(self, suggestion_list):
        """Test getting icon for keyword source."""
        icon = suggestion_list._get_category_icon('keyword')
        assert icon == '🔑'

    def test_get_category_icon_unknown(self, suggestion_list):
        """Test getting default icon for unknown source."""
        icon = suggestion_list._get_category_icon('unknown')
        assert icon == '●'

    def test_format_score_stars_style(self, suggestion_list):
        """Test score formatting with stars style."""
        # High score (0.9) should give 4 stars
        result = suggestion_list._format_score(0.9)
        assert result == '⭐⭐⭐⭐'

        # Perfect score (1.0) should give 5 stars
        result = suggestion_list._format_score(1.0)
        assert result == '⭐⭐⭐⭐⭐'

        # Low score (0.2) should give 1 star
        result = suggestion_list._format_score(0.2)
        assert result == '⭐'

        # Zero score should give 0 stars
        result = suggestion_list._format_score(0.0)
        assert result == ''

    def test_format_score_bar_style(self):
        """Test score formatting with bar style."""
        widget = SmartSuggestionList(score_style='bar')

        result = widget._format_score(0.85)
        assert result == '85%'

        result = widget._format_score(1.0)
        assert result == '100%'

        result = widget._format_score(0.0)
        assert result == '0%'

    def test_get_score_style_high(self, suggestion_list):
        """Test score style for high scores."""
        style = suggestion_list._get_score_style(0.9)
        assert style == "score-high"

    def test_get_score_style_medium(self, suggestion_list):
        """Test score style for medium scores."""
        style = suggestion_list._get_score_style(0.6)
        assert style == "score-medium"

    def test_get_score_style_low(self, suggestion_list):
        """Test score style for low scores."""
        style = suggestion_list._get_score_style(0.3)
        assert style == "score-low"

    @pytest.mark.asyncio
    async def test_show_makes_visible(self, suggestion_list):
        """Test show() makes list visible."""
        assert suggestion_list._visible is False

        await suggestion_list.show()

        assert suggestion_list._visible is True

    @pytest.mark.asyncio
    async def test_hide_makes_invisible(self, suggestion_list):
        """Test hide() makes list invisible."""
        await suggestion_list.show()
        assert suggestion_list._visible is True

        await suggestion_list.hide()

        assert suggestion_list._visible is False

    def test_get_selected_returns_text(self, suggestion_list, sample_candidates):
        """Test getting selected suggestion text."""
        suggestion_list._suggestions = sample_candidates
        suggestion_list.highlighted = 1

        result = suggestion_list.get_selected()

        assert result == "users"

    def test_get_selected_returns_none_when_empty(self, suggestion_list):
        """Test getting selected when no suggestions."""
        result = suggestion_list.get_selected()
        assert result is None

    def test_get_selected_returns_none_when_invalid_index(self, suggestion_list, sample_candidates):
        """Test getting selected with invalid index."""
        suggestion_list._suggestions = sample_candidates
        suggestion_list.highlighted = 999

        result = suggestion_list.get_selected()
        assert result is None

    def test_get_selected_candidate_returns_object(self, suggestion_list, sample_candidates):
        """Test getting selected candidate object."""
        suggestion_list._suggestions = sample_candidates
        suggestion_list.highlighted = 2

        result = suggestion_list.get_selected_candidate()

        assert isinstance(result, CompletionCandidate)
        assert result.text == "user_id"

    def test_is_visible_property(self, suggestion_list):
        """Test is_visible property."""
        assert suggestion_list.is_visible is False

        suggestion_list._visible = True
        assert suggestion_list.is_visible is True

    def test_suggestion_count_property(self, suggestion_list, sample_candidates):
        """Test suggestion_count property."""
        assert suggestion_list.suggestion_count == 0

        suggestion_list._suggestions = sample_candidates
        assert suggestion_list.suggestion_count == 5

    def test_clear_removes_suggestions(self, suggestion_list, sample_candidates):
        """Test clear removes all suggestions."""
        with patch.object(suggestion_list, 'clear_options'):
            suggestion_list._suggestions = sample_candidates
            suggestion_list._visible = True

            suggestion_list.clear()

            assert suggestion_list._suggestions == []

    @pytest.mark.asyncio
    async def test_on_key_escape_hides_list(self, suggestion_list):
        """Test Escape key hides suggestion list."""
        await suggestion_list.show()
        assert suggestion_list._visible is True

        event = Mock(spec=events.Key)
        event.key = "escape"
        event.prevent_default = Mock()

        await suggestion_list.on_key(event)

        assert suggestion_list._visible is False
        event.prevent_default.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_key_up_navigates(self, suggestion_list, sample_candidates):
        """Test Up key navigates selection."""
        suggestion_list._suggestions = sample_candidates
        suggestion_list._visible = True
        suggestion_list.highlighted = 2

        event = Mock(spec=events.Key)
        event.key = "up"
        event.prevent_default = Mock()

        await suggestion_list.on_key(event)

        assert suggestion_list.highlighted == 1
        event.prevent_default.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_key_down_navigates(self, suggestion_list, sample_candidates):
        """Test Down key navigates selection."""
        suggestion_list._suggestions = sample_candidates
        suggestion_list._visible = True
        suggestion_list.highlighted = 1

        event = Mock(spec=events.Key)
        event.key = "down"
        event.prevent_default = Mock()

        await suggestion_list.on_key(event)

        assert suggestion_list.highlighted == 2
        event.prevent_default.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_key_number_selects_shortcut(self, suggestion_list, sample_candidates):
        """Test number key selects corresponding suggestion."""
        suggestion_list._suggestions = sample_candidates
        suggestion_list._visible = True

        event = Mock(spec=events.Key)
        event.key = "3"
        event.prevent_default = Mock()

        await suggestion_list.on_key(event)

        # Key "3" should select index 2
        assert suggestion_list.highlighted == 2
        event.prevent_default.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_key_ignores_when_not_visible(self, suggestion_list):
        """Test key events ignored when list not visible."""
        event = Mock(spec=events.Key)
        event.key = "down"
        event.prevent_default = Mock()

        await suggestion_list.on_key(event)

        # Should not call prevent_default
        event.prevent_default.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_key_enter_with_selection(self, suggestion_list, sample_candidates):
        """Test Enter key with selection."""
        suggestion_list._suggestions = sample_candidates
        suggestion_list._visible = True
        suggestion_list.highlighted = 0

        event = Mock(spec=events.Key)
        event.key = "enter"
        event.prevent_default = Mock()

        await suggestion_list.on_key(event)

        event.prevent_default.assert_called_once()

    def test_css_classes_defined(self, suggestion_list):
        """Test CSS classes are defined."""
        assert hasattr(SmartSuggestionList, 'DEFAULT_CSS')
        assert isinstance(SmartSuggestionList.DEFAULT_CSS, str)
        assert 'SmartSuggestionList' in SmartSuggestionList.DEFAULT_CSS

    @pytest.mark.asyncio
    async def test_multiple_updates_replace_suggestions(self, suggestion_list, sample_candidates):
        """Test multiple updates replace previous suggestions."""
        with patch.object(suggestion_list, 'add_options'):
            with patch.object(suggestion_list, 'clear_options'):
                with patch.object(suggestion_list, 'show', new_callable=AsyncMock):
                    # First update
                    await suggestion_list.update_suggestions(sample_candidates[:2])
                    assert len(suggestion_list._suggestions) == 2

                    # Second update
                    await suggestion_list.update_suggestions(sample_candidates[2:4])
                    assert len(suggestion_list._suggestions) == 2
                    assert suggestion_list._suggestions[0].text == "user_id"

    @pytest.mark.asyncio
    async def test_auto_select_first_option(self, suggestion_list, sample_candidates):
        """Test first option is auto-selected."""
        with patch.object(suggestion_list, 'add_options'):
            with patch.object(suggestion_list, 'clear_options'):
                with patch.object(suggestion_list, 'show', new_callable=AsyncMock):
                    await suggestion_list.update_suggestions(sample_candidates)

                    # Should auto-select first option
                    assert suggestion_list.highlighted == 0
