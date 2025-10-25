# Cognitive AI Features Integration Guide

## Overview

Advanced cognitive AI features have been integrated from AIShell into the consolidated version. These features are **disabled by default** and use feature flags for gradual adoption.

## Quick Start

### 1. Check What's Available

```python
from src.cognitive import FEATURES

print("Available cognitive features:")
for feature, enabled in FEATURES.items():
    status = "ENABLED" if enabled else "DISABLED"
    print(f"  {feature}: {status}")
```

### 2. Enable a Feature

```python
from src.cognitive import enable_feature, get_cognitive_memory

# Enable cognitive memory
enable_feature('cognitive_memory')

# Get the memory system (lazy loaded)
memory = get_cognitive_memory()

if memory:
    print("Cognitive memory is ready!")
else:
    print("Failed to load - check dependencies")
```

### 3. Install Dependencies (if needed)

```bash
# For cognitive memory
pip install faiss-cpu numpy

# For anomaly detection
pip install psutil numpy

# Or install all cognitive dependencies
pip install -r requirements-cognitive.txt
```

## Features Overview

### 1. Cognitive Memory (106K lines of code)

**What it does:**
- Semantic search across all command history using FAISS
- Automatic pattern recognition and learning
- Command suggestions based on context
- Cross-session knowledge retention
- Team knowledge sharing

**Use cases:**
- "What command did I use last week to deploy?"
- "Suggest commands based on my current directory"
- "What's the success rate of this git workflow?"
- "Share knowledge base with team members"

**Code size:** 30,962 lines

### 2. Anomaly Detection (35K lines of code)

**What it does:**
- ML-based performance anomaly detection
- Resource usage monitoring (CPU, memory, disk, network)
- Error pattern recognition
- Automatic remediation suggestions
- Optional auto-fix for low-risk issues

**Use cases:**
- "Detect when disk space is running low"
- "Alert when error rate increases"
- "Automatically restart crashed services"
- "Predict and prevent system failures"

**Code size:** 35,419 lines

### 3. Autonomous DevOps (40K lines of code)

**What it does:**
- Self-managing infrastructure
- Auto-scaling based on load patterns
- Performance optimization
- Cost optimization
- Deployment automation with rollback

**Use cases:**
- "Scale up services during peak hours"
- "Optimize resource allocation to reduce costs"
- "Automatically deploy tested changes"
- "Self-heal infrastructure issues"

**Code size:** 39,574 lines

**⚠️ Warning:** Most powerful but also most risky. Start with monitoring only.

### 4. MCP Auto-Discovery

**What it does:**
- Automatically discover available MCP servers
- Detect server capabilities
- Manual approval for connections

**Use cases:**
- "Find all MCP servers on the network"
- "What tools does this MCP server provide?"
- "Auto-connect to known safe servers"

**Status:** Enabled by default (safe)

## Integration Architecture

```
aishell-consolidated/
├── src/
│   └── cognitive/
│       ├── __init__.py              # Feature flags & lazy loading
│       ├── config.py                # Configuration management
│       ├── memory.py                # Cognitive memory (30,962 lines)
│       ├── anomaly_detector.py      # Anomaly detection (35,419 lines)
│       ├── autonomous_devops.py     # Autonomous DevOps (39,574 lines)
│       └── README.md               # Detailed usage guide
├── requirements-cognitive.txt       # Optional dependencies
└── docs/
    └── COGNITIVE_FEATURES.md       # This file
```

## Safety Features

1. **Feature Flags**: All advanced features disabled by default
2. **Lazy Loading**: Dependencies only loaded when feature is enabled
3. **Graceful Degradation**: Missing dependencies don't crash the system
4. **Approval Gates**: High-risk operations require manual approval
5. **Risk Scoring**: All operations have risk scores (1-5)
6. **Rollback Plans**: All changes include rollback procedures
7. **Audit Logging**: All actions are logged for review

## Configuration Methods

### Method 1: Python API (Runtime)

```python
from src.cognitive import enable_feature, update_config

# Enable feature
enable_feature('cognitive_memory')

# Update configuration
update_config('memory', {
    'max_memories': 50000,
    'learning_rate': 0.2
})
```

### Method 2: Environment Variables

```bash
# Memory
export AISHELL_MEMORY_ENABLED=true
export AISHELL_MEMORY_DIR=~/.aishell/memory

# Anomaly detection
export AISHELL_ANOMALY_ENABLED=true
export AISHELL_AUTO_REMEDIATION=false

# Autonomous DevOps
export AISHELL_DEVOPS_ENABLED=false
export AISHELL_AUTO_SCALING=false
```

### Method 3: Configuration File

Create `~/.aishell/cognitive.yaml`:

```yaml
features:
  cognitive_memory: true
  anomaly_detection: true
  autonomous_devops: false
  mcp_discovery: true

memory:
  directory: ~/.aishell/memory
  max_memories: 100000
  learning_rate: 0.1

anomaly_detection:
  auto_remediation: false
  max_remediation_risk: 3

autonomous_devops:
  auto_scaling: false
  require_approval_above_risk: 3
```

## Gradual Adoption Path

### Phase 1: MCP Discovery (Week 1)
- **Risk**: Very Low
- **Action**: Already enabled by default
- **Benefit**: Discover available MCP servers

