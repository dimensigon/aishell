# Comprehensive Testing Guide for AIShell

## Overview

This guide provides complete information about testing in the AIShell project, including how to run tests, interpret coverage reports, write new tests, and follow best practices.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Architecture](#test-architecture)
3. [Running Tests](#running-tests)
4. [Coverage Analysis](#coverage-analysis)
5. [Writing Tests](#writing-tests)
6. [Test Categories](#test-categories)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [CI/CD Integration](#cicd-integration)

## Quick Start

### Prerequisites

```bash
# Python 3.9-3.14 supported
python --version

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run complete test suite
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run specific test file
python -m pytest tests/agents/test_base.py -v

# Run tests by marker
python -m pytest tests/ -m "not slow" -v
```

## Test Architecture

### Project Statistics

- **Total Files**: 286 source files
- **Test Files**: 134 test modules
- **Test Functions**: 3,396 test cases
- **Overall Coverage**: 22.60%
- **Lines Tested**: 9,496 out of 42,025

### Directory Structure

```
tests/
├── agents/                    # Agent framework tests (45 files)
│   ├── test_base.py          # Base agent functionality
│   ├── test_agent_chain.py   # Agent chaining
│   ├── test_parallel_executor.py
│   ├── safety/               # Safety controller tests
│   ├── state/                # State management tests
│   └── tools/                # Tool registry tests
│
├── api/                       # API tests (8 files)
│   └── graphql/              # GraphQL API tests
│
├── coordination/              # Coordination tests (3 files)
│   ├── test_distributed_lock.py
│   ├── test_state_sync.py
│   └── test_task_queue.py
│
├── core/                      # Core system tests (6 files)
│   ├── test_config.py
│   ├── test_event_bus.py
│   ├── test_health_checks.py
│   └── test_ai_shell.py
│
├── database/                  # Database tests (17 files)
│   ├── test_backup.py
│   ├── test_migration.py
│   ├── test_query_optimizer.py
│   ├── test_risk_analyzer.py
│   └── test_restore.py
│
├── enterprise/                # Enterprise feature tests (15 files)
│   ├── audit/
│   ├── cloud/
│   ├── rbac/
│   └── tenancy/
│
├── llm/                       # LLM integration tests (3 files)
│   ├── test_embeddings.py
│   ├── test_manager.py
│   └── test_providers.py
│
├── mcp_clients/              # MCP client tests (14 files)
│   ├── test_base.py
│   ├── test_oracle_client.py
│   ├── test_postgresql_client.py
│   ├── test_mongodb_client.py
│   └── test_retry.py
│
├── performance/              # Performance tests (4 files)
│   ├── test_cache.py
│   ├── test_monitor.py
│   └── test_optimizer.py
│
├── security/                 # Security tests (9 files)
│   ├── test_auth.py
│   ├── test_encryption.py
│   └── advanced/
│
└── ui/                       # UI component tests (10 files)
    ├── test_dynamic_panels.py
    ├── containers/
    └── screens/
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with extra verbosity (show individual test names)
pytest tests/ -vv

# Run specific test
pytest tests/agents/test_base.py::TestBaseAgent::test_initialization

# Run tests matching pattern
pytest tests/ -k "test_backup"

# Run tests with markers
pytest tests/ -m "unit"
pytest tests/ -m "integration"
pytest tests/ -m "slow"
```

### Coverage Commands

```bash
# Generate HTML report
pytest tests/ --cov=. --cov-report=html
# View: htmlcov/index.html

# Generate terminal report
pytest tests/ --cov=. --cov-report=term-missing

# Generate JSON report (for CI/CD)
pytest tests/ --cov=. --cov-report=json

# Generate XML report (for code quality tools)
pytest tests/ --cov=. --cov-report=xml

# Multiple formats
pytest tests/ --cov=. --cov-report=html --cov-report=json --cov-report=xml
```

### Parallel Execution

```bash
# Run tests in parallel (requires pytest-xdist)
pytest tests/ -n auto

# Run with specific number of workers
pytest tests/ -n 4

# Parallel with coverage
pytest tests/ -n auto --cov=. --cov-report=html
```

### Test Selection

```bash
# Run only failed tests from last run
pytest tests/ --lf

# Run failed tests first, then others
pytest tests/ --ff

# Stop after first failure
pytest tests/ -x

# Stop after N failures
pytest tests/ --maxfail=3

# Run tests by directory
pytest tests/agents/
pytest tests/database/

# Run specific test classes
pytest tests/agents/test_base.py::TestBaseAgent
```

## Coverage Analysis

### Current Coverage by Module

| Module | Coverage | Lines | Missing | Status |
|--------|----------|-------|---------|--------|
| **Core** | 25% | 500 | 375 | 🟡 In Progress |
| **Agents** | 35% | 2,500 | 1,625 | 🟡 In Progress |
| **Database** | 24% | 3,000 | 2,280 | 🟡 In Progress |
| **MCP Clients** | 18% | 1,800 | 1,476 | 🔴 Needs Work |
| **Enterprise** | 30% | 1,500 | 1,050 | 🟡 In Progress |
| **Security** | 35% | 800 | 520 | 🟡 In Progress |
| **LLM** | 23% | 400 | 308 | 🟡 In Progress |
| **Performance** | 25% | 600 | 450 | 🟡 In Progress |
| **UI** | 30% | 500 | 350 | 🟡 In Progress |

### Interpreting Coverage Reports

#### HTML Report (htmlcov/index.html)

The HTML report provides:
- **File-level coverage**: Click files to see line-by-line coverage
- **Green lines**: Covered by tests
- **Red lines**: Not covered by tests
- **Yellow lines**: Partially covered (branches)
- **Gray lines**: Excluded from coverage

#### Terminal Report

```bash
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
src/agents/base.py                  113     47    58%   220-254, 297
src/database/backup.py              254    193    24%   78-81, 112-123
src/llm/manager.py                  160    118    26%   53-62, 75-100
---------------------------------------------------------------
TOTAL                             42025  32529    23%
```

- **Stmts**: Total executable statements
- **Miss**: Statements not covered
- **Cover**: Percentage covered
- **Missing**: Line numbers not covered

#### JSON Report (coverage.json)

Used for programmatic access and CI/CD integration:

```json
{
  "totals": {
    "covered_lines": 9496,
    "num_statements": 42025,
    "percent_covered": 22.60,
    "missing_lines": 32529
  },
  "files": {
    "src/agents/base.py": {
      "summary": {
        "covered_lines": 66,
        "num_statements": 113,
        "percent_covered": 58.41
      }
    }
  }
}
```

### Coverage Goals

- **Critical Paths**: 80%+ coverage required
  - Authentication and authorization
  - Data validation and sanitization
  - Error handling
  - Security controls

- **Standard Code**: 60%+ coverage target
  - Business logic
  - API endpoints
  - Database operations

- **UI and Utilities**: 40%+ coverage acceptable
  - Display logic
  - Formatting utilities
  - Helper functions

## Writing Tests

### Test Structure

```python
"""
Test module for <component>.

This module tests the <component> functionality including:
- Feature 1
- Feature 2
- Edge cases and error handling
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.component import ComponentClass


class TestComponentClass:
    """Test suite for ComponentClass."""

    @pytest.fixture
    def mock_dependency(self):
        """Create mock dependency."""
        return Mock()

    @pytest.fixture
    def component(self, mock_dependency):
        """Create component instance."""
        return ComponentClass(dependency=mock_dependency)

    def test_basic_functionality(self, component):
        """Test basic component functionality."""
        # Arrange
        input_data = "test"

        # Act
        result = component.process(input_data)

        # Assert
        assert result == expected_output

    @pytest.mark.asyncio
    async def test_async_operation(self, component):
        """Test async component operation."""
        result = await component.async_process()
        assert result is not None

    def test_error_handling(self, component):
        """Test component error handling."""
        with pytest.raises(ValueError):
            component.process(invalid_input)

    @pytest.mark.parametrize("input,expected", [
        ("a", "A"),
        ("b", "B"),
        ("c", "C"),
    ])
    def test_multiple_cases(self, component, input, expected):
        """Test multiple input cases."""
        assert component.transform(input) == expected
```

### Fixtures

```python
# conftest.py - shared fixtures

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def database_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(database_engine):
    """Create database session."""
    Session = sessionmaker(bind=database_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def mock_llm():
    """Create mock LLM provider."""
    with patch('src.llm.manager.LLMManager') as mock:
        mock.return_value.query.return_value = "test response"
        yield mock
```

### Mocking Strategies

#### Mock External Services

```python
@patch('src.mcp_clients.oracle_client.oracledb')
def test_database_connection(mock_oracledb):
    """Test database connection with mock."""
    mock_conn = Mock()
    mock_oracledb.connect.return_value = mock_conn

    client = OracleClient(config)
    client.connect()

    mock_oracledb.connect.assert_called_once()
```

#### Mock Async Operations

```python
@pytest.mark.asyncio
async def test_async_query():
    """Test async database query."""
    mock_pool = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = Mock()

    result = await execute_query(mock_pool, "SELECT 1")
    assert result is not None
```

#### Mock File Operations

```python
def test_file_backup(fs):  # fs from pyfakefs
    """Test file backup with fake filesystem."""
    fs.create_file('/tmp/test.txt', contents='data')

    backup_manager.backup('/tmp/test.txt')

    assert fs.exists('/backup/test.txt')
```

### Parameterized Tests

```python
@pytest.mark.parametrize("risk_level,expected", [
    (RiskLevel.LOW, True),
    (RiskLevel.MEDIUM, True),
    (RiskLevel.HIGH, False),
    (RiskLevel.CRITICAL, False),
])
def test_risk_approval(risk_level, expected):
    """Test risk approval logic."""
    result = safety_controller.auto_approve(risk_level)
    assert result == expected
```

### Testing Exceptions

```python
def test_invalid_config():
    """Test configuration validation."""
    with pytest.raises(ConfigError) as exc_info:
        Config.load(invalid_data)

    assert "missing required field" in str(exc_info.value)
```

### Async Testing

```python
import pytest
import asyncio


@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent async operations."""
    tasks = [
        agent.execute(f"task_{i}")
        for i in range(10)
    ]

    results = await asyncio.gather(*tasks)

    assert len(results) == 10
    assert all(r.success for r in results)
```

## Test Categories

### Markers

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow running tests",
    "requires_db: Tests requiring database",
    "requires_llm: Tests requiring LLM",
]
```

### Usage

```python
@pytest.mark.unit
def test_validation():
    """Unit test for validation logic."""
    pass


@pytest.mark.integration
@pytest.mark.requires_db
def test_database_workflow():
    """Integration test with database."""
    pass


@pytest.mark.slow
def test_performance_benchmark():
    """Slow performance test."""
    pass
```

## Best Practices

### 1. Test Organization

- **One test class per component**
- **Clear test names** (test_method_scenario_expected)
- **Group related tests** in classes
- **Use fixtures** for setup/teardown

### 2. Test Independence

```python
# ❌ Bad - tests depend on each other
def test_create_user():
    global user_id
    user_id = create_user("test")

def test_update_user():
    update_user(user_id, "new_name")  # Depends on previous test

# ✅ Good - independent tests
def test_create_user(db_session):
    user = create_user("test", session=db_session)
    assert user.name == "test"

def test_update_user(db_session):
    user = create_user("test", session=db_session)
    update_user(user.id, "new_name", session=db_session)
    assert user.name == "new_name"
```

### 3. Arrange-Act-Assert Pattern

```python
def test_calculation():
    # Arrange - setup test data
    calculator = Calculator()
    a, b = 5, 3

    # Act - perform operation
    result = calculator.add(a, b)

    # Assert - verify result
    assert result == 8
```

### 4. Meaningful Assertions

```python
# ❌ Bad - unclear what's being tested
assert result

# ✅ Good - clear expectations
assert result.status == "success"
assert len(result.items) == 5
assert result.timestamp > start_time
```

### 5. Test Documentation

```python
def test_backup_with_compression():
    """
    Test database backup with compression enabled.

    Verifies that:
    1. Backup creates compressed file
    2. Compressed file is smaller than uncompressed
    3. Backup can be restored successfully
    4. Data integrity is maintained
    """
    pass
```

### 6. Mock External Dependencies

```python
# ❌ Bad - makes actual API call
def test_api_integration():
    response = requests.get("https://api.example.com/data")
    assert response.status_code == 200

# ✅ Good - mocks API call
@patch('requests.get')
def test_api_integration(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"data": "test"}

    response = fetch_data()
    assert response["data"] == "test"
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Error: ModuleNotFoundError
# Solution: Ensure PYTHONPATH is set
export PYTHONPATH=/home/claude/AIShell:$PYTHONPATH
pytest tests/
```

#### 2. Fixture Not Found

```bash
# Error: fixture 'db_session' not found
# Solution: Check conftest.py location
# Fixtures should be in conftest.py in test directory or parent
```

#### 3. Async Tests Failing

```bash
# Error: RuntimeError: Event loop is closed
# Solution: Use pytest-asyncio
pip install pytest-asyncio

# In test file
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result
```

#### 4. Coverage Not Including Files

```bash
# Solution: Add to .coveragerc or pyproject.toml
[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/venv/*",
    "*/__pycache__/*"
]
```

#### 5. Slow Test Suite

```bash
# Solution: Run only specific tests during development
pytest tests/agents/ -v

# Use markers to skip slow tests
pytest tests/ -m "not slow"

# Run in parallel
pytest tests/ -n auto
```

### Debug Tests

```python
# Add breakpoint
def test_complex_logic():
    result = complex_function()
    breakpoint()  # Debugger stops here
    assert result.is_valid()
```

```bash
# Run with pdb
pytest tests/test_file.py --pdb

# Show print statements
pytest tests/ -s

# Show more details on failure
pytest tests/ -vv --tb=long
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests with coverage
      run: |
        pytest tests/ --cov=. --cov-report=xml --cov-report=html

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

    - name: Archive coverage report
      uses: actions/upload-artifact@v3
      with:
        name: coverage-report
        path: htmlcov/
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/ --cov=. --cov-fail-under=20
```

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Mock Objects](https://docs.python.org/3/library/unittest.mock.html)

## Support

For testing questions or issues:
- Create an issue on GitHub
- Check existing test files for examples
- Review this guide and inline test documentation

---

**Last Updated**: 2025-10-12
**Version**: 2.0.0
**Maintainers**: AIShell Testing Team
