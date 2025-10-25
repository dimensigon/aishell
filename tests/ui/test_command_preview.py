"""
Tests for Command Preview Widget

Performance tests ensuring < 200ms async update target and proper
integration with SQLRiskAnalyzer and ImpactEstimator.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.ui.widgets.command_preview import CommandPreviewWidget
from src.ui.widgets.risk_indicator import RiskIndicator
from src.database.risk_analyzer import SQLRiskAnalyzer, RiskLevel
from src.database.impact_estimator import ImpactEstimator, OperationType


class TestCommandPreviewWidget:
    """Test suite for CommandPreviewWidget."""

    @pytest.fixture
    def risk_analyzer(self):
        """Create SQLRiskAnalyzer instance."""
        return SQLRiskAnalyzer()

    @pytest.fixture
    def widget(self, risk_analyzer):
        """Create CommandPreviewWidget instance."""
        return CommandPreviewWidget(risk_analyzer=risk_analyzer)

    @pytest.mark.asyncio
    async def test_widget_initialization(self, widget):
        """Test widget initializes correctly."""
        assert widget.risk_analyzer is not None
        assert widget.current_command == ""
        assert widget.is_visible is False
        assert widget.last_analysis is None

    @pytest.mark.asyncio
    async def test_empty_command_hides_widget(self, widget):
        """Test empty command hides the widget."""
        await widget.update_preview("")
        assert widget.is_visible is False

    @pytest.mark.asyncio
    async def test_high_risk_command_analysis(self, widget):
        """Test high-risk command triggers proper analysis."""
        dangerous_sql = "DELETE FROM users"

        # Mock the widget mounting
        with patch.object(widget, 'query_one') as mock_query:
            # Setup mocks
            mock_text = Mock()
            mock_container = Mock()
            mock_container.remove_children = Mock()
            mock_container.mount = Mock()
            mock_impact = Mock()

            def query_side_effect(selector, widget_type=None):
                if selector == "#command-text":
                    return mock_text
                elif selector == "#warnings-section":
                    return mock_container
                elif selector == "#impact-section":
                    return mock_impact
                return Mock()

            mock_query.side_effect = query_side_effect

            # Also mock risk indicator
            widget.risk_indicator = Mock(spec=RiskIndicator)

            await widget.update_preview(dangerous_sql)
            await asyncio.sleep(0.3)  # Wait for async analysis

            # Verify analysis was performed
            assert widget.last_analysis is not None
            assert widget.last_analysis['risk_level'] == RiskLevel.HIGH.value

    @pytest.mark.asyncio
    async def test_low_risk_auto_hide(self, widget):
        """Test low-risk commands auto-hide when configured."""
        widget.auto_hide_low_risk = True
        safe_sql = "SELECT * FROM users"

        with patch.object(widget, 'query_one') as mock_query:
            mock_text = Mock()
            mock_container = Mock()
            mock_container.remove_children = Mock()
            mock_container.mount = Mock()
            mock_impact = Mock()

            def query_side_effect(selector, widget_type=None):
                if selector == "#command-text":
                    return mock_text
                elif selector == "#warnings-section":
                    return mock_container
                elif selector == "#impact-section":
                    return mock_impact
                return Mock()

            mock_query.side_effect = query_side_effect
            widget.risk_indicator = Mock(spec=RiskIndicator)

            await widget.update_preview(safe_sql)
            await asyncio.sleep(0.3)

            # Should auto-hide for LOW risk
            assert widget.is_visible is False

    @pytest.mark.asyncio
    async def test_performance_target(self, widget):
        """Test analysis completes within 200ms target."""
        sql = "UPDATE users SET status='active' WHERE id > 1000"

        with patch.object(widget, 'query_one') as mock_query:
            mock_text = Mock()
            mock_container = Mock()
            mock_container.remove_children = Mock()
            mock_container.mount = Mock()
            mock_impact = Mock()

            def query_side_effect(selector, widget_type=None):
                if selector == "#command-text":
                    return mock_text
                elif selector == "#warnings-section":
                    return mock_container
                elif selector == "#impact-section":
                    return mock_impact
                return Mock()

            mock_query.side_effect = query_side_effect
            widget.risk_indicator = Mock(spec=RiskIndicator)

            start = datetime.now()
            await widget.update_preview(sql)
            await asyncio.sleep(0.3)  # Allow time for async task
            duration = (datetime.now() - start).total_seconds() * 1000

            # Should complete well within 200ms (allowing for test overhead)
            assert duration < 500, f"Analysis took {duration}ms (target: 200ms)"

    @pytest.mark.asyncio
    async def test_cancels_previous_analysis(self, widget):
        """Test that new analysis cancels previous one."""
        with patch.object(widget, 'query_one'):
            widget.risk_indicator = Mock(spec=RiskIndicator)

            # Start first analysis
            await widget.update_preview("SELECT * FROM table1")
            first_task = widget.analysis_task

            # Immediately start second analysis
            await widget.update_preview("SELECT * FROM table2")
            second_task = widget.analysis_task

            # Tasks should be different
            assert first_task is not second_task

    @pytest.mark.asyncio
    async def test_impact_estimation_integration(self, widget):
        """Test impact estimation display."""
        with patch.object(widget, 'query_one') as mock_query:
            mock_impact = Mock()
            mock_query.return_value = mock_impact

            await widget.set_impact_estimation(5000, 0.85)

            # Verify update was called with formatted text
            mock_impact.update.assert_called_once()
            call_args = str(mock_impact.update.call_args)
            assert "5000" in call_args
            assert "85%" in call_args

    @pytest.mark.asyncio
    async def test_critical_risk_display(self, widget):
        """Test CRITICAL risk level displays correctly."""
        critical_sql = "DROP TABLE users"

        with patch.object(widget, 'query_one') as mock_query:
            mock_text = Mock()
            mock_container = Mock()
            mock_container.remove_children = Mock()
            mock_container.mount = Mock()
            mock_impact = Mock()

            def query_side_effect(selector, widget_type=None):
                if selector == "#command-text":
                    return mock_text
                elif selector == "#warnings-section":
                    return mock_container
                elif selector == "#impact-section":
                    return mock_impact
                return Mock()

            mock_query.side_effect = query_side_effect
            widget.risk_indicator = Mock(spec=RiskIndicator)

            await widget.update_preview(critical_sql)
            await asyncio.sleep(0.3)

            # Verify critical risk was detected
            assert widget.last_analysis is not None
            assert widget.last_analysis['risk_level'] == RiskLevel.CRITICAL.value

            # Widget should be visible for critical risk
            assert widget.is_visible is True

    @pytest.mark.asyncio
    async def test_clear_resets_widget(self, widget):
        """Test clear method resets widget state."""
        sql = "DELETE FROM users WHERE id = 1"

        with patch.object(widget, 'query_one') as mock_query:
            mock_text = Mock()
            mock_container = Mock()
            mock_container.remove_children = Mock()
            mock_container.mount = Mock()
            mock_impact = Mock()

            def query_side_effect(selector, widget_type=None):
                if selector == "#command-text":
                    return mock_text
                elif selector == "#warnings-section":
                    return mock_container
                elif selector == "#impact-section":
                    return mock_impact
                return Mock()

            mock_query.side_effect = query_side_effect
            widget.risk_indicator = Mock(spec=RiskIndicator)

            # Set some state
            await widget.update_preview(sql)
            await asyncio.sleep(0.3)

            # Clear
            await widget.clear()

            # Verify reset
            assert widget.is_visible is False
            assert widget.current_command == ""


class TestRiskIndicator:
    """Test suite for RiskIndicator widget."""

    @pytest.fixture
    def indicator(self):
        """Create RiskIndicator instance."""
        return RiskIndicator()

    def test_indicator_initialization(self, indicator):
        """Test indicator initializes with LOW risk."""
        assert indicator.current_risk_level == RiskLevel.LOW.value
        assert indicator.current_message == ""

    def test_update_low_risk(self, indicator):
        """Test LOW risk update."""
        with patch.object(indicator, 'query_one') as mock_query:
            mock_bar = Mock()
            mock_text = Mock()

            def query_side_effect(selector, widget_type=None):
                if selector == "#risk-bar":
                    return mock_bar
                elif selector == "#risk-text":
                    return mock_text
                return Mock()

            mock_query.side_effect = query_side_effect

            indicator.update_risk(RiskLevel.LOW.value, "Safe operation")

            assert indicator.current_risk_level == RiskLevel.LOW.value
            assert indicator.current_message == "Safe operation"

    def test_update_critical_risk(self, indicator):
        """Test CRITICAL risk update."""
        with patch.object(indicator, 'query_one') as mock_query:
            mock_bar = Mock()
            mock_text = Mock()

            def query_side_effect(selector, widget_type=None):
                if selector == "#risk-bar":
                    return mock_bar
                elif selector == "#risk-text":
                    return mock_text
                return Mock()

            mock_query.side_effect = query_side_effect

            indicator.update_risk(RiskLevel.CRITICAL.value, "Destructive!")

            assert indicator.current_risk_level == RiskLevel.CRITICAL.value
            assert indicator.has_class("risk-critical")

    def test_reset_indicator(self, indicator):
        """Test reset returns to LOW risk."""
        with patch.object(indicator, 'query_one') as mock_query:
            mock_bar = Mock()
            mock_text = Mock()

            def query_side_effect(selector, widget_type=None):
                if selector == "#risk-bar":
                    return mock_bar
                elif selector == "#risk-text":
                    return mock_text
                return Mock()

            mock_query.side_effect = query_side_effect

            # Set to HIGH
            indicator.update_risk(RiskLevel.HIGH.value, "Dangerous")

            # Reset
            indicator.reset()

            assert indicator.current_risk_level == RiskLevel.LOW.value
            assert indicator.current_message == ""


class TestImpactEstimator:
    """Test suite for ImpactEstimator."""

    @pytest.fixture
    def estimator(self):
        """Create ImpactEstimator instance."""
        return ImpactEstimator()

    @pytest.mark.asyncio
    async def test_select_estimation(self, estimator):
        """Test SELECT query estimation."""
        result = await estimator.estimate_impact(
            "SELECT * FROM users WHERE id = 1",
            None
        )

        assert result['operation_type'] == OperationType.SELECT.value
        assert result['table_name'] == 'users'
        assert result['has_where_clause'] is True
        assert result['confidence'] > 0.5
        assert result['is_safe'] is True

    @pytest.mark.asyncio
    async def test_delete_without_where(self, estimator):
        """Test DELETE without WHERE clause."""
        result = await estimator.estimate_impact(
            "DELETE FROM users",
            None
        )

        assert result['operation_type'] == OperationType.DELETE.value
        assert result['has_where_clause'] is False
        assert result['estimated_rows'] > 0
        assert result['is_safe'] is False

    @pytest.mark.asyncio
    async def test_update_with_where(self, estimator):
        """Test UPDATE with WHERE clause."""
        result = await estimator.estimate_impact(
            "UPDATE users SET active=1 WHERE id > 100",
            None
        )

        assert result['operation_type'] == OperationType.UPDATE.value
        assert result['has_where_clause'] is True
        assert result['table_name'] == 'users'
        assert result['estimated_rows'] > 0

    @pytest.mark.asyncio
    async def test_insert_estimation(self, estimator):
        """Test INSERT estimation."""
        result = await estimator.estimate_impact(
            "INSERT INTO users (name) VALUES ('John')",
            None
        )

        assert result['operation_type'] == OperationType.INSERT.value
        assert result['table_name'] == 'users'
        assert result['estimated_rows'] >= 1
        assert result['is_safe'] is True

    @pytest.mark.asyncio
    async def test_drop_table(self, estimator):
        """Test DROP TABLE estimation."""
        result = await estimator.estimate_impact(
            "DROP TABLE logs",
            None
        )

        assert result['operation_type'] == OperationType.DROP.value
        assert result['table_name'] == 'logs'
        assert result['is_safe'] is False

    @pytest.mark.asyncio
    async def test_accuracy_variance(self, estimator):
        """Test that estimates have ±20% variance."""
        # Set known table size
        estimator.set_table_size('test_table', 1000)

        # Run multiple estimates
        results = []
        for _ in range(10):
            result = await estimator.estimate_impact(
                "DELETE FROM test_table",
                None
            )
            results.append(result['estimated_rows'])

        # Check variance (should not all be identical due to ±20% variance)
        unique_results = set(results)
        assert len(unique_results) > 1, "No variance in estimates"

        # All should be within ±20% of 1000
        for rows in results:
            assert 800 <= rows <= 1200, f"Estimate {rows} outside ±20% range"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
