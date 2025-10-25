# Phase 11: Component Diagrams & Class Structures

## Component Interaction Diagram

```mermaid
graph TB
    subgraph "UI Layer - Textual Framework"
        A[EnhancedAIShellApp]
        B[MatrixStartupScreen]
        C[DynamicPanelContainer]
        D[OutputPanel]
        E[ModulePanel]
        F[SmartPromptPanel]
        G[CommandPreviewWidget]
        H[SmartSuggestionList]
    end

    subgraph "Event Coordination"
        I[UIEventIntegration]
        J[AsyncEventBus]
    end

    subgraph "Core Services"
        K[SQLRiskAnalyzer]
        L[IntelligentCompleter]
        M[ModulePanelEnricher]
        N[HealthCheckRunner]
    end

    subgraph "Data Layer"
        O[VectorDatabase - FAISS]
        P[Embedding Provider]
    end

    A --> B
    A --> C
    C --> D
    C --> E
    C --> F
    F --> G
    F --> H

    G --> I
    H --> I
    F --> I

    I --> J
    J --> K
    J --> L
    J --> M

    L --> O
    L --> P
    K --> M

    B --> N
    N --> J
```

## Class Hierarchy: MatrixStartupScreen

```mermaid
classDiagram
    class Screen {
        +compose() ComposeResult
        +on_mount() None
    }

    class MatrixStartupScreen {
        -check_results: Dict~str, CheckResult~
        -animation_task: Optional~Task~
        -checks_complete: bool
        +compose() ComposeResult
        +on_mount() None
        -_run_matrix_animation() None
        -_run_system_checks() None
        -_transition_to_main() None
        +action_skip() None
    }

    class MatrixRainWidget {
        -columns: List~MatrixColumn~
        -chars: List~str~
        +on_mount() None
        +update_columns() None
        +render() RenderableType
    }

    class HealthCheckGrid {
        -checks: Dict~str, CheckStatus~
        +update_check(name, status) None
        +render() RenderableType
    }

    class HealthCheckRunner {
        +CHECKS: List~HealthCheck~
        +run_all_checks(callback) Dict
        -run_check(check) Tuple
    }

    Screen <|-- MatrixStartupScreen
    MatrixStartupScreen *-- MatrixRainWidget
    MatrixStartupScreen *-- HealthCheckGrid
    MatrixStartupScreen --> HealthCheckRunner
```

## Class Hierarchy: DynamicPanelContainer

```mermaid
classDiagram
    class Container {
        +compose() ComposeResult
    }

    class DynamicPanelContainer {
        -panel_manager: DynamicPanelManager
        -output_panel: OutputPanel
        -module_panel: ModulePanel
        -prompt_panel: SmartPromptPanel
        +compose() ComposeResult
        +on_resize(event) None
        +on_typing_state_changed(message) None
        -_recalculate_layout(height) None
        -_animate_resize(panel, height) None
    }

    class DynamicPanelManager {
        -panel_weights: Dict
        -active_typing: bool
        -content_sizes: Dict
        +calculate_dimensions(height) Dict
        +set_typing_state(typing) None
        +update_content_size(panel, lines) None
        -_calculate_prompt_lines() int
    }

    class ContentSizeTracker {
        -panel_manager: DynamicPanelManager
        -content_observers: Dict
        +register_panel(id, observer) None
        +monitor_loop() None
    }

    Container <|-- DynamicPanelContainer
    DynamicPanelContainer --> DynamicPanelManager
    DynamicPanelContainer --> ContentSizeTracker
```

## Class Hierarchy: Command Preview System

```mermaid
classDiagram
    class Static {
        +update(content) None
        +render() RenderableType
    }

    class CommandPreviewWidget {
        -risk_analyzer: SQLRiskAnalyzer
        -current_analysis: Optional~Dict~
        -analysis_task: Optional~Task~
        +analyze_command(command) None
        -_run_analysis(command) None
        -_update_display(analysis) None
        -_build_content(analysis) RenderableType
        -_is_sql_command(command) bool
        -_hide() None
    }

    class RiskIndicator {
        -risk_level: str
        +render() RenderableType
    }

    class ImpactEstimator {
        +estimate_impact(sql, connection) Dict
        -_extract_tables(sql) List
        -_estimate_table_rows(table, conn) int
        -_estimate_execution_time(sql, rows) float
        -_classify_resource_usage(rows) str
    }

    class SQLRiskAnalyzer {
        -RISK_PATTERNS: Dict
        -compiled_patterns: Dict
        +analyze(sql) Dict
        -_detect_risk_level(sql) RiskLevel
        -_generate_warnings(sql, level) List
        -_check_common_issues(sql) List
        +get_confirmation_message(analysis) str
    }

    Static <|-- CommandPreviewWidget
    CommandPreviewWidget *-- RiskIndicator
    CommandPreviewWidget --> SQLRiskAnalyzer
    CommandPreviewWidget --> ImpactEstimator
```

