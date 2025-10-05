#!/usr/bin/env python3
"""
AI-Shell entry point script.

This script allows running AIShell without needing to use -m flag.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path to enable package imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run main using absolute import from src package
from src.main import main

if __name__ == "__main__":
    asyncio.run(main())
