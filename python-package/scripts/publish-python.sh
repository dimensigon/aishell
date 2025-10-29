#!/bin/bash
# Publish script for ai-shell-py Python package to PyPI or TestPyPI

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

# Parse arguments
TEST_MODE=false
SKIP_BUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --test)
            TEST_MODE=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --test        Upload to TestPyPI instead of PyPI"
            echo "  --skip-build  Skip the build step (use existing dist/)"
            echo "  -h, --help    Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

cd "$PACKAGE_DIR"

if [ "$TEST_MODE" = true ]; then
    REPO_NAME="TestPyPI"
    REPO_URL="https://test.pypi.org/legacy/"
    PACKAGE_URL="https://test.pypi.org/project/ai-shell-py/"
else
    REPO_NAME="PyPI"
    REPO_URL="https://upload.pypi.org/legacy/"
    PACKAGE_URL="https://pypi.org/project/ai-shell-py/"
fi

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}AI-Shell Python Package Publisher${NC}"
echo -e "${BLUE}Target: ${REPO_NAME}${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Step 1: Check for twine
echo -e "${YELLOW}[1/6]${NC} Checking for twine..."
if ! python3 -c "import twine" 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} 'twine' not found. Installing..."
    pip install twine
fi
echo -e "${GREEN}✓${NC} Twine installed"

# Step 2: Build package (unless skipped)
if [ "$SKIP_BUILD" = false ]; then
    echo -e "${YELLOW}[2/6]${NC} Building package..."
    bash "$SCRIPT_DIR/build-python.sh"
else
    echo -e "${YELLOW}[2/6]${NC} Skipping build (using existing dist/)..."
fi

# Step 3: Verify dist/ exists and has files
echo -e "${YELLOW}[3/6]${NC} Verifying build artifacts..."
if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
    echo -e "${RED}✗${NC} No build artifacts found in dist/"
    echo -e "Run without --skip-build to build the package first"
    exit 1
fi

WHEEL_COUNT=$(ls -1 dist/*.whl 2>/dev/null | wc -l)
TARBALL_COUNT=$(ls -1 dist/*.tar.gz 2>/dev/null | wc -l)

echo -e "${GREEN}✓${NC} Found $WHEEL_COUNT wheel file(s)"
echo -e "${GREEN}✓${NC} Found $TARBALL_COUNT source distribution(s)"

# Step 4: Check credentials
echo -e "${YELLOW}[4/6]${NC} Checking credentials..."
if [ "$TEST_MODE" = true ]; then
    if [ -z "$TEST_PYPI_TOKEN" ]; then
        echo -e "${YELLOW}⚠${NC} TEST_PYPI_TOKEN not set in environment"
        echo -e "You'll need to enter your TestPyPI credentials manually"
    else
        echo -e "${GREEN}✓${NC} TestPyPI token found in environment"
    fi
else
    if [ -z "$PYPI_TOKEN" ]; then
        echo -e "${YELLOW}⚠${NC} PYPI_TOKEN not set in environment"
        echo -e "You'll need to enter your PyPI credentials manually"
    else
        echo -e "${GREEN}✓${NC} PyPI token found in environment"
    fi
fi

# Step 5: Confirm publication
echo -e "${YELLOW}[5/6]${NC} Ready to publish..."
echo ""
echo -e "Package: ${GREEN}ai-shell-py${NC}"
echo -e "Version: ${GREEN}$(grep '^version = ' pyproject.toml | cut -d'"' -f2)${NC}"
echo -e "Target: ${GREEN}${REPO_NAME}${NC}"
echo ""
echo -e "Files to upload:"
ls -lh dist/
echo ""

read -p "Continue with upload? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠${NC} Upload cancelled"
    exit 0
fi

# Step 6: Upload to repository
echo -e "${YELLOW}[6/6]${NC} Uploading to ${REPO_NAME}..."

if [ "$TEST_MODE" = true ]; then
    # Upload to TestPyPI
    if [ -n "$TEST_PYPI_TOKEN" ]; then
        python3 -m twine upload --repository testpypi dist/* \
            --username __token__ \
            --password "$TEST_PYPI_TOKEN"
    else
        python3 -m twine upload --repository testpypi dist/*
    fi
else
    # Upload to PyPI
    if [ -n "$PYPI_TOKEN" ]; then
        python3 -m twine upload dist/* \
            --username __token__ \
            --password "$PYPI_TOKEN"
    else
        python3 -m twine upload dist/*
    fi
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Upload successful!"
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}Publication Successful!${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    echo -e "Package URL: ${GREEN}${PACKAGE_URL}${NC}"
    echo ""
    if [ "$TEST_MODE" = true ]; then
        echo -e "To install from TestPyPI:"
        echo -e "  ${YELLOW}pip install --index-url https://test.pypi.org/simple/ ai-shell-py${NC}"
    else
        echo -e "To install:"
        echo -e "  ${YELLOW}pip install ai-shell-py${NC}"
    fi
    echo ""
    echo -e "With extras:"
    echo -e "  ${YELLOW}pip install ai-shell-py[postgresql,mysql,mongodb]${NC}"
    echo -e "  ${YELLOW}pip install ai-shell-py[all]${NC}"
    echo ""
else
    echo -e "${RED}✗${NC} Upload failed"
    exit 1
fi
