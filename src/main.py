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

from .core.ai_shell import AIShellCore
from .core.config import ConfigManager
from .llm.manager import LocalLLMManager
from .mcp_clients.manager import ConnectionManager
from .database.module import DatabaseModule
from .performance.optimizer import PerformanceOptimizer
from .performance.monitor import SystemMonitor
from .performance.cache import QueryCache
from .security.vault import SecureVault
from .vector.autocomplete import IntelligentCompleter
from . import __version__

# Default logging configuration (will be updated by CLI args)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIShell:
    """Main AI-Shell application."""

    def __init__(self, config_path: Optional[str] = None, db_path: Optional[str] = None):
        """
        Initialize AI-Shell.

        Args:
            config_path: Optional custom config file path
            db_path: Optional database path override
        """
        self.config = ConfigManager(config_path=config_path) if config_path else ConfigManager()
        self.db_path_override = db_path
        self.core = AIShellCore()
        self.vault = None
        self.llm_manager = None
        self.mcp_manager = None
        self.db_module = None
        self.autocomplete = None
        self.optimizer = None
        self.monitor = None
        self.cache = None
        self._initialized = False

    async def initialize(self):
        """Initialize all components."""
        if self._initialized:
            logger.warning("AI-Shell already initialized")
            return

        logger.info("Initializing AI-Shell...")

        try:
            # Initialize core
            await self.core.initialize()
            logger.info("Core initialized")

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

            # Initialize MCP client manager
            self.mcp_manager = ConnectionManager(
                max_connections=self.config.get('mcp.max_connections', 10)
            )
            logger.info("MCP manager initialized")

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

    async def shutdown(self):
        """Shutdown all components."""
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
        """
        Execute a database query.

        Args:
            query: SQL query to execute
            connection_id: Optional connection identifier

        Returns:
            Query execution result
        """
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

    async def interactive_mode(self):
        """Run interactive shell mode."""
        if not self._initialized:
            await self.initialize()

        print("AI-Shell Interactive Mode")
        print("=" * 50)
        print("Commands:")
        print("  query <sql>    - Execute SQL query")
        print("  ask <question> - Ask AI assistant")
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

    args = parser.parse_args()

    # Configure logging based on arguments
    configure_logging(args.log_level, args.log_file)

    # Create shell instance with optional config and db path
    shell = AIShell(config_path=args.config, db_path=args.db_path)

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
