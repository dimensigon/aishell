# Cognitive AI Features

This directory contains advanced cognitive AI features integrated from AIShell.

## Features

### 1. Cognitive Memory (FAISS-based)
**Status**: Disabled by default
**Dependencies**: `faiss-cpu`, `numpy`

Semantic memory system that learns from every interaction:
- FAISS-based semantic search across command history
- Automatic pattern recognition
- Cross-session learning
- Command suggestions based on context
- Knowledge export/import for team sharing

**Enable**:
```python
from src.cognitive import enable_feature, get_cognitive_memory

enable_feature('cognitive_memory')
memory = get_cognitive_memory()
```

**Environment Variables**:
```bash
export AISHELL_MEMORY_ENABLED=true
export AISHELL_MEMORY_DIR=~/.aishell/memory
```

### 2. Anomaly Detection
**Status**: Disabled by default
**Dependencies**: `psutil`, `numpy`

ML-based anomaly detection with auto-remediation:
- Performance anomaly detection
- Resource usage monitoring
- Error rate analysis
- Pattern-based detection
- Automatic fix suggestions
- Optional auto-remediation (requires approval)

### 3. Autonomous DevOps
**Status**: Disabled by default
**Dependencies**: Cognitive Memory, Anomaly Detection

Self-managing infrastructure with intelligent optimization.

### 4. MCP Auto-Discovery
**Status**: Enabled by default (safe)

Automatic discovery of MCP servers.

## Installation

### Full Installation (All cognitive features)
```bash
pip install -r requirements.txt -r requirements-cognitive.txt
```

## Configuration

See `config.py` for detailed configuration options and `docs/COGNITIVE_FEATURES.md` for full documentation.
