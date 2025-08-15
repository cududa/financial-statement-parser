import re
import logging
from typing import List

try:
    from .pnc_patterns import PNCPatterns
except ImportError:
    from pnc_patterns import PNCPatterns

logger = logging.getLogger(__name__)


class TextCleaner:
    """
    Utilities for cleaning and validating transaction text.
    Handles contamination removal and extraneous text filtering.
    """
    
    def __init__(self, patterns: PNCPatterns):
        self.patterns = patterns
        self.contamination_patterns = patterns.get_contamination_patterns()
    
    def clean_description(self, description: str) -> str:
        """Clean transaction description of contaminated header/footer text"""
        if not description:
            return description
            
        cleaned = description
        
        # First, fix broken words from PDF extraction
        cleaned = re.sub(r'DebitCard Credit', 'Debit Card Credit', cleaned)
        cleaned = re.sub(r'DebitCard Purchase', 'Debit Card Purchase', cleaned)
        cleaned = re.sub(r'RecurringDebit Card', 'Recurring Debit Card', cleaned)
        cleaned = re.sub(r'POSPurchase', 'POS Purchase', cleaned)
        cleaned = re.sub(r'Credit(\w)', r'Credit \1', cleaned)
        cleaned = re.sub(r'DirectDeposit', 'Direct Deposit', cleaned)
        
        # Fix missing spaces between card numbers and transaction types
        cleaned = re.sub(r'(\d{4})Debit Card', r'\1 Debit Card', cleaned)
        cleaned = re.sub(r'(\d{4})Recurring', r'\1 Recurring', cleaned)
        
        # Fix concatenated phone numbers and locations
        cleaned = re.sub(r'\.Com(\d{10})', r'.Com \1', cleaned)  # Walmart.Com8009666546 → Walmart.Com 8009666546
        cleaned = re.sub(r'(\d{10})([A-Z]{2,})', r'\1 \2', cleaned)  # 8009666546BENTONVILLE → 8009666546 BENTONVILLE  
        cleaned = re.sub(r'([A-Z]+)AR$', r'\1 AR', cleaned)  # BENTONVILLEAR → BENTONVILLE AR
        cleaned = re.sub(r'([A-Z]+)LLC', r'\1 LLC', cleaned)  # ACMELLC → ACME LLC
        
        # Then remove contamination patterns
        for pattern in self.contamination_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up multiple spaces and trim
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # If cleaning removed most of the description, return a minimal version
        if len(cleaned) < 10 and len(description) > 50:
            # Try to extract just the merchant part before contamination starts
            parts = description.split()
            for i, part in enumerate(parts):
                if any(contamination in part.upper() for contamination in 
                       ['DATE', 'AMOUNT', 'DESCRIPTION', 'BANKING', 'ACCOUNT', 'CONTINUED']):
                    cleaned = ' '.join(parts[:i]).strip()
                    break
        
        return cleaned if cleaned else "Unknown Transaction"
    
    def is_extraneous_line(self, line: str) -> bool:
        """
        Check if a line should be ignored as extraneous text.
        Returns True if line matches any ignore pattern.
        """
        for pattern in self.patterns.IGNORE_PATTERNS:
            if pattern.match(line):
                logger.debug(f"Ignoring extraneous line: '{line}'")
                return True
        
        # Additional heuristics for extraneous content
        stripped = line.strip()
        
        # Ignore very short lines that are likely location suffixes (but not phone numbers)
        if len(stripped) <= 3 and stripped.isalpha():
            logger.debug(f"Ignoring short location line: '{line}'")
            return True
        
        # Don't filter out potential phone number continuation lines (4-10 digits)
        if re.match(r'^\d{4,10}$', stripped):
            return False
        
        # Ignore standalone state abbreviations or similar
        if len(stripped) == 2 and stripped.isupper() and stripped.isalpha():
            logger.debug(f"Ignoring state abbreviation: '{line}'")
            return True
        
        # Ignore lines that look like account summary headers
        if 'ACCOUNT SUMMARY' in stripped.upper() or 'BALANCE SUMMARY' in stripped.upper():
            logger.debug(f"Ignoring account summary header: '{line}'")
            return True
        
        # Ignore lines with balance/summary keywords
        summary_keywords = ['opening balance', 'closing balance', 'total deposits', 'total withdrawals']
        if any(keyword in stripped.lower() for keyword in summary_keywords):
            logger.debug(f"Ignoring summary line: '{line}'")
            return True
        
        return False
    
    def is_valid_merchant_continuation(self, line: str) -> bool:
        """
        Check if a line is valid merchant continuation data.
        Should capture merchant names, phone numbers, addresses, but avoid summary text.
        """
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            return False
        
        # Skip lines that look like contamination/summary text
        contamination_keywords = [
            'there were', 'there was', 'totaling', 'purchases totaling', 
            'deductions totaling', 'withdrawals totaling', 'banking machine',
            'pin pos', 'machine/debit', 'other banking', 'continued on next page'
        ]
        
        if any(keyword in stripped.lower() for keyword in contamination_keywords):
            return False
        
        # Skip standalone dollar amounts (these are summary totals)
        if re.match(r'^\$[\d,]+\.\d{2}\.?$', stripped):
            return False
        
        # Accept lines that look like merchant data:
        # - Phone numbers (96665, 8886880458, etc.)
        # - Addresses (BENTONVILLEAR, LAKEWOOD, etc.)  
        # - Merchant identifiers (Gsuite_lum, etc.)
        # - Alphanumeric codes
        
        # Special case: Accept phone number continuation lines (4-10 digit numbers)
        if re.match(r'^\d{4,10}$', stripped):
            return True
        
        # Accept merchant address/location lines (mostly letters, 2+ chars for state codes)
        if re.match(r'^[A-Za-z\s]{2,}$', stripped):
            return True
        
        # Accept if it's mostly alphanumeric (merchant names, codes, phone numbers)
        if re.match(r'^[A-Za-z0-9\s\-_\.]+$', stripped) and len(stripped.strip()) >= 3:
            return True
        
        return False


