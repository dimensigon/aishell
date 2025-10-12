# Custom Command Development Guide

## Overview

AI-Shell provides a powerful plugin system for developing custom commands and modules. This guide covers creating custom commands, integrating AI capabilities, and extending the shell with new functionality.

## Command Architecture

### Command Types

1. **Simple Commands**: Single function execution
2. **Interactive Commands**: User input and multi-step workflows
3. **Agentic Commands**: AI-powered multi-step automation
4. **Module Commands**: Complex functionality with subcommands

## Creating Simple Commands

### Basic Command Structure

```python
# ~/.agentic-aishell/plugins/hello.py
from ai_shell.core.command import Command
from ai_shell.core.context import ExecutionContext

class HelloCommand(Command):
    """Simple greeting command"""

    name = "hello"
    description = "Greet the user"
    usage = "hello [name]"

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        """Execute the command"""
        name = args[0] if args else "World"
        return f"Hello, {name}!"

# Register command
def register(shell):
    return HelloCommand()
```

### Command Metadata

```python
class MyCommand(Command):
    # Basic metadata
    name = "mycommand"
    description = "Description of what the command does"
    usage = "mycommand [options] <args>"

    # Categories for organization
    category = "utilities"  # utilities, database, system, ai, custom

    # Aliases
    aliases = ["mc", "mycmd"]

    # Permissions
    requires_sudo = False

    # Help text
    help_text = """
    Detailed help information for the command.

    Examples:
        mycommand arg1 arg2
        mycommand --option value
    """
```

### Argument Parsing

```python
from ai_shell.core.arguments import ArgumentParser

class MyCommand(Command):
    def __init__(self):
        super().__init__()
        self.parser = ArgumentParser(prog=self.name)

        # Positional arguments
        self.parser.add_argument('input', help='Input file')

        # Optional arguments
        self.parser.add_argument('--output', '-o', help='Output file')
        self.parser.add_argument('--verbose', '-v', action='store_true')

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        # Parse arguments
        parsed = self.parser.parse_args(args)

        if parsed.verbose:
            ctx.output.write("Verbose mode enabled")

        return f"Processing {parsed.input}"
```

## Interactive Commands

### User Input

```python
from ai_shell.ui.input import UserInput

class InteractiveCommand(Command):
    name = "setup"

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        # Prompt for input
        name = await UserInput.prompt("Enter your name: ")
        email = await UserInput.prompt("Enter your email: ")

        # Confirmation
        confirm = await UserInput.confirm(
            f"Create user {name} ({email})?",
            default=True
        )

        if confirm:
            return self._create_user(name, email)
        else:
            return "Cancelled"

    # Password input (hidden)
    async def get_password(self):
        password = await UserInput.prompt(
            "Enter password: ",
            is_password=True
        )
        return password

    # Choice selection
    async def select_option(self):
        choice = await UserInput.select(
            "Select database type:",
            choices=['Oracle', 'PostgreSQL', 'MySQL']
        )
        return choice
```

### Progress Indication

```python
from ai_shell.ui.progress import Progress

class LongRunningCommand(Command):
    name = "process"

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        items = self._get_items_to_process()

        # Progress bar
        async with Progress() as progress:
            task = progress.add_task(
                "Processing items",
                total=len(items)
            )

            for item in items:
                await self._process_item(item)
                progress.update(task, advance=1)

        return f"Processed {len(items)} items"

    # Spinner for indeterminate progress
    async def fetch_data(self):
        async with Progress.spinner("Fetching data...") as spinner:
            data = await self._fetch_from_api()
        return data
```

## AI-Powered Commands

### Using LLM Integration

```python
from ai_shell.ai.llm_manager import LLMManager

class AICommand(Command):
    name = "analyze"

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        file_path = args[0]
        content = await self._read_file(file_path)

        # Get LLM instance
        llm = ctx.llm_manager

        # Analyze with AI
        prompt = f"""
        Analyze this code and provide:
        1. Summary of functionality
        2. Potential issues
        3. Optimization suggestions

        Code:
        {content}
        """

        # Use local LLM for privacy
        analysis = await llm.query(
            prompt,
            model="intent",  # Uses configured intent model
            provider="ollama"  # Force local
        )

        return analysis
```

### Agentic Commands

```python
from ai_shell.ai.agent import Agent, Tool

class AgenticCommand(Command):
    name = "autobuild"

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        description = ' '.join(args)

        # Create agent with tools
        agent = Agent(
            name="build-agent",
            llm_manager=ctx.llm_manager,
            tools=[
                Tool("file_read", self._read_file),
                Tool("file_write", self._write_file),
                Tool("run_command", self._run_command),
                Tool("run_tests", self._run_tests)
            ]
        )

        # Agent analyzes and executes
        result = await agent.execute(
            task=f"Build project: {description}",
            context=ctx
        )

        return result.summary

    async def _read_file(self, path: str) -> str:
        """Tool: Read file contents"""
        # Implementation
        pass

    async def _write_file(self, path: str, content: str) -> bool:
        """Tool: Write file"""
        # Implementation
        pass
```

