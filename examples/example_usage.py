#!/usr/bin/env python3
"""
Example usage of PNC Statement Parser
Demonstrates basic parsing with JSON categorization (recommended approach)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers import PNCStatementParser
from src.pdf_ingester import PDFIngester
from src.csv_exporter import CSVExporter
from src.data_processor import DataProcessor


def example_basic_parsing():
    """Example of basic parsing with JSON categorization"""
    print("Basic Parsing with Categorization Example")
    print("-" * 40)
    
    # Initialize components
    ingester = PDFIngester()
    parser = PNCStatementParser()  # Includes JSON categorization
    processor = DataProcessor()
    exporter = CSVExporter()
    
    # Process a PDF file
    pdf_file = Path("path/to/your/statement.pdf")
    
    if pdf_file.exists():
        # Extract text
        pages_text = ingester.extract_text_content(pdf_file)
        combined_text = ingester.handle_multi_page_documents(pages_text)
        
        # Parse transactions with categorization
        transactions = parser.extract_transaction_data(combined_text)
        statement_summary = parser.parse_account_info(combined_text)
        
        # Clean and validate data
        cleaned_transactions = processor.clean_transaction_data(transactions)
        if statement_summary:
            processor.validate_data_integrity(cleaned_transactions, statement_summary)
        
        final_transactions = processor.handle_duplicate_transactions(cleaned_transactions)
        
        # Export to CSV
        output_file = Path("output/transactions.csv")
        exporter.create_google_sheets_compatible_format(
            final_transactions, output_file, pdf_file.name
        )
        
        print(f"Extracted {len(final_transactions)} transactions")
        print(f"Categories applied from src/categories.json")
        print(f"Saved to {output_file}")
    else:
        print(f"Please provide a valid PDF file path")


def example_category_customization():
    """Example of customizing transaction categories"""
    print("\nCategory Customization Example")
    print("-" * 35)
    
    # Show how to view current categories
    import json
    categories_file = Path("src/categories.json")
    
    if categories_file.exists():
        with open(categories_file, 'r') as f:
            categories = json.load(f)
        
        print("Current categories in src/categories.json:")
        for category_name, category_data in categories.get('categories', {}).items():
            patterns = category_data.get('patterns', [])
            print(f"  {category_name}: {', '.join(patterns[:3])}{'...' if len(patterns) > 3 else ''}")
        
        print("\nTo add new categories:")
        print("1. Edit src/categories.json")
        print("2. Add your patterns under the appropriate category")
        print("3. Submit a PR to share with the community!")
        
        print("\nExample new category:")
        print("""
{
  "categories": {
    "Utilities": {
      "patterns": ["Electric Company", "Gas.*Bill", "Water.*Dept"]
    }
  }
}""")
    else:
        print("Categories file not found - it will be created with defaults")


def example_batch_processing():
    """Example of processing multiple statements"""
    print("\nBatch Processing Example")
    print("-" * 30)
    
    # Initialize components
    ingester = PDFIngester()
    parser = PNCStatementParser()
    processor = DataProcessor()
    exporter = CSVExporter()
    
    # Process all PDFs in a directory
    pdf_directory = Path("path/to/statements/")
    
    if pdf_directory.exists():
        pdf_files = list(pdf_directory.glob("*.pdf"))
        all_transactions = []
        
        for pdf_file in pdf_files:
            print(f"Processing {pdf_file.name}...")
            
            # Extract and parse
            pages_text = ingester.extract_text_content(pdf_file)
            combined_text = ingester.handle_multi_page_documents(pages_text)
            transactions = parser.extract_transaction_data(combined_text)
            
            # Clean and validate
            cleaned_transactions = processor.clean_transaction_data(transactions)
            final_transactions = processor.handle_duplicate_transactions(cleaned_transactions)
            
            all_transactions.extend(final_transactions)
        
        # Export all transactions to single CSV
        output_file = Path("output/all_transactions.csv")
        source_files = ", ".join(f.name for f in pdf_files)
        exporter.create_google_sheets_compatible_format(
            all_transactions, output_file, source_files
        )
        
        print(f"\nTotal: {len(all_transactions)} transactions from {len(pdf_files)} files")
        print(f"All transactions categorized using JSON configuration")
        print(f"Saved to {output_file}")
    else:
        print(f"Please provide a valid directory path")


if __name__ == "__main__":
    print("PNC Statement Parser - Usage Examples\n")
    
    # Run examples (uncomment to test with your PDFs)
    # example_basic_parsing()
    # example_category_customization()
    # example_batch_processing()
    
    print("\nFor command-line usage:")
    print("  python parse_statements.py --file statement.pdf --output output.csv")
    print("  python parse_statements.py --directory statements/ --output all.csv --monthly")
    print("\nFor category customization:")
    print("  Edit src/categories.json and submit a PR to share with the community!")
    print("\nSee README.md for full documentation")