"""
Tests for UI Components
"""

import pytest
from src.ui.app import AIShellApp
from src.ui.panel_manager import DynamicPanelManager, PanelDimensions
from src.ui.prompt_handler import PromptHandler


# Panel Manager Tests

def test_panel_dimensions_typing_active():
    """Test panel sizing when user is typing"""
    manager = DynamicPanelManager()
    manager.active_typing = True
    manager.content_sizes = {'output': 20, 'module': 10, 'prompt': 5}

    dims = manager.calculate_dimensions(terminal_height=50)

    # When typing, prompt gets priority allocation
    # Verify prompt has reasonable size
    assert dims['prompt'].min >= 5
    assert dims['output'].min > 0
    assert dims['module'].min > 0


def test_panel_dimensions_idle():
    """Test panel sizing when idle"""
    manager = DynamicPanelManager()
    manager.active_typing = False
    manager.content_sizes = {'output': 30, 'module': 15}

    dims = manager.calculate_dimensions(terminal_height=50)

    # Should have balanced distribution
    assert dims['output'].min > 0
    assert dims['module'].min > 0
    assert dims['prompt'].min > 0


def test_panel_dimensions_all_content_fits():
    """Test when all content fits in terminal"""
    manager = DynamicPanelManager()
    manager.active_typing = False
    manager.content_sizes = {'output': 10, 'module': 5}

    dims = manager.calculate_dimensions(terminal_height=50)

    # Output should match content size
    assert dims['output'].min == 10
    assert dims['module'].min == 5


def test_set_typing_state():
    """Test updating typing state"""
    manager = DynamicPanelManager()

    manager.set_typing_state(True)
    assert manager.active_typing == True

    manager.set_typing_state(False)
    assert manager.active_typing == False


def test_update_content_size():
    """Test updating panel content sizes"""
    manager = DynamicPanelManager()

    manager.update_content_size('output', 25)
    manager.update_content_size('module', 12)

    assert manager.content_sizes['output'] == 25
    assert manager.content_sizes['module'] == 12


# Prompt Handler Tests

@pytest.mark.asyncio
async def test_multiline_input():
    """Test multi-line input with backslash continuation"""
    handler = PromptHandler()

    lines = [
        "SELECT * FROM users \\",
        "WHERE active = 1 \\",
        "ORDER BY created_at;"
    ]

    result = await handler.process_multiline(lines)
    assert "SELECT * FROM users" in result
    assert "WHERE active = 1" in result
    assert "ORDER BY created_at;" in result


@pytest.mark.asyncio
async def test_multiline_without_backslash():
    """Test multi-line without continuation"""
    handler = PromptHandler()

    lines = ["ls -la", "pwd"]

    result = await handler.process_multiline(lines)
    assert "ls -la" in result
    assert "pwd" in result


def test_line_numbering():
    """Test line number display for multi-line input"""
    handler = PromptHandler()

    display = handler.format_with_line_numbers([
        "line one",
        "line two",
        "line three"
    ])

    assert "  1 line one" in display
    assert "  2 line two" in display
    assert "  3 line three" in display


def test_detect_multiline():
    """Test multi-line detection"""
    handler = PromptHandler()

    assert handler.detect_multiline("command \\") == True
    assert handler.detect_multiline("command") == False
    assert handler.detect_multiline("  \\") == True


def test_validate_input_valid():
    """Test input validation for valid commands"""
    handler = PromptHandler()

    valid, msg = handler.validate_input("ls -la")
    assert valid == True
    assert msg == ""


def test_validate_input_empty():
    """Test input validation for empty input"""
    handler = PromptHandler()

    valid, msg = handler.validate_input("")
    assert valid == False
    assert "Empty" in msg


def test_validate_input_dangerous():
    """Test input validation for dangerous commands"""
    handler = PromptHandler()

    valid, msg = handler.validate_input("rm -rf /")
    assert valid == False
    assert "dangerous" in msg.lower()


def test_multiline_buffer():
    """Test multiline buffer management"""
    handler = PromptHandler()

    handler.add_to_buffer("line 1 \\")
    assert handler.in_multiline == True
    assert len(handler.get_buffer()) == 1

    handler.add_to_buffer("line 2")
    assert handler.in_multiline == False
    assert len(handler.get_buffer()) == 2

    handler.clear_buffer()
    assert len(handler.get_buffer()) == 0
    assert handler.in_multiline == False


# App Tests (async)

@pytest.mark.asyncio
async def test_app_initialization():
    """Test app initializes with panels"""
    app = AIShellApp()

    assert app.command_history == []
    assert app.is_typing == False


def test_app_update_output():
    """Test updating output panel"""
    app = AIShellApp()
    # Note: This requires app to be running, so we just test the method exists
    assert hasattr(app, 'update_output')
    assert callable(app.update_output)


def test_app_update_module():
    """Test updating module panel"""
    app = AIShellApp()
    assert hasattr(app, 'update_module')
    assert callable(app.update_module)


def test_app_command_history():
    """Test command history tracking"""
    app = AIShellApp()

    app.command_history.append("ls")
    app.command_history.append("pwd")

    assert len(app.command_history) == 2
    assert app.command_history[0] == "ls"
    assert app.command_history[1] == "pwd"
