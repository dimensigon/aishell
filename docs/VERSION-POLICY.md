# Version Policy

**Document Version:** 1.0
**Last Updated:** 2025-10-30
**Status:** Active

---

## 1. Current Version

### Official Version: **v1.0.0**

**Source of Truth:** `/home/claude/AIShell/aishell/package.json`

```json
{
  "version": "1.0.0"
}
```

This is the **canonical version** that all documentation, code, and artifacts must reference unless specifically documenting historical or future versions.

---

## 2. Version Reference Guidelines

### 2.1 When to Use Current Version (v1.0.0)

**ALWAYS use current version in:**

- ✅ **User-facing documentation**
  - User guides (`docs/guides/`)
  - Installation guides
  - Quick start guides
  - Tutorial files
  - API references
  - CLI command references

- ✅ **Active technical documentation**
  - Architecture documents
  - Deployment guides
  - Configuration documentation
  - Security documentation
  - Integration guides

- ✅ **Metadata and headers**
  - Document footers: `Version: 1.0.0`
  - File headers: `**Version:** 1.0.0`
  - Release artifacts
  - Docker image tags
  - Package manifests

- ✅ **Code and configuration**
  - package.json
  - Docker Compose files
  - Kubernetes manifests
  - Helm charts
  - CI/CD configurations

### 2.2 When Other Versions Are Acceptable

**Historical Versions (v1.0.x, v0.x, etc.):**

Acceptable in:
- ✅ `docs/archive/` directory - Historical records
- ✅ `CHANGELOG.md` - Version history
- ✅ Migration guides - Showing upgrade paths
- ✅ Test result reports - Documenting test coverage by version
- ✅ Status reports - Project history and milestones

**Future Versions (v1.1.0, v1.2.0, v2.0.0, etc.):**

Acceptable in:
- ✅ `docs/ROADMAP.md` - Product roadmap
- ✅ `docs/FEATURE_PROPOSALS.md` - Feature planning
- ✅ `docs/PENDING_FEATURES.md` - Work backlog
- ✅ Project planning documents
- ✅ Issue tracker milestones

**IMPORTANT:** Clearly label these as future or historical:
```markdown
## Roadmap for v1.2.0 (Planned - Q1 2026)
## Historical: v0.9.0 Development Phase (Completed)
```

---

## 3. Version Update Procedures

### 3.1 When Releasing a New Version

**Follow these steps in order:**

1. **Update package.json**
   ```bash
   npm version patch  # For v1.0.1
   npm version minor  # For v1.1.0
   npm version major  # For v2.0.0
   ```

2. **Run automated update script**
   ```bash
   ./scripts/update-version.sh <new-version>
   ```

   This script will:
   - Update all documentation headers
   - Update Docker configurations
   - Update Kubernetes manifests
   - Update CI/CD files
   - Create a summary report

3. **Update CHANGELOG.md**
   ```bash
   # Add new section at top
   ## [1.0.1] - 2025-11-15
   ### Added
   - Feature description

   ### Fixed
   - Bug fix description
   ```

4. **Create release notes**
   ```bash
   cp docs/templates/RELEASE_NOTES_TEMPLATE.md RELEASE-NOTES-v1.0.1.md
   # Fill in details
   ```

5. **Validate consistency**
   ```bash
   ./scripts/check-version-consistency.sh
   # Must show all ✅ green checks
   ```

6. **Archive previous version documentation**
   ```bash
   mkdir -p docs/archive/v1.0.0/
   # Move version-specific docs to archive
   ```

7. **Commit and tag**
   ```bash
   git add .
   git commit -m "chore: bump version to v1.0.1"
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin main --tags
   ```

8. **Publish**
   ```bash
   npm publish
   docker build -t ai-shell:1.0.1 .
   docker push ai-shell:1.0.1
   ```

### 3.2 Version Numbering Convention

**We follow Semantic Versioning (semver):**

```
MAJOR.MINOR.PATCH
  |     |     |
  |     |     └─ Bug fixes, patches (v1.0.1, v1.0.2)
  |     └─────── New features, backwards-compatible (v1.1.0, v1.2.0)
  └───────────── Breaking changes (v2.0.0, v3.0.0)
```

