#!/usr/bin/env python3
"""
Main entry point for PNC Statement Parser.
This script provides the command-line interface for processing PNC bank statements.
"""

import sys
import subprocess

if __name__ == '__main__':
    # Run the main module to avoid import issues
    subprocess.run([sys.executable, "-m", "src.main"] + sys.argv[1:])