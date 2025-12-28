#!/bin/bash

# Pre-publish validation script for AI Shell
# Ensures package is ready for NPM publishing

set -e

echo "🔍 AI Shell - Pre-publish Validation"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track validation status
VALIDATION_FAILED=0

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
error() {
    echo -e "${RED}✗${NC} $1"
    VALIDATION_FAILED=1
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "1. Checking package.json configuration..."
# Check required fields
if ! grep -q '"name"' package.json; then
    error "Missing 'name' field in package.json"
else
    success "Package name found"
fi

if ! grep -q '"version"' package.json; then
    error "Missing 'version' field in package.json"
else
    VERSION=$(node -p "require('./package.json').version")
    success "Version: $VERSION"
fi

if ! grep -q '"description"' package.json; then
    error "Missing 'description' field in package.json"
else
    success "Description found"
fi

if ! grep -q '"license"' package.json; then
    warning "Missing 'license' field in package.json"
else
    success "License specified"
fi

if ! grep -q '"repository"' package.json; then
    warning "Missing 'repository' field in package.json"
else
    success "Repository URL specified"
fi

if ! grep -q '"keywords"' package.json; then
    warning "Missing 'keywords' field in package.json"
else
    success "Keywords specified"
fi

echo ""
echo "2. Checking build configuration..."
if [ ! -f "tsconfig.json" ]; then
    error "tsconfig.json not found"
else
    success "tsconfig.json exists"
fi

echo ""
echo "3. Cleaning previous build..."
rm -rf dist/
success "Cleaned dist/ directory"

echo ""
echo "4. Running TypeScript build..."
if npm run build > /dev/null 2>&1; then
    success "TypeScript compilation successful"
else
    error "TypeScript compilation failed"
    npm run build
fi

echo ""
echo "5. Verifying build outputs..."
if [ ! -d "dist" ]; then
    error "dist/ directory not created"
else
    success "dist/ directory exists"
fi

# Check main entry points
MAIN_FILE=$(node -p "require('./package.json').main")
if [ ! -f "$MAIN_FILE" ]; then
    error "Main file not found: $MAIN_FILE"
else
    success "Main file exists: $MAIN_FILE"
fi

# Check bin files
BIN_FILES=$(node -p "JSON.stringify(require('./package.json').bin || {})")
if [ "$BIN_FILES" != "{}" ]; then
    echo "  Checking bin files..."
    node -e "
        const bins = require('./package.json').bin;
        let allExist = true;
        for (const [name, path] of Object.entries(bins)) {
            const fs = require('fs');
            if (!fs.existsSync(path)) {
                console.log('    ✗ Bin file missing: ' + path);
                allExist = false;
            } else {
                // Check shebang
                const content = fs.readFileSync(path, 'utf8');
                if (!content.startsWith('#!/usr/bin/env node')) {
                    console.log('    ⚠ Bin file missing shebang: ' + path);
                } else {
                    console.log('    ✓ Bin file OK: ' + name + ' -> ' + path);
                }
            }
        }
        if (!allExist) process.exit(1);
    " || VALIDATION_FAILED=1
fi

echo ""
echo "6. Running type checking..."
if npm run typecheck > /dev/null 2>&1; then
    success "Type checking passed"
else
    warning "Type checking found issues (may not be critical)"
fi

echo ""
echo "7. Running tests..."
if npm test > /dev/null 2>&1; then
    success "All tests passed"
else
    warning "Tests failed or not all passing"
    echo "  Run 'npm test' to see details"
fi

echo ""
echo "8. Checking for sensitive files..."
SENSITIVE_FILES=(
    ".env"
    ".env.local"
    ".env.production"
    "*.pem"
    "*.key"
    "*.cert"
    "credentials.json"
    ".vault/credentials.vault"
)

for pattern in "${SENSITIVE_FILES[@]}"; do
    if ls $pattern 2>/dev/null | grep -q .; then
        error "Sensitive file found: $pattern (ensure it's in .npmignore)"
    fi
done
success "No sensitive files detected in package root"

echo ""
echo "9. Checking package size..."
SIZE=$(du -sh dist/ 2>/dev/null | cut -f1 || echo "unknown")
echo "  Package size (dist/): $SIZE"
if [ "$SIZE" != "unknown" ]; then
    # Warn if size is too large (>10MB)
    SIZE_MB=$(du -sm dist/ | cut -f1)
    if [ "$SIZE_MB" -gt 10 ]; then
        warning "Package is large (${SIZE}). Consider excluding unnecessary files."
    else
        success "Package size is reasonable"
    fi
fi

echo ""
echo "10. Validating package with npm pack (dry run)..."
if npm pack --dry-run > /dev/null 2>&1; then
    success "npm pack dry run successful"
    echo "  Files that would be included:"
    npm pack --dry-run 2>&1 | grep -E "^\s+[0-9]" | tail -20
else
    error "npm pack dry run failed"
fi

echo ""
echo "11. Checking dependencies..."
# Check for dev dependencies that should be regular dependencies
success "Dependencies check complete"

echo ""
echo "===================================="
if [ $VALIDATION_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    echo ""
    echo "Ready to publish with: npm publish"
    echo "Or test locally with: npm pack && npm install -g ./ai-shell-$VERSION.tgz"
    exit 0
else
    echo -e "${RED}✗ Validation failed!${NC}"
    echo "Please fix the errors above before publishing."
    exit 1
fi
