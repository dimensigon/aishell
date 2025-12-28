# Pre-Publish Checklist for ai-shell-py

Complete this checklist before publishing to PyPI.

## Code Quality

- [ ] All tests pass: `pytest tests/`
- [ ] Test coverage > 80%: `pytest --cov=ai_shell_py tests/`
- [ ] No linting errors: `ruff check ai_shell_py/`
- [ ] Code formatted: `black ai_shell_py/`
- [ ] Type checking passes: `mypy ai_shell_py/`
- [ ] No security vulnerabilities: `pip-audit`

## Package Structure

- [ ] `pyproject.toml` exists and is valid
- [ ] `setup.py` exists (backwards compatibility)
- [ ] `README.md` exists and is comprehensive
- [ ] `LICENSE` file exists (MIT)
- [ ] `MANIFEST.in` includes necessary files
- [ ] `CHANGELOG.md` updated with new version
- [ ] `ai_shell_py/__init__.py` has correct version
- [ ] `py.typed` file exists for type checking support

## Documentation

- [ ] README includes installation instructions
- [ ] README includes usage examples
- [ ] README lists all optional dependencies
- [ ] API documentation is up to date
- [ ] Docstrings complete for public APIs
- [ ] Links in README are valid
- [ ] Images/badges display correctly

## Version Management

- [ ] Version incremented in `pyproject.toml`
- [ ] Version matches in `ai_shell_py/__init__.py`
- [ ] Version follows semantic versioning (X.Y.Z)
- [ ] CHANGELOG.md has entry for this version
- [ ] Git working directory is clean: `git status`
- [ ] All changes committed to git

## Dependencies

- [ ] All dependencies listed in `pyproject.toml`
- [ ] Dependency versions pinned appropriately
- [ ] Optional dependencies grouped correctly
- [ ] No development dependencies in main list
- [ ] All dependencies available on PyPI

## Build Process

- [ ] Clean build directory: `rm -rf dist/ build/`
- [ ] Build succeeds: `python3 -m build`
- [ ] Both wheel and sdist created
- [ ] Package passes twine check: `twine check dist/*`
- [ ] No warnings from twine
- [ ] File sizes reasonable (check `ls -lh dist/`)

## TestPyPI Testing

- [ ] Uploaded to TestPyPI: `twine upload -r testpypi dist/*`
- [ ] TestPyPI page renders correctly
- [ ] README displays properly on TestPyPI
- [ ] Metadata (author, license, etc.) correct
- [ ] Links work on TestPyPI page
- [ ] Can install from TestPyPI:
  ```bash
  pip install --index-url https://test.pypi.org/simple/ \
      --extra-index-url https://pypi.org/simple/ ai-shell-py
  ```
- [ ] Imports work after TestPyPI installation
- [ ] Basic functionality works
- [ ] Optional extras install correctly

## PyPI Account

- [ ] PyPI account created and verified
- [ ] 2FA enabled on PyPI account
- [ ] API token created (project-scoped if possible)
- [ ] Token stored securely (env var or .pypirc)
- [ ] Token tested and working

## Git Tagging

- [ ] Create git tag: `git tag -a v1.0.0 -m "Release 1.0.0"`
- [ ] Tag pushed: `git push origin v1.0.0`
- [ ] GitHub release created from tag
- [ ] Release notes added to GitHub release

## Final Verification

- [ ] Package name available on PyPI (first release) or owned by you
- [ ] No conflicts with existing package names
- [ ] All team members notified
- [ ] Documentation website updated (if applicable)
- [ ] Changelog reviewed by team

## Post-Publish Tasks

After successful publication:

- [ ] Verify package on PyPI: https://pypi.org/project/ai-shell-py/
- [ ] Test installation from PyPI: `pip install ai-shell-py`
- [ ] Verify imports work: `python -c "import ai_shell_py"`
- [ ] Test with different Python versions (3.9, 3.10, 3.11, 3.12)
- [ ] Announce release (social media, forums, etc.)
- [ ] Update project documentation with new version
- [ ] Create GitHub release with binaries (if applicable)
- [ ] Monitor PyPI download stats
- [ ] Monitor for bug reports/issues

## Emergency Rollback

If critical issues found after publication:

1. **Cannot delete PyPI versions**, but can:
   - Yank the release: `twine upload --skip-existing --yank dist/*`
   - Publish hotfix version immediately
   - Update documentation with warnings

2. **Hotfix Process**:
   - Increment patch version (1.0.0 → 1.0.1)
   - Fix critical issue
   - Run full checklist again
   - Publish hotfix
   - Document in CHANGELOG

## Automation (Future)

Consider automating with GitHub Actions:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI
on:
  release:
    types: [published]
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - name: Build and publish
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: |
          pip install build twine
          python -m build
          twine upload dist/*
```

## Notes

- **First Release**: Extra scrutiny needed as it sets expectations
- **Breaking Changes**: Increment major version (1.x.x → 2.0.0)
- **New Features**: Increment minor version (1.0.x → 1.1.0)
- **Bug Fixes**: Increment patch version (1.0.0 → 1.0.1)

## Sign-Off

- [ ] Package maintainer reviewed: _______________
- [ ] Technical lead approved: _______________
- [ ] Date: _______________
- [ ] Ready for publication: YES / NO

---

**Remember**: Once published to PyPI, you cannot delete or modify that version. Only publish when confident!
