"""Comprehensive tests for main entry point."""

import pytest
import asyncio
import sys
import logging
from unittest.mock import Mock, MagicMock, patch, AsyncMock, call
from io import StringIO
from pathlib import Path

from src.main import (
    AIShell,
    configure_logging,
    print_health_check,
    execute_single_command,
    main
)


class TestAIShellInit:
    """Test AIShell initialization."""

    def test_aishell_init_no_args(self):
        """Test AIShell initializes with no arguments."""
        shell = AIShell()

        assert shell is not None
        assert shell.config is not None
        assert shell.db_path_override is None
        assert shell.core is not None
        assert shell._initialized is False

    def test_aishell_init_with_config_path(self):
        """Test AIShell initializes with custom config path."""
        with patch('src.main.ConfigManager') as mock_config:
            shell = AIShell(config_path='/custom/config.yaml')

            mock_config.assert_called_once_with(config_path='/custom/config.yaml')
            assert shell.config is not None

    def test_aishell_init_with_db_path(self):
        """Test AIShell initializes with database path override."""
        shell = AIShell(db_path='/custom/db.sqlite')

        assert shell.db_path_override == '/custom/db.sqlite'

    def test_aishell_init_both_paths(self):
        """Test AIShell initializes with both custom paths."""
        with patch('src.main.ConfigManager') as mock_config:
            shell = AIShell(config_path='/config.yaml', db_path='/db.sqlite')

            mock_config.assert_called_once_with(config_path='/config.yaml')
            assert shell.db_path_override == '/db.sqlite'

    def test_aishell_components_not_initialized(self):
        """Test AIShell components are None before initialization."""
        shell = AIShell()

        assert shell.vault is None
        assert shell.llm_manager is None
        assert shell.mcp_manager is None
        assert shell.db_module is None
        assert shell.autocomplete is None
        assert shell.optimizer is None
        assert shell.monitor is None
        assert shell.cache is None


