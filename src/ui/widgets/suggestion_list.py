"""Smart Suggestion List Widget for Context-Aware Autocomplete.

This module provides a dropdown autocomplete widget with visual score indicators
and smooth animations, integrated with the vector-based IntelligentCompleter.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from textual.widgets import OptionList
from textual.widgets.option_list import Option
from textual import events
from rich.text import Text
import asyncio
import logging

try:
    from ...vector.autocomplete import CompletionCandidate
except ImportError:
    from vector.autocomplete import CompletionCandidate

logger = logging.getLogger(__name__)


@dataclass
class SuggestionDisplay:
    """Display configuration for a suggestion."""
    text: str
    score: float
    category: str
    icon: str
    shortcut: Optional[str] = None


class SmartSuggestionList(OptionList):
    """Dropdown autocomplete widget with relevance scores.

    Features:
    - Displays up to 10 suggestions with score indicators
    - Keyboard navigation (Up/Down/Enter/Esc)
    - Visual score representation (stars or progress bars)
    - Smooth show/hide animations
    - Integration with ContextAwareSuggestionEngine

    Attributes:
        max_suggestions: Maximum number of suggestions to display (default: 10)
        show_scores: Whether to display score indicators (default: True)
        score_style: Style for score display ('stars' or 'bar')
    """

    # CSS classes for styling
    DEFAULT_CSS = """
    SmartSuggestionList {
        display: none;
        height: auto;
        max-height: 15;
        background: $panel;
        border: solid $primary;
        padding: 0 1;
    }

    SmartSuggestionList.visible {
        display: block;
    }

    SmartSuggestionList > .option-list--option-highlighted {
        background: $accent;
    }

    SmartSuggestionList .score-high {
        color: $success;
    }

    SmartSuggestionList .score-medium {
        color: $warning;
    }

    SmartSuggestionList .score-low {
        color: $error;
    }
    """

    def __init__(
        self,
        max_suggestions: int = 10,
        show_scores: bool = True,
        score_style: str = 'stars',
        **kwargs
    ):
        """Initialize SmartSuggestionList.

        Args:
            max_suggestions: Maximum suggestions to display
            show_scores: Whether to show score indicators
            score_style: Score display style ('stars' or 'bar')
            **kwargs: Additional OptionList arguments
        """
        super().__init__(**kwargs)
        self.max_suggestions = max_suggestions
        self.show_scores = show_scores
        self.score_style = score_style
        self._suggestions: List[CompletionCandidate] = []
        self._visible = False

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.add_class("suggestion-list")

    async def update_suggestions(
        self,
        candidates: List[CompletionCandidate]
    ) -> None:
        """Update the suggestion list with new candidates.

        Args:
            candidates: List of completion candidates from the engine
        """
        # Store suggestions
        self._suggestions = candidates[:self.max_suggestions]

        # Clear existing options
        self.clear_options()

        if not self._suggestions:
            await self.hide()
            return

        # Create options from candidates
        options = []
        for idx, candidate in enumerate(self._suggestions):
            display = self._format_suggestion(candidate, idx)
            option = Option(display, id=str(idx))
            options.append(option)

        # Add options to list
        self.add_options(options)

        # Show the list with animation
        await self.show()

        # Auto-select first option
        if options:
            self.highlighted = 0

    def _format_suggestion(
        self,
        candidate: CompletionCandidate,
        index: int
    ) -> Text:
        """Format a suggestion for display.

        Args:
            candidate: Completion candidate
            index: Suggestion index

        Returns:
            Formatted Rich Text object
        """
        text = Text()

        # Add category icon
        icon = self._get_category_icon(candidate.source)
        text.append(f"{icon} ", style="bold")

        # Add suggestion text
        text.append(candidate.text, style="white")

        # Add score indicator if enabled
        if self.show_scores:
            score_display = self._format_score(candidate.score)
            score_style = self._get_score_style(candidate.score)
            text.append(f" {score_display}", style=score_style)

        # Add keyboard shortcut hint
        if index < 9:
            shortcut = f" [{index + 1}]"
            text.append(shortcut, style="dim")

        return text

    def _get_category_icon(self, source: str) -> str:
        """Get icon for suggestion category.

        Args:
            source: Suggestion source type

        Returns:
            Unicode icon character
        """
        icons = {
            'vector': '🔍',     # Vector similarity
            'pattern': '📋',    # SQL pattern
            'syntax': '⚙️',     # Syntax completion
            'history': '🕐',    # Command history
            'table': '📊',      # Database table
            'column': '📝',     # Database column
            'keyword': '🔑',    # SQL keyword
        }
        return icons.get(source, '●')

    def _format_score(self, score: float) -> str:
        """Format score for display.

        Args:
            score: Relevance score (0.0 - 1.0)

        Returns:
            Formatted score string
        """
        if self.score_style == 'stars':
            # Convert to 0-5 stars
            stars = int(score * 5)
            return '⭐' * stars
        else:  # bar style
            # Convert to percentage bar
            percentage = int(score * 100)
            return f"{percentage}%"

    def _get_score_style(self, score: float) -> str:
        """Get style class for score display.

        Args:
            score: Relevance score (0.0 - 1.0)

        Returns:
            CSS class name
        """
        if score >= 0.8:
            return "score-high"
        elif score >= 0.5:
            return "score-medium"
        else:
            return "score-low"

    async def show(self) -> None:
        """Show the suggestion list with animation."""
        if not self._visible:
            self.remove_class("hidden")
            self.add_class("visible")
            self._visible = True
            logger.debug("Suggestion list shown")

    async def hide(self) -> None:
        """Hide the suggestion list with animation."""
        if self._visible:
            self.remove_class("visible")
            self.add_class("hidden")
            self._visible = False
            logger.debug("Suggestion list hidden")

    def get_selected(self) -> Optional[str]:
        """Get the currently selected suggestion text.

        Returns:
            Selected suggestion text or None if nothing selected
        """
        if self.highlighted is not None and self._suggestions:
            if 0 <= self.highlighted < len(self._suggestions):
                return self._suggestions[self.highlighted].text
        return None

    def get_selected_candidate(self) -> Optional[CompletionCandidate]:
        """Get the currently selected completion candidate.

        Returns:
            Selected CompletionCandidate or None if nothing selected
        """
        if self.highlighted is not None and self._suggestions:
            if 0 <= self.highlighted < len(self._suggestions):
                return self._suggestions[self.highlighted]
        return None

    def clear(self) -> None:
        """Clear all suggestions and hide the list."""
        self._suggestions = []
        self.clear_options()
        asyncio.create_task(self.hide())

    async def on_key(self, event: events.Key) -> None:
        """Handle keyboard events.

        Args:
            event: Key event
        """
        if not self._visible:
            return

        if event.key == "escape":
            # Hide suggestions on Escape
            await self.hide()
            event.prevent_default()
        elif event.key == "enter":
            # Accept selected suggestion
            if self.get_selected():
                # Let parent handle the selection
                event.prevent_default()
        elif event.key == "up":
            # Navigate up
            if self.highlighted is not None and self.highlighted > 0:
                self.highlighted -= 1
            event.prevent_default()
        elif event.key == "down":
            # Navigate down
            if self.highlighted is not None and self.highlighted < len(self._suggestions) - 1:
                self.highlighted += 1
            event.prevent_default()
        elif event.key.isdigit() and event.key != "0":
            # Number key shortcuts (1-9)
            index = int(event.key) - 1
            if 0 <= index < len(self._suggestions):
                self.highlighted = index
                # Let parent handle the selection
                event.prevent_default()

    @property
    def is_visible(self) -> bool:
        """Check if suggestion list is currently visible.

        Returns:
            True if visible, False otherwise
        """
        return self._visible

    @property
    def suggestion_count(self) -> int:
        """Get the number of current suggestions.

        Returns:
            Number of suggestions
        """
        return len(self._suggestions)
