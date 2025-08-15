"""
Enhanced PNC statement parser with layout-aware parsing.
Implements ChatGPT suggestions for coordinate-based filtering and validation.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, Dict, Any
import logging
from pathlib import Path

from .models import Transaction, StatementSummary
from .layout_analyzer import LayoutAnalyzer, TextElement
from .pnc_parser import PNCStatementParser

logger = logging.getLogger(__name__)


class EnhancedPNCParser(PNCStatementParser):
    """
    Enhanced parser that combines text-based parsing with layout awareness.
    Implements coordinate-based filtering and improved validation.
    """
    
    def __init__(self):
        super().__init__()
        self.layout_analyzer = LayoutAnalyzer()
        self.column_bands = None
        
        # Enhanced amount pattern to handle leading dots
        self.ENHANCED_AMOUNT_PATTERN = re.compile(r'(\.?\d{1,3}(?:,\d{3})*\.?\d{0,2})')
        
        # Patterns for section total extraction
        self.SECTION_TOTAL_PATTERNS = {
            'deposits': re.compile(r'There were?\s+\d+.*Deposits.*totaling\s*\$?([\d,]+\.\d{2})', re.IGNORECASE),
            'withdrawals': re.compile(r'There was?\s+\d+.*Withdrawal.*totaling\s*\$?([\d,]+\.\d{2})', re.IGNORECASE),
            'online_banking': re.compile(r'There were?\s+\d+.*Banking Deductions.*totaling\s*\$?([\d,]+\.\d{2})', re.IGNORECASE)
        }
    
    def extract_transaction_data_enhanced(self, pdf_path: Path) -> Tuple[List[Transaction], Dict[str, Any]]:
        """
        Enhanced extraction using layout-aware parsing.
        Returns transactions and comprehensive validation data.
        """
        # Extract text with coordinates
        text_elements = self.layout_analyzer.extract_text_with_coordinates(pdf_path)
        
        # Detect column boundaries
        self.column_bands = self.layout_analyzer.detect_column_bands(text_elements)
        if not self.column_bands:
            logger.warning("Could not detect column bands, falling back to text-only parsing")
            return self._fallback_to_text_parsing(pdf_path)
        
        # Filter elements by coordinates
        categorized_elements = self.layout_analyzer.filter_by_coordinates(text_elements, self.column_bands)
        
        # Reconstruct text from coordinate-filtered elements  
        filtered_lines = self.layout_analyzer.reconstruct_lines_from_coordinates(categorized_elements['main_table'])
        filtered_text = '\n'.join(filtered_lines)
        
        # Parse account info for context
        summary = self.parse_account_info(filtered_text)
        if not summary:
            logger.error("Could not parse statement header")
            return [], {}
        
        # Extract transactions from each section
        transactions = []
        
        # Extract deposits
        deposits = self._extract_deposits_section_enhanced(filtered_text, summary, text_elements)
        transactions.extend(deposits)
        
        # Extract withdrawals
        withdrawals = self._extract_withdrawals_section_enhanced(filtered_text, summary, text_elements)
        transactions.extend(withdrawals)
        
        # Extract online banking
        online_banking = self._extract_online_banking_section_enhanced(filtered_text, summary, text_elements)
        transactions.extend(online_banking)
        
        # Perform enhanced validation
        validation_data = self._perform_enhanced_validation(transactions, summary, filtered_text)
        
        logger.info(f"Enhanced extraction: {len(transactions)} transactions with validation")
        return transactions, validation_data
    
    def _fallback_to_text_parsing(self, pdf_path: Path) -> Tuple[List[Transaction], Dict[str, Any]]:
        """Fallback to original text-based parsing if layout detection fails"""
        logger.info("Using fallback text-based parsing")
        
        # Use original PDF ingester
        from .pdf_ingester import PDFIngester
        ingester = PDFIngester()
        
        pages_text = ingester.extract_text_content(pdf_path)
        combined_text = ingester.handle_multi_page_documents(pages_text)
        
        transactions = self.extract_transaction_data(combined_text)
        summary = self.parse_account_info(combined_text)
        
        # Basic validation
        validation_data = {
            'method': 'text_fallback',
            'section_totals': {},
            'balance_check': None,
            'warnings': ['Layout detection failed, used text-only parsing']
        }
        
        return transactions, validation_data
    
    def _reconstruct_filtered_text(self, main_table_elements: List[TextElement]) -> str:
        """Reconstruct text from coordinate-filtered elements"""
        lines = self.layout_analyzer.reconstruct_lines_from_coordinates(main_table_elements)
        return '\n'.join(lines)
    
    def _extract_deposits_section_enhanced(self, filtered_text: str, summary: StatementSummary, 
                                         _text_elements: List[TextElement]) -> List[Transaction]:
        """Enhanced deposits extraction with coordinate awareness"""
        # Use original section extraction but with enhanced amount parsing
        deposits = self._extract_deposits_section(filtered_text, summary)
        
        # Enhance amount parsing for each transaction
        for transaction in deposits:
            transaction.amount = self._parse_enhanced_amount(str(transaction.amount))
        
        return deposits
    
    def _extract_withdrawals_section_enhanced(self, filtered_text: str, summary: StatementSummary,
                                            _text_elements: List[TextElement]) -> List[Transaction]:
        """Enhanced withdrawals extraction with coordinate awareness"""
        withdrawals = self._extract_withdrawals_section(filtered_text, summary)
        
        # Enhance amount parsing
        for transaction in withdrawals:
            transaction.amount = self._parse_enhanced_amount(str(transaction.amount))
        
        return withdrawals
    
    def _extract_online_banking_section_enhanced(self, filtered_text: str, summary: StatementSummary,
                                               _text_elements: List[TextElement]) -> List[Transaction]:
        """Enhanced online banking extraction with coordinate awareness"""
        online_banking = self._extract_online_banking_section(filtered_text, summary)
        
        # Enhance amount parsing
        for transaction in online_banking:
            transaction.amount = self._parse_enhanced_amount(str(transaction.amount))
        
        return online_banking
    
    def _parse_enhanced_amount(self, amount_str: str) -> Decimal:
        """
        Enhanced amount parsing that handles leading dots and other edge cases.
        Implements ChatGPT suggestion for .14 → 0.14 conversion.
        """
        if not amount_str:
            return Decimal('0')
        
        # Clean the amount string
        cleaned = amount_str.strip().replace('$', '').replace(',', '')
        
        # Handle leading dot case (.14 → 0.14)
        if cleaned.startswith('.'):
            cleaned = '0' + cleaned
        
        # Handle trailing dot case (14. → 14.00)
        if cleaned.endswith('.'):
            cleaned = cleaned + '00'
        
        # Handle cases like "14" → "14.00"
        if '.' not in cleaned and cleaned.isdigit():
            cleaned = cleaned + '.00'
        
        try:
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            logger.warning(f"Could not parse amount: '{amount_str}' → '{cleaned}'")
            return Decimal('0')
    
    def _perform_enhanced_validation(self, transactions: List[Transaction], 
                                   summary: StatementSummary, filtered_text: str) -> Dict[str, Any]:
        """
        Perform comprehensive validation including section total reconciliation.
        Implements ChatGPT validation suggestions.
        """
        validation_data = {
            'method': 'layout_aware',
            'section_totals': {},
            'balance_check': None,
            'warnings': [],
            'reconciliation_passed': True
        }
        
        # Extract section totals from statement text
        section_totals = self._extract_section_totals(filtered_text)
        validation_data['section_totals'] = section_totals
        
        # Calculate parsed totals by section
        parsed_totals = self._calculate_parsed_totals(transactions)
        
        # Compare section totals
        reconciliation_results = self._reconcile_section_totals(section_totals, parsed_totals)
        validation_data.update(reconciliation_results)
        
        # Perform balance check
        balance_check = self._perform_ledger_balance_check(transactions, summary, filtered_text)
        validation_data['balance_check'] = balance_check
        
        # Check for overall reconciliation
        if not all(reconciliation_results.get('section_reconciliation', {}).values()):
            validation_data['reconciliation_passed'] = False
            validation_data['warnings'].append("Section totals do not match parsed amounts")
        
        if not balance_check.get('balance_matches', True):
            validation_data['reconciliation_passed'] = False
            validation_data['warnings'].append("Ledger balance check failed")
        
        return validation_data
    
    def _extract_section_totals(self, text: str) -> Dict[str, Decimal]:
        """Extract section totals from statement summary text"""
        section_totals = {}
        
        for section, pattern in self.SECTION_TOTAL_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                try:
                    # Take the last match (most recent/relevant)
                    amount_str = matches[-1].replace(',', '')
                    section_totals[section] = Decimal(amount_str)
                    logger.info(f"Found {section} total: ${amount_str}")
                except (InvalidOperation, ValueError):
                    logger.warning(f"Could not parse {section} total: {matches[-1]}")
        
        return section_totals
    
    def _calculate_parsed_totals(self, transactions: List[Transaction]) -> Dict[str, Decimal]:
        """Calculate totals from parsed transactions by type"""
        parsed_totals = {
            'deposits': Decimal('0'),
            'withdrawals': Decimal('0'),
            'online_banking': Decimal('0')
        }
        
        for transaction in transactions:
            if transaction.transaction_type == 'CREDIT':
                parsed_totals['deposits'] += transaction.amount
            elif 'online' in transaction.category.lower() or 'ach' in transaction.description.lower():
                parsed_totals['online_banking'] += transaction.amount
            else:
                parsed_totals['withdrawals'] += transaction.amount
        
        return parsed_totals
    
    def _reconcile_section_totals(self, statement_totals: Dict[str, Decimal], 
                                parsed_totals: Dict[str, Decimal]) -> Dict[str, Any]:
        """Compare statement totals with parsed totals"""
        reconciliation = {
            'section_reconciliation': {},
            'total_differences': {}
        }
        
        for section in statement_totals:
            if section in parsed_totals:
                statement_amount = statement_totals[section]
                parsed_amount = parsed_totals[section]
                difference = abs(statement_amount - parsed_amount)
                
                # Allow small rounding differences (< $0.01)
                matches = difference < Decimal('0.01')
                
                reconciliation['section_reconciliation'][section] = matches
                reconciliation['total_differences'][section] = {
                    'statement': float(statement_amount),
                    'parsed': float(parsed_amount),
                    'difference': float(difference),
                    'matches': matches
                }
                
                if matches:
                    logger.info(f"✓ {section} totals match: ${statement_amount}")
                else:
                    logger.warning(f"✗ {section} mismatch: Statement ${statement_amount} vs Parsed ${parsed_amount}")
        
        return reconciliation
    
    def _perform_ledger_balance_check(self, transactions: List[Transaction], 
                                    _summary: StatementSummary, text: str) -> Dict[str, Any]:
        """
        Perform ledger balance verification: opening + credits - debits = closing.
        Implements ChatGPT balance check suggestion.
        """
        balance_check = {
            'balance_matches': True,
            'opening_balance': None,
            'closing_balance': None,
            'calculated_balance': None,
            'difference': None
        }
        
        # Extract opening and closing balances from statement
        opening_balance = self._extract_opening_balance(text)
        closing_balance = self._extract_closing_balance(text)
        
        if opening_balance is None or closing_balance is None:
            balance_check['balance_matches'] = None
            balance_check['error'] = "Could not extract opening/closing balances"
            return balance_check
        
        # Calculate balance from transactions
        total_credits = sum(t.amount for t in transactions if t.transaction_type == 'CREDIT')
        total_debits = sum(t.amount for t in transactions if t.transaction_type == 'DEBIT')
        
        calculated_closing = opening_balance + total_credits - total_debits
        difference = abs(calculated_closing - closing_balance)
        
        balance_check.update({
            'opening_balance': float(opening_balance),
            'closing_balance': float(closing_balance),
            'calculated_balance': float(calculated_closing),
            'difference': float(difference),
            'balance_matches': difference < Decimal('0.01')  # Allow small rounding
        })
        
        if balance_check['balance_matches']:
            logger.info(f"✓ Balance check passed: {opening_balance} + {total_credits} - {total_debits} = {calculated_closing}")
        else:
            logger.warning(f"✗ Balance mismatch: Expected {closing_balance}, calculated {calculated_closing}")
        
        return balance_check
    
    def _extract_opening_balance(self, text: str) -> Optional[Decimal]:
        """Extract opening balance from statement text"""
        patterns = [
            re.compile(r'Opening Balance.*?\$?([\d,]+\.\d{2})', re.IGNORECASE),
            re.compile(r'Beginning Balance.*?\$?([\d,]+\.\d{2})', re.IGNORECASE),
            re.compile(r'Previous Balance.*?\$?([\d,]+\.\d{2})', re.IGNORECASE)
        ]
        
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                try:
                    return Decimal(match.group(1).replace(',', ''))
                except (InvalidOperation, ValueError):
                    continue
        
        return None
    
    def _extract_closing_balance(self, text: str) -> Optional[Decimal]:
        """Extract closing balance from statement text"""
        patterns = [
            re.compile(r'Closing Balance.*?\$?([\d,]+\.\d{2})', re.IGNORECASE),
            re.compile(r'Ending Balance.*?\$?([\d,]+\.\d{2})', re.IGNORECASE),
            re.compile(r'Current Balance.*?\$?([\d,]+\.\d{2})', re.IGNORECASE)
        ]
        
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                try:
                    return Decimal(match.group(1).replace(',', ''))
                except (InvalidOperation, ValueError):
                    continue
        
        return None