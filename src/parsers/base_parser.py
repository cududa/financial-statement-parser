from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

try:
    from ..models import Transaction, StatementSummary
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from models import Transaction, StatementSummary


class BaseStatementParser(ABC):
    """
    Abstract base class for bank statement parsers.
    Defines the interface that all bank-specific parsers should implement.
    """
    
    @abstractmethod
    def parse_account_info(self, text: str) -> Optional[StatementSummary]:
        """
        Extract account and statement period information from header.
        
        Args:
            text: Raw statement text
            
        Returns:
            StatementSummary object with account info, or None if parsing fails
        """
        pass
    
    @abstractmethod
    def extract_transaction_data(self, text: str) -> List[Transaction]:
        """
        Extract all transactions from statement text.
        
        Args:
            text: Raw statement text
            
        Returns:
            List of Transaction objects
        """
        pass
    
    def validate_transactions(self, transactions: List[Transaction], 
                            summary: StatementSummary) -> List[str]:
        """
        Validate extracted transactions for data integrity.
        
        Args:
            transactions: List of transactions to validate
            summary: Statement summary for validation context
            
        Returns:
            List of validation warnings/errors
        """
        warnings = []
        
        if not transactions:
            warnings.append("No transactions found in statement")
            return warnings
        
        # Date range validation
        for transaction in transactions:
            transaction_date = datetime(transaction.year, transaction.month, 
                                      int(transaction.date.split('/')[1]))
            
            if (transaction_date < summary.statement_period_start or 
                transaction_date > summary.statement_period_end):
                warnings.append(
                    f"Transaction date {transaction.date}/{transaction.year} "
                    f"outside statement period"
                )
        
        # Duplicate detection - include page and position to avoid false positives
        # for legitimate same-day, same-amount transactions at the same merchant
        seen_transactions = set()
        for idx, transaction in enumerate(transactions):
            tx_key = (
                transaction.date,
                transaction.amount,
                transaction.description[:50],
                transaction.page_number,
                transaction.source_file,
                idx  # Position in transaction list as tie-breaker
            )
            if tx_key in seen_transactions:
                warnings.append(
                    f"Potential duplicate transaction: {transaction.date} "
                    f"{transaction.amount} on page {transaction.page_number}"
                )
            seen_transactions.add(tx_key)
        
        # Amount reasonableness check
        for transaction in transactions:
            if transaction.amount > 50000:  # $50k threshold
                warnings.append(f"Large transaction amount: ${transaction.amount}")
        
        return warnings