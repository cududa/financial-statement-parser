import logging
from typing import List, Optional, Tuple

try:
    from ..models import Transaction, StatementSummary
    from .pnc_patterns import PNCPatterns
    from .transaction_parser import TransactionParser
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from models import Transaction, StatementSummary
    from pnc_patterns import PNCPatterns
    from transaction_parser import TransactionParser

logger = logging.getLogger(__name__)


class SectionExtractor:
    """
    Handles extraction of different sections from PNC statements.
    Manages deposits, withdrawals, and online banking sections.
    """
    
    def __init__(self, patterns: PNCPatterns, transaction_parser: TransactionParser):
        self.patterns = patterns
        self.transaction_parser = transaction_parser
    
    def extract_deposits_section(self, text: str, summary: StatementSummary, source_file: str = "") -> List[Transaction]:
        """Extract transactions from Deposits and Other Additions section"""
        deposits = []

        # Find deposits section
        deposits_match = self.patterns.DEPOSITS_START.search(text)
        if not deposits_match:
            logger.warning("No deposits section found")
            return []

        # Extract section text until next major section
        section_start = deposits_match.end()

        # Find end of deposits section (start of withdrawals or end of text)
        withdrawals_match = self.patterns.WITHDRAWALS_START.search(text, section_start)
        section_end = withdrawals_match.start() if withdrawals_match else len(text)

        deposits_text = text[section_start:section_end]

        # Parse transactions in this section
        transactions = self.transaction_parser.parse_transaction_lines(
            deposits_text,
            summary,
            transaction_type='CREDIT',
            source_file=source_file
        )
        
        logger.info(f"Found {len(transactions)} deposit transactions")
        return transactions
    
    def extract_withdrawals_section(self, text: str, summary: StatementSummary, source_file: str = "") -> List[Transaction]:
        """Extract transactions from Banking/Debit Card Withdrawals section"""
        withdrawals = []

        # Find withdrawals section
        withdrawals_match = self.patterns.WITHDRAWALS_START.search(text)
        if not withdrawals_match:
            logger.warning("No withdrawals section found")
            return []

        # Extract section text until next major section
        section_start = withdrawals_match.end()

        # Find end of withdrawals section (start of online banking or daily balance)
        online_banking_match = self.patterns.ONLINE_BANKING_START.search(text, section_start)
        daily_balance_match = self.patterns.DAILY_BALANCE_START.search(text, section_start)

        # Use the earliest next section as the end point
        section_end = len(text)
        if online_banking_match:
            section_end = min(section_end, online_banking_match.start())
        if daily_balance_match:
            section_end = min(section_end, daily_balance_match.start())

        withdrawals_text = text[section_start:section_end]

        # Parse transactions in this section
        transactions = self.transaction_parser.parse_transaction_lines(
            withdrawals_text,
            summary,
            transaction_type='DEBIT',
            source_file=source_file
        )
        
        logger.info(f"Found {len(transactions)} withdrawal transactions")
        return transactions
    
    def extract_online_banking_section(self, text: str, summary: StatementSummary, source_file: str = "") -> List[Transaction]:
        """Extract transactions from Online and Electronic Banking Deductions section"""
        online_banking = []

        # Find online banking section
        online_banking_match = self.patterns.ONLINE_BANKING_START.search(text)
        if not online_banking_match:
            logger.info("No online banking section found")
            return []

        # Find the page number where this section starts
        section_start_page = self._find_page_number_at_position(text, online_banking_match.start())

        # Extract section text until next major section (Daily Balance Detail)
        section_start = online_banking_match.end()

        # Find end of online banking section
        daily_balance_match = self.patterns.DAILY_BALANCE_START.search(text, section_start)
        section_end = daily_balance_match.start() if daily_balance_match else len(text)

        online_banking_text = text[section_start:section_end]

        # Parse transactions in this section (these are debits/payments)
        transactions = self.transaction_parser.parse_transaction_lines_with_page(
            online_banking_text,
            summary,
            transaction_type='DEBIT',
            starting_page=section_start_page,
            source_file=source_file
        )
        
        logger.info(f"Found {len(transactions)} online banking transactions")
        return transactions
    
    def _find_page_number_at_position(self, text: str, position: int) -> int:
        """Find the page number at a given position in the full text"""
        # Look backwards from the position to find the most recent page marker
        text_before = text[:position]
        page_markers = []
        
        lines = text_before.split('\n')
        for line in lines:
            if '--- PAGE' in line:
                try:
                    page_num = int(line.split('PAGE')[1].split('---')[0].strip())
                    page_markers.append(page_num)
                except:
                    pass
        
        return page_markers[-1] if page_markers else 1