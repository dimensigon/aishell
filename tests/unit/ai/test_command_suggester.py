"""
Tests for Command Suggester
"""

import pytest
from datetime import datetime, timedelta

from src.ai.command_suggester import (
    CommandSuggester, CommandContext, Suggestion
)


class TestCommandSuggester:
    """Test suite for command suggester"""

    @pytest.fixture
    def suggester(self):
        """Create command suggester instance"""
        return CommandSuggester()

    def test_initialization(self, suggester):
        """Test suggester initialization"""
        assert suggester.command_history is not None
        assert len(suggester.commands) > 0
        assert len(suggester.shortcuts) > 0
        assert suggester.session_start is not None

    def test_add_to_history(self, suggester):
        """Test adding commands to history"""
        suggester.add_to_history("query SELECT * FROM users")
        suggester.add_to_history("help")
        suggester.add_to_history("metrics")

        assert len(suggester.command_history) == 3
        assert suggester.command_patterns["query"] == 1
        assert suggester.command_patterns["help"] == 1
        assert suggester.command_patterns["metrics"] == 1

    def test_command_sequences(self, suggester):
        """Test command sequence tracking"""
        suggester.add_to_history("mcp connect")
        suggester.add_to_history("mcp status")
        suggester.add_to_history("query SELECT")

        # Check sequence patterns
        assert "mcp->mcp" in suggester.command_patterns
        assert "mcp->query" in suggester.command_patterns

    def test_completion_suggestions(self, suggester):
        """Test command completion"""
        context = CommandContext(current_command="qu")
        suggestions = suggester.get_suggestions(context)

        # Should suggest 'query' command
        assert any("query" in s.command for s in suggestions)

    def test_shortcut_suggestions(self, suggester):
        """Test shortcut suggestions"""
        context = CommandContext(current_command="q")
        suggestions = suggester.get_suggestions(context)

        # Should suggest 'query' as shortcut
        assert any(s.shortcut == "q" for s in suggestions)

    def test_error_recovery_suggestions(self, suggester):
        """Test error recovery suggestions"""
        context = CommandContext(
            current_command="",
            last_error="Connection refused"
        )
        suggestions = suggester.get_suggestions(context)

        # Should suggest connection-related commands
        assert any("mcp" in s.command for s in suggestions)

    def test_sequence_based_suggestions(self, suggester):
        """Test sequence-based suggestions"""
        suggester.add_to_history("mcp connect")

        context = CommandContext(
            current_command="",
            command_history=["mcp connect"]
        )
        suggestions = suggester.get_suggestions(context)

        # Should suggest next command in sequence
        assert any("mcp status" in s.command for s in suggestions)

    def test_context_suggestions_no_connections(self, suggester):
        """Test context suggestions when no connections"""
        context = CommandContext(
            current_command="",
            active_connections=[]
        )
        suggestions = suggester.get_suggestions(context)

        # Should suggest connecting
        assert any("mcp connect" in s.command for s in suggestions)

    def test_context_suggestions_new_session(self, suggester):
        """Test context suggestions for new session"""
        context = CommandContext(
            current_command="",
            session_duration=30  # 30 seconds
        )
        suggestions = suggester.get_suggestions(context)

        # Should suggest help or health
        assert any("help" in s.command or "health" in s.command for s in suggestions)

    def test_explain_command(self, suggester):
        """Test command explanation"""
        explanation = suggester.explain_command("query")
        assert "Execute SQL query" in explanation
        assert "database" in explanation.lower()

    def test_explain_shortcut(self, suggester):
        """Test shortcut explanation"""
        explanation = suggester.explain_command("q")
        assert "shortcut" in explanation.lower()
        assert "query" in explanation

    def test_explain_unknown_command(self, suggester):
        """Test unknown command explanation"""
        explanation = suggester.explain_command("unknown_cmd")
        assert "Unknown command" in explanation

    def test_get_command_help_all(self, suggester):
        """Test getting help for all commands"""
        help_text = suggester.get_command_help()

        # Should include all categories
        assert "DATABASE COMMANDS" in help_text
        assert "AI COMMANDS" in help_text
        assert "SYSTEM COMMANDS" in help_text
        assert "SHORTCUTS" in help_text

    def test_get_command_help_category(self, suggester):
        """Test getting help for specific category"""
        help_text = suggester.get_command_help("database")

        assert "DATABASE COMMANDS" in help_text
        assert "AI COMMANDS" not in help_text

    def test_record_error(self, suggester):
        """Test error recording"""
        suggester.record_error("query bad", "Syntax error")
        suggester.record_error("query bad", "Table not found")

        assert "query bad" in suggester.error_patterns
        assert len(suggester.error_patterns["query bad"]) == 2

    def test_popular_suggestions(self, suggester):
        """Test popular command suggestions"""
        # Add commands multiple times to make them popular
        for _ in range(5):
            suggester.add_to_history("metrics")
        for _ in range(3):
            suggester.add_to_history("health")

        context = CommandContext(current_command="")
        suggestions = suggester.get_suggestions(context)

        # Popular commands should appear
        popular_cmds = [s.command for s in suggestions if "frequently used" in s.description]
        assert any("metrics" in cmd for cmd in popular_cmds)

    def test_fuzzy_matching(self, suggester):
        """Test fuzzy matching for typos"""
        context = CommandContext(current_command="qurey")  # Typo
        suggestions = suggester.get_suggestions(context)

        # Should suggest 'query' despite typo
        assert any("query" in s.command and "did you mean" in s.description
                  for s in suggestions)

    def test_suggestion_confidence(self, suggester):
        """Test suggestion confidence scoring"""
        context = CommandContext(current_command="query")
        suggestions = suggester.get_suggestions(context)

        # Exact matches should have high confidence
        exact_match = [s for s in suggestions if s.command.startswith("query")]
        if exact_match:
            assert exact_match[0].confidence >= 0.7

    def test_suggestion_limit(self, suggester):
        """Test suggestion limit"""
        context = CommandContext(current_command="")
        suggestions = suggester.get_suggestions(context, limit=3)

        assert len(suggestions) <= 3

    def test_unique_suggestions(self, suggester):
        """Test that suggestions are unique"""
        context = CommandContext(current_command="")
        suggestions = suggester.get_suggestions(context)

        commands = [s.command for s in suggestions]
        assert len(commands) == len(set(commands)), "Duplicate suggestions found"


