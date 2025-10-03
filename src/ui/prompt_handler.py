"""
Prompt Input Handler

Handles multi-line input with backslash continuation and line numbering.
"""

from typing import List
import re


class PromptHandler:
    """
    Advanced prompt input handler.

    Features:
    - Multi-line input with backslash continuation
    - Line numbering
    - Input validation
    """

    def __init__(self):
        self.multiline_buffer = []
        self.in_multiline = False

    async def process_multiline(self, lines: List[str]) -> str:
        """
        Process multi-line input with backslash continuation.

        Args:
            lines: List of input lines

        Returns:
            Combined command string
        """
        result = []

        for line in lines:
            # Remove trailing backslash and newline
            if line.endswith('\\'):
                result.append(line[:-1].strip())
            else:
                result.append(line.strip())

        return ' '.join(result)

    def format_with_line_numbers(self, lines: List[str]) -> str:
        """
        Format lines with line numbers.

        Args:
            lines: List of lines to format

        Returns:
            Formatted string with line numbers
        """
        formatted = []
        for i, line in enumerate(lines, start=1):
            formatted.append(f"{i:3d} {line}")

        return '\n'.join(formatted)

    def detect_multiline(self, text: str) -> bool:
        """
        Detect if input starts multi-line mode.

        Args:
            text: Input text

        Returns:
            True if multi-line mode should be enabled
        """
        return text.strip().endswith('\\')

    def validate_input(self, text: str) -> tuple[bool, str]:
        """
        Validate input text.

        Args:
            text: Input text to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Empty input"

        # Check for dangerous patterns (basic validation)
        dangerous_patterns = [
            r'rm\s+-rf\s+/',  # Dangerous rm
            r':\(\)\{.*\};',   # Fork bomb
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, text):
                return False, "Potentially dangerous command detected"

        return True, ""

    def add_to_buffer(self, line: str) -> None:
        """Add line to multiline buffer"""
        self.multiline_buffer.append(line)
        self.in_multiline = line.endswith('\\')

    def get_buffer(self) -> List[str]:
        """Get current multiline buffer"""
        return self.multiline_buffer.copy()

    def clear_buffer(self) -> None:
        """Clear multiline buffer"""
        self.multiline_buffer = []
        self.in_multiline = False
