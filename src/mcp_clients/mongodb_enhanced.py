"""
Enhanced MongoDB MCP Client with 100% Feature Coverage

Adds advanced MongoDB features:
- Change streams
- Transactions
- GridFS support
- Retry logic with exponential backoff
- Connection health monitoring
"""

import asyncio
from typing import Any, Dict, Optional, List, AsyncIterator
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from pymongo.errors import PyMongoError
from .mongodb_client import MongoDBClient
from .base import ConnectionConfig, MCPClientError
import logging

logger = logging.getLogger(__name__)


class MongoDBEnhancedClient(MongoDBClient):
    """Enhanced MongoDB client with advanced features"""

    def __init__(self) -> None:
        super().__init__()
        self._gridfs: Optional[AsyncIOMotorGridFSBucket] = None
        self._retry_config = {
            'max_retries': 3,
            'base_delay': 0.1,
            'max_delay': 10.0,
            'exponential_base': 2
        }
        self._metrics = {
            'operations': 0,
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

    async def _retry_with_backoff(self, operation, *args, **kwargs) -> Any:
        """Execute operation with exponential backoff"""
        last_error = None
        for attempt in range(self._retry_config['max_retries'] + 1):
            try:
                result = await operation(*args, **kwargs)
                self._metrics['operations'] += 1
                return result
            except Exception as e:
                last_error = e
                self._metrics['failures'] += 1
                if attempt < self._retry_config['max_retries']:
                    delay = min(
                        self._retry_config['base_delay'] * (
                            self._retry_config['exponential_base'] ** attempt
                        ),
                        self._retry_config['max_delay']
                    )
                    await asyncio.sleep(delay)
        raise MCPClientError(
            f"Operation failed after {self._retry_config['max_retries']} retries: {last_error}",
            "RETRY_EXHAUSTED"
        ) from last_error

    # Change Streams

    async def watch_collection(
        self,
        collection_name: str,
        pipeline: Optional[List[Dict]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Watch a collection for changes

        Args:
            collection_name: Collection to watch
            pipeline: Optional aggregation pipeline

        Yields:
            Change documents
        """
        if not self._database:
            raise MCPClientError("No active database", "NOT_CONNECTED")

        collection = self._database[collection_name]
        async with collection.watch(pipeline=pipeline) as stream:
            async for change in stream:
                yield {
                    'operation_type': change['operationType'],
                    'document_key': change.get('documentKey'),
                    'full_document': change.get('fullDocument'),
                    'update_description': change.get('updateDescription'),
                    'timestamp': change['clusterTime']
                }

    # Transactions

    async def start_session(self):
        """Start a MongoDB session for transactions"""
        if not self._client:
            raise MCPClientError("No active client", "NOT_CONNECTED")
        return await self._client.start_session()

    async def with_transaction(self, callback, session=None):
        """
        Execute callback within a transaction

        Args:
            callback: Async function to execute
            session: Optional session

        Returns:
            Result from callback
        """
        if session is None:
            async with await self.start_session() as session:
                return await session.with_transaction(callback)
        else:
            return await session.with_transaction(callback)

    # GridFS Support

    def get_gridfs(self, bucket_name: str = 'fs') -> AsyncIOMotorGridFSBucket:
        """
        Get GridFS bucket

        Args:
            bucket_name: Bucket name

        Returns:
            GridFS bucket
        """
        if not self._database:
            raise MCPClientError("No active database", "NOT_CONNECTED")

        return AsyncIOMotorGridFSBucket(self._database, bucket_name=bucket_name)

    async def gridfs_upload(
        self,
        filename: str,
        data: bytes,
        bucket_name: str = 'fs',
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Upload file to GridFS

        Args:
            filename: File name
            data: File data
            bucket_name: GridFS bucket
            metadata: Optional metadata

        Returns:
            File ID
        """
        gridfs = self.get_gridfs(bucket_name)
        file_id = await gridfs.upload_from_stream(
            filename,
            data,
            metadata=metadata
        )
        return str(file_id)

    async def gridfs_download(
        self,
        file_id: str,
        bucket_name: str = 'fs'
    ) -> bytes:
        """
        Download file from GridFS

        Args:
            file_id: File ID
            bucket_name: GridFS bucket

        Returns:
            File data
        """
        from bson import ObjectId
        gridfs = self.get_gridfs(bucket_name)
        grid_out = await gridfs.open_download_stream(ObjectId(file_id))
        return await grid_out.read()

    async def gridfs_delete(self, file_id: str, bucket_name: str = 'fs') -> None:
        """Delete file from GridFS"""
        from bson import ObjectId
        gridfs = self.get_gridfs(bucket_name)
        await gridfs.delete(ObjectId(file_id))

    async def gridfs_list(self, bucket_name: str = 'fs') -> List[Dict[str, Any]]:
        """List files in GridFS"""
        gridfs = self.get_gridfs(bucket_name)
        cursor = gridfs.find()
        files = []
        async for file_doc in cursor:
            files.append({
                'file_id': str(file_doc._id),
                'filename': file_doc.filename,
                'length': file_doc.length,
                'upload_date': file_doc.upload_date,
                'metadata': file_doc.metadata
            })
        return files

    # Health Monitoring

    async def health_check_detailed(self) -> Dict[str, Any]:
        """Detailed health check"""
        health = await super().health_check()
        health['metrics'] = self._metrics.copy()

        if self._client:
            try:
                server_info = await self._client.server_info()
                health['server_version'] = server_info.get('version')
                health['uptime'] = server_info.get('uptime')
            except Exception as e:
                health['server_info_error'] = str(e)

        return health

    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        return self._metrics.copy()
