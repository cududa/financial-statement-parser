# PNC Statement Parser

A Python application that automatically extracts financial transaction data from PNC bank statement PDFs and converts them into structured CSV format suitable for import into Google Sheets or Excel.

## 🎯 Features

### Reliable Text-Based Parsing
- **JSON-Based Categorization**: Configurable transaction categorization system for community contributions
- **Proven Transaction Detection**: Handles deposits, withdrawals, and online banking with correct CREDIT/DEBIT types
- **Document Flow Ordering**: Maintains proper page ordering and transaction sequence
- **Clean Description Extraction**: Removes header contamination while preserving legitimate data

### Core Parsing Features
- **Accurate PDF Parsing**: Extracts transaction data from PNC Virtual Wallet statements
- **Smart Text Filtering**: Automatically filters out summary lines, headers, and extraneous text
- **Multiple Transaction Types**: Handles deposits, withdrawals, and online banking deductions
- **Enhanced Amount Parsing**: Handles edge cases like `.14` → `0.14`, trailing dots, comma separators

### Financial-Grade Validation
- **Data Integrity Checks**: Validates transaction data consistency and completeness
- **Date Range Validation**: Ensures transactions fall within statement period
- **Duplicate Detection**: Identifies potential duplicate transactions
- **Year Boundary Handling**: Correctly assigns years for cross-year statement periods

### Output & Integration
- **Google Sheets Compatible**: Optimized CSV output format for easy spreadsheet import
- **Flexible Output**: Single file or monthly file exports with summary reports
- **Configurable Categories**: JSON-based category system for easy community contributions
- **Command Line Interface**: Easy-to-use CLI with various options

## 📋 Supported Statement Formats

Currently supports **PNC Virtual Wallet Spend Statements** with these sections:
- Deposits and Other Additions
- Banking/Debit Card Withdrawals and Purchases  
- Online and Electronic Banking Deductions

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pnc-statement-parser
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

### Basic Usage

**Basic parsing (recommended):**
```bash
python parse_statements.py --file statement.pdf --output transactions.csv
```

**Process entire directory:**
```bash
python parse_statements.py --directory 2023/ --output 2023_all.csv
```

**🆕 Year Processing Mode (NEW!) - Process complete year automatically:**
```bash
# Auto-discovers files from PNC_Documents/2023/ and processes complete year
python parse_statements.py --year 2023 --output 2023_complete.csv

# Include December transactions from January 2024 statement for complete year-end data
python parse_statements.py --year 2023 --include-next-month --output 2023_complete.csv

# Custom base directory for statements
python parse_statements.py --year 2023 --base-path /path/to/statements --output 2023.csv
```

**With monthly files and summary:**
```bash
python parse_statements.py --directory 2023/ --output 2023_all.csv --monthly --summary report.txt
```

## 📊 Output Format

The parser generates CSV files with the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| Date | Transaction date (YYYY-MM-DD) | 2022-12-08 |
| Amount | Signed amount (negative for debits) | -24.93 |
| Type | Transaction type | DEBIT/CREDIT |
| Description | Full transaction description | 3767 Debit Card Purchase Ross Beverage Lakewood |
| Merchant | Extracted merchant name | Ross Beverage |
| Card | Last 4 digits of card (if applicable) | 3767 |
| Category | Auto-categorized type | Shopping |
| Source_File | Original PDF filename | statement.pdf |
| Month | Year-month for filtering | 2022-12 |
| Page | Source page number | 1 |

## 🛠️ Command Line Options

```bash
python parse_statements.py [OPTIONS]

Options:
  -f, --file PATH             Single PDF statement file to process
  -d, --directory PATH        Directory containing PDF statements to process
  -y, --year YYYY             🆕 Process complete year (auto-discovers directories)
  --base-path PATH            Root directory containing year subdirectories (default: PNC_Documents/)
  --include-next-month        Include first statement of next year for complete data
  -o, --output PATH           Output CSV file path [required]
  --monthly                   Create separate CSV files for each month (auto-enabled for --year)
  --summary PATH              Generate summary report file
  -v, --verbose               Enable verbose logging
  --validate-only             Only validate files without generating output
  --help                      Show help message
```

### 🆕 Year Processing Features

**Auto-Discovery**: The `--year` option automatically finds files in your directory structure:
```
PNC_Documents/
├── 2023/               # All 2023 monthly statements
│   ├── Statement_01_January_2023.pdf
│   ├── Statement_02_February_2023.pdf
│   └── ...
└── 2024/               # Optional: for cross-year boundary data
    └── Statement_01_January_2024.pdf  # Contains Dec 2023 transactions
```

**Smart Output Naming**: Automatically generates appropriate filenames:
- `2023_complete.csv` - Main consolidated file
- `2023_complete_monthly/` - Individual monthly breakdowns
- `2023_complete_summary.txt` - Comprehensive summary report

**Coverage Validation**: Warns about missing months or unusual file counts to ensure complete data.

## 🏗️ Modular Architecture

The application features a **modular, extensible architecture** designed to support multiple bank formats:

### Core Components

