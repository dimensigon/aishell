#!/usr/bin/env python3
"""
AI-Shell main entry point.

Provides command-line interface for AI-powered database management.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from .core.ai_shell import AIShellCore
from .core.config import ConfigManager
from .llm.manager import LocalLLMManager
from .ai.command_suggester import CommandSuggester, CommandContext, Suggestion
from .mcp_clients.enhanced_manager import EnhancedConnectionManager
from .database.module import DatabaseModule
from .performance.optimizer import PerformanceOptimizer
from .performance.monitor import SystemMonitor
from .performance.cache import QueryCache
from .security.vault import SecureVault
from .vector.autocomplete import IntelligentCompleter
from .agents.manager import AgentManager, AgentType
from . import __version__

# Default logging configuration (will be updated by CLI args)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIShell:
    """Main AI-Shell application."""

    def __init__(self, config_path: Optional[str] = None, db_path: Optional[str] = None, mock_mode: bool = False) -> None:
        """
        Initialize AI-Shell.

        Args:
            config_path: Optional custom config file path
            db_path: Optional database path override
            mock_mode: Run in mock mode without real connections
        """
        self.mock_mode = mock_mode
        self.config = ConfigManager(config_path=config_path) if config_path else ConfigManager()
        self.db_path_override = db_path
        self.core = AIShellCore()
        self.vault = None
        self.llm_manager = None
        self.mcp_manager = None
        self.db_module = None
        self.autocomplete = None
        self.agent_manager = None
        self.optimizer = None
        self.command_suggester = None
        self.monitor = None
        self.cache = None
        self._initialized = False

    async def initialize(self) -> None:
        """Method implementation."""
        if self._initialized:
            logger.warning("AI-Shell already initialized")
            return

        logger.info(f"Initializing AI-Shell{' in MOCK mode' if self.mock_mode else ''}...")

        try:
            # Initialize core
            await self.core.initialize()
            logger.info("Core initialized")

            # In mock mode, initialize limited functionality
            if self.mock_mode:
                logger.info("Mock mode: Initializing limited functionality")

                # Initialize enhanced MCP manager even in mock mode for demo purposes
                self.mcp_manager = EnhancedConnectionManager(max_connections=10)
                logger.info("MCP manager initialized (mock mode)")

                # Initialize LLM manager with mock provider
                self.llm_manager = LocalLLMManager(model_path="/tmp/models")
                self.llm_manager.initialize("mock", "mock-model")
                logger.info("LLM manager initialized with mock provider")

                # Initialize command suggester
                self.command_suggester = CommandSuggester(llm_manager=self.llm_manager)
                logger.info("Command suggester initialized")

                self._initialized = True
                logger.info("AI-Shell mock initialization complete")
                return

            # Initialize vault
            vault_key = self.config.get('security.vault_key', 'default-key-change-me')
            self.vault = SecureVault(master_password=vault_key)
            logger.info("Vault initialized")

            # Initialize LLM manager
            model_path = self.config.get('llm.model_path', '/data0/models')
            self.llm_manager = LocalLLMManager(model_path=model_path)
            provider_type = self.config.get('llm.provider', 'ollama')
            model_name = self.config.get('llm.models.intent', 'llama2')
            self.llm_manager.initialize(provider_type=provider_type, model_name=model_name)
            logger.info("LLM manager initialized")

            # Initialize enhanced MCP client manager
            self.mcp_manager = EnhancedConnectionManager(
                max_connections=self.config.get('mcp.max_connections', 20)
            )
            logger.info("Enhanced MCP manager initialized with multi-protocol support")

            # Initialize agent manager
            self.agent_manager = AgentManager(
                llm_manager=self.llm_manager,
                performance_monitor=SystemMonitor(self.config.config),
                max_concurrent_tasks=self.config.get('agents.max_concurrent_tasks', 5)
            )
            await self.agent_manager.start()

            # Create default agents
            await self.agent_manager.create_agent(
                agent_type=AgentType.COMMAND,
                config={'allowed_commands': self.config.get('agents.allowed_commands', ['ls', 'cat', 'grep'])}
            )
            await self.agent_manager.create_agent(
                agent_type=AgentType.RESEARCH,
                config={'max_results': self.config.get('agents.research.max_results', 10)}
            )
            await self.agent_manager.create_agent(
                agent_type=AgentType.CODE,
                config={'languages': self.config.get('agents.code.languages', ['python', 'javascript', 'sql'])}
            )
            await self.agent_manager.create_agent(
                agent_type=AgentType.ANALYSIS
            )
            logger.info("Agent manager initialized with default agents")

            # Initialize performance components
            self.optimizer = PerformanceOptimizer(self.config.config)
            self.monitor = SystemMonitor(self.config.config)
            self.cache = QueryCache(self.config.config)

            # Start monitoring
            await self.monitor.start_monitoring()
            logger.info("Monitoring started")

            # Initialize database module
            db_path = self.db_path_override or self.config.get('database.path', None)
            self.db_module = DatabaseModule(
                db_path=db_path,
                auto_confirm=self.config.get('database.auto_confirm', False)
            )
            # Note: DatabaseModule doesn't have async initialize, already ready
            logger.info("Database module initialized")

            # Initialize autocomplete (requires VectorDatabase instance)
            # Note: IntelligentCompleter requires VectorDatabase, skipping for now
            # TODO: Initialize VectorDatabase first, then create IntelligentCompleter
            self.autocomplete = None
            logger.info("Autocomplete initialization skipped (requires VectorDatabase)")

            self._initialized = True
            logger.info("AI-Shell initialization complete")

            # Perform initial health check
            health = await self.monitor.perform_health_check()
            for component, check in health.items():
                logger.info(f"Health check - {component}: {check}")

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown AI-Shell application and cleanup resources."""
        logger.info("Shutting down AI-Shell...")

        try:
            # Stop monitoring
            if self.monitor:
                await self.monitor.stop_monitoring()

            # Database module cleanup (no async shutdown method)
            if self.db_module:
                pass  # DatabaseModule doesn't have shutdown method

            # LLM manager cleanup (no async shutdown needed)
            if self.llm_manager:
                self.llm_manager.initialized = False

            # Clear cache
            if self.cache:
                await self.cache.clear()

            # Shutdown core
            await self.core.shutdown()

            self._initialized = False
            logger.info("AI-Shell shutdown complete")

        except Exception as e:
            logger.error(f"Shutdown error: {e}")

    async def execute_query(self, query: str, connection_id: Optional[str] = None) -> dict:
        """Execute a database query and return results."""
        if not self._initialized:
            raise RuntimeError("AI-Shell not initialized. Call initialize() first.")

        try:
            # Optimize query
            optimized_query = await self.optimizer.optimize_query(query)

            # Execute through database module
            result = await self.db_module.execute_query(
                query=optimized_query,
                connection_id=connection_id
            )

            # Record metrics
            execution_time = result.get('execution_time', 0)
            await self.optimizer.record_execution(query, execution_time)

            return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def get_ai_suggestion(self, question: str, context: Optional[dict] = None) -> str:
        """
        Get AI suggestion for database operation.

        Args:
            question: User question
            context: Optional context information

        Returns:
            AI-generated suggestion
        """
        if not self._initialized:
            raise RuntimeError("AI-Shell not initialized. Call initialize() first.")

        try:
            # Use intent model for suggestions
            response = await self.llm_manager.generate_response(
                prompt=question,
                model_type='intent',
                context=context
            )
            return response

        except Exception as e:
            logger.error(f"AI suggestion failed: {e}")
            raise

    async def get_health_status(self) -> dict:
        """
        Get current system health status.

        Returns:
            Health status summary
        """
        if not self._initialized:
            raise RuntimeError("AI-Shell not initialized. Call initialize() first.")

        return await self.monitor.get_health_summary()

    async def get_performance_metrics(self) -> dict:
        """
        Get performance metrics.

        Returns:
            Performance metrics summary
        """
        if not self._initialized:
            raise RuntimeError("AI-Shell not initialized. Call initialize() first.")

        optimizer_metrics = await self.optimizer.get_metrics()
        cache_stats = await self.cache.get_stats()
        monitor_metrics = await self.monitor.get_metrics_summary()

        return {
            'optimizer': {
                'query_count': optimizer_metrics.query_count,
                'avg_execution_time': optimizer_metrics.avg_execution_time,
                'slow_queries': optimizer_metrics.slow_queries
            },
            'cache': cache_stats,
            'system': monitor_metrics
        }

    async def interactive_mode(self) -> None:
        """Method implementation."""
        if not self._initialized:
            await self.initialize()

        print("AI-Shell Interactive Mode")
        print("=" * 50)
        print("Commands:")
        print("  query <sql>    - Execute SQL query")
        print("  ask <question> - Ask AI assistant")
        print("  agent <task>   - Delegate task to intelligent agents")
        print("  agents         - List available agents")
        print("  mcp resources  - List available MCP resources")
        print("  mcp tools      - List available MCP tools")
        print("  mcp connect    - Create MCP connection")
        print("  mcp status     - Show MCP connection status")
        print("  llm providers  - List available LLM providers")
        print("  llm switch     - Switch LLM provider")
        print("  llm status     - Show current LLM provider")
        print("  llm generate   - Generate text with LLM")
        print("  suggest        - Get command suggestions")
        print("  help [cmd]     - Get help on commands")
        print("  history        - Show command history")
        print("  health         - Show health status")
        print("  metrics        - Show performance metrics")
        print("  exit           - Exit shell")
        print("=" * 50)

        while True:
            try:
                user_input = input("\nai-shell> ").strip()

                if not user_input:
                    continue

                if user_input.lower() == 'exit':
                    break

                # LLM Commands
                if user_input == 'llm providers':
                    if not self.llm_manager:
                        print("\nLLM manager not available.")
                        continue
                    providers = self.llm_manager.list_providers()
                    print("\nAvailable LLM Providers:")
                    for provider in providers:
                        print(f"  - {provider}")
                    continue

                if user_input == 'llm status':
                    if not self.llm_manager:
                        print("\nLLM manager not available.")
                        continue
                    if self.llm_manager.provider:
                        print(f"\nCurrent Provider: {self.llm_manager.provider.__class__.__name__}")
                        print(f"Model: {self.llm_manager.provider.model_name}")
                        print(f"Initialized: {self.llm_manager.initialized}")
                    else:
                        print("\nNo LLM provider currently active")
                    continue

                if user_input.startswith('llm switch'):
                    if not self.llm_manager:
                        print("\nLLM manager not available.")
                        continue
                    parts = user_input.split()
                    if len(parts) < 3:
                        print("\nUsage: llm switch <provider> [model] [api_key]")
                        print("Example: llm switch ollama llama2")
                        print("Example: llm switch openai gpt-3.5-turbo YOUR_API_KEY")
                        continue
                    provider = parts[2]
                    model = parts[3] if len(parts) > 3 else "default-model"
                    api_key = parts[4] if len(parts) > 4 else None

                    success = self.llm_manager.switch_provider(provider, model, api_key)
                    if success:
                        print(f"\n✓ Switched to {provider} with model {model}")
                    else:
                        print(f"\n✗ Failed to switch to {provider}")
                    continue

                if user_input.startswith('llm generate'):
                    if not self.llm_manager or not self.llm_manager.initialized:
                        print("\nLLM not initialized. Use 'llm switch' to select a provider.")
                        continue
                    prompt = user_input[12:].strip()
                    if not prompt:
                        print("\nUsage: llm generate <prompt>")
                        continue
                    try:
                        response = self.llm_manager.provider.generate(prompt, max_tokens=200)
                        print(f"\n{response}")
                    except Exception as e:
                        print(f"\nError generating text: {e}")
                    continue

                # Command suggestions
                if user_input.lower() == 'suggest' or user_input == '?':
                    if not self.command_suggester:
                        print("\nCommand suggester not available.")
                        continue

                    # Build context
                    context = CommandContext(
                        current_command="",
                        command_history=list(self.command_suggester.command_history)[-5:],
                        active_connections=list(self.mcp_manager._connections.keys()) if self.mcp_manager else [],
                        session_duration=(datetime.now() - self.command_suggester.session_start).total_seconds()
                    )

                    suggestions = self.command_suggester.get_suggestions(context)

                    if suggestions:
                        print("\nSuggested commands:")
                        for i, suggestion in enumerate(suggestions, 1):
                            print(f"  {i}. {suggestion.command}")
                            print(f"     {suggestion.description} (confidence: {suggestion.confidence:.0%})")
                            if suggestion.usage_example:
                                print(f"     Example: {suggestion.usage_example}")
                    else:
                        print("\nNo suggestions available. Type 'help' for command list.")
                    continue

                if user_input.lower() == 'history':
                    if not self.command_suggester:
                        print("\nCommand history not available.")
                        continue

                    history = list(self.command_suggester.command_history)
                    if history:
                        print("\nCommand History (last 20):")
                        for i, cmd in enumerate(history[-20:], 1):
                            print(f"  {i:2}. {cmd}")
                    else:
                        print("\nNo command history yet.")
                    continue

                if user_input.startswith('help'):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) > 1:
                        # Help for specific command
                        if self.command_suggester:
                            explanation = self.command_suggester.explain_command(parts[1])
                            print(f"\n{explanation}")
                        else:
                            print(f"\nNo help available for '{parts[1]}'")
                    else:
                        # General help
                        if self.command_suggester:
                            help_text = self.command_suggester.get_command_help()
                            print(f"\n{help_text}")
                        else:
                            # Fallback to basic help
                            print("\nUse 'suggest' for command suggestions or type a command.")
                    continue

                # Track command in history (after processing special commands above)
                if self.command_suggester and user_input and not user_input.startswith(('suggest', 'help', 'history')):
                    self.command_suggester.add_to_history(user_input)

                if user_input.lower() == 'health':
                    health = await self.get_health_status()
                    print(f"\nSystem Status: {health['status']}")
                    print(f"Message: {health['message']}")
                    for check in health['checks']:
                        print(f"  - {check['component']}: {check['status']}")
                    continue

                if user_input.lower() == 'metrics':
                    metrics = await self.get_performance_metrics()
                    print("\nPerformance Metrics:")
                    print(f"  Queries: {metrics['optimizer']['query_count']}")
                    print(f"  Avg Time: {metrics['optimizer']['avg_execution_time']:.3f}s")
                    print(f"  Cache Hit Rate: {metrics['cache']['hit_rate']:.1%}")
                    continue

                if user_input.startswith('query '):
                    query = user_input[6:].strip()
                    result = await self.execute_query(query)
                    print(f"\nResult: {result}")
                    continue

                if user_input.startswith('ask '):
                    question = user_input[4:].strip()
                    suggestion = await self.get_ai_suggestion(question)
                    print(f"\nAI: {suggestion}")
                    continue

                if user_input.lower() == 'agents':
                    if not self.agent_manager:
                        print("\nAgents not available in mock mode.")
                        continue
                    agents = await self.agent_manager.list_agents()
                    print("\nAvailable Agents:")
                    for agent_id, agent_info in agents.items():
                        print(f"  - {agent_info['type'].value}: {agent_info['status']} (ID: {agent_id[:8]}...)")
                    continue

                if user_input.startswith('agent '):
                    if not self.agent_manager:
                        print("\nAgents not available in mock mode.")
                        continue
                    task_desc = user_input[6:].strip()
                    if not task_desc:
                        print("Please provide a task description after 'agent'")
                        continue

                    # Submit task to agent manager for automatic delegation
                    from src.agents.base import TaskContext
                    task_context = TaskContext(
                        task_id=f"user-task-{asyncio.get_event_loop().time():.0f}",
                        task_description=task_desc,
                        input_data={'user_request': task_desc},
                        metadata={'source': 'interactive_cli'}
                    )

                    try:
                        task_id = await self.agent_manager.submit_task(task_context)
                        print(f"\nTask submitted (ID: {task_id[:8]}...). Processing...")

                        # Wait for task completion with timeout
                        for _ in range(30):  # 30 second timeout
                            status = await self.agent_manager.get_task_status(task_id)
                            if status['status'] == 'completed':
                                result = status.get('result', {})
                                print(f"\n✓ Task completed by {status['agent_type']} agent")
                                print(f"Result: {result.get('output', 'No output available')}")
                                break
                            elif status['status'] == 'failed':
                                print(f"\n✗ Task failed: {status.get('error', 'Unknown error')}")
                                break
                            await asyncio.sleep(1)
                        else:
                            print("\n⚠ Task timed out")
                    except Exception as e:
                        print(f"\nError executing task: {e}")
                    continue

                if user_input == 'mcp resources':
                    if not self.mcp_manager:
                        print("\nMCP manager not available.")
                        continue
                    resources = await self.mcp_manager.list_resources()
                    print("\nAvailable MCP Resources:")
                    print("-" * 40)
                    for resource in resources:
                        print(f"• {resource.name} ({resource.protocol.value})")
                        print(f"  URI: {resource.uri}")
                        print(f"  {resource.description}")
                    continue

                if user_input == 'mcp tools':
                    if not self.mcp_manager:
                        print("\nMCP manager not available.")
                        continue
                    tools = await self.mcp_manager.list_tools()
                    print("\nAvailable MCP Tools:")
                    print("-" * 40)
                    for tool in tools:
                        print(f"• {tool.name}")
                        print(f"  {tool.description}")
                        print(f"  Protocol: {tool.protocol.value}")
                    continue

                if user_input == 'mcp status':
                    if not self.mcp_manager:
                        print("\nMCP manager not available.")
                        continue
                    stats = await self.mcp_manager.get_connection_stats()
                    print("\nMCP Connection Status:")
                    print("-" * 40)
                    print(f"Total Connections: {stats['total_connections']}/{stats['max_connections']}")
                    print(f"Available Resources: {stats['resources_available']}")
                    print(f"Available Tools: {stats['tools_available']}")
                    if stats['connections_by_type']:
                        print("\nConnections by Type:")
                        for conn_type, count in stats['connections_by_type'].items():
                            print(f"  {conn_type}: {count}")
                    if stats['connections_by_state']:
                        print("\nConnections by State:")
                        for state, count in stats['connections_by_state'].items():
                            print(f"  {state}: {count}")
                    continue

                if user_input == 'mcp connect':
                    print("\nCreate MCP Connection")
                    print("Available types: database, api, storage, queue")
                    conn_type = input("Connection type: ").strip()
                    conn_id = input("Connection ID: ").strip()
                    host = input("Host: ").strip()
                    port = input("Port (default 443): ").strip() or "443"

                    from .mcp_clients.base import ConnectionConfig
                    config = ConnectionConfig(
                        host=host,
                        port=int(port),
                        database=input("Database/Bucket/Queue name: ").strip(),
                        username=input("Username: ").strip(),
                        password=input("Password: ").strip()
                    )

                    try:
                        await self.mcp_manager.create_connection(conn_id, conn_type, config)
                        print(f"\n✓ Connection '{conn_id}' created successfully")
                    except Exception as e:
                        print(f"\n✗ Failed to create connection: {e}")
                    continue

                print("Unknown command. Type 'exit' to quit.")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
            except Exception as e:
                print(f"\nError: {e}")


