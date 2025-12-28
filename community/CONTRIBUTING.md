# Contributing to AI-Shell

Thank you for your interest in contributing to AI-Shell! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:
- Check the [existing issues](https://github.com/ruvnet/AIShell/issues) to avoid duplicates
- Collect relevant information (version, OS, error messages, steps to reproduce)

When submitting a bug report, include:
- Clear, descriptive title
- Detailed steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Environment details

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:
- Check existing feature requests first
- Provide clear use cases
- Explain why this would be valuable
- Consider implementation complexity

### Contributing Code

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Add tests for your changes**
5. **Ensure all tests pass**
6. **Commit with clear messages**
7. **Push to your fork**
8. **Open a Pull Request**

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip or pipx
- Git
- (Optional) Docker for integration tests

### Setup Instructions

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/AIShell.git
cd AIShell

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest tests/
```

### Project Structure

```
AIShell/
├── src/aishell/          # Main package
│   ├── core/            # Core functionality
│   ├── agents/          # AI agents
│   ├── mcp_clients/     # MCP client implementations
│   ├── database/        # Database connectors
│   └── enterprise/      # Enterprise features
├── tests/               # Test suite
├── docs/                # Documentation
├── examples/            # Example code
└── scripts/             # Utility scripts
```

## Pull Request Process

1. **Update Documentation**
   - Add docstrings to new functions/classes
   - Update README.md if needed
   - Add example usage if applicable

2. **Add Tests**
   - Aim for 95%+ code coverage
   - Include unit and integration tests
   - Test edge cases and error handling

3. **Follow Code Style**
   - Run `black` for formatting
   - Run `flake8` for linting
   - Run `mypy` for type checking

4. **Update CHANGELOG.md**
   - Add entry under "Unreleased" section
   - Follow Keep a Changelog format

5. **Get Reviews**
   - At least one approval from maintainers
   - Address all review comments
   - Keep PR focused and reasonably sized

6. **Squash Commits**
   - Before merging, squash related commits
   - Write clear commit message

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting (line length: 100)
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Type hints required for all functions

### Code Quality

```python
# Good Example
async def execute_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> QueryResult:
    """
    Execute a database query with parameters.

    Args:
        query: SQL query to execute
        params: Query parameters (optional)
        timeout: Query timeout in seconds

    Returns:
        QueryResult object containing rows and metadata

    Raises:
        QueryTimeoutError: If query exceeds timeout
        DatabaseError: If query execution fails
    """
    if params is None:
        params = {}

    try:
        result = await self.db.execute(query, params, timeout=timeout)
        return QueryResult(rows=result.rows, metadata=result.metadata)
    except TimeoutError as e:
        raise QueryTimeoutError(f"Query exceeded {timeout}s timeout") from e
    except Exception as e:
        raise DatabaseError(f"Query failed: {e}") from e
```

### Documentation Style

- Use Google-style docstrings
- Include type hints
- Provide examples for complex functions
- Document exceptions

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/aishell --cov-report=html

# Run specific test file
pytest tests/test_core.py -v

# Run tests matching pattern
pytest tests/ -k "test_query" -v

# Run tests in parallel
pytest tests/ -n auto
```

### Writing Tests

```python
# tests/test_feature.py
import pytest
from aishell import AIShell

class TestFeature:
    """Test suite for new feature"""

    @pytest.fixture
    async def shell(self):
        """Fixture for AI-Shell instance"""
        shell = AIShell()
        await shell.initialize()
        yield shell
        await shell.cleanup()

    @pytest.mark.asyncio
    async def test_basic_functionality(self, shell):
        """Test basic feature functionality"""
        result = await shell.some_feature()
        assert result.success is True
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_error_handling(self, shell):
        """Test error handling"""
        with pytest.raises(ExpectedError):
            await shell.some_feature(invalid_input=True)
```

### Test Coverage

- Aim for 95%+ coverage
- Test happy paths and error cases
- Include integration tests for database operations
- Mock external services

## Documentation

### Types of Documentation

1. **Code Documentation**
   - Docstrings for all public APIs
   - Inline comments for complex logic
   - Type hints

2. **User Documentation**
   - Usage examples
   - Tutorials
   - API reference

3. **Developer Documentation**
   - Architecture decisions
   - Development guides
   - Contributing guidelines

### Building Documentation

```bash
# Build Sphinx documentation
cd docs/api
make html

# View documentation
python -m http.server 8000 --directory _build/html
# Open http://localhost:8000
```

## Release Process

1. Update version in `setup.py` and `__init__.py`
2. Update CHANGELOG.md
3. Create git tag
4. Build and publish to PyPI
5. Create GitHub release

## Getting Help

- **Documentation**: https://docs.aishell.dev
- **Discord**: https://discord.gg/aishell
- **GitHub Discussions**: https://github.com/ruvnet/AIShell/discussions
- **Email**: dev@aishell.dev

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

Thank you for contributing to AI-Shell!
