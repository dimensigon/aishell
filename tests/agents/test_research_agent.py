"""
Tests for Research Agent
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.agents.research_agent import ResearchAgent
from src.agents.base import TaskContext, AgentState


class TestResearchAgent:
    """Test suite for ResearchAgent"""

    @pytest.fixture
    async def research_agent(self):
        """Create a research agent instance for testing"""
        agent = ResearchAgent(
            agent_id="test-research-agent",
            config={
                "max_results": 5
            }
        )
        agent.status = AgentState.EXECUTING
        return agent

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test research agent initialization"""
        agent = ResearchAgent(
            agent_id="test-agent",
            config={"max_results": 10}
        )

        assert agent.agent_id == "test-agent"
        assert agent.max_results == 10
        assert agent.research_results == []
        assert agent.sources_checked == []

    @pytest.mark.asyncio
    async def test_plan_generation(self, research_agent):
        """Test research plan generation"""
        task = TaskContext(
            task_id="test-task-1",
            task_description="Research Python best practices",
            input_data={
                "query": "Python async programming best practices",
                "type": "general",
                "depth": "standard"
            }
        )

        plan = await research_agent.plan(task)

        assert isinstance(plan, list)
        assert len(plan) == 2  # standard depth has 2 steps
        assert plan[0]["tool"] == "search_information"
        assert plan[1]["tool"] == "synthesize_findings"

    @pytest.mark.asyncio
    async def test_deep_research_plan(self, research_agent):
        """Test deep research plan generation"""
        task = TaskContext(
            task_id="test-task-2",
            task_description="Deep research on database optimization",
            input_data={
                "query": "PostgreSQL query optimization techniques",
                "type": "technical",
                "depth": "deep",
                "criteria": ["performance", "scalability"]
            }
        )

        plan = await research_agent.plan(task)

        assert isinstance(plan, list)
        assert len(plan) == 3  # deep research has 3 steps
        assert plan[0]["tool"] == "search_information"
        assert plan[1]["tool"] == "analyze_sources"
        assert plan[2]["tool"] == "synthesize_findings"

    @pytest.mark.asyncio
    async def test_search_information(self, research_agent):
        """Test information search functionality"""
        step = {
            "tool": "search_information",
            "params": {
                "query": "test query",
                "max_results": 3,
                "sources": ["documentation"]
            }
        }

        result = await research_agent.execute_step(step)

        assert result["success"] is True
        assert "results_count" in result
        assert result["results_count"] > 0
        assert result["sources"] == ["documentation"]
        assert len(research_agent.research_results) > 0

    @pytest.mark.asyncio
    async def test_analyze_sources(self, research_agent):
        """Test source analysis functionality"""
        # First populate some research results
        research_agent.research_results = [
            {
                "source": "test",
                "title": "Test Result 1",
                "content": "This is about performance optimization",
                "relevance": 0.9
            },
            {
                "source": "test",
                "title": "Test Result 2",
                "content": "This is about scalability",
                "relevance": 0.6
            }
        ]

        step = {
            "tool": "analyze_sources",
            "params": {
                "criteria": ["performance", "scalability"]
            }
        }

        result = await research_agent.execute_step(step)

        assert result["success"] is True
        assert "analyzed_count" in result
        assert result["analyzed_count"] == 2
        assert result["results"][0]["validation"] == "validated"  # relevance > 0.7
        assert result["results"][1]["validation"] == "needs_review"  # relevance <= 0.7

    @pytest.mark.asyncio
    async def test_synthesize_findings_summary(self, research_agent):
        """Test synthesis of findings into summary"""
        research_agent.research_results = [
            {"title": "Result 1", "source": "doc1"},
            {"title": "Result 2", "source": "doc2"}
        ]
        research_agent.sources_checked = ["documentation"]

        step = {
            "tool": "synthesize_findings",
            "params": {"format": "summary"}
        }

        result = await research_agent.execute_step(step)

        assert result["success"] is True
        assert result["format"] == "summary"
        assert isinstance(result["synthesis"], str)
        assert "Research Summary" in result["synthesis"]

    @pytest.mark.asyncio
    async def test_synthesize_findings_detailed(self, research_agent):
        """Test synthesis of findings into detailed report"""
        research_agent.research_results = [
            {
                "title": "Result 1",
                "source": "doc1",
                "content": "Content 1",
                "relevance": 0.9
            }
        ]
        research_agent.sources_checked = ["documentation", "web"]

        step = {
            "tool": "synthesize_findings",
            "params": {"format": "detailed"}
        }

        result = await research_agent.execute_step(step)

        assert result["success"] is True
        assert result["format"] == "detailed"
        assert isinstance(result["synthesis"], dict)
        assert "total_results" in result["synthesis"]
        assert "sources" in result["synthesis"]
        assert "findings" in result["synthesis"]

    @pytest.mark.asyncio
    async def test_execute_complete_task(self, research_agent):
        """Test executing a complete research task"""
        task = TaskContext(
            task_id="test-complete-task",
            task_description="Research test topic",
            input_data={
                "query": "test topic",
                "type": "general",
                "depth": "standard",
                "output_format": "summary"
            }
        )

        # Generate plan
        plan = await research_agent.plan(task)

        # Execute each step
        for step in plan:
            result = await research_agent.execute_step(step)
            assert result["success"] is True

        # Verify research results were collected
        assert len(research_agent.research_results) > 0
        assert len(research_agent.sources_checked) > 0

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, research_agent):
        """Test handling of empty query"""
        task = TaskContext(
            task_id="test-empty",
            task_description="Research without query",
            input_data={
                "query": "",
                "type": "general"
            }
        )

        with pytest.raises(ValueError, match="No research query specified"):
            await research_agent.plan(task)

    @pytest.mark.asyncio
    async def test_unknown_tool_handling(self, research_agent):
        """Test handling of unknown tool"""
        step = {
            "tool": "unknown_tool",
            "params": {}
        }

        with pytest.raises(ValueError, match="Unknown tool: unknown_tool"):
            await research_agent.execute_step(step)

    @pytest.mark.asyncio
    async def test_get_research_results(self, research_agent):
        """Test getting research results"""
        test_results = [
            {"title": "Test 1"},
            {"title": "Test 2"}
        ]
        research_agent.research_results = test_results

        results = research_agent.get_research_results()

        assert results == test_results

    @pytest.mark.asyncio
    async def test_clear_results(self, research_agent):
        """Test clearing research results"""
        research_agent.research_results = [{"title": "Test"}]
        research_agent.sources_checked = ["test_source"]

        research_agent.clear_results()

        assert research_agent.research_results == []
        assert research_agent.sources_checked == []

    @pytest.mark.asyncio
    async def test_web_search_with_llm(self, research_agent):
        """Test web search when LLM is available"""
        research_agent.llm_manager = Mock()

        step = {
            "tool": "search_information",
            "params": {
                "query": "test query",
                "sources": ["web"]
            }
        }

        result = await research_agent.execute_step(step)

        assert result["success"] is True
        assert "web" in result["sources"]
        # Should have web results when LLM is available
        web_results = [r for r in result["results"] if r["source"] == "web"]
        assert len(web_results) > 0

    @pytest.mark.asyncio
    async def test_json_output_format(self, research_agent):
        """Test JSON output format for synthesis"""
        research_agent.research_results = [
            {"title": "Test", "content": "Test content"}
        ]

        step = {
            "tool": "synthesize_findings",
            "params": {"format": "json"}
        }

        result = await research_agent.execute_step(step)

        assert result["success"] is True
        assert result["format"] == "json"
        assert isinstance(result["synthesis"], dict)
        assert "findings" in result["synthesis"]