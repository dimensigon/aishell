# Core API Reference

## Overview

The AI-Shell core API provides the foundation for building commands, modules, and integrations. This reference covers all core interfaces and classes.

## Core Components

### AIShellCore

Main application orchestrator managing lifecycle and coordination.

```python
from ai_shell.core import AIShellCore

class AIShellCore:
    """Central orchestrator for AI-Shell"""

    def __init__(self, config_path: str = None):
        """
        Initialize AI-Shell core.

        Args:
            config_path: Path to configuration file
        """
        self.modules: Dict[str, Module] = {}
        self.mcp_clients: Dict[str, MCPClient] = {}
        self.llm_manager: LocalLLMManager = LocalLLMManager()
        self.ui_manager: UIManager = UIManager()
        self.event_bus: AsyncEventBus = AsyncEventBus()
        self.vector_store: VectorDatabase = VectorDatabase()

    async def initialize(self) -> None:
        """Initialize all components with health checks"""

    async def execute_command(self, command: str) -> ExecutionResult:
        """Execute a command with full context"""

    async def shutdown(self) -> None:
        """Gracefully shutdown all components"""
```

### ExecutionContext

Context object passed to all commands containing environment state.

```python
from ai_shell.core.context import ExecutionContext

@dataclass
class ExecutionContext:
    """Execution context for commands"""

    # Core managers
    llm_manager: LLMManager
    vault: SecureVault
    vector_store: VectorStore
    event_bus: EventBus

    # Module contexts
    modules: Dict[str, ModuleContext]

    # UI components
    output: OutputManager
    module_panel: ModulePanel
    logger: Logger

    # Session state
    session_id: str
    current_directory: Path
    environment: Dict[str, str]
    user: UserContext

    def get_module(self, name: str) -> Module:
        """Get module instance by name"""

    def get_module_context(self, name: str) -> ModuleContext:
        """Get module-specific context"""

    async def emit_event(self, event: Event) -> None:
        """Emit event to event bus"""
```

### ExecutionResult

Result object returned from command execution.

```python
from ai_shell.core.result import ExecutionResult

@dataclass
class ExecutionResult:
    """Command execution result"""

    success: bool
    output: str
    error: Optional[str] = None

    # Metrics
    execution_time: float = 0.0
    llm_calls: int = 0
    database_queries: int = 0

    # Metadata
    command: str = ""
    exit_code: int = 0
    stdout_lines: int = 0
    stderr_lines: int = 0

    def __str__(self) -> str:
        """String representation for display"""
        return self.output
```

## Command System

### Command Base Class

Abstract base class for all commands.

```python
from ai_shell.core.command import Command
from abc import ABC, abstractmethod

class Command(ABC):
    """Base class for all commands"""

    # Metadata
    name: str
    description: str
    usage: str
    category: str = "general"
    aliases: List[str] = []

    # Permissions
    requires_sudo: bool = False
    requires_database: bool = False

    @abstractmethod
    async def execute(
        self,
        ctx: ExecutionContext,
        args: List[str]
    ) -> Union[str, ExecutionResult]:
        """
        Execute the command.

        Args:
            ctx: Execution context
            args: Command arguments

        Returns:
            Result string or ExecutionResult object
        """
        pass

    async def validate_args(self, args: List[str]) -> bool:
        """Validate command arguments"""
        return True

    async def pre_execute(self, ctx: ExecutionContext) -> None:
        """Hook called before execution"""
        pass

    async def post_execute(
        self,
        ctx: ExecutionContext,
        result: ExecutionResult
    ) -> None:
        """Hook called after execution"""
        pass

    def get_help(self) -> str:
        """Return detailed help text"""
        return f"{self.description}\n\nUsage: {self.usage}"
```

### Command Registry

Manages command registration and lookup.

```python
from ai_shell.core.registry import CommandRegistry

class CommandRegistry:
    """Global command registry"""

    _commands: Dict[str, Command] = {}
    _aliases: Dict[str, str] = {}

    @classmethod
    def register(cls, command: Command) -> None:
        """Register a command"""
        cls._commands[command.name] = command
        for alias in command.aliases:
            cls._aliases[alias] = command.name

    @classmethod
    def get(cls, name: str) -> Optional[Command]:
        """Get command by name or alias"""
        if name in cls._commands:
            return cls._commands[name]
        if name in cls._aliases:
            return cls._commands[cls._aliases[name]]
        return None

    @classmethod
    def list_commands(
        cls,
        category: Optional[str] = None
    ) -> List[Command]:
        """List all commands, optionally filtered by category"""
        commands = cls._commands.values()
        if category:
            return [c for c in commands if c.category == category]
        return list(commands)
```

## Module System

### Module Base Class

