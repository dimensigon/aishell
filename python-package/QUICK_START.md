# Quick Start Guide - Publishing ai-shell-py to PyPI

Fast-track guide for publishing the ai-shell-py package.

## Prerequisites Check

```bash
# Check Python version (need 3.9+)
python3 --version

# Install tools
pip install build twine
```

## Step 1: Copy Source Code

```bash
cd /path/to/AIShell/aishell

# Copy database clients
cp -r src/database/* python-package/ai_shell_py/database/

# Copy MCP clients
cp -r src/mcp_clients/* python-package/ai_shell_py/mcp_clients/

# Copy agents
cp -r src/agents/database/* python-package/ai_shell_py/agents/

# Verify
ls python-package/ai_shell_py/
```

## Step 2: Create CHANGELOG

```bash
cd python-package

cat > CHANGELOG.md << 'EOF'
# Changelog

## [1.0.0] - 2024-01-XX

### Added
- Initial release of ai-shell-py Python SDK
- Multi-database client support (PostgreSQL, MySQL, MongoDB, Redis, Oracle, Cassandra, Neo4j, DynamoDB)
- MCP integration for AI coordination
- Database optimization and migration agents
- Backup and restore managers
- Connection pooling with retry logic
- Full async/await support
- Type hints with py.typed support
- Comprehensive documentation and examples

### Features
- Modular installation with optional database drivers
- Secure credential management
- Docker integration
- Performance monitoring
- High availability support
EOF
```

## Step 3: Build Package

```bash
# Automated build (recommended)
./scripts/build-python.sh

# Or manual
python3 -m build
python3 -m twine check dist/*
```

Expected output in `dist/`:
- `ai_shell_py-1.0.0-py3-none-any.whl`
- `ai_shell_py-1.0.0.tar.gz`

## Step 4: Setup PyPI Accounts

### TestPyPI (for testing)
1. Register: https://test.pypi.org/account/register/
2. Enable 2FA
3. Create API token: Account Settings → API tokens
4. Save token: `export TEST_PYPI_TOKEN="pypi-..."`

### PyPI (production)
1. Register: https://pypi.org/account/register/
2. Enable 2FA
3. Create API token: Account Settings → API tokens
4. Save token: `export PYPI_TOKEN="pypi-..."`

## Step 5: Test on TestPyPI

```bash
# Upload to TestPyPI
./scripts/publish-python.sh --test

# Test installation
./scripts/test-install.sh --testpypi --clean

# Manual verification
python3 -m venv /tmp/test
source /tmp/test/bin/activate
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    ai-shell-py

python3 -c "import ai_shell_py; print(ai_shell_py.__version__)"
deactivate
```

## Step 6: Verify TestPyPI

Check: https://test.pypi.org/project/ai-shell-py/

Verify:
- ✓ README renders correctly
- ✓ Metadata is accurate
- ✓ Links work
- ✓ Installation successful
- ✓ Imports work

## Step 7: Publish to PyPI

```bash
# Final checks
cd python-package
python3 -m pytest ../tests/  # Run full test suite
./scripts/build-python.sh    # Fresh build

# Publish
./scripts/publish-python.sh

# Confirm when prompted
```

## Step 8: Verify Publication

```bash
# Check PyPI page
open https://pypi.org/project/ai-shell-py/

# Test installation
python3 -m venv /tmp/verify
source /tmp/verify/bin/activate
pip install ai-shell-py
pip install ai-shell-py[postgresql,mysql,mongodb]
python3 -c "import ai_shell_py; print(ai_shell_py.__version__)"
deactivate
rm -rf /tmp/verify
```

## Step 9: Git Tag and Release

```bash
# Commit package files
git add python-package/
git commit -m "Add ai-shell-py Python package v1.0.0"

# Create tag
git tag -a v1.0.0-python -m "Python SDK v1.0.0"

# Push
git push origin main --tags

# Create GitHub release
gh release create v1.0.0-python \
    --title "ai-shell-py v1.0.0" \
    --notes "Initial release of Python SDK. See CHANGELOG.md"
```

## Step 10: Announce

- Update main README.md with PyPI badge
- Post on social media
- Notify contributors
- Update documentation

## Common Commands

```bash
# Build
./scripts/build-python.sh

# Test on TestPyPI
./scripts/publish-python.sh --test

# Publish to PyPI
./scripts/publish-python.sh

# Test installation
./scripts/test-install.sh --pypi --clean

# Clean build artifacts
rm -rf dist/ build/ *.egg-info
```

## Version Updates (Future Releases)

```bash
# 1. Update version
vim pyproject.toml              # version = "1.0.1"
vim ai_shell_py/__init__.py     # __version__ = "1.0.1"

# 2. Update changelog
vim CHANGELOG.md

# 3. Build and test
./scripts/build-python.sh
./scripts/publish-python.sh --test

# 4. Publish
./scripts/publish-python.sh

# 5. Tag
git tag v1.0.1-python
git push --tags
```

## Troubleshooting

**Build fails**: Check `pyproject.toml` syntax
**Upload fails**: Verify API token is correct
**Import fails**: Ensure `__init__.py` files exist in all directories
**README doesn't render**: Check Markdown syntax, test with `readme_renderer`

## Help

- Full guide: `docs/publishing/PYPI_PUBLISHING_GUIDE.md`
- Checklist: `docs/publishing/PRE_PUBLISH_CHECKLIST.md`
- Report: `docs/publishing/pypi-publish-setup.md`

## Important Notes

- **Cannot delete PyPI versions** - version numbers are permanent
- **Test on TestPyPI first** - always!
- **Keep tokens secure** - never commit to git
- **Use semantic versioning** - MAJOR.MINOR.PATCH

---

**Estimated Time**: 2-3 hours for first release
**Next Release**: 30-60 minutes
