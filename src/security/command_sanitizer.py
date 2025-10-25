"""
Command Sanitization for Safe Execution

Provides utilities to sanitize and validate shell commands before execution.
"""

import shlex
import re
from typing import List, Optional


class SecurityError(Exception):
    """Security-related error"""
    pass


class CommandSanitizer:
    """Sanitize commands for safe execution"""

    # Commands that are completely blocked
    BLOCKED_COMMANDS = {
        'rm',
        'rmdir',
        'del',
        'format',
        'dd',
        'mkfs',
        'fdisk',
        'diskpart',
        'shutdown',
        'reboot',
        'halt',
        'poweroff',
        'init',
    }

    # Commands that require explicit approval
    HIGH_RISK_COMMANDS = {
        'curl',
        'wget',
        'nc',
        'netcat',
        'ncat',
        'telnet',
        'ssh',
        'scp',
        'rsync',
        'chmod',
        'chown',
        'chgrp',
        'sudo',
        'su',
    }

    # Dangerous patterns in arguments
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',  # Recursive deletion from root
        r'rm\s+-rf\s+\*',  # Recursive wildcard deletion
        r':\(\)\{.*\};',   # Fork bomb
        r'>\s*/dev/sd[a-z]',  # Writing to raw disk
        r'dd\s+.*of=/dev',  # DD to device
        r'mkfs\.',  # Filesystem creation
        r'\|.*bash',  # Piping to bash
        r'\|.*sh\b',  # Piping to shell
        r';.*rm\s',  # Chained rm command
        r'&&.*rm\s',  # Chained rm command
        r'\$\(.*\)',  # Command substitution
        r'`.*`',  # Backtick command substitution
    ]

    @classmethod
    def sanitize_command(cls, command: str) -> str:
        """
        Sanitize command for safe execution.

        Args:
            command: Command string to sanitize

        Returns:
            Safely quoted command string

        Raises:
            SecurityError: If command is dangerous or blocked
        """
        if not command or not command.strip():
            raise SecurityError("Empty command")

        # Check for dangerous patterns first
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise SecurityError(f"Dangerous command pattern detected: {pattern}")

        # Parse command
        try:
            parts = shlex.split(command)
        except ValueError as e:
            raise SecurityError(f"Invalid command syntax: {e}")

        if not parts:
            raise SecurityError("Empty command after parsing")

        base_command = parts[0].lower()

        # Extract just the command name (handle paths)
        if '/' in base_command:
            base_command = base_command.split('/')[-1]

        # Block dangerous commands
        if base_command in cls.BLOCKED_COMMANDS:
            raise SecurityError(f"Command blocked for safety: {base_command}")

        # Warn about high-risk commands (caller should confirm)
        if base_command in cls.HIGH_RISK_COMMANDS:
            raise SecurityError(
                f"High-risk command requires approval: {base_command}"
            )

        # Return safely quoted command
        return shlex.join(parts)

    @classmethod
    def is_safe_command(cls, command: str) -> tuple[bool, Optional[str]]:
        """
        Check if command is safe without raising exception.

        Args:
            command: Command to check

        Returns:
            Tuple of (is_safe, error_message)
        """
        try:
            cls.sanitize_command(command)
            return True, None
        except SecurityError as e:
            return False, str(e)

    @classmethod
    def validate_file_path(cls, path: str) -> bool:
        """
        Validate file path for safe operations.

        Args:
            path: File path to validate

        Returns:
            True if path is safe

        Raises:
            SecurityError: If path is unsafe
        """
        dangerous_paths = [
            '/etc/passwd',
            '/etc/shadow',
            '/etc/sudoers',
            '/boot/',
            '/sys/',
            '/proc/',
            '/dev/',
        ]

        path_lower = path.lower()
        for dangerous in dangerous_paths:
            if dangerous in path_lower:
                raise SecurityError(f"Access to system path denied: {path}")

        # Check for path traversal
        if '..' in path:
            raise SecurityError(f"Path traversal detected: {path}")

        return True

    @classmethod
    def get_allowed_commands(cls) -> List[str]:
        """
        Get list of commonly allowed safe commands.

        Returns:
            List of safe command names
        """
        return [
            'ls',
            'cat',
            'echo',
            'pwd',
            'cd',
            'mkdir',
            'touch',
            'cp',
            'mv',
            'grep',
            'find',
            'head',
            'tail',
            'less',
            'more',
            'wc',
            'sort',
            'uniq',
            'diff',
            'python',
            'python3',
            'node',
            'npm',
            'git',
            'docker',
        ]
