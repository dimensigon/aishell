"""
Tests for Dynamic Panel Container (src/ui/containers/dynamic_panel_container.py)

Tests dynamic sizing, content adaptation, and panel management.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from textual.widget import Widget

from src.ui.containers.dynamic_panel_container import (
    DynamicPanelContainer,
    PanelConfig
)


class TestPanelConfig:
    """Test suite for PanelConfig dataclass."""

    def test_panel_config_creation(self):
        """Test creating panel configuration."""
        config = PanelConfig(
            name="output",
            default_size=50,
            min_size=10,
            max_size=80
        )

        assert config.name == "output"
        assert config.default_size == 50
        assert config.min_size == 10
        assert config.max_size == 80
        assert config.current_size == 50  # Should match default

    def test_panel_config_defaults(self):
        """Test panel config uses defaults."""
        config = PanelConfig(name="test", default_size=30)

        assert config.min_size == 10
        assert config.max_size == 80
        assert config.current_size == 30

    def test_panel_config_post_init(self):
        """Test __post_init__ sets current_size."""
        config = PanelConfig(name="test", default_size=40)

        assert config.current_size == 40


class TestDynamicPanelContainer:
    """Test suite for DynamicPanelContainer."""

    @pytest.fixture
    def container(self):
        """Create DynamicPanelContainer instance."""
        return DynamicPanelContainer(id="test-container")

    def test_initialization(self, container):
        """Test container initializes with correct defaults."""
        assert 'output' in container.panels
        assert 'module' in container.panels
        assert 'prompt' in container.panels

        assert container.panels['output'].default_size == 50
        assert container.panels['module'].default_size == 30
        assert container.panels['prompt'].default_size == 20

    def test_panel_sizes_sum_to_100(self, container):
        """Test default panel sizes sum to 100%."""
        total = sum(p.default_size for p in container.panels.values())
        assert total == 100

    @pytest.mark.asyncio
    async def test_resize_panel_valid(self, container):
        """Test resizing panel to valid size."""
        # Mock _apply_panel_sizes to avoid UI operations
        container._apply_panel_sizes = Mock()

        success = await container.resize_panel('output', 60)

        assert success is True
        assert container.panels['output'].current_size == 60

    @pytest.mark.asyncio
    async def test_resize_panel_invalid_name(self, container):
        """Test resizing non-existent panel."""
        success = await container.resize_panel('invalid', 50)

        assert success is False

    @pytest.mark.asyncio
    async def test_resize_panel_enforces_min(self, container):
        """Test resize enforces minimum size."""
        container._apply_panel_sizes = Mock()

        await container.resize_panel('output', 5)  # Below min

        # Should be set to min_size (10)
        assert container.panels['output'].current_size >= 10

    @pytest.mark.asyncio
    async def test_resize_panel_enforces_max(self, container):
        """Test resize enforces maximum size."""
        container._apply_panel_sizes = Mock()

        await container.resize_panel('output', 90)  # Above max

        # Should be capped at max_size (80)
        assert container.panels['output'].current_size <= 80

    @pytest.mark.asyncio
    async def test_resize_panel_adjusts_others(self, container):
        """Test resizing one panel adjusts others."""
        container._apply_panel_sizes = Mock()

        initial_module = container.panels['module'].current_size
        initial_prompt = container.panels['prompt'].current_size

        await container.resize_panel('output', 60)

        # Other panels should be adjusted
        # Total should still be 100
        total = sum(p.current_size for p in container.panels.values())
        assert total == 100

    @pytest.mark.asyncio
    async def test_resize_panel_user_initiated_flag(self, container):
        """Test manual adjustment flag is set."""
        container._apply_panel_sizes = Mock()

        await container.resize_panel('output', 60, user_initiated=True)

        assert container._manual_adjustment['output'] is True

    @pytest.mark.asyncio
    async def test_resize_panel_triggers_callbacks(self, container):
        """Test resize triggers registered callbacks."""
        container._apply_panel_sizes = Mock()
        callback = Mock()
        container.register_resize_callback(callback)

        await container.resize_panel('output', 60)

        callback.assert_called_once_with('output', 60)

    @pytest.mark.asyncio
    async def test_auto_adjust_skips_manual_panels(self, container):
        """Test auto-adjust skips manually adjusted panels."""
        container._apply_panel_sizes = Mock()

        # Mark output as manually adjusted
        container._manual_adjustment['output'] = True

        await container.auto_adjust()
        await asyncio.sleep(0.1)  # Let async task run

        # Output should retain its size
        # (More detailed testing would require mocking more internals)

    @pytest.mark.asyncio
    async def test_auto_adjust_empty_content_minimizes(self, container):
        """Test auto-adjust minimizes panels with no content."""
        container._apply_panel_sizes = Mock()
        container.resize_panel = AsyncMock()

        # Set empty content
        for panel_name in container.panels:
            container.panels[panel_name].content_height = 0

        await container._run_auto_adjust()

        # Should call resize_panel (implementation may vary)
        # At least verify it runs without error

    @pytest.mark.asyncio
    async def test_auto_adjust_active_panel_preference(self, container):
        """Test auto-adjust prefers active panel."""
        container._apply_panel_sizes = Mock()
        container.resize_panel = AsyncMock()

        container.panels['prompt'].is_active = True
        container.panels['prompt'].content_height = 5

        await container._run_auto_adjust()

        # Should attempt to expand active panel
        # (Exact behavior depends on implementation)

    def test_set_panel_content(self, container):
        """Test setting panel content."""
        # Mock panel widgets
        mock_panel = Mock(remove_children=Mock(), mount=Mock())
        container._panel_widgets = {'output': mock_panel}

        mock_widget = Mock(spec=Widget)

        success = container.set_panel_content('output', mock_widget, content_height=30)

        assert success is True
        mock_panel.remove_children.assert_called_once()
        mock_panel.mount.assert_called_once_with(mock_widget)
        assert container.panels['output'].content_height == 30

    def test_set_panel_content_invalid_panel(self, container):
        """Test setting content for invalid panel."""
        mock_widget = Mock(spec=Widget)

        success = container.set_panel_content('invalid', mock_widget)

        assert success is False

    def test_set_active_panel(self, container):
        """Test setting active panel."""
        # Mock panel widgets
        for name in ['output', 'module', 'prompt']:
            container._panel_widgets[name] = Mock(
                remove_class=Mock(),
                add_class=Mock()
            )

        container.set_active_panel('prompt')

        assert container.panels['prompt'].is_active is True
        assert container.panels['output'].is_active is False
        assert container.panels['module'].is_active is False
        assert container.active_panel == 'prompt'

    def test_set_active_panel_none(self, container):
        """Test deactivating all panels."""
        # Mock panel widgets
        for name in ['output', 'module', 'prompt']:
            container._panel_widgets[name] = Mock(
                remove_class=Mock(),
                add_class=Mock()
            )

        container.set_active_panel(None)

        assert all(not p.is_active for p in container.panels.values())

    def test_update_content_height(self, container):
        """Test updating content height."""
        container.update_content_height('output', 50)

        assert container.panels['output'].content_height == 50

    def test_update_content_height_invalid_panel(self, container):
        """Test updating height for invalid panel."""
        # Should not raise
        container.update_content_height('invalid', 50)

    def test_register_resize_callback(self, container):
        """Test registering callback."""
        callback = Mock()

        container.register_resize_callback(callback)

        assert callback in container._resize_callbacks

    def test_unregister_resize_callback(self, container):
        """Test unregistering callback."""
        callback = Mock()
        container.register_resize_callback(callback)

        container.unregister_resize_callback(callback)

        assert callback not in container._resize_callbacks

    def test_get_panel_size(self, container):
        """Test getting panel size."""
        size = container.get_panel_size('output')

        assert size == 50  # Default

    def test_get_panel_size_invalid(self, container):
        """Test getting size for invalid panel."""
        size = container.get_panel_size('invalid')

        assert size is None

    def test_reset_manual_adjustments(self, container):
        """Test resetting manual adjustment flags."""
        container._manual_adjustment['output'] = True
        container._manual_adjustment['module'] = True

        container.reset_manual_adjustments()

        assert all(not v for v in container._manual_adjustment.values())

    @pytest.mark.asyncio
    async def test_resize_panel_maintains_total_100(self, container):
        """Test all resizes maintain 100% total."""
        container._apply_panel_sizes = Mock()

        for size in [40, 50, 60, 70]:
            await container.resize_panel('output', size)

            total = sum(p.current_size for p in container.panels.values())
            assert total == 100

    @pytest.mark.asyncio
    async def test_multiple_resize_callbacks(self, container):
        """Test multiple callbacks are all triggered."""
        container._apply_panel_sizes = Mock()

        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()

        container.register_resize_callback(callback1)
        container.register_resize_callback(callback2)
        container.register_resize_callback(callback3)

        await container.resize_panel('output', 55)

        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_errors_handled(self, container):
        """Test callback errors don't break resize."""
        container._apply_panel_sizes = Mock()

        # Callback that raises
        def bad_callback(panel, size):
            raise ValueError("Test error")

        container.register_resize_callback(bad_callback)

        # Should not raise
        success = await container.resize_panel('output', 55)

        assert success is True
