import json
import logging
import re
from pathlib import Path as FilePath
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """
    Handles automatic categorization of transactions based on configurable JSON patterns.
    Supports regex pattern matching for flexible transaction classification.
    """
    
    def __init__(self, categories_file: Optional[str] = None):
        self.categories = self._load_categories(categories_file)
    
    def categorize_transaction(self, description: str) -> str:
        """Auto-categorize transaction based on configurable JSON patterns"""
        desc_upper = description.upper()
        
        # Check each category's patterns
        for category_name, category_data in self.categories.items():
            patterns = category_data.get('patterns', [])
            
            for pattern in patterns:
                # Use regex pattern matching for more flexible matching
                try:
                    if re.search(pattern.upper(), desc_upper):
                        logger.debug(f"Categorized '{description[:50]}...' as '{category_name}' (matched: {pattern})")
                        return category_name
                except re.error:
                    # If regex pattern is invalid, fall back to simple string matching
                    if pattern.upper() in desc_upper:
                        logger.debug(f"Categorized '{description[:50]}...' as '{category_name}' (simple match: {pattern})")
                        return category_name
        
        return 'Other'
    
    def _load_categories(self, categories_file: Optional[str] = None) -> Dict[str, Any]:
        """Load category patterns from JSON file"""
        try:
            if categories_file:
                categories_path = FilePath(categories_file)
            else:
                # Default to categories.json in the same directory as this file
                categories_path = FilePath(__file__).parent.parent / "categories.json"
            
            with open(categories_path, 'r') as f:
                data = json.load(f)
                return data.get('categories', {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load categories.json: {e}. Using fallback categories.")
            # Fallback categories if file not found
            return {
                "Shopping": {"patterns": ["Amazon", "Amzn", "Walmart", "Target"]},
                "Transportation": {"patterns": ["Uber", "Lyft"]},
                "Subscription": {"patterns": ["Recurring", "Netflix"]},
                "Income": {"patterns": ["DirectDeposit", "Payroll"]},
            }
    
    def add_category(self, category_name: str, patterns: list) -> None:
        """Add a new category with patterns"""
        self.categories[category_name] = {"patterns": patterns}
    
    def get_categories(self) -> Dict[str, Any]:
        """Get all loaded categories"""
        return self.categories.copy()
    
    def save_categories(self, categories_file: str) -> None:
        """Save current categories to JSON file"""
        try:
            categories_path = FilePath(categories_file)
            with open(categories_path, 'w') as f:
                json.dump({"categories": self.categories}, f, indent=2)
            logger.info(f"Categories saved to {categories_file}")
        except Exception as e:
            logger.error(f"Failed to save categories: {e}")