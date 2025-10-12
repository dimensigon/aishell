"""Test plugin with dependencies."""


class DependentPlugin:
    """Plugin that depends on other plugins."""

    name = "dependent_plugin"
    version = "2.0.0"
    plugin_type = "extension"
    dependencies = ["test_plugin>=1.0.0", "another_plugin"]

    def __init__(self):
        """Initialize plugin."""
        self.initialized = False

    def activate(self):
        """Activate the plugin."""
        self.initialized = True
        return True

    def get_name(self):
        """Get plugin name."""
        return self.name
