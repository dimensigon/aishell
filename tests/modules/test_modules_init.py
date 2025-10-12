"""Tests for modules package initialization."""

import pytest
import asyncio


class TestModulesInit:
    """Test modules package __init__.py exports."""

    def test_imports_available(self):
        """Test all expected exports are available from modules package."""
        from src import modules

        assert hasattr(modules, 'ModulePanelEnricher')

    def test_module_panel_enricher_import(self):
        """Test ModulePanelEnricher can be imported from modules."""
        from src.modules import ModulePanelEnricher

        assert ModulePanelEnricher is not None
        assert callable(ModulePanelEnricher)

    def test_all_exports(self):
        """Test __all__ contains expected exports."""
        from src import modules

        expected_exports = {'ModulePanelEnricher'}
        assert set(modules.__all__) == expected_exports

    def test_module_panel_enricher_is_same_class(self):
        """Test ModulePanelEnricher from modules is same as from panel_enricher."""
        from src.modules import ModulePanelEnricher as ModulesEnricher
        from src.modules.panel_enricher import ModulePanelEnricher as PanelEnricher

        assert ModulesEnricher is PanelEnricher

    @pytest.mark.asyncio
    async def test_can_instantiate_enricher_from_modules(self):
        """Test ModulePanelEnricher can be instantiated when imported from modules."""
        from src.modules import ModulePanelEnricher

        enricher = ModulePanelEnricher()
        assert enricher is not None
        assert hasattr(enricher, 'max_workers')

    def test_module_docstring(self):
        """Test modules package has docstring."""
        from src import modules

        assert modules.__doc__ is not None
        assert len(modules.__doc__) > 0

    def test_no_unexpected_exports(self):
        """Test modules package doesn't export unexpected items."""
        from src import modules

        public_attrs = [attr for attr in dir(modules) if not attr.startswith('_')]
        expected = {'ModulePanelEnricher'}

        # Should only have expected exports
        assert expected.issubset(set(public_attrs))

    @pytest.mark.asyncio
    async def test_enricher_attributes_accessible(self):
        """Test ModulePanelEnricher attributes accessible from modules import."""
        from src.modules import ModulePanelEnricher

        enricher = ModulePanelEnricher()
        assert hasattr(enricher, 'max_workers')
        assert hasattr(enricher, 'queue')
        assert hasattr(enricher, 'register_context_provider')
        assert hasattr(enricher, 'enqueue_enrichment')

    def test_multiple_imports_same_reference(self):
        """Test multiple imports reference same class."""
        from src.modules import ModulePanelEnricher as Enricher1
        from src.modules import ModulePanelEnricher as Enricher2

        assert Enricher1 is Enricher2

    @pytest.mark.asyncio
    async def test_enricher_default_initialization(self):
        """Test ModulePanelEnricher has correct default initialization."""
        from src.modules import ModulePanelEnricher

        enricher = ModulePanelEnricher()
        assert enricher.max_workers == 4
        assert enricher.running is False
        assert len(enricher.enrichment_cache) == 0

    @pytest.mark.asyncio
    async def test_enricher_custom_workers(self):
        """Test ModulePanelEnricher accepts custom worker count."""
        from src.modules import ModulePanelEnricher

        enricher = ModulePanelEnricher(max_workers=8)
        assert enricher.max_workers == 8

    def test_priority_enum_accessible(self):
        """Test Priority enum is accessible from panel_enricher."""
        from src.modules.panel_enricher import Priority

        assert hasattr(Priority, 'LOW')
        assert hasattr(Priority, 'MEDIUM')
        assert hasattr(Priority, 'HIGH')
        assert hasattr(Priority, 'CRITICAL')

    def test_enrichment_task_accessible(self):
        """Test EnrichmentTask is accessible from panel_enricher."""
        from src.modules.panel_enricher import EnrichmentTask

        assert EnrichmentTask is not None
        assert callable(EnrichmentTask)