**Examples:**
- v1.0.0 → v1.0.1: Bug fix release
- v1.0.0 → v1.1.0: New features added
- v1.0.0 → v2.0.0: Breaking API changes

**Pre-release versions:**
- v1.1.0-alpha.1: Alpha release
- v1.1.0-beta.1: Beta release
- v1.1.0-rc.1: Release candidate

---

## 4. Validation Tools

### 4.1 Automated Validation Script

**Script:** `/home/claude/AIShell/aishell/scripts/check-version-consistency.sh`

**Purpose:** Validates that all version references are consistent.

**Usage:**
```bash
# Run validation
./scripts/check-version-consistency.sh

# Expected output when consistent:
✅ package.json version correct: 1.0.0
✅ All active documentation versions correct
✅ Archive files preserved for historical context
✅ Roadmap files preserved for future planning

OVERALL: ✅ PASS - Version consistency validated
```

**Exit codes:**
- `0` - All checks passed
- `1` - Version inconsistencies found
- `2` - Script error

**CI/CD Integration:**
```yaml
# .github/workflows/version-check.yml
- name: Check version consistency
  run: |
    chmod +x scripts/check-version-consistency.sh
    ./scripts/check-version-consistency.sh
```

### 4.2 Manual Validation Checklist

Before each release, manually verify:

- [ ] package.json version updated
- [ ] All docs/guides/ files show correct version
- [ ] Docker Compose files reference correct version
- [ ] Kubernetes manifests reference correct version
- [ ] README.md shows correct version
- [ ] RELEASE-NOTES-vX.Y.Z.md created
- [ ] CHANGELOG.md updated
- [ ] Git tag created
- [ ] No stray old version references in active docs

**Quick check command:**
```bash
# Find all version references in active docs
grep -r "Version.*[0-9]\+\.[0-9]\+\.[0-9]\+" docs/ --include="*.md" \
  | grep -v archive \
  | grep -v roadmap \
  | grep -v CHANGELOG
```

---

## 5. Historical Reference Handling

### 5.1 Archive Structure

**Archive Organization:**
```
docs/archive/
├── v0.9.0/                 # Pre-release documentation
│   ├── guides/
│   └── api/
├── v1.0.0/                 # GA release documentation (archive after v1.1.0)
│   ├── guides/
│   └── api/
├── status-reports/         # Historical project status
│   ├── v1.2.0_implementation_report.md
│   └── TEST_RESULTS_V2.md
└── phase-reports/          # Development phase history
    ├── phase1-complete.md
    └── phase2-complete.md
```

### 5.2 When to Archive

**Archive previous version documentation when:**

1. A new minor version is released (v1.0.0 → v1.1.0)
2. Documentation has substantial changes
3. API changes require separate version docs
4. Users need reference to old version behavior

**How to archive:**
```bash
# When releasing v1.1.0, archive v1.0.0 docs
mkdir -p docs/archive/v1.0.0
cp -r docs/guides docs/archive/v1.0.0/
cp -r docs/api docs/archive/v1.0.0/
cp README.md docs/archive/v1.0.0/

# Update archive README
cat > docs/archive/v1.0.0/README.md << 'EOF'
# AI-Shell v1.0.0 Documentation Archive

This is the archived documentation for AI-Shell v1.0.0.

**Current Version:** v1.1.0 (see /docs/)
**Archived:** 2025-12-15
**Status:** Historical reference only

For current documentation, see the main /docs/ directory.
EOF
```

### 5.3 Linking to Archives

**In current documentation, reference archives like:**

```markdown
For documentation of previous versions:
- [v1.0.0 Documentation Archive](/docs/archive/v1.0.0/)
- [v0.9.0 Beta Documentation](/docs/archive/v0.9.0/)

Current version: [v1.1.0 Documentation](/docs/)
```

---

## 6. Future Version Planning

### 6.1 Roadmap References

**When documenting future versions in roadmap:**

Always clearly indicate they are **planned** and subject to change:

```markdown
## v1.2.0 - Enhanced Intelligence (Planned - Q1 2026)

**Status:** 🗓️ Planned
**Target Release:** Q1 2026
**Subject to change**

### Proposed Features:
- Feature A (planned)
- Feature B (under consideration)
```

### 6.2 Feature Proposals

**In FEATURE_PROPOSALS.md, use target version tags:**

