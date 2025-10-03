"""Intelligent autocomplete system using vector similarity."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import logging

from .store import VectorDatabase

logger = logging.getLogger(__name__)


@dataclass
class CompletionCandidate:
    """Autocomplete candidate."""
    text: str
    score: float
    metadata: Dict[str, Any]
    source: str  # 'vector', 'pattern', 'syntax'


class IntelligentCompleter:
    """Intelligent autocomplete using vector similarity and patterns."""

    def __init__(self, vector_db: VectorDatabase):
        """Initialize completer.

        Args:
            vector_db: Vector database instance
        """
        self.vector_db = vector_db
        self.pattern_cache: Dict[str, List[str]] = {}
        self.completion_history: List[str] = []
        self.max_history = 100

    def add_to_history(self, completion: str) -> None:
        """Add completion to history.

        Args:
            completion: Completed text
        """
        self.completion_history.append(completion)
        if len(self.completion_history) > self.max_history:
            self.completion_history.pop(0)

    def get_completions(
        self,
        query: str,
        query_vector: np.ndarray,
        context: Optional[Dict[str, Any]] = None,
        max_results: int = 10
    ) -> List[CompletionCandidate]:
        """Get intelligent completions for a query.

        Args:
            query: Query text
            query_vector: Query embedding vector
            context: Additional context (cursor position, statement type, etc.)
            max_results: Maximum number of results

        Returns:
            List of completion candidates
        """
        context = context or {}
        candidates = []

        # 1. Vector-based completions
        vector_candidates = self._get_vector_completions(
            query_vector,
            context,
            max_results
        )
        candidates.extend(vector_candidates)

        # 2. Pattern-based completions
        pattern_candidates = self._get_pattern_completions(query, context)
        candidates.extend(pattern_candidates)

        # 3. Syntax-based completions
        syntax_candidates = self._get_syntax_completions(query, context)
        candidates.extend(syntax_candidates)

        # 4. History-based completions
        history_candidates = self._get_history_completions(query)
        candidates.extend(history_candidates)

        # Deduplicate and sort by score
        unique_candidates = self._deduplicate_candidates(candidates)
        sorted_candidates = sorted(
            unique_candidates,
            key=lambda c: c.score,
            reverse=True
        )

        return sorted_candidates[:max_results]

    def _get_vector_completions(
        self,
        query_vector: np.ndarray,
        context: Dict[str, Any],
        max_results: int
    ) -> List[CompletionCandidate]:
        """Get completions from vector similarity.

        Args:
            query_vector: Query embedding
            context: Query context
            max_results: Maximum results

        Returns:
            List of candidates
        """
        candidates = []

        # Determine object type from context
        object_type = context.get('object_type')

        # Search vector database
        results = self.vector_db.search_similar(
            query_vector,
            k=max_results,
            object_type=object_type,
            threshold=0.3
        )

        for entry, distance in results:
            score = 1 - distance  # Convert distance to similarity

            # Generate completion text based on object type
            if entry.object_type == 'table':
                text = entry.metadata.get('name', '')
            elif entry.object_type == 'column':
                table = entry.metadata.get('table', '')
                name = entry.metadata.get('name', '')
                text = f"{table}.{name}"
            else:
                text = entry.id

            candidates.append(CompletionCandidate(
                text=text,
                score=score * 0.9,  # Weight vector completions
                metadata=entry.metadata,
                source='vector'
            ))

        return candidates

    def _get_pattern_completions(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> List[CompletionCandidate]:
        """Get completions from SQL patterns.

        Args:
            query: Query text
            context: Query context

        Returns:
            List of candidates
        """
        candidates = []
        query_lower = query.lower().strip()

        # SQL keyword patterns
        if query_lower.startswith('sel'):
            candidates.append(CompletionCandidate(
                text='SELECT',
                score=0.95,
                metadata={'type': 'keyword'},
                source='pattern'
            ))
        elif query_lower.startswith('fr'):
            candidates.append(CompletionCandidate(
                text='FROM',
                score=0.95,
                metadata={'type': 'keyword'},
                source='pattern'
            ))
        elif query_lower.startswith('wh'):
            candidates.append(CompletionCandidate(
                text='WHERE',
                score=0.95,
                metadata={'type': 'keyword'},
                source='pattern'
            ))
        elif query_lower.startswith('join'):
            for join_type in ['INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN']:
                candidates.append(CompletionCandidate(
                    text=join_type,
                    score=0.9,
                    metadata={'type': 'keyword'},
                    source='pattern'
                ))

        # Function patterns
        if query_lower.endswith('('):
            prev_word = query_lower.split()[-1][:-1] if query_lower.split() else ''
            if prev_word in ['count', 'sum', 'avg', 'max', 'min']:
                candidates.append(CompletionCandidate(
                    text='*)',
                    score=0.85,
                    metadata={'type': 'function'},
                    source='pattern'
                ))

        return candidates

    def _get_syntax_completions(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> List[CompletionCandidate]:
        """Get syntax-based completions.

        Args:
            query: Query text
            context: Query context

        Returns:
            List of candidates
        """
        candidates = []

        # Check for unclosed parentheses
        open_parens = query.count('(')
        close_parens = query.count(')')
        if open_parens > close_parens:
            candidates.append(CompletionCandidate(
                text=')',
                score=0.8,
                metadata={'type': 'syntax'},
                source='syntax'
            ))

        # Check for incomplete quotes
        if query.count("'") % 2 == 1:
            candidates.append(CompletionCandidate(
                text="'",
                score=0.85,
                metadata={'type': 'syntax'},
                source='syntax'
            ))

        return candidates

    def _get_history_completions(self, query: str) -> List[CompletionCandidate]:
        """Get completions from history.

        Args:
            query: Query text

        Returns:
            List of candidates
        """
        candidates = []
        query_lower = query.lower()

        for historical in self.completion_history[-20:]:  # Last 20
            if historical.lower().startswith(query_lower) and historical != query:
                # Calculate score based on recency and match quality
                recency_score = (
                    self.completion_history.index(historical) /
                    len(self.completion_history)
                )
                match_score = len(query) / len(historical) if historical else 0
                score = (recency_score * 0.3 + match_score * 0.7) * 0.6

                candidates.append(CompletionCandidate(
                    text=historical,
                    score=score,
                    metadata={'type': 'history'},
                    source='history'
                ))

        return candidates

    def _deduplicate_candidates(
        self,
        candidates: List[CompletionCandidate]
    ) -> List[CompletionCandidate]:
        """Remove duplicate candidates, keeping highest score.

        Args:
            candidates: List of candidates

        Returns:
            Deduplicated list
        """
        unique: Dict[str, CompletionCandidate] = {}

        for candidate in candidates:
            text = candidate.text
            if text not in unique or candidate.score > unique[text].score:
                unique[text] = candidate

        return list(unique.values())

    def register_pattern(self, pattern: str, completions: List[str]) -> None:
        """Register a completion pattern.

        Args:
            pattern: Pattern to match
            completions: List of completions for this pattern
        """
        self.pattern_cache[pattern] = completions
        logger.debug(f"Registered pattern: {pattern} with {len(completions)} completions")

    def get_context_aware_completions(
        self,
        query: str,
        query_vector: np.ndarray,
        statement_type: str,
        cursor_position: int
    ) -> List[CompletionCandidate]:
        """Get context-aware completions based on statement analysis.

        Args:
            query: Query text
            query_vector: Query embedding
            statement_type: Type of SQL statement (SELECT, INSERT, etc.)
            cursor_position: Cursor position in query

        Returns:
            List of completion candidates
        """
        context = {
            'statement_type': statement_type,
            'cursor_position': cursor_position,
            'query_length': len(query)
        }

        # Determine what's expected at cursor position
        before_cursor = query[:cursor_position].strip()

        if statement_type == 'SELECT':
            if before_cursor.lower().endswith('from'):
                context['object_type'] = 'table'
            elif before_cursor.lower().endswith('select'):
                context['object_type'] = 'column'
        elif statement_type == 'INSERT':
            if 'into' in before_cursor.lower():
                context['object_type'] = 'table'

        return self.get_completions(query, query_vector, context)
