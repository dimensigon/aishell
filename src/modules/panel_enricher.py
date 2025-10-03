"""Async panel enrichment system with priority queue."""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)


class Priority(IntEnum):
    """Enrichment priority levels."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


@dataclass(order=True)
class EnrichmentTask:
    """Task for async enrichment queue."""
    priority: int
    panel_id: str = field(compare=False)
    context: Dict[str, Any] = field(default_factory=dict, compare=False)
    timestamp: datetime = field(default_factory=datetime.now, compare=False)
    callback: Optional[Callable] = field(default=None, compare=False)


class ModulePanelEnricher:
    """Async module for panel enrichment with priority queue."""

    def __init__(self, max_workers: int = 4):
        """Initialize panel enricher.

        Args:
            max_workers: Maximum concurrent enrichment tasks
        """
        self.max_workers = max_workers
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.enrichment_cache: Dict[str, Dict[str, Any]] = {}
        self.context_providers: Dict[str, Callable] = {}
        self._stats = {
            'total_enriched': 0,
            'cache_hits': 0,
            'errors': 0
        }

    def register_context_provider(self, name: str, provider: Callable) -> None:
        """Register a context gathering provider.

        Args:
            name: Provider name
            provider: Async function that gathers context
        """
        self.context_providers[name] = provider
        logger.info(f"Registered context provider: {name}")

    async def enqueue_enrichment(
        self,
        panel_id: str,
        priority: Priority = Priority.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable] = None
    ) -> None:
        """Enqueue a panel for enrichment.

        Args:
            panel_id: Panel identifier
            priority: Enrichment priority
            context: Additional context data
            callback: Optional callback when enrichment completes
        """
        task = EnrichmentTask(
            priority=-priority,  # Negative for correct priority ordering
            panel_id=panel_id,
            context=context or {},
            callback=callback
        )
        await self.queue.put(task)
        logger.debug(f"Enqueued panel {panel_id} with priority {priority.name}")

    async def _enrichment_worker(self, worker_id: int) -> None:
        """Worker coroutine for processing enrichment tasks.

        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get task with timeout to check running flag
                task = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=0.5
                )

                logger.debug(f"Worker {worker_id} processing panel {task.panel_id}")

                # Check cache first
                if task.panel_id in self.enrichment_cache:
                    self._stats['cache_hits'] += 1
                    result = self.enrichment_cache[task.panel_id]
                    logger.debug(f"Cache hit for panel {task.panel_id}")
                else:
                    # Perform enrichment
                    result = await self._enrich_panel(task.panel_id, task.context)
                    self.enrichment_cache[task.panel_id] = result
                    self._stats['total_enriched'] += 1

                # Call callback if provided
                if task.callback:
                    await self._safe_callback(task.callback, task.panel_id, result)

                self.queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self._stats['errors'] += 1
                logger.error(f"Worker {worker_id} error: {e}")

        logger.info(f"Worker {worker_id} stopped")

    async def _enrich_panel(
        self,
        panel_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich a panel with context data.

        Args:
            panel_id: Panel identifier
            context: Base context data

        Returns:
            Enriched panel data
        """
        enriched = {
            'panel_id': panel_id,
            'timestamp': datetime.now().isoformat(),
            'context': context.copy()
        }

        # Gather context from all providers
        for name, provider in self.context_providers.items():
            try:
                provider_context = await provider(panel_id, context)
                enriched['context'][name] = provider_context
                logger.debug(f"Gathered context from {name} for panel {panel_id}")
            except Exception as e:
                logger.error(f"Error gathering context from {name}: {e}")
                enriched['context'][name] = {'error': str(e)}

        return enriched

    async def _safe_callback(
        self,
        callback: Callable,
        panel_id: str,
        result: Dict[str, Any]
    ) -> None:
        """Safely execute callback with error handling.

        Args:
            callback: Callback function
            panel_id: Panel identifier
            result: Enrichment result
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(panel_id, result)
            else:
                callback(panel_id, result)
        except Exception as e:
            logger.error(f"Callback error for panel {panel_id}: {e}")

    async def start(self) -> None:
        """Start enrichment workers."""
        if self.running:
            logger.warning("Enricher already running")
            return

        self.running = True
        self.workers = [
            asyncio.create_task(self._enrichment_worker(i))
            for i in range(self.max_workers)
        ]
        logger.info(f"Started {self.max_workers} enrichment workers")

    async def stop(self) -> None:
        """Stop enrichment workers gracefully."""
        if not self.running:
            return

        self.running = False

        # Wait for queue to empty
        await self.queue.join()

        # Cancel and wait for workers
        for worker in self.workers:
            worker.cancel()

        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

        logger.info("Stopped enrichment workers")

    async def get_enriched(self, panel_id: str) -> Optional[Dict[str, Any]]:
        """Get enriched data for a panel.

        Args:
            panel_id: Panel identifier

        Returns:
            Enriched data or None if not available
        """
        return self.enrichment_cache.get(panel_id)

    def clear_cache(self, panel_id: Optional[str] = None) -> None:
        """Clear enrichment cache.

        Args:
            panel_id: Specific panel to clear, or None for all
        """
        if panel_id:
            self.enrichment_cache.pop(panel_id, None)
            logger.debug(f"Cleared cache for panel {panel_id}")
        else:
            self.enrichment_cache.clear()
            logger.debug("Cleared all enrichment cache")

    def get_stats(self) -> Dict[str, int]:
        """Get enrichment statistics.

        Returns:
            Statistics dictionary
        """
        return {
            **self._stats,
            'cache_size': len(self.enrichment_cache),
            'queue_size': self.queue.qsize(),
            'workers': len(self.workers)
        }
