# Phase 11: Advanced UI & Interactive Experience - Technical Architecture

**Document Version:** 1.0
**Created:** 2025-10-04
**Project:** AIShell - AI-powered CLI database management tool
**Phase:** 11 - Advanced UI & Interactive Experience

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Architecture Overview](#architecture-overview)
4. [Component Design](#component-design)
5. [Integration Architecture](#integration-architecture)
6. [Implementation Roadmap](#implementation-roadmap)
7. [Technical Specifications](#technical-specifications)
8. [Performance Considerations](#performance-considerations)
9. [Testing Strategy](#testing-strategy)
10. [Appendix](#appendix)

---

## Executive Summary

### Objectives

Phase 11 introduces advanced interactive UI features to AIShell, transforming the command-line experience with:

1. **Matrix-style Startup Animation** - Visual system health checks with async initialization
2. **Enhanced Dynamic Panel Management** - Content-aware, activity-responsive layout system
3. **Real-time Command Preview** - AI-powered risk visualization before execution
4. **Smart Command Suggestions** - Integrated vector-based autocomplete in UI

### Key Architectural Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Textual Framework | Modern async TUI framework with rich widgets | Maintainable, testable UI code |
| Event-Driven Architecture | Leverage existing AsyncEventBus | Non-blocking, responsive UI |
| Component-Based Design | Modular widgets with clear interfaces | Easy to test and extend |
| Layered Integration | UI components subscribe to core events | Decoupled from business logic |

### Success Metrics

- Startup animation completes in < 2 seconds
- Panel resizing responds within 50ms of user action
- Command risk analysis displays in < 200ms
- UI maintains 60fps during all interactions
- Zero blocking operations in main UI thread

---

## Current State Analysis

### Existing UI Components

```
src/ui/
├── app.py              # Mock AIShellApp (basic 3-panel concept)
├── panel_manager.py    # DynamicPanelManager (content-aware sizing)
├── prompt_handler.py   # PromptHandler (multiline input, validation)
└── __init__.py
```

### Existing Core Infrastructure

**AsyncEventBus** (`src/core/event_bus.py`)
- Priority-based event processing
- Backpressure handling
- Critical event guarantees
- 1000-event queue capacity

**VectorAutocomplete** (`src/vector/autocomplete.py`)
- FAISS-based semantic search
- Pattern-based completions
- Syntax-aware suggestions
- History-based learning

**SQLRiskAnalyzer** (`src/database/risk_analyzer.py`)
- 4-level risk classification (LOW, MEDIUM, HIGH, CRITICAL)
- Pattern-based SQL analysis
- Confirmation message generation

**ModulePanelEnricher** (`src/modules/panel_enricher.py`)
- Async enrichment with priority queue
- 4 concurrent workers
- Context provider system
- Cache with statistics

### Integration Points

```
┌─────────────────────────────────────────────────┐
│              Existing Architecture              │
├─────────────────────────────────────────────────┤
│                                                 │
│  AsyncEventBus ←→ Panel Enricher                │
│       ↕                    ↕                    │
│  Risk Analyzer ←→ Vector Autocomplete           │
│                                                 │
└─────────────────────────────────────────────────┘
                     ↓
        Phase 11 UI Components Subscribe
```

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Textual Application                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              MatrixStartupScreen (Layer 1)            │  │
│  │   - Async system checks with visual feedback         │  │
│  │   - Matrix rain animation                             │  │
│  │   - Graceful transition to main app                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           EnhancedAIShellApp (Layer 2)                │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │     DynamicPanelContainer (Adaptive Layout)     │  │  │
│  │  │  ┌───────────────────────────────────────────┐  │  │  │
│  │  │  │  OutputPanel (50% default)                │  │  │  │
│  │  │  │  - Scrollable command output              │  │  │  │
│  │  │  │  - Syntax highlighting                    │  │  │  │
│  │  │  └───────────────────────────────────────────┘  │  │  │
│  │  │  ┌───────────────────────────────────────────┐  │  │  │
│  │  │  │  ModulePanel (30% default)                │  │  │  │
│  │  │  │  - Async enrichment display               │  │  │  │
│  │  │  │  - Context-aware information              │  │  │  │
│  │  │  └───────────────────────────────────────────┘  │  │  │
│  │  │  ┌───────────────────────────────────────────┐  │  │  │
│  │  │  │  SmartPromptPanel (20% default)           │  │  │  │
│  │  │  │  ┌─────────────────────────────────────┐  │  │  │  │
│  │  │  │  │ CommandPreviewWidget (Overlay)      │  │  │  │  │
│  │  │  │  │ - Real-time risk visualization      │  │  │  │  │
│  │  │  │  │ - AI-powered impact analysis        │  │  │  │  │
│  │  │  │  └─────────────────────────────────────┘  │  │  │  │
│  │  │  │  ┌─────────────────────────────────────┐  │  │  │  │
│  │  │  │  │ SmartSuggestionList (Dropdown)      │  │  │  │  │
│  │  │  │  │ - Vector-based completions          │  │  │  │  │
│  │  │  │  │ - Contextual suggestions            │  │  │  │  │
│  │  │  │  └─────────────────────────────────────┘  │  │  │  │
│  │  │  │  └─── Enhanced TextArea                  │  │  │  │
│  │  │  └───────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↕
        ┌─────────────────────────────────────────┐
        │      Core Services (Event-Driven)       │
        ├─────────────────────────────────────────┤
        │  • AsyncEventBus (Priority Queue)       │
        │  • ModulePanelEnricher (4 workers)      │
        │  • SQLRiskAnalyzer (Pattern-based)      │
        │  • VectorAutocomplete (FAISS)           │
        └─────────────────────────────────────────┘
```

### Data Flow Architecture

```
User Input → SmartPromptPanel
     ↓
     ├─→ [Typing Event] → DynamicPanelContainer
     │                     └→ Adjust panel weights (prompt grows)
     │
     ├─→ [Text Change] → CommandPreviewWidget
     │                   └→ SQLRiskAnalyzer (async)
     │                       └→ Display risk overlay
     │
     ├─→ [Autocomplete] → SmartSuggestionList
     │                    └→ VectorAutocomplete (FAISS search)
     │                        └→ Show ranked suggestions
     │
     └─→ [Command Submit] → Event Bus
                            ├→ Panel Enricher (background)
                            │   └→ Update ModulePanel
                            └→ Command Executor
                                └→ Update OutputPanel
```

---

## Component Design

### 1. Matrix Startup Animation System

#### 1.1 MatrixStartupScreen

**Purpose:** Visual startup sequence with system health checks

**Class Design:**

```python
class MatrixStartupScreen(Screen):
    """
    Matrix-style startup screen with async system checks.

    Features:
    - Cascading matrix rain animation (green characters)
    - Parallel async health checks with progress indicators
    - Smooth transition to main application
    - Error handling with fallback to basic startup
    """

    BINDINGS = [("escape", "skip", "Skip startup")]

    def __init__(self):
        super().__init__()
        self.check_results: Dict[str, CheckResult] = {}
        self.animation_task: Optional[asyncio.Task] = None
        self.checks_complete = False

    def compose(self) -> ComposeResult:
        """Build UI components."""
        yield MatrixRainWidget(id="matrix-bg")
        yield Container(
            Static("AI-Shell Initializing...", classes="title"),
            HealthCheckGrid(id="health-checks"),
            ProgressBar(id="init-progress", total=100),
            Static("", id="status-text"),
            id="startup-container"
        )

    async def on_mount(self) -> None:
        """Start parallel checks and animation."""
        self.animation_task = asyncio.create_task(
            self._run_matrix_animation()
        )
        await self._run_system_checks()
        await self._transition_to_main()
```

#### 1.2 System Health Checks

**Check Architecture:**

```python
@dataclass
class HealthCheck:
    """System health check definition."""
    name: str
    description: str
    check_fn: Callable[[], Awaitable[CheckResult]]
    critical: bool = False
    timeout: float = 5.0

@dataclass
class CheckResult:
    """Health check result."""
    success: bool
    message: str
    duration_ms: float
    error: Optional[Exception] = None

class HealthCheckRunner:
    """Manages parallel health check execution."""

    CHECKS = [
        HealthCheck(
            name="LLM Connection",
            description="Testing AI model availability",
            check_fn=_check_llm_connection,
            critical=False,
            timeout=3.0
        ),
        HealthCheck(
            name="Vector Database",
            description="Initializing FAISS index",
            check_fn=_check_vector_db,
            critical=True,
            timeout=2.0
        ),
        HealthCheck(
            name="MCP Clients",
            description="Loading database clients",
            check_fn=_check_mcp_clients,
            critical=False,
            timeout=2.0
        ),
        HealthCheck(
            name="Event Bus",
            description="Starting async event system",
            check_fn=_check_event_bus,
            critical=True,
            timeout=1.0
        ),
        HealthCheck(
            name="Panel Enricher",
            description="Spawning enrichment workers",
            check_fn=_check_panel_enricher,
            critical=False,
            timeout=1.0
        )
    ]

    async def run_all_checks(
        self,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, CheckResult]:
        """Run all checks in parallel."""
        results = {}
        total = len(self.CHECKS)

        async def run_check(check: HealthCheck) -> Tuple[str, CheckResult]:
            start = time.perf_counter()
            try:
                result = await asyncio.wait_for(
                    check.check_fn(),
                    timeout=check.timeout
                )
                duration = (time.perf_counter() - start) * 1000
                result.duration_ms = duration
                return check.name, result
            except asyncio.TimeoutError:
                return check.name, CheckResult(
                    success=False,
                    message=f"Timeout after {check.timeout}s",
                    duration_ms=check.timeout * 1000
                )

        # Run all checks concurrently
        tasks = [run_check(check) for check in self.CHECKS]

        for i, coro in enumerate(asyncio.as_completed(tasks)):
            name, result = await coro
            results[name] = result

            if progress_callback:
                await progress_callback(
                    completed=i + 1,
                    total=total,
                    current_check=name,
                    result=result
                )

        return results
```

#### 1.3 Matrix Rain Animation Widget

```python
class MatrixRainWidget(Widget):
    """
    Matrix rain background animation.

    Renders cascading green characters using Textual's rich rendering.
    Optimized for performance with column-based rendering.
    """

    DEFAULT_CSS = """
    MatrixRainWidget {
        background: $surface;
        color: $success;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.columns: List[MatrixColumn] = []
        self.chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()")

    def on_mount(self) -> None:
        """Initialize matrix columns."""
        width = self.size.width
        self.columns = [
            MatrixColumn(
                x=i,
                speed=random.uniform(0.5, 2.0),
                length=random.randint(5, 20),
                chars=self.chars
            )
            for i in range(0, width, 2)
        ]
        self.set_interval(0.05, self.update_columns)

    def update_columns(self) -> None:
        """Update column positions."""
        for column in self.columns:
            column.update(self.size.height)
        self.refresh()

    def render(self) -> RenderableType:
        """Render matrix rain."""
        console = Console()
        for column in self.columns:
            for y, char, intensity in column.get_chars():
                style = Style(
                    color=f"green{int(intensity * 100)}"
                )
                console.print(char, style=style, end="")
        return console
```

---

### 2. Enhanced Dynamic Panel Management

#### 2.1 DynamicPanelContainer

**Purpose:** Adaptive layout controller with content-aware sizing

```python
class DynamicPanelContainer(Container):
    """
    Container managing adaptive panel sizing.

    Features:
    - Content-aware height allocation
    - Typing state detection
    - Smooth resize transitions
    - Min/max constraints per panel
    """

    DEFAULT_CSS = """
    DynamicPanelContainer {
        layout: vertical;
        height: 100%;
    }

    .panel-output {
        height: auto;
        min-height: 10;
        max-height: 70%;
    }

    .panel-module {
        height: auto;
        min-height: 5;
        max-height: 50%;
    }

    .panel-prompt {
        height: auto;
        min-height: 3;
        max-height: 50%;
    }
    """

    def __init__(self, panel_manager: DynamicPanelManager):
        super().__init__()
        self.panel_manager = panel_manager
        self.output_panel: Optional[OutputPanel] = None
        self.module_panel: Optional[ModulePanel] = None
        self.prompt_panel: Optional[SmartPromptPanel] = None

    def compose(self) -> ComposeResult:
        """Compose panel structure."""
        self.output_panel = OutputPanel(classes="panel-output")
        self.module_panel = ModulePanel(classes="panel-module")
        self.prompt_panel = SmartPromptPanel(classes="panel-prompt")

        yield self.output_panel
        yield self.module_panel
        yield self.prompt_panel

    async def on_resize(self, event: events.Resize) -> None:
        """Handle terminal resize."""
        await self._recalculate_layout(event.size.height)

    async def on_typing_state_changed(
        self,
        message: TypingStateChanged
    ) -> None:
        """React to typing state changes."""
        self.panel_manager.set_typing_state(message.is_typing)
        await self._recalculate_layout(self.size.height)

    async def _recalculate_layout(self, terminal_height: int) -> None:
        """
        Recalculate panel dimensions based on current state.

        Algorithm:
        1. Get dimensions from panel_manager
        2. Apply min/max constraints
        3. Animate resize if smooth_resize enabled
        4. Update panel heights
        """
        dimensions = self.panel_manager.calculate_dimensions(terminal_height)

        # Apply constraints and update
        for panel_name, panel_dims in dimensions.items():
            panel = getattr(self, f"{panel_name}_panel")
            if panel:
                # Clamp between min and max
                target_height = max(
                    panel_dims.min,
                    min(panel_dims.preferred, panel_dims.max)
                )

                # Smooth animation
                await self._animate_resize(panel, target_height)

    async def _animate_resize(
        self,
        panel: Widget,
        target_height: int
    ) -> None:
        """Animate panel resize smoothly."""
        current = panel.styles.height.value if panel.styles.height else 0

        if abs(target_height - current) <= 1:
            panel.styles.height = target_height
            return

        # Smooth transition over 100ms
        steps = 5
        step_size = (target_height - current) / steps

        for i in range(steps):
            await asyncio.sleep(0.02)
            new_height = int(current + step_size * (i + 1))
            panel.styles.height = new_height

        panel.styles.height = target_height
```

#### 2.2 Content Size Tracking

```python
class ContentSizeTracker:
    """
    Tracks content size for adaptive panel management.

    Monitors:
    - Line count in output panel
    - Module panel content height
    - Prompt panel line count
    """

    def __init__(self, panel_manager: DynamicPanelManager):
        self.panel_manager = panel_manager
        self.content_observers: Dict[str, Callable] = {}

    def register_panel(
        self,
        panel_id: str,
        observer: Callable[[], int]
    ) -> None:
        """Register content size observer for panel."""
        self.content_observers[panel_id] = observer

    async def monitor_loop(self) -> None:
        """Continuous monitoring loop."""
        while True:
            await asyncio.sleep(0.1)  # Check every 100ms

            for panel_id, observer in self.content_observers.items():
                try:
                    size = observer()
                    self.panel_manager.update_content_size(panel_id, size)
                except Exception as e:
                    logger.error(f"Error monitoring panel {panel_id}: {e}")
```

---

### 3. Real-time Command Preview System

#### 3.1 CommandPreviewWidget

**Purpose:** Real-time risk visualization overlay

```python
class CommandPreviewWidget(Static):
    """
    Overlay widget showing real-time command risk analysis.

    Features:
    - Async risk analysis (non-blocking)
    - Color-coded risk levels
    - Expandable details on hover
    - Auto-hide when risk is LOW
    """

    DEFAULT_CSS = """
    CommandPreviewWidget {
        dock: top;
        height: auto;
        padding: 1;
        margin: 0 1;
        display: none;
    }

    CommandPreviewWidget.risk-low {
        display: none;
    }

    CommandPreviewWidget.risk-medium {
        background: $warning-darken-2;
        border: tall $warning;
        display: block;
    }

    CommandPreviewWidget.risk-high {
        background: $error-darken-2;
        border: tall $error;
        display: block;
    }

    CommandPreviewWidget.risk-critical {
        background: $error;
        border: thick $error;
        display: block;
        color: $text;
    }
    """

    def __init__(self, risk_analyzer: SQLRiskAnalyzer):
        super().__init__()
        self.risk_analyzer = risk_analyzer
        self.current_analysis: Optional[Dict] = None
        self.analysis_task: Optional[asyncio.Task] = None

    async def analyze_command(self, command: str) -> None:
        """
        Analyze command asynchronously.

        Debounces rapid typing to avoid excessive analysis.
        """
        # Cancel previous analysis
        if self.analysis_task and not self.analysis_task.done():
            self.analysis_task.cancel()

        # Debounce - wait 300ms before analyzing
        await asyncio.sleep(0.3)

        # Perform analysis
        self.analysis_task = asyncio.create_task(
            self._run_analysis(command)
        )

    async def _run_analysis(self, command: str) -> None:
        """Run risk analysis in background."""
        try:
            # Check if SQL command
            if not self._is_sql_command(command):
                self._hide()
                return

            # Analyze risk
            analysis = await asyncio.to_thread(
                self.risk_analyzer.analyze,
                command
            )

            self.current_analysis = analysis
            self._update_display(analysis)

        except Exception as e:
            logger.error(f"Preview analysis error: {e}")
            self._hide()

    def _update_display(self, analysis: Dict) -> None:
        """Update widget display with analysis."""
        risk_level = analysis['risk_level']

        # Set CSS class based on risk
        self.remove_class("risk-low", "risk-medium", "risk-high", "risk-critical")
        self.add_class(f"risk-{risk_level.lower()}")

        # Build content
        content = self._build_content(analysis)
        self.update(content)

    def _build_content(self, analysis: Dict) -> RenderableType:
        """Build rich content for display."""
        risk_level = analysis['risk_level']
        warnings = analysis.get('warnings', [])

        # Icon based on risk
        icons = {
            'LOW': '✓',
            'MEDIUM': '⚠',
            'HIGH': '⚠⚠',
            'CRITICAL': '⛔'
        }
        icon = icons.get(risk_level, '?')

        # Build table
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Icon", width=3)
        table.add_column("Content")

        table.add_row(
            icon,
            f"[bold]{risk_level} RISK[/bold]"
        )

        for warning in warnings:
            table.add_row("", warning)

        return table

    def _is_sql_command(self, command: str) -> bool:
        """Check if command is SQL."""
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER']
        command_upper = command.strip().upper()
        return any(command_upper.startswith(kw) for kw in sql_keywords)

    def _hide(self) -> None:
        """Hide widget."""
        self.add_class("risk-low")
        self.current_analysis = None
```

#### 3.2 Risk Visualization Components

```python
class RiskIndicator(Static):
    """Visual risk level indicator."""

    def __init__(self, risk_level: str):
        super().__init__()
        self.risk_level = risk_level

    def render(self) -> RenderableType:
        """Render risk indicator bar."""
        levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        current_index = levels.index(self.risk_level) if self.risk_level in levels else 0

        bars = []
        for i, level in enumerate(levels):
            if i <= current_index:
                color = {
                    'LOW': 'green',
                    'MEDIUM': 'yellow',
                    'HIGH': 'red',
                    'CRITICAL': 'red bold'
                }[level]
                bars.append(f"[{color}]█[/]")
            else:
                bars.append("[dim]░[/]")

        return " ".join(bars) + f"  {self.risk_level}"


class ImpactEstimator:
    """
    Estimates impact of SQL commands.

    Features:
    - Row count estimation
    - Affected table analysis
    - Performance impact prediction
    """

    async def estimate_impact(
        self,
        sql: str,
        db_connection: Any
    ) -> Dict[str, Any]:
        """
        Estimate impact of SQL command.

        Returns:
            {
                'affected_rows': int (estimated),
                'affected_tables': List[str],
                'execution_time_estimate': float (seconds),
                'lock_duration': float (seconds),
                'resource_usage': str ('low', 'medium', 'high')
            }
        """
        # Parse SQL to extract tables
        tables = self._extract_tables(sql)

        # Estimate rows for each table
        row_estimates = {}
        for table in tables:
            count = await self._estimate_table_rows(table, db_connection)
            row_estimates[table] = count

        # Calculate total affected rows
        total_rows = sum(row_estimates.values())

        # Estimate execution time based on operation and rows
        exec_time = self._estimate_execution_time(sql, total_rows)

        return {
            'affected_rows': total_rows,
            'affected_tables': tables,
            'execution_time_estimate': exec_time,
            'lock_duration': exec_time * 1.2,  # Locks held longer
            'resource_usage': self._classify_resource_usage(total_rows)
        }
```

---

### 4. Smart Command Suggestion System

#### 4.1 SmartSuggestionList

**Purpose:** Integrated vector-based autocomplete UI

```python
class SmartSuggestionList(OptionList):
    """
    Smart suggestion dropdown with vector-based completions.

    Features:
    - Real-time FAISS search
    - Ranked by relevance score
    - Keyboard navigation
    - Contextual icons
    - Preview pane for complex suggestions
    """

    DEFAULT_CSS = """
    SmartSuggestionList {
        dock: bottom;
        height: auto;
        max-height: 10;
        border: tall $primary;
        background: $surface;
        display: none;
    }

    SmartSuggestionList.visible {
        display: block;
    }

    SmartSuggestionList > .option-list--option-highlighted {
        background: $primary-darken-2;
    }
    """

    BINDINGS = [
        ("up", "cursor_up", "Previous suggestion"),
        ("down", "cursor_down", "Next suggestion"),
        ("enter", "select", "Accept suggestion"),
        ("escape", "hide", "Hide suggestions")
    ]

    def __init__(
        self,
        autocompleter: IntelligentCompleter,
        embedding_provider: Any
    ):
        super().__init__()
        self.autocompleter = autocompleter
        self.embedding_provider = embedding_provider
        self.current_suggestions: List[CompletionCandidate] = []
        self.search_task: Optional[asyncio.Task] = None

    async def search_suggestions(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> None:
        """Search for suggestions asynchronously."""
        # Cancel previous search
        if self.search_task and not self.search_task.done():
            self.search_task.cancel()

        # Debounce
        await asyncio.sleep(0.15)

        # Run search
        self.search_task = asyncio.create_task(
            self._run_search(query, context or {})
        )

    async def _run_search(
        self,
        query: str,
        context: Dict
    ) -> None:
        """Execute search and update UI."""
        try:
            # Generate embedding
            embedding = await asyncio.to_thread(
                self.embedding_provider.embed,
                query
            )

            # Get completions
            candidates = await asyncio.to_thread(
                self.autocompleter.get_completions,
                query,
                embedding,
                context,
                max_results=10
            )

            self.current_suggestions = candidates
            self._update_options(candidates)

            if candidates:
                self._show()
            else:
                self._hide()

        except Exception as e:
            logger.error(f"Suggestion search error: {e}")
            self._hide()

    def _update_options(self, candidates: List[CompletionCandidate]) -> None:
        """Update option list with candidates."""
        self.clear_options()

        for candidate in candidates:
            # Build rich option
            icon = self._get_source_icon(candidate.source)
            score_bar = self._render_score(candidate.score)

            label = f"{icon} {candidate.text} {score_bar}"

            self.add_option(
                Option(
                    label,
                    id=candidate.text
                )
            )

    def _get_source_icon(self, source: str) -> str:
        """Get icon for suggestion source."""
        icons = {
            'vector': '🔍',
            'pattern': '📋',
            'syntax': '⚙️',
            'history': '🕐'
        }
        return icons.get(source, '•')

    def _render_score(self, score: float) -> str:
        """Render relevance score as visual bar."""
        filled = int(score * 5)
        empty = 5 - filled
        return f"[dim]{'█' * filled}{'░' * empty}[/]"

    def _show(self) -> None:
        """Show suggestion list."""
        self.add_class("visible")

    def _hide(self) -> None:
        """Hide suggestion list."""
        self.remove_class("visible")

    async def on_option_list_option_selected(
        self,
        event: OptionList.OptionSelected
    ) -> None:
        """Handle suggestion selection."""
        # Emit custom event
        await self.emit(SuggestionSelected(event.option.id))
        self._hide()
```

#### 4.2 Context-Aware Suggestion Engine

```python
class ContextAwareSuggestionEngine:
    """
    Manages context gathering for intelligent suggestions.

    Analyzes:
    - Current SQL statement type
    - Cursor position in query
    - Active database schema
    - Recent command history
    - Current module state
    """

    def __init__(
        self,
        autocompleter: IntelligentCompleter,
        event_bus: AsyncEventBus
    ):
        self.autocompleter = autocompleter
        self.event_bus = event_bus
        self.schema_cache: Dict[str, SchemaInfo] = {}
        self.history: List[str] = []

    async def get_context(
        self,
        query: str,
        cursor_position: int
    ) -> Dict[str, Any]:
        """
        Gather context for suggestions.

        Returns:
            {
                'statement_type': str,
                'cursor_position': int,
                'expected_object': str,  # 'table', 'column', 'function'
                'active_schema': str,
                'recent_tables': List[str],
                'query_fragment': str
            }
        """
        # Parse query to determine context
        statement_type = self._detect_statement_type(query)
        expected = self._infer_expected_object(query, cursor_position)

        # Get active schema from event bus
        schema = await self._get_active_schema()

        # Extract recent tables from history
        recent_tables = self._extract_recent_tables(self.history[-10:])

        # Extract fragment around cursor
        fragment = self._extract_fragment(query, cursor_position)

        return {
            'statement_type': statement_type,
            'cursor_position': cursor_position,
            'expected_object': expected,
            'active_schema': schema,
            'recent_tables': recent_tables,
            'query_fragment': fragment
        }

    def _infer_expected_object(
        self,
        query: str,
        cursor_position: int
    ) -> str:
        """
        Infer what type of object should be suggested.

        Logic:
        - After FROM → table
        - After SELECT → column
        - After JOIN → table
        - After ON → column
        - After WHERE → column
        """
        before_cursor = query[:cursor_position].upper()

        # Check keywords before cursor
        if 'FROM' in before_cursor and 'WHERE' not in before_cursor:
            return 'table'
        elif 'SELECT' in before_cursor and 'FROM' not in before_cursor:
            return 'column'
        elif 'JOIN' in before_cursor:
            # After JOIN but before ON → table
            if 'ON' not in before_cursor.split('JOIN')[-1]:
                return 'table'
            else:
                return 'column'
        elif 'WHERE' in before_cursor or 'ON' in before_cursor:
            return 'column'

        return 'keyword'
```

---

## Integration Architecture

### Event Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Interactions                    │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 UI Event Handlers                       │
│  • on_key() → TypingStateChanged event                  │
│  • on_input_changed() → CommandPreview request          │
│  • on_autocomplete() → SuggestionRequest event          │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────┐
│              AsyncEventBus (Priority Queue)             │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Event Types:                                     │  │
│  │  • typing_state_changed (NORMAL)                  │  │
│  │  • command_preview_request (HIGH)                 │  │
│  │  • suggestion_request (NORMAL)                    │  │
│  │  • panel_enrichment_request (LOW)                 │  │
│  │  • command_executed (CRITICAL)                    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
            ↓             ↓             ↓
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Risk Analyzer    │ │ Autocompleter    │ │ Panel Enricher   │
│ (Async Worker)   │ │ (Async Worker)   │ │ (4 Workers)      │
└──────────────────┘ └──────────────────┘ └──────────────────┘
            │             │             │
            └─────────────┼─────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────┐
│              UI Update Events (Results)                 │
│  • risk_analysis_complete → CommandPreviewWidget        │
│  • suggestions_ready → SmartSuggestionList              │
│  • panel_enriched → ModulePanel                         │
└─────────────────────────────────────────────────────────┘
```

### Subscription Architecture

```python
class UIEventIntegration:
    """
    Central integration point for UI and core services.

    Manages event subscriptions and coordinated responses.
    """

    def __init__(
        self,
        event_bus: AsyncEventBus,
        risk_analyzer: SQLRiskAnalyzer,
        autocompleter: IntelligentCompleter,
        panel_enricher: ModulePanelEnricher
    ):
        self.event_bus = event_bus
        self.risk_analyzer = risk_analyzer
        self.autocompleter = autocompleter
        self.panel_enricher = panel_enricher

    async def setup_subscriptions(self) -> None:
        """Register all UI event subscriptions."""

        # Command preview requests
        self.event_bus.subscribe(
            'command_preview_request',
            self._handle_preview_request
        )

        # Autocomplete requests
        self.event_bus.subscribe(
            'suggestion_request',
            self._handle_suggestion_request
        )

        # Panel enrichment
        self.event_bus.subscribe(
            'panel_enrichment_request',
            self._handle_enrichment_request
        )

        # Typing state changes
        self.event_bus.subscribe(
            'typing_state_changed',
            self._handle_typing_state
        )

    async def _handle_preview_request(self, event: Event) -> None:
        """Handle command preview request."""
        command = event.data['command']

        # Analyze in background
        analysis = await asyncio.to_thread(
            self.risk_analyzer.analyze,
            command
        )

        # Publish result
        await self.event_bus.publish(Event(
            'risk_analysis_complete',
            data={'analysis': analysis},
            priority=EventPriority.HIGH
        ))

    async def _handle_suggestion_request(self, event: Event) -> None:
        """Handle autocomplete request."""
        query = event.data['query']
        context = event.data.get('context', {})
        embedding = event.data['embedding']

        # Get suggestions
        candidates = await asyncio.to_thread(
            self.autocompleter.get_completions,
            query,
            embedding,
            context
        )

        # Publish result
        await self.event_bus.publish(Event(
            'suggestions_ready',
            data={'candidates': candidates},
            priority=EventPriority.NORMAL
        ))
```

---

## Implementation Roadmap

### Phase 11.1: Matrix Startup Animation (Week 1)

**Tasks:**
1. Implement MatrixRainWidget with column-based rendering
2. Create HealthCheckRunner with parallel async checks
3. Build MatrixStartupScreen with progress tracking
4. Integrate with existing AsyncEventBus
5. Add error handling and fallback to basic startup

**Deliverables:**
- `/src/ui/widgets/matrix_rain.py`
- `/src/ui/screens/startup_screen.py`
- `/src/core/health_checks.py`
- Unit tests with 90% coverage

**Success Criteria:**
- Startup completes in < 2 seconds
- All health checks run in parallel
- Graceful degradation on check failures
- Smooth transition to main app

---

### Phase 11.2: Dynamic Panel Enhancement (Week 2)

**Tasks:**
1. Enhance DynamicPanelManager with smooth resize animations
2. Implement ContentSizeTracker for real-time monitoring
3. Create DynamicPanelContainer with Textual integration
4. Add typing state event propagation
5. Implement panel weight adjustment algorithm

**Deliverables:**
- `/src/ui/containers/dynamic_panel_container.py`
- `/src/ui/utils/content_tracker.py`
- Enhanced `/src/ui/panel_manager.py`
- Integration tests

**Success Criteria:**
- Panel resizes respond within 50ms
- Smooth animation over 100ms
- No UI flicker or tearing
- Correct min/max constraint enforcement

---

### Phase 11.3: Command Preview System (Week 3)

**Tasks:**
1. Build CommandPreviewWidget with risk visualization
2. Implement ImpactEstimator for row count estimation
3. Create RiskIndicator visual components
4. Integrate with SQLRiskAnalyzer
5. Add debouncing for rapid typing

**Deliverables:**
- `/src/ui/widgets/command_preview.py`
- `/src/database/impact_estimator.py`
- `/src/ui/widgets/risk_indicator.py`
- Performance tests

**Success Criteria:**
- Risk analysis completes in < 200ms
- No typing lag or blocking
- Clear visual distinction between risk levels
- Accurate impact estimation (±20%)

---

### Phase 11.4: Smart Suggestions UI (Week 4)

**Tasks:**
1. Implement SmartSuggestionList with keyboard navigation
2. Create ContextAwareSuggestionEngine
3. Integrate with VectorAutocomplete
4. Add suggestion preview pane
5. Implement scoring visualization

**Deliverables:**
- `/src/ui/widgets/suggestion_list.py`
- `/src/ui/engines/context_suggestion.py`
- `/src/ui/widgets/suggestion_preview.py`
- User acceptance tests

**Success Criteria:**
- Suggestions appear within 150ms
- Keyboard navigation smooth
- Top suggestion relevance > 80%
- Visual score bars accurate

---

### Phase 11.5: Integration & Polish (Week 5)

**Tasks:**
1. Integrate all components into EnhancedAIShellApp
2. Create UIEventIntegration coordinator
3. Comprehensive end-to-end testing
4. Performance optimization
5. Documentation and examples

**Deliverables:**
- `/src/ui/app_enhanced.py`
- `/src/ui/integration/event_coordinator.py`
- Full test suite
- User documentation

**Success Criteria:**
- All 251 existing tests still pass
- New UI tests pass (50+ tests)
- 60fps maintained during all interactions
- Memory usage < 100MB baseline increase

---

## Technical Specifications

### Technology Stack

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| TUI Framework | Textual | 0.82.0+ | Modern async framework, rich widgets |
| Animation | Rich | 13.7.0+ | High-quality console rendering |
| Async Runtime | asyncio | stdlib | Native async/await support |
| Vector Search | FAISS | 1.12.0+ | Already integrated, fast similarity |
| Event Bus | Custom | - | Existing AsyncEventBus |
| Testing | pytest-asyncio | 0.23.0+ | Async test support |

### Performance Requirements

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Startup Time | < 2s | < 3s |
| Panel Resize | < 50ms | < 100ms |
| Risk Analysis | < 200ms | < 500ms |
| Autocomplete | < 150ms | < 300ms |
| Frame Rate | 60fps | 30fps |
| Memory Overhead | < 100MB | < 200MB |

### API Contracts

#### Event Types

```python
# Typing State Changed
Event(
    type='typing_state_changed',
    data={'is_typing': bool},
    priority=EventPriority.NORMAL
)

# Command Preview Request
Event(
    type='command_preview_request',
    data={'command': str},
    priority=EventPriority.HIGH
)

# Risk Analysis Complete
Event(
    type='risk_analysis_complete',
    data={'analysis': Dict[str, Any]},
    priority=EventPriority.HIGH
)

# Suggestion Request
Event(
    type='suggestion_request',
    data={
        'query': str,
        'embedding': np.ndarray,
        'context': Dict[str, Any]
    },
    priority=EventPriority.NORMAL
)

# Suggestions Ready
Event(
    type='suggestions_ready',
    data={'candidates': List[CompletionCandidate]},
    priority=EventPriority.NORMAL
)
```

---

## Performance Considerations

### Async Architecture Best Practices

1. **Non-Blocking UI Thread**
   - All heavy computation in `asyncio.to_thread()`
   - Risk analysis, embeddings, FAISS search off main thread
   - UI updates only in main event loop

2. **Debouncing Strategy**
   - Typing input: 300ms debounce before risk analysis
   - Autocomplete: 150ms debounce before search
   - Panel resize: immediate but animated over 100ms

3. **Caching Strategy**
   - Panel enrichment cache (hit rate target: 60%)
   - Autocomplete history cache (last 100 items)
   - Schema metadata cache (TTL: 5 minutes)

4. **Resource Pooling**
   - Panel enrichment: 4 worker pool
   - Event bus: 1000 event queue
   - Connection pool: per MCP client config

### Memory Management

```python
class MemoryMonitor:
    """Monitor memory usage and trigger cleanup."""

    THRESHOLDS = {
        'warning': 150 * 1024 * 1024,  # 150MB
        'critical': 200 * 1024 * 1024   # 200MB
    }

    async def monitor_loop(self) -> None:
        """Continuous memory monitoring."""
        while True:
            await asyncio.sleep(5.0)  # Check every 5s

            current = self._get_memory_usage()

            if current > self.THRESHOLDS['critical']:
                await self._emergency_cleanup()
            elif current > self.THRESHOLDS['warning']:
                await self._gradual_cleanup()

    async def _gradual_cleanup(self) -> None:
        """Gradual cache cleanup."""
        # Clear enrichment cache older than 5 minutes
        # Trim autocomplete history to last 50
        # Clear schema cache for unused connections
        pass
```

---

## Testing Strategy

### Unit Tests

```python
# Example: MatrixRainWidget Test
@pytest.mark.asyncio
async def test_matrix_rain_animation():
    """Test matrix rain renders without errors."""
    widget = MatrixRainWidget()

    # Mount in test app
    async with widget.run_test() as pilot:
        await pilot.pause(0.1)

        # Check columns initialized
        assert len(widget.columns) > 0

        # Check rendering
        rendered = widget.render()
        assert rendered is not None

# Example: CommandPreviewWidget Test
@pytest.mark.asyncio
async def test_command_preview_risk_detection():
    """Test risk analysis updates preview widget."""
    analyzer = SQLRiskAnalyzer()
    widget = CommandPreviewWidget(analyzer)

    async with widget.run_test() as pilot:
        # Analyze high-risk command
        await widget.analyze_command("DELETE FROM users")
        await pilot.pause(0.5)

        # Check risk level displayed
        assert "HIGH" in widget.render_str()
        assert widget.has_class("risk-high")
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_end_to_end_command_flow():
    """Test complete command input flow."""
    app = EnhancedAIShellApp()

    async with app.run_test() as pilot:
        # Type dangerous command
        prompt = app.query_one(SmartPromptPanel)
        await pilot.press("D", "E", "L", "E", "T", "E")
        await pilot.pause(0.4)  # Wait for debounce

        # Check preview appeared
        preview = app.query_one(CommandPreviewWidget)
        assert preview.has_class("visible")
        assert "HIGH" in preview.render_str()

        # Continue typing to add WHERE clause
        await pilot.press(" ", "W", "H", "E", "R", "E")
        await pilot.pause(0.4)

        # Check risk downgraded
        assert "MEDIUM" in preview.render_str()
```

### Performance Tests

```python
@pytest.mark.performance
async def test_autocomplete_performance():
    """Ensure autocomplete responds within 150ms."""
    completer = IntelligentCompleter(vector_db)
    engine = ContextAwareSuggestionEngine(completer, event_bus)

    query = "SELECT * FROM use"

    start = time.perf_counter()
    context = await engine.get_context(query, len(query))
    embedding = await embed(query)
    candidates = completer.get_completions(query, embedding, context)
    duration = (time.perf_counter() - start) * 1000

    assert duration < 150, f"Autocomplete took {duration}ms (limit: 150ms)"
    assert len(candidates) > 0
```

---

## Appendix

### A. Textual Widget Hierarchy

```
App (EnhancedAIShellApp)
│
├─ Screen (MatrixStartupScreen)
│   ├─ MatrixRainWidget
│   └─ Container
│       ├─ Static (title)
│       ├─ HealthCheckGrid
│       ├─ ProgressBar
│       └─ Static (status)
│
└─ Screen (MainAppScreen)
    └─ DynamicPanelContainer
        ├─ OutputPanel (ScrollableContainer)
        │   └─ RichLog
        │
        ├─ ModulePanel (ScrollableContainer)
        │   └─ Static (enriched content)
        │
        └─ SmartPromptPanel (Container)
            ├─ CommandPreviewWidget (overlay)
            ├─ SmartSuggestionList (dropdown)
            └─ TextArea (input)
```

### B. CSS Styling Guidelines

```css
/* Color Scheme - Cyberpunk Theme */
App {
    background: $surface;
}

.risk-low {
    background: $success-darken-2;
    border: tall $success;
}

.risk-medium {
    background: $warning-darken-2;
    border: tall $warning;
}

.risk-high {
    background: $error-darken-2;
    border: tall $error;
}

.risk-critical {
    background: $error;
    border: thick $error;
    color: $text;
}

.suggestion-item {
    padding: 0 1;
}

.suggestion-item:hover {
    background: $primary-darken-2;
}

.matrix-column {
    color: $success;
}
```

### C. File Structure (New Files)

```
src/ui/
├── screens/
│   ├── __init__.py
│   ├── startup_screen.py          # MatrixStartupScreen
│   └── main_screen.py              # MainAppScreen
│
├── widgets/
│   ├── __init__.py
│   ├── matrix_rain.py              # MatrixRainWidget
│   ├── command_preview.py          # CommandPreviewWidget
│   ├── suggestion_list.py          # SmartSuggestionList
│   ├── risk_indicator.py           # RiskIndicator
│   └── health_check_grid.py        # HealthCheckGrid
│
├── containers/
│   ├── __init__.py
│   └── dynamic_panel_container.py  # DynamicPanelContainer
│
├── engines/
│   ├── __init__.py
│   └── context_suggestion.py       # ContextAwareSuggestionEngine
│
├── integration/
│   ├── __init__.py
│   └── event_coordinator.py        # UIEventIntegration
│
├── utils/
│   ├── __init__.py
│   ├── content_tracker.py          # ContentSizeTracker
│   └── memory_monitor.py           # MemoryMonitor
│
├── app_enhanced.py                 # EnhancedAIShellApp
├── app.py                          # (existing mock)
├── panel_manager.py                # (enhanced)
└── prompt_handler.py               # (existing)

src/core/
└── health_checks.py                # HealthCheckRunner

src/database/
└── impact_estimator.py             # ImpactEstimator

tests/ui/
├── test_matrix_startup.py
├── test_dynamic_panels.py
├── test_command_preview.py
├── test_smart_suggestions.py
└── test_integration.py
```

### D. Configuration Extensions

```yaml
# ~/.ai-shell/config.yaml additions

ui:
  framework: textual

  # Startup animation
  startup:
    animation_enabled: true
    matrix_style: true
    health_checks_parallel: true
    skip_on_error: false

  # Panel management
  panels:
    weights:
      output: 0.5
      module: 0.3
      prompt: 0.2

    resize:
      smooth_animation: true
      animation_duration_ms: 100
      debounce_ms: 50

    typing_priority: prompt
    idle_priority: balanced

  # Command preview
  preview:
    enabled: true
    debounce_ms: 300
    auto_hide_low_risk: true
    show_impact_estimation: true

  # Smart suggestions
  suggestions:
    enabled: true
    debounce_ms: 150
    max_displayed: 10
    show_scores: true
    show_icons: true
    preview_pane: true

  # Performance
  performance:
    target_fps: 60
    memory_warning_mb: 150
    memory_critical_mb: 200
    cleanup_interval_s: 5
```

---

## Architecture Decision Records (ADRs)

### ADR-001: Textual Framework for TUI

**Status:** Accepted
**Date:** 2025-10-04
**Context:** Need modern async TUI framework for advanced UI features
**Decision:** Use Textual 0.82.0+
**Consequences:**
- Positive: Rich widget library, async-native, excellent documentation
- Positive: Built-in animation support, CSS-like styling
- Negative: Learning curve for team
- Negative: Relatively new framework (potential bugs)

---

### ADR-002: Event-Driven UI Integration

**Status:** Accepted
**Date:** 2025-10-04
**Context:** UI needs to react to core service results without blocking
**Decision:** Leverage existing AsyncEventBus for all UI-service communication
**Consequences:**
- Positive: Decoupled architecture, testable components
- Positive: Non-blocking operations, responsive UI
- Negative: Complexity in event flow debugging
- Mitigation: Comprehensive event logging and visualization tools

---

### ADR-003: Async-First Implementation

**Status:** Accepted
**Date:** 2025-10-04
**Context:** All heavy operations must not block UI thread
**Decision:** Use `asyncio.to_thread()` for all CPU/IO intensive work
**Consequences:**
- Positive: Smooth 60fps UI during all operations
- Positive: Better resource utilization
- Negative: Increased complexity in coordination
- Mitigation: Clear async/sync boundaries, comprehensive testing

---

### ADR-004: Component-Based Widget Design

**Status:** Accepted
**Date:** 2025-10-04
**Context:** Need maintainable, testable UI components
**Decision:** Each feature as isolated Textual widget with clear interface
**Consequences:**
- Positive: Easy to test, reusable components
- Positive: Clear separation of concerns
- Negative: More files to manage
- Mitigation: Clear directory structure, comprehensive documentation

---

**End of Architecture Document**

**Version:** 1.0
**Authors:** AI-Shell Architecture Team
**Review Status:** Ready for Implementation
**Next Steps:** Review → Approval → Phase 11.1 Implementation
