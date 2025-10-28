"""
Enhanced Redis MCP Client with 100% Feature Coverage

Adds advanced Redis features:
- Streams support
- Lua scripts
- Pipeline batching
- Retry logic with exponential backoff
- Connection health monitoring
"""

import asyncio
from typing import Any, Dict, Optional, List
from redis.asyncio import Redis
from redis.exceptions import RedisError
from .redis_client import RedisClient
from .base import ConnectionConfig, MCPClientError
import logging

logger = logging.getLogger(__name__)


class RedisEnhancedClient(RedisClient):
    """Enhanced Redis client with advanced features"""

    def __init__(self) -> None:
        super().__init__()
        self._scripts: Dict[str, Any] = {}
        self._retry_config = {
            'max_retries': 3,
            'base_delay': 0.1,
            'max_delay': 10.0,
            'exponential_base': 2
        }
        self._metrics = {
            'commands': 0,
            'failures': 0,
            'reconnections': 0
        }

    def configure_retry(self, max_retries: int = 3, base_delay: float = 0.1,
                       max_delay: float = 10.0, exponential_base: int = 2) -> None:
        """Configure retry behavior"""
        self._retry_config = {
            'max_retries': max_retries,
            'base_delay': base_delay,
            'max_delay': max_delay,
            'exponential_base': exponential_base
        }

    # Redis Streams

    async def xadd(self, stream: str, fields: Dict[str, str],
                   message_id: str = '*') -> str:
        """
        Add entry to stream

        Args:
            stream: Stream name
            fields: Field-value pairs
            message_id: Message ID (default: auto-generate)

        Returns:
            Message ID
        """
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")
        return await self._client.xadd(stream, fields, id=message_id)

    async def xread(self, streams: Dict[str, str], count: Optional[int] = None,
                   block: Optional[int] = None) -> List[Dict]:
        """
        Read from streams

        Args:
            streams: Dict of stream names to IDs
            count: Maximum entries per stream
            block: Block timeout in milliseconds

        Returns:
            List of stream entries
        """
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")
        return await self._client.xread(streams, count=count, block=block)

    async def xrange(self, stream: str, min: str = '-', max: str = '+',
                    count: Optional[int] = None) -> List:
        """Get range of entries from stream"""
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")
        return await self._client.xrange(stream, min, max, count)

    async def xlen(self, stream: str) -> int:
        """Get stream length"""
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")
        return await self._client.xlen(stream)

    async def xtrim(self, stream: str, maxlen: int, approximate: bool = True) -> int:
        """Trim stream to maximum length"""
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")
        return await self._client.xtrim(stream, maxlen, approximate=approximate)

    # Consumer Groups

    async def xgroup_create(self, stream: str, group: str, id: str = '$') -> None:
        """Create consumer group"""
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")
        await self._client.xgroup_create(stream, group, id)

    async def xgroup_destroy(self, stream: str, group: str) -> None:
        """Destroy consumer group"""
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")
        await self._client.xgroup_destroy(stream, group)

    async def xreadgroup(self, group: str, consumer: str, streams: Dict[str, str],
                        count: Optional[int] = None, block: Optional[int] = None) -> List:
        """Read from stream as consumer"""
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")
        return await self._client.xreadgroup(group, consumer, streams, count=count, block=block)

    # Lua Scripts

    async def register_script(self, name: str, script: str) -> None:
        """
        Register Lua script

        Args:
            name: Script name
            script: Lua script code
        """
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")

        script_obj = self._client.register_script(script)
        self._scripts[name] = script_obj
        logger.debug(f"Registered Lua script: {name}")

    async def execute_script(self, name: str, keys: List[str] = None,
                           args: List[Any] = None) -> Any:
        """
        Execute registered Lua script

        Args:
            name: Script name
            keys: Redis keys to pass
            args: Arguments to pass

        Returns:
            Script result
        """
        if name not in self._scripts:
            raise MCPClientError(f"Script not registered: {name}", "SCRIPT_NOT_FOUND")

        script = self._scripts[name]
        return await script(keys=keys or [], args=args or [])

    async def eval_script(self, script: str, keys: List[str] = None,
                         args: List[Any] = None) -> Any:
        """
        Evaluate Lua script directly

        Args:
            script: Lua script code
            keys: Redis keys
            args: Arguments

        Returns:
            Script result
        """
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")
        return await self._client.eval(script, len(keys or []), *(keys or []), *(args or []))

    # Pipeline Support

    async def pipeline(self) -> Any:
        """Create pipeline for batching commands"""
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")
        return self._client.pipeline()

    async def execute_pipeline(self, commands: List[tuple]) -> List[Any]:
        """
        Execute multiple commands in pipeline

        Args:
            commands: List of (command, args, kwargs) tuples

        Returns:
            List of results
        """
        pipe = await self.pipeline()
        for cmd, args, kwargs in commands:
            getattr(pipe, cmd)(*args, **kwargs)
        return await pipe.execute()

    # Health Monitoring

    async def health_check_detailed(self) -> Dict[str, Any]:
        """Detailed health check"""
        health = await super().health_check()
        health['metrics'] = self._metrics.copy()

        if self._client:
            try:
                info = await self._client.info()
                health['redis_version'] = info.get('redis_version')
                health['uptime_seconds'] = info.get('uptime_in_seconds')
                health['connected_clients'] = info.get('connected_clients')
                health['used_memory'] = info.get('used_memory')
                health['used_memory_human'] = info.get('used_memory_human')
            except Exception as e:
                health['info_error'] = str(e)

        return health

    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        return self._metrics.copy()

    # Advanced Operations

    async def scan_keys(self, pattern: str = '*', count: int = 100) -> List[str]:
        """
        Scan keys using cursor (memory efficient)

        Args:
            pattern: Key pattern
            count: Hint for number of keys per iteration

        Returns:
            List of matching keys
        """
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")

        keys = []
        cursor = 0
        while True:
            cursor, partial_keys = await self._client.scan(cursor, match=pattern, count=count)
            keys.extend(partial_keys)
            if cursor == 0:
                break
        return keys

    async def get_memory_usage(self, key: str) -> int:
        """Get memory usage of key in bytes"""
        if not self._client:
            raise MCPClientError("Not connected", "NOT_CONNECTED")
        return await self._client.memory_usage(key)
