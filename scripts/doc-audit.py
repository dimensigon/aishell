#!/usr/bin/env python3
"""
Documentation Audit Script for GA Release
Scans all markdown files, validates links, and generates comprehensive report
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Base directory
BASE_DIR = Path("/home/claude/AIShell/aishell")
DOCS_DIR = BASE_DIR / "docs"

class DocAudit:
    def __init__(self):
        self.all_md_files: Set[Path] = set()
        self.link_map: Dict[Path, List[Tuple[int, str, str]]] = defaultdict(list)
        self.broken_links: List[Dict] = []
        self.orphaned_files: Set[Path] = set()
        self.files_linking_to: Dict[Path, Set[Path]] = defaultdict(set)
        self.anchor_map: Dict[Path, Set[str]] = defaultdict(set)

    def find_all_markdown_files(self):
        """Find all markdown files in the project"""
        print(f"Scanning for markdown files in {BASE_DIR}...")

        # Skip node_modules and .venv
        skip_dirs = {'node_modules', '.venv', '.git', 'dist', 'build'}

        for md_file in BASE_DIR.rglob("*.md"):
            # Skip if in excluded directory
            if any(skip_dir in md_file.parts for skip_dir in skip_dirs):
                continue
            self.all_md_files.add(md_file)

        print(f"Found {len(self.all_md_files)} markdown files")

    def extract_headers(self, file_path: Path) -> Set[str]:
        """Extract all headers from a markdown file for anchor validation"""
        headers = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Match markdown headers (# Header)
                    header_match = re.match(r'^#{1,6}\s+(.+)$', line.strip())
                    if header_match:
                        header_text = header_match.group(1)
                        # Convert to anchor format (lowercase, spaces to dashes)
                        anchor = re.sub(r'[^\w\s-]', '', header_text.lower())
                        anchor = re.sub(r'[-\s]+', '-', anchor).strip('-')
                        headers.add(anchor)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

        return headers

    def extract_links(self, file_path: Path):
        """Extract all markdown links from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract headers for anchor validation
            self.anchor_map[file_path] = self.extract_headers(file_path)

            # Pattern for markdown links: [text](url)
            link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

            for line_num, line in enumerate(content.split('\n'), 1):
                for match in link_pattern.finditer(line):
                    link_text = match.group(1)
                    link_url = match.group(2)

                    # Skip external URLs
                    if link_url.startswith(('http://', 'https://', 'mailto:', 'ftp://')):
                        continue

                    self.link_map[file_path].append((line_num, link_text, link_url))

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    def validate_link(self, source_file: Path, link_url: str, line_num: int) -> Tuple[bool, str]:
        """Validate a single link"""
        # Split anchor from path
        parts = link_url.split('#', 1)
        link_path = parts[0]
        anchor = parts[1] if len(parts) > 1 else None

        # Handle empty path (anchor only in same file)
        if not link_path:
            if anchor:
                if anchor in self.anchor_map.get(source_file, set()):
                    return True, "Valid anchor in same file"
                else:
                    return False, f"Anchor #{anchor} not found in {source_file.name}"
            return True, "Empty link (current file)"

        # Resolve relative path
        source_dir = source_file.parent

        # Handle absolute paths from root
        if link_path.startswith('/'):
            target_path = BASE_DIR / link_path.lstrip('/')
        else:
            target_path = (source_dir / link_path).resolve()

        # Check if file exists
        if not target_path.exists():
            return False, f"File not found: {target_path.relative_to(BASE_DIR) if target_path.is_relative_to(BASE_DIR) else target_path}"

        # Track reverse link (who links to this file)
        if target_path in self.all_md_files:
            self.files_linking_to[target_path].add(source_file)

        # Validate anchor if present
        if anchor:
            if target_path in self.anchor_map:
                if anchor not in self.anchor_map[target_path]:
                    return False, f"Anchor #{anchor} not found in {target_path.name}"

        return True, "Valid"

    def validate_all_links(self):
        """Validate all extracted links"""
        print("\nValidating links...")

        total_links = sum(len(links) for links in self.link_map.values())
        print(f"Total links to validate: {total_links}")

        for source_file, links in self.link_map.items():
            for line_num, link_text, link_url in links:
                is_valid, message = self.validate_link(source_file, link_url, line_num)

                if not is_valid:
                    self.broken_links.append({
                        'source_file': str(source_file.relative_to(BASE_DIR)),
                        'line_number': line_num,
                        'link_text': link_text,
                        'link_url': link_url,
                        'error': message
                    })

    def find_orphaned_files(self):
        """Find documentation files that aren't linked from anywhere"""
        print("\nFinding orphaned files...")

        # Files in docs/ directory
        docs_files = {f for f in self.all_md_files if f.is_relative_to(DOCS_DIR)}

        # Exclude index files and root README
        excluded_patterns = ['README.md', 'INDEX.md', 'SUMMARY.md']

        for doc_file in docs_files:
            # Skip excluded files
            if any(pattern in doc_file.name for pattern in excluded_patterns):
                continue

            # Check if any file links to this one
            if doc_file not in self.files_linking_to:
                self.orphaned_files.add(doc_file)

    def check_critical_files(self) -> List[str]:
        """Check for missing critical documentation files"""
        critical_files = [
            'README.md',
            'CONTRIBUTING.md',
            'CHANGELOG.md',
            'LICENSE',
            'docs/ARCHITECTURE.md',
            'docs/API_REFERENCE.md',
            'docs/QUICKSTART.md',
            'docs/INSTALLATION.md',
        ]

        missing = []
        for file_path in critical_files:
            if not (BASE_DIR / file_path).exists():
                missing.append(file_path)

        return missing

    def generate_report(self) -> str:
        """Generate comprehensive audit report"""
        report_lines = [
            "# Documentation Audit Report - GA Release",
            "",
            f"**Generated:** {os.popen('date').read().strip()}",
            f"**Total Markdown Files:** {len(self.all_md_files)}",
            f"**Files with Links:** {len(self.link_map)}",
            f"**Total Links Scanned:** {sum(len(links) for links in self.link_map.values())}",
            f"**Broken Links:** {len(self.broken_links)}",
            f"**Orphaned Files:** {len(self.orphaned_files)}",
            "",
            "---",
            "",
        ]

        # Executive Summary
        report_lines.extend([
            "## Executive Summary",
            "",
            f"This audit scanned **{len(self.all_md_files)}** markdown files across the project.",
            f"Found **{len(self.broken_links)}** broken links and **{len(self.orphaned_files)}** orphaned documentation files.",
            "",
        ])

        # Broken Links Section
        if self.broken_links:
            report_lines.extend([
                "## 🔴 Broken Links",
                "",
                f"Found **{len(self.broken_links)}** broken links:",
                "",
            ])

            # Group by source file
            links_by_file = defaultdict(list)
            for link in self.broken_links:
                links_by_file[link['source_file']].append(link)

            for source_file, links in sorted(links_by_file.items()):
                report_lines.append(f"### `{source_file}`")
                report_lines.append("")
                for link in links:
                    report_lines.append(f"- **Line {link['line_number']}**: `[{link['link_text']}]({link['link_url']})`")
                    report_lines.append(f"  - **Error**: {link['error']}")
                report_lines.append("")
        else:
            report_lines.extend([
                "## ✅ Broken Links",
                "",
                "No broken links found! All internal links are valid.",
                "",
            ])

        # Orphaned Files Section
        if self.orphaned_files:
            report_lines.extend([
                "## 📄 Orphaned Files",
                "",
                f"Found **{len(self.orphaned_files)}** files not linked from anywhere:",
                "",
            ])

            for orphan in sorted(self.orphaned_files):
                rel_path = orphan.relative_to(BASE_DIR)
                report_lines.append(f"- `{rel_path}`")
            report_lines.append("")
        else:
            report_lines.extend([
                "## ✅ Orphaned Files",
                "",
                "No orphaned files found! All documentation is linked.",
                "",
            ])

        # Missing Critical Files
        missing_critical = self.check_critical_files()
        if missing_critical:
            report_lines.extend([
                "## ⚠️ Missing Critical Files",
                "",
            ])
            for missing in missing_critical:
                report_lines.append(f"- `{missing}`")
            report_lines.append("")
        else:
            report_lines.extend([
                "## ✅ Critical Files",
                "",
                "All critical documentation files present.",
                "",
            ])

        # Documentation Structure
        report_lines.extend([
            "## 📁 Documentation Structure",
            "",
            "### Main Documentation Directories",
            "",
        ])

        # Count files by directory
        dir_counts = defaultdict(int)
        for md_file in self.all_md_files:
            if md_file.is_relative_to(DOCS_DIR):
                # Get first level subdirectory
                rel_path = md_file.relative_to(DOCS_DIR)
                if len(rel_path.parts) > 1:
                    dir_counts[rel_path.parts[0]] += 1
                else:
                    dir_counts['.'] += 1

        for dir_name, count in sorted(dir_counts.items(), key=lambda x: -x[1]):
            report_lines.append(f"- `docs/{dir_name}/`: {count} files")

        report_lines.extend([
            "",
            "---",
            "",
            "## 🎯 Recommended Actions",
            "",
        ])

        priority_actions = []

        if self.broken_links:
            priority_actions.append({
                'priority': 'HIGH',
                'action': f'Fix {len(self.broken_links)} broken links',
                'impact': 'Users may encounter 404s and incomplete documentation'
            })

        if missing_critical:
            priority_actions.append({
                'priority': 'HIGH',
                'action': f'Create {len(missing_critical)} missing critical files',
                'files': missing_critical,
                'impact': 'Essential documentation missing for GA release'
            })

        if len(self.orphaned_files) > 10:
            priority_actions.append({
                'priority': 'MEDIUM',
                'action': f'Link or archive {len(self.orphaned_files)} orphaned files',
                'impact': 'Valuable documentation may be undiscoverable'
            })

        if not priority_actions:
            report_lines.append("✅ **No critical actions required!** Documentation is in good shape.")
        else:
            for i, action in enumerate(priority_actions, 1):
                report_lines.append(f"### {i}. [{action['priority']}] {action['action']}")
                report_lines.append(f"   - **Impact**: {action['impact']}")
                if 'files' in action:
                    report_lines.append(f"   - **Files**: {', '.join(action['files'])}")
                report_lines.append("")

        report_lines.extend([
            "---",
            "",
            "## 📊 Statistics",
            "",
            f"- **Total Markdown Files**: {len(self.all_md_files)}",
            f"- **Documentation Files**: {len([f for f in self.all_md_files if f.is_relative_to(DOCS_DIR)])}",
            f"- **Files with Links**: {len(self.link_map)}",
            f"- **Total Links**: {sum(len(links) for links in self.link_map.values())}",
            f"- **Valid Links**: {sum(len(links) for links in self.link_map.values()) - len(self.broken_links)}",
            f"- **Broken Links**: {len(self.broken_links)}",
            f"- **Link Success Rate**: {((sum(len(links) for links in self.link_map.values()) - len(self.broken_links)) / sum(len(links) for links in self.link_map.values()) * 100):.1f}%",
            f"- **Orphaned Files**: {len(self.orphaned_files)}",
            "",
        ])

        return '\n'.join(report_lines)

    def run_audit(self) -> str:
        """Run complete audit and return report"""
        self.find_all_markdown_files()

        print("\nExtracting links from all files...")
        for md_file in self.all_md_files:
            self.extract_links(md_file)

        self.validate_all_links()
        self.find_orphaned_files()

        return self.generate_report()

if __name__ == "__main__":
    auditor = DocAudit()
    report = auditor.run_audit()

    # Save report
    report_path = DOCS_DIR / "reports" / "documentation-audit-ga-release.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\n✅ Audit complete! Report saved to:")
    print(f"   {report_path}")
    print(f"\n📊 Summary:")
    print(f"   - Total files: {len(auditor.all_md_files)}")
    print(f"   - Broken links: {len(auditor.broken_links)}")
    print(f"   - Orphaned files: {len(auditor.orphaned_files)}")
