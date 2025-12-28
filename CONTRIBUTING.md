# Contributing to AIShell

Thank you for your interest in contributing to AIShell! This document provides guidelines and standards for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Testing Requirements](#testing-requirements)
5. [Code Style](#code-style)
6. [Pull Request Process](#pull-request-process)
7. [Coverage Thresholds](#coverage-thresholds)
8. [Test Organization Standards](#test-organization-standards)
9. [Documentation](#documentation)
10. [Community](#community)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a branch** for your contribution
4. **Make your changes**
5. **Test thoroughly**
6. **Submit a pull request**

## Development Setup

### Prerequisites

- Python 3.9 or higher (3.9-3.14 supported)
- Git
- pip and virtualenv

### Setup Instructions

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/AIShell.git
cd AIShell

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Verify setup
python -m pytest tests/ --collect-only
```

## Testing Requirements

### All Pull Requests Must Include Tests

Every code contribution must include appropriate tests:

- **New Features**: Add tests that cover the new functionality
- **Bug Fixes**: Add tests that demonstrate the bug and verify the fix
- **Refactoring**: Ensure existing tests pass and add new tests if behavior changes
- **Documentation**: No tests required, but examples should be tested

### Coverage Requirements

#### Minimum Coverage Thresholds

- **Overall Project**: 20% minimum (current baseline: 22.60%)
- **New Code**: 60% minimum coverage required
- **Critical Paths**: 80% minimum coverage required
  - Authentication and authorization
  - Data validation and sanitization
  - Error handling
  - Security controls

#### Coverage by Component

| Component | Current | Target | Critical Path |
|-----------|---------|--------|---------------|
| Core | 25% | 40% | Yes |
| Agents | 35% | 50% | Yes |
| Database | 24% | 40% | Yes |
| MCP Clients | 18% | 30% | No |
| Enterprise | 30% | 45% | Yes |
| Security | 35% | 80% | Yes |
| LLM | 23% | 40% | No |
| Performance | 25% | 35% | No |
| UI | 30% | 40% | No |

### Running Tests Locally

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Run specific test categories
pytest tests/ -m unit          # Unit tests only
pytest tests/ -m integration   # Integration tests only
pytest tests/ -m "not slow"    # Skip slow tests

# Run tests in parallel (faster)
pytest tests/ -n auto

# Check coverage threshold
pytest tests/ --cov=. --cov-fail-under=20
```

### Test Quality Standards

#### 1. Test Independence

Tests must be independent and not rely on execution order:

```python
# ❌ Bad - tests depend on each other
def test_create_user():
    global user_id
    user_id = create_user("test")

def test_update_user():
    update_user(user_id, "new_name")

# ✅ Good - independent tests
def test_create_user(db_session):
    user = create_user("test", session=db_session)
    assert user.name == "test"

def test_update_user(db_session):
    user = create_user("test", session=db_session)
    update_user(user.id, "new_name", session=db_session)
    assert user.name == "new_name"
```

#### 2. Clear Test Names

Use descriptive test names that explain what is being tested:

```python
# ❌ Bad - unclear test name
def test_user():
    pass

# ✅ Good - clear test name
def test_create_user_with_valid_email_succeeds():
    pass

def test_create_user_with_invalid_email_raises_validation_error():
    pass
```

#### 3. Arrange-Act-Assert Pattern

Structure tests clearly:

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

#### 4. Comprehensive Testing

Cover these cases:

- **Happy path**: Normal operation
- **Edge cases**: Boundary conditions
- **Error cases**: Invalid input, exceptions
- **Async operations**: Concurrent execution
- **Integration**: Component interaction

#### 5. Use Fixtures

Leverage pytest fixtures for reusable setup:

```python
@pytest.fixture
def database_session():
    """Provide database session for tests."""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()

def test_database_operation(database_session):
    # Use the fixture
    result = database_session.query(User).first()
    assert result is not None
```

## Test Organization Standards

### Directory Structure

```
tests/
├── conftest.py              # Shared fixtures
├── agents/
│   ├── conftest.py         # Agent-specific fixtures
│   ├── test_base.py        # Test base agent
│   └── safety/
│       └── test_controller.py
├── database/
│   ├── conftest.py         # Database fixtures
│   ├── test_backup.py
│   └── test_migration.py
└── ...
```

### File Naming

- Test files: `test_<module>.py`
- Test classes: `Test<ComponentName>`
- Test functions: `test_<operation>_<scenario>_<expected>`

### Test Markers

Use pytest markers to categorize tests:

```python
import pytest

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

Available markers:
- `unit`: Unit tests (fast, isolated)
- `integration`: Integration tests (slower, external dependencies)
- `slow`: Slow tests (> 1 second)
- `requires_db`: Requires database connection
- `requires_llm`: Requires LLM provider

### Mock External Dependencies

Always mock external services:

```python
@patch('src.llm.manager.LLMManager')
def test_ai_query(mock_llm):
    """Test AI query with mocked LLM."""
    mock_llm.return_value.query.return_value = "test response"

    result = process_query("test question")

    assert result == "test response"
    mock_llm.return_value.query.assert_called_once()
```

## Code Style

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with these specifics:

- **Line length**: 100 characters maximum
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Imports**: Organized (standard library, third-party, local)

### Code Quality Tools

```bash
# Format code
black src/ tests/

# Check formatting
black src/ tests/ --check

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Security scan
bandit -r src/
```

### Pre-commit Hooks

Pre-commit hooks automatically run before commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
```

## Pull Request Process

### Before Submitting

1. **Run all tests**: `pytest tests/ -v`
2. **Check coverage**: `pytest tests/ --cov=. --cov-report=term`
3. **Format code**: `black src/ tests/`
4. **Lint code**: `flake8 src/ tests/`
5. **Type check**: `mypy src/`
6. **Update documentation**: If adding features
7. **Update changelog**: Add entry to CHANGELOG.md

### PR Checklist

- [ ] Tests added for new functionality
- [ ] All tests pass locally
- [ ] Coverage meets minimum threshold (20% overall, 60% for new code)
- [ ] Code formatted with black
- [ ] No linting errors
- [ ] Type hints added
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] PR description explains changes

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing performed

## Coverage
- Overall coverage: X%
- New code coverage: X%
- Critical path coverage: X%

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### Review Process

1. **Automated checks**: CI runs tests and coverage
2. **Code review**: Maintainers review code
3. **Feedback**: Address comments and make changes
4. **Approval**: Two approvals required
5. **Merge**: Squash and merge to main

## Coverage Thresholds

### Overall Project

- **Minimum**: 20% (enforced by CI)
- **Target**: 40% (short-term goal)
- **Goal**: 60% (long-term goal)

### New Code

- **Minimum**: 60% (enforced by CI)
- **Target**: 80%
- **Critical Paths**: 80% minimum

### How Coverage is Checked

```yaml
# GitHub Actions (automatic)
- name: Check coverage
  run: |
    pytest tests/ --cov=. --cov-report=json
    python scripts/check_coverage_delta.py \
      --current coverage.json \
      --base main \
      --threshold 60
```

### Coverage Reports

- **HTML**: `htmlcov/index.html` (local development)
- **Terminal**: Shows missing lines
- **JSON**: Used by CI/CD
- **Codecov**: Automatic PR comments

## Documentation

### Required Documentation

- **Docstrings**: All public functions, classes, and modules
- **Type hints**: All function signatures
- **README updates**: For new features
- **Tutorial updates**: For user-facing features
- **API documentation**: For public APIs

### Docstring Format

Use Google-style docstrings:

```python
def backup_database(
    database_url: str,
    backup_path: str,
    compress: bool = True
) -> BackupResult:
    """
    Create a backup of the specified database.

    Args:
        database_url: Connection URL for the database
        backup_path: Path where backup will be saved
        compress: Whether to compress the backup (default: True)

    Returns:
        BackupResult containing status and metadata

    Raises:
        BackupError: If backup operation fails
        ConnectionError: If cannot connect to database

    Example:
        >>> result = backup_database(
        ...     "postgresql://localhost/mydb",
        ...     "/backups/mydb.sql",
        ...     compress=True
        ... )
        >>> print(result.success)
        True
    """
    pass
```

## Community

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **Documentation**: Read the comprehensive guides

### Communication

- Be respectful and inclusive
- Provide constructive feedback
- Help other contributors
- Share knowledge and experiences

## Additional Resources

- [Testing Guide](docs/TESTING_GUIDE.md)
- [CI/CD Integration](docs/CI_CD_INTEGRATION.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [API Reference](docs/api/)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to AIShell!**

**Questions?** Open an issue or start a discussion on GitHub.

**Last Updated**: 2025-10-12
**Version**: 2.0.0
