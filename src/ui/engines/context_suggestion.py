"""Context-Aware Suggestion Engine.

This module provides intelligent autocomplete suggestions by gathering context
from the current environment and scoring suggestions based on relevance.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import asyncio
import logging
import os
import time
from pathlib import Path

try:
    from ...vector.autocomplete import IntelligentCompleter, CompletionCandidate
    from ...llm.embeddings import EmbeddingModel
except ImportError:
    from vector.autocomplete import IntelligentCompleter, CompletionCandidate
    from llm.embeddings import EmbeddingModel

logger = logging.getLogger(__name__)


@dataclass
class SuggestionContext:
    """Context information for suggestion generation.

    Attributes:
        current_directory: Current working directory
        command_history: Recent command history
        database_objects: Available database tables/columns
        cursor_position: Cursor position in current input
        statement_type: Detected SQL statement type (SELECT, INSERT, etc.)
        partial_command: Text before cursor
        query_text: Full query text
    """
    current_directory: str = ""
    command_history: List[str] = field(default_factory=list)
    database_objects: Dict[str, List[str]] = field(default_factory=dict)
    cursor_position: int = 0
    statement_type: Optional[str] = None
    partial_command: str = ""
    query_text: str = ""


class ContextAwareSuggestionEngine:
    """Engine for context-aware autocomplete suggestions.

    This engine integrates with IntelligentCompleter to provide smart suggestions
    based on the current context including directory, history, and database schema.

    Performance target: < 150ms response time

    Attributes:
        completer: IntelligentCompleter instance
        embedding_model: EmbeddingModel for query embeddings
        context_cache: Cache of gathered context
        cache_ttl: Time-to-live for cached context (seconds)
    """

    def __init__(
        self,
        completer: IntelligentCompleter,
        embedding_model: EmbeddingModel,
        cache_ttl: int = 300  # 5 minutes
    ):
        """Initialize ContextAwareSuggestionEngine.

        Args:
            completer: IntelligentCompleter instance
            embedding_model: EmbeddingModel for embeddings
            cache_ttl: Cache time-to-live in seconds
        """
        self.completer = completer
        self.embedding_model = embedding_model
        self.cache_ttl = cache_ttl
        self._context_cache: Dict[str, Tuple[Any, float]] = {}
        self._command_history: List[str] = []
        self._max_history = 100

    async def get_suggestions(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        max_results: int = 10
    ) -> List[CompletionCandidate]:
        """Get context-aware suggestions for a query.

        Args:
            query: User's query text
            context: Optional pre-gathered context
            max_results: Maximum number of suggestions

        Returns:
            List of scored CompletionCandidate objects
        """
        start_time = time.perf_counter()

        try:
            # Gather context if not provided
            if context is None:
                context = await self.gather_context(query)

            # Generate query embedding asynchronously
            query_vector = await asyncio.to_thread(
                self.embedding_model.encode,
                query
            )

            # Get completions from IntelligentCompleter
            candidates = await asyncio.to_thread(
                self.completer.get_completions,
                query,
                query_vector,
                context,
                max_results
            )

            # Re-score based on additional context
            scored_candidates = await self._rescore_with_context(
                candidates,
                query,
                context
            )

            # Sort by final score
            sorted_candidates = sorted(
                scored_candidates,
                key=lambda c: c.score,
                reverse=True
            )

            # Check performance
            duration_ms = (time.perf_counter() - start_time) * 1000
            if duration_ms > 150:
                logger.warning(
                    f"Suggestion generation took {duration_ms:.1f}ms (target: <150ms)"
                )
            else:
                logger.debug(f"Suggestions generated in {duration_ms:.1f}ms")

            return sorted_candidates[:max_results]

        except Exception as e:
            logger.error(f"Error generating suggestions: {e}", exc_info=True)
            return []

    async def gather_context(
        self,
        query: str = "",
        cursor_position: Optional[int] = None
    ) -> Dict[str, Any]:
        """Gather current context for suggestion generation.

        Args:
            query: Current query text
            cursor_position: Cursor position in query

        Returns:
            Context dictionary
        """
        if cursor_position is None:
            cursor_position = len(query)

        context = {
            'query': query,
            'cursor_position': cursor_position,
            'partial_command': query[:cursor_position],
        }

        # Add current directory (cached)
        context['current_directory'] = await self._get_cached_or_fetch(
            'current_directory',
            self._get_current_directory
        )

        # Add command history
        context['command_history'] = self._command_history[-20:]  # Last 20

        # Add database objects (cached)
        context['database_objects'] = await self._get_cached_or_fetch(
            'database_objects',
            self._get_database_objects
        )

        # Detect statement type
        context['statement_type'] = self._detect_statement_type(query)

        # Determine expected object type
        context['object_type'] = self._determine_object_type(
            query,
            cursor_position,
            context['statement_type']
        )

        return context

    def score_suggestion(
        self,
        query: str,
        candidate: CompletionCandidate,
        context: Dict[str, Any]
    ) -> float:
        """Score a suggestion based on query and context.

        Args:
            query: User's query
            candidate: Completion candidate
            context: Current context

        Returns:
            Relevance score (0.0 - 1.0)
        """
        base_score = candidate.score

        # Boost factor starts at 1.0
        boost = 1.0

        # 1. Prefix match boost
        if candidate.text.lower().startswith(query.lower()):
            boost *= 1.2

        # 2. Recent history boost
        if candidate.text in context.get('command_history', [])[-5:]:
            boost *= 1.15

        # 3. Context-appropriate type boost
        expected_type = context.get('object_type')
        if expected_type:
            candidate_type = candidate.metadata.get('type')
            if candidate_type == expected_type:
                boost *= 1.3

        # 4. Statement context boost
        statement_type = context.get('statement_type')
        if statement_type == 'SELECT' and candidate.source == 'column':
            boost *= 1.1
        elif statement_type in ('INSERT', 'UPDATE', 'DELETE') and candidate.source == 'table':
            boost *= 1.1

        # 5. Length penalty for very long suggestions
        if len(candidate.text) > 50:
            boost *= 0.9

        # Calculate final score (capped at 1.0)
        final_score = min(base_score * boost, 1.0)

        return final_score

    async def _rescore_with_context(
        self,
        candidates: List[CompletionCandidate],
        query: str,
        context: Dict[str, Any]
    ) -> List[CompletionCandidate]:
        """Re-score candidates with additional context.

        Args:
            candidates: Initial candidates
            query: User query
            context: Gathered context

        Returns:
            Re-scored candidates
        """
        rescored = []

        for candidate in candidates:
            new_score = self.score_suggestion(query, candidate, context)

            # Create new candidate with updated score
            rescored_candidate = CompletionCandidate(
                text=candidate.text,
                score=new_score,
                metadata=candidate.metadata,
                source=candidate.source
            )
            rescored.append(rescored_candidate)

        return rescored

    def _detect_statement_type(self, query: str) -> Optional[str]:
        """Detect SQL statement type from query.

        Args:
            query: Query text

        Returns:
            Statement type (SELECT, INSERT, etc.) or None
        """
        query_upper = query.strip().upper()

        for statement_type in ['SELECT', 'INSERT', 'UPDATE', 'DELETE',
                               'CREATE', 'DROP', 'ALTER', 'DESCRIBE']:
            if query_upper.startswith(statement_type):
                return statement_type

        return None

    def _determine_object_type(
        self,
        query: str,
        cursor_position: int,
        statement_type: Optional[str]
    ) -> Optional[str]:
        """Determine expected database object type at cursor.

        Args:
            query: Query text
            cursor_position: Cursor position
            statement_type: Detected statement type

        Returns:
            Expected object type ('table', 'column', etc.) or None
        """
        before_cursor = query[:cursor_position].upper()

        # Check last few words before cursor
        words = before_cursor.strip().split()
        if not words:
            return None

        last_word = words[-1] if words else ""
        prev_word = words[-2] if len(words) > 1 else ""

        # FROM clause -> expecting table
        if last_word == "FROM" or prev_word == "FROM":
            return 'table'

        # INTO clause -> expecting table
        if last_word == "INTO" or prev_word == "INTO":
            return 'table'

        # UPDATE statement -> expecting table
        if statement_type == "UPDATE" and prev_word == "UPDATE":
            return 'table'

        # SELECT clause -> expecting column
        if statement_type == "SELECT" and prev_word == "SELECT":
            return 'column'

        # WHERE clause -> expecting column
        if last_word == "WHERE" or prev_word == "WHERE":
            return 'column'

        # JOIN clause -> expecting table
        if "JOIN" in last_word or "JOIN" in prev_word:
            return 'table'

        return None

    async def _get_cached_or_fetch(
        self,
        key: str,
        fetch_func
    ) -> Any:
        """Get value from cache or fetch if expired.

        Args:
            key: Cache key
            fetch_func: Function to fetch value if not cached

        Returns:
            Cached or fetched value
        """
        now = time.time()

        if key in self._context_cache:
            value, timestamp = self._context_cache[key]
            if now - timestamp < self.cache_ttl:
                return value

        # Fetch new value
        value = await asyncio.to_thread(fetch_func)
        self._context_cache[key] = (value, now)

        return value

    def _get_current_directory(self) -> str:
        """Get current working directory.

        Returns:
            Current directory path
        """
        try:
            return os.getcwd()
        except Exception as e:
            logger.error(f"Error getting current directory: {e}")
            return "/"

    def _get_database_objects(self) -> Dict[str, List[str]]:
        """Get available database objects (tables, columns).

        This should be overridden to connect to actual database metadata.

        Returns:
            Dictionary of object types and their names
        """
        # TODO: Connect to actual database metadata
        # For now, return empty dict
        return {
            'tables': [],
            'columns': []
        }

    def add_to_history(self, command: str) -> None:
        """Add command to history.

        Args:
            command: Executed command
        """
        if command and command not in self._command_history[-5:]:
            self._command_history.append(command)
            if len(self._command_history) > self._max_history:
                self._command_history.pop(0)
            logger.debug(f"Added to history: {command}")

    def clear_cache(self, key: Optional[str] = None) -> None:
        """Clear context cache.

        Args:
            key: Specific key to clear, or None to clear all
        """
        if key:
            self._context_cache.pop(key, None)
        else:
            self._context_cache.clear()
        logger.debug(f"Cache cleared: {key or 'all'}")

    def set_database_objects(
        self,
        tables: List[str],
        columns: Dict[str, List[str]]
    ) -> None:
        """Manually set database objects (for testing or external updates).

        Args:
            tables: List of table names
            columns: Dictionary mapping table names to column lists
        """
        objects = {
            'tables': tables,
            'columns': columns
        }
        now = time.time()
        self._context_cache['database_objects'] = (objects, now)
        logger.debug(f"Database objects updated: {len(tables)} tables")
