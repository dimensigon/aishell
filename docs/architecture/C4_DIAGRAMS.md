# AI-Shell C4 Architecture Diagrams

## C4 Model Overview

The C4 model provides a hierarchical way to visualize software architecture through four levels of abstraction: Context, Containers, Components, and Code.

## Level 1: System Context Diagram

```
                                    ┌─────────────┐
                                    │    User     │
                                    │ (Developer) │
                                    └──────┬──────┘
                                           │
                                           │ Executes commands
                                           │ Gets AI assistance
                                           ▼
                              ┌────────────────────────┐
                              │                        │
                              │      AI-Shell          │
                              │                        │
                              │  Intelligent CLI with  │
                              │  MCP & LLM Integration │
                              │                        │
                              └───┬────────────────┬───┘
                                  │                │
                    ┌─────────────┘                └─────────────┐
                    │                                            │
                    ▼                                            ▼
         ┌─────────────────────┐                      ┌──────────────────┐
         │                     │                      │                  │
         │   MCP Servers       │                      │  Local LLM       │
         │                     │                      │  Providers       │
         │ - Filesystem        │                      │                  │
         │ - Database          │                      │ - Ollama         │
         │ - Git               │                      │ - LlamaCPP       │
         │ - Custom Tools      │                      │ - Custom         │
         │                     │                      │                  │
         └─────────────────────┘                      └──────────────────┘
                    │                                            │
                    │                                            │
                    ▼                                            ▼
         ┌─────────────────────┐                      ┌──────────────────┐
         │                     │                      │                  │
         │  External Systems   │                      │  Model Files     │
         │                     │                      │                  │
         │ - File System       │                      │ - GGUF models    │
         │ - Databases         │                      │ - Safetensors    │
         │ - APIs              │                      │ - PyTorch        │
         │ - Version Control   │                      │                  │
         │                     │                      │                  │
         └─────────────────────┘                      └──────────────────┘
```

**Key Relationships:**
- User interacts with AI-Shell through CLI/REPL
- AI-Shell connects to MCP Servers for tool access
- AI-Shell uses Local LLM Providers for AI capabilities
- MCP Servers interact with external systems
- LLM Providers load and use model files

## Level 2: Container Diagram

```
                                    ┌─────────────┐
                                    │    User     │
                                    └──────┬──────┘
                                           │
                           ┌───────────────┼───────────────┐
                           │               │               │
                           ▼               ▼               ▼
                    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
                    │ CLI Parser  │ │ REPL Shell  │ │  Formatter  │
                    │             │ │             │ │             │
                    │ Commander.js│ │ Readline    │ │ Chalk/Table │
                    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
                           │               │               │
                           └───────────────┼───────────────┘
                                           │
                                           ▼
                              ┌────────────────────────┐
                              │  Command Processing    │
                              │       Pipeline         │
                              │                        │
                              │ - Interpreter          │
                              │ - Intent Classifier    │
                              │ - Executor             │
                              └───┬────────────────┬───┘
                                  │                │
                    ┌─────────────┘                └─────────────┐
                    │                                            │
                    ▼                                            ▼
         ┌─────────────────────┐                      ┌──────────────────┐
         │                     │                      │                  │
         │   MCP Client        │                      │  AI Orchestrator │
         │   Manager           │                      │                  │
         │                     │◄─────────────────────┤ - LLM Provider   │
         │ - Protocol Handler  │  Requests tools      │ - Context Mgr    │
         │ - Server Manager    │                      │ - Tool Execution │
         │ - Message Queue     │                      │                  │
         │                     │                      │                  │
         └──────────┬──────────┘                      └──────────────────┘
                    │                                            │
                    │                                            │
                    ▼                                            ▼
         ┌─────────────────────┐                      ┌──────────────────┐
         │                     │                      │                  │
         │  Infrastructure     │                      │  Memory Store    │
         │                     │                      │                  │
         │ - Config Manager    │◄─────────────────────┤ - SQLite DB      │
         │ - Plugin System     │  Reads/Writes        │ - Namespace Mgr  │
         │ - Logger            │                      │ - Cache Layer    │
         │                     │                      │                  │
         └─────────────────────┘                      └──────────────────┘
```

**Container Descriptions:**

1. **CLI Parser**: Parses command-line arguments and flags
2. **REPL Shell**: Interactive shell with autocomplete and history
3. **Formatter**: Formats output for terminal display
4. **Command Processing Pipeline**: Core command interpretation and execution
5. **MCP Client Manager**: Manages MCP server connections
6. **AI Orchestrator**: Coordinates LLM and tool execution
7. **Infrastructure**: Configuration, plugins, logging
8. **Memory Store**: Persistent storage for context and state

