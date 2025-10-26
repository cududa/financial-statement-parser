"""
PNC Statement Parser Package

This package provides modular parsing capabilities for bank statements.
The architecture is designed to support multiple bank formats through 
inheritance from BaseStatementParser.

Main Components:
- BaseStatementParser: Abstract interface for all bank parsers
- PNCStatementParser: PNC-specific implementation
- PNCPatterns: Regex patterns for PNC statement parsing
- SectionExtractor: Handles different statement sections
- TransactionParser: Core transaction parsing logic
- TransactionCategorizer: Auto-categorization with JSON patterns
- TextCleaner: Text cleaning and validation utilities
- MerchantExtractor: Merchant information extraction

Example Usage:
    from parsers import PNCStatementParser
    
    parser = PNCStatementParser()
    summary = parser.parse_account_info(statement_text)
    transactions = parser.extract_transaction_data(statement_text)
"""

from .base_parser import BaseStatementParser
from .pnc_statement_parser import PNCStatementParser
from .bbva_statement_parser import BBVAStatementParser
from .pnc_patterns import PNCPatterns
from .section_extractor import SectionExtractor
from .transaction_parser import TransactionParser
from .categorization import TransactionCategorizer
from .text_utils import TextCleaner, MerchantExtractor

__all__ = [
    'BaseStatementParser',
    'PNCStatementParser', 
    'BBVAStatementParser',
    'PNCPatterns',
    'SectionExtractor',
    'TransactionParser',
    'TransactionCategorizer',
    'TextCleaner',
    'MerchantExtractor'
]
