#!/bin/bash
# Version Update Script
# Automatically updates version across project
# Usage: ./scripts/update-version.sh <new-version>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version number required${NC}"
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.1"
    exit 1
fi

NEW_VERSION="$1"

# Validate version format (semver)
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$ ]]; then
    echo -e "${RED}Error: Invalid version format${NC}"
    echo "Version must follow semantic versioning: MAJOR.MINOR.PATCH"
    echo "Examples: 1.0.0, 1.0.1, 1.1.0, 2.0.0-alpha.1"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(grep '"version"' package.json | head -1 | sed 's/.*"version": "\(.*\)".*/\1/')

echo "=================================================="
echo "AI-Shell Version Update"
echo "=================================================="
echo ""
echo "Current Version: ${CURRENT_VERSION}"
echo "New Version:     ${NEW_VERSION}"
echo ""
read -p "Continue with version update? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Version update cancelled."
    exit 0
fi

echo ""
echo "Updating version across project..."
echo ""

# Track files updated
FILES_UPDATED=0

# Update package.json
echo -e "${BLUE}→${NC} Updating package.json..."
sed -i "s/\"version\": \"${CURRENT_VERSION}\"/\"version\": \"${NEW_VERSION}\"/" package.json
FILES_UPDATED=$((FILES_UPDATED + 1))
echo -e "${GREEN}✓${NC} package.json updated"

# Update documentation headers
echo ""
echo -e "${BLUE}→${NC} Updating documentation headers..."

# Update all active docs (not in archive)
for file in $(find docs -name "*.md" -not -path "*/archive/*" -not -name "CHANGELOG.md"); do
    if grep -q "Version: ${CURRENT_VERSION}\|Version:${CURRENT_VERSION}" "$file" 2>/dev/null; then
        sed -i "s/Version: ${CURRENT_VERSION}/Version: ${NEW_VERSION}/g" "$file"
        sed -i "s/Version:${CURRENT_VERSION}/Version:${NEW_VERSION}/g" "$file"
        echo -e "${GREEN}✓${NC} Updated $file"
        FILES_UPDATED=$((FILES_UPDATED + 1))
    fi
done

# Update Dockerfile
if [ -f "Dockerfile" ]; then
    echo ""
    echo -e "${BLUE}→${NC} Updating Dockerfile..."
    if grep -q "version=\"${CURRENT_VERSION}\"" Dockerfile 2>/dev/null; then
        sed -i "s/version=\"${CURRENT_VERSION}\"/version=\"${NEW_VERSION}\"/" Dockerfile
        echo -e "${GREEN}✓${NC} Dockerfile updated"
        FILES_UPDATED=$((FILES_UPDATED + 1))
    else
        echo -e "${YELLOW}⚠${NC} Dockerfile not updated (no version label found)"
    fi
fi

# Update docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    echo ""
    echo -e "${BLUE}→${NC} Updating docker-compose.yml..."
    if grep -q "image:.*:${CURRENT_VERSION}" docker-compose.yml 2>/dev/null; then
        sed -i "s/:${CURRENT_VERSION}/:${NEW_VERSION}/g" docker-compose.yml
        echo -e "${GREEN}✓${NC} docker-compose.yml updated"
        FILES_UPDATED=$((FILES_UPDATED + 1))
    else
        echo -e "${YELLOW}⚠${NC} docker-compose.yml not updated (no version tag found)"
    fi
fi

# Update Kubernetes manifests
if [ -d "k8s" ] || [ -d "kubernetes" ]; then
    echo ""
    echo -e "${BLUE}→${NC} Updating Kubernetes manifests..."

    k8s_dir="k8s"
    [ ! -d "$k8s_dir" ] && k8s_dir="kubernetes"

    for file in $(find "$k8s_dir" -name "*.yaml" -o -name "*.yml" 2>/dev/null); do
        if grep -q "version.*${CURRENT_VERSION}" "$file" 2>/dev/null; then
            sed -i "s/version: \"${CURRENT_VERSION}\"/version: \"${NEW_VERSION}\"/g" "$file"
            sed -i "s/version: ${CURRENT_VERSION}/version: ${NEW_VERSION}/g" "$file"
            sed -i "s/app.kubernetes.io\/version: \"${CURRENT_VERSION}\"/app.kubernetes.io\/version: \"${NEW_VERSION}\"/g" "$file"
            echo -e "${GREEN}✓${NC} Updated $file"
            FILES_UPDATED=$((FILES_UPDATED + 1))
        fi
    done
fi

# Update Helm charts
if [ -d "helm" ] || [ -d "charts" ]; then
    echo ""
    echo -e "${BLUE}→${NC} Updating Helm charts..."

    helm_dir="helm"
    [ ! -d "$helm_dir" ] && helm_dir="charts"

    for file in $(find "$helm_dir" -name "Chart.yaml" 2>/dev/null); do
        if grep -q "version: ${CURRENT_VERSION}\|appVersion: ${CURRENT_VERSION}" "$file" 2>/dev/null; then
            sed -i "s/version: ${CURRENT_VERSION}/version: ${NEW_VERSION}/g" "$file"
            sed -i "s/appVersion: ${CURRENT_VERSION}/appVersion: ${NEW_VERSION}/g" "$file"
            echo -e "${GREEN}✓${NC} Updated $file"
            FILES_UPDATED=$((FILES_UPDATED + 1))
        fi
    done
fi