#### 1. PDFIngester (`src/pdf_ingester.py`)
- Validates PDF files and extracts text using pdfplumber with PyPDF2 fallback
- Identifies PNC statement types and handles multi-page documents

#### 2. Modular Parser System (`src/parsers/`)
**Base Parser Framework**:
- `BaseStatementParser` - Abstract interface for all bank parsers
- Designed for easy extension to other bank formats

**PNC-Specific Implementation**:
- `PNCStatementParser` - Main parser class inheriting from base
- `PNCPatterns` - All PNC-specific regex patterns and rules
- `SectionExtractor` - Handles deposits, withdrawals, and online banking sections
- `TransactionParser` - Core transaction parsing with multi-line description support
- `TransactionCategorizer` - JSON-based auto-categorization engine
- `TextCleaner` & `MerchantExtractor` - Text processing and merchant extraction utilities

#### 3. Data Processing (`src/data_processor.py`)
- Cleans and normalizes transaction data
- Validates data integrity and date ranges
- Detects potential duplicates and generates validation reports

#### 4. Export System (`src/csv_exporter.py`)
- Google Sheets compatible formatting
- Monthly breakdowns and summary reports
- Proper data type handling

#### 5. Data Models (`src/models.py`)
- Type-safe Transaction and StatementSummary classes
- Date conversion and amount signing methods

### 🔧 Extensibility for Future Banks

The modular design makes adding support for other banks straightforward:

```python
# Example: Adding Bank of America support
class BOAStatementParser(BaseStatementParser):
    def __init__(self):
        self.patterns = BOAPatterns()  # Bank-specific patterns
        self.categorizer = TransactionCategorizer()
        # ... reuse existing components
```

**General Purpose Components Ready for Reuse**:
- Date parsing patterns (MM/DD format)
- Amount extraction (handles commas, decimals)
- Section detection framework
- Text cleaning utilities
- JSON-based categorization system

## 🔍 Parsing Intelligence

The parser includes sophisticated text filtering to handle common PNC statement issues:

### Filtered Content
- Summary lines like "There were 2 Deposits and Other Additions totaling $6,288.87"
- Section headers and column headers
- Page continuation markers
- Account information and statement metadata
- Daily balance details (not transaction data)

### Transaction Recognition
- Date patterns: `MM/DD` format
- Amount patterns: Handles comma separators (`6,250.00`)
- Multi-line descriptions spanning 2+ lines
- Different transaction prefixes (Debit Card, POS, Direct Deposit, etc.)

### Auto-Categorization
Transactions are automatically categorized using `src/categories.json`:
- **Income**: DirectDeposit, Payroll, INTRVLLLC
- **Shopping**: Amazon, Walmart, Target, Amzn Mktp
- **Medical**: Cleveland Clinic, MetroHealth, Mhs\*Metrohealth
- **Media**: Netflix, Nytimes\*Nytimes, Hulu
- **Transportation**: Uber, Lyft
- **Subscription**: Recurring payments, OnlyFans, Google

**Contributing Categories**: Edit `src/categories.json` and submit a PR!

## 📁 Project Structure

```
pnc-statement-parser/
├── src/                     # Core application code
│   ├── main.py              # CLI entry point
│   ├── models.py            # Data models
│   ├── pdf_ingester.py      # PDF text extraction
│   ├── data_processor.py    # Data validation and cleaning
│   ├── csv_exporter.py      # CSV output generation
│   ├── year_processor.py    # 🆕 Year processing and multi-directory handling
│   ├── categories.json      # Configurable transaction categories
│   └── parsers/             # Modular parser system
│       ├── __init__.py      # Parser package
│       ├── base_parser.py   # Abstract parser interface
│       ├── pnc_statement_parser.py  # Main PNC parser
│       ├── pnc_patterns.py  # PNC-specific regex patterns
│       ├── section_extractor.py    # Statement section handling
│       ├── transaction_parser.py   # Core transaction parsing
│       ├── categorization.py       # Auto-categorization engine
│       └── text_utils.py    # Text cleaning utilities
├── experiments/             # Deprecated experimental features
│   ├── enhanced_parser.py   # [DEPRECATED] Layout-aware parsing
│   ├── layout_analyzer.py   # [DEPRECATED] Coordinate-based analysis
│   ├── parse_statements_enhanced.py  # [DEPRECATED] Enhanced CLI
│   └── README.md            # Explanation of deprecated features
├── tests/                   # Test suite
│   ├── test_basic.py        # Basic functionality tests
│   └── test_extraneous_filtering.py  # Text filtering tests
├── docs/                    # Documentation
│   ├── PNC_Statement_Parser_Plan.md  # Project planning
│   ├── PNC_Statement_Structure_Analysis.md  # PDF structure analysis
│   └── chatgptplan.md       # Alternative approach analysis
├── examples/                # Usage examples
│   └── example_usage.py     # Python API examples
├── data/                    # Input directory (user PDFs)
├── output/                  # Output directory (CSVs)
├── parse_statements.py      # Parser entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🧪 Testing

Run the test suite from the project root:
```bash
# Basic functionality tests
python tests/test_basic.py

