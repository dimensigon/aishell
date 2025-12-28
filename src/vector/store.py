"""Vector database implementation with FAISS backend.

FAISS (Facebook AI Similarity Search) is required for vector operations.
Install with: pip install faiss-cpu==1.12.0
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import faiss

logger = logging.getLogger(__name__)


@dataclass
class VectorEntry:
    """Vector database entry."""
    id: str
    vector: np.ndarray
    metadata: Dict[str, Any]
    object_type: str


class VectorDatabase:
    """Vector database for semantic search and indexing.

    Requires FAISS (Facebook AI Similarity Search) library.
    Uses FAISS IndexFlatL2 for exact L2 distance search.
    """

    def __init__(self, dimension: int = 384) -> None:
        """Initialize vector database with FAISS backend.

        Args:
            dimension: Vector dimension for embeddings (default: 384)

        Raises:
            ImportError: If FAISS is not installed
        """
        self.dimension = dimension

        # Initialize FAISS index with L2 distance (IndexFlatL2)
        # FAISS 1.12.0 API is compatible with 1.7.4
        self.index = faiss.IndexFlatL2(dimension)
        logger.info(f"Initialized FAISS IndexFlatL2 with dimension {dimension}")

        self.entries: List[VectorEntry] = []
        self._id_to_idx: Dict[str, int] = {}

    def add_object(
        self,
        object_id: str,
        vector: np.ndarray,
        object_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a system object to the vector database.

        Args:
            object_id: Unique identifier
            vector: Embedding vector
            object_type: Type of object (table, column, index, etc.)
            metadata: Additional metadata
        """
        if vector.shape[0] != self.dimension:
            raise ValueError(
                f"Vector dimension {vector.shape[0]} doesn't match "
                f"index dimension {self.dimension}"
            )

        entry = VectorEntry(
            id=object_id,
            vector=vector.copy(),
            metadata=metadata or {},
            object_type=object_type
        )

        idx = len(self.entries)
        self.entries.append(entry)
        self._id_to_idx[object_id] = idx

        # Add to FAISS index - requires float32 2D array (n_vectors, dimension)
        vec_2d = vector.reshape(1, -1).astype(np.float32)
        self.index.add(vec_2d)

        logger.debug(f"Added {object_type} object: {object_id}")

    def search_similar(
        self,
        query_vector: np.ndarray,
        k: int = 5,
        object_type: Optional[str] = None,
        threshold: float = 0.5
    ) -> List[Tuple[VectorEntry, float]]:
        """Search for similar objects using FAISS L2 distance.

        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            object_type: Filter by object type
            threshold: Similarity threshold (0-1, higher is more similar)

        Returns:
            List of (entry, L2_distance) tuples, sorted by distance (ascending)

        Note:
            Uses L2 distance where smaller values indicate higher similarity.
            For normalized vectors, L2 distance ranges from 0 to 2.
            Threshold is converted to similarity metric: similarity = 1.0 / (1.0 + distance)
        """
        if not self.entries:
            return []

        # Prepare query for FAISS - requires float32 2D array
        query_2d = query_vector.reshape(1, -1).astype(np.float32)

        # Get more results than needed to allow for filtering
        distances, indices = self.index.search(query_2d, k * 2)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= len(self.entries):
                continue

            entry = self.entries[idx]

            # Apply object type filter
            if object_type and entry.object_type != object_type:
                continue

            # Apply threshold using L2 distance
            # Convert L2 distance to similarity-like metric for threshold comparison
            # For normalized vectors, L2 distance ranges from 0 to 2
            similarity = 1.0 / (1.0 + dist)
            if similarity < threshold:
                continue

            results.append((entry, float(dist)))

            if len(results) >= k:
                break

        return results

    def get_by_id(self, object_id: str) -> Optional[VectorEntry]:
        """Get entry by ID.

        Args:
            object_id: Object identifier

        Returns:
            Vector entry or None
        """
        idx = self._id_to_idx.get(object_id)
        if idx is not None:
            return self.entries[idx]
        return None

    def delete_by_id(self, object_id: str) -> bool:
        """Delete entry by ID.

        Args:
            object_id: Object identifier

        Returns:
            True if deleted, False if not found
        """
        idx = self._id_to_idx.get(object_id)
        if idx is None:
            return False

        # Mark as deleted in metadata
        self.entries[idx].metadata['_deleted'] = True
        logger.debug(f"Deleted object: {object_id}")
        return True

    def index_database_objects(
        self,
        tables: List[Dict[str, Any]],
        embedding_func: callable
    ) -> None:
        """Index database objects with embeddings.

        Args:
            tables: List of table definitions
            embedding_func: Function to generate embeddings from text
        """
        for table in tables:
            table_name = table.get('name', '')
            table_desc = table.get('description', '')

            # Index table
            table_text = f"Table: {table_name}. {table_desc}"
            table_vector = embedding_func(table_text)
            self.add_object(
                object_id=f"table:{table_name}",
                vector=table_vector,
                object_type='table',
                metadata={
                    'name': table_name,
                    'description': table_desc,
                    'schema': table.get('schema', 'public')
                }
            )

            # Index columns
            for column in table.get('columns', []):
                col_name = column.get('name', '')
                col_type = column.get('type', '')
                col_desc = column.get('description', '')

                col_text = (
                    f"Column: {table_name}.{col_name}. "
                    f"Type: {col_type}. {col_desc}"
                )
                col_vector = embedding_func(col_text)
                self.add_object(
                    object_id=f"column:{table_name}.{col_name}",
                    vector=col_vector,
                    object_type='column',
                    metadata={
                        'table': table_name,
                        'name': col_name,
                        'type': col_type,
                        'description': col_desc
                    }
                )

        logger.info(f"Indexed {len(self.entries)} database objects")

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Statistics dictionary
        """
        type_counts = {}
        for entry in self.entries:
            if not entry.metadata.get('_deleted'):
                type_counts[entry.object_type] = type_counts.get(entry.object_type, 0) + 1

        return {
            'total_entries': len(self.entries),
            'dimension': self.dimension,
            'type_counts': type_counts,
            'index_size': self.index.ntotal
        }
