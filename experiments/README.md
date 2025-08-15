# Experiments

This directory contains experimental and deprecated parsing approaches that were tested during development.

## Deprecated: Enhanced/Coordinate-Based Parsing

The enhanced parser attempted to use layout-aware parsing with coordinate detection for more precise transaction extraction. However, it had fundamental issues:

- Coordinate-based filtering disrupted section identification
- Transaction types were incorrectly assigned (deposits as DEBIT instead of CREDIT)  
- Page ordering became scrambled due to coordinate reordering
- Overall less reliable than the basic text-based parser

**Files:**
- `enhanced_parser.py` - Layout-aware parser with coordinate detection
- `layout_analyzer.py` - PDF coordinate extraction and column detection
- `parse_statements_enhanced.py` - CLI interface for enhanced parser
- `enhanced_main.py` - Deprecated CLI with both basic and enhanced options (moved from src/)

## Current Recommendation

Use the **modular parser** (`src/parsers/`) which provides:
- **Extensible architecture**: Ready for multi-bank support
- Reliable transaction type detection (CREDIT/DEBIT)
- Proper document flow ordering
- Clean description filtering
- JSON-based categorization system
- Component separation for easy testing and maintenance
- Proven accuracy on real PNC statements

The modular parser is more maintainable, extensible, and handles all the edge cases correctly.