"""
Integration tests for AI-Shell.

End-to-end tests validating complete workflows.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import AIShell
from src.core.config import ConfigManager
from src.llm.manager import LocalLLMManager
from src.mcp_clients.manager import ConnectionManager


class TestAIShellIntegration:
    """Integration tests for AIShell application."""

    @pytest.fixture
    async def ai_shell(self):
        """Create AIShell instance with mocked dependencies."""
        # Create mocks
        with patch('src.llm.manager.LocalLLMManager.initialize') as mock_llm_init, \
             patch('src.llm.manager.LocalLLMManager.generate_response') as mock_llm_gen, \
             patch('src.database.module.DatabaseModule.initialize') as mock_db_init, \
             patch('src.vector.autocomplete.IntelligentCompleter.initialize') as mock_ac_init, \
             patch('src.performance.monitor.SystemMonitor.start_monitoring') as mock_mon, \
             patch('src.performance.monitor.SystemMonitor.perform_health_check') as mock_health:

            # Configure mocks for async
            mock_llm_init.return_value = asyncio.coroutine(lambda: None)()
            mock_llm_gen.return_value = asyncio.coroutine(lambda: "AI response")()
            mock_db_init.return_value = asyncio.coroutine(lambda: None)()
            mock_ac_init.return_value = asyncio.coroutine(lambda: None)()
            mock_mon.return_value = asyncio.coroutine(lambda: None)()
            mock_health.return_value = asyncio.coroutine(lambda: {'system': {'status': 'healthy'}})()

            shell = AIShell()
            try:
                await shell.initialize()
                yield shell
            finally:
                await shell.shutdown()

    @pytest.mark.asyncio
    async def test_initialization(self, ai_shell):
        """Test complete initialization flow."""
        assert ai_shell._initialized
        assert ai_shell.ai_provider is not None
        assert ai_shell.optimizer is not None
        assert ai_shell.monitor is not None
        assert ai_shell.cache is not None

    @pytest.mark.asyncio
    async def test_query_execution_flow(self, ai_shell):
        """Test end-to-end query execution."""
        # Mock query executor
        ai_shell.query_executor = AsyncMock()
        ai_shell.query_executor.execute_query.return_value = {
            'status': 'success',
            'rows': [{'id': 1, 'name': 'Test'}],
            'execution_time': 0.1
        }

        result = await ai_shell.execute_query("SELECT * FROM users")

        assert result['status'] == 'success'
        assert len(result['rows']) == 1
        ai_shell.query_executor.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_suggestion_flow(self, ai_shell):
        """Test AI suggestion generation."""
        response = await ai_shell.get_ai_suggestion(
            "How do I optimize this query?",
            context={'query': 'SELECT * FROM users'}
        )

        assert response == "AI response"
        ai_shell.ai_provider.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_monitoring(self, ai_shell):
        """Test health monitoring integration."""
        health = await ai_shell.get_health_status()

        assert 'status' in health
        assert 'checks' in health
        assert isinstance(health['checks'], list)

    @pytest.mark.asyncio
    async def test_performance_metrics(self, ai_shell):
        """Test performance metrics collection."""
        # Record some activity
        await ai_shell.optimizer.record_execution("SELECT 1", 0.1)
        await ai_shell.cache.set("SELECT 1", [1])
        await ai_shell.cache.get("SELECT 1")

        metrics = await ai_shell.get_performance_metrics()

        assert 'optimizer' in metrics
        assert 'cache' in metrics
        assert 'system' in metrics
        assert metrics['optimizer']['query_count'] > 0

    @pytest.mark.asyncio
    async def test_caching_integration(self, ai_shell):
        """Test query caching in execution flow."""
        ai_shell.query_executor = AsyncMock()
        ai_shell.query_executor.execute_query.return_value = {
            'status': 'success',
            'rows': [{'id': 1}],
            'execution_time': 0.1
        }

        query = "SELECT * FROM users WHERE id = 1"

        # First execution - cache miss
        result1 = await ai_shell.execute_query(query)

        # Second execution - should use cache
        result2 = await ai_shell.execute_query(query)

        assert result1 == result2

    @pytest.mark.asyncio
    async def test_optimization_integration(self, ai_shell):
        """Test query optimization in execution flow."""
        original_query = "SELECT * FROM users"

        # Mock executor to capture optimized query
        ai_shell.query_executor = AsyncMock()
        ai_shell.query_executor.execute_query.return_value = {
            'status': 'success',
            'rows': [],
            'execution_time': 0.05
        }

        await ai_shell.execute_query(original_query)

        # Verify optimizer was called
        metrics = await ai_shell.optimizer.get_metrics()
        assert metrics.query_count > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, ai_shell):
        """Test error handling in execution flow."""
        ai_shell.query_executor = AsyncMock()
        ai_shell.query_executor.execute_query.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await ai_shell.execute_query("SELECT * FROM invalid")

    @pytest.mark.asyncio
    async def test_shutdown_cleanup(self, ai_shell):
        """Test proper cleanup on shutdown."""
        await ai_shell.shutdown()

        assert not ai_shell._initialized
        assert not ai_shell.monitor._monitoring


class TestMultiProviderIntegration:
    """Test integration with multiple AI providers."""

    @pytest.mark.asyncio
    async def test_openai_provider_integration(self):
        """Test OpenAI provider integration."""
        with patch('src.core.ai_provider.OpenAIProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.generate_response.return_value = "OpenAI response"
            mock_provider.return_value = mock_instance

            settings = Settings(
                ai_provider='openai',
                openai_api_key='test-key'
            )

            from src.core.ai_provider import get_ai_provider
            provider = await get_ai_provider(settings)

            response = await provider.generate_response("test prompt")
            assert response == "OpenAI response"

    @pytest.mark.asyncio
    async def test_anthropic_provider_integration(self):
        """Test Anthropic provider integration."""
        with patch('src.core.ai_provider.AnthropicProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.generate_response.return_value = "Anthropic response"
            mock_provider.return_value = mock_instance

            settings = Settings(
                ai_provider='anthropic',
                anthropic_api_key='test-key'
            )

            from src.core.ai_provider import get_ai_provider
            provider = await get_ai_provider(settings)

            response = await provider.generate_response("test prompt")
            assert response == "Anthropic response"


class TestDatabaseIntegration:
    """Test database integration scenarios."""

    @pytest.mark.asyncio
    async def test_connection_pooling(self):
        """Test connection pool management."""
        with patch('aiomysql.create_pool') as mock_pool:
            mock_pool.return_value = AsyncMock()

            settings = Settings(
                database_url='mysql://user:pass@localhost/test',
                max_connections=5
            )

            manager = DatabaseConnectionManager(settings)
            pool = await manager.get_connection('test')

            assert pool is not None
            mock_pool.assert_called_once()

    @pytest.mark.asyncio
    async def test_multi_database_support(self):
        """Test multiple database connections."""
        with patch('aiomysql.create_pool') as mock_mysql, \
             patch('aiopg.create_pool') as mock_pg:

            mock_mysql.return_value = AsyncMock()
            mock_pg.return_value = AsyncMock()

            settings = Settings(database_url='mysql://localhost/db1')
            manager = DatabaseConnectionManager(settings)

            mysql_pool = await manager.get_connection('db1')
            pg_pool = await manager.get_connection('postgres://localhost/db2')

            assert mysql_pool is not None
            assert pg_pool is not None


class TestSecurityIntegration:
    """Test security integration scenarios."""

    @pytest.mark.asyncio
    async def test_query_validation(self):
        """Test SQL injection prevention."""
        from src.core.security_manager import SecurityManager

        settings = Settings()
        security = SecurityManager(settings)

        # Test malicious query
        malicious = "SELECT * FROM users; DROP TABLE users;"
        with pytest.raises(ValueError, match="Multiple statements"):
            await security.validate_query(malicious)

    @pytest.mark.asyncio
    async def test_api_key_encryption(self):
        """Test API key encryption/decryption."""
        from src.core.security_manager import SecurityManager

        settings = Settings(encryption_key='test-key-32-characters-long!!!!')
        security = SecurityManager(settings)

        original = "secret-api-key"
        encrypted = security.encrypt_value(original)
        decrypted = security.decrypt_value(encrypted)

        assert encrypted != original
        assert decrypted == original


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_complete_query_workflow(self):
        """Test complete query execution workflow."""
        with patch('src.main.get_settings'), \
             patch('src.main.get_ai_provider'), \
             patch('src.core.security_manager.SecurityManager'), \
             patch('src.db.connection_manager.DatabaseConnectionManager'):

            shell = AIShell()
            await shell.initialize()

            # Mock complete workflow
            shell.query_executor = AsyncMock()
            shell.query_executor.execute_query.return_value = {
                'status': 'success',
                'rows': [{'count': 10}],
                'execution_time': 0.15
            }

            # Execute query
            result = await shell.execute_query("SELECT COUNT(*) FROM users")

            # Verify workflow
            assert result['status'] == 'success'

            # Check metrics recorded
            metrics = await shell.get_performance_metrics()
            assert metrics['optimizer']['query_count'] > 0

            # Check health
            health = await shell.get_health_status()
            assert health['status'] in ['healthy', 'degraded', 'unhealthy']

            await shell.shutdown()

    @pytest.mark.asyncio
    async def test_ai_assisted_optimization(self):
        """Test AI-assisted query optimization workflow."""
        with patch('src.main.get_settings'), \
             patch('src.main.get_ai_provider') as mock_ai:

            # Mock AI provider
            ai_provider = AsyncMock()
            ai_provider.generate_response.return_value = """
            To optimize this query, consider:
            1. Add index on user_id
            2. Use LIMIT clause
            3. Avoid SELECT *
            """
            mock_ai.return_value = ai_provider

            shell = AIShell()
            await shell.initialize()

            # Get AI suggestion
            suggestion = await shell.get_ai_suggestion(
                "How can I optimize: SELECT * FROM orders WHERE user_id = 1",
                context={'database': 'production'}
            )

            assert 'index' in suggestion.lower()
            assert 'optimize' in suggestion.lower()

            await shell.shutdown()
