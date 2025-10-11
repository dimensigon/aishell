"""
Comprehensive tests for src/main.py to achieve 85%+ coverage.

Tests CLI argument parsing, initialization flows, shutdown, command execution,
interactive mode, health checks, and all main entry points.
"""

import pytest
import asyncio
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import argparse

from src.main import (
    AIShell,
    configure_logging,
    print_health_check,
    execute_single_command,
    main
)


class TestAIShellInitialization:
    """Test AIShell class initialization"""

    def test_init_default(self):
        """Test default initialization"""
        shell = AIShell()
        assert shell.config is not None
        assert shell.db_path_override is None
        assert shell.core is not None
        assert not shell._initialized

    def test_init_with_config_path(self):
        """Test initialization with custom config path"""
        shell = AIShell(config_path="/custom/config.yaml")
        assert shell.config is not None
        assert shell.db_path_override is None

    def test_init_with_db_path(self):
        """Test initialization with db path override"""
        shell = AIShell(db_path="/custom/db.sqlite")
        assert shell.db_path_override == "/custom/db.sqlite"

    def test_init_with_both_params(self):
        """Test initialization with both config and db path"""
        shell = AIShell(config_path="/config.yaml", db_path="/db.sqlite")
        assert shell.config is not None
        assert shell.db_path_override == "/db.sqlite"


