#!/usr/bin/env python3
"""
Basic functionality test for PNC Statement Parser.
Tests core modules without requiring actual PDF files.
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Add parent directory to Python path
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from src.models import Transaction, StatementSummary
from src.parsers import PNCStatementParser
from src.data_processor import DataProcessor
from src.csv_exporter import CSVExporter


def test_transaction_model():
    """Test Transaction dataclass functionality"""
    print("Testing Transaction model...")
    
    transaction = Transaction(
        date="12/08",
        year=2022,
        month=12,
        amount=Decimal("38.87"),
        transaction_type="CREDIT",
        description="Debit Card Credit ACME Store 8001234567 SEATTLE WA",
        merchant="ACME Store",
        card_last_four="1234",
        category="Refund",
        raw_lines=["12/08    38.87    Debit Card Credit ACME Store 8001234567", "                  SEATTLE WA"],
        page_number=1
    )
    
    # Test full_date property
    expected_date = datetime(2022, 12, 8)
    assert transaction.full_date == expected_date, f"Expected {expected_date}, got {transaction.full_date}"
    
    # Test signed_amount property
    assert transaction.signed_amount == Decimal("38.87"), f"Expected 38.87, got {transaction.signed_amount}"
    
    print("✓ Transaction model tests passed")


def test_parser_patterns():
    """Test PNCStatementParser regex patterns"""
    print("Testing parser patterns...")
    
    parser = PNCStatementParser()
    
    # Test date pattern via the patterns object
    test_line = "12/08    38.87    Debit Card Credit"
    date_match = parser.patterns.DATE_PATTERN.match(test_line)
    assert date_match is not None, "Date pattern should match"
    assert date_match.group(1) == "12/08", f"Expected '12/08', got '{date_match.group(1)}'"
    
    # Test amount pattern
    amount_match = parser.patterns.AMOUNT_PATTERN.search(test_line)
    assert amount_match is not None, "Amount pattern should match"
    assert amount_match.group(1) == "38.87", f"Expected '38.87', got '{amount_match.group(1)}'"
    
    # Test large amount with comma
    large_amount_line = "12/30    6,250.00 Direct Deposit"
    large_amount_match = parser.patterns.AMOUNT_PATTERN.search(large_amount_line)
    assert large_amount_match is not None, "Large amount pattern should match"
    assert large_amount_match.group(1) == "6,250.00", f"Expected '6,250.00', got '{large_amount_match.group(1)}'"
    
    print("✓ Parser pattern tests passed")


def test_data_processor():
    """Test DataProcessor functionality"""
    print("Testing data processor...")
    
    processor = DataProcessor()
    
    # Create test transactions
    transactions = [
        Transaction(
            date="12/08", year=2022, month=12, amount=Decimal("38.87"),
            transaction_type="CREDIT", description="  Test  Description  ",
            merchant="Test Merchant", card_last_four="3767", category="Shopping",
            raw_lines=["test"], page_number=1
        ),
        Transaction(
            date="12/09", year=2022, month=12, amount=Decimal("25.00"),
            transaction_type="DEBIT", description="Another Transaction",
            merchant="Another Merchant", card_last_four="3767", category="Food",
            raw_lines=["test"], page_number=1
        )
    ]
    
    # Test cleaning
    cleaned = processor.clean_transaction_data(transactions)
    assert len(cleaned) == 2, f"Expected 2 transactions, got {len(cleaned)}"
    assert cleaned[0].description == "Test Description", f"Description not cleaned properly: '{cleaned[0].description}'"
    
    print("✓ Data processor tests passed")


def test_csv_exporter():
    """Test CSVExporter formatting"""
    print("Testing CSV exporter...")
    
    exporter = CSVExporter()
    
    # Create test transactions
    transactions = [
        Transaction(
            date="12/08", year=2022, month=12, amount=Decimal("38.87"),
            transaction_type="CREDIT", description="Test Credit",
            merchant="Test Merchant", card_last_four="3767", category="Income",
            raw_lines=["test"], page_number=1
        ),
        Transaction(
            date="12/09", year=2022, month=12, amount=Decimal("25.00"),
            transaction_type="DEBIT", description="Test Debit",
            merchant="Another Merchant", card_last_four="3767", category="Shopping",
            raw_lines=["test"], page_number=1
        )
    ]
    
    # Test formatting
    formatted = exporter.format_data_for_export(transactions, "test.pdf")
    assert len(formatted) == 2, f"Expected 2 formatted transactions, got {len(formatted)}"
    
    # Check credit amount is positive
    credit_row = next(row for row in formatted if row['Type'] == 'CREDIT')
    assert credit_row['Amount'] == 38.87, f"Expected 38.87, got {credit_row['Amount']}"
    
    # Check debit amount is negative
    debit_row = next(row for row in formatted if row['Type'] == 'DEBIT')
    assert debit_row['Amount'] == -25.00, f"Expected -25.00, got {debit_row['Amount']}"
    
    print("✓ CSV exporter tests passed")


def main():
    """Run all basic tests"""
    print("Running basic functionality tests for PNC Statement Parser\n")
    
    try:
        test_transaction_model()
        test_parser_patterns()
        test_data_processor()
        test_csv_exporter()
        
        print("\n✅ All basic tests passed! Core functionality is working.")
        print("\nNext steps:")
        print("1. Test with actual PNC PDF statements")
        print("2. Run: python parse_statements.py --file your_statement.pdf --output output.csv")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()