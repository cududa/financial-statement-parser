import pdfplumber
import PyPDF2
from collections import defaultdict
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class PDFIngester:
    """
    PDF text extraction and validation module.
    Handles PDF ingestion with fallback methods for reliable text extraction.
    """
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def validate_pdf_format(self, file_path: Path) -> bool:
        """Validate that file is a readable PDF"""
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return False
            
        if file_path.suffix.lower() not in self.supported_formats:
            logger.error(f"Unsupported file format: {file_path.suffix}")
            return False
            
        try:
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) == 0:
                    logger.error(f"PDF has no pages: {file_path}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Failed to open PDF {file_path}: {e}")
            return False
    
    def extract_text_content(self, file_path: Path) -> List[str]:
        """
        Extract text from all pages using pdfplumber.
        Returns list of strings, one per page.
        """
        if not self.validate_pdf_format(file_path):
            raise ValueError(f"Invalid PDF file: {file_path}")
        
        pages_text = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = self._extract_page_text(page)
                    if text:
                        pages_text.append(text)
                        logger.debug(f"Extracted text from page {page_num}: {len(text)} characters")
                    else:
                        logger.warning(f"No text found on page {page_num}")
                        pages_text.append("")
                        
        except Exception as e:
            logger.error(f"pdfplumber failed for {file_path}: {e}")
            # Fallback to PyPDF2
            pages_text = self._extract_with_pypdf2(file_path)
            
        return pages_text
    
    def _extract_with_pypdf2(self, file_path: Path) -> List[str]:
        """Fallback text extraction using PyPDF2"""
        logger.info(f"Using PyPDF2 fallback for {file_path}")
        pages_text = []

        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    pages_text.append(text or "")
                    logger.debug(f"PyPDF2 extracted page {page_num}: {len(text or '')} characters")

        except Exception as e:
            logger.error(f"PyPDF2 also failed for {file_path}: {e}")
            raise

        return pages_text

    def _extract_page_text(self, page) -> str:
        """Extract text for a single page, normalizing mirrored text layouts when detected"""
        try:
            text = page.extract_text()
        except Exception as exc:
            logger.debug(f"pdfplumber failed to extract text via default method: {exc}")
            text = None

        if text:
            return text if not self._is_mirrored_page(page) else self._reconstruct_mirrored_page(page)

        # No text via the standard path, attempt reconstruction directly
        return self._reconstruct_mirrored_page(page)

    def _is_mirrored_page(self, page) -> bool:
        """Detect pages where text is mirrored horizontally (characters ordered right-to-left)."""
        try:
            chars = page.chars
        except Exception:
            return False

        if not chars:
            return False

        line_groups = defaultdict(list)
        for ch in chars:
            key = round(ch.get('top', 0.0), 1)
            line_groups[key].append(ch)

        if not line_groups:
            return False

        # Inspect first non-empty line
        for key in sorted(line_groups.keys()):
            line_chars = line_groups[key]
            if len(line_chars) < 2:
                continue

            decreasing = 0
            increasing = 0
            for idx in range(len(line_chars) - 1):
                current = line_chars[idx]
                nxt = line_chars[idx + 1]
                x_current = current.get('x0')
                x_next = nxt.get('x0')
                if x_current is None or x_next is None:
                    continue
                if x_current > x_next:
                    decreasing += 1
                elif x_current < x_next:
                    increasing += 1

            if decreasing == 0 and increasing == 0:
                continue

            return decreasing > increasing

        return False

    def _reconstruct_mirrored_page(self, page) -> str:
        """Rebuild text for mirrored pages by walking characters in their original order."""
        try:
            chars = page.chars
        except Exception:
            return ""

        if not chars:
            return ""

        line_groups = defaultdict(list)
        for ch in chars:
            key = round(ch.get('top', 0.0), 1)
            line_groups[key].append(ch)

        text_lines = []
        for key in sorted(line_groups.keys()):
            line_chars = line_groups[key]
            if not line_chars:
                continue
            text_lines.append(self._build_line_from_chars(line_chars))

        reconstructed = "\n".join(text_lines)
        if reconstructed and reconstructed != page.extract_text():
            logger.debug("Reconstructed mirrored page text")
        return reconstructed

    def _build_line_from_chars(self, chars, space_threshold: float = 1.5) -> str:
        """Build a text line from a list of characters preserving original ordering."""
        line_text = []
        prev_x = None

        for ch in chars:
            text = ch.get('text', '')
            if text is None:
                continue

            x0 = ch.get('x0')
            if prev_x is not None and x0 is not None and abs(x0 - prev_x) > space_threshold:
                line_text.append(' ')

            line_text.append(text)

            if x0 is not None:
                prev_x = x0

        return ''.join(line_text)
    
    def identify_statement_type(self, pages_text: List[str]) -> Optional[str]:
        """
        Identify if this is a PNC Virtual Wallet statement.
        Returns statement type or None if not recognized.
        """
        if not pages_text:
            return None
            
        first_page = pages_text[0].upper()
        
        # Check for PNC Virtual Wallet indicators
        pnc_indicators = [
            'VIRTUAL WALLET SPEND STATEMENT',
            'PNC BANK',
            'VIRTUAL WALLET'
        ]

        for indicator in pnc_indicators:
            if indicator in first_page:
                logger.info("Identified as PNC Virtual Wallet statement")
                return 'PNC_VIRTUAL_WALLET'

        legacy_header_variants = [
            'DATE * SERIAL # DESCRIPTION',
            'DATE* SERIAL# DESCRIPTION'
        ]

        header_present = any(variant in first_page for variant in legacy_header_variants)

        if (('PRIMARY ACCOUNT' in first_page or 'PRIMARYACCOUNT' in first_page)
                and header_present):
            logger.info("Identified as BBVA legacy statement")
            return 'BBVA_LEGACY'

        logger.warning("Could not identify statement type")
        return None
    
    def handle_multi_page_documents(self, pages_text: List[str]) -> str:
        """
        Concatenate all pages into single text block for parsing.
        Preserves page boundaries with markers.
        """
        if not pages_text:
            return ""
            
        combined_text = []
        for page_num, page_text in enumerate(pages_text, 1):
            combined_text.append(f"\n--- PAGE {page_num} ---\n")
            combined_text.append(page_text)
            
        return "\n".join(combined_text)
