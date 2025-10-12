"""
Tests for Prompt Input Handler (src/ui/prompt_handler.py)

Tests multi-line input, validation, rate limiting, and line numbering.
"""

import pytest
import asyncio
from src.ui.prompt_handler import PromptHandler


class TestPromptHandler:
    """Test suite for PromptHandler."""

    @pytest.fixture
    def handler(self):
        """Create PromptHandler instance for testing."""
        return PromptHandler()

    @pytest.mark.asyncio
    async def test_initialization(self, handler):
        """Test handler initializes with correct defaults."""
        assert handler.multiline_buffer == []
        assert handler.in_multiline is False
        # Rate limiter may or may not be initialized
        assert hasattr(handler, 'rate_limiter')

    @pytest.mark.asyncio
    async def test_process_multiline_single_line(self, handler):
        """Test processing single line input."""
        lines = ["SELECT * FROM users"]

        result = await handler.process_multiline(lines)

        assert result == "SELECT * FROM users"

    @pytest.mark.asyncio
    async def test_process_multiline_continuation(self, handler):
        """Test processing multi-line input with backslash."""
        lines = [
            "SELECT id, name \\",
            "FROM users \\",
            "WHERE active = true"
        ]

        result = await handler.process_multiline(lines)

        assert "SELECT id, name" in result
        assert "FROM users" in result
        assert "WHERE active = true" in result

    @pytest.mark.asyncio
    async def test_process_multiline_removes_backslash(self, handler):
        """Test backslash continuation is removed."""
        lines = ["SELECT * \\", "FROM users"]

        result = await handler.process_multiline(lines)

        # Backslash should be removed
        assert "\\" not in result

    @pytest.mark.asyncio
    async def test_format_with_line_numbers(self, handler):
        """Test line number formatting."""
        lines = ["Line 1", "Line 2", "Line 3"]

        formatted = handler.format_with_line_numbers(lines)

        assert "  1 Line 1" in formatted
        assert "  2 Line 2" in formatted
        assert "  3 Line 3" in formatted

    @pytest.mark.asyncio
    async def test_format_with_line_numbers_alignment(self, handler):
        """Test line numbers are aligned correctly."""
        lines = ["First", "Second", "Third"]

        formatted = handler.format_with_line_numbers(lines)

        # Numbers should be right-aligned in 3 characters
        assert formatted.startswith("  1")

    def test_detect_multiline_with_backslash(self, handler):
        """Test detection of multiline input."""
        text = "SELECT * FROM users \\"

        is_multiline = handler.detect_multiline(text)

        assert is_multiline is True

    def test_detect_multiline_without_backslash(self, handler):
        """Test single line is not detected as multiline."""
        text = "SELECT * FROM users"

        is_multiline = handler.detect_multiline(text)

        assert is_multiline is False

    def test_detect_multiline_with_trailing_spaces(self, handler):
        """Test multiline detection with trailing spaces."""
        text = "SELECT * FROM users \\   "

        # After strip, should still end with backslash
        is_multiline = handler.detect_multiline(text)

        assert is_multiline is True

    def test_validate_input_valid(self, handler):
        """Test validation accepts valid input."""
        text = "SELECT * FROM users WHERE id = 1"

        is_valid, message = handler.validate_input(text)

        assert is_valid is True
        assert message == ""

    def test_validate_input_empty(self, handler):
        """Test validation rejects empty input."""
        is_valid, message = handler.validate_input("")

        assert is_valid is False
        assert "Empty" in message

    def test_validate_input_whitespace_only(self, handler):
        """Test validation rejects whitespace-only input."""
        is_valid, message = handler.validate_input("   \n\t  ")

        assert is_valid is False
        assert "Empty" in message

    def test_validate_input_dangerous_rm(self, handler):
        """Test validation detects dangerous rm command."""
        text = "rm -rf /"

        is_valid, message = handler.validate_input(text)

        assert is_valid is False
        assert "dangerous" in message.lower()

    def test_validate_input_fork_bomb(self, handler):
        """Test validation detects fork bomb pattern."""
        text = ":(){ :|:& };:"

        is_valid, message = handler.validate_input(text)

        assert is_valid is False
        assert "dangerous" in message.lower()

    def test_validate_input_normal_rm(self, handler):
        """Test validation allows normal rm usage."""
        text = "rm temp.txt"

        is_valid, message = handler.validate_input(text)

        # Should be valid - not the dangerous pattern
        assert is_valid is True

    def test_add_to_buffer(self, handler):
        """Test adding lines to multiline buffer."""
        handler.add_to_buffer("Line 1 \\")

        assert len(handler.multiline_buffer) == 1
        assert handler.multiline_buffer[0] == "Line 1 \\"
        assert handler.in_multiline is True

    def test_add_to_buffer_without_continuation(self, handler):
        """Test adding line without continuation."""
        handler.add_to_buffer("Line 1")

        assert len(handler.multiline_buffer) == 1
        assert handler.in_multiline is False

    def test_add_multiple_to_buffer(self, handler):
        """Test adding multiple lines to buffer."""
        handler.add_to_buffer("Line 1 \\")
        handler.add_to_buffer("Line 2 \\")
        handler.add_to_buffer("Line 3")

        assert len(handler.multiline_buffer) == 3
        assert handler.in_multiline is False

    def test_get_buffer(self, handler):
        """Test getting buffer returns copy."""
        handler.add_to_buffer("Test line")

        buffer = handler.get_buffer()

        assert buffer == ["Test line"]
        # Should be a copy, not the original
        buffer.append("New line")
        assert len(handler.multiline_buffer) == 1

    def test_clear_buffer(self, handler):
        """Test clearing buffer."""
        handler.add_to_buffer("Line 1 \\")
        handler.add_to_buffer("Line 2")

        handler.clear_buffer()

        assert handler.multiline_buffer == []
        assert handler.in_multiline is False

    @pytest.mark.asyncio
    async def test_multiline_workflow(self, handler):
        """Test complete multiline input workflow."""
        # Detect multiline
        assert handler.detect_multiline("SELECT * \\")

        # Add to buffer
        handler.add_to_buffer("SELECT * \\")
        handler.add_to_buffer("FROM users \\")
        handler.add_to_buffer("WHERE id = 1")

        # Process buffer
        result = await handler.process_multiline(handler.get_buffer())

        # Clear buffer
        handler.clear_buffer()

        assert "SELECT *" in result
        assert "FROM users" in result
        assert "WHERE id = 1" in result
        assert handler.multiline_buffer == []

    @pytest.mark.asyncio
    async def test_process_multiline_with_empty_lines(self, handler):
        """Test processing multiline with empty lines."""
        lines = ["SELECT * \\", "", "FROM users"]

        result = await handler.process_multiline(lines)

        # Empty line should be handled
        assert "SELECT *" in result
        assert "FROM users" in result

    def test_format_large_number_of_lines(self, handler):
        """Test formatting many lines."""
        lines = [f"Line {i}" for i in range(100)]

        formatted = handler.format_with_line_numbers(lines)

        # Should handle all lines
        assert "100 Line 99" in formatted

    @pytest.mark.asyncio
    async def test_rate_limiting_not_triggered_normal_use(self, handler):
        """Test rate limiting doesn't block normal usage."""
        lines = ["SELECT 1"]

        # Should not raise
        result = await handler.process_multiline(lines)
        assert result == "SELECT 1"

    @pytest.mark.asyncio
    async def test_multiple_sequential_commands(self, handler):
        """Test processing multiple commands sequentially."""
        for i in range(5):
            lines = [f"SELECT {i}"]
            result = await handler.process_multiline(lines)
            assert f"SELECT {i}" == result

    def test_validate_sql_injection_attempt(self, handler):
        """Test validation of potentially malicious SQL."""
        # Note: Handler does basic validation, not SQL injection detection
        text = "SELECT * FROM users WHERE name = 'admin' OR '1'='1'"

        is_valid, message = handler.validate_input(text)

        # Should pass basic validation (it's valid SQL syntax)
        # SQL injection protection should be in database layer
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, handler):
        """Test concurrent processing of multiple inputs."""
        tasks = [
            handler.process_multiline([f"SELECT {i}"])
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(isinstance(r, str) for r in results)

    def test_buffer_state_management(self, handler):
        """Test buffer state is managed correctly."""
        # Start with empty buffer
        assert handler.in_multiline is False

        # Add line with continuation
        handler.add_to_buffer("Line 1 \\")
        assert handler.in_multiline is True

        # Add line without continuation
        handler.add_to_buffer("Line 2")
        assert handler.in_multiline is False

        # Clear
        handler.clear_buffer()
        assert handler.in_multiline is False