## Level 3: Component Diagram - Command Processing

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Command Processing Container                     │
│                                                                      │
│   ┌──────────────┐         ┌──────────────┐         ┌────────────┐ │
│   │              │         │              │         │            │ │
│   │   Parser     │────────▶│ Interpreter  │────────▶│ Classifier │ │
│   │              │ Parsed  │              │ Intent  │            │ │
│   └──────────────┘ Command └──────────────┘ Analysis└────────────┘ │
│          │                         │                       │        │
│          │                         │                       │        │
│          ▼                         ▼                       ▼        │
│   ┌──────────────┐         ┌──────────────┐         ┌────────────┐ │
│   │              │         │              │         │            │ │
│   │  Validator   │         │   Enricher   │         │   Router   │ │
│   │              │         │              │         │            │ │
│   └──────────────┘         └──────────────┘         └────────────┘ │
│          │                         │                       │        │
│          └─────────────┬───────────┘                       │        │
│                        │                                   │        │
│                        ▼                                   │        │
│              ┌──────────────────┐                          │        │
│              │                  │                          │        │
│              │  Command Router  │◄─────────────────────────┘        │
│              │                  │                                   │
│              └────────┬─────────┘                                   │
│                       │                                             │
│          ┌────────────┼────────────┐                                │
│          │            │            │                                │
│          ▼            ▼            ▼                                │
│   ┌────────────┐ ┌─────────┐ ┌──────────┐                          │
│   │            │ │         │ │          │                          │
│   │   Direct   │ │   AI    │ │  Hybrid  │                          │
│   │  Executor  │ │ Executor│ │ Executor │                          │
│   │            │ │         │ │          │                          │
│   └────────────┘ └─────────┘ └──────────┘                          │
│          │            │            │                                │
│          └────────────┼────────────┘                                │
│                       │                                             │
│                       ▼                                             │
│              ┌─────────────────┐                                    │
│              │                 │                                    │
│              │ Result Formatter│                                    │
│              │                 │                                    │
│              └─────────────────┘                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Level 3: Component Diagram - MCP Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MCP Client Manager Container                    │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                    Server Registry                            │  │
│   │                                                               │  │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │  │
│   │  │ Filesystem │  │  Database  │  │    Git     │  ...       │  │
│   │  │   Server   │  │   Server   │  │   Server   │            │  │
│   │  └────────────┘  └────────────┘  └────────────┘            │  │
│   │                                                               │  │
│   └───────────────────────────────┬───────────────────────────────┘  │
│                                   │                                  │
│                                   ▼                                  │
│                          ┌─────────────────┐                         │
│                          │                 │                         │
│                          │ Connection Pool │                         │
│                          │                 │                         │
│                          └────────┬────────┘                         │
│                                   │                                  │
│              ┌────────────────────┼────────────────────┐             │
│              │                    │                    │             │
│              ▼                    ▼                    ▼             │
│     ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│     │                 │  │                 │  │                 │   │
│     │ Stdio Adapter   │  │  HTTP Adapter   │  │ WebSocket       │   │
│     │                 │  │                 │  │  Adapter        │   │
│     └────────┬────────┘  └────────┬────────┘  └────────┬────────┘   │
│              │                    │                    │             │
│              └────────────────────┼────────────────────┘             │
│                                   │                                  │
│                                   ▼                                  │
│                          ┌─────────────────┐                         │
│                          │                 │                         │
│                          │ Protocol Handler│                         │
│                          │                 │                         │
│                          │ - Initialize    │                         │
│                          │ - Tool Calls    │                         │
│                          │ - Resources     │                         │
│                          │ - Prompts       │                         │
│                          │                 │                         │
│                          └────────┬────────┘                         │
│                                   │                                  │
│                                   ▼                                  │
│                          ┌─────────────────┐                         │
│                          │                 │                         │
│                          │  Message Queue  │                         │
│                          │                 │                         │
│                          │ - Request Queue │                         │
│                          │ - Response Map  │                         │
│                          │ - Event Bus     │                         │
│                          │                 │                         │
│                          └─────────────────┘                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Level 3: Component Diagram - AI Orchestration

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AI Orchestrator Container                       │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                    LLM Provider Factory                       │  │
│   │                                                               │  │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │  │
│   │  │   Ollama   │  │  LlamaCPP  │  │   Custom   │            │  │
│   │  │  Provider  │  │  Provider  │  │  Provider  │            │  │
│   │  └────────────┘  └────────────┘  └────────────┘            │  │
│   │                                                               │  │
│   └───────────────────────────────┬───────────────────────────────┘  │
│                                   │                                  │
│                                   ▼                                  │
│                          ┌─────────────────┐                         │
│                          │                 │                         │
│                          │  Prompt Builder │                         │
│                          │                 │                         │
│                          │ - Context Inject│                         │
│                          │ - Tool Format   │                         │
│                          │ - History Merge │                         │
│                          │                 │                         │
│                          └────────┬────────┘                         │
│                                   │                                  │
│                                   ▼                                  │
│                          ┌─────────────────┐                         │
│                          │                 │                         │
│                          │  LLM Executor   │                         │
│                          │                 │                         │
│                          │ - Generate      │                         │
│                          │ - Stream        │                         │
│                          │ - Tool Calling  │                         │
│                          │                 │                         │
│                          └────────┬────────┘                         │
│                                   │                                  │
│              ┌────────────────────┼────────────────────┐             │
│              │                    │                    │             │
│              ▼                    ▼                    ▼             │
│     ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│     │                 │  │                 │  │                 │   │
│     │ Tool Call       │  │  MCP Tool       │  │ Result          │   │
│     │ Parser          │  │  Executor       │  │ Aggregator      │   │
│     │                 │  │                 │  │                 │   │
│     └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│              │                    │                    │             │
│              └────────────────────┼────────────────────┘             │
│                                   │                                  │
│                                   ▼                                  │
│                          ┌─────────────────┐                         │
│                          │                 │                         │
│                          │ Context Manager │                         │
│                          │                 │                         │
│                          │ - History       │                         │
│                          │ - Variables     │                         │
│                          │ - Session State │                         │
│                          │                 │                         │
│                          └─────────────────┘                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Sequence Diagrams

