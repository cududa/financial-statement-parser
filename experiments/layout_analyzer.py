"""
Layout-aware PDF analysis module for PNC statements.
Implements coordinate-based parsing as suggested in ChatGPT plan.
"""

import pdfplumber
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, NamedTuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class BoundingBox(NamedTuple):
    """Represents a bounding box with coordinates"""
    x0: float  # left
    y0: float  # bottom  
    x1: float  # right
    y1: float  # top


class TextElement(NamedTuple):
    """Represents a text element with position and content"""
    text: str
    bbox: BoundingBox
    page_number: int


class ColumnBands:
    """Represents detected column boundaries in the statement"""
    def __init__(self, date_band: Tuple[float, float], 
                 amount_band: Tuple[float, float],
                 description_band: Tuple[float, float],
                 page_width: float):
        self.date_band = date_band      # (x_min, x_max) for date column
        self.amount_band = amount_band  # (x_min, x_max) for amount column  
        self.description_band = description_band  # (x_min, x_max) for description
        self.page_width = page_width
    
    def is_in_date_column(self, x: float) -> bool:
        """Check if x coordinate is in date column"""
        return self.date_band[0] <= x <= self.date_band[1]
    
    def is_in_amount_column(self, x: float) -> bool:
        """Check if x coordinate is in amount column"""
        return self.amount_band[0] <= x <= self.amount_band[1]
    
    def is_in_description_column(self, x: float) -> bool:
        """Check if x coordinate is in description column"""
        return self.description_band[0] <= x <= self.description_band[1]
    
    def is_in_main_table(self, x: float) -> bool:
        """Check if x coordinate is within main transaction table"""
        return self.date_band[0] <= x <= self.description_band[1]
    
    def is_right_margin_text(self, x: float) -> bool:
        """Check if text is in right margin (likely summary text)"""
        return x > self.description_band[1] + 20  # 20pt buffer


