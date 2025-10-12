#!/bin/bash
# Validate GitHub Actions Workflows
# Usage: .github/scripts/validate-workflows.sh

set -e

echo "🔍 Validating GitHub Actions Workflows..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter
ERRORS=0
WARNINGS=0

# Check if GitHub CLI is installed
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✓${NC} GitHub CLI installed"
else
    echo -e "${YELLOW}⚠${NC} GitHub CLI not installed (optional for validation)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check if act is installed
if command -v act &> /dev/null; then
    echo -e "${GREEN}✓${NC} act (GitHub Actions local runner) installed"
else
    echo -e "${YELLOW}⚠${NC} act not installed (optional for local testing)"
    echo "   Install: brew install act"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "📁 Checking workflow files..."

# List of expected workflow files
WORKFLOWS=(
    "test.yml"
    "coverage.yml"
    "lint.yml"
    "security.yml"
    "release.yml"
)

for workflow in "${WORKFLOWS[@]}"; do
    if [ -f ".github/workflows/$workflow" ]; then
        echo -e "${GREEN}✓${NC} $workflow exists"

        # Validate YAML syntax
        if command -v yamllint &> /dev/null; then
            if yamllint -d relaxed ".github/workflows/$workflow" &> /dev/null; then
                echo -e "  ${GREEN}✓${NC} Valid YAML syntax"
            else
                echo -e "  ${RED}✗${NC} Invalid YAML syntax"
                ERRORS=$((ERRORS + 1))
            fi
        fi
    else
        echo -e "${RED}✗${NC} $workflow missing"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "📋 Checking supporting files..."

# Check supporting files
FILES=(
    ".github/dependabot.yml"
    ".github/CODEOWNERS"
    ".github/pull_request_template.md"
    ".github/ISSUE_TEMPLATE/bug_report.md"
    ".github/ISSUE_TEMPLATE/feature_request.md"
    "docs/CI_CD_GUIDE.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file exists"
    else
        echo -e "${RED}✗${NC} $file missing"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "🔐 Checking required Python packages..."

# Check if required packages are in pyproject.toml or requirements
if [ -f "pyproject.toml" ]; then
    echo -e "${GREEN}✓${NC} pyproject.toml exists"

    # Check for dev dependencies
    PACKAGES=(
        "pytest"
        "pytest-cov"
        "black"
        "isort"
        "mypy"
        "pylint"
        "ruff"
        "bandit"
        "safety"
    )

    for pkg in "${PACKAGES[@]}"; do
        if grep -q "$pkg" pyproject.toml; then
            echo -e "  ${GREEN}✓${NC} $pkg configured"
        else
            echo -e "  ${YELLOW}⚠${NC} $pkg not found in pyproject.toml"
            WARNINGS=$((WARNINGS + 1))
        fi
    done
else
    echo -e "${RED}✗${NC} pyproject.toml missing"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "🧪 Testing local workflow execution..."

# Try to list workflows with act (if installed)
if command -v act &> /dev/null; then
    echo "Available workflows:"
    act -l 2>/dev/null || echo -e "${YELLOW}⚠${NC} Could not list workflows"
fi

echo ""
echo "📊 Validation Summary"
echo "━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All critical checks passed!"
else
    echo -e "${RED}✗${NC} $ERRORS error(s) found"
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} $WARNINGS warning(s) found"
fi

echo ""
echo "📚 Next Steps:"
echo "1. Configure secrets in GitHub repository settings"
echo "2. Enable GitHub Actions in repository settings"
echo "3. Set up branch protection rules"
echo "4. Create initial PR to test workflows"
echo "5. Review CI/CD Guide: docs/CI_CD_GUIDE.md"

echo ""
echo "🎯 Quick Commands:"
echo "  Test workflows locally:  act push"
echo "  Run specific workflow:   act push -W .github/workflows/test.yml"
echo "  List all workflows:      act -l"
echo "  GitHub Actions docs:     https://docs.github.com/en/actions"

exit $ERRORS
