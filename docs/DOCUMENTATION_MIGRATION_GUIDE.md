# Documentation Migration Guide

**For:** AI-Shell Documentation Reorganization
**Date:** October 29, 2025
**Version:** 2.0 → 3.0

---

## Quick Reference: Old → New Paths

This guide helps you update links and find documentation in the new structure.

### Most Common Documents

| Old Path | New Path | Notes |
|----------|----------|-------|
| `GETTING_STARTED.md` | `docs/getting-started/quick-start.md` | Merged with QUICK_START_CLI |
| `QUICK_START_CLI.md` | `docs/getting-started/quick-start.md` | Merged into single guide |
| `INSTALLATION.md` | `docs/getting-started/installation.md` | Consolidated installation |
| `CLI_REFERENCE.md` | `docs/cli-reference/overview.md` | Split into categories |
| `TROUBLESHOOTING.md` | `docs/user-guide/troubleshooting.md` | Moved to user guide |
| `TESTING_GUIDE.md` | `docs/development/testing.md` | Moved to development |
| `CONTRIBUTING.md` | `docs/development/contributing.md` | Moved to development |
| `ARCHITECTURE.md` | `docs/architecture/overview.md` | Renamed for clarity |
| `API_REFERENCE.md` | `docs/api-reference/overview.md` | Moved to api-reference |

### Getting Started Documents

| Old Path | New Path |
|----------|----------|
| `docs/GETTING_STARTED.md` | `docs/getting-started/quick-start.md` |
| `docs/QUICK_START_CLI.md` | `docs/getting-started/quick-start.md` |
| `docs/quick-start.md` | `docs/getting-started/quick-start.md` |
| `docs/INSTALLATION.md` | `docs/getting-started/installation.md` |
| `docs/installation.md` | `docs/getting-started/installation.md` |
| `docs/configuration.md` | `docs/getting-started/configuration.md` |

### User Guide Documents

| Old Path | New Path |
|----------|----------|
| `docs/guides/USER_GUIDE.md` | `docs/user-guide/overview.md` |
| `docs/guides/DATABASE_OPERATIONS.md` | `docs/user-guide/database-operations.md` |
| `docs/guides/QUERY_OPTIMIZATION.md` | `docs/user-guide/query-optimization.md` |
| `docs/guides/BACKUP_RECOVERY.md` | `docs/user-guide/backup-recovery.md` |
| `docs/guides/SECURITY_BEST_PRACTICES.md` | `docs/user-guide/security.md` |
| `docs/guides/MONITORING_ANALYTICS.md` | `docs/user-guide/monitoring.md` |
| `docs/guides/troubleshooting.md` | `docs/user-guide/troubleshooting.md` |
| `docs/TROUBLESHOOTING.md` | `docs/user-guide/troubleshooting.md` |
| `docs/backup-cli-guide.md` | `docs/user-guide/backup-recovery.md` |
| `docs/security-cli-guide.md` | `docs/user-guide/security.md` |

### CLI Reference Documents

| Old Path | New Path |
|----------|----------|
| `docs/CLI_REFERENCE.md` | `docs/cli-reference/overview.md` |
| `docs/cli-reference.md` | `docs/cli-reference/overview.md` |
| `docs/cli/query-optimization-commands.md` | `docs/cli-reference/query-commands.md` |
| `docs/CLI_WRAPPER_QUICK_START.md` | `docs/cli-reference/overview.md` |
| `docs/CLI_WRAPPER_USAGE.md` | `docs/cli-reference/overview.md` |
| `docs/security-cli-quick-reference.md` | `docs/cli-reference/security-commands.md` |
| `docs/mongodb-cli-usage-examples.md` | `docs/cli-reference/database-commands/mongodb.md` |

### Tutorial Documents

| Old Path | New Path |
|----------|----------|
| `docs/tutorials/natural-language-queries.md` | `docs/tutorials/beginner/your-first-query.md` |
| `docs/tutorials/database-federation.md` | `docs/tutorials/intermediate/multi-database-setup.md` |
| `docs/tutorials/backup-recovery.md` | `docs/tutorials/intermediate/backup-strategies.md` |
| `docs/tutorials/query-optimization.md` | `docs/tutorials/intermediate/query-performance.md` |
| `docs/tutorials/autonomous-devops.md` | `docs/tutorials/advanced/autonomous-devops.md` |
| `docs/tutorials/cognitive-features.md` | `docs/tutorials/advanced/cognitive-features.md` |

### Architecture Documents

| Old Path | New Path |
|----------|----------|
| `docs/ARCHITECTURE.md` | `docs/architecture/overview.md` |
| `docs/AIShell.md` | `docs/architecture/overview.md` |
| `docs/ai-shell-mcp-architecture.md` | `docs/architecture/database-integration.md` |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | `docs/architecture/overview.md` |
| `docs/architecture/MODULE_SPECIFICATIONS.md` | `docs/architecture/core-components.md` |

### API Reference Documents

