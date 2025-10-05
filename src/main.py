#!/usr/bin/env python3
"""
AI-Shell main entry point.

Provides command-line interface for AI-powered database management.
"""

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIShell:
    """Main AI-Shell application."""

    def __init__(self):
        self.config = ConfigManager()
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
            db_path = self.config.get('database.path', None)
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


async def main():
    """Main entry point."""
    shell = AIShell()

    try:
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
