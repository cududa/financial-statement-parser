import logging
from decimal import Decimal
from typing import List, Optional

try:
    from ..models import Transaction, StatementSummary
    from .pnc_patterns import PNCPatterns
    from .text_utils import TextCleaner, MerchantExtractor
    from .categorization import TransactionCategorizer
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from models import Transaction, StatementSummary
    from pnc_patterns import PNCPatterns
    from text_utils import TextCleaner, MerchantExtractor
    from categorization import TransactionCategorizer

logger = logging.getLogger(__name__)


class TransactionParser:
    """
    Core transaction parsing logic for PNC statements.
    Handles individual transaction extraction and multi-line description parsing.
    """
    
    def __init__(self, patterns: PNCPatterns, categorizer: TransactionCategorizer):
        self.patterns = patterns
        self.categorizer = categorizer
        self.text_cleaner = TextCleaner(patterns)
        self.merchant_extractor = MerchantExtractor(patterns)
    
    def parse_transaction_lines(self, section_text: str, summary: StatementSummary,
                              transaction_type: str, source_file: str = "") -> List[Transaction]:
        """
        Parse individual transaction lines from a section.
        Handles multi-line descriptions.
        """
        transactions = []
        lines = section_text.split('\n')
        i = 0
        
        # Find the starting page number from any page marker in the section
        current_page = 1
        for line in lines:
            if '--- PAGE' in line:
                try:
                    current_page = int(line.split('PAGE')[1].split('---')[0].strip())
                    break
                except:
                    pass
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Track page numbers
            if '--- PAGE' in line:
                try:
                    current_page = int(line.split('PAGE')[1].split('---')[0].strip())
                except:
                    pass
                i += 1
                continue
            
            # Skip empty lines, headers, and extraneous text
            if not line or self.text_cleaner.is_extraneous_line(line):
                i += 1
                continue
            
            # Look for date pattern at start of line
            date_match = self.patterns.DATE_PATTERN.match(line)
            if date_match:
                transaction = self._parse_single_transaction(
                    lines, i, summary, transaction_type, current_page, source_file
                )
                if transaction:
                    transactions.append(transaction)
                    # Skip lines consumed by this transaction
                    i += len(transaction.raw_lines)
                else:
                    i += 1
            else:
                i += 1
        
        return transactions
    
    def parse_transaction_lines_with_page(self, section_text: str, summary: StatementSummary,
                                        transaction_type: str, starting_page: int, source_file: str = "") -> List[Transaction]:
        """Parse transaction lines with a known starting page number"""
        transactions = []
        lines = section_text.split('\n')
        i = 0
        current_page = starting_page
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Track page numbers (though unlikely in section text)
            if '--- PAGE' in line:
                try:
                    current_page = int(line.split('PAGE')[1].split('---')[0].strip())
                except:
                    pass
                i += 1
                continue
            
            # Skip empty lines, headers, and extraneous text
            if not line or self.text_cleaner.is_extraneous_line(line):
                i += 1
                continue
            
            # Look for date pattern at start of line
            date_match = self.patterns.DATE_PATTERN.match(line)
            if date_match:
                transaction = self._parse_single_transaction(
                    lines, i, summary, transaction_type, current_page, source_file
                )
                if transaction:
                    transactions.append(transaction)
                    # Skip lines consumed by this transaction
                    i += len(transaction.raw_lines)
                else:
                    i += 1
            else:
                i += 1
        
        return transactions
    
    def _parse_single_transaction(self, lines: List[str], start_idx: int, summary: StatementSummary,
                                transaction_type: str, page_number: int, source_file: str = "") -> Optional[Transaction]:
        """
        Parse a single transaction that may span multiple lines.
        Returns Transaction object or None if parsing fails.
        """
        try:
            # Start with the date line
            current_line = lines[start_idx].strip()
            raw_lines = [current_line]
            
            # Extract date
            date_match = self.patterns.DATE_PATTERN.match(current_line)
            if not date_match:
                return None
            
            date_str = date_match.group(1)
            
            # Extract amount from first line
            amount_match = self.patterns.AMOUNT_PATTERN.search(current_line)
            if not amount_match:
                logger.warning(f"No amount found in line: {current_line}")
                return None
            
            amount_str = amount_match.group(1).replace(',', '')
            amount = Decimal(amount_str)
            
            # Extract description starting after amount
            amount_end = amount_match.end()
            description_parts = [current_line[amount_end:].strip()]
            
            # Look for continuation lines (non-date lines that follow)
            next_idx = start_idx + 1
            while next_idx < len(lines):
                next_line = lines[next_idx].strip()
                
                # Stop if we hit another date line or empty line
                if not next_line or self.patterns.DATE_PATTERN.match(next_line):
                    break
                
                # Skip page markers
                if '--- PAGE' in next_line:
                    next_idx += 1
                    continue
                
                # Skip extraneous lines that shouldn't be part of transaction description
                if self.text_cleaner.is_extraneous_line(next_line):
                    logger.debug(f"Skipping extraneous continuation line: '{next_line}'")
                    next_idx += 1
                    continue
                
                # Clean potential continuation line to check if it contains valid merchant data
                cleaned_line = self.text_cleaner.clean_description(next_line)
                
                # Check if the cleaned line or original line contains valid merchant continuation data
                if (self.text_cleaner.is_valid_merchant_continuation(next_line) or 
                    (cleaned_line and len(cleaned_line.strip()) >= 3 and 
                     self.text_cleaner.is_valid_merchant_continuation(cleaned_line))):
                    # Add continuation line (only if it's actually transaction data)
                    description_parts.append(next_line)
                    raw_lines.append(next_line)
                    next_idx += 1
                else:
                    # Stop if we hit non-merchant data
                    break
            
            # Combine description parts
            full_description = ' '.join(description_parts).strip()
            
            # Clean description of contaminated text
            full_description = self.text_cleaner.clean_description(full_description)
            
            # Extract merchant and card info
            merchant, card_last_four = self.merchant_extractor.extract_merchant_info(
                full_description, transaction_type
            )
            
            # Auto-categorize
            category = self.categorizer.categorize_transaction(full_description)
            
            # Determine year from statement period
            month, day = map(int, date_str.split('/'))
            
            # Handle year boundary correctly - match transaction month to statement period
            if month == summary.statement_period_start.month:
                year = summary.statement_period_start.year
            elif month == summary.statement_period_end.month:
                year = summary.statement_period_end.year
            else:
                # For months between start and end, use the appropriate year
                # If statement spans year boundary (Dec -> Jan), assign year based on month
                if summary.statement_period_start.year != summary.statement_period_end.year:
                    # Statement crosses year boundary
                    if month >= summary.statement_period_start.month:
                        year = summary.statement_period_start.year  # Dec transactions = start year
                    else:
                        year = summary.statement_period_end.year    # Jan transactions = end year
                else:
                    # Statement within same year
                    year = summary.statement_period_start.year
            
            return Transaction(
                date=date_str,
                year=year,
                month=month,
                amount=amount,
                transaction_type=transaction_type,
                description=full_description,
                merchant=merchant,
                card_last_four=card_last_four,
                category=category,
                raw_lines=raw_lines,
                page_number=page_number,
                source_file=source_file
            )
            
        except Exception as e:
            logger.error(f"Failed to parse transaction at line {start_idx}: {e}")
            return None