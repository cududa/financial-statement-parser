#!/usr/bin/env python3
"""
Detailed analysis of PNC statement structure - focuses on transaction data.
"""

import pdfplumber
import sys
from pathlib import Path
import re

def analyze_transactions(pdf_path):
    """Deep dive into transaction structure"""
    print(f"Detailed Transaction Analysis: {pdf_path}")
    print("=" * 80)
    
    with pdfplumber.open(pdf_path) as pdf:
        all_text = ""
        
        # Extract text from all pages
        for page_num, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text()
            if page_text:
                print(f"\n--- PAGE {page_num} ---")
                all_text += page_text + "\n"
                
                # Look for transaction sections on this page
                if "Activity Detail" in page_text:
                    print("Found Activity Detail section on this page")
                
                if "Deposits and Other Additions" in page_text:
                    print("Found Deposits section on this page")
                    # Extract the deposits section
                    extract_deposits_section(page_text)
                
                if "Banking/Debit Card Withdrawals" in page_text:
                    print("Found Withdrawals section on this page")
                    # Extract the withdrawals section
                    extract_withdrawals_section(page_text)

def extract_deposits_section(text):
    """Extract and analyze the deposits section"""
    print("\nDEPOSITS SECTION ANALYSIS:")
    print("-" * 40)
    
    lines = text.split('\n')
    in_deposits = False
    deposit_lines = []
    
    for line in lines:
        if "Deposits and Other Additions" in line:
            in_deposits = True
            continue
        elif in_deposits and ("Banking/Debit Card" in line or "Checks" in line or line.strip() == ""):
            if line.strip() == "":
                continue
            else:
                break
        elif in_deposits:
            deposit_lines.append(line)
    
    print(f"Found {len(deposit_lines)} lines in deposits section:")
    for i, line in enumerate(deposit_lines, 1):
        print(f"{i:2d}: '{line}'")
    
    # Try to parse individual transactions
    print("\nParsing individual deposit transactions:")
    parse_transactions(deposit_lines, "DEPOSIT")

def extract_withdrawals_section(text):
    """Extract and analyze the withdrawals section"""
    print("\nWITHDRAWALS SECTION ANALYSIS:")
    print("-" * 40)
    
    lines = text.split('\n')
    in_withdrawals = False
    withdrawal_lines = []
    
    for line in lines:
        if "Banking/Debit Card Withdrawals" in line:
            in_withdrawals = True
            continue
        elif in_withdrawals and (line.strip() == "" or "continued on next page" in line.lower()):
            if "continued on next page" in line.lower():
                break
            continue
        elif in_withdrawals:
            withdrawal_lines.append(line)
    
    print(f"Found {len(withdrawal_lines)} lines in withdrawals section:")
    for i, line in enumerate(withdrawal_lines[:10], 1):  # First 10 only
        print(f"{i:2d}: '{line}'")
    
    # Try to parse individual transactions
    print("\nParsing individual withdrawal transactions:")
    parse_transactions(withdrawal_lines[:10], "WITHDRAWAL")

def parse_transactions(lines, transaction_type):
    """Attempt to parse transaction lines"""
    print(f"\nTransaction parsing for {transaction_type}:")
    
    # Look for patterns like: MM/DD  AMOUNT  DESCRIPTION
    date_pattern = r'^(\d{1,2}/\d{1,2})\s+'
    amount_pattern = r'(\d+\.\d{2})\s+'
    
    for line in lines:
        if not line.strip():
            continue
            
        # Try to match date at start of line
        date_match = re.match(date_pattern, line.strip())
        if date_match:
            print(f"  Date found: {date_match.group(1)} | Full line: '{line.strip()}'")
            
            # Try to extract amount (look for decimal patterns)
            amounts = re.findall(r'\b\d+\.\d{2}\b', line)
            if amounts:
                print(f"    Amounts found: {amounts}")
        else:
            # Might be a continuation line or description
            if len(line.strip()) > 0:
                print(f"  Non-date line: '{line.strip()}'")

def main():
    if len(sys.argv) != 2:
        print("Usage: python detailed_analyzer.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: File {pdf_path} does not exist")
        sys.exit(1)
    
    analyze_transactions(pdf_path)

if __name__ == "__main__":
    main()