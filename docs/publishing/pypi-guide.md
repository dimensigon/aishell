# PyPI Publishing Guide for AIShell

A comprehensive guide to publishing AIShell to the Python Package Index (PyPI).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [Version Management](#version-management)
4. [Building Distribution](#building-distribution)
5. [Testing on TestPyPI](#testing-on-testpypi)
6. [Publishing to PyPI](#publishing-to-pypi)
7. [Post-Publishing](#post-publishing)
8. [Automation with GitHub Actions](#automation-with-github-actions)
9. [Troubleshooting](#troubleshooting)
10. [Complete Example](#complete-example)

---

## Prerequisites

### 1. Python Packaging Knowledge

Required understanding:
- Python package structure and `__init__.py` files
- Semantic versioning (SemVer)
- Package dependencies and requirements
- Distribution formats (sdist vs wheel)

### 2. PyPI Account Setup

**Create accounts on both PyPI and TestPyPI:**

```bash
# PyPI (production)
# Register at: https://pypi.org/account/register/

# TestPyPI (testing)
# Register at: https://test.pypi.org/account/register/
```

**Enable Two-Factor Authentication (Recommended):**
1. Log in to PyPI/TestPyPI
2. Go to Account Settings → Two-Factor Authentication
3. Set up TOTP with an authenticator app

### 3. API Token Generation

**Generate API tokens for secure authentication:**

1. **PyPI Token:**
   - Navigate to: https://pypi.org/manage/account/token/
   - Click "Add API token"
   - Name: "AIShell Publishing"
   - Scope: "Entire account" or specific to "aishell"
   - **Copy the token** (shown only once): `pypi-AgEIcHl...`

2. **TestPyPI Token:**
   - Navigate to: https://test.pypi.org/manage/account/token/
   - Follow same steps as above

**Configure credentials in `~/.pypirc`:**

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...
```

**Set file permissions (important!):**
```bash
chmod 600 ~/.pypirc
```

---

## Project Setup

### 1. Modern Approach: pyproject.toml

Create `/home/claude/AIShell/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "aishell"
version = "1.0.0"
description = "AI-powered database management and intelligent shell interface"
readme = "README.md"
requires-python = ">=3.9,<3.15"
license = {text = "MIT"}
authors = [
    {name = "AI-Shell Development Team", email = "support@aishell.dev"}
]
maintainers = [
    {name = "AI-Shell Development Team", email = "support@aishell.dev"}
]
keywords = [
    "ai",
    "shell",
    "database",
    "llm",
    "cli",
    "assistant",
    "automation",
    "oracle",
    "postgresql",
    "mcp"
]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Database",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Shells",
    "Topic :: Utilities",
]

dependencies = [
    "prompt-toolkit==3.0.43",
    "textual==0.47.1",
    "click==8.1.7",
    "rich==13.7.0",
    "oracledb==2.0.0",
    "psycopg2-binary==2.9.9",
    "ollama==0.1.7",
    "sentence-transformers==2.2.2",
    "transformers==4.36.2",
    "faiss-cpu==1.12.0",
    "cryptography==41.0.7",
    "keyring==24.3.0",
    "pyyaml==6.0.1",
    "aiofiles==23.2.1",
    "asyncio-mqtt==0.16.1",
    "psutil==5.9.8",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.5",
    "pytest-asyncio==0.26.0",
    "pytest-cov==6.1.1",
    "pytest-mock==3.14.0",
    "black==23.12.1",
    "mypy==1.8.0",
    "flake8==7.0.0",
]

test = [
    "pytest==8.3.5",
    "pytest-asyncio==0.26.0",
    "pytest-cov==6.1.1",
    "pytest-mock==3.14.0",
]

[project.urls]
Homepage = "https://github.com/dimensigon/aishell"
Documentation = "https://agentic-aishell.readthedocs.io"
Repository = "https://github.com/dimensigon/aishell.git"
"Bug Tracker" = "https://github.com/dimensigon/aishell/issues"
Changelog = "https://github.com/dimensigon/aishell/blob/main/CHANGELOG.md"

[project.scripts]
aishell = "aishell:main"
agentic-aishell = "src.main:main"

[tool.setuptools]
package-dir = {"" = "src"}
packages = {find = {where = ["src"], exclude = ["tests*"]}}

[tool.setuptools.package-data]
aishell = [
    "config/*.yaml",
    "config/*.json",
    "templates/*.txt",
    "templates/*.md",
]

[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311', 'py312', 'py313', 'py314']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hive-mind
  | \.pytest_cache
  | \.venv
  | build
  | dist
)/
'''

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=src --cov-report=html --cov-report=term-missing"
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true
```

### 2. Legacy Approach: setup.py

If you need backward compatibility, create `/home/claude/AIShell/setup.py`:

```python
#!/usr/bin/env python3
"""
Setup script for AIShell package.
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read version from __init__.py
def get_version():
    init_file = Path(__file__).parent / "src" / "__init__.py"
    with open(init_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0"

# Read long description from README
def get_long_description():
    readme_file = Path(__file__).parent / "README.md"
    with open(readme_file, "r", encoding="utf-8") as f:
        return f.read()

# Read requirements
def get_requirements():
    req_file = Path(__file__).parent / "requirements.txt"
    with open(req_file, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="aishell",
    version=get_version(),
    author="AI-Shell Development Team",
    author_email="support@aishell.dev",
    description="AI-powered database management and intelligent shell interface",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/dimensigon/aishell",
    project_urls={
        "Documentation": "https://agentic-aishell.readthedocs.io",
        "Bug Tracker": "https://github.com/dimensigon/aishell/issues",
        "Source Code": "https://github.com/dimensigon/aishell",
        "Changelog": "https://github.com/dimensigon/aishell/blob/main/CHANGELOG.md",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=["tests*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Shells",
        "Topic :: Utilities",
    ],
    python_requires=">=3.9,<3.15",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=8.3.5",
            "pytest-asyncio>=0.26.0",
            "pytest-cov>=6.1.1",
            "pytest-mock>=3.14.0",
            "black>=23.12.1",
            "mypy>=1.8.0",
            "flake8>=7.0.0",
        ],
        "test": [
            "pytest>=8.3.5",
            "pytest-asyncio>=0.26.0",
            "pytest-cov>=6.1.1",
            "pytest-mock>=3.14.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aishell=aishell:main",
            "ai-shell=aishell:main",
        ],
    },
    package_data={
        "aishell": [
            "config/*.yaml",
            "config/*.json",
            "templates/*.txt",
            "templates/*.md",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "ai",
        "shell",
        "database",
        "llm",
        "cli",
        "assistant",
        "automation",
        "oracle",
        "postgresql",
        "mcp",
    ],
    license="MIT",
)
```

### 3. MANIFEST.in for Non-Python Files

Create `/home/claude/AIShell/MANIFEST.in`:

```
# Include documentation
include README.md
include LICENSE
include CHANGELOG.md
include CONTRIBUTING.md

# Include configuration files
recursive-include src/config *.yaml
recursive-include src/config *.json
recursive-include src/templates *.txt
recursive-include src/templates *.md

# Include tests
recursive-include tests *.py

# Exclude unnecessary files
global-exclude __pycache__
global-exclude *.py[co]
global-exclude .DS_Store
global-exclude .git*
global-exclude *.swp
global-exclude *.swo
global-exclude .coverage
global-exclude .pytest_cache
global-exclude .mypy_cache
global-exclude .hive-mind
global-exclude .swarm
recursive-exclude docs *.md
exclude .gitignore
exclude .coveragerc
exclude tox.ini
```

### 4. Package Structure Validation

**Verify your package structure:**

```bash
# AIShell structure
/home/claude/AIShell/
├── src/
│   ├── __init__.py           # Contains __version__ = "1.0.0"
│   ├── agents/
│   ├── config/
│   ├── core/
│   ├── database/
│   ├── llm/
│   ├── mcp_clients/
│   ├── modules/
│   ├── performance/
│   ├── security/
│   ├── ui/
│   └── vector/
├── tests/
├── docs/
├── examples/
├── README.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
└── setup.py (optional)
```

**Check that all packages have `__init__.py`:**

```bash
cd /home/claude/AIShell
find src -type d -exec test -e '{}/__init__.py' \; -print
```

---

## Version Management

### 1. Semantic Versioning (SemVer)

**Format:** `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (e.g., 1.0.0 → 2.0.0)
- **MINOR**: New features, backward compatible (e.g., 1.0.0 → 1.1.0)
- **PATCH**: Bug fixes, backward compatible (e.g., 1.0.0 → 1.0.1)

**Pre-release versions:**
- `1.0.0-alpha.1` - Alpha release
- `1.0.0-beta.1` - Beta release
- `1.0.0-rc.1` - Release candidate

### 2. Where to Update Version Numbers

**1. Primary version in `src/__init__.py`:**

```python
__version__ = "1.0.0"
```

**2. If using `pyproject.toml`:**

```toml
[project]
version = "1.0.0"
```

**3. If using `setup.py` (reads from `__init__.py`):**

```python
def get_version():
    init_file = Path(__file__).parent / "src" / "__init__.py"
    with open(init_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0"
```

**4. Update `CHANGELOG.md`:**

```markdown
# Changelog

## [1.0.0] - 2025-10-05

### Added
- Initial release
- AI-powered shell interface
- Multi-database support (Oracle, PostgreSQL)
- Health check system
- Custom agent framework

### Changed
- N/A

### Fixed
- N/A
```

### 3. Git Tagging Strategy

**Create an annotated tag for each release:**

```bash
# Update version in code
vim src/__init__.py  # Change to "1.0.0"

# Commit version change
git add src/__init__.py CHANGELOG.md
git commit -m "Bump version to 1.0.0"

# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push commits and tags
git push origin main
git push origin v1.0.0
```

**List all tags:**

```bash
git tag -l
```

**Delete a tag (if needed):**

```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin :refs/tags/v1.0.0
```

---

## Building Distribution

### 1. Install Build Tools

```bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Install build tools
python3 -m pip install --upgrade build twine

# Verify installation
python3 -m build --version
twine --version
```

### 2. Build Source Distribution (sdist)

```bash
# Navigate to project root
cd /home/claude/AIShell

# Clean previous builds
rm -rf build/ dist/ *.egg-info src/*.egg-info

# Build source distribution and wheel
python3 -m build
```

**Expected output:**

```
* Creating venv isolated environment...
* Installing packages in isolated environment... (setuptools>=68.0.0, wheel)
* Getting build dependencies for sdist...
* Building sdist...
* Building wheel from sdist
* Creating venv isolated environment...
* Installing packages in isolated environment... (setuptools>=68.0.0, wheel)
* Getting build dependencies for wheel...
* Building wheel...
Successfully built aishell-1.0.0.tar.gz and aishell-1.0.0-py3-none-any.whl
```

### 3. Verify Build Artifacts

```bash
# List generated files
ls -lh dist/
```

**Expected files:**

```
aishell-1.0.0-py3-none-any.whl    # Wheel distribution (recommended)
aishell-1.0.0.tar.gz              # Source distribution
```

**Inspect the wheel contents:**

```bash
# Extract wheel (it's a ZIP file)
unzip -l dist/aishell-1.0.0-py3-none-any.whl

# Expected structure:
# aishell/__init__.py
# aishell/agents/...
# aishell/config/...
# aishell/core/...
# aishell-1.0.0.dist-info/METADATA
# aishell-1.0.0.dist-info/WHEEL
```

**Verify package metadata:**

```bash
# Check package metadata
twine check dist/*
```

**Expected output:**

```
Checking dist/aishell-1.0.0-py3-none-any.whl: PASSED
Checking dist/aishell-1.0.0.tar.gz: PASSED
```

---

## Testing on TestPyPI

### 1. Upload to test.pypi.org

```bash
# Upload to TestPyPI (use token from ~/.pypirc)
python3 -m twine upload --repository testpypi dist/*

# Or specify credentials manually
python3 -m twine upload \
    --repository-url https://test.pypi.org/legacy/ \
    --username __token__ \
    --password pypi-AgEIcHl... \
    dist/*
```

**Expected output:**

```
Uploading distributions to https://test.pypi.org/legacy/
Uploading aishell-1.0.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 156.7/156.7 kB • 00:01 • 89.3 kB/s
Uploading aishell-1.0.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 143.2/143.2 kB • 00:00 • 112.5 kB/s

View at:
https://test.pypi.org/project/agentic-aishell/1.0.0/
```

### 2. Install from TestPyPI

**Create a test environment:**

```bash
# Create fresh virtual environment
python3 -m venv test-env
source test-env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    aishell==1.0.0
```

**Note:** The `--extra-index-url` allows dependencies to be installed from the main PyPI since they may not exist on TestPyPI.

### 3. Verify Installation Works

```bash
# Check installation
pip show aishell

# Expected output:
# Name: aishell
# Version: 1.0.0
# Summary: AI-powered database management and intelligent shell interface
# Home-page: https://github.com/dimensigon/aishell
# ...

# Test import
python3 -c "import aishell; print(aishell.__version__)"
# Output: 1.0.0

# Test entry point
aishell --help
# or
ai-shell --help

# Run basic functionality test
python3 << 'EOF'
import aishell
from aishell import mcp_clients

print(f"AIShell version: {aishell.__version__}")
print(f"MCP clients available: {dir(mcp_clients)}")
print("✅ Package imports successfully!")
EOF
```

**Clean up test environment:**

```bash
deactivate
rm -rf test-env/
```

---

## Publishing to PyPI

### 1. Final Pre-Publishing Checklist

**Before publishing to production PyPI:**

- [ ] All tests pass: `pytest tests/`
- [ ] Version number is correct in `src/__init__.py`
- [ ] `CHANGELOG.md` is updated
- [ ] Git tag created: `git tag v1.0.0`
- [ ] `README.md` is accurate and well-formatted
- [ ] Package builds cleanly: `python3 -m build`
- [ ] Metadata validates: `twine check dist/*`
- [ ] Tested on TestPyPI successfully
- [ ] License file included
- [ ] `.gitignore` excludes build artifacts

### 2. Upload to pypi.org

```bash
# Upload to production PyPI
python3 -m twine upload dist/*

# Or specify repository explicitly
python3 -m twine upload --repository pypi dist/*
```

**Expected output:**

```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading aishell-1.0.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 156.7/156.7 kB • 00:02 • 78.3 kB/s
Uploading aishell-1.0.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 143.2/143.2 kB • 00:01 • 97.8 kB/s

View at:
https://pypi.org/project/agentic-aishell/1.0.0/
```

### 3. Verify Package Page

**Visit the PyPI page:**

https://pypi.org/project/agentic-aishell/

**Verify:**
- [ ] Package name and version are correct
- [ ] README displays properly
- [ ] All metadata is accurate (author, license, classifiers)
- [ ] Links work (homepage, documentation, issues)
- [ ] Dependencies are listed correctly
- [ ] Python version requirements are correct

### 4. Installation Verification

```bash
# Install from PyPI
pip install agentic-aishell

# Verify version
python3 -c "import aishell; print(aishell.__version__)"

# Test functionality
aishell --help
```

---

## Post-Publishing

### 1. Update Documentation

**Update README badges:**

```markdown
# AI-Shell Documentation

![PyPI Version](https://img.shields.io/pypi/v/aishell)
![PyPI Downloads](https://img.shields.io/pypi/dm/aishell)
![Python Version](https://img.shields.io/pypi/pyversions/aishell)
![License](https://img.shields.io/pypi/l/aishell)
```

**Update installation instructions:**

```markdown
## Installation

### From PyPI (Recommended)

```bash
pip install agentic-aishell
```

### From Source

```bash
git clone https://github.com/dimensigon/aishell.git
cd aishell
pip install -e .
```
```

### 2. Create GitHub Release

```bash
# Push tag if not already pushed
git push origin v1.0.0
```

**On GitHub:**

1. Navigate to: https://github.com/dimensigon/aishell/releases/new
2. Select tag: `v1.0.0`
3. Release title: `AIShell v1.0.0`
4. Description (from CHANGELOG):

```markdown
## AIShell v1.0.0

First production release of AIShell! 🎉

### Features
- AI-powered shell interface with local LLM support
- Multi-database support (Oracle, PostgreSQL)
- Health check system with async monitoring
- Custom agent framework for automation
- Tool registry with validation
- Safety and approval workflows

### Installation

```bash
pip install agentic-aishell
```

### Documentation
- [Quick Start Guide](https://github.com/dimensigon/aishell#quick-start)
- [Full Documentation](https://ai-shell.readthedocs.io)
- [Tutorials](https://github.com/dimensigon/aishell/tree/main/tutorials)

### Requirements
- Python 3.9-3.14
- FAISS 1.12.0
```

5. Attach build artifacts (optional):
   - Upload `dist/aishell-1.0.0.tar.gz`
   - Upload `dist/aishell-1.0.0-py3-none-any.whl`

6. Click "Publish release"

### 3. Announce to Community

**Channels to announce:**

1. **GitHub Discussions:**
   - Post in Announcements
   - Link to release notes

2. **Social Media:**
   - Twitter/X with hashtags: #Python #AI #Database #CLI
   - LinkedIn announcement

3. **Reddit:**
   - r/Python
   - r/learnpython
   - r/database

4. **Dev.to / Medium:**
   - Write release announcement blog post

**Sample announcement:**

```markdown
🎉 AIShell v1.0.0 Released!

We're excited to announce the first production release of AIShell - an AI-powered shell interface with intelligent database management!

✨ Key Features:
- 🤖 Local LLM integration (Ollama, OpenAI, Anthropic)
- 📊 Oracle & PostgreSQL support
- 🏥 Async health monitoring
- 🔒 Built-in safety controls
- 🛠️ Custom agent framework

Install now:
pip install agentic-aishell

Docs: https://ai-shell.readthedocs.io
GitHub: https://github.com/dimensigon/aishell
```

---

## Automation with GitHub Actions

### GitHub Actions Workflow for PyPI Publishing

Create `.github/workflows/publish-pypi.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deploy to TestPyPI or PyPI'
        required: true
        default: 'testpypi'
        type: choice
        options:
          - testpypi
          - pypi

jobs:
  build-and-publish:
    name: Build and publish Python distributions
    runs-on: ubuntu-latest

    permissions:
      contents: read
      id-token: write  # For trusted publishing

    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install build dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine

    - name: Extract version from code
      id: get_version
      run: |
        VERSION=$(python -c "import sys; sys.path.insert(0, 'src'); import aishell; print(aishell.__version__)")
        echo "version=$VERSION" >> $GITHUB_OUTPUT
        echo "📦 Building version: $VERSION"

    - name: Verify version matches tag (on release)
      if: github.event_name == 'release'
      run: |
        TAG_VERSION="${GITHUB_REF#refs/tags/v}"
        CODE_VERSION="${{ steps.get_version.outputs.version }}"
        if [ "$TAG_VERSION" != "$CODE_VERSION" ]; then
          echo "❌ Version mismatch: tag=$TAG_VERSION, code=$CODE_VERSION"
          exit 1
        fi
        echo "✅ Version matches: $TAG_VERSION"

    - name: Build distributions
      run: |
        python -m build
        ls -lh dist/

    - name: Verify distributions
      run: |
        twine check dist/*

    - name: Publish to TestPyPI
      if: |
        (github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'testpypi') ||
        (github.event_name == 'release' && github.event.release.prerelease)
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        repository-url: https://test.pypi.org/legacy/
        password: ${{ secrets.TEST_PYPI_API_TOKEN }}
        skip-existing: true

    - name: Publish to PyPI
      if: |
        (github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'pypi') ||
        (github.event_name == 'release' && !github.event.release.prerelease)
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}

    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      with:
        name: python-distributions
        path: dist/
        retention-days: 30
```

### Configure GitHub Secrets

1. Go to: `https://github.com/dimensigon/aishell/settings/secrets/actions`
2. Add secrets:
   - `PYPI_API_TOKEN` - Your PyPI API token
   - `TEST_PYPI_API_TOKEN` - Your TestPyPI API token

### Automated Version Bumping

Create `.github/workflows/version-bump.yml`:

```yaml
name: Version Bump

on:
  workflow_dispatch:
    inputs:
      bump_type:
        description: 'Version bump type'
        required: true
        default: 'patch'
        type: choice
        options:
          - major
          - minor
          - patch

jobs:
  bump-version:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        token: ${{ secrets.GITHUB_TOKEN }}

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install bump2version
      run: pip install bump2version

    - name: Bump version
      run: |
        bump2version ${{ github.event.inputs.bump_type }}

    - name: Get new version
      id: new_version
      run: |
        VERSION=$(python -c "import sys; sys.path.insert(0, 'src'); import aishell; print(aishell.__version__)")
        echo "version=$VERSION" >> $GITHUB_OUTPUT

    - name: Commit and tag
      run: |
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"
        git add .
        git commit -m "Bump version to ${{ steps.new_version.outputs.version }}"
        git tag -a "v${{ steps.new_version.outputs.version }}" -m "Version ${{ steps.new_version.outputs.version }}"
        git push origin main --tags
```

---

## Troubleshooting

### Common Errors and Solutions

#### 1. Package Name Already Exists

**Error:**
```
HTTPError: 403 Forbidden from https://upload.pypi.org/legacy/
The name 'aishell' is already in use.
```

**Solution:**
- Choose a different package name: `aishell-ai`, `ai-shell-pro`, etc.
- Update name in `pyproject.toml` or `setup.py`
- Rebuild: `rm -rf dist/ && python3 -m build`

#### 2. Version Already Exists

**Error:**
```
HTTPError: 400 Bad Request from https://upload.pypi.org/legacy/
File already exists.
```

**Solution:**
- You cannot overwrite existing versions on PyPI
- Bump version number: `1.0.0` → `1.0.1`
- Update `src/__init__.py` and rebuild

#### 3. Authentication Failed

**Error:**
```
HTTPError: 403 Forbidden from https://upload.pypi.org/legacy/
Invalid or non-existent authentication information.
```

**Solutions:**

```bash
# Verify ~/.pypirc exists and has correct permissions
ls -l ~/.pypirc
chmod 600 ~/.pypirc

# Verify token format (should start with pypi-)
cat ~/.pypirc | grep password

# Try manual authentication
python3 -m twine upload \
    --username __token__ \
    --password pypi-AgEI... \
    dist/*
```

#### 4. Missing Dependencies in Wheel

**Error:**
```
ModuleNotFoundError: No module named 'aishell.config'
```

**Solution:**

```bash
# Check MANIFEST.in includes necessary files
cat MANIFEST.in

# Verify package_data in pyproject.toml
# Rebuild completely
rm -rf build/ dist/ *.egg-info src/*.egg-info
python3 -m build

# Inspect wheel contents
unzip -l dist/aishell-*.whl
```

#### 5. Invalid Metadata

**Error:**
```
WARNING: The following metadata is invalid and will be ignored:
- 'long_description_content_type' is missing
```

**Solution:**

Update `pyproject.toml`:
```toml
[project]
readme = {file = "README.md", content-type = "text/markdown"}
```

Or in `setup.py`:
```python
setup(
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
)
```

#### 6. Build Fails with Import Error

**Error:**
```
ModuleNotFoundError: No module named 'setuptools'
```

**Solution:**

```bash
# Upgrade build tools
python3 -m pip install --upgrade pip setuptools wheel build

# Build in isolated environment
python3 -m build --no-isolation
```

#### 7. README Not Displaying on PyPI

**Issue:** README shows as plain text instead of formatted Markdown

**Solutions:**

1. **Verify content type:**
```toml
[project]
readme = {file = "README.md", content-type = "text/markdown"}
```

2. **Check README has no invalid Markdown:**
```bash
# Install markdown checker
pip install pymarkdown

# Check README
pymarkdown scan README.md
```

3. **Validate with twine:**
```bash
twine check dist/*
```

---

## Complete Example

### Step-by-Step: Publishing AIShell v1.0.0

```bash
# ============================================
# 1. PREPARE PROJECT
# ============================================

cd /home/claude/AIShell

# Update version
vim src/__init__.py
# Change: __version__ = "1.0.0"

# Update CHANGELOG
vim CHANGELOG.md

# Commit changes
git add src/__init__.py CHANGELOG.md
git commit -m "Bump version to 1.0.0"

# Create tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# ============================================
# 2. BUILD PACKAGE
# ============================================

# Clean previous builds
rm -rf build/ dist/ *.egg-info src/*.egg-info

# Install build tools
python3 -m pip install --upgrade build twine

# Build distributions
python3 -m build

# Verify build
ls -lh dist/
# Expected:
# aishell-1.0.0-py3-none-any.whl
# aishell-1.0.0.tar.gz

# Check metadata
twine check dist/*
# Expected: PASSED

# ============================================
# 3. TEST ON TESTPYPI
# ============================================

# Upload to TestPyPI
python3 -m twine upload --repository testpypi dist/*

# Create test environment
python3 -m venv test-env
source test-env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    aishell==1.0.0

# Test installation
python3 -c "import aishell; print(aishell.__version__)"
aishell --help

# Clean up
deactivate
rm -rf test-env/

# ============================================
# 4. PUBLISH TO PYPI
# ============================================

# Upload to PyPI (production)
python3 -m twine upload dist/*

# Verify on PyPI
# Visit: https://pypi.org/project/agentic-aishell/1.0.0/

# Test installation from PyPI
pip install agentic-aishell
python3 -c "import aishell; print(aishell.__version__)"

# ============================================
# 5. POST-RELEASE
# ============================================

# Push commits and tags
git push origin main
git push origin v1.0.0

# Create GitHub release
# Go to: https://github.com/dimensigon/aishell/releases/new
# - Select tag: v1.0.0
# - Add release notes from CHANGELOG
# - Publish release

# Update documentation
# - Update README badges
# - Update installation instructions

# Announce release
# - GitHub Discussions
# - Social media
# - Community forums
```

### Complete pyproject.toml for AIShell

```toml
[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "aishell"
version = "1.0.0"
description = "AI-powered database management and intelligent shell interface"
readme = {file = "README.md", content-type = "text/markdown"}
requires-python = ">=3.9,<3.15"
license = {text = "MIT"}
authors = [
    {name = "AI-Shell Development Team", email = "support@aishell.dev"}
]
maintainers = [
    {name = "AI-Shell Development Team", email = "support@aishell.dev"}
]
keywords = [
    "ai", "shell", "database", "llm", "cli", "assistant",
    "automation", "oracle", "postgresql", "mcp", "faiss"
]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Database",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Shells",
    "Topic :: Utilities",
]

dependencies = [
    "prompt-toolkit==3.0.43",
    "textual==0.47.1",
    "click==8.1.7",
    "rich==13.7.0",
    "oracledb==2.0.0",
    "psycopg2-binary==2.9.9",
    "ollama==0.1.7",
    "sentence-transformers==2.2.2",
    "transformers==4.36.2",
    "faiss-cpu==1.12.0",
    "cryptography==41.0.7",
    "keyring==24.3.0",
    "pyyaml==6.0.1",
    "aiofiles==23.2.1",
    "asyncio-mqtt==0.16.1",
    "psutil==5.9.8",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.5",
    "pytest-asyncio==0.26.0",
    "pytest-cov==6.1.1",
    "pytest-mock==3.14.0",
    "black==23.12.1",
    "mypy==1.8.0",
    "flake8==7.0.0",
]

test = [
    "pytest==8.3.5",
    "pytest-asyncio==0.26.0",
    "pytest-cov==6.1.1",
    "pytest-mock==3.14.0",
]

[project.urls]
Homepage = "https://github.com/dimensigon/aishell"
Documentation = "https://agentic-aishell.readthedocs.io"
Repository = "https://github.com/dimensigon/aishell.git"
"Bug Tracker" = "https://github.com/dimensigon/aishell/issues"
Changelog = "https://github.com/dimensigon/aishell/blob/main/CHANGELOG.md"

[project.scripts]
aishell = "aishell:main"
agentic-aishell = "src.main:main"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
exclude = ["tests*"]

[tool.setuptools.package-data]
aishell = [
    "config/*.yaml",
    "config/*.json",
    "templates/*.txt",
    "templates/*.md",
]
```

---

## Best Practices & Security Tips

### Security Best Practices

1. **Never commit API tokens to Git:**
```bash
# Add to .gitignore
echo ".pypirc" >> .gitignore
echo "dist/" >> .gitignore
echo "*.egg-info" >> .gitignore
```

2. **Use API tokens, not passwords:**
- Tokens can be scoped and revoked
- Easier to rotate without changing account password

3. **Enable 2FA on PyPI:**
- Protects against account takeover
- Required for trusted publishers

4. **Verify package before publishing:**
```bash
# Install locally first
pip install -e .
# Run tests
pytest tests/
# Check with twine
twine check dist/*
```

5. **Sign releases with GPG (optional):**
```bash
# Sign distribution
gpg --detach-sign -a dist/aishell-1.0.0.tar.gz
# Upload signature
twine upload dist/* dist/*.asc
```

### Publishing Checklist

**Before EVERY release:**

- [ ] All tests pass
- [ ] Documentation is up to date
- [ ] Version bumped correctly
- [ ] CHANGELOG updated
- [ ] Git tag created
- [ ] Built cleanly (`python3 -m build`)
- [ ] Metadata valid (`twine check dist/*`)
- [ ] Tested on TestPyPI
- [ ] README renders correctly

---

## Additional Resources

### Official Documentation

- **Python Packaging Guide:** https://packaging.python.org/
- **PyPI Help:** https://pypi.org/help/
- **Setuptools Documentation:** https://setuptools.pypa.io/
- **Twine Documentation:** https://twine.readthedocs.io/

### Tools

- **build:** https://pypa-build.readthedocs.io/
- **twine:** https://twine.readthedocs.io/
- **bump2version:** https://github.com/c4urself/bump2version
- **check-wheel-contents:** https://github.com/jwodder/check-wheel-contents

### GitHub Actions

- **PyPI Publish Action:** https://github.com/pypa/gh-action-pypi-publish
- **Setup Python:** https://github.com/actions/setup-python

---

## Conclusion

You now have a complete guide to publishing AIShell to PyPI! Follow these steps carefully, and don't hesitate to test on TestPyPI first. Remember:

1. **Test thoroughly** before publishing
2. **Use TestPyPI** for practice
3. **Never reuse version numbers**
4. **Keep credentials secure**
5. **Document changes** in CHANGELOG

Happy publishing! 🚀

---

**Last Updated:** 2025-10-05
**AIShell Version:** 1.0.0
**Guide Version:** 1.0
