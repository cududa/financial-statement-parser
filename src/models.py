from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import List, Optional


@dataclass
class Transaction:
    """
    Data model for a single transaction from PNC statement.
    Based on structure analysis from PNC_Statement_Structure_Analysis.md
    """
    date: str              # MM/DD format from statement
    year: int              # Derived from statement period
    month: int             # Derived from statement period  
    amount: Decimal        # Always positive
    transaction_type: str  # DEBIT/CREDIT
    description: str       # Full concatenated description
    merchant: str          # Extracted merchant name
    card_last_four: str    # Card reference (e.g., "3767")
    category: str          # Auto-categorized type
    raw_lines: List[str]   # Original text lines for debugging
    page_number: int       # Source page
    
    @property
    def full_date(self) -> datetime:
        """Convert MM/DD date to full datetime using statement year/month"""
        month, day = map(int, self.date.split('/'))
        return datetime(self.year, month, day)
    
    @property
    def signed_amount(self) -> Decimal:
        """Return amount with correct sign based on transaction type"""
        if self.transaction_type == 'DEBIT':
            return -self.amount
        return self.amount


@dataclass  
class StatementSummary:
    """Summary information extracted from PNC statement header"""
    account_number: str
    statement_period_start: datetime
    statement_period_end: datetime
    total_pages: int
    total_deposits: Decimal
    total_withdrawals: Decimal
    deposit_count: int
    withdrawal_count: int