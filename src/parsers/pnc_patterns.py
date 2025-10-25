import re
from typing import List


class PNCPatterns:
    """
    Pattern definitions specific to PNC Virtual Wallet statements.
    Contains all regex patterns used for parsing PNC statement text.
    """
    
    def __init__(self):
        # Date patterns
        self.DATE_PATTERN = re.compile(r'^(\d{1,2}/\d{1,2})\s+')
        
        # Amount patterns allow optional leading digits to catch values like ".75"
        self.AMOUNT_PATTERN = re.compile(r'((?:\d{1,3}(?:,\d{3})*)?\.\d{2})')
        self.SIMPLE_AMOUNT = re.compile(r'((?:\d+)?\.\d{2})')
        
        # Transaction type patterns
        self.DEBIT_CARD_PURCHASE = re.compile(r'(\d{4})\s+Debit Card Purchase\s+(.+)', re.IGNORECASE)
        self.RECURRING_PAYMENT = re.compile(r'(\d{4})\s+Recurring Debit Card\s+(.+)', re.IGNORECASE)
        self.POS_PURCHASE = re.compile(r'POS Purchase\s+(.+)', re.IGNORECASE)
        self.DIRECT_DEPOSIT = re.compile(r'Direct\s*Deposit\s*-\s*(.+)', re.IGNORECASE)
        self.DEBIT_CARD_CREDIT = re.compile(r'DebitCard Credit(.+)', re.IGNORECASE)
        
        # Section boundary patterns
        self.DEPOSITS_START = re.compile(r'Deposits and Other Additions', re.IGNORECASE)
        self.WITHDRAWALS_START = re.compile(r'Banking/Debit Card Withdrawals and Purchases', re.IGNORECASE)
        self.ONLINE_BANKING_START = re.compile(r'Online and Electronic Banking Deductions', re.IGNORECASE)
        self.DAILY_BALANCE_START = re.compile(r'Daily Balance Detail', re.IGNORECASE)
        self.SECTION_END = re.compile(r'(continued on next page|^\s*$)')
        
        # Header patterns
        self.ACCOUNT_PATTERN = re.compile(r'Primary account number:\s*(\d{2}-\d{4}-\d{4})')
        self.PERIOD_PATTERN = re.compile(r'For the period\s+(\d{1,2}/\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{1,2}/\d{4})')
        self.PAGE_PATTERN = re.compile(r'Page\s+(\d+)\s+of\s+(\d+)')
        
        # Extraneous text patterns to ignore/filter out
        self.IGNORE_PATTERNS = self._build_ignore_patterns()
    
    def _build_ignore_patterns(self) -> List[re.Pattern]:
        """Build list of patterns for filtering extraneous text"""
        return [
            re.compile(r'^\s*Date\s+Amount\s+Description\s*$', re.IGNORECASE),
            re.compile(r'^\s*There were?\s+\d+.*totaling.*\$.*$', re.IGNORECASE),
            re.compile(r'^\s*There was\s+\d+.*totaling.*\$.*$', re.IGNORECASE),
            re.compile(r'^\s*There were?\s+\d+.*deductions.*totaling.*\$.*$', re.IGNORECASE),
            re.compile(r'^\s*There were?\s+\d+.*purchases.*totaling.*\$.*$', re.IGNORECASE),
            re.compile(r'^\s*continued on next page\s*$', re.IGNORECASE),
            re.compile(r'^\s*Page\s+\d+\s+of\s+\d+\s*$', re.IGNORECASE),
            re.compile(r'^\s*Virtual Wallet.*Statement\s*$', re.IGNORECASE),
            re.compile(r'^\s*PNC Bank\s*$', re.IGNORECASE),
            re.compile(r'^\s*Primary account number:.*$', re.IGNORECASE),
            re.compile(r'^\s*For the period.*$', re.IGNORECASE),
            re.compile(r'^\s*Number of enclosures:.*$', re.IGNORECASE),
            re.compile(r'^\s*\$\d+\.\d{2}\s*$'),
            re.compile(r'^\s*\d{1,3}\s*$'),
            re.compile(r'^\s*-+\s*$'),
            re.compile(r'^\s*Activity Detail\s*$', re.IGNORECASE),
            re.compile(r'^\s*Deposits and Other Additions\s*$', re.IGNORECASE),
            re.compile(r'^\s*Banking/Debit Card Withdrawals and Purchases\s*$', re.IGNORECASE),
            re.compile(r'^\s*Online and Electronic Banking Deductions\s*$', re.IGNORECASE),
            re.compile(r'^\s*Daily Balance Detail\s*$', re.IGNORECASE),
            re.compile(r'^\s*There were?\s+\d+.*Banking Deductions.*totaling.*\$.*$', re.IGNORECASE),
            re.compile(r'^\d{1,2}/\d{1,2}\s+[\d,]+\.\d{2}\s+\d{1,2}/\d{1,2}\s+[\d,]+\.\d{2}', re.IGNORECASE),
            re.compile(r'^.*Date Balance Date Balance.*$', re.IGNORECASE),
            re.compile(r'^.*PIN There Date Amount Description.*$', re.IGNORECASE),
            re.compile(r'^.*Banking/Debit Card Withdrawals andPurchases.*$', re.IGNORECASE),
            re.compile(r'^.*continued on next page.*Account Number.*$', re.IGNORECASE),
            re.compile(r'^\d{1,2}/\d{1,2}\s+[\d,]+\.\d{2}$'),
            re.compile(r'^.*PNC Bank Online Banking.*$', re.IGNORECASE),
            re.compile(r'.*Date Amount Description.*', re.IGNORECASE),
            re.compile(r'.*Withdrawal.*totaling.*transactions.*', re.IGNORECASE),
            re.compile(r'.*Transaction Summary.*balance.*fees.*', re.IGNORECASE),
            re.compile(r'.*Account Number:.*continued.*Page.*', re.IGNORECASE),
            re.compile(r'.*Banking/Debit Card Withdrawals and Purchases.*continued.*', re.IGNORECASE),
            re.compile(r'.*Overdraft.*Coverage.*Protection.*', re.IGNORECASE),
            re.compile(r'.*PNC Bank.*Pittsburgh.*PA.*PO Box.*', re.IGNORECASE),
            re.compile(r'.*Write to: Customer.*Moving.*', re.IGNORECASE),
            re.compile(r'.*Para servicio.*TRS.*calls.*', re.IGNORECASE),
        ]
    
    def get_contamination_patterns(self) -> List[str]:
        """Get patterns for cleaning contaminated transaction descriptions"""
        return [
            r'PIN There Date Amount Description.*',
            r'Date Amount Description.*',
            r'Banking/Debit Card Withdrawals and Purchases.*',
            r'Account Number:.*',
            r'continued.*Page \d+ of \d+.*',
            r'Primary account.*',
            r'PNC Bank Online Banking.*',
            r'Transaction Summary.*',
            r'balance and fees.*',
            r'Average monthly.*',
            r'Beginning Deposits.*',
            r'Deposits and Other Additions.*',
            r'Overdraft.*Coverage.*',
            r'Protection.*established.*',
            r'Write to: Customer.*',
            r'Pittsburgh, PA.*',
            r'Para servicio.*',
            r'TRS.*calls.*',
            r'Visit us at pnc\.com.*',
            r'For customer.*',
            r'interest rate.*',
            r'There \d+ \d+ \d+ transactions.*',
            r'ATM.*Bank ATM.*',
            r'paid/withdrawals.*',
            r'signed transactions.*',
            r'POS PIN transactions.*',
            r'Checks Debit Card.*',
            r'Debit Card/Bankcard.*',
            r'Opted-Out.*',
            r'Please contact us.*',
            # Patterns for mid-line contamination from summary sections
            r'\s+There were?\s+\d+\s+.*?Banking.*',
            r'\s+There was\s+\d+\s+.*?Banking.*',
            r'\s+There were?\s+\d+\s+.*?Machine.*',
            r'\s+There were?\s+\d+\s+.*?totaling.*',
            r'\s+There were?\s+\d+\s+.*?deductions.*',
            r'\s+There were?\s+\d+\s+.*?purchases.*',
            r'\s+There were?\s+\d+\s+.*?withdrawals.*',
            r'\s+PIN POS purchases totaling.*',
            r'\s+Machine/Debit Card deductions.*',
            r'\s+Banking Machine.*totaling.*',
            r'\s+other Banking.*',
            # Additional patterns for continuation line contamination
            r'\s+Machine/Debit.*',
            r'\s+totaling\s+\$[\d,]+\.\d{2}.*',
            r'\s+Withdrawal\s*$',  # Remove trailing "Withdrawal"
            r'\s+withdrawals?\s*$',  # Remove trailing "withdrawal(s)"
        ]
