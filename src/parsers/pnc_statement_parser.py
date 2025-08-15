import logging
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
            account_number = account_match.group(1) if account_match else "Unknown"
            
            # Extract statement period
            period_match = self.patterns.PERIOD_PATTERN.search(text)
            if period_match:
                start_date = datetime.strptime(period_match.group(1), '%m/%d/%Y')
                end_date = datetime.strptime(period_match.group(2), '%m/%d/%Y')
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
        
        logger.info(f"Extracted {len(transactions)} total transactions")
        return transactions