#!/usr/bin/env python3
"""Test stop pattern matching"""

import re
from src.parsers.bbva_patterns import BBVAPatterns

patterns = BBVAPatterns()
stop_patterns = patterns.STOP_PATTERNS

# The problematic line
lookahead = 'Ending Balance on 10/1'

# The normalization that the parser does
normalized = re.sub(r'\s+', '', lookahead.upper())

print(f"Original line: {repr(lookahead)}")
print(f"Normalized: {repr(normalized)}")
print()

print("Stop patterns being tested:")
for i, prefix in enumerate(stop_patterns[:5]):  # Show first 5
    pattern_normalized = prefix.replace(' ', '')
    matches = normalized.startswith(pattern_normalized)
    print(f"{i+1}. Pattern: {repr(prefix)}")
    print(f"   Normalized: {repr(pattern_normalized)}")
    print(f"   Matches: {matches}")
    print()

# Test the full check
should_stop = any(normalized.startswith(prefix.replace(' ', '')) for prefix in stop_patterns)
print(f"Should stop parsing: {should_stop}")
