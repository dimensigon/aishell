"""
Database Metadata Cache with FAISS-based Semantic Search

Provides intelligent caching and semantic search for database metadata including
tables, columns, indexes, and relationships.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

import numpy as np

from ..vector.store import VectorDatabase

# FAISS is now required
try:
    import faiss
except ImportError:
    raise ImportError(
        "FAISS is required for DatabaseMetadataCache. "
        "Install with: pip install faiss-cpu==1.12.0"
    )

logger = logging.getLogger(__name__)


@dataclass
class TableMetadata:
    """Metadata for a database table."""
    connection_id: str
    schema: str
    name: str
    description: str = ""
    columns: List[Dict[str, Any]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = field(default_factory=list)
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'connection_id': self.connection_id,
            'schema': self.schema,
            'name': self.name,
            'description': self.description,
            'columns': self.columns,
            'indexes': self.indexes,
            'foreign_keys': self.foreign_keys,
            'row_count': self.row_count,
            'size_bytes': self.size_bytes,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TableMetadata':
        """Create from dictionary."""
        if data.get('last_updated'):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


@dataclass
class ColumnMetadata:
    """Metadata for a database column."""
    connection_id: str
    schema: str
    table_name: str
    name: str
    data_type: str
    nullable: bool = True
    default_value: Optional[str] = None
    description: str = ""
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_ref: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'connection_id': self.connection_id,
            'schema': self.schema,
            'table_name': self.table_name,
            'name': self.name,
            'data_type': self.data_type,
            'nullable': self.nullable,
            'default_value': self.default_value,
            'description': self.description,
            'is_primary_key': self.is_primary_key,
            'is_foreign_key': self.is_foreign_key,
            'foreign_key_ref': self.foreign_key_ref
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColumnMetadata':
        """Create from dictionary."""
        return cls(**data)


class DatabaseMetadataCache:
    """
    Intelligent cache for database metadata with semantic search capabilities.

    Features:
    - FAISS-based vector search for tables and columns
    - Persistent disk storage
    - Automatic indexing of MCP database metadata
    - Fast lookup and semantic search
    """

    def __init__(self, cache_dir: str, dimension: int = 384):
        """
        Initialize metadata cache.

        Args:
            cache_dir: Directory for cache storage
            dimension: Embedding dimension (default 384 for sentence transformers)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.dimension = dimension

        # Vector database for semantic search (FAISS required)
        self.vector_db = VectorDatabase(dimension=dimension, use_faiss=True)

        # Metadata storage
        self.tables: Dict[str, TableMetadata] = {}  # key: connection_id:schema.table
        self.columns: Dict[str, ColumnMetadata] = {}  # key: connection_id:schema.table.column

        # Track cache state
        self.last_refresh: Dict[str, datetime] = {}  # connection_id -> timestamp

        logger.info(f"Initialized DatabaseMetadataCache with FAISS (dimension={dimension})")

    def _make_table_key(self, connection_id: str, schema: str, table_name: str) -> str:
        """Create unique key for table."""
        return f"{connection_id}:{schema}.{table_name}"

    def _make_column_key(self, connection_id: str, schema: str, table_name: str, column_name: str) -> str:
        """Create unique key for column."""
        return f"{connection_id}:{schema}.{table_name}.{column_name}"

    def _text_to_vector(self, text: str) -> np.ndarray:
        """
        Convert text to embedding vector.

        For now, uses simple hash-based embedding. In production, this should use
        a proper embedding model like sentence-transformers.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        # Simple hash-based embedding (placeholder for real embedding model)
        # In production, use: from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer('all-MiniLM-L6-v2')
        # return model.encode(text)

        # Hash-based deterministic "embedding"
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to vector
        vector = np.zeros(self.dimension, dtype=np.float32)
        for i in range(min(len(hash_bytes), self.dimension)):
            vector[i] = (hash_bytes[i] / 255.0) - 0.5

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    async def index_database(self, connection_id: str, metadata: Dict[str, Any]) -> None:
        """
        Index database metadata for semantic search.

        Args:
            connection_id: MCP connection identifier
            metadata: Database metadata structure with tables and columns
        """
        logger.info(f"Indexing database metadata for connection: {connection_id}")

        tables = metadata.get('tables', [])
        indexed_tables = 0
        indexed_columns = 0

        for table_info in tables:
            schema = table_info.get('schema', 'public')
            table_name = table_info.get('name', '')

            if not table_name:
                continue

            # Create table metadata
            table_meta = TableMetadata(
                connection_id=connection_id,
                schema=schema,
                name=table_name,
                description=table_info.get('description', ''),
                columns=table_info.get('columns', []),
                indexes=table_info.get('indexes', []),
                foreign_keys=table_info.get('foreign_keys', []),
                row_count=table_info.get('row_count'),
                size_bytes=table_info.get('size_bytes'),
                last_updated=datetime.utcnow()
            )

            # Store table metadata
            table_key = self._make_table_key(connection_id, schema, table_name)
            self.tables[table_key] = table_meta

            # Index table for semantic search
            table_text = f"Table: {schema}.{table_name}. {table_meta.description}"
            table_vector = self._text_to_vector(table_text)

            self.vector_db.add_object(
                object_id=table_key,
                vector=table_vector,
                object_type='table',
                metadata={
                    'connection_id': connection_id,
                    'schema': schema,
                    'name': table_name,
                    'description': table_meta.description
                }
            )
            indexed_tables += 1

            # Index columns
            for column_info in table_info.get('columns', []):
                column_name = column_info.get('name', '')
                if not column_name:
                    continue

                column_meta = ColumnMetadata(
                    connection_id=connection_id,
                    schema=schema,
                    table_name=table_name,
                    name=column_name,
                    data_type=column_info.get('type', 'unknown'),
                    nullable=column_info.get('nullable', True),
                    default_value=column_info.get('default'),
                    description=column_info.get('description', ''),
                    is_primary_key=column_info.get('is_primary_key', False),
                    is_foreign_key=column_info.get('is_foreign_key', False),
                    foreign_key_ref=column_info.get('foreign_key_ref')
                )

                # Store column metadata
                column_key = self._make_column_key(connection_id, schema, table_name, column_name)
                self.columns[column_key] = column_meta

                # Index column for semantic search
                column_text = (
                    f"Column: {schema}.{table_name}.{column_name}. "
                    f"Type: {column_meta.data_type}. {column_meta.description}"
                )
                column_vector = self._text_to_vector(column_text)

                self.vector_db.add_object(
                    object_id=column_key,
                    vector=column_vector,
                    object_type='column',
                    metadata={
                        'connection_id': connection_id,
                        'schema': schema,
                        'table_name': table_name,
                        'name': column_name,
                        'data_type': column_meta.data_type,
                        'description': column_meta.description
                    }
                )
                indexed_columns += 1

        self.last_refresh[connection_id] = datetime.utcnow()
        logger.info(
            f"Indexed {indexed_tables} tables and {indexed_columns} columns "
            f"for connection {connection_id}"
        )

    async def search_tables(
        self,
        query: str,
        connection_id: Optional[str] = None,
        limit: int = 5,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search for tables semantically.

        Args:
            query: Search query
            connection_id: Optional filter by connection
            limit: Maximum results
            threshold: Minimum similarity threshold

        Returns:
            List of matching tables with metadata
        """
        query_vector = self._text_to_vector(query)

        results = self.vector_db.search_similar(
            query_vector=query_vector,
            k=limit * 2,  # Get more for filtering
            object_type='table',
            threshold=threshold
        )

        matches = []
        for entry, distance in results:
            # Filter by connection if specified
            if connection_id and entry.metadata.get('connection_id') != connection_id:
                continue

            matches.append({
                'connection_id': entry.metadata.get('connection_id'),
                'schema': entry.metadata.get('schema'),
                'name': entry.metadata.get('name'),
                'description': entry.metadata.get('description'),
                'similarity': 1.0 / (1.0 + distance)  # Convert distance to similarity
            })

            if len(matches) >= limit:
                break

        return matches

    async def search_columns(
        self,
        query: str,
        connection_id: Optional[str] = None,
        table_name: Optional[str] = None,
        limit: int = 5,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search for columns semantically.

        Args:
            query: Search query
            connection_id: Optional filter by connection
            table_name: Optional filter by table
            limit: Maximum results
            threshold: Minimum similarity threshold

        Returns:
            List of matching columns with metadata
        """
        query_vector = self._text_to_vector(query)

        results = self.vector_db.search_similar(
            query_vector=query_vector,
            k=limit * 3,  # Get more for filtering
            object_type='column',
            threshold=threshold
        )

        matches = []
        for entry, distance in results:
            # Filter by connection if specified
            if connection_id and entry.metadata.get('connection_id') != connection_id:
                continue

            # Filter by table if specified
            if table_name and entry.metadata.get('table_name') != table_name:
                continue

            matches.append({
                'connection_id': entry.metadata.get('connection_id'),
                'schema': entry.metadata.get('schema'),
                'table_name': entry.metadata.get('table_name'),
                'name': entry.metadata.get('name'),
                'data_type': entry.metadata.get('data_type'),
                'description': entry.metadata.get('description'),
                'similarity': 1.0 / (1.0 + distance)
            })

            if len(matches) >= limit:
                break

        return matches

    def get_table(self, connection_id: str, schema: str, table_name: str) -> Optional[TableMetadata]:
        """Get table metadata by name."""
        key = self._make_table_key(connection_id, schema, table_name)
        return self.tables.get(key)

    def get_column(
        self,
        connection_id: str,
        schema: str,
        table_name: str,
        column_name: str
    ) -> Optional[ColumnMetadata]:
        """Get column metadata by name."""
        key = self._make_column_key(connection_id, schema, table_name, column_name)
        return self.columns.get(key)

    def clear_connection(self, connection_id: str) -> None:
        """Clear all cached metadata for a connection."""
        # Remove tables
        tables_to_remove = [
            key for key, table in self.tables.items()
            if table.connection_id == connection_id
        ]
        for key in tables_to_remove:
            del self.tables[key]
            # Also remove from vector DB
            self.vector_db.delete_by_id(key)

        # Remove columns
        columns_to_remove = [
            key for key, column in self.columns.items()
            if column.connection_id == connection_id
        ]
        for key in columns_to_remove:
            del self.columns[key]
            self.vector_db.delete_by_id(key)

        # Remove refresh timestamp
        self.last_refresh.pop(connection_id, None)

        logger.info(f"Cleared cache for connection: {connection_id}")

    def clear_all(self) -> None:
        """Clear all cached metadata."""
        self.tables.clear()
        self.columns.clear()
        self.last_refresh.clear()
        self.vector_db = VectorDatabase(dimension=self.dimension, use_faiss=True)
        logger.info("Cleared all metadata cache")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        connections = set(table.connection_id for table in self.tables.values())

        return {
            'total_tables': len(self.tables),
            'total_columns': len(self.columns),
            'connections_cached': len(connections),
            'vector_db_stats': self.vector_db.get_stats(),
            'last_refresh': {
                conn_id: timestamp.isoformat()
                for conn_id, timestamp in self.last_refresh.items()
            }
        }

    async def save_to_disk(self) -> None:
        """Save cache to disk."""
        try:
            # Save metadata
            metadata_file = self.cache_dir / 'metadata.json'
            metadata = {
                'tables': {key: table.to_dict() for key, table in self.tables.items()},
                'columns': {key: column.to_dict() for key, column in self.columns.items()},
                'last_refresh': {
                    conn_id: timestamp.isoformat()
                    for conn_id, timestamp in self.last_refresh.items()
                }
            }

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Save vector database
            vector_file = self.cache_dir / 'vectors.pkl'
            with open(vector_file, 'wb') as f:
                pickle.dump({
                    'entries': self.vector_db.entries,
                    'id_to_idx': self.vector_db._id_to_idx
                }, f)

            logger.info(f"Saved metadata cache to {self.cache_dir}")

        except Exception as e:
            logger.error(f"Failed to save cache to disk: {e}")

    async def load_from_disk(self) -> bool:
        """
        Load cache from disk.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            metadata_file = self.cache_dir / 'metadata.json'
            vector_file = self.cache_dir / 'vectors.pkl'

            if not metadata_file.exists():
                logger.info("No cached metadata found on disk")
                return False

            # Load metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            self.tables = {
                key: TableMetadata.from_dict(data)
                for key, data in metadata.get('tables', {}).items()
            }

            self.columns = {
                key: ColumnMetadata.from_dict(data)
                for key, data in metadata.get('columns', {}).items()
            }

            self.last_refresh = {
                conn_id: datetime.fromisoformat(timestamp)
                for conn_id, timestamp in metadata.get('last_refresh', {}).items()
            }

            # Load vector database if available
            if vector_file.exists():
                with open(vector_file, 'rb') as f:
                    vector_data = pickle.load(f)
                    self.vector_db.entries = vector_data['entries']
                    self.vector_db._id_to_idx = vector_data['id_to_idx']

                    # Rebuild FAISS index
                    if self.vector_db.entries:
                        vectors = np.array([entry.vector for entry in self.vector_db.entries], dtype=np.float32)
                        self.vector_db.index.add(vectors)

            logger.info(
                f"Loaded metadata cache from disk: "
                f"{len(self.tables)} tables, {len(self.columns)} columns"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load cache from disk: {e}")
            return False
