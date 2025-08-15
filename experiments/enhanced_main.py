#!/usr/bin/env python3

import click
import logging
from pathlib import Path
from typing import List
import sys
import json

# Enhanced parser moved to experiments/ - now deprecated
try:
    from .pdf_ingester import PDFIngester
    from .parsers import PNCStatementParser
    from .data_processor import DataProcessor
    from .csv_exporter import CSVExporter
except ImportError:
    from pdf_ingester import PDFIngester
    from parsers import PNCStatementParser
    from data_processor import DataProcessor
    from csv_exporter import CSVExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--file', '-f', type=click.Path(exists=True, path_type=Path), 
              help='Single PDF statement file to process')
@click.option('--directory', '-d', type=click.Path(exists=True, path_type=Path),
              help='Directory containing PDF statements to process')
@click.option('--output', '-o', type=click.Path(path_type=Path), required=True,
              help='Output CSV file path')
@click.option('--enhanced', is_flag=True, default=False,
              help='[DEPRECATED] Enhanced parsing moved to experiments/ - use basic parser')
@click.option('--basic', is_flag=True, default=True,
              help='Use reliable text-based parsing with JSON categorization (recommended)')
@click.option('--monthly', is_flag=True, 
              help='Create separate CSV files for each month')
@click.option('--summary', type=click.Path(path_type=Path),
              help='Generate summary report file')