class MerchantExtractor:
    """
    Utilities for extracting merchant information from transaction descriptions.
    """
    
    def __init__(self, patterns: PNCPatterns):
        self.patterns = patterns
    
    def extract_merchant_info(self, description: str, transaction_type: str) -> tuple[str, str]:
        """Extract merchant name and card info from description"""
        merchant = "Unknown"
        card_last_four = ""
        
        if transaction_type == 'DEBIT':
            # Check for debit card purchase patterns
            debit_match = self.patterns.DEBIT_CARD_PURCHASE.search(description)
            if debit_match:
                card_last_four = debit_match.group(1)
                merchant = debit_match.group(2).strip()
            
            # Check for recurring payment patterns  
            recurring_match = self.patterns.RECURRING_PAYMENT.search(description)
            if recurring_match:
                card_last_four = recurring_match.group(1)
                merchant = recurring_match.group(2).strip()
            
            # Check for POS purchase patterns
            pos_match = self.patterns.POS_PURCHASE.search(description)
            if pos_match:
                merchant = pos_match.group(1).strip()
        
        elif transaction_type == 'CREDIT':
            # Check for direct deposit
            deposit_match = self.patterns.DIRECT_DEPOSIT.search(description)
            if deposit_match:
                merchant_text = deposit_match.group(1).strip()
                # If this is a payroll deposit, extract company name after "Payroll"
                if merchant_text.startswith('Payroll '):
                    # Extract everything after "Payroll " as the company name
                    company_parts = merchant_text[8:].split()  # Remove "Payroll " prefix
                    # Take first 2 words as company name to avoid account numbers
                    if len(company_parts) >= 2:
                        merchant = ' '.join(company_parts[:2])
                    else:
                        merchant = company_parts[0] if company_parts else merchant_text
                else:
                    merchant = merchant_text
            
            # Check for debit card credit (refunds)
            credit_match = self.patterns.DEBIT_CARD_CREDIT.search(description)
            if credit_match:
                merchant = credit_match.group(1).strip()
        
        # Clean up merchant name
        if merchant != "Unknown":
            # Remove common suffixes and clean up
            merchant = re.sub(r'\s+', ' ', merchant).strip()
            # Take first part before location info
            merchant_parts = merchant.split()
            if len(merchant_parts) > 2:
                merchant = ' '.join(merchant_parts[:2])
        
        return merchant, card_last_four