### Direct Command Execution

```
User    CLI Parser  Interpreter  Classifier  Executor    System
 │          │           │            │          │          │
 │ ls -la   │           │            │          │          │
 ├─────────>│           │            │          │          │
 │          │  Parse    │            │          │          │
 │          ├──────────>│            │          │          │
 │          │           │  Classify  │          │          │
 │          │           ├───────────>│          │          │
 │          │           │            │ Direct   │          │
 │          │           │<───────────┤ Command  │          │
 │          │           │            │          │          │
 │          │           │  Execute   │          │          │
 │          │           ├───────────────────────>│          │
 │          │           │            │          │  exec    │
 │          │           │            │          ├─────────>│
 │          │           │            │          │  result  │
 │          │           │            │          │<─────────┤
 │          │           │  Result    │          │          │
 │          │           │<───────────────────────┤          │
 │  Output  │           │            │          │          │
 │<─────────┤           │            │          │          │
 │          │           │            │          │          │
```

### AI-Assisted Command

```
User    CLI Parser  Classifier  Orchestrator  LLM    MCP     System
 │          │           │            │         │      │        │
 │ "show   │           │            │         │      │        │
 │ largest │           │            │         │      │        │
 │  files" │           │            │         │      │        │
 ├─────────>│           │            │         │      │        │
 │          │  Classify │            │         │      │        │
 │          ├──────────>│            │         │      │        │
 │          │           │ Task       │         │      │        │
 │          │           │ Description│         │      │        │
 │          │<──────────┤            │         │      │        │
 │          │           │            │         │      │        │
 │          │  Process  │            │         │      │        │
 │          ├────────────────────────>│         │      │        │
 │          │           │            │ Build   │      │        │
 │          │           │            │ Prompt  │      │        │
 │          │           │            │         │      │        │
 │          │           │            │ Generate│      │        │
 │          │           │            ├────────>│      │        │
 │          │           │            │ "du -sh │      │        │
 │          │           │            │ * | sort│      │        │
 │          │           │            │ -h"     │      │        │
 │          │           │            │<────────┤      │        │
 │          │           │            │         │      │        │
 │          │           │            │ Execute │      │        │
 │          │           │            ├────────────────>│        │
 │          │           │            │         │ exec │        │
 │          │           │            │         │      ├───────>│
 │          │           │            │         │ result       │
 │          │           │            │         │      │<───────┤
 │          │           │            │<────────────────┤        │
 │          │  Result   │            │         │      │        │
 │          │<────────────────────────┤         │      │        │
 │  Output  │           │            │         │      │        │
 │<─────────┤           │            │         │      │        │
 │          │           │            │         │      │        │
```

