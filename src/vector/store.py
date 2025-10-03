"""Vector database implementation with FAISS-like interface."""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VectorEntry:
    """Vector database entry."""
    id: str
    vector: np.ndarray
    metadata: Dict[str, Any]
    object_type: str


class MockFAISSIndex:
    """Mock FAISS index for testing without external dependencies."""

    def __init__(self, dimension: int):
        """Initialize mock index.

        Args:
            dimension: Vector dimension
        """
        self.dimension = dimension
        self.vectors: List[np.ndarray] = []
        self.ntotal = 0

    def add(self, vectors: np.ndarray) -> None:
        """Add vectors to index.

        Args:
            vectors: Array of vectors to add
        """
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        for vec in vectors:
            self.vectors.append(vec.copy())
        self.ntotal = len(self.vectors)

    def search(self, query: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Search for nearest neighbors.

        Args:
            query: Query vector
            k: Number of neighbors

        Returns:
            Tuple of (distances, indices)
        """
        if query.ndim == 1:
            query = query.reshape(1, -1)

        if not self.vectors:
            return np.array([[]]), np.array([[]])

        # Calculate cosine similarity
        similarities = []
        for vec in self.vectors:
            dot_product = np.dot(query[0], vec)
            norm_product = np.linalg.norm(query[0]) * np.linalg.norm(vec)
            similarity = dot_product / (norm_product + 1e-8)
            similarities.append(similarity)

        similarities = np.array(similarities)

        # Get top k indices
        k = min(k, len(similarities))
        top_indices = np.argsort(similarities)[-k:][::-1]
        top_distances = 1 - similarities[top_indices]  # Convert to distance

        return top_distances.reshape(1, -1), top_indices.reshape(1, -1)


class VectorDatabase:
    """Vector database for semantic search and indexing."""

    def __init__(self, dimension: int = 384):
        """Initialize vector database.

        Args:
            dimension: Vector dimension for embeddings
        """
        self.dimension = dimension
        self.index = MockFAISSIndex(dimension)
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
        self.index.add(vector)

        logger.debug(f"Added {object_type} object: {object_id}")

    def search_similar(
        self,
        query_vector: np.ndarray,
        k: int = 5,
        object_type: Optional[str] = None,
        threshold: float = 0.5
    ) -> List[Tuple[VectorEntry, float]]:
        """Search for similar objects.

        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            object_type: Filter by object type
            threshold: Similarity threshold (0-1)

        Returns:
            List of (entry, distance) tuples
        """
        if not self.entries:
            return []

        distances, indices = self.index.search(query_vector, k * 2)  # Get more for filtering

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= len(self.entries):
                continue

            entry = self.entries[idx]

            # Apply object type filter
            if object_type and entry.object_type != object_type:
                continue

            # Apply threshold (distance is 1 - similarity)
            similarity = 1 - dist
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
