import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

try:
    from ..models import Transaction, StatementSummary
    from .base_parser import BaseStatementParser
    from .pnc_patterns import PNCPatterns
    from .section_extractor import SectionExtractor
    from .transaction_parser import TransactionParser
    from .categorization import TransactionCategorizer
except ImportError:
    import sys
    from pathlib import Path
    # Add parent directory to path for standalone execution
    sys.path.append(str(Path(__file__).parent.parent))
    from models import Transaction, StatementSummary
    from base_parser import BaseStatementParser
    from pnc_patterns import PNCPatterns
    from section_extractor import SectionExtractor
    from transaction_parser import TransactionParser
    from categorization import TransactionCategorizer

logger = logging.getLogger(__name__)


class PNCStatementParser(BaseStatementParser):
    """
    Parser for PNC Virtual Wallet statements.
    Implements patterns identified in PNC_Statement_Structure_Analysis.md
    """
    
    def __init__(self):
        self.patterns = PNCPatterns()
        self.categorizer = TransactionCategorizer()
        self.transaction_parser = TransactionParser(self.patterns, self.categorizer)
        self.section_extractor = SectionExtractor(self.patterns, self.transaction_parser)
    
    def parse_account_info(self, text: str) -> Optional[StatementSummary]:
        """Extract account and statement period information from header"""
        try:
            # Extract account number
            account_match = self.patterns.ACCOUNT_PATTERN.search(text)
            account_number = account_match.group(1).strip() if account_match else "Unknown"
            
            # Extract statement period
            period_match = self.patterns.PERIOD_PATTERN.search(text)
            if period_match:
                start_date = datetime.strptime(period_match.group(1), '%m/%d/%Y')
                end_date = datetime.strptime(period_match.group(2), '%m/%d/%Y')
            else:
                alt_period_match = self.patterns.ALT_PERIOD_PATTERN.search(text)
                if alt_period_match:
                    start_date = self._parse_month_day_year(
                        alt_period_match.group(1),
                        alt_period_match.group(2),
                        alt_period_match.group(3)
                    )
                    end_date = self._parse_month_day_year(
                        alt_period_match.group(4),
                        alt_period_match.group(5),
                        alt_period_match.group(6)
                    )
                else:
                    logger.warning("Could not parse statement period")
                    return None
            
            # Extract page count
            page_match = self.patterns.PAGE_PATTERN.search(text)
            total_pages = int(page_match.group(2)) if page_match else 1
            
            return StatementSummary(
                account_number=account_number,
                statement_period_start=start_date,
                statement_period_end=end_date,
                total_pages=total_pages,
                total_deposits=Decimal(0),
                total_withdrawals=Decimal(0),
                deposit_count=0,
                withdrawal_count=0
            )
            
        except Exception as e:
            logger.error(f"Failed to parse account info: {e}")
            return None
    
    def extract_transaction_data(self, text: str) -> List[Transaction]:
        """
        Extract all transactions from statement text.
        Handles deposits, withdrawals, and online banking sections.
        """
        transactions = []
        
        # Parse account info for date context
        summary = self.parse_account_info(text)
        if not summary:
            logger.error("Could not parse statement header - cannot determine year")
            return []
        
        # Extract deposits
        deposits = self.section_extractor.extract_deposits_section(text, summary)
        transactions.extend(deposits)

        # Extract withdrawals  
        withdrawals = self.section_extractor.extract_withdrawals_section(text, summary)
        transactions.extend(withdrawals)

        # Extract online banking deductions
        online_banking = self.section_extractor.extract_online_banking_section(text, summary)
        transactions.extend(online_banking)

        if not transactions:
            legacy_transactions = self._extract_legacy_table_transactions(text, summary)
            if legacy_transactions:
                logger.info(f"Extracted {len(legacy_transactions)} legacy table transactions")
                transactions.extend(legacy_transactions)

        logger.info(f"Extracted {len(transactions)} total transactions")
        return transactions

    def _parse_month_day_year(self, month_str: str, day_str: str, year_str: str) -> datetime:
        """Parse textual month/day/year values into a datetime object."""
        month_str = month_str.strip()
        day = int(day_str)
        year = int(year_str)

        try:
            return datetime.strptime(f"{month_str} {day} {year}", '%B %d %Y')
        except ValueError:
            # Fallback for abbreviated month names
            return datetime.strptime(f"{month_str} {day} {year}", '%b %d %Y')

    def _extract_legacy_table_transactions(self, text: str, summary: StatementSummary) -> List[Transaction]:
        """Fallback parser for legacy statements with combined credit/debit tables."""
        legacy_transactions = []
        lines = text.split('\n')

        for line in lines:
            stripped = line.strip()
            if not stripped or 'DATE * SERIAL #' in stripped.upper():
                continue

            date_match = self.patterns.DATE_PATTERN.match(stripped)
            if not date_match:
                continue

            amounts = self.patterns.AMOUNT_PATTERN.findall(stripped)
            if not amounts:
                continue

            # Separate balance amount when both debit and balance are present
            transaction_amount = amounts[-1]
            balance_amount = None
            if len(amounts) >= 2:
                balance_amount = amounts[-1]
                transaction_amount = amounts[-2]

            # Remove amounts (including possible dollar signs) from description portion
            description_portion = stripped
            for amt in amounts:
                description_portion = re.sub(r'(?:\$)?' + re.escape(amt), '', description_portion, count=1)
            description_portion = re.sub(r'\s+', ' ', description_portion).strip()

            # Remove trailing balance keywords if present
            if balance_amount:
                description_portion = description_portion.replace(balance_amount, '').strip()

            # Determine transaction type heuristically
            uppercase_desc = description_portion.upper()
            if any(keyword in uppercase_desc for keyword in ['DEPOSIT', 'CREDIT', 'PAYROLL', 'ACH CREDIT', 'DIRECT DEP']):
                transaction_type = 'CREDIT'
            else:
                transaction_type = 'DEBIT'

            synthetic_line = f"{date_match.group(1)} {transaction_amount} {description_portion}"
            parsed = self.transaction_parser.parse_transaction_lines(
                synthetic_line,
                summary,
                transaction_type=transaction_type
            )

            legacy_transactions.extend(parsed)

        return legacy_transactions
