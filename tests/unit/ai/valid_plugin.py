"""Valid test plugin for testing plugin loader."""


class TestPlugin:
    """A simple valid test plugin."""

    name = "test_plugin"
    version = "1.0.0"
    plugin_type = "utility"
    dependencies = []

    def __init__(self):
        """Initialize plugin."""
        self.value = 42
        self.activated = False

    def activate(self):
        """Activate the plugin."""
        self.activated = True
        return True

    def deactivate(self):
        """Deactivate the plugin."""
        self.activated = False

    def get_value(self):
        """Get plugin value."""
        return self.value

    def get_version(self):
        """Get plugin version."""
        return self.version
