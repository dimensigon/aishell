# PyPI Publishing Guide for AI-Shell Python SDK

Complete guide for publishing the `ai-shell-py` package to PyPI.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Package Structure](#package-structure)
3. [PyPI Account Setup](#pypi-account-setup)
4. [Building the Package](#building-the-package)
5. [Testing with TestPyPI](#testing-with-testpypi)
6. [Publishing to PyPI](#publishing-to-pypi)
7. [Version Management](#version-management)
8. [Post-Publication](#post-publication)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Prerequisites

### Required Software

- **Python 3.9+**: Check with `python3 --version`
- **pip**: Python package installer (comes with Python)
- **git**: Version control (for tagging releases)

### Required Python Packages

Install the required tools:

```bash
pip install --upgrade pip
pip install build twine
```

### Environment Setup

1. Navigate to the package directory:
```bash
cd /path/to/AIShell/python-package
```

2. Verify package structure:
```bash
ls -la
# Should see: pyproject.toml, setup.py, README.md, ai_shell_py/
```

## Package Structure

```
python-package/
├── pyproject.toml          # Package configuration (PEP 621)
├── setup.py                # Backwards compatibility
├── README.md               # Package documentation
├── LICENSE                 # MIT License
├── MANIFEST.in            # File inclusion rules
├── CHANGELOG.md           # Version history (create before publishing)
├── ai_shell_py/           # Main package
│   ├── __init__.py        # Package initialization
│   ├── py.typed           # PEP 561 type marker
│   ├── database/          # Database clients
│   ├── mcp_clients/       # MCP integration
│   └── agents/            # AI agents
├── tests/                 # Test suite (not published)
├── scripts/               # Build/publish scripts
│   ├── build-python.sh
│   ├── publish-python.sh
│   └── test-install.sh
└── docs/                  # Documentation (not published)
```

## PyPI Account Setup

### 1. Create PyPI Accounts

You need accounts on both TestPyPI (for testing) and PyPI (production):

- **TestPyPI**: https://test.pypi.org/account/register/
- **PyPI**: https://pypi.org/account/register/

### 2. Enable Two-Factor Authentication (2FA)

**Highly recommended for security:**

1. Go to Account Settings
2. Enable 2FA using TOTP app (Google Authenticator, Authy, etc.)
3. Save recovery codes in a secure location

### 3. Create API Tokens

**For TestPyPI:**

1. Login to https://test.pypi.org
2. Go to Account Settings → API tokens
3. Click "Add API token"
4. Name: "ai-shell-py-test"
5. Scope: "Entire account" or "Project: ai-shell-py"
6. Copy the token (starts with `pypi-`)

**For PyPI:**

1. Login to https://pypi.org
2. Go to Account Settings → API tokens
3. Click "Add API token"
4. Name: "ai-shell-py"
5. Scope: "Entire account" or "Project: ai-shell-py"
6. Copy the token (starts with `pypi-`)

### 4. Store Tokens Securely

**Option 1: Environment Variables (recommended)**

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export TEST_PYPI_TOKEN="pypi-..."
export PYPI_TOKEN="pypi-..."
```

Then reload: `source ~/.bashrc`

**Option 2: `.pypirc` File**

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

Set permissions: `chmod 600 ~/.pypirc`

## Building the Package

### Automatic Build (Recommended)

Use the provided build script:

```bash
cd python-package
./scripts/build-python.sh
```

The script will:
1. ✓ Check Python version (>= 3.9)
2. ✓ Install/verify build tools
3. ✓ Clean previous builds
4. ✓ Validate package structure
5. ✓ Check for LICENSE file
6. ✓ Build wheel and source distribution
7. ✓ Verify artifacts
8. ✓ Run twine checks

### Manual Build

If you prefer manual control:

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Build package
python3 -m build

# Check package
python3 -m twine check dist/*
```

### Verify Build Output

Check `dist/` directory:

```bash
ls -lh dist/
# Should see:
# ai_shell_py-1.0.0-py3-none-any.whl      (wheel distribution)
# ai_shell_py-1.0.0.tar.gz                (source distribution)
```

## Testing with TestPyPI

**Always test on TestPyPI before publishing to PyPI!**

### 1. Upload to TestPyPI

```bash
# Using the publish script (recommended)
./scripts/publish-python.sh --test

# OR manually
python3 -m twine upload --repository testpypi dist/*
```

### 2. Test Installation

Create a test virtual environment:

```bash
# Create and activate venv
python3 -m venv /tmp/test-ai-shell-py
source /tmp/test-ai-shell-py/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    ai-shell-py

# Test import
python3 -c "import ai_shell_py; print(ai_shell_py.__version__)"

# Test with extras
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    ai-shell-py[postgresql,mysql]

# Deactivate and cleanup
deactivate
rm -rf /tmp/test-ai-shell-py
```

### 3. Automated Test

Use the test script:

```bash
./scripts/test-install.sh --testpypi --clean
```

### 4. Verify TestPyPI Package

Visit: https://test.pypi.org/project/ai-shell-py/

Check:
- ✓ Package name and version
- ✓ README renders correctly
- ✓ Metadata is correct
- ✓ Links work
- ✓ Dependencies listed properly

## Publishing to PyPI

### Pre-Publication Checklist

Before publishing, verify:

- [ ] All tests pass (`pytest`)
- [ ] Version number updated in `pyproject.toml`
- [ ] CHANGELOG.md updated with new version
- [ ] README.md is up to date
- [ ] LICENSE file exists
- [ ] Git commit all changes
- [ ] Git tag created: `git tag v1.0.0`
- [ ] Successfully tested on TestPyPI
- [ ] API token ready (PyPI, not TestPyPI)

### 1. Final Build

```bash
# Clean and rebuild
rm -rf dist/
./scripts/build-python.sh
```

### 2. Publish to PyPI

```bash
# Using the publish script (recommended)
./scripts/publish-python.sh

# OR manually
python3 -m twine upload dist/*
```

### 3. Verify Publication

1. Check PyPI page: https://pypi.org/project/ai-shell-py/
2. Install and test:

```bash
pip install ai-shell-py
python3 -c "import ai_shell_py; print(ai_shell_py.__version__)"
```

### 4. Push Git Tags

```bash
git push origin main
git push origin v1.0.0
```

## Version Management

### Semantic Versioning

Follow [SemVer](https://semver.org/): `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (1.0.0 → 2.0.0)
- **MINOR**: New features, backwards compatible (1.0.0 → 1.1.0)
- **PATCH**: Bug fixes, backwards compatible (1.0.0 → 1.0.1)

### Version Bump Process

1. **Update version in `pyproject.toml`**:
```toml
[project]
name = "ai-shell-py"
version = "1.0.1"  # Updated
```

2. **Update `ai_shell_py/__init__.py`**:
```python
__version__ = "1.0.1"
```

3. **Update CHANGELOG.md**:
```markdown
## [1.0.1] - 2024-01-15
### Fixed
- Fixed connection pooling issue in PostgreSQL client
- Improved error handling in MCP manager
```

4. **Commit and tag**:
```bash
git add pyproject.toml ai_shell_py/__init__.py CHANGELOG.md
git commit -m "Bump version to 1.0.1"
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin main --tags
```

5. **Build and publish**:
```bash
./scripts/build-python.sh
./scripts/publish-python.sh
```

## Post-Publication

### 1. Announce Release

- Create GitHub release from tag
- Post on social media/forums
- Update project documentation
- Notify users/contributors

### 2. Monitor Package Health

Check:
- Download statistics: https://pypistats.org/packages/ai-shell-py
- Package status on PyPI
- User issues/feedback

### 3. Create GitHub Release

```bash
# Via GitHub CLI
gh release create v1.0.0 \
    --title "Release v1.0.0" \
    --notes "See CHANGELOG.md for details"

# OR manually on GitHub
# https://github.com/yourusername/AIShell/releases/new
```

## Troubleshooting

### Common Issues

#### Issue: "Package already exists"

**Cause**: You can't re-upload the same version.

**Solution**:
1. Increment version number
2. Rebuild and upload new version

```bash
# Edit pyproject.toml: version = "1.0.1"
./scripts/build-python.sh
./scripts/publish-python.sh
```

#### Issue: "Invalid credentials"

**Cause**: Wrong or expired API token.

**Solution**:
1. Verify token in environment: `echo $PYPI_TOKEN`
2. Regenerate token on PyPI
3. Update environment variable
4. Try again

#### Issue: "README doesn't render"

**Cause**: Markdown syntax errors or unsupported features.

**Solution**:
1. Test locally: `python3 -m readme_renderer README.md`
2. Install: `pip install readme-renderer`
3. Fix any errors
4. Rebuild and re-upload (increment version)

#### Issue: "Missing dependency"

**Cause**: Dependency not found during installation.

**Solution**:
1. Check `pyproject.toml` dependencies
2. Ensure all dependencies exist on PyPI
3. Test in clean environment
4. Fix and re-publish with new version

#### Issue: "Import error after installation"

**Cause**: Package structure or imports incorrect.

**Solution**:
1. Check `__init__.py` files exist
2. Verify package name in imports matches directory name
3. Test locally: `pip install -e .`
4. Fix and re-publish with new version

### Getting Help

- **PyPI Help**: https://pypi.org/help/
- **Packaging User Guide**: https://packaging.python.org/
- **GitHub Issues**: https://github.com/yourusername/AIShell/issues

## Best Practices

### Security

1. **Never commit tokens to git**
2. Use API tokens, not passwords
3. Enable 2FA on PyPI account
4. Use project-scoped tokens when possible
5. Rotate tokens periodically

### Package Quality

1. **Always test on TestPyPI first**
2. Include comprehensive README
3. Add LICENSE file (MIT recommended)
4. Maintain CHANGELOG.md
5. Follow semantic versioning
6. Include type hints (`py.typed`)
7. Write good docstrings
8. Add examples in README

### Documentation

1. Keep README up to date
2. Document all public APIs
3. Include installation instructions
4. Provide usage examples
5. List all optional dependencies
6. Document breaking changes

### Release Process

1. Run full test suite
2. Update version and changelog
3. Test on TestPyPI
4. Commit and tag in git
5. Publish to PyPI
6. Push git tags
7. Create GitHub release
8. Announce release

### Continuous Integration

Consider adding CI/CD:

```yaml
# .github/workflows/publish-python.yml
name: Publish Python Package

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*
```

## Quick Reference

### Common Commands

```bash
# Build package
./scripts/build-python.sh

# Test on TestPyPI
./scripts/publish-python.sh --test

# Test installation
./scripts/test-install.sh --testpypi --clean

# Publish to PyPI
./scripts/publish-python.sh

# Manual upload
python3 -m twine upload dist/*

# Check package
python3 -m twine check dist/*

# Install locally for testing
pip install -e .

# Uninstall
pip uninstall ai-shell-py
```

### Important URLs

- **PyPI Package**: https://pypi.org/project/ai-shell-py/
- **TestPyPI Package**: https://test.pypi.org/project/ai-shell-py/
- **PyPI Account**: https://pypi.org/account/
- **TestPyPI Account**: https://test.pypi.org/account/
- **Packaging Guide**: https://packaging.python.org/

## Conclusion

Publishing to PyPI makes your package accessible to Python developers worldwide. Follow this guide to ensure a smooth publication process.

For questions or issues, please:
- Check the [Troubleshooting](#troubleshooting) section
- Review [PyPI documentation](https://pypi.org/help/)
- Open an issue on GitHub

Happy publishing! 🚀
