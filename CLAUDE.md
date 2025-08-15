# Claude Configuration - PNC Statement Parser

## 🎯 Project Overview
This is a Python application that parses PNC bank statement PDFs and converts them to CSV format for import into Google Sheets or Excel. The project uses reliable text-based parsing with JSON-based categorization. Enhanced coordinate-based parsing has been deprecated due to reliability issues.

## 🚀 Key Commands

### Quick Test
```bash
source venv/bin/activate
python tests/test_basic.py
```

### Process Statements
```bash
# Basic parsing with categorization (recommended)
python parse_statements.py --file statement.pdf --output output.csv

# Process directory with monthly files
python parse_statements.py --directory statements/ --output all.csv --monthly

# 🆕 YEAR PROCESSING MODE - Process complete year (auto-discovers directories)
python parse_statements.py --year 2023 --output output/2023.csv

# Year mode with cross-year boundary completion (includes January 2024 for December 2023 transactions)
python parse_statements.py --year 2023 --include-next-month --output output/2023_complete.csv

# Year mode with custom base path
python parse_statements.py --year 2023 --base-path /path/to/statements --output 2023.csv

# With summary report
python parse_statements.py --directory statements/ --output all.csv --summary report.txt
```

## 📁 Project Structure
- `src/` - Core parsing logic with JSON categorization
  - `parsers/` - **🏗️ Modular parser system (NEW August 2025)**
    - `base_parser.py` - Abstract interface for all bank parsers
    - `pnc_statement_parser.py` - Main PNC parser class
    - `pnc_patterns.py` - All PNC-specific regex patterns
    - `section_extractor.py` - Statement section handling
    - `transaction_parser.py` - Core transaction parsing logic
    - `categorization.py` - JSON-based auto-categorization engine
    - `text_utils.py` - Text cleaning and merchant extraction utilities
- `experiments/` - Deprecated enhanced parsing features
- `tests/` - Test suite 
- `docs/` - Documentation and analysis
- `examples/` - Usage examples
- `data/` - Input PDFs (gitignored)
- `output/` - Output CSVs (gitignored)

## 🔧 Key Technical Details

### 🆕 Year Processing Mode (NEW August 2025)
The parser now supports comprehensive year processing that automatically discovers and processes files across multiple directories:

**Key Features:**
- **Auto-Discovery**: `--year 2023` automatically finds files in `PNC_Documents/2023/` and optionally `PNC_Documents/2024/`
- **Cross-Year Boundaries**: `--include-next-month` includes January 2024 statement for complete December 2023 transactions
- **Smart Filtering**: Filters transactions to only include the target year, even from cross-year statements
- **Enhanced Output**: Auto-generates `2023_complete.csv`, monthly breakdowns, and summary reports
- **Coverage Validation**: Warns about missing months or incomplete data

**Directory Structure Expected:**
```
PNC_Documents/
├── 2023/
│   ├── Spend_x2157_Statement_01_January_2023.pdf
│   ├── Spend_x2157_Statement_02_February_2023.pdf
│   └── ... (all 2023 monthly statements)
└── 2024/
    ├── Spend_x2157_Statement_01_January_2024.pdf  # Contains Dec 2023 transactions
    └── ...
```

**Usage Examples:**
```bash
# Complete 2023 with automatic monthly breakdown
python parse_statements.py --year 2023 --output output/2023.csv

# Include next year for complete cross-year data
python parse_statements.py --year 2023 --include-next-month --output output/2023.csv
```

### Current Architecture (Modular Design - August 2025)
1. **🏗️ Modular Parser System** (`src/parsers/`)
   - **Extensible Design**: `BaseStatementParser` abstract interface for future bank support
   - **PNC Implementation**: `PNCStatementParser` inherits from base with PNC-specific logic
   - **Pattern Management**: `PNCPatterns` centralizes all regex patterns
   - **Component Separation**: Individual modules for sections, transactions, categorization, text cleaning
   - **Easy Testing**: Each component can be tested in isolation
   - **Future-Ready**: Adding new banks requires only new pattern/parser classes

2. **Core Components** (`src/parsers/`)
   - `SectionExtractor` - Handles deposits, withdrawals, online banking sections
   - `TransactionParser` - Core parsing logic with multi-line description support
   - `TransactionCategorizer` - JSON-based auto-categorization (reusable across banks)
   - `TextCleaner` & `MerchantExtractor` - Text processing utilities

3. **Deprecated Features** (`experiments/`)
   - Enhanced coordinate-based parsing (moved to experiments/)
   - Had issues with transaction type assignment and page ordering
   - Use modular parser for reliable results

### Critical Parsing Challenges
- **Multi-line descriptions**: Transaction descriptions span multiple lines
- **Extraneous text filtering**: Summary lines like "There were 2 Deposits totaling $6,288.87"
- **Amount edge cases**: Leading dots (.14), trailing dots, comma separators
- **Page continuations**: Transactions spanning multiple pages

### Validation Features
- Data integrity checks and consistency validation
- Date range validation (transactions within statement period)
- Duplicate detection and removal
- Year boundary handling for cross-year statements
- Amount reasonableness checks
- Clean transaction descriptions with contamination filtering

## 🧪 Testing Priority
Always test after making changes:
```bash
python tests/test_basic.py                    # Core functionality
python tests/test_extraneous_filtering.py     # Text filtering
```

## ⚠️ Important Patterns to Preserve

### Date Pattern
```python
r'^(\d{1,2}/\d{1,2})\s+'  # MM/DD at start of line
```

### Amount Pattern
```python
r'(\.?\d{1,3}(?:,\d{3})*\.?\d{0,2})'  # Handles .14, 6,250.00, etc.
```

