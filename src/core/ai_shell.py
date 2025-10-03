"""
AI-Shell Core Application

Central orchestrator managing module lifecycle, MCP clients, and UI state.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .event_bus import AsyncEventBus
from .config import ConfigManager

logger = logging.getLogger(__name__)


class AIShellCore:
    """
    Central orchestrator for AI-Shell application.

    Manages:
    - Module registry and lifecycle
    - MCP client connections
    - Event bus communication
    - Application configuration
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize AI-Shell core.

        Args:
            config_path: Optional path to configuration file
        """
        self.modules: Dict[str, Any] = {}
        self.mcp_clients: Dict[str, Any] = {}
        self.event_bus: Optional[AsyncEventBus] = None
        self.config: Optional[ConfigManager] = None
        self.config_path = config_path
        self.initialized = False

        logger.info("AI-Shell Core created")

    async def initialize(self) -> None:
        """
        Initialize all core components.

        This includes:
        - Event bus setup
        - Configuration loading
        - Module registry initialization
        """
        if self.initialized:
            logger.warning("AI-Shell Core already initialized")
            return

        # Initialize event bus
        self.event_bus = AsyncEventBus()
        await self.event_bus.start()
        logger.info("Event bus initialized")

        # Initialize configuration
        self.config = ConfigManager(self.config_path)
        await self.config.load()
        logger.info("Configuration loaded")

        # Initialize module registry
        self.modules = {}
        logger.info("Module registry initialized")

        self.initialized = True
        logger.info("AI-Shell Core initialization complete")

    def register_module(self, module: Any) -> None:
        """
        Register a module with the core.

        Args:
            module: Module instance to register

        Raises:
            ValueError: If module has no name attribute
            KeyError: If module with same name already registered
        """
        if not hasattr(module, 'name'):
            raise ValueError("Module must have 'name' attribute")

        module_name = module.name

        if module_name in self.modules:
            raise KeyError(f"Module '{module_name}' already registered")

        self.modules[module_name] = module
        logger.info(f"Module '{module_name}' registered")

    def unregister_module(self, module_name: str) -> None:
        """
        Unregister a module from the core.

        Args:
            module_name: Name of module to unregister

        Raises:
            KeyError: If module not found
        """
        if module_name not in self.modules:
            raise KeyError(f"Module '{module_name}' not found")

        del self.modules[module_name]
        logger.info(f"Module '{module_name}' unregistered")

    def get_module(self, module_name: str) -> Any:
        """
        Get a registered module by name.

        Args:
            module_name: Name of module to retrieve

        Returns:
            Module instance

        Raises:
            KeyError: If module not found
        """
        if module_name not in self.modules:
            raise KeyError(f"Module '{module_name}' not found")

        return self.modules[module_name]

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the application.

        This includes:
        - Stopping event bus
        - Disconnecting MCP clients
        - Cleaning up modules
        """
        logger.info("Shutting down AI-Shell Core")

        # Stop event bus
        if self.event_bus:
            await self.event_bus.stop()
            logger.info("Event bus stopped")

        # Clear modules
        self.modules.clear()
        logger.info("Modules cleared")

        self.initialized = False
        logger.info("AI-Shell Core shutdown complete")
