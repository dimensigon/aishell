#!/bin/bash
# Version Consistency Validation Script
# Checks that all documentation references the correct version
# Usage: ./scripts/check-version-consistency.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Expected version from package.json
EXPECTED_VERSION=$(grep '"version"' package.json | head -1 | sed 's/.*"version": "\(.*\)".*/\1/')

if [ -z "$EXPECTED_VERSION" ]; then
    echo -e "${RED}❌ Could not read version from package.json${NC}"
    exit 2
fi

echo "=================================================="
echo "AI-Shell Version Consistency Check"
echo "=================================================="
echo ""
echo "Expected Version: ${EXPECTED_VERSION}"
echo ""

# Track errors
ERRORS=0
WARNINGS=0

# Check 1: Validate package.json version
echo -e "${GREEN}✓${NC} package.json version: ${EXPECTED_VERSION}"

# Check 2: Check active documentation (excluding archives, roadmap, changelogs)
echo ""
echo "Checking active documentation..."

# Find all version references in active docs (excluding correct version and library versions)
WRONG_REFS=$(grep -r "\*\*.*Version\*\*.*[0-9]\+\.[0-9]\+\.[0-9]\+" docs/ --include="*.md" 2>/dev/null \
    | grep -v "archive/" \
    | grep -v "CHANGELOG" \
    | grep -v "ROADMAP" \
    | grep -v "FEATURE" \
    | grep -v "PENDING" \
    | grep -v "${EXPECTED_VERSION}" \
    | grep -v "FAISS" \
    | grep -v "Node.js" \
    | grep -v "npm" \
    | grep -v "Python" \
    | grep -v "Docker" \
    | grep -v "Current Version:" \
    | grep -v "Fixed Version:" \
    | grep -v "Version Before:" \
    | grep -v "Version After:" \
    | grep -v "## Version" \
    || true)

if [ -n "$WRONG_REFS" ]; then
    echo -e "${RED}❌ Found incorrect version references in active docs:${NC}"
    echo "$WRONG_REFS" | head -10
    if [ $(echo "$WRONG_REFS" | wc -l) -gt 10 ]; then
        echo "... and $(($(echo "$WRONG_REFS" | wc -l) - 10)) more"
    fi
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓${NC} All active documentation versions correct"
fi

# Check 3: Verify critical files
echo ""
echo "Checking critical files..."

critical_files=(
    "docs/README.md"
    "docs/guides/USER_GUIDE.md"
    "docs/INSTALLATION.md"
    "RELEASE-NOTES-v${EXPECTED_VERSION}.md"
)

for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        if grep -q "Version.*${EXPECTED_VERSION}\|version.*${EXPECTED_VERSION}" "$file" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $file"
        else
            # Check if file should have version
            if grep -q "Version.*[0-9]\+\.[0-9]\+\.[0-9]\+" "$file" 2>/dev/null; then
                echo -e "${RED}❌${NC} $file - has wrong version"
                ERRORS=$((ERRORS + 1))
            else
                echo -e "${YELLOW}⚠${NC} $file - no version found (may be ok)"
                WARNINGS=$((WARNINGS + 1))
            fi
        fi
    else
        echo -e "${YELLOW}⚠${NC} $file - not found"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# Check 4: Find v2.0.0 or v1.2.0 references in active docs
echo ""
echo "Checking for outdated version references..."

OLD_V2_REFS=$(grep -rn "v2\.0\.0\|Version.*2\.0\.0" docs/ --include="*.md" 2>/dev/null \
    | grep -v "archive/" \
    | grep -v "ROADMAP" \
    | grep -v "FEATURE" \
    | grep -v "PENDING" \
    | grep -v "CHANGELOG" \
    || true)

OLD_V12_REFS=$(grep -rn "v1\.2\.0\|Version.*1\.2\.0" docs/ --include="*.md" 2>/dev/null \
    | grep -v "archive/" \
    | grep -v "ROADMAP" \
    | grep -v "FEATURE" \
    | grep -v "PENDING" \
    | grep -v "CHANGELOG" \
    || true)

if [ -n "$OLD_V2_REFS" ]; then
    echo -e "${YELLOW}⚠${NC} Found v2.0.0 references in active docs (may be roadmap):"
    echo "$OLD_V2_REFS" | head -5
    if [ $(echo "$OLD_V2_REFS" | wc -l) -gt 5 ]; then
        echo "... and $(($(echo "$OLD_V2_REFS" | wc -l) - 5)) more"
    fi
    WARNINGS=$((WARNINGS + 1))
fi

if [ -n "$OLD_V12_REFS" ]; then
    echo -e "${YELLOW}⚠${NC} Found v1.2.0 references in active docs (may be roadmap):"
    echo "$OLD_V12_REFS" | head -5
    if [ $(echo "$OLD_V12_REFS" | wc -l) -gt 5 ]; then
        echo "... and $(($(echo "$OLD_V12_REFS" | wc -l) - 5)) more"
    fi
    WARNINGS=$((WARNINGS + 1))
fi

# Check 5: Docker configuration
echo ""
echo "Checking Docker configuration..."

if [ -f "Dockerfile" ]; then
    if grep -q "version=\"${EXPECTED_VERSION}\"" Dockerfile 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Dockerfile version correct"
    else
        echo -e "${YELLOW}⚠${NC} Dockerfile version may need update"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

if [ -f "docker-compose.yml" ]; then
    if grep -q "image:.*:${EXPECTED_VERSION}" docker-compose.yml 2>/dev/null; then
        echo -e "${GREEN}✓${NC} docker-compose.yml version correct"
    else
        echo -e "${YELLOW}⚠${NC} docker-compose.yml version may need update"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check 6: Archive files (should NOT be changed)
echo ""
echo "Checking archive preservation..."

ARCHIVE_COUNT=$(find docs/archive -name "*.md" 2>/dev/null | wc -l)
if [ "$ARCHIVE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Archive files preserved ($ARCHIVE_COUNT files)"
else
    echo -e "${YELLOW}⚠${NC} No archive files found (may be ok for new project)"
fi

# Summary
echo ""
echo "=================================================="
echo "Summary"
echo "=================================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ PASS - Version consistency validated${NC}"
    echo ""
    echo "All checks passed:"
    echo "  ✓ package.json version: ${EXPECTED_VERSION}"
    echo "  ✓ Active documentation correct"
    echo "  ✓ Critical files verified"
    echo "  ✓ No outdated references"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ PASS WITH WARNINGS${NC}"
    echo ""
    echo "Version is consistent but there are $WARNINGS warnings."
    echo "Review the output above for details."
    exit 0
else
    echo -e "${RED}❌ FAIL - Version inconsistencies found${NC}"
    echo ""
    echo "Found $ERRORS error(s) and $WARNINGS warning(s)."
    echo ""
    echo "To fix:"
    echo "  1. Review the errors above"
    echo "  2. Update incorrect version references to ${EXPECTED_VERSION}"
    echo "  3. Run this script again"
    echo ""
    echo "Common fixes:"
    echo "  sed -i 's/Version: 2\\.0\\.0/Version: ${EXPECTED_VERSION}/g' docs/guides/*.md"
    echo "  sed -i 's/version=\"2\\.0\\.0\"/version=\"${EXPECTED_VERSION}\"/g' Dockerfile"
    exit 1
fi