### MCP Tool Execution

```
Orchestrator  MCP Manager  MCP Server  Tool Implementation
      │            │            │              │
      │ List Tools │            │              │
      ├───────────>│            │              │
      │            │  Request   │              │
      │            ├───────────>│              │
      │            │   Tools    │              │
      │            │<───────────┤              │
      │   Tools    │            │              │
      │<───────────┤            │              │
      │            │            │              │
      │ Execute    │            │              │
      │ Tool       │            │              │
      ├───────────>│            │              │
      │            │  Call      │              │
      │            ├───────────>│              │
      │            │            │   Execute    │
      │            │            ├─────────────>│
      │            │            │   Result     │
      │            │            │<─────────────┤
      │            │  Response  │              │
      │            │<───────────┤              │
      │   Result   │            │              │
      │<───────────┤            │              │
      │            │            │              │
```

## Deployment Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User's Machine                           │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │              AI-Shell Installation                  │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │    │
│  │  │             │  │             │  │            │ │    │
│  │  │   CLI App   │  │   Config    │  │  Plugins   │ │    │
│  │  │             │  │             │  │            │ │    │
│  │  └─────────────┘  └─────────────┘  └────────────┘ │    │
│  │                                                     │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                   │
│  ┌──────────────────────┼──────────────────────────────┐    │
│  │                      │                              │    │
│  │  ┌───────────────────▼───────────┐  ┌─────────────┐│    │
│  │  │                               │  │             ││    │
│  │  │     Memory Store              │  │   Model     ││    │
│  │  │     (.ai-shell/memory.db)     │  │   Files     ││    │
│  │  │                               │  │  (.models/) ││    │
│  │  └───────────────────────────────┘  └─────────────┘│    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                         │                                   │
│                         │                                   │
│  ┌──────────────────────┼──────────────────────────────┐    │
│  │      MCP Servers     │                              │    │
│  │                      │                              │    │
│  │  ┌───────────────────▼───────────┐                 │    │
│  │  │                               │                 │    │
│  │  │   Filesystem MCP Server       │                 │    │
│  │  │   (Node.js process)           │                 │    │
│  │  │                               │                 │    │
│  │  └───────────────────────────────┘                 │    │
│  │                                                     │    │
│  │  ┌───────────────────────────────┐                 │    │
│  │  │                               │                 │    │
│  │  │   Database MCP Server         │                 │    │
│  │  │   (Python process)            │                 │    │
│  │  │                               │                 │    │
│  │  └───────────────────────────────┘                 │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                         │                                   │
│  ┌──────────────────────┼──────────────────────────────┐    │
│  │    LLM Services      │                              │    │
│  │                      │                              │    │
│  │  ┌───────────────────▼───────────┐                 │    │
│  │  │                               │                 │    │
│  │  │   Ollama Service              │                 │    │
│  │  │   (localhost:11434)           │                 │    │
│  │  │                               │                 │    │
│  │  └───────────────────────────────┘                 │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌──────────┐
│   User   │
│  Input   │
└─────┬────┘
      │
      ▼
┌──────────────────┐
│   Parse Input    │──┐
│   Classify       │  │ Context
└─────┬────────────┘  │
      │               │
      ▼               ▼
┌──────────────────────────┐
│  Decision Point          │
│                          │
│  Direct? ──Yes──> System │
│    │                     │
│   No                     │
│    │                     │
│    ▼                     │
│  AI Assisted?            │
└─────┬────────────────────┘
      │
      ▼
┌──────────────────┐
│  Build Prompt    │<──┐
│  with Context    │   │
└─────┬────────────┘   │
      │                │
      ▼                │
┌──────────────────┐   │
│  Query LLM       │   │ Tools/Resources
│  with Tools      │   │
└─────┬────────────┘   │
      │                │
      ▼                │
┌──────────────────┐   │
│  Parse Response  │   │
│  Extract Tools   │   │
└─────┬────────────┘   │
      │                │
      ▼                │
┌──────────────────┐   │
│  Execute Tools   │───┘
│  via MCP         │
└─────┬────────────┘
      │
      ▼
┌──────────────────┐
│  Aggregate       │
│  Results         │
└─────┬────────────┘
      │
      ▼
┌──────────────────┐
│  Format Output   │
│  Display         │
└─────┬────────────┘
      │
      ▼
┌──────────────────┐
│  Update Context  │
│  Save History    │
└──────────────────┘
```

---

**Diagram Version**: 1.0.0
**Last Updated**: 2025-10-03
**Notation**: C4 Model + UML Sequence
