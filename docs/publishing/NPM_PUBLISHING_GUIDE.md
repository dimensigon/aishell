# NPM Publishing Guide for AI Shell

Complete guide for publishing AI Shell to NPM registry.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [First-Time Setup](#first-time-setup)
3. [Pre-Publishing Checklist](#pre-publishing-checklist)
4. [Publishing Process](#publishing-process)
5. [Updating Existing Package](#updating-existing-package)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Prerequisites

### 1. NPM Account Setup

**Create NPM Account:**
```bash
# Visit https://www.npmjs.com/signup
# Or use CLI:
npm adduser
```

**Two-Factor Authentication (Required):**
1. Go to https://www.npmjs.com/settings/[username]/tfa
2. Enable 2FA using authenticator app
3. Save backup codes in secure location

**Verify Account:**
```bash
npm whoami
# Should display your username
```

### 2. System Requirements

- Node.js >= 18.0.0
- npm >= 8.0.0
- Git installed and configured
- TypeScript globally installed: `npm install -g typescript`

### 3. Package Name Verification

**Important:** The name `ai-shell` is already taken on NPM!

**Options:**
1. Use scoped package: `@your-username/ai-shell`
2. Choose different name: `ai-shell-db`, `aishell-cli`, etc.
3. Request package name transfer (if original is abandoned)

**Check availability:**
```bash
npm search your-package-name
```

## First-Time Setup

### 1. Update package.json

**Option A: Use scoped package (Recommended)**
```json
{
  "name": "@your-username/ai-shell",
  "version": "1.0.0",
  "description": "AI-powered database management shell with MCP integration",
  "author": "Your Name <your.email@example.com>",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/your-username/ai-shell.git"
  },
  "bugs": {
    "url": "https://github.com/your-username/ai-shell/issues"
  },
  "homepage": "https://github.com/your-username/ai-shell#readme",
  "keywords": [
    "ai",
    "shell",
    "mcp",
    "database",
    "llm",
    "cli",
    "repl",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "grafana"
  ]
}
```

**Option B: Different package name**
```json
{
  "name": "aishell-db",
  "version": "1.0.0",
  // ... rest of configuration
}
```

### 2. Verify Files Configuration

**Main entry points:**
```json
{
  "main": "dist/cli/index.js",
  "types": "dist/types/index.d.ts",
  "bin": {
    "ai-shell": "./dist/cli/index.js",
    "aishell-grafana": "./dist/cli/grafana-integration.js",
    "ai-shell-mcp-server": "./dist/mcp/server.js"
  }
}
```

**Files to include:**
```json
{
  "files": [
    "dist/",
    "README.md",
    "LICENSE"
  ]
}
```

### 3. Create/Update .npmignore

Already created at `/home/claude/AIShell/aishell/.npmignore`

Key exclusions:
- Source TypeScript files (`src/`)
- Tests and coverage
- Development configuration
- Sensitive files (`.env`, `.vault/`)
- Documentation (except README)

## Pre-Publishing Checklist

### Automated Validation

Run the pre-publish validation script:

```bash
bash scripts/prepublish.sh
```

This checks:
- ✓ Package.json configuration
- ✓ Build configuration
- ✓ TypeScript compilation
- ✓ Build outputs exist
- ✓ Bin files have shebangs
- ✓ Type checking
- ✓ Tests passing
- ✓ No sensitive files
- ✓ Package size
- ✓ NPM pack dry run

### Manual Checks

**1. Documentation:**
- [ ] README.md is complete and accurate
- [ ] Installation instructions are clear
- [ ] Usage examples work
- [ ] API documentation is up-to-date

**2. Code Quality:**
- [ ] All tests pass: `npm test`
- [ ] No TypeScript errors: `npm run typecheck`
- [ ] Code is linted: `npm run lint`
- [ ] Build succeeds: `npm run build`

**3. Version Management:**
- [ ] Version number follows semver
- [ ] CHANGELOG.md is updated
- [ ] Git working directory is clean

**4. Legal:**
- [ ] LICENSE file exists
- [ ] All dependencies have compatible licenses
- [ ] No proprietary code included

## Publishing Process

### Option 1: Automated Publishing (Recommended)

Use the automated publish script:

```bash
# Patch version (1.0.0 -> 1.0.1)
bash scripts/publish.sh --patch

# Minor version (1.0.0 -> 1.1.0)
bash scripts/publish.sh --minor

# Major version (1.0.0 -> 2.0.0)
bash scripts/publish.sh --major

# Dry run to see what would happen
bash scripts/publish.sh --patch --dry-run

# Skip tests (use with caution)
bash scripts/publish.sh --patch --skip-tests
```

The script will:
1. Check git status is clean
2. Run pre-publish validation
3. Run tests
4. Update package.json version
5. Update CHANGELOG.md
6. Commit changes
7. Create git tag
8. Build package
9. Prompt for NPM publish confirmation
10. Publish to NPM
11. Push to git repository

### Option 2: Manual Publishing

**Step-by-step:**

```bash
# 1. Ensure clean working directory
git status

# 2. Run validation
bash scripts/prepublish.sh

# 3. Update version
npm version patch  # or minor, or major

# 4. Update CHANGELOG.md manually
# Add entry for new version with date and changes

# 5. Commit changes
git add .
git commit -m "chore: release v1.0.1"

# 6. Create git tag
git tag -a v1.0.1 -m "Release v1.0.1"

# 7. Build package
npm run build

# 8. Test package locally (optional but recommended)
npm pack
npm install -g ./ai-shell-1.0.1.tgz
ai-shell --version
ai-shell --help

# 9. Login to NPM (if not already)
npm login

# 10. Publish
npm publish --access public  # Use --access public for scoped packages

# 11. Push to git
git push && git push --tags
```

### First-Time Publishing

For the very first publish (v1.0.0):

```bash
# 1. Complete all setup steps above
# 2. Ensure version is 1.0.0 in package.json
# 3. Run full validation
bash scripts/prepublish.sh

# 4. Test package locally first
npm pack
npm install -g ./ai-shell-1.0.0.tgz

# Test all commands work:
ai-shell --version
ai-shell --help
aishell-grafana --help
ai-shell-mcp-server --help

# 5. If all tests pass, publish
npm publish --access public

# 6. Verify on NPM
npm view ai-shell
# or
npm view @your-username/ai-shell

# 7. Test installation
npm install -g ai-shell
```

## Updating Existing Package

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR** (1.0.0 -> 2.0.0): Breaking changes
- **MINOR** (1.0.0 -> 1.1.0): New features (backward compatible)
- **PATCH** (1.0.0 -> 1.0.1): Bug fixes (backward compatible)

### Update Process

```bash
# Quick update and publish
bash scripts/publish.sh --patch

# Or manual process:
npm version patch
# Edit CHANGELOG.md
git commit -am "chore: release v1.0.1"
git tag -a v1.0.1 -m "Release v1.0.1"
npm run build
npm publish
git push && git push --tags
```

### Beta/Alpha Releases

For pre-release versions:

```bash
# Set version to beta
npm version 2.0.0-beta.0

# Publish with beta tag
npm publish --tag beta

# Users install with:
npm install ai-shell@beta
```

## Troubleshooting

### Common Issues

**1. Package name already taken**
```
npm ERR! 403 Forbidden - PUT https://registry.npmjs.org/ai-shell
npm ERR! You do not have permission to publish "ai-shell"
```

**Solution:** Use scoped package or different name:
```bash
# Update package.json name field
"name": "@your-username/ai-shell"

# Publish with access public flag
npm publish --access public
```

**2. Not logged in**
```
npm ERR! need auth This command requires you to be logged in
```

**Solution:**
```bash
npm login
# Enter credentials and 2FA code
```

**3. Build files missing**
```
Error: Cannot find module './dist/cli/index.js'
```

**Solution:**
```bash
npm run build
# Verify dist/ directory exists and contains all files
ls -la dist/cli/
```

**4. Bin files not executable**
```
/usr/bin/env: 'node': No such file or directory
```

**Solution:** Ensure shebangs are present:
```bash
# Should already be in source files:
#!/usr/bin/env node
```

**5. Version already published**
```
npm ERR! 403 Forbidden - PUT https://registry.npmjs.org/ai-shell
npm ERR! You cannot publish over the previously published version 1.0.0
```

**Solution:** Bump version:
```bash
npm version patch
npm publish
```

**6. Package size too large**
```
npm notice package size:  15.2 MB
npm notice unpacked size: 45.0 MB
```

**Solution:** Check what's being included:
```bash
npm pack --dry-run
# Review and update .npmignore
```

### Getting Help

- NPM Support: https://www.npmjs.com/support
- NPM Docs: https://docs.npmjs.com/
- Package Issues: Check your repository's Issues page

## Best Practices

### Version Management

1. **Always update CHANGELOG.md** with each release
2. **Use git tags** for version tracking
3. **Follow semver strictly** for user expectations
4. **Test before publishing** using `npm pack`

### Package Quality

1. **Keep package small**: Exclude unnecessary files
2. **Maintain README**: Clear installation and usage
3. **Include LICENSE**: Specify terms clearly
4. **Add examples**: Help users get started quickly

### Security

1. **Never include secrets**: Check with `prepublish.sh`
2. **Enable 2FA**: Protect your NPM account
3. **Use .npmignore**: Exclude sensitive files
4. **Review dependencies**: Audit regularly with `npm audit`

### Maintenance

1. **Respond to issues**: Monitor GitHub issues
2. **Update dependencies**: Keep packages current
3. **Deprecate old versions**: Use `npm deprecate` if needed
4. **Test on clean install**: Use Docker or VMs

### Documentation

1. **README.md essentials:**
   - Installation instructions
   - Quick start guide
   - API documentation
   - Examples
   - Contributing guidelines

2. **CHANGELOG.md format:**
   ```markdown
   ## [1.0.1] - 2025-10-29
   ### Added
   - New feature X
   ### Fixed
   - Bug in Y
   ### Changed
   - Updated Z
   ```

3. **Package.json metadata:**
   - Descriptive keywords
   - Repository URL
   - Bug tracker URL
   - Homepage URL

## Quick Reference

### Essential Commands

```bash
# Check authentication
npm whoami

# Search for package name
npm search package-name

# View package info
npm view package-name

# Test package locally
npm pack
npm install -g ./package-name-1.0.0.tgz

# Validate package
bash scripts/prepublish.sh

# Publish new version
bash scripts/publish.sh --patch

# Manual version bump
npm version patch

# Publish manually
npm publish --access public

# Deprecate version
npm deprecate package-name@1.0.0 "Reason"

# Unpublish (within 72 hours only)
npm unpublish package-name@1.0.0
```

### URLs to Update

After first publish, add these to README.md:

```markdown
[![npm version](https://badge.fury.io/js/ai-shell.svg)](https://www.npmjs.com/package/ai-shell)
[![npm downloads](https://img.shields.io/npm/dm/ai-shell.svg)](https://www.npmjs.com/package/ai-shell)
```

## Next Steps

After successful publishing:

1. ✓ Test installation on clean system
2. ✓ Update repository README with npm badge
3. ✓ Announce release (Twitter, Reddit, etc.)
4. ✓ Monitor for issues and feedback
5. ✓ Plan next release features

---

**Need help?** Open an issue at your repository or contact npm support.

**Last Updated:** 2025-10-29
