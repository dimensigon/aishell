#!/usr/bin/env python3
"""
Analyze broken links and categorize them for prioritized fixing
"""

import re
from pathlib import Path
from collections import defaultdict

AUDIT_REPORT = Path("/home/claude/AIShell/aishell/docs/reports/documentation-audit-ga-release.md")

def analyze_broken_links():
    """Categorize broken links by type"""

    categories = {
        'placeholder': [],  # Links like [text](link)
        'github_actions': [],  # GitHub Actions badges/links
        'missing_files': defaultdict(list),  # Files that don't exist
        'broken_anchors': [],  # Invalid anchor references
        'wrong_paths': [],  # Path resolution issues
    }

    with open(AUDIT_REPORT, 'r') as f:
        content = f.read()

    # Parse broken links
    current_file = None
    for line in content.split('\n'):
        # Track current source file
        if line.startswith('### `') and line.endswith('`'):
            current_file = line.strip('### `')

        # Parse error lines
        if '**Error**:' in line:
            error_match = re.search(r'\*\*Error\*\*: (.+)', line)
            if error_match:
                error_msg = error_match.group(1)

                # Get link from previous line
                prev_lines = content.split('\n')
                idx = prev_lines.index(line)
                if idx > 0:
                    link_line = prev_lines[idx - 1]
                    link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', link_line)

                    if link_match:
                        link_text = link_match.group(1)
                        link_url = link_match.group(2)
                        line_num_match = re.search(r'\*\*Line (\d+)\*\*:', link_line)
                        line_num = line_num_match.group(1) if line_num_match else '?'

                        entry = {
                            'file': current_file,
                            'line': line_num,
                            'text': link_text,
                            'url': link_url,
                            'error': error_msg
                        }

                        # Categorize
                        if link_url == 'link' or link_url.startswith('link'):
                            categories['placeholder'].append(entry)
                        elif 'actions/workflows' in link_url or '/actions' in link_url or '/issues' in link_url:
                            categories['github_actions'].append(entry)
                        elif 'Anchor #' in error_msg:
                            categories['broken_anchors'].append(entry)
                        elif 'File not found' in error_msg:
                            # Extract missing file
                            file_match = re.search(r'File not found: (.+)', error_msg)
                            if file_match:
                                missing_file = file_match.group(1)
                                categories['missing_files'][missing_file].append(entry)
                        else:
                            categories['wrong_paths'].append(entry)

    return categories

def print_analysis(categories):
    """Print categorized analysis"""

    print("=" * 80)
    print("BROKEN LINKS ANALYSIS - CATEGORIZED")
    print("=" * 80)
    print()

    # Placeholder links
    print(f"1. PLACEHOLDER LINKS: {len(categories['placeholder'])} instances")
    print("   Pattern: [text](link) or [text](link1.md)")
    print("   Fix: Replace with actual URLs or remove")
    print()
    if categories['placeholder']:
        print("   Top 10 files with placeholder links:")
        file_counts = defaultdict(int)
        for entry in categories['placeholder']:
            file_counts[entry['file']] += 1
        for file, count in sorted(file_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"   - {file}: {count} placeholder(s)")
    print()
    print("-" * 80)
    print()

    # GitHub Actions
    print(f"2. GITHUB ACTIONS LINKS: {len(categories['github_actions'])} instances")
    print("   Pattern: ../../actions/workflows/*.yml or /actions")
    print("   Fix: These are expected to fail locally (GitHub-specific)")
    print("   Action: Add note in docs or use absolute GitHub URLs")
    print()
    print("-" * 80)
    print()

    # Broken anchors
    print(f"3. BROKEN ANCHOR LINKS: {len(categories['broken_anchors'])} instances")
    print("   Pattern: [text](#section-name) where anchor doesn't exist")
    print("   Fix: Match header text exactly (lowercase, dashes)")
    print()
    if categories['broken_anchors']:
        print("   Top 10 files with broken anchors:")
        file_counts = defaultdict(int)
        for entry in categories['broken_anchors']:
            file_counts[entry['file']] += 1
        for file, count in sorted(file_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"   - {file}: {count} broken anchor(s)")
    print()
    print("-" * 80)
    print()

    # Missing files
    print(f"4. MISSING FILES: {len(categories['missing_files'])} unique files")
    print("   Pattern: Links to files that don't exist")
    print("   Fix: Create files or remove links")
    print()
    print("   Top 20 most referenced missing files:")
    sorted_missing = sorted(categories['missing_files'].items(), key=lambda x: -len(x[1]))
    for missing_file, entries in sorted_missing[:20]:
        print(f"   - {missing_file}")
        print(f"     Referenced {len(entries)} time(s) from:")
        for entry in entries[:3]:  # Show first 3 references
            print(f"       * {entry['file']} (line {entry['line']})")
        if len(entries) > 3:
            print(f"       * ... and {len(entries) - 3} more")
    print()
    print("-" * 80)
    print()

    # Summary
    total = (len(categories['placeholder']) +
             len(categories['github_actions']) +
             len(categories['broken_anchors']) +
             sum(len(v) for v in categories['missing_files'].values()))

    print("SUMMARY")
    print(f"Total broken links analyzed: {total}")
    print()
    print("Priority for fixing:")
    print("  HIGH:   Placeholder links + Missing critical files")
    print("  MEDIUM: Broken anchors + Common missing files")
    print("  LOW:    GitHub Actions links (expected failures)")
    print()

if __name__ == "__main__":
    categories = analyze_broken_links()
    print_analysis(categories)

    # Save categorized data
    import json
    output_file = Path("/home/claude/AIShell/aishell/docs/reports/broken-links-categorized.json")

    # Convert to serializable format
    serializable = {
        'placeholder': categories['placeholder'],
        'github_actions': categories['github_actions'],
        'broken_anchors': categories['broken_anchors'],
        'missing_files': {k: v for k, v in categories['missing_files'].items()},
    }

    with open(output_file, 'w') as f:
        json.dump(serializable, f, indent=2)

    print(f"✅ Categorized data saved to: {output_file}")
