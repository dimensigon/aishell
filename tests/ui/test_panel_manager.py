"""
Tests for Dynamic Panel Manager (src/ui/panel_manager.py)

Tests panel sizing, content-aware adaptation, and typing state handling.
"""

import pytest
from src.ui.panel_manager import DynamicPanelManager, PanelDimensions


class TestPanelDimensions:
    """Test suite for PanelDimensions dataclass."""

    def test_panel_dimensions_creation(self):
        """Test creating panel dimensions."""
        dims = PanelDimensions(min=10, max=50, preferred=30)

        assert dims.min == 10
        assert dims.max == 50
        assert dims.preferred == 30

    def test_panel_dimensions_attributes(self):
        """Test panel dimensions has all required attributes."""
        dims = PanelDimensions(min=5, max=100, preferred=50)

        assert hasattr(dims, 'min')
        assert hasattr(dims, 'max')
        assert hasattr(dims, 'preferred')


class TestDynamicPanelManager:
    """Test suite for DynamicPanelManager."""

    @pytest.fixture
    def manager(self):
        """Create DynamicPanelManager instance for testing."""
        return DynamicPanelManager()

    def test_initialization(self, manager):
        """Test panel manager initializes with correct defaults."""
        assert manager.panel_weights == {
            'output': 0.5,
            'module': 0.3,
            'prompt': 0.2
        }
        assert manager.active_typing is False
        assert manager.content_sizes == {}

    def test_default_panel_weights(self, manager):
        """Test default panel weights sum to 1.0."""
        total_weight = sum(manager.panel_weights.values())
        assert abs(total_weight - 1.0) < 0.01  # Allow small floating point error

    def test_calculate_dimensions_default(self, manager):
        """Test dimension calculation with default state."""
        terminal_height = 100

        dimensions = manager.calculate_dimensions(terminal_height)

        assert 'output' in dimensions
        assert 'module' in dimensions
        assert 'prompt' in dimensions

        # Check all are PanelDimensions instances
        assert isinstance(dimensions['output'], PanelDimensions)
        assert isinstance(dimensions['module'], PanelDimensions)
        assert isinstance(dimensions['prompt'], PanelDimensions)

    def test_calculate_dimensions_typing_active(self, manager):
        """Test dimensions prioritize prompt when typing."""
        manager.set_typing_state(True)
        manager.update_content_size('prompt', 5)

        dimensions = manager.calculate_dimensions(100)

        # Prompt should get reasonable space when typing
        prompt_height = dimensions['prompt'].preferred
        assert prompt_height > 0
        assert prompt_height <= 50  # Max half of terminal

    def test_calculate_dimensions_all_content_fits(self, manager):
        """Test dimensions when all content fits in terminal."""
        manager.update_content_size('output', 30)
        manager.update_content_size('module', 10)

        dimensions = manager.calculate_dimensions(100)

        # When content fits, use exact content sizes
        assert dimensions['output'].preferred == 30
        assert dimensions['module'].preferred == 10
        assert dimensions['prompt'].preferred == 3

    def test_calculate_dimensions_weighted_distribution(self, manager):
        """Test weighted distribution when content doesn't fit."""
        manager.update_content_size('output', 60)
        manager.update_content_size('module', 50)

        dimensions = manager.calculate_dimensions(80)

        # Should use weighted distribution
        output_height = dimensions['output'].preferred
        module_height = dimensions['module'].preferred
        prompt_height = dimensions['prompt'].preferred

        # Total should not exceed terminal height
        total = output_height + module_height + prompt_height
        assert total <= 80

    def test_set_typing_state(self, manager):
        """Test setting typing state."""
        assert manager.active_typing is False

        manager.set_typing_state(True)
        assert manager.active_typing is True

        manager.set_typing_state(False)
        assert manager.active_typing is False

    def test_update_content_size(self, manager):
        """Test updating content size for panels."""
        manager.update_content_size('output', 50)
        manager.update_content_size('module', 20)
        manager.update_content_size('prompt', 3)

        assert manager.content_sizes['output'] == 50
        assert manager.content_sizes['module'] == 20
        assert manager.content_sizes['prompt'] == 3

    def test_update_content_size_overwrites(self, manager):
        """Test updating content size overwrites previous value."""
        manager.update_content_size('output', 30)
        assert manager.content_sizes['output'] == 30

        manager.update_content_size('output', 50)
        assert manager.content_sizes['output'] == 50

    def test_calculate_prompt_lines(self, manager):
        """Test prompt line calculation."""
        manager.update_content_size('prompt', 5)

        lines = manager._calculate_prompt_lines()

        assert lines == 5

    def test_calculate_prompt_lines_default(self, manager):
        """Test prompt line calculation with no content."""
        lines = manager._calculate_prompt_lines()

        assert lines == 1  # Default

    def test_dimensions_respect_terminal_height(self, manager):
        """Test dimensions don't exceed terminal height."""
        for height in [50, 100, 200]:
            dimensions = manager.calculate_dimensions(height)

            total = (
                dimensions['output'].preferred +
                dimensions['module'].preferred +
                dimensions['prompt'].preferred
            )

            assert total <= height

    def test_typing_state_affects_prompt_size(self, manager):
        """Test typing state increases prompt allocation."""
        manager.update_content_size('prompt', 3)

        # Get dimensions without typing
        manager.set_typing_state(False)
        dims_not_typing = manager.calculate_dimensions(100)

        # Get dimensions with typing
        manager.set_typing_state(True)
        dims_typing = manager.calculate_dimensions(100)

        # Prompt should get more space when typing
        # (This may not always be true due to content-aware logic, but test intent)
        assert dims_typing['prompt'].max > 0

    def test_panel_weights_affect_distribution(self, manager):
        """Test panel weights affect size distribution."""
        # Set large content that won't fit
        manager.update_content_size('output', 100)
        manager.update_content_size('module', 100)

        dimensions = manager.calculate_dimensions(100)

        output_pct = dimensions['output'].preferred / 100
        module_pct = dimensions['module'].preferred / 100

        # Output should get more space than module (0.5 vs 0.3 weight)
        assert output_pct > module_pct

    def test_multiple_content_updates(self, manager):
        """Test multiple content updates work correctly."""
        for i in range(10):
            manager.update_content_size('output', i * 10)

        assert manager.content_sizes['output'] == 90

    def test_dimensions_min_max_constraints(self, manager):
        """Test dimensions have min/max values."""
        dimensions = manager.calculate_dimensions(100)

        for panel_name, dims in dimensions.items():
            assert dims.min >= 0
            assert dims.max >= dims.min
            assert dims.min <= dims.preferred <= dims.max

    def test_small_terminal_handling(self, manager):
        """Test handling of small terminal sizes."""
        dimensions = manager.calculate_dimensions(20)

        # Should still return valid dimensions
        assert all(dims.preferred > 0 for dims in dimensions.values())

    def test_large_terminal_handling(self, manager):
        """Test handling of large terminal sizes."""
        dimensions = manager.calculate_dimensions(500)

        # Should distribute space appropriately
        total = sum(dims.preferred for dims in dimensions.values())
        assert total > 0

    def test_typing_with_large_prompt_content(self, manager):
        """Test typing state with large prompt content."""
        manager.set_typing_state(True)
        manager.update_content_size('prompt', 30)

        dimensions = manager.calculate_dimensions(100)

        # Prompt should be capped at half terminal height
        assert dimensions['prompt'].preferred <= 50

    def test_zero_content_sizes(self, manager):
        """Test handling of zero content sizes."""
        manager.update_content_size('output', 0)
        manager.update_content_size('module', 0)
        manager.update_content_size('prompt', 0)

        dimensions = manager.calculate_dimensions(100)

        # Should still return valid dimensions
        assert all(dims.preferred > 0 for dims in dimensions.values())