```markdown
## Feature: Advanced Query Optimizer

**Target Version:** v2.1.0
**Status:** Proposal
**Priority:** High

### Description
[Feature description...]
```

### 6.3 Pending Features

**In PENDING_FEATURES.md, categorize by version:**

```markdown
## 🟢 SHORT-TERM (v1.0.1 - Bug Fix Release)
- [ ] Fix TypeScript compilation errors
- [ ] Update dependencies

## 🟡 MEDIUM-TERM (v1.1.0 - Feature Release)
- [ ] GraphQL API layer
- [ ] Enhanced RBAC

## 🔵 LONG-TERM (v2.0.0 - Major Release)
- [ ] Web UI
- [ ] Multi-tenancy
```

---

## 7. Common Patterns

### 7.1 Documentation Headers

**Standard header format:**

```markdown
# Document Title

**Version:** 1.0.0
**Last Updated:** 2025-10-30
**Status:** Current

[Document content...]
```

### 7.2 Documentation Footers

**Standard footer format:**

```markdown
---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-30
**Status:** Active

For the latest documentation, visit: https://docs.ai-shell.dev
```

### 7.3 Docker Images

**Docker tag format:**

```dockerfile
# Dockerfile
LABEL version="1.0.0"
LABEL release-date="2025-10-30"
```

```yaml
# docker-compose.yml
services:
  ai-shell:
    image: ai-shell/ai-shell:1.0.0
    # Always tag with explicit version, not 'latest'
```

### 7.4 Kubernetes Manifests

**Kubernetes version labels:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-shell
  labels:
    app.kubernetes.io/name: ai-shell
    app.kubernetes.io/version: "1.0.0"
spec:
  template:
    metadata:
      labels:
        version: "1.0.0"
```

---

## 8. Troubleshooting

### 8.1 Version Inconsistency Detected

**Problem:** Validation script reports version inconsistencies.

**Solution:**
```bash
# 1. Identify all inconsistent files
grep -r "Version.*[0-9]\+\.[0-9]\+\.[0-9]\+" docs/ --include="*.md" \
  | grep -v archive | grep -v "1.0.0"

