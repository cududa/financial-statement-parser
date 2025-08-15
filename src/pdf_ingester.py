import pdfplumber
import PyPDF2
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
                    text = page.extract_text()
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
                logger.info(f"Identified as PNC Virtual Wallet statement")
                return 'PNC_VIRTUAL_WALLET'
                
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