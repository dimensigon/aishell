"""Comprehensive tests for panel enricher module."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from src.modules.panel_enricher import (
    Priority,
    EnrichmentTask,
    ModulePanelEnricher
)


class TestPriority:
    """Test Priority enum."""

    def test_priority_values(self):
        """Test Priority enum has correct values."""
        assert Priority.LOW == 0
        assert Priority.MEDIUM == 1
        assert Priority.HIGH == 2
        assert Priority.CRITICAL == 3

    def test_priority_ordering(self):
        """Test Priority enum values can be compared."""
        assert Priority.LOW < Priority.MEDIUM
        assert Priority.MEDIUM < Priority.HIGH
        assert Priority.HIGH < Priority.CRITICAL

    def test_priority_names(self):
        """Test Priority enum has correct names."""
        assert Priority.LOW.name == 'LOW'
        assert Priority.MEDIUM.name == 'MEDIUM'
        assert Priority.HIGH.name == 'HIGH'
        assert Priority.CRITICAL.name == 'CRITICAL'


class TestEnrichmentTask:
    """Test EnrichmentTask dataclass."""

    def test_enrichment_task_creation(self):
        """Test EnrichmentTask can be created."""
        task = EnrichmentTask(priority=1, panel_id='panel-123')

        assert task.priority == 1
        assert task.panel_id == 'panel-123'
        assert isinstance(task.context, dict)
        assert isinstance(task.timestamp, datetime)

    def test_enrichment_task_with_context(self):
        """Test EnrichmentTask with custom context."""
        context = {'user_id': 'user-1', 'data': 'test'}
        task = EnrichmentTask(priority=2, panel_id='panel-456', context=context)

        assert task.context == context

    def test_enrichment_task_with_callback(self):
        """Test EnrichmentTask with callback function."""
        callback = Mock()
        task = EnrichmentTask(priority=1, panel_id='panel-789', callback=callback)

        assert task.callback is callback

    def test_enrichment_task_ordering(self):
        """Test EnrichmentTask ordering by priority."""
        task1 = EnrichmentTask(priority=1, panel_id='low')
        task2 = EnrichmentTask(priority=2, panel_id='high')

        assert task1 < task2

    def test_enrichment_task_default_context(self):
        """Test EnrichmentTask has empty dict as default context."""
        task = EnrichmentTask(priority=1, panel_id='panel-123')

        assert task.context == {}
        assert isinstance(task.context, dict)

    def test_enrichment_task_timestamp_auto_generated(self):
        """Test EnrichmentTask timestamp is automatically generated."""
        before = datetime.now()
        task = EnrichmentTask(priority=1, panel_id='panel-123')
        after = datetime.now()

        assert before <= task.timestamp <= after


class TestModulePanelEnricherInit:
    """Test ModulePanelEnricher initialization."""

    def test_enricher_init_default(self):
        """Test enricher initializes with default values."""
        enricher = ModulePanelEnricher()

        assert enricher.max_workers == 4
        assert isinstance(enricher.queue, asyncio.PriorityQueue)
        assert enricher.workers == []
        assert enricher.running is False
        assert enricher.enrichment_cache == {}
        assert enricher.context_providers == {}

    def test_enricher_init_custom_workers(self):
        """Test enricher initializes with custom worker count."""
        enricher = ModulePanelEnricher(max_workers=8)

        assert enricher.max_workers == 8

    def test_enricher_init_stats(self):
        """Test enricher initializes statistics."""
        enricher = ModulePanelEnricher()

        assert enricher._stats == {
            'total_enriched': 0,
            'cache_hits': 0,
            'errors': 0
        }


class TestRegisterContextProvider:
    """Test context provider registration."""

    def test_register_context_provider(self):
        """Test registering a context provider."""
        enricher = ModulePanelEnricher()
        provider = AsyncMock()

        enricher.register_context_provider('test_provider', provider)

        assert 'test_provider' in enricher.context_providers
        assert enricher.context_providers['test_provider'] is provider

    def test_register_multiple_providers(self):
        """Test registering multiple context providers."""
        enricher = ModulePanelEnricher()
        provider1 = AsyncMock()
        provider2 = AsyncMock()

        enricher.register_context_provider('provider1', provider1)
        enricher.register_context_provider('provider2', provider2)

        assert len(enricher.context_providers) == 2
        assert enricher.context_providers['provider1'] is provider1
        assert enricher.context_providers['provider2'] is provider2

    def test_register_provider_overwrites(self):
        """Test registering provider with same name overwrites."""
        enricher = ModulePanelEnricher()
        provider1 = AsyncMock()
        provider2 = AsyncMock()

        enricher.register_context_provider('provider', provider1)
        enricher.register_context_provider('provider', provider2)

        assert enricher.context_providers['provider'] is provider2


class TestEnqueueEnrichment:
    """Test enqueueing enrichment tasks."""

    @pytest.mark.asyncio
    async def test_enqueue_enrichment_basic(self):
        """Test enqueuing basic enrichment task."""
        enricher = ModulePanelEnricher()

        await enricher.enqueue_enrichment('panel-123')

        assert enricher.queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_enqueue_enrichment_with_priority(self):
        """Test enqueuing task with custom priority."""
        enricher = ModulePanelEnricher()

        await enricher.enqueue_enrichment('panel-123', priority=Priority.HIGH)

        task = await enricher.queue.get()
        assert task.panel_id == 'panel-123'
        assert task.priority == -Priority.HIGH  # Negative for correct ordering

    @pytest.mark.asyncio
    async def test_enqueue_enrichment_with_context(self):
        """Test enqueuing task with context."""
        enricher = ModulePanelEnricher()
        context = {'key': 'value'}

        await enricher.enqueue_enrichment('panel-123', context=context)

        task = await enricher.queue.get()
        assert task.context == context

    @pytest.mark.asyncio
    async def test_enqueue_enrichment_with_callback(self):
        """Test enqueuing task with callback."""
        enricher = ModulePanelEnricher()
        callback = Mock()

        await enricher.enqueue_enrichment('panel-123', callback=callback)

        task = await enricher.queue.get()
        assert task.callback is callback

    @pytest.mark.asyncio
    async def test_enqueue_multiple_tasks(self):
        """Test enqueuing multiple tasks."""
        enricher = ModulePanelEnricher()

        await enricher.enqueue_enrichment('panel-1')
        await enricher.enqueue_enrichment('panel-2')
        await enricher.enqueue_enrichment('panel-3')

        assert enricher.queue.qsize() == 3

    @pytest.mark.asyncio
    async def test_enqueue_priority_ordering(self):
        """Test tasks are dequeued in priority order."""
        enricher = ModulePanelEnricher()

        await enricher.enqueue_enrichment('low', priority=Priority.LOW)
        await enricher.enqueue_enrichment('high', priority=Priority.HIGH)
        await enricher.enqueue_enrichment('medium', priority=Priority.MEDIUM)

        task1 = await enricher.queue.get()
        task2 = await enricher.queue.get()
        task3 = await enricher.queue.get()

        assert task1.panel_id == 'high'
        assert task2.panel_id == 'medium'
        assert task3.panel_id == 'low'


class TestEnrichmentWorker:
    """Test enrichment worker functionality."""

    @pytest.mark.asyncio
    async def test_worker_processes_task(self):
        """Test worker processes enqueued task."""
        enricher = ModulePanelEnricher(max_workers=1)

        await enricher.start()
        await enricher.enqueue_enrichment('panel-123')

        # Wait for processing with timeout
        await asyncio.wait_for(enricher.queue.join(), timeout=2.0)
        await enricher.stop()

        assert enricher._stats['total_enriched'] == 1

    @pytest.mark.asyncio
    async def test_worker_uses_cache(self):
        """Test worker uses cached results."""
        enricher = ModulePanelEnricher(max_workers=1)
        enricher.enrichment_cache['panel-123'] = {'cached': True}

        await enricher.start()
        await enricher.enqueue_enrichment('panel-123')

        await asyncio.wait_for(enricher.queue.join(), timeout=2.0)
        await enricher.stop()

        assert enricher._stats['cache_hits'] == 1
        assert enricher._stats['total_enriched'] == 0

    @pytest.mark.asyncio
    async def test_worker_calls_callback(self):
        """Test worker calls callback after enrichment."""
        enricher = ModulePanelEnricher(max_workers=1)
        callback = AsyncMock()

        await enricher.start()
        await enricher.enqueue_enrichment('panel-123', callback=callback)

        await asyncio.wait_for(enricher.queue.join(), timeout=2.0)
        await enricher.stop()

        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_worker_handles_errors(self):
        """Test worker handles enrichment errors gracefully."""
        enricher = ModulePanelEnricher(max_workers=1)

        async def failing_provider(panel_id, context):
            raise Exception("Provider error")

        enricher.register_context_provider('failing', failing_provider)

        await enricher.start()
        await enricher.enqueue_enrichment('panel-123')

        await asyncio.wait_for(enricher.queue.join(), timeout=2.0)
        await enricher.stop()

        # Should complete despite error
        assert enricher._stats['total_enriched'] == 1


class TestEnrichPanel:
    """Test panel enrichment logic."""

    @pytest.mark.asyncio
    async def test_enrich_panel_basic(self):
        """Test basic panel enrichment."""
        enricher = ModulePanelEnricher()

        result = await enricher._enrich_panel('panel-123', {})

        assert result['panel_id'] == 'panel-123'
        assert 'timestamp' in result
        assert 'context' in result

    @pytest.mark.asyncio
    async def test_enrich_panel_with_context(self):
        """Test panel enrichment preserves context."""
        enricher = ModulePanelEnricher()
        context = {'user': 'test', 'value': 42}

        result = await enricher._enrich_panel('panel-123', context)

        assert result['context']['user'] == 'test'
        assert result['context']['value'] == 42

    @pytest.mark.asyncio
    async def test_enrich_panel_calls_providers(self):
        """Test panel enrichment calls all registered providers."""
        enricher = ModulePanelEnricher()

        provider1 = AsyncMock(return_value={'data1': 'value1'})
        provider2 = AsyncMock(return_value={'data2': 'value2'})

        enricher.register_context_provider('provider1', provider1)
        enricher.register_context_provider('provider2', provider2)

        result = await enricher._enrich_panel('panel-123', {})

        provider1.assert_called_once_with('panel-123', {})
        provider2.assert_called_once_with('panel-123', {})
        assert result['context']['provider1'] == {'data1': 'value1'}
        assert result['context']['provider2'] == {'data2': 'value2'}

    @pytest.mark.asyncio
    async def test_enrich_panel_handles_provider_errors(self):
        """Test panel enrichment handles provider errors."""
        enricher = ModulePanelEnricher()

        async def failing_provider(panel_id, context):
            raise ValueError("Provider failed")

        enricher.register_context_provider('failing', failing_provider)

        result = await enricher._enrich_panel('panel-123', {})

        assert 'failing' in result['context']
        assert 'error' in result['context']['failing']


class TestStartStop:
    """Test starting and stopping enricher."""

    @pytest.mark.asyncio
    async def test_start_creates_workers(self):
        """Test start creates worker tasks."""
        enricher = ModulePanelEnricher(max_workers=3)

        await enricher.start()

        assert len(enricher.workers) == 3
        assert enricher.running is True

        await enricher.stop()

    @pytest.mark.asyncio
    async def test_start_already_running(self):
        """Test start when already running."""
        enricher = ModulePanelEnricher()

        await enricher.start()
        worker_count = len(enricher.workers)

        await enricher.start()  # Should not create more workers

        assert len(enricher.workers) == worker_count

        await enricher.stop()

    @pytest.mark.asyncio
    async def test_stop_waits_for_queue(self):
        """Test stop waits for queue to empty."""
        enricher = ModulePanelEnricher(max_workers=1)

        await enricher.start()
        await enricher.enqueue_enrichment('panel-1')
        await enricher.enqueue_enrichment('panel-2')

        # Wait for queue to be processed
        await asyncio.wait_for(enricher.queue.join(), timeout=2.0)
        await enricher.stop()

        assert enricher.queue.qsize() == 0
        assert enricher.running is False

    @pytest.mark.asyncio
    async def test_stop_cancels_workers(self):
        """Test stop cancels worker tasks."""
        enricher = ModulePanelEnricher(max_workers=2)

        await enricher.start()
        await enricher.stop()

        assert len(enricher.workers) == 0


class TestGetEnriched:
    """Test getting enriched data."""

    @pytest.mark.asyncio
    async def test_get_enriched_exists(self):
        """Test get_enriched returns cached data."""
        enricher = ModulePanelEnricher()
        enricher.enrichment_cache['panel-123'] = {'data': 'test'}

        result = await enricher.get_enriched('panel-123')

        assert result == {'data': 'test'}

    @pytest.mark.asyncio
    async def test_get_enriched_not_exists(self):
        """Test get_enriched returns None for non-existent panel."""
        enricher = ModulePanelEnricher()

        result = await enricher.get_enriched('panel-999')

        assert result is None


class TestClearCache:
    """Test cache clearing."""

    def test_clear_cache_specific_panel(self):
        """Test clearing cache for specific panel."""
        enricher = ModulePanelEnricher()
        enricher.enrichment_cache = {
            'panel-1': {'data': '1'},
            'panel-2': {'data': '2'}
        }

        enricher.clear_cache('panel-1')

        assert 'panel-1' not in enricher.enrichment_cache
        assert 'panel-2' in enricher.enrichment_cache

    def test_clear_cache_all(self):
        """Test clearing entire cache."""
        enricher = ModulePanelEnricher()
        enricher.enrichment_cache = {
            'panel-1': {'data': '1'},
            'panel-2': {'data': '2'}
        }

        enricher.clear_cache()

        assert len(enricher.enrichment_cache) == 0

    def test_clear_cache_non_existent(self):
        """Test clearing non-existent panel doesn't raise error."""
        enricher = ModulePanelEnricher()

        enricher.clear_cache('panel-999')  # Should not raise


