from decimal import Decimal
from typing import List, Tuple, Set, Optional
import logging
from datetime import datetime

try:
    from .models import Transaction, StatementSummary
except ImportError:
    from models import Transaction, StatementSummary

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Data processing, validation, and cleaning module.
    Handles data integrity checks and duplicate detection.
    """
    
    def __init__(self):
        self.validation_errors = []
        self.warnings = []
    
    def clean_transaction_data(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Clean and normalize transaction data.
        Handles description cleanup, amount validation, etc.
        """
        cleaned_transactions = []
        
        for transaction in transactions:
            try:
                # Clean description
                cleaned_description = self._clean_description(transaction.description)
                
                # Validate amount
                if not self._validate_amount(transaction.amount):
                    self.warnings.append(f"Suspicious amount: ${transaction.amount} on {transaction.date}")
                
                # Create cleaned transaction
                cleaned_transaction = Transaction(
                    date=transaction.date,
                    year=transaction.year,
                    month=transaction.month,
                    amount=transaction.amount,
                    transaction_type=transaction.transaction_type,
                    description=cleaned_description,
                    merchant=self._clean_merchant_name(transaction.merchant),
                    card_last_four=transaction.card_last_four,
                    category=transaction.category,
                    raw_lines=transaction.raw_lines,
                    page_number=transaction.page_number
                )
                
                cleaned_transactions.append(cleaned_transaction)
                
            except Exception as e:
                logger.error(f"Failed to clean transaction {transaction.date}: {e}")
                self.validation_errors.append(f"Transaction cleanup failed: {transaction.date} - {e}")
        
        logger.info(f"Cleaned {len(cleaned_transactions)} transactions")
        return cleaned_transactions
    
    def validate_data_integrity(self, transactions: List[Transaction], 
                              summary: StatementSummary) -> bool:
        """
        Validate transaction data integrity.
        Checks date ranges, amount consistency, etc.
        """
        is_valid = True
        
        # Validate date ranges
        for transaction in transactions:
            if not self._validate_transaction_date(transaction, summary):
                is_valid = False
        
        # Validate balance calculations
        if not self._validate_balance_calculations(transactions, summary):
            is_valid = False
        
        # Check for missing data
        if not self._check_completeness(transactions):
            is_valid = False
        
        return is_valid
    
    def handle_duplicate_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Identify and handle duplicate transactions.
        Returns deduplicated list.
        """
        duplicates = self._find_duplicates(transactions)
        
        if duplicates:
            logger.warning(f"Found {len(duplicates)} potential duplicate transactions")
            for dup_group in duplicates:
                self.warnings.append(f"Potential duplicates: {[t.date + ' ' + t.description[:50] for t in dup_group]}")
        
        # For now, just log duplicates. In production, might want user input
        return transactions
    
    def calculate_running_balances(self, transactions: List[Transaction], 
                                 opening_balance: Optional[Decimal] = None) -> List[Transaction]:
        """
        Calculate running balances for transactions.
        Assumes transactions are in chronological order.
        """
        if opening_balance is None:
            logger.warning("No opening balance provided - cannot calculate running balances")
            return transactions
        
        # Sort transactions by date
        sorted_transactions = sorted(transactions, key=lambda t: t.full_date)
        
        current_balance = opening_balance
        
        for transaction in sorted_transactions:
            current_balance += transaction.signed_amount
            # Note: Transaction model would need a balance_after field for this
            # For now, just log the calculated balance
            logger.debug(f"{transaction.date}: {transaction.signed_amount} -> Balance: {current_balance}")
        
        return sorted_transactions
    
    def _clean_description(self, description: str) -> str:
        """Clean up transaction description"""
        if not description:
            return ""
        
        # Remove excessive whitespace
        cleaned = ' '.join(description.split())
        
        # Remove common artifacts
        cleaned = cleaned.replace('  ', ' ')
        
        # Truncate if too long (for CSV compatibility)
        if len(cleaned) > 200:
            cleaned = cleaned[:197] + "..."
        
        return cleaned.strip()
    
    def _clean_merchant_name(self, merchant: str) -> str:
        """Clean up merchant name"""
        if not merchant or merchant == "Unknown":
            return merchant
        
        # Remove common suffixes
        cleaned = merchant.replace('*', '').strip()
        
        # Capitalize properly
        cleaned = cleaned.title()
        
        return cleaned
    
    def _validate_amount(self, amount: Decimal) -> bool:
        """Validate that amount is reasonable"""
        # Check for extremely large amounts that might be parsing errors
        if amount > Decimal('50000'):  # $50,000 threshold
            return False
        
        # Check for zero amounts
        if amount == Decimal('0'):
            return False
        
        # Check for negative amounts (should always be positive)
        if amount < Decimal('0'):
            return False
        
        return True
    
    def _validate_transaction_date(self, transaction: Transaction, 
                                 summary: StatementSummary) -> bool:
        """Validate transaction date falls within statement period"""
        try:
            transaction_date = transaction.full_date
            
            # Allow some flexibility for transactions on boundary dates
            start_date = summary.statement_period_start
            end_date = summary.statement_period_end
            
            if transaction_date < start_date or transaction_date > end_date:
                self.validation_errors.append(
                    f"Transaction date {transaction.date} outside statement period "
                    f"{start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
                )
                return False
                
        except Exception as e:
            self.validation_errors.append(f"Invalid date format: {transaction.date} - {e}")
            return False
        
        return True
    
    def _validate_balance_calculations(self, transactions: List[Transaction],
                                     summary: StatementSummary) -> bool:
        """Validate that transaction totals match statement summary"""
        total_credits = sum((t.amount for t in transactions if t.transaction_type == 'CREDIT'), Decimal('0'))
        total_debits = sum((t.amount for t in transactions if t.transaction_type == 'DEBIT'), Decimal('0'))
        
        credit_count = len([t for t in transactions if t.transaction_type == 'CREDIT'])
        debit_count = len([t for t in transactions if t.transaction_type == 'DEBIT'])
        
        # Update summary with calculated totals
        summary.total_deposits = total_credits
        summary.total_withdrawals = total_debits
        summary.deposit_count = credit_count
        summary.withdrawal_count = debit_count
        
        logger.info(f"Calculated totals - Credits: ${total_credits} ({credit_count} transactions)")
        logger.info(f"Calculated totals - Debits: ${total_debits} ({debit_count} transactions)")
        
        return True
    
    def _check_completeness(self, transactions: List[Transaction]) -> bool:
        """Check for missing or incomplete transaction data"""
        incomplete_count = 0
        
        for transaction in transactions:
            if not transaction.description.strip():
                incomplete_count += 1
                self.warnings.append(f"Empty description for transaction on {transaction.date}")
            
            if transaction.amount == Decimal('0'):
                incomplete_count += 1
                self.warnings.append(f"Zero amount for transaction on {transaction.date}")
        
        if incomplete_count > 0:
            logger.warning(f"Found {incomplete_count} incomplete transactions")
        
        return incomplete_count == 0
    
    def _find_duplicates(self, transactions: List[Transaction]) -> List[List[Transaction]]:
        """Find potential duplicate transactions"""
        duplicates = []
        seen = {}
        
        for transaction in transactions:
            # Create a key based on date, amount, and merchant
            key = (
                transaction.date,
                transaction.amount,
                transaction.merchant.lower() if transaction.merchant else ""
            )
            
            if key in seen:
                # Found potential duplicate
                duplicates.append([seen[key], transaction])
            else:
                seen[key] = transaction
        
        return duplicates
    
    def get_validation_report(self) -> str:
        """Generate validation report with errors and warnings"""
        report = []
        
        if self.validation_errors:
            report.append("VALIDATION ERRORS:")
            for error in self.validation_errors:
                report.append(f"  - {error}")
            report.append("")
        
        if self.warnings:
            report.append("WARNINGS:")
            for warning in self.warnings:
                report.append(f"  - {warning}")
            report.append("")
        
        if not self.validation_errors and not self.warnings:
            report.append("No validation issues found.")
        
        return "\n".join(report)
