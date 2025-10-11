"""
Main Application (Mock Implementation for Testing)

This is a testable mock implementation without external UI dependencies.
"""

from typing import List, Optional, Dict
import asyncio


class AIShellApp:
    """
    Main AI-Shell application (mock for testing).

    Features:
    - 3-panel concept (Output, Module, Prompt)
    - Command history
    - Async command execution
    """

    def __init__(self) -> None:
        self.output_lines: List[str] = []
        self.module_info: str = "Ready | Module: OS-Base | Path: /"
        self.prompt_text: str = ""
        self.command_history: List[str] = []
        self.is_typing: bool = False
        self.running: bool = False

    async def start(self) -> None:
        """Start the application"""
        self.running = True
        self.output_lines.append("AI-Shell initialized. Type commands below.")

    async def stop(self) -> None:
        """Stop the application"""
        self.running = False

    async def submit_command(self, command: str) -> None:
        """
        Submit a command for execution.

        Args:
            command: Command to execute
        """
        if not command.strip():
            return

        self.command_history.append(command)
        self.output_lines.append(f"AI$ > {command}")

        # Process command
        await self.process_command(command)

    async def process_command(self, command: str) -> None:
        """
        Process a command.

        Args:
            command: Command to process
        """
        # Simple echo for testing
        result = f"Command executed: {command}"
        self.output_lines.append(result)

    def update_output(self, text: str) -> None:
        """Update output panel"""
        self.output_lines.append(text)

    def update_module(self, text: str) -> None:
        """Update module panel"""
        self.module_info = text

    def get_output(self) -> str:
        """Get current output"""
        return '\n'.join(self.output_lines)

    def get_module_info(self) -> str:
        """Get current module info"""
        return self.module_info
