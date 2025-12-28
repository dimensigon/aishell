# Sample AI-Shell Plugin

This is a template plugin for AI-Shell that demonstrates plugin development.

## Features

- Plugin metadata and configuration
- Lifecycle management (initialize, start, stop, cleanup)
- Configuration validation
- Logging integration
- Example plugin logic

## Installation

### Manual Installation

1. Copy this directory to AI-Shell's plugin directory:
   ```bash
   cp -r sample-plugin ~/.agentic-aishell/plugins/
   ```

2. Or install globally:
   ```bash
   cp -r sample-plugin /usr/local/lib/ai-shell/plugins/
   ```

### Using AI-Shell

```bash
# Install from directory
ai-shell plugin install /path/to/sample-plugin

# Install from Git repository
ai-shell plugin install git+https://github.com/yourusername/ai-shell-sample-plugin.git
```

## Configuration

### Default Configuration

```json
{
  "greeting": "Hello from Sample Plugin!",
  "max_items": 10,
  "enable_logging": true
}
```

### Configuration Schema

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `greeting` | string | "Hello from Sample Plugin!" | Custom greeting message |
| `max_items` | integer | 10 | Maximum items to process (1-1000) |
| `enable_logging` | boolean | true | Enable detailed logging |

### Configuration File

Create `~/.agentic-aishell/plugins/sample-plugin/config.json`:

```json
{
  "greeting": "Custom greeting!",
  "max_items": 20,
  "enable_logging": true
}
```

## Usage

### Load Plugin

```bash
# Using AI-Shell CLI
ai-shell plugin load sample-plugin

# With custom config
ai-shell plugin load sample-plugin --config '{"max_items": 50}'
```

### Python API

```python
from ai_shell.plugins import get_plugin_manager

# Get plugin manager
manager = get_plugin_manager()

# Discover plugins
plugins = manager.discover_plugins()

# Load plugin
config = {
    "greeting": "Hello!",
    "max_items": 15
}
plugin = manager.load_plugin("sample-plugin", config)

# Start plugin
await manager.start_plugin("sample-plugin")

# Get plugin stats
stats = plugin.get_stats()
print(stats)

# Stop plugin
await manager.stop_plugin("sample-plugin")
```

## Development

### File Structure

```
sample-plugin/
├── plugin.json         # Plugin metadata
├── sample_plugin.py    # Plugin implementation
├── README.md           # This file
├── requirements.txt    # Python dependencies
└── tests/              # Plugin tests
    └── test_sample.py
```

### Plugin Metadata (plugin.json)

```json
{
  "name": "sample-plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Plugin description",
  "homepage": "https://github.com/...",
  "license": "MIT",
  "tags": ["tag1", "tag2"],
  "dependencies": [],
  "entry_point": "sample_plugin:SamplePlugin"
}
```

### Plugin Class

```python
from ai_shell.plugins import BasePlugin

class SamplePlugin(BasePlugin):
    @classmethod
    def get_name(cls) -> str:
        return "sample-plugin"

    @classmethod
    def get_version(cls) -> str:
        return "1.0.0"

    async def initialize(self):
        # Initialize resources
        pass

    async def start(self):
        # Start plugin work
        pass

    async def stop(self):
        # Stop plugin work
        pass

    async def cleanup(self):
        # Cleanup resources
        pass
```

### Testing

```bash
# Run tests
pytest tests/

# Run specific test
pytest tests/test_sample.py::test_plugin_initialization

# With coverage
pytest --cov=sample_plugin tests/
```

Example test:

```python
import pytest
from sample_plugin import SamplePlugin

@pytest.mark.asyncio
async def test_plugin_initialization():
    config = {"max_items": 5}
    plugin = SamplePlugin(config)

    await plugin.initialize()
    assert plugin.max_items == 5

    await plugin.cleanup()
```

## Extending This Plugin

### Add Custom Methods

```python
class SamplePlugin(BasePlugin):
    # ... existing methods ...

    async def custom_operation(self, data):
        """Custom plugin operation"""
        self.logger.info(f"Processing: {data}")
        # Your logic here
        return result
```

### Add Event Handlers

```python
from ai_shell.events import on_event

class SamplePlugin(BasePlugin):
    async def initialize(self):
        # Register event handler
        on_event("database.query", self.on_query)

    async def on_query(self, event):
        """Handle query events"""
        query = event.data["query"]
        self.logger.info(f"Query executed: {query}")
```

### Add Configuration Options

Update `plugin.json`:

```json
{
  "config_schema": {
    "properties": {
      "new_option": {
        "type": "string",
        "description": "New configuration option",
        "default": "value"
      }
    }
  }
}
```

Use in plugin:

```python
def __init__(self, config):
    super().__init__(config)
    self.new_option = config.get("new_option", "value")
```

## Best Practices

1. **Configuration Validation**: Always validate configuration in `validate_config()`
2. **Error Handling**: Use try-except blocks and log errors
3. **Resource Cleanup**: Always cleanup resources in `cleanup()`
4. **Logging**: Use `self.logger` for consistent logging
5. **Async Operations**: Use async/await for I/O operations
6. **Documentation**: Document all public methods
7. **Testing**: Write tests for all functionality
8. **Versioning**: Follow semantic versioning (MAJOR.MINOR.PATCH)

## Common Patterns

### Database Operations

```python
async def query_database(self):
    from ai_shell.database import get_database_manager

    db = get_database_manager()
    result = await db.execute("SELECT * FROM users")
    return result
```

### AI Integration

```python
async def use_ai(self, question):
    from ai_shell.ai import get_ai_client

    ai = get_ai_client()
    response = await ai.complete(question)
    return response
```

### Background Tasks

```python
import asyncio

async def start(self):
    self.is_running = True
    self.task = asyncio.create_task(self.background_work())

async def background_work(self):
    while self.is_running:
        await self.do_something()
        await asyncio.sleep(60)

async def stop(self):
    self.is_running = False
    await self.task
```

## Troubleshooting

### Plugin Won't Load

- Check `plugin.json` is valid JSON
- Verify entry_point matches class name
- Check dependencies are installed
- Review logs: `~/.agentic-aishell/logs/plugins.log`

### Configuration Errors

- Validate config against schema
- Check required fields are present
- Verify data types match schema

### Runtime Errors

- Check plugin logs
- Enable debug logging: `"enable_logging": true`
- Test plugin independently

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- Documentation: https://docs.ai-shell.io/plugins
- Issues: https://github.com/yourusername/ai-shell-sample-plugin/issues
- Community: https://discord.gg/ai-shell

## Resources

- [Plugin Development Guide](https://docs.ai-shell.io/plugins/development)
- [Plugin API Reference](https://docs.ai-shell.io/plugins/api)
- [Example Plugins](https://github.com/yourusername/ai-shell/tree/main/examples/plugins)
- [Plugin Marketplace](https://marketplace.ai-shell.io)
