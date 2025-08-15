#!/usr/bin/env python3
"""
Test suite for contamination cleaning functionality.
Uses configurable test data from test_config.json to avoid personal information.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from src.parsers.text_utils import TextCleaner, MerchantExtractor
    from src.parsers.pnc_patterns import PNCPatterns
except ImportError:
    # Add parent directory to path and try again
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    from src.parsers.text_utils import TextCleaner, MerchantExtractor
    from src.parsers.pnc_patterns import PNCPatterns


def load_test_config():
    """Load test configuration from JSON file."""
    config_path = Path(__file__).parent / 'test_config.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Test config not found at {config_path}")
        print("Using minimal built-in test cases")
        return get_minimal_test_config()


def get_minimal_test_config():
    """Fallback test configuration if JSON file is missing."""
    return {
        "contamination_test_cases": [
            {
                "name": "Basic contamination removal",
                "input": "Transaction Description There were 5 other Banking",
                "expected": "Transaction Description",
                "description": "Basic contamination test"
            }
        ],
        "merchant_extraction_test_cases": [],
        "validation_test_cases": []
    }


class TestContaminationCleaning:
    """Test suite for transaction description contamination cleaning."""
    
    def __init__(self):
        self.patterns = PNCPatterns()
        self.text_cleaner = TextCleaner(self.patterns)
        self.merchant_extractor = MerchantExtractor(self.patterns)
        self.config = load_test_config()
        
    def test_contamination_cleaning(self):
        """Test contamination cleaning with configurable test cases."""
        print("🧪 Testing Contamination Cleaning")
        print("=" * 50)
        
        test_cases = self.config.get("contamination_test_cases", [])
        passed = 0
        failed = 0
        
        for case in test_cases:
            name = case["name"]
            input_text = case["input"]
            expected = case["expected"]
            description = case.get("description", "")
            
            result = self.text_cleaner.clean_description(input_text)
            
            if result == expected:
                print(f"✅ PASS: {name}")
                if description:
                    print(f"   📝 {description}")
                print(f"   Input:    '{input_text}'")
                print(f"   Expected: '{expected}'")
                print(f"   Got:      '{result}'")
                passed += 1
            else:
                print(f"❌ FAIL: {name}")
                if description:
                    print(f"   📝 {description}")
                print(f"   Input:    '{input_text}'")
                print(f"   Expected: '{expected}'")
                print(f"   Got:      '{result}'")
                failed += 1
            print()
        
        print(f"📊 Results: {passed} passed, {failed} failed")
        return failed == 0
    
    def test_merchant_extraction(self):
        """Test merchant and card extraction with configurable test cases."""
        print("🏪 Testing Merchant Extraction")
        print("=" * 50)
        
        test_cases = self.config.get("merchant_extraction_test_cases", [])
        passed = 0
        failed = 0
        
        for case in test_cases:
            name = case["name"]
            input_text = case["input"]
            expected_merchant = case["expected_merchant"]
            expected_card = case["expected_card"]
            description = case.get("description", "")
            
            # Determine transaction type based on input
            transaction_type = "CREDIT" if "Direct Deposit" in input_text else "DEBIT"
            
            merchant, card = self.merchant_extractor.extract_merchant_info(
                input_text, transaction_type
            )
            
            success = (merchant == expected_merchant and card == expected_card)
            
            if success:
                print(f"✅ PASS: {name}")
                if description:
                    print(f"   📝 {description}")
                print(f"   Input:     '{input_text}'")
                print(f"   Merchant:  '{merchant}' (expected: '{expected_merchant}')")
                print(f"   Card:      '{card}' (expected: '{expected_card}')")
                passed += 1
            else:
                print(f"❌ FAIL: {name}")
                if description:
                    print(f"   📝 {description}")
                print(f"   Input:     '{input_text}'")
                print(f"   Merchant:  '{merchant}' (expected: '{expected_merchant}')")
                print(f"   Card:      '{card}' (expected: '{expected_card}')")
                failed += 1
            print()
        
        print(f"📊 Results: {passed} passed, {failed} failed")
        return failed == 0
    
    def test_merchant_continuation_validation(self):
        """Test merchant continuation line validation."""
        print("🔗 Testing Merchant Continuation Validation")
        print("=" * 50)
        
        test_cases = self.config.get("validation_test_cases", [])
        passed = 0
        failed = 0
        
        for case in test_cases:
            name = case["name"]
            lines = case["lines"]
            expected_valid = case["expected_valid"]
            description = case.get("description", "")
            
            print(f"📋 Test: {name}")
            if description:
                print(f"   📝 {description}")
            
            case_passed = True
            for line, expected in zip(lines, expected_valid):
                result = self.text_cleaner.is_valid_merchant_continuation(line)
                if result == expected:
                    print(f"   ✅ '{line}' -> {result} (expected: {expected})")
                else:
                    print(f"   ❌ '{line}' -> {result} (expected: {expected})")
                    case_passed = False
            
            if case_passed:
                passed += 1
                print("   ✅ OVERALL PASS")
            else:
                failed += 1
                print("   ❌ OVERALL FAIL")
            print()
        
        print(f"📊 Results: {passed} passed, {failed} failed")
        return failed == 0
    
    def run_all_tests(self):
        """Run all test suites."""
        print("🚀 Starting Contamination Cleaning Test Suite")
        print("=" * 60)
        print()
        
        results = []
        results.append(self.test_contamination_cleaning())
        results.append(self.test_merchant_extraction())
        results.append(self.test_merchant_continuation_validation())
        
        print("📋 FINAL RESULTS")
        print("=" * 60)
        
        if all(results):
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print("❌ Some tests failed. Check output above.")
            return False


def main():
    """Main test runner."""
    tester = TestContaminationCleaning()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)
    
    print("\n✅ Test suite completed successfully!")


if __name__ == "__main__":
    main()