Abstract base class for modules.

```python
from ai_shell.core.module import Module

class Module(ABC):
    """Base class for modules"""

    # Metadata
    name: str
    description: str
    version: str

    # Dependencies
    requires_modules: List[str] = []

    @abstractmethod
    async def initialize(self, ctx: ExecutionContext) -> None:
        """Initialize module"""
        pass

    @abstractmethod
    def get_panel_info(self, ctx: ExecutionContext) -> Dict:
        """Get information for module panel"""
        pass

    async def shutdown(self) -> None:
        """Cleanup on shutdown"""
        pass

    def register_commands(self) -> List[Command]:
        """Return list of module commands"""
        return []

    def register_event_handlers(self) -> Dict[str, Callable]:
        """Return event handlers"""
        return {}
```

### ModuleContext

Module-specific context and state.

```python
from ai_shell.core.module import ModuleContext

class ModuleContext:
    """Context for a specific module"""

    def __init__(self, module: Module, global_ctx: ExecutionContext):
        self.module = module
        self.global_ctx = global_ctx
        self.state: Dict[str, Any] = {}

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get module state value"""
        return self.state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        """Set module state value"""
        self.state[key] = value

    async def emit_event(self, event_type: str, data: Any) -> None:
        """Emit module-specific event"""
        await self.global_ctx.emit_event(
            Event(type=f"{self.module.name}.{event_type}", data=data)
        )
```

## Event System

### Event Base Class

```python
from ai_shell.core.events import Event
from dataclasses import dataclass
from typing import Any
from datetime import datetime

@dataclass
class Event:
    """Base event class"""

    type: str
    data: Any
    timestamp: datetime = None
    source: str = ""
    critical: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
```

### AsyncEventBus

Asynchronous event processing system.

```python
from ai_shell.core.events import AsyncEventBus

class AsyncEventBus:
    """Asynchronous event bus"""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing = True

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Awaitable[None]]
    ) -> None:
        """Subscribe to event type"""
        self.subscribers[event_type].append(handler)

    async def unsubscribe(
        self,
        event_type: str,
        handler: Callable
    ) -> None:
        """Unsubscribe from event type"""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(handler)

    async def publish(self, event: Event) -> None:
        """Publish event to bus"""
        await self.event_queue.put(event)

    async def process_events(self) -> None:
        """Background event processing loop"""
        while self.processing:
            event = await self.event_queue.get()

            handlers = self.subscribers.get(event.type, [])

            if event.critical:
                # Wait for critical events
                await asyncio.gather(*[h(event) for h in handlers])
            else:
                # Fire and forget for non-critical
                for handler in handlers:
                    asyncio.create_task(handler(event))
```

## LLM Integration

### LLMManager

Manages local and cloud LLM providers.

```python
from ai_shell.ai.llm_manager import LLMManager

class LLMManager:
    """LLM provider management"""

    def __init__(self, config: Dict):
        self.config = config
        self.providers: Dict[str, LLMProvider] = {}
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    async def query(
        self,
        prompt: str,
        model: str = None,
        provider: str = None,
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncIterator[str]]:
        """
        Query LLM with prompt.

        Args:
            prompt: Input prompt
            model: Model identifier (uses config if not specified)
            provider: Provider name (uses config if not specified)
            stream: Enable streaming response
            **kwargs: Additional provider-specific arguments

        Returns:
            Response string or async iterator for streaming
        """

    async def analyze_intent(
        self,
        user_input: str,
        context: Dict
    ) -> Dict:
        """
        Analyze user intent for command routing.

        Returns:
            {
                'primary_intent': str,
                'confidence': float,
                'suggested_commands': List[str],
                'context_enrichment': Dict
            }
        """

    def pseudo_anonymize(
        self,
        text: str
    ) -> Tuple[str, Dict[str, str]]:
        """
        Anonymize sensitive data before external LLM calls.

        Returns:
            (anonymized_text, anonymization_map)
        """

    async def check_models(self) -> Dict[str, bool]:
        """Check availability of configured models"""
```

### LLMProvider Interface

```python
from ai_shell.ai.provider import LLMProvider

class LLMProvider(Protocol):
    """Interface for LLM providers"""

    async def query(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> str:
        """Execute query"""
        ...

    async def stream_query(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream query response"""
        ...

    async def check_availability(self) -> bool:
        """Check if provider is available"""
        ...
```

## Vector Store

### VectorDatabase

FAISS-based semantic search.

