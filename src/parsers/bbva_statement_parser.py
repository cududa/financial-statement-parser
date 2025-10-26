import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Set, Tuple

try:
    from ..models import Transaction, StatementSummary
    from .base_parser import BaseStatementParser
    from .bbva_patterns import BBVAPatterns
    from .categorization import TransactionCategorizer
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from models import Transaction, StatementSummary
    from base_parser import BaseStatementParser
    from bbva_patterns import BBVAPatterns
    from categorization import TransactionCategorizer

logger = logging.getLogger(__name__)


class BBVAStatementParser(BaseStatementParser):
    """Parser for legacy BBVA statements that pre-date the PNC migration."""

    def __init__(self):
        self.patterns = BBVAPatterns()
        self.categorizer = TransactionCategorizer()

    def parse_account_info(self, text: str) -> Optional[StatementSummary]:
        """Extract account header information from BBVA legacy format."""
        try:
            account_match = self.patterns.ACCOUNT_PATTERN.search(text)
            account_number = account_match.group(1).strip() if account_match else "Unknown"

            # BBVA uses "Beginning August 2, 2021 - Ending September 1, 2021" format
            period_match = self.patterns.PERIOD_PATTERN.search(text)
            if not period_match:
                logger.warning("BBVA parser could not parse statement period")
                return None

            # Parse BBVA period format with full month names
            start_date = self._parse_month_day_year(
                period_match.group(1),  # Start month name
                period_match.group(2),  # Start day
                period_match.group(3)   # Start year
            )
            end_date = self._parse_month_day_year(
                period_match.group(4),  # End month name
                period_match.group(5),  # End day
                period_match.group(6)   # End year
            )

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
        except Exception as exc:
            logger.error(f"Failed to parse BBVA account info: {exc}")
            return None

    def extract_transaction_data(self, text: str, source_file: str = "") -> List[Transaction]:
        summary = self.parse_account_info(text)
        if not summary:
            logger.error("BBVA parser could not parse header; aborting transactions")
            return []

        transactions = self._extract_legacy_transactions(text, summary, source_file)
        logger.info(f"Extracted {len(transactions)} BBVA transactions")
        return transactions

    def _extract_legacy_transactions(self, text: str, summary: StatementSummary, source_file: str = "") -> List[Transaction]:
        transactions: List[Transaction] = []
        seen_keys: Set[Tuple[str, str, str, int]] = set()

        lines = text.split('\n')
        current_page = 1
        i = 0
        # Use BBVA-specific stop patterns from the patterns class
        summary_stop_prefixes = self.patterns.STOP_PATTERNS

        while i < len(lines):
            raw_line = lines[i]
            line = raw_line.strip()
            if not line:
                i += 1
                continue

            if line.startswith('--- PAGE'):
                try:
                    current_page = int(line.split('PAGE')[1].split('---')[0].strip())
                except Exception:
                    pass
                i += 1
                continue

            date_match = self.patterns.DATE_PATTERN.match(line)
            if not date_match:
                i += 1
                continue

            date_fragment = date_match.group(1)
            raw_lines = [raw_line]
            combined = line

            j = i + 1
            while j < len(lines):
                lookahead_raw = lines[j]
                lookahead = lookahead_raw.strip()
                if not lookahead:
                    j += 1
                    continue
                if lookahead.startswith('--- PAGE') or self.patterns.DATE_PATTERN.match(lookahead):
                    break
                normalized = re.sub(r'\s+', '', lookahead.upper())
                if any(normalized.startswith(prefix.replace(' ', '').upper()) for prefix in summary_stop_prefixes):
                    break
                raw_lines.append(lookahead_raw)
                combined += ' ' + lookahead
                j += 1

            amounts = self.patterns.AMOUNT_PATTERN.findall(combined)
            if not amounts:
                i = j
                continue

            transaction_amount_str, balance_amount_str = self._split_amounts(amounts)
            transaction_amount = Decimal(transaction_amount_str.replace(',', ''))

            description_portion = re.sub(r'^' + re.escape(date_fragment), '', combined, count=1).strip()
            description_portion = self._remove_amount_from_text(description_portion, transaction_amount_str)
            if balance_amount_str:
                description_portion = self._remove_amount_from_text(description_portion, balance_amount_str)
            description_portion = re.sub(r'\s+', ' ', description_portion).strip()

            transaction_type = self._infer_transaction_type(description_portion)
            normalized_date = self._normalize_date(date_fragment)
            transaction_year = self._infer_year(normalized_date, summary)
            month = int(normalized_date.split('/')[0])

            card_last_four = self._extract_card_last_four(combined)
            # Include line position to distinguish legitimate same-day, same-amount transactions
            key = (normalized_date, transaction_amount_str, description_portion.upper(), i)
            if key in seen_keys:
                i = j
                continue
            seen_keys.add(key)

            transaction = Transaction(
                date=normalized_date,
                year=transaction_year,
                month=month,
                amount=transaction_amount,
                transaction_type=transaction_type,
                description=description_portion,
                merchant='Unknown',
                card_last_four=card_last_four,
                category=self.categorizer.categorize_transaction(description_portion),
                raw_lines=raw_lines,
                page_number=current_page,
                source_file=source_file
            )
            transactions.append(transaction)
            i = j

        return transactions

    def _split_amounts(self, amounts: List[str]) -> Tuple[str, Optional[str]]:
        if len(amounts) == 1:
            return amounts[0], None

        cleaned = [amt for amt in amounts]
        transaction_amount = cleaned[-2] if len(cleaned) >= 2 else cleaned[0]
        balance_amount = cleaned[-1]

        if transaction_amount == balance_amount and len(cleaned) == 2:
            balance_amount = None

        return transaction_amount, balance_amount

    def _remove_amount_from_text(self, text: str, amount_str: str) -> str:
        pattern = r'(?:\$\s*)?' + re.escape(amount_str)
        return re.sub(pattern, '', text, count=1).strip()

    def _infer_transaction_type(self, description: str) -> str:
        upper = description.upper()
        credit_keywords = ['DEPOSIT', 'CREDIT', 'ACH', 'PAYROLL', 'REFUND']
        if any(keyword in upper for keyword in credit_keywords):
            return 'CREDIT'
        return 'DEBIT'

    def _normalize_date(self, date_fragment: str) -> str:
        month, day = date_fragment.split('/')
        return f"{int(month):02d}/{int(day):02d}"

    def _infer_year(self, date_str: str, summary: StatementSummary) -> int:
        month = int(date_str.split('/')[0])
        start = summary.statement_period_start
        end = summary.statement_period_end

        if start.year == end.year:
            return start.year

        if month >= start.month:
            return start.year
        return end.year

    def _parse_month_day_year(self, month_str: str, day_str: str, year_str: str) -> datetime:
        month_str = month_str.strip()
        day = int(day_str)
        year = int(year_str)

        try:
            return datetime.strptime(f"{month_str} {day} {year}", '%B %d %Y')
        except ValueError:
            return datetime.strptime(f"{month_str} {day} {year}", '%b %d %Y')

    def _extract_card_last_four(self, text: str) -> str:
        candidate = re.search(r'X{2,}(\d{4})', text.replace(' ', ''))
        if candidate:
            return candidate.group(1)
        candidate = re.search(r'#(\d{3,4})', text)
        if candidate:
            return candidate.group(1)[-4:]
        return ''