class TestCommandContext:
    """Test command context dataclass"""

    def test_context_creation(self):
        """Test creating command context"""
        context = CommandContext(
            current_command="query",
            command_history=["help", "metrics"],
            active_connections=["postgres"],
            last_error="Connection timeout"
        )

        assert context.current_command == "query"
        assert len(context.command_history) == 2
        assert len(context.active_connections) == 1
        assert context.last_error is not None

    def test_context_defaults(self):
        """Test context default values"""
        context = CommandContext(current_command="test")

        assert context.command_history == []
        assert context.current_directory == "/"
        assert context.active_connections == []
        assert context.last_error is None
        assert context.session_duration == 0.0
        assert context.user_patterns == {}


class TestSuggestion:
    """Test suggestion dataclass"""

    def test_suggestion_creation(self):
        """Test creating suggestion"""
        suggestion = Suggestion(
            command="query SELECT * FROM users",
            description="Execute SQL query",
            confidence=0.9,
            category="database",
            usage_example="query SELECT id, name FROM users WHERE active=true"
        )

        assert suggestion.command == "query SELECT * FROM users"
        assert suggestion.confidence == 0.9
        assert suggestion.category == "database"
        assert suggestion.usage_example is not None

    def test_suggestion_defaults(self):
        """Test suggestion default values"""
        suggestion = Suggestion(
            command="help",
            description="Show help",
            confidence=0.5,
            category="system"
        )

        assert suggestion.usage_example is None
        assert suggestion.shortcut is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])