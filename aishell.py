#!/usr/bin/env python3
"""
AI-Shell entry point script.

This script allows running AIShell without needing to use -m flag.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run main
from main import main

if __name__ == "__main__":
    asyncio.run(main())