class TestAIShellInitialize:
    """Test AIShell async initialization."""

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful initialization of all components."""
        shell = AIShell()

        with patch.object(shell.core, 'initialize', new_callable=AsyncMock) as mock_core, \
             patch('src.main.SecureVault') as mock_vault, \
             patch('src.main.LocalLLMManager') as mock_llm, \
             patch('src.main.ConnectionManager') as mock_mcp, \
             patch('src.main.PerformanceOptimizer') as mock_optimizer, \
             patch('src.main.SystemMonitor') as mock_monitor, \
             patch('src.main.QueryCache') as mock_cache, \
             patch('src.main.DatabaseModule') as mock_db:

            mock_monitor_instance = mock_monitor.return_value
            mock_monitor_instance.start_monitoring = AsyncMock()
            mock_monitor_instance.perform_health_check = AsyncMock(return_value={})

            await shell.initialize()

            assert shell._initialized is True
            mock_core.assert_called_once()
            mock_vault.assert_called_once()
            mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self):
        """Test initialize warns when already initialized."""
        shell = AIShell()
        shell._initialized = True

        with patch.object(shell.core, 'initialize', new_callable=AsyncMock) as mock_core:
            with patch('src.main.logger') as mock_logger:
                await shell.initialize()

                mock_logger.warning.assert_called_with("AI-Shell already initialized")
                mock_core.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_vault_with_config(self):
        """Test vault initialization uses config value."""
        shell = AIShell()
        shell.config.get = MagicMock(side_effect=lambda key, default: {
            'security.vault_key': 'custom-vault-key',
            'llm.model_path': '/models',
            'llm.provider': 'ollama',
            'llm.models.intent': 'llama2',
            'mcp.max_connections': 10,
            'database.path': None,
            'database.auto_confirm': False
        }.get(key, default))

        with patch.object(shell.core, 'initialize', new_callable=AsyncMock), \
             patch('src.main.SecureVault') as mock_vault, \
             patch('src.main.LocalLLMManager'), \
             patch('src.main.ConnectionManager'), \
             patch('src.main.PerformanceOptimizer'), \
             patch('src.main.SystemMonitor') as mock_monitor, \
             patch('src.main.QueryCache'), \
             patch('src.main.DatabaseModule'):

            mock_monitor.return_value.start_monitoring = AsyncMock()
            mock_monitor.return_value.perform_health_check = AsyncMock(return_value={})

            await shell.initialize()

            mock_vault.assert_called_with(master_password='custom-vault-key')

    @pytest.mark.asyncio
    async def test_initialize_llm_manager_config(self):
        """Test LLM manager initialization with config values."""
        shell = AIShell()
        shell.config.get = MagicMock(side_effect=lambda key, default: {
            'security.vault_key': 'key',
            'llm.model_path': '/custom/models',
            'llm.provider': 'huggingface',
            'llm.models.intent': 'gpt2',
            'mcp.max_connections': 10,
            'database.path': None,
            'database.auto_confirm': False
        }.get(key, default))

        with patch.object(shell.core, 'initialize', new_callable=AsyncMock), \
             patch('src.main.SecureVault'), \
             patch('src.main.LocalLLMManager') as mock_llm, \
             patch('src.main.ConnectionManager'), \
             patch('src.main.PerformanceOptimizer'), \
             patch('src.main.SystemMonitor') as mock_monitor, \
             patch('src.main.QueryCache'), \
             patch('src.main.DatabaseModule'):

            mock_llm_instance = mock_llm.return_value
            mock_monitor.return_value.start_monitoring = AsyncMock()
            mock_monitor.return_value.perform_health_check = AsyncMock(return_value={})

            await shell.initialize()

            mock_llm.assert_called_with(model_path='/custom/models')
            mock_llm_instance.initialize.assert_called_with(
                provider_type='huggingface',
                model_name='gpt2'
            )

    @pytest.mark.asyncio
    async def test_initialize_db_path_override(self):
        """Test database initialization uses path override."""
        shell = AIShell(db_path='/override/db.sqlite')
        shell.config.get = MagicMock(return_value=False)

        with patch.object(shell.core, 'initialize', new_callable=AsyncMock), \
             patch('src.main.SecureVault'), \
             patch('src.main.LocalLLMManager'), \
             patch('src.main.ConnectionManager'), \
             patch('src.main.PerformanceOptimizer'), \
             patch('src.main.SystemMonitor') as mock_monitor, \
             patch('src.main.QueryCache'), \
             patch('src.main.DatabaseModule') as mock_db:

            mock_monitor.return_value.start_monitoring = AsyncMock()
            mock_monitor.return_value.perform_health_check = AsyncMock(return_value={})

            await shell.initialize()

            mock_db.assert_called_with(
                db_path='/override/db.sqlite',
                auto_confirm=False
            )

    @pytest.mark.asyncio
    async def test_initialize_failure_raises(self):
        """Test initialization failure raises exception."""
        shell = AIShell()

        with patch.object(shell.core, 'initialize', new_callable=AsyncMock, side_effect=Exception("Init failed")):
            with pytest.raises(Exception, match="Init failed"):
                await shell.initialize()

    @pytest.mark.asyncio
    async def test_initialize_performs_health_check(self):
        """Test initialization performs health check."""
        shell = AIShell()

        health_data = {
            'component1': {'status': 'healthy'},
            'component2': {'status': 'healthy'}
        }

        with patch.object(shell.core, 'initialize', new_callable=AsyncMock), \
             patch('src.main.SecureVault'), \
             patch('src.main.LocalLLMManager'), \
             patch('src.main.ConnectionManager'), \
             patch('src.main.PerformanceOptimizer'), \
             patch('src.main.SystemMonitor') as mock_monitor, \
             patch('src.main.QueryCache'), \
             patch('src.main.DatabaseModule'):

            mock_monitor_instance = mock_monitor.return_value
            mock_monitor_instance.start_monitoring = AsyncMock()
            mock_monitor_instance.perform_health_check = AsyncMock(return_value=health_data)

            await shell.initialize()

            mock_monitor_instance.perform_health_check.assert_called_once()


class TestAIShellShutdown:
    """Test AIShell shutdown."""

    @pytest.mark.asyncio
    async def test_shutdown_success(self):
        """Test successful shutdown of all components."""
        shell = AIShell()
        shell._initialized = True
        shell.monitor = MagicMock()
        shell.monitor.stop_monitoring = AsyncMock()
        shell.cache = MagicMock()
        shell.cache.clear = AsyncMock()
        shell.llm_manager = MagicMock()
        shell.llm_manager.initialized = True

        with patch.object(shell.core, 'shutdown', new_callable=AsyncMock):
            await shell.shutdown()

            shell.monitor.stop_monitoring.assert_called_once()
            shell.cache.clear.assert_called_once()
            assert shell.llm_manager.initialized is False
            assert shell._initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_handles_errors(self):
        """Test shutdown handles errors gracefully."""
        shell = AIShell()
        shell._initialized = True
        shell.monitor = MagicMock()
        shell.monitor.stop_monitoring = AsyncMock(side_effect=Exception("Stop failed"))

        with patch.object(shell.core, 'shutdown', new_callable=AsyncMock):
            # Should not raise
            await shell.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_none_components(self):
        """Test shutdown with None components."""
        shell = AIShell()

        with patch.object(shell.core, 'shutdown', new_callable=AsyncMock):
            # Should not raise with None components
            await shell.shutdown()


class TestAIShellExecuteQuery:
    """Test query execution."""

    @pytest.mark.asyncio
    async def test_execute_query_not_initialized(self):
        """Test execute_query raises when not initialized."""
        shell = AIShell()

        with pytest.raises(RuntimeError, match="not initialized"):
            await shell.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_success(self):
        """Test successful query execution."""
        shell = AIShell()
        shell._initialized = True
        shell.optimizer = MagicMock()
        shell.optimizer.optimize_query = AsyncMock(return_value="OPTIMIZED QUERY")
        shell.optimizer.record_execution = AsyncMock()
        shell.db_module = MagicMock()
        shell.db_module.execute_query = AsyncMock(return_value={
            'result': 'success',
            'execution_time': 0.5
        })

        result = await shell.execute_query("SELECT 1")

        assert result['result'] == 'success'
        shell.optimizer.optimize_query.assert_called_with("SELECT 1")
        shell.db_module.execute_query.assert_called_with(
            query="OPTIMIZED QUERY",
            connection_id=None
        )

    @pytest.mark.asyncio
    async def test_execute_query_with_connection_id(self):
        """Test query execution with connection ID."""
        shell = AIShell()
        shell._initialized = True
        shell.optimizer = MagicMock()
        shell.optimizer.optimize_query = AsyncMock(return_value="QUERY")
        shell.optimizer.record_execution = AsyncMock()
        shell.db_module = MagicMock()
        shell.db_module.execute_query = AsyncMock(return_value={'execution_time': 0.1})

        await shell.execute_query("SELECT 1", connection_id="conn-123")

        shell.db_module.execute_query.assert_called_with(
            query="QUERY",
            connection_id="conn-123"
        )

    @pytest.mark.asyncio
    async def test_execute_query_records_metrics(self):
        """Test query execution records performance metrics."""
        shell = AIShell()
        shell._initialized = True
        shell.optimizer = MagicMock()
        shell.optimizer.optimize_query = AsyncMock(return_value="QUERY")
        shell.optimizer.record_execution = AsyncMock()
        shell.db_module = MagicMock()
        shell.db_module.execute_query = AsyncMock(return_value={'execution_time': 1.5})

        await shell.execute_query("SELECT 1")

        shell.optimizer.record_execution.assert_called_with("SELECT 1", 1.5)

    @pytest.mark.asyncio
    async def test_execute_query_failure(self):
        """Test query execution handles failures."""
        shell = AIShell()
        shell._initialized = True
        shell.optimizer = MagicMock()
        shell.optimizer.optimize_query = AsyncMock(return_value="QUERY")
        shell.db_module = MagicMock()
        shell.db_module.execute_query = AsyncMock(side_effect=Exception("DB error"))

        with pytest.raises(Exception, match="DB error"):
            await shell.execute_query("SELECT 1")


class TestConfigureLogging:
    """Test logging configuration."""

    def test_configure_logging_default(self):
        """Test configure_logging with default settings."""
        with patch('logging.basicConfig') as mock_config:
            configure_logging('INFO')

            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs['level'] == logging.INFO

    def test_configure_logging_debug(self):
        """Test configure_logging with DEBUG level."""
        with patch('logging.basicConfig') as mock_config:
            configure_logging('DEBUG')

            call_kwargs = mock_config.call_args[1]
            assert call_kwargs['level'] == logging.DEBUG

    def test_configure_logging_with_file(self):
        """Test configure_logging with log file."""
        with patch('logging.basicConfig') as mock_config, \
             patch('logging.FileHandler'):
            configure_logging('INFO', log_file='/tmp/test.log')

            call_kwargs = mock_config.call_args[1]
            assert 'handlers' in call_kwargs
            assert len(call_kwargs['handlers']) == 1

    def test_configure_logging_case_insensitive(self):
        """Test configure_logging handles lowercase levels."""
        with patch('logging.basicConfig') as mock_config:
            configure_logging('error')

            call_kwargs = mock_config.call_args[1]
            assert call_kwargs['level'] == logging.ERROR


class TestPrintHealthCheck:
    """Test health check printing."""

    @pytest.mark.asyncio
    async def test_print_health_check_healthy(self):
        """Test print_health_check with healthy status."""
        shell = MagicMock()
        shell.initialize = AsyncMock()
        shell.get_health_status = AsyncMock(return_value={
            'status': 'healthy',
            'message': 'All systems operational',
            'checks': [
                {'component': 'database', 'status': 'healthy'},
                {'component': 'cache', 'status': 'healthy'}
            ]
        })

        with patch('builtins.print'), \
             patch('sys.exit') as mock_exit:
            await print_health_check(shell)

            mock_exit.assert_called_with(0)

    @pytest.mark.asyncio
    async def test_print_health_check_unhealthy(self):
        """Test print_health_check with unhealthy status."""
        shell = MagicMock()
        shell.initialize = AsyncMock()
        shell.get_health_status = AsyncMock(return_value={
            'status': 'unhealthy',
            'message': 'System degraded',
            'checks': [{'component': 'database', 'status': 'unhealthy'}]
        })

        with patch('builtins.print'), \
             patch('sys.exit') as mock_exit:
            await print_health_check(shell)

            mock_exit.assert_called_with(1)

    @pytest.mark.asyncio
    async def test_print_health_check_error(self):
        """Test print_health_check handles errors."""
        shell = MagicMock()
        shell.initialize = AsyncMock(side_effect=Exception("Init failed"))

        with patch('builtins.print'), \
             patch('sys.exit') as mock_exit:
            await print_health_check(shell)

            mock_exit.assert_called_with(1)


class TestExecuteSingleCommand:
    """Test single command execution."""

    @pytest.mark.asyncio
    async def test_execute_single_command_query(self):
        """Test execute_single_command with query."""
        shell = MagicMock()
        shell.initialize = AsyncMock()
        shell.execute_query = AsyncMock(return_value={'result': 'data'})

        with patch('builtins.print'), \
             patch('sys.exit') as mock_exit:
            await execute_single_command(shell, "query SELECT 1")

            shell.execute_query.assert_called_with("SELECT 1")
            mock_exit.assert_called_with(0)

    @pytest.mark.asyncio
    async def test_execute_single_command_ask(self):
        """Test execute_single_command with ask."""
        shell = MagicMock()
        shell.initialize = AsyncMock()
        shell.get_ai_suggestion = AsyncMock(return_value="AI response")

        with patch('builtins.print'), \
             patch('sys.exit') as mock_exit:
            await execute_single_command(shell, "ask What is SQL?")

            shell.get_ai_suggestion.assert_called_with("What is SQL?")
            mock_exit.assert_called_with(0)

    @pytest.mark.asyncio
    async def test_execute_single_command_health(self):
        """Test execute_single_command with health."""
        shell = MagicMock()
        shell.initialize = AsyncMock()
        shell.get_health_status = AsyncMock(return_value={
            'status': 'healthy',
            'message': 'OK'
        })

        with patch('builtins.print'), \
             patch('sys.exit') as mock_exit:
            await execute_single_command(shell, "health")

            mock_exit.assert_called_with(0)

    @pytest.mark.asyncio
    async def test_execute_single_command_unknown(self):
        """Test execute_single_command with unknown command."""
        shell = MagicMock()
        shell.initialize = AsyncMock()

        with patch('builtins.print') as mock_print, \
             patch('sys.exit') as mock_exit:
            await execute_single_command(shell, "unknown command")

            # Check that error message was printed
            assert any('Unknown command' in str(call) for call in mock_print.call_args_list)
            # Should call exit(1) first, then potentially exit(0) in the else branch
            assert mock_exit.call_count >= 1
            assert mock_exit.call_args_list[0] == call(1)


class TestMain:
    """Test main entry point."""

    @pytest.mark.asyncio
    async def test_main_no_args_interactive(self):
        """Test main with no arguments starts interactive mode."""
        shell_mock = MagicMock()
        shell_mock.initialize = AsyncMock()
        shell_mock.interactive_mode = AsyncMock()
        shell_mock.shutdown = AsyncMock()

        with patch('src.main.AIShell', return_value=shell_mock), \
             patch('src.main.configure_logging'), \
             patch('sys.argv', ['ai-shell']):
            await main()

            shell_mock.initialize.assert_called_once()
            shell_mock.interactive_mode.assert_called_once()
            shell_mock.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self):
        """Test main handles keyboard interrupt."""
        shell_mock = MagicMock()
        shell_mock.initialize = AsyncMock()
        shell_mock.interactive_mode = AsyncMock(side_effect=KeyboardInterrupt())
        shell_mock.shutdown = AsyncMock()

        with patch('src.main.AIShell', return_value=shell_mock), \
             patch('src.main.configure_logging'), \
             patch('sys.argv', ['ai-shell']), \
             patch('builtins.print'):
            await main()

            shell_mock.shutdown.assert_called_once()
