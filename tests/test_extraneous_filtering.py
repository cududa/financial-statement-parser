#!/usr/bin/env python3
"""
Test the modular parser's ability to filter out extraneous text.
Tests filtering of summary lines, headers, and other non-transaction content.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from src.parsers import PNCStatementParser


def test_extraneous_filtering():
    """Test that summary lines and extraneous text are properly filtered"""
    print("Testing extraneous text filtering...")
    
    parser = PNCStatementParser()
    
    # Test the exact summary lines from the screenshot
    test_lines = [
        "There were 2 Deposits and Other Additions totaling $6,288.87.",
        "There was 1 Banking Machine Withdrawal totaling $100.99.",
        "There were 8 Debit Card/Bank card PIN POS purchases totaling $210.49.",
        "There were 122 other Banking Machine/Debit Card deductions totaling $3,603.67.",
        "Date Amount Description",  # Column header
        "Activity Detail",  # Section header
        "Deposits and Other Additions",  # Section header
        "Banking/Debit Card Withdrawals and Purchases",  # Section header
        "continued on next page",  # Page continuation
        "Page 1 of 6",  # Page number
        "Virtual Wallet Spend Statement",  # Header text
        "PNC Bank",  # Bank name
        "$123.45",  # Standalone amount
        "123",  # Standalone number
        "OH",  # State abbreviation
        "Ca",  # Short location
    ]
    
    # Test each line
    for line in test_lines:
        is_extraneous = parser.transaction_parser.text_cleaner.is_extraneous_line(line)
        if is_extraneous:
            print(f"✓ Correctly filtered: '{line}'")
        else:
            print(f"❌ Failed to filter: '{line}'")
    
    # Test valid transaction lines that should NOT be filtered
    valid_lines = [
        "12/08    38.87    DebitCard CreditWalmart.Com8009666546",
        "12/30    6,250.00 DirectDeposit - Payroll",
        "12/02    24.93    3767 Debit Card Purchase Ross Beverage",
        "                  BENTONVILLE AR",  # Valid continuation
        "                  Lakewood",  # Valid location continuation
    ]
    
    print("\nTesting valid transaction lines (should NOT be filtered):")
    for line in valid_lines:
        is_extraneous = parser.transaction_parser.text_cleaner.is_extraneous_line(line)
        if not is_extraneous:
            print(f"✓ Correctly kept: '{line}'")
        else:
            print(f"❌ Incorrectly filtered: '{line}'")


def test_section_parsing():
    """Test parsing a mock section with extraneous text mixed in"""
    print("\n" + "="*60)
    print("Testing section parsing with mixed content...")
    
    parser = PNCStatementParser()
    
    # Mock section text that includes the problematic summary lines
    mock_section = """
Deposits and Other Additions
Date Amount Description
There were 2 Deposits and Other Additions totaling $6,288.87.
12/08    38.87    DebitCard CreditWalmart.Com8009666546
                  BENTONVILLE AR
12/30    6,250.00 DirectDeposit - Payroll
                  INTRVL LLC 00209104E34DE14

Banking/Debit Card Withdrawals and Purchases
Date Amount Description  
There was 1 Banking Machine Withdrawal totaling $100.99.
There were 8 Debit Card/Bank card PIN POS purchases totaling $210.49.
There were 122 other Banking Machine/Debit Card deductions totaling $3,603.67.
12/02    24.93    3767 Debit Card Purchase Ross Beverage
                  Lakewoo
12/02    22.68    3767 Recurring Debit Card Google Llc
                  Gsuite_lum
continued on next page
"""
    
    # Parse lines to see what gets filtered
    lines = mock_section.strip().split('\n')
    filtered_count = 0
    kept_count = 0
    
    print("Line-by-line filtering results:")
    for i, line in enumerate(lines):
        if line.strip():
            is_extraneous = parser.transaction_parser.text_cleaner.is_extraneous_line(line.strip())
            if is_extraneous:
                filtered_count += 1
                print(f"  {i+1:2d}. [FILTERED] {line}")
            else:
                kept_count += 1
                print(f"  {i+1:2d}. [KEPT]     {line}")
    
    print(f"\nSummary: {filtered_count} lines filtered, {kept_count} lines kept")
    print(f"Expected to filter summary lines and headers while keeping transaction data")


def main():
    """Run extraneous text filtering tests"""
    print("Testing PNC Statement Parser - Extraneous Text Filtering\n")
    
    test_extraneous_filtering()
    test_section_parsing()
    
    print("\n" + "="*60)
    print("✅ Extraneous text filtering tests completed!")
    print("\nThe parser should now correctly ignore summary lines like:")
    print("  'There were 2 Deposits and Other Additions totaling $6,288.87'")
    print("  'There was 1 Banking Machine Withdrawal totaling $100.99'")
    print("And keep actual transaction data while filtering out headers and summaries.")


if __name__ == '__main__':
    main()