# Text filtering tests
python tests/test_extraneous_filtering.py

# Configurable contamination cleaning tests
python tests/test_contamination_cleaning.py

# Run all tests
for test in tests/test_*.py; do python "$test" || echo "Skipping $test"; done
```

### 🔧 Test Configuration

The parser includes a **configurable test system** that allows users to customize test cases without exposing personal financial information.

#### Configuration File
Edit `tests/test_config.json` to add your own test cases:

```json
{
  "contamination_test_cases": [
    {
      "name": "Custom contamination test",
      "input": "Your transaction with contamination text",
      "expected": "Your clean transaction",
      "description": "Tests your specific contamination pattern"
    }
  ],
  "merchant_extraction_test_cases": [
    {
      "name": "Custom merchant extraction",
      "input": "1234 Debit Card Purchase Your Store Name",
      "expected_merchant": "Your Store",
      "expected_card": "1234",
      "description": "Tests merchant extraction for your data"
    }
  ],
  "validation_test_cases": [
    {
      "name": "Custom validation test",
      "lines": ["Your test line 1", "Your test line 2"],
      "expected_valid": [true, false],
      "description": "Tests line validation logic"
    }
  ]
}
```

#### Test Categories

1. **Contamination Cleaning Tests** (`contamination_test_cases`)
   - Test removal of summary text that gets mixed into transaction descriptions
   - Test fixing of spacing issues from PDF text extraction
   - Test removal of extraneous bank statement headers/footers

2. **Merchant Extraction Tests** (`merchant_extraction_test_cases`)
   - Test extraction of merchant names from transaction descriptions
   - Test extraction of card numbers (last 4 digits)
   - Test special cases like Direct Deposit payroll processing

3. **Validation Tests** (`validation_test_cases`)
   - Test merchant continuation line validation
   - Test rejection of contamination lines vs. acceptance of valid merchant data

#### Adding Your Own Test Cases

To add test cases with your own transaction patterns:

1. **Copy a real transaction description** from your parsed output
2. **Identify the contamination** (unwanted text that got mixed in)
3. **Add the test case** to `tests/test_config.json`:
   ```json
   {
     "name": "My bank contamination",
     "input": "Your transaction with unwanted summary text",
     "expected": "Your clean transaction only", 
     "description": "Removes summary text from my statements"
   }
   ```
4. **Run the test** to verify: `python tests/test_contamination_cleaning.py`

This approach allows you to test the parser with your specific statement patterns while keeping personal financial information out of the codebase.

## 📝 Example Workflow

1. **Prepare your statements**: Collect PNC PDF statements in a folder
2. **Run the parser**: 
   ```bash
   python parse_statements.py -d statements/ -o transactions.csv --monthly --summary report.txt -v
   ```
3. **Review output**: Check the CSV file and validation report
4. **Import to Google Sheets**: Use the CSV import feature in Google Sheets
5. **Verify data**: Spot-check a few transactions against the original PDFs

## ⚠️ Validation and Quality Assurance

The parser includes comprehensive validation:

- **Date Range Validation**: Ensures all transactions fall within statement period
- **Amount Validation**: Flags unreasonable amounts (> $50,000 or $0)
- **Balance Calculations**: Verifies totals match statement summaries
- **Duplicate Detection**: Identifies potential duplicate transactions
- **Completeness Checks**: Flags missing or incomplete data

Always review the validation report and manually verify a sample of transactions.

## 🔧 Troubleshooting

### Common Issues

**"No text extracted from PDF"**
- PDF may be scanned/image-based rather than text-based
- Try using OCR tools to convert to text-based PDF first

**"Could not identify statement type"**
- Ensure PDF is a PNC Virtual Wallet statement
- Check that the PDF contains expected header text

**"No transactions found"**
- Verify the PDF contains transaction sections
- Check if statement period has any transactions
- Use `--verbose` flag for detailed parsing logs

**Validation errors**
- Review validation report for specific issues
- Some edge cases may require manual review
- Consider running with `--validate-only` first

### Performance Notes

- Processing time: ~2 seconds per statement (6 pages)
- Memory usage: Minimal for typical statement sizes
- Large statements (>20 pages) may need additional optimization

## 🤝 Contributing

This parser was built specifically for PNC Virtual Wallet statements based on detailed analysis of the statement structure. To extend support to other banks or statement formats:

1. Analyze the new statement format thoroughly
2. Create new parser classes following the existing pattern
3. Add appropriate regex patterns and section identifiers
4. Update the main extraction logic to handle the new format
5. Add comprehensive tests

## 📄 License

This project is provided as-is for personal financial data processing. Use responsibly and in compliance with your bank's terms of service.

## 🔒 Security Notes

- This application processes financial data locally only
- No data is transmitted to external servers
- Always verify extracted data against original statements
- Keep your PDF files and exported CSVs secure
- Consider encryption for sensitive financial data

---

**Generated with Phase 3 Implementation - August 2025**

*Successfully converts PNC bank statement PDFs into structured CSV format for easy financial analysis and record keeping.*