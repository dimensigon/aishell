# GitHub Actions CI/CD Pipeline

Comprehensive continuous integration and deployment pipeline for AIShell.

## Quick Links

- [CI/CD Guide](/docs/CI_CD_GUIDE.md) - Complete documentation
- [Workflows](.github/workflows/) - All workflow files
- [Actions](../../actions) - Workflow runs

## Workflows Overview

### 1. Test Suite (`test.yml`)
[![Test Suite](../../actions/workflows/test.yml/badge.svg)](../../actions/workflows/test.yml)

**Multi-platform, multi-version testing**
- Python: 3.9, 3.10, 3.11, 3.12, 3.13
- OS: Ubuntu, macOS, Windows
- Parallel execution across 15 jobs

### 2. Coverage (`coverage.yml`)
[![Coverage](../../actions/workflows/coverage.yml/badge.svg)](../../actions/workflows/coverage.yml)

**Comprehensive coverage reporting**
- Codecov integration
- PR comments with coverage diff
- 70% minimum threshold
- HTML and XML reports

### 3. Code Quality (`lint.yml`)
[![Code Quality](../../actions/workflows/lint.yml/badge.svg)](../../actions/workflows/lint.yml)

**Automated code quality checks**
- Black (formatting)
- isort (import sorting)
- Ruff (linting)
- Flake8 (style guide)
- Pylint (code analysis)
- mypy (type checking)
- Auto-formatting on PRs

### 4. Security (`security.yml`)
[![Security](../../actions/workflows/security.yml/badge.svg)](../../actions/workflows/security.yml)

**Security vulnerability scanning**
- Bandit (security issues)
- Safety (known vulnerabilities)
- pip-audit (dependency scanning)
- CodeQL (semantic analysis)
- Weekly scheduled scans

### 5. Release (`release.yml`)
[![Release](../../actions/workflows/release.yml/badge.svg)](../../actions/workflows/release.yml)

**Automated release pipeline**
- PyPI publishing
- GitHub releases
- Docker images
- Multi-platform testing

## Quick Start

### Running Tests Locally

```bash
# Install dependencies
pip install -e ".[dev,test]"

# Run tests
pytest -v

# Check coverage
pytest --cov=. --cov-report=term-missing

# Run linting
black --check .
isort --check .
ruff check .

# Security checks
bandit -r .
safety check
```

### Testing Workflows Locally

Install [act](https://github.com/nektos/act):

```bash
# macOS
brew install act

# Run workflows
act push -W .github/workflows/test.yml
act push -j lint
```

## Required Secrets

Configure in Settings → Secrets and variables → Actions:

| Secret | Purpose |
|--------|---------|
| `CODECOV_TOKEN` | Coverage reporting |
| `PYPI_API_TOKEN` | PyPI publishing |
| `TEST_PYPI_API_TOKEN` | Test PyPI |
| `DOCKER_USERNAME` | Docker Hub |
| `DOCKER_PASSWORD` | Docker Hub token |

## Status Badges

Add to README.md:

```markdown
[![Test Suite](https://github.com/yourusername/AIShell/actions/workflows/test.yml/badge.svg)](https://github.com/yourusername/AIShell/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/yourusername/AIShell/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/AIShell)
[![Code Quality](https://github.com/yourusername/AIShell/actions/workflows/lint.yml/badge.svg)](https://github.com/yourusername/AIShell/actions/workflows/lint.yml)
[![Security](https://github.com/yourusername/AIShell/actions/workflows/security.yml/badge.svg)](https://github.com/yourusername/AIShell/actions/workflows/security.yml)
```

## Automated Features

### Dependabot
- Weekly dependency updates
- Grouped PRs (production vs dev)
- Auto-review assignment

### Auto-formatting
- Automatic code formatting on PRs
- Black + isort integration
- Auto-commit changes

### PR Comments
- Coverage diff on every PR
- Test result summaries
- Security scan results

## Branch Protection

Recommended settings for `main` branch:

- [x] Require pull request reviews (1 reviewer)
- [x] Require status checks to pass
  - Test Suite / test
  - Coverage / coverage
  - Code Quality / lint
  - Security Scanning / security
- [x] Require conversation resolution
- [x] Require signed commits
- [x] Include administrators

## Performance

| Workflow | Duration | Jobs |
|----------|----------|------|
| Test Suite | 8-12 min | 15 parallel |
| Coverage | 3-5 min | 1 |
| Code Quality | 2-4 min | 2 |
| Security | 5-8 min | 3 |
| Release | 15-20 min | 4 |

**Total pipeline time**: ~10 minutes (parallel execution)

## Caching Strategy

All workflows use aggressive caching:
- pip dependencies
- pytest cache
- Docker layers (release)

## Maintenance

- **Weekly**: Review Dependabot PRs
- **Monthly**: Update GitHub Actions versions
- **Quarterly**: Review security policies
- **Per Release**: Verify all workflows pass

## Troubleshooting

### Common Issues

**Tests failing on specific Python version?**
```bash
pyenv install 3.12.0
pyenv local 3.12.0
pytest
```

**Coverage below threshold?**
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

**Linting failures?**
```bash
black .
isort .
ruff check . --fix
```

### Debug Mode

Enable debug logging:
1. Settings → Secrets → Actions
2. Add `ACTIONS_STEP_DEBUG` = `true`
3. Add `ACTIONS_RUNNER_DEBUG` = `true`

## Documentation

- [Complete CI/CD Guide](/docs/CI_CD_GUIDE.md)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Python Testing](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)

## Support

- Open an [issue](../../issues) for problems
- Check [workflow runs](../../actions) for details
- Review [CI/CD Guide](/docs/CI_CD_GUIDE.md) for help

---

**Maintained By**: @ruvnet
**Last Updated**: 2025-10-12
