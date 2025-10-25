"""
MongoDB MCP Client Implementation

Implements MongoDB database connectivity using motor for async operations.
"""

import asyncio
from typing import Any, Dict, Optional, List, Union
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import PyMongoError, ConnectionFailure
from bson import ObjectId
from .base import BaseMCPClient, ConnectionConfig, MCPClientError


class MongoDBClient(BaseMCPClient):
    """
    MongoDB database client using motor

    Provides async interface to MongoDB database operations including
    CRUD, aggregation pipelines, and index management.
    """

    def __init__(self) -> None:
        super().__init__()
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._default_collection: Optional[str] = None

    async def _connect_impl(self, config: ConnectionConfig) -> Any:
        """
        Connect to MongoDB database

        Args:
            config: Connection configuration

        Returns:
            Motor client instance
        """
        # Build connection URI
        if config.username and config.password:
            uri = f"mongodb://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        else:
            uri = f"mongodb://{config.host}:{config.port}/{config.database}"

        # Add extra parameters to URI
        if config.extra_params:
            params = "&".join([f"{k}={v}" for k, v in config.extra_params.items()])
            uri += f"?{params}"

        # Create motor client
        self._client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        self._database = self._client[config.database]

        # Verify connection
        try:
            await self._client.admin.command('ping')
        except ConnectionFailure as e:
            raise MCPClientError(f"Failed to connect to MongoDB: {str(e)}", "CONNECTION_FAILED")

        return self._client

    async def _disconnect_impl(self) -> None:
        """Disconnect from MongoDB"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None

    async def _execute_query_impl(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute MongoDB query (JSON format)

        Args:
            query: MongoDB query as JSON string (e.g., '{"operation": "find", "collection": "users", "filter": {...}}')
            params: Additional parameters

        Returns:
            Dictionary with results
        """
        import json

        if self._database is None:
            raise MCPClientError("No active database connection", "NOT_CONNECTED")

        try:
            # Parse query
            query_dict = json.loads(query) if isinstance(query, str) else query
            operation = query_dict.get('operation', 'find')
            collection_name = query_dict.get('collection')

            if not collection_name:
                raise MCPClientError("Collection name required", "INVALID_QUERY")

            collection = self._database[collection_name]

            # Execute operation
            if operation == 'find':
                results = await self._execute_find(collection, query_dict)
            elif operation == 'insert_one':
                results = await self._execute_insert_one(collection, query_dict)
            elif operation == 'insert_many':
                results = await self._execute_insert_many(collection, query_dict)
            elif operation == 'update_one':
                results = await self._execute_update_one(collection, query_dict)
            elif operation == 'update_many':
                results = await self._execute_update_many(collection, query_dict)
            elif operation == 'delete_one':
                results = await self._execute_delete_one(collection, query_dict)
            elif operation == 'delete_many':
                results = await self._execute_delete_many(collection, query_dict)
            elif operation == 'aggregate':
                results = await self._execute_aggregate(collection, query_dict)
            else:
                raise MCPClientError(f"Unsupported operation: {operation}", "INVALID_OPERATION")

            return {
                'columns': results.get('columns', []),
                'rows': results.get('rows', []),
                'rowcount': results.get('rowcount', 0),
                'metadata': {
                    'database': self._config.database if self._config else 'unknown',
                    'collection': collection_name,
                    'operation': operation
                }
            }

        except json.JSONDecodeError as e:
            raise MCPClientError(f"Invalid JSON query: {str(e)}", "INVALID_QUERY")
        except PyMongoError as e:
            raise MCPClientError(f"MongoDB error: {str(e)}", "QUERY_FAILED")

    async def _execute_find(self, collection: AsyncIOMotorCollection, query: Dict) -> Dict:
        """Execute find operation"""
        filter_query = query.get('filter', {})
        projection = query.get('projection')
        limit = query.get('limit', 0)
        skip = query.get('skip', 0)
        sort = query.get('sort')

        cursor = collection.find(filter_query, projection)

        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        if sort:
            cursor = cursor.sort(sort)

        documents = await cursor.to_list(length=limit if limit else None)

        # Convert ObjectId to string
        for doc in documents:
            if '_id' in doc and isinstance(doc['_id'], ObjectId):
                doc['_id'] = str(doc['_id'])

        # Extract columns from first document
        columns = list(documents[0].keys()) if documents else []
        rows = [tuple(doc.values()) for doc in documents]

        return {
            'columns': columns,
            'rows': rows,
            'rowcount': len(documents)
        }

    async def _execute_insert_one(self, collection: AsyncIOMotorCollection, query: Dict) -> Dict:
        """Execute insert_one operation"""
        document = query.get('document', {})
        result = await collection.insert_one(document)

        return {
            'columns': ['inserted_id'],
            'rows': [(str(result.inserted_id),)],
            'rowcount': 1 if result.inserted_id else 0
        }

    async def _execute_insert_many(self, collection: AsyncIOMotorCollection, query: Dict) -> Dict:
        """Execute insert_many operation"""
        documents = query.get('documents', [])
        result = await collection.insert_many(documents)

        return {
            'columns': ['inserted_count', 'inserted_ids'],
            'rows': [(len(result.inserted_ids), [str(id) for id in result.inserted_ids])],
            'rowcount': len(result.inserted_ids)
        }

    async def _execute_update_one(self, collection: AsyncIOMotorCollection, query: Dict) -> Dict:
        """Execute update_one operation"""
        filter_query = query.get('filter', {})
        update = query.get('update', {})
        upsert = query.get('upsert', False)

        result = await collection.update_one(filter_query, update, upsert=upsert)

        return {
            'columns': ['matched_count', 'modified_count', 'upserted_id'],
            'rows': [(result.matched_count, result.modified_count,
                     str(result.upserted_id) if result.upserted_id else None)],
            'rowcount': result.modified_count
        }

    async def _execute_update_many(self, collection: AsyncIOMotorCollection, query: Dict) -> Dict:
        """Execute update_many operation"""
        filter_query = query.get('filter', {})
        update = query.get('update', {})
        upsert = query.get('upsert', False)

        result = await collection.update_many(filter_query, update, upsert=upsert)

        return {
            'columns': ['matched_count', 'modified_count'],
            'rows': [(result.matched_count, result.modified_count)],
            'rowcount': result.modified_count
        }

    async def _execute_delete_one(self, collection: AsyncIOMotorCollection, query: Dict) -> Dict:
        """Execute delete_one operation"""
        filter_query = query.get('filter', {})
        result = await collection.delete_one(filter_query)

        return {
            'columns': ['deleted_count'],
            'rows': [(result.deleted_count,)],
            'rowcount': result.deleted_count
        }

    async def _execute_delete_many(self, collection: AsyncIOMotorCollection, query: Dict) -> Dict:
        """Execute delete_many operation"""
        filter_query = query.get('filter', {})
        result = await collection.delete_many(filter_query)

        return {
            'columns': ['deleted_count'],
            'rows': [(result.deleted_count,)],
            'rowcount': result.deleted_count
        }

    async def _execute_aggregate(self, collection: AsyncIOMotorCollection, query: Dict) -> Dict:
        """Execute aggregation pipeline"""
        pipeline = query.get('pipeline', [])

        cursor = collection.aggregate(pipeline)
        documents = await cursor.to_list(length=None)

        # Convert ObjectId to string
        for doc in documents:
            if '_id' in doc and isinstance(doc['_id'], ObjectId):
                doc['_id'] = str(doc['_id'])

        columns = list(documents[0].keys()) if documents else []
        rows = [tuple(doc.values()) for doc in documents]

        return {
            'columns': columns,
            'rows': rows,
            'rowcount': len(documents)
        }

    async def _execute_ddl_impl(self, ddl: str) -> None:
        """
        Execute DDL-like operation (create collection, index management)

        Args:
            ddl: JSON string with DDL operation
        """
        import json

        if self._database is None:
            raise MCPClientError("No active database connection", "NOT_CONNECTED")

        try:
            ddl_dict = json.loads(ddl) if isinstance(ddl, str) else ddl
            operation = ddl_dict.get('operation')
            collection_name = ddl_dict.get('collection')

            if not collection_name:
                raise MCPClientError("Collection name required", "INVALID_DDL")

            collection = self._database[collection_name]

            if operation == 'create_collection':
                # Collection is created automatically on first write
                pass
            elif operation == 'drop_collection':
                await collection.drop()
            elif operation == 'create_index':
                keys = ddl_dict.get('keys', [])
                options = ddl_dict.get('options', {})
                await collection.create_index(keys, **options)
            elif operation == 'drop_index':
                index_name = ddl_dict.get('index_name')
                await collection.drop_index(index_name)
            elif operation == 'create_indexes':
                indexes = ddl_dict.get('indexes', [])
                await collection.create_indexes(indexes)
            else:
                raise MCPClientError(f"Unsupported DDL operation: {operation}", "INVALID_DDL")

        except json.JSONDecodeError as e:
            raise MCPClientError(f"Invalid JSON DDL: {str(e)}", "INVALID_DDL")
        except PyMongoError as e:
            raise MCPClientError(f"MongoDB DDL error: {str(e)}", "DDL_FAILED")

    def _get_ping_query(self) -> str:
        """Get MongoDB-specific ping query"""
        return '{"operation": "find", "collection": "system.profile", "filter": {}, "limit": 1}'

    async def get_collections(self) -> List[str]:
        """
        Get list of collections in database

        Returns:
            List of collection names
        """
        if self._database is None:
            raise MCPClientError("No active database connection", "NOT_CONNECTED")

        return await self._database.list_collection_names()

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with collection statistics
        """
        if self._database is None:
            raise MCPClientError("No active database connection", "NOT_CONNECTED")

        stats = await self._database.command('collStats', collection_name)

        return {
            'name': collection_name,
            'count': stats.get('count', 0),
            'size': stats.get('size', 0),
            'avgObjSize': stats.get('avgObjSize', 0),
            'storageSize': stats.get('storageSize', 0),
            'indexes': stats.get('nindexes', 0),
            'totalIndexSize': stats.get('totalIndexSize', 0)
        }

    async def list_indexes(self, collection_name: str) -> List[Dict[str, Any]]:
        """
        List all indexes for a collection

        Args:
            collection_name: Name of the collection

        Returns:
            List of index information
        """
        if self._database is None:
            raise MCPClientError("No active database connection", "NOT_CONNECTED")

        collection = self._database[collection_name]
        cursor = collection.list_indexes()
        indexes = await cursor.to_list(length=None)

        return indexes

    async def create_index(
        self,
        collection_name: str,
        keys: List[tuple],
        unique: bool = False,
        sparse: bool = False,
        name: Optional[str] = None
    ) -> str:
        """
        Create an index on a collection

        Args:
            collection_name: Name of the collection
            keys: List of (field, direction) tuples
            unique: Whether index should be unique
            sparse: Whether index should be sparse
            name: Optional index name

        Returns:
            Name of created index
        """
        if self._database is None:
            raise MCPClientError("No active database connection", "NOT_CONNECTED")

        collection = self._database[collection_name]
        options = {'unique': unique, 'sparse': sparse}

        if name:
            options['name'] = name

        index_name = await collection.create_index(keys, **options)
        return index_name

    async def drop_index(self, collection_name: str, index_name: str) -> None:
        """
        Drop an index from a collection

        Args:
            collection_name: Name of the collection
            index_name: Name of the index to drop
        """
        if self._database is None:
            raise MCPClientError("No active database connection", "NOT_CONNECTED")

        collection = self._database[collection_name]
        await collection.drop_index(index_name)

    async def count_documents(
        self,
        collection_name: str,
        filter_query: Optional[Dict] = None
    ) -> int:
        """
        Count documents in a collection

        Args:
            collection_name: Name of the collection
            filter_query: Optional filter

        Returns:
            Document count
        """
        if self._database is None:
            raise MCPClientError("No active database connection", "NOT_CONNECTED")

        collection = self._database[collection_name]
        return await collection.count_documents(filter_query or {})
