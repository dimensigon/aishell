"""
Sample AI-Shell Plugin

This is a template plugin that demonstrates how to create custom plugins for AI-Shell.
"""

from typing import Dict, Any
from ai_shell.plugins import BasePlugin, PluginMetadata


class SamplePlugin(BasePlugin):
    """
    Sample plugin demonstrating plugin development.

    This plugin shows how to:
    - Define plugin metadata
    - Initialize plugin resources
    - Handle configuration
    - Implement lifecycle methods
    - Interact with AI-Shell core
    """

    @classmethod
    def get_name(cls) -> str:
        """Get plugin name"""
        return "sample-plugin"

    @classmethod
    def get_version(cls) -> str:
        """Get plugin version"""
        return "1.0.0"

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        """Get plugin metadata"""
        return PluginMetadata(
            name="sample-plugin",
            version="1.0.0",
            author="AI-Shell Contributors",
            description="Sample plugin demonstrating plugin development",
            homepage="https://github.com/yourusername/ai-shell-sample-plugin",
            license="MIT",
            tags=["example", "sample", "tutorial"],
            dependencies=[],
            entry_point="sample_plugin:SamplePlugin"
        )

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize plugin.

        Args:
            config: Plugin configuration
        """
        super().__init__(config)

        # Get configuration values
        self.greeting = config.get("greeting", "Hello from Sample Plugin!")
        self.max_items = config.get("max_items", 10)
        self.enable_logging = config.get("enable_logging", True)

        # Plugin state
        self.items_processed = 0
        self.is_running = False

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if valid, False otherwise
        """
        # Check max_items range
        max_items = config.get("max_items", 10)
        if not isinstance(max_items, int) or max_items < 1 or max_items > 1000:
            self.logger.error("max_items must be between 1 and 1000")
            return False

        # Check greeting type
        greeting = config.get("greeting")
        if greeting is not None and not isinstance(greeting, str):
            self.logger.error("greeting must be a string")
            return False

        return True

    async def initialize(self):
        """
        Initialize plugin resources.

        Called when plugin is loaded, before start().
        """
        if self.enable_logging:
            self.logger.info(f"Initializing {self.get_name()} v{self.get_version()}")

        # Initialize any resources here
        # Examples:
        # - Database connections
        # - File handles
        # - Network clients
        # - Thread pools

        self.logger.info(f"Configuration: {self.config}")

    async def start(self):
        """
        Start plugin operations.

        Called after initialization to begin plugin work.
        """
        self.is_running = True

        if self.enable_logging:
            self.logger.info(f"Starting {self.get_name()}")
            self.logger.info(self.greeting)

        # Start plugin operations here
        # Examples:
        # - Start background tasks
        # - Register event handlers
        # - Begin monitoring
        # - Connect to services

        await self.do_work()

    async def do_work(self):
        """
        Perform plugin work.

        This is where the main plugin logic goes.
        """
        self.logger.info("Processing items...")

        for i in range(self.max_items):
            if not self.is_running:
                break

            # Simulate work
            await self.process_item(i)
            self.items_processed += 1

            if self.enable_logging:
                self.logger.info(f"Processed item {i+1}/{self.max_items}")

        self.logger.info(f"Completed processing {self.items_processed} items")

    async def process_item(self, item_id: int):
        """
        Process a single item.

        Args:
            item_id: Item identifier
        """
        # Example plugin work
        # This could be:
        # - Query optimization
        # - Data transformation
        # - Health checks
        # - Custom analysis
        # - etc.

        self.logger.debug(f"Processing item: {item_id}")

        # You can interact with AI-Shell core here:
        # - Execute database queries
        # - Use AI capabilities
        # - Send notifications
        # - Store metrics

    async def stop(self):
        """
        Stop plugin operations.

        Called when plugin is being shut down.
        """
        self.is_running = False

        if self.enable_logging:
            self.logger.info(f"Stopping {self.get_name()}")
            self.logger.info(f"Total items processed: {self.items_processed}")

        # Stop plugin operations here
        # Examples:
        # - Stop background tasks
        # - Unregister event handlers
        # - Disconnect from services
        # - Save state

    async def cleanup(self):
        """
        Cleanup plugin resources.

        Called after stop, before plugin is destroyed.
        """
        if self.enable_logging:
            self.logger.info(f"Cleaning up {self.get_name()}")

        # Cleanup resources here
        # Examples:
        # - Close database connections
        # - Release file handles
        # - Close network connections
        # - Free memory

    # Custom plugin methods
    # Add any custom methods your plugin needs

    def get_stats(self) -> Dict[str, Any]:
        """
        Get plugin statistics.

        Returns:
            Dictionary of plugin stats
        """
        return {
            "items_processed": self.items_processed,
            "is_running": self.is_running,
            "max_items": self.max_items,
            "greeting": self.greeting
        }

    async def reset(self):
        """Reset plugin state"""
        self.items_processed = 0
        self.logger.info("Plugin state reset")


# Example usage
if __name__ == "__main__":
    import asyncio
    import logging

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def main():
        # Create plugin with config
        config = {
            "greeting": "Hello from test!",
            "max_items": 5,
            "enable_logging": True
        }

        plugin = SamplePlugin(config)

        # Run plugin lifecycle
        await plugin.initialize()
        await plugin.start()

        # Get stats
        stats = plugin.get_stats()
        print(f"\nPlugin Stats: {stats}")

        # Cleanup
        await plugin.stop()
        await plugin.cleanup()

    asyncio.run(main())