@click.option('--validation-report', type=click.Path(path_type=Path),
              help='Generate detailed validation report (JSON)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
@click.option('--validate-only', is_flag=True,
              help='Only validate files without generating output')
@click.option('--compare-methods', is_flag=True,
              help='Compare enhanced vs basic parsing methods')
def main(file, directory, output, enhanced, basic, monthly, summary, 
         validation_report, verbose, validate_only, compare_methods):
    """
    PNC Statement Parser - Convert PNC bank statement PDFs to CSV format.
    
    Uses reliable text-based parsing with JSON categorization by default.
    Enhanced coordinate-based parsing has been deprecated and moved to experiments/.
    
    Examples:
        # Basic parsing with categorization (recommended)
        python -m src.enhanced_main --file statement.pdf --output transactions.csv
        
        # Process directory with validation
        python -m src.enhanced_main --directory 2023/ --output 2023_all.csv --validation-report validation.json
    """
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if not file and not directory:
        click.echo("Error: Must specify either --file or --directory", err=True)
        sys.exit(1)
    
    if file and directory:
        click.echo("Error: Cannot specify both --file and --directory", err=True)
        sys.exit(1)
    
    # Deprecation warning for enhanced parsing
    if enhanced:
        click.echo("⚠ WARNING: Enhanced parsing has been deprecated and moved to experiments/", err=True)
        click.echo("⚠ Using basic parser instead (recommended for reliability)", err=True)
        enhanced = False
    
    try:
        # Get list of files to process
        pdf_files = []
        if file:
            pdf_files = [file]
        else:
            pdf_files = list(directory.glob("*.pdf"))
            if not pdf_files:
                click.echo(f"No PDF files found in {directory}", err=True)
                sys.exit(1)
        
        click.echo(f"Found {len(pdf_files)} PDF file(s) to process")
        
        if compare_methods:
            click.echo("⚠ WARNING: Compare methods feature deprecated - enhanced parser moved to experiments/", err=True)
            click.echo("Using basic parser only", err=True)
        
        # Always use basic parsing now (enhanced is deprecated)
        process_with_basic_method(pdf_files, output, monthly, summary, 
                                validation_report, validate_only)
        
        click.echo("\nProcessing completed successfully!")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def process_with_basic_method(pdf_files: List[Path], output: Path,
                            monthly: bool, summary_path: Path, validation_report: Path, 
                            validate_only: bool):
    """Process files with basic parser (enhanced parsing is deprecated)"""
    
    click.echo("Using reliable text-based parsing with JSON categorization...")
    
    ingester = PDFIngester()
    parser = PNCStatementParser()
    processor = DataProcessor()
    exporter = CSVExporter()
    
    all_transactions = []
    all_summaries = []
    validation_data = []
    
    for pdf_file in pdf_files:
        click.echo(f"Processing: {pdf_file.name}")
        
        # Basic parsing with categorization
        pages_text = ingester.extract_text_content(pdf_file)
        if not pages_text:
            click.echo(f"Warning: No text extracted from {pdf_file.name}", err=True)
            continue
        
        combined_text = ingester.handle_multi_page_documents(pages_text)
        transactions = parser.extract_transaction_data(combined_text)
        statement_summary = parser.parse_account_info(combined_text)
        
        if not transactions:
            click.echo(f"Warning: No transactions found in {pdf_file.name}", err=True)
            continue
        
        if statement_summary:
            all_summaries.append(statement_summary)
        
        # Clean and validate
        cleaned_transactions = processor.clean_transaction_data(transactions)
        if statement_summary:
            processor.validate_data_integrity(cleaned_transactions, statement_summary)
        
        final_transactions = processor.handle_duplicate_transactions(cleaned_transactions)
        all_transactions.extend(final_transactions)
        
        click.echo(f"  Extracted {len(final_transactions)} transactions")
        click.echo(f"  ✓ Categories applied from JSON configuration")
        
        # Basic validation info
        validation_data.append({
            'file': pdf_file.name,
            'transaction_count': len(final_transactions),
            'method': 'basic_with_categorization'
        })
    
    # Save basic validation report if requested
    if validation_report:
        with open(validation_report, 'w') as f:
            json.dump(validation_data, f, indent=2, default=str)
        click.echo(f"Processing report saved: {validation_report}")
    
    if validate_only:
        click.echo(f"\nValidation completed for {len(all_transactions)} transactions")
        return
    
    if not all_transactions:
        click.echo("No transactions found in any files", err=True)
        sys.exit(1)
    
    click.echo(f"\nTotal transactions extracted: {len(all_transactions)}")
    
    # Generate outputs
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Main CSV export
    source_files = ", ".join(f.name for f in pdf_files)
    success = exporter.create_google_sheets_compatible_format(
        all_transactions, output_path, source_files
    )
    
    if success:
        click.echo(f"Exported transactions to: {output_path}")
    else:
        click.echo("Failed to export main CSV file", err=True)
        sys.exit(1)
    
    # Monthly exports if requested
    if monthly:
        monthly_dir = output_path.parent / f"{output_path.stem}_monthly"
        success = exporter.export_monthly_files(all_transactions, monthly_dir, source_files)
        if success:
            click.echo(f"Exported monthly files to: {monthly_dir}")
    
    # Summary report if requested
    if summary_path:
        create_basic_summary_report(all_transactions, validation_data, summary_path)
        click.echo(f"Generated summary report: {summary_path}")


def create_basic_summary_report(transactions: List, validation_data: List, 
                              summary_path: Path):
    """Create summary report for basic parsing"""
    with open(summary_path, 'w') as f:
        f.write("PNC Statement Processing Summary\n")
        f.write("=" * 40 + "\n\n")
        
        f.write(f"Total transactions processed: {len(transactions)}\n")
        f.write(f"Files processed: {len(validation_data)}\n\n")
        
        # Processing summary
        f.write("Processing Summary:\n")
        f.write("-" * 20 + "\n")
        
        for file_data in validation_data:
            f.write(f"✓ {file_data['file']}: {file_data['transaction_count']} transactions\n")
        
        # Method information
        f.write(f"\nParsing method: Basic text-based parsing\n")
        f.write(f"Features used:\n")
        f.write(f"  • Text pattern matching\n")
        f.write(f"  • JSON-based categorization\n") 
        f.write(f"  • Transaction type detection\n")
        f.write(f"  • Description cleaning\n")


if __name__ == '__main__':
    main()