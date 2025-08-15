"""
Year-based processing module for handling multi-directory year processing.
Provides smart file discovery and year boundary transaction filtering.
"""

import logging
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime

try:
    from .models import Transaction
except ImportError:
    from models import Transaction

logger = logging.getLogger(__name__)


class YearProcessor:
    """
    Handles year-specific processing logic including file discovery
    across multiple directories and year boundary filtering.
    """
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.supported_extensions = {'.pdf'}
    
    def discover_year_files(self, year: int, include_next_month: bool = False) -> List[Path]:
        """
        Discover all PDF files for a given year across multiple directories.
        
        Args:
            year: The target year (e.g., 2023)
            include_next_month: Include first statement of next year for complete data
            
        Returns:
            List of PDF file paths for the year
        """
        pdf_files = []
        
        # Primary year directory
        year_dir = self.base_path / str(year)
        if year_dir.exists():
            year_files = self._scan_directory_for_pdfs(year_dir)
            pdf_files.extend(year_files)
            logger.info(f"Found {len(year_files)} files in {year_dir}")
        else:
            logger.warning(f"Year directory not found: {year_dir}")
        
        # Include next year's first statement if requested
        if include_next_month:
            next_year_dir = self.base_path / str(year + 1)
            if next_year_dir.exists():
                next_year_files = self._scan_directory_for_pdfs(next_year_dir)
                # Filter to likely first-of-year statements (January)
                january_files = [f for f in next_year_files 
                               if self._is_likely_january_statement(f)]
                if january_files:
                    pdf_files.extend(january_files)
                    logger.info(f"Added {len(january_files)} next-year files for complete {year} data")
        
        # Sort files for consistent processing order
        pdf_files.sort(key=lambda x: x.name)
        
        logger.info(f"Total files discovered for year {year}: {len(pdf_files)}")
        return pdf_files
    
    def _scan_directory_for_pdfs(self, directory: Path) -> List[Path]:
        """Scan directory for PDF files"""
        if not directory.exists():
            return []
        
        pdf_files = []
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                pdf_files.append(file_path)
        
        return pdf_files
    
    def _is_likely_january_statement(self, file_path: Path) -> bool:
        """
        Heuristic to identify January statements from filename.
        Looks for patterns like "01_January", "Statement_01", etc.
        """
        filename_lower = file_path.name.lower()
        january_indicators = [
            '01_january', 'statement_01', 'january_', '_01_',
            'jan_', '_jan_', 'january', '01.'
        ]
        
        return any(indicator in filename_lower for indicator in january_indicators)
    
    def filter_transactions_by_year(self, transactions: List[Transaction], 
                                  target_year: int) -> List[Transaction]:
        """
        Filter transactions to only include those from the target year.
        Handles cross-year statements by checking actual transaction dates.
        
        Args:
            transactions: List of all transactions
            target_year: Year to filter for (e.g., 2023)
            
        Returns:
            Filtered list containing only target year transactions
        """
        year_transactions = []
        other_year_count = 0
        
        for transaction in transactions:
            if transaction.year == target_year:
                year_transactions.append(transaction)
            else:
                other_year_count += 1
        
        logger.info(f"Filtered {len(year_transactions)} transactions for year {target_year}")
        if other_year_count > 0:
            logger.info(f"Excluded {other_year_count} transactions from other years")
        
        return year_transactions
    
    def validate_year_coverage(self, pdf_files: List[Path], year: int) -> dict:
        """
        Validate that we have reasonable coverage for the year.
        
        Args:
            pdf_files: List of PDF files found
            year: Target year
            
        Returns:
            Dict with coverage information and warnings
        """
        coverage_info = {
            'files_found': len(pdf_files),
            'expected_months': 12,
            'warnings': [],
            'file_list': [f.name for f in pdf_files]
        }
        
        # Basic file count check
        if len(pdf_files) < 12:
            coverage_info['warnings'].append(
                f"Only {len(pdf_files)} files found for {year}. "
                f"Expected ~12 for complete year coverage."
            )
        elif len(pdf_files) > 15:
            coverage_info['warnings'].append(
                f"Found {len(pdf_files)} files for {year}. "
                f"This may include duplicate or extra files."
            )
        
        # Month coverage heuristic (basic filename analysis)
        likely_months = self._analyze_month_coverage(pdf_files)
        if len(likely_months) < 12:
            missing_months = set(range(1, 13)) - likely_months
            coverage_info['warnings'].append(
                f"Potentially missing months: {sorted(missing_months)}"
            )
        
        return coverage_info
    
    def _analyze_month_coverage(self, pdf_files: List[Path]) -> Set[int]:
        """
        Analyze filenames to guess which months are covered.
        Returns set of month numbers (1-12) likely present.
        """
        likely_months = set()
        
        month_patterns = {
            1: ['01', 'jan', 'january'],
            2: ['02', 'feb', 'february'],
            3: ['03', 'mar', 'march'],
            4: ['04', 'apr', 'april'],
            5: ['05', 'may'],
            6: ['06', 'jun', 'june'],
            7: ['07', 'jul', 'july'],
            8: ['08', 'aug', 'august'],
            9: ['09', 'sep', 'september'],
            10: ['10', 'oct', 'october'],
            11: ['11', 'nov', 'november'],
            12: ['12', 'dec', 'december']
        }
        
        for pdf_file in pdf_files:
            filename_lower = pdf_file.name.lower()
            for month_num, patterns in month_patterns.items():
                if any(pattern in filename_lower for pattern in patterns):
                    likely_months.add(month_num)
                    break
        
        return likely_months
    
    def generate_year_output_paths(self, base_output_path: Path, year: int) -> dict:
        """
        Generate appropriate output paths for year processing mode.
        
        Args:
            base_output_path: Base output path provided by user
            year: Year being processed
            
        Returns:
            Dict with various output paths
        """
        base_path = Path(base_output_path)
        base_stem = base_path.stem
        
        # If user didn't include year in filename, add it
        if str(year) not in base_stem:
            base_stem = f"{year}_{base_stem}"
        
        return {
            'main_csv': base_path.parent / f"{base_stem}_complete.csv",
            'monthly_dir': base_path.parent / f"{base_stem}_complete_monthly",
            'summary': base_path.parent / f"{base_stem}_complete_summary.txt"
        }