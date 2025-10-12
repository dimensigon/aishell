"""
Tests for RiskIndicator Widget (src/ui/widgets/risk_indicator.py)

Tests risk display, color coding, visual updates, and state management.
"""

import pytest
from unittest.mock import Mock, patch
from textual.widgets import Static

from src.ui.widgets.risk_indicator import RiskIndicator
from src.database.risk_analyzer import RiskLevel


class TestRiskIndicator:
    """Test suite for RiskIndicator widget."""

    @pytest.fixture
    def indicator(self):
        """Create RiskIndicator instance for testing."""
        return RiskIndicator(id="test-indicator")

    def test_initialization(self, indicator):
        """Test indicator initializes with correct defaults."""
        assert indicator.current_risk_level == RiskLevel.LOW.value
        assert indicator.current_message == ""

    def test_initialization_with_params(self):
        """Test initialization with custom parameters."""
        widget = RiskIndicator(
            name="risk_widget",
            id="custom-id",
            classes="custom-class"
        )

        assert widget.current_risk_level == RiskLevel.LOW.value

    def test_update_risk_low(self, indicator):
        """Test updating to LOW risk level."""
        # Mock child widgets
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            indicator.update_risk(RiskLevel.LOW.value, "Safe operation")

        assert indicator.current_risk_level == RiskLevel.LOW.value
        assert indicator.current_message == "Safe operation"

    def test_update_risk_medium(self, indicator):
        """Test updating to MEDIUM risk level."""
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            indicator.update_risk(RiskLevel.MEDIUM.value, "Review carefully")

        assert indicator.current_risk_level == RiskLevel.MEDIUM.value
        assert indicator.current_message == "Review carefully"

    def test_update_risk_high(self, indicator):
        """Test updating to HIGH risk level."""
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            indicator.update_risk(RiskLevel.HIGH.value, "High risk operation")

        assert indicator.current_risk_level == RiskLevel.HIGH.value

    def test_update_risk_critical(self, indicator):
        """Test updating to CRITICAL risk level."""
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            indicator.update_risk(RiskLevel.CRITICAL.value, "CRITICAL!")

        assert indicator.current_risk_level == RiskLevel.CRITICAL.value

    def test_update_risk_classes_removed(self, indicator):
        """Test old risk classes are removed."""
        # Add some existing classes
        indicator.add_class("risk-high")

        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            with patch.object(indicator, 'remove_class') as mock_remove:
                indicator.update_risk(RiskLevel.LOW.value)

                # Should remove all risk classes
                assert mock_remove.call_count >= 1

    def test_update_risk_classes_added(self, indicator):
        """Test correct risk class is added."""
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            with patch.object(indicator, 'add_class') as mock_add:
                indicator.update_risk(RiskLevel.HIGH.value)

                # Should add risk-high class
                mock_add.assert_called_with("risk-high")

    def test_update_bar_low_risk(self, indicator):
        """Test bar update for LOW risk."""
        mock_bar = Mock(spec=Static)
        mock_bar.update = Mock()

        with patch.object(indicator, 'query_one', return_value=mock_bar):
            indicator._update_bar(RiskLevel.LOW.value)

        # Should update with low bar pattern
        mock_bar.update.assert_called_once()

    def test_update_bar_critical_risk(self, indicator):
        """Test bar update for CRITICAL risk."""
        mock_bar = Mock(spec=Static)
        mock_bar.update = Mock()

        with patch.object(indicator, 'query_one', return_value=mock_bar):
            indicator._update_bar(RiskLevel.CRITICAL.value)

        mock_bar.update.assert_called_once()

    def test_update_text_low_risk(self, indicator):
        """Test text update for LOW risk."""
        mock_text = Mock(spec=Static)
        mock_text.update = Mock()
        mock_text.remove_class = Mock()
        mock_text.add_class = Mock()

        with patch.object(indicator, 'query_one', return_value=mock_text):
            indicator._update_text(RiskLevel.LOW.value, "Safe")

        # Should contain checkmark indicator
        call_args = str(mock_text.update.call_args)
        assert "✓" in call_args or "LOW" in call_args

    def test_update_text_medium_risk(self, indicator):
        """Test text update for MEDIUM risk."""
        mock_text = Mock(spec=Static)
        mock_text.update = Mock()
        mock_text.remove_class = Mock()
        mock_text.add_class = Mock()

        with patch.object(indicator, 'query_one', return_value=mock_text):
            indicator._update_text(RiskLevel.MEDIUM.value, "Caution")

        # Should contain warning indicator
        call_args = str(mock_text.update.call_args)
        assert "⚠" in call_args or "MEDIUM" in call_args

    def test_update_text_high_risk(self, indicator):
        """Test text update for HIGH risk."""
        mock_text = Mock(spec=Static)
        mock_text.update = Mock()
        mock_text.remove_class = Mock()
        mock_text.add_class = Mock()

        with patch.object(indicator, 'query_one', return_value=mock_text):
            indicator._update_text(RiskLevel.HIGH.value, "Danger")

        # Should contain double warning indicator
        call_args = str(mock_text.update.call_args)
        assert "HIGH" in call_args or "⚠⚠" in call_args

    def test_update_text_critical_risk(self, indicator):
        """Test text update for CRITICAL risk."""
        mock_text = Mock(spec=Static)
        mock_text.update = Mock()
        mock_text.remove_class = Mock()
        mock_text.add_class = Mock()

        with patch.object(indicator, 'query_one', return_value=mock_text):
            indicator._update_text(RiskLevel.CRITICAL.value, "STOP")

        # Should contain X indicator
        call_args = str(mock_text.update.call_args)
        assert "✗" in call_args or "CRITICAL" in call_args

    def test_update_text_includes_message(self, indicator):
        """Test text includes custom message."""
        mock_text = Mock(spec=Static)
        mock_text.update = Mock()
        mock_text.remove_class = Mock()
        mock_text.add_class = Mock()

        with patch.object(indicator, 'query_one', return_value=mock_text):
            indicator._update_text(RiskLevel.LOW.value, "Custom message here")

        # Should include message
        call_args = str(mock_text.update.call_args)
        assert "Custom message here" in call_args

    def test_get_risk_level(self, indicator):
        """Test getting current risk level."""
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            indicator.update_risk(RiskLevel.HIGH.value, "Test")

        assert indicator.get_risk_level() == RiskLevel.HIGH.value

    def test_get_message(self, indicator):
        """Test getting current message."""
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            indicator.update_risk(RiskLevel.MEDIUM.value, "Test message")

        assert indicator.get_message() == "Test message"

    def test_reset_to_low_risk(self, indicator):
        """Test reset sets to LOW risk."""
        # Set to high risk first
        with patch.object(indicator, 'query_one', side_effect=[
            Mock(spec=Static), Mock(spec=Static),  # First update
            Mock(spec=Static), Mock(spec=Static)   # Reset
        ]):
            indicator.update_risk(RiskLevel.HIGH.value, "Danger")
            indicator.reset()

        assert indicator.current_risk_level == RiskLevel.LOW.value
        assert indicator.current_message == ""

    def test_multiple_updates(self, indicator):
        """Test multiple risk updates."""
        levels = [
            (RiskLevel.LOW.value, "Safe"),
            (RiskLevel.MEDIUM.value, "Caution"),
            (RiskLevel.HIGH.value, "Danger"),
            (RiskLevel.CRITICAL.value, "CRITICAL")
        ]

        for level, message in levels:
            with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
                indicator.update_risk(level, message)

                assert indicator.current_risk_level == level
                assert indicator.current_message == message

    def test_update_risk_classes_low(self, indicator):
        """Test CSS class updates for LOW risk."""
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            with patch.object(indicator, 'remove_class') as mock_remove:
                with patch.object(indicator, 'add_class') as mock_add:
                    indicator._update_risk_classes(RiskLevel.LOW.value)

                    # Should remove all levels and add risk-low
                    assert mock_remove.call_count >= 4
                    mock_add.assert_called_with("risk-low")

    def test_update_risk_classes_critical(self, indicator):
        """Test CSS class updates for CRITICAL risk."""
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            with patch.object(indicator, 'remove_class'):
                with patch.object(indicator, 'add_class') as mock_add:
                    indicator._update_risk_classes(RiskLevel.CRITICAL.value)

                    mock_add.assert_called_with("risk-critical")

    def test_css_defined(self):
        """Test CSS is defined."""
        assert hasattr(RiskIndicator, 'CSS')
        assert isinstance(RiskIndicator.CSS, str)
        assert 'RiskIndicator' in RiskIndicator.CSS

    def test_css_has_all_risk_levels(self):
        """Test CSS includes all risk level classes."""
        css = RiskIndicator.CSS

        assert 'risk-low' in css
        assert 'risk-medium' in css
        assert 'risk-high' in css
        assert 'risk-critical' in css

    def test_compose_yields_widgets(self, indicator):
        """Test compose yields required widgets."""
        widgets = list(indicator.compose())

        assert len(widgets) == 2
        # Should yield risk-bar and risk-text
        assert all(isinstance(w, Static) for w in widgets)

    def test_update_without_message(self, indicator):
        """Test update with empty message."""
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            indicator.update_risk(RiskLevel.MEDIUM.value, "")

        assert indicator.current_risk_level == RiskLevel.MEDIUM.value
        assert indicator.current_message == ""

    def test_sequential_same_level_updates(self, indicator):
        """Test sequential updates with same risk level."""
        with patch.object(indicator, 'query_one', side_effect=[
            Mock(spec=Static), Mock(spec=Static),
            Mock(spec=Static), Mock(spec=Static)
        ]):
            indicator.update_risk(RiskLevel.HIGH.value, "First message")
            indicator.update_risk(RiskLevel.HIGH.value, "Second message")

        # Should update message even if level is same
        assert indicator.current_message == "Second message"

    def test_update_risk_calls_all_update_methods(self, indicator):
        """Test update_risk calls all update methods."""
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            with patch.object(indicator, '_update_risk_classes') as mock_classes:
                with patch.object(indicator, '_update_bar') as mock_bar:
                    with patch.object(indicator, '_update_text') as mock_text:
                        indicator.update_risk(RiskLevel.MEDIUM.value, "Test")

        mock_classes.assert_called_once_with(RiskLevel.MEDIUM.value)
        mock_bar.assert_called_once_with(RiskLevel.MEDIUM.value)
        mock_text.assert_called_once_with(RiskLevel.MEDIUM.value, "Test")

    def test_bar_characters_different_per_level(self, indicator):
        """Test bar uses different characters per risk level."""
        # This tests the visual distinction
        mock_bar = Mock(spec=Static)

        results = []
        for level in [RiskLevel.LOW.value, RiskLevel.MEDIUM.value,
                      RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]:
            with patch.object(indicator, 'query_one', return_value=mock_bar):
                indicator._update_bar(level)
                results.append(str(mock_bar.update.call_args))

        # All should be different
        assert len(set(results)) == 4

    def test_risk_level_persistence(self, indicator):
        """Test risk level persists across multiple gets."""
        with patch.object(indicator, 'query_one', side_effect=[Mock(spec=Static), Mock(spec=Static)]):
            indicator.update_risk(RiskLevel.HIGH.value, "Persistent")

        # Get multiple times
        for _ in range(5):
            assert indicator.get_risk_level() == RiskLevel.HIGH.value
            assert indicator.get_message() == "Persistent"
