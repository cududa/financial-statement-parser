#!/usr/bin/env python3
"""Test script for BBVA statement parser"""

import sys
from pathlib import Path

# Add parent directory to Python path
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from src.pdf_ingester import PDFIngester
from src.parsers import BBVAStatementParser

def test_bbva_parser(pdf_path: str):
    """Test BBVA parser on a PDF file"""
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        return None

    print(f"Testing file: {pdf_file.name}")
    print("=" * 80)

    # Initialize components
    ingester = PDFIngester()
    parser = BBVAStatementParser()

    # Extract text
    print("\n📄 Extracting text from PDF...")
    pages_text = ingester.extract_text_content(pdf_file)
    full_text = ingester.handle_multi_page_documents(pages_text)

    # Test pattern detection
    print("\n🔍 Testing statement type detection...")
    statement_type = ingester.identify_statement_type(pages_text)
    print(f"Detected type: {statement_type}")

    if statement_type != 'BBVA_LEGACY':
        print(f"⚠️  WARNING: Expected 'BBVA_LEGACY', got '{statement_type}'")

    # Parse account info
    print("\n📋 Parsing account information...")
    summary = parser.parse_account_info(full_text)

    if summary:
        print(f"✅ Account Number: {summary.account_number}")
        print(f"✅ Statement Period: {summary.statement_period_start} to {summary.statement_period_end}")
        print(f"   Total Pages: {summary.total_pages}")
        print(f"   Total Deposits: ${summary.total_deposits:.2f} ({summary.deposit_count} transactions)")
        print(f"   Total Withdrawals: ${summary.total_withdrawals:.2f} ({summary.withdrawal_count} transactions)")
    else:
        print("❌ FAILED to parse account info")
        return None

    # Parse transactions
    print("\n💰 Parsing transactions...")
    transactions = parser.extract_transaction_data(full_text)
    print(f"✅ Transactions found: {len(transactions)}")

    if not transactions:
        print("❌ No transactions found!")
        return None

    # Show first 3 transactions
    print("\n" + "=" * 80)
    print("=== FIRST 3 TRANSACTIONS ===")
    print("=" * 80)

    for i, txn in enumerate(transactions[:3], 1):
        print(f"\n{i}. Date: {txn.date}/{txn.year}")
        print(f"   Amount: ${txn.amount:.2f}")
        print(f"   Type: {txn.transaction_type}")
        print(f"   Card: {txn.card_last_four or 'N/A'}")
        print(f"   Description: {txn.description}")
        print(f"   Category: {txn.category}")

    # Show last 3 transactions
    print("\n" + "=" * 80)
    print("=== LAST 3 TRANSACTIONS ===")
    print("=" * 80)

    for i, txn in enumerate(transactions[-3:], len(transactions) - 2):
        print(f"\n{i}. Date: {txn.date}/{txn.year}")
        print(f"   Amount: ${txn.amount:.2f}")
        print(f"   Type: {txn.transaction_type}")
        print(f"   Card: {txn.card_last_four or 'N/A'}")
        print(f"   Description: {txn.description}")
        print(f"   Category: {txn.category}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("=== STATISTICS ===")
    print("=" * 80)

    total_debit = sum(t.amount for t in transactions if t.transaction_type == 'DEBIT')
    total_credit = sum(t.amount for t in transactions if t.transaction_type == 'CREDIT')
    debit_count = sum(1 for t in transactions if t.transaction_type == 'DEBIT')
    credit_count = sum(1 for t in transactions if t.transaction_type == 'CREDIT')

    print(f"Total Transactions: {len(transactions)}")
    print(f"DEBIT Transactions: {debit_count} (${total_debit:.2f})")
    print(f"CREDIT Transactions: {credit_count} (${total_credit:.2f})")

    # Check for cards
    cards = set(t.card_last_four for t in transactions if t.card_last_four)
    if cards:
        print(f"Card Numbers Found: {', '.join(sorted(cards))}")
    else:
        print("⚠️  No card numbers found")

    # Check for footer contamination
    print("\n🔍 Checking for footer contamination...")
    footer_keywords = ['BBVA USA', 'Member FDIC', 'How to Balance', 'Daily Balance Detail']
    contaminated = []

    for txn in transactions:
        for keyword in footer_keywords:
            if keyword.lower() in txn.description.lower():
                contaminated.append((txn.description[:100], keyword))

    if contaminated:
        print(f"⚠️  WARNING: Found {len(contaminated)} transactions with footer text:")
        for desc, keyword in contaminated[:3]:
            print(f"   - '{desc}...' contains '{keyword}'")
    else:
        print("✅ No footer contamination detected")

    return {
        'statement_type': statement_type,
        'summary': summary,
        'transactions': transactions
    }

if __name__ == '__main__':
    # Test the first priority file
    test_file = "PNC_Documents/Spend_x2157_Statement_October_2021(1).pdf"
    result = test_bbva_parser(test_file)

    if result:
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
