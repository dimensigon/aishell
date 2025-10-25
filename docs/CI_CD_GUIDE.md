# CI/CD Pipeline Documentation

Complete guide for the AIShell GitHub Actions CI/CD pipeline.

## Table of Contents

1. [Overview](#overview)
2. [Workflows](#workflows)
3. [Setup Instructions](#setup-instructions)
4. [Badges](#badges)
5. [Secrets Configuration](#secrets-configuration)
6. [Testing Locally](#testing-locally)
7. [Troubleshooting](#troubleshooting)

## Overview

The AIShell project uses GitHub Actions for continuous integration and continuous deployment. Our CI/CD pipeline includes:

- **Automated Testing**: Multi-platform, multi-version Python testing
- **Code Coverage**: Comprehensive coverage reporting with Codecov integration
- **Code Quality**: Linting, formatting, and type checking
- **Security Scanning**: Vulnerability detection and dependency auditing
- **Automated Releases**: PyPI publishing and GitHub releases

## Workflows

### 1. Test Suite (`test.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual dispatch

**Features:**
- Matrix testing across Python 3.9-3.13
- Multi-OS support (Ubuntu, macOS, Windows)
- Parallel test execution
- Test result artifacts
- Test summary reports

**Configuration:**
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ['3.9', '3.10', '3.11', '3.12', '3.13']
```

**Caching:**
- pip dependencies
- pytest cache

### 2. Coverage (`coverage.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main`
- Manual dispatch

**Features:**
- Coverage report generation (XML, HTML, terminal)
- Codecov integration
- PR comments with coverage diff
- 70% minimum coverage threshold
- Coverage badge generation

**Usage:**
```bash
# View coverage locally
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### 3. Code Quality (`lint.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Manual dispatch

**Tools:**
- **Black**: Code formatting
- **isort**: Import sorting
- **Ruff**: Fast Python linter
- **Flake8**: Style guide enforcement
- **Pylint**: Code analysis
- **mypy**: Static type checking
- **interrogate**: Docstring coverage

**Auto-formatting:**
- Automatically formats code on pull requests
- Commits changes back to PR branch

### 4. Security Scanning (`security.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main`
- Weekly schedule (Sunday at midnight)
- Manual dispatch

**Tools:**
- **Bandit**: Security issue detection
- **Safety**: Known vulnerability checking
- **pip-audit**: Dependency vulnerability scanning
- **CodeQL**: Advanced semantic code analysis
- **Dependency Review**: PR dependency change analysis

**Reports:**
- JSON security reports uploaded as artifacts
- CodeQL results in Security tab

### 5. Release (`release.yml`)

**Triggers:**
- Tags matching `v*.*.*` (e.g., v2.0.1)
- Manual dispatch with version input

**Steps:**
1. Build distribution packages (wheel + sdist)
2. Test package installation across platforms
3. Publish to PyPI
4. Create GitHub release with changelog
5. Build and push Docker image

**Package Testing:**
- Tests installation on Ubuntu, macOS, Windows
- Verifies Python 3.9, 3.11, 3.13 compatibility
- Validates import functionality

## Setup Instructions

### 1. Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/AIShell.git
cd AIShell

# Install dependencies
pip install -e ".[dev,test]"

# Verify workflows
ls -la .github/workflows/
```

### 2. Enable GitHub Actions

1. Go to repository Settings
2. Navigate to Actions → General
3. Select "Allow all actions and reusable workflows"
4. Save changes

### 3. Configure Branch Protection

1. Go to Settings → Branches
2. Add rule for `main` branch:
   - Require pull request reviews
   - Require status checks to pass
   - Required checks:
     - Test Suite / test
     - Coverage / coverage
     - Code Quality / lint
     - Security Scanning / security

### 4. Set Up Code Owners

The `.github/CODEOWNERS` file is already configured. Ensure:
- Repository settings allow code owner reviews
- Update owner usernames as needed

## Badges

Add these badges to your README.md:

```markdown
# Status Badges

[![Test Suite](https://github.com/yourusername/AIShell/actions/workflows/test.yml/badge.svg)](https://github.com/yourusername/AIShell/actions/workflows/test.yml)
[![Coverage](https://github.com/yourusername/AIShell/actions/workflows/coverage.yml/badge.svg)](https://github.com/yourusername/AIShell/actions/workflows/coverage.yml)
[![Code Quality](https://github.com/yourusername/AIShell/actions/workflows/lint.yml/badge.svg)](https://github.com/yourusername/AIShell/actions/workflows/lint.yml)
[![Security](https://github.com/yourusername/AIShell/actions/workflows/security.yml/badge.svg)](https://github.com/yourusername/AIShell/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/yourusername/AIShell/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/AIShell)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
```

## Secrets Configuration

Configure these secrets in Settings → Secrets and variables → Actions:

### Required Secrets

| Secret | Description | Required For |
|--------|-------------|--------------|
| `CODECOV_TOKEN` | Codecov upload token | Coverage reporting |
| `PYPI_API_TOKEN` | PyPI publishing token | Release workflow |
| `TEST_PYPI_API_TOKEN` | Test PyPI token | Test releases |
| `DOCKER_USERNAME` | Docker Hub username | Docker image publishing |
| `DOCKER_PASSWORD` | Docker Hub password/token | Docker image publishing |

### Getting Tokens

**Codecov Token:**
1. Sign up at https://codecov.io
2. Add your repository
3. Copy the upload token
4. Add as `CODECOV_TOKEN` secret

**PyPI Token:**
1. Create account at https://pypi.org
2. Go to Account Settings → API tokens
3. Create token with scope "Entire account" or specific project
4. Add as `PYPI_API_TOKEN` secret

**Docker Hub Token:**
1. Sign in to https://hub.docker.com
2. Account Settings → Security → Access Tokens
3. Create new token
4. Add username as `DOCKER_USERNAME` and token as `DOCKER_PASSWORD`

## Testing Locally

### Using Act (GitHub Actions Local Runner)

Install act:
```bash
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Windows
choco install act-cli
```

Run workflows locally:
```bash
# List available workflows
act -l

# Run test workflow
act push -W .github/workflows/test.yml

# Run specific job
act push -j test

# Run with secrets
act -s CODECOV_TOKEN=your-token

# Use specific platform
act -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

### Manual Testing

```bash
# Run tests
pytest -v

# Check coverage
pytest --cov=. --cov-report=term-missing

# Run linting
black --check .
isort --check .
ruff check .
flake8 .
pylint **/*.py
mypy .

# Security checks
bandit -r .
safety check
pip-audit
```

## Workflow Optimization

### Caching Strategy

All workflows use caching to speed up execution:

```yaml
# pip dependencies
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'

# pytest cache
- uses: actions/cache@v4
  with:
    path: .pytest_cache
    key: pytest-${{ runner.os }}-${{ matrix.python-version }}
```

### Parallel Execution

- Test workflow runs 15 jobs in parallel (5 Python versions × 3 OS)
- Uses `fail-fast: false` to run all combinations
- Concurrency groups prevent duplicate runs

### Artifact Management

Artifacts are retained for 30 days:
- Test results (JUnit XML)
- Coverage reports (HTML)
- Security reports (JSON)
- Distribution packages

## Troubleshooting

### Common Issues

**1. Tests Failing on Specific Python Version**

```bash
# Test locally with specific version
pyenv install 3.12.0
pyenv local 3.12.0
pytest
```

**2. Coverage Below Threshold**

```bash
# Generate detailed coverage report
pytest --cov=. --cov-report=term-missing --cov-report=html
open htmlcov/index.html
# Add tests for uncovered lines
```

**3. Linting Failures**

```bash
# Auto-fix formatting
black .
isort .

# Check remaining issues
ruff check . --fix
flake8 .
```

**4. Security Vulnerabilities**

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Check specific package
pip install --upgrade package-name

# Audit all dependencies
pip-audit --fix
```

**5. Release Workflow Fails**

Check:
- Tag format matches `v*.*.*`
- PyPI token is valid
- Package version matches tag
- All tests pass before release

**6. Docker Build Fails**

```bash
# Test Docker build locally
docker build -t aishell:test .
docker run -it aishell:test python -c "import aishell; print(aishell.__version__)"
```

### Debug Mode

Enable debug logging in workflows:

1. Repository Settings → Secrets and variables → Actions
2. Add repository secret: `ACTIONS_STEP_DEBUG` = `true`
3. Add repository secret: `ACTIONS_RUNNER_DEBUG` = `true`

### Getting Help

- Check [Actions docs](https://docs.github.com/en/actions)
- Review [workflow runs](https://github.com/yourusername/AIShell/actions)
- Open issue for persistent problems

## Maintenance

### Regular Tasks

- **Weekly**: Review Dependabot PRs
- **Monthly**: Update GitHub Actions versions
- **Quarterly**: Review and update security policies
- **Per Release**: Verify all workflows pass

### Updating Workflows

1. Create feature branch
2. Modify workflow files
3. Test with `act` locally
4. Create PR (workflows will test themselves)
5. Merge after approval

## Performance Metrics

Current pipeline performance:

| Workflow | Average Duration | Parallel Jobs |
|----------|-----------------|---------------|
| Test Suite | 8-12 minutes | 15 |
| Coverage | 3-5 minutes | 1 |
| Code Quality | 2-4 minutes | 2 |
| Security | 5-8 minutes | 3 |
| Release | 15-20 minutes | 4 |

## Best Practices

1. **Always run tests locally before pushing**
2. **Keep workflows DRY with reusable workflows**
3. **Use matrix strategies for multi-environment testing**
4. **Cache dependencies aggressively**
5. **Set appropriate timeout values**
6. **Use concurrency groups to prevent waste**
7. **Monitor workflow costs in Usage tab**
8. **Keep secrets secure and rotate regularly**
9. **Review security alerts promptly**
10. **Document any workflow changes**

## Advanced Configuration

### Custom Runners

For private repositories or specialized hardware:

```yaml
jobs:
  test:
    runs-on: [self-hosted, linux, x64]
```

### Conditional Execution

```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

### Manual Approval

For production deployments:

```yaml
jobs:
  deploy:
    environment:
      name: production
      url: https://pypi.org/project/agentic-aishell
```

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python in Actions](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Act - Local Testing](https://github.com/nektos/act)
- [Codecov Documentation](https://docs.codecov.io/)
- [PyPI Publishing Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

---

**Last Updated**: 2025-10-12
**Version**: 1.0.0
**Maintained By**: @ruvnet
