"""
Research Agent - Gathers and analyzes information

Specialized agent for research tasks, information gathering,
web searches, and data analysis.
"""

import asyncio
import logging
from typing import Any, Dict, List

from src.agents.base import BaseAgent, AgentCapability, TaskContext

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Agent specialized in research and information gathering

    Features:
    - Web search and content extraction
    - Document analysis
    - Information synthesis
    - Citation tracking
    - Knowledge base queries
    """

    def __init__(self, agent_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(agent_id=agent_id, config=config, **kwargs)
        self.research_results: List[Dict[str, Any]] = []
        self.max_results = config.get("max_results", 10)
        self.sources_checked: List[str] = []

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create research plan

        Args:
            task: Task context with research query

        Returns:
            List of planned research steps
        """
        query = task.input_data.get("query", "")
        research_type = task.input_data.get("type", "general")
        depth = task.input_data.get("depth", "standard")

        if not query:
            raise ValueError("No research query specified")

        plan = []

        # Step 1: Search for information
        plan.append(
            {
                "tool": "search_information",
                "params": {
                    "query": query,
                    "max_results": self.max_results,
                    "sources": task.input_data.get("sources", ["documentation", "web"]),
                },
                "rationale": f"Search for information about: {query}",
            }
        )

        # Step 2: Analyze results (if deep research)
        if depth == "deep":
            plan.append(
                {
                    "tool": "analyze_sources",
                    "params": {"criteria": task.input_data.get("criteria", [])},
                    "rationale": "Analyze and validate found sources",
                }
            )

        # Step 3: Synthesize findings
        plan.append(
            {
                "tool": "synthesize_findings",
                "params": {"format": task.input_data.get("output_format", "summary")},
                "rationale": "Synthesize research findings into coherent output",
            }
        )

        return plan

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a research step

        Args:
            step: Step definition

        Returns:
            Step execution result
        """
        tool = step["tool"]
        params = step["params"]

        if tool == "search_information":
            return await self._search_information(params)
        elif tool == "analyze_sources":
            return await self._analyze_sources(params)
        elif tool == "synthesize_findings":
            return await self._synthesize_findings(params)
        else:
            raise ValueError(f"Unknown tool: {tool}")

    async def _search_information(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for information based on query

        Args:
            params: Search parameters

        Returns:
            Search results
        """
        query = params.get("query", "")
        max_results = params.get("max_results", self.max_results)
        sources = params.get("sources", ["documentation"])

        results = []

        # Search in documentation
        if "documentation" in sources:
            doc_results = await self._search_documentation(query, max_results)
            results.extend(doc_results)

        # Web search (if available)
        if "web" in sources and self.llm_manager:
            web_results = await self._search_web(query, max_results)
            results.extend(web_results)

        # Store results for later analysis
        self.research_results = results[:max_results]
        self.sources_checked = sources

        return {
            "success": True,
            "results_count": len(self.research_results),
            "sources": sources,
            "results": self.research_results
        }

    async def _search_documentation(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search local documentation"""
        # Simulate documentation search
        return [
            {
                "source": "local_docs",
                "title": f"Documentation: {query}",
                "content": f"Information about {query} from local documentation",
                "relevance": 0.9
            }
        ]

    async def _search_web(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search web using LLM"""
        # Simulate web search
        return [
            {
                "source": "web",
                "title": f"Web result: {query}",
                "content": f"Web information about {query}",
                "relevance": 0.8
            }
        ]

    async def _analyze_sources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze and validate sources

        Args:
            params: Analysis parameters

        Returns:
            Analysis results
        """
        criteria = params.get("criteria", [])

        analyzed_results = []
        for result in self.research_results:
            analysis = {
                "source": result["source"],
                "title": result["title"],
                "relevance": result.get("relevance", 0),
                "validation": "validated" if result.get("relevance", 0) > 0.7 else "needs_review",
                "criteria_met": []
            }

            # Check against criteria
            for criterion in criteria:
                if criterion.lower() in result.get("content", "").lower():
                    analysis["criteria_met"].append(criterion)

            analyzed_results.append(analysis)

        return {
            "success": True,
            "analyzed_count": len(analyzed_results),
            "results": analyzed_results
        }

    async def _synthesize_findings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize research findings

        Args:
            params: Synthesis parameters

        Returns:
            Synthesized output
        """
        output_format = params.get("format", "summary")

        if output_format == "summary":
            summary = self._create_summary()
        elif output_format == "detailed":
            summary = self._create_detailed_report()
        elif output_format == "json":
            summary = {"findings": self.research_results}
        else:
            summary = str(self.research_results)

        return {
            "success": True,
            "format": output_format,
            "synthesis": summary,
            "sources_count": len(self.research_results),
            "sources_checked": self.sources_checked
        }

    def _create_summary(self) -> str:
        """Create a summary of findings"""
        if not self.research_results:
            return "No research results found."

        summary_lines = [f"Research Summary ({len(self.research_results)} results):"]
        for i, result in enumerate(self.research_results[:3], 1):
            summary_lines.append(f"{i}. {result.get('title', 'Untitled')}")

        return "\n".join(summary_lines)

    def _create_detailed_report(self) -> Dict[str, Any]:
        """Create detailed research report"""
        return {
            "total_results": len(self.research_results),
            "sources": self.sources_checked,
            "findings": [
                {
                    "title": r.get("title"),
                    "source": r.get("source"),
                    "content": r.get("content"),
                    "relevance": r.get("relevance", 0)
                }
                for r in self.research_results
            ]
        }

    async def _search_information(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for information"""
        query = params["query"]
        max_results = params.get("max_results", 10)
        sources = params.get("sources", ["documentation", "web"])

        logger.info(f"Searching for: {query}")

        results = []

        # Simulate search (in real implementation, use actual search APIs)
        for source in sources:
            self.sources_checked.append(source)

            # Mock search results
            for i in range(min(3, max_results)):
                results.append(
                    {
                        "source": source,
                        "title": f"Result {i+1} from {source} for '{query}'",
                        "content": f"Information about {query} from {source}...",
                        "relevance": 0.9 - (i * 0.1),
                        "url": f"https://example.com/{source}/{i}",
                    }
                )

        self.research_results.extend(results)

        return {
            "query": query,
            "results_found": len(results),
            "sources_checked": sources,
            "results": results[:max_results],
        }

    async def _analyze_sources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze source quality and reliability"""
        criteria = params.get("criteria", [])

        logger.info("Analyzing sources...")

        analyzed = []
        for result in self.research_results:
            analysis = {
                "source": result["source"],
                "title": result["title"],
                "quality_score": result.get("relevance", 0.8),
                "credibility": "high" if result.get("relevance", 0) > 0.7 else "medium",
                "meets_criteria": True,  # Simplified
            }
            analyzed.append(analysis)

        return {"analyzed_sources": len(analyzed), "sources": analyzed}

    async def _synthesize_findings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize research findings"""
        output_format = params.get("format", "summary")

        logger.info("Synthesizing findings...")

        if not self.research_results:
            return {
                "synthesis": "No research results to synthesize",
                "confidence": 0.0,
            }

        # Generate synthesis based on results
        synthesis = {
            "summary": (
                f"Research synthesis from {len(self.research_results)} sources. "
                f"Checked sources: {', '.join(set(self.sources_checked))}"
            ),
            "key_findings": [
                result.get("title", "Finding") for result in self.research_results[:5]
            ],
            "confidence": sum(r.get("relevance", 0) for r in self.research_results)
            / len(self.research_results),
            "sources_count": len(self.research_results),
        }

        if output_format == "detailed":
            synthesis["detailed_results"] = self.research_results

        return synthesis

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate research step safety

        Args:
            step: Step to validate

        Returns:
            Safety validation result
        """
        tool = step["tool"]

        # Research operations are generally safe
        return {
            "requires_approval": False,
            "safe": True,
            "risk_level": "low",
            "risks": [],
            "mitigations": [],
        }

    def get_research_results(self) -> List[Dict[str, Any]]:
        """Get all research results"""
        return self.research_results

    def clear_results(self) -> None:
        """Clear research results"""
        self.research_results.clear()
        self.sources_checked.clear()
