#!/bin/bash

# Automated NPM publishing script for AI Shell
# Handles version bumping, changelog, git tagging, and publishing

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
BUMP_TYPE="patch"
DRY_RUN=false
SKIP_TESTS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --major)
            BUMP_TYPE="major"
            shift
            ;;
        --minor)
            BUMP_TYPE="minor"
            shift
            ;;
        --patch)
            BUMP_TYPE="patch"
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--major|--minor|--patch] [--dry-run] [--skip-tests]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🚀 AI Shell - NPM Publishing Script${NC}"
echo "===================================="
echo ""

# Get current version
CURRENT_VERSION=$(node -p "require('./package.json').version")
echo "Current version: $CURRENT_VERSION"

# Calculate new version
if [ "$BUMP_TYPE" = "major" ]; then
    NEW_VERSION=$(node -p "
        const v = '$CURRENT_VERSION'.split('.');
        \`\${parseInt(v[0])+1}.0.0\`
    ")
elif [ "$BUMP_TYPE" = "minor" ]; then
    NEW_VERSION=$(node -p "
        const v = '$CURRENT_VERSION'.split('.');
        \`\${v[0]}.\${parseInt(v[1])+1}.0\`
    ")
else
    NEW_VERSION=$(node -p "
        const v = '$CURRENT_VERSION'.split('.');
        \`\${v[0]}.\${v[1]}.\${parseInt(v[2])+1}\`
    ")
fi

echo -e "New version: ${GREEN}$NEW_VERSION${NC} ($BUMP_TYPE bump)"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
    echo ""
fi

# Check git status
echo "1. Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${RED}✗ Working directory is not clean${NC}"
    echo "Please commit or stash changes before publishing"
    exit 1
fi
echo -e "${GREEN}✓ Working directory is clean${NC}"
echo ""

# Check current branch
echo "2. Checking git branch..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    echo -e "${YELLOW}⚠ Warning: Not on main/master branch (currently on: $CURRENT_BRANCH)${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ On $CURRENT_BRANCH branch${NC}"
fi
echo ""

# Run validation
echo "3. Running pre-publish validation..."
if bash scripts/prepublish.sh; then
    echo -e "${GREEN}✓ Pre-publish validation passed${NC}"
else
    echo -e "${RED}✗ Pre-publish validation failed${NC}"
    exit 1
fi
echo ""

# Run tests (unless skipped)
if [ "$SKIP_TESTS" = false ]; then
    echo "4. Running test suite..."
    if npm test; then
        echo -e "${GREEN}✓ Tests passed${NC}"
    else
        echo -e "${RED}✗ Tests failed${NC}"
        exit 1
    fi
else
    echo "4. Skipping tests (--skip-tests flag)"
fi
echo ""

if [ "$DRY_RUN" = false ]; then
    # Update version in package.json
    echo "5. Updating package.json version..."
    npm version $NEW_VERSION --no-git-tag-version
    echo -e "${GREEN}✓ Version updated to $NEW_VERSION${NC}"
    echo ""

    # Update CHANGELOG.md
    echo "6. Updating CHANGELOG.md..."
    DATE=$(date +%Y-%m-%d)

    if [ ! -f CHANGELOG.md ]; then
        cat > CHANGELOG.md << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [$NEW_VERSION] - $DATE

### Added
- Initial release

EOF
    else
        # Insert new version section after the header
        sed -i "/^## /i\\
## [$NEW_VERSION] - $DATE\n\n### Changed\n- Version bump to $NEW_VERSION\n" CHANGELOG.md
    fi
    echo -e "${GREEN}✓ CHANGELOG.md updated${NC}"
    echo ""

    # Commit changes
    echo "7. Committing changes..."
    git add package.json CHANGELOG.md
    git commit -m "chore: release v$NEW_VERSION"
    echo -e "${GREEN}✓ Changes committed${NC}"
    echo ""

    # Create git tag
    echo "8. Creating git tag..."
    git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"
    echo -e "${GREEN}✓ Tag v$NEW_VERSION created${NC}"
    echo ""

    # Build package
    echo "9. Building package..."
    npm run build
    echo -e "${GREEN}✓ Build complete${NC}"
    echo ""

    # Check NPM authentication
    echo "10. Checking NPM authentication..."
    if npm whoami > /dev/null 2>&1; then
        NPM_USER=$(npm whoami)
        echo -e "${GREEN}✓ Logged in as: $NPM_USER${NC}"
    else
        echo -e "${RED}✗ Not logged in to NPM${NC}"
        echo "Please run: npm login"
        exit 1
    fi
    echo ""

    # Publish to NPM
    echo "11. Publishing to NPM..."
    read -p "Publish v$NEW_VERSION to NPM? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        npm publish --access public
        echo -e "${GREEN}✓ Published to NPM successfully!${NC}"
        echo ""

        # Push to git
        echo "12. Pushing to git repository..."
        git push && git push --tags
        echo -e "${GREEN}✓ Pushed to git repository${NC}"
        echo ""

        echo "===================================="
        echo -e "${GREEN}🎉 Successfully published v$NEW_VERSION!${NC}"
        echo ""
        echo "View on NPM: https://www.npmjs.com/package/ai-shell"
        echo "Install with: npm install -g ai-shell"
    else
        echo ""
        echo -e "${YELLOW}Publishing cancelled${NC}"
        echo "To publish manually, run: npm publish"
        echo "To push git changes: git push && git push --tags"
    fi
else
    echo "5-12. [DRY RUN] Would perform:"
    echo "  - Update package.json to $NEW_VERSION"
    echo "  - Update CHANGELOG.md"
    echo "  - Commit changes"
    echo "  - Create tag v$NEW_VERSION"
    echo "  - Build package"
    echo "  - Publish to NPM"
    echo "  - Push to git repository"
fi

echo ""
echo "===================================="
echo -e "${GREEN}Done!${NC}"
