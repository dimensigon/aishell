# GitHub Workflows for AI-Shell

This directory contains automated CI/CD workflows for the AI-Shell project.

## Available Workflows

### 1. **release.yml** - PyPI Publishing & Release Automation

Automatically publishes AI-Shell to PyPI when a new version tag is created.

#### Triggers
- **Tag Push**: Automatically runs when you push a tag matching `v*.*.*` (e.g., `v2.0.1`)
- **Manual**: Can be triggered manually via GitHub Actions UI with a custom version

#### Features
- ✅ **Build Distribution**: Creates source distribution and wheel packages
- ✅ **Multi-Platform Testing**: Tests installation on Ubuntu, macOS, and Windows with Python 3.9, 3.11, and 3.13
- ✅ **PyPI Publishing**: Publishes to PyPI (supports both Trusted Publishing and API tokens)
- ✅ **Test PyPI**: Optional publishing to Test PyPI for manual workflow dispatch
- ✅ **GitHub Release**: Creates a GitHub release with changelog and artifacts
- ✅ **Docker Image**: Builds and pushes Docker image to Docker Hub

#### Setup Instructions

##### Option 1: Trusted Publishing (Recommended)

Trusted Publishing uses OpenID Connect (OIDC) for secure, keyless authentication with PyPI.

1. **Configure PyPI Trusted Publisher**:
   - Go to [PyPI Account Settings](https://pypi.org/manage/account/publishing/)
   - Add a new publisher:
     - **PyPI Project Name**: `aishell`
     - **Owner**: `dimensigon` (your GitHub org/username)
     - **Repository**: `aishell`
     - **Workflow**: `release.yml`
     - **Environment**: `pypi`

2. **No secrets required** - The workflow automatically uses OIDC!

##### Option 2: API Token (Legacy)

1. **Generate PyPI API Token**:
   - Go to [PyPI Account Settings](https://pypi.org/manage/account/token/)
   - Create a new API token with scope for the `aishell` project

2. **Add to GitHub Secrets**:
   - Go to your repository settings → Secrets and variables → Actions
   - Add secret: `PYPI_API_TOKEN` with your token value

3. **Optional - Test PyPI Token**:
   - Generate token at [Test PyPI](https://test.pypi.org/manage/account/token/)
   - Add secret: `TEST_PYPI_API_TOKEN`

##### Docker Hub Setup (Optional)

To enable Docker image publishing:

1. **Create Docker Hub Account**: [https://hub.docker.com](https://hub.docker.com)

2. **Add GitHub Secrets**:
   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_PASSWORD`: Your Docker Hub access token or password

#### Usage

##### Automatic Release (Tag-based)

```bash
# 1. Update version in pyproject.toml or setup.py
# 2. Commit changes
git add pyproject.toml
git commit -m "chore: bump version to 2.0.1"

# 3. Create and push tag
git tag v2.0.1
git push origin v2.0.1

# The workflow will automatically:
# - Build the package
# - Test on multiple platforms
# - Publish to PyPI
# - Create GitHub release
# - Build Docker image
```

##### Manual Release

1. Go to **Actions** → **Release and Publish**
2. Click **Run workflow**
3. Enter version number (e.g., `2.0.1`)
4. Click **Run workflow**

This will publish to Test PyPI first for verification.

#### Workflow Steps

1. **Build** (runs on: tag push or manual trigger)
   - Checkout code
   - Set up Python 3.11
   - Install build dependencies
   - Build source distribution and wheel
   - Verify package with `twine check`
   - Upload artifacts

2. **Test Package** (runs after build)
   - Test installation on Ubuntu, macOS, Windows
   - Test with Python 3.9, 3.11, 3.13
   - Verify package can be imported
   - Check version string

3. **Publish to PyPI** (runs after tests pass)
   - Download build artifacts
   - Publish to PyPI using Trusted Publishing or API token
   - Skip if version already exists

4. **Publish to Test PyPI** (manual workflow only)
   - Download build artifacts
   - Publish to Test PyPI for verification

5. **GitHub Release** (runs after PyPI publish)
   - Generate changelog from commits
   - Create GitHub release
   - Attach distribution files
   - Generate release notes

6. **Docker Build** (runs after PyPI publish)
   - Build Docker image
   - Push to Docker Hub with version tags
   - Tag as `latest` for main branch

#### Environment Protection (Recommended)

For additional security, configure a PyPI environment with protection rules:

1. Go to **Settings** → **Environments** → **New environment**
2. Name: `pypi`
3. Add protection rules:
   - ✅ Required reviewers (optional)
   - ✅ Wait timer (optional delay before deployment)
   - ✅ Deployment branches: Only `main` and tags

#### Troubleshooting

##### Build Failures

Check that `pyproject.toml` or `setup.py` is properly configured:

```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "aishell"
version = "2.0.0"
# ... other metadata
```

##### PyPI Upload Fails

- **Trusted Publishing**: Ensure publisher is configured correctly on PyPI
- **API Token**: Verify `PYPI_API_TOKEN` secret is set correctly
- **Version Conflict**: Check if version already exists on PyPI

##### Docker Build Fails

- Verify `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets are set
- Check that Dockerfile exists in repository root
- Ensure Docker Hub repository exists

#### Security Notes

- ✅ **Trusted Publishing** is more secure than API tokens (no long-lived credentials)
- ✅ Workflow uses `id-token: write` permission for OIDC
- ✅ All secrets are encrypted by GitHub
- ✅ Workflow runs in isolated environment
- ✅ `skip-existing: true` prevents accidental overwrites

### 2. **test.yml** - Continuous Integration

Runs tests on every push and pull request.

### 3. **coverage.yml** - Code Coverage

Measures and reports test coverage.

### 4. **lint.yml** - Code Quality

Runs linters and formatters (flake8, black, isort, mypy).

### 5. **security.yml** - Security Scanning

Scans for security vulnerabilities using bandit and safety.

## Quick Reference

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `release.yml` | Tag `v*.*.*` or manual | Publish to PyPI, create release |
| `test.yml` | Push, PR | Run test suite |
| `coverage.yml` | Push, PR | Check code coverage |
| `lint.yml` | Push, PR | Code quality checks |
| `security.yml` | Push, PR, schedule | Security vulnerability scanning |

## Release Checklist

Before creating a release:

1. ✅ All tests pass (`test.yml`)
2. ✅ Coverage meets target (`coverage.yml`)
3. ✅ No linting errors (`lint.yml`)
4. ✅ No security issues (`security.yml`)
5. ✅ Update `CHANGELOG.md`
6. ✅ Update version in `pyproject.toml`
7. ✅ Commit changes to `main` branch
8. ✅ Create and push tag: `git tag v2.0.1 && git push origin v2.0.1`

## Support

- **PyPI Package**: [https://pypi.org/project/aishell/](https://pypi.org/project/aishell/)
- **Documentation**: [https://github.com/dimensigon/aishell](https://github.com/dimensigon/aishell)
- **Issues**: [https://github.com/dimensigon/aishell/issues](https://github.com/dimensigon/aishell/issues)