class TestAIShellInitializeMethod:
    """Test AIShell.initialize() method"""

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful initialization"""
        shell = AIShell()

        with patch.object(shell.core, 'initialize', new_callable=AsyncMock), \
             patch.object(shell.config, 'get') as mock_get, \
             patch('src.main.SecureVault'), \
             patch('src.main.LocalLLMManager'), \
             patch('src.main.ConnectionManager'), \
             patch('src.main.PerformanceOptimizer'), \
             patch('src.main.SystemMonitor') as MockMonitor, \
             patch('src.main.QueryCache'), \
             patch('src.main.DatabaseModule'):

            # Mock config get calls
            mock_get.side_effect = lambda k, default=None: {
                'security.vault_key': 'test-key',
                'llm.model_path': '/models',
                'llm.provider': 'ollama',
                'llm.models.intent': 'llama2',
                'mcp.max_connections': 10,
                'database.path': None,
                'database.auto_confirm': False
            }.get(k, default)

            # Mock monitor
            mock_monitor = MockMonitor.return_value
            mock_monitor.start_monitoring = AsyncMock()
            mock_monitor.perform_health_check = AsyncMock(return_value={
                'core': 'healthy',
                'database': 'healthy'
            })

            await shell.initialize()

            assert shell._initialized
            assert shell.vault is not None
            assert shell.llm_manager is not None

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self):
        """Test initialize when already initialized"""
        shell = AIShell()
        shell._initialized = True

        with patch('src.main.logger') as mock_logger:
            await shell.initialize()
            mock_logger.warning.assert_called_with("AI-Shell already initialized")

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """Test initialization failure"""
        shell = AIShell()

        with patch.object(shell.core, 'initialize', new_callable=AsyncMock) as mock_init:
            mock_init.side_effect = Exception("Init failed")

            with pytest.raises(Exception, match="Init failed"):
                await shell.initialize()

            assert not shell._initialized


class TestAIShellShutdown:
    """Test AIShell.shutdown() method"""

    @pytest.mark.asyncio
    async def test_shutdown_success(self):
        """Test successful shutdown"""
        shell = AIShell()
        shell._initialized = True

        # Create mocks
        shell.monitor = Mock()
        shell.monitor.stop_monitoring = AsyncMock()
        shell.db_module = Mock()
        shell.llm_manager = Mock(initialized=True)
        shell.cache = Mock()
        shell.cache.clear = AsyncMock()
        shell.core = Mock()
        shell.core.shutdown = AsyncMock()

        await shell.shutdown()

        assert not shell._initialized
        shell.monitor.stop_monitoring.assert_called_once()
        shell.cache.clear.assert_called_once()
        shell.core.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_with_none_components(self):
        """Test shutdown with None components"""
        shell = AIShell()
        shell._initialized = True
        shell.monitor = None
        shell.cache = None

        await shell.shutdown()
        assert not shell._initialized

    @pytest.mark.asyncio
    async def test_shutdown_with_error(self):
        """Test shutdown with error"""
        shell = AIShell()
        shell._initialized = True
        shell.core = Mock()
        shell.core.shutdown = AsyncMock(side_effect=Exception("Shutdown failed"))

        with patch('src.main.logger') as mock_logger:
            await shell.shutdown()
            mock_logger.error.assert_called()


class TestAIShellExecuteQuery:
    """Test AIShell.execute_query() method"""

    @pytest.mark.asyncio
    async def test_execute_query_not_initialized(self):
        """Test query execution when not initialized"""
        shell = AIShell()

        with pytest.raises(RuntimeError, match="AI-Shell not initialized"):
            await shell.execute_query("SELECT * FROM test")

    @pytest.mark.asyncio
    async def test_execute_query_success(self):
        """Test successful query execution"""
        shell = AIShell()
        shell._initialized = True
        shell.optimizer = Mock()
        shell.optimizer.optimize_query = AsyncMock(return_value="OPTIMIZED SQL")
        shell.optimizer.record_execution = AsyncMock()
        shell.db_module = Mock()
        shell.db_module.execute_query = AsyncMock(return_value={
            'rows': [],
            'execution_time': 0.5
        })

        result = await shell.execute_query("SELECT * FROM test")

        assert result['execution_time'] == 0.5
        shell.optimizer.optimize_query.assert_called_once()
        shell.optimizer.record_execution.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_with_connection_id(self):
        """Test query execution with connection ID"""
        shell = AIShell()
        shell._initialized = True
        shell.optimizer = Mock()
        shell.optimizer.optimize_query = AsyncMock(return_value="SQL")
        shell.optimizer.record_execution = AsyncMock()
        shell.db_module = Mock()
        shell.db_module.execute_query = AsyncMock(return_value={'execution_time': 0.1})

        await shell.execute_query("SELECT 1", connection_id="conn123")

        shell.db_module.execute_query.assert_called_with(
            query="SQL",
            connection_id="conn123"
        )

    @pytest.mark.asyncio
    async def test_execute_query_failure(self):
        """Test query execution failure"""
        shell = AIShell()
        shell._initialized = True
        shell.optimizer = Mock()
        shell.optimizer.optimize_query = AsyncMock(side_effect=Exception("Query failed"))

        with pytest.raises(Exception, match="Query failed"):
            await shell.execute_query("BAD SQL")


class TestAIShellGetAISuggestion:
    """Test AIShell.get_ai_suggestion() method"""

    @pytest.mark.asyncio
    async def test_get_ai_suggestion_not_initialized(self):
        """Test AI suggestion when not initialized"""
        shell = AIShell()

        with pytest.raises(RuntimeError, match="AI-Shell not initialized"):
            await shell.get_ai_suggestion("How to optimize?")

    @pytest.mark.asyncio
    async def test_get_ai_suggestion_success(self):
        """Test successful AI suggestion"""
        shell = AIShell()
        shell._initialized = True
        shell.llm_manager = Mock()
        shell.llm_manager.generate_response = AsyncMock(
            return_value="Use indexes for better performance"
        )

        result = await shell.get_ai_suggestion("How to optimize?")

        assert result == "Use indexes for better performance"
        shell.llm_manager.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ai_suggestion_with_context(self):
        """Test AI suggestion with context"""
        shell = AIShell()
        shell._initialized = True
        shell.llm_manager = Mock()
        shell.llm_manager.generate_response = AsyncMock(return_value="Response")

        context = {'database': 'postgres', 'tables': ['users']}
        await shell.get_ai_suggestion("Question", context=context)

        shell.llm_manager.generate_response.assert_called_with(
            prompt="Question",
            model_type='intent',
            context=context
        )


class TestAIShellHealthAndMetrics:
    """Test health and metrics methods"""

    @pytest.mark.asyncio
    async def test_get_health_status_not_initialized(self):
        """Test health status when not initialized"""
        shell = AIShell()

        with pytest.raises(RuntimeError, match="AI-Shell not initialized"):
            await shell.get_health_status()

    @pytest.mark.asyncio
    async def test_get_health_status_success(self):
        """Test successful health status"""
        shell = AIShell()
        shell._initialized = True
        shell.monitor = Mock()
        shell.monitor.get_health_summary = AsyncMock(return_value={
            'status': 'healthy',
            'checks': []
        })

        result = await shell.get_health_status()

        assert result['status'] == 'healthy'

    @pytest.mark.asyncio
    async def test_get_performance_metrics_not_initialized(self):
        """Test metrics when not initialized"""
        shell = AIShell()

        with pytest.raises(RuntimeError, match="AI-Shell not initialized"):
            await shell.get_performance_metrics()

    @pytest.mark.asyncio
    async def test_get_performance_metrics_success(self):
        """Test successful performance metrics"""
        shell = AIShell()
        shell._initialized = True

        # Mock optimizer metrics
        shell.optimizer = Mock()
        mock_opt_metrics = Mock(
            query_count=100,
            avg_execution_time=0.5,
            slow_queries=5
        )
        shell.optimizer.get_metrics = AsyncMock(return_value=mock_opt_metrics)

        # Mock cache stats
        shell.cache = Mock()
        shell.cache.get_stats = AsyncMock(return_value={
            'hit_rate': 0.8,
            'size': 50
        })

        # Mock monitor metrics
        shell.monitor = Mock()
        shell.monitor.get_metrics_summary = AsyncMock(return_value={
            'cpu': 50,
            'memory': 1024
        })

        result = await shell.get_performance_metrics()

        assert result['optimizer']['query_count'] == 100
        assert result['optimizer']['avg_execution_time'] == 0.5
        assert result['cache']['hit_rate'] == 0.8


class TestAIShellInteractiveMode:
    """Test interactive mode"""

    @pytest.mark.asyncio
    async def test_interactive_mode_initializes_if_needed(self):
        """Test interactive mode initializes if not initialized"""
        shell = AIShell()

        with patch.object(shell, 'initialize', new_callable=AsyncMock) as mock_init, \
             patch('builtins.input', side_effect=['exit']):
            await shell.interactive_mode()
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_interactive_mode_health_command(self):
        """Test health command in interactive mode"""
        shell = AIShell()
        shell._initialized = True

        with patch('builtins.input', side_effect=['health', 'exit']), \
             patch.object(shell, 'get_health_status', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {
                'status': 'healthy',
                'message': 'All good',
                'checks': [{'component': 'db', 'status': 'healthy'}]
            }

            await shell.interactive_mode()
            mock_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_interactive_mode_metrics_command(self):
        """Test metrics command in interactive mode"""
        shell = AIShell()
        shell._initialized = True

        with patch('builtins.input', side_effect=['metrics', 'exit']), \
             patch.object(shell, 'get_performance_metrics', new_callable=AsyncMock) as mock_metrics:
            mock_metrics.return_value = {
                'optimizer': {'query_count': 10, 'avg_execution_time': 0.5},
                'cache': {'hit_rate': 0.8}
            }

            await shell.interactive_mode()
            mock_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_interactive_mode_query_command(self):
        """Test query command in interactive mode"""
        shell = AIShell()
        shell._initialized = True

        with patch('builtins.input', side_effect=['query SELECT 1', 'exit']), \
             patch.object(shell, 'execute_query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = {'rows': []}

            await shell.interactive_mode()
            mock_query.assert_called_with('SELECT 1')

    @pytest.mark.asyncio
    async def test_interactive_mode_ask_command(self):
        """Test ask command in interactive mode"""
        shell = AIShell()
        shell._initialized = True

        with patch('builtins.input', side_effect=['ask How to optimize?', 'exit']), \
             patch.object(shell, 'get_ai_suggestion', new_callable=AsyncMock) as mock_ask:
            mock_ask.return_value = "Use indexes"

            await shell.interactive_mode()
            mock_ask.assert_called_with('How to optimize?')

    @pytest.mark.asyncio
    async def test_interactive_mode_empty_input(self):
        """Test empty input is skipped"""
        shell = AIShell()
        shell._initialized = True

        with patch('builtins.input', side_effect=['', '  ', 'exit']):
            await shell.interactive_mode()
            # Should complete without errors

    @pytest.mark.asyncio
    async def test_interactive_mode_unknown_command(self):
        """Test unknown command"""
        shell = AIShell()
        shell._initialized = True

        with patch('builtins.input', side_effect=['unknown', 'exit']):
            await shell.interactive_mode()
            # Should print error and continue

    @pytest.mark.asyncio
    async def test_interactive_mode_keyboard_interrupt(self):
        """Test KeyboardInterrupt handling"""
        shell = AIShell()
        shell._initialized = True

        with patch('builtins.input', side_effect=[KeyboardInterrupt, 'exit']):
            await shell.interactive_mode()
            # Should handle gracefully

    @pytest.mark.asyncio
    async def test_interactive_mode_exception(self):
        """Test exception handling in interactive mode"""
        shell = AIShell()
        shell._initialized = True

        with patch('builtins.input', side_effect=['health', 'exit']), \
             patch.object(shell, 'get_health_status', new_callable=AsyncMock) as mock_health:
            mock_health.side_effect = Exception("Health check failed")

            await shell.interactive_mode()
            # Should handle exception and continue


class TestConfigureLogging:
    """Test configure_logging function"""

    def test_configure_logging_default(self):
        """Test default logging configuration"""
        configure_logging('INFO')
        # Should complete without errors

    def test_configure_logging_debug(self):
        """Test DEBUG level"""
        configure_logging('DEBUG')
        # Should complete without errors

    def test_configure_logging_with_file(self, tmp_path):
        """Test logging to file"""
        log_file = tmp_path / "test.log"
        configure_logging('INFO', str(log_file))
        # Should complete without errors

    def test_configure_logging_invalid_level(self):
        """Test invalid log level uses INFO as default"""
        configure_logging('INVALID')
        # Should complete without errors (falls back to INFO)


class TestPrintHealthCheck:
    """Test print_health_check function"""

    @pytest.mark.asyncio
    async def test_print_health_check_healthy(self):
        """Test health check printing when healthy"""
        shell = Mock()
        shell.initialize = AsyncMock()
        shell.get_health_status = AsyncMock(return_value={
            'status': 'healthy',
            'message': 'All systems operational',
            'checks': [
                {'component': 'core', 'status': 'healthy'},
                {'component': 'database', 'status': 'healthy'}
            ]
        })

        with pytest.raises(SystemExit) as exc_info:
            await print_health_check(shell)

        assert exc_info.value.code == 0

    @pytest.mark.asyncio
    async def test_print_health_check_unhealthy(self):
        """Test health check printing when unhealthy"""
        shell = Mock()
        shell.initialize = AsyncMock()
        shell.get_health_status = AsyncMock(return_value={
            'status': 'unhealthy',
            'message': 'Issues detected',
            'checks': [
                {'component': 'core', 'status': 'healthy'},
                {'component': 'database', 'status': 'unhealthy', 'details': 'Connection failed'}
            ]
        })

        with pytest.raises(SystemExit) as exc_info:
            await print_health_check(shell)

        assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_print_health_check_exception(self):
        """Test health check with exception"""
        shell = Mock()
        shell.initialize = AsyncMock(side_effect=Exception("Init failed"))

        with pytest.raises(SystemExit) as exc_info:
            await print_health_check(shell)

        assert exc_info.value.code == 1


class TestExecuteSingleCommand:
    """Test execute_single_command function"""

    @pytest.mark.asyncio
    async def test_execute_single_command_query(self):
        """Test executing query command"""
        shell = Mock()
        shell.initialize = AsyncMock()
        shell.execute_query = AsyncMock(return_value={'rows': []})

        with pytest.raises(SystemExit) as exc_info:
            await execute_single_command(shell, "query SELECT 1")

        assert exc_info.value.code == 0
        shell.execute_query.assert_called_with("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_single_command_ask(self):
        """Test executing ask command"""
        shell = Mock()
        shell.initialize = AsyncMock()
        shell.get_ai_suggestion = AsyncMock(return_value="Response")

        with pytest.raises(SystemExit) as exc_info:
            await execute_single_command(shell, "ask What is SQL?")

        assert exc_info.value.code == 0
        shell.get_ai_suggestion.assert_called_with("What is SQL?")

    @pytest.mark.asyncio
    async def test_execute_single_command_health(self):
        """Test executing health command"""
        shell = Mock()
        shell.initialize = AsyncMock()
        shell.get_health_status = AsyncMock(return_value={
            'status': 'healthy',
            'message': 'OK'
        })

        with pytest.raises(SystemExit) as exc_info:
            await execute_single_command(shell, "health")

        assert exc_info.value.code == 0

    @pytest.mark.asyncio
    async def test_execute_single_command_metrics(self):
        """Test executing metrics command"""
        shell = Mock()
        shell.initialize = AsyncMock()
        shell.get_performance_metrics = AsyncMock(return_value={
            'optimizer': {'query_count': 10, 'avg_execution_time': 0.5},
            'cache': {'hit_rate': 0.8}
        })

        with pytest.raises(SystemExit) as exc_info:
            await execute_single_command(shell, "metrics")

        assert exc_info.value.code == 0

    @pytest.mark.asyncio
    async def test_execute_single_command_unknown(self):
        """Test executing unknown command"""
        shell = Mock()
        shell.initialize = AsyncMock()

        with pytest.raises(SystemExit) as exc_info:
            await execute_single_command(shell, "unknown command")

        assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_execute_single_command_exception(self):
        """Test exception during command execution"""
        shell = Mock()
        shell.initialize = AsyncMock(side_effect=Exception("Failed"))

        with pytest.raises(SystemExit) as exc_info:
            await execute_single_command(shell, "health")

        assert exc_info.value.code == 1


class TestMainFunction:
    """Test main() function"""

    @pytest.mark.asyncio
    async def test_main_default_interactive(self):
        """Test default interactive mode"""
        with patch('sys.argv', ['ai-shell']), \
             patch('src.main.AIShell') as MockShell:

            mock_shell = MockShell.return_value
            mock_shell.initialize = AsyncMock()
            mock_shell.interactive_mode = AsyncMock()
            mock_shell.shutdown = AsyncMock()

            await main()

            mock_shell.initialize.assert_called_once()
            mock_shell.interactive_mode.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_health_check(self):
        """Test --health-check flag"""
        with patch('sys.argv', ['ai-shell', '--health-check']), \
             patch('src.main.AIShell'), \
             patch('src.main.print_health_check', new_callable=AsyncMock) as mock_health:

            await main()
            mock_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_execute_command(self):
        """Test --execute flag"""
        with patch('sys.argv', ['ai-shell', '--execute', 'health']), \
             patch('src.main.AIShell'), \
             patch('src.main.execute_single_command', new_callable=AsyncMock) as mock_exec:

            await main()
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_no_interactive(self):
        """Test --no-interactive flag"""
        with patch('sys.argv', ['ai-shell', '--no-interactive']), \
             patch('src.main.AIShell') as MockShell:

            mock_shell = MockShell.return_value
            mock_shell.initialize = AsyncMock()
            mock_shell.shutdown = AsyncMock()

            await main()

            mock_shell.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_with_config(self):
        """Test --config flag"""
        with patch('sys.argv', ['ai-shell', '--config', '/config.yaml', '--no-interactive']), \
             patch('src.main.AIShell') as MockShell:

            mock_shell = MockShell.return_value
            mock_shell.initialize = AsyncMock()
            mock_shell.shutdown = AsyncMock()

            await main()

            MockShell.assert_called_with(
                config_path='/config.yaml',
                db_path=None
            )

    @pytest.mark.asyncio
    async def test_main_with_db_path(self):
        """Test --db-path flag"""
        with patch('sys.argv', ['ai-shell', '--db-path', '/db.sqlite', '--no-interactive']), \
             patch('src.main.AIShell') as MockShell:

            mock_shell = MockShell.return_value
            mock_shell.initialize = AsyncMock()
            mock_shell.shutdown = AsyncMock()

            await main()

            MockShell.assert_called_with(
                config_path=None,
                db_path='/db.sqlite'
            )

    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self):
        """Test KeyboardInterrupt handling"""
        with patch('sys.argv', ['ai-shell']), \
             patch('src.main.AIShell') as MockShell:

            mock_shell = MockShell.return_value
            mock_shell.initialize = AsyncMock()
            mock_shell.interactive_mode = AsyncMock(side_effect=KeyboardInterrupt)
            mock_shell.shutdown = AsyncMock()

            await main()

            mock_shell.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_exception(self):
        """Test exception handling"""
        with patch('sys.argv', ['ai-shell']), \
             patch('src.main.AIShell') as MockShell:

            mock_shell = MockShell.return_value
            mock_shell.initialize = AsyncMock(side_effect=Exception("Fatal error"))
            mock_shell.shutdown = AsyncMock()

            with pytest.raises(SystemExit) as exc_info:
                await main()

            assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_main_log_level_debug(self):
        """Test --log-level DEBUG"""
        with patch('sys.argv', ['ai-shell', '--log-level', 'DEBUG', '--no-interactive']), \
             patch('src.main.AIShell') as MockShell, \
             patch('src.main.configure_logging') as mock_config_log:

            mock_shell = MockShell.return_value
            mock_shell.initialize = AsyncMock()
            mock_shell.shutdown = AsyncMock()

            await main()

            mock_config_log.assert_called_with('DEBUG', None)

    @pytest.mark.asyncio
    async def test_main_log_file(self, tmp_path):
        """Test --log-file flag"""
        log_file = tmp_path / "app.log"

        with patch('sys.argv', ['ai-shell', '--log-file', str(log_file), '--no-interactive']), \
             patch('src.main.AIShell') as MockShell, \
             patch('src.main.configure_logging') as mock_config_log:

            mock_shell = MockShell.return_value
            mock_shell.initialize = AsyncMock()
            mock_shell.shutdown = AsyncMock()

            await main()

            mock_config_log.assert_called_with('INFO', str(log_file))