class TestGetStats:
    """Test statistics retrieval."""

    def test_get_stats_initial(self):
        """Test get_stats returns initial statistics."""
        enricher = ModulePanelEnricher()

        stats = enricher.get_stats()

        assert stats['total_enriched'] == 0
        assert stats['cache_hits'] == 0
        assert stats['errors'] == 0
        assert stats['cache_size'] == 0
        assert stats['queue_size'] == 0
        assert stats['workers'] == 0

    @pytest.mark.asyncio
    async def test_get_stats_after_enrichment(self):
        """Test get_stats reflects enrichment activity."""
        enricher = ModulePanelEnricher(max_workers=1)

        await enricher.start()
        await enricher.enqueue_enrichment('panel-1')
        await enricher.enqueue_enrichment('panel-2')

        await asyncio.wait_for(enricher.queue.join(), timeout=2.0)
        await enricher.stop()

        stats = enricher.get_stats()

        assert stats['total_enriched'] == 2
        assert stats['cache_size'] == 2

    def test_get_stats_includes_queue_size(self):
        """Test get_stats includes queue size."""
        enricher = ModulePanelEnricher()

        asyncio.run(enricher.enqueue_enrichment('panel-1'))
        asyncio.run(enricher.enqueue_enrichment('panel-2'))

        stats = enricher.get_stats()

        assert stats['queue_size'] == 2


class TestSafeCallback:
    """Test safe callback execution."""

    @pytest.mark.asyncio
    async def test_safe_callback_async(self):
        """Test safe callback with async function."""
        enricher = ModulePanelEnricher()
        callback = AsyncMock()

        await enricher._safe_callback(callback, 'panel-123', {'result': 'data'})

        callback.assert_called_once_with('panel-123', {'result': 'data'})

    @pytest.mark.asyncio
    async def test_safe_callback_sync(self):
        """Test safe callback with sync function."""
        enricher = ModulePanelEnricher()
        callback = Mock()

        await enricher._safe_callback(callback, 'panel-123', {'result': 'data'})

        callback.assert_called_once_with('panel-123', {'result': 'data'})

    @pytest.mark.asyncio
    async def test_safe_callback_handles_errors(self):
        """Test safe callback handles callback errors."""
        enricher = ModulePanelEnricher()

        def failing_callback(panel_id, result):
            raise Exception("Callback failed")

        # Should not raise
        await enricher._safe_callback(failing_callback, 'panel-123', {})