# Update Python setup files
if [ -f "setup.py" ]; then
    echo ""
    echo -e "${BLUE}→${NC} Updating setup.py..."
    if grep -q "version='${CURRENT_VERSION}'\|version=\"${CURRENT_VERSION}\"" setup.py 2>/dev/null; then
        sed -i "s/version='${CURRENT_VERSION}'/version='${NEW_VERSION}'/g" setup.py
        sed -i "s/version=\"${CURRENT_VERSION}\"/version=\"${NEW_VERSION}\"/g" setup.py
        echo -e "${GREEN}✓${NC} setup.py updated"
        FILES_UPDATED=$((FILES_UPDATED + 1))
    fi
fi

if [ -f "pyproject.toml" ]; then
    echo ""
    echo -e "${BLUE}→${NC} Updating pyproject.toml..."
    if grep -q "version = \"${CURRENT_VERSION}\"" pyproject.toml 2>/dev/null; then
        sed -i "s/version = \"${CURRENT_VERSION}\"/version = \"${NEW_VERSION}\"/g" pyproject.toml
        echo -e "${GREEN}✓${NC} pyproject.toml updated"
        FILES_UPDATED=$((FILES_UPDATED + 1))
    fi
fi

# Create release notes file if it doesn't exist
RELEASE_NOTES="RELEASE-NOTES-v${NEW_VERSION}.md"
if [ ! -f "$RELEASE_NOTES" ]; then
    echo ""
    echo -e "${BLUE}→${NC} Creating release notes template..."

    cat > "$RELEASE_NOTES" << EOF
# AI-Shell v${NEW_VERSION} Release Notes

**Release Date:** TBD
**Version:** ${NEW_VERSION}
**Type:** $(echo "$NEW_VERSION" | grep -q "-" && echo "Pre-release" || echo "Stable Release")

---

## What's New in v${NEW_VERSION}

### Highlights

- [Add key highlights here]

---

## New Features

### 1. Feature Name

[Describe feature]

---

## Bug Fixes

### Critical Fixes

1. **Issue description**
   - Impact: [High/Medium/Low]
   - Fix: [Description]

---

## Breaking Changes ⚠️

[List any breaking changes, or write "None"]

---

## Performance Improvements

[List performance improvements]

---

## Known Issues

[List known issues]

---

## Upgrade Guide

### From v${CURRENT_VERSION}

\`\`\`bash
# Update to v${NEW_VERSION}
npm install -g ai-shell@${NEW_VERSION}

# Or using Docker
docker pull ai-shell/ai-shell:${NEW_VERSION}
\`\`\`

---

## Resources

- **Documentation:** https://docs.ai-shell.dev
- **GitHub:** https://github.com/your-org/ai-shell
- **Issues:** https://github.com/your-org/ai-shell/issues

---

**Version:** ${NEW_VERSION}
**Release Date:** TBD
**Status:** $(echo "$NEW_VERSION" | grep -q "-" && echo "Pre-release" || echo "Production")
EOF

    echo -e "${GREEN}✓${NC} Created $RELEASE_NOTES"
    echo -e "${YELLOW}⚠${NC} Please edit this file to add release details"
    FILES_UPDATED=$((FILES_UPDATED + 1))
else
    echo -e "${YELLOW}⚠${NC} $RELEASE_NOTES already exists, not overwriting"
fi

# Update CHANGELOG.md
if [ -f "CHANGELOG.md" ]; then
    echo ""
    echo -e "${BLUE}→${NC} Updating CHANGELOG.md..."

    # Create new entry at top of changelog
    DATE=$(date +%Y-%m-%d)

    # Create temp file with new entry
    cat > /tmp/changelog_new.md << EOF
## [${NEW_VERSION}] - ${DATE}

### Added
- [Add new features here]

### Changed
- [Add changes here]

### Fixed
- [Add bug fixes here]

### Security
- [Add security updates here]

---

EOF

    # Append existing changelog
    cat CHANGELOG.md >> /tmp/changelog_new.md

    # Replace changelog
    mv /tmp/changelog_new.md CHANGELOG.md

    echo -e "${GREEN}✓${NC} CHANGELOG.md updated with new entry"
    echo -e "${YELLOW}⚠${NC} Please edit CHANGELOG.md to add actual changes"
    FILES_UPDATED=$((FILES_UPDATED + 1))
fi

# Summary
echo ""
echo "=================================================="
echo "Version Update Complete"
echo "=================================================="
echo ""
echo -e "${GREEN}✓${NC} Updated ${FILES_UPDATED} file(s)"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Edit release notes: $RELEASE_NOTES"
echo "  3. Edit changelog: CHANGELOG.md"
echo "  4. Run tests: npm test"
echo "  5. Validate: ./scripts/check-version-consistency.sh"
echo "  6. Commit: git add . && git commit -m 'chore: bump version to v${NEW_VERSION}'"
echo "  7. Tag: git tag -a v${NEW_VERSION} -m 'Release version ${NEW_VERSION}'"
echo "  8. Push: git push origin main --tags"
echo ""

# Offer to run validation
read -p "Run version consistency check now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    if [ -f "./scripts/check-version-consistency.sh" ]; then
        chmod +x ./scripts/check-version-consistency.sh
        ./scripts/check-version-consistency.sh
    else
        echo -e "${YELLOW}⚠${NC} Validation script not found"
    fi
fi

echo ""
echo -e "${GREEN}✅ Version update complete!${NC}"
