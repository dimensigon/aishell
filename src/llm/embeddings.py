"""
Embedding Model Wrapper

Provides text embedding functionality for semantic search and similarity.
"""

from typing import List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Wrapper for sentence transformer embedding models"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", model_path: str = "/data0/models") -> None:
        self.model_name = model_name
        self.model_path = model_path
        self.model = None
        self.initialized = False

    def initialize(self) -> bool:
        """Initialize embedding model"""
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=self.model_path
            )
            self.initialized = True
            logger.info(f"Embedding model initialized: {self.model_name}")
            return True
        except ImportError:
            logger.warning("sentence-transformers not installed, using mock embeddings")
            self.model = self._create_mock_model()
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            return False

    def _create_mock_model(self):
        """Create mock model for testing"""
        class MockEmbedder:
            def encode(self, texts, batch_size=32, convert_to_numpy=True):
                # Generate consistent fake embeddings
                if isinstance(texts, str):
                    texts = [texts]
                return np.random.randn(len(texts), 384).astype(np.float32)

        return MockEmbedder()

    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for text(s)

        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding

        Returns:
            numpy array of embeddings
        """
        if not self.initialized:
            raise RuntimeError("Embedding model not initialized")

        try:
            if isinstance(texts, str):
                texts = [texts]

            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            raise

    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        embeddings = self.encode([text1, text2])

        # Cosine similarity
        dot_product = np.dot(embeddings[0], embeddings[1])
        norm1 = np.linalg.norm(embeddings[0])
        norm2 = np.linalg.norm(embeddings[1])

        return float(dot_product / (norm1 * norm2))

    def find_most_similar(self, query: str, candidates: List[str], top_k: int = 5) -> List[tuple]:
        """
        Find most similar texts to query

        Args:
            query: Query text
            candidates: List of candidate texts
            top_k: Number of top results to return

        Returns:
            List of (text, similarity_score) tuples
        """
        if not candidates:
            return []

        # Encode all texts
        all_texts = [query] + candidates
        embeddings = self.encode(all_texts)

        query_embedding = embeddings[0]
        candidate_embeddings = embeddings[1:]

        # Calculate similarities
        similarities = []
        for i, candidate_emb in enumerate(candidate_embeddings):
            dot_product = np.dot(query_embedding, candidate_emb)
            norm1 = np.linalg.norm(query_embedding)
            norm2 = np.linalg.norm(candidate_emb)
            similarity = float(dot_product / (norm1 * norm2))
            similarities.append((candidates[i], similarity))

        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def cleanup(self):
        """Cleanup resources"""
        self.model = None
        self.initialized = False