### Semantic Command Search

```python
from ai_shell.core.vector_store import VectorStore

class SmartCommand(Command):
    name = "find"

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        query = ' '.join(args)

        # Vector similarity search
        vector_store = ctx.vector_store

        # Find similar commands
        similar = await vector_store.search(
            query=query,
            k=5,
            filters={'type': 'command'}
        )

        # Display results
        ctx.output.write("Similar commands:")
        for item in similar:
            ctx.output.write(
                f"  {item['name']}: {item['description']} "
                f"(similarity: {item['score']:.2%})"
            )

        return ""
```

## Database Commands

### Database Module Integration

```python
from ai_shell.modules.database import DatabaseContext

class DatabaseCommand(Command):
    name = "dbexport"
    category = "database"

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        # Get active database connection
        db_ctx = ctx.get_module_context('database')

        if not db_ctx.is_connected():
            return "Error: Not connected to database"

        # Execute query
        query = "SELECT * FROM users WHERE active = true"
        result = await db_ctx.execute(query)

        # Export to file
        output_file = args[0] if args else "export.csv"
        await self._export_csv(result, output_file)

        return f"Exported {result.rowcount} rows to {output_file}"

    async def _export_csv(self, result, filename):
        """Export result to CSV"""
        import csv
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(result.columns)
            writer.writerows(result.rows)
```

### SQL Risk Analysis

```python
from ai_shell.modules.database.risk import RiskAnalyzer

class RiskyCommand(Command):
    name = "dbcleanup"

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        sql = "DELETE FROM logs WHERE date < NOW() - INTERVAL '30 days'"

        # Analyze risk
        risk_analyzer = RiskAnalyzer()
        risk = await risk_analyzer.analyze(sql)

        # Show risk assessment
        ctx.module_panel.update({
            'risk_level': risk.level,
            'affected_rows': risk.estimated_rows,
            'recommendations': risk.recommendations
        })

        # Require confirmation for high risk
        if risk.level == 'HIGH':
            confirm = await UserInput.confirm(
                f"This will delete ~{risk.estimated_rows} rows. "
                "Type 'DELETE CONFIRMED' to proceed: ",
                exact_match="DELETE CONFIRMED"
            )
            if not confirm:
                return "Cancelled"

        # Execute
        db_ctx = ctx.get_module_context('database')
        result = await db_ctx.execute(sql)

        return f"Deleted {result.rowcount} rows"
```

## Module Development

### Creating a Custom Module

```python
# ~/.agentic-aishell/plugins/monitoring/__init__.py
from ai_shell.core.module import Module
from ai_shell.core.context import ExecutionContext

class MonitoringModule(Module):
    """System monitoring module"""

    name = "monitoring"
    description = "System performance monitoring"
    version = "1.0.0"

    def __init__(self):
        super().__init__()
        self.metrics = {}

    async def initialize(self, ctx: ExecutionContext):
        """Module initialization"""
        # Start background monitoring
        ctx.event_bus.subscribe('command_executed', self.track_metric)

        # Load saved metrics
        self.metrics = await self._load_metrics()

    async def track_metric(self, event):
        """Track command execution metrics"""
        self.metrics[event.command] = {
            'count': self.metrics.get(event.command, {}).get('count', 0) + 1,
            'avg_time': event.execution_time
        }

    def get_panel_info(self, ctx: ExecutionContext) -> dict:
        """Information displayed in module panel"""
        return {
            'title': 'System Monitoring',
            'items': [
                f"Commands executed: {sum(m['count'] for m in self.metrics.values())}",
                f"Avg execution time: {self._avg_time():.2f}s"
            ]
        }

# Register module
def register(shell):
    return MonitoringModule()
```

### Module Commands

```python
# ~/.agentic-aishell/plugins/monitoring/commands.py
from ai_shell.core.command import Command

class StatsCommand(Command):
    name = "stats"
    module = "monitoring"  # Associate with module

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        # Get module instance
        monitoring = ctx.get_module('monitoring')

        # Display statistics
        ctx.output.write("Command Statistics:")
        for cmd, metrics in monitoring.metrics.items():
            ctx.output.write(
                f"  {cmd}: {metrics['count']} executions, "
                f"avg {metrics['avg_time']:.2f}s"
            )

        return ""

class ClearStatsCommand(Command):
    name = "clearstats"
    module = "monitoring"

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        monitoring = ctx.get_module('monitoring')
        monitoring.metrics.clear()
        return "Statistics cleared"
```

## Output Formatting

### Rich Output

```python
from ai_shell.ui.formatting import Table, Panel, Syntax

class FormattedCommand(Command):
    name = "report"

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        # Table output
        table = Table(title="User Report")
        table.add_column("Name", style="cyan")
        table.add_column("Email", style="magenta")
        table.add_column("Status", style="green")

        for user in self._get_users():
            table.add_row(user.name, user.email, user.status)

        ctx.output.write(table)

        # Panel with code
        code = Syntax(
            "SELECT * FROM users WHERE active = true",
            "sql",
            theme="monokai"
        )
        ctx.output.write(Panel(code, title="SQL Query"))

        return ""
```

