"""
Main entry point for running GranolaMCP as a module.

Enables execution via: python -m granola_mcp
"""

import sys
from .cli.main import main

if __name__ == '__main__':
    sys.exit(main())