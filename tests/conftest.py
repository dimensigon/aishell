"""
Pytest configuration for AIShell tests.

Ensures src module is importable during test discovery and execution.
"""

import sys
from pathlib import Path

# Add project root to Python path so 'src' can be imported
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
