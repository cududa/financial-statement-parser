#!/usr/bin/env python3
"""
Debug script to examine raw PDF text extraction and understand contamination.
"""

import sys
sys.path.insert(0, 'src')

from src.pdf_ingester import PDFIngester
from pathlib import Path

def debug_pdf_extraction():
    """Examine raw PDF text extraction to understand contamination"""
    
    pdf_path = Path("PNC_Documents/2023/Spend_x2157_Statement_01_January_2023.pdf")
    
    print("🔍 DEBUGGING PDF TEXT EXTRACTION")
    print("=" * 60)
    
    ingester = PDFIngester()
    
    # Extract text from each page separately
    pages_text = ingester.extract_text_content(pdf_path)
    
    print(f"📄 Found {len(pages_text)} pages")
    
    # Focus on page 1 where we know the contamination occurs
    if pages_text:
        page1_text = pages_text[0]
        
        print("\n📖 PAGE 1 RAW TEXT (first 2000 characters):")
        print("-" * 50)
        print(page1_text[:2000])
        print("-" * 50)
        
        # Look for the specific problematic lines
        lines = page1_text.split('\n')
        
        print(f"\n🔍 ANALYZING {len(lines)} LINES FROM PAGE 1:")
        print("-" * 50)
        
        # Find lines containing Ross Beverage and Google
        for i, line in enumerate(lines):
            if 'Ross Beverage' in line or 'Google' in line or 'PIN POS' in line or 'Machine/Debit' in line:
                print(f"Line {i:3d}: '{line.strip()}'")
        
        print("\n🎯 LINES AROUND TRANSACTION AREA (lines 40-80):")
        print("-" * 50)
        for i in range(40, min(80, len(lines))):
            line = lines[i].strip()
            if line:  # Only show non-empty lines
                print(f"Line {i:3d}: '{line}'")
        
        # Look for specific patterns
        print("\n🚨 CONTAMINATION PATTERNS FOUND:")
        print("-" * 50)
        contamination_found = False
        for i, line in enumerate(lines):
            if any(pattern in line.lower() for pattern in [
                'pin pos purchases totaling',
                'machine/debit card deductions totaling',
                'there were', 'there was'
            ]):
                print(f"Line {i:3d}: '{line.strip()}'")
                contamination_found = True
        
        if not contamination_found:
            print("No obvious contamination patterns found in raw text")
        
        # Show the transaction section specifically
        print("\n💰 BANKING/DEBIT CARD SECTION:")
        print("-" * 50)
        in_section = False
        for i, line in enumerate(lines):
            if 'Banking/Debit Card Withdrawals' in line:
                in_section = True
                print(f"Line {i:3d}: '{line.strip()}' <-- SECTION START")
                continue
            elif in_section and ('Deposits' in line or 'Online and Electronic' in line):
                print(f"Line {i:3d}: '{line.strip()}' <-- SECTION END")
                break
            elif in_section:
                if line.strip():
                    print(f"Line {i:3d}: '{line.strip()}'")

if __name__ == "__main__":
    debug_pdf_extraction()