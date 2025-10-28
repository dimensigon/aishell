"""
Enhanced MCP Connection Manager with Multi-Protocol Support

Extends the basic connection manager to support various protocols including:
- Database connections (PostgreSQL, MySQL, Oracle, SQLite)
- API connections (REST, GraphQL, WebSocket)
- File storage (S3, GCS, Azure Blob)
- Message queues (RabbitMQ, Kafka, Redis)
- External services (Elasticsearch, MongoDB, etc.)
"""

import asyncio
import json
from typing import Dict, Optional, List, Type, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

from .base import BaseMCPClient, ConnectionConfig, MCPClientError, ConnectionState, QueryResult
from .manager import ConnectionManager, ConnectionInfo

logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    """Supported MCP protocol types"""
    DATABASE = "database"
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    FILE_STORAGE = "file_storage"
    MESSAGE_QUEUE = "message_queue"
    SEARCH_ENGINE = "search_engine"
    NOSQL = "nosql"
    CACHE = "cache"


@dataclass
class MCPResource:
    """Represents an MCP-accessible resource"""
    uri: str
    name: str
    protocol: ProtocolType
    description: str
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPTool:
    """Represents an MCP tool/function"""
    name: str
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    protocol: ProtocolType
    handler: Optional[callable] = None


class APIClient(BaseMCPClient):
    """MCP client for REST/GraphQL APIs"""

    def __init__(self):
        super().__init__()
        self.base_url = None
        self.headers = {}
        self.session = None

    async def connect(self, config: ConnectionConfig) -> bool:
        """Connect to API endpoint"""
        try:
            self._state = ConnectionState.CONNECTING
            self.base_url = f"https://{config.host}:{config.port}"

            # Set up authentication headers
            if config.password:
                self.headers['Authorization'] = f"Bearer {config.password}"

            # Additional headers from config
            if config.extra_params and 'headers' in config.extra_params:
                self.headers.update(config.extra_params['headers'])

            self._state = ConnectionState.CONNECTED
            self._connection_time = datetime.utcnow()
            logger.info(f"Connected to API: {self.base_url}")
            return True

        except Exception as e:
            self._state = ConnectionState.ERROR
            self._last_error = str(e)
            raise MCPClientError(f"API connection failed: {e}")

    async def execute_query(self, endpoint: str, method: str = "GET",
                           params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute API request"""
        if self._state != ConnectionState.CONNECTED:
            raise MCPClientError("Not connected to API")

        # Simulate API call (would use aiohttp in real implementation)
        start_time = datetime.utcnow()

        # Mock response
        response_data = {
            "status": "success",
            "data": params or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        return QueryResult(
            columns=["response"],
            rows=[(json.dumps(response_data),)],
            rowcount=1,
            execution_time=execution_time,
            metadata={"method": method, "endpoint": endpoint}
        )

    async def disconnect(self) -> bool:
        """Disconnect from API"""
        self._state = ConnectionState.DISCONNECTED
        if self.session:
            # Would close aiohttp session here
            self.session = None
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        return {
            "healthy": self._state == ConnectionState.CONNECTED,
            "base_url": self.base_url,
            "connected_at": self._connection_time.isoformat() if self._connection_time else None
        }

    async def execute_ddl(self, ddl: str) -> bool:
        """Not applicable for API clients"""
        raise MCPClientError("DDL operations not supported for API clients")


class FileStorageClient(BaseMCPClient):
    """MCP client for file storage systems"""

    def __init__(self):
        super().__init__()
        self.storage_type = None
        self.bucket = None

    async def connect(self, config: ConnectionConfig) -> bool:
        """Connect to file storage"""
        try:
            self._state = ConnectionState.CONNECTING

            # Determine storage type from config
            self.storage_type = config.extra_params.get('storage_type', 's3')
            self.bucket = config.database  # Use database field for bucket name

            # Would initialize actual storage client here (boto3, gcs, etc.)

            self._state = ConnectionState.CONNECTED
            self._connection_time = datetime.utcnow()
            logger.info(f"Connected to {self.storage_type} storage: {self.bucket}")
            return True

        except Exception as e:
            self._state = ConnectionState.ERROR
            self._last_error = str(e)
            raise MCPClientError(f"Storage connection failed: {e}")

    async def list_files(self, prefix: str = "") -> List[str]:
        """List files in storage"""
        if self._state != ConnectionState.CONNECTED:
            raise MCPClientError("Not connected to storage")

        # Mock file listing
        return [f"{prefix}file1.txt", f"{prefix}file2.json", f"{prefix}dir/file3.csv"]

    async def read_file(self, key: str) -> bytes:
        """Read file from storage"""
        if self._state != ConnectionState.CONNECTED:
            raise MCPClientError("Not connected to storage")

        # Mock file content
        return f"Content of {key}".encode()

    async def write_file(self, key: str, content: bytes) -> bool:
        """Write file to storage"""
        if self._state != ConnectionState.CONNECTED:
            raise MCPClientError("Not connected to storage")

        # Mock file write
        logger.info(f"Wrote {len(content)} bytes to {key}")
        return True

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute storage operation as query"""
        operation = params.get('operation', 'list') if params else 'list'

        if operation == 'list':
            files = await self.list_files(params.get('prefix', ''))
            return QueryResult(
                columns=["file"],
                rows=[(f,) for f in files],
                rowcount=len(files),
                execution_time=0.1,
                metadata={"operation": "list"}
            )
        else:
            raise MCPClientError(f"Unsupported operation: {operation}")

    async def disconnect(self) -> bool:
        """Disconnect from storage"""
        self._state = ConnectionState.DISCONNECTED
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Check storage health"""
        return {
            "healthy": self._state == ConnectionState.CONNECTED,
            "storage_type": self.storage_type,
            "bucket": self.bucket,
            "connected_at": self._connection_time.isoformat() if self._connection_time else None
        }

    async def execute_ddl(self, ddl: str) -> bool:
        """Not applicable for storage clients"""
        raise MCPClientError("DDL operations not supported for storage clients")


class MessageQueueClient(BaseMCPClient):
    """MCP client for message queue systems"""

    def __init__(self):
        super().__init__()
        self.queue_type = None
        self.queue_name = None
        self.messages = []  # Mock message storage

    async def connect(self, config: ConnectionConfig) -> bool:
        """Connect to message queue"""
        try:
            self._state = ConnectionState.CONNECTING

            self.queue_type = config.extra_params.get('queue_type', 'rabbitmq')
            self.queue_name = config.database  # Use database field for queue name

            # Would initialize actual queue client here

            self._state = ConnectionState.CONNECTED
            self._connection_time = datetime.utcnow()
            logger.info(f"Connected to {self.queue_type}: {self.queue_name}")
            return True

        except Exception as e:
            self._state = ConnectionState.ERROR
            self._last_error = str(e)
            raise MCPClientError(f"Queue connection failed: {e}")

    async def publish(self, message: Dict[str, Any]) -> bool:
        """Publish message to queue"""
        if self._state != ConnectionState.CONNECTED:
            raise MCPClientError("Not connected to queue")

        self.messages.append({
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
        logger.info(f"Published message to {self.queue_name}")
        return True

    async def consume(self, max_messages: int = 1) -> List[Dict[str, Any]]:
        """Consume messages from queue"""
        if self._state != ConnectionState.CONNECTED:
            raise MCPClientError("Not connected to queue")

        # Return mock messages
        consumed = self.messages[:max_messages]
        self.messages = self.messages[max_messages:]
        return consumed

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute queue operation as query"""
        operation = params.get('operation', 'consume') if params else 'consume'

        if operation == 'publish':
            await self.publish(params.get('message', {}))
            return QueryResult(
                columns=["status"],
                rows=[("published",)],
                rowcount=1,
                execution_time=0.01,
                metadata={"operation": "publish"}
            )
        elif operation == 'consume':
            messages = await self.consume(params.get('max_messages', 1))
            return QueryResult(
                columns=["message", "timestamp"],
                rows=[(m['message'], m['timestamp']) for m in messages],
                rowcount=len(messages),
                execution_time=0.01,
                metadata={"operation": "consume"}
            )
        else:
            raise MCPClientError(f"Unsupported operation: {operation}")

    async def disconnect(self) -> bool:
        """Disconnect from queue"""
        self._state = ConnectionState.DISCONNECTED
        self.messages.clear()
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Check queue health"""
        return {
            "healthy": self._state == ConnectionState.CONNECTED,
            "queue_type": self.queue_type,
            "queue_name": self.queue_name,
            "pending_messages": len(self.messages),
            "connected_at": self._connection_time.isoformat() if self._connection_time else None
        }

    async def execute_ddl(self, ddl: str) -> bool:
        """Not applicable for queue clients"""
        raise MCPClientError("DDL operations not supported for queue clients")


class EnhancedConnectionManager(ConnectionManager):
    """
    Enhanced MCP Connection Manager with multi-protocol support

    Extends base connection manager to handle various protocols
    and provide unified resource/tool discovery.
    """

    # Extended client registry
    EXTENDED_CLIENT_REGISTRY: Dict[str, Type[BaseMCPClient]] = {
        'api': APIClient,
        'rest': APIClient,
        'graphql': APIClient,
        'storage': FileStorageClient,
        's3': FileStorageClient,
        'gcs': FileStorageClient,
        'queue': MessageQueueClient,
        'rabbitmq': MessageQueueClient,
        'kafka': MessageQueueClient,
    }

    def __init__(self, max_connections: int = 20,
                 health_check_interval: int = 60,
                 auto_reconnect: bool = True):
        super().__init__(max_connections)
        # Merge registries
        self.CLIENT_REGISTRY.update(self.EXTENDED_CLIENT_REGISTRY)
        self._resources: List[MCPResource] = []
        self._tools: List[MCPTool] = []
        self._health_check_interval = health_check_interval
        self._auto_reconnect = auto_reconnect
        self._health_check_task: Optional[asyncio.Task] = None
        self._initialize_resources()

    def _initialize_resources(self):
        """Initialize available MCP resources"""
        # Database resources
        self._resources.extend([
            MCPResource(
                uri="mcp://database/postgresql",
                name="PostgreSQL Database",
                protocol=ProtocolType.DATABASE,
                description="PostgreSQL relational database",
                capabilities=["query", "ddl", "transaction"]
            ),
            MCPResource(
                uri="mcp://database/mysql",
                name="MySQL Database",
                protocol=ProtocolType.DATABASE,
                description="MySQL relational database",
                capabilities=["query", "ddl", "transaction"]
            ),
        ])

        # API resources
        self._resources.extend([
            MCPResource(
                uri="mcp://api/rest",
                name="REST API",
                protocol=ProtocolType.REST_API,
                description="RESTful API endpoint",
                capabilities=["get", "post", "put", "delete"]
            ),
            MCPResource(
                uri="mcp://api/graphql",
                name="GraphQL API",
                protocol=ProtocolType.GRAPHQL,
                description="GraphQL API endpoint",
                capabilities=["query", "mutation", "subscription"]
            ),
        ])

        # Storage resources
        self._resources.append(
            MCPResource(
                uri="mcp://storage/s3",
                name="AWS S3",
                protocol=ProtocolType.FILE_STORAGE,
                description="AWS S3 object storage",
                capabilities=["read", "write", "list", "delete"]
            )
        )

        # Message queue resources
        self._resources.append(
            MCPResource(
                uri="mcp://queue/rabbitmq",
                name="RabbitMQ",
                protocol=ProtocolType.MESSAGE_QUEUE,
                description="RabbitMQ message broker",
                capabilities=["publish", "consume", "acknowledge"]
            )
        )

    async def list_resources(self) -> List[MCPResource]:
        """List all available MCP resources"""
        return self._resources

    async def list_tools(self) -> List[MCPTool]:
        """List all available MCP tools"""
        if not self._tools:
            self._initialize_tools()
        return self._tools

    def _initialize_tools(self):
        """Initialize MCP tools"""
        self._tools = [
            MCPTool(
                name="execute_sql",
                description="Execute SQL query on database",
                parameters={"query": "string", "params": "object"},
                returns={"result": "QueryResult"},
                protocol=ProtocolType.DATABASE
            ),
            MCPTool(
                name="api_request",
                description="Make API request",
                parameters={"method": "string", "endpoint": "string", "body": "object"},
                returns={"response": "object"},
                protocol=ProtocolType.REST_API
            ),
            MCPTool(
                name="read_file",
                description="Read file from storage",
                parameters={"key": "string"},
                returns={"content": "string"},
                protocol=ProtocolType.FILE_STORAGE
            ),
            MCPTool(
                name="publish_message",
                description="Publish message to queue",
                parameters={"message": "object", "routing_key": "string"},
                returns={"success": "boolean"},
                protocol=ProtocolType.MESSAGE_QUEUE
            ),
        ]

    async def execute_tool(self, tool_name: str, connection_id: str,
                          params: Dict[str, Any]) -> Any:
        """Execute an MCP tool on a connection"""
        # Find the tool
        tool = next((t for t in self._tools if t.name == tool_name), None)
        if not tool:
            raise MCPClientError(f"Unknown tool: {tool_name}")

        # Get connection
        connection_info = self._connections.get(connection_id)
        if not connection_info:
            raise MCPClientError(f"Connection not found: {connection_id}")

        client = connection_info.client

        # Execute based on tool
        if tool_name == "execute_sql":
            return await client.execute_query(params['query'], params.get('params'))
        elif tool_name == "api_request":
            return await client.execute_query(
                params['endpoint'],
                params['method'],
                params.get('body')
            )
        elif tool_name == "read_file":
            return await client.read_file(params['key'])
        elif tool_name == "publish_message":
            return await client.publish(params['message'])
        else:
            raise MCPClientError(f"Tool not implemented: {tool_name}")

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about all connections"""
        stats = {
            "total_connections": len(self._connections),
            "max_connections": self._max_connections,
            "connections_by_type": {},
            "connections_by_state": {},
            "resources_available": len(self._resources),
            "tools_available": len(self._tools)
        }

        for conn_info in self._connections.values():
            # By type
            conn_type = conn_info.client_type
            stats["connections_by_type"][conn_type] = stats["connections_by_type"].get(conn_type, 0) + 1

            # By state
            state = conn_info.client.state.value
            stats["connections_by_state"][state] = stats["connections_by_state"].get(state, 0) + 1

        return stats

    # Health Monitoring and Auto-Reconnection

    async def start_health_monitoring(self) -> None:
        """Start background health monitoring task"""
        if self._health_check_task and not self._health_check_task.done():
            logger.warning("Health monitoring already running")
            return

        self._health_check_task = asyncio.create_task(self._health_monitor_loop())
        logger.info("Started health monitoring")

    async def stop_health_monitoring(self) -> None:
        """Stop background health monitoring task"""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped health monitoring")

    async def _health_monitor_loop(self) -> None:
        """Background loop for health monitoring"""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self._check_all_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")

    async def _check_all_connections(self) -> None:
        """Check health of all connections and reconnect if needed"""
        for conn_id, conn_info in list(self._connections.items()):
            try:
                health = await conn_info.client.health_check()

                if not health.get('connected', False) or not health.get('ping_successful', True):
                    logger.warning(f"Connection {conn_id} unhealthy: {health}")

                    if self._auto_reconnect:
                        logger.info(f"Attempting to reconnect: {conn_id}")
                        try:
                            await self.reconnect(conn_id)
                            logger.info(f"Successfully reconnected: {conn_id}")
                        except Exception as reconnect_error:
                            logger.error(f"Failed to reconnect {conn_id}: {reconnect_error}")

            except Exception as e:
                logger.error(f"Health check failed for {conn_id}: {e}")

    async def get_connection_health(self, connection_id: str) -> Dict[str, Any]:
        """
        Get health status for a specific connection

        Args:
            connection_id: Connection identifier

        Returns:
            Health status dictionary

        Raises:
            MCPClientError: If connection not found
        """
        async with self._lock:
            conn_info = self._connections.get(connection_id)
            if not conn_info:
                raise MCPClientError(
                    f"Connection '{connection_id}' not found",
                    "CONNECTION_NOT_FOUND"
                )

            return await conn_info.client.health_check()

    async def get_all_connection_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status for all connections

        Returns:
            Dictionary mapping connection_id to health status
        """
        health_status = {}

        for conn_id in list(self._connections.keys()):
            try:
                health_status[conn_id] = await self.get_connection_health(conn_id)
            except Exception as e:
                health_status[conn_id] = {
                    'error': str(e),
                    'connected': False
                }

        return health_status

    async def resize_pool(self, new_max: int) -> None:
        """
        Resize connection pool

        Args:
            new_max: New maximum connections

        Raises:
            MCPClientError: If new size is smaller than current connections
        """
        async with self._lock:
            current_count = len(self._connections)

            if new_max < current_count:
                raise MCPClientError(
                    f"Cannot resize pool to {new_max}, currently have {current_count} connections",
                    "INVALID_POOL_SIZE"
                )

            self._max_connections = new_max
            logger.info(f"Resized connection pool to {new_max}")

    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics

        Returns:
            Pool statistics dictionary
        """
        return {
            'current_connections': len(self._connections),
            'max_connections': self._max_connections,
            'utilization_percent': (len(self._connections) / self._max_connections * 100)
                if self._max_connections > 0 else 0,
            'health_check_interval': self._health_check_interval,
            'auto_reconnect_enabled': self._auto_reconnect,
            'health_monitoring_active': (
                self._health_check_task is not None and
                not self._health_check_task.done()
            )
        }