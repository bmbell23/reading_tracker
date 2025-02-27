#!/usr/bin/env python3
"""
Wrapper script for backward compatibility.
The main functionality has moved to src/reading_list/cli/excel_template_cli.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from reading_list.cli.excel_template_cli import main

if __name__ == "__main__":
    exit(main())