## Class Hierarchy: Smart Suggestion System

```mermaid
classDiagram
    class OptionList {
        +add_option(option) None
        +clear_options() None
    }

    class SmartSuggestionList {
        -autocompleter: IntelligentCompleter
        -embedding_provider: Any
        -current_suggestions: List~CompletionCandidate~
        -search_task: Optional~Task~
        +search_suggestions(query, context) None
        -_run_search(query, context) None
        -_update_options(candidates) None
        -_get_source_icon(source) str
        -_render_score(score) str
        -_show() None
        -_hide() None
        +on_option_list_option_selected(event) None
    }

    class IntelligentCompleter {
        -vector_db: VectorDatabase
        -pattern_cache: Dict
        -completion_history: List
        +get_completions(query, vector, context, max) List
        -_get_vector_completions(vector, context, max) List
        -_get_pattern_completions(query, context) List
        -_get_syntax_completions(query, context) List
        -_get_history_completions(query) List
        -_deduplicate_candidates(candidates) List
        +register_pattern(pattern, completions) None
        +get_context_aware_completions(...) List
    }

    class ContextAwareSuggestionEngine {
        -autocompleter: IntelligentCompleter
        -event_bus: AsyncEventBus
        -schema_cache: Dict
        -history: List
        +get_context(query, cursor_pos) Dict
        -_detect_statement_type(query) str
        -_infer_expected_object(query, pos) str
        -_get_active_schema() str
        -_extract_recent_tables(history) List
        -_extract_fragment(query, pos) str
    }

    OptionList <|-- SmartSuggestionList
    SmartSuggestionList --> IntelligentCompleter
    SmartSuggestionList --> ContextAwareSuggestionEngine
```

## Sequence Diagram: Command Input Flow

```mermaid
sequenceDiagram
    actor User
    participant Prompt as SmartPromptPanel
    participant Preview as CommandPreviewWidget
    participant Suggest as SmartSuggestionList
    participant Bus as AsyncEventBus
    participant Risk as SQLRiskAnalyzer
    participant Auto as IntelligentCompleter

    User->>Prompt: Type "DELETE FROM users"
    Prompt->>Bus: Publish typing_state_changed
    Prompt->>Bus: Publish command_preview_request

    Bus->>Risk: Analyze command (async)
    Risk-->>Bus: Risk analysis complete
    Bus->>Preview: Update with HIGH risk

    Preview->>Preview: Show risk overlay (red)
    Preview-->>User: Display warnings

    User->>Prompt: Continue typing " WHERE"
    Prompt->>Bus: Publish command_preview_request
    Bus->>Risk: Re-analyze
    Risk-->>Bus: Risk now MEDIUM
    Bus->>Preview: Update display

    User->>Prompt: Press Tab for autocomplete
    Prompt->>Suggest: Trigger suggestion search
    Suggest->>Auto: Get completions with context
    Auto->>Auto: FAISS vector search
    Auto-->>Suggest: Return candidates
    Suggest->>Suggest: Display dropdown
    Suggest-->>User: Show ranked suggestions

    User->>Suggest: Select suggestion
    Suggest->>Prompt: Insert completion
    Prompt-->>User: Updated input
```

## Sequence Diagram: Startup Animation

```mermaid
sequenceDiagram
    actor User
    participant App as EnhancedAIShellApp
    participant Startup as MatrixStartupScreen
    participant Matrix as MatrixRainWidget
    participant Checks as HealthCheckRunner
    participant Bus as AsyncEventBus

    User->>App: Launch AIShell
    App->>Startup: Mount startup screen
    Startup->>Matrix: Start animation task

    par Matrix Animation
        Matrix->>Matrix: Update columns (50ms interval)
        Matrix->>Matrix: Render cascading characters
    and Health Checks
        Startup->>Checks: Run all checks (parallel)
        Checks->>Checks: Check LLM connection (3s timeout)
        Checks->>Checks: Check Vector DB (2s timeout)
        Checks->>Checks: Check MCP Clients (2s timeout)
        Checks->>Bus: Check Event Bus (1s timeout)
        Checks->>Checks: Check Panel Enricher (1s timeout)
    end

    Checks-->>Startup: All results
    Startup->>Startup: Update progress bar
    Startup->>Startup: Display check status

    alt All Critical Checks Pass
        Startup->>App: Transition to main screen
        App->>App: Mount DynamicPanelContainer
        App-->>User: Show main application
    else Critical Check Fails
        Startup->>Startup: Show error message
        Startup-->>User: Display fallback options
    end
```

## Data Flow: Panel Enrichment

