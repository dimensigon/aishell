# NPM Publishing Checklist

Quick reference checklist for publishing AI Shell to NPM.

## Pre-Publishing Setup (One-Time)

### 1. NPM Account Setup
- [ ] Create NPM account at https://www.npmjs.com/signup
- [ ] Verify email address
- [ ] Enable Two-Factor Authentication (2FA)
- [ ] Save backup codes securely
- [ ] Test login: `npm whoami`

### 2. Package Name Decision
**CRITICAL:** The name `ai-shell` is already taken!

Choose one:
- [ ] Option A: Use scoped package `@your-username/ai-shell`
- [ ] Option B: Use alternative name (e.g., `aishell-db`, `aishell-cli`)

**Selected Name:** `_________________`

### 3. Update package.json

Copy from `docs/publishing/package-json-template.json` and update:

- [ ] `name` field (your chosen package name)
- [ ] `author` field: `"Your Name <your.email@example.com>"`
- [ ] `repository.url`: `"https://github.com/your-username/ai-shell.git"`
- [ ] `bugs.url`: `"https://github.com/your-username/ai-shell/issues"`
- [ ] `homepage`: `"https://github.com/your-username/ai-shell#readme"`

Add these scripts if not present:
```json
{
  "scripts": {
    "prepublishOnly": "npm run clean && npm run build && npm test",
    "prepack": "bash scripts/prepublish.sh"
  }
}
```

Add files field:
```json
{
  "files": [
    "dist/",
    "README.md",
    "LICENSE"
  ]
}
```

### 4. Verify Files Exist
- [ ] README.md exists and is complete
- [ ] LICENSE file exists (MIT license)
- [ ] CHANGELOG.md exists (created by setup)
- [ ] .npmignore exists (created by setup)

## Pre-Publishing Validation

### 1. Code Quality
```bash
# Run all checks
npm run lint          # Should pass
npm run typecheck     # Should pass (may have warnings)
npm test              # Should pass
npm run build         # Should succeed
```

- [ ] Linting passes
- [ ] Type checking passes (or only warnings)
- [ ] Tests pass
- [ ] Build succeeds

### 2. Run Pre-Publish Script
```bash
bash scripts/prepublish.sh
```

- [ ] All validation checks pass
- [ ] No sensitive files detected
- [ ] Package size is reasonable
- [ ] All bin files have shebangs

### 3. Local Testing
```bash
# Create package tarball
npm pack

# Install globally from tarball
npm install -g ./ai-shell-1.0.0.tgz

# Test all commands work
ai-shell --version
ai-shell --help
aishell-grafana --help
ai-shell-mcp-server --help

# Uninstall test package
npm uninstall -g ai-shell
```

- [ ] Package builds successfully
- [ ] Global install works
- [ ] All bin commands are accessible
- [ ] Help text displays correctly
- [ ] Version matches package.json

### 4. Git Status
```bash
git status
```

- [ ] Working directory is clean
- [ ] All changes are committed
- [ ] On correct branch (main/master)

## Publishing Process

### Option 1: Automated Publishing (Recommended)

```bash
# Dry run first to see what would happen
bash scripts/publish.sh --patch --dry-run

# Actual publish (interactive)
bash scripts/publish.sh --patch
```

The script will:
- [ ] Check git status
- [ ] Run validation
- [ ] Update version
- [ ] Update CHANGELOG.md
- [ ] Commit changes
- [ ] Create git tag
- [ ] Build package
- [ ] Prompt for publish confirmation
- [ ] Publish to NPM
- [ ] Push to git repository

### Option 2: Manual Publishing

```bash
# 1. Update version
npm version patch  # or minor, or major

# 2. Update CHANGELOG.md
# Add new version section manually

# 3. Commit changes
git add .
git commit -m "chore: release v1.0.1"

# 4. Tag release
git tag -a v1.0.1 -m "Release v1.0.1"

# 5. Build
npm run build

# 6. Publish
npm publish --access public  # Use --access public for scoped packages

# 7. Push to git
git push && git push --tags
```

- [ ] Version updated
- [ ] CHANGELOG updated
- [ ] Changes committed
- [ ] Tag created
- [ ] Package built
- [ ] Published to NPM
- [ ] Pushed to git

## Post-Publishing

### 1. Verify Publication
```bash
# Check package on NPM
npm view ai-shell  # or @your-username/ai-shell

# View on web
open https://www.npmjs.com/package/ai-shell
```

- [ ] Package visible on NPM
- [ ] Version number correct
- [ ] Metadata displays correctly

### 2. Test Installation
```bash
# On clean system or new terminal
npm install -g ai-shell  # or @your-username/ai-shell

# Test commands
ai-shell --version
ai-shell --help
```

- [ ] Package installs successfully
- [ ] Commands are accessible
- [ ] Version is correct

### 3. Update Repository
- [ ] Add NPM badge to README.md:
  ```markdown
  [![npm version](https://badge.fury.io/js/ai-shell.svg)](https://www.npmjs.com/package/ai-shell)
  [![npm downloads](https://img.shields.io/npm/dm/ai-shell.svg)](https://www.npmjs.com/package/ai-shell)
  ```
- [ ] Update installation instructions
- [ ] Commit and push changes

### 4. Announce Release
- [ ] Create GitHub release
- [ ] Update project documentation
- [ ] Announce on social media (optional)
- [ ] Post to relevant communities (optional)

## Updating Existing Package

For subsequent releases:

### Determine Version Bump
- **Patch (1.0.0 → 1.0.1):** Bug fixes only
- **Minor (1.0.0 → 1.1.0):** New features (backward compatible)
- **Major (1.0.0 → 2.0.0):** Breaking changes

### Quick Update Process
```bash
# 1. Run validation
bash scripts/prepublish.sh

# 2. Publish with version bump
bash scripts/publish.sh --patch  # or --minor or --major

# 3. Verify
npm view ai-shell
```

- [ ] Validation passed
- [ ] Published successfully
- [ ] New version visible on NPM

## Troubleshooting

### Common Issues

**Package name taken:**
- Use scoped package: `@username/ai-shell`
- Or choose different name

**Not logged in:**
```bash
npm login
```

**Build errors:**
```bash
npm run clean
npm run build
```
- Fix TypeScript errors before publishing

**Git not clean:**
```bash
git status
git add .
git commit -m "fix: resolve issues"
```

**Version already published:**
```bash
npm version patch  # Bump version
npm publish
```

**Package too large:**
- Review files with: `npm pack --dry-run`
- Update .npmignore to exclude more files

## Quick Reference Commands

```bash
# Validation
bash scripts/prepublish.sh

# Local test
npm pack && npm install -g ./ai-shell-1.0.0.tgz

# Automated publish
bash scripts/publish.sh --patch

# Manual publish
npm publish --access public

# Check published package
npm view ai-shell

# Test install
npm install -g ai-shell
```

## Notes

- **Always test locally before publishing**
- **Never publish with failing tests**
- **Keep CHANGELOG.md updated**
- **Use semantic versioning**
- **Enable 2FA on NPM account**

## Resources

- [Complete Publishing Guide](./NPM_PUBLISHING_GUIDE.md)
- [Setup Report](./npm-publish-setup.md)
- [Package Template](./package-json-template.json)
- NPM Documentation: https://docs.npmjs.com/

---

**Checklist Version:** 1.0
**Last Updated:** 2025-10-29
