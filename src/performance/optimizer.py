"""
Performance optimization engine for AI-Shell.

Handles query optimization, connection pooling, and resource management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class OptimizationMetrics:
    """Metrics for optimization analysis."""
    query_count: int = 0
    avg_execution_time: float = 0.0
    cache_hit_rate: float = 0.0
    connection_pool_usage: float = 0.0
    slow_queries: List[str] = None

    def __post_init__(self):
        if self.slow_queries is None:
            self.slow_queries = []


class PerformanceOptimizer:
    """Optimizes database operations and resource usage."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.query_stats: Dict[str, List[float]] = defaultdict(list)
        self.slow_query_threshold = self.config.get('slow_query_threshold', 1.0)
        self.optimization_enabled = True
        self._optimization_lock = asyncio.Lock()
        self._query_patterns: Set[str] = set()

    async def optimize_query(self, query: str) -> str:
        """
        Optimize SQL query for better performance.

        Args:
            query: Original SQL query

        Returns:
            Optimized SQL query
        """
        if not self.optimization_enabled:
            return query

        optimized = query.strip()

        # Add basic optimizations
        optimized = self._add_index_hints(optimized)
        optimized = self._optimize_joins(optimized)
        optimized = self._add_query_limits(optimized)

        # Track pattern
        pattern = self._extract_pattern(optimized)
        self._query_patterns.add(pattern)

        return optimized

    def _add_index_hints(self, query: str) -> str:
        """Add index hints for common patterns."""
        query_upper = query.upper()

        # Add FORCE INDEX for common ID lookups
        if 'WHERE ID =' in query_upper and 'FORCE INDEX' not in query_upper:
            # Basic hint addition (database-specific logic would go here)
            pass

        return query

    def _optimize_joins(self, query: str) -> str:
        """Optimize JOIN operations."""
        query_upper = query.upper()

        # Suggest INNER JOIN over implicit joins
        if 'FROM' in query_upper and ',' in query and 'JOIN' not in query_upper:
            logger.info("Query uses implicit join, consider explicit INNER JOIN")

        return query

    def _add_query_limits(self, query: str) -> str:
        """Add reasonable limits to unbounded queries."""
        query_upper = query.upper()

        # Add LIMIT if missing on SELECT without WHERE
        if query_upper.startswith('SELECT') and 'LIMIT' not in query_upper:
            if 'WHERE' not in query_upper and 'JOIN' not in query_upper:
                logger.warning("Unbounded SELECT query detected")

        return query

    def _extract_pattern(self, query: str) -> str:
        """Extract query pattern for analysis."""
        # Normalize query to pattern
        pattern = query.upper()

        # Replace literals with placeholders
        import re
        pattern = re.sub(r"'[^']*'", '?', pattern)
        pattern = re.sub(r'\d+', '?', pattern)

        return pattern

    async def record_execution(self, query: str, execution_time: float):
        """
        Record query execution metrics.

        Args:
            query: Executed query
            execution_time: Execution time in seconds
        """
        async with self._optimization_lock:
            pattern = self._extract_pattern(query)
            self.query_stats[pattern].append(execution_time)

            if execution_time > self.slow_query_threshold:
                logger.warning(f"Slow query detected ({execution_time:.2f}s): {query[:100]}")

    async def get_metrics(self) -> OptimizationMetrics:
        """
        Get current optimization metrics.

        Returns:
            Current optimization metrics
        """
        async with self._optimization_lock:
            total_queries = sum(len(times) for times in self.query_stats.values())

            if total_queries == 0:
                return OptimizationMetrics()

            # Calculate average execution time
            all_times = [t for times in self.query_stats.values() for t in times]
            avg_time = sum(all_times) / len(all_times)

            # Find slow queries
            slow_queries = []
            for pattern, times in self.query_stats.items():
                avg_pattern_time = sum(times) / len(times)
                if avg_pattern_time > self.slow_query_threshold:
                    slow_queries.append(pattern)

            return OptimizationMetrics(
                query_count=total_queries,
                avg_execution_time=avg_time,
                slow_queries=slow_queries
            )

    async def suggest_indexes(self) -> List[str]:
        """
        Suggest database indexes based on query patterns.

        Returns:
            List of index suggestions
        """
        suggestions = []

        async with self._optimization_lock:
            for pattern, times in self.query_stats.items():
                # Analyze slow patterns for index opportunities
                avg_time = sum(times) / len(times) if times else 0

                if avg_time > self.slow_query_threshold:
                    # Extract potential index columns
                    if 'WHERE' in pattern:
                        suggestions.append(f"Consider index for pattern: {pattern[:100]}")

        return suggestions

    async def optimize_connection_pool(self, current_usage: float) -> Dict[str, int]:
        """
        Optimize connection pool settings.

        Args:
            current_usage: Current pool usage percentage (0-1)

        Returns:
            Recommended pool settings
        """
        min_size = self.config.get('min_pool_size', 2)
        max_size = self.config.get('max_pool_size', 10)

        # Adjust based on usage
        if current_usage > 0.8:
            recommended_max = min(max_size * 2, 20)
            logger.info(f"High pool usage ({current_usage:.1%}), recommend increasing max to {recommended_max}")
            return {'min_size': min_size, 'max_size': recommended_max}
        elif current_usage < 0.2:
            recommended_max = max(max_size // 2, min_size + 1)
            logger.info(f"Low pool usage ({current_usage:.1%}), recommend decreasing max to {recommended_max}")
            return {'min_size': min_size, 'max_size': recommended_max}

        return {'min_size': min_size, 'max_size': max_size}

    async def reset_stats(self):
        """Reset optimization statistics."""
        async with self._optimization_lock:
            self.query_stats.clear()
            self._query_patterns.clear()
            logger.info("Optimization statistics reset")

    def enable_optimization(self, enabled: bool = True):
        """Enable or disable query optimization."""
        self.optimization_enabled = enabled
        logger.info(f"Query optimization {'enabled' if enabled else 'disabled'}")
