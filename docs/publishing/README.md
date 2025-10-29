# NPM Publishing Documentation

This directory contains all documentation and resources for publishing AI Shell to NPM.

## Files

### [NPM_PUBLISHING_GUIDE.md](./NPM_PUBLISHING_GUIDE.md)
Complete step-by-step guide for publishing to NPM, including:
- Prerequisites and account setup
- First-time publishing instructions
- Update publishing workflow
- Troubleshooting common issues
- Best practices

### [npm-publish-setup.md](./npm-publish-setup.md)
Detailed setup report covering:
- Current configuration analysis
- Package name availability check
- Build verification
- File structure review
- Pre-publishing checklist
- Recommendations

### [package-json-template.json](./package-json-template.json)
Template package.json with all required metadata:
- Proper package naming (scoped)
- Complete metadata fields
- Repository URLs
- Keywords for discovery
- Scripts for publishing

## Quick Start

### 1. Choose Package Name

The name `ai-shell` is taken. Options:
- Use scoped: `@your-username/ai-shell`
- Alternative: `aishell-db`, `aishell-cli`, etc.

### 2. Update package.json

Copy fields from `package-json-template.json` to your `package.json`:
```bash
# Update these fields:
- name (choose from options above)
- author (your name and email)
- repository (your GitHub URL)
- bugs (your GitHub issues URL)
- homepage (your GitHub README URL)
```

### 3. Run Validation

```bash
bash scripts/prepublish.sh
```

### 4. Test Locally

```bash
npm pack
npm install -g ./ai-shell-1.0.0.tgz
ai-shell --version
```

### 5. Publish

```bash
# Automated (recommended)
bash scripts/publish.sh --patch

# Manual
npm publish --access public
```

## Scripts

### `/home/claude/AIShell/aishell/scripts/prepublish.sh`
Validates package before publishing:
- Checks package.json
- Verifies build
- Tests compilation
- Validates bin files
- Checks for sensitive files

### `/home/claude/AIShell/aishell/scripts/publish.sh`
Automates publishing process:
- Version bumping
- CHANGELOG updates
- Git tagging
- NPM publishing
- Git pushing

Usage:
```bash
bash scripts/publish.sh [--major|--minor|--patch] [--dry-run] [--skip-tests]
```

## Files Created

The NPM publishing setup has created:

1. **Configuration Files:**
   - `.npmignore` - Excludes unnecessary files from package
   - `CHANGELOG.md` - Version history tracking

2. **Scripts:**
   - `scripts/prepublish.sh` - Pre-publish validation
   - `scripts/publish.sh` - Automated publishing

3. **Documentation:**
   - `docs/publishing/NPM_PUBLISHING_GUIDE.md` - Complete guide
   - `docs/publishing/npm-publish-setup.md` - Setup report
   - `docs/publishing/package-json-template.json` - Template
   - `docs/publishing/README.md` - This file

## Package.json Scripts

Added to your package.json:

```json
{
  "scripts": {
    "prepublishOnly": "npm run clean && npm run build && npm test",
    "prepack": "bash scripts/prepublish.sh"
  }
}
```

These run automatically before `npm publish`.

## Checklist Before First Publish

- [ ] Choose package name (scoped or alternative)
- [ ] Update package.json metadata
- [ ] Run `bash scripts/prepublish.sh`
- [ ] Fix any validation errors
- [ ] Test locally with `npm pack`
- [ ] Create NPM account (if needed)
- [ ] Login with `npm login`
- [ ] Enable 2FA on NPM account
- [ ] Run `bash scripts/publish.sh --patch`

## Important Notes

1. **Package Name:** Must be unique on NPM or use scoped package
2. **Version 1.0.0:** Signals production-ready (consider 0.1.0 if not stable)
3. **Scoped Packages:** Require `--access public` flag
4. **Testing:** Always test locally before publishing
5. **Automation:** Use provided scripts for consistency

## Support

- NPM Documentation: https://docs.npmjs.com/
- Issues: File in your repository's issue tracker
- Questions: Check NPM_PUBLISHING_GUIDE.md

## Next Steps

1. Read [NPM_PUBLISHING_GUIDE.md](./NPM_PUBLISHING_GUIDE.md)
2. Update package.json with your metadata
3. Run validation script
4. Test locally
5. Publish to NPM

---

**Last Updated:** 2025-10-29
