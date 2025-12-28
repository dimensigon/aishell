"""
AI-Shell Python SDK

Python SDK for AI-Shell providing database clients, MCP integration,
and AI agents for database management.
"""

__version__ = "1.0.0"
__author__ = "AIShell Contributors"
__license__ = "MIT"
__all__ = [
    "__version__",
    "database",
    "mcp_clients",
    "agents",
]

# Version tuple for programmatic version checking
VERSION = tuple(map(int, __version__.split(".")))

# Package metadata
PACKAGE_NAME = "ai-shell-py"
GITHUB_URL = "https://github.com/yourusername/AIShell"
DOCS_URL = "https://ai-shell-py.readthedocs.io"
PYPI_URL = "https://pypi.org/project/ai-shell-py/"
