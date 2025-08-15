#!/usr/bin/env python3
"""
Initial PDF analysis script for PNC statements.
This script helps us understand the structure and format of PNC bank statements.
"""

import pdfplumber
import sys
from pathlib import Path

def analyze_pdf(pdf_path):
    """Analyze a single PDF to understand its structure"""
    print(f"Analyzing: {pdf_path}")
    print("=" * 60)
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        print()
        
        # Analyze first page in detail
        page = pdf.pages[0]
        print("PAGE 1 ANALYSIS:")
        print("-" * 30)
        
        # Extract raw text
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            print(f"Total lines on page 1: {len(lines)}")
            print()
            print("First 20 lines:")
            for i, line in enumerate(lines[:20], 1):
                print(f"{i:2d}: {line}")
        
        print("\n" + "=" * 60)
        
        # Try to extract tables
        tables = page.extract_tables()
        if tables:
            print(f"Found {len(tables)} tables on page 1")
            for i, table in enumerate(tables):
                print(f"\nTable {i+1}:")
                for row in table[:5]:  # First 5 rows only
                    print(row)
        else:
            print("No tables detected on page 1")
        
        print("\n" + "=" * 60)
        
        # Look for specific patterns we saw in the image
        print("SEARCHING FOR KEY PATTERNS:")
        print("-" * 30)
        
        if text:
            # Look for date patterns
            import re
            
            # Account info
            if "Primary account number:" in text:
                print("✓ Found account number section")
            
            # Statement period
            period_match = re.search(r'For the period\s+(\d{2}/\d{2}/\d{4})\s+to\s+(\d{2}/\d{2}/\d{4})', text)
            if period_match:
                print(f"✓ Found statement period: {period_match.group(1)} to {period_match.group(2)}")
            
            # Balance summary
            if "Balance Summary" in text:
                print("✓ Found Balance Summary section")
            
            # Transaction sections
            if "Activity Detail" in text:
                print("✓ Found Activity Detail section")
                
            if "Deposits and Other Additions" in text:
                print("✓ Found Deposits and Other Additions section")
                
            if "Banking/Debit Card Withdrawals and Purchases" in text:
                print("✓ Found Banking/Debit Card Withdrawals section")

def main():
    if len(sys.argv) != 2:
        print("Usage: python pdf_analyzer.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: File {pdf_path} does not exist")
        sys.exit(1)
    
    analyze_pdf(pdf_path)

if __name__ == "__main__":
    main()