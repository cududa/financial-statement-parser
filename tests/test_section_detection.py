#!/usr/bin/env python3
"""
Regression tests for PNC section boundary detection patterns.
Ensures patterns handle PDF text extraction spacing variations.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from src.parsers.pnc_patterns import PNCPatterns


def test_deposits_section_spacing_variations():
    """Test that deposits section is detected with various spacing"""
    patterns = PNCPatterns()

    test_cases = [
        'Deposits and Other Additions',          # Normal spacing
        'Deposits  and  Other  Additions',       # Extra spaces
        'Deposits   and   Other   Additions',    # Multiple spaces
    ]

    for test in test_cases:
        match = patterns.DEPOSITS_START.search(test)
        assert match is not None, f"Failed to match deposits section: '{test}'"

    print("✓ Deposits section pattern tests passed")


def test_withdrawals_section_spacing_variations():
    """Test that withdrawals section is detected with various spacing variations

    Critical test for bug fix: PDFs sometimes extract with missing spaces
    between 'and' and 'Purchases', causing withdrawal transactions to be
    incorrectly classified as deposits.
    """
    patterns = PNCPatterns()

    test_cases = [
        'Banking/Debit Card Withdrawals and Purchases',     # Normal spacing
        'Banking/Debit Card Withdrawals andPurchases',      # Missing space before 'Purchases' (BUG CASE)
        'Banking/Debit Card WithdrawalsandPurchases',       # Missing both spaces
        'Banking/Debit Card Withdrawals  and  Purchases',   # Extra spaces
        'Banking/Debit Card Withdrawals   and   Purchases', # Multiple spaces
    ]

    for test in test_cases:
        match = patterns.WITHDRAWALS_START.search(test)
        assert match is not None, f"Failed to match withdrawals section: '{test}'"

    print("✓ Withdrawals section pattern tests passed (including bug case fix)")


def test_online_banking_section_spacing_variations():
    """Test that online banking section is detected with various spacing"""
    patterns = PNCPatterns()

    test_cases = [
        'Online and Electronic Banking Deductions',      # Normal spacing
        'Online  and  Electronic  Banking  Deductions',  # Extra spaces
        'Online   and   Electronic   Banking   Deductions', # Multiple spaces
    ]

    for test in test_cases:
        match = patterns.ONLINE_BANKING_START.search(test)
        assert match is not None, f"Failed to match online banking section: '{test}'"

    print("✓ Online banking section pattern tests passed")


def test_section_patterns_case_insensitive():
    """Test that all section patterns are case insensitive"""
    patterns = PNCPatterns()

    test_cases = [
        (patterns.DEPOSITS_START, 'DEPOSITS AND OTHER ADDITIONS'),
        (patterns.DEPOSITS_START, 'deposits and other additions'),
        (patterns.WITHDRAWALS_START, 'BANKING/DEBIT CARD WITHDRAWALS AND PURCHASES'),
        (patterns.WITHDRAWALS_START, 'banking/debit card withdrawals andpurchases'),
        (patterns.ONLINE_BANKING_START, 'ONLINE AND ELECTRONIC BANKING DEDUCTIONS'),
        (patterns.ONLINE_BANKING_START, 'online and electronic banking deductions'),
    ]

    for pattern, test_text in test_cases:
        match = pattern.search(test_text)
        assert match is not None, f"Failed case-insensitive match: '{test_text}'"

    print("✓ Section pattern case-insensitive tests passed")


def main():
    """Run all section detection tests"""
    print("Running PNC section detection pattern tests\n")

    try:
        test_deposits_section_spacing_variations()
        test_withdrawals_section_spacing_variations()
        test_online_banking_section_spacing_variations()
        test_section_patterns_case_insensitive()

        print("\n✅ All section detection tests passed!")
        print("\nThese tests ensure the parser handles PDF text extraction")
        print("spacing variations that previously caused withdrawal transactions")
        print("to be incorrectly classified as deposits.")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