def configure_logging(log_level: str, log_file: Optional[str] = None):
    """
    Configure logging based on CLI arguments.

    Args:
        log_level: Logging level (DEBUG/INFO/WARNING/ERROR)
        log_file: Optional log file path
    """
    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure handlers
    handlers = []
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    else:
        handlers.append(logging.StreamHandler(sys.stdout))

    # Reconfigure logging
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True
    )


async def print_health_check(shell: AIShell):
    """Print health check results and exit."""
    print("Running health checks...")
    print("=" * 60)

    try:
        await shell.initialize()
        health = await shell.get_health_status()

        print(f"\nOverall Status: {health['status']}")
        print(f"Message: {health['message']}")
        print("\nComponent Checks:")
        print("-" * 60)

        for check in health['checks']:
            status_icon = "✓" if check['status'] == 'healthy' else "✗"
            print(f"  {status_icon} {check['component']}: {check['status']}")
            if 'details' in check:
                print(f"    Details: {check['details']}")

        print("\n" + "=" * 60)

        # Exit with appropriate code
        exit_code = 0 if health['status'] == 'healthy' else 1
        sys.exit(exit_code)

    except Exception as e:
        print(f"\nHealth check failed: {e}")
        sys.exit(1)


async def execute_single_command(shell: AIShell, command: str):
    """Execute a single command and exit."""
    try:
        await shell.initialize()

        # Parse command type
        command = command.strip()

        if command.lower().startswith('query '):
            query = command[6:].strip()
            result = await shell.execute_query(query)
            print(f"Result: {result}")

        elif command.lower().startswith('ask '):
            question = command[4:].strip()
            suggestion = await shell.get_ai_suggestion(question)
            print(f"AI: {suggestion}")

        elif command.lower() == 'health':
            health = await shell.get_health_status()
            print(f"Status: {health['status']}")
            print(f"Message: {health['message']}")

        elif command.lower() == 'metrics':
            metrics = await shell.get_performance_metrics()
            print("Performance Metrics:")
            print(f"  Queries: {metrics['optimizer']['query_count']}")
            print(f"  Avg Time: {metrics['optimizer']['avg_execution_time']:.3f}s")
            print(f"  Cache Hit Rate: {metrics['cache']['hit_rate']:.1%}")

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

        sys.exit(0)

    except Exception as e:
        print(f"Command execution failed: {e}")
        sys.exit(1)


