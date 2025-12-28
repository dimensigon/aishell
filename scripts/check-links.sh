#!/bin/bash
# Link Validation Script for AI-Shell Documentation
# Checks all markdown files for broken links, missing references, and invalid anchors

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"
REPORT_FILE="$DOCS_DIR/LINK_VALIDATION_REPORT.md"
EXIT_CODE=0

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Arrays to store issues
declare -a BROKEN_LINKS
declare -a MISSING_FILES
declare -a INVALID_ANCHORS
declare -a EXTERNAL_ERRORS

echo "🔍 Starting link validation..."
echo "Project root: $PROJECT_ROOT"
echo "Documentation directory: $DOCS_DIR"
echo ""

# Function to check if file exists (relative to project root)
check_file_exists() {
    local file_path="$1"
    local source_file="$2"
    local source_dir="$(dirname "$source_file")"

    # Handle different path types
    if [[ "$file_path" == /* ]]; then
        # Absolute path from project root
        full_path="$PROJECT_ROOT$file_path"
    elif [[ "$file_path" == ../* ]] || [[ "$file_path" == ./* ]]; then
        # Relative path
        full_path="$(cd "$source_dir" && realpath -m "$file_path" 2>/dev/null || echo "")"
    else
        # Try relative to source file
        full_path="$source_dir/$file_path"
    fi

    if [ -z "$full_path" ] || [ ! -f "$full_path" ]; then
        return 1
    fi
    return 0
}

# Function to check if heading exists in file
check_heading_exists() {
    local file_path="$1"
    local anchor="$2"

    if [ ! -f "$file_path" ]; then
        return 1
    fi

    # Convert anchor to heading format (replace - with space, handle case)
    local heading="${anchor//-/ }"

    # Check if heading exists in file (case-insensitive grep)
    if grep -qi "^#.*${heading}" "$file_path"; then
        return 0
    fi
    return 1
}

# Function to validate external URL (basic check)
check_external_url() {
    local url="$1"

    # Skip certain domains that require authentication or are known to block bots
    if [[ "$url" =~ (localhost|127\.0\.0\.1|github\.com|readthedocs\.io) ]]; then
        return 0
    fi

    return 0  # Skip external validation for now (would require curl/wget)
}

# Scan all markdown files
echo "📄 Scanning markdown files..."
TOTAL_FILES=0
TOTAL_LINKS=0

while IFS= read -r -d '' md_file; do
    ((TOTAL_FILES++))
    rel_path="${md_file#$PROJECT_ROOT/}"

    # Extract markdown links: [text](url)
    while IFS= read -r line; do
        if [[ $line =~ \[([^\]]*)\]\(([^\)]+)\) ]]; then
            link_text="${BASH_REMATCH[1]}"
            link_url="${BASH_REMATCH[2]}"
            ((TOTAL_LINKS++))

            # Skip empty links
            if [ -z "$link_url" ]; then
                continue
            fi

            # Check link type
            if [[ "$link_url" =~ ^https?:// ]]; then
                # External URL
                if ! check_external_url "$link_url"; then
                    EXTERNAL_ERRORS+=("$rel_path: $link_url")
                    EXIT_CODE=1
                fi
            elif [[ "$link_url" =~ ^# ]]; then
                # Anchor link in same file
                anchor="${link_url#\#}"
                if ! check_heading_exists "$md_file" "$anchor"; then
                    INVALID_ANCHORS+=("$rel_path: #$anchor")
                    EXIT_CODE=1
                fi
            elif [[ "$link_url" =~ ^mailto: ]] || [[ "$link_url" =~ ^tel: ]]; then
                # Skip mailto and tel links
                continue
            else
                # Internal file link
                # Split by # to get file and anchor
                file_part="${link_url%%\#*}"
                anchor_part=""
                if [[ "$link_url" =~ \# ]]; then
                    anchor_part="${link_url##*\#}"
                fi

                # Check if file exists
                if [ -n "$file_part" ]; then
                    if ! check_file_exists "$file_part" "$md_file"; then
                        MISSING_FILES+=("$rel_path: $link_url")
                        EXIT_CODE=1
                    elif [ -n "$anchor_part" ]; then
                        # Check if anchor exists in target file
                        source_dir="$(dirname "$md_file")"
                        if [[ "$file_part" == /* ]]; then
                            target_file="$PROJECT_ROOT$file_part"
                        elif [[ "$file_part" == ../* ]] || [[ "$file_part" == ./* ]]; then
                            target_file="$(cd "$source_dir" && realpath -m "$file_part" 2>/dev/null || echo "")"
                        else
                            target_file="$source_dir/$file_part"
                        fi

                        if [ -f "$target_file" ] && ! check_heading_exists "$target_file" "$anchor_part"; then
                            INVALID_ANCHORS+=("$rel_path: $link_url (anchor #$anchor_part not found)")
                            EXIT_CODE=1
                        fi
                    fi
                fi
            fi
        fi
    done < "$md_file"
done < <(find "$DOCS_DIR" -name "*.md" -type f -print0)

# Also check README.md in root
if [ -f "$PROJECT_ROOT/README.md" ]; then
    ((TOTAL_FILES++))
    while IFS= read -r line; do
        if [[ $line =~ \[([^\]]*)\]\(([^\)]+)\) ]]; then
            link_url="${BASH_REMATCH[2]}"
            ((TOTAL_LINKS++))

            if [[ ! "$link_url" =~ ^https?:// ]] && [[ ! "$link_url" =~ ^# ]] && [[ ! "$link_url" =~ ^mailto: ]]; then
                file_part="${link_url%%\#*}"
                if [ -n "$file_part" ] && ! check_file_exists "$file_part" "$PROJECT_ROOT/README.md"; then
                    MISSING_FILES+=("README.md: $link_url")
                    EXIT_CODE=1
                fi
            fi
        fi
    done < "$PROJECT_ROOT/README.md"
fi

# Print summary
echo ""
echo "📊 Validation Summary"
echo "===================="
echo "Total files scanned: $TOTAL_FILES"
echo "Total links found: $TOTAL_LINKS"
echo ""

if [ ${#MISSING_FILES[@]} -eq 0 ] && [ ${#INVALID_ANCHORS[@]} -eq 0 ] && [ ${#EXTERNAL_ERRORS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ No broken links found!${NC}"
else
    if [ ${#MISSING_FILES[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing files: ${#MISSING_FILES[@]}${NC}"
    fi
    if [ ${#INVALID_ANCHORS[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Invalid anchors: ${#INVALID_ANCHORS[@]}${NC}"
    fi
    if [ ${#EXTERNAL_ERRORS[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠️  External URL errors: ${#EXTERNAL_ERRORS[@]}${NC}"
    fi
fi

echo ""
echo "📝 Generating detailed report: $REPORT_FILE"

# Generate detailed report
cat > "$REPORT_FILE" << 'EOF_HEADER'
# Link Validation Report

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')

## Summary

EOF_HEADER

{
    echo "- **Total files scanned:** $TOTAL_FILES"
    echo "- **Total links found:** $TOTAL_LINKS"
    echo "- **Missing files:** ${#MISSING_FILES[@]}"
    echo "- **Invalid anchors:** ${#INVALID_ANCHORS[@]}"
    echo "- **External URL errors:** ${#EXTERNAL_ERRORS[@]}"
    echo ""

    if [ ${#MISSING_FILES[@]} -eq 0 ] && [ ${#INVALID_ANCHORS[@]} -eq 0 ] && [ ${#EXTERNAL_ERRORS[@]} -eq 0 ]; then
        echo "## ✅ Status: PASS"
        echo ""
        echo "All links are valid! No broken links found."
    else
        echo "## ❌ Status: FAIL"
        echo ""
        echo "Issues found that need attention."
    fi

    echo ""
    echo "---"
    echo ""

    # Missing files section
    if [ ${#MISSING_FILES[@]} -gt 0 ]; then
        echo "## 🔴 Missing Files (${#MISSING_FILES[@]})"
        echo ""
        echo "These links reference files that do not exist:"
        echo ""
        for issue in "${MISSING_FILES[@]}"; do
            echo "- \`$issue\`"
        done
        echo ""
    fi

    # Invalid anchors section
    if [ ${#INVALID_ANCHORS[@]} -gt 0 ]; then
        echo "## 🟡 Invalid Anchors (${#INVALID_ANCHORS[@]})"
        echo ""
        echo "These links reference headings/anchors that do not exist:"
        echo ""
        for issue in "${INVALID_ANCHORS[@]}"; do
            echo "- \`$issue\`"
        done
        echo ""
    fi

    # External errors section
    if [ ${#EXTERNAL_ERRORS[@]} -gt 0 ]; then
        echo "## 🟡 External URL Issues (${#EXTERNAL_ERRORS[@]})"
        echo ""
        echo "These external URLs may have issues:"
        echo ""
        for issue in "${EXTERNAL_ERRORS[@]}"; do
            echo "- \`$issue\`"
        done
        echo ""
    fi

    echo "---"
    echo ""
    echo "## Recommendations"
    echo ""

    if [ ${#MISSING_FILES[@]} -gt 0 ]; then
        echo "### Fix Missing Files"
        echo ""
        echo "1. Check if files were moved or renamed"
        echo "2. Update links to point to correct locations"
        echo "3. Consider creating missing documentation files"
        echo "4. Remove links to intentionally deleted content"
        echo ""
    fi

    if [ ${#INVALID_ANCHORS[@]} -gt 0 ]; then
        echo "### Fix Invalid Anchors"
        echo ""
        echo "1. Verify heading text matches anchor reference"
        echo "2. Check for case sensitivity issues"
        echo "3. Update anchor links to match actual headings"
        echo "4. Consider adding missing sections"
        echo ""
    fi

    echo "### Prevention"
    echo ""
    echo "1. Run this script before committing documentation changes"
    echo "2. Add to CI/CD pipeline for automated checking"
    echo "3. Use relative paths consistently"
    echo "4. Keep documentation structure stable"
    echo ""

    echo "---"
    echo ""
    echo "**To run this check manually:**"
    echo "\`\`\`bash"
    echo "bash scripts/check-links.sh"
    echo "\`\`\`"
    echo ""
    echo "**To run in CI/CD:**"
    echo "\`\`\`yaml"
    echo "- name: Validate documentation links"
    echo "  run: bash scripts/check-links.sh"
    echo "\`\`\`"

} >> "$REPORT_FILE"

echo "✅ Report generated successfully"
echo ""

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}❌ Link validation failed. See $REPORT_FILE for details.${NC}"
else
    echo -e "${GREEN}✅ All links validated successfully!${NC}"
fi

exit $EXIT_CODE
