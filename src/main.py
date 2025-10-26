#!/usr/bin/env python3

import click
import logging
from pathlib import Path
from typing import List
import sys

try:
    from .pdf_ingester import PDFIngester
    from .parsers import PNCStatementParser
    from .data_processor import DataProcessor
    from .csv_exporter import CSVExporter
    from .year_processor import YearProcessor
except ImportError:
    from pdf_ingester import PDFIngester
    from parsers import PNCStatementParser
    from data_processor import DataProcessor
    from csv_exporter import CSVExporter
    from year_processor import YearProcessor

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
@click.option('--year', '-y', type=int,
              help='Process complete year (e.g., 2023) - auto-discovers files from multiple directories')
@click.option('--base-path', type=click.Path(exists=True, path_type=Path), default='PNC_Documents',
              help='Root directory containing year subdirectories (default: PNC_Documents/)')
@click.option('--include-next-month', is_flag=True,
              help='Include first statement of next year for complete end-of-year data')
@click.option('--output', '-o', type=click.Path(path_type=Path), required=True,
              help='Output CSV file path')
@click.option('--monthly', is_flag=True, 
              help='Create separate CSV files for each month')
@click.option('--summary', type=click.Path(path_type=Path),
              help='Generate summary report file')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
@click.option('--validate-only', is_flag=True,
              help='Only validate files without generating output')
@click.option('--detect-duplicates', is_flag=True,
              help='Enable duplicate transaction detection (disabled by default)')