async def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="AI-Shell - AI-powered database management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-shell                                    # Start interactive mode
  ai-shell --health-check                     # Run health checks
  ai-shell --execute "query SELECT * FROM t"  # Execute single query
  ai-shell --config /path/to/config.yaml      # Use custom config
  ai-shell --log-level DEBUG --log-file app.log  # Debug logging to file
  ai-shell --no-interactive --execute "health"   # Non-interactive health check

For more information, visit: https://github.com/yourusername/AIShell
        """
    )

    # Version
    parser.add_argument(
        '--version',
        action='version',
        version=f'AI-Shell {__version__}'
    )

    # Configuration
    parser.add_argument(
        '--config',
        type=str,
        metavar='PATH',
        help='Path to custom configuration file'
    )

    parser.add_argument(
        '--db-path',
        type=str,
        metavar='PATH',
        help='Database path override (overrides config file setting)'
    )

    parser.add_argument(
        '--mock',
        action='store_true',
        help='Run in mock mode without real database/LLM connections'
    )

    # Execution modes
    parser.add_argument(
        '--no-interactive',
        action='store_true',
        help='Disable interactive mode (for scripts/automation)'
    )

    parser.add_argument(
        '--execute',
        type=str,
        metavar='COMMAND',
        help='Execute single command and exit (e.g., "query SELECT * FROM table")'
    )

    parser.add_argument(
        '--health-check',
        action='store_true',
        help='Run health checks only and exit (exit code 0=healthy, 1=unhealthy)'
    )

    # Logging
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        metavar='PATH',
        help='Log to file instead of stdout'
    )

    # Cognitive features subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Memory commands
    memory_parser = subparsers.add_parser('memory', help='Cognitive Memory commands')
    memory_subparsers = memory_parser.add_subparsers(dest='memory_command', help='Memory operations')

    memory_recall = memory_subparsers.add_parser('recall', help='Recall similar commands')
    memory_recall.add_argument('query', type=str, help='Search query')
    memory_recall.add_argument('--limit', type=int, default=5, help='Max results')
    memory_recall.add_argument('--threshold', type=float, default=0.7, help='Similarity threshold')

    memory_insights = memory_subparsers.add_parser('insights', help='Get memory insights')
    memory_insights.add_argument('--json-output', action='store_true', help='Output as JSON')

    memory_suggest = memory_subparsers.add_parser('suggest', help='Get command suggestions')
    memory_suggest.add_argument('-c', '--context', type=str, help='Context as JSON string')

    memory_export = memory_subparsers.add_parser('export', help='Export knowledge base')
    memory_export.add_argument('output_file', type=str, help='Output file path')

    memory_import = memory_subparsers.add_parser('import', help='Import knowledge base')
    memory_import.add_argument('input_file', type=str, help='Input file path')

    # Anomaly detection commands
    anomaly_parser = subparsers.add_parser('anomaly', help='Anomaly Detection commands')
    anomaly_subparsers = anomaly_parser.add_subparsers(dest='anomaly_command', help='Anomaly operations')

    anomaly_start = anomaly_subparsers.add_parser('start', help='Start monitoring')
    anomaly_start.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    anomaly_start.add_argument('--no-auto-fix', action='store_true', help='Disable auto-remediation')

    anomaly_status = anomaly_subparsers.add_parser('status', help='Show status')
    anomaly_status.add_argument('--json-output', action='store_true', help='Output as JSON')

    anomaly_check = anomaly_subparsers.add_parser('check', help='Run immediate check')

    # ADA commands
    ada_parser = subparsers.add_parser('ada', help='Autonomous DevOps Agent commands')
    ada_subparsers = ada_parser.add_subparsers(dest='ada_command', help='ADA operations')

    ada_start = ada_subparsers.add_parser('start', help='Start ADA')
    ada_start.add_argument('--interval', type=int, default=300, help='Check interval in seconds')

    ada_status = ada_subparsers.add_parser('status', help='Show ADA status')
    ada_status.add_argument('--json-output', action='store_true', help='Output as JSON')

    ada_analyze = ada_subparsers.add_parser('analyze', help='Analyze infrastructure')

    ada_optimize = ada_subparsers.add_parser('optimize', help='Find and apply optimizations')
    ada_optimize.add_argument('--dry-run', action='store_true', help='Simulate without executing')
    ada_optimize.add_argument('--type', type=str, choices=['cost', 'performance', 'reliability'], help='Optimization type')

    args = parser.parse_args()

    # Configure logging based on arguments
    configure_logging(args.log_level, args.log_file)

    # Handle cognitive feature commands before creating shell
    if args.command == 'memory':
        from .cli.cognitive_handlers import handle_memory_command
        await handle_memory_command(args)
        return
    elif args.command == 'anomaly':
        from .cli.cognitive_handlers import handle_anomaly_command
        await handle_anomaly_command(args)
        return
    elif args.command == 'ada':
        from .cli.cognitive_handlers import handle_ada_command
        await handle_ada_command(args)
        return

    # Create shell instance with optional config, db path, and mock mode
    shell = AIShell(config_path=args.config, db_path=args.db_path, mock_mode=args.mock)

    try:
        # Handle different execution modes
        if args.health_check:
            await print_health_check(shell)
            # print_health_check calls sys.exit, won't reach here

        elif args.execute:
            await execute_single_command(shell, args.execute)
            # execute_single_command calls sys.exit, won't reach here

        elif args.no_interactive:
            # Non-interactive mode: just initialize and exit
            logger.info("Running in non-interactive mode")
            await shell.initialize()
            logger.info("Initialization complete. Exiting.")

        else:
            # Default: interactive mode
            await shell.initialize()
            await shell.interactive_mode()

    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        await shell.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
