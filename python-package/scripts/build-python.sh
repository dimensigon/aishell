#!/bin/bash
# Build script for ai-shell-py Python package

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}AI-Shell Python Package Builder${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Step 1: Check Python version
echo -e "${YELLOW}[1/8]${NC} Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION (>= $REQUIRED_VERSION)"
else
    echo -e "${RED}✗${NC} Python $PYTHON_VERSION is too old. Required: >= $REQUIRED_VERSION"
    exit 1
fi

# Step 2: Check if build tools are installed
echo -e "${YELLOW}[2/8]${NC} Checking build tools..."
if ! python3 -c "import build" 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} 'build' not found. Installing..."
    pip install build
fi

if ! python3 -c "import twine" 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} 'twine' not found. Installing..."
    pip install twine
fi

echo -e "${GREEN}✓${NC} Build tools installed"

# Step 3: Clean previous builds
echo -e "${YELLOW}[3/8]${NC} Cleaning previous builds..."
cd "$PACKAGE_DIR"
rm -rf build/ dist/ *.egg-info ai_shell_py.egg-info
echo -e "${GREEN}✓${NC} Clean complete"

# Step 4: Validate package structure
echo -e "${YELLOW}[4/8]${NC} Validating package structure..."
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}✗${NC} pyproject.toml not found!"
    exit 1
fi

if [ ! -f "README.md" ]; then
    echo -e "${RED}✗${NC} README.md not found!"
    exit 1
fi

if [ ! -d "ai_shell_py" ]; then
    echo -e "${RED}✗${NC} ai_shell_py/ directory not found!"
    exit 1
fi

echo -e "${GREEN}✓${NC} Package structure valid"

# Step 5: Check for LICENSE file
echo -e "${YELLOW}[5/8]${NC} Checking for LICENSE..."
if [ ! -f "LICENSE" ]; then
    echo -e "${YELLOW}⚠${NC} LICENSE file not found. Copying from parent..."
    if [ -f "../LICENSE" ]; then
        cp ../LICENSE .
        echo -e "${GREEN}✓${NC} LICENSE copied"
    else
        echo -e "${YELLOW}⚠${NC} No LICENSE file found. Create one before publishing!"
    fi
else
    echo -e "${GREEN}✓${NC} LICENSE exists"
fi

# Step 6: Build the package
echo -e "${YELLOW}[6/8]${NC} Building package..."
python3 -m build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Build successful"
else
    echo -e "${RED}✗${NC} Build failed"
    exit 1
fi

# Step 7: Verify build artifacts
echo -e "${YELLOW}[7/8]${NC} Verifying build artifacts..."
WHEEL_COUNT=$(ls -1 dist/*.whl 2>/dev/null | wc -l)
TARBALL_COUNT=$(ls -1 dist/*.tar.gz 2>/dev/null | wc -l)

if [ "$WHEEL_COUNT" -eq 0 ]; then
    echo -e "${RED}✗${NC} No wheel file generated!"
    exit 1
fi

if [ "$TARBALL_COUNT" -eq 0 ]; then
    echo -e "${RED}✗${NC} No source distribution generated!"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found $WHEEL_COUNT wheel file(s)"
echo -e "${GREEN}✓${NC} Found $TARBALL_COUNT source distribution(s)"

# Step 8: Check package with twine
echo -e "${YELLOW}[8/8]${NC} Running package checks with twine..."
python3 -m twine check dist/*

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Package checks passed"
else
    echo -e "${RED}✗${NC} Package checks failed"
    exit 1
fi

# Display build summary
echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Build Summary${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Package: ${GREEN}ai-shell-py${NC}"
echo -e "Version: ${GREEN}$(grep '^version = ' pyproject.toml | cut -d'"' -f2)${NC}"
echo -e "Artifacts:"
ls -lh dist/

echo ""
echo -e "${GREEN}✓ Build complete!${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Test on TestPyPI: ${YELLOW}./scripts/publish-python.sh --test${NC}"
echo -e "  2. Publish to PyPI: ${YELLOW}./scripts/publish-python.sh${NC}"
echo ""
