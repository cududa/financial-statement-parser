import re
from typing import List


class BBVAPatterns:
    """
    Pattern definitions specific to BBVA legacy statements (pre-PNC migration).
    BBVA statements used from 2021 and earlier.
    """

    def __init__(self):
        # ===== DATE PATTERN =====
        # BBVA uses M/D or MM/DD format (no year in transaction lines)
        # Example: "9/27", "8/31", "10/1"
        self.DATE_PATTERN = re.compile(r'^(\d{1,2}/\d{1,2})\s+')

        # ===== AMOUNT PATTERN =====
        # BBVA includes dollar sign: $22.63, $1,347.42
        # Captures: $123.45 → "123.45"
        self.AMOUNT_PATTERN = re.compile(r'\$(\d{1,3}(?:,\d{3})*\.\d{2})')

        # ===== TRANSACTION TYPE PATTERNS =====
        # BBVA-specific transaction identifiers
        self.CHECKCARD_PURCHASE = re.compile(
            r'CHECKCARD PURCHASE - (.+)',
            re.IGNORECASE
        )
        self.DEBIT_FOR_CHECKCARD = re.compile(
            r'DEBIT FOR CHECKCARD\s+XXXXXX(\d{4})\s+(\d{2}/\d{2}/\d{2})',
            re.IGNORECASE
        )
        self.ISA_FEE = re.compile(r'ISA FEE', re.IGNORECASE)

        # ===== CARD NUMBER PATTERN =====
        # BBVA format: "CARD XXXXXX4009" (6 X's + 4 digits)
        # Captures: 4009
        self.CARD_NUMBER_PATTERN = re.compile(
            r'CARD\s+XXXXXX(\d{4})',
            re.IGNORECASE
        )

        # ===== SERIAL NUMBER PATTERN =====
        # Format: "VISA 8400360008/31/21"
        # Groups: (1) network, (2) serial, (3) date
        self.SERIAL_NUMBER_PATTERN = re.compile(
            r'(VISA|MASTERCARD|DISCOVER|MC)\s+(\d+)(\d{2}/\d{2}/\d{2})',
            re.IGNORECASE
        )

        # ===== HEADER PATTERNS =====
        # Account number: "Primary Account: XXXXXXXXXX" or "PrimaryAccount:XXXXXXXXXX" (PyPDF2 variant)
        # BBVA uses 10 digits, no dashes
        self.ACCOUNT_PATTERN = re.compile(
            r'Primary\s*Account:\s*(\d{10})',
            re.IGNORECASE
        )

        # Statement period: "Beginning August 2, 2021 - Ending September 1, 2021"
        # or "Beginning September 2,2021-EndingOctober1,2021" (PyPDF2 variant without spaces)
        # Groups: (1) start month, (2) start day, (3) start year,
        #         (4) end month, (5) end day, (6) end year
        self.PERIOD_PATTERN = re.compile(
            r'Beginning\s*([A-Za-z]+)\s*(\d{1,2}),?\s*(\d{4})\s*-?\s*Ending\s*([A-Za-z]+)\s*(\d{1,2}),?\s*(\d{4})',
            re.IGNORECASE
        )

        # Page number: "Page 6 of 7"
        self.PAGE_PATTERN = re.compile(r'Page\s+(\d+)\s+of\s+(\d+)')

        # ===== STOP PATTERNS =====
        # Text patterns that indicate end of transaction section
        self.STOP_PATTERNS = [
            'Ending Balance on',
            'T o t a l s',  # Spaced out in BBVA format
            'P l e a s e n o t e',
            'P e r i o d i c N o n',
            'Total overdraft',
            'How to Balance Your Account',
            'HowtoBalanceYourAccount',
            'Step1',
            'Step2',
            'Step3',
            'Step4',
            'Step5',
            'Change of Address',
            'ChangeofAddress',
            'Electronic Transfers',
            'ElectronicTransfers',
            'Overdraft Protection',
            'OverdraftProtection',
            'BBVA USA is a Member FDIC',
            'BBVAUSAisaMemberFDIC',
            'BBVAUSA',
            'Calculation of Interest',
            'In esaC of srorrE',  # Mirrored text sometimes
        ]

        # ===== IGNORE PATTERNS =====
        # Compiled regex patterns for lines to skip
        self.IGNORE_PATTERNS = self._build_ignore_patterns()

    def _build_ignore_patterns(self) -> List[re.Pattern]:
        """Build list of patterns for filtering extraneous text"""
        return [
            # Page headers (with or without spaces - PyPDF2 variant)
            re.compile(r'^\s*Page\s*\d+\s*of\s*\d+\s*$', re.IGNORECASE),
            re.compile(r'^\s*Page\d+of\d+\s*$', re.IGNORECASE),

            # Account info lines (with or without spaces)
            re.compile(r'^\s*Primary\s*Account:\s*\d+\s*$', re.IGNORECASE),
            re.compile(r'^\s*PrimaryAccount:\s*\d+\s*$', re.IGNORECASE),
            re.compile(r'^\s*Beginning.*Ending.*\d{4}\s*$', re.IGNORECASE),

            # Column headers (with or without spaces)
            re.compile(r'^\s*Check/.*Serial\s*#.*Description.*$', re.IGNORECASE),
            re.compile(r'^\s*Date\s*\*.*Credits.*Debits.*Balance\s*$', re.IGNORECASE),
            re.compile(r'^\s*Check/\s*Deposits/\s*Withdrawals/.*$', re.IGNORECASE),

            # Summary sections
            re.compile(r'^\s*Ending Balance on.*$', re.IGNORECASE),
            re.compile(r'^\s*T o t a l s.*\$.*$', re.IGNORECASE),  # Spaced format
            re.compile(r'^\s*Totals\s+\$.*$', re.IGNORECASE),  # Non-spaced format

            # Footer text
            re.compile(r'^\s*P l e a s e n o t e.*$', re.IGNORECASE),
            re.compile(r'^\s*\* T h e D a t e.*$', re.IGNORECASE),
            re.compile(r'^\s*P e r i o d i c.*$', re.IGNORECASE),

            # Overdraft summary
            re.compile(r'^\s*Total overdraft.*$', re.IGNORECASE),
            re.compile(r'^\s*NSF-returned.*$', re.IGNORECASE),
            re.compile(r'^\s*Total this Period.*$', re.IGNORECASE),
            re.compile(r'^\s*Total \d{4} YTD.*$', re.IGNORECASE),

            # Standalone amounts
            re.compile(r'^\s*\$\s*\d+\.\d{2}\s*$'),

            # Bank branding
            re.compile(r'^.*BBVA.*Member FDIC.*$', re.IGNORECASE),
            re.compile(r'^.*BBVA.*trademark.*$', re.IGNORECASE),

            # Instructions sections
            re.compile(r'^.*How to Balance.*$', re.IGNORECASE),
            re.compile(r'^\s*Step\d+.*$', re.IGNORECASE),

            # Blank or whitespace-only lines
            re.compile(r'^\s*$'),
        ]

    def get_contamination_patterns(self) -> List[str]:
        """Get patterns for cleaning contaminated transaction descriptions"""
        return [
            # Header contamination (with or without spaces - PyPDF2 variant)
            r'Date\s*\*\s*Serial\s*#\s*Description.*',
            r'Credits\s*Debits\s*Balance.*',
            r'Check/\s*Deposits/\s*Withdrawals/.*',
            r'Primary\s*Account:.*',
            r'PrimaryAccount:.*',

            # Summary contamination
            r'Ending\s*Balance\s*on.*',
            r'EndingBalance.*',
            r'T\s*o\s*t\s*a\s*l\s*s.*',
            r'P\s*l\s*e\s*a\s*s\s*e\s*n\s*o\s*t\s*e.*',
            r'\*\s*T\s*h\s*e\s*D\s*a\s*t\s*e.*',

            # Footer contamination
            r'How\s*to\s*Balance.*',
            r'HowtoBalance.*',
            r'Step\d+.*',
            r'BBVA.*FDIC.*',
            r'Overdraft\s*Protection.*',
            r'OverdraftProtection.*',
            r'Electronic\s*Transfers.*',
            r'ElectronicTransfers.*',

            # Page markers (with or without spaces)
            r'Page\s*\d+\s*of\s*\d+.*',
            r'Page\d+of\d+.*',
            r'---\s*PAGE\s*\d+\s*---.*',

            # Trailing amounts that are balances, not part of description
            r'\s+\$[\d,]+\.\d{2}\s*$',
        ]
