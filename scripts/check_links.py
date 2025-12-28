#!/usr/bin/env python3
"""
Link Validation Script for AI-Shell Documentation
Checks all markdown files for broken links, missing references, and invalid anchors
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict

# ANSI color codes
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

class LinkValidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_dir = project_root / 'docs'
        self.missing_files = []
        self.invalid_anchors = []
        self.external_warnings = []
        self.total_files = 0
        self.total_links = 0

        # Cache for file existence and headings
        self.existing_files = set()
        self.file_headings = {}

    def scan_project_files(self):
        """Cache all existing files in the project"""
        print(f"📁 Scanning project structure...")
        for path in self.project_root.rglob('*'):
            if path.is_file():
                self.existing_files.add(path)

    def extract_headings(self, file_path: Path) -> Set[str]:
        """Extract all headings from a markdown file"""
        if file_path in self.file_headings:
            return self.file_headings[file_path]

        headings = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('#'):
                        # Extract heading text
                        heading = line.lstrip('#').strip()
                        # Convert to anchor format
                        anchor = heading.lower()
                        anchor = re.sub(r'[^\w\s-]', '', anchor)
                        anchor = re.sub(r'\s+', '-', anchor)
                        headings.add(anchor)
        except Exception as e:
            print(f"⚠️  Warning: Could not read {file_path}: {e}")

        self.file_headings[file_path] = headings
        return headings

    def resolve_link_path(self, link: str, source_file: Path) -> Tuple[Path, str]:
        """Resolve a link to an absolute path and anchor"""
        # Split link into file and anchor parts
        if '#' in link:
            file_part, anchor = link.split('#', 1)
        else:
            file_part, anchor = link, ''

        # Skip if no file part
        if not file_part:
            return source_file, anchor

        # Handle different path types
        if file_part.startswith('/'):
            # Absolute path from project root
            target_path = self.project_root / file_part.lstrip('/')
        else:
            # Relative path from source file
            target_path = (source_file.parent / file_part).resolve()

        return target_path, anchor

    def check_link(self, link: str, source_file: Path, line_num: int = 0) -> bool:
        """Check if a link is valid"""
        self.total_links += 1

        # Skip external URLs
        if link.startswith(('http://', 'https://', 'mailto:', 'tel:')):
            # Could add external URL checking here
            return True

        # Handle anchor-only links (same file)
        if link.startswith('#'):
            anchor = link[1:]
            headings = self.extract_headings(source_file)
            if anchor not in headings:
                rel_path = source_file.relative_to(self.project_root)
                self.invalid_anchors.append(f"{rel_path}:{line_num} - #{anchor}")
                return False
            return True

        # Handle file links
        target_path, anchor = self.resolve_link_path(link, source_file)

        # Check if file exists
        if not target_path.exists():
            rel_source = source_file.relative_to(self.project_root)
            self.missing_files.append(f"{rel_source}:{line_num} - {link}")
            return False

        # Check anchor if present
        if anchor:
            headings = self.extract_headings(target_path)
            if anchor not in headings:
                rel_source = source_file.relative_to(self.project_root)
                self.invalid_anchors.append(f"{rel_source}:{line_num} - {link} (anchor #{anchor} not found)")
                return False

        return True

    def scan_markdown_file(self, file_path: Path):
        """Scan a markdown file for links"""
        self.total_files += 1

        # Regex patterns for markdown links
        link_pattern = re.compile(r'\[([^\]]*)\]\(([^\)]+)\)')
        image_pattern = re.compile(r'!\[([^\]]*)\]\(([^\)]+)\)')

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Check regular links
                    for match in link_pattern.finditer(line):
                        link_text, link_url = match.groups()
                        self.check_link(link_url, file_path, line_num)

                    # Check image links
                    for match in image_pattern.finditer(line):
                        alt_text, image_url = match.groups()
                        if not image_url.startswith(('http://', 'https://')):
                            self.check_link(image_url, file_path, line_num)

        except Exception as e:
            print(f"⚠️  Error scanning {file_path}: {e}")

    def scan_all_docs(self):
        """Scan all markdown files in docs directory"""
        print(f"📄 Scanning markdown files in {self.docs_dir}...")

        # Scan all .md files in docs
        md_files = list(self.docs_dir.rglob('*.md'))

        # Also scan root README
        root_readme = self.project_root / 'README.md'
        if root_readme.exists():
            md_files.append(root_readme)

        for md_file in md_files:
            self.scan_markdown_file(md_file)

    def print_summary(self):
        """Print validation summary"""
        print()
        print("📊 Validation Summary")
        print("=" * 50)
        print(f"Total files scanned: {self.total_files}")
        print(f"Total links found: {self.total_links}")
        print()

        has_errors = bool(self.missing_files or self.invalid_anchors or self.external_warnings)

        if not has_errors:
            print(f"{GREEN}✅ No broken links found!{NC}")
        else:
            if self.missing_files:
                print(f"{RED}❌ Missing files: {len(self.missing_files)}{NC}")
            if self.invalid_anchors:
                print(f"{YELLOW}⚠️  Invalid anchors: {len(self.invalid_anchors)}{NC}")
            if self.external_warnings:
                print(f"{YELLOW}⚠️  External warnings: {len(self.external_warnings)}{NC}")

    def generate_report(self, report_path: Path):
        """Generate detailed markdown report"""
        print()
        print(f"📝 Generating detailed report: {report_path}")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Link Validation Report\n\n")
            f.write(f"**Generated:** {Path.cwd()}\n\n")

            f.write("## Summary\n\n")
            f.write(f"- **Total files scanned:** {self.total_files}\n")
            f.write(f"- **Total links found:** {self.total_links}\n")
            f.write(f"- **Missing files:** {len(self.missing_files)}\n")
            f.write(f"- **Invalid anchors:** {len(self.invalid_anchors)}\n")
            f.write(f"- **External warnings:** {len(self.external_warnings)}\n\n")

            has_errors = bool(self.missing_files or self.invalid_anchors or self.external_warnings)

            if not has_errors:
                f.write("## ✅ Status: PASS\n\n")
                f.write("All links are valid! No broken links found.\n\n")
            else:
                f.write("## ❌ Status: FAIL\n\n")
                f.write("Issues found that need attention.\n\n")

            f.write("---\n\n")

            # Missing files
            if self.missing_files:
                f.write(f"## 🔴 Missing Files ({len(self.missing_files)})\n\n")
                f.write("These links reference files that do not exist:\n\n")
                for issue in sorted(self.missing_files):
                    f.write(f"- `{issue}`\n")
                f.write("\n")

            # Invalid anchors
            if self.invalid_anchors:
                f.write(f"## 🟡 Invalid Anchors ({len(self.invalid_anchors)})\n\n")
                f.write("These links reference headings/anchors that do not exist:\n\n")
                for issue in sorted(self.invalid_anchors):
                    f.write(f"- `{issue}`\n")
                f.write("\n")

            # External warnings
            if self.external_warnings:
                f.write(f"## 🟡 External URL Issues ({len(self.external_warnings)})\n\n")
                f.write("These external URLs may have issues:\n\n")
                for issue in sorted(self.external_warnings):
                    f.write(f"- `{issue}`\n")
                f.write("\n")

            f.write("---\n\n")
            f.write("## Recommendations\n\n")

            if self.missing_files:
                f.write("### Fix Missing Files\n\n")
                f.write("1. Check if files were moved or renamed\n")
                f.write("2. Update links to point to correct locations\n")
                f.write("3. Consider creating missing documentation files\n")
                f.write("4. Remove links to intentionally deleted content\n\n")

            if self.invalid_anchors:
                f.write("### Fix Invalid Anchors\n\n")
                f.write("1. Verify heading text matches anchor reference\n")
                f.write("2. Check for case sensitivity issues\n")
                f.write("3. Update anchor links to match actual headings\n")
                f.write("4. Consider adding missing sections\n\n")

            f.write("### Prevention\n\n")
            f.write("1. Run this script before committing documentation changes\n")
            f.write("2. Add to CI/CD pipeline for automated checking\n")
            f.write("3. Use relative paths consistently\n")
            f.write("4. Keep documentation structure stable\n\n")

            f.write("---\n\n")
            f.write("**To run this check manually:**\n")
            f.write("```bash\n")
            f.write("python scripts/check_links.py\n")
            f.write("```\n\n")

            f.write("**To run in CI/CD:**\n")
            f.write("```yaml\n")
            f.write("- name: Validate documentation links\n")
            f.write("  run: python scripts/check_links.py\n")
            f.write("```\n")

        print("✅ Report generated successfully")

    def run(self) -> int:
        """Run the full validation"""
        print(f"🔍 Starting link validation...")
        print(f"Project root: {self.project_root}")
        print(f"Documentation directory: {self.docs_dir}")
        print()

        self.scan_project_files()
        self.scan_all_docs()
        self.print_summary()

        report_path = self.docs_dir / 'LINK_VALIDATION_REPORT.md'
        self.generate_report(report_path)

        print()
        has_errors = bool(self.missing_files or self.invalid_anchors)

        if has_errors:
            print(f"{RED}❌ Link validation failed. See {report_path} for details.{NC}")
            return 1
        else:
            print(f"{GREEN}✅ All links validated successfully!{NC}")
            return 0

def main():
    project_root = Path(__file__).parent.parent.resolve()
    validator = LinkValidator(project_root)
    sys.exit(validator.run())

if __name__ == '__main__':
    main()