| Old Path | New Path |
|----------|----------|
| `docs/API_REFERENCE.md` | `docs/api-reference/overview.md` |
| `docs/api/core.md` | `docs/api-reference/core-api.md` |
| `docs/MCP_CLIENTS.md` | `docs/api-reference/database-clients-api.md` |
| `docs/developer/MCP_CLIENT_API.md` | `docs/api-reference/database-clients-api.md` |

### Development Documents

| Old Path | New Path |
|----------|----------|
| `CONTRIBUTING.md` | `docs/development/contributing.md` |
| `docs/TESTING_GUIDE.md` | `docs/development/testing.md` |
| `docs/CI_CD_GUIDE.md` | `docs/development/release-process.md` |
| `docs/claude-code-implementation-guide.md` | `docs/development/development-setup.md` |

### Deployment Documents

| Old Path | New Path |
|----------|----------|
| `docs/deployment/DEPLOYMENT_GUIDE.md` | `docs/deployment/production-checklist.md` |
| `docs/deployment/PRODUCTION_CHECKLIST.md` | `docs/deployment/production-checklist.md` |

### Reference Materials

| Old Path | New Path |
|----------|----------|
| `docs/FAQ.md` | `docs/reference/faq.md` |
| `docs/context-quick-reference.md` | `docs/reference/command-cheatsheet.md` |
| `docs/monitoring-quick-reference.md` | `docs/reference/command-cheatsheet.md` |

---

## Link Update Patterns

### For Markdown Files

**Pattern 1: Relative links to root docs**
```markdown
# Before
[Getting Started](../GETTING_STARTED.md)
[Installation](../INSTALLATION.md)

# After
[Getting Started](../getting-started/quick-start.md)
[Installation](../getting-started/installation.md)
```

**Pattern 2: Links to guides**
```markdown
# Before
[User Guide](../guides/USER_GUIDE.md)
[Backup Guide](../guides/BACKUP_RECOVERY.md)

# After
[User Guide](../user-guide/overview.md)
[Backup Guide](../user-guide/backup-recovery.md)
```

**Pattern 3: Links to CLI reference**
```markdown
# Before
[CLI Commands](../CLI_REFERENCE.md)

# After
[CLI Commands](../cli-reference/overview.md)
[PostgreSQL Commands](../cli-reference/database-commands/postgresql.md)
```

**Pattern 4: Links to tutorials**
```markdown
# Before
[Query Optimization Tutorial](../tutorials/query-optimization.md)

# After
[Query Optimization Tutorial](../tutorials/intermediate/query-performance.md)
```

### For Code Files

**JavaScript/TypeScript imports:**
```typescript
// Before
import { guide } from '../docs/guides/USER_GUIDE.md';

// After
import { guide } from '../docs/user-guide/overview.md';
```

**Python docstrings:**
```python
# Before
"""See docs/GETTING_STARTED.md for usage"""

# After
"""See docs/getting-started/quick-start.md for usage"""
```

### For README Files

**Main README.md:**
```markdown
# Before
- [Installation](docs/INSTALLATION.md)
- [Quick Start](docs/QUICK_START_CLI.md)

# After
- [Installation](docs/getting-started/installation.md)
- [Quick Start](docs/getting-started/quick-start.md)
```

---

## Automated Link Updates

### Using sed (Linux/Mac)

```bash
# Update links to getting started
find docs -name "*.md" -type f -exec sed -i '' \
  's|GETTING_STARTED\.md|getting-started/quick-start.md|g' {} +

# Update links to installation
find docs -name "*.md" -type f -exec sed -i '' \
  's|INSTALLATION\.md|getting-started/installation.md|g' {} +

# Update links to CLI reference
find docs -name "*.md" -type f -exec sed -i '' \
  's|CLI_REFERENCE\.md|cli-reference/overview.md|g' {} +
```

### Using PowerShell (Windows)

```powershell
# Update links to getting started
Get-ChildItem -Path docs -Filter *.md -Recurse | ForEach-Object {
    (Get-Content $_.FullName) -replace 'GETTING_STARTED\.md', 'getting-started/quick-start.md' |
    Set-Content $_.FullName
}

# Update links to installation
Get-ChildItem -Path docs -Filter *.md -Recurse | ForEach-Object {
    (Get-Content $_.FullName) -replace 'INSTALLATION\.md', 'getting-started/installation.md' |
    Set-Content $_.FullName
}
```

### Using Node.js Script

```javascript
// update-doc-links.js
const fs = require('fs');
const path = require('path');
const glob = require('glob');

const replacements = {
  'GETTING_STARTED.md': 'getting-started/quick-start.md',
  'INSTALLATION.md': 'getting-started/installation.md',
  'CLI_REFERENCE.md': 'cli-reference/overview.md',
  'TROUBLESHOOTING.md': 'user-guide/troubleshooting.md',
  // Add more mappings...
};

glob('docs/**/*.md', (err, files) => {
  files.forEach(file => {
    let content = fs.readFileSync(file, 'utf8');
    let updated = false;

    Object.entries(replacements).forEach(([old, newPath]) => {
      const regex = new RegExp(old.replace('.', '\\.'), 'g');
      if (content.match(regex)) {
        content = content.replace(regex, newPath);
        updated = true;
      }
    });

    if (updated) {
      fs.writeFileSync(file, content);
      console.log(`Updated: ${file}`);
    }
  });
});
```