### Extraneous Text Filters (35+ patterns)
Now centralized in `TextCleaner` class (`src/parsers/text_utils.py`):
- Summary lines ("There were X transactions totaling...")
- Section headers
- Page continuation markers
- Daily Balance Detail sections
- Account information and statement metadata
- Balance data and malformed lines

## 🔒 Security Notes
- Never commit actual bank statements (*.pdf)
- Never commit parsed data (*.csv)
- PNC_Documents/ folder is gitignored
- Always validate financial data accuracy

## 💡 Common Issues & Solutions

### Issue: "No text extracted from PDF"
- PDF may be scanned/image-based
- Solution: Need OCR preprocessing

### Issue: Wrong transaction types or page ordering
- Enhanced parser was deprecated due to these issues
- Use modular parser which correctly handles CREDIT/DEBIT types
- Modular parser maintains proper document flow ordering

### Issue: Type errors in imports
- Variable name conflicts (e.g., `summary` used for both Path and StatementSummary)
- Solution: Use unique variable names

## 📝 Development Workflow

1. **Understand existing patterns**: Review `docs/PNC_Statement_Structure_Analysis.md`
2. **Make changes**: Edit files in `src/parsers/` for parser logic, `src/` for other components
3. **Test immediately**: Run relevant tests in `tests/`
4. **Validate with real PDFs**: Use sample statements if available
5. **Check validation reports**: Review JSON output for reconciliation

## 🔧 Working with Modular Components

### Adding New Bank Support
```python
# 1. Create new pattern class
class BankOfAmericaPatterns:
    def __init__(self):
        self.DATE_PATTERN = re.compile(r'...')  # BOA-specific patterns

# 2. Create parser inheriting from base
class BOAStatementParser(BaseStatementParser):
    def __init__(self):
        self.patterns = BankOfAmericaPatterns()
        self.categorizer = TransactionCategorizer()  # Reuse
        # Initialize other components...
```

### Accessing Parser Components
```python
parser = PNCStatementParser()
# Access patterns: parser.patterns.DATE_PATTERN
# Access text cleaner: parser.transaction_parser.text_cleaner
# Access categorizer: parser.categorizer
```

## 🎓 Key Learning Points

### 🆕 Year Processing Benefits
- **One Command Complete Years**: `--year 2023` processes all 12 months + cross-year data automatically
- **Accurate Financial Records**: Captures December transactions that appear in January statements
- **Enhanced Validation**: Cross-file duplicate detection and comprehensive gap reporting
- **Smart Output Naming**: Automatically generates `2023_complete.csv`, `2023_complete_monthly/`, etc.
- **User-Friendly**: No manual file copying or temporary directories needed
- **Coverage Validation**: Warns if months appear missing or if unusual file counts detected

### Successful Architecture
- Text-based parsing provides reliable, consistent results
- JSON-based categorization allows community contributions
- Proper transaction type detection (deposits as CREDIT, withdrawals as DEBIT)
- Document flow ordering maintains logical transaction sequence
- Clean description extraction removes contamination while preserving data

### Architecture Decisions
- **Modular Design**: Separated concerns into focused components
- **Extensible Framework**: BaseStatementParser enables multi-bank support
- **JSON Configuration**: Easy category customization via `src/categories.json`
- **Comprehensive Text Filtering**: 35+ patterns centralized in TextCleaner
- **Component Reusability**: Core components work across different bank formats
- **Testing Isolation**: Each module can be tested independently

## 📊 Performance Expectations
- Processing time: ~2 seconds per 6-page statement
- Accuracy: 95%+ transaction identification with correct types
- Proper CREDIT/DEBIT assignment (deposits as CREDIT, withdrawals as DEBIT)
- Maintains document flow ordering (page 1 → 2 → 3, etc.)

## 🔄 Future Improvements to Consider
- **✅ Multi-bank support**: Framework now ready - add new bank parsers easily
- **✅ Year Processing Mode**: Now implemented - complete year processing with cross-year boundaries
- OCR integration for scanned PDFs
- Machine learning for transaction categorization
- Web interface for non-technical users
- Expanded JSON category patterns via community PRs
- Parser factory for automatic bank detection
- Common pattern extraction to shared modules
- Multi-year processing (e.g., `--years 2022,2023,2024`)
- Automatic gap detection and filling suggestions

## 🎯 Category Contribution
The parser uses `src/categories.json` for transaction categorization:
```json
{
  "categories": {
    "Medical": {
      "patterns": ["Cleveland Clinic", "MetroHealth", "Mhs\\*Metrohealth"]
    }
  }
}
```
Users can submit PRs to expand categories for the community!

---

**Note to Claude**: This is a financial data processing application. Always prioritize accuracy and data integrity. Test thoroughly before deploying changes. The **modular parser with JSON categorization** provides the most reliable results and is now designed for easy extension to other banks.

## 🏗️ Modular Architecture Summary (August 2025)

**Key Benefits Achieved**:
- ✅ **Extensible Design**: Easy to add new bank support
- ✅ **Component Separation**: Each module has single responsibility  
- ✅ **Testing Isolation**: Individual components can be tested
- ✅ **Pattern Reusability**: Common patterns ready for other banks
- ✅ **Maintainable Code**: Clear structure, focused responsibilities
- ✅ **Future-Ready**: Framework supports community contributions

**Import Changes**: 
- Old: `from src.pnc_parser import PNCStatementParser`
- New: `from src.parsers import PNCStatementParser`

**Access Patterns**:
- Patterns: `parser.patterns.DATE_PATTERN`
- Text cleaning: `parser.transaction_parser.text_cleaner`
- Categorization: `parser.categorizer`