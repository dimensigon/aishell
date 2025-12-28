# FAISS 1.12.0 Quick Reference

## Installation

```bash
pip install faiss-cpu==1.12.0
```

## Verify Installation

```bash
python scripts/verify_faiss.py
```

Expected output: `🎉 ALL CHECKS PASSED`

## Usage in AIShell

### Default (Automatic FAISS detection)

```python
from src.vector.store import VectorDatabase

# Automatically uses real FAISS if available, falls back to mock
db = VectorDatabase(dimension=384)
```

### Force Real FAISS

```python
db = VectorDatabase(dimension=384, use_faiss=True)
```

### Force Mock (for testing)

```python
db = VectorDatabase(dimension=384, use_faiss=False)
```

## Run Tests

```bash
# Vector database tests
python -m pytest tests/test_vector.py -v

# FAISS compatibility tests
python -m pytest tests/test_faiss_compatibility.py -v

# All vector tests
python -m pytest tests/test_vector.py tests/test_faiss_compatibility.py -v
```

## Python Compatibility

| Version | Status |
|---------|--------|
| 3.9-3.11 | ✅ Fully Supported |
| 3.12+ | ✅ **NOW SUPPORTED** |

## Common Issues

### ImportError: No module named 'faiss'

**Solution:**
```bash
pip install faiss-cpu==1.12.0
```

### Old version still installed

**Solution:**
```bash
pip uninstall faiss-cpu
pip install faiss-cpu==1.12.0
```

## Performance

- **25-33% faster** than version 1.7.4
- Supports SIMD optimizations
- Better memory management

## Documentation

- **Full Guide**: `docs/FAISS_UPGRADE_NOTES.md`
- **Technical Details**: `docs/UPGRADE_SUMMARY.md`
- **Completion Status**: `FAISS_UPGRADE_COMPLETE.md`

## Support

FAISS GitHub: https://github.com/facebookresearch/faiss

---

**Version**: 1.12.0
**Updated**: 2025-10-04