### Progress Tracking

```python
from ai_shell.ui.progress import ProgressBar, Spinner

class DownloadCommand(Command):
    name = "download"

    async def execute(self, ctx: ExecutionContext, args: list) -> str:
        url = args[0]

        # Create progress bar
        progress = ProgressBar(total=100, desc="Downloading")

        async for chunk in self._download_chunks(url):
            progress.update(len(chunk))

        progress.close()
        return "Download complete"

    async def _download_chunks(self, url):
        # Download implementation
        pass
```

## Testing Custom Commands

### Unit Tests

```python
# tests/test_hello.py
import pytest
from ai_shell.core.context import ExecutionContext
from plugins.hello import HelloCommand

@pytest.mark.asyncio
async def test_hello_command():
    cmd = HelloCommand()
    ctx = ExecutionContext()

    # Test with argument
    result = await cmd.execute(ctx, ["Alice"])
    assert result == "Hello, Alice!"

    # Test without argument
    result = await cmd.execute(ctx, [])
    assert result == "Hello, World!"

@pytest.mark.asyncio
async def test_hello_command_output(capsys):
    cmd = HelloCommand()
    ctx = ExecutionContext()

    await cmd.execute(ctx, ["Bob"])
    captured = capsys.readouterr()
    assert "Bob" in captured.out
```

### Integration Tests

```python
# tests/integration/test_ai_command.py
import pytest
from ai_shell.core.shell import AIShell

@pytest.mark.asyncio
async def test_ai_command_integration():
    shell = AIShell()
    await shell.initialize()

    # Execute command
    result = await shell.execute("analyze test.py")

    # Verify AI analysis occurred
    assert result.llm_calls > 0
    assert "analysis" in result.output.lower()
```

## Best Practices

### 1. Async-First Design

```python
# Good: Async operations
async def execute(self, ctx, args):
    data = await self.fetch_data()
    result = await self.process(data)
    return result

# Bad: Blocking operations
def execute(self, ctx, args):
    data = self.fetch_data()  # Blocks
    return self.process(data)
```

### 2. Error Handling

```python
from ai_shell.core.exceptions import CommandError

async def execute(self, ctx, args):
    try:
        return await self._do_work(args)
    except ValueError as e:
        raise CommandError(f"Invalid input: {e}")
    except Exception as e:
        ctx.logger.error(f"Unexpected error: {e}")
        raise CommandError("Command failed")
```

### 3. Context Usage

```python
async def execute(self, ctx: ExecutionContext, args: list):
    # Access LLM
    llm = ctx.llm_manager

    # Update module panel
    ctx.module_panel.update({'status': 'Processing...'})

    # Get database connection
    db = ctx.get_module_context('database')

    # Log events
    ctx.logger.info("Command executed")

    # Access vault
    api_key = ctx.vault.get('api_key')
```

### 4. Documentation

```python
class WellDocumentedCommand(Command):
    """
    One-line description of the command.

    Detailed explanation of what the command does,
    when to use it, and any important considerations.

    Args:
        ctx: Execution context
        args: Command arguments
            args[0]: Input file path
            args[1]: Optional output file path

    Returns:
        Success message or error

    Examples:
        $ mycommand input.txt
        $ mycommand input.txt output.txt

    Raises:
        CommandError: If input file doesn't exist
    """

    name = "mycommand"
    # ... implementation
```

## Plugin Distribution

### Package Structure

```
my-ai-shell-plugin/
├── setup.py
├── README.md
├── LICENSE
├── ai_shell_plugin/
│   ├── __init__.py
│   ├── commands/
│   │   ├── __init__.py
│   │   └── mycommand.py
│   └── config/
│       └── default.yaml
└── tests/
    └── test_mycommand.py
```

### setup.py

```python
from setuptools import setup, find_packages

setup(
    name='ai-shell-myplugin',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'ai-shell>=1.0.0',
    ],
    entry_points={
        'ai_shell.plugins': [
            'myplugin = ai_shell_plugin:register',
        ],
    },
    author='Your Name',
    description='My AI-Shell plugin',
    python_requires='>=3.11',
)
```

### Installation

```bash
# Install from PyPI
pip install ai-shell-myplugin

# Install from local
pip install -e .

# Install from git
pip install git+https://github.com/user/ai-shell-myplugin.git
```

## Next Steps

- [API Reference](../api/commands.md) - Complete command API
- [Module API](../api/modules.md) - Module development API
- [Examples](../../examples/custom-commands/) - Example implementations

## Support

- Plugin Development: https://ai-shell.dev/docs/plugins
- API Documentation: https://ai-shell.dev/api
- Community Plugins: https://github.com/ai-shell/plugins
