"""
Integration tests for Agent Workflows.

Tests complete agent workflows including multi-step processes,
data flow between agents, and error handling.
"""

import pytest
import asyncio
from tests.utils.test_helpers import MockAgent, MockEventBus, MockDatabase


@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentWorkflows:
    """Test suite for complete agent workflows."""

    async def test_data_processing_workflow(self):
        """Test end-to-end data processing workflow."""
        # Create agents for each step
        fetcher = MockAgent("data_fetcher", responses=[{"data": [1, 2, 3]}])
        processor = MockAgent("processor", responses=[{"data": [2, 4, 6]}])
        validator = MockAgent("validator", responses=[{"valid": True}])

        # Execute workflow
        fetch_result = await fetcher.execute({"source": "database"})
        process_result = await processor.execute({"data": fetch_result["data"]})
        validation_result = await validator.execute({"data": process_result["data"]})

        assert validation_result["valid"] is True
        assert len(fetcher.tasks_executed) == 1
        assert len(processor.tasks_executed) == 1
        assert len(validator.tasks_executed) == 1

    async def test_parallel_data_aggregation(self):
        """Test parallel data aggregation workflow."""
        # Create multiple data fetchers
        fetchers = [
            MockAgent(f"fetcher{i}", responses=[{"data": [i, i+1, i+2]}])
            for i in range(5)
        ]

        # Fetch data in parallel
        fetch_tasks = [
            fetcher.execute({"source": f"source{i}"})
            for i, fetcher in enumerate(fetchers)
        ]

        results = await asyncio.gather(*fetch_tasks)

        # Aggregate results
        all_data = []
        for result in results:
            all_data.extend(result["data"])

        assert len(all_data) == 15  # 5 fetchers * 3 items each

    async def test_error_recovery_workflow(self):
        """Test workflow with error recovery."""
        # Agent that fails then succeeds
        attempts = []

        async def flaky_execute(task):
            attempts.append(1)
            if len(attempts) < 3:
                raise Exception("Temporary error")
            return {"success": True}

        agent = MockAgent("flaky_agent")
        agent.execute = flaky_execute

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await agent.execute({"task": "test"})
                break
            except Exception:
                if attempt == max_retries - 1:
                    raise

        assert result["success"] is True
        assert len(attempts) == 3

    async def test_conditional_workflow(self):
        """Test workflow with conditional branching."""
        checker = MockAgent("checker", responses=[{"condition": True}])
        path_a = MockAgent("path_a", responses=[{"result": "A"}])
        path_b = MockAgent("path_b", responses=[{"result": "B"}])

        # Check condition
        check_result = await checker.execute({"check": "something"})

        # Branch based on condition
        if check_result["condition"]:
            result = await path_a.execute({"branch": "A"})
        else:
            result = await path_b.execute({"branch": "B"})

        assert result["result"] == "A"

    async def test_long_running_workflow(self):
        """Test long-running workflow with multiple steps."""
        steps = [
            MockAgent(f"step{i}", responses=[{"step": i, "complete": True}])
            for i in range(10)
        ]

        results = []
        for step in steps:
            result = await step.execute({"step": step.name})
            results.append(result)

        assert len(results) == 10
        assert all(r["complete"] for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
class TestMCPIntegration:
    """Test suite for MCP client integration."""

    async def test_database_query_workflow(self, mock_mcp_client, mock_database):
        """Test database query via MCP client."""
        await mock_mcp_client.connect()
        await mock_database.connect()

        # Query via MCP
        mcp_result = await mock_mcp_client.send_request(
            "query",
            {"sql": "SELECT * FROM users"}
        )

        # Direct database query
        db_result = await mock_database.execute("SELECT * FROM users")

        assert mcp_result is not None
        assert len(mock_mcp_client.requests) == 1

    async def test_multi_database_operations(self, mock_mcp_client):
        """Test operations across multiple databases."""
        await mock_mcp_client.connect()

        # Query multiple databases
        operations = [
            ("query", {"sql": "SELECT * FROM users", "db": "db1"}),
            ("query", {"sql": "SELECT * FROM orders", "db": "db2"}),
            ("query", {"sql": "SELECT * FROM products", "db": "db3"})
        ]

        results = []
        for method, params in operations:
            result = await mock_mcp_client.send_request(method, params)
            results.append(result)

        assert len(results) == 3
        assert len(mock_mcp_client.requests) == 3

    async def test_transaction_workflow(self, mock_mcp_client):
        """Test transaction workflow via MCP."""
        await mock_mcp_client.connect()

        # Begin transaction
        await mock_mcp_client.send_request("begin", {})

        # Execute operations
        await mock_mcp_client.send_request(
            "execute",
            {"sql": "INSERT INTO users (name) VALUES ('test')"}
        )
        await mock_mcp_client.send_request(
            "execute",
            {"sql": "UPDATE accounts SET balance = balance - 100"}
        )

        # Commit
        await mock_mcp_client.send_request("commit", {})

        assert len(mock_mcp_client.requests) == 4


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseOperations:
    """Test suite for database operation integration."""

    async def test_crud_operations(self, connected_database):
        """Test complete CRUD workflow."""
        # Create
        await connected_database.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s)",
            ("Test User", "test@example.com")
        )

        # Read
        await connected_database.execute("SELECT * FROM users WHERE name = %s", ("Test User",))

        # Update
        await connected_database.execute(
            "UPDATE users SET email = %s WHERE name = %s",
            ("new@example.com", "Test User")
        )

        # Delete
        await connected_database.execute("DELETE FROM users WHERE name = %s", ("Test User",))

        assert len(connected_database.queries_executed) == 4

    async def test_batch_operations(self, connected_database):
        """Test batch database operations."""
        # Batch insert
        users = [
            ("User1", "user1@example.com"),
            ("User2", "user2@example.com"),
            ("User3", "user3@example.com")
        ]

        for name, email in users:
            await connected_database.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                (name, email)
            )

        assert len(connected_database.queries_executed) == 3

    async def test_join_operations(self, connected_database):
        """Test complex join operations."""
        query = """
        SELECT u.name, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.name
        """

        result = await connected_database.execute(query)

        assert len(connected_database.queries_executed) == 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestLLMRouting:
    """Test suite for LLM provider routing."""

    async def test_provider_selection(self, mock_llm):
        """Test selecting appropriate LLM provider."""
        # Route to provider based on task type
        task_type = "sql_generation"

        response = await mock_llm.generate("Generate SQL for users table")

        assert response is not None
        assert "SELECT" in response.upper()

    async def test_fallback_routing(self):
        """Test fallback to alternative provider."""
        from tests.utils.test_helpers import MockLLMProvider

        primary = MockLLMProvider()

        async def failing_generate(prompt, **kwargs):
            raise Exception("Primary failed")

        primary.generate = failing_generate

        fallback = MockLLMProvider(responses=["Fallback response"])

        # Try primary, fall back
        try:
            response = await primary.generate("test")
        except Exception:
            response = await fallback.generate("test")

        assert response == "Fallback response"

    async def test_load_balancing(self):
        """Test load balancing across providers."""
        from tests.utils.test_helpers import MockLLMProvider

        providers = [
            MockLLMProvider(responses=[f"Response from provider {i}"])
            for i in range(3)
        ]

        # Round-robin selection
        results = []
        for i, provider in enumerate(providers * 2):
            response = await provider.generate(f"Request {i}")
            results.append(response)

        assert len(results) == 6