```python
from ai_shell.core.vector_store import VectorDatabase

class VectorDatabase:
    """Vector database for semantic search"""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata: List[Dict] = []

    async def add(
        self,
        text: str,
        metadata: Dict,
        embedding: np.ndarray = None
    ) -> None:
        """
        Add item to vector database.

        Args:
            text: Text content
            metadata: Associated metadata
            embedding: Pre-computed embedding (optional)
        """

    async def search(
        self,
        query: Union[str, np.ndarray],
        k: int = 5,
        filters: Dict = None
    ) -> List[Dict]:
        """
        Semantic search.

        Args:
            query: Search query (text or embedding)
            k: Number of results
            filters: Metadata filters

        Returns:
            List of results with metadata and similarity scores
        """

    async def load_system_objects(self) -> None:
        """Pre-load database system objects"""

    async def save(self, path: Path) -> None:
        """Save index to disk"""

    async def load(self, path: Path) -> None:
        """Load index from disk"""
```

## Utility Functions

### Argument Parsing

```python
from ai_shell.core.arguments import ArgumentParser

class ArgumentParser:
    """Enhanced argument parser for commands"""

    def __init__(self, prog: str, description: str = ""):
        self.prog = prog
        self.description = description
        self.arguments: List[Argument] = []

    def add_argument(
        self,
        name: str,
        **kwargs
    ) -> None:
        """
        Add argument definition.

        Supported kwargs:
            help: Help text
            type: Type converter
            default: Default value
            required: Required flag
            choices: Valid choices
            action: 'store_true', 'store_false', 'append'
        """

    def parse_args(self, args: List[str]) -> Namespace:
        """Parse arguments and return namespace"""

    def print_help(self) -> str:
        """Generate help text"""
```

### Output Formatting

```python
from ai_shell.ui.formatting import Table, Panel, Syntax

class Table:
    """Formatted table output"""

    def __init__(self, title: str = ""):
        self.title = title
        self.columns: List[Column] = []
        self.rows: List[List[str]] = []

    def add_column(
        self,
        header: str,
        style: str = "",
        width: int = None
    ) -> None:
        """Add column definition"""

    def add_row(self, *values) -> None:
        """Add row data"""

    def render(self) -> str:
        """Render table for display"""

class Panel:
    """Bordered panel for content"""

    def __init__(
        self,
        content: Any,
        title: str = "",
        style: str = ""
    ):
        self.content = content
        self.title = title
        self.style = style

    def render(self) -> str:
        """Render panel"""

class Syntax:
    """Syntax highlighted code"""

    def __init__(
        self,
        code: str,
        language: str,
        theme: str = "monokai"
    ):
        self.code = code
        self.language = language
        self.theme = theme

    def render(self) -> str:
        """Render syntax highlighted code"""
```

## Exception Handling

### Exception Hierarchy

```python
from ai_shell.core.exceptions import *

class AIShellError(Exception):
    """Base exception for AI-Shell"""
    pass

class CommandError(AIShellError):
    """Command execution error"""
    pass

class ModuleError(AIShellError):
    """Module initialization/execution error"""
    pass

class ConfigurationError(AIShellError):
    """Configuration error"""
    pass

class DatabaseError(AIShellError):
    """Database operation error"""
    pass

class LLMError(AIShellError):
    """LLM provider error"""
    pass

class ValidationError(AIShellError):
    """Input validation error"""
    pass
```

## Configuration

### Config Object

```python
from ai_shell.core.config import Config

class Config:
    """Configuration management"""

    def __init__(self, config_path: Path = None):
        self.config_path = config_path or Path.home() / ".ai-shell" / "config.yaml"
        self.data: Dict = {}

    def load(self) -> None:
        """Load configuration from file"""

    def save(self) -> None:
        """Save configuration to file"""

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value (supports dot notation)"""

    def set(self, key: str, value: Any) -> None:
        """Set configuration value (supports dot notation)"""

    def merge(self, other: Dict) -> None:
        """Merge configuration dictionary"""

# Usage
config = Config()
config.load()

# Dot notation access
llm_provider = config.get('llm.provider')
config.set('llm.openai.api_key', 'sk-...')
```

## Logging

### Logger

```python
from ai_shell.core.logger import Logger

class Logger:
    """Enhanced logging with context"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)

    def debug(self, msg: str, **kwargs) -> None:
        """Debug level log"""

    def info(self, msg: str, **kwargs) -> None:
        """Info level log"""

    def warning(self, msg: str, **kwargs) -> None:
        """Warning level log"""

    def error(self, msg: str, exc_info: bool = False, **kwargs) -> None:
        """Error level log"""

    def critical(self, msg: str, **kwargs) -> None:
        """Critical level log"""

# Usage
logger = Logger('mymodule')
logger.info("Command executed", command="test", duration=0.5)
```

## Next Steps

- [Module API](./modules.md) - Module development
- [MCP Client API](./mcp-clients.md) - Database client development
- [UI Components API](./ui-components.md) - UI customization
