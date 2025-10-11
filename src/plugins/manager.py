"""Alias module for backward compatibility."""

# Import everything from plugin_manager for backward compatibility
from .plugin_manager import *

__all__ = ['PluginManager', 'BasePlugin', 'PluginMetadata',
           'PluginError', 'PluginLoadError', 'PluginValidationError']
