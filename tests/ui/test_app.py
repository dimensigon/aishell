"""
Tests for UI Application (src/ui/app.py)

Tests app lifecycle, command history, async operations, and state management.
"""

import pytest
import asyncio
from src.ui.app import AIShellApp


class TestAIShellApp:
    """Test suite for AIShellApp main application."""

    @pytest.fixture
    async def app(self):
        """Create AIShellApp instance for testing."""
        app = AIShellApp()
        yield app
        # Cleanup if needed
        if app.running:
            await app.stop()

    @pytest.mark.asyncio
    async def test_app_initialization(self):
        """Test app initializes with correct default state."""
        app = AIShellApp()

        assert app.output_lines == []
        assert app.module_info == "Ready | Module: OS-Base | Path: /"
        assert app.prompt_text == ""
        assert app.command_history == []
        assert app.is_typing is False
        assert app.running is False

    @pytest.mark.asyncio
    async def test_app_start(self, app):
        """Test app start initializes state correctly."""
        await app.start()

        assert app.running is True
        assert len(app.output_lines) == 1
        assert "AI-Shell initialized" in app.output_lines[0]

    @pytest.mark.asyncio
    async def test_app_stop(self, app):
        """Test app stop sets running flag to False."""
        await app.start()
        assert app.running is True

        await app.stop()
        assert app.running is False

    @pytest.mark.asyncio
    async def test_submit_command_adds_to_history(self, app):
        """Test command submission adds to history."""
        await app.start()

        await app.submit_command("SELECT * FROM users")

        assert len(app.command_history) == 1
        assert app.command_history[0] == "SELECT * FROM users"

    @pytest.mark.asyncio
    async def test_submit_command_adds_to_output(self, app):
        """Test command submission adds to output."""
        await app.start()
        initial_lines = len(app.output_lines)

        await app.submit_command("SELECT * FROM users")

        # Should add command line and result
        assert len(app.output_lines) > initial_lines
        assert any("SELECT * FROM users" in line for line in app.output_lines)

    @pytest.mark.asyncio
    async def test_submit_empty_command_ignored(self, app):
        """Test empty command is not added to history."""
        await app.start()

        await app.submit_command("")
        await app.submit_command("   ")

        assert len(app.command_history) == 0

    @pytest.mark.asyncio
    async def test_multiple_commands_in_sequence(self, app):
        """Test multiple commands are processed in order."""
        await app.start()

        commands = [
            "SELECT * FROM users",
            "UPDATE users SET active=true",
            "DELETE FROM sessions"
        ]

        for cmd in commands:
            await app.submit_command(cmd)

        assert len(app.command_history) == 3
        assert app.command_history == commands

    @pytest.mark.asyncio
    async def test_process_command_generates_output(self, app):
        """Test command processing generates output."""
        await app.start()
        initial_lines = len(app.output_lines)

        await app.process_command("SELECT 1")

        assert len(app.output_lines) > initial_lines

    @pytest.mark.asyncio
    async def test_update_output_appends_text(self, app):
        """Test update_output appends to output lines."""
        app.update_output("Test output 1")
        app.update_output("Test output 2")

        assert len(app.output_lines) == 2
        assert app.output_lines[0] == "Test output 1"
        assert app.output_lines[1] == "Test output 2"

    @pytest.mark.asyncio
    async def test_update_module_sets_info(self, app):
        """Test update_module sets module info."""
        new_info = "Active | Module: SQLite | Path: /data/test.db"
        app.update_module(new_info)

        assert app.module_info == new_info

    @pytest.mark.asyncio
    async def test_get_output_returns_joined_lines(self, app):
        """Test get_output returns formatted output."""
        app.update_output("Line 1")
        app.update_output("Line 2")
        app.update_output("Line 3")

        output = app.get_output()

        assert output == "Line 1\nLine 2\nLine 3"

    @pytest.mark.asyncio
    async def test_get_module_info_returns_current_state(self, app):
        """Test get_module_info returns current module info."""
        assert app.get_module_info() == "Ready | Module: OS-Base | Path: /"

        app.update_module("New module info")
        assert app.get_module_info() == "New module info"

    @pytest.mark.asyncio
    async def test_concurrent_command_execution(self, app):
        """Test concurrent command execution doesn't cause issues."""
        await app.start()

        # Submit multiple commands concurrently
        tasks = [
            app.submit_command(f"SELECT {i}")
            for i in range(10)
        ]

        await asyncio.gather(*tasks)

        # All commands should be in history
        assert len(app.command_history) == 10

    @pytest.mark.asyncio
    async def test_command_output_format(self, app):
        """Test command output has correct format."""
        await app.start()

        await app.submit_command("SELECT * FROM test")

        # Should have command prompt in output
        assert any("AI$ >" in line for line in app.output_lines)
        # Should have command result in output
        assert any("Command executed" in line for line in app.output_lines)

    @pytest.mark.asyncio
    async def test_typing_state_management(self, app):
        """Test typing state can be tracked."""
        assert app.is_typing is False

        # Simulate typing
        app.is_typing = True
        assert app.is_typing is True

        # Simulate stop typing
        app.is_typing = False
        assert app.is_typing is False

    @pytest.mark.asyncio
    async def test_long_output_accumulation(self, app):
        """Test app handles long output accumulation."""
        # Add many lines of output
        for i in range(1000):
            app.update_output(f"Line {i}")

        assert len(app.output_lines) == 1000
        output = app.get_output()
        assert "Line 0" in output
        assert "Line 999" in output

    @pytest.mark.asyncio
    async def test_special_characters_in_commands(self, app):
        """Test app handles special characters in commands."""
        await app.start()

        special_cmd = "SELECT * FROM users WHERE name LIKE '%test%' AND id > 100"
        await app.submit_command(special_cmd)

        assert special_cmd in app.command_history
        assert any(special_cmd in line for line in app.output_lines)

    @pytest.mark.asyncio
    async def test_app_state_persistence(self, app):
        """Test app maintains state across operations."""
        await app.start()

        # Perform various operations
        await app.submit_command("CMD1")
        app.update_module("Module1")
        await app.submit_command("CMD2")
        app.update_output("Custom output")

        # Verify state is maintained
        assert len(app.command_history) == 2
        assert app.module_info == "Module1"
        assert "Custom output" in app.output_lines
        assert app.running is True
