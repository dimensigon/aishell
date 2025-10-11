"""
Redis MCP Client Implementation

Implements Redis connectivity using redis[asyncio] for async operations.
"""

import asyncio
import json
from typing import Any, Dict, Optional, List, Union
from datetime import timedelta
import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
from .base import BaseMCPClient, ConnectionConfig, MCPClientError


class RedisClient(BaseMCPClient):
    """
    Redis database client using redis[asyncio]

    Provides async interface to Redis operations including caching,
    pub/sub, and session management.
    """

    def __init__(self) -> None:
        super().__init__()
        self._client: Optional[Redis] = None
        self._pubsub = None
        self._subscribers: Dict[str, callable] = {}

    async def _connect_impl(self, config: ConnectionConfig) -> Any:
        """
        Connect to Redis

        Args:
            config: Connection configuration

        Returns:
            Redis client instance
        """
        # Build connection parameters
        conn_params = {
            'host': config.host,
            'port': config.port,
            'db': int(config.database) if config.database.isdigit() else 0,
            'decode_responses': True,
            'socket_connect_timeout': 5,
        }

        # Add password if provided
        if config.password:
            conn_params['password'] = config.password

        # Add extra parameters
        if config.extra_params:
            conn_params.update(config.extra_params)

        # Create Redis client
        self._client = aioredis.Redis(**conn_params)

        # Verify connection
        try:
            await self._client.ping()
        except RedisConnectionError as e:
            raise MCPClientError(f"Failed to connect to Redis: {str(e)}", "CONNECTION_FAILED")

        return self._client

    async def _disconnect_impl(self) -> None:
        """Disconnect from Redis"""
        if self._pubsub:
            await self._pubsub.close()
            self._pubsub = None

        if self._client:
            await self._client.close()
            self._client = None

    async def _execute_query_impl(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Redis command (JSON format)

        Args:
            query: Redis command as JSON string (e.g., '{"command": "get", "key": "user:1"}')
            params: Additional parameters

        Returns:
            Dictionary with results
        """
        if self._client is None:
            raise MCPClientError("No active Redis connection", "NOT_CONNECTED")

        try:
            # Parse command
            query_dict = json.loads(query) if isinstance(query, str) else query
            command = query_dict.get('command', '').lower()

            # Execute command
            if command == 'get':
                result = await self._execute_get(query_dict)
            elif command == 'set':
                result = await self._execute_set(query_dict)
            elif command == 'delete' or command == 'del':
                result = await self._execute_delete(query_dict)
            elif command == 'exists':
                result = await self._execute_exists(query_dict)
            elif command == 'expire':
                result = await self._execute_expire(query_dict)
            elif command == 'ttl':
                result = await self._execute_ttl(query_dict)
            elif command == 'keys':
                result = await self._execute_keys(query_dict)
            elif command == 'hget':
                result = await self._execute_hget(query_dict)
            elif command == 'hset':
                result = await self._execute_hset(query_dict)
            elif command == 'hgetall':
                result = await self._execute_hgetall(query_dict)
            elif command == 'lpush':
                result = await self._execute_lpush(query_dict)
            elif command == 'rpush':
                result = await self._execute_rpush(query_dict)
            elif command == 'lpop':
                result = await self._execute_lpop(query_dict)
            elif command == 'rpop':
                result = await self._execute_rpop(query_dict)
            elif command == 'lrange':
                result = await self._execute_lrange(query_dict)
            elif command == 'sadd':
                result = await self._execute_sadd(query_dict)
            elif command == 'smembers':
                result = await self._execute_smembers(query_dict)
            elif command == 'zadd':
                result = await self._execute_zadd(query_dict)
            elif command == 'zrange':
                result = await self._execute_zrange(query_dict)
            elif command == 'incr':
                result = await self._execute_incr(query_dict)
            elif command == 'decr':
                result = await self._execute_decr(query_dict)
            else:
                raise MCPClientError(f"Unsupported command: {command}", "INVALID_COMMAND")

            return {
                'columns': result.get('columns', ['result']),
                'rows': result.get('rows', []),
                'rowcount': result.get('rowcount', 0),
                'metadata': {
                    'database': self._config.database if self._config else '0',
                    'command': command
                }
            }

        except json.JSONDecodeError as e:
            raise MCPClientError(f"Invalid JSON command: {str(e)}", "INVALID_COMMAND")
        except RedisError as e:
            raise MCPClientError(f"Redis error: {str(e)}", "COMMAND_FAILED")

    async def _execute_get(self, query: Dict) -> Dict:
        """Execute GET command"""
        key = query.get('key')
        value = await self._client.get(key)

        return {
            'columns': ['key', 'value'],
            'rows': [(key, value)],
            'rowcount': 1 if value is not None else 0
        }

    async def _execute_set(self, query: Dict) -> Dict:
        """Execute SET command"""
        key = query.get('key')
        value = query.get('value')
        ex = query.get('ex')  # Expiration in seconds
        px = query.get('px')  # Expiration in milliseconds
        nx = query.get('nx', False)  # Only set if not exists
        xx = query.get('xx', False)  # Only set if exists

        result = await self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)

        return {
            'columns': ['success'],
            'rows': [(bool(result),)],
            'rowcount': 1 if result else 0
        }

    async def _execute_delete(self, query: Dict) -> Dict:
        """Execute DEL command"""
        keys = query.get('keys', [])
        if isinstance(keys, str):
            keys = [keys]

        count = await self._client.delete(*keys)

        return {
            'columns': ['deleted_count'],
            'rows': [(count,)],
            'rowcount': count
        }

    async def _execute_exists(self, query: Dict) -> Dict:
        """Execute EXISTS command"""
        keys = query.get('keys', [])
        if isinstance(keys, str):
            keys = [keys]

        count = await self._client.exists(*keys)

        return {
            'columns': ['exists_count'],
            'rows': [(count,)],
            'rowcount': count
        }

    async def _execute_expire(self, query: Dict) -> Dict:
        """Execute EXPIRE command"""
        key = query.get('key')
        seconds = query.get('seconds')

        result = await self._client.expire(key, seconds)

        return {
            'columns': ['success'],
            'rows': [(bool(result),)],
            'rowcount': 1 if result else 0
        }

    async def _execute_ttl(self, query: Dict) -> Dict:
        """Execute TTL command"""
        key = query.get('key')
        ttl = await self._client.ttl(key)

        return {
            'columns': ['key', 'ttl'],
            'rows': [(key, ttl)],
            'rowcount': 1
        }

    async def _execute_keys(self, query: Dict) -> Dict:
        """Execute KEYS command"""
        pattern = query.get('pattern', '*')
        keys = await self._client.keys(pattern)

        rows = [(key,) for key in keys]

        return {
            'columns': ['key'],
            'rows': rows,
            'rowcount': len(keys)
        }

    async def _execute_hget(self, query: Dict) -> Dict:
        """Execute HGET command"""
        key = query.get('key')
        field = query.get('field')

        value = await self._client.hget(key, field)

        return {
            'columns': ['field', 'value'],
            'rows': [(field, value)],
            'rowcount': 1 if value is not None else 0
        }

    async def _execute_hset(self, query: Dict) -> Dict:
        """Execute HSET command"""
        key = query.get('key')
        field = query.get('field')
        value = query.get('value')

        result = await self._client.hset(key, field, value)

        return {
            'columns': ['created'],
            'rows': [(result,)],
            'rowcount': result
        }

    async def _execute_hgetall(self, query: Dict) -> Dict:
        """Execute HGETALL command"""
        key = query.get('key')
        data = await self._client.hgetall(key)

        rows = [(k, v) for k, v in data.items()]

        return {
            'columns': ['field', 'value'],
            'rows': rows,
            'rowcount': len(rows)
        }

    async def _execute_lpush(self, query: Dict) -> Dict:
        """Execute LPUSH command"""
        key = query.get('key')
        values = query.get('values', [])

        result = await self._client.lpush(key, *values)

        return {
            'columns': ['length'],
            'rows': [(result,)],
            'rowcount': 1
        }

    async def _execute_rpush(self, query: Dict) -> Dict:
        """Execute RPUSH command"""
        key = query.get('key')
        values = query.get('values', [])

        result = await self._client.rpush(key, *values)

        return {
            'columns': ['length'],
            'rows': [(result,)],
            'rowcount': 1
        }

    async def _execute_lpop(self, query: Dict) -> Dict:
        """Execute LPOP command"""
        key = query.get('key')
        value = await self._client.lpop(key)

        return {
            'columns': ['value'],
            'rows': [(value,)],
            'rowcount': 1 if value is not None else 0
        }

    async def _execute_rpop(self, query: Dict) -> Dict:
        """Execute RPOP command"""
        key = query.get('key')
        value = await self._client.rpop(key)

        return {
            'columns': ['value'],
            'rows': [(value,)],
            'rowcount': 1 if value is not None else 0
        }

    async def _execute_lrange(self, query: Dict) -> Dict:
        """Execute LRANGE command"""
        key = query.get('key')
        start = query.get('start', 0)
        stop = query.get('stop', -1)

        values = await self._client.lrange(key, start, stop)
        rows = [(v,) for v in values]

        return {
            'columns': ['value'],
            'rows': rows,
            'rowcount': len(values)
        }

    async def _execute_sadd(self, query: Dict) -> Dict:
        """Execute SADD command"""
        key = query.get('key')
        members = query.get('members', [])

        result = await self._client.sadd(key, *members)

        return {
            'columns': ['added_count'],
            'rows': [(result,)],
            'rowcount': result
        }

    async def _execute_smembers(self, query: Dict) -> Dict:
        """Execute SMEMBERS command"""
        key = query.get('key')
        members = await self._client.smembers(key)
        rows = [(m,) for m in members]

        return {
            'columns': ['member'],
            'rows': rows,
            'rowcount': len(members)
        }

    async def _execute_zadd(self, query: Dict) -> Dict:
        """Execute ZADD command"""
        key = query.get('key')
        mapping = query.get('mapping', {})  # {member: score}

        result = await self._client.zadd(key, mapping)

        return {
            'columns': ['added_count'],
            'rows': [(result,)],
            'rowcount': result
        }

    async def _execute_zrange(self, query: Dict) -> Dict:
        """Execute ZRANGE command"""
        key = query.get('key')
        start = query.get('start', 0)
        stop = query.get('stop', -1)
        withscores = query.get('withscores', False)

        values = await self._client.zrange(key, start, stop, withscores=withscores)

        if withscores:
            rows = [(v, s) for v, s in zip(values[::2], values[1::2])]
            columns = ['member', 'score']
        else:
            rows = [(v,) for v in values]
            columns = ['member']

        return {
            'columns': columns,
            'rows': rows,
            'rowcount': len(rows)
        }

    async def _execute_incr(self, query: Dict) -> Dict:
        """Execute INCR command"""
        key = query.get('key')
        result = await self._client.incr(key)

        return {
            'columns': ['value'],
            'rows': [(result,)],
            'rowcount': 1
        }

    async def _execute_decr(self, query: Dict) -> Dict:
        """Execute DECR command"""
        key = query.get('key')
        result = await self._client.decr(key)

        return {
            'columns': ['value'],
            'rows': [(result,)],
            'rowcount': 1
        }

    async def _execute_ddl_impl(self, ddl: str) -> None:
        """
        Execute DDL-like operation (database management commands)

        Args:
            ddl: JSON string with DDL operation
        """
        if self._client is None:
            raise MCPClientError("No active Redis connection", "NOT_CONNECTED")

        try:
            ddl_dict = json.loads(ddl) if isinstance(ddl, str) else ddl
            operation = ddl_dict.get('operation')

            if operation == 'flushdb':
                await self._client.flushdb()
            elif operation == 'flushall':
                await self._client.flushall()
            elif operation == 'select':
                db = ddl_dict.get('db', 0)
                await self._client.select(db)
            else:
                raise MCPClientError(f"Unsupported DDL operation: {operation}", "INVALID_DDL")

        except json.JSONDecodeError as e:
            raise MCPClientError(f"Invalid JSON DDL: {str(e)}", "INVALID_DDL")
        except RedisError as e:
            raise MCPClientError(f"Redis DDL error: {str(e)}", "DDL_FAILED")

    def _get_ping_query(self) -> str:
        """Get Redis-specific ping query"""
        return '{"command": "ping"}'

    # High-level caching methods

    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a cache value

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        if self._client is None:
            raise MCPClientError("No active Redis connection", "NOT_CONNECTED")

        # Serialize value
        serialized = json.dumps(value) if not isinstance(value, str) else value

        result = await self._client.set(key, serialized, ex=ttl)
        return bool(result)

    async def cache_get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Get a cache value

        Args:
            key: Cache key
            deserialize: Whether to JSON deserialize the value

        Returns:
            Cached value or None
        """
        if self._client is None:
            raise MCPClientError("No active Redis connection", "NOT_CONNECTED")

        value = await self._client.get(key)

        if value is None:
            return None

        if deserialize:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        return value

    async def cache_delete(self, *keys: str) -> int:
        """
        Delete cache keys

        Args:
            keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        if self._client is None:
            raise MCPClientError("No active Redis connection", "NOT_CONNECTED")

        return await self._client.delete(*keys)

    async def cache_exists(self, *keys: str) -> int:
        """
        Check if cache keys exist

        Args:
            keys: Keys to check

        Returns:
            Number of keys that exist
        """
        if self._client is None:
            raise MCPClientError("No active Redis connection", "NOT_CONNECTED")

        return await self._client.exists(*keys)

    # Pub/Sub support

    async def publish(self, channel: str, message: str) -> int:
        """
        Publish a message to a channel

        Args:
            channel: Channel name
            message: Message to publish

        Returns:
            Number of subscribers that received the message
        """
        if self._client is None:
            raise MCPClientError("No active Redis connection", "NOT_CONNECTED")

        return await self._client.publish(channel, message)

    async def subscribe(self, channel: str, callback: callable) -> None:
        """
        Subscribe to a channel

        Args:
            channel: Channel name
            callback: Callback function to handle messages
        """
        if self._client is None:
            raise MCPClientError("No active Redis connection", "NOT_CONNECTED")

        if self._pubsub is None:
            self._pubsub = self._client.pubsub()

        await self._pubsub.subscribe(channel)
        self._subscribers[channel] = callback

        # Start listening in background
        asyncio.create_task(self._listen_pubsub())

    async def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribe from a channel

        Args:
            channel: Channel name
        """
        if self._pubsub:
            await self._pubsub.unsubscribe(channel)
            if channel in self._subscribers:
                del self._subscribers[channel]

    async def _listen_pubsub(self) -> None:
        """Listen for pub/sub messages"""
        if self._pubsub is None:
            return

        async for message in self._pubsub.listen():
            if message['type'] == 'message':
                channel = message['channel']
                data = message['data']

                if channel in self._subscribers:
                    callback = self._subscribers[channel]
                    await callback(channel, data)

    # Session management

    async def session_create(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """
        Create a session

        Args:
            session_id: Session identifier
            data: Session data
            ttl: Time to live in seconds (default: 1 hour)

        Returns:
            True if successful
        """
        key = f"session:{session_id}"
        return await self.cache_set(key, data, ttl=ttl)

    async def session_get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data

        Args:
            session_id: Session identifier

        Returns:
            Session data or None
        """
        key = f"session:{session_id}"
        return await self.cache_get(key)

    async def session_update(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Update session data

        Args:
            session_id: Session identifier
            data: New session data
            ttl: Optional new TTL

        Returns:
            True if successful
        """
        key = f"session:{session_id}"
        return await self.cache_set(key, data, ttl=ttl)

    async def session_delete(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: Session identifier

        Returns:
            True if deleted
        """
        key = f"session:{session_id}"
        count = await self.cache_delete(key)
        return count > 0

    async def session_extend(self, session_id: str, ttl: int = 3600) -> bool:
        """
        Extend session TTL

        Args:
            session_id: Session identifier
            ttl: New time to live in seconds

        Returns:
            True if successful
        """
        if self._client is None:
            raise MCPClientError("No active Redis connection", "NOT_CONNECTED")

        key = f"session:{session_id}"
        result = await self._client.expire(key, ttl)
        return bool(result)