# 2. Fix each file
sed -i 's/Version: 2\.0\.0/Version: 1.0.0/g' docs/guides/*.md

# 3. Validate
./scripts/check-version-consistency.sh

# 4. Commit fix
git add .
git commit -m "fix: correct version references to v1.0.0"
```

### 8.2 Old Version in Docker Image

**Problem:** Docker image shows old version.

**Solution:**
```bash
# 1. Update Dockerfile version
sed -i 's/version=".*"/version="1.0.0"/' Dockerfile

# 2. Rebuild image
docker build -t ai-shell:1.0.0 .

# 3. Verify
docker inspect ai-shell:1.0.0 | grep version
```

### 8.3 Git Tag Missing

**Problem:** Release tag not created.

**Solution:**
```bash
# 1. Check existing tags
git tag -l

# 2. Create missing tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# 3. Push tag
git push origin v1.0.0

# 4. Verify on GitHub
gh release view v1.0.0
```

---

## 9. Best Practices

### 9.1 Development Workflow

1. **Feature branches**: Always include version in branch name
   ```bash
   git checkout -b feature/v1.1.0-graphql-api
   ```

2. **Commit messages**: Reference target version for features
   ```bash
   git commit -m "feat(v1.1.0): add GraphQL API layer"
   ```

3. **Pull requests**: Label with target version
   ```
   Labels: v1.1.0, enhancement, api
   ```

### 9.2 Documentation Updates

1. **Always update version in header** when making significant changes
2. **Use version placeholders** in templates: `{VERSION}`
3. **Link to version-specific docs** when discussing historical behavior
4. **Archive old docs** before major version bumps

### 9.3 Release Process

1. **Pre-release validation**
   ```bash
   npm run lint
   npm run test
   npm run build
   ./scripts/check-version-consistency.sh
   ```

2. **Version bump and tag**
   ```bash
   npm version minor
   git push --follow-tags
   ```

3. **Post-release tasks**
   - Update documentation
   - Create release notes
   - Archive previous version docs
   - Update roadmap

---

## 10. FAQ

### Q: Should I update version in every commit?

**A:** No. Only update version when:
- Preparing a release
- Creating a release candidate
- Documenting a new version in roadmap

### Q: What if I find old version references?

**A:** Run the validation script and fix them:
```bash
./scripts/check-version-consistency.sh
# Follow the suggestions in the output
```

### Q: Can I use "latest" in Docker tags?

**A:** Not recommended for production. Always use explicit versions:
```yaml
# ❌ Bad
image: ai-shell:latest

# ✅ Good
image: ai-shell:1.0.0
```

### Q: How do I handle version in Python code?

**A:** Use a version constant:
```python
# src/version.py
__version__ = "1.0.0"

# Other files
from .version import __version__
```

### Q: When should I create a release branch?

**A:** For major or minor releases with long development cycles:
```bash
git checkout -b release/v1.1.0
# Stabilize, fix bugs, prepare release
# Merge to main when ready
```

---

## 11. Compliance

### 11.1 Semver Compliance

We strictly follow [Semantic Versioning 2.0.0](https://semver.org/):

- MAJOR: Breaking changes
- MINOR: New features (backwards-compatible)
- PATCH: Bug fixes (backwards-compatible)

### 11.2 Git Tagging Convention

All release tags must follow:
```
v<MAJOR>.<MINOR>.<PATCH>[-<prerelease>][+<buildmetadata>]

Examples:
v1.0.0           # GA release
v1.0.1           # Patch release
v1.1.0-alpha.1   # Alpha
v1.1.0-beta.2    # Beta
v1.1.0-rc.1      # Release candidate
```

---

## 12. Enforcement

### 12.1 CI/CD Checks

**Required checks before merge:**
- ✅ Version consistency validation passes
- ✅ All tests pass with current version
- ✅ Docker build succeeds with correct version
- ✅ Documentation builds without errors

**GitHub Action:**
```yaml
name: Version Check
on: [pull_request]
jobs:
  version-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate versions
        run: ./scripts/check-version-consistency.sh
```

### 12.2 Pre-commit Hook

**Install pre-commit hook:**
```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Check version consistency before commit
./scripts/check-version-consistency.sh
if [ $? -ne 0 ]; then
    echo "❌ Version consistency check failed"
    echo "Fix version references before committing"
    exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

---

## 13. Maintenance

### 13.1 Quarterly Audit

**Every quarter, perform version audit:**

1. Run consistency check
2. Review archive structure
3. Update roadmap versions
4. Clean up obsolete references
5. Update this policy document

**Audit checklist:**
- [ ] All active docs show current version
- [ ] Archives organized properly
- [ ] Roadmap versions realistic
- [ ] Validation script working
- [ ] Update script working
- [ ] CI/CD checks passing

### 13.2 Policy Updates

**This policy document is versioned:**

```markdown
**Document Version:** 1.1
**Last Updated:** 2025-12-01
**Changes:** Added section on pre-commit hooks
```

Update policy when:
- Versioning strategy changes
- New tools added
- Process improvements identified
- Feedback from team

---

## 14. Resources

### 14.1 Tools

- **Validation Script:** `/scripts/check-version-consistency.sh`
- **Update Script:** `/scripts/update-version.sh`
- **Template:** `/docs/templates/RELEASE_NOTES_TEMPLATE.md`

### 14.2 Documentation

- **Semver Spec:** https://semver.org/
- **Git Tagging:** https://git-scm.com/book/en/v2/Git-Basics-Tagging
- **npm versioning:** https://docs.npmjs.com/cli/v8/commands/npm-version

### 14.3 Examples

- **Current release:** `/RELEASE-NOTES-v1.0.0.md`
- **Changelog:** `/CHANGELOG.md`
- **Roadmap:** `/docs/ROADMAP.md`

---

## 15. Contact

**Questions about version policy?**
- Open an issue: https://github.com/your-org/ai-shell/issues
- Email: dev-team@ai-shell.dev

**Propose policy changes:**
- Submit PR to this document
- Discuss in team meeting
- Document rationale in PR description

---

**Policy Version:** 1.0
**Effective Date:** 2025-10-30
**Next Review:** 2026-01-30
**Maintained By:** Development Team

---

*This version policy ensures consistency, clarity, and professionalism across all AI-Shell documentation and releases.*
