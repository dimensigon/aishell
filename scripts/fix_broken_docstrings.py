#!/usr/bin/env python3
"""Fix broken docstrings created by the regex script."""

import re
from pathlib import Path

def fix_file(file_path: Path):
    """Fix broken docstrings in a file."""
    content = file_path.read_text()
    original = content

    # Pattern 1: Fix async def with broken docstring starting with code
    # From: async def method() -> None:\n        """\n        code...
    # To: async def method() -> None:\n        """Docstring."""\n        code...
    pattern1 = r'(async def \w+\([^)]*\)) -> None:\s*"""\s*\n\s+(await |if |return |for |while |with |try |async |loop |self\.|raise )'

    def replace1(match):
        func_sig = match.group(1)
        code_start = match.group(2)
        return f'{func_sig} -> None:\n        """Method implementation."""\n        {code_start}'

    content = re.sub(pattern1, replace1, content)

    # Pattern 2: Fix def with broken docstring
    pattern2 = r'(def \w+\([^)]*\)) -> None:\s*"""\s*\n\s+(if |return |for |while |with |try |self\.|raise )'

    def replace2(match):
        func_sig = match.group(1)
        code_start = match.group(2)
        return f'{func_sig} -> None:\n        """Method implementation."""\n        {code_start}'

    content = re.sub(pattern2, replace2, content)

    # Pattern 3: Fix class docstrings
    pattern3 = r'(class \w+[^:]*:)\s*"""\s*\n\s+([A-Z][a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+)\s*\n\s+"""\s*\n'

    def replace3(match):
        class_sig = match.group(1)
        doc_text = match.group(2)
        return f'{class_sig}\n    """{doc_text}."""\n\n'

    content = re.sub(pattern3, replace3, content)

    if content != original:
        file_path.write_text(content)
        print(f"Fixed {file_path}")
        return True
    return False

def main():
    src_dir = Path(__file__).parent.parent / "src"
    files = list(src_dir.rglob("*.py"))

    fixed = 0
    for file in files:
        if fix_file(file):
            fixed += 1

    print(f"\nFixed {fixed} files")

if __name__ == "__main__":
    main()