### Phase 2: Cognitive Memory (Week 2-3)
- **Risk**: Low
- **Action**: Enable memory system
- **Dependencies**: `pip install faiss-cpu numpy`
- **Benefit**: Command history search and suggestions

```bash
export AISHELL_MEMORY_ENABLED=true
```

### Phase 3: Anomaly Detection (Week 4-6)
- **Risk**: Low-Medium
- **Action**: Enable monitoring without auto-remediation
- **Dependencies**: `pip install psutil numpy`
- **Benefit**: Detect performance issues early

```bash
export AISHELL_ANOMALY_ENABLED=true
export AISHELL_AUTO_REMEDIATION=false  # Manual approval
```

### Phase 4: Auto-Remediation (Month 2-3)
- **Risk**: Medium
- **Action**: Enable auto-fix for low-risk issues
- **Benefit**: Automatic resolution of simple problems

```python
update_config('anomaly_detection', {
    'auto_remediation': True,
    'max_remediation_risk': 2  # Only low-risk fixes
})
```

### Phase 5: Autonomous DevOps Monitoring (Month 3-4)
- **Risk**: Medium
- **Action**: Enable DevOps monitoring without automation
- **Benefit**: Infrastructure insights and optimization suggestions

```bash
export AISHELL_DEVOPS_ENABLED=true
export AISHELL_AUTO_SCALING=false  # Manual approval
```

### Phase 6: Limited Automation (Month 4-6)
- **Risk**: High
- **Action**: Enable low-risk automation
- **Benefit**: Automatic optimization and scaling

```python
update_config('autonomous_devops', {
    'auto_scaling': True,
    'auto_optimization': True,
    'auto_deployment': False,  # Never enable without thorough testing
    'require_approval_above_risk': 3
})
```

## Monitoring and Metrics

### Check Feature Status

```python
from src.cognitive import is_enabled, FEATURES

for feature in FEATURES:
    status = "ENABLED" if is_enabled(feature) else "DISABLED"
    print(f"{feature}: {status}")
```

### Get Memory Statistics

```python
memory = get_cognitive_memory()
if memory:
    insights = await memory.get_insights()
    print(f"Total memories: {insights['total_memories']}")
    print(f"Success rate: {insights['overall_success_rate']:.1f}%")
    print(f"Most used commands: {insights['most_used_commands']}")
```

### Get Anomaly Status

```python
detector = get_anomaly_detector()
if detector:
    anomalies = await detector.get_active_anomalies()
    print(f"Active anomalies: {len(anomalies)}")
    for a in anomalies:
        print(f"  - {a.description} (severity: {a.severity.name})")
```

### Get DevOps Metrics

```python
devops = get_autonomous_devops()
if devops:
    metrics = await devops.get_metrics()
    print(f"Infrastructure health: {metrics['health_score']:.1f}")
    print(f"Active optimizations: {len(metrics['active_optimizations'])}")
```

## Performance Impact

| Feature | Cold Start | Steady State | Memory | Disk |
|---------|-----------|--------------|--------|------|
| MCP Discovery | <100ms | Minimal | <10MB | <1MB |
| Cognitive Memory | 1-2s | Low | 100-500MB | 1-10GB |
| Anomaly Detection | <500ms | Medium | 50-100MB | 100MB |
| Autonomous DevOps | 1-3s | Medium | 100-200MB | 500MB |

## Troubleshooting

### Feature Won't Enable

```python
# Check what happened
import logging
logging.basicConfig(level=logging.DEBUG)

from src.cognitive import enable_feature
enable_feature('cognitive_memory')
# Check logs for error message
```

Common issues:
1. Missing dependencies → Install with `pip install -r requirements-cognitive.txt`
2. Import errors → Check Python version (requires 3.8+)
3. Memory issues → Reduce `max_memories` in config

### FAISS Not Available

Cognitive memory will fall back to simple text search if FAISS is not installed:

```bash
# Install FAISS
pip install faiss-cpu

# Or use FAISS-GPU for better performance
pip install faiss-gpu
```

### High Memory Usage

```python
# Reduce memory footprint
update_config('memory', {
    'max_memories': 50000,  # Default: 100000
    'vector_dim': 256       # Default: 384
})
```

## Examples

See `src/cognitive/README.md` for detailed examples of:
- Using cognitive memory for command suggestions
- Setting up anomaly detection alerts
- Configuring autonomous DevOps policies
- Exporting and importing knowledge bases

## Security Considerations

1. **Data Privacy**: Memory system stores command history
   - Configure retention policies
   - Exclude sensitive commands
   - Encrypt memory database

2. **Auto-Remediation Risks**: Automatic fixes can cause issues
   - Start with manual approval
   - Test in staging first
   - Monitor all automated actions

3. **Autonomous Actions**: DevOps automation is powerful but risky
   - Never enable auto-deployment without thorough testing
   - Set cost limits
   - Require approval for high-risk operations

## Support

- Detailed documentation: `src/cognitive/README.md`
- Configuration reference: `src/cognitive/config.py`
- Source code: `src/cognitive/`

## Credits

Integrated from AIShell project (3.7M codebase)
- Cognitive Memory: 30,962 lines
- Anomaly Detection: 35,419 lines
- Autonomous DevOps: 39,574 lines
- Total cognitive codebase: 105,955 lines

Integration Date: 2025-10-23
