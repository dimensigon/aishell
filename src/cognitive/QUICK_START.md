# Cognitive Features Quick Start

## 1. Check What's Available

```python
from src.cognitive import FEATURES

for feature, enabled in FEATURES.items():
    print(f"{feature}: {'ENABLED' if enabled else 'DISABLED'}")
```

## 2. Install Dependencies

```bash
# Full installation
pip install -r requirements-cognitive.txt

# Or selective
pip install faiss-cpu numpy psutil
```

## 3. Enable Features

```python
from src.cognitive import enable_feature, get_cognitive_memory

# Enable cognitive memory
enable_feature('cognitive_memory')
memory = get_cognitive_memory()

if memory:
    print("Cognitive memory ready!")
```

## 4. Use Features

### Cognitive Memory
```python
# Remember a command
await memory.remember(
    command="npm install express",
    output="added 50 packages",
    context={'cwd': '/project'},
    duration=2.5
)

# Recall similar commands
results = await memory.recall("install packages", k=5)
for result in results:
    print(result.command)
```

### Anomaly Detection
```python
from src.cognitive import enable_feature, get_anomaly_detector

enable_feature('anomaly_detection')
detector = get_anomaly_detector()

await detector.start_monitoring()
anomalies = await detector.get_active_anomalies()
```

## 5. Environment Variables (Alternative)

```bash
export AISHELL_MEMORY_ENABLED=true
export AISHELL_ANOMALY_ENABLED=true
```

## Documentation

- Complete Guide: `docs/COGNITIVE_FEATURES.md`
- Configuration: `src/cognitive/config.py`
- Full README: `src/cognitive/README.md`