class LayoutAnalyzer:
    """
    Analyzes PDF layout to detect column boundaries and spatial relationships.
    Uses coordinate-based approach for more robust parsing.
    """
    
    def __init__(self):
        self.date_pattern = re.compile(r'^\d{1,2}/\d{1,2}$')
        self.amount_pattern = re.compile(r'^\.?\d{1,3}(?:,\d{3})*\.?\d{0,2}$')
        self.currency_pattern = re.compile(r'^\$?[\d,]*\.?\d{0,2}$')
    
    def extract_text_with_coordinates(self, pdf_path: Path) -> List[TextElement]:
        """
        Extract all text elements with their coordinates from PDF.
        Returns list of TextElement objects.
        """
        text_elements = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Get individual characters with coordinates
                    chars = page.chars
                    
                    # Group characters into words/text blocks
                    words = page.extract_words()
                    
                    for word in words:
                        bbox = BoundingBox(
                            x0=word['x0'], y0=word['bottom'],
                            x1=word['x1'], y1=word['top']
                        )
                        
                        text_element = TextElement(
                            text=word['text'],
                            bbox=bbox,
                            page_number=page_num
                        )
                        
                        text_elements.append(text_element)
                        
        except Exception as e:
            logger.error(f"Failed to extract coordinates from {pdf_path}: {e}")
            raise
        
        logger.info(f"Extracted {len(text_elements)} text elements with coordinates")
        return text_elements
    
    def detect_column_bands(self, text_elements: List[TextElement]) -> Optional[ColumnBands]:
        """
        Detect column boundaries by clustering x-positions of dates and amounts.
        Implements the ChatGPT band detection strategy.
        """
        date_x_positions = []
        amount_x_positions = []
        page_width = 0
        
        # Find all elements that look like dates or amounts
        for element in text_elements:
            # Track page width
            page_width = max(page_width, element.bbox.x1)
            
            # Check if this looks like a date
            if self.date_pattern.match(element.text):
                date_x_positions.append(element.bbox.x0)
                logger.debug(f"Found date '{element.text}' at x={element.bbox.x0}")
            
            # Check if this looks like an amount  
            elif (self.amount_pattern.match(element.text) or 
                  self.currency_pattern.match(element.text)):
                amount_x_positions.append(element.bbox.x0)
                logger.debug(f"Found amount '{element.text}' at x={element.bbox.x0}")
        
        if not date_x_positions or not amount_x_positions:
            logger.warning("Could not find enough dates or amounts to detect columns")
            return None
        
        # Cluster x-positions to find column boundaries
        date_cluster = self._find_dominant_cluster(date_x_positions)
        amount_cluster = self._find_dominant_cluster(amount_x_positions)
        
        if not date_cluster or not amount_cluster:
            logger.warning("Could not detect column clusters")
            return None
        
        # Define column bands with some buffer
        date_band = (date_cluster[0] - 5, date_cluster[1] + 30)  # Date column
        amount_band = (amount_cluster[0] - 5, amount_cluster[1] + 30)  # Amount column
        description_start = max(date_band[1], amount_band[1]) + 10
        description_band = (description_start, page_width * 0.75)  # Description column (75% of page)
        
        bands = ColumnBands(date_band, amount_band, description_band, page_width)
        
        logger.info(f"Detected column bands:")
        logger.info(f"  Date: {date_band}")
        logger.info(f"  Amount: {amount_band}")  
        logger.info(f"  Description: {description_band}")
        logger.info(f"  Page width: {page_width}")
        
        return bands
    
    def _find_dominant_cluster(self, positions: List[float], tolerance: float = 20) -> Optional[Tuple[float, float]]:
        """
        Find the dominant cluster of x-positions.
        Returns (min, max) of the largest cluster.
        """
        if not positions:
            return None
        
        # Sort positions
        sorted_positions = sorted(positions)
        
        # Find clusters (positions within tolerance of each other)
        clusters = []
        current_cluster = [sorted_positions[0]]
        
        for pos in sorted_positions[1:]:
            if pos - current_cluster[-1] <= tolerance:
                current_cluster.append(pos)
            else:
                clusters.append(current_cluster)
                current_cluster = [pos]
        
        clusters.append(current_cluster)
        
        # Find the largest cluster
        largest_cluster = max(clusters, key=len)
        
        return (min(largest_cluster), max(largest_cluster))
    
    def filter_by_coordinates(self, text_elements: List[TextElement], 
                            bands: ColumnBands) -> Dict[str, List[TextElement]]:
        """
        Filter text elements by their coordinate location.
        Returns categorized elements: main_table, right_margin, etc.
        """
        categorized = {
            'main_table': [],
            'right_margin': [],
            'left_margin': [],
            'date_column': [],
            'amount_column': [],
            'description_column': []
        }
        
        for element in text_elements:
            x = element.bbox.x0
            
            # Categorize by location
            if bands.is_right_margin_text(x):
                categorized['right_margin'].append(element)
            elif x < bands.date_band[0] - 20:
                categorized['left_margin'].append(element)
            elif bands.is_in_main_table(x):
                categorized['main_table'].append(element)
                
                # Sub-categorize within main table
                if bands.is_in_date_column(x):
                    categorized['date_column'].append(element)
                elif bands.is_in_amount_column(x):
                    categorized['amount_column'].append(element)
                elif bands.is_in_description_column(x):
                    categorized['description_column'].append(element)
        
        # Log results
        for category, elements in categorized.items():
            logger.debug(f"{category}: {len(elements)} elements")
        
        return categorized
    
    def is_extraneous_by_coordinates(self, element: TextElement, 
                                   bands: ColumnBands) -> bool:
        """
        Determine if a text element is extraneous based on its coordinates.
        Implements coordinate-based filtering from ChatGPT plan.
        """
        x = element.bbox.x0
        text = element.text.strip()
        
        # Right margin text is likely summary/extraneous
        if bands.is_right_margin_text(x):
            logger.debug(f"Filtering right margin text: '{text}' at x={x}")
            return True
        
        # Far left margin text is likely headers/footers
        if x < bands.date_band[0] - 30:
            logger.debug(f"Filtering left margin text: '{text}' at x={x}")
            return True
        
        # Text that appears between columns might be artifacts
        if (bands.date_band[1] < x < bands.amount_band[0] - 10 or
            bands.amount_band[1] < x < bands.description_band[0] - 10):
            logger.debug(f"Filtering inter-column text: '{text}' at x={x}")
            return True
        
        return False
    
    def reconstruct_lines_from_coordinates(self, text_elements: List[TextElement]) -> List[str]:
        """
        Reconstruct text lines from coordinate-aware elements.
        Groups elements by y-coordinate to rebuild lines.
        """
        # Group elements by page and y-coordinate
        pages = defaultdict(list)
        for element in text_elements:
            pages[element.page_number].append(element)
        
        reconstructed_lines = []
        
        for page_num in sorted(pages.keys()):
            page_elements = pages[page_num]
            
            # Sort by y-coordinate (top to bottom), then x-coordinate (left to right)
            page_elements.sort(key=lambda e: (-e.bbox.y0, e.bbox.x0))
            
            # Group elements into lines by y-coordinate
            lines = []
            current_line = []
            current_y = None
            y_tolerance = 5  # Points tolerance for same line
            
            for element in page_elements:
                if current_y is None or abs(element.bbox.y0 - current_y) <= y_tolerance:
                    current_line.append(element)
                    current_y = element.bbox.y0
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = [element]
                    current_y = element.bbox.y0
            
            if current_line:
                lines.append(current_line)
            
            # Convert lines to text
            reconstructed_lines.append(f"--- PAGE {page_num} ---")
            for line_elements in lines:
                # Sort elements in line by x-coordinate
                line_elements.sort(key=lambda e: e.bbox.x0)
                line_text = ' '.join(e.text for e in line_elements)
                reconstructed_lines.append(line_text)
        
        return reconstructed_lines