def main(file, directory, year, base_path, include_next_month, output, monthly, summary, verbose, validate_only, detect_duplicates):
    """
    PNC Statement Parser - Convert PNC bank statement PDFs to CSV format.
    
    Examples:
        # Process single statement
        python -m src.main --file statement.pdf --output transactions.csv
        
        # Process entire directory
        python -m src.main --directory 2023/ --output 2023_transactions.csv
        
        # Process complete year (auto-discovers directories)
        python -m src.main --year 2023 --output 2023_complete.csv --monthly
        
        # Year mode with next month for complete data
        python -m src.main --year 2023 --include-next-month --output 2023_complete.csv
        
        # Create monthly files with summary
        python -m src.main --directory 2023/ --output 2023_all.csv --monthly --summary summary.txt
    """
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    input_modes = sum(bool(x) for x in [file, directory, year])
    if input_modes == 0:
        click.echo("Error: Must specify either --file, --directory, or --year", err=True)
        sys.exit(1)
    
    if input_modes > 1:
        click.echo("Error: Cannot specify multiple input modes (--file, --directory, --year)", err=True)
        sys.exit(1)
    
    try:
        # Initialize components
        ingester = PDFIngester()
        parser = PNCStatementParser()
        processor = DataProcessor()
        exporter = CSVExporter()
        
        # Get list of files to process
        pdf_files = []
        year_mode = False
        
        if file:
            pdf_files = [file]
        elif directory:
            pdf_files = list(directory.glob("*.pdf"))
            if not pdf_files:
                click.echo(f"No PDF files found in {directory}", err=True)
                sys.exit(1)
        elif year:
            # Year processing mode
            year_mode = True
            year_processor = YearProcessor(base_path)
            pdf_files = year_processor.discover_year_files(year, include_next_month)
            
            if not pdf_files:
                click.echo(f"No PDF files found for year {year} in {base_path}", err=True)
                sys.exit(1)
            
            # Validate year coverage
            coverage_info = year_processor.validate_year_coverage(pdf_files, year)
            if coverage_info['warnings']:
                click.echo("Year Coverage Warnings:", err=True)
                for warning in coverage_info['warnings']:
                    click.echo(f"  - {warning}", err=True)
                click.echo()  # Add blank line
        
        click.echo(f"Found {len(pdf_files)} PDF file(s) to process")
        
        all_transactions = []
        all_summaries = []
        
        # Process each file
        for pdf_file in pdf_files:
            click.echo(f"Processing: {pdf_file.name}")
            
            # Extract text
            pages_text = ingester.extract_text_content(pdf_file)
            if not pages_text:
                click.echo(f"Warning: No text extracted from {pdf_file.name}", err=True)
                continue
            
            # Identify statement type
            statement_type = ingester.identify_statement_type(pages_text)
            if statement_type != 'PNC_VIRTUAL_WALLET':
                click.echo(f"Warning: {pdf_file.name} may not be a PNC Virtual Wallet statement", err=True)
            
            # Combine pages
            combined_text = ingester.handle_multi_page_documents(pages_text)

            # Parse transactions
            transactions = parser.extract_transaction_data(combined_text, source_file=pdf_file.name)
            if not transactions:
                click.echo(f"Warning: No transactions found in {pdf_file.name}", err=True)
                continue
            
            # Parse summary info
            statement_summary = parser.parse_account_info(combined_text)
            if statement_summary:
                all_summaries.append(statement_summary)
            
            # Clean and validate
            cleaned_transactions = processor.clean_transaction_data(transactions)

            if statement_summary:
                is_valid = processor.validate_data_integrity(cleaned_transactions, statement_summary)
                if not is_valid:
                    click.echo(f"Warning: Validation issues found in {pdf_file.name}")

            # Handle duplicates only if flag is enabled
            if detect_duplicates:
                final_transactions = processor.handle_duplicate_transactions(cleaned_transactions)
            else:
                final_transactions = cleaned_transactions

            all_transactions.extend(final_transactions)
            click.echo(f"  Extracted {len(final_transactions)} transactions")
        
        # Apply year filtering if in year mode
        if year_mode and year:
            pre_filter_count = len(all_transactions)
            all_transactions = year_processor.filter_transactions_by_year(all_transactions, year)
            post_filter_count = len(all_transactions)
            if pre_filter_count != post_filter_count:
                click.echo(f"Filtered to {post_filter_count} transactions for year {year} "
                          f"(excluded {pre_filter_count - post_filter_count} from other years)")
        
        if validate_only:
            # Show validation report only
            validation_report = processor.get_validation_report()
            click.echo("\nValidation Report:")
            click.echo(validation_report)
            return
        
        if not all_transactions:
            click.echo("No transactions found in any files", err=True)
            sys.exit(1)
        
        click.echo(f"\nTotal transactions extracted: {len(all_transactions)}")
        
        # Generate outputs with appropriate naming
        if year_mode and year:
            # Use year-specific output paths
            output_paths = year_processor.generate_year_output_paths(Path(output), year)
            output_path = output_paths['main_csv']
            monthly_dir = output_paths['monthly_dir']
            summary_path = output_paths['summary']
        else:
            # Use user-provided paths
            output_path = Path(output)
            monthly_dir = output_path.parent / f"{output_path.stem}_monthly"
            summary_path = Path(summary) if summary else None
        
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Main CSV export
        success = exporter.create_google_sheets_compatible_format(
            all_transactions, output_path
        )
        
        if success:
            click.echo(f"Exported transactions to: {output_path}")
        else:
            click.echo("Failed to export main CSV file", err=True)
            sys.exit(1)
        
        # Monthly exports if requested (auto-enabled for year mode)
        if monthly or year_mode:
            success = exporter.export_monthly_files(all_transactions, monthly_dir)
            if success:
                click.echo(f"Exported monthly files to: {monthly_dir}")
        
        # Summary report if requested (auto-enabled for year mode if summaries available)
        if (summary and all_summaries) or (year_mode and all_summaries):
            if summary_path is not None:
                success = exporter.generate_summary_report(
                    all_transactions, all_summaries[0], summary_path
                )
            else:
                click.echo("Error: Summary path is None, cannot generate summary report", err=True)
                sys.exit(1)
            if success:
                click.echo(f"Generated summary report: {summary_path}")
        
        # Show validation report
        validation_report = processor.get_validation_report()
        if validation_report.strip() != "No validation issues found.":
            click.echo("\nValidation Report:")
            click.echo(validation_report)
        
        click.echo("\nProcessing completed successfully!")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()