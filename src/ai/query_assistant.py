"""
AI-Powered Query Assistant

Provides intelligent SQL generation, explanation, and optimization using Claude API.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Types of query intents"""
    GENERATE_SQL = "generate_sql"
    EXPLAIN_SQL = "explain_sql"
    OPTIMIZE_SQL = "optimize_sql"
    FIX_SQL = "fix_sql"
    SCHEMA_ANALYSIS = "schema_analysis"
    COMPLEX_QUERY = "complex_query"


@dataclass
class QueryContext:
    """Context for AI query processing"""
    database_type: str = "sqlite"
    schema_info: Dict[str, Any] = field(default_factory=dict)
    table_names: List[str] = field(default_factory=list)
    recent_queries: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    performance_history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for API calls"""
        return {
            'database_type': self.database_type,
            'schema_info': self.schema_info,
            'table_names': self.table_names,
            'recent_queries': self.recent_queries[-5:],  # Last 5 queries
            'user_preferences': self.user_preferences
        }


@dataclass
class QueryResponse:
    """Response from AI query assistant"""
    success: bool
    sql_query: Optional[str] = None
    explanation: Optional[str] = None
    optimization_suggestions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_response: Optional[str] = None


class QueryAssistant:
    """
    AI-powered query assistant using Anthropic Claude API

    Features:
    - Natural language to complex SQL conversion
    - Query explanation in plain English
    - Performance optimization suggestions
    - Schema understanding from metadata
    - Query correction and validation
    - Context-aware suggestions
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        """
        Initialize Query Assistant

        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            logger.warning("No Anthropic API key provided. AI features will be limited.")

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Import Anthropic client if available
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key) if self.api_key else None
            self.available = True
        except ImportError:
            logger.error("anthropic package not installed. Install with: pip install anthropic")
            self.client = None
            self.available = False

        # Import prompt templates
        from src.ai.prompt_templates import PromptTemplates
        self.prompts = PromptTemplates()

    def generate_sql(
        self,
        natural_query: str,
        context: QueryContext,
        stream: bool = False
    ) -> QueryResponse:
        """
        Generate SQL from natural language query

        Args:
            natural_query: Natural language description of desired query
            context: Query context with schema and history
            stream: Enable streaming responses

        Returns:
            QueryResponse with generated SQL and explanation
        """
        if not self.available or not self.client:
            return self._fallback_generate_sql(natural_query, context)

        try:
            # Build prompt with context
            prompt = self.prompts.generate_sql_prompt(natural_query, context)

            # Call Claude API
            if stream:
                return self._generate_sql_stream(prompt)
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )

                # Parse response
                return self._parse_sql_response(response.content[0].text, natural_query)

        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return QueryResponse(
                success=False,
                warnings=[f"API error: {str(e)}"]
            )

    def explain_query(
        self,
        sql_query: str,
        context: QueryContext,
        detail_level: str = "medium"
    ) -> QueryResponse:
        """
        Explain SQL query in plain English

        Args:
            sql_query: SQL query to explain
            context: Query context
            detail_level: Level of detail (simple, medium, detailed)

        Returns:
            QueryResponse with explanation
        """
        if not self.available or not self.client:
            return self._fallback_explain_query(sql_query)

        try:
            prompt = self.prompts.explain_query_prompt(sql_query, context, detail_level)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.5,  # Lower temperature for explanations
                messages=[{"role": "user", "content": prompt}]
            )

            explanation = response.content[0].text

            return QueryResponse(
                success=True,
                sql_query=sql_query,
                explanation=explanation,
                confidence=0.9,
                metadata={'detail_level': detail_level}
            )

        except Exception as e:
            logger.error(f"Error explaining query: {e}")
            return QueryResponse(
                success=False,
                warnings=[f"API error: {str(e)}"]
            )

    def optimize_query(
        self,
        sql_query: str,
        context: QueryContext,
        performance_data: Optional[Dict] = None
    ) -> QueryResponse:
        """
        Suggest optimizations for SQL query

        Args:
            sql_query: SQL query to optimize
            context: Query context with schema
            performance_data: Execution time, rows affected, etc.

        Returns:
            QueryResponse with optimization suggestions
        """
        if not self.available or not self.client:
            return self._fallback_optimize_query(sql_query)

        try:
            prompt = self.prompts.optimize_query_prompt(sql_query, context, performance_data)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.6,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse optimization suggestions
            result = self._parse_optimization_response(response.content[0].text, sql_query)
            return result

        except Exception as e:
            logger.error(f"Error optimizing query: {e}")
            return QueryResponse(
                success=False,
                warnings=[f"API error: {str(e)}"]
            )

    def fix_query(
        self,
        sql_query: str,
        error_message: str,
        context: QueryContext
    ) -> QueryResponse:
        """
        Fix SQL query based on error message

        Args:
            sql_query: Failed SQL query
            error_message: Error message from database
            context: Query context

        Returns:
            QueryResponse with corrected SQL
        """
        if not self.available or not self.client:
            return QueryResponse(
                success=False,
                warnings=["AI query fixing not available without API key"]
            )

        try:
            prompt = self.prompts.fix_query_prompt(sql_query, error_message, context)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )

            return self._parse_sql_response(response.content[0].text, sql_query)

        except Exception as e:
            logger.error(f"Error fixing query: {e}")
            return QueryResponse(
                success=False,
                warnings=[f"API error: {str(e)}"]
            )

    def analyze_schema(
        self,
        schema_info: Dict[str, Any],
        analysis_type: str = "general"
    ) -> QueryResponse:
        """
        Analyze database schema and provide insights

        Args:
            schema_info: Schema metadata
            analysis_type: Type of analysis (general, relationships, optimization)

        Returns:
            QueryResponse with schema analysis
        """
        if not self.available or not self.client:
            return QueryResponse(
                success=False,
                warnings=["AI schema analysis not available without API key"]
            )

        try:
            prompt = self.prompts.analyze_schema_prompt(schema_info, analysis_type)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.6,
                messages=[{"role": "user", "content": prompt}]
            )

            return QueryResponse(
                success=True,
                explanation=response.content[0].text,
                metadata={'analysis_type': analysis_type}
            )

        except Exception as e:
            logger.error(f"Error analyzing schema: {e}")
            return QueryResponse(
                success=False,
                warnings=[f"API error: {str(e)}"]
            )

    # Helper methods

    def _parse_sql_response(self, response_text: str, original_query: str) -> QueryResponse:
        """Parse Claude's response containing SQL"""
        try:
            # Try to extract JSON if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                data = json.loads(json_str)

                return QueryResponse(
                    success=True,
                    sql_query=data.get('sql'),
                    explanation=data.get('explanation'),
                    optimization_suggestions=data.get('optimizations', []),
                    warnings=data.get('warnings', []),
                    confidence=data.get('confidence', 0.8),
                    raw_response=response_text
                )

            # Extract SQL from code blocks
            if "```sql" in response_text:
                sql_start = response_text.find("```sql") + 6
                sql_end = response_text.find("```", sql_start)
                sql = response_text[sql_start:sql_end].strip()

                # Extract explanation (text after SQL block)
                explanation = response_text[sql_end+3:].strip()

                return QueryResponse(
                    success=True,
                    sql_query=sql,
                    explanation=explanation if explanation else None,
                    confidence=0.85,
                    raw_response=response_text
                )

            # Fallback: entire response is explanation
            return QueryResponse(
                success=True,
                explanation=response_text,
                confidence=0.7,
                raw_response=response_text
            )

        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return QueryResponse(
                success=False,
                warnings=[f"Failed to parse response: {str(e)}"],
                raw_response=response_text
            )

    def _parse_optimization_response(self, response_text: str, original_sql: str) -> QueryResponse:
        """Parse optimization suggestions from response"""
        try:
            suggestions = []
            optimized_sql = None

            # Extract optimized SQL if present
            if "```sql" in response_text:
                sql_start = response_text.find("```sql") + 6
                sql_end = response_text.find("```", sql_start)
                optimized_sql = response_text[sql_start:sql_end].strip()

            # Extract suggestions (look for numbered lists or bullet points)
            lines = response_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                    # Remove numbering/bullets
                    suggestion = line.lstrip('0123456789.-* ')
                    if len(suggestion) > 10:  # Avoid empty suggestions
                        suggestions.append(suggestion)

            return QueryResponse(
                success=True,
                sql_query=optimized_sql or original_sql,
                optimization_suggestions=suggestions,
                explanation=response_text,
                confidence=0.85,
                raw_response=response_text
            )

        except Exception as e:
            logger.error(f"Error parsing optimization response: {e}")
            return QueryResponse(
                success=False,
                warnings=[f"Failed to parse response: {str(e)}"],
                raw_response=response_text
            )

    def _generate_sql_stream(self, prompt: str) -> QueryResponse:
        """Generate SQL with streaming response"""
        try:
            accumulated_text = ""

            with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    accumulated_text += text
                    # Could yield chunks here for real-time display

            return self._parse_sql_response(accumulated_text, "")

        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            return QueryResponse(
                success=False,
                warnings=[f"Streaming error: {str(e)}"]
            )

    # Fallback methods when API is not available

    def _fallback_generate_sql(self, natural_query: str, context: QueryContext) -> QueryResponse:
        """Fallback SQL generation using pattern matching"""
        # Use existing NLP to SQL converter as fallback
        from src.database.nlp_to_sql import NLPToSQL
        converter = NLPToSQL()
        result = converter.convert(natural_query)

        return QueryResponse(
            success=bool(result.get('sql')),
            sql_query=result.get('sql'),
            explanation=f"Pattern-based conversion (confidence: {result.get('confidence', 0.5)})",
            confidence=result.get('confidence', 0.5),
            warnings=["Using fallback pattern matching. For better results, set ANTHROPIC_API_KEY"]
        )

    def _fallback_explain_query(self, sql_query: str) -> QueryResponse:
        """Fallback query explanation"""
        # Simple pattern-based explanation
        explanation = f"This query: {sql_query[:100]}..."
        if "SELECT" in sql_query.upper():
            explanation += " retrieves data from the database."
        elif "INSERT" in sql_query.upper():
            explanation += " inserts new records into the database."
        elif "UPDATE" in sql_query.upper():
            explanation += " updates existing records in the database."
        elif "DELETE" in sql_query.upper():
            explanation += " deletes records from the database."

        return QueryResponse(
            success=True,
            sql_query=sql_query,
            explanation=explanation,
            confidence=0.5,
            warnings=["Using basic explanation. For detailed AI explanations, set ANTHROPIC_API_KEY"]
        )

    def _fallback_optimize_query(self, sql_query: str) -> QueryResponse:
        """Fallback query optimization"""
        suggestions = [
            "Consider adding indexes on frequently queried columns",
            "Use parameterized queries to prevent SQL injection",
            "Avoid SELECT * when only specific columns are needed",
            "Use appropriate WHERE clauses to limit result sets"
        ]

        return QueryResponse(
            success=True,
            sql_query=sql_query,
            optimization_suggestions=suggestions,
            explanation="Generic optimization suggestions",
            confidence=0.5,
            warnings=["Using generic suggestions. For AI-powered optimization, set ANTHROPIC_API_KEY"]
        )
