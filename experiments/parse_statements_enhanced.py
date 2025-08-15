#!/usr/bin/env python3
"""
Enhanced entry point for PNC Statement Parser.
This script provides the enhanced command-line interface with layout-aware parsing.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.enhanced_main import main

if __name__ == '__main__':
    main()