```mermaid
graph LR
    A[User Types Command] --> B{Command Type?}
    B -->|SQL Query| C[Panel Enrichment Request]
    B -->|Shell Command| D[Skip Enrichment]

    C --> E[AsyncEventBus]
    E --> F[ModulePanelEnricher Queue]

    F --> G{Priority?}
    G -->|HIGH| H[Worker 1 - Immediate]
    G -->|MEDIUM| I[Worker 2 - Queued]
    G -->|LOW| J[Worker 3/4 - Deferred]

    H --> K[Gather Context]
    I --> K
    J --> K

    K --> L{Cache Hit?}
    L -->|Yes| M[Return Cached Data]
    L -->|No| N[Enrich Panel Data]

    N --> O[Query Database Schema]
    N --> P[Check Recent History]
    N --> Q[Analyze Context]

    O --> R[Merge Results]
    P --> R
    Q --> R

    R --> S[Cache Result]
    M --> T[Update ModulePanel]
    S --> T

    T --> U[User Sees Enriched Info]
```

## State Diagram: Panel Manager States

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> Typing: User starts typing
    Typing --> Idle: User stops typing (1s)
    Typing --> Analyzing: Text change detected

    Analyzing --> PreviewShown: Risk > LOW
    Analyzing --> Idle: Risk = LOW

    PreviewShown --> Typing: User continues
    PreviewShown --> Executing: User submits

    Executing --> ResultDisplay: Command complete
    ResultDisplay --> Idle: After 2s

    Idle --> Resizing: Terminal resize
    Typing --> Resizing: Terminal resize
    Resizing --> Idle: Layout calculated
    Resizing --> Typing: Layout calculated + typing

    note right of Typing
        Prompt panel grows
        Output/Module shrink
    end note

    note right of PreviewShown
        Risk overlay visible
        Panel weights shift
    end note

    note right of Resizing
        Smooth animation
        100ms duration
    end note
```

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Textual    │  │   Textual    │  │   Textual    │  │
│  │   Screens    │  │  Containers  │  │   Widgets    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │         │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼─────────┐
│         ↓                  ↓                  ↓         │
│                  INTEGRATION LAYER                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │          UIEventIntegration Coordinator          │   │
│  └──────────────────────────────────────────────────┘   │
│                           ↕                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │        AsyncEventBus (Priority Queue)            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Risk         │  │ Autocomplete │  │ Panel        │  │
│  │ Analyzer     │  │ Engine       │  │ Enricher     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │         │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼─────────┐
│         ↓                  ↓                  ↓         │
│                     DATA LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   FAISS      │  │  Embedding   │  │   Cache      │  │
│  │  VectorDB    │  │  Provider    │  │  Manager     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Deployment View

```
┌─────────────────────────────────────────────────────────┐
│                   User's Terminal                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Enhanced AIShell Process                 │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │  Main Thread (Event Loop)                  │  │   │
│  │  │  - Textual UI rendering                    │  │   │
│  │  │  - Event bus processing                    │  │   │
│  │  │  - Panel updates                           │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  │                                                  │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │  Worker Thread Pool (4 workers)            │  │   │
│  │  │  - Risk analysis                           │  │   │
│  │  │  - Vector search                           │  │   │
│  │  │  - Panel enrichment                        │  │   │
│  │  │  - Embedding generation                    │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  │                                                  │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │  Memory-Mapped Storage                     │  │   │
│  │  │  - FAISS index (memory-mapped)             │  │   │
│  │  │  - Embedding cache                         │  │   │
│  │  │  - Enrichment cache                        │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────┐
│                External Dependencies                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Ollama     │  │  Database    │  │   MCP        │  │
│  │   (LLM)      │  │  Servers     │  │  Clients     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Performance Optimization Points

```
┌─────────────────────────────────────────────────────────┐
│              Optimization Strategy                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. DEBOUNCING                                          │
│     • Typing input: 300ms before risk analysis          │
│     • Autocomplete: 150ms before vector search          │
│     • Panel resize: Immediate but animated              │
│                                                         │
│  2. CACHING                                             │
│     • Panel enrichment: 60% cache hit rate              │
│     • Autocomplete history: Last 100 items              │
│     • Schema metadata: 5-minute TTL                     │
│                                                         │
│  3. ASYNC THREADING                                     │
│     • All CPU-intensive work in thread pool             │
│     • FAISS searches: asyncio.to_thread()               │
│     • Risk analysis: asyncio.to_thread()                │
│                                                         │
│  4. PRIORITY QUEUING                                    │
│     • CRITICAL: Command execution events                │
│     • HIGH: Risk analysis, command preview              │
│     • NORMAL: Autocomplete, typing state                │
│     • LOW: Panel enrichment, background updates         │
│                                                         │
│  5. MEMORY MANAGEMENT                                   │
│     • Warning threshold: 150MB                          │
│     • Critical threshold: 200MB                         │
│     • Cleanup interval: Every 5 seconds                 │
│     • Gradual cache eviction on warning                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

**Document Version:** 1.0
**Created:** 2025-10-04
**Purpose:** Visual reference for Phase 11 implementation
