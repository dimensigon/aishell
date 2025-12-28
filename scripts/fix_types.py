#!/usr/bin/env python3
"""
Automated type hint fixer for mypy strict mode compliance.
Fixes common type annotation issues across the codebase.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Common pattern fixes
FIXES = [
    # Fix: def __init__(self): -> def __init__(self) -> None:
    (r'(\s+def __init__\(self[^\)]*\)):', r'\1 -> None:'),

    # Fix: async def method(self): -> async def method(self) -> None:
    (r'(\s+async def \w+\(self[^\)]*\)):\s*"""[^"]*"""', r'\1 -> None:\n        """'),

    # Fix: def _init_database(self): -> def _init_database(self) -> None:
    (r'(\s+def _init_\w+\(self[^\)]*\)):', r'\1 -> None:'),

    # Fix: Dict -> Dict[str, Any]
    (r':\s*Dict\s*=', r': Dict[str, Any] ='),
    (r':\s*Optional\[Dict\]', r': Optional[Dict[str, Any]]'),
    (r'->\ *Dict:', r'-> Dict[str, Any]:'),

    # Fix: list -> List[str] or List[Any]
    (r':\s*list\s*=', r': List[Any] ='),
    (r'->\ *list:', r'-> List[Any]:'),
    (r':\s*tuple\s*=', r': Tuple[Any, ...] ='),
    (r'->\ *tuple:', r'-> Tuple[Any, ...]:'),

    # Fix: Callable -> Callable[..., Any]
    (r':\s*Callable\b(?!\[)', r': Callable[..., Any]'),
]

def fix_file(file_path: Path) -> Tuple[int, List[str]]:
    """
    Fix type hints in a single file.

    Returns:
        Tuple of (num_fixes, list_of_fixes)
    """
    try:
        content = file_path.read_text()
        original = content
        fixes_applied = []

        for pattern, replacement in FIXES:
            matches = len(re.findall(pattern, content))
            if matches > 0:
                content = re.sub(pattern, replacement, content)
                fixes_applied.append(f"  Applied {matches}x: {pattern[:40]}...")

        if content != original:
            file_path.write_text(content)
            return len(fixes_applied), fixes_applied

        return 0, []
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return 0, []

def main():
    """Main entry point."""
    src_dir = Path(__file__).parent.parent / "src"

    if not src_dir.exists():
        print(f"Source directory not found: {src_dir}", file=sys.stderr)
        sys.exit(1)

    python_files = list(src_dir.rglob("*.py"))
    print(f"Found {len(python_files)} Python files")

    total_fixes = 0
    files_modified = 0

    for py_file in python_files:
        num_fixes, fixes = fix_file(py_file)
        if num_fixes > 0:
            files_modified += 1
            total_fixes += num_fixes
            print(f"\n{py_file.relative_to(src_dir)}:")
            for fix in fixes:
                print(fix)

    print(f"\n{'='*60}")
    print(f"Summary: {files_modified} files modified, {total_fixes} total fixes applied")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
