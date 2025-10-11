"""AI-Shell Plugin System.

Provides extensibility through a comprehensive plugin architecture.
"""

from .plugin_manager import (
    PluginManager,
    BasePlugin,
    PluginMetadata,
    PluginError,
    PluginLoadError,
    PluginValidationError,
    get_plugin_manager
)
from .discovery import PluginDiscovery
from .loader import PluginLoader
from .hooks import HookManager
from .dependencies import DependencyResolver
from .security import PluginSecurityManager, CodeSignatureVerifier
from .sandbox import PluginSandbox, ResourceLimiter
from .config import PluginConfig, PluginConfigManager

__all__ = [
    # Manager
    'PluginManager',
    'BasePlugin',
    'PluginMetadata',
    'PluginError',
    'PluginLoadError',
    'PluginValidationError',
    'get_plugin_manager',
    # Discovery & Loading
    'PluginDiscovery',
    'PluginLoader',
    # Hooks
    'HookManager',
    # Dependencies
    'DependencyResolver',
    # Security
    'PluginSecurityManager',
    'CodeSignatureVerifier',
    # Sandbox
    'PluginSandbox',
    'ResourceLimiter',
    # Config
    'PluginConfig',
    'PluginConfigManager',
]
