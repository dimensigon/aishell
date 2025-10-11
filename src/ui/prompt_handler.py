"""
Prompt Input Handler

Handles multi-line input with backslash continuation and line numbering.
Includes rate limiting for command execution security.
"""

from typing import List, Optional
import re
import sys
import os

# Add src to path for security imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
try:
    from src.security.rate_limiter import RateLimiter, RateLimitConfig, RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    RateLimiter = None  # type: ignore
    RateLimitConfig = None  # type: ignore
    RateLimitExceeded = None  # type: ignore


class PromptHandler:
    """
    Advanced prompt input handler.

    Features:
    - Multi-line input with backslash continuation
    - Line numbering
    - Input validation
    """

    def __init__(self) -> None:
        self.multiline_buffer: List[str] = []
        self.in_multiline = False

        # SECURITY FIX: Initialize rate limiter
        if RATE_LIMITING_AVAILABLE:
            # Configure rate limits: 100 commands per minute, max 10 per 5 seconds
            config = RateLimitConfig(
                max_calls=100,
                period_seconds=60,
                burst_limit=10,
                burst_period_seconds=5
            )
            self.rate_limiter: Optional[RateLimiter] = RateLimiter(config)
        else:
            self.rate_limiter: Optional[RateLimiter] = None

    async def process_multiline(self, lines: List[str]) -> str:
        """
        Process multi-line input with backslash continuation.

        Args:
            lines: List of input lines

        Returns:
            Combined command string

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        # SECURITY FIX: Check rate limit before processing
        if self.rate_limiter:
            try:
                self.rate_limiter.check_rate_limit('command_execution', raise_on_limit=True)
            except (RateLimitExceeded, Exception) as e:
                if RATE_LIMITING_AVAILABLE and isinstance(e, RateLimitExceeded):
                    raise
                # If rate limiting not available, continue without it
                pass

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
