"""Tests for async module system."""

import pytest
import asyncio
from datetime import datetime
from src.modules.panel_enricher import (
    ModulePanelEnricher,
    Priority,
    EnrichmentTask
)


@pytest.fixture
def enricher():
    """Create panel enricher fixture."""
    return ModulePanelEnricher(max_workers=2)


@pytest.mark.asyncio
async def test_enricher_initialization(enricher):
    """Test enricher initialization."""
    assert enricher.max_workers == 2
    assert enricher.running is False
    assert len(enricher.workers) == 0
    assert len(enricher.context_providers) == 0


@pytest.mark.asyncio
async def test_register_context_provider(enricher):
    """Test registering context providers."""
    async def mock_provider(panel_id, context):
        return {'data': f'context for {panel_id}'}

    enricher.register_context_provider('test_provider', mock_provider)
    assert 'test_provider' in enricher.context_providers
    assert enricher.context_providers['test_provider'] == mock_provider


@pytest.mark.asyncio
async def test_enqueue_enrichment(enricher):
    """Test enqueueing enrichment tasks."""
    await enricher.enqueue_enrichment('panel_1', Priority.HIGH)
    assert enricher.queue.qsize() == 1

    await enricher.enqueue_enrichment('panel_2', Priority.LOW)
    assert enricher.queue.qsize() == 2


@pytest.mark.asyncio
async def test_priority_ordering(enricher):
    """Test priority queue ordering."""
    await enricher.enqueue_enrichment('low', Priority.LOW)
    await enricher.enqueue_enrichment('high', Priority.HIGH)
    await enricher.enqueue_enrichment('medium', Priority.MEDIUM)

    # Get tasks and check order (highest priority first)
    task1 = await enricher.queue.get()
    task2 = await enricher.queue.get()
    task3 = await enricher.queue.get()

    assert task1.panel_id == 'high'
    assert task2.panel_id == 'medium'
    assert task3.panel_id == 'low'


@pytest.mark.asyncio
async def test_start_stop_workers(enricher):
    """Test starting and stopping workers."""
    await enricher.start()
    assert enricher.running is True
    assert len(enricher.workers) == 2

    await enricher.stop()
    assert enricher.running is False
    assert len(enricher.workers) == 0


@pytest.mark.asyncio
async def test_enrichment_with_providers(enricher):
    """Test enrichment with context providers."""
    results = []

    async def mock_provider(panel_id, context):
        return {'provider_data': f'enriched {panel_id}'}

    async def result_callback(panel_id, result):
        results.append(result)

    enricher.register_context_provider('test', mock_provider)

    await enricher.start()
    await enricher.enqueue_enrichment(
        'panel_1',
        Priority.HIGH,
        context={'base': 'data'},
        callback=result_callback
    )

    # Wait for processing
    await asyncio.sleep(0.2)
    await enricher.stop()

    assert len(results) == 1
    assert results[0]['panel_id'] == 'panel_1'
    assert 'test' in results[0]['context']
    assert results[0]['context']['test']['provider_data'] == 'enriched panel_1'


@pytest.mark.asyncio
async def test_cache_functionality(enricher):
    """Test enrichment cache."""
    async def mock_provider(panel_id, context):
        return {'data': 'test'}

    enricher.register_context_provider('test', mock_provider)

    await enricher.start()

    # First enrichment
    await enricher.enqueue_enrichment('panel_1', Priority.HIGH)
    await asyncio.sleep(0.1)

    stats_before = enricher.get_stats()

    # Second enrichment (should hit cache)
    await enricher.enqueue_enrichment('panel_1', Priority.HIGH)
    await asyncio.sleep(0.1)

    stats_after = enricher.get_stats()

    await enricher.stop()

    assert stats_after['cache_hits'] > stats_before['cache_hits']


@pytest.mark.asyncio
async def test_error_handling_in_provider(enricher):
    """Test error handling in context providers."""
    async def failing_provider(panel_id, context):
        raise ValueError("Provider error")

    enricher.register_context_provider('failing', failing_provider)

    await enricher.start()
    await enricher.enqueue_enrichment('panel_1', Priority.HIGH)
    await asyncio.sleep(0.2)
    await enricher.stop()

    enriched = await enricher.get_enriched('panel_1')
    assert enriched is not None
    assert 'failing' in enriched['context']
    assert 'error' in enriched['context']['failing']


@pytest.mark.asyncio
async def test_get_enriched_data(enricher):
    """Test retrieving enriched data."""
    async def mock_provider(panel_id, context):
        return {'data': 'test'}

    enricher.register_context_provider('test', mock_provider)

    await enricher.start()
    await enricher.enqueue_enrichment('panel_1', Priority.HIGH)
    await asyncio.sleep(0.1)
    await enricher.stop()

    enriched = await enricher.get_enriched('panel_1')
    assert enriched is not None
    assert enriched['panel_id'] == 'panel_1'
    assert 'timestamp' in enriched


@pytest.mark.asyncio
async def test_clear_cache(enricher):
    """Test cache clearing."""
    enricher.enrichment_cache['panel_1'] = {'data': 'test'}
    enricher.enrichment_cache['panel_2'] = {'data': 'test'}

    # Clear specific panel
    enricher.clear_cache('panel_1')
    assert 'panel_1' not in enricher.enrichment_cache
    assert 'panel_2' in enricher.enrichment_cache

    # Clear all
    enricher.clear_cache()
    assert len(enricher.enrichment_cache) == 0


@pytest.mark.asyncio
async def test_statistics(enricher):
    """Test statistics tracking."""
    async def mock_provider(panel_id, context):
        return {'data': 'test'}

    enricher.register_context_provider('test', mock_provider)

    await enricher.start()
    await enricher.enqueue_enrichment('panel_1', Priority.HIGH)
    await enricher.enqueue_enrichment('panel_2', Priority.HIGH)
    await asyncio.sleep(0.2)
    await enricher.stop()

    stats = enricher.get_stats()
    assert stats['total_enriched'] == 2
    assert stats['cache_size'] == 2
    assert 'workers' in stats


@pytest.mark.asyncio
async def test_multiple_workers_concurrent(enricher):
    """Test multiple workers processing concurrently."""
    processed = []

    async def slow_provider(panel_id, context):
        await asyncio.sleep(0.1)
        processed.append(panel_id)
        return {'data': panel_id}

    enricher.register_context_provider('slow', slow_provider)

    await enricher.start()

    # Enqueue multiple tasks
    for i in range(4):
        await enricher.enqueue_enrichment(f'panel_{i}', Priority.HIGH)

    await asyncio.sleep(0.3)
    await enricher.stop()

    # All tasks should be processed
    assert len(processed) == 4