Run with: `node update-doc-links.js`

---

## Verification Checklist

After migration, verify these items:

### Link Verification

```bash
# Install markdown link checker
npm install -g markdown-link-check

# Check all markdown files
find docs -name "*.md" -exec markdown-link-check {} \;

# Generate report
find docs -name "*.md" -exec markdown-link-check {} \; > link-check-report.txt
```

### Manual Verification

- [ ] README.md links work
- [ ] All getting-started/ links work
- [ ] All user-guide/ links work
- [ ] All cli-reference/ links work
- [ ] All tutorials/ links work
- [ ] All architecture/ links work
- [ ] All api-reference/ links work
- [ ] All development/ links work
- [ ] Cross-directory links work
- [ ] External links still work

### User Journey Testing

Test these common paths:

1. **New User Journey**
   - Start at README.md
   - Follow "New User" path
   - Can reach installation and quick start
   - First tutorial is accessible

2. **DBA Journey**
   - Start at README.md
   - Follow "Database Administrator" path
   - Can reach operational guides
   - Backup and security docs accessible

3. **Developer Journey**
   - Start at README.md
   - Follow "Developer" path
   - Can reach architecture and API docs
   - Contributing guide accessible

---

## Troubleshooting

### Common Issues

**Issue 1: Broken relative links**

```markdown
# Problem
[Guide](../../guides/USER_GUIDE.md)  # Path depth changed

# Solution
[Guide](../../user-guide/overview.md)  # Update path depth
```

**Issue 2: Case sensitivity**

```markdown
# Problem (case-sensitive filesystems)
[Guide](user-guide/Database-Operations.md)

# Solution
[Guide](user-guide/database-operations.md)
```

**Issue 3: Absolute vs relative paths**

```markdown
# Problem
[Guide](/docs/guides/USER_GUIDE.md)  # Absolute

# Solution
[Guide](../user-guide/overview.md)  # Relative
```

### Rollback Plan

If issues arise, rollback steps:

```bash
# Revert to previous commit
git revert <migration-commit-hash>

# Or restore from backup
cp -r docs-backup/* docs/

# Verify restoration
git status
```

---

## Migration Timeline

### Phase 1: Preparation (Day 1)
- [ ] Create backup of current docs: `cp -r docs docs-backup`
- [ ] Create new directory structure
- [ ] Test link update scripts on sample files

### Phase 2: Content Migration (Days 2-3)
- [ ] Move getting-started docs
- [ ] Move user-guide docs
- [ ] Move cli-reference docs
- [ ] Move tutorials
- [ ] Move architecture docs
- [ ] Move api-reference docs
- [ ] Move development docs

### Phase 3: Link Updates (Day 4)
- [ ] Run automated link update scripts
- [ ] Manual review of updated links
- [ ] Fix any broken links

### Phase 4: Verification (Day 5)
- [ ] Run link checker on all files
- [ ] Test user journeys
- [ ] Review with team

### Phase 5: Cleanup (Day 6)
- [ ] Archive old files
- [ ] Update CI/CD
- [ ] Announce changes

---

## Communication Plan

### Announcement Template

```markdown
# Documentation Reorganization Complete

We've reorganized AI-Shell documentation for better usability!

## What Changed

- **Clearer Structure**: 15 logical sections (down from 40+)
- **Easier Navigation**: User-type entry points (New User, DBA, Developer, DevOps)
- **Less Duplication**: Single source of truth for all topics
- **Better Learning Path**: Progressive disclosure from beginner to advanced

## How to Find Things

Old Path → New Path examples:
- GETTING_STARTED.md → docs/getting-started/quick-start.md
- CLI_REFERENCE.md → docs/cli-reference/overview.md
- guides/ → user-guide/

Full migration guide: [DOCUMENTATION_MIGRATION_GUIDE.md](DOCUMENTATION_MIGRATION_GUIDE.md)

## Need Help?

- Check the [Migration Guide](DOCUMENTATION_MIGRATION_GUIDE.md)
- See [Old → New Path Table](#quick-reference-old--new-paths)
- Ask in #documentation channel

## Timeline

- Oct 29: Migration complete
- Oct 30-31: Link updates and verification
- Nov 1: Old structure archived
```

---

## Support

### Questions?

- Check this migration guide first
- Review the [complete reorganization report](documentation-reorganization.md)
- Ask in #documentation channel
- Open an issue: [GitHub Issues](https://github.com/your-org/ai-shell/issues)

### Feedback

We want to hear from you:
- What's working well?
- What's confusing?
- What's missing?

Provide feedback:
- GitHub Discussions
- #documentation channel
- documentation-feedback@ai-shell.dev

---

**Last Updated:** October 29, 2025
**Next Review:** November 29, 2025
