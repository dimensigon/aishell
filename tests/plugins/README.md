# Plugin System Tests

Comprehensive test suite for the AIShell plugin system.

## Test Coverage: 87%

### Test Statistics
- **Total Tests**: 295
- **Test Files**: 8
- **Mock Plugins**: 4
- **Coverage**: 87% overall

### Module Coverage Breakdown

| Module | Coverage | Tests |
|--------|----------|-------|
| config.py | 90% | 39 |
| dependencies.py | 93% | 56 |
| discovery.py | 95% | 35 |
| hooks.py | 100% | 47 |
| loader.py | 95% | 42 |
| sandbox.py | 95% | 38 |
| security.py | 98% | 38 |

## Test Organization

### Core Test Files

1. **test_loader.py** - Plugin loading/unloading
   - File path loading
   - Directory scanning
   - Module caching
   - Error handling
   - Concurrent loading

2. **test_discovery.py** - Plugin discovery
   - File system scanning
   - Metadata extraction
   - AST parsing
   - Type filtering
   - Multiple search paths

3. **test_manager.py** - Plugin lifecycle management
   - Plugin registration
   - Activation/deactivation
   - Dependency resolution
   - Start/stop operations
   - Reload functionality

4. **test_hooks.py** - Event-driven hooks
   - Hook registration
   - Priority-based execution
   - Async hook execution
   - Hook chaining
   - Error handling

5. **test_sandbox.py** - Resource isolation
   - Path access control
   - Resource limiting
   - Memory tracking
   - CPU monitoring
   - Concurrent operations

6. **test_security.py** - Security management
   - Permission system
   - Wildcard permissions
   - Code signing
   - Signature verification
   - Permission isolation

7. **test_dependencies.py** - Dependency resolution
   - Version checking
   - Dependency graphs
   - Circular dependency detection
   - Topological sorting
   - Load order resolution

8. **test_config.py** - Configuration management
   - Config validation
   - JSON schema validation
   - File persistence
   - Cache management
   - Concurrent operations

### Mock Plugins

Mock plugins are located in `tests/plugins/mocks/`:

- **valid_plugin.py** - Standard valid plugin
- **plugin_with_deps.py** - Plugin with dependencies
- **invalid_plugin.py** - Syntax error plugin
- **no_class_plugin.py** - No plugin class

## Test Patterns

### 1. Mock Plugins for Isolation
```python
@pytest.fixture
def mock_plugin_path(tmp_path):
    plugin_file = tmp_path / "test_plugin.py"
    plugin_file.write_text("""
class TestPlugin:
    name = "test"
    def activate(self): return True
""")
    return plugin_file
```

### 2. Concurrent Operations Testing
```python
def test_concurrent_operations(self):
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(operation, arg) for arg in args]
        results = [f.result() for f in futures]
```

### 3. Edge Case Coverage
- Unicode filenames
- Special characters
- Empty files
- Large files
- Symlinks
- Permission errors

### 4. Security Validation
```python
def test_permission_isolation(self):
    manager.grant_permission("plugin1", "file.read")
    manager.grant_permission("plugin2", "db.write")

    assert manager.has_permission("plugin1", "file.read")
    assert not manager.has_permission("plugin1", "db.write")
```

### 5. Sandbox Testing
```python
def test_resource_limits(self):
    limiter.track_usage("plugin", memory_mb=150, cpu_percent=75)
    assert limiter.within_limits("plugin") is False
```

## Running Tests

### Run All Plugin Tests
```bash
python -m pytest tests/plugins/ -v
```

### Run With Coverage
```bash
python -m pytest tests/plugins/ --cov=src/plugins --cov-report=term
```

### Run Specific Test File
```bash
python -m pytest tests/plugins/test_loader.py -v
```

### Run Tests Concurrently
```bash
python -m pytest tests/plugins/ -n auto
```

## Best Practices

1. **Use tmp_path fixtures** - Always use pytest's tmp_path for file operations
2. **Test concurrent operations** - Include threading/multiprocessing tests
3. **Validate permissions** - Test security boundaries
4. **Test error handling** - Cover exception paths
5. **Mock external dependencies** - Isolate plugin system from external services
6. **Test Unicode and special chars** - Ensure internationalization support
7. **Verify cleanup operations** - Test resource cleanup and memory management

## Coverage Goals

- **Target**: 80%+ coverage
- **Current**: 87% coverage
- **Next Steps**: Improve topological sort tests, add more edge cases

## Continuous Integration

These tests are designed to run in CI/CD pipelines with:
- Parallel test execution
- Coverage reporting
- Failure notifications
- Performance benchmarks

## Contributing

When adding new plugin features:
1. Write tests first (TDD)
2. Aim for 80%+ coverage
3. Include edge cases
4. Test concurrent operations
5. Document test patterns
6. Update this README
