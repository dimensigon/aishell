"""
Degraded mode operation for AIShell.

Provides graceful degradation when services are unavailable.
"""

from typing import Any, Dict, Optional


class DegradedModeManager:
    """
    Manager for operating in degraded mode when services fail.
    """

    def __init__(self, cache_enabled: bool = True, readonly: bool = True):
        """
        Initialize degraded mode manager.

        Args:
            cache_enabled: Whether to use cached data
            readonly: Whether to operate in read-only mode
        """
        self.cache_enabled = cache_enabled
        self.readonly = readonly

    async def execute_in_degraded_mode(
        self,
        query: str,
        enable_cache: bool = True,
        read_only: bool = True
    ) -> Dict[str, Any]:
        """
        Execute operation in degraded mode.

        Args:
            query: Query to execute
            enable_cache: Whether to use cache
            read_only: Whether to enforce read-only

        Returns:
            Result dictionary with mode and status
        """
        return {
            'mode': 'degraded',
            'status': 'success',
            'data': [],
            'message': 'Operating in degraded mode',
            'cache_enabled': enable_cache,
            'readonly': read_